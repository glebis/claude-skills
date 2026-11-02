import { spawn } from 'node:child_process';
import { Readable, Writable } from 'node:stream';
import * as acp from '@agentclientprotocol/sdk';
import { withTimeout, terminateProcess } from './runtime.mjs';
import { permissionAllowed } from './safeguards.mjs';

export class AcpAgent {
  constructor(id, cfg, cwd, log = () => {}, options = {}) {
    Object.assign(this, { id, cfg, cwd, log, options, transport: 'acp', busy: false, unusable: false });
  }

  async start() {
    try { return await this.startSession(); }
    catch (error) { await this.close(); throw error; }
  }

  async startSession() {
    if (this.unusable) throw new Error(`${this.id} closed`);
    const [cmd, ...args] = this.cfg.acp;
    this.proc = spawn(cmd, args, { cwd: this.cwd, stdio: ['pipe', 'pipe', 'pipe'], detached: process.platform !== 'win32' });
    this.stderr = '';
    this.proc.stdin.on('error', () => {}); // connection reports stream failures
    this.proc.stderr.on('data', d => { this.stderr = (this.stderr + d).slice(-4000); });
    await new Promise((resolve, reject) => { this.proc.once('spawn', resolve); this.proc.once('error', reject); });
    if (this.unusable) throw new Error(`${this.id} closed during spawn`);
    const stream = acp.ndJsonStream(Writable.toWeb(this.proc.stdin), Readable.toWeb(this.proc.stdout));
    this.conn = acp.client({ name: 'agent-roundtable' })
      .onNotification(acp.methods.client.session.update, ({ params }) => {
        if (params?.update?.sessionUpdate === 'config_option_update') this.updateConfigOptions(params.update.configOptions);
      })
      .onRequest(acp.methods.client.session.requestPermission, async ({ params }) => this.decidePermission(params))
      .connect(stream);
    const ctx = this.conn.agent;
    const init = await withTimeout(ctx.request(acp.methods.agent.initialize, { protocolVersion: 1, clientCapabilities: {} }), this.options.initializeMs ?? 60_000, `${this.id} initialize`);
    if (this.unusable) throw new Error(`${this.id} closed during initialize`);
    this.info = init.agentInfo;
    const newSession = () => withTimeout(ctx.buildSession(this.cwd).start(), this.options.initializeMs ?? 120_000, `${this.id} session/new`);
    try { this.session = await newSession(); }
    catch (error) {
      // JSON-RPC ACP auth-required is -32000; an internal error is not evidence
      // of auth failure. Only use a configured, advertised method.
      const advertised = init.authMethods?.some(method => method.id === this.cfg.authMethod);
      if (error.code !== -32000 || !this.cfg.authMethod || !advertised) throw error;
      await withTimeout(ctx.request(acp.methods.agent.authenticate, { methodId: this.cfg.authMethod }), this.options.initializeMs ?? 120_000, `${this.id} authenticate`);
      this.session = await newSession();
    }
    if (this.unusable) { this.session.dispose(); throw new Error(`${this.id} closed during session creation`); }
    this.updateConfigOptions(this.session.newSessionResponse.configOptions ?? []);
    if (this.cfg.model !== undefined) await this.setModel(this.cfg.model);
  }

  updateConfigOptions(configOptions) {
    this.configOptions = configOptions ?? [];
    this.model = this.getModelCatalog().currentModel;
  }

  getModelCatalog() {
    const candidates = (this.configOptions ?? []).filter(option => (option.type === 'select' || option.kind === 'select') &&
      (this.cfg.modelConfigId ? option.id === this.cfg.modelConfigId : option.category === 'model' || option.id === 'model'));
    if (candidates.length > 1) throw new Error(`${this.id} advertises multiple model controls; configure modelConfigId`);
    const config = candidates[0];
    if (!config) return { supported: false, configId: null, currentModel: null, models: [] };
    const flatten = options => options.flatMap(option => Array.isArray(option.options) ? flatten(option.options) : [{
      id: option.value, name: option.name, ...(option.description ? { description: option.description } : {}),
    }]);
    return { supported: true, configId: config.id, currentModel: config.currentValue, models: flatten(config.options ?? []) };
  }

