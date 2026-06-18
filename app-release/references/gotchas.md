# Gotchas — silent failures and their fixes

Each entry is a real failure mode that blocks a release gate with a misleading or
cryptic symptom. Match the symptom, apply the fix. Ordered by where they bite in the
pipeline.

---

## G1 — "Cloud signing permission error / No signing certificate 'iOS Distribution' found"

**When:** `xcodebuild -exportArchive` (Gate 8), even though archive succeeded and
`-allowProvisioningUpdates` is set.

**Cause:** The App Store Connect **API key role is too low.** A *Developer*-role key
cannot create signing assets via cloud signing; it needs **Admin** (App Manager also
cannot manage certificates). And no Distribution cert exists yet, so there is nothing
to fall back to.

**Fix:** Create a new **Admin** API key — App Store Connect → Users and Access →
Integrations → App Store Connect API → **+** (Generate) → name it, select **Admin** →
Generate → **Download** the `.p8` (one-time). Move to `~/.appstoreconnect/`, re-run
export with the new `-authenticationKeyID` (same Issuer ID). API keys cannot be
upgraded after creation — you must make a new one. Note the key id (not the value) for
the user; it is revocable later.

## G2 — SwiftPM "public headers (include) directory path for '_FoundationICU' is invalid" / "Could not resolve package dependencies"

**When:** `xcodebuild archive` fails at *Resolve Package Graph*. Common right after a
fresh `xcodegen generate`, which resets the package graph and forces a re-resolve.

**Cause:** A corrupted SourcePackages checkout — the dependency drifted to the wrong
ref (e.g. `swift-foundation-icu` sitting on `main` instead of the pinned tag), so the
expected source layout / `include` dir is missing.

**Diagnose:**

```bash
DD=~/Library/Developer/Xcode/DerivedData/<Project>-*/SourcePackages/checkouts/<dep>
git -C "$DD" status; git -C "$DD" log --oneline -1     # wrong branch? dirty tree?
git ls-remote --tags <dep-url> | grep <pinned-tag>     # confirm the pin exists
```

**Fix:** Wipe the project's SourcePackages cache and re-resolve cleanly (it re-checks
out the pinned revision):

```bash
trash ~/Library/Developer/Xcode/DerivedData/<Project>-*/SourcePackages
xcodebuild -resolvePackageDependencies -project <Project>.xcodeproj -scheme <SCHEME>
# verify the include/source dir now exists in the checkout
```

## G3 — Upload reject 90057: framework "missing the required key: CFBundleShortVersionString"

**When:** `-exportArchive` validation, naming an embedded `.framework`.

**Cause:** Framework targets using `GENERATE_INFOPLIST_FILE: YES` read
`MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` **build settings** for their generated
Info.plist. If those settings are unset, the version keys come out empty/missing. (App
*targets* with an explicit Info.plist often default to 1.0/1, so only the frameworks
break — easy to miss.)

**Fix:** Set both at the project level so every target inherits them:

```yaml
# project.yml → settings (base, applies to all targets)
settings:
  MARKETING_VERSION: "1.0"
  CURRENT_PROJECT_VERSION: "1"
```

`xcodegen generate`, re-archive, verify each framework's Info.plist now has a version.

## G4 — Upload reject 90474: "orientations … you need to include all four … to support iPad multitasking"

**When:** `-exportArchive` validation, naming the iPhone app bundle, when it declares
3 orientations (no `PortraitUpsideDown`).

**Cause:** The app defaults to **universal** (iPhone + iPad). iPad multitasking
requires all four orientations.

**Fix (preferred for a phone+watch companion):** make it iPhone-only — the iPad rule
no longer applies:

```yaml
# project.yml → the iPhone app target → settings.base
TARGETED_DEVICE_FAMILY: "1"
```

Do **not** put this at the project base — it would break the watchOS target. Set it on
the iPhone app target only. (Alternatives: add `UIInterfaceOrientationPortraitUpsideDown`,
or set `UIRequiresFullScreen`. Upside-down on a notched iPhone is usually undesirable.)

## G5 — Archive must use the embedding scheme

The iPhone scheme must **embed** the watch app (and shared frameworks) so one archive
contains the whole product. Confirm in `project.yml` the iPhone target lists the watch
target as a dependency with `embed: true`. Archiving a bare framework or the watch
target alone will not produce an App Store-uploadable bundle.

## G6 — Firecrawl/scrape key rejected when fetching your own legal text

**When:** Pulling the operator's existing Impressum to reuse (Gate 5) and the scrape
API returns 401.

**Fix:** Use `WebFetch` (or the already-open logged-in browser's page snapshot) for
the operator's own page. Some pages are client-rendered and 404 to a plain fetch — in
that case read the rendered DOM via the browser session. Never invent legal text.

## G7 — Hardcoded environment log lines lie

A writer's `OK wrote … (Development)` style log string may be **hardcoded text**, not a
real environment readout. Verify the CloudKit environment from signed entitlements /
the actual dashboard, not from a log line.

## G8 — TestFlight UI lags the upload

`xcodebuild` reporting `Upload succeeded` is authoritative. The build then processes
for ~10–30 min before surfacing in the TestFlight tab — a blank/empty TestFlight page
right after upload is normal, not a failure. Do not re-upload; wait or poll.
