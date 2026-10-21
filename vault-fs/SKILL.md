---
name: vault-fs
description: Safely move, rename, or trash notes and attachments in an Obsidian vault while keeping every link working. Use whenever a vault file operation is requested — "move this note to X", "rename note", "reorganize folder", "bulk move", "archive these notes", "delete/trash this note", "is anything linking to this?" — instead of mv/rm/git mv, which silently break [[wikilinks]]. Dry-run by default, stdlib only.
---

# Vault FS

One script, `scripts/vault_fs.py`, does vault file operations the way Obsidian's
"Automatically update internal links" does. **Dry-run by default** — always run once without
`--apply`, show the user the summary, then re-run with `--apply`.

Default vault: `~/Brains/brain` (override with `--vault PATH`).

```bash
S=~/.claude/skills/vault-fs/scripts/vault_fs.py
python3 $S mv "Inbox/Idea.md" "Projects/"                 # move into a folder (keeps name)
python3 $S mv "Old name" "Folder/New name" --apply        # move + rename; .md optional
python3 $S mv --batch moves.tsv                           # many moves, one vault scan (source<TAB>dest)
python3 $S rm "Dead note" "Attachments/x.png"             # list inbound links; refuses if any
python3 $S rm "Dead note" --apply                         # send to macOS Trash via `trash`
```

## What it guarantees

- Rewrites `[[x]]`, `![[x]]`, `#heading`, `#^block`, `|alias`, table-escaped `[[x\|a]]`, and
  markdown links `[t](x.md)` / `%20`-encoded — in the style they were written.
- Renames rewrite bare `[[Old]]` links. If the new name is shared with another note, writes a
  path link instead of trusting Obsidian's tie-break.
- Relative links inside a moved note are re-based on its new folder.
- Code blocks and inline code are never touched.
- Whole batch is validated first (missing source, existing destination, duplicates); one
  refusal means nothing moved.
- `rm` never hard-deletes; it refuses while anything links to the file unless `--force`.

## From other scripts

```python
sys.path.insert(0, os.path.expanduser("~/.claude/skills/vault-fs/scripts"))
import vault_fs
moves, edits, warnings = vault_fs.move_files(vault_root, [(src_rel, dst_rel), ...], apply=True)
# raises vault_fs.MoveError (nothing changed) if any pair is refused
```

## Not handled

Moving whole folders (list the files in a batch instead), Obsidian aliases in frontmatter
(`aliases:` keep working because they live inside the moved note), and links in non-markdown
files (canvas, JSON).

Tests: `cd scripts && python3 -m unittest test_vault_fs`.
