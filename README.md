# Claude Skills

A collection of skills for [Claude Code](https://claude.com/claude-code) that extend AI capabilities with specialized workflows, tools, and domain expertise.

## 📦 Available Skills

### [TDD (Test-Driven Development)](./tdd/)
Multi-agent TDD orchestration with architecturally enforced context isolation. Uses Claude Code's Task tool to spawn separate subagents for test writing and implementation -- the Test Writer never sees implementation code, and the Implementer never sees the specification.

**Features:**
- Multi-agent context isolation: Test Writer, Implementer, and Refactorer run as separate Task subagents with strict information boundaries
- Strict RED -> GREEN -> REFACTOR phase enforcement
- `--auto` mode: run all slices without pausing, stop only on unrecoverable errors
- Inside-out vertical slicing by architectural layer (domain -> domain-service -> application -> infrastructure)
- Layer-specific test constraints and dependency rules per slice
- `layer_map` path validation: rejects Implementer writes to wrong-layer directories
- Post-RED test lint: blocks mocking libraries in domain/domain-service tests
- Full-repo import scan: catches dependency violations in untouched files
- Port interface rule: consumer defines the contract (Dependency Inversion)
- Retry loop: up to 5 fresh Implementer attempts with previous-attempt context (no accumulated history)
- Regression auto-fix: detects and repairs broken tests after implementation (3-attempt limit)
- Greenfield project support: handles empty codebases with no existing tests
- `run_tests.sh`: universal test runner wrapping 7 frameworks into structured JSON with timeout support
- `extract_api.sh`: public API surface extractor (signatures only, no bodies) for 7 languages
- Implementer always returns complete file content (no ambiguous partial patches)
- Failure recovery table covering 11 error scenarios with concrete recovery actions
- 18 documented anti-patterns with prevention guidance (incl. service locator, Active Record bleed)
- Session state via `.tdd-state.json` with `--resume` support
- 7 frameworks: Jest, Vitest, pytest, Go test, cargo test, RSpec, PHPUnit
- Bug-fix TDD: reproduce-first workflow

**Architecture:**
```
ORCHESTRATOR (main Claude context)
├─ Phase 0: Setup (detect framework, extract API, create state)
├─ Phase 1: Decompose into vertical slices -> user approves
├─ FOR EACH SLICE:
│   ├─ Phase 2 (RED):     Task(Test Writer)  <- spec + API only
│   ├─ Phase 3 (GREEN):   Task(Implementer)  <- failing test + error only
│   └─ Phase 4 (REFACTOR): Task(Refactorer)  <- all code + green results
└─ Summary
```

**Quick Start:**
```bash
# Copy to skills directory
cp -r tdd ~/.claude/skills/

# Interactive mode (pauses at each RED checkpoint)
/tdd "add user authentication with JWT tokens"

# Autonomous mode (runs all slices, stops only on errors)
/tdd --auto "add user authentication with JWT tokens"

# Resume a paused session
/tdd --resume

# Bug fix
/tdd "fix: cart total doesn't include tax"
```

**Design informed by:**
- [tdd-guard](https://github.com/nizos/tdd-guard) (hook-enforced TDD)
- [Matt Pocock's TDD Skill](https://www.aihero.dev/skill-test-driven-development-claude-code) (vertical slicing)
- [TDFlow](https://arxiv.org/html/2510.23761v1) (test quality as ceiling for implementation quality)
- [alexop.dev](https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/) (context isolation between phases)

**Use when:** Implementing features or fixing bugs where you want disciplined test-first development. Use `--auto` for maximum autonomy. The multi-agent architecture is especially valuable when single-context TDD produces tests that mirror implementation details.

---

### [NotebookLM](./notebooklm/) ⭐ NEW
Full CLI and Python API wrapper for Google NotebookLM. Lets you manage notebooks, sources, chat, artifacts (podcasts, videos, slides, quizzes, flashcards), notes, sharing, and research entirely from the terminal via natural language.

**Features:**
- Complete command coverage: notebooks, sources, chat, artifacts, notes, sharing, research, language
- Natural language mapping: "upload this folder and ask about X" → create + add sources + ask
- Artifact generation: audio (podcast), video, cinematic-video, slide-deck, quiz, flashcards, infographic, mind-map, data-table, report
- Batch operations: upload folders of .md files, multiple URLs, parallel research queries
- Python API reference: direct access to `notebooklm-py` async library for programmatic use
- Common workflows: create-add-ask, folder upload with summary, deep research, podcast generation
- Error handling: authentication, source processing, rate limiting, timeouts

**Quick Start:**
```bash
# Copy to skills directory
cp -r notebooklm ~/.claude/skills/

# Then just talk naturally:
# "create a notebook called My Research"
# "upload all markdown files from ./notes/"
# "ask the notebook about key themes"
# "generate a podcast about the findings"
# "download the podcast"
```

**Depends on:** [notebooklm-py](https://github.com/teng-lin/notebooklm-py) (v0.3.4+) — `pip install notebooklm-py`

**Use when:** Interacting with Google NotebookLM from Claude Code. Covers all CLI commands and the underlying Python API for advanced automation.

---

### [Temple Generator](./temple-generator/) ⭐
Generate a 3D interactive knowledge map (Inner Temple) from any Obsidian vault. Maps vault structure into a spatial mythology with concentric entity rings, synthesized audio, discovery mechanics, and multi-scale semantic zoom.

![Temple Generator Screenshot](./temple-generator/screenshot.png)

**Features:**
- Vault scanner extracts 10K+ notes, 39K+ link edges, computes centrality and clusters
- 15 entity types: gods, demigods, tensions, narratives, blind spots, spirits, crystals, values, trails, research, questions, depths, whispers, secrets, fields
- Dual vocabulary: canonical (portable) + poetic (mythic) naming
- Confidence-gated abstraction levels: entities → domains → tension axes → comparison
- Dual-graph common map: shared scaffold with divergence offsets for comparing two vaults
- Data-driven HTML template (Three.js) with Web Audio API soundtrack
- Electroacoustic audio: FM synthesis, ring modulation, filtered noise, arpeggios per entity type
- Arrow key navigation, immersive mode (Shift+.), install mode (?install)
- Hand tracking (MediaPipe), secret discovery engine, flythrough journey

**Architecture:**
```
Generation Pipeline (Claude)          Runtime Renderer (Template)
├─ extract_entities.py → vault-scan   ├─ Three.js scene from JSON
├─ Claude classifies entities         ├─ Concentric ring layout
├─ Builds abstraction levels          ├─ Audio per entity type
├─ Writes temple-data.json            ├─ Discovery mechanics
└─ Inlines into template              └─ Semantic zoom transitions
```

**Quick Start:**
```bash
cp -r temple-generator ~/.claude/skills/
/temple-generate ~/my-vault --inline
```

**Use when:** Visualizing any Obsidian vault as a 3D spatial mythology, comparing two knowledge graphs, or creating an art installation from structured knowledge.

---

### [Granola Meeting Importer](./granola/) ⭐ NEW
Query Granola's local cache and API to list meetings, view transcripts, and export to Obsidian vault in Fathom-compatible format. Includes auto-sync via macOS LaunchAgent.

**Features:**
- List all meetings from Granola's local cache with attendee and transcript info
- Show meeting details by ID prefix or title substring
- Get transcripts from local cache with API fallback
- Export to Obsidian markdown with Fathom-compatible frontmatter (`**Speaker**: text` format)
- Speaker attribution: microphone source mapped to meeting creator, system audio to "Other"
- API integration using Granola's local WorkOS auth token (no separate API key needed)
- **Auto-sync script** (`sync.sh`) — checks for new meetings every 15 min via LaunchAgent, exports only unseen ones, logs to `~/Library/Logs/granola-sync.log`
- 18 tests covering pure functions and CLI integration

**Quick Start:**
```bash
# Copy to skills directory
cp -r granola ~/.claude/skills/

# List meetings
python3 ~/.claude/skills/granola/scripts/granola.py list

# Export a meeting to Obsidian
python3 ~/.claude/skills/granola/scripts/granola.py export "meeting title"

# Get transcript
python3 ~/.claude/skills/granola/scripts/granola.py transcript abc123

# Set up auto-sync (see SKILL.md for LaunchAgent setup)
chmod +x ~/.claude/skills/granola/scripts/sync.sh
bash ~/.claude/skills/granola/scripts/sync.sh  # test run
```

**Use when:** Importing Granola meeting recordings and transcripts into an Obsidian vault, querying meeting history from the command line, or setting up automated transcript sync on a schedule.

---

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

### [Vault Daydream](./daydream/) ⭐ NEW
Multi-agent system that mines your Obsidian vault for non-obvious connections between notes, mimicking the brain's default mode network. Samples random note pairs, synthesizes connections via Sonnet, filters with Haiku critic. Inspired by [Gwern's LLM Daydreaming](https://gwern.net/ai-daydreaming).

**Features:**
- 🧠 Simulates the brain's default mode network for knowledge vaults
- 🎲 Recency-weighted random pair sampling (50 pairs per run)
- 🔀 Multi-agent architecture: Sonnet synthesizer + Haiku critic in parallel batches
- 📊 Quality filtering: only insights scoring >= 7.0 average (novelty, coherence, usefulness)
- 📝 Obsidian-native output: individual insight notes with wikilinks + daily digest
- 🔄 History dedup: tracks previously sampled pairs to avoid repetition
- 📅 Daily note integration with daydream summary

**Architecture:**
```
Skill (orchestrator)
  |-- Glob/Read: scan vault, extract excerpts
  |-- Generate 50 random pairs (recency-weighted)
  |-- Task(model: sonnet) x 10: synthesize connections  <-- parallel
  |-- Task(model: haiku) x 10: critique/score insights  <-- parallel
  |-- Filter (avg >= 7.0)
  +-- Write: save insight notes + daily digest
```

No external dependencies -- pure Claude Code tools (Glob, Read, Write, Bash, Task).

**Quick Start:**
```bash
# Copy to skills directory
cp -r daydream ~/.claude/skills/

# Edit instructions.md to set your VAULT_ROOT path
# Then invoke
/daydream
```

**Output:**
- `Daydreams/YYYYMMDD-slug.md` -- individual insight notes with scores and wikilinks
- `Daydreams/digests/YYYYMMDD-digest.md` -- daily digest with stats and ranked insights
- Daily note `## Daydream` section -- summary with top connections

**Cost:** ~$0.40-0.50 per run (~50 pairs) via Claude Code usage.

**Inspired by:** [Gwern's "LLM Daydreaming"](https://gwern.net/ai-daydreaming) -- the idea that LLMs can productively "daydream" by finding unexpected connections between disparate pieces of knowledge, similar to how the brain's default mode network generates creative insights during idle periods.

**Use when:** You want to discover surprising connections across your knowledge base -- run daily or weekly to surface insights you wouldn't find through deliberate search.

---

### [Thinking Patterns](./thinking-patterns/) ⭐ NEW
Longitudinal cognitive pattern analysis across months of recorded conversations. Extracts 12 evidence-based dimensions from Fathom transcripts, synthesizes cross-session patterns, and detects blind spots via multi-agent parallel processing.

**Scientific Foundation:**
- **Tier 1 (Validated):** Burns' cognitive distortions, LIWC dimensions, epistemic markers, Russell's Circumplex Model
- **Tier 2 (Established):** Lakoff conceptual metaphors, McAdams narrative identity, Kegan immunity to change, ACT flexibility
- **Tier 3 (Applied):** Kegan developmental stages, Schon reflective practice, agency language ratio

**12 Extraction Dimensions:**
- Cognitive distortions, problem framing, conceptual metaphors, hedging/certainty
- Code-switching (bilingual), decision moments, emotional indicators, avoidance/deflection
- Agency language, competing commitments, role/register markers, energy signals

**10 Output Sections + Blind Spot Summary:**
1. Recurring Narratives -- 2. Problem Framing -- 3. Metaphors -- 4. Decision Heuristics -- 5. Topics Avoided -- 6. Contradictions & Competing Commitments -- 7. Energy Patterns -- 8. Role Shifts -- 9. Execution Gap -- 10. Cognitive Distortions & Biases -- plus "The 5 Things You Don't See"

**Architecture:**
```
Stage 0: Corpus Discovery (orchestrator)
  |-- Find transcripts, classify by type, extract speaker lines
Stage 1: Per-Transcript Extraction (~13 parallel sonnet agents)
  |-- 12 dimensions extracted per transcript
Stage 2: Aggregation (orchestrator)
  |-- De-duplicate, cluster, package into synthesis bundles
Stage 3: Cross-Session Synthesis (4 parallel + 1 sequential sonnet agents)
  |-- Pattern detection, blind spot analysis, contradiction mapping
Stage 4: Output (orchestrator)
  +-- Compile analysis document, link to daily note
```

**Features:**
- Multi-agent parallel extraction (up to 13 sonnet agents) and synthesis (5 agents)
- Bilingual support: English structure, Russian quotes preserved with translations
- Weighted corpus: coaching (1.0), meetings (0.9), podcasts (0.8), impromptu (0.7), workshops (0.6), labs (0.4)
- Unknown speaker recovery for Fathom transcripts with failed diarization
- Immunity to Change maps (Kegan & Lahey) for competing commitments
- Evidence-grounded: every finding backed by 2+ dated session quotes
- Execution gap analysis against stated priorities (Profile Brief, My Focus)
- Configurable date ranges, session type weights, speaker identifiers

**Quick Start:**
```bash
# Copy to skills directory
cp -r thinking-patterns ~/.claude/skills/

# Dry run -- see corpus stats and batch plan
/thinking-patterns --dry-run

# Full analysis (default: last 3 months)
/thinking-patterns

# Custom date range
/thinking-patterns --period 2026-01 2026-02
```

**Output:**
- `ai-research/YYYYMMDD-thinking-patterns-analysis.md` -- full analysis with evidence
- Daily note link under `## Research`

**Cost:** ~$3.50 per full run, ~6-8 minutes runtime.

**Use when:** Quarterly self-reflection, coaching preparation, or whenever you want evidence-based insight into your own cognitive patterns across recorded conversations.

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

---

### [Wispr Analytics](./wispr-analytics/)
Extract and analyze [Wispr Flow](https://wispr.com/) voice dictation history from the local SQLite database. Combines quantitative metrics with LLM-powered qualitative analysis for self-reflection, work pattern recognition, and mental health awareness.

**Features:**
- Reads directly from Wispr Flow's local SQLite database (~8,500+ dictations)
- Period selection: `today`, `yesterday`, `week`, `month`, specific dates, date ranges
- Five analysis modes: `all`, `technical` (coding/work), `soft` (communication patterns), `trends` (volume/frequency), `mental` (sentiment/energy/rumination)
- App-aware categorization: coding, AI tools, communication, writing
- Bilingual analysis (Russian/English) with language-switching pattern detection
- Hourly activity heatmaps and daily trend tables
- LLM-powered qualitative analysis with mode-specific prompt templates
- Saves output to Obsidian vault (`meta/wispr-analytics/`)

**Quick Start:**
```bash
# Copy to skills directory
cp -r wispr-analytics ~/.claude/skills/

# Today's full analysis
/wispr-analytics today

# Last 7 days, communication patterns
/wispr-analytics week soft

# Monthly mental health reflection
/wispr-analytics month mental

# Specific date range, productivity focus
/wispr-analytics 2026-02-01:2026-02-14 technical
```

**Use when:** Self-reflection on work patterns, reviewing dictation habits, tracking energy/sentiment over time, understanding how you communicate across contexts, or generating periodic self-awareness reports.

### [Context Builder](./context-builder/) ⭐ NEW
Generate interactive AI transformation context-builder prompts for consulting clients. Creates structured discovery session prompts that guide a company through context gathering about their business, pain points, tech stack, and AI opportunities -- producing a resumable, multi-section questionnaire with Express and Deep Dive modes.

**Features:**
- 5-phase workflow: Intake (AskUserQuestion) -> Research (web + vault) -> Section Selection -> Generation -> Delivery
- 15 pre-built sections in the section library (Revenue Map, Existential Question, Process Inventory, Pain Points, Tech Stack, AI Opportunities, New Business Models, People & Org, Client Value Chain, Data Assets, and more)
- Focus-based section presets: AI Automation (7 sections), Existential Strategy (7 sections), Full Assessment (10+)
- Two modes per generated prompt: Express (~15-20 min, 4 mega-sections) and Deep Dive (~60-90 min, 10 sections)
- Session resumability: generated prompts check for existing output files and pick up where they left off
- Auto-research: searches the web and Obsidian vault for company info, transcripts, and existing notes before generating
- Baked-in consulting frameworks: BCG 10/20/70, Andrew Ng's Playbook, Deloitte AI Maturity, Value Stream Mapping, custom heuristics ("The But Heuristic", "Metro Newspaper Test", "Curiosity > Fear")
- Output: per-section markdown files + compiled CLAUDE.md context file for future sessions
- Optional Telegram delivery of generated prompts
- Multilingual support (e.g., Russian session language with English output files)

**Quick Start:**
```bash
# Copy to skills directory
cp -r context-builder ~/.claude/skills/

# Run the skill
/context-builder
```

**Use when:** Preparing for a consulting engagement, onboarding a new client, running a structured discovery session, or doing a self-assessment of your own business's AI transformation readiness.

### [Sketch MCP Server](https://github.com/glebis/sketch-mcp-server) ⭐ NEW
Collaborative SVG canvas MCP server with a Fabric.js browser editor. Claude writes and reads SVG via MCP tools while the user edits interactively in the browser. Real-time sync via WebSocket.

**Features:**
- Open named canvases in standalone browser windows (Chrome --app mode)
- Set, replace, or incrementally add SVG elements with live updates
- Fixed-width Textbox support with word wrapping (Fabric.js Textbox)
- Lock/unlock objects -- freeze grid structure while keeping text areas editable
- JSON template save/load -- preserves Textbox widths, lock states, and all object properties
- Undo/redo with lock state persistence
- Built-in toolbar: select, draw, shapes (rect, ellipse, triangle, line, arrow), text tool (click for IText, drag for Textbox)
- Clipboard paste support (images, SVG)
- Includes a before/after grid template

**MCP Tools:**
- `sketch_open_canvas` -- create/open canvas, launches browser
- `sketch_get_svg` / `sketch_set_svg` -- read/replace SVG
- `sketch_add_element` -- add SVG fragment without clearing
- `sketch_add_textbox` -- add fixed-width text area with word wrapping
- `sketch_lock_objects` / `sketch_unlock_objects` -- freeze/unfreeze objects
- `sketch_save_template` / `sketch_load_template` / `sketch_list_templates` -- JSON template persistence
- `sketch_clear_canvas` / `sketch_focus_canvas` / `sketch_close_canvas` -- canvas management

**Quick Start:**
```bash
# Clone and build
git clone https://github.com/glebis/sketch-mcp-server.git
cd sketch-mcp-server && npm install && npm run build

# Add to Claude Code MCP config
# mcpServers: { "sketch-mcp-server": { "command": "node", "args": ["path/to/dist/index.js", "--stdio"] } }
```

**Use when:** Visual prototyping, creating diagrams, building reusable canvas templates, before/after comparisons, or any task where Claude and the user need a shared visual workspace.

### [Meeting Processor](./meeting-processor/)
Intelligent meeting transcript processor that auto-detects meeting type (leadgen, partnership, coaching, internal) and applies type-specific structured extraction with optional interactive clarification.

**Features:**
- Auto-detection of meeting type from transcript content
- Interactive mode with AskUserQuestion for ambiguous details
- Batch mode for high-confidence extraction without interaction
- Type-specific extractors: leadgen (deal stage, commitments, budget), partnership (strategic alignment, fit assessment), coaching (delegates to coaching-session-summarizer)
- Appends structured `## Meeting Analysis` section to transcript files
- Updates frontmatter with `meeting_type`, `processed_date`, `processing_mode`

**Quick Start:**
```bash
# Copy to skills directory
cp -r meeting-processor ~/.claude/skills/

# Install dependencies
pip install openai pyyaml

# Process a transcript interactively
python3 ~/.claude/skills/meeting-processor/scripts/process.py <transcript-file> --mode interactive

# Batch mode (no interaction)
python3 ~/.claude/skills/meeting-processor/scripts/process.py <transcript-file> --mode batch

# Force meeting type
python3 ~/.claude/skills/meeting-processor/scripts/process.py <transcript-file> --type leadgen
```

**Use when:** Processing meeting transcripts after Fathom/Granola sync, or when asked to analyze/summarize a meeting. Requires `CEREBRAS_API_KEY` environment variable.

---

### [Session Search](./session-search/)
Semantic search across Claude Code session transcripts. Combines keyword pre-filtering with LLM-powered relevance evaluation to find previous sessions about specific topics, debugging conversations, research tasks, or past work.

**Features:**
- Keyword pre-filtering for fast candidate selection across thousands of sessions
- Meaningful excerpt extraction prioritizing keyword-matching content over boilerplate
- Smart project name parsing from session paths
- Filters out system reminders and skill descriptions from results
- Configurable lookback period (default 90 days) and result count
- Outputs structured data for Claude's semantic relevance scoring

**Quick Start:**
```bash
# Copy to skills directory
cp -r session-search ~/.claude/skills/

# Search for sessions about a topic
/session-search "debugging auth flow"

# With custom parameters (20 results, 180 days lookback)
/session-search "obsidian vault" 20 180
```

**Use when:** Finding previous Claude Code sessions about specific topics, locating past debugging conversations, or searching for research/planning sessions.

### [Balanced Dialog](./balanced/) ⭐ NEW
Evidence-based dialogue mode that replaces sycophantic AI responses with structured, critical analysis. Five modes for different contexts — from quick gut-checks to deep Socratic dialogue.

**Modes:**
- **FULL** — 4-move structured analysis: Surface Merits → Rigorous Challenge → Expansion → Refinement
- **INTERACTIVE** — Socratic Q&A, one move at a time with user input at each step
- **TLDR** — 3-5 line insight box: one fact, one challenge, one action
- **STEELMAN** — strongest argument + strongest counter-argument. For debate prep
- **DECISION** — tradeoff table + the call. For when analysis is done

**Output Modifiers:**
- `--table` — ASCII pro/contra table
- `--refs` — full academic citations with DOI validation

**Meta-Rules:**
- No flattery, no filler phrases, no opinion statements
- Quantified confidence levels (~70% confident...)
- Scientific citation format with DOI web-search validation
- Explicit uncertainty flagging
- Subjective vs objective separation

**Quick Start:**
```bash
# Install via npx
npx skills add glebis/claude-skills -s balanced

# Or copy manually
cp -r balanced ~/.claude/skills/

# Quick analysis
/balanced "AI agents will replace most knowledge work within 5 years"

# Steelman mode for debate prep
/balanced steelman "remote work is more productive than office work"

# TLDR with table
/balanced tldr --table "should I migrate from REST to GraphQL?"

# Interactive Socratic dialogue
/balanced i "consciousness is an illusion"

# Onboarding — pick your default mode
/balanced onboard
```

**Use when:** You need honest, structured feedback instead of agreement — testing assumptions, evaluating claims, preparing arguments, making decisions.

---

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
# or
cp -r claude-skills/tdd ~/.claude/skills/
# or
cp -r claude-skills/daydream ~/.claude/skills/
# or
cp -r claude-skills/thinking-patterns ~/.claude/skills/
# or
cp -r claude-skills/meeting-processor ~/.claude/skills/
# or
cp -r claude-skills/balanced ~/.claude/skills/

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
