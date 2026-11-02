import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, existsSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync, spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { AcpAgent } from './acp-agent.mjs';
import { setTimeout as delay } from 'node:timers/promises';
import { run } from './roundtable.mjs';
import { atomicWrite } from './safeguards.mjs';

function setup(agents = 'a,b') {
  const cwd = mkdtempSync(join(tmpdir(), 'roundtable-run-test-'));
  const git = args => execFileSync('git', args, { cwd, stdio: 'ignore' });
  git(['init']); git(['config', 'user.email', 'test@localhost']); git(['config', 'user.name', 'test']);
  writeFileSync(join(cwd, 'target'), 'original'); git(['add', 'target']); git(['commit', '-m', 'fixture']);
  const runDir = join(cwd, 'run'); mkdirSync(runDir); const brief = join(runDir, 'brief.md'); writeFileSync(brief, 'Audit target');
  const registry = Object.fromEntries(agents.split(',').map(id => [id, { label: id, defaultTransport: 'acp' }]));
  return { cwd, runDir, registry, options: { cwd, brief, 'run-dir': runDir, agents, rounds: '3', 'min-rounds': '2', 'no-veto': true, 'wait-timeout': '2', 'turn-timeout': '1' } };
}
const answer = (stance = 'converged', blocking = []) => ({ text: 'Audit\n```roundtable-status\n' + JSON.stringify({ stance, blocking, new_issues: [], resolved: [] }) + '\n```', stopReason: 'end_turn' });
async function until(predicate, ms = 3000) { const deadline = Date.now() + ms; while (Date.now() < deadline) { if (predicate()) return; await delay(10); } throw new Error('test observer timed out'); }
const stateAt = s => JSON.parse(readFileSync(join(s.runDir, 'state.json'), 'utf8'));

test('runner completes rounds and veto, exposes peer positions, atomic outputs do not trip edit guard', async () => {
  const s = setup(); let vetoPrompt; let closes = 0;
  const work = run({ ...s.options, 'no-veto': false }, { registry: s.registry, createAgent(id) { return {
    async start() {}, async ask(prompt) { if (prompt.includes('final review')) vetoPrompt = prompt; return answer(); }, async close() { closes++; },
  }; } });
  await until(() => existsSync(join(s.runDir, 'state.json')) && stateAt(s).status === 'awaiting_synthesis');
  atomicWrite(join(s.runDir, 'synthesis.md'), 'Complete synthesis');
  const state = await work;
  assert.equal(state.status, 'done'); assert.equal(state.result, 'consensus'); assert.match(state.stopReason, /^consensus:/);
  assert.ok(vetoPrompt.includes('finalPositions')); assert.ok(vetoPrompt.includes('"agent":"a"')); assert.ok(vetoPrompt.includes('"round":2'));
  assert.ok(state.veto.every(vote => vote.approve)); assert.equal(closes, 2);
  assert.ok(!state.warnings.some(w => w.includes('content changed')));
  assert.equal(state.editDetection.checks.at(-1).phase, 'after veto/cleanup');
  assert.ok(stateAt(s).finishedAt);
});

test('runner records an ACP restart as recovery, not degradation, and preserves successful context', async () => {
  const s = setup(); const created = []; let count = 0;
  const state = await run(s.options, { registry: s.registry, createAgent(id, transport, { history }) {
    const generation = id === 'a' ? count++ : 0; let calls = 0;
    const entry = { id, generation, history, prompts: [] }; created.push(entry);
    return { async start() {}, async ask(prompt) { calls++; entry.prompts.push(prompt);
      if (id === 'a' && generation === 0 && calls === 2) throw new Error('crash after first round'); return answer(); }, async close() {} };
  } });
  assert.equal(state.result, 'consensus'); assert.match(state.stopReason, /^consensus:/);
  assert.equal(state.agents.a.acpRestartsUsed, 1); assert.equal(state.agents.a.failedAttempts, 1);
  assert.equal(created.find(e => e.id === 'a' && e.generation === 1).history.length, 1);
  assert.ok(created.find(e => e.id === 'a' && e.generation === 1).prompts[0].includes('completed_turns'));
  const failure = JSON.parse(readFileSync(join(s.runDir, 'rounds', 'r2-a.attempt-1.json'), 'utf8'));
  assert.equal(failure.ok, false); assert.equal(failure.error, 'crash after first round');
});

