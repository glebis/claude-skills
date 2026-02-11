# Insight Extractor Skill - Implementation Instructions

## Overview
Parse the `/insights` report from `~/.claude/usage-data/report.html`, extract actionable items into structured markdown, save to vault, link from daily note, update MoC, and create tasks for automation candidates.

## Three Modes

### Mode 1: Auto (default)
`/insight-extractor` -- reads report, extracts all 6 categories, saves everything automatically.

### Mode 2: Interactive
`/insight-extractor --interactive` -- reads report, then walks user through each category with AskUserQuestion, letting them cherry-pick which items to keep, edit priorities, and decide what gets task files.

### Mode 3: Configure
`/insight-extractor --configure` -- walks user through configuration using AskUserQuestion, saves preferences to config file.

---

## Configuration

### Config file location
```
.claude/skills/insight-extractor/config.json
```

### Loading config
Before any extraction run (auto or interactive), read the config file:
```bash
CONFIG=".claude/skills/insight-extractor/config.json"
```
If config file exists, read it with the Read tool and parse the JSON. If it doesn't exist, use these defaults:
```json
{
  "insights_folder": "Research/Insights",
  "tasks_folder": "Tasks/inbox",
  "daily_folder": "Daily",
  "moc_file": "MoC - Insights.md",
  "date_format": "YYYYMMDD",
  "include_machine": true,
  "include_statistics": true,
  "auto_create_tasks": true,
  "stale_report_days": 7
}
```

### Date format handling
The `date_format` setting controls how dates appear in filenames and frontmatter:
- `YYYYMMDD` -> `20260211` (default, compact)
- `YYYY-MM-DD` -> `2026-02-11` (ISO standard)

Map to bash `date` format strings:
- `YYYYMMDD` -> `date +"%Y%m%d"`
- `YYYY-MM-DD` -> `date +"%Y-%m-%d"`

Use the configured format for:
- Insight filenames: `{date_format}-insights-{machine}.md`
- Frontmatter `created_date`: `'[[{date_format}]]'`
- Task filenames: `{date_format}-automate-{slug}.md`
- Daily note lookup: `{daily_folder}/{date_format}.md`

### Configure mode (--configure)

When user runs `/insight-extractor --configure`, walk through these questions:

#### Question 1: Output folders
```
AskUserQuestion:
  question: "Where should insight files be saved?"
  header: "Insights folder"
  options:
    - label: "Research/Insights" (current)
    - label: "Insights"
    - label: "Notes/Insights"
  multiSelect: false
```

#### Question 2: Tasks folder
```
AskUserQuestion:
  question: "Where should automation task files be created?"
  header: "Tasks folder"
  options:
    - label: "Tasks/inbox" (current)
    - label: "Tasks"
    - label: "Don't create task files"
  multiSelect: false
```

#### Question 3: Date format
```
AskUserQuestion:
  question: "Which date format for filenames?"
  header: "Date format"
  options:
    - label: "YYYYMMDD" -- compact, e.g. 20260211
    - label: "YYYY-MM-DD" -- ISO, e.g. 2026-02-11
  multiSelect: false
```

#### Question 4: Machine name
```
AskUserQuestion:
  question: "Include machine name in filenames?"
  header: "Machine name"
  options:
    - label: "Yes (default)" -- e.g. 20260211-insights-macbook-pro.md
    - label: "No" -- e.g. 20260211-insights.md
  multiSelect: false
```

#### Question 5: Statistics section
```
AskUserQuestion:
  question: "Include session statistics (outcomes, satisfaction, tool errors) in insight files?"
  header: "Statistics"
  options:
    - label: "Yes (default)"
    - label: "No"
  multiSelect: false
```

#### Question 6: Daily notes folder
```
AskUserQuestion:
  question: "Where are your daily notes?"
  header: "Daily notes"
  options:
    - label: "Daily" (current)
    - label: "Journal"
    - label: "Daily Notes"
  multiSelect: false
```

#### Question 7: MoC file
```
AskUserQuestion:
  question: "Which MoC file should track insights?"
  header: "MoC file"
  options:
    - label: "MoC - Insights.md" (current)
    - label: "Don't update MoC"
  multiSelect: false
```

#### Question 8: Stale report threshold
```
AskUserQuestion:
  question: "Warn if /insights report is older than how many days?"
  header: "Stale threshold"
  options:
    - label: "7 days (default)"
    - label: "3 days"
    - label: "14 days"
    - label: "Don't warn"
  multiSelect: false
```

After all questions, save the config:
```json
{
  "insights_folder": "<user choice>",
  "tasks_folder": "<user choice or null if disabled>",
  "daily_folder": "<user choice>",
  "moc_file": "<user choice or null if disabled>",
  "date_format": "YYYYMMDD or YYYY-MM-DD",
  "include_machine": true/false,
  "include_statistics": true/false,
  "auto_create_tasks": true/false,
  "stale_report_days": 3/7/14/null
}
```

Write the JSON to `.claude/skills/insight-extractor/config.json` using the Write tool.

