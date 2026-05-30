#!/usr/bin/env python3
"""Build a case-conceptualization card from an authored session JSON.

Emits a markdown card scaffold that summarizes the (synthetic) client: a snapshot, the
modality-appropriate formulation skeleton, themes and goals pulled from the session's `ground_truth`,
and a slot for a portrait image. The clinical narrative (the `<!-- FILL: ... -->` blocks) is authored
by the model; this script supplies structure, watermark, and a ready-to-use portrait prompt for the
`gpt-image-2` skill.

Usage:
    python3 make_card.py --in /tmp/maya_ifs.json --out /tmp/maya_card.md
    python3 make_card.py --in /tmp/maya_ifs.json --image assets/maya_portrait.png --out card.md
    python3 make_card.py --in /tmp/maya_ifs.json --print-prompt
"""
import argparse
import json
import sys

from _common import (WATERMARK, validate_session, as_str_list, frontmatter, SessionError,
                     write_text, run_cli)

# Card-specific provenance line, shown in addition to the mandatory base watermark.
CARD_NOTE = "Case card for a fictional persona — not a real clinical record."

FORMULATIONS = {
    "cbt": [
        ("Core belief / schema", "the central 'I am…' belief driving the pattern"),
        ("Key automatic thoughts", "recurring hot thoughts and the situations that trigger them"),
        ("Cognitive distortions", "named distortions evidenced in the session"),
        ("Maintenance cycle", "thought → emotion → behaviour → consequence loop"),
    ],
    "ifs": [
        ("Parts map", "managers / firefighters / exiles identified, and their roles"),
        ("Protective intent", "what each protector is guarding against"),
        ("Burdens", "the beliefs/feelings the exile carries and where they came from"),
        ("Self-energy & access", "how much Self was available; what unblended access"),
    ],
    "icf-grow": [
        ("Goal", "what the client wants, in their words"),
        ("Current reality", "the honest present-state picture"),
        ("Options & resources", "paths considered and strengths in play"),
        ("Will / commitment", "what they committed to and their readiness level"),
    ],
    "act-mi": [
        ("Values", "what matters to the client underneath the problem"),
        ("Ambivalence", "the change-vs-status-quo tension and sustain talk"),
        ("Fusion / avoidance", "thoughts they are fused with; experiences avoided"),
        ("Change talk & commitment", "DARN-C evidence and committed action"),
    ],
}


def portrait_prompt(persona, modality):
    """A safe, clearly-synthetic, courtroom-sketch line-art prompt for gpt-image-2.

    Deliberately loose and gestural — a reportage sketch reads unmistakably as hand-drawn, never a
    photo of a real person, and captures mood/posture/environment over literal likeness.
    """
    persona = str(persona) if persona not in (None, "") else "client"
    modality = modality if isinstance(modality, str) and modality else "coaching"
    return (
        f"Loose courtroom-sketch / reportage line art of a fictional therapy-client persona "
        f"named '{persona}'. Quick gestural pen-and-ink linework with a few light marker or "
        f"colored-pencil washes, expressive and unfinished, sketched on the go. Capture mood, "
        f"posture, and the session environment of a {modality.upper()} session rather than a "
        f"literal likeness. Clearly a hand-drawn sketch — not a photograph, not a polished "
        f"portrait. No text, no logos. Synthetic/illustrative character — not a real individual."
    )


def build_card(data, image_path=None):
    spec, _ = validate_session(data)
    gt = data.get("ground_truth")
    if not isinstance(gt, dict):
        gt = {}
    # Coerce to scalars: malformed JSON may carry list/dict here, which would break .get()/f-strings.
    persona = spec.get("persona")
    persona = str(persona) if persona not in (None, "") else "client"
    modality = spec.get("modality")
    modality = modality if isinstance(modality, str) else ""
    formulation = FORMULATIONS.get(modality, FORMULATIONS["cbt"])

    L = [
        frontmatter([
            ("persona", persona),
            ("modality", modality),
            ("session_position", spec.get("session_position", "")),
            ("type", "case-conceptualization-card"),
            ("synthetic", True),
            ("not_clinical_advice", True),
        ]),
        "",
        f"> {WATERMARK}",
        f"> {CARD_NOTE}",
        "",
        f"# Case Card — {persona} ({modality})",
        "",
    ]

    if image_path:
        L += [f"![Synthetic portrait of {persona}]({image_path})", ""]
    else:
        L += [
            "<!-- PORTRAIT: generate with the gpt-image-2 skill, then embed the path here. -->",
            f"<!-- Suggested prompt:\n{portrait_prompt(persona, modality)}\n-->",
            "",
        ]

    L += ["## Snapshot", "<!-- FILL: one-paragraph who-they-are, in clinical-summary voice -->", ""]
    L += ["## Presenting issue", "<!-- FILL: surface complaint and what's underneath -->", ""]

    L += [f"## Formulation ({modality or 'general'})"]
    for heading, hint in formulation:
        L += [f"### {heading}", f"<!-- FILL: {hint} -->", ""]

    themes = as_str_list(gt.get("themes"))
    L += ["## Working themes"]
    L += [f"- {t}" for t in themes] if themes else ["<!-- FILL: 2–4 themes -->"]
    L += [""]

    actions = as_str_list(gt.get("action_items"))
    L += ["## Goals & between-session experiments"]
    L += [f"- [ ] {a}" for a in actions] if actions else ["<!-- FILL: agreed experiments -->"]
    L += [""]

    arc = gt.get("emotional_arc")
    arc = str(arc) if arc else ""
    L += ["## Emotional arc", arc if arc else "<!-- FILL: arc across the session -->", ""]

    return "\n".join(L).rstrip() + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--in", dest="inp", required=True, help="authored session JSON")
    p.add_argument("--image", help="path to an already-generated portrait to embed")
    p.add_argument("--out", help="output path (default: stdout)")
    p.add_argument("--print-prompt", action="store_true",
                   help="print only the gpt-image-2 portrait prompt and exit")
    args = p.parse_args()

    try:
        with open(args.inp, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.inp}", file=sys.stderr)
        sys.exit(2)
    except (OSError, ValueError) as e:  # ValueError: JSON decode / bad UTF-8 / oversized ints
        print(f"ERROR: could not parse JSON ({e})", file=sys.stderr)
        sys.exit(2)

    try:
        if args.print_prompt:
            spec, _ = validate_session(data)
            print(portrait_prompt(spec.get("persona"), spec.get("modality")))
            return
        card = build_card(data, image_path=args.image)
    except SessionError as e:
        print(f"ERROR: invalid session JSON — {e}", file=sys.stderr)
        sys.exit(2)

    if args.out:
        write_text(args.out, card)
        print(f"Wrote card: {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(card)


if __name__ == "__main__":
    run_cli(main)
