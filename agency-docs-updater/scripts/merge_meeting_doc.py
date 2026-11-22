#!/usr/bin/env python3
"""Smart, idempotent merge of pipeline output into an existing meeting MDX.

Meeting pages often exist before the meeting (plan, slides link, practice
notes, curated frontmatter). The pipeline owns only a few *managed blocks*;
everything else is the author's and is kept verbatim.

Managed blocks are wrapped in MDX comments so re-runs replace exactly them:
    {/* agency:recording */} ... {/* /agency:recording */}
First run (no markers yet), per block:
  1. a heading that already means this block (e.g. "## Запись", "## Видео",
     "## Конспект", "## Summary") -> that section is replaced and wrapped;
  2. otherwise the block is inserted: recording after the date line,
     summary after recording, transcript after summary.
Also: pending notes ("Запись появится после встречи", "Recording will be
posted…") are dropped; frontmatter keys are kept, except placeholder values
("[Название встречи]", empty) which are filled from the pipeline.

CLI:
  merge_meeting_doc.py EXISTING.mdx --block recording=rec.md --block summary=sum.md \
      [--set title="…" --set description="…"] [--lang ru] [--dry-run]
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

ORDER = ["recording", "summary", "transcript"]
HEADINGS = {
    "ru": {"recording": "Запись", "summary": "Конспект", "transcript": "Транскрипт"},
    "en": {"recording": "Recording", "summary": "Summary", "transcript": "Transcript"},
}
ALIASES = {
    "recording": r"запись|видео|запись встречи|recording|video",
    "summary": r"конспект|краткое содержание|итоги|summary|recap|notes",
    "transcript": r"транскрипт|расшифровка|transcript",
}
# Pending notes: any short line saying the recording/materials will appear later.
# GDA 01 #02: «Запись, слайды и материалы появятся здесь после встречи.» (comma + plural).
PENDING_RE = re.compile(
    r"^\s*[*_>]*\s*(?=[^\n]{0,200}$)(?=[^\n]*(запис|видео|материал|слайд|recording|video|materials|slides))"
    r"[^\n]*(появ(ится|ятся)|обрабатывается|после встречи|will appear|is being processed|coming soon|after the (meeting|session))"
    r"[^\n]*$", re.I | re.M)
# Placeholder frontmatter: bracket templates, empty, or the bare generic values the
# course scaffolding writes ("Встреча 02", "Встреча 02 лаборатории Goal-Driven AI.").
PLACEHOLDER_RE = re.compile(
    r"^\s*$|\[[^\]]*(назван|описан|дата|title|description)[^\]]*\]|"
    r"^(Встреча|Meeting|Session|Занятие)\s*\d{1,3}\.?$|"
    r"^(Встреча|Meeting|Session|Занятие)\s*\d{1,3} (лаборатории|of the) [^.]{0,60}\.?$", re.I)
DATE_LINE_RE = re.compile(r"^\*\*(Дата|Date)[:：]?\*\*", re.M)


def _open(name):
    return "{/* agency:%s */}" % name


def _close(name):
    return "{/* /agency:%s */}" % name


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)


def merge_frontmatter(fm, updates, changes):
    lines = fm.splitlines()
    for key, val in updates.items():
        rx = re.compile(rf"^{re.escape(key)}:\s*(.*)$")
        idx = next((i for i, l in enumerate(lines) if rx.match(l)), None)
        quoted = '"%s"' % val.replace('"', '\\"')
        if idx is None:
            lines.append(f"{key}: {quoted}")
            changes.append(f"frontmatter: added {key}")
        elif PLACEHOLDER_RE.search(rx.match(lines[idx]).group(1).strip('"\'')):
            lines[idx] = f"{key}: {quoted}"
            changes.append(f"frontmatter: filled placeholder {key}")
    return "\n".join(lines)


def _section_bounds(body, name):
    """Find an existing '## <alias>' section -> (start, end) or None."""
    m = re.search(rf"^(##)\s+(?:{ALIASES[name]})\b[^\n]*\n", body, re.I | re.M)
    if not m:
        return None
    nxt = re.search(r"^#{1,2}\s|^---\s*$", body[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(body)
    return m.start(), end


def _render(name, content, lang):
    head = HEADINGS.get(lang, HEADINGS["ru"])[name]
    # nest the block's own headings under its "## <head>" (## -> ###, …)
    content = re.sub(r"^(#{2,5}) ", r"#\1 ", content, flags=re.M)
    return f"{_open(name)}\n## {head}\n\n{content.strip()}\n{_close(name)}\n\n"


def merge_body(body, blocks, lang, changes):
    body = PENDING_RE.sub("", body)
    for name in ORDER:
        if name not in blocks:
            continue
        rendered = _render(name, blocks[name], lang)
        marked = re.search(re.escape(_open(name)) + r".*?" + re.escape(_close(name)) + r"\n*", body, re.S)
        if marked:
            body = body[:marked.start()] + rendered + body[marked.end():]
            changes.append(f"{name}: replaced managed block")
            continue
        bounds = _section_bounds(body, name)
        if bounds:
            body = body[:bounds[0]] + rendered + body[bounds[1]:]
            changes.append(f"{name}: took over existing section")
            continue
        # insert after the previous managed block, else after the date line, else at top
        prev = [n for n in ORDER[:ORDER.index(name)] if _close(n) in body]
        if prev:
            pos = body.index(_close(prev[-1])) + len(_close(prev[-1]))
            pos = body.index("\n", pos) + 1 if "\n" in body[pos:] else len(body)
            while body[pos:pos + 1] == "\n":
                pos += 1
        else:
            d = DATE_LINE_RE.search(body)
            pos = (body.find("\n\n", d.end()) + 2) if d and body.find("\n\n", d.end()) != -1 else \
                (len(body) if d else 0)
        body = body[:pos] + rendered + body[pos:]
        changes.append(f"{name}: inserted")
    return re.sub(r"\n{3,}", "\n\n", body)


def merge(text, blocks, updates=None, lang="ru", keep_frontmatter=False):
    """Return (merged_text, changes)."""
    changes = []
    fm, body = split_frontmatter(text)
    if updates and not keep_frontmatter:
        fm = merge_frontmatter(fm, updates, changes)
    body = merge_body(body, blocks, lang, changes)
    out = (f"---\n{fm}\n---\n\n" if fm else "") + body.lstrip("\n")
    return out, changes


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mdx")
    p.add_argument("--block", action="append", default=[], help="name=path.md")
    p.add_argument("--set", action="append", default=[], help="frontmatter key=value")
    p.add_argument("--lang", default="ru")
    p.add_argument("--keep-frontmatter", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    blocks = {k: Path(v).read_text(encoding="utf-8") for k, v in (b.split("=", 1) for b in a.block)}
    updates = dict(s.split("=", 1) for s in a.set)
    path = Path(a.mdx)
    old = path.read_text(encoding="utf-8")
    new, changes = merge(old, blocks, updates, a.lang, a.keep_frontmatter)
    for c in changes:
        print("merge:", c, file=sys.stderr)
    if a.dry_run:
        sys.stdout.writelines(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                                   str(path), str(path) + " (merged)"))
    elif new != old:
        path.write_text(new, encoding="utf-8")
        print(f"merge: wrote {path}", file=sys.stderr)
    else:
        print("merge: no changes", file=sys.stderr)


if __name__ == "__main__":
    main()
