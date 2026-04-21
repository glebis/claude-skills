from __future__ import annotations
import getpass
import os
from pathlib import Path
from typing import Callable
import urllib.request

from skill_studio.sops_helper import encrypt_dotenv
from skill_studio import paths


DEFAULT_ENV_PATH = paths.env_file()
DEFAULT_PIPECAT_ENV = paths.pipecat_env_file()
DEFAULT_AGENCY_RAG_ENV = paths.import_env_file()


def _validate_gemini(key: str) -> bool:
    try:
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def run_setup(
    env_path: Path = DEFAULT_ENV_PATH,
    pipecat_env: Path = DEFAULT_PIPECAT_ENV,
    agency_rag_env: Path | None = DEFAULT_AGENCY_RAG_ENV,
    validate_gemini: Callable[[str], bool] = _validate_gemini,
    sops_helper=None,
) -> None:
    print("Welcome. I'll ask for a few keys and encrypt them locally.\n")

    if sops_helper is None:
        from skill_studio import sops_helper as _sh
        sops_helper = _sh

    entries: dict[str, str] = {}

    print("1. Gemini API key (image gen, nano-banana)")
    print("   Get one: https://aistudio.google.com/apikey")
    gemini = getpass.getpass("   Paste (hidden): ").strip()
    if not gemini:
        print("   Skipped.")
    else:
        print("   testing… ", end="")
        if validate_gemini(gemini):
            print("✓")
            entries["GEMINI_API_KEY"] = gemini
        else:
            print("✗ (bad key) — aborting")
            return

    print("\n2. OpenRouter API key (primary LLM provider — default for text + voice)")
    print("   Get one: https://openrouter.ai/keys")
    or_imported = False
    if agency_rag_env and agency_rag_env.exists():
        ans = input(f"   Found {agency_rag_env} — try to import OPENROUTER_API_KEY? [Y/n] ").strip().lower() or "y"
        if ans == "y":
            try:
                rag_env = sops_helper.decrypt_dotenv(agency_rag_env)
                if "OPENROUTER_API_KEY" in rag_env:
                    entries["OPENROUTER_API_KEY"] = rag_env["OPENROUTER_API_KEY"]
                    entries.setdefault("LLM_PROVIDER", "openrouter")
                    entries.setdefault("OPENROUTER_MODEL", "anthropic/claude-opus-4")
                    print(f"   ✓ imported from {agency_rag_env}")
                    or_imported = True
                else:
                    print(f"   OPENROUTER_API_KEY not found in {agency_rag_env}")
            except Exception as exc:
                print(f"   Could not decrypt {agency_rag_env}: {exc}")
    if not or_imported:
        key = getpass.getpass("   Paste (hidden): ").strip()
        if key:
            entries["OPENROUTER_API_KEY"] = key
            entries.setdefault("LLM_PROVIDER", "openrouter")
            entries.setdefault("OPENROUTER_MODEL", "anthropic/claude-opus-4")

    print("\n3. Anthropic API key (optional — only needed if you set LLM_PROVIDER=anthropic)")
    existing = os.environ.get("ANTHROPIC_API_KEY")
    if existing:
        ans = input(f"   Reuse from $ANTHROPIC_API_KEY? [y/N] ").strip().lower() or "n"
        if ans == "y":
            entries["ANTHROPIC_API_KEY"] = existing
            print("   ✓")
    if "ANTHROPIC_API_KEY" not in entries:
        key = getpass.getpass("   Paste (hidden, or Enter to skip): ").strip()
        if key:
            entries["ANTHROPIC_API_KEY"] = key

    print("\n4. Pipecat voice keys (Daily, Groq, Deepgram)")
    if pipecat_env.exists():
        ans = input(f"   Found {pipecat_env} — reuse? [Y/n] ").strip().lower() or "y"
        if ans == "y":
            for line in pipecat_env.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    entries[k.strip()] = v.strip()
            print("   ✓")

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(f"{k}={v}" for k, v in entries.items()) + "\n")
    print(f"\nEncrypting to {env_path} via sops…", end=" ")
    try:
        encrypt_dotenv(env_path)
        print("✓")
    except Exception as e:
        env_path.unlink(missing_ok=True)
        print(f"✗ {e}")
        raise

    print("Done. Run /skill-studio new to try it out.")
