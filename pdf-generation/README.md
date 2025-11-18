# PDF Generation Skill

Professional PDF generation from markdown using Pandoc with Eisvogel template and EB Garamond fonts.

## Overview

This skill enables Claude to generate professional PDFs from markdown files with:

- **Professional title pages** with color-coded themes
- **English and Russian language support** with proper typography
- **Automatic table of contents** generation
- **Theme-based styling** for different document types
- **Markdown preprocessing** to fix common formatting issues

## Installation

1. Download `pdf-generation.zip`
2. Extract to `~/.claude/skills/pdf-generation/`
3. Ensure dependencies installed:

```bash
# macOS
brew install pandoc
brew install --cask mactex

# Verify installation
pandoc --version
xelatex --version
```

## Quick Start

### Basic Usage

```bash
# Simple English PDF
pandoc document.md -o document.pdf --pdf-engine=xelatex --toc --toc-depth=2 \
  -V geometry:margin=2.5cm -V fontsize=11pt -V documentclass=article

# Russian PDF with EB Garamond
pandoc document-ru.md -o document.pdf --pdf-engine=xelatex --toc --toc-depth=2 \
  -V geometry:margin=2.5cm -V fontsize=11pt -V documentclass=article \
  -V mainfont="EB Garamond"
```

### Using the Generation Script

```bash
# White paper (blue theme)
scripts/generate_pdf.py report.md -t white-paper

# Marketing material (green theme)
scripts/generate_pdf.py marketing.md -t marketing

# Russian research paper (purple theme)
scripts/generate_pdf.py research-ru.md -t research --russian

# Custom output path
scripts/generate_pdf.py input.md -o custom/path/output.pdf
```

## Document Themes

Different document types use specific color schemes:

| Theme | Color | Use Case |
|-------|-------|----------|
| `white-paper` | Blue (1e3a8a) | White papers, reports |
| `marketing` | Green (059669) | Marketing materials |
| `research` | Purple (7c3aed) | Research papers, analysis |
| `technical` | Gray (374151) | Technical documentation |

## YAML Frontmatter

Add frontmatter to markdown files for professional title pages:

```yaml
---
title: "Document Title"
subtitle: "Document Subtitle"
author: "Author Name"
date: "2025-11-18"
titlepage: true
titlepage-color: "1e3a8a"
titlepage-text-color: "ffffff"
titlepage-rule-color: "ffffff"
titlepage-rule-height: 2
book: true
classoption: oneside
toc: true
toc-depth: 2
---
```

See `references/frontmatter_templates.md` for complete examples.

## Markdown Formatting

For proper list rendering, ensure blank lines before lists:

```markdown
### Section Title

This is a paragraph.

- List item 1
- List item 2

1. Numbered item 1

   - Nested item (3 spaces indent)
   - Nested item
```

**Fix formatting automatically:**

```bash
scripts/fix_markdown.py input.md output.md
```

## Skill Structure

```
pdf-generation/
├── SKILL.md                              # Main skill definition
├── README.md                             # This file
├── scripts/
│   ├── generate_pdf.py                   # Automated PDF generation
│   └── fix_markdown.py                   # Markdown preprocessing
└── references/
    ├── frontmatter_templates.md          # YAML frontmatter examples
    └── pandoc_reference.md               # Pandoc command reference
```

## Script Options

### generate_pdf.py

```
Options:
  -t, --theme        Document theme (white-paper, marketing, research, technical)
  -r, --russian      Enable EB Garamond font for Russian text
  -o, --output       Custom output path
  --no-toc          Disable table of contents
  --toc-depth       TOC depth (default: 2)
  --margin          Page margin (default: 2.5cm)
  --fontsize        Font size (default: 11pt)
```

### fix_markdown.py

```
Usage: fix_markdown.py <input.md> [output.md]

Fixes:
- Adds blank lines before lists
- Handles lists after colons (Claude Code format)
- Handles nested list formatting
- Ensures proper spacing after headings

Example - Claude Code pattern:
"text with colon:"
"- list item"  → Auto-adds blank line
```

## Troubleshooting

### Pandoc not found

```bash
brew install pandoc  # macOS
sudo apt-get install pandoc  # Linux
```

### XeLaTeX not found

```bash
brew install --cask mactex  # macOS
sudo apt-get install texlive-xetex  # Linux
```

### Lists rendering as inline text

Run markdown preprocessor:

```bash
scripts/fix_markdown.py input.md fixed.md
pandoc fixed.md -o output.pdf --pdf-engine=xelatex
```

### Russian text not rendering

Ensure EB Garamond font installed and specify:

```bash
pandoc input.md -o output.pdf -V mainfont="EB Garamond"
```

### Unicode characters missing (▬, ✓)

These are warnings, not errors. Content renders correctly. To eliminate warnings, use standard ASCII alternatives in source markdown.

## Examples

### Example 1: White Paper

```yaml
---
title: "Product Strategy 2025"
subtitle: "Market Analysis and Roadmap"
author: "Strategy Team"
date: "November 2025"
titlepage: true
titlepage-color: "1e3a8a"
titlepage-text-color: "ffffff"
book: true
toc: true
---

# Executive Summary

Key findings from market analysis...
```

```bash
scripts/generate_pdf.py strategy.md -t white-paper
```

### Example 2: Russian Research Paper

```yaml
---
title: "Анализ данных здоровья"
subtitle: "Кардиоваскулярные метрики"
author: "Исследовательская группа"
date: "Ноябрь 2025"
titlepage: true
titlepage-color: "7c3aed"
titlepage-text-color: "ffffff"
book: true
toc: true
---

# Введение

Анализ показателей здоровья...
```

```bash
scripts/generate_pdf.py research-ru.md -t research --russian
```

## Dependencies

- **Pandoc** (>=2.0) - Document converter
- **XeLaTeX** (TeX Live) - PDF engine
- **Python 3** (>=3.6) - For scripts
- **EB Garamond font** (optional) - For Russian documents

## License

MIT

## Contributing

Issues and improvements welcome at your GitHub repository.

## Version

1.0.0 - Initial release with Eisvogel styling, Russian support, and markdown preprocessing
