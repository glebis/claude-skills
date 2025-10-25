---
name: deep-research
description: This skill should be used when conducting comprehensive research on any topic using the OpenAI Deep Research API. It automates prompt enhancement through interactive clarifying questions, saves research parameters, and executes deep research with web search capabilities. Use when the user asks for in-depth analysis, investigation, research summaries, or topic exploration.
---

# Deep Research Skill

## Purpose

This skill enables comprehensive, internet-enabled research on any topic using OpenAI's Deep Research API (o4-mini-deep-research model). It intelligently enhances user research prompts through interactive clarifying questions, ensures research parameters are saved for reproducibility, and executes deep research with full web search capabilities.

## When to Use This Skill

Trigger this skill when:
- User requests research on a specific topic
- User asks for analysis, investigation, or comprehensive information gathering
- User wants exploration of a subject with web search and reasoning
- User provides a brief research query that could be refined
- User wants to understand current state, trends, or comparisons in a field

Example user requests:
- "Research the most effective open-source RAG solutions with high benchmark performance"
- "What are the latest AI developments in 2025?"
- "I need a comprehensive analysis of distributed database systems"
- "Find best practices for implementing vector search"
- "Investigate how AI is impacting the software engineering industry"

## Workflow Overview

```
User Input
    ↓
Assessment: Prompt too brief?
    ↓
YES → Ask Enhancement Questions → Collect Answers
    ↓                               ↓
    └───────→ Construct Enhanced Prompt ←──┘
                    ↓
            Save to Timestamped File
                    ↓
            Execute deep_research.py
                    ↓
            Output Report + Sources
                    ↓
            Present to User
```

## How Claude Should Use This Skill

**Important for Token Efficiency:**
Deep research takes 10-20 minutes to complete. The skill is designed to run synchronously (blocking) without intermediate status checks. This approach minimizes token usage during the wait. Claude should:
1. Start the research
2. Wait for completion (subprocess blocks automatically)
3. Present final results once complete

No need for periodic polling or status updates during execution.

### Step 1: Accept Research Request

Receive the user's research prompt. This can range from brief ("Latest AI trends") to highly detailed ("Impact of language models on developer productivity with focus on 2024-2025").

### Step 2: Execute the Orchestration Script

Run the skill's main orchestration script with the user's research prompt:

```bash
python3 scripts/run_deep_research.py "Your research prompt here"
```

The script is located at `scripts/run_deep_research.py` within the skill's installation.

### Step 3: Script Execution Flow

The script automatically:

1. **Assesses prompt completeness**: Checks if prompt is too brief or generic (< 15 words or starts with "what is", "how to", etc.)

2. **Asks clarifying questions** (if needed):
   - Presents 2-3 focused questions relevant to the research type
   - Detects if research is technical or general based on keywords
   - Allows users to select from predefined options (1-4) or provide custom text
   - Questions cover: Scope/Timeframe, Depth level, Focus areas

3. **Enhances the prompt**: Combines original prompt with user's answers into structured research parameters

4. **Saves prompt file**: Writes enhanced prompt to `research_prompt_YYYYMMDD_HHMMSS.txt` for reproducibility

5. **Executes deep research**: Runs the core `deep_research.py` script with:
   - Model: o4-mini-deep-research (configurable via `--model`)
   - Timeout: 1800 seconds / 30 minutes (configurable via `--timeout`)
   - Tools: Web search enabled by default

### Step 4: Present Results to User

The script automatically:
- **Saves markdown file**: Research report with sources saved to `research_report_YYYYMMDD_HHMMSS.md`
- **Prints to terminal**: Complete research report with markdown formatting
- **Lists web sources**: Numbered URLs referenced in the research
- **Confirms completion**: Path where research files were saved

**Token Efficiency Note**: Deep research takes 10-20 minutes. The script runs synchronously (blocking) without intermediate polling, minimizing token usage during the wait.

## Bundled Resources

### Scripts

#### `scripts/run_deep_research.py` (Main Entry Point)

The orchestration script that handles:
- Prompt quality assessment
- Interactive enhancement questions (with smart detection for technical vs. general research)
- Prompt saving and timestamping
- Execution of core deep research

**Key Features:**
- Smart enhancement: Only asks questions if prompt is brief/generic
- Template-based questions: Different question sets for technical vs. general research
- Flexible input: Numbered options + custom text input
- Error handling: Helpful messages if deep_research.py is not found

**Available options:**
```
python3 run_deep_research.py <prompt> [OPTIONS]
  --no-enhance              Skip enhancement questions
  --model <model>           Model to use (default: o4-mini-deep-research)
  --timeout <seconds>       Timeout in seconds (default: 1800)
  --output-dir <path>       Where to save prompt file
```

