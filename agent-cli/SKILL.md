---
name: agent-cli
description: Add agent-friendly --json NDJSON output to Python CLI scripts, or scaffold a complete cli_utils package for a project. Use this skill when the user wants to make scripts machine-readable for AI agents, add --json flags, convert print statements to structured JSON, build a CLI helper library, create an open-source CLI-for-agents package, add structured logging, or make CLI output machine-readable. Also use when the user mentions NDJSON, structured CLI output, agent-friendly CLI, non-interactive scripts, or JSON I/O for automation.
---

# Agent-Friendly CLI Builder

Convert Python CLI scripts from human-only output to agent-consumable NDJSON, or scaffold a complete `cli_utils` package ready for open-source distribution.

## Two Modes

### Mode A: Convert an existing script

When the user points at a script and says "make this agent-friendly" or "add --json":

1. **Scan** the script for output points
2. **Generate** `cli_utils.py` if the project doesn't have one
3. **Replace** all output with structured helpers
4. **Verify** no raw output leaks in JSON mode

### Mode B: Scaffold a complete package

When the user says "create a cli_utils package" or wants an open-source library:

1. **Scaffold** a full Python package with pyproject.toml, tests, license, README
2. **Include** all helpers: `json_log`, `json_error`, `die`, `log`, `add_json_flag`, `enable_json`, `is_json`
3. **Add** pytest test suite with full coverage
4. **Add** MIT license (or ask user preference)

## Core Architecture

The fundamental pattern: every script gets a `--json` flag. When active, **all stdout becomes newline-delimited JSON** (NDJSON). Each line is a self-contained JSON object with a standard envelope.

### The NDJSON Event Envelope

Every JSON line has at minimum:

```json
{"event": "ready", "ts": "2026-04-30T14:00:00+00:00", "pid": 1234, "port": 8765}
```

- `event` — what happened (snake_case string)
- `ts` — ISO 8601 UTC timestamp
- Additional fields are event-specific kwargs

### Why This Design

- **NDJSON over JSON arrays**: processable line-by-line, one bad line doesn't break the stream, works with grep/jq, low memory for long-running processes
- **`--json` opt-in over default**: preserves human DX, doesn't break existing scripts or habits
- **Global mode flag over per-call checks**: set once at startup, every helper respects it automatically
- **`die()` over repeated if/else**: the pattern `if is_json(): json_error(); sys.exit(1) else: print(); sys.exit()` appears constantly — `die()` collapses it to one line

## The cli_utils.py Reference Implementation

When generating `cli_utils.py`, produce exactly this (adapt only if the project has specific needs):

```python
"""Shared helpers for JSON CLI output."""
import json
import os
import sys
from datetime import datetime, timezone

_json_mode = False

def enable_json():
    global _json_mode
    _json_mode = True

def is_json():
    return _json_mode

def json_log(event: str, **kwargs):
    """Emit one NDJSON line to stdout."""
    obj = {"event": event, "ts": datetime.now(timezone.utc).isoformat(), **kwargs}
    print(json.dumps(obj, default=str), flush=True)

def json_error(message: str, **kwargs):
    """Emit a structured error event."""
    json_log("error", message=message, **kwargs)

def die(message: str, code: int = 1, **kwargs):
    """Print error and exit — JSON or human depending on mode."""
    if _json_mode:
        json_error(message, **kwargs)
    else:
        print(message, file=sys.stderr)
    sys.exit(code)

def add_json_flag(parser):
    """Add --json flag to an argparse parser."""
    parser.add_argument("--json", action="store_true",
                        help="NDJSON output for agent consumption")

def log(message: str, **json_kwargs):
    """Print human message normally, or emit JSON event if --json is active."""
    if _json_mode:
        json_log(json_kwargs.pop("event", "info"), message=message, **json_kwargs)
    else:
        print(message)

def json_ready(**kwargs):
    """Emit the readiness signal — only in JSON mode. Call early in daemon startup."""
    if _json_mode:
        json_log("ready", pid=os.getpid(), **kwargs)
```

## Converting a Script — Step by Step

### Step 1: Scan for output points

Search the target script for all places that produce output or exit:

```bash
grep -n 'print(\|sys\.exit\|exit(\|input(\|os\.system.*say' TARGET.py
```

Categorize each hit:
- **Informational print** → replace with `log(message, event="descriptive_name")`
- **Error + exit** → replace with `die(message)`
- **Status line with \r** → replace with `if is_json(): json_log("status", ...) else: print("\r...", end="", flush=True)`
- **Interactive input()** → guard with `if not is_json():` or add `--no-interactive` flag
- **Side effects (say, osascript, notifications)** → guard with `if not is_json():`
- **Import-time errors** (before argparse runs) → use `sys.exit("message")` (writes to stderr)

### Step 2: Add the import and flag

At the top of the script, after existing imports:
```python
from cli_utils import add_json_flag, enable_json, is_json, json_log, log, die
```

In the `if __name__ == "__main__"` block, add to argparse:
```python
add_json_flag(parser)
args = parser.parse_args()
if args.json:
    enable_json()
```

### Step 3: Replace each output point

Apply the categorization from Step 1. Key patterns:

**Simple informational:**
```python
# Before
print(f"Connected to {device}")

# After
log(f"Connected to {device}", event="connected", device=device)
```

**Error + exit:**
```python
# Before
print("Device not found")
sys.exit(1)

# After
die("Device not found")
```

**Daemon readiness (first output after initialization):**
```python
# Before
print(f"Server running on port {port}")

# After — json_ready() only emits in JSON mode, so always call it + human fallback
json_ready(port=port)
log(f"Server running on port {port}", event="ready", port=port)
```

