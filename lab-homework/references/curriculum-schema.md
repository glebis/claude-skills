# Curriculum Manifest Schema

The `lab-homework` skill fetches a **curriculum manifest** — a JSON file hosted on agency-docs that describes the current cohort's program. This is the contract.

## Hosting

Suggested canonical path:

```
https://<agency-docs-domain>/api/curriculum/<cohort-slug>.json
```

Examples:
- `https://docs.aimindset.ai/api/curriculum/claude-code-internal-03.json`
- `https://docs.aimindset.ai/api/curriculum/claude-code-internal-04.json`

The URL is passed to the skill via the `CLAUDE_LAB_CURRICULUM_URL` env var or the vault config file. One cohort = one URL.

Implementation tip for agency-docs (Next.js / Fumadocs): expose it as a route handler in `app/api/curriculum/[cohort]/route.ts` that reads the cohort's MDX files and returns this JSON. That way editing the presentations automatically updates the manifest — no duplication.

## Schema

```json
{
  "cohort": "claude-code-internal-03",
  "title": "Claude Code Lab — Cohort 03",
  "language": "en",
  "updated_at": "2026-04-08",
  "chat_url": "https://t.me/+aENH1IqZJGY0ODFi",
  "meetings": [
    {
      "number": "01",
      "title": "Introduction and first steps",
      "date": "2026-02-17",
      "topics": [
        "Three Claude Code modes (Normal, Plan, AutoAccept)",
        "Basic commands",
        "Creating CLAUDE.md"
      ],
      "transcript_url": "https://gist.githubusercontent.com/glebis/0a9135c5729725774edfaaf7082f3711/raw/meeting-01.md",
      "slides_url": "https://docs.aimindset.ai/docs/claude-code-internal-03/meetings/01",
      "homework_examples": [
        "Try all three modes on one task and write down the differences",
        "Set up your first CLAUDE.md"
      ]
    },
    {
      "number": "03",
      "title": "Prompt engineering",
      "date": "2026-03-03",
      "topics": [
        "Context management",
        "Structured prompts",
        "Using AskUserQuestion"
      ],
      "transcript_url": "https://gist.githubusercontent.com/glebis/ca1d2409e93f228b2ec314105b336001/raw/meeting-03.md",
      "slides_url": "https://docs.aimindset.ai/docs/claude-code-internal-03/meetings/03",
      "homework_examples": []
    }
  ]
}
```

## Field reference

| Field | Required | Notes |
|---|---|---|
| `cohort` | yes | Slug, matches directory name in agency-docs |
| `title` | yes | Human-readable cohort name |
| `language` | yes | `"en"` or `"ru"` — used as a hint for homework language if the user hasn't specified |
| `updated_at` | yes | ISO date. Skill warns if older than 7 days |
| `chat_url` | no | Optional Telegram/Discord link for participants |
| `meetings[]` | yes | Array, sorted by number |
| `meetings[].number` | yes | Zero-padded string ("01", "03", "11") |
| `meetings[].title` | yes | Short human title |
| `meetings[].date` | yes | ISO date of the meeting |
| `meetings[].topics[]` | yes | 2-5 bullet points. These seed the homework generator's understanding of what was covered — keep them concrete |
| `meetings[].transcript_url` | yes | Raw-text URL (GitHub Gist, agency-docs raw endpoint, or any public markdown). Must be fetchable via `WebFetch` |
| `meetings[].slides_url` | no | Human-facing link, shown to the user for reference |
| `meetings[].homework_examples[]` | no | Optional seed ideas. The skill treats these as inspiration, not a checklist — the rubric still applies |

## Versioning

The skill doesn't do strict schema versioning yet. If the schema evolves, add a `schema_version: 2` field at the top level and update this document. For now, additive changes are safe — the skill ignores unknown fields.

## Minimal example for testing

If you want to test the skill without hosting anything yet, save this as `<vault>/.cache/curriculum.json` manually:

```json
{
  "cohort": "test",
  "title": "Test cohort",
  "language": "en",
  "updated_at": "2026-04-08",
  "meetings": [
    {
      "number": "01",
      "title": "Test meeting",
      "date": "2026-04-08",
      "topics": ["Testing the skill"],
      "transcript_url": "https://gist.githubusercontent.com/glebis/0a9135c5729725774edfaaf7082f3711/raw/meeting-01.md"
    }
  ]
}
```

The skill will use the local cache and skip the remote fetch.
