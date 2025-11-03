# LLM CLI Skill - File Manifest

## 📚 Documentation Files

### START_HERE.md (7.0 KB)
**Your entry point!** Quick 5-minute overview with examples and troubleshooting.
- Quick setup instructions
- Common tasks
- Model recommendations
- File support list
- Pro tips

### QUICKSTART.md (3.3 KB)
Condensed reference guide for quick lookups.
- 5-minute setup recap
- Common commands with examples
- Model cheat sheet
- Aliases reference
- Troubleshooting table

### README.md (7.5 KB)
Comprehensive user documentation with detailed explanations.
- Purpose and features
- Workflow overview
- All supported models with details
- Complete input methods
- Extensive examples by use case
- Configuration guide
- Troubleshooting guide

### INSTALL.md (4.7 KB)
Step-by-step installation and setup guide.
- Prerequisites
- Installation steps (pip install llm)
- API key setup for each provider
- Verification testing
- Troubleshooting for installation issues
- Upgrade/uninstall instructions

### SKILL.md (5.8 KB)
Claude Code skill definition and integration documentation.
- Skill purpose and triggers
- Supported providers and models
- Workflow architecture
- Feature descriptions
- Claude integration instructions

### IMPLEMENTATION_SUMMARY.md (8.5 KB)
Technical documentation of the implementation.
- Architecture overview
- Module structure and responsibilities
- Features implemented
- Recent model data (2025)
- Configuration system details
- Testing checklist
- Future enhancement ideas
- Implementation statistics

### FILES.md (This file)
Complete manifest of all files in the skill.

---

## 🐍 Python Source Files

### llm_skill.py (7.0 KB) - MAIN ENTRY POINT
Main orchestrator and CLI entry point.

**Responsibilities:**
- Parse command-line arguments
- Model selection logic
- Input/output coordination
- Setup mode handling
- Error handling and user feedback

**Key Classes:**
- `LLMSkill`: Main skill orchestrator

**Key Methods:**
- `select_model()`: Intelligent model selection
- `run()`: Main entry point
- `_setup_mode()`: Provider detection and setup

**Dependencies:**
- executor, input_handler, models, providers

---

### models.py (5.7 KB) - MODEL REGISTRY
Comprehensive model definitions and aliases for all providers.

**Features:**
- 30+ latest LLM models (2025 data)
- Model metadata (provider, description, aliases)
- Provider alias mapping
- Model lookup functions

**Data Structures:**
- `MODELS`: Dictionary of model configurations
- `PROVIDER_ALIASES`: Provider alias mappings

**Key Functions:**
- `get_model()`: Lookup model by name or alias
- `get_models_by_provider()`: Get all models for a provider
- `resolve_provider_alias()`: Resolve provider aliases

**Models Included:**
- **OpenAI**: gpt-5, gpt-4.1, gpt-4o, o3, o3-mini (7 variants)
- **Anthropic**: claude-sonnet-4.5, claude-opus-4.1, claude-3.5-haiku (6 variants)
- **Google**: gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite (5 variants)
- **Ollama**: llama3.1, llama3.2, mistral-large-2, deepseek-coder, starcode2 (5 variants)

---

### providers.py (4.3 KB) - PROVIDER DETECTION & CONFIG
Provider detection and persistent configuration management.

**Classes:**
- `ConfigManager`: Handles persistent configuration
- `ProviderDetector`: Detects available providers

**ConfigManager Responsibilities:**
- Load/save configuration from/to JSON
- Track last used model and provider
- Manage available providers list
- Auto-create default config

**ProviderDetector Responsibilities:**
- Check environment variables for API keys
- Detect Ollama local service availability
- Suggest provider setup for first-time users
- Generate helpful setup instructions

**Environment Variables Monitored:**
- `OPENAI_API_KEY` → OpenAI
- `ANTHROPIC_API_KEY` → Anthropic
- `GOOGLE_API_KEY` → Google
- `OLLAMA_BASE_URL` → Ollama

**Config Storage:**
Location: `~/.claude/llm-skill-config.json`

---

### executor.py (4.9 KB) - EXECUTION ENGINE
Handles LLM CLI invocation in different modes.

**Classes:**
- `LLMExecutor`: Main executor class

**Execution Modes:**
1. **Non-Interactive**: Input → Output (one-shot)
2. **Interactive**: REPL conversation loop

**Key Methods:**
- `execute_non_interactive()`: Process input and return output
- `execute_interactive()`: Start conversation loop
- `execute_with_prompt()`: Execute with custom system prompt
- `check_llm_installed()`: Verify llm CLI availability
- `get_llm_version()`: Get installed version

**Features:**
- Subprocess-based execution
- Timeout handling (5 minutes default)
- Error messages with helpful suggestions
- Input validation

---

### input_handler.py (4.9 KB) - INPUT PROCESSING
Flexible input handling for various sources and file types.

**Classes:**
- `InputHandler`: Handles all input scenarios

