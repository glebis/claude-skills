# GWS CLI — Full API Reference

## Global Flags (all commands)

```
--params <JSON>       URL/Query parameters as JSON
--json <JSON>         Request body as JSON (POST/PATCH/PUT)
--upload <PATH>       Local file to upload as media content (multipart)
--output <PATH>       Output file path for binary responses
--format <FMT>        Output format: json (default), table, yaml, csv
--api-version <VER>   Override the API version
--page-all            Auto-paginate, one JSON line per page (NDJSON)
--page-limit <N>      Max pages to fetch with --page-all (default: 10)
--page-delay <MS>     Delay between pages in ms (default: 100)
--sanitize <TEMPLATE> Sanitize via Model Armor template
--dry-run             Validate locally without sending
```

## Gmail

### Helper Commands

#### `gws gmail +triage`
Show unread inbox summary (sender, subject, date). Read-only.
```
--max <N>           Maximum messages (default: 20)
--query <QUERY>     Gmail search query (default: is:unread)
--labels            Include label names in output
--format <FORMAT>   Output format (defaults to table)
```
Examples:
```bash
gws gmail +triage
gws gmail +triage --max 5 --query 'from:boss'
gws gmail +triage --format json | jq '.[].subject'
gws gmail +triage --labels
```

#### `gws gmail +send`
Send an email. Handles RFC 2822 formatting and base64 encoding automatically.
```
--to <EMAIL>        Recipient email address (required)
--subject <SUBJECT> Email subject (required)
--body <TEXT>       Email body plain text (required)
```
Examples:
```bash
gws gmail +send --to alice@example.com --subject 'Hello' --body 'Hi Alice!'
```
For HTML bodies, attachments, or CC/BCC, use the raw API: `gws gmail users messages send --json '...'`

#### `gws gmail +watch`
Watch for new emails and stream them as NDJSON. Requires GCP project with Pub/Sub.
```
--project <PROJECT>     GCP project ID for Pub/Sub
--subscription <NAME>   Existing Pub/Sub subscription (skip setup)
--topic <TOPIC>         Existing Pub/Sub topic
--label-ids <LABELS>    Comma-separated Gmail label IDs to filter
--max-messages <N>      Max messages per pull batch (default: 10)
--poll-interval <SECS>  Seconds between pulls (default: 5)
--msg-format <FORMAT>   full, metadata, minimal, raw (default: full)
--once                  Pull once and exit
--cleanup               Delete created Pub/Sub resources on exit
--output-dir <DIR>      Write each message to a separate JSON file
```

### Raw API

All raw API calls require `userId` in params (use `"me"` for authenticated user).

#### Messages
- **List**: `gws gmail users messages list --params '{"userId": "me", "q": "search query", "maxResults": 10}'`
- **Get**: `gws gmail users messages get --params '{"userId": "me", "id": "MSG_ID", "format": "full"}'`
  - format options: `full`, `metadata`, `minimal`, `raw`
  - For metadata only: add `"metadataHeaders": ["Subject", "From", "Date"]`
- **Send**: `gws gmail users messages send --json '{"raw": "base64_encoded_message"}'`
- **Trash**: `gws gmail users messages trash --params '{"userId": "me", "id": "MSG_ID"}'`
- **Modify labels**: `gws gmail users messages modify --params '{"userId": "me", "id": "MSG_ID"}' --json '{"addLabelIds": ["LABEL_ID"], "removeLabelIds": ["INBOX"]}'`
- **Batch modify**: `gws gmail users messages batchModify --params '{"userId": "me"}' --json '{"ids": ["MSG1", "MSG2"], "addLabelIds": ["LABEL"]}'`

#### Labels
- **List**: `gws gmail users labels list --params '{"userId": "me"}'`
- **Create**: `gws gmail users labels create --params '{"userId": "me"}' --json '{"name": "MyLabel", "labelListVisibility": "labelShow", "messageListVisibility": "show"}'`

#### Threads
- **List**: `gws gmail users threads list --params '{"userId": "me", "q": "search query"}'`
- **Get**: `gws gmail users threads get --params '{"userId": "me", "id": "THREAD_ID"}'`

#### Drafts
- **List**: `gws gmail users drafts list --params '{"userId": "me"}'`
- **Create**: `gws gmail users drafts create --params '{"userId": "me"}' --json '{"message": {"raw": "base64"}}'`

#### Settings / Filters
- **List filters**: `gws gmail users settings filters list --params '{"userId": "me"}'`
- **Create filter**: `gws gmail users settings filters create --params '{"userId": "me"}' --json '{"criteria": {"from": "sender@example.com"}, "action": {"addLabelIds": ["LABEL_ID"], "removeLabelIds": ["INBOX"]}}'`
- Note: Requires `gmail.settings.basic` scope

