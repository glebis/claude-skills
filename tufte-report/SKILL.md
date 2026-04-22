---
name: tufte-report
description: Create Tufte-inspired data reports and infographic dashboards as standalone HTML files. Uses EB Garamond for text, Monaspace Argon for numbers, Chart.js for interactive charts, and inline SVG sparklines. Produces publication-quality reports with 2-column narrative+data layouts, status dashboards, scroll animations, and responsive mobile support. Use this skill whenever the user wants to create a data report, activity dashboard, infographic, personal analytics page, health tracker visualization, or any document that combines narrative text with interactive charts and tables. Also triggers for "make a report like Tufte", "create an infographic", "build a dashboard", "visualize my data", or requests for beautiful data-driven documents.
---

# Tufte Report — Data-Driven Infographic Skill

Create standalone HTML reports that combine editorial narrative with interactive data visualization in Edward Tufte's style: high information density, minimal chart junk, typography-first design.

## Design Philosophy

Tufte's core principles drive every decision:
- **Data-ink ratio**: every pixel of ink should represent data, not decoration
- **Small multiples**: repeat a design to show comparison, not animation
- **Sparklines**: word-sized graphics that live inside prose
- **Layering**: overview first, then detail on demand
- **Integration**: text and graphics share the same visual space (sidenotes, not footnotes)

The report should feel like a well-edited magazine feature — you read it top to bottom, narrative carries you through the data, and every chart earns its space by answering a specific question.

## Onboarding — Ask Before Building

Before writing ANY code, ask these questions. Do not proceed until all are answered:

1. **What data sources do you have?** (CSV, JSON, SQLite, API endpoint, or raw numbers)
2. **What is the primary question this report should answer?** (one sentence — this becomes the title and drives all design decisions)
3. **How many sections do you need?** (cap at 8 — push back if more are requested; each section should answer one sub-question)
4. **What's the output format?** (standalone HTML file, or embedded component)
5. **Time budget?** Provide an estimate:
   - 1-2 sections with tables only: ~200 LOC, ~5 min bypass / ~10 min manual
   - 3-4 sections with 2-3 charts: ~500 LOC, ~15 min bypass / ~25 min manual
   - 5-8 sections with charts + health data + sparklines: ~1200 LOC, ~30 min bypass / ~50 min manual

## Scope Protection

This skill enforces hard limits to prevent scope creep:

- **Max 8 sections** — if the user asks for more, suggest combining related topics
- **Max 2 chart types per section** — a section gets one primary chart and optionally one supporting chart or table. More than that means the section should split
- **Max 3 colors per chart** — beyond that, use small multiples instead of rainbow legends
- **No 3D charts, no pie charts, no donut charts** — these violate Tufte principles
- **No gratuitous animation** — scroll-reveal on enter is fine; spinning, bouncing, or pulsing is not
- **Every chart must have a caption** — if you can't write a one-sentence caption explaining what the chart shows, the chart shouldn't exist

When the user asks for something outside these limits, respond with: "That would take the report from [current LOC estimate] to [new estimate]. The extra complexity adds [X] but risks [Y]. Shall I proceed, or can we [simpler alternative]?"

## Architecture

```
report.html (standalone, no build step)
├── Google Fonts CDN (EB Garamond)
├── jsDelivr CDN (Monaspace Argon woff2)
├── jsDelivr CDN (Chart.js 4.x UMD)
├── Inline <style> (design system CSS)
├── Inline HTML (semantic structure)
└── Inline <script> (data + Chart.js configs + sparklines + scroll-reveal)
```

No build tools, no frameworks, no npm. One file, opens in any browser.

## Design System

Read `references/design-tokens.md` for the complete CSS variables, typography scale, and color palette.

Read `references/components.md` for the HTML+CSS snippet of every reusable component.

Read `references/charts.md` for Chart.js configuration patterns and inline SVG sparkline code.

## Report Structure Template

Every report follows this skeleton:

```
1. Title + subtitle + data source tags (monospace, subtle)
2. [Optional] Status dashboard (4-column KPI strip)
3. Overview narrative with inline sparklines + TOC sidebar
4. Summary cards (2-4 KPI tiles with sparklines)
5. Sections (each: state-line → chart+narrative aside → table+narrative aside)
6. [Optional] Decision register (threshold table with status colors)
7. Footer (generation date, sources)
```

### Section Pattern

Each section follows this rhythm:
```
<h2> with ↑ back-to-top link
<p class="state-line"> — one italic sentence, the takeaway
<div class="aside-container"> — chart on left, narrative on right
<div class="aside-container"> — table on left, interpretation on right
```

