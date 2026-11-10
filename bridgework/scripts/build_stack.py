#!/usr/bin/env python3
"""Build a Bridgework site from a confirmed stack file.

  build_stack.py STACK.json [--out ~/.bridgework/site]

STACK.json (see references/stack-format.md):
  {"name": "...", "observed": "YYYY-MM-DD",
   "places": [{"id": "home", "label": "Mac mini (LAN)"}],          optional label overrides or additions
   "parts": [{"use": "obsidian", "evidence": "installed", "signals": [...]},   catalog tool, optional overrides
             {"id": "my-db", "name": "...", "domain": "...", "place": "...", "act": "...",
              "takes": [{"type": "record", "label": "..."}], "gives": [...], "evidence": "user-confirmed"}],
   "gaps": [{"from": "a", "to": "b", "statement": "Why this is not a working route."}]}

Copies the app, writes data/ for this stack, and drops built-in examples whose parts are missing.
Exits with a list of problems instead of writing a broken site.
"""
import argparse, copy, datetime, json, os, re, shutil, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
APP = SKILL / "assets/app"
BOUNDARY = {"device": "device", "mac": "local", "home": "lan", "vps": "own-cloud", "hosted": "vendor"}
KIND = {"app": "App present", "path": "Folder present", "cli": "Command on PATH", "mcp": "MCP server configured", "models": "Local models present", "key": "Credential variable set"}


def load(p): return json.loads(Path(p).read_text())


