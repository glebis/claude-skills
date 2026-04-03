# Meeting Processor

Intelligent meeting transcript processor that detects meeting type and applies type-specific analysis with optional interactive clarification.

## Features

- **Auto-detection**: Identifies meeting type from transcript content
- **Interactive mode**: Uses AskUserQuestion to clarify ambiguous details
- **Batch mode**: Auto-extracts only high-confidence information
- **Type-specific extraction**: Custom analysis per meeting type

## Supported Meeting Types

### 1. Leadgen Call
Sales/business development calls with potential clients.

**Extracts:**
- Commitments (both sides) with deadlines
- Client pain points & needs
- Budget/timeline discussed
- Decision makers identified
- Next follow-up scheduled
- Deal stage assessment
- Objections/blockers
- Meeting sentiment

### 2. Partnership/Collaboration
Strategic partnership and collaboration exploration calls.

**Extracts:**
- Opportunity overview & value proposition
- Commitments & actions with deadlines
- Strategic alignment points
- Technical integration needs
- Resource requirements
- Challenges/concerns
- Fit & readiness assessment
- Meeting sentiment
### 3. Coaching Session (delegates to coaching-session-summarizer)
### 4. Internal Meeting (coming soon)

## Usage

### Interactive Mode (default)
```bash
python3 ~/.claude/skills/meeting-processor/scripts/process.py \
  <transcript-file> \
  --mode interactive
```

Flow:
1. Script analyzes transcript
2. Identifies missing/ambiguous fields
3. Outputs questions in JSON format (exit code 2)
4. Claude Code uses AskUserQuestion to collect answers
5. Script reprocesses with user input
6. Final analysis appended to transcript

Example questions:
- **Leadgen**: Follow-up scheduled? Budget discussed? Decision makers? Confidence level?
- **Partnership**: Follow-up scheduled? Resource requirements? Partnership fit assessment?

### Batch Mode
```bash
python3 ~/.claude/skills/meeting-processor/scripts/process.py \
  <transcript-file> \
  --mode batch
```

Extracts only high-confidence information without user interaction.

### Force Meeting Type
```bash
python3 ~/.claude/skills/meeting-processor/scripts/process.py \
  <transcript-file> \
  --type leadgen \
  --mode interactive
```

## Output

Appends analysis section to transcript file:

```markdown
---
meeting_type: leadgen
processed_date: 2026-02-04
processing_mode: interactive
---

## Meeting Analysis

### Type
Leadgen Call

### Commitments & Actions
- [DEADLINE: 2026-02-10] Send proposal document (Gleb)
- [DEADLINE: 2026-02-07] Review technical requirements (Client)

### Follow-up
Next call: 2026-02-15 14:00 CET

### Client Context
**Pain Points:**
- Current system too slow for production needs
- Manual data entry causing errors

**Budget:** €50-75K discussed
**Timeline:** Q2 2026 deployment target
**Decision Makers:** CTO (technical approval), CFO (budget approval)

### Deal Assessment
**Stage:** Warm
**Probability:** 4/5
**Main Blocker:** Budget approval timeline

**Sentiment:** Positive - client engaged, asked detailed technical questions
```

## Requirements

- Python 3.8+
- `anthropic` package
- `ANTHROPIC_API_KEY` environment variable

## Installation

```bash
pip install anthropic pyyaml
```

## Configuration

Set meeting type detection thresholds in `scripts/detectors.py`.
