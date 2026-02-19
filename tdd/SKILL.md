---
name: tdd
description: This skill should be used when the user wants to implement features or fix bugs using test-driven development. Enforces the RED-GREEN-REFACTOR cycle with vertical slicing, context isolation between test writing and implementation, human checkpoints, and auto-test feedback loops. Uses multi-agent orchestration with the Task tool for architecturally enforced context isolation. Supports Jest, Vitest, pytest, Go test, cargo test, PHPUnit, and RSpec.
---

# Test-Driven Development — Multi-Agent Orchestration

Enforce disciplined RED-GREEN-REFACTOR cycles using **separate subagents** for test writing and implementation. The core innovation: **the Test Writer never sees implementation code, and the Implementer never sees the specification.** This prevents the LLM from leaking implementation intent into test design.

## When to Use

- User requests TDD, test-first, or red-green-refactor workflow
- User says `/tdd` with a feature description or bug report
- User wants to add a feature with test coverage enforced from the start
- User wants to fix a bug by first writing a reproducing test

## Architecture Overview

```
ORCHESTRATOR (you, reading this file)
├─ Phase 0: Setup — detect framework, extract API, create state file
├─ Phase 1: Decompose into vertical slices → user approves
│
├─ FOR EACH SLICE:
│   ├─ Phase 2 (RED):    Task(Test Writer)  ← spec + API only
│   ├─ Phase 3 (GREEN):  Task(Implementer)  ← failing test + error only
│   └─ Phase 4 (REFACTOR): Task(Refactorer) ← all code + green results
│
└─ Summary
```

### Context Boundaries (the key constraint)

| Agent | Sees | Does NOT See |
|-------|------|-------------|
| **Test Writer** | Slice spec, public API signatures, framework conventions | Implementation code, other slices, implementation plans |
| **Implementer** | Failing test code, test failure output, file tree, existing source | Original spec, slice descriptions, future plans |
| **Refactorer** | All implementation + all tests + green results | Original spec, decomposition rationale |

## Workflow

### Phase 0: Setup (once per session)

**Step 1**: Detect framework and test runner.

```
Check for: package.json (jest/vitest), pyproject.toml/pytest.ini (pytest),
go.mod (go test), Cargo.toml (cargo test), Gemfile (rspec), composer.json (phpunit)
```

If ambiguous, ask: "What command runs your tests? (e.g., `npm test`, `pytest`)"

**Step 2**: Verify green baseline.

```bash
bash ~/.claude/skills/tdd/scripts/run_tests.sh {FRAMEWORK} "{TEST_COMMAND}"
```

Parse the JSON output. If `status` is not `"pass"`, stop: "Existing tests are failing. TDD starts from a green baseline."

**Step 3**: Extract the public API surface.

```bash
bash ~/.claude/skills/tdd/scripts/extract_api.sh {SOURCE_DIR}
```

Save the output — this is what the Test Writer will see.

**Step 4**: Create the state file `.tdd-state.json` in the project root:

```json
{
  "feature": "user's feature description",
  "framework": "jest|vitest|pytest|go|cargo|rspec|phpunit",
  "test_command": "the full test command",
  "source_dir": "src/",
  "slices": [],
  "current_slice": 0,
  "phase": "setup",
  "files_modified": [],
  "test_files_created": []
}
```

This enables `/tdd --resume` to pick up where a previous session left off.

### Phase 1: Specification Decomposition

Take the user's feature request and decompose into **ordered vertical slices**. Each slice is one testable behavior.

Present to the user:

```
I've broken this into N vertical slices:
1. [behavior] — [what the test verifies]
2. [behavior] — [what the test verifies]
...

Each slice follows RED → GREEN → REFACTOR before moving to the next.
Does this decomposition look right?
```

**Wait for user approval.** Update `.tdd-state.json` with the slices array.

---

### Phase 2: RED — Write One Failing Test

**Step 1**: Refresh the API surface (it changes as slices are implemented):

```bash
bash ~/.claude/skills/tdd/scripts/extract_api.sh {SOURCE_DIR}
```

**Step 2**: Read the prompt template from `references/agent_prompts.md` → "Test Writer Agent" section. Construct the prompt by filling in:

- `{SLICE_SPEC}`: The current slice's behavior description
- `{API_SURFACE}`: Output from extract_api.sh
- `{FRAMEWORK}`: Detected framework name
- `{TEST_FILE_PATH}`: Where the test should go (follow project conventions)
- `{EXISTING_TEST_CONTENT}`: Current content of the test file (if it exists)
- `{FRAMEWORK_SKELETON}`: The relevant skeleton from `references/framework_configs.md`

**Step 3**: Launch the Test Writer agent:

```
Task(subagent_type="general-purpose", prompt=<constructed prompt>)
```

**Step 4**: Parse the JSON response. Strip markdown fences if present:
1. Remove leading/trailing whitespace
2. If response starts with `` ```json `` or `` ``` ``, remove first line and last `` ``` ``
3. Parse as JSON
4. If parse fails, find first `{` and last `}`, try that substring

**Step 5**: Write the test code to the test file. If the file exists, append the test function. If new, create with proper imports.

**Step 6**: Run the test to confirm it FAILS:

```bash
bash ~/.claude/skills/tdd/scripts/run_tests.sh {FRAMEWORK} "{TEST_COMMAND_FOR_SPECIFIC_TEST}"
```

The test **MUST fail** (status: `"fail"`). If it passes:
- The behavior already exists, OR
- The test is trivially passing (wrong assertion)
- Investigate before proceeding. Do NOT move to GREEN.

**Step 7**: Present to the user (HUMAN CHECKPOINT):

```
RED: Test written and failing as expected.

Test: {test_name}
File: {test_file_path}
Failure: {failure message from JSON}

This test verifies: {test_description from agent response}

Proceed to GREEN phase? (or adjust the test?)
```

**Wait for user approval before proceeding to GREEN.**

Update `.tdd-state.json`: `"phase": "red"`.

---

### Phase 3: GREEN — Minimal Implementation

**Step 1**: Read the failing test file and the test failure output.

**Step 2**: Build the file tree of source files (not test files, not node_modules, etc.):

```bash
find {SOURCE_DIR} -type f \( -name '*.ts' -o -name '*.js' -o -name '*.py' ... \) | grep -v test | grep -v node_modules | head -50
```

**Step 3**: Read existing source files that the test imports or references.

**Step 4**: Read the prompt template from `references/agent_prompts.md` → "Implementer Agent" section. Fill in:

- `{FAILING_TEST_CODE}`: The complete test file content
- `{TEST_FAILURE_OUTPUT}`: The `raw_tail` from run_tests.sh JSON output
- `{FILE_TREE}`: Source file listing
- `{EXISTING_SOURCE}`: Content of relevant source files

**CRITICAL**: Do NOT include the slice specification, feature description, or any future plans. The Implementer works from the test alone.

**Step 5**: Launch the Implementer agent:

```
Task(subagent_type="general-purpose", prompt=<constructed prompt>)
```

**Step 6**: Parse the JSON response. Apply file changes:
- For `"action": "create"` — use the Write tool
- For `"action": "modify"` — use the Edit tool

**Step 7**: Run the specific test:

```bash
bash ~/.claude/skills/tdd/scripts/run_tests.sh {FRAMEWORK} "{TEST_COMMAND_FOR_SPECIFIC_TEST}"
```

**Step 8**: RETRY LOOP (if test still fails):

```
attempt = 1
while status == "fail" AND attempt <= 5:
    Read the NEW failure output
    Launch a FRESH Task(Implementer) with the updated failure output
    Apply changes
    Re-run test
    attempt += 1

if still failing after 5 attempts:
    Present to user: "Implementation failed after 5 attempts. Last error: {error}"
    Ask: "Adjust the test, try a different approach, or debug manually?"
```

Each retry is a **fresh** Task call — no accumulated context from previous attempts. This prevents the Implementer from going down rabbit holes.

**Step 9**: Once the specific test passes, run the FULL test suite:

```bash
bash ~/.claude/skills/tdd/scripts/run_tests.sh {FRAMEWORK} "{FULL_TEST_COMMAND}" --all
```

If regressions detected, fix them before proceeding.

**Step 10**: Present to the user:

```
GREEN: Test passing with minimal implementation.

