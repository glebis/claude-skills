#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
installer="$script_dir/install-suite.sh"
source_root=$(cd "$script_dir/../.." && pwd)
tmp=$(mktemp -d)
trap 'trash "$tmp"' EXIT
skills=(cull-release cull-release-check cull-release-prepare cull-release-publish cull-release-verify cull-release-recover)

created="$tmp/created"
AGENT_SKILLS_DIR="$created" bash "$installer"
for skill in "${skills[@]}"; do
  test -L "$created/$skill"
  test "$(readlink "$created/$skill")" = "$source_root/$skill"
done
AGENT_SKILLS_DIR="$created" bash "$installer"

wrong="$tmp/wrong"
mkdir -p "$wrong"
ln -s "$tmp/not-the-suite" "$wrong/cull-release"
if AGENT_SKILLS_DIR="$wrong" bash "$installer"; then
  echo "installer replaced or accepted a wrong symlink" >&2
  exit 1
fi
test "$(readlink "$wrong/cull-release")" = "$tmp/not-the-suite"

directory="$tmp/directory"
mkdir -p "$directory/cull-release"
if AGENT_SKILLS_DIR="$directory" bash "$installer"; then
  echo "installer replaced or accepted a real directory" >&2
  exit 1
fi
test -d "$directory/cull-release"

echo "install-suite tests passed"
