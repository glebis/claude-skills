"""Versioned JSON-lines interface. No inference dependencies imported at startup."""
from __future__ import annotations
import argparse
import contextlib
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

VERSION = '0.1.2'
ENTITIES = ('PERSON','ADDRESS','EMAIL','PHONE','IBAN','ACCOUNT')
EXIT_CODES = {0:'completed_unvalidated',1:'internal_error',2:'invalid_arguments',3:'dependency_unavailable',4:'needs_review',5:'processing_failed_or_partial',6:'output_conflict',130:'interrupted'}

class CLIError(Exception):
    def __init__(self, code, message, exit_code=2):
        self.code, self.message, self.exit_code = code, message, exit_code
        super().__init__(message)

class Emitter:
    def __init__(self):
        self.run_id = str(uuid.uuid4()); self.seq = 0
    def emit(self, event, **fields):
        self.seq += 1
        obj = dict(schema_version='1.0',event=event,ts=datetime.now(timezone.utc).isoformat(),run_id=self.run_id,seq=self.seq,**fields)
        print(json.dumps(obj,ensure_ascii=False,allow_nan=False,separators=(',',':')),flush=True)

class Parser(argparse.ArgumentParser):
    def error(self,message):
        raise CLIError('invalid_arguments',message)

def parser():
    p=Parser(prog='pii-pdf',description='Local experimental PDF PII engine. stdout is NDJSON; no output is certified anonymous.')
    p.add_argument('--json',action='store_true',help='Explicit NDJSON mode (also the default). Accepted before/after commands.')
    p.add_argument('--schema',action='store_true',help='Emit machine-readable CLI contract.')
    p.add_argument('--version',action='store_true',help='Emit version as JSON.')
    sub=p.add_subparsers(dest='command')
    sub.add_parser('schema',help='Discover options, event schemas and exit codes.')
    sub.add_parser('doctor',help='Check dependencies/model without downloading anything.').add_argument('--model',default='en_core_web_sm')
    for cmd in ('detect','redact'):
        s=sub.add_parser(cmd,help='Find PII without writing a PDF.' if cmd=='detect' else 'Write a modified copy; source PDFs remain intact.')
        s.add_argument('input',type=Path,help='One PDF or a directory of PDFs.')
        s.add_argument('-o','--output',type=Path,help='Output directory. Required for redact; optional for detect manifests.')
        s.add_argument('-r','--recursive',action='store_true',help='Search subdirectories and preserve their relative paths.')
        s.add_argument('--config',type=Path,help='JSON object of engine options. Explicit flags override it.')
        s.add_argument('--dry-run',action='store_true',help='Emit input/output plan only; no OCR, inference or writes.')
        s.add_argument('--overwrite',action='store_true',help='Allow replacement of existing output copies, never source PDFs.')
        s.add_argument('--fail-fast',action='store_true',help='Stop after first file error (default: continue batch).')
        s.add_argument('--include-sensitive',action='store_true',help='Include original PII in JSON records/manifests; default omits source text.')
        s.add_argument('--save-evidence',dest='evidence',action='store_true',default=None,help='Save raw OCR TSV (contains original text); requires --include-sensitive and --output.')
        for flag,choices in [('ocr-mode',('auto','always','never')),('replacement',('synthetic','blank')),('metadata',('strip','keep')),('attachments',('error','drop','keep'))]:
            s.add_argument('--'+flag,choices=choices,default=None)
        s.add_argument('--model',default=None,help='Installed spaCy English model name or local path; no auto-download.')
        s.add_argument('--dpi',type=int,default=None,help='OCR resolution, 72–600 dpi; default 300.')
        s.add_argument('--psm',type=int,default=None,help='Tesseract page segmentation, 3–13; default 3.')
        s.add_argument('--language',default=None,help='Installed Tesseract language(s), e.g. eng or eng+deu.')
        s.add_argument('--ocr-timeout',type=float,default=None,help='Maximum seconds per OCR page; default 60.')
        s.add_argument('--entities',default=None,help='Comma-separated entity types: '+','.join(ENTITIES))
        s.add_argument('--padding',type=float,default=None,help='Detection mask expansion in PDF points, 0–10; default 1.')
        s.add_argument('--max-font-size',type=float,default=None,help='Maximum replacement text size in points, 1–72; default 9.')
    return p

