---
name: agency-docs-updater
description: This skill should be used when updating ~/Sites/agency-docs meeting documentation after Claude Code lab sessions. Automatically creates/updates meeting MDX files with Fathom links, YouTube embeds, fact-checked summaries using claude-code-guide agent, and presentation content. Auto-detects lab number from filename, finds presentations, commits and pushes changes.
---

# Agency Docs Updater

## Overview

Automates creation and updates of meeting documentation in the agency-docs repository after Claude Code lab sessions. Combines Fathom transcripts, YouTube videos, fact-checked summaries, and presentation content into properly formatted MDX files.

## When to Use

Use this skill after completing a Claude Code lab meeting publishing workflow when:
- Video has been uploaded to YouTube via videopublish skill
- Fathom transcript exists in Obsidian vault (~/Brains/brain/)
- Need to create/update meeting documentation in ~/Sites/agency-docs
- Want to auto-commit and push to trigger Vercel deployment

## Workflow

### Step 1: Generate Fact-Checked Summary

Before running the script, generate a detailed meeting summary with fact-checking:

```
Using @claude-code-guide agent, create a detailed summary of the meeting from the Fathom transcript at [path].

Requirements:
- Summary should be comprehensive and structured
- Fact-check all claims about Claude Code features using claude-code-guide agent knowledge
- Format sections with H2 headers
- Include key concepts, demos, and discussions
- Save to summary.md
```

