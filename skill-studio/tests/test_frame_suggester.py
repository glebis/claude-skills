from skill_studio.interview.frame_suggester import suggest_frame


def test_emotional_signals_prefer_forces():
    transcript = "I've been stuck on this for months. I keep meaning to fix it but never do."
    assert suggest_frame(transcript, preset="life-automation") == "forces"


def test_metrics_language_prefers_outcomes():
    transcript = "Right now I spend 6 hours a week. I want that down to 1 hour."
    assert suggest_frame(transcript, preset="knowledge-work") == "outcomes"


def test_social_signals_prefer_fse():
    transcript = "I want my team to see me as the person who doesn't drop balls."
    assert suggest_frame(transcript, preset="knowledge-work") == "fse"


def test_default_falls_back_to_preset_default():
    assert suggest_frame("Build a thing", preset="ai-agent") == "forces"
    assert suggest_frame("Build a thing", preset="custom") == "job-story"
