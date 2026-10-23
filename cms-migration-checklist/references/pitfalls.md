# Known pitfalls: WordPress → Next.js + Payload

Traps found in a real migration (2026: WordPress 6.9 → Next 16, Payload 3.91,
PostgreSQL 17, nginx 1.24, Ubuntu 24.04). Version-specific items are marked; check them
against current docs before relying on them, because Payload and Next change quickly.

## Audit

| Pitfall | Why it bites | What to do |
|---|---|---|
| Non-ASCII regex/LIKE on a connection without `utf8mb4` | Counts come back wrong without an error; a decision built on one was reversed twice | Set the connection charset; re-verify any count that drives a decision with a second method |
| Custom post statuses from deactivated plugins (e.g. Edit Flow `pitch`) | wp-admin shows no tab and a blank status, so the admin view undercounts | Count `post_status` values straight from `wp_posts` |
| Plugin dropdown fields with a default value (Pods, ACF) | A field filled by default looks like real data (e.g. a translator "credited" on 100 posts) | Compare the field to the body text before importing it as a credit |
| Co-Authors Plus | Order lives in `term_order`; posts with no author term rely on `post_author` | Import both; never merge identities by display name |
| Revisions | Often >90 % of body bytes | Exclude from the working set; keep them in the recovery archive |
| Media filenames in a legacy encoding | `B�hme.jpg` on disk vs `Böhme.jpg` in the DB | Map reversibly; don't rename the originals |
| Generated image sizes | Most are often missing, and they can be regenerated anyway | Import originals only |
| Jetpack CDN (`i0.wp.com/...`) and old-domain URLs in body HTML | They point at hosts you're leaving | Resolve to imported Media; list the ones you can't resolve |
| The current frontend's own bugs | They get copied into the new site if nobody looks | Check every content type is routable, unknown slugs answer 404, and API calls don't 401 or 500 |

## Content conversion (Payload Lexical; checked on Payload 3.91)

| Pitfall | Why it bites | What to do |
|---|---|---|
| `convertHTMLToLexical` drops plain `<img>` | Images disappear without an error | Create Media docs first and emit upload nodes; turn unresolved images into links and report them |
| Lexical link validation | One bad href (whitespace, or `<a>` without href) rejects the whole document, and its comments fail too | Trim and `%20`-encode hrefs; unwrap empty links |
| Bare video URLs on their own line (WordPress auto-embeds them) | They become plain text | Convert them to an embed block |
| Word footnotes (`#_ftnN` anchors) | Anchors and their targets get separated | Preserve both ids; check the footnote count before and after |
| Custom admin components | A stale import map breaks the admin | Regenerate the Payload import map; add a test that it's up to date |

## Import

| Pitfall | Why it bites | What to do |
|---|---|---|
| The Local API bypasses access control by default | Fine for the importer, a leak if public reads use it the same way | Pass `overrideAccess: false` (and the user) on public reads |
| Import hooks | Imports can publish drafts, send email or queue schedules | Disable side effects during import; map statuses explicitly |
| Delegated or agent-written importer changes | One change published unpublished posts and reset their original dates | Test "nothing unpublished becomes public" and "dates unchanged" |

## Public site

| Pitfall | Why it bites | What to do |
|---|---|---|
| Trailing slashes | WordPress URLs end in `/`; Next defaults differ, so every old link redirects | Serve slashed URLs, emit slashed internal links, redirect in one place (middleware or proxy), never touching `/api` or the admin path |
| Absolute redirect `Location` built behind a proxy | Readers get sent to `http://localhost:3000/...` | Use a relative `Location` |
| `og:image` / `metadataBase` | Share previews point at localhost, so Telegram, Facebook etc. show no image | Set the base to the canonical origin; check the rendered HTML in production |
| Starter-template leftovers | Template favicon, share image and titles ship to production | Add a test that the brand assets are in place |
| Archive canonicals | Tag/category pages pointing their canonical at the home page | Add a canonicals test and crawl |
| Missing media file | Gives a 500 instead of a 404 | Handle it explicitly |
| Long articles at phone width | Horizontal scroll from tables, embeds and long URLs | Test at 375 px |

## Admin and editorial (checked on Payload 3.91 / Next 16)

| Pitfall | Why it bites | What to do |
|---|---|---|
| Payload crons don't start on their own | Scheduled posts never publish until something calls `getPayload({ cron: true })` | Boot it in `instrumentation.ts`; run one mode only (in-process or system cron) |
| Scheduled job fails | The post silently stays a draft | Retry with backoff and alert after the last attempt |
| A `'use server'` module with a non-async export | The build fails | Export only async functions (add a test) |
| Comment rate limit by IP | Spoofable if the proxy *appends* to `X-Forwarded-For` | nginx: `proxy_set_header X-Forwarded-For $remote_addr;` |
| Password-reset link | Points at the internal host | Build it from the public origin |
| Draft mode | A draft-mode cookie without a session might reveal drafts | Probe it against a production build |

## Deploy and cutover

| Pitfall | Why it bites | What to do |
|---|---|---|
| Native modules (sharp) built on a different OS | The app crashes on the server | Build on the server |
| A per-user pnpm install | Fails silently under systemd | System-wide `corepack enable` |
| Read-only release dirs | Next's cache can't write | Make releases writable by the app user |
| `pg_dump` older than the server | The dump is refused | Use the client matching the server's major version |
| `http2 on;` on nginx < 1.25.1 | `nginx -t` fails | `listen 443 ssl http2;` |
| TLS before DNS points at the new host | HTTP-01 can't succeed yet | DNS-01 challenge, or a bootstrap HTTP block and a short certificate gap |
| DNS edits by hand | Risk of touching MX, and no record of the old values | A script with dry-run / apply / rollback that saves the old values |
| Off-server backups | The item most often still open after go-live | Make it a gate, not a follow-up |
