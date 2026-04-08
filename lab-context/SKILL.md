---
name: lab-context
description: Use when the user wants to set up, view, or update their Claude Code Lab personal profile — including goals, skill level, learned tools, and active projects. Triggers on phrases like "set up lab context", "update my lab profile", "what have I learned at the lab", "add a goal", "настрой lab-контекст", "обнови профиль лаборатории". Stores data as plain markdown in an Obsidian-compatible vault so the user owns their data.
---

# Lab Context

Maintains the Claude Code Lab participant profile as plain markdown in a local vault.

## Language

**Default: English.** Switch to Russian if the user writes to you in Russian. Never mix languages in generated files — pick one per file based on how the user spoke when creating/updating it.

## Where data lives

Default vault: `~/claude-lab-vault/`. Override via `CLAUDE_LAB_VAULT` env var or by asking the user on first setup.

Verify the vault exists before any operation. If missing — propose creating it and confirm the path. The path MUST be a subfolder, never `$HOME` directly and never the root of an existing git project.

## Файлы профиля

Всегда markdown с YAML frontmatter для машинного чтения + человеческий текст ниже.

### `profile.md`
```markdown
---
name: <имя>
role: <роль/должность>
experience_level: beginner | intermediate | advanced
primary_language: <основной язык программирования или "none">
updated: <YYYY-MM-DD>
---

# Профиль

Свободный текст о пользователе: бэкграунд, контекст, особенности.
```

### `goals.md`
```markdown
---
updated: <YYYY-MM-DD>
---

# Цели

- [ ] <цель 1> — <почему важно>
- [x] <достигнутая цель> — <дата>
```

### `tools-learned.md`
```markdown
---
updated: <YYYY-MM-DD>
---

# Изученные инструменты

## <YYYY-MM-DD> — <тема встречи лабы>
- **<инструмент>** — краткое описание, уровень уверенности (tried/comfortable/confident)
```

### `projects.md`
```markdown
---
updated: <YYYY-MM-DD>
---

# Активные проекты

## <Название>
- **Путь:** `<абсолютный путь>`
- **Статус:** active | paused | done
- **Описание:** одно предложение
```

## Операции

### Initial setup

Use **`AskUserQuestion`** for structured questions — faster and cleaner than a free-form interview. Free text only for fields where choice is impossible (name, project description).

1. **Vault path.** Ask in plain text, suggest the default `~/claude-lab-vault/`. Confirm it's a subfolder.
2. **Create the directory** and four starter files with empty frontmatter.
3. **Structured questions** via `AskUserQuestion`:
   - **"What's your role?"** (singleSelect): developer / designer / product / researcher / founder / other
   - **"How often do you use Claude Code?"** (singleSelect): just started / occasionally / daily / I build my own skills and MCPs
   - **"Primary language or stack?"** (singleSelect): Python / TypeScript / Go / Rust / I don't code / other
   - **"What do you want to get out of the lab?"** (multiSelect): automate routine / build my own product / master MCP and Skills / understand subagents / clean up my workflow / learn to deploy
   - **"Do you have an active project where you can apply practice?"** (singleSelect): yes, work / yes, personal / no, need a playground
4. **Free text** as separate messages: name, one-line project description (if any), project path.
5. Write everything into the matching files. Keep it under 3 minutes — first-run should be painless.

### Update
On "update X" / "add Y" — read the file, preserve existing data, change only what was asked. Update `updated:` in frontmatter.

### Read
"What's in my profile?", "show my goals" — read the file and summarise briefly. Don't dump raw markdown unless asked.

## Rules

- **Never overwrite a file wholesale** without user confirmation. Use Edit.
- **Wikilinks are encouraged**: `[[projects/my-app]]`, `[[tools-learned#MCP]]` — the user reads this in Obsidian.
- **Dates are always absolute** (`2026-04-08`), never "today".
- **Don't invent fields** — only what the user said or confirmed.
- If the vault is empty and the user asks for homework or a session review — point them to initial setup first.
