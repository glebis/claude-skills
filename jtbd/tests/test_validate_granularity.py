"""TDD tests for validate_granularity.py — all 5 dimensions."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate_granularity as vg  # noqa: E402


class ScoreActorTests(unittest.TestCase):
    def test_generic_actor_scores_zero(self):
        self.assertEqual(vg.score_actor("users"), 0)

    def test_generic_with_article_scores_zero(self):
        self.assertEqual(vg.score_actor("the users"), 0)

    def test_role_scores_one(self):
        self.assertEqual(vg.score_actor("product managers"), 1)

    def test_specific_actor_scores_two(self):
        self.assertEqual(vg.score_actor("Junior PMs at Series-B SaaS companies preparing launch docs"), 2)

    def test_empty_scores_zero(self):
        self.assertEqual(vg.score_actor(""), 0)


class ScoreContextTests(unittest.TestCase):
    def test_always_scores_zero(self):
        self.assertEqual(vg.score_context("always when they need it"), 0)

    def test_when_with_detail_scores_two(self):
        self.assertEqual(vg.score_context("When a PM at a Series-B SaaS is preparing launch-readiness docs the Sunday before a Monday review"), 2)

    def test_short_context_scores_zero(self):
        self.assertEqual(vg.score_context("needs help"), 0)

    def test_when_short_scores_one(self):
        self.assertEqual(vg.score_context("when preparing a report"), 1)


class ScoreWorkaroundTests(unittest.TestCase):
    def test_nothing_scores_zero(self):
        self.assertEqual(vg.score_workaround("nothing"), 0)

    def test_detailed_workaround_scores_two(self):
        self.assertEqual(vg.score_workaround("They paste the transcript into ChatGPT, then copy tasks manually"), 2)

    def test_medium_workaround_scores_one(self):
        self.assertEqual(vg.score_workaround("They use a spreadsheet to track things roughly"), 1)


class ScoreOutcomeTests(unittest.TestCase):
    def test_better_scores_zero(self):
        self.assertEqual(vg.score_outcome("better"), 0)

    def test_quantified_scores_two(self):
        self.assertEqual(vg.score_outcome("Cut doc prep from 90 minutes to under 15"), 2)

    def test_directional_scores_one(self):
        self.assertEqual(vg.score_outcome("reduce the time spent on weekly reporting"), 1)


class ScoreEvidenceTests(unittest.TestCase):
    def test_empty_scores_zero(self):
        self.assertEqual(vg.score_evidence([]), 0)

    def test_quotes_without_attribution_scores_one(self):
        self.assertEqual(vg.score_evidence(["I hate doing this every week"]), 1)

    def test_attributed_verbatim_scores_two(self):
        self.assertEqual(vg.score_evidence(['"I spend my entire Sunday rebuilding it" — PM at Series-B SaaS']), 2)


class ValidateTests(unittest.TestCase):
    def test_good_example_passes(self):
        import json
        good_path = Path(__file__).resolve().parent.parent / "templates" / "example_good.json"
        with open(good_path) as f:
            data = json.load(f)
        result = vg.validate(data)
        self.assertTrue(result["passes"], f"Good example should pass but blocked by: {result['blocking']}")

    def test_bad_example_fails(self):
        import json
        bad_path = Path(__file__).resolve().parent.parent / "templates" / "example_bad_then_fixed.json"
        with open(bad_path) as f:
            data = json.load(f)
        result = vg.validate(data["bad_version"])
        self.assertFalse(result["passes"])
        self.assertTrue(len(result["blocking"]) > 0)


if __name__ == "__main__":
    unittest.main()
