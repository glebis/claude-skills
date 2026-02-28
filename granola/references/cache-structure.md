# Granola Cache Structure

Location: `~/Library/Application Support/Granola/cache-v4.json`

## Top-level
```
{ "cache": { "state": <string|object>, "version": 5 } }
```
`state` may be a JSON string that needs parsing.

## State Keys

| Key | Type | Description |
|-----|------|-------------|
| `documents` | dict[id -> doc] | All meeting documents |
| `transcripts` | dict[id -> utterance[]] | Locally cached transcripts (only recent/active) |
| `meetingsMetadata` | dict[id -> metadata] | Enriched people data for meetings |
| `events` | list | Upcoming calendar events |
| `calendars` | list | Connected calendars |

## Document Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string (UUID) | Primary key |
| `title` | string | Meeting title (from calendar or manual) |
| `created_at` | ISO datetime | When recording started |
| `updated_at` | ISO datetime | Last update |
| `notes` | ProseMirror doc | Structured notes (usually empty stub in cache) |
| `notes_markdown` | string | Markdown notes (usually empty in cache, available via API) |
| `notes_plain` | string | Plain text notes |
| `summary` | string | AI-generated summary |
| `overview` | string | Overview text |
| `people` | object | `{ creator, attendees, title, url, conferencing }` |
| `google_calendar_event` | object | Full GCal event with start/end times |
| `type` | string | "meeting" |
| `valid_meeting` | bool | Whether Granola considers it a valid meeting |
| `subscription_plan_id` | string | e.g. "granola.plan.business.v1" |

## People Object (within document)

```json
{
  "creator": {
    "name": "Gleb Kalinin",
    "email": "glebis@gmail.com",
    "details": { "person": { "name": { "fullName": "..." }, "avatar": "..." }, "company": {} }
  },
  "attendees": [
    {
      "email": "someone@example.com",
      "details": { "person": { "name": { "fullName": "..." } }, "company": {} }
    }
  ]
}
```

## Transcript Utterance

```json
{
  "id": "uuid",
  "document_id": "uuid",
  "start_timestamp": "2026-02-28T10:15:53.490Z",
  "end_timestamp": "2026-02-28T10:16:23.849Z",
  "text": "Utterance text...",
  "source": "microphone" | "system",
  "is_final": true | false
}
```

- `source: "microphone"` = user's microphone (typically the meeting owner)
- `source: "system"` = system audio (other participants)
- No per-utterance speaker names; speaker must be inferred from source

## Auth Token

Location: `~/Library/Application Support/Granola/supabase.json`

```json
{
  "workos_tokens": "{\"access_token\":\"...\", \"refresh_token\":\"...\", \"expires_in\":21599, \"obtained_at\":...}",
  "session_id": "...",
  "user_info": "{...}"
}
```

Token expires after ~6 hours. Refreshed when Granola app is open.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/get-documents` | POST | List docs (supports limit, offset, include_content) |
| `/v1/get-document-transcript` | POST | Get transcript by document_id |
| `/v1/get-documents-batch` | POST | Fetch multiple docs by IDs |
| `/v2/get-document-lists` | POST | Get folders/lists |

## Important Limitations

1. **Local cache has metadata but not content** for most documents. The `notes_markdown`, `summary`, `overview` fields are typically empty.
2. **Transcripts are only cached locally for active/recent meetings** (usually just the current one).
3. **API access uses the local WorkOS token** from supabase.json -- no separate API key needed.
4. **Older transcripts may return 404** from the API if they've been purged.
5. **No per-utterance speaker names** -- only `source` field distinguishing microphone vs system audio.
