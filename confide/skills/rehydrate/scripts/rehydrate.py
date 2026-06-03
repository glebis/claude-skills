#!/usr/bin/env python3
"""confide:rehydrate — restore real values into an analysis produced from GREEN text.

Completes the local round-trip:
    redact (confide:anon, reversible) -> cloud-analyze the GREEN placeholders ->
    rehydrate LOCALLY with your own <name>.map.json -> real analysis.

Input is an analysis/text file full of reserved-sentinel placeholders
([CONFIDE_PERSON_0001], [CONFIDE_DATE_0002], possibly mangled by the LLM to
"CONFIDE_PERSON_0001" or "[CONFIDE PERSON 0001]" — but always keeping the full
CONFIDE_TYPE_NNNN core) plus the secret <name>.map.json written by confide:anon
(auto-found as a sibling if --map omitted). We replace every placeholder with its
mapped original via core.rehydrate, write <name>.restored.md next to the input, and
print a COUNTS-ONLY restore summary. Ordinary prose ("Person 1") is never touched,
and --verify-green warns if the map doesn't belong to the supplied GREEN document.

Privacy invariants:
- Runs entirely LOCALLY on the user's OWN map. The map never leaves the machine;
  this script never fetches or transmits anything.
- stdout carries COUNTS ONLY (restored N, unmatched M) — restored PII is written to
  the local file but never echoed to stdout.
- Placeholders not present in the map are reported as `unmatched` and LEFT IN PLACE
  (a possible LLM hallucination — we never invent a value for them).

Usage:
    python3 rehydrate.py ANALYSIS_FILE [--map <name>.map.json] [--out PATH]
"""
import argparse
import json
import os
import re
import sys

# Import the shared core via ../../../shared relative to this file (robust to cwd).
_HERE = os.path.dirname(os.path.abspath(__file__))
_SHARED = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "shared"))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)
import confide_core as core  # noqa: E402


def rehydrate_text(text, mapping):
    """Thin wrapper over core.rehydrate. Returns (restored_text, {restored, unmatched})."""
    return core.rehydrate(text, mapping)


def _auto_find_map(analysis_path):
    """Find a sibling <stem>.map.json for the given analysis file.

    Tries the analysis stem, then strips known confide suffixes (.green, .restored)
    so an analysis derived from session.green.md finds session.map.json.
    """
    d, base = os.path.split(analysis_path)
    stem = base
    for ext in (".md", ".txt"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break
    candidates = [stem]
    for suf in (".green", ".restored", ".analysis"):
        if stem.endswith(suf):
            candidates.append(stem[: -len(suf)])
    for c in candidates:
        cand = os.path.join(d or ".", c + ".map.json")
        if os.path.exists(cand):
            return cand
    return None


def _restored_path(analysis_path, out=None):
    if out:
        return out
    d, base = os.path.split(analysis_path)
    stem = base
    for ext in (".md", ".txt"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break
    return os.path.join(d or ".", stem + ".restored.md")


def _verify_green(mapping, green_path):
    """Compare the map's recorded green_sha256 against the sha256 of green_path.

    Returns (ok, warning_or_None). ok is True only when the map carries a
    green_sha256 AND it matches the supplied green file. A mismatch means this is
    the WRONG map for this document — warn loudly, never auto-pair blindly."""
    recorded = mapping.get("green_sha256") if isinstance(mapping, dict) else None
    if not recorded:
        return None, ("WARNING: --verify-green given but the map has no green_sha256 "
                      "(legacy/flat map) — cannot verify it belongs to this document.")
    try:
        with open(green_path, encoding="utf-8") as f:
            actual = core.green_sha256(f.read())
    except OSError as e:
        return False, f"WARNING: could not read --verify-green file ({type(e).__name__})."
    if actual != recorded:
        return False, ("WARNING: green sha256 MISMATCH — this map does NOT belong to the "
                       "supplied green document. Rehydration may corrupt the text. "
                       "Use the correct <name>.map.json for this document.")
    return True, None


def process(analysis_path, map_path=None, out=None, quiet=False, verify_green=None):
    """Rehydrate an analysis file against its map. Writes <name>.restored.md.

    Returns a dict: {restored, unmatched, restored_path, map_path}. Prints a
    counts-only summary unless quiet. Never echoes restored PII to stdout.
    `verify_green` (a path to the GREEN file) warns if the map's green_sha256 does
    not match — i.e. it is the wrong map for this document.
    """
    if map_path is None:
        map_path = _auto_find_map(analysis_path)
        if map_path is None:
            raise SystemExit(
                f"error: no --map given and no sibling *.map.json found for {analysis_path}"
            )
    with open(analysis_path, encoding="utf-8") as f:
        text = f.read()
    with open(map_path, encoding="utf-8") as f:
        try:
            mapping = json.load(f)
        except json.JSONDecodeError as e:
            raise SystemExit(f"error: malformed map.json ({type(e).__name__})")

    verify_ok, verify_warn = (None, None)
    if verify_green:
        verify_ok, verify_warn = _verify_green(mapping, verify_green)

    restored_text, summary = rehydrate_text(text, mapping)
    dest = _restored_path(analysis_path, out)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(restored_text)

    result = {"restored": summary["restored"], "unmatched": summary["unmatched"],
              "restored_path": dest, "map_path": map_path,
              "verify_ok": verify_ok, "verify_warning": verify_warn}
    if not quiet:
        # COUNTS ONLY — never print restored PII.
        print(f"confide:rehydrate — local-only (your own map: {os.path.basename(map_path)})")
        if verify_warn:
            print(verify_warn)
        print(f"restored {summary['restored']} placeholder(s), "
              f"{summary['unmatched']} unmatched (left in place)")
        if summary["unmatched"]:
            print("WARNING: unmatched placeholders are NOT in your map — possible LLM "
                  "hallucination. They were left untouched, not invented.")
        print(f"-> {os.path.basename(dest)} (local; contains originals — do not share/commit)")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="confide:rehydrate — restore real values into a placeholder analysis, "
                    "LOCALLY, using your own map. Prints counts only; never echoes PII."
    )
    ap.add_argument("analysis", help="analysis/text file containing placeholders")
    ap.add_argument("--map", dest="map_path", help="<name>.map.json (default: auto-find sibling)")
    ap.add_argument("--out", help="output path (default: <name>.restored.md next to input)")
    ap.add_argument("--verify-green", dest="verify_green",
                    help="GREEN file to check the map's green_sha256 against (warns on mismatch)")
    args = ap.parse_args(argv)

    if not os.path.exists(args.analysis):
        print(f"error: file not found: {args.analysis}", file=sys.stderr)
        return 2
    process(args.analysis, map_path=args.map_path, out=args.out,
            verify_green=args.verify_green)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
