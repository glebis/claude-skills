#!/usr/bin/env python3
"""Minimal safe file operations for this Obsidian vault: move/rename and trash.

Both commands are dry-run by default; pass --apply to change anything.

  vault_fs.py mv SRC DST [--apply]      move or rename a note/attachment (DST may be a folder/)
  vault_fs.py mv --batch moves.tsv      many moves in one vault scan (source<TAB>dest per line)
  vault_fs.py rm PATH... [--apply]      send to macOS Trash via `trash`; refuses while other
                                        notes still link to it (override with --force)

Link rewriting mirrors Obsidian's "Automatically update internal links":
wikilinks ([[x]], ![[x]], with #heading, #^block, |alias) and markdown links
([t](x.md)) that resolve to a moved file are rewritten in their original style,
including bare [[Old]] links when a note is renamed. Relative links inside a
moved note are re-based on its new folder. Links inside code are left alone.
Other scripts move files through move_files(root, pairs), the engine behind --batch.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from urllib.parse import quote, unquote

DEFAULT_VAULT = os.path.expanduser("~/Brains/brain")
WIKILINK_RE = re.compile(r"(!?)\[\[([^\[\]\n]+?)\]\]")
MDLINK_RE = re.compile(r"(!?\[[^\]\n]*\]\()(<[^>\n]+>|[^)\s]+)((?:\s+\"[^\"\n]*\")?\))")
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\1[ \t]*$", re.M | re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def norm(path: str) -> str:
    path = os.path.normpath(path.replace("\\", "/")).replace("\\", "/")
    return "" if path == "." else path


def is_md(rel: str) -> bool:
    return rel.lower().endswith(".md")


def link_key(rel: str) -> str:
    """Name a bare wikilink uses for this file: stem for notes, full name otherwise."""
    name = os.path.basename(rel)
    return (name[:-3] if is_md(name) else name).lower()


class Index:
    """Case-insensitive file index that resolves links the way Obsidian does."""

    def __init__(self, files):
        self.files = set(files)
        self.lower = {f.lower(): f for f in self.files}
        self.by_key = defaultdict(list)
        for f in self.files:
            self.by_key[link_key(f)].append(f)

    @classmethod
    def scan(cls, root: str) -> "Index":
        files = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                if not name.startswith("."):
                    files.append(norm(os.path.relpath(os.path.join(dirpath, name), root)))
        return cls(files)

    def lookup(self, path: str) -> str | None:
        path = norm(path)
        for cand in (path + ".md", path):
            if cand.lower() in self.lower:
                return self.lower[cand.lower()]
        return None

    def resolve_wiki(self, target: str, src: str) -> str | None:
        target = target.strip()
        if not target:
            return None
        if target.startswith(("./", "../")):
            return self.lookup(os.path.join(os.path.dirname(src), target))
        if "/" in target:
            hit = self.lookup(target)
            if hit:
                return hit
            # Obsidian also accepts a trailing partial path: [[sub/Note]] -> x/sub/Note.md
            tail = "/" + target.lower()
            cands = [f for f in self.files if f.lower().endswith((tail + ".md", tail))]
            return min(cands, key=len) if cands else None
        key = target[:-3] if is_md(target) else target
        cands = self.by_key.get(key.lower(), [])
        if not cands:
            return None
        same_dir = [c for c in cands if os.path.dirname(c) == os.path.dirname(src)]
        return (same_dir or sorted(cands, key=lambda c: (len(c), c)))[0]

    def resolve_md(self, href: str, src: str) -> tuple[str, str] | None:
        """Return (file, style) for a markdown-link href; style is 'rel' or 'root'."""
        if not href or href.startswith("#") or SCHEME_RE.match(href):
            return None
        path = unquote(href.split("#", 1)[0])
        if not path:
            return None
        rel = norm(os.path.join(os.path.dirname(src), path))
        if rel.lower() in self.lower:
            return self.lower[rel.lower()], "rel"
        root = norm(path.lstrip("/"))
        if root.lower() in self.lower:
            return self.lower[root.lower()], "root"
        return None


def code_spans(text: str) -> list[tuple[int, int]]:
    spans = [m.span() for m in FENCE_RE.finditer(text)]
    spans += [m.span() for m in INLINE_CODE_RE.finditer(text)]
    return spans


def in_code(pos: int, spans) -> bool:
    return any(a <= pos < b for a, b in spans)


def bare_link_text(old_target: str, new_rel: str, unique: bool) -> str:
    """Text for a bare [[old_target]] whose note was renamed (or whose name is no longer unique).

    `unique` says whether the new name resolves to new_rel from the linking note.
    """
    # TODO(user): decide how a renamed bare link should read. Current behaviour is
    # Obsidian's: [[Old]] -> [[New]], or a full path when New is ambiguous.
    # Alternative: keep prose unchanged by returning f"{new}|{old_target}" when
    # the link has no alias (caller passes only links without an alias here).
    new = os.path.basename(new_rel)[:-3] if is_md(new_rel) else os.path.basename(new_rel)
    if not unique:
        new = new_rel[:-3] if is_md(new_rel) else new_rel
    return new


def rewrite(text: str, src: str, moves: dict, old: Index, new: Index, log: list) -> str:
    """Rewrite links in one note. `src` is its old path; moves maps old -> new paths."""
    new_src = moves.get(src, src)
    new_dir = os.path.dirname(new_src)
    spans = code_spans(text)

    def wiki(m: re.Match) -> str:
        if in_code(m.start(), spans):
            return m.group(0)
        bang, inner = m.groups()
        target, sep, alias = inner.partition("|")
        escaped = target.endswith("\\")  # [[a\|b]] inside tables
        if escaped:
            target = target[:-1]
        path, hsep, sub = target.partition("#")
        hit = old.resolve_wiki(path, src)
        if hit is None or (hit not in moves and src not in moves):
            return m.group(0)
        dest = moves.get(hit, hit)
        keep_ext = is_md(path.strip()) or not is_md(dest)
        out = dest if keep_ext else dest[:-3]
        stripped = path.strip()
        if stripped.startswith(("./", "../")):
            out = os.path.relpath(out, new_dir or ".")
        elif hit not in moves:
            return m.group(0)  # only the linking note moved; bare and vault-path links still resolve
        elif "/" not in stripped:
            if link_key(dest) == link_key(hit) and new.resolve_wiki(stripped, new_src) == dest:
                return m.group(0)
            # Don't lean on tie-breaks between same-named notes: only a sole match or a sibling is safe
            cands = new.by_key[link_key(dest)]
            unique = cands == [dest] or os.path.dirname(dest) == new_dir
            if sep:
                out = os.path.basename(out) if unique else out
            else:
                out, sep, alias = bare_link_text(stripped, dest, unique).partition("|")
        new_inner = out + ("\\" if escaped else "") + hsep + sub + sep + alias
        res = f"{bang}[[{new_inner}]]"
        if res != m.group(0):
            log.append((m.group(0), res))
        return res

    def md(m: re.Match) -> str:
        if in_code(m.start(), spans):
            return m.group(0)
        head, href, tail = m.groups()
        angled = href.startswith("<")
        raw = href[1:-1] if angled else href
        hit = old.resolve_md(raw, src)
        if hit is None or (hit[0] not in moves and src not in moves):
            return m.group(0)
        target, style = hit
        dest = moves.get(target, target)
        if style == "root" and target not in moves:
            return m.group(0)
        path = os.path.relpath(dest, new_dir or ".") if style == "rel" else dest
        frag = "#" + raw.split("#", 1)[1] if "#" in raw else ""
        path = path if angled or "%" not in raw and " " not in path else quote(path, safe="/")
        new_href = f"<{path}{frag}>" if angled else path + frag
        res = head + new_href + tail
        if res != m.group(0):
            log.append((m.group(0), res))
        return res

    return MDLINK_RE.sub(md, WIKILINK_RE.sub(wiki, text))


def needles(paths) -> re.Pattern:
    stems = set()
    for p in paths:
        stem = os.path.splitext(os.path.basename(p))[0] if is_md(p) else os.path.basename(p)
        stems |= {stem, quote(stem)}
    return re.compile(b"|".join(re.escape(s.encode()) for s in stems), re.I)


def linking_notes(root: str, index: Index, targets, extra=()):
    """Yield (rel, text) for notes that may link to targets, plus every note in extra."""
    pat = needles(targets)
    for rel in sorted(index.files):
        if not is_md(rel):
            continue
        with open(os.path.join(root, rel), "rb") as fh:
            raw = fh.read()
        if rel in extra or pat.search(raw):
            yield rel, raw.decode("utf-8", errors="replace")


class MoveError(ValueError):
    """A move plan was refused; nothing has been changed."""


def plan_moves(root: str, index: Index, pairs) -> dict:
    moves = {}
    taken = set()
    for src, dst in pairs:
        hit = index.lookup(src)
        if hit is None:
            raise MoveError(f"Source not found: {src}")
        if dst.endswith("/") or os.path.isdir(os.path.join(root, dst)):
            dst = os.path.join(dst, os.path.basename(hit))
        dst = norm(dst)
        if is_md(hit) and not is_md(dst):
            dst += ".md"
        if dst.startswith(".."):
            raise MoveError(f"Destination outside vault: {dst}")
        clash = index.lower.get(dst.lower())
        if (clash and clash != hit) or dst.lower() in taken:
            raise MoveError(f"Destination already exists: {dst}")
        if hit in moves:
            raise MoveError(f"Duplicate source: {hit}")
        taken.add(dst.lower())
        moves[hit] = dst
    return moves


def move_files(root: str, pairs, apply: bool = True):
    """Move (src, dst) vault-relative pairs and rewrite links in one vault scan.

    Library entry point for other scripts (the archivers). Validates the whole
    batch before touching anything and raises MoveError if any pair is refused.
    Returns (moves, edits, warnings); edits maps note -> (new text, link log).
    """
    if not pairs:
        return {}, {}, []
    old = Index.scan(root)
    moves = plan_moves(root, old, pairs)
    new = Index([moves.get(f, f) for f in old.files])

    warnings = []
    for dest in moves.values():
        others = [f for f in new.by_key[link_key(dest)] if f != dest]
        if others:
            warnings.append(f"name of {dest} is shared with {others[0]}; bare links pick by folder")

    edits = {}
    for rel, text in linking_notes(root, old, moves, extra=moves):
        log = []
        updated = rewrite(text, rel, moves, old, new, log)
        if updated != text:
            edits[moves.get(rel, rel)] = (updated, log)

    if apply:
        for src, dst in moves.items():
            os.makedirs(os.path.join(root, os.path.dirname(dst)), exist_ok=True)
            os.rename(os.path.join(root, src), os.path.join(root, dst))
        for rel, (updated, _) in edits.items():
            with open(os.path.join(root, rel), "w", encoding="utf-8") as fh:
                fh.write(updated)
    return moves, edits, warnings


def cmd_mv(args) -> int:
    root = os.path.abspath(args.vault)
    if args.batch:
        with open(args.batch, encoding="utf-8") as fh:
            rows = [l.rstrip("\n").split("\t") for l in fh if l.strip() and not l.lstrip().startswith("#")]
        bad = [r for r in rows if len(r) != 2]
        if bad:
            sys.exit(f"{args.batch}: expected 'source<TAB>dest', got {bad[0]!r}")
        pairs = [(s.strip(), d.strip()) for s, d in rows]
    elif args.src and args.dst:
        pairs = [(args.src, args.dst)]
    else:
        sys.exit("mv needs SRC DST or --batch FILE")

    try:
        moves, edits, warnings = move_files(root, pairs, apply=args.apply)
    except MoveError as e:
        sys.exit(str(e))

    for w in warnings:
        print(f"warning: {w}")
    for src, dst in moves.items():
        print(f"{'move' if args.apply else 'would move'}  {src} -> {dst}")
    for rel, (_, log) in sorted(edits.items()):
        print(f"  {rel}: {len(log)} link(s)")
        for before, after in log[: args.show]:
            print(f"      {before}  ->  {after}")

    verb = "updated" if args.apply else "would update"
    print(f"{len(moves)} file(s), {verb} links in {len(edits)} note(s)" + ("" if args.apply else "  (dry run; add --apply)"))
    return 0


def cmd_rm(args) -> int:
    root = os.path.abspath(args.vault)
    index = Index.scan(root)
    targets = []
    for p in args.paths:
        hit = index.lookup(p)
        if hit is None:
            sys.exit(f"Not found: {p}")
        targets.append(hit)
    doomed = set(targets)

    inbound = defaultdict(set)
    for rel, text in linking_notes(root, index, targets):
        if rel in doomed:
            continue
        spans = code_spans(text)
        for m in WIKILINK_RE.finditer(text):
            if not in_code(m.start(), spans):
                hit = index.resolve_wiki(m.group(2).split("|")[0].rstrip("\\").split("#")[0], rel)
                if hit in doomed:
                    inbound[hit].add(rel)
        for m in MDLINK_RE.finditer(text):
            href = m.group(2)[1:-1] if m.group(2).startswith("<") else m.group(2)
            hit = index.resolve_md(href, rel)
            if not in_code(m.start(), spans) and hit and hit[0] in doomed:
                inbound[hit[0]].add(rel)

    for t in targets:
        refs = sorted(inbound.get(t, ()))
        print(f"{t}: {len(refs)} inbound" + "".join(f"\n    <- {r}" for r in refs[: args.show]))
    if inbound and not args.force:
        print("refusing: still linked (fix links or pass --force)")
        return 1
    if args.apply:
        subprocess.run(["trash", *[os.path.join(root, t) for t in targets]], check=True)
        print(f"trashed {len(targets)} file(s)")
    else:
        print(f"would trash {len(targets)} file(s)  (dry run; add --apply)")
    return 0


def main(argv=None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault", default=DEFAULT_VAULT, help="vault root")
    common.add_argument("--apply", action="store_true", help="actually change files (default: dry run)")
    common.add_argument("--show", type=int, default=5, help="max link examples per note")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    mv = sub.add_parser("mv", parents=[common], help="move/rename and update links")
    mv.add_argument("src", nargs="?")
    mv.add_argument("dst", nargs="?")
    mv.add_argument("--batch", help="TSV of source<TAB>dest")
    rm = sub.add_parser("rm", parents=[common], help="trash files that nothing links to")
    rm.add_argument("paths", nargs="+")
    rm.add_argument("--force", action="store_true", help="trash even if still linked")
    args = parser.parse_args(argv)
    return cmd_mv(args) if args.cmd == "mv" else cmd_rm(args)


if __name__ == "__main__":
    sys.exit(main())
