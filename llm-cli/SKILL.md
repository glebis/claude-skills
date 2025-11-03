---
name: llm-cli
description: Process textual and multimedia files with various LLM providers using the llm CLI. Supports both non-interactive and interactive modes with model selection, config persistence, and file input handling.
---

# LLM CLI Skill

## Purpose

This skill enables seamless interaction with multiple LLM providers (OpenAI, Anthropic, Google Gemini, Ollama) through the `llm` CLI tool. It processes textual and multimedia information with support for both one-off executions and interactive conversation modes.

## When to Use This Skill

Trigger this skill when:
- User wants to process text/files with an LLM
- User needs to choose between multiple available LLMs
- User wants interactive conversation with an LLM
- User needs to pipe content through an LLM for processing
- User wants to use specific model aliases (e.g., "claude-opus", "gpt-4o")

Example user requests:
- "Process this file with Claude"
- "Analyze this text with the fastest available model"
- "Start an interactive chat with OpenAI"
- "Use Gemini to summarize this document"
- "Chat mode with my local Ollama instance"

## Supported Providers & Models

### OpenAI
- **Latest Models (2025)**:
  - `gpt-5` - Most advanced model
  - `gpt-4-1` / `gpt-4.1` - Latest high-performance
  - `gpt-4-1-mini` / `gpt-4.1-mini` - Smaller, faster version
  - `gpt-4o` - Multimodal omni model
  - `gpt-4o-mini` - Lightweight multimodal
  - `o3` - Advanced reasoning
  - `o3-mini` / `o3-mini-high` - Reasoning variants

**Aliases**: `openai`, `gpt`

### Anthropic
- **Latest Models (2025)**:
  - `claude-sonnet-4.5` - Latest flagship model
  - `claude-opus-4.1` - Complex task specialist
  - `claude-opus-4` - Coding specialist
  - `claude-sonnet-4` - Balanced performance
  - `claude-3.5-sonnet` - Previous generation
  - `claude-3.5-haiku` - Fast & efficient

**Aliases**: `anthropic`, `claude`

### Google Gemini
- **Latest Models (2025)**:
  - `gemini-2.5-pro` - Most advanced
  - `gemini-2.5-flash` - Default fast model
  - `gemini-2.5-flash-lite` - Speed optimized
  - `gemini-2.0-flash` - Previous generation
  - `gemini-2.5-computer-use` - UI interaction

**Aliases**: `google`, `gemini`

### Ollama (Local)
- **Popular Models**:
  - `llama3.1` - Meta's latest (8b, 70b, 405b)
  - `llama3.2` - Compact versions (1b, 3b)
  - `mistral-large-2` - Mistral flagship
  - `deepseek-coder` - Code specialist
  - `starcode2` - Code models

**Aliases**: `ollama`, `local`

## Workflow Overview

```
User Input (with optional model)
    ↓
Check Available Providers (env vars)
    ↓
Determine Model to Use:
  - If specified: Use provided model
  - If ambiguous: Show selection menu
  - Otherwise: Use last remembered choice
    ↓
Load/Create Config (~/.claude/llm-skill-config.json)
    ↓
Detect Input Type:
  - stdin/piped
  - file path
  - inline text
    ↓
Execute llm CLI:
  - Non-interactive: Process & return
  - Interactive: Keep conversation loop
    ↓
Save Model Choice to Config
```

## Features

### 1. Provider Detection
- Checks environment variables for API keys
- Suggests available LLM providers on first run
- Detects: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`

### 2. Model Selection
- Accept model aliases (`gpt-4o`, `claude-opus`, `gemini-2.5-pro`)
- Accept provider aliases (`openai`, `anthropic`, `google`, `ollama`)
- Interactive menu when selection is ambiguous
- Remembers last used model in `~/.claude/llm-skill-config.json`

### 3. Input Processing
- Accepts stdin/piped input
- Processes file paths (detects: .txt, .md, .json, .pdf, images)
- Handles inline text prompts
- Supports multimedia files with appropriate encoding

### 4. Execution Modes

#### Non-Interactive (Default)
```bash
llm "Your prompt here"
llm --model gpt-4o "Process this text"
llm < file.txt
cat document.md | llm "Summarize"
```

#### Interactive Mode
```bash
llm --interactive
llm -i
llm --model claude-opus --interactive
```

### 5. Configuration
Persistent config location: `~/.claude/llm-skill-config.json`
```json
{
  "last_model": "claude-sonnet-4.5",
  "default_provider": "anthropic",
  "available_providers": ["openai", "anthropic", "google", "ollama"]
}
```

## Implementation Details

### Core Files
- `llm_skill.py` - Main skill orchestration
- `providers.py` - Provider detection & config
- `models.py` - Model definitions & aliases
- `executor.py` - Execution logic (interactive/non-interactive)
- `input_handler.py` - Input type detection

### Key Functions

#### `detect_providers()`
- Scans environment for provider API keys
- Returns dict of available providers

#### `get_model_selector(input_text, provider=None)`
- Returns selected model, showing menu if needed
- Respects `last_model` config preference

#### `load_input(input_source)`
- Handles stdin, file paths, or inline text
- Returns content string

#### `execute_llm(content, model, interactive=False)`
- Calls `llm` CLI with appropriate parameters
- Manages stdin/stdout for interactive mode

### Usage in Claude Code

When user invokes this skill, Claude should:
1. Parse input for model specification (e.g., `--model gpt-4o`)
2. Call skill with content and optional model parameter
3. Wait for provider/model selection if needed
4. Execute and return results
5. For interactive mode, maintain conversation loop

## Error Handling

- If no providers available: Suggest installing API keys
- If model not found: Show available models for chosen provider
- If llm CLI not installed: Suggest installation via `pip install llm`
- If file not readable: Fall back to treating as inline text

## Configuration

Users can pre-configure preferences:
```json
{
  "last_model": "claude-sonnet-4.5",
  "default_provider": "anthropic",
  "interactive_mode": false,
  "available_providers": ["openai", "anthropic"]
}
```

## Slash Command Integration

Support `/llm` command:
```
/llm process this text
/llm --interactive
/llm --model gpt-4o analyze this
```
