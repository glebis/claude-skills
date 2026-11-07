#!/usr/bin/env python3
"""Locate a configured local CLI; never install or download during a document run."""
import argparse,json,os,shutil,subprocess,sys,uuid
from pathlib import Path
from datetime import datetime,timezone

def main():
 p=argparse.ArgumentParser(add_help=False);p.add_argument('--runtime',type=Path)
 opts,args=p.parse_known_args();runtime=(opts.runtime or Path.home()/'.local/share/pii-pdf/venv').expanduser()
 exe=runtime/('Scripts/pii-pdf.exe' if os.name=='nt' else 'bin/pii-pdf')
 if not exe.is_file() and opts.runtime is None:
  located=shutil.which('pii-pdf');exe=Path(located) if located else exe
 try:
  if not exe.is_file():raise FileNotFoundError('Local pii-pdf runtime is missing. Run setup mode or select --runtime PATH.')
  return subprocess.run([str(exe),*args],check=False).returncode
 except OSError as exc:
  print(json.dumps({'schema_version':'1.0','event':'error','ts':datetime.now(timezone.utc).isoformat(),'run_id':str(uuid.uuid4()),'seq':1,'code':'runtime_unavailable','message':str(exc),'exit_code':3,'retry':False}),flush=True)
  return 3
if __name__=='__main__':raise SystemExit(main())
