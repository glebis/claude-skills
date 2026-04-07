---
name: recording
description: Demo/recording mode that redacts personally identifiable and sensitive information from Claude Code's outputs. Use when the user invokes /recording or says they are about to record, screen-share, or demo their Claude Code session and want PII scrubbed in real time.
---

# Recording Mode

Activate this mode when the user runs `/recording` or otherwise signals a demo/screen-share. Stay in this mode for the rest of the session unless the user says "stop recording", "/recording off", or equivalent.

## Core rule

While recording mode is active, every user-visible output (chat text, code, file contents shown inline, tool result summaries, commit messages, file names invented for examples) MUST have sensitive content replaced with **obviously fake** placeholder data before it leaves the assistant.

This applies to text the model generates. It does NOT retroactively edit files on disk — only what the audience sees on screen. If asked to write redacted content to a file, do so explicitly; otherwise leave files alone.

## What to redact

Replace these categories:

- **Names** (people, partners, family, colleagues, clients) → `Alex Doe`, `Jamie Roe`, `Sam Park`
- **Handles / emails / phones / URLs with identifiers** → `@demo_user`, `user@example.com`, `+49 000 000 0000`
- **Org / company / brand names** (when private) → `Acme Co`, `Globex`
- **Locations** — anything more specific than continent. City, neighborhood, street, venue, coordinates, IP-derived location → `Some City`, `Main Street`, `Venue A`. Even "Berlin" gets replaced if it could identify the user.
- **Dates** — any real calendar date (birthdays, appointments, sessions, deadlines, deploy dates, transaction dates, file timestamps shown inline) → shift to placeholder dates like `2025-01-01`, `2025-01-02`. Keep relative ordering and weekday if it matters to the demo. Today's actual date should be replaced too if it appears in output.
- **Financial values** (revenue, prices, salaries, invoice amounts) → round dummy numbers like `€1,234` or `$X,XXX`
- **Medical info** (diagnoses, medications, doses, symptoms, lab values) → `[medication]`, `[condition]`, `[symptom]`
- **Emotional / therapy / coaching content** (feelings, session notes, DIMs/SIMs, relationship details) → `[personal reflection]`
- **Business info** (deal terms, client lists, internal strategy, unreleased projects) → `[business detail]`
- **Credentials** (tokens, keys, passwords, session IDs, file paths containing usernames) → `sk-XXXX`, `/Users/demo/...`
- **Genetic / health data** specific to the user → `[genetic marker]`

When in doubt, redact. The cost of over-redaction in a demo is near zero; the cost of leaking is high.

## Style of replacement

- Use **obviously dummy** values, not plausible fakes that could be mistaken for real ones. `Alex Doe` not `Andrey Volkov`. `Acme Co` not `Northwind Studio`.
- Keep replacements **consistent within a session**: the same real name maps to the same fake name every time, so the demo stays coherent. Maintain this mapping mentally for the duration of recording mode.
- Preserve **structure and length roughly** so the demo still reads naturally (e.g. a real email becomes a fake email, not `[REDACTED]`).
- Preserve **technical accuracy** of non-sensitive parts: code logic, library names, public APIs, framework terminology stay exact.

## What NOT to redact

- Public technical content: language keywords, public package names, public docs URLs, generic file names (`README.md`, `package.json`).
- The user's own typed input — do not rewrite what they said, only what the assistant outputs.
- Vault structure conventions and folder names that are already public knowledge from CLAUDE.md.

## Tool calls

Tool calls themselves run normally — redaction is about what the assistant *says*. But:

- When **summarizing** tool results back to the user, apply redaction to the summary.
- When **quoting** file contents inline (e.g. showing a snippet of a daily note), redact the snippet.
- Avoid reading sensitive files into the visible transcript unnecessarily — prefer to act on them silently and report a redacted summary.

## Toggle behavior

`/recording` is a **toggle**. Calling it flips the current state:

- If recording mode is OFF, `/recording` turns it ON. Reply with one short redacted line confirming it's on.
- If recording mode is ON, `/recording` turns it OFF. Reply with one short line confirming it's off, then resume normal output.

Track the current state across the session. Natural-language equivalents also toggle: "I'm about to record" / "starting a demo" turn it on; "stop recording" / "demo done" / "you can stop redacting" turn it off. When in doubt about intent, infer from current state — if already recording and the user says "recording", they mean stop.

## Self-check before sending

Before emitting any message while recording mode is active, scan the draft for:
1. Any proper noun that isn't a public technical term.
2. Any number that looks like money, age, dose, or measurement tied to the user.
3. Any path containing `glebkalinin`, `Brains/brain`, real folder names from People/, Daily/, etc.
4. Any emotional or medical vocabulary tied to a first-person subject.

If any hit, redact and re-check. Only then send.
