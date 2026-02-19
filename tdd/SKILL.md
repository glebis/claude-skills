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

## Invocation Modes

| Invocation | Behavior |
|-----------|----------|
| `/tdd <feature>` | Interactive mode — pause for approval at slices and each RED checkpoint |
| `/tdd --auto <feature>` | Autonomous mode — run all slices without pausing; stop ONLY on unrecoverable errors |
| `/tdd --resume` | Resume from `.tdd-state.json` in project root |

In `--auto` mode, skip all `[HUMAN CHECKPOINT]` steps. Print status lines instead:

```
[auto] RED  slice 1/4: "validates email format" — test failing as expected
[auto] GREEN slice 1/4: passing (attempt 1)
[auto] REFACTOR slice 1/4: 1 suggestion applied, 0 skipped
```

Stop and ask the user ONLY when:
- Implementation fails after 5 attempts
- Regressions cannot be auto-fixed after 3 attempts
- A script error makes it impossible to continue (missing binary, permission denied, etc.)

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
| **Test Writer** | Slice spec, public API signatures, framework conventions, layer constraints | Implementation code, other slices, implementation plans |
| **Implementer** | Failing test code, test failure output, file tree, existing source, layer constraints | Original spec, slice descriptions, future plans |
| **Refactorer** | All implementation + all tests + green results, layers touched | Original spec, decomposition rationale |

## Workflow

### Phase 0: Setup (once per session)

**Step 1**: Detect framework and test runner.

```
Check for: package.json (jest/vitest), pyproject.toml/pytest.ini (pytest),
go.mod (go test), Cargo.toml (cargo test), Gemfile (rspec), composer.json (phpunit)
```

If ambiguous, ask: "What command runs your tests? (e.g., `npm test`, `pytest`)"

**Step 2**: Detect language from source files (for agent prompts):

```
TypeScript (.ts/.tsx), JavaScript (.js/.jsx), Python (.py), Go (.go), Rust (.rs), Ruby (.rb), PHP (.php)
```

**Step 3**: Verify green baseline.

```bash
bash ~/.claude/skills/tdd/scripts/run_tests.sh {FRAMEWORK} "{TEST_COMMAND}"
```

Parse the JSON output.

- If `status` is `"pass"`: proceed.
- If `status` is `"fail"`: stop — "Existing tests are failing. TDD starts from a green baseline."
- If `status` is `"error"` AND `total` is 0: **greenfield project** — no tests exist yet. This is fine. Proceed.

**Step 4**: Extract the public API surface.

```bash
bash ~/.claude/skills/tdd/scripts/extract_api.sh {SOURCE_DIR}
```

Save the output — this is what the Test Writer will see. If empty (greenfield), that's expected.

**Step 5**: Create the state file `.tdd-state.json` in the project root:

```json
{
  "feature": "user's feature description",
  "framework": "jest|vitest|pytest|go|cargo|rspec|phpunit",
  "language": "typescript|javascript|python|go|rust|ruby|php",
  "test_command": "the full test command",
  "source_dir": "src/",
  "auto_mode": false,
  "slices": [],
  "current_slice": 0,
  "phase": "setup",
  "layer_map": {},
  "files_modified": [],
  "test_files_created": []
}
```

Each slice in the `slices` array includes a `layer` field: `"domain"`, `"domain-service"`, `"application"`, or `"infrastructure"`. See Phase 1 for how layers are assigned.

The `layer_map` maps directory prefixes to layers. Built during Phase 1 from project structure:

```json
{
  "layer_map": {
    "src/domain/": "domain",
    "src/services/": "domain-service",
    "src/application/": "application",
    "src/infrastructure/": "infrastructure",
    "src/adapters/": "infrastructure",
    "src/controllers/": "infrastructure"
  }
}
```

If the project has no clear directory-layer mapping (flat structure), set `layer_map` to `{}` and skip path-based validation.

**Step 5a** (auto-detect layer_map): If `layer_map` is empty, scan the source directory for common DDD/layered architecture directory names and auto-populate:

```
Common directory → layer mappings (check if directories exist):
  */domain/       → "domain"
  */models/       → "domain"          (ORM models often serve as domain entities)
  */entities/     → "domain"
  */value_objects/ → "domain"
  */services/     → "application"     (unless clearly infrastructure)
  */application/  → "application"
  */use_cases/    → "application"
  */core/         → "application"
  */infrastructure/ → "infrastructure"
  */adapters/     → "infrastructure"
  */controllers/  → "infrastructure"
  */api/          → "infrastructure"
  */bot/          → "infrastructure"  (Telegram/Discord bot handlers)
  */handlers/     → "infrastructure"
  */repositories/ → "infrastructure"  (concrete repo implementations)
```

