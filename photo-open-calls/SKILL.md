---
name: photo-open-calls
description: This skill should be used to research photography open calls (awards, exhibitions, festivals, photobook prizes, grants and residencies) against a photographer's profile and to build or refresh a standalone HTML catalogue of them, with image-led cards, a comparison table, a deadline timeline, filters, favourites and full terms with sources. Triggers on "find open calls for my photography", "refresh the open-calls catalogue", "build the open-calls page", "weekly open calls run", "add this competition to the catalogue", or "show the open-calls demo".
---

# Photo open calls

Two separate jobs that share one data folder: **research** keeps verified facts up to date, and **build** turns them into one self-contained HTML file. A data refresh never restyles the page, and a redesign never changes facts.

Everything about the photographer lives in their project folder, never in this skill. The skill's own demo (`examples/demo/`) is synthetic.

## Project folder

| File | Holds |
| --- | --- |
| `calls.json` | Full researched records: deadline, fees, style, photos, printing, rights, winners, eligibility, benefits, sources |
| `catalog-meta.json` | Compact display fields keyed by the same stable `id` (short name, ISO date, euro value, formats, genres, summaries, optional `feeNote` / `rightsNote`) |
| `snapshot.json` | Research date, its label, and the minimum deadline the run accepted |
| `profile.json` | Selection criteria shown on the page and the region list |
| `assets/manifest.json` | One entry per image: type, caption, credit, `short_credit`, source URL, local path |
| `assets/previews/<id>.webp` | Preferred embedded image; falls back to `local_path`, then `image_url` |
| `research/YYYY-MM-DD/` | Evidence log for each research run |

Field-by-field format: `references/data-format.md`. To start a new project, copy `examples/demo/` and replace its records.

## Build

```sh
python3 scripts/build.py --project /path/to/project --output /absolute/path/open-calls.html
```

Standard library only. The output embeds data and images, so it opens straight from disk; official links still need internet, and fonts fall back to Georgia and system fonts offline. A project may carry its own `template.html`; otherwise the skill's `assets/template.html` is used. The build fails on mismatched ids or unresolved placeholders.

`--output` writes a local file. Publishing anywhere (a hosted site, a repository) only happens when the user asks for it in this conversation; a local build is complete on its own.

Demo: `python3 scripts/build.py --project examples/demo --output /tmp/open-calls-demo.html`.

## Research

1. **Read the profile first.** Genres, eligibility (nationality, residence, age), budget caps, minimum time to deadline and regions come from the user's `profile.json` and project notes. Ask once if they are missing; never guess eligibility.
2. **Verify against official rules.** Positive eligibility must be stated; silence is not eligibility. Record original currencies and the source and date of any conversion. Separate online submission from physical arrival deadlines, and entry fees from later production or travel costs.
3. **Keep required fields.** Every record keeps genre, photo count, printing and who pays, rights (scope, duration, exclusivity), past winners and primary source links. Unknown facts stay `—`. Distinguish winners, shortlists, residents and exhibition archives.
4. **Preserve provenance.** Keep ids stable across runs so favourites survive. Log each changed field with source URL and date under `research/YYYY-MM-DD/`. If a source cannot be read, keep the previous fact, flag the gap, and do not present it as freshly verified. Keep conflicting dates or terms explicit.
5. **Separate lists.** Keep verified open calls in the catalogue; archive closed or ineligible ones; keep upcoming, rolling and unresolved ones apart. Report only real changes as new.
6. **Images.** Use official images with caption, credit and source. Label winners, posters and spaces accurately. Never substitute unrelated images; missing images get the page's fallback.

Generating a file does not advance `snapshot.json`; only a research run does.

## Language

Use the language of the user's request for interface labels, dates and the delivery note, unless they choose another. Official names, quoted terms and links stay as they are. An unattended weekly run reuses its configured language.

## Preserve the interface

The page design is documented in `references/design.md`. Keep: matted images shown whole with a days-left marker; serif masthead; sentence-case chrome with mono capitals only for utility labels; the deadline timeline with its "Next to close" sentence; filters collapsed by default with one-click choices (no dropdowns); cards and a sortable comparison table; favourites; full terms in a dialog with sources and image credits; light and dark themes; square edges and no decorative borders; visible focus.

State lives in the URL (filters, search, sort direction, view, open call via `?call=<id>`) and is restored on load and Back/Forward. No statistics hero, instructional sections or generic copyright footer.

## Check before delivering

- Build passes; ids match; no placeholders remain.
- Open the file: collapsed filters, combined filters, both sort directions with `aria-sort`, favourites keep focus, zero matches offers reset, a 0-record and a 1-record edition read correctly, `?call=` deep link opens and Back closes it.
- Phone width (375px): no page-level horizontal scroll; the table scrolls inside itself with the call name pinned.
- Both themes.
- For design-only work, research files are unchanged. For research work, the evidence log exists.
