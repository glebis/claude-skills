#!/usr/bin/env bash
# Verifies JTBD ingestion renders the right artifacts into a throwaway project dir.
set -euo pipefail
SKILL=~/ai_projects/claude-skills/init-tauri-app
TMP="$(mktemp -d)"; cd "$TMP"
mkdir -p proj/docs/internal proj/.claude
printf '# proj\n\nA Tauri app.\n' > proj/AGENTS.md   # stand-in for the core AGENTS.md
F="$SKILL/assets/jtbd/fixtures/sample-jtbd.json"
bash "$SKILL/scripts/render-jtbd.sh" "$F" "$SKILL/assets/jtbd/PRODUCT.md.template" "$F" > proj/docs/PRODUCT.md
bash "$SKILL/scripts/render-jtbd.sh" "$F" "$SKILL/assets/jtbd/guardrails-check.md.template" "$F" > proj/docs/internal/guardrails-check.md
bash "$SKILL/scripts/render-jtbd.sh" "$F" "$SKILL/assets/jtbd/agents-product-section.md.template" "$F" > proj/.jtbd-section.md
# insert section after first heading (read section from file — portable across BSD/GNU awk)
awk 'NR==FNR{sec=sec $0 ORS; next} FNR==1{print; print ""; printf "%s", sec; next} {print}' proj/.jtbd-section.md proj/AGENTS.md > proj/AGENTS.md.new && mv proj/AGENTS.md.new proj/AGENTS.md
trash proj/.jtbd-section.md
cp "$F" proj/jtbd.json
# assertions
grep -q "Capture a fleeting idea" proj/docs/PRODUCT.md
grep -q "Must NOT do" proj/AGENTS.md
grep -q "one project per session" proj/docs/internal/guardrails-check.md
test -f proj/jtbd.json
echo "JTBD_SMOKE_PASS dir=$TMP"
