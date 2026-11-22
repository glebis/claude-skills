# Thought Record

**Flagship CBT technique.** A structured 7-column method for examining distorted automatic thoughts, weighing evidence, and generating balanced perspectives. Based on Beck's cognitive therapy (1979), refined by Greenberger & Padesky (*Mind Over Mood*, 2015).

Pushback behavior for each step is governed by `pushback-config.md`. Session state machine is defined in `session-engine.md`.

---

## When to Recommend

- **Rumination / spiraling** — same thought looping repeatedly
- **Strong emotional reaction** — distress feels disproportionate to the trigger
- **Stuck thought** — a belief the user can't shake even when they "know better"
- **Cognitive distortion patterns** — user phrases suggest all-or-nothing thinking, mind reading, catastrophizing, or self-blame
- **Post-conflict review** — after a difficult interaction where the user is still stewing
- **Pre-performance anxiety** — when worry thoughts are undermining upcoming action

Not for: acute distress or crisis (follow the Safety section of `session-engine.md` and settle first), or a thought that is simply accurate — a real loss, a real threat, a real mistake. Restructuring an accurate thought is invalidating; see the Accuracy Check after Step 5.

---

## Step 1: Situation

**Pushback zone: Supportive**

**Primary prompt:**
> "Describe the situation briefly — what happened? Just the facts, like a camera would capture it."

**Goal:** Establish objective, observable trigger. No interpretation, no story — only what a neutral observer could see or hear.

### Adaptive follow-ups for vague responses

If user gives a feeling ("I was overwhelmed") or a label ("it was a disaster") rather than a situation:

- "When did this happen — roughly what time, what day?"
- "Where were you when it hit?"
- "Who was there, or were you alone?"
- "What specifically triggered it — was there a moment, a thing someone said or did, a message you read?"

### Adaptive follow-ups if response includes interpretation

If user embeds interpretation in the situation description (e.g., "she ignored me on purpose," "he clearly didn't care"):

- "That's the story about it — which we'll get to. For now, what happened that a camera would have recorded? What did she actually do or not do?"
- "Let's separate the event from the meaning you gave it. What were the observable facts?"

### Move-to-next criterion

Situation is concrete and factual: a specific time, place, event, or observable behavior. No interpretation embedded. One sentence is fine.

---

## Step 2: Automatic Thought

**Pushback zone: Supportive**

**Primary prompt:**
> "What went through your mind in that moment? The raw thought, not what you think you should have thought."

**Goal:** Surface the hot cognition — the automatic, unedited thought that arose immediately in response to the situation.

### Follow-ups

**If user gives an emotion instead of a thought** ("I felt terrible," "I was so anxious"):
- "That's the feeling — we'll get to that next. Right now, what was the thought? What did your mind say to produce that feeling?"
- "Feelings are responses to thoughts. What was the thought that triggered the feeling?"

**If user gives a reasonable/edited thought** ("I thought I should handle it better"):
- "That sounds like the meta-thought — the one you think you should have. What was the first, raw, automatic thing that went through your mind before you caught yourself?"

**If user says "I don't know" or draws a blank:**
- "Close your eyes for a moment and replay the scene. You're back in that moment. What are you telling yourself? What's the first thing your mind says?"
- "Sometimes the thought is so automatic it feels like a fact. What did you take as true about yourself, the situation, or the future in that moment?"

**If multiple thoughts surface:**
- "Which one carries the most emotional charge? Which one stings most?"

---

### Distortion Detection (Internal — Do NOT announce to user)

Silently classify the automatic thought against Burns' 10 cognitive distortions. Do not name the distortion out loud. Log classification for session output only. The Socratic work in Steps 4 and 5 will address it implicitly.

**Burns' 10 Cognitive Distortions:**

1. **All-or-Nothing Thinking** — Seeing in black-and-white categories. "I failed completely." "Either I do it perfectly or I'm a failure."
2. **Overgeneralization** — Drawing sweeping conclusions from a single event. "This always happens." "I never get it right." "Nobody likes me."
3. **Mental Filter** — Focusing exclusively on a negative detail while ignoring the larger picture. Fixating on the one criticism in otherwise positive feedback.
4. **Disqualifying the Positive** — Dismissing positive experiences as not counting. "That went well, but it doesn't matter." "Anyone could have done that."
5. **Jumping to Conclusions** — Making negative interpretations without supporting facts.
   - *Mind Reading*: assuming others are reacting negatively without checking.
   - *Fortune Telling*: predicting a negative outcome as if it were already determined.
