# Apple Health Database Schema

Database location: `~/data/health.db`

## Tables

### health_records

Main table containing 6.3M+ health measurements across 43 types.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| record_type | TEXT | HK identifier (e.g., HKQuantityTypeIdentifierHeartRate) |
| value | REAL | Numeric value |
| value_text | TEXT | String value (for categories) |
| unit | TEXT | Unit of measurement |
| start_date | TEXT | ISO timestamp with timezone |
| end_date | TEXT | End timestamp (if applicable) |
| start_ts | INTEGER | Unix timestamp for fast queries |
| end_ts | INTEGER | End unix timestamp |
| source_id | INTEGER | FK to sources table |
| source_name | TEXT | Device/app name |
| device | TEXT | Raw device string |
| creation_date | TEXT | When record was created |

**Indexes:** `idx_records_type`, `idx_records_start_date`, `idx_records_start_ts`, `idx_records_type_date`, `idx_records_type_ts`

### workouts

Exercise sessions with metadata.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| workout_type | TEXT | HKWorkoutActivityType* |
| duration_minutes | REAL | Duration |
| total_distance | REAL | Distance traveled |
| distance_unit | TEXT | km, mi, etc. |
| total_energy_burned | REAL | Calories |
| energy_unit | TEXT | kcal |
| start_date | TEXT | Start timestamp |
| end_date | TEXT | End timestamp |
| source_name | TEXT | Recording app |
| route_file | TEXT | GPX file reference |

### sleep_sessions

Sleep analysis with stages.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| start_date | TEXT | Sleep start |
| end_date | TEXT | Sleep end |
| duration_minutes | REAL | Duration |
| sleep_stage | TEXT | InBed, Asleep, Awake, Core, Deep, REM |
| source_name | TEXT | Tracking source |

### activity_summaries

Daily activity ring data.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| date | TEXT | YYYY-MM-DD |
| active_energy_burned | REAL | Move ring calories |
| active_energy_goal | REAL | Move goal |
| exercise_time_minutes | REAL | Exercise ring |
| exercise_time_goal | REAL | Exercise goal (usually 30) |
| stand_hours | INTEGER | Stand ring |
| stand_hours_goal | INTEGER | Stand goal (usually 12) |

### sources

Device/app metadata (normalized).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | App/device name |
| version | TEXT | Software version |
| device_name | TEXT | e.g., "Apple Watch" |
| device_model | TEXT | e.g., "Watch6,1" |

---

## Record Type Mappings

| HK Identifier | Friendly Name | Unit |
|--------------|---------------|------|
| HKQuantityTypeIdentifierHeartRate | Heart Rate | count/min |
| HKQuantityTypeIdentifierHeartRateVariabilitySDNN | HRV | ms |
| HKQuantityTypeIdentifierRestingHeartRate | Resting HR | count/min |
| HKQuantityTypeIdentifierOxygenSaturation | Blood Oxygen | % |
| HKQuantityTypeIdentifierStepCount | Steps | count |
| HKQuantityTypeIdentifierDistanceWalkingRunning | Distance | km |
| HKQuantityTypeIdentifierActiveEnergyBurned | Active Calories | kcal |
| HKQuantityTypeIdentifierBasalEnergyBurned | Basal Calories | kcal |
| HKQuantityTypeIdentifierFlightsClimbed | Flights | count |
| HKQuantityTypeIdentifierAppleExerciseTime | Exercise Time | min |
| HKQuantityTypeIdentifierAppleStandTime | Stand Time | min |
| HKQuantityTypeIdentifierVO2Max | VO2 Max | mL/min·kg |
| HKQuantityTypeIdentifierRespiratoryRate | Respiratory Rate | count/min |
| HKQuantityTypeIdentifierBodyMass | Weight | kg |
| HKQuantityTypeIdentifierWalkingSpeed | Walking Speed | km/hr |
| HKQuantityTypeIdentifierWalkingStepLength | Step Length | cm |
| HKQuantityTypeIdentifierEnvironmentalAudioExposure | Noise Level | dBASPL |
| HKQuantityTypeIdentifierHeadphoneAudioExposure | Headphone Level | dBASPL |
| HKQuantityTypeIdentifierTimeInDaylight | Daylight Time | min |