#### `assets/deep_research.py`

Core script that interfaces with OpenAI's Deep Research API. Handles:
- API authentication via OPENAI_API_KEY
- Request creation and execution
- **Automatic markdown saving**: Saves timestamped report files by default
- Output formatting (report + sources with metadata)
- Error handling and retries

**New command-line options:**
```
--output-file <path>      Custom output file path
--no-save                 Disable automatic markdown saving
```

### References

#### `references/workflow.md`

Detailed workflow documentation covering:
- Complete skill workflow with examples
- Prompt enhancement strategies
- Research parameters explanation
- Integration guidance for Claude
- Command-line interface reference
- Error handling and troubleshooting
- Tips for effective research

## Key Behaviors

### Smart Prompt Enhancement

The skill intelligently determines whether enhancement is needed:
- **Triggers enhancement** for prompts with < 15 words or generic starts
- **Skips enhancement** for detailed, specific prompts
- **Allows users** to disable with `--no-enhance` flag
- **Template-aware**: Uses different questions for technical vs. general research

### Research Parameters

Enhanced prompts include:
- Original user query with full context
- Scope and timeframe preferences
- Desired depth level (summary, technical, implementation, comparative)
- Specific focus areas (performance, cost, security, etc.)

These parameters help the deep research model deliver more targeted, relevant results.

### Reproducibility

Every research execution:
- Saves the exact prompt used to a timestamped file
- Enables tracing research decisions
- Allows follow-up research using same/modified prompts
- Maintains audit trail of research parameters

## Examples

### Brief Prompt with Enhancement

**User:** "Research the most effective opensource RAG solutions"

**Script behavior:**
1. Detects brief prompt (12 words) + technical keywords ("opensource", "RAG")
2. Asks technical research questions:
   - Technology scope: Open-source only? (User: Yes)
   - Key metrics: Performance/benchmarks? (User: Speed and Accuracy)
   - Use cases: Production deployment? (User: Multiple aspects)
3. Enhances to detailed prompt with parameters
4. Saves and executes deep research
5. Returns comprehensive report with comparative benchmarks and source URLs

### Detailed Prompt Without Enhancement

**User:** "Analyze the impact of large language models on software developer productivity in 2024-2025, focusing on code generation tools, pair programming, and productivity metrics."

**Script behavior:**
1. Detects detailed prompt (24 words) with specific scope/focus
2. Skips enhancement questions
3. Saves and executes deep research immediately
4. Returns focused analysis aligned with user specifications

## Requirements

- Python 3.7+
- OpenAI API key (set via `OPENAI_API_KEY` environment variable or `.env` file)
- Internet connection (for web search)
- 30+ minutes for research completion (configurable timeout)

## Token-Efficient Workflow

### Long-Running Task Optimization

Deep research queries typically take **10-20 minutes** to complete. This skill is optimized to minimize token usage during long waits:

**How it works:**
1. **Synchronous execution**: The script runs as a blocking subprocess (no background polling)
2. **No intermediate checks**: Claude waits silently for completion without status updates
3. **Single output**: Results are presented once at the end
4. **Automatic saving**: Markdown files are saved automatically, no manual intervention needed

**Token savings:**
- Traditional approach: Checking status every 30 seconds = ~40 checks × 500 tokens = ~20,000 tokens wasted
- This approach: Single wait = ~1,000 tokens total

### Automatic File Management

The skill automatically generates and saves files:

**Generated files:**
- `research_prompt_YYYYMMDD_HHMMSS.txt` - Enhanced research prompt with parameters
- `research_report_YYYYMMDD_HHMMSS.md` - Complete markdown report with:
  - Research sections (historical, cognitive, cultural, etc.)
  - Numbered source citations
  - Metadata footer (date, model)

**Customization options:**
```bash
# Custom output location
python3 deep_research.py --prompt-file prompt.txt --output-file my_research.md

# Disable automatic saving (terminal output only)
python3 deep_research.py --prompt-file prompt.txt --no-save
```

## Troubleshooting

### Missing OPENAI_API_KEY

**Error:** "Missing OPENAI_API_KEY"

**Solution:**
- Set environment variable: `export OPENAI_API_KEY="your-key"`
- Or create `.env` file in working directory with `OPENAI_API_KEY=your-key`

### deep_research.py Not Found

**Error:** "Could not find deep_research.py"

**Solution:**
- Ensure skill is properly installed with assets
- Script searches in: skill assets folder → current directory → parent directory

### Research Timeout

**Error:** Request times out after 30 minutes

**Solution:**
- Increase timeout: `--timeout 5400` (90 minutes)
- Simplify prompt to reduce research scope
- Run during off-peak hours for potentially faster API responses
