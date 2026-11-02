import test from 'node:test';
import assert from 'node:assert/strict';
import { HeadlessAgent, parseHeadlessOutput, substituteArgs } from './headless.mjs';

const fake = `
let input=''; process.stdin.setEncoding('utf8');
process.stdin.on('data', d=>input+=d);
process.stdin.on('end', ()=>{
 const [protocol, mode, session] = process.argv.slice(1);
 if(mode==='hang'){ process.on('SIGTERM',()=>{}); setInterval(()=>{},1000); return; }
 const id=session || 'explicit-native-id';
 const text=JSON.stringify({input,session:session || null});
 const stop=mode==='cancel'?'cancelled':'end_turn';
 const emit=e=>console.log(JSON.stringify(e));
 if(protocol==='codex') {emit({type:'thread.started',thread_id:id});emit({type:'item.completed',item:{type:'agent_message',text}});emit({type:'turn.completed'});}
 if(protocol==='claude') emit({type:'result',subtype:'success',session_id:id,result:text,stop_reason:stop});
 if(protocol==='cmd') {emit({type:'event',event:{type:'run_start'}});emit({type:'result',subtype:'success',sessionId:id,finalText:text,stopReason:stop});}
});`;
function cfg(protocol, mode='normal') {
 const args=[process.execPath,'-e',fake,protocol,mode];
 return {headlessProtocol:protocol,headless:args,headlessResume:[...args,'{session}']};
}
for(const protocol of ['codex','claude','cmd']) test(`${protocol}: three turns plus veto resume an explicit id and bootstrap once`, async()=>{
 const agent=new HeadlessAgent(protocol,cfg(protocol),process.cwd(),()=>{}, {history:[{prompt:'old prompt',reply:'old reply'}],graceMs:30});
 try {
  for(let turn=0;turn<4;turn++) {
   const response=await agent.ask(turn===3?'veto':`turn ${turn}`,2000);
   const decoded=JSON.parse(response.text);
   assert.equal(decoded.session,turn===0?null:'explicit-native-id');
   assert.equal(decoded.input.includes('old prompt'),turn===0);
   assert.equal(response.stopReason,'end_turn');
  }
 } finally {await agent.close();}
});
test('stdin preserves replacement tokens and a prompt larger than argv limits', async()=>{
 const agent=new HeadlessAgent('cmd',cfg('cmd'),process.cwd());
 const prompt='$$ $& {out} {cwd} {session}\n'+'x'.repeat(2_000_000);
 try {assert.equal(JSON.parse((await agent.ask(prompt,3000)).text).input,prompt);} finally {await agent.close();}
 assert.deepEqual(substituteArgs(['{cwd}/{session}'],{cwd:'$$ {session}',session:'$&'}),['$$ {session}/$&']);
});
test('non-end stop invalidates native id and does not commit completed history',async()=>{
 const agent=new HeadlessAgent('cmd',cfg('cmd','cancel'),process.cwd(),()=>{}, {nativeSessionId:'explicit-native-id'});
 const result=await agent.ask('cancel',2000);
 assert.equal(result.stopReason,'cancelled'); assert.equal(agent.nativeSessionId,null);assert.equal(agent.history.length,0);
 await agent.close();
});
test('timeout kills an uncooperative subprocess and clears session',async()=>{
 const agent=new HeadlessAgent('cmd',cfg('cmd','hang'),process.cwd(),()=>{}, {nativeSessionId:'explicit-native-id',graceMs:30});
 await assert.rejects(agent.ask('hang',200),/timed out/);
 assert.equal(agent.proc,null);assert.equal(agent.nativeSessionId,null);
 await agent.close();
});
test('spawn failure clears native id',async()=>{
 const bad=cfg('cmd');bad.headlessResume=['/nonexistent/roundtable-cli','{session}'];
 const agent=new HeadlessAgent('cmd',bad,process.cwd(),()=>{}, {nativeSessionId:'explicit-native-id'});
 await assert.rejects(agent.ask('hello',1000),/ENOENT/);assert.equal(agent.nativeSessionId,null);assert.equal(agent.proc,null);
});
test('reject unsupported adapters, missing terminal result, changed native id and malformed events',async()=>{
 await assert.rejects(new HeadlessAgent('other',{},process.cwd()).start(),/no validated/);
 assert.throws(()=>parseHeadlessOutput('cmd','{}'),/without a terminal/);
 assert.throws(()=>parseHeadlessOutput('cmd','noise'),/non-JSON/);
 const bad=cfg('cmd');bad.headlessResume=[process.execPath,'-e',`process.stdin.resume();process.stdin.on('end',()=>console.log(JSON.stringify({type:'result',subtype:'success',sessionId:'wrong',finalText:'oops',stopReason:'end_turn'})))`,'{session}'];
 const agent=new HeadlessAgent('cmd',bad,process.cwd(),()=>{}, {nativeSessionId:'explicit-native-id'});
 await assert.rejects(agent.ask('hello',1000),/changed the native/);assert.equal(agent.nativeSessionId,null);
});
test('CMD max-turn terminal result survives exit 8 and invalidates session',async()=>{
 const args=[process.execPath,'-e',`process.stdin.resume();process.stdin.on('end',()=>{console.log(JSON.stringify({type:'result',subtype:'max_turns',sessionId:'explicit-native-id',finalText:'partial',stopReason:'max_turns'}));process.exitCode=8;})`];
 const agent=new HeadlessAgent('cmd',{headlessProtocol:'cmd',headless:args,headlessResume:[...args,'{session}']},process.cwd());
 const result=await agent.ask('hello',1000);assert.equal(result.stopReason,'max_turns');assert.equal(agent.nativeSessionId,null);assert.equal(agent.history.length,0);
});

test('close during deferred startup never spawns a late child; concurrent ask is rejected', async () => {
  const agent = new HeadlessAgent('deferred', {}, process.cwd());
  let release;
  agent.start = () => new Promise(resolve => { release = resolve; });
  const pending = agent.ask('task', 1000);
  await assert.rejects(agent.ask('competing task', 1000), /concurrent/);
  await agent.close();
  release();
  await assert.rejects(pending, /closed during startup/);
  assert.equal(agent.proc, null);
});

test('configured model flag is preserved on initial and resumed headless turns', async () => {
  const source = `let input='';process.stdin.on('data',d=>input+=d);process.stdin.on('end',()=>console.log(JSON.stringify({type:'result',subtype:'success',sessionId:'explicit',stopReason:'end_turn',finalText:JSON.stringify(process.argv.slice(1))})));`;
  const config = { headlessProtocol: 'cmd', model: 'provider/deep', headless: [process.execPath, '-e', source, '--'], headlessResume: [process.execPath, '-e', source, '--', '{session}'] };
  const agent = new HeadlessAgent('cmd', config, process.cwd());
  try {
    assert.deepEqual(JSON.parse((await agent.ask('one', 1000)).text), ['--model', 'provider/deep']);
    assert.deepEqual(JSON.parse((await agent.ask('two', 1000)).text), ['explicit', '--model', 'provider/deep']);
  } finally { await agent.close(); }
});
