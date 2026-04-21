from pathlib import Path


def generate_report(results: list[dict], criteria: dict, fmt: str = "markdown") -> str:
    if fmt == "json":
        import json
        return json.dumps(results, indent=2)
    if fmt == "table":
        return _table(results)
    return _markdown(results, criteria)


def _markdown(results: list[dict], criteria: dict) -> str:
    lines = [f"# Vision Benchmark: {criteria.get('name', 'Results')}\n"]
    criterion_names = list(criteria["criteria"].keys())

    for r in results:
        lines.append(f"## {Path(r['image']).name}\n")
        for model, data in r["judges"].items():
            lines.append(f"### Judge: `{model}`")
            if "error" in data:
                lines.append(f"> Error: {data['error']}\n")
                continue
            lines.append(f"**Weighted total: {data['weighted_total']:.2f} / 5.00**")
            lines.append(f"> {data['overall_impression']}\n")
            lines.append("| Criterion | Score | Reasoning |")
            lines.append("|---|---|---|")
            for name in criterion_names:
                if name in data["scores"]:
                    s = data["scores"][name]
                    lines.append(f"| {name} | {s['score']}/5 | {s['reasoning']} |")
            lines.append("")

    if len(results) > 1:
        lines.append("## Ranking\n")
        lines.append(_ranking_table(results))

    return "\n".join(lines)


def _ranking_table(results: list[dict]) -> str:
    rows = []
    for r in results:
        name = Path(r["image"]).name
        totals = [d["weighted_total"] for d in r["judges"].values() if "weighted_total" in d]
        avg = sum(totals) / len(totals) if totals else 0
        rows.append((name, avg, totals))

    rows.sort(key=lambda x: x[1], reverse=True)
    lines = ["| Rank | Image | Avg Score |", "|---|---|---|"]
    for i, (name, avg, _) in enumerate(rows, 1):
        lines.append(f"| {i} | {name} | {avg:.2f} |")
    return "\n".join(lines)


def _table(results: list[dict]) -> str:
    rows = []
    for r in results:
        name = Path(r["image"]).name
        for model, data in r["judges"].items():
            total = data.get("weighted_total", "ERR")
            rows.append(f"{name:<40} {model:<35} {total}")
    header = f"{'Image':<40} {'Judge':<35} {'Score'}"
    sep = "-" * len(header)
    return "\n".join([header, sep] + sorted(rows, key=lambda x: x.split()[-1], reverse=True))
