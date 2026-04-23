# YouTube API Reference

All scripts run from `${YOUTUBE_UPLOADER_DIR}` with `PYTHONPATH=.` to access `auth.py`.

`auth.py` manages `token.pickle` with `youtube.force-ssl` scope (covers uploads + metadata updates). Token auto-refreshes; if revoked: `rm token.pickle && python3 -c "from auth import get_authenticated_service; get_authenticated_service()"` (requires browser click-through).

## Update video metadata

```python
cd ${YOUTUBE_UPLOADER_DIR} && PYTHONPATH=. python3 -c "
from auth import get_authenticated_service
youtube = get_authenticated_service()
resp = youtube.videos().list(part='snippet', id='${VIDEO_ID}').execute()
snippet = resp['items'][0]['snippet']
snippet['title'] = '${MEETING_TITLE}'
snippet['description'] = DESCRIPTION
snippet['tags'] = ['Claude Code', 'Claude', 'Anthropic', 'AI', 'AI agents', 'programming', 'Claude Code Lab', 'MCP']
youtube.videos().update(part='snippet', body={'id': '${VIDEO_ID}', 'snippet': snippet}).execute()
"
```

## Add video to playlist

Playlists are looked up by name at runtime — no hardcoded IDs.

```python
cd ${YOUTUBE_UPLOADER_DIR} && PYTHONPATH=. python3 -c "
from auth import get_authenticated_service
youtube = get_authenticated_service()
resp = youtube.playlists().list(part='snippet', mine=True, maxResults=50).execute()
playlist_id = None
for p in resp['items']:
    if p['snippet']['title'] == 'Claude Code Lab ${LAB_NUMBER}':
        playlist_id = p['id']
        break

if not playlist_id:
    playlist = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title': 'Claude Code Lab ${LAB_NUMBER}',
                'description': 'Claude Code Lab ${LAB_NUMBER}'
            },
            'status': {'privacyStatus': 'unlisted'}
        }
    ).execute()
    playlist_id = playlist['id']
    print(f'Created playlist: {playlist_id}')

youtube.playlistItems().insert(part='snippet', body={
    'snippet': {
        'playlistId': playlist_id,
        'resourceId': {'kind': 'youtube#video', 'videoId': '${VIDEO_ID}'}
    }
}).execute()
print(f'Added to playlist: {playlist_id}')
"
```

If no matching playlist exists, one is created automatically (unlisted). Playlist name must match exactly (e.g. "Claude Code Lab 03").

## Description format

YouTube API rejects `<` and `>` in descriptions (`invalidDescription`). Use plain language instead.

### English template (when `TRANSCRIPT_LANG=en`)

```
${MEETING_TITLE}

[1-2 sentence overview]

In this video:
- [bullet 1]
- ...
- [bullet 8-10 max]

Course materials and session notes:
https://${SITE_DOMAIN}/docs/claude-code-internal-${LAB_NUMBER}/meetings/${MEETING_NUMBER}

AGENCY community — AI agent practitioners:
https://${SITE_DOMAIN}

#ClaudeCode #AI #Anthropic #Claude #AIagents #programming
```

### Russian template (when `TRANSCRIPT_LANG=ru`)

```
${MEETING_TITLE}

[1-2 предложения обзора]

В этом видео:
- [пункт 1]
- ...
- [пункт 8-10 макс]

Материалы и конспект занятия:
https://${SITE_DOMAIN}/docs/claude-code-internal-${LAB_NUMBER}/meetings/${MEETING_NUMBER}

Сообщество AGENCY — практики AI-агентов:
https://${SITE_DOMAIN}

#ClaudeCode #AI #Anthropic #Claude #AIагенты #программирование
```

Use the template matching `${TRANSCRIPT_LANG}`. Do NOT mix languages in a single description. Hashtags differ slightly between templates.
