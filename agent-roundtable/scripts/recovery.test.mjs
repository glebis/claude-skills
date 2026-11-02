import test from 'node:test';
import assert from 'node:assert/strict';
import { Participant } from './recovery.mjs';
const success = text => ({ text, stopReason: 'end_turn' });
function harness(plans, options = {}) {
  const created = [], events = [], attempts = [];
  const participant = new Participant({ id: 'fake', initialTransport: 'acp', onUpdate: state => events.push(state), onAttempt: event => attempts.push(event), ...options,
    factory(transport, { history }) {
      const plan = plans.shift(); assert.ok(plan, 'recovery exceeded configured ladder');
      const record = { transport, history, prompts: [], closed: false }; created.push(record);
      return { async start() { if (plan.startError) throw new Error(plan.startError); }, async ask(prompt) { record.prompts.push(prompt); const result = plan.turns.shift(); if (result instanceof Error) throw result; return result; }, async close() { record.closed = true; } };
    } });
  return { participant, created, events, attempts };
}
test('ACP restart then headless then drop after exactly two recovery failures', async () => {
  const h = harness([{ turns: [new Error('crash')] }, { turns: [new Error('restart failed')] }, { turns: [new Error('fallback failed')] }]);
  await h.participant.start(); await assert.rejects(h.participant.ask('task', 100), /dropped/);
  assert.deepEqual(h.created.map(x => x.transport), ['acp', 'acp', 'headless']);
  assert.ok(h.created.every(x => x.closed));
  assert.equal(h.participant.state.failedAttempts, 3); assert.equal(h.participant.state.recoveryFailures, 2);
  assert.equal(h.participant.state.failedTurns, 3); assert.equal(h.participant.state.dropped, true);
  assert.equal(h.participant.state.degraded, true); assert.equal(h.participant.state.ok, false);
  assert.equal(h.attempts.length, 3); assert.equal(h.participant.history.length, 0);
});
test('startup failures use the same finite recovery ladder', async () => {
  const h = harness([{ startError: 'initial' }, { startError: 'restart' }, { startError: 'headless' }]);
  await assert.rejects(h.participant.start(), /dropped/);
  assert.deepEqual(h.created.map(x => x.transport), ['acp', 'acp', 'headless']);
  assert.equal(h.participant.state.recoveryFailures, 2); assert.equal(h.participant.state.failedTurns, 0);
  assert.ok(h.attempts.every(x => x.phase === 'startup'));
});
test('restart reconstructs completed history; interrupted prompt is included once', async () => {
  const failed = Object.assign(new Error('crash'), { partialText: 'INCOMPLETE_SECRET' });
  const h = harness([{ turns: [success('accepted reply'), failed] }, { turns: [new Error('restart broke')] }, { turns: [success('recovered')] }]);
  await h.participant.start(); await h.participant.ask('completed task', 100); await h.participant.ask('interrupted task', 100);
  assert.deepEqual(h.created[1].history, [{ prompt: 'completed task', reply: 'accepted reply' }]);
  const reconstructed = h.created[1].prompts[0];
  assert.ok(reconstructed.includes('accepted reply')); assert.equal(reconstructed.split('interrupted task').length - 1, 1);
  assert.ok(!reconstructed.includes('INCOMPLETE_SECRET'));
  assert.deepEqual(h.created[2].history, h.created[1].history);
  assert.deepEqual(h.created[2].prompts, ['interrupted task']);
  assert.deepEqual(h.participant.history, [{ prompt: 'completed task', reply: 'accepted reply' }, { prompt: 'interrupted task', reply: 'recovered' }]);
  assert.equal(h.participant.state.failedAttempts, 2); assert.equal(h.participant.state.recoveryFailures, 1);
});
test('success does not reset recovery budget', async () => {
  const h = harness([{ turns: [new Error('one')] }, { turns: [success('ok'), new Error('two')] }, { turns: [success('ok again'), new Error('three')] }]);
  await h.participant.start(); await h.participant.ask('a', 100); await h.participant.ask('b', 100);
  await assert.rejects(h.participant.ask('c', 100), /dropped/);
  assert.equal(h.created.length, 3); assert.equal(h.participant.state.failedAttempts, 3); assert.equal(h.participant.state.recoveryFailures, 2);
});
test('non-end_turn response triggers recovery and cannot enter accepted history', async () => {
  const h = harness([{ turns: [{ text: 'truncated', stopReason: 'max_tokens' }] }, { turns: [success('complete')] }]);
  await h.participant.start(); assert.equal((await h.participant.ask('a', 100)).text, 'complete');
  assert.equal(h.attempts[0].stopReason, 'max_tokens'); assert.deepEqual(h.participant.history, [{ prompt: 'a', reply: 'complete' }]);
});
test('abort prevents transport replacement or retry', async () => {
  const controller = new AbortController();
  const h = harness([{ turns: [new Error('crash')] }], { signal: controller.signal, onAttempt() { controller.abort(new Error('user cancelled')); } });
  await h.participant.start(); await assert.rejects(h.participant.ask('a', 100), /user cancelled/);
  assert.equal(h.created.length, 1); assert.equal(h.created[0].closed, true);
});

test('default headless has one fresh-process recovery, then drops without entering ACP', async () => {
  const h = harness([{ turns: [new Error('native failed')] }, { turns: [success('rebuilt'), new Error('retry failed')] }], { initialTransport: 'headless' });
  await h.participant.start(); await h.participant.ask('a', 100);
  await assert.rejects(h.participant.ask('b', 100), /dropped/);
  assert.deepEqual(h.created.map(x => x.transport), ['headless', 'headless']);
  assert.equal(h.participant.state.failedAttempts, 2); assert.equal(h.participant.state.recoveryFailures, 1);
  assert.equal(h.participant.state.acpRestartsUsed, 0);
});

test('cleanup failure never launches a replacement and remains owned for final cleanup', async () => {
  let created = 0, closes = 0;
  const p = new Participant({ id: 'unsafe', initialTransport: 'acp', factory() {
    created++; return { async start() {}, async ask() { throw new Error('crash'); }, async close() { closes++; throw new Error('cannot terminate'); } };
  } });
  await p.start(); await assert.rejects(p.ask('task', 100), /cannot terminate/);
  assert.equal(created, 1); assert.equal(p.state.dropped, true);
  await assert.rejects(p.close(), /cleanup failed/); assert.equal(closes, 2);
});