Confirm to user:
```
Configuration saved to .claude/skills/insight-extractor/config.json

Settings:
- Insights folder: {insights_folder}
- Tasks folder: {tasks_folder}
- Daily notes: {daily_folder}
- MoC file: {moc_file}
- Date format: {date_format}
- Machine name: {include_machine}
- Statistics: {include_statistics}
- Stale warning: {stale_report_days} days
```

---

## Step 0: Load Configuration

Read config from `.claude/skills/insight-extractor/config.json`. If file doesn't exist, use defaults (see Configuration section above). Store all values in variables for use throughout extraction.

## Step 1: Locate the /insights Report

The built-in `/insights` command generates an HTML report at:
```
~/.claude/usage-data/report.html
```

Additional data may be in:
```
~/.claude/usage-data/facets/    (JSON facet files)
```

### Check for report:
```bash
REPORT="$HOME/.claude/usage-data/report.html"
ls -la "$REPORT" 2>/dev/null
```

If report doesn't exist: tell user "Run `/insights` first to generate the report, then run `/insight-extractor`."

If report exists, check its modification time to determine freshness:
```bash
stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$HOME/.claude/usage-data/report.html"
```

### Parse the HTML report

Read the HTML file directly with the Read tool. The report contains structured sections:
- At a Glance (summary)
- Project Areas
- Interaction Style
- Impressive Workflows
- Friction Analysis
- Suggestions (CLAUDE.md additions, features to try, usage patterns)
- On the Horizon (ambitious workflows)

Also check for JSON facet files in `~/.claude/usage-data/facets/` which may contain structured data that's easier to parse than HTML.

## Step 2: Determine Machine Name

```bash
MACHINE=$(hostname -s | tr '[:upper:]' '[:lower:]')
```

Always lowercase the machine name for consistent filenames.

If user passes `--no-machine`, omit machine from filename.

## Step 3: Check for Existing Insight File

Use configured `date_format` and `insights_folder`:
```bash
# date_format "YYYYMMDD" -> date +"%Y%m%d", "YYYY-MM-DD" -> date +"%Y-%m-%d"
TODAY=$(date +"<format from config>")
MACHINE=$(hostname -s | tr '[:upper:]' '[:lower:]')
# If include_machine is false, omit machine suffix
TARGET="${insights_folder}/${TODAY}-insights-${MACHINE}.md"
```

If file exists, ask user: "Insight file for today already exists. Overwrite or append?"

## Step 4: Extract Insights (6 Categories)

Parse the report and categorize into:

#### Category 1: Action Items
Tasks and CLAUDE.md additions suggested by the report.
- Format: `- [ ] **[Owner]**: Description (source: section)`
- Sources: `suggestions.claude_md_additions`, `friction_analysis`, `usage_patterns`

#### Category 2: Useful Prompts & Patterns
Effective prompting strategies from `suggestions.usage_patterns` and `interaction_style`.
- Format: `- **Pattern name**: Description\n  > Example prompt or approach`
- Sources: `copyable_prompt` fields, `interaction_style.key_pattern`

#### Category 3: Technical Learnings
Insights from friction analysis and what-works sections.
- Format: `- **Topic**: What was learned (context)`
- Sources: `friction_analysis.categories`, `what_works.impressive_workflows`

#### Category 4: Workflow Improvements
From suggestions and usage patterns.
- Format: `- **Improvement**: Description -> Impact`
- Sources: `suggestions.usage_patterns`, `friction_analysis`

#### Category 5: Tool Discoveries
Features to try and new capabilities.
- Format: `- **Tool/Command**: What it does and when to use it`
- Sources: `suggestions.features_to_try`

#### Category 6: Automation Candidates
From on-the-horizon and usage patterns.
- Format: `- **Task**: Description #automation-candidate`
  - If agent-runnable: add `#agent-task`
  - Estimated effort: low/medium/high
  - Automation approach: brief suggestion
- Sources: `on_the_horizon.opportunities`, `suggestions.usage_patterns`

---

## Interactive Mode (--interactive)

When running in interactive mode, use AskUserQuestion after extracting each category.

### Step 4i-A: Present Action Items
After extracting action items, use AskUserQuestion:

```
Question: "Which action items should be included?"
Options:
- "All N items" -- include everything extracted
- "Let me review each" -- present items one by one
- "Skip action items" -- omit this category
```

If "Let me review each": present items in batches of 3-4 using AskUserQuestion with multiSelect=true, letting user check which to keep.

### Step 4i-B: Present Automation Candidates
Use AskUserQuestion:

```
Question: "Which automation candidates should get task files in Tasks/inbox/?"
Options (multiSelect=true):
- Each automation candidate as a separate option with effort estimate
```

### Step 4i-C: Priority Override
Use AskUserQuestion:

```
Question: "Any priority overrides for the extracted items?"
Options:
- "Keep defaults" -- use extracted priorities
- "Mark all CLAUDE.md items as high" -- prioritize config improvements
- "Mark all automation tasks as high" -- prioritize automation backlog
- "Custom" -- user specifies
```