**Input Sources (Priority):**
1. Stdin/piped input
2. File path argument
3. Inline text prompt

**Supported File Types:**

**Text Files (25+):**
- `.txt`, `.md`, `.json`, `.csv`, `.log`, `.py`, `.js`, `.ts`
- `.jsx`, `.tsx`, `.html`, `.css`, `.xml`, `.yaml`, `.yml`
- `.toml`, `.sh`, etc.

**Media Files:**
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Audio**: `.mp3`, `.wav`, `.m4a`
- **Documents**: `.pdf`

**Media Handling:**
- Base64 encoding for images/audio
- PDF text extraction (requires PyPDF2)
- MIME type detection

**Key Methods:**
- `load_input()`: Load from any source
- `load_file()`: Load and process file
- `has_stdin()`: Check for piped input
- `read_stdin()`: Read from stdin
- `get_file_info()`: Get file metadata

---

## 🔧 Configuration Files

### requirements.txt (143 bytes)
Python package dependencies.

**Required:**
- `llm >= 0.14.0`

**Optional:**
- `PyPDF2 >= 3.0.0` - PDF support
- `rich >= 13.0.0` - Enhanced output formatting

---

### SKILL.md (Claude Code Integration)
Skill definition file for Claude Code system.
- Skill metadata (name, description)
- Usage trigger points
- Integration instructions

---

### Slash Command Integration

**Location:** `~/.claude/commands/llm.md`

Command definition for `/llm` slash command support.
- Usage examples
- Supported models
- Configuration reference

---

## 📊 File Statistics

| Category | Files | Size | Purpose |
|----------|-------|------|---------|
| **Documentation** | 7 | ~40 KB | User guides & technical docs |
| **Python Core** | 5 | ~27 KB | Implementation |
| **Config** | 1 | <1 KB | Dependencies |
| **Total** | 13 | ~68 KB | Complete skill |

---

## 🎯 File Reading Guide

### For Users

1. **First Time?** → Start with `START_HERE.md`
2. **Quick Setup?** → Read `QUICKSTART.md`
3. **Need Details?** → Check `README.md`
4. **Installation Help?** → See `INSTALL.md`

### For Developers

1. **Overview?** → Check `IMPLEMENTATION_SUMMARY.md`
2. **Architecture?** → Read `llm_skill.py` + `IMPLEMENTATION_SUMMARY.md`
3. **Models?** → Look at `models.py`
4. **Configuration?** → See `providers.py`
5. **Execution?** → Study `executor.py`
6. **Input?** → Check `input_handler.py`

### For Maintainers

1. Start with `IMPLEMENTATION_SUMMARY.md` (overview)
2. Check `SKILL.md` (integration points)
3. Review `FILES.md` (this file, dependencies)
4. Study individual Python modules in order:
   - `models.py` (data)
   - `providers.py` (config)
   - `input_handler.py` (input)
   - `executor.py` (execution)
   - `llm_skill.py` (orchestration)

---

## 📦 Installation Checklist

- [ ] Python 3.8+
- [ ] `pip install llm`
- [ ] Set API key (at least one provider)
- [ ] Run `pip install -r requirements.txt` (optional but recommended)
- [ ] Run `/llm --setup` to verify

---

## 🔍 Key Locations

```
~/.claude/skills/llm-cli/        ← Skill directory
├── llm_skill.py                ← Main program
├── *.py                        ← Support modules
├── SKILL.md                    ← Claude integration
├── START_HERE.md               ← User entry point
├── README.md                   ← Full documentation
├── QUICKSTART.md               ← Quick reference
├── INSTALL.md                  ← Setup guide
├── IMPLEMENTATION_SUMMARY.md   ← Technical docs
└── requirements.txt            ← Dependencies

~/.claude/commands/llm.md        ← Slash command definition

~/.claude/llm-skill-config.json  ← User configuration (auto-created)
```

---

## 📝 File Dependencies Graph

```
llm_skill.py (Main)
  ├── models.py (Model definitions)
  ├── providers.py (Config & detection)
  ├── executor.py (Execution)
  │   └── subprocess (built-in)
  ├── input_handler.py (Input)
  │   ├── base64 (built-in)
  │   └── PyPDF2 (optional)
  └── argparse (built-in)

providers.py
  ├── json (built-in)
  ├── subprocess (built-in)
  └── pathlib (built-in)

input_handler.py
  ├── base64 (built-in)
  ├── pathlib (built-in)
  └── PyPDF2 (optional)
```

---

## ✅ Completeness Checklist

- ✅ Core Python implementation (5 modules)
- ✅ Comprehensive documentation (7 guides)
- ✅ 30+ latest LLM models
- ✅ 4 provider support
- ✅ Configuration system
- ✅ Slash command integration
- ✅ Error handling
- ✅ File type support
- ✅ Examples and tutorials
- ✅ Troubleshooting guides
- ✅ Installation instructions
- ✅ Technical documentation

---

**Last Updated:** November 3, 2025
**Version:** 1.0.0
**Status:** Complete and Production-Ready
