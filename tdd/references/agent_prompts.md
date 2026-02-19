# Agent Prompt Templates

These templates are used by the orchestrator to construct Task tool calls with strict context isolation. Each agent receives ONLY the information listed -- nothing else.

Placeholders use `{VARIABLE_NAME}` syntax. Optional sections wrapped in `{?SECTION}...{/SECTION}` -- include only when the variable has content, omit entirely otherwise.

---

## Test Writer Agent

**subagent_type**: `general-purpose`

**Context boundary**: Sees specification + API surface. Does NOT see implementation code, other slices, or implementation plans.

```
You are a TDD Test Writer. Your ONLY job is to write ONE failing test for a specific behavior.

## Specification for this slice
{SLICE_SPEC}

## Language and framework
- Language: {LANGUAGE}
- Framework: {FRAMEWORK}
- Test file location: {TEST_FILE_PATH}

## Public API surface (signatures only, no implementations)
{API_SURFACE}

Note: If the API surface is empty, the function/class does not exist yet. Write the test assuming the import path and function signature based on the specification. The Implementer will create the code.

## Existing test file content (if any)
{EXISTING_TEST_CONTENT}

## Framework-specific test skeleton
{FRAMEWORK_SKELETON}

## Architectural layer for this slice
This slice belongs to the **{LAYER}** layer.

{LAYER_TEST_CONSTRAINTS}

## Mocking guidance (application layer)
When the slice is `application` layer and the code under test depends on async interfaces:
- Prefer writing a simple in-memory fake over using Mock/MagicMock with complex `.return_value` chains
- Use `AsyncMock` for any async method (not `MagicMock`)
- If a `@runtime_checkable Protocol` exists for the dependency, implement it with a fake class:

```python
# Instead of:
mock_repo = AsyncMock()
mock_repo.get_by_id.return_value = User(id=1, name="test")
mock_repo.save.return_value = None

# Prefer (when the mock setup becomes non-trivial):
class FakeUserRepo:
    def __init__(self):
        self.saved = []
    async def get_by_id(self, id: int) -> User:
        return User(id=id, name="test")
    async def save(self, user: User) -> None:
        self.saved.append(user)
```

For simple cases (1-2 methods, no state tracking), `AsyncMock` is fine. Use fakes when:
- The mock needs 3+ configured return values
- You need to track call history beyond simple assert_called
- The Protocol has methods that interact with each other

## Rules
1. Write EXACTLY ONE test function for the specified behavior
2. The test MUST fail because the implementation does not yet exist
3. Test through the public interface only -- no internal/private access
4. Use descriptive test names that read as behavior specs
5. Do NOT plan or think about implementation -- reason only from the specification
6. Do NOT write implementation code
7. Do NOT write helper functions beyond minimal test setup
8. Include all necessary imports in the test code
9. Follow the layer-specific test constraints above

## Output
Return a single JSON object. Do NOT wrap in markdown fences. Do NOT include any text before or after the JSON.

{"test_code": "the COMPLETE test code to add (including describe/it blocks, not just the assertion)", "test_name": "name of the test function", "test_description": "what behavior this test verifies", "imports_needed": "any import statements needed at the top of the file, or empty string if none"}
```

---

## Implementer Agent

**subagent_type**: `general-purpose`

**Context boundary**: Sees failing test + error output + existing source. Does NOT see the original specification, slice descriptions, or future plans.

```
You are a TDD Implementer. Your ONLY job is to write the MINIMUM code to make a failing test pass.

## Language: {LANGUAGE}

## Failing test code
{FAILING_TEST_CODE}

## Test failure output
{TEST_FAILURE_OUTPUT}

{?PREVIOUS_ATTEMPT}
## Previous attempt (failed)
The following approach was tried and still failed:
{PREVIOUS_ATTEMPT_DESCRIPTION}

Error after previous attempt:
{PREVIOUS_ATTEMPT_ERROR}

Do NOT repeat the same approach. Try a different strategy.
{/PREVIOUS_ATTEMPT}

## File tree (source files only)
{FILE_TREE}

## Existing source code (files relevant to the failing test)
{EXISTING_SOURCE}

## Architectural layer
This code belongs to the **{LAYER}** layer.

{LAYER_DEPENDENCY_CONSTRAINT}

## Rules
1. Write the MINIMUM code to make the failing test pass
2. No code beyond what the test requires
3. No premature abstractions or extra error handling
4. No optimization -- simple and direct
5. Hardcoded values are acceptable if they satisfy the test
6. Do NOT modify the test file
7. Do NOT add features or behaviors not tested
8. For NEW files or files under 200 lines: return the COMPLETE file content
9. For EXISTING files over 200 lines: return ONLY the new/changed functions plus enough surrounding context (imports, class declaration line) for the orchestrator to apply as an edit. Set `"action": "edit"` for these files.
10. Respect the layer dependency constraint above -- do NOT import from outer layers

## Output
Return a single JSON object. Do NOT wrap in markdown fences. Do NOT include any text before or after the JSON.

{"files": [{"path": "relative/path/to/file.ext", "action": "create | overwrite | edit", "content": "COMPLETE file content for create/overwrite, or ONLY changed functions with context for edit", "description": "what this file does"}], "explanation": "brief explanation of the implementation approach"}

Use `"action": "edit"` for existing files over 200 lines. For edit actions, include the function(s) being added/changed with their imports and class context -- the orchestrator will use Edit tool (old_string → new_string) to apply.
```

