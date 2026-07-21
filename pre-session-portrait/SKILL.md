---
name: pre-session-portrait
description: Build a compressed, visualizable "portrait" of a consulting/coaching client before a session, so the paid hour is spent solving, not scoping. Runs a 7-lens JTBD-inspired interview (where / how / what / problem / ideal / tension / jobs-to-be-done) that takes rich open answers in and compresses them to an 11-field YAML portrait out. Delivers three ways: raw paste-into-a-clean-chat prompt, a secret GitHub gist link, or a Codex CLI one-liner. Use when preparing for an upcoming client call, when the user says "prep an intake", "portrait interview", "questions before our session", "send a client a pre-session questionnaire", or wants a reusable client-intake instrument.
---

# Pre-Session Portrait

Turn "help me with X" into a decision-grade brief **before** the session starts. The instrument asks the client open, voice-note-friendly questions across seven fixed lenses; the consultant (or an LLM) compresses each answer to one line, yielding a portrait that is iterable, compressible, and easy to visualize.

Design principle: **rich in, compressed out.** The client talks freely; compression happens after, not in their head.

## The seven lenses

| # | Lens | Elicits | Compresses to |
|---|------|---------|---------------|
| 0 | ANCHOR | the topic — what the call is for (referent for every later "this") | the topic in one line |
| 1 | WHERE | what's been tried, where it stalls | current state in one line |
| 2 | HOW | cognitive style — fast/slow, visual/verbal, systems/stories | how they think |
| 3 | WHAT | live preoccupations, open loops | current focus |
| 4 | PROBLEM | the problem under the problem | the core job |
| 5 | IDEAL | concrete "solved" state (day/feeling, not tool) | desired outcome |
| 6 | TENSION | what holds them back / worries them | dominant anxiety |
| 7 | JTBD | Push · Pull · Habit · Anxiety · Trigger | switching forces |

## Output schema

```yaml
portrait:
  where: ""
  how: ""
  what: ""
  problem: ""
  ideal: ""
  tension: ""
  jtbd:
    push: ""
    pull: ""
    habit: ""
    anxiety: ""
    trigger: ""
```

## How it visualizes
- **7-spoke radial / hexad map** — one label per lens, the capture line as the value.
- **JTBD 2×2** — Push+Pull (energy toward change) vs Habit+Anxiety (energy against). The gap = leverage.
- **Iterable** — re-run any lens next session; watch the capture line drift over time.

## Workflow

1. **Gather context.** Client name, consultant name, session date, and (if known) the topic. Pull prior history from vault/email/Fathom if available so the consultant-only prep notes are grounded.
2. **Fill the template.** Copy `assets/interview-prompt.md` and substitute `{{CONSULTANT}}` (and topic if narrowing lens 4). Leave the seven lenses intact.
3. **Pick a delivery** (ask the user):
   - **Raw text** — paste the substituted prompt into a message; client runs it in any clean Claude/ChatGPT.
   - **Secret gist** — `gh gist create --desc "Pre-session portrait interview (for <name>)" interview-prompt.md`. Share the gist link. Use the unpinned raw URL (`/raw/<filename>`) so edits propagate.
   - **Codex one-liner** — see `assets/codex-bootstrap.txt`; fetches the raw gist URL and runs the interview interactively.
4. **Optional preview.** Before sending, generate a synthetic filled-in version (answers simulated from known context) so the consultant judges the deliverable's shape. Mark it clearly as synthetic.
5. **After the session.** Fold the returned `portrait:` YAML into the client's People/Session note; diff against any prior portrait to show movement.

## Delivery notes
- Secret gist ≠ auth-private: anyone with the link can read it. Fine for a benign intake; don't put client PII in the gist itself.
- Codex: run interactive `codex` (not `codex exec`), and include the "do not write code / touch files — this is a conversation" guard so it stays in interview mode.
- Framing line to prepend when sending: *"Paste this into a fresh Claude or ChatGPT chat — it'll ask you 7 quick questions and give you a block to send back to me before our call."*

## Call cockpit (interactive HTML)

Once a portrait is back, generate an interactive **prep cockpit** the consultant runs live during the session. Start from `assets/cockpit-template.html` — a self-contained, theme-aware single file (no external deps).

Tabs: **Setup** (structured stack/facts fields + a paste box for the `portrait:` block) · **Framework** (six-station pipeline with per-station AUTO/ASSIST/HUMAN + quality-gate inputs) · **Questions** (per-section bank, each with an autosaved answer field; add-your-own) · **Decisions & Actions** (dynamic add/delete rows; actions carry an owner) + a build/demo box and show-don't-tell cues · **Agenda** (accordion of time-blocks that expand into checkable sub-steps + per-block notes; a **live timer auto-opens the current block** and fills a progress bar) · **Notes**.

Key properties:
- **Autosaved** to `localStorage`, **namespaced by the Client-name field** — so multiple cockpit files opened from the same folder (same `file://` origin) never clobber each other's data.
- **Filled instances:** copy the template and inject a `const SEED = {fields, decisions, actions}` object just before `// init`; a one-time guard (`prep::<ns>::__seeded`) writes the seed into the client's namespace on first load, then the consultant's edits persist. Use this to pre-populate a cockpit from a known portrait + prior-session facts.

Also generate a **client-facing recap** after the session (same visual language): what we covered, current→target pipeline, decisions, what we built live, their next steps (autosaved checkboxes + fields), tech notes. Deliver as a file or publish as an Artifact URL to share a link.

## Assets
- `assets/interview-prompt.md` — the self-contained interviewer prompt (template).
- `assets/intake-form.md` — human-readable version with per-lens `capture:` fields, if the consultant prefers to interview live.
- `assets/codex-bootstrap.txt` — the Codex CLI one-liner template.
- `assets/cockpit-template.html` — the interactive prep cockpit (blank, reusable; autosaved + client-namespaced).
