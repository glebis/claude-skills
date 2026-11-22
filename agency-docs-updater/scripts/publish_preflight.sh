#!/usr/bin/env bash
# Step 6 guard: run BEFORE committing/pushing in the docs site. Exits non-zero on
# any hazard and says why. Born from GDA 01 (2026-10-10), where the checkout was on
# a feature branch (codex/companion-t-shaped) whose content production already ran
# via Vercel CLI deploys, while origin/main lagged 22 commits behind:
#   - committing there put the meeting on the wrong branch;
#   - pushing only the meeting onto origin/main would have rolled production back;
#   - another session was editing the same checkout at the same time.
# Usage: publish_preflight.sh [DOCS_SITE_DIR]
set -uo pipefail
DIR="${1:-${DOCS_SITE_DIR:-$HOME/Sites/agency-docs}}"
cd "$DIR" || { echo "✗ not found: $DIR"; exit 2; }
fail=0
branch=$(git branch --show-current)
git fetch -q origin main 2>/dev/null
ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "?")
behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "?")
dirty=$(git status --porcelain | wc -l | tr -d ' ')

echo "branch: ${branch:-DETACHED}  vs origin/main: ahead $ahead, behind $behind  uncommitted: $dirty"
if [ "$branch" != "main" ]; then
  echo "✗ checkout is on '${branch:-detached HEAD}', not main — a commit here lands on that branch,"
  echo "  and pushing it to main merges the whole branch. Ask the user; or commit in a temp"
  echo "  worktree from origin/main (git worktree add --detach <tmp> origin/main)."
  fail=1
fi
if [ "$ahead" != "0" ] && [ "$ahead" != "?" ]; then
  echo "✗ HEAD has $ahead commit(s) not on origin/main — pushing publishes them too. List them"
  echo "  (git log origin/main..HEAD) and ask before pushing anything that isn't the pipeline's."
  fail=1
fi
if [ "$dirty" != "0" ]; then
  echo "• $dirty uncommitted path(s) — possibly another session's work. Stage ONLY pipeline files;"
  echo "  never stash/rebase in this checkout (use a temp worktree)."
fi
# Production source vs origin/main: a CLI deploy newer than main's last git deploy means
# production runs code that main lacks — a git push to main would roll it back.
if command -v vercel >/dev/null 2>&1 && [ -f .vercel/project.json ]; then
  latest=$(vercel ls --prod 2>/dev/null | grep -m1 -o 'https://[^ ]*vercel.app')
  if [ -n "$latest" ]; then
    created=$(vercel inspect "$latest" 2>&1 | awk '/created/{$1=""; print; exit}')
    main_date=$(git log -1 --format=%cI origin/main)
    echo "production: $latest (created$created); origin/main last commit: $main_date"
    echo "  → if production is newer than origin/main and was deployed from a branch/CLI,"
    echo "    pushing to main ships origin/main's tree: confirm production's source first."
  fi
fi
[ "$fail" -eq 0 ] && echo "✓ safe to commit pipeline files on main and push" || echo "✗ STOP — resolve the above with the user"
exit "$fail"
