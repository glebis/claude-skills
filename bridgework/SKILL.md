---
name: bridgework
description: This skill should be used when someone wants to see what their tech stack could do in combination. It first audits the stack (an optional, consent-gated, read-only scan of this Mac plus a short interview), then builds and serves Bridgework, a local canvas for practising "what could these two capabilities do together?", with a prompt for an agent at every step. Triggers on "audit my stack", "what could my tools do together", "map my tech stack", "find combinations in my stack", "bridgework", "open the bridgework canvas", or "show the bridgework demo".
---

# Bridgework

Two phases: **audit** the person's stack into a stack file, then **serve** the Bridgework canvas on it. The canvas runs locally, connects to nothing and calls no model. Every step in it can produce a prompt (Sources, Ideas or Build) to paste into an agent.

Everything about the person lives in `~/.bridgework/`, never in this skill folder. The skill's own demo is synthetic.

## Ground rules

- **The scan is optional and needs permission.** Never run `audit.py` with a category the person has not agreed to in this conversation. Show the plan first.
- **Names, never values.** The audit records app, tool, MCP server and variable names. Never read, print or store a secret value, and never open config files to read anything except server names.
- **Presence is not proof.** Found means installed or configured, not working. Keep the evidence levels honest; never mark anything `e2e-verified` unless the person ran it.
- **No scores.** Do not rate imagination, novelty, value or feasibility anywhere.
- **Nothing outward.** Do not install, sign in, call an API, purchase, or publish. Serve on 127.0.0.1 only.

## Phase 1: Audit

1. **Offer the demo.** For a first look, run `scripts/serve.sh demo` (port 4174) in the background and open it. Skip if the person wants their own stack straight away.
2. **Ask before scanning.** Run `python3 scripts/audit.py --plan` and show the person what each category reads. Then ask, with a multi-select question, which categories to allow: `apps`, `clis`, `mcp`, `models`, `keys`, or none (interview only). Explain that `keys` lists variable names such as `OPENAI_API_KEY` and never their values.
3. **Scan only what was allowed.** `python3 scripts/audit.py --categories <agreed>` writes `~/.bridgework/audit.json` and prints a summary. Without `--categories` it reads nothing.
4. **Interview.** Follow `references/interview.md`: confirm the matches, pick relevant unmatched items, then ask about what a scan cannot see (phone and watch data, hosted accounts, other machines, known dead ends). Keep it short: three or four questions per round, two rounds at most.
5. **Write `~/.bridgework/stack.json`.** Catalog tools use `{"use": "<id>"}` and keep the audit's `signals`. Anything else becomes a custom part, classified with the types, domains and places in `references/stack-format.md`. Record known dead ends as `gaps` so they are drawn broken, never as working arrows.

## Phase 2: Build and serve

1. `python3 scripts/build_stack.py ~/.bridgework/stack.json` builds `~/.bridgework/site`. It validates everything first; on errors it lists each problem and writes nothing. Fix the stack file and rerun.
2. `scripts/serve.sh` serves the site on http://localhost:4175 (run it in the background). The demo uses 4174, so the two keep separate saved trails.
3. Open the page for the person and point out three things: tap two parts (or more) and connect them; write your own idea before the examples appear; press **Prompt** (or Q) anywhere to get a prompt for an agent.

To update later, rerun the audit (with permission again) and the interview for what changed, edit `stack.json`, and rebuild. The builder only replaces a folder it created.

## Files

- `scripts/audit.py`: consent-gated, read-only scan. `--plan` reads nothing. `--home` and `--root` point it at a test folder.
- `scripts/catalog.json`: about 50 known tools, each with read-only detection rules and a takes/does/gives template. Add a tool here when the same unknown keeps coming up.
- `scripts/build_stack.py`: stack file to site, with validation. Keeps built-in examples and unlocks only when all their parts exist.
- `scripts/serve.sh`: local server. `demo`, your site, or any folder and port.
- `references/interview.md`: interview questions, consent wording, and how to read the audit.
- `references/stack-format.md`: stack file format and the allowed types, domains, places and evidence levels.
- `assets/app/`: the canvas, with the synthetic demo in `data/`. `assets/app/INTERACTION.md` explains the interaction design. Tests: `npm test` there, and `PORT=4174 sh tests/run-browser.sh` with the demo served (needs Playwright and Chrome).
