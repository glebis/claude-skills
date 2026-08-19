---
name: repo-publish
description: 'Publish a local repository to a remote with quality gates, version tagging, and rollout steps. Use this skill when the user asks to publish, release, or push a project end-to-end. Triggers on "publish repo", "release project", "ship it", "push to remote".'
---

# Repo Publish

End-to-end pipeline for taking a project from "I made changes" to "live on a remote". Runs quality gates, generates an intelligent multi-commit history, pushes, and verifies the deploy.

## When to Use

Use this skill when:
- The user says "publish", "release", "ship it", "push to remote", "deploy this"
- A project has accumulated local changes that need to land cleanly
- A version bump or release needs to be cut
- The user explicitly asks to run the full landing-the-plane workflow

Do **not** use this skill for:
- Single quick commits the user is doing themselves
- Documentation-only edits (use the project's own docs workflow)
- Anything involving secrets/credentials (the scripts will skip those files)

## Workflow Decision Tree

Start here. Pick the lane based on the user's intent:

```
User wants to publish
  ├─ Has local changes? ──── no ──► Just push / bump version
  ├─ Want a release? ──── yes ──► [Release mode](#release-mode)
  └─ Just routine commit? ──────► [Push mode](#push-mode)
```

## Push Mode

For ordinary commits that need to land.

### Step 1 — File remaining work

Run the issue tracker step:

```bash
bd ready              # What's pending
bd show <id>          # Inspect any blockers
bd update <id> --status in_progress  # Claim work
```

If you can't `bd`, ask the user how they track issues for this project. Don't silently skip it — issue hygiene is part of the gate.

### Step 2 — Run quality gates

Inspect `package.json`, `pyproject.toml`, `Makefile`, or whatever exists and run whatever the project defines as "test + lint + build":

```bash
# Node
npm test && npm run lint && npm run build

# Python
pytest && ruff check . && mypy .

# Go
go test ./... && go vet ./...

# Rust
cargo test && cargo clippy -- -D warnings

# Makefile-driven
make test lint build
```

If a gate fails, **stop**. Report which gate failed and the relevant error. Don't try to fix the code in the same publish flow — open a fix-PR first.

For projects without an obvious test command, run `ls` to find the closest script and ask the user.

### Step 3 — Stage and commit intelligently

Use the `scripts/intelligent_commit.sh` helper. It groups files by change type (features, fixes, docs, chore) and produces one commit per group:

```bash
~/.agents/skills/repo-publish/scripts/intelligent_commit.sh
```

Read its docs at `references/commit-grouping.md` for the heuristics.

If the user prefers a single commit, ask explicitly before combining.

### Step 4 — Pull rebase, push, verify

```bash
git pull --rebase        # Resolve any rebase conflicts before pushing
git push                 # Pushes the working branch
git status               # MUST show "Your branch is up to date"
```

If push is rejected: there's a remote-side change. Pull rebase again, resolve, retry. Never `--force` without explicit user consent.

## Release Mode

For cutting versions. Adds three extra steps before push.

### Step R1 — Choose bump type

Ask the user: `patch` (x.y.Z → x.y.(Z+1)), `minor` (X.Y → X.(Y+1)), or `major`. Default to patch unless they say otherwise. Read the change log to confirm.

### Step R2 — Bump version

```bash
# Node
npm version <patch|minor|major>  # Updates package.json + creates tag

# Python (with bumpversion or similar)
bumpversion <patch|minor|major>

# Manual: edit pyproject.toml / VERSION / package.json by hand, then:
git tag -a v<VERSION> -m "Release v<VERSION>"
```

### Step R3 — Generate / update CHANGELOG

If the project has a `CHANGELOG.md`, append a new section for this version with bullet points summarizing the commits in `git log --oneline v<PREV>..HEAD`. If it doesn't, skip — don't create empty changelogs.

### Step R4 — Commit the release

```bash
git add package.json CHANGELOG.md  # or equivalents
git commit -m "release: v<VERSION>"
git push --follow-tags
```

The `--follow-tags` pushes the new tag along with the commit.

### Step R5 — Post-release verification

```bash
git tag --list "v<VERSION>"   # Tag should appear
git ls-remote --tags origin    # Verify remote has the tag
```

For projects with deployment automation (Vercel, npm publish, etc.), the user usually has a manual post-push step. Ask, don't assume.

## Common Pitfalls

- **Never `--force` push** without explicit user consent and a clear reason. It rewrites shared history.
- **Don't run tests in a publish flow that you can't read the output of.** If the runner is opaque, surface the URL or command to the user.
- **Don't commit secrets.** `.env`, `*.pem`, `id_rsa`, etc. Check `git status` for these before staging.
- **If `bd` (or whatever tracker) has open issues**, file the remaining work as a new issue and reference the ID in the commit before pushing.
- **If multiple branches diverge**, the right move is `bd sync` followed by a fresh `git pull --rebase`. Don't try to force-push your way out of sync.

## Environment Variables

None required. The skill uses whatever git is configured to use for push. If the user needs a specific remote credential, they'll have it set in their git config.

## Related Workflows

- **Single-commit hotfix** → skip intelligent_commit.sh, use `git add -p` + a single `git commit`
- **Bisecting a regression** → not the publish skill's job; use git bisect directly
- **Pre-release testing** → use the project's own staging environment before invoking this skill
