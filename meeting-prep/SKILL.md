---
name: meeting-prep
description: Prepare for upcoming meetings — pulls Cal.com bookings, researches participants, audits previous sessions from Obsidian vault, and creates prep notes. Also links prep notes to post-meeting session notes.
---

# Meeting Prep

Prepares comprehensive meeting prep notes for upcoming Cal.com bookings by researching participants and auditing session history from the Obsidian vault.

## Configuration

All paths and settings are in `config.yaml` next to this file. Read it before executing any steps.

```yaml
# config.yaml — key fields:
vault.root          # Obsidian vault root
vault.meetings      # Where meeting notes live
vault.people_search_depth  # How deep to search for person notes
prep_notes.prefix   # Filename prefix (default: "prep")
prep_notes.type_tag # Frontmatter type value (default: "meeting-prep")
calcom.lookahead_days  # Default booking lookahead
calcom.timezone     # Display timezone
calcom.time_format  # 12h or 24h
```

**On first run:** Read `config.yaml` from the same directory as this SKILL.md file. Resolve `~` to the user's home directory. Use these values for all path references below — never hardcode paths.

## When to Use

- User invokes `/meeting-prep`
- User asks to prepare for upcoming meetings/sessions/calls
- User says "who do I have coming up" or "prep for my next session"

## Arguments

- No args → prep all bookings in the next `calcom.lookahead_days` days
- Date (`2026-06-03`) → prep bookings on that specific date
- Name (`Greg`) → prep only bookings with that participant
- `tomorrow` / `today` / `this week` → natural date ranges
- `link` → scan for unlinked prep↔session note pairs and connect them
- `sync` → reconcile prep notes with Cal.com booking state (cancelled, rescheduled, deleted)
- `status` → show Dataview-style overview of all prep notes and their link status

## Workflow

### Step 0: Load Config

Read `config.yaml` from the skill directory. Resolve all paths (expand `~`). Store as variables for use in subsequent steps:

```
VAULT_ROOT     = config.vault.root
MEETINGS_DIR   = config.vault.meetings
PEOPLE_DEPTH   = config.vault.people_search_depth
PREP_PREFIX    = config.prep_notes.prefix
TYPE_TAG       = config.prep_notes.type_tag
LOOKAHEAD      = config.calcom.lookahead_days
TIMEZONE       = config.calcom.timezone
```

### Step 1: Fetch Bookings

Load Cal.com MCP tools via ToolSearch (query: "calcom", max_results: 20). Then:

1. Call `get_bookings` to retrieve upcoming bookings (status: accepted) within the target date range
2. For each booking, call `get_booking_attendees` to get the full attendee list — Cal.com bookings can have multiple attendees (e.g., lab sessions, masterminds, group calls)
3. Filter by arguments if provided (date, name)
4. If no bookings found, report and stop

### Step 2: Search Vault for Session History

For each unique participant, search `MEETINGS_DIR` for previous session notes:

```bash
grep -rl "PARTICIPANT_NAME" $MEETINGS_DIR 2>/dev/null
```

Read matching files (up to 5 most recent) to extract:
- Date and duration of each past session
- Key topics discussed (from headings, summary sections, or transcript excerpts)
- Any action items or follow-ups mentioned
- Session source (Fathom, Granola, manual)

Also search for a person note in the vault:
```bash
find $VAULT_ROOT -maxdepth $PEOPLE_DEPTH -name "*PARTICIPANT_NAME*" -not -path "*/Meetings/*" 2>/dev/null
```

### Step 3: Research Participants (Workflow)

Use the Workflow tool to parallelize participant research. Pass `MEETINGS_DIR` and `VAULT_ROOT` via workflow args so subagents know where to search.

For each unique participant, spawn an agent that:

1. Web-searches the participant's name + company/email domain
2. Checks LinkedIn profile (via web search, not direct scrape)
3. Summarizes: role, company, recent activity, mutual context
4. For returning participants: cross-references with vault history to identify patterns and continuity points

### Step 4: Create Prep Notes in Obsidian

There are two modes depending on the number of attendees:

