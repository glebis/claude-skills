---
name: agency-docs-updater
description: End-to-end pipeline for publishing Claude Code lab meetings. Accepts optional args: date (YYYYMMDD, "yesterday", "today") and lab number (e.g. "04"). Examples: "yesterday 04", "20260420 05", "04" (today, lab 04), "" (today, auto-detect lab).
---

# Agency Docs Updater

Execute ALL steps automatically in sequence. Only pause if a step fails and cannot be recovered. Read `references/learnings.md` before starting for known pitfalls.

**Configuration**: paths are read from `.env` in the skill root (see `.env.example`). Defaults work for the standard setup. Key env vars: `VAULT_DIR`, `DOCS_SITE_DIR`, `YOUTUBE_UPLOADER_DIR`, `PRESENTATIONS_DIR`, `SKILLS_REPO_DIR`, `SKILLS_LOCAL_DIR`, `ZOOM_CREDENTIALS_DIR`, `GITHUB_REPO`, `SITE_DOMAIN`.

**Dependencies** (verify these exist before running):
- [zoom](https://github.com/glebis/claude-skills/tree/main/zoom) — Zoom recording download (`scripts/zoom_meetings.py`)
- [fathom](https://github.com/glebis/claude-skills/tree/main/fathom) — Fathom video fallback (`scripts/download_video.py`)
- [nano-banana](https://github.com/glebis/claude-skills/tree/main/nano-banana) — thumbnail overlay generation (`scripts/generate_image.sh`)
- [calendar-sync](~/.claude/skills/calendar-sync) — local-only, calendar event sync (`sync.sh`)
- [youtube-uploader](https://github.com/glebis/youtube-uploader) — video processing, upload, and YouTube API auth

## Step 0: Parse Arguments & Load Config

Load `.env` from skill root. Then split `args` by whitespace:
- 8-digit token (`YYYYMMDD`) → `DATE`
- "yesterday" → `DATE = $(date -v-1d +%Y%m%d)`
- "today" or missing → `DATE = $(date +%Y%m%d)`
- 2-digit token (`NN`) or `lab-NN` → `LAB_FILTER`

Expand env vars for paths used in subsequent steps:
```bash
VAULT_DIR="${VAULT_DIR:-$HOME/Brains/brain}"
DOCS_SITE_DIR="${DOCS_SITE_DIR:-$HOME/Sites/agency-docs}"
YOUTUBE_UPLOADER_DIR="${YOUTUBE_UPLOADER_DIR:-$HOME/ai_projects/youtube-uploader}"
SKILLS_REPO_DIR="${SKILLS_REPO_DIR:-$HOME/ai_projects/claude-skills}"
SKILLS_LOCAL_DIR="${SKILLS_LOCAL_DIR:-$HOME/.claude/skills}"
ZOOM_CREDENTIALS_DIR="${ZOOM_CREDENTIALS_DIR:-$HOME/.zoom_credentials}"
PRESENTATIONS_DIR="${PRESENTATIONS_DIR:-$HOME/ai_projects/claude-code-lab}"
GITHUB_REPO="${GITHUB_REPO:-glebis/agency-docs}"
SITE_DOMAIN="${SITE_DOMAIN:-agency-lab.glebkalinin.com}"
```

## Step 1: Find Fathom Transcript

If `LAB_FILTER` is set: `${VAULT_DIR}/${DATE}-claude-code-lab-${LAB_FILTER}.md`
If empty: glob `${VAULT_DIR}/${DATE}-claude-code-lab-*.md` (pick most recent by mtime).

If missing: run `${SKILLS_LOCAL_DIR}/calendar-sync/sync.sh`, re-check, stop if still missing.

Extract from YAML frontmatter and store:
- `FATHOM_FILE`, `SHARE_URL`, `MEETING_TITLE`, `DATE`, `LAB_NUMBER`
- `VIDEO_NAME` = `${DATE}-claude-code-lab-${LAB_NUMBER}`
- `TRANSCRIPT_LANG` = auto-detect from first ~50 lines (Cyrillic ratio > 0.3 → `ru`, else `en`)

## Step 2: Download Video

Skip if `${VAULT_DIR}/${VIDEO_NAME}.mp4` exists and is > 1MB.

**Primary — Zoom:**
```bash
python3 ${SKILLS_REPO_DIR}/zoom/scripts/zoom_meetings.py recordings \
  --start ${DATE:0:4}-${DATE:4:2}-${DATE:6:2} \
  --end $(date -j -v+1d -f %Y%m%d ${DATE} +%Y-%m-%d) \
  --show-downloads 2>&1
```
Find the MP4 URL, then:
```bash
TOK=$(python3 -c "import json,pathlib; print(json.load(open(pathlib.Path('${ZOOM_CREDENTIALS_DIR}')/'.zoom_credentials/oauth_token.json'))['access_token'])")
curl -L -H "Authorization: Bearer ${TOK}" -o ${VAULT_DIR}/${VIDEO_NAME}.mp4 "${MP4_DOWNLOAD_URL}"
```

**Fallback — Fathom** (if no Zoom recording):
```bash
cd ${VAULT_DIR} && python3 ${SKILLS_LOCAL_DIR}/fathom/scripts/download_video.py \
  "${SHARE_URL}" --output-name "${VIDEO_NAME}"
```

## Step 3: Upload to YouTube

```bash
cd ${YOUTUBE_UPLOADER_DIR} && \
python3 process_video.py \
  --video ${VAULT_DIR}/${VIDEO_NAME}.mp4 \
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

Generate YouTube description from the summary in `${TRANSCRIPT_LANG}`. Meeting page URL: `https://${SITE_DOMAIN}/docs/claude-code-internal-${LAB_NUMBER}/meetings/${MEETING_NUMBER}`

Update title, description, tags via YouTube API, then add video to playlist "Claude Code Lab ${LAB_NUMBER}" (auto-created if it does not exist).

## Step 5: Generate MDX

```bash
python3 ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/update_meeting_doc.py \
  ${FATHOM_FILE} "${YOUTUBE_URL}" ${SCRATCHPAD}/summary.md
```

**Before running**: check if a placeholder MDX already exists for today's date (`grep -l` in `meetings/`). If so, use `-n NN --update` to target it.

**After running**:
1. Strip appended Marp content (everything after summary's closing `---` before `<!-- _class: lead -->`)
2. If `${PRESENTATIONS_DIR}/lesson-generator/${DATE}.html` exists, copy to `${DOCS_SITE_DIR}/public/${DATE}-claude-code-lab-${LAB_NUMBER}.html` and add link in MDX
3. Replace frontmatter placeholders (`[Название встречи]`, `[Краткое описание встречи]`, `[Дата встречи]`)
4. If `TRANSCRIPT_LANG=en`, rewrite MDX with English labels (script defaults to Russian)
5. Verify: `cd ${DOCS_SITE_DIR} && npm run build 2>&1 | tail -5`

## Step 6: Commit and Push

Only stage pipeline files — never `git add .`:
```bash
cd ${DOCS_SITE_DIR}
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
until [ "$(gh api repos/${GITHUB_REPO}/commits/${COMMIT_HASH}/status --jq '.state')" != "pending" ]; do sleep 15; done
```

Run with `run_in_background: true`. On failure: fix locally, re-push, restart this step.

## Step 8: Verify in Browser

Load `mcp__claude-in-chrome__*` tools via ToolSearch. Open `https://${SITE_DOMAIN}/docs/claude-code-internal-${LAB_NUMBER}/meetings/${MEETING_NUMBER}`, wait 5s, screenshot. Verify YouTube embed is visible. If not: check VIDEO_ID, wait for YouTube processing, or re-upload.

## Pipeline Report

After completion, report: Fathom path, video path, YouTube URL, MDX path, commit hash, deploy status, embed verification.
