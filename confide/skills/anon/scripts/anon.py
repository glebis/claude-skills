#!/usr/bin/env python3
"""confide:anon — local de-identification of a transcript file or folder.

Runs the layered local stack from shared/confide_core.py over each input file and
writes, next to it (or to --out), a redacted GREEN copy (<name>.green.md) plus a
counts-only stats file (<name>.stats.json).

Privacy invariants enforced here:
- The ORIGINAL PII text is NEVER written or printed. The only artifact containing
  transformed text is the GREEN file (placeholders only).
- stdout and the stats JSON carry COUNTS ONLY (by type / by layer, redaction rate).
- Everything runs locally per config; no raw text leaves the machine in this script.

Usage:
    python3 anon.py PATH [--layers regex,natasha,llm] [--out DIR] [--dry-run]
"""
import argparse
import json
import os
import sys

# Import the shared core via ../../shared relative to this file (robust to cwd).
_HERE = os.path.dirname(os.path.abspath(__file__))
_SHARED = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "shared"))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)
import confide_core as core  # noqa: E402

# Files we treat as inputs. We deliberately skip our own outputs so a folder can be
# re-run without redacting the already-redacted GREEN copies.
_INPUT_EXTS = (".md", ".txt")
_SKIP_SUFFIXES = (".green.md", ".stats.json")


# --------------------------------------------------------------------- helpers
def _is_input(name):
    if name.endswith(_SKIP_SUFFIXES):
        return False
    return name.endswith(_INPUT_EXTS)


def _green_path(src, out=None):
    d, base = os.path.split(src)
    stem = base
    for ext in _INPUT_EXTS:
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break
    dest_dir = out if out else d
    return (
        os.path.join(dest_dir, stem + ".green.md"),
        os.path.join(dest_dir, stem + ".stats.json"),
    )


def summarize(stats, name=None):
    """One-line, COUNTS-ONLY summary for stdout. Never contains PII values."""
    by_type = ", ".join(f"{t}:{c}" for t, c in sorted(stats.get("by_type", {}).items())) or "-"
    by_layer = ", ".join(f"{l}:{c}" for l, c in sorted(stats.get("by_layer", {}).items())) or "-"
    prefix = f"{name}: " if name else ""
    return (
        f"{prefix}chars={stats.get('chars', 0)} "
        f"spans={stats.get('spans_total', 0)}(merged {stats.get('spans_merged', 0)}) "
        f"rate={stats.get('redaction_rate', 0.0)} "
        f"| types[{by_type}] layers[{by_layer}]"
    )


# --------------------------------------------------------------------- core ops
def process_file(path, cfg, out=None, dry=False):
    """De-identify a single file.

    Reads the original, runs core.anonymize, and (unless dry) writes the GREEN
    redacted copy + counts-only stats JSON. Returns a dict with the stats and the
    written paths (None when dry). The original is read but never rewritten.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    result = core.anonymize(text, cfg)
    stats = result["stats"]
    green_path, stats_path = _green_path(path, out)

    if dry:
        return {"stats": stats, "green": None, "stats_path": None, "name": os.path.basename(path)}

    if out:
        os.makedirs(out, exist_ok=True)
    # GREEN copy: redacted text ONLY (placeholders). Original PII is never written.
    with open(green_path, "w", encoding="utf-8") as f:
        f.write(result["redacted_text"])
    # stats: counts only.
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    return {"stats": stats, "green": green_path, "stats_path": stats_path,
            "name": os.path.basename(path)}


def process_path(path, cfg, out=None, dry=False):
    """Process a file or every .md/.txt input in a directory (non-recursive).

    Skips already-emitted .green.md / .stats.json so folders are re-runnable.
    Returns a list of per-file result dicts.
    """
    if os.path.isdir(path):
        names = sorted(n for n in os.listdir(path) if _is_input(n))
        targets = [os.path.join(path, n) for n in names]
    else:
        targets = [path]
    return [process_file(t, cfg, out=out, dry=dry) for t in targets]


def aggregate(results):
    """Combine per-file stats into a counts-only aggregate (no PII)."""
    agg = {"files": len(results), "chars": 0, "spans_total": 0, "spans_merged": 0,
           "by_type": {}, "by_layer": {}}
    for r in results:
        s = r["stats"]
        agg["chars"] += s.get("chars", 0)
        agg["spans_total"] += s.get("spans_total", 0)
        agg["spans_merged"] += s.get("spans_merged", 0)
        for t, c in s.get("by_type", {}).items():
            agg["by_type"][t] = agg["by_type"].get(t, 0) + c
        for l, c in s.get("by_layer", {}).items():
            agg["by_layer"][l] = agg["by_layer"].get(l, 0) + c
    agg["redaction_rate"] = round(
        sum(r["stats"].get("redaction_rate", 0.0) for r in results) / len(results), 4
    ) if results else 0.0
    return agg


# --------------------------------------------------------------------- cli
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="confide:anon — local PII redaction. Writes a GREEN copy + counts-only stats. "
                    "Never prints or writes original PII."
    )
    ap.add_argument("path", help="file or directory (.md/.txt) to de-identify")
    ap.add_argument("--layers", help="override layers, e.g. regex,natasha,llm")
    ap.add_argument("--out", help="output directory (default: next to each input)")
    ap.add_argument("--dry-run", action="store_true", help="compute stats only; write no files")
    args = ap.parse_args(argv)

    cfg = core.load_config()
    if args.layers:
        cfg = dict(cfg)
        cfg["layers"] = [x.strip() for x in args.layers.split(",") if x.strip()]

    if not os.path.exists(args.path):
        print(f"error: path not found: {args.path}", file=sys.stderr)
        return 2

    results = process_path(args.path, cfg, out=args.out, dry=args.dry_run)
    if not results:
        print("no .md/.txt input files found", file=sys.stderr)
        return 1

    mode = " (dry-run, no files written)" if args.dry_run else ""
    print(f"confide:anon — local-only, layers={cfg['layers']}{mode}")
    for r in results:
        line = summarize(r["stats"], name=r["name"])
        if r["green"]:
            line += f"  -> {os.path.basename(r['green'])}"
        print(line)
    if len(results) > 1:
        print("AGGREGATE: " + summarize(aggregate(results), name=f"{len(results)} files"))
    print("Counts only above — nothing printed is PII. Human review still required before sharing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
