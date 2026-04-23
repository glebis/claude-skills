"""ODI outcome statement validator.

Validates that outcome statements follow the strict ODI format:
[Direction] the [metric] it takes to [action] when [situation]
"""

import re
import sys
import json


DIRECTIONS = {"minimize", "increase", "maintain", "reduce"}
METRICS = {
    "time", "likelihood", "amount", "number", "frequency",
    "cost", "effort", "risk", "errors", "steps",
}


def validate_statement(statement):
    lower = statement.lower().strip()
    issues = []

    has_direction = any(lower.startswith(d) for d in DIRECTIONS)
    if not has_direction:
        issues.append(f"Must start with a direction ({', '.join(sorted(DIRECTIONS))})")

    has_metric = any(m in lower for m in METRICS)
    if not has_metric:
        issues.append(f"Must include a metric ({', '.join(sorted(METRICS))})")

    has_action = "to " in lower and len(lower.split("to ", 1)) > 1
    if not has_action:
        issues.append("Must include 'to [action]'")

    has_context = "when " in lower or "while " in lower or "during " in lower
    if not has_context:
        issues.append("Should include 'when [situation]' for context (optional but recommended)")

    solution_words = ["button", "tool", "app", "dashboard", "plugin", "widget", "modal", "sidebar"]
    describes_solution = any(f" {w} " in f" {lower} " for w in solution_words)
    if describes_solution:
        issues.append("Describes a solution, not an outcome. Rewrite as what the user achieves.")

    return {
        "statement": statement,
        "valid": len([i for i in issues if "optional" not in i]) == 0,
        "issues": issues,
    }


def validate_all(outcomes):
    results = [validate_statement(o["statement"]) for o in outcomes]
    return {
        "results": results,
        "all_valid": all(r["valid"] for r in results),
        "count": len(results),
        "valid_count": sum(1 for r in results if r["valid"]),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_outcome.py <path-to-jtbd.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    outcomes = data.get("odi", {}).get("outcomes", [])
    if not outcomes:
        print("No ODI outcomes found in JSON.")
        sys.exit(0)
    result = validate_all(outcomes)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["all_valid"] else 1)
