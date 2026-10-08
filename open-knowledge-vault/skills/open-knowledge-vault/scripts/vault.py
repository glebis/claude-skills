#!/usr/bin/env python3
"""Local setup and basic structural audit for Open Knowledge Vault. Requires PyYAML."""
import argparse, json, re, shutil, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit
import yaml

PROFILES = {
 'meeting': ['sources','concepts','ideas','events','questions','actions','people','organisations','maps'],
 'learning': ['sources','domains','courses','lessons','concepts','scenarios','questions','maps'],
 'research': ['sources','concepts','claims','decisions','procedures','questions','actions','maps'],
}

def fm(meta, body):
 return '---\n'+yaml.safe_dump(meta,sort_keys=False,allow_unicode=True)+'---\n\n'+body

def missing(path, text):
 if path.exists(): return False
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x',encoding='utf-8') as f: f.write(text)
 return True

def meta_of(path):
 text=path.read_text(encoding='utf-8')
 lines=text.splitlines()
 if not lines or lines[0]!='---': return None,text
 end=next((i for i in range(1,len(lines)) if lines[i]=='---'),None)
 if end is None: raise ValueError('unclosed frontmatter')
 meta=yaml.safe_load('\n'.join(lines[1:end]))
 if not isinstance(meta,dict): raise ValueError('frontmatter must be a mapping')
 return meta,'\n'.join(lines[end+1:])

def instant(value):
 if isinstance(value,datetime): dt=value
 elif isinstance(value,str): dt=datetime.fromisoformat(value.replace('Z','+00:00'))
 else: raise ValueError('not a datetime')
 if dt.utcoffset() is None: raise ValueError('UTC offset required')
 return dt

def audit(root):
 errors=[];warnings=[];count=0
 for p in sorted(root.rglob('*.md')):
  if p.is_symlink():warnings.append(f'{p.relative_to(root)}: symlink not traversed');continue
  rel=str(p.relative_to(root));count+=1
  try: m,body=meta_of(p)
  except (ValueError,yaml.YAMLError,UnicodeError) as e:errors.append(f'{rel}: {e}');continue
  if p.name=='index.md':
   if m is not None and (p.parent!=root or set(m)-{'okf_version'}):errors.append(f'{rel}: only root index may declare okf_version frontmatter')
   if m and m.get('okf_version')!='0.2':warnings.append(f'{rel}: target version is not 0.2')
  elif p.name=='log.md':
   if m is not None:errors.append(f'{rel}: log must not have frontmatter')
   for heading in re.findall(r'^##\s+(.+)$',body,re.M):
    try: datetime.strptime(heading,'%Y-%m-%d')
    except ValueError:errors.append(f'{rel}: log date heading must be YYYY-MM-DD')
  elif m is None or not isinstance(m.get('type'),str) or not m['type'].strip():errors.append(f'{rel}: non-empty string type required')
  if m and p.name not in ('index.md','log.md'):
   if 'status' in m and m['status'] not in ('draft','stable','deprecated'):warnings.append(f'{rel}: put workflow status in workflow_status; lifecycle is draft/stable/deprecated')
   if m.get('type')=='Attested Computation' and not m.get('runtime'):warnings.append(f'{rel}: Attested Computation should declare runtime')
   if 'sources' in m:
    sources=m['sources']
    if not isinstance(sources,list):warnings.append(f'{rel}: sources should be a list')
    else:
     ids=[]
     for source in sources:
      if not isinstance(source,dict) or not isinstance(source.get('resource'),str) or not source['resource'].strip():warnings.append(f'{rel}: each source needs resource')
      elif source.get('id'): ids.append(source['id'])
     if len(ids)!=len(set(ids)):warnings.append(f'{rel}: duplicate source IDs')
   for family in ('generated','verified'):
    if family not in m:continue
    events=m[family] if isinstance(m[family],list) else [m[family]]
    if family=='generated' and isinstance(m[family],list):warnings.append(f'{rel}: generated should be a mapping')
    for event in events:
     if not isinstance(event,dict):warnings.append(f'{rel}: invalid {family} event');continue
     actor=event.get('by')
     if not isinstance(actor,str) or not (re.fullmatch(r'(human|process):.+',actor) or re.fullmatch(r'[^/]+/[^/]+',actor)):warnings.append(f'{rel}: {family}.by needs an actor identity')
     if 'at' in event:
      try:instant(event['at'])
      except ValueError:warnings.append(f'{rel}: {family}.at needs an offset-aware datetime')
     elif family=='verified':warnings.append(f'{rel}: verification event needs at')
   if 'stale_after' in m:
    try:instant(m['stale_after'])
    except ValueError:warnings.append(f'{rel}: stale_after needs an offset-aware datetime')
  # Ignore fenced examples and inline code; unresolved links are advisory only.
  visible=re.sub(r'```.*?```|~~~.*?~~~','',body,flags=re.S)
  visible=re.sub(r'`[^`]*`','',visible)
  if '[[' in visible:warnings.append(f'{rel}: wikilinks are an Obsidian extension; add canonical Markdown links for portability')
  for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^\s)]+)\)',visible):
   target=unquote(target.strip('<>'));parts=urlsplit(target)
   if parts.scheme or parts.netloc or not parts.path:continue
   dest=(root/parts.path.lstrip('/') if parts.path.startswith('/') else p.parent/parts.path).resolve()
   if not dest.is_relative_to(root.resolve()):warnings.append(f'{rel}: link leaves bundle: {target}')
   elif not dest.exists():warnings.append(f'{rel}: unresolved link: {target}')
 return {'target':'OKF 0.2 basic structure','documents':count,'errors':errors,'warnings':warnings,'core_structure_passed':not errors}

