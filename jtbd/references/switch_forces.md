# Switch Forces — Question Bank

The four forces that govern whether someone switches to a new solution (Bob Moesta / Chris Spiek via *Switch*). Capture all four. If the user genuinely doesn't know, mark `"unknown"` and add a follow-up to `open_questions[]`. Do not fabricate.

## Switch Timeline — 6 moments

Every switch follows this temporal arc. In Pass 2, reconstruct the timeline before diving into individual forces. Ask: "Walk me through the decision — when did it start?"

| Moment | What happened | Key question |
|--------|--------------|--------------|
| **1. First thought** | Something triggered "this isn't working" | "When did you first think something needed to change?" |
| **2. Passive looking** | Noticing alternatives without actively searching | "Did you start noticing options — articles, mentions, ads — before you actively searched?" |
| **3. Active looking** | Deliberately comparing options | "When did you start actually comparing? What did you look at?" |
| **4. Deciding** | Committing to the new solution | "What tipped it? Was there a single moment or a gradual lean?" |
| **5. Consuming** | First use / onboarding experience | "What was your first experience like? What surprised you?" |
| **6. Ongoing use** | Satisfaction vs. regret | "Now that you've been using it — what's better, what's worse than expected?" |

The timeline reveals where prospects stall. If most people get stuck between passive and active looking, that's a positioning problem. If they stall between deciding and consuming, that's an onboarding problem.

## Decision-force enrichment (beyond the four forces)

The four forces (Push/Pull/Habit/Anxiety) are the primary framework. When interviews surface richer decision psychology, tag with these additional dimensions from cognitive product analytics:

- **Perceived value** — what the user believes they'll get (may differ from actual value). Maps to Pull but can be more specific.
- **Uncertainty** — ambiguity about whether the new thing will work. Deeper than Anxiety — includes "I literally don't know what this does."
- **Trust** — belief that the product/team/company will deliver. Missing trust = hard no, regardless of other forces.
- **Effort** — switching cost in time, learning, migration. Overlaps Habit but is more concrete.
- **Social context** — who else needs to agree, who's watching, whose opinion matters.
- **Cognitive biases** — anchoring to current price, loss aversion, status quo bias. Name the bias when you spot it.

These are optional enrichments, not replacements. Always capture the four forces first. Add these when the interview naturally surfaces them — they go into the `switch_forces` block as additional fields.

## Push — frustration with current situation

What's making "today" unbearable enough to even consider a change.

- "What happened the last time this pain actually bit you? Walk me through that moment."
- "When did you first think 'this isn't working anymore'?"
- "What's the cost of staying with what you have today — time, money, stress, reputation?"
- "Who complained? Who noticed?"
- "What made this week different from the week you first had the problem but did nothing?"

Red flags: "It's just annoying" / "Would be nice to have better." No switching event behind this.

## Pull — attraction to the new solution

What the new thing promises, concretely.

- "If you imagine this working in a month, what changes first?"
- "What's the outcome you can't stop picturing?"
- "What would this let you finally do / stop doing?"
- "When you compare it to alternatives, what does yours do that they don't?"

Red flags: feature lists ("it's faster, cheaper, better"). Push for the outcome.

## Habit — inertia keeping them with the old

What they already know how to do, what's in muscle memory, what they've invested in.

- "What are you currently using — even if it's duct tape and a spreadsheet?"
- "How long have you been working around this?"
- "What would break if you stopped using the current thing tomorrow?"
- "Who else on your team depends on the current setup?"
- "What workflow or ritual has this become part of?"

Red flags: "Nothing, really" — probably wrong. Workarounds always exist, even if ugly.

## Anxiety — fear of switching

What could go wrong. Why they haven't already switched.

- "What worries you about trying the new thing?"
- "What have you heard go wrong with tools like this?"
- "What would a failed switch cost you — time, reputation, data, relationships?"
- "Who do you need to convince before this becomes real?"
- "What happens if you commit and it doesn't work?"

Red flags: "Nothing, I'm ready." Under-examined anxiety kills rollouts later. Push at least one concrete fear.

## Using the output

- `push` and `pull` are your **messaging copy** — they go straight into the headline and body of `messaging-angles.md`.
- `habit` and `anxiety` are your **design targets** — they tell you what onboarding friction to remove and what switching cost to absorb.
- Strong Push + weak Pull = user ready to leave but nothing's pulling — your positioning problem.
- Weak Push + strong Pull = shiny-object appeal, no urgency — your conversion will stall.
- Strong Habit = needs a migration path, not just a signup.
- Strong Anxiety = needs social proof, guarantees, or a reversible trial.

## One-minute pass (transcript mode)

When mining from a transcript, search for these phrases:

- Push: "tired of," "frustrated," "can't believe," "every time," "wasted"
- Pull: "I wish," "imagine if," "what if I could," "finally"
- Habit: "we currently," "right now I," "I've been using," "for years"
- Anxiety: "worried," "afraid," "what if," "last time we tried," "the team won't"
