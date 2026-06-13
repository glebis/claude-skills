---
name: wispr-analytics
description: This skill should be used when analyzing Wispr Flow voice dictation history for self-reflection, work patterns, mental health insights, or productivity analytics AND when managing the Wispr Flow dictionary (adding terms, fixing mishears, exporting/importing, suggesting improvements). Triggered by requests like "/wispr-analytics", "analyze my dictations", "what did I dictate today", "wispr reflection", "add to wispr dictionary", "improve dictation", "wispr suggest", "export wispr dictionary", or any request to review voice dictation patterns or manage dictation quality.
---

# Wispr Analytics

Extract and analyze Wispr Flow dictation history from the local SQLite database. Combine quantitative metrics with LLM-powered qualitative analysis for self-reflection, work pattern recognition, and mental health awareness.

## Data Source

Wispr Flow stores all dictations in SQLite at:
```
~/Library/Application Support/Wispr Flow/flow.sqlite
```

Key table: `History` with fields: `formattedText`, `timestamp`, `app`, `numWords`, `duration`, `speechDuration`, `detectedLanguage`, `isArchived`.

The user has ~8,500+ dictations since Feb 2025, bilingual (Russian/English), across apps: iTerm2, ChatGPT, Arc browser, Claude Desktop, Windsurf, Telegram, Obsidian, Perplexity.

## Extraction Script

Run `scripts/extract_wispr.py` to pull data from the database:

```bash
# Get today's data as JSON with stats + text samples
python3 scripts/extract_wispr.py --period today --mode all --format json

# Get markdown stats for the last week
python3 scripts/extract_wispr.py --period week --format markdown

# Get text samples only for LLM analysis
python3 scripts/extract_wispr.py --period month --mode mental --texts-only

# Save to file
python3 scripts/extract_wispr.py --period week --format markdown --output /path/to/output.md
```

### Period Options
- `today` -- current day (default)
- `yesterday` -- previous day
- `week` -- last 7 days
- `month` -- last 30 days
- `YYYY-MM-DD` -- specific date
- `YYYY-MM-DD:YYYY-MM-DD` -- date range

### Mode Options
- `all` -- full analysis (default)
- `technical` -- filters to coding/AI tool dictations
- `soft` -- filters to communication/writing dictations
- `trends` -- focus on volume/frequency patterns
- `mental` -- all text, framed for wellbeing reflection
- `prosody` -- audio-based: pitch/intensity/voice-quality from recorded WAV (separate script `scripts/extract_prosody.py`; recent dictations only). See "Prosody Mode" below.

### Comparison & Graphs
- `--compare` -- auto-compare with the equivalent previous period (week vs previous week, month vs previous month)
- `--graphs PATH` -- generate an HTML dashboard with Chart.js graphs (implies --compare). Graphs include: daily words overlay, hourly activity, category breakdown, top apps, language distribution

```bash
# Compare this month vs previous month (markdown)
python3 scripts/extract_wispr.py --period month --compare --format markdown

# Generate visual dashboard for week comparison
python3 scripts/extract_wispr.py --period week --compare --graphs /tmp/wispr-week.html

# Compare and save both markdown + graphs
python3 scripts/extract_wispr.py --period month --compare --format markdown --output report.md --graphs report.html
```

## Prosody Mode (audio-based)

A standalone analysis mode -- a peer of `technical`/`soft`/`trends`/`mental` -- that analyzes *how* dictations sounded, not just *what* was said. It reads the recorded WAV audio stored in `History.audio` and uses Praat (via `parselmouth`) to extract prosodic features as gentle affect/energy proxies for self-reflection. Run it via the dedicated script `scripts/extract_prosody.py`.

### Dependency

```bash
pip install praat-parselmouth
```

`librosa`/`scipy`/`soundfile` are acceptable fallbacks but the script uses parselmouth (Praat) as the gold standard.

### Audio-retention caveat (read this first)

Wispr keeps the recorded audio **only for recent dictations** -- roughly the last ~900 of 16,000+ history rows. Older rows have their `audio` blob pruned after upload (and `builtInAudio` is always empty). So prosody is available for **recent dictations only**; for older periods the audio is gone and only timing-based metrics (rate, pauses) could ever be recovered. The script surfaces this honestly: every report opens with a coverage line (`X of Y dictations in this period had retained audio`) and logs when `--limit` truncates coverage.

### What it measures

