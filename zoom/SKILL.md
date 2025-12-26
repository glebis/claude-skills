---
name: zoom
description: Create and manage Zoom meetings and access cloud recordings via the Zoom API. Use for queries like "create a Zoom meeting", "list my Zoom meetings", "show my Zoom recordings", or "schedule a meeting for tomorrow".
---

# Zoom Skill

Manage Zoom meetings and cloud recordings via the Zoom API.

## Features

- **Meetings**: List, create, update, delete scheduled meetings
- **Recordings**: List cloud recordings with transcripts, summaries, and download links

**Note:** All times passed to create/update commands are interpreted as **local time**. The script auto-detects your timezone if not explicitly specified with `--timezone`.

## Prerequisites

This skill uses two authentication methods:

| Feature | Auth Type | Credentials File |
|---------|-----------|------------------|
| Meetings | Server-to-Server OAuth | `~/.zoom_credentials/credentials.json` |
| Recordings | User OAuth (General App) | `~/.zoom_credentials/oauth_token.json` |

Check status:

```bash
python3 scripts/zoom_meetings.py setup
```

## Setup

### Part 1: Server-to-Server OAuth (for Meetings)

1. Go to [marketplace.zoom.us](https://marketplace.zoom.us/) → Develop → Build App
2. Select **Server-to-Server OAuth**
3. Name it (e.g., "Claude Zoom Meetings")
4. Copy **Account ID**, **Client ID**, **Client Secret**
5. Add scopes:
   - `meeting:read:meeting:admin`
   - `meeting:read:list_meetings:admin`
   - `meeting:write:meeting:admin`
   - `user:read:user:admin`
6. Activate the app
7. Save credentials:

```bash
mkdir -p ~/.zoom_credentials
cat > ~/.zoom_credentials/credentials.json << 'EOF'
{
  "account_id": "YOUR_ACCOUNT_ID",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
}
EOF
```

### Part 2: General App OAuth (for Recordings)

Server-to-Server apps cannot access cloud recordings. You need a separate General App:

1. Go to [marketplace.zoom.us](https://marketplace.zoom.us/) → Develop → Build App
2. Select **General App**
3. Set redirect URL: `http://localhost:8888/callback`
4. Copy **Client ID** and **Client Secret**
5. Add scopes:
   - `cloud_recording:read:list_user_recordings`
   - `cloud_recording:read:list_recording_files`
6. Activate the app
7. Authorize (one-time browser flow):

```bash
# Open this URL in browser (replace CLIENT_ID):
https://zoom.us/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8888/callback

# After authorizing, you'll be redirected to:
# http://localhost:8888/callback?code=AUTHORIZATION_CODE

# Exchange the code for tokens (replace values):
python3 -c "
import requests, json
resp = requests.post('https://zoom.us/oauth/token',
    auth=('CLIENT_ID', 'CLIENT_SECRET'),
    data={'grant_type': 'authorization_code', 'code': 'AUTH_CODE', 'redirect_uri': 'http://localhost:8888/callback'})
data = resp.json()
data['client_id'] = 'CLIENT_ID'
data['client_secret'] = 'CLIENT_SECRET'
data['expires_at'] = __import__('time').time() + data.get('expires_in', 3600)
with open(__import__('pathlib').Path.home() / '.zoom_credentials/oauth_token.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Saved!')
"
```

## Quick Start

```bash
# Check setup
python3 scripts/zoom_meetings.py setup

# List upcoming meetings
python3 scripts/zoom_meetings.py list

# Create a meeting
python3 scripts/zoom_meetings.py create "Team Standup" --start "2025-01-15T10:00:00" --duration 30

# List recordings
python3 scripts/zoom_meetings.py recordings --start 2025-01-01
```

## Commands

### Meetings

```bash
# List meetings
python3 scripts/zoom_meetings.py list                      # upcoming
python3 scripts/zoom_meetings.py list --type previous      # past
python3 scripts/zoom_meetings.py list --limit 10 --json

# Get meeting details
python3 scripts/zoom_meetings.py get MEETING_ID

# Create meeting (times are treated as LOCAL time)
python3 scripts/zoom_meetings.py create "Topic"                              # instant
python3 scripts/zoom_meetings.py create "Topic" --start "2025-01-15T14:00:00" # scheduled (local time)
python3 scripts/zoom_meetings.py create "Topic" --duration 60 --timezone "Europe/Berlin"
python3 scripts/zoom_meetings.py create "Topic" --agenda "Discussion points" --waiting-room
python3 scripts/zoom_meetings.py create "Topic" --invite "user@example.com"  # send invite
python3 scripts/zoom_meetings.py create "Topic" --invite "a@x.com" --invite "b@x.com"  # multiple

# Update meeting
python3 scripts/zoom_meetings.py update MEETING_ID --topic "New Topic"
python3 scripts/zoom_meetings.py update MEETING_ID --start "2025-01-16T10:00:00"

# Delete meeting (requires meeting:delete:meeting:admin scope)
python3 scripts/zoom_meetings.py delete MEETING_ID
```

### Recordings

```bash
# List all recordings (default: last 30 days)
python3 scripts/zoom_meetings.py recordings

# With date range
python3 scripts/zoom_meetings.py recordings --start 2025-01-01 --end 2025-01-31

# Show download URLs
python3 scripts/zoom_meetings.py recordings --show-downloads

# Get specific meeting's recordings
python3 scripts/zoom_meetings.py recording MEETING_ID

# JSON output
python3 scripts/zoom_meetings.py recordings --json
```

## Output Formats

### Markdown (default)

```markdown
# Zoom Meetings (3 upcoming)

## Weekly Team Sync
**ID:** 123456789
**Start:** 2025-01-15 14:00:00 UTC
**Duration:** 60 minutes
**Join URL:** https://zoom.us/j/123456789
```

### JSON

Add `--json` for structured output suitable for piping to other tools.

## Recording File Types

| Type | Description |
|------|-------------|
| MP4 | Video recording |
| M4A | Audio only |
| TRANSCRIPT | Text transcript (VTT) |
| CHAT | Chat messages |
| TIMELINE | Speaker timeline |
| SUMMARY | AI meeting summary |

## Example User Requests

| User says | Command |
|-----------|---------|
| "List my Zoom meetings" | `list` |
| "Show past meetings" | `list --type previous` |
| "Create a meeting for tomorrow at 2pm" | `create "Meeting" --start "2025-01-15T14:00:00"` |
| "Show my Zoom recordings" | `recordings --start 2025-01-01` |
| "Get the recording for meeting X" | `recording MEETING_ID` |

## Dependencies

```bash
pip install requests
```

## Files

| File | Purpose |
|------|---------|
| `~/.zoom_credentials/credentials.json` | S2S OAuth credentials |
| `~/.zoom_credentials/token.json` | S2S cached token |
| `~/.zoom_credentials/oauth_token.json` | User OAuth tokens (auto-refreshes) |

## API Reference

- [Zoom Meeting APIs](https://developers.zoom.us/docs/api/meetings/)
- [Zoom API Reference](https://developers.zoom.us/docs/api/rest/reference/zoom-api/methods/)
