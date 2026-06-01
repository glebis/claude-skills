#!/usr/bin/env python3
"""Watch a long-running job until it reaches a terminal state, then emit a verdict.

Designed to be launched as a background process by the job-babysitter skill. The
agent does NOT poll inside its own loop — it starts this watcher in the background
and is re-invoked when the watcher exits. The watcher writes a single verdict JSON
to --verdict-out on exit, and a live heartbeat line to stdout on every poll.

Completion is judged from the most reliable signal available, in priority order:

  1. process exit        (when --pid is given) — the gold standard for "done"
  2. output-file plateau (when --output-file is given) — growth stalls for
                          --plateau-polls consecutive polls
  3. log-file idle       (when --log-file is given) — no new bytes appended

"Stuck" is deliberately distinguished from "done": a plateau while the process is
STILL ALIVE past --stuck-after seconds is reported as needs-attention, NOT done,
and NEVER triggers a kill. Recovery is left to the agent + human (see SKILL.md
guardrails).

Stdlib only. Python 3.11+.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time


def pid_alive(pid: int) -> bool:
    """Return True if the process is still running (signal 0 probe)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Exists but owned by another user — still "alive" for our purposes.
        return True
    return True


def file_size(path: str) -> int | None:
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def human_bytes(n: int | None) -> str:
    if n is None:
        return "n/a"
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    for u in units:
        if f < 1024 or u == units[-1]:
            return f"{f:.0f}{u}" if u == "B" else f"{f:.1f}{u}"
        f /= 1024
    return f"{n}B"


def emit_heartbeat(state: dict) -> None:
    """One compact line per poll, flushed — lets the agent tail progress live."""
    sys.stdout.write(json.dumps({"hb": state}) + "\n")
    sys.stdout.flush()


def write_verdict(path: str | None, verdict: dict) -> None:
    payload = json.dumps(verdict, indent=2)
    if path:
        # Atomic-ish write so a reader never sees a half-written file.
        tmp = f"{path}.tmp"
        with open(tmp, "w") as fh:
            fh.write(payload)
        os.replace(tmp, path)
    sys.stdout.write(payload + "\n")
    sys.stdout.flush()


