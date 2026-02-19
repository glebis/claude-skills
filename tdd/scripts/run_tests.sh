#!/usr/bin/env bash
# Universal test runner — wraps framework output into structured JSON.
# Usage: run_tests.sh <framework> <test_command> [--all]
#
# Examples:
#   run_tests.sh jest "npx jest src/sum.test.ts"
#   run_tests.sh pytest "pytest tests/test_sum.py -v"
#   run_tests.sh jest "npx jest" --all
#
# Output: single JSON object on stdout:
#   {"status":"pass|fail|error","total":N,"passed":N,"failed":N,
#    "failures":[{"test_name":"...","message":"...","stack":"..."}],
#    "raw_tail":"last 30 lines of output"}

set -euo pipefail

FRAMEWORK="${1:?Usage: run_tests.sh <framework> <test_command> [--all]}"
TEST_CMD="${2:?Usage: run_tests.sh <framework> <test_command> [--all]}"
MODE="${3:-single}"  # --all or single

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

# Run the test command, capture output and exit code
set +e
eval "$TEST_CMD" > "$TMPFILE" 2>&1
EXIT_CODE=$?
set -e

RAW_OUTPUT=$(cat "$TMPFILE")
RAW_TAIL=$(tail -30 "$TMPFILE" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')

# Helper: escape string for JSON
json_escape() {
  printf '%s' "$1" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || \
  printf '"%s"' "$(printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g' | tr '\n' ' ')"
}

# Parse based on framework
parse_jest_vitest() {
  local total=0 passed=0 failed=0 failures="[]"

  # Jest/Vitest summary line: "Tests: N failed, N passed, N total"
  local summary_line
  summary_line=$(grep -E '(Tests|Test Suites):.*total' "$TMPFILE" | tail -1 || true)

  if [[ -n "$summary_line" ]]; then
    total=$(echo "$summary_line" | grep -oE '[0-9]+ total' | grep -oE '[0-9]+' || echo 0)
    passed=$(echo "$summary_line" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
    failed=$(echo "$summary_line" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)
  fi

  # Extract failure details
  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json, sys

text = open('$TMPFILE').read()
# Match FAIL blocks with test name and error
pattern = r'● (.+?)(?:\n\n|\n\s*\n)([\s\S]*?)(?=\n\s*●|\n\s*Test Suites:|\Z)'
matches = re.findall(pattern, text)
results = []
for name, body in matches[:10]:
    msg_lines = body.strip().split('\n')
    msg = msg_lines[0] if msg_lines else ''
    stack = '\n'.join(msg_lines[1:4]) if len(msg_lines) > 1 else ''
    results.append({'test_name': name.strip(), 'message': msg.strip(), 'stack': stack.strip()})

# Fallback: look for 'FAIL' lines
if not results:
    for line in text.split('\n'):
        if line.strip().startswith('FAIL'):
            results.append({'test_name': line.strip(), 'message': 'See raw output', 'stack': ''})

print(json.dumps(results))
" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"
  [[ "$total" -eq 0 && "$EXIT_CODE" -ne 0 ]] && status="error"

  printf '{"status":"%s","total":%d,"passed":%d,"failed":%d,"failures":%s,"raw_tail":"%s"}\n' \
    "$status" "$total" "$passed" "$failed" "$failures" "$RAW_TAIL"
}

parse_pytest() {
  local total=0 passed=0 failed=0 failures="[]"

  # pytest summary: "N passed, N failed" or "N passed"
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
import re, json

text = open('$TMPFILE').read()
pattern = r'FAILED (.+?)(?:\s*-\s*(.+))?$'
results = []
for m in re.finditer(pattern, text, re.MULTILINE):
    name = m.group(1).strip()
    msg = m.group(2).strip() if m.group(2) else 'See raw output'
    results.append({'test_name': name, 'message': msg, 'stack': ''})

# Also capture assertion errors
if not results:
    pattern2 = r'___+ (.+?) ___+\n([\s\S]*?)(?=___+|\Z)'
    for m in re.finditer(pattern2, text):
        name = m.group(1).strip()
        body = m.group(2).strip().split('\n')
        msg = next((l for l in body if 'assert' in l.lower() or 'Error' in l), body[0] if body else '')
        results.append({'test_name': name, 'message': msg.strip(), 'stack': ''})

print(json.dumps(results[:10]))
" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"
  [[ "$total" -eq 0 && "$EXIT_CODE" -ne 0 ]] && status="error"

  printf '{"status":"%s","total":%d,"passed":%d,"failed":%d,"failures":%s,"raw_tail":"%s"}\n' \
    "$status" "$total" "$passed" "$failed" "$failures" "$RAW_TAIL"
}

parse_go() {
  local total=0 passed=0 failed=0 failures="[]"

  passed=$(grep -cE '^--- PASS:' "$TMPFILE" || echo 0)
  failed=$(grep -cE '^--- FAIL:' "$TMPFILE" || echo 0)
  total=$((passed + failed))

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json

text = open('$TMPFILE').read()
results = []
for m in re.finditer(r'^--- FAIL: (\S+)', text, re.MULTILINE):
    name = m.group(1)
    # Grab lines between this FAIL and next --- or end
    start = m.end()
    end_match = re.search(r'^---', text[start:], re.MULTILINE)
    block = text[start:start + end_match.start()] if end_match else text[start:start+500]
    lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
    msg = lines[0] if lines else 'See raw output'
    results.append({'test_name': name, 'message': msg, 'stack': ''})
print(json.dumps(results[:10]))
" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"
  [[ "$total" -eq 0 && "$EXIT_CODE" -ne 0 ]] && status="error"

  printf '{"status":"%s","total":%d,"passed":%d,"failed":%d,"failures":%s,"raw_tail":"%s"}\n' \
    "$status" "$total" "$passed" "$failed" "$failures" "$RAW_TAIL"
}

parse_cargo() {
  local total=0 passed=0 failed=0 failures="[]"

  # "test result: ok. N passed; N failed; N ignored"
  local summary_line
  summary_line=$(grep -E '^test result:' "$TMPFILE" | tail -1 || true)

  if [[ -n "$summary_line" ]]; then
    passed=$(echo "$summary_line" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo 0)
    failed=$(echo "$summary_line" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo 0)
    total=$((passed + failed))
  fi

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json

text = open('$TMPFILE').read()
results = []
for m in re.finditer(r\"^---- (.+?) stdout ----\n([\s\S]*?)(?=^----|\Z)\", text, re.MULTILINE):
    name = m.group(1).strip()
    body = m.group(2).strip().split('\n')
    msg = next((l for l in body if 'panicked' in l or 'assert' in l), body[0] if body else '')
    results.append({'test_name': name, 'message': msg.strip(), 'stack': ''})
print(json.dumps(results[:10]))
" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"
  [[ "$total" -eq 0 && "$EXIT_CODE" -ne 0 ]] && status="error"

  printf '{"status":"%s","total":%d,"passed":%d,"failed":%d,"failures":%s,"raw_tail":"%s"}\n' \
    "$status" "$total" "$passed" "$failed" "$failures" "$RAW_TAIL"
}

parse_rspec() {
  local total=0 passed=0 failed=0 failures="[]"

  # "N examples, N failures"
  local summary_line
  summary_line=$(grep -E '[0-9]+ examples' "$TMPFILE" | tail -1 || true)

  if [[ -n "$summary_line" ]]; then
    total=$(echo "$summary_line" | grep -oE '[0-9]+ examples' | grep -oE '[0-9]+' || echo 0)
    failed=$(echo "$summary_line" | grep -oE '[0-9]+ failures?' | grep -oE '[0-9]+' || echo 0)
    passed=$((total - failed))
  fi

  if [[ "$failed" -gt 0 ]] || [[ "$EXIT_CODE" -ne 0 ]]; then
    failures=$(python3 -c "
import re, json

text = open('$TMPFILE').read()
results = []
for m in re.finditer(r'^\s+\d+\) (.+?)\n\s+Failure/Error: (.+?)$', text, re.MULTILINE):
    results.append({'test_name': m.group(1).strip(), 'message': m.group(2).strip(), 'stack': ''})
print(json.dumps(results[:10]))
" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"

  printf '{"status":"%s","total":%d,"passed":%d,"failed":%d,"failures":%s,"raw_tail":"%s"}\n' \
    "$status" "$total" "$passed" "$failed" "$failures" "$RAW_TAIL"
}

parse_phpunit() {
  local total=0 passed=0 failed=0 failures="[]"

  # "OK (N tests, N assertions)" or "FAILURES! Tests: N, Assertions: N, Failures: N"
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
import re, json

text = open('$TMPFILE').read()
results = []
for m in re.finditer(r'^\d+\) (.+?)$\n(.+?)$', text, re.MULTILINE):
    results.append({'test_name': m.group(1).strip(), 'message': m.group(2).strip(), 'stack': ''})
print(json.dumps(results[:10]))
" 2>/dev/null || echo '[]')
  fi

  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"

  printf '{"status":"%s","total":%d,"passed":%d,"failed":%d,"failures":%s,"raw_tail":"%s"}\n' \
    "$status" "$total" "$passed" "$failed" "$failures" "$RAW_TAIL"
}

# Generic fallback for unknown frameworks
parse_generic() {
  local status="pass"
  [[ "$EXIT_CODE" -ne 0 ]] && status="fail"

  printf '{"status":"%s","total":0,"passed":0,"failed":0,"failures":[],"raw_tail":"%s"}\n' \
    "$status" "$RAW_TAIL"
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
