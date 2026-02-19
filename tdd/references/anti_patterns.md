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

## Layer & Dependency Anti-Patterns

### Domain importing infrastructure
**Symptom**: Domain model code imports ORM classes, HTTP clients, file system modules, or framework utilities.
**Examples**:
- `from sqlalchemy.orm import Session` in a domain entity
- `import axios from 'axios'` in a domain service
- `use Illuminate\Database\Eloquent\Model` in a domain value object

**Fix**: Domain code must have zero external dependencies. If the domain needs to persist or communicate, define an interface (port) in the domain layer and let infrastructure implement it.
**Why it matters**: Domain code that imports infrastructure cannot be tested without that infrastructure. It also locks business logic to a specific technology choice.

### Business logic in handlers/controllers
**Symptom**: Validation rules, calculations, state transitions, or conditional logic living in HTTP handlers, CLI commands, or event listeners instead of domain objects or services.
**Examples**:
- Price calculation in an Express route handler
- Email format validation in a controller
- Order state machine transitions in a message consumer

**Fix**: Extract the logic into a domain entity, value object, or domain service. The handler should only translate HTTP/CLI/event input into domain calls and translate domain output back.
**Why it matters**: Business logic in handlers is untestable without spinning up the framework. It also gets duplicated when you add a second entry point (API + CLI + queue consumer).

### Mocking domain objects
**Symptom**: Using `jest.mock()`, `unittest.mock.Mock()`, or similar to create fake domain entities or value objects instead of constructing real instances.
**Examples**:
- `const user = { validate: jest.fn().mockReturnValue(true) }` instead of `new User("valid@email.com")`
- `mock_order = Mock(spec=Order)` instead of `Order(items=[item1, item2])`

**Fix**: Domain objects are pure and cheap to construct. Use real instances in tests. Only mock at boundaries (repositories, external services).
**Why it matters**: Mocking domain objects defeats the purpose of testing — you're testing your mocks, not your domain logic. If a domain object is hard to construct, that's a design smell.

### Anemic domain model
**Symptom**: Entities with only getters/setters, all logic in services. Tests pass but the design is wrong — behavior is disconnected from the data it operates on.
**Examples**:
- `User` class with only `name`, `email` properties; `UserService.validateUser(user)` does all validation
- `Order` with `items` list; `OrderCalculator.calculateTotal(order)` computes the total externally

**Fix**: Move behavior onto the entity that owns the data. `user.validate()`, `order.calculateTotal()`. Services coordinate; entities compute.
**Why it matters**: Anemic models scatter related logic across services, making it harder to find, test, and enforce invariants. It's procedural code wearing OOP clothing.

### Repository interface in wrong layer
**Symptom**: The repository interface (`UserRepository`, `OrderRepository`) is defined alongside its implementation in the infrastructure layer, rather than in the domain layer.
**Examples**:
- `infrastructure/repositories/user_repository.py` contains both the interface and the PostgreSQL implementation
- `src/database/UserRepository.ts` defines the interface and exports it

**Fix**: Define the interface in the consuming layer (`domain/ports/user_repository.py` if consumed by domain services, `application/ports/` if consumed by use cases). The infrastructure layer imports and implements it. The consumer defines the contract.
**Why it matters**: If the interface lives in infrastructure, domain code must import infrastructure to reference it — breaking the dependency rule.

### Service locator / static global container
**Symptom**: Domain or application code obtains dependencies through a global registry, static container, or service locator instead of constructor injection.
**Examples**:
- `Container.resolve(UserRepository)` called inside a domain service method
- `ServiceLocator.get('emailService')` in a use case
- `app.make('UserRepository')` (Laravel) inside domain code
- `@inject` decorators that resolve from a global container at import time

**Fix**: Accept dependencies through the constructor (or function parameters). The composition root (in infrastructure) wires everything together. Domain and application code never knows where implementations come from.
**Why it matters**: Service locators hide dependencies — the class signature doesn't reveal what it needs. Tests require configuring a global container instead of passing fakes directly. It also makes dependency direction invisible: a domain class appears independent but actually reaches into infrastructure at runtime.

### Active Record bleed (ORM entity as domain object)
**Symptom**: The same class serves as both the database model (ORM entity) and the domain object. Framework-specific annotations, base classes, or conventions leak into domain logic.
**Examples**:
- `class User extends Model` (Eloquent/ActiveRecord) used directly in domain services
- `@Entity() class Order` (TypeORM) with both column decorators and business logic
- Domain code calling `.save()`, `.delete()`, or `.query()` on domain objects
- SQLAlchemy `Base` subclass used as a domain entity

**Fix**: Separate the persistence model from the domain model. The infrastructure layer maps between them. Domain entities have zero ORM awareness.
**Why it matters**: Active Record couples business logic to the database schema and ORM framework. Domain tests require a database (or complex mocking). Schema changes break business logic. The domain layer becomes untestable without infrastructure — violating the core DDD/Onion principle.
