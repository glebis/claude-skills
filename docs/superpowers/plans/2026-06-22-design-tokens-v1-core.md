# Design Tokens v1 Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic core of the `design-tokens` skill — a dependency-free Python package that validates, merges, resolves, and exports DTCG token files to CSS, plus a `tokens` CLI and a `SKILL.md`.

**Architecture:** A small Python package `dtokens` (stdlib only) with one module per responsibility (model, validate, merge, resolve, export_css, cli). A `tokens` shim invokes the CLI. The skill scaffolds/validates token files (`setup-edit`) and resolves them to CSS + an LLM-readable context file (`use`). This is v1 of a phased delivery; later phases add the interview door, Style Dictionary, importers, share, and skillify.

**Tech Stack:** Python 3 (stdlib only — `json`, `re`, `argparse`, `pathlib`, `datetime`), pytest 9 for tests.

## Global Constraints

- DTCG Format Module 2025.10 is the format. Files use `*.tokens.json` (house convention).
- Keys: `$value` required; `$type` resolved directly, by group inheritance, or from an alias target.
- v1 implements a **named deterministic DTCG subset**: whole-value `{alias}` references only — NO JSON Pointer `$ref`, NO `$root`, NO full name-restriction enforcement.
- Allowed `$type` values in v1: `color`, `dimension`, `duration`, `fontFamily`, `fontWeight`, `number`, `typography`, `shadow`.
- Color `$value` in v1 is a CSS color **string** (e.g. `#1A73E8`); structured color objects are deferred.
- `dimension`/`duration` `$value` is a `{ "value": <number>, "unit": <str> }` object.
- Global/project layering and theme-as-override-file are **skill conventions**, labelled as such in code comments — not DTCG behavior.
- Zero third-party runtime dependencies. Tests may use pytest only.
- All new code lives under `design-tokens/`.

---

## File Structure

- `design-tokens/scripts/dtokens/__init__.py` — package marker + `TokenError`
- `design-tokens/scripts/dtokens/model.py` — load, walk/index tokens, type resolution
- `design-tokens/scripts/dtokens/validate.py` — collect validation errors
- `design-tokens/scripts/dtokens/merge.py` — global-base ← project-override merge
- `design-tokens/scripts/dtokens/resolve.py` — flatten aliases to concrete values
- `design-tokens/scripts/dtokens/export_css.py` — serialize resolved tokens to CSS
- `design-tokens/scripts/dtokens/cli.py` — argparse dispatch (`main()`)
- `design-tokens/scripts/tokens` — executable shim
- `design-tokens/templates/base.tokens.json` — scaffold for `setup-edit`
- `design-tokens/tests/fixtures/*` — golden fixtures
- `design-tokens/tests/test_*.py` — unit + integration tests
- `design-tokens/SKILL.md` — skill entry doc

---

### Task 1: Package scaffold, model loading & type resolution

**Files:**
- Create: `design-tokens/scripts/dtokens/__init__.py`
- Create: `design-tokens/scripts/dtokens/model.py`
- Test: `design-tokens/tests/test_model.py`
- Create: `design-tokens/tests/__init__.py` (empty, makes tests importable)

**Interfaces:**
- Produces:
  - `TokenError(Exception)` in `dtokens/__init__.py`
  - `model.load(path: str) -> dict` — parse JSON file, raise `TokenError` on malformed JSON / missing file
  - `model.index(tree: dict) -> dict[str, dict]` — map dotted path → `{"node": dict, "inherited_type": str | None}` for every leaf token (a dict containing `$value`)
  - `model.is_alias(value) -> bool` — True if `value` is a string matching `^\{[^}]+\}$`
  - `model.alias_target(value: str) -> str` — return the dotted path inside the braces
  - `model.resolve_type(path: str, entry: dict, idx: dict) -> str | None` — declared `$type` → inherited group type → alias target's declared/inherited type; `None` if undeterminable

- [ ] **Step 1: Create the package marker with the error type**

Create `design-tokens/scripts/dtokens/__init__.py`:

```python
"""dtokens — deterministic DTCG (2025.10) subset core for the design-tokens skill."""


class TokenError(Exception):
    """Raised on malformed token files or unresolvable token graphs."""
```

Create an empty `design-tokens/tests/__init__.py`:

```python
```

- [ ] **Step 2: Write failing tests for model**

Create `design-tokens/tests/test_model.py`:

