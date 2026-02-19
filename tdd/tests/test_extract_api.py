"""Tests for extract_api.sh — public API signature extraction.

Note: Python/TS fixtures are copied to tmp_path to avoid extract_api.sh's
`-not -path '*/tests/*'` exclusion (fixtures live under tests/).
"""

import shutil
import subprocess

import pytest

from conftest import FIXTURES_DIR


def run_extract(scripts_dir, source_dir, lang=None):
    cmd = ["bash", str(scripts_dir / "extract_api.sh"), str(source_dir)]
    if lang:
        cmd += ["--lang", lang]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result


@pytest.fixture
def py_src(tmp_path):
    """Copy Python fixture to tmp_path so it's not under tests/."""
    src = tmp_path / "src"
    shutil.copytree(FIXTURES_DIR / "python_project" / "src", src)
    return src


@pytest.fixture
def ts_src(tmp_path):
    src = tmp_path / "src"
    shutil.copytree(FIXTURES_DIR / "ts_project" / "src", src)
    return src


@pytest.fixture
def go_src(tmp_path):
    dst = tmp_path / "go_project"
    shutil.copytree(FIXTURES_DIR / "go_project", dst)
    return dst


class TestPythonExtraction:
    def test_extracts_class_signatures(self, scripts_dir, py_src):
        result = run_extract(scripts_dir, py_src)
        assert result.returncode == 0
        assert "class Calculator" in result.stdout

    def test_extracts_function_signatures(self, scripts_dir, py_src):
        result = run_extract(scripts_dir, py_src)
        # extract_api.sh matches top-level definitions only (^def)
        # methods inside classes are indented and won't match
        assert "def factorial" in result.stdout

    def test_extracts_dataclass_decorator(self, scripts_dir, py_src):
        result = run_extract(scripts_dir, py_src)
        assert "@dataclass" in result.stdout

    def test_excludes_private_functions(self, scripts_dir, py_src):
        result = run_extract(scripts_dir, py_src)
        assert "_internal_helper" not in result.stdout

    def test_shows_file_paths(self, scripts_dir, py_src):
        result = run_extract(scripts_dir, py_src)
        assert "calculator.py" in result.stdout
        assert "models.py" in result.stdout

    def test_header_present(self, scripts_dir, py_src):
        result = run_extract(scripts_dir, py_src)
        assert "Python API Surface" in result.stdout


class TestTypeScriptExtraction:
    def test_extracts_exports(self, scripts_dir, ts_src):
        result = run_extract(scripts_dir, ts_src)
        assert result.returncode == 0
        assert "export function add" in result.stdout
        assert "export function divide" in result.stdout

    def test_extracts_class_exports(self, scripts_dir, ts_src):
        result = run_extract(scripts_dir, ts_src)
        assert "export class Calculator" in result.stdout

    def test_extracts_type_exports(self, scripts_dir, ts_src):
        result = run_extract(scripts_dir, ts_src)
        assert "export type Operation" in result.stdout
        assert "export interface CalculatorConfig" in result.stdout

    def test_header_present(self, scripts_dir, ts_src):
        result = run_extract(scripts_dir, ts_src)
        assert "TypeScript" in result.stdout


class TestGoExtraction:
    def test_extracts_exported_functions(self, scripts_dir, go_src):
        result = run_extract(scripts_dir, go_src)
        assert result.returncode == 0
        assert "func Add" in result.stdout
        assert "func Divide" in result.stdout

    def test_extracts_exported_types(self, scripts_dir, go_src):
        result = run_extract(scripts_dir, go_src)
        assert "type Calculator" in result.stdout

    def test_excludes_unexported(self, scripts_dir, go_src):
        result = run_extract(scripts_dir, go_src)
        assert "internal" not in result.stdout

    def test_header_present(self, scripts_dir, go_src):
        result = run_extract(scripts_dir, go_src)
        assert "Go API Surface" in result.stdout


class TestLanguageDetection:
    def test_auto_detects_python(self, scripts_dir, py_src):
        result = run_extract(scripts_dir, py_src)
        assert "Python" in result.stdout

    def test_auto_detects_typescript(self, scripts_dir, ts_src):
        result = run_extract(scripts_dir, ts_src)
        assert "TypeScript" in result.stdout

    def test_lang_override(self, scripts_dir, py_src):
        result = run_extract(scripts_dir, py_src, lang="go")
        assert "Go API Surface" in result.stdout


class TestEmptyProject:
    def test_empty_returns_successfully(self, scripts_dir, empty_project):
        result = run_extract(scripts_dir, empty_project)
        assert result.returncode in (0, 1)

    def test_empty_no_crash(self, scripts_dir, empty_project):
        result = run_extract(scripts_dir, empty_project, lang="python")
        assert result.returncode == 0
        assert "Python API Surface" in result.stdout