def action_schema(p):
    data=[]
    for a in p._actions:
        if isinstance(a,argparse._SubParsersAction):continue
        entry={'name':a.dest,'flags':a.option_strings,'required':a.required,'help':a.help,'default':str(a.default) if isinstance(a.default,Path) else a.default}
        if a.choices is not None:entry['choices']=list(a.choices)
        entry['type']='boolean' if isinstance(a,(argparse._StoreTrueAction,argparse._StoreFalseAction)) else ('integer' if a.type==int else 'number' if a.type==float else 'string')
        data.append(entry)
    return data

def contract(p):
    subs=next(a for a in p._actions if isinstance(a,argparse._SubParsersAction))
    envelope={'type':'object','required':['schema_version','event','ts','run_id','seq'], 'properties':{'schema_version':{'const':'1.0'},'event':{'type':'string'},'ts':{'type':'string','format':'date-time'},'run_id':{'type':'string'},'seq':{'type':'integer','minimum':1}},'additionalProperties':True}
    return {'name':'pii-pdf','version':VERSION,'transport':'ndjson','interactive':False,'global_options':action_schema(p),'commands':{k:action_schema(v) for k,v in subs.choices.items()},'engine_defaults':{'model':'en_core_web_sm','ocr_mode':'auto','dpi':300,'psm':3,'language':'eng','ocr_timeout':60.0,'entities':list(ENTITIES),'padding':1.0,'max_font_size':9.0,'replacement':'synthetic','metadata':'strip','attachments':'error','evidence':False},'entities':list(ENTITIES),'events':{'version':'version','schema':'contract','help':'command/options','doctor':'checks/ok','plan':'files/options','run_started':'command/input/files/options','file_started':'input/output','file_result':'input/output/status/counts/record','error':'code/message/exit_code/retry/input(optional)','summary':'total/succeeded/failed/needs_review/exit_code/validated/manifest'},'event_json_schema':envelope,'exit_codes':EXIT_CODES,'semantics':{'exit_0':'Operation completed, anonymity NOT validated.','needs_review':'Unsupported data retained, OCR disabled on image page or metadata kept.','detect':'No PDF mutation; optional sanitized manifest.','redact':'Atomic per-PDF writes; batches are NOT atomic. Prior completed files remain if later file fails.','sensitive_data':'Default omits original text and before-values from events and manifest. Filenames/coordinates/replacements remain. OCR evidence is opt-in and contains originals.','known_limitations':['Same experimental rules as prior benchmark; multiline PERSON can damage financial tables.','No exhaustive forensic audit or automatic quality certificate.','Synthetic substitutions are deterministic demo values; collisions possible; not a reversible mapping.']}}

def atom_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,prefix='.pii-',suffix='.tmp',delete=False) as f:
            tmp=Path(f.name);json.dump(data,f,ensure_ascii=False,allow_nan=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path);tmp=None
    finally:
        if tmp is not None and shutil.which('trash'):
            import subprocess
            subprocess.run(['trash',str(tmp)],capture_output=True,check=False)

def safe_record(value,include_sensitive=False):
    if include_sensitive:return value
    if isinstance(value,dict):return {k:safe_record(v) for k,v in value.items() if k not in ('text','before','after','old','original','ocr')}
    if isinstance(value,list):return [safe_record(v) for v in value]
    return value

def resolve_options(args):
    # Importing the engine module must itself stay dependency-free.
    from .engine import Options
    values=asdict(Options())
    if args.config:
        try:cfg=json.loads(args.config.read_text())
        except (OSError,ValueError) as e:raise CLIError('invalid_config','Cannot read JSON config: '+str(e)) from e
        if not isinstance(cfg,dict) or set(cfg)-set(values):raise CLIError('invalid_config','Config must be an object containing only engine option names: '+','.join(values))
        values.update(cfg)
    for k in values:
        v=getattr(args,k,None)
        if v is not None:values[k]=v
    if isinstance(values['entities'],str):values['entities']=[x.strip().upper() for x in values['entities'].split(',') if x.strip()]
    for name,lo,hi,kind in [('dpi',72,600,int),('psm',3,13,int),('ocr_timeout',.1,3600,(int,float)),('padding',0,10,(int,float)),('max_font_size',1,72,(int,float))]:
        v=values[name]
        if isinstance(v,bool) or not isinstance(v,kind) or not math.isfinite(v) or not lo<=v<=hi:raise CLIError('invalid_option',f'{name} must be finite in range {lo}..{hi}.')
    for name,choices in [('ocr_mode',('auto','always','never')),('replacement',('synthetic','blank')),('metadata',('strip','keep')),('attachments',('error','drop','keep'))]:
        if values[name] not in choices:raise CLIError('invalid_option',f'{name} must be one of '+','.join(choices))
    if not isinstance(values['evidence'],bool):raise CLIError('invalid_option','evidence must be a boolean.')
    for k in ('model','language'):
        if not isinstance(values[k],str) or not values[k].strip() or values[k].startswith('-'):raise CLIError('invalid_option',f'{k} must be a nonempty string, not an option.')
    if not isinstance(values['entities'],(list,tuple)) or not values['entities'] or any(x not in ENTITIES for x in values['entities']):raise CLIError('invalid_option','Unknown or empty entities list.')
    values['entities']=tuple(dict.fromkeys(values['entities']))
    if values['evidence'] and (not args.include_sensitive or not args.output):raise CLIError('sensitive_evidence_requires_opt_in','--save-evidence requires --include-sensitive and --output.')
    return Options(**values)

