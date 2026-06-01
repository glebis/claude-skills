# Job-type heuristics, recovery playbook, and notification routing

Reference loaded on demand by the job-babysitter skill. Three sections:
completion heuristics per job type, the safe-recovery playbook, and notification routing.

---

## 1. Completion heuristics by job type

Pick `watch_job.py` flags from the job type. The watcher always prefers a **PID
exit** signal when one is available — pass `--pid` whenever the job's process ID
is known. Add file/log signals as corroboration.

### Media encodes (ffmpeg, video-transcribe, audio extraction)
- **Best signal:** output file size plateau. The target file grows steadily, then
  stalls during muxing/finalization, then the process exits.
- **Flags:** `--output-file <target> --pid <ffmpeg_pid> --plateau-bytes 65536 --plateau-polls 5`
- **Gotcha:** ffmpeg can plateau for several seconds while writing the moov atom at
  the end. Keep `--stuck-after` ≥ 120s so finalization isn't mistaken for a wedge.
- **Done check after verdict:** `ffprobe <file>` returns a valid duration; file is
  non-zero and larger than a trivial header.

### Embeddings / vector DB (qmd embed, vector index builds)
- **Best signal:** progress counter in the log ("12,033 done") plus PID exit.
- **Flags:** `--log-file <embed.log> --pid <pid> --stuck-after 240`
- **Gotchas (seen in real sessions):**
  - GPU contention: a foreground vector search competes with the background embed
    for the GPU and both crawl. Symptom: long plateau while pid alive.
  - WAL bloat / `SQLITE_FULL`: the write-ahead log grows huge and blocks writes.
- **Done check:** the embed count equals the source count; no `.wal` larger than the DB.

### Batch agent / LLM jobs (background agents, batch API, multi-step pipelines)
- **Best signal:** PID exit, or a terminal marker line in the output/log
  (e.g. a results JSON appears, or a "DONE"/"completed" line).
- **Flags:** `--pid <pid> --log-file <run.log> --max-wait 14400`
- **Gotcha:** batch jobs legitimately idle (waiting on a remote queue). Prefer PID
  exit or an explicit completion marker over plateau; raise `--stuck-after` high.

### Browser / scrape daemons (real-browser, agent-browser)
- **Best signal:** a state/output file the daemon writes, plus liveness of the daemon.
- **Flags:** `--output-file <state.json> --stuck-after 90`
- **Gotchas (seen in real sessions):** daemon stuck with `EAGAIN`; a tab reverts to a
  "guest"/logged-out state; the page hangs and needs a direct re-navigation.

---

## 2. Recovery playbook — SAFE BY DEFAULT

The guardrail is absolute: **never kill, restart, or mutate a job without confidence
it is truly stuck, and never run a destructive recovery without asking the user first.**
A single slow poll is not "stuck" — require plateau **and** elapsed-past-`--stuck-after`,
which the watcher already enforces before it returns `needs-attention`.

When the verdict is `needs-attention` or `blocked`, diagnose before acting:

| Symptom | Diagnose (read-only) | Recovery (ASK FIRST — destructive) |
|---|---|---|
| ffmpeg plateau, pid alive | `ffprobe` partial file; check `tail` of stderr | Usually just wait longer. Only `kill` if confirmed hung. |
| Embed stalled, GPU busy | `nvidia-smi` / `ps` for a competing search proc | Pause/kill the *competing* search, not the embed. |
| `SQLITE_FULL` / WAL bloat | `ls -lh *.wal`; check disk free | WAL checkpoint / `VACUUM` — **ask first**, these mutate the DB. |
| agent-browser `EAGAIN`/hung | snapshot the daemon state file; check the port | Restart the daemon; try direct navigation. |
| Browser tab "guest" | snapshot the page | Re-auth the tab (user action) before resuming. |
| Generic process hung | `ps`, `lsof`, `tail` the log | `kill` only after confirming, and **ask first** before `pkill`. |

Always report honestly in the final message: distinguish **"done"** from
**"gave up waiting"** (`blocked`) from **"wedged"** (`needs-attention`). Never imply
success the watcher did not actually observe.

---

## 3. Notification routing

The verdict carries `status` ∈ {done, needs-attention, blocked}. Route per the user's
chosen channel (configurable; default to in-session resume if unspecified). Always
include the status emoji, the label, elapsed time, and the **exact next command**.

- **Telegram** — invoke the `telegram` skill / plugin to send a message to the user's
  saved chat. Use for jobs the user walked away from. Message shape:
  `✅ <label> done in <elapsed> — <suggested_next>`
- **Voice / TTS** — `elevenlabs-tts` then `afplay` (per user's global preference:
  read-aloud needs no confirmation). Keep it one short spoken sentence; refer to files
  loosely ("the encode finished"), never full paths.
- **In-session resume** — no external ping; the watcher's exit re-invokes the agent.
  Print the digest and continue the original work automatically.
- **macOS desktop + digest** — `osascript -e 'display notification "…" with title "…"'`
  plus a written digest block in the session.

### Verdict → message mapping
- `done` → `✅` + confirm output verified + proceed.
- `needs-attention` → `⚠️` + what's wedged + the read-only diagnosis to run next.
  Never auto-run destructive recovery.
- `blocked` → `❌` + "gave up waiting after <max-wait>" + how to re-check or extend.