#### Profile
- **Get**: `gws gmail users getProfile --params '{"userId": "me"}'`

## Calendar

### Helper Commands

#### `gws calendar +agenda`
Show upcoming events across all calendars. Read-only.
```
--today              Show today's events
--tomorrow           Show tomorrow's events
--week               Show this week's events
--days <N>           Number of days ahead
--calendar <NAME>    Filter to specific calendar name or ID
--format <FORMAT>    Output format (defaults to table for readability)
```
Examples:
```bash
gws calendar +agenda --today
gws calendar +agenda --week --format table
gws calendar +agenda --days 3 --calendar 'Work'
```

#### `gws calendar +insert`
Create a new event.
```
--summary <TEXT>     Event title (required)
--start <TIME>       Start time ISO 8601 / RFC3339 (required)
--end <TIME>         End time ISO 8601 / RFC3339 (required)
--calendar <ID>      Calendar ID (default: primary)
--location <TEXT>    Event location
--description <TEXT> Event description
--attendee <EMAIL>   Attendee (repeatable)
```
Examples:
```bash
gws calendar +insert --summary 'Standup' --start '2026-06-17T09:00:00+02:00' --end '2026-06-17T09:30:00+02:00'
gws calendar +insert --summary 'Review' --start ... --end ... --attendee alice@example.com
```
For recurring events or conference links, use the raw API.