```python
import json

import pytest

from dtokens import TokenError
from dtokens import model


def test_load_parses_json(tmp_path):
    p = tmp_path / "x.tokens.json"
    p.write_text(json.dumps({"color": {"blue": {"$type": "color", "$value": "#00f"}}}))
    assert model.load(str(p)) == {"color": {"blue": {"$type": "color", "$value": "#00f"}}}


def test_load_raises_on_bad_json(tmp_path):
    p = tmp_path / "bad.tokens.json"
    p.write_text("{ not json ")
    with pytest.raises(TokenError):
        model.load(str(p))


def test_load_raises_on_missing_file(tmp_path):
    with pytest.raises(TokenError):
        model.load(str(tmp_path / "nope.tokens.json"))


def test_index_finds_leaf_tokens_and_inherits_group_type():
    tree = {
        "color": {
            "$type": "color",
            "blue": {"$value": "#00f"},
            "brand": {"primary": {"$value": "{color.blue}"}},
        },
        "space": {"sm": {"$type": "dimension", "$value": {"value": 8, "unit": "px"}}},
    }
    idx = model.index(tree)
    assert set(idx) == {"color.blue", "color.brand.primary", "space.sm"}
    assert idx["color.blue"]["inherited_type"] == "color"
    assert idx["color.brand.primary"]["inherited_type"] == "color"
    assert idx["space.sm"]["inherited_type"] is None


def test_is_alias_and_target():
    assert model.is_alias("{color.blue}") is True
    assert model.is_alias("#00f") is False
    assert model.is_alias({"value": 8, "unit": "px"}) is False
    assert model.alias_target("{color.brand.primary}") == "color.brand.primary"


def test_resolve_type_direct_inherited_and_via_alias():
    tree = {
        "color": {"$type": "color", "blue": {"$value": "#00f"}},
        "bg": {"main": {"$value": "{color.blue}"}},
    }
    idx = model.index(tree)
    assert model.resolve_type("color.blue", idx["color.blue"], idx) == "color"
    assert model.resolve_type("bg.main", idx["bg.main"], idx) == "color"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dtokens.model'`

- [ ] **Step 4: Implement `model.py`**

Create `design-tokens/scripts/dtokens/model.py`:

```python
"""Loading, indexing and type-resolution over a DTCG token tree.

A *token* is a dict containing the key ``$value``. A *group* is a dict without it.
Keys beginning with ``$`` are metadata, never children.
"""

import json
import re

from . import TokenError

_ALIAS_RE = re.compile(r"^\{([^}]+)\}$")


def load(path):
    """Parse a token file. Raise TokenError on missing file or invalid JSON."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise TokenError(f"token file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TokenError(f"invalid JSON in {path}: {exc}") from exc


def is_alias(value):
    """True if value is a whole-value alias string like ``{group.token}``."""
    return isinstance(value, str) and _ALIAS_RE.match(value) is not None


def alias_target(value):
    """Return the dotted path inside a ``{...}`` alias string."""
    m = _ALIAS_RE.match(value)
    if not m:
        raise TokenError(f"not an alias: {value!r}")
    return m.group(1)


def index(tree):
    """Map dotted path -> {'node': token_dict, 'inherited_type': str|None}."""
    out = {}

    def walk(node, prefix, inherited_type):
        local_type = node.get("$type", inherited_type)
        for key, child in node.items():
            if key.startswith("$"):
                continue
            if not isinstance(child, dict):
                continue
            path = f"{prefix}.{key}" if prefix else key
            if "$value" in child:
                out[path] = {"node": child, "inherited_type": inherited_type}
            else:
                walk(child, path, child.get("$type", local_type))

    walk(tree, "", None)
    return out


def resolve_type(path, entry, idx, _seen=None):
    """Resolve a token's $type: declared -> inherited -> alias target's type."""
    node = entry["node"]
    if "$type" in node:
        return node["$type"]
    if entry["inherited_type"] is not None:
        return entry["inherited_type"]
    value = node.get("$value")
    if is_alias(value):
        seen = _seen or set()
        if path in seen:
            return None
        seen.add(path)
        target = alias_target(value)
        if target in idx:
            return resolve_type(target, idx[target], idx, seen)
    return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_model.py -v`
Expected: PASS (6 passed)

- [ ] **Step 6: Commit**

```bash
git add design-tokens/scripts/dtokens/__init__.py design-tokens/scripts/dtokens/model.py design-tokens/tests/__init__.py design-tokens/tests/test_model.py
git commit -m "feat(design-tokens): model loading, indexing, type resolution"
```

---

### Task 2: Validation

**Files:**
- Create: `design-tokens/scripts/dtokens/validate.py`
- Test: `design-tokens/tests/test_validate.py`

**Interfaces:**
- Consumes: `model.index`, `model.resolve_type`, `model.is_alias`, `model.alias_target`
- Produces:
  - `validate.ALLOWED_TYPES: set[str]` = `{"color","dimension","duration","fontFamily","fontWeight","number","typography","shadow"}`
  - `validate.validate(tree: dict) -> list[str]` — return a list of human-readable error strings (empty list == valid). Collects ALL of: undeterminable type, type not in ALLOWED_TYPES, alias target not present, circular alias.

- [ ] **Step 1: Write failing tests**

Create `design-tokens/tests/test_validate.py`:

