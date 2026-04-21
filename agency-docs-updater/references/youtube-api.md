# YouTube API Reference

All scripts run from `${YOUTUBE_UPLOADER_DIR}` with `PYTHONPATH=.` to access `auth.py`.

`auth.py` manages `token.pickle` with `youtube.force-ssl` scope (covers uploads + metadata updates). Token auto-refreshes; if revoked: `rm token.pickle && python3 -c "from auth import get_authenticated_service; get_authenticated_service()"` (requires browser click-through).

## Update video metadata

```python
cd ${YOUTUBE_UPLOADER_DIR} && PYTHONPATH=. python3 -c "
from auth import get_authenticated_service
youtube = get_authenticated_service()
resp = youtube.videos().list(part='snippet', id='VIDEO_ID').execute()
snippet = resp['items'][0]['snippet']
snippet['title'] = MEETING_TITLE
snippet['description'] = DESCRIPTION
snippet['tags'] = ['Claude Code', 'Claude', 'Anthropic', 'AI', 'AI agents', 'AI агенты', 'programming', 'программирование', 'Claude Code Lab', 'MCP']
youtube.videos().update(part='snippet', body={'id': 'VIDEO_ID', 'snippet': snippet}).execute()
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
    if p['snippet']['title'] == 'Claude Code Lab LAB_NUMBER':
        playlist_id = p['id']
        break

if playlist_id:
    youtube.playlistItems().insert(part='snippet', body={
        'snippet': {
            'playlistId': playlist_id,
            'resourceId': {'kind': 'youtube#video', 'videoId': 'VIDEO_ID'}
        }
    }).execute()
    print(f'Added to playlist: {playlist_id}')
else:
    print('Playlist not found — create it manually on YouTube first')
"
```

Playlist name must match exactly (e.g. "Claude Code Lab 03").

## Description format

YouTube API rejects `<` and `>` in descriptions (`invalidDescription`). Use plain language instead.

```
${MEETING_TITLE}

[1-2 sentence overview in ${TRANSCRIPT_LANG}]

In this video: / В этом видео:
- [bullet 1]
- ...
- [bullet 8-10 max]

Course materials and session notes: / Материалы и конспект занятия:
https://agency-lab.glebkalinin.com/docs/claude-code-internal-XX/meetings/NN

AGENCY community — AI agent practitioners: / Сообщество AGENCY — практики AI-агентов:
https://agency-lab.glebkalinin.com

#ClaudeCode #AI #Anthropic #Claude #AIагенты #программирование
```

Use Russian or English labels depending on `${TRANSCRIPT_LANG}`. Hashtags stay the same.
