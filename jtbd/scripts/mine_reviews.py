"""Review mining — cluster reviews on three axes: pain, outcome, workaround.

Accepts CSV or JSON input.  Emits a Markdown brief (review-brief.md) and
prints a JSON summary to stdout.

See references/review_taxonomy.md for axis vocabularies and cluster labels.
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# ── Keyword maps ────────────────────────────────────────────────────────

PAIN_KEYWORDS = {
    "time_cost": [
        "takes forever", "slow", "waste", "wasted", "wasting", "too long",
        "hours", "all day", "wait", "waiting", "delays", "delayed",
    ],
    "quality_cost": [
        "wrong", "error", "errors", "unreliable", "inaccurate", "buggy",
        "broken", "glitch", "incorrect", "mistake", "mistakes", "fails",
    ],
    "social_cost": [
        "embarrassing", "my boss", "my manager", "look bad", "looks bad",
        "unprofessional", "in front of", "colleagues",
    ],
    "cognitive_cost": [
        "confusing", "can't figure", "hard to understand", "complicated",
        "overwhelming", "unintuitive", "not intuitive", "steep learning",
        "learning curve", "too complex",
    ],
    "money_cost": [
        "expensive", "not worth", "pricey", "overpriced", "costs too much",
        "too much money", "waste of money", "rip off", "ripoff",
    ],
    "trust_cost": [
        "lost data", "lost my data", "can't count on", "can't trust",
        "broke", "crashed", "crash", "unreliable", "data loss",
        "disappeared", "went down",
    ],
}

OUTCOME_KEYWORDS = {
    "speed": [
        "faster", "quicker", "quick", "instant", "rapid", "save time",
        "saves time", "time-saving", "efficient", "efficiency",
    ],
    "accuracy": [
        "accurate", "correct", "reliable", "precise", "precision",
        "dependable", "consistent", "no errors", "error-free",
    ],
    "control": [
        "control", "customize", "customizable", "configure", "configurable",
        "flexible", "flexibility", "options", "settings", "adjust",
    ],
    "simplicity": [
        "simple", "easy", "easier", "straightforward", "intuitive",
        "user-friendly", "user friendly", "no-brainer", "clean",
        "minimal", "just works",
    ],
    "trust": [
        "predictable", "no surprises", "dependable", "stable", "solid",
        "reliable", "always works", "never fails", "count on",
    ],
    "status": [
        "professional", "impressive", "looks great", "polished",
        "beautiful", "sleek", "modern", "cutting-edge", "premium",
    ],
}

WORKAROUND_KEYWORDS = {
    "manual": [
        "spreadsheet", "manually", "by hand", "pen and paper",
        "excel", "google sheets", "paper", "handwritten", "notepad",
        "sticky notes", "whiteboard",
    ],
    "abandoned": [
        "gave up", "stopped", "quit", "abandoned", "don't bother",
        "stopped trying", "no longer", "moved on",
    ],
    "hybrid": [
        "combine", "alongside", "in addition to", "supplement",
        "workaround", "work around", "plus", "together with",
    ],
}

# Generic phrases that appear in any business category (hygiene factors).
GENERIC_PRAISE = [
    "great customer service", "easy to use", "fast delivery",
    "friendly staff", "good value", "highly recommend",
    "love this product", "works great", "very helpful",
    "excellent service", "best ever", "amazing product",
    "five stars", "5 stars", "would recommend",
]


# ── Helpers ──────────────────────────────────────────────────────────────

def _normalize(text):
    """Lowercase and collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower().strip())


def _match_axis(text, keyword_map):
    """Return the best-matching axis label or None.

    If multiple labels match, pick the one with the most keyword hits.
    """
    text_norm = _normalize(text)
    scores = {}
    for label, keywords in keyword_map.items():
        hits = sum(1 for kw in keywords if kw in text_norm)
        if hits > 0:
            scores[label] = hits
    if not scores:
        return None
    return max(scores, key=scores.get)


def _detect_competitor(text):
    """Very basic competitor mention detection.

    Returns competitor name if found, else None.  Looks for patterns like
    "switched to X", "using X instead", "moved to X".
    """
    text_norm = _normalize(text)
    patterns = [
        r"switch(?:ed)? to (\w+)",
        r"moved? to (\w+)",
        r"using (\w+) instead",
        r"went (?:back )?to (\w+)",
        r"prefer (\w+)",
    ]
    for pat in patterns:
        m = re.search(pat, text_norm)
        if m:
            candidate = m.group(1)
            # Filter out generic words that aren't tool names.
            if candidate not in {"it", "the", "a", "an", "this", "that",
                                 "them", "something", "nothing", "another"}:
                return candidate
    return None


