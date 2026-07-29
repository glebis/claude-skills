# Claude Skills

~100 skills for [Claude Code](https://claude.com/claude-code) — meeting pipelines, research, image generation, TDD, publishing, personal analytics, and Claude Code ops. Each skill is a self-contained folder with a `SKILL.md`; Claude triggers them from natural language.

By [Gleb Kalinin](https://glebkalinin.com/) — Berlin-based technologist, AI educator, solopreneur, artist. Join the [Claude Code Lab](https://claude.salient.community/).

## Install

```bash
# Plugin marketplace (recommended)
claude plugin marketplace add glebis/claude-skills
claude plugin install tdd@glebis-skills

# skills CLI
npx skills add glebis/claude-skills --skill tdd

# Manual
git clone https://github.com/glebis/claude-skills.git
cp -r claude-skills/<skill-name> ~/.claude/skills/
```

Per-skill setup (API keys, Python/Node deps) is documented in each skill's `SKILL.md`. See [BUNDLES.md](./BUNDLES.md) for curated groupings.

## Contents

[Recent additions](#recent-additions) · [Meetings & transcripts](#meetings--transcripts) · [Research & knowledge](#research--knowledge) · [Writing, design & publishing](#writing-design--publishing) · [Images, audio & media](#images-audio--media) · [Communication](#communication) · [Development & release](#development--release) · [Thinking & decisions](#thinking--decisions) · [Personal analytics](#personal-analytics) · [Claude Code ops](#claude-code-ops) · [Lab, consulting & business](#lab-consulting--business)

## Recent additions

| Added | Skill | What it does |
| --- | --- | --- |
| 2026-07 | [font-features](./font-features/) | Inspect and apply OpenType features — ligatures, stylistic sets, alternates |
| 2026-07 | [typography](./typography/) | Deterministic smart quotes, dashes, non-breaking spaces (RU/EN/DE/FR) |
| 2026-07 | [pre-session-portrait](./pre-session-portrait/) | 7-lens JTBD client portrait before a paid consulting hour |
| 2026-07 | [automation-advisor](./automation-advisor/) | Quantified ROI + break-even analysis for "should I automate this?" |
| 2026-07 | [cull-release](./cull-release/) | Six-skill release orchestration suite (check, prepare, publish, verify, recover) |
| 2026-07 | [elimination-research](./elimination-research/) | Numeric, source-auditable shortlist comparisons for products and vendors |
| 2026-07 | [nielsen-heuristics](./nielsen-heuristics/) | Formal heuristic evaluation against Nielsen's 10 usability heuristics |
| 2026-07 | [i18n-studio](./i18n-studio/) | Edit, translate, and review Astro-style i18n string corpora |
| 2026-07 | [the-goal](./the-goal/) | Theory-of-Constraints diagnostic for deciding what to automate |
| 2026-06 | [design-tokens](./design-tokens/) | DTCG 2025.10 token sets — validate, resolve, export to CSS |
| 2026-06 | [app-release](./app-release/) | iOS/watchOS release pipeline to TestFlight and the App Store |
| 2026-06 | [local-models](./local-models/) | Offline llama.cpp inference reusing models Ollama already downloaded |
| 2026-06 | [feature-factory](./feature-factory/) | Solo-dev feature pipeline: goal-first, TDD, deterministic verification |

## Meetings & transcripts

| Skill | What it does |
| --- | --- |
| [fathom](./fathom/) | Fetch Fathom meetings, transcripts, summaries, action items; download video |
| [granola](./granola/) | Granola cache/API → transcripts and Obsidian export, with 15-min auto-sync |
| [zoom](./zoom/) | Create/manage Zoom meetings, access cloud recordings and transcripts |
| [meeting-prep](./meeting-prep/) | Pull Cal.com bookings, research participants, audit past sessions, write prep notes |
| [meeting-processor](./meeting-processor/) | Auto-detect meeting type and extract type-specific structured summaries |
| [transcript-analyzer](./transcript-analyzer/) | Decisions, action items, opinions, terminology via Cerebras llama-3.3-70b |
| [coaching-session-summarizer](./coaching-session-summarizer/) | Summarize coaching/therapy transcripts after a Fathom/Granola sync |
| [session-anonymizer](./session-anonymizer/) | Three-layer PII anonymization (Natasha NER + privacy filter + local LLM) |
| [youtube-transcript](./youtube-transcript/) | Transcript + metadata → Obsidian markdown, no video download |
| [thinking-patterns](./thinking-patterns/) | Longitudinal cognitive analysis across months of transcripts (12 dimensions, multi-agent) |

## Research & knowledge

| Skill | What it does |
| --- | --- |
| [deep-research](./deep-research/) | OpenAI Deep Research API with prompt enhancement and sourced markdown reports |
| [firecrawl-research](./firecrawl-research/) | Scrape and enrich notes with web sources; scientific writing with citations |
| [elimination-research](./elimination-research/) | Deterministic scoring, ownership costs, and audit trail for shortlists |
| [doctorg](./doctorg/) | Evidence-based health research, GRADE-style ratings, Apple Health context |
| [qmd-search](./qmd-search/) | Local semantic + keyword search over an Obsidian vault; cross-lingual (EN↔RU) |
| [learning-vault](./learning-vault/) | Generate an Obsidian study vault for any certification or course |
| [temple-generator](./temple-generator/) | Turn a vault into a 3D interactive knowledge map with generative audio |
| [daydream](./daydream/) | Multi-agent mining of non-obvious connections between vault notes |
| [insight-extractor](./insight-extractor/) | Parse `/insights` output into trackable markdown action items |
| [weekly-digest](./weekly-digest/) | Research, score, and publish a weekly industry digest on any topic |
| [wow-digest](./wow-digest/) | Daily digest of genuinely surprising items, scored for epistemic friction |
| [rag-eval](./rag-eval/) | Tune RAG pipelines with structured evals instead of eyeballing |
| [rigorous-experiments](./rigorous-experiments/) | Pre-registered n-of-1 experiments, permutation tests, FDR discipline |
| [whitepaper-audit](./whitepaper-audit/) | Audit long-form technical documents against a research-grounded checklist |
| [name-audition](./name-audition/) | Domain availability, collision research, and scoring for candidate names |
| [google-image-search](./google-image-search/) | Google CSE image search with LLM-powered selection and Obsidian enrichment |

## Writing, design & publishing

| Skill | What it does |
| --- | --- |
| [present](./present/) | Narrated HTML presentations — dual article/slides mode, ElevenLabs voiceover |
| [presentation-generator](./presentation-generator/) | Neobrutalist HTML decks with Anime.js; export to PNG/PDF/video |
| [pdf-generation](./pdf-generation/) | Markdown → PDF via Pandoc; mobile (6×9in) and print (A4) layouts, EN/RU |
| [tufte-report](./tufte-report/) | Tufte-style data reports and dashboards as standalone HTML |
| [brand-agency](./brand-agency/) | Agency brand colors, typography, and 11 social templates via Playwright |
| [design-tokens](./design-tokens/) | DTCG token sets — global base + per-project layering, CSS export |
| [typography](./typography/) | Locale-correct quotes, dashes, and non-breaking spaces via pinned CLI |
| [font-features](./font-features/) | Inspect and apply ligatures, stylistic sets, and character variants |
| [nielsen-heuristics](./nielsen-heuristics/) | Evidence-backed heuristic usability evaluation |
| [de-ai](./de-ai/) | Humanize AI-sounding text across 5 languages, preserving meaning and facts |
| [i18n-studio](./i18n-studio/) | Edit, translate, and review i18n string corpora |
| [sketch](./sketch/) | Sketch/diagram generation support |
| [publish-skill](./publish-skill/) | Publish or update a skill on the claude-skills-site Astro website |
| [telegram-post](./telegram-post/) | Draft → preview → publish formatted Telegram channel posts |
| [agency-socials](./agency-socials/) | Event covers, YouTube thumbnails, and social assets for AGENCY Community |

## Images, audio & media

| Skill | What it does |
| --- | --- |
| [gpt-image-2](./gpt-image-2/) | OpenAI GPT Image 2 — thinking mode, 14 style presets, draft mode, cost controls |
| [nano-banana](./nano-banana/) | Gemini image generation and editing with style and platform presets |
| [vision-bench](./vision-bench/) | Score and compare images using vision LLMs as judges (11 criteria presets) |
| [elevenlabs-tts](./elevenlabs-tts/) | Text → audio via ElevenLabs with voice presets and tunable parameters |

## Communication

| Skill | What it does |
| --- | --- |
| [telegram](./telegram/) | Fetch, search, send, schedule Telegram messages and media |
| [telegram-telethon](./telegram-telethon/) | Full Telethon wrapper + daemon that spawns Claude sessions on triggers |
| [tg-responder](./tg-responder/) | Review and send response drafts; track unanswered outbound messages |
| [gws](./gws/) | Google Workspace CLI reference — Gmail, Calendar, Drive, Sheets, Docs, Chat |
| [gmail](./gmail/) | Gmail search, fetch, attachments, labels via API |
| [browser-mate](./browser-mate/) | Automate a logged-in Chrome without disturbing the user's open tabs |

## Development & release

| Skill | What it does |
| --- | --- |
| [tdd](./tdd/) | Multi-agent TDD with enforced context isolation across RED→GREEN→REFACTOR |
| [feature-factory](./feature-factory/) | Solo-dev pipeline from feature intent to shipped, with evidence gates |
| [skills/release](./skills/release/) | Config-driven releases with a tiered compatibility policy (`COMPATIBILITY.md`) |
| [cull-release](./cull-release/) | Cull release suite: [check](./cull-release-check/), [prepare](./cull-release-prepare/), [publish](./cull-release-publish/), [verify](./cull-release-verify/), [recover](./cull-release-recover/) |
| [app-release](./app-release/) | iOS/watchOS → TestFlight and App Store |
| [init-tauri-app](./init-tauri-app/) | Scaffold Tauri v2 projects with house conventions |
| [init-xcode-app](./init-xcode-app/) | Scaffold SwiftUI apps via XcodeGen (macOS, iOS, iOS+watchOS) |
| [agent-cli](./agent-cli/) | Add agent-friendly `--json` NDJSON output to Python CLIs |
| [repo-prep](./repo-prep/) | Prepare a repo for publication — LICENSE, README, metadata, community docs |
| [llm-cli](./llm-cli/) | One CLI across 6 LLM providers and 40+ models |
| [local-models](./local-models/) | Cheap offline inference via llama.cpp on Ollama-downloaded models |
| [codex](./codex/) | Drive OpenAI Codex CLI for analysis, refactoring, automated edits |
| [peer-agent-collaboration](./peer-agent-collaboration/) | Have Claude Code, Codex, and other agents work together as peers |
| [linear](./linear/) | Create, list, update, and search Linear issues and projects |
| [github-gist](./github-gist/) | Publish files or notes as secret/public gists |
| [skills/job-babysitter](./skills/job-babysitter/) | Watch long-running background jobs (encodes, embeddings, batch pipelines) |
| [skills/cmux](./skills/cmux/) | Control the cmux terminal app via its CLI socket API |

## Thinking & decisions

| Skill | What it does |
| --- | --- |
| [the-goal](./the-goal/) | Theory-of-Constraints diagnostic before building any automation |
| [automation-advisor](./automation-advisor/) | 8 questions → break-even math, with voice-enabled web UI |
| [decision-toolkit](./decision-toolkit/) | 7 frameworks, 20+ bias counter-questions, interactive HTML wizards |
| [jtbd](./jtbd/) | Jobs-to-be-Done interviews, switching forces, messaging and GTM briefs |
| [balanced](./balanced/) | Anti-sycophantic multi-perspective analysis and Socratic dialogue |
| [cognitive-toolkit](https://github.com/glebis/claude-cognitive-toolkit) | CBT/DBT interventions — thought records, DEAR MAN, crisis skills (separate repo) |
| [synthetic-session-generator](./synthetic-session-generator/) | Persona-consistent synthetic coaching/therapy transcripts for evals |

## Personal analytics

| Skill | What it does |
| --- | --- |
| [health-data](./health-data/) | Query Apple Health SQLite — vitals, activity, sleep, workouts (MD/JSON/FHIR) |
| [wispr-analytics](./wispr-analytics/) | Analyze Wispr Flow dictation history; manage the dictation dictionary |
| [browsing-history](./browsing-history/) | Query history across all synced Chrome devices with natural language |
| [chrome-history](./chrome-history/) | Query local Chrome history by date, type, keyword, site |
| [session-finder](./session-finder/) | Semantic index of Claude Code sessions (Gemini embeddings); relaunch best match |
| [session-search](./session-search/) | Search session transcripts with synonym-aware semantic matching |

## Claude Code ops

| Skill | What it does |
| --- | --- |
| [ecosystem](./ecosystem/) | Audit skill health, project pulse, CLAUDE.md drift, service status |
| [retrospective](./retrospective/) | Extract learnings from one session or all of today's, update skills and memory |
| [skill-studio](https://github.com/glebis/skill-studio) | Interview-driven skill/automation design; analyze sessions into new skills |
| [recording](./recording/) | Demo mode — redact PII from outputs in real time while screen-sharing |
| [skills/disk-cleanup](./skills/disk-cleanup/) | Survey and clean macOS caches, package data, crash dumps |
| [wispr-fix](./wispr-fix/) | Queue and batch-apply Wispr dictation corrections |
| [context-builder](./context-builder/) | Generate AI-transformation discovery prompts for consulting clients |
| [meta](./meta/) | Run Claude Code commands against the telegram_agent project |

## Lab, consulting & business

| Skill | What it does |
| --- | --- |
| [agency-docs-updater](./agency-docs-updater/) | Lab meeting pipeline: transcript → video → YouTube → summary → MDX → deploy |
| [agency-meetup-publish](./agency-meetup-publish/) | Zoom recording → intro/outro, thumbnail, timecodes, YouTube, playlist |
| [lab-retro](./lab-retro/) | Four-part retrospective and self-assessment for Lab participants |
| [skills/library-sync](./skills/library-sync/) | Sync bilingual (EN/RU) library content for agency-docs |
| [site-diagnosis](./site-diagnosis/) | Pre-consultation questionnaire for clients building sites with AI tools |
| [sorted](./sorted/) | getSorted.de automation — invoicing, expenses, German VAT/ZM filings |
| [cull](./cull/) | View, rate, organize, search, and export images with the Cull app |
| [timebuzzer-led](./timebuzzer-led/) | Control timeBuzzer hardware LED via MIDI — colors, effects, status signals |

## Skill structure

```
skill-name/
├── SKILL.md          # Metadata, triggers, usage
├── CHANGELOG.md      # Version history
├── scripts/          # Executable orchestration
├── assets/           # Resources
└── references/       # Detailed docs
```

## Contributing

Fork, add a skill following the structure above, document it, open a PR. For guidance on authoring skills, see the [Claude Code skills docs](https://docs.claude.com/docs/claude-code/skills).

## License

[MIT](./LICENSE) — see individual skill directories for exceptions.

---

Skills require Claude Code to function; they are not standalone tools. [Support this work and learn Claude Code →](https://claude.salient.community/)
