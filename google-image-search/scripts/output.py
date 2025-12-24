"""Markdown output generation for image search results."""

from pathlib import Path
from typing import Any, Dict, Iterable, List


def format_alt_text(text: str) -> str:
    """Format text for use as markdown alt text (escape brackets)."""
    return text.replace("[", "(").replace("]", ")")


def emit_summary_markdown(results: Iterable[Dict[str, Any]]) -> str:
    """Generate summary markdown with links and metadata."""
    lines: List[str] = []
    for bundle in results:
        entry = bundle["entry"]
        heading = entry.get("heading") or entry.get("id", "Unnamed")
        description = entry.get("description")
        lines.append(f"### {heading}")
        if description:
            lines.append(description)
        for item in bundle["results"]:
            link = item.get("link")
            title = item.get("title")
            display = item.get("displayLink")
            context = item.get("contextLink")
            mime = item.get("mime")
            detail_parts = [display] if display else []
            if mime:
                detail_parts.append(mime)
            score = item.get("evaluation", {}).get("score")
            if score is not None:
                detail_parts.append(f"score={score}")
            if item.get("finalChoice"):
                detail_parts.append("final")
            detail = ", ".join(detail_parts)
            lines.append(f"- {title or 'Untitled'} ({detail})\n  {link}")
            if context and context != link:
                lines.append(f"  Source page: {context}")
            reasons = item.get("evaluation", {}).get("reasons")
            if reasons:
                lines.append("  Reasons: " + "; ".join(reasons))
            final_reason = item.get("finalChoiceReason")
            if final_reason:
                lines.append(f"  Final pick rationale: {final_reason}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def emit_preview_markdown(
    results: Iterable[Dict[str, Any]],
    *,
    prefer_local: bool = False,
) -> str:
    """Generate preview markdown with inline images."""
    lines: List[str] = []
    for bundle in results:
        entry = bundle["entry"]
        heading = entry.get("heading") or entry.get("id", "Unnamed")
        description = entry.get("description")
        lines.append(f"### {heading}")
        if description:
            lines.append(description)
        for idx, item in enumerate(bundle["results"], start=1):
            raw_title = item.get("title") or f"Image {idx}"
            title = format_alt_text(raw_title)
            image_target = (
                item.get("localPath")
                if prefer_local and item.get("localPath")
                else item.get("link")
            )
            if not image_target:
                continue
            source = item.get("contextLink") or item.get("link")
            lines.append(f"![{title}]({image_target})")
            if source and source != image_target:
                lines.append(f"[Source]({source})")
            score = item.get("evaluation", {}).get("score")
            if score is not None:
                lines.append(f"Score: {score}")
            reasons = item.get("evaluation", {}).get("reasons")
            if reasons:
                lines.append("Reasons: " + "; ".join(reasons))
            final_reason = item.get("finalChoiceReason")
            if final_reason:
                lines.append(f"Final pick: {final_reason}")
            lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def emit_selection_markdown(results: Iterable[Dict[str, Any]]) -> str:
    """Generate markdown showing top-scoring selections."""
    lines: List[str] = []
    for bundle in results:
        entry = bundle["entry"]
        heading = entry.get("heading") or entry.get("id", "Unnamed")
        criteria = entry.get("selectionCriteria")
        selection_count = entry.get("selectionCount", 1)
        lines.append(f"### {heading}")
        if criteria:
            lines.append(f"Criteria: {criteria}")
        sorted_items = sorted(
            bundle["results"],
            key=lambda item: item.get("evaluation", {}).get("score", float("-inf")),
            reverse=True,
        )
        for idx, item in enumerate(sorted_items[:selection_count], start=1):
            title = item.get("title") or f"Image {idx}"
            link = item.get("link")
            score = item.get("evaluation", {}).get("score")
            lines.append(f"{idx}. {title} - score {score}")
            lines.append(f"   Link: {link}")
            local_path = item.get("localPath")
            if local_path:
                lines.append(f"   Local: {local_path}")
            source = item.get("contextLink")
            if source and source != link:
                lines.append(f"   Source: {source}")
            reasons = item.get("evaluation", {}).get("reasons")
            if reasons:
                lines.append(f"   Reasons: {', '.join(reasons)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def emit_final_selection_markdown(results: Iterable[Dict[str, Any]]) -> str:
    """Generate markdown showing only final LLM-selected images."""
    lines: List[str] = []
    for bundle in results:
        entry = bundle["entry"]
        heading = entry.get("heading") or entry.get("id", "Unnamed")
        criteria = entry.get("selectionCriteria") or entry.get("description")
        lines.append(f"### {heading}")
        if criteria:
            lines.append(f"Criteria: {criteria}")
        selection = entry.get("finalSelection")
        if not selection:
            lines.append("No final selection was made.")
            lines.append("")
            continue
        item = selection["item"]
        title = item.get("title") or "Untitled"
        link = item.get("link")
        lines.append(f"Chosen image: {title}")
        lines.append(f"Link: {link}")
        local_path = item.get("localPath")
        if local_path:
            lines.append(f"Local file: {local_path}")
        source = item.get("contextLink")
        if source and source != link:
            lines.append(f"Source page: {source}")
        lines.append(f"LLM explanation: {selection['explanation']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def emit_urls_only(results: Iterable[Dict[str, Any]], best_only: bool = True) -> str:
    """Generate simple list of image URLs."""
    lines: List[str] = []
    for bundle in results:
        entry = bundle["entry"]
        heading = entry.get("heading") or entry.get("id", "Unnamed")
        lines.append(f"# {heading}")

        if best_only:
            # Find final choice or top scored
            best_item = None
            for item in bundle["results"]:
                if item.get("finalChoice"):
                    best_item = item
                    break
            if not best_item and bundle["results"]:
                sorted_items = sorted(
                    bundle["results"],
                    key=lambda x: x.get("evaluation", {}).get("score", float("-inf")),
                    reverse=True,
                )
                best_item = sorted_items[0]
            if best_item:
                lines.append(best_item.get("link", ""))
        else:
            for item in bundle["results"]:
                lines.append(item.get("link", ""))

        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def emit_obsidian_embed(
    item: Dict[str, Any],
    use_local: bool = True,
) -> str:
    """Generate Obsidian-style image embed."""
    if use_local and item.get("localPath"):
        path = Path(item["localPath"])
        filename = path.name
        alt_text = format_alt_text(item.get("title") or "Image")
        return f"![[{filename}|{alt_text}]]"
    else:
        link = item.get("link", "")
        alt_text = format_alt_text(item.get("title") or "Image")
        return f"![{alt_text}]({link})"
