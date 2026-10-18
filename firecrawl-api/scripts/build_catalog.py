#!/usr/bin/env python3
"""
Build a local catalog of Firecrawl Alexandria tools (free: uses find-tools only).

Writes:
  references/alexandria-catalog.json  full harvest (categories, providers, tools)
  references/alexandria-catalog.md    browsable catalog grouped by category

Usage:
  python3 build_catalog.py [--out-dir DIR]
"""

import argparse
import contextlib
import datetime
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firecrawl as fc  # noqa: E402

PAGE = 100
MIN_INTERVAL = 6.0  # seconds between calls: stays under the 12 req/min team limit
MAX_RETRIES = 5
_last_call = [0.0]


def paced_find_tools(**kwargs):
    """Call find_tools at a safe rate; wait out 429s and retry.

    Retrying is safe only because find-tools is free. Never reuse this for `run`.
    """
    for attempt in range(MAX_RETRIES + 1):
        wait = MIN_INTERVAL - (time.monotonic() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.monotonic()
        buf = io.StringIO()
        try:
            with contextlib.redirect_stderr(buf):  # silence per-call Request IDs
                return fc.find_tools(**kwargs)
        except SystemExit:
            err = buf.getvalue()
            match = re.search(r'"retry_after_seconds": (\d+)', err)
            if "(429)" not in err or attempt == MAX_RETRIES:
                sys.stderr.write(err)  # surface the error die() printed
                raise
            delay = int(match.group(1)) + 1 if match else 15
            print(f"rate limited; waiting {delay}s", file=sys.stderr)
            time.sleep(delay)


def harvest(level, **selectors):
    """Follow `next` pagination for one find-tools listing; return all items."""
    items, request, meta = [], None, {}
    while True:
        data = paced_find_tools(level=level, limit=PAGE, request=request, **selectors)
        items.extend(data.get("items", []))
        meta = {"total": data.get("total"), "catalogueVersion": data.get("catalogueVersion")}
        request = data.get("next")
        if not request:
            return items, meta


def one_line(text, n=140):
    text = " ".join((text or "").split()).replace("|", "\\|")
    return text if len(text) <= n else text[: n - 1] + "…"


def cost_label(tool):
    cost = tool.get("creditsCost")
    if cost is None:
        return "?"
    return f"{cost:g}/record" if tool.get("perRecord") else f"{cost:g}"


def render_markdown(catalog):
    cats, provs, tools = catalog["categories"], catalog["providers"], catalog["tools"]
    by_provider = {}
    for t in tools:
        by_provider.setdefault(t["provider"], []).append(t)
    lines = [
        "# Firecrawl Alexandria catalog",
        "",
        f"Snapshot {catalog['retrieved']} · catalogue `{catalog['catalogueVersion'][:19]}…` · "
        f"{len(cats)} categories · {len(provs)} providers · {len(tools)} tools.",
        "",
        "Built with `scripts/build_catalog.py` from free find-tools listings. Prices are the "
        "listed `creditsCost` at snapshot time; check `contract` before running. "
        "A listed tool is not proof that it covers your market or inputs.",
        "",
        "## Categories",
        "",
        "| Category | Providers | Tools | What it covers |",
        "| --- | --- | --- | --- |",
    ]
    for c in cats:
        pids = c["providers"]
        n_tools = sum(len(by_provider.get(p, [])) for p in pids)
        lines.append(f"| [{c['id']}](#{c['id']}) | {len(pids)} | {n_tools} | {one_line(c.get('description'), 110)} |")
    uncategorized = sorted(set(provs) - {p for c in cats for p in c["providers"]})
    if uncategorized:
        lines.append(f"| [uncategorized](#uncategorized) | {len(uncategorized)} | "
                     f"{sum(len(by_provider.get(p, [])) for p in uncategorized)} | Providers not listed under any category |")
    lines.append("")

    def provider_block(pid):
        p = provs[pid]
        ts = sorted(by_provider.get(pid, []), key=lambda t: t["capability"])
        out = [f'<a id="p-{pid}"></a>', "", f"### {p.get('name') or pid} (`{pid}`)", "",
               one_line(p.get("description"), 400), "",
               "| Capability | Credits | Use |", "| --- | --- | --- |"]
        out += [f"| `{t['capability']}` | {cost_label(t)} | {one_line(t.get('description'))} |" for t in ts]
        return out + [""]

    rendered = set()  # a provider in several categories gets one table, linked from the rest
    for c in cats:
        lines += [f"## {c['id']}", "", one_line(c.get("description"), 300), ""]
        seen_elsewhere = [pid for pid in sorted(c["providers"]) if pid in rendered]
        for pid in sorted(c["providers"]):
            if pid in provs and pid not in rendered:
                lines += provider_block(pid)
                rendered.add(pid)
        if seen_elsewhere:
            links = ", ".join(f"[{provs[pid].get('name') or pid}](#p-{pid})" for pid in seen_elsewhere if pid in provs)
            lines += [f"Also in this category: {links}", ""]
    if uncategorized:
        lines += ["## uncategorized", ""]
        for pid in uncategorized:
            lines += provider_block(pid)
    return "\n".join(lines) + "\n"


def main():
    default_out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
    parser = argparse.ArgumentParser(description="Build the Alexandria tool catalog (free)")
    parser.add_argument("--out-dir", default=default_out)
    args = parser.parse_args()
    if not fc.API_KEY:
        fc.die("FIRECRAWL_API_KEY not found in SOPS or environment")

    categories, _ = harvest(None)
    print(f"categories: {len(categories)}", file=sys.stderr)
    for c in categories:
        provs, _ = harvest("providers", categories=[c["id"]])
        c["providers"] = [p["provider"] for p in provs]
    providers, pmeta = harvest("providers")
    print(f"providers: {len(providers)} (listed total {pmeta['total']})", file=sys.stderr)
    tools, tmeta = harvest("tools")
    print(f"tools: {len(tools)} (listed total {tmeta['total']})", file=sys.stderr)

    keep = ("id", "provider", "capability", "name", "description", "creditsCost", "perRecord")
    catalog = {
        "retrieved": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "catalogueVersion": tmeta["catalogueVersion"] or "",
        "categories": [{"id": c["id"], "description": c.get("description"), "providers": c["providers"]}
                       for c in categories],
        "providers": {p["provider"]: {k: p.get(k) for k in ("name", "description", "toolCount")}
                      for p in providers},
        "tools": [{k: t.get(k) for k in keep} for t in tools],
    }
    if len(tools) != tmeta["total"] or len(providers) != pmeta["total"]:
        print("WARNING: harvested counts differ from listed totals", file=sys.stderr)

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "alexandria-catalog.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=1, ensure_ascii=False)
    with open(os.path.join(args.out_dir, "alexandria-catalog.md"), "w", encoding="utf-8") as f:
        f.write(render_markdown(catalog))
    print(f"Saved to {args.out_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
