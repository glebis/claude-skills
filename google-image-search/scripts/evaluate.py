"""Keyword-based scoring for image search results."""

from typing import Any, Dict, Iterable, List


def keyword_match(text: str, keywords: Iterable[str]) -> Dict[str, bool]:
    """Check which keywords are present in text."""
    lowered = text.lower()
    return {kw: (kw.lower() in lowered) for kw in keywords}


def evaluate_item(item: Dict[str, Any], entry: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single image result against entry criteria."""
    score = 0
    reasons: List[str] = []

    # Combine text fields for keyword matching
    combined_text = " ".join(
        filter(
            None,
            [
                item.get("title"),
                item.get("displayLink"),
                item.get("contextLink"),
                entry.get("description"),
            ],
        )
    )

    # Required terms
    required = entry.get("requiredTerms", [])
    if required:
        matches = keyword_match(combined_text, required)
        missing = [kw for kw, ok in matches.items() if not ok]
        if missing:
            score -= 80
            reasons.append(f"missing required: {', '.join(missing)}")
        else:
            score += 30
            reasons.append("contains all required terms")

    # Optional terms
    optional = entry.get("optionalTerms", [])
    if optional:
        matches = keyword_match(combined_text, optional)
        present = [kw for kw, ok in matches.items() if ok]
        if present:
            boost = 5 * len(present)
            score += boost
            reasons.append(f"optional terms: {', '.join(present)} (+{boost})")

    # Exclude terms
    exclude = entry.get("excludeTerms", [])
    if exclude:
        matches = keyword_match(combined_text, exclude)
        present = [kw for kw, ok in matches.items() if ok]
        if present:
            penalty = 50 * len(present)
            score -= penalty
            reasons.append(f"excluded terms present: {', '.join(present)} (-{penalty})")

    # Preferred hosts
    host = item.get("host")
    preferred_hosts: List[str] = [
        host_name.lower() for host_name in entry.get("preferredHosts", [])
    ]
    if host and preferred_hosts:
        if any(host_name in host for host_name in preferred_hosts):
            score += 25
            reasons.append(f"trusted host: {host}")
        else:
            score -= 5
            reasons.append(f"unlisted host: {host}")

    # MIME type preference
    mime = item.get("mime") or item.get("fileFormat")
    if mime:
        if "jpeg" in mime.lower() or "png" in mime.lower():
            score += 5
            reasons.append("preferred mime")
        elif "gif" in mime.lower():
            score -= 10
            reasons.append("gif penalized")

    # Resolution scoring
    width = item.get("width") or 0
    height = item.get("height") or 0
    if width and height:
        if width >= 600 and height >= 400:
            score += 10
            reasons.append("high resolution")
        elif width < 300 or height < 300:
            score -= 10
            reasons.append("low resolution")

    # File size scoring
    byte_size = item.get("byteSize") or 0
    if byte_size and byte_size < 20_000:
        score -= 5
        reasons.append("small file size")

    return {"score": score, "reasons": reasons}


def evaluate_results(results: Iterable[Dict[str, Any]]) -> None:
    """Evaluate all results in place."""
    for bundle in results:
        entry = bundle["entry"]
        for item in bundle["results"]:
            item["evaluation"] = evaluate_item(item, entry)


def get_top_candidates(
    bundle: Dict[str, Any],
    count: int = 2,
) -> List[Dict[str, Any]]:
    """Get top N candidates by score from a bundle."""
    sorted_items = sorted(
        bundle["results"],
        key=lambda item: item.get("evaluation", {}).get("score", float("-inf")),
        reverse=True,
    )
    return sorted_items[:count]
