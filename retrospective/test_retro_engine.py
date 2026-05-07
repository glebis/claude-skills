"""Tests for retro_engine — driven by YAML scenario fixtures."""

from pathlib import Path

import yaml
import pytest

from retro_engine import (
    CandidateType,
    Memory,
    Mode,
    SessionData,
    SignalSource,
    SkillInvocation,
    check_skill_conflict,
    dedup_against_memory,
    filter_by_skill_content,
    filter_linear_candidates,
    gate_check,
    generate_findings,
    process_session,
    rank_candidates,
    MAX_CANDIDATES,
)

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


def load_scenario(name: str) -> dict:
    path = SCENARIOS_DIR / name
    return yaml.safe_load(path.read_text())


def build_session(scenario: dict) -> SessionData:
    ms = scenario["mock_session"]
    return SessionData(
        tool_calls=ms["tool_calls"],
        skills_invoked=[
            SkillInvocation(name=s["name"], status=s["status"], error=s.get("error"))
            for s in ms.get("skills_invoked", [])
        ],
        user_corrections=ms.get("user_corrections", []),
        errors=ms.get("errors", []),
        repeated_patterns=ms.get("repeated_patterns", []),
        existing_memories=[
            Memory(name=m["name"], content=m["content"])
            for m in ms.get("existing_memories", [])
        ],
        existing_skill_content=ms.get("existing_skill_content", {}),
        linear_configured=ms.get("linear_configured", True),
    )


# ── Gate check tests ──


class TestGateCheck:
    def test_short_session_returns_fast(self):
        assert gate_check(3) == Mode.FAST

    def test_threshold_returns_full(self):
        assert gate_check(8) == Mode.FULL

    def test_long_session_returns_full(self):
        assert gate_check(85) == Mode.FULL

    def test_boundary_below_threshold(self):
        assert gate_check(7) == Mode.FAST


# ── Scenario: productive long session ──


class TestProductiveLong:
    @pytest.fixture
    def scenario(self):
        return load_scenario("01_productive_long.yaml")

    @pytest.fixture
    def result(self, scenario):
        session = build_session(scenario)
        return process_session(session)

    def test_mode_is_full(self, result):
        mode, _ = result
        assert mode == Mode.FULL

    def test_candidate_count_in_range(self, result, scenario):
        _, candidates = result
        expected = scenario["expected"]["candidate_count"]
        assert expected["min"] <= len(candidates) <= expected["max"]

    def test_includes_telegram_skill_update(self, result):
        _, candidates = result
        telegram_updates = [
            c for c in candidates
            if c.type == CandidateType.SKILL_UPDATE and c.target_skill == "telegram"
        ]
        assert len(telegram_updates) >= 1
        assert any("Telethon" in c.description or "telethon" in c.description.lower()
                    for c in telegram_updates)

    def test_excludes_duplicate_memory(self, result):
        _, candidates = result
        memory_candidates = [c for c in candidates if c.type == CandidateType.FEEDBACK_MEMORY]
        for c in memory_candidates:
            assert "don't mock the database" not in c.proposed_content.lower()


# ── Scenario: short session ──


class TestShortSession:
    @pytest.fixture
    def result(self):
        scenario = load_scenario("02_short_session.yaml")
        session = build_session(scenario)
        return process_session(session)

    def test_mode_is_fast(self, result):
        mode, _ = result
        assert mode == Mode.FAST

    def test_no_candidates_in_fast_mode(self, result):
        _, candidates = result
        assert len(candidates) == 0


# ── Scenario: rough session ──


class TestRoughSession:
    @pytest.fixture
    def result(self):
        scenario = load_scenario("03_rough_session.yaml")
        session = build_session(scenario)
        return process_session(session)

    def test_mode_is_full(self, result):
        mode, _ = result
        assert mode == Mode.FULL

    def test_has_candidates(self, result):
        _, candidates = result
        assert len(candidates) >= 1


# ── Scenario: no skills used ──


class TestNoSkillsUsed:
    @pytest.fixture
    def result(self):
        scenario = load_scenario("04_no_skills.yaml")
        session = build_session(scenario)
        return process_session(session)

    def test_mode_is_full(self, result):
        mode, _ = result
        assert mode == Mode.FULL

    def test_no_skill_update_candidates(self, result):
        _, candidates = result
        skill_updates = [c for c in candidates if c.type == CandidateType.SKILL_UPDATE]
        assert len(skill_updates) == 0

    def test_has_correction_candidate(self, result):
        _, candidates = result
        corrections = [c for c in candidates if c.source == SignalSource.USER_CORRECTION]
        assert len(corrections) >= 1
        assert any("single quotes" in c.proposed_content.lower() for c in corrections)


# ── Scenario: many learnings (cap test) ──


class TestManyLearnings:
    @pytest.fixture
    def result(self):
        scenario = load_scenario("05_many_learnings.yaml")
        session = build_session(scenario)
        return process_session(session)

    def test_capped_at_max(self, result):
        _, candidates = result
        assert len(candidates) <= MAX_CANDIDATES

    def test_corrections_ranked_first(self, result):
        _, candidates = result
        if len(candidates) >= 2:
            first_sources = [c.source for c in candidates[:3]]
            assert SignalSource.USER_CORRECTION in first_sources

    def test_deduplicates_existing_telethon_memory(self, result):
        _, candidates = result
        for c in candidates:
            if c.type == CandidateType.FEEDBACK_MEMORY:
                assert "telethon directly for dms" not in c.proposed_content.lower()


