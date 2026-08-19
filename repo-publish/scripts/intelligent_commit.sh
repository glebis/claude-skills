#!/usr/bin/env bash
# intelligent_commit.sh
#
# Group git changes by type and produce one commit per group.
# Reads heuristics from references/commit-grouping.md.
#
# Compatible with bash 3.2 (default on macOS) and bash 4+.
#
# Usage:
#   intelligent_commit.sh            # Stage all, commit in groups
#   intelligent_commit.sh --dry-run  # Show planned commits, don't run
#
# Requires: git, GNU coreutils (sort, head)

set -euo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

# 1. Verify we're in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2
  exit 1
fi

# 2. Check there are changes to commit
if git diff --cached --quiet && git diff --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
  echo "nothing to commit, working tree clean"
  exit 0
fi

# 3. Heuristic: file path → commit prefix
map_to_prefix() {
  local file="$1"
  case "$file" in
    *.test.*|*.spec.*|*__tests__/*|tests/*|test/*) echo "test" ;;
    *.md|*README*|*CHANGELOG*|docs/*) echo "docs" ;;
    package-lock.json|yarn.lock|poetry.lock|Pipfile.lock|go.sum|Cargo.lock) echo "chore(deps)" ;;
    .github/*|.circleci/*|.gitlab-ci.yml|.buildkite/*|Dockerfile|docker-compose*.yml) echo "ci" ;;
    *.json|*.toml|*.yaml|*.yml|*.env.example) echo "chore(config)" ;;
    *.css|*.scss|*.sass|*.less|*.tsx|*.jsx|components/*|src/components/*|app/*) echo "feat(ui)" ;;
    *.ts|*.js|*.py|*.go|*.rs|*.java|*.swift|*.kt|*.c|*.cpp|*.h|*.hpp) echo "feat" ;;
    *) echo "chore" ;;
  esac
}

# 4. Stage everything (respecting .gitignore)
git add -A

# 5. Snapshot staged files, group them by prefix into flat variable files
TMP=$(mktemp)
trap "rm -f $TMP" EXIT
git diff --cached --name-only > "$TMP"

# Use temp files per-prefix (bash 3 doesn't have associative arrays)
GROUPS_DIR=$(mktemp -d)
trap "rm -f $TMP; rm -rf $GROUPS_DIR" EXIT

while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  prefix=$(map_to_prefix "$file")
  # Sanitize prefix for use as a filename (parens and slashes are bad)
  safe_prefix=$(echo "$prefix" | tr '/()' '___')
  echo "$file" >> "$GROUPS_DIR/$safe_prefix"
  echo "$prefix" >> "$GROUPS_DIR/.prefixes_seen"
done < "$TMP"

# 6. Iterate each group, emit (or execute) one commit per group
ran_any=0
sort -u "$GROUPS_DIR/.prefixes_seen" 2>/dev/null | while IFS= read -r prefix; do
  [[ -z "$prefix" ]] && continue
  safe_prefix=$(echo "$prefix" | tr '/()' '___')
  group_file="$GROUPS_DIR/$safe_prefix"
  [[ ! -f "$group_file" ]] && continue
  files=$(sort -u "$group_file" | grep -v '^$' || true)
  [[ -z "$files" ]] && continue

  echo "────────────────────────────────────────"
  echo "Group: $prefix"
  echo "$files" | sed 's/^/  /'
  echo "────────────────────────────────────────"

  if [[ $DRY_RUN -eq 1 ]]; then
    continue
  fi

  git reset >/dev/null
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    git add -- "$f"
  done <<< "$files"

  msg="${prefix}: "
  case "$prefix" in
    feat|feat\(ui\)) msg+="add " ;;
    test)             msg+="add tests for " ;;
    docs)             msg+="update documentation" ;;
    chore*)           msg+="update " ;;
    ci)               msg+="update CI configuration" ;;
    fix)              msg+="resolve " ;;
    *)                msg+="update " ;;
  esac

  if git commit -m "$msg" --no-verify; then
    ran_any=1
  else
    echo "warning: commit for group '$prefix' failed, leaving staged" >&2
  fi
done

if [[ $DRY_RUN -eq 0 && $ran_any -eq 0 ]]; then
  echo "no commits produced"
  exit 1
fi

echo
git log --oneline -n 10
