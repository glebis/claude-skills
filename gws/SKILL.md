---
name: gws
description: This skill should be used when interacting with Google Workspace services via the gws CLI — Gmail (search, triage, send, labels, filters, drafts), Calendar (agenda, events, Meet conferencing), Drive (upload, list, share, download), Sheets (read, append), Docs, Tasks, Chat (send), People/Contacts, and cross-service workflows (standup, meeting prep, weekly digest, email-to-task). Triggers on queries like "check my email", "search Gmail", "send email", "calendar agenda", "create calendar event", "upload to Drive", "read spreadsheet", "create a task", "triage inbox", "find contact", "post to Chat".
---

# Google Workspace CLI (gws)

CLI for Gmail, Calendar, Drive, Sheets, Docs, Slides, Tasks, People, Chat, Meet, Forms, Keep, Admin, and cross-service workflows.

Binary: `/opt/homebrew/bin/gws`

## Command Pattern

```
gws <service> <resource> [sub-resource] <method> [flags]
```

Every command accepts:
- `--params <JSON>` — URL/query parameters
- `--json <JSON>` — request body (POST/PATCH/PUT)
- `--upload <PATH>` — file to upload as media content
- `--output <PATH>` — path for binary responses (downloads)
- `--format json|table|yaml|csv` — output format (default: json)
- `--page-all` / `--page-limit N` — auto-paginate
- `--dry-run` — validate locally without sending

## Quick Reference — Helper Commands (prefer these)

| Command | Purpose | R/W |
|---|---|---|
| `gws gmail +triage [--max N] [--query Q]` | Unread inbox summary | R |
| `gws gmail +send --to EMAIL --subject S --body T` | Send plaintext email | W |
| `gws gmail +watch --project GCP` | Stream new emails (Pub/Sub) | R |
| `gws calendar +agenda [--today\|--tomorrow\|--week\|--days N]` | Upcoming events | R |
| `gws calendar +insert --summary T --start ISO --end ISO` | Create event | W |
| `gws drive +upload FILE [--parent ID] [--name N]` | Upload file | W |
| `gws sheets +read --spreadsheet ID --range R` | Read range (e.g. `Sheet1!A1:D10`) | R |
| `gws sheets +append --spreadsheet ID --values "a,b,c"` | Append row (or `--json-values`) | W |
| `gws docs +write --document ID --text T` | Append text to doc | W |
| `gws chat +send --space spaces/ID --text T` | Post to Chat space | W |
| `gws workflow +standup-report` | Today's meetings + open tasks | R |
| `gws workflow +meeting-prep [--calendar ID]` | Next meeting details | R |
| `gws workflow +email-to-task --message-id ID` | Email → Task | W |
| `gws workflow +weekly-digest` | Week's meetings + unread | R |
| `gws workflow +file-announce --file-id ID --space SPACE` | Announce file in Chat | W |

## Common Patterns

### Gmail
```bash
# Triage unread (table for humans)
gws gmail +triage --max 10 --format table

# Search
gws gmail users messages list --params '{"userId":"me","q":"from:amazon newer_than:7d","maxResults":5}'

# Read full message
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID","format":"full"}'

# Read headers only (faster)
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID","format":"metadata","metadataHeaders":["Subject","From","Date"]}'

# Archive (remove INBOX)
gws gmail users messages modify --params '{"userId":"me","id":"MSG_ID"}' --json '{"removeLabelIds":["INBOX"]}'

# Trash
gws gmail users messages trash --params '{"userId":"me","id":"MSG_ID"}'

# Bulk label
gws gmail users messages batchModify --params '{"userId":"me"}' --json '{"ids":["ID1","ID2"],"addLabelIds":["Label_123"]}'
```

