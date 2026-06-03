"""Offline tests for confide:setup — no real pip installs, no real network/ollama.

All subprocess / urllib / importlib calls are monkeypatched so the suite runs with
zero real deps installed and never touches the network.
"""
import importlib
import importlib.util
import json
import os
import sys
import tempfile

import pytest

# import the setup script module directly
_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "skills", "setup", "scripts", "setup.py")
_spec = importlib.util.spec_from_file_location("confide_setup", _SCRIPT)
setup = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(setup)

# the shared core, for asserting against canonical DEFAULTS
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C


# ----------------------------------------------------------------- ensure_config
def test_write_config_produces_optimal_defaults():
    p = os.path.join(tempfile.mkdtemp(), "config.json")
    path = setup.ensure_config(reconfigure=False, path=p)
    assert path == p
    cfg = C.load_config(p)
    assert cfg["engine"] == "ollama"
    assert cfg["anon_model"] == "qwen2.5:3b"
    assert cfg["privacy"]["local_only"] is True
    assert cfg["layers"] == ["regex", "natasha", "llm"]
    # parseable raw JSON too
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    assert raw["redaction_style"] == "typed_placeholder"


def test_ensure_config_idempotent_does_not_clobber():
    p = os.path.join(tempfile.mkdtemp(), "config.json")
    setup.ensure_config(reconfigure=False, path=p)
    # user-customize the file
    cfg = C.load_config(p)
    cfg["anon_model"] = "qwen2.5:14b"
    C.write_config(cfg, p)
    # re-run without reconfigure -> must NOT overwrite
    setup.ensure_config(reconfigure=False, path=p)
    assert C.load_config(p)["anon_model"] == "qwen2.5:14b"


def test_reconfigure_overwrites():
    p = os.path.join(tempfile.mkdtemp(), "config.json")
    setup.ensure_config(reconfigure=False, path=p)
    cfg = C.load_config(p)
    cfg["anon_model"] = "qwen2.5:14b"
    C.write_config(cfg, p)
    # reconfigure -> back to defaults
    setup.ensure_config(reconfigure=True, path=p)
    assert C.load_config(p)["anon_model"] == "qwen2.5:3b"


# ----------------------------------------------------------------- readiness
def test_readiness_structure_all_false(monkeypatch):
    # no deps importable
    monkeypatch.setattr(setup.importlib.util, "find_spec", lambda name: None)
    # ollama unreachable
    monkeypatch.setattr(setup, "_http_get_json", lambda url, timeout=2: None)
    # no llama.cpp on PATH
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)

    r = setup.readiness(config_path="/nonexistent/confide/config.json")
    assert isinstance(r, dict)
    # required structured fields
    assert set(["deps", "ollama", "model", "llama", "config"]).issubset(r.keys())
    assert isinstance(r["deps"], dict)
    for pkg in ("natasha", "scrubadub", "phonenumbers", "pymorphy2"):
        assert r["deps"][pkg] is False
    assert r["ollama"] is False
    assert r["model"] is False
    assert r["llama"] is False
    assert r["config"] is False


def test_readiness_all_true(monkeypatch, tmp_path):
    monkeypatch.setattr(setup.importlib.util, "find_spec", lambda name: object())
    # ollama returns the anon model present
    monkeypatch.setattr(
        setup, "_http_get_json",
        lambda url, timeout=2: {"models": [{"name": "qwen2.5:3b"}]},
    )
    monkeypatch.setattr(setup.shutil, "which", lambda name: "/usr/local/bin/" + name)
    cfgp = tmp_path / "config.json"
    setup.ensure_config(reconfigure=False, path=str(cfgp))

    r = setup.readiness(config_path=str(cfgp))
    assert all(r["deps"].values())
    assert r["ollama"] is True
    assert r["model"] is True
    assert r["llama"] is True
    assert r["config"] is True


def test_readiness_model_absent_when_not_pulled(monkeypatch):
    monkeypatch.setattr(setup.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(
        setup, "_http_get_json",
        lambda url, timeout=2: {"models": [{"name": "llama3:8b"}]},
    )
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    r = setup.readiness(config_path="/nonexistent/config.json")
    assert r["ollama"] is True       # reachable
    assert r["model"] is False       # but anon_model not present


def test_readiness_no_pii_only_booleans(monkeypatch):
    monkeypatch.setattr(setup.importlib.util, "find_spec", lambda name: None)
    monkeypatch.setattr(setup, "_http_get_json", lambda url, timeout=2: None)
    monkeypatch.setattr(setup.shutil, "which", lambda name: None)
    r = setup.readiness(config_path="/nonexistent/config.json")
    # every leaf is a bool (no stray strings / paths / PII)
    flat = list(r["deps"].values()) + [r["ollama"], r["model"], r["llama"], r["config"]]
    assert all(isinstance(v, bool) for v in flat)


# ----------------------------------------------------------------- install (mocked)
def test_install_uses_subprocess_and_tolerates_failure(monkeypatch):
    calls = []

    def fake_run(cmd, *a, **k):
        calls.append(cmd)

        class R:
            returncode = 1  # simulate failure
        return R()

    monkeypatch.setattr(setup.subprocess, "run", fake_run)
    # ollama present so a pull is attempted
    monkeypatch.setattr(setup.shutil, "which", lambda name: "/usr/bin/ollama")
    # must not raise despite failures
    setup.install(with_presidio=False)
    assert calls, "install should invoke subprocess"
    # pip install of the core deps happened
    joined = " ".join(" ".join(map(str, c)) for c in calls)
    assert "natasha" in joined and "scrubadub" in joined
    assert "qwen2.5:3b" in joined  # ollama pull attempted
