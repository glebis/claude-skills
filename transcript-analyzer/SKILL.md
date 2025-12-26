---
name: transcript-analyzer
description: This skill analyzes meeting transcripts to extract decisions, action items, opinions, questions, and terminology using Cerebras AI (llama-3.3-70b). Use this skill when the user asks to analyze a transcript, extract action items from meetings, find decisions in conversations, build glossaries from discussions, or summarize key points from recorded meetings.
---

# Transcript Analyzer

## Overview

Analyze meeting transcripts using AI to automatically extract and categorize:
- **Decisions** - Explicit agreements or choices made
- **Action Items** - Tasks assigned to people
- **Opinions** - Viewpoints expressed but not agreed upon
- **Questions** - Unresolved questions raised
- **Terms** - Domain-specific terminology for glossary

## Prerequisites

Before first use, install dependencies:

```bash
cd ~/.claude/skills/transcript-analyzer/scripts && npm install
```

## Usage

To analyze a transcript:

```bash
cd ~/.claude/skills/transcript-analyzer/scripts && npm run cli -- <transcript-file> -o <output.md> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `<file>` | Transcript file to analyze (first positional arg) |
| `-o, --output <path>` | Write markdown to file instead of stdout |
| `--include-transcript` | Include full transcript in output [default: off] |
| `--no-extractions` | Exclude extractions section |
| `--no-glossary` | Exclude glossary section |
| `--glossary <path>` | Custom glossary JSON path |
| `--skip-glossary` | Don't preload glossary terms |
| `--max-terms <num>` | Limit glossary suggestions |
| `--chunk-size <num>` | Override chunk size (default: 3000) |

## Examples

### Basic Analysis

```bash
cd ~/.claude/skills/transcript-analyzer/scripts && npm run cli -- /path/to/meeting.md -o /path/to/analysis.md
```

### Include Original Transcript

```bash
cd ~/.claude/skills/transcript-analyzer/scripts && npm run cli -- /path/to/meeting.md -o /path/to/analysis.md --include-transcript
```

### Extractions Only (No Glossary)

```bash
cd ~/.claude/skills/transcript-analyzer/scripts && npm run cli -- /path/to/meeting.md -o /path/to/analysis.md --no-glossary
```

### Analyze Specific Section

To analyze only part of a transcript, extract the section first:

```bash
sed -n '50,100p' /path/to/meeting.md > /tmp/section.md
cd ~/.claude/skills/transcript-analyzer/scripts && npm run cli -- /tmp/section.md -o /path/to/section-analysis.md
```

## Output Format

The tool generates markdown with:

1. **YAML Frontmatter** - Processing metadata:
   - chunks processed
   - extractions count by type
   - new terms discovered
   - model used (llama-3.3-70b via Cerebras)
   - token usage (input/output/total)

2. **Extractions** - Categorized findings with confidence scores:
   - Each extraction includes speaker (if identified), source snippet, and related terms

3. **Glossary** - Approved terms from existing glossary + suggested new terms with definitions

## Configuration

The skill uses Cerebras API with the key stored in `scripts/.env`:

```
CEREBRAS_API_KEY=<your-key>
```

## Scripts

- `scripts/cli.ts` - Main CLI entry point
- `scripts/src/lib/extract-service.ts` - AI processing logic using Cerebras
- `scripts/src/lib/markdown.ts` - Markdown output generation
- `scripts/src/lib/term-utils.ts` - Term deduplication utilities
- `scripts/src/lib/mockExtractor.ts` - Mock mode for testing
- `scripts/src/types/index.ts` - TypeScript type definitions
- `scripts/data/glossary.json` - Default glossary storage
