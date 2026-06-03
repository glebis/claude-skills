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

## File upload — hidden `<input type=file>` (no native dialog)
`upload` takes a **CSS selector or @ref** and sets the file via CDP — it does NOT
open the OS file picker and works on HIDDEN inputs. Do NOT click the visible
"attach"/"+" button (that opens a native dialog you can't drive).
```bash
agent-browser --cdp $PORT --session $SID upload "input[type=file]" /abs/file.zip
```
Pick the right input when there are several: the general attachment input has
`accept="*"` (image-only ones have `accept="image/*"`). Verify after:
`eval 'document.body.innerText.includes("file.zip")'`.

## Text entry — textarea vs contenteditable
- Real `<input>`/`<textarea>`: `fill "<sel>" "text"`.
- **contenteditable / ProseMirror** (e.g. ChatGPT's `#prompt-textarea` is a
  `<div contenteditable>`, not a textarea — `.value` stays empty): `click` it then
  `type "text"`. `fill` silently does nothing on these. Detect first:
  `eval 'const e=document.querySelector(sel); e.tagName+"/"+e.getAttribute("contenteditable")'`.

## Recipe: drive ChatGPT (file + prompt + model) — works first try
1. `open "https://chatgpt.com/"`; confirm a composer (`#prompt-textarea`) exists (logged in).
2. **CHECK THE MODEL FIRST — before touching anything.** It is usually already what you
   want; don't open the switcher unless you must change it. Read the composer model pill
   (`+ ⏱ Pro ⌄`), NOT the switcher button (its `innerText` is just the brand "ChatGPT").
   - To change: `click "[data-testid=\"model-switcher-dropdown-button\"]"`; the menu is a
     PORTAL — read `[data-radix-popper-content-wrapper]` (e.g. "Latest 5.5", "Thinking",
     "Pro"), click the target, then verify.
3. `upload "input[type=file]" /abs/file` (the `accept="*"` input); verify filename in body.
4. `click "#prompt-textarea"` then `type "<prompt>"` (contenteditable — see above).
5. `click "[data-testid=\"send-button\"]"`. Generating == `[data-testid=\"stop-button\"]` present.
6. Wait until the stop-button disappears, then read the last
   `[data-message-author-role=\"assistant\"]` element's innerText.

## Reliability
- **Read state before acting.** Check the current value/model/login before changing it —
  it is often already correct, and clobbering a good state is the common failure mode.
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
