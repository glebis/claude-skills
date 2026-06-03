# Driving a browser-mate instance with `agent-browser`

`browser-mate` only launches/reuses the debug Chrome; interaction is via the
`agent-browser` CLI against the printed port. Pass `--cdp <port>` on EVERY call.

```bash
PORT=$(python3 scripts/browser.py chatgpt)   # ensure up, capture port
SID=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6)   # unique session id

agent-browser --cdp $PORT --session $SID snapshot -i        # interactive snapshot (refs)
agent-browser --cdp $PORT --session $SID open "https://chatgpt.com/"
agent-browser --cdp $PORT --session $SID click @e3
agent-browser --cdp $PORT --session $SID fill @e5 "text"
agent-browser --cdp $PORT --session $SID screenshot /tmp/page.png
agent-browser --cdp $PORT --session $SID eval 'navigator.webdriver'   # expect false/undefined
```

## File upload (hidden `<input type=file>`)
Find the file input ref in a snapshot, then:
```bash
agent-browser --cdp $PORT --session $SID upload @e7 /abs/path/file.zip
```
If the input is hidden, `upload` still targets it by ref. Some sites need the
visible "attach" button clicked first to mount the input.

## Reliability
- Bound long calls: macOS has no `timeout` — use `gtimeout` (coreutils) if present,
  else run the call in the background and `kill` after N seconds. On timeout,
  `snapshot` to capture last-known state, then retry that step (checkpoint, don't restart).
- Generate the 6-char `--session` once per run; two runs sharing a name collide.
- After upgrading agent-browser: `pkill -f agent-browser; rm -rf ~/.agent-browser/sockets/`
  then reconnect (stale daemons cause blank pages / missing cookies).
- Never use `agent-browser ... connect <port>` (its daemon opens a blank tab).
  `--cdp <port>` attaches correctly.

## Cleanup
- Leave the instance running (reused next time). To stop OUR instance only:
  `python3 scripts/browser.py stop chatgpt` (SIGTERM to the matched pid; never
  the user's browser).
