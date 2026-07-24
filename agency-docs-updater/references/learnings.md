# Learnings

## Fathom / recording selection (seen 2026-06-13, Lab 05 #12)
- **Wrong recording captured.** When 2+ Fathom/Zoom recordings exist for one event on the same day (e.g. a short pre-meeting test + the real session), calendar-sync may save the SHORT test recording into the session `.md` — tiny `duration` (e.g. `00:08`), empty body, wrong `fathom_id`/`share_url`. **Now mechanized:** `calendar-sync/sync_calendar.py` dedupes same-filename recordings keeping the longest, and warns (instead of silently skipping) when an existing file holds a different recording. If a stale wrong file predates the fix, delete it and re-run sync. Manual fallback: `python3 fathom/scripts/fetch.py --list` to find the real recording ID and rebuild.
- **Fathom fetch gotchas.** `fetch.py --id` paginates through ALL meetings to find one → hits `429 Too Many Requests`. Instead call the direct endpoints via `utils.FathomClient`: `c.get_transcript(id)` (`recordings/{id}/transcript`, returns a list of `{speaker:{display_name}, text, timestamp}`) and `c.get_summary(id)` (`recordings/{id}/summary`). The canonical `share_url` is the `fathom.video/share/...` link embedded inside the summary markdown.
- **Transcript format for the converter.** `youtube-uploader/fathom_converter.py` historically required a `## Transcript` header AND `**Speaker**: text` (colon OUTSIDE the bold). **Now mechanized:** the parser accepts both colon placements and a missing header (falls back to the whole body). Hand-rebuilt session files in the natural `**Name:** text` form just work.

## Pipeline
- Parallelize summary (Step 4) with YouTube upload (Step 3) — saves 10+ minutes
- `--resume-from upload` skips metadata/thumbnail regeneration on retry
- Always run `npm run build` locally before pushing — MDX errors cause Vercel deploy failures
- Zoom recordings may take ~15 min to process after meeting ends

## MDX pitfalls
- `update_meeting_doc.py` appends Marp presentation content with `<!-- -->` HTML comments — always strip everything after the summary. Use `head -N` truncation at the last valid `---` before `<!-- _class: lead -->`
- MDX breaks on HTML comments (`<!-- -->`), unescaped `<`, and bare `{` characters

## YouTube API
- Always pass `--title` from Fathom frontmatter — without it, the LLM generates poor/generic titles for Russian content
- `youtube.force-ssl` scope is needed for both uploads and metadata updates
- **Videos can silently disappear after upload.** On 2026-05-16, a video was uploaded successfully (got VIDEO_ID), but YouTube later deleted it (shows as "Deleted video" with `privacyStatusUnspecified`). Always run Step 3a verification after upload. If verification fails, re-upload before proceeding
- The YouTube oEmbed API (`youtube.com/oembed?url=...`) returns "Not Found" for deleted/private videos — useful quick check

## Meeting number detection
- Don't trust auto-detected meeting number blindly — placeholder MDX files may already exist. Check existing files by date content first, use `-n NN` to override

## Thumbnails
- Nano Banana with "pure black background" prompt usually returns black-bg + light lines — skip `-negate`
- Always inspect the raw image before recoloring — wrong assumptions flood the image with orange
- Use custom renderer config JSON with `imagePath` field

