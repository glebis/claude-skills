# Block Library

Each block is a self-contained HTML+CSS+JS unit with a defined data contract. Blocks compose into report sections.

## Block Contract

Every block receives:
```javascript
{
  type: "block-type",      // determines which renderer to use
  data: { ... },           // type-specific data shape
  caption: "string",       // optional, shown below the block
  id: "unique-id"          // for CSS targeting and anchoring
}
```

Claude generates each block by looking up the type below and filling in the HTML template with the data.

---

## 1. sparkline-row

Inline sparkline with label and value. Used in tables, KPI strips, and inline text.

**Data contract:**
```json
{
  "label": "HRV",
  "value": 42.3,
  "unit": "ms",
  "sparkline": [38, 41, 44, 39, 42, 45, 40, 43],
  "color": "primary",
  "trend": -0.13
}
```

**HTML output:**
```html
<div class="sparkline-row">
  <span class="sr-label">HRV</span>
  <span class="sr-value"><span class="mono">42.3</span> ms</span>
  <svg class="spark-inline" id="spark-hrv" width="60" height="16"></svg>
  <span class="sr-trend down">▼ 13%</span>
</div>
```

**Rendering JS:**
```javascript
drawSparkline('spark-hrv', [38,41,44,39,42,45,40,43], `var(--spark-primary)`);
```

---

## 2. kpi-card

Summary card with big number, sparkline, and context.

**Data contract:**
```json
{
  "label": "Claude Code",
  "value": "2,082",
  "sparkline": [120, 180, 340, 520, 610, 780],
  "detail": "sessions across 81 active days",
  "trend_text": "+450% growth Jan–Apr",
  "trend_direction": "up",
  "color": "primary"
}
```

**HTML output:**
```html
<div class="summary-card" style="--card-color: var(--spark-primary)">
  <div class="label">Claude Code</div>
  <div class="big-number-row">
    <div class="big-number">2,082</div>
    <svg class="card-spark" id="cardSparkClaude" width="80" height="30"></svg>
  </div>
  <div class="detail">sessions across 81 active days</div>
  <div class="trend up">+450% growth Jan–Apr</div>
</div>
```

Wrap 2–4 cards in `<div class="summary-row">`.

---

## 3. trend-chart

Line or bar chart via Chart.js. The workhorse visualization.

**Data contract:**
```json
{
  "chart_type": "line",
  "labels": ["Jan", "Feb", "Mar", "Apr"],
  "datasets": [
    {
      "label": "Deep Sleep",
      "values": [1.2, 1.0, 0.98, 1.1],
      "color": "primary",
      "fill": true
    },
    {
      "label": "REM",
      "values": [1.5, 1.4, 1.5, 1.6],
      "color": "secondary",
      "fill": false
    }
  ],
  "y_label": "hours",
  "x_label": "Month"
}
```

**HTML output:**
```html
<div class="chart-container reveal">
  <canvas id="chartDeepSleep" height="260"></canvas>
  <div class="caption">Hours per night, 7-day rolling average</div>
</div>
```

**Color mapping:** `"primary"` → `--spark-primary`, `"secondary"` → `--spark-secondary`, `"tertiary"` → `--spark-tertiary`. Direct hex also accepted.

**Rules:**
- Max 3 datasets per chart (use small multiples for more)
- Always include `y_label`
- Set `fill: true` for area charts, `false` for overlay lines
- Chart.js config: see `references/charts.md` for defaults

---

## 4. data-table

Structured table with optional inline sparklines and highlight rows.

**Data contract:**
```json
{
  "columns": [
    {"key": "label", "header": "Metric", "align": "left", "font": "serif"},
    {"key": "current", "header": "Current", "align": "right", "font": "mono"},
    {"key": "previous", "header": "Previous", "align": "right", "font": "mono"},
    {"key": "shape", "header": "Shape", "type": "sparkline"}
  ],
  "rows": [
    {"label": "HRV", "current": "42.3", "previous": "48.1", "shape": [38,41,44,39,42], "highlight": true},
    {"label": "Steps", "current": "6,200", "previous": "9,100", "shape": [9100,8800,7200,6800,6200]}
  ],
  "hide_on_mobile": ["previous"]
}
```

