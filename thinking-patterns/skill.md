# Thinking Patterns Skill

Longitudinal cognitive pattern analysis across months of recorded conversations. Extracts evidence-based dimensions from Fathom transcripts, synthesizes cross-session patterns, and detects blind spots you can't see yourself.

## Usage

```
/thinking-patterns                              # full analysis, default period (3 months)
/thinking-patterns --dry-run                    # corpus stats + batch plan only
/thinking-patterns --period 2026-01 2026-02     # custom date range
```

## What it does

1. Discovers all Fathom transcripts in date range, classifies by type (coaching, meeting, lab, etc.)
2. Extracts Gleb's speech lines from each transcript
3. Analyzes 12 evidence-based cognitive dimensions per transcript (parallel sonnet agents)
4. Synthesizes cross-session patterns across 10 analysis sections (parallel sonnet agents)
5. Detects contradictions, competing commitments, and blind spots
6. Produces single analysis document with dated evidence quotes

## 12 Extraction Dimensions

| Dimension | Framework |
|-----------|-----------|
| Cognitive distortions | Burns' 10 categories |
| Problem framing | Discourse analysis |
| Conceptual metaphors | Lakoff & Johnson / MIPVU |
| Hedging & certainty | Epistemic marker taxonomy |
| Code-switching | Bilingual cognition research |
| Decision moments | GDMS + behavioral markers |
| Emotional indicators | Russell's Circumplex + ACT |
| Avoidance & deflection | ACT experiential avoidance |
| Agency language | Narrative Identity Theory |
| Competing commitments | Immunity to Change (Kegan) |
| Role/register markers | Sociolinguistic analysis |
| Energy signals | Engagement markers |

## 10 Output Sections

1. Recurring Narratives
2. Problem Framing Patterns
3. Metaphors & Unconscious Language
4. Decision Heuristics
5. Topics Avoided
6. Contradictions & Competing Commitments
7. Energy Patterns
8. Role Shifts
9. Execution Gap (stated priorities vs actual focus)
10. Cognitive Distortions & Biases

Plus: "The 5 Things You Don't See" summary.

## Output

- **Analysis**: `ai-research/YYYYMMDD-thinking-patterns-analysis.md`
- **Daily note**: Link appended under `## Research`

## Architecture

```
Stage 0: Corpus Discovery (~30s, orchestrator)
  ├── Find transcripts, classify, extract Gleb's speech
  └── Load reference docs, plan batches

Stage 1: Per-Transcript Extraction (~3 min, 10-13 parallel sonnet agents)
  ├── Each agent processes 1-4 transcripts
  └── Returns structured JSON per transcript (12 dimensions)

Stage 2: Aggregation (~30s, orchestrator)
  ├── Parse JSONs, de-duplicate, cluster
  └── Package into 5 synthesis bundles

Stage 3: Cross-Session Synthesis (~2 min, 5 parallel sonnet agents)
  ├── Narratives + Metaphors + Language
  ├── Decisions + Problem Framing + Biases
  ├── Avoidance + Energy + Execution Gap
  ├── Role Shifts + Developmental Markers
  └── Blind Spot Detection

Stage 4: Output (~1 min, orchestrator)
  └── Compile, save, link
```

## Cost

~$3.50 per full run, ~6 minutes runtime.

## Requirements

- Fathom transcripts in vault root (YYYYMMDD-*.md format)
- Reference docs: Profile Brief, My Focus, Strategic Decisions Framework
- No external dependencies -- pure Claude Code tools