def build(stack, out):
    demo = load(APP / "data/facts.json")
    catalog = {t["id"]: t for t in load(SKILL / "scripts/catalog.json")["tools"]}
    observed = stack.get("observed") or datetime.date.today().isoformat()
    places = {p["id"]: p for p in demo["places"]}
    for p in stack.get("places", []): places[p["id"]] = {**places.get(p["id"], {}), **p}
    T = {k: {x["id"] for x in demo[k]} for k in ("types", "domains", "evidence")}
    errs, parts = [], []

    for i, raw in enumerate(stack.get("parts", [])):
        base = copy.deepcopy(catalog.get(raw.get("use"), {})) if raw.get("use") else {}
        if raw.get("use") and not base: errs.append(f"parts[{i}]: '{raw['use']}' is not in the catalog. Write it as a custom part."); continue
        r = {**base, **{k: v for k, v in raw.items() if k not in ("use", "signals")}}
        r.pop("detect", None)
        r["id"] = r.get("id") or base.get("id")
        where = r.get("name") or r.get("id") or f"parts[{i}]"
        for k in ("id", "name", "domain", "place", "act"):
            if not r.get(k): errs.append(f"{where}: missing {k}")
        if r.get("id") and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", r["id"]): errs.append(f"{where}: id must be lowercase letters, digits and hyphens")
        if r.get("domain") and r["domain"] not in T["domains"]: errs.append(f"{where}: domain '{r['domain']}' must be one of {sorted(T['domains'])}")
        if r.get("place") and r["place"] not in places: errs.append(f"{where}: place '{r['place']}' must be one of {sorted(places)} or be added under places")
        r["evidence"] = r.get("evidence") or ("user-confirmed" if not raw.get("signals") else "installed")
        if r["evidence"] not in T["evidence"]: errs.append(f"{where}: evidence '{r['evidence']}' must be one of {sorted(T['evidence'])}")
        r.setdefault("takes", []); r.setdefault("gives", [])
        for k in ("takes", "gives"):
            for x in r[k]:
                if x.get("type") not in T["types"]: errs.append(f"{where}: {k} type '{x.get('type')}' must be one of {sorted(T['types'])}")
        if r.get("place"): r.setdefault("boundary", BOUNDARY.get(r["place"], "vendor"))
        r.setdefault("does", [r.get("act", "").split(" ")[0] or "works"])
        r.setdefault("asThird", {"adds": r.get("name", "it"), "then": "it can add what it gives to the route"})
        r.setdefault("unknown", [])
        sig = raw.get("signals") or []
        src = "audit" if sig else "interview"
        r["gates"] = [{"label": KIND.get(s["kind"], s["kind"]), "state": "pass", "detail": s["detail"], "src": "audit"} for s in sig] or \
                     [{"label": "In use", "state": "pass", "detail": "The owner said so in the interview", "src": "interview"}]
        r["gates"].append({"label": "Working call", "state": "unknown", "detail": "Not run. Presence is not proof that it works.", "src": src})
        r.setdefault("constraints", {}); r["constraints"].setdefault("auth", "Not tested")
        r["sources"] = [src]
        parts.append(r)

    ids = [p["id"] for p in parts if p.get("id")]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup: errs.append("duplicate ids: " + ", ".join(dup))
    if len(parts) < 2: errs.append("a stack needs at least two parts")
    have = set(ids)
    for g in stack.get("gaps", []):
        if g.get("from") not in have or g.get("to") not in have or not g.get("statement"): errs.append(f"gap {g}: needs from and to ids in this stack, and a statement")
    if errs:
        sys.exit("Not built. Fix these in the stack file:\n- " + "\n- ".join(errs))

    facts = {k: demo[k] for k in ("boundaries", "domains", "types", "evidence")}
    facts["places"] = list(places.values())
    facts["meta"] = {"observed_date": observed, "timezone": demo["meta"].get("timezone", "UTC"), "stack_name": stack.get("name") or "My stack",
                     "note": "Built from a read-only audit and an interview. Nothing is connected and no bridge has been run. Every combination is a hypothesis, even when its parts are present."}
    facts["sources"] = {"audit": {"title": "Local audit (presence only)", "where": "~/.bridgework/audit.json", "checked": observed},
                        "interview": {"title": "Interview with the owner", "checked": observed},
                        "examples": {"title": "Bridgework's built-in examples", "checked": demo["meta"]["observed_date"]}}
    facts["gaps"] = [{**g, "source": g.get("source", "interview")} for g in stack.get("gaps", [])]
    facts["resources"] = parts

    bridges = load(APP / "data/bridges.json")
    seeds = []
    for s in bridges["seeds"]:
        if s["from"] in have and s["to"] in have:
            s = copy.deepcopy(s); s["source"] = "examples"
            s["thirds"] = {k: v for k, v in (s.get("thirds") or {}).items() if k in have}
            loc = (s.get("variants") or {}).get("local")
            if loc and not set(loc.get("parts", [])) <= have: s["variants"].pop("local")
            seeds.append(s)
    kept = {s["id"] for s in seeds}
    bridges["seeds"] = seeds
    bridges["swaps"] = [w for w in bridges["swaps"] if w["from"] in have and w["to"] in have]
    costs = load(APP / "data/costs.json")
    costs["opportunities"] = [o for o in costs["opportunities"] if set(o["existing"]) <= have and (not o.get("bridge") or o["bridge"] in kept)]

    out = Path(os.path.expanduser(out))
    if out.exists():
        if not (out / ".bridgework-site").exists(): sys.exit(f"{out} exists and was not made by this script. Choose another --out. Nothing was written.")
        shutil.rmtree(out)  # only a folder this script built earlier
    shutil.copytree(APP, out, ignore=shutil.ignore_patterns("tests", "node_modules", "package.json"))
    for name, data in (("facts", facts), ("bridges", bridges), ("costs", costs)):
        (out / f"data/{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    (out / ".bridgework-site").write_text("Built by bridgework/scripts/build_stack.py. Safe to rebuild.\n")
    return {"parts": len(parts), "examples": len(seeds), "unlocks": len(costs["opportunities"]), "out": str(out)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stack"); ap.add_argument("--out", default="~/.bridgework/site")
    a = ap.parse_args()
    r = build(load(os.path.expanduser(a.stack)), a.out)
    print(f"Built {r['parts']} parts, {r['examples']} built-in examples kept, {r['unlocks']} unlocks kept. Site: {r['out']}")


if __name__ == "__main__":
    main()