**HTML output:** Standard `<table>` wrapped in `.table-wrapper`, numbers in Monaspace Argon, sparklines rendered via `drawSparkline()`.

---

## 5. correlation-matrix

Heatmap grid showing pairwise correlations between variables.

**Data contract:**
```json
{
  "variables": ["Screen time", "Caffeine", "Exercise", "Deep sleep"],
  "matrix": [
    [1.0, 0.15, -0.22, -0.45],
    [0.15, 1.0, -0.08, -0.38],
    [-0.22, -0.08, 1.0, 0.52],
    [-0.45, -0.38, 0.52, 1.0]
  ]
}
```

**HTML output:**
```html
<div class="correlation-matrix reveal">
  <table class="corr-table">
    <thead><tr><th></th><th>Screen</th><th>Caffeine</th><th>Exercise</th><th>Sleep</th></tr></thead>
    <tbody>
      <tr><th>Screen</th><td style="background:rgba(160,42,42,0.0)">1.00</td><td style="background:rgba(160,42,42,0.08)">0.15</td>...</tr>
    </tbody>
  </table>
  <div class="caption">Pearson correlations, 90-day window</div>
</div>
```

**Color logic:**
- Positive correlations: green channel intensity = `abs(r) * 0.4` opacity of `--status-green`
- Negative correlations: red channel intensity = `abs(r) * 0.4` opacity of `--status-red`
- Diagonal (1.0): neutral gray
- Display values in Monaspace Argon

---

## 6. narrative

Prose block with optional bold keywords. Pure text, no visualization.

**Data contract:**
```json
{
  "content": "**Deep sleep** declined steadily after the caffeine experiment in Feb. **REM** held steady, suggesting the issue is slow-wave, not total sleep.",
  "style": "aside"
}
```

**Styles:** `"body"` (full-width, normal size), `"aside"` (280px sidebar, smaller italic), `"flyout"` (callout box with diamond marker).

**HTML output:** Depends on style. `"body"` → `<p>`, `"aside"` → wraps in `.aside` div, `"flyout"` → wraps in `.flyout` div.

---

## 7. heatmap

Calendar or grid heatmap for daily/weekly data.

**Data contract:**
```json
{
  "period": "daily",
  "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  "series": [
    {"week": "W1", "values": [3, 5, 2, 7, 4, 1, 0]},
    {"week": "W2", "values": [4, 6, 3, 5, 5, 2, 1]}
  ],
  "color": "primary",
  "max_value": 7
}
```

**HTML output:** CSS Grid of cells, opacity proportional to `value / max_value`, using the semantic color.

---

## 8. strip-chart

Horizontal bar rows — good for ranked or periodic data.

**Data contract:**
```json
{
  "rows": [
    {"label": "W1 Jan 6", "value": 42, "note": "started tracking"},
    {"label": "W2 Jan 13", "value": 38},
    {"label": "W3 Jan 20", "value": 55, "note": "peak week"}
  ],
  "max_value": 55,
  "color": "primary",
  "value_label": "messages"
}
```

**HTML output:** Each row is `.tg-week` + `.tg-count` + `.tg-bar-area` (proportional width) + `.tg-note`.

---

## Composing Blocks into Sections

A section is a sequence of blocks. The layout engine follows these rules:

1. **Never place two chart blocks back-to-back** — insert a narrative or data-table between them
2. **Pair charts with narratives** using aside-container layout (chart left, narrative right)
3. **KPI cards** always go in `summary-row` groups of 2–4
4. **Correlation matrices** are standalone — they don't pair with asides
5. **Strip charts** and **heatmaps** span full width

### Section Assembly Example

```json
{
  "id": "sleep",
  "title": "Sleep Architecture",
  "state_line": "Deep sleep down **18%**, REM stable",
  "blocks": [
    {"type": "trend-chart", "data": {...}, "caption": "..."},
    {"type": "narrative", "data": {"content": "...", "style": "aside"}},
    {"type": "data-table", "data": {...}},
    {"type": "narrative", "data": {"content": "...", "style": "aside"}},
    {"type": "correlation-matrix", "data": {...}, "caption": "..."}
  ]
}
```

This renders as:
```
h2 + state-line
aside-container: [trend-chart | narrative]
aside-container: [data-table | narrative]
correlation-matrix (full width)
ornament separator
```
