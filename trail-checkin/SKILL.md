---
name: trail-checkin
description: 'Interactive trail review and update process for Obsidian vault at ~/Brains/brain. Lists available Trails, lets you select which to check in with, then walks through structured questions for each (progress, markers, tasks, metrics, open questions, status, next review date) and updates the trail file. Use for weekly reviews, milestone moments, context switching, or monthly reflection. Triggers on /trail-checkin.'
---

Base directory for this skill: ~/.Codex/skills/trail-checkin

# Trail Check-in Skill

Interactive trail review and update process. Lists available trails, lets you select which to check in with, then walks through structured questions for each trail to capture progress, update markers, and reflect on direction.

## Prerequisites

- Obsidian vault at `~/Brains/brain`
- Trails located in `~/Brains/brain/Trails/`
- Trail files follow naming pattern `Trail - *.md`

## Usage

Run the skill to start an interactive check-in:

```bash
/trail-checkin
```

Or invoke directly:

```bash
python3 ~/.Codex/skills/trail-checkin/scripts/trail_checkin.py
```

## How It Works

### Step 1: List Trails

Script scans `Trails/` folder and extracts:
- Trail name
- Status (active/paused/completed)
- Last updated date
- Objective (first line summary)

Returns JSON with trail list.

### Step 2: Select Trails

Codex uses `AskUserQuestion` with multiSelect to let you choose which trails to check in with.

### Step 3: Check-in Questions (per trail)

For each selected trail, Codex asks:

1. **Progress made** - What happened since last check-in?
2. **Markers to add** - Any new milestones reached?
3. **Tasks completed** - Which tasks can be marked done?
4. **New tasks** - What needs to be added?
5. **Metrics update** - Any numbers to update?
6. **Open questions** - New questions or resolved ones?
7. **Status change** - Still active? Paused? Completed?
8. **Next review date** - When to check in again?

### Step 4: Update Trails

Codex updates each trail file with:
- New progress markers
- Updated metrics
- Task status changes
- New open questions
- Updated `last_updated` date
- Next review date

## Output

Returns summary of updates made to each trail.

## Example Session

```
User: /trail-checkin

Codex: Found 5 trails. Which would you like to check in with?
[multiSelect: Mental Health Tech, Codex Lab, Telegram Agent, Salience, Voice Codex]

User: [selects Mental Health Tech, Voice Codex]

Codex: Let's check in with Trail: Mental Health Tech

What progress have you made since last update (2026-01-19)?
[short answer input]

User: Published Vastaamo hack post, drafted privacy ethics analysis

Codex: Should we add any progress markers?
[yes/no]

[continues through questions...]

Codex: Updated Trail: Mental Health Tech
- Added marker: Vastaamo hack post published
- Updated posts metric: 78
- Marked task complete: Publish privacy post
- Updated last_updated: 2026-01-19

Now checking in with Trail: Voice Codex...
```

## Script API

```bash
# List all trails
python3 scripts/trail_checkin.py list

# Get trail details
python3 scripts/trail_checkin.py show "Mental Health Tech"
```

Returns JSON for programmatic use.

## When to Use

- Weekly reviews
- Project milestone moments
- When switching contexts between trails
- Monthly reflection sessions
- When a trail needs status update
