# Test Framework Configuration Reference

## JavaScript / TypeScript

### Jest

**Detection**: `jest` in package.json devDependencies, or `jest.config.js/ts/mjs`

**Run commands**:
```bash
# All tests
npx jest

# Single file
npx jest path/to/file.test.ts

# Single test by name
npx jest --testPathPattern=file.test.ts -t "should calculate total"

# Watch mode
npx jest --watch

# With coverage
npx jest --coverage
```

**Test file conventions**: `*.test.ts`, `*.test.js`, `*.spec.ts`, `*.spec.js`, or files in `__tests__/`

**Minimal test skeleton**:
```typescript
describe("ModuleName", () => {
  it("should [behavior]", () => {
    // Arrange
    const input = ...;

    // Act
    const result = functionUnderTest(input);

    // Assert
    expect(result).toBe(expected);
  });
});
```

### Vitest

**Detection**: `vitest` in package.json devDependencies, or `vitest.config.ts/js`

**Run commands**:
```bash
# All tests (run once)
npx vitest run

# Single file
npx vitest run path/to/file.test.ts

# Single test by name
npx vitest run path/to/file.test.ts -t "should calculate total"

# Watch mode (default)
npx vitest

# With coverage
npx vitest run --coverage
```

**Test file conventions**: Same as Jest. Vitest is API-compatible with Jest.

**Minimal test skeleton**: Same as Jest (uses same `describe`/`it`/`expect` API).

### Mocha + Chai

**Detection**: `mocha` in package.json, `.mocharc.yml`

**Run commands**:
```bash
npx mocha "test/**/*.test.js"
npx mocha --grep "should calculate"
```

---

## Python

### pytest

**Detection**: `pytest` in pyproject.toml/setup.cfg, `pytest.ini`, `conftest.py`

**Run commands**:
```bash
# All tests
pytest -v

# Single file
pytest tests/test_module.py -v

# Single test
pytest tests/test_module.py::test_function_name -v

# By keyword match
pytest -k "calculate and total" -v

# With coverage
pytest --cov=src -v

# Stop on first failure
pytest -x -v
```

**Test file conventions**: `test_*.py` or `*_test.py`, functions prefixed with `test_`

**Minimal test skeleton**:
```python
def test_should_calculate_total():
    # Arrange
    items = [Item(price=10), Item(price=20)]

    # Act
    result = calculate_total(items)

    # Assert
    assert result == 30
```

**With classes**:
```python
class TestCalculator:
    def test_should_add_numbers(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5

    def test_should_handle_negative(self):
        calc = Calculator()
        assert calc.add(-1, 1) == 0
```

**Fixtures**:
```python
import pytest

@pytest.fixture
def calculator():
    return Calculator()

def test_should_add(calculator):
    assert calculator.add(2, 3) == 5
```

### pytest-asyncio

**Detection**: `pytest-asyncio` in pyproject.toml/requirements, or `asyncio_mode` in pytest.ini/pyproject.toml

**asyncio_mode detection**: Check `pytest.ini` and `pyproject.toml` for `asyncio_mode = auto`. When `auto` mode is set, `@pytest.mark.asyncio` is not needed — all `async def test_*` functions are automatically collected as async tests.

**Run commands**: Same as pytest (no difference for async tests).

**Async test skeleton** (asyncio_mode = auto):
```python
from unittest.mock import AsyncMock, MagicMock


async def test_should_process_message():
    # Arrange
    service = MessageService()
    mock_repo = AsyncMock()
    mock_repo.save.return_value = None

    # Act
    result = await service.process("hello", repo=mock_repo)

    # Assert
    assert result.status == "processed"
    mock_repo.save.assert_awaited_once()
```

**Async test skeleton** (asyncio_mode = strict, or not set):
```python
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_should_process_message():
    service = MessageService()
    result = await service.process("hello")
    assert result.status == "processed"
```

**Async fixtures**:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_chat.id = 12345
    update.message.text = "test"
    return update


