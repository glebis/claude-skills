# Claude Cognitive Toolkit

[Русская версия](README.ru.md)

Guided CBT and DBT practice exercises for AI assistants. A Claude Code skill that walks you through one of seven exercises in the terminal (or over Telegram) and saves the result as markdown.

It is a practice tool for between therapy sessions. It is not a therapist and does not diagnose.

---

## What's in it

| Technique | Type | Steps | Time | Status |
|---|---|---|---|---|
| Thought Record | CBT | 7 | 10–15 min | ✅ Available |
| Opposite Action | DBT | 4 | ~5 min | ✅ Available |
| TIPP | DBT | 4 | 5–10 min | ✅ Available |
| DEAR MAN (with roleplay) | DBT | 7 | 10–15 min | ✅ Available |
| Wise Mind | DBT | 6 | ~8 min | ✅ Available |
| Chain Analysis | DBT | 6 | ~15 min | ✅ Available |
| Behavioral Activation | CBT | 6 | ~8 min | ✅ Available |

Each technique has its own protocol file in [references/](references/), including a "When NOT to use" section. Anything not in this table has no protocol, and the skill will say so rather than improvise one.

The five newest techniques (TIPP onwards) are written but have not yet been tried in many real sessions. Treat them as a first version.

### One-page overviews

Every technique has a one-page map: when to use it, when not to, the steps, and where it branches. Ask for it with `/cbt overview dear-man`.

![DEAR MAN overview](assets/overviews/dear-man.svg)

The maps are built by [scripts/build_overviews.py](scripts/build_overviews.py), which reads step names and core steps from the protocol files, so a map cannot drift from its protocol. If you use a Fabric.js-based sketch canvas, the SVG loads into it for annotation.

---

## Thought Record

A 7-step cognitive restructuring exercise based on Beck's cognitive therapy and the worksheet format from Greenberger & Padesky's *Mind Over Mood*.

1. **Situation** — what happened, as a camera would record it
2. **Automatic thought** — the raw thought in the moment
3. **Emotion** — name it and rate its intensity, 0–10
4. **Evidence for** the thought
5. **Evidence against** the thought
6. **Balanced thought** — a more complete view, not positive thinking
7. **Re-rate** the emotion, 0–10

Two things happen around those steps:

- **Distortion classification is silent.** The automatic thought is classified against Burns' ten cognitive distortions and the result is written to the saved session. It is not announced during the exercise — the Socratic questions do that work.
- **Accuracy check.** If the evidence shows the thought is simply true (a real loss, a real threat, a real mistake), the exercise stops trying to restructure it and moves to problem-solving or coping instead.

## Opposite Action

A 4-step DBT emotion-regulation skill (Linehan): name the emotion, identify the action urge, check whether the urge is justified by the facts, and — only if it is not — act opposite to it. If the urge is justified, the exercise helps you act on it skillfully instead.

## TIPP

A DBT distress-tolerance skill (Linehan) for when arousal is too high to think: **T**emperature, **I**ntense exercise, **P**aced breathing, **P**aired muscle relaxation. You pick one; paced breathing is the default. It calms the body and does nothing about the problem that set it off — that can come later, with another technique. The cold-water step is offered only after a screening question, and not at all with a heart condition, beta blockers, a cold allergy or an eating disorder.

## DEAR MAN

A DBT interpersonal-effectiveness skill for one specific conversation — asking for something or saying no. You build a short script: **D**escribe, **E**xpress, **A**ssert, **R**einforce, then a delivery plan (stay **M**indful, **A**ppear confident, **N**egotiate). You can then rehearse it: the assistant plays the other person, and steps out of role after each round with one observation. It is not for conversations with someone who is unsafe for you.

## Wise Mind

A DBT mindfulness skill for a decision pulled two ways. You let emotion mind and reasonable mind each speak, pause, and ask what you know when both are taken seriously. "Nothing yet" is a valid result. The assistant does not tell you which option to pick.

## Chain Analysis

A DBT method for one specific thing you did and regret: the behaviour, what set it off, what made you vulnerable that day, the links in between, the consequences, and where the chain could break next time. The stance is curiosity, not blame. It is **not** run on self-harm or suicidal behaviour — that analysis belongs with a trained therapist.

## Behavioral Activation