```python
from dtokens import validate


def test_valid_tree_returns_no_errors():
    tree = {
        "color": {
            "$type": "color",
            "blue": {"$value": "#00f"},
            "brand": {"$value": "{color.blue}"},
        }
    }
    assert validate.validate(tree) == []


def test_unknown_type_is_reported():
    tree = {"x": {"$type": "banana", "$value": "1"}}
    errors = validate.validate(tree)
    assert any("banana" in e and "x" in e for e in errors)


def test_undeterminable_type_is_reported():
    tree = {"x": {"$value": "whatever"}}
    errors = validate.validate(tree)
    assert any("type" in e.lower() and "x" in e for e in errors)


def test_dangling_alias_is_reported():
    tree = {"a": {"$type": "color", "$value": "{color.missing}"}}
    errors = validate.validate(tree)
    assert any("color.missing" in e for e in errors)


def test_circular_alias_is_reported():
    tree = {
        "a": {"$type": "color", "$value": "{b}"},
        "b": {"$type": "color", "$value": "{a}"},
    }
    errors = validate.validate(tree)
    assert any("circular" in e.lower() for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_validate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dtokens.validate'`

- [ ] **Step 3: Implement `validate.py`**

Create `design-tokens/scripts/dtokens/validate.py`:

```python
"""Collect validation errors over a DTCG token tree (v1 subset)."""

from . import model

ALLOWED_TYPES = {
    "color",
    "dimension",
    "duration",
    "fontFamily",
    "fontWeight",
    "number",
    "typography",
    "shadow",
}


def _detect_cycles(idx):
    errors = []
    for path, entry in idx.items():
        seen = []
        cur = path
        while True:
            node = idx[cur]["node"]
            value = node.get("$value")
            if not model.is_alias(value):
                break
            target = model.alias_target(value)
            if target not in idx:
                break  # dangling alias reported elsewhere
            if target in seen or target == path:
                errors.append(f"circular alias chain starting at {path}")
                break
            seen.append(target)
            cur = target
    return errors


def validate(tree):
    """Return a list of error strings; empty means the tree is valid."""
    idx = model.index(tree)
    errors = []

    for path, entry in idx.items():
        node = entry["node"]
        value = node.get("$value")

        if model.is_alias(value):
            target = model.alias_target(value)
            if target not in idx:
                errors.append(f"{path}: alias target {target} does not exist")

        ttype = model.resolve_type(path, entry, idx)
        if ttype is None:
            errors.append(f"{path}: cannot determine $type")
        elif ttype not in ALLOWED_TYPES:
            errors.append(f"{path}: $type {ttype!r} is not allowed in v1")

    errors.extend(_detect_cycles(idx))
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_validate.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add design-tokens/scripts/dtokens/validate.py design-tokens/tests/test_validate.py
git commit -m "feat(design-tokens): token validation with collected errors"
```

---

### Task 3: Merge (global base ← project override)

**Files:**
- Create: `design-tokens/scripts/dtokens/merge.py`
- Test: `design-tokens/tests/test_merge.py`

**Interfaces:**
- Produces:
  - `merge.merge(base: dict, override: dict) -> dict` — deep-merge two token trees. **Documented precedence (skill convention, not DTCG):** groups merge recursively; when a path is a leaf token (`$value` present) in `override`, it replaces the entire base token; metadata keys (`$type` etc.) at group level from `override` win. Pure function; does not mutate inputs; does not resolve aliases.

- [ ] **Step 1: Write failing tests**

Create `design-tokens/tests/test_merge.py`:

```python
import copy

from dtokens import merge


def test_override_replaces_whole_token():
    base = {"color": {"brand": {"$type": "color", "$value": "#000", "$description": "old"}}}
    override = {"color": {"brand": {"$type": "color", "$value": "#fff"}}}
    out = merge.merge(base, override)
    assert out["color"]["brand"] == {"$type": "color", "$value": "#fff"}


def test_different_paths_merge():
    base = {"color": {"a": {"$type": "color", "$value": "#000"}}}
    override = {"color": {"b": {"$type": "color", "$value": "#fff"}}}
    out = merge.merge(base, override)
    assert set(out["color"]) == {"a", "b"}


def test_base_token_survives_when_not_overridden():
    base = {"space": {"sm": {"$type": "dimension", "$value": {"value": 8, "unit": "px"}}}}
    override = {"color": {"x": {"$type": "color", "$value": "#fff"}}}
    out = merge.merge(base, override)
    assert out["space"]["sm"]["$value"] == {"value": 8, "unit": "px"}


def test_inputs_not_mutated():
    base = {"color": {"a": {"$type": "color", "$value": "#000"}}}
    override = {"color": {"a": {"$type": "color", "$value": "#fff"}}}
    base_snapshot = copy.deepcopy(base)
    merge.merge(base, override)
    assert base == base_snapshot
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_merge.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dtokens.merge'`

- [ ] **Step 3: Implement `merge.py`**

Create `design-tokens/scripts/dtokens/merge.py`:

