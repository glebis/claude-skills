#!/usr/bin/env bash
# Discover and extract project documentation relevant to TDD spec writing.
# Usage: discover_docs.sh <project_dir> [--lang <language>]
#
# Searches for:
#   1. Documentation files (README, docs/, ARCHITECTURE, CONTRIBUTING, ADRs)
#   2. API specification files (OpenAPI/Swagger, GraphQL schemas, .proto)
#   3. Inline docstrings from source code (JSDoc, Google-style, Rust doc comments)
#
# Output: structured text summary of discovered documentation,
# fed to Phase 1 (decomposition) and Phase 2 (Test Writer) as context.

set -euo pipefail

PROJECT_DIR="${1:?Usage: discover_docs.sh <project_dir> [--lang <language>]}"
LANG_OVERRIDE=""

shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang) LANG_OVERRIDE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

MAX_DOC_LINES=200  # cap per-file extraction to keep context reasonable
MAX_TOTAL_CHARS=15000  # hard cap on total output

# Track total chars emitted
TOTAL_CHARS=0

emit() {
  local text="$1"
  local len=${#text}
  if (( TOTAL_CHARS + len > MAX_TOTAL_CHARS )); then
    local remaining=$((MAX_TOTAL_CHARS - TOTAL_CHARS))
    if (( remaining > 50 )); then
      echo "${text:0:$remaining}"
      echo "... (truncated — doc discovery capped at ${MAX_TOTAL_CHARS} chars)"
    fi
    TOTAL_CHARS=$MAX_TOTAL_CHARS
    return 1  # signal to stop
  fi
  echo "$text"
  TOTAL_CHARS=$((TOTAL_CHARS + len + 1))  # +1 for newline
  return 0
}

# ── Section 1: Documentation files ──────────────────────────────────

emit "# Project Documentation" || exit 0
emit "" || exit 0

# Find markdown/text docs (not in node_modules, vendor, etc.)
DOC_FILES=$(find "$PROJECT_DIR" -maxdepth 3 -type f \
  \( -iname 'README*' -o -iname 'ARCHITECTURE*' -o -iname 'CONTRIBUTING*' \
     -o -iname 'DESIGN*' -o -iname 'SPEC*' -o -iname 'API*' \
     -o -iname 'CHANGELOG*' \) \
  -not -path '*/node_modules/*' -not -path '*/vendor/*' \
  -not -path '*/.git/*' -not -path '*/target/*' \
  -not -path '*/dist/*' -not -path '*/build/*' \
  -not -path '*/venv/*' -not -path '*/__pycache__/*' \
  2>/dev/null | sort || true)

# Also check docs/ directory
if [[ -d "$PROJECT_DIR/docs" ]]; then
  DOCS_DIR_FILES=$(find "$PROJECT_DIR/docs" -maxdepth 2 -type f \
    \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) \
    2>/dev/null | sort || true)
  DOC_FILES=$(printf '%s\n%s' "$DOC_FILES" "$DOCS_DIR_FILES" | sort -u)
fi

# Also check doc/ directory
if [[ -d "$PROJECT_DIR/doc" ]]; then
  DOC_DIR_FILES=$(find "$PROJECT_DIR/doc" -maxdepth 2 -type f \
    \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) \
    2>/dev/null | sort || true)
  DOC_FILES=$(printf '%s\n%s' "$DOC_FILES" "$DOC_DIR_FILES" | sort -u)
fi

if [[ -n "$DOC_FILES" ]]; then
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    rel="${file#$PROJECT_DIR/}"
    emit "## $rel" || exit 0
    head -n "$MAX_DOC_LINES" "$file" | while IFS= read -r line; do
      emit "$line" || exit 0
    done
    emit "" || exit 0
  done <<< "$DOC_FILES"
else
  emit "(No documentation files found)" || exit 0
  emit "" || exit 0
fi

# ── Section 2: API specification files ──────────────────────────────

emit "# API Specifications" || exit 0
emit "" || exit 0

API_SPECS=$(find "$PROJECT_DIR" -maxdepth 4 -type f \
  \( -name 'openapi.*' -o -name 'swagger.*' \
     -o -name '*.openapi.json' -o -name '*.openapi.yaml' -o -name '*.openapi.yml' \
     -o -name 'schema.graphql' -o -name '*.graphqls' \
     -o -name '*.proto' \
     -o -name 'api-spec.*' \) \
  -not -path '*/node_modules/*' -not -path '*/vendor/*' \
  -not -path '*/.git/*' \
  2>/dev/null | sort || true)

if [[ -n "$API_SPECS" ]]; then
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    rel="${file#$PROJECT_DIR/}"
    emit "## $rel" || exit 0
    head -n "$MAX_DOC_LINES" "$file" | while IFS= read -r line; do
      emit "$line" || exit 0
    done
    emit "" || exit 0
  done <<< "$API_SPECS"
else
  emit "(No API specification files found)" || exit 0
  emit "" || exit 0
fi

# ── Section 3: Docstrings from source code ──────────────────────────

emit "# Source Docstrings" || exit 0
emit "" || exit 0

# Auto-detect language if not overridden
if [[ -z "$LANG_OVERRIDE" ]]; then
  ts_count=$(find "$PROJECT_DIR" -name '*.ts' -not -path '*/node_modules/*' 2>/dev/null | head -20 | wc -l | tr -d ' ')
  py_count=$(find "$PROJECT_DIR" -name '*.py' -not -path '*/venv/*' -not -path '*/__pycache__/*' 2>/dev/null | head -20 | wc -l | tr -d ' ')
  go_count=$(find "$PROJECT_DIR" -name '*.go' -not -path '*/vendor/*' 2>/dev/null | head -20 | wc -l | tr -d ' ')
  rs_count=$(find "$PROJECT_DIR" -name '*.rs' -not -path '*/target/*' 2>/dev/null | head -20 | wc -l | tr -d ' ')

  max=0; LANG="unknown"
  for pair in "typescript:$ts_count" "python:$py_count" "go:$go_count" "rust:$rs_count"; do
    l="${pair%%:*}"; c="${pair##*:}"
    if [[ "$c" -gt "$max" ]]; then max="$c"; LANG="$l"; fi
  done
  [[ "$ts_count" -gt 0 ]] && LANG="typescript"
