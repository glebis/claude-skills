---
name: notebooklm
description: "This skill should be used when the user wants to interact with Google NotebookLM from the terminal. Trigger when the user mentions: notebooklm, notebook lm, notebook, upload to notebook, ask notebook, create notebook, research with notebooklm, add source, add to notebook, notebook sources, generate podcast, generate audio overview, notebook summary, notebook quiz, notebook flashcards, notebook video, notebook slides, share notebook, notebook notes, deep research notebook, download podcast, notebook artifacts, notebook sharing, notebook language"
---

# NotebookLM CLI Skill

You are an expert at using the NotebookLM CLI (v0.3.4+) to manage Google NotebookLM notebooks, sources, artifacts, notes, and sharing -- all from the terminal. Translate the user's natural language request into the correct CLI commands.

## General Rules

- Always append `2>&1` to capture both stdout and stderr.
- Use `--json` flag when you need to parse output programmatically (e.g., to extract IDs).
- Partial IDs are supported everywhere (notebooks, sources, artifacts, notes) -- no need for full UUIDs.
- If the user is not authenticated, run `notebooklm login 2>&1` first. Use `notebooklm auth check 2>&1` to diagnose issues.
- After adding sources, they need processing time. Use `notebooklm source wait <id>` before querying.
- For batch uploads, add a 2-second delay between sources to avoid rate limiting.
- Max ~50 sources per notebook, ~500K words total.
- Add `-v` or `-vv` flag for verbose/debug output when troubleshooting.
- Use `--storage PATH` to specify alternate credentials file if needed.

## Command Reference

### Session Management

| User says | Command |
|-----------|---------|
| "create a notebook called X" | `notebooklm create "X" 2>&1` |
| "list my notebooks" | `notebooklm list 2>&1` |
| "use notebook X" / "switch to X" | `notebooklm use <id> 2>&1` |
| "what notebook am I in" / "current notebook" | `notebooklm status 2>&1` |
| "clear notebook context" | `notebooklm clear 2>&1` |
| "delete this notebook" | `notebooklm delete -y 2>&1` |
| "delete notebook X" | `notebooklm delete -n <id> -y 2>&1` |
| "rename notebook to Y" | `notebooklm rename "Y" 2>&1` |
| "notebook summary" / "what's in this notebook" | `notebooklm summary 2>&1` |
| "summary with topics" | `notebooklm summary --topics 2>&1` |
| "show notebook metadata" | `notebooklm metadata 2>&1` |

### Sources

| User says | Command |
|-----------|---------|
| "add this URL as a source" | `notebooklm source add "URL" 2>&1` |
| "add this file" | `notebooklm source add ./path/to/file 2>&1` |
| "add this YouTube video" | `notebooklm source add "https://youtube.com/..." 2>&1` |
| "add this text as a source" | `notebooklm source add "text content" --title "Title" 2>&1` |
| "add Google Drive doc" | `notebooklm source add-drive <file_id> "Title" 2>&1` |
| "research X" / "find sources about X" | `notebooklm source add-research "X" 2>&1` |
| "deep research X" | `notebooklm source add-research "X" --mode deep 2>&1` |
| "research X from Drive" | `notebooklm source add-research "X" --from drive 2>&1` |
| "research X and add everything" | `notebooklm source add-research "X" --import-all 2>&1` |
| "list sources" / "what sources are there" | `notebooklm source list 2>&1` |
| "show source details" | `notebooklm source get <id> 2>&1` |
| "source summary" / "source guide" | `notebooklm source guide <id> 2>&1` |
| "get source full text" | `notebooklm source fulltext <id> 2>&1` |
| "save source text to file" | `notebooklm source fulltext <id> -o output.txt 2>&1` |
| "rename source to Y" | `notebooklm source rename <id> "Y" 2>&1` |
| "delete source X" | `notebooklm source delete <id> -y 2>&1` |
| "delete source by name" | `notebooklm source delete-by-title "Title" -y 2>&1` |
| "is source stale" / "check if outdated" | `notebooklm source stale <id> 2>&1` |
| "refresh source" | `notebooklm source refresh <id> 2>&1` |
| "wait for source to process" | `notebooklm source wait <id> 2>&1` |

Source type is auto-detected: URLs become `url`, YouTube links become `youtube`, file paths become `text`/`file`, everything else becomes inline `text`. Override with `--type`.

### Chat / Ask

| User says | Command |
|-----------|---------|
| "ask X" / "question: X" | `notebooklm ask "X" 2>&1` |
| "ask about specific sources" | `notebooklm ask -s <src_id> -s <src_id> "X" 2>&1` |
| "ask and save as note" | `notebooklm ask "X" --save-as-note 2>&1` |
| "ask and save with title" | `notebooklm ask "X" --save-as-note --note-title "Title" 2>&1` |
| "show chat history" | `notebooklm history 2>&1` |
| "show full chat history" | `notebooklm history --show-all 2>&1` |
| "save chat history as note" | `notebooklm history --save 2>&1` |
| "clear chat history" | `notebooklm history --clear 2>&1` |