```python
"""Layer a project-override tree on top of a global-base tree.

This layering is a *skill convention*, not DTCG ``$extends`` group inheritance.
Rule: a leaf token in the override replaces the whole base token at that path;
groups merge recursively.
"""

import copy


def _is_token(node):
    return isinstance(node, dict) and "$value" in node


def merge(base, override):
    """Return a new tree = base with override layered on top. Pure function."""
    result = copy.deepcopy(base)

    def recurse(dst, src):
        for key, src_val in src.items():
            if key in dst and isinstance(dst[key], dict) and isinstance(src_val, dict):
                if _is_token(src_val) or _is_token(dst[key]):
                    dst[key] = copy.deepcopy(src_val)  # token override replaces wholesale
                else:
                    recurse(dst[key], src_val)
            else:
                dst[key] = copy.deepcopy(src_val)

    recurse(result, override)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_merge.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add design-tokens/scripts/dtokens/merge.py design-tokens/tests/test_merge.py
git commit -m "feat(design-tokens): global-base / project-override merge"
```

---

### Task 4: Resolve (flatten aliases to concrete values)

**Files:**
- Create: `design-tokens/scripts/dtokens/resolve.py`
- Test: `design-tokens/tests/test_resolve.py`

**Interfaces:**
- Consumes: `model.index`, `model.resolve_type`, `model.is_alias`, `model.alias_target`, `TokenError`
- Produces:
  - `resolve.resolve(tree: dict) -> dict[str, dict]` — return `{dotted_path: {"type": str, "value": <concrete>}}` with every alias replaced by its concrete value. Raise `TokenError` on circular alias, dangling alias, or undeterminable type.

- [ ] **Step 1: Write failing tests**

Create `design-tokens/tests/test_resolve.py`:

```python
import pytest

from dtokens import TokenError
from dtokens import resolve


def test_resolves_direct_values():
    tree = {"color": {"$type": "color", "blue": {"$value": "#00f"}}}
    out = resolve.resolve(tree)
    assert out["color.blue"] == {"type": "color", "value": "#00f"}


def test_resolves_alias_chain_and_inherits_type():
    tree = {
        "color": {"$type": "color", "blue": {"$value": "#00f"}},
        "action": {"primary": {"$value": "{color.blue}"}},
        "button": {"bg": {"$value": "{action.primary}"}},
    }
    out = resolve.resolve(tree)
    assert out["button.bg"] == {"type": "color", "value": "#00f"}


def test_circular_alias_raises():
    tree = {
        "a": {"$type": "color", "$value": "{b}"},
        "b": {"$type": "color", "$value": "{a}"},
    }
    with pytest.raises(TokenError):
        resolve.resolve(tree)


def test_dangling_alias_raises():
    tree = {"a": {"$type": "color", "$value": "{nope}"}}
    with pytest.raises(TokenError):
        resolve.resolve(tree)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_resolve.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dtokens.resolve'`

- [ ] **Step 3: Implement `resolve.py`**

Create `design-tokens/scripts/dtokens/resolve.py`:

```python
"""Flatten a token tree to concrete values, resolving aliases after merge."""

from . import TokenError
from . import model


def resolve(tree):
    """Return {path: {'type': str, 'value': concrete}} with aliases resolved."""
    idx = model.index(tree)
    resolved = {}
    resolving = set()

    def resolve_one(path):
        if path in resolved:
            return resolved[path]
        if path in resolving:
            raise TokenError(f"circular alias at {path}")
        if path not in idx:
            raise TokenError(f"unknown token {path}")
        resolving.add(path)
        node = idx[path]["node"]
        value = node["$value"]
        if model.is_alias(value):
            target = model.alias_target(value)
            target_resolved = resolve_one(target)
            concrete = target_resolved["value"]
            ttype = node.get("$type") or idx[path]["inherited_type"] or target_resolved["type"]
        else:
            concrete = value
            ttype = model.resolve_type(path, idx[path], idx)
            if ttype is None:
                raise TokenError(f"cannot determine $type for {path}")
        resolving.discard(path)
        resolved[path] = {"type": ttype, "value": concrete}
        return resolved[path]

    for path in idx:
        resolve_one(path)
    return resolved
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_resolve.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add design-tokens/scripts/dtokens/resolve.py design-tokens/tests/test_resolve.py
git commit -m "feat(design-tokens): alias resolution to concrete values"
```

---

### Task 5: Export to CSS (per-type serialization)

**Files:**
- Create: `design-tokens/scripts/dtokens/export_css.py`
- Test: `design-tokens/tests/test_export_css.py`

**Interfaces:**
- Consumes: `TokenError`
- Produces:
  - `export_css.css_var_name(path: str, suffix: str = "") -> str` — `"color.brand.primary"` → `"--color-brand-primary"`; with suffix `"font-size"` → `"--type-body-font-size"` style
  - `export_css.serialize_value(ttype: str, value) -> str | dict[str, str]` — scalar types return a CSS string; `typography` returns a dict of `{sub-name: css-string}` for composite expansion; `shadow` returns one `box-shadow` string. Raise `TokenError` on unsupported shapes (e.g. structured color object).
  - `export_css.export_css(resolved: dict, selector: str = ":root") -> str` — full CSS block. Composite tokens expand to multiple custom properties using the documented suffix scheme.

