---
name: granola
description: This skill should be used when importing, listing, or exporting Granola meeting recordings and transcripts. Queries Granola's local cache and API to list meetings, extract transcripts, and export to Obsidian notes in Fathom-compatible format.
---

# Granola Meeting Importer

Query Granola's local data (cache + API) to list meetings, view transcripts, and export to Obsidian vault in the same format as the Fathom skill.

## Prerequisites

- Granola desktop app installed and authenticated (macOS)
- No additional dependencies required (uses stdlib only)

## Usage

```bash
python3 ~/.claude/skills/granola/scripts/granola.py <command> [options]
```

### Commands

| Command | Description |
|---------|-------------|
| `list` | List all meetings from local cache |
| `show <id>` | Show meeting details (by ID prefix or title substring) |
| `transcript <id>` | Get transcript (local cache, falls back to API) |
| `export <id>` | Export meeting to Obsidian note (Fathom-compatible format) |
| `api-list` | List meetings via Granola API (may show more than cache) |

### Options

| Option | Applies to | Description |
|--------|-----------|-------------|
| `--format text\|json` | list, transcript | Output format (default: text) |
| `--local-only` | transcript, export | Skip API fallback, use only cached data |
| `--vault <path>` | export | Obsidian vault path (default: ~/Brains/brain) |
| `--output <path>` | export | Custom output file path |
| `--limit <n>` | api-list | Max results (default: 50) |
| `--offset <n>` | api-list | Pagination offset |

## Examples

### List meetings
```bash
python3 ~/.claude/skills/granola/scripts/granola.py list
python3 ~/.claude/skills/granola/scripts/granola.py list --format json
```

### Export to Obsidian
```bash
python3 ~/.claude/skills/granola/scripts/granola.py export bbeba240
python3 ~/.claude/skills/granola/scripts/granola.py export "Подкаст"
```

### Get transcript
```bash
python3 ~/.claude/skills/granola/scripts/granola.py transcript bbeba240
python3 ~/.claude/skills/granola/scripts/granola.py transcript "Подкаст" --format json
```

## Output Format

Exported notes match Fathom skill format for consistency:

```markdown
---
granola_id: <uuid>
title: "Meeting Title"
date: YYYY-MM-DD
participants: ['Name 1', 'Name 2']
duration: HH:MM
source: granola
---

# Meeting Title

## Summary
{AI-generated summary if available}

## Notes
{Markdown notes if available}

## Transcript
**Speaker Name**: What they said...
```

Files saved as: `YYYYMMDD-meeting-title-slug.md`

## Data Sources

The script reads from two local sources:

1. **Cache file**: `~/Library/Application Support/Granola/cache-v4.json` -- metadata for all meetings, transcripts for active/recent meetings only
2. **API token**: `~/Library/Application Support/Granola/supabase.json` -- WorkOS bearer token for API calls (auto-refreshed when app is open, ~6h expiry)

See `references/cache-structure.md` for full schema documentation.

## Known Limitations

- **Transcript content is sparse in cache** -- only the most recent/active meeting typically has a full transcript locally. Older ones require API fetch.
- **No per-utterance speaker names** -- Granola only provides `source` (microphone vs system audio). The export assigns the meeting creator to microphone utterances and "Other" to system audio.
- **Notes/summaries often empty** -- Granola stores rich content server-side; the local cache has stubs. The API also returns empty for personal (non-workspace) docs.
- **Token expiry** -- if the Granola app hasn't been open recently, the token may be expired. Open the app to refresh.

## Integration

- **transcript-analyzer**: After export, run transcript-analyzer on the output file for deeper analysis
- **Fathom skill**: Granola exports use the same frontmatter and transcript format as Fathom exports, so downstream tools work with both