def plan(args):
    src=args.input.expanduser().resolve();out=args.output.expanduser().resolve() if args.output else None
    if not src.exists():raise CLIError('input_not_found','Input does not exist: '+str(src))
    if args.command=='redact' and out is None:raise CLIError('output_required','redact requires --output DIRECTORY.')
    if out is not None and out.exists() and not out.is_dir():raise CLIError('invalid_output','Output must be a directory.')
    if src.is_dir() and out==src:raise CLIError('source_output_overlap','Output directory must differ from input directory.',6)
    if src.is_file():
        if src.suffix.lower()!='.pdf':raise CLIError('unsupported_input','Input file must have a .pdf extension.')
        files=[(src,Path(src.name))]
    elif src.is_dir():
        candidates=src.rglob('*') if args.recursive else src.iterdir()
        files=[]
        for p in candidates:
            if not p.is_file() or p.suffix.lower()!='.pdf':continue
            if p.is_symlink():continue
            if out and p.resolve().is_relative_to(out):continue
            files.append((p,p.relative_to(src)))
        files.sort(key=lambda a:str(a[1]))
    else:raise CLIError('unsupported_input','Input must be a regular PDF file or a directory.')
    if not files:raise CLIError('no_pdf_files','No PDF files found (directory scan skips symlink files).')
    result=[]
    source_paths={p.resolve() for p,rel in files}
    source_inodes={(p.stat().st_dev,p.stat().st_ino) for p,rel in files}
    for p,rel in files:
        target=(out/rel) if out and args.command=='redact' else None
        if target and (target.resolve() in source_paths or (target.exists() and (target.stat().st_dev,target.stat().st_ino) in source_inodes)):raise CLIError('source_output_overlap','Refusing to overwrite any source PDF: '+str(target),6)
        if target and target.exists() and not args.overwrite:raise CLIError('output_exists','Output exists; use --overwrite for output copies: '+str(target),6)
        if target and target.exists() and not target.is_file():raise CLIError('output_conflict','Output path is not a file: '+str(target),6)
        result.append((p,target,rel))
    return src,out,result

def doctor(args,emit):
    checks={}
    for dist in ('PyMuPDF','spacy'):
        try:checks[dist]={'available':True,'version':importlib.metadata.version(dist)}
        except importlib.metadata.PackageNotFoundError:checks[dist]={'available':False}
    if checks['PyMuPDF'].get('available'):
        try:checks['PyMuPDF']['available']=(1,26,7)<=tuple(int(x) for x in checks['PyMuPDF']['version'].split('.'))<(1,27,0)
        except ValueError:checks['PyMuPDF']['available']=False
        checks['PyMuPDF']['required']='>=1.26.7,<1.27'
    checks['tesseract']={'available':bool(shutil.which('tesseract')),'path':shutil.which('tesseract')}
    try:
        with contextlib.redirect_stdout(sys.stderr):
            import spacy
            spacy.load(args.model,disable=['parser','lemmatizer','attribute_ruler','tagger'])
        checks['model']={'available':True,'name':args.model}
    except Exception:
        checks['model']={'available':False,'name':args.model,'install_hint':'python -m spacy download '+args.model}
    ok=all(x['available'] for x in checks.values());emit.emit('doctor',ok=ok,checks=checks)
    return 0 if ok else 3

