# Insert: Push notifications
1. Copy `registration.swift` → the app source dir. Add `@UIApplicationDelegateAdaptor(PushDelegate.self) var delegate` to the `App` struct.
2. Merge `project-fragment.yml` into `targets.<Name>` — add `aps-environment` to the existing
   `entitlements.properties` map (do not overwrite a CloudKit entitlements block if present; merge keys),
   and add `INFOPLIST_KEY_UIBackgroundModes` to the target's `settings` map. Do NOT add a top-level
   `info:` block: with `GENERATE_INFOPLIST_FILE: YES` XcodeGen requires `info.path` and will fail to
   decode the spec — `UIBackgroundModes` must go through the `INFOPLIST_KEY_*` build setting instead.
3. iOS only (no `aps-environment` on macOS without extra setup). Requires a real team to build signed.
4. Verify: `xcodegen generate && xcodebuild build -scheme <Name> -destination 'generic/platform=iOS Simulator'`.
