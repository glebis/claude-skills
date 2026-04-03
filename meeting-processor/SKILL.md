---
name: meeting-processor
description: This skill should be used when processing meeting transcripts to auto-detect meeting type (leadgen, partnership, coaching, internal) and extract type-specific structured analysis. Triggers on "process meeting", "analyze meeting", "meeting summary", or after syncing new Fathom/Granola transcripts.
---

# Meeting Processor

Intelligent meeting transcript processor that auto-detects meeting type and applies type-specific extraction with optional interactive clarification.

## When to Use

- After syncing Fathom or Granola transcripts (`/fathom --today`, `/granola export`)
- When asked to process, analyze, or summarize a meeting transcript
- When a new meeting transcript appears in the vault root matching `YYYYMMDD-*.md`
- For coaching sessions, delegate to `coaching-session-summarizer` skill instead

## Prerequisites

```bash
pip install openai pyyaml
```

Requires `CEREBRAS_API_KEY` environment variable (uses Cerebras API with llama-3.3-70b).

## Supported Meeting Types

| Type | Description | Key Extractions |
|------|-------------|-----------------|
| **leadgen** | Sales/business development calls | Commitments, pain points, budget, timeline, decision makers, deal stage, sentiment |
| **partnership** | Collaboration/partnership exploration | Opportunity overview, value proposition, strategic alignment, technical needs, fit assessment |
| **coaching** | Coaching/mentoring sessions | Insights, decisions, action items, themes, emotional arc, techniques, session quality |
| **internal** | Internal team meetings | Coming soon |

## Usage

### Interactive Mode (default)

Run the processor, which auto-detects meeting type and asks clarifying questions:

```bash
python3 ~/.claude/skills/meeting-processor/scripts/process.py <transcript-file> --mode interactive
```

**Interactive flow:**
1. Script analyzes transcript and detects meeting type
2. Extracts structured data via LLM
3. Identifies missing/ambiguous fields
4. Returns questions as JSON (exit code 2 signals interaction needed)
5. Parse the JSON between `__INTERACTIVE_QUESTIONS__` markers
6. Use AskUserQuestion to collect answers for each question
7. Save answers to a temp JSON file and re-run with `process_with_answers.py`

**Handling interactive questions:**

When the script exits with code 2, parse the output for questions JSON. Each question has:
- `question`: The question text
- `header`: Short label (used as answer key)
- `options`: Array of `{label, description}` for AskUserQuestion

After collecting answers, create two temp files:
- `questions.json` — the original questions context (includes `partial_data`, `meeting_type`, `transcript_file`)
- `answers.json` — map of `{header_lowercase: selected_label}`

Then run:
```bash
python3 ~/.claude/skills/meeting-processor/scripts/process_with_answers.py questions.json answers.json
```

### Batch Mode

Extract only high-confidence information without user interaction:

```bash
python3 ~/.claude/skills/meeting-processor/scripts/process.py <transcript-file> --mode batch
```

### Force Meeting Type

Skip auto-detection:

```bash
python3 ~/.claude/skills/meeting-processor/scripts/process.py <transcript-file> --type leadgen
python3 ~/.claude/skills/meeting-processor/scripts/process.py <transcript-file> --type partnership
```

## Output

Analysis is appended to the transcript file as a `## Meeting Analysis` section. Frontmatter is updated with `meeting_type`, `processed_date`, and `processing_mode`.

### Leadgen Output Structure

- **Commitments & Actions** — with deadlines and owners
- **Follow-up** — next meeting date if scheduled
- **Client Context** — pain points, budget, timeline, decision makers
- **Deal Assessment** — stage (cold/warm/hot), probability (1-5), blocker, sentiment

### Partnership Output Structure

- **Opportunity** — description and value proposition for both sides
- **Commitments & Actions** — with deadlines and owners
- **Follow-up** — next meeting date if scheduled
- **Partnership Context** — strategic alignment, technical needs, resources, challenges
- **Opportunity Assessment** — fit (strong/medium/weak), readiness, success factors, sentiment