- **Solo session** (1 attendee): one prep note per session, exactly as described below. Filename: `YYYYMMDD-$PREP_PREFIX-PARTICIPANT_SLUG.md`
- **Group session** (2+ attendees): one prep note for the whole session. Filename: `YYYYMMDD-$PREP_PREFIX-EVENT_SLUG.md` (where `EVENT_SLUG` is the Cal.com event type slug in lowercase kebab-case). The note lists all attendees with brief profiles, and the research section covers all participants.

**If a prep note already exists for that date+session, update it instead of creating a duplicate.**

#### Solo Session Template

Use this template:

```markdown
---
type: $TYPE_TAG
date: YYYY-MM-DD
participant: "Full Name"
email: email@example.com
event_type: "Cal.com event type name"
duration: X min
time: "HH:MM $TIMEZONE"
zoom_link: "https://..."
status: prep
session_note: ""
tags:
  - $TYPE_TAG
  - SESSION_TYPE
---

# Prep: Full Name — YYYY-MM-DD

## Session Info
- **Time**: HH:MM–HH:MM $TIMEZONE (Day of week)
- **Type**: Event type name (X min)
- **Location**: Zoom link
- **Participant timezone**: Timezone

## About FIRST_NAME

RESEARCH_SUMMARY

## Previous Sessions (N total)

### Most Recent: YYYY-MM-DD — Event Type
KEY_TOPICS_AND_OUTCOMES

### Earlier Sessions
BRIEF_LIST_WITH_DATES_AND_TOPICS

## Continuity & Follow-ups

- Outstanding action items from previous sessions
- Recurring themes or patterns
- Progress on previously discussed goals

## Prep Ideas

- Conversation starters from research
- Topics to revisit based on session history
- Questions to explore

## Notes

_Space for pre-meeting thoughts and during-meeting notes_
```

#### Sequential Bookings for the Same Participant

When multiple bookings exist for the same participant within the lookahead window (e.g., Jun 3 and Jun 9), sort them by date and handle as follows:

- **First booking**: standard prep note, no changes.
- **Second+ booking**: the prep note should acknowledge the earlier session:
  - Add `prior_prep: "[[YYYYMMDD-prep-participant]]"` to frontmatter, pointing to the earlier prep note
  - Include a **## Prior Session** section after Session Info:
    ```markdown
    ## Prior Session
    A session with FIRST_NAME is scheduled for PRIOR_DATE — it will have happened by the time this session occurs.
    Update this note after the PRIOR_DATE session with fresh context.
    ```
  - Keep the full research/history sections but flag them as "will be stale after PRIOR_DATE" so the user knows to revisit
  - The note is still useful as-is for background research, but action items and continuity will need a post-session refresh

For first-time participants (no vault history), replace the "Previous Sessions" and "Continuity" sections with:

```markdown
## First Meeting

No previous sessions found in vault.

## Context & Talking Points

- Research-based conversation starters
- Questions to understand their goals and needs
- How they likely found you / booking context
```

#### Group Session Template

For bookings with 2+ attendees, use this template instead:

```markdown
---
type: $TYPE_TAG
date: YYYY-MM-DD
participants:
  - name: "Full Name 1"
    email: email1@example.com
  - name: "Full Name 2"
    email: email2@example.com
event_type: "Cal.com event type name"
duration: X min
time: "HH:MM $TIMEZONE"
zoom_link: "https://..."
status: prep
session_note: ""
tags:
  - $TYPE_TAG
  - SESSION_TYPE
---

# Prep: Event Type Name — YYYY-MM-DD

## Session Info
- **Time**: HH:MM–HH:MM $TIMEZONE (Day of week)
- **Type**: Event type name (X min)
- **Location**: Zoom link
- **Attendees**: N participants

## Attendees

### FIRST_NAME_1 LAST_NAME_1
BRIEF_PROFILE_AND_RESEARCH_SUMMARY

### FIRST_NAME_2 LAST_NAME_2
BRIEF_PROFILE_AND_RESEARCH_SUMMARY

## Previous Sessions per Attendee

SUMMARY_OF_VAULT_HISTORY_PER_ATTENDEE (grouped by person, skip if no history)

## Prep Ideas

- Group dynamics to consider
- Topics to cover with the full group
- Individual follow-ups to weave in

## Notes

_Space for pre-meeting thoughts and during-meeting notes_
```