test('dropped participant excluded from future consensus but retained in health and warnings', async () => {
  const s = setup('a,b,c'); const order = [];
  const state = await run(s.options, { registry: s.registry, createAgent(id, transport) { if (id === 'a') order.push(transport); return {
    async start() {}, async ask() { if (id === 'a') throw new Error('dead'); return answer(); }, async close() {},
  }; } });
  assert.deepEqual(order, ['acp', 'acp', 'headless']); assert.equal(state.agents.a.dropped, true);
  assert.equal(state.agents.a.failedAttempts, 3); assert.equal(state.agents.a.recoveryFailures, 2);
  assert.match(state.stopReason, /^degraded convergence:/); assert.ok(state.warnings.some(w => w.includes('a:')));
  const summary = JSON.parse(readFileSync(join(s.runDir, 'rounds', 'r2.summary.json'), 'utf8'));
  assert.deepEqual(summary.expectedAgents, ['b', 'c']);
});

test('fewer than two survivors fails and closes all started agents', async () => {
  const s = setup(); const closed = [];
  await assert.rejects(run(s.options, { registry: s.registry, createAgent(id, transport) { return {
    async start() {}, async ask() { if (id === 'a') throw new Error('dead'); return answer(); }, async close() { closed.push(`${id}:${transport}`); },
  }; } }), /fewer than 2/);
  assert.equal(stateAt(s).status, 'failed'); assert.equal(stateAt(s).result, 'degraded'); assert.ok(closed.includes('b:acp'));
});

test('auto deadlock pauses for moderator; late STOP is consumed', async () => {
  const s = setup();
  const work = run(s.options, { registry: s.registry, createAgent() { return { async start() {}, async ask() { return answer('open', ['ISSUE-1: still blocking']); }, async close() {} }; } });
  await until(() => existsSync(join(s.runDir, 'state.json')) && stateAt(s).status === 'awaiting_moderator');
  assert.equal(stateAt(s).round, 2); assert.equal(stateAt(s).moderatorReason, 'deadlock');
  atomicWrite(join(s.runDir, 'moderator', 'r2.md'), 'STOP\nHuman decision');
  assert.equal((await work).stopReason, 'moderator stopped');
});

test('veto edits detected after cleanup and non-end_turn cannot approve', async () => {
  const s = setup();
  const work = run({ ...s.options, 'no-veto': false }, { registry: s.registry, createAgent(id) { return {
    async start() {}, async ask(prompt) {
      if (prompt.includes('final review')) { writeFileSync(join(s.cwd, 'target'), 'changed by veto'); if (id === 'a') return { ...answer(), stopReason: 'cancelled' }; }
      return answer();
    }, async close() {},
  }; } });
  await until(() => existsSync(join(s.runDir, 'state.json')) && stateAt(s).status === 'awaiting_synthesis');
  atomicWrite(join(s.runDir, 'synthesis.md'), 'Draft');
  await assert.rejects(work, /fewer than 2 agents remain after veto/);
  assert.equal(stateAt(s).veto.find(v => v.agent === 'a').approve, null);
  assert.ok(stateAt(s).warnings.some(w => w.includes('content changed')));
});

test('abort interrupts synthesis wait, records interrupted state and closes agents', async () => {
  const s = setup(); const controller = new AbortController(); let closed = 0;
  const work = run({ ...s.options, 'no-veto': false }, { registry: s.registry, signal: controller.signal, createAgent() { return {
    async start() {}, async ask() { return answer(); }, async close() { closed++; },
  }; } });
  await until(() => existsSync(join(s.runDir, 'state.json')) && stateAt(s).status === 'awaiting_synthesis');
  controller.abort(new Error('test abort'));
  await assert.rejects(work, /abort/i); assert.equal(stateAt(s).status, 'interrupted'); assert.ok(closed >= 2);
});

test('fresh-run rejection happens before spawning or overwriting state', async () => {
  const s = setup(); const prior = '{"prior":true}'; writeFileSync(join(s.runDir, 'state.json'), prior); let created = false;
  await assert.rejects(run(s.options, { registry: s.registry, createAgent() { created = true; } }), /already used/);
  assert.equal(created, false); assert.equal(readFileSync(join(s.runDir, 'state.json'), 'utf8'), prior);
});


