#!/bin/bash
#
# Interactive meeting processor wrapper
# Called by Claude Code to handle AskUserQuestion flow
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRANSCRIPT_FILE="$1"
MODE="${2:-interactive}"

if [ -z "$TRANSCRIPT_FILE" ]; then
    echo "Usage: $0 <transcript-file> [mode]"
    exit 1
fi

# Load environment
if [ -f "$SCRIPT_DIR/scripts/.env" ]; then
    export $(cat "$SCRIPT_DIR/scripts/.env" | grep -v '^#' | xargs)
fi

# Run initial processing
cd "$SCRIPT_DIR/scripts"
python3 process.py "$TRANSCRIPT_FILE" --mode "$MODE"

echo ""
echo "Interactive processing complete!"