6. **Magnification or Minimization** — Blowing up negatives (catastrophizing) or shrinking positives. "This is the worst thing that could happen." / "It's no big deal that I did that well."
7. **Emotional Reasoning** — Treating feelings as facts. "I feel like a failure, therefore I am one." "I feel overwhelmed, so the situation must be unmanageable."
8. **Should Statements** — Using "should," "must," "ought" as rigid rules that generate guilt (self-directed) or resentment (other-directed).
9. **Labeling** — Attaching a fixed negative label to self or others based on a behavior. "I'm an idiot." "He's a jerk." More extreme than overgeneralization.
10. **Personalization** — Taking responsibility for events outside one's control. "It's my fault she's upset." "If I'd been better, this wouldn't have happened."

**Classification instruction:** Identify primary distortion(s). If ambiguous, note 2 at most. This will appear in the session output under "Automatic Thought."

### Move-to-next criterion

A specific, first-person thought is captured — not an emotion, not a behavior, not an edited version. It should be possible to rate it for belief intensity (0–100%) if needed.

---

## Step 3: Emotion

**Pushback zone: Supportive**

**Primary prompt:**
> "What emotion did that thought bring up? And how intense was it, on a 0–10 scale where 10 is the strongest you've ever felt it?"

**Goal:** Name the emotion(s) and establish a baseline intensity rating for post-session comparison.

### Follow-ups

**If user confuses thought and feeling** ("I felt like nobody cares"):
- "That's a thought — it starts with 'I felt like,' but it's actually a belief about others. The emotion is the physical/felt sense: anxious, sad, angry, ashamed. What was the feeling in your body?"

**If user gives only a number without a name** ("like a 7"):
- "What's the emotion behind the 7? What would you call it?"

**If user says "I don't know" or gives a vague answer** ("bad," "off"):
- "Sometimes naming it helps. Was there any anger or frustration? Any sadness or disappointment? Any anxiety or fear? Any shame or guilt?"

**If user reports multiple emotions:**
- Accept all of them. "That's normal — emotions often cluster. We'll track all of them."
- Ask for a separate intensity rating for each if they're distinct.

### Affect Labeling Support

If user is struggling to name the emotion, offer this emotion family menu (read aloud or share visually):

| Family | Words |
|---|---|
| **Anger** | angry, irritated, frustrated, resentful, furious |
| **Sadness** | sad, disappointed, hopeless, lonely, grief |
| **Anxiety** | anxious, worried, nervous, scared, panicked |
| **Shame** | ashamed, embarrassed, humiliated, inadequate |
| **Guilt** | guilty, remorseful, regretful |

Note: shame and guilt are often confused. Shame = "I am bad." Guilt = "I did something bad." If clinically relevant, help the user distinguish.

### Move-to-next criterion

At least one emotion is named with an intensity rating (0–10). Record the strongest as `pre_intensity` — this replaces the check-in rating, so do not ask for a second number.

---

## Step 4: Evidence FOR the Thought

**Pushback zone: Core pushback zone**

**Primary prompt:**
> "What evidence supports this thought being true? What facts back it up?"

**Goal:** Take the automatic thought seriously. Give it a fair hearing. This is not where we dismiss it — it's where we examine it honestly. Skipping or rushing this step undercuts the credibility of the counter-evidence in Step 5.

### Socratic follow-ups

**To help surface evidence:**
- "What happened that makes this thought feel true right now?"
- "If you were making the case for this thought in court, what would you present?"

**To distinguish evidence from interpretation:**
- "Is that a fact — something that happened — or is it your interpretation of what happened?"
- "Would a neutral third party agree that's evidence, or is it a reading of the situation?"
- "Would a jury accept that as hard evidence?"

**If user jumps immediately to counter-evidence:**
- Gently hold: "Let's stay here a moment. Even if the thought is partially wrong, there may be something that made it feel true. What is it?"

**If user produces only distorted evidence:**
- Don't correct here — log it. The correction happens in Step 5.

### Move-to-next criterion

