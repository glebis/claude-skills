"""Shared helpers for disk-cleanup survey/clean. Stdlib only — runs headless, no deps.

Safety model (per design audit): every path that clean.py might trash passes preflight():
  canonical realpath → must resolve under an allowed root → must not be a symlink.
Sizes come from `du -sk` and are APPROXIMATE on APFS (block counts, shared/sparse blocks);
treat them as estimates, never as exact freed-byte guarantees.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent


def load_json(name: str) -> dict:
    return json.loads((SKILL_DIR / name).read_text(encoding="utf-8"))


def expand(p: str) -> Path:
    """Expand ~ and env vars; do NOT resolve symlinks yet (preflight does that)."""
    return Path(os.path.expandvars(os.path.expanduser(p)))


def canonical(p: str | Path) -> Path:
    return Path(os.path.realpath(expand(str(p))))


def human(n: int) -> str:
    f = float(n)
    for unit in ("B", "K", "M", "G", "T"):
        if f < 1024 or unit == "T":
            return f"{f:.0f}{unit}" if unit in ("B", "K") else f"{f:.1f}{unit}"
        f /= 1024
    return f"{f:.1f}T"


def du_bytes(path: Path) -> int:
    """Approximate disk usage in bytes via `du -sk` (KiB → bytes). 0 if missing."""
    if not path.exists():
        return 0
    try:
        out = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            return 0
        return int(out.stdout.split("\t", 1)[0].strip()) * 1024
    except (ValueError, subprocess.SubprocessError):
        return 0


def disk() -> dict:
    total, used, free = shutil.disk_usage("/")
    return {
        "total_bytes": total, "avail_bytes": free,
        "total_gb": round(total / 1e9), "avail_gb": round(free / 1e9, 1),
        "used_pct": round(100 * used / total),
    }


def in_allowed_roots(path: Path, roots: list[str]) -> bool:
    rp = canonical(path)
    for r in roots:
        try:
            rp.relative_to(canonical(r))
            return True
        except ValueError:
            continue
    return False


def preflight(path: Path, roots: list[str]) -> tuple[bool, str]:
    """Prove a path is safe to trash. Returns (ok, reason)."""
    raw = expand(str(path))
    if not raw.exists():
        return False, "does not exist"
    if raw.is_symlink():
        return False, "is a symlink (refused — could point outside the tree)"
    real = canonical(raw)
    home = canonical("~")
    if real == home or real == Path("/"):
        return False, "refuses to trash $HOME or /"
    if not in_allowed_roots(real, roots):
        return False, f"resolves to {real} — outside allowed roots"
    return True, "ok"


def find_dirs(root: str, name: str, maxdepth: int, min_mb: int) -> list[Path]:
    """Deterministic exact-name dir search with a size floor (for crash-dump sweeps)."""
    base = expand(root)
    if not base.exists():
        return []
    hits = []
    base_depth = len(base.parts)
    for dirpath, dirnames, _ in os.walk(base, followlinks=False):
        depth = len(Path(dirpath).parts) - base_depth
        if depth >= maxdepth:
            dirnames[:] = []
        for d in list(dirnames):
            if d == name:  # exact terminal-name match, no substrings
                p = Path(dirpath) / d
                if du_bytes(p) >= min_mb * 1024 * 1024:
                    hits.append(p)
    return sorted(hits, key=lambda x: str(x))


def trash(paths: list[Path]) -> tuple[bool, str]:
    """Trash via the `trash` CLI using argv (handles spaces). Never rm."""
    if not paths:
        return True, "nothing to trash"
    if shutil.which("trash") is None:
        return False, "`trash` CLI not found — install it; refusing to fall back to rm"
    try:
        out = subprocess.run(["trash", *[str(p) for p in paths]], capture_output=True, text=True, timeout=300)
        return out.returncode == 0, (out.stderr or out.stdout).strip()[:200]
    except subprocess.SubprocessError as e:
        return False, str(e)


def empty_trash() -> tuple[bool, str]:
    try:
        out = subprocess.run(
            ["osascript", "-e", 'tell application "Finder" to empty the trash'],
            capture_output=True, text=True, timeout=120)
        return out.returncode == 0, (out.stderr or "").strip()[:200]
    except subprocess.SubprocessError as e:
        return False, str(e)


def scan_downloads(spec: dict) -> list[Path]:
    """Old, non-sensitive Downloads files. Config-driven: age_days + exclude_patterns + min_mb.
    Deterministic candidate list; deletion still goes through preflight + dry-run in clean.py."""
    import re
    import time
    base = expand(spec.get("root", "~/Downloads"))
    if not base.exists():
        return []
    age_days = spec.get("age_days", 180)
    min_b = spec.get("min_mb", 0) * 1024 * 1024
    patt = re.compile("|".join(spec.get("exclude_patterns", [])) or r"(?!x)x", re.I)
    cutoff = time.time() - age_days * 86400
    hits = []
    for child in base.iterdir():
        if child.name.startswith(".") or child.is_symlink():
            continue
        if patt.search(child.name):  # sensitive: genome/legal/financial/personal — never
            continue
        try:
            if child.stat().st_mtime > cutoff:
                continue
        except OSError:
            continue
        if min_b and du_bytes(child) < min_b:
            continue
        hits.append(child)
    return sorted(hits, key=lambda x: str(x))


def resolve_target_paths(target: dict) -> list[Path]:
    """Expand a target's paths/find spec into concrete, deduped, sorted existing paths."""
    out: list[Path] = []
    method = target.get("method")
    if method == "find-trash":
        f = target["find"]
        out = find_dirs(f["root"], f["name"], f.get("maxdepth", 4), f.get("min_mb", 50))
    elif method == "downloads-scan":
        out = scan_downloads(load_json("config.json").get("downloads_scan", {}))
    elif method == "simctl":
        return []  # action, not paths
    else:
        for p in target.get("paths", []):
            ep = expand(p)
            if "*" in p or "?" in p:
                out.extend(sorted(ep.parent.glob(ep.name)))
            elif ep.exists():
                out.append(ep)
    # dedupe by canonical path, drop nested overlaps, deterministic order
    seen: dict[str, Path] = {}
    for p in out:
        seen[str(canonical(p))] = p
    return [seen[k] for k in sorted(seen)]
