"""Serve generated previews over HTTP so they get a real origin.

`file://` URLs are treated as unique security origins by browsers, which breaks
cross-origin font loads, `fetch`, and many extensions (you get "Unsafe attempt to
load URL ... 'file:' URLs are treated as unique security origins"). Serving the
output directory over `http://127.0.0.1` gives every preview a normal origin.

Stdlib only — no dependency added.
"""

import contextlib
import functools
import http.server
import pathlib
import socket
import socketserver
import threading
import webbrowser


def find_free_port(start=8787, host="127.0.0.1"):
    """Return the first bindable TCP port at or after `start`."""
    port = start
    for _ in range(500):
        with contextlib.closing(socket.socket()) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                port += 1
    return start


def url_for(directory, open_path, port, host="127.0.0.1"):
    """Build the http URL for `open_path` (a file) under served `directory`."""
    base = f"http://{host}:{port}/"
    if not open_path:
        return base.rstrip("/")
    directory = pathlib.Path(directory).resolve()
    rel = pathlib.Path(open_path).resolve().relative_to(directory)
    return base + str(rel).replace("\\", "/")


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the console clean
        pass


def serve(directory, open_path=None, port=None, host="127.0.0.1", open_browser=True, _block=True):
    """Serve `directory` over HTTP and (optionally) open `open_path` in a browser.

    Blocks serving until interrupted. With `_block=False` (used by tests), starts
    a daemon thread and returns `(httpd, url)` immediately.
    """
    directory = str(pathlib.Path(directory).resolve())
    port = port or find_free_port(host=host)
    handler = functools.partial(_QuietHandler, directory=directory)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer((host, port), handler)
    url = url_for(directory, open_path, port, host)
    print(f"serving {directory}\n  → {url}\n  (Ctrl-C to stop)")
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
