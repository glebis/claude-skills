---
name: context-builder
description: Generate interactive AI transformation context-builder prompts for consulting clients. Use when creating structured discovery session prompts that guide a company through context gathering about their business, pain points, tech stack, and AI opportunities. Produces a resumable, multi-section prompt with Express/Deep Dive modes.
---

# Context Builder

Generate interactive context-building prompts for consulting clients. These prompts are designed to be run in Claude Code -- they guide a team through structured questions using AskUserQuestion, generate output files per section, and compile everything into a reusable CLAUDE.md.

## Workflow

### Phase 1: Intake (AskUserQuestion)

Ask all intake questions using AskUserQuestion with closed-list options. Gather:

**Question 1: Company identifier**
- Options: "I have a website URL", "I have a company name", "I have both"
- Follow up to get the actual URL/name

**Question 2: Who will use this prompt?**
- Options: "Specific person (name + role)", "A team (no specific person)", "Unknown / TBD"
- If specific person: follow up for name and role

**Question 3: Primary consulting focus** (multiSelect)
- "AI automation of current operations"
- "Existential strategy (what survives AI)"
- "New business models / pivots"
- "Product development with AI"

**Question 4: Industry**
- "Marketing / Advertising"
- "Manufacturing / Construction"
- "SaaS / Software"
- "Professional Services / Consulting"
- (Other)

**Question 5: Existing context in vault?**
- "Yes, there's a call transcript"
- "Yes, there are notes/files"
- "No existing context"
- If yes: ask for filename or search term to locate it

**Question 6: Session language**
- "Russian (questions in Russian, output in English)"
- "English throughout"
- "Other"

### Phase 2: Research (automated)

Run these research steps in parallel where possible:

1. **Web research**: Use WebSearch and WebFetch (via Task agent) to gather:
   - What the company does, products/services
   - Target market, company size, geography
   - Tech stack, partnerships
   - Recent news, funding, team info
   - Competitive landscape

2. **Vault search**: Search the Obsidian vault for:
   - Transcripts mentioning the company name (Grep in vault root and Daily/)
   - People files for contacts at the company (People/ folder)
   - Any existing notes or research

3. **Transcript analysis** (if found): Extract from call transcripts:
   - Team members and their roles
   - Current AI tool usage
   - Pain points and concerns mentioned
   - Specific processes described
   - Questions raised by the team

### Phase 3: Section Selection (AskUserQuestion)

Present a curated set of sections based on the consulting focus. Use AskUserQuestion with multiSelect to let the user pick which sections to include.

#### Section Library

Draw from `references/section-library.md` for the full section catalog. Default section sets by focus:

**AI Automation focus:**
1. Process Inventory, 2. Pain Points & Waste, 3. Current Tech Stack, 4. AI Opportunity Mapping, 5. People & Org, 6. Data Reality Check, 7. Quick Wins

**Existential Strategy focus:**
1. Revenue & Service Map, 2. The Existential Question, 3. Client Value Chain, 4. New Business Models, 5. Data & Knowledge Assets, 6. People & Org, 7. Quick Wins & Pilots

**Full Assessment (both):**
All 10 sections from the library.

After section selection, ask:

**Express mode grouping**: Present a suggested grouping of selected sections into 4 Express mega-sections. Let user confirm or adjust.

### Phase 4: Generation

Generate two files:

#### 1. The Context-Builder Prompt

Save to: `Claude-Drafts/{company-slug}-context-prompt.md`

**Structure** (follow the template in `references/prompt-template.md`):

```
---
created_date: '[[YYYYMMDD]]'
type: draft
topic: consulting, AI transformation, {industry}
for: {contact person or team name}
---

# AI Transformation Context Builder -- {Company Name}

## About {Company}
  [Generated from research -- company description, size, market, positioning]

## Current State
  **What's working:** [from research + transcript]
  **The gap:** [from research + transcript]
  [If existential concerns found: **Existential context:**]

## Mode Selection
  [Express vs Deep Dive with section descriptions]

## How This Works
  [Standard interactive session instructions]

## Session Resumability
  [Standard resumability logic]

## Interactive Flow
  [Selected sections with tailored questions]

## Output Files
  [One file per section + final CLAUDE.md]

## Relevant Frameworks
  [Selected from references/frameworks.md based on focus]
```

#### 2. Instruction File (optional)

If the prompt will be sent to someone external, generate a short instruction file:
`Claude-Drafts/{company-slug}-context-instructions.md`

Containing:
- What this file is and how to use it
- Prerequisites (Claude Code or similar)
- The two modes explained simply
- What they'll get on output
- Privacy note (they can share as much or as little as they want)

### Phase 5: Delivery (AskUserQuestion)

**Question: What to do with the generated files?**
- "Save to vault only"
- "Save and send via Telegram"
- "Save and let me review first"

If Telegram: ask for the recipient handle/name, then send using the telegram skill (intro message + file).

## Key Principles

- **Maximize closed-list questions**: Every AskUserQuestion should have concrete options. Minimize free-text input.
- **Research before asking**: Don't ask the user things that can be found via web search or vault search.
- **Tailor sections to context**: If the transcript reveals specific concerns (e.g., existential fears, specific tech stack), customize the section questions to reference those specifics.
- **Bake in discovered context**: The generated prompt's "About" and "Current State" sections should be rich with researched details so the person running the prompt gets a warm start.
- **Language awareness**: If session language is Russian, all AskUserQuestion interactions during prompt execution should be in Russian, but output files in English.

## Resources

### references/
- `section-library.md` -- Full catalog of available sections with question templates
- `prompt-template.md` -- Structural template for the generated prompt
- `frameworks.md` -- Consulting frameworks to selectively include
