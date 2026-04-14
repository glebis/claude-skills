#!/bin/bash
# Nano Banana - thin bash wrapper for nano_banana.py
#
# This script preserves the original positional interface for backwards compat:
#   ./generate_image.sh "prompt" [output] [model]
#   ./generate_image.sh --preset NAME "subject" [output]
#   ./generate_image.sh --list-presets
#
# For full features (variants, edit, platforms, projects, history, init), use:
#   ./nano_banana.py
#
# See: nano_banana.py --help

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY="${SCRIPT_DIR}/nano_banana.py"

# Backwards-compatible legacy flag: --list-presets → list-presets subcommand
if [ "${1:-}" = "--list-presets" ]; then
  exec python3 "$PY" list-presets
fi

# Legacy: third positional was model ID. Translate to --model.
# Usage was: ./generate_image.sh [--preset N] "prompt" [output] [model]
ARGS=()
POSITIONAL=()
MODEL_FROM_POS=""

while [ $# -gt 0 ]; do
  case "$1" in
    --preset|--platform|--model|--edit|--reference|--project|--n)
      ARGS+=("$1" "$2")
      shift 2
      ;;
    --list-presets|--list-platforms|init|again|history|list-presets|list-platforms|\
    --no-metadata|--dry-run|--help|-h)
      ARGS+=("$1")
      shift
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

# Map 3rd positional (legacy model) to --model if not already set
if [ "${#POSITIONAL[@]}" -ge 3 ]; then
  MODEL_FROM_POS="${POSITIONAL[2]}"
  POSITIONAL=("${POSITIONAL[0]}" "${POSITIONAL[1]}")
  ARGS+=("--model" "$MODEL_FROM_POS")
fi

exec python3 "$PY" "${ARGS[@]}" "${POSITIONAL[@]}"
