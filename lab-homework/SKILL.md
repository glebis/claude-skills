---
name: lab-homework
description: Use when the user wants a practice assignment between Claude Code Lab meetings — a concrete task tied to a specific lab meeting, that combines their personal goals with what was actually covered in the presentation. Triggers on "give me homework", "generate a practice task", "what should I practice", "homework for meeting 3", "задание на неделю". Fetches the current curriculum from a remote manifest, reads the meeting transcript, reads the lab vault for personal context, and writes the assignment as a new markdown file.
---

# Lab Homework

Generates a personal practice assignment tied to a specific Claude Code Lab meeting.

## Language

**Default: English.** Switch to Russian if the user wrote to you in Russian. The generated assignment file is written in the same language as the user's request.

## Inputs

### 1. Remote curriculum manifest

The skill fetches a curriculum manifest from the agency-docs website. This is the **source of truth** for what's been covered in the lab — so homework stays aligned with the presentations.

**Manifest URL** — resolution order:
1. Env var `CLAUDE_LAB_CURRICULUM_URL`
2. Value in `<vault>/.config.md` under `curriculum_url:`
3. Fallback default: `https://docs.aimindset.ai/api/curriculum/claude-code-internal-03.json` (or whichever cohort; ask the user on first run)

**Schema:** see `references/curriculum-schema.md`.

**Cache:** after fetching, write to `<vault>/.cache/curriculum.json` with an `_fetched_at` key. Reuse the cache if younger than 24h unless the user says "refresh curriculum" / "update curriculum" / "pull latest".

**Fallback:** if the manifest URL returns 404 or is unset, try to fetch the cohort `homework.mdx` directly (same agency-docs site) and extract the meeting list + transcript URLs from it. If that also fails, tell the user the curriculum is unavailable and ask for the meeting number + transcript URL manually.

### 2. Meeting transcript

Each manifest entry has a `transcript_url` (typically a GitHub Gist raw URL). Fetch via `WebFetch` only for the meeting the user selected — don't prefetch all of them. Cache transcripts at `<vault>/.cache/transcripts/meeting-<NN>.md`.

### 3. Personal vault

Read from the vault (see `lab-context` skill):
- `goals.md` — what the user wants
- `tools-learned.md` — what's already familiar (recent entries matter more)
- `projects.md` — what they're working on (best landing pad for tasks)
- `profile.md` — level, primary language
- `homework/` — existing assignments (to avoid duplicates)

If the vault is missing or empty, point to `lab-context` first. Don't invent personal context.

## Workflow

1. **Fetch or refresh the curriculum manifest** (see caching rules above).
2. **Ask which meeting** via `AskUserQuestion`, populated from the manifest entries (number + title). Single-select.
3. **Ask parameters** via a second `AskUserQuestion`:
   - **"How much time do you have?"** — 30 min / 1 hour / evening / weekend
   - **"Where should this land?"** — active project / playground / either
4. **Fetch the meeting transcript** for the selected meeting (use cache if fresh).
5. **Read the vault** (profile, goals, tools-learned, projects, existing homework).
6. **Generate the assignment** using the pedagogical rubric below, grounded in the transcript so the task matches topics the user actually saw.
7. **Write the file** to `<vault>/homework/YYYY-MM-DD-meeting-<NN>-<slug>.md`.
8. **Summarise briefly** in the chat: one sentence about what the task is and the reflection question. Don't dump the whole file.

## Pedagogical rubric

A good Claude Code Lab homework task is structured like this:

- **An artifact is mandatory.** The participant must end up with a file / folder / script / commit they can show at the next meeting. No artifact, no homework. "Read the docs" ≠ a task.
- **Open-ended, not a test.** There's no single correct solution. Frame tasks as "build X that does Y" — the *how* is the participant's call. This mirrors real work with an agent far better than checklist exercises.
- **80% familiar + 20% new.** Most of the task leans on things already in `tools-learned.md`. Exactly one new element: an unfamiliar combination, a new MCP, a subagent they haven't tried, an unusual mode (plan/think). Not two, not three — that tips over into frustration.
- **Ground it in the transcript.** Pull the specific topic, demo, or tool the presenter showed in that meeting. The task should feel like "continue what we did on screen" — not a generic MCP tutorial.
- **Land it in a real project when possible.** Check `projects.md`. If an active project fits — ship the task there, artifact = commit or PR. Playground is the fallback when nothing fits.
- **Provocation, not instruction.** The phrasing should force the participant to *decide*, not *execute*. Good: "figure out how the agent could verify its own work in your project". Bad: "create a hook that runs pytest after every Edit".
- **One reflection question.** A single question at the end that can't be googled — only answered from your own experience. This *is* the success check: if the participant can answer it in depth, the insight landed.
- **Smaller than feels right.** Participants overestimate what they'll do between meetings. A 45-minute task that gets finished beats a 3-hour task that gets abandoned halfway.

## Output format

Save to `<vault>/homework/YYYY-MM-DD-meeting-<NN>-<slug>.md`:

```markdown
---
date: <YYYY-MM-DD>
meeting: <NN>
meeting_title: <title from manifest>
estimated_time: <30m | 1h | evening | weekend>
tools: [<tool1>, <tool2>]
related_goal: <quote from goals.md>
related_project: <[[projects#name]] or playground>
status: new
---

# <Task name>

## Why this matters for you
<1-2 sentences linking the task to the user's goal from goals.md>

## Context from the meeting
<1-2 sentences summarising the relevant slice of the transcript — what the presenter showed>

## What you'll build
<clear description of the target — build, fix, or investigate>

## The new thing
<the single 20% — explicitly named. Example: "You've used subagents before. This time you'll dispatch three in parallel and reconcile their output.">

## Done when
- [ ] <concrete observable result>
- [ ] <another one>

## Reflection
<one question worth asking yourself after you finish>
```

## Rules

- **One task per call.** Never a bundle of five. If the user wants more — suggest picking one.
- **Never duplicate past homework.** Check `homework/` first. If a similar task exists, either continue it (part 2) or pick a different angle.
- **Concrete over abstract.** Not "practice MCP" but "write an MCP server with one tool `get_current_weather`, wire it into Claude Code, call it three times".
- **Never create files outside the vault.** If the task needs a scratch folder, create `<vault>/homework/<slug>/` — not `$HOME`, not the root of the user's active git project.
- **If the transcript can't be fetched**, tell the user and ask them to either provide the URL or describe the meeting topic in one sentence. Don't fabricate a transcript.
- **If the manifest is stale** (older than a week), warn the user and offer to refresh before generating.
