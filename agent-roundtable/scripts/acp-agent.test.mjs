import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { AcpAgent } from './acp-agent.mjs';
const fixture = fileURLToPath(new URL('./fixtures/fake-acp.mjs', import.meta.url));
const make = mode => new AcpAgent('fake', { acp: [process.execPath, fixture, mode] }, process.cwd(), () => {}, { initializeMs: 2000, cancelGraceMs: 180, closeGraceMs: 50 });
const gone = agent => assert.throws(() => process.kill(agent.proc.pid, 0), { code: 'ESRCH' });
for (const mode of ['late', 'hang', 'ignore-term', 'cancel']) {
  test(`timeout ${mode}: old session unavailable, cleanup completed, replacement clean`, { timeout: 5000 }, async t => {
    const agent = make(mode); t.after(() => agent.close()); await agent.start();
    await assert.rejects(agent.ask('first', 30), /timed out/);
    await assert.rejects(agent.ask('next', 100), /unavailable/);
    gone(agent);
    const replacement = make('ok'); t.after(() => replacement.close()); await replacement.start();
    assert.deepEqual(await replacement.ask('next', 1000), { text: 'CLEAN', stopReason: 'end_turn' });
  });
}
for (const mode of ['crash', 'eof']) test(`${mode} rejects promptly and leaves no process`, { timeout: 5000 }, async t => {
  const agent = make(mode); t.after(() => agent.close()); await agent.start();
  const before = Date.now(); await assert.rejects(agent.ask('first', 2000));
  assert.ok(Date.now() - before < 1500); gone(agent);
});
test('real SDK propagates original prompt rejection', { timeout: 5000 }, async t => {
  const agent = make('error'); t.after(() => agent.close()); await agent.start();
  await assert.rejects(agent.ask('first', 1000), /credentials expired/); gone(agent);
});
test('close escalates when SIGTERM ignored and is idempotent', { timeout: 5000 }, async () => {
  const agent = make('ignore-term'); await agent.start();
  await Promise.all([agent.close(), agent.close()]); gone(agent);
});
test('concurrent prompt cannot create a second collector', { timeout: 5000 }, async t => {
  const agent = make('hang'); t.after(() => agent.close()); await agent.start();
  const first = agent.ask('first', 30);
  await assert.rejects(agent.ask('second', 100), /already collecting/);
  await assert.rejects(first, /timed out/); gone(agent);
});
test('spawn error is reported and close remains safe', { timeout: 5000 }, async () => {
  const agent = new AcpAgent('missing', { acp: ['/definitely/not/a/roundtable-agent'] }, process.cwd());
  await assert.rejects(agent.start(), { code: 'ENOENT' }); await agent.close();
});
test('close terminates a descendant that ignores SIGTERM', { timeout: 5000 }, async t => {
  const agent = make('descendant'); t.after(() => agent.close()); await agent.start();
  const { text } = await agent.ask('spawn child', 1000); const childPid = Number(text);
  assert.ok(childPid > 0); process.kill(childPid, 0);
  await agent.close(); gone(agent);
  for (let i = 0; i < 50; i++) {
    try { process.kill(childPid, 0); } catch (error) { if (error.code === 'ESRCH') return; throw error; }
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  assert.fail(`descendant ${childPid} remains after close`);
});

const makeModels = (mode = 'models', cfg = {}, options = {}) => new AcpAgent('models', { acp: [process.execPath, fixture, mode], ...cfg }, process.cwd(), () => {}, { initializeMs: 500, closeGraceMs: 30, ...options });
test('discovers grouped model choices without prompting or changing default', async t => {
  const agent = makeModels(); t.after(() => agent.close()); await agent.start();
  assert.deepEqual(agent.getModelCatalog(), { supported: true, configId: 'model', currentModel: 'fast', models: [
    { id: 'fast', name: 'Fast' }, { id: 'deep', name: 'Deep', description: 'More capable' },
  ] });
  assert.equal(agent.model, 'fast');
});
test('configured model is applied before first prompt and public setter updates effective model', async t => {
  const agent = makeModels('models', { model: 'deep' }); t.after(() => agent.close()); await agent.start();
  assert.equal((await agent.ask('first', 1000)).text, 'deep');
  await agent.setModel('fast'); assert.equal(agent.model, 'fast');
});
for (const [mode, cfg, pattern] of [
  ['models', { model: 'unknown' }, /unsupported model/],
  ['ok', { model: 'deep' }, /does not advertise/],
  ['models-mismatch', { model: 'deep' }, /mismatch/],
  ['models-hang', { model: 'deep' }, /timed out/],
]) test(`model setup failure ${mode} ${JSON.stringify(cfg)} closes child`, async () => {
  const agent = makeModels(mode, cfg); await assert.rejects(agent.start(), pattern); gone(agent);
});
test('ambiguous model controls need explicit config id', () => {
  const agent = makeModels();
  agent.configOptions = ['a', 'b'].map(id => ({ id, category: 'model', type: 'select', currentValue: 'fast', options: [{ value: 'fast', name: 'Fast' }] }));
  assert.throws(() => agent.getModelCatalog(), /multiple model controls/);
  agent.cfg.modelConfigId = 'b'; assert.equal(agent.getModelCatalog().configId, 'b');
});

test('config option notifications refresh effective model', async t => {
  const agent = makeModels('models-update'); t.after(() => agent.close()); await agent.start();
  await agent.ask('update', 1000); assert.equal(agent.model, 'deep');
});
test('model setup interrupted by close cannot report success', async () => {
  const agent = makeModels('models-hang', { model: 'deep' });
  const starting = agent.start();
  while (!agent.configuring) await new Promise(resolve => setTimeout(resolve, 5));
  await agent.close(); await assert.rejects(starting); gone(agent);
});