Implementation: {explanation from agent response}
Files changed: {list}
All tests: {passed} passing, {failed} failing

Proceed to REFACTOR phase? (or adjust?)
```

Update `.tdd-state.json`: `"phase": "green"`, update `files_modified`.

---

### Phase 4: REFACTOR

**Step 1**: Gather all context:
- All test files created/modified during this session
- All source files modified during this session
- The green test output

**Step 2**: Read the prompt template from `references/agent_prompts.md` → "Refactorer Agent" section. Fill in:

- `{GREEN_TEST_OUTPUT}`: Full test output showing all green
- `{ALL_TEST_CODE}`: Content of all test files
- `{ALL_IMPLEMENTATION_CODE}`: Content of all modified source files

**Step 3**: Launch the Refactorer agent:

```
Task(subagent_type="general-purpose", prompt=<constructed prompt>)
```

**Step 4**: Parse the JSON response. Apply suggestions **one at a time**, in priority order:

For each suggestion:
1. Apply the code change (Edit tool)
2. Run the full test suite
3. If any test fails → **revert immediately** (undo the edit) and skip this suggestion
4. If all tests pass → keep the change

**Step 5**: Present:

```
REFACTOR: Code improved, all tests still passing.

Applied: {list of accepted suggestions}
Skipped: {list of reverted suggestions, if any}
All tests: {count} passing

[Moving to slice N of M] or [All slices complete]
```

Update `.tdd-state.json`: `"phase": "refactor"`.

---

### Phase 5: Next Slice or Complete

If more slices remain → increment `current_slice` in state, return to Phase 2.

If all slices complete → present summary:

```
TDD Complete: {feature name}

Slices implemented: N
Tests written: N
Files created/modified: {list}
All tests passing: yes
```

Clean up: optionally remove `.tdd-state.json` (ask user).

---

## Resume Support

When user invokes `/tdd --resume`:

1. Read `.tdd-state.json` from project root
2. Report current state: "Found TDD session for '{feature}'. Currently at slice {N}/{total}, phase: {phase}."
3. Resume from the current phase of the current slice

---

## Edge Cases

### Bug Fix TDD

1. Write a test demonstrating the bug (should FAIL showing the bug exists)
2. Confirm failure matches the reported bug — human checkpoint
3. Fix: minimal code to make test pass (GREEN phase as normal)
4. Verify: no regressions

### Existing Code (Characterization Tests)

1. Write a test for CURRENT behavior (should PASS — this is a characterization test)
2. Modify the test for DESIRED behavior (should FAIL)
3. Proceed with GREEN → REFACTOR

### User-Provided Tests

If user provides test code:
1. Run to confirm it fails (RED confirmed)
2. Skip to Phase 3 (GREEN) — user-provided tests are authoritative
3. Do not modify without asking

### Flaky Tests

If a test sometimes passes/fails: stop, report, fix the flaky test before continuing.

---

## Anti-Patterns to Avoid

See `references/anti_patterns.md`. Critical ones:
- Never modify a test to make it pass (change implementation, not tests)
- Never write implementation before tests
- Never write all tests at once (vertical slicing)
- Never test implementation details
- Never skip the RED phase

---

## Framework Quick Reference

See `references/framework_configs.md` for setup details.

| Framework | Run single test | Run all | Watch mode |
|-----------|----------------|---------|------------|
| Jest | `npx jest --testPathPattern=<file> -t "<name>"` | `npx jest` | `npx jest --watch` |
| Vitest | `npx vitest run <file> -t "<name>"` | `npx vitest run` | `npx vitest` |
| pytest | `pytest <file>::<test_name> -v` | `pytest -v` | `pytest-watch` |
| Go | `go test -run <TestName> ./...` | `go test ./...` | — |
| Cargo | `cargo test <test_name>` | `cargo test` | `cargo watch -x test` |
| RSpec | `rspec <file>:<line>` | `rspec` | `guard` |
| PHPUnit | `phpunit --filter <test_name>` | `phpunit` | — |
