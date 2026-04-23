"""TDD tests for validate_outcome.py — ODI outcome statement validation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate_outcome as vo  # noqa: E402


class ValidateStatementTests(unittest.TestCase):
    def test_good_statement_is_valid(self):
        result = vo.validate_statement("Minimize the time it takes to prepare launch-readiness docs when shipping a new feature")
        self.assertTrue(result["valid"])

    def test_missing_direction_fails(self):
        result = vo.validate_statement("The time it takes to prepare docs when shipping")
        self.assertFalse(result["valid"])

    def test_solution_language_flagged(self):
        result = vo.validate_statement("Minimize the time it takes to click the dashboard button when viewing reports")
        self.assertTrue(any("solution" in i.lower() for i in result["issues"]))

    def test_vague_statement_fails(self):
        result = vo.validate_statement("Better launch prep")
        self.assertFalse(result["valid"])

    def test_missing_context_is_warning_not_failure(self):
        result = vo.validate_statement("Minimize the time it takes to prepare launch docs")
        self.assertTrue(result["valid"])


class ValidateAllTests(unittest.TestCase):
    def test_mixed_outcomes(self):
        outcomes = [
            {"statement": "Minimize the time it takes to verify document completeness when reviewing"},
            {"statement": "Better docs"},
        ]
        result = vo.validate_all(outcomes)
        self.assertFalse(result["all_valid"])
        self.assertEqual(result["valid_count"], 1)


if __name__ == "__main__":
    unittest.main()
