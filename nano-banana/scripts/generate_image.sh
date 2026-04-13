#!/bin/bash
# Nano Banana - Gemini Image Generation
# Generates images from text prompts using Google's Gemini API
#
# Usage:
#   ./generate_image.sh "prompt text" [output_path] [model]
#   ./generate_image.sh --preset <name> "subject" [output_path] [model]
#   ./generate_image.sh --list-presets
#
# Arguments:
#   prompt      - Text description of the image to generate (required)
#   output_path - Where to save the image (default: ./generated_image.png)
#   model       - Model to use (default: gemini-3.1-flash-image-preview)
#                 Options: gemini-3.1-flash-image-preview (Nano Banana 2 - fastest, best instruction following)
#                          gemini-3-pro-image-preview     (Nano Banana Pro - highest quality, text in images)
#                          gemini-2.5-flash-image         (Nano Banana - original, fast)
#
# Presets:
#   --preset <name>   Apply a style preset from presets.yaml (wraps subject in style prompt)
#   --list-presets    Show available presets and exit
#
# Environment:
#   GEMINI_API_KEY - Auto-decrypted from secrets.enc.yaml or set manually
#
# Examples:
#   ./generate_image.sh "a cat sitting on a laptop"
#   ./generate_image.sh --preset editorial "interconnected nodes in a loop" ./overlay.png
#   ./generate_image.sh --preset ink "a mountain landscape" ./mountain.png
#   ./generate_image.sh --list-presets

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PRESETS_FILE="${SCRIPT_DIR}/presets.yaml"

# Handle --list-presets
if [ "${1:-}" = "--list-presets" ]; then
  if [ ! -f "$PRESETS_FILE" ]; then
    echo "No presets file found at $PRESETS_FILE" >&2
    exit 1
  fi
  python3 -c "
import yaml, sys
with open('$PRESETS_FILE') as f:
    presets = yaml.safe_load(f)
for name, conf in presets.items():
    print(f'  {name:16s} {conf[\"description\"]}')
"
  exit 0
fi

# Handle --preset <name>
PRESET=""
if [ "${1:-}" = "--preset" ]; then
  PRESET="${2:?Error: --preset requires a preset name}"
  shift 2
fi

SUBJECT="${1:?Error: prompt/subject is required. Usage: $0 [--preset name] \"prompt\" [output_path] [model]}"
OUTPUT="${2:-./generated_image.png}"
MODEL="${3:-gemini-3.1-flash-image-preview}"

# Apply preset if specified
if [ -n "$PRESET" ]; then
  if [ ! -f "$PRESETS_FILE" ]; then
    echo "Error: presets file not found at $PRESETS_FILE" >&2
    exit 1
  fi
  PROMPT=$(python3 -c "
import yaml, sys
with open('$PRESETS_FILE') as f:
    presets = yaml.safe_load(f)
name = '$PRESET'
if name not in presets:
    print(f'Error: preset \"{name}\" not found. Available: {list(presets.keys())}', file=sys.stderr)
    sys.exit(1)
template = presets[name]['prompt']
subject = '''$SUBJECT'''
print(template.replace('{subject}', subject))
")
  echo "Preset: ${PRESET}"
else
  PROMPT="$SUBJECT"
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
  CENTRAL_SECRETS="${SCRIPT_DIR}/../secrets.enc.yaml"
  LOCAL_SECRETS="${SCRIPT_DIR}/secrets.enc.yaml"
  if command -v sops >/dev/null 2>&1; then
    for f in "$LOCAL_SECRETS" "$CENTRAL_SECRETS"; do
      if [ -f "$f" ]; then
        GEMINI_API_KEY=$(sops --decrypt --extract '["GEMINI_API_KEY"]' "$f" 2>/dev/null)
        [ -n "$GEMINI_API_KEY" ] && break
      fi
    done
  fi
  if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "Error: GEMINI_API_KEY not set and could not decrypt from secrets.enc.yaml" >&2
    echo "Either: export GEMINI_API_KEY=... or ensure sops + age key are configured" >&2
    exit 1
  fi
fi

API_URL="https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent"

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT")"

echo "Generating image with ${MODEL}..."
echo "Prompt: ${PROMPT}"

# Escape prompt for JSON (handle quotes and newlines)
ESCAPED_PROMPT=$(printf '%s' "$PROMPT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')

# Make API call
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL" \
  -H "x-goog-api-key: ${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"contents\": [{
      \"parts\": [{\"text\": ${ESCAPED_PROMPT}}]
    }],
    \"generationConfig\": {
      \"responseModalities\": [\"TEXT\", \"IMAGE\"]
    }
  }")

# Split response body and HTTP status
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "200" ]; then
  echo "Error: API returned HTTP ${HTTP_CODE}" >&2
  echo "$BODY" | python3 -c "
import sys, json
try:
    err = json.load(sys.stdin)
    msg = err.get('error', {}).get('message', 'Unknown error')
    print(f'Message: {msg}', file=sys.stderr)
except:
    print(sys.stdin.read(), file=sys.stderr)
" 2>&1
  exit 1
fi

# Extract base64 image data from response
IMAGE_DATA=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
candidates = data.get('candidates', [])
if not candidates:
    print('ERROR:No candidates in response', file=sys.stderr)
    sys.exit(1)
parts = candidates[0].get('content', {}).get('parts', [])
for part in parts:
    if 'inlineData' in part:
        print(part['inlineData']['data'])
        sys.exit(0)
print('ERROR:No image data in response', file=sys.stderr)
sys.exit(1)
")

if [ $? -ne 0 ] || [ -z "$IMAGE_DATA" ]; then
  echo "Error: No image data found in response" >&2
  # Print any text response for debugging
  echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for part in data.get('candidates', [{}])[0].get('content', {}).get('parts', []):
    if 'text' in part:
        print(f'API text response: {part[\"text\"]}', file=sys.stderr)
" 2>&1
  exit 1
fi

# Decode and save
echo "$IMAGE_DATA" | base64 -d > "$OUTPUT"

FILE_SIZE=$(wc -c < "$OUTPUT" | tr -d ' ')
echo "Saved: ${OUTPUT} (${FILE_SIZE} bytes)"
echo "$OUTPUT"
