"""Actually generate on-brand images: tokens (+ refs.json) -> API calls.

SKILL CONVENTION. Where the prompt door (`prompt`) emits paste-ready command
lines, `generate` runs them: it composes the winning prompt formulation from
the fidelity tests (art-direction prose with hexes + color words + brand
avoid-list — see references/prompt-fidelity-notes.md) and shells out to the
gpt-image-2 / nano-banana skill scripts. Draft quality by default.

Reference images: `--refs <dir>` reads the `refs.json` manifest written by
`annotate`. No provider has typed per-image role fields (references/providers.md),
so roles are translated into (a) `--reference <img>` flags — both skill scripts
accept them — and (b) a role-annotated clause in the prompt ("from ref-1
(a.png) take palette, mood: …").
"""

import pathlib
import subprocess

from . import annotate as annotate_mod
from . import brand_summary as _bs
from .export_prompt import _color_word, _by_role, _ROLE_ORDER, _slug

_SCRIPTS = {
    "gpt-image-2": "~/.claude/skills/gpt-image-2/scripts/gpt_image_2.py",
    "nano-banana": "~/.claude/skills/nano-banana/scripts/nano_banana.py",
}


def _script(target):
    return str(pathlib.Path(_SCRIPTS[target]).expanduser())


def compose_prompt(summary, subject, refs=None):
    """Formulation C: art-direction prose. `refs` = refs.json entries with roles."""
    brand = summary.get("brand") or {}
    parts = []
    mood = brand.get("mood")
    lead = ", ".join(mood) if isinstance(mood, list) else (mood or "")
    parts.append(f"A {lead} image: {subject}." if lead else f"{subject}.")
    if brand.get("imageryStyle"):
        parts.append(str(brand["imageryStyle"]).rstrip(".") + ".")
    roles = _by_role(summary)
    if roles:
        ordered = sorted(roles, key=lambda r: _ROLE_ORDER.index(r) if r in _ROLE_ORDER else 99)
        swatches = []
        for role in ordered:
            word = _color_word(roles[role])
            swatches.append(f"{role} {word} ({roles[role]})" if word else f"{role} ({roles[role]})")
        parts.append("Palette, exactly and only: " + ", ".join(swatches) + ".")
    if summary["fonts"]:
        parts.append("Any visible text set in " + summary["fonts"][0] + "-style monospace type.")
    for i, entry in enumerate(refs or [], start=1):
        take = ", ".join(entry.get("take", [])) or "overall style"
        clause = f"From reference image {i} ({entry['file']}) take: {take}"
        if entry.get("note"):
            clause += f" — {entry['note']}"
        parts.append(clause + ".")
    neg = brand.get("negativePrompt")
    avoid = brand.get("avoid") or []
    donts = ", ".join([*avoid, neg] if neg else avoid)
    if donts:
        parts.append(f"Strictly avoid: {donts}.")
    return " ".join(parts)


def load_refs(refs_dir):
    """Annotated entries (take/note non-empty) + their absolute paths."""
    refs_dir = pathlib.Path(refs_dir)
    entries = [e for e in annotate_mod.load_manifest(refs_dir).get("images", [])
               if e.get("take") or e.get("note")]
    return [{**e, "path": str(refs_dir / e["file"])} for e in entries]


def build_command(target, prompt, out_path, refs=None, draft=True, platform="square"):
    cmd = ["python3", _script(target)]
    if target == "gpt-image-2":
        cmd += ["--platform", platform, "-y"]
        cmd += ["--draft"] if draft else ["--quality", "high"]
    else:
        cmd += ["--platform", platform, "--model", "flash" if draft else "pro"]
    for entry in refs or []:
        cmd += ["--reference", entry["path"]]
    cmd += [prompt, str(out_path)]
    return cmd


def generate(tree, resolved, name, targets, subject=None, refs_dir=None,
             out_dir=".", draft=True, platform="square", dry_run=False, runner=subprocess.run):
    """Compose + execute one generation per target. Returns [(target, out, rc)]."""
    brand = _bs.extract_brand(tree)
    summary = _bs.summarize(resolved, brand=brand)
    subject = subject or (f"abstract brand mood board for {name}, "
                          "geometric composition expressing the brand's character")
    refs = load_refs(refs_dir) if refs_dir else []
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = compose_prompt(summary, subject, refs=refs)
    results = []
    for target in targets:
        out = out_dir / f"{_slug(name)}-{target}.png"
        cmd = build_command(target, prompt, out, refs=refs, draft=draft, platform=platform)
        if dry_run:
            print(f"# {target}\n{' '.join(cmd)}\n")
            results.append((target, str(out), 0))
            continue
        proc = runner(cmd)
        results.append((target, str(out), proc.returncode))
    return results
