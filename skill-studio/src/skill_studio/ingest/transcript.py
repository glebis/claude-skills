"""Deterministic transcript ingest — compresses a session transcript into a
small structured bundle before any LLM touches it.

Sources auto-detected:
  - Claude Code session transcript (~/.claude/projects/*/<uuid>.jsonl)
  - skill-studio session (~/.skill-studio/sessions/<uuid>/transcript.md)
  - Arbitrary file via --from-path
  - Current session via CLAUDE_CODE_SESSION_ID env var

Zero LLM calls. Pure regex + parse. The output bundle is meant to fit into
a single LLM prompt for the proposal step.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from collections import Counter
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
class AgentCall:
    description: str
    subagent_type: str | None = None
    prompt_snippet: str = ""

    def to_dict(self) -> dict:
        d = {"description": self.description}
        if self.subagent_type:
            d["subagent_type"] = self.subagent_type
        if self.prompt_snippet:
            d["prompt_snippet"] = self.prompt_snippet
        return d


@dataclass
class SkillCall:
    skill: str
    args: str | None = None

    def to_dict(self) -> dict:
        d = {"skill": self.skill}
        if self.args:
            d["args"] = self.args
        return d


@dataclass
class WorkflowStep:
    tool: str
    description: str = ""

    def to_dict(self) -> dict:
        d = {"tool": self.tool}
        if self.description:
            d["description"] = self.description
        return d


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
    agents: list[AgentCall] = field(default_factory=list)
    skills: list[SkillCall] = field(default_factory=list)
    tool_sequence: list[WorkflowStep] = field(default_factory=list)
    tool_frequency: dict[str, int] = field(default_factory=dict)
    workflow_patterns: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["agents"] = [a.to_dict() for a in self.agents]
        d["skills"] = [s.to_dict() for s in self.skills]
        d["tool_sequence"] = [w.to_dict() for w in self.tool_sequence]
        d["summary"] = {
            "turns": self.turn_count,
            "iterations": len(self.iterations),
            "models_tried": len(self.models_tried),
            "prompt_variants": len(self.prompt_hashes),
            "total_cost_usd": round(self.total_cost_usd, 4),
            "pain_signals": len(self.pain_snippets),
            "agent_calls": len(self.agents),
            "skill_calls": len(self.skills),
            "unique_tools": len(self.tool_frequency),
            "workflow_patterns": len(self.workflow_patterns),
        }
        return d


def get_current_session_id() -> str | None:
    return os.environ.get("CLAUDE_CODE_SESSION_ID")


def find_claude_code_session(session_id: str, project: str | None = None) -> Path | None:
    root = Path.home() / ".claude" / "projects"
    if not root.exists():
        return None
    if project:
        project_dir = root / project
        if project_dir.exists():
            matches = list(project_dir.glob(f"{session_id}*.jsonl"))
            return matches[0] if matches else None
    matches = list(root.rglob(f"{session_id}*.jsonl"))
    return matches[0] if matches else None


def list_claude_code_sessions(project: str | None = None, limit: int = 20) -> list[dict]:
    root = Path.home() / ".claude" / "projects"
    if not root.exists():
        return []
    if project:
        dirs = [root / project]
    else:
        dirs = [d for d in root.iterdir() if d.is_dir()]
    results = []
    for d in dirs:
        for f in d.glob("*.jsonl"):
            sid = f.stem
            title = _read_session_title(f)
            results.append({
                "session_id": sid,
                "project": d.name,
                "modified": f.stat().st_mtime,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "title": title,
            })
    results.sort(key=lambda r: r["modified"], reverse=True)
    return results[:limit]


def _read_session_title(path: Path) -> str:
    for line in path.open():
        try:
            obj = json.loads(line)
            if obj.get("type") == "ai-title":
                return obj.get("title", "")
        except json.JSONDecodeError:
            continue
    return ""


def find_skill_studio_session(session_id: str) -> Path | None:
    from skill_studio import paths
    for d in paths.session_root().glob(f"{session_id}*"):
        t = d / "transcript.md"
        if t.exists():
            return t
    return None


def resolve_session(session_id: str, *, project: str | None = None) -> tuple[Path, Source]:
    """Find a session by id across known sources. Raises if not found."""
    p = find_claude_code_session(session_id, project=project)
    if p is not None:
        return p, "claude-code"
    p = find_skill_studio_session(session_id)
    if p is not None:
        return p, "skill-studio"
    raise FileNotFoundError(f"session not found: {session_id}")


def resolve_current_session(*, project: str | None = None) -> tuple[Path, str]:
    """Find the current running session via env var. Returns (path, session_id)."""
    sid = get_current_session_id()
    if not sid:
        raise RuntimeError(
            "CLAUDE_CODE_SESSION_ID not set — run inside a Claude Code session "
            "or pass a session_id explicitly"
        )
    p = find_claude_code_session(sid, project=project)
    if p is None:
        raise FileNotFoundError(f"current session file not found: {sid}")
    return p, sid


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


def _iter_tool_uses(path: Path) -> Iterable[dict]:
    """Yield tool_use blocks from assistant messages in a JSONL session."""
    if path.suffix != ".jsonl":
        return
    for line in path.read_text().splitlines():
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "assistant":
            continue
        msg = obj.get("message", {})
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield block


def _detect_workflow_patterns(steps: list[WorkflowStep], min_length: int = 2, min_count: int = 2) -> list[dict]:
    """Find repeated subsequences of tool calls that indicate a workflow.
    Filters out homogeneous sequences (e.g. Bash→Bash) since those are noise.
    """
    if len(steps) < min_length * min_count:
        return []
    tool_names = [s.tool for s in steps]
    patterns: Counter[tuple[str, ...]] = Counter()
    for length in range(min_length, min(6, len(tool_names) // min_count + 1)):
        for i in range(len(tool_names) - length + 1):
            seq = tuple(tool_names[i : i + length])
            if len(set(seq)) < 2:
                continue
            patterns[seq] += 1
    results = []
    seen_supersets: set[tuple[str, ...]] = set()
    for seq, count in patterns.most_common():
        if count < min_count:
            continue
        is_subset = any(
            len(sup) > len(seq) and _is_subsequence(seq, sup)
            for sup in seen_supersets
        )
        if is_subset:
            continue
        seen_supersets.add(seq)
        results.append({
            "tools": list(seq),
            "count": count,
            "label": " → ".join(seq),
        })
    return results[:10]


def _is_subsequence(short: tuple[str, ...], long: tuple[str, ...]) -> bool:
    it = iter(long)
    return all(c in it for c in short)


def extract(path: Path, session_id: str, source: Source, *, max_pain_snippets: int = 6) -> Bundle:
    b = Bundle(session_id=session_id, source=source)
    seen_models: set[str] = set()
    seen_prompts: set[str] = set()
    tool_counter: Counter[str] = Counter()

    for block in _iter_tool_uses(path):
        name = block.get("name", "")
        inp = block.get("input", {})
        tool_counter[name] += 1

        if name == "Agent":
            desc = inp.get("description", "")
            prompt = inp.get("prompt", "")
            agent = AgentCall(
                description=desc,
                subagent_type=inp.get("subagent_type"),
                prompt_snippet=prompt[:200] if prompt else "",
            )
            b.agents.append(agent)
            b.tool_sequence.append(WorkflowStep(tool="Agent", description=desc))
        elif name == "Skill":
            skill = SkillCall(skill=inp.get("skill", ""), args=inp.get("args"))
            b.skills.append(skill)
            b.tool_sequence.append(WorkflowStep(tool="Skill", description=inp.get("skill", "")))
        else:
            desc = inp.get("description", "")
            b.tool_sequence.append(WorkflowStep(tool=name, description=desc))

    b.tool_frequency = dict(tool_counter.most_common())
    b.workflow_patterns = _detect_workflow_patterns(b.tool_sequence)

    for chunk in _iter_text(path):
        b.turn_count += 1

        for pattern in MODEL_PATTERNS:
            for m in re.findall(pattern, chunk, re.I):
                seen_models.add(m.lower())

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
