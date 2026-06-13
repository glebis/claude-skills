# init-xcode-app Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill that scaffolds a standalone SwiftUI app via XcodeGen in one of three target shapes (macOS / iOS / iOS+watchOS), with house conventions, a Swift Testing target, JTBD ingestion, and four opt-in modules, verified by `xcodegen generate && xcodebuild build`.

**Architecture:** A `SKILL.md` procedure renders a per-shape `project.yml` + Swift sources, applies optional modules (YAML fragments + source stubs merged agent-side), runs `xcodegen generate`, and gates on an unsigned `xcodebuild build`/`test`. Composition is YAML-merge, not code-merge, so it's far less brittle than the Tauri skill.

**Tech Stack:** Claude Code skill (Markdown + asset files), XcodeGen (`/opt/homebrew/bin/xcodegen`), SwiftUI, Swift Testing, xcodebuild, swiftformat/swiftlint. Reference: `~/ai_projects/cenno/companion/project.yml`.

**Spec:** `claude-skills/docs/superpowers/specs/2026-06-12-init-xcode-app-design.md`

**Conventions for all tasks:**
- All paths under `~/ai_projects/claude-skills/init-xcode-app/`.
- **No git commits** unless the controller says otherwise — SKIP every "Commit" step.
- Asset template files store placeholders as `<Name>` (PascalCase product), `<name>` (lowercase),
  `<bundlePrefix>` (e.g. `com.glebkalinin`), `<TEAM>` (DEVELOPMENT_TEAM or empty).
- These are template assets in the skill repo — NOT compiled in place. Real compilation happens only
  in the Task 9 smoke harness.

---

## File Structure

```
init-xcode-app/
  SKILL.md
  assets/
    core/
      common/   { AGENTS.md, CLAUDE.md, gitignore, swiftformat, swiftlint.yml, README.md, CONTRIBUTING.md }
      shapes/
        ios/         { project.yml, Sources/App/{App,ContentView,DetailView,Item}.swift, Tests/ItemTests.swift }
        macos/       { project.yml }                      # reuses ios Sources/App + Tests
        ios-watchos/ { project.yml, Sources/Shared/{Item,SyncService}.swift,
                       Sources/iPhone/{App,ContentView}.swift, Sources/Watch/{App,ContentView}.swift,
                       Tests/ItemTests.swift }
    jtbd/    # byte-identical copy of init-tauri-app/assets/jtbd/, AGENTS injection point differs
    modules/
      cloudkit/ { INSERT.md, project-fragment.yml, App.entitlements, CloudKitStore.swift }
      ci/       { INSERT.md, ci.yml }
      release/  { INSERT.md, archive.sh, ExportOptions.plist }
      push/     { INSERT.md, project-fragment.yml, registration.swift }
  scripts/smoke-xcode.sh
```

---

## Task 1: Skill skeleton + SKILL.md

**Files:**
- Create: `init-xcode-app/SKILL.md`

- [ ] **Step 1: Create SKILL.md frontmatter + overview**

```markdown
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
```

- [ ] **Step 2: Append the procedure**

````markdown
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
````

- [ ] **Step 3: Validate** — `grep -nE "TBD|FIXME" SKILL.md` (ignore `TBD` inside `JTBD`); confirm frontmatter `name: init-xcode-app`.

- [ ] **Step 4: Commit** — SKIP if no-commit.

---

## Task 2: Core common assets

**Files:**
- Create: `assets/core/common/{AGENTS.md, CLAUDE.md, gitignore, swiftformat, swiftlint.yml, README.md, CONTRIBUTING.md}`

- [ ] **Step 1: Seed AGENTS.md from the existing Xcode starter template**

