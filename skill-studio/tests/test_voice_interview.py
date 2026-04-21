from unittest.mock import MagicMock


def test_run_voice_interview_calls_preflight_and_opens_daily(monkeypatch, tmp_path):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    monkeypatch.setattr("skill_studio.voice.pipecat_interview.SESSION_ROOT", tmp_path)
    opens: list[str] = []
    preflights = []

    def fake_open(url):
        opens.append(url)

    def fake_preflight():
        preflights.append(True)
        return True

    monkeypatch.setattr("skill_studio.voice.pipecat_interview.webbrowser_open", fake_open)
    monkeypatch.setattr("skill_studio.voice.pipecat_interview.run_preflight", fake_preflight)
    monkeypatch.setattr("skill_studio.voice.pipecat_interview.create_daily_room", lambda: "https://example.daily.co/abc")
    monkeypatch.setattr("skill_studio.voice.pipecat_interview.decrypt_dotenv", lambda p: {"OPENROUTER_API_KEY": "x"})
    monkeypatch.setattr("skill_studio.voice.pipecat_interview.get_provider", lambda **kw: MagicMock())
    monkeypatch.setattr("skill_studio.voice.pipecat_interview.run_pipeline", lambda *a, **kw: None)

    from skill_studio.voice.pipecat_interview import run_voice_interview
    args = MagicMock(preset="ai-agent", depth="sprint", style="scenario-first", resume=None, fresh=True)
    rc = run_voice_interview(args)
    assert rc == 0
    assert preflights == [True]
    assert opens == ["https://example.daily.co/abc"]


def test_interview_processor_class_exists():
    from skill_studio.voice.pipecat_interview import InterviewProcessor
    assert hasattr(InterviewProcessor, "process_frame")
    import inspect
    sig = inspect.signature(InterviewProcessor.__init__)
    assert set(sig.parameters.keys()) >= {"design", "preset", "interviewer", "storage"}


def test_greeting_fresh_session_has_intro():
    from skill_studio.voice.pipecat_interview import _build_greeting
    from skill_studio.schema import DesignJSON, Meta
    d = DesignJSON(meta=Meta(preset="ai-agent"))
    g = _build_greeting(d, "What do you want to build?", resumed=False)
    # New greeting mentions the preset and voice commands instead of the brand name
    assert "AI agent" in g
    assert "tell me more" in g  # voice commands surfaced
    assert "What do you want to build?" in g


def test_greeting_resumed_with_hook_says_welcome_back():
    from skill_studio.voice.pipecat_interview import _build_greeting
    from skill_studio.schema import DesignJSON, Meta
    d = DesignJSON(meta=Meta(preset="ai-agent"))
    d.hook = "weekly review drafter"
    g = _build_greeting(d, "What happens on Sundays?", resumed=True)
    assert "Welcome back" in g
    assert "weekly review drafter" in g
    assert "What happens on Sundays?" in g


def test_greeting_resumed_without_hook_generic_welcome_back():
    from skill_studio.voice.pipecat_interview import _build_greeting
    from skill_studio.schema import DesignJSON, Meta
    d = DesignJSON(meta=Meta(preset="ai-agent"))
    g = _build_greeting(d, "Tell me more.", resumed=True)
    assert "Welcome back" in g
    assert "pick up" in g.lower()
    assert "Tell me more." in g
