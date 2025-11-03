# LLM CLI Skill

Process textual and multimedia information with various LLM providers using the `llm` CLI tool. Supports both non-interactive and interactive modes with intelligent model selection and persistent configuration.

## Installation

### Prerequisites
- Python 3.8+
- `llm` CLI: `pip install llm`

### Setup

The skill automatically detects available providers on first run. To manually set up:

```bash
/llm --setup
```

This will scan your environment for API keys and display available providers.

## Quick Start

### First Time: Set Up Providers

```bash
/llm --setup
```

Available providers are detected from environment variables:
- **OpenAI**: `OPENAI_API_KEY`
- **Anthropic**: `ANTHROPIC_API_KEY`
- **Google**: `GOOGLE_API_KEY`
- **Ollama**: Local service (no API key needed)

### Non-Interactive Mode (Default)

Process text with a single command:

```bash
# Simple text
/llm "Summarize this article about AI"

# Specific model
/llm --model gpt-4o "Translate to French"

# From file
/llm < document.txt

# Piped input
cat notes.md | /llm "Extract key points"
```

### Interactive Mode

Start a conversation loop:

```bash
# Default model
/llm --interactive

# Short form
/llm -i

# Specific model
/llm --model claude-sonnet-4.5 --interactive
```

## Model Selection

### By Name
Use full model name:
```bash
/llm --model gpt-4o "your prompt"
/llm --model claude-sonnet-4.5 "your prompt"
/llm --model gemini-2.5-pro "your prompt"
```

### By Alias
Use shorter aliases:
```bash
/llm --model gpt4o "prompt"
/llm --model claude-opus "prompt"
/llm --model gemini-pro "prompt"
```

### By Provider
Specify provider to see available models:
```bash
/llm --model openai "prompt"     # Shows OpenAI models
/llm --model anthropic "prompt"  # Shows Anthropic models
/llm --model google "prompt"     # Shows Google models
/llm --model ollama "prompt"     # Shows local Ollama models
```

### Interactive Selection
If no model specified and multiple available, you'll see a menu:
```
Available Providers:
  1. openai
  2. anthropic
  3. google

Select provider (number): 1

Available OpenAI Models:
  1. gpt-5 - Most advanced OpenAI model (2025)
  2. gpt-4-1 - Latest high-performance
  3. gpt-4o - Multimodal omni model

Select model (1-3): 1
```

## Input Methods

### Inline Text
```bash
/llm "Process this text"
```

### Piped Input
```bash
cat file.txt | /llm "Analyze"
echo "Hello" | /llm "Respond"
```

### File Input
```bash
/llm < document.txt
```

### File Path as Argument
```bash
/llm "Summarize this" < notes.md
llm document.txt  # Treats as file if exists
```

### Supported File Types

**Text Files**: `.txt`, `.md`, `.json`, `.csv`, `.log`, `.py`, `.js`, `.ts`, `.html`, `.css`, `.xml`, `.yaml`, `.toml`, `.sh`

**Media Files** (base64 encoded):
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Audio**: `.mp3`, `.wav`, `.m4a`
- **Documents**: `.pdf`

## Available Models

### OpenAI (2025)
- `gpt-5` - Most advanced model
- `gpt-4-1` / `gpt-4.1` - Latest high-performance
- `gpt-4-1-mini` - Smaller, faster
- `gpt-4o` - Multimodal omni
- `gpt-4o-mini` - Lightweight multimodal
- `o3` - Advanced reasoning
- `o3-mini` - Compact reasoning

**Aliases**: `openai`, `gpt`

### Anthropic (2025)
- `claude-sonnet-4.5` - Latest flagship
- `claude-opus-4.1` - Complex tasks
- `claude-opus-4` - Coding specialist
- `claude-sonnet-4` - Balanced
- `claude-3.5-sonnet` - Previous generation
- `claude-3.5-haiku` - Fast & efficient

**Aliases**: `anthropic`, `claude`

### Google Gemini (2025)
- `gemini-2.5-pro` - Most advanced
- `gemini-2.5-flash` - Default fast
- `gemini-2.5-flash-lite` - Speed optimized
- `gemini-2.0-flash` - Previous generation
- `gemini-2.5-computer-use` - UI interaction

**Aliases**: `google`, `gemini`

