"""Provider detection and configuration management."""

import json
import os
import subprocess
import sys
from pathlib import Path


class ConfigManager:
    """Manages persistent configuration for the skill."""

    CONFIG_PATH = Path.home() / ".claude" / "llm-skill-config.json"

    def __init__(self):
        """Initialize config manager."""
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load config from file or create default."""
        if self.CONFIG_PATH.exists():
            try:
                with open(self.CONFIG_PATH) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "last_model": None,
            "last_provider": None,
            "available_providers": [],
            "auto_detect": True,
        }

    def save(self) -> None:
        """Save config to file."""
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)

    def get_last_model(self) -> str | None:
        """Get last used model."""
        return self.config.get("last_model")

    def set_last_model(self, model: str, provider: str) -> None:
        """Save last used model."""
        self.config["last_model"] = model
        self.config["last_provider"] = provider
        self.save()

    def get_available_providers(self) -> list[str]:
        """Get list of available providers."""
        return self.config.get("available_providers", [])

    def set_available_providers(self, providers: list[str]) -> None:
        """Save list of available providers."""
        self.config["available_providers"] = providers
        self.save()


class ProviderDetector:
    """Detects available LLM providers via environment variables."""

    ENV_VARS = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "ollama": "OLLAMA_BASE_URL",
    }

    @staticmethod
    def detect_providers() -> dict[str, bool]:
        """Detect available providers from environment variables."""
        available = {}

        for provider, env_var in ProviderDetector.ENV_VARS.items():
            available[provider] = bool(os.getenv(env_var))

        # Special check for ollama: can run without env var if local
        if not available["ollama"]:
            available["ollama"] = ProviderDetector._check_ollama_running()

        return available

    @staticmethod
    def _check_ollama_running() -> bool:
        """Check if Ollama is running locally."""
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available providers."""
        available = ProviderDetector.detect_providers()
        return [provider for provider, is_available in available.items() if is_available]

    @staticmethod
    def suggest_providers_setup(available: list[str]) -> None:
        """Suggest setting up providers for the first run."""
        if not available:
            print("❌ No LLM providers detected!")
            print("\nTo use this skill, you need to set up at least one provider:")
            print("\n1. OpenAI:")
            print("   export OPENAI_API_KEY='sk-...'")
            print("\n2. Anthropic:")
            print("   export ANTHROPIC_API_KEY='sk-ant-...'")
            print("\n3. Google Gemini:")
            print("   export GOOGLE_API_KEY='...'")
            print("\n4. Ollama (local):")
            print("   - Install from https://ollama.ai")
            print("   - Run: ollama serve")
            return

        print("✅ Available LLM Providers:")
        for provider in available:
            print(f"   • {provider.capitalize()}")

        missing = [p for p in ProviderDetector.ENV_VARS.keys() if p not in available]
        if missing:
            print(f"\nYou can also set up: {', '.join(missing)}")
            print("\n5. Groq (free, fast Llama models):")
            print("   export GROQ_API_KEY='...'")
            print("   Get key from: https://console.groq.com/keys")
            print("\n6. OpenRouter (unified API for 200+ models):")
            print("   export OPENROUTER_API_KEY='sk-or-...'")
            print("   Get key from: https://openrouter.ai")
