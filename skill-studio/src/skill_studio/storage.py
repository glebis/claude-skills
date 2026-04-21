from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from skill_studio.schema import DesignJSON, Meta


def _migrate_str_submodels(data: dict) -> dict:
    """Best-effort migration: coerce str values into their submodel shape.

    Older sessions may have `trigger: "..."` or `problem: "..."` on disk because
    the updater used to shove LLM string outputs directly into Pydantic submodel
    fields. Current schema rejects that. Auto-wrap during load.
    """
    str_to_sub = {
        "trigger": "detail",
        "problem": "what_hurts",
        "jtbd": "situation",
        "needs": None,  # Needs is a dict of lists; can't wrap a bare string
        "before_after": None,
        "concept_imagery": "metaphor",
    }
    for key, text_field in str_to_sub.items():
        if isinstance(data.get(key), str) and text_field:
            data[key] = {text_field: data[key]}
    return data


class SessionStorage:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def new(self) -> DesignJSON:
        design = DesignJSON(meta=Meta())
        self._session_dir(design.meta.id).mkdir()
        (self._session_dir(design.meta.id) / "transcript.md").touch()
        self.save(design)
        return design

    def load(self, session_id: str) -> DesignJSON:
        path = self._session_dir(session_id) / "design.json"
        data = json.loads(path.read_text())
        data = _migrate_str_submodels(data)
        return DesignJSON.model_validate(data)

    def save(self, design: DesignJSON) -> None:
        path = self._session_dir(design.meta.id) / "design.json"
        path.write_text(design.model_dump_json(indent=2))

    def list(self) -> list[DesignJSON]:
        out: list[DesignJSON] = []
        for child in sorted(self.root.iterdir()):
            if (child / "design.json").exists():
                out.append(self.load(child.name))
        return out

    def append_transcript(self, session_id: str, role: str, text: str) -> None:
        path = self._session_dir(session_id) / "transcript.md"
        ts = datetime.utcnow().isoformat(timespec="seconds")
        with path.open("a") as f:
            f.write(f"\n**{role}** `{ts}`\n\n{text}\n")

    def _session_dir(self, session_id: str) -> Path:
        return self.root / session_id
