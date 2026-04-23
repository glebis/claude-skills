"""Tests for mine_reviews.py — review clustering on pain/outcome/workaround axes."""
import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import mine_reviews  # noqa: E402


class ParseInputTests(unittest.TestCase):
    """CSV and JSON parsing."""

    def test_csv_basic(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=["text", "rating", "source"])
            writer.writeheader()
            writer.writerow({"text": "Too slow", "rating": "2", "source": "G2"})
            writer.writerow({"text": "Great tool", "rating": "5", "source": "G2"})
            path = f.name
        try:
            rows = mine_reviews.parse_input(path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["text"], "Too slow")
            self.assertEqual(rows[1]["rating"], "5")
        finally:
            os.unlink(path)

    def test_json_basic(self):
        data = [
            {"text": "Takes forever to load", "rating": 1},
            {"text": "Love the simplicity", "rating": 5},
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            path = f.name
        try:
            rows = mine_reviews.parse_input(path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["text"], "Takes forever to load")
        finally:
            os.unlink(path)

    def test_csv_missing_text_column_raises(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=["review", "rating"])
            writer.writeheader()
            writer.writerow({"review": "hello", "rating": "3"})
            path = f.name
        try:
            with self.assertRaises(ValueError):
                mine_reviews.parse_input(path)
        finally:
            os.unlink(path)

    def test_json_missing_text_field_raises(self):
        data = [{"body": "no text field"}]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            path = f.name
        try:
            with self.assertRaises(ValueError):
                mine_reviews.parse_input(path)
        finally:
            os.unlink(path)

    def test_json_not_array_raises(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({"text": "single object"}, f)
            path = f.name
        try:
            with self.assertRaises(ValueError):
                mine_reviews.parse_input(path)
        finally:
            os.unlink(path)


class ClassifyPainTests(unittest.TestCase):
    """Pain axis classification."""

    def test_time_cost(self):
        result = mine_reviews.classify_review("This takes forever to process")
        self.assertEqual(result["pain"], "time_cost")

    def test_time_cost_slow(self):
        result = mine_reviews.classify_review("The app is incredibly slow")
        self.assertEqual(result["pain"], "time_cost")

    def test_quality_cost(self):
        result = mine_reviews.classify_review("Results are always wrong and unreliable")
        self.assertEqual(result["pain"], "quality_cost")

    def test_social_cost(self):
        result = mine_reviews.classify_review("It was embarrassing in front of my boss")
        self.assertEqual(result["pain"], "social_cost")

    def test_cognitive_cost(self):
        result = mine_reviews.classify_review("So confusing, I can't figure out anything")
        self.assertEqual(result["pain"], "cognitive_cost")

    def test_money_cost(self):
        result = mine_reviews.classify_review("Way too expensive, not worth the price")
        self.assertEqual(result["pain"], "money_cost")

    def test_trust_cost(self):
        result = mine_reviews.classify_review("It crashed and I lost my data")
        self.assertEqual(result["pain"], "trust_cost")

    def test_no_pain_detected(self):
        result = mine_reviews.classify_review("It exists.")
        self.assertIsNone(result["pain"])


class ClassifyOutcomeTests(unittest.TestCase):
    """Outcome axis classification."""

    def test_speed(self):
        result = mine_reviews.classify_review("I need something faster")
        self.assertEqual(result["outcome"], "speed")

    def test_accuracy(self):
        result = mine_reviews.classify_review("I need accurate and reliable results")
        self.assertEqual(result["outcome"], "accuracy")

    def test_control(self):
        result = mine_reviews.classify_review("I want more control and customizable options")
        self.assertEqual(result["outcome"], "control")

    def test_simplicity(self):
        result = mine_reviews.classify_review("Should be easier and more intuitive")
        self.assertEqual(result["outcome"], "simplicity")

    def test_trust_outcome(self):
        result = mine_reviews.classify_review("I need something stable and predictable")
        self.assertEqual(result["outcome"], "trust")

    def test_status(self):
        result = mine_reviews.classify_review("I need a more professional looking tool")
        self.assertEqual(result["outcome"], "status")


class ClassifyWorkaroundTests(unittest.TestCase):
    """Workaround axis classification."""

    def test_manual(self):
        result = mine_reviews.classify_review("I do it manually in a spreadsheet")
        self.assertEqual(result["workaround"], "manual")

    def test_abandoned(self):
        result = mine_reviews.classify_review("I just gave up trying")
        self.assertEqual(result["workaround"], "abandoned")

    def test_competitor(self):
        result = mine_reviews.classify_review("I switched to Notion instead")
        self.assertEqual(result["workaround"], "competitor")
        self.assertEqual(result["competitor"], "notion")

    def test_hybrid(self):
        result = mine_reviews.classify_review(
            "I use it alongside another tool to work around the gaps"
        )
        self.assertEqual(result["workaround"], "hybrid")

    def test_unknown_default(self):
        result = mine_reviews.classify_review("The color is blue.")
        self.assertEqual(result["workaround"], "unknown")


class ConvergenceThresholdTests(unittest.TestCase):
    """Clusters with <3 reviews get confidence: low."""

    def _make_reviews(self, texts):
        return [{"text": t} for t in texts]

    def test_cluster_below_threshold_is_low(self):
        reviews = self._make_reviews([
            "Too slow, takes forever",
            "Very slow app",
        ])
        clusters, _ = mine_reviews.cluster_reviews(reviews)
        # Both should land in time_cost cluster with <3 reviews.
        time_clusters = [c for c in clusters if c["pain"] == "time_cost"]
        self.assertTrue(len(time_clusters) > 0)
        self.assertEqual(time_clusters[0]["confidence"], "low")

    def test_cluster_at_threshold_is_not_low(self):
        reviews = self._make_reviews([
            "Too slow, takes forever",
            "Very slow app, wastes my time",
            "So slow, I waste all day waiting",
        ])
        clusters, _ = mine_reviews.cluster_reviews(reviews)
        time_clusters = [c for c in clusters if c["pain"] == "time_cost"]
        self.assertTrue(len(time_clusters) > 0)
        # 3 reviews, no source info -> medium.
        self.assertIn(time_clusters[0]["confidence"], ("medium", "high"))

    def test_cross_source_boosts_to_high(self):
        reviews = [
            {"text": "Too slow", "source": "G2"},
            {"text": "Very slow", "source": "App Store"},
            {"text": "Wasting my time", "source": "Google Maps"},
        ]
        clusters, _ = mine_reviews.cluster_reviews(reviews)
        time_clusters = [c for c in clusters if c["pain"] == "time_cost"]
        self.assertTrue(len(time_clusters) > 0)
        self.assertEqual(time_clusters[0]["confidence"], "high")


class GenericFilterTests(unittest.TestCase):
    """Unique-to-business filter flags generic praise."""

    def test_generic_praise_flagged(self):
        result = mine_reviews.classify_review("Great customer service, highly recommend!")
        self.assertTrue(result["generic"])

    def test_specific_review_not_flagged(self):
        result = mine_reviews.classify_review(
            "The Kanban board crashes when I drag cards between columns"
        )
        self.assertFalse(result["generic"])


class EmptyInputTests(unittest.TestCase):
    """Edge cases: empty and minimal inputs."""

    def test_empty_review_list(self):
        clusters, classified = mine_reviews.cluster_reviews([])
        self.assertEqual(len(clusters), 0)
        self.assertEqual(len(classified), 0)

    def test_single_review(self):
        reviews = [{"text": "App is slow"}]
        clusters, classified = mine_reviews.cluster_reviews(reviews)
        self.assertEqual(len(classified), 1)
        # Single review cluster should be low confidence.
        for c in clusters:
            self.assertEqual(c["confidence"], "low")

    def test_reviews_with_empty_text(self):
        reviews = [{"text": ""}, {"text": ""}]
        clusters, classified = mine_reviews.cluster_reviews(reviews)
        self.assertEqual(len(classified), 2)


class RenderBriefTests(unittest.TestCase):
    """Brief generation writes a valid file."""

    def test_brief_file_created(self):
        reviews = [{"text": f"Too slow number {i}"} for i in range(5)]
        clusters, _ = mine_reviews.cluster_reviews(reviews)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = mine_reviews.render_brief(clusters, 5, "test-source", tmpdir)
            self.assertTrue(os.path.exists(path))
            content = Path(path).read_text()
            self.assertIn("Review Brief", content)
            self.assertIn("test-source", content)
            self.assertIn("Reviews parsed:** 5", content)


class CLITests(unittest.TestCase):
    """End-to-end CLI invocation."""

    def test_main_with_csv(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=["text", "rating"])
            writer.writeheader()
            for i in range(5):
                writer.writerow({"text": f"This is way too slow {i}", "rating": "2"})
            path = f.name
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                summary = mine_reviews.main([path, "-o", tmpdir])
                self.assertEqual(summary["total_reviews"], 5)
                self.assertIn("clusters", summary)
                self.assertTrue(os.path.exists(summary["brief_path"]))
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
