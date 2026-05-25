---
name: learning-vault
description: Generate a dedicated Obsidian learning vault for any certification, course, or study goal. Creates structured notes with domains, concepts, lessons, scenarios, MoCs, dataview queries, action items, and multiple navigation paths. Inspired by the genome vault pattern. Use when the user wants to create a study vault, learning vault, certification prep vault, or structured knowledge base for a learning goal.
---

# Learning Vault Generator

Create a fully structured Obsidian vault for any learning goal — certification exams, courses, skill acquisition, or research programs.

## Trigger Phrases

- "create a learning vault for X"
- "build a study vault"
- "set up a certification vault"
- "learning vault for [topic]"
- "/learning-vault"

## Interactive Setup

Ask the user these questions (use AskUserQuestion):

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
- Dataview plugin assumed? (yes — required for queries)

## Vault Architecture

Based on the genome vault pattern at ~/Brains/genome/:

```
{vault}/
├── Dashboard.md              — central hub with dataview queries
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
├── Templates/                — note templates
│   ├── _Course.md
│   ├── _Lesson.md
│   ├── _Concept.md
│   ├── _Scenario.md
│   └── _Domain.md
└── .obsidian/
    ├── app.json
    ├── community-plugins.json
    └── plugins/
        └── dataview/
            ├── main.js          — copy from reference vault
            ├── manifest.json
            ├── styles.css
            └── data.json        — enable DataviewJS, inline queries, HTML
```

## Dataview Plugin Setup

The vault MUST include a working Dataview plugin — not just config, but the actual plugin binary. During generation:

1. **Copy the bundled plugin** from this skill's directory:
   ```bash
   SKILL_DIR="$(dirname "$0")"  # or resolve from ~/.claude/skills/learning-vault/
   mkdir -p {vault}/.obsidian/plugins/dataview
   cp ~/.claude/skills/learning-vault/dataview-plugin/* {vault}/.obsidian/plugins/dataview/
   ```
   The `dataview-plugin/` directory inside this skill contains: `main.js`, `manifest.json`, `styles.css`, `data.json` — a complete, pre-configured Dataview plugin.
2. **Register in `community-plugins.json`**: `["dataview"]`

No manual plugin installation needed — Dataview works on first vault open.

## Frontmatter Schema

### All Notes
```yaml
type: course | domain | concept | scenario | lesson | resource | moc | meta | dashboard
created_date: 'YYYY-MM-DD'
tags: []
```

### Course
```yaml
status: not-started | in-progress | completed
priority: 1-5
lessons_total: 0
lessons_done: 0
exam_weight: ""
difficulty: easy | moderate | hard
domains: []  # wikilinks
```

### Concept
```yaml
domain: "[[Domain Name]]"
status: not-started | in-progress | completed
confidence: low | medium | high
importance: critical | high | medium | low
```

### Scenario
```yaml
number: 1-N
domains: []  # wikilinks
difficulty: easy | moderate | hard
```

### Lesson
```yaml
course: "[[Course Name]]"
section: ""
status: not-started | in-progress | completed
concepts: []  # wikilinks
```

## Generation Rules

1. **Every concept note** gets a `- [ ] #review Can I explain this without notes?` task
2. **Every scenario note** gets a `- [ ] #practice Build a mini-project for this scenario` task
3. **Every lesson note** gets a `- [ ] #review Review this lesson before exam` task
4. **Wikilinks everywhere** — concepts link to domains, scenarios link to concepts, courses link to both
5. **Question Index** maps common questions to concept notes (like genome vault's "search by concern, not gene")
6. **Key Pitfalls** lists wrong answers the exam loves to test (attractive distractors)
7. **Study Plan** generates phases based on: easy stuff first → gaps second → big course → practice → review

## Dataview Queries Used

The vault uses these Dataview query patterns:

- `TABLE` from folders with filters on status, priority, confidence
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
→ Generate: vault at ~/Brains/aws-saa/ with domains (Compute, Storage, Networking, Security, etc.), concepts per domain, practice scenarios, course tracking, dataview-powered progress dashboard

## Reference Implementation

The CCAF vault at ~/Brains/ccaf/ is the canonical example:
- 88 files, 462 wikilinks
- 5 domains, 31 concepts, 8 scenarios, 7 courses, 21 lessons
- Full dataview integration
- Multiple navigation paths: by domain, by concept, by scenario, by question type
