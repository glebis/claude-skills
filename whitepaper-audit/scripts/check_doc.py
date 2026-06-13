#!/usr/bin/env python3
"""Deterministic lane of the whitepaper-audit skill.

Stdlib-only checks over a markdown document:
  readability        Flesch-Kincaid grade (heuristic syllables; trend-level)
  acronym-undefined  acronyms used before any definition (allowlist-aware)
  structure          required blocks present (title, abstract, date, author,
                     limitations, glossary)
  links              relative links exist on disk; http(s) HEAD/GET unless --offline

Outputs a JSON list of findings (schema per DESIGN.md v0.2) on stdout, exit 0.
Never crashes on malformed markdown.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------- findings

def _finding(check_id, severity, confidence, location, evidence, rationale, fix):
    return {
        "check_id": check_id,
        "lane": "script",
        "severity": severity,
        "confidence": confidence,
        "location": location,
        "evidence_quote": evidence,
        "rationale": rationale,
        "suggested_fix": fix,
    }


# ---------------------------------------------------------------- markdown

CODE_BLOCK_RE = re.compile(r"```.*?(```|\Z)", re.S)
TABLE_ROW_RE = re.compile(r"^\s*\|.*$", re.M)
HEADING_RE = re.compile(r"^#{1,6} .*$", re.M)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]*)\)")
URL_RE = re.compile(r"https?://\S+")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def strip_markdown(text: str) -> str:
    """Remove code blocks, tables, headings, URLs, comments; keep link text."""
    text = CODE_BLOCK_RE.sub(" ", text)
    text = HTML_COMMENT_RE.sub(" ", text)
    text = HEADING_RE.sub(" ", text)
    text = TABLE_ROW_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    text = URL_RE.sub(" ", text)
    text = re.sub(r"[*_`>#]+", " ", text)
    return re.sub(r"[ \t]+", " ", text)


# ---------------------------------------------------------------- readability

VOWELS = "aeiouy"


def _syllables(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    groups = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and groups > 1 and not word.endswith(("le", "ee")):
        groups -= 1
    return max(1, groups)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.split()) >= 3]


def fk_grade(text: str) -> float:
    """Flesch-Kincaid grade level (heuristic, trend-level only)."""
    sents = _sentences(text) or [text]
    words = [w for s in sents for w in re.findall(r"[A-Za-z']+", s)]
    if not words:
        return 0.0
    syl = sum(_syllables(w) for w in words)
    return 0.39 * (len(words) / len(sents)) + 11.8 * (syl / len(words)) - 15.59


def hardest_sentences(text: str, n: int = 5) -> list[str]:
    sents = _sentences(strip_markdown(text))
    return sorted(sents, key=fk_grade, reverse=True)[:n]


def _readability_findings(text: str, target: float) -> list[dict]:
    findings = []
    sections = re.split(r"^(#{1,3} .*)$", text, flags=re.M)
    # pair headings with bodies; leading chunk = preamble
    pairs = [("(preamble)", sections[0])]
    for i in range(1, len(sections) - 1, 2):
        pairs.append((sections[i].lstrip("# ").strip(), sections[i + 1]))
    critical = re.compile(r"abstract|summary|one paragraph|introduction|overview", re.I)
    for name, body in pairs:
        prose = strip_markdown(body)
        if len(prose.split()) < 30:
            continue
        grade = fk_grade(prose)
        if grade <= target:
            continue
        is_critical = bool(critical.search(name))
        sev = "P1" if (is_critical and grade > target + 3) else "P2"
        top = hardest_sentences(body, 3)
        findings.append(_finding(
            "readability", sev, "medium", f"section: {name}",
            (top[0][:200] if top else prose[:200]),
            f"FK grade ≈ {grade:.1f} exceeds target {target:g} "
            f"(heuristic, trend-level).",
            "Shorten sentences; prefer concrete words. Hardest sentences: "
            + " | ".join(t[:120] for t in top),
        ))
    return findings


# ---------------------------------------------------------------- acronyms

ALLOWLIST = {
    "PDF", "URL", "URLS", "USA", "EU", "US", "UK", "IT", "AI", "API", "ID",
    "IDS", "FAQ", "ISO", "CEO", "CTO", "OK", "TV", "GB", "MB", "KB", "CPU",
    "GPU", "RAM", "HTML", "HTTP", "HTTPS", "JSON", "CSV", "YAML", "TODO",
    "README", "MIT", "CC", "BY",
}
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,5}\b")


def _acronym_findings(text: str, allowlist=frozenset()) -> list[dict]:
    body = CODE_BLOCK_RE.sub(" ", text)
    body = URL_RE.sub(" ", body)
    allow = ALLOWLIST | {a.upper() for a in allowlist}
    glossary = set()
    gloss_m = re.search(r"^#{1,3} .*glossar.*$", body, re.I | re.M)
    if gloss_m:
        for row in TABLE_ROW_RE.findall(body[gloss_m.end():]):
            glossary.update(a.upper() for a in ACRONYM_RE.findall(row))
    findings, seen = [], set()
    for m in ACRONYM_RE.finditer(body):
        acro = m.group(0)
        base = acro[:-1] if acro.endswith("S") and len(acro) > 2 else acro
        if base in seen or acro in seen:
            continue
        seen.add(base)
        if base in allow or acro in allow or base in glossary:
            continue
        before = body[:m.end() + 200]  # definition may trail the first use
        defined = (
            re.search(re.escape(base) + r"s?\s*\(", before) and
            re.search(re.escape(base) + r"s?\s*\([A-Z]", before)
        ) or re.search(r"\(\s*" + re.escape(base) + r"s?\s*\)", before)
        if defined:
            continue
        line = body[:m.start()].count("\n") + 1
        findings.append(_finding(
            "acronym-undefined", "P1", "high", f"line {line}",
            body[max(0, m.start() - 40):m.end() + 40].strip(),
            f"Acronym '{base}' is used without a definition at or before "
            "first use, and is not in the glossary.",
            f"Define on first use: 'Full Term ({base})' — or add a glossary "
            "entry.",
        ))
    return findings


# ---------------------------------------------------------------- structure

BLOCKS = {
    "title": (r"^# .+", "P1", "high"),
    "abstract/summary": (r"^#{1,3} .*(abstract|summary|one paragraph|overview|tl;dr)", "P1", "medium"),
    "date/version": (r"version\s*\d|\b(19|20)\d{2}\b", "P1", "medium"),
    "author": (r"author|contributors|by\s+[A-Z][a-z]+ [A-Z]", "P1", "low"),
    "limitations": (r"^#{1,3} .*(limitation|caveat|known issue)", "P0", "medium"),
    "glossary": (r"^#{1,3} .*(glossar|terminolog|definitions)", "P2", "medium"),
}


def _structure_findings(text: str) -> list[dict]:
    head = "\n".join(text.splitlines()[:30])
    findings = []
    for name, (pat, sev, conf) in BLOCKS.items():
        scope = head if name in {"title", "date/version", "author"} else text
        if re.search(pat, scope, re.I | re.M):
            continue
        findings.append(_finding(
            "structure", sev, conf, "document", f"missing block: {name}",
            f"No {name} block detected. "
            + ("Empirical claims without a limitations section are a trust "
               "risk." if name == "limitations" else
               "Expected in a practitioner-facing white paper."),
            f"Add a {name} section."
            + (" If terms are defined inline throughout, a glossary may be "
               "optional." if name == "glossary" else ""),
        ))
    return findings


# ---------------------------------------------------------------- links

def _check_url(url: str, timeout: float = 5.0) -> str:
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method,
                                         headers={"User-Agent": "whitepaper-audit/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status < 400:
                    return "ok"
                if resp.status in (404, 410):
                    return "broken"
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return "broken"
            return "uncertain"
        except Exception:
            continue
    return "unreachable"


def _link_findings(text: str, base_dir, offline: bool) -> list[dict]:
    findings = []
    body = CODE_BLOCK_RE.sub(" ", text)
    for m in LINK_RE.finditer(body):
        label, target = m.groups()
        if not target or target.startswith(("#", "mailto:")):
            continue
        if target.startswith(("http://", "https://")):
            if offline:
                continue
            if _check_url(target) != "broken":
                continue
            status = "broken (HTTP 404/410)"
        else:
            if base_dir is None:
                continue
            if (Path(base_dir) / target.split("#")[0]).exists():
                continue
            status = "missing on disk"
        line = body[:m.start()].count("\n") + 1
        findings.append(_finding(
            "links", "P1", "high", f"line {line}",
            f"[{label}]({target})",
            f"Link target is {status}.",
            "Fix the path/URL or remove the link.",
        ))
    return findings


# ---------------------------------------------------------------- entry

def check_document(text: str, *, base_dir=None, offline: bool = True,
                   target_grade: float = 13.0, allowlist=()) -> list[dict]:
    try:
        return (
            _readability_findings(text, target_grade)
            + _acronym_findings(text, allowlist)
            + _structure_findings(text)
            + _link_findings(text, base_dir, offline)
        )
    except Exception as e:  # never crash on malformed input
        return [_finding("internal", "P2", "low", "document", str(e)[:200],
                         "check_doc internal error on this input.",
                         "Report this input to the skill maintainer.")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", type=Path)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--target-grade", type=float, default=13.0)
    ap.add_argument("--allow", action="append", default=[],
                    help="extra allowlisted acronyms")
    args = ap.parse_args(argv)
    text = args.file.read_text(encoding="utf-8", errors="replace")
    findings = check_document(
        text, base_dir=args.file.parent, offline=args.offline,
        target_grade=args.target_grade, allowlist=args.allow)
    json.dump(findings, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