- **Pitch (F0)** via Praat `to_pitch()`, unvoiced frames ignored: mean, median, min, max, range, std, and **CV (std/mean)** as a monotone <-> expressive proxy.
- **Intensity (dB)**: mean, range, std -- loudness dynamics.
- **Voice quality**: jitter (local), shimmer (local), and **HNR** (harmonics-to-noise ratio). Computed in try/except -- short/noisy clips that fail are skipped and counted (`feature_failures`).
- **Tempo** (from DB timing columns, not audio): speaking rate `numWords / (speechDuration/60)` WPM, and pause ratio `(duration - speechDuration)/duration` (clamped >= 0).
- **By-language split** (Russian vs English F0/rate differ -- kept separate so bilingual mixing doesn't muddy the signal) and a **per-day trend table** for multi-day periods.

### Commands

```bash
# Prosody report for the last week (text)
python3 scripts/extract_prosody.py --period week

# Last month as JSON
python3 scripts/extract_prosody.py --period month --format json

# Specific day, raise the clip cap so coverage isn't truncated
python3 scripts/extract_prosody.py --period 2026-06-11 --limit 600

# Save to a file
python3 scripts/extract_prosody.py --period week --output /tmp/prosody-week.md
```

Args: `--period` (same semantics as `extract_wispr.py`: today/yesterday/week/month/`YYYY-MM-DD`/`YYYY-MM-DD:YYYY-MM-DD`), `--format text|json`, `--limit N` (cap clips processed, default 300 to bound runtime -- logs to stderr when it truncates), `--output PATH`. The DB is opened strictly read-only (`mode=ro&immutable=1`).

Performance: audio analysis is ~15-20s for 300 clips (slow vs SQL). The default `--limit 300` keeps single runs fast; raise it for full coverage of a busy period.

### Sanity expectations

Gleb is male, so expect mean F0 roughly 95-150 Hz (observed ~120 Hz). Russian typically shows slightly higher F0 and CV than English in the by-language split. F0 CV usually lands ~0.2-0.3.

### How it ties into mental mode

Prosody complements the text-based `mental` mode with acoustic affect/energy proxies, framed the same way -- as reflection invitations, never diagnoses:
- **F0 CV** (pitch variability) as an engagement/expressiveness proxy: flatter = possibly tired/transactional, more varied = more animated.
- **Speaking rate & pause ratio** as energy / cognitive-load proxies.
- **HNR drops** can track vocal fatigue or strain.

Acoustic features are also shaped by microphone, room, a cold, and language -- so always name that uncertainty and compare like-with-like (same language, against the user's recent baseline). See the **Prosody Mode** template in `references/analysis-prompts.md` for the full interpretive prompt.

## Workflow

### Step 1: Extract Data

Run the extraction script with the requested period and mode. Use `--format json` for full data or `--texts-only` for LLM analysis focus.

### Step 2: Present Quantitative Stats

Display the quantitative summary first:
- Total dictations, words, speech time
- Category breakdown (coding, ai_tools, communication, writing, other)
- Language distribution
- Hourly activity pattern
- Daily trends (for multi-day periods)
- Top apps

### Step 3: Perform Qualitative Analysis

Read `references/analysis-prompts.md` to load the appropriate analysis template for the requested mode. Then analyze the text samples using that template.

For each mode:

**Technical**: Focus on what was worked on, technical decisions, context-switching patterns, productivity assessment.

**Soft**: Focus on communication style shifts, language-switching patterns, audience adaptation, interpersonal dynamics.

**Trends**: Focus on volume changes, time-of-day shifts, app migration, behavioral change hypotheses.

**Mental**: Focus on energy proxies, sentiment signals, rumination detection, activity pattern changes. Frame all observations as invitations for self-reflection, never as diagnoses. Use language like "you might notice..." or "this pattern could suggest..."

**All**: Combine all four perspectives into a unified reflection.

### Step 4: Output

Default output location: `meta/wispr-analytics/YYYYMMDD-period-mode.md` in the vault.

File format:
```markdown
---
created_date: '[[YYYYMMDD]]'
type: wispr-analytics
period: [period description]
mode: [mode]
---

# Wispr Flow Analytics: [period]

## Quantitative Summary
[stats from Step 2]

## Analysis
[qualitative analysis from Step 3]

## Reflection Prompts
[3-5 questions based on observations]
```

If the user requests console-only output, skip file creation and display directly.

## App Category Mapping

The extraction script categorizes apps:
- **coding**: iTerm2, cmuxterm, VS Code, Windsurf, Zed, Cursor, Terminal
- **ai_tools**: ChatGPT, Claude Desktop, Perplexity, OpenAI Atlas, Codex
- **communication**: Telegram, Messages, Slack, Zoom
- **writing**: Obsidian, Notes, Chrome, Arc browser

## Dictionary Management

Manage Wispr Flow's dictionary for better recognition accuracy. The dictionary JSON is version-controlled in `~/ai_projects/claude-skills/wispr-analytics/data/dictionary.json`.

### Dictionary Script

Run `scripts/wispr_dictionary.py` for all dictionary operations:

```bash
# Check database health and dictionary stats
python3 scripts/wispr_dictionary.py check

# List all entries (safe while Wispr is running)
python3 scripts/wispr_dictionary.py list
python3 scripts/wispr_dictionary.py list --filter "claude"

# Export dictionary to JSON (safe while running)
python3 scripts/wispr_dictionary.py export

# Suggest new entries by analyzing ASR vs formatted text differences
python3 scripts/wispr_dictionary.py suggest --days 30 --min-freq 3

# Propose snippets + replacement rules + vocab from dictation logs (safe while running)
python3 scripts/wispr_dictionary.py propose --days 30 --min-freq 3
python3 scripts/wispr_dictionary.py propose --days 90 --min-freq 2 --format json

# Add a single term (requires Wispr Flow to be QUIT)
python3 scripts/wispr_dictionary.py add "Gastown"
python3 scripts/wispr_dictionary.py add "cloud code" "Claude Code"

# Remove an entry (requires Wispr Flow to be QUIT)
python3 scripts/wispr_dictionary.py remove "old term"

# Import from JSON (requires Wispr Flow to be QUIT)
python3 scripts/wispr_dictionary.py import --dry-run
python3 scripts/wispr_dictionary.py import
```

### Dictionary Safety Rules

**CRITICAL**: Wispr Flow must be quit before any write operations (add, remove, import). The script enforces this automatically. Read operations (export, list, suggest, check) are safe while Wispr is running.

Writing to the SQLite database while Wispr Flow has it open causes index corruption. Always:
1. Check if Wispr is running: `pgrep -f "Wispr Flow"`
2. If running, ask user to quit first (Cmd+Q)
3. After writes, run `check` to verify integrity
4. Restart Wispr Flow

### Dictionary Entry Types

- **Recognition terms** (phrase only): teaches Wispr to hear the word correctly (e.g., "Gastown", "LLM", "subagent")
- **Replacement rules** (phrase → replacement): auto-corrects mishears (e.g., "cloud code" → "Claude Code", "клод дизайн" → "Claude Design")
- **Snippets** (isSnippet=true): text expansion shortcuts (e.g., "my email" → "glebis@gmail.com")

### Propose Replacements & Snippets

`suggest` only catches ASR mishears. `propose` is the broader, human-style review:
it reads recent dictation logs and proposes dictionary additions in **three
categories**, skipping anything already in the dictionary. It is **read-only and
safe while Wispr Flow is running** -- it never writes to the database.

```bash
# Default: last 30 days, terms seen >= 3 times
python3 scripts/wispr_dictionary.py propose

# Wider net, machine-readable
python3 scripts/wispr_dictionary.py propose --days 90 --min-freq 2 --format json
```

Flags: `--days` (history window), `--min-freq` (minimum occurrences), `--format`
(`text` default, or `json`).

The three categories:

1. **Snippet candidates** (highest leverage, most underused): recurring URLs,
   emails, and phone numbers, plus repeated boilerplate sentences/intros/sign-offs
   (>= 8 words, counted by normalized verbatim frequency). Each proposal includes a
   short `My X` trigger phrase + the full expansion.
2. **Replacement-rule candidates**: recurring ASR mishears (shares code with
   `suggest` via the `find_mishears` helper).
3. **Vocab candidates**: frequently-dictated capitalized/technical terms
   (e.g. `HTML`, `LinkedIn`, `SDK`) that may be mis-recognized -- teach Wispr the
   spelling.

Each proposal prints a frequency count and a ready-to-run `add` command line.

**Snippets are the single highest-leverage, most underused dictionary feature.**
A user with 1,600+ dictations/month often has only a handful of snippets. One
`My GitHub` -> URL snippet saves dictating (and mis-dictating) a URL dozens of
times. Always foreground snippet candidates first.

#### Suggested workflow

1. Run analytics (`extract_wispr.py`) to understand volume and where snippets pay off.
2. Run `propose` (safe while Wispr runs).
3. Present the grouped proposals to the user -- snippets first, then replacement
   rules, then vocab. Frame snippets as the big win.
4. After the user approves and **quits Wispr Flow (Cmd+Q)**, run the approved
   `add` lines (snippets need `add "My X" "expansion"`).
5. Run `python3 scripts/wispr_dictionary.py check` to verify integrity.
6. Restart Wispr Flow.

### Proactive Dictionary Improvement Workflow

When running analytics, also check for dictionary improvement opportunities:

1. Run `propose` to surface snippets, replacement rules, and vocab in one pass
   (or `suggest` for mishears only)
2. Compare `asrText` vs `formattedText` for patterns
3. Look for Russian/English code-switching mishears
4. Check for new technical terms the user started using
5. Export updated dictionary and commit to git

## Notes

- For analytics: the database is read-only; analytics never modifies Wispr data
- For dictionary: writes require Wispr Flow to be quit first
- Text samples are capped at 100 per extraction to manage context window
- For multi-day periods, daily trend tables help visualize changes
- Bilingual dictations are common; analysis should honor both Russian and English
- The `asrText` field contains raw speech recognition before formatting -- useful for detecting speech patterns vs formatted output
- Dictionary JSON is stored at `~/ai_projects/claude-skills/wispr-analytics/data/dictionary.json` for version control
