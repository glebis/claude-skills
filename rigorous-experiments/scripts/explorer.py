#!/usr/bin/env python3
"""Experiment results explorer — launchable viewer over a directory of
results JSONs. Part of the rigorous-experiments skill.

Usage:
  python3 explorer.py <results_dir> [--port 8799] [--pattern "exp*.json"]
                      [--sort newest|oldest] [--no-open] [--no-serve]

What it does:
  1. Scans <results_dir> for experiment results files (default pattern
     exp*.json, verdict files excluded) and builds a manifest with
     confirmed/lead counts per experiment (q<0.10 / p<0.06). "Creation
     date" = st_birthtime on macOS; on filesystems without birthtime it
     falls back to mtime (re-runs reorder the list there).
  2. Links full-text reports: every *.html in the directory is scanned
     for experiment ids; matching reports are linked from each
     experiment's detail view.
  3. Writes explorer.html into <results_dir>. The page fetches result
     files live (same origin), so re-running experiments updates the view
     without regenerating; regenerate only when NEW files appear.
  4. Ensures a local http server is serving <results_dir> on --port
     (starts one bound to 127.0.0.1 if the port is free; reuses a server
     only after verifying it serves THIS directory) and opens the browser.

UI: system sans-serif; resizable sidebar (drag the divider, width
persisted); star experiments (★, persisted in localStorage per
directory) and filter by starred; every scalar/dict/list field of a
results JSON is rendered (facts table, definition lists like
"approaches", bullet lists) — nothing meaningful hides in raw JSON only.

LOCAL-ONLY: serves on loopback. Results files following the skill's
conventions ({experiment, hypothesis, method, tests:[{h,desc,r,p,q,n}],
caveats}) render richest; unknown shapes degrade gracefully.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import socket
import subprocess
import sys
import webbrowser

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Experiment explorer</title>
<style>
:root{--ink:#1a1a1a;--bg:#fdfbf7;--muted:#6b6b6b;--rule:#d8d2c4;
--green:#2a7a5a;--amber:#c89000;--red:#a02a2a;--purple:#5a5aaa}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,Arial,sans-serif;
background:var(--bg);color:var(--ink);margin:0;font-size:15px;line-height:1.5}
.layout{display:grid;grid-template-columns:var(--sidew,420px) 6px 1fr;height:100vh}
.side{border-right:1px solid var(--rule);overflow-y:auto;padding:1rem;min-width:240px}
#drag{cursor:col-resize;background:transparent}
#drag:hover{background:rgba(90,90,170,.15)}
.main{overflow-y:auto;padding:1.4rem 2rem}
h1{font-size:1.15rem;margin:.2rem 0 .8rem;font-weight:600}
input#q{width:100%;font:inherit;padding:.4rem .6rem;border:1px solid var(--rule);
border-radius:6px;background:#fff;margin-bottom:.5rem}
select#sortsel{width:100%;font:inherit;font-size:.8rem;margin-bottom:.45rem;
padding:.3rem;border:1px solid var(--rule);border-radius:6px;background:#fff}
#chips{display:flex;flex-wrap:wrap;gap:.25rem;margin-bottom:.6rem}
#chips button{font:inherit;font-size:.72rem;padding:.12rem .55rem;
border:1px solid var(--rule);border-radius:10px;background:#fff;cursor:pointer}
.exp{padding:.5rem .6rem;border-radius:7px;cursor:pointer;margin:.18rem 0;
border:1px solid transparent;position:relative}
.exp:hover{background:#f6f2e8}
.exp.active{border-color:var(--purple);background:#fff}
.exp .id{font-family:ui-monospace,Menlo,monospace;font-size:.7rem;color:var(--muted)}
.exp .t{font-size:.82rem;line-height:1.3;display:block;margin-top:.1rem}
.star{position:absolute;top:.35rem;right:.4rem;cursor:pointer;font-size:.9rem;
color:#c8c2b4;user-select:none}
.star.on{color:var(--amber)}
.badge{display:inline-block;font-family:ui-monospace,Menlo,monospace;font-size:.65rem;
border-radius:8px;padding:0 .4rem;margin-left:.25rem;color:#fff}
.b-c{background:var(--green)}.b-l{background:var(--amber)}
h2{font-size:1.3rem;margin:.2rem 0 .5rem;font-weight:650}
h3{font-size:.95rem;margin:1.4rem 0 .3rem;font-weight:650}
.meta{font-size:.86rem;color:#444;margin:.4rem 0 .8rem}
.meta b{color:var(--ink)}
table{border-collapse:collapse;width:100%;font-size:.82rem;
margin:1.4rem 0 1.6rem}
th{text-align:left;border-bottom:2px solid var(--ink);padding:.35rem .5rem;
cursor:pointer;user-select:none;white-space:nowrap;font-size:.75rem;
text-transform:uppercase;letter-spacing:.04em;color:#444}
td{border-bottom:1px solid var(--rule);padding:.35rem .5rem}
td.num{font-family:ui-monospace,Menlo,monospace;font-size:.76rem;text-align:right;
white-space:nowrap}
tr.confirmed td{background:rgba(42,122,90,.16);font-weight:600}
tr.confirmed td:first-child{border-left:4px solid var(--green)}
tr.lead td{background:rgba(200,144,0,.10)}
tr.lead td:first-child{border-left:4px solid var(--amber)}
tr.null td{color:#777}
tr.null td:first-child{border-left:4px solid transparent}
.st-confirmed{color:var(--green);font-weight:700}
.st-lead{color:var(--amber);font-weight:600}
.st-null{color:#999}
.caveats{border-left:3px solid var(--amber);background:#fffaf0;
padding:.6rem 1rem;font-size:.83rem;margin:1.4rem 0}
.verdict{border-left:3px solid var(--purple);background:#fff;
padding:.6rem 1rem;font-size:.88rem;margin:.8rem 0}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:.15rem .9rem;
font-size:.84rem;margin:.5rem 0 1rem}
.kv dt{font-family:ui-monospace,Menlo,monospace;font-size:.74rem;
color:var(--muted);padding-top:.1rem}
.kv dd{margin:0}
.facts{display:flex;flex-wrap:wrap;gap:.3rem;margin:.6rem 0 1rem}
.fact{font-size:.74rem;border:1px solid var(--rule);border-radius:6px;
background:#fff;padding:.15rem .5rem}
.fact b{font-family:ui-monospace,Menlo,monospace;font-weight:600}
.reports{margin:.5rem 0 .9rem}
.reports a{display:inline-block;font-size:.76rem;border:1px solid var(--purple);
color:var(--purple);border-radius:10px;padding:.1rem .6rem;margin:0 .3rem .3rem 0;
text-decoration:none}
.reports a:hover{background:var(--purple);color:#fff}
ul.plain{margin:.3rem 0 1rem;padding-left:1.2rem;font-size:.84rem}
details{margin:1.4rem 0}
summary{cursor:pointer;font-size:.85rem;color:var(--muted)}
pre{background:#fff;border:1px solid var(--rule);border-radius:6px;
padding:.8rem;font-size:.72rem;overflow-x:auto;max-height:50vh}
.note{color:var(--muted);font-size:.88rem}
</style></head><body>
<div class="layout" id="layout">
<div class="side">
<h1>Experiments <span style="font-size:.75rem;color:var(--muted)" id="count"></span></h1>
<input id="q" placeholder="filter…">
<select id="sortsel">
<option value="newest">newest first</option>
<option value="oldest">oldest first</option>
<option value="expnum">by experiment №</option>
<option value="tests">most tests</option>
<option value="confirmed">most confirmed</option>
<option value="leads">most leads</option>
</select>
<div id="chips"></div>
<div id="list"></div>
</div>
<div id="drag"></div>
<div class="main" id="main"><p class="note">← pick an experiment.
Green badge — confirmed (q&lt;0.10), amber — lead (p&lt;0.06).
★ stars an experiment; the «starred» chip filters to your stars.</p></div>
</div>
<script>
const M=__DATA__;
const esc=v=>String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const list=document.getElementById('list'),main=document.getElementById('main');
let active=null;

// ---- resizable sidebar (width persisted per directory)
const WKEY='explorer-width-'+M.dir_token;
const saved=localStorage.getItem(WKEY);
if(saved)document.getElementById('layout').style.setProperty('--sidew',saved+'px');
(()=>{const drag=document.getElementById('drag');let on=false;
 drag.addEventListener('mousedown',()=>{on=true;document.body.style.userSelect='none';});
 window.addEventListener('mousemove',e=>{if(!on)return;
  const w=Math.max(240,Math.min(700,e.clientX));
  document.getElementById('layout').style.setProperty('--sidew',w+'px');});
 window.addEventListener('mouseup',()=>{if(on){on=false;
  document.body.style.userSelect='';
  const w=getComputedStyle(document.getElementById('layout'))
    .getPropertyValue('--sidew').trim().replace('px','');
  localStorage.setItem(WKEY,w);}});})();

// ---- stars (persisted per directory)
const SKEY='explorer-stars-'+M.dir_token;
let stars=new Set(JSON.parse(localStorage.getItem(SKEY)||'[]'));
function toggleStar(file){
  stars.has(file)?stars.delete(file):stars.add(file);
  localStorage.setItem(SKEY,JSON.stringify([...stars]));
  render(document.getElementById('q').value);
}

let dir=M.sort||'newest';
document.getElementById('sortsel').value=dir;
document.getElementById('sortsel').onchange=e=>{dir=e.target.value;
  render(document.getElementById('q').value);};
const CHIPS=[
 ['all','all',e=>true],
 ['starred','★ starred',e=>stars.has(e.file)],
 ['tests','with tests',e=>e.n_tests>0],
 ['confirmed','confirmed ✓',e=>e.n_confirmed>0],
 ['leads','leads',e=>e.n_leads>0],
 ['nulls','nulls only',e=>e.n_tests>0&&!e.n_confirmed&&!e.n_leads],
 ['notests','no tests',e=>e.n_tests===0]];
let chip='all';
const chipsEl=document.getElementById('chips');
for(const [id,label] of CHIPS.map(c=>[c[0],c[1]])){
  const b=document.createElement('button');
  b.textContent=label;b.dataset.id=id;
  b.onclick=()=>{chip=id;render(document.getElementById('q').value);};
  chipsEl.appendChild(b);
}
function expnum(e){const m=e.exp.match(/\\d+/);return m?+m[0]:1e9;}
const SORTS={
 newest:(a,b)=>b.created-a.created,
 oldest:(a,b)=>a.created-b.created,
 expnum:(a,b)=>expnum(a)-expnum(b),
 tests:(a,b)=>b.n_tests-a.n_tests,
 confirmed:(a,b)=>b.n_confirmed-a.n_confirmed||b.n_leads-a.n_leads,
 leads:(a,b)=>b.n_leads-a.n_leads||b.n_confirmed-a.n_confirmed};
function render(filter){
  list.innerHTML='';
  for(const b of chipsEl.children)
    b.style.background=b.dataset.id===chip?'var(--purple)':'#fff',
    b.style.color=b.dataset.id===chip?'#fff':'inherit';
  const f=(filter||'').toLowerCase();
  const pred=CHIPS.find(c=>c[0]===chip)[2];
  const items=[...M.manifest].sort(SORTS[dir]||SORTS.newest);
  let shown=0;
  for(const e of items){
    if(!pred(e))continue;
    if(f && !(e.file+' '+e.title).toLowerCase().includes(f))continue;
    shown++;
    const div=document.createElement('div');
    div.className='exp'+(active===e.file?' active':'');
    div.innerHTML=`<span class="id">${e.exp} · ${e.created_h} · ${e.n_tests} tests`+
      (e.n_confirmed?`<span class="badge b-c">${e.n_confirmed}</span>`:'')+
      (e.n_leads?`<span class="badge b-l">${e.n_leads}</span>`:'')+
      `</span><span class="t">${esc(e.title)}</span>`+
      `<span class="star${stars.has(e.file)?' on':''}" data-f="${esc(e.file)}">`+
      (stars.has(e.file)?'★':'☆')+`</span>`;
    div.onclick=ev=>{
      if(ev.target.classList.contains('star')){toggleStar(e.file);
        ev.stopPropagation();return;}
      show(e);};
    list.appendChild(div);
  }
  document.getElementById('count').textContent='('+shown+'/'+M.manifest.length+')';
}
document.getElementById('q').oninput=e=>render(e.target.value);

// mirrors Python extract_tests(): p/q-like keys, lists + standalone dicts
const P_AL=new Set(['p','p_band','perm_p','exact_p','pval','p_value']);
const Q_AL=new Set(['q','q_value','q_bh','fdr_q']);
function pq(x){
  let p=null,q=null,has=false;
  for(const [k,v] of Object.entries(x)){
    if(typeof v!=='number'&&v!==null)continue;
    if(Q_AL.has(k)){q=v;has=true;}
    else if(P_AL.has(k)){p=v;has=true;}
  }
  return {has,p,q};
}
function findTests(o,path,acc){
  acc=acc||[];path=path||[];
  if(Array.isArray(o)){
    const dicts=o.filter(x=>x&&typeof x==='object'&&!Array.isArray(x));
    const hits=dicts.filter(x=>pq(x).has);
    if(hits.length){
      for(const x of hits){const r=pq(x);
        acc.push({item:x,p:r.p,q:r.q,path:path.join('.'),top:path[0]||''});}
      return acc;
    }
    for(const x of o)findTests(x,path,acc);
  }else if(o&&typeof o==='object'){
    const r=pq(o);
    if(r.has&&!Object.values(o).some(v=>v&&typeof v==='object')){
      acc.push({item:o,p:r.p,q:r.q,path:path.join('.'),top:path[0]||''});
      return acc;
    }
    for(const [k,v] of Object.entries(o))
      findTests(v,path.length<6?path.concat(k):path,acc);
  }
  return acc;
}
const NUMK=new Set(['r','p','q','n','effect','beta','F','tau','d','slope']);
function testDesc(w){
  const t=w.item;
  const named=t.desc??t.label??t.relation;
  if(named)return String(named);
  if(t.from!==undefined&&t.to!==undefined)return t.from+' \\u2192 '+t.to;
  const parts=[];
  for(const [k,v] of Object.entries(t))
    if(typeof v==='string'&&!NUMK.has(k)&&k!=='h'&&k!=='id')parts.push(v);
  if(parts.length)return parts.join(' \\u00b7 ');
  return w.path||'(unnamed test)';
}
function testEffect(w){
  const t=w.item;
  for(const k of ['r','effect','d','beta','F','tau','slope'])
    if(t[k]!==undefined&&t[k]!==null)return k+'='+t[k];
  return '';
}
function status(w){
  if(w.q!=null&&w.q<0.10)return 'confirmed';
  if(w.p!=null&&w.p<0.06)return 'lead';
  return w.p!=null?'null':'desc';
}

// ---- generic field rendering: nothing meaningful hides in raw JSON
const HANDLED=new Set(['experiment','title','hypothesis','goal','method',
 'verdict','verdict_summary','caveats','tests']);
function renderExtras(d,testTops){
  let h='';
  const facts=[];
  for(const [k,v] of Object.entries(d)){
    if(HANDLED.has(k)||testTops.has(k))continue;
    if(v===null)continue;
    if(typeof v==='number'||typeof v==='boolean'||
       (typeof v==='string'&&v.length<=80)){
      facts.push(`<span class="fact"><b>${esc(k)}</b>: ${esc(v)}</span>`);
    }
  }
  if(facts.length)h+=`<h3>Facts</h3><div class="facts">${facts.join('')}</div>`;
  for(const [k,v] of Object.entries(d)){
    if(HANDLED.has(k)||testTops.has(k))continue;
    if(typeof v==='string'&&v.length>80){
      h+=`<h3>${esc(k)}</h3><p class="meta">${esc(v)}</p>`;
    }else if(Array.isArray(v)&&v.length&&v.every(x=>typeof x==='string')){
      h+=`<h3>${esc(k)}</h3><ul class="plain">`+
        v.map(x=>`<li>${esc(x)}</li>`).join('')+'</ul>';
    }else if(v&&typeof v==='object'&&!Array.isArray(v)){
      const ent=Object.entries(v);
      if(ent.length&&ent.every(([kk,vv])=>typeof vv==='string'||
          typeof vv==='number'||typeof vv==='boolean')){
        // dicts like "approaches": {A: "...", B: "..."} -> definition list
        h+=`<h3>${esc(k)}</h3><dl class="kv">`+
          ent.map(([kk,vv])=>`<dt>${esc(kk)}</dt><dd>${esc(vv)}</dd>`).join('')+
          '</dl>';
      }else if(ent.length){
        h+=`<h3>${esc(k)}</h3><p class="note">nested object `+
          `(${ent.length} keys) — see raw JSON below</p>`;
      }
    }else if(Array.isArray(v)&&v.length){
      h+=`<h3>${esc(k)}</h3><p class="note">${v.length} records — `+
        `see raw JSON below</p>`;
    }
  }
  return h;
}

let sortKey=null,sortAsc=true,reqToken=0;
function show(e,keepSort){
  active=e.file;render(document.getElementById('q').value);
  const tok=++reqToken;
  fetch(encodeURIComponent(e.file)+'?'+Date.now()).then(r=>r.json()).then(d=>{
    if(tok!==reqToken)return; // stale response from a faster earlier click
    if(!keepSort){sortKey=null;}
    const tests=findTests(d);
    const testTops=new Set(tests.map(w=>w.top).filter(Boolean));
    if(sortKey)tests.sort((a,b)=>{
      const get=w=>sortKey==='p'?w.p:sortKey==='q'?w.q:
        sortKey==='n'?w.item.n:sortKey==='status'?status(w):
        sortKey==='effect'?testEffect(w):sortKey==='desc'?testDesc(w):
        (w.item.h??w.item.id);
      const av=get(a),bv=get(b);
      if(av==null)return 1;if(bv==null)return -1;
      return (av<bv?-1:av>bv?1:0)*(sortAsc?1:-1);});
    let h=`<h2>${esc(e.exp)} · ${esc(d.title||d.experiment||e.file)}</h2>`;
    if(e.reports&&e.reports.length)
      h+='<div class="reports">Reports: '+e.reports.map(r=>
        `<a href="${esc(r)}" target="_blank">${esc(r.replace('.html',''))}</a>`)
        .join('')+'</div>';
    if(d.hypothesis)h+=`<div class="meta"><b>Hypothesis:</b> ${esc(d.hypothesis)}</div>`;
    else if(d.goal)h+=`<div class="meta"><b>Goal:</b> ${esc(d.goal)}</div>`;
    if(d.method)h+=`<div class="meta"><b>Method:</b> ${esc(d.method)}</div>`;
    const verd=d.verdict||d.verdict_summary;
    if(verd)h+=`<div class="verdict"><b>Verdict:</b> ${
      esc(typeof verd==='string'?verd:JSON.stringify(verd))}</div>`;
    if(tests.length){
      h+='<table><tr>';
      for(const k of ['h','desc','effect','p','q','n','status'])
        h+=`<th data-k="${k}">${k}${sortKey===k?(sortAsc?' \\u2191':' \\u2193'):''}</th>`;
      h+='</tr>';
      const SLBL={confirmed:'\\u2713 confirmed',lead:'lead','null':'null',desc:'\\u2014'};
      for(const w of tests){
        const st=status(w);
        h+=`<tr class="${st}"><td class="num">${esc(w.item.h??w.item.id??'')}</td>`+
          `<td>${esc(testDesc(w))}</td>`+
          `<td class="num">${esc(testEffect(w))}</td>`+
          `<td class="num">${w.p??''}</td><td class="num">${w.q??''}</td>`+
          `<td class="num">${w.item.n??''}</td>`+
          `<td class="num st-${st}">${SLBL[st]}</td></tr>`;
      }
      h+='</table>';
    }else{
      h+='<p class="note">No inferential tests detected in this results '+
        'file \\u2014 descriptive layer. See fields and raw JSON below.</p>';
    }
    h+=renderExtras(d,testTops);
    if(d.caveats&&d.caveats.length)
      h+='<div class="caveats"><b>Caveats:</b><br>'+
        d.caveats.map(c=>'\\u2022 '+esc(c)).join('<br>')+'</div>';
    h+=`<details><summary>raw JSON (${esc(e.file)})</summary><pre>${
      JSON.stringify(d,null,1).replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .slice(0,200000)}</pre></details>`;
    main.innerHTML=h;
    main.querySelectorAll('th').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k;
      if(sortKey===k)sortAsc=!sortAsc;else{sortKey=k;sortAsc=true;}
      show(e,true);});
  }).catch(err=>{main.innerHTML='<p>failed to load '+esc(e.file)+': '+esc(err)+'</p>'});
}
render('');
</script>
</body></html>
"""


