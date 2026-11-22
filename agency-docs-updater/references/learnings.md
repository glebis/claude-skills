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
- Meeting pages are audience-facing notes, not operator logs. Never publish recording provenance, trimming/cutting decisions, silence or preamble removal, remux/re-encode details, transcript synchronization, upload retries, or other production mechanics. Keep these only in the internal Pipeline Report.
- Proper nouns require a cross-surface check because ASR variants leak into summaries, transcripts, YouTube descriptions, and thumbnails. Explicit user corrections override transcript spelling. Regression case (2026-08-14): canonical product name is `Дзынь (Ding)`, never `Zynia`, `Dzynia`, or `Dingo`.

## YouTube API
- Always pass `--title` from Fathom frontmatter — without it, the LLM generates poor/generic titles for Russian content
- `youtube.force-ssl` scope is needed for both uploads and metadata updates
- **Videos can silently disappear after upload.** On 2026-05-16, a video was uploaded successfully (got VIDEO_ID), but YouTube later deleted it (shows as "Deleted video" with `privacyStatusUnspecified`). Always run Step 3a verification after upload. If verification fails, re-upload before proceeding
- The YouTube oEmbed API (`youtube.com/oembed?url=...`) returns "Not Found" for deleted/private videos — useful quick check
- **Description `->` chain rejected (2026-08-18, GDD RU #09).** YouTube `videos.update` returns `400 invalidDescription` for descriptions containing chained ASCII `->` arrows inside parentheses (e.g. `(Engelbart -> Xerox Alto -> Mac -> Web -> iPhone)`). The error gives no token hint. Bisect test: a single Cyrillic char, Cyrillic + Cyrillic URL, ASCII-only all pass — the chained ASCII arrow is the trigger. **Fix:** rewrite arrow chains as comma-separated lists, or use Cyrillic `→` (U+2192) which is accepted. Affects YouTube descriptions, NOT the MDX body (no API call).

## Meeting number detection
- Don't trust auto-detected meeting number blindly — placeholder MDX files may already exist. Check existing files by date content first, use `-n NN` to override

## GDA 01 Sunday advanced group (2026-10-18)
- Calendar titles add descriptors: `Sessions/20261018-goal-driven-ai-01-продвинутая-группа.md` didn't match `goal-driven-ai-{lab}`. Patterns now allow a `-<suffix>`, which `find_transcript` returns (`layout_find_transcript_in_sessions`).
- A second track inside one cohort has no page structure (meetings 01–08 = Saturdays). Where it lives is the owner's IA decision: ask, don't improvise a path.
- The brand label «Встреча {meeting}» collided with Saturday meeting 01, so `brand_cover.py --label` overrides it (`cover_label_override`).
- Zoom now emits a TRANSCRIPT .vtt with speaker names on the video clock. That's the best edit context; pass `--offset 0`. Its text is badly garbled, so take proper nouns from Wispr.
- Pre-meeting waiting with the screen shared reads as "long demo wait"; replace it with an `editorial` cut up to the host's start phrase.

## GDA 01 #02 (2026-10-17): every item has an eval or a SKILL change
- No Fathom recording at all; calendar-sync found nothing and icalBuddy said "No calendars." (access lost). Zoom cloud auto-recording (enabled 2026-10-10) saved it. Processing took ~2 h 10 min; the API showed 0 MB, empty file_type and empty recording_end the whole time. Session note was built from Wispr refined text; `update_meeting_doc` made Fathom optional (`merge_without_fathom`).
- Scaffold placeholders weren't recognised: title "Встреча 02", description "Встреча 02 лаборатории …", and «Запись, слайды и материалы появятся здесь после встречи.». Last week's live 01 page still showed «…появятся здесь после встречи» under its recording (`merge_scaffold_placeholders`, `merge_keeps_curated_content`).
- A new lab (goal-driven-ai-en) landed on main unregistered and was indexed as `claude-code-lab-??`. Registered it, and the fallback is now the folder route plus a warning (`layout_unregistered_lab_never_question_marks`).
- Temp-worktree publishing: the build needs `node_modules` (symlink only if lockfiles match) and `.env.production.local` (Clerk publishable key; `.env.local` lacks it, and the failure reads "Missing publishableKey", not an MDX error).
- Wispr diarization drifts: the host was "Спикер 1" then "Спикер 7" from ~24 min. Don't attribute statements from Wispr speaker ids; use the Zoom TIMELINE (speaker activity on the video clock).
- Session-specific ASR fixes: GLM (JLM), Jev («слой Java… модель для быстрых решений»), Dataview («Data View»), Simon Willison («Саймон Вилкинсон»), ELI6 («Ellie six»), meat proxy («MeetProxy»), Wispr Flow («Whisper Flow»).

## First real run: Goal-Driven AI 01 (2026-10-10). Every item has an eval
- **Transcript lookup**: the file was `Sessions/20261010-goal-driven-ai-01.md`. Step 1 globbed the vault root for `*-lab-NN.md` and `update_meeting_doc.py` crashed parsing the lab number. Now `find_transcript.py` + `vault_names` in labs.json (`layout_find_transcript_in_sessions`, `layout_lab_number_from_real_names`).
- **No Zoom cloud recording**: the Saturday cohort meeting had no `auto_recording`. The Fathom download (2h35, 1.5 GB, ~20 min at ~1.2 MB/s) was the only source. Enable cloud auto-recording on new recurring lab meetings (S2S token, see above).
- **Hand-built URLs**: SKILL.md built `/${LAB_SLUG}-lab-NN/` (404 for goal-driven-ai) and `content/docs/${LAB_SLUG}-internal-NN` (empty `git add`). Always use the layout's `page_url`/`meetings_dir`/`playlist` (`layout_docs_resolve_paths_via_registry`).
- **Visual signal**: freezedetect marked every webcam pause "screen active", so 183/183 silences were kept (0% removed). Measured scene scores: talking head median 0.010-0.014 (never still), screen share 0.001-0.002 with sparse jumps, camera off 0. Classify webcam / screen_activity / static (`edit_visual_states`). Synthetic fixtures must mimic this: grain noise scores ~0, Game of Life ~0.015.
- **Alignment confidence**: "share of cues after a pause" is ~10% for a perfectly aligned transcript of continuous speech. Use the share of speech onsets with a cue nearby.
- **Breaks aren't silent**: room noise splits a 4.5-min break into short silences. The transcript gap shows it whole; refine its start with a silence inside it (`edit_spoken_directives`).
- **Spoken directives**: «Так, агент, это конец паузы. | Пожалуйста, вырежи паузу.» spans two Fathom segments, and «агент» as a topic noun appeared ~20× as false positives. Require a vocative plus an imperative within 3 segments. Cuts are review-only; fact-check requests go to `agent_notes` for the summary.
- **Wispr Flow vs Fathom** (`compare_transcripts.py`): Wispr spells tech terms in Latin (Claude 32/0 vs Fathom 0/23 «Клод»), has no Whisper hallucinations, and has no duplicated passages. But its clock skips paused time (offset jumped +68 s → +127 s around 100 min), so it's unusable for cuts. Detect this by TEXT (`compare_transcripts.py` clock steps, eval `edit_compare_detects_clock_step`), not by audio onsets: onset-matching drift detection was built, then removed. On real speech (~1 pause/min) it flagged a same-recording transcript and missed Wispr's real step. `edit_video` now warns on the declared `recording_active_ms` clock (`edit_warns_on_wispr_clock`). Fathom: timing source, but wrong speaker labels (Lilit tagged "Andrew"), hallucinations («Субтитры сделал DimaTorzok», «Продолжение следует», a 300-char «эээ»), and a duplicated 2-min passage. Use Fathom for timing and Wispr for text/proper nouns.
- **Composition choice**: topic keywords tied portrait/pricing and declared order picked pricing. Headline hits now count double (`cover_headline_outweighs_topic`).
- **Canonical names this lab** (ASR variants in both tools): Ollama (Allama/Аллама/Alamo), Pi (Py/PIE/пай), Zed («Z и D»), herdr (Herder/эрдер), Palmier Pro, GLM (JLM), Claude Code (плод-код/Cloud Code), Wispr Flow (WhisperFlow/Visperflow).

- **Wrong branch + push (the serious one)**: the agency-docs checkout was on `codex/companion-t-shaped`, not `main`, and I didn't check. The "22 unpushed commits" were pushed to that branch, and production ran it via CLI. My meeting commit landed on the branch, and pushing to `main` merged the branch without a PR. It was harmless only because production already ran that exact tree (checked via `vercel inspect` created-times). Now `publish_preflight.sh` blocks (`layout_publish_preflight_blocks_feature_branch`). Never rebase or stash in the shared checkout; use a temp worktree. A rebase there also hit an ordering conflict (typography before plugin tile); a merge with local-side resolution gave a byte-identical tree.
- **Aggregations on templated dirs**: `meetings_dir` with `{lab}` never matched, so the new lab's meetings got `claude-code-lab-??` URLs in the index and glossary (`layout_aggregations_resolve_templated_dirs`).
- **ffmpeg expression limits**: one `select` with 145 terms fails ("Cannot allocate memory"). Chain groups of 25; setpts groups latest-first (`edit_hundreds_of_cuts`).
- **Negative first pts**: AAC priming (`silence_start: -0.0213`) broke silence pairing (`edit_pairs_negative_start`).
- **Lesson start**: a participant's «всем привет» at 16:31; host-only phrases now (`edit_lesson_start_is_hosts`).
- **Whisper hallucination**: a bare "DimaTorzok" with no_speech_prob 0.07, so filter by pattern, not probability (`edit_whisper_hallucination_filter`).
- **Build**: the first `npm run build` with an existing `.next` failed with `'hash'` twice in a row. That looks systematic, not random. `safe_build` retry passes (~1 min extra).
- **Gated GDA pages**: unlike claude-code-lab, the anonymous 404 shell doesn't inline the embed, and `/api/search` returns []. Live verification needs a logged-in browser. Fall back to: deploy success + deployed tree == locally built tree whose HTML has the embed.
- **Process checks**: pgrep on an absolute venv path missed the uploader started as `.venv/bin/python` (false "not running"). Match the relative command, or wait on the task itself.
- **Groq key**: preflight read a dead copy in youtube-uploader/.env.local while SOPS (`~/.claude/skills/secrets.enc.yaml`) held a valid key, so the run asked the user for a key it already had. preflight now reads SOPS first. Rotated key stored in SOPS 2026-10-10.
- **Zoom**: cloud auto-recording enabled on the Goal-Driven AI 01 recurring meeting on 2026-10-10 via the S2S token (PATCH 204).
- **Upload path**: process_video.py needs node Playwright (missing). Direct `upload_video(VideoConfig, thumbnail_file=…, notify_subscribers=False)` with hand-checked metadata beat Groq-generated titles anyway.

## Video editing (2026-10-10)
- Vault Fathom `.md` transcripts have no timestamps; context-aware editing needs a Zoom VTT (exact) or Fathom JSON (offset auto-estimated). The offset score is flat over ±tolerance; picking the plateau edge was off by 1 s. Now refined by median residual (eval `edit_offset_auto`).
- Context window for "why is it quiet" must be short (8 s). With 20 s, a demo announced earlier labelled later frozen dead air as a demo (eval `edit_frozen_dead_air_not_demo`).
- Single-pass `select`/`aselect` with `setpts=N/FRAME_RATE/TB` + `asetpts=N/SR/TB` drifts by SECONDS on VFR Zoom files (5.3 s over 38 cuts in the eval). Both streams must use the same map `PTS - removed_before(T)`. Constant-frame-rate fixtures hid this: the sync eval uses a VFR clip on purpose.

## Meeting pages
- Pages often exist before the meeting. Never full-overwrite: `merge_meeting_doc.py` managed blocks (evals `merge_*`).

## Thumbnails
- **Brand covers (2026-10-10, Goal-Driven AI 01).** `thumbnail_style: "site-token"` existed in labs.json but had NO implementation — every GDD cover was improvised. Now `brand` = `brands/<name>.json` + `scripts/brand_cover.py` (references/brand-covers.md). Prefer the site's existing art kit over generation: it is already on-brand, free and deterministic.
- `youtube-uploader/node_modules` can be missing and Playwright's bundled headless shell absent; `render_html.mjs` falls back to global `npm root -g` playwright and installed Chrome (`channel: chrome`) — a separate headless process, safe for the user's open browser.
- The uploader's `render-thumbnails.mjs` uses `page.setContent` (about:blank origin) → local `file://` fonts/images may not load. Brand covers use `page.goto(file://…)` + `document.fonts.ready`.
- Transparent portrait cutouts end in a hard horizontal edge: anchor with `bottom: -1` to bleed off-canvas; use `fade_bottom` where impossible.
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

## Recording completeness (seen 2026-07-24/26, GDD RU #02 lost its last hour)
- BEFORE publishing, compare recording duration against the planned meeting length (~2 h for GDD). A short Fathom recording (e.g. 1:35 of a 2.5 h session) means Fathom stopped early — immediately check Zoom cloud AND the other cohort's Zoom account AND ask the host for local recordings. Meeting 01 was saved by merging Fathom part 1 + Zoom part 2; meeting 02's last hour was captured nowhere.
- Fix applied 2026-07-26: `auto_recording: cloud` enabled on both recurring cohort meetings (RU and EN) via `PATCH /meetings/{id}` with the **S2S token** (`get_access_token(load_credentials())`) — the recordings OAuth token lacks `meeting:update`/`user:update:settings` scopes and 400s with code 4711.
- Zoom auto-recordings will start at meeting open → trim dead air with `scripts/trim_leading_silence.sh` (SKILL Step 3-pre) before uploading.

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

## Already published by another session (2026-10-24, GDA 01 #03)
- A second run started ~4 h after another session had published meeting 03 end-to-end (page `published`, YouTube `rubQFtpbOUw`, bot receipt `goal-driven-ai-01--03--…json` status `sent`). The local checkout was 1 commit behind, so the local placeholder still looked empty, and the run downloaded 650 MB and started edit analysis before the temp worktree showed the published page.
- Check first: `git fetch origin main && git show origin/main:<meetings_dir>/NN.mdx | grep publication_status`, plus `ls ~/ai_projects/pibot/data/publication-receipts/ | grep -- '--NN-'`. If it's published, stop and report. Never re-upload or re-announce.

## GDA 01 advanced #02 (2026-10-25)
- `update_meeting_doc.py` appends `meetings/` to its `docs_dir` positional, so it can't target `goal-driven-ai-01/advanced/NN.mdx`. It wrote stray `meetings/02.mdx` dirs twice. For the advanced layout, call `merge_meeting_doc.py MDX --block recording=rec.md --block summary=sum.md --set title=… --set description=…` directly.
- `merge_meeting_doc.py` adds the `## Запись` / `## Конспект` headings itself and demotes the block's own headings by one level. Pass bodies WITHOUT those H2s, then `sed 's/^#### /### /'` to match earlier pages' `###`.
- Hand-added EDL actions: `remove` is a `[start, end]` span (often padded), not a bool. `apply` crashes with `'bool' object is not subscriptable`.
- No Wispr meeting this time, and Fathom stopped at 1:51 of a 2:02 Zoom recording, so the closing Q&A came from the Zoom VTT only.
- Vercel sat in "pending" for ~9 min (queued) before building; `vercel ls` showed it. It isn't a failure.

## GDA 01 #05 (2026-11-07): two sessions, one meeting, and a split Zoom recording
- **Zoom split the meeting in two** (recording stopped and restarted after 31 min, a 16 s gap): two MP4s at different resolutions (1708×918, 1832×982), two VTTs, two TIMELINEs. List files by `recording_start` and take ALL segments. Join with a scale+pad concat re-encode, then shift part 2's VTT by part 1's exact duration. Stream-copy concat fails on the resolution change.
- **A parallel session published only part 2.** It took the larger MP4 (465 MB), so its video was 1:34 and skipped the first 31 min, yet it went live and was announced. Sanity check before upload: the edited duration should be roughly the Fathom/Zoom total minus about 15%. 1:34 against a 2:16 meeting is a red flag.
- **Two runs collided.** This run pushed the summary (stage 1) at ~21:40. The other session pushed the recording on top at 22:26 and announced at 22:30, while this run was still encoding. Re-check `git fetch && git show origin/main:<page> | grep publication_status`, the receipts dir AND the playlist for an existing "Встреча NN" right before uploading, not only at start.
- Under heavy load (Spotlight indexing a fresh node_modules plus ffmpeg), the local build hit 137 prerender timeouts on unrelated pages and the content check hit vitest's 5 s timeout. Vercel built the same tree in 100 s. Rerun the check with `--testTimeout=120000` before calling it a content error.
- The main checkout had no `node_modules` at all; the worktree symlink dangled ("vitest: command not found"). Check for `node_modules/.bin` before symlinking, else `npm ci` in the worktree.
- ASR: the people-search service is **Exa** (Fathom "EXO", Wispr "Excel"). Meeting 04's published page still says EXO.

## GDA 01 advanced 04 (2026-11-08) — edit_video auto-offset, don't force `--offset 0`

- Zoom's VTT timestamps match the video's audio: `edit_video.py analyze` auto-detect found
  `transcript offset -1.5s (match 79%, peak z=16.1)`. First run with `--offset 0` produced
  identical plan, so pass the flag ONLY if you already know the drift; otherwise let the
  auto-detect run (it adds ~10s for the peak-z scan, well within tolerance).
- Video duration 119 min @ 548 MB → x264 `veryfast` apply pass ≈ 3.5 min for 26.6 min removal.
- YouTube rejected a 106-char title (`invalidTitle`, code 400 unknown reason) — keep ≤100.
  Advanced-track naming: `Goal-Driven AI · Продвинутая 04: <short topic>` works.
- `announce_publication.ts` publication gate reads the **live** feed (`/api/curriculum/...`),
  not the local MDX. After pushing `publication_status: "published"` you must wait for the
  Vercel redeploy before retrying (~2 min, confirmed 2026-11-08).

## GDA 01 #07 (2026-11-21)
- **Build "getaddrinfo ENOTFOUND localhost"** at vitest startup isn't a content error: `.zshrc` exports `NODE_OPTIONS=--import /tmp/nodefix/dnsfix.mjs`, a DNS shim that resolves every non-IP host (including `localhost`) via 1.1.1.1/8.8.8.8. Build with `NODE_OPTIONS= … safe_build.sh`.
- **Disk**: 10 GB free at start wasn't enough for a 650 MB recording + edited copy + `npm ci` in the worktree + `.next` (1.2 GB). The harness itself hit ENOSPC mid-build. Want ≥15 GB, or trash the raw recording right after the edited file verifies.
- **Host-specified start** ("start video from MM:SS"): drop EDL actions ending before it and prepend one approved `editorial` action `remove: [0, T]`.
- **Skill name**: "Cloud Deep Research Monitor" is literal (`cloud-deep-research-monitor`, runs in ChatGPT cloud), NOT an ASR error for Claude. Check the actual skill file before applying the Cloud→Claude rule.

## GDA 01 advanced 06 (2026-11-22)
- **Skipped slot**: advanced 05 (15 Nov) has only a 19-min Zoom recording and no Fathom transcript. Asked the user: today stays **06** per the placeholder date; 05 remains a draft placeholder. Don't renumber by "next empty slot" when the placeholder date matches.
- **Skill built in the session** (`sops-mesh`): the user pushed it to `glebis/claude-skills` during the run. Read it via `gh api repos/glebis/claude-skills/contents/<skill>/SKILL.md` (the local skills checkout may be on someone else's branch, so don't pull there) and add a dedicated `### Скилл <name>` section with the GitHub link to the summary + YouTube description.
- **Glossary store format** is `{"TERM": {"definition": "...", "mentions": [...]}}`. Fill `definition` with a targeted text replace; `json.dump` reformats the whole file.
- `transcribe_cut.py` output is `{"transcript": [{"timestamp", "end", "text"}]}`, not `segments`/`start`.
- Timings: 121 min recording → analyze ~10 min, apply ~4 min, upload 550 MB ~12 min at 0.75 MB/s, Vercel 2 min per push, YouTube processing ~10 min.
