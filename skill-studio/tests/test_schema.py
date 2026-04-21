import json
from pathlib import Path
from skill_studio.schema import DesignJSON, Meta, BeforeAfter, Scenario

FIXTURE = Path(__file__).parent / "fixtures" / "sample_design.json"


def test_schema_roundtrip():
    data = json.loads(FIXTURE.read_text())
    design = DesignJSON.model_validate(data)
    assert design.meta.preset == "ai-agent"
    assert design.meta.jtbd_frame == "forces"
    assert len(design.scenarios) >= 1
    back = json.loads(design.model_dump_json())
    assert back["meta"]["preset"] == "ai-agent"


def test_schema_defaults_empty():
    design = DesignJSON.model_validate({
        "meta": {
            "id": "11111111-1111-1111-1111-111111111111",
            "created": "2026-04-16T10:00:00",
            "preset": "custom",
            "jtbd_frame": "job-story",
            "interview_mode": {"depth": "standard", "style": "scenario-first"},
            "language": "en",
        }
    })
    assert design.hook == ""
    assert design.needs.functional == []
    assert design.coverage == {}