---

## SQL Query Templates

### Time-Based Queries

**Daily totals for a metric:**
```sql
SELECT DATE(start_date) as day, SUM(value) as total
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierStepCount'
AND start_date >= '2025-11-01'
GROUP BY day
ORDER BY day;
```

**Hourly averages (circadian pattern):**
```sql
SELECT strftime('%H', start_date) as hour, AVG(value) as avg
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierHeartRate'
AND value BETWEEN 40 AND 200
GROUP BY hour
ORDER BY hour;
```

**Weekly aggregation:**
```sql
SELECT strftime('%Y-W%W', start_date) as week,
       AVG(value) as avg, MIN(value) as min, MAX(value) as max
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierHeartRate'
GROUP BY week
ORDER BY week DESC
LIMIT 12;
```

**Monthly trends:**
```sql
SELECT strftime('%Y-%m', start_date) as month,
       AVG(value) as avg, COUNT(*) as readings
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierRestingHeartRate'
GROUP BY month
ORDER BY month DESC;
```

### Latest Values

**Most recent reading per metric type:**
```sql
SELECT record_type, value, unit, start_date
FROM health_records
WHERE id IN (
    SELECT MAX(id) FROM health_records
    WHERE record_type IN (
        'HKQuantityTypeIdentifierHeartRate',
        'HKQuantityTypeIdentifierOxygenSaturation',
        'HKQuantityTypeIdentifierRestingHeartRate'
    )
    GROUP BY record_type
);
```

**Last N readings:**
```sql
SELECT value, start_date
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierHeartRate'
ORDER BY start_date DESC
LIMIT 10;
```

### Sleep Queries

**Sleep duration by night:**
```sql
SELECT DATE(start_date) as night,
       SUM(duration_minutes) as total_min,
       ROUND(SUM(duration_minutes)/60.0, 1) as hours
FROM sleep_sessions
WHERE sleep_stage IN ('Asleep', 'Core', 'Deep', 'REM')
GROUP BY night
ORDER BY night DESC
LIMIT 14;
```

**Sleep stage breakdown:**
```sql
SELECT sleep_stage,
       COUNT(*) as sessions,
       ROUND(AVG(duration_minutes), 1) as avg_duration
FROM sleep_sessions
WHERE start_date >= DATE('now', '-30 days')
GROUP BY sleep_stage;
```

**Best sleep nights (most deep+REM):**
```sql
SELECT DATE(start_date) as night,
       SUM(CASE WHEN sleep_stage IN ('Deep', 'REM') THEN duration_minutes ELSE 0 END) as quality_min
FROM sleep_sessions
WHERE start_date >= DATE('now', '-30 days')
GROUP BY night
ORDER BY quality_min DESC
LIMIT 5;
```

### Workout Queries

**Workout summary by type:**
```sql
SELECT
    REPLACE(workout_type, 'HKWorkoutActivityType', '') as type,
    COUNT(*) as sessions,
    ROUND(SUM(duration_minutes), 0) as total_min,
    ROUND(SUM(total_energy_burned), 0) as total_cal
FROM workouts
WHERE start_date >= DATE('now', '-90 days')
GROUP BY type
ORDER BY sessions DESC;
```

**Workouts with distance:**
```sql
SELECT
    REPLACE(workout_type, 'HKWorkoutActivityType', '') as type,
    DATE(start_date) as date,
    ROUND(duration_minutes, 1) as minutes,
    ROUND(total_distance, 2) as distance_km,
    ROUND(total_energy_burned, 0) as calories
FROM workouts
WHERE total_distance > 0
ORDER BY start_date DESC
LIMIT 20;
```

