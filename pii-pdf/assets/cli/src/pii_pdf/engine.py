"""Local PDF PII baseline. Successful processing is never an anonymity claim."""
from pathlib import Path
from dataclasses import dataclass
import csv, hashlib, io, os, re, shutil, subprocess, tempfile, time

class EngineError(Exception):
 def __init__(self, code, message):
  self.code=code
  super().__init__(message)

@dataclass
class Options:
 model: str = 'en_core_web_sm'
 ocr_mode: str = 'auto'
 dpi: int = 300
 psm: int = 3
 language: str = 'eng'
 ocr_timeout: float = 60.0
 entities: tuple = ('PERSON','ADDRESS','EMAIL','PHONE','IBAN','ACCOUNT')
 padding: float = 1.0
 max_font_size: float = 9.0
 replacement: str = 'synthetic'
 metadata: str = 'strip'
 attachments: str = 'error'
 evidence: bool = False

RULES=[
 ('EMAIL',re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')),
 ('IBAN',re.compile(r'\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b')),
 ('ADDRESS',re.compile(r'\b\d{1,5}\s+(?:[A-Za-z][A-Za-z.\x27-]*\s+){1,5}(?:Street|St|Road|Rd|Lane|Ln|Avenue|Ave|Drive|Dr|Close|Way|Place|Pl|Court|Ct|Boulevard|Blvd)\b[^\n;|]*',re.I)),
 ('PHONE',re.compile(r'(?<![\w])\+\d[\d ()\-]{7,22}\d(?![\w])')),
 ('ACCOUNT',re.compile(r'\b(?:Account(?:\s+(?:number|no\.?))?|A/C)\s*[:#]\s*([A-Za-z0-9][A-Za-z0-9 -]{3,35}?)(?=\s*\||\s{2,}|$)',re.I|re.M)),
]
IBAN_LENGTH={'GB':22,'DE':22,'FR':27,'NL':18,'ES':24,'IT':27,'IE':22,'BE':16,'CH':21,'AT':20}
class Engine:
 def __init__(self, options=None):
  self.options=options or Options()
  o=self.options
  if o.ocr_mode not in ('auto','always','never') or o.replacement not in ('synthetic','blank') or o.metadata not in ('strip','keep') or o.attachments not in ('error','drop','keep'):
   raise EngineError('invalid_options','Invalid processing policy')
  if o.dpi<=0 or o.ocr_timeout<=0 or o.max_font_size<=0 or o.padding<0:
   raise EngineError('invalid_options','Invalid numeric processing option')
  try:
   import fitz
   import spacy
  except ImportError as exc:raise EngineError('missing_dependency',str(exc)) from exc
  if tuple(int(x) for x in fitz.VersionBind.split('.')[:3]) < (1,26,7):
   raise EngineError('dependency_version','PyMuPDF >=1.26.7 is required')
  self.fitz=fitz
  try:self.nlp=spacy.load(o.model,disable=['parser','lemmatizer','attribute_ruler','tagger'])
  except Exception as exc:raise EngineError('model_unavailable',str(exc)) from exc

 def spans(self,text):
  out=[]
  for typ,rx in RULES:
   if typ not in self.options.entities:continue
   for m in rx.finditer(text):
    s,e=(m.span(1) if typ=='ACCOUNT' else m.span());value=text[s:e].strip();e=s+len(value)
    if typ=='IBAN':
     compact=value.replace(' ','')
     if len(compact)!=IBAN_LENGTH.get(compact[:2],len(compact)):continue
    if typ=='PHONE' and not 8<=len(re.sub(r'\D','',value))<=15:continue
    if any(s<b and e>a for a,b,_,_ in out):continue
    out.append((s,e,typ,value))
  for ent in self.nlp(text).ents:
   if ent.label_!='PERSON' or 'PERSON' not in self.options.entities:continue
   s,e=ent.start_char,ent.end_char
   if any(s<b and e>a for a,b,_,_ in out):continue
   out.append((s,e,'PERSON',ent.text))
  return sorted(out)
 def substitute(self,typ,value):
  if self.options.replacement=='blank':return ''
  n=int(hashlib.sha256(value.lower().encode()).hexdigest()[:8],16)
  return {'PERSON':['Emily Carter','Noah Bennett','Olivia Reed','Daniel Brooks'][n%4],
  'EMAIL':f'person{n%10000:04}@example.net','PHONE':f'+44 7700 900{n%1000:03}',
  'ADDRESS':'8 Sample Road, York YO1 7AA','IBAN':'GB29 NWBK 6016 1331 9268 19',
  'ACCOUNT':f'4839 2017 6600 {n%10000:04}'}[typ]
 def sanitize(self,text):
  found=self.spans(text)
  for s,e,typ,value in reversed(found):text=text[:s]+self.substitute(typ,value)+text[e:]
  return text,[{'type':t,'text':v,'replacement':self.substitute(t,v)} for s,e,t,v in found]
 def native(self,page):
  lines=[]
  for block in page.get_text('rawdict')['blocks']:
   for line in block.get('lines',[]):
    chars=[c for span in line['spans'] for c in span['chars']]
    if not chars:continue
    text=''.join(c['c'] for c in chars)
    lines.append((text,[(i,i+1,c['bbox']) for i,c in enumerate(chars)]))
  return lines
 def ocr(self,page,evidence):
  pix=page.get_pixmap(dpi=self.options.dpi,alpha=False)
  try:proc=subprocess.run(['tesseract','stdin','stdout','-l',self.options.language,'--psm',str(self.options.psm),'tsv'],input=pix.tobytes('png'),capture_output=True,check=True,timeout=self.options.ocr_timeout)
  except subprocess.TimeoutExpired as exc:raise EngineError('ocr_timeout','Tesseract exceeded the configured timeout') from exc
  except (OSError,subprocess.CalledProcessError) as exc:raise EngineError('ocr_failed','Tesseract failed') from exc
  if evidence is not None and self.options.evidence:evidence.write_bytes(proc.stdout)
  groups={}
  for r in csv.DictReader(io.StringIO(proc.stdout.decode()),delimiter='\t',quoting=csv.QUOTE_NONE):
   if r['level']!='5' or not r.get('text','').strip():continue
   key=tuple(r[k] for k in ['page_num','block_num','par_num','line_num']);groups.setdefault(key,[]).append(r)
  lines=[]
  for words in groups.values():
   text='';boxes=[]
   for w in words:
    if text:text+=' '
    start=len(text);text+=w['text'];x,y,ww,hh=[int(w[k]) for k in ['left','top','width','height']]
    boxes.append((start,len(text),[x*72/self.options.dpi,y*72/self.options.dpi,(x+ww)*72/self.options.dpi,(y+hh)*72/self.options.dpi]))
   lines.append((text,boxes))
  return lines

 def locate(self,lines,source):
  # NER sees complete page text; coordinates remain tied to exact native chars/OCR tokens.
  text='\n'.join(t for t,b in lines);det=[];offset=0;records=[]
  for t,boxes in lines:
   records.append((offset,offset+len(t),boxes));offset+=len(t)+1
  for start,end,typ,value in self.spans(text):
   for ls,le,boxes in records:
    if not (start<le and end>ls):continue
    hits=[self.fitz.Rect(box) for s,e,box in boxes if ls+s<end and ls+e>start]
    if not hits:continue
    r=hits[0]
    for b in hits[1:]:r|=b
    p=self.options.padding;r+=(-p,-p,p,p)
    det.append({'type':typ,'text':value,'rect':list(r),'source':source,'replacement':self.substitute(typ,value)})
  return det

 def process(self,input_path:Path,pdf_path:Path|None,evidence_dir:Path|None=None,*,overwrite:bool=False):
  started=time.perf_counter();input_path=Path(input_path);o=self.options;fitz=self.fitz
  if pdf_path is not None:
   pdf_path=Path(pdf_path)
   if input_path.resolve()==pdf_path.resolve() or (pdf_path.exists() and os.path.samefile(input_path,pdf_path)):
    raise EngineError('same_path','Input and output must be different files')
  try:doc=fitz.open(input_path)
  except Exception as exc:raise EngineError('invalid_pdf',str(exc)) from exc
  temp=None;placeholder=None
  record={'document':input_path.stem,'input_sha256':hashlib.sha256(input_path.read_bytes()).hexdigest(),'pages':[],'auxiliary':[],'unsupported':[],'metadata_policy':'remove document-info and XMP' if o.metadata=='strip' else 'keep document-info and XMP','status':'processed_unvalidated'}
  review=False
  try:
   if doc.needs_pass:raise EngineError('encrypted_pdf','Encrypted input is not supported')
   # Preflight attachments before producing either a PDF or OCR evidence.
   attachments=[]
   for name in list(doc.embfile_names()):
    raw=doc.embfile_get(name);txt=None
    if name.lower().endswith('.txt'):
     try:txt=raw.decode('utf-8')
     except UnicodeDecodeError:pass
    if txt is None:
     issue={'kind':'attachment-encoding' if name.lower().endswith('.txt') else 'attachment','name':name,'action':o.attachments}
     record['unsupported'].append(issue)
     if o.attachments=='error':raise EngineError('unsupported_attachment','Unsupported attachment: '+name)
     if o.attachments=='keep':review=True
    attachments.append((name,txt))
   if o.evidence and evidence_dir is not None:Path(evidence_dir).mkdir(parents=True,exist_ok=True)
   for pi,page in enumerate(doc):
    detections=self.locate(self.native(page),'native');has_images=bool(page.get_images(full=True))
    if o.ocr_mode=='never' and has_images:
     review=True;record['unsupported'].append({'kind':'raster_detection_skipped','page':pi})
    if o.ocr_mode=='always' or (o.ocr_mode=='auto' and has_images):
     evidence=Path(evidence_dir)/f'{input_path.stem}-p{pi+1}.tsv' if evidence_dir is not None and o.evidence else None
     for hit in self.locate(self.ocr(page,evidence),'ocr'):
      r=fitz.Rect(hit['rect']);duplicate=False
      for other in detections:
       q=fitz.Rect(other['rect']);inter=(r&q).get_area()
       if other['type']==hit['type'] and inter/max(min(r.get_area(),q.get_area()),1)>.6:
        other['rect']=list(r|q);other['source']='native+ocr';duplicate=True;break
      if not duplicate:detections.append(hit)
    if pdf_path is not None:
     clusters=[]
     for hit in detections:
      r=fitz.Rect(hit['rect']);members=[hit];remaining=[]
      for cluster in clusters:
       if (r&cluster[0]).get_area()>0:r|=cluster[0];members+=cluster[1]
       else:remaining.append(cluster)
      clusters=remaining+[(r,members)]
     # Mask merged groups, then insert a replacement for each evidence detection.
     for r,members in clusters:page.add_redact_annot(r,fill=(1,1,1))
     page.apply_redactions(images=2,graphics=0,text=0)
     for hit in detections:
      r=fitz.Rect(hit['rect']);new=hit['replacement']
      if new:
       size=min(o.max_font_size,max(4,r.height*.85),(r.width-2)/max(fitz.get_text_length(new,fontsize=1),1))
       if size>0:page.insert_text((r.x0+1,r.y1-max(1,r.height*.16)),new,fontsize=size)
    for widget in list(page.widgets() or []):
     value,hits=self.sanitize(widget.field_value or '')
     if hits:
      record['auxiliary'].append({'page':pi,'kind':'widget','before':widget.field_value,'after':value,'detections':hits})
      if pdf_path is not None:widget.field_value=value;widget.update()
    for annot in list(page.annots() or []):
     info=annot.info
     for k in ['content','title','subject']:
      value,hits=self.sanitize(info.get(k,'') or '')
      if hits:record['auxiliary'].append({'page':pi,'kind':'annotation.'+k,'detections':hits});info[k]=value
     if pdf_path is not None:annot.set_info(info)
    record['pages'].append({'page':pi,'detections':detections})
   if o.metadata=='keep':
    if any(doc.metadata.values()) or doc.get_xml_metadata():
     review=True;record['unsupported'].append({'kind':'metadata_retained'})
   elif pdf_path is not None:doc.set_metadata({});doc.del_xml_metadata()
   for name,txt in attachments:
    if txt is None:
     if o.attachments=='drop' and pdf_path is not None:doc.embfile_del(name)
     continue
    value,hits=self.sanitize(txt);newname,namehits=self.sanitize(name)
    record['auxiliary'].append({'kind':'attachment','name':name,'detections':hits+namehits})
    if pdf_path is not None:doc.embfile_del(name);doc.embfile_add(newname or 'attachment.txt',value.encode('utf-8'))
   if pdf_path is not None:
    pdf_path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.'+pdf_path.name+'.',suffix='.pdf',dir=pdf_path.parent);os.close(fd)
    doc.save(temp,garbage=4,deflate=True,clean=True)
    doc.close()
    if not overwrite:
     # Reserve the output name exclusively (no clobber), then atomically replace our own
     # empty placeholder with the finished file. No second hard link exists, so no cleanup
     # step can ever trash the published copy (0.1.1 bug: macOS /usr/bin/trash resolved the
     # temp hard link to the published name and moved the output to the Trash).
     try:pfd=os.open(pdf_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
     except FileExistsError as exc:raise EngineError('output_exists','Output exists at publication time') from exc
     placeholder=(pdf_path,os.fstat(pfd).st_ino);os.close(pfd)
    os.replace(temp,pdf_path);temp=None;placeholder=None
    record['output_sha256']=hashlib.sha256(pdf_path.read_bytes()).hexdigest()
   record['status']='processed_unvalidated'
   record['needs_review']=review
   record['seconds']=round(time.perf_counter()-started,3)
   return record
  finally:
   if not doc.is_closed:doc.close()
   if temp is not None and shutil.which('trash'):
    # Recoverable cleanup when available; otherwise leave unpublished temp for review.
    subprocess.run(['trash',temp],capture_output=True,check=False)
   if placeholder is not None and shutil.which('trash'):
    # Publication failed after reserving the name: discard only our own, still-empty placeholder.
    try:st=os.stat(placeholder[0])
    except FileNotFoundError:st=None
    if st is not None and st.st_ino==placeholder[1] and st.st_size==0 and st.st_nlink==1:
     subprocess.run(['trash',str(placeholder[0])],capture_output=True,check=False)
