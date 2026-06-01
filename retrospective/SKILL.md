---
name: retrospective
description: Interactive post-session retrospective that captures learnings, updates skills, and saves memories. Use when the user says "/retrospective", "let's do a retro", "what did we learn", "session review", "retro", or "wrap up". Also use at the end of long productive sessions when significant patterns or corrections emerged. Supports multi-session mode — by default processes all of today's sessions across projects.
---

# Retrospective

Interactive post-session retro. Scans sessions, asks focused questions, proposes concrete actions the user approves in one step.

## Modes

### Single-session mode (default when inside a substantial conversation)
Scans the current conversation only. This is the original behavior.

### Multi-session mode (default when invoked with no args, or with "today", or with a date)
Scans all sessions from a given day (default: today) across all projects. Extracts user corrections, skill failures, and patterns from JSONL transcripts.

**Trigger:** `/retrospective` at the start of a fresh session, or `/retrospective today`, or `/retrospective 2026-05-24`.

## Multi-Session Discovery

### Step 0 — Discover sessions

```bash
# Find today's sessions (default)
find ~/.claude/projects -maxdepth 2 -name "*.jsonl" -not -path "*/subagents/*" -mtime 0

# Or for a specific date, filter by file modification date
find ~/.claude/projects -maxdepth 2 -name "*.jsonl" -not -path "*/subagents/*" -newermt "YYYY-MM-DD" ! -newermt "YYYY-MM-DD + 1 day"
```

For each JSONL file found, extract a summary:
1. Parse the project name from the path (the directory name after `projects/`, decoded from the path-encoding)
2. Extract `user` and `assistant` messages (type `user` and `assistant`)
3. For user messages: `message.content` (may be string or array of `{type: "text", text: "..."}`)
4. For assistant messages: collect text blocks from `message.content` array where `type == "text"`
5. Build a condensed transcript: first 10 user messages + last 5 user messages (to capture corrections at the end)
6. Skip sessions with fewer than 3 user messages (too short to have learnings)

### Step 0b — Present session list

Show the user what was found:

```
Found N sessions today:
- project-name-1 (session-id[:8]) — "first user message preview..."
- project-name-2 (session-id[:8]) — "first user message preview..."
```

Then continue to Step 1a with the combined findings from all sessions. Each candidate action should note which session it came from (project name + short ID).

## Single-Session Process

### Step 0 — Gate Check (silent)

Scan the conversation and estimate session depth. Look for tool calls (Read, Edit, Write, Bash, Skill invocations), errors encountered, and back-and-forth exchanges. Don't try to count exactly — judge by feel:

- **Short session** (a quick question and answer, ~1-2 tasks) → **Fast mode** (Step 1b)
- **Substantial session** (multiple tasks, skill usage, errors, corrections) → **Full mode** (Step 1a)

### Step 1a — Full Mode

Silently scan the conversation and collect:

1. **Skills invoked** — which succeeded, which failed, workarounds applied
2. **User corrections** — explicit "no, do it this way" moments (highest signal)
3. **Repeated patterns** — same error hit multiple times, same workaround applied
4. **Cross-skill workflows** — 3+ skills chained in sequence

Then read existing state:
- Find the current project's memory directory: `glob ~/.claude/projects/*/memory/MEMORY.md` and read it plus relevant memory files
- Read skill files for any skills that were invoked (`~/.claude/skills/{name}/skill.md`)
- Check if Linear CLI exists: `test -f ~/.claude/skills/linear/scripts/linear && echo "configured" || echo "not configured"`

Generate up to **5 candidate actions**, ranked by signal strength:
1. User corrections (highest priority)
2. Failed/workarounded skills
3. Repeated patterns
4. Error patterns
5. Workflow patterns (lowest)

**Dedup rules:**
- If a candidate's content overlaps with an existing memory file → drop it
- If a skill update candidate overlaps with existing skill file content → drop it
- If Linear is not configured → omit any Linear task candidates

Present everything in a **single AskUserQuestion call** (up to 4 questions):

| # | Question | Type |
|---|----------|------|
| 1 | "Quick session check?" | Single select: `Productive / Mixed / Rough / Skip retro` |
| 2 | "What felt slow or broken?" | Free text via Other (optional) |
| 3 | "Anything to carry forward as a rule?" | Free text via Other (optional) |
| 4 | "Which of these should I save?" | Multi-select: generated candidates with descriptions. Always include a "Nothing / skip all" option. |

