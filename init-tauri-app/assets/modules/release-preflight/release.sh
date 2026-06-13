#!/usr/bin/env bash
#
# release.sh — build, notarize, and publish a <name> release to GitHub.
#
# Reads ALL secrets from the environment; nothing is typed inline or stored
# in this file. Export these before running (sourced from your secrets vault
# — see README "Releasing an update"):
#
#   TAURI_SIGNING_PRIVATE_KEY_PASSWORD   updater key password
#   TAURI_SIGNING_PRIVATE_KEY_PATH       path to the minisign private key file
#   APPLE_API_KEY, APPLE_API_ISSUER, APPLE_API_KEY_PATH   App Store Connect key
#   APPLE_SIGNING_IDENTITY               "Developer ID Application: … (TEAMID)"
#
# Usage:
#
#   scripts/release.sh                 # build + publish from current version
#   scripts/release.sh --dry-run       # build + make latest.json, skip push/release
#
set -euo pipefail

REPO="glebis/<name>"
KEY_PATH="${TAURI_SIGNING_PRIVATE_KEY_PATH:-$HOME/.tauri/<name>.key}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

cd "$ROOT"

# --- Preflight: required env, version agreement -----------------

missing=()
for v in TAURI_SIGNING_PRIVATE_KEY_PASSWORD APPLE_API_KEY APPLE_API_ISSUER \
         APPLE_API_KEY_PATH APPLE_SIGNING_IDENTITY; do
  [[ -z "${!v:-}" ]] && missing+=("$v")
done
if ((${#missing[@]})); then
  echo "error: missing env vars: ${missing[*]}" >&2
  echo "see README 'Releasing an update' for what to export." >&2
  exit 1
fi
[[ -f "$KEY_PATH" ]] || { echo "error: signing key not found at $KEY_PATH" >&2; exit 1; }

VERSION="$(node -p "require('./package.json').version")"
CONF_VERSION="$(node -p "require('./src-tauri/tauri.conf.json').version")"
if [[ "$VERSION" != "$CONF_VERSION" ]]; then
  echo "error: version mismatch — package.json $VERSION vs tauri.conf.json $CONF_VERSION" >&2
  exit 1
fi
TAG="v$VERSION"
echo "==> releasing $TAG"

if git rev-parse "$TAG" >/dev/null 2>&1 || \
   gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  echo "error: $TAG already exists (tag or release). Bump the version first." >&2
  exit 1
fi

# --- Build (PATH=/usr/bin first: shadow conda/Python xattr that breaks bundling) ---

echo "==> building (signed, notarized, updater artifacts)"
PATH="/usr/bin:$PATH" \
TAURI_SIGNING_PRIVATE_KEY="$(cat "$KEY_PATH")" \
  npx tauri build

BUNDLE="src-tauri/target/release/bundle"
DMG="$(ls "$BUNDLE"/dmg/<name>_"$VERSION"_*.dmg)"
TARGZ="$BUNDLE/macos/<name>.app.tar.gz"
SIG="$TARGZ.sig"
for f in "$DMG" "$TARGZ" "$SIG"; do
  [[ -f "$f" ]] || { echo "error: expected artifact missing: $f" >&2; exit 1; }
done

# --- latest.json (the updater manifest) -------------------------------------

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp "$DMG" "$STAGE/"
cp "$TARGZ" "$STAGE/<name>.app.tar.gz"
cp "$SIG" "$STAGE/<name>.app.tar.gz.sig"

PUB_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
NOTES="$(awk "/^## \[$VERSION\]/{f=1;next} /^## \[/{f=0} f" CHANGELOG.md | tr '\n' ' ' | sed 's/  */ /g;s/^ *//;s/ *$//')"
node -e "
  const fs=require('fs');
  fs.writeFileSync('$STAGE/latest.json', JSON.stringify({
    version: '$VERSION',
    notes: process.env.N || 'See CHANGELOG.md.',
    pub_date: '$PUB_DATE',
    platforms: { 'darwin-aarch64': {
      signature: fs.readFileSync('$SIG','utf8').trim(),
      url: 'https://github.com/$REPO/releases/download/$TAG/<name>.app.tar.gz'
    }}
  }, null, 2));
" N="$NOTES"
echo "==> latest.json:"; cat "$STAGE/latest.json"

if ((DRY_RUN)); then
  echo "==> --dry-run: artifacts staged in $STAGE (not pushed). Copying out…"
  OUT="$ROOT/dist-release-$VERSION"; mkdir -p "$OUT"; cp "$STAGE"/* "$OUT/"
  echo "    $OUT"
  trap - EXIT
  exit 0
fi

# --- Publish ----------------------------------------------------------------

echo "==> pushing main"
git push origin main

echo "==> creating GitHub release $TAG"
gh release create "$TAG" --repo "$REPO" --title "<name> $TAG" \
  --notes "${NOTES:-Release $TAG. See CHANGELOG.md.}" \
  "$STAGE/$(basename "$DMG")" \
  "$STAGE/<name>.app.tar.gz" \
  "$STAGE/<name>.app.tar.gz.sig" \
  "$STAGE/latest.json"

echo "==> verifying live endpoint"
sleep 3
curl -sL "https://github.com/$REPO/releases/latest/download/latest.json" \
  | node -e "const d=JSON.parse(require('fs').readFileSync(0));console.log('live version:',d.version)"

echo "==> done: https://github.com/$REPO/releases/tag/$TAG"