### Raw API
- **List events**: `gws calendar events list --params '{"calendarId": "primary", "timeMin": "2026-04-10T00:00:00Z", "maxResults": 10, "singleEvents": true, "orderBy": "startTime"}'`
- **Get event**: `gws calendar events get --params '{"calendarId": "primary", "eventId": "EVENT_ID"}'`
- **Insert event**: `gws calendar events insert --params '{"calendarId": "primary"}' --json '{"summary": "...", "start": {"dateTime": "..."}, "end": {"dateTime": "..."}}'`
- **Insert event with Google Meet link** (helper doesn't support this):
  ```bash
  gws calendar events insert \
    --params '{"calendarId":"primary","conferenceDataVersion":1}' \
    --json '{"summary":"Sync","start":{"dateTime":"2026-04-15T14:00:00+02:00"},"end":{"dateTime":"2026-04-15T15:00:00+02:00"},"conferenceData":{"createRequest":{"requestId":"unique-id-123","conferenceSolutionKey":{"type":"hangoutsMeet"}}}}'
  ```
- **Recurring event**: add `"recurrence":["RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=10"]` to event body
- **Add attendees and send invites**: `--params '{"calendarId":"primary","sendUpdates":"all"}'` with `"attendees":[{"email":"a@b.com"}]` in body
- **Update event**: `gws calendar events patch --params '{"calendarId": "primary", "eventId": "EVENT_ID"}' --json '{"summary": "Updated"}'`
- **Delete event**: `gws calendar events delete --params '{"calendarId": "primary", "eventId": "EVENT_ID"}'`
- **List calendars**: `gws calendar calendarList list`
- **Free/busy lookup**: `gws calendar freebusy query --json '{"timeMin":"...","timeMax":"...","items":[{"id":"primary"}]}'`

## Drive

### Helper Commands

#### `gws drive +upload`
Upload a file with automatic metadata. MIME type auto-detected.
```
<file>               Path to file (required, positional)
--parent <ID>        Parent folder ID
--name <NAME>        Target filename (defaults to source filename)
```
Examples:
```bash
gws drive +upload ./report.pdf
gws drive +upload ./report.pdf --parent FOLDER_ID
gws drive +upload ./data.csv --name 'Sales Data.csv'
```

### Raw API
- **List files**: `gws drive files list --params '{"q": "name contains \"report\"", "pageSize": 10}'`
- **Get file metadata**: `gws drive files get --params '{"fileId": "FILE_ID"}'`
- **Download file**: `gws drive files get --params '{"fileId": "FILE_ID", "alt": "media"}' --output ./downloaded_file.pdf`
- **Create folder**: `gws drive files create --json '{"name": "MyFolder", "mimeType": "application/vnd.google-apps.folder"}'`
- **Delete file**: `gws drive files delete --params '{"fileId": "FILE_ID"}'`
- **Share file**: `gws drive permissions create --params '{"fileId": "FILE_ID"}' --json '{"role": "reader", "type": "user", "emailAddress": "user@example.com"}'`

## Sheets

### Helper Commands
#### `gws sheets +read`
Read values from a range. Read-only.
```
--spreadsheet <ID>   Spreadsheet ID (required)
--range <RANGE>      A1 notation (e.g. 'Sheet1!A1:D10')
```
Examples:
```bash
gws sheets +read --spreadsheet SID --range 'Sheet1!A1:D10' --format table
gws sheets +read --spreadsheet SID --range Sheet1
```

#### `gws sheets +append`
Append row(s). Simple strings via `--values` or structured via `--json-values`.
```
--spreadsheet <ID>        Spreadsheet ID (required)
--values <CSV>            Comma-separated single row
--json-values <JSON>      2D array of rows
```
Examples:
```bash
gws sheets +append --spreadsheet SID --values 'Alice,100,true'
gws sheets +append --spreadsheet SID --json-values '[["a","b"],["c","d"]]'
```

### Raw API
- **Get spreadsheet metadata**: `gws sheets spreadsheets get --params '{"spreadsheetId":"SID"}'`
- **Create spreadsheet**: `gws sheets spreadsheets create --json '{"properties":{"title":"My Sheet"}}'`
- **Read values**: `gws sheets spreadsheets values get --params '{"spreadsheetId":"SID","range":"Sheet1!A1:D10"}'`
- **Write values (overwrite)**: `gws sheets spreadsheets values update --params '{"spreadsheetId":"SID","range":"Sheet1!A1","valueInputOption":"USER_ENTERED"}' --json '{"values":[["a","b"]]}'`
- **Clear range**: `gws sheets spreadsheets values clear --params '{"spreadsheetId":"SID","range":"Sheet1!A1:Z1000"}'`
- **Batch update (formatting, formulas)**: `gws sheets spreadsheets batchUpdate --params '{"spreadsheetId":"SID"}' --json '{"requests":[...]}'`

## Chat

### Helper Commands
#### `gws chat +send`
Send plaintext message to a Chat space.
```
--space <NAME>   e.g. spaces/AAAAxxxx
--text <TEXT>    Message body
```

### Raw API
- **List spaces**: `gws chat spaces list`
- **Get space**: `gws chat spaces get --params '{"name":"spaces/AAAA"}'`
- **Send card / threaded reply**: `gws chat spaces messages create --params '{"parent":"spaces/AAAA"}' --json '{"text":"hi","thread":{"threadKey":"mykey"}}'`
- **List messages**: `gws chat spaces messages list --params '{"parent":"spaces/AAAA"}'`

## Meet
- **List conferences**: `gws meet spaces get --params '{"name":"spaces/SID"}'`
- **Create meeting**: `gws meet spaces create --json '{}'` (returns a new Meet space with join URL)

## Tasks

- **List task lists**: `gws tasks tasklists list`
- **List tasks**: `gws tasks tasks list --params '{"tasklist": "@default"}'`
- **Create task**: `gws tasks tasks insert --params '{"tasklist": "@default"}' --json '{"title": "My task", "notes": "Details"}'`
- **Complete task**: `gws tasks tasks patch --params '{"tasklist": "@default", "task": "TASK_ID"}' --json '{"status": "completed"}'`

## Docs

### Helper Commands
#### `gws docs +write`
Append text to a document.

### Raw API
- **Get doc**: `gws docs documents get --params '{"documentId": "DOC_ID"}'`
- **Batch update**: `gws docs documents batchUpdate --params '{"documentId": "DOC_ID"}' --json '{"requests": [...]}'`

## People (Contacts)

- **List contacts**: `gws people people connections list --params '{"resourceName": "people/me", "personFields": "names,emailAddresses"}'`
- **Search**: `gws people people searchContacts --params '{"query": "John", "readMask": "names,emailAddresses"}'`

## Workflow (Cross-Service Helpers)

#### `gws workflow +standup-report`
Today's meetings + open tasks as a standup summary. Read-only.

#### `gws workflow +meeting-prep`
Prepare for next meeting: agenda, attendees, linked docs. Read-only.
```
--calendar <ID>     Calendar ID (default: primary)
```

#### `gws workflow +email-to-task`
Convert a Gmail message into a Google Tasks entry. Write command — confirm before executing.
```
--message-id <ID>   Gmail message ID to convert (required)
--tasklist <ID>     Task list ID (default: @default)
```

#### `gws workflow +weekly-digest`
Weekly summary: this week's meetings + unread email count. Read-only.

#### `gws workflow +file-announce`
Announce a Drive file in a Chat space. Write command.
```
--file-id <ID>      Drive file ID (required)
--space <SPACE>     Chat space name (required)
--message <TEXT>    Custom announcement message
```

## Schema Introspection

Discover API parameters and request body schemas:
```bash
gws schema gmail.users.messages.list
gws schema drive.files.list --resolve-refs
gws schema calendar.events.insert
```
Format: `service.resource.method` or `service.Resource.method`

## All Available Services

gmail, calendar, drive, sheets, docs, slides, tasks, people, chat, vault, admin (directory), admin-reports (reports), groupssettings, reseller, licensing, apps-script (script), classroom, cloudidentity, alertcenter, forms, keep, meet, events, modelarmor, workflow (wf)
