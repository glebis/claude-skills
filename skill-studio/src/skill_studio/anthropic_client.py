# DEPRECATED: Use skill_studio.llm_provider.get_provider() instead.
# Kept for backwards compatibility only.
from __future__ import annotations
from typing import Any
import os
from anthropic import Anthropic


MODEL_DEFAULT = "claude-opus-4-7"


class AnthropicInterviewer:
    def __init__(self, system_prompt: str, client: Any | None = None, model: str = MODEL_DEFAULT):
        self.client = client or Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model
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
