#!/usr/bin/env bash
# Trim leading silence (pre-meeting dead air) from a recording before YouTube upload.
# Usage: trim_leading_silence.sh input.mp4 [output.mp4]
#   - Detects the first moment of sustained speech via ffmpeg silencedetect.
#   - Trims only if the leading silence is >10s; keeps 2s of lead-in before speech.
#   - Refuses to trim more than 20 minutes (safety against misdetection).
#   - Stream-copies (no re-encode); cut lands on the nearest keyframe.
# Prints the applied offset; writes output next to input as <name>.trimmed.mp4 if no output given.
set -euo pipefail

IN="$1"
OUT="${2:-${IN%.mp4}.trimmed.mp4}"
NOISE_DB="${NOISE_DB:--35dB}"   # silence threshold
MIN_SIL="${MIN_SIL:-2}"          # seconds of quiet that count as silence
LEAD_IN="${LEAD_IN:-2}"          # seconds kept before first speech
MAX_TRIM="${MAX_TRIM:-1200}"     # never cut more than 20 min

[ -f "$IN" ] || { echo "ERROR: input not found: $IN" >&2; exit 1; }

# Analyze only the first 25 minutes — leading silence lives there.
LOG=$(ffmpeg -hide_banner -t 1500 -i "$IN" -vn -af "silencedetect=noise=${NOISE_DB}:d=${MIN_SIL}" -f null - 2>&1 || true)

# If the file does not START in silence (first silence_start > 1s), nothing to trim.
FIRST_SIL_START=$(echo "$LOG" | grep -o 'silence_start: [0-9.]*' | head -1 | awk '{print $2}')
FIRST_SIL_END=$(echo "$LOG" | grep -o 'silence_end: [0-9.]*' | head -1 | awk '{print $2}')

if [ -z "${FIRST_SIL_END:-}" ] || [ -z "${FIRST_SIL_START:-}" ]; then
  echo "trim: no leading silence detected — keeping original"; exit 0
fi

python3 - "$FIRST_SIL_START" "$FIRST_SIL_END" "$LEAD_IN" "$MAX_TRIM" <<'PY' > /tmp/.trim_offset || { echo "trim: skipped"; exit 0; }
import sys
start, end, lead, cap = map(float, sys.argv[1:5])
if start > 1.0:      # audio present from the beginning
    sys.exit(1)
offset = max(0.0, end - lead)
if offset < 10.0:    # not worth cutting
    sys.exit(1)
if offset > cap:     # suspicious — refuse
    sys.exit(1)
print(f"{offset:.2f}")
PY

OFFSET=$(cat /tmp/.trim_offset)
echo "trim: cutting first ${OFFSET}s of leading silence"
ffmpeg -hide_banner -loglevel error -y -ss "$OFFSET" -i "$IN" -c copy -movflags faststart "$OUT"
echo "trim: wrote $OUT"
