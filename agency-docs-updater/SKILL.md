---
name: agency-docs-updater
description: End-to-end pipeline for publishing Claude Code lab meetings. Automatically finds/creates Fathom transcript, downloads video, uploads to YouTube, generates fact-checked Russian summary, creates MDX documentation, and pushes to agency-docs for Vercel deployment. Single invocation replaces 5+ manual steps.
---

# Agency Docs Updater — End-to-End Pipeline

When this skill is invoked, execute ALL steps below automatically in sequence. Do not stop to ask for confirmation between steps — run the full pipeline. Only pause if a step fails and cannot be recovered.

## Step 1: Find Fathom Transcript

```bash
DATE=$(date +%Y%m%d)
```

Look for `~/Brains/brain/${DATE}-claude-code-lab-02.md`. If it exists, read it and extract `share_url` and `fathom_id` from its YAML frontmatter.

If the file does NOT exist:
1. Run `~/.claude/skills/calendar-sync/sync.sh` to sync today's calendar
2. Re-check for the file
3. If still missing, stop and report the issue

Store these variables for later steps:
- `FATHOM_FILE` = full path to transcript (e.g. `~/Brains/brain/20260207-claude-code-lab-02.md`)
- `SHARE_URL` = the `share_url` from frontmatter
- `MEETING_TITLE` = the `title` from frontmatter (e.g. "Claude Code Lab 03 — Meeting 01: Знакомство и введение")
- `DATE` = YYYYMMDD string
- `VIDEO_NAME` = `${DATE}-claude-code-lab-02`
- `LAB_NUMBER` = lab number from filename (e.g. `03`)
- `MEETING_NUMBER` = meeting number from title or determined in Step 5 (e.g. `01`)

## Step 2: Download Video from Fathom

First check if `~/Brains/brain/${VIDEO_NAME}.mp4` already exists and is > 1MB. If so, skip this step.

Otherwise:

```bash
cd ~/Brains/brain && python3 ~/.claude/skills/fathom/scripts/download_video.py \
  "${SHARE_URL}" --output-name "${VIDEO_NAME}"
```

After download, verify the mp4 exists and is > 1MB:
```bash
ls -la ~/Brains/brain/${VIDEO_NAME}.mp4
```

If download fails, stop and report. This is a long-running operation (may take several minutes for a 2h video).

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

## Step 4: Generate Fact-Checked Russian Summary

Read the full Fathom transcript from `${FATHOM_FILE}`.

Generate a comprehensive Russian-language summary of the meeting with these requirements:
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

The description generated by `process_video.py`'s built-in LLM (Groq) is generic and low-quality for Russian content. Instead, generate the YouTube description yourself using the summary from Step 4.

Determine the meeting page URL: `https://agency-lab.glebkalinin.com/docs/claude-code-internal-XX/meetings/NN` (where XX = lab number, NN = meeting number).

Generate a YouTube description in this format:
```
${MEETING_TITLE}

[1-2 sentence overview of the meeting in Russian]

В этом видео:
- [bullet point 1 — key topic covered]
- [bullet point 2]
- ...
- [bullet point 8-10 max]

Материалы и конспект занятия:
https://agency-lab.glebkalinin.com/docs/claude-code-internal-XX/meetings/NN

Сообщество AGENCY — практики AI-агентов:
https://agency-lab.glebkalinin.com

#ClaudeCode #AI #Anthropic #Claude #AIагенты #программирование
```

Then update the video on YouTube using the API via `auth.py` (which manages `token.pickle` with `youtube.force-ssl` scope):

```python
cd ~/ai_projects/youtube-uploader && PYTHONPATH=. python3 -c "
from auth import get_authenticated_service
youtube = get_authenticated_service()
resp = youtube.videos().list(part='snippet', id='VIDEO_ID').execute()
snippet = resp['items'][0]['snippet']
snippet['title'] = MEETING_TITLE
snippet['description'] = DESCRIPTION
snippet['tags'] = ['Claude Code', 'Claude', 'Anthropic', 'AI', 'AI агенты', 'программирование', 'Claude Code Lab', 'MCP']
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

Known playlist IDs (for reference):
- Claude Code Lab 03: `PLZNP0SKU2Sqic4njcSQemmyrVLHZ4C_iT`
- Claude Code Lab 02: `PLZNP0SKU2SqizoM9_7jMjgae2cvjGN9bQ`
- Claude Code Lab: `PLZNP0SKU2Sqga_EjxAW_OxnqaUk1ZGfXU`

Replace `LAB_NUMBER` with the two-digit lab number (e.g. `03`). The playlist name must match exactly (e.g. "Claude Code Lab 03").

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

```bash
cd ~/Sites/agency-docs && git add . && git commit -m "Add meeting NN" && git push
```

Replace `NN` with the actual meeting number from Step 5 output.

This triggers Vercel deployment automatically.

## Step 7: Verify Vercel Deployment

Wait ~90 seconds after push, then check deployment status:

```bash
gh api repos/glebis/agency-docs/commits/COMMIT_HASH/status --jq '{state, total_count}'
gh api repos/glebis/agency-docs/commits/COMMIT_HASH/statuses --jq '.[0] | {state, description}'
```

- If `state: success` — deployment is live.
- If `state: failure` — check the build error locally with `cd ~/Sites/agency-docs && npm run build 2>&1 | tail -20`, fix, and re-push.
- If `state: pending` — wait another 60 seconds and re-check.

## Pipeline Summary

After completion, report:
1. Fathom transcript path
2. Downloaded video path
3. YouTube URL
4. Generated MDX path
5. Git commit hash
6. Vercel deployment status (success/failure)

## Error Recovery

- **Step 1 fail (no transcript)**: Run calendar-sync, retry once. If still missing, stop.
- **Step 2 fail (download)**: Check if share_url is valid. Report ffmpeg errors.
- **Step 3 fail (upload)**: Check YouTube OAuth tokens, Playwright installation. Report specific error. Do NOT try `source venv/bin/activate`.
- **Step 4 fail (summary)**: Proceed with English summary if Russian generation fails.
- **Step 5 fail (MDX)**: Check that fathom_url exists in frontmatter. Check docs_dir exists.
- **Step 6 fail (git)**: Report conflict details. Do not force-push.

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
