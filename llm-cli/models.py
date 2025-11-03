"""LLM Model definitions and aliases."""

# Model registry with provider and aliases
MODELS = {
    # OpenAI Models
    "gpt-5": {
        "provider": "openai",
        "full_name": "gpt-5",
        "description": "Most advanced OpenAI model (2025)",
        "aliases": ["gpt5"],
    },
    "gpt-4-1": {
        "provider": "openai",
        "full_name": "gpt-4-1",
        "description": "Latest high-performance GPT-4 variant",
        "aliases": ["gpt-4.1", "gpt4.1"],
    },
    "gpt-4-1-mini": {
        "provider": "openai",
        "full_name": "gpt-4-1-mini",
        "description": "Smaller, faster GPT-4.1 variant",
        "aliases": ["gpt-4.1-mini", "gpt4-mini"],
    },
    "gpt-4o": {
        "provider": "openai",
        "full_name": "gpt-4o",
        "description": "Multimodal omni model",
        "aliases": ["gpt4o"],
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "full_name": "gpt-4o-mini",
        "description": "Lightweight multimodal model",
        "aliases": ["gpt4o-mini"],
    },
    "o3": {
        "provider": "openai",
        "full_name": "o3",
        "description": "Advanced reasoning model",
        "aliases": ["o3-full"],
    },
    "o3-mini": {
        "provider": "openai",
        "full_name": "o3-mini",
        "description": "Reasoning model optimized for speed",
        "aliases": ["o3-mini-standard"],
    },
    "o3-mini-high": {
        "provider": "openai",
        "full_name": "o3-mini-high",
        "description": "Reasoning model with higher performance",
        "aliases": [],
    },
    # Anthropic Claude Models
    "claude-sonnet-4.5": {
        "provider": "anthropic",
        "full_name": "claude-sonnet-4.5",
        "description": "Latest flagship Claude model (Sept 2025)",
        "aliases": ["claude-4.5", "claude-latest"],
    },
    "claude-opus-4.1": {
        "provider": "anthropic",
        "full_name": "claude-opus-4.1",
        "description": "Complex task specialist",
        "aliases": ["claude-opus"],
    },
    "claude-opus-4": {
        "provider": "anthropic",
        "full_name": "claude-opus-4",
        "description": "Coding specialist model",
        "aliases": [],
    },
    "claude-sonnet-4": {
        "provider": "anthropic",
        "full_name": "claude-sonnet-4",
        "description": "Balanced performance model",
        "aliases": ["claude-sonnet"],
    },
    "claude-3.5-sonnet": {
        "provider": "anthropic",
        "full_name": "claude-3-5-sonnet-20241022",
        "description": "Previous generation Sonnet",
        "aliases": ["claude-3.5"],
    },
    "claude-3.5-haiku": {
        "provider": "anthropic",
        "full_name": "claude-3-5-haiku-20241022",
        "description": "Fast and efficient model",
        "aliases": ["claude-haiku"],
    },
    # Google Gemini Models
    "gemini-2.5-pro": {
        "provider": "google",
        "full_name": "gemini-2.5-pro",
        "description": "Most advanced Gemini model",
        "aliases": ["gemini-pro", "gemini-2.5"],
    },
    "gemini-2.5-flash": {
        "provider": "google",
        "full_name": "gemini-2.5-flash",
        "description": "Default fast Gemini model",
        "aliases": ["gemini-flash"],
    },
    "gemini-2.5-flash-lite": {
        "provider": "google",
        "full_name": "gemini-2.5-flash-lite",
        "description": "Speed-optimized Gemini model",
        "aliases": ["gemini-lite"],
    },
    "gemini-2.0-flash": {
        "provider": "google",
        "full_name": "gemini-2.0-flash",
        "description": "Previous generation Flash model",
        "aliases": [],
    },
    "gemini-2.5-computer-use": {
        "provider": "google",
        "full_name": "gemini-2.5-computer-use",
        "description": "UI interaction specialized model",
        "aliases": ["gemini-computer"],
    },
    # Ollama Local Models
    "llama3.1": {
        "provider": "ollama",
        "full_name": "llama3.1:8b",
        "description": "Meta's Llama 3.1 (8B, 70B, 405B available)",
        "aliases": ["llama3"],
    },
    "llama3.2": {
        "provider": "ollama",
        "full_name": "llama3.2:1b",
        "description": "Compact Llama 3.2 (1B, 3B available)",
        "aliases": [],
    },
    "mistral-large-2": {
        "provider": "ollama",
        "full_name": "mistral:large",
        "description": "Mistral's flagship model",
        "aliases": ["mistral"],
    },
    "deepseek-coder": {
        "provider": "ollama",
        "full_name": "deepseek-coder",
        "description": "Specialized coding model",
        "aliases": ["deepseek"],
    },
    "starcode2": {
        "provider": "ollama",
        "full_name": "starcode2:3b",
        "description": "Code generation model (3B, 7B, 15B)",
        "aliases": ["starcode"],
    },
    # Groq Llama Models
    "groq-llama-3.3-70b": {
        "provider": "groq",
        "full_name": "groq/llama-3.3-70b-versatile",
        "description": "Most capable Groq Llama model (fast & free)",
        "aliases": ["groq-llama-3.3", "groq-llama", "llama-3.3-70b"],
    },
    "groq-llama-3.1-8b": {
        "provider": "groq",
        "full_name": "groq/llama-3.1-8b-instant",
        "description": "Lightweight Groq Llama model (fastest)",
        "aliases": ["groq-llama-3.1", "llama-3.1-8b"],
    },
    "groq-llama-3.3-70b-instruct": {
        "provider": "groq",
        "full_name": "groq/meta-llama/llama-3.3-70b-versatile",
        "description": "Instruction-tuned Llama 3.3 70B",
        "aliases": ["llama-3.3-instruct"],
    },
    # OpenRouter Models - Unified API for 200+ models
    "openrouter-gpt-4o": {
        "provider": "openrouter",
        "full_name": "openai/gpt-4o",
        "description": "OpenAI GPT-4o via OpenRouter",
        "aliases": ["or-gpt-4o", "openai/gpt-4o"],
    },
    "openrouter-claude-opus": {
        "provider": "openrouter",
        "full_name": "anthropic/claude-3-opus",
        "description": "Anthropic Claude 3 Opus via OpenRouter",
        "aliases": ["or-claude-opus", "anthropic/claude-opus"],
    },
    "openrouter-claude-sonnet": {
        "provider": "openrouter",
        "full_name": "anthropic/claude-3-sonnet",
        "description": "Anthropic Claude 3 Sonnet via OpenRouter",
        "aliases": ["or-claude-sonnet", "anthropic/claude-sonnet"],
    },
    "openrouter-llama-3.3-70b": {
        "provider": "openrouter",
        "full_name": "meta-llama/llama-3.3-70b-instruct",
        "description": "Meta Llama 3.3 70B via OpenRouter",
        "aliases": ["or-llama-3.3", "meta-llama/llama-3.3-70b"],
    },
    "openrouter-mistral-large": {
        "provider": "openrouter",
        "full_name": "mistralai/mistral-large",
        "description": "Mistral Large via OpenRouter",
        "aliases": ["or-mistral-large", "mistralai/mistral-large"],
    },
    "openrouter-gpt-4-turbo": {
        "provider": "openrouter",
        "full_name": "openai/gpt-4-turbo",
        "description": "OpenAI GPT-4 Turbo via OpenRouter",
        "aliases": ["or-gpt-4-turbo", "openai/gpt-4-turbo"],
    },
}

# Provider aliases
PROVIDER_ALIASES = {
    "openai": "openai",
    "gpt": "openai",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "google": "google",
    "gemini": "google",
    "groq": "groq",
    "llama": "groq",
    "openrouter": "openrouter",
    "or": "openrouter",
    "ollama": "ollama",
    "local": "ollama",
}

# Reverse lookup: model name -> model config
def get_model(identifier: str) -> dict | None:
    """Get model config by name or alias."""
    # Direct match
    if identifier in MODELS:
        return MODELS[identifier]

    # Check aliases
    for model_name, config in MODELS.items():
        if identifier in config.get("aliases", []):
            return MODELS[model_name]

    return None


def get_models_by_provider(provider: str) -> list[dict]:
    """Get all models for a provider."""
    provider = PROVIDER_ALIASES.get(provider, provider)
    return [
        (name, config)
        for name, config in MODELS.items()
        if config["provider"] == provider
    ]


def resolve_provider_alias(alias: str) -> str | None:
    """Resolve provider alias to full provider name."""
    return PROVIDER_ALIASES.get(alias.lower())
