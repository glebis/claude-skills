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
- slug token (e.g. `ai-design`, `claude-code`) → `LAB_SLUG` (overrides env; default `claude-code`)

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
LAB_SLUG="${LAB_SLUG:-claude-code}"   # e.g. ai-design for the AI Design Lab
LAB_TITLE="${LAB_TITLE:-$(echo $LAB_SLUG | tr '-' ' ' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1' | sed 's/^Ai /AI /')}"  # "Claude Code", "AI Design"
```

### Step 0a: Preflight (recommended)

Run the preflight doctor to catch the three common mid-pipeline failures up front (missing youtube-uploader Python deps, missing Playwright/chromium, dead Groq key):

```bash
bash ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/preflight.sh
```

Hard blockers (deps/Playwright) exit non-zero with the exact fix command — run it, then re-run preflight. A dead Groq key is a soft warning: the LLM metadata step will 401, so plan to supply title/description/tags manually (build a `VideoConfig` and call `upload.py` directly, then set the thumbnail and playlist separately).

## Step 1: Find Fathom Transcript

Resolve with the script. Transcripts live in `${VAULT_DIR}/Sessions/` since the 2026-06-12 restructure, and naming differs per lab (`claude-code-lab-05`, `goal-driven-ai-01`, `goal-driven-design`). The patterns are `vault_names` in `labs.json`:
```bash
python3 ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/find_transcript.py ${DATE} [--slug ${LAB_SLUG}] [--lab ${LAB_FILTER}] --json
# → {"path": ".../Sessions/20261010-goal-driven-ai-01.md", "slug": "goal-driven-ai", "lab": "01"}
```
Use its `slug` as `LAB_SLUG` and `lab` as `LAB_NUMBER` (pass `--lab` to `update_meeting_doc.py` too).

If missing: run `${SKILLS_LOCAL_DIR}/calendar-sync/sync.sh` and re-check. If calendar-sync finds nothing, check that `icalBuddy eventsToday` doesn't say "No calendars." (calendar access lost). Then check the other sources before stopping. **No Fathom recording is a normal case** (GDA 01 #02): Zoom cloud has the video (`zoom_meetings.py recordings`) and Wispr Flow has the text (`flow.sqlite` Meetings + `meetings/<id>/refined.ndjson`). Write `Sessions/${DATE}-<vault_name>.md` from Wispr's refined text, with a frontmatter note on its source, late start and clock. `update_meeting_doc.py` no longer requires a Fathom URL. Zoom cloud processing of a 2.5 h meeting took ~2 h 10 min (file shows "processing", 0 MB, empty `recording_end`). Publish the summary first and the video second rather than blocking.

Extract from YAML frontmatter and store:
- `FATHOM_FILE`, `SHARE_URL`, `MEETING_TITLE`, `DATE`, `LAB_NUMBER`
- `VIDEO_NAME` = `${DATE}-${LAB_SLUG}-lab-${LAB_NUMBER}`
- `TRANSCRIPT_LANG` = auto-detect from first ~50 lines (Cyrillic ratio > 0.3 → `ru`, else `en`)

**Resolve the lab layout FIRST** — paths, page URLs, and playlist names differ per lab. Never build them by hand; resolve through the registry:

```bash
python3 ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/lab_layout.py ${LAB_SLUG} --lab ${LAB_NUMBER} --meeting ${MEETING_NUMBER} --json
# → meetings_dir (relative to DOCS_SITE_DIR), page_url, playlist, lang, thumbnail_style,
#   preserve_placeholder_frontmatter, registered
```

The registry is `labs.json` in the skill root (claude-code legacy layout, GDD RU `goal-driven-design-ru`, GDD EN, Goal-Driven AI `goal-driven-ai-NN`). `update_meeting_doc.py` and `rebuild_aggregations.py` resolve through it automatically. Unregistered slugs fall back to the legacy `{slug}-internal-{lab}` scheme with a warning — add new labs to `labs.json`, don't improvise paths. Use `playlist` for Step 4b (search the existing playlist list by this exact name before creating), `page_url` for Step 4b/8, `lang` for summary/MDX language, honor `preserve_placeholder_frontmatter` (GDD placeholders carry curated `toolkit:` frontmatter — merge, never overwrite) and `preserve_placeholder_body` (Goal-Driven AI pages carry a curated plan + slides link — insert sections, never regenerate). `thumbnail_style` + `brand` + `cover_formats` drive Step 3b.

**Determine `MEETING_NUMBER`**: check existing MDX files in `${DOCS_SITE_DIR}/${MEETINGS_DIR}/` (`meetings_dir` from `lab_layout.py`) for a placeholder with today's date. If found, use that number. Otherwise, check file content sizes to find the next empty slot. Store as zero-padded two-digit string (e.g. `04`). This variable is used in Steps 3b, 4b, 5, 6, and 8.

## Step 2: Download Video

Skip if `${VAULT_DIR}/${VIDEO_NAME}.mp4` exists and is > 1MB.

**Note**: Zoom recordings may take ~15 minutes to process after a meeting ends. If the Zoom API returns no recordings, wait and retry before falling back to Fathom.

**Primary — Zoom:**
```bash
python3 ${SKILLS_REPO_DIR}/zoom/scripts/zoom_meetings.py recordings \
  --start ${DATE:0:4}-${DATE:4:2}-${DATE:6:2} \
  --end $(date -j -v+1d -f %Y%m%d ${DATE} +%Y-%m-%d) \
  --show-downloads 2>&1
