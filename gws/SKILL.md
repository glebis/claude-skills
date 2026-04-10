---
name: gws
description: This skill should be used when interacting with Google Workspace services via the gws CLI — Gmail (search, triage, send, labels, filters), Calendar (agenda, events), Drive (upload, list, share), Tasks, Docs, People/Contacts, and cross-service workflows (standup, meeting prep, weekly digest). Triggers on queries like "check my email", "search Gmail", "send email", "calendar agenda", "upload to Drive", "create a task", "triage inbox", "find contact".
---

# Google Workspace CLI (gws)

CLI tool for interacting with Gmail, Calendar, Drive, Tasks, Docs, People, and cross-service workflows.

Binary: `/opt/homebrew/bin/gws`

## Command Pattern

```
gws <service> <resource> [sub-resource] <method> [flags]
```

All commands accept `--params <JSON>` for URL/query parameters and `--json <JSON>` for request bodies. Output formats: `json` (default), `table`, `yaml`, `csv`.

## Quick Reference — Helper Commands

Prefer helper commands (`+command`) over raw API calls when available. They handle formatting, pagination, and defaults automatically.

| Command | Purpose | Read/Write |
|---------|---------|------------|
| `gws gmail +triage` | Unread inbox summary | Read |
| `gws gmail +send --to EMAIL --subject SUBJ --body TEXT` | Send email | Write |
| `gws gmail +watch --project GCP_PROJECT` | Stream new emails | Read |
| `gws calendar +agenda --today` | Today's events | Read |
| `gws calendar +insert --summary TITLE --start TIME --end TIME` | Create event | Write |
| `gws drive +upload FILE` | Upload file | Write |
| `gws docs +write` | Append to doc | Write |
| `gws workflow +standup-report` | Meetings + tasks summary | Read |
| `gws workflow +meeting-prep` | Next meeting details | Read |
| `gws workflow +email-to-task --message-id ID` | Email to task | Write |
| `gws workflow +weekly-digest` | Weekly summary | Read |
| `gws workflow +file-announce --file-id ID --space SPACE` | Announce file in Chat | Write |

## Common Patterns

### Gmail Search
```bash
# Triage unread
gws gmail +triage --max 10 --format table

# Search for specific emails
gws gmail users messages list --params '{"userId": "me", "q": "from:amazon subject:S3", "maxResults": 5}'

# Read a message (full content)
gws gmail users messages get --params '{"userId": "me", "id": "MSG_ID", "format": "full"}'

# Read metadata only (faster)
gws gmail users messages get --params '{"userId": "me", "id": "MSG_ID", "format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]}'
```

### Calendar
```bash
# Today's agenda
gws calendar +agenda --today --format table

# Create event (use RFC3339 times)
gws calendar +insert --summary 'Meeting' --start '2026-04-10T14:00:00+02:00' --end '2026-04-10T15:00:00+02:00'
```

### Drive
```bash
# Upload
gws drive +upload ./file.pdf --parent FOLDER_ID

# Search files
gws drive files list --params '{"q": "name contains \"report\"", "pageSize": 10}'
```

## Critical Notes

- **userId**: All Gmail raw API calls require `"userId": "me"` in params
- **Pagination**: Use `--page-all` for full result sets, `--page-limit N` to cap pages
- **Schema discovery**: `gws schema gmail.users.messages.list` to explore any API method's parameters
- **Filters**: Require `gmail.settings.basic` OAuth scope (special manual OAuth flow needed — see references)
- **Write commands**: Confirm with user before executing `+send`, `+insert`, `+email-to-task`, `+file-announce`
- **Times**: Calendar uses RFC3339 format (e.g., `2026-04-10T14:00:00+02:00`)

## OAuth Setup

- Credentials: `~/.config/gws/credentials.json`
- Login: `gws auth login --scopes gmail,drive,calendar,tasks`
- The `gmail.settings.basic` scope (needed for filters) requires a manual OAuth flow — `gws auth login --scopes` does not support granular Gmail scopes directly

## Full API Reference

For complete command documentation including all raw API calls, parameters, and examples, read `references/api_reference.md`.
