import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, renameSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { atomicWrite, assertFreshRun, waitForFile, permissionAllowed, fingerprint, sameBlockingSet } from './safeguards.mjs';
const temporary = () => mkdtempSync(join(tmpdir(), 'roundtable-safeguards-'));
const git = (cwd, ...args) => execFileSync('git', args, { cwd, stdio: 'pipe' });
function repo() {
  const dir = temporary(); git(dir, 'init'); git(dir, 'config', 'user.email', 'test@example.invalid'); git(dir, 'config', 'user.name', 'Test');
  writeFileSync(join(dir, 'tracked'), 'baseline'); writeFileSync(join(dir, '.gitignore'), 'ignored\n');
  git(dir, 'add', '.'); git(dir, 'commit', '-m', 'fixture'); return dir;
}
test('permissions allow known reads/execute/other in target, reject unknown and incomplete mutations', () => {
  const cwd = temporary(), run = join(cwd, 'run'), outside = temporary();
  for (const kind of ['read', 'search', 'think', 'fetch', 'execute', 'other', 'switch_mode']) assert.equal(permissionAllowed({kind, locations:[{path:cwd}]},cwd,run),true);
  for (const kind of [undefined, '', 'future']) assert.equal(permissionAllowed({kind},cwd,run),false);
  assert.equal(permissionAllowed({kind:'edit'},cwd,run),false);
  assert.equal(permissionAllowed({kind:'edit',locations:[{path:'new'}]},cwd,run),false);
  assert.equal(permissionAllowed({kind:'move',locations:[{path:outside},{path:cwd}]},cwd,run),false);
  assert.equal(permissionAllowed({kind:'edit',locations:[{path:join(outside,'new')}]},cwd,run),true);
});
test('permission containment follows symlinks and rejects run directory outside cwd', () => {
  const cwd = temporary(), outside = temporary(), run = temporary();
  symlinkSync(cwd,join(outside,'link'));
  symlinkSync(join(cwd,'not-created'),join(outside,'dangling'));
  for (const path of [join(outside,'link','new'),join(outside,'dangling','new'),join(run,'new')]) assert.equal(permissionAllowed({kind:'edit',locations:[{path}]},cwd,run),false);
  assert.equal(permissionAllowed({kind:'edit',locations:[{path:`${cwd}-sibling/new`}]},cwd,run),true);
});
test('fresh runs allow brief but reject prior artifacts', () => {
  const dir=temporary(); writeFileSync(join(dir,'brief.md'),'brief'); assertFreshRun(dir);
  mkdirSync(join(dir,'rounds')); assert.throws(()=>assertFreshRun(dir),/reused/);
});
test('atomic publication keeps slow draft invisible until complete rename', async () => {
  const dir=temporary(), path=join(dir,'synthesis.md'), pending=join(dir,'draft.tmp');
  writeFileSync(pending,'partial');
  const publication = setTimeout(()=>{writeFileSync(pending,'complete synthesis');renameSync(pending,path);},40);
  assert.equal(await waitForFile(path,1000,{pollMs:5}),'complete synthesis'); clearTimeout(publication);
  atomicWrite(path,'replacement'); assert.equal(await waitForFile(path,0),'replacement');
  assert.equal(await waitForFile(join(dir,'missing'),5,{pollMs:1}),null);
  const abort=new AbortController(); abort.abort(); await assert.rejects(waitForFile(path,100,{signal:abort.signal}));
});
test('fingerprints detect dirty tracked and untracked content, addition, rename, exclude run output', () => {
  const cwd=repo(), run=join(cwd,'run');
  writeFileSync(join(cwd,'tracked'),'dirty one'); const a=fingerprint(cwd,run);
  writeFileSync(join(cwd,'tracked'),'dirty two'); const b=fingerprint(cwd,run); assert.notEqual(a.hash,b.hash);
  writeFileSync(join(cwd,'new'),'one'); const c=fingerprint(cwd,run); assert.notEqual(b.hash,c.hash);
  writeFileSync(join(cwd,'new'),'two'); const d=fingerprint(cwd,run); assert.notEqual(c.hash,d.hash);
  renameSync(join(cwd,'new'),join(cwd,'renamed')); const e=fingerprint(cwd,run); assert.notEqual(d.hash,e.hash);
  mkdirSync(run); writeFileSync(join(run,'output'),'artifact'); assert.equal(e.hash,fingerprint(cwd,run).hash);
  writeFileSync(join(cwd,'ignored'),'excluded'); const f=fingerprint(cwd,run); assert.equal(e.hash,f.hash); assert.equal(f.coverage.ignoredExcluded,true);
  assert.equal(f.coverage.status,'complete');
});
test('fingerprint scopes subdirectories and excludes tracked run artifacts',()=>{
  const cwd=repo(), child=join(cwd,'child'), run=join(child,'run'); mkdirSync(run,{recursive:true});
  writeFileSync(join(run,'tracked'),'initial'); git(cwd,'add','.'); git(cwd,'commit','-m','run fixture');
  const a=fingerprint(child,run); writeFileSync(join(run,'tracked'),'changed'); writeFileSync(join(cwd,'tracked'),'outside');
  assert.equal(a.hash,fingerprint(child,run).hash);
});
test('missing HEAD reports unavailable rather than unchanged',()=>{
  const cwd=temporary(); git(cwd,'init'); const result=fingerprint(cwd,join(cwd,'run')); assert.equal(result.hash,null); assert.equal(result.coverage.status,'unavailable'); assert.ok(result.errors.length);
});
test('fingerprint detects index changes even when working-tree content matches HEAD',()=>{
  const cwd=repo(), run=join(cwd,'run'), baseline=fingerprint(cwd,run);
  writeFileSync(join(cwd,'tracked'),'staged change'); git(cwd,'add','tracked');
  writeFileSync(join(cwd,'tracked'),'baseline');
  const staged=fingerprint(cwd,run); assert.notEqual(staged.hash,baseline.hash);
  git(cwd,'reset','HEAD','tracked'); assert.equal(fingerprint(cwd,run).hash,baseline.hash);
});
test('fingerprint outside a Git repository reports unavailable coverage',()=>{
  const result=fingerprint(temporary()); assert.equal(result.hash,null);
  assert.equal(result.coverage.status,'unavailable'); assert.equal(result.coverage.tracked,false);
});
test('deadlock requires identical nonempty blocking sets',()=>{
  assert.equal(sameBlockingSet(['b','a'],['a','b']),true); assert.equal(sameBlockingSet([],[]),false); assert.equal(sameBlockingSet(['a'],['b']),false);
});
