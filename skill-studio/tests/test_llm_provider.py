from unittest.mock import MagicMock
import pytest


def test_openrouter_provider_ask(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="test answer"))]
    )
    from skill_studio.llm_provider import OpenRouterProvider
    p = OpenRouterProvider(system_prompt="sys", client=fake_client, model="anthropic/claude-opus-4")
    out = p.ask(history=[{"role": "user", "content": "hi"}])
    assert out == "test answer"
    # Verify system was prepended
    call = fake_client.chat.completions.create.call_args
    assert call.kwargs["messages"][0] == {"role": "system", "content": "sys"}


def test_openrouter_provider_history_preserved(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="reply"))]
    )
    from skill_studio.llm_provider import OpenRouterProvider
    p = OpenRouterProvider(system_prompt="sys", client=fake_client, model="m")
    history = [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
    ]
    p.ask(history=history)
    call = fake_client.chat.completions.create.call_args
    msgs = call.kwargs["messages"]
    assert msgs[0]["role"] == "system"
    assert msgs[1:] == history


def test_openrouter_provider_empty_content(monkeypatch):
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=None))]
    )
    from skill_studio.llm_provider import OpenRouterProvider
    p = OpenRouterProvider(system_prompt="sys", client=fake_client, model="m")
    out = p.ask(history=[{"role": "user", "content": "hi"}])
    assert out == ""


def test_factory_default_is_openrouter(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    from skill_studio.llm_provider import get_provider, OpenRouterProvider
    # Pass a fake client to avoid real HTTP
    fake_client = MagicMock()
    import skill_studio.llm_provider as lp
    monkeypatch.setattr(lp, "OpenRouterProvider",
                        lambda system_prompt: OpenRouterProvider(system_prompt=system_prompt, client=fake_client, model="m"))
    p = get_provider("s")
    assert isinstance(p, OpenRouterProvider)


def test_factory_anthropic_when_env_set(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    from skill_studio.llm_provider import get_provider, AnthropicProvider
    fake_client = MagicMock()
    import skill_studio.llm_provider as lp
    monkeypatch.setattr(lp, "AnthropicProvider",
                        lambda system_prompt: AnthropicProvider(system_prompt=system_prompt, client=fake_client, model="m"))
    p = get_provider("s")
    assert isinstance(p, AnthropicProvider)


def test_factory_raises_on_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    from skill_studio.llm_provider import get_provider
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        get_provider("s")


def test_anthropic_provider_ask(monkeypatch):
    from unittest.mock import MagicMock
    fake_client = MagicMock()
    fake_block = MagicMock()
    fake_block.text = "answer from claude"
    fake_client.messages.create.return_value = MagicMock(content=[fake_block])
    from skill_studio.llm_provider import AnthropicProvider
    p = AnthropicProvider(system_prompt="sys", client=fake_client, model="claude-test")
    out = p.ask(history=[{"role": "user", "content": "hi"}])
    assert out == "answer from claude"
    call = fake_client.messages.create.call_args
    assert call.kwargs["system"][0]["text"] == "sys"
    assert call.kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
