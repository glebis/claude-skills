#!/usr/bin/env python3
"""
Firecrawl CLI — search, scrape, and extract web content via Firecrawl API.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
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


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# --- Alexandria (structured data providers) ---------------------------------
# Discovery (tools, find-tools, contract) is free. Execution (run) is billed
# at the tool's listed price. All calls go through the v2 API.


def alexandria_call(call, request_id=None):
    """POST one Alexandria call {provider, capability, options} to /v2/scrape.

    Prints the request ID to stderr before sending so an interrupted request
    can be traced. Returns the parsed response; never retries.
    """
    request_id = request_id or str(uuid.uuid4())
    print(f"Request ID: {request_id}", file=sys.stderr)
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


def allow_spend(entry, options, max_credits):
    """Decide whether a billed Alexandria run may proceed.

    entry: the contract from contract(), incl. creditsCost and perRecord.
    options: the input JSON about to be sent (may contain a limit).
    max_credits: the --max-credits value, or None if not given.
    Return True to run, or False to abort.
    """
    # TODO(user): spend policy. See the request in chat.
    return True


def run(address, options, max_credits=None):
    """Execute a provider capability. Billed at the tool's listed price."""
    provider, _, capability = address.partition("/")
    entry = contract(address)
    if not allow_spend(entry, options, max_credits):
        die(f"Aborted: {address} costs {entry.get('creditsCost')} credits"
            f"{' per record' if entry.get('perRecord') else ''}; raise --max-credits to allow")
    body = alexandria_call({"provider": provider, "capability": capability, "options": options})
    items = alexandria_items(body)
    print(json.dumps({"creditsCost": body.get("data", {}).get("creditsCost"),
                      "results": [i.get("data") for i in items]},
                     indent=2, ensure_ascii=False))
    return items


def search(query, limit=5, fmt="markdown"):
    """Search the web and return scraped results."""
    r = requests.post(
        f"{BASE}/search",
        headers=HEADERS,
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
    p_run.add_argument("-o", "--output", help="Save to file")

    args = parser.parse_args()

    def csv(value):
        return [v.strip() for v in value.split(",") if v.strip()] if value else None

    # Redirect stdout to file if --output specified
    original_stdout = sys.stdout
    if hasattr(args, "output") and args.output:
        sys.stdout = open(args.output, "w", encoding="utf-8")

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
            run(args.address, options, args.max_credits)
    finally:
        if sys.stdout != original_stdout:
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
