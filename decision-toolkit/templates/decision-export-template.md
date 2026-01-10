# Decision Export Template

Template for generating markdown decision records from the interactive decision guide.

---

## Template Variables

| Variable | Description |
|----------|-------------|
| `{{DECISION_TITLE}}` | Title of the decision being analyzed |
| `{{DATE}}` | Generation date (YYYY-MM-DD) |
| `{{PROBLEM_ASSESSMENT}}` | First principles assessment result |
| `{{WEEKS}}` | Number of weeks until milestone |
| `{{HOURS_PER_WEEK}}` | Hours available per week |
| `{{TOTAL_HOURS}}` | Calculated: weeks × hours |
| `{{ECOSYSTEM_MATURITY}}` | 1-10 rating of ecosystem/team stability |
| `{{BIASES_COUNT}}` | Number of biases identified |
| `{{BIASES_LIST}}` | Comma-separated list of bias names |
| `{{HOURLY_RATE}}` | Hourly rate for cost calculation |
| `{{OPPORTUNITY_COST}}` | Calculated: total_hours × rate |
| `{{DECISION_LABEL}}` | Selected decision option label |
| `{{DECISION_DESC}}` | Selected decision option description |

---

## Markdown Template

```markdown
# Decision Record: {{DECISION_TITLE}}

*Generated: {{DATE}}*

---

## Decision

**{{DECISION_LABEL}}**

{{DECISION_DESC}}

---

## Analysis Summary

| Factor | Value |
|--------|-------|
| Solves real problem? | {{PROBLEM_ASSESSMENT}} |
| Time available | {{TOTAL_HOURS}}h ({{WEEKS}} weeks × {{HOURS_PER_WEEK}}h/week) |
| Ecosystem maturity | {{ECOSYSTEM_MATURITY}}/10 |
| Biases identified | {{BIASES_COUNT}} |
| Opportunity cost | {{OPPORTUNITY_COST}} |

---

## First Principles Assessment

{{PROBLEM_ASSESSMENT}}

This assessment determines whether pursuing this decision solves a problem that cannot be easily solved through existing capabilities or simpler alternatives.

---

## Timing

- **Weeks until key milestone**: {{WEEKS}}
- **Hours available per week**: {{HOURS_PER_WEEK}}
- **Total available hours**: {{TOTAL_HOURS}}

---

## Biases Acknowledged

{{#if BIASES_LIST}}
The following cognitive biases were identified as potentially influencing this decision:

{{BIASES_LIST}}

Being aware of these biases helps ensure the decision is based on evidence rather than cognitive shortcuts.
{{else}}
No significant biases were identified during this analysis.
{{/if}}

---

## Opportunity Cost

At a rate of {{HOURLY_RATE}}/hour, the time investment of {{TOTAL_HOURS}} hours represents an opportunity cost of approximately **{{OPPORTUNITY_COST}}**.

This represents the value of what else could be done with that time.

---

## Next Steps

{{#switch DECISION_TYPE}}
{{#case "proceed"}}
1. Define clear success criteria
2. Set first milestone for {{WEEKS}} weeks
3. Allocate {{HOURS_PER_WEEK}}h/week in calendar
4. Identify early warning signs of failure
5. Schedule review checkpoint
{{/case}}
{{#case "defer"}}
1. Set calendar reminder for re-evaluation
2. Document current context for future reference
3. Identify what would change the assessment
4. Focus resources on current priorities
{{/case}}
{{#case "decline"}}
1. Document reasoning for future reference
2. Communicate decision if relevant
3. Redirect attention to alternatives
4. Consider what would make you reconsider
{{/case}}
{{#default}}
1. Review this analysis with fresh perspective
2. Identify any missing information
3. Consider discussing with trusted advisor
4. Set deadline for final decision
{{/default}}
{{/switch}}

---

## Review Date

Schedule review: _____________________

---

*Generated using Decision Toolkit*
```

---

## JavaScript Implementation

