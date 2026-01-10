---
name: decision-toolkit
description: Generate structured decision-making tools — step-by-step guides, bias checkers, scenario explorers, and interactive dashboards. Use when facing significant choices requiring systematic analysis. Supports multiple cognitive styles and output formats.
---

# Decision Toolkit

## Overview

Create structured decision support materials that help humans think through significant choices systematically. This skill produces interactive tools, not just analysis — empowering the decision-maker rather than deciding for them.

## Philosophy

### Principles

1. **Guide, don't decide** — Tools illuminate the decision space; humans choose
2. **One thing at a time** — Reduce cognitive load through progressive disclosure
3. **Multiple lenses** — Same decision viewed through different frameworks reveals blind spots
4. **Biases visible** — Make cognitive biases explicit and checkable
5. **Actionable output** — End with concrete next steps, not abstract conclusions

### Accessibility First

- Support screen readers (semantic HTML, ARIA labels)
- Keyboard navigable (tab order, focus states)
- High contrast by default (WCAG AA minimum)
- Reduced motion option
- Works without JavaScript (graceful degradation)
- Mobile-friendly touch targets (44px minimum)

### Cognitive Inclusivity

Different people process decisions differently:

| Style | Accommodation |
|-------|---------------|
| **Analytical** | Numbers, matrices, weighted scores |
| **Intuitive** | Gut-check prompts, "how does this feel?" |
| **Visual** | Diagrams, progress bars, color coding |
| **Verbal** | Written summaries, question prompts |
| **Sequential** | Step-by-step wizard flow |
| **Global** | Dashboard overview option |

## When to Use

Invoke this skill when user faces:
- Collaboration/partnership decisions
- Career or job changes
- Investment of significant time/money
- Project prioritization
- Technology/tool selection
- Any choice with multiple factors and uncertainty

**Not for**: Trivial decisions, emergency responses, or when user just needs information.

## Decision Types

### Type 1: Opportunity Evaluation
*Should I pursue this opportunity?*
- Partnership, job offer, investment, project

### Type 2: Resource Allocation
*Where should I invest my time/money/attention?*
- Prioritization, budgeting, focus areas

### Type 3: Risk Assessment
*What could go wrong and is it worth it?*
- New ventures, changes, experiments

### Type 4: Trade-off Navigation
*Which option among alternatives?*
- Tool selection, hire decisions, strategic choices

## The Decision Journey

Nine steps, each focused on one dimension:

```
┌─────────────────────────────────────────────────────────────┐
│  1. CONTEXT         What is the decision?                   │
│  2. FIRST PRINCIPLES Does this solve a real problem?        │
│  3. TIMING          Is now the right moment?                │
│  4. STAKEHOLDERS    Who else is involved? Are they stable?  │
│  5. BIASES          What might cloud my judgment?           │
│  6. OPPORTUNITY COST What am I giving up?                   │
│  7. SCENARIOS       What could happen?                      │
│  8. QUESTIONS       What do I still need to learn?          │
│  9. SYNTHESIS       Summary + decision                      │
└─────────────────────────────────────────────────────────────┘
```

## Output Formats

### 1. Interactive HTML Guide (Primary)
Step-by-step wizard with:
- Progress indicator
- One question per screen
- State persistence across steps
- Final summary aggregating all inputs
- Keyboard navigation
- Print-friendly CSS

### 2. Markdown Framework
For offline/text-based use:
- Structured prompts
- Checkbox-style bias audit
- Fill-in-the-blank templates

### 3. Voice Summary
For audio consumption:
- 5-7 paragraph executive summary
- Orpheus TTS markup for emotional texture
- Key decision + rationale

### 4. PDF Report
For documentation/sharing:
- Professional formatting
- All frameworks applied
- Appendix with raw analysis

## Frameworks Reference

### First Principles Test
```
1. What problem does this solve?
2. Can I solve it myself?
3. Is this the best solution?
4. What assumptions am I making?
5. If starting fresh today, would I choose this?
```

### Bias Checklist
```
□ FOMO — Am I afraid of missing out?
□ Sunk Cost — Am I factoring past investment?
□ Authority — Am I deferring to credentials?
□ Social Proof — Am I following the crowd?
□ Commitment — Do I feel locked in by past statements?
□ Optimism — Am I assuming problems will resolve?
□ Recency — Am I overweighting recent events?
□ Confirmation — Am I seeking validating info only?
□ Shiny Object — Is novelty distracting me?
□ Loss Aversion — Am I overweighting potential losses?
```

### Opportunity Cost Calculator
```
Hours/week × Weeks × Hourly rate = Direct cost
+ What else could those hours produce?
+ What relationships/opportunities might suffer?
= True opportunity cost
```

### Scenario Matrix
```
| Scenario | Probability | Outcome | Expected Value |
|----------|-------------|---------|----------------|
| Worst    | X%          | ...     | ...            |
| Bad      | X%          | ...     | ...            |
| Neutral  | X%          | ...     | ...            |
| Good     | X%          | ...     | ...            |
| Best     | X%          | ...     | ...            |
```