def init(root,title,profile,obsidian=False,dataview=False):
 root.mkdir(parents=True,exist_ok=True);made=[]
 for folder in PROFILES[profile]:
  p=root/folder/'index.md'
  if missing(p,f'# {folder.title()}\n\nAdd links and short descriptions as knowledge arrives.\n'):made.append(str(p.relative_to(root)))
 body='# '+title+'\n\n'+''.join(f'- [{f.title()}]({f}/index.md) — browse {f}\n' for f in PROFILES[profile])
 if missing(root/'index.md',fm({'okf_version':'0.2'},body)):made.append('index.md')
 if missing(root/'log.md','# Update log\n\n## '+datetime.now().astimezone().date().isoformat()+'\n\n- **Initialization**: Created the portable '+profile+' structure\n'):made.append('log.md')
 if obsidian or dataview:
  p=root/'.obsidian/app.json'
  if missing(p,json.dumps({'useMarkdownLinks':True},indent=2)+'\n'):made.append('.obsidian/app.json')
 if dataview:
  body='# Dashboard\n\n[Browse all knowledge](index.md)\n\n## Notes\n\n```dataview\nTABLE type, workflow_status, status\nWHERE file.name != "Dashboard"\nSORT file.name ASC\n```\n\n## Open tasks\n\n```dataview\nTASK\nWHERE !completed\n```\n\nQueries require the optional Dataview plugin. The index remains usable without it.\n'
  if missing(root/'Dashboard.md',fm({'type':'Dashboard','title':'Dashboard'},body)):made.append('Dashboard.md')
 return {'created':made,'dataview_requested':dataview,'dataview_installed':False,'obsidian_requested':obsidian or dataview}

def dataview(root,source):
 if not root.is_dir():raise ValueError('vault directory does not exist')
 manifest=json.loads((source/'manifest.json').read_text());pid=manifest.get('id')
 if pid!='dataview':raise ValueError('source manifest is not Dataview')
 if not (source/'main.js').is_file():raise ValueError('source has no main.js')
 config=root/'.obsidian';dest=config/'plugins/dataview'
 if dest.exists():raise ValueError('Dataview already exists; preserve it and use the normal update flow')
 register=config/'community-plugins.json';enabled=json.loads(register.read_text()) if register.exists() else []
 if not isinstance(enabled,list) or not all(isinstance(x,str) for x in enabled):raise ValueError('community-plugins.json must be a list of plugin IDs')
 dest.mkdir(parents=True)
 for name in ('manifest.json','main.js','styles.css'):
  if (source/name).is_file():shutil.copyfile(source/name,dest/name)
 (dest/'data.json').write_text(json.dumps({'enableDataviewJs':False,'enableInlineDataviewJs':False,'enableInlineDataview':True},indent=2)+'\n')
 if pid not in enabled:enabled.append(pid)
 register.write_text(json.dumps(enabled,indent=2)+'\n')
 return {'installed':pid,'version':manifest.get('version'),'activation_verified':False,'next':'Reload vault and verify a rendered Dataview query'}

def main():
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 p=sub.add_parser('init');p.add_argument('path',type=Path);p.add_argument('--title',required=True);p.add_argument('--profile',choices=PROFILES,default='meeting');p.add_argument('--obsidian',action='store_true');p.add_argument('--dataview',action='store_true')
 p=sub.add_parser('audit');p.add_argument('path',type=Path)
 p=sub.add_parser('dataview');p.add_argument('path',type=Path);p.add_argument('--from-plugin',type=Path,required=True)
 a=parser.parse_args();root=a.path.expanduser().resolve()
 try:
  if a.command=='init':result=init(root,a.title,a.profile,a.obsidian,a.dataview)
  elif a.command=='dataview':result=dataview(root,a.from_plugin.expanduser().resolve())
  else:
   if not root.is_dir():raise ValueError('bundle directory does not exist')
   result=audit(root)
  print(json.dumps(result,ensure_ascii=False,indent=2));return 1 if result.get('errors') else 0
 except (ValueError,OSError,json.JSONDecodeError) as e:print(str(e),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
