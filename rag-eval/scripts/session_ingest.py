#!/usr/bin/env python3
"""Deterministic session ingest — takes a session ID, emits a compact JSON
signal bundle ready to feed into rag-eval. No LLM calls; pure regex + parse.

Supported session sources (auto-detected by ID prefix and path):
  - Claude Code session transcript (~/.claude/projects/*/<uuid>.jsonl)
  - skill-studio session (~/.skill-studio/sessions/<uuid>/transcript.md)
  - Fathom meeting transcript path (passed explicitly)

Emits to stdout (JSON):
  {
    "session_id": "...",
    "source": "claude-code" | "skill-studio" | "fathom",
    "iterations": [
      {"action": "prompt_change", "text": "...", "ts": "..."},
      {"action": "model_swap", "from": "gpt-4o", "to": "claude-3-5", "ts": "..."},
      {"action": "eval_result", "query": "...", "answer_excerpt": "...", "ts": "..."},
      {"action": "cost_event", "amount_usd": 0.42, "provider": "openrouter", "ts": "..."}
    ],
    "models_tried": ["gpt-4o", "claude-3-5-sonnet"],
    "prompts_tried": ["...short hashes..."],
    "total_cost_usd": 1.73,
    "summary_stats": {"turns": 42, "iterations": 8, "failed_queries": 3}
  }

Usage:
  session_ingest.py <session_id>
  session_ingest.py --path <path-to-transcript>
  session_ingest.py <session_id> --source claude-code
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable


MODEL_PATTERNS = [
    r"\b(gpt-[0-9][a-z0-9\-\.]*)\b",
    r"\b(claude-[0-9a-z\-\.]+)\b",
    r"\b(mistral-[a-z0-9\-\.]+)\b",
    r"\b(llama-?\d[a-z0-9\-\.]*)\b",
    r"\b(gemini-[a-z0-9\-\.]+)\b",
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


def _find_claude_code_session(session_id: str) -> Path | None:
    root = Path.home() / ".claude" / "projects"
    if not root.exists():
        return None
    matches = list(root.rglob(f"{session_id}*.jsonl"))
    return matches[0] if matches else None


def _find_skill_studio_session(session_id: str) -> Path | None:
    root = Path.home() / ".skill-studio" / "sessions"
    for d in root.glob(f"{session_id}*"):
        t = d / "transcript.md"
        if t.exists():
            return t
    return None


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


def extract_signals(path: Path, session_id: str, source: str) -> dict:
    models: set[str] = set()
    prompts_seen: list[str] = []
    iterations: list[dict] = []
    total_cost = 0.0

    for chunk in _iter_text(path):
        for pattern in MODEL_PATTERNS:
            for m in re.findall(pattern, chunk, re.I):
                models.add(m.lower())

        for rx in COST_PATTERNS:
            for m in rx.finditer(chunk):
                try:
                    amt = float(m.group(1))
                    if 0.001 <= amt <= 100:
                        total_cost += amt
                        iterations.append({"action": "cost_event", "amount_usd": amt})
                except (ValueError, IndexError):
                    pass

        for rx in PROMPT_CHANGE_MARKERS:
            if rx.search(chunk):
                h = hashlib.sha1(chunk.encode("utf-8", "ignore")).hexdigest()[:8]
                if h not in prompts_seen:
                    prompts_seen.append(h)
                    iterations.append({"action": "prompt_change", "hash": h})
                break

    return {
        "session_id": session_id,
        "source": source,
        "iterations": iterations,
        "models_tried": sorted(models),
        "prompts_tried": prompts_seen,
        "total_cost_usd": round(total_cost, 4),
        "summary_stats": {
            "iterations": len(iterations),
            "models_tried": len(models),
            "prompt_variants": len(prompts_seen),
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_id", nargs="?")
    ap.add_argument("--path", type=Path, help="Direct path to transcript file")
    ap.add_argument(
        "--source", choices=["claude-code", "skill-studio", "fathom", "auto"], default="auto"
    )
    args = ap.parse_args(argv)

    if args.path:
        path = args.path
        source = args.source if args.source != "auto" else "fathom"
        session_id = args.session_id or path.stem
    elif args.session_id:
        path = _find_claude_code_session(args.session_id) or _find_skill_studio_session(args.session_id)
        if path is None:
            print(f"session not found: {args.session_id}", file=sys.stderr)
            return 1
        source = "claude-code" if ".claude/projects" in str(path) else "skill-studio"
        session_id = args.session_id
    else:
        ap.error("provide session_id or --path")
        return 2

    bundle = extract_signals(path, session_id, source)
    json.dump(bundle, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