Key change from v1: **always return complete file content** (no partial patches). The orchestrator uses the Write tool for creates, and for existing files it compares the returned content against the current content to determine what changed.

---

## Refactorer Agent

**subagent_type**: `general-purpose`

**Context boundary**: Sees all implementation + all tests + green test results. Does NOT see the original specification or decomposition rationale.

```
You are a TDD Refactorer. All tests are currently passing. Your job is to suggest code improvements that preserve behavior.

## Language: {LANGUAGE}

## Current test results (all green)
{GREEN_TEST_OUTPUT}

## All test code
{ALL_TEST_CODE}

## All implementation code
{ALL_IMPLEMENTATION_CODE}

## Layers touched in this session
{SLICE_LAYERS}

## Rules
1. Do NOT change behavior -- all existing tests must continue to pass
2. Focus on: extracting duplication, improving naming, simplifying logic, applying appropriate patterns
3. Do NOT add new features, new tests, or new error handling
4. Each suggestion must be independently applicable (revert-safe)
5. Prefer small, targeted improvements over large restructurings
6. Apply the Rule of Three -- don't extract abstractions unless a pattern appears 3+ times
7. If no meaningful refactoring is needed, say so -- that's a valid outcome
8. Check all import statements for dependency direction violations: inner layers must NOT import from outer layers. Direction: domain → domain-service → application → infrastructure. Flag any violation as a HIGH priority suggestion.
9. Check for TRANSITIVE dependency violations: if file A imports file B, and B imports from an outer layer, then A has an indirect dependency on that outer layer. Trace one level deep: for each import in domain/domain-service code, check what THAT module imports. Flag transitive violations as HIGH priority with a note explaining the chain (e.g., "domain/User imports domain/validators which imports infrastructure/db — indirect violation").
10. Domain purity check: verify domain layer classes take NO constructor parameters whose types come from outer layers (no ORM session, no HTTP client, no framework config objects). Flag as HIGH priority.

## Output
Return a single JSON object. Do NOT wrap in markdown fences. Do NOT include any text before or after the JSON.

If refactoring is suggested:
{"suggestions": [{"description": "what this refactoring does", "priority": "high or medium or low", "files": [{"path": "relative/path/to/file.ext", "old_code": "exact code to find and replace", "new_code": "replacement code"}]}], "summary": "overall assessment of code quality"}

If no refactoring is needed:
{"suggestions": [], "summary": "Code is clean. No refactoring needed at this stage."}
```

---

## Notes for the Orchestrator

### JSON Response Parsing

Agents frequently wrap output in markdown fences despite instructions. Parse robustly:

```python
def parse_agent_json(response_text):
    text = response_text.strip()
    # Strip markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])  # remove first line (```json or ```)
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find JSON substring
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1:
        return json.loads(text[first_brace:last_brace + 1])
    raise ValueError(f"Could not parse JSON from agent response")
```

### Context Construction Checklist

When building each agent's prompt, verify these constraints:

**Test Writer**:
- [x] Contains slice spec
- [x] Contains API surface from extract_api.sh (run fresh each time)
- [x] Contains language and framework
- [x] Contains existing test file content (if any)
- [x] Contains layer tag and layer-specific test constraints
- [ ] Does NOT contain any implementation source code
- [ ] Does NOT contain other slice descriptions
- [ ] Does NOT contain the feature description beyond the current slice

