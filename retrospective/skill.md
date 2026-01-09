# Retrospective

Session retrospective for continual learning. Reviews conversation, extracts learnings, updates skills.

## When to Use

Run at end of coding sessions to capture learnings before context is lost. Invoke via `/retrospective` or when user says "let's do a retro".

## Process

### 1. Session Analysis

Review the entire conversation and identify:

**Successes**
- What worked well
- Effective approaches discovered
- Useful patterns or techniques
- Tools/commands that solved problems

**Failures**
- What didn't work
- Dead ends encountered
- Errors and their root causes
- Approaches to avoid

**Discoveries**
- New insights about the codebase
- Unexpected behaviors
- Configuration quirks
- Edge cases found

### 2. Skill Identification

Determine which skills were used or could benefit:
- Check `~/.claude/skills/` for personal skills
- Check `.claude/skills/` for project skills
- Identify if new skill should be created

### 3. Learning Extraction

For each relevant skill, extract:
```markdown
## Learnings from [DATE]

### What Worked
- [specific technique or approach]

### What Failed
- [approach] — [why it failed]

### Configuration Notes
- [any settings or params that matter]
```

### 4. Skill Update

Update skill files with extracted learnings:
- Add to existing `## Learnings` or `## Known Issues` sections
- Create sections if they don't exist
- Keep entries dated and concise
- Preserve existing content

### 5. Summary Output

Report to user:
- Skills updated (with paths)
- Key learnings captured
- Suggested new skills (if patterns emerged)

## Output Format

```
## Session Retrospective

### Skills Updated
- `~/.claude/skills/[name]/skill.md` — added [X] learnings

### Key Takeaways
1. [Most important learning]
2. [Second learning]

### Failures Documented
- [Failure 1]: [brief reason]

### Suggested Actions
- [ ] Create new skill for [pattern]
- [ ] Update CLAUDE.md with [insight]
```

## Guidelines

- **Be specific**: "Use `--no-cache` flag" not "caching can cause issues"
- **Include context**: When/why something works or fails
- **Date entries**: Learnings should have dates for tracking
- **Don't over-document**: Only capture genuinely useful insights
- **Failures are valuable**: Non-deterministic LLM behavior means documenting anti-patterns prevents repeating mistakes

## Example Skill Update

Adding to `~/.claude/skills/pdf-generation/skill.md`:

```markdown
## Known Issues

### 2025-01-01
- Eisvogel template fails with emoji in headers — escape or remove
- Russian text needs `babel-lang: russian` in YAML frontmatter

## What Works

### 2025-01-01
- `--pdf-engine=xelatex` required for non-Latin scripts
- Pre-flight check: `pandoc --version` to verify filters installed
```

## Integration

Can be combined with:
- Git commit hooks (auto-retro before commit)
- CLAUDE.md instructions (remind to run retro)
- CI/CD (capture learnings from failed builds)

## Tools

- Read: Access skill files and conversation history
- Edit: Update existing skills
- Write: Create new skill files if needed
- Glob: Find skill directories

## Learnings

