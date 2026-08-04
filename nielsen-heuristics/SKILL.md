---
name: nielsen-heuristics
description: MOVED — nielsen-heuristics now ships in the humane plugin (glebis/humane-agentic-design), not here. This directory is a redirect; install humane to get the maintained skill.
---

# nielsen-heuristics has moved

This skill is now part of **[humane-agentic-design](https://github.com/glebis/humane-agentic-design)**,
where it sits inside the design method cycle it belongs to and is maintained
alongside the skills it hands off to.

```
npx skills add glebis/humane-agentic-design
```

In Claude Code:

```
/plugin marketplace add glebis/humane-agentic-design
/plugin install humane@humane-agentic-design
```

## Why the copy here was removed

One skill should live in exactly one channel. Two published copies of the
same name drift, and this one had: it was frozen in 2026-07 and lacked
the shared humane review contract — finding caps, a required considered-but-rejected table, and the Block/Needs changes/Approve verdict that lets it consolidate with the other review skills.

Leaving it installable would have meant someone running the old behaviour
while reading the current documentation.