**Status lines (\r overwrite):**
```python
# Before
print(f"\r  HR {hr} RMSSD {rmssd:.1f}", end="", flush=True)

# After
if is_json():
    json_log("status", hr=hr, rmssd=rmssd)
else:
    print(f"\r  HR {hr} RMSSD {rmssd:.1f}", end="", flush=True)
```

**Human-only output (banners, usage examples):**
```python
if not is_json():
    print("Usage: send {\"type\": \"join\", \"name\": \"Alice\"}")
```

### Step 4: Verify

1. Run `python script.py --help` — confirm `--json` flag appears
2. Run `python script.py --json` — confirm first line is valid JSON
3. Grep for remaining raw `print(` calls — ensure each is guarded or intentional

## Event Name Conventions

Use snake_case, be descriptive, keep them grep-friendly:

| Category | Events |
|----------|--------|
| Lifecycle | `ready`, `shutdown`, `connected`, `disconnected` |
| Data | `hr`, `status`, `metric`, `heartbeat` |
| Errors | `error`, `retry` |
| Actions | `recording_started`, `recording_stopped`, `preset_change` |
| Progress | `scanning`, `connecting`, `downloading`, `importing` |

## Scaffolding an Open-Source Package

When the user wants a distributable package, scaffold this structure:

```
cli-utils-agent/
├── pyproject.toml
├── LICENSE                  # MIT by default, ask user
├── README.md
├── src/
│   └── cli_utils_agent/
│       ├── __init__.py      # re-exports all public API
│       └── core.py          # the implementation
├── tests/
│   ├── __init__.py
│   ├── test_json_log.py
│   ├── test_die.py
│   ├── test_log.py
│   └── test_add_json_flag.py
└── .github/
    └── workflows/
        └── test.yml         # CI with pytest
```

### `__init__.py` — re-export public API

```python
# src/cli_utils_agent/__init__.py
from .core import (
    enable_json, is_json, json_log, json_error, die,
    add_json_flag, log, json_ready,
)

__all__ = [
    "enable_json", "is_json", "json_log", "json_error", "die",
    "add_json_flag", "log", "json_ready",
]
```

### README.md template

Generate a README with: project name, one-line description, install instructions (`pip install cli-utils-agent`), quick usage example showing `add_json_flag` + `enable_json` + `log()`, API reference table listing all exports with one-line descriptions, and a link to the research background.

### pyproject.toml template

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cli-utils-agent"
version = "0.1.0"
description = "Add agent-friendly --json NDJSON output to any Python CLI"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Topic :: Software Development :: Libraries",
]

[project.urls]
Homepage = "https://github.com/USER/cli-utils-agent"

[tool.hatch.build.targets.wheel]
packages = ["src/cli_utils_agent"]
```

### Test suite

Use `capsys` for stdout capture, `pytest.raises(SystemExit)` for die(). Example:

```python
# tests/test_json_log.py
import json
from cli_utils_agent import json_log, enable_json, is_json

def test_json_log_writes_ndjson(capsys):
    json_log("ready", port=8765, pid=42)
    line = capsys.readouterr().out.strip()
    obj = json.loads(line)
    assert obj["event"] == "ready"
    assert obj["port"] == 8765
    assert "ts" in obj

# tests/test_die.py
import json
import pytest
from cli_utils_agent import die, enable_json
from cli_utils_agent import core as _core

def test_die_human_mode(capsys):
    _core._json_mode = False
    with pytest.raises(SystemExit) as exc:
        die("something broke")
    assert exc.value.code == 1
    assert "something broke" in capsys.readouterr().err

def test_die_json_mode(capsys):
    _core._json_mode = True
    try:
        with pytest.raises(SystemExit):
            die("something broke", code=10)
        obj = json.loads(capsys.readouterr().out.strip())
        assert obj["event"] == "error"
        assert obj["message"] == "something broke"
    finally:
        _core._json_mode = False
```

Cover: `json_log`, `json_error`, `die`, `log`, `add_json_flag`, `enable_json`/`is_json`, `json_ready`.

### GitHub Actions CI

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest -v
```

Add dev dependencies to pyproject.toml:
```toml
[project.optional-dependencies]
dev = ["pytest>=8.0"]
```

## Checklist — Run Before Declaring Done

After converting a script or creating a package:

- [ ] `--help` shows `--json` flag
- [ ] Running with `--json` produces valid NDJSON (every line is parseable JSON)
- [ ] First JSON line from daemons has `"event": "ready"`
- [ ] Error paths emit `"event": "error"` with non-zero exit code
- [ ] No raw `print()` can fire when `--json` is active
- [ ] Import-time errors (missing deps) use `sys.exit("message")` not `print()`
- [ ] Interactive prompts are guarded
- [ ] Side effects (voice, notifications) are guarded
- [ ] Human output is preserved when `--json` is NOT passed
- [ ] Unhandled exceptions don't leak tracebacks to stdout in JSON mode (wrap main in try/except, emit json_error)
- [ ] Tests pass (if package mode)
- [ ] Package builds cleanly: `python -m build` (if package mode)
- [ ] Install in clean venv and import works (if package mode)

## Further Reading

Read `references/best-practices.md` when you need:
- Heartbeat patterns for liveness detection (section 2.4)
- Exit code conventions and string error codes (section 2.3)
- Schema introspection with `--schema` (section 2.5)
- CLI vs MCP decision matrix (section 2.7)
- Token efficiency tips for agent consumption (section 5)
