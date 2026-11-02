"""Explicit voice controls; source speech is never evaluated as executable code."""
import json,re
from pathlib import Path
from live_wispr import atomic,now

def parse(text):
 # Whole utterance only: mentioning or quoting a command does not invoke it.
 value=re.sub(r'[,:]+',' ',text.strip().lower())
 value=re.sub(r'\s+',' ',value).rstrip('.!?').strip()
 if not value.startswith('agent '):return None
 command=value[6:]
 aliases={'analyze':'start','analyse':'start','from this moment analyze':'start','from this moment analyse':'start','start analyzing':'start','start analysing':'start','pause':'pause','stop':'pause','resume':'resume','status':'status','update':'update'}
 return aliases.get(command)

class CommandGate:
 def __init__(self,root,records):
  self.root=Path(root);self.path=self.root/'.live/commands.json'
  if self.path.exists():self.state=json.loads(self.path.read_text())
  else:
   self.state={'enabled':False,'armed_at':now(),'seen':{k:v.get('revision',0) for k,v in records.items()},'command_ids':[],'selected':{},'history':[],'request':None,'worker_status':'not_configured'}
   self.save()
 def save(self):atomic(self.path,json.dumps(self.state,ensure_ascii=False,indent=2))
 def apply(self,events):
  changed=False
  for e in events:
   if e['kind']!='transcript':continue
   ident=e['id'];revision=e['revision']
   if self.state['seen'].get(ident,0)>=revision:continue
   existed=ident in self.state['seen'];self.state['seen'][ident]=revision
   command=parse(e['text'])
   if command and not existed:
    self.state['command_ids'].append(ident)
    self.state['history'].append({'id':ident,'action':command,'at':now()})
    if command=='start':
     self.state.update(enabled=True,selected={},request=None)
    elif command=='pause':self.state.update(enabled=False,request=None)
    elif command=='resume':self.state['enabled']=True
    elif command=='update' and self.state['selected']:changed=True
    continue
   if ident in self.state['command_ids']:continue # corrections never reinterpret a control
   if ident in self.state['selected'] or (self.state['enabled'] and not existed):
    self.state['selected'][ident]={'id':ident,'revision':revision,'text':e['text'],'source_timestamp':e['source_timestamp']}
    if self.state['enabled']:changed=True
  if changed:
   self.state['request']={'id':now(),'created_at':now(),'sources':list(self.state['selected'].values())}
  self.save()
  return changed
