---
name: cms-migration-checklist
description: Gated checklist and working method for migrating a WordPress site to Next.js with a Payload CMS admin — audit, owner decisions, HTML→Lexical conversion, idempotent import and reconciliation, URL/SEO parity, editorial admin, security probes, self-hosted deploy, DNS cutover, rollback and the first week after. Use this whenever someone is planning, building, reviewing or launching a WordPress → Payload (or WordPress → headless Next.js) migration, even if they only ask one slice of it. Includes a setup mode that interviews the user about the old site and goals and writes a migration brief — "set up a migration for example.com", "are we ready to cut over?", "how do I know the import didn't lose anything?", "what should I audit in the WP database first?", "replace wp-admin with Payload", "move off WordPress", "migration plan for our blog", "will old URLs still work?".
---

# WordPress → Next.js + Payload migration checklist

A migration is done when **every source record has an accounted outcome, every public URL
still answers, editors can publish without WordPress, and you can roll back**. A site that
merely looks right can still be missing records, URLs or editorial flows, which is why the
checklist is split into phases that each end in a gate with evidence.

## How to work with this skill

Don't paste the whole checklist back at the user. Instead:

0. **Setup mode for a new migration.** If the user wants to start or set up a migration,
   or the project has no migration evidence yet, run the intake in `references/setup.md`:
   at most 10 questions via `AskUserQuestion` (the old site's URL or code, how much should
   change, URLs, body format, editorial features, plugins, hosting, audience, freeze,
   approver), a read-only look at the old site between rounds, and a `MIGRATION-BRIEF.md`
   that marks n/a items and pre-fills the decision packet.
1. **Find out where the project is.** Look for evidence before asking: an audit folder or
   reports (inventory, field matrix, URL manifest), a Payload config and collections, an
   import ledger or reconciliation report, a crawl report, deploy scripts, a cutover
   runbook. Map what you find to a phase below. If there's no repo yet, start at Phase 0.
2. **Check the current phase and the gate before it.** Mark each item **done** (with its
   evidence: a file, a test name, a commit, a command output), **missing**, or
   **n/a** (with the reason: e.g. the site has no comments). An item without evidence is
   missing, however likely it seems.
3. **Report the gaps first**, ordered by what blocks the next gate, then what's done.
   Offer to fix or write the missing pieces (tests, scripts, reports).
4. For a fresh project, help the user copy the phases into the repo as
   `MIGRATION-CHECKLIST.md` or as tracker epics whose acceptance criteria are the
   checklist lines, so the evidence accumulates where the work happens.

Read `references/pitfalls.md` before the audit, conversion, import and deploy phases: it
lists concrete traps with fixes. Read `references/cutover-runbook.md` when planning the
cutover. Several pitfalls are tied to specific Payload/Next/nginx versions; confirm them
against current docs when the project uses different versions.

## Ground rules

- **Production stays read-only until cutover.** Audit a restored local copy through a
  query guard that only allows `SELECT/SHOW/DESCRIBE/WITH/EXPLAIN`. Mistakes on a copy are
  free; on production they're incidents.
- **No silent loss.** Every table, field, status and comment class gets a disposition:
  preserve, transform, retire with a reason, or unresolved. Unresolved blocks the gate,
  because "we'll decide later" usually means "we dropped it".
- **Keep hosting, CMS and redesign apart.** Each changes risk independently; bundling
  them makes failures impossible to attribute.
- **The owner decides; you recommend.** Collect decisions in a numbered packet (D1…Dn)
  with evidence, options and a recommendation, and record the answers and dates in the
  repo. Re-open a decision when its evidence changes.
- **Test first.** A failing test, then the fix, per task. Migrations regress quietly, and
  tests are what keep fixed traps fixed across re-imports.
- **Re-verify every number that drives a decision**, with a second query or method.

## Phase 0: Backups and source evidence

- [ ] Full DB dump (with revisions) and a revision-free copy, both restored locally, with
      counts per post type × status identical to production; sha256 manifests stored.
      Revisions are usually most of the bytes and none of the migration.
- [ ] Note table engines: MyISAM isn't transactional, so a consistent dump needs a read
      lock the owner has approved, or a quiet window.
- [ ] Uploads archive with a per-file manifest (path, size, sha256), extracted and
      verified. Leave out backup-plugin folders on purpose, and say so.
