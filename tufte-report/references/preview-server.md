# Preview Server

Zero-dependency Python script for live-reloading Tufte reports during development.

## Usage

```bash
python3 ~/.claude/skills/tufte-report/scripts/serve.py report.html
# → Serving report.html on http://localhost:8042
# → Watching for changes...
```

Opens automatically in default browser. Reloads when the HTML file changes.

## How It Works

1. Injects a tiny WebSocket client `<script>` before `</body>` in the served HTML
2. Watches the file's mtime every 500ms
3. Sends `reload` message over WebSocket when the file changes
4. Browser refreshes without full page navigation (preserves scroll position by default)

## The Script

Claude should create this script at `~/.claude/skills/tufte-report/scripts/serve.py` if it doesn't exist:

```python
#!/usr/bin/env python3
"""Zero-dependency live-reload server for Tufte reports."""
import http.server, hashlib, json, os, sys, threading, time, struct, webbrowser
from pathlib import Path

PORT = int(os.environ.get("TUFTE_PORT", 8042))
WS_PORT = PORT + 1

INJECT = f'''<script>
(function(){{
  var ws = new WebSocket("ws://localhost:{WS_PORT}");
  ws.onmessage = function(e) {{
    if (e.data === "reload") {{
      var y = window.scrollY;
      sessionStorage.setItem("_tufte_scroll", y);
      location.reload();
    }}
  }};
  ws.onclose = function() {{ setTimeout(function(){{ location.reload(); }}, 2000); }};
  window.addEventListener("load", function() {{
    var y = sessionStorage.getItem("_tufte_scroll");
    if (y) {{ window.scrollTo(0, parseInt(y)); sessionStorage.removeItem("_tufte_scroll"); }}
  }});
}})();
</script>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, html_path=None, **kw):
        self._html = html_path
        super().__init__(*a, **kw)

    def do_GET(self):
        if self.path in ("/", f"/{self._html.name}"):
            content = self._html.read_text()
            content = content.replace("</body>", INJECT + "</body>")
            data = content.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(data))
            self.end_headers()
            self.wfile.write(data)
        else:
            super().do_GET()

    def log_message(self, fmt, *args): pass

def ws_server(html_path):
    """Minimal WebSocket server — just enough for reload signals."""
    import socket, hashlib, base64
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("localhost", WS_PORT))
    srv.listen(1)
    clients = []

    def accept_loop():
        while True:
            conn, _ = srv.accept()
            data = conn.recv(4096).decode()
            key = ""
            for line in data.split("\r\n"):
                if line.startswith("Sec-WebSocket-Key:"):
                    key = line.split(": ", 1)[1].strip()
            accept = base64.b64encode(
                hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-5AB5DC11650A").encode()).digest()
            ).decode()
            conn.send(
                f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode()
            )
            clients.append(conn)

    threading.Thread(target=accept_loop, daemon=True).start()

    last_hash = hashlib.md5(html_path.read_bytes()).hexdigest()
    while True:
        time.sleep(0.5)
        try:
            cur = hashlib.md5(html_path.read_bytes()).hexdigest()
        except FileNotFoundError:
            continue
        if cur != last_hash:
            last_hash = cur
            frame = b"\x81" + bytes([len(b"reload")]) + b"reload"
            dead = []
            for c in clients:
                try:
                    c.send(frame)
                except Exception:
                    dead.append(c)
            for c in dead:
                clients.remove(c)
            print(f"  ↻ reloaded ({time.strftime('%H:%M:%S')})")

def main():
    if len(sys.argv) < 2:
        print("Usage: serve.py <report.html>")
        sys.exit(1)
    html_path = Path(sys.argv[1]).resolve()
    if not html_path.exists():
        print(f"File not found: {html_path}")
        sys.exit(1)

    os.chdir(html_path.parent)

    handler = lambda *a, **kw: Handler(*a, html_path=html_path, **kw)
    server = http.server.HTTPServer(("localhost", PORT), handler)

    threading.Thread(target=ws_server, args=(html_path,), daemon=True).start()

    url = f"http://localhost:{PORT}/"
    print(f"  Serving {html_path.name} on {url}")
    print(f"  Watching for changes... (Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")

if __name__ == "__main__":
    main()
```

## Integration with Skill

After generating a report, Claude should offer:

> "Want me to start the preview server? I'll watch for changes and auto-reload."

Then run:
```bash
python3 ~/.claude/skills/tufte-report/scripts/serve.py /path/to/report.html
```

Keep it running in the background. Each time Claude updates the HTML file, the browser reloads automatically with scroll position preserved.
