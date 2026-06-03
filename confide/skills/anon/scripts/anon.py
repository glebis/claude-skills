#!/usr/bin/env python3
"""confide:anon — local de-identification of a transcript file or folder.

Runs the layered local stack from shared/confide_core.py over each input file and
writes, next to it (or to --out), a redacted GREEN copy (<name>.green.md) plus a
counts-only stats file (<name>.stats.json).

By DEFAULT it emits a local **reversible map**: unique, coreferent placeholders
reserved-sentinel placeholders ([CONFIDE_PERSON_0001], [CONFIDE_EMAIL_0001]...) in
the GREEN file plus a sibling <name>.map.json (structured schema: schema_version,
doc_id, green_sha256, created, entries[]) that maps each placeholder to its original
value. That map is the SECRET — it is the ONLY artifact that contains originals. It
is written 0600 and *.map.json / *.view.html / *.restored.md lines are added to a
.gitignore in the output dir so they can never be committed. Pair with
confide:rehydrate to put real values back into a cloud analysis of the GREEN text.
Use --no-map for the legacy non-reversible typed_placeholder ([PERSON]) style.

Privacy invariants enforced here:
- The ORIGINAL PII text is NEVER written to the GREEN file or printed. The only
  artifact containing originals is the local, gitignored, 0600 <name>.map.json.
- stdout and the stats JSON carry COUNTS ONLY (by type / by layer, redaction rate).
- Everything runs locally per config; no raw text leaves the machine in this script.

Usage:
    python3 anon.py PATH [--layers regex,natasha,llm] [--out DIR] [--dry-run] [--no-map]
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
_SKIP_SUFFIXES = (".green.md", ".stats.json", ".map.json", ".restored.md")


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
        os.path.join(dest_dir, stem + ".map.json"),
    )


# local-only artifacts that must never be committed (all carry originals or PII-derived data)
_GITIGNORE_LINES = ("*.map.json", "*.view.html", "*.restored.md")
# cloud-sync folder markers — a secret map under one of these would be uploaded.
_CLOUD_MARKERS = ("/iCloud", "Mobile Documents", "/Dropbox", "/OneDrive", "/Google Drive", "/GoogleDrive")


def _ensure_gitignore(dest_dir):
    """Ensure the local-only artifact globs are in a .gitignore in dest_dir so the
    secret map / view / restored files can never be committed."""
    gi = os.path.join(dest_dir, ".gitignore")
    try:
        existing = ""
        if os.path.exists(gi):
            with open(gi, encoding="utf-8") as f:
                existing = f.read()
        have = set(existing.split())
        missing = [l for l in _GITIGNORE_LINES if l not in have]
        if missing:
            with open(gi, "a", encoding="utf-8") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write("\n".join(missing) + "\n")
    except OSError:
        pass  # best-effort; never block redaction on gitignore write


def _cloud_warning(dest_dir):
    """Return a warning string if dest_dir looks cloud-synced (so the secret map would
    be uploaded), else None. Detection is by path substring."""
    p = os.path.abspath(dest_dir or ".")
    for marker in _CLOUD_MARKERS:
        if marker in p:
            return (f"WARNING: output path looks cloud-synced ({marker.strip('/')}). "
                    "The secret *.map.json would be uploaded off your machine. "
                    "Write the map to a LOCAL (non-synced) folder instead.")
    return None


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
def _detect_spans(text, cfg):
    """Run the enabled detection layers and return the raw spans (no redaction yet)."""
    layers = cfg.get("layers", core.DEFAULTS["layers"])
    spans = []
    if "regex" in layers:
        spans += core.detect_regex(text)
    if "natasha" in layers:
        spans += core.detect_natasha(text)
    if "llm" in layers:
        spans += core.detect_llm(text, cfg)
    return spans


def _stats_from_spans(text, spans):
    """Counts-only stats (mirrors core.anonymize). Never carries PII values."""
    merged = core.merge_spans(spans)
    by_type, by_layer = {}, {}
    for s in spans:
        by_type[s.type] = by_type.get(s.type, 0) + 1
        by_layer[s.source] = by_layer.get(s.source, 0) + 1
    masked = sum(s.end - s.start for s in merged)
    return {
        "chars": len(text), "spans_total": len(spans), "spans_merged": len(merged),
        "by_type": by_type, "by_layer": by_layer,
        "redaction_rate": round(masked / len(text), 4) if text else 0.0,
    }


def process_file(path, cfg, out=None, dry=False, reversible=True):
    """De-identify a single file.

    Reads the original, detects PII spans, and (unless dry) writes the GREEN copy +
    counts-only stats JSON. By default (reversible=True) the GREEN copy uses UNIQUE
    reserved-sentinel placeholders ([CONFIDE_EMAIL_0001]...) and a secret <name>.map.json (0600,
    gitignored) is written next to it — the ONLY artifact with originals. With
    reversible=False it falls back to the non-reversible typed_placeholder ([EMAIL])
    style and writes no map. The original is read but never rewritten.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    spans = _detect_spans(text, cfg)
    stats = _stats_from_spans(text, spans)
    green_path, stats_path, map_path = _green_path(path, out)

    if reversible:
        green_text, mapping = core.redact_reversible(text, spans)
    else:
        green_text = core.redact(text, spans, cfg.get("redaction_style", "typed_placeholder"))
        mapping = None

    if dry:
        return {"stats": stats, "green": None, "stats_path": None, "map_path": None,
                "cloud_warning": None, "name": os.path.basename(path)}

    dest_dir = out if out else os.path.dirname(green_path)
    if out:
        os.makedirs(out, exist_ok=True)
    # GREEN copy: redacted text ONLY (placeholders). Original PII is never written here.
    with open(green_path, "w", encoding="utf-8") as f:
        f.write(green_text)
    # stats: counts only.
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    written_map = None
    cloud_warn = None
    if mapping is not None:
        # The map is the SECRET (structured schema, includes green sha256): write
        # 0600, and gitignore *.map.json (+ view/restored) in the out dir.
        fd = os.open(map_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
        finally:
            # ensure perms even if file pre-existed with other perms
            os.chmod(map_path, 0o600)
        _ensure_gitignore(dest_dir or ".")
        written_map = map_path
        cloud_warn = _cloud_warning(dest_dir or ".")

    return {"stats": stats, "green": green_path, "stats_path": stats_path,
            "map_path": written_map, "cloud_warning": cloud_warn,
            "name": os.path.basename(path)}


def process_path(path, cfg, out=None, dry=False, reversible=True):
    """Process a file or every .md/.txt input in a directory (non-recursive).

    Skips already-emitted .green.md / .stats.json / .map.json so folders are
    re-runnable. Returns a list of per-file result dicts.
    """
    if os.path.isdir(path):
        names = sorted(n for n in os.listdir(path) if _is_input(n))
        targets = [os.path.join(path, n) for n in names]
    else:
        targets = [path]
    return [process_file(t, cfg, out=out, dry=dry, reversible=reversible) for t in targets]


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
    ap.add_argument("--no-map", action="store_true",
                    help="disable the reversible map; emit non-unique [TYPE] placeholders, no map.json")
    args = ap.parse_args(argv)

    cfg = core.load_config()
    if args.layers:
        cfg = dict(cfg)
        cfg["layers"] = [x.strip() for x in args.layers.split(",") if x.strip()]

    if not os.path.exists(args.path):
        print(f"error: path not found: {args.path}", file=sys.stderr)
        return 2

    reversible = not args.no_map
    results = process_path(args.path, cfg, out=args.out, dry=args.dry_run, reversible=reversible)
    if not results:
        print("no .md/.txt input files found", file=sys.stderr)
        return 1

    mode = " (dry-run, no files written)" if args.dry_run else ""
    map_mode = "reversible map (local, gitignored, 0600)" if reversible else "no-map (non-reversible [TYPE])"
    print(f"confide:anon — local-only, layers={cfg['layers']}, {map_mode}{mode}")
    for r in results:
        line = summarize(r["stats"], name=r["name"])
        if r["green"]:
            line += f"  -> {os.path.basename(r['green'])}"
        if r.get("map_path"):
            line += f" + {os.path.basename(r['map_path'])}"
        print(line)
        if r.get("cloud_warning"):
            print(r["cloud_warning"], file=sys.stderr)
    if len(results) > 1:
        print("AGGREGATE: " + summarize(aggregate(results), name=f"{len(results)} files"))
    print("Counts only above — nothing printed is PII. Human review still required before sharing.")
    if reversible and not args.dry_run:
        print("The *.map.json is the SECRET (originals). It stays LOCAL, is 0600 + gitignored. "
              "Use confide:rehydrate to restore real values into a cloud analysis of the GREEN text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
