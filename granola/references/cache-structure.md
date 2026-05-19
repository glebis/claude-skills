# Granola API Reference

> **Note**: As of April 2026, Granola encrypted its local database and cache files.
> This skill now uses the Personal API exclusively. Local cache access no longer works.

## Base URL

`https://public-api.granola.ai/v1`

## Authentication

Bearer token: `Authorization: Bearer grn_...`

Personal API key from Granola desktop app: Settings > Connectors > API keys.
Key stored sops-encrypted at `~/Brains/brain/.env.granola` as `GRANOLA_API_KEY=grn_...`.

## Endpoints

### List Notes
```
GET /notes
```
Query params:
- `created_after` (optional): ISO 8601 timestamp
- `cursor` (optional): pagination cursor from previous response

Response:
```json
{
  "notes": [...],
  "hasMore": true,
  "cursor": "next_page_cursor"
}
```

### Get Note
```
GET /notes/{note_id}
```
- `note_id`: pattern `^not_[a-zA-Z0-9]{14}$`
- Query param `include=transcript` to get transcript data

Response: Note object with id, title, owner, created_at, updated_at, web_url,
calendar_event, attendees, summary_text, summary_markdown, transcript (if requested).

### Transcript format
```json
{
  "speaker": {
    "source": "microphone" | "speaker",
    "diarization_label": "optional label"
  },
  "text": "utterance text",
  "start_time": "ISO 8601",
  "end_time": "ISO 8601"
}
```
- macOS: source is "microphone" (user) or "speaker" (system audio / other participants)
- iOS: source always "microphone"; may include diarization_label

## Rate Limits

- Burst: 25 requests per 5 seconds
- Sustained: 5 req/sec (300/min)
- Per user for Personal API keys
- 429 Too Many Requests on exceed

## Important Limitations

1. **Only completed notes** — API returns notes with generated AI summary only. In-progress meetings return 404.
2. **No live/streaming access** — no way to read transcript of ongoing recording.
3. **Business/Enterprise plan required** — Personal API not available on Free or Pro.
4. **No webhooks** — must poll. Webhooks on Granola's roadmap.
5. **No per-utterance speaker names** — only source field and optional diarization_label.
