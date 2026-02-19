"""Snapshot tests for agent prompt templates.

Renders each agent prompt (Test Writer, Implementer, Refactorer) with
known sample variables and compares against stored snapshots. Catches
accidental regressions in prompt templates without any LLM calls.

Update snapshots: pytest tests/test_prompts.py --snapshot-update
"""

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
PROMPTS_FILE = SKILL_DIR / "references" / "agent_prompts.md"
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


# ── Template parsing ────────────────────────────────────────────────


def load_prompt_templates():
    """Extract agent prompt templates from agent_prompts.md."""
    content = PROMPTS_FILE.read_text()

    templates = {}
    # Match ``` blocks that follow "## <Agent Name> Agent" headers
    pattern = r"## (Test Writer|Implementer|Refactorer) Agent.*?```\n(.*?)```"
    for match in re.finditer(pattern, content, re.DOTALL):
        name = match.group(1).lower().replace(" ", "_")
        templates[name] = match.group(2).strip()

    return templates


def render_template(template, variables):
    """Substitute {VARIABLE} placeholders and handle {?SECTION}...{/SECTION}."""
    result = template

    # Handle optional sections: {?SECTION}...{/SECTION}
    # Include section content if variable exists and is non-empty
    optional_pattern = r"\{(\?[A-Z_]+)\}(.*?)\{/([A-Z_]+)\}"
    for match in re.finditer(optional_pattern, result, re.DOTALL):
        section_open = match.group(1)  # e.g. ?DOC_CONTEXT
        section_body = match.group(2)
        section_close = match.group(3)  # e.g. DOC_CONTEXT
        var_name = section_open[1:]  # strip leading ?

        if var_name in variables and variables[var_name]:
            # Include the section with variables substituted
            rendered_body = section_body
            for k, v in variables.items():
                rendered_body = rendered_body.replace(f"{{{k}}}", v)
            result = result.replace(match.group(0), rendered_body.strip())
        else:
            # Remove the entire optional section
            result = result.replace(match.group(0), "")

    # Substitute remaining {VARIABLE} placeholders
    for k, v in variables.items():
        result = result.replace(f"{{{k}}}", v)

    return result.strip()


# ── Sample variables for each agent ─────────────────────────────────

TEST_WRITER_VARS = {
    "SLICE_SPEC": "User email validation: should reject emails without @ symbol",
    "LANGUAGE": "python",
    "FRAMEWORK": "pytest",
    "API_SURFACE": (
        "# Python API Surface\n"
        "## src/models.py\n"
        "  5:class User:\n"
        "  10:def validate_email(self) -> bool:\n"
    ),
    "DOC_CONTEXT": (
        "# Project Documentation\n"
        "## README.md\n"
        "User model validates email format on creation.\n"
        "# Source Docstrings\n"
        "## models.py\n"
        "  User: Represents a user in the system.\n"
        "  validate_email: Check if email contains @ symbol.\n"
    ),
    "TEST_FILE_PATH": "tests/test_user.py",
    "EXISTING_TEST_CONTENT": "No test file exists yet.",
    "FRAMEWORK_SKELETON": (
        "def test_should_behavior():\n"
        "    # Arrange\n"
        "    ...\n"
        "    # Act\n"
        "    result = function_under_test()\n"
        "    # Assert\n"
        "    assert result == expected\n"
    ),
    "LAYER": "domain",
    "LAYER_TEST_CONSTRAINTS": (
        "Write tests using only domain types. NO database mocks, NO HTTP mocks, "
        "NO file system. Test pure business logic through public methods. "
        "Construct real domain objects directly — never mock them."
    ),
}

IMPLEMENTER_VARS = {
    "LANGUAGE": "python",
    "FAILING_TEST_CODE": (
        "def test_should_reject_email_without_at():\n"
        "    user = User(name='Test', email='invalid')\n"
        "    assert user.validate_email() is False\n"
    ),
    "TEST_FAILURE_OUTPUT": (
        "FAILED tests/test_user.py::test_should_reject_email_without_at\n"
        "ModuleNotFoundError: No module named 'src.models'\n"
    ),
    "FILE_TREE": "src/\nsrc/models.py\nsrc/__init__.py\n",
    "EXISTING_SOURCE": (
        "# src/models.py\n"
        "class User:\n"
        "    pass\n"
    ),
    "LAYER": "domain",
    "LAYER_DEPENDENCY_CONSTRAINT": (
        "This is the innermost layer. It MUST NOT import anything from "
        "domain-service, application, or infrastructure layers. No ORM imports, "
        "no HTTP clients, no framework imports. Only standard library and domain types."
    ),
    "PREVIOUS_ATTEMPT": "",
    "PREVIOUS_ATTEMPT_DESCRIPTION": "",
    "PREVIOUS_ATTEMPT_ERROR": "",
}

REFACTORER_VARS = {
    "LANGUAGE": "python",
    "GREEN_TEST_OUTPUT": (
        "======================== 2 passed in 0.03s ========================\n"
    ),
    "ALL_TEST_CODE": (
        "def test_should_reject_email_without_at():\n"
        "    user = User(name='Test', email='invalid')\n"
        "    assert user.validate_email() is False\n\n"
        "def test_should_accept_valid_email():\n"
        "    user = User(name='Test', email='test@example.com')\n"
        "    assert user.validate_email() is True\n"
    ),
    "ALL_IMPLEMENTATION_CODE": (
        "class User:\n"
        "    def __init__(self, name: str, email: str):\n"
        "        self.name = name\n"
        "        self.email = email\n\n"
        "    def validate_email(self) -> bool:\n"
        "        return '@' in self.email\n"
    ),
    "SLICE_LAYERS": "domain",
}


# ── Snapshot management ─────────────────────────────────────────────


