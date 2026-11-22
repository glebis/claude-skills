#!/usr/bin/env python3
"""Resolve the Fathom transcript for a lab meeting (SKILL Step 1).

  find_transcript.py DATE [--slug SLUG] [--lab NN] [--vault DIR] [--json]

Searches ${VAULT}/Sessions/ (where transcripts live since the 2026-06-12
restructure) and the vault root, trying each registered lab's `vault_names`
patterns from labs.json (e.g. "goal-driven-ai-{lab}", "claude-code-lab-{lab}").
Without --slug every registered lab is tried. Prints path, slug, lab; exit 1
if nothing matches.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lab_layout  # noqa: E402


def candidates(vault, date):
    for d in (vault / "Sessions", vault):
        if d.is_dir():
            yield from sorted(d.glob(f"{date}-*.md"), key=lambda p: -p.stat().st_mtime)


def find(date, slug=None, lab=None, vault=None):
    vault = Path(vault or os.path.expanduser(os.environ.get("VAULT_DIR", "~/Brains/brain")))
    reg = lab_layout.load_registry()
    slugs = [slug] if slug else list(reg)
    for path in candidates(vault, date):
        stem = path.stem[len(date) + 1:]
        # Most specific pattern wins: "goal-driven-ai-01-продвинутая-группа" is the advanced
        # track's exact name, not the Saturday pattern plus a suffix.
        hits = []
        for s in slugs:
            for pat in reg.get(s, {}).get("vault_names", [f"{s}-lab-{{lab}}"]):
                # optional "-<descriptor>" suffix: calendar titles append the session kind,
                # e.g. 20261018-goal-driven-ai-01-продвинутая-группа.md (GDA 01 Sunday group)
                rx = "^" + re.escape(pat).replace(r"\{lab\}", r"(?P<lab>\d{1,3})") + r"(?P<suffix>-.+)?$"
                m = re.match(rx, stem)
                if m and (lab is None or m.groupdict().get("lab", lab).zfill(2) == lab.zfill(2)):
                    found = (m.groupdict().get("lab") or lab or "01").zfill(2)
                    hits.append({"path": str(path), "slug": s, "lab": found, "suffix": (m.group("suffix") or "").lstrip("-")})
        if hits:
            return min(hits, key=lambda h: len(h["suffix"]))
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("date"); p.add_argument("--slug"); p.add_argument("--lab"); p.add_argument("--vault")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    r = find(a.date, a.slug, a.lab, a.vault)
    if not r:
        print(f"no transcript for {a.date} (slug={a.slug or 'any'}) in Sessions/ or vault root", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(r) if a.json else "\n".join(f"{k}: {v}" for k, v in r.items()))


if __name__ == "__main__":
    main()
