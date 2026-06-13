# Insert: xcodebuild CI
1. Copy `ci.yml` → `.github/workflows/ci.yml`, substitute `<Name>`.
2. For a macOS app, change both `-destination` values to `'platform=macOS'`.
3. Verify locally: `bash -n` is N/A (YAML); run `xcodegen generate && xcodebuild build -scheme <Name> -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO`.