### Calendar
```bash
# Today (Europe/Berlin default works with RFC3339 +02:00/+01:00)
gws calendar +agenda --today --format table

# Create simple event
gws calendar +insert \
  --summary 'AGENCY Meetup' \
  --start '2026-04-14T18:00:00+02:00' \
  --end '2026-04-14T19:00:00+02:00' \
  --location 'https://us02web.zoom.us/j/8991032224' \
  --description 'Zoom: https://us02web.zoom.us/j/8991032224'

# Event WITH Google Meet link (helper doesn't support — use raw)
gws calendar events insert \
  --params '{"calendarId":"primary","conferenceDataVersion":1}' \
  --json '{
    "summary":"Sync",
    "start":{"dateTime":"2026-04-15T14:00:00+02:00"},
    "end":{"dateTime":"2026-04-15T15:00:00+02:00"},
    "conferenceData":{"createRequest":{"requestId":"req-'$(date +%s)'","conferenceSolutionKey":{"type":"hangoutsMeet"}}}
  }'

# Update event
gws calendar events patch --params '{"calendarId":"primary","eventId":"EID"}' --json '{"summary":"New title"}'

# Delete
gws calendar events delete --params '{"calendarId":"primary","eventId":"EID"}'

# List all calendars
gws calendar calendarList list --format table
```

### Drive
```bash
# Upload to root
gws drive +upload ./report.pdf

# Upload to folder
gws drive +upload ./data.csv --parent FOLDER_ID --name 'Sales Data.csv'

# Search files
gws drive files list --params '{"q":"name contains \"report\" and mimeType=\"application/pdf\"","pageSize":10}'

# Download
gws drive files get --params '{"fileId":"FID","alt":"media"}' --output ./local.pdf

# Create folder
gws drive files create --json '{"name":"MyFolder","mimeType":"application/vnd.google-apps.folder"}'

# Share with user
gws drive permissions create --params '{"fileId":"FID"}' --json '{"role":"reader","type":"user","emailAddress":"user@example.com"}'
```

### Sheets
```bash
# Read
gws sheets +read --spreadsheet SID --range 'Sheet1!A1:D10' --format table

# Append single row (simple values)
gws sheets +append --spreadsheet SID --values 'Alice,100,true'

# Append multiple rows
gws sheets +append --spreadsheet SID --json-values '[["a","b"],["c","d"]]'
```

### Tasks
```bash
gws tasks tasklists list
gws tasks tasks list --params '{"tasklist":"@default"}'
gws tasks tasks insert --params '{"tasklist":"@default"}' --json '{"title":"My task","notes":"Details","due":"2026-04-20T00:00:00Z"}'
gws tasks tasks patch --params '{"tasklist":"@default","task":"TID"}' --json '{"status":"completed"}'
```

### Chat
```bash
# Find space
gws chat spaces list --format table

# Post message
gws chat +send --space spaces/AAAAxxxx --text 'Hello team!'
```

### People / Contacts
```bash
gws people people connections list --params '{"resourceName":"people/me","personFields":"names,emailAddresses","pageSize":100}'
gws people people searchContacts --params '{"query":"John","readMask":"names,emailAddresses"}'
```

## Critical Notes

- **userId**: Every Gmail raw call needs `"userId":"me"` in params.
- **RFC3339 times**: Calendar uses full ISO with offset (`2026-04-14T18:00:00+02:00`). "Z" for UTC.
- **Meet links**: `+insert` does NOT add conferencing — use raw `events.insert` with `conferenceDataVersion=1` and `conferenceData.createRequest`.
- **Pagination**: `--page-all` emits NDJSON (one JSON object per page). `--page-limit N` caps pages.
- **Schema discovery**: `gws schema <service>.<resource>.<method>` — e.g. `gws schema gmail.users.messages.list`.
- **Filters**: `gmail.settings.basic` scope required — special manual OAuth flow (see `references/api_reference.md`).
- **Write confirmation**: Always confirm with user before `+send`, `+insert`, `+email-to-task`, `+file-announce`, `drive files delete`, `events delete`, `messages trash`.
- **Format choice**: `--format table` for human-readable summaries; default `json` for scripting/piping to `jq`.

## OAuth Setup

- GCP project: `n8n-automations-454016`
- Credentials: `~/.config/gws/credentials.json`
- Configured scopes: `gmail.modify`, `gmail.settings.basic`, `drive`, `spreadsheets`, `tasks`, `calendar`, `documents`, `chat.messages`, `contacts.readonly`
- `gmail.settings.basic` scope needs manual OAuth (Python localhost listener on port 8085) — `gws auth login --scopes` cannot request it directly.

## Full API Reference

For full command inventory, all raw API calls, pagination, labels, drafts, filters, and admin APIs, see `references/api_reference.md`.
