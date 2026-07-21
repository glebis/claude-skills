#!/usr/bin/env python3
"""
Rebuild site-wide aggregations for the agency-docs site from every published
lab meeting. Run after each meeting is published (Step 9 of the pipeline) or
standalone to backfill.

Produces three aggregations, each derived from ALL meeting MDX across ALL labs:

  1. database  — a meetings index: one row per meeting (lab, number, date,
     title, YouTube/Fathom links). Written as both an MDX page (human) and a
     JSON file (machine / client-side search).
  2. glossary  — technical terms seen across meetings, with definitions. Term
     definitions are persisted in a JSON store so human/LLM-written wording
     survives rebuilds; only NEW terms are reported for definition.
  3. library   — a deduplicated "global library" of every external link
     mentioned across all meetings, grouped by domain.

DESIGN NOTE — this script is authored against the documented ${DOCS_SITE_DIR}
conventions (see SKILL.md) without access to the live site, so every input and
output path is configurable via .env / environment and the defaults are
conservative. Run with --dry-run first to confirm the paths and counts before
writing anything. Adjust the AGG_* env vars if your site lays things out
differently.

Reads path configuration from .env in the skill root, matching update_meeting_doc.py.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
from collections import defaultdict


# ---------------------------------------------------------------------------
# Config (mirrors update_meeting_doc.py so both scripts read the same .env)
# ---------------------------------------------------------------------------

def load_env():
    """Load .env file from skill root if it exists."""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = os.path.expanduser(value.strip())
                    os.environ.setdefault(key.strip(), value)


def get_path(env_var: str, default_relative: str) -> Path:
    value = os.environ.get(env_var)
    if value:
        return Path(os.path.expanduser(value))
    return Path.home() / default_relative


def docs_site_dir() -> Path:
    return get_path('DOCS_SITE_DIR', 'Sites/agency-docs')


def site_domain() -> str:
    return os.environ.get('SITE_DOMAIN', 'agency-lab.glebkalinin.com')


def out_path(env_var: str, default_rel_to_site: str) -> Path:
    """Resolve an output path, defaulting to a location under the site dir."""
    value = os.environ.get(env_var)
    if value:
        return Path(os.path.expanduser(value))
    return docs_site_dir() / default_rel_to_site


# Seed glossary: terms the lab uses constantly. Persisted-store definitions
# (if present) always win over these; this is only a starting vocabulary so a
# first run isn't empty.
SEED_TERMS = {
    "MCP": "Model Context Protocol — open standard for connecting Claude to external tools and data sources.",
    "Skills": "Reusable instruction sets (SKILL.md) Claude Code invokes contextually to perform a procedure.",
    "Claude Code": "Anthropic's agentic coding CLI/IDE assistant.",
    "Subagents": "Worker Claude sessions spawned to handle a side task in their own context.",
    "Workflows": "Dynamic workflows — a script that orchestrates many subagents at scale (Opus 4.8, research preview).",
    "CLI": "Command-line interface.",
    "SDK": "Software development kit.",
    "MDX": "Markdown extended with JSX — the format the docs site is authored in.",
    "RAG": "Retrieval-augmented generation.",
    "LLM": "Large language model.",
    "YOLO": "Running an agent with permissions bypassed (no per-action approval).",
}

# Known multi-word / branded terms to detect verbatim (case-insensitive match,
# canonical casing preserved).
KNOWN_PHRASES = [
    "Claude Code", "Nano Banana", "vibe coding", "Agent SDK", "Model Context Protocol",
]


# ---------------------------------------------------------------------------
# MDX helpers
# ---------------------------------------------------------------------------

def mdx_escape(text: str) -> str:
    """Make a plain string safe to drop into MDX prose/table cells."""
    if text is None:
        return ""
    # Escape MDX/JSX hazards documented in learnings.md: <, {, and HTML comments.
    text = text.replace("<!--", "").replace("-->", "")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("{", "&#123;").replace("}", "&#125;")
    text = text.replace("|", "\\|")  # don't break table rows
    return text.strip()


def split_frontmatter(content: str):
    """Return (frontmatter_dict, body_str). Tolerant of missing yaml module."""
    parts = content.split('---')
    if len(parts) < 3 or parts[0].strip():
        return {}, content
    fm_raw, body = parts[1].strip(), '---'.join(parts[2:])
    fm = {}
    try:
        import yaml
        fm = yaml.safe_load(fm_raw) or {}
    except Exception:
        for line in fm_raw.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"\'')
    return fm, body


# ---------------------------------------------------------------------------
# Meeting parsing
# ---------------------------------------------------------------------------

YT_EMBED_RE = re.compile(r'youtube\.com/embed/([A-Za-z0-9_-]{6,})')
YT_WATCH_RE = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{6,})')
FATHOM_RE = re.compile(r'https?://[^)\s"]*fathom\.video[^)\s"]*')
DATE_RE = re.compile(r'\*\*(?:Дата|Date)[:：]\*\*\s*([^\|\n]+)')
MD_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^)\s]+)\)')
BARE_URL_RE = re.compile(r'(?<![\(\["])\bhttps?://[^\s)<>"\]]+')

# Acronyms (2-6 uppercase letters/digits) and TitleCase tech words.
ACRONYM_RE = re.compile(r'\b[A-Z][A-Z0-9]{1,5}\b')


def parse_meeting(path: Path):
    """Parse one meeting MDX into a structured record. Returns None if unusable."""
    try:
        content = path.read_text(encoding='utf-8')
    except OSError as e:
        print(f"  ! cannot read {path}: {e}")
        return None

    fm, body = split_frontmatter(content)

    lab_match = re.search(r'([a-z0-9-]+)-internal-(\d+)', str(path))
    slug = lab_match.group(1) if lab_match else "claude-code"
    lab = lab_match.group(2).zfill(2) if lab_match else "??"
    number = path.stem.zfill(2) if path.stem.isdigit() else path.stem

    title = str(fm.get('title', '')).strip()
    description = str(fm.get('description', '')).strip()

    yt_id = None
    m = YT_EMBED_RE.search(body) or YT_WATCH_RE.search(body)
    if m:
        yt_id = m.group(1)

    fathom = None
    fm_match = FATHOM_RE.search(body)
    if fm_match:
        fathom = fm_match.group(0)

    date = None
    d = DATE_RE.search(body)
    if d:
        date = d.group(1).strip()

    # Placeholder detection — frontmatter left unfilled by the pipeline.
    placeholders = [p for p in ("[Название встречи]", "[Краткое описание встречи]",
                                "[Дата встречи]") if p in content]

    links = []
    for label, url in MD_LINK_RE.findall(body):
        links.append((label.strip(), url.strip()))
    for url in BARE_URL_RE.findall(body):
        links.append(("", url))

    return {
        "lab": lab,
        "slug": slug,
        "number": number,
        "title": title,
        "description": description,
        "date": date,
        "youtube_id": yt_id,
        "fathom_url": fathom,
        "placeholders": placeholders,
        "links": links,
        "body": body,
        "path": str(path),
        "url": f"https://{site_domain()}/{slug}-lab-{lab}/meetings/{number}",
    }


def collect_meetings():
    site = docs_site_dir()
    base = site / 'content' / 'docs'
    if not base.exists():
        print(f"FATAL: docs content dir not found: {base}")
        print("Set DOCS_SITE_DIR in .env to your local agency-docs checkout.")
        sys.exit(1)

    meeting_files = sorted(base.glob('*-internal-*/meetings/*.mdx'))
    records = []
    for f in meeting_files:
        if not f.stem.isdigit():
            continue  # skip index/meta pages
        rec = parse_meeting(f)
        if rec:
            records.append(rec)
    records.sort(key=lambda r: (r["slug"], r["lab"], r["number"]))
    return records


# ---------------------------------------------------------------------------
# 1. Database (meetings index)
# ---------------------------------------------------------------------------

def build_database(records, dry_run):
    page = out_path('AGG_DB_PAGE', 'content/docs/database.mdx')
    data = out_path('AGG_DB_JSON', 'public/data/meetings.json')

    rows = []
    for r in records:
        yt = f"[▶](https://youtu.be/{r['youtube_id']})" if r['youtube_id'] else "—"
        fa = f"[Fathom]({r['fathom_url']})" if r['fathom_url'] else "—"
        title = mdx_escape(r['title']) or "—"
        rows.append(
            f"| {r['lab']} | {r['number']} | {mdx_escape(r['date']) or '—'} "
            f"| [{title}]({r['url']}) | {yt} | {fa} |"
        )

    mdx = (
        "---\n"
        'title: "База встреч"\n'
        "description: Полный индекс всех встреч лаборатории Claude Code.\n"
        "---\n\n"
        "{/* GENERATED by agency-docs-updater/scripts/rebuild_aggregations.py — do not edit by hand. */}\n\n"
        f"Всего встреч: **{len(records)}**. Обновлено: {datetime.now(timezone.utc):%Y-%m-%d}.\n\n"
        "| Лаб | № | Дата | Встреча | Видео | Запись |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        + "\n".join(rows) + "\n"
    )

    json_payload = [
        {k: r[k] for k in ("lab", "number", "title", "description", "date",
                           "youtube_id", "fathom_url", "url")}
        for r in records
    ]

    _write(page, mdx, dry_run)
    _write(data, json.dumps(json_payload, ensure_ascii=False, indent=2), dry_run)
    return [page, data]


# ---------------------------------------------------------------------------
# 2. Glossary (persisted term store + generated page)
# ---------------------------------------------------------------------------

def load_glossary_store():
    store = out_path('AGG_GLOSSARY_STORE', '.agency-glossary.json')
    if store.exists():
        try:
            return json.loads(store.read_text(encoding='utf-8')), store
        except json.JSONDecodeError:
            print(f"  ! glossary store is corrupt, starting fresh: {store}")
    return {}, store


def extract_terms(records):
    """Return {term: set(meeting_urls)} of candidate technical terms."""
    seen = defaultdict(set)
    for r in records:
        text = f"{r['title']} {r['description']} {r['body']}"
        # Strip URLs first so referral codes / IDs inside links (e.g. .../r/GLEB3)
        # don't get mistaken for acronyms.
        text = re.sub(r'https?://\S+', ' ', text)
        for term in ACRONYM_RE.findall(text):
            seen[term].add(r['url'])
        low = text.lower()
        for phrase in KNOWN_PHRASES:
            if phrase.lower() in low:
                seen[phrase].add(r['url'])
    # Drop trivial false positives.
    noise = {"HTTP", "HTTPS", "HTML", "JSON", "URL", "ID", "OK", "PM", "AM", "TODO"}
    return {t: u for t, u in seen.items() if t not in noise and len(u) >= 1}


def build_glossary(records, dry_run):
    store, store_path = load_glossary_store()
    candidates = extract_terms(records)

    # Merge: seed < persisted store; record mentions; flag new undefined terms.
    new_terms = []
    for term, urls in sorted(candidates.items()):
        entry = store.get(term, {})
        if "definition" not in entry:
            seed_def = SEED_TERMS.get(term, "")
            entry["definition"] = seed_def
            if not seed_def:
                new_terms.append(term)
        entry["mentions"] = sorted(urls)
        store[term] = entry

    # Persist the store (so definitions survive and new terms can be filled in).
    _write(store_path, json.dumps(store, ensure_ascii=False, indent=2), dry_run)

    lines = []
    for term in sorted(store, key=str.lower):
        entry = store[term]
        definition = mdx_escape(entry.get("definition", "")) or "_TODO: definition needed_"
        mentions = entry.get("mentions", [])
        ref = f" ({len(mentions)} встреч)" if mentions else ""
        lines.append(f"### {mdx_escape(term)}\n\n{definition}{ref}\n")

    mdx = (
        "---\n"
        'title: "Глоссарий"\n'
        "description: Технические термины, встречающиеся в материалах лаборатории.\n"
        "---\n\n"
        "{/* GENERATED by agency-docs-updater/scripts/rebuild_aggregations.py — "
        "edit definitions in .agency-glossary.json, not here. */}\n\n"
        + "\n".join(lines) + "\n"
    )
    page = out_path('AGG_GLOSSARY_PAGE', 'content/docs/glossary.mdx')
    _write(page, mdx, dry_run)

    if new_terms:
        print(f"  → {len(new_terms)} NEW term(s) need definitions: {', '.join(new_terms)}")
        print(f"    Add definitions to: {store_path}")
    return page, new_terms


# ---------------------------------------------------------------------------
# 3. Global library (all external links across meetings)
# ---------------------------------------------------------------------------

def build_library(records, dry_run):
    # url -> {label, domain, mentions:set(meeting_url)}
    by_url = {}
    self_domain = site_domain()
    # Per-meeting media (the Fathom recording and the YouTube video) already live
    # in the database; the library is for genuine external resources, so skip them.
    media_hosts = {"youtube.com", "youtu.be", "fathom.video"}
    for r in records:
        for label, url in r['links']:
            host = urlparse(url).netloc.lower()
            if host.startswith('www.'):
                host = host[4:]
            if not host or self_domain in host or host in media_hosts:
                continue  # skip self-links and per-meeting video/recording links
            item = by_url.setdefault(url, {"label": label, "domain": host, "mentions": set()})
            if label and not item["label"]:
                item["label"] = label
            item["mentions"].add(r['url'])

    by_domain = defaultdict(list)
    for url, item in by_url.items():
        by_domain[item["domain"]].append((url, item))

    sections = []
    for domain in sorted(by_domain):
        sections.append(f"### {mdx_escape(domain)}\n")
        for url, item in sorted(by_domain[domain], key=lambda x: x[0]):
            label = mdx_escape(item["label"]) or url
            n = len(item["mentions"])
            sections.append(f"- [{label}]({url}){f' — {n} упоминаний' if n > 1 else ''}")
        sections.append("")

    mdx = (
        "---\n"
        'title: "Библиотека ресурсов"\n'
        "description: Все внешние ссылки и ресурсы, упомянутые на встречах.\n"
        "---\n\n"
        "{/* GENERATED by agency-docs-updater/scripts/rebuild_aggregations.py — do not edit by hand. */}\n\n"
        f"Всего ресурсов: **{len(by_url)}** из {len(by_domain)} источников.\n\n"
        + "\n".join(sections) + "\n"
    )
    page = out_path('AGG_LIBRARY_PAGE', 'content/docs/library.mdx')
    _write(page, mdx, dry_run)
    return page


# ---------------------------------------------------------------------------
# Write helper
# ---------------------------------------------------------------------------

def _write(path: Path, content: str, dry_run: bool):
    if dry_run:
        print(f"  [dry-run] would write {path} ({len(content)} bytes)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"  ✓ wrote {path} ({len(content)} bytes)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_env()
    ap = argparse.ArgumentParser(description="Rebuild agency-docs site-wide aggregations.")
    ap.add_argument('--dry-run', action='store_true',
                    help="Parse and report, but write nothing.")
    ap.add_argument('--only', choices=['database', 'glossary', 'library'],
                    help="Rebuild a single aggregation.")
    args = ap.parse_args()

    print(f"Scanning meetings under {docs_site_dir() / 'content' / 'docs'} ...")
    records = collect_meetings()
    print(f"Found {len(records)} meeting(s) across "
          f"{len(set(r['lab'] for r in records))} lab(s).")

    flagged = [r for r in records if r['placeholders'] or not r['youtube_id']]
    if flagged:
        print(f"⚠️  {len(flagged)} meeting(s) look incomplete "
              f"(unfilled placeholders or missing video) — see the audit workflow:")
        for r in flagged:
            issues = []
            if r['placeholders']:
                issues.append("placeholders")
            if not r['youtube_id']:
                issues.append("no video")
            print(f"    lab {r['lab']} #{r['number']}: {', '.join(issues)}")

    written = []
    if args.only in (None, 'database'):
        print("Building database (meetings index)...")
        written += build_database(records, args.dry_run)
    if args.only in (None, 'glossary'):
        print("Building glossary...")
        page, new_terms = build_glossary(records, args.dry_run)
        written.append(page)
    if args.only in (None, 'library'):
        print("Building global library...")
        written.append(build_library(records, args.dry_run))

    print(f"\nDone. {'Would write' if args.dry_run else 'Wrote'} {len(written)} file(s).")
    if not args.dry_run:
        print("Next: cd $DOCS_SITE_DIR && npm run build  (verify MDX compiles), then commit.")


if __name__ == '__main__':
    main()
