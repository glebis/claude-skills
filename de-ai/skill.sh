#!/bin/bash

# De-AI Text Humanization Skill
# Transforms AI-sounding text into human, authentic writing

set -e

# Parse arguments
TEXT=""
FILE=""
LANGUAGE=""
REGISTER=""
INTERACTIVE="true"
EXPLAIN="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --text)
            TEXT="$2"
            shift 2
            ;;
        --file)
            FILE="$2"
            shift 2
            ;;
        --language)
            LANGUAGE="$2"
            shift 2
            ;;
        --register)
            REGISTER="$2"
            shift 2
            ;;
        --interactive)
            INTERACTIVE="$2"
            shift 2
            ;;
        --explain)
            EXPLAIN="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate input
if [ -z "$TEXT" ] && [ -z "$FILE" ]; then
    echo "Error: Must provide either --text or --file"
    exit 1
fi

# Get text content
if [ -n "$FILE" ]; then
    if [ ! -f "$FILE" ]; then
        echo "Error: File not found: $FILE"
        exit 1
    fi
    TEXT=$(cat "$FILE")
fi

# Build context
CONTEXT="# De-AI Text Humanization

Source: $([ -n "$FILE" ] && echo "File: $FILE" || echo "Inline text")
Interactive mode: $INTERACTIVE
Language: ${LANGUAGE:-auto-detect}
Register: ${REGISTER:-auto-detect}
Explain changes: $EXPLAIN

## Original Text

$TEXT

---

## Instructions

"

# Add workflow based on settings
if [ "$INTERACTIVE" = "true" ]; then
    CONTEXT+="Follow the full workflow from system.md:
1. **Context Gathering**: Use AskUserQuestion to understand purpose, audience, and constraints
2. **AI Tell Diagnosis**: Identify patterns at all six levels
3. **Humanization**: Apply language-appropriate transformations
4. **Register Adaptation**: Match intensity to text type
5. **Quality Check**: Verify meaning preserved and clarity maintained
6. **Output**: "
else
    CONTEXT+="Skip context gathering. Apply humanization directly:
1. **AI Tell Diagnosis**: Identify patterns quickly
2. **Humanization**: Apply language-appropriate transformations
3. **Quality Check**: Verify meaning and clarity
4. **Output**: "
fi

if [ "$EXPLAIN" = "true" ]; then
    CONTEXT+="Provide revised text followed by a short bullet list of main AI tells removed."
else
    CONTEXT+="Provide revised text only (no commentary)."
fi

# Add language-specific guidance
if [ -n "$LANGUAGE" ]; then
    case $LANGUAGE in
        ru|russian)
            CONTEXT+="

**Russian-specific focus:**
- Remove канцелярит (bureaucratic language)
- Reduce excessive participles
- Replace formal pronouns
- Use живую речь (living speech)"
            ;;
        de|german)
            CONTEXT+="

**German-specific focus:**
- Break excessive compounds
- Vary sentence structure
- Add conversational particles appropriately
- Mix Nominalstil with Verbalstil"
            ;;
        en|english)
            CONTEXT+="

**English-specific focus:**
- Use contractions naturally
- Mix latinate and germanic vocabulary
- Vary sentence openings
- Active voice predominantly"
            ;;
    esac
fi

# Output context for Claude to process
echo "$CONTEXT"
