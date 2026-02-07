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
- `DATE` = YYYYMMDD string
- `VIDEO_NAME` = `${DATE}-claude-code-lab-02`

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

```bash
cd ~/ai_projects/youtube-uploader && source venv/bin/activate && \
python3 process_video.py \
  --video ~/Brains/brain/${VIDEO_NAME}.mp4 \
  --fathom-transcript ${FATHOM_FILE} \
  --upload
```

Key notes:
- `--fathom-transcript` makes it skip video transcription (uses Fathom transcript instead)
- `--upload` triggers YouTube + Yandex.Disk upload
- Handles: metadata generation, thumbnail creation, YouTube upload, Yandex upload

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
  --fathom-transcript ${FATHOM_FILE} --upload --resume-from upload
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
- **Step 3 fail (upload)**: Check YouTube OAuth tokens, venv activation. Report specific error.
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
