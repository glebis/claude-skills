#!/usr/bin/env python3
"""Inventory what a user can do in a product, from its code and docs, so journeys are grounded in real controls.

usage: inventory.py OUT.json FILE_OR_DIR [...]
Collects from HTML/JS/TS(X)/Python/Markdown:
  buttons (visible labels), aria-labels/titles, keyboard shortcuts (<kbd>, key handlers), modes (segmented
  toggles / data-mode), HTTP endpoints (/api/...), CLI subcommands (argparse add_parser), and doc headings.
"""
import json, re, sys
from collections import Counter
from pathlib import Path

EXT = {".html", ".htm", ".js", ".ts", ".tsx", ".jsx", ".py", ".md", ".vue", ".svelte"}

def files(args):
    for a in map(Path, args):
        if a.is_dir():
            yield from (p for p in a.rglob("*") if p.suffix in EXT and "node_modules" not in p.parts and ".git" not in p.parts)
        elif a.exists():
            yield a

def main():
    out = Path(sys.argv[1]); inv = {k: Counter() for k in ("buttons", "labels", "keys", "modes", "endpoints", "cli", "headings")}
    for p in files(sys.argv[2:]):
        t = p.read_text(errors="ignore")
        for b in re.findall(r"<button[^>]*>\s*([^<]{1,48})", t):
            b = re.sub(r"\$\{[^}]*\}", "…", b).strip()
            if b and not b.startswith("$"): inv["buttons"][b] += 1
        for a in re.findall(r'(?:aria-label|title)="([^"]{2,60})"', t): inv["labels"][a] += 1
        for k in re.findall(r"<kbd>([^<]{1,12})</kbd>", t): inv["keys"][k] += 1
        for k in re.findall(r"e\.key\s*===?\s*['\"]([^'\"]{1,10})['\"]", t): inv["keys"][k] += 1
        for m in re.findall(r"data-mode=['\"]([\w-]+)", t): inv["modes"][m] += 1
        for e in re.findall(r"['\"`](/api/[\w/-]+)", t): inv["endpoints"][e] += 1
        for c in re.findall(r"add_parser\(\s*['\"]([\w-]+)", t): inv["cli"][c] += 1
        if p.suffix == ".md":
            for h in re.findall(r"^#{1,3} (.+)$", t, re.M): inv["headings"][f"{p.name}: {h.strip()}"] += 1
    res = {k: [x for x, _ in v.most_common()] for k, v in inv.items()}
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(out, {k: len(v) for k, v in res.items()})

if __name__ == "__main__":
    main()
