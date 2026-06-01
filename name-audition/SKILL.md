---
name: name-audition
description: Run candidate product, brand, company, or benchmark names through an audition — authoritative domain-availability checks, collision research across SaaS/GitHub/packages/the target adjacent domain, a light trademark and ownability read, a ranked callback list, and an interactive casting report of finalists with optional draft branding. Use when the user is naming a product, app, company, feature, or benchmark; asks "is this name taken", "check these domains", "help me pick a name", "is X available", "name my product", "brand name research", "audition names"; or wants to compare and pressure-test a shortlist of candidate names before committing.
---

# Name Audition — «Кастинг имён»

Audition candidate names before you cast one. Brandability is not availability, and a free
domain is not a safe name — the audition separates the three. Candidates *try out*; the best one
gets *cast*; the rest simply don't make the cut.

## The core lesson this skill encodes

A name can sound perfect, score well, have every domain free — and still be the wrong choice.
Three ways a candidate fails its screen test, worst first:

1. **Adjacent-domain collision is the worst kind.** A product already operating in the target
   vertical means a name doesn't make the cut even when the string is free to register —
   confusion and SEO dilution are fatal in the same space.
2. **Descriptive / generic names are domain-free but weak.** Easy to register, hard to own — bad
   for trademark, bad for SEO, easy for competitors to crowd.
3. **Search visibility ≠ availability.** "I didn't see it in results" is not proof a name is
   free. Verify with authoritative sources before casting.

## Workflow — the casting call

Run these stages in order. Stages 3a and 3b run together.

1. **Brief.** Establish: (a) what is being named (product / app / company / feature / benchmark),
   (b) scope + one-line description, (c) **the adjacent domain** — the vertical it lives in
   (healthcare, coaching, privacy/security, dev tooling); the user supplies this, (d) tone / vibe,
   (e) which TLDs matter (default `.com .org .ai .io .app .co`). If (a)–(c) is missing, ask first —
   the adjacent domain is what makes collision research meaningful.
2. **The audition.** Generate 4–8 candidate names matching the tone. Favor short, pronounceable,
   ownable coinages over descriptive compounds. Note for each what it means / why it fits.
3. **The screen test** (run 3a and 3b together):
   - **3a — Domains (authoritative).** Run `scripts/check_domains.sh NAME [NAME ...] -- com ai io ...`
     for a name × TLD availability table. WHOIS no-match + no NS = registrable; Creation Date /
     Registrar / NS present = taken; ambiguous = verify by hand. Authoritative for *registration*,
     never for trademark.
   - **3b — Collision research.** For each candidate, use the `firecrawl` skill or web search
     (never beautifulsoup) to check the sources below.
4. **Callbacks.** Build a per-candidate risk table and rank by safety + ownability.
5. **Casting report.** Use the `present` skill to build an interactive HTML deck — one slide per
   finalist plus a ranked comparison and a "cast it?" slide.
6. **Branding (optional, gated).** Only if the user wants it: draft a wordmark/logo per finalist
   with `nano-banana` or `gpt-image-2` (draft quality), embed in the slides.
7. **Cast → user decides.** Give a clear top pick with reasoning; the user makes the final call.
   Names that fail "didn't make the cut" — never "killed".

## Stage 3b — collision research checklist

For each candidate, search these surfaces and record URLs:

- **SaaS / AI / startups** — Crunchbase, Product Hunt, a plain web search of `"<name>"` + vertical.
- **Code namespace** — GitHub repos literally named it; PyPI and npm packages with that exact name.
- **The adjacent domain (most important)** — `"<name>"` + the user's vertical. A same-vertical hit
  is the one that ends an audition.
- **Privacy / security tooling** — relevant if the thing touches data handling.
- **Trademark + ownability** — a light USPTO / EUIPO look for live marks in the relevant classes,
  plus a judgment call on descriptiveness: distinctive enough to own, or a generic compound a
  competitor can crowd?