  async setModel(model) {
    if (this.unusable || this.busy || this.configuring || !this.session) throw new Error(`${this.id} session unavailable for model selection`);
    const catalog = this.getModelCatalog();
    if (!catalog.supported) throw new Error(`${this.id} does not advertise ACP model selection`);
    if (typeof model !== 'string' || !catalog.models.some(option => option.id === model)) throw new Error(`${this.id} unsupported model: ${model}`);
    this.configuring = true;
    try {
      const response = await withTimeout(this.conn.agent.request(acp.methods.agent.session.setConfigOption, {
        sessionId: this.session.sessionId, configId: catalog.configId, value: model,
      }), this.options.initializeMs ?? 60_000, `${this.id} model selection`);
      if (this.unusable) throw new Error(`${this.id} closed during model selection`);
      this.updateConfigOptions(response.configOptions);
      if (this.model !== model) throw new Error(`${this.id} model selection mismatch: requested ${model}, received ${this.model}`);
      return this.getModelCatalog();
    } catch (error) {
      // A timed-out or mismatched selection leaves effective configuration uncertain.
      await this.close();
      throw error;
    } finally { this.configuring = false; }
  }

  decidePermission(params) {
    const allow = permissionAllowed(params.toolCall, this.cwd, this.options.runDir);
    const option = params.options.find(o => o.kind === (allow ? 'allow_once' : 'reject_once'));
    this.log(`${this.id} permission ${params.toolCall?.kind ?? 'missing'} ${JSON.stringify(params.toolCall?.title ?? '')} -> ${allow ? 'allow' : 'reject'}`);
    // Never elevate to allow_always; a later call may target another path.
    return option ? { outcome: { outcome: 'selected', optionId: option.optionId } } : { outcome: { outcome: 'cancelled' } };
  }

  async ask(prompt, timeoutMs) {
    if (this.busy || this.configuring || this.unusable || !this.session) throw new Error(`${this.id} session unavailable or already collecting`);
    this.busy = true;
    const done = this.session.prompt(prompt);
    done.catch(() => {}); // SDK forwards rejection to the same collector queue
    let partialText = '';
    const collect = (async () => {
      for (;;) {
        const message = await this.session.nextUpdate();
        if (message.kind === 'stop') {
          await done;
          return { text: partialText, stopReason: message.stopReason };
        }
        const u = message.update;
        if (u.sessionUpdate === 'agent_message_chunk' && u.content?.type === 'text') partialText += u.content.text;
        else if (u.sessionUpdate === 'tool_call') this.log(`${this.id} tool ${u.kind ?? ''} ${u.title ?? ''}`);
      }
    })();
    this.collect = collect;
    try {
      const result = await withTimeout(collect, timeoutMs, `${this.id} turn`);
      if (result.stopReason !== 'end_turn') throw Object.assign(new Error(`${this.id} stopped: ${result.stopReason}`), { stopReason: result.stopReason });
      return result;
    } catch (error) {
      // Even if cancellation drains successfully, never retry an uncertain turn
      // in this session. Recovery reconstructs only accepted completed pairs.
      this.unusable = true;
      error.partialText = partialText;
      if (error.code === 'TURN_TIMEOUT') {
        const grace = this.options.cancelGraceMs ?? 30_000;
        const drain = Promise.all([
          this.conn.agent.notify(acp.methods.agent.session.cancel, { sessionId: this.session.sessionId }),
          collect,
          done,
        ]);
        try { await withTimeout(drain, grace, `${this.id} cancel/drain`); }
        catch { await this.close(); }
      }
      throw error;
    } finally {
      // An abandoned reader is disposed by close before releasing the lock.
      if (this.unusable) await this.close();
      this.busy = false;
      this.collect = null;
    }
  }

  async close() {
    if (this.closing) return this.closing;
    this.unusable = true;
    this.closing = (async () => {
      this.session?.dispose(); // rejects outstanding nextUpdate, no orphan waiter
      try { this.conn?.close(); } catch {}
      await terminateProcess(this.proc, this.options.closeGraceMs ?? 5000);
      if (this.collect) await this.collect.catch(() => {});
    })();
    return this.closing;
  }
}