# EXACT alias whitelist — broad q_*/p_* matching once swallowed feature
# columns like q_rate (question rate) and fabricated q-values.
P_ALIASES = {"p", "p_band", "perm_p", "exact_p", "pval", "p_value"}
Q_ALIASES = {"q", "q_value", "q_bh", "fdr_q"}


def _pq(x):
    """(p, q) values of a dict via alias keys, else (None-marker)."""
    p = q = None
    has = False
    for k, v in x.items():
        if not isinstance(v, (int, float, type(None))):
            continue
        if k in Q_ALIASES:
            q, has = v, True
        elif k in P_ALIASES:
            p, has = v, True
    return has, p, q


def extract_tests(d):
    """Universal test discovery, mirrored EXACTLY by findTests() in the
    embedded JS: (a) every list whose dict items carry a p/q-like key
    (p, q, p_band, perm_p, exact_p, ...); (b) standalone dicts carrying
    a p-like key (single pre-registered tests like primary_partial),
    named by their JSON path."""
    found = []

    def walk(o, path):
        if isinstance(o, list):
            dicts = [x for x in o if isinstance(x, dict)]
            hits = [x for x in dicts if _pq(x)[0]]
            if hits:
                for x in hits:
                    has, p, q = _pq(x)
                    found.append({"_p": p, "_q": q, "raw": x,
                                  "path": path})
                return
            for x in o:
                walk(x, path)
        elif isinstance(o, dict):
            has, p, q = _pq(o)
            if has and not any(isinstance(v, (dict, list))
                               for v in o.values()):
                found.append({"_p": p, "_q": q, "raw": o, "path": path})
                return
            for k, v in o.items():
                walk(v, path + [k] if len(path) < 6 else path)

    walk(d, [])
    return found