- **Benchmark names** — if naming a *benchmark*, the decisive check is the literature, not domains:
  is the name already a published dataset/benchmark (arXiv / ACL / Papers with Code)? Citation
  clash, not a domain, is what matters there.

Output table:

| Name | Notable existing uses (URLs) | Adjacent-domain clash? | Trademark / ownability | Verdict |
|---|---|---|---|---|
| Acme | github.com/x, acme.io (logistics) | No | Distinctive, no live marks | Callback |

`Verdict` is Callback (advances) / Cut (out) / Cast (the pick). Apply the Decision rules.

## Decision rules

- **Adjacent-domain collision → Cut.** Even if every domain is free. A competing product in the
  same vertical poisons the name.
- **Descriptive / generic compound → weak.** Domains may be free, but hard to trademark and bad for
  SEO. Flag the ownability risk even when registrable.
- **Domains-free ≠ safe.** Availability is necessary, not sufficient. A name earns the part only
  when it is *both* registrable *and* clear of adjacent-domain and trademark collisions.
- **Verify before casting.** Confirm domains with `check_domains.sh` and trademark with a registry
  lookup, not with "I didn't find anything."
- **Rank by safety first, then ownability, then aesthetics.**

## Example (a real audition)

Naming a privacy-focused de-id toolkit + benchmark for the mental-health / coaching vertical.
Audition: Praxio, Dyad, Sessio, ClientPII, CONFIDE.

| Name | Screen test | Verdict |
|---|---|---|
| **Praxio** | Sounded great, but Praxis EMR is a mental-health EHR — adjacent-domain collision in the exact vertical. | Cut |
| **Dyad** | Clean, meaningful, but `dyad.sh` is a local-AI dev tool and `dyad.ai` is a healthcare company — collisions in both tech and the vertical. | Cut |
| **Sessio** | Nice, but `sessio.base44.app` is a same-vertical product for therapists. | Cut |
| **ClientPII** | All TLDs free — but a generic descriptive compound, weak to trademark, bad SEO. | Didn't make the cut (as a brand) |
| **CONFIDE** | Domains all taken (bad product brand) — but as a *benchmark* name, citation-collision is low. | **Cast** (as the benchmark name) |

One line: **domains-free ≠ safe, and brandable ≠ available.** Most names that look good fail on
adjacent-domain collisions a domain check alone would never catch.

## scripts/check_domains.sh

```bash
scripts/check_domains.sh praxio dyad sessio          # default TLDs (.com .org .ai .io .app .co)
scripts/check_domains.sh praxio dyad -- com ai io     # custom TLDs after a --
TLDS="com org ai" scripts/check_domains.sh praxio     # or via env
```

Per domain it runs `whois` (following the IANA registry referral when needed) plus `dig +short NS`,
printing a `name × TLD` table of `free` / `taken` / `?`. `?` = verify by hand (WHOIS rate-limit or
`.ai` flakiness). Needs `whois` and `dig` on PATH (ship with macOS; `apt install whois dnsutils`).

## Referenced skills

- **`firecrawl`** — collision / literature research (stage 3b). Never beautifulsoup.
- **`present`** — interactive HTML casting report (stage 5). Pass it the comparison + per-name slides.
- **`nano-banana`** or **`gpt-image-2`** — optional draft branding (stage 6). Draft quality by default.

## Safety & limits

- **WHOIS is authoritative for registration, not trademark.** A free domain can still infringe a
  live mark. Always do the separate trademark read.
- **`.ai` WHOIS is flaky.** Treat `?` as "check the registrar's search," not "free."
- **The script proves registrability, not legal clearance** — no trademarks, social handles, or
  app-store conflicts. For a name you'll build a business on, get an attorney's clearance.
- **Branding is optional and gated** — generate logos only when the user asks; draft quality unless
  told otherwise.
- The user casts. The skill recommends; it does not commit.

## Install

Portable across Claude Code and Codex — plain-prose workflow, one bash script, no Claude-only tools.

```bash
cp -R name-audition ~/.claude/skills/   # Claude Code
cp -R name-audition ~/.agents/skills/   # Codex
```
