---
name: retrospective
description: Interactive post-session retrospective that captures learnings, updates skills, and saves memories. Use when the user says "/retrospective", "let's do a retro", "what did we learn", "session review", "retro", or "wrap up". Also use at the end of long productive sessions when significant patterns or corrections emerged.
---

# Retrospective

Interactive post-session retro. Scans the conversation, asks focused questions, proposes concrete actions the user approves in one step.

## Process

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
