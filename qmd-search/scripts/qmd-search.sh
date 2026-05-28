#!/usr/bin/env bash
# qmd-search.sh — thin, agent-friendly wrapper around `qmd` (https://github.com/tobi/qmd)
#
# Why this exists:
#   - qmd writes its spinner + query-expansion trace to STDERR; this wrapper suppresses
#     it so captured output is clean.
#   - Running a search while `qmd embed` is active causes GPU/DB contention and returns
#     EMPTY results. This wrapper makes a best-effort check and refuses (override: --force).
#   - Normalizes result rows to "score  path" by parsing qmd's --json (comma-safe), or
#     passes through --json / --full unchanged. Real qmd failures are surfaced, not hidden.
#
# Usage:
#   qmd-search.sh [-m query|search|vsearch] [-n N] [-c COLLECTION] [--json] [--full] [--force] <query...>
#
# Modes:
#   query   (default) hybrid: query expansion + vector + BM25 + LLM rerank. Best quality.
#   search  BM25 full-text. Instant, no model. Use for exact keywords/filenames.
#   vsearch pure vector/semantic similarity. Fast concept lookup.
#
# Examples:
#   qmd-search.sh "how do I stop overengineering"
#   qmd-search.sh -m search -n 10 sensorium
#   qmd-search.sh -m vsearch --json "behavioral health from photos"
#   qmd-search.sh --full "what helps with anxiety"
set -euo pipefail

MODE="query"
N=5
COLLECTION=""
JSON=0
FULL=0
FORCE=0

die() { echo "qmd-search: $*" >&2; exit 1; }
need_val() { [[ $# -ge 2 ]] || die "flag $1 needs a value"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--mode)        need_val "$@"; MODE="$2"; shift 2;;
    -n|--num)         need_val "$@"; N="$2"; shift 2;;
    -c|--collection)  need_val "$@"; COLLECTION="$2"; shift 2;;
    --json)           JSON=1; shift;;
    --full)           FULL=1; shift;;
    --force)          FORCE=1; shift;;
    -h|--help)        sed -n '2,24p' "$0"; exit 0;;
    --)               shift; break;;
    -*)               die "unknown flag: $1";;
    *)                break;;
  esac
done

QUERY="$*"
[[ -n "$QUERY" ]] || die "no query given (run with -h for help)"
command -v qmd >/dev/null 2>&1 || die "qmd not on PATH — install with: bun install -g @tobilu/qmd"
case "$MODE" in query|search|vsearch) ;; *) die "mode must be query|search|vsearch (got: $MODE)";; esac
[[ "$N" =~ ^[1-9][0-9]*$ ]] || die "-n must be a positive integer (got: $N)"

# Best-effort guard against a concurrent embed (the #1 cause of empty results).
if [[ $FORCE -eq 0 ]] && pgrep -f "qmd[^ ]* embed" >/dev/null 2>&1; then
  die "a 'qmd embed' appears to be running — search would contend and likely return nothing. Wait, or pass --force."
fi

# Assemble base args.
args=("$MODE" "$QUERY" -n "$N")
[[ -n "$COLLECTION" ]] && args+=(-c "$COLLECTION")
[[ $FULL -eq 1 ]] && args+=(--full)

# NOTE on exit codes: hybrid `qmd query` may abort during model teardown (exit 134/SIGABRT)
# *after* writing complete, valid output. So success is judged by output validity, not $rc;
# a genuine failure produces no usable output and IS surfaced.
err="$(mktemp "${TMPDIR:-/tmp}/qmd-search.XXXXXX")"
trap 'rm -f "$err"' EXIT
set +e

# --json passthrough: emit verbatim if it parses as JSON.
if [[ $JSON -eq 1 ]]; then
  out="$(qmd "${args[@]}" --json 2>"$err")"; rc=$?
  if printf '%s' "$out" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{JSON.parse(s)}catch(e){process.exit(3)}process.stdout.write(s.endsWith("\n")?s:s+"\n")})'; then
    exit 0
  fi
  echo "qmd-search: qmd produced no valid JSON (exit $rc)" >&2; head -n 5 "$err" >&2 || true; exit $(( rc == 0 ? 1 : rc ))
fi

# --full passthrough: emit if non-empty.
if [[ $FULL -eq 1 ]]; then
  out="$(qmd "${args[@]}" 2>"$err")"; rc=$?
  if [[ -n "$out" ]]; then printf '%s\n' "$out"; exit 0; fi
  echo "qmd-search: qmd returned nothing (exit $rc)" >&2; head -n 5 "$err" >&2 || true; exit $(( rc == 0 ? 1 : rc ))
fi

# Default: parse --json (comma/quote-safe) into "score  path".
out="$(qmd "${args[@]}" --json 2>"$err")"; rc=$?
if printf '%s' "$out" | node -e '
  let s = "";
  process.stdin.on("data", d => s += d).on("end", () => {
    let a;
    try { a = JSON.parse(s); } catch (e) { process.exit(3); }
    if (!Array.isArray(a)) { process.exit(3); }
    if (a.length === 0) { console.log("(no results)"); process.exit(0); }
    for (const r of a) {
      const f = String(r.file || "").replace(/^qmd:\/\/[^/]+\//, "");
      const score = (r.score === undefined || r.score === null) ? "" : String(r.score);
      console.log("  " + score.padEnd(5) + "  " + f);
    }
    process.exit(0);
  });
'; then
  exit 0
fi
# Output didn't parse → a real failure.
echo "qmd-search: qmd exited $rc with no usable output" >&2
head -n 5 "$err" >&2 || true
exit $(( rc == 0 ? 1 : rc ))
