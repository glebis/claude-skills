---
name: automation-advisor
description: Interactive automation decision advisor using the Automation Decision Matrix framework. Use when the user asks "should I automate this?", wants to evaluate an automation opportunity, calculate automation ROI or break-even, or requests an automation decision analysis. Guides a structured questionnaire, scores four dimensions, applies override checks, and generates an Obsidian-formatted report with a visual decision diagram.
---

# Automation Advisor

Help the user decide whether to automate a task using data, not gut feeling.

## Process

1. Gather task context through freeform conversation
2. Score four dimensions using AskUserQuestion
3. Calculate the automation score
4. Apply override checks
5. Recommend validation patterns for high-stakes automation
6. Calculate break-even analysis
7. Generate a markdown report + visualization (`visualize.py`)

Follow the full interactive flow in [prompt.md](prompt.md).

**Output location:** `/Users/glebkalinin/Brains/brain/automation-decisions/`

## Optional web/voice interface

A voice-enabled (Groq TTS) web interface lives in `server_web.py` / `server.py` — see [docs/WEB_SERVER_GUIDE.md](docs/WEB_SERVER_GUIDE.md) and [docs/QUICKSTART.md](docs/QUICKSTART.md).
