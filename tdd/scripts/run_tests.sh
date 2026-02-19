#!/usr/bin/env bash
# Universal test runner — wraps framework output into structured JSON.
# Usage: run_tests.sh <framework> <test_command> [--all] [--timeout <seconds>]
#
# Examples:
#   run_tests.sh jest "npx jest src/sum.test.ts"
#   run_tests.sh pytest "pytest tests/test_sum.py -v"
#   run_tests.sh jest "npx jest" --all
#   run_tests.sh jest "npx jest" --timeout 120
#
# Output: single JSON object on stdout:
#   {"status":"pass|fail|error","total":N,"passed":N,"failed":N,
#    "failures":[{"test_name":"...","message":"...","stack":"..."}],
#    "raw_tail":"last 30 lines of output"}
#
# Status values:
#   pass  — all tests passed (exit 0)
#   fail  — one or more tests failed (exit non-zero, parseable output)
#   error — script/compilation/infra error (exit non-zero, no parseable test results)

set -uo pipefail
# NOTE: intentionally NOT using set -e. Parsing steps may fail on unexpected
# output formats; we always want to produce JSON, even degraded.

FRAMEWORK="${1:?Usage: run_tests.sh <framework> <test_command> [--all] [--timeout <seconds>]}"
TEST_CMD="${2:?Usage: run_tests.sh <framework> <test_command> [--all] [--timeout <seconds>]}"

shift 2
TIMEOUT=300  # default 5 minutes
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) shift ;;  # informational only, doesn't change behavior
    --timeout) TIMEOUT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

# Run the test command with timeout, capture output and exit code
EXIT_CODE=0
if command -v timeout &>/dev/null; then
  timeout "$TIMEOUT" bash -c "$TEST_CMD" > "$TMPFILE" 2>&1 || EXIT_CODE=$?
elif command -v gtimeout &>/dev/null; then
  gtimeout "$TIMEOUT" bash -c "$TEST_CMD" > "$TMPFILE" 2>&1 || EXIT_CODE=$?
else
  # No timeout command available — run directly
  bash -c "$TEST_CMD" > "$TMPFILE" 2>&1 || EXIT_CODE=$?
fi

# Exit code 124 = timeout killed the process
if [[ "$EXIT_CODE" -eq 124 ]]; then
  echo '{"status":"error","total":0,"passed":0,"failed":0,"failures":[{"test_name":"TIMEOUT","message":"Test command exceeded '"$TIMEOUT"'s timeout","stack":""}],"raw_tail":"killed by timeout after '"$TIMEOUT"' seconds"}'
  exit 0
fi

