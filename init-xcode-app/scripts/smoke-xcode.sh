#!/usr/bin/env bash
# Scaffolds a throwaway project for one shape and verifies xcodegen + unsigned xcodebuild build.
# Usage: smoke-xcode.sh <ios|macos|ios-watchos>
set -euo pipefail
SHAPE="$1"; SKILL=~/ai_projects/claude-skills/init-xcode-app
NAME="Smoke"; LOWER="smoke"; PREFIX="com.example"; TEAM=""
TMP="$(mktemp -d)"; cd "$TMP"
echo "=== $SHAPE in $TMP ==="
# core common
cp "$SKILL"/assets/core/common/AGENTS.md AGENTS.md
mkdir -p .claude && cp "$SKILL"/assets/core/common/CLAUDE.md .claude/CLAUDE.md
cp "$SKILL"/assets/core/common/gitignore .gitignore
cp "$SKILL"/assets/core/common/swiftformat .swiftformat
cp "$SKILL"/assets/core/common/swiftlint.yml .swiftlint.yml
# shape
cp -R "$SKILL/assets/core/shapes/$SHAPE/." .
# macos reuses ios sources
if [ "$SHAPE" = "macos" ]; then cp -R "$SKILL"/assets/core/shapes/ios/Sources .; cp -R "$SKILL"/assets/core/shapes/ios/Tests .; fi
# substitute placeholders in all text files (rename <Name>* files too)
find . -type f \( -name "*.swift" -o -name "*.yml" -o -name "*.md" -o -name "*.plist" \) -print0 \
  | xargs -0 sed -i '' -e "s/<Name>/$NAME/g" -e "s/<name>/$LOWER/g" -e "s/<bundlePrefix>/$PREFIX/g" -e "s/<TEAM>/$TEAM/g"
# rename files that carried <Name> in their filename
find . -depth -name "*<Name>*" | while read -r f; do mv "$f" "$(echo "$f" | sed "s/<Name>/$NAME/g")"; done
# generate + build
xcodegen generate
if [ "$SHAPE" = "macos" ]; then
  xcodebuild build -scheme "$NAME" -destination 'platform=macOS' CODE_SIGNING_ALLOWED=NO -quiet
else
  xcodebuild build -scheme "$NAME" -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO -quiet
fi
echo "=== PASS: $SHAPE === ($TMP)"
