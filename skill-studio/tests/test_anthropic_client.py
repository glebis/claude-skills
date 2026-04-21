from unittest.mock import MagicMock
from skill_studio.anthropic_client import AnthropicInterviewer


def test_ask_returns_text(monkeypatch):
    fake_message = MagicMock()
    fake_message.content = [MagicMock(text="What's the core pain?")]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_message

    interviewer = AnthropicInterviewer(client=fake_client, system_prompt="sys")
    out = interviewer.ask(history=[{"role": "user", "content": "hi"}])
    assert out == "What's the core pain?"
    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert isinstance(call_kwargs["system"], list)
    assert call_kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
