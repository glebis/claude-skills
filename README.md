# Claude Skills

A collection of skills for [Claude Code](https://claude.com/claude-code) that extend AI capabilities with specialized workflows, tools, and domain expertise.

## 📦 Available Skills

### [Deep Research](./deep-research/)
Comprehensive research automation using OpenAI's Deep Research API (o4-mini-deep-research model).

**Features:**
- 🤖 Smart prompt enhancement with interactive clarifying questions
- 🔍 Web search with comprehensive source extraction
- 💾 Automatic markdown file generation with timestamped reports
- ⚡ Token-optimized for long-running tasks (10-20 min)
- 📊 Saves ~19,000 tokens per research vs. polling approach

**Use when:** You need in-depth research with web sources, analysis, or topic exploration.

## 🚀 Installation

### Using Claude Code

1. Download the skill zip file from the [releases](../../releases) or clone this repo
2. Extract to your Claude Code skills directory (usually `~/.claude/skills/`)
3. The skill will be automatically available in Claude Code

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/glebis/claude-skills.git

# Copy skill to Claude Code skills directory
cp -r claude-skills/deep-research ~/.claude/skills/

# Set up environment (for deep-research skill)
cd ~/.claude/skills/deep-research
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## 📋 Requirements

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
