---
name: granola
description: This skill should be used when importing, listing, or exporting Granola meeting recordings and transcripts. Queries Granola's Personal API to list meetings, extract transcripts, and export to Obsidian notes in Fathom-compatible format.
---

# Granola Meeting Importer

Query Granola via Personal API to list notes, view transcripts, and export to Obsidian vault in the same format as the Fathom skill.

## Prerequisites

- Granola Business or Enterprise plan (Personal API required)
- API key in sops-encrypted `~/Brains/brain/.env.granola` as `GRANOLA_API_KEY=grn_...`
- No additional dependencies (uses stdlib only)

## Usage

```bash
python3 ~/.claude/skills/granola/scripts/granola.py <command> [options]
```

### Commands

| Command | Description |
|---------|-------------|
| `list` | List notes from Personal API |
| `show <note_id>` | Show note details (summary, attendees, optionally transcript) |
| `export <note_id>` | Export note to Obsidian markdown (Fathom-compatible format) |

### Options

| Option | Applies to | Description |
|--------|-----------|-------------|
| `--format text\|json` | list, show | Output format (default: text) |
| `--after <ISO date>` | list | Filter notes created after date |
| `--all` | list | Paginate through all results |
| `--transcript` | show | Include transcript in output |
| `--vault <path>` | export | Obsidian vault path (default: ~/Brains/brain) |
| `--output <path>` | export | Custom output file path |

## Examples

### List recent meetings
```bash
python3 ~/.claude/skills/granola/scripts/granola.py list
python3 ~/.claude/skills/granola/scripts/granola.py list --format json
python3 ~/.claude/skills/granola/scripts/granola.py list --after 2026-05-01
```

### Show note with transcript
```bash
python3 ~/.claude/skills/granola/scripts/granola.py show not_5FkswTp4Omkpm5
python3 ~/.claude/skills/granola/scripts/granola.py show not_5FkswTp4Omkpm5 --transcript --format json
```

### Export to Obsidian
```bash
python3 ~/.claude/skills/granola/scripts/granola.py export not_5FkswTp4Omkpm5
python3 ~/.claude/skills/granola/scripts/granola.py export not_5FkswTp4Omkpm5 --vault ~/Brains/brain
```

## Output Format

Exported notes match Fathom skill format for consistency:

```markdown
---
granola_id: not_xxxx
title: "Meeting Title"
date: YYYY-MM-DD
participants: ['Name 1', 'Name 2']
duration: HH:MM
source: granola
---

# Meeting Title

## Summary
{AI-generated summary}

## Transcript
**Speaker Name**: What they said...
```

Files saved as: `YYYYMMDD-meeting-title-slug.md`

## API Details

- **Base URL**: `https://public-api.granola.ai/v1`
- **Auth**: Bearer token (Personal API key, never expires)
- **Rate limits**: 25 req burst / 5 req/sec sustained
- **Important**: API only returns notes with generated summaries — in-progress meetings won't appear

## Known Limitations

- **No live/in-progress access** — notes appear only after Granola generates the AI summary
- **No per-utterance speaker names** — Granola provides `source` (microphone vs speaker) and optional `diarization_label`. Export assigns meeting owner to microphone utterances
- **Note IDs required** — use `list` first to get `not_xxxx` IDs, then `show`/`export`

## Integration

- **transcript-analyzer**: After export, run transcript-analyzer on the output file for deeper analysis
- **Fathom skill**: Granola exports use the same frontmatter and transcript format as Fathom exports, so downstream tools work with both
