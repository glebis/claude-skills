---
name: firecrawl-research
description: This skill should be used when the user requests to research topics using FireCrawl, enrich notes with web sources, search and scrape information, or write scientific/academic papers. It extracts research topics from markdown files, creates research documents with scraped sources, generates BibTeX bibliographies from research results, and provides Pandoc/MyST templates for academic writing with citation management.
---

# FireCrawl Research

## Overview

Enrich research documents by automatically searching and scraping web sources using the FireCrawl API. Extract research topics from markdown files and generate comprehensive research documents with source material.

## When to Use This Skill

Use this skill when the user:
- Says "Research this topic using FireCrawl"
- Requests to enrich notes or documents with web sources
- Wants to gather information about topics listed in a markdown file
- Needs to search and scrape multiple topics systematically

## How It Works

### 1. Topic Extraction

The script automatically extracts research topics from markdown files using two methods:

**Method 1: Headers**
```markdown
## Spatial Reasoning in AI
### Computer Vision Applications
```
Both `Spatial Reasoning in AI` and `Computer Vision Applications` become research topics.

**Method 2: Research Tags**
```markdown
- [research] Large Language Models for robotics
- [search] Theory of Mind in autonomous driving
```
Both tagged items become research topics.

### 2. Search and Scrape

For each topic:
1. Searches FireCrawl with the topic as query
2. Retrieves up to N results (default: 5)
3. Automatically scrapes full content from each result
4. Extracts markdown-formatted content (main content only)

### 3. Output Generation

Creates new markdown files in the specified output directory:
- One file per topic
- Filename: `{topic}_{timestamp}.md`
- Contains: title, date, sources count, full scraped content
- Each source includes: title, URL, markdown content

## Usage

### Basic Usage

```bash
python scripts/firecrawl_research.py research.md
```

Outputs to current directory.

### Specify Output Directory

```bash
python scripts/firecrawl_research.py research.md ./output
```

Creates files in `./output/` folder.

### Limit Results Per Topic

```bash
python scripts/firecrawl_research.py research.md ./output 3
```

Retrieves maximum 3 results per topic.

## Configuration

### API Key Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add FireCrawl API key:
   ```
   FIRECRAWL_API_KEY=fc-your-actual-api-key
   ```

The script automatically loads the API key from the skill's `.env` file.

### Rate Limiting

The script includes automatic rate limiting for FireCrawl's free tier:
- **Free tier limit:** 5 requests/minute
- **Built-in delay:** 12 seconds between topics
- Prevents API errors and credit exhaustion

When processing multiple topics, expect:
- 5 topics: ~1 minute
- 10 topics: ~2 minutes
- 20 topics: ~4 minutes

## Workflow Example

**User request:** "Research these AI topics using FireCrawl"

**Input file (`ai-research.md`):**
```markdown
# AI Research Topics

## Spatial Reasoning in Vision-Language Models

- [research] Embodied AI for robotics
- [research] Computer Use Agents
```

**Command:**
```bash
python scripts/firecrawl_research.py ai-research.md ./research_output 5
```

**Output:**
```
research_output/
├── Spatial_Reasoning_in_Vision-Language_Models_20251122_140530.md
├── Embodied_AI_for_robotics_20251122_140542.md
└── Computer_Use_Agents_20251122_140554.md
```

Each file contains:
- Topic title
- Timestamp
- Source count
- Full scraped content from up to 5 sources
- Source URLs

## Common Patterns

### Pattern 1: Quick Research
Extract topics from existing notes, research them, save to current folder:
```bash
python scripts/firecrawl_research.py my-notes.md
```

### Pattern 2: Organized Research
Create dedicated output folder for research results:
```bash
python scripts/firecrawl_research.py topics.md ./research_results
```

### Pattern 3: Deep Dive
Increase results per topic for comprehensive coverage:
```bash
python scripts/firecrawl_research.py topics.md ./deep_research 10
```

### Pattern 4: Obsidian Vault Integration
Direct output to vault's research folder:
```bash
python scripts/firecrawl_research.py topics.md ~/Brains/brain/Research
```

## Error Handling

### "API key not found"
Create `.env` file in skill folder with `FIRECRAWL_API_KEY=...`

