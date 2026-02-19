---
name: tdd
description: This skill should be used when the user wants to implement features or fix bugs using test-driven development. Enforces the RED-GREEN-REFACTOR cycle with vertical slicing, context isolation between test writing and implementation, human checkpoints, and auto-test feedback loops. Supports Jest, Vitest, pytest, Go test, cargo test, PHPUnit, and RSpec.
---

# Test-Driven Development

Enforce disciplined RED-GREEN-REFACTOR cycles where tests are written before implementation, one vertical slice at a time. The core constraint: **no implementation code exists without a corresponding failing test written first.**

## When to Use

- User requests TDD, test-first, or red-green-refactor workflow
- User says `/tdd` with a feature description or bug report
- User wants to add a feature with test coverage enforced from the start
- User wants to fix a bug by first writing a reproducing test

## Core Principles

1. **Vertical slicing** -- one failing test, then minimal implementation to pass it, then refactor. Never write all tests first.
2. **Context isolation** -- when writing a test, reason only from the specification/requirement, not from a planned implementation. This prevents tests that mirror implementation details.
3. **Test public interfaces** -- test behavior through public APIs and return values. Avoid testing internal implementation, mocking internals, or verifying call counts on private methods.
4. **Human checkpoints** -- present the failing test to the user for approval before writing implementation. The user is the arbiter of test correctness.
5. **Auto-test feedback loop** -- after writing implementation, run the test immediately. If it fails, iterate. If it passes, present for refactoring.

## Workflow

### Phase 0: Setup (once per session)

Detect the project's test framework and runner:

```
Project detection checklist:
- package.json → jest, vitest, mocha, playwright
- pyproject.toml / setup.cfg / pytest.ini → pytest
- go.mod → go test
- Cargo.toml → cargo test
- composer.json → phpunit
- Gemfile → rspec
```

Determine the test command. If ambiguous, ask the user:
"What command runs your tests? (e.g., `npm test`, `pytest`, `go test ./...`)"

Store the test command for the session. Check if tests currently pass:

```bash
<TEST_COMMAND>
```

If existing tests fail, stop and report. TDD starts from a green baseline.

### Phase 1: Specification Decomposition

Take the user's feature request or bug report and decompose it into **ordered vertical slices**. Each slice is one testable behavior.

Present the slices to the user:

```
I've broken this into N vertical slices:
1. [behavior description] -- [what the test would verify]
2. [behavior description] -- [what the test would verify]
...

Each slice follows RED -> GREEN -> REFACTOR before moving to the next.
Does this decomposition look right?
```

Wait for user approval. Adjust if needed.

### Phase 2: RED -- Write One Failing Test

**Critical constraint**: When writing the test, reason ONLY from the specification for this slice. Do not plan or think about the implementation.

Write exactly one test that:
- Tests a single behavior from the current slice
- Uses the public interface (function signatures, API endpoints, component props)
- Has a descriptive name that reads as a behavior specification
- Contains clear assertions on expected outcomes
- Will FAIL because the implementation does not yet exist

**Test naming convention**: `test_<behavior_in_plain_english>` or `it("should <behavior>")` or `Test<Behavior>`.

Run the test to confirm it fails:

```bash
<TEST_COMMAND> <specific_test_file_or_filter>
```

**The test MUST fail.** If it passes, the behavior already exists or the test is wrong. Investigate before proceeding.

Present the failing test and output to the user:

```
RED: Test written and failing as expected.

Test: <test name>
File: <test file path>
Failure: <failure message summary>

This test verifies: <what behavior this proves>

Proceed to GREEN phase? (or adjust the test?)
```

Wait for user approval.

### Phase 3: GREEN -- Minimal Implementation

Write the **minimum code** to make the failing test pass. Constraints:

- No code beyond what the test requires
- No premature abstractions
- No error handling for untested cases
- No optimization
- Hardcoded values are acceptable if they satisfy the test

Run the test:

```bash
<TEST_COMMAND> <specific_test_file_or_filter>
```

