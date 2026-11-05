# Finding what to put on the map

## Surfaces

A surface is a place a person or agent meets the product, with its own code: a marketing site, web app, desktop app, CLI, API, agent skill, generated output. List them first, with their source paths.

## Screens

A screen is anything with its own purpose and entry point: pages, dialogs, sheets, tray menus, emails, generated files, command families. Include business touchpoints such as pricing, checkout, receipts, support and legal pages, and mark them `biz: true`.

Where to look:

- Routers and navigation: route tables, `pages/`, `app/`, nav components, deep links.
- Native apps: windows, sheets, menus, tray items, notification handlers.
- Dialogs: search for `dialog`, `modal`, `sheet`, `alert`, `confirm`.
- CLIs: the argument parser. Group a large command set into one screen rather than listing every command.
- Outside the app: outbound email, webhooks, generated files, checkout pages.
- Empty, error and onboarding screens, which are often separate components.

For each one record what it shows, how it is reached, where it leads and what it calls. Read the code that navigates; don't infer exits from names.

## Stages

Stages are the order a person meets the product, such as Discover, Buy, Install, Set up, Daily work, Share. They become the columns of the flow graph, so keep to about 12 or fewer. A screen may appear in more than one.

## Scenarios

Write them per journey, from the screen inventory. Each has steps and an observable expected result. Cover the failure paths as well as the working path: refusal, conflict, missing dependency, empty first run. Say honestly whether a test covers it today, and list the files in `t`.

## Gaps

While reading, note what looks untested or broken: flows that cross surfaces with no end-to-end test, states no test names, screens with no tests. Each gap points at a scenario, so write the scenario too.

## Tests

- Find the test globs, including inline ones such as Rust `#[cfg(test)]` modules.
- Decide the kinds that matter to this project, such as UI logic, unit, API, browser, live. A kind should tell someone where a new test goes and how to run it. Add a `kindGuide` entry for each kind an agent could write.
- Write `testing.links` so test files land on screens. Aim for few files outside the map. Files that aren't about any screen, such as release or lint checks, go in `testing.ignore`.
- Add `outside` as a regex of outside services, so failure paths through them suggest a mocked test. This only applies when a `mock` kind exists.
- Read the project's agent instructions and CI config for the real run commands.

## Jobs

In order of strength:

- Interview records: `jtbd.json` files (check `~/jtbd/`), research notes. Use `src: people`, with `ev: owner` or `ev: user` depending on who was interviewed.
- Specs, roadmaps and code comments that state who it is for. Use `src: code`, `ev: inferred`.
- What the site or README promises with no job statement behind it. Use `src: cand`, `ev: none`, and put the promise in `pr`.

Link each job to the screens that would serve it, and set `fit` honestly. If no job material exists at all, say so. Candidates inferred from the README are still worth listing, and the page will show them as unrecorded. Leave `jobs` empty rather than padding, and the Jobs tab disappears.

## Layers and sequences

Layers run from business and people-facing surfaces down to storage, each with a one-line note on what calls what. Rules are invariants every screen must keep, such as "the CLI is the only writer", taken from the code and docs. Sequences are Mermaid `sequenceDiagram` source for the risky paths.
