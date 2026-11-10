#!/usr/bin/env python3
"""Read-only scan of this Mac for parts of a tech stack.

Consent first: nothing is read unless categories are named with --categories.
Run --plan to see exactly what each category would read, without reading it.

Categories:
  apps    application names in /Applications, ~/Applications, /System/Applications, plus a few known folders
  clis    whether known command-line tools are on PATH (shutil.which; nothing is executed)
  mcp     MCP server NAMES from Claude and Cursor config files (never their env, args or values)
  models  local model names from Ollama and LM Studio model folders (folder names only)
  keys    NAMES of environment variables that look like credentials (never their values)

Never: reads secret values, runs a tool, opens a network connection, or writes outside --out.
"""
import argparse, datetime, json, os, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATS = ["apps", "clis", "mcp", "models", "keys"]
KEY_NAME = re.compile(r"(API_KEY|_KEY|_TOKEN|_SECRET|ACCESS_KEY|_PAT)$")


def sources(home, root="/"):
    h, r = Path(home), Path(root)
    return {
        "apps": [r / "Applications", h / "Applications", r / "System/Applications", r / "System/Applications/Utilities"],
        "mcp": [h / ".claude.json", h / "Library/Application Support/Claude/claude_desktop_config.json", h / ".cursor/mcp.json", Path.cwd() / ".mcp.json"],
        "models": [h / ".ollama/models/manifests", h / ".lmstudio/models", h / ".cache/lm-studio/models"],
    }


def plan(cat, home, catalog, root="/"):
    s = sources(home, root)
    if cat == "apps":
        paths = [str(p) for p in s["apps"]] + sorted({p.replace("~", home, 1) for t in catalog for p in t["detect"].get("paths", [])})
        return "List the .app names in: " + ", ".join(paths) + ". Check that these folders exist."
    if cat == "clis":
        names = sorted({c for t in catalog for c in t["detect"].get("clis", [])})
        return "Check whether these are on PATH, without running them: " + ", ".join(names) + "."
    if cat == "mcp":
        return "Read MCP server names (keys only) from: " + ", ".join(str(p) for p in s["mcp"]) + ". Never their commands, arguments or env values."
    if cat == "models":
        return "List model folder names in: " + ", ".join(str(p) for p in s["models"]) + "."
    if cat == "keys":
        return "List the names of environment variables ending in _KEY, _TOKEN, _SECRET or _PAT. Values are never read or stored."


def tilde(p, home):
    p = str(p)
    return "~" + p[len(home):] if p.startswith(home) else p


def scan_apps(home, catalog, root="/"):
    found, own = set(), set()
    for i, d in enumerate(sources(home, root)["apps"]):
        if d.is_dir():
            names = {p.name[:-4] for p in d.iterdir() if p.name.endswith(".app") and not p.name.startswith(".")}
            found |= names
            if i < 2: own |= names  # installed by you, not built into macOS
    paths = {}
    for t in catalog:
        for p in t["detect"].get("paths", []):
            full = Path(p.replace("~", home, 1))
            if full.exists(): paths[p] = True
    return found, own, paths


def scan_mcp(home):
    names = {}
    for f in sources(home)["mcp"]:
        if not f.is_file(): continue
        try: data = json.loads(f.read_text())
        except (OSError, ValueError): continue
        blocks = [data.get("mcpServers") or {}]
        for proj in (data.get("projects") or {}).values():
            if isinstance(proj, dict): blocks.append(proj.get("mcpServers") or {})
        for b in blocks:
            if isinstance(b, dict):
                for k in b: names.setdefault(k, tilde(f, home))
    return names


