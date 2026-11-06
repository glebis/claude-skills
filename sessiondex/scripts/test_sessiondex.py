"""Run with: python3 -m unittest test_sessiondex"""
import json
import os
import tempfile
import unittest

import sessiondex as sd


class Clean(unittest.TestCase):
    def test_keeps_voice_input_and_drops_transcript(self):
        text = "<realtime_delegation>\n<input>open my calendar</input>\n<transcript_delta>user: hi</transcript_delta>\n</realtime_delegation>"
        self.assertEqual(sd.clean(text), "open my calendar")

    def test_keeps_text_after_ambient_context(self):
        text = '<in-app-browser-context source="x">state</in-app-browser-context>\nfix the header'
        self.assertEqual(sd.clean(text), "fix the header")

    def test_drops_pure_automation(self):
        self.assertEqual(sd.clean("<heartbeat><instructions>x</instructions></heartbeat>"), "")

    def test_slash_command_becomes_readable(self):
        text = "<command-message>finances</command-message>\n<command-name>/finances</command-name>\n<command-args>q3</command-args>"
        self.assertEqual(" ".join(sd.clean(text).split()), "/finances q3")

    def test_non_string_is_empty(self):
        self.assertEqual(sd.clean(None), "")


class Redact(unittest.TestCase):
    def test_scrubs_known_shapes(self):
        for secret in ("sk-" + "a" * 30, "ghp_" + "b" * 30, "AKIA" + "C" * 16):
            self.assertNotIn(secret, sd.redact(f"key {secret} here"))

    def test_keeps_label_of_assignment(self):
        self.assertEqual(sd.redact("password=hunter2hunter2"), "password=[REDACTED]")

    def test_leaves_prose_alone(self):
        prose = "the token budget was fine"
        self.assertEqual(sd.redact(prose), prose)


class Query(unittest.TestCase):
    def test_quotes_terms_so_punctuation_is_safe(self):
        self.assertEqual(sd.fts_query("foo-bar c++"), '"foo-bar" "c++"')


class Pipeline(unittest.TestCase):
    def test_claude_file_indexes_and_skips_when_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            project = os.path.join(root, "proj")
            os.makedirs(os.path.join(project, "vercel-plugin"))
            rows = [
                {"type": "user", "uuid": "1", "cwd": "/w", "timestamp": "2026-01-01T10:00:00Z",
                 "message": {"content": "find the parser bug"}},
                {"type": "assistant", "uuid": "2", "timestamp": "2026-01-01T10:01:00Z",
                 "message": {"content": [{"type": "thinking", "thinking": "secret plan"},
                                         {"type": "text", "text": "fixed it"}]}},
                {"type": "user", "uuid": "2", "message": {"content": "duplicate uuid"}},
            ]
            with open(os.path.join(project, "abc.jsonl"), "w") as fh:
                fh.write("\n".join(json.dumps(r) for r in rows) + "\nnot json\n")
            with open(os.path.join(project, "vercel-plugin", "log.jsonl"), "w") as fh:
                fh.write("{}\n")
            sd.CLAUDE_DIR = root
            found = list(sd.read_claude())
            self.assertEqual(len(found), 1)  # plugin log ignored
            session, load = found[0]
            messages = load()
            self.assertEqual([m[2] for m in messages], ["find the parser bug", "fixed it"])
            self.assertEqual(session["cwd"], "/w")


if __name__ == "__main__":
    unittest.main()