At least 1–3 pieces of evidence for the thought are listed, however weak. The step doesn't require the evidence to be strong — it requires the thought to be taken seriously.

---

## Step 5: Evidence AGAINST the Thought

**Pushback zone: Core — PRIMARY PUSHBACK ZONE**

**Primary prompt:**
> "Now the harder part. What evidence goes against this thought? What doesn't fit?"

**Goal:** This is where cognitive restructuring actually happens. The user challenges their own automatic thought using facts, perspective, and prior experience. This step carries the most therapeutic value in the entire protocol.

Pushback is highest here. If the user rushes through or says nothing, hold the frame longer than any other step. Use the pushback levels from `pushback-config.md`.

### Socratic questions (use 1–2, not all — avoid interrogation feel)

- "Has this thought been 100% true every single time in your life?"
- "What would you tell a close friend who had this exact thought?"
- "If someone you trust was watching the situation, what might they see differently?"
- "Are there any times when the opposite was true — even once?"
- "What are you not seeing because the emotion is loud right now?"
- "Is there any part of you that doesn't fully believe this thought? What does that part see?"
- "What would you need to believe for this thought to be completely false?"

### When user says "I can't think of anything" — pushback by level

**Level 0 (Off):** Accept immediately, advance.

**Level 1 (Gentle):**
> "This step often holds the most value — want to give it one try? Even one small thing."

If user still can't → accept, advance, log skip.

**Level 2 (Moderate — default):**

*1st exchange:* "It can feel impossible to find counter-evidence when the emotion is strong — that's normal. Let me try a different angle: What would you tell a close friend who was thinking exactly what you're thinking right now?"

*2nd exchange:* "Or think about your history with this kind of thought. Has there been a single time when this thought turned out to be wrong? Even once?"

*3rd insistence* → yield, advance, log skip.

**Level 3 (Firm):**

*1st exchange:* Same as Level 2 first exchange.

*2nd exchange:* "I notice this feels like a dead end. That can mean two things: the feeling is too loud right now to see around it, or the thought is mostly accurate. Which does it feel like to you?"

If the user says the thought is accurate → go to the Accuracy Check below. Do not keep pushing.

*3rd exchange:* "Let's try the minimal version: Not 'this thought is totally wrong' — just, is there one small piece of the picture it might be missing?"

*After 3 failed exchanges* → yield, advance, log skip with note: "Evidence against: none generated."

### Move-to-next criterion

At least 1 piece of counter-evidence is captured, or the user has had the number of opportunities their pushback level allows and produced none (logged as skip), or the Accuracy Check below applies.

---

## Accuracy Check (between Steps 5 and 6)

**Pushback zone: none — pushback is switched off here regardless of level**

A thought record assumes the automatic thought is distorted. Sometimes it is not. Before asking for a balanced thought, check which case this is.

**The check applies when any of these is true:**

- The evidence FOR is strong and factual, and the evidence AGAINST is empty or thin after honest effort.
- The thought describes a real event rather than a prediction or a judgment ("my father died", "I was laid off", "I did say that to her").
- The thought is about real danger (threats, violence, coercion, an unsafe person or place). Treat it as accurate without further testing — see Safety in `session-engine.md`.
- The user says the thought is accurate.

**If the thought is accurate — say so and exit the technique.** Do not ask for counter-evidence again and do not ask for a balanced thought.

<!-- TODO(Gleb): replace the interim wording below with your own. This is the line that tells
     someone their painful thought is true, so tone matters more here than anywhere else in the
     toolkit. Things to decide: how plainly to say "this is true"; whether to name the emotion
     as fitting the facts; whether to offer one next move or a choice. -->

Interim wording:
> "From what you've laid out, this thought looks accurate — it isn't a distortion to correct. So the question changes from 'is this true?' to 'given that it's true, what would help?'"

Then offer one of these, and follow the user's choice:

- **Something can be done about it** → problem-solving: what is the smallest next action, and when?
- **Nothing can be done about it** (a loss, something in the past) → coping: what would make the next few hours more bearable? Who could they tell?
- **Part of it is accurate and part is not** (accurate event, inflated conclusion — "I made a mistake" vs. "I'm a failure") → split them, keep the accurate part as is, and continue to Step 6 with only the inflated part.

Record `outcome: accurate-thought-exit` (or continue normally in the split case). Go to Step 7 for the re-rating, then close. An unchanged rating after an accurate-thought exit is expected, not a failure.

