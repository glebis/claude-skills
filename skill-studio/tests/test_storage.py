import json
from pathlib import Path
from skill_studio.schema import DesignJSON, Meta
from skill_studio.storage import SessionStorage


def test_new_session_creates_dir(tmp_path):
    storage = SessionStorage(root=tmp_path)
    session = storage.new()
    session_dir = tmp_path / session.meta.id
    assert session_dir.exists()
    assert (session_dir / "design.json").exists()
    assert (session_dir / "transcript.md").exists()


def test_save_and_load_roundtrip(tmp_path):
    storage = SessionStorage(root=tmp_path)
    session = storage.new()
    session.hook = "test hook"
    storage.save(session)
    loaded = storage.load(session.meta.id)
    assert loaded.hook == "test hook"


def test_list_sessions(tmp_path):
    storage = SessionStorage(root=tmp_path)
    a = storage.new()
    b = storage.new()
    ids = {s.meta.id for s in storage.list()}
    assert {a.meta.id, b.meta.id} <= ids


def test_append_transcript(tmp_path):
    storage = SessionStorage(root=tmp_path)
    session = storage.new()
    storage.append_transcript(session.meta.id, "assistant", "hi")
    storage.append_transcript(session.meta.id, "user", "hello")
    text = (tmp_path / session.meta.id / "transcript.md").read_text()
    assert "hi" in text and "hello" in text


def test_load_migrates_str_submodels_on_disk(tmp_path):
    """Older sessions persisted submodel fields as bare strings — load auto-coerces."""
    import uuid
    storage = SessionStorage(root=tmp_path)
    sid = str(uuid.uuid4())
    (tmp_path / sid).mkdir()
    bad = {
        "meta": {
            "id": sid, "created": "2026-04-17T00:00:00",
            "preset": "ai-agent", "jtbd_frame": "forces",
            "interview_mode": {"depth": "sprint", "style": "scenario-first"},
            "language": "en",
        },
        "trigger": "when I want to launch the thing",
        "problem": "takes too long",
    }
    (tmp_path / sid / "design.json").write_text(json.dumps(bad))
    design = storage.load(sid)
    assert design.trigger.detail == "when I want to launch the thing"
    assert design.problem.what_hurts == "takes too long"


def test_list_recovers_from_corrupted_session(tmp_path):
    """list() should not crash if one session has string-for-submodel corruption."""
    import uuid
    storage = SessionStorage(root=tmp_path)
    good = storage.new()
    sid = str(uuid.uuid4())
    (tmp_path / sid).mkdir()
    bad = {
        "meta": {
            "id": sid, "created": "2026-04-17T00:00:00",
            "preset": "custom", "jtbd_frame": "job-story",
            "interview_mode": {"depth": "standard", "style": "scenario-first"},
            "language": "en",
        },
        "trigger": "some string that used to break us",
    }
    (tmp_path / sid / "design.json").write_text(json.dumps(bad))
    ids = {s.meta.id for s in storage.list()}
    assert good.meta.id in ids
    assert sid in ids
