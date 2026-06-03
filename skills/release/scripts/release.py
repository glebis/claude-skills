#!/usr/bin/env python3
"""Config-driven release engine (stdlib only).

Pure functions (parse/bump/changelog/surface-gate/config/plan) are unit-tested
in test_release.py. The CLI wraps them with side effects (reading/writing files,
git). See ../SKILL.md for the full /release orchestration and teaching layer.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


class ReleaseError(Exception):
    """User-facing, recoverable error (printed; CLI exits non-zero)."""


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


# --- SemVer ----------------------------------------------------------------

_SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_version(s: str) -> Version:
    m = _SEMVER.match(s.strip())
    if not m:
        raise ReleaseError(f"not a SemVer x.y.z: {s!r}")
    return Version(int(m[1]), int(m[2]), int(m[3]))


def bump(v: Version, kind: str) -> Version:
    if kind == "major":
        return Version(v.major + 1, 0, 0)
    if kind == "minor":
        return Version(v.major, v.minor + 1, 0)
    if kind == "patch":
        return Version(v.major, v.minor, v.patch + 1)
    raise ReleaseError(f"bump kind must be major|minor|patch, got {kind!r}")


# --- version files (JSON pointer / TOML key) -------------------------------

try:  # read-only; present on 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def read_version_file(path, kind: str, *, pointer=None, key=None) -> str:
    text = Path(path).read_text()
    if kind == "json":
        node = json.loads(text)
        for part in [p for p in (pointer or "").split("/") if p]:
            if not isinstance(node, dict) or part not in node:
                raise ReleaseError(f"JSON pointer {pointer} not found in {path}")
            node = node[part]
        return str(node)
    if kind == "toml":
        sect, name = key.split(".", 1)
        if tomllib:
            data = tomllib.loads(text)
            try:
                return str(data[sect][name])
            except KeyError:
                raise ReleaseError(f"no {key} in {path}")
        m = re.search(
            rf'(?ms)^\[{re.escape(sect)}\].*?^{re.escape(name)}\s*=\s*"([^"]+)"', text
        )
        if not m:
            raise ReleaseError(f"no {key} in {path}")
        return m[1]
    raise ReleaseError(f"unknown version-file kind {kind!r}")


def write_version_file(path, kind: str, new: str, *, pointer=None, key=None) -> None:
    # Match on key AND the *current* value, and require exactly one occurrence in
    # the whole file. This refuses to guess (and corrupt) when a same-named key
    # exists elsewhere — it errors loudly instead. Preserves file formatting.
    path = Path(path)
    old = read_version_file(path, kind, pointer=pointer, key=key)
    if old == new:
        return  # idempotent
    text = path.read_text()
    if kind == "json":
        leaf = [p for p in (pointer or "").split("/") if p][-1]
        pat = rf'("{re.escape(leaf)}"\s*:\s*)"{re.escape(old)}"'
        new_text, n = re.subn(pat, rf'\g<1>"{new}"', text)
        if n != 1:
            raise ReleaseError(
                f'expected exactly one "{leaf}": "{old}" in {path}, found {n} '
                f"(ambiguous — refusing to rewrite)"
            )
        path.write_text(new_text)
        return
    if kind == "toml":
        sect, name = key.split(".", 1)
        # `[^\[]*?` refuses to cross into another [section] header, so the match
        # is structurally confined to the target section.
        pat = rf'(?ms)(^\[{re.escape(sect)}\][^\[]*?^{re.escape(name)}\s*=\s*)"{re.escape(old)}"'
        new_text, n = re.subn(pat, rf'\g<1>"{new}"', text, count=1)
        if n != 1:
            raise ReleaseError(f"could not rewrite {key}={old!r} in {path} (found {n})")
        path.write_text(new_text)
        return
    raise ReleaseError(f"unknown version-file kind {kind!r}")


# --- changelog -------------------------------------------------------------

_CC = re.compile(r"^(?P<type>\w+)(?:\([^)]*\))?(?P<bang>!)?:\s*(?P<desc>.+)$")
_BUCKETS = {"feat": "Added", "fix": "Fixed", "perf": "Changed", "refactor": "Changed"}
_SKIP = {"chore", "docs", "test", "ci", "style", "build"}


def draft_changelog(version: str, date: str, commit_subjects) -> str:
    groups: dict[str, list[str]] = {}
    for s in commit_subjects:
        m = _CC.match(s.strip())
        if not m:
            continue
        t = m["type"]
        if t in _SKIP and not m["bang"]:
            continue
        section = "Changed" if m["bang"] else _BUCKETS.get(t, "Changed")
        groups.setdefault(section, []).append(m["desc"].strip())
    out = [f"## [{version}] - {date}", ""]
    for section in ("Added", "Changed", "Fixed"):
        items = groups.get(section)
        if not items:
            continue
        out.append(f"### {section}")
        out += [f"- {i}" for i in items]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# --- surface-tier gate -----------------------------------------------------

_ORDER = {"patch": 0, "minor": 1, "major": 2}


def required_bump(surfaces_changed) -> str:
    req = "patch"
    for s in surfaces_changed:
        if s.get("breaking") and s.get("tier") == "stable":
            return "major"
        # any declared change to a surface is at least a minor
        if _ORDER[req] < _ORDER["minor"]:
            req = "minor"
    return req


def enforce_bump(requested: str, required: str) -> None:
    if _ORDER[requested] < _ORDER[required]:
        raise ReleaseError(
            f"requested '{requested}' but a {required} bump is required "
            f"(a stable surface changed incompatibly). See COMPATIBILITY.md."
        )


# --- config + plan ---------------------------------------------------------

_TIERS = {"experimental", "preview", "stable"}


def load_config(path) -> dict:
    cfg = json.loads(Path(path).read_text())
    for req in ("versionFiles", "gate", "compatibility", "surfaces", "tag"):
        if req not in cfg:
            raise ReleaseError(f"release.config.json missing '{req}'")
    if not cfg["versionFiles"]:
        raise ReleaseError("versionFiles must be non-empty")
    for vf in cfg["versionFiles"]:
        if "path" not in vf or "kind" not in vf:
            raise ReleaseError("each versionFile needs 'path' and 'kind'")
        if vf["kind"] not in ("json", "toml"):
            raise ReleaseError(f"versionFile kind must be json|toml, got {vf['kind']!r}")
        if vf["kind"] == "json" and not vf.get("pointer"):
            raise ReleaseError(f"versionFile {vf['path']!r}: json kind requires 'pointer'")
        if vf["kind"] == "toml" and not vf.get("key"):
            raise ReleaseError(f"versionFile {vf['path']!r}: toml kind requires 'key'")
    for s in cfg["surfaces"]:
        if s.get("tier") not in _TIERS:
            raise ReleaseError(
                f"surface {s.get('id')!r}: tier must be one of {sorted(_TIERS)}"
            )
    return cfg


def build_plan(cfg: dict, current: str, kind: str) -> dict:
    new = str(bump(parse_version(current), kind))
    prefix = cfg.get("tag", {}).get("prefix", "v")
    return {
        "new_version": new,
        "tag": f"{prefix}{new}",
        "files": [vf["path"] for vf in cfg["versionFiles"]],
    }


# --- CLI -------------------------------------------------------------------


def _current_version(cfg: dict) -> str:
    vf = cfg["versionFiles"][0]
    return read_version_file(
        Path(vf["path"]), vf["kind"], pointer=vf.get("pointer"), key=vf.get("key")
    )


def _assert_versions_agree(cfg: dict) -> str:
    seen = {}
    for vf in cfg["versionFiles"]:
        seen[vf["path"]] = read_version_file(
            Path(vf["path"]), vf["kind"], pointer=vf.get("pointer"), key=vf.get("key")
        )
    distinct = set(seen.values())
    if len(distinct) != 1:
        raise ReleaseError(f"version files disagree before bump: {seen}")
    return distinct.pop()


def _cmd_plan(args):
    cfg = load_config(Path(args.config))
    plan = build_plan(cfg, _current_version(cfg), args.kind)
    print(json.dumps(plan, indent=2))


def _cmd_bump(args):
    """Write the new version into every versionFile (no git side effects)."""
    cfg = load_config(Path(args.config))
    cur = _assert_versions_agree(cfg)
    new = str(bump(parse_version(cur), args.kind))
    for vf in cfg["versionFiles"]:
        write_version_file(
            Path(vf["path"]), vf["kind"], new, pointer=vf.get("pointer"), key=vf.get("key")
        )
    print(f"bumped {cur} -> {new} across {len(cfg['versionFiles'])} files")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="release")
    ap.add_argument("--config", default="release.config.json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="show the planned version/tag (no mutation)")
    p.add_argument("kind", choices=["patch", "minor", "major"])
    p.set_defaults(func=_cmd_plan)

    b = sub.add_parser("bump", help="write the new version into the version files")
    b.add_argument("kind", choices=["patch", "minor", "major"])
    b.set_defaults(func=_cmd_bump)

    args = ap.parse_args(argv)
    try:
        args.func(args)
    except ReleaseError as e:
        print(f"error: {e}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
