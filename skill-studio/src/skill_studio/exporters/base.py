from __future__ import annotations
from pathlib import Path
from typing import Protocol
from skill_studio.schema import DesignJSON


class Exporter(Protocol):
    name: str

    def render(self, design: DesignJSON, out_dir: Path) -> list[Path]: ...
