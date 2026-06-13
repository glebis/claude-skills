#!/usr/bin/env python3
"""Deterministic disk-cleanup executor. DRY-RUN BY DEFAULT — prints the plan and touches
nothing unless you pass --go.

  python3 clean.py --preset safe                 # dry-run plan for the safe preset
  python3 clean.py --preset safe --go            # actually clean (safe only)
  python3 clean.py --ids cargo-registry-cache,go-mod-cache --go
  python3 clean.py --preset full --allow-medium --go --empty-trash

Safety (per audit):
  - every trashed path passes preflight(): canonical realpath, must be under an allowed
    root, must not be a symlink, never $HOME or /.
  - risk=safe runs automatically; risk=medium needs --allow-medium; risk=never is refused.
  - method=advisory never executes — it only prints guidance.
  - command-method freed bytes are measured by scope_path du-delta when declared, else "unknown".
"""

import argparse
import json
import subprocess
import sys

import lib


def select(reg, args) -> list[dict]:
    by_id = {t["id"]: t for t in reg["targets"]}
    if args.ids:
        chosen = [by_id[i] for i in args.ids.split(",") if i in by_id]
    else:
        risks = reg["presets"].get(args.preset, ["safe"])
        chosen = [t for t in reg["targets"] if t["risk"] in risks]
    skip = set(args.skip.split(",")) if args.skip else set()
    return [t for t in chosen if t["id"] not in skip]


def run(args):
    reg = lib.load_json("targets.json")
    roots = reg["allowed_roots"]
    disk_before = lib.disk()
    plan, advisories, refused, freed = [], [], [], 0

    for t in select(reg, args):
        if t["method"] == "advisory":
            advisories.append({"id": t["id"], "note": t["note"]})
            continue
        if t["risk"] == "never":
            refused.append({"id": t["id"], "reason": "risk=never"})
            continue
        if t["risk"] == "medium" and not args.allow_medium:
            refused.append({"id": t["id"], "reason": "medium risk needs --allow-medium"})
            continue

        if t["method"] == "command":
            plan.append({"id": t["id"], "action": " ".join(t["command"]), "bytes": _scope_size(t)})
            if args.go:
                freed += _run_command(t)
            continue

        if t["method"] == "simctl":
            plan.append({"id": t["id"], "action": "xcrun simctl delete unavailable", "bytes": 0})
            if args.go:
                try:
                    subprocess.run(["xcrun", "simctl", "delete", "unavailable"],
                                   capture_output=True, text=True, timeout=300)
                except subprocess.SubprocessError:
                    refused.append({"id": t["id"], "reason": "simctl failed"})
            continue

        # trash / find-trash / downloads-scan
        ok_paths, bad = [], []
        for p in lib.resolve_target_paths(t):
            ok, reason = lib.preflight(p, roots)
            (ok_paths if ok else bad).append((p, reason))
        size = sum(lib.du_bytes(p) for p, _ in ok_paths)
        # name the items for reviewable methods (downloads/node_modules sweeps trash many things)
        items = ([p.name for p, _ in ok_paths] if t["method"] in ("downloads-scan", "find-trash")
                 else [])
        plan.append({"id": t["id"], "action": f"trash {len(ok_paths)} path(s)",
                     "bytes": size, "items": items,
                     "rejected": [{"path": str(p), "why": r} for p, r in bad]})
        if args.go and ok_paths:
            okk, msg = lib.trash([p for p, _ in ok_paths])
            if okk:
                freed += size
            else:
                refused.append({"id": t["id"], "reason": f"trash failed: {msg}"})

    emptied = False
    if args.go and args.empty_trash:
        emptied, _ = lib.empty_trash()

    disk_after = lib.disk() if args.go else disk_before
    return {
        "mode": "EXECUTED" if args.go else "DRY-RUN (nothing touched — add --go to apply)",
        "preset": args.preset, "allow_medium": args.allow_medium,
        "plan": plan, "advisories": advisories, "refused": refused,
        "planned_bytes": sum(p["bytes"] for p in plan), "planned_human": lib.human(sum(p["bytes"] for p in plan)),
        "freed_bytes": freed, "freed_human": lib.human(freed),
        "trash_emptied": emptied,
        "disk_before": disk_before, "disk_after": disk_after,
    }


def _scope_size(t) -> int:
    sp = t.get("scope_path")
    return lib.du_bytes(lib.expand(sp)) if sp else 0


def _run_command(t) -> int:
    before = _scope_size(t)
    try:
        subprocess.run(t["command"], capture_output=True, text=True, timeout=300)
    except subprocess.SubprocessError:
        return 0
    if not t.get("scope_path"):
        return 0  # unmeasurable (e.g. brew) — reported as 0, real freed is "unknown"
    return max(0, before - _scope_size(t))


def render(r: dict) -> str:
    out = [f"=== {r['mode']} ===",
           f"planned: {r['planned_human']}" + (f"  freed: {r['freed_human']}" if r['mode'].startswith('EXEC') else "")]
    out.append("")
    for p in r["plan"]:
        out.append(f"  {lib.human(p['bytes']):>7}  {p['id']:<26} {p['action']}")
        for it in p.get("items", [])[:30]:
            out.append(f"           · {it}")
        if len(p.get("items", [])) > 30:
            out.append(f"           … +{len(p['items']) - 30} more")
        for rej in p.get("rejected", []):
            out.append(f"           ↳ SKIPPED {rej['path']} — {rej['why']}")
    if r["refused"]:
        out += ["", "REFUSED"] + [f"  {x['id']}: {x['reason']}" for x in r["refused"]]
    if r["advisories"]:
        out += ["", "ADVISORIES (manual — never auto-cleaned)"] + [f"  {a['id']}: {a['note']}" for a in r["advisories"]]
    if r["mode"].startswith("EXEC"):
        b, a = r["disk_before"], r["disk_after"]
        out += ["", f"disk: {b['avail_gb']}G → {a['avail_gb']}G free  (trash emptied: {r['trash_emptied']})"]
        if not r["trash_emptied"]:
            out.append("  note: freed space lands in Trash — empty it (or use --empty-trash) to reclaim.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", default="safe")
    ap.add_argument("--ids", help="comma-separated target ids (overrides --preset)")
    ap.add_argument("--skip", help="comma-separated ids to skip")
    ap.add_argument("--allow-medium", action="store_true", help="permit risk=medium targets")
    ap.add_argument("--go", action="store_true", help="actually execute (default is dry-run)")
    ap.add_argument("--empty-trash", action="store_true", help="empty Trash after (only with --go)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    r = run(args)
    print(json.dumps(r, indent=2) if args.json else render(r))


if __name__ == "__main__":
    sys.path.insert(0, str(lib.HERE))
    main()
