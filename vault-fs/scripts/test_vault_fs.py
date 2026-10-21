import contextlib
import io
import os
import tempfile
import unittest

import vault_fs


class VaultFsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, text="x"):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def get(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8") as fh:
            return fh.read()

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = vault_fs.main([*argv, "--vault", self.root])
        return code, out.getvalue()

    def test_rename_rewrites_bare_pathed_and_markdown_links(self):
        self.put("a/Old.md")
        self.put("ref.md", "[[Old]] [[Old#h|al]] ![[a/Old]] [m](a/Old.md) `[[Old]]`\n"
                           "```\n[[Old]]\n```\n| [[Old\\|t]] |")
        self.run_cli("mv", "a/Old.md", "b/New.md", "--apply")
        self.assertTrue(os.path.exists(os.path.join(self.root, "b/New.md")))
        self.assertEqual(self.get("ref.md"),
                         "[[New]] [[New#h|al]] ![[b/New]] [m](b/New.md) `[[Old]]`\n"
                         "```\n[[Old]]\n```\n| [[New\\|t]] |")

    def test_dry_run_changes_nothing(self):
        self.put("Old.md")
        self.put("ref.md", "[[Old]]")
        code, out = self.run_cli("mv", "Old", "New")
        self.assertEqual(code, 0)
        self.assertIn("dry run", out)
        self.assertTrue(os.path.exists(os.path.join(self.root, "Old.md")))
        self.assertEqual(self.get("ref.md"), "[[Old]]")

    def test_moved_note_rebases_its_relative_links(self):
        self.put("x/Note.md", "[[../Other]] [o](../Other.md) [[Other]] [[x/Sib]]")
        self.put("Other.md")
        self.put("x/Sib.md")
        self.run_cli("mv", "x/Note.md", "y/z/", "--apply")
        self.assertEqual(self.get("y/z/Note.md"), "[[../../Other]] [o](../../Other.md) [[Other]] [[x/Sib]]")

    def test_ambiguous_new_name_falls_back_to_path(self):
        self.put("p/Old.md")
        self.put("q/New.md")
        self.put("ref.md", "[[Old]]")
        self.run_cli("mv", "p/Old.md", "p/New.md", "--apply")
        self.assertEqual(self.get("ref.md"), "[[p/New]]")

    def test_attachment_and_encoded_markdown_link(self):
        self.put("Attachments/my pic.png")
        self.put("n.md", "![[my pic.png]] ![p](Attachments/my%20pic.png)")
        self.run_cli("mv", "Attachments/my pic.png", "img/pic 2.png", "--apply")
        self.assertEqual(self.get("n.md"), "![[pic 2.png]] ![p](img/pic%202.png)")

    def test_refuses_existing_destination(self):
        self.put("A.md")
        self.put("B.md")
        with self.assertRaises(SystemExit):
            self.run_cli("mv", "A", "B")

    def test_rm_refuses_while_linked(self):
        self.put("Dead.md")
        self.put("ref.md", "see [[Dead]]")
        code, out = self.run_cli("rm", "Dead", "--apply")
        self.assertEqual(code, 1)
        self.assertIn("ref.md", out)
        self.assertTrue(os.path.exists(os.path.join(self.root, "Dead.md")))


if __name__ == "__main__":
    unittest.main()
