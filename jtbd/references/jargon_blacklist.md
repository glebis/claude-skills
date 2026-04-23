# Jargon Blacklist

Banned phrases and their evidence-grounded replacements. When any of these appear in user input, the draft JSON, or derived markdown, the Jargon Kill Switch fires: demand evidence or replace with the concrete substitute.

This file is **opinionated** — edit it to match your voice. Add domain-specific landmines you keep hearing.

---

## Generic "good vibes"

| Banned | Why it's empty | Replacement pattern |
|---|---|---|
| seamless | means "no friction I'll name" | `cuts the step where [specific action] → [next action]` |
| delightful | means "I like it" | `removes [specific annoyance]` |
| beautiful | unscored | `uses [specific visual principle, e.g. 8px grid, monochrome]` |
| intuitive | "I know how to use it" | `familiar to people who already use [named tool]` |
| seamlessly integrated | no integration details | `connects via [named API / webhook / file]` |

## "Engagement theater"

| Banned | Why it's empty | Replacement pattern |
|---|---|---|
| drive engagement | metric laundering | `increases [specific action, e.g. weekly return visits]` |
| delight users | see above | `users [describe observable behavior]` |
| improve experience | unscored | `reduces [specific friction] by [direction or number]` |
| enhance productivity | unscored | `cuts [specific task] from [X] to [Y]` |
| empower users | marketing vapor | `lets users [specific capability they don't have today]` |

## "Enterprise noise"

| Banned | Why it's empty | Replacement pattern |
|---|---|---|
| leverage synergies | nothing | `combines [A] and [B] to produce [outcome]` |
| best-in-class | unfalsifiable | `the only tool that [specific capability]` or `matches [competitor] on [X] and beats on [Y]` |
| robust | means nothing | `handles [specific failure case, e.g. 10k concurrent users]` |
| scalable | usually a lie | `tested up to [specific volume]` |
| enterprise-ready | compliance theater | `has [named cert: SOC2, HIPAA, GDPR] + [named capability: SSO, audit log]` |

## "Innovation theater"

| Banned | Why it's empty | Replacement pattern |
|---|---|---|
| AI-powered | unscored | `uses [specific model + specific task, e.g. Whisper for transcription]` |
| next-generation | unfalsifiable | `replaces [named prior approach] because [specific limitation]` |
| revolutionary | marketing | `first to [specific capability]` |
| game-changing | marketing | `changes [specific workflow] from [X] to [Y]` |
| disruptive | cliché | leave it out entirely |

## Gleb contribution zone (add your own landmines here)

<!--
CONTRIBUTION REQUESTED: Add 5-10 phrases you personally find empty or grating. 
Look for: phrases that keep showing up in your client briefs, landing pages, 
or LinkedIn posts that make you cringe. One per row with a concrete replacement pattern.

Example rows to kickstart:
| holistic approach | laundered meaning | `combines [A], [B], [C] because [specific reason]` |
| transformation | vague | `changes [current state] to [future state]` |
| cutting-edge | unfalsifiable | `uses [named technique/method]` |
-->

| | | |
| | | |
| | | |

---

## How the Kill Switch uses this file

When drafting JSON or markdown:
1. Scan `hook`, `jtbd.*`, `problem.*`, `needs.*`, `outputs`, `switch_forces.*` for any exact-match or near-match to a banned phrase.
2. If found and a quote/behavior/workaround is nearby → attempt concrete rewrite using the replacement pattern.
3. If no evidence is nearby → ask the user: "What does [banned phrase] look like in practice?"
4. If the user can't answer → replace with a plain factual description and flag in `evidence.weaknesses[]`.

Never silently publish a banned phrase. The credibility cost is the entire reason this file exists.
