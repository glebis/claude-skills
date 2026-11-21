---
name: Photo Open Calls
description: Darkroom contact-sheet catalogue with direct filters
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
Redesign 2026-11-21: a darkroom / contact-sheet editorial look on a neutral archival grey (not cream). Images sit on a mat like prints with a days-left marker; serif masthead with an italic accent word. Mono capitals are reserved for utility labels (field names, table headers, month ticks, days left) in the --label token, which clears APCA Lc 75; headings, top bar, filter groups and actions use sentence case. No frame numbers: list order is not a sequence. Fonts load from Google Fonts and fall back to Georgia/system fonts offline.

## Colors
Dark neutral ink for titles, warm brown actions, light terracotta selected states and white surfaces on a quiet neutral canvas.
## Typography
Serif page heading; system sans-serif for data. Dates and prices have a larger, heavier weight.
## Layout
Bounded canvas; concise heading and filters collapsed by default; direct filter groups and selection criteria live inside the disclosure. Three card columns become two and then one. On narrow screens filter choices scroll within their group. The comparison table keeps its columns and scrolls inside its own container without widening the page. No large statistical hero, instructional sections or generic copyright footer.
## Elevation & Depth
Flat, borderless surfaces. Separate content through spacing, typography and surface colour rather than decorative outlines. A modal overlays the page for full conditions and image credits.
## Shapes
Square edges throughout: cards, controls, input fields, table surfaces and dialog use zero border radius and no decorative borders. Preserve visible keyboard focus outlines and disclosure chevrons; they communicate interaction and are not decorative surface borders.
## Components
Search; region, format, genre and sort buttons with visible pressed states; free and favorites toggles; gallery/table selector; image-led cards; table rows; full conditions dialog. Small choice sets use direct buttons, never dropdowns.
## Do's and Don'ts
Preserve factual copy and image credits. Keep unknown values visible. Live variants must remain reversible until accepted.

## Interaction continuity
Filters, search, sorting direction and view are restored from URL parameters on load and Back/Forward; the filter disclosure still starts collapsed. Activated controls retain focus. Name, deadline and price headers toggle sorting direction with accessible state. Narrow tables pin a compact contest identifier. Empty editions and zero filter matches use separate states and only useful reset actions.

## Language
Interface language follows the project (the bundled template is English, en-GB dates and currency). Translation does not advance the research snapshot or verify facts anew.

## Deadline ribbon
A compact timeline under the masthead places every call on a month axis with a Today line. Marks stack when deadlines are close, turn the urgent colour within 30 days, fade when filtered out, show a tooltip on hover and open the full terms on click. The track is a redundant visual index (aria-hidden, marks not in tab order); the "Next to close" sentence above it is readable and its names are buttons. Cards and table remain the full accessible path. It is navigation, not a statistics block.

## Days left
Cards, table rows and the dialog show days remaining, computed in the browser from today's date against the researched deadline. It is derived, not a research fact; past deadlines read "Closed".

## Theme
Light by default from the system setting; a darkroom dark theme (neutral near-black, light terracotta accent) follows prefers-color-scheme, and the top-bar button pins a choice per browser (localStorage, optional).

## Contrast
--label (small mono capitals) clears WCAG 4.5:1 and APCA Lc 75 on every surface in both themes. --muted, --accent and --soon clear WCAG 4.5:1 and APCA Lc 65 on every surface; they are reserved for 13px+ secondary text and links. Measured 2026-11-21.

## Motion
One orchestrated moment: the first-load card cascade (400ms, 30ms stagger, capped at 9 cards). Otherwise motion is functional only, all on --ease-out cubic-bezier(.23,1,.32,1): filter disclosure height/opacity 220ms; dialog enters and leaves the same way (opacity + 8px rise, 200ms, @starting-style); press feedback scale(.97) 120ms on buttons; ribbon tooltip fade 140ms. Hover states apply only under (hover:hover) and (pointer:fine). Reduced motion keeps fades and drops transforms. No card lift, image zoom or arrow nudges.

## URL
Opening full terms adds ?call=<id>; deep links open that call over the restored filters, and Back/Forward open and close it.

## Timeline sentence
Above the ribbon: "Next to close: <linked calls>, <date> · <days left>." The names open full terms. With no upcoming deadline it says every deadline has passed.

## Winners and table flow
Unknown winners use an em dash on its own line, without a period; any archive link or explanatory note starts on the following line and wraps naturally. Table rows scroll with the page, with no internal vertical scroller. Columns fit desktop width; horizontal scrolling is confined to narrow screens, where the contest identifier remains pinned.

## Compact masthead controls
The heading is Photography Open calls. The top-bar Snapshot label is omitted. A sun/moon SVG theme switch retains accessible action labels. Deadline / Fee sorting remains on one line at all viewport widths.
