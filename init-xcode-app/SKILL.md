---
name: init-xcode-app
description: Scaffold a standalone SwiftUI app via XcodeGen — pick macOS, iOS, or iOS+watchOS; ships house conventions, a Swift Testing target, swiftformat/swiftlint, optional CloudKit/CI/Release/Push modules, and optional JTBD product context. Use to "init an xcode project", "scaffold a swiftui app", "new mac/ios app".
---

# init-xcode-app

Scaffolds a native SwiftUI app with XcodeGen (`project.yml` → generated, committed `.xcodeproj`),
pre-loaded with the conventions and loop-closer toolchain (xcsift, the Xcode MCP, swiftformat/lint).
The lighter native sibling of `init-tauri-app`.

## When to use
- "init an xcode project", "scaffold a swiftui app", "new macOS/iOS app".

## Prerequisites (verify before scaffolding)
- `xcodegen` on PATH (`xcodegen --version`; `brew install xcodegen` if missing).
- Xcode + CLT (`xcodebuild -version`).

## Procedure

### 1. Gather inputs (AskUserQuestion)
- **App name** (PascalCase, e.g. `Tidepool`) → `<Name>`; lowercase → `<name>`.
- **Bundle-id prefix** (default `com.glebkalinin`) → `<bundlePrefix>`.
- **DEVELOPMENT_TEAM** (optional — blank allowed) → `<TEAM>`.
- **Target shape:** `ios` | `macos` | `ios-watchos`.
- **Modules** (multi-select): CloudKit · CI · Release · Push.
- **JTBD artifact (optional):** path to a `jtbd.json` (else auto-discover `./jtbd.json`, `~/jtbd/<name>/jtbd.json`). See 1.5.
- **Target directory** (default `~/ai_projects/<name>`). Abort if non-empty.

### 1.5 Ingest JTBD (optional, additive)
Identical contract to init-tauri-app: resolve (explicit → `./jtbd.json` → `~/jtbd/<name>/jtbd.json`),
confirm via `hook`, validate (`render-jtbd.sh` exits 3 → skip), pre-fill name. Artifacts written in Step 3.

### 2. Render core
Copy `assets/core/common/*` into the project (renames: `gitignore`→`.gitignore`, `swiftformat`→`.swiftformat`,
`CLAUDE.md`→`.claude/CLAUDE.md`). Copy `assets/core/shapes/<shape>/*` into the project root. For `macos`,
also copy `assets/core/shapes/ios/Sources` + `Tests` (macos reuses the same SwiftUI sources). Substitute
`<Name>`/`<name>`/`<bundlePrefix>`/`<TEAM>` in every copied file. Blank `<TEAM>` → leave the placeholder line
`DEVELOPMENT_TEAM: ""`.

**If a JTBD artifact was confirmed:** render `assets/jtbd/PRODUCT.md.template`→`docs/PRODUCT.md`,
`guardrails-check.md.template`→`docs/internal/guardrails-check.md`, insert
`agents-product-section.md.template` into `AGENTS.md` after the first heading, copy the artifact to
project-root `jtbd.json`. See `assets/jtbd/jtbd-map.md`.

### 3. Compose selected modules
For each selected module open `assets/modules/<m>/INSERT.md` and follow it: it lists source files to copy
and a `project-fragment.yml` to merge into `project.yml` (merge into the existing `targets.<Name>` and
`entitlements:` maps — never overwrite). CloudKit + Push both extend the same `entitlements:` map.

### 4. Generate + verify (the gate)
```bash
xcodegen generate
```
Then the unsigned build gate by shape:
- ios / ios-watchos: `xcodebuild build -scheme <Name> -destination 'generic/platform=iOS Simulator'`
- macos: `xcodebuild build -scheme <Name> -destination 'platform=macOS' CODE_SIGNING_ALLOWED=NO`

Then `xcodebuild test` against the same destination for the test target. Both must pass.

### 5. Handoff
Offer `git init && git add -A && git commit`. Print summary: shape, modules, signing note
(device/release signing is a human step), next command (`open <Name>.xcodeproj`).