### Activity Ring Queries

**Ring completion rates:**
```sql
SELECT
    COUNT(*) as days,
    ROUND(AVG(CASE WHEN active_energy_burned >= active_energy_goal THEN 100.0 ELSE active_energy_burned*100.0/active_energy_goal END), 1) as move_pct,
    ROUND(AVG(CASE WHEN exercise_time_minutes >= exercise_time_goal THEN 100.0 ELSE exercise_time_minutes*100.0/exercise_time_goal END), 1) as exercise_pct,
    ROUND(AVG(CASE WHEN stand_hours >= stand_hours_goal THEN 100.0 ELSE stand_hours*100.0/stand_hours_goal END), 1) as stand_pct
FROM activity_summaries
WHERE date >= DATE('now', '-30 days');
```

**Perfect ring days:**
```sql
SELECT date, active_energy_burned, exercise_time_minutes, stand_hours
FROM activity_summaries
WHERE active_energy_burned >= active_energy_goal
AND exercise_time_minutes >= exercise_time_goal
AND stand_hours >= stand_hours_goal
ORDER BY date DESC;
```

### Correlation Queries

**Heart rate vs. exercise correlation:**
```sql
SELECT
    a.date,
    a.exercise_time_minutes,
    ROUND(AVG(h.value), 1) as avg_hr
FROM activity_summaries a
JOIN health_records h ON DATE(h.start_date) = a.date
WHERE h.record_type = 'HKQuantityTypeIdentifierRestingHeartRate'
AND a.date >= DATE('now', '-90 days')
GROUP BY a.date;
```

**Sleep vs. next day HRV:**
```sql
SELECT
    s.night,
    s.sleep_hours,
    ROUND(AVG(h.value), 1) as next_day_hrv
FROM (
    SELECT DATE(start_date) as night, SUM(duration_minutes)/60.0 as sleep_hours
    FROM sleep_sessions
    WHERE sleep_stage IN ('Asleep', 'Core', 'Deep', 'REM')
    GROUP BY night
) s
JOIN health_records h ON DATE(h.start_date) = DATE(s.night, '+1 day')
WHERE h.record_type = 'HKQuantityTypeIdentifierHeartRateVariabilitySDNN'
GROUP BY s.night
ORDER BY s.night DESC
LIMIT 30;
```

### Statistical Queries

**Percentiles:**
```sql
SELECT
    MIN(value) as min,
    MAX(value) as max,
    AVG(value) as mean,
    (SELECT value FROM health_records
     WHERE record_type = 'HKQuantityTypeIdentifierHeartRate'
     AND value BETWEEN 40 AND 200
     ORDER BY value LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM health_records WHERE record_type = 'HKQuantityTypeIdentifierHeartRate')) as median
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierHeartRate'
AND value BETWEEN 40 AND 200;
```

**Day-of-week patterns:**
```sql
SELECT
    CASE strftime('%w', start_date)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END as day_name,
    ROUND(AVG(value), 1) as avg
FROM health_records
WHERE record_type = 'HKQuantityTypeIdentifierHeartRate'
AND value BETWEEN 40 AND 200
GROUP BY strftime('%w', start_date)
ORDER BY strftime('%w', start_date);
```

---

## Quick Reference

**Database connection:**
```bash
sqlite3 ~/data/health.db
```

**List all record types:**
```sql
SELECT DISTINCT record_type, COUNT(*) as cnt
FROM health_records
GROUP BY record_type
ORDER BY cnt DESC;
```

**Date range:**
```sql
SELECT MIN(start_date), MAX(start_date) FROM health_records;
```

**Table sizes:**
```sql
SELECT 'health_records' as tbl, COUNT(*) FROM health_records
UNION SELECT 'workouts', COUNT(*) FROM workouts
UNION SELECT 'sleep_sessions', COUNT(*) FROM sleep_sessions
UNION SELECT 'activity_summaries', COUNT(*) FROM activity_summaries;
```
