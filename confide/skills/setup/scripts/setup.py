#!/usr/bin/env python3
"""confide:setup — local-first install + optimal-default config writer.

Subcommands (argparse main is thin; the logic lives in importable functions):
  --check (default)  report readiness without installing (no PII, booleans only)
  --install          pip-install deps + `ollama pull` the anon model (tolerates failure)
  --write-config     write ~/.config/confide/config.json from confide_core.DEFAULTS if absent
  --reconfigure      overwrite the config with defaults
  --show             print the current config

Everything runs locally. Readiness emits only booleans (no transcript text, no PII).
"""
import argparse
import importlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import urllib.request

# --- import the shared core: scripts live at skills/setup/scripts/, so shared is ../../../shared
_HERE = os.path.dirname(os.path.abspath(__file__))
_SHARED = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "shared"))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)
import confide_core as C  # noqa: E402

# core deps (pkg_resources via setuptools<81 needed by pymorphy2)
CORE_PIP = [
    "natasha",
    "scrubadub",
    "phonenumbers",
    "pymorphy2",
    "pymorphy2-dicts-ru",
    "setuptools<81",
]
OPTIONAL_PIP = ["presidio-analyzer"]
# importable module names to probe for readiness
DEP_MODULES = ["natasha", "scrubadub", "phonenumbers", "pymorphy2"]


# ----------------------------------------------------------------- helpers
def _http_get_json(url, timeout=2):
    """GET url and parse JSON; return None on any failure (no exceptions escape)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "confide-setup"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


def _dep_present(module_name):
    """True if an importable module is available (without importing it)."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


# ----------------------------------------------------------------- readiness
def readiness(config_path=C.CONFIG_PATH):
    """Structured readiness check. Returns a dict of booleans only — never any PII.

    Fields:
      deps:   {module: bool} for natasha/scrubadub/phonenumbers/pymorphy2
      ollama: bool — is Ollama reachable (GET <host>/api/tags)
      model:  bool — is the configured anon_model present in Ollama's tag list
      llama:  bool — is `llama-cli`/`llama.cpp` on PATH (optional engine)
      config: bool — does the config file exist
    """
    cfg = C.load_config(config_path)
    host = cfg.get("ollama_host", "http://localhost:11434").rstrip("/")
    anon_model = cfg.get("anon_model", "qwen2.5:3b")

    deps = {m: _dep_present(m) for m in DEP_MODULES}

    tags = _http_get_json(host + "/api/tags", timeout=2)
    ollama = tags is not None
    model = False
    if ollama and isinstance(tags, dict):
        names = [m.get("name", "") for m in tags.get("models", []) or []]
        model = any(n == anon_model or n.split(":")[0] == anon_model.split(":")[0] and n == anon_model
                    for n in names) or anon_model in names

    llama = bool(shutil.which("llama-cli") or shutil.which("llama.cpp") or shutil.which("llama-server"))

    config = os.path.isfile(config_path)

    return {"deps": deps, "ollama": ollama, "model": model, "llama": llama, "config": config}


# ----------------------------------------------------------------- config
def ensure_config(reconfigure=False, path=C.CONFIG_PATH):
    """Write the optimal-default config from confide_core.DEFAULTS.

    Idempotent: if the file exists and reconfigure is False, leave it untouched.
    Returns the config path.
    """
    if os.path.isfile(path) and not reconfigure:
        return path
    return C.write_config(dict(C.DEFAULTS), path)


def show_config(path=C.CONFIG_PATH):
    """Return the current config dict (merged over defaults)."""
    return C.load_config(path)


# ----------------------------------------------------------------- install
def install(with_presidio=False):
    """Best-effort: pip-install deps and pull the Ollama model. Tolerates failures.

    Returns a dict of step -> bool (success). Never raises on subprocess errors.
    """
    results = {}
    pip_pkgs = list(CORE_PIP)
    if with_presidio:
        pip_pkgs += OPTIONAL_PIP

    cmd = [sys.executable, "-m", "pip", "install", *pip_pkgs]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        results["pip"] = getattr(r, "returncode", 1) == 0
    except Exception:
        results["pip"] = False

    anon_model = C.load_config().get("anon_model", "qwen2.5:3b")
    if shutil.which("ollama"):
        try:
            r = subprocess.run(["ollama", "pull", anon_model], capture_output=True, text=True)
            results["ollama_pull"] = getattr(r, "returncode", 1) == 0
        except Exception:
            results["ollama_pull"] = False
    else:
        results["ollama_pull"] = False

    return results


# ----------------------------------------------------------------- reporting
def _render_readiness(r):
    def mark(b):
        return "✓" if b else "✗"

    lines = ["confide readiness (local-first; booleans only, no PII):"]
    lines.append("  python deps:")
    for m, ok in r["deps"].items():
        lines.append(f"    {mark(ok)} {m}")
    lines.append(f"  {mark(r['ollama'])} ollama reachable")
    lines.append(f"  {mark(r['model'])} anon_model pulled")
    lines.append(f"  {mark(r['llama'])} llama.cpp on PATH (optional)")
    lines.append(f"  {mark(r['config'])} config present")
    return "\n".join(lines)


# ----------------------------------------------------------------- main (thin)
def main(argv=None):
    p = argparse.ArgumentParser(prog="confide-setup", description="confide:setup — local de-id install + config")
    p.add_argument("--check", action="store_true", help="report readiness without installing (default)")
    p.add_argument("--install", action="store_true", help="pip-install deps + pull the Ollama model")
    p.add_argument("--with-presidio", action="store_true", help="also install presidio-analyzer (EN baseline)")
    p.add_argument("--write-config", action="store_true", help="write config if absent")
    p.add_argument("--reconfigure", action="store_true", help="overwrite config with defaults")
    p.add_argument("--show", action="store_true", help="print current config")
    p.add_argument("--config", default=C.CONFIG_PATH, help="config path")
    args = p.parse_args(argv)

    did = False

    if args.install:
        did = True
        print("Installing deps (best-effort, local)...")
        res = install(with_presidio=args.with_presidio)
        for step, ok in res.items():
            print(f"  {'✓' if ok else '✗'} {step}")

    if args.write_config or args.reconfigure:
        did = True
        path = ensure_config(reconfigure=args.reconfigure, path=args.config)
        print(f"config: {path}")
    elif not os.path.isfile(args.config):
        # first run with no config present: write the optimal defaults
        path = ensure_config(reconfigure=False, path=args.config)
        print(f"config written: {path}")

    if args.show:
        did = True
        print(json.dumps(show_config(args.config), ensure_ascii=False, indent=2))

    # default action / always show readiness on --check or when nothing else asked
    if args.check or not did:
        print(_render_readiness(readiness(config_path=args.config)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
