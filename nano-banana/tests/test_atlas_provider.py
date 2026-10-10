import importlib.util
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "nano_banana.py"
SPEC = importlib.util.spec_from_file_location("nano_banana", SCRIPT)
nano_banana = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = nano_banana
SPEC.loader.exec_module(nano_banana)


class FakeResponse:
    def __init__(self, body):
        self.body = body if isinstance(body, bytes) else json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class AtlasProviderTests(unittest.TestCase):
    def test_platform_size_maps_to_supported_aspect_ratio(self):
        self.assertEqual(nano_banana._atlas_aspect_ratio({"width": 1920, "height": 1080}), "16:9")
        self.assertEqual(nano_banana._atlas_aspect_ratio({"width": 1200, "height": 630}), "auto")

    def test_submit_once_poll_and_download(self):
        calls = []

        def urlopen(request, timeout):
            url = request.full_url if hasattr(request, "full_url") else request
            calls.append(url)
            if url.endswith("generateImage"):
                payload = json.loads(request.data)
                self.assertEqual(payload["model"], nano_banana.ATLAS_DEFAULT_MODEL)
                self.assertEqual(payload["aspect_ratio"], "16:9")
                self.assertEqual(request.get_header("User-agent"), "nano-banana/1.0")
                return FakeResponse({"data": {"id": "prediction-1", "status": "created"}})
            if "prediction/prediction-1" in url:
                return FakeResponse(
                    {"data": {"id": "prediction-1", "status": "completed", "outputs": ["https://cdn.example/image.png"]}}
                )
            return FakeResponse(b"image-bytes")

        with mock.patch.object(nano_banana.urllib.request, "urlopen", side_effect=urlopen):
            output = nano_banana._call_atlas(
                "test prompt",
                nano_banana.ATLAS_DEFAULT_MODEL,
                "test-key",
                aspect_ratio="16:9",
            )

        self.assertEqual(output, b"image-bytes")
        self.assertEqual(sum(url.endswith("generateImage") for url in calls), 1)

    def test_billable_post_is_not_retried(self):
        error = urllib.error.HTTPError("url", 503, "unavailable", {}, None)
        error.read = mock.Mock(return_value=b"temporarily unavailable")
        with mock.patch.object(nano_banana.urllib.request, "urlopen", side_effect=error) as mocked:
            with self.assertRaises(nano_banana.TransientAPIError):
                nano_banana._call_atlas("test", nano_banana.ATLAS_DEFAULT_MODEL, "test-key")
        mocked.assert_called_once()

    def test_atlas_rejects_edit_mode_before_submission(self):
        with mock.patch.object(nano_banana.urllib.request, "urlopen") as mocked:
            with self.assertRaisesRegex(nano_banana.PermanentAPIError, "text-to-image only"):
                nano_banana._call_atlas(
                    "edit",
                    nano_banana.ATLAS_DEFAULT_MODEL,
                    "test-key",
                    edit_source=Path("source.png"),
                )
        mocked.assert_not_called()

    def test_cli_accepts_atlas_provider(self):
        args = nano_banana.build_parser().parse_args(["--provider", "atlas", "a lighthouse"])
        self.assertEqual(args.provider, "atlas")


if __name__ == "__main__":
    unittest.main()
