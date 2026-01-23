#!/usr/bin/env python3
"""
Apple Health Database Query Tool
Query health data with multiple output formats: Markdown, JSON, FHIR R4

Usage:
    python health_query.py daily [--date DATE] [--format FORMAT]
    python health_query.py weekly [--weeks N] [--format FORMAT]
    python health_query.py sleep [--days N] [--format FORMAT]
    python health_query.py vitals [--format FORMAT]
    python health_query.py activity [--days N] [--format FORMAT]
    python health_query.py workouts [--days N] [--type TYPE] [--format FORMAT]
    python health_query.py query "SQL" [--format FORMAT]
"""

import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

DB_PATH = Path.home() / "data" / "health.db"

# LOINC codes for FHIR output
LOINC_CODES = {
    "HKQuantityTypeIdentifierHeartRate": ("8867-4", "Heart rate", "/min"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": ("80404-7", "R-R interval.standard deviation", "ms"),
    "HKQuantityTypeIdentifierRestingHeartRate": ("40443-4", "Resting heart rate", "/min"),
    "HKQuantityTypeIdentifierOxygenSaturation": ("59408-5", "Oxygen saturation", "%"),
    "HKQuantityTypeIdentifierStepCount": ("55423-8", "Number of steps", "{steps}"),
    "HKQuantityTypeIdentifierBodyMass": ("29463-7", "Body weight", "kg"),
    "HKQuantityTypeIdentifierRespiratoryRate": ("9279-1", "Respiratory rate", "/min"),
    "HKQuantityTypeIdentifierActiveEnergyBurned": ("41981-2", "Calories burned", "kcal"),
    "HKQuantityTypeIdentifierDistanceWalkingRunning": ("41953-1", "Walking distance", "km"),
    "HKQuantityTypeIdentifierFlightsClimbed": ("93831-6", "Flights of stairs climbed", "{flights}"),
    "HKQuantityTypeIdentifierVO2Max": ("60842-2", "VO2 max", "mL/min/kg"),
}

FRIENDLY_NAMES = {
    "HKQuantityTypeIdentifierHeartRate": "Heart Rate",
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "HRV",
    "HKQuantityTypeIdentifierRestingHeartRate": "Resting HR",
    "HKQuantityTypeIdentifierOxygenSaturation": "Blood Oxygen",
    "HKQuantityTypeIdentifierStepCount": "Steps",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "Active Calories",
    "HKQuantityTypeIdentifierBasalEnergyBurned": "Basal Calories",
    "HKQuantityTypeIdentifierDistanceWalkingRunning": "Distance",
    "HKQuantityTypeIdentifierFlightsClimbed": "Flights Climbed",
    "HKQuantityTypeIdentifierAppleExerciseTime": "Exercise Minutes",
    "HKQuantityTypeIdentifierVO2Max": "VO2 Max",
    "HKQuantityTypeIdentifierRespiratoryRate": "Respiratory Rate",
    "HKQuantityTypeIdentifierBodyMass": "Weight",
}


def get_connection() -> sqlite3.Connection:
    """Connect to health database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# Deduplication Note
# ============================================================
#
# Cumulative metrics (steps, calories, distance) are recorded by BOTH
# iPhone and Apple Watch simultaneously, causing double-counting when
# both sources are summed. Solution: filter to Apple Watch data only
# using "source_name LIKE '%Watch%'" since Watch is more accurate for
# movement tracking (always on wrist).
#
# Also: start_date has timezone offset ("+0100") that SQLite's DATE()
# function doesn't handle, so we use substr(start_date, 1, 10) instead.
#
# ============================================================
# Query Functions
# ============================================================

def daily_summary(date: str = None) -> Dict[str, Any]:
    """Get daily health summary"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()

    result = {"date": date, "metrics": {}}

    # Steps (deduplicated - Apple Watch source only to avoid iPhone double-counting)
    cursor = conn.execute("""
        SELECT SUM(value) as total FROM health_records
        WHERE record_type = 'HKQuantityTypeIdentifierStepCount'
        AND start_date LIKE ?
        AND source_name LIKE '%Watch%'
    """, (f"{date}%",))
    row = cursor.fetchone()
    result["metrics"]["steps"] = int(row["total"]) if row["total"] else 0

    # Active calories (deduplicated - Apple Watch source only)
    cursor = conn.execute("""
        SELECT SUM(value) as total FROM health_records
        WHERE record_type = 'HKQuantityTypeIdentifierActiveEnergyBurned'
        AND start_date LIKE ?
        AND source_name LIKE '%Watch%'
    """, (f"{date}%",))
    row = cursor.fetchone()
    result["metrics"]["active_calories"] = round(row["total"], 1) if row["total"] else 0

    # Heart rate avg/min/max
    cursor = conn.execute("""
        SELECT AVG(value) as avg, MIN(value) as min, MAX(value) as max
        FROM health_records
        WHERE record_type = 'HKQuantityTypeIdentifierHeartRate'
        AND start_date LIKE ?
        AND value BETWEEN 40 AND 200
    """, (f"{date}%",))
    row = cursor.fetchone()
    result["metrics"]["heart_rate"] = {
        "avg": round(row["avg"], 1) if row["avg"] else None,
        "min": int(row["min"]) if row["min"] else None,
        "max": int(row["max"]) if row["max"] else None,
    }

    # Exercise minutes
    cursor = conn.execute("""
        SELECT SUM(value) as total FROM health_records
        WHERE record_type = 'HKQuantityTypeIdentifierAppleExerciseTime'
        AND start_date LIKE ?
    """, (f"{date}%",))
    row = cursor.fetchone()
    result["metrics"]["exercise_minutes"] = int(row["total"]) if row["total"] else 0

    # Distance (deduplicated - Apple Watch source only)
    cursor = conn.execute("""
        SELECT SUM(value) as total FROM health_records
        WHERE record_type = 'HKQuantityTypeIdentifierDistanceWalkingRunning'
        AND start_date LIKE ?
        AND source_name LIKE '%Watch%'
    """, (f"{date}%",))
    row = cursor.fetchone()
    result["metrics"]["distance_km"] = round(row["total"], 2) if row["total"] else 0

    # Activity ring data
    cursor = conn.execute("""
        SELECT * FROM activity_summaries WHERE date = ?
    """, (date,))
    row = cursor.fetchone()
    if row:
        result["activity_rings"] = {
            "move": {"value": row["active_energy_burned"], "goal": row["active_energy_goal"]},
            "exercise": {"value": row["exercise_time_minutes"], "goal": row["exercise_time_goal"]},
            "stand": {"value": row["stand_hours"], "goal": row["stand_hours_goal"]},
        }

    conn.close()
    return result


def weekly_trends(weeks: int = 4) -> Dict[str, Any]:
    """Get weekly trends for key metrics"""
    conn = get_connection()
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)

    result = {"period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", "weeks": []}

    for w in range(weeks):
        week_start = end_date - timedelta(weeks=weeks - w)
        week_end = week_start + timedelta(days=7)

        week_data = {
            "week_of": week_start.strftime("%Y-%m-%d"),
            "metrics": {}
        }

        # Average daily steps (deduplicated - Apple Watch source only)
        # Note: Using substr(start_date,1,10) instead of DATE() because
        # start_date has timezone offset (+0100) that DATE() doesn't handle
        cursor = conn.execute("""
            SELECT AVG(daily_steps) as avg FROM (
                SELECT substr(start_date, 1, 10) as day, SUM(value) as daily_steps
                FROM health_records
                WHERE record_type = 'HKQuantityTypeIdentifierStepCount'
                AND start_date >= ? AND start_date < ?
                AND source_name LIKE '%Watch%'
                GROUP BY day
            )
        """, (week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")))
        row = cursor.fetchone()
        week_data["metrics"]["avg_daily_steps"] = int(row["avg"]) if row["avg"] else 0

        # Average resting heart rate
        cursor = conn.execute("""
            SELECT AVG(value) as avg FROM health_records
            WHERE record_type = 'HKQuantityTypeIdentifierRestingHeartRate'
            AND start_date >= ? AND start_date < ?
        """, (week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")))
        row = cursor.fetchone()
        week_data["metrics"]["avg_resting_hr"] = round(row["avg"], 1) if row["avg"] else None

        # Total exercise minutes
        cursor = conn.execute("""
            SELECT SUM(value) as total FROM health_records
            WHERE record_type = 'HKQuantityTypeIdentifierAppleExerciseTime'
            AND start_date >= ? AND start_date < ?
        """, (week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")))
        row = cursor.fetchone()
        week_data["metrics"]["total_exercise_min"] = int(row["total"]) if row["total"] else 0

        # Workout count
        cursor = conn.execute("""
            SELECT COUNT(*) as cnt FROM workouts
            WHERE start_date >= ? AND start_date < ?
        """, (week_start.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")))
        row = cursor.fetchone()
        week_data["metrics"]["workouts"] = row["cnt"]

        result["weeks"].append(week_data)

    conn.close()
    return result


def sleep_analysis(days: int = 7) -> Dict[str, Any]:
    """Analyze sleep patterns"""
    conn = get_connection()
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    result = {"period_days": days, "nights": [], "summary": {}}

    # Get sleep sessions grouped by night
    cursor = conn.execute("""
        SELECT SUBSTR(start_date, 1, 10) as night, sleep_stage, SUM(duration_minutes) as duration
        FROM sleep_sessions
        WHERE start_date >= ?
        GROUP BY night, sleep_stage
        ORDER BY night DESC
    """, (start_date,))

    nights = {}
    for row in cursor:
        night = row["night"]
        if night not in nights:
            nights[night] = {"date": night, "stages": {}}
        nights[night]["stages"][row["sleep_stage"]] = round(row["duration"], 1)

    # Calculate totals per night
    for night, data in nights.items():
        total = sum(data["stages"].values())
        data["total_minutes"] = round(total, 1)
        data["total_hours"] = round(total / 60, 1)

    result["nights"] = list(nights.values())

    # Summary stats
    if nights:
        all_totals = [n["total_minutes"] for n in nights.values()]
        result["summary"] = {
            "avg_sleep_hours": round(sum(all_totals) / len(all_totals) / 60, 1),
            "nights_tracked": len(nights),
        }

    conn.close()
    return result


def latest_vitals() -> Dict[str, Any]:
    """Get most recent vital readings"""
    conn = get_connection()

    vitals = ["HKQuantityTypeIdentifierHeartRate", "HKQuantityTypeIdentifierOxygenSaturation",
              "HKQuantityTypeIdentifierRestingHeartRate", "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
              "HKQuantityTypeIdentifierRespiratoryRate"]

    result = {"timestamp": datetime.now().isoformat(), "vitals": {}}

    for vital in vitals:
        cursor = conn.execute("""
            SELECT value, unit, start_date FROM health_records
            WHERE record_type = ?
            ORDER BY start_date DESC LIMIT 1
        """, (vital,))
        row = cursor.fetchone()
        if row:
            name = FRIENDLY_NAMES.get(vital, vital)
            result["vitals"][name] = {
                "value": round(row["value"], 1) if row["value"] else None,
                "unit": row["unit"],
                "recorded": row["start_date"][:19]
            }

    conn.close()
    return result


def activity_rings(days: int = 30) -> Dict[str, Any]:
    """Get activity ring completion data"""
    conn = get_connection()
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    cursor = conn.execute("""
        SELECT * FROM activity_summaries
        WHERE date >= ?
        ORDER BY date DESC
    """, (start_date,))

    result = {"period_days": days, "days": [], "summary": {}}

    move_pct = []
    exercise_pct = []
    stand_pct = []

    for row in cursor:
        day = {
            "date": row["date"],
            "move": {"value": row["active_energy_burned"], "goal": row["active_energy_goal"]},
            "exercise": {"value": row["exercise_time_minutes"], "goal": row["exercise_time_goal"]},
            "stand": {"value": row["stand_hours"], "goal": row["stand_hours_goal"]},
        }

        # Calculate percentages
        if row["active_energy_goal"] and row["active_energy_goal"] > 0:
            day["move"]["pct"] = round(row["active_energy_burned"] / row["active_energy_goal"] * 100, 1)
            move_pct.append(day["move"]["pct"])
        if row["exercise_time_goal"] and row["exercise_time_goal"] > 0:
            day["exercise"]["pct"] = round(row["exercise_time_minutes"] / row["exercise_time_goal"] * 100, 1)
            exercise_pct.append(day["exercise"]["pct"])
        if row["stand_hours_goal"] and row["stand_hours_goal"] > 0:
            day["stand"]["pct"] = round(row["stand_hours"] / row["stand_hours_goal"] * 100, 1)
            stand_pct.append(day["stand"]["pct"])

        result["days"].append(day)

    # Summary
    result["summary"] = {
        "days_tracked": len(result["days"]),
        "avg_move_pct": round(sum(move_pct) / len(move_pct), 1) if move_pct else 0,
        "avg_exercise_pct": round(sum(exercise_pct) / len(exercise_pct), 1) if exercise_pct else 0,
        "avg_stand_pct": round(sum(stand_pct) / len(stand_pct), 1) if stand_pct else 0,
        "perfect_days": sum(1 for d in result["days"] if
                          d.get("move", {}).get("pct", 0) >= 100 and
                          d.get("exercise", {}).get("pct", 0) >= 100 and
                          d.get("stand", {}).get("pct", 0) >= 100),
    }

    conn.close()
    return result


def workout_history(days: int = 30, workout_type: str = None) -> Dict[str, Any]:
    """Get workout history"""
    conn = get_connection()
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    query = """
        SELECT workout_type, duration_minutes, total_distance, distance_unit,
               total_energy_burned, energy_unit, start_date, end_date, source_name
        FROM workouts
        WHERE start_date >= ?
    """
    params = [start_date]

    if workout_type:
        query += " AND workout_type LIKE ?"
        params.append(f"%{workout_type}%")

    query += " ORDER BY start_date DESC"

    cursor = conn.execute(query, params)

    result = {"period_days": days, "workouts": [], "summary": {}}

    total_duration = 0
    total_calories = 0
    types = {}

    for row in cursor:
        workout = {
            "type": row["workout_type"].replace("HKWorkoutActivityType", ""),
            "date": row["start_date"][:19],
            "duration_min": round(row["duration_minutes"], 1) if row["duration_minutes"] else 0,
            "calories": round(row["total_energy_burned"], 1) if row["total_energy_burned"] else 0,
        }
        if row["total_distance"]:
            workout["distance"] = round(row["total_distance"], 2)
            workout["distance_unit"] = row["distance_unit"]

        result["workouts"].append(workout)
        total_duration += workout["duration_min"]
        total_calories += workout["calories"]
        types[workout["type"]] = types.get(workout["type"], 0) + 1

    result["summary"] = {
        "total_workouts": len(result["workouts"]),
        "total_duration_min": round(total_duration, 1),
        "total_calories": round(total_calories, 1),
        "by_type": types,
    }

    conn.close()
    return result


def run_query(sql: str) -> List[Dict[str, Any]]:
    """Run custom SQL query"""
    conn = get_connection()
    cursor = conn.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    result = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return result


# ============================================================
# Output Formatters
# ============================================================

def to_markdown(data: Any, title: str = "Health Data") -> str:
    """Format data as Markdown"""
    lines = [f"# {title}", ""]

    if isinstance(data, dict):
        _dict_to_md(data, lines)
    elif isinstance(data, list):
        if data and isinstance(data[0], dict):
            # Table format
            headers = list(data[0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in data:
                lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
        else:
            for item in data:
                lines.append(f"- {item}")
    else:
        lines.append(str(data))

    return "\n".join(lines)


def _dict_to_md(d: Dict, lines: List[str], indent: int = 0):
    """Recursively convert dict to markdown"""
    prefix = "  " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}**{key}:**")
            _dict_to_md(value, lines, indent + 1)
        elif isinstance(value, list):
            lines.append(f"{prefix}**{key}:** ({len(value)} items)")
            if value and isinstance(value[0], dict):
                # Table for list of dicts
                headers = list(value[0].keys())
                lines.append("")
                lines.append(f"{prefix}| " + " | ".join(headers) + " |")
                lines.append(f"{prefix}| " + " | ".join(["---"] * len(headers)) + " |")
                for row in value[:20]:  # Limit to 20 rows
                    lines.append(f"{prefix}| " + " | ".join(str(row.get(h, ""))[:30] for h in headers) + " |")
                if len(value) > 20:
                    lines.append(f"{prefix}*... and {len(value) - 20} more*")
                lines.append("")
        else:
            lines.append(f"{prefix}- **{key}:** {value}")


def to_json(data: Any) -> str:
    """Format data as JSON"""
    return json.dumps(data, indent=2, default=str)


def to_ascii(data: Any, title: str = "Health Data") -> str:
    """Format data as ASCII charts and statistics"""
    lines = [f"{'=' * 60}", f"  {title.upper()}", f"{'=' * 60}", ""]

    if isinstance(data, dict):
        # Handle different data structures
        if "metrics" in data:
            lines.append("METRICS")
            lines.append("-" * 40)
            for key, value in data["metrics"].items():
                if isinstance(value, dict):
                    if "avg" in value:
                        avg_val = value['avg'] if value['avg'] is not None else 'N/A'
                        min_val = value.get('min', 'N/A') if value.get('min') is not None else 'N/A'
                        max_val = value.get('max', 'N/A') if value.get('max') is not None else 'N/A'
                        lines.append(f"  {key:20s} avg:{str(avg_val):>6}  min:{str(min_val):>4}  max:{str(max_val):>4}")
                    else:
                        lines.append(f"  {key:20s} {value.get('value', 'N/A')}")
                else:
                    lines.append(f"  {key:20s} {value:>10}")
            lines.append("")

        if "activity_rings" in data:
            lines.append("ACTIVITY RINGS")
            lines.append("-" * 40)
            for ring, info in data["activity_rings"].items():
                val = info.get("value", 0)
                goal = info.get("goal", 1)
                pct = min(val / goal * 100, 100) if goal else 0
                bar_len = int(pct / 5)  # 20 chars = 100%
                bar = "█" * bar_len + "░" * (20 - bar_len)
                lines.append(f"  {ring:10s} [{bar}] {pct:5.1f}% ({val:.0f}/{goal:.0f})")
            lines.append("")

        if "vitals" in data:
            lines.append("VITALS")
            lines.append("-" * 40)
            for name, info in data["vitals"].items():
                val = info.get("value", "N/A")
                unit = info.get("unit", "")
                lines.append(f"  {name:20s} {val:>8} {unit}")
            lines.append("")

        if "weeks" in data:
            lines.append("WEEKLY TRENDS")
            lines.append("-" * 40)
            # Steps bar chart
            weeks = data["weeks"]
            if weeks:
                max_steps = max(w["metrics"].get("avg_daily_steps", 0) for w in weeks) or 1
                lines.append("  Avg Daily Steps:")
                for w in weeks:
                    steps = w["metrics"].get("avg_daily_steps", 0)
                    bar_len = int(steps / max_steps * 30)
                    bar = "▓" * bar_len
                    lines.append(f"    {w['week_of'][5:10]} {bar} {steps:,}")
                lines.append("")

                # Exercise minutes
                lines.append("  Exercise Minutes:")
                max_ex = max(w["metrics"].get("total_exercise_min", 0) for w in weeks) or 1
                for w in weeks:
                    ex = w["metrics"].get("total_exercise_min", 0)
                    bar_len = int(ex / max_ex * 30)
                    bar = "▓" * bar_len
                    lines.append(f"    {w['week_of'][5:10]} {bar} {ex}")
            lines.append("")

        if "nights" in data:
            lines.append("SLEEP ANALYSIS")
            lines.append("-" * 40)
            nights = data.get("nights", [])[:10]  # Last 10 nights
            if nights:
                for n in nights:
                    hours = n.get("total_hours", 0) or 0
                    bar_len = int(min(hours, 10) * 3)  # 30 chars = 10 hours
                    bar = "█" * bar_len
                    stages = n.get("stages", {})
                    deep = stages.get("Deep", 0) or 0
                    rem = stages.get("REM", 0) or 0
                    date_str = (n.get("date") or "????-??-??")[5:10]
                    lines.append(f"  {date_str} [{bar:30s}] {hours:.1f}h  (D:{deep:.0f}m R:{rem:.0f}m)")
            if "summary" in data:
                lines.append("")
                lines.append(f"  Average: {data['summary'].get('avg_sleep_hours', 0):.1f} hours/night")
            lines.append("")

        if "days" in data and "summary" in data:
            # Activity summary
            s = data["summary"]
            lines.append("SUMMARY")
            lines.append("-" * 40)
            lines.append(f"  Days tracked:    {s.get('days_tracked', 0)}")
            if "avg_move_pct" in s:
                lines.append(f"  Avg Move %:      {s.get('avg_move_pct', 0):.1f}%")
                lines.append(f"  Avg Exercise %:  {s.get('avg_exercise_pct', 0):.1f}%")
                lines.append(f"  Avg Stand %:     {s.get('avg_stand_pct', 0):.1f}%")
                lines.append(f"  Perfect days:    {s.get('perfect_days', 0)}")
            lines.append("")

        if "workouts" in data:
            lines.append("WORKOUTS")
            lines.append("-" * 40)
            workouts = data.get("workouts", [])[:10]
            for w in workouts:
                dur = w.get("duration_min", 0)
                cal = w.get("calories", 0)
                dist = w.get("distance", "")
                dist_str = f"{dist:.1f}km" if dist else ""
                lines.append(f"  {w['date'][5:16]} {w['type']:15s} {dur:5.0f}min {cal:5.0f}cal {dist_str}")
            if "summary" in data:
                s = data["summary"]
                lines.append("")
                lines.append(f"  Total: {s.get('total_workouts', 0)} workouts, {s.get('total_duration_min', 0):.0f} min, {s.get('total_calories', 0):.0f} cal")
            lines.append("")

    elif isinstance(data, list):
        # Table format for query results
        if data and isinstance(data[0], dict):
            headers = list(data[0].keys())
            col_widths = {h: max(len(h), max(len(str(row.get(h, ""))[:20]) for row in data)) for h in headers}

            header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
            lines.append(header_line)
            lines.append("-" * len(header_line))

            for row in data[:30]:
                lines.append(" | ".join(str(row.get(h, ""))[:20].ljust(col_widths[h]) for h in headers))

            if len(data) > 30:
                lines.append(f"... and {len(data) - 30} more rows")

    lines.append("=" * 60)
    return "\n".join(lines)


def to_fhir(data: Any, resource_type: str = "Observation") -> str:
    """Format data as FHIR R4 Bundle"""
    bundle = {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "collection",
        "timestamp": datetime.now().isoformat() + "Z",
        "entry": []
    }

    # Convert data to FHIR observations
    observations = _data_to_fhir_observations(data)

    for obs in observations:
        bundle["entry"].append({
            "fullUrl": f"urn:uuid:{obs['id']}",
            "resource": obs
        })

    return json.dumps(bundle, indent=2)


def _data_to_fhir_observations(data: Any) -> List[Dict]:
    """Convert health data to FHIR Observations"""
    observations = []

    if isinstance(data, dict):
        # Handle different data structures
        if "vitals" in data:
            for name, info in data["vitals"].items():
                obs = _create_fhir_observation(name, info.get("value"), info.get("unit"), info.get("recorded"))
                if obs:
                    observations.append(obs)
        elif "metrics" in data:
            for name, value in data["metrics"].items():
                if isinstance(value, dict):
                    obs = _create_fhir_observation(name, value.get("avg") or value.get("value"), None, data.get("date"))
                else:
                    obs = _create_fhir_observation(name, value, None, data.get("date"))
                if obs:
                    observations.append(obs)

    return observations


def _create_fhir_observation(metric_name: str, value: Any, unit: str = None, timestamp: str = None) -> Optional[Dict]:
    """Create a single FHIR Observation resource"""
    if value is None:
        return None

    # Find LOINC code
    loinc_code = None
    loinc_display = metric_name
    ucum_unit = unit or ""

    for hk_type, (code, display, ucum) in LOINC_CODES.items():
        if metric_name.lower() in display.lower() or metric_name.lower() in hk_type.lower():
            loinc_code = code
            loinc_display = display
            ucum_unit = ucum
            break

    obs = {
        "resourceType": "Observation",
        "id": str(uuid.uuid4()),
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": loinc_code or "unknown",
                "display": loinc_display
            }],
            "text": metric_name
        },
        "effectiveDateTime": timestamp or datetime.now().isoformat(),
        "valueQuantity": {
            "value": value,
            "unit": ucum_unit,
            "system": "http://unitsofmeasure.org",
            "code": ucum_unit
        }
    }

    return obs


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Query Apple Health database")
    parser.add_argument("--format", "-f", choices=["markdown", "json", "fhir", "ascii"], default="markdown",
                       help="Output format")

    subparsers = parser.add_subparsers(dest="command", help="Query command")

    # Daily summary
    daily_p = subparsers.add_parser("daily", help="Daily health summary")
    daily_p.add_argument("--date", "-d", help="Date (YYYY-MM-DD), default: today")

    # Weekly trends
    weekly_p = subparsers.add_parser("weekly", help="Weekly trends")
    weekly_p.add_argument("--weeks", "-w", type=int, default=4, help="Number of weeks")

    # Sleep analysis
    sleep_p = subparsers.add_parser("sleep", help="Sleep analysis")
    sleep_p.add_argument("--days", "-d", type=int, default=7, help="Number of days")

    # Latest vitals
    subparsers.add_parser("vitals", help="Latest vital readings")

    # Activity rings
    activity_p = subparsers.add_parser("activity", help="Activity ring data")
    activity_p.add_argument("--days", "-d", type=int, default=30, help="Number of days")

    # Workouts
    workouts_p = subparsers.add_parser("workouts", help="Workout history")
    workouts_p.add_argument("--days", "-d", type=int, default=30, help="Number of days")
    workouts_p.add_argument("--type", "-t", help="Filter by workout type")

    # Custom query
    query_p = subparsers.add_parser("query", help="Run custom SQL query")
    query_p.add_argument("sql", help="SQL query")

    args = parser.parse_args()

    # Execute command
    if args.command == "daily":
        data = daily_summary(args.date)
        title = f"Daily Summary - {data['date']}"
    elif args.command == "weekly":
        data = weekly_trends(args.weeks)
        title = f"Weekly Trends ({args.weeks} weeks)"
    elif args.command == "sleep":
        data = sleep_analysis(args.days)
        title = f"Sleep Analysis ({args.days} days)"
    elif args.command == "vitals":
        data = latest_vitals()
        title = "Latest Vitals"
    elif args.command == "activity":
        data = activity_rings(args.days)
        title = f"Activity Rings ({args.days} days)"
    elif args.command == "workouts":
        data = workout_history(args.days, args.type)
        title = f"Workout History ({args.days} days)"
    elif args.command == "query":
        data = run_query(args.sql)
        title = "Query Results"
    else:
        parser.print_help()
        return

    # Format output
    if args.format == "markdown":
        print(to_markdown(data, title))
    elif args.format == "json":
        print(to_json(data))
    elif args.format == "fhir":
        print(to_fhir(data))
    elif args.format == "ascii":
        print(to_ascii(data, title))


if __name__ == "__main__":
    main()
