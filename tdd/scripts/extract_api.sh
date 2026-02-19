#!/usr/bin/env bash
# Extract public API signatures from source files (no function bodies).
# Usage: extract_api.sh <source_dir> [--lang <language>]
#
# Auto-detects language from file extensions. Override with --lang.
# Supported: typescript, javascript, python, go, rust, ruby, php
#
# Output: public function/class/type signatures, one per line.
# This output is fed to the Test Writer agent so it knows what
# interfaces exist without seeing implementation details.

set -euo pipefail

SOURCE_DIR="${1:?Usage: extract_api.sh <source_dir> [--lang <language>]}"
LANG_OVERRIDE=""

shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang) LANG_OVERRIDE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Auto-detect language from most common file extension
detect_language() {
  local dir="$1"
  local ts_count js_count py_count go_count rs_count rb_count php_count

  ts_count=$(find "$dir" -name '*.ts' -not -name '*.d.ts' -not -path '*/node_modules/*' -not -path '*/.next/*' | head -50 | wc -l | tr -d ' ')
  js_count=$(find "$dir" -name '*.js' -not -path '*/node_modules/*' -not -path '*/.next/*' | head -50 | wc -l | tr -d ' ')
  py_count=$(find "$dir" -name '*.py' -not -path '*/__pycache__/*' -not -path '*/venv/*' | head -50 | wc -l | tr -d ' ')
  go_count=$(find "$dir" -name '*.go' -not -path '*/vendor/*' | head -50 | wc -l | tr -d ' ')
  rs_count=$(find "$dir" -name '*.rs' -not -path '*/target/*' | head -50 | wc -l | tr -d ' ')
  rb_count=$(find "$dir" -name '*.rb' -not -path '*/vendor/*' | head -50 | wc -l | tr -d ' ')
  php_count=$(find "$dir" -name '*.php' -not -path '*/vendor/*' | head -50 | wc -l | tr -d ' ')

  local max=0 lang="unknown"
  for pair in "typescript:$ts_count" "javascript:$js_count" "python:$py_count" "go:$go_count" "rust:$rs_count" "ruby:$rb_count" "php:$php_count"; do
    local l="${pair%%:*}" c="${pair##*:}"
    if [[ "$c" -gt "$max" ]]; then max="$c"; lang="$l"; fi
  done

  # If ts and js both exist, prefer ts
  if [[ "$ts_count" -gt 0 ]]; then lang="typescript"; fi

  echo "$lang"
}

LANG="${LANG_OVERRIDE:-$(detect_language "$SOURCE_DIR")}"

extract_typescript() {
  local dir="$1"
  echo "# TypeScript/JavaScript API Surface"
  echo "# Source: $dir"
  echo ""

  find "$dir" -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' \) \
    -not -name '*.test.*' -not -name '*.spec.*' -not -name '*.d.ts' \
    -not -path '*/node_modules/*' -not -path '*/.next/*' -not -path '*/dist/*' \
    -not -path '*/__tests__/*' -not -path '*/build/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    local rel="${file#$dir/}"

    # Extract export lines (includes re-exports and default exports)
    local exports
    exports=$(grep -nE '^export ' "$file" 2>/dev/null | grep -vE '^\s*//' || true)

    if [[ -n "$exports" ]]; then
      echo "## $rel"
      while IFS= read -r line; do
        local cleaned
        cleaned=$(echo "$line" | sed -E 's/\{[^}]*$/\{...}/' | sed -E 's/= .+$/= ...;/')
        echo "  $cleaned"
      done <<< "$exports"
      echo ""
    fi
  done
}

