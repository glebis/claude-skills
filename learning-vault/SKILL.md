---
name: learning-vault
description: Create or maintain a portable learning vault for any certification, course, or study goal. Creates or updates domains, concepts, lessons, scenarios, maps, review tasks, and optional Dataview views using an Open Knowledge Format profile. Inspired by the genome vault pattern. Use when the user wants to create a study vault, learning vault, certification prep vault, or structured knowledge base for a learning goal.
---

# Learning Vault Generator

Create or maintain a learning vault for certifications, courses, skill acquisition, or research programs. This is the learning profile of Open Knowledge Vault. Read `../open-knowledge-vault/skills/open-knowledge-vault/SKILL.md` when available for shared setup, preservation, provenance, and audit. The learning profile below remains usable independently.

## Trigger Phrases

- "create a learning vault for X"
- "build a study vault"
- "set up a certification vault"
- "learning vault for [topic]"
- "/learning-vault"

## Interactive Setup

Infer answers from the request and existing vault. Ask only for missing information that changes the result; avoid repeating setup questions for maintenance. Use an available user-input tool rather than assuming a particular client API.

### 1. Subject & Goal
- What is the learning goal? (certification, course, skill, research)
- What is the subject? (e.g., "AWS Solutions Architect", "Rust programming", "Machine Learning")
- Is there a specific exam or assessment? If yes, get: format, passing score, domains/topics, timeline

### 2. Structure
- How many main topics/domains? (auto-detect from curriculum if URL provided)
- Are there courses to track? (get URLs, lesson counts)
- Are there scenarios/practice areas?

### 3. Self-Assessment
- For each domain/topic, ask: "How confident are you?" (expert/strong/moderate/needs-work/no-experience)
- This drives the study priority ordering

### 4. Configuration
- Vault location (default: ~/Brains/{subject-slug}/)
- Daily notes? (yes/no)
- Dataview is optional; default to ordinary Markdown navigation unless requested

## Vault Architecture

Based on the genome vault pattern at ~/Brains/genome/:

```
{vault}/
├── index.md                  — portable bundle entry point
├── Dashboard.md              — optional typed hub with Dataview queries
├── MoC - Courses.md          — course progress tracker
├── MoC - Domains.md          — domain/topic overview
├── MoC - Concepts.md         — key concepts by domain
├── MoC - Scenarios.md        — practice scenarios (if applicable)
├── Action Items.md           — dataview task aggregator
├── Question Index.md         — navigate by question type
├── Key Pitfalls.md           — common mistakes to avoid
├── Exam Cheat Sheet.md       — last-minute review card
├── Courses/                  — one note per course
│   └── {Course Name}.md
├── Domains/                  — one note per domain/topic
│   └── {Domain Name}.md
├── Concepts/                 — atomic knowledge units
│   └── {Concept Name}.md
├── Scenarios/                — practice scenarios
│   └── {Scenario Name}.md
├── Lessons/                  — individual lesson notes
│   └── Lesson - {Name}.md
├── Resources/                — links, study plans
│   ├── Official Links.md
│   └── Study Plan.md
└── .obsidian/                — optional Obsidian setup and Dataview adapter
```

## Portable core and optional Dataview

Use OKF v0.2: typed YAML-frontmatter concept notes, standard Markdown links, and plain `index.md` navigation. Root `index.md` may declare `okf_version: "0.2"`; nested indexes and `log.md` do not carry concept frontmatter. Templates and tooling instructions belong outside the bundle unless they also conform.

Prefer the shared Open Knowledge Vault setup/audit helper when present. Dataview is an optional view, not required infrastructure. Do not overwrite the plugin registry with `["dataview"]`; append while preserving existing IDs. Use an authorised installed build or official release. Do not copy personal `data.json`; new installs disable DataviewJS and inline JavaScript. Verify a rendered query before claiming activation.

The historical `dataview-plugin/` directory is retained for compatibility, not automatically installed or packaged with the new plugin. Static maps and tasks must stay usable without it.

