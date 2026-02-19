"""Tests for discover_docs.sh — project documentation discovery."""

import subprocess

import pytest


def run_discover(scripts_dir, project_dir, lang=None):
    cmd = ["bash", str(scripts_dir / "discover_docs.sh"), str(project_dir)]
    if lang:
        cmd += ["--lang", lang]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result


class TestDocumentationFiles:
    def test_finds_readme(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project)
        assert result.returncode == 0
        assert "README.md" in result.stdout
        assert "Calculator Project" in result.stdout

    def test_finds_docs_folder(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project)
        assert "API.md" in result.stdout
        assert "Calculator" in result.stdout

    def test_ts_readme(self, scripts_dir, ts_project):
        result = run_discover(scripts_dir, ts_project)
        assert "TypeScript Calculator" in result.stdout


class TestAPISpecifications:
    def test_finds_openapi_yaml(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project)
        assert "openapi" in result.stdout.lower()
        assert "/calculate" in result.stdout

    def test_no_specs_in_ts_project(self, scripts_dir, ts_project):
        result = run_discover(scripts_dir, ts_project)
        assert "No API specification files found" in result.stdout


class TestPythonDocstrings:
    def test_extracts_class_docstrings(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project, lang="python")
        assert "Calculator" in result.stdout
        assert "arithmetic" in result.stdout.lower()

    def test_extracts_function_docstrings(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project, lang="python")
        assert "factorial" in result.stdout

    def test_excludes_private_docstrings(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project, lang="python")
        assert "_internal_helper" not in result.stdout

    def test_extracts_model_docstrings(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project, lang="python")
        assert "User" in result.stdout


class TestTypeScriptDocstrings:
    def test_extracts_jsdoc(self, scripts_dir, ts_project):
        result = run_discover(scripts_dir, ts_project, lang="typescript")
        assert "Source Docstrings" in result.stdout
        # JSDoc for exported functions
        assert "add" in result.stdout.lower() or "calculator" in result.stdout.lower()


class TestGoDocstrings:
    def test_extracts_doc_comments(self, scripts_dir, go_project):
        result = run_discover(scripts_dir, go_project, lang="go")
        assert "Source Docstrings" in result.stdout


class TestEmptyProject:
    def test_handles_empty_gracefully(self, scripts_dir, empty_project):
        result = run_discover(scripts_dir, empty_project)
        assert result.returncode == 0
        assert "No documentation files found" in result.stdout
        assert "No API specification files found" in result.stdout


class TestOutputStructure:
    def test_has_three_sections(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project)
        assert "# Project Documentation" in result.stdout
        assert "# API Specifications" in result.stdout
        assert "# Source Docstrings" in result.stdout

    def test_output_not_empty(self, scripts_dir, python_project):
        result = run_discover(scripts_dir, python_project)
        assert len(result.stdout) > 100


class TestTruncation:
    def test_respects_char_limit(self, scripts_dir, tmp_project):
        """Create a project with very large docs to test truncation."""
        readme = tmp_project / "README.md"
        readme.write_text("# Big Doc\n" + ("x" * 200 + "\n") * 100)
        result = run_discover(scripts_dir, tmp_project, lang="python")
        assert len(result.stdout) <= 16000  # 15k + some overhead
