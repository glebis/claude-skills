# Claude Skills

A collection of skills for [Claude Code](https://claude.com/claude-code) that extend AI capabilities with specialized workflows, tools, and domain expertise.

## 📦 Available Skills

### [LLM CLI](./llm-cli/) ⭐ NEW
Unified interface for processing text with multiple LLM providers from a single CLI.

**Features:**
- 🎯 Support for 6 LLM providers (OpenAI, Anthropic, Google, Groq, OpenRouter, Ollama)
- 🚀 40+ configured models with intelligent selection and aliasing
- 📁 Process files, stdin, or inline text (25+ file types supported)
- 💬 Both non-interactive and interactive (REPL) execution modes
- 🔄 Persistent configuration that remembers your last used model
- 🆓 Free fast inference options (Groq, OpenRouter, Ollama)

**Quick Start:**
```bash
# Install llm CLI
pip install llm

# Set Groq API key (free, no credit card)
export GROQ_API_KEY='gsk_...'

# Use it
llm -m groq-llama-3.3-70b "Your prompt"
```

**Documentation:**
- [START_HERE.md](./llm-cli/START_HERE.md) - 5-minute quick start
- [QUICK_REFERENCE.md](./llm-cli/QUICK_REFERENCE.md) - Command cheat sheet
- [GROQ_INTEGRATION.md](./llm-cli/GROQ_INTEGRATION.md) - Free fast inference setup
- [OPENROUTER_INTEGRATION.md](./llm-cli/OPENROUTER_INTEGRATION.md) - 200+ model access

**Use when:** You want to process text with LLMs, compare models, or build AI-powered workflows.

---

### [Deep Research](./deep-research/)
Comprehensive research automation using OpenAI's Deep Research API (o4-mini-deep-research model).

**Features:**
- 🤖 Smart prompt enhancement with interactive clarifying questions
- 🔍 Web search with comprehensive source extraction
- 💾 Automatic markdown file generation with timestamped reports
- ⚡ Token-optimized for long-running tasks (10-20 min)
- 📊 Saves ~19,000 tokens per research vs. polling approach

**Use when:** You need in-depth research with web sources, analysis, or topic exploration.

---

### [PDF Generation](./pdf-generation/)
Professional PDF generation from markdown with Eisvogel template and EB Garamond fonts.

**Features:**
- 📄 Convert markdown to professional PDFs
- 🎨 Support for English and Russian documents
- 🖼️ Color-coded themes for different document types
- ✍️ Professional typography with EB Garamond fonts
- 📋 White papers, research documents, marketing materials

**Use when:** You need to create professional PDF documents from markdown with publication-quality formatting.

---

### [YouTube Transcript](./youtube-transcript/)
Extract YouTube video transcripts with metadata and save as Markdown to Obsidian vault.

**Features:**
- 📝 Download transcripts without downloading video/audio files
- 🌐 Auto language detection (English first, Russian fallback)
- 📊 YAML frontmatter with complete metadata (title, channel, date, stats, tags)
- 📑 Chapter-based organization with timestamps
- 🔄 Automatic deduplication of subtitle artifacts
- 💾 Direct save to Obsidian vault

**Quick Start:**
```bash
python scripts/extract_transcript.py <youtube_url>
```

**Use when:** You need to extract YouTube video transcripts, convert videos to text, or save video content to your knowledge base.

---

### [Chrome History](./chrome-history/)
Query Chrome browsing history with natural language search and filtering.

**Features:**
- 🔍 Natural language search of browsing history
- 📅 Filter by date range, article type, keywords
- 🌐 Search specific websites
- ⚡ Fast historical data retrieval

**Use when:** You need to find and recall websites you've visited, search by topic or date.

---

### [ElevenLabs Text-to-Speech](./elevenlabs-tts/)
Convert text to high-quality audio files using ElevenLabs API with customizable voice parameters.

**Features:**
- 🎙️ 7 pre-configured voice presets (rachel, adam, bella, elli, josh, arnold, ava)
- 🎚️ Voice parameter customization (stability, similarity boost)
- 📝 Support for any text length
- 🔧 Both CLI and Python module interfaces
- 🎵 MP3 audio output with automatic directory creation

**Quick Start:**
```bash
cd ~/.claude/skills/elevenlabs-tts
pip install -r requirements.txt
# Add your API key to .env
python scripts/elevenlabs_tts.py "Welcome to Claude Code"
```

**Use when:** You need text-to-speech generation, audio narration, voice synthesis, or want to speak generated content aloud.

## 🚀 Installation

### Using Claude Code

1. Download the skill zip file from the [releases](../../releases) or clone this repo
2. Extract to your Claude Code skills directory (usually `~/.claude/skills/`)
3. The skill will be automatically available in Claude Code

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/glebis/claude-skills.git

# Copy desired skill to Claude Code skills directory
cp -r claude-skills/llm-cli ~/.claude/skills/
# or
cp -r claude-skills/deep-research ~/.claude/skills/
# or
cp -r claude-skills/youtube-transcript ~/.claude/skills/

# For llm-cli: Install Python dependencies
cd ~/.claude/skills/llm-cli
pip install -r requirements.txt

# For deep-research: Set up environment
cd ~/.claude/skills/deep-research
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# For youtube-transcript: Install yt-dlp
pip install yt-dlp
```

## 📋 Requirements

### LLM CLI Skill
- Python 3.8+
- `llm` CLI tool: `pip install llm`
- At least one API key (free options available):
  - **Groq**: https://console.groq.com/keys (free, no credit card)
  - **OpenRouter**: https://openrouter.ai/keys (free account)
  - **Ollama**: https://ollama.ai (free, local)
  - Or paid APIs: OpenAI, Anthropic, Google

### Deep Research Skill
- Python 3.7+
- OpenAI API key with access to Deep Research API
- Internet connection

**⚠️ Important:** OpenAI requires **organization verification** to access certain models via API, including `o4-mini-deep-research`.

To verify your organization:
1. Go to https://platform.openai.com/settings/organization/general
2. Click "Verify Organization"
3. Complete the automatic ID verification process
4. Wait up to 15 minutes for access to propagate

Without verification, you'll receive a `model_not_found` error when trying to use the Deep Research API.

### YouTube Transcript Skill
- Python 3.7+
- `yt-dlp`: `pip install yt-dlp`
- Internet connection

## 💡 Usage

Skills are automatically triggered by Claude Code based on your requests. For example:

```
User: "Research the most effective open-source RAG solutions"
Claude: [Triggers deep-research skill]
        - Asks clarifying questions
        - Enhances prompt with parameters
        - Runs comprehensive research
        - Saves markdown report with sources
```

## 🔧 Configuration

### Deep Research

Create a `.env` file in the skill directory:

```bash
OPENAI_API_KEY=your-key-here
```

Or export as environment variable:

```bash
export OPENAI_API_KEY="your-key-here"
```

## 📖 Documentation

Each skill includes comprehensive documentation:
- `SKILL.md` - Complete skill overview and usage guide
- `CHANGELOG.md` - Version history and updates
- `references/` - Detailed workflow documentation

## 🤝 Contributing

Contributions are welcome! To add a new skill:

1. Fork this repository
2. Create a new skill following the structure in `deep-research/`
3. Include comprehensive documentation
4. Submit a pull request

## 📝 Skill Structure

```
skill-name/
├── SKILL.md              # Skill metadata and documentation
├── CHANGELOG.md          # Version history
├── .env.example          # Example environment configuration
├── scripts/              # Executable orchestration scripts
├── assets/               # Core scripts and resources
└── references/           # Detailed documentation
```

## 🏗️ Building Skills

For guidance on creating your own skills, see the [skill-creator guide](https://docs.claude.com/docs/claude-code/skills).

## 📜 License

MIT License - see individual skill directories for specific licenses.

## 🔗 Links

- [Claude Code Documentation](https://docs.claude.com/docs/claude-code)
- [Anthropic](https://www.anthropic.com)
- [OpenAI Deep Research API](https://platform.openai.com/docs/guides/deep-research)

---

**Note:** Skills require Claude Code to function. These are not standalone tools.
