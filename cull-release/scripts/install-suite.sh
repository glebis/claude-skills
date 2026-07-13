#!/usr/bin/env bash
set -euo pipefail

skills=(cull-release cull-release-check cull-release-prepare cull-release-publish cull-release-verify cull-release-recover)
source_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
target_root=${AGENT_SKILLS_DIR:-$HOME/.agents/skills}
mkdir -p "$target_root"

for skill in "${skills[@]}"; do
  source_path="$source_root/$skill"
  target_path="$target_root/$skill"
  if [[ ! -d "$source_path" ]]; then
    echo "missing suite skill: $source_path" >&2
    exit 2
  fi
  if [[ -L "$target_path" && "$(readlink "$target_path")" == "$source_path" ]]; then
    continue
  fi
  if [[ -e "$target_path" || -L "$target_path" ]]; then
    echo "refusing to replace existing skill path: $target_path" >&2
    exit 2
  fi
  ln -s "$source_path" "$target_path"
done
