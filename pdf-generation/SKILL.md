---
name: pdf-generation
description: Professional PDF generation from markdown using Pandoc with Eisvogel template and EB Garamond fonts. Use when converting markdown to PDF, creating white papers, research documents, marketing materials, or technical documentation. Supports both English and Russian documents with professional typography and color-coded themes. Mobile-optimized layout (6x9) by default for Telegram bot context, desktop/print layout (A4) for other contexts.
---

# PDF Generation

## Overview

Generate professional PDFs from markdown files using Pandoc with Eisvogel template styling. Supports English and Russian documents with customizable themes, table of contents, and professional typography including EB Garamond font for Russian text.

## Quick Start

Basic commands:

```bash
# Desktop/Print PDF (A4 format)
pandoc doc.md -o doc.pdf --pdf-engine=xelatex --toc --toc-depth=2 -V geometry:margin=2.5cm -V fontsize=11pt -V documentclass=article

# Mobile-friendly PDF (6x9 phone screen optimized)
pandoc doc.md -o doc-mobile.pdf --pdf-engine=xelatex --toc --toc-depth=2 -V geometry:paperwidth=6in -V geometry:paperheight=9in -V geometry:margin=0.5in -V fontsize=10pt -V linestretch=1.2

# Russian PDF with EB Garamond
pandoc doc-ru.md -o doc.pdf --pdf-engine=xelatex --toc --toc-depth=2 -V geometry:margin=2.5cm -V fontsize=11pt -V documentclass=article -V mainfont="EB Garamond"

# Russian Mobile PDF
pandoc doc-ru.md -o doc-mobile.pdf --pdf-engine=xelatex --toc --toc-depth=2 -V geometry:paperwidth=6in -V geometry:paperheight=9in -V geometry:margin=0.5in -V fontsize=10pt -V linestretch=1.2 -V mainfont="EB Garamond"
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

## Layout Options

### Desktop/Print Layout (A4)
- Paper: 210mm x 297mm (A4)
- Margins: 2.5cm
- Font size: 11pt
- Best for: Printing, reading on large screens, archival

### Mobile Layout (Phone-optimized)
- Paper: 6in x 9in (phone aspect ratio)
- Margins: 0.5in (minimal for screen space)
- Font size: 10pt with 1.2 line spacing
- Best for: Phone/tablet reading, Telegram/messaging apps

**Default for Telegram Bot**: Use mobile layout for all PDFs sent via Telegram unless user explicitly requests print/desktop version.

## Generation Workflows

### Workflow 1: Simple PDF

1. Check context (Telegram = mobile, otherwise desktop)
2. Check if Russian (use EB Garamond if yes)
3. Run appropriate pandoc command
4. Verify output

### Workflow 2: Professional Title Page

1. Add YAML frontmatter with theme color
2. Include metadata (title, author, date)
3. Choose layout (mobile vs desktop)
4. Generate with xelatex

### Workflow 3: Using Script

```bash
scripts/generate_pdf.py doc.md -t white-paper
scripts/generate_pdf.py doc.md -t marketing --russian
scripts/generate_pdf.py doc.md --mobile  # Mobile layout
```

## Resources

- **scripts/generate_pdf.py** - Automated generation
- **references/frontmatter_templates.md** - YAML templates
- **references/pandoc_reference.md** - Command reference

## Troubleshooting

Install pandoc: `brew install pandoc`
Install LaTeX: `brew install --cask mactex`
## Mobile-Friendly PDFs

For phone and tablet reading, use the mobile layout option:

```bash
# Using script (recommended)
scripts/generate_pdf.py doc.md --mobile

# Direct pandoc command
pandoc doc.md -o doc-mobile.pdf \
  --pdf-engine=xelatex \
  --toc --toc-depth=2 \
  -V geometry:paperwidth=6in \
  -V geometry:paperheight=9in \
  -V geometry:margin=0.5in \
  -V fontsize=10pt \
  -V linestretch=1.2 \
  -V colorlinks=true \
  -V linkcolor=blue \
  -V urlcolor=blue
```

**Mobile layout features**:
- 6x9 inch page size (optimal for mobile screens)
- 10pt font (readable on smaller screens)
- 0.5in margins (maximizes content area)
- 1.2 line spacing (improved readability)
- Auto-generated `-mobile.pdf` filename suffix

**When to use mobile layout**:
- Sharing research via Telegram/messaging apps
- Reading on phones or tablets
- Creating portable reference documents
- Quick consumption on the go

**Default context**: Mobile layout is used by default when generating PDFs through the Telegram bot for optimal mobile reading experience.
