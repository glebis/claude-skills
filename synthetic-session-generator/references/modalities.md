# Modality Cheat-Sheets

Use these to keep the practitioner's voice and technique faithful to the chosen framework. Each
section lists signature moves, characteristic question forms, vocabulary, pacing, and the
ground-truth labels worth emitting for evals.

---

## icf-grow — Professional Coaching (ICF + GROW)

- **Stance**: non-directive, client-as-expert, future/action focused. Coach asks more than tells.
- **GROW arc**: **G**oal (what do you want from this session/topic) → **R**eality (what's true now) →
  **O**ptions (what could you do) → **W**ill (what will you commit to).
- **Signature moves**: powerful open questions, reflecting back, holding silence, asking permission
  ("Can I offer an observation?"), accountability check on prior commitments.
- **Question forms**: "What would success look like?" · "What's getting in the way?" · "What else?"
  (asked repeatedly to widen options) · "On a scale of 1–10, how committed are you?"
- **Avoid**: diagnosing, giving advice, deep childhood/trauma exploration (that drifts to therapy).
- **Eval labels**: `grow_phase`, `powerful_question`, `commitment/action_item`, `accountability_check`.

## cbt — Cognitive Behavioral Therapy

- **Stance**: collaborative, structured, present-focused, psychoeducational. Agenda-setting at the top.
- **Core tools**: thought records (situation → automatic thought → emotion → evidence for/against →
  balanced thought), Socratic questioning, identifying cognitive distortions, behavioral experiments,
  homework review.
- **Cognitive distortions to surface/label**: catastrophizing, mind-reading, all-or-nothing,
  overgeneralization, "should" statements, emotional reasoning, discounting the positive.
- **Question forms**: "What went through your mind right then?" · "What's the evidence for that
  thought?" · "If a friend said this, what would you tell them?" · "How could we test that belief?"
- **Pacing**: check-in → agenda → homework review → main work → new homework → summary.
- **Eval labels**: `cognitive_distortion`, `automatic_thought`, `reframe`, `homework_assigned`.

## ifs — Internal Family Systems (Parts Work)

- **Stance**: gentle, curious, non-pathologizing; every part has positive intent. Therapist helps the
  client lead from **Self** (calm, curious, compassionate).
- **Core concepts**: parts (managers, firefighters, exiles), Self-energy, unblending, the 8 C's
  (calm, curiosity, compassion, clarity, courage, confidence, creativity, connectedness).
- **Signature moves**: "Let's get to know that part." · asking the client to turn toward a part ·
  the unblending question "How do you feel **toward** that part right now?" (if not open/curious,
  another part is blended) · asking permission of protectors before approaching exiles.
- **Question forms**: "Where do you notice it in your body?" · "What does that part want you to
  know?" · "How old does it feel?" · "What is it afraid would happen if it stopped?"
- **Pacing**: slow, somatic, lots of silence; one part at a time. Never rush an exile.
- **Eval labels**: `part_identified` (manager/firefighter/exile), `unblending`, `self_energy`,
  `protector_permission`.

## act-mi — Acceptance & Commitment / Motivational Interviewing

- **Stance**: values-driven, accepting of inner experience, change-talk-evoking, non-confrontational.
- **ACT tools**: cognitive defusion ("I'm having the thought that…"), acceptance/willingness, values
  clarification, committed action, present-moment contact, self-as-context.
- **MI tools**: OARS (Open questions, Affirmations, Reflections, Summaries), evoking and reinforcing
  change talk (DARN-C: Desire, Ability, Reasons, Need, Commitment), rolling with resistance, the
  readiness ruler.
- **Question forms**: "What matters to you here, underneath the worry?" · "If this thought weren't in
  the way, what would you do?" · "What makes you want to change this now?" · "Why a 6 and not a 3?"
- **Avoid**: arguing for change (evokes the client's own change talk instead), the "righting reflex".
- **Eval labels**: `change_talk` (DARN-C), `value_named`, `defusion`, `reflection`, `affirmation`.

---

## Mixing modalities

Default to a single modality per session for clean evals. Depict integrative/eclectic practice only
when the user asks — and if so, label which technique each move belongs to so eval ground truth
stays unambiguous.