### Configure Chat Persona

| User says | Command |
|-----------|---------|
| "make it a tutor" / "set persona" | `notebooklm configure --persona "Act as a tutor" 2>&1` |
| "concise mode" | `notebooklm configure --mode concise 2>&1` |
| "detailed mode" | `notebooklm configure --mode detailed 2>&1` |
| "learning guide mode" | `notebooklm configure --mode learning-guide 2>&1` |
| "shorter responses" | `notebooklm configure --response-length shorter 2>&1` |
| "longer responses" | `notebooklm configure --response-length longer 2>&1` |

### Generate Artifacts

| User says | Command |
|-----------|---------|
| "generate a podcast" / "create audio" | `notebooklm generate audio "description" 2>&1` |
| "generate a debate podcast" | `notebooklm generate audio "description" --format debate 2>&1` |
| "generate a short podcast" | `notebooklm generate audio "description" --length short 2>&1` |
| "generate a video" | `notebooklm generate video "description" 2>&1` |
| "generate cinematic video" | `notebooklm generate cinematic-video "description" 2>&1` |
| "generate anime style video" | `notebooklm generate video "description" --style anime 2>&1` |
| "generate slides" / "create presentation" | `notebooklm generate slide-deck "description" 2>&1` |
| "generate a quiz" | `notebooklm generate quiz "description" 2>&1` |
| "generate hard quiz" | `notebooklm generate quiz "description" --difficulty hard 2>&1` |
| "generate flashcards" | `notebooklm generate flashcards "description" 2>&1` |
| "generate infographic" | `notebooklm generate infographic "description" 2>&1` |
| "generate mind map" | `notebooklm generate mind-map 2>&1` |
| "generate data table" | `notebooklm generate data-table "description" 2>&1` |
| "generate a report" / "briefing doc" | `notebooklm generate report 2>&1` |
| "generate study guide" | `notebooklm generate report --format study-guide 2>&1` |
| "generate blog post" | `notebooklm generate report --format blog-post 2>&1` |
| "generate custom report about X" | `notebooklm generate report --format custom "X" 2>&1` |
| "generate from specific sources" | Add `-s <src_id>` to any generate command |
| "wait for generation" | `notebooklm artifact wait <artifact_id> 2>&1` |

Generate options reference:
- **audio**: `--format deep-dive|brief|critique|debate`, `--length short|default|long`
- **video**: `--format explainer|brief|cinematic`, `--style auto|classic|whiteboard|kawaii|anime|watercolor|retro-print|heritage|paper-craft`
- **slide-deck**: `--format detailed|presenter`, `--length default|short`
- **quiz**: `--quantity fewer|standard|more`, `--difficulty easy|medium|hard`
- **flashcards**: `--quantity fewer|standard|more`, `--difficulty easy|medium|hard`
- **infographic**: `--orientation landscape|portrait|square`, `--detail concise|standard|detailed`, `--style auto|sketch-note|professional|bento-grid|editorial|instructional|bricks|clay|anime|kawaii|scientific`
- **report**: `--format briefing-doc|study-guide|blog-post|custom`, `--append "extra instructions"`

All generate commands support: `-s/--source` (limit sources), `--wait/--no-wait`, `--retry N`, `--json`, `--language`

### Download Artifacts

| User says | Command |
|-----------|---------|
| "download the podcast" | `notebooklm download audio 2>&1` |
| "download audio to X" | `notebooklm download audio "X.mp3" 2>&1` |
| "download all audio" | `notebooklm download audio --all ./audio/ 2>&1` |
| "download the video" | `notebooklm download video 2>&1` |
| "download cinematic video" | `notebooklm download cinematic-video 2>&1` |
| "download slides" | `notebooklm download slide-deck 2>&1` |
| "download slides as pptx" | `notebooklm download slide-deck output.pptx 2>&1` |
| "download infographic" | `notebooklm download infographic 2>&1` |
| "download report" | `notebooklm download report 2>&1` |
| "download mind map" | `notebooklm download mind-map 2>&1` |
| "download data table" | `notebooklm download data-table 2>&1` |
| "download quiz" | `notebooklm download quiz 2>&1` |
| "download flashcards" | `notebooklm download flashcards 2>&1` |

Download options: `--latest` (default), `--earliest`, `--all`, `--name "fuzzy match"`, `-a <artifact_id>`, `--dry-run`, `--force`, `--no-clobber`

### Artifact Management

