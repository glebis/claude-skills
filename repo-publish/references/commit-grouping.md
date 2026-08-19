# Commit Grouping Heuristics

How `intelligent_commit.sh` decides what goes in one commit and what gets separated. Read this when you want to override the default behavior or write a custom grouping rule.

## The Goal

A repo's commit log should read like a changelog written by someone who remembered what they were doing. That means:

1. **One logical change per commit.** A refactor and a feature are not one change.
2. **Same-prefix commits can be batched** when they're part of the same effort (e.g., all `test:` additions while implementing a feature).
3. **Lockfiles and config** stay separate from feature work, so reviewers can `git log --grep=feat` and get a clean diff.

## Default Mapping

`intelligent_commit.sh` uses this table to decide each file's commit prefix:

| File pattern                       | Prefix         | Rationale                                                |
|------------------------------------|----------------|----------------------------------------------------------|
| `*.test.*`, `*.spec.*`, `tests/*`  | `test`         | Test additions cluster together                          |
| `*.md`, `*README*`, `docs/*`       | `docs`         | Documentation rarely depends on code changes             |
| Lockfiles (`package-lock.json`...) | `chore(deps)`  | Auto-generated, separate from authored changes           |
| `.github/*`, `Dockerfile`, CI YAML | `ci`           | Infrastructure, not product                              |
| `*.json`, `*.toml`, `*.yaml` (config) | `chore(config)` | Configuration changes                                   |
| `*.css`, `*.tsx`, `components/*`   | `feat(ui)`     | UI changes are user-visible                               |
| `*.ts`, `*.js`, `*.py`, `*.go`...  | `feat`         | Default for source code                                   |
| Anything else                      | `chore`        | Catch-all                                                |

## When to Override

The default works in 80% of cases. Override when:

- **A "chore" file is actually load-bearing.** Example: a `Dockerfile` change that flips the runtime from Node 18 to Node 22 is a `feat`, not `ci`. Re-stage manually before running the script.
- **You're splitting a feature across many files** and want all of them in one commit. Run `git add -p` interactively, then `git commit -m "feat: ..."` and skip the script for that session.
- **The repo uses Conventional Commits strictly.** The script emits `feat:`, `fix:`, `docs:` prefixes — that's compatible. If the repo requires scopes (e.g., `feat(api): ...`), edit the `msg+="add "` line in the script to include the scope.

## Edge Cases

**Renames show up as add+delete.** Git treats most renames correctly but reports them in the path list twice. The script's `sort -u` deduplicates them.

**Binary files** (images, fonts) get routed to `chore`. Move them to a `chore(assets):` prefix manually if you want more signal.

**Submodule bumps** end up under the parent repo's diff. Group with the surrounding feature unless they're truly independent (rare).

## The "One Commit Per Release" Anti-Pattern

Don't try to reduce your PR to a single commit if the changes are genuinely multiple efforts. Multi-commit is the *point* — git bisect, `git revert`, and `git log -- path` all depend on logical separation. If a senior engineer asks you to squash, do it *after* landing, not before, via an interactive rebase that preserves meaningful messages.

## Verifying After Running

`git log --oneline -n 10` should look something like:

```
a1b2c3d docs: update installation instructions
e4f5g6h test: add coverage for parser error paths
i7j8k9l feat: add endpoint rate limiting
m0n1o2p chore(deps): update package-lock
```

If the prefixes look right, push. If not, `git reset --soft HEAD~N` to back out and re-stage manually.
