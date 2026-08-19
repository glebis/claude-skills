# Trail Check-in Interactive Session

You are conducting an interactive trail check-in session. Follow this structured workflow:

## Step 1: List Available Trails

Run the trail listing script:

```bash
python3 ~/.claude/skills/trail-checkin/scripts/trail_checkin.py list
```

Parse the JSON response and prepare a summary showing:
- Trail name
- Status and velocity
- Last updated date
- Brief objective preview (first 80 chars)

## Step 2: Select Trails to Check In

Use `AskUserQuestion` with `multiSelect: true` to let the user choose which trails to review.

Present options with:
- **header**: "Select trails"
- **question**: "Which trails would you like to check in with today?"
- **options**: One per trail with:
  - **label**: Trail name
  - **description**: Status, last updated, velocity (e.g. "Active • Updated 2026-01-19 • Medium velocity")

## Step 3: For Each Selected Trail

For each trail the user selected, run through this sequence:

### 3.1 Load Trail Details

```bash
python3 ~/.claude/skills/trail-checkin/scripts/trail_checkin.py show "<trail-name>"
```

Show the user a concise summary:
- Objective
- Last updated date
- Current key metrics (2-3 most important ones)
- Number of open questions

### 3.2 Ask Check-in Questions

Use `AskUserQuestion` for each of these (one question at a time, wait for response):

**Question 1: Progress Made**
- header: "Progress"
- question: "What progress have you made on [Trail Name] since [last_updated]?"
- options:
  - "Significant progress - multiple milestones"
  - "Some progress - steady movement"
  - "Minimal progress - mostly planning"
  - "No progress - paused/stuck"

**Question 2: New Markers** (if progress made)
- header: "Milestones"
- question: "What milestones or achievements should we record?"
- options:
  - "Major milestone reached"
  - "Project deliverable completed"
  - "Research phase completed"
  - "No markers to add"

If user selects anything except "No markers", ask for details in follow-up.

**Question 3: Metrics Update**
- header: "Metrics"
- question: "Do any metrics need updating?"
- Show current metrics from the trail
- options:
  - "Yes - numbers changed"
  - "No - metrics unchanged"

If yes, ask which metrics and new values.

**Question 4: Tasks Review**
- header: "Tasks"
- question: "Task status changes?"
- options:
  - "Completed tasks to mark done"
  - "New tasks to add"
  - "Both completed and new"
  - "No task changes"

Get details if needed.

**Question 5: Open Questions**
- header: "Questions"
- question: "Any updates to open questions?"
- options:
  - "Question resolved"
  - "New question to add"
  - "Both resolved and new"
  - "No changes"

**Question 6: Direction Check**
- header: "Direction"
- question: "Is the trail's direction still accurate?"
- Show current direction from frontmatter
- options:
  - "Yes - direction unchanged"
  - "Needs adjustment"
  - "Major shift needed"

**Question 7: Status Check**
- header: "Status"
- question: "Should the trail status change?"
- Show current status
- options:
  - "Keep as [current status]"
  - "Pause trail"
  - "Archive/complete trail"
  - "Reactivate trail"

**Question 8: Next Review**
- header: "Next review"
- question: "When should we check in again?"
- options:
  - "1 week" (for high-velocity trails)
  - "2 weeks" (for medium velocity)
  - "1 month" (for exploration trails)
  - "Custom date"

### 3.3 Update Trail File

Based on user responses, update the trail markdown file:

1. Update frontmatter:
   - `last_updated: YYYY-MM-DD` (today's date)
   - `next_review: YYYY-MM-DD` (based on answer to Q8)
   - `status:` (if changed)
   - `velocity:` (infer from progress report)

2. Add progress marker to table (if provided):
   ```
   | [[YYYYMMDD]] | Brief description | Evidence/link |
   ```

3. Update metrics table with new values

4. Update tasks:
   - Mark completed tasks with ✓ or remove
   - Add new tasks to appropriate section

5. Update open questions:
   - Remove resolved questions
   - Add new questions

6. Add to "Published (Recent)" or relevant section if deliverables mentioned

After updating, show user a concise summary:
```
Updated Trail: [Name]
- Last updated: 2026-01-19
- Added marker: [description]
- Updated metrics: [metric name] → [new value]
- Completed tasks: [count]
- Added tasks: [count]
- Next review: 2026-01-26
```

## Step 4: Session Summary

After all selected trails are checked in, provide a final summary:

```
✓ Trail Check-in Complete

Reviewed trails:
- [Trail 1]: [key update]
- [Trail 2]: [key update]
- [Trail 3]: [key update]

Next reviews scheduled:
- [Trail 1]: [date]
- [Trail 2]: [date]
```

## Important Guidelines

- **Be concise** - trail check-ins should feel quick and effortless
- **One question at a time** - don't overwhelm with multiple questions
- **Preserve context** - when updating files, maintain existing structure
- **Use exact dates** - always use YYYY-MM-DD format
- **Respect user time** - if user indicates minimal progress, skip detailed questions
- **Be encouraging** - frame updates positively, acknowledge any progress

## Example Flow

```
User: /trail-checkin

Claude: Found 15 active trails. Which would you like to check in with?
[multiSelect: Mental Health Tech, Voice Claude, Salience, ...]

User: [selects Mental Health Tech, Salience]

Claude: Let's check in with Trail: Mental Health Tech

Objective: Run @mentalhealthtech Telegram channel...
Last updated: 2026-01-19
Key metrics: 78 posts (target: 100)

What progress have you made since 2026-01-19?
[options presented]

User: Some progress - steady movement

Claude: What milestones should we record?
[options presented]

User: Project deliverable completed

Claude: Please describe the milestone:

User: Published Vastaamo hack post analyzing Finnish therapy data breach

[continues through questions...]

Claude: Updated Trail: Mental Health Tech
- Added marker: Vastaamo hack post published
- Updated posts: 78
- Next review: 2026-01-26

Now checking in with Trail: Salience...

[repeats for each selected trail]

Claude: ✓ Trail Check-in Complete

Reviewed: Mental Health Tech, Salience
Next reviews: Jan 26, Feb 2
```