#!/usr/bin/env node
// File-mediated audit runner. Importable without parsing argv or spawning agents.
import { existsSync, mkdirSync, readFileSync, appendFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { AcpAgent } from './acp-agent.mjs';
import { HeadlessAgent } from './headless.mjs';
import { Participant } from './recovery.mjs';
import { setup, loadModelConfig, withModelConfig } from './setup.mjs';
import { atomicWrite, assertFreshRun, waitForFile, fingerprint } from './safeguards.mjs';
import { openingPrompt, critiquePrompt, vetoPrompt, parseStatus } from './prompts.mjs';
import { assessConsensus, blockingIds, isDeadlock } from './consensus.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
export const REGISTRY = JSON.parse(readFileSync(join(HERE, '..', 'agents.json'), 'utf8'));
const ROLES = ['auditor', 'devils-advocate', 'architect', 'qa'];
const now = () => new Date().toISOString();
export const DEFAULTS = { agents: 'codex,cmd', format: 'panel', rounds: '3', 'min-rounds': '2', mode: 'auto', transport: 'auto',
  cwd: process.cwd(), 'turn-timeout': '900', 'drain-timeout': '30', 'kill-grace': '5', 'budget-min': '60', 'wait-timeout': '3600', 'no-veto': false };

// Timing knobs handed to every adapter: how long a cancelled ACP turn may drain
// before its session is discarded, and how long a process gets between SIGTERM
// and SIGKILL. One option set covers both constructor conventions.
const agentOptions = opt => {
  const drainMs = Number(opt['drain-timeout']) * 1000, graceMs = Number(opt['kill-grace']) * 1000;
  return { drainMs, killGraceMs: graceMs, cancelGraceMs: drainMs, closeGraceMs: graceMs, graceMs };
};
// The registry names its default transport either `transport` or `defaultTransport`.
const initialTransportFor = (opt, cfg) => opt.transport !== 'auto' ? opt.transport : cfg.defaultTransport ?? cfg.transport ?? (cfg.acp ? 'acp' : 'headless');

function validate(options, registry) {
  const ids = options.agents.split(',').map(s => s.trim()).filter(Boolean);
  if (ids.length < 2 || new Set(ids).size !== ids.length) throw new Error('At least two distinct agents are required');
  for (const id of ids) if (!Object.hasOwn(registry, id) || id.startsWith('_') || !/^[a-zA-Z0-9_-]+$/.test(id)) throw new Error(`Unknown or invalid agent: ${id}`);
  for (const [key, choices] of Object.entries({ format: ['panel', 'pingpong', 'roles'], mode: ['auto', 'active'], transport: ['auto', 'acp', 'headless'] })) {
    if (!choices.includes(options[key])) throw new Error(`Invalid ${key}: ${options[key]}`);
  }
  for (const key of ['rounds', 'min-rounds', 'turn-timeout', 'drain-timeout', 'kill-grace', 'budget-min', 'wait-timeout']) {
    const n = Number(options[key]);
    if (!Number.isFinite(n) || n <= 0 || (['rounds', 'min-rounds'].includes(key) && !Number.isInteger(n))) throw new Error(`Invalid ${key}`);
  }
  if (Number(options['min-rounds']) > Number(options.rounds)) throw new Error('min-rounds cannot exceed rounds');
  if (options.format === 'pingpong' && ids.length !== 2) throw new Error('pingpong needs exactly two agents');
  return ids;
}

export async function run(input, { registry = REGISTRY, createAgent, signal } = {}) {
  // A registry may arrive as the parsed object (from --registry) or as a path.
  registry = typeof input.registry === 'string' ? JSON.parse(readFileSync(input.registry, 'utf8')) : input.registry ?? registry;
  const opt = { ...DEFAULTS, ...input };
  registry = withModelConfig(registry, loadModelConfig(opt.cwd, opt.config));
  if (!opt.brief || !opt['run-dir']) throw new Error('run needs --brief and --run-dir');
  const ids = validate(opt, registry);
  const cwd = resolve(opt.cwd), runDir = resolve(opt['run-dir']);
  assertFreshRun(runDir); // before directories, output, baseline or any subprocess
  const brief = readFileSync(opt.brief, 'utf8');
  const baseline = fingerprint(cwd, runDir); // includes startup-phase edits
  for (const folder of ['rounds', 'moderator', 'veto']) mkdirSync(join(runDir, folder), { recursive: true });
  const log = message => {
    const line = `${now()} ${String(message).replace(/\s*\n\s*/g, ' ⏎ ').slice(0, 1000)}`;
    appendFileSync(join(runDir, 'events.log'), line + '\n');
    console.error(line);
  };
  atomicWrite(join(runDir, 'brief.md'), brief);
  const state = { status: 'starting', result: 'full', format: opt.format, mode: opt.mode, maxRounds: Number(opt.rounds), round: 0,
    agents: {}, rounds: [], turns: [], degraded: [], warnings: [],
    degradedAgents: [], stopReason: null, editDetection: { baseline, checks: [] } };
  const save = () => atomicWrite(join(runDir, 'state.json'), JSON.stringify(state, null, 2));
  const warn = message => { if (!state.warnings.includes(message)) { state.warnings.push(message); log(message); } };
  if (baseline.errors.length) warn(`Baseline edit coverage ${baseline.coverage.status}: ${baseline.errors.join('; ')}`);
  if (opt.format === 'roles' && !opt.roles) warn('Roles assigned by agent position; use --roles to select explicitly');
  const roles = opt.roles ? opt.roles.split(',').map(s => s.trim()) : ROLES;
  if (!roles.length || roles.some(role => !role)) throw new Error('Empty role');
  save();
  const participants = {}, latest = {};
  const turnMs = Number(opt['turn-timeout']) * 1000, waitMs = Number(opt['wait-timeout']) * 1000;
  const deadline = Date.now() + Number(opt['budget-min']) * 60_000;
  const checkAbort = () => signal?.throwIfAborted();
  const live = () => ids.filter(id => participants[id] && !participants[id].state.dropped);
  const degradedLabel = () => state.result === 'degraded' ? `degraded: ${state.degraded.map(d => `${d.agent} ${d.what}`).join(', ')}` : 'all original participants';
  const checkEdits = phase => {
    const after = fingerprint(cwd, runDir);
    state.editDetection.checks.push({ phase, ...after });
    if (after.coverage.status !== 'complete') warn(`${phase}: edit detection ${after.coverage.status}: ${after.errors.join('; ')}`);
    if (baseline.hash !== null && after.hash !== null && baseline.hash !== after.hash) warn(`${phase}: working tree content changed during audit`);
    save();
  };
  // On a signal, interrupt in-flight subprocesses as well as file waits. finally
  // awaits the same idempotent close operations before returning to the CLI.
  let interruptCleanup;
  const interrupt = () => { interruptCleanup = Promise.allSettled(Object.values(participants).map(p => p.close())); };
  signal?.addEventListener('abort', interrupt, { once: true });
  let scope = 'startup';
  try {
    checkAbort();
    for (const [i, id] of ids.entries()) {
      const initialTransport = initialTransportFor(opt, registry[id]);
      const role = opt.format === 'roles' ? roles[i % roles.length] : null;
      participants[id] = new Participant({ id, initialTransport, signal,
        factory: (transport, context) => createAgent ? createAgent(id, transport, context) :
          new (transport === 'acp' ? AcpAgent : HeadlessAgent)(id, registry[id], cwd, log, { ...agentOptions(opt), ...context, runDir }),
        onUpdate: health => {
          state.agents[id] = { ...state.agents[id], ...health, live: !health.dropped, role, requestedModel: registry[id].model ?? null };
          if (!health.ok && latest[id]) latest[id].status = null;
          for (const what of health.degradedWhat ?? []) {
            if (state.degraded.some(d => d.agent === id && d.what === what)) continue;
            state.degraded.push({ agent: id, what });
            if (!state.degradedAgents.includes(id)) state.degradedAgents.push(id);
            warn(`${id}: ${what}`);
          }
          state.result = state.degraded.length ? 'degraded' : state.result;
          save();
        },
        onAttempt: attempt => {
          atomicWrite(join(runDir, 'rounds', `${scope}-${id}.attempt-${attempt.failedAttempts}.json`), JSON.stringify(attempt, null, 2));
          // Each failed attempt is its own turn record, so a turn that recovered
          // internally still shows the failure that caused the recovery.
          state.turns.push({ round: state.round || null, agent: id, outcome: 'failed', phase: attempt.phase,
            transport: attempt.transport, stopReason: attempt.stopReason ?? null, error: attempt.error, recovered: true });
          log(`${id} ${scope} failed attempt ${attempt.failedAttempts}: ${attempt.error}`);
        },
      });
      state.agents[id] = { ...participants[id].state, role, requestedModel: registry[id].model ?? null, live: true };
    }
    const started = await Promise.allSettled(ids.map(id => participants[id].start()));
    started.forEach((result, i) => { if (result.status === 'rejected') warn(`${ids[i]} startup failed: ${result.reason.message}`); });
    checkAbort();
    if (live().length < 2) throw new Error('fewer than 2 agents available after recovery');

    const turn = async (round, id, prompt) => {
      const began = Date.now();
      atomicWrite(join(runDir, 'rounds', `r${round}-${id}.prompt.md`), prompt);
      try {
        const result = await participants[id].ask(prompt, turnMs);
        const status = parseStatus(result.text);
        latest[id] = { text: result.text, status, round, stopReason: result.stopReason };
        state.agents[id].lastReplyStatus = status;
        atomicWrite(join(runDir, 'rounds', `r${round}-${id}.md`), result.text);
        state.rounds.push({ round, agent: id, durationMs: Date.now() - began, outcome: status.parsed ? 'answered' : 'invalid_status', transport: participants[id].state.transport, stopReason: result.stopReason });
        state.turns.push({ round, agent: id, durationMs: Date.now() - began, outcome: status.parsed ? 'answered' : 'invalid_status', transport: participants[id].state.transport, stopReason: result.stopReason });
        if (!status.parsed) log(`${id} r${round}: invalid status (${status.error})`);
        save();
        return { agent: id, ...status };
      } catch (error) {
        if (latest[id]) latest[id].status = null;
        // Failed attempts are recorded by onAttempt as they happen, one turn record
        // each, so an internally recovered turn does not double-count.
        warn(`${id} r${round}: ${error.message}`);
        save();
        return null;
      }
    };
    const consumedNotes = new Set();
    const consumeNotes = throughRound => {
      const notes = [];
      for (let n = 1; n <= throughRound; n++) {
        const path = join(runDir, 'moderator', `r${n}.md`);
        if (!consumedNotes.has(path) && existsSync(path)) { notes.push(readFileSync(path, 'utf8')); consumedNotes.add(path); }
      }
      return notes.length ? notes.join('\n\n') : null;
    };
    let previousBlocking = null, moderatorNote = null;
    for (let round = 1; round <= state.maxRounds; round++) {
      checkAbort();
      const pendingNote = consumeNotes(round - 1);
      if (pendingNote) moderatorNote = pendingNote;
      if (moderatorNote?.trim().split('\n')[0].trim().toUpperCase() === 'STOP') { state.stopReason = 'moderator stopped'; break; }
      if (Date.now() > deadline) { state.stopReason = 'budget exhausted'; break; }
      state.round = round; state.status = 'debating'; scope = `r${round}`; delete state.waitingFor; save();
      const current = live();
      const speakers = opt.format === 'pingpong' ? [current[(round - 1) % current.length]] : current;
      // Snapshot every peer before starting any parallel turn.
      const peerSnapshot = Object.fromEntries(speakers.map(id => [id, ids.filter(p => p !== id && latest[p]).map(p => ({ label: registry[p].label ?? p, prefix: p.toUpperCase(), text: latest[p].text }))]));
      const results = await Promise.all(speakers.map(id => {
        const parts = [];
        if (!latest[id]) parts.push(openingPrompt({ brief, prefix: id.toUpperCase(), role: state.agents[id].role, format: opt.format }));
        if (peerSnapshot[id].length) parts.push(critiquePrompt({ round, peers: peerSnapshot[id], moderatorNote, prefix: id.toUpperCase() }));
        return turn(round, id, parts.join('\n\n'));
      }));
      checkAbort(); checkEdits(`round ${round}`);
      const expected = live();
      const statuses = expected.filter(id => latest[id]?.status).map(id => ({ agent: id, ...latest[id].status }));
      const verdict = expected.length < 2 ? { converged: false, reason: 'fewer than 2 agents remain' } :
        assessConsensus(statuses, { round, maxRounds: state.maxRounds, minRounds: Number(opt['min-rounds']), expectedAgents: expected });
      // The verdict reason stays plain; degradation is stated once, in the stop reason.
      const reason = state.result === 'degraded' ? `${degradedLabel()}; ${verdict.reason}` : verdict.reason;
      atomicWrite(join(runDir, 'rounds', `r${round}.summary.json`), JSON.stringify({ round, answered: results.filter(Boolean).length, statuses, expectedAgents: expected, degraded: state.degraded, reason }, null, 2));
      log(`round ${round}: ${reason}`);
      if (expected.length < 2) throw new Error('fewer than 2 agents remain after recovery');
      if (verdict.converged) { state.stopReason = state.result === 'degraded' ? `degraded convergence: ${degradedLabel()}` : `consensus: ${reason}`; break; }
      if (round === state.maxRounds) { state.stopReason = 'round limit'; break; }
      const blocking = blockingIds(statuses);
      const deadlock = isDeadlock(previousBlocking, blocking);
      previousBlocking = blocking;
      if (deadlock) {
        // Same blocking set two rounds running: a human-shaped call is needed even
        // in auto mode, so the moderator is asked for a note.
        state.deadlocks = [...(state.deadlocks ?? []), { round, blocking }];
        log(`deadlock: same blocking set ${blocking.join(', ')} two rounds running`);
      }
      if (opt.mode === 'active' || deadlock) {
        const path = join(runDir, 'moderator', `r${round}.md`);
        state.status = 'awaiting_moderator'; state.waitingFor = path; state.moderatorReason = deadlock ? 'deadlock' : 'active'; save();
        const note = await waitForFile(path, waitMs, { signal });
        delete state.waitingFor;
        if (note === null) { state.stopReason = 'moderator timeout'; break; }
        moderatorNote = consumeNotes(round);
      } else moderatorNote = consumeNotes(round);
      if (moderatorNote?.trim().split('\n')[0].trim().toUpperCase() === 'STOP') { state.stopReason = 'moderator stopped'; break; }
    }
    delete state.waitingFor;
    state.stopReason ??= 'round limit';
    checkAbort();
    if (!opt['no-veto']) {
      const path = join(runDir, 'synthesis.md');
      state.status = 'awaiting_synthesis'; state.waitingFor = path; save();
      const synthesis = await waitForFile(path, waitMs, { signal });
      delete state.waitingFor;
      if (synthesis === null) warn('no synthesis written; veto round skipped');
      else {
        state.status = 'veto'; scope = 'veto'; save();
        const finalPositions = ids.map(id => ({ agent: id, round: latest[id]?.round ?? null, status: latest[id]?.status ?? null,
          lastKnownStatus: state.agents[id].lastReplyStatus ?? null, health: state.agents[id], text: latest[id]?.text ?? 'No completed reply' }));
        const context = { result: state.result, degradedAgents: state.degradedAgents, warnings: state.warnings, finalPositions };
        // Panel overview in the documented per-agent shape, so a veto message shows
        // every agent's status and its own reply text.
        const panel = ids.map(id => ({ label: registry[id].label ?? id, prefix: id.toUpperCase(),
          status: latest[id]?.status ?? null, state: participants[id]?.state.dropped ? 'dropped' : 'live',
          text: latest[id]?.text ?? null }));
        const votes = await Promise.all(live().map(async id => {
          try {
            const { text, stopReason } = await participants[id].ask(vetoPrompt({ synthesis, prefix: id.toUpperCase(), context, panel }), turnMs);
            atomicWrite(join(runDir, 'veto', `${id}.md`), text);
            const s = parseStatus(text);
            return { agent: id, approve: stopReason === 'end_turn' && s.parsed && s.stance === 'converged' && s.blocking.length === 0, stopReason, ...s };
          } catch (error) { warn(`${id} veto failed: ${error.message}`); return { agent: id, approve: null, error: error.message }; }
        }));
        checkAbort();
        atomicWrite(join(runDir, 'veto.json'), JSON.stringify(votes, null, 2));
        state.veto = votes;
        if (live().length < 2) throw new Error('fewer than 2 agents remain after veto recovery');
      }
    }
    state.status = 'done';
    // SKILL.md: `result` is consensus, no_consensus or degraded.
    if (state.result !== 'degraded') state.result = /^consensus:/.test(state.stopReason ?? '') ? 'consensus' : 'no_consensus';
  } catch (error) {
    state.status = signal?.aborted ? 'interrupted' : 'failed';
    state.stopReason = error.message;
    state.result = 'degraded';
    throw error;
  } finally {
    signal?.removeEventListener('abort', interrupt);
    const closed = await Promise.allSettled(Object.values(participants).map(p => p.close()));
    await interruptCleanup;
    closed.forEach(result => { if (result.status === 'rejected') { state.status = 'failed'; state.result = 'degraded'; state.stopReason = `cleanup failed: ${result.reason.message}`; warn(state.stopReason); } });
    delete state.waitingFor;
    checkEdits('after veto/cleanup');
    state.finishedAt = now(); save();
    atomicWrite(join(runDir, 'result.json'), JSON.stringify({ status: state.status, result: state.result, stopReason: state.stopReason,
      degradedAgents: state.degradedAgents, warnings: state.warnings, editCoverage: state.editDetection.checks.at(-1)?.coverage, agents: state.agents }, null, 2));
  }
  if (state.status === 'failed') throw new Error(state.stopReason ?? 'cleanup failed');
  return state;
}

export async function doctor(ids, { registry = REGISTRY, signal, cwd = process.cwd(), config } = {}) {
  registry = withModelConfig(registry, loadModelConfig(cwd, config));
  const rows = [];
  for (const id of ids) {
    if (!Object.hasOwn(registry, id) || id.startsWith('_')) throw new Error(`unknown agent ${id}`);
    const row = { agent: id };
    for (const transport of ['acp', 'headless']) {
      const agent = new (transport === 'acp' ? AcpAgent : HeadlessAgent)(id, registry[id], cwd, () => {});
      const abort = () => { void agent.close().catch(() => {}); };
      signal?.addEventListener('abort', abort, { once: true });
      try {
        signal?.throwIfAborted(); await agent.start();
        const reply = await agent.ask('Reply exactly OK. Do not use tools or change files.', 60_000);
        row[transport] = reply.stopReason === 'end_turn' && reply.text.trim() === 'OK' ? 'prompt OK' : 'FAIL: unexpected probe reply';
      } catch (error) { row[transport] = `FAIL: ${error.message}`; }
      finally { signal?.removeEventListener('abort', abort); await agent.close(); }
    }
    rows.push(row);
  }
  return rows;
}

export async function main(argv = process.argv.slice(2), dependencies = {}) {
  process.env.PATH = `${join(HERE, 'node_modules', '.bin')}:${process.env.PATH}`;
  const options = Object.fromEntries(Object.entries(DEFAULTS).map(([key, value]) => [key, { type: typeof value === 'boolean' ? 'boolean' : 'string', default: value }]));
  for (const key of ['brief', 'run-dir', 'roles', 'config', 'models', 'registry']) options[key] = { type: 'string' };
  options.json = { type: 'boolean', default: false };
  options.interactive = { type: 'boolean', default: false };
  const { positionals, values } = parseArgs({ args: argv, allowPositionals: true, options });
  if (positionals[0] !== 'setup' && (values.models || values.interactive)) throw new Error('Use setup --models to save model choices before running');
  const controller = new AbortController();
  const handlers = Object.fromEntries(['SIGINT', 'SIGTERM'].map(name => [name, () => controller.abort(new Error(`interrupted by ${name}`))]));
  for (const [name, handler] of Object.entries(handlers)) process.on(name, handler);
  try {
    if (positionals[0] === 'setup') {
      const { parseModelSelections } = await import('./setup.mjs');
      const interactive = values.interactive || (!values.json && !values.models && !!process.stdin.isTTY);
      if (interactive && !process.stdin.isTTY && !dependencies.choose) throw new Error('Interactive setup needs a terminal; use --json then --models agent=model-id');
      const report = await setup({ ids: values.agents.split(',').map(id => id.trim()).filter(Boolean), cwd: values.cwd,
        path: values.config, selections: parseModelSelections(values.models), interactive, signal: controller.signal }, { registry: REGISTRY, ...dependencies });
      console.log(JSON.stringify(report, null, 2));
      return report;
    }
    // An injected registry (tests, embedding) wins over the file on disk.
    const loaded = dependencies.registry ?? (values.registry ? JSON.parse(readFileSync(values.registry, 'utf8')) : REGISTRY);
    if (positionals[0] === 'run') return await run({ ...values, registry: loaded }, { ...dependencies, signal: controller.signal });
    if (positionals[0] === 'doctor') {
      const ids = (positionals[1] ?? values.agents).split(',').map(s => s.trim()).filter(Boolean);
      console.log(JSON.stringify(await doctor(ids, { ...dependencies, registry: loaded, signal: controller.signal, cwd: values.cwd, config: values.config }), null, 2));
      return;
    }
    throw new Error('usage: roundtable.mjs run --brief FILE --run-dir DIR [options] | doctor [a,b] | setup --agents a,b [--json | --models a=model-id,b=model-id] [--config FILE]');
  } finally { for (const [name, handler] of Object.entries(handlers)) process.off(name, handler); }
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { console.error(error.stack ?? error); process.exitCode = 1; });
}