def scan_reports(results_dir, exp_ids):
    """Map exp id -> [report html files mentioning it]. Whole-word match
    (exp21 must not match exp210)."""
    links = {e: [] for e in exp_ids}
    for path in sorted(glob.glob(os.path.join(results_dir, "*.html"))):
        name = os.path.basename(path)
        if name == "explorer.html":
            continue
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for e in exp_ids:
            if re.search(re.escape(e) + r"(?![0-9a-z])", text):
                links[e].append(name)
    return links


def build_manifest(results_dir, pattern):
    if os.path.isabs(pattern) or ".." in pattern.split(os.sep):
        sys.exit("--pattern must be relative without parent traversal")
    manifest = []
    for path in sorted(glob.glob(os.path.join(results_dir, pattern))):
        if os.path.commonpath([os.path.abspath(path), results_dir]) \
                != results_dir:
            continue
        name = os.path.basename(path)
        if "verdicts" in name or name == "explorer.html":
            continue
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        tests = extract_tests(d)
        n_sig = sum(1 for t in tests
                    if t["_q"] is not None and t["_q"] < 0.10)
        n_lead = sum(1 for t in tests
                     if t["_p"] is not None and t["_p"] < 0.06
                     and (t["_q"] is None or t["_q"] >= 0.10))
        m = re.match(r"([A-Za-z]+\d+[a-z]?)", name)
        title = str(d.get("title") or d.get("hypothesis") or d.get("goal")
                    or d.get("verdict_summary") or d.get("experiment")
                    or name)[:140]
        st = os.stat(path)
        created = getattr(st, "st_birthtime", st.st_mtime)
        import datetime as _dt
        manifest.append({
            "file": name, "exp": m.group(1) if m else name,
            "title": title,
            "n_tests": len(tests), "n_confirmed": n_sig,
            "n_leads": n_lead, "created": created,
            "created_h": _dt.datetime.fromtimestamp(created)
            .strftime("%Y-%m-%d %H:%M"),
        })
    # link full-text reports to experiments
    links = scan_reports(results_dir, sorted({e["exp"] for e in manifest}))
    for e in manifest:
        e["reports"] = links.get(e["exp"], [])
    return manifest


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def dir_token(rd):
    import hashlib
    return hashlib.sha1(rd.encode()).hexdigest()[:12]


