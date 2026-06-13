#!/usr/bin/env python3
"""Read-only disk-cleanup survey. Measures every registered target + discovers unlisted
caches, classifies by risk, emits a compact summary. Touches nothing.

  python3 survey.py            # human summary
  python3 survey.py --json     # machine summary (for the agent / clean.py)

Sizes are APPROXIMATE (du block counts on APFS). Output is deterministically sorted.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # import lib regardless of CWD
import lib


def measure_targets(reg: dict) -> list[dict]:
    rows = []
    for t in reg["targets"]:
        if t.get("method") == "advisory":
            paths = [str(lib.expand(p)) for p in t.get("paths", [])]
            present = [p for p in paths if lib.expand(p).exists()]
            size = sum(lib.du_bytes(lib.expand(p)) for p in present)
            rows.append({**_base(t), "bytes": size, "human": lib.human(size),
                         "exists": bool(present), "advisory": True})
            continue
        paths = lib.resolve_target_paths(t)
        size = sum(lib.du_bytes(p) for p in paths)
        rows.append({**_base(t), "bytes": size, "human": lib.human(size),
                     "exists": bool(paths), "n_paths": len(paths), "advisory": False})
    rows.sort(key=lambda r: (-r.get("priority", 0), -r["bytes"]))
    return rows


def _base(t: dict) -> dict:
    return {"id": t["id"], "category": t["category"], "risk": t["risk"],
            "method": t["method"], "priority": t.get("priority", 0), "note": t.get("note", "")}


def discover(reg: dict, min_mb: int) -> list[dict]:
    """Caches >min_mb under common roots not already named by a target."""
    known = set()
    for t in reg["targets"]:
        for p in t.get("paths", []):
            known.add(str(lib.canonical(p)))
    out = []
    for root in ["~/Library/Caches", "~/.cache", "~/Library/Application Support"]:
        base = lib.expand(root)
        if not base.exists():
            continue
        for child in sorted(base.iterdir(), key=lambda x: x.name):
            if child.is_symlink() or str(lib.canonical(child)) in known:
                continue
            b = lib.du_bytes(child)
            if b >= min_mb * 1024 * 1024:
                out.append({"path": str(child), "bytes": b, "human": lib.human(b)})
    out.sort(key=lambda r: -r["bytes"])
    return out[:20]


def build(args) -> dict:
    reg = lib.load_json("targets.json")
    cfg = lib.load_config()["defaults"]
    min_mb = args.min_mb or cfg.get("min_size_mb", 10)
    rows = measure_targets(reg)
    totals = {}
    for r in rows:
        if not r["advisory"]:
            totals[r["risk"]] = totals.get(r["risk"], 0) + r["bytes"]
    flags = []
    for r in rows:
        if r["id"] == "crashpad-dumps" and r["bytes"] > 1e9:
            flags.append(f"crashpad-dumps={r['human']} → an app is crash-looping (update/reinstall it)")
    return {
        "disk": lib.disk(),
        "targets": [r for r in rows if r["bytes"] >= min_mb * 1024 * 1024 or r["advisory"]
                    or r["method"] in ("command", "simctl")],
        "totals_by_risk": {k: {"bytes": v, "human": lib.human(v)} for k, v in totals.items()},
        "uncategorized": discover(reg, max(min_mb, 100)),
        "flags": flags,
    }


def render(s: dict) -> str:
    d = s["disk"]
    out = [f"DISK  {d['avail_gb']}G free / {d['total_gb']}G ({d['used_pct']}% used)", ""]
    safe = s["totals_by_risk"].get("safe", {}).get("human", "0B")
    med = s["totals_by_risk"].get("medium", {}).get("human", "0B")
    out.append(f"RECOVERABLE  safe={safe}  medium={med}")
    if s["flags"]:
        out += ["", "FLAGS"] + [f"  ⚠ {f}" for f in s["flags"]]
    out += ["", "TARGETS (size-sorted within priority)"]
    for r in s["targets"]:
        tag = "ADVISORY" if r["advisory"] else r["risk"].upper()
        out.append(f"  {r['human']:>7}  [{tag:<8}] {r['id']:<26} {r['note'][:60]}")
    if s["uncategorized"]:
        out += ["", "UNCATEGORIZED (>100M, unknown — decide manually)"]
        for u in s["uncategorized"]:
            out.append(f"  {u['human']:>7}  {u['path']}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-mb", type=int, default=0)
    args = ap.parse_args()
    s = build(args)
    print(json.dumps(s, indent=2) if args.json else render(s))


if __name__ == "__main__":
    main()
