# Authorship Wizard

A structured interview that produces a defensible `AUTHORSHIP.md` — a record of
the **human creative contribution** behind an AI-assisted project. Its purpose
is to make human authorship *evidenced and explicit*, because copyright
protection for AI-assisted works hinges on demonstrable human authorship.

> **Not legal advice.** This wizard surfaces general, widely-reported principles
> and helps the author document facts. It is not a substitute for a qualified
> lawyer in the relevant jurisdiction. Always present this disclaimer to the user.

## How to run it

Fill the placeholders in `assets/templates/AUTHORSHIP.md` by interviewing the
user **and** gathering external evidence. Prefer evidence over assertion: a
specific decision with a commit/ADR reference is stronger than a vague claim.

Work section by section. Keep each section to a few concrete bullets — quality
and specificity beat volume.

**Interview transport.** Prefer **cenno** if installed (detect per the SKILL.md
*Asking questions* section: `ToolSearch` for `mcp__cenno__ask_sequence`). The
wizard maps naturally onto `mcp__cenno__ask_sequence` with `flow: "question"`:

- Jurisdiction and "which sections apply" → questions with `input.kind: "choice"`.
- The five substance sections → questions with `input.kind: "voice_text"` so the
  user can *speak* their reasoning (richer authorship evidence than terse typing).
- Run the substance questions as one `ask_sequence` so progress dots show; parse
  `{answers: [...]}` in order. On `{answered: false}` (timeout), fall back.

If cenno is absent, use `AskUserQuestion` for choices and conversational prompts
for free text — same questions, plainer surface.

### Step 0 — Gather external evidence first

Before asking the user to recall things, mine what the repo already records, and
offer the findings as a starting draft the user edits:

| Source | Command / location | Feeds section |
|---|---|---|
| ADRs / design docs | `docs/adr/`, `docs/`, `DESIGN.md` | Decisions |
| Commit history | `git log --pretty='%ad %s' --date=short` | Decisions, Direction |
| Changelog | `CHANGELOG.md` | Decisions, Direction |
| AI session logs | `~/.claude/projects/<cwd>/`, transcripts | Judgment, Implementation |
| Constraints files | `CLAUDE.md`, `AGENTS.md` | Judgment, Direction |
| Design tokens / brand | `docs/design/`, theme/token files | Art Direction |
| README | `README.md` | Direction |

Summarise findings, then ask the user to confirm/correct — never invent.

### Step 1 — Jurisdiction (ask first; drives the Legal section)

Ask: *"Under which jurisdiction are you primarily operating / will you assert
rights?"* Offer the common options (see [Jurisdiction notes](#jurisdiction-notes))
plus "Other / multiple". The answer selects which legal framing to write into the
Legal & Copyright section and which cautions to surface.

### Step 2 — The five substance sections

For each, ask 1–3 focused questions, then write tight bullets.

1. **Decisions** — *What significant choices did you make, and why?*
   Architecture, tech-stack selection, data models, API/interface design, build
   vs. buy, tradeoffs accepted. Anchor each to evidence where possible.

2. **Exercise of Judgment** — *Where did your judgment shape or override the work?*
   Selection among alternatives, AI output you rejected/refined, quality bars
   enforced, taste calls. This is often the strongest evidence of authorship in
   AI-assisted work — be specific about *what was changed and why*.

3. **Goal Setting & Direction** — *What problem, for whom, with what goals and
   non-goals?* Establishes that generated output served human-set objectives.

4. **Art Direction** — *What visual identity, design system, UX patterns, and
   tone did you author?* Selection and arrangement of expressive elements is
   frequently protectable even where individual components are not.

5. **AI Implementation** — *Which AI tools assisted, and how was output reviewed?*
   Name the tools, describe the human review loop, note where logs are retained.

### Step 3 — Legal & Copyright section

Write the copyright line (`(c) {{year}}-present {{author}}`), the
human-direction statement, and the jurisdiction-specific framing from below.
Optionally record AI provider output-rights terms for transparency (see
[Provider terms](#provider-output-terms)). Re-state the not-legal-advice
disclaimer in conversation (not necessarily in the file).

## Jurisdiction notes

General, widely-reported positions as of 2026. Summarise the relevant one into
the Legal section; flag uncertainty; recommend counsel for anything load-bearing.

### United States
- The US Copyright Office position: copyright protects **human-authored**
  contributions; purely AI-generated material lacking human creative control is
  **not registrable**. (Cf. *Thaler v. Perlmutter*; the *Zarya of the Dawn*
  decision; the USCO's reports on copyright and AI.)
- Human **selection, arrangement, coordination**, and substantial creative
  modification of AI output **can** be protectable.
- On registration, AI-generated portions should be **disclaimed**; claim the
  human-authored selection/arrangement and modifications.
- Practical takeaway: the Decisions/Judgment/Art-Direction sections are the
  evidentiary core. Document them concretely.

### European Union (incl. Germany)
- Originality standard: the work must be the **author's own intellectual
  creation** reflecting **free and creative choices** (*Infopaq*, *Painer*).
- AI-**assisted** works are protectable where a human makes such creative
  choices; fully autonomous AI output without human creative input is not.
- Germany (UrhG): requires a **persönliche geistige Schöpfung** (personal
  intellectual creation). Document the human choices that meet this bar.

### United Kingdom
- The CDPA s.9(3) has an unusual **computer-generated works** provision: where
  there is no human author, the author is **the person who made the arrangements
  necessary** for creation; protection runs ~50 years. (Under active policy
  review — verify current status.)
- For AI-**assisted** work with clear human authorship, ordinary originality
  rules apply.

### Other / multiple jurisdictions
- General principle everywhere: **more demonstrable human creative control =
  stronger protection.** When operating across jurisdictions, document to the
  **strictest** applicable standard (typically the US human-authorship bar).
- Recommend qualified local counsel before relying on the record commercially.

## Provider output terms

Optionally record, for transparency (do not rely on these in place of authorship
documentation):
- **OpenAI** — terms state that, as between user and OpenAI and to the extent
  permitted by law, the user owns the Output.
- **Anthropic** — commercial terms let customers retain ownership rights over
  generated outputs.

Verify the current wording at the providers' published terms before quoting.

## Output

Write the completed `AUTHORSHIP.md` to the repo root. If `NOTICE` exists (Apache
projects), ensure it points to `AUTHORSHIP.md` for the authorship record.