# ── Scenario: duplicate memory ──


class TestDuplicateMemory:
    @pytest.fixture
    def result(self):
        scenario = load_scenario("06_duplicate_memory.yaml")
        session = build_session(scenario)
        return process_session(session)

    def test_dedup_filters_known_insights(self, result):
        _, candidates = result
        memory_candidates = [c for c in candidates if c.type == CandidateType.FEEDBACK_MEMORY]
        for c in memory_candidates:
            assert "telethon directly" not in c.proposed_content.lower()


# ── Scenario: skill file conflict ──


class TestSkillConflict:
    @pytest.fixture
    def result(self):
        scenario = load_scenario("07_skill_conflict.yaml")
        session = build_session(scenario)
        return process_session(session)

    def test_no_duplicate_skill_update(self, result):
        _, candidates = result
        pdf_updates = [
            c for c in candidates
            if c.type == CandidateType.SKILL_UPDATE and c.target_skill == "pdf-generation"
        ]
        assert len(pdf_updates) == 0


# ── Scenario: linear not configured ──


class TestLinearNotConfigured:
    @pytest.fixture
    def result(self):
        scenario = load_scenario("08_linear_not_configured.yaml")
        session = build_session(scenario)
        return process_session(session)

    def test_no_linear_candidates(self, result):
        _, candidates = result
        linear = [c for c in candidates if c.type == CandidateType.LINEAR_TASK]
        assert len(linear) == 0

    def test_still_has_skill_update(self, result):
        _, candidates = result
        skill_updates = [c for c in candidates if c.type == CandidateType.SKILL_UPDATE]
        assert len(skill_updates) >= 1


# ── Scenario: cross-skill workflow ──


class TestCrossSkillWorkflow:
    @pytest.fixture
    def result(self):
        scenario = load_scenario("09_cross_skill_workflow.yaml")
        session = build_session(scenario)
        return process_session(session)

    def test_detects_workflow_pattern(self, result):
        _, candidates = result
        workflow = [c for c in candidates if c.source == SignalSource.WORKFLOW_PATTERN]
        assert len(workflow) >= 1


# ── Unit tests for individual functions ──


class TestDedup:
    def test_filters_exact_match(self):
        candidates = [
            _make_candidate("use Telethon directly for DMs"),
        ]
        memories = [Memory(name="x", content="Use Telethon directly for private DMs")]
        result = dedup_against_memory(candidates, memories)
        assert len(result) == 0

    def test_keeps_novel_content(self):
        candidates = [
            _make_candidate("always use single quotes"),
        ]
        memories = [Memory(name="x", content="Use Telethon for DMs")]
        result = dedup_against_memory(candidates, memories)
        assert len(result) == 1


class TestRanking:
    def test_corrections_before_failures(self):
        candidates = [
            _make_candidate("error", source=SignalSource.FAILED_SKILL),
            _make_candidate("correction", source=SignalSource.USER_CORRECTION),
        ]
        ranked = rank_candidates(candidates)
        assert ranked[0].source == SignalSource.USER_CORRECTION

    def test_failures_before_patterns(self):
        candidates = [
            _make_candidate("pattern", source=SignalSource.REPEATED_PATTERN),
            _make_candidate("failure", source=SignalSource.FAILED_SKILL),
        ]
        ranked = rank_candidates(candidates)
        assert ranked[0].source == SignalSource.FAILED_SKILL


class TestSkillConflictCheck:
    def test_detects_overlap(self):
        assert check_skill_conflict(
            "babel-lang: russian in YAML frontmatter",
            "Russian text needs babel-lang: russian in YAML frontmatter",
        )

    def test_no_overlap(self):
        assert not check_skill_conflict(
            "xelatex required for CJK fonts",
            "Russian text needs babel-lang: russian in YAML frontmatter",
        )


class TestLinearFilter:
    def test_removes_linear_when_not_configured(self):
        from retro_engine import Candidate, CandidateType, SignalSource
        candidates = [
            Candidate(
                type=CandidateType.LINEAR_TASK,
                source=SignalSource.FAILED_SKILL,
                label="Create task",
                description="Fix telegram bug",
            ),
            Candidate(
                type=CandidateType.SKILL_UPDATE,
                source=SignalSource.FAILED_SKILL,
                label="Update skill",
                description="Fix telegram bug",
            ),
        ]
        result = filter_linear_candidates(candidates, linear_configured=False)
        assert len(result) == 1
        assert result[0].type == CandidateType.SKILL_UPDATE


# ── Helpers ──


def _make_candidate(
    content: str,
    source: SignalSource = SignalSource.USER_CORRECTION,
) -> "Candidate":
    from retro_engine import Candidate, CandidateType
    return Candidate(
        type=CandidateType.FEEDBACK_MEMORY,
        source=source,
        label=content[:40],
        description=content,
        proposed_content=content,
    )
