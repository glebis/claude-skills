# Installation & Setup Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Claude Code (CLI)

## Step 1: Install llm CLI

The skill requires the `llm` CLI tool by Simon Willison.

```bash
pip install llm
```

Verify installation:
```bash
llm --version
```

## Step 2: Set Up API Keys (Choose Your Providers)

### Option A: OpenAI (GPT Models)

1. Get API key from https://platform.openai.com/api-keys
2. Add to your shell configuration (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
export OPENAI_API_KEY='sk-proj-...'
```

3. Reload shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### Option B: Anthropic (Claude Models)

1. Get API key from https://console.anthropic.com/account/keys
2. Add to your shell configuration:

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

3. Reload shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### Option C: Google Gemini

1. Get API key from https://aistudio.google.com/app/apikey
2. Add to your shell configuration:

```bash
export GOOGLE_API_KEY='your-api-key'
```

3. Reload shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### Option D: Ollama (Free, Local)

1. Install Ollama from https://ollama.ai
2. Pull a model:

```bash
ollama pull llama2
# or other models: mistral, neural-chat, etc.
```

3. Start Ollama service (keeps running in background):

```bash
ollama serve
```

No API key needed for Ollama!

## Step 3: Verify Installation

Test that the skill can detect your providers:

```bash
/llm --setup
```

You should see output like:
```
🔍 Scanning for available LLM providers...

✅ Available LLM Providers:
   • openai
   • anthropic
   • google

You can also set up: ollama

✅ Configuration saved to ~/.claude/llm-skill-config.json
```

## Step 4: Optional - Install Support Libraries

For enhanced features:

```bash
# PDF support
pip install PyPDF2

# Better output formatting (recommended)
pip install rich
```

## Step 5: Configure Default Model (Optional)

Edit `~/.claude/llm-skill-config.json`:

```json
{
  "last_model": "gpt-4o",
  "last_provider": "openai",
  "available_providers": ["openai", "anthropic", "google", "ollama"],
  "auto_detect": true
}
```

Or just use the skill and it will remember your last choice!

## Testing

### Test with OpenAI
```bash
/llm --model gpt-4o "Say hello"
```

### Test with Anthropic
```bash
/llm --model claude-sonnet-4.5 "Say hello"
```

### Test with Google
```bash
/llm --model gemini-2.5-flash "Say hello"
```

### Test with Ollama
```bash
/llm --model ollama "Say hello"
```

### Test Interactive Mode
```bash
/llm --interactive
```

## Troubleshooting Installation

### llm CLI not found
```bash
# Verify installation
which llm

# Reinstall if needed
pip install --upgrade llm
```

### API key not recognized
```bash
# Check if environment variable is set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
echo $GOOGLE_API_KEY

# If empty, check shell configuration file
cat ~/.zshrc | grep "OPENAI_API_KEY"

# Make sure to source after editing
source ~/.zshrc
```

### No models available
```bash
# Run setup to detect providers
/llm --setup

# Check which providers you set up
cat ~/.claude/llm-skill-config.json
```

### Ollama connection error
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, test:
curl http://localhost:11434/api/tags

# Pull a model if needed
ollama pull llama2
```

### Python version issue
```bash
# Check Python version
python --version
python3 --version

# Ensure it's 3.8 or higher
# If not, install from python.org
```

## Upgrading

To upgrade the llm CLI to the latest version:

```bash
pip install --upgrade llm
```

To check for updates:
```bash
pip list | grep llm
```

## Uninstalling

If you need to remove the skill:

```bash
# Remove the skill directory
rm -rf ~/.claude/skills/llm-cli

# Optionally remove config
rm ~/.claude/llm-skill-config.json

# Optionally uninstall llm CLI
pip uninstall llm
```

## Next Steps

- Read the [README.md](README.md) for usage examples
- Check out the [SKILL.md](SKILL.md) for detailed feature documentation
- Try the interactive mode: `/llm --interactive`
- Explore different models: `/llm --setup` then experiment

## Getting Help

If you encounter issues:

1. **Provider not detected**: Run `/llm --setup`
2. **API key error**: Check `echo $PROVIDER_API_KEY`
3. **llm not installed**: Run `pip install llm`
4. **Model not found**: List models for provider: `/llm --model openai "test"`
5. **Timeout issues**: Check internet connection or use local Ollama

## Additional Resources

- [llm CLI Documentation](https://llm.datasette.io/)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Anthropic Console](https://console.anthropic.com/)
- [Google AI Studio](https://aistudio.google.com/)
- [Ollama](https://ollama.ai)
