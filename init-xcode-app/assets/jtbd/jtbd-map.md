# JTBD → project mapping

Shared by all `init-*` skills. Source schema: `solopreneur-vault/references/jtbd-schema.md`.

## Field → destination

| Source field(s) | Destination |
|---|---|
| `name`, `hook` | README tagline; PRODUCT.md title |
| `jtbd.{situation,motivation,outcome}` | PRODUCT.md "The Job"; AGENTS.md product section |
| `problem.{what_hurts,cost_today}` | PRODUCT.md "Problem" |
| `needs.{functional,emotional,social}` | PRODUCT.md "Needs" |
| `switch_forces.*` | PRODUCT.md "Switch forces" |
| `before_after.*` | PRODUCT.md "Before / After" |
| `scenarios[]` | PRODUCT.md "Scenarios" |
| `guardrails[]` | AGENTS.md "Must NOT do"; PRODUCT.md "Guardrails"; guardrails-check.md |
| `evidence.quotes[]` | PRODUCT.md "Evidence" |
| `open_questions[]` | PRODUCT.md "Open questions" |
| source path, `version` | PRODUCT.md + AGENTS.md footers (`Source JTBD: <path>`) |
| (whole file) | copied verbatim to project-root `jtbd.json` |

## Rendering rules
- Scalars: `{{field}}` (dotted, e.g. `{{jtbd.situation}}`).
- Arrays: a block delimited by `<!-- each:FIELD -->` ... `<!-- /each -->` containing one `{{item}}`
  line; the renderer repeats it per element. `scenarios[]` items are objects: use
  `{{item.title}}` and `{{item.vignette}}`.
- Missing optional field → render an empty string; an empty array → omit the whole `each` block.
- Required fields (`name`, `hook`, `jtbd`) — if absent, ingestion is skipped entirely (see SKILL.md 1.5).

> This asset group is duplicated in `init-tauri-app` and `init-xcode-app` and must be kept
> byte-identical. The only per-skill difference is where `agents-product-section.md.template`
> is injected into that skill's AGENTS.md (after the first heading).
