---
name: app-release
description: "End-to-end pipeline for releasing an iOS / watchOS app to TestFlight and the App Store. Use when the user wants to publish, ship, or release an iOS/watchOS app, get a build onto TestFlight, archive and upload via xcodebuild, deploy a CloudKit schema to Production, set App Privacy or export compliance, mint a Distribution certificate, or work through App Store Connect / Apple Developer portal steps. Triggers on 'continue publishing', 'ship the app to TestFlight', 'release the iOS app', 'upload a build', 'deploy CloudKit to production', 'App Privacy labels', 'distribution signing', or any cryptic Apple upload error (cloud signing, 90057 missing CFBundleShortVersionString, 90474 orientation). macOS and Xcode only."
---

# App Release (iOS / watchOS → TestFlight / App Store)

Drive an iOS/watchOS app from "production path unstarted" to a Distribution-signed
build processing in TestFlight. The hard part is not any single step — it is that
the release path spans three disconnected web portals (Apple Developer, App Store
Connect, CloudKit Dashboard) plus CLI signing arcana, and **each gate hides a silent
failure discoverable only after the previous one passes.** Treat the whole thing as
an airlock checklist: each gate must verifiably seal before the next opens.

## When to use

Releasing/publishing/shipping an iOS or watchOS app; getting a build to TestFlight;
archiving + uploading; deploying CloudKit schema to Production; filling App Privacy
or export compliance; distribution signing; or debugging an Apple upload rejection.

## The gates (run in order; verify each before moving on)

Track every gate in the project's issue tracker. Do **not** assume a gate is closed
because a portal shows green — verify the underlying artifact.

1. **Inventory the gates.** List what is actually open (issue tracker, or derive
   from the steps below). Distinguish gates that block TestFlight from gates that
   block App Store submission — they are different.
2. **CloudKit → Production** (if the app uses CloudKit). Development indexes/record
   types do **not** exist in Production until an explicit *Deploy Schema Changes*.
   Deploy via the dashboard and verify the record type appears in the Production
   environment. **One-way action — confirm with the user first.**
3. **Export compliance.** Bake `ITSAppUsesNonExemptEncryption: false` into **every**
   shippable target (the app *and* the watch app), in the source of truth (e.g.
   XcodeGen `project.yml` info.properties), so TestFlight never prompts per build.
4. **App Privacy.** Audit the code for analytics / third-party SDKs / external
   networking first. If the developer cannot access user data (e.g. data lives only
   in the user's private CloudKit), the honest label is **Data Not Collected**. Set
   it in App Store Connect. Leave **Publish** for submission time.
5. **Privacy Policy + Impressum.** App Store requires a hosted privacy-policy URL;
   an EU/German operator also needs an Impressum. Add pages to the product site,
   deploy, paste the privacy URL into App Store Connect.
6. **Signing audit.** With automatic signing, Xcode mints the Distribution cert +
   App Store profiles at archive/export — no manual portal work. Confirm the team
   id and `CODE_SIGN_STYLE: Automatic`.
7. **Archive.** `xcodebuild archive` the iPhone scheme that *embeds* the Watch app,
   `-allowProvisioningUpdates`. (Archive signs with Apple Development; the
   Distribution cert is minted at the **export** step.)
8. **Export + upload to TestFlight.** `xcodebuild -exportArchive` with method
   `app-store-connect`, automatic signing, and an App Store Connect **API key**.
   The key must be **Admin** role — a Developer-role key cannot cloud-sign and fails
   with "Cloud signing permission error / no iOS Distribution cert found."
9. **Hand off the device test.** The final TestFlight verification (install the
   processed build, exercise the real feature loop on Production) is a **human**
   on-device step. Do not claim it as done.

**Read [references/pipeline.md](references/pipeline.md) for the exact commands,
ExportOptions.plist, and verification one-liners for every gate above.**

**When any step fails with a cryptic Apple error, read
[references/gotchas.md](references/gotchas.md) first** — it catalogs the silent
failures from real releases (corrupted SwiftPM checkout, Developer-role API key,
missing `CFBundleShortVersionString`, iPad-orientation 90474) with the exact fix.

## Guardrails (non-negotiable)

- **Confirm before one-way production actions**: CloudKit *Deploy to Production* and
  App Privacy *Publish*. They affect shipped users / the public product page.
- **Never print secret key values.** Keep `.p8` keys in `~/.appstoreconnect/`; clean
  up any temp copies after use.
- **Use `trash`, never `rm`.**
- **Drive logged-in portals via browser automation; never enter Apple credentials.**
  Ask the user to log in once in the automation browser.
- **Leave the on-device feature-loop test and the final Publish / Submit-for-review
  to the human.**
- **Commit only release-related changes** in focused commits; never sweep unrelated
  branch WIP into a release commit.

## Tooling notes

- Portal work (CloudKit Dashboard, App Store Connect, Apple Developer) is best driven
  through a persistent logged-in browser (e.g. the `browser-mate` skill) so the user
  logs in once and the session persists.
- The heavy build/sign/upload steps belong in the shell (`xcodebuild`), not GUI
  clicking — the CLI gives real error output instead of a progress bar. Reserve
  computer-use/GUI for steps that genuinely need it.
- Run long `xcodebuild` steps in the background and poll for `ARCHIVE SUCCEEDED` /
  `EXPORT SUCCEEDED` / `Upload succeeded` markers.
