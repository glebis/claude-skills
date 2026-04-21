from __future__ import annotations
import os
from typing import Protocol, Any


class LLMProvider(Protocol):
    system_prompt: str
    model: str

    def ask(self, history: list[dict], max_tokens: int = 600) -> str: ...


class AnthropicProvider:
    def __init__(self, system_prompt: str, client: Any | None = None, model: str | None = None):
        from anthropic import Anthropic
        self.client = client or Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")
        self.system_prompt = system_prompt

    def ask(self, history: list[dict], max_tokens: int = 600) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=[{
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=history,
        )
        for block in resp.content:
            if getattr(block, "text", None):
                return block.text
        return ""


class OpenRouterProvider:
    def __init__(self, system_prompt: str, client: Any | None = None, model: str | None = None):
        from openai import OpenAI
        self.client = client or OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = model or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-opus-4")
        self.system_prompt = system_prompt

    def ask(self, history: list[dict], max_tokens: int = 600) -> str:
        # Convert anthropic-style history [{"role":"user","content":"..."}] -> openai format
        # (same shape, just prepend system message)
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages,
        )
        return resp.choices[0].message.content or ""


def get_provider(system_prompt: str) -> LLMProvider:
    """Factory — picks provider from LLM_PROVIDER env (default: openrouter)."""
    provider = os.environ.get("LLM_PROVIDER", "openrouter").lower()
    if provider == "anthropic":
        return AnthropicProvider(system_prompt=system_prompt)
    elif provider == "openrouter":
        return OpenRouterProvider(system_prompt=system_prompt)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use 'anthropic' or 'openrouter'.")
