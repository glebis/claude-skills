---
name: agency-meetup-publish
description: End-to-end pipeline for publishing AGENCY Community meetup recordings to YouTube. Downloads Zoom recording, adds intro/outro, generates thumbnail, creates description with timecodes, uploads to YouTube, sets thumbnail, and adds to the AGENCY Community playlist. Use this skill when the user wants to publish a meetup, says "upload the meetup", "publish the recording", "process the Zoom recording for YouTube", or mentions uploading an AGENCY Community session. Also triggers on requests to add intro/outro to a meeting recording and upload it.
---

# AGENCY Meetup Publish

Publish AGENCY Community meetup recordings to YouTube with intro, thumbnail, description, and timecodes.

## Prerequisites

- `~/ai_projects/youtube-uploader/` — YouTube upload scripts with OAuth credentials
- `~/ai_projects/my-video/out/agency-swarm-intro.mp4` — AGENCY intro animation (6s, 1920x1080)
- Zoom OAuth configured at `~/.zoom_credentials/`
- `ffmpeg` and `ffprobe` installed
- Playwright or Chrome installed (for thumbnail rendering)

## Pipeline Overview

```
1. Identify meeting → 2. Download from Zoom → 3. Add intro/outro
→ 4. Generate timecodes → 5. Write description → 6. Create thumbnail
→ 7. Upload to YouTube → 8. Set thumbnail → 9. Add to playlist
```

## Step 1: Identify the Meeting

Ask the user for:
- **Meeting name or Zoom ID** — if unknown, list recent recordings:
  ```bash
  python3 ~/.claude/skills/zoom/scripts/zoom_meetings.py recordings --start YYYY-MM-DD
  ```
- **Speaker name** — for description and thumbnail
- **Topic summary** — or derive from transcript

Get recording details:
```bash
python3 ~/.claude/skills/zoom/scripts/zoom_meetings.py recording MEETING_ID
```

This returns MP4 download URL, duration, transcript URL, and other files.

## Step 2: Download from Zoom

Download MP4 and VTT transcript in parallel:

```bash
# Video (run in background — large file)
curl -L -o ~/Brains/brain/YYYYMMDD-meeting-slug.mp4 "DOWNLOAD_URL"

# Transcript
curl -L -o ~/Brains/brain/YYYYMMDD-meeting-slug.vtt "TRANSCRIPT_URL"
```

**Naming convention:** `YYYYMMDD-meeting-slug.mp4` where slug is a kebab-case topic summary.

## Step 3: Add Intro (and Outro if Available)

The intro and meeting likely have different specs. Check both:

```bash
ffprobe -v quiet -print_format json -show_streams INTRO.mp4
ffprobe -v quiet -print_format json -show_streams MEETING.mp4
```

Key parameters to match: **resolution, fps, audio sample rate, audio channels**.

### Re-encode intro to match meeting

```bash
ffmpeg -y -i ~/ai_projects/my-video/out/agency-swarm-intro.mp4 \
  -vf "scale=WIDTH:HEIGHT:force_original_aspect_ratio=decrease,pad=WIDTH:HEIGHT:(ow-iw)/2:(oh-ih)/2:black" \
  -r FPS -c:v libx264 -preset fast -crf 18 \
  -ar SAMPLE_RATE -ac CHANNELS -c:a aac \
  /tmp/intro-matched.mp4
```

### Trim meeting start

Review the VTT to find where real content begins. Typically trim 1-3 seconds of silence:

```bash
ffmpeg -y -ss TRIM_SECONDS -i MEETING.mp4 \
  -c:v libx264 -preset fast -crf 18 \
  -ar SAMPLE_RATE -ac CHANNELS -c:a aac \
  -r FPS -vf "scale=WIDTH:HEIGHT" \
  /tmp/meeting-trimmed.mp4
```

This re-encode is necessary for concat compatibility. Run in background — it takes several minutes for long recordings.

### Concatenate

```bash
echo "file '/tmp/intro-matched.mp4'" > /tmp/concat-list.txt
echo "file '/tmp/meeting-trimmed.mp4'" >> /tmp/concat-list.txt
# If outro exists:
# echo "file '/tmp/outro-matched.mp4'" >> /tmp/concat-list.txt

ffmpeg -y -f concat -safe 0 -i /tmp/concat-list.txt -c copy \
  ~/ai_projects/my-video/out/YYYYMMDD-meeting-slug-final.mp4
```