Only add entries for directories that actually exist in the source tree. If fewer than 2 directories match, leave `layer_map` empty (flat project). Present the auto-detected map to the user for confirmation:

```
Auto-detected layer map from directory structure:
  src/models/     → domain
  src/services/   → application
  src/core/       → application
  src/bot/        → infrastructure
  src/api/        → infrastructure

Does this mapping look correct? (adjust if needed)
```

**Update state**: `"phase": "setup"`. Write state file immediately.

---

### Phase 1: Specification Decomposition

Take the user's feature request and decompose into **ordered vertical slices**. Each slice is one testable behavior.

#### Inside-Out Slice Ordering

After identifying all slices, **sort them inside-out by architectural layer**. This ensures each slice can build on real (not mocked) implementations from previous slices:

1. **Domain model** slices first — pure logic, no dependencies, no mocks needed
2. **Domain service** slices — cross-aggregate operations using real domain objects
3. **Application service / use case** slices — orchestration using in-memory fakes for ports
4. **Infrastructure adapter** slices last — repos, external APIs, framework adapters

Assign each slice a `layer` tag: `domain`, `domain-service`, `application`, or `infrastructure`. Use the heuristics from `references/layer_guide.md` to classify.

**Why inside-out?** Domain slices produce real objects that later slices use directly. This minimizes mocking and catches integration issues early. It also ensures business rules are implemented and tested before any infrastructure decisions are made.

For simple projects where all code lives in one layer, all slices get `layer: "application"` and the ordering doesn't change — the guidance degrades gracefully.

#### Edge Cases in Slice Ordering

**Infrastructure-only features** (e.g., "add email provider retry logic", "switch from Postgres to MySQL"):
- If a feature has NO domain or application behavior changes, all slices may be `infrastructure`. This is valid — skip the inner layers entirely.
- Present as: "This is a pure infrastructure change. All slices are infrastructure-layer."

