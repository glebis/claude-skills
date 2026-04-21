from __future__ import annotations
from skill_studio.interview.frameworks import load_framework
from skill_studio.interview.subjects import Subject
from skill_studio.interview.director import Move, MoveKind


def pick_question(
    move: Move,
    framework_name: str,
    transcript_tail: list[dict],
    llm,
    style_prompt: str = "",
    asked_in_phase: set[str] | None = None,
) -> str:
    """Pick a question given the director's move.

    Uses the YAML question bank first, falls back to LLM generation when
    all curated questions for a phase have already been asked.

    asked_in_phase: explicit set of questions already asked in this phase
    (persisted across restarts via DirectorState). If None, falls back to
    scanning the transcript tail.
    """
    fw = load_framework(framework_name)
    phase_key = move.phase.value
    phase_data = fw.get("phases", {}).get(phase_key, {})

    if move.kind == MoveKind.FOLLOW_UP:
        pool = phase_data.get("follow_ups", []) or phase_data.get("questions", [])
    elif move.kind in (MoveKind.NEW_SUBJECT, MoveKind.ADVANCE_PHASE):
        pool = phase_data.get("questions", [])
    elif move.kind == MoveKind.CLOSE:
        pool = fw.get("phases", {}).get("close", {}).get("questions", [
            "Here's what I heard. Does this feel like you?"
        ])
    else:
        pool = phase_data.get("questions", [])

    # Combine persistent per-phase dedup set with tail-scan (belt + suspenders).
    tail_asked = {t["text"] for t in transcript_tail if t.get("role") == "assistant"}
    already_asked = (asked_in_phase or set()) | tail_asked

    for q in pool:
        if q not in already_asked:
            return q

    # Fallback: use LLM with the framework's stance + style prompt.
    stance = fw.get("stance", "")
    context = "\n".join(f"{t['role']}: {t['text']}" for t in transcript_tail[-6:])
    user_msg = (
        f"{stance}\n\n{style_prompt}\n\n"
        f"Recent exchange:\n{context}\n\n"
        f"Current phase: {move.phase.value}. "
        f"Current subject: {move.subject.label if move.subject else 'close'}. "
        f"Move: {move.kind.value}.\n\n"
        f"Ask ONE short, human, natural question in keeping with the stance. "
        f"No preamble. Don't number. Don't ask about features."
    )
    try:
        return llm.ask(history=[{"role": "user", "content": user_msg}], max_tokens=100)
    except Exception:
        return pool[0] if pool else "Tell me more."


# ---------------------------------------------------------------------------
# Deprecated alias — kept so any code that still imports pick_next_question
# (e.g. old test snapshots or external callers) does not hard-crash.
# The old signature is incompatible with the new engine; this shim returns
# the opening question unconditionally and logs a deprecation warning.
# ---------------------------------------------------------------------------

def pick_next_question(design, preset, llm) -> str:  # type: ignore[override]
    """Deprecated. Use pick_question() with a director Move instead."""
    import warnings
    warnings.warn(
        "pick_next_question() is deprecated — use pick_question() with a Move.",
        DeprecationWarning,
        stacklevel=2,
    )
    if not design.transcript:
        return preset.opening_question
    # Minimal fallback: ask LLM with old-style context
    from skill_studio.interview.coverage import next_uncovered_field
    from skill_studio.interview.modes import STYLE_SYSTEM_PROMPTS
    target = next_uncovered_field(design, preset)
    if target is None:
        return "I think we have enough — want to wrap up, or keep going?"
    context = design.model_dump_json(indent=2)
    style_prompt = STYLE_SYSTEM_PROMPTS[design.meta.interview_mode.style]
    user_msg = (
        f"{style_prompt}\n\n"
        f"Current design state:\n```json\n{context}\n```\n\n"
        f"TARGET FIELD: {target}\n\n"
        f"Ask ONE question that most efficiently fills this field. "
        f"Do not add preamble or summarize prior answers. Just the question."
    )
    return llm.ask(history=[{"role": "user", "content": user_msg}], max_tokens=200)
