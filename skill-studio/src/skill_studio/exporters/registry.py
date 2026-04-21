from __future__ import annotations
from skill_studio.exporters.base import Exporter
from skill_studio.exporters.md_svg import MdSvgExporter


EXPORTERS: dict[str, Exporter] = {
    "md-svg": MdSvgExporter(),
}


def get_exporter(name: str) -> Exporter:
    if name not in EXPORTERS:
        raise KeyError(f"Unknown exporter: {name}. Available: {sorted(EXPORTERS)}")
    return EXPORTERS[name]