def _is_generic(text):
    """Return True if the review text matches a generic praise pattern."""
    text_norm = _normalize(text)
    return any(phrase in text_norm for phrase in GENERIC_PRAISE)


# ── Core pipeline ────────────────────────────────────────────────────────

def parse_input(filepath):
    """Parse CSV or JSON file.  Returns list of dicts with at least 'text'."""
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON input must be an array of objects.")
        for item in data:
            if "text" not in item:
                raise ValueError("Each JSON object must have a 'text' field.")
        return data

    # Default: treat as CSV.
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "text" not in (reader.fieldnames or []):
            raise ValueError("CSV must have a 'text' column.")
        for row in reader:
            rows.append(row)
    return rows


def classify_review(review_text):
    """Classify a single review on all three axes.

    Returns dict: {pain, outcome, workaround, competitor, generic}.
    """
    pain = _match_axis(review_text, PAIN_KEYWORDS)
    outcome = _match_axis(review_text, OUTCOME_KEYWORDS)

    # Workaround: check competitor first, then keyword map.
    competitor = _detect_competitor(review_text)
    if competitor:
        workaround = "competitor"
    else:
        workaround = _match_axis(review_text, WORKAROUND_KEYWORDS) or "unknown"

    return {
        "pain": pain,
        "outcome": outcome,
        "workaround": workaround,
        "competitor": competitor,
        "generic": _is_generic(review_text),
    }


def cluster_reviews(reviews):
    """Cluster a list of review dicts.

    Returns (clusters, classified_reviews) where clusters is a dict keyed
    by (pain, outcome) tuples with metadata.
    """
    classified = []
    cluster_map = defaultdict(list)

    for review in reviews:
        text = review.get("text", "")
        cls = classify_review(text)
        cls["text"] = text
        cls["rating"] = review.get("rating")
        cls["date"] = review.get("date")
        cls["source"] = review.get("source")
        cls["author"] = review.get("author")
        classified.append(cls)

        key = (cls["pain"], cls["outcome"])
        cluster_map[key].append(cls)

    # Build cluster summaries, sorted by volume descending.
    clusters = []
    for (pain, outcome), members in sorted(
        cluster_map.items(), key=lambda kv: -len(kv[1])
    ):
        # Determine dominant workaround.
        wa_counts = Counter(m["workaround"] for m in members)
        dominant_wa = wa_counts.most_common(1)[0][0]

        # Competitor name if applicable.
        competitors = [m["competitor"] for m in members if m["competitor"]]
        comp_name = Counter(competitors).most_common(1)[0][0] if competitors else None

        # Confidence based on convergence threshold.
        count = len(members)
        if count >= 3:
            sources = set(m["source"] for m in members if m.get("source"))
            confidence = "high" if len(sources) > 1 else "medium"
        else:
            confidence = "low"

        # Check if cluster is mostly generic.
        generic_count = sum(1 for m in members if m["generic"])
        is_generic = generic_count > len(members) / 2

        # Build label.
        pain_label = pain or "mixed_pain"
        outcome_label = outcome or "unclear_outcome"
        wa_label = dominant_wa
        if comp_name and wa_label == "competitor":
            wa_label = f"competitor ({comp_name})"

        label = f"{pain_label} — users want {outcome_label} but currently {wa_label}"

        # Representative quotes (up to 3).
        quotes = [m["text"] for m in members[:3]]

        clusters.append({
            "pain": pain,
            "outcome": outcome,
            "workaround": dominant_wa,
            "competitor": comp_name,
            "label": label,
            "count": count,
            "confidence": confidence,
            "generic": is_generic,
            "quotes": quotes,
        })

    return clusters, classified


