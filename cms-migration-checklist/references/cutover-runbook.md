# Cutover runbook skeleton

Copy into the project as `deploy/CUTOVER.md` and fill in hosts, records and times.
Append a timestamped **Cutover log** section on the day.

## Before the day

- [ ] Owner's explicit go-ahead (written).
- [ ] SSH key-only on the new server, verified from a new terminal.
- [ ] Off-server backup target set; `backup.sh` run once; restore drill into a scratch DB.
- [ ] DNS TTL ≤ 120 s on every record you will change. List them; list MX/mail to leave alone.
- [ ] TLS plan: DNS-01 credentials ready (preferred), or a bootstrap HTTP server block.
- [ ] Old CMS stays reachable read-only under an archive hostname (optional).
- [ ] Editors told: freeze from T-0 until T+1 h.
- [ ] Rollback owner: who can repoint DNS.

## T-0 — freeze and final import (~15 min)

1. Editors stop; note the time. Fresh source DB dump + uploads.
2. Did anything change since the last snapshot (posts, pages, comments, attachments)? If not,
   skip to step 3 with the existing data and say so in the log.
3. Otherwise refresh the audit copy, run the idempotent import, reconciliation = 0 mismatches
   including orphans.
4. `pg_dump` (server-major client) → `pg_restore` into a **new** DB on the server; media rsync;
   point the app at it; restart. Previous DB untouched.
5. Crawl through a tunnel: N/N.

## T+15 — go public (~10 min)

6. Certificates for every hostname; install the production proxy config; `nginx -t`; reload.
7. DNS script: dry run → apply (saves old values) → note the time.
8. From outside, including the audience's countries: 200 on home, article, CPT item, author, tag;
   http/www/old subdomains 301 to the canonical origin with path + query; default admin path 404.
9. Crawl the public origin: N/N.
10. Admin smoke test: log in, edit a draft, preview, publish; schedule a publish 2 min ahead.

## Rollback (a step fails and isn't fixed within 30 min)

- DNS script `--rollback` (old values recorded in a TSV next to the runbook).
- Source CMS was frozen, not changed; re-enter any edits made in the new admin after T-0.
- Keep the new server running for diagnosis.

## First week

- Daily error log, scheduled-publish failures, off-server backups.
- Search Console for the canonical host, sitemap resubmitted, analytics live.
- Old CMS read-only for 30 days, then archive; decommission old hosting on approval.
