"""Tests for voice-command detection and the bumped follow-up default."""
from __future__ import annotations

from skill_studio.voice.pipecat_interview import _match_voice_command
from skill_studio.interview.director import DirectorState


def test_stop_command_variants():
    assert _match_voice_command("done") == "stop"
    assert _match_voice_command("done.") == "stop"
    assert _match_voice_command("DONE") == "stop"
    assert _match_voice_command("stop") == "stop"
    assert _match_voice_command("that's enough") == "stop"


def test_go_deeper_variants():
    assert _match_voice_command("tell me more") == "go_deeper"
    assert _match_voice_command("Tell me more.") == "go_deeper"
    assert _match_voice_command("go deeper") == "go_deeper"
    assert _match_voice_command("elaborate") == "go_deeper"


def test_skip_variants():
    assert _match_voice_command("skip") == "skip"
    assert _match_voice_command("next") == "skip"
    assert _match_voice_command("move on") == "skip"


def test_no_false_positives():
    assert _match_voice_command("I want to skip the Monday meeting") is None
    assert _match_voice_command("the RAG is done poorly") is None  # substring-of-command, not exact
    assert _match_voice_command("") is None


def test_director_default_follow_ups_bumped():
    """Conversational-by-default: each subject gets up to 4 follow-ups before we move on."""
    s = DirectorState()
    assert s.max_follow_ups == 4