```
Find the MP4 URL, then:
```bash
TOK=$(python3 -c "import json,pathlib; print(json.load(open(pathlib.Path('${ZOOM_CREDENTIALS_DIR}')/'oauth_token.json'))['access_token'])")
curl -L -H "Authorization: Bearer ${TOK}" -o ${VAULT_DIR}/${VIDEO_NAME}.mp4 "${MP4_DOWNLOAD_URL}"
```

**Fallback — Fathom** (if no Zoom recording):
```bash
cd ${VAULT_DIR} && python3 ${SKILLS_LOCAL_DIR}/fathom/scripts/download_video.py \
  "${SHARE_URL}" --output-name "${VIDEO_NAME}"
```

## Step 3: Upload to YouTube

### Step 3-pre: Edit the recording (silences, pauses, context)

Every recording gets a context-aware edit before upload: dead air before the meeting, pauses, frozen-screen silences, participant exercise time and breaks are removed. Demos where the screen is moving are kept. The edit runs in two phases so decisions can be reviewed before anything is cut.

**1. Get a timestamped transcript for context.** Compare candidates with `scripts/compare_transcripts.py A B`: it reports text-aligned clock steps, tech-term spelling and hallucinations. Rule of thumb from GDA 01: Fathom (or Zoom) for **timing**, Wispr Flow for **text and proper nouns**; Wispr's clock skips paused time, so never cut video by it. The vault Fathom `.md` has NO timestamps, so it can't be used. Priority: Zoom VTT from the same Zoom recording (exact alignment; `zoom_meetings.py recordings --show-downloads` lists `TRANSCRIPT`/`.vtt`) → Fathom JSON (`FathomClient.get_transcript(id)`, alignment estimated automatically) → none (`audio + screen` only; no exercise/break/tech classes).

**2. Analyze** (~5–10 min for 2 h; run in background):
```bash
python3 ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/edit_video.py analyze ${VAULT_DIR}/${VIDEO_NAME}.mp4 \
  --transcript <zoom.vtt|fathom.json> -o ${SCRATCHPAD}/${VIDEO_NAME}.edl.json
```
It prints an edit plan (minutes removed per class) and a **Needs review** table. Check the `offset` line: below 40% match means the transcript is misaligned, so drop to `--offset 0` or use the VTT.

**3. Review (you, not the script).** For each review row, read `before`/`after` in the EDL and decide:
- `exercise`: cut, unless the host talks participants through it (then set `approved: false`).
- `demo` > 60 s: keep the head and tail unless the wait itself is the lesson (e.g. showing that agents are slow).
- `tech`: approve only a genuine "can you see my screen?" exchange; never a rhetorical «секундочку».
Edit `approved` in the JSON. If the plan removes > 35%, look at it again before raising `--max-remove`.

**4. Apply** (single-pass re-encode; every cut lands inside silence, so no clicks; A/V sync is preserved even for variable-frame-rate Zoom files):
```bash
python3 ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/edit_video.py apply ${VAULT_DIR}/${VIDEO_NAME}.mp4 \
  ${SCRATCHPAD}/${VIDEO_NAME}.edl.json -o ${VAULT_DIR}/${VIDEO_NAME}.edited.mp4
