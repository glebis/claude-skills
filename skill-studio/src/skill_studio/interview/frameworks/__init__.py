from __future__ import annotations
from pathlib import Path
import yaml

FRAMEWORKS_DIR = Path(__file__).parent


def load_framework(name: str) -> dict:
    path = FRAMEWORKS_DIR / f"{name}.yaml"
    if not path.exists():
        raise ValueError(f"Unknown framework: {name}. Available: {list_frameworks()}")
    return yaml.safe_load(path.read_text())


def list_frameworks() -> list[str]:
    return sorted(p.stem for p in FRAMEWORKS_DIR.glob("*.yaml"))