### Step 5: Report

After creating all prep notes, output a concise summary:
- List of prepped sessions (date, time, participant, event type)
- Key highlights (first-timers flagged, notable follow-ups from history)
- Links to the created prep notes as `[[YYYYMMDD-PREP_PREFIX-participant-slug]]`

## Notes

- Always convert times to the configured `TIMEZONE` for display
- Participant research should be respectful — professional context only
- If a participant has many previous sessions (>5), focus on the 3 most recent + overall patterns
- The prep note should be actionable: things to discuss, not just a dossier
- Tag first-time participants so they're easy to filter in Obsidian
- For group sessions, use the event type slug for the filename instead of participant name

## Linking: `meeting-prep link`

When invoked with `link`, scan for prep notes that don't yet have a linked session note, and connect them.

### How It Works

1. Find all prep notes:
```bash
grep -rl "type: $TYPE_TAG" $MEETINGS_DIR 2>/dev/null
```

2. For each prep note with `session_note: ""` (unlinked):
   - Extract `date` and `participant` from frontmatter
   - Search for a matching post-meeting note by date + participant name:
   ```bash
   find $MEETINGS_DIR -name "YYYYMMDD-*" -not -name "*$PREP_PREFIX*" | xargs grep -l "PARTICIPANT_NAME" 2>/dev/null
   ```
   - Fathom notes have `participants:` in YAML frontmatter; Granola notes have `participants:` too
   - Match by date prefix AND participant name appearing in the file

3. When a match is found, update both files:

   **In the prep note:**
   - Update frontmatter: `session_note: "[[YYYYMMDD-matching-note-filename]]"`
   - Update `status: prep` → `status: done`

   **In the session note:**
   - Append a `## Prep Note` section at the end (before any existing `## See also` section if present):
   ```markdown
   ## Prep Note
   - [[YYYYMMDD-PREP_PREFIX-participant-slug]]
   ```
   - If the session note already has a `## See also` section, add the link there instead of creating a new section

