# Task Export — Linear & Beads

How to turn qualifying findings into tracker issues. Used by Step 5. **Never create an issue before the user confirms the proposed list.**

## 1. Select qualifying findings

- **Evaluation mode:** default **severity ≥ 3**. Honor a user override (`≥ 4` only, `≥ 2`, or an explicit pick).
- **Design-risk mode:** no severities exist. Only export (a) risk flags the user explicitly selects, or (b) the "highest-risk heuristics" named in the risk summary. State which basis was used — do not invent severities.

## 2. Severity → tracker priority mapping

| Finding severity | Linear `--priority` | Beads `--priority` |
|------------------|---------------------|--------------------|
| 4 — Catastrophe | `urgent` | `0` (highest) |
| 3 — Major | `high` | `1` |
| 2 — Minor | `medium` | `2` |
| 1 — Cosmetic | `low` | `3` |
| design-risk flag | `medium` (or ask) | `2` |

## 3. Task shape (one per finding)

- **Title:** `[H<n>] <short finding>` — e.g. `[H6] Toolbar icons unlabeled — recognition burden`.
- **Body/description (markdown):**
  ```
  **Heuristic:** H<n> — <name>
  **Severity:** <0–4> (<label>)   ·   **Artifact:** <name/URL/file>
  **Evidence:** <locator>
  **Fix:** <concrete fix>
  Source: nielsen-heuristics evaluation, <date>
  ```
- **Label (both trackers):** `usability` (and optionally `heuristic-eval`).

## 4. Propose-then-confirm gate (mandatory)

Print a table BEFORE creating anything, then ask "Create these N tasks in <tracker>?":

```
# | Title                                   | Sev | Priority | Heuristic
1 | [H6] Toolbar icons unlabeled            | 3   | high     | Recognition
2 | [H2] Cryptic "B:nsfw:hide" status token | 3   | high     | Match real world
```

Only on explicit approval, proceed to create. If the user edits the list, honor it.

## 5. Create — Linear (`linear` CLI, cloud)

Binary: `~/.claude/skills/linear/scripts/linear`. Default team is `Gleb-in-berlin` (override with `--team`). Prefer `--description-file` style by passing markdown via `-d`. One command per task:

```bash
~/.claude/skills/linear/scripts/linear create "[H6] Toolbar icons unlabeled — recognition burden" \
  --team "Gleb-in-berlin" \
  --priority high \
  --label usability \
  -d "**Heuristic:** H6 — Recognition rather than recall
**Severity:** 3 (Major) · **Artifact:** Cull Grid view
**Evidence:** top-center toolbar icon cluster, unlabeled
**Fix:** add tooltips/labels to the icon cluster
Source: nielsen-heuristics evaluation, 2026-07-04"
```

Capture the returned issue URL/ID and report it. Verify auth first if a call fails: `linear me` (re-auth via `linear auth`).

## 6. Create — Beads (`bd` CLI, local, per-repo)

`bd` operates on the `.beads` database of the **current repo** — confirm the working directory is the intended repo before creating (a heuristic eval of a codebase should file into that codebase's beads). Use `--dry-run` first to preview.

```bash
# preview
bd create "[H6] Toolbar icons unlabeled — recognition burden" \
  --priority 1 --label usability \
  --description "Heuristic H6 (Recognition). Severity 3. Evidence: unlabeled top toolbar cluster. Fix: add tooltips/labels." \
  --dry-run

# create for real (drop --dry-run); or capture just the ID with `bd q`
```

Useful flags: `--design` / `--design-file` (put the fix rationale), `--acceptance` (acceptance criteria = "the fix"), `--external-ref` (link back to a Linear issue if cross-filed), `-f <file>` to batch-create many issues from one markdown file. For batch creation, write all tasks to a markdown file and use `bd create -f <file>` rather than many single calls.

## 7. After creation

Report a compact list of created IDs/URLs grouped by tracker, and note any that failed (with the reason) so the user can retry.
