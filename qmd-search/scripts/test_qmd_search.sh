#!/usr/bin/env bash
# Smoke tests for qmd-search.sh. Requires an indexed `qmd` collection.
# Run: scripts/test_qmd_search.sh   (exit 0 = all pass)
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
W="$HERE/qmd-search.sh"
pass=0; fail=0
ok()   { pass=$((pass+1)); echo "  PASS: $1"; }
bad()  { fail=$((fail+1)); echo "  FAIL: $1"; }

# 1. help exits 0
"$W" -h >/dev/null 2>&1 && ok "help exits 0" || bad "help exits 0"

# 2. empty query errors non-zero
"$W" >/dev/null 2>&1 && bad "empty query should fail" || ok "empty query fails"

# 3. bad mode errors non-zero
"$W" -m bogus "x" >/dev/null 2>&1 && bad "bad mode should fail" || ok "bad mode fails"

# 4. BM25 returns formatted rows for a known term
out="$("$W" -m search -n 3 sensorium 2>/dev/null)"
echo "$out" | grep -qE '^[[:space:]]+[0-9.]+[[:space:]]+[^[:space:]]+\.md' && ok "BM25 returns score+path rows" || bad "BM25 rows ($out)"

# 5. vsearch returns rows
out="$("$W" -m vsearch -n 3 "embodied computing" 2>/dev/null)"
echo "$out" | grep -qE '\.md$' && ok "vsearch returns .md paths" || bad "vsearch rows ($out)"

# 6. json mode emits valid JSON array
out="$("$W" -m vsearch --json -n 1 anxiety 2>/dev/null)"
echo "$out" | head -c1 | grep -q '\[' && ok "json starts with [" || bad "json output ($out)"

# 7. nonsense query gives clean sentinel, not garbage
out="$("$W" -m search "zzqxwz_no_such_token_42" 2>/dev/null)"
echo "$out" | grep -q "no results" && ok "no-results sentinel" || bad "no-results ($out)"

# 8. output has no ANSI escape bytes
out="$("$W" -m vsearch -n 2 "agents" 2>/dev/null)"
printf '%s' "$out" | grep -q $'\x1b' && bad "ANSI leaked into output" || ok "no ANSI escapes"

# 9. -n rejects non-numeric
"$W" -n abc "x" >/dev/null 2>&1 && bad "-n abc should fail" || ok "-n non-numeric fails"

# 10. missing flag value errors, not crash
"$W" -m >/dev/null 2>&1 && bad "dangling -m should fail" || ok "dangling flag fails"

# 11. hybrid (default mode) returns rows and exits 0 despite qmd's teardown abort
out="$("$W" -n 2 "what helps with anxiety" 2>/dev/null)"; rc=$?
{ [ "$rc" -eq 0 ] && echo "$out" | grep -qE '\.md$'; } && ok "hybrid default returns rows, exit 0" || bad "hybrid default (rc=$rc): $out"

# 12. grep mode finds a literal token (auto-detected root) and prints file:line:text
out="$("$W" -m grep -n 3 "sensorium" 2>/dev/null)"
echo "$out" | grep -qE '\.md:[0-9]+:' && ok "grep returns file:line:text" || bad "grep rows ($out)"

# 13. grep mode no-match prints sentinel and exits 0 (not aborted by set -e)
out="$("$W" -m grep "zzqxnowaymatch_42" 2>/dev/null)"; rc=$?
{ [ "$rc" -eq 0 ] && echo "$out" | grep -q "no literal matches"; } && ok "grep no-match sentinel, exit 0" || bad "grep no-match (rc=$rc): $out"

# 14. bad mode name still rejected (now includes grep in allowed set)
"$W" -m frobnicate "x" >/dev/null 2>&1 && bad "bad mode should fail" || ok "bad mode still fails"

# 15. --snippet adds an indented snippet line under a row
out="$("$W" -m search -n 1 --snippet sensorium 2>/dev/null)"
{ echo "$out" | grep -qE '\.md$' && echo "$out" | grep -qE '^         [^ ]'; } && ok "--snippet renders snippet" || bad "--snippet ($out)"

# 16. --min-score validates range
"$W" --min-score 2 "x" >/dev/null 2>&1 && bad "--min-score 2 should fail" || ok "--min-score range validated"

# 17. --min-score rejected for grep mode
"$W" -m grep --min-score 0.5 "x" >/dev/null 2>&1 && bad "grep+min-score should fail" || ok "grep rejects --min-score"

# 18. find mode prints both labeled sections, exit 0, no abort-trap leakage
out="$("$W" -m find -n 2 "sensorium" 2>&1)"; rc=$?
{ [ "$rc" -eq 0 ] \
  && echo "$out" | grep -q "SEMANTIC (hybrid):" \
  && echo "$out" | grep -q "LITERAL (grep" \
  && ! echo "$out" | grep -qi "Abort trap"; } \
  && ok "find: two sections, clean exit" || bad "find ($rc): $out"

echo "----"
echo "passed=$pass failed=$fail"
[ "$fail" -eq 0 ]
