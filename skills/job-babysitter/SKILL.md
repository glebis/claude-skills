---
name: job-babysitter
description: This skill should be used to watch a long-running background job (ffmpeg/media encode, qmd or other embedding/vector-DB run, batch agent/LLM pipeline, or a real-browser/agent-browser daemon) until it finishes or wedges, then deliver a verdict (done, needs-attention, or blocked) plus the exact next command, without burning dozens of manual poll commands. Triggers on "babysit this job", "watch this until it's done", "ping me when the encode/embed/batch finishes", "is this background process stuck", "monitor this ffmpeg/qmd run", or any request to wait on a long-running process and be told when it's complete or hung.
---

# Job Babysitter

## Purpose

Stop manually polling long-running background jobs. Instead of dozens-to-hundreds of
`ls -lh` / `ps` checks while guessing at completion, start one background watcher that
detects the terminal state via plateau heuristics, then routes a verdict — done,
needs-attention, or blocked — with the exact next command.

A night-shift nurse for background jobs: it checks vitals on a schedule and escalates
only when something is actually wrong.

## When to use

Use when a job will run long enough that babysitting it by hand wastes attention:
- Media encodes / transcodes (ffmpeg, video-transcribe, audio extraction)
- Embedding or vector-DB builds (qmd embed, index builds)
- Batch agent / LLM pipelines run in the background
- Browser / scrape daemons (real-browser, agent-browser) prone to hanging

Do NOT use for jobs that finish in seconds, or where a single `Bash` call already
returns the result.

## Core principle: stay thin, lean on the harness

This skill orchestrates Claude Code's own primitives — do not reimplement them:
- Start the watcher with **`run_in_background: true`**. When it exits, the harness
  re-invokes the agent automatically — no manual polling loop needed.
- The watcher (`scripts/watch_job.py`) owns the deterministic part: poll with backoff,
  detect plateau, distinguish done from stuck, emit a verdict JSON.
- The skill's value is the **per-job-type heuristics**, the **safe-recovery playbook**,
  and **notification routing** — all in `references/playbook.md`.

## Workflow

### 1. Identify the job's signals
Determine what can be watched, in order of reliability:
- **PID** — the process ID (most reliable completion signal). Get it from the job's
  launch, `pgrep`, or `ps`.
- **Output file** — a file that grows as the job progresses (e.g. ffmpeg target).
- **Log file** — a log that gets appended (e.g. an embed progress log).

Read `references/playbook.md` § "Completion heuristics by job type" to pick flags for
the specific job type (ffmpeg, embed, batch, browser).

### 2. Launch the watcher in the background
Run with `run_in_background: true`. Always pass `--pid` when known; add file/log
signals as corroboration. Write the verdict to a known path.

```bash
scripts/watch_job.py \
  --label "lab05 stream encode" \
  --pid <PID> \
  --output-file /path/to/output.mp4 \
  --plateau-bytes 65536 --plateau-polls 5 --stuck-after 120 \
  --max-wait 7200 \
  --verdict-out /tmp/job-babysitter-<label>.json
```

The watcher prints a one-line JSON heartbeat per poll (tail it for live progress) and
writes the final verdict JSON to `--verdict-out` on exit.

Tuning lives in the playbook; sensible defaults: `--interval 10` (backs off to 60),
`--plateau-polls 4`, `--stuck-after 300`, `--max-wait 7200`.

### 3. On watcher exit, read the verdict and route it
The harness re-invokes the agent when the background watcher finishes. Read the
verdict JSON. It has `status` ∈ {done, needs-attention, blocked}, a `reason`,
`suggested_next`, elapsed time, and final size.

- **done** → verify the output is real (see the job-type "Done check" in the playbook,
  e.g. `ffprobe` for media, count match for embeds), then proceed with the original task.
- **needs-attention** → the job plateaued while still alive (possibly wedged). Follow
  the recovery playbook: diagnose read-only FIRST. **Never kill or run destructive
  recovery (pkill, WAL checkpoint, VACUUM) without asking the user.**
- **blocked** → the watcher gave up after `--max-wait`. Report honestly: "gave up
  waiting" ≠ "failed". Offer to re-check or extend the ceiling.

### 4. Notify per the chosen channel
Default to in-session resume. If the user picked a channel (Telegram, voice/TTS,
desktop notification), route per `references/playbook.md` § "Notification routing".
Always include the status emoji, label, elapsed time, and the exact next command.

## Guardrails (non-negotiable)

- **Never act on a single slow poll.** "Stuck" requires plateau AND elapsed past
  `--stuck-after` — the watcher already enforces this before returning needs-attention.
- **Ask before any destructive recovery** — `pkill`, `kill`, WAL checkpoint, `VACUUM`,
  daemon restart. Diagnose read-only first.
- **Report honestly.** Distinguish done from "gave up waiting" from "wedged". Never
  imply a success the watcher did not observe.
- **Poll with backoff, not tight loops** — the watcher handles this; never wrap it in
  a manual fast-polling loop.

## Resources

- `scripts/watch_job.py` — background watcher: plateau detection, stuck-vs-done logic,
  verdict JSON. Stdlib only, Python 3.11+.
- `references/playbook.md` — per-job-type completion heuristics, the safe-recovery
  table, and notification routing. Load when picking watcher flags or handling a
  needs-attention/blocked verdict.
