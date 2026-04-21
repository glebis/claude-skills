---
name: agency-docs-updater
description: End-to-end pipeline for publishing Claude Code lab meetings. Accepts optional args: date (YYYYMMDD, "yesterday", "today") and lab number (e.g. "04"). Examples: "yesterday 04", "20260420 05", "04" (today, lab 04), "" (today, auto-detect lab).
---

# Agency Docs Updater

Execute ALL steps automatically in sequence. Only pause if a step fails and cannot be recovered. Read `references/learnings.md` before starting for known pitfalls.

**Dependencies** (verify these exist before running):
- [zoom](https://github.com/glebis/claude-skills/tree/main/zoom) — Zoom recording download (`scripts/zoom_meetings.py`)
- [fathom](https://github.com/glebis/claude-skills/tree/main/fathom) — Fathom video fallback (`scripts/download_video.py`)
- [nano-banana](https://github.com/glebis/claude-skills/tree/main/nano-banana) — thumbnail overlay generation (`scripts/generate_image.sh`)
- [calendar-sync](~/.claude/skills/calendar-sync) — local-only, calendar event sync (`sync.sh`)
- [youtube-uploader](https://github.com/glebis/youtube-uploader) — video processing, upload, and YouTube API auth (`~/ai_projects/youtube-uploader/`)

## Step 0: Parse Arguments

Split `args` by whitespace:
- 8-digit token (`YYYYMMDD`) → `DATE`
- "yesterday" → `DATE = $(date -v-1d +%Y%m%d)`
- "today" or missing → `DATE = $(date +%Y%m%d)`
- 2-digit token (`NN`) or `lab-NN` → `LAB_FILTER`

## Step 1: Find Fathom Transcript

If `LAB_FILTER` is set: `~/Brains/brain/${DATE}-claude-code-lab-${LAB_FILTER}.md`
If empty: glob `~/Brains/brain/${DATE}-claude-code-lab-*.md` (pick most recent by mtime).

If missing: run `~/.claude/skills/calendar-sync/sync.sh`, re-check, stop if still missing.

Extract from YAML frontmatter and store:
- `FATHOM_FILE`, `SHARE_URL`, `MEETING_TITLE`, `DATE`, `LAB_NUMBER`
- `VIDEO_NAME` = `${DATE}-claude-code-lab-${LAB_NUMBER}`
- `TRANSCRIPT_LANG` = auto-detect from first ~50 lines (Cyrillic ratio > 0.3 → `ru`, else `en`)

## Step 2: Download Video

Skip if `~/Brains/brain/${VIDEO_NAME}.mp4` exists and is > 1MB.

**Primary — Zoom:**
```bash
python3 ~/ai_projects/claude-skills/zoom/scripts/zoom_meetings.py recordings \
  --start ${DATE:0:4}-${DATE:4:2}-${DATE:6:2} \
  --end $(date -j -v+1d -f %Y%m%d ${DATE} +%Y-%m-%d) \
  --show-downloads 2>&1
```
Find the MP4 URL, then:
```bash
TOK=$(python3 -c "import json,pathlib; print(json.load(open(pathlib.Path.home()/'.zoom_credentials/oauth_token.json'))['access_token'])")
curl -L -o ~/Brains/brain/${VIDEO_NAME}.mp4 "${MP4_DOWNLOAD_URL}?access_token=${TOK}"
```

**Fallback — Fathom** (if no Zoom recording):
```bash
cd ~/Brains/brain && python3 ~/.claude/skills/fathom/scripts/download_video.py \
  "${SHARE_URL}" --output-name "${VIDEO_NAME}"
```

## Step 3: Upload to YouTube

```bash
cd ~/ai_projects/youtube-uploader && \
python3 process_video.py \
  --video ~/Brains/brain/${VIDEO_NAME}.mp4 \
  --fathom-transcript ${FATHOM_FILE} \
  --title "${MEETING_TITLE}" \
  --upload
```

Run with `run_in_background: true` (10-30 min). On failure: `--resume-from upload`.

Extract `YOUTUBE_URL` from stdout (`✓ YouTube video: ...`) or `processed/metadata/${VIDEO_NAME}.json`.

**Start Step 4 in parallel** — summary doesn't depend on YouTube URL.

### Step 3b: Lab-Style Thumbnail

Read `references/thumbnail-guide.md` for the full thumbnail generation workflow (Nano Banana overlay → recolor → Playwright render → upload).

## Step 4: Generate Fact-Checked Summary

Read `${FATHOM_FILE}`. Generate a structured summary **in `${TRANSCRIPT_LANG}`**:
- `##` section headers, bullet points, code examples where relevant
- Technical terms in English (MCP, Skills, Claude Code, etc.)
- **Exclude personal scheduling details**

Fact-check Claude Code feature claims using `claude-code-guide` subagent. Save corrected summary to scratchpad as `summary.md`.

## Step 4b: Update YouTube Metadata

**After both Step 3 and Step 4 complete.** Read `references/youtube-api.md` for description format and API snippets.

Generate YouTube description from the summary in `${TRANSCRIPT_LANG}`. Meeting page URL: `https://agency-lab.glebkalinin.com/docs/claude-code-internal-${LAB_NUMBER}/meetings/${MEETING_NUMBER}`

Update title, description, tags via YouTube API, then add video to playlist (looked up by name "Claude Code Lab ${LAB_NUMBER}").

## Step 5: Generate MDX

```bash
python3 ~/.claude/skills/agency-docs-updater/scripts/update_meeting_doc.py \
  ${FATHOM_FILE} "${YOUTUBE_URL}" ${SCRATCHPAD}/summary.md
```

**Before running**: check if a placeholder MDX already exists for today's date (`grep -l` in `meetings/`). If so, use `-n NN --update` to target it.

**After running**:
1. Strip appended Marp content (everything after summary's closing `---` before `<!-- _class: lead -->`)
2. If `~/ai_projects/claude-code-lab/lesson-generator/${DATE}.html` exists, copy to `~/Sites/agency-docs/public/${DATE}-claude-code-lab-${LAB_NUMBER}.html` and add link in MDX
3. Replace frontmatter placeholders (`[Название встречи]`, `[Краткое описание встречи]`, `[Дата встречи]`)
4. If `TRANSCRIPT_LANG=en`, rewrite MDX with English labels (script defaults to Russian)
5. Verify: `cd ~/Sites/agency-docs && npm run build 2>&1 | tail -5`

## Step 6: Commit and Push

Only stage pipeline files — never `git add .`:
```bash
cd ~/Sites/agency-docs
git fetch origin main
BEHIND=$(git rev-list --count HEAD..origin/main)
if [ "$BEHIND" -gt 0 ]; then
  git stash push -m "agency-docs-updater: temp stash"
  git pull --rebase origin main
  git stash pop || true
fi
git add content/docs/claude-code-internal-${LAB_NUMBER}/meetings/${MEETING_NUMBER}.mdx public/${DATE}-claude-code-lab-${LAB_NUMBER}.html
git commit -m "Add Lab ${LAB_NUMBER} Meeting ${MEETING_NUMBER}"
git push
```

## Step 7: Wait for Vercel Deploy

```bash
until [ "$(gh api repos/glebis/agency-docs/commits/${COMMIT_HASH}/status --jq '.state')" != "pending" ]; do sleep 15; done
```

Run with `run_in_background: true`. On failure: fix locally, re-push, restart this step.

## Step 8: Verify in Browser

Load `mcp__claude-in-chrome__*` tools via ToolSearch. Open `https://agency-lab.glebkalinin.com/docs/claude-code-internal-${LAB_NUMBER}/meetings/${MEETING_NUMBER}`, wait 5s, screenshot. Verify YouTube embed is visible. If not: check VIDEO_ID, wait for YouTube processing, or re-upload.

## Pipeline Report

After completion, report: Fathom path, video path, YouTube URL, MDX path, commit hash, deploy status, embed verification.
