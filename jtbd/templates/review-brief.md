# Review Brief — {{project_name}}

**Reviews parsed:** {{review_count}}
**Source:** {{review_source}}
**Date:** {{date}}

## Top 3 clusters (ranked by volume)

{{#clusters}}
### {{rank}}. {{label}} — {{count}} reviews ({{pct}}%)

**Representative quotes:**
{{#quotes}}- "{{.}}"
{{/quotes}}

**Hypothesized job:**
When {{situation_hypothesis}}, I want to {{outcome_hypothesis}}, so I can {{payoff_hypothesis}}.

**Confidence:** {{confidence}}

{{/clusters}}

## Underserved forces (interview priorities)

Reviews are systematically weak on these two Switch forces. Probe them in the interview.

- **Habit:** reviewers rarely describe the muscle memory / workflow inertia that keeps them with the old. Ask: "What have you been using, even if it's duct tape and a spreadsheet?"
- **Anxiety:** only unhappy switchers leave reviews — happy stayers are invisible. Ask at least one real user what worries them about switching.

## Conflicts / tensions

{{#conflicts}}- {{.}}
{{/conflicts}}

## Interview prep

Given these clusters, skip these questions in the interview (reviews already answered them):

- [ ] {{skipped_question_1}}
- [ ] {{skipped_question_2}}

Emphasize these instead:

- [ ] Walk through one specific switching moment
- [ ] Probe all four Switch forces (especially habit + anxiety)
- [ ] Push for measurable outcomes

---

**Next step:** run `/jtbd` in Interview mode, using this brief as pre-seed.
