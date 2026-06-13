# Insert: Release / archive
1. Copy `archive.sh` → `scripts/archive.sh` (chmod +x), `ExportOptions.plist` → project root. Substitute `<Name>`/`<TEAM>`.
2. macOS apps: change `-destination 'generic/platform=iOS'` to `'generic/platform=macOS'` and add a
   notarization step (`xcrun notarytool submit`); set `method` to `developer-id`.
3. Requires a real DEVELOPMENT_TEAM + signing assets — this is a human-run release step, not the build gate.
4. Verify syntax only: `bash -n scripts/archive.sh`.