def run(args,emit):
    options=resolve_options(args);src,out,files=plan(args)
    if args.dry_run:
        emit.emit('plan',command=args.command,options=asdict(options),files=[{'input':str(p),'output':str(t) if t else None} for p,t,r in files],writes=False)
        return 0
    from .engine import Engine, EngineError
    try:
        with contextlib.redirect_stdout(sys.stderr):engine=Engine(options)
    except (ImportError,ModuleNotFoundError) as e:raise CLIError('dependency_missing','Missing dependency: '+str(e),3) from e
    except Exception as e:raise CLIError('engine_unavailable','Cannot initialise engine: '+str(e),3) from e
    if out:out.mkdir(parents=True,exist_ok=True)
    manifest=out/('run-'+emit.run_id+'.json') if out else None
    records=[];succeeded=failed=review=0;failure_codes=[]
    emit.emit('run_started',command=args.command,input=str(src),files=len(files),options=asdict(options),include_sensitive=args.include_sensitive,validated=False)
    for path,target,rel in files:
        emit.emit('file_started',input=str(path),output=str(target) if target else None)
        try:
            if target:
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists() and not args.overwrite:raise CLIError('output_exists','Output appeared during processing: '+str(target),6)
            evidence=(out/'evidence'/rel.with_suffix('')) if options.evidence else None
            with contextlib.redirect_stdout(sys.stderr):record=engine.process(path,target,evidence,overwrite=args.overwrite)
            clean=safe_record(record,args.include_sensitive)
            count=sum(len(p['detections']) for p in record['pages'])
            result={'input':str(path),'output':str(target) if target else None,'status':'needs_review' if record.get('needs_review') else record['status'],'detections':count,'record':clean,'validated':False}
            records.append(result);succeeded+=1
            review+=bool(record.get('needs_review'))
            emit.emit('file_result',**result)
        except Exception as e:
            code=e.code if hasattr(e,'code') else 'processing_error'
            message=str(e) if isinstance(e,(CLIError,EngineError)) else type(e).__name__+': '+str(e)
            file_exit=e.exit_code if isinstance(e,CLIError) else 6 if code=='output_exists' else 5
            failure_codes.append(file_exit)
            emit.emit('error',code=code,message=message,input=str(path),exit_code=file_exit,retry=False)
            records.append({'input':str(path),'status':'error','code':code,'message':message});failed+=1
        if manifest:atom_json(manifest,{'schema_version':'1.0','run_id':emit.run_id,'command':args.command,'options':asdict(options),'validated':False,'files':records})
        if failed and args.fail_fast:break
    exit_code=(6 if failure_codes and all(c==6 for c in failure_codes) else 5) if failed else 4 if review else 0
    emit.emit('summary',total=len(files),attempted=succeeded+failed,succeeded=succeeded,failed=failed,needs_review=review,validated=False,exit_code=exit_code,manifest=str(manifest) if manifest else None)
    return exit_code

def main(argv=None):
    emit=Emitter();p=parser();argv=list(sys.argv[1:] if argv is None else argv)
    # Output is always NDJSON; allow --json at any position for agent convenience.
    wants_json='--json' in argv;argv=[a for a in argv if a!='--json']
    try:
        if '--help' in argv and wants_json:
            cmd=next((x for x in argv if x in ('redact','detect','doctor','schema')),None)
            emit.emit('help',contract=contract(p),command=cmd);return 0
        args=p.parse_args(argv)
        if args.version:emit.emit('version',version=VERSION);return 0
        if args.schema or args.command=='schema':emit.emit('schema',contract=contract(p));return 0
        if args.command=='doctor':return doctor(args,emit)
        if args.command not in ('redact','detect'):raise CLIError('command_required','Use redact, detect, doctor or schema. See --help.')
        return run(args,emit)
    except CLIError as e:
        emit.emit('error',code=e.code,message=e.message,exit_code=e.exit_code,retry=False);return e.exit_code
    except KeyboardInterrupt:
        emit.emit('error',code='interrupted',message='Interrupted; previously completed PDFs may remain.',exit_code=130,retry=False);return 130
    except BrokenPipeError:
        return 1
    except Exception as e:
        emit.emit('error',code='internal_error',message=type(e).__name__+': '+str(e),exit_code=1,retry=False);return 1

if __name__=='__main__':raise SystemExit(main())
