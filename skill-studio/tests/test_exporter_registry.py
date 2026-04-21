from skill_studio.exporters.registry import EXPORTERS, get_exporter


def test_md_svg_registered():
    assert "md-svg" in EXPORTERS


def test_get_exporter_returns_instance():
    exp = get_exporter("md-svg")
    assert exp.name == "md-svg"


def test_unknown_exporter_raises():
    import pytest
    with pytest.raises(KeyError):
        get_exporter("nope")
