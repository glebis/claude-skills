# Release pipeline — exact commands

Concrete, copy-adaptable commands for each gate. Replace placeholders:
`<TEAM>` (Developer team id), `<CONTAINER>` (e.g. `iCloud.app.example`),
`<SCHEME>` (the iPhone scheme that embeds the watch app), `<APP_ID>` (App Store
Connect numeric app id), `<KEYID>` / `<ISSUER>` (App Store Connect API key).

Assumes an **XcodeGen** project (`project.yml` is the source of truth — editing the
generated `.plist`/`.xcodeproj` directly gets overwritten by `xcodegen generate`).
For a hand-managed `.xcodeproj`, edit the targets' Info.plist/build settings directly.

---

## Gate 1 — Inventory

Find the open release gates. With a beads tracker: `bd ready`, `bd show <epic>`.
Otherwise walk gates 2–9 below and note which artifacts are missing.

## Gate 2 — CloudKit schema → Production

Drive the CloudKit Dashboard in the logged-in browser:
`https://icloud.developer.apple.com/dashboard/` → container → **Database**.

1. Confirm the record type(s) + indexes exist in **Development**
   (`…/environments/DEVELOPMENT/types` and `…/indexes`).
2. Check **Production** is missing them (`…/environments/PRODUCTION/types`) — the
   "New Record Type" button is disabled in Production; schema is *promoted*, not edited.
3. **Menu → Deploy Schema Changes…** → review the diff (record types / indexes /
   security roles — all additive for a first deploy) → **confirm with the user** →
   **Deploy**.
4. Verify: the record type now lists under the Production environment.

Notes: the relay/feature data zone in a *private* database is created at runtime
per-user; what gets deployed is the **record type + its field indexes** (e.g.
`state`/`expires_at` QUERYABLE, `created_at` SORTABLE). Indexes auto-create in
Development on the first successful save; they reach Production only via this deploy.

## Gate 3 — Export compliance (per target)

In `project.yml`, add to **each** shippable target's `info.properties`:

```yaml
ITSAppUsesNonExemptEncryption: false
```

The watch target is easy to miss — without it TestFlight prompts for compliance on
the watch app. Then `xcodegen generate` and verify:

```bash
/usr/libexec/PlistBuddy -c "Print :ITSAppUsesNonExemptEncryption" path/to/Watch/Info.plist
```

## Gate 4 — App Privacy (App Store Connect)

First audit the codebase — only declare "not collected" if it is true:

```bash
grep -rniE "analytics|firebase|sentry|amplitude|mixpanel|crashlytics|posthog|telemetry|facebook|google" Sources/
grep -rniE "URLSession|http(s)?://|api\." Sources/      # external networking beyond CloudKit/APNs
# also check Package.swift / project.yml for third-party SDK dependencies
```

If there is no analytics, no third-party SDK, and user content lives only in the
user's **private** CloudKit DB (developer cannot access it), the correct nutrition
label is **Data Not Collected** (Apple's rule: CloudKit data you can't access is not
"collected").

In App Store Connect → app → **App Privacy**: *Get Started* → Data Collection →
"No, we do not collect data from this app" → Save. **Do not click Publish** — that is
gated to submission; leave it for the user.

## Gate 5 — Privacy Policy + Impressum

App Store requires a hosted privacy-policy URL before publishing; an EU/German
operator also needs an Impressum (§ 5 DDG/TMG). If the product site exists (e.g. an
Astro app), add routes:

- `/privacy` — reflect reality (no collection, private-CloudKit-only, APNs for delivery).
- `/impressum` — operator name, address, contact, EU ODR clause. Reuse the operator's
  existing Impressum text (fetch with WebFetch; do not invent legal text).

**Do not publish internal docs.** If the repo's `docs/` holds internal material,
enabling GitHub Pages on it leaks them — prefer the existing product site or an
isolated branch. Build, deploy (e.g. `vercel --prod` from the site dir), verify both
pages return 200, then paste the privacy URL into App Store Connect → App Privacy →
Privacy Policy → Edit → Save.

## Gate 6 — Signing audit

```bash
grep -nE "CODE_SIGN_STYLE|DEVELOPMENT_TEAM" project.yml      # expect Automatic + <TEAM>
# certs present? (Developer portal → Certificates) — for App Store you need
# "Apple Distribution"; with Automatic signing it is minted at export, not manually.
xcodebuild -list -project <Project>.xcodeproj                 # find the embedding scheme
```

With `CODE_SIGN_STYLE: Automatic`, no manual cert/profile creation is needed — they
mint during archive/export with `-allowProvisioningUpdates`.

## Gate 7 — Archive

```bash
cd <project-dir-with-xcodeproj>
[ -e build/App.xcarchive ] && trash build/App.xcarchive
xcodebuild archive \
  -project <Project>.xcodeproj \
  -scheme <SCHEME> \
  -configuration Release \
  -destination 'generic/platform=iOS' \
  -archivePath build/App.xcarchive \
  -allowProvisioningUpdates \
  DEVELOPMENT_TEAM=<TEAM>
```

Run in the background; success marker: `** ARCHIVE SUCCEEDED **`. The archive signs
with **Apple Development** — the Distribution cert is minted at export. Verify
embedded-framework versions before exporting (see gotchas: 90057):

```bash
A=build/App.xcarchive/Products/Applications/App.app
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$A/Frameworks/<Fw>.framework/Info.plist"
```

## Gate 8 — Export + upload to TestFlight

App Store Connect **API key** (Users and Access → Integrations → App Store Connect
API). Need **Admin** role (Developer cannot cloud-sign). Issuer ID is on that page;
key id is in the `.p8` filename `AuthKey_<KEYID>.p8`. Store at `~/.appstoreconnect/`.

`build/ExportOptions.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>method</key><string>app-store-connect</string>
  <key>teamID</key><string>&lt;TEAM&gt;</string>
  <key>destination</key><string>upload</string>
  <key>signingStyle</key><string>automatic</string>
  <key>uploadSymbols</key><true/>
  <key>manageAppVersionAndBuildNumber</key><true/>
</dict>
</plist>
```

```bash
xcodebuild -exportArchive \
  -archivePath build/App.xcarchive \
  -exportOptionsPlist build/ExportOptions.plist \
  -exportPath build/export \
  -allowProvisioningUpdates \
  -authenticationKeyPath ~/.appstoreconnect/AuthKey_<KEYID>.p8 \
  -authenticationKeyID <KEYID> \
  -authenticationKeyIssuerID <ISSUER>
```

Background; success markers: `Upload succeeded` then `** EXPORT SUCCEEDED **`.
`destination: upload` mints the Distribution cert + App Store profiles via cloud
signing and uploads in one step. The build then **processes** in App Store Connect
(~10–30 min) before appearing in TestFlight. Because export compliance is baked into
the build (Gate 3), it skips the "Missing Compliance" prompt.

## Gate 9 — Device test (human)

Once processing completes, the user installs via TestFlight on a device signed into
the **same iCloud account** as any Production CloudKit writer, exercises the real
feature loop, and confirms it works against Production. Do not mark done on the user's
behalf — note it as the remaining gate before *Submit for Review*.

## Wrap-up

- Commit only release-related changes (`project.yml`, generated Info.plist, site
  pages) in focused commits; push.
- Record the build version/number and the Admin API key id (not the value) in the
  tracker/memory. Clean up temp `.p8` copies.
