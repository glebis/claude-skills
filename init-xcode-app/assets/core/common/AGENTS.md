# Agent guide — Xcode / Swift project

Canonical instructions for any coding agent (Claude Code, Codex, Cursor) working in this repo.
`CLAUDE.md` just points here.

**Project files:** this app uses XcodeGen — edit `project.yml`, then `xcodegen generate`. Never
hand-edit `<Name>.xcodeproj/project.pbxproj` (it's regenerated).

**Native code from Rust?** If you need a Swift static lib callable from a Rust/Tauri backend, use
the `swift-sidecar` module in `init-tauri-app`, not this skill.

## The loop (how you verify your own work)

1. Edit Swift.
2. Build + read errors as structured JSON — never eyeball raw `xcodebuild`.
3. Fix from `file:line:col`. Repeat until clean.
4. Run tests. Then, for UI, *look* at the result.

## Build & test

Two paths — prefer the Xcode MCP when Xcode is open, fall back to CLI:

- **Xcode MCP (already wired at user scope, `xcrun mcpbridge`)** — `BuildProject`, `RunAllTests`/`RunSomeTests`, `GetBuildLog`, and **`RenderPreview`** which returns a real SwiftUI screenshot so you can see UI iterations. This is the primary loop when Xcode is running.
- **CLI (headless / CI / Xcode closed)** — always pipe through `xcsift` for token-lean JSON:

```bash
xcodebuild -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 16' build 2>&1 | xcsift
xcodebuild -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 16' test  2>&1 | xcsift
swift test            # for SPM packages — clean output, no wrapper needed
```

## Simulator (UI automation)

`xcrun simctl` is fully scriptable; for tap/swipe/screenshot loops add the **XcodeBuildMCP** server (see `.mcp.json`).

```bash
xcrun simctl boot "iPhone 16"
xcrun simctl install booted <App.app>
xcrun simctl launch booted <bundle.id>
xcrun simctl io booted screenshot /tmp/sim.png   # feed back to yourself to "see" the UI
```

## Lint / format (deterministic gates)

```bash
swiftformat .
swiftlint --strict
```

## Hard rules / human gates

- **Never hand-edit `.pbxproj`.** Adding files to targets is unreliable. If this project uses **XcodeGen/Tuist**, edit the YAML/Swift spec and regenerate. Otherwise flag target-membership changes for the human.
- **Code signing, provisioning, App Store submission** stay human steps. Validate, don't sign.
- **Storyboards/XIBs are opaque** — prefer SwiftUI for anything you author.
- Simulator ≠ device (unlimited memory, ideal network). Necessary, not sufficient.

## Recommended skills

Community Swift skills (Apple's `mcpbridge skills export` was empty on this machine):
- Paul Hudson's `swift-agent-skills` — `swiftui-pro`, `swift-concurrency`, `swift-testing`.
  `npx skills add https://github.com/twostraws/swiftui-agent-skill --skill swiftui-pro`
