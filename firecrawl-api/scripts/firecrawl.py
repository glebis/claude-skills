#!/usr/bin/env python3
"""
Firecrawl CLI — search, scrape, and extract web content via Firecrawl API.
"""

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import requests

SOPS_SECRETS = os.path.expanduser("~/.claude/skills/secrets.enc.yaml")
AGE_KEY_FILE = os.path.expanduser("~/.config/sops/age/keys.txt")


def load_api_key():
    """Read FIRECRAWL_API_KEY from SOPS first; fall back to the env var.

    Falls back silently when sops, the secrets file, or the key is missing,
    or when decryption fails or times out.
    """
    if shutil.which("sops") and os.path.exists(SOPS_SECRETS):
        env = dict(os.environ)
        if "SOPS_AGE_KEY_FILE" not in env and os.path.exists(AGE_KEY_FILE):
            env["SOPS_AGE_KEY_FILE"] = AGE_KEY_FILE
        try:
            r = subprocess.run(
                ["sops", "-d", "--extract", '["FIRECRAWL_API_KEY"]', SOPS_SECRETS],
                capture_output=True, text=True, env=env, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    return os.getenv("FIRECRAWL_API_KEY")


API_KEY = load_api_key()
BASE = "https://api.firecrawl.dev/v1"
BASE_V2 = "https://api.firecrawl.dev/v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
TERMS_DASHBOARD_URL = "https://www.firecrawl.dev/app/settings?tab=data-sources"


LAST_ERROR = [""]  # message of the most recent die(), for ledger records


def die(msg):
    LAST_ERROR[0] = str(msg)
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# --- Alexandria (structured data providers) ---------------------------------
# Discovery (tools, find-tools, contract) is free. Execution (run) is billed
# at the tool's listed price. All calls go through the v2 API.


FREE_RETRIES = 3  # the team limit is 12 requests/minute


def retry_delay(response, body):
    """Seconds to wait after a 429: the API's retry hint plus 1, else 15."""
    hint = body.get("retry_after_seconds") if isinstance(body, dict) else None
    hint = hint or response.headers.get("Retry-After")
    try:
        return int(float(hint)) + 1
    except (TypeError, ValueError):
        return 15


def alexandria_call(call, request_id=None, billed=False):
    """POST one Alexandria call {provider, capability, options} to /v2/scrape.

    Prints the request ID to stderr before sending so an interrupted request
    can be traced. A free call that hits the rate limit (429) waits and retries
    up to FREE_RETRIES times; a billed call is never retried.
    """
    request_id = request_id or str(uuid.uuid4())
    kind = "billed" if billed else "free"
    print(f"Request ID ({kind}): {request_id}", file=sys.stderr)
    for attempt in range(FREE_RETRIES + 1):
        r = requests.post(
            f"{BASE_V2}/scrape",
            headers={**HEADERS, "x-request-id": request_id},
            json={"alexandria": call},
            timeout=120,
        )
        try:
            body = r.json()
        except ValueError:
            die(f"Alexandria call failed ({r.status_code}): {r.text[:500]}")
        if r.status_code != 429:
            break
        if billed or attempt == FREE_RETRIES:
            die(f"Rate limited (429){' on a billed call; not retried' if billed else ''}: "
                f"{json.dumps(body)[:300]}")
        delay = retry_delay(r, body)
        print(f"Rate limited; retrying free call in {delay}s", file=sys.stderr)
        time.sleep(delay)
    if body.get("code") == "THIRD_PARTY_DATA_TERMS_REQUIRED":
        url = (body.get("requiresAction") or {}).get("url") or TERMS_DASHBOARD_URL
        die(f"Provider terms not accepted. An org admin must review and accept them at {url}. "
            "Do not retry until accepted.")
    if r.status_code != 200 or not body.get("success"):
        die(f"Alexandria call failed ({r.status_code}): {json.dumps(body)[:500]}")
    return body


def alexandria_items(body):
    """Return data.alexandria[] and fail if any item carries an error."""
    items = body.get("data", {}).get("alexandria", [])
    errors = [i for i in items if i.get("error")]
    if errors:
        print(json.dumps(errors, indent=2, ensure_ascii=False), file=sys.stderr)
        die(f"{len(errors)} Alexandria result(s) returned an error")
    return items


def tools(query, limit=5, with_web=False, fmt="markdown"):
    """Semantic tool discovery. Free unless --web adds billed web results."""
    sources = ["web", "alexandria"] if with_web else ["alexandria"]
    if with_web:
        print("Note: --web results are billed as a normal search (not covered by the run ceiling).",
              file=sys.stderr)
    r = requests.post(
        f"{BASE_V2}/search",
        headers=HEADERS,
        json={"query": query, "sources": sources, "limit": limit},
        timeout=60,
    )
    if r.status_code != 200:
        die(f"Tool search failed ({r.status_code}): {r.text[:500]}")
    data = r.json().get("data", {})
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    found = data.get("tools", [])
    for t in found:
        print(f"- {t.get('provider')}/{t.get('capability')}: {t.get('description', '')}")
    for w in data.get("web", []):
        print(f"- [web] {w.get('title', 'Untitled')}: {w.get('url', '')}")
    print(f"\nTotal: {len(found)} tools")
    return data


def find_tools(providers=None, urls=None, query=None, capabilities=None,
               level=None, expand=None, limit=None, request=None, categories=None):
    """Browse the catalogue or inspect contracts (free). `request` replays a `next`."""
    if request:
        call = request
    else:
        options = {k: v for k, v in {
            "providers": providers, "urls": urls, "query": query,
            "capabilities": capabilities, "categories": categories, "level": level,
            "expand": expand, "limit": limit,
        }.items() if v}
        call = {"provider": "firecrawl", "capability": "find-tools", "options": options}
    items = alexandria_items(alexandria_call(call))
    return items[0].get("data", {}) if items else {}


def contract(address):
    """Return the catalogue entry (inputs, response, price) for provider/capability."""
    provider, _, capability = address.partition("/")
    if not capability:
        die("Use a provider/capability address, e.g. arxiv-org/papers/get_paper")
    data = find_tools(providers=[provider], capabilities=[capability], level="tools",
                      expand=["options", "response", "examples"], limit=1)
    entries = [i for i in data.get("items", []) if i.get("capability") == capability]
    if not entries:
        die(f"No contract found for {address}")
    return entries[0]


DEFAULT_MAX_CREDITS = 25  # covers most single lookups (median listed price: 5)


def estimate_cost(entry, options):
    """Estimated credits for one run, or None if it cannot be bounded.

    Per-record tools cost price x records; the request's `limit` is the only
    upper bound known before paying, so without it the cost is unknown.
    """
    cost = entry.get("creditsCost")
    if cost is None:
        return None
    if not entry.get("perRecord"):
        return cost
    limit = options.get("limit")
    numeric = isinstance(limit, (int, float)) and not isinstance(limit, bool)
    return cost * limit if numeric and limit > 0 else None


def resolve_ceiling(max_credits=None):
    """Per-run ceiling: explicit value, else FIRECRAWL_MAX_CREDITS, else the default."""
    if max_credits is not None:
        return max_credits
    try:
        return float(os.getenv("FIRECRAWL_MAX_CREDITS", DEFAULT_MAX_CREDITS))
    except ValueError:
        return DEFAULT_MAX_CREDITS


# --- Session ledger -----------------------------------------------------------
# A JSON file shared by a series of `run` calls: it enforces a total budget,
# records what each call cost, and blocks further runs after a failure until
# someone has looked at it.


def load_ledger(path, budget=None):
    """Read a ledger, creating it when `budget` is given. Returns the dict."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            ledger = json.load(f)
        if budget is not None and budget != ledger["budget"]:
            die(f"Ledger {path} already has budget {ledger['budget']:g}; "
                "start a new ledger file to change it")
        return ledger
    if budget is None:
        die(f"Ledger {path} does not exist; pass --budget N to create it")
    return {"budget": budget, "calls": []}


def ledger_spent(ledger):
    return sum(c["credits"] for c in ledger["calls"])


def record_call(path, ledger, address, credits, status, detail=""):
    ledger["calls"].append({
        "address": address, "credits": credits, "status": status,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **({"detail": detail[-300:]} if detail else {}),
    })
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=1)
    os.replace(tmp, path)


def ledger_summary(path):
    """Print budget, spend, and every recorded call."""
    ledger = load_ledger(path)
    spent = ledger_spent(ledger)
    print(f"Budget {ledger['budget']:g} · spent {spent:g} · remaining {ledger['budget'] - spent:g}")
    for c in ledger["calls"]:
        print(f"  {c['at']}  {c['status']:<6} {c['credits']:>5g}  {c['address']}"
              + (f"  ({c['detail'][:80]})" if c.get("detail") else ""))


def allow_spend(entry, options, max_credits):
    """Decide whether a billed Alexandria run may proceed.

    Ceiling: --max-credits, else FIRECRAWL_MAX_CREDITS, else DEFAULT_MAX_CREDITS.
    A run is refused when its estimate exceeds the ceiling or cannot be bounded.
    """
    max_credits = resolve_ceiling(max_credits)
    estimate = estimate_cost(entry, options)
    if estimate is None:
        print("Cost cannot be bounded: set a numeric `limit` in --options for a per-record tool.",
              file=sys.stderr)
        return False
    if estimate > max_credits:
        print(f"Estimated {estimate:g} credits exceeds the {max_credits:g}-credit ceiling.",
              file=sys.stderr)
        return False
    return True


def run(address, options, max_credits=None, ledger_path=None, budget=None, after_failure=False):
    """Execute a provider capability. Billed at the tool's listed price.

    With ledger_path, the run must also fit the ledger's remaining budget, is
    refused after a recorded failure (unless after_failure), and is recorded:
    the reported creditsCost on success, the listed price on failure (a failed
    call may still be billed, so the ledger stays conservative).
    """
    provider, _, capability = address.partition("/")
    ledger = load_ledger(ledger_path, budget) if ledger_path else None
    if ledger:
        failed = [c for c in ledger["calls"] if c["status"] == "failed"]
        if failed and not after_failure:
            die(f"Ledger has a failed call ({failed[-1]['address']}: {failed[-1].get('detail', '')[:120]}). "
                "Fix the cause before spending more; pass --after-failure to continue anyway")
    entry = contract(address)
    ceiling = resolve_ceiling(max_credits)
    if ledger:
        ceiling = min(ceiling, ledger["budget"] - ledger_spent(ledger))
    if not allow_spend(entry, options, ceiling):
        die(f"Aborted: {address} costs {entry.get('creditsCost')} credits"
            f"{' per record' if entry.get('perRecord') else ''}; ceiling for this run is {ceiling:g}"
            f"{' (ledger remaining)' if ledger else ''}")
    try:
        body = alexandria_call({"provider": provider, "capability": capability, "options": options},
                               billed=True)
        items = alexandria_items(body)
    except SystemExit:
        if ledger:
            record_call(ledger_path, ledger, address, estimate_cost(entry, options) or 0, "failed",
                        LAST_ERROR[0] or "unknown error")
        raise
    if ledger:
        record_call(ledger_path, ledger, address, body.get("data", {}).get("creditsCost") or 0, "ok")
    print(json.dumps({"creditsCost": body.get("data", {}).get("creditsCost"),
                      "results": [i.get("data") for i in items]},
                     indent=2, ensure_ascii=False))
    return items


def search(query, limit=5, fmt="markdown"):
    """Search the web and return scraped results."""
    r = requests.post(
        f"{BASE}/search",
        headers=HEADERS,
        timeout=120,
        json={
            "query": query,
            "limit": limit,
            "scrapeOptions": {
                "formats": ["markdown"],
                "onlyMainContent": True,
            },
        },
    )
    if r.status_code != 200:
        die(f"Search failed ({r.status_code}): {r.text}")

    results = r.json().get("data", [])

    if fmt == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return results

    for i, item in enumerate(results, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        md = item.get("markdown", "")
        print(f"## {i}. {title}\n")
        print(f"**URL:** {url}\n")
        if md:
            print(md[:3000])
            if len(md) > 3000:
                print("\n... (truncated)")
        print("\n---\n")

    print(f"Total: {len(results)} results")
    return results


def scrape(url, fmt="markdown"):
    """Scrape a single URL and return content."""
    r = requests.post(
        f"{BASE}/scrape",
        headers=HEADERS,
        timeout=120,
        json={
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
    )
    if r.status_code != 200:
        die(f"Scrape failed ({r.status_code}): {r.text}")

    data = r.json().get("data", {})

    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data

    title = data.get("metadata", {}).get("title", "Untitled")
    md = data.get("markdown", "")
    print(f"# {title}\n")
    print(f"**URL:** {url}\n")
    print(md)
    return data


def extract(urls, prompt, fmt="markdown"):
    """Extract structured data from URLs using a prompt."""
    if isinstance(urls, str):
        urls = [urls]

    r = requests.post(
        f"{BASE}/extract",
        headers=HEADERS,
        timeout=300,
        json={
            "urls": urls,
            "prompt": prompt,
        },
    )
    if r.status_code != 200:
        die(f"Extract failed ({r.status_code}): {r.text}")

    data = r.json().get("data", {})

    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

    return data


def map_site(url, limit=100):
    """Get all URLs from a website."""
    r = requests.post(
        f"{BASE}/map",
        headers=HEADERS,
        timeout=120,
        json={"url": url, "limit": limit},
    )
    if r.status_code != 200:
        die(f"Map failed ({r.status_code}): {r.text}")

    data = r.json()
    links = data.get("links", [])
    for link in links:
        print(link)
    print(f"\nTotal: {len(links)} URLs")
    return links


def main():
    if not API_KEY:
        die("FIRECRAWL_API_KEY not found in SOPS (~/.claude/skills/secrets.enc.yaml) or environment")

    parser = argparse.ArgumentParser(description="Firecrawl CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = sub.add_parser("search", help="Search the web")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("-n", "--limit", type=int, default=5)
    p_search.add_argument("-f", "--format", choices=["markdown", "json"], default="markdown")
    p_search.add_argument("-o", "--output", help="Save to file")

    # scrape
    p_scrape = sub.add_parser("scrape", help="Scrape a URL")
    p_scrape.add_argument("url", help="URL to scrape")
    p_scrape.add_argument("-f", "--format", choices=["markdown", "json"], default="markdown")
    p_scrape.add_argument("-o", "--output", help="Save to file")

    # extract
    p_extract = sub.add_parser("extract", help="Extract structured data from URLs")
    p_extract.add_argument("urls", nargs="+", help="URLs to extract from")
    p_extract.add_argument("-p", "--prompt", required=True, help="Extraction prompt")
    p_extract.add_argument("-f", "--format", choices=["markdown", "json"], default="json")
    p_extract.add_argument("-o", "--output", help="Save to file")

    # map
    p_map = sub.add_parser("map", help="Get all URLs from a site")
    p_map.add_argument("url", help="Site URL")
    p_map.add_argument("-n", "--limit", type=int, default=100)
    p_map.add_argument("-o", "--output", help="Save to file")

    # Alexandria: tools (free discovery)
    p_tools = sub.add_parser("tools", help="Discover Alexandria data tools (free)")
    p_tools.add_argument("query", help="Data you need, in plain words")
    p_tools.add_argument("-n", "--limit", type=int, default=5)
    p_tools.add_argument("--web", action="store_true", help="Also return web results (billed)")
    p_tools.add_argument("-f", "--format", choices=["markdown", "json"], default="markdown")
    p_tools.add_argument("-o", "--output", help="Save to file")

    # Alexandria: find-tools (free catalogue browsing)
    p_find = sub.add_parser("find-tools", help="Browse the Alexandria catalogue (free)")
    p_find.add_argument("--providers", help="Comma-separated provider IDs")
    p_find.add_argument("--urls", nargs="+", help="Websites to match tools for")
    p_find.add_argument("--query", help="Semantic filter")
    p_find.add_argument("--capabilities", help="Comma-separated capability IDs")
    p_find.add_argument("--categories", help="Comma-separated category IDs")
    p_find.add_argument("--level", choices=["providers", "groups", "tools"])
    p_find.add_argument("--expand", help="Comma-separated: options,response,examples")
    p_find.add_argument("-n", "--limit", type=int)
    p_find.add_argument("--request", help="A complete `next` request JSON from a previous result")
    p_find.add_argument("-o", "--output", help="Save to file")

    # Alexandria: contract (free)
    p_contract = sub.add_parser("contract", help="Show a tool's inputs, response, and price (free)")
    p_contract.add_argument("address", help="provider/capability, e.g. arxiv-org/papers/get_paper")
    p_contract.add_argument("-o", "--output", help="Save to file")

    # Alexandria: run (billed)
    p_run = sub.add_parser("run", help="Execute an Alexandria tool (billed at its listed price)")
    p_run.add_argument("address", help="provider/capability")
    p_run.add_argument("--options", default="{}", help="Input JSON matching the contract")
    p_run.add_argument("--max-credits", type=float, help="Spend ceiling for this run")
    p_run.add_argument("--ledger", help="Session ledger JSON: shared budget, spend record, stop after failure")
    p_run.add_argument("--budget", type=float, help="Total budget when creating a new --ledger")
    p_run.add_argument("--after-failure", action="store_true", help="Run even though the ledger has a failed call")
    p_run.add_argument("-o", "--output", help="Save to file")

    # Ledger summary (no API calls)
    p_ledger = sub.add_parser("ledger", help="Show a session ledger's budget and calls")
    p_ledger.add_argument("path", help="Ledger JSON file")

    args = parser.parse_args()

    def csv(value):
        return [v.strip() for v in value.split(",") if v.strip()] if value else None

    # With --output, buffer stdout and write the file only if the command succeeds,
    # so a failed or aborted call never leaves an empty or partial file behind.
    original_stdout = sys.stdout
    output = getattr(args, "output", None)
    if output:
        sys.stdout = io.StringIO()
    succeeded = False

    try:
        if args.command == "search":
            search(args.query, args.limit, args.format)
        elif args.command == "scrape":
            scrape(args.url, args.format)
        elif args.command == "extract":
            extract(args.urls, args.prompt, args.format)
        elif args.command == "map":
            map_site(args.url, args.limit)
        elif args.command == "tools":
            tools(args.query, args.limit, args.web, args.format)
        elif args.command == "find-tools":
            request = json.loads(args.request) if args.request else None
            data = find_tools(csv(args.providers), args.urls, args.query, csv(args.capabilities),
                              args.level, csv(args.expand), args.limit, request,
                              csv(args.categories))
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif args.command == "contract":
            print(json.dumps(contract(args.address), indent=2, ensure_ascii=False))
        elif args.command == "run":
            try:
                options = json.loads(args.options)
            except json.JSONDecodeError as e:
                die(f"--options is not valid JSON: {e}")
            if not isinstance(options, dict):
                die("--options must be a JSON object")
            if args.budget is not None and not args.ledger:
                die("--budget needs --ledger")
            run(args.address, options, args.max_credits, args.ledger, args.budget, args.after_failure)
        elif args.command == "ledger":
            ledger_summary(args.path)
        succeeded = True
    finally:
        if output:
            buffered = sys.stdout.getvalue()
            sys.stdout = original_stdout
            if succeeded:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(buffered)
                print(f"Saved to {output}")
            else:
                print(f"Not saved: command failed, {output} left unchanged", file=sys.stderr)


if __name__ == "__main__":
    main()