**Documented serialization rules (v1):**
- `color`: value is a string → emitted verbatim.
- `dimension` / `duration`: value is `{value, unit}` → `f"{value}{unit}"`.
- `fontFamily`: string → verbatim; list → comma-joined.
- `fontWeight` / `number`: → `str(value)`.
- `typography`: object with keys `fontFamily`, `fontSize`, `fontWeight`, `lineHeight` → expands to `--<name>-font-family`, `--<name>-font-size`, `--<name>-font-weight`, `--<name>-line-height`.
- `shadow`: object `{offsetX, offsetY, blur, spread, color}` (each dimension a `{value,unit}` or color string) → `"<offsetX> <offsetY> <blur> <spread> <color>"`.

- [ ] **Step 1: Write failing tests**

Create `design-tokens/tests/test_export_css.py`:

```python
import pytest

from dtokens import TokenError
from dtokens import export_css


def test_var_name():
    assert export_css.css_var_name("color.brand.primary") == "--color-brand-primary"
    assert export_css.css_var_name("type.body", "font-size") == "--type-body-font-size"


def test_serialize_scalar_types():
    assert export_css.serialize_value("color", "#00f") == "#00f"
    assert export_css.serialize_value("dimension", {"value": 8, "unit": "px"}) == "8px"
    assert export_css.serialize_value("duration", {"value": 200, "unit": "ms"}) == "200ms"
    assert export_css.serialize_value("fontFamily", ["Inter", "sans-serif"]) == "Inter, sans-serif"
    assert export_css.serialize_value("fontWeight", 600) == "600"


def test_serialize_typography_expands():
    out = export_css.serialize_value(
        "typography",
        {
            "fontFamily": "Inter",
            "fontSize": {"value": 16, "unit": "px"},
            "fontWeight": 400,
            "lineHeight": 1.5,
        },
    )
    assert out == {
        "font-family": "Inter",
        "font-size": "16px",
        "font-weight": "400",
        "line-height": "1.5",
    }


def test_serialize_shadow():
    out = export_css.serialize_value(
        "shadow",
        {
            "offsetX": {"value": 0, "unit": "px"},
            "offsetY": {"value": 2, "unit": "px"},
            "blur": {"value": 4, "unit": "px"},
            "spread": {"value": 0, "unit": "px"},
            "color": "#0003",
        },
    )
    assert out == "0px 2px 4px 0px #0003"


def test_structured_color_object_raises():
    with pytest.raises(TokenError):
        export_css.serialize_value("color", {"colorSpace": "srgb", "components": [0, 0, 1]})


def test_export_css_full_block():
    resolved = {
        "color.brand": {"type": "color", "value": "#00f"},
        "type.body": {
            "type": "typography",
            "value": {
                "fontFamily": "Inter",
                "fontSize": {"value": 16, "unit": "px"},
                "fontWeight": 400,
                "lineHeight": 1.5,
            },
        },
    }
    css = export_css.export_css(resolved)
    assert ":root {" in css
    assert "  --color-brand: #00f;" in css
    assert "  --type-body-font-size: 16px;" in css
    assert "  --type-body-line-height: 1.5;" in css
    assert css.rstrip().endswith("}")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_export_css.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dtokens.export_css'`

- [ ] **Step 3: Implement `export_css.py`**

Create `design-tokens/scripts/dtokens/export_css.py`:

```python
"""Serialize resolved tokens to CSS custom properties (v1 type rules)."""

from . import TokenError

_TYPO_KEYS = [
    ("fontFamily", "font-family"),
    ("fontSize", "font-size"),
    ("fontWeight", "font-weight"),
    ("lineHeight", "line-height"),
]


def css_var_name(path, suffix=""):
    base = "--" + path.replace(".", "-")
    return f"{base}-{suffix}" if suffix else base


def _dimension(value):
    if not (isinstance(value, dict) and "value" in value and "unit" in value):
        raise TokenError(f"expected {{value, unit}} dimension, got {value!r}")
    return f"{value['value']}{value['unit']}"


def serialize_value(ttype, value):
    if ttype == "color":
        if not isinstance(value, str):
            raise TokenError(f"v1 supports string colors only, got {value!r}")
        return value
    if ttype in ("dimension", "duration"):
        return _dimension(value)
    if ttype == "fontFamily":
        return ", ".join(value) if isinstance(value, list) else str(value)
    if ttype in ("fontWeight", "number"):
        return str(value)
    if ttype == "typography":
        out = {}
        for key, css_key in _TYPO_KEYS:
            if key not in value:
                continue
            sub = value[key]
            if key == "fontSize":
                out[css_key] = _dimension(sub)
            elif key == "fontFamily":
                out[css_key] = ", ".join(sub) if isinstance(sub, list) else str(sub)
            else:
                out[css_key] = str(sub)
        return out
    if ttype == "shadow":
        parts = [
            _dimension(value["offsetX"]),
            _dimension(value["offsetY"]),
            _dimension(value["blur"]),
            _dimension(value["spread"]),
            value["color"],
        ]
        return " ".join(parts)
    raise TokenError(f"unsupported $type for CSS export: {ttype}")


def export_css(resolved, selector=":root"):
    lines = [f"{selector} {{"]
    for path in sorted(resolved):
        entry = resolved[path]
        serialized = serialize_value(entry["type"], entry["value"])
        if isinstance(serialized, dict):
            for css_key, css_val in serialized.items():
                lines.append(f"  {css_var_name(path, css_key)}: {css_val};")
        else:
            lines.append(f"  {css_var_name(path)}: {serialized};")
    lines.append("}")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_export_css.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add design-tokens/scripts/dtokens/export_css.py design-tokens/tests/test_export_css.py
git commit -m "feat(design-tokens): CSS export with per-type serialization"
```