**Missing port interface** (domain-service needs a port that doesn't exist yet):
- The first slice that needs the port should create the interface as part of its implementation. The Implementer is allowed to create files in inner layers (domain/domain-service can define their own ports).
- Example: a `domain-service` slice for `RegistrationService` creates `domain/ports/UserRepository` interface as part of GREEN.

**Cross-cutting slices** (a slice touches multiple layers):
- Tag with the INNERMOST layer it touches. The Implementer may create files in that layer and any inner layers.
- Example: a use case that also introduces a new domain event is tagged `application` but creates a file in `domain/events/`.

Present to the user:

```
I've broken this into N vertical slices (ordered inside-out):

Domain:
1. [behavior] — [what the test verifies]

Domain Services:
2. [behavior] — [what the test verifies]

Application:
3. [behavior] — [what the test verifies]

Infrastructure:
4. [behavior] — [what the test verifies]

Each slice follows RED -> GREEN -> REFACTOR before moving to the next.
Does this decomposition look right?
```

If all slices fall in one layer, skip the layer headings and present as a flat list.

**Wait for user approval** (even in `--auto` mode — slice decomposition always needs sign-off).

**Update state**: Write slices array (each with `layer` field), set `"phase": "decomposed"`.

---

### Phase 2: RED — Write One Failing Test

**Step 1**: Refresh the API surface (it changes as slices are implemented):

```bash
bash ~/.claude/skills/tdd/scripts/extract_api.sh {SOURCE_DIR}
```

**Step 2**: Read the prompt template from `references/agent_prompts.md` -> "Test Writer Agent" section. Construct the prompt by filling in:

- `{SLICE_SPEC}`: The current slice's behavior description
- `{LANGUAGE}`: Detected language from Phase 0
- `{FRAMEWORK}`: Detected framework name
- `{API_SURFACE}`: Output from extract_api.sh
- `{TEST_FILE_PATH}`: Where the test should go (follow project conventions)
- `{EXISTING_TEST_CONTENT}`: Current content of the test file (if it exists), or "No test file exists yet."
- `{FRAMEWORK_SKELETON}`: The relevant skeleton from `references/framework_configs.md`
- `{LAYER}`: The slice's layer tag from Phase 1
- `{LAYER_TEST_CONSTRAINTS}`: Layer-specific test constraints (see agent_prompts.md -> Layer-Specific Constraint Lookup)

**Step 3**: Launch the Test Writer agent:

```
Task(subagent_type="general-purpose", prompt=<constructed prompt>)
```

**Step 4**: Parse the JSON response using the `parse_agent_json` logic from `agent_prompts.md`:
1. Strip markdown fences if present
2. Try direct JSON parse
3. If that fails, find first `{` and last `}`, try that substring
4. If still invalid: retry the Task call once with appended "Return ONLY a JSON object."
5. If still failing: extract test code manually from the raw response

**Step 5**: Write the test code to the test file. If the file exists, append the test function (and merge imports). If new, create with the agent's `imports_needed` + `test_code`.

**Step 5a** (post-write test smell scan): Scan the test code for common smells before running:

| Smell | Detection | Action |
|-------|-----------|--------|
| **Assertion Roulette** | Multiple bare `assert` statements without messages in the same test function (3+) | Warn the user (don't block): "Test has N bare assertions — consider adding failure messages for easier debugging." |
| **Unknown Test** | Test name is generic: matches `test_1`, `test_it`, `test_works`, `test_example`, `test_thing` | Re-launch Test Writer with appended: "Use a descriptive test name that reads as a behavior spec (e.g., test_rejects_empty_email)." |
| **Tautological assertion** | `assert True`, `assert result is not None` when function has no None return path, `assert isinstance(result, X)` as sole assertion | Re-launch Test Writer with appended: "The assertion is tautological — test the actual behavior/value, not just that the function returns something." |

**Step 5b** (post-write layer lint): Scan the test code for layer-violating patterns:

| Layer | Forbidden patterns in test code |
|-------|-------------------------------|
| `domain` | `jest.mock(`, `vi.mock(`, `Mock(`, `mock.patch`, `unittest.mock`, `gomock`, `mockery` — domain tests must not use mocking libraries |
| `domain-service` | Same mocking patterns for domain objects (mocking ports/repos is OK) |
| `application` | No forbidden patterns (mocking ports is expected) |
| `infrastructure` | No forbidden patterns |

If forbidden patterns found:
1. Remove the offending mock/pattern from the test
2. Re-launch Test Writer with appended: "Do NOT use mocking libraries. This is a {LAYER} layer test. Use real domain objects."
3. If second attempt still uses forbidden patterns, ask user

**Step 6**: Run the test to confirm it FAILS (expect an assertion failure, not a setup error):

```bash
bash ~/.claude/skills/tdd/scripts/run_tests.sh {FRAMEWORK} "{TEST_COMMAND_FOR_SPECIFIC_TEST}"
```

**Step 7**: Evaluate the result with semantic validation:

| Result | Action |
|--------|--------|
| `status: "fail"`, assertion error | **Proper RED** — test fails because the expected behavior doesn't exist yet. Proceed. |
| `status: "fail"`, `ImportError` / `ModuleNotFoundError` | **Setup problem, not a proper RED.** The test can't even import the module under test. Fix: create a minimal stub (empty class/function) so the import resolves, then re-run. The test should now fail on the assertion instead. |
| `status: "fail"`, `AttributeError` on missing method | Similar to import error — the class exists but the method doesn't. This is an acceptable RED if the assertion would also fail. Proceed. |
| `status: "pass"` | Behavior already exists. Log: "Test passes — skipping slice (already implemented)." Increment `current_slice`, move to next slice. |
| `status: "error"`, `SyntaxError` | Fix: the test has a typo. Read the `raw_tail`, fix the test file directly. Re-run. If still erroring after 2 fix attempts, ask user. |
| `status: "error"`, compile/framework error | Fix: bad import, missing fixture, or framework misconfiguration. Read the `raw_tail`, fix the test file directly. Re-run. If still erroring after 2 fix attempts, ask user. |

**Step 8** (interactive mode only — skip in `--auto`): Present to the user:

```
RED: Test written and failing as expected.

Test: {test_name}
File: {test_file_path}
Failure: {failure message from JSON}

This test verifies: {test_description from agent response}

Proceed to GREEN phase? (or adjust the test?)
```

**Wait for user approval before proceeding to GREEN.**

**Update state**: `"phase": "red"`, add test file to `test_files_created`. Write state immediately.

---

### Phase 3: GREEN — Minimal Implementation

**Step 1**: Read the failing test file and the test failure output (the full `raw_tail` from the RED phase run_tests.sh result).

**Step 2**: Build the file tree of source files (not test files, not node_modules, etc.):

```bash
find {SOURCE_DIR} -type f \( -name '*.ts' -o -name '*.js' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.rb' -o -name '*.php' \) | grep -v test | grep -v spec | grep -v node_modules | grep -v __pycache__ | grep -v vendor | grep -v target | grep -v dist | grep -v build | head -50
```

**Step 3**: Read existing source files that the test imports or references.

**Step 4**: Read the prompt template from `references/agent_prompts.md` -> "Implementer Agent" section. Fill in:

- `{LANGUAGE}`: Detected language
- `{FAILING_TEST_CODE}`: The complete test file content
- `{TEST_FAILURE_OUTPUT}`: The `raw_tail` from run_tests.sh JSON output
- `{FILE_TREE}`: Source file listing from Step 2
- `{EXISTING_SOURCE}`: Content of relevant source files (if any — may be empty for greenfield)
- `{LAYER}`: The slice's layer tag from Phase 1
- `{LAYER_DEPENDENCY_CONSTRAINT}`: Layer-specific dependency constraint (see agent_prompts.md -> Layer-Specific Constraint Lookup)

On retries (attempt > 1), also fill in the `{?PREVIOUS_ATTEMPT}` section:
- `{PREVIOUS_ATTEMPT_DESCRIPTION}`: the `explanation` field from the failed attempt
- `{PREVIOUS_ATTEMPT_ERROR}`: the `raw_tail` from the test run after the failed attempt

**CRITICAL**: Do NOT include the slice specification, feature description, or any future plans. The Implementer works from the test alone.

**Step 5**: Launch the Implementer agent:

```
Task(subagent_type="general-purpose", prompt=<constructed prompt>)
```

**Step 6**: Parse the JSON response. **Validate layer boundaries**, then apply file changes.

**Step 6a** (Layer path validation): If `layer_map` is not empty, check each file path in the response against the current slice's layer:

```
For each file in response.files:
  inferred_layer = lookup file.path against layer_map (longest prefix match)
  if inferred_layer exists AND inferred_layer != current_slice.layer:
    if inferred_layer is OUTER relative to current_slice.layer:
      REJECT: "Implementer created/modified {file.path} which belongs to
      the {inferred_layer} layer, but this is a {current_slice.layer} slice.
      Inner layers must not depend on outer layers."
      → Re-launch Implementer with appended constraint:
        "Do NOT create or modify files in {inferred_layer} directories.
        This slice is {current_slice.layer} only."
    if inferred_layer is INNER relative to current_slice.layer:
      ALLOW: outer layers may touch inner-layer files (e.g., adding a port interface)
```

Layer ordering for "outer" check: domain < domain-service < application < infrastructure.

If `layer_map` is empty (flat project), skip this validation.

**Step 6b**: Apply validated file changes:

For each file in the response `files` array:
- If `action` is `"create"` or `"overwrite"`: Use the Write tool to create or overwrite the file with the complete content
- If `action` is `"edit"` (used for existing files over 200 lines): Use the Edit tool with `old_string` → `new_string` to apply the changes. The Implementer returns only the changed functions with surrounding context — identify the insertion point or the function being replaced, and use Edit tool accordingly. If the edit target is ambiguous, fall back to reading the full file and using Write.
- For existing files over 200 lines where the Implementer returned full content anyway (action = "overwrite"), prefer using Edit tool to apply only the diff — this prevents accidental reformatting of untouched code

**Step 7**: Run the specific test:

```bash
bash ~/.claude/skills/tdd/scripts/run_tests.sh {FRAMEWORK} "{TEST_COMMAND_FOR_SPECIFIC_TEST}"
```

**Step 8**: RETRY LOOP (if test still fails):

```
attempt = 1
max_attempts = 5
previous_explanation = null
previous_error = null

while status != "pass" AND attempt <= max_attempts:
    previous_explanation = explanation from last Implementer response
    previous_error = raw_tail from last test run

    Launch FRESH Task(Implementer) with:
      - same test code + file tree + existing source (re-read!)
      - NEW failure output
      - PREVIOUS_ATTEMPT section filled in

    Apply changes (Write tool for each file)
    Re-run test
    attempt += 1

if still failing after max_attempts:
    STOP. Present to user:
    "Implementation failed after 5 attempts. Last error: {raw_tail}"
    Ask: "Adjust the test, try a different approach, or debug manually?"
```

Each retry is a **fresh** Task call with only the previous attempt's explanation and error. This prevents the Implementer from going down rabbit holes while giving it enough context to try a different strategy.

**Step 9**: Once the specific test passes, run the FULL test suite:

```bash
bash ~/.claude/skills/tdd/scripts/run_tests.sh {FRAMEWORK} "{FULL_TEST_COMMAND}" --all
```

**Step 10**: Handle regressions:

| Result | Action |
|--------|--------|
| All pass | Proceed to REFACTOR |
| Regressions found | Auto-fix: launch a fresh Implementer with the regression test failures. Apply. Re-run full suite. Repeat up to 3 times. If still failing after 3 regression-fix attempts, STOP and present to user. |

**Step 11** (interactive mode only — skip in `--auto`): Present to the user:

```
GREEN: Test passing with minimal implementation.

Implementation: {explanation from agent response}
Files changed: {list}
All tests: {passed} passing, {failed} failing

Proceed to REFACTOR phase? (or adjust?)
```

**Update state**: `"phase": "green"`, update `files_modified`. Write state immediately.

**Step 12** (domain/domain-service slices only): Layer purity check before REFACTOR:

For each new/modified file in a `domain` or `domain-service` layer slice:
- **Import scan**: Read all import/require statements. Check each imported module against `layer_map`. Flag any import from an outer layer as a violation.
- **Constructor check**: Verify constructor takes NO parameters typed from outer layers (no ORM sessions, HTTP clients, framework configs)
- **Static call check**: No static method calls to outer-layer code
- If violations found, fix them now (move the dependency to a port interface) before entering REFACTOR

**Step 13**: Full-repo import scan (all layers, runs once per slice):

Scan ALL source files (not just session-modified) for dependency direction violations:

```bash
# For each source file, extract imports and check against layer_map
# Language-specific patterns:
#   Python: from X import Y, import X
#   TypeScript/JS: import ... from 'X', require('X')
#   Go: import "X"
```

For each file:
1. Determine its layer from `layer_map` (skip if no match)
2. For each import, determine the imported module's layer from `layer_map`
3. If imported layer is OUTER relative to file's layer → violation

Report violations to the user before REFACTOR:

```
Layer scan found N dependency direction violation(s):
- domain/user.py imports infrastructure/db.py (domain → infrastructure)
- domain/services/registration.py imports adapters/email.py (domain-service → infrastructure)
```

In `--auto` mode: attempt auto-fix (replace concrete import with port interface). In interactive mode: present violations and ask user how to proceed.

This supplements the Refactorer's import checking (which only sees session files) with a repo-wide scan. Static tools miss ~23% of violations (Pruijt et al., 2017) — combining textual + structural checks improves coverage.

---

### Phase 4: REFACTOR

**Step 1**: Gather all context:
- All test files created/modified during this session
- All source files modified during this session
- The green test output

**Step 2**: Read the prompt template from `references/agent_prompts.md` -> "Refactorer Agent" section. Fill in:

- `{LANGUAGE}`: Detected language
- `{GREEN_TEST_OUTPUT}`: Full test output showing all green
- `{ALL_TEST_CODE}`: Content of all test files
- `{ALL_IMPLEMENTATION_CODE}`: Content of all modified source files
- `{SLICE_LAYERS}`: Comma-separated list of unique layers from all slices completed so far

**Step 3**: Launch the Refactorer agent:

```
Task(subagent_type="general-purpose", prompt=<constructed prompt>)
```

**Step 4**: Parse the JSON response. If `suggestions` is empty, skip to Step 6.

Apply suggestions **one at a time**, in priority order (high first):

For each suggestion:
1. Apply the code change (Edit tool, using `old_code` -> `new_code` for each file)
2. Run the project linter/formatter check (detect from project config):
   - **Python**: `python -m black --check {files} && python -m flake8 {files} && python -m mypy {files}`
   - **TypeScript/JS**: `npx eslint {files}` or `npx tsc --noEmit`
   - **Go**: `go vet ./...`
   - **Rust**: `cargo clippy`
   - If lint fails -> **revert immediately** and skip this suggestion (same as test failure)
3. Run the full test suite
4. If any test fails -> **revert immediately** (re-read the file from before the edit and Write it back) and skip this suggestion
5. If all tests pass and lint passes -> keep the change

**Step 5** (interactive mode only — skip in `--auto`): Present:

```
REFACTOR: Code improved, all tests still passing.

Applied: {list of accepted suggestions}
Skipped: {list of reverted suggestions, if any}
All tests: {count} passing

[Moving to slice N of M] or [All slices complete]
```

In `--auto` mode, print one-liner:

```
[auto] REFACTOR slice N/M: {applied_count} applied, {skipped_count} skipped
```

**Update state**: `"phase": "refactor"`. Write state immediately.

---

### Phase 5: Next Slice or Complete

If more slices remain -> increment `current_slice` in state, return to Phase 2.

If all slices complete -> present summary:

```
TDD Complete: {feature name}

Slices implemented: N
Tests written: N
Files created/modified: {list}
All tests passing: yes
```

Clean up: remove `.tdd-state.json` (in `--auto` mode, remove silently; in interactive, ask user).

---

## Resume Support

When user invokes `/tdd --resume`:

1. Read `.tdd-state.json` from project root
2. Report current state: "Found TDD session for '{feature}'. Currently at slice {N}/{total}, phase: {phase}."
3. Resume from the current phase of the current slice
4. If `auto_mode` is true in state, continue in auto mode

---

## Edge Cases

### Greenfield Projects

No source files, no tests, no test configuration. Handle gracefully:

1. **Phase 0 Step 3**: If run_tests.sh returns `status: "error"` with `total: 0`, check if any test files exist. If none, this is greenfield — proceed.
2. **Phase 0 Step 4**: extract_api.sh will return empty output. Pass `"(No existing API — this is a new project)"` to the Test Writer.
3. **Phase 2**: The Test Writer will create test files from scratch. May need to set up the test framework config (e.g., `jest.config.js`, `pytest.ini`). If the first test run fails with a framework error (not a test failure), create minimal framework config and retry.

### Bug Fix TDD

1. Write a test demonstrating the bug (should FAIL showing the bug exists)
2. Confirm failure matches the reported bug — human checkpoint
3. Fix: minimal code to make test pass (GREEN phase as normal)
4. Verify: no regressions

### Existing Code (Characterization Tests)

1. Write a test for CURRENT behavior (should PASS — this is a characterization test)
2. Modify the test for DESIRED behavior (should FAIL)
3. Proceed with GREEN -> REFACTOR

### User-Provided Tests

If user provides test code:
1. Run to confirm it fails (RED confirmed)
2. Skip to Phase 3 (GREEN) — user-provided tests are authoritative
3. Do not modify without asking

### Flaky Tests

If a test sometimes passes/fails: stop, report, fix the flaky test before continuing.

---

## Failure Recovery Reference

| Failure | Phase | Recovery |
|---------|-------|----------|
| Test Writer returns invalid JSON | RED | Parse with fence-stripping + substring extraction. Retry once with "Return ONLY JSON." Fall back to manual extraction. |
| Test passes when it should fail | RED | Log "already implemented", skip slice, move to next. |
| Test has syntax/compile error | RED | Read raw_tail, fix test file directly. Retry up to 2 times. Then ask user. |
| Implementer returns invalid JSON | GREEN | Same JSON recovery as Test Writer. |
| Test still fails after implementation | GREEN | Retry loop: up to 5 fresh Implementer calls with previous-attempt context. Then ask user. |
| Full suite has regressions | GREEN | Auto-fix: fresh Implementer with regression failures. Up to 3 attempts. Then ask user. |
| Refactorer suggestion breaks tests | REFACTOR | Revert immediately, skip suggestion, continue with next. |
| run_tests.sh timeout | Any | Increase timeout. If persistent, ask user about test performance. |
| run_tests.sh returns `"error"` | Any | Read raw_tail for cause. Script error (missing binary, bad path) -> fix and retry. Compilation error -> treat as implementation error. |
| extract_api.sh returns empty | RED | Normal for greenfield. Pass "(No existing API)" message. |
| Agent response is completely empty | Any | Retry the Task call once. If still empty, ask user. |

---

## Layer Reference

See `references/layer_guide.md` for layer definitions, dependency rules, test strategies by layer, and detection heuristics.

## Anti-Patterns to Avoid

See `references/anti_patterns.md`. Critical ones:
- Never modify a test to make it pass (change implementation, not tests)
- Never write implementation before tests
- Never write all tests at once (vertical slicing)
- Never test implementation details
- Never skip the RED phase
- Never let domain code import infrastructure (dependency direction violation)
- Never mock domain objects — construct real instances instead

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
