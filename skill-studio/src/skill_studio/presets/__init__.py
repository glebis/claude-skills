from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel


PRESET_DIR = Path(__file__).parent


class Preset(BaseModel):
    name: str
    label: str
    default_jtbd_frame: str
    opening_question: str
    field_weights: dict[str, Any]  # nested dict or flat — both allowed


def load_preset(name: str) -> Preset:
    path = PRESET_DIR / f"{name.replace('-', '_')}.yaml"
    if not path.exists():
        raise ValueError(f"Unknown preset: {name}")
    data = yaml.safe_load(path.read_text())
    return Preset.model_validate(data)


def list_presets() -> list[str]:
    return [p.stem.replace("_", "-") for p in sorted(PRESET_DIR.glob("*.yaml"))]