If Q1 = "Skip retro" → exit immediately.

If Q1 = "Rough" and Q2/Q3 are empty → exit with "Nothing to save — session closed." Don't add another question after the user already signaled they're done.

### Step 1b — Fast Mode

Single AskUserQuestion call with one question:
- "Anything worth remembering from this session?" with options:
  - "Nothing, we're done" (default)
  - Other (free text)

If "Nothing" → exit. If free text → save as memory, exit.

### Step 2 — Execute (silent, no re-confirmation)

For each approved item from Q4 (plus any insights from Q2/Q3 free text):

1. **Read the target file** before writing
2. **Check for conflicts/duplicates** against current content
3. **Write the change** if clean
4. **Skip with warning** if conflict detected

Action types and their targets:

| Type | Target | Tool |
|------|--------|------|
| Skill update | `~/.claude/skills/{name}/skill.md` | Edit |
| Memory (feedback) | Current project's `memory/feedback_*.md` + MEMORY.md | Write |
| Memory (project) | Current project's `memory/project_*.md` + MEMORY.md | Write |
| CLAUDE.md rule | `~/.claude/CLAUDE.md` or project CLAUDE.md | Edit |
| Linear task | `~/.claude/skills/linear/scripts/linear issue create --title "..." --description "..."` | Bash |

### Step 3 — Summary (brief)

One-line per action taken:
```
Updated telegram skill — added chat type mismatch note
Saved memory — Qwen /api/chat not /api/generate
Skipped: pdf-generation update (already documented)
```

Done. No trailing commentary.

## JSONL Transcript Format

Session transcripts are stored as JSONL files at `~/.claude/projects/{project-path}/{session-id}.jsonl`.

Each line is a JSON object with a `type` field. Relevant types:
- `user` — user message. Content at `message.content` (string or array of `{type: "text", text: "..."}`)
- `assistant` — Claude's response. Content at `message.content` (array of content blocks; extract where `type == "text"`)
- `ai-title` — auto-generated session title

To extract a readable transcript from a JSONL file, use a Python one-liner or read the file and filter for `user`/`assistant` types.

**Project name decoding:** The directory name uses the absolute path with slashes replaced by dashes, e.g., `-Users-glebkalinin-ai-projects-foo` → `~/ai_projects/foo`.

## Mode Selection Logic

When `/retrospective` is invoked:
1. If the current conversation has 10+ user messages → **single-session mode** (retro this conversation)
2. If the current conversation is short (just the `/retrospective` invocation) → **multi-session mode** (scan today's sessions)
3. If args contain a date (e.g., "today", "yesterday", "2026-05-24") → **multi-session mode** for that date
4. If args contain "all" → **multi-session mode** for today

## Candidate Description Format

Each candidate in Q4 must have a description showing the **exact proposed content**, not just a title. The user judges candidates by reading descriptions, not by opening files.

Good: `"Add to telegram skill: get_chat_type() misclassifies private chats as channels — use Telethon client.send_message() directly for DMs"`

Bad: `"Update telegram skill with DM fix"`

## What This Skill Does NOT Do

This skill only captures session learnings. It does not review code quality, analyze PRs, create documentation, or run tests. For those, use the appropriate dedicated skills.

## Rules

- Never write learnings into this skill file itself — distribute to relevant skills or memory
- Cap candidates at 5 even if more findings exist
- User corrections always rank above tool failures
- The multi-select in Step 1a IS the approval — do not ask again per action
- If the session used no skills, only offer memory and CLAUDE.md candidates
- Keep the entire interaction to 2 moments: one question call, then silent execution

## Tools

- AskUserQuestion: Interactive questions (1-4 per call, single/multi select)
- Read: Check existing memory and skill files before proposing changes
- Edit: Update existing skill files and CLAUDE.md
- Write: Create new memory files
- Bash: Linear task creation, skill directory listing
- Glob: Find skill and memory files

## Testing

Engine logic is tested in `retro_engine.py` with 9 scenario fixtures and 30 pytest tests.
Run: `cd ~/.claude/skills/retrospective && python3 -m pytest test_retro_engine.py -v`
