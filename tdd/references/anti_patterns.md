# TDD Anti-Patterns Reference

## Phase Violations

### Writing implementation before tests
**Symptom**: Code appears in source files before a corresponding test exists.
**Fix**: Delete the implementation. Write the test first. Period.
**Why it matters**: Implementation-first means the test is verifying what was built, not specifying what should be built. The test becomes a rubber stamp, not a design tool.

### Writing all tests at once (horizontal slicing)
**Symptom**: Multiple test functions written in a batch before any implementation.
**Fix**: Write exactly one test. Make it fail. Make it pass. Refactor. Then write the next test.
**Why it matters**: Batch testing leads to batch implementation. The feedback loop widens, errors compound, and refactoring becomes risky because too many things change at once.

### Skipping the RED phase
**Symptom**: A test is written and passes immediately without implementation.
**Fix**: If the test passes without new code, either (a) the behavior already exists, (b) the test is trivially passing (wrong assertion), or (c) the test setup is wrong. Investigate.
**Why it matters**: A test that was never seen failing provides no confidence. It might pass for the wrong reasons.

### Modifying tests to match implementation
**Symptom**: After writing implementation, the test is changed to match what the code does rather than what the spec requires.
**Fix**: The test encodes the REQUIREMENT. If the implementation doesn't match, fix the implementation. Only change the test if the user confirms the requirement was wrong.
**Why it matters**: This inverts the authority chain. Tests are specifications; implementation serves them, not the other way around.

## Test Quality Anti-Patterns

### Testing implementation details
**Symptom**: Tests assert on private methods, internal state, call counts of mocked internals, or specific algorithm steps.
**Examples**:
- `expect(service._cache).toHaveLength(3)` -- testing private cache
- `expect(mockDb.query).toHaveBeenCalledTimes(2)` -- testing internal query pattern
- `expect(result.__internal_flag).toBe(true)` -- testing private state

**Fix**: Test through public interfaces only. Assert on return values, side effects visible to callers, or observable state changes.
**Why it matters**: Implementation-detail tests break on every refactor, even when behavior is preserved. They test HOW the code works, not WHAT it does.

### Testing the framework, not the code
**Symptom**: Tests that verify the test framework, mocking library, or ORM works correctly.
**Examples**:
- Mocking a database then asserting the mock returns the mocked value
- Testing that `JSON.parse(JSON.stringify(x))` round-trips correctly

**Fix**: Tests should verify YOUR code's behavior, not third-party behavior.

### Tautological tests
**Symptom**: Tests where the assertion is trivially true regardless of implementation.
**Examples**:
- `expect(true).toBe(true)`
- `expect(result).toBeDefined()` (where result is always defined by the function signature)
- Asserting a function returns without throwing when it has no throw paths

**Fix**: Every assertion must be capable of failing given a plausible incorrect implementation.

### Over-mocking
**Symptom**: More mock setup code than actual test code. Every dependency is mocked.
**Fix**: Use real implementations where practical. Mock only at system boundaries (network, filesystem, clock). Prefer integration tests with in-memory fakes over unit tests with extensive mocks.
**Why it matters**: Over-mocked tests pass even when integration is broken. They test the wiring, not the behavior.

## Structural Anti-Patterns

### God test
**Symptom**: A single test function that tests multiple behaviors with multiple assertions and complex setup.
**Fix**: Split into one test per behavior. Each test should have one reason to fail.
**Pattern**: Arrange-Act-Assert, each section clearly delineated.

### Test interdependence
**Symptom**: Tests that depend on execution order, shared mutable state, or other tests' side effects.
**Fix**: Each test sets up its own state and tears it down. Tests must pass when run in isolation or in any order.

### Fragile test fixtures
**Symptom**: A change in test setup code breaks many unrelated tests.
**Fix**: Use builder patterns or factory functions that provide sensible defaults. Each test overrides only what it cares about.

### Testing trivial code
**Symptom**: Tests for getters, setters, constructors, or obvious one-liners.
**Fix**: Skip tests for code with zero logic. Focus testing on code with conditionals, loops, transformations, or business rules.

## Process Anti-Patterns

### Gold plating during GREEN
**Symptom**: Implementation during the GREEN phase includes extra features, optimization, or error handling not required by the current test.
**Fix**: Write the absolute minimum to make the test pass. If you want to add more, write a test for it first.

### Skipping REFACTOR
**Symptom**: After GREEN, immediately writing the next test without cleaning up.
**Fix**: Always assess the code after GREEN. Even if no refactoring is needed, consciously evaluate. Refactoring is where design emerges.

### Premature refactoring
**Symptom**: Extracting abstractions after only one or two instances of a pattern.
**Fix**: Wait for the "Rule of Three" -- extract abstractions only after seeing a pattern three times. In early TDD cycles, duplication is acceptable.

### Ignoring test failures in the full suite
**Symptom**: A new test passes but existing tests break, and the broken tests are dismissed as "unrelated."
**Fix**: Every test failure after GREEN is a regression until proven otherwise. Investigate and fix before moving to REFACTOR.