## Step 4: Generate Timecodes from Transcript

Read the VTT transcript and identify **up to 20** topic transitions. Look for:
- Speaker changes (especially when the main speaker starts)
- Topic shifts signaled by phrases like "давайте", "следующий", "перейдем к"
- Q&A segments
- Demo/screen-share moments
- Conclusion/wrap-up

**Important:** Timecodes must account for the intro offset. Add the intro duration (typically 6s) to all VTT timestamps.

Format: `MM:SS Topic description` or `H:MM:SS` for videos over 1 hour.

## Step 5: Write Description

Follow the template from previous AGENCY Community uploads. See `references/description-template.md` for the full template.

Key sections:
1. **Title line** — `AGENCY Community Meetup: [Topic]`
2. **Summary paragraph** — 2-3 sentences about the speaker and topic
3. **Bullet points** — 5-7 key topics covered (use •)
4. **Timecodes** — prefixed with `⏱ Таймкоды:`
5. **Community line** — `AGENCY Community — сообщество практиков AI-автоматизации.`
6. **Links** — prefixed with 🔗, using → arrows
7. **Hashtags** — topic-relevant, always include `#AGENCY #Community`

Save description to `/tmp/youtube-description.txt`.

## Step 6: Create Thumbnail

Use the AGENCY thumbnail HTML template rendered to 1280x720 PNG.

### Template approach

Write an HTML file at `/tmp/thumbnail.html` based on `references/thumbnail-template.html`. Customize:
- **Title text** — short, punchy (2-4 words max per line)
- **Subtitle** — in EB Garamond italic
- **Speaker line** — `Speaker Name × AGENCY`
- **Speaker photo** — if available, use with `mix-blend-mode: hard-light`

### Render to PNG

Preferred: headless Chrome (no install needed):
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --screenshot=/tmp/thumbnail.png \
  --window-size=1280,720 --hide-scrollbars \
  "file:///tmp/thumbnail.html"
```

Fallback: Playwright:
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 720})
    page.goto('file:///tmp/thumbnail.html')
    page.wait_for_timeout(2000)
    page.screenshot(path='/tmp/thumbnail.png')
    browser.close()
```

## Step 7: Upload to YouTube

```bash
cd ~/ai_projects/youtube-uploader && python3 youtube_upload.py \
  --video ~/ai_projects/my-video/out/FINAL.mp4 \
  --title "TITLE" \
  --description "$(cat /tmp/youtube-description.txt)" \
  --category education \
  --privacy public \
  --tags "TAG1,TAG2,..." \
  --yes
```

The upload script outputs the **Video ID** and **Video URL** on success. Capture these for the next steps.

**Title guidelines:** Keep under 100 chars. Format: `Topic — Speaker Name`. Include key terms for search.

## Step 8: Set Thumbnail

```bash
cd ~/ai_projects/youtube-uploader && \
  python3 youtube_manage.py thumbnails set VIDEO_ID /tmp/thumbnail.png
```

## Step 9: Add to Playlist

The AGENCY Community playlist ID is `PLZNP0SKU2SqjHOy01UjDxhSRtcluvuw0m`.

```bash
cd ~/ai_projects/youtube-uploader && \
  python3 youtube_manage.py playlists add-item PLZNP0SKU2SqjHOy01UjDxhSRtcluvuw0m VIDEO_ID
```

## Parallelization Strategy

For speed, run these in parallel where possible:

| Phase | Can parallelize with |
|-------|---------------------|
| Download MP4 | Download VTT |
| Re-encode meeting (bg) | Read transcript, draft timecodes |
| Upload to YouTube (bg) | Generate thumbnail |
| Set thumbnail | Add to playlist |

## Output

Report to the user:
- **Video URL**: `https://www.youtube.com/watch?v=VIDEO_ID`
- **Studio URL**: `https://studio.youtube.com/video/VIDEO_ID/edit`
- **Playlist**: AGENCY Community

## Existing Skills Used

This pipeline builds on:
- **zoom** — `~/.claude/skills/zoom/` for Zoom recording access
- **video-youtube-upload** — `~/.claude/skills/video-youtube-upload/` for upload reference
- **youtube** — `~/.claude/skills/youtube/` for post-upload management
- **agency-socials** — `~/.claude/skills/agency-socials/` for cover design system reference
