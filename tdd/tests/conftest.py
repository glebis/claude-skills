"""Shared fixtures for TDD skill script tests."""

import os
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def scripts_dir():
    return SCRIPTS_DIR


@pytest.fixture
def python_project():
    return FIXTURES_DIR / "python_project"


@pytest.fixture
def ts_project():
    return FIXTURES_DIR / "ts_project"


@pytest.fixture
def go_project():
    return FIXTURES_DIR / "go_project"


@pytest.fixture
def empty_project():
    return FIXTURES_DIR / "empty_project"


@pytest.fixture
def tmp_project(tmp_path):
    """A writable temp directory for tests that need to create files."""
    return tmp_path
