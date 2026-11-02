#!/usr/bin/env python3
"""Loopback-only editor and image-generation bridge. Keys remain in server memory."""
import argparse, base64, json, os, re, socket, threading, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial

MODELS={'openai':['gpt-image-1.5','gpt-image-1','gpt-image-1-mini'],'gemini':['gemini-nano-banana-2.1','gemini-3.1-flash-image','gemini-3-pro-image','gemini-2.5-flash-image']}
KEYS={'openai':os.getenv('OPENAI_API_KEY',''),'gemini':os.getenv('GEMINI_API_KEY',os.getenv('GOOGLE_API_KEY',''))}
LOCK=threading.Lock()
def request_json(url,headers,payload):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json',**headers},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=240) as response:return json.load(response)
    except urllib.error.HTTPError as e:
        # Never echo provider responses or request headers: they can contain credentials.
        messages={401:'API key rejected',403:'API access denied',429:'Provider rate limit or billing quota reached',400:'Provider rejected the image settings or prompt'}
        raise ValueError(messages.get(e.code,f'Provider request failed (HTTP {e.code})')) from None
    except (urllib.error.URLError,TimeoutError,socket.timeout):raise ValueError('Provider could not be reached or timed out. Check your connection before trying again') from None

def generate(value):
    provider=value.get('provider');model=value.get('model');prompt=value.get('prompt','').strip();ratio=value.get('ratio','1:1')
    if provider not in MODELS or model not in MODELS[provider]:raise ValueError('Choose a supported provider and model')
    if not prompt or len(prompt)>12000:raise ValueError('Enter a prompt under 12,000 characters')
    if ratio not in ['1:1','16:9','9:16','4:5']:raise ValueError('Unsupported aspect ratio')
    reference=value.get('reference');ref_image=None
    if reference:
        match=re.fullmatch(r'data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=]+)',reference)
        if not match:raise ValueError('Choose a valid image reference')
        try:raw=base64.b64decode(match[2],validate=True)
        except Exception:raise ValueError('Invalid reference image') from None
        if len(raw)>12*1024*1024:raise ValueError('Reference must be under 12 MB')
        ref_image={'mimeType':match[1],'data':match[2]}
    key=KEYS[provider]
    if not key:raise ValueError('Add an API key in Generation settings first')
    if value.get('style',True):prompt+='\nVisual style: minimal risograph print, warm paper #f3f0e8, charcoal black and red #d01920, tactile grainy geometric shapes, generous negative space. Artwork only, no text, no lettering, no watermark.'
    if provider=='openai':
        size='1536x1024' if ratio=='16:9' else '1024x1536' if ratio in ['9:16','4:5'] else '1024x1024'
        quality=value.get('quality','medium')
        if quality not in ['low','medium','high']:raise ValueError('Unsupported quality')
        payload={'model':model,'prompt':prompt,'n':1,'size':size,'quality':quality,'output_format':'png'}
        if reference:payload['images']=[{'image_url':reference}]
        result=request_json('https://api.openai.com/v1/images/'+('edits' if reference else 'generations'),{'Authorization':'Bearer '+key},payload)
        data=result.get('data',[{}])[0].get('b64_json');mime='image/png'
    else:
        result=request_json(f'https://generativelanguage.googleapis.com/v1/models/{model}:generateContent',{'x-goog-api-key':key},{'contents':[{'parts':[{'text':prompt}]+([{'inlineData':ref_image}] if ref_image else [])}],'generationConfig':{'responseFormat':{'image':{'aspectRatio':ratio}}}})
        parts=[p for candidate in result.get('candidates',[]) for p in candidate.get('content',{}).get('parts',[])]
        image=next((p.get('inlineData') or p.get('inline_data') for p in parts if p.get('inlineData') or p.get('inline_data')),{});data=image.get('data');mime=image.get('mimeType',image.get('mime_type','image/png'))
    if not data or mime not in ['image/png','image/jpeg','image/webp']:raise ValueError('Provider returned no usable image. Try a different prompt')
    try:raw=base64.b64decode(data,validate=True)
    except Exception:raise ValueError('Provider returned invalid image data') from None
    if len(raw)>25*1024*1024:raise ValueError('Generated image is too large')
    return {'src':f'data:{mime};base64,{data}','provider':provider,'model':model}

class Handler(SimpleHTTPRequestHandler):
    def valid_host(self):return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
    def respond(self,code,value):
        body=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if not self.valid_host():return self.respond(403,{'error':'Local access only'})
        if self.path=='/api/config':return self.respond(200,{'configured':{p:bool(k) for p,k in KEYS.items()},'models':MODELS})
        return super().do_GET()
    def do_POST(self):
        origin=self.headers.get('Origin');allowed=[f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']
        if not self.valid_host() or origin not in allowed or self.headers.get('X-Cover-Studio')!='1':return self.respond(403,{'error':'Use the local editor to make this request'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<17*1024*1024:raise ValueError('Invalid request size')
            value=json.loads(self.rfile.read(length))
            if self.path=='/api/settings':
                provider=value.get('provider');key=value.get('key','').strip()
                if provider not in KEYS or not key or len(key)>512:raise ValueError('Enter a valid API key')
                KEYS[provider]=key;return self.respond(200,{'configured':True})
            if self.path!='/api/generate':return self.respond(404,{'error':'Unknown action'})
            if not LOCK.acquire(blocking=False):return self.respond(409,{'error':'An image is already generating. Wait for it to finish'})
            try:result=generate(value)
            finally:LOCK.release()
            self.respond(200,result)
        except (ValueError,TypeError,KeyError,IndexError):self.respond(400,{'error':str(__import__('sys').exc_info()[1]) if isinstance(__import__('sys').exc_info()[1],ValueError) else 'Invalid generation request'})
        except Exception:self.respond(502,{'error':'Image generation failed. Your design is unchanged'})
    def log_message(self,*args):pass

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--port',type=int,default=8899);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(Path(args.directory).resolve())))
    print(f'Cover studio: http://127.0.0.1:{args.port}/',flush=True);server.serve_forever()