### Pre-mortem
```
Imagine it's [future date]. This decision failed. Why?

Possible causes:
1. ...
2. ...
3. ...

Which causes are within my control?
Which warning signs should I watch for?
```

### 10-10-10 Framework
```
How will I feel about this decision in:
- 10 minutes?
- 10 months?
- 10 years?
```

### Regret Minimization
```
Imagine you're 80 looking back.
Would you regret doing this?
Would you regret NOT doing this?
```

## Implementation Guide

### Step 1: Gather Context

Ask user for:
- What is the decision?
- What are the options?
- What's the timeline?
- What's at stake?
- Any relevant background?

Or extract from existing documents (meeting transcripts, notes).

### Step 2: Choose Output Format

Based on user preference and context:
- Complex decision + time available → Interactive HTML
- Quick analysis → Markdown framework
- On-the-go consumption → Voice summary
- Need to share with others → PDF report

### Step 3: Generate Tool

Use templates in `templates/` directory:
- `decision-guide-template.html` — Full interactive wizard
- `decision-framework.md` — Text-based analysis
- `decision-voice-summary.md` — Audio script template

### Step 4: Customize

Replace placeholders:
- `{{DECISION_TITLE}}` — What's being decided
- `{{CONTEXT}}` — Background information
- `{{OPTIONS}}` — Available choices
- `{{STAKEHOLDERS}}` — People/teams involved
- `{{TIMELINE}}` — Relevant dates
- `{{FACTORS}}` — Key evaluation criteria

### Step 5: Apply Branding (Optional)

If using Agency brand:
- Import brand-agency skill CSS variables
- Use neobrutalism styling
- Apply Geist/EB Garamond typography

## Accessibility Implementation

### Semantic HTML
```html
<main role="main" aria-label="Decision Guide">
  <nav aria-label="Progress">
    <ol role="list">...</ol>
  </nav>
  <section aria-labelledby="step-title">
    <h1 id="step-title">...</h1>
  </section>
</main>
```

### Keyboard Navigation
```javascript
// Ensure all interactive elements are focusable
// Tab order follows visual order
// Enter/Space activate buttons
// Arrow keys navigate options
```

### Screen Reader Announcements
```html
<div role="status" aria-live="polite" id="announcer">
  <!-- Announce step changes, selections, results -->
</div>
```

### Color Contrast
```css
/* Minimum 4.5:1 for normal text, 3:1 for large text */
--text-on-light: #000000;  /* 21:1 on white */
--text-on-dark: #ffffff;   /* 21:1 on black */
--text-on-primary: #ffffff; /* Check each color */
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

## Cultural Considerations

### Individualist Framing
- "What do YOU want?"
- Personal goals and values
- Individual opportunity cost

### Collectivist Framing
- "How does this affect your team/family?"
- Relationship implications
- Group harmony considerations

### Power Distance Awareness
- Some cultures defer to authority figures
- Bias check should include "Am I deferring inappropriately?"
- Include stakeholder perspectives explicitly

### Uncertainty Tolerance
- Some prefer detailed scenario analysis
- Others find it anxiety-inducing
- Offer both detailed and simplified views

## Example Invocations

### From Meeting Transcript
```
User: Analyze this meeting transcript and create a decision toolkit
Claude: [Extracts decision, stakeholders, options from transcript]
        [Generates interactive HTML guide]
        [Creates voice summary]
```

### From Scratch
```
User: I need to decide whether to take a new job offer
Claude: [Asks clarifying questions]
        [Generates decision framework]
        [Customizes for career decision type]
```

### Quick Analysis
```
User: Help me think through this partnership decision, just give me the frameworks
Claude: [Provides markdown framework]
        [Skips interactive tool]
        [Focuses on key questions]
```

## Files

- `SKILL.md` — This file
- `templates/decision-guide-template.html` — Interactive wizard template
- `templates/decision-framework.md` — Text-based analysis template
- `templates/decision-voice-summary.md` — Audio script template
- `references/bias-encyclopedia.md` — Detailed bias descriptions
- `references/framework-deep-dives.md` — Extended framework explanations

## Integration

Works well with:
- **brand-agency** — Apply visual branding
- **transcript-analyzer** — Extract decisions from meetings
- **pdf-generation** — Create shareable reports
- **elevenlabs-tts** — Generate audio summaries

## Learnings

### 2026-01-09
**Context**: Initial skill creation from Synthius decision session

**Key Insight**: Dashboard-everything-at-once overwhelms. Step-by-step wizard with one concept per screen dramatically improves usability.

**Architecture**: 9-step journey covering all major decision dimensions. State object persists selections across steps. Summary aggregates everything.

**Accessibility Note**: High contrast neobrutalism actually helps accessibility — clear borders, distinct states, no subtle gradients.
