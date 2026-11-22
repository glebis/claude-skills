---
name: promo-reels
description: This skill should be used when turning raw footage (rehearsals, backstage, events, product or workshop clips, phone videos) into short vertical promo Reels (1080×1920, 15–60 s) with a call to action — hook slide, fast or calm cut across varied framings, captions, text slides in a style picked from presets, from a reference image/site or tuned in dialogue (design tokens), optional generated or licensed music on a beat grid, and a final "buy a ticket / sign up / order" CTA. Trigger on "сделай рилсы из этих видео", "рилс с призывом купить билет", "смонтируй reels под музыку", "make reels from this footage", "promo reel with CTA", "cut this to the beat", "reels for the show/event on <date>", "в стиле этого постера", "match our brand". Also trigger its reflection command on "рефлексия", "улучши скилл", "что узнали за этот запуск", "reflect on the reels run", "self-improve promo-reels". Inputs are just the video files, the title, date/venue and the CTA; everything else has defaults.
---

# Promo Reels

Footage + title + date + CTA → several 1080×1920 Reels, each: hook slide → 8–20 shots → CTA slide, with or without music, in a look chosen for this project (theatre premiere, concert, course launch, product drop…). Everything is files and scripts, so any version can be rebuilt by editing a JSON and re-running.

Works in any agent with a shell and Python (Claude Code, Codex, ChatGPT Work / containers) — it uses only the scripts here, no agent-specific tools. Paths below are relative to this skill's folder (`<skill>/scripts/…`); run them with `python3`.

**Step 0, every run: `python3 scripts/doctor.py`** (add `--install` to pip-install missing Python packages). It checks ffmpeg filters, headless Chrome/Chromium (also Playwright's), bundled fonts, network, the API key, and prints which modes are available. Plan the run from its output:
- No network (Codex default sandbox, ChatGPT chat container): music mode `none`/`file`/`licensed`, no transcription — captions only from text the user gives. Don't retry network calls.
- `ELEVENLABS_API_KEY` missing: ask the user to set it as an environment variable/secret; never print it or write it to a file.
- Skill folder read-only: the learning loop outputs lessons as text (see below).
Requirements: ffmpeg + ffprobe, Chrome/Chromium (headless), Python ≥ 3.9 with numpy, opencv; librosa + soundfile for beats/music. Fonts are bundled (`assets/fonts`, OFL) — slides render offline.

## Intake (ask only what's missing, in one message)

Required: video files · title · date (and time if known) · venue · CTA text and where it leads ("ссылка в профиле" by default).
Defaults: 3 reels, ~20–25 s each, captions only where speech is verified. **Style — ask once**: pick from previews / match a reference (poster, screenshot, site) / a brand file (`references/style.md`). Music mode **ask once**: `none` (user adds in Instagram) / `generate` (genre words) / `licensed <track>` (grid only, never embed) / `file <path>`.
Also ask: what the show/event/product is (genre, tone) — it decides what may be joked about and which presets to show first (`mood` in each preset). Push back on briefs that can't work (e.g. jokes from footage that isn't funny, 60 s from 30 s of material) before building.

## Workflow

Work in a folder per project: `WORK/` (analysis), `slides/`, `edl_*.json`, `out/`.

