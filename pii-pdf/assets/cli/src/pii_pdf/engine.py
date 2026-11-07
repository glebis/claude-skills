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
 ('ADDRESS',re.compile(r'(?<![\d.,/:\-])\b\d{1,5}\s+(?:[A-Za-z][A-Za-z.\x27-]*\s+){1,5}(?:Street|St|Road|Rd|Lane|Ln|Avenue|Ave|Drive|Dr|Close|Way|Place|Pl|Court|Ct|Boulevard|Blvd)\b[^\n;|]*',re.I)),
 ('PHONE',re.compile(r'(?<![\w])\+\d[\d ()\-]{7,22}\d(?![\w])')),
 ('ACCOUNT',re.compile(r'\b(?:Account(?:\s+(?:number|no\.?))?|A/C)\s*[:#]\s*([A-Za-z0-9][A-Za-z0-9 -]{3,35}?)(?=\s*\||\s{2,}|$)',re.I|re.M)),
]
# Account numbers (0.1.3). General statement conventions, applied locally:
# 1) a field-initial account label followed by a 6-17 digit value (spaces/hyphens allowed);
# 2) a label-only line paired with a digits-only line to its right or directly below;
# 3) document-wide propagation of found values (standalone tokens only), incl. the account
#    number embedded in GB/IE IBANs (BBAN = 4 bank + 6 sort/NSC + 8 account digits).
ACCOUNT_LABEL=r'(?:account\s+(?:number|no\.?|nr\.?|#)|acct\.?(?:\s+no\.?)?|a/c(?:\s+no\.?)?|account)'
ACCOUNT_VALUE=r'(\d(?:[ -]?\d){5,16})(?![\w-])'
ACCOUNT_LABELLED=re.compile(r'(?:^|[\u00b7|/,;\u2013\u2014-][ \t]*|[ \t]{2,})'+ACCOUNT_LABEL+r'[ \t]*(?:[:#.][ \t]*)?'+ACCOUNT_VALUE,re.I|re.M)
ACCOUNT_LABEL_ONLY=re.compile(r'^\s*'+ACCOUNT_LABEL+r'\s*[:#.]?\s*$',re.I)
ACCOUNT_VALUE_ONLY=re.compile(r'^\s*'+ACCOUNT_VALUE+r'\s*$')
IBAN_ACCOUNT_SLICE={'GB':slice(14,22),'IE':slice(14,22)}
def account_pattern(digits):
 return re.compile(r'(?<![\w-])'+r'[ -]?'.join(digits)+r'(?![\w-])')
