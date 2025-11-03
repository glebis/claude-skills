# LLM CLI Skill - Quick Reference Card

## Setup (Choose One)

### Groq (Recommended - Fastest & Free)
```bash
# 1. Get key (no credit card)
Visit: https://console.groq.com/keys

# 2. Set environment
export GROQ_API_KEY='gsk_...'

# 3. Use
llm -m groq-llama-3.3-70b "Your prompt"
```

### OpenRouter (Multiple Providers)
```bash
# 1. Get key (no credit card needed)
Visit: https://openrouter.ai/keys

# 2. Set environment
export OPENROUTER_API_KEY='sk-or-...'

# 3. Use
llm -m openrouter-gpt-4o "Your prompt"
```

### OpenAI
```bash
export OPENAI_API_KEY='sk-proj-...'
llm -m gpt-4o "Your prompt"
```

### Anthropic
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
llm -m claude-sonnet-4.5 "Your prompt"
```

---

## Basic Usage

```bash
# Simple query
llm -m groq-llama-3.3-70b "What is AI?"

# Process file
cat document.txt | llm -m groq-llama-3.3-70b "Summarize"

# Interactive chat
llm -m groq-llama-3.3-70b --conversation

# Check setup
/llm --setup
```

---

## Popular Models

| Name | Use Case | Speed | Quality |
|------|----------|-------|---------|
| `groq-llama-3.3-70b` | General purpose | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| `groq-llama-3.1-8b` | Fast tasks | ⚡⚡⚡⚡ | ⭐⭐⭐ |
| `openrouter-gpt-4o` | Premium | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| `or-claude-opus` | Complex tasks | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| `gpt-4o` | Premium OpenAI | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| `claude-sonnet-4.5` | Premium Claude | ⚡⚡ | ⭐⭐⭐⭐⭐ |

---

## Aliases (Shortcuts)

```bash
# Same thing
llm -m groq-llama-3.3-70b "prompt"
llm -m groq-llama "prompt"
llm -m groq-llama-3.3 "prompt"
llm -m llama-3.3-70b "prompt"

# Same thing
llm -m openrouter-gpt-4o "prompt"
llm -m or-gpt-4o "prompt"
llm -m openai/gpt-4o "prompt"

# Same thing
llm -m claude-opus "prompt"
llm -m anthropic/claude-opus "prompt"
```

---

## File Operations

```bash
# Summarize
cat long.txt | llm -m groq-llama-3.3-70b "Summarize in 3 sentences"

# Analyze code
cat main.py | llm -m gpt-4o "Review this code"

# Extract info
cat data.csv | llm -m groq-llama-3.3-70b "What patterns do you see?"

# Translate
echo "Hello" | llm -m gpt-4o "Translate to Spanish"

# Fix JSON
cat broken.json | llm -m gpt-4o "Fix this JSON"
```

---

## Interactive Mode

```bash
# Start conversation
llm -m groq-llama-3.3-70b --conversation

# With specific model
llm -m openrouter-gpt-4o --conversation

# Keep chatting until Ctrl+C
# Each response maintains context
```

---

## With the Skill

```bash
# Using /llm skill
/llm "Your prompt" --model groq-llama-3.3-70b

# Let it choose from available
/llm "Your prompt"

# By provider
/llm "Your prompt" --model groq
# Shows menu of Groq models

# Interactive
/llm --interactive
```

---

## Common Tasks

### Ask a Question
```bash
llm -m groq-llama-3.3-70b "Explain quantum computing"
```

### Write Code
```bash
llm -m gpt-4o "Write a Python function to sort a list"
```

### Analyze Text
```bash
cat article.md | llm -m or-claude-opus "Summarize main points"
```

### Get Ideas
```bash
llm -m groq-llama-3.3-70b "Brainstorm 5 creative ideas for"
```

### Learn Topic
```bash
llm -m openrouter-claude-sonnet "Explain [topic] like I'm 10"
```

### Check Your Writing
```bash
cat draft.txt | llm -m gpt-4o "Fix grammar and improve clarity"
```

### Explain Code
```bash
cat script.py | llm -m gpt-4o "Explain what this code does"
```

### Translate
```bash
echo "Hello world" | llm -m groq-llama-3.3-70b "Translate to French"
```

---

## Troubleshooting

### API Key Not Found
```bash
# Check if set
echo $GROQ_API_KEY

