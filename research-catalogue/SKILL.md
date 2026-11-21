---
name: research-catalogue
description: This skill should be used to research a collection of comparable things (open calls, grants, residencies, conferences, jobs, products, tools, venues, courses, papers) against a user's criteria and to build or refresh a standalone HTML catalogue of them, with cards, a sortable comparison table, faceted filters, favourites, an optional date timeline and full details with sources. Triggers on "research and compare", "build a catalogue of", "make a comparison page for", "refresh the catalogue", "weekly research run", "add this to the catalogue", "find open calls / grants / options for me and put them in a page", or "show the catalogue demo".
---

# Research catalogue

Two separate jobs share one project folder: **research** keeps verified facts up to date, and **build** turns them into one self-contained HTML file. A data refresh never restyles the page, and a redesign never changes facts.

The skill knows nothing about any topic. What a collection *is* — its nouns, filters, card rows, table columns and detail fields — lives in the project's `catalogue.json`. Everything about the user (eligibility, budget, preferences) lives in the project folder, never in this skill.

## Project folder

| File | Holds |
| --- | --- |
| `catalogue.json` | What the collection is and how to show it (see `references/data-format.md`) |
| `items.json` | Full researched records, any fields, each with a stable `id` |
| `items-meta.json` | Optional compact display fields keyed by id (short names, ISO dates, numbers, one-line summaries) |
| `snapshot.json` | Research date and label, plus any thresholds the run used |
| `profile.json` | Selection criteria shown on the page |
| `assets/manifest.json`, `assets/previews/<id>.webp` | Optional images with type, caption, credit and source |
| `research/YYYY-MM-DD/` | Evidence log for each research run |

To start a project, copy the closest example and replace its records:

- `examples/photo-open-calls/` — deadlines, entry fees, images, region / format / genre facets.
- `examples/espresso-grinders/` — prices, no dates, no images, a custom "quietest first" sort.

## Design a new catalogue

Before researching, settle with the user (ask once, briefly, only what is unclear):

1. **The noun and the question.** "Grinders under €800 for home espresso", "residencies open to non-EU artists". This becomes `title`, `dek` and `noun`.
2. **Date and cost.** Does each item have a date that matters (deadline, event, release)? A comparable price? Each enables its block; leave out what doesn't apply rather than filling it with —.
3. **Facets.** Two or three short groups the user will actually filter by, with values the research can verify for every item.
4. **Card rows.** Four or five summaries that let the user decide from the card. Full text goes to `detail.fields`; the table repeats what is worth comparing side by side.
5. **Images.** Only when an official image helps recognition (posters, winners, products). Otherwise `"images": false`.

## Build

```sh
python3 scripts/build.py --project /path/to/project --output /absolute/path/catalogue.html
```

Standard library only. The output embeds data and images, so it opens straight from disk; official links still need internet, and fonts fall back to Georgia and system fonts offline. The build fails on duplicate or mismatched ids, non-ISO dates, non-numeric costs, reserved facet keys or unresolved placeholders.

`--output` writes a local file. Publishing anywhere (a hosted site, a repository) only happens when the user asks for it in this conversation; a local build is complete on its own.

Demo: `python3 scripts/build.py --project examples/espresso-grinders --output /tmp/grinders.html`.

## Research

1. **Read the profile first.** Eligibility, budget caps, thresholds and must-haves come from the user's `profile.json` and project notes. Ask once if they are missing; never guess eligibility or fit.
2. **Verify against primary sources.** Official rules, maker specifications, organiser pages. Positive eligibility or compatibility must be stated; silence is not a yes. Record original currencies and the source and date of any conversion. Keep conflicting dates or figures explicit.
3. **Keep every field the catalogue shows.** Unknown facts stay `—`; never fill gaps with plausible values. Distinguish similar-looking facts (winners vs shortlists, list vs street price, online vs arrival deadline).
4. **Preserve provenance.** Keep ids stable across runs. Log each changed field with source URL and date under `research/YYYY-MM-DD/`. If a source cannot be read, keep the previous fact, flag the gap, and do not present it as freshly verified.
5. **Separate lists.** Keep verified, in-scope items in the catalogue; archive closed, discontinued or out-of-scope ones; keep unresolved ones apart. Report only real changes as new.
6. **Images.** Official images with caption, credit and source, labelled accurately. Never substitute unrelated images; missing images get the page's fallback.

Generating a file does not advance `snapshot.json`; only a research run does.

## Language

Use the language of the user's request for `title`, `dek`, labels and `strings`, unless they choose another; set `language` and, if needed, `locale`. Official names, quoted terms and links stay as they are. An unattended scheduled run reuses its configured language.

## Preserve the interface

The page design is documented in `references/design.md`. Keep: matted images shown whole; serif masthead with an italic accent; sentence-case chrome with mono capitals only for utility labels; filters collapsed by default with one-click choices (no dropdowns); cards and a sortable comparison table; favourites; full details in a dialog with sources and credits; light and dark themes; square edges and no decorative borders; visible focus. With dates: days-left markers and the timeline with its "Next to close" sentence.

State lives in the URL (facets, search, sort and direction, view, open item via `?call=<id>`) and is restored on load and Back/Forward. No statistics hero, instructional sections or generic copyright footer.

## Check before delivering

- Build passes.
- Open the file: collapsed filters, combined facets, every sort in both directions with `aria-sort`, missing values last, favourites keep focus, zero matches offers reset, a 0-item and a 1-item edition read correctly, `?call=` deep link opens and Back closes it.
- Phone width (375px): no page-level horizontal scroll; the table scrolls inside itself with the name pinned.
- Both themes.
- For design-only work, research files are unchanged. For research work, the evidence log exists.
