# Universal Data Adapter

Normalize any data source into a standard intermediate format before building the report.

## Intermediate Schema: ReportData

Every report starts from this JSON structure. Claude transforms user-provided data (CSV, JSON, SQLite query results, API responses, raw numbers) into this format before generating HTML.

```json
{
  "meta": {
    "title": "Q1 Health Report",
    "subtitle": "Jan–Mar 2026",
    "question": "Is my sleep quality improving?",
    "generated": "2026-04-22T15:00:00Z",
    "sources": ["Apple Health", "Oura Ring API"]
  },
  "kpis": [
    {
      "id": "hrv",
      "label": "Avg HRV",
      "value": 42.3,
      "unit": "ms",
      "trend": -0.13,
      "status": "red",
      "sparkline": [38, 41, 44, 39, 42, 45, 40, 43],
      "context": "below 50ms baseline"
    }
  ],
  "sections": [
    {
      "id": "sleep",
      "title": "Sleep Architecture",
      "state_line": "Deep sleep down **18%**, REM stable at 22%",
      "blocks": [
        {
          "type": "trend-chart",
          "data": {
            "labels": ["Jan", "Feb", "Mar"],
            "datasets": [
              {"label": "Deep Sleep", "values": [1.2, 1.0, 0.98], "color": "primary"},
              {"label": "REM", "values": [1.5, 1.4, 1.5], "color": "secondary"}
            ]
          },
          "caption": "Hours per night, 7-day rolling average"
        },
        {
          "type": "narrative",
          "content": "**Deep sleep** declined steadily after the caffeine experiment in Feb. **REM** held steady, suggesting the issue is slow-wave, not total sleep."
        },
        {
          "type": "correlation-matrix",
          "data": {
            "variables": ["Screen time", "Caffeine", "Exercise", "Deep sleep"],
            "matrix": [
              [1.0, 0.15, -0.22, -0.45],
              [0.15, 1.0, -0.08, -0.38],
              [-0.22, -0.08, 1.0, 0.52],
              [-0.45, -0.38, 0.52, 1.0]
            ]
          },
          "caption": "Pearson correlations, 90-day window"
        }
      ]
    }
  ]
}
```

## Field Reference

### meta
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| title | string | yes | Becomes h1 |
| subtitle | string | no | Date range or scope |
| question | string | yes | The one question the report answers — drives design |
| generated | ISO datetime | yes | Auto-set at generation time |
| sources | string[] | yes | Shown in footer tags |

### kpis[]
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | string | yes | CSS id and anchor |
| label | string | yes | Human name |
| value | number | yes | Current value, displayed in Monaspace Argon |
| unit | string | no | "ms", "%", "hrs", etc. |
| trend | number | no | Fractional change (-0.13 = -13%). Sign determines arrow |
| status | "red" / "amber" / "green" | no | Maps to status-strip color |
| sparkline | number[] | no | Last 7-14 data points for inline sparkline |
| context | string | no | One-line note below the number |

### sections[].blocks[]

Each block has a `type` and a `data` shape. See `references/blocks.md` for the full block catalog.

## Adapter Instructions

When the user provides raw data, follow this process:

1. **Identify the source type**: CSV → parse headers as labels; JSON → map keys; SQLite → run query, use column names; API → extract from response body; raw numbers → ask for labels
2. **Ask the user** for the primary question (becomes `meta.question`) and desired sections
3. **Normalize numbers**: strip currency symbols, convert percentages to decimals for `trend`, keep display values as-is for `value`
4. **Compute derived fields**: sparklines from time-series slices, trends from first/last comparison, status from user-defined thresholds (ask if not provided)
5. **Emit the ReportData JSON** and confirm with the user before generating HTML

### Example: CSV → ReportData

Input CSV:
```csv
date,hrv_ms,deep_sleep_hrs,steps
2026-01-01,45,1.3,8200
2026-01-02,42,1.1,7800
...
```

Transformation:
- Each numeric column becomes a potential KPI (latest value, trend from first→last)
- Time-series columns become sparkline arrays
- Group related columns into sections
- Compute correlations between columns for correlation-matrix blocks

### Example: Raw numbers → ReportData

User says: "HRV is 42ms (was 48), sleep score 72 (was 81), steps 6200 (was 9100)"

Transformation:
- Three KPIs with computed trends: -12.5%, -11.1%, -31.9%
- Status inferred: all declining → amber/red
- Single section with a narrative summary block
