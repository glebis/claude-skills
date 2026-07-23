"""Reference-image annotator: images dir -> refs.json role manifest.

SKILL CONVENTION (not DTCG). Multi-reference generation needs to know WHAT to
take from each reference image ("palette from A, composition from B"). The
source of truth is a `refs.json` sidecar next to the images:

    {"images": [{"file": "a.png", "take": ["palette", "mood"], "note": "…"}]}

`annotate <dir>` serves a single-page HTML interface over http://127.0.0.1
showing ALL images with per-image role chips and a free-text note. Saving
POSTs back to this server, which writes `refs.json`. If GROQ_API_KEY is set,
each note gains a mic button: audio is recorded in the browser and proxied to
Groq Whisper (`whisper-large-v3`) for transcription; without the key the
interface degrades to text-only. Stdlib only — no dependency added.
"""

import functools
import http.server
import json
import mimetypes
import os
import pathlib
import socketserver
import threading
import urllib.request
import uuid
import webbrowser

from . import serve as serve_mod

# Role vocabulary for `take`. Kept coarse on purpose: providers map these onto
# their own mechanisms (style ref channels, palette params, NL prompt clauses).
ROLES = ["style", "palette", "composition", "subject", "texture", "typography", "mood"]

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3"


def list_images(directory):
    directory = pathlib.Path(directory)
    return sorted(
        p.name for p in directory.iterdir()
        if p.suffix.lower() in IMAGE_SUFFIXES and not p.name.startswith(".")
    )


def load_manifest(directory):
    path = pathlib.Path(directory) / "refs.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"images": []}


def merged_entries(directory):
    """One entry per image on disk, carrying over any existing annotations."""
    manifest = load_manifest(directory)
    known = {e.get("file"): e for e in manifest.get("images", []) if isinstance(e, dict)}
    return [
        known.get(f, {"file": f, "take": [], "note": ""})
        for f in list_images(directory)
    ]


