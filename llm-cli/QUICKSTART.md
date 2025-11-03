# Quick Start Guide

## 5-Minute Setup

### 1. Install
```bash
pip install llm
```

### 2. Set One API Key
```bash
# OpenAI
export OPENAI_API_KEY='sk-proj-...'

# OR Anthropic
export ANTHROPIC_API_KEY='sk-ant-...'

# OR both, or Google, or just use Ollama (free, local)
```

### 3. Test
```bash
/llm "Hello world"
```

Done! You're ready to go.

---

## Common Commands

### Process Text
```bash
/llm "Summarize this: [your text]"
```

### Use Specific Model
```bash
/llm --model gpt-4o "Your prompt"
/llm --model claude-opus "Your prompt"
/llm --model gemini-pro "Your prompt"
```

### Process Files
```bash
/llm "Analyze this" < document.txt
cat code.py | /llm "Review"
```

### Interactive Chat
```bash
/llm --interactive
/llm -i --model claude-sonnet-4.5
```

### Find Available Models
```bash
/llm --setup
```

---

## Model Cheat Sheet

| Speed | Quality | Price | Model |
|-------|---------|-------|-------|
| ⚡⚡⚡ | ⭐⭐ | 💰 | `gpt-4o-mini`, `claude-haiku` |
| ⚡⚡ | ⭐⭐⭐ | 💰💰 | `gpt-4o`, `claude-sonnet-4.5` |
| ⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 | `gpt-5`, `claude-opus-4.1` |
| ⚡⚡⚡ | ⭐⭐⭐ | 🆓 | `ollama` (local) |

---

## Pro Tips

1. **Last model remembered**: Use any model once, then skip `--model` next time
2. **Pipe anything**: `cat file | /llm "process"`
3. **Interactive mode**: `/llm -i` then keep chatting
4. **File input**: Works with `.txt`, `.md`, `.json`, `.py`, images, PDFs, audio
5. **Multiple providers**: Set multiple API keys, system picks best available

---

## Aliases

Shorter ways to specify models:

```bash
/llm --model gpt-4o          # OpenAI (also: gpt4o)
/llm --model claude-opus     # Anthropic (also: claude)
/llm --model gemini-pro      # Google (also: gemini)
/llm --model ollama          # Local (also: local)

# Or by provider:
/llm --model openai "prompt"
/llm --model anthropic "prompt"
```

---

## Examples

```bash
# Summarize
/llm "Summarize: [paste text]"

# Code review
cat main.py | /llm "Review and suggest improvements"

# Translate
/llm "Translate to French" < article.md

# Explain
/llm "Explain this like I'm 5" < physics_paper.txt

# Extract
/llm "Extract email addresses from this" < data.txt

# Fix JSON
/llm "Validate and fix JSON" < broken.json

# Find bugs
grep "ERROR" app.log | /llm "What's happening?"

# Q&A session
/llm -i --model claude-sonnet-4.5
# Then ask questions
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No providers | `pip install llm` then set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` |
| API key error | `echo $OPENAI_API_KEY` to verify, check spelling |
| Model not found | `/llm --setup` to see available models |
| Connection error | Check internet or switch to `ollama` for local processing |
| Timeout | File too large? Try streaming or splitting |

---

## Environment Setup

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# One or more of these:
export OPENAI_API_KEY='sk-proj-...'
export ANTHROPIC_API_KEY='sk-ant-...'
export GOOGLE_API_KEY='...'

# Then reload:
source ~/.zshrc
```

---

## Next Steps

- Read [README.md](README.md) for full documentation
- Run `/llm --setup` to explore all models
- Try different models: `gpt-4o`, `claude-sonnet-4.5`, `gemini-2.5-pro`
- Start interactive chat: `/llm -i`
- Check [INSTALL.md](INSTALL.md) for detailed setup

---

**That's it! Enjoy processing with LLMs!** 🚀
