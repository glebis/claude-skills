# {{project_name}}

> {{hook}}

## The job

When **{{situation}}**, I want to **{{motivation}}**, so I can **{{outcome}}**.

## Who hurts, and how

**Who:** {{actor}}
**What hurts:** {{what_hurts}}
{{#cost_today}}**What it costs today:** {{cost_today}}{{/cost_today}}

## What they're doing now

{{current_workaround}}

## Switch forces

| Force | What we heard |
|---|---|
| **Push** — why leave today | {{push}} |
| **Pull** — why come to us | {{pull}} |
| **Habit** — what keeps them stuck | {{habit}} |
| **Anxiety** — what they fear about switching | {{anxiety}} |

## What it must do

{{#functional}}- {{.}}
{{/functional}}

## How it must feel

{{#emotional}}- {{.}}
{{/emotional}}

## What it ships

{{#outputs}}- {{.}}
{{/outputs}}

{{#guardrails.length}}
## What it must NOT do

{{#guardrails}}- {{.}}
{{/guardrails}}
{{/guardrails.length}}

{{#open_questions.length}}
## Open questions

{{#open_questions}}- {{.}}
{{/open_questions}}
{{/open_questions.length}}

---

**Evidence source:** {{evidence.source}}
{{#evidence.weaknesses.length}}**Weaknesses flagged by Granularity Gate:** {{evidence.weaknesses}}{{/evidence.weaknesses.length}}
