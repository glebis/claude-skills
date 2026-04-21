from skill_studio.interview.modes import (
    COVERAGE_THRESHOLD,
    QUESTION_BUDGET,
    STYLE_SYSTEM_PROMPTS,
)


def test_coverage_thresholds_monotonic():
    assert COVERAGE_THRESHOLD["sprint"] < COVERAGE_THRESHOLD["standard"] < COVERAGE_THRESHOLD["deep"]


def test_question_budget_monotonic():
    assert QUESTION_BUDGET["sprint"] < QUESTION_BUDGET["standard"] < QUESTION_BUDGET["deep"]


def test_all_styles_defined():
    assert set(STYLE_SYSTEM_PROMPTS.keys()) == {
        "socratic", "scenario-first", "metaphor-first", "form", "conversational"
    }
    for prompt in STYLE_SYSTEM_PROMPTS.values():
        assert len(prompt) > 50


def test_conversational_style_emphasizes_reflection():
    """The conversational style must tell the LLM to reflect back what the user said."""
    p = STYLE_SYSTEM_PROMPTS["conversational"]
    assert "reflect back" in p.lower() or "quote" in p.lower()
