# init-xcode-app — Design Spec

**Date:** 2026-06-12
**Status:** Approved — ready for planning
**Author:** Gleb + Claude (brainstormed)

## 1. Purpose

A Claude Code skill that scaffolds a standalone **SwiftUI** app via **XcodeGen**, pre-loaded with
house conventions and the loop-closer toolchain set up earlier this session. The lighter native
sibling of `init-tauri-app`.

Reference project: `~/ai_projects/cenno/companion/` (real XcodeGen multi-target app).

Out of scope (covered elsewhere / YAGNI): the Swift-package-as-Rust-sidecar case (already the
`swift-sidecar` module in `init-tauri-app`); Storyboards/UIKit; multiplatform-single-target;
CocoaPods/Carthage; manual `.pbxproj` editing.

## 2. Approach: XcodeGen + layer

```
gather inputs → JTBD ingest (opt) → render project.yml + Swift sources → apply modules
   → xcodegen generate → xcodebuild build/test (gate)
```

`project.yml` is declarative, mergeable YAML → generated, **committed** `.xcodeproj`. This makes
module composition far less brittle than Tauri's (no `Cargo.toml`/`lib.rs` merges).

## 3. Target shapes (chosen at run time)

| shape | project.yml targets |
|---|---|
| **macOS app** | one macOS app target |
| **iOS app** | one iOS app target |
| **iOS + watchOS** | a Shared framework compiled for iOS *and* watchOS + iPhone app + Watch app (cenno pattern) |

(Not supported: multiplatform-single-target.)

## 4. Runtime flow

1. **Gather inputs** (AskUserQuestion): app name (kebab or PascalCase), bundle-id prefix
   (default `com.glebkalinin`), `DEVELOPMENT_TEAM` (**optional** — blank allowed), target shape,
   modules, optional JTBD path, target directory (default `~/ai_projects/<name>`).
2. **JTBD ingest (Step 1.5, optional, additive):** identical contract to `init-tauri-app` —
   resolve (explicit path → `./jtbd.json` → `~/jtbd/<name>/jtbd.json`), confirm via `hook`,
   validate, render product artifacts in the core layer. Reuses `assets/jtbd/`.
3. **Render core** (§5) for the chosen shape, substituting name / bundle-prefix / team / deployment targets.
4. **Compose selected modules** (§6), agent-assembled, gated per module.
5. **Generate + verify:** `xcodegen generate`, then the build gate (§7).

## 5. Core layer (always applied)

- **`project.yml`** — XcodeGen spec for the chosen shape, parameterized: `name`,
  `options.bundleIdPrefix`, `options.deploymentTarget`, `settings.DEVELOPMENT_TEAM` (placeholder if
  blank), `CODE_SIGN_STYLE: Automatic`, target(s), and a **test target** + scheme.
- **Swift sources** — SwiftUI `@main App`, a `ContentView` (List), a `DetailView`, and a sample
  `Item: Identifiable, Codable` model. For iOS+watchOS: a `Shared/` framework holding the model +
  a stub service, consumed by both apps.
- **Test target** — one **Swift Testing** (`import Testing`) test asserting on the sample model.
  (Tests ship by default — the analysis flagged their absence as the top gap.)
- **`.swiftformat` + `.swiftlint.yml`** — sensible defaults (tools already installed).
- **House `.gitignore`** — `build/`, `**/xcuserdata/`, `**/DerivedData/`, `.DS_Store`,
  `.enzyme/`; the generated `*.xcodeproj` **is committed** (XcodeGen output is deterministic).
- **`AGENTS.md`** — seeded from `~/.claude/templates/xcode-agent-starter/AGENTS.md`: build/test loop
  (xcsift + xcodebuild, the native Xcode MCP `RenderPreview`, `xcrun simctl`), **edit `project.yml`,
  never `.pbxproj`**, signing as a human gate, and a cross-reference to `init-tauri-app`'s
  `swift-sidecar` module for the native-from-Rust case.
- **`.claude/CLAUDE.md`** — one-line pointer to AGENTS.md.
- **README.md + CONTRIBUTING.md** stubs; `docs/` + ignored `docs/internal/`.

## 6. Opt-in modules

Each module = a `project.yml` fragment (targets/settings/entitlements) + source stubs + an
`INSERT.md` with merge instructions. Composition is agent-assembled, gated by
`xcodegen generate && xcodebuild build` after each.

| Module | Adds |
|---|---|
| **CloudKit + entitlements** | iCloud container id, `*.entitlements` (CloudKit) wired into the target's `entitlements:` block, a `CloudKitRelay`-style sync stub (cenno pattern) |
| **xcodebuild CI** | `.github/workflows/ci.yml` (macOS runner): `xcodegen generate` → `xcodebuild build`/`test` → `swiftlint` |
| **Release / archive** | `scripts/archive.sh` (`xcodebuild archive`) + `ExportOptions.plist`; macOS notarization steps / iOS TestFlight notes |
| **Push notifications** | `aps-environment` entitlement + `remote-notification` background mode in Info.plist + a registration stub |

Modules are written to compose: CloudKit + Push both touch the entitlements block (the skill merges
into one `entitlements:` map, doesn't overwrite).

## 7. Signing & the build gate

`DEVELOPMENT_TEAM` is **optional**. If blank, `project.yml` gets a placeholder and the gate runs an
**unsigned build**, by shape:
- **iOS / watchOS:** `xcodebuild build -scheme <S> -destination 'generic/platform=iOS Simulator'`
  (simulator needs no signing).
- **macOS:** `xcodebuild build -scheme <S> -destination 'platform=macOS' CODE_SIGNING_ALLOWED=NO`.

Device builds, archiving, notarization, and App Store submission remain documented **human steps**.
If a real team id is provided, the same gate still runs unsigned (fast, no signing assets needed).

## 8. Reuse across skills

- **`assets/jtbd/`** (map + templates + `render-jtbd.sh` + fixtures) — `init-xcode-app` carries its
  **own copy**, copied verbatim from `init-tauri-app/assets/jtbd/` at authoring time. (Skills install
  self-contained to `~/.claude/skills/<skill>/`, so a shared dir isn't reliable; the copies are
  byte-identical and a note in each `jtbd-map.md` flags that they must be kept in sync.) Only the
  AGENTS.md injection point differs per skill.
- Core AGENTS.md seeds from `~/.claude/templates/xcode-agent-starter/AGENTS.md`.

## 9. Location & packaging

- Authored in `glebis/claude-skills` at `init-xcode-app/`.
- `SKILL.md` + `assets/{core/<shape>/, jtbd/, modules/<m>/}`.
- Installed to `~/.claude/skills/init-xcode-app/`.

## 10. Testing

- Smoke matrix: **macOS/none, iOS/none, iOS+watchOS/none** (validates the three `project.yml`
  shapes via `xcodegen generate && xcodebuild build`), plus **iOS/all-modules** (validates
  composition + entitlements merge). Each ends green on the unsigned build gate.
- JTBD: reuse the existing `render-jtbd.sh` smoke against the Xcode AGENTS.md injection point.
- Negative: blank `DEVELOPMENT_TEAM` still produces a buildable project (the default path).

## 11. Non-goals

- Swift-package-as-Rust-sidecar (in `init-tauri-app`).
- UIKit/Storyboards/XIBs; multiplatform-single-target; CocoaPods/Carthage.
- Manual `.pbxproj` editing.
- Automated device signing / notarization (documented, not performed).
