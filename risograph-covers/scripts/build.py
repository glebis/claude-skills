#!/usr/bin/env python3
"""Compose a portable cover from validated configuration and local artwork."""
import argparse, html, json, math, shutil
from pathlib import Path

def build(config_path, output):
    config_path=Path(config_path); output=Path(output)
    c=json.loads(config_path.read_text()); title=c['title']; graph=c['graph']; nodes=c['nodes']; edges=c['edges']; footer=c.get('footer',{})
    def num(v):
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v): raise ValueError('Geometry must be finite numbers')
        return v
    ids=[n['id'] for n in nodes]
    if len(ids)!=len(set(ids)): raise ValueError('Node IDs must be unique')
    shape={'circle':'black-circle.png','square':'black-square.png','triangle':'red-triangle.png'}
    for n in nodes:
        if n['shape'] not in shape or n.get('ink','black') not in ('red','black'): raise ValueError('Unsupported shape or ink')
        for k in ('x','y','size'):num(n[k])
        if n['size']<=0:raise ValueError('Node size must be positive')
    for e in edges:
        if len(e)!=2 or any(n not in ids for n in e):raise ValueError('Edge refers to missing node')
    for k in ('x','y','width','height','rotation'):num(graph[k])
    opacity=num(footer.get('opacity',.24))
    if not 0<=opacity<=1:raise ValueError('Opacity must be between zero and one')
    if footer.get('align','right') not in ('left','right'):raise ValueError('Footer alignment must be left or right')
    for k in ('first_size','emphasis_size'):num(title[k])
    def esc(v):return html.escape(str(v),quote=True)
    # Validate before creating or overwriting output
    output.mkdir(parents=True,exist_ok=True)
    shutil.copytree(Path(__file__).resolve().parent.parent/'assets',output/'assets',dirs_exist_ok=True)
    byid={n['id']:n for n in nodes}; parts=[]; seen=set()
    for a,b in edges:
        key=tuple(sorted((a,b)))
        if key in seen or a==b:continue
        seen.add(key);u=byid[a];v=byid[b]
        parts.append(f'<line class="edge" x1="{u["x"]}" y1="{u["y"]}" x2="{v["x"]}" y2="{v["y"]}"/>')
    for n in nodes:
        x,y,z=n['x'],n['y'],n['size']; ink=n.get('ink','black')
        parts.append(f'<image href="assets/{shape[n["shape"]]}" x="{x-z/2}" y="{y-z/2}" width="{z}" height="{z}" filter="url(#{ink})"/>')
        if n.get('label'):parts.append(f'<text class="label" x="{x}" y="{y+z/2+28}" text-anchor="middle">{esc(n["label"])}</text>')
    filters=''.join(f'<filter id="{name}" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="0 0 0 0 {r} 0 0 0 0 {g} 0 0 0 0 {b} 0 0 0 1 0"/></filter>' for name,(r,g,b) in {'red':(.816,.098,.125),'black':(.035,.035,.035)}.items())
    logo='<svg class="logo" viewBox="0 0 24 24" aria-label="LinkedIn"><rect width="24" height="24" rx="2" fill="currentColor"/><path fill="#f3f0e8" d="M4 9h3v11H4zM9 9h3v1.5c1-2 6-3 7 2V20h-3v-6c0-3-4-3-4 0v6H9z"/><circle cx="5.5" cy="5.5" r="1.7" fill="#f3f0e8"/></svg>'
    foot=f'<footer><span>{esc(footer.get("name","Gleb Kalinin"))} ·</span>{logo}<span>{esc(footer.get("profile","/in/glebkalinin/"))}</span></footer>' if footer.get('enabled',True) else ''
    template=(Path(__file__).resolve().parent.parent/'editor/editor.html').read_text()
    result=template.replace('__CONFIG__',json.dumps(c,ensure_ascii=False).replace('<','\\u003c'))
    (output/'index.html').write_text(result);(output/'cover.json').write_text(json.dumps(c,ensure_ascii=False,indent=2));print(output/'index.html')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('output');a=p.parse_args();build(a.config,a.output)
