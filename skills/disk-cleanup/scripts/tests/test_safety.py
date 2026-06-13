#!/usr/bin/env python3
"""Safety-core tests for disk-cleanup. Stdlib unittest only (no deps).

Run:  python3 scripts/tests/test_safety.py
"""

import os
import sys
import time
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lib  # noqa: E402


class Preflight(unittest.TestCase):
    def test_refuses_outside_allowed_roots(self):
        with tempfile.TemporaryDirectory() as d:
            ok, _ = lib.preflight(Path(d), ["~/Library"])  # tmp is not under ~/Library
            self.assertFalse(ok)

    def test_allows_dir_under_allowed_root(self):
        with tempfile.TemporaryDirectory() as d:
            sub = Path(d) / "cache"
            sub.mkdir()
            ok, reason = lib.preflight(sub, [d])
            self.assertTrue(ok, reason)

    def test_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "real"
            target.mkdir()
            link = Path(d) / "link"
            link.symlink_to(target)
            ok, _ = lib.preflight(link, [d])
            self.assertFalse(ok)

    def test_refuses_home_even_if_allowed(self):
        ok, reason = lib.preflight(Path("~"), ["~"])
        self.assertFalse(ok)
        self.assertIn("HOME", reason)


class DownloadsScan(unittest.TestCase):
    def test_excludes_sensitive_and_keeps_old_junk(self):
        with tempfile.TemporaryDirectory() as d:
            keep_out = Path(d) / "tax_return_2020.pdf"   # matches exclude → must NOT be returned
            sweep = Path(d) / "old_installer.dmg"        # no match, old → must be returned
            for f in (keep_out, sweep):
                f.write_text("x")
            old = time.time() - 400 * 86400
            for f in (keep_out, sweep):
                os.utime(f, (old, old))
            res = {p.name for p in lib.scan_downloads(
                {"root": d, "age_days": 180, "min_mb": 0, "exclude_patterns": ["tax"]})}
            self.assertIn("old_installer.dmg", res)
            self.assertNotIn("tax_return_2020.pdf", res)

    def test_skips_recent_files(self):
        with tempfile.TemporaryDirectory() as d:
            recent = Path(d) / "fresh.zip"
            recent.write_text("x")  # mtime = now
            res = lib.scan_downloads(
                {"root": d, "age_days": 180, "min_mb": 0, "exclude_patterns": []})
            self.assertEqual(res, [])


class GlobResolution(unittest.TestCase):
    def test_midpath_wildcard_resolves(self):
        # regression: parent.glob(name) missed mid-path '*'; glob.glob must find it.
        with tempfile.TemporaryDirectory() as d:
            deep = Path(d) / "aa" / "bb" / "C"
            deep.mkdir(parents=True)
            (deep / "clang").mkdir()
            target = {"method": "trash", "paths": [str(Path(d) / "*" / "*" / "C" / "clang")]}
            res = lib.resolve_target_paths(target)
            self.assertEqual([p.name for p in res], ["clang"])

    def test_nested_overlap_dropped(self):
        with tempfile.TemporaryDirectory() as d:
            outer = Path(d) / "node_modules"
            inner = outer / "pkg" / "node_modules"
            inner.mkdir(parents=True)
            target = {"method": "trash", "paths": [str(outer), str(inner)]}
            res = [str(p) for p in lib.resolve_target_paths(target)]
            self.assertEqual(res, [str(outer)])  # inner absorbed by its parent


if __name__ == "__main__":
    unittest.main(verbosity=2)