- [ ] DB and media timestamps recorded (they're rarely captured together; expect drift).
- [ ] Plugin and theme source copied read-only; the real WordPress version taken from
      `db_version`, not assumed.
- [ ] Server access by SSH key, checked from a new terminal before the old one closes;
      no passwords stored in notes or the repo.

## Phase 0a: Audit (what exists, not what the frontend shows)

- [ ] **DB inventory:** tables by owning plugin, row counts, post types × statuses,
      including statuses left by deactivated plugins (invisible in wp-admin).
- [ ] **Active vs installed plugins:** inactive plugins still own data (comments,
      avatars, donations, views), and each needs a decision.
- [ ] **Field matrix:** every meta key / ACF / Pods field → label, type, cardinality,
      populated count, owning plugin, target field, transform, disposition.
- [ ] **Admin screen map:** screenshots of every edit screen (posts, pages, custom post
      types, media, users, terms); each control → storage → target. Flag *unmapped*
      (a control with no data) and *hidden* (data with no control). Note classic vs block
      editor per screen.
- [ ] **Authors and credits:** co-author storage and order, guest authors, the fallback to
      `post_author`; extra roles (translator, photographer) checked against body text.
      Public author profiles are not login users, and password hashes don't migrate.
- [ ] **API contracts:** custom REST endpoints the current frontend uses (routes,
      permission callbacks, response shapes). The new content layer must reproduce them
      while both run.
- [ ] **URL manifest:** every public URL by kind: posts, pages (with hierarchy), custom
      post types, categories, tags, authors, **plus** pagination (`/page/N/`), feeds
      (`/feed/`, per-category feeds), date archives, attachment pages and search. Note slug
      collisions across types and existing redirects (Redirection plugin,
      `_wp_old_slug`, framework config), and check that redirect targets exist.
- [ ] **Media reconciliation:** attachments vs files (missing, orphans, no metadata),
      size variants, inline URLs to the old domain or a CDN, images hot-linked from other
      sites.
- [ ] **Bugs in the current site** recorded in the tracker, so they aren't rebuilt.
- [ ] **Fixtures:** 10–20 real, difficult records (multiple authors, footnotes,
      captions, embeds, tables, long text, odd encodings, slug collisions), with a
      manifest of checks a machine can run on each.
- [ ] **Decision packet** drafted with the questions below.

**Decisions the packet usually needs:** hosting · author profiles vs logins · byline
order and fallback · extra credit roles · comments (native, read-only archive, third
party, or dropped; approved only; spam and unmoderated stay in the source archive; close
on old posts?) · donations or other personal data (usually not imported) · editorial
workflow (drafts, stages, scheduled publishing) · fields to retire · analytics and Search
Console · body format (convert to Lexical, or keep legacy HTML) · admin URL and language.

**Gate 0:** field matrix, screen map and author mapping reviewed; decision packet answered.

## Phase 1: Payload proof on fixtures

- [ ] Next, React and Node versions that the chosen Payload release supports, pinned
      exactly, with one lockfile. Upgrade the runtime in its own commit before adding
      Payload, so a breakage points at one change.
- [ ] Collections modelled from the field matrix, not from the old frontend's types.
- [ ] Fixtures import; every manifest check passes or is listed as lossy.
- [ ] Editor flow: edit → save draft → preview → publish → edit again → restore an earlier
      version. The public page shows the last *published* version throughout; anonymous
      visitors never see drafts.
- [ ] Two editors on one document: document locking behaves as expected.
- [ ] Opening and saving an imported document doesn't change its stored source.
- [ ] Author pages list exactly the fixtures credited to each profile.
- [ ] The owner has walked through the admin (screenshots or a live session).

**Gate 1:** the owner accepts the editor workflow; unsupported features are listed with
how each will be handled.

## Phase 2: Content conversion (HTML → Lexical)

- [ ] Sanitized legacy HTML kept unchanged next to the converted body, with a
      `conversionStatus` (clean / lossy). Lossy documents go to a manual review list.
- [ ] Per-document checks, legacy vs converted: headings, images, images with empty alt,
      footnotes, captions, embeds, links, blockquotes, list items, tables.
- [ ] Images resolved to Media docs before conversion (Payload drops plain `<img>`).
- [ ] Links normalized so Lexical validation accepts them; embeds and footnotes kept
      (see pitfalls).
- [ ] Shortcodes and plugin markup converted or reported.

## Phase 3: Full import and reconciliation

- [ ] An importer that is **idempotent and resumable**, with a ledger per run and per
      record (created / updated / unchanged / kept-admin-edit / skipped / failed). A second
      run straight after reports 0 created and 0 updated; that's what makes the final
      import at cutover safe and fast.
- [ ] Nothing that wasn't published in WordPress becomes public; original dates and the
      site timezone kept; drafts and custom statuses mapped explicitly.
- [ ] Import side effects off: no emails, notifications, schedules or search pings.
- [ ] Public reads enforce access control (the Local API bypasses it by default).
- [ ] Reconciliation report: source vs target per type × status, 0 mismatches,
      **including orphans** (target rows with no source).
- [ ] Preflight that stops with one clear error when the source DB is unreachable.
- [ ] Run time, peak memory, DB size and media size recorded; they size the server.

**Gate 3:** reconciliation clean, lossy list reviewed, full URL crawl passes locally.

## Phase 4: Public site parity

- [ ] Public pages read Payload only. A content-source switch makes any accidental
      WordPress fetch fail loudly instead of quietly serving stale data.
- [ ] URLs keep WordPress's shape, trailing slashes included; one place handles
      redirects and leaves `/api` and the admin path alone.
- [ ] **Crawl of the whole URL manifest: N/N return 200**, with latency recorded.
- [ ] Real 404s for unknown slugs and pages past the last listing page (soft 404s hurt
      SEO).
- [ ] Old `/wp-content/uploads/...` URLs 301 to the imported files (relative
      `Location`); a missing file returns 404, not 500.
- [ ] Feeds exist where WordPress had them, or redirect deliberately.
- [ ] Search works and covers the imported content.
- [ ] One canonical origin in config; sitemap, canonical tags, robots and OpenGraph URLs
      derive from it. Archive canonicals point at themselves.
- [ ] `og:image` is an absolute URL on the production host (checked in rendered HTML);
      favicon, share images and titles from the starter template replaced.
- [ ] Every content type is reachable (custom post types need routes and listings).
- [ ] Author index and author pages from the new data; byline order and links.
- [ ] Phone width: no horizontal scroll on long articles; tap targets, contrast, `lang`,
      main landmark, visible focus.
- [ ] Comments, if kept: threaded view, a notice when closed, nothing rendered when
      closed and empty.

## Phase 5: Admin and editorial operations

- [ ] Admin at a non-default path (the default returns 404), defined in one module.
- [ ] Admin in the editors' language: default locale, collection and field labels,
      options, help texts; types regenerated afterwards. Short guides for editors and
      admins.
- [ ] Logins only for people who edit; how author names are displayed, with an override
      per profile.
- [ ] Excerpts, bios, featured images and SEO fields editable.
- [ ] Media can't be deleted while documents still reference it.
- [ ] Scheduled publishing (if decided): durable jobs, cron started at boot, one runner,
      the editors' timezone as default, overdue jobs run as soon as possible, retries
      with an alert after the last failure.
- [ ] Comments (if kept): moderation queue, spam guard, per-IP rate limit with the proxy
      overwriting `X-Forwarded-For`.
- [ ] Email configured; password-reset links use the public origin.
- [ ] Probes against a **production build**: no draft leaks, upload pipeline
      (validation, image processing, write, delete), scheduled publish end to end.

## Phase 6: Hosting and staging

- [ ] Reachability measured from where the audience is (some regions block or throttle
      certain clouds and CDNs) before the host is chosen.
- [ ] Repeatable deploy: build on the server (native modules), health check,
      automatic rollback, several releases kept, `payload migrate` run in the deploy.
- [ ] Process manager with memory limits; firewall open only for SSH, HTTP, HTTPS.
- [ ] Staging is access-restricted **and** `noindex`, so search engines don't index a
      duplicate of the site.
- [ ] Staging crawl N/N.
- [ ] Restore drill: the backup restored into a new database, the app started on it,
      crawl N/N. Use `pg_dump` matching the server's major version.
- [ ] Nightly DB and media backups landing **off the server**, and checked.

**Gate 6:** staging crawl N/N, restore drill passed, off-server backups landing.

## Phase 7: Cutover

Follow `references/cutover-runbook.md`. In short:

- [ ] Owner's written go-ahead; editors told about the freeze.
- [ ] Freeze, then check whether WordPress changed since the last snapshot; if it did,
      run the final import and reconcile.
- [ ] Data restored into a **new** database; the previous one kept for rollback.
- [ ] TLS planned for before DNS points at the new host.
- [ ] DNS changed by script (dry run, apply, old values saved, rollback) and only the
      records intended; mail records untouched.
- [ ] From outside, including the audience's regions: key pages 200; `http`, `www` and
      old hostnames 301 to the canonical origin, keeping path and query.
- [ ] Public crawl N/N; admin smoke test including a publish scheduled two minutes ahead.
- [ ] Rollback trigger defined, and any edits made after the freeze listed.

## Phase 8: First week and decommissioning

- [ ] Daily: application errors, failed scheduled jobs, off-server backups.
- [ ] Search Console verified for the canonical host, sitemap submitted; analytics
      recording.
- [ ] Social preview caches refreshed for the main pages.
- [ ] WordPress kept read-only (and backed up) for an agreed period, then archived; old
      hosting shut down only with the owner's approval.
