import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setup, loadModelConfig, withModelConfig, parseModelSelections, configPath } from './setup.mjs';
import { AcpAgent } from './acp-agent.mjs';
const temp = () => mkdtempSync(join(tmpdir(), 'roundtable-setup-test-'));
const catalog = { supported: true, configId: 'model', currentModel: 'fast', models: [{ id: 'fast', name: 'Fast' }, { id: 'deep', name: 'Deep' }] };
function fake(registry = { a: {}, b: {} }) {
  const agents = [];
  return { agents, deps: { registry, createAgent(id) {
    const record = { id, closed: false, prompts: 0 }; agents.push(record);
    return { async start() {}, getModelCatalog: () => catalog, async ask() { record.prompts++; throw new Error('setup must not prompt'); }, async close() { record.closed = true; } };
  } } };
}
test('setup discovers without inference or modifying files', async () => {
  const cwd = temp(), f = fake();
  const report = await setup({ ids: ['a', 'b'], cwd }, f.deps);
  assert.equal(report.saved, false); assert.equal(existsSync(configPath(cwd)), false);
  assert.deepEqual(report.agents.a.models, catalog.models);
  assert.ok(f.agents.every(a => a.closed && a.prompts === 0));
});
test('selections persist atomically, retain other agents, and @default clears override', async () => {
  const cwd = temp(), f = fake();
  await setup({ ids: ['a', 'b'], cwd, selections: { a: 'deep', b: 'fast' } }, f.deps);
  assert.deepEqual(loadModelConfig(cwd).agents.a, { model: 'deep', modelConfigId: 'model' });
  await setup({ ids: ['a'], cwd, selections: parseModelSelections('a=@default') }, f.deps);
  const config = loadModelConfig(cwd);
  assert.equal(config.agents.a.model, null); assert.equal(config.agents.b.model, 'fast');
  const registry = withModelConfig({ a: { acp: ['fake'] }, b: {} }, config);
  assert.equal(registry.a.model, undefined); assert.equal(registry.b.model, 'fast');
});
test('invalid selections do not partially overwrite saved configuration', async () => {
  const cwd = temp(), f = fake();
  await setup({ ids: ['a'], cwd, selections: { a: 'fast' } }, f.deps);
  const before = readFileSync(configPath(cwd), 'utf8');
  await assert.rejects(setup({ ids: ['a', 'b'], cwd, selections: { a: 'deep', b: 'not-advertised' } }, f.deps), /not advertised/);
  assert.equal(readFileSync(configPath(cwd), 'utf8'), before);
});
test('custom config starts independently and read failures are explicit', async () => {
  const cwd = temp(), f = fake();
  await setup({ ids: ['a'], cwd, selections: { a: 'deep' } }, f.deps);
  const report = await setup({ ids: ['b'], cwd, path: 'other.json', selections: { b: 'fast' } }, f.deps);
  assert.deepEqual(Object.keys(report.configuration.agents), ['b']);
  assert.throws(() => loadModelConfig(cwd, 'missing.json'), /does not exist/);
  writeFileSync(join(cwd, 'broken.json'), '{');
  assert.throws(() => loadModelConfig(cwd, 'broken.json'));
});
test('interactive selection uses injected chooser and rejects unsupported catalogs', async () => {
  const cwd = temp(), f = fake();
  const report = await setup({ ids: ['a'], cwd, interactive: true }, { ...f.deps, choose: async (id, options) => {
    assert.equal(id, 'a'); assert.equal(options.currentModel, 'fast'); return 'deep';
  } });
  assert.equal(report.saved, true); assert.equal(report.configuration.agents.a.model, 'deep');
  await assert.rejects(setup({ ids: ['a'], cwd, selections: { a: 'deep' } }, { registry: { a: {} }, createAgent: () => ({ async start() {}, getModelCatalog: () => ({ supported: false, models: [] }), async close() {} }) }), /not advertised/);
});
test('real SDK setup discovers grouped models and closes without prompting', async () => {
  const cwd = temp(), owned = [];
  const fixture = fileURLToPath(new URL('./fixtures/fake-acp.mjs', import.meta.url));
  const report = await setup({ ids: ['a'], cwd, selections: { a: 'deep' } }, { registry: { a: {} }, createAgent(id) {
    const agent = new AcpAgent(id, { acp: [process.execPath, fixture, 'models'] }, cwd, () => {}, { initializeMs: 1000, closeGraceMs: 30 });
    agent.ask = () => { throw new Error('setup must not send a prompt'); };
    owned.push(agent); return agent;
  } });
  assert.equal(report.saved, true); assert.equal(report.agents.a.currentModel, 'fast');
  assert.equal(report.configuration.agents.a.model, 'deep');
  for (const agent of owned) assert.throws(() => process.kill(agent.proc.pid, 0), { code: 'ESRCH' });
});
test('discovery errors close agents, cannot silently save a model, and abort never writes', async () => {
  const cwd = temp(); let closed = 0;
  const deps = { registry: { a: {} }, createAgent: () => ({ async start() { throw new Error('auth unavailable'); }, async close() { closed++; } }) };
  const report = await setup({ ids: ['a'], cwd }, deps);
  assert.match(report.agents.a.error, /auth unavailable/); assert.equal(closed, 1);
  await assert.rejects(setup({ ids: ['a'], cwd, selections: { a: 'deep' } }, deps), /configuration unchanged/);
  const signal = AbortSignal.abort(new Error('cancel setup'));
  await assert.rejects(setup({ ids: ['a'], cwd, selections: { a: 'deep' }, signal }, deps), /cancel setup/);
  assert.equal(existsSync(configPath(cwd)), false);
});
test('selection parser and config reject duplicates, unknown agents and invalid schemas', () => {
  assert.deepEqual(parseModelSelections('a=provider/model,b=default'), { a: 'provider/model', b: 'default' });
  assert.throws(() => parseModelSelections('a=deep,a=fast'), /Use --models/);
  assert.throws(() => withModelConfig({}, { agents: { missing: { model: 'deep' } } }), /unknown agent/);
  const cwd = temp(); writeFileSync(configPath(cwd), JSON.stringify({ version: 2, agents: {} }));
  assert.throws(() => loadModelConfig(cwd), /Invalid model configuration/);
});
