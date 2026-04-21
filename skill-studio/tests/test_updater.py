from unittest.mock import MagicMock
from skill_studio.schema import DesignJSON, Meta
from skill_studio.interview.updater import apply_answer, _deep_merge


def test_apply_answer_fills_hook():
    design = DesignJSON(meta=Meta(preset="ai-agent"))
    llm = MagicMock()
    llm.ask.return_value = '{"hook": "Agent that drafts weekly reviews", "problem": {"what_hurts": "Takes 90 min every Sunday"}}'
    apply_answer(design, target="hook", answer="Want an agent to draft reviews, takes me 90 minutes now", llm=llm)
    assert design.hook == "Agent that drafts weekly reviews"
    assert "90" in design.problem.what_hurts


def test_apply_answer_handles_lists():
    design = DesignJSON(meta=Meta(preset="ai-agent"))
    llm = MagicMock()
    llm.ask.return_value = '{"capabilities": ["vault read", "LLM summarize"]}'
    apply_answer(design, target="capabilities", answer="It needs to read my vault and summarize", llm=llm)
    assert design.capabilities == ["vault read", "LLM summarize"]


def test_string_into_trigger_maps_to_detail():
    """LLM sometimes returns trigger as a string — map to Trigger.detail instead of corrupting the submodel."""
    d = DesignJSON(meta=Meta(preset="ai-agent"))
    _deep_merge(d, {"trigger": "I just couldn't launch the thing"})
    assert d.trigger.detail == "I just couldn't launch the thing"
    # Round-trip should not raise Pydantic serialization warnings
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        d.model_dump_json()


def test_dict_into_trigger_still_works():
    d = DesignJSON(meta=Meta(preset="ai-agent"))
    _deep_merge(d, {"trigger": {"type": "scheduled", "detail": "weekly"}})
    assert d.trigger.type == "scheduled"
    assert d.trigger.detail == "weekly"


def test_string_into_problem_maps_to_what_hurts():
    d = DesignJSON(meta=Meta(preset="ai-agent"))
    _deep_merge(d, {"problem": "takes too long"})
    assert d.problem.what_hurts == "takes too long"
