"""Retrospective engine — deterministic logic for the /retrospective skill.

Extracts testable functions: gate check, finding generation, candidate ranking,
dedup against existing memories, and conflict detection against skill files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Mode(Enum):
    FAST = "fast"
    FULL = "full"
    SKIP = "skip"


class CandidateType(Enum):
    SKILL_UPDATE = "skill_update"
    FEEDBACK_MEMORY = "feedback_memory"
    CLAUDE_MD_RULE = "claude_md_rule"
    LINEAR_TASK = "linear_task"


class SignalSource(Enum):
    USER_CORRECTION = "user_correction"
    FAILED_SKILL = "failed_skill"
    REPEATED_PATTERN = "repeated_pattern"
    ERROR_PATTERN = "error_pattern"
    WORKFLOW_PATTERN = "workflow_pattern"


SIGNAL_PRIORITY = {
    SignalSource.USER_CORRECTION: 1,
    SignalSource.FAILED_SKILL: 2,
    SignalSource.REPEATED_PATTERN: 3,
    SignalSource.ERROR_PATTERN: 4,
    SignalSource.WORKFLOW_PATTERN: 5,
}

TOOL_CALL_THRESHOLD = 8
MAX_CANDIDATES = 5


@dataclass
class SkillInvocation:
    name: str
    status: str  # "success" | "failed"
    error: str | None = None


@dataclass
class Memory:
    name: str
    content: str


@dataclass
class SessionData:
    tool_calls: int
    skills_invoked: list[SkillInvocation] = field(default_factory=list)
    user_corrections: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    repeated_patterns: list[str] = field(default_factory=list)
    existing_memories: list[Memory] = field(default_factory=list)
    existing_skill_content: dict[str, str] = field(default_factory=dict)
    linear_configured: bool = True


@dataclass
class Candidate:
    type: CandidateType
    source: SignalSource
    label: str
    description: str
    target_skill: str | None = None
    proposed_content: str = ""
    conflict: bool = False


def gate_check(tool_calls: int) -> Mode:
    if tool_calls < TOOL_CALL_THRESHOLD:
        return Mode.FAST
    return Mode.FULL


def _normalize(text: str) -> str:
    return text.lower().strip()


def _content_overlaps(needle: str, haystack: str, threshold: float = 0.5) -> bool:
    """Check if key terms from needle appear in haystack."""
    needle_words = set(_normalize(needle).split())
    haystack_lower = _normalize(haystack)
    stopwords = {"the", "a", "an", "is", "was", "to", "in", "for", "of", "and", "or", "not", "don't", "do", "use"}
    meaningful = needle_words - stopwords
    if not meaningful:
        return False
    matches = sum(1 for w in meaningful if w in haystack_lower)
    return (matches / len(meaningful)) >= threshold


def dedup_against_memory(
    candidates: list[Candidate],
    existing_memories: list[Memory],
) -> list[Candidate]:
    result = []
    for c in candidates:
        is_dup = False
        for mem in existing_memories:
            if _content_overlaps(c.proposed_content or c.description, mem.content):
                is_dup = True
                break
        if not is_dup:
            result.append(c)
    return result


def check_skill_conflict(
    proposed_content: str,
    existing_content: str,
) -> bool:
    """Return True if proposed content overlaps with existing skill file content."""
    return _content_overlaps(proposed_content, existing_content)


def generate_findings(session: SessionData) -> list[Candidate]:
    candidates: list[Candidate] = []

    for correction in session.user_corrections:
        candidates.append(Candidate(
            type=CandidateType.FEEDBACK_MEMORY,
            source=SignalSource.USER_CORRECTION,
            label=f"Remember: {correction[:60]}",
            description=correction,
            proposed_content=correction,
        ))

    for skill in session.skills_invoked:
        if skill.status == "failed" and skill.error:
            candidates.append(Candidate(
                type=CandidateType.SKILL_UPDATE,
                source=SignalSource.FAILED_SKILL,
                label=f"Update {skill.name} skill",
                description=f"{skill.name} failed: {skill.error}",
                target_skill=skill.name,
                proposed_content=skill.error,
            ))

    for pattern in session.repeated_patterns:
        if any(s.name for s in session.skills_invoked if s.status == "success") and len(session.skills_invoked) >= 3:
            candidates.append(Candidate(
                type=CandidateType.FEEDBACK_MEMORY,
                source=SignalSource.WORKFLOW_PATTERN,
                label=f"Workflow: {pattern[:60]}",
                description=pattern,
                proposed_content=pattern,
            ))
        else:
            candidates.append(Candidate(
                type=CandidateType.FEEDBACK_MEMORY,
                source=SignalSource.REPEATED_PATTERN,
                label=f"Pattern: {pattern[:60]}",
                description=pattern,
                proposed_content=pattern,
            ))

    return candidates


def filter_by_skill_content(
    candidates: list[Candidate],
    existing_skill_content: dict[str, str],
) -> list[Candidate]:
    result = []
    for c in candidates:
        if c.type == CandidateType.SKILL_UPDATE and c.target_skill:
            content = existing_skill_content.get(c.target_skill, "")
            if content and check_skill_conflict(c.proposed_content, content):
                continue
        result.append(c)
    return result


def filter_linear_candidates(
    candidates: list[Candidate],
    linear_configured: bool,
) -> list[Candidate]:
    if linear_configured:
        return candidates
    return [c for c in candidates if c.type != CandidateType.LINEAR_TASK]


def rank_candidates(candidates: list[Candidate]) -> list[Candidate]:
    return sorted(candidates, key=lambda c: SIGNAL_PRIORITY.get(c.source, 99))


def process_session(session: SessionData) -> tuple[Mode, list[Candidate]]:
    """Full pipeline: gate → generate → dedup → filter → rank → cap."""
    mode = gate_check(session.tool_calls)
    if mode == Mode.FAST:
        return mode, []

    candidates = generate_findings(session)
    candidates = dedup_against_memory(candidates, session.existing_memories)
    candidates = filter_by_skill_content(candidates, session.existing_skill_content)
    candidates = filter_linear_candidates(candidates, session.linear_configured)
    candidates = rank_candidates(candidates)
    candidates = candidates[:MAX_CANDIDATES]

    return mode, candidates
