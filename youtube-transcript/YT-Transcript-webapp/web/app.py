#!/usr/bin/env python3
"""
YouTube Transcript Downloader — local web app.

Paste YouTube URLs or playlist links, pick language and options,
get transcripts (and optionally videos) downloaded to a folder you choose.
"""

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import uuid
from pathlib import Path

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

from flask import Flask, Response, jsonify, request, send_from_directory

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
EXTRACT_SCRIPT = SCRIPT_DIR.parent / "scripts" / "extract_transcript.py"

ALLOWED_HOSTS = {"www.youtube.com", "youtube.com", "youtu.be", "m.youtube.com"}

DEFAULT_TRANSCRIPT_DIR = Path.home() / "Downloads" / "yt-transcripts"
DEFAULT_VIDEO_DIR = Path.home() / "Downloads" / "yt-videos"

KNOWN_YTDLP_PATHS = [
    Path("/usr/local/bin/yt-dlp"),
    Path("/opt/homebrew/bin/yt-dlp"),
    Path.home() / ".local" / "bin" / "yt-dlp",
]

# ---------------------------------------------------------------------------
# yt-dlp discovery
# ---------------------------------------------------------------------------

def find_ytdlp() -> str | None:
    found = shutil.which("yt-dlp")
    if found:
        return found
    for p in KNOWN_YTDLP_PATHS:
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    return None


YTDLP = find_ytdlp()

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)
jobs: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_youtube_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.hostname in ALLOWED_HOSTS
    except Exception:
        return False


def is_playlist_url(url: str) -> bool:
    return "list=" in url


