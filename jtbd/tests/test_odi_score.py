"""TDD tests for odi_score.py — Outcome-Driven Innovation scoring."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import odi_score  # noqa: E402


class ScoreTests(unittest.TestCase):
    def test_underserved_outcome_scores_above_importance(self):
        # Given importance=9 and satisfaction=3, the formula is
        # 9 + max(0, 9-3) = 9 + 6 = 15, rounded to 2 dp.
        self.assertEqual(odi_score.score(9, 3), 15.0)

    def test_tier_prioritize_above_12(self):
        self.assertEqual(odi_score.tier(13.8), "prioritize")


if __name__ == "__main__":
    unittest.main()