```
Upload the `.edited.mp4`.

**5. Timestamps after editing.** Source-transcript times no longer match the video. Never remap them. Re-transcribe the edited file with `GROQ_API_KEY=… scripts/transcribe_cut.py EDITED.mp4 -o edited.json --slug ${LAB_SLUG}`. It passes the lab's `asr_glossary` (labs.json) as the Whisper prompt (on GDA 01 it got "Ollama" right where Fathom and Wispr both failed) and drops known Whisper credit hallucinations. Take YouTube chapters (`detect_lesson_start.py` on the new transcript: `0:00 Начало` / `MM:SS Презентация`) and the publication transcript timecodes from that.

`trim_leading_silence.sh` and `cut_spans.py --remove A-B` still work for a quick manual fix.

`detect_lesson_start.py` counts only the **host's** phrases (Fathom JSON speakers). `lesson_start_review: true` (start later than 10 min) means read the context and never auto-trim: a participant's «всем привет» at 16:31 once nearly cut the recording notice. Pre-lesson small talk is an `editorial` cut you add to the EDL yourself after reading it.

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
Extract `VIDEO_ID` from the URL (the part after `?v=` or last path segment).

### Step 3a: Verify Upload (REQUIRED)

After extracting `VIDEO_ID`, verify the video actually exists on YouTube before proceeding. Videos can silently fail processing or get auto-deleted by YouTube's content review. The same check **trashes the local recordings, but only when it fully passes** (run in background; processing of a 2 h video takes ~10 min):

```bash
${YOUTUBE_UPLOADER_DIR}/.venv/bin/python ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/verify_upload.py ${VIDEO_ID} \
  --uploaded ${VAULT_DIR}/${VIDEO_NAME}.edited.mp4 \
  --trash ${VAULT_DIR}/${VIDEO_NAME}.mp4 ${VAULT_DIR}/${VIDEO_NAME}.edited.mp4   # every local copy, incl. split parts
```

"Fully passes" = not rejected/failed, `uploadStatus=processed` AND `processingStatus=succeeded`, and YouTube's duration matches `--uploaded` within 5 s (catches uploading the wrong file, e.g. one part of a split recording). Files go to the Trash via `trash`, never `rm`.

| exit | meaning | next |
|---|---|---|
| 0 | verified; files trashed | proceed |
| 2 | still processing after `--wait` (default 1200 s); files kept | continue Steps 3b/4/4b; re-run this before marking the meeting published |
| 1 | rejected, failed, or wrong duration; files kept | `rm processed/metadata/${VIDEO_NAME}.json`, re-upload with `--resume-from upload` (or upload the right file), re-verify |

Do NOT proceed to MDX or thumbnail steps with a VIDEO_ID that exited 1. If you re-cut after a pass, the files are in the Trash; Zoom cloud keeps the original.

**Start Step 4 in parallel** — summary doesn't depend on YouTube URL.

### Step 3b: Lab-Style Thumbnail (REQUIRED)

**Always run this step** — it replaces the generic thumbnail from `process_video.py` with the branded lab template. The generic thumbnail is NOT acceptable for publishing.

**Prerequisites**: `VIDEO_ID` must be known (wait for Step 3 to complete if needed).

**Branch on the layout's `thumbnail_style`:**
- `brand` → follow `references/brand-covers.md`: `scripts/brand_cover.py render ${BRAND} …` composes the site's own art kit, fonts and `design.tokens.json` into every format in `cover_formats` (YouTube + OG). No Nano Banana, no recolour unless the composition needs a generated layer. Then upload as in step 6 below.
- `site-token` (GDD, legacy) → manual: the lab's tokens at `${DOCS_SITE_DIR}/design.tokens.json` per `learnings.md`. Migrate by writing a `brands/` profile.
- `claude-code` (default) → the dark editorial flow below.

Claude Code flow — follow `references/thumbnail-guide.md`:
1. Generate Nano Banana overlay image (topic-specific prompt from the guide's prompt patterns)
2. Read/inspect raw image to confirm background color, then recolor lines to orange (#e85d04)
3. Write a **temporary** HTML file (e.g. `/tmp/lab-meeting-${MEETING_NUMBER}.html`) based on `${YOUTUBE_UPLOADER_DIR}/templates/images/lab-meeting.html` — update meeting number, topic hero text, bullet descriptions, date. **Do not edit the original template in-place.**
4. Render with Playwright at 1280×720 → `${YOUTUBE_UPLOADER_DIR}/processed/thumbnails/${VIDEO_NAME}.jpg`
5. Read/inspect the rendered thumbnail to verify layout before uploading
6. Upload to YouTube: use `VIDEO_ID` extracted from Step 3

Do NOT skip this step or rely on the `process_video.py` thumbnail.

## Step 4: Generate Fact-Checked Summary

Read `${FATHOM_FILE}`. Generate a structured summary **in `${TRANSCRIPT_LANG}`**:
- `##` section headers, bullet points, code examples where relevant
- Technical terms in English (MCP, Skills, Claude Code, etc.)
- **Exclude personal scheduling details**
- **Exclude operator/pipeline notes**: recording source, trimming or cutting, silence/preamble removal, remuxing or re-encoding, transcript synchronization, upload retries, and other production mechanics belong only in the internal Pipeline Report — never in the published summary or meeting page
- Verify product, company, and person names against authoritative project context or explicit user corrections before publishing; do not trust ASR/LLM normalization for proper nouns
- Sanitize for MDX: escape `<`, `>`, and bare `{` characters that would break MDX compilation