The summary should follow the existing pattern from agency-docs meetings:
- Structured sections (## Section Name)
- Bullet points for key concepts
- Code examples where relevant
- Clear, informative descriptions

**Important:** Use Task tool with claude-code-guide agent for fact-checking. Example:

```
Launch claude-code-guide agent to fact-check this summary about Claude Code features.

Verify:
- Subagent types and their capabilities
- Tool names and parameters
- Feature availability and limitations
- Best practices mentioned

Correct any inaccuracies.
```

### Step 2: Run Update Script

Execute the update script to create meeting documentation:

```bash
python3 scripts/update_meeting_doc.py \
  ~/Brains/brain/YYYYMMDD-claude-code-lab-XX.md \
  https://www.youtube.com/watch?v=VIDEO_ID \
  summary.md
```

**Script behavior:**
- Parses Fathom frontmatter for meeting URL (looks for `meeting_url`, `url`, or `fathom_url` fields)
- Extracts lab number from filename pattern: `claude-code-lab-XX`
- Auto-detects target docs directory: `~/Sites/agency-docs/content/docs/claude-code-internal-XX`
- Auto-detects summary language (Cyrillic vs Latin characters)
- Translates to Russian if needed (preserves technical terms in English)
- Determines next meeting number from existing files (or uses specified number)
- Finds latest presentation in `~/ai_projects/claude-code-lab/presentations/lab-XX/`
- Creates MDX file at `meetings/XX.mdx`

**Advanced options:**

```bash
# Specify exact meeting number (updates existing or creates new)
python3 scripts/update_meeting_doc.py \
  [fathom_file] [youtube_url] [summary_file] \
  -n 07

# Force Russian translation
python3 scripts/update_meeting_doc.py \
  [fathom_file] [youtube_url] [summary_file] \
  -l ru

# Update existing meeting file
python3 scripts/update_meeting_doc.py \
  [fathom_file] [youtube_url] [summary_file] \
  -n 07 --update

# Specify custom docs directory
python3 scripts/update_meeting_doc.py \
  [fathom_file] [youtube_url] [summary_file] \
  ~/Sites/agency-docs/content/docs/custom-path
```

**Command-line flags:**
- `-n, --meeting-number`: Specific meeting number (e.g., 07) - prevents auto-increment
- `-l, --language`: Summary language (auto, en, or ru) - auto-detects and translates if needed
- `--update`: Update existing meeting file instead of creating new
- `docs_dir`: Optional positional argument for custom docs directory

### Step 3: Edit Frontmatter

The script creates a template with placeholders. Edit the generated MDX file:

```yaml
---
title: "Встреча XX: [Название встречи]"  # Replace with actual title
description: [Краткое описание встречи]  # Replace with brief description
---
```

Update title and description based on meeting content.

### Step 4: Commit and Push

The script outputs git commands. Execute them:

```bash
cd ~/Sites/agency-docs
git add .
git commit -m "Add meeting XX documentation"
git push
```

### Step 5: Verify Deployment

Check Vercel deployment logs:

```bash
# Option 1: Check Vercel CLI
vercel logs

# Option 2: Visit Vercel dashboard
# https://vercel.com/[your-org]/agency-docs/deployments
```

Verify the new meeting page loads correctly at the deployed URL.

## File Structure

### Input Files

**Fathom Transcript** (`~/Brains/brain/YYYYMMDD-claude-code-lab-XX.md`):
```yaml
---
meeting_url: https://fathom.video/share/[id]
# or
url: https://fathom.video/share/[id]
---

## Transcript
**Speaker**: Content...
```

**Presentation** (auto-detected from `~/ai_projects/claude-code-lab/presentations/lab-XX/`):
- Looks for latest `.md` file (not `.html`)
- Excludes `homework-prompt.md`
- Strips frontmatter before insertion

**Summary** (`summary.md`):
- Generated by claude-code-guide agent
- Fact-checked Claude Code feature claims
- Structured with H2 headers
- Detailed enough for comprehensive overview

### Output File

**Meeting MDX** (`~/Sites/agency-docs/content/docs/claude-code-internal-XX/meetings/XX.mdx`):

```mdx
---
title: "Встреча XX: Title"
description: Brief description
---

**Дата:** Date | **Длительность:** ~2 часа

## Видео

**Fathom:** [Запись на Fathom](fathom_url)

**YouTube:** [Смотреть на YouTube](youtube_url)

<iframe ... YouTube embed ...></iframe>

---

## Краткое содержание

[Fact-checked summary from summary.md]

---

[Presentation content from lab-XX presentations folder]
```

## Auto-Detection Logic

### Lab Number Extraction
Parses filename pattern: `YYYYMMDD-claude-code-lab-XX.md`
- Extracts `XX` as lab number
- Pads to 2 digits: `2` → `02`

### Docs Directory
Constructs path: `~/Sites/agency-docs/content/docs/claude-code-internal-XX/`

### Meeting Number
Two modes:
1. **Auto-detect** (default): Scans `meetings/` directory for existing `XX.mdx` files, finds max, returns max + 1
2. **Specified** (via `-n` flag): Uses exact number provided, checks if file exists

### Presentation File
Searches `~/ai_projects/claude-code-lab/presentations/lab-XX/`:
- Finds all `.md` files
- Excludes `homework-prompt.md`
- Returns most recently modified
- Continues without presentation if not found

## Example Usage

### Example 1: Auto-detect everything (default)

```bash
# Step 1: Generate fact-checked summary (via Claude)
# "Using @claude-code-guide, create detailed fact-checked summary from
#  ~/Brains/brain/20260203-claude-code-lab-02.md, save to summary.md"

# Step 2: Run update script (auto-detects next meeting number, translates to Russian)
python3 ~/.claude/skills/agency-docs-updater/scripts/update_meeting_doc.py \
  ~/Brains/brain/20260203-claude-code-lab-02.md \
  https://www.youtube.com/watch?v=abc123xyz \
  summary.md

# Step 3: Edit frontmatter, commit, push
```

### Example 2: Specify meeting number (update existing placeholder)

```bash
# Create/update meeting 07 specifically
python3 ~/.claude/skills/agency-docs-updater/scripts/update_meeting_doc.py \
  ~/Brains/brain/20260203-claude-code-lab-02.md \
  https://www.youtube.com/watch?v=abc123xyz \
  summary.md \
  -n 07

# If file exists, add --update flag
python3 ~/.claude/skills/agency-docs-updater/scripts/update_meeting_doc.py \
  ~/Brains/brain/20260203-claude-code-lab-02.md \
  https://www.youtube.com/watch?v=abc123xyz \
  summary.md \
  -n 07 --update
```

### Example 3: Force English summary (skip translation)

```bash
python3 ~/.claude/skills/agency-docs-updater/scripts/update_meeting_doc.py \
  ~/Brains/brain/20260203-claude-code-lab-02.md \
  https://www.youtube.com/watch?v=abc123xyz \
  summary.md \
  -l en
```

## Error Handling

**Missing Fathom URL in frontmatter:**
```
⚠️  Could not find Fathom URL in frontmatter (looking for 'meeting_url' or 'url')
```
Solution: Add `meeting_url:` or `url:` field to Fathom transcript frontmatter

**Cannot extract lab number:**
```
ValueError: Could not extract lab number from filename: [filename]
```
Solution: Ensure filename matches pattern `*claude-code-lab-XX*`

**Presentations directory not found:**
```
⚠️  Presentations directory not found: [path]
```
Result: Continues without presentation content

**No presentation markdown found:**
```
⚠️  No presentation markdown found in [path]
```
Result: Continues without presentation content

**Meeting file already exists:**
```
⚠️  Meeting file already exists: [path]
    Use --update flag to update existing file, or omit -n to create new meeting
```
Solution: Add `--update` flag to update existing file, or remove `-n` flag to auto-increment

## Integration with Other Skills

**Before agency-docs-updater:**
1. `videopublish` - Process and upload video to YouTube
2. `fathom` - Sync meeting transcript to Obsidian vault

**During agency-docs-updater:**
1. Launch `claude-code-guide` agent for fact-checking summary
2. Run `update_meeting_doc.py` script

**After agency-docs-updater:**
1. Verify Vercel deployment
2. Check live documentation URL

## Notes

- **Language handling**: Auto-detects Cyrillic/Latin, defaults to Russian translation for docs
- **Meeting numbering**: Supports both auto-increment and explicit specification via `-n` flag
- **Update mode**: Use `--update` with `-n` to replace existing meeting docs
- **Technical terms**: Translation preserves English terms (MCP, Skills, Claude Code, etc.)
- **Presentation auto-detection**: Handles multiple labs cleanly
- **Frontmatter**: Must be manually edited (title/description placeholders)
- **Git operations**: Manual to allow review before pushing
- **Idempotent**: Safe to run multiple times with same inputs
