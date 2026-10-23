# Setup mode: migration intake

Use this at the start of a migration, when the user asks to set one up, or when the
project has no migration evidence yet. The goal is a short brief that decides which
phases matter, which checklist items are n/a, and which decisions can already go in the
packet, so the later phases don't start from guesses.

Ask with the `AskUserQuestion` tool: **at most 10 questions in total**, in up to three
rounds of no more than 4. If that tool isn't available, ask the same questions in
plain text, one round at a time. Put the recommended option first. Skip any question
the evidence already answers, and say what you inferred instead of asking.

Tool format: each question needs a short `header` chip (≤12 characters, e.g. "Old site",
"Scope", "URLs", "Body", "Editorial", "Plugins", "Hosting", "Audience", "Freeze",
"Approver"), 2–4 options with a 1–5 word label and a one-line description (given below
as label — "description"), and `multiSelect: true` where marked. The user can always
pick "Other", so don't add one.

## Round 1: the old site (ask first, then look before asking more)

1. **What do you have for the old site?** (multi-select)
   - Live URL — "The public site address"
   - Theme / frontend code — "A repo or folder with the theme or a headless frontend"
   - Database dump + uploads — "An export of the WordPress database and wp-content/uploads"
   - Server access — "SSH or hosting panel for the WordPress server"

   Then ask for the URL and/or path in plain text (or read them from the message if the
   user already gave them).

**Look before round 2.** With a URL, read only public endpoints (no logins, no load):
- `/wp-json/` → namespaces (shows plugins: `yoast`, `acf`, `coauthors`, `wc`…),
  custom endpoints, site name and timezone.
- `/wp-json/wp/v2/posts?per_page=1` (and `pages`, `categories`, `tags`, `users`) → the
  `X-WP-Total` header gives the counts.
- `/wp-json/wp/v2/types` → custom post types.
- `/sitemap.xml` or `/wp-sitemap.xml`, `/feed/`, `<meta name="generator">`, permalink
  shape from a few post URLs.

With code: `package.json` (an existing Next.js frontend?), `lib/` API clients, theme
`functions.php`, `composer.json`, `next.config` redirects. With a dump: table prefixes and
plugin tables (Phase 0a starts here anyway).

Summarize what you found in 3–5 lines before round 2, and drop questions it answers.

## Round 2: what the migration should achieve

2. **How much should change?**
   - Move as is (Recommended) — "Same content, URLs and look; only the CMS and hosting change"
   - Move, then refresh — "Migrate as is first, redesign after go-live"
   - Refresh during the move — "New design and templates, same content and URLs"
   - Rebuild — "New content model or site structure; URLs may change"

   If they pick one of the last two, say plainly that it mixes two risks in one cutover
   (see Ground rules) and record their answer anyway; it's their call.

3. **What must happen to existing URLs?**
   - Keep every URL (Recommended) — "Same paths, trailing slashes included"
   - Keep content URLs, archives may change — "Posts and pages keep paths; tags/dates may redirect"
   - New structure with 301s — "A full redirect map from old to new"

4. **How should article bodies be stored?**
   - Convert to Lexical (Recommended) — "Everything editable in Payload's editor; keep sanitized HTML as the source"
   - Keep legacy HTML read-only — "Old articles stay HTML; new ones use Lexical"
   - Decide after fixtures — "Convert 10–20 hard articles first and look at the losses"

5. **Which editorial features are needed on day one?** (multi-select)
   - Drafts and preview — "Edit without publishing, preview the result"
   - Scheduled publishing — "Publish or unpublish at a set time"
   - Comments — "Readers comment; editors moderate"
   - Roles and stages — "Several roles or workflow stages beyond draft/published"

## Round 3: content and operations

6. **Which of these does the site rely on?** (multi-select; pre-select what discovery found)
   - Custom fields — "ACF, Pods, Meta Box, or custom post types"
   - Several authors per post — "Co-Authors Plus, guest authors, translator or photo credits"
   - SEO plugin data — "Yoast / Rank Math titles, descriptions, redirects"
   - Shop, membership or forms — "WooCommerce, paywalls, donations, form entries"

   A shop, memberships or stored form entries are a bigger project (orders, payments,
   personal data). Flag that they're outside this checklist and need their own plan.

7. **Where will the new site run?**
   - Single VPS (Recommended) — "Next, Payload, Postgres and media on one server; fits small teams"
   - Managed platform — "e.g. Vercel + managed Postgres + S3-compatible storage"
   - Existing infrastructure — "Company servers or Kubernetes"
   - Not decided — "Choose after measuring staging"

8. **Who reads the site, and from where?** Free text if needed; options:
   - One country or region — "Measure reachability from there before choosing a host"
   - Global — "A CDN matters more than the server's location"
   - Includes regions that block some clouds — "Test candidate hosts from those networks first"

9. **How long can editors stop publishing at cutover?**
   - An hour or two (Recommended) — "Freeze, final import, switch DNS"
   - A day or more — "Easiest; no rush on cutover day"
   - No freeze possible — "Needs a final delta import and a tightly rehearsed cutover"

10. **Who approves decisions and the cutover?**
    - Me — "I decide; ask me directly"
    - Someone else — "Collect decisions in a packet for them"
    - A team — "Decisions go through a review"

Stop at 10. Anything else goes into the decision packet in Phase 0a.

## Output: `MIGRATION-BRIEF.md`

Write it in the project root (create the project folder if there isn't one):

```markdown
# Migration brief: <site>

Date · Source: <URL / code path / dump> · Approver: <who>

## What we know about the old site
<discovery summary: WP version if known, counts per type, custom post types,
plugins with data, permalink shape, existing frontend, sitemap/feeds>

## Goals
Scope: <move as is / …> · URLs: <…> · Body format: <…> · Hosting: <…> · Audience: <…>
Day-one editorial features: <…> · Cutover freeze: <…>

## Already decided (copy into the decision packet)
D1 hosting: … · D… body format: … (with "from intake, <date>")

## Checklist adjustments
- n/a: <items, with reasons — e.g. comments: none on the site>
- Extra weight: <e.g. multi-author → audit authors early; regions → reachability first>
- Out of scope: <shop/memberships, with the follow-up it needs>

## Next step
<usually Phase 0: backups and source evidence; list what access is still missing>
```

Then offer to copy the phases into `MIGRATION-CHECKLIST.md` (or tracker epics) with the
n/a items already marked.