Fact-check Claude Code feature claims using `claude-code-guide` subagent (if available; skip fact-checking if the agent is not accessible). Save corrected summary to scratchpad as `summary.md`.

## Step 4b: Update YouTube Metadata

**After both Step 3 and Step 4 complete.** `VIDEO_ID`, `MEETING_NUMBER`, and `LAB_NUMBER` must all be determined before this step. Read `references/youtube-api.md` for description format and API snippets.

Generate YouTube description from the summary. Use the language-appropriate template:

- **If `TRANSCRIPT_LANG=en`**: English labels ("In this video:", "Course materials and session notes:")
- **If `TRANSCRIPT_LANG=ru`**: Russian labels ("В этом видео:", "Материалы и конспект занятия:")

Do NOT mix languages in a single description.

Meeting page URL: `https://${SITE_DOMAIN}${PAGE_URL}` where `PAGE_URL` is `page_url` from `lab_layout.py` (Step 1). Never build it by hand: `/${LAB_SLUG}-lab-NN/` 404s for labs like `goal-driven-ai` (`/goal-driven-ai-01/meetings/NN`).

Update title, description, tags via YouTube API, then add the video to the layout's `playlist` (search the full playlist list by exact name first; create unlisted only if missing).

## Step 5: Generate MDX

```bash
LAB_SLUG=${LAB_SLUG} python3 ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/update_meeting_doc.py \
  ${FATHOM_FILE} "${YOUTUBE_URL}" ${SCRATCHPAD}/summary.md
```

**Before running**: check if a placeholder MDX already exists for today's date (`grep -l` in `meetings/`). If so, use `-n ${MEETING_NUMBER} --update` to target it.

**Mark the meeting published (explicit gate).** Once the page is deployed AND the recording is processed and embeddable, set the frontmatter: `merge_meeting_doc.py MDX --set publication_status=published --set published_at=<ISO with offset, now>`. The curriculum feed (`/api/curriculum/<cohort>`) treats everything else as `draft`. PiBot's `LabPublicationSync` watches that feed and composes personalized participant follow-ups for published meetings, so flipping this has effects beyond the site. Never set it before the recording works, and never to force an announcement.

**Existing pages are merged, never overwritten.** If `meetings/${MEETING_NUMBER}.mdx` already exists (placeholder, preliminary plan, slides link), the script merges automatically via `scripts/merge_meeting_doc.py`. It owns only three managed blocks, `{/* agency:recording|summary|transcript */}`: on the first run it takes over a matching section (`## Видео`/`## Запись`/`## Конспект`/`## Summary`…) or inserts after the date line. Everything else stays byte for byte. Pending notes ("Запись появится…") are dropped, and frontmatter is only filled where a value is a placeholder. Re-runs are idempotent. Useful flags: `--title/--description` (fill placeholders), `--transcript-url`, `--dry-run` (print diff). `--overwrite` is the old destructive rewrite; use it only for a page known to be junk. Merge mode never appends Marp content.