## English-language labs
- When `TRANSCRIPT_LANG=en`, rewrite the MDX entirely with English labels — `update_meeting_doc.py` defaults to Russian and the translation fallback produces broken mixed-language output
- Correct spelling: "WisprFlow" (https://wisprflow.ai/r/GLEB3)

## Git push
- Only stage pipeline-created files — never `git add .`
- If remote is ahead: `git stash push`, `git pull --rebase`, push, `git stash pop`

## Step 2/3 environment pitfalls (seen 2026-05-30, Lab 05 #08)
- **Preflight catches the first three (seen 2026-06-13).** `scripts/preflight.sh` checks youtube-uploader Python deps, the Playwright/chromium render path, and Groq key validity up front and prints the exact fix command. Run it before the pipeline (SKILL Step 0a). The items below are what it detects.
- **Missing Python deps (seen 2026-06-13).** `ModuleNotFoundError: No module named 'google_auth_oauthlib'` — youtube-uploader has no venv and the deps aren't in system python. Fix: `cd ${YOUTUBE_UPLOADER_DIR} && python3 -m pip install --user -r requirements.txt` (ignore unrelated pymemgpt version-conflict warnings). `token.json`/`token.pickle` exist so auth stays non-interactive afterward.
- `process_video.py` can fail at thumbnail step with `Executable doesn't exist … chrome-headless-shell` — Playwright browser missing. Fix: `cd ${YOUTUBE_UPLOADER_DIR} && npx playwright install chromium`, then re-run. It fails BEFORE upload, so nothing is lost.
- `update_meeting_doc.py` could false-match a presentation in `presentations/lab-NN/` even when the filename DATE differed from today (it picked most-recent-by-mtime). **Now mechanized:** it extracts the date from the transcript filename and only links a presentation whose filename contains that date; otherwise it skips the deck. No more manual Marp strip for unrelated decks.

## Build / deploy pitfalls
- **Mechanized:** use `scripts/safe_build.sh` instead of raw `npm run build` (SKILL Steps 5 & 9). It detects the corrupt-cache / ENOSPC failure, clears `.next`, and retries once.
- `npm run build` failing with `uncaughtException [TypeError: Cannot read properties of null (reading 'hash')]` is a corrupt/low-space `.next` cache, NOT an MDX error (MDX map step succeeds first). Fix: `trash .next` and rebuild.
- Root cause is often `ENOSPC: no space left on device` during prerender. Free space: `npm cache clean --force` (~3 GB) and `trash .next`. Need ~8–10 GB free for a clean build.
- Step 8 verification: `/claude-code-lab-NN/*` is Clerk-auth-gated (see `src/middleware.ts`), so anonymous `curl` returns 404 even for known-good published meetings. To verify: (a) confirm build compiled the page + deploy state=success, (b) the deployed page inlines a search index — `curl … | grep youtube.com/embed/${VIDEO_ID}` finds it even on the gated 404 shell, confirming the page is in the build. A live visual embed check needs an authenticated browser session.

## Aggregations (Step 9)
- `rebuild_aggregations.py` regenerates database/glossary/library from ALL meetings — it's idempotent, safe to re-run
- Glossary definitions live in `.agency-glossary.json`, NOT in the generated MDX — edit the store, then re-run. Definitions survive rebuilds; only genuinely new terms are flagged
- Generated MDX pages carry a `{/* GENERATED ... */}` banner — don't hand-edit them
- The acronym extractor strips URLs first so referral codes (e.g. `…/r/GLEB3`) aren't mistaken for terms; still skim the NEW-term list for noise before defining
- Per-meeting Fathom/YouTube links are intentionally excluded from the library (they're in the database) — the library is for external resources only
- Always `npm run build` after a rebuild — the generated MDX can break the deploy just like meeting MDX can

## Non-lab / community sessions (seen 2026-07-07)
- A session may not fit any lab slot (cross-cohort alumni meetup). Fathom saved only an 11-min fragment ("Impromptu Zoom Meeting") while Zoom had the full 87-min recording + VTT transcript. Always cross-check Zoom when the Fathom duration looks too short.
- For "YouTube only" publishing: build `VideoConfig` manually (Groq-free path), `upload_video(..., notify_subscribers=False)`, privacy `unlisted` — matches process_video.py defaults. Thumbnail template adapts fine: "Claude Code Lab · Community" / "Community Session" instead of meeting number.

## GDD / non-standard lab layouts (seen 2026-07-24, GDD RU #02)
- The GDD lab does NOT follow `${LAB_SLUG}-internal-${LAB_NUMBER}` — meetings live in `content/docs/goal-driven-design-ru/meetings/NN.mdx` (and `goal-driven-design-en/`). Placeholder MDX files exist for all 10 meetings with date lines like «23 июля 2026» — match by date, keep the placeholder's `toolkit:` frontmatter intact, only fix title/description.
- Vault naming for GDD: `${DATE}-ai-design-lab-01.md` (lab number = cohort 01), but the SITE slug is `goal-driven-design-ru`. Don't derive one from the other.
- calendar-sync only processes TODAY — it ignores date arguments. For yesterday's meeting, rebuild the vault file directly via `FathomClient` (`get_transcript(id)` + `get_summary(id)`, share_url from the summary markdown), frontmatter modeled on the previous meeting's file.
- YouTube playlists: check the FULL existing playlist list before creating one — «Goal-Driven Design Lab (RU)» already existed and held meeting 01; a freshly created playlist 404s on immediate `playlistItems.list` (propagation delay — retry after ~10-20 s, or insert without listing).
- Thumbnails: the lab has its own design token at `${DOCS_SITE_DIR}/design.tokens.json` (orange #ff6b35, dark-bg #0a0a0a, Geist Sans headings + Inter). Use IT, not the youtube-uploader template fonts (EB Garamond/JetBrains Mono, #e85d04) — those are the Claude Code Lab style. Brighten Nano Banana overlays (`magick -level 0%,55%`) before recoloring or they vanish at preview size.
- Publication transcript is a wanted artifact: merge consecutive same-speaker segments, `[HH:MM:SS]` timecodes, names shortened to «Имя Ф.» (site rule: no last names), targeted ASR fixes only → `public/transcripts/${DATE}-<slug>-NN-transcript.md`, linked from the meeting MDX.
- Pipeline can ship in stages: page + materials + transcript first (with «Запись обрабатывается» note), video embed as a second commit once upload verifies. Unblocks the page by ~an hour.

## Dead API keys (policy)
- When a required API key is invalid (e.g. Groq 401 in preflight): do NOT just silently work around it — ask the user for a fresh key via AppleScript dialog first: `osascript -e 'display dialog "Enter GROQ_API_KEY:" default answer "" with hidden answer'`, then use it for the run and offer to store it in the appropriate secrets file (SOPS). Only if the user declines/has no key, fall back to the manual `VideoConfig` path (title/description/tags hand-written).

## Disk space (seen 2026-07-24, GDD RU #02 — cost three lost downloads)
- The Fathom downloader needs ~2× the video size free (raw .ts + remuxed mp4). On failure it DELETES both the partial mp4 AND the raw .ts — an ENOSPC remux loses the whole download. Check `df` BEFORE starting; want ≥5 GB free for a ~1 h meeting.
- ffmpeg exit code 228 during remux = ENOSPC in disguise.
- disk-cleanup safe preset also trashes `~/Library/Caches/ms-playwright` — re-run `python3 -m playwright install chromium` after cleaning (Node's `npx playwright install` uses a DIFFERENT cache than Python playwright; each needs its own install).
- Long downloads: launch with `nohup ... & disown`, monitor by PID from a separate background loop. Plain `run_in_background` Bash tasks got killed twice mid-download (process dies with the task).

## Environment (seen 2026-07-07)
- `nano-banana/scripts/generate_image.sh` fails to decrypt secrets unless `SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt` is exported first.
- Disk-full during `npm install`/`npx playwright install` fails HALF-silently: node_modules ends up empty and chromium downloads but never extracts. After freeing space, re-run BOTH.
- Disk-full also blocks the agent harness itself (ENOSPC opening task output files) — nothing can run until the user frees space manually (e.g. empties Trash).