```javascript
function exportMarkdown(state, decisionTitle) {
    const date = new Date().toISOString().split('T')[0];
    const totalHours = state.weeks * state.hours;
    const cost = totalHours * state.rate;

    // Determine decision type for next steps
    let decisionType = 'unknown';
    if (state.decision === 'proceed') decisionType = 'proceed';
    else if (state.decision === 'defer') decisionType = 'defer';
    else if (state.decision === 'decline') decisionType = 'decline';

    // Format biases list
    const biasesList = state.biases && state.biases.length > 0
        ? state.biases.map(b => `- ${b}`).join('\n')
        : null;

    // Generate next steps based on decision type
    let nextSteps;
    switch (decisionType) {
        case 'proceed':
            nextSteps = `1. Define clear success criteria
2. Set first milestone for ${state.weeks} weeks
3. Allocate ${state.hours}h/week in calendar
4. Identify early warning signs of failure
5. Schedule review checkpoint`;
            break;
        case 'defer':
            nextSteps = `1. Set calendar reminder for re-evaluation
2. Document current context for future reference
3. Identify what would change the assessment
4. Focus resources on current priorities`;
            break;
        case 'decline':
            nextSteps = `1. Document reasoning for future reference
2. Communicate decision if relevant
3. Redirect attention to alternatives
4. Consider what would make you reconsider`;
            break;
        default:
            nextSteps = `1. Review this analysis with fresh perspective
2. Identify any missing information
3. Consider discussing with trusted advisor
4. Set deadline for final decision`;
    }

    const md = `# Decision Record: ${decisionTitle}

*Generated: ${date}*

---

## Decision

**${state.decisionLabel || 'Not selected'}**

${state.decisionDesc || ''}

---

## Analysis Summary

| Factor | Value |
|--------|-------|
| Solves real problem? | ${state.problemLabel || '—'} |
| Time available | ${totalHours}h (${state.weeks} weeks × ${state.hours}h/week) |
| Ecosystem maturity | ${state.team}/10 |
| Biases identified | ${state.biases?.length || 0} |
| Opportunity cost | ${cost.toLocaleString()} |

---

## First Principles Assessment

${state.problemLabel || 'Not assessed'}

This assessment determines whether pursuing this decision solves a problem that cannot be easily solved through existing capabilities or simpler alternatives.

---

## Timing

- **Weeks until key milestone**: ${state.weeks}
- **Hours available per week**: ${state.hours}
- **Total available hours**: ${totalHours}

---

## Biases Acknowledged

${biasesList ? `The following cognitive biases were identified as potentially influencing this decision:

${biasesList}

Being aware of these biases helps ensure the decision is based on evidence rather than cognitive shortcuts.` : 'No significant biases were identified during this analysis.'}

---

## Opportunity Cost

At a rate of ${state.rate}/hour, the time investment of ${totalHours} hours represents an opportunity cost of approximately **${cost.toLocaleString()}**.

This represents the value of what else could be done with that time.

---

## Next Steps

${nextSteps}

---

## Review Date

Schedule review: _____________________

---

*Generated using Decision Toolkit*
`;

    return md;
}

// Download function
function downloadMarkdown(content, filename) {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
```

---

## Usage Notes

1. **State object requirements**: The export function expects a state object with these properties:
   - `problem`: internal value
   - `problemLabel`: display text for first principles result
   - `weeks`: number
   - `hours`: number (per week)
   - `team`: 1-10 number
   - `biases`: array of strings
   - `rate`: number (hourly rate)
   - `decision`: internal value
   - `decisionLabel`: display text
   - `decisionDesc`: description text

2. **Filename convention**: `decision-YYYY-MM-DD-slug.md`
   - Date in ISO format
   - Slug derived from decision title (lowercase, hyphens)

3. **Integration**: Add export button to final step of decision guide:
   ```html
   <button class="export-btn" onclick="downloadMarkdown(exportMarkdown(state, title), filename)">
       Export Decision Record
   </button>
   ```
