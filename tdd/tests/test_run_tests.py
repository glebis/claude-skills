"""Tests for run_tests.sh — universal test runner JSON output."""

import json
import shutil
import subprocess

import pytest


def run_tests_sh(scripts_dir, framework, test_cmd, extra_args=None):
    cmd = ["bash", str(scripts_dir / "run_tests.sh"), framework, test_cmd]
    if extra_args:
        cmd += extra_args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result


def parse_output(result):
    """Parse the JSON from run_tests.sh stdout."""
    stdout = result.stdout.strip()
    assert stdout, f"Empty stdout. stderr={result.stderr}"
    return json.loads(stdout)


HAS_TIMEOUT = shutil.which("timeout") or shutil.which("gtimeout")


class TestPytestParsing:
    def test_passing_tests(self, scripts_dir):
        cmd = (
            "echo '============================= test session starts =============================='; "
            "echo 'collected 3 items'; "
            "echo ''; "
            "echo 'tests/test_calc.py ...                                                    [100%]'; "
            "echo ''; "
            "echo '============================== 3 passed in 0.02s ==============================='; "
            "exit 0"
        )
        result = run_tests_sh(scripts_dir, "pytest", cmd)
        data = parse_output(result)
        assert data["status"] == "pass"
        assert data["passed"] == 3
        assert data["failed"] == 0
        assert data["total"] == 3

    def test_failing_tests(self, scripts_dir):
        cmd = (
            "echo '============================= test session starts =============================='; "
            "echo 'collected 2 items'; "
            "echo ''; "
            "echo 'FAILED tests/test_calc.py::test_add - assert 4 == 5'; "
            "echo ''; "
            "echo '=========================== 1 failed, 1 passed in 0.03s ========================'; "
            "exit 1"
        )
        result = run_tests_sh(scripts_dir, "pytest", cmd)
        data = parse_output(result)
        assert data["status"] == "fail"
        assert data["passed"] == 1
        assert data["failed"] == 1
        assert len(data["failures"]) >= 1

    def test_error_no_tests(self, scripts_dir):
        cmd = "echo 'ERROR: not found'; exit 1"
        result = run_tests_sh(scripts_dir, "pytest", cmd)
        data = parse_output(result)
        assert data["status"] == "error"
        assert data["total"] == 0


class TestJestParsing:
    def test_passing_tests(self, scripts_dir):
        cmd = (
            "echo 'PASS src/sum.test.ts'; "
            "echo '  sum'; "
            "echo '    ✓ adds 1 + 2 to equal 3 (2 ms)'; "
            "echo ''; "
            "echo 'Tests:        2 passed, 2 total'; "
            "echo 'Time:         0.5 s'; "
            "exit 0"
        )
        result = run_tests_sh(scripts_dir, "jest", cmd)
        data = parse_output(result)
        assert data["status"] == "pass"
        assert data["passed"] == 2
        assert data["total"] == 2

    def test_failing_tests(self, scripts_dir):
        cmd = (
            "echo 'FAIL src/sum.test.ts'; "
            "echo '  ● sum › adds 1 + 2 to equal 3'; "
            "echo ''; "
            "echo '    expect(received).toBe(expected)'; "
            "echo ''; "
            "echo '    Expected: 3'; "
            "echo '    Received: 4'; "
            "echo ''; "
            "echo 'Tests:        1 failed, 1 passed, 2 total'; "
            "echo 'Time:         0.8 s'; "
            "exit 1"
        )
        result = run_tests_sh(scripts_dir, "jest", cmd)
        data = parse_output(result)
        assert data["status"] == "fail"
        assert data["failed"] == 1
        assert data["total"] == 2


class TestGoParsing:
    def test_passing_tests(self, scripts_dir):
        cmd = (
            "echo '--- PASS: TestAdd (0.00s)'; "
            "echo '--- PASS: TestSubtract (0.00s)'; "
            "echo 'PASS'; "
            "echo 'ok      calculator    0.003s'; "
            "exit 0"
        )
        result = run_tests_sh(scripts_dir, "go", cmd)
        data = parse_output(result)
        assert data["status"] == "pass"
        assert data["passed"] == 2
        assert data["total"] == 2

    def test_failing_tests(self, scripts_dir):
        cmd = (
            "echo '--- FAIL: TestDivide (0.00s)'; "
            "echo '    calculator_test.go:15: expected 5, got 0'; "
            "echo '--- PASS: TestAdd (0.00s)'; "
            "echo 'FAIL'; "
            "exit 1"
        )
        result = run_tests_sh(scripts_dir, "go", cmd)
        data = parse_output(result)
        assert data["status"] == "fail"
        assert data["failed"] == 1
        assert data["passed"] == 1


class TestJSONStructure:
    def test_always_returns_valid_json(self, scripts_dir):
        """Even on weird output, should produce valid JSON."""
        cmd = "echo 'garbage output'; exit 1"
        result = run_tests_sh(scripts_dir, "pytest", cmd)
        data = parse_output(result)
        assert "status" in data
        assert "total" in data
        assert "passed" in data
        assert "failed" in data
        assert "failures" in data
        assert "raw_tail" in data

    def test_raw_tail_captures_output(self, scripts_dir):
        cmd = "echo 'line1'; echo 'line2'; echo 'line3'; exit 0"
        result = run_tests_sh(scripts_dir, "pytest", cmd)
        data = parse_output(result)
        assert "line1" in data["raw_tail"]
        assert "line3" in data["raw_tail"]

    def test_json_escapes_special_chars(self, scripts_dir):
        """Ensure quotes and newlines in output don't break JSON."""
        cmd = """echo 'he said "hello"'; echo "line with 'quotes'"; exit 0"""
        result = run_tests_sh(scripts_dir, "pytest", cmd)
        data = parse_output(result)
        assert isinstance(data["raw_tail"], str)

    def test_all_fields_have_correct_types(self, scripts_dir):
        cmd = "echo 'some output'; exit 0"
        result = run_tests_sh(scripts_dir, "pytest", cmd)
        data = parse_output(result)
        assert isinstance(data["status"], str)
        assert isinstance(data["total"], int)
        assert isinstance(data["passed"], int)
        assert isinstance(data["failed"], int)
        assert isinstance(data["failures"], list)
        assert isinstance(data["raw_tail"], str)


class TestTimeout:
    @pytest.mark.skipif(not HAS_TIMEOUT, reason="timeout/gtimeout not installed")
    def test_timeout_produces_json(self, scripts_dir):
        result = run_tests_sh(
            scripts_dir, "pytest", "sleep 10", ["--timeout", "1"]
        )
        data = parse_output(result)
        assert data["status"] == "error"
        assert "timeout" in data["raw_tail"].lower() or "TIMEOUT" in str(
            data["failures"]
        )


class TestGenericFramework:
    def test_unknown_framework_returns_json(self, scripts_dir):
        cmd = "echo 'some output'; exit 0"
        result = run_tests_sh(scripts_dir, "unknown_framework", cmd)
        data = parse_output(result)
        assert data["status"] == "pass"

    def test_unknown_framework_failure(self, scripts_dir):
        cmd = "echo 'error'; exit 1"
        result = run_tests_sh(scripts_dir, "unknown_framework", cmd)
        data = parse_output(result)
        assert data["status"] == "fail"