A CBT approach for low mood and withdrawal (Martell, Dimidjian & Herman-Dunn): you plan one small, scheduled activity chosen by what matters to you, predict how it will feel, and compare afterwards. It first checks whether the low energy is asking for rest — illness, burnout or lack of sleep — and plans rest instead if so.

---

## Pushback

When you try to skip an uncomfortable step, the skill can hold the frame for a moment before yielding. It always yields.

| Level | Name | Behavior |
|---|---|---|
| 0 | `off` | No pushback; `skip` advances at once |
| 1 | `gentle` | One soft redirect |
| 2 | `moderate` | Two attempts from different angles (default) |
| 3 | `firm` | Three exchanges, including one about what makes the step hard |

Set it per session with `/cbt --pushback firm`, or say `softer`, `harder`, or `no pushback` mid-session. Pushback is switched off entirely during safety responses and the accuracy check.

---

## Quick Start

### Claude Code

```bash
git clone https://github.com/glebis/claude-cognitive-toolkit.git ~/.claude/skills/cognitive-toolkit
```

Then, in Claude Code:

```
/cbt                    # check-in, then a recommended technique
/cbt thought-record     # go straight to a thought record
/cbt opposite-action    # go straight to opposite action
/cbt tipp               # calm the body first
/cbt dear-man           # prepare a request or a no
/cbt wise-mind          # a decision pulled two ways
/cbt chain-analysis     # reconstruct something you regret
/cbt behavioral-activation   # plan one small activity
/cbt --lang ru          # run the session in Russian
```

### Language

Sessions run in English or Russian. The skill follows the language you write in. On the very first session it asks once which you prefer; you can ignore the question and just start. The Russian names and wording are in [references/language-ru.md](references/language-ru.md).

The Russian README, [README.ru.md](README.ru.md), says where the translation comes from:
- the technique names and descriptions are the project author's own;
- the ТРУД (TIPP) and ПОПРОСИ (DEAR MAN) expansions follow the Russian edition of Linehan's skills manual;
- the remaining wording was drafted with AI help and has not yet been reviewed by a clinician.

### Telegram (via Hermes)

See [hermes/setup-mac-mini.md](hermes/setup-mac-mini.md). Commands: `/record`, `/opposite`, `/tipp`, `/dearman`, `/wise`, `/chain`, `/activate`, `/checkin`, `/settings`.

An optional script, [scripts/nudge-check.sh](scripts/nudge-check.sh), decides when a check-in message is due. It only nudges someone who has used the toolkit before, backs off when nudges go unanswered, and supports opt-out and snooze.

---

## Output

Each session is saved to `~/Brains/brain/cognitive-toolkit/sessions/` as `YYYYMMDD-[technique]-NN.md`. To use a different folder, change the path in [references/session-engine.md](references/session-engine.md) — it is defined only there.

```markdown
---
type: cognitive-toolkit-session
technique: thought-record
date: 2026-04-26
time: "14:30"
channel: cli
pushback_level: moderate
pre_intensity: 7
post_intensity: 4
intensity_delta: -3
emotions: [anxiety]
distortions_identified: [all-or-nothing, fortune-telling]
steps_completed: 7
steps_skipped: []
outcome: completed
---

**Situation**
...

**Automatic Thought**
...

**Evidence FOR**
...

**Evidence AGAINST**
...

**Balanced Thought**
...

## Takeaway
...
```

---

## Health Data (optional)

If a health MCP is available, the skill can read your latest HRV at check-in and compare it with your own recent baseline. A below-baseline reading is mentioned once as context; nothing else changes. See [references/health-integration.md](references/health-integration.md).

The skill does not compare HRV before and after a session (wearable sampling is too sparse for that to mean anything) and does not use genetic data.

---

## Privacy

Sessions are written as local markdown files. The conversation itself goes to whichever model provider runs the skill, and to Telegram if you use the Telegram channel — so this is local storage, not local processing.

---

## Safety

This toolkit implements publicly documented self-help techniques. It is not a substitute for professional mental health care, and it does not diagnose.

If you express suicidal thoughts or imminent danger, the skill stops the exercise and points you to emergency services and a crisis line; it cannot do more than that. If you are in crisis, contact your local emergency number or a crisis line directly — [findahelpline.com](https://findahelpline.com) lists them by country.

---

## License

MIT — see [LICENSE](LICENSE)

## Citation

See [CITATION.cff](CITATION.cff).