---

### Task 6: CLI, shim, template & golden integration test

**Files:**
- Create: `design-tokens/scripts/dtokens/cli.py`
- Create: `design-tokens/scripts/tokens`
- Create: `design-tokens/templates/base.tokens.json`
- Create: `design-tokens/tests/fixtures/global.base.tokens.json`
- Create: `design-tokens/tests/fixtures/project.override.tokens.json`
- Create: `design-tokens/tests/fixtures/expected.tokens.css`
- Test: `design-tokens/tests/test_cli.py`

**Interfaces:**
- Consumes: all of `model`, `validate`, `merge`, `resolve`, `export_css`
- Produces:
  - `cli.main(argv: list[str] | None = None) -> int` — argparse dispatch; returns process exit code (0 ok, 1 validation/error).
  - Subcommands:
    - `validate <file>` — print errors or `OK`; exit 1 if invalid.
    - `merge <base> <override> [-o OUT]` — write/print merged JSON.
    - `resolve <file> [-o OUT]` — write/print resolved JSON map.
    - `export-css <file> [--selector SEL] [-o OUT]` — write/print CSS.
    - `setup-edit <dest>` — copy `templates/base.tokens.json` to `<dest>`, then validate it; refuse to overwrite an existing file.
    - `use <file> [--out-dir DIR]` — validate, resolve, write `tokens.css` and `tokens.context.md` into `--out-dir` (default `<file dir>/resolved`).

- [ ] **Step 1: Write the template and fixtures**

Create `design-tokens/templates/base.tokens.json`:

```json
{
  "color": {
    "$type": "color",
    "blue-600": { "$value": "#1A73E8" },
    "ink-900": { "$value": "#0B0B0C" },
    "action": { "primary": { "$value": "{color.blue-600}" } }
  },
  "space": {
    "$type": "dimension",
    "sm": { "$value": { "value": 8, "unit": "px" } },
    "md": { "$value": { "value": 16, "unit": "px" } }
  },
  "type": {
    "body": {
      "$type": "typography",
      "$value": {
        "fontFamily": "Inter",
        "fontSize": { "value": 16, "unit": "px" },
        "fontWeight": 400,
        "lineHeight": 1.5
      }
    }
  }
}
```

Create `design-tokens/tests/fixtures/global.base.tokens.json`:

```json
{
  "color": {
    "$type": "color",
    "blue-600": { "$value": "#1A73E8" },
    "action": { "primary": { "$value": "{color.blue-600}" } }
  },
  "space": {
    "$type": "dimension",
    "sm": { "$value": { "value": 8, "unit": "px" } }
  }
}
```

Create `design-tokens/tests/fixtures/project.override.tokens.json`:

```json
{
  "color": {
    "blue-600": { "$type": "color", "$value": "#2563EB" }
  }
}
```

Create `design-tokens/tests/fixtures/expected.tokens.css` (note: `action.primary` aliases `blue-600`, which the override changes to `#2563EB`; keys are emitted sorted):

```css
:root {
  --color-action-primary: #2563EB;
  --color-blue-600: #2563EB;
  --space-sm: 8px;
}
```

- [ ] **Step 2: Write failing CLI tests**

Create `design-tokens/tests/test_cli.py`:

```python
import json
import pathlib

from dtokens import cli

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_validate_ok(capsys):
    rc = cli.main(["validate", str(FIXTURES / "global.base.tokens.json")])
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_validate_reports_errors(tmp_path, capsys):
    bad = tmp_path / "bad.tokens.json"
    bad.write_text(json.dumps({"a": {"$type": "color", "$value": "{missing}"}}))
    rc = cli.main(["validate", str(bad)])
    assert rc == 1
    assert "missing" in capsys.readouterr().out


def test_merge_then_export_matches_golden(tmp_path):
    merged = tmp_path / "merged.tokens.json"
    cli.main([
        "merge",
        str(FIXTURES / "global.base.tokens.json"),
        str(FIXTURES / "project.override.tokens.json"),
        "-o", str(merged),
    ])
    out_css = tmp_path / "out.css"
    cli.main(["export-css", str(merged), "-o", str(out_css)])
    expected = (FIXTURES / "expected.tokens.css").read_text()
    assert out_css.read_text() == expected


def test_setup_edit_scaffolds_and_validates(tmp_path, capsys):
    dest = tmp_path / "new.tokens.json"
    rc = cli.main(["setup-edit", str(dest)])
    assert rc == 0
    assert dest.exists()
    assert "color" in json.loads(dest.read_text())


def test_setup_edit_refuses_overwrite(tmp_path):
    dest = tmp_path / "exists.tokens.json"
    dest.write_text("{}")
    rc = cli.main(["setup-edit", str(dest)])
    assert rc == 1


def test_use_writes_css_and_context(tmp_path):
    rc = cli.main([
        "use",
        str(FIXTURES / "global.base.tokens.json"),
        "--out-dir", str(tmp_path),
    ])
    assert rc == 0
    assert (tmp_path / "tokens.css").exists()
    context = (tmp_path / "tokens.context.md").read_text()
    assert "color.action.primary" in context
    assert "#1A73E8" in context
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dtokens.cli'`

