# Opposite Action

A 4-step DBT emotion regulation technique from Marsha Linehan's Dialectical Behavior Therapy (Linehan, 1993). Based on the principle that emotions are maintained by their action urges — and that acting opposite to those urges, all the way, changes the emotional experience itself.

Session duration: 3–5 minutes in Telegram exchange format.

---

## When to Recommend

- User is avoiding something and feeling the pull to stay away
- User has withdrawn or is about to withdraw from a person or situation
- User has an impulse to act that would likely make things worse (send a harsh message, cancel, isolate)
- User is experiencing a strong emotion with a clear action urge — and the situation doesn't warrant the full force of that urge

---

## Pushback Zones Reference

See `pushback-config.md` for full level behavior. Pushback zones for this technique:

| Step | Name | Zone |
|------|------|------|
| 1 | Name the Emotion | Supportive |
| 2 | Identify the Action Urge | **Core** |
| 3 | Justified Check | **Core** (key dialectical pivot) |
| 4 | Act Opposite | **Core** |

---

## Step 1: Name the Emotion

**Zone: Supportive** — gentle pushback only (max 1 exchange)

**Prompt:**
> "What emotion are you experiencing right now? Name it as specifically as you can."

**Follow-ups:**

- **Vague response** ("I feel bad", "off", "weird"): "Can you get more specific? Is it more anger, fear, sadness, shame, or guilt?"
- **Multiple emotions**: "Which one has the strongest pull right now — which one is driving?"
- **Thought instead of feeling** ("I feel like he doesn't care"): "That sounds like a thought about the situation. What's the *feeling* underneath it — the emotion in your body?"

**Affect labeling support** (same families as Thought Record — use to help user get specific):

- **Anger family**: irritated, annoyed, frustrated, resentful, furious, contemptuous
- **Sadness family**: sad, hopeless, disappointed, grief, empty, despairing
- **Anxiety/fear family**: anxious, scared, worried, dread, panic, nervous
- **Shame family**: ashamed, embarrassed, humiliated, exposed, worthless
- **Guilt family**: guilty, regretful, remorseful

---

## Step 2: Identify the Action Urge

**Zone: Core** — pushback applies fully

**Prompt:**
> "What does that emotion make you *want* to do? The urge — even if you haven't acted on it yet."

**Follow-ups:**

- **Thought instead of action** ("I want things to be different"): "That's more of a wish. What do you feel *pulled to do* — what does the emotion want you to act on?"
- **"Nothing" response**: "Sometimes the urge is to withdraw, isolate, or avoid. Does any of that fit? Or maybe to stay very still and not engage?"
- **Vague action** ("do something"): "Can you get more specific? Is it approach or pull away? Attack or shut down?"

**Emotion-urge reference table** (for bot's internal use — do not recite to user unprompted; use to probe or reflect back):

| Emotion | Common Action Urges |
|---------|---------------------|
| Anger | Attack, argue, slam doors, send harsh message, withdraw coldly |
| Fear | Avoid, escape, freeze, cancel plans, over-prepare |
| Sadness | Withdraw, isolate, stay in bed, stop activities |
| Shame | Hide, avoid eye contact, apologize excessively, people-please |
| Guilt | Over-apologize, self-punish, ruminate, confess unnecessarily |

---

## Step 3: Justified Check

**Zone: Core** — key pushback zone. This is the dialectical pivot.

**Prompt:**
> "Is this urge justified by the *facts* of the situation? Not by the feeling — by what's actually happening."

**Key principle:** The emotion is always valid. The action urge may or may not be justified by the facts.

**If justified:**
> "OK, so the urge makes sense here. Acting on it isn't opposite action — it's appropriate. What would be a *skillful* version of acting on it?"
(Exit the technique here — help them act skillfully rather than act opposite.)

**If unjustified:** Proceed to Step 4.

**If unsure:**
> "If your best friend described this exact situation to you, would you tell them to [action urge]?"

**Pushback per level when user rationalizes the urge:**

- **Level 0:** Accept their assessment without challenge.
- **Level 1–2:** "Is the *intensity* of the urge proportional to what actually happened — or is it larger than the situation warrants?"
- **Level 3:** "Notice what just happened — the emotion is building a case for the urge. That's what emotions do. They're very convincing. But is the case based on the facts, or on the feeling?"

---

## Step 4: Act Opposite

**Zone: Core**

**Prompt (when urge is unjustified):**
> "What's the opposite of [their action urge]? Not the extreme opposite — just a move in the *other* direction."

**Opposite action reference table** (offer this if user is stuck or asks for examples):

| Emotion | Urge | Opposite Action |
|---------|------|-----------------|
| Anger | Attack, send harsh message | Approach gently, wait before responding, speak softly |
| Anger | Withdraw coldly | Stay engaged, express the feeling without attacking |
| Fear | Avoid, cancel | Approach what you're avoiding — even a small step |
| Fear | Over-prepare | Act before you feel "ready enough" |
| Sadness | Withdraw, stay in bed | Get active — walk, call someone, do one thing |
| Sadness | Isolate | Reach out to one person, even a text |
| Shame | Hide, avoid | Share what happened with someone safe |
| Shame | People-please | Express your actual preference or boundary |
| Guilt | Self-punish | Practice self-compassion; repair without self-flagellation |

**Key instruction (communicate this clearly):**
> "Do the opposite action *all the way*. Half-measures don't work — they often maintain the emotion instead of changing it."

**Follow-up prompts:**
- "Can you do that right now, or within the next hour?"
- "What would be the smallest version you could take in the next 10 minutes?"
- "What would doing it *all the way* look like for you specifically?"

---

## Session Output Body

Template for session log:

```
- Emotion: [named]
- Action Urge: [described]
- Justified?: [Yes/No + brief reasoning]
- Opposite Action: [identified]
- Committed to: [yes / no / partial]
- Outcome: [if followed up]
```

Skipped steps: log with `[skipped]` in the relevant field. Skip data flows to `cognitive-toolkit/patterns/` for longitudinal review.
