# Insert: CloudKit + entitlements

1. Copy `App.entitlements` → `<Name>.entitlements` (substitute `<Name>`/`<bundlePrefix>`/`<name>`).
2. Copy `CloudKitStore.swift` → the app's source dir (`Sources/App` or `Sources/Shared` for ios-watchos).
3. Merge `project-fragment.yml` into `targets.<Name>` in `project.yml` (add the `entitlements:` and
   `dependencies:` keys; if a `dependencies:` list already exists, append).
4. Requires a real `DEVELOPMENT_TEAM` to build signed; the unsigned simulator gate still compiles.
5. Verify: `xcodegen generate && xcodebuild build -scheme <Name> -destination 'generic/platform=iOS Simulator'`.
