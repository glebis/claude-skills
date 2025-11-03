#!/usr/bin/env python3
"""Main LLM CLI Skill - Orchestrates model selection and execution."""

import argparse
import sys
from pathlib import Path

from executor import LLMExecutor
from input_handler import InputHandler
from models import PROVIDER_ALIASES, get_model, get_models_by_provider, resolve_provider_alias
from providers import ConfigManager, ProviderDetector


class LLMSkill:
    """Main skill orchestrator for LLM CLI integration."""

    def __init__(self):
        """Initialize the skill."""
        self.config = ConfigManager()
        self.detector = ProviderDetector()

    def select_model(self, identifier: str = None) -> tuple[str, str]:
        """
        Select model based on identifier or user choice.

        Args:
            identifier: Model name, alias, or provider name

        Returns:
            Tuple of (model_name, provider)
        """
        # If no identifier, use last model
        if not identifier:
            last_model = self.config.get_last_model()
            if last_model:
                return last_model, self.config.config.get("last_provider", "")
            # Fall back to interactive selection
            return self._interactive_model_selection()

        # Try to resolve as a model
        model_config = get_model(identifier)
        if model_config:
            return identifier, model_config["provider"]

        # Try to resolve as a provider alias
        provider = resolve_provider_alias(identifier)
        if provider:
            # Get available models for this provider
            models = get_models_by_provider(provider)
            if not models:
                print(f"❌ No models found for provider: {provider}")
                return self._interactive_model_selection()

            if len(models) == 1:
                model_name = models[0][0]
                return model_name, provider

            # Multiple models, show menu
            return self._show_model_menu(models, provider)

        # Unknown identifier, show menu
        return self._interactive_model_selection()

    def _interactive_model_selection(self) -> tuple[str, str]:
        """Show interactive model selection menu."""
        available_providers = self.detector.get_available_providers()

        if not available_providers:
            print("❌ No LLM providers available!")
            self.detector.suggest_providers_setup([])
            sys.exit(1)

        print("Available Providers:")
        for i, provider in enumerate(available_providers, 1):
            print(f"  {i}. {provider.capitalize()}")

        try:
            choice = int(input("Select provider (number): "))
            if 1 <= choice <= len(available_providers):
                provider = available_providers[choice - 1]
                return self._select_model_for_provider(provider)
        except (ValueError, IndexError):
            pass

        print("Invalid choice. Using first available provider.")
        return self._select_model_for_provider(available_providers[0])

    def _select_model_for_provider(self, provider: str) -> tuple[str, str]:
        """Select model from a specific provider."""
        models = get_models_by_provider(provider)

        if not models:
            print(f"❌ No models found for provider: {provider}")
            return self._interactive_model_selection()

        return self._show_model_menu(models, provider)

    def _show_model_menu(self, models: list, provider: str) -> tuple[str, str]:
        """Display model selection menu."""
        print(f"\nAvailable {provider.capitalize()} Models:")
        for i, (name, config) in enumerate(models, 1):
            desc = config.get("description", "")
            print(f"  {i}. {name} - {desc}")

        try:
            choice = int(input(f"Select model (1-{len(models)}): "))
            if 1 <= choice <= len(models):
                model_name = models[choice - 1][0]
                return model_name, provider
        except (ValueError, IndexError):
            pass

        print("Invalid choice. Using first model.")
        return models[0][0], provider

    def run(self, args=None) -> None:
        """
        Main entry point for the skill.

        Args:
            args: Command-line arguments
        """
        parser = self._build_parser()
        parsed = parser.parse_args(args)

        # Handle setup mode
        if parsed.setup:
            self._setup_mode()
            return

        # Check if llm CLI is installed
        if not LLMExecutor.check_llm_installed():
            print("❌ llm CLI not found!")
            print("Install with: pip install llm")
            sys.exit(1)

        # Load or select model
        model, provider = self.select_model(parsed.model)
        self.config.set_last_model(model, provider)

        # Load input
        content, source = InputHandler.load_input(parsed.prompt)

        if not content and not parsed.interactive:
            print("❌ No input provided and not in interactive mode")
            parser.print_help()
            sys.exit(1)

        # Execute
        executor = LLMExecutor(model, provider)

        try:
            if parsed.interactive:
                executor.execute_interactive()
            else:
                output = executor.execute_non_interactive(content)
                print(output, end="")
        except RuntimeError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    def _setup_mode(self) -> None:
        """Run setup to detect and display available providers."""
        print("🔍 Scanning for available LLM providers...\n")

        available = self.detector.get_available_providers()
        self.config.set_available_providers(available)

        self.detector.suggest_providers_setup(available)

        if available:
            print("\n✅ Configuration saved to ~/.claude/llm-skill-config.json")

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="Process text with LLM CLI",
            prog="llm",
        )

        parser.add_argument(
            "prompt",
            nargs="?",
            default=None,
            help="Text prompt or file path to process",
        )

        parser.add_argument(
            "-m",
            "--model",
            default=None,
            help="Model name or alias (e.g., gpt-4o, claude-opus)",
        )

        parser.add_argument(
            "-i",
            "--interactive",
            action="store_true",
            help="Start interactive conversation mode",
        )

        parser.add_argument(
            "--setup",
            action="store_true",
            help="Detect and configure available providers",
        )

        parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 1.0.0",
        )

        return parser


def main():
    """Entry point when run as a script."""
    skill = LLMSkill()
    skill.run()


if __name__ == "__main__":
    main()