### "Rate limit exceeded"
- Free tier: 5 req/min
- Script has 12s delay built-in
- If still hitting limit, reduce topics or wait between runs

### "Insufficient credits"
- Check FireCrawl account credits
- Upgrade plan or wait for credit reset

### "No topics found"
Add topics to markdown using:
- `## Header format`
- `- [research] Topic format`
- `- [search] Topic format`

## Script Details

**Location:** `scripts/firecrawl_research.py`

**Dependencies:**
- `python-dotenv` - Environment variable management
- `requests` - HTTP requests to FireCrawl API

**Install dependencies:**
```bash
pip install python-dotenv requests
```

**FireCrawl Features Used:**
- `/v1/search` endpoint - Search with automatic scraping
- `scrapeOptions.formats: ['markdown']` - Markdown output
- `scrapeOptions.onlyMainContent: true` - Filter noise

## Academic Writing Templates

This skill includes templates for writing scientific papers in markdown format.

### Available Templates

**1. Pandoc Scholarly Paper** (`assets/templates/pandoc-scholarly-paper.md`)
- Standard academic paper format
- Compatible with Pandoc converter
- Supports citations via BibTeX
- Exports to PDF, DOCX, HTML

**2. MyST Scientific Paper** (`assets/templates/myst-scientific-paper.md`)
- MyST (Markedly Structured Text) format
- Advanced cross-referencing
- Professional scientific publishing
- Multi-format export (PDF, LaTeX, DOCX)

### Using Templates

**Copy template to your project:**
```bash
cp assets/templates/pandoc-scholarly-paper.md my-paper.md
# or
cp assets/templates/myst-scientific-paper.md my-paper.md
```

**Edit content:**
- Update YAML frontmatter (title, authors, affiliations)
- Write your content in sections
- Add citations using `[@AuthorYear]` (Pandoc) or `{cite}\`AuthorYear\`` (MyST)

**Convert to PDF/DOCX:**
```bash
python scripts/convert_academic.py my-paper.md pdf
python scripts/convert_academic.py my-paper.md docx
python scripts/convert_academic.py my-paper.md pdf --myst  # For MyST
```

### Bibliography Generation

Convert FireCrawl research results into BibTeX bibliography entries:

```bash
python scripts/generate_bibliography.py research_output/*.md -o references.bib
```

**What it does:**
- Extracts URLs and titles from FireCrawl markdown files
- Generates BibTeX `@misc` entries
- Creates citation keys automatically
- Adds access dates

**Example workflow:**
```bash
# 1. Research topics
python scripts/firecrawl_research.py topics.md ./research

# 2. Generate bibliography
python scripts/generate_bibliography.py research/*.md -o refs.bib

# 3. Copy template
cp assets/templates/pandoc-scholarly-paper.md paper.md

# 4. Edit paper.md (add content, cite sources)

# 5. Convert to PDF
python scripts/convert_academic.py paper.md pdf
```

### Citation Examples

**Pandoc syntax:**
```markdown
Recent research [@Smith2024] shows...
Multiple studies [@Jones2023; @Brown2024] indicate...
```

**MyST syntax:**
```markdown
Recent research {cite}`Smith2024` shows...
Multiple studies {cite}`Jones2023,Brown2024` indicate...
```

### Example Bibliography File

An example bibliography is provided in `assets/references.bib` with common entry types:
- Journal articles (`@article`)
- Conference papers (`@inproceedings`)
- Books (`@book`)
- PhD theses (`@phdthesis`)
- Web resources (`@misc`)
- Preprints (`@article` with arXiv)

## Tips

1. **Organize topics hierarchically** - Use `##` for main topics, `###` for subtopics
2. **Use descriptive names** - Topic text becomes filename, make it clear
3. **Batch processing** - Group related topics in one file for efficiency
4. **Output organization** - Create separate folders for different research projects
5. **Content review** - Results are truncated at 3000 chars/source for readability
6. **Academic workflow** - Use bibliography generator to cite research sources in papers
7. **Template customization** - Modify templates for your field's citation style

## Limitations

- **No summarization** - Returns raw scraped content, not summaries
- **No deduplication** - Duplicate sources may appear across topics
- **No quality ranking** - All results treated equally
- **New files only** - Does not append to existing files
- **Free tier constraints** - Rate limiting affects processing speed