test('real SDK runner: three audit rounds plus veto, no live models or leftover processes', { timeout: 8000 }, async () => {
  const s = setup(); const owned = [];
  const fixture = fileURLToPath(new URL('./fixtures/fake-acp.mjs', import.meta.url));
  const work = run({ ...s.options, 'min-rounds': '3', 'no-veto': false }, { registry: s.registry, createAgent(id) {
    const agent = new AcpAgent(id, { acp: [process.execPath, fixture, 'audit'] }, s.cwd, () => {}, { initializeMs: 1000, cancelGraceMs: 50, closeGraceMs: 50 });
    owned.push(agent); return agent;
  } });
  await until(() => existsSync(join(s.runDir, 'state.json')) && stateAt(s).status === 'awaiting_synthesis');
  atomicWrite(join(s.runDir, 'synthesis.md'), 'Complete three-round audit synthesis');
  const state = await work;
  assert.equal(state.round, 3); assert.equal(state.rounds.length, 6); assert.equal(state.veto.length, 2);
  assert.ok(state.veto.every(v => v.approve));
  for (const agent of owned) assert.throws(() => process.kill(agent.proc.pid, 0), { code: 'ESRCH' });
});

for (const name of ['SIGINT', 'SIGTERM']) test(`CLI ${name} closes in-flight fake processes without recovery`, { timeout: 8000 }, async t => {
  const s = setup();
  const runnerUrl = new URL('./roundtable.mjs', import.meta.url).href;
  const acpUrl = new URL('./acp-agent.mjs', import.meta.url).href;
  const fixture = fileURLToPath(new URL('./fixtures/fake-acp.mjs', import.meta.url));
  const argv = ['run', '--brief', s.options.brief, '--run-dir', s.runDir, '--cwd', s.cwd, '--agents', 'a,b', '--transport', 'acp', '--no-veto'];
  const pidPath = join(s.runDir, 'agent-pids.txt');
  const code = `import {main} from ${JSON.stringify(runnerUrl)}; import {AcpAgent} from ${JSON.stringify(acpUrl)}; import {appendFileSync} from 'node:fs';
    try { await main(${JSON.stringify(argv)}, {registry:${JSON.stringify(s.registry)}, createAgent(id) {
      const agent = new AcpAgent(id,{acp:[process.execPath,${JSON.stringify(fixture)},'ignore-term']},${JSON.stringify(s.cwd)},()=>{},{initializeMs:1000,cancelGraceMs:30,closeGraceMs:50});
      const start=agent.start.bind(agent); agent.start=async()=>{await start();appendFileSync(${JSON.stringify(pidPath)},String(agent.proc.pid)+',');};return agent;
    }}); } catch(e) { process.exitCode=1; }`;
  const child = spawn(process.execPath, ['--input-type=module', '-e', code], { stdio: ['ignore', 'pipe', 'pipe'] });
  t.after(() => { if (child.exitCode === null) child.kill('SIGKILL'); });
  let stderr = ''; child.stderr.on('data', d => { stderr += d; });
  const done = new Promise(resolve => child.once('close', (code, signal) => resolve({ code, signal })));
  await until(() => existsSync(join(s.runDir, 'state.json')) && stateAt(s).status === 'debating');
  child.kill(name);
  const exit = await done;
  assert.equal(exit.code, 1, stderr); assert.equal(exit.signal, null);
  const state = stateAt(s); assert.equal(state.status, 'interrupted'); assert.equal(state.agents.a.failedAttempts, 0);
  const pids = readFileSync(pidPath, 'utf8').split(',').filter(Boolean).map(Number);
  for (const pid of pids) assert.throws(() => process.kill(pid, 0), { code: 'ESRCH' });
});

test('saved model choices apply to actual fake ACP sessions and appear in run state', async () => {
  const s = setup();
  const fixture = fileURLToPath(new URL('./fixtures/fake-acp.mjs', import.meta.url));
  writeFileSync(join(s.cwd, '.roundtable.json'), JSON.stringify({ version: 1, agents: { a: { model: 'deep', modelConfigId: 'model' }, b: { model: 'fast', modelConfigId: 'model' } } }));
  const registry = Object.fromEntries(['a', 'b'].map(id => [id, { label: id, defaultTransport: 'acp', acp: [process.execPath, fixture, 'models'] }]));
  const state = await run({ ...s.options, rounds: '1', 'min-rounds': '1' }, { registry });
  assert.equal(state.agents.a.requestedModel, 'deep'); assert.equal(state.agents.a.model, 'deep');
  assert.equal(state.agents.b.requestedModel, 'fast'); assert.equal(state.agents.b.model, 'fast');
  assert.equal(readFileSync(join(s.runDir, 'rounds', 'r1-a.md'), 'utf8'), 'deep');
});
