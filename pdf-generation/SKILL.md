---
name: pdf-generation
description: Professional PDF generation from markdown using Pandoc with Eisvogel template and EB Garamond fonts. Use when converting markdown to PDF, creating white papers, research documents, marketing materials, or technical documentation. Supports both English and Russian documents with professional typography and color-coded themes.
---

# PDF Generation

## Overview

Generate professional PDFs from markdown files using Pandoc with Eisvogel template styling. Supports English and Russian documents with customizable themes, table of contents, and professional typography including EB Garamond font for Russian text.

## Quick Start

Basic commands:

```bash
# English PDF
pandoc doc.md -o doc.pdf --pdf-engine=xelatex --toc --toc-depth=2 -V geometry:margin=2.5cm -V fontsize=11pt -V documentclass=article

# Russian PDF with EB Garamond
pandoc doc-ru.md -o doc.pdf --pdf-engine=xelatex --toc --toc-depth=2 -V geometry:margin=2.5cm -V fontsize=11pt -V documentclass=article -V mainfont="EB Garamond"
```

## Document Theme Colors

- **White Papers** - Blue (1e3a8a)
- **Marketing** - Green (059669)
- **Research** - Purple (7c3aed)
- **Technical** - Gray (374151)

## YAML Frontmatter Example

```yaml
---
title: "Document Title"
subtitle: "Subtitle"
author: "Author"
date: "2025-11-18"
titlepage: true
titlepage-color: "1e3a8a"
titlepage-text-color: "ffffff"
book: true
---
```

See references/frontmatter_templates.md for complete templates.


## Markdown Formatting Best Practices

For optimal PDF rendering, ensure:

1. **Blank lines before lists** - Required for proper list rendering
2. **Blank lines after headings** - Improves spacing
3. **Nested list indentation** - Use 3 spaces for sub-items

### Common Claude Code Pattern

Lists after colons need blank lines:

```markdown
Your data spans 9 years with complete tracking:

- Item 1
- Item 2
```

Without blank line after colon, renders as inline text.

### Automatic Fix

Use preprocessing script:

```bash
scripts/fix_markdown.py input.md output.md
```

Automatically detects and fixes:
- Lists after colons (Claude Code format)
- Lists after headings
- Nested list spacing

## Generation Workflows

### Workflow 1: Simple PDF

1. Check if Russian (use EB Garamond if yes)
2. Run pandoc command
3. Verify output

### Workflow 2: Professional Title Page

1. Add YAML frontmatter with theme color
2. Include metadata (title, author, date)
3. Generate with xelatex

### Workflow 3: Using Script

```bash
scripts/generate_pdf.py doc.md -t white-paper
scripts/generate_pdf.py doc.md -t marketing --russian
```

## Resources

- **scripts/generate_pdf.py** - Automated generation
- **references/frontmatter_templates.md** - YAML templates
- **references/pandoc_reference.md** - Command reference

## Troubleshooting

Install pandoc: `brew install pandoc`
Install LaTeX: `brew install --cask mactex`