extract_python() {
  local dir="$1"
  echo "# Python API Surface"
  echo "# Source: $dir"
  echo ""

  find "$dir" -type f -name '*.py' \
    -not -name 'test_*' -not -name '*_test.py' -not -name 'conftest.py' \
    -not -path '*/venv/*' -not -path '*/__pycache__/*' -not -path '*/tests/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    local rel="${file#$dir/}"
    local output=""

    # Extract __all__ exports if present
    local all_exports
    all_exports=$(grep -n '^__all__' "$file" 2>/dev/null || true)
    if [[ -n "$all_exports" ]]; then
      output+="$all_exports"$'\n'
    fi

    # Get top-level functions, classes, and decorators
    local top_level
    top_level=$(grep -nE '^(def [a-zA-Z][a-zA-Z0-9_]*|class [a-zA-Z][a-zA-Z0-9_]*|async def [a-zA-Z][a-zA-Z0-9_]*|@(property|staticmethod|classmethod|dataclass|runtime_checkable))' "$file" 2>/dev/null | grep -v '^\s*def _' || true)
    if [[ -n "$top_level" ]]; then
      output+="$top_level"$'\n'
    fi

    # Get class methods (1-level indent: 4 spaces or 1 tab)
    local methods
    methods=$(grep -nE '^(    |\t)(def [a-zA-Z][a-zA-Z0-9_]*|async def [a-zA-Z][a-zA-Z0-9_]*)' "$file" 2>/dev/null | grep -v 'def _[a-zA-Z]' || true)
    if [[ -n "$methods" ]]; then
      output+="$methods"$'\n'
    fi

    output=$(echo "$output" | sort -t: -k1,1n | uniq)

    if [[ -n "$output" ]]; then
      echo "## $rel"
      while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        echo "  $line"
      done <<< "$output"
      echo ""
    fi
  done
}

extract_go() {
  local dir="$1"
  echo "# Go API Surface"
  echo "# Source: $dir"
  echo ""

  find "$dir" -type f -name '*.go' \
    -not -name '*_test.go' \
    -not -path '*/vendor/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    local rel="${file#$dir/}"

    # Exported: functions/types starting with uppercase
    local signatures
    signatures=$(grep -nE '^(func [A-Z]|type [A-Z]|var [A-Z]|const [A-Z])' "$file" 2>/dev/null || true)

    if [[ -n "$signatures" ]]; then
      echo "## $rel"
      while IFS= read -r line; do
        echo "  $line"
      done <<< "$signatures"
      echo ""
    fi
  done
}

extract_rust() {
  local dir="$1"
  echo "# Rust API Surface"
  echo "# Source: $dir"
  echo ""

  find "$dir" -type f -name '*.rs' \
    -not -path '*/target/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    local rel="${file#$dir/}"

    local signatures
    signatures=$(grep -nE '^pub (fn|struct|enum|trait|type|const|static|mod|use)' "$file" 2>/dev/null || true)

    if [[ -n "$signatures" ]]; then
      echo "## $rel"
      while IFS= read -r line; do
        echo "  $line"
      done <<< "$signatures"
      echo ""
    fi
  done
}

extract_ruby() {
  local dir="$1"
  echo "# Ruby API Surface"
  echo "# Source: $dir"
  echo ""

  find "$dir" -type f -name '*.rb' \
    -not -name '*_spec.rb' -not -name '*_test.rb' \
    -not -path '*/spec/*' -not -path '*/test/*' -not -path '*/vendor/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    local rel="${file#$dir/}"

    local signatures
    signatures=$(grep -nE '^\s*(class |module |def [a-z]|def self\.)' "$file" 2>/dev/null || true)

    if [[ -n "$signatures" ]]; then
      echo "## $rel"
      while IFS= read -r line; do
        echo "  $line"
      done <<< "$signatures"
      echo ""
    fi
  done
}

extract_php() {
  local dir="$1"
  echo "# PHP API Surface"
  echo "# Source: $dir"
  echo ""

  find "$dir" -type f -name '*.php' \
    -not -name '*Test.php' \
    -not -path '*/vendor/*' -not -path '*/tests/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    local rel="${file#$dir/}"

    local signatures
    signatures=$(grep -nE '^\s*(public |protected |private )?(static )?(function |class |interface |trait |enum )' "$file" 2>/dev/null || true)

    if [[ -n "$signatures" ]]; then
      echo "## $rel"
      while IFS= read -r line; do
        echo "  $line"
      done <<< "$signatures"
      echo ""
    fi
  done
}

# Dispatch
case "$LANG" in
  typescript|javascript) extract_typescript "$SOURCE_DIR" ;;
  python)                extract_python "$SOURCE_DIR" ;;
  go)                    extract_go "$SOURCE_DIR" ;;
  rust)                  extract_rust "$SOURCE_DIR" ;;
  ruby)                  extract_ruby "$SOURCE_DIR" ;;
  php)                   extract_php "$SOURCE_DIR" ;;
  *)
    echo "# Unknown language: $LANG"
    echo "# Could not auto-detect from files in $SOURCE_DIR"
    echo "# Use --lang to specify: typescript, python, go, rust, ruby, php"
    exit 1
    ;;
esac