def read_snapshot(name):
    path = SNAPSHOTS_DIR / f"{name}.txt"
    if path.exists():
        return path.read_text()
    return None


def write_snapshot(name, content):
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOTS_DIR / f"{name}.txt"
    path.write_text(content)


# ── Tests ───────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def templates():
    return load_prompt_templates()


@pytest.fixture
def update_snapshots(request):
    return request.config.getoption("--snapshot-update", default=False)


def pytest_addoption(parser):
    parser.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Update prompt snapshots",
    )


class TestPromptTemplatesParsing:
    def test_loads_three_templates(self, templates):
        assert "test_writer" in templates
        assert "implementer" in templates
        assert "refactorer" in templates

    def test_templates_not_empty(self, templates):
        for name, tmpl in templates.items():
            assert len(tmpl) > 100, f"{name} template too short"

    def test_test_writer_has_required_placeholders(self, templates):
        tmpl = templates["test_writer"]
        required = [
            "{SLICE_SPEC}",
            "{LANGUAGE}",
            "{FRAMEWORK}",
            "{API_SURFACE}",
            "{TEST_FILE_PATH}",
            "{LAYER}",
        ]
        for placeholder in required:
            assert placeholder in tmpl, f"Missing {placeholder} in test_writer"

    def test_implementer_has_required_placeholders(self, templates):
        tmpl = templates["implementer"]
        required = [
            "{LANGUAGE}",
            "{FAILING_TEST_CODE}",
            "{TEST_FAILURE_OUTPUT}",
            "{FILE_TREE}",
            "{LAYER}",
        ]
        for placeholder in required:
            assert placeholder in tmpl, f"Missing {placeholder} in implementer"

    def test_refactorer_has_required_placeholders(self, templates):
        tmpl = templates["refactorer"]
        required = [
            "{LANGUAGE}",
            "{GREEN_TEST_OUTPUT}",
            "{ALL_TEST_CODE}",
            "{ALL_IMPLEMENTATION_CODE}",
            "{SLICE_LAYERS}",
        ]
        for placeholder in required:
            assert placeholder in tmpl, f"Missing {placeholder} in refactorer"

    def test_test_writer_has_doc_context_section(self, templates):
        tmpl = templates["test_writer"]
        assert "{?DOC_CONTEXT}" in tmpl or "DOC_CONTEXT" in tmpl


class TestPromptRendering:
    def test_test_writer_renders_without_unresolved_vars(self, templates):
        rendered = render_template(templates["test_writer"], TEST_WRITER_VARS)
        # No unresolved {VARIABLE} patterns (except JSON examples like {"test_code":...)
        unresolved = re.findall(r"\{[A-Z][A-Z_]+\}", rendered)
        assert not unresolved, f"Unresolved variables: {unresolved}"

    def test_implementer_renders_without_unresolved_vars(self, templates):
        rendered = render_template(templates["implementer"], IMPLEMENTER_VARS)
        unresolved = re.findall(r"\{[A-Z][A-Z_]+\}", rendered)
        assert not unresolved, f"Unresolved variables: {unresolved}"

    def test_refactorer_renders_without_unresolved_vars(self, templates):
        rendered = render_template(templates["refactorer"], REFACTORER_VARS)
        unresolved = re.findall(r"\{[A-Z][A-Z_]+\}", rendered)
        assert not unresolved, f"Unresolved variables: {unresolved}"

    def test_doc_context_included_when_present(self, templates):
        rendered = render_template(templates["test_writer"], TEST_WRITER_VARS)
        assert "Project Documentation" in rendered
        assert "validate_email" in rendered

    def test_doc_context_omitted_when_empty(self, templates):
        vars_no_docs = {**TEST_WRITER_VARS, "DOC_CONTEXT": ""}
        rendered = render_template(templates["test_writer"], vars_no_docs)
        assert "Project Documentation" not in rendered

    def test_previous_attempt_omitted_when_empty(self, templates):
        rendered = render_template(templates["implementer"], IMPLEMENTER_VARS)
        assert "Previous attempt" not in rendered

    def test_previous_attempt_included_when_present(self, templates):
        vars_with_retry = {
            **IMPLEMENTER_VARS,
            "PREVIOUS_ATTEMPT": "yes",
            "PREVIOUS_ATTEMPT_DESCRIPTION": "Tried adding @property",
            "PREVIOUS_ATTEMPT_ERROR": "AttributeError: can't set attribute",
        }
        rendered = render_template(templates["implementer"], vars_with_retry)
        assert "Tried adding @property" in rendered


class TestPromptSnapshots:
    """Compare rendered prompts against stored snapshots.

    Run with --snapshot-update to regenerate snapshots.
    """

    def _check_snapshot(self, name, rendered, update_snapshots):
        existing = read_snapshot(name)
        if existing is None or update_snapshots:
            write_snapshot(name, rendered)
            if existing is None:
                pytest.skip(f"Snapshot {name} created (first run)")
        else:
            assert rendered == existing, (
                f"Prompt snapshot '{name}' changed. "
                f"Run with --snapshot-update to accept changes."
            )

    def test_test_writer_snapshot(self, templates, update_snapshots):
        rendered = render_template(templates["test_writer"], TEST_WRITER_VARS)
        self._check_snapshot("test_writer", rendered, update_snapshots)

    def test_implementer_snapshot(self, templates, update_snapshots):
        rendered = render_template(templates["implementer"], IMPLEMENTER_VARS)
        self._check_snapshot("implementer", rendered, update_snapshots)

    def test_refactorer_snapshot(self, templates, update_snapshots):
        rendered = render_template(templates["refactorer"], REFACTORER_VARS)
        self._check_snapshot("refactorer", rendered, update_snapshots)
