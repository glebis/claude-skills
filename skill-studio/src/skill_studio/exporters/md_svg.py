from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from skill_studio.schema import DesignJSON


TEMPLATE_DIR = Path(__file__).resolve().parents[2].parent / "assets"


class MdSvgExporter:
    name = "md-svg"

    def __init__(self, template_dir: Path = TEMPLATE_DIR):
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "svg"]),
            keep_trailing_newline=True,
        )

    def render(self, design: DesignJSON, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        md = self.env.get_template("design.md.j2").render(design=design)
        svg = self.env.get_template("design.svg.j2").render(design=design)
        md_path = out_dir / "design.md"
        svg_path = out_dir / "design.svg"
        md_path.write_text(md)
        svg_path.write_text(svg)
        return [md_path, svg_path]
