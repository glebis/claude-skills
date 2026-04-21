from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from skill_studio.storage import SessionStorage
from skill_studio.presets import load_preset, list_presets
from skill_studio.interview.loop import run_interview_turn
from skill_studio.interview.modes import QUESTION_BUDGET, COVERAGE_THRESHOLD
from skill_studio.interview.updater import _deep_merge
from skill_studio.interview.coverage import overall_coverage, next_uncovered_field, score_coverage
from skill_studio.exporters.registry import get_exporter
from skill_studio.llm_provider import get_provider
from skill_studio import paths


SESSION_ROOT = paths.session_root()


def find_resumable(storage: SessionStorage):
    """Return most recent session whose coverage is below its depth-mode threshold, or None."""
    sessions = storage.list()
    sessions.sort(key=lambda s: s.meta.created, reverse=True)
    for s in sessions:
        try:
            preset = load_preset(s.meta.preset)
        except ValueError:
            continue
        threshold = COVERAGE_THRESHOLD.get(s.meta.interview_mode.depth, 0.8)
        if overall_coverage(s, preset) < threshold:
            return s
    return None


def resolve_session(args: argparse.Namespace, storage: SessionStorage):
    """Return (design, resumed_bool). Auto-resume unless --fresh or --resume given."""
    if getattr(args, "resume", None):
        return storage.load(args.resume), True
    if not getattr(args, "fresh", False):
        candidate = find_resumable(storage)
        if candidate is not None:
            return candidate, True
    design = storage.new()
    design.meta.preset = args.preset
    design.meta.interview_mode.depth = args.depth
    design.meta.interview_mode.style = args.style
    storage.save(design)
    return design, False


# ---------------------------------------------------------------------------
# Original stdin-loop fallback (now uses provider factory instead of hardcoded Anthropic)
# ---------------------------------------------------------------------------

def cmd_new(args: argparse.Namespace) -> int:
    storage = SessionStorage(SESSION_ROOT)
    design, resumed = resolve_session(args, storage)
    preset = load_preset(design.meta.preset)
    if resumed:
        cov = overall_coverage(design, preset)
        print(f"Resuming session {design.meta.id[:8]} ({cov:.0%} covered)")

    provider = get_provider(system_prompt=preset.opening_question)
    budget = QUESTION_BUDGET[args.depth]
    question = run_interview_turn(design, preset, provider, user_input=None)
    storage.append_transcript(design.meta.id, "assistant", question)
    print(f"\n{question}\n")

    asked = 1
    while asked < budget:
        try:
            user_input = input("you> ").strip()
        except EOFError:
            break
        if not user_input or user_input.lower() in {"done", "wrap up", "stop"}:
            break
        storage.append_transcript(design.meta.id, "user", user_input)
        question = run_interview_turn(design, preset, provider, user_input=user_input)
        storage.append_transcript(design.meta.id, "assistant", question)
        print(f"\n{question}\n")
        asked += 1
        storage.save(design)

    exporter = get_exporter("md-svg")
    out = SESSION_ROOT / design.meta.id
    exporter.render(design, out)
    print(f"\nDone. Session id: {design.meta.id}")
    print(f"Files: {out}")
    return 0


# ---------------------------------------------------------------------------
# State-only CLI subcommands (used by Claude Code-native interview)
# ---------------------------------------------------------------------------

def cmd_new_session(args: argparse.Namespace) -> int:
    """Create a session, print session_id and opening question. No LLM calls."""
    storage = SessionStorage(SESSION_ROOT)
    preset = load_preset(args.preset)
    design = storage.new()
    design.meta.preset = args.preset
    design.meta.interview_mode.depth = args.depth
    design.meta.interview_mode.style = args.style
    storage.save(design)
    print(f"session_id: {design.meta.id}")
    print(f"opening: {preset.opening_question}")
    return 0


def cmd_apply_patch(args: argparse.Namespace) -> int:
    """Read JSON patch from stdin, apply to design, print updated coverage + next_target."""
    storage = SessionStorage(SESSION_ROOT)
    design = storage.load(args.id)
    preset = load_preset(design.meta.preset)

    raw = sys.stdin.read().strip()
    if raw:
        try:
            patch = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON patch: {exc}", file=sys.stderr)
            return 1
        if isinstance(patch, dict):
            _deep_merge(design, patch)
            storage.save(design)

    cov = overall_coverage(design, preset)
    nxt = next_uncovered_field(design, preset) or "DONE"
    print(f"coverage: {cov:.2f}")
    print(f"next_target: {nxt}")
    return 0


def cmd_next_target(args: argparse.Namespace) -> int:
    """Print the next uncovered field path, or DONE."""
    storage = SessionStorage(SESSION_ROOT)
    design = storage.load(args.id)
    preset = load_preset(design.meta.preset)
    nxt = next_uncovered_field(design, preset)
    print(nxt if nxt else "DONE")
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    """Print overall coverage + per-field scores as JSON."""
    storage = SessionStorage(SESSION_ROOT)
    design = storage.load(args.id)
    preset = load_preset(design.meta.preset)
    scores = score_coverage(design)
    cov = overall_coverage(design, preset)
    print(json.dumps({"overall": round(cov, 4), "fields": {k: round(v, 4) for k, v in scores.items()}}, indent=2))
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    """Export design.md + design.svg for a session and print the paths."""
    storage = SessionStorage(SESSION_ROOT)
    design = storage.load(args.id)
    exporter = get_exporter("md-svg")
    out_dir = SESSION_ROOT / args.id
    paths = exporter.render(design, out_dir)
    for p in paths:
        print(f"wrote {p}")
    return 0


