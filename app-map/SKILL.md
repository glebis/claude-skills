---
name: app-map
description: This skill should be used when mapping an application's screens, workflows and tests into one interactive page. It inventories every screen and touchpoint from the code, writes test scenarios and jobs to be done, reads the project's real tests, and builds a self-contained HTML map with a ranked "Test next" list, a flow graph, a state-by-state testing matrix, a jobs view and agent hand-off prompts. Trigger on "map this app", "app map", "screen inventory", "what should we test next", "map the workflows", "which jobs are underrepresented", or refreshing an existing map after tests change.
---

# App Map

Build one page that answers five questions about an application:

- What should be tested next?
- How can a gap be handed to an agent?
- What does a change touch?
- Which jobs are thin or missing?
- How does the system fit together?

The agent does the judgement work and writes `map.json`. `scripts/app_map.py` does the rest: it reads the real tests, checks the map against them and writes one HTML file. Do not edit the generated page. Change `map.json`, or `assets/` when the page itself should change for every project.

## Refresh an existing map

When a `map.json` already exists, run the script and report what moved. Update `map.json` only for screens, scenarios or coverage that changed.

```bash
python3 <skill>/scripts/app_map.py <folder>/map.json --repo <repo>
```

## Build a new map

**Check the checkout first.** Note the branch and any uncommitted work. Put the map in `design/app-map/` when the project has a `design/` folder, otherwise `docs/app-map/`. Follow the project's own layout rules if it has them.

**Inventory from the code.** Read `references/discovery.md` and work through it. List what exists in the source, not what the specs promise. For a large app, delegate the sweep of each surface if the user allows subagents, then merge the results here.

**Write `map.json`.** Read `references/schema.md` for every field. `assets/example-map.json` is a small complete example. Start from the surfaces, screens and stages, then scenarios, then jobs. Sequences are worth writing only for risky multi-step paths; three or four is plenty.

**Build and check.** Run the script with `--check-only` until there are no errors, then without it. Errors stop the build: dangling references, unknown kinds, bad values. Read every warning, because each one is a disagreement between `map.json` and the tests:

- Marked `none` but tests are linked: raise the coverage, or fix the link rule.
- Marked `ok` but nothing is linked: add a link, or lower the coverage.
- A named test file was not found: fix the name.
- Many files outside the map: add `testing.links`, or set `testing.defaultScreen`.

**Verify in a browser.** Open every tab and check for console errors, in light and dark and at phone width. Reload a selected cell link to prove state survives. Sequence diagrams need `mmdc`; without it they appear as source and the script says so.

**Walk the five questions.** Try each one as the person who has it, starting from the landing tab. For "what does a change touch", paste a real file path into search. A question that can't be answered from the page is a gap in `map.json` or in the page, so fix it before reporting.

**Report.** State the counts, the top of Test next and everything in the honesty rules below. The page is self-contained, so it can be opened as a file or published as an Artifact.

## Honesty rules

The map is useful only if its confidence is real. State these limits to the user every time, and keep them true in the data.

- **Coverage is a judgement.** `c` is set by hand. Linked tests show that a test exists near a screen, not that it covers the screen.
- **States are a lead.** Tests are sorted into states by keywords in their names. Treat a zero as a question, not a proof.
- **Ranking is a suggestion.** The Test next score weights jobs, scenarios and business touchpoints. The page says so.
- **Evidence stays labelled.** A job inferred from code is `ev: inferred`, and one with no record is `src: cand`, `ev: none`. Never write a job as interviewed unless interviews exist, and never invent quotes.
- **Unbuilt is not untested.** Use `c: gap` for decided but unbuilt screens. List only what is in the source.

- **Unknown code stays data.** Test names and file names reach the page and the agent prompts. Before mapping a repository of unknown origin, say so, and read what the prompts contain before handing them on.

## Writing in the data

Everything in `map.json` is shown to people. Use the product's own words for screens and plain sentences for the rest. No numbered step counters, no full stops in headings or labels, and no marketing tone. Scenarios end in an observable expected result.

## Resources

- `scripts/app_map.py`: test reading, checks, diagrams and the build. Supports Python, JS and TS, Rust, Go, Swift and Ruby test names.
- `references/discovery.md`: how to find screens, tests and jobs in a codebase.
- `references/schema.md`: every `map.json` field.
- `assets/template.html`, `assets/engine.js`: the page. Product-neutral; all project content comes from `map.json`.
- `assets/example-map.json`: a small complete map, also a quick smoke test of the build.