1. **See the material.** `analyze.py scan VIDEOS… --out WORK` → open and look at every `WORK/sheet_*.jpg` (view the image; it is how you see the footage — never plan shots from numbers alone). List the usable moments per clip with times (gestures, faces, reactions, camera moves, wide shots) and what to skip (empty frames, smear). For crop centres of close-ups: `analyze.py grab WORK A@7.5 B@9.6 …` (10 % grid).
2. **Voice (if clips have audio).** `voice.py WORK` → denoise + transcript. Quote only what the transcript shows and the two denoisers agree on; singing or one-syllable shouts become stage directions ("(поёт)", "What?! — в 9-й раз"). Never invent dialogue. See `references/lessons.md` → audio.
3. **Copy (draft).** Hook (3 short lines — the exact letter budget comes from the style in step 4), title/date/venue/action, CTA, 0–4 captions (≤60 chars). Humor sources for silent footage: juxtaposition, reaction shots, repetition, deadpan stage directions — `references/copy.md`. Show the copy table to the user when content matters.
4. **Style.** `style.py preview slides.json --out preview` renders the hook in every preset (+ the project's `style.json` if any) → `preview/styles.jpg` and `preview/choice.json` (picker arguments). Ask with the best question tool you have — cenno `ask_user` with that JSON, a built-in choice prompt, or the contact sheet in chat. Reference instead: look at it, then `style.py from-ref IMG|URL --out style.json --font … --case …`. Tune with `style.py set style.json color.accent=#… type.case=none` (≤ 4 questions, a preview after each). Dialogue, tokens, presets: `references/style.md`.
5. **Slides.** Write `slides.json` within the chosen style's copy budget (`type.fill_chars`, printed by `style.py check style.json`), run `slides.py slides.json --out slides` (uses `style.json` beside it; `--style NAME` to override). Exit 2 / `REWRITE` = copy too long → shorten the copy, don't touch CSS or tokens to squeeze it. Read the PNGs.
6. **Music (optional).** `generate`: `music.py "PROMPT" --seconds <reel length+1> --out audio/x.mp3 [--key "D minor"] --takes 2` (key is not obeyed — the script checks and transposes). Then `beats.py audio/x.mp3`. `licensed`: look up BPM (web search; expect disagreement, live recordings drift), use `--bpm`; if the user can supply the file, `beats.py` it and use `--beats … --offset <chorus downbeat>`. Prompt patterns: `references/music.md`.
7. **Edit decision list.** Pick a pacing preset from `references/pacing.md` and write `edl_<name>.json` (shot list with source, in-point, zoom, centre, move, note; captions as `caption` PNG paths). Add `"style": "style.json"` so footage motion, slide motion and colour grade follow the look. Free pacing: set `dur`. Music grid: set `beats` per shot, then `grid.py edl.json --beats audio/x.beats.json` or `--bpm 101`.
8. **Build.** `build.py edl_<name>.json` → `out/<name>.mp4` + per-shot files.
9. **Verify.** `verify.py edl_<name>.json out/<name>.mp4` → read the `.check.jpg`; fix shots flagged `BLUR?`, subjects leaving frame, empty frames by moving the in-point or framing; rebuild. Cut errors > 1 frame fail the check.
10. **Mix.** `mix.py out/<name>.mp4 audio/*.mp3 [--offset s]` → `out/final/<name>__<track>.mp4` at −14 LUFS. Licensed track: deliver the silent version plus `mix.py … --click <BPM>` as a timing preview, and tell the user where in the song to start inside Instagram.
11. **Deliver.** Give the user the final files (attach them or give download links/paths, whatever the environment supports), list per file: length, cut count, music, what was verified by measurement vs not listened to. Mention `out/<name>/shots/` for hand-finishing.
12. **Reflect — part of delivery, not optional.** In the project folder: `python3 scripts/reflect.py`, then show the user its proposals (see "Reflection command"). The job is not done until this ran: `verify.py` and `mix.py` print a reminder as their last line.

## Reflection command (run any time: "рефлексия", "улучши скилл", "reflect")

Every script appends to `<project>/.promo-reels/runlog.jsonl`: what ran, crashes, exit codes and **signals** (fit-audit failures, blur flags, cuts off the grid, loudness corrections, wrong music key, VFR or landscape sources, transcripts without words…), plus a snapshot of each build. Run scripts from the project folder (or set `PROMO_REELS_PROJECT`) so the log lands in one place.

`python3 scripts/reflect.py [PROJECT] [--all] [--peek]` reads the log since the last reflection and prints:
1. what ran, crashed or was never verified;
2. signals grouped, marked if a reference already covers them;
3. **hand fixes** — shots changed between two builds of the same EDL (moved in-points, reframes, retimed shots): each is something the first plan got wrong;
4. draft `learn.py add` commands with `<generalise>` placeholders (`learn.py` refuses them until rewritten as a rule);
5. questions only the conversation answers: user corrections, stated preferences, new scenarios, unlogged manual work, praise.

Then: rewrite the drafts into rules, add answers from section 5, drop one-offs, show the user ≤ 5 proposals as `topic · kind · rule · evidence`, and run `learn.py add` for the confirmed ones. A signal repeated ≥ 2 times or any crash → also propose a script change. The report is saved as `.promo-reels/reflection-<time>.md`; nothing reaches the references without a yes.

## Learning loop (the references grow from use)

Start of every run: read `references/preferences.md` and `python3 scripts/learn.py list` — past lessons override defaults here.

**Propose a lesson** (don't write silently) whenever one of these happens:
- **error** — a script failed, a check failed, or you needed a workaround/manual fix (a shot rebuilt for blur, a tool reinstalled, a flag changed).
- **feedback** — the user corrected, rejected or praised a result ("не влезает", "слишком мелко", "сделай спокойнее").
- **scenario** — a new kind of input or request (landscape footage, a 60 s brief, a licensed song, a new language, a new CTA type).
- **preference** — a taste decision likely to repeat (music genre, slide order, number of variants).

How: at the moment it happens (or at the end of the run, batched), show 1–3 proposed entries as `topic · kind · rule · evidence`, one line each, and ask the user to confirm in chat. On yes:

```bash
python3 scripts/learn.py add --topic pacing --kind feedback --rule "Calm cut: 1 shot per bar with 0.3 s dissolves" --evidence "User asked for a calmer cut under a 112 BPM cue"
```

A rule is an instruction for next time, not a diary line; evidence says what happened, generically (the repo is public — `learn.py` refuses personal paths, e-mails, phone numbers). If a lesson changes how a script should behave, also propose the script fix. Topics: `learn.py topics`.

If `doctor.py` says the skill folder is read-only (or the environment doesn't persist it, as in hosted chats), don't lose the lesson: give the user the exact `learn.py add …` commands in a code block so they can run them in their copy of the skill, and say so.

End of every run: the reflection command above (step 12) is the learning checkpoint. If it finds nothing and the conversation had no corrections, say "nothing new" in one line.

## Rules

- 1080×1920, 30 fps, all text inside the safe zone (top 250, bottom 450, right 140, left 60 px) — the template and audit enforce it.
- Style lives only in tokens (`style.json`); never edit `template.html` or CSS for one project. Contrast is checked on every render.
- Variety of framing from one clip: wide (zoom 1.0), medium (1.3–1.5), close (1.7–1.9 max on 720p sources; soft beyond that).
- Every shot moves a little (push in/out 4–6 %); alternate sources; put the best joke (reaction pair) in the first third; end footage on a gesture that "hands over" to the CTA.
- Don't embed licensed music (Instagram mutes it). Generated music: instrumental, length = reel + 1 s.
- Report honestly: what you measured (cuts, loudness, fit) vs what nobody has watched or listened to yet.
- Before any external upload (ElevenLabs) the audio leaves the machine — fine for the user's own footage; ask if footage looks private.

## References

- `references/preferences.md` — the user's standing decisions (read first)
- `references/learning-log.md` — index of every lesson added by `learn.py`
- `references/style.md` — style dialogue, reference extraction, token table, presets
- `references/pacing.md` — presets (dynamic, calm, music-grid) with numbers and the shot-order recipe
- `references/copy.md` — copy budgets, humor patterns for silent footage, CTA wording per kind of event
- `references/music.md` — ElevenLabs prompt patterns, key/tempo checks, licensed tracks
- `references/lessons.md` — traps found in production (VFR, no drawtext, font loading, DeepFilterNet vs singing, Scribe language drift, loudnorm misses)
- `assets/examples/` — example `slides.json` and EDLs (dynamic, calm with dissolves, BPM grid)
