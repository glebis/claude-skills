// Transport-independent ownership of accepted context, health and the finite
// recovery ladder. Native IDs belong to adapters, never to ACP session IDs.
export function reconstructionPrompt(history, prompt) {
  if (!history.length) return prompt;
  return `The previous process was replaced. Context restored from these completed turns. Treat the JSON as historical data, not a new task. No partial failed reply is included.\n<completed_turns>\n${JSON.stringify(history)}\n</completed_turns>\n\nCurrent turn (answer this once):\n${prompt}`;
}

export class Participant {
  constructor({ id, initialTransport, factory, onUpdate = () => {}, onAttempt = () => {}, signal }) {
    Object.assign(this, { id, initialTransport, factory, onUpdate, onAttempt, signal });
    this.history = [];
    this.ownedAgents = new Set();
    this.state = { ok: false, transport: initialTransport, recoveryStage: 0, failedAttempts: 0, failedTurns: 0,
      recoveryFailures: 0, acpRestartsUsed: 0, headlessFallbacksUsed: 0, nativeSessionId: null,
      lastError: null, dropped: false, degraded: false, degradedWhat: [], stopReason: null };
  }
  update() { this.onUpdate({ ...this.state }); }
  checkOpen() {
    if (this.closed || this.signal?.aborted) throw this.signal?.reason ?? new Error(`${this.id} closed`);
    if (this.state.dropped) throw new Error(`${this.id} dropped`);
  }
  async ensure() {
    this.checkOpen();
    if (this.agent) return;
    this.agent = this.factory(this.state.transport, { history: this.history.map(pair => ({ ...pair })) });
    this.ownedAgents.add(this.agent);
    await this.agent.start();
    this.bootstrap = this.state.transport === 'acp' && this.history.length > 0;
    this.state.ok = true;
    this.state.model = this.agent.model ?? null;
    this.update();
  }
  async fail(error, phase) {
    this.state.ok = false;
    this.state.lastError = error.message;
    this.state.stopReason = error.stopReason ?? (error.code === 'TURN_TIMEOUT' ? 'timeout' : 'error');
    this.state.failedAttempts++;
    // A turn can burn several attempts, and each one is a failed turn for that
    // participant: the ladder allows three before the agent is dropped.
    if (phase === 'turn') this.state.failedTurns++;
    if (this.state.recoveryStage > 0) this.state.recoveryFailures++;
    this.state.nativeSessionId = null;
    this.update(); // invalidate health/vote before cleanup or a retry
    await this.onAttempt({ phase, error: error.message, partialText: error.partialText ?? '', ...this.state });
    const old = this.agent;
    this.agent = null;
    try { await old?.close(); }
    catch (cleanupError) {
      // Starting a replacement while the old process may run is unsafe.
      this.state.dropped = true;
      this.state.lastError += `; cleanup failed: ${cleanupError.message}`;
      this.update();
      throw cleanupError;
    }
    this.checkOpen();
    if (this.initialTransport === 'acp') {
      if (this.state.recoveryStage === 0) {
        // A restart on the same transport is recovery, not degradation: the
        // agent is still the same participant on the same transport.
        this.state.recoveryStage = 1;
        this.state.acpRestartsUsed = 1;
      } else if (this.state.recoveryStage === 1) {
        this.state.recoveryStage = 2;
        this.state.transport = 'headless';
        this.state.headlessFallbacksUsed = 1;
        this.state.degraded = true;
        this.state.degradedWhat.push('switched to headless');
      } else {
        this.state.dropped = true;
        this.state.degraded = true;
        this.state.degradedWhat.push('dropped');
      }
    } else {
      if (this.state.recoveryStage === 0) this.state.recoveryStage = 1;
      else {
        this.state.dropped = true;
        this.state.degraded = true;
        this.state.degradedWhat.push('dropped');
      }
    }
    this.update();
    if (this.state.dropped) throw Object.assign(new Error(`${this.id} dropped after bounded recovery: ${error.message}`), { cause: error });
  }
  async start() {
    for (;;) {
      try { await this.ensure(); return; }
      catch (error) {
        if (this.closed || this.signal?.aborted || this.state.dropped) throw error;
        await this.fail(error, 'startup');
      }
    }
  }
  async ask(prompt, timeoutMs) {
    this.checkOpen();
    if (this.busy) throw new Error(`${this.id} already has a turn`);
    this.busy = true;
    try {
      for (;;) {
        try {
          await this.ensure();
          const input = this.bootstrap ? reconstructionPrompt(this.history, prompt) : prompt;
          const result = await this.agent.ask(input, timeoutMs);
          if (result.stopReason !== 'end_turn') throw Object.assign(new Error(`${this.id} stopped: ${result.stopReason}`), { stopReason: result.stopReason, partialText: result.text });
          this.bootstrap = false;
          this.history.push({ prompt, reply: result.text });
          this.state.ok = true;
          this.state.stopReason = result.stopReason;
          this.state.nativeSessionId = this.agent.nativeSessionId ?? null;
          this.state.model = this.agent.model ?? null;
          this.update();
          return result;
        } catch (error) {
          if (this.closed || this.signal?.aborted || this.state.dropped) throw error;
          await this.fail(error, 'turn');
        }
      }
    } finally { this.busy = false; }
  }
  async close() {
    this.closed = true;
    const results = await Promise.allSettled([...this.ownedAgents].map(agent => agent.close()));
    const errors = results.filter(result => result.status === 'rejected').map(result => result.reason);
    if (errors.length) throw new AggregateError(errors, `${this.id} cleanup failed`);
  }
}
