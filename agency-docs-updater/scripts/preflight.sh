#!/usr/bin/env bash
# Preflight checks for the agency-docs-updater pipeline.
# Surfaces the three mid-pipeline failure modes (missing Python deps, missing
# Playwright browser, dead Groq key) UP FRONT, with the exact fix command.
# Exit non-zero only on hard blockers (deps/browser); a dead Groq key is a
# soft warning because metadata can be supplied manually.
set -uo pipefail

YOUTUBE_UPLOADER_DIR="${YOUTUBE_UPLOADER_DIR:-$HOME/ai_projects/youtube-uploader}"
fail=0

echo "── agency-docs-updater preflight ──"

# 1. youtube-uploader Python deps (no venv; installed --user)
if python3 -c "import google_auth_oauthlib, googleapiclient, groq" 2>/dev/null; then
  echo "✓ youtube-uploader Python deps importable"
else
  echo "✗ Missing Python deps — fix: cd \"$YOUTUBE_UPLOADER_DIR\" && python3 -m pip install --user -r requirements.txt"
  fail=1
fi

# 2. Playwright thumbnail render capability. Probe the SAME way render-thumbnails.mjs
#    resolves it (node module resolution from the uploader dir) — caches under
#    ~/Library/Caches/ms-playwright can be evicted under disk pressure, and the
#    `playwright` npm module itself must be installed (it's in package.json).
if (cd "$YOUTUBE_UPLOADER_DIR" && node -e "require.resolve('playwright')") >/dev/null 2>&1; then
  pw_exec=$(cd "$YOUTUBE_UPLOADER_DIR" && node -e "const {chromium}=require('playwright');process.stdout.write(chromium.executablePath())" 2>/dev/null)
  if [ -n "$pw_exec" ] && [ -x "$pw_exec" ]; then
    echo "✓ Playwright + chromium ready"
  else
    echo "✗ Playwright module OK but chromium browser missing — fix: cd \"$YOUTUBE_UPLOADER_DIR\" && npx playwright install chromium"
    fail=1
  fi
else
  echo "✗ Playwright module not installed — fix: cd \"$YOUTUBE_UPLOADER_DIR\" && npm install && npx playwright install chromium"
  fail=1
fi

# 3. Groq key validity (LLM metadata generation). Soft check.
GROQ_KEY="${GROQ_API_KEY:-}"
if [ -z "$GROQ_KEY" ] && [ -f "$YOUTUBE_UPLOADER_DIR/.env.local" ]; then
  GROQ_KEY=$(grep -E '^GROQ_API_KEY=' "$YOUTUBE_UPLOADER_DIR/.env.local" | head -1 | cut -d= -f2-)
fi
if [ -n "$GROQ_KEY" ]; then
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
    -H "Authorization: Bearer $GROQ_KEY" https://api.groq.com/openai/v1/models)
  if [ "$code" = "200" ]; then
    echo "✓ Groq API key valid"
  else
    echo "⚠ Groq API key invalid (HTTP $code) — LLM metadata will 401."
    echo "  Workaround: build VideoConfig with your own title/desc/tags and call upload.py directly."
  fi
else
  echo "⚠ No Groq key found — LLM metadata unavailable; supply title/desc/tags manually."
fi

if [ "$fail" -ne 0 ]; then
  echo "✗ Preflight FAILED — fix the blockers above before running the pipeline."
else
  echo "✓ Preflight OK"
fi
exit "$fail"
