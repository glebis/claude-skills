from pathlib import Path
from skill_studio.schema import DesignJSON
from skill_studio.exporters.md_svg import MdSvgExporter


FIXTURE = Path(__file__).parent / "fixtures" / "sample_design.json"


def test_markdown_contains_hook_and_jtbd(tmp_path):
    design = DesignJSON.model_validate_json(FIXTURE.read_text())
    exporter = MdSvgExporter()
    paths = exporter.render(design, tmp_path)
    md_path = next(p for p in paths if p.suffix == ".md")
    md = md_path.read_text()
    assert design.hook in md
    assert design.jtbd.situation in md
    assert "Before" in md and "After" in md


def test_svg_is_valid_and_contains_hook(tmp_path):
    import xml.etree.ElementTree as ET
    design = DesignJSON.model_validate_json(FIXTURE.read_text())
    exporter = MdSvgExporter()
    paths = exporter.render(design, tmp_path)
    svg_path = next(p for p in paths if p.suffix == ".svg")
    root = ET.fromstring(svg_path.read_text())
    assert root.tag.endswith("svg")
    text_elements = root.iter()
    all_text = "".join((el.text or "") for el in text_elements)
    assert design.hook[:20] in all_text
