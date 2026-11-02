import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
const mode = process.argv[2];
if (mode === 'ignore-term') process.on('SIGTERM', () => {});
const send = value => process.stdout.write(`${JSON.stringify(value)}\n`);
const chunk = text => send({ jsonrpc: '2.0', method: 'session/update', params: { sessionId: 'fake', update: { sessionUpdate: 'agent_message_chunk', content: { type: 'text', text } } } });
let selectedModel = 'fast';
const configOptions = () => [{ id: 'model', name: 'Model', category: 'model', type: 'select', currentValue: selectedModel,
  options: [{ group: 'provider', name: 'Provider', options: [{ value: 'fast', name: 'Fast' }, { value: 'deep', name: 'Deep', description: 'More capable' }] }] }];
let pending;
createInterface({ input: process.stdin }).on('line', line => {
  const message = JSON.parse(line);
  const reply = result => send({ jsonrpc: '2.0', id: message.id, result });
  if (message.method === 'initialize') reply({ protocolVersion: 1, agentCapabilities: {}, agentInfo: { name: 'fake', version: '1' } });
  if (message.method === 'session/new') reply({ sessionId: 'fake', ...(mode.startsWith('models') ? { configOptions: configOptions() } : {}) });
  if (message.method === 'session/set_config_option') {
    if (mode === 'models-hang') return;
    if (mode !== 'models-mismatch') selectedModel = message.params.value;
    reply({ configOptions: configOptions() });
  }
  if (message.method === 'session/prompt') {
    if (mode === 'crash') return process.exit(23);
    if (mode === 'eof') return process.stdout.end();
    if (mode === 'hang' || mode === 'ignore-term' || mode === 'cancel') { pending = reply; return; }
    if (mode === 'late') { pending = reply; setTimeout(() => { chunk('LATE'); reply({ stopReason: 'end_turn' }); }, 120); return; }
    if (mode === 'error') return send({ jsonrpc: '2.0', id: message.id, error: { code: -32603, message: 'credentials expired' } });
    if (mode === 'descendant') {
      const child = spawn(process.execPath, ['-e', "process.on('SIGTERM', () => {}); setInterval(() => {}, 1000)"], { stdio: 'ignore' });
      setTimeout(() => { chunk(String(child.pid)); reply({ stopReason: 'end_turn' }); }, 80); return;
    }
    if (mode === 'models-update') { selectedModel = 'deep'; send({ jsonrpc: '2.0', method: 'session/update', params: { sessionId: 'fake', update: { sessionUpdate: 'config_option_update', configOptions: configOptions() } } }); }
    if (mode.startsWith('models')) { chunk(selectedModel); reply({ stopReason: 'end_turn' }); return; }
    chunk(mode === 'audit' ? 'Audit\n```roundtable-status\n{"stance":"converged","blocking":[],"new_issues":[],"resolved":[]}\n```' : 'CLEAN'); reply({ stopReason: 'end_turn' });
  }
  if (message.method === 'session/cancel' && mode === 'cancel') pending?.({ stopReason: 'cancelled' });
});
