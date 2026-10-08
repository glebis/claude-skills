# OKF v0.2 writing profile

Authoritative source: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md (checked 2026-10-08, version 0.2). Recheck before changing the target version. This summary is an implementation profile, not the specification.

A bundle contains UTF-8 Markdown. Every non-reserved `.md` document needs parseable YAML frontmatter with a non-empty string `type`. Unknown types and producer fields are allowed. `index.md` lists contents; only the root index may have `okf_version` frontmatter. `log.md` uses ISO-date headings and has no frontmatter. Keep plugin state, templates without complete frontmatter, and tool instructions outside the declared bundle, or make documents conformant rather than silently excluding them from an audit.

Minimal document:

```yaml
---
type: Concept
title: Source and interpretation
description: Preserve original material while making derived knowledge inspectable.
status: draft
sources:
  - id: talk-1
    resource: ../sources/talk-1.md
    title: Talk transcript
generated:
  by: open-knowledge-vault/0.1.0
  at: '2026-10-08T10:00:00+02:00'
workflow_status: needs-review
---
```

Use real timestamps and actual producer identity at write time; the example is illustrative. Attribute a claim with `[^talk-1]` and define the footnote; its label joins to `sources[].id`. Internal paths may be relative or `/` bundle-relative. Prefer relative links for ordinary Obsidian handling. Escape spaces in link targets. Concept identity is its bundle path without `.md`, not a required UUID.

Optional `sources` entries require `resource`; `id`, title, author, usage_count, and last_modified are optional. A resource may be a scope description, so do not automatically interpret every source string as a broken file. Missing optional fields or broken links do not make the bundle nonconformant.

`generated` requires `by`; `at` records meaningful content change. `verified` accepts one mapping or a list of real `{by, at}` checks. Actors: agent/tool `producer/version`, person `human:id`, process `process:id`. No verification means unverified; non-human checks imply machine-confirmed; a human check implies human-reviewed. These are trust signals, not security permissions.

`status`: draft/stable/deprecated (absent means stable). Put in-progress, completed, open, live, or confidence in producer fields such as `workflow_status`, `confidence`, and `talk`. `stale_after` is an absolute offset-aware datetime. Preserve actor and timestamp fields; do not manufacture verification during migration.

Attested Computation additionally requires `runtime`. Executor/attester references describe a separate run protocol. The scaffold/auditor does not execute them or attest results. Never label a figure attested because an LLM recomputed it.

# Adapting an existing Obsidian vault

Audit first and report a concrete adaptation plan. Preserve files and custom fields. Do not silently relabel existing workflow statuses: propose copying to `workflow_status` while setting OKF lifecycle separately. Keep existing wikilinks until a link-safe conversion is ready; resolve targets by path and heading, not a blind text replacement. Migrate the smallest authorised scope, re-audit, and inspect linked notes. Core conformance is narrower than full portability or factual verification.
