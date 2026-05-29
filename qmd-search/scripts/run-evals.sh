#!/usr/bin/env bash
# run-evals.sh — run the qmd-search quality regression set via `qmd bench`.
# Usage: scripts/run-evals.sh [fixture.json]   (defaults to evals/fixture.example.json)
# Compare the printed Summary against evals/BASELINE.md after any change to the
# wrapper, the index, or the embedding model.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
FIXTURE="${1:-$HERE/../evals/fixture.example.json}"
[[ -f "$FIXTURE" ]] || { echo "fixture not found: $FIXTURE" >&2; exit 1; }
command -v qmd >/dev/null 2>&1 || { echo "qmd not on PATH" >&2; exit 1; }
# Strip the stderr spinner; show the table + summary.
qmd bench "$FIXTURE" 2>&1 | tr '\r' '\n' \
  | grep -vE 'gguf|MB/s|[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]' \
  | grep -vE '^\s*$'