def main() -> int:
    p = argparse.ArgumentParser(description="Watch a long-running job to a terminal state.")
    p.add_argument("--pid", type=int, help="Process ID to watch (most reliable completion signal).")
    p.add_argument("--output-file", help="Output file whose growth indicates progress (e.g. ffmpeg target).")
    p.add_argument("--log-file", help="Log file whose appends indicate progress.")
    p.add_argument("--label", default="job", help="Human label for this job, echoed in the verdict.")
    p.add_argument("--interval", type=float, default=10.0, help="Base poll interval seconds (default 10).")
    p.add_argument("--max-interval", type=float, default=60.0, help="Backoff cap seconds (default 60).")
    p.add_argument("--plateau-polls", type=int, default=4,
                   help="Consecutive no-growth polls that count as a plateau (default 4).")
    p.add_argument("--plateau-bytes", type=int, default=4096,
                   help="Growth below this many bytes across the window counts as no-growth (default 4096).")
    p.add_argument("--stuck-after", type=float, default=300.0,
                   help="Seconds of plateau-while-alive before reporting needs-attention (default 300).")
    p.add_argument("--max-wait", type=float, default=7200.0,
                   help="Hard ceiling in seconds before giving up (default 7200 = 2h).")
    p.add_argument("--verdict-out", help="Path to write the final verdict JSON.")
    args = p.parse_args()

    if not any([args.pid, args.output_file, args.log_file]):
        sys.stderr.write("error: provide at least one of --pid, --output-file, --log-file\n")
        return 2

    start = time.monotonic()
    sizes: list[int] = []        # rolling window of output-file sizes
    log_sizes: list[int] = []    # rolling window of log-file sizes
    last_progress_ts = start     # last time we saw real growth/activity
    interval = args.interval
    polls = 0

    def elapsed() -> float:
        return time.monotonic() - start

    def finish(status: str, reason: str, suggested_next: str) -> int:
        verdict = {
            "label": args.label,
            "status": status,                 # done | needs-attention | blocked
            "reason": reason,
            "suggested_next": suggested_next,
            "elapsed_seconds": round(elapsed(), 1),
            "polls": polls,
            "output_file": args.output_file,
            "final_size": human_bytes(file_size(args.output_file)) if args.output_file else None,
            "pid": args.pid,
        }
        write_verdict(args.verdict_out, verdict)
        return 0 if status == "done" else 1

    while True:
        polls += 1
        now_elapsed = elapsed()

        proc_gone = args.pid is not None and not pid_alive(args.pid)

        out_size = file_size(args.output_file) if args.output_file else None
        if out_size is not None:
            sizes.append(out_size)
            sizes = sizes[-(args.plateau_polls + 1):]

        log_size = file_size(args.log_file) if args.log_file else None
        if log_size is not None:
            log_sizes.append(log_size)
            log_sizes = log_sizes[-(args.plateau_polls + 1):]

        # Did anything grow since last poll? Reset the progress clock if so.
        grew = False
        if len(sizes) >= 2 and sizes[-1] - sizes[-2] >= args.plateau_bytes:
            grew = True
        if len(log_sizes) >= 2 and log_sizes[-1] - log_sizes[-2] >= 1:
            grew = True
        if grew:
            last_progress_ts = time.monotonic()

        plateau = False
        if len(sizes) > args.plateau_polls:
            window_growth = sizes[-1] - sizes[-(args.plateau_polls + 1)]
            plateau = window_growth < args.plateau_bytes
        elif args.output_file is None and len(log_sizes) > args.plateau_polls:
            window_growth = log_sizes[-1] - log_sizes[-(args.plateau_polls + 1)]
            plateau = window_growth < 1

        stalled_secs = time.monotonic() - last_progress_ts

        emit_heartbeat({
            "poll": polls,
            "elapsed_s": round(now_elapsed, 1),
            "size": human_bytes(out_size) if out_size is not None else None,
            "proc_alive": (not proc_gone) if args.pid else None,
            "plateau": plateau,
            "stalled_s": round(stalled_secs, 1),
        })

        # --- Terminal-state decisions, in priority order ---

        # 1. Process exited — the most reliable "done".
        if proc_gone:
            return finish(
                "done",
                f"process {args.pid} exited after {round(now_elapsed,1)}s",
                "Verify the output file is complete and non-empty, then proceed.",
            )

        # 2. No pid to watch, but the output/log plateaued — treat as done.
        if args.pid is None and plateau:
            return finish(
                "done",
                f"output plateaued ({args.plateau_polls} polls, <{args.plateau_bytes}B growth)",
                "No PID was watched — sanity-check the output before trusting completion.",
            )

        # 3. Plateau while the process is STILL ALIVE past the stuck threshold.
        #    Report, never kill. Recovery is the agent+human's call.
        if plateau and not proc_gone and stalled_secs >= args.stuck_after:
            return finish(
                "needs-attention",
                f"no progress for {round(stalled_secs)}s while pid {args.pid} still alive — possibly wedged",
                "Inspect the process (logs, GPU, locks). Do NOT kill blindly — see recovery playbook.",
            )

        # 4. Hard ceiling — give up waiting, but say so honestly.
        if now_elapsed >= args.max_wait:
            return finish(
                "blocked",
                f"max-wait {args.max_wait}s exceeded without a terminal state",
                "Gave up waiting (not the same as failed). Re-check the job manually or raise --max-wait.",
            )

        # Sleep with gentle backoff once we're past the first few polls.
        time.sleep(interval)
        if polls >= args.plateau_polls:
            interval = min(interval * 1.3, args.max_interval)

    # unreachable


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stderr.write("\nwatcher interrupted\n")
        sys.exit(130)