def render_brief(clusters, total_count, source_name, output_dir):
    """Render review-brief.md from clusters into output_dir."""
    template_path = Path(__file__).resolve().parent.parent / "templates" / "review-brief.md"

    date_str = datetime.now().strftime("%Y-%m-%d")

    # Filter out generic clusters for the top-3 ranking.
    featured = [c for c in clusters if not c["generic"]]
    # If everything is generic, show them anyway.
    if not featured:
        featured = clusters
    top3 = featured[:3]

    lines = []
    lines.append(f"# Review Brief — {source_name}")
    lines.append("")
    lines.append(f"**Reviews parsed:** {total_count}")
    lines.append(f"**Source:** {source_name}")
    lines.append(f"**Date:** {date_str}")
    lines.append("")
    lines.append("## Top 3 clusters (ranked by volume)")
    lines.append("")

    for rank, cluster in enumerate(top3, 1):
        pct = round(cluster["count"] / total_count * 100) if total_count else 0
        lines.append(f"### {rank}. {cluster['label']} — {cluster['count']} reviews ({pct}%)")
        lines.append("")
        lines.append("**Representative quotes:**")
        for q in cluster["quotes"]:
            lines.append(f'- "{q}"')
        lines.append("")
        lines.append("**Hypothesized job:**")
        lines.append(f"When [situation], I want to [{cluster['outcome'] or '...'}], so I can [outcome].")
        lines.append("")
        lines.append(f"**Confidence:** {cluster['confidence']}")
        lines.append("")

    # Underserved forces.
    lines.append("## Underserved forces (interview priorities)")
    lines.append("")
    lines.append("Reviews are systematically weak on these two Switch forces. Probe them in the interview.")
    lines.append("")
    lines.append('- **Habit:** reviewers rarely describe the muscle memory / workflow inertia that keeps them with the old. Ask: "What have you been using, even if it\'s duct tape and a spreadsheet?"')
    lines.append('- **Anxiety:** only unhappy switchers leave reviews — happy stayers are invisible. Ask at least one real user what worries them about switching.')
    lines.append("")

    # Conflicts.
    lines.append("## Conflicts / tensions")
    lines.append("")
    conflict_pairs = _find_conflicts(clusters)
    if conflict_pairs:
        for conflict in conflict_pairs:
            lines.append(f"- {conflict}")
    else:
        lines.append("- No obvious conflicts detected in this review set.")
    lines.append("")

    # Interview prep.
    lines.append("## Interview prep")
    lines.append("")
    if total_count >= 30:
        lines.append("Given these clusters, skip these questions in the interview (reviews already answered them):")
        lines.append("")
        if top3:
            lines.append(f"- [ ] Pain around {top3[0]['pain'] or 'top cluster'} is well-documented")
        if len(top3) > 1:
            lines.append(f"- [ ] Desired outcome of {top3[1]['outcome'] or 'second cluster'} is clear")
    else:
        lines.append("Volume < 30 — treat clusters as hypotheses. Run the full interview.")
    lines.append("")
    lines.append("Emphasize these instead:")
    lines.append("")
    lines.append("- [ ] Walk through one specific switching moment")
    lines.append("- [ ] Probe all four Switch forces (especially habit + anxiety)")
    lines.append("- [ ] Push for measurable outcomes")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Next step:** run `/jtbd` in Interview mode, using this brief as pre-seed.")
    lines.append("")

    out_path = Path(output_dir) / "review-brief.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)


def _find_conflicts(clusters):
    """Detect clusters that contradict each other."""
    conflicts = []
    # Conflict: same pain, opposite desired outcomes.
    by_pain = defaultdict(list)
    for c in clusters:
        if c["pain"]:
            by_pain[c["pain"]].append(c)
    for pain, group in by_pain.items():
        outcomes = set(c["outcome"] for c in group if c["outcome"])
        if "simplicity" in outcomes and "control" in outcomes:
            conflicts.append(
                f"Tension in {pain}: some users want simplicity, others want control."
            )
        if "speed" in outcomes and "accuracy" in outcomes:
            conflicts.append(
                f"Tension in {pain}: some users want speed, others want accuracy."
            )
    return conflicts


def build_summary(clusters, total_count):
    """Build a JSON-serializable summary dict."""
    return {
        "total_reviews": total_count,
        "cluster_count": len(clusters),
        "clusters": [
            {
                "label": c["label"],
                "count": c["count"],
                "confidence": c["confidence"],
                "generic": c["generic"],
            }
            for c in clusters
        ],
    }


# ── CLI ──────────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Mine product reviews and cluster on pain/outcome/workaround axes."
    )
    parser.add_argument("input", help="Path to CSV or JSON file of reviews.")
    parser.add_argument(
        "-o", "--output-dir", default=".",
        help="Directory to write review-brief.md (default: current dir).",
    )
    parser.add_argument(
        "--source-name", default=None,
        help="Human-readable name for the review source (default: filename).",
    )
    args = parser.parse_args(argv)

    reviews = parse_input(args.input)
    clusters, classified = cluster_reviews(reviews)
    total = len(reviews)
    source = args.source_name or Path(args.input).stem

    brief_path = render_brief(clusters, total, source, args.output_dir)
    summary = build_summary(clusters, total)
    summary["brief_path"] = brief_path

    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