---

## Step 6: Balanced Thought

**Pushback zone: Core**

**Primary prompt:**
> "Looking at both columns — the evidence for and against — what's a more balanced way to see this? Not positive thinking, just more complete."

**Goal:** Synthesize both columns into a nuanced, realistic statement that acknowledges complexity. The balanced thought should feel true — not forced optimism, not dismissal of the original concern.

### Follow-ups

**If balanced thought swings to the opposite extreme** ("actually, everything is fine"):
- "That might swing a bit too far — does it feel genuinely true, or more like what you think you should believe?"
- "The balanced thought holds both sides: it doesn't erase the concern, it adds the fuller picture. What would a version sound like that acknowledges the difficult part AND includes what the evidence against suggests?"

**If user can't generate a balanced thought:**
- "Try this template: 'It's true that [evidence for], AND it's also true that [evidence against].' What would you fill in?"
- Example: "It's true that I made an error in the presentation, AND it's also true that the feedback overall was positive and one mistake doesn't define my performance."

**If user generates a genuinely strong balanced thought:**
- "How does that land? Does it feel true?"
- "Where would you rate your belief in that, 0–100%?"

**If user is dismissive of the balanced thought:**
- "Sometimes the balanced thought feels hollow at first — more intellectual than felt. That's okay. The feeling tends to catch up."

### Move-to-next criterion

A balanced thought statement is captured that: (a) acknowledges the kernel of truth in the original thought, (b) incorporates counter-evidence, and (c) feels plausibly true to the user.

---

## Step 7: Re-rate Emotion

**Pushback zone: Closing — no pushback**

**Primary prompt:**
> "How are you feeling now? Same 0–10 scale as before."

**Goal:** Measure emotional shift. Validate whatever has happened. No judgment if intensity is unchanged.

### Delta-based responses

**Drop of 3 or more points:**
> "That's a real shift. What do you think made the difference?"

Follow up by naming which step seemed most impactful, if the user doesn't know.

**Drop of 1–2 points:**
> "A shift, even if small. The balanced thought might settle in more over the next few hours — cognitive shifts sometimes take a little time to move from head to body."

**No change (same rating as before):**
> "Sometimes the shift is more intellectual right now and the feeling catches up later. That's not unusual, especially when the thought is touching something deep. The work still counts."

**Increase in intensity:**
> "That happens sometimes — examining a thought closely can temporarily intensify the feeling. It usually settles. How are you right now — do you want to do a brief grounding exercise, or are you okay to continue?"

If the increase is significant (3+ points) and the user seems distressed: follow the acute-distress rule in the Safety section of `session-engine.md` before closing.

Record the rating as `post_intensity` — this replaces the close-phase re-rating.

---

## Session Output Body

Body template for the saved session. Frontmatter, filename and path are defined once in `session-engine.md` — do not add a second frontmatter block here.

```
**Situation**
[One sentence — objective, factual trigger]

**Automatic Thought**
[Exact wording of the hot cognition]
Distortion pattern: [Primary distortion(s) from Burns' list — logged silently, shown in output]
Belief intensity (pre): [0–100% if captured]

**Emotion (Pre)**
[Emotion name(s)] — [intensity]/10

**Evidence FOR**
- [Fact or interpreted evidence as stated by user]
- [...]

**Evidence AGAINST**
- [Counter-evidence as generated by user]
- [...]
[If skipped: "None generated."]

**Accuracy Check**
[Omit unless it applied. "Thought judged accurate — moved to problem-solving / coping" + what was chosen.]

**Balanced Thought**
[User's balanced reframe, in their words. Omit after an accurate-thought exit.]

**Outcome**
Emotion (post): [emotion name(s)] — [intensity]/10
Delta: [+/– points]
```

---

## Reference Notes

- Burns, D. D. (1980). *Feeling Good: The New Mood Therapy.* — Source of the 10 cognitive distortions list.
- Beck, A. T. (1979). *Cognitive Therapy of Depression.* — Foundational 7-column thought record.
- Greenberger, D. & Padesky, C. A. (2015). *Mind Over Mood* (2nd ed.) — Refined worksheet format used here.
- Pushback behavior → `pushback-config.md`
- Session flow → `session-engine.md`
