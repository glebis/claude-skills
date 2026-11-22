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

# 1. youtube-uploader Python deps. Prefer the repo venv when present — system
#    python3 is PEP 668 externally-managed, so `pip install --user` there fails.
if [ -x "$YOUTUBE_UPLOADER_DIR/.venv/bin/python" ]; then
  PY="$YOUTUBE_UPLOADER_DIR/.venv/bin/python"
  PY_FIX="cd \"$YOUTUBE_UPLOADER_DIR\" && .venv/bin/pip install -r requirements.txt"
else
  PY=python3
  PY_FIX="cd \"$YOUTUBE_UPLOADER_DIR\" && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
fi
if "$PY" -c "import google_auth_oauthlib, googleapiclient, groq" 2>/dev/null; then
  echo "✓ youtube-uploader Python deps importable ($PY)"
else
  echo "✗ Missing Python deps — fix: $PY_FIX"
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

# 3. Groq key validity (LLM metadata + transcribe_cut.py). Soft check.
# Source of truth: SOPS (~/.claude/skills/secrets.enc.yaml). GDA 01 (2026-10-10): the
# preflight read a dead copy in youtube-uploader/.env.local while SOPS held a valid key,
# and the run stalled asking the user for a key it already had. Order: SOPS -> env -> .env.local.
SOPS_FILE="${SOPS_SECRETS_FILE:-$HOME/.claude/skills/secrets.enc.yaml}"
GROQ_KEY="" ; GROQ_SRC=""
if command -v sops >/dev/null 2>&1 && [ -f "$SOPS_FILE" ]; then
  GROQ_KEY=$(OPENAI_API_KEY="" SOPS_AGE_KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}" \
    sops -d --extract '["GROQ_API_KEY"]' "$SOPS_FILE" 2>/dev/null) && GROQ_SRC="SOPS"
fi
if [ -z "$GROQ_KEY" ] && [ -n "${GROQ_API_KEY:-}" ]; then GROQ_KEY="$GROQ_API_KEY"; GROQ_SRC="env"; fi
if [ -z "$GROQ_KEY" ] && [ -f "$YOUTUBE_UPLOADER_DIR/.env.local" ]; then
  GROQ_KEY=$(grep -E '^GROQ_API_KEY=' "$YOUTUBE_UPLOADER_DIR/.env.local" | head -1 | cut -d= -f2- | tr -d '"')
  [ -n "$GROQ_KEY" ] && GROQ_SRC=".env.local"
fi
if [ -n "$GROQ_KEY" ]; then
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
    -H "Authorization: Bearer $GROQ_KEY" https://api.groq.com/openai/v1/models)
  if [ "$code" = "200" ]; then
    echo "✓ Groq API key valid (from $GROQ_SRC)"
    [ "$GROQ_SRC" = "SOPS" ] && echo "  run uploader/transcription steps with: GROQ_API_KEY=\"\$(OPENAI_API_KEY= SOPS_AGE_KEY_FILE=\$HOME/.config/sops/age/keys.txt sops -d --extract '[\"GROQ_API_KEY\"]' $SOPS_FILE)\" …  (overrides any stale .env.local copy)"
  else
    echo "⚠ Groq API key from $GROQ_SRC invalid (HTTP $code) — update it in SOPS (sops set --value-file), not in .env.local."
  fi
else
  echo "⚠ No Groq key found in SOPS, env or .env.local — LLM metadata unavailable; supply title/desc/tags manually."
fi

if [ "$fail" -ne 0 ]; then
  echo "✗ Preflight FAILED — fix the blockers above before running the pipeline."
else
  echo "✓ Preflight OK"
fi
exit "$fail"