- [ ] **Step 4: Implement `cli.py`**

Create `design-tokens/scripts/dtokens/cli.py`:

```python
"""Command-line dispatch for the design-tokens v1 core."""

import argparse
import json
import pathlib

from . import TokenError
from . import export_css as export_css_mod
from . import merge as merge_mod
from . import model
from . import resolve as resolve_mod
from . import validate as validate_mod

_TEMPLATE = pathlib.Path(__file__).resolve().parents[2] / "templates" / "base.tokens.json"


def _emit(text, out):
    if out:
        pathlib.Path(out).write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def _cmd_validate(args):
    errors = validate_mod.validate(model.load(args.file))
    if errors:
        for e in errors:
            print(e)
        return 1
    print("OK")
    return 0


def _cmd_merge(args):
    merged = merge_mod.merge(model.load(args.base), model.load(args.override))
    _emit(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", args.out)
    return 0


def _cmd_resolve(args):
    resolved = resolve_mod.resolve(model.load(args.file))
    _emit(json.dumps(resolved, indent=2, ensure_ascii=False) + "\n", args.out)
    return 0


def _cmd_export_css(args):
    resolved = resolve_mod.resolve(model.load(args.file))
    _emit(export_css_mod.export_css(resolved, args.selector), args.out)
    return 0


def _cmd_setup_edit(args):
    dest = pathlib.Path(args.dest)
    if dest.exists():
        print(f"refusing to overwrite existing file: {dest}")
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    errors = validate_mod.validate(model.load(str(dest)))
    if errors:
        for e in errors:
            print(e)
        return 1
    print(f"scaffolded {dest}")
    return 0


def _context_md(source, resolved):
    lines = [
        f"# Design tokens: {pathlib.Path(source).stem}",
        "",
        f"Resolved from `{source}`. {len(resolved)} tokens.",
        "",
        "| Token | Type | Value |",
        "| --- | --- | --- |",
    ]
    for path in sorted(resolved):
        entry = resolved[path]
        value = json.dumps(entry["value"], ensure_ascii=False) if isinstance(entry["value"], (dict, list)) else entry["value"]
        lines.append(f"| {path} | {entry['type']} | {value} |")
    return "\n".join(lines) + "\n"


def _cmd_use(args):
    tree = model.load(args.file)
    errors = validate_mod.validate(tree)
    if errors:
        for e in errors:
            print(e)
        return 1
    resolved = resolve_mod.resolve(tree)
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else pathlib.Path(args.file).parent / "resolved"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "tokens.css").write_text(export_css_mod.export_css(resolved), encoding="utf-8")
    (out_dir / "tokens.context.md").write_text(_context_md(args.file, resolved), encoding="utf-8")
    print(f"wrote {out_dir / 'tokens.css'} and {out_dir / 'tokens.context.md'}")
    return 0


def _build_parser():
    p = argparse.ArgumentParser(prog="tokens", description="design-tokens v1 core")
    sub = p.add_subparsers(dest="command", required=True)

    sv = sub.add_parser("validate")
    sv.add_argument("file")
    sv.set_defaults(func=_cmd_validate)

    sm = sub.add_parser("merge")
    sm.add_argument("base")
    sm.add_argument("override")
    sm.add_argument("-o", "--out")
    sm.set_defaults(func=_cmd_merge)

    sr = sub.add_parser("resolve")
    sr.add_argument("file")
    sr.add_argument("-o", "--out")
    sr.set_defaults(func=_cmd_resolve)

    se = sub.add_parser("export-css")
    se.add_argument("file")
    se.add_argument("--selector", default=":root")
    se.add_argument("-o", "--out")
    se.set_defaults(func=_cmd_export_css)

    ss = sub.add_parser("setup-edit")
    ss.add_argument("dest")
    ss.set_defaults(func=_cmd_setup_edit)

    su = sub.add_parser("use")
    su.add_argument("file")
    su.add_argument("--out-dir")
    su.set_defaults(func=_cmd_use)

    return p


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TokenError as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Create the executable shim**

Create `design-tokens/scripts/tokens`:

```python
#!/usr/bin/env python3
"""Entry shim so `scripts/tokens <cmd>` works without PYTHONPATH gymnastics."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dtokens.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
```

Then make it executable:

Run: `chmod +x design-tokens/scripts/tokens`

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/test_cli.py -v`
Expected: PASS (6 passed)

- [ ] **Step 7: Smoke-test the shim end to end**

Run: `cd design-tokens && ./scripts/tokens export-css tests/fixtures/global.base.tokens.json`
Expected: prints a `:root { ... }` block including `--color-blue-600: #1A73E8;`

- [ ] **Step 8: Commit**

```bash
git add design-tokens/scripts/dtokens/cli.py design-tokens/scripts/tokens design-tokens/templates/base.tokens.json design-tokens/tests/fixtures design-tokens/tests/test_cli.py
git commit -m "feat(design-tokens): CLI, shim, template and golden integration test"
```

---

### Task 7: SKILL.md

**Files:**
- Create: `design-tokens/SKILL.md`

**Interfaces:**
- Consumes: the `tokens` CLI verbs from Task 6.
- Produces: the skill's trigger description and usage doc. No code.

- [ ] **Step 1: Write `SKILL.md`**

Create `design-tokens/SKILL.md`:

```markdown
---
name: design-tokens
description: This skill should be used to set up, validate, resolve, and export design tokens following the DTCG (Design Tokens Community Group) Format Module 2025.10 standard. Use when the user wants to define a design token set globally or per project, compile tokens to CSS variables, layer a project's tokens over a global brand base, or produce an on-brand context file for other generation skills. Triggers on "set up design tokens", "create a token set", "compile tokens to CSS", "design system variables", "brand tokens".
---

# Design Tokens

Manage [DTCG 2025.10](https://www.designtokens.org/tr/drafts/format/) design tokens
with a dependency-free Python core. v1 covers the deterministic spine: scaffold,
validate, merge (global base + project override), resolve aliases, and export CSS.

## Standard vs convention

- **Standard (DTCG):** `*.tokens.json`, `$value`/`$type`, whole-value `{alias}` references.
- **Skill convention (NOT DTCG):** global-base / project-override layering via `merge`,
  and theme-as-override-file. These are labelled in code; do not present them as standard.

## v1 scope

Supported `$type`: `color` (string values), `dimension`, `duration`, `fontFamily`,
`fontWeight`, `number`, `typography`, `shadow`. Not in v1: JSON Pointer `$ref`, `$root`,
structured color objects, name-restriction enforcement, Style Dictionary, importers,
share bundles, `skillify` (see the phased spec).

## Commands

Run via `scripts/tokens <command>` (or `PYTHONPATH=scripts python3 -m dtokens.cli`):

| Command | What it does |
| --- | --- |
| `setup-edit <dest>` | Scaffold a template token file at `<dest>` and validate it (refuses to overwrite). |
| `validate <file>` | Print `OK` or a list of errors; exit 1 if invalid. |
| `merge <base> <override> [-o OUT]` | Layer project override on global base. |
| `resolve <file> [-o OUT]` | Flatten aliases to concrete values (JSON map). |
| `export-css <file> [--selector SEL] [-o OUT]` | Emit CSS custom properties. |
| `use <file> [--out-dir DIR]` | Validate + resolve, then write `tokens.css` and `tokens.context.md`. |

## Storage convention

- Global sets: `~/.claude/design-tokens/<set>/base.tokens.json`
- Project deltas: `<project>/.design-tokens/project.tokens.json` (override of a global set)
- Multiple themes (light/dark): keep one override file per theme and merge it before `use`.

## Tests

`cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/ -v`
```

- [ ] **Step 2: Verify the full test suite passes**

Run: `cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/ -v`
Expected: PASS (all tasks' tests, ~25 passed)

- [ ] **Step 3: Commit**

```bash
git add design-tokens/SKILL.md
git commit -m "docs(design-tokens): add SKILL.md for v1 core"
```

---

## Self-Review

**Spec coverage:**
- DTCG standard (`$value`/`$type`/`{alias}`, `*.tokens.json`) → Tasks 1, 6 (template), 7.
- `$type` resolution (direct/inherited/alias) → Task 1 `resolve_type`.
- v1 type cut incl. fontFamily/fontWeight/number → Tasks 2 (ALLOWED_TYPES), 5 (serialization).
- Deterministic core verbs validate/merge/resolve/export-css → Tasks 2-5.
- Documented merge precedence (skill convention) → Task 3 docstring + tests.
- Explicit CSS serialization + composite naming → Task 5 + golden fixture (Task 6).
- `setup edit` door + `use` (CSS + Claude context file) → Task 6.
- "named deterministic DTCG subset, no $ref/$root" → Global Constraints + SKILL.md.
- Phasing (v1 only) → this plan covers v1; later phases excluded by design.

**Placeholder scan:** No TBD/TODO; every code step contains complete, runnable code.

**Type consistency:** `model.index` returns `{"node", "inherited_type"}` and is consumed
with those exact keys in validate/resolve. `resolve.resolve` returns `{path: {"type","value"}}`,
consumed unchanged by `export_css.export_css` and `cli`. `serialize_value` returns str|dict,
handled by `export_css` for both branches. CLI subcommand funcs all return int exit codes.

Gaps: none identified for v1 scope.
```
