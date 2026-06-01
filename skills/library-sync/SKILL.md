---
name: library-sync
description: Sync and manage bilingual (EN/RU) library content for agency-docs. Use when adding, updating, or reviewing library articles. Handles translation, sync checks, and Russian stylistic review.
triggers:
  - /library-sync
  - sync library
  - add library article
  - update library article
  - library translation
  - review Russian translation
  - check library sync
---

# Library Sync Skill

Manages the bilingual library at `~/Sites/agency-docs/content/docs/library/` with English (`en/`) and Russian (`ru/`) versions.

## Commands

### `add <slug>` — Add a new article to both languages
1. Create the article in English first at `content/docs/library/en/<slug>.mdx`
2. Translate to Russian at `content/docs/library/ru/<slug>.mdx`
3. Add to both `meta.json` files in the appropriate section
4. Run Russian stylistic review
5. Verify both render correctly

### `sync` — Check sync status between EN and RU
1. List all files in `en/` and `ru/`
2. Report files missing in either language
3. Compare frontmatter titles (ensure they match conceptually)
4. Flag articles updated in one language but not the other (compare git timestamps)

### `translate <slug> <from> <to>` — Translate an article
1. Read the source article
2. Translate to target language
3. Adapt examples and links for the target audience
4. Run stylistic review if target is Russian
5. Update meta.json

### `review-ru` — Russian stylistic review
Run on all Russian library articles. Check for:
- **Consistency**: same terms used throughout (not mixing Агент/Эйджент)
- **Natural Russian**: not word-for-word translation from English
- **Technical terms**: keep English terms where standard (Git, MCP, API, CLAUDE.md)
- **Links**: internal links use `/library/ru/` paths
- **Tone**: educational but not condescending, informal "ты" address

### `update <slug>` — Update an existing article in both languages
1. Read the current version
2. Apply changes to the primary language
3. Sync changes to the other language
4. Run Russian review if Russian was changed

## File Structure

```
content/docs/library/
├── index.mdx          # Landing page
├── meta.json          # Top-level nav (separators + language folders)
├── en/
│   ├── meta.json      # English article order with section separators
│   └── *.mdx          # English articles
└── ru/
    ├── meta.json      # Russian article order with section separators
    └── *.mdx          # Russian articles
```

## Russian Style Guide

- Use "ты" (informal), not "вы" (formal)
- Keep technical terms in English: Git, API, MCP, CLAUDE.md, CLI, LLM, token
- Transliterate only when a Russian term is well-established: агент, промт, токен
- Don't translate code examples or command-line output
- Adapt cultural references (e.g., currency examples: use both $ and ₽)
- Cross-link to English version at the bottom: `[English version](/library/en/<slug>)`
- Cross-link from English to Russian: `[Русская версия](/library/ru/<slug>)`

## Meta.json Sections

Use `---SectionName---` separators in meta.json for nav grouping:
- Modes / Режимы
- Core Concepts / Ключевые концепции
- Features / Возможности
- Tools / Инструменты
- Reference / Справочник