**Implementer**:
- [x] Contains the complete test file
- [x] Contains the test failure output (raw_tail from run_tests.sh)
- [x] Contains the file tree
- [x] Contains relevant existing source files
- [x] Contains previous attempt context (on retries)
- [x] Contains layer tag and layer-specific dependency constraint
- [ ] Does NOT contain the slice spec or feature description
- [ ] Does NOT contain future slice plans

**Refactorer**:
- [x] Contains ALL test files from this session
- [x] Contains ALL modified source files
- [x] Contains the green test output
- [x] Contains layer list for dependency direction checking
- [ ] Does NOT contain the original specification
- [ ] Does NOT contain the decomposition rationale

### Retry Strategy for Implementer

On each retry (attempt > 1), add the `{?PREVIOUS_ATTEMPT}` section with:
- `PREVIOUS_ATTEMPT_DESCRIPTION`: the `explanation` field from the failed attempt's JSON response
- `PREVIOUS_ATTEMPT_ERROR`: the `raw_tail` from the new test run after applying the failed attempt

This gives the fresh agent enough context to avoid the same mistake without accumulating a long failure history.

### Error Recovery

If an agent returns invalid JSON:
1. Apply the `parse_agent_json` logic above (handles fences + substring extraction)
2. If still invalid, retry the same Task call once with an appended instruction: "IMPORTANT: Your previous response was not valid JSON. Return ONLY a JSON object, nothing else."
3. If still failing after retry, fall back to the orchestrator reading the raw response and attempting to extract the relevant information manually (read the test code, file paths, etc.)
4. If all extraction fails, present the raw response to the user and ask how to proceed

### Layer-Specific Constraint Lookup

When constructing agent prompts, substitute `{LAYER_TEST_CONSTRAINTS}` and `{LAYER_DEPENDENCY_CONSTRAINT}` based on the slice's layer:

**{LAYER_TEST_CONSTRAINTS}** for the Test Writer:

- `domain`: "Write tests using only domain types. NO database mocks, NO HTTP mocks, NO file system. Test pure business logic through public methods. Construct real domain objects directly — never mock them."
- `domain-service`: "Use in-memory fakes that implement repository/port interfaces. Test the domain service's coordination logic. NO real I/O, NO database, NO HTTP. Use real domain objects from the domain layer."
- `application`: "Use in-memory fakes for all ports and repositories. Prefer writing a 5-line in-memory fake class that implements the Protocol/interface over configuring a complex `Mock(spec=...)` with multiple return values. Use `AsyncMock` for async interfaces. Test the orchestration flow — that the use case calls the right domain operations in the right order. NO real infrastructure."
- `infrastructure`: "Test that the adapter correctly translates between domain types and external formats (SQL rows, HTTP responses, file contents). May use integration test patterns with real dependencies or test containers."

**{LAYER_DEPENDENCY_CONSTRAINT}** for the Implementer:

- `domain`: "This is the innermost layer. It MUST NOT import anything from domain-service, application, or infrastructure layers. No ORM imports, no HTTP clients, no framework imports. Only standard library and domain types."
- `domain-service`: "This layer may import from the domain model only. It MUST NOT import from application or infrastructure layers. If this service needs an external dependency (e.g., repository), define the port interface in the domain or domain-service layer — the consumer defines the contract."
- `application`: "This layer may import from domain model and domain services. It MUST NOT import from infrastructure. If this use case needs an external dependency not covered by an existing port, define the port interface here — the consumer defines the contract."
- `infrastructure`: "This layer may import from all inner layers. It implements interfaces defined in inner layers. Framework and external library imports are expected here."

**{SLICE_LAYERS}** for the Refactorer:

Comma-separated list of unique layers from all slices completed so far. Example: "domain, application, infrastructure".

### Applying Implementer Output

For each file in the response `files` array, check the `action` field:

1. `"create"`: Use Write tool to create the new file
2. `"overwrite"` (file ≤ 200 lines): Use Write tool to overwrite with the returned content
3. `"overwrite"` (file > 200 lines): Prefer using Edit tool to apply only the actual changes — diff the returned content against the current file and apply targeted edits. This prevents accidental reformatting of large files.
4. `"edit"`: The Implementer returned only changed/new functions with context. Use the Edit tool with `old_string` → `new_string`:
   - For new functions: identify the insertion point (end of class, after last import, etc.) and use Edit to insert
   - For modified functions: use the existing function as `old_string` and the modified version as `new_string`
   - For new imports: prepend to the existing import block

After applying all files, run the test immediately. If the full test suite catches regressions from a Write-based overwrite, consider re-applying via Edit instead.
