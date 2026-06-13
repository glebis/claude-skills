#!/usr/bin/env bash
set -euo pipefail
SCHEME="<Name>"
ARCHIVE="build/<Name>.xcarchive"
xcodegen generate
xcodebuild archive -scheme "$SCHEME" -archivePath "$ARCHIVE" -destination 'generic/platform=iOS'
xcodebuild -exportArchive -archivePath "$ARCHIVE" \
  -exportOptionsPlist ExportOptions.plist -exportPath build/export
echo "Archive + export complete: build/export"