### Ollama (Local)
- `llama3.1` - Meta's latest (8b, 70b, 405b)
- `llama3.2` - Compact versions (1b, 3b)
- `mistral-large-2` - Mistral flagship
- `deepseek-coder` - Code specialist
- `starcode2` - Code models (3b, 7b, 15b)

**Aliases**: `ollama`, `local`

## Configuration

### Config File Location
`~/.claude/llm-skill-config.json`

### Default Configuration
```json
{
  "last_model": "claude-sonnet-4.5",
  "last_provider": "anthropic",
  "available_providers": ["openai", "anthropic", "google", "ollama"],
  "auto_detect": true
}
```

### Manual Configuration
Edit `~/.claude/llm-skill-config.json` to set defaults:

```json
{
  "last_model": "gpt-4o",
  "last_provider": "openai",
  "available_providers": ["openai", "anthropic"],
  "auto_detect": true
}
```

**Note**: `last_model` and `last_provider` are automatically updated each time you use the skill.

## Environment Variables

### OpenAI
```bash
export OPENAI_API_KEY='sk-...'
```

### Anthropic
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

### Google
```bash
export GOOGLE_API_KEY='...'
```

### Ollama
No API key needed. Requires local Ollama service running:
```bash
ollama serve  # In another terminal
```

## Examples

### Text Analysis
```bash
/llm --model claude-sonnet-4.5 "Analyze the sentiment of this review"
```

### Code Review
```bash
cat src/main.py | /llm --model gpt-4o "Review this code for bugs"
```

### Document Processing
```bash
/llm --model gemini-2.5-pro < research_paper.txt | head -20
```

### Translation
```bash
/llm --model claude-opus "Translate to Spanish" < article.md
```

### Summarization
```bash
/llm "Create a bullet-point summary" < long_document.txt
```

### Interactive Q&A
```bash
/llm --model claude-sonnet-4.5 --interactive
# Then ask questions in the conversation loop
```

### File Processing
```bash
# JSON validation
/llm --model gpt-4o "Validate this JSON and fix errors" < config.json

# Log analysis
cat app.log | /llm "Identify errors and patterns"

# CSV analysis
/llm "Summarize this data" < sales.csv
```

## Troubleshooting

### No providers found
```bash
/llm --setup  # Shows setup instructions
```

### API key issues
- Verify environment variables: `echo $OPENAI_API_KEY`
- Check key validity with provider
- Re-export if needed: `export OPENAI_API_KEY='your-key'`

### llm CLI not installed
```bash
pip install llm
```

### Model not found
- Check spelling and available models: `/llm --model anthropic "test"`
- Verify provider has API key set
- Try a different provider: `/llm --model openai "test"`

### Timeout
- Large files may take time to process
- Check internet connection for cloud providers
- Use local Ollama for offline processing

### Interactive mode not responding
- Press Ctrl+C to exit
- Check model name is correct
- Verify API key is valid

## Tips & Tricks

### Remember Last Model
The skill automatically remembers your last used model. No need to specify `--model` every time!

```bash
/llm --model gpt-4o "first prompt"
/llm "second prompt"  # Uses gpt-4o again
```

### Combine with Other Tools
```bash
# Search and analyze
grep "ERROR" app.log | /llm "Summarize errors"

# Count occurrences and analyze
wc -l data.csv | /llm "Is this a large dataset?"

# Pipeline multiple operations
cat data.json | /llm "Format nicely" | less
```

### Use in Shell Scripts
```bash
#!/bin/bash
ANALYSIS=$(/llm "Analyze this" < input.txt)
echo "Results: $ANALYSIS"
```

## Performance Considerations

- **Fastest**: `gpt-4o-mini`, `claude-3.5-haiku`, `gemini-2.5-flash-lite`, `ollama`
- **Best quality**: `gpt-5`, `claude-sonnet-4.5`, `gemini-2.5-pro`
- **Best balance**: `gpt-4o`, `claude-sonnet-4.5`, `gemini-2.5-flash`
- **Best offline**: `ollama` (requires local installation)

## Support

For issues:
1. Check configuration: `cat ~/.claude/llm-skill-config.json`
2. Run setup: `/llm --setup`
3. Verify `llm` CLI: `llm --version`
4. Check provider: `echo $PROVIDER_API_KEY`