def save_manifest(directory, entries):
    path = pathlib.Path(directory) / "refs.json"
    clean = []
    valid = set(list_images(directory))
    for e in entries:
        if not isinstance(e, dict) or e.get("file") not in valid:
            continue
        clean.append({
            "file": e["file"],
            "take": [r for r in e.get("take", []) if r in ROLES],
            "note": str(e.get("note", ""))[:2000],
        })
    path.write_text(json.dumps({"images": clean}, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


def transcribe_groq(audio_bytes, content_type="audio/webm", api_key=None):
    """Send audio to Groq Whisper; return the transcript text (raises on error)."""
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    boundary = uuid.uuid4().hex
    ext = content_type.split("/")[-1].split(";")[0] or "webm"
    body = b"".join([
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{GROQ_MODEL}\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"note.{ext}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        audio_bytes,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = urllib.request.Request(
        GROQ_URL, data=body, method="POST",
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8")).get("text", "").strip()


def to_annotator_html(entries, voice=False):
    """Standalone page: all images, per-image role chips + note (+ mic if voice)."""
    data = json.dumps({"entries": entries, "roles": ROLES, "voice": voice},
                      ensure_ascii=False)
    return _PAGE_TEMPLATE.replace("__DATA__", data)


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reference annotator</title>
<style>
  :root { --bg:#0C1116; --panel:#0F151C; --ink:#F4F6F8; --muted:#AAB3BD;
          --border:#262D35; --accent:#BC9AFA; }
  @media (prefers-color-scheme: light) {
    :root { --bg:#FBF7F0; --panel:#FFFFFF; --ink:#14201E; --muted:#5c6670;
            --border:#E2DCCF; --accent:#7c4fd0; }
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--ink);
         font: 16px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; padding:2rem; }
  h1 { font-size:1.3rem; margin-bottom:0.4rem; }
  .hint { color:var(--muted); margin-bottom:1.6rem; max-width:70ch; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(340px,1fr)); gap:1rem; }
  .card { background:var(--panel); border:1px solid var(--border); border-radius:8px;
          padding:1rem; display:flex; flex-direction:column; gap:0.8rem; }
  .card img { width:100%; height:220px; object-fit:contain; border-radius:4px;
              background:rgba(127,127,127,0.08); }
  .fname { font-size:0.8rem; color:var(--muted); overflow-wrap:anywhere; }
  .roles { display:flex; flex-wrap:wrap; gap:0.4rem; }
  .roles label { border:1px solid var(--border); border-radius:999px;
                 padding:0.3rem 0.75rem; cursor:pointer; font-size:0.85rem;
                 user-select:none; }
  .roles input { position:absolute; opacity:0; pointer-events:none; }
  .roles input:checked + span { color:var(--accent); font-weight:700; }
  .roles label:has(input:checked) { border-color:var(--accent); }
  .roles label:focus-within { outline:2px solid var(--accent); outline-offset:2px; }
  .noterow { display:flex; gap:0.5rem; align-items:flex-start; }
  textarea { flex:1; background:transparent; color:var(--ink); resize:vertical;
             border:1px solid var(--border); border-radius:6px; min-height:3.2rem;
             padding:0.5rem; font:inherit; font-size:0.9rem; }
  button { background:transparent; color:var(--ink); border:1px solid var(--border);
           border-radius:6px; padding:0.5rem 0.9rem; font:inherit; cursor:pointer; }
  button:hover { border-color:var(--accent); }
  .mic.rec { background:var(--accent); color:var(--bg); }
  .savebar { position:sticky; bottom:1rem; margin-top:2rem; display:flex; gap:1rem;
             align-items:center; }
  #save { background:var(--accent); color:var(--bg); font-weight:700;
          padding:0.7rem 1.6rem; border:none; }
  #status { color:var(--muted); }
</style>
</head>
<body>
<h1>Reference annotator</h1>
<p class="hint">For each image: pick what a generation should <strong>take</strong> from it,
and add a note (typed or dictated). Save writes <code>refs.json</code> next to the images.</p>
<div class="grid" id="grid"></div>
<div class="savebar"><button id="save">Save refs.json</button><span id="status"></span></div>
<script>
const DATA = __DATA__;
const grid = document.getElementById('grid');
const state = DATA.entries.map(e => ({file:e.file, take:[...(e.take||[])], note:e.note||''}));

state.forEach((entry, i) => {
  const card = document.createElement('div'); card.className = 'card';
  const img = document.createElement('img');
  img.src = encodeURIComponent(entry.file); img.alt = entry.file; img.loading = 'lazy';
  const name = document.createElement('div'); name.className = 'fname'; name.textContent = entry.file;
  const roles = document.createElement('div'); roles.className = 'roles';
  roles.setAttribute('role', 'group'); roles.setAttribute('aria-label', 'take from ' + entry.file);
  DATA.roles.forEach(r => {
    const label = document.createElement('label');
    const cb = document.createElement('input');
    cb.type = 'checkbox'; cb.checked = entry.take.includes(r);
    cb.addEventListener('change', () => {
      entry.take = cb.checked ? [...entry.take, r] : entry.take.filter(x => x !== r);
    });
    const span = document.createElement('span'); span.textContent = r;
    label.append(cb, span); roles.append(label);
  });
  const row = document.createElement('div'); row.className = 'noterow';
  const ta = document.createElement('textarea');
  ta.value = entry.note; ta.placeholder = 'note — what exactly, any caveats';
  ta.setAttribute('aria-label', 'note for ' + entry.file);
  ta.addEventListener('input', () => { entry.note = ta.value; });
  row.append(ta);
  if (DATA.voice) row.append(micButton(ta, entry));
  card.append(img, name, roles, row); grid.append(card);
});

function micButton(ta, entry) {
  const btn = document.createElement('button');
  btn.className = 'mic'; btn.textContent = '🎙'; btn.title = 'dictate note';
  btn.setAttribute('aria-label', 'dictate note for ' + entry.file);
  let rec = null, chunks = [];
  btn.addEventListener('click', async () => {
    if (rec && rec.state === 'recording') { rec.stop(); return; }
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    chunks = []; rec = new MediaRecorder(stream);
    rec.ondataavailable = e => chunks.push(e.data);
    rec.onstop = async () => {
      btn.classList.remove('rec'); btn.textContent = '…';
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(chunks, {type: rec.mimeType || 'audio/webm'});
      try {
        const resp = await fetch('/transcribe', {method:'POST',
          headers:{'Content-Type': blob.type}, body: blob});
        const out = await resp.json();
        if (out.text) { ta.value = (ta.value ? ta.value + ' ' : '') + out.text;
                        entry.note = ta.value; }
        else status(out.error || 'transcription failed');
      } catch (err) { status('transcription failed: ' + err); }
      btn.textContent = '🎙';
    };
    rec.start(); btn.classList.add('rec'); btn.textContent = '■';
  });
  return btn;
}

function status(msg) { document.getElementById('status').textContent = msg; }
document.getElementById('save').addEventListener('click', async () => {
  const resp = await fetch('/save', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({images: state})});
  status(resp.ok ? 'saved ✓' : 'save failed');
});
</script>
</body>
</html>
"""


class _AnnotateHandler(http.server.SimpleHTTPRequestHandler):
    """Serves the images dir; `/` is the annotator page, POST /save and
    POST /transcribe are the two API endpoints."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            entries = merged_entries(self.directory)
            voice = bool(os.environ.get("GROQ_API_KEY"))
            body = to_annotator_html(entries, voice=voice).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        if self.path == "/save":
            try:
                payload = json.loads(raw.decode("utf-8"))
                path = save_manifest(self.directory, payload.get("images", []))
                self._json(200, {"saved": str(path)})
            except (json.JSONDecodeError, OSError) as err:
                self._json(400, {"error": str(err)})
            return
        if self.path == "/transcribe":
            try:
                text = transcribe_groq(raw, self.headers.get("Content-Type", "audio/webm"))
                self._json(200, {"text": text})
            except Exception as err:  # network/key errors -> shown in the UI
                self._json(502, {"error": str(err)})
            return
        self._json(404, {"error": "unknown endpoint"})


def annotate(directory, port=None, host="127.0.0.1", open_browser=True, _block=True):
    """Serve the annotator for `directory`. Same contract as serve.serve()."""
    directory = str(pathlib.Path(directory).resolve())
    if not list_images(directory):
        raise FileNotFoundError(f"no images found in {directory}")
    port = port or serve_mod.find_free_port(host=host)
    handler = functools.partial(_AnnotateHandler, directory=directory)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    voice = "voice+text (Groq Whisper)" if os.environ.get("GROQ_API_KEY") else "text only (set GROQ_API_KEY for voice)"
    print(f"annotating {directory}\n  → {url}   [{voice}]\n  (Ctrl-C to stop)")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    if not _block:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return httpd, url
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        httpd.server_close()
    return httpd, url