4. Report which notes were linked and which prep notes are still unlinked (meeting hasn't happened yet or transcript not imported)

### Matching Rules

- Date must match exactly (same YYYYMMDD prefix)
- Participant name match is fuzzy: check both full name and first name, case-insensitive
- Skip files that are themselves prep notes (`-$PREP_PREFIX-` in filename)
- If multiple session notes match the same date+participant, prefer the one with a transcript (longer file)
- Never create duplicate links — check if the link already exists before adding

## Sync: `meeting-prep sync`

When invoked with `sync`, reconcile all active prep notes with the current state of their Cal.com bookings. This catches cancellations, reschedules, and deleted bookings that would otherwise leave stale prep notes in the vault.

### How It Works

1. **Find all active prep notes:**
```bash
grep -rl "type: $TYPE_TAG" $MEETINGS_DIR 2>/dev/null
```
Filter to only notes where `status: prep` (skip `done`, `cancelled`, `orphaned`).

2. **Extract booking identifiers** from each prep note's frontmatter:
   - `date` (YYYY-MM-DD)
   - `participant` (full name)
   - `email` (attendee email)
   - `event_type` (Cal.com event type name)

3. **Check Cal.com state:** Load Cal.com MCP tools via ToolSearch (query: "calcom", max_results: 20). Call `get_bookings` to retrieve bookings covering the date range of all active prep notes. For each prep note, match against Cal.com bookings by date + attendee email.

4. **Update based on booking status:**

   **Cancelled** — the booking exists on Cal.com with a cancelled status:
   - Update frontmatter: `status: prep` → `status: cancelled`
   - Append a section to the note:
   ```markdown
   ## Cancelled
   Booking was cancelled on YYYY-MM-DD (detected during sync).
   ```

   **Rescheduled** — the booking exists but with a different date/time:
   - Update the `date` field in frontmatter to the new date
   - Update the `time` field to the new time
   - Rename the file from `YYYYMMDD-$PREP_PREFIX-participant-slug.md` to `NEW_YYYYMMDD-$PREP_PREFIX-participant-slug.md`
   - Append a section to the note:
   ```markdown
   ## Rescheduled
   Moved from ORIGINAL_DATE to NEW_DATE (detected during sync on YYYY-MM-DD).
   ```

   **Still active** — booking exists, same date/time, accepted status:
   - No changes needed.

5. **Report what changed:** Output a summary table listing each prep note and the action taken (no change / cancelled / rescheduled / orphaned).

### Edge Cases

- **Booking not found on Cal.com** (may have been deleted entirely, or is older than Cal.com's retention): Update frontmatter `status: prep` → `status: orphaned`. Append:
  ```markdown
  ## Orphaned
  No matching booking found on Cal.com (detected during sync on YYYY-MM-DD). The booking may have been deleted.
  ```
- **Multiple bookings on the same day with the same participant**: Match by `event_type` in addition to date + attendee email to disambiguate. If ambiguity remains, skip the note and flag it in the report for manual review.
- **Prep notes with `status: done`**: Skip entirely — these are already linked to session notes and should not be modified by sync.

## Status & Queries: `meeting-prep status`

When invoked with `status`, scan all prep notes and report their current state. Also output useful Dataview queries the user can paste into their vault.

### Status Report

Scan `$MEETINGS_DIR` for files matching `*-$PREP_PREFIX-*.md`. For each, read frontmatter and report:

| Date | Participant | Status | Session Note |
|------|------------|--------|-------------|
| from `date` | from `participant` | `prep` or `done` | linked note or `—` |

After the table, output a **Top 5 most-met participants** summary by scanning all prep notes in the vault, counting occurrences per participant, and listing the top 5 with their session count and date of last meeting.

### Dataview Queries

Include these ready-to-paste queries in the status output:

**Upcoming preps (unlinked):**
````markdown
```dataview
TABLE participant AS "Who", time AS "Time", event_type AS "Type", duration + " min" AS "Duration"
FROM "Meetings"
WHERE type = "$TYPE_TAG" AND status = "prep"
SORT date ASC
```
````

**Completed preps (linked to session notes):**
````markdown
```dataview
TABLE participant AS "Who", date AS "Date", session_note AS "Session Note"
FROM "Meetings"
WHERE type = "$TYPE_TAG" AND status = "done"
SORT date DESC
```
````

**Prep coverage — sessions without a prep note:**
````markdown
```dataview
TABLE title AS "Session", date AS "Date", participants AS "Participants"
FROM "Meetings"
WHERE !contains(file.name, "$PREP_PREFIX") AND !contains(file.inlinks.file.name, "$PREP_PREFIX")
SORT date DESC
LIMIT 20
```
````

**All preps by participant:**
````markdown
```dataview
TABLE date AS "Date", status AS "Status", event_type AS "Type", session_note AS "Linked"
FROM "Meetings"
WHERE type = "$TYPE_TAG"
SORT participant ASC, date DESC
```
````

### Relationship & Activity Queries

**Meeting frequency by participant:**
````markdown
```dataview
TABLE length(rows) AS "Sessions", min(rows.date) AS "First", max(rows.date) AS "Last"
FROM "Meetings"
WHERE type = "$TYPE_TAG"
GROUP BY participant
SORT length(rows) DESC
```
````

**Participant timeline** (embed in a participant's person note — uses `this.participant` for context):
````markdown
```dataview
TABLE date AS "Date", event_type AS "Type", status AS "Status", session_note AS "Linked"
FROM "Meetings"
WHERE type = "$TYPE_TAG" AND participant = this.participant
SORT date DESC
```
````

**Recent meeting activity** (last 30 days, all sessions, cross-referenced with prep coverage):
````markdown
```dataview
TABLE title AS "Session", participants AS "With", 
  choice(contains(file.inlinks.file.name, "prep"), "✓", "—") AS "Prepped"
FROM "Meetings"
WHERE date >= date(today) - dur(30 days) AND !contains(file.name, "prep")
SORT date DESC
```
````

**First-timers list** (people met only once — potential follow-up candidates):
````markdown
```dataview
TABLE participant AS "Who", date AS "Met On", event_type AS "Type"
FROM "Meetings"  
WHERE type = "$TYPE_TAG"
GROUP BY participant
FLATTEN length(rows) AS count
WHERE count = 1
FLATTEN rows.date AS date
FLATTEN rows.event_type AS event_type
SORT date DESC
```
````