# ---------------------------------------------------------------------------
# Existing subcommands
# ---------------------------------------------------------------------------

def cmd_list(args: argparse.Namespace) -> int:
    storage = SessionStorage(SESSION_ROOT)
    for s in storage.list():
        print(f"{s.meta.id[:8]}  preset={s.meta.preset}  hook={s.hook[:60]}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    storage = SessionStorage(SESSION_ROOT)
    design = storage.load(args.id)
    exporter = get_exporter(args.target)
    paths = exporter.render(design, SESSION_ROOT / args.id)
    for p in paths:
        print(f"wrote {p}")
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    from skill_studio.setup import run_setup
    run_setup()
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    from skill_studio.init_wizard import run_init_wizard
    return run_init_wizard()


def cmd_propose_from_session(args: argparse.Namespace) -> int:
    """Ingest a prior session (deterministic) + propose a DesignJSON patch (one LLM call).

    Does NOT apply the patch. Caller (Claude Code) shows the proposal to the
    user, collects approval/edits, then pipes the approved patch to apply-patch.
    """
    import sys
    from skill_studio.ingest.transcript import extract, resolve_session
    from skill_studio.ingest.proposer import propose
    from pathlib import Path as _P

    if args.path:
        path = _P(args.path).expanduser()
        source = "path"
        session_id = args.session_id or path.stem
    else:
        path, source = resolve_session(args.session_id)
        session_id = args.session_id

    bundle = extract(path, session_id, source)
    if args.bundle_only:
        json.dump(bundle.to_dict(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    provider = get_provider(system_prompt="You are a JTBD interview seeder.")
    patch, rationale = propose(bundle, provider)
    out = {
        "bundle_summary": bundle.to_dict().get("summary"),
        "patch": patch,
        "rationale": rationale,
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="skill-studio")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- new (stdin fallback) ---
    new_p = sub.add_parser("new")
    new_p.add_argument("--preset", choices=list_presets(), default="custom")
    new_p.add_argument("--depth", choices=["sprint", "standard", "deep"], default="standard")
    new_p.add_argument("--style", choices=["socratic", "scenario-first", "metaphor-first", "form", "conversational"], default="scenario-first")
    new_p.add_argument("--voice", action="store_true")
    new_p.add_argument("--resume", metavar="ID", help="Resume a specific session id")
    new_p.add_argument("--fresh", action="store_true", help="Force new session even if a resumable one exists")
    new_p.set_defaults(func=cmd_new)

    # --- new-session (state-only) ---
    ns_p = sub.add_parser("new-session")
    ns_p.add_argument("--preset", choices=list_presets(), default="custom")
    ns_p.add_argument("--depth", choices=["sprint", "standard", "deep"], default="standard")
    ns_p.add_argument("--style", choices=["socratic", "scenario-first", "metaphor-first", "form", "conversational"], default="scenario-first")
    ns_p.set_defaults(func=cmd_new_session)

    # --- apply-patch ---
    ap_p = sub.add_parser("apply-patch")
    ap_p.add_argument("id")
    ap_p.set_defaults(func=cmd_apply_patch)

    # --- next-target ---
    nt_p = sub.add_parser("next-target")
    nt_p.add_argument("id")
    nt_p.set_defaults(func=cmd_next_target)

    # --- coverage ---
    cov_p = sub.add_parser("coverage")
    cov_p.add_argument("id")
    cov_p.set_defaults(func=cmd_coverage)

    # --- done ---
    done_p = sub.add_parser("done")
    done_p.add_argument("id")
    done_p.set_defaults(func=cmd_done)

    # --- list ---
    list_p = sub.add_parser("list")
    list_p.set_defaults(func=cmd_list)

    # --- export ---
    export_p = sub.add_parser("export")
    export_p.add_argument("id")
    export_p.add_argument("target")
    export_p.set_defaults(func=cmd_export)

    # --- setup (key-entry only, sops-required) ---
    setup_p = sub.add_parser("setup")
    setup_p.set_defaults(func=cmd_setup)

    # --- init (full first-run wizard) ---
    init_p = sub.add_parser("init", help="Interactive first-run setup wizard")
    init_p.set_defaults(func=cmd_init)

    # --- propose-from-session (ingest a prior transcript → JTBD patch proposal) ---
    pfs_p = sub.add_parser(
        "propose-from-session",
        help="Ingest a prior session and propose a DesignJSON patch (user must approve before apply-patch)",
    )
    pfs_p.add_argument("session_id", nargs="?")
    pfs_p.add_argument("--path", help="Direct path to a transcript file")
    pfs_p.add_argument(
        "--bundle-only",
        action="store_true",
        help="Emit just the deterministic bundle (no LLM call)",
    )
    pfs_p.set_defaults(func=cmd_propose_from_session)

    args = parser.parse_args(argv)
    if args.cmd == "new" and getattr(args, "voice", False):
        from skill_studio.voice.pipecat_interview import run_voice_interview
        return run_voice_interview(args)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
