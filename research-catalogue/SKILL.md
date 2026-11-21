---
name: research-catalogue
description: This skill should be used to research any collection of comparable things — opportunities (open calls, grants, jobs, conferences), products, tools, places, courses, studies or papers, sources, vendors — against a user's question and criteria, and to build or refresh a standalone HTML catalogue of the verified results, with cards, a sortable comparison table, filters, favourites, optional dates and timeline, numeric measures, per-item verification status and full details with sources. Triggers on "research and compare", "build a catalogue of", "make a comparison page for", "literature review page", "refresh the catalogue", "weekly research run", "add this to the catalogue", "find options for me and put them in a page", or "show the catalogue demo".
---

# Research catalogue

Two separate jobs share one project folder: **research** keeps verified facts up to date, and **build** turns them into one self-contained HTML file. A data refresh never restyles the page, and a redesign never changes facts.

The skill knows nothing about any topic. What a collection *is* — its nouns, filters, numbers, dates, card rows, table columns and detail fields — lives in the project's `catalogue.json`. Everything about the user (eligibility, budget, preferences) lives in the project folder, never in this skill.

## Project folder

| File | Holds |
| --- | --- |
| `catalogue.json` | What the collection is and how to show it (see `references/data-format.md`) |
| `items.json` | Full researched records, any fields, each with a stable `id` |
| `items-meta.json` | Optional compact display fields keyed by id |
| `snapshot.json` | Research date and label, plus any thresholds the run used |
| `profile.json` | Selection criteria shown on the page |
| `assets/manifest.json`, `assets/previews/<id>.webp` | Optional images with type, caption, credit and source |
| `research/YYYY-MM-DD/` | Evidence log for each research run |

To start a project, copy the closest example and replace its records:

| Example | Shows |
| --- | --- |
| `examples/photo-open-calls/` | Deadlines with countdown and timeline, a currency measure with a free toggle, images, verification badges |
| `examples/espresso-grinders/` | No dates or images; two measures (price, noise in dB) with their own sorts |
| `examples/sleep-memory-studies/` | Publication dates ("3 months ago", newest first), sample and effect size measures, verification with conflicting sources |

## Design a new catalogue

Before researching, settle with the user (ask once, briefly, only what is unclear):

1. **The question and the noun.** "Which grinders under €800 suit home espresso?", "What do recent studies say about sleep and memory?" This becomes `title`, `dek` and `noun`, and decides what counts as in scope.
2. **Dates.** Does each item have a date that matters? Pick the `kind`: a deadline, an event, a publication, or other. Leave the block out when dates don't help the decision.
3. **Measures.** Which numbers do people compare: price, size, score, year, distance? For each, its unit and whether higher or lower is better.
4. **Facets.** Two or three short groups the user will filter by, with values the research can establish for every item.
5. **Card rows and detail.** Four or five summaries for the card; full text goes to `detail.fields`; the table repeats what is worth comparing side by side.
6. **Verification.** Turn it on when claims can go stale or sources disagree, which is most research.
7. **Images.** Only when an official image helps recognition (posters, products, places). Otherwise `"images": false`.

## Research method

1. **Scope.** Write down the question, inclusion and exclusion criteria (from `profile.json` and the user's words) and the time window. Ask once if a criterion that decides inclusion is missing; never guess eligibility, fit or preference.
2. **Sources.** Prefer primary sources: the organiser, maker, publisher, registry or dataset itself. Secondary sources (reviews, aggregators, news) can lead you to an item but don't confirm its facts. Record every source with URL and access date.
3. **Extract.** For each item, fill every field the catalogue shows. Numbers go in as numbers with the unit and basis named in a note (which package, which test condition, which currency and conversion date). Unknown facts stay `—` or `null`; never fill gaps with plausible values.
4. **Verify.** Set `status` per item:
   - `verified`: the shown facts were confirmed on a primary source in this run.
   - `unverified`: only secondary or announced information was available.
   - `conflicting`: sources disagree. Keep both versions in `verificationNote`; don't pick one silently.
   - `outdated`: facts come from an earlier run or edition and need a re-check.
   Set `checked` to the date you confirmed it and `confidence` to how much the item's key facts can be trusted.
5. **Distinguish look-alikes.** Keep apart things that read the same but aren't: winners vs shortlists, list vs street price, preprint vs peer-reviewed, announced vs confirmed dates, online vs physical deadlines.
6. **Log.** Under `research/YYYY-MM-DD/`, record what changed per item and field, with source and date, plus the items you excluded and why. If a source could not be read, keep the previous fact, mark the item `outdated` or `unverified`, and say so.
7. **Separate lists.** Keep in-scope, researched items in the catalogue. Archive closed, discontinued or excluded ones in the log rather than deleting the evidence. Report only real changes as new.
8. **Images.** Official images with caption, credit and source, labelled accurately. Never substitute unrelated images; missing images get the page's fallback.

Generating a file does not advance `snapshot.json`; only a research run does.

## Build

```sh
python3 scripts/build.py --project /path/to/project --output /absolute/path/catalogue.html
```

Standard library only. The output embeds data and images, so it opens straight from disk; official links still need internet, and fonts fall back to Georgia and system fonts offline. The build fails on duplicate or mismatched ids, non-ISO dates, non-numeric measures, clashing keys or unresolved placeholders.

`--output` writes a local file. Publishing anywhere (a hosted site, a repository) only happens when the user asks for it in this conversation; a local build is complete on its own.

Demo: `python3 scripts/build.py --project examples/sleep-memory-studies --output /tmp/studies.html`.

## Language

Use the language of the user's request for `title`, `dek`, labels and `strings`, unless they choose another; set `language` and, if needed, `locale`. Official names, quoted terms and links stay as they are. An unattended scheduled run reuses its configured language.

## Preserve the interface

The page design is documented in `references/design.md`. Keep: matted images shown whole; serif masthead with an italic accent; sentence-case chrome with mono capitals only for utility labels; filters collapsed by default with one-click choices (no dropdowns); cards and a sortable comparison table; favourites; full details in a dialog with sources and credits; light and dark themes; square edges and no decorative borders; visible focus. With dates: relative markers and the timeline with its sentence. With verification: badges whose shape carries the status.

State lives in the URL (facets, toggles, search, sort and direction, view, open record via `?item=<id>`) and is restored on load and Back/Forward. No statistics hero, instructional sections or generic copyright footer.

## Check before delivering

- Build passes.
- Open the file: collapsed filters, combined facets, every sort starting in its natural direction and reversing with `aria-sort`, missing values last, favourites keep focus, zero matches offers reset, a 0-item and a 1-item edition read correctly, `?item=` deep link opens and Back closes it.
- Phone width (375px): no page-level horizontal scroll; the table scrolls inside itself with the name pinned.
- Both themes.
- For design-only work, research files are unchanged. For research work, the evidence log exists and every item has a status.
