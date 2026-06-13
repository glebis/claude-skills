# Contributing

- Read [AGENTS.md](./AGENTS.md) first.
- Edit `project.yml`, then `xcodegen generate` — never touch `.pbxproj`.
- Build loop: `xcodebuild build -scheme <Name> | xcsift`. Format: `swiftformat .`. Lint: `swiftlint`.
- Signing for device/release is a manual step (see AGENTS.md).
