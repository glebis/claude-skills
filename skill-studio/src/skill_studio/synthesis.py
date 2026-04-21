from __future__ import annotations
from datetime import datetime
from pathlib import Path
from loguru import logger
import yaml
from skill_studio.schema import DesignJSON
from skill_studio import paths


def _groundwork_root() -> Path | None:
    """Indirect through paths module so tests can monkeypatch SKILL_STUDIO_GROUNDWORK_ROOT."""
    return paths.groundwork_root()


# Back-compat module-level attr for existing tests that monkeypatch it.
GROUNDWORK_ROOT = _groundwork_root()


SYNTHESIS_PROMPT = """Read the interview transcript below. Write a 3-5 sentence summary of what emerged — the user's central pain, a specific moment they shared, what they want to change, and any surprising insight. Plain English, first-person user-voice is fine. No headers, no bullets, no clichés like 'the user discussed' — just the substance."""


def synthesize_session(transcript_turns: list[dict], llm) -> str:
    """Run the LLM over the transcript to produce a narrative recap. Returns plain text."""
    if not transcript_turns:
        return ""
    body = "\n".join(f"{t['role']}: {t['text']}" for t in transcript_turns)
    try:
        out = llm.ask(
            history=[{"role": "user", "content": f"{SYNTHESIS_PROMPT}\n\nTranscript:\n{body}"}],
            max_tokens=400,
        )
        return out.strip()
    except Exception as e:
        logger.warning(f"synthesis failed: {e}")
        return ""


def _read_groundwork_profile() -> dict:
    """Parse .groundwork/profile.md frontmatter. Returns {} if not found."""
    root = GROUNDWORK_ROOT
    if root is None:
        return {}
    path = root / "profile.md"
    if not path.exists():
        return {}
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    try:
        _, fm, _ = text.split("---", 2)
        return yaml.safe_load(fm) or {}
    except Exception:
        return {}


def write_groundwork_session(design: DesignJSON, synthesis: str, session_dir: Path) -> Path | None:
    """Write a skill-studio session log into .groundwork/sessions/ for groundwork-review to see.
    Returns the written path, or None if groundwork is not initialized."""
    root = GROUNDWORK_ROOT
    if root is None:
        logger.info("groundwork root not configured (set SKILL_STUDIO_GROUNDWORK_ROOT) — skipping")
        return None
    sessions_dir = root / "sessions"
    if not sessions_dir.exists():
        logger.info(f"groundwork sessions dir not found at {sessions_dir} — skipping")
        return None
    date = datetime.utcnow().strftime("%Y%m%d")
    short_id = design.meta.id[:8]
    out = sessions_dir / f"skill-studio_{date}_{short_id}.md"
    out.write_text(_render_session_md(design, synthesis, session_dir))
    logger.info(f"[groundwork] wrote session log: {out}")
    return out


def _render_session_md(design: DesignJSON, synthesis: str, session_dir: Path) -> str:
    iso = datetime.utcnow().isoformat(timespec="seconds")
    hook = design.hook or "(untitled)"
    lines = [
        "---",
        "source: skill-studio",
        f"session_id: {design.meta.id}",
        f"created: {iso}",
        f"preset: {design.meta.preset}",
        f"depth: {design.meta.interview_mode.depth}",
        "type: interview",
        "---",
        "",
        f"# {hook}",
        "",
        "## What emerged",
        "",
        synthesis or "_(no synthesis generated)_",
        "",
        "## Artifacts",
        "",
        f"- [design.md]({session_dir / 'design.md'})",
        f"- [design.svg]({session_dir / 'design.svg'})",
        f"- [transcript.md]({session_dir / 'transcript.md'})",
        "",
    ]
    return "\n".join(lines)


def write_session_summary(design: DesignJSON, transcript_turns: list[dict], llm, session_dir: Path) -> dict:
    """Do both: write skill-studio-local summary.md AND a groundwork session log if possible.
    Returns a dict of written paths. Never raises — logs on failure."""
    results = {}
    try:
        synthesis = synthesize_session(transcript_turns, llm)
        # skill-studio-local
        local = session_dir / "summary.md"
        local.write_text(
            f"# Session summary — {design.meta.id[:8]}\n\n{synthesis or '_(empty)_'}\n"
        )
        results["local"] = local
        logger.info(f"[synthesis] wrote {local}")
        # groundwork session log (best effort)
        gw = write_groundwork_session(design, synthesis, session_dir)
        if gw:
            results["groundwork"] = gw
    except Exception as e:
        logger.warning(f"session summary failed: {e}")
    return results