### Step 4i-D: Additional Context
Use AskUserQuestion:

```
Question: "Add personal notes or context to this insight file?"
Options:
- "No, save as-is"
- "Yes, I'll add notes" -- prompt for free text to append
```

---

## Step 5: Generate Insight File

**File path**: `{config.insights_folder}/{date}-insights-{machine}.md`

**Template**:
```markdown
---
created_date: '[[YYYYMMDD]]'
type: insights
machine: {hostname}
source: /insights
report_date: YYYY-MM-DD
tags:
  - insights
  - insights/{YYYY-MM}
---

# Insights - YYYY-MM-DD ({machine})

*Generated: YYYY-MM-DD HH:MM | Source: ~/.claude/usage-data/report.html*

## Action Items
- [ ] **[Owner]**: Description (source: project/context)

## Useful Prompts & Patterns
- **Pattern name**: Description
  > Example

## Technical Learnings
- **Topic**: What was learned

## Workflow Improvements
- **Improvement**: Description -> Impact

## Tool Discoveries
- **Tool**: Description and use case

## Automation Candidates
- **Task**: Description #automation-candidate #agent-task
  - Effort: low | Approach: brief suggestion

---
*Source: ~/.claude/usage-data/report.html*
```

## Step 6: Link from Daily Note

Append to today's daily note (`{config.daily_folder}/{date}.md`). Prefer adding under `## Insights` section if it exists, otherwise under `## log`:

```markdown
- [[YYYYMMDD-insights-{machine}|Insights ({machine})]]
```

If daily note doesn't exist, create it from template first.

## Step 7: Update MoC

If `config.moc_file` is set (not null), append new entry to the configured MoC file under `## Recent Insights` section. If `config.moc_file` is null, skip this step.

```markdown
- [[YYYYMMDD-insights-{machine}]] - {summary_line}
```

Where `summary_line` is a 1-line summary like "3 actions, 2 automations, hook safety patterns"

## Step 8: Create Tasks for Automation Candidates

If `config.auto_create_tasks` is true, create task files. If false, skip this step.

For each automation candidate (all in auto mode, user-selected in interactive mode), create a task file in `{config.tasks_folder}/`:

**File**: `{config.tasks_folder}/{date}-automate-{slug}.md`

```yaml
---
created: YYYY-MM-DDTHH:MM:00
status: inbox
tags: [automation-candidate]
priority: medium
context: From insights extraction
source: insights
agent_task: true/false
---

# Automate: {task description}

**Source**: [[YYYYMMDD-insights-{machine}]]
**Effort**: low/medium/high
**Approach**: {brief suggestion}

## Details
{fuller description from insight extraction}
```

## Step 9: Confirmation with TLDR

After saving all files, output a concise summary with a TLDR and one key insight.

Generate the TLDR by identifying the single most impactful theme across all 6 categories. The key insight should be the one actionable finding that would deliver the most value if acted on today.

Report to user:
```
Insights extracted for {date} on {machine}

TLDR: {1-2 sentence summary of the most important pattern or finding across all categories}

Key insight: {the single most actionable finding -- what to do and why it matters}

Summary:
- Action Items: N
- Prompts & Patterns: N
- Technical Learnings: N
- Workflow Improvements: N
- Tool Discoveries: N
- Automation Candidates: N (M agent-runnable)

Saved to: {insights_folder}/{date}-insights-{machine}.md
Tasks created: N (in {tasks_folder}/)
Daily note updated: {daily_folder}/{date}.md
MoC updated: {moc_file}
```

## Error Handling

### /insights Not Run Yet
- Check `~/.claude/usage-data/report.html`
- If missing: "No /insights report found. Run `/insights` first, then run `/insight-extractor`."

### Report is Stale
- If report.html is older than 7 days, warn user: "Report is from {date}. Run `/insights` to get fresh data, or proceed with existing report?"

### Missing Daily Note
- Create from template at `templates/_Template Daily.md`
- Use Templater format for dates

### Missing MoC
- Create `MoC - Insights.md` from template (see MoC structure in CLAUDE.md)

### Missing Tasks Folder Structure
- Create `Tasks/inbox/` if it doesn't exist

## Machine-Specific Behavior

- **Default**: Include machine name (hostname -s) in filename
- **Flag**: User can pass argument to disable: `/insight-extractor --no-machine`
- **Merging**: When reviewing across machines, MoC shows all machine files for same date together
- **Use case**: Gleb has 2 machines, insights differ per machine since sessions are local

## Integration Points

- **~/.claude/usage-data/report.html**: Source data from built-in /insights command
- **~/.claude/usage-data/facets/**: Additional structured JSON data
- **MoC - Insights.md**: Master tracking of all insight files
- **MoC - Personal Productivity.md**: Link from Session-as-Memory theme
- **Daily notes**: Quick reference from daily log
- **Tasks/inbox/**: Automation candidates become actionable tasks
- **Weekly review**: Review MoC to track patterns across days/machines