def serves_this_dir(port, rd):
    """True if the listener on `port` serves OUR explorer for `rd`."""
    import urllib.request
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/explorer.html", timeout=2) as r:
            return dir_token(rd) in r.read(100000).decode("utf-8", "ignore")
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--pattern", default="exp*.json")
    ap.add_argument("--sort", choices=["newest", "oldest"],
                    default="newest",
                    help="initial sidebar order by file creation date")
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--no-serve", action="store_true")
    a = ap.parse_args()
    rd = os.path.abspath(a.results_dir)
    if not os.path.isdir(rd):
        sys.exit(f"not a directory: {rd}")

    manifest = build_manifest(rd, a.pattern)
    if not manifest:
        sys.exit(f"no experiment results matching {a.pattern} in {rd}")
    out = os.path.join(rd, "explorer.html")
    # </script>-breakout-safe embedding: escape < > & line separators
    payload = json.dumps({"manifest": manifest, "sort": a.sort,
                          "dir_token": dir_token(rd)},
                         ensure_ascii=False)
    payload = (payload.replace("&", "\\u0026").replace("<", "\\u003c")
               .replace(">", "\\u003e").replace(" ", "\\u2028")
               .replace(" ", "\\u2029"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(HTML.replace("__DATA__", payload))
    n_linked = sum(1 for e in manifest if e["reports"])
    print(f"wrote {out} ({len(manifest)} experiments, "
          f"{n_linked} linked to reports)")

    port = a.port
    if not a.no_serve:
        # reuse ONLY a server that provably serves this directory
        # (token embedded in explorer.html); otherwise find a free port
        while port_in_use(port) and not serves_this_dir(port, rd):
            print(f"port {port} busy with something else — trying "
                  f"{port + 1}")
            port += 1
        if port_in_use(port):
            print(f"port {port} already serving this directory — reusing")
        else:
            subprocess.Popen(
                [sys.executable, "-m", "http.server", str(port),
                 "--bind", "127.0.0.1", "--directory", rd],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"started http.server on 127.0.0.1:{port}")
    url = f"http://localhost:{port}/explorer.html"
    if not a.no_open:
        webbrowser.open(url)
    print(url)


if __name__ == "__main__":
    main()
