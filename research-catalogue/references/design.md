---
name: Research Catalogue
description: Contact-sheet editorial catalogue with direct filters, for any researched collection
colors:
  ink: "#1c1d1f"
  muted: "#5c5a55"
  label: "#42413f"
  primary: "#934124"
  pale: "#f2d6c4"
  paper: "#f9f9f7"
  mat: "#e0e0dc"
  surface: "#e7e7e4"
  background: "#ececea"
  dark-background: "#121212"
  dark-primary: "#eeb298"
typography:
  display:
    fontFamily: "Newsreader, Georgia, Times New Roman, serif"
    fontWeight: 400
    lineHeight: 0.95
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, Menlo, monospace"
    fontSize: "12px uppercase, tracked; utility labels only"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "16px"
    lineHeight: 1.55
rounded:
  control: "0px"
  panel: "0px"
---
## Overview
A contact-sheet editorial look on a neutral archival grey (not cream). Images sit on a mat like prints; a serif masthead carries an italic accent word (`title.accent`). Mono capitals are reserved for utility labels (field names, table headers, month ticks, days left) in the --label token, which clears APCA Lc 75; headings, filter groups and actions use sentence case. No frame numbers: list order is not a sequence. Fonts load from Google Fonts and fall back to Georgia/system fonts offline.

What the collection is — its nouns, facets, card rows, table columns and detail fields — comes from the project's `catalogue.json`. The template never names a topic.

## Colors
Dark neutral ink for titles, warm brown actions, light terracotta selected states and paper surfaces on a quiet neutral canvas.

## Typography
Serif page heading; system sans-serif for data. Dates and measures have a larger, heavier weight with tabular figures.

## Layout
Bounded canvas; concise heading and filters collapsed by default; direct filter groups and selection criteria live inside the disclosure. Three card columns become two and then one. On narrow screens filter choices scroll within their group. The comparison table fits desktop width in percentage columns; below 1000px it switches to fixed pixel columns and scrolls inside its own container with the name column pinned (180px on phones), never widening the page. No statistics hero, instructional sections or generic copyright footer.

## Optional blocks
- **Images** (`images`, default on when `assets/manifest.json` exists): matted image on cards, table and dialog; off gives text cards.
- **Date** (`date`): date box, relative marker (`countdown`), timeline (`timeline`), date sorting. `kind` sets the wording: deadlines count down and turn urgent within `soonDays`; events say "In n days"; publications age ("3 months ago") and sort newest first; `other` shows dates only.
- **Measures** (`measures`): any number of numeric facts (price, size, score, year). Up to three show as boxes on cards; the first shares the date's table column with a sort pair (which may wrap onto two lines), the rest get their own sortable columns. Each starts sorting in its better direction.
- **Verification** (`verification`): a status badge with a last-checked date on cards and table rows, a status filter, and a verification box with confidence and notes in the dialog. Status is carried by badge shape as well as colour: filled square for verified, hollow square for unverified or needing a re-check, diamond for conflicting sources.
- **Stream** (`layout: "stream"`): for dated research read newest first. A single reading column instead of cards: margin date, serif headline as a button, one muted summary line, a meta line with source, topic and any measure. Week headings (serif, larger than headlines) carry the grouping; hairline separators between items; the bookmark stays transparent until saved. No mono caps labels in the list.
Without a block, none of its parts render.

## Elevation & Depth
Flat, borderless surfaces. Separate content through spacing, typography and surface colour rather than decorative outlines. A modal overlays the page for full details and image credits.

## Shapes
Square edges throughout: cards, controls, input fields, table surfaces and dialog use zero border radius and no decorative borders. Preserve visible keyboard focus outlines and disclosure chevrons.

## Components
Search; one button group per facet plus the sort order, with visible pressed states and optional counts; zero-value toggles (such as free entry) and favourites; gallery/table selector; cards; table rows; full-details dialog. Small choice sets use direct buttons, never dropdowns.

## Do's and Don'ts
Preserve factual copy and image credits. Keep unknown values visible as —. Missing values sort last in both directions.

## Interaction continuity
Facets, search, sort and direction, view and the open item are restored from URL parameters on load and Back/Forward; the filter disclosure still starts collapsed. Activated controls retain focus. Name, date and measure headers toggle sort direction with `aria-sort`. Empty editions and zero filter matches use separate states and only useful reset actions.

## Language
Interface copy lives in the builder's default strings and the project's `strings` overrides; dates and currency follow `locale` (en-GB for English). Translation does not advance the research snapshot or verify facts anew.

## Timeline
When the collection has dates, a compact timeline under the masthead places every dated item on a month axis (a year axis when the range exceeds about 18 months) with a Today line, whose label flips to the left near the right edge. Marks stack when dates are close, turn the urgent colour within `soonDays` (default 30), fade when filtered out, show a tooltip on hover and open full details on click. The track is a redundant visual index (aria-hidden, marks not in tab order); the sentence above it ("Next to close: …" for deadlines, "Next up: …" for events, "Most recent: …" for publications) is readable and its names are buttons. Cards and table remain the full accessible path.

## Relative dates
Days left, "in n days" and ages are derived in the browser from today's date against the researched date, not research facts; past deadlines read "Closed", past events "Past".

## Theme
Light by default from the system setting; a dark theme (neutral near-black, light terracotta accent) follows prefers-color-scheme, and the sun/moon button pins a choice per browser.

## Contrast
--label (small mono capitals) clears WCAG 4.5:1 and APCA Lc 75 on every surface in both themes. --muted, --accent and --soon clear WCAG 4.5:1 and APCA Lc 65 on every surface; they are reserved for 13px+ secondary text and links. Measured 2026-11-21.

## Motion
One orchestrated moment: the first-load card cascade (400ms, 30ms stagger, capped at 9 cards). Otherwise motion is functional only, all on --ease-out cubic-bezier(.23,1,.32,1): filter disclosure height/opacity 220ms; dialog enters and leaves the same way (opacity + 8px rise, 200ms, @starting-style); press feedback scale(.97) 120ms; timeline tooltip fade 140ms. Hover states apply only under (hover:hover) and (pointer:fine). Reduced motion keeps fades and drops transforms.

## Unknown-with-note fields
`dashNote` fields that start with — put the dash on its own line; any archive link or note starts on the next line.