The alternation of chart→narrative→table→narrative creates visual breathing room and prevents "wall of data" fatigue.

### Rules for Narrative Text

- **State-lines** (the italic intro under each heading): one sentence, max 20 words, states the conclusion not the topic. "HRV down 13%, steps down 42%" not "This section covers health metrics"
- **Aside narratives**: 3-4 short paragraphs, each starting with a bold keyword. Written like a newspaper sidebar — facts first, interpretation second
- **Flyouts**: reserved for actionable insights or methodology notes. The ✦ symbol marks them as "pay attention"
- **No "tells its own story"** or similar filler. Every sentence should contain a number or a decision

## Dual-Font Strategy

| Context | Font | Why |
|---------|------|-----|
| All body text, headers, captions | EB Garamond | Classical editorial feel, excellent readability |
| All numbers in tables | Monaspace Argon | Tabular figures align in columns, monospace scannability |
| Big numbers in cards/dashboards | Monaspace Argon | Visual weight, distinct from prose |
| Status indicators, trend percentages | Monaspace Argon | Precision signaling |
| Data source tags, code references | Monaspace Argon | Technical register |
| Ornament separators (:::) | Monaspace Argon with ligatures | Programming aesthetic, replaces floral Unicode |

## Color Principles

Use `--ink` (near-black) for text, `--bg` (warm white) for background. Chart colors must be semantically meaningful — don't assign colors randomly:

- **Orange** (`--spark-claude`, #c45a28): primary data stream, effort/work metrics
- **Green** (`--spark-wispr`, #2a7a5a): growth, positive health signals, English language
- **Purple** (`--spark-social`, #5a5aaa): social/communication metrics
- **Blue** (rgba(42,80,140)): secondary overlay lines on charts
- **Red** (#a02a2a): alerts, negative trends, declining metrics
- **Amber** (#c89000): warnings, watch-level signals
- **Green** (#2a7a3a): healthy baselines, positive trends

Never use more than 3 colors in a single chart. If you need more, use opacity/saturation variations of the same hue.

## Session Lessons (What Goes Wrong)

Based on building the reference report, these are the recurring problems:

1. **Chart.js CDN version**: Use `@4` not a specific patch version — specific versions may not exist
2. **Chart.js defaults**: Set individual properties, never replace entire objects (`Chart.defaults.scale.grid.color = '#eee'` not `Chart.defaults.scale.grid = {color: '#eee'}`)
3. **Legend circles**: Use `usePointStyle: false` with `boxWidth: 8, boxHeight: 8, borderRadius: 4` for true circles. `usePointStyle: true` creates ovals
4. **file:// protocol**: Charts won't load CDN scripts via file://. Always test via localhost
5. **Back-to-back charts**: Always separate consecutive charts with narrative, a table, or an ornament. Two charts in a row = "wall of data"
6. **Table overflow on mobile**: Wrap in `.table-wrapper` and add `.hide-mobile` to secondary columns
7. **Dual-axis charts**: Use sparingly — they invite false visual equivalence. Always label both axes clearly
8. **Narrative overreach**: Don't claim correlations without computing them. "r = 0.10" is more trustworthy than "strong relationship"

## Universal Data Adapter

When the user provides data from any source (CSV, JSON, SQLite, API, raw numbers), normalize it into the standard **ReportData** intermediate format before generating HTML. This decouples data ingestion from report rendering.

Read `references/data-adapter.md` for the ReportData JSON schema, field reference, and adapter instructions for each source type.

**Workflow:**
1. User provides data → identify source type
2. Transform into ReportData JSON (ask user for `meta.question` and desired sections)
3. Confirm the normalized structure with the user
4. Generate HTML from the ReportData using the block library

## Composable Block Library

Reports are assembled from typed blocks, each with a defined data contract. This replaces ad-hoc HTML generation with a systematic approach.

Read `references/blocks.md` for the complete block catalog: sparkline-row, kpi-card, trend-chart, data-table, correlation-matrix, narrative, heatmap, strip-chart.

Each block defines:
- **Data contract** (what JSON shape it expects)
- **HTML template** (copy-paste ready)
- **Composition rules** (how blocks pair and sequence)

## Preview Server

For iterative development, use the built-in live-reload server:

```bash
python3 ~/.claude/skills/tufte-report/scripts/serve.py report.html
```

Serves on `localhost:8042`, auto-reloads on file change with scroll position preserved. Zero dependencies — Python stdlib only.

Read `references/preview-server.md` for details. After generating a report, offer to start the preview server for the user.