else
  LANG="$LANG_OVERRIDE"
fi

extract_docstrings_python() {
  python3 -c "
import ast, sys, os

project = sys.argv[1]
max_lines = int(sys.argv[2])
count = 0

for root, dirs, files in os.walk(project):
    # Skip irrelevant dirs
    dirs[:] = [d for d in dirs if d not in ('__pycache__', 'venv', '.venv', 'node_modules', '.git', 'tests', 'test')]
    for f in sorted(files):
        if not f.endswith('.py') or f.startswith('test_') or f.endswith('_test.py'):
            continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, project)
        try:
            with open(path) as fh:
                tree = ast.parse(fh.read())
        except Exception:
            continue

        file_docs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                if doc and not node.name.startswith('_'):
                    # Truncate long docstrings
                    lines = doc.strip().split('\n')
                    if len(lines) > 8:
                        lines = lines[:8] + ['...']
                    file_docs.append(f'  {node.name}: {chr(10).join(\"    \" + l for l in lines)}')

        if file_docs:
            print(f'## {rel}')
            for d in file_docs:
                print(d)
                count += 1
            print()

        if count > max_lines:
            print('... (truncated)')
            sys.exit(0)
" "$PROJECT_DIR" "$MAX_DOC_LINES" 2>/dev/null || true
}

extract_docstrings_typescript() {
  # Extract JSDoc comments (/** ... */) attached to exports
  find "$PROJECT_DIR" -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' \) \
    -not -name '*.test.*' -not -name '*.spec.*' -not -name '*.d.ts' \
    -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/build/*' \
    -not -path '*/__tests__/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    rel="${file#$PROJECT_DIR/}"

    # Use python to extract JSDoc + following signature
    docs=$(python3 -c "
import re, sys

with open(sys.argv[1]) as f:
    content = f.read()

# Match JSDoc blocks followed by export declarations
pattern = r'(/\*\*[\s\S]*?\*/)\s*\n\s*(export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|type|interface|enum)\s+\w+)'
matches = re.findall(pattern, content)

for jsdoc, sig in matches[:15]:
    # Compact the JSDoc
    lines = jsdoc.strip().split('\n')
    if len(lines) > 6:
        lines = lines[:6] + [' * ...', ' */']
    print('  ' + sig.split('{')[0].split('(')[0].strip())
    for l in lines:
        print('    ' + l.strip())
    print()
" "$file" 2>/dev/null || true)

    if [[ -n "$docs" ]]; then
      emit "## $rel" || exit 0
      echo "$docs" | while IFS= read -r line; do
        emit "$line" || exit 0
      done
      emit "" || exit 0
    fi
  done
}

extract_docstrings_go() {
  # Go doc comments: // comments directly above exported functions/types
  find "$PROJECT_DIR" -type f -name '*.go' \
    -not -name '*_test.go' -not -path '*/vendor/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    rel="${file#$PROJECT_DIR/}"

    docs=$(python3 -c "
import re, sys

with open(sys.argv[1]) as f:
    content = f.read()

# Match comment blocks before exported declarations
pattern = r'((?://[^\n]*\n)+)\s*(func [A-Z]\w*|type [A-Z]\w*)'
matches = re.findall(pattern, content)

for comments, sig in matches[:15]:
    lines = comments.strip().split('\n')
    if len(lines) > 6:
        lines = lines[:6] + ['// ...']
    print('  ' + sig)
    for l in lines:
        print('    ' + l.strip())
    print()
" "$file" 2>/dev/null || true)

    if [[ -n "$docs" ]]; then
      emit "## $rel" || exit 0
      echo "$docs" | while IFS= read -r line; do
        emit "$line" || exit 0
      done
      emit "" || exit 0
    fi
  done
}

extract_docstrings_rust() {
  # Rust doc comments: /// before pub items
  find "$PROJECT_DIR" -type f -name '*.rs' \
    -not -path '*/target/*' \
    -print0 2>/dev/null | sort -z | while IFS= read -r -d '' file; do

    rel="${file#$PROJECT_DIR/}"

    docs=$(python3 -c "
import re, sys

with open(sys.argv[1]) as f:
    content = f.read()

pattern = r'((?:///[^\n]*\n)+)\s*(pub (?:fn|struct|enum|trait|type)\s+\w+)'
matches = re.findall(pattern, content)

for comments, sig in matches[:15]:
    lines = comments.strip().split('\n')
    if len(lines) > 6:
        lines = lines[:6] + ['/// ...']
    print('  ' + sig)
    for l in lines:
        print('    ' + l.strip())
    print()
" "$file" 2>/dev/null || true)

    if [[ -n "$docs" ]]; then
      emit "## $rel" || exit 0
      echo "$docs" | while IFS= read -r line; do
        emit "$line" || exit 0
      done
      emit "" || exit 0
    fi
  done
}

case "$LANG" in
  typescript|javascript) extract_docstrings_typescript ;;
  python)                extract_docstrings_python ;;
  go)                    extract_docstrings_go ;;
  rust)                  extract_docstrings_rust ;;
  *)                     emit "(Docstring extraction not supported for $LANG)" || true ;;
esac
