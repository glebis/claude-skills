# Claude Skills

A collection of skills for [Claude Code](https://claude.com/claude-code) that extend AI capabilities with specialized workflows, tools, and domain expertise.

## 📦 Available Skills

### [Insight Extractor](./insight-extractor/) ⭐ NEW
Parse Claude Code's built-in `/insights` report and extract actionable items into structured, trackable markdown files. Designed for Obsidian vaults but works with any markdown-based knowledge system.

**Features:**
- 📊 Extracts 6 categories: action items, prompts/patterns, technical learnings, workflow improvements, tool discoveries, automation candidates
- 🤖 Auto-creates task files for automation candidates (with agent-runnable tagging)
- 🔗 Links insights to daily notes and updates a Map of Content
- 💬 Interactive mode (`--interactive`) to cherry-pick items via AskUserQuestion
- ⚙️ Configure mode (`--configure`) to set folders, date format, and preferences
- 🖥️ Machine-specific filenames (for multi-machine setups)
- 📝 TLDR + key insight summary on completion

**Quick Start:**
```bash
# Run /insights first, then extract
/insight-extractor

# Interactive -- review and filter each category
/insight-extractor --interactive

# Configure output paths, date format, etc.
/insight-extractor --configure
```

**Use when:** After running `/insights` to persist analysis into your vault, during weekly reviews, or to discover automation candidates from session patterns.

---

### [Doctor G](./doctorg/)
Evidence-based health research using tiered trusted sources with GRADE-inspired evidence ratings. Integrates Apple Health data for personalized context.

**Features:**
- 🔬 3 depth levels: Quick (WebSearch), Deep (+Tavily), Full (+Firecrawl)
- 📊 GRADE-inspired evidence strength ratings (Strong/Moderate/Weak/Minimal/Contested)
- 🏥 40+ curated trusted sources across 4 tiers (primary research → journalism)
- ❤️ Apple Health integration for personalized recommendations
- ⚖️ Expert comparison mode (detects "X vs Y" questions)
- 🔍 Topic-aware source prioritization (nutrition, exercise, sleep, cardiovascular, etc.)
- ⚠️ Red flag detection (retracted studies, industry bias, predatory journals)

**Quick Start:**
```bash
# Quick answer (~30s)
/doctorg Is creatine safe for daily use?

# Deep research (~90s)
/doctorg --deep Huberman vs Attia on fasted training

# Full investigation (~3min)
/doctorg --full Safety profile of long-term melatonin supplementation

# Without personal health data
/doctorg --no-personal Best stretching protocol for lower back pain
```

**Use when:** Asking any health, nutrition, exercise, sleep, or wellness question and wanting evidence-based answers with explicit strength ratings rather than opinion.

---

### [Agency Docs Updater](./agency-docs-updater/)
End-to-end pipeline for publishing Claude Code lab meetings. Single `/agency-docs-updater` invocation replaces 5+ manual steps: finds Fathom transcript, downloads video, uploads to YouTube, generates fact-checked Russian summary, creates MDX, and deploys to Vercel.

**Features:**
- 🔄 Full pipeline: transcript → video download → YouTube upload → summary → MDX → deploy
- 📝 Fact-checked Russian summaries via claude-code-guide agent
- 🎥 YouTube + Yandex.Disk upload with resume support
- 📊 Lesson HTML copied to public/ and linked in meeting page
- ✅ Local build verification + Vercel deployment check
- 🔢 Auto-detect or specify meeting number

**Quick Start:**
```bash
# Run full pipeline (invoke as Claude Code skill)
/agency-docs-updater

# Or use the script directly
python3 scripts/update_meeting_doc.py \
  transcript.md youtube_url summary.md [-n 08] [--update]
```

**Use when:** Publishing Claude Code lab sessions — automates the entire flow from Fathom recording to live documentation site.

---

### [De-AI Text Humanizer](./de-ai/) ⭐ NEW
Transform AI-sounding text into human, authentic writing while preserving meaning and facts. Research-backed approach focusing on quality over detection evasion.

**Features:**
- 🤖 Interactive context gathering (purpose, audience, constraints)
- 🌍 Language-specific optimization (Russian, German, English, Spanish, French)
- 📝 Register-aware humanization (personal, essay, technical, academic)
- 🔍 6-level AI tell diagnosis (structural, lexical, voice, rhetorical)
- 📊 Research-backed (7 academic papers + 30+ commercial tools analyzed)
- 💡 Optional change explanations
- ⚡ No word limits (unlike commercial tools)
- 🎯 Meaning preservation priority vs. detection evasion

**Quick Start:**
```bash
# Interactive mode (asks questions)
/de-ai --file article.md

# Quick mode (no questions)
/de-ai --file article.md --interactive false

# Specify language and register
/de-ai --file text.md --language ru --register essay

# Show what AI tells were removed
/de-ai --file content.md --explain true
```

**Use when:** You need to improve AI-generated text quality, remove bureaucratic language (канцелярит), humanize drafts while preserving facts, or refine professional writing across languages.

---

### [Automation Advisor](./automation-advisor/) ⭐ NEW
Quantified ROI analysis for automation decisions with voice-enabled web interface. Analytical precision design.

**Features:**
- 📊 8 structured questions transforming intuition into data
- 💰 Break-even analysis with time/frequency scoring
- 🎙️ Voice input via Groq Whisper transcription
- 🗣️ Browser TTS for voice output
- 🎨 Sophisticated cream theme with editorial typography
- 📱 Multi-user session support
- ⌨️ Keyboard-first interaction design

**Quick Start:**
```bash
# Install dependencies
pip install flask groq python-dotenv

# Add Groq API key (optional, for voice)
export GROQ_API_KEY="your-key"

# Start web server
python3 server_web.py

# Open browser
open http://localhost:8080
```

**Use when:** Deciding whether to automate repetitive tasks - transforms "this feels tedious" into quantified recommendations with clear next steps.

---

### [Decision Toolkit](./decision-toolkit/) ⭐ NEW
Generate structured decision-making tools — step-by-step guides, bias checkers, scenario matrices, and interactive dashboards.

**Features:**
- 🎯 7 decision frameworks (First Principles, 10-10-10, Pre-Mortem, Regret Minimization, etc.)
- 🧠 Comprehensive bias encyclopedia (20+ cognitive biases with counter-questions)
- 📊 Interactive HTML wizards with Agency neobrutalism styling
- 📝 Markdown export with decision records
- 🎙️ Voice summary templates for Orpheus TTS
- ⚖️ Opportunity cost calculators and scenario matrices

**Frameworks Included:**
- First Principles Thinking (5 core questions)
- Opportunity Cost Calculator
- Scenario Matrix with probability calibration
- Pre-Mortem Analysis
- 10-10-10 Framework (Suzy Welch)
- Regret Minimization (Jeff Bezos method)
- Weighted Decision Matrix

**Quick Start:**
```bash
# Copy to skills directory
cp -r decision-toolkit ~/.claude/skills/

# Invoke for a decision
/decision-toolkit "Should I switch to a new tech stack?"
```

**Use when:** Facing significant choices requiring systematic analysis — career moves, technology decisions, major purchases, strategic pivots.

---

### [Fathom](./fathom/) ⭐ NEW
Fetch meetings, transcripts, summaries, action items, and download video recordings from Fathom API.

**Features:**
- 📋 List recent meetings with recording IDs
- 📝 Fetch full transcripts with speaker attribution
- 🤖 AI-generated meeting summaries from Fathom
- ✅ Action items with assignees and completion status
- 👥 Participant info from calendar invites
- 🔗 Links to Fathom recordings and share URLs
- 🎥 Download video recordings via M3U8 streaming
- ✓ Automatic video validation with retry mechanism
- 🔬 Optional integration with transcript-analyzer skill

**Quick Start:**
```bash
# Install dependencies
pip install requests python-dotenv

# Requires ffmpeg for video downloads
brew install ffmpeg  # macOS
# or: apt-get install ffmpeg  # Linux

# Add API key
echo "FATHOM_API_KEY=your-key" > ~/.claude/skills/fathom/scripts/.env

# List recent meetings
python3 scripts/fetch.py --list

# Fetch today's meetings
python3 scripts/fetch.py --today

# Download video recording
python3 scripts/fetch.py --id abc123 --download-video

# Fetch and analyze
python3 scripts/fetch.py --today --analyze
```

**Use when:** You need to fetch Fathom meeting recordings, download video files, sync transcripts to your vault, or extract meeting data via API.

---

### [Retrospective](./retrospective/) ⭐ NEW
Session retrospective for continual learning. Reviews conversations, extracts learnings, updates skills.

**Features:**
- 🔄 Analyze session for successes, failures, and discoveries
- 📝 Update skill files with dated learnings
- ⚠️ Document failures explicitly (prevents repeating mistakes)
- 📊 Surface patterns for skill improvement
- 🎯 Compound knowledge over sessions

**Quick Start:**
```bash
# Copy to skills directory
cp -r retrospective ~/.claude/skills/

# Invoke at end of session
/retrospective
```

**Use when:** End of coding sessions to capture learnings before context is lost. Based on [Continual Learning in Claude Code](https://www.youtube.com/watch?v=sWbsD-cP4rI) concepts.

---

### [GitHub Gist](./github-gist/) ⭐ NEW
Publish files and notes as GitHub Gists for easy sharing.

**Features:**
- 🔗 Publish any file as a shareable gist URL
- 🔒 Secret (unlisted) by default for safety
- 🌐 Optional public gists (visible on profile)
- 📥 Support stdin for quick snippets
- 🖥️ Uses `gh` CLI (recommended) or falls back to API

**Quick Start:**
```bash
# Publish file as secret gist
python3 scripts/publish_gist.py ~/notes/idea.md

# Public gist with description
python3 scripts/publish_gist.py code.py --public -d "My utility script"

# Quick snippet from stdin
echo "Hello world" | python3 scripts/publish_gist.py - -f "hello.txt"

# Publish and open in browser
python3 scripts/publish_gist.py doc.md --open
```

**Setup:**
```bash
# Option 1: gh CLI (recommended)
gh auth login

# Option 2: Environment variable
# Get token at https://github.com/settings/tokens (select 'gist' scope)
export GITHUB_GIST_TOKEN="ghp_your_token_here"
```

**Use when:** You want to share code snippets, notes, or files via a quick shareable URL.

---

### [Google Image Search](./google-image-search/)
Search and download images via Google Custom Search API with LLM-powered selection and Obsidian integration.

**Features:**
- 🔍 Simple query mode or batch processing from JSON config
- 🤖 LLM-powered image selection (picks best from candidates)
- 📝 Auto-generate search configs from plain text terms
- 📓 Obsidian note enrichment (extract terms, find images, insert below headings)
- 📊 Keyword-based scoring (required/optional/exclude terms, preferred hosts)
- 🖼️ Magic byte detection for proper file extensions

**Quick Start:**
```bash
# Simple query
python3 scripts/google_image_search.py --query "neural interface demo" --output-dir ./images

# Enrich Obsidian note with images
python3 scripts/google_image_search.py --enrich-note ~/vault/research.md

# Generate config from terms
python3 scripts/google_image_search.py --generate-config --terms "AI therapy" "VR mental health"
```

**Use when:** Finding images for articles, presentations, research docs, or enriching Obsidian notes with visuals.

---

### [Zoom](./zoom/) ⭐ NEW
Create and manage Zoom meetings and access cloud recordings via the Zoom API.

**Features:**
- 📅 List, create, update, delete scheduled meetings
- 🎥 Access cloud recordings with transcripts and summaries
- 📥 Get download links for MP4, audio, transcripts, chat logs
- 🔐 Dual auth: Server-to-Server OAuth (meetings) + User OAuth (recordings)

**Quick Start:**
```bash
# Check setup status
python3 scripts/zoom_meetings.py setup

# List upcoming meetings
python3 scripts/zoom_meetings.py list

# Create a meeting
python3 scripts/zoom_meetings.py create "Team Standup" --start "2025-01-15T10:00:00" --duration 30

# List recordings (last 30 days)
python3 scripts/zoom_meetings.py recordings --show-downloads
```

**Use when:** You need to create Zoom meetings, list scheduled calls, or access cloud recordings with transcripts.

---

### [Presentation Generator](./presentation-generator/)
Interactive HTML presentations with neobrutalism style and Anime.js animations.

**Features:**
- 🎬 HTML presentations with scroll-snap navigation
- 🎭 Anime.js animations (fade, slide, scale, stagger)
- 📸 Export to PNG, PDF, or video via Playwright
- 📊 11 slide types: title, content, two-col, code, stats, grid, ascii, terminal, image, quote, comparison
- 🎨 Neobrutalism style with brand-agency colors
- ⌨️ Keyboard navigation (arrows, space, R to replay)

**Quick Start:**
```bash
# Generate HTML from JSON
node scripts/generate-presentation.js --input slides.json --output presentation.html

# Export to PNG/PDF/video
node scripts/export-slides.js presentation.html --format png
node scripts/export-slides.js presentation.html --format pdf
node scripts/export-slides.js presentation.html --format video --duration 5
```

**Use when:** You need animated presentations, video slide decks, or interactive HTML slideshows.

---

### [Brand Agency](./brand-agency/)
Neobrutalism brand styling with social media template rendering.

**Features:**
- 🎨 Complete brand color palette (orange, yellow, blue, green, red)
- 📝 Typography: Geist (headings), EB Garamond (body), Geist Mono (code)
- 🖼️ 11 social media templates (Instagram, YouTube, Twitter, TikTok, Pinterest)
- 🎯 Neobrutalism style: hard shadows, 3px borders, zero radius
- ⚡ Playwright-based PNG rendering
- 📐 ASCII box-drawing decorations

**Quick Start:**
```bash
# Install Playwright
npm install playwright

# Render all templates
node scripts/render-templates.js

# Render specific template
node scripts/render-templates.js -t instagram/story-announcement

# List templates
node scripts/render-templates.js --list
```

**Use when:** You need branded graphics, social media images, presentations with consistent neobrutalism styling.

---

### [Gmail](./gmail/)
Search and fetch emails via Gmail API with flexible query options and output formats.

**Features:**
- 🔍 Free-text search with Gmail query syntax
- 📧 Filter by sender, recipient, subject, label, date
- 📋 List labels
- 📎 Download attachments
- 🔐 Configurable OAuth scopes (readonly/modify/full)
- 📄 Markdown or JSON output

**Quick Start:**
```bash
# Install dependencies
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Authenticate (opens browser)
python scripts/gmail_search.py auth

# Search emails
python scripts/gmail_search.py search "meeting notes"
python scripts/gmail_search.py search --from "boss@company.com" --unread
```

**Use when:** You need to search, read, or download emails from Gmail.

---

### [Telegram](./telegram/)
Fetch, search, download, and send Telegram messages with flexible filtering and output options.

**Features:**
- 📬 List chats with unread counts
- 📥 Fetch recent messages (all chats or specific)
- 🔍 Search messages by content
- 📨 Send messages to chats or @usernames
- ↩️ Reply to specific messages
- 💬 Send to forum topics (groups with topics)
- 📎 Send and download media files
- 💾 Save to file (token-efficient archiving with --with-media)
- 📝 Output to Obsidian daily/person notes

**Quick Start:**
```bash
# Install dependency
pip install telethon

# List chats
python scripts/telegram_fetch.py list

# Get recent messages
python scripts/telegram_fetch.py recent --limit 20

# Send message
python scripts/telegram_fetch.py send --chat "@username" --text "Hello!"
```

**Use when:** You need to read, search, or send Telegram messages from Claude Code.

---

### [Telegram Post](./telegram-post/) ⭐ NEW
Create, preview, and publish formatted Telegram posts from draft markdown files with HTML formatting and media. Built for [@klodkot](https://t.me/klodkot) and Gleb Kalinin's other Telegram channels -- channel configs (footers, tags, language) are hardcoded but the pattern is easy to adapt.

**Features:**
- 📝 Create drafts with proper frontmatter for any configured channel
- 🔄 Markdown to Telegram HTML conversion (bold, italic, links, headers)
- 🛡️ Formatting safety check -- refuses to send if stray markdown detected
- 🎬 Video attached as caption (not separate reply)
- 📤 Default target: Saved Messages (safe preview before publishing)
- 📦 Post-publish: updates frontmatter, moves to published/, updates channel index
- 🏷️ Channel-aware: footers, tags reference, language defaults

**Configured channels:** [@klodkot](https://t.me/klodkot), @mentalhealthtech, @toolbuildingape, @opytnymputem

**Quick Start:**
```bash
# Create a draft
python3 scripts/post.py create "my-post-slug" --topic "Topic" --source "https://..."

# Preview (always do this first)
python3 scripts/post.py send "Channels/klodkot/drafts/20260211-my-post.md" --dry-run

# Send to saved messages for review
python3 scripts/post.py send "Channels/klodkot/drafts/20260211-my-post.md"

# Publish to channel (triggers post-publish: move, frontmatter update, index)
python3 scripts/post.py send "Channels/klodkot/drafts/20260211-my-post.md" -c "@klodkot"
```

**Use when:** Creating, previewing, or publishing Telegram channel posts from Obsidian draft files. Note: channel configs are specific to Gleb's channels -- fork and edit `CHANNEL_CONFIG` in `post.py` for your own.

---

### [Telegram Telethon](./telegram-telethon/) ⭐ NEW
Full Telethon API wrapper with daemon mode and Claude Code integration. Monitor chats, auto-respond with Claude, and manage sessions.

**Features:**
- 🔄 Daemon mode with configurable triggers (regex patterns)
- 🤖 Auto-spawn Claude Code sessions per chat
- 💾 Session persistence across restarts
- 📬 All basic operations: list, recent, search, send, edit, delete, forward
- 🎤 Voice message transcription (Telegram API, Groq, or local Whisper)
- 📎 Media download with type filtering
- 📓 Obsidian integration (daily notes, person notes)
- 🧵 Forum/topic support

**Quick Start:**
```bash
# Install dependencies
pip install telethon rich questionary

# Interactive setup
python3 scripts/tg.py setup

# Check status
python3 scripts/tg.py status

# List chats
python3 scripts/tg.py list

# Start daemon (monitors for triggers)
python3 scripts/tgd.py start --foreground
```

**Daemon Configuration** (`~/.config/telegram-telethon/daemon.yaml`):
```yaml
triggers:
  - chat: "@yourusername"
    pattern: "^/claude (.+)$"
    action: claude
    reply_mode: inline
```

**Use when:** You need advanced Telegram automation, background monitoring, or Claude-powered chat responses.

---

### [LLM CLI](./llm-cli/)
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
Professional PDF generation from markdown with mobile-optimized and desktop layouts.

**Features:**
- 📄 Convert markdown to professional PDFs
- 📱 Mobile-friendly layout (6x9in) optimized for phones/tablets
- 🖨️ Desktop/print layout (A4) for documents and archival
- 🎨 Support for English and Russian documents
- 🖼️ Color-coded themes for different document types
- ✍️ Professional typography with EB Garamond fonts
- 📋 White papers, research documents, marketing materials

**Quick Start:**
```bash
# Mobile-optimized PDF (default for Telegram)
python scripts/generate_pdf.py doc.md --mobile

# Desktop/print PDF
python scripts/generate_pdf.py doc.md -t research

# Russian document
python scripts/generate_pdf.py doc.md --russian --mobile
```

**Use when:** You need to create professional PDF documents from markdown - mobile layout for sharing via messaging apps, desktop for printing and archival.

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

### [Browsing History](./browsing-history/) ⭐ NEW
Query browsing history from **all synced Chrome devices** (iPhone, iPad, Mac, desktop) with natural language.

**Features:**
- 📱 Multi-device support (iPhone, iPad, Mac, desktop, Android)
- 🔍 Natural language queries ("yesterday", "last week", "articles about AI")
- 🤖 LLM-powered smart categorization
- 📊 Group by domain, category, or date
- 💾 Export to Markdown or JSON
- 📝 Save directly to Obsidian vault

**Quick Start:**
```bash
# Initialize database
python3 scripts/init_db.py

# Sync local Chrome history
python3 scripts/sync_chrome_history.py

# Query history
python3 browsing_query.py "yesterday" --device iPhone
python3 browsing_query.py "AI articles" --days 7 --categorize
python3 browsing_query.py "last week" --output ~/vault/history.md
```

**Use when:** You need to search browsing history across all your devices, find articles by topic, or export history to your notes.

---

### [Chrome History](./chrome-history/)
Query **local** Chrome browsing history with natural language search and filtering.

**Features:**
- 🔍 Natural language search of browsing history
- 📅 Filter by date range, article type, keywords
- 🌐 Search specific websites
- ⚡ Fast historical data retrieval

**Use when:** You need quick access to local desktop Chrome history only.

---

### [Health Data](./health-data/) ⭐ NEW
Query and analyze Apple Health data from SQLite database with multiple output formats.

**Features:**
- 📊 Query 6.3M+ health records across 43 metric types
- 💓 Daily summaries, weekly trends, sleep analysis, vitals, activity rings, workouts
- 📄 Output formats: Markdown, JSON, FHIR R4, ASCII charts
- 🏥 FHIR R4 with LOINC codes for healthcare interoperability
- 📈 Pre-built queries + raw SQL templates for ad-hoc analysis
- 🎯 ASCII visualization with Unicode bar charts

**Quick Start:**
```bash
# Daily summary
python scripts/health_query.py daily --date 2025-11-29

# Weekly trends in JSON
python scripts/health_query.py --format json weekly --weeks 4

# Sleep analysis in FHIR format
python scripts/health_query.py --format fhir sleep --days 7

# ASCII charts
python scripts/health_query.py --format ascii activity --days 30

# Custom SQL
python scripts/health_query.py query "SELECT * FROM workouts LIMIT 5"
```

**Use when:** You need to analyze Apple Health metrics, generate health reports, export data in FHIR format, or visualize fitness/sleep patterns.

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

---

### [FireCrawl Research](./firecrawl-research/) ⭐ NEW
Research automation using FireCrawl API with academic writing templates and bibliography generation.

**Features:**
- 🔍 Extract research topics from markdown headers and `[research]` tags
- 🌐 Search and scrape web sources automatically
- 📚 Generate BibTeX bibliographies from research results
- 📝 Pandoc and MyST templates for academic papers
- ⚡ Built-in rate limiting for free tier (5 req/min)
- 📄 Export to PDF/DOCX with citations

**Quick Start:**
```bash
# Install dependencies
pip install python-dotenv requests

# Add API key to .env
echo "FIRECRAWL_API_KEY=fc-your-key" > ~/.claude/skills/firecrawl-research/.env

# Research topics from markdown
python scripts/firecrawl_research.py topics.md ./output 5

# Generate bibliography
python scripts/generate_bibliography.py output/*.md -o refs.bib

# Convert to PDF with citations
python scripts/convert_academic.py paper.md pdf
```

**Use when:** You need to research topics from the web, write academic papers with citations, or build bibliographies from scraped sources.

---

### [Transcript Analyzer](./transcript-analyzer/) ⭐ NEW
Analyze meeting transcripts using Cerebras AI to extract decisions, action items, and terminology.

**Features:**
- 📋 Extract decisions, action items, opinions, questions
- 📖 Build domain-specific glossaries from discussions
- 🎯 Confidence scores for each extraction
- ⚡ Fast inference via Cerebras (llama-3.3-70b)
- 📊 YAML frontmatter with processing metadata
- 🔄 Chunked processing for long transcripts

**Quick Start:**
```bash
# Install dependencies
cd ~/.claude/skills/transcript-analyzer/scripts && npm install

# Add API key
echo "CEREBRAS_API_KEY=your-key" > scripts/.env

# Analyze transcript
npm run cli -- /path/to/meeting.md -o analysis.md

# Include original transcript
npm run cli -- meeting.md -o analysis.md --include-transcript

# Skip glossary
npm run cli -- meeting.md -o analysis.md --no-glossary
```

**Use when:** You need to extract action items from meetings, find decisions in conversations, or build glossaries from recorded discussions.

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
cp -r claude-skills/doctorg ~/.claude/skills/
# or
cp -r claude-skills/llm-cli ~/.claude/skills/
# or
cp -r claude-skills/deep-research ~/.claude/skills/
# or
cp -r claude-skills/youtube-transcript ~/.claude/skills/
# or
cp -r claude-skills/telegram ~/.claude/skills/
# or
cp -r claude-skills/gmail ~/.claude/skills/
# or
cp -r claude-skills/brand-agency ~/.claude/skills/
# or
cp -r claude-skills/health-data ~/.claude/skills/
# or
cp -r claude-skills/firecrawl-research ~/.claude/skills/
# or
cp -r claude-skills/transcript-analyzer ~/.claude/skills/
# or
cp -r claude-skills/retrospective ~/.claude/skills/
# or
cp -r claude-skills/github-gist ~/.claude/skills/
# or
cp -r claude-skills/decision-toolkit ~/.claude/skills/

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

### Telegram Skill
- Python 3.8+
- `telethon`: `pip install telethon`
- Telegram API credentials (api_id, api_hash from https://my.telegram.org)
- Pre-configured session in `~/.telegram_dl/` (run telegram_dl.py to authenticate)

### Telegram Telethon Skill
- Python 3.8+
- `telethon`, `rich`, `questionary`: `pip install telethon rich questionary`
- Telegram API credentials (api_id, api_hash from https://my.telegram.org)
- For voice transcription: `GROQ_API_KEY` env var or `pip install openai-whisper`
- Config stored in `~/.config/telegram-telethon/`

### Gmail Skill
- Python 3.8+
- Google API libraries: `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
- OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Gmail API enabled in your Google Cloud project

### Brand Agency Skill
- Node.js 18+
- Playwright: `npm install playwright`
- Google Fonts (loaded automatically via CSS)

### Health Data Skill
- Python 3.8+
- SQLite database at `~/data/health.db` (imported from Apple Health export)
- To import: Use the [apple_health_export](https://github.com/glebis/apple_health_export) project

### FireCrawl Research Skill
- Python 3.8+
- `python-dotenv`, `requests`: `pip install python-dotenv requests`
- FireCrawl API key from https://firecrawl.dev

### Transcript Analyzer Skill
- Node.js 18+
- Cerebras API key from https://cloud.cerebras.ai

### Doctor G Skill
- Python 3.8+
- Requires **health-data** skill for Apple Health integration (optional)
- Requires **tavily-search** skill for `--deep` mode (optional)
- Requires **firecrawl-research** skill for `--full` mode (optional)

### GitHub Gist Skill
- Python 3.8+
- **Option 1 (Recommended):** GitHub CLI (`gh`) - install from https://cli.github.com, then run `gh auth login`
- **Option 2:** Personal Access Token with `gist` scope from https://github.com/settings/tokens

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