For maintenance, inspect and patch relevant sections, preserve custom fields and completed tasks, attach source evidence, and refresh maps. Do not silently rewrite existing links or statuses. Updating an existing vault is not a request to regenerate it.

## Frontmatter Schema

### All Notes
```yaml
type: course | domain | concept | scenario | lesson | resource | moc | meta | dashboard
title: Human-readable title
status: draft | stable | deprecated
created_date: 'YYYY-MM-DD'
tags: []
```

### Course
```yaml
workflow_status: not-started | in-progress | completed
priority: 1-5
lessons_total: 0
lessons_done: 0
exam_weight: ""
difficulty: easy | moderate | hard
domains: []  # producer-defined references; keep canonical Markdown links in the body
```

### Concept
```yaml
domain: Domain Name
workflow_status: not-started | in-progress | completed
confidence: low | medium | high
importance: critical | high | medium | low
```

### Scenario
```yaml
number: 1-N
domains: []  # producer-defined references; keep canonical Markdown links in the body
difficulty: easy | moderate | hard
```

### Lesson
```yaml
course: Course Name
section: ""
workflow_status: not-started | in-progress | completed
concepts: []  # producer-defined references
```

## Generation Rules

1. For exam preparation, **concept notes** get a `- [ ] #review Can I explain this without notes?` task
2. For practice, **scenario notes** get a `- [ ] #practice Build a mini-project for this scenario` task
3. For review, **lesson notes** get a `- [ ] #review Review this lesson before exam` task
4. **Portable links** — use standard Markdown links between concepts, domains, scenarios, and courses; preserve existing wikilinks during maintenance until a safe conversion is authorised
5. **Question Index** (a typed Map or reserved index.md) maps common questions to concept notes (like genome vault's "search by concern, not gene")
6. **Key Pitfalls** lists wrong answers the exam loves to test (attractive distractors)
7. **Study Plan** generates phases based on: easy stuff first → gaps second → big course → practice → review

## Dataview Queries Used

When Dataview is requested, add query views alongside static navigation. Study progress uses `workflow_status`; OKF lifecycle uses `status`. Query patterns:

- `TABLE` from folders with filters on workflow_status, priority, confidence
- `TASK` aggregation from all notes with tag filters (#review, #practice)
- `GROUP BY` for domain-level summaries
- `SORT` by priority, weight, confidence level
- `LIST` for filtered views (not-started, in-progress, completed)

## Self-Assessment → Priority Mapping

| Self-Assessment | Confidence | Study Priority |
|---|---|---|
| no-experience | low | 1 (study first) |
| needs-work | low | 2 |
| moderate | medium | 3 |
| strong | medium-high | 4 (review only) |
| expert | high | 5 (quick check) |

Higher exam weight × lower confidence = higher study priority.

## Study Plan Generation

Phases are generated based on:
1. **Quick wins**: courses with few lessons + high confidence → build momentum
2. **Gap-filling**: domains with low confidence + high exam weight
3. **The big course**: the largest course by lesson count
4. **Practice**: scenarios, hands-on projects
5. **Final review**: cheat sheet, pitfalls, low-confidence concepts

## Example Usage

User: "Create a learning vault for the AWS Solutions Architect Associate exam"

→ Ask: domains, courses (e.g., Udemy course URL), timeline, self-assessment
→ Generate: vault at ~/Brains/aws-saa/ with domains (Compute, Storage, Networking, Security, etc.), concepts per domain, practice scenarios, course tracking, optional Dataview progress dashboard with a portable static fallback

## Reference Implementation

The CCAF vault at ~/Brains/ccaf/ is the canonical example:
- 88 files, 462 wikilinks
- 5 domains, 31 concepts, 8 scenarios, 7 courses, 21 lessons
- Full dataview integration
- Multiple navigation paths: by domain, by concept, by scenario, by question type

## Provenance and review

Keep sources, generated content, and actual verification distinct. Use OKF `sources` with stable IDs and real actor/timestamp metadata when available. Never invent exam traps, weights, progress, or human sign-off. In source-driven learning, preserve one source per session and derive smaller reusable notes. Core format details are in the Open Knowledge Vault format reference or the official v0.2 specification.