def expand_playlist(url: str, max_videos: int, ytdlp: str) -> list[dict]:
    cmd = [ytdlp, "--flat-playlist", "--dump-json", "--no-exec", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    videos = []
    for line in result.stdout.strip().splitlines():
        try:
            entry = json.loads(line)
            vid_url = entry.get("url") or entry.get("webpage_url", "")
            if not vid_url.startswith("http"):
                vid_url = f"https://www.youtube.com/watch?v={entry.get('id', '')}"
            title = entry.get("title", "")
            videos.append({"url": vid_url, "title": title})
        except json.JSONDecodeError:
            continue
        if len(videos) >= max_videos:
            break
    return videos


def extract_metadata(url: str, ytdlp: str) -> dict | None:
    cmd = [ytdlp, "--no-exec", "--no-playlist", "--restrict-filenames",
           "--dump-json", "--no-download", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def download_video(url: str, output_dir: Path, ytdlp: str, name: str | None = None) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    template = f"{output_dir}/{name}.%(ext)s" if name else f"{output_dir}/%(title)s.%(ext)s"
    cmd = [ytdlp, "--no-exec", "--no-playlist", "--restrict-filenames",
           "-o", template, url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if "Destination:" in line:
            return Path(line.split("Destination: ")[-1].strip())
        if "has already been downloaded" in line:
            return Path(line.replace("[download] ", "").split(" has already")[0].strip())
    merged = [l for l in result.stdout.splitlines() if "Merging" in l]
    if merged and '"' in merged[-1]:
        return Path(merged[-1].split('"')[1])
    candidates = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def extract_transcript(url: str, output_dir: Path, ytdlp: str,
                       langs: list[str], name: str | None = None) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = str(Path(ytdlp).parent) + os.pathsep + env.get("PATH", "")
    env["YT_TRANSCRIPT_OUTPUT_DIR"] = str(output_dir)
    env["YT_TRANSCRIPT_LANGS"] = ",".join(langs)

    cmd = [sys.executable, str(EXTRACT_SCRIPT), url]
    if name:
        cmd.append(f"{name}.md")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        if "Saved to:" in line:
            path_str = line.split("Saved to:")[-1].strip().lstrip("\u2713 ").strip()
            return Path(path_str)
    return None


def sanitize_name(title: str) -> str:
    clean = re.sub(r'[<>:"/\\|?*]', '', title)
    return clean.replace(' ', '_')[:80]


# ---------------------------------------------------------------------------
# Job processor (runs in background thread)
# ---------------------------------------------------------------------------

def process_job(job_id: str):
    job = jobs[job_id]
    q: queue.Queue = job["queue"]
    ytdlp = job["ytdlp"]
    urls = job["urls"]
    langs = job["langs"]
    do_video = job["download_video"]
    transcript_dir = Path(job["transcript_dir"])
    video_dir = Path(job["video_dir"])
    max_playlist = job["max_playlist"]

    all_videos = []

    for url in urls:
        if is_playlist_url(url):
            q.put({"type": "status", "message": f"Expanding playlist..."})
            try:
                expanded = expand_playlist(url, max_playlist, ytdlp)
                q.put({"type": "status", "message": f"Found {len(expanded)} videos in playlist"})
                all_videos.extend(expanded)
            except Exception as e:
                q.put({"type": "error", "message": f"Playlist error: {e}"})
        else:
            all_videos.append({"url": url, "title": ""})

    total = len(all_videos)
    q.put({"type": "total", "count": total})
    completed = 0
    failed = 0

    for idx, video in enumerate(all_videos):
        url = video["url"]
        title = video.get("title", "")

        q.put({"type": "progress", "index": idx, "total": total,
               "status": "metadata", "url": url, "title": title or "..."})

        if not title:
            meta = extract_metadata(url, ytdlp)
            if meta:
                title = meta.get("title", "Unknown")
                video["title"] = title
            q.put({"type": "progress", "index": idx, "total": total,
                   "status": "metadata_done", "url": url, "title": title})

        safe_name = sanitize_name(title) if title else None

        if do_video:
            q.put({"type": "progress", "index": idx, "total": total,
                   "status": "downloading", "url": url, "title": title})
            vid_path = download_video(url, video_dir, ytdlp, safe_name)
            if vid_path:
                q.put({"type": "progress", "index": idx, "total": total,
                       "status": "downloaded", "url": url, "title": title,
                       "path": str(vid_path)})
            else:
                q.put({"type": "progress", "index": idx, "total": total,
                       "status": "download_failed", "url": url, "title": title})

        q.put({"type": "progress", "index": idx, "total": total,
               "status": "transcribing", "url": url, "title": title})
        transcript_path = extract_transcript(url, transcript_dir, ytdlp, langs, safe_name)

        if transcript_path:
            completed += 1
            q.put({"type": "progress", "index": idx, "total": total,
                   "status": "done", "url": url, "title": title,
                   "transcript": str(transcript_path)})
        else:
            failed += 1
            q.put({"type": "progress", "index": idx, "total": total,
                   "status": "failed", "url": url, "title": title})

    q.put({"type": "complete", "completed": completed, "failed": failed, "total": total,
           "transcript_dir": str(transcript_dir), "video_dir": str(video_dir)})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return INDEX_HTML


@app.route("/api/check", methods=["GET"])
def check_setup():
    issues = []
    ytdlp = find_ytdlp()
    if not ytdlp:
        issues.append("yt-dlp not found. Install: brew install yt-dlp")
    return jsonify({
        "ok": len(issues) == 0,
        "ytdlp": ytdlp,
        "python": sys.executable,
        "issues": issues,
    })


@app.route("/api/start", methods=["POST"])
def start_job():
    data = request.json
    urls_raw = data.get("urls", "").strip()
    if not urls_raw:
        return jsonify({"error": "No URLs provided"}), 400

    urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
    invalid = [u for u in urls if not is_youtube_url(u)]
    if invalid:
        return jsonify({"error": f"Invalid URLs: {', '.join(invalid[:3])}"}), 400

    ytdlp = find_ytdlp()
    if not ytdlp:
        return jsonify({"error": "yt-dlp not found"}), 500

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "id": job_id,
        "queue": queue.Queue(),
        "ytdlp": ytdlp,
        "urls": urls,
        "langs": data.get("langs", ["en"]),
        "download_video": data.get("download_video", False),
        "transcript_dir": data.get("transcript_dir", str(DEFAULT_TRANSCRIPT_DIR)),
        "video_dir": data.get("video_dir", str(DEFAULT_VIDEO_DIR)),
        "max_playlist": data.get("max_playlist", 50),
        "started": time.time(),
    }

    thread = threading.Thread(target=process_job, args=(job_id,), daemon=True)
    thread.start()
    return jsonify({"job_id": job_id})


@app.route("/api/progress/<job_id>")
def progress(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Unknown job"}), 404

    def generate():
        q = jobs[job_id]["queue"]
        while True:
            try:
                msg = q.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") == "complete":
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/open-folder", methods=["POST"])
def open_folder():
    folder = request.json.get("path", "")
    if folder and Path(folder).is_dir():
        subprocess.Popen(["open", folder])
        return jsonify({"ok": True})
    return jsonify({"error": "Folder not found"}), 404


# ---------------------------------------------------------------------------
# Inline HTML — uses textContent and safe DOM APIs, no innerHTML with user data
# ---------------------------------------------------------------------------

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>YT Transcript</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f7; color: #1d1d1f; line-height: 1.5;
    display: flex; justify-content: center; padding: 40px 20px;
    min-height: 100vh;
  }
  .container { max-width: 640px; width: 100%; }
  h1 { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
  .subtitle { color: #86868b; font-size: 14px; margin-bottom: 24px; }
  .card {
    background: #fff; border-radius: 12px; padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 16px;
  }
  label { display: block; font-size: 13px; font-weight: 500; color: #6e6e73; margin-bottom: 6px; }
  textarea {
    width: 100%; min-height: 120px; border: 1px solid #d2d2d7; border-radius: 8px;
    padding: 12px; font-size: 14px; font-family: inherit; resize: vertical;
    outline: none; transition: border-color 0.2s;
  }
  textarea:focus { border-color: #0071e3; }
  textarea::placeholder { color: #aeaeb2; }
  .options { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
  .option-group label { margin-bottom: 4px; }
  select, input[type="text"], input[type="number"] {
    width: 100%; padding: 8px 10px; border: 1px solid #d2d2d7; border-radius: 8px;
    font-size: 14px; font-family: inherit; outline: none; background: #fff;
  }
  select:focus, input:focus { border-color: #0071e3; }
  .checkbox-row {
    display: flex; align-items: center; gap: 8px; margin-top: 12px;
    font-size: 14px; cursor: pointer;
  }
  .checkbox-row input[type="checkbox"] { width: 18px; height: 18px; accent-color: #0071e3; cursor: pointer; }
  .btn {
    display: inline-flex; align-items: center; justify-content: center;
    padding: 12px 24px; border: none; border-radius: 10px; font-size: 15px;
    font-weight: 500; cursor: pointer; transition: all 0.2s; width: 100%; margin-top: 16px;
  }
  .btn-primary { background: #0071e3; color: #fff; }
  .btn-primary:hover { background: #0077ed; }
  .btn-primary:disabled { background: #d2d2d7; cursor: not-allowed; }
  .btn-secondary { background: #e8e8ed; color: #1d1d1f; margin-top: 12px; }
  .btn-secondary:hover { background: #dcdce1; }
  .hidden { display: none !important; }
  .progress-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .progress-count { font-size: 13px; color: #86868b; }
  .progress-bar-track { height: 4px; background: #e8e8ed; border-radius: 2px; overflow: hidden; margin-bottom: 16px; }
  .progress-bar-fill { height: 100%; background: #0071e3; border-radius: 2px; transition: width 0.3s ease; width: 0%; }
  .video-item { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f0f0f2; font-size: 14px; }
  .video-item:last-child { border-bottom: none; }
  .video-status {
    width: 24px; height: 24px; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0;
  }
  .status-waiting { background: #e8e8ed; color: #86868b; }
  .status-working { background: #fff3cd; color: #856404; animation: pulse 1.5s infinite; }
  .status-done { background: #d4edda; color: #155724; }
  .status-failed { background: #f8d7da; color: #721c24; }
  .video-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
  .setup-ok { color: #34c759; font-size: 13px; padding: 4px 0; }
  .setup-err { color: #ff3b30; font-size: 13px; padding: 4px 0; }
  .summary-stat {
    display: inline-block; padding: 6px 14px; border-radius: 8px;
    font-size: 14px; font-weight: 500; margin-right: 8px; margin-bottom: 8px;
  }
  .stat-ok { background: #d4edda; color: #155724; }
  .stat-fail { background: #f8d7da; color: #721c24; }
  .folder-path { font-size: 13px; color: #86868b; margin-top: 8px; word-break: break-all; }
  .folder-btn { display: inline-block; padding: 8px 16px; width: auto; margin-top: 8px; }
</style>
</head>
<body>
<div class="container">

  <div id="screen-setup">
    <h1>YT Transcript</h1>
    <p class="subtitle">Download transcripts (and videos) from YouTube</p>
    <div class="card">
      <label id="setup-label">Checking requirements...</label>
      <div id="setup-results"></div>
    </div>
  </div>

  <div id="screen-main" class="hidden">
    <h1>YT Transcript</h1>
    <p class="subtitle">Paste YouTube URLs or playlist links, one per line</p>
    <div class="card">
      <label for="urls">YouTube URLs</label>
      <textarea id="urls" placeholder="https://www.youtube.com/watch?v=...&#10;https://www.youtube.com/playlist?list=...&#10;https://youtu.be/..."></textarea>
      <div class="options">
        <div class="option-group">
          <label for="lang">Language priority</label>
          <select id="lang">
            <option value="en">English</option>
            <option value="ru">Russian</option>
            <option value="pl">Polish</option>
            <option value="de">German</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="pt">Portuguese</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="zh">Chinese</option>
          </select>
        </div>
        <div class="option-group">
          <label for="max-playlist">Max per playlist</label>
          <input type="number" id="max-playlist" value="50" min="1" max="500">
        </div>
      </div>
      <label class="checkbox-row"><input type="checkbox" id="download-video"> Also download video files</label>
      <div class="options" style="margin-top:12px;">
        <div class="option-group">
          <label for="transcript-dir">Transcript folder</label>
          <input type="text" id="transcript-dir" placeholder="~/Downloads/yt-transcripts">
        </div>
        <div class="option-group">
          <label for="video-dir">Video folder</label>
          <input type="text" id="video-dir" placeholder="~/Downloads/yt-videos">
        </div>
      </div>
      <button class="btn btn-primary" id="btn-start">Start</button>
    </div>
  </div>

  <div id="screen-progress" class="hidden">
    <h1>Processing...</h1>
    <p class="subtitle" id="progress-subtitle">Starting...</p>
    <div class="card">
      <div class="progress-header">
        <span id="progress-label">Preparing...</span>
        <span class="progress-count" id="progress-count">0 / 0</span>
      </div>
      <div class="progress-bar-track"><div class="progress-bar-fill" id="progress-bar"></div></div>
      <div id="video-list"></div>
    </div>
  </div>

  <div id="screen-done" class="hidden">
    <h1>Done!</h1>
    <p class="subtitle" id="done-subtitle"></p>
    <div class="card">
      <div id="done-stats"></div>
      <div id="done-folders"></div>
      <button class="btn btn-secondary" id="btn-reset">Process more videos</button>
    </div>
  </div>

</div>

<script>
const $ = id => document.getElementById(id);
let currentJobId = null;

function showScreen(name) {
  ['setup','main','progress','done'].forEach(s => {
    $('screen-'+s).classList.toggle('hidden', s !== name);
  });
}

function createEl(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text) el.textContent = text;
  return el;
}

async function checkSetup() {
  try {
    const res = await fetch('/api/check');
    const data = await res.json();
    const container = $('setup-results');
    container.replaceChildren();
    if (data.ok) {
      const ok1 = createEl('div', 'setup-ok', '\u2713 yt-dlp: ' + data.ytdlp);
      const ok2 = createEl('div', 'setup-ok', '\u2713 Python: ' + data.python);
      container.append(ok1, ok2);
      setTimeout(() => showScreen('main'), 800);
    } else {
      $('setup-label').textContent = 'Setup issues:';
      data.issues.forEach(i => {
        container.appendChild(createEl('div', 'setup-err', '\u2717 ' + i));
      });
    }
  } catch(e) {
    $('setup-results').appendChild(createEl('div', 'setup-err', 'Cannot connect to server'));
  }
}

$('btn-start').addEventListener('click', startJob);
$('btn-reset').addEventListener('click', () => { $('btn-start').disabled = false; showScreen('main'); });

async function startJob() {
  const urls = $('urls').value.trim();
  if (!urls) { alert('Paste at least one YouTube URL'); return; }
  $('btn-start').disabled = true;

  const body = {
    urls: urls,
    langs: [$('lang').value, 'en'].filter((v,i,a) => a.indexOf(v) === i),
    download_video: $('download-video').checked,
    transcript_dir: $('transcript-dir').value || undefined,
    video_dir: $('video-dir').value || undefined,
    max_playlist: parseInt($('max-playlist').value) || 50,
  };

  try {
    const res = await fetch('/api/start', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (data.error) { alert(data.error); $('btn-start').disabled = false; return; }

    currentJobId = data.job_id;
    $('video-list').replaceChildren();
    showScreen('progress');
    listenProgress(data.job_id);
  } catch(e) {
    alert('Failed to start: ' + e.message);
    $('btn-start').disabled = false;
  }
}

function listenProgress(jobId) {
  const source = new EventSource('/api/progress/' + jobId);
  const videoEls = {};
  let total = 0, doneCount = 0;

  source.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    if (msg.type === 'total') {
      total = msg.count;
      $('progress-count').textContent = '0 / ' + total;
      $('progress-subtitle').textContent = total + ' video' + (total !== 1 ? 's' : '') + ' to process';
    }

    if (msg.type === 'status') {
      $('progress-label').textContent = msg.message;
    }

    if (msg.type === 'progress') {
      const key = msg.index;
      const title = msg.title || msg.url;
      let statusClass = 'status-waiting', icon = '\u2026';

      if (['metadata', 'downloading', 'transcribing'].includes(msg.status)) {
        statusClass = 'status-working'; icon = '\u25CF';
        const labels = { downloading: 'Downloading video...', transcribing: 'Extracting transcript...', metadata: 'Getting info...' };
        $('progress-label').textContent = labels[msg.status] || msg.status;
      } else if (msg.status === 'done') {
        statusClass = 'status-done'; icon = '\u2713';
        doneCount++;
        $('progress-count').textContent = doneCount + ' / ' + total;
        $('progress-bar').style.width = (doneCount / total * 100) + '%';
      } else if (msg.status === 'failed') {
        statusClass = 'status-failed'; icon = '\u2717';
        doneCount++;
        $('progress-count').textContent = doneCount + ' / ' + total;
        $('progress-bar').style.width = (doneCount / total * 100) + '%';
      }

      if (!videoEls[key]) {
        const item = createEl('div', 'video-item');
        const badge = createEl('div', 'video-status ' + statusClass, icon);
        const name = createEl('div', 'video-title', title);
        item.id = 'video-' + key;
        item.append(badge, name);
        $('video-list').appendChild(item);
        videoEls[key] = item;
      } else {
        const el = videoEls[key];
        const badge = el.querySelector('.video-status');
        badge.className = 'video-status ' + statusClass;
        badge.textContent = icon;
        el.querySelector('.video-title').textContent = title;
      }
    }

    if (msg.type === 'error') {
      $('progress-label').textContent = msg.message;
    }

    if (msg.type === 'complete') {
      source.close();
      showDone(msg);
    }
  };

  source.onerror = () => {
    source.close();
    $('progress-label').textContent = 'Connection lost. Check terminal.';
  };
}

function showDone(msg) {
  showScreen('done');
  $('done-subtitle').textContent = msg.completed + ' of ' + msg.total + ' processed successfully';

  const statsEl = $('done-stats');
  statsEl.replaceChildren();
  if (msg.completed > 0) {
    statsEl.appendChild(createEl('span', 'summary-stat stat-ok', msg.completed + ' completed'));
  }
  if (msg.failed > 0) {
    statsEl.appendChild(createEl('span', 'summary-stat stat-fail', msg.failed + ' failed'));
  }

  const foldersEl = $('done-folders');
  foldersEl.replaceChildren();

  const tPath = createEl('div', 'folder-path', 'Transcripts: ' + msg.transcript_dir);
  const tBtn = createEl('button', 'btn btn-secondary folder-btn', 'Open transcripts folder');
  tBtn.addEventListener('click', () => openFolder(msg.transcript_dir));
  foldersEl.append(tPath, tBtn);

  if (msg.video_dir) {
    const vPath = createEl('div', 'folder-path', 'Videos: ' + msg.video_dir);
    vPath.style.marginTop = '12px';
    const vBtn = createEl('button', 'btn btn-secondary folder-btn', 'Open videos folder');
    vBtn.addEventListener('click', () => openFolder(msg.video_dir));
    foldersEl.append(vPath, vBtn);
  }
}

async function openFolder(path) {
  await fetch('/api/open-folder', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path})
  });
}

checkSetup();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import webbrowser
    port = int(os.environ.get("PORT", 5555))
    print(f"\n  YT Transcript \u2014 http://localhost:{port}\n")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