**If the test fails**: Read the error, adjust the implementation, re-run. Repeat up to 5 times. If still failing after 5 attempts, present the situation to the user -- the test may need adjustment.

**If the test passes**: Run the FULL test suite to check for regressions:

```bash
<TEST_COMMAND>
```

If regressions detected, fix them before proceeding.

Present the result:

```
GREEN: Test passing with minimal implementation.

Implementation: <brief description of what was written>
Files changed: <list>
All tests: <pass count> passing, <fail count> failing

Proceed to REFACTOR phase? (or adjust?)
```

### Phase 4: REFACTOR

With all tests green, improve code quality without changing behavior:

- Extract duplicated code
- Improve naming
- Simplify logic
- Apply appropriate patterns

**After every refactoring change**, re-run the full test suite:

```bash
<TEST_COMMAND>
```

If any test fails during refactoring, revert the change immediately and try a different approach.

Present the result:

```
REFACTOR: Code improved, all tests still passing.

Changes: <what was refactored>
All tests: <pass count> passing

[If more slices remain]: Moving to slice N of M.
[If all slices complete]: All slices implemented. TDD cycle complete.
```

### Phase 5: Next Slice or Complete

If more slices remain, return to Phase 2 with the next slice.

If all slices are complete, present a summary:

```
TDD Complete: <feature/fix name>

Slices implemented: N
Tests written: N
Files created/modified: <list>
All tests passing: yes

Test coverage for new code: <if coverage tool available>
```

## Edge Cases

### Bug Fix TDD

For bug fixes, the workflow adjusts:

1. **Reproduce first**: Write a test that demonstrates the bug (it should FAIL showing the bug exists)
2. **Confirm the failure matches the reported bug** -- human checkpoint
3. **Fix**: Write minimal code to make the test pass
4. **Verify**: Ensure no regressions

### Adding Tests to Existing Code (Characterization Tests)

When adding TDD to code that already exists:

1. Write a test for the CURRENT behavior (it should PASS)
2. This is a "characterization test" -- it documents what the code does now
3. Then modify the test for the DESIRED behavior (it should FAIL)
4. Proceed with normal GREEN -> REFACTOR

### When the User Writes Tests

If the user provides test code:

1. Run it to confirm it fails (RED confirmed)
2. Skip to Phase 3 (GREEN)
3. User-provided tests are authoritative -- do not modify them without asking

### Flaky Tests

If a test sometimes passes and sometimes fails:

1. Stop the TDD cycle
2. Report the flakiness to the user
3. Fix the flaky test before continuing (flaky tests poison TDD)

## Anti-Patterns to Avoid

See `references/anti_patterns.md` for the full list. Critical ones:

- **Never modify a test to make it pass** -- change implementation, not tests (unless the test is genuinely wrong, confirmed with user)
- **Never write implementation before tests** -- if implementation code was written first, delete it and start over
- **Never write all tests at once** -- one test per cycle (vertical slicing)
- **Never test implementation details** -- no mocking internal methods, no asserting private state
- **Never skip the RED phase** -- every test must be seen failing before implementation

## Framework Quick Reference

See `references/framework_configs.md` for setup details per framework.

| Framework | Run single test | Run all | Watch mode |
|-----------|----------------|---------|------------|
| Jest | `npx jest --testPathPattern=<file> -t "<name>"` | `npx jest` | `npx jest --watch` |
| Vitest | `npx vitest run <file> -t "<name>"` | `npx vitest run` | `npx vitest` |
| pytest | `pytest <file>::<test_name> -v` | `pytest -v` | `pytest-watch` |
| Go | `go test -run <TestName> ./...` | `go test ./...` | -- |
| Cargo | `cargo test <test_name>` | `cargo test` | `cargo watch -x test` |
| RSpec | `rspec <file>:<line>` | `rspec` | `guard` |
| PHPUnit | `phpunit --filter <test_name>` | `phpunit` | -- |

## Session Memory

After completing a TDD session, note patterns that emerged:
- Which slices were too large and needed further decomposition
- Whether the test framework needed special configuration
- Any anti-patterns that crept in and how they were caught
