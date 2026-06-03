"""Unit tests for the release engine. Stdlib unittest, no external deps.

Run: python3 -m unittest test_release -v
"""
import json
import tempfile
import unittest
from pathlib import Path

from release import (
    Version,
    parse_version,
    bump,
    read_version_file,
    write_version_file,
    draft_changelog,
    required_bump,
    enforce_bump,
    load_config,
    build_plan,
    ReleaseError,
)


class TestVersion(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_version("1.2.3"), Version(1, 2, 3))

    def test_parse_rejects_junk(self):
        with self.assertRaises(ReleaseError):
            parse_version("1.2")

    def test_bump_patch(self):
        self.assertEqual(str(bump(Version(0, 1, 0), "patch")), "0.1.1")

    def test_bump_minor_resets_patch(self):
        self.assertEqual(str(bump(Version(0, 1, 4), "minor")), "0.2.0")

    def test_bump_major_resets(self):
        self.assertEqual(str(bump(Version(0, 9, 3), "major")), "1.0.0")

    def test_bump_rejects_bad_kind(self):
        with self.assertRaises(ReleaseError):
            bump(Version(0, 1, 0), "huge")


class TestVersionFiles(unittest.TestCase):
    def _tmp(self, name, content):
        d = tempfile.mkdtemp()
        p = Path(d) / name
        p.write_text(content)
        return p

    def test_json_pointer(self):
        p = self._tmp("package.json", '{\n  "name": "x",\n  "version": "0.1.0"\n}\n')
        self.assertEqual(read_version_file(p, "json", pointer="/version"), "0.1.0")
        write_version_file(p, "json", "0.2.0", pointer="/version")
        self.assertEqual(json.loads(p.read_text())["version"], "0.2.0")
        # name preserved
        self.assertEqual(json.loads(p.read_text())["name"], "x")

    def test_toml_key(self):
        p = self._tmp("Cargo.toml", '[package]\nname = "x"\nversion = "0.1.0"\n\n[deps]\nversion = "9.9.9"\n')
        self.assertEqual(read_version_file(p, "toml", key="package.version"), "0.1.0")
        write_version_file(p, "toml", "0.2.0", key="package.version")
        self.assertIn('version = "0.2.0"', p.read_text())
        # the unrelated [deps] version must NOT change
        self.assertIn('[deps]\nversion = "9.9.9"', p.read_text())

    def test_missing_field_errors(self):
        p = self._tmp("package.json", '{"name":"x"}')
        with self.assertRaises(Exception):
            read_version_file(p, "json", pointer="/version")


class TestChangelog(unittest.TestCase):
    def test_buckets_by_type(self):
        commits = [
            "feat(mcp): add tag scopes",
            "fix: stop key leak",
            "perf(db): sql folders",
            "chore: bump dep",
            "docs: tweak",
        ]
        md = draft_changelog("0.2.0", "2026-06-03", commits)
        self.assertIn("## [0.2.0] - 2026-06-03", md)
        self.assertIn("### Added", md)
        self.assertIn("add tag scopes", md)
        self.assertIn("### Fixed", md)
        self.assertIn("stop key leak", md)
        self.assertIn("### Changed", md)
        # chores/docs excluded
        self.assertNotIn("bump dep", md)
        self.assertNotIn("tweak", md)

    def test_breaking_bang_goes_to_changed(self):
        md = draft_changelog("1.0.0", "2026-06-03", ["feat!: drop old api"])
        self.assertIn("### Changed", md)
        self.assertIn("drop old api", md)

    def test_empty_when_only_chores(self):
        md = draft_changelog("0.1.1", "2026-06-03", ["chore: x", "ci: y"])
        self.assertIn("## [0.1.1] - 2026-06-03", md)
        self.assertNotIn("###", md)


class TestSurfaceGate(unittest.TestCase):
    def test_breaking_stable_forces_major(self):
        self.assertEqual(
            required_bump([{"id": "db", "tier": "stable", "breaking": True}]), "major"
        )

    def test_breaking_preview_is_minor(self):
        self.assertEqual(
            required_bump([{"id": "mcp", "tier": "preview", "breaking": True}]), "minor"
        )

    def test_additive_is_minor(self):
        self.assertEqual(
            required_bump([{"id": "db", "tier": "stable", "breaking": False}]), "minor"
        )

    def test_nothing_is_patch(self):
        self.assertEqual(required_bump([]), "patch")

    def test_enforce_rejects_too_small(self):
        with self.assertRaises(ReleaseError):
            enforce_bump(requested="patch", required="major")

    def test_enforce_allows_equal_or_larger(self):
        enforce_bump(requested="major", required="minor")  # no raise
        enforce_bump(requested="minor", required="minor")  # no raise


class TestConfig(unittest.TestCase):
    def _cfg(self, obj):
        d = tempfile.mkdtemp()
        p = Path(d) / "release.config.json"
        p.write_text(json.dumps(obj))
        return p

    def test_loads_and_validates(self):
        p = self._cfg({
            "versionFiles": [{"path": "package.json", "kind": "json", "pointer": "/version"}],
            "gate": "true",
            "compatibility": {"path": "docs/COMPATIBILITY.md"},
            "surfaces": [{"id": "db", "name": "DB", "tier": "stable", "mode": "BACKWARD_TRANSITIVE"}],
            "tag": {"prefix": "v", "push": True},
        })
        cfg = load_config(p)
        self.assertEqual(cfg["gate"], "true")
        self.assertEqual(cfg["surfaces"][0]["tier"], "stable")

    def test_rejects_bad_tier(self):
        p = self._cfg({
            "versionFiles": [{"path": "p", "kind": "json", "pointer": "/version"}],
            "gate": "true",
            "compatibility": {"path": "x"},
            "surfaces": [{"id": "db", "name": "DB", "tier": "GA", "mode": "x"}],
            "tag": {"prefix": "v"},
        })
        with self.assertRaises(ReleaseError):
            load_config(p)

    def test_rejects_missing_key(self):
        p = self._cfg({"gate": "true"})
        with self.assertRaises(ReleaseError):
            load_config(p)


class TestPlan(unittest.TestCase):
    def test_build_plan(self):
        cfg = {
            "versionFiles": [{"path": "package.json", "kind": "json", "pointer": "/version"}],
            "tag": {"prefix": "v"},
        }
        plan = build_plan(cfg, current="0.1.0", kind="minor")
        self.assertEqual(plan["new_version"], "0.2.0")
        self.assertEqual(plan["tag"], "v0.2.0")
        self.assertIn("package.json", plan["files"])


if __name__ == "__main__":
    unittest.main()
