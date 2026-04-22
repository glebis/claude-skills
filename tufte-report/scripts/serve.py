#!/usr/bin/env python3
"""Zero-dependency live-reload server for Tufte reports."""
import http.server, hashlib, os, sys, threading, time, webbrowser, socket, base64
from pathlib import Path

PORT = int(os.environ.get("TUFTE_PORT", 8042))
WS_PORT = PORT + 1

INJECT = f'''<script>
(function(){{
  var ws=new WebSocket("ws://localhost:{WS_PORT}");
  ws.onmessage=function(e){{if(e.data==="reload"){{var y=window.scrollY;sessionStorage.setItem("_ts",y);location.reload()}}}};
  ws.onclose=function(){{setTimeout(function(){{location.reload()}},2000)}};
  window.addEventListener("load",function(){{var y=sessionStorage.getItem("_ts");if(y){{window.scrollTo(0,parseInt(y));sessionStorage.removeItem("_ts")}}}});
}})();
</script>'''

_html_path = None

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", f"/{_html_path.name}"):
            content = _html_path.read_text()
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

def ws_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("localhost", WS_PORT))
    srv.listen(5)
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
            conn.send(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode())
            clients.append(conn)
    threading.Thread(target=accept_loop, daemon=True).start()
    last = hashlib.md5(_html_path.read_bytes()).hexdigest()
    while True:
        time.sleep(0.5)
        try:
            cur = hashlib.md5(_html_path.read_bytes()).hexdigest()
        except FileNotFoundError:
            continue
        if cur != last:
            last = cur
            frame = b"\x81" + bytes([len(b"reload")]) + b"reload"
            dead = []
            for c in clients:
                try: c.send(frame)
                except Exception: dead.append(c)
            for c in dead: clients.remove(c)
            print(f"  ↻ reloaded ({time.strftime('%H:%M:%S')})")

def main():
    global _html_path
    if len(sys.argv) < 2:
        print("Usage: serve.py <report.html>"); sys.exit(1)
    _html_path = Path(sys.argv[1]).resolve()
    if not _html_path.exists():
        print(f"Not found: {_html_path}"); sys.exit(1)
    os.chdir(_html_path.parent)
    threading.Thread(target=ws_server, daemon=True).start()
    server = http.server.HTTPServer(("localhost", PORT), Handler)
    url = f"http://localhost:{PORT}/"
    print(f"  Serving {_html_path.name} on {url}")
    print(f"  Watching for changes... (Ctrl+C to stop)")
    webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n  Stopped.")

if __name__ == "__main__":
    main()
