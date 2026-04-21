"""Interactive first-run wizard. Walks a new user through prereq checks,
data-home selection, encryption mode, LLM/voice provider setup, and prints
a shell-rc snippet with the env vars they need exported.

Wraps the narrower `setup.run_setup` (which only handles key entry via sops).
The wizard falls back to plaintext dotenv when sops is unavailable."""
from __future__ import annotations
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

from skill_studio import paths


# ---------------------------------------------------------------------------
# Prereqs
# ---------------------------------------------------------------------------

def check_python() -> tuple[bool, str]:
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 11)
    return ok, f"Python {major}.{minor} ({'ok' if ok else 'need 3.11+'})"


def check_sops() -> tuple[bool, str]:
    path = shutil.which("sops")
    if not path:
        return False, "sops: not found on PATH"
    return True, f"sops: {path}"


def check_age_key() -> tuple[bool, str]:
    """age key is needed for sops. Accept either SOPS_AGE_KEY_FILE or the
    standard ~/.config/sops/age/keys.txt location."""
    env = os.environ.get("SOPS_AGE_KEY_FILE")
    if env and Path(env).expanduser().exists():
        return True, f"age key: {env}"
    default = Path.home() / ".config/sops/age/keys.txt"
    if default.exists():
        return True, f"age key: {default}"
    return False, "age key: not found (SOPS_AGE_KEY_FILE unset; ~/.config/sops/age/keys.txt missing)"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    ans = input(f"{label}{suffix}: ").strip()
    return ans or default


def _prompt_yn(label: str, default: bool = True) -> bool:
    marker = "Y/n" if default else "y/N"
    ans = input(f"{label} [{marker}]: ").strip().lower()
    if not ans:
        return default
    return ans.startswith("y")


def _prompt_choice(label: str, choices: list[str], default: str) -> str:
    shown = "/".join(c if c != default else c.upper() for c in choices)
    while True:
        ans = input(f"{label} ({shown}): ").strip().lower() or default
        if ans in choices:
            return ans
        print(f"  pick one of: {', '.join(choices)}")


# ---------------------------------------------------------------------------
# Env writing
# ---------------------------------------------------------------------------

def _write_plaintext_env(path: Path, entries: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"{k}={v}" for k, v in entries.items()) + "\n"
    path.write_text(body)
    path.chmod(0o600)


def _write_sops_env(path: Path, entries: dict[str, str]) -> None:
    from skill_studio.sops_helper import encrypt_dotenv
    _write_plaintext_env(path, entries)
    encrypt_dotenv(path)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def _smoke_test() -> bool:
    """Run `pytest -q` inside the project. Returns True on pass."""
    root = Path(__file__).resolve().parents[2]
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header", "-x"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception as e:
        print(f"  smoke test could not run: {e}")
        return False
    if r.returncode == 0:
        last = r.stdout.strip().splitlines()[-1] if r.stdout else ""
        print(f"  ✓ {last}")
        return True
    print(r.stdout[-500:])
    print(r.stderr[-500:])
    return False


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

BANNER = """
╭─────────────────────────────────────────────╮
│  skill-studio — first-run setup wizard      │
╰─────────────────────────────────────────────╯
"""


def run_init_wizard(
    input_fn: Callable[[str], str] | None = None,
) -> int:
    """Return 0 on success, non-zero on abort."""
    # input_fn injection is for tests; default module uses builtin input.
    if input_fn is not None:
        global input
        input = input_fn  # type: ignore[assignment]

    print(BANNER)

    # 1. Prereqs
    print("Checking prerequisites…")
    py_ok, py_msg = check_python()
    sops_ok, sops_msg = check_sops()
    age_ok, age_msg = check_age_key()
    for ok, msg in [(py_ok, py_msg), (sops_ok, sops_msg), (age_ok, age_msg)]:
        print(f"  {'✓' if ok else '·'} {msg}")

    if not py_ok:
        print("\nPython 3.11+ is required. Aborting.")
        return 1

    # 2. Data home
    print("\n— Data location —")
    current_home = os.environ.get("SKILL_STUDIO_HOME") or str(paths.home())
    data_home = Path(_prompt("Data home (sessions + cache)", current_home)).expanduser()
    data_home.mkdir(parents=True, exist_ok=True)
    (data_home / "sessions").mkdir(exist_ok=True)
    print(f"  ✓ {data_home}")

    # 3. Encryption mode
    print("\n— Secrets storage —")
    sops_available = sops_ok and age_ok
    if sops_available:
        encrypt = _prompt_yn("Encrypt provider keys with sops?", default=True)
    else:
        print("  sops unavailable — secrets will be stored in plaintext (chmod 600).")
        print("  Install sops + age to enable encryption later: https://github.com/getsops/sops")
        encrypt = False
    env_file = Path(_prompt(
        "Env file path",
        os.environ.get("SKILL_STUDIO_ENV_FILE") or str(paths.env_file()),
    )).expanduser()

    # 4. LLM provider
    print("\n— LLM provider —")
    provider = _prompt_choice(
        "Provider",
        ["openrouter", "anthropic", "skip"],
        default="openrouter",
    )
    entries: dict[str, str] = {}
    if provider == "openrouter":
        key = getpass.getpass("  OPENROUTER_API_KEY (hidden, Enter to skip): ").strip()
        if key:
            entries["OPENROUTER_API_KEY"] = key
            entries["LLM_PROVIDER"] = "openrouter"
            entries["OPENROUTER_MODEL"] = _prompt(
                "  OpenRouter model", "anthropic/claude-opus-4"
            )
    elif provider == "anthropic":
        key = getpass.getpass("  ANTHROPIC_API_KEY (hidden, Enter to skip): ").strip()
        if key:
            entries["ANTHROPIC_API_KEY"] = key
            entries["LLM_PROVIDER"] = "anthropic"
    else:
        print("  Skipped — text mode inside Claude Code still works without a provider key.")

    # 5. Voice mode
    print("\n— Voice mode —")
    want_voice = _prompt_yn("Enable voice mode? (needs Daily / Groq / Deepgram)", default=False)
    if want_voice:
        for k, label in [
            ("DAILY_API_KEY", "Daily API key"),
            ("GROQ_API_KEY", "Groq API key"),
            ("DEEPGRAM_API_KEY", "Deepgram API key"),
        ]:
            v = getpass.getpass(f"  {label} (hidden): ").strip()
            if v:
                entries[k] = v
        entries.setdefault("DEEPGRAM_VOICE", "aura-asteria-en")

    # 6. Write env file
    if entries:
        print(f"\nWriting env file to {env_file} ({'sops-encrypted' if encrypt else 'plaintext'})…")
        try:
            if encrypt:
                _write_sops_env(env_file, entries)
            else:
                _write_plaintext_env(env_file, entries)
            print("  ✓")
        except Exception as e:
            print(f"  ✗ {e}")
            return 2
    else:
        print("\nNo keys captured — skipping env file write.")

    # 7. Shell rc snippet
    print("\n— Shell configuration —")
    lines = [
        f'export SKILL_STUDIO_HOME="{data_home}"',
        f'export SKILL_STUDIO_ENV_FILE="{env_file}"',
    ]
    print("Add these to your shell rc (~/.zshrc, ~/.bashrc, etc.):\n")
    for line in lines:
        print(f"  {line}")

    # 8. Smoke test
    print("\n— Smoke test —")
    if _prompt_yn("Run test suite to verify install?", default=True):
        ok = _smoke_test()
        if not ok:
            print("  tests failed — check output above")

    print("\nDone. Try: skill-studio new --preset ai-agent --depth sprint")
    return 0
