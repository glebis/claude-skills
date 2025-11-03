"""LLM execution logic for interactive and non-interactive modes."""

import subprocess
import sys
from typing import Optional


class LLMExecutor:
    """Handles execution of LLM CLI with various modes."""

    def __init__(self, model: str, provider: str = None):
        """
        Initialize executor.

        Args:
            model: Model name (e.g., 'gpt-4o', 'claude-sonnet-4.5')
            provider: Provider name (optional, can be inferred from model)
        """
        self.model = model
        self.provider = provider

    def execute_non_interactive(self, content: str) -> str:
        """
        Execute LLM in non-interactive mode (process input and return output).

        Args:
            content: Input text to process

        Returns:
            LLM output as string
        """
        if not content.strip():
            raise ValueError("No content provided")

        cmd = ["llm", self.model]

        try:
            result = subprocess.run(
                cmd,
                input=content,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"LLM execution failed: {result.stderr}"
                )

            return result.stdout

        except FileNotFoundError:
            raise RuntimeError(
                "llm CLI not found. Install with: pip install llm"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("LLM execution timed out after 5 minutes")

    def execute_interactive(self) -> None:
        """
        Execute LLM in interactive mode (conversation REPL).

        Starts an interactive conversation loop that continues until user exits.
        """
        cmd = ["llm", self.model]

        try:
            print(f"Starting interactive session with {self.model}...")
            print("Type 'exit', 'quit', or Ctrl+D to end conversation.\n")

            # Start the llm interactive process
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            try:
                while True:
                    # Read user input
                    try:
                        user_input = input("You: ").strip()
                    except EOFError:
                        break

                    if user_input.lower() in {"exit", "quit"}:
                        break

                    if not user_input:
                        continue

                    # Send to LLM and get response
                    try:
                        stdout, stderr = process.communicate(
                            input=user_input + "\n",
                            timeout=60,
                        )
                        if stdout:
                            print(f"Assistant: {stdout.strip()}\n")
                        if stderr:
                            print(f"Error: {stderr}", file=sys.stderr)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        print("Response timeout. Ending session.")
                        break

            finally:
                if process.poll() is None:
                    process.terminate()

        except FileNotFoundError:
            raise RuntimeError(
                "llm CLI not found. Install with: pip install llm"
            )
        except KeyboardInterrupt:
            print("\n\nSession ended.")

    def execute_with_prompt(self, prompt: str, content: str) -> str:
        """
        Execute LLM with a custom prompt and content.

        Args:
            prompt: System prompt or instruction
            content: Content to process

        Returns:
            LLM output as string
        """
        if not content.strip():
            raise ValueError("No content provided")

        # Combine prompt and content
        full_input = f"{prompt}\n\n{content}"

        return self.execute_non_interactive(full_input)

    @staticmethod
    def check_llm_installed() -> bool:
        """Check if llm CLI is installed."""
        try:
            subprocess.run(
                ["llm", "--version"],
                capture_output=True,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def get_llm_version() -> str | None:
        """Get installed llm CLI version."""
        try:
            result = subprocess.run(
                ["llm", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