# Escape raw_tail safely via python3 (handles all JSON-special chars)
RAW_TAIL=$(tail -30 "$TMPFILE" | python3 -c '
import sys, json
text = sys.stdin.read()
# json.dumps produces a quoted string with all escaping handled
print(json.dumps(text))
' 2>/dev/null || echo '"(could not read output)"')
# RAW_TAIL is now a JSON-quoted string like "\"line1\\nline2\""

# Emit valid JSON. Uses python3 for safe assembly to avoid printf % issues.
emit_json() {
  local status="$1" total="$2" passed="$3" failed="$4" failures="$5"
  python3 -c "
import json, sys
obj = {
    'status': sys.argv[1],
    'total': int(sys.argv[2]),
    'passed': int(sys.argv[3]),
    'failed': int(sys.argv[4]),
    'failures': json.loads(sys.argv[5]),
    'raw_tail': json.loads(sys.argv[6])
}
print(json.dumps(obj))
" "$status" "$total" "$passed" "$failed" "$failures" "$RAW_TAIL" 2>/dev/null || \
  echo '{"status":"error","total":0,"passed":0,"failed":0,"failures":[],"raw_tail":"JSON assembly failed"}'
}

# Parse based on framework
parse_jest_vitest() {
  local total=0 passed=0 failed=0 failures="[]"

  local summary_line
  summary_line=$(grep -E '(Tests|Test Suites):.*total' "$TMPFILE" | tail -1 || true)

  if [[ -n "$summary_line" ]]; then
    total=$(echo "$summary_line" | grep -oE '[0-9]+ total' | grep -oE '[0-9]+' || echo 0)
    passed=$(echo "$summary_line" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
    failed=$(echo "$summary_line" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)
  fi

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json, sys

text = open(sys.argv[1]).read()
pattern = r'● (.+?)(?:\n\n|\n\s*\n)([\s\S]*?)(?=\n\s*●|\n\s*Test Suites:|\Z)'
matches = re.findall(pattern, text)
results = []
for name, body in matches[:10]:
    msg_lines = body.strip().split('\n')
    msg = msg_lines[0] if msg_lines else ''
    stack = '\n'.join(msg_lines[1:4]) if len(msg_lines) > 1 else ''
    results.append({'test_name': name.strip(), 'message': msg.strip(), 'stack': stack.strip()})

if not results:
    for line in text.split('\n'):
        if line.strip().startswith('FAIL'):
            results.append({'test_name': line.strip(), 'message': 'See raw output', 'stack': ''})

print(json.dumps(results))
" "$TMPFILE" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"
  [[ "$total" -eq 0 && "$EXIT_CODE" -ne 0 ]] && status="error"

  emit_json "$status" "$total" "$passed" "$failed" "$failures"
}

parse_pytest() {
  local total=0 passed=0 failed=0 failures="[]"

  local summary_line
  summary_line=$(grep -E '=+ .*(passed|failed|error).*=+' "$TMPFILE" | tail -1 || true)

  if [[ -n "$summary_line" ]]; then
    passed=$(echo "$summary_line" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
    failed=$(echo "$summary_line" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)
    local errors
    errors=$(echo "$summary_line" | grep -oE '[0-9]+ error' | grep -oE '[0-9]+' || echo 0)
    total=$((passed + failed + errors))
  fi

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json, sys

text = open(sys.argv[1]).read()
pattern = r'FAILED (.+?)(?:\s*-\s*(.+))?$'
results = []
for m in re.finditer(pattern, text, re.MULTILINE):
    name = m.group(1).strip()
    msg = m.group(2).strip() if m.group(2) else 'See raw output'
    results.append({'test_name': name, 'message': msg, 'stack': ''})

if not results:
    pattern2 = r'___+ (.+?) ___+\n([\s\S]*?)(?=___+|\Z)'
    for m in re.finditer(pattern2, text):
        name = m.group(1).strip()
        body = m.group(2).strip().split('\n')
        msg = next((l for l in body if 'assert' in l.lower() or 'Error' in l), body[0] if body else '')
        results.append({'test_name': name, 'message': msg.strip(), 'stack': ''})

print(json.dumps(results[:10]))
" "$TMPFILE" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"
  [[ "$total" -eq 0 && "$EXIT_CODE" -ne 0 ]] && status="error"

  emit_json "$status" "$total" "$passed" "$failed" "$failures"
}

parse_go() {
  local total=0 passed=0 failed=0 failures="[]"

  passed=$(grep -cE '^--- PASS:' "$TMPFILE" || echo 0)
  failed=$(grep -cE '^--- FAIL:' "$TMPFILE" || echo 0)
  total=$((passed + failed))

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json, sys

text = open(sys.argv[1]).read()
results = []
for m in re.finditer(r'^--- FAIL: (\S+)', text, re.MULTILINE):
    name = m.group(1)
    start = m.end()
    end_match = re.search(r'^---', text[start:], re.MULTILINE)
    block = text[start:start + end_match.start()] if end_match else text[start:start+500]
    lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
    msg = lines[0] if lines else 'See raw output'
    results.append({'test_name': name, 'message': msg, 'stack': ''})
print(json.dumps(results[:10]))
" "$TMPFILE" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"
  [[ "$total" -eq 0 && "$EXIT_CODE" -ne 0 ]] && status="error"

  emit_json "$status" "$total" "$passed" "$failed" "$failures"
}

parse_cargo() {
  local total=0 passed=0 failed=0 failures="[]"

  local summary_line
  summary_line=$(grep -E '^test result:' "$TMPFILE" | tail -1 || true)

  if [[ -n "$summary_line" ]]; then
    passed=$(echo "$summary_line" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
    failed=$(echo "$summary_line" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)
    total=$((passed + failed))
  fi

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json, sys

text = open(sys.argv[1]).read()
results = []
for m in re.finditer(r'^---- (.+?) stdout ----\n([\s\S]*?)(?=^----|\Z)', text, re.MULTILINE):
    name = m.group(1).strip()
    body = m.group(2).strip().split('\n')
    msg = next((l for l in body if 'panicked' in l or 'assert' in l), body[0] if body else '')
    results.append({'test_name': name, 'message': msg.strip(), 'stack': ''})
print(json.dumps(results[:10]))
" "$TMPFILE" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"
  [[ "$total" -eq 0 && "$EXIT_CODE" -ne 0 ]] && status="error"

  emit_json "$status" "$total" "$passed" "$failed" "$failures"
}

parse_rspec() {
  local total=0 passed=0 failed=0 failures="[]"

  local summary_line
  summary_line=$(grep -E '[0-9]+ examples' "$TMPFILE" | tail -1 || true)

  if [[ -n "$summary_line" ]]; then
    total=$(echo "$summary_line" | grep -oE '[0-9]+ examples' | grep -oE '[0-9]+' || echo 0)
    failed=$(echo "$summary_line" | grep -oE '[0-9]+ failures?' | grep -oE '[0-9]+' || echo 0)
    passed=$((total - failed))
  fi

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json, sys

text = open(sys.argv[1]).read()
results = []
for m in re.finditer(r'^\s+\d+\) (.+?)\n\s+Failure/Error: (.+?)$', text, re.MULTILINE):
    results.append({'test_name': m.group(1).strip(), 'message': m.group(2).strip(), 'stack': ''})
print(json.dumps(results[:10]))
" "$TMPFILE" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"

  emit_json "$status" "$total" "$passed" "$failed" "$failures"
}

parse_phpunit() {
  local total=0 passed=0 failed=0 failures="[]"

  if grep -qE '^OK \(' "$TMPFILE"; then
    total=$(grep -oE 'OK \([0-9]+ tests' "$TMPFILE" | grep -oE '[0-9]+' || echo 0)
    passed=$total
  elif grep -qE 'Tests: [0-9]+' "$TMPFILE"; then
    total=$(grep -oE 'Tests: [0-9]+' "$TMPFILE" | grep -oE '[0-9]+' || echo 0)
    failed=$(grep -oE 'Failures: [0-9]+' "$TMPFILE" | grep -oE '[0-9]+' || echo 0)
    passed=$((total - failed))
  fi

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json, sys

text = open(sys.argv[1]).read()
results = []
for m in re.finditer(r'^\d+\) (.+?)$\n(.+?)$', text, re.MULTILINE):
    results.append({'test_name': m.group(1).strip(), 'message': m.group(2).strip(), 'stack': ''})
print(json.dumps(results[:10]))
" "$TMPFILE" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"

  emit_json "$status" "$total" "$passed" "$failed" "$failures"
}

# Generic fallback for unknown frameworks
parse_generic() {
  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"

  emit_json "$status" "0" "0" "0" "[]"
}

# Dispatch
case "$FRAMEWORK" in
  jest|vitest)   parse_jest_vitest ;;
  pytest)        parse_pytest ;;
  go)            parse_go ;;
  cargo)         parse_cargo ;;
  rspec)         parse_rspec ;;
  phpunit)       parse_phpunit ;;
  *)             parse_generic ;;
esac
