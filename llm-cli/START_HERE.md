# 🚀 LLM CLI Skill - START HERE

Welcome to the LLM CLI Skill! This document will get you started in 5 minutes.

## What Is This?

A powerful Claude Code skill that gives you access to **multiple LLM providers** (OpenAI, Anthropic, Google, Ollama) through a simple command interface.

**Use cases:**
- ✅ Process documents with AI
- ✅ Quick text analysis and summarization
- ✅ Code review and generation
- ✅ Interactive conversations
- ✅ Batch file processing

## Quick Setup (5 minutes)

### Step 1: Install llm CLI
```bash
pip install llm
```

### Step 2: Add an API Key
Pick ONE of these (or do multiple):

**OpenAI (GPT-4o, GPT-5):**
```bash
export OPENAI_API_KEY='sk-proj-...'
```

**Anthropic (Claude):**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

**Google Gemini:**
```bash
export GOOGLE_API_KEY='...'
```

**Ollama (Free, Local):**
No key needed! Just install from https://ollama.ai

### Step 3: Verify Setup
```bash
/llm --setup
```

You're done! 🎉

---

## First Commands

### Try a simple prompt:
```bash
/llm "What is the capital of France?"
```

### Use a specific model:
```bash
/llm --model gpt-4o "Explain quantum computing"
```

### Process a file:
```bash
cat myfile.txt | /llm "Summarize this"
```

### Start a conversation:
```bash
/llm --interactive
# Type your questions, press Ctrl+C to exit
```

---

## What You Get

| Feature | Details |
|---------|---------|
| **4 Providers** | OpenAI, Anthropic, Google, Ollama |
| **30+ Models** | Latest 2025 models from all providers |
| **Smart Selection** | Remembers your last model choice |
| **File Support** | Text, code, JSON, PDF, images, audio |
| **Modes** | Non-interactive or interactive chat |
| **Aliases** | Use `gpt-4o` or `openai` - both work |

---

## Common Tasks

### Summarize
```bash
/llm "Summarize in 3 bullet points" < long_document.txt
```

### Code Review
```bash
/llm --model gpt-4o "Review this code for bugs" < main.py
```

### Translate
```bash
/llm "Translate to Spanish" < article.md
```

### Analyze Data
```bash
/llm "What patterns do you see?" < data.csv
```

### Interactive Q&A
```bash
/llm -i --model claude-sonnet-4.5
# Ask questions in the chat loop
```

---

## Model Recommendations

Choose by your needs:

| Goal | Model | Command |
|------|-------|---------|
| Fastest | gpt-4o-mini | `/llm --model gpt-4o-mini` |
| Best Quality | gpt-5 | `/llm --model gpt-5` |
| Best Balance | claude-sonnet-4.5 | `/llm --model claude-sonnet-4.5` |
| Free & Local | ollama | `/llm --model ollama` |

---

## Next Steps

1. **Explore Models**: Run `/llm --setup` to see all available models
2. **Read Full Guide**: Open [README.md](README.md) for detailed docs
3. **Quick Reference**: Check [QUICKSTART.md](QUICKSTART.md)
4. **Install Help**: See [INSTALL.md](INSTALL.md) for detailed setup

---

## Troubleshooting

### "No providers found"
```bash
# Make sure you set an API key
echo $OPENAI_API_KEY
# If empty, set it again and reload shell
source ~/.zshrc
```

### "llm command not found"
```bash
pip install llm
llm --version  # Should show version
```

### "Model not found"
```bash
/llm --setup  # Shows all available models
```

### "Permission denied"
```bash
chmod +x ~/.claude/skills/llm-cli/llm_skill.py
```

---

## File Support

Works with:
- **Text**: `.txt`, `.md`, `.json`, `.log`, `.csv`
- **Code**: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.html`, `.css`
- **Config**: `.yaml`, `.yml`, `.toml`, `.xml`
- **Media**: `.pdf`, `.jpg`, `.png`, `.gif`, `.mp3`, `.wav`

Example:
```bash
/llm "Fix the JSON" < config.json
cat code.ts | /llm "Type check this"
```

---

## Pro Tips

1. **Remember Your Choice**: Use any model once, then it's the default
2. **Pipe Anything**: `cat file | /llm "process"`
3. **Quick Interactive**: `/llm -i` starts chat immediately
4. **Combine with Shell**: `grep ERROR app.log | /llm "analyze"`
5. **Multiple Providers**: Set multiple API keys for flexibility

---

## Command Reference

```bash
# Basic usage
/llm "Your prompt"                          # Uses remembered model
/llm "Prompt" < file.txt                    # From file
cat file | /llm "Process"                   # From pipe

# Model selection
/llm --model gpt-4o "prompt"               # Specific model
/llm --model openai "prompt"               # Specific provider
/llm --model claude-opus --interactive     # Model + mode

# Modes
/llm --interactive                         # Interactive chat
/llm -i --model claude-sonnet-4.5         # Interactive + model

# Setup
/llm --setup                               # Detect providers
/llm --help                                # Show all options
```

---

## Configuration File

**Location**: `~/.claude/llm-skill-config.json`

Automatically created and updated. Shows:
- Last model used
- Available providers
- Provider settings

Edit manually if needed, but usually not necessary!

---

## Security

- API keys stored in environment variables (not in config)
- Config file only stores model preferences (no secrets)
- All communication goes directly to providers
- Local models (Ollama) run entirely offline

---

## Support

**Problem?** Check these in order:
1. [QUICKSTART.md](QUICKSTART.md) - 5-minute overview
2. [README.md](README.md) - Detailed documentation
3. [INSTALL.md](INSTALL.md) - Setup troubleshooting
4. [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details

---

## What's Inside

```
llm-cli/
├── START_HERE.md                  ← You are here! 👈
├── QUICKSTART.md                  ← 5-min setup
├── README.md                       ← Full guide (3000+ words)
├── INSTALL.md                     ← Detailed setup
├── SKILL.md                       ← Skill definition
├── IMPLEMENTATION_SUMMARY.md      ← Technical details
├── requirements.txt               ← Dependencies
│
├── llm_skill.py                  ← Main program
├── models.py                     ← Model registry
├── providers.py                  ← Provider detection
├── executor.py                   ← Execution engine
└── input_handler.py              ← File handling
```

---

## Examples by Use Case

### Content Creation
```bash
/llm "Write a blog post about AI safety" < notes.txt
```

### Code Tasks
```bash
cat broken.js | /llm "Fix syntax errors"
/llm --model gpt-5 "Refactor this" < legacy.py
```

### Learning
```bash
/llm "Explain like I'm 5" < quantum_physics.pdf
/llm -i --model claude-opus  # Ask follow-up questions
```

### Data Analysis
```bash
/llm "Find trends in this data" < sales.csv
```

### Writing/Editing
```bash
/llm "Fix grammar and improve clarity" < draft.txt
```

### Bulk Processing
```bash
for file in *.txt; do
  /llm "Summarize" < "$file" > "${file%.txt}_summary.txt"
done
```

---

## Before You Go

✅ Install `llm`: `pip install llm`
✅ Set API key: `export OPENAI_API_KEY='...'` (or another provider)
✅ Test: `/llm "Hello"`
✅ Explore: `/llm --setup`
✅ Read: Check [README.md](README.md) for advanced features

---

**Ready?** Start with:
```bash
/llm "Hello, world!"
```

**Questions?** Check the documentation files or run `/llm --help`

**Enjoy! 🎉**
