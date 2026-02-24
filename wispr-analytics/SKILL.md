---
name: wispr-analytics
description: This skill should be used when analyzing Wispr Flow voice dictation history for self-reflection, work patterns, mental health insights, or productivity analytics. Triggered by requests like "/wispr-analytics", "analyze my dictations", "what did I dictate today", "wispr reflection", or any request to review voice dictation patterns. Supports modes - technical (coding/work), soft (communication), trends (volume/frequency), mental (sentiment/energy/rumination).
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
- **coding**: iTerm2, VS Code, Windsurf, Zed, Cursor, Terminal
- **ai_tools**: ChatGPT, Claude Desktop, Perplexity, OpenAI Atlas
- **communication**: Telegram, Messages, Slack, Zoom
- **writing**: Obsidian, Notes, Chrome, Arc browser

## Notes

- The database is read-only; this skill never modifies Wispr data
- Text samples are capped at 100 per extraction to manage context window
- For multi-day periods, daily trend tables help visualize changes
- Bilingual dictations are common; analysis should honor both Russian and English
- The `asrText` field contains raw speech recognition before formatting -- useful for detecting speech patterns vs formatted output