| User says | Command |
|-----------|---------|
| "list artifacts" / "list generated content" | `notebooklm artifact list 2>&1` |
| "list audio artifacts" | `notebooklm artifact list --type audio 2>&1` |
| "show artifact details" | `notebooklm artifact get <id> 2>&1` |
| "rename artifact" | `notebooklm artifact rename <id> "New Title" 2>&1` |
| "delete artifact" | `notebooklm artifact delete <id> 2>&1` |
| "export to Google Docs" | `notebooklm artifact export <id> --title "Title" --type docs 2>&1` |
| "export to Google Sheets" | `notebooklm artifact export <id> --title "Title" --type sheets 2>&1` |
| "suggest report topics" | `notebooklm artifact suggestions 2>&1` |
| "check generation status" | `notebooklm artifact poll <id> 2>&1` |

### Notes (in-notebook notes)

| User says | Command |
|-----------|---------|
| "create a note" | `notebooklm note create "content" -t "Title" 2>&1` |
| "list notes" | `notebooklm note list 2>&1` |
| "show note" | `notebooklm note get <id> 2>&1` |
| "update note" | `notebooklm note save <id> "new content" 2>&1` |
| "rename note" | `notebooklm note rename <id> "New Title" 2>&1` |
| "delete note" | `notebooklm note delete <id> 2>&1` |

### Sharing

| User says | Command |
|-----------|---------|
| "who has access" / "sharing status" | `notebooklm share status 2>&1` |
| "make notebook public" | `notebooklm share public --enable 2>&1` |
| "make notebook private" | `notebooklm share public --disable 2>&1` |
| "share with user@example.com" | `notebooklm share add user@example.com 2>&1` |
| "share as editor" | `notebooklm share add user@example.com --permission editor 2>&1` |
| "share with message" | `notebooklm share add user@example.com -m "Check this out" 2>&1` |
| "change permission to editor" | `notebooklm share update user@example.com --permission editor 2>&1` |
| "remove access" | `notebooklm share remove user@example.com 2>&1` |
| "set viewer access level" | `notebooklm share view-level --level full|chat-only 2>&1` |

### Research Management

| User says | Command |
|-----------|---------|
| "start deep research (non-blocking)" | `notebooklm source add-research "query" --mode deep --no-wait 2>&1` |
| "check research status" | `notebooklm research status 2>&1` |
| "wait for research to finish" | `notebooklm research wait 2>&1` |
| "wait and import all results" | `notebooklm research wait --import-all 2>&1` |

### Language

| User says | Command |
|-----------|---------|
| "list supported languages" | `notebooklm language list 2>&1` |
| "what language is set" | `notebooklm language get 2>&1` |
| "set language to Russian" | `notebooklm language set ru 2>&1` |

Note: Language is a GLOBAL setting affecting all notebooks.

## Batch Operations

### Upload all .md files from a folder

```bash
for f in /path/to/folder/*.md; do
  echo "Adding: $f"
  notebooklm source add "$f" 2>&1
  sleep 2
done
```

### Upload all files matching a pattern

```bash
for f in /path/to/folder/**/*.{md,txt,pdf}; do
  [ -f "$f" ] && echo "Adding: $f" && notebooklm source add "$f" 2>&1 && sleep 2
done
```

### Upload multiple URLs

```bash
urls=(
  "https://example.com/page1"
  "https://example.com/page2"
  "https://example.com/page3"
)
for url in "${urls[@]}"; do
  echo "Adding: $url"
  notebooklm source add "$url" 2>&1
  sleep 2
done
```

### Add research from multiple queries

```bash
queries=("machine learning basics" "neural network architectures" "transformer models")
for q in "${queries[@]}"; do
  echo "Researching: $q"
  notebooklm source add-research "$q" --import-all 2>&1
  sleep 3
done
```

### Wait for all sources to finish processing

```bash
# Get source IDs as JSON, then wait for each
notebooklm source list --json 2>&1 | python3 -c "
import json, sys, subprocess
data = json.load(sys.stdin)
for src in data:
    sid = src['id']
    print(f'Waiting for {sid}...')
    subprocess.run(['notebooklm', 'source', 'wait', sid])
"
```

## Common Workflows

### Create notebook, add sources, and ask a question

```bash
# 1. Create
notebooklm create "My Research" --json 2>&1
# 2. Use it (grab ID from create output)
notebooklm use <notebook_id> 2>&1
# 3. Add sources
notebooklm source add "https://example.com/article" 2>&1
# 4. Wait for processing
# (get source ID from add output)
notebooklm source wait <source_id> 2>&1
# 5. Ask
notebooklm ask "What are the key findings?" 2>&1
```

### Upload a folder of notes and get a summary

