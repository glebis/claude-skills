---
name: health-data
description: Query Apple Health SQLite database for vitals, activity, sleep, and workouts. Supports Markdown, JSON, and FHIR R4 output formats. This skill should be used when analyzing health metrics, generating health reports, answering questions about fitness or sleep patterns, or exporting health data in standard formats.
---

# Apple Health Data Query Skill

Query and analyze health data from the local SQLite database containing 6.3M+ records across 43 health metrics.

## Database Location

```
~/data/health.db
```

## Query Methods

### 1. Python Script (Recommended for Common Queries)

Use `scripts/health_query.py` for pre-built queries with automatic formatting:

```bash
# Daily summary
python ~/.claude/skills/health-data/scripts/health_query.py --format markdown daily --date 2025-11-29

# Weekly trends
python ~/.claude/skills/health-data/scripts/health_query.py --format json weekly --weeks 4

# Sleep analysis
python ~/.claude/skills/health-data/scripts/health_query.py --format fhir sleep --days 7

# Latest vitals
python ~/.claude/skills/health-data/scripts/health_query.py vitals

# Activity rings
python ~/.claude/skills/health-data/scripts/health_query.py --format json activity --days 30

# Workout history
python ~/.claude/skills/health-data/scripts/health_query.py workouts --days 30 --type Running

# Custom SQL
python ~/.claude/skills/health-data/scripts/health_query.py --format json query "SELECT * FROM workouts LIMIT 5"
```

**Output formats:** `markdown`, `json`, `fhir`, `ascii`

### 2. Direct SQL (For Custom/Ad-hoc Queries)

For flexible queries, run SQL directly against the database. See `references/schema.md` for table structures and query templates.

```bash
sqlite3 ~/data/health.db "SELECT AVG(value) FROM health_records WHERE record_type LIKE '%HeartRate%' AND start_date LIKE '2025-11%'"
```

## Pre-built Queries

### Daily Health Summary

Get today's key metrics:
```bash
python ~/.claude/skills/health-data/scripts/health_query.py daily
```

Returns: steps, calories, heart rate (avg/min/max), exercise minutes, distance, activity ring status.

### Weekly Trends

Compare week-over-week performance:
```bash
python ~/.claude/skills/health-data/scripts/health_query.py weekly --weeks 4
```

Returns: average daily steps, resting HR, exercise minutes, workout count per week.

### Sleep Analysis

Analyze sleep patterns:
```bash
python ~/.claude/skills/health-data/scripts/health_query.py sleep --days 14
```

Returns: nightly duration, sleep stages (Core, Deep, REM), average sleep hours.

### Latest Vitals

Get most recent vital readings:
```bash
python ~/.claude/skills/health-data/scripts/health_query.py vitals
```

Returns: Heart Rate, HRV, Resting HR, Blood Oxygen, Respiratory Rate with timestamps.

### Activity Rings

Track ring completion:
```bash
python ~/.claude/skills/health-data/scripts/health_query.py activity --days 30
```

Returns: daily ring values/goals, completion percentages, perfect day count.

### Workout History

Review exercise sessions:
```bash
python ~/.claude/skills/health-data/scripts/health_query.py workouts --days 30 --type Running
```

Returns: workout type, duration, distance, calories, summary by type.

## Output Formats

### Markdown (default)

Human-readable tables and lists. Best for reports and summaries.

### JSON

Structured data for programmatic use:
```json
{
  "date": "2025-11-29",
  "metrics": {
    "steps": 8542,
    "active_calories": 450.5,
    "heart_rate": {"avg": 72.3, "min": 52, "max": 145}
  }
}
```

### FHIR R4

Healthcare interoperability format. Outputs as FHIR Bundle with Observation resources using LOINC codes. See `references/fhir_mappings.md` for code mappings.

### ASCII

Terminal-friendly output with bar charts and statistics:
```
============================================================
  DAILY SUMMARY - 2025-11-29
============================================================

METRICS
----------------------------------------
  steps                      2620
  active_calories           234.5
  heart_rate           avg:  67.5  min:  52  max: 108

ACTIVITY RINGS
----------------------------------------
  move       [███████░░░░░░░░░░░░░]  36.7% (238/650)
  exercise   [░░░░░░░░░░░░░░░░░░░░]   0.0% (0/35)
  stand      [████████████████████] 100.0% (10/10)
```

## Common SQL Patterns

For ad-hoc queries, use these patterns from `references/schema.md`:

**Heart rate by hour (circadian pattern):**
```sql
SELECT strftime('%H', start_date) as hour, ROUND(AVG(value), 1) as avg_hr
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierHeartRate'
AND value BETWEEN 40 AND 200
GROUP BY hour ORDER BY hour;
```

**Steps per day this month:**
```sql
SELECT DATE(start_date) as day, SUM(value) as steps
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierStepCount'
AND start_date >= DATE('now', 'start of month')
GROUP BY day ORDER BY day;
```

**Sleep quality (deep + REM hours):**
```sql
SELECT DATE(start_date) as night,
       ROUND(SUM(duration_minutes)/60.0, 1) as quality_hours
FROM sleep_sessions
WHERE sleep_stage IN ('Deep', 'REM')
GROUP BY night ORDER BY night DESC LIMIT 14;
```

**Workout summary:**
```sql
SELECT REPLACE(workout_type, 'HKWorkoutActivityType', '') as type,
       COUNT(*) as count, ROUND(SUM(duration_minutes)) as total_min
FROM workouts
WHERE start_date >= DATE('now', '-30 days')
GROUP BY type ORDER BY count DESC;
```

## Record Types Available

The database contains 43 health metric types including:

**Vitals:** Heart Rate, HRV, Resting HR, Blood Oxygen, Respiratory Rate, Blood Pressure

**Activity:** Steps, Distance, Active Calories, Basal Calories, Flights Climbed, Exercise Time, Stand Time

**Mobility:** Walking Speed, Step Length, Walking Asymmetry, Stair Speed, Walking Steadiness

**Body:** Weight, BMI, Body Fat %

**Audio:** Environmental Noise, Headphone Exposure

**Other:** VO2 Max, Time in Daylight, UV Exposure

## Data Coverage

- **Records:** 6.3M+ measurements
- **Date range:** 2015-10-13 to present
- **Workouts:** 1,435 sessions
- **Sleep sessions:** 40,514 records
- **Activity days:** 1,875 daily summaries

## Resources

### scripts/

- `health_query.py` - Main query tool with Markdown/JSON/FHIR output

### references/

- `schema.md` - Database schema, record type mappings, SQL query templates
- `fhir_mappings.md` - LOINC codes and FHIR R4 templates

## Troubleshooting

**Database not found:**
Ensure `~/data/health.db` exists. Run the import script from `/Users/server/apple_health_export/`:
```bash
python import_health.py --status
```

**No data for date range:**
Check available date range:
```sql
SELECT MIN(start_date), MAX(start_date) FROM health_records;
```

**Outlier values:**
Filter physiologically valid ranges (e.g., heart rate 40-200 bpm):
```sql
WHERE value BETWEEN 40 AND 200
```