# Set it
export GROQ_API_KEY='gsk_...'

# Reload shell
source ~/.zshrc
```

### Model Not Found
```bash
# List available models
llm models | grep groq

# Verify your API key is set
echo $GROQ_API_KEY
```

### Connection Error
- Check internet connection
- Verify API key is correct
- Try different model
- Check provider status page

### Rate Limited
- Wait a few minutes
- Use free tier properly
- Upgrade account if needed

---

## Tips & Tricks

1. **Remember Last Model**
   - First use: `llm -m groq-llama-3.3-70b "test"`
   - Later: `llm "test"` (uses Groq by default)

2. **Combine with Shell**
   ```bash
   grep ERROR app.log | llm -m groq-llama-3.3-70b "Analyze"
   ```

3. **Save Output**
   ```bash
   llm -m groq-llama-3.3-70b "Your prompt" > output.txt
   ```

4. **Pipeline Multiple Tools**
   ```bash
   cat file.txt | llm -m groq-llama-3.3-70b "Summarize" | less
   ```

5. **Use in Scripts**
   ```bash
   #!/bin/bash
   RESPONSE=$(llm -m groq-llama-3.3-70b "Your prompt")
   echo "$RESPONSE"
   ```

---

## Provider Comparison

| Feature | Groq | OpenRouter | OpenAI | Anthropic |
|---------|------|-----------|--------|-----------|
| Speed | ⚡⚡⚡ | ⚡⚡ | ⚡⚡ | ⚡⚡ |
| Cost | 🆓 | 💰 | 💰💰 | 💰💰 |
| Setup | Easy | Easy | Easy | Easy |
| Models | 3 | 200+ | 5 | 6 |

---

## Documentation Files

- **START_HERE.md** - Quick start
- **QUICKSTART.md** - Fast reference
- **README.md** - Full guide
- **GROQ_INTEGRATION.md** - Groq details
- **OPENROUTER_INTEGRATION.md** - OpenRouter details
- **INSTALL.md** - Setup help
- **SKILL.md** - Claude integration

---

## Key Websites

- Groq: https://console.groq.com/keys
- OpenRouter: https://openrouter.ai/keys
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/account/keys
- LLM CLI: https://llm.datasette.io

---

## One-Liners

```bash
# Groq setup & test
export GROQ_API_KEY='gsk_...' && llm -m groq-llama-3.3-70b "Hello"

# OpenRouter setup & test
export OPENROUTER_API_KEY='sk-or-...' && llm -m openrouter-gpt-4o "Hello"

# Check all available models
llm models

# Check available providers
/llm --setup

# Interactive Groq chat
llm -m groq-llama-3.3-70b --conversation
```

---

## Recommended Setup

**For Quick Start:**
1. Get Groq key (free): https://console.groq.com/keys
2. Run: `export GROQ_API_KEY='gsk_...'`
3. Use: `llm -m groq-llama-3.3-70b "Your prompt"`

**For Model Variety:**
1. Get OpenRouter key (free): https://openrouter.ai/keys
2. Run: `export OPENROUTER_API_KEY='sk-or-...'`
3. Use: `llm -m openrouter-gpt-4o "Your prompt"`

**For Production:**
1. Add OpenAI API key
2. Add Anthropic API key
3. Use: `llm -m gpt-4o` or `llm -m claude-sonnet-4.5`

---

## Need Help?

- Check: `~/.claude/skills/llm-cli/START_HERE.md`
- Run: `/llm --help`
- Setup: `/llm --setup`
- Models: `llm models`

---

**Status**: ✅ Production Ready | **Version**: 1.0.0 | **Updated**: Nov 3, 2025