**After running**:
1. Strip appended Marp content (everything after summary's closing `---` before `<!-- _class: lead -->`) — MDX breaks on HTML comments (`<!-- -->`), unescaped `<`, and bare `{` characters
2. Check for presentation file: look in `${PRESENTATIONS_DIR}/presentations/lab-${LAB_NUMBER}/` (set `PRESENTATIONS_DIR` per lab; the ai-design lab keeps decks elsewhere — skip if unset for the slug) and `${PRESENTATIONS_DIR}/lesson-generator/` for files matching `${DATE}`. If found, copy to `${DOCS_SITE_DIR}/public/${DATE}-${LAB_SLUG}-lab-${LAB_NUMBER}.html` and add link in MDX
3. Replace frontmatter placeholders (`[Название встречи]`, `[Краткое описание встречи]`, `[Дата встречи]`)
4. If `TRANSCRIPT_LANG=en`, rewrite the MDX entirely with English labels — the script defaults to Russian and the translation fallback produces broken mixed-language output
5. Verify: `bash ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/safe_build.sh` (wraps `npm run build`; auto-clears a corrupt `.next` cache and retries once on the `reading 'hash'` / ENOSPC error)
6. Search the generated MDX for operator/pipeline notes (recording provenance, edit/cut details, encoding, transcript synchronization, upload mechanics) and remove them before publication
7. Search the MDX, public transcript, YouTube metadata, and thumbnail copy for known ASR variants of corrected proper nouns; use the canonical spelling consistently across every public surface

## Step 6: Commit and Push

**Run the guard first, and stop if it fails:**
```bash
bash ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/publish_preflight.sh
```
It refuses when the checkout isn't on `main`, when HEAD has commits not on `origin/main`, and it prints production's latest deploy for comparison. Background (GDA 01, 2026-10-10): the checkout was on `codex/companion-t-shaped`, and production ran that branch via Vercel CLI deploys while `origin/main` lagged 22 commits behind. Pushing only the meeting onto `main` would have rolled production back; pushing the branch merged it without a PR. Other sessions edit this repo concurrently (`codex/*` branches, temp worktrees). On a STOP, show the user the branch, the commits and production's source, and ask. Safe pattern when `main` is right but the checkout is busy: `git worktree add --detach <tmp> origin/main`, copy only the pipeline files in, commit, push, remove the worktree.

Only stage pipeline files — never `git add .`. Default to a temp worktree from `origin/main`; never stash, rebase or switch branches in the shared checkout (other sessions work there):
```bash
cd ${DOCS_SITE_DIR} && git fetch -q origin main
W=${SCRATCHPAD}/agency-main && git worktree add -q --detach $W origin/main
# build prerequisites the worktree lacks (all gitignored): reuse deps only if lockfiles match;
# the Clerk key lives in .env.production.local (a prod build fails without it)
cmp -s $W/package-lock.json package-lock.json && ln -s ${DOCS_SITE_DIR}/node_modules $W/node_modules
ln -s ${DOCS_SITE_DIR}/.env.production.local $W/.env.production.local
# run update_meeting_doc.py (pass the worktree as docs_dir) / merge_meeting_doc.py and
# rebuild_aggregations.py with DOCS_SITE_DIR=$W, then DOCS_SITE_DIR=$W safe_build.sh
cd $W && git add ${MEETINGS_DIR}/${MEETING_NUMBER}.mdx content/docs/database.mdx content/docs/glossary.mdx \
  public/data/meetings.json .agency-glossary.json
git commit -m "Add ${LAB_TITLE} Lab ${LAB_NUMBER} Meeting ${MEETING_NUMBER}"
git fetch -q origin main && git merge-base --is-ancestor origin/main HEAD && git push origin HEAD:refs/heads/main
cd ${DOCS_SITE_DIR} && git worktree remove --force $W
```
Production must be deploying from `main` for this to be safe. `publish_preflight.sh` prints production's created time next to `origin/main`'s last commit; they should be seconds apart.

Store `COMMIT_HASH=$(git rev-parse HEAD)` for Step 7.

## Step 7: Wait for Vercel Deploy

```bash
TIMEOUT=300; ELAPSED=0
until [ "$(gh api repos/${GITHUB_REPO}/commits/${COMMIT_HASH}/status --jq '.state' 2>/dev/null || echo 'pending')" != "pending" ]; do
  sleep 15; ELAPSED=$((ELAPSED+15))
  [ "$ELAPSED" -ge "$TIMEOUT" ] && echo "Deploy timeout after ${TIMEOUT}s" && break
done
DEPLOY_STATE=$(gh api repos/${GITHUB_REPO}/commits/${COMMIT_HASH}/status --jq '.state')
echo "Deploy state: ${DEPLOY_STATE}"
```

Run with `run_in_background: true`. If state is `failure` or `error`: check Vercel logs (`vercel logs`), fix locally, re-push, restart this step.

## Step 8: Verify in Browser

Open `https://${SITE_DOMAIN}${PAGE_URL}` in a browser (via chrome automation tools or manually). Verify YouTube embed is visible. If not: check VIDEO_ID, wait for YouTube processing, or re-upload.

## Step 9: Rebuild Site-Wide Aggregations

After the new meeting is committed (Step 6), regenerate the three site-wide aggregations from **all** meetings so the new one is reflected: the **database** (meetings index), the **glossary**, and the **global library** of links.

```bash
python3 ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/rebuild_aggregations.py
```

The script reads the same `.env` paths and writes (paths configurable via `AGG_*` env vars):
- `content/docs/database.mdx` + `public/data/meetings.json` — index of every meeting
- `content/docs/glossary.mdx` (definitions persisted in `.agency-glossary.json`)
- `content/docs/library.mdx` — deduplicated external links across all meetings

**Handle new glossary terms**: the script prints `→ N NEW term(s) need definitions` for terms it has never seen. For each, write a one-line definition into `${DOCS_SITE_DIR}/.agency-glossary.json` (keep technical terms in English; match the page language otherwise), then re-run the script so the glossary MDX regenerates with the definitions. Leave already-defined terms untouched — the store is the source of truth.

**Then**: `bash ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/safe_build.sh` to confirm the generated MDX compiles (auto-recovers from a corrupt `.next` cache), stage the changed aggregation files (the three MDX pages, `public/data/meetings.json`, and `.agency-glossary.json` — never `git add .`), and commit:
```bash
git add content/docs/database.mdx content/docs/glossary.mdx content/docs/library.mdx \
        public/data/meetings.json .agency-glossary.json
git commit -m "Rebuild aggregations after Lab ${LAB_NUMBER} Meeting ${MEETING_NUMBER}"
git push
```

This commit can be folded into Step 6's commit if you prefer a single push; either way it must land before re-running Step 7's deploy wait.

## Evals

After changing any script, run `python3 evals/run_evals.py` (46 deterministic cases, ~1 min; `--fast` skips renders and encodes; `--only edit,merge,cover,layout,upload`). Fixtures are synthesized: a lesson clip with known lead/pause/exercise/demo/dead-air spans plus a VTT, a VFR flash+beep sync probe, and a curated meeting page (`evals/fixtures/curated-meeting.mdx`). When a real run surprises you, add a `case_<group>_<name>` that reproduces it before fixing.

## Step 10: Announce the Published Recording via the Lab Bot (REQUIRED)

After the final deployment and browser verification, announce the recording and materials through the lab's configured Telegram bot. This is part of publication, not a separate reminder or scheduled task. Read `references/bot-announcement.md` and follow its verification and duplicate-prevention rules. Do not send on a build success, transcript completion, draft page, or unverified deployment alone.

Send with the skill's one-shot sender (it verifies `getMe`, writes a pending receipt before sending, refuses if any receipt exists, and records the message ID and permalink in `pibot/data/publication-receipts/`):
```bash
cd ~/ai_projects/pibot && OPENAI_API_KEY= SOPS_AGE_KEY_FILE=$HOME/.config/sops/age/keys.txt \
  npx tsx ${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts/announce_publication.ts --chat ${LAB_ANNOUNCE_CHAT_ID} \
  --meeting ${MEETING_NUMBER} --recording "${YOUTUBE_URL}" --lead "<one sentence: what the meeting did>" --published-at <ISO> \
  [--feed <layout feed_cohort> --page <layout page_url> --heading "<title>"]   # second tracks, e.g. the advanced group
```
The sender re-checks the LIVE feed and refuses (exit 5) unless the meeting is `published`; the receipt key is `feed|meeting|chat`, so Saturday 01 and advanced 01 never collide.
```
```
Telethon read-back can fail with `database is locked` when another process holds the session. Don't break it; ask the user to glance at the permalink.

For Goal-Driven AI 01 use **@agency_lab_companion_bot**, posting to **Goal-Driven AI 01 — Чат**. Include clickable recording and meeting-material links, a brief description of currently available companion features, and a button inviting participants to open the bot's private chat. Record the resulting Telegram message link in the Pipeline Report. Other labs require their own verified bot and destination mapping; never reuse this cohort's chat by default.

## Pipeline Report

After completion, report: Fathom path, video path, YouTube URL, MDX path, commit hash, deploy status, embed verification, and the aggregation rebuild (meeting count, any new glossary terms defined). Include bot announcement status, destination, and verified Telegram message link (or the exact blocking reason).

## Related: fan-out maintenance workflows

For **repo-wide** jobs across all past meetings — auditing every page for broken embeds/MDX defects, or backfilling/repairing incomplete meetings — see `references/workflows.md`. Those are fan-out [dynamic workflows](https://code.claude.com/docs/en/workflows.md) (one agent per meeting), run on demand, separate from this single-meeting pipeline.
