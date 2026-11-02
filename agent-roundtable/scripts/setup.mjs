import { existsSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createInterface } from 'node:readline/promises';
import { AcpAgent } from './acp-agent.mjs';
import { atomicWrite } from './safeguards.mjs';

export const configPath = (cwd, path) => path ? resolve(cwd, path) : join(resolve(cwd), '.roundtable.json');
export function loadModelConfig(cwd, path) {
  const file = configPath(cwd, path);
  if (!existsSync(file)) {
    if (path) throw new Error(`Configuration does not exist: ${file}`);
    return { version: 1, agents: {} };
  }
  const config = JSON.parse(readFileSync(file, 'utf8'));
  if (config.version !== 1 || !config.agents || typeof config.agents !== 'object' || Array.isArray(config.agents)) throw new Error(`Invalid model configuration: ${file}`);
  for (const [id, value] of Object.entries(config.agents)) {
    if (!/^[a-zA-Z0-9_-]+$/.test(id) || !value || typeof value !== 'object' || Array.isArray(value) ||
      ![null, undefined].includes(value.model) && (typeof value.model !== 'string' || !value.model.trim()) ||
      value.modelConfigId !== undefined && (typeof value.modelConfigId !== 'string' || !value.modelConfigId.trim())) throw new Error(`Invalid model selection for ${id}`);
  }
  return config;
}
export function withModelConfig(registry, config) {
  const result = { ...registry };
  for (const [id, selection] of Object.entries(config.agents)) {
    if (!Object.hasOwn(registry, id) || id.startsWith('_')) throw new Error(`Model configuration names unknown agent: ${id}`);
    result[id] = { ...registry[id], model: selection.model ?? undefined, modelConfigId: selection.modelConfigId };
  }
  return result;
}
export function parseModelSelections(text) {
  if (!text) return {};
  const selections = {};
  for (const assignment of text.split(',')) {
    const index = assignment.indexOf('=');
    const id = assignment.slice(0, index).trim(), model = assignment.slice(index + 1).trim();
    if (index < 1 || !/^[a-zA-Z0-9_-]+$/.test(id) || !model || Object.hasOwn(selections, id)) throw new Error('Use --models agent=model-id,other=model-id; @default clears a selection');
    selections[id] = model === '@default' ? null : model;
  }
  return selections;
}

// Discovery creates sessions but sends no inference prompt. Applications may
// inject choose() (e.g. a cenno panel); the terminal CLI uses a numbered menu.
export async function setup({ ids, cwd, path, selections = {}, interactive = false, signal }, { registry, createAgent, choose } = {}) {
  cwd = resolve(cwd);
  const file = configPath(cwd, path);
  // setup may create an explicitly named config for the first time.
  const existing = existsSync(file) ? loadModelConfig(cwd, file) : { version: 1, agents: {} };
  const config = { ...existing, agents: { ...existing.agents } };
  if (new Set(ids).size !== ids.length || !ids.length) throw new Error('Select distinct agents for setup');
  for (const id of [...ids, ...Object.keys(selections)]) if (!ids.includes(id) || !Object.hasOwn(registry, id) || id.startsWith('_')) throw new Error(`Unknown or unselected setup agent: ${id}`);
  const agents = {};
  for (const id of ids) {
    signal?.throwIfAborted();
    const cfg = { ...registry[id] };
    delete cfg.model;
    cfg.modelConfigId = existing.agents[id]?.modelConfigId ?? cfg.modelConfigId;
    const agent = createAgent ? createAgent(id, cfg) : new AcpAgent(id, cfg, cwd);
    const abort = () => { void agent.close().catch(() => {}); };
    signal?.addEventListener('abort', abort, { once: true });
    try {
      signal?.throwIfAborted(); await agent.start(); signal?.throwIfAborted();
      agents[id] = { ...agent.getModelCatalog(), savedModel: config.agents[id]?.model ?? null };
    } catch (error) {
      if (signal?.aborted) throw error;
      agents[id] = { supported: false, models: [], currentModel: null, configId: null, error: error.message };
    } finally { signal?.removeEventListener('abort', abort); await agent.close(); }
  }
  let changes = { ...selections };
  if (interactive) {
    const menu = choose ?? terminalChooser;
    for (const id of ids) if (agents[id].supported) changes[id] = await menu(id, agents[id], { signal });
  }
  for (const [id, model] of Object.entries(changes)) {
    const catalog = agents[id];
    if (model !== null && (catalog.error || !catalog.supported || !catalog.models.some(option => option.id === model))) throw new Error(`${id}: model ${JSON.stringify(model)} was not advertised by ACP${catalog.error ? ` (${catalog.error})` : ''}; configuration unchanged`);
    config.agents[id] = model === null ? { model: null } : { model, modelConfigId: catalog.configId };
  }
  signal?.throwIfAborted();
  const saved = Object.keys(changes).length > 0;
  if (saved) atomicWrite(file, JSON.stringify(config, null, 2) + '\n');
  return { configPath: file, saved, agents, configuration: config, note: 'Discovery only: no model prompt sent. Live inference and native-resume behavior are not verified by setup.' };
}
async function terminalChooser(id, catalog, { signal }) {
  const rl = createInterface({ input: process.stdin, output: process.stderr });
  try {
    console.error(`\n${id}: current ${catalog.currentModel ?? 'unknown'}, saved ${catalog.savedModel ?? 'agent default'}`);
    console.error('  0. Use agent default');
    catalog.models.forEach((model, index) => console.error(`  ${index + 1}. ${model.name} (${model.id})`));
    for (;;) {
      const answer = (await rl.question('Choose a model number (Enter keeps the saved choice): ', { signal })).trim();
      if (!answer) return catalog.savedModel;
      const number = Number(answer);
      if (/^\d+$/.test(answer) && number >= 0 && number <= catalog.models.length) return number === 0 ? null : catalog.models[number - 1].id;
      console.error('Choose a listed number.');
    }
  } finally { rl.close(); }
}
