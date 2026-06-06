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
  2. Writes explorer.html into <results_dir>. The page fetches result
     files live (same origin), so re-running experiments updates the view
     without regenerating; regenerate only when NEW files appear.
  3. Ensures a local http server is serving <results_dir> on --port
     (starts one bound to 127.0.0.1 if the port is free; reuses an
     existing one otherwise) and opens the browser.

LOCAL-ONLY: serves on loopback. Results files must follow the skill's
conventions ({experiment, hypothesis, method, tests:[{h,desc,r,p,q,n}],
caveats}); unknown shapes degrade to the raw-JSON view.
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
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
:root{--ink:#1a1a1a;--bg:#fdfbf7;--muted:#6b6b6b;--rule:#d8d2c4;
--green:#2a7a5a;--amber:#c89000;--red:#a02a2a;--purple:#5a5aaa}
*{box-sizing:border-box}
body{font-family:'EB Garamond',serif;background:var(--bg);color:var(--ink);
margin:0;font-size:17px;line-height:1.45}
.layout{display:grid;grid-template-columns:330px 1fr;height:100vh}
.side{border-right:1px solid var(--rule);overflow-y:auto;padding:1rem}
.main{overflow-y:auto;padding:1.4rem 2rem}
h1{font-size:1.3rem;margin:.2rem 0 .8rem}
input#q{width:100%;font:inherit;padding:.35rem .6rem;border:1px solid var(--rule);
border-radius:5px;background:#fff;margin-bottom:.7rem}
.exp{padding:.45rem .55rem;border-radius:6px;cursor:pointer;margin:.15rem 0;
border:1px solid transparent}
.exp:hover{background:#f6f2e8}
.exp.active{border-color:var(--purple);background:#fff}
.exp .id{font-family:ui-monospace,monospace;font-size:.72rem;color:var(--muted)}
.exp .t{font-size:.82rem;line-height:1.25;display:block}
.badge{display:inline-block;font-family:ui-monospace,monospace;font-size:.65rem;
border-radius:8px;padding:0 .4rem;margin-left:.25rem;color:#fff}
.b-c{background:var(--green)}.b-l{background:var(--amber)}
h2{font-size:1.35rem;margin:.2rem 0 .4rem}
.meta{font-size:.85rem;color:var(--muted);font-style:italic;margin:.4rem 0 1rem}
table{border-collapse:collapse;width:100%;font-size:.85rem;margin:.8rem 0}
th{text-align:left;border-bottom:2px solid var(--ink);padding:.3rem .45rem;
cursor:pointer;user-select:none;white-space:nowrap}
td{border-bottom:1px solid var(--rule);padding:.3rem .45rem}
td.num{font-family:ui-monospace,monospace;font-size:.78rem;text-align:right;
white-space:nowrap}
tr.confirmed td{background:rgba(42,122,90,.10)}
tr.lead td{background:rgba(200,144,0,.10)}
.caveats{border-left:3px solid var(--amber);background:#fffaf0;
padding:.5rem .9rem;font-size:.85rem;margin:1rem 0}
.verdict{border-left:3px solid var(--purple);background:#fff;
padding:.5rem .9rem;font-size:.9rem;margin:.6rem 0}
details{margin:1rem 0}
pre{background:#fff;border:1px solid var(--rule);border-radius:6px;
padding:.8rem;font-size:.72rem;overflow-x:auto;max-height:50vh}
</style></head><body>
<div class="layout">
<div class="side">
<h1>Experiments <span style="font-size:.75rem;color:var(--muted)" id="count"></span></h1>
<input id="q" placeholder="filter…">
<select id="sortsel" style="width:100%;font:inherit;font-size:.8rem;
margin-bottom:.4rem;padding:.25rem;border:1px solid var(--rule);
border-radius:5px;background:#fff">
<option value="newest">newest first</option>
<option value="oldest">oldest first</option>
<option value="expnum">by experiment №</option>
<option value="tests">most tests</option>
<option value="confirmed">most confirmed</option>
<option value="leads">most leads</option>
</select>
<div id="chips" style="display:flex;flex-wrap:wrap;gap:.25rem;margin-bottom:.6rem"></div>
<div id="list"></div>
</div>
<div class="main" id="main"><p style="color:var(--muted)">← pick an
experiment. Green badge — confirmed (q&lt;0.10), amber — lead
(p&lt;0.06).</p></div>
</div>
<script>
const M=__DATA__;
const esc=v=>String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const list=document.getElementById('list'),main=document.getElementById('main');
document.getElementById('count').textContent='('+M.manifest.length+')';
let active=null;

let dir=M.sort||'newest';
document.getElementById('sortsel').value=dir;
document.getElementById('sortsel').onchange=e=>{dir=e.target.value;
  render(document.getElementById('q').value);};
const CHIPS=[
 ['all','all',e=>true],
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
  b.style.cssText='font:inherit;font-size:.7rem;padding:.1rem .5rem;'+
   'border:1px solid var(--rule);border-radius:10px;background:#fff;cursor:pointer';
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
      `</span><span class="t">${esc(e.title)}</span>`;
    div.onclick=()=>show(e);
    list.appendChild(div);
  }
  document.getElementById('count').textContent='('+shown+'/'+M.manifest.length+')';
}
document.getElementById('q').oninput=e=>render(e.target.value);

function flatTests(d){
  let t=d.tests||[];
  if(!Array.isArray(t))
    t=Object.values(t).filter(Array.isArray).flat();
  return t.filter(x=>x&&typeof x==='object');
}
function status(t){
  if(t.q!=null&&t.q<0.10)return 'confirmed';
  if(t.p!=null&&t.p<0.06)return 'lead';
  return t.p!=null?'null':'desc';
}
let sortKey=null,sortAsc=true,reqToken=0;
function show(e,keepSort){
  active=e.file;render(document.getElementById('q').value);
  const tok=++reqToken;
  fetch(encodeURIComponent(e.file)+'?'+Date.now()).then(r=>r.json()).then(d=>{
    if(tok!==reqToken)return; // stale response from a faster earlier click
    if(!keepSort){sortKey=null;}
    const tests=flatTests(d);
    if(sortKey)tests.sort((a,b)=>{
      const av=a[sortKey],bv=b[sortKey];
      if(av==null)return 1;if(bv==null)return -1;
      return (av<bv?-1:av>bv?1:0)*(sortAsc?1:-1);});
    let h=`<h2>${esc(e.exp)} · ${esc(d.experiment||e.file)}</h2>`;
    if(d.hypothesis)h+=`<div class="meta"><b>Hypothesis:</b> ${esc(d.hypothesis)}</div>`;
    if(d.method)h+=`<div class="meta"><b>Method:</b> ${esc(d.method)}</div>`;
    if(d.verdict)h+=`<div class="verdict"><b>Verdict:</b> ${
      esc(typeof d.verdict==='string'?d.verdict:JSON.stringify(d.verdict))}</div>`;
    if(tests.length){
      h+='<table><tr>';
      for(const k of ['h','desc','r','p','q','n'])
        h+=`<th data-k="${k}">${k}${sortKey===k?(sortAsc?' ↑':' ↓'):''}</th>`;
      h+='</tr>';
      for(const t of tests){
        h+=`<tr class="${status(t)}"><td class="num">${esc(t.h??t.id??'')}</td>`+
          `<td>${esc(t.desc??t.label??'')}</td>`+
          `<td class="num">${t.r??t.effect??''}</td>`+
          `<td class="num">${t.p??''}</td><td class="num">${t.q??''}</td>`+
          `<td class="num">${t.n??''}</td></tr>`;
      }
      h+='</table>';
    }
    if(d.caveats&&d.caveats.length)
      h+='<div class="caveats"><b>Caveats:</b><br>'+
        d.caveats.map(c=>'• '+esc(c)).join('<br>')+'</div>';
    h+=`<details><summary>raw JSON (${e.file})</summary><pre>${
      JSON.stringify(d,null,1).replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .slice(0,200000)}</pre></details>`;
    main.innerHTML=h;
    main.querySelectorAll('th').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k;
      if(sortKey===k)sortAsc=!sortAsc;else{sortKey=k;sortAsc=true;}
      show(e,true);});
  }).catch(err=>{main.innerHTML='<p>failed to load '+e.file+': '+err+'</p>'});
}
render('');
</script>
</body></html>
"""


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
        tests = d.get("tests") or []
        if isinstance(tests, dict):
            tests = [t for v in tests.values() if isinstance(v, list)
                     for t in v]
        tests = [t for t in tests if isinstance(t, dict)]
        n_sig = sum(1 for t in tests
                    if t.get("q") is not None and t["q"] < 0.10)
        n_lead = sum(1 for t in tests
                     if t.get("p") is not None and t["p"] < 0.06
                     and (t.get("q") is None or t["q"] >= 0.10))
        m = re.match(r"([A-Za-z]+\d+[a-z]?)", name)
        st = os.stat(path)
        created = getattr(st, "st_birthtime", st.st_mtime)
        import datetime as _dt
        manifest.append({
            "file": name, "exp": m.group(1) if m else name,
            "title": str(d.get("hypothesis") or d.get("goal")
                         or d.get("experiment") or name)[:140],
            "n_tests": len(tests), "n_confirmed": n_sig,
            "n_leads": n_lead, "created": created,
            "created_h": _dt.datetime.fromtimestamp(created)
            .strftime("%Y-%m-%d %H:%M"),
        })
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
               .replace(">", "\\u003e").replace("\u2028", "\\u2028")
               .replace("\u2029", "\\u2029"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(HTML.replace("__DATA__", payload))
    print(f"wrote {out} ({len(manifest)} experiments)")

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
