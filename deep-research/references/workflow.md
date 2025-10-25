# Deep Research Skill Workflow

## Overview

This skill enables comprehensive research on any topic using the OpenAI Deep Research API (o4-mini-deep-research model). It automates the process of enhancing user prompts through interactive clarifying questions, saving the research parameters, and executing the deep research.

## When to Use This Skill

Use this skill when:
- User requests in-depth research on a topic
- User asks for analysis, investigation, or comprehensive information gathering
- User wants to explore a subject with web search and structured reasoning
- User provides a brief or vague research query that needs refinement

Example triggers:
- "Research the most effective open-source RAG solutions"
- "I need to understand the current state of quantum computing"
- "Find information about emerging web frameworks"
- "Investigate best practices for distributed systems"

## Skill Workflow

### 1. **Receive User Research Prompt**

Accept the user's research request. This can be:
- Brief/vague: "Latest AI trends"
- Detailed: "Impact of large language models on software engineering in 2025"
- Technical: "Comparison of vector databases for semantic search"

### 2. **Assess Prompt Completeness**

Determine if the prompt needs enhancement:
- **Too brief** (< 15 words): Ask clarifying questions
- **Generic** (starts with "what is", "how to", etc.): Ask clarifying questions
- **Detailed/Specific**: Proceed directly to research

### 3. **Enhance Prompt (if needed)**

Ask user 2-3 focused clarifying questions based on research type:

**For General Research:**
- Scope/Timeframe: Latest (2024-2025), Historical, Specific period?
- Depth level: Executive summary, Technical, Implementation guide, Comparative?
- Focus areas: Performance, Cost, Ease of use, Security, Multiple?

**For Technical Research:**
- Technology scope: Open-source only, Enterprise, Language-specific?
- Key metrics: Speed, Accuracy, Scalability, Resources?
- Use cases: Production, Research, Education, Exploration?

Allow users to:
- Select from predefined options (numbered list)
- Provide custom text input for more control

### 4. **Construct Enhanced Prompt**

Combine:
1. Original user prompt
2. User's answers to clarification questions as structured research parameters

Example:
```
Original: "Most effective opensource RAG solutions with highest benchmark performance"

Enhanced: "Most effective opensource RAG solutions with highest benchmark performance

Research parameters:
- Latest developments (2024-2025)
- Technical deep dive
- Performance/Benchmarks
```

### 5. **Save Research Prompt**

Save the final research prompt to a timestamped file:
- Location: User's specified output directory or current working directory
- Format: `research_prompt_YYYYMMDD_HHMMSS.txt`
- Purpose: Reproducibility and audit trail of research parameters

Output: Display file path where prompt was saved

### 6. **Execute Deep Research**

Run `deep_research.py` with:
- Prompt file: The enhanced research prompt file
- Model: o4-mini-deep-research (configurable)
- Timeout: 1800 seconds / 30 minutes (configurable)
- Tools: Web search enabled by default

The script outputs:
- **Deep Research Report**: Comprehensive analysis with citations
- **Web Sources**: URLs extracted from search actions (numbered list)

### 7. **Present Results**

Output to user:
1. Research report (formatted markdown/text)
2. Referenced web sources (numbered list)
3. Path to saved research prompt file

## File Structure

```
deep-research/
├── SKILL.md                          # Skill metadata and instructions
├── scripts/
│   ├── run_deep_research.py         # Orchestration script (main entry point)
│   └── deep_research.py             # Core deep research API client
├── references/
│   └── workflow.md                  # This file - detailed workflow
└── assets/
    └── deep_research.py             # Copy for easy skill access
```

## Key Concepts

### Prompt Enhancement

Enhancement is **smart and optional**:
- Only triggered for brief or generic prompts
- Users can skip with `--no-enhance` flag
- Questions use closed-list options + custom text input
- Template-aware: Technical vs. General research questions

### Research Parameters

The enhanced prompt includes:
- Original user query with context
- Explicit scope/timeframe
- Depth level expectations
- Specific focus areas
- Success criteria

This helps the deep research model deliver more targeted results.

### Reproducibility

Each research run saves:
- Complete enhanced prompt used
- Timestamp for tracking
- Can be re-used or modified for follow-up research

## Integration with Claude

When Claude uses this skill:

1. **Receive research request** → Accept user prompt
2. **Check prompt quality** → Determine if enhancement needed
3. **Ask questions** → Guide user to refine scope (if needed)
4. **Execute script** → Run `run_deep_research.py` with enhanced prompt
5. **Present results** → Show report + sources to user
6. **Offer follow-ups** → Suggest related research directions or refinements

## Command-Line Interface

```bash
python3 run_deep_research.py "Your research prompt"
python3 run_deep_research.py "Brief prompt" --no-enhance
python3 run_deep_research.py "Prompt" --model o4-mini-deep-research
python3 run_deep_research.py "Prompt" --timeout 3600 --output-dir ./results
```

## Error Handling

The skill handles:
- Missing deep_research.py → Helpful error message with location hints
- Invalid API key → Passes through to deep_research.py error handling
- Timeout exceeded → User can increase timeout parameter
- Interrupted research → Saved prompt file available for retry

## Tips for Effective Research

1. **Be specific**: More specific prompts often yield better results even without enhancement
2. **Define scope**: Clarify timeframe and domain (e.g., "2025 trends in quantum computing")
3. **Set expectations**: Indicate desired output format (comparison table, timeline, etc.)
4. **Review sources**: Check URLs in results for credibility and relevance
5. **Iterate**: Use saved prompts as starting points for follow-up research