@pytest.fixture
async def db_session():
    """Async fixture with setup and teardown."""
    session = await create_test_session()
    yield session
    await session.close()
```

**Key patterns**:
- Use `AsyncMock` for any method that is `async def` — it returns an awaitable
- Use `MagicMock` for synchronous attributes/properties on async objects
- `assert_awaited_once()` / `assert_awaited_once_with(...)` — async equivalents of `assert_called_once`
- Async fixtures use `async def` + `yield` for setup/teardown

---

## Go

### go test

**Detection**: `go.mod` in project root

**Run commands**:
```bash
# All tests
go test ./...

# Single package
go test ./pkg/calculator/

# Single test
go test -run TestCalculateTotal ./pkg/calculator/

# Verbose
go test -v ./...

# With coverage
go test -cover ./...

# Race detection
go test -race ./...
```

**Test file conventions**: `*_test.go` in same package

**Minimal test skeleton**:
```go
func TestShouldCalculateTotal(t *testing.T) {
    // Arrange
    items := []Item{{Price: 10}, {Price: 20}}

    // Act
    result := CalculateTotal(items)

    // Assert
    if result != 30 {
        t.Errorf("expected 30, got %d", result)
    }
}
```

**Table-driven tests** (idiomatic Go):
```go
func TestCalculateTotal(t *testing.T) {
    tests := []struct {
        name     string
        items    []Item
        expected int
    }{
        {"empty list", []Item{}, 0},
        {"single item", []Item{{Price: 10}}, 10},
        {"multiple items", []Item{{Price: 10}, {Price: 20}}, 30},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := CalculateTotal(tt.items)
            if result != tt.expected {
                t.Errorf("expected %d, got %d", tt.expected, result)
            }
        })
    }
}
```

---

## Rust

### cargo test

**Detection**: `Cargo.toml`

**Run commands**:
```bash
# All tests
cargo test

# Single test
cargo test test_name

# Single module
cargo test module_name::

# With output
cargo test -- --nocapture

# Watch mode (requires cargo-watch)
cargo watch -x test
```

**Test file conventions**: `#[cfg(test)]` module in source files, or `tests/` directory for integration tests

**Minimal test skeleton**:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn should_calculate_total() {
        let items = vec![Item { price: 10 }, Item { price: 20 }];
        let result = calculate_total(&items);
        assert_eq!(result, 30);
    }
}
```

---

## Ruby

### RSpec

**Detection**: `rspec` in Gemfile, `.rspec` file, `spec/` directory

**Run commands**:
```bash
# All tests
rspec

# Single file
rspec spec/calculator_spec.rb

# Single test by line
rspec spec/calculator_spec.rb:15

# By description
rspec -e "should calculate total"

# With documentation format
rspec --format documentation
```

**Test file conventions**: `spec/**/*_spec.rb`

**Minimal test skeleton**:
```ruby
RSpec.describe Calculator do
  describe "#total" do
    it "should calculate total for multiple items" do
      items = [Item.new(price: 10), Item.new(price: 20)]
      calculator = Calculator.new(items)

      result = calculator.total

      expect(result).to eq(30)
    end
  end
end
```

---

## PHP

### PHPUnit

**Detection**: `phpunit` in composer.json, `phpunit.xml`

**Run commands**:
```bash
# All tests
./vendor/bin/phpunit

# Single file
./vendor/bin/phpunit tests/CalculatorTest.php

# Single test
./vendor/bin/phpunit --filter testShouldCalculateTotal

# With coverage
./vendor/bin/phpunit --coverage-text
```

**Test file conventions**: `tests/**/*Test.php`, classes extend `TestCase`

**Minimal test skeleton**:
```php
class CalculatorTest extends TestCase
{
    public function testShouldCalculateTotal(): void
    {
        $items = [new Item(price: 10), new Item(price: 20)];
        $calculator = new Calculator($items);

        $result = $calculator->total();

        $this->assertEquals(30, $result);
    }
}
```
