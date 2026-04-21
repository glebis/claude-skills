---
name: agency-docs-updater
description: End-to-end pipeline for publishing Claude Code lab meetings. Accepts optional args: date (YYYYMMDD, "yesterday", "today") and lab number (e.g. "04"). Examples: "yesterday 04", "20260420 05", "04" (today, lab 04), "" (today, auto-detect lab).
---

# Agency Docs Updater — End-to-End Pipeline

When this skill is invoked, execute ALL steps below automatically in sequence. Do not stop to ask for confirmation between steps — run the full pipeline. Only pause if a step fails and cannot be recovered.

## Step 0: Parse Arguments

The skill accepts optional arguments via the `args` string. Parse them as follows:

**Supported formats** (order doesn't matter):
- `yesterday 04` → date = yesterday, lab = 04
- `20260420 05` → date = 2026-04-20, lab = 05
- `04` → date = today, lab = 04
- `yesterday` → date = yesterday, lab = auto-detect from filename
- *(empty)* → date = today, lab = auto-detect from filename

**Parsing rules**:
1. Split `args` by whitespace
2. Any token that is exactly 8 digits (`YYYYMMDD`) → treat as `DATE`
3. Any token that is "yesterday" → `DATE = $(date -v-1d +%Y%m%d)`
4. Any token that is "today" or missing → `DATE = $(date +%Y%m%d)`
5. Any token that is 2 digits (`NN`) → treat as `LAB_FILTER` (restricts the glob in Step 1)
6. Any token that matches `lab-NN` or `labNN` → extract NN as `LAB_FILTER`

Store `DATE` and `LAB_FILTER` (may be empty) for Step 1.

## Step 1: Find Fathom Transcript

`DATE` is already set from Step 0. Do NOT override it with `$(date +%Y%m%d)`.

If `LAB_FILTER` is set (e.g. `04`), look for: `~/Brains/brain/${DATE}-claude-code-lab-${LAB_FILTER}.md` (exact match).
If `LAB_FILTER` is empty, look for: `~/Brains/brain/${DATE}-claude-code-lab-*.md` (glob — pick most recent by mtime if multiple matches).

If it exists, read it and extract `share_url` and `fathom_id` from its YAML frontmatter.

If the file does NOT exist:
1. Run `~/.claude/skills/calendar-sync/sync.sh` to sync today's calendar
2. Re-check for the file
3. If still missing, stop and report the issue

Store these variables for later steps:
- `FATHOM_FILE` = full path to transcript (e.g. `~/Brains/brain/20260413-claude-code-lab-04.md`)
- `SHARE_URL` = the `share_url` from frontmatter
- `MEETING_TITLE` = the `title` from frontmatter (e.g. "Claude Code Lab 04")
- `DATE` = YYYYMMDD string
- `VIDEO_NAME` = `${DATE}-claude-code-lab-XX` (XX = lab number from filename)
- `LAB_NUMBER` = lab number from filename (e.g. `04`)
- `MEETING_NUMBER` = meeting number from title or determined in Step 5 (e.g. `01`)
- `TRANSCRIPT_LANG` = auto-detected language of the transcript (see below)

### Language auto-detection

Read the first ~50 lines of the transcript body (after YAML frontmatter). Detect the dominant language:
- If most dialogue is in Russian (Cyrillic characters) → `TRANSCRIPT_LANG=ru`
- If most dialogue is in English → `TRANSCRIPT_LANG=en`
- Mixed → use the language of the presenter (Gleb Kalinin's lines)

This variable determines the language for: summary (Step 4), YouTube description (Step 4b), and MDX labels (Step 5).

## Step 2: Download Video (Zoom by default, Fathom fallback)

First check if `~/Brains/brain/${VIDEO_NAME}.mp4` already exists and is > 1MB. If so, skip this step.

### Primary: Zoom Cloud Recording

Lab meetings are recorded on Zoom; Fathom doesn't always capture the video. Use the `zoom` skill to find and download the MP4.

```bash
python3 ~/ai_projects/claude-skills/zoom/scripts/zoom_meetings.py recordings \
  --start ${DATE:0:4}-${DATE:4:2}-${DATE:6:2} \
  --end $(date -j -v+1d -f %Y%m%d ${DATE} +%Y-%m-%d) \
  --show-downloads 2>&1
```

Find the "Claude Code Lab" meeting in the output and grab the MP4 Download URL (the entry labeled `**MP4**`). Then download using the Zoom OAuth token:

```bash
TOK=$(python3 -c "import json,pathlib; print(json.load(open(pathlib.Path.home()/'.zoom_credentials/oauth_token.json'))['access_token'])")
curl -L -o ~/Brains/brain/${VIDEO_NAME}.mp4 "${MP4_DOWNLOAD_URL}?access_token=${TOK}"
ls -lh ~/Brains/brain/${VIDEO_NAME}.mp4
```

Verify the file is > 1MB.

### Fallback: Fathom

If no Zoom recording exists (rare — recordings may take ~15 min to process after meeting ends), fall back to Fathom:

```bash
cd ~/Brains/brain && python3 ~/.claude/skills/fathom/scripts/download_video.py \
  "${SHARE_URL}" --output-name "${VIDEO_NAME}"
```

If both fail, stop and report. Zoom download is usually faster (direct from us02web.zoom.us) — ~30MB/s vs Fathom's variable speeds.

## Step 3: Upload to YouTube via videopublish

**Prerequisites check** (run before first invocation):
```bash
cd ~/ai_projects/youtube-uploader && node -e "require('playwright')" 2>/dev/null || (npm install playwright && npx playwright install chromium)
```

```bash
cd ~/ai_projects/youtube-uploader && \
python3 process_video.py \
  --video ~/Brains/brain/${VIDEO_NAME}.mp4 \
  --fathom-transcript ${FATHOM_FILE} \
  --title "${MEETING_TITLE}" \
  --upload
```

Key notes:
- **Always pass `--title`** with the `title` from the Fathom transcript frontmatter. Without it, the LLM generates a generic/wrong title (e.g. "Клод Код Лаб" instead of the proper meeting name)
- **Do NOT use `source venv/bin/activate`** — youtube-uploader has no venv, run python3 directly
- `--fathom-transcript` makes it skip video transcription (uses Fathom transcript instead)
- `--upload` triggers YouTube + Yandex.Disk upload
- Handles: metadata generation, thumbnail creation, YouTube upload, Yandex upload
- Thumbnail generation requires `playwright` npm package and Chromium browser

### Step 3b: Generate Lab-Style Thumbnail (Lab 04+)

After `process_video.py` completes, replace its generic thumbnail with the lab-style dark editorial template. Do this BEFORE Step 4b (YouTube metadata update), or upload separately after.

**Do NOT trust prior learnings' `-negate -level` step blindly.** Nano Banana's output varies — inspect the raw image first, then decide:
- If raw image has BLACK background + light-colored lines → skip `-negate`, go straight to color swap
- If raw image has WHITE background + dark lines → apply `-negate` first, then color swap
- Prompt Nano Banana for "pure black background" to bias toward the first case

#### 1. Generate overlay image
```bash
~/ai_projects/claude-skills/nano-banana/scripts/generate_image.sh \
  "Abstract minimalist technical diagram: [topic-specific shape]. Thin line art on pure black background. No text, no words. Geometric, architectural blueprint style. Wireframe aesthetic." \
  /tmp/overlay-raw.png
```

Prompt patterns by meeting topic:
- Agents / MCP → "network graph with interconnected nodes radiating outward"
- Plan mode / terminal → "tree structure branching from root node, terminal cursor at top"
- Skills / context engineering → "layered concentric rings, knowledge graph"
- Live coding → "abstract code flow, brackets and indentation, architectural"

#### 2. Inspect + recolor
Read the raw image (Read tool) to confirm background color. Then:

```bash
# If black-bg + light lines (usual case with explicit "pure black background" prompt):
magick /tmp/overlay-raw.png \
  -fuzz 35% -fill '#e85d04' -opaque '#0080ff' \
  -fuzz 35% -fill '#e85d04' -opaque '#2090ff' \
  -fuzz 30% -fill '#e85d04' -opaque '#0070e0' \
  -fuzz 30% -fill '#e85d04' -opaque 'cyan' \
  -fuzz 30% -fill '#e85d04' -opaque '#4a90e2' \
  -fuzz 25% -fill '#e85d04' -opaque '#c0c0c0' \
  ~/ai_projects/youtube-uploader/processed/thumbnails/${VIDEO_NAME}.overlay.png

# If white-bg + dark lines (fallback):
magick /tmp/overlay-raw.png -negate -level 15%,100% /tmp/overlay-neg.png
# ... then same color swap on /tmp/overlay-neg.png
```

Re-Read the final overlay to confirm it's orange-on-black before proceeding. If the whole image is flooded with orange, you color-swapped the background — revert and add that color to the "keep" list or re-generate.

#### 3. Edit the template

Edit `~/ai_projects/youtube-uploader/templates/images/lab-meeting.html` — update text content to match the current meeting:
- `<span class="top-left" data-field="title">` → `Claude Code Lab · XX`
- `<span class="top-right" data-field="subtitle">` → short session descriptor (e.g. "live coding + plan mode")
- `<div class="meeting-label" data-field="meeting_number">` → `Meeting NN`
- `.topic-hero` three lines: short topic phrase, highlighted word, tail
- `.bullets` three one-line descriptions
- `<span data-field="date">` → `DD.MM.YYYY`

Keep topic-hero to 3 short lines — font sizes are fixed and long phrases overflow.

#### 4. Render with Playwright

Write a renderer config and invoke the existing renderer script directly (avoids the default title/subtitle data-field warnings since we set text in the template):

```bash
cat > /tmp/render-thumb.json <<EOF
{
  "template": "/Users/glebkalinin/ai_projects/youtube-uploader/templates/images/lab-meeting.html",
  "jobs": [
    {
      "name": "youtube_maxres",
      "width": 1280,
      "height": 720,
      "format": "jpeg",
      "quality": 95,
      "output": "/Users/glebkalinin/ai_projects/youtube-uploader/processed/thumbnails/${VIDEO_NAME}.jpg",
      "data": {
        "imagePath": "/Users/glebkalinin/ai_projects/youtube-uploader/processed/thumbnails/${VIDEO_NAME}.overlay.png",
        "imageAlt": "Meeting topic"
      }
    }
  ]
}
EOF
cd ~/ai_projects/youtube-uploader && node scripts/render-thumbnails.mjs --config /tmp/render-thumb.json
```

Read the rendered `.jpg` to verify layout before uploading.

#### 5. Upload thumbnail to YouTube

```bash
cd ~/ai_projects/youtube-uploader && PYTHONPATH=. python3 - <<'PY'
from auth import get_authenticated_service
from googleapiclient.http import MediaFileUpload
youtube = get_authenticated_service()
media = MediaFileUpload("processed/thumbnails/${VIDEO_NAME}.jpg", mimetype="image/jpeg")
youtube.thumbnails().set(videoId="${VIDEO_ID}", media_body=media).execute()
PY
```

Template location: `~/ai_projects/youtube-uploader/templates/images/lab-meeting.html`
Style: dark editorial (#0f0f0f bg), EB Garamond italic hero text, JetBrains Mono labels, orange #e85d04 accents, overlay image at 0.3 opacity positioned at right 50% of frame.

Extract YouTube URL from stdout — look for the line:
```
✓ YouTube video: https://www.youtube.com/watch?v=VIDEO_ID
```

If not found in stdout, check the metadata JSON:
```bash
cat ~/ai_projects/youtube-uploader/processed/metadata/${VIDEO_NAME}.json
```

Store `YOUTUBE_URL` for the next steps.

This step is long-running (10-30 minutes depending on upload speed). Run in background with `run_in_background: true`.

If the upload fails or stalls mid-way, resume from the upload step only (skips metadata/thumbnail regeneration):
```bash
python3 process_video.py --video ~/Brains/brain/${VIDEO_NAME}.mp4 \
  --fathom-transcript ${FATHOM_FILE} --title "${MEETING_TITLE}" --upload --resume-from upload
```

**Parallelization**: Start Step 4 (summary generation) while Step 3 upload runs in background. The summary does not depend on the YouTube URL.

## Step 4: Generate Fact-Checked Summary

Read the full Fathom transcript from `${FATHOM_FILE}`.

Generate a comprehensive summary of the meeting **in `${TRANSCRIPT_LANG}`** (the language detected in Step 1) with these requirements:
- Structured with `##` section headers
- Bullet points for key concepts
- Code examples where relevant (keep code/paths in English)
- All technical terms in English (MCP, Skills, Claude Code, YOLO, vibe coding, etc.)
- Comprehensive enough to serve as meeting notes
- **Exclude personal scheduling details** (e.g. "X will be on vacation next week") — only include content relevant to the meeting topic itself

Then use the Task tool with `claude-code-guide` subagent to fact-check all Claude Code feature claims in the summary:

```
Launch claude-code-guide agent to fact-check this summary about Claude Code features.

Verify:
- Subagent types and their capabilities
- Tool names and parameters
- Feature availability and limitations
- Best practices mentioned

Correct any inaccuracies.
```

After fact-checking, save the corrected summary to the scratchpad directory as `summary.md`.

## Step 4b: Update YouTube Video Description

**Do this after both Step 3 (upload) and Step 4 (summary) are complete.**

The description generated by `process_video.py`'s built-in LLM (Groq) is generic and low-quality. Instead, generate the YouTube description yourself using the summary from Step 4, **in `${TRANSCRIPT_LANG}`**.

Determine the meeting page URL: `https://agency-lab.glebkalinin.com/docs/claude-code-internal-XX/meetings/NN` (where XX = lab number, NN = meeting number).

**Character restrictions**: YouTube API rejects descriptions containing `<` or `>` (returns `invalidDescription`). Swap for plain language (e.g. "trash over rm" not "trash > rm"; "use X instead of Y" not "X > Y").

Generate a YouTube description in this format (adapt labels to `${TRANSCRIPT_LANG}`):
```
${MEETING_TITLE}

[1-2 sentence overview of the meeting in ${TRANSCRIPT_LANG}]

In this video: / В этом видео:
- [bullet point 1 — key topic covered]
- [bullet point 2]
- ...
- [bullet point 8-10 max]

Course materials and session notes: / Материалы и конспект занятия:
https://agency-lab.glebkalinin.com/docs/claude-code-internal-XX/meetings/NN

AGENCY community — AI agent practitioners: / Сообщество AGENCY — практики AI-агентов:
https://agency-lab.glebkalinin.com

#ClaudeCode #AI #Anthropic #Claude #AIагенты #программирование
```

Use the Russian or English variant of each label depending on `${TRANSCRIPT_LANG}`. Hashtags stay the same for both languages.

Then update the video on YouTube using the API via `auth.py` (which manages `token.pickle` with `youtube.force-ssl` scope):

```python
cd ~/ai_projects/youtube-uploader && PYTHONPATH=. python3 -c "
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

Key notes:
- `auth.py` uses `youtube.force-ssl` scope which covers both uploads and metadata updates
- `token.pickle` persists across sessions — no browser auth needed after initial setup
- If token expires, `auth.py` auto-refreshes it
- Extract `VIDEO_ID` from `YOUTUBE_URL`
- Generate the bullet points from the summary content, not from the transcript directly

**Add video to playlist** — after updating metadata, add the video to the lab's playlist:

```python
cd ~/ai_projects/youtube-uploader && PYTHONPATH=. python3 -c "
from auth import get_authenticated_service
youtube = get_authenticated_service()

# Find playlist matching 'Claude Code Lab XX'
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

Playlist IDs are looked up at runtime via the YouTube API (the code above searches by name). The playlist name must match exactly (e.g. "Claude Code Lab 03"). If not found, create it manually on YouTube first.

## Step 5: Run update_meeting_doc.py

```bash
python3 ~/.claude/skills/agency-docs-updater/scripts/update_meeting_doc.py \
  ${FATHOM_FILE} \
  "${YOUTUBE_URL}" \
  ${SCRATCHPAD}/summary.md
```

The script auto-detects:
- Lab number from filename (`claude-code-lab-XX` -> `XX`)
- Target docs dir: `~/Sites/agency-docs/content/docs/claude-code-internal-XX/`
- Next meeting number from existing files in `meetings/`
- Presentation files from `~/ai_projects/claude-code-lab/presentations/lab-XX/`
- Summary language (auto-translates to Russian if needed)

**IMPORTANT: Meeting number detection** — The script picks the next available number, but placeholder MDX files may already exist for future meetings with dates pre-filled. Before using the script's auto-detected number:
1. List existing MDX files in `meetings/`
2. Check if any placeholder file already has today's date in its content (e.g. `grep -l "14 февраля" meetings/*.mdx`)
3. If a placeholder exists for today's date, use `--update` flag or `-n NN` to target that file instead of creating a new one

Output: MDX file at `~/Sites/agency-docs/content/docs/claude-code-internal-XX/meetings/NN.mdx`

After the script runs, post-process the generated MDX:

1. **Strip appended presentation content**: The script appends Marp presentation markdown from `presentations/lab-XX/` which contains HTML comments (`<!-- _class: lead -->`) that break MDX compilation. Remove everything after the summary section (after the last `---` separator following the summary). The MDX should only contain: frontmatter, video section, and summary.

2. **Copy lesson HTML to public**: If `~/ai_projects/claude-code-lab/lesson-generator/${DATE}.html` exists, copy it to `~/Sites/agency-docs/public/${DATE}-claude-code-lab-XX.html` (where XX is the lab number). Then add a link in the MDX video section:
   ```
   **Материалы:** [Презентация занятия](/${DATE}-claude-code-lab-XX.html)
   ```

3. **Replace frontmatter placeholders**:
   - `[Название встречи]` -> actual meeting title derived from transcript content
   - `[Краткое описание встречи]` -> brief description
   - `[Дата встречи]` -> formatted date from the transcript

4. **Verify build locally** before committing:
   ```bash
   cd ~/Sites/agency-docs && npm run build 2>&1 | tail -5
   ```
   If build fails, fix the MDX (common issues: HTML comments, unescaped `<` or `{` characters) and retry.

## Step 6: Commit and Push

The working directory often has unrelated unstaged changes that cause push failures. Follow this sequence exactly:

### 1. Identify our files
Only stage the files this pipeline created/modified:
- `content/docs/claude-code-internal-XX/meetings/NN.mdx`
- `public/${DATE}-claude-code-lab-XX.html` (if presentation was copied)

Do NOT use `git add .` or `git add -A` — that pulls in unrelated work.

### 2. Stash unrelated changes if needed
```bash
cd ~/Sites/agency-docs
# Check if remote is ahead
git fetch origin main
BEHIND=$(git rev-list --count HEAD..origin/main)
if [ "$BEHIND" -gt 0 ]; then
  # Stash any unstaged/staged changes to allow clean rebase
  git stash push -m "agency-docs-updater: temp stash"
  git pull --rebase origin main
  git stash pop || true
fi
```

### 3. Stage and commit only our files
```bash
git add content/docs/claude-code-internal-XX/meetings/NN.mdx public/${DATE}-claude-code-lab-XX.html
git commit -m "Add Lab XX Meeting NN"
```

Replace `XX` with lab number and `NN` with meeting number.

### 4. Push
```bash
git push
```

If push still fails (remote updated between fetch and push), repeat: `git pull --rebase origin main && git push`.

This triggers Vercel deployment automatically.

## Step 7: Wait for Vercel Deployment

Poll the GitHub commit status until Vercel deployment completes. Do NOT proceed to Step 8 until deployment succeeds.

```bash
# Poll every 15s until no longer pending (run in background)
until [ "$(gh api repos/glebis/agency-docs/commits/COMMIT_HASH/status --jq '.state' 2>/dev/null)" != "pending" ]; do
  sleep 15
done
gh api repos/glebis/agency-docs/commits/COMMIT_HASH/status --jq '{state, total_count}'
```

Run this with `run_in_background: true` — you'll be notified when it completes.

- If `state: success` — proceed to Step 8.
- If `state: failure` — check the build error locally with `cd ~/Sites/agency-docs && npm run build 2>&1 | tail -20`, fix, and re-push. Then restart Step 7.
- Typical deploy time is 1-3 minutes.

## Step 8: Verify Video Loads in Browser

**Only run after Step 7 confirms `state: success`.** Verify the meeting page and embedded video actually work.

**Requires**: `mcp__claude-in-chrome__*` tools (Chrome browser automation). Load them via `ToolSearch` before calling.

### 1. Open the meeting page
```
ToolSearch: select:mcp__claude-in-chrome__tabs_create_mcp
```
Create a new tab navigating to:
`https://agency-lab.glebkalinin.com/docs/claude-code-internal-XX/meetings/NN`

### 2. Wait for page load and take a screenshot
Wait 5 seconds for the page and YouTube embed to load, then take a screenshot:
```
ToolSearch: select:mcp__claude-in-chrome__tabs_context_mcp
ToolSearch: select:mcp__claude-in-chrome__computer
```
Use `computer` with action `screenshot` to capture the page.

### 3. Verify the video embed
Read the screenshot. Check for:
- **YouTube embed visible**: An iframe with a video player (play button, dark video area). This means the upload succeeded and the embed ID is correct.
- **"Video unavailable" or blank iframe**: The YouTube upload failed or the video is still processing. Wait 2-3 minutes and re-check.
- **No iframe at all**: The MDX is missing the video embed. Fix the MDX and re-push.
- **Page 404 or auth wall**: Deployment may not have propagated yet, or the route is wrong.

### 4. If video doesn't load
Common fixes:
1. **Video still processing on YouTube** — YouTube takes 5-15 minutes to process uploads. Wait and re-check.
2. **Wrong VIDEO_ID in MDX** — Compare the embed URL in the MDX (`/embed/VIDEO_ID`) with the actual YouTube URL. Fix if mismatched.
3. **Upload failed silently** — Re-upload with `--resume-from upload`:
   ```bash
   cd ~/ai_projects/youtube-uploader && python3 process_video.py \
     --video ~/Brains/brain/${VIDEO_NAME}.mp4 \
     --fathom-transcript ${FATHOM_FILE} --title "${MEETING_TITLE}" \
     --upload --resume-from upload
   ```
   Then update the VIDEO_ID in the MDX, rebuild, commit, push.
4. **Embed blocked** — YouTube sometimes blocks embedding for newly uploaded unlisted videos. Change privacy to `public` or wait.

After fixing, repeat Step 8 to confirm the fix worked.

## Pipeline Summary

After completion, report:
1. Fathom transcript path
2. Downloaded video path
3. YouTube URL
4. Generated MDX path
5. Git commit hash
6. Vercel deployment status (success/failure)
7. Video embed verification (pass/fail)

## Error Recovery

- **Step 1 fail (no transcript)**: Run calendar-sync, retry once. If still missing, stop.
- **Step 2 fail (download)**: Check if share_url is valid. Report ffmpeg errors.
- **Step 3 fail (upload)**: Check YouTube OAuth tokens, Playwright installation. Report specific error. Do NOT try `source venv/bin/activate`.
- **Step 4 fail (summary)**: If summary generation in detected language fails, fall back to English.
- **Step 5 fail (MDX)**: Check that fathom_url exists in frontmatter. Check docs_dir exists.
- **Step 6 fail (git push rejected)**: Run `git fetch origin main && git stash push -m "temp" && git pull --rebase origin main && git stash pop && git push`. If rebase has conflicts, resolve them (our meeting files should always win). Do not force-push.

## Reference: CLI Interfaces

### download_video.py
```
python3 download_video.py <share_url> --output-name <name_without_ext>
```
Downloads to current directory as `<name>.mp4`.

### process_video.py
```
python3 process_video.py --video <path> --fathom-transcript <path> --upload
```
Flags: `--upload` (YouTube+Yandex), `--yandex-only`, `--skip-thumbnail`, `--language <code>`, `--title <override>`.

### update_meeting_doc.py
```
python3 update_meeting_doc.py <fathom_file> <youtube_url> <summary_file> [-n NN] [-l ru|en|auto] [--update]
```

## Learnings

### 2026-02-07
**Context**: First full pipeline run for meeting 08

**What Worked**:
- `--resume-from upload` avoids re-generating metadata/thumbnails on upload retry
- Parallelizing summary (Step 4) with YouTube upload (Step 3) saves 10+ minutes
- `gh api repos/OWNER/REPO/commits/HASH/status` reliably checks Vercel deploy status
- Local `npm run build` catches MDX errors before pushing

**What Failed**:
- YouTube upload speed degraded from 5.4 MB/s to 0.15 MB/s mid-upload (3 attempts needed)
- `update_meeting_doc.py` appended lab-01 Marp presentation with `<!-- -->` comments — broke MDX build
- Pushed without local build check — caused Vercel deploy failure, required fix commit

**Known Issues**:
- `presentations/lab-XX/` may contain presentations from wrong meetings — always strip appended content
- YouTube API upload speed is highly variable and not controllable from client side
- MDX does not support HTML comments (`<!-- -->`), unescaped `<`, or bare `{` characters

### 2026-02-14
**Context**: Pipeline run for meeting 10 (Agent SDK workshop)

**What Worked**:
- Parallelizing summary with YouTube upload continues to save significant time
- Date-matching existing placeholder MDX files correctly identifies target meeting number
- Local `npm run build` caught issues before push

**What Failed**:
1. **venv activation** — `source venv/bin/activate` fails because youtube-uploader has no venv. Fixed: run `python3` directly
2. **Playwright missing** — `ERR_MODULE_NOT_FOUND: Cannot find package 'playwright'` during thumbnail generation. Fixed: added prerequisite check in Step 3
3. **Wrong meeting number** — `update_meeting_doc.py` auto-detected meeting 13 (next available), but meeting 10 was a placeholder for today's date. Fixed: added date-matching guidance in Step 5
4. **Personal scheduling details in summary** — "X will be on vacation" included in published summary. Fixed: added exclusion rule in Step 4
5. **Appended Marp content** — still happens despite being documented. Reinforced in Step 5 post-processing

**Key Fix**: Always check existing MDX files by date content before trusting auto-detected meeting number. Use `-n NN` flag to override.

### 2026-03-04
**Context**: Pipeline run for Lab 03, Meeting 01

**What Worked**:
- Full pipeline completed successfully (transcript, download, upload, summary, MDX, deploy)
- Fathom recorded as "Impromptu Zoom Meeting" — found by date, renamed correctly

**What Failed**:
1. **Wrong YouTube title** — Without `--title` flag, LLM generated "Клод Код Лаб" instead of proper meeting name. Fixed: added `--title "${MEETING_TITLE}"` to Step 3 using frontmatter title
2. **YouTube OAuth scope too narrow** — `youtube.upload` scope can't update video metadata (title/description) after upload. Needed `youtube.force-ssl` scope for `videos().update()` call
3. **Appended Marp content** — Still happens (3rd time). Truncation via Edit tool only replaced first match, leaving 1100+ lines of Marp. Fixed: rewrote entire file with Write tool

**Key Fix**: Always pass `--title` from Fathom frontmatter `title` field to `process_video.py`. The LLM metadata generator produces poor/generic titles for Russian-language content.

### 2026-04-08
**Context**: Pipeline run for Lab 03, Meeting 11

**What Worked**:
- **Zoom as primary video source** — Fathom had transcript but no video. `zoom_meetings.py recordings` + curl with OAuth token downloaded 407MB in ~13s (~30 MB/s, much faster than Fathom)
- Placeholder date-matching correctly identified meeting 11 (not auto-detected next number)
- `--resume-from upload` worked perfectly after OAuth re-auth

**What Failed**:
1. **YouTube OAuth token revoked** — `invalid_grant: Token has been expired or revoked`. Fix: `rm token.pickle && python3 -c "from auth import get_authenticated_service; get_authenticated_service()"` — opens browser for re-auth (user must click through)
2. **Appended Marp content** — 6th occurrence. Summary ends at `## Ключевые выводы` list, then `---` + `<!-- _class: lead -->` starts. Fix: `head -N + sed -n 'start,endp'` concat to rewrite file at clean boundary

**Key Fix**: Zoom is now the primary video source (Step 2). Fathom is fallback only.

### 2026-04-13
**Context**: Pipeline run for Lab 04, Meeting 01 (first English-language lab)

**What Worked**:
- Zoom download: 306MB in 11s (~28 MB/s)
- YouTube playlist auto-created when "Claude Code Lab 04" didn't exist yet
- Appended Marp content cleanly stripped with `head -N` truncation
- Full pipeline completed including Vercel deploy

**What Failed**:
1. **Wrong summary language** — Skill hardcoded Russian summary generation. Lab 04 is in English. Generated Russian summary, had to redo in English and re-push.
2. **Fathom filename hardcoded as `-lab-02`** — Step 1 looked for `${DATE}-claude-code-lab-02.md` but Lab 04 transcript was `${DATE}-claude-code-lab-04.md`. Fixed: glob `${DATE}-claude-code-lab-*.md`
3. **WhisperFlow misspelled** — Correct name is "WisprFlow" with link https://wisprflow.ai
4. **Zoom recording still processing** — Meeting just ended, had to wait ~15 min before MP4 was available

**Key Fixes**:
- Added `TRANSCRIPT_LANG` auto-detection in Step 1 (check first 50 lines of transcript for dominant language)
- Summary, YouTube description, and MDX labels now adapt to detected language
- Step 1 now uses glob pattern instead of hardcoded lab number
- Removed hardcoded playlist IDs — now looked up by name via YouTube API at runtime

### 2026-04-15
**Context**: Pipeline run for Lab 04, Meeting 02 (Terminal & Plan Mode)

**What Worked**:
- Zoom download: 488MB in 16s (~30 MB/s)
- Placeholder date-matching correctly identified meeting 02
- `--resume-from upload` recovered cleanly after mid-pipeline OAuth failure
- Custom Python block for metadata/playlist update (bypassing Groq's generic description)
- Custom renderer config + `node scripts/render-thumbnails.mjs` for lab-style thumbnail regeneration

**What Failed**:
1. **YouTube OAuth token revoked mid-pipeline** — had to stop, run re-auth (`rm token.pickle && python3 -c "from auth import get_authenticated_service; get_authenticated_service()"`) in a user terminal, then `--resume-from upload`. Auth requires browser click-through.
2. **YouTube description rejected: `>` character** — YouTube API returns `invalidDescription` for `<` or `>` in description. Must swap for plain language (e.g. "trash over rm" instead of "trash > rm").
3. **`update_meeting_doc.py` tried to translate English summary to Russian** — Lab 04 is English but script's default target lang is `ru`. Translation failed (empty), leaving English content but with Russian section headers (`## Видео`, `## Краткое содержание`). Fix: when `TRANSCRIPT_LANG=en`, rewrite the MDX entirely with English labels instead of relying on the script.
4. **Step 3b thumbnail prior guidance was wrong** — Old skill said to run `-negate -level 15%,100%` unconditionally, but Nano Banana (with explicit "pure black background" prompt) already returns black-bg + light-line images. The negation flipped it to white-bg + dark-line. The orange color swap then flooded the whole background with orange. Fix: inspect raw image first; only negate if background is actually white.
5. **Appended Marp content (8th occurrence)** — persistent issue. Use `head -N` truncation at last valid `---` before `<!-- _class: lead -->`.
6. **Git push rejected (remote ahead + unstaged changes)** — had to `git stash push -- <unrelated paths>`, `git pull --rebase`, push, `git stash pop`.

**Key Fixes**:
- Rewrote Step 3b with conditional recolor logic based on actual image inspection, plus a concrete renderer config JSON example (bypasses the default `thumbnail_generator.py` flow which only injects `title`/`subtitle`/`agency` — for lab-meeting.html we need `imagePath` and template-embedded text)
- Added YouTube description character restrictions to Step 4b (no `<` or `>`)
- Added English-lab MDX rewrite guidance for when `update_meeting_doc.py`'s translation step fails
