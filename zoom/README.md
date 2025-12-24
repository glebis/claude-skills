# Zoom Skill

Manage Zoom meetings and cloud recordings via the Zoom API.

## Features

- List, create, update, and delete Zoom meetings
- Access cloud recordings with transcripts, summaries, and download links
- Supports both instant and scheduled meetings
- JSON and Markdown output formats

## Authentication

This skill requires two Zoom apps due to API limitations:

1. **Server-to-Server OAuth** - For meeting management (no user interaction)
2. **General App (OAuth)** - For cloud recordings (one-time browser auth)

See [SKILL.md](SKILL.md) for detailed setup instructions.

## Quick Example

```bash
# List upcoming meetings
python3 scripts/zoom_meetings.py list

# Create a scheduled meeting
python3 scripts/zoom_meetings.py create "Team Sync" --start "2025-01-15T14:00:00"

# List recordings from last month
python3 scripts/zoom_meetings.py recordings --start 2025-01-01
```

## Requirements

```bash
pip install requests
```

## License

MIT