```bash
notebooklm create "Vault Export" --json 2>&1
notebooklm use <id> 2>&1
for f in /path/to/notes/*.md; do
  notebooklm source add "$f" 2>&1
  sleep 2
done
# Wait for all to process, then summarize
sleep 30
notebooklm summary --topics 2>&1
```

### Deep research workflow

```bash
notebooklm create "Deep Research: Topic" --json 2>&1
notebooklm use <id> 2>&1
notebooklm source add-research "topic query" --mode deep --no-wait 2>&1
notebooklm research wait --import-all 2>&1
notebooklm ask "Summarize the key findings" 2>&1
```

### Generate podcast from sources

```bash
notebooklm generate audio "engaging deep dive discussion" --format deep-dive --wait 2>&1
notebooklm download audio ./podcast.mp3 2>&1
```

### Generate and download a full content suite

```bash
notebooklm generate report --format briefing-doc --wait 2>&1
notebooklm generate audio "overview discussion" --wait 2>&1
notebooklm generate slide-deck "executive summary" --wait 2>&1
notebooklm download report ./report.md 2>&1
notebooklm download audio ./podcast.mp3 2>&1
notebooklm download slide-deck ./slides.pdf 2>&1
```

## Error Handling

- **"Not authenticated"**: Run `notebooklm login 2>&1`
- **"No current notebook"**: Run `notebooklm use <id>` or `notebooklm list` to find one
- **"Source not ready"**: Run `notebooklm source wait <id>` -- sources need processing after being added
- **"Rate limited"**: Use `--retry 3` on generate commands, or add `sleep 5` between batch operations
- **"Notebook not found"**: IDs are partial-match; run `notebooklm list --json` to get exact IDs
- **Generation timeout**: Use `notebooklm artifact wait <id> --timeout 600` for longer artifacts (videos can take 30+ min)
- **Research still running**: Use `notebooklm research status` to check, `notebooklm research wait` to block

## Tips

- Use `--json` output and pipe through `python3 -c` or `jq` for scripting.
- Artifact generation defaults to `--no-wait`; add `--wait` to block until done.
- `revise-slide` lets you update individual slides: `notebooklm generate revise-slide "instructions" --artifact <id> --slide <N>` (slide index is zero-based; `--artifact` and `--slide` are required named flags)
- The `ask --save-as-note` flag saves the answer directly as a notebook note.
- `history --save` persists the full conversation as a note.
- `metadata --json` exports notebook info + source list for archival.

## Python Library Reference

The CLI wraps [notebooklm-py](https://github.com/teng-lin/notebooklm-py) (v0.3.4+). For programmatic use in scripts or pipelines:

### Setup
```python
from notebooklm import NotebookLMClient

async with NotebookLMClient.from_storage() as client:
    # Uses same auth as CLI (~/.notebooklm/storage_state.json)
    notebooks = await client.notebooks.list()
```

### Key API Methods

| Category | Method | CLI Equivalent |
|----------|--------|---------------|
| **Notebooks** | `client.notebooks.list()` | `notebooklm list` |
| | `client.notebooks.create(title)` | `notebooklm create "title"` |
| | `client.notebooks.delete(id)` | `notebooklm delete id` |
| **Sources** | `client.sources.list(notebook_id)` | `notebooklm source list` |
| | `client.sources.add_url(notebook_id, url)` | `notebooklm source add URL` |
| | `client.sources.add_text(notebook_id, text, title)` | `notebooklm source add "text" --title X` |
| | `client.sources.delete(notebook_id, source_id)` | `notebooklm source delete id` |
| **Chat** | `client.chat.ask(notebook_id, question)` | `notebooklm ask "question"` |
| **Artifacts** | `client.artifacts.list(notebook_id)` | `notebooklm artifact list` |
| | `client.artifacts.generate_audio(notebook_id, desc)` | `notebooklm generate audio "desc"` |
| | `client.artifacts.download(notebook_id, artifact_id)` | `notebooklm download audio` |
| **Notes** | `client.notes.list(notebook_id)` | `notebooklm note list` |
| | `client.notes.create(notebook_id, title, content)` | `notebooklm note create` |
| **Sharing** | `client.sharing.status(notebook_id)` | `notebooklm share status` |
| | `client.sharing.add_user(notebook_id, email, role)` | `notebooklm share add` |

### When to Use Python vs CLI
- **CLI**: Interactive use, simple automations, batch uploads, one-off queries
- **Python**: Complex pipelines, conditional logic, error handling with retries, integration with other Python tools, async concurrent operations

### Dependencies
- `httpx` (async HTTP), `click` (CLI), `rich` (terminal formatting)
- Auth via Playwright browser automation (shares state with CLI)
- Install: `pip install notebooklm-py`
- Repo: https://github.com/teng-lin/notebooklm-py