def scan_models(home):
    s = sources(home)["models"]; out = []
    lib = s[0] / "registry.ollama.ai/library"
    if lib.is_dir():
        out += [("ollama", f"{m.name}:{t.name}") for m in lib.iterdir() if m.is_dir() for t in m.iterdir()]
    for d in s[1:]:
        if d.is_dir():
            out += [("lmstudio", f"{a.name}/{m.name}") for a in d.iterdir() if a.is_dir() for m in a.iterdir() if m.is_dir()]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categories", default="", help="comma-separated, from: " + ",".join(CATS))
    ap.add_argument("--plan", action="store_true", help="print what each category would read, then exit without reading")
    ap.add_argument("--out", default="~/.bridgework/audit.json")
    ap.add_argument("--home", default=os.path.expanduser("~"), help="for tests: scan a different home folder")
    ap.add_argument("--root", default="/", help="for tests: where /Applications and /System live")
    a = ap.parse_args()
    catalog = json.loads((HERE / "catalog.json").read_text())["tools"]
    home = str(Path(a.home).resolve())
    if a.plan:
        for c in CATS: print(f"{c}: {plan(c, home, catalog, a.root)}")
        return
    cats = [c.strip() for c in a.categories.split(",") if c.strip()]
    bad = [c for c in cats if c not in CATS]
    if not cats or bad:
        sys.exit(f"Name the categories the user agreed to, from: {', '.join(CATS)}. Nothing was read." + (f" Unknown: {', '.join(bad)}." if bad else ""))

    signals = {t["id"]: [] for t in catalog}
    unmatched = {}
    if "apps" in cats:
        apps, own, paths = scan_apps(home, catalog, a.root); used = set()
        for t in catalog:
            for name in t["detect"].get("apps", []):
                if name in apps: signals[t["id"]].append({"kind": "app", "detail": f"{name}.app"}); used.add(name)
            for p in t["detect"].get("paths", []):
                if p in paths: signals[t["id"]].append({"kind": "path", "detail": p})
        unmatched["apps"] = sorted(own - used)
    if "clis" in cats:
        for t in catalog:
            for c in t["detect"].get("clis", []):
                w = shutil.which(c)
                if w: signals[t["id"]].append({"kind": "cli", "detail": tilde(w, home)})
    if "mcp" in cats:
        names = scan_mcp(home); used = set()
        for t in catalog:
            for frag in t["detect"].get("mcp", []):
                for n, f in names.items():
                    if frag in n.lower(): signals[t["id"]].append({"kind": "mcp", "detail": f"MCP server '{n}' in {f}"}); used.add(n)
        unmatched["mcp"] = sorted(set(names) - used)
    if "models" in cats:
        models = scan_models(home)
        for t in catalog:
            kind = t["detect"].get("models")
            hits = [m for k, m in models if k == kind]
            if hits: signals[t["id"]].append({"kind": "models", "detail": f"{len(hits)} local model(s): " + ", ".join(sorted(hits)[:8])})
    if "keys" in cats:
        names = sorted(k for k in os.environ if KEY_NAME.search(k)); used = set()
        for t in catalog:
            for frag in t["detect"].get("keys", []):
                for n in names:
                    if n.startswith(frag): signals[t["id"]].append({"kind": "key", "detail": f"variable {n} is set (value not read)"}); used.add(n)
        unmatched["keys"] = [n for n in names if n not in used]

    matched = []
    for t in catalog:
        sig = signals[t["id"]]
        if not sig: continue
        ev = "configured" if any(s["kind"] in ("key", "mcp") for s in sig) else "installed"
        matched.append({"use": t["id"], "name": t["name"], "evidence": ev, "signals": sig})
    out = {"meta": {"observed": datetime.date.today().isoformat(), "categories": cats, "note": "Read-only. Presence only: nothing was run, called or authenticated."},
           "matched": matched, "unmatched": unmatched}
    dest = Path(os.path.expanduser(a.out)); dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"Scanned: {', '.join(cats)}. Matched {len(matched)} known tools: {', '.join(m['name'] for m in matched) or 'none'}.")
    for k, v in unmatched.items(): print(f"Unmatched {k}: {len(v)}")
    print(f"Wrote {tilde(dest, home)}")


if __name__ == "__main__":
    main()