# Multi-line addresses (0.1.4): a postcode-ending line plus the left-aligned lines directly
# above it, up to the topmost address start (unit keyword, house number, street pattern or
# text after an "address:" label). The postcode is the evidence, so no street-type list.
POSTCODE_END=re.compile(r'(?:\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[ABD-HJLNP-UW-Z]{2}|\b[A-Z]{2}\s\d{5}(?:-\d{4})?|\b[AC-FHKNPRTV-Y]\d[\dW]\s?[AC-FHKNPRTV-Y\d]{4})\s*[.,]?\s*$')
ADDRESS_CUE=re.compile(r'address(?:\s+on\s+file)?\s*:\s*',re.I)
ADDRESS_START=re.compile(r'^(?:(?:flat|apartment|apt\.?|unit|suite)\s+\w|\d{1,5}[A-Za-z]?,?\s+[A-Za-z])',re.I)
MONEY=re.compile(r'\d[.,]\d{2}(?!\d)')
# Table safety (0.1.6): an address tail stops at a date, a money amount or a wide gap, and
# PERSON spans with digits, line breaks, organisation words or form labels are rejected.
ADDRESS_TAIL_STOP=re.compile(r'\s{2,}|\s(?=\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b)|\s(?=[-+]?[$\u00a3\u20ac]?\d[\d.,]*[.,]\d{2}(?!\d))')
NOT_PERSON=re.compile(r'\d|\n|\b(?:ltd|limited|llc|llp|plc|inc|corp|gmbh|dac|teoranta|co|company|group|partners|bank|banc|building|society|mutual|union|council|trust|services|holdings|iban|bic|swift|sort|account|statement|balance|amount|ref|reference|invoice|total)\b',re.I)
PERSON_CUT=re.compile(r'\n|\s[-\u2013\u2014\u00b7|]\s|\s(?=(?:account|acct|a/c|iban|bic|sort|statement|balance|ref|mob|tel|phone|e-?mail|continued)\b)',re.I)
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
    if typ=='ADDRESS':
     cut=ADDRESS_TAIL_STOP.search(value)
     if cut:value=value[:cut.start()].rstrip(' ,;-');e=s+len(value)
    if any(s<b and e>a for a,b,_,_ in out):continue
    out.append((s,e,typ,value))
  if 'ACCOUNT' in self.options.entities:
   for m in ACCOUNT_LABELLED.finditer(text):
    s,e=m.span(1)
    if not any(s<b and e>a for a,b,_,_ in out):out.append((s,e,'ACCOUNT',text[s:e]))
   for digits in sorted(getattr(self,'known_accounts',()),key=len,reverse=True):
    for m in account_pattern(digits).finditer(text):
     s,e=m.span()
     if not any(s<b and e>a for a,b,_,_ in out):out.append((s,e,'ACCOUNT',text[s:e]))
  for ent in self.nlp(text).ents:
   if ent.label_!='PERSON' or 'PERSON' not in self.options.entities:continue
   # Split spans at line breaks, trim each part at a field separator or label, then judge each part.
   pos=ent.start_char
   for part in ent.text.split('\n'):
    s=pos+len(part)-len(part.lstrip());txt=part.strip();pos+=len(part)+1
    cut=PERSON_CUT.search(txt)
    if cut:txt=txt[:cut.start()]
    txt=txt.rstrip(' ,;:-')
    if not re.search(r'[A-Za-z]{2}',txt) or NOT_PERSON.search(txt):continue
    e=s+len(txt)
    if any(s<b and e>a for a,b,_,_ in out):continue
    out.append((s,e,'PERSON',txt))
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
  if 'ACCOUNT' in self.options.entities:det+=self.paired_accounts(lines,source,det)
  if 'ADDRESS' in self.options.entities:
   new,drop=self.address_blocks(lines,source,det)
   det=[d for d in det if id(d) not in drop]+new
  return det

 def address_blocks(self,lines,source,existing):
  fitz=self.fitz;info=[]
  for t,boxes in lines:
   if not boxes or not t.strip():continue
   # Split at wide horizontal gaps: OCR (and sometimes native) lines can join separate columns.
   segs=[[boxes[0]]]
   for prev,cur in zip(boxes,boxes[1:]):
    h=max(prev[2][3]-prev[2][1],1)
    if cur[2][0]-prev[2][2]>2.0*h:segs.append([cur])
    else:segs[-1].append(cur)
   for sg in segs:
    s0,e0=sg[0][0],sg[-1][1];st=t[s0:e0]
    if not st.strip():continue
    cue=ADDRESS_CUE.search(st);off=cue.end() if cue else len(st)-len(st.lstrip())
    body_boxes=[b for s,e,b in sg if e>s0+off]
    if not body_boxes:continue
    r=fitz.Rect(body_boxes[0])
    for b in body_boxes[1:]:r|=fitz.Rect(b)
    body=st[off:]
    info.append({'body':body,'rect':r,'seg_x0':sg[0][2][0],'money':bool(MONEY.search(body)),
                 'anchor':bool(cue and body.strip()) or bool(ADDRESS_START.match(body)) or bool(RULES[2][1].search(body))})
  new,drop,used=[],set(),set()
  for i,P in enumerate(info):
   if i in used or P['money'] or not POSTCODE_END.search(P['body']):continue
   chain=[i];cur=P
   for _ in range(5):
    h=max(cur['rect'].height,1);best=None
    for j,Q in enumerate(info):
     if j in chain or j in used or Q['money']:continue
     gap=cur['rect'].y0-Q['rect'].y1
     aligned=abs(Q['rect'].x0-cur['rect'].x0)<6 or abs(Q['seg_x0']-cur['rect'].x0)<6  # wrapped continuation
     if -1<=gap<1.3*h and aligned and (best is None or gap<best[0]):best=(gap,j)
    if best is None:break
    chain.append(best[1]);cur=info[best[1]]
   anchors=[k for k,j in enumerate(chain) if info[j]['anchor']]
   if not anchors:continue
   block=list(reversed(chain[:max(anchors)+1]))
   n=len(block)
   for k,j in enumerate(block):
    L=info[j];used.add(j)
    if self.options.replacement=='blank':new_text=''
    elif n==1:new_text=self.substitute('ADDRESS',L['body'])
    else:new_text='8 Sample Road' if k==0 else ('York YO1 7AA' if k==n-1 else '')
    p=self.options.padding;r=L['rect']+(-p,-p,p,p)
    new.append({'type':'ADDRESS','text':L['body'].strip(),'rect':list(r),'source':source+':address-block',
                'replacement':new_text,'fragment':{'index':k,'count':n}})
    for d in existing:
     if d['type'] in ('ADDRESS','PERSON') and (fitz.Rect(d['rect'])&r).get_area()>0.5*fitz.Rect(d['rect']).get_area():drop.add(id(d))
  return new,drop

 def paired_accounts(self,lines,source,existing):
  # A label-only line ("Account number") owns the nearest digits-only line on its row or just below.
  fitz=self.fitz;out=[]
  def bbox(boxes):
   r=fitz.Rect(boxes[0][2])
   for b in boxes[1:]:r|=fitz.Rect(b[2])
   return r
  values=[(t,bbox(b)) for t,b in lines if b and ACCOUNT_VALUE_ONLY.match(t)]
  for t,b in lines:
   if not b or not ACCOUNT_LABEL_ONLY.match(t):continue
   lab=bbox(b);h=max(lab.height,1);best=None
   for vt,vr in values:
    same_row=abs((vr.y0+vr.y1)/2-(lab.y0+lab.y1)/2)<.6*h and 0<=vr.x0-lab.x1<220
    below=0<=vr.y0-lab.y1<1.6*h and abs(vr.x0-lab.x0)<24
    if not(same_row or below):continue
    d=(vr.x0-lab.x1) if same_row else (vr.y0-lab.y1)*4
    if best is None or d<best[0]:best=(d,vt,vr)
   if best is None:continue
   _,vt,vr=best;p=self.options.padding;r=vr+(-p,-p,p,p)
   if any(e['type']=='ACCOUNT' and (fitz.Rect(e['rect'])&r).get_area()>0 for e in existing+out):continue
   value=vt.strip()
   out.append({'type':'ACCOUNT','text':value,'rect':list(r),'source':source+':label-pair','replacement':self.substitute('ACCOUNT',value)})
  return out

 def learn_accounts(self,detections):
  # Collect account digits for document-wide propagation (and from GB/IE IBANs).
  for d in detections:
   digits=re.sub(r'\D','',d['text'])
   if d['type']=='ACCOUNT' and 6<=len(digits)<=17:self.known_accounts.add(digits)
   if d['type']=='IBAN':
    c=re.sub(r'\s','',d['text']).upper();sl=IBAN_ACCOUNT_SLICE.get(c[:2])
    if sl and len(c)==22 and c[sl].isdigit():self.known_accounts.add(c[sl])

 def process(self,input_path:Path,pdf_path:Path|None,evidence_dir:Path|None=None,*,overwrite:bool=False):
  started=time.perf_counter();input_path=Path(input_path);o=self.options;fitz=self.fitz
  if pdf_path is not None:
   pdf_path=Path(pdf_path)
   if input_path.resolve()==pdf_path.resolve() or (pdf_path.exists() and os.path.samefile(input_path,pdf_path)):
    raise EngineError('same_path','Input and output must be different files')
  try:doc=fitz.open(input_path)
  except Exception as exc:raise EngineError('invalid_pdf',str(exc)) from exc
  temp=None;placeholder=None;self.known_accounts=set()
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
   # Pass 1: read every page once (native + OCR) and learn account numbers document-wide.
   self.known_accounts=set();page_lines=[]
   for pi,page in enumerate(doc):
    has_images=bool(page.get_images(full=True));ocr_lines=None
    if o.ocr_mode=='always' or (o.ocr_mode=='auto' and has_images):
     evidence=Path(evidence_dir)/f'{input_path.stem}-p{pi+1}.tsv' if evidence_dir is not None and o.evidence else None
     ocr_lines=self.ocr(page,evidence)
    native_lines=self.native(page);page_lines.append((native_lines,ocr_lines,has_images))
    if 'ACCOUNT' in o.entities:
     self.learn_accounts(self.locate(native_lines,'native')+(self.locate(ocr_lines,'ocr') if ocr_lines else []))
   # Pass 2: detect with propagation, then redact.
   for pi,page in enumerate(doc):
    native_lines,ocr_lines,has_images=page_lines[pi]
    detections=self.locate(native_lines,'native')
    if o.ocr_mode=='never' and has_images:
     review=True;record['unsupported'].append({'kind':'raster_detection_skipped','page':pi})
    if ocr_lines is not None:
     for hit in self.locate(ocr_lines,'ocr'):
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
