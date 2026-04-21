"""Deterministic transcript ingest — compresses a session transcript into a
small structured bundle before any LLM touches it.

Sources auto-detected:
  - Claude Code session transcript (~/.claude/projects/*/<uuid>.jsonl)
  - skill-studio session (~/.skill-studio/sessions/<uuid>/transcript.md)
  - Arbitrary file via --from-path

Zero LLM calls. Pure regex + parse. The output bundle is meant to fit into
a single LLM prompt for the proposal step.
"""
from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Literal


Source = Literal["claude-code", "skill-studio", "path"]


MODEL_PATTERNS = [
    r"\b(gpt-[0-9][a-z0-9\-\.]*)\b",
    r"\b(claude-[0-9a-z\-\.]+)\b",
    r"\b(mistral-[a-z0-9\-\.]+)\b",
    r"\b(llama-?\d[a-z0-9\-\.]*)\b",
    r"\b(gemini-[a-z0-9\-\.]+)\b",
    r"\b(sonnet-[0-9a-z\-\.]+)\b",
    r"\b(opus-[0-9a-z\-\.]+)\b",
    r"\b(haiku-[0-9a-z\-\.]+)\b",
]
COST_PATTERNS = [
    re.compile(r"\$(\d+\.\d{2,4})\s*(?:spent|cost|charged|USD)?", re.I),
    re.compile(r"cost[:= ]+\$?(\d+\.\d{2,4})", re.I),
    re.compile(r"usage[:= ]+\$?(\d+\.\d{2,4})", re.I),
]
PROMPT_CHANGE_MARKERS = [
    re.compile(r"\b(retrieval|rag|system)\s+prompt[:= ]", re.I),
    re.compile(r"(changed|updated|tweaked)\s+(the\s+)?prompt", re.I),
    re.compile(r"new prompt", re.I),
]
PAIN_MARKERS = [
    re.compile(r"\b(frustrat|annoy|wast|slow|stuck|blocked|hate|struggle|hurt)\w*", re.I),
    re.compile(r"(too (many|much|long|slow)|keeps? (fail|breaking))", re.I),
]


@dataclass
class Bundle:
    session_id: str
    source: Source
    models_tried: list[str] = field(default_factory=list)
    prompt_hashes: list[str] = field(default_factory=list)
    iterations: list[dict] = field(default_factory=list)
    pain_snippets: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    turn_count: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["summary"] = {
            "turns": self.turn_count,
            "iterations": len(self.iterations),
            "models_tried": len(self.models_tried),
            "prompt_variants": len(self.prompt_hashes),
            "total_cost_usd": round(self.total_cost_usd, 4),
            "pain_signals": len(self.pain_snippets),
        }
        return d


def find_claude_code_session(session_id: str) -> Path | None:
    root = Path.home() / ".claude" / "projects"
    if not root.exists():
        return None
    matches = list(root.rglob(f"{session_id}*.jsonl"))
    return matches[0] if matches else None


def find_skill_studio_session(session_id: str) -> Path | None:
    from skill_studio import paths
    for d in paths.session_root().glob(f"{session_id}*"):
        t = d / "transcript.md"
        if t.exists():
            return t
    return None


def resolve_session(session_id: str) -> tuple[Path, Source]:
    """Find a session by id across known sources. Raises if not found."""
    p = find_claude_code_session(session_id)
    if p is not None:
        return p, "claude-code"
    p = find_skill_studio_session(session_id)
    if p is not None:
        return p, "skill-studio"
    raise FileNotFoundError(f"session not found: {session_id}")


def _iter_text(path: Path) -> Iterable[str]:
    if path.suffix == ".jsonl":
        for line in path.read_text().splitlines():
            try:
                obj = json.loads(line)
                msg = obj.get("message") or obj
                content = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            yield block.get("text", "")
                elif isinstance(content, str):
                    yield content
            except json.JSONDecodeError:
                continue
    else:
        yield path.read_text()


def extract(path: Path, session_id: str, source: Source, *, max_pain_snippets: int = 6) -> Bundle:
    b = Bundle(session_id=session_id, source=source)
    seen_models: set[str] = set()
    seen_prompts: set[str] = set()

    for chunk in _iter_text(path):
        b.turn_count += 1

        for pattern in MODEL_PATTERNS:
            for m in re.findall(pattern, chunk, re.I):
                seen_models.add(m.lower())

        # Collect cost matches across patterns, then dedupe by span so a single
        # "$2.45" doesn't get counted once per matching regex.
        cost_spans: dict[tuple[int, int], float] = {}
        for rx in COST_PATTERNS:
            for m in rx.finditer(chunk):
                try:
                    amt = float(m.group(1))
                except (ValueError, IndexError):
                    continue
                if 0.001 <= amt <= 100:
                    span = m.span(1)
                    cost_spans.setdefault(span, amt)
        for amt in cost_spans.values():
            b.total_cost_usd += amt
            b.iterations.append({"action": "cost_event", "amount_usd": amt})

        for rx in PROMPT_CHANGE_MARKERS:
            if rx.search(chunk):
                h = hashlib.sha1(chunk.encode("utf-8", "ignore")).hexdigest()[:8]
                if h not in seen_prompts:
                    seen_prompts.add(h)
                    b.iterations.append({"action": "prompt_change", "hash": h})
                break

        if len(b.pain_snippets) < max_pain_snippets:
            for rx in PAIN_MARKERS:
                m = rx.search(chunk)
                if m:
                    start = max(0, m.start() - 60)
                    end = min(len(chunk), m.end() + 60)
                    snippet = chunk[start:end].strip().replace("\n", " ")
                    if snippet and snippet not in b.pain_snippets:
                        b.pain_snippets.append(snippet)
                        break

    b.models_tried = sorted(seen_models)
    b.prompt_hashes = sorted(seen_prompts)
    return b