```bash
mkdir -p ~/ai_projects/claude-skills/init-xcode-app/assets/core/common
cp ~/.claude/templates/xcode-agent-starter/AGENTS.md \
   ~/ai_projects/claude-skills/init-xcode-app/assets/core/common/AGENTS.md
```
Then edit the copy to add, near the top, an XcodeGen note and a sidecar cross-reference:
- "**Project files:** this app uses XcodeGen — edit `project.yml`, then `xcodegen generate`. Never
  hand-edit `<Name>.xcodeproj/project.pbxproj` (it's regenerated)."
- "**Native code from Rust?** If you need a Swift static lib callable from a Rust/Tauri backend, use
  the `swift-sidecar` module in `init-tauri-app`, not this skill."

- [ ] **Step 2: Create `CLAUDE.md`**

```markdown
# Project instructions

See **[AGENTS.md](../AGENTS.md)** — the canonical agent guide for this repo. Follow it exactly.
```

- [ ] **Step 3: Create `gitignore`**

```gitignore
# macOS
.DS_Store
# Xcode
build/
**/xcuserdata/
**/DerivedData/
*.xcuserstate
# SwiftPM
.build/
# Agent/tooling caches
.enzyme/
.enzyme-embeddings/
docs/internal/
# NOTE: the XcodeGen-generated <Name>.xcodeproj IS committed (deterministic output).
```

- [ ] **Step 4: Create `swiftformat`**

```
--swiftversion 6.0
--indent 4
--maxwidth 100
--self remove
--commas inline
```

- [ ] **Step 5: Create `swiftlint.yml`**

```yaml
disabled_rules:
  - trailing_whitespace
opt_in_rules:
  - empty_count
  - closure_spacing
excluded:
  - build
  - DerivedData
line_length:
  warning: 120
  error: 200
```

- [ ] **Step 6: Create `README.md`**

```markdown
# <Name>

A native SwiftUI app (XcodeGen). See [AGENTS.md](./AGENTS.md) for the developer/agent guide.

## Develop
```bash
xcodegen generate
open <Name>.xcodeproj
```
```

- [ ] **Step 7: Create `CONTRIBUTING.md`**

```markdown
# Contributing

- Read [AGENTS.md](./AGENTS.md) first.
- Edit `project.yml`, then `xcodegen generate` — never touch `.pbxproj`.
- Build loop: `xcodebuild build -scheme <Name> | xcsift`. Format: `swiftformat .`. Lint: `swiftlint`.
- Signing for device/release is a manual step (see AGENTS.md).
```

- [ ] **Step 8: Validate** — `test -f` each of the 7 files; `grep -c "XcodeGen" AGENTS.md` ≥ 1.

- [ ] **Step 9: Commit** — SKIP if no-commit.

---

## Task 3: Shape — iOS (project.yml + Swift sources + test)

**Files:**
- Create: `assets/core/shapes/ios/project.yml`, `.../Sources/App/{App,ContentView,DetailView,Item}.swift`, `.../Tests/ItemTests.swift`

- [ ] **Step 1: `project.yml`**

```yaml
name: <Name>
options:
  bundleIdPrefix: <bundlePrefix>
  deploymentTarget:
    iOS: "17.0"
settings:
  DEVELOPMENT_TEAM: "<TEAM>"
  CODE_SIGN_STYLE: Automatic
targets:
  <Name>:
    type: application
    platform: iOS
    sources:
      - path: Sources/App
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: <bundlePrefix>.<name>
      GENERATE_INFOPLIST_FILE: YES
      INFOPLIST_KEY_UILaunchScreen_Generation: YES
  <Name>Tests:
    type: bundle.unit-test
    platform: iOS
    sources:
      - path: Tests
    dependencies:
      - target: <Name>
    settings:
      GENERATE_INFOPLIST_FILE: YES
schemes:
  <Name>:
    build:
      targets:
        <Name>: all
        <Name>Tests: [test]
    run:
      config: Debug
    test:
      config: Debug
      targets: [<Name>Tests]
```

- [ ] **Step 2: `Sources/App/<Name>App.swift`** (file literally named with the placeholder; renamed at apply)

```swift
import SwiftUI

@main
struct <Name>App: App {
    var body: some Scene {
        WindowGroup { ContentView() }
    }
}
```

- [ ] **Step 3: `Sources/App/ContentView.swift`**

```swift
import SwiftUI

struct ContentView: View {
    private let items = Item.samples
    var body: some View {
        NavigationStack {
            List(items) { item in
                NavigationLink(item.title) { DetailView(item: item) }
            }
            .navigationTitle("<Name>")
        }
    }
}
```

- [ ] **Step 4: `Sources/App/DetailView.swift`**

```swift
import SwiftUI

struct DetailView: View {
    let item: Item
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(item.title).font(.title)
            Text(item.detail).foregroundStyle(.secondary)
            Spacer()
        }
        .padding()
        .navigationTitle(item.title)
    }
}
```

- [ ] **Step 5: `Sources/App/Item.swift`**

```swift
import Foundation

struct Item: Identifiable, Codable, Hashable {
    let id: UUID
    let title: String
    let detail: String

    init(id: UUID = UUID(), title: String, detail: String) {
        self.id = id
        self.title = title
        self.detail = detail
    }

    static let samples = [
        Item(title: "First", detail: "A sample item."),
        Item(title: "Second", detail: "Another sample item."),
    ]
}
```

- [ ] **Step 6: `Tests/ItemTests.swift`** (Swift Testing)

```swift
import Testing
@testable import <Name>

struct ItemTests {
    @Test func samplesArePresent() {
        #expect(Item.samples.count == 2)
        #expect(Item.samples.first?.title == "First")
    }
}
```

- [ ] **Step 7: Validate** — `grep -RnE "TBD|FIXME" assets/core/shapes/ios` → none; YAML parses
  (`python3 -c "import yaml,sys; yaml.safe_load(open('assets/core/shapes/ios/project.yml'))"` —
  note the `<...>` placeholders are valid YAML strings here since they're quoted or bare scalars;
  if the bare `<Name>` trips the parser, that's expected for a template — confirm by eye instead).

- [ ] **Step 8: Commit** — SKIP if no-commit.

---

## Task 4: Shape — macOS (project.yml delta)

**Files:**
- Create: `assets/core/shapes/macos/project.yml`

macOS reuses the iOS `Sources/App` + `Tests` (copied by SKILL.md Step 2). Only `project.yml` differs.

- [ ] **Step 1: `project.yml`**

```yaml
name: <Name>
options:
  bundleIdPrefix: <bundlePrefix>
  deploymentTarget:
    macOS: "14.0"
settings:
  DEVELOPMENT_TEAM: "<TEAM>"
  CODE_SIGN_STYLE: Automatic
targets:
  <Name>:
    type: application
    platform: macOS
    sources:
      - path: Sources/App
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: <bundlePrefix>.<name>
      GENERATE_INFOPLIST_FILE: YES
  <Name>Tests:
    type: bundle.unit-test
    platform: macOS
    sources:
      - path: Tests
    dependencies:
      - target: <Name>
    settings:
      GENERATE_INFOPLIST_FILE: YES
schemes:
  <Name>:
    build:
      targets:
        <Name>: all
        <Name>Tests: [test]
    run:
      config: Debug
    test:
      config: Debug
      targets: [<Name>Tests]
```

- [ ] **Step 2: Validate** — file exists; differs from iOS only in `platform`/`deploymentTarget`/launch-screen key. Commit — SKIP if no-commit.

---

## Task 5: Shape — iOS + watchOS (shared framework)

**Files:**
- Create: `assets/core/shapes/ios-watchos/project.yml`, `.../Sources/Shared/{Item,SyncService}.swift`, `.../Sources/iPhone/{<Name>App,ContentView}.swift`, `.../Sources/Watch/{<Name>WatchApp,WatchContentView}.swift`, `.../Tests/ItemTests.swift`

**Adapt from:** `~/ai_projects/cenno/companion/project.yml` (genericize: `Cenno*`→`<Name>*`,
`app.cenno`→`<bundlePrefix>.<name>`, drop CloudKit/push from core — those are modules).

- [ ] **Step 1: `project.yml`** (Shared framework iOS + watchOS + iPhone app + Watch app + test)

```yaml
name: <Name>
options:
  bundleIdPrefix: <bundlePrefix>
  deploymentTarget:
    iOS: "17.0"
    watchOS: "10.0"
settings:
  DEVELOPMENT_TEAM: "<TEAM>"
  CODE_SIGN_STYLE: Automatic
targets:
  <Name>Shared:
    type: framework
    platform: iOS
    sources: [{ path: Sources/Shared }]
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: <bundlePrefix>.<name>.shared
      GENERATE_INFOPLIST_FILE: YES
  <Name>SharedWatch:
    type: framework
    platform: watchOS
    sources: [{ path: Sources/Shared }]
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: <bundlePrefix>.<name>.shared.watch
      GENERATE_INFOPLIST_FILE: YES
  <Name>:
    type: application
    platform: iOS
    sources: [{ path: Sources/iPhone }]
    dependencies:
      - target: <Name>Shared
        embed: true
      - target: <Name>Watch
        embed: true
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: <bundlePrefix>.<name>
      GENERATE_INFOPLIST_FILE: YES
      INFOPLIST_KEY_UILaunchScreen_Generation: YES
  <Name>Watch:
    type: application
    platform: watchOS
    sources: [{ path: Sources/Watch }]
    dependencies:
      - target: <Name>SharedWatch
        embed: true
    info:
      path: Sources/Watch/Info.plist
      properties:
        WKApplication: true
        WKCompanionAppBundleIdentifier: <bundlePrefix>.<name>
    settings:
      PRODUCT_BUNDLE_IDENTIFIER: <bundlePrefix>.<name>.watch
      LD_RUNPATH_SEARCH_PATHS: ["$(inherited)", "@executable_path/Frameworks"]
  <Name>Tests:
    type: bundle.unit-test
    platform: iOS
    sources: [{ path: Tests }]
    dependencies:
      - target: <Name>Shared
    settings:
      GENERATE_INFOPLIST_FILE: YES
schemes:
  <Name>:
    build:
      targets:
        <Name>: all
        <Name>Shared: all
        <Name>Tests: [test]
    run: { config: Debug }
    test: { config: Debug, targets: [<Name>Tests] }
  <Name>Watch:
    build:
      targets:
        <Name>Watch: all
        <Name>SharedWatch: all
    run: { config: Debug }
```

- [ ] **Step 2: `Sources/Shared/Item.swift`** — same `Item` struct as Task 3 Step 5, but make
  the type and `samples` `public` (it's consumed by app targets across a framework boundary):

```swift
import Foundation

public struct Item: Identifiable, Codable, Hashable {
    public let id: UUID
    public let title: String
    public let detail: String

    public init(id: UUID = UUID(), title: String, detail: String) {
        self.id = id
        self.title = title
        self.detail = detail
    }

    public static let samples = [
        Item(title: "First", detail: "A sample item."),
        Item(title: "Second", detail: "Another sample item."),
    ]
}
```

- [ ] **Step 3: `Sources/Shared/SyncService.swift`** — a trivial public stub (extension point):

```swift
import Foundation

public final class SyncService: ObservableObject {
    @Published public private(set) var items: [Item]
    public init(items: [Item] = Item.samples) { self.items = items }
    public func reload() { items = Item.samples }
}
```

- [ ] **Step 4: `Sources/iPhone/<Name>App.swift`**

```swift
import SwiftUI
import <Name>Shared

@main
struct <Name>App: App {
    @StateObject private var sync = SyncService()
    var body: some Scene {
        WindowGroup { ContentView().environmentObject(sync) }
    }
}
```

- [ ] **Step 5: `Sources/iPhone/ContentView.swift`**

```swift
import SwiftUI
import <Name>Shared

struct ContentView: View {
    @EnvironmentObject private var sync: SyncService
    var body: some View {
        NavigationStack {
            List(sync.items) { item in
                VStack(alignment: .leading) {
                    Text(item.title).font(.headline)
                    Text(item.detail).font(.subheadline).foregroundStyle(.secondary)
                }
            }
            .navigationTitle("<Name>")
        }
    }
}
```

- [ ] **Step 6: `Sources/Watch/<Name>WatchApp.swift`**

```swift
import SwiftUI
import <Name>SharedWatch

@main
struct <Name>WatchApp: App {
    @StateObject private var sync = SyncService()
    var body: some Scene {
        WindowGroup { WatchContentView().environmentObject(sync) }
    }
}
```

- [ ] **Step 7: `Sources/Watch/WatchContentView.swift`**

```swift
import SwiftUI
import <Name>SharedWatch

struct WatchContentView: View {
    @EnvironmentObject private var sync: SyncService
    var body: some View {
        List(sync.items) { Text($0.title) }
    }
}
```

> Note: `Sources/Shared` is compiled into both `<Name>Shared` (iOS) and `<Name>SharedWatch`
> (watchOS), so the iPhone imports `<Name>Shared` and the Watch imports `<Name>SharedWatch` —
> same source, two module names. The skill substitutes both.

- [ ] **Step 8: `Tests/ItemTests.swift`** — imports the framework module:

```swift
import Testing
@testable import <Name>Shared

struct ItemTests {
    @Test func samplesArePresent() {
        #expect(Item.samples.count == 2)
        #expect(Item.samples.first?.title == "First")
    }
}
```

- [ ] **Step 9: Validate** — all files exist; `grep -Rn "Cenno" assets/core/shapes/ios-watchos` → none (fully genericized). Commit — SKIP if no-commit.

---

## Task 6: JTBD assets (copy + retarget)

**Files:**
- Create: `assets/jtbd/*` (copied from init-tauri-app)

- [ ] **Step 1: Copy the JTBD asset group verbatim**

```bash
cp -R ~/ai_projects/claude-skills/init-tauri-app/assets/jtbd \
      ~/ai_projects/claude-skills/init-xcode-app/assets/jtbd
```

- [ ] **Step 2: Add the sync note to `jtbd-map.md`**

Append to `assets/jtbd/jtbd-map.md`:
```markdown

> This asset group is duplicated in `init-tauri-app` and `init-xcode-app` and must be kept
> byte-identical. The only per-skill difference is where `agents-product-section.md.template`
> is injected into that skill's AGENTS.md (after the first heading).
```

- [ ] **Step 3: Verify the renderer still works here**

```bash
cd ~/ai_projects/claude-skills/init-xcode-app
bash scripts/../assets/jtbd/../../init-tauri-app/scripts/render-jtbd.sh 2>/dev/null || true
# Direct check: render the copied fixture against the copied template
bash ~/ai_projects/claude-skills/init-tauri-app/scripts/render-jtbd.sh \
  assets/jtbd/fixtures/sample-jtbd.json assets/jtbd/PRODUCT.md.template x | grep -q "Capture a fleeting idea" && echo JTBD_COPY_OK
```
Expected: `JTBD_COPY_OK`. (The renderer script itself lives at `init-tauri-app/scripts/render-jtbd.sh`;
copy it into `init-xcode-app/scripts/render-jtbd.sh` too so the skill is self-contained.)

- [ ] **Step 4: Copy the renderer into this skill**

```bash
mkdir -p ~/ai_projects/claude-skills/init-xcode-app/scripts
cp ~/ai_projects/claude-skills/init-tauri-app/scripts/render-jtbd.sh \
   ~/ai_projects/claude-skills/init-xcode-app/scripts/render-jtbd.sh
chmod +x ~/ai_projects/claude-skills/init-xcode-app/scripts/render-jtbd.sh
```

- [ ] **Step 5: Commit** — SKIP if no-commit.

---

## Task 7: Module — CloudKit + entitlements

**Files:**
- Create: `assets/modules/cloudkit/{INSERT.md, project-fragment.yml, App.entitlements, CloudKitStore.swift}`

**Adapt from:** `cenno/companion/Sources/iPhone/CennoiPhone.entitlements` and `Sources/Shared/CloudKitRelay.swift` (reduce to a minimal store stub).

- [ ] **Step 1: `App.entitlements`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.developer.icloud-container-identifiers</key>
  <array><string>iCloud.<bundlePrefix>.<name></string></array>
  <key>com.apple.developer.icloud-services</key>
  <array><string>CloudKit</string></array>
</dict>
</plist>
```

- [ ] **Step 2: `project-fragment.yml`** (merge into `targets.<Name>`)

```yaml
# Merge into targets.<Name>:
entitlements:
  path: <Name>.entitlements
  properties:
    com.apple.developer.icloud-container-identifiers:
      - iCloud.<bundlePrefix>.<name>
    com.apple.developer.icloud-services:
      - CloudKit
dependencies:
  - sdk: CloudKit.framework
```

- [ ] **Step 3: `CloudKitStore.swift`** (minimal stub)

```swift
import CloudKit
import Foundation

/// Minimal CloudKit store stub. Container id must match the entitlement.
public final class CloudKitStore {
    private let container: CKContainer
    public init(identifier: String = "iCloud.<bundlePrefix>.<name>") {
        self.container = CKContainer(identifier: identifier)
    }
    /// Fetches the account status; expand with record fetch/save as needed.
    public func accountStatus() async throws -> CKAccountStatus {
        try await container.accountStatus()
    }
}
```

- [ ] **Step 4: `INSERT.md`**

```markdown
# Insert: CloudKit + entitlements

1. Copy `App.entitlements` → `<Name>.entitlements` (substitute `<Name>`/`<bundlePrefix>`/`<name>`).
2. Copy `CloudKitStore.swift` → the app's source dir (`Sources/App` or `Sources/Shared` for ios-watchos).
3. Merge `project-fragment.yml` into `targets.<Name>` in `project.yml` (add the `entitlements:` and
   `dependencies:` keys; if a `dependencies:` list already exists, append).
4. Requires a real `DEVELOPMENT_TEAM` to build signed; the unsigned simulator gate still compiles.
5. Verify: `xcodegen generate && xcodebuild build -scheme <Name> -destination 'generic/platform=iOS Simulator'`.
```

- [ ] **Step 5: Validate** — XML + YAML files exist; `grep -c "CloudKit" CloudKitStore.swift` ≥ 1. Commit — SKIP if no-commit.

---

## Task 8: Modules — CI, Release, Push

**Files:**
- Create: `assets/modules/ci/{INSERT.md, ci.yml}`, `assets/modules/release/{INSERT.md, archive.sh, ExportOptions.plist}`, `assets/modules/push/{INSERT.md, project-fragment.yml, registration.swift}`

- [ ] **Step 1: `ci/ci.yml`**

```yaml
name: ci
on: [push, pull_request]
jobs:
  build:
    runs-on: macos-15
    steps:
      - uses: actions/checkout@v4
      - run: brew install xcodegen swiftlint
      - run: xcodegen generate
      - run: swiftlint
      - run: xcodebuild build -scheme <Name> -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO
      - run: xcodebuild test -scheme <Name> -destination 'platform=iOS Simulator,name=iPhone 16' CODE_SIGNING_ALLOWED=NO
```

- [ ] **Step 2: `ci/INSERT.md`**

```markdown
# Insert: xcodebuild CI
1. Copy `ci.yml` → `.github/workflows/ci.yml`, substitute `<Name>`.
2. For a macOS app, change both `-destination` values to `'platform=macOS'`.
3. Verify locally: `bash -n` is N/A (YAML); run `xcodegen generate && xcodebuild build -scheme <Name> -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO`.
```

- [ ] **Step 3: `release/archive.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
SCHEME="<Name>"
ARCHIVE="build/<Name>.xcarchive"
xcodegen generate
xcodebuild archive -scheme "$SCHEME" -archivePath "$ARCHIVE" -destination 'generic/platform=iOS'
xcodebuild -exportArchive -archivePath "$ARCHIVE" \
  -exportOptionsPlist ExportOptions.plist -exportPath build/export
echo "Archive + export complete: build/export"
```

- [ ] **Step 4: `release/ExportOptions.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>method</key><string>app-store-connect</string>
  <key>teamID</key><string><TEAM></string>
  <key>signingStyle</key><string>automatic</string>
</dict>
</plist>
```

- [ ] **Step 5: `release/INSERT.md`**

```markdown
# Insert: Release / archive
1. Copy `archive.sh` → `scripts/archive.sh` (chmod +x), `ExportOptions.plist` → project root. Substitute `<Name>`/`<TEAM>`.
2. macOS apps: change `-destination 'generic/platform=iOS'` to `'generic/platform=macOS'` and add a
   notarization step (`xcrun notarytool submit`); set `method` to `developer-id`.
3. Requires a real DEVELOPMENT_TEAM + signing assets — this is a human-run release step, not the build gate.
4. Verify syntax only: `bash -n scripts/archive.sh`.
```

- [ ] **Step 6: `push/project-fragment.yml`** (merge into `targets.<Name>`)

```yaml
# Merge into targets.<Name>:
entitlements:
  properties:
    aps-environment: development
info:
  properties:
    UIBackgroundModes:
      - remote-notification
```

- [ ] **Step 7: `push/registration.swift`**

```swift
import SwiftUI

/// Registers for remote notifications on launch. Attach via @UIApplicationDelegateAdaptor.
final class PushDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        application.registerForRemoteNotifications()
        return true
    }
    func application(_ application: UIApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        // Forward the token to your server / CloudKit subscription.
    }
}
```

- [ ] **Step 8: `push/INSERT.md`**

```markdown
# Insert: Push notifications
1. Copy `registration.swift` → the app source dir. Add `@UIApplicationDelegateAdaptor(PushDelegate.self) var delegate` to the `App` struct.
2. Merge `project-fragment.yml` into `targets.<Name>` — extend the existing `entitlements.properties`
   and `info.properties` maps (do not overwrite a CloudKit entitlements block if present; merge keys).
3. iOS only (no `aps-environment` on macOS without extra setup). Requires a real team to build signed.
4. Verify: `xcodegen generate && xcodebuild build -scheme <Name> -destination 'generic/platform=iOS Simulator'`.
```

- [ ] **Step 9: Validate** — all 7 files exist; `bash -n assets/modules/release/archive.sh` clean; plists/yaml parse. Commit — SKIP if no-commit.

---

## Task 9: End-to-end smoke matrix (the real gate)

**Files:**
- Create: `init-xcode-app/scripts/smoke-xcode.sh`

- [ ] **Step 1: Write the harness**

```bash
#!/usr/bin/env bash
# Scaffolds a throwaway project for one shape and verifies xcodegen + unsigned xcodebuild build.
# Usage: smoke-xcode.sh <ios|macos|ios-watchos>
set -euo pipefail
SHAPE="$1"; SKILL=~/ai_projects/claude-skills/init-xcode-app
NAME="Smoke"; LOWER="smoke"; PREFIX="com.example"; TEAM=""
TMP="$(mktemp -d)"; cd "$TMP"
echo "=== $SHAPE in $TMP ==="
# core common
cp "$SKILL"/assets/core/common/AGENTS.md AGENTS.md
mkdir -p .claude && cp "$SKILL"/assets/core/common/CLAUDE.md .claude/CLAUDE.md
cp "$SKILL"/assets/core/common/gitignore .gitignore
cp "$SKILL"/assets/core/common/swiftformat .swiftformat
cp "$SKILL"/assets/core/common/swiftlint.yml .swiftlint.yml
# shape
cp -R "$SKILL/assets/core/shapes/$SHAPE/." .
# macos reuses ios sources
if [ "$SHAPE" = "macos" ]; then cp -R "$SKILL"/assets/core/shapes/ios/Sources .; cp -R "$SKILL"/assets/core/shapes/ios/Tests .; fi
# substitute placeholders in all text files (rename <Name>* files too)
find . -type f \( -name "*.swift" -o -name "*.yml" -o -name "*.md" -o -name "*.plist" \) -print0 \
  | xargs -0 sed -i '' -e "s/<Name>/$NAME/g" -e "s/<name>/$LOWER/g" -e "s/<bundlePrefix>/$PREFIX/g" -e "s/<TEAM>/$TEAM/g"
# rename files that carried <Name> in their filename
find . -depth -name "*<Name>*" | while read -r f; do mv "$f" "$(echo "$f" | sed "s/<Name>/$NAME/g")"; done
# generate + build
xcodegen generate
if [ "$SHAPE" = "macos" ]; then
  xcodebuild build -scheme "$NAME" -destination 'platform=macOS' CODE_SIGNING_ALLOWED=NO -quiet
else
  xcodebuild build -scheme "$NAME" -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO -quiet
fi
echo "=== PASS: $SHAPE === ($TMP)"
```

- [ ] **Step 2: Run the three no-module shapes**

```bash
bash ~/ai_projects/claude-skills/init-xcode-app/scripts/smoke-xcode.sh ios
bash ~/ai_projects/claude-skills/init-xcode-app/scripts/smoke-xcode.sh macos
bash ~/ai_projects/claude-skills/init-xcode-app/scripts/smoke-xcode.sh ios-watchos
```
Expected: each prints `=== PASS: <shape> ===`. If `xcodebuild` reports "scheme not found", check that
`xcodegen generate` produced `<Name>.xcodeproj` and the scheme name matches `$NAME`.

- [ ] **Step 3: Run iOS + all modules (composition + entitlements merge)**

Manually apply all four modules' INSERT.md to a fresh `ios` smoke dir (the executing agent does the
merges, since composition is agent-driven), then `xcodegen generate && xcodebuild build -scheme Smoke
-destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO`. Expected: build succeeds; the
merged `entitlements.properties` contains BOTH the CloudKit keys and `aps-environment`.

- [ ] **Step 4: Clean up** — `trash` each printed temp dir (per user rule; never `rm`).

- [ ] **Step 5: Commit** — SKIP if no-commit.

---

## Task 10: Publish (optional)

- [ ] **Step 1:** Confirm `SKILL.md` frontmatter valid and description triggers on "scaffold a swiftui app".
- [ ] **Step 2:** `/publish-skill init-xcode-app` (only if the user wants it on the site).
- [ ] **Step 3:** Push (only if the user asks).

---

## Self-Review

**Spec coverage:** §2 XcodeGen+layer → Task 1 procedure. §3 three shapes → Tasks 3 (ios), 4 (macos),
5 (ios-watchos). §4 flow incl. JTBD 1.5 → Task 1 Step 2 + Task 6. §5 core (AGENTS seed, Swift Testing
target, swiftformat/lint, gitignore-commits-xcodeproj, sidecar cross-ref) → Tasks 2-3. §6 four modules
+ entitlements-merge → Tasks 7-8 (CloudKit+Push both extend `entitlements`, called out in their
INSERT.md). §7 signing/unsigned gate by shape → Task 1 Step 4 + Task 9 harness. §8 shared jtbd as
per-skill copy → Task 6. §9 packaging → file structure + Task 1. §10 smoke matrix (3 shapes + ios/all)
→ Task 9. §11 non-goals → respected (no sidecar, no UIKit, no multiplatform-single-target, no pbxproj edits).

**Placeholder scan:** No vague TODOs. `<Name>`/`<name>`/`<bundlePrefix>`/`<TEAM>` are intentional
template tokens, substituted in Task 9 harness and SKILL.md. The cenno-adapt items (Task 5 project.yml,
Task 7 CloudKit stub) cite exact source files + genericization rules — concrete transforms, not gaps.

**Type/name consistency:** `Item`/`Item.samples` consistent across ios sources, ios-watchos Shared,
and both test targets. `SyncService` defined in Task 5 Step 3, used in Steps 4-7. `<Name>Shared` /
`<Name>SharedWatch` module names consistent between project.yml (Task 5 Step 1) and the imports
(Steps 4-8). Scheme name `<Name>` consistent across project.yml, INSERT.md gates, and the smoke
harness. `entitlements` merge (CloudKit Task 7 + Push Task 8) targets the same `targets.<Name>` map.
