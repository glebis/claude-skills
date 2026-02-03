# De-AI Text Humanization Skill

Transform AI-sounding text into human, authentic writing while preserving meaning and facts.

## Key Differentiators

Unlike commercial de-AI tools that focus on detection evasion, this skill prioritizes:

1. **Meaning preservation** over detection bypass
2. **Interactive dialogue** - understands context before processing
3. **Language-specific optimization** - especially Russian, German, English
4. **Professional quality** - not just for academic cheating
5. **Transparency** - explains what was changed and why
6. **No word limits** - process entire documents

## Installation

```bash
# Copy to Claude Code skills directory
cp -r de-ai ~/.claude/skills/

# Or clone from GitHub
git clone https://github.com/glebis/claude-skills.git
cp -r claude-skills/de-ai ~/.claude/skills/
```

No additional dependencies required - works out of the box with Claude Code.

## Usage

### Basic Usage

```bash
# Process file (interactive mode)
/de-ai --file article.md

# Process inline text
/de-ai --text "Your AI-generated text here..."
```

### Advanced Options

```bash
# Specify language
/de-ai --file article.md --language ru

# Specify register/type
/de-ai --file draft.txt --register essay

# Quick mode (no questions)
/de-ai --file content.md --interactive false

# Show explanation of changes
/de-ai --file text.md --explain true

# Combine options
/de-ai --file article.md --language de --register technical --explain true
```

## Parameters

- `--text` - Text to humanize (alternative to --file)
- `--file` - Path to file containing text
- `--language` - Target language: en, ru, de, es, fr (auto-detected if not specified)
- `--register` - Text type: personal, essay, critique, narrative, technical, academic
- `--interactive` - Ask clarifying questions (default: true)
- `--explain` - Show AI tells removed (default: false)

## Supported Languages

- **English** (en)
- **Russian** (ru)
- **German** (de)
- **Spanish** (es)
- **French** (fr)

Each language has specific optimization patterns based on linguistic research.

## Register Types

- **Personal** - Strong subjective voice, emotional variation
- **Essay/Analysis** - Varied formality, allows uncertainty
- **Critique** - Evaluative language, stronger opinions
- **Narrative** - Temporal variation, personal reflection
- **Technical** - Preserves precision, reduces stylistic AI tells
- **Academic** - Maintains rigor, removes meta-commentary

## How It Works

### Phase 1: Context Gathering (if interactive)

The skill asks about:
- Purpose and audience
- Constraints (must preserve facts, citations, terms?)
- Priorities (can restructure? can add subjectivity?)
- Language-specific preferences

### Phase 2: AI Tell Diagnosis

Identifies patterns at six levels:
1. **Structural** - uniform paragraphs, symmetrical organization
2. **Sentence** - uniform complexity, similar lengths
3. **Lexical** - stock AI vocabulary, repetitive phrases
4. **Voice** - emotional flatness, no subjective markers
5. **Rhetorical** - meta-signposting, over-explaining
6. **Predictability** - too-safe word choices, low perplexity

### Phase 3: Humanization

Applies language-appropriate transformations:
- Vary paragraph/sentence length aggressively
- Remove stock AI vocabulary
- Add emotional range and subjective markers
- Increase unpredictability
- Cut meta-commentary
- Allow imperfection

### Phase 4: Quality Check

Verifies:
- Meaning preserved
- Perplexity increased
- Structural/lexical diversity
- Voice authenticity
- Clarity maintained

## Examples

### Russian Academic Text

**Before**:
```
В современном мире важно отметить, что данный подход является комплексным решением. Необходимо учитывать следующие аспекты.
```

**After**:
```
Этот подход решает сразу несколько задач. Методология работает — это видно по результатам.
```

### English Technical Explanation

**Before**:
```
It is important to note that in order to achieve robust performance, one must leverage comprehensive testing methodologies.
```

**After**:
```
Strong performance needs thorough testing. Period.
```

### German Business Communication

**Before**:
```
Es ist wichtig zu beachten, dass im Hinblick auf die nachhaltige Entwicklung umfassende Maßnahmen erforderlich sind.
```

**After**:
```
Für nachhaltige Entwicklung brauchen wir konkrete Schritte. Nicht nur einzelne Projekte—das Ganze muss zusammenpassen.
```

## Research Foundation

Based on:
- 7 academic papers on AI text detection (2023-2026)
- 30+ commercial tool analysis
- Linguistic pattern research across languages
- Multilingual NLP studies

Key findings:
- Perplexity and lexical repetitiveness are primary AI tells (Kujur, 2025)
- Register-specific differences matter (Goulart et al., 2024)
- Intrinsic features beat semantic features for detection (Yu et al., 2024)
- Commercial tools sacrifice meaning for detection evasion

## Use Cases

### Professional Writing
- Blog posts and articles
- Business communications
- Technical documentation
- Marketing copy

### Academic Work
- Essay refinement (integrity-preserving)
- Research paper editing
- Grant applications
- Literature reviews

### Multilingual Content
- Russian business communications
- German technical writing
- English-Russian translation cleanup
- Multilingual marketing materials

### Content Creation
- Newsletter writing
- Social media posts
- Video scripts
- Podcast show notes

## When NOT to Use

This skill is **not** for:
- Academic cheating or plagiarism
- Hiding AI authorship dishonestly
- Bypassing detection for deceptive purposes
- Generating misinformation

Focus: quality improvement, readability, authenticity

## Comparison with Commercial Tools

| Feature | This Skill | Commercial Tools |
|---------|-----------|-----------------|
| **Approach** | Meaning preservation | Detection evasion |
| **Interaction** | Interactive dialogue | One-click black box |
| **Languages** | Language-specific optimization | Generic multilingual |
| **Word limits** | Unlimited | 125-300 words free |
| **Transparency** | Explains changes | Black box |
| **Cost** | Free (uses Claude) | $10-60/month |
| **Quality focus** | Professional improvement | Bypass AI detectors |
| **Use case** | Professional writing | Academic cheating |

## Real-World Workflows

### Workflow 1: Blog Post Refinement
```bash
# Draft article with AI assistance
# Save to draft.md

# Interactive humanization (asks questions about audience, tone)
/de-ai --file draft.md --register essay

# Review output, iterate on specific sections if needed
/de-ai --text "[problematic paragraph]" --interactive false --explain true
```

### Workflow 2: Russian Business Email
```bash
# AI-generated Russian email in email.md
/de-ai --file email.md --language ru --register personal

# Remove канцелярит, make conversational
# Output preserves facts but sounds human
```

### Workflow 3: Technical Documentation
```bash
# AI-generated docs need humanization but must preserve accuracy
/de-ai --file api-docs.md --register technical --interactive true

# Claude asks: "Must preserve technical terms exactly?"
# You confirm: "Yes, only humanize explanations"
```

### Workflow 4: Multilingual Marketing
```bash
# Process same content in multiple languages
/de-ai --file campaign-en.md --language en --register personal
/de-ai --file campaign-ru.md --language ru --register personal
/de-ai --file campaign-de.md --language de --register personal

# Each gets language-specific optimization
```

## Common AI Vocabulary Removed

### Universal (Any Language)
- crucial, transformative, robust, comprehensive
- delve, underscore, paradigm, foster, navigate
- landscape, realm, leverage, synergy, holistic
- "it is important to note", "let's explore", "the key is"

### Russian Specific
- важно отметить, следует подчеркнуть, необходимо учитывать
- в современном мире, в конечном счете, в целом
- данный, указанный, вышеуказанный
- комплексный, инновационный, эффективный
- Excessive деепричастия/причастия

### German Specific
- Es ist wichtig zu beachten, Man sollte bedenken
- Im Hinblick auf, Vor diesem Hintergrund, Darüber hinaus
- umfassend, nachhaltig, ganzheitlich, zielgerichtet
- Excessive Nominalstil and Schachtelsätze

### English Specific
- "in order to", "the fact that", "in today's world"
- "here's the thing", "it's worth noting"
- Over-use of "however", "moreover", "furthermore"

## Tips for Best Results

1. **Provide context** - Let interactive mode ask questions
2. **Specify language** - Gets better optimization
3. **Match register** - Technical vs. personal needs different treatment
4. **Review output** - Always read and refine the result
5. **Use explain mode** - Learn what makes text sound AI-generated
6. **Iterate** - Run multiple times on problem sections
7. **Preserve facts first** - If unsure, use interactive mode to clarify constraints
8. **Test both modes** - Interactive for important content, quick for drafts

## Technical Details

**Built on:**
- Claude Sonnet 4.5
- Linguistic research (2023-2026)
- Multi-language NLP patterns
- Professional writing best practices

**Performance:**
- No word limits
- Processes full documents
- Language-aware transformations
- Context-preserving changes

## Troubleshooting

### "Text already reads as human"
**Issue**: Skill reports no changes needed
**Solution**: Text may already be well-written. Try `--explain true` to see if any minor AI tells were found.

### Output too conservative
**Issue**: Not enough changes made
**Solution**: Use `--interactive false` for more aggressive humanization, or specify lower formality in interactive questions.

### Output too aggressive
**Issue**: Changes feel excessive or meaning unclear
**Solution**: Use interactive mode, specify "preserve technical accuracy" when asked about constraints.

### Language not detected correctly
**Issue**: Wrong language optimizations applied
**Solution**: Explicitly specify `--language ru/de/en/es/fr`

### Register mismatch
**Issue**: Tone doesn't match content type
**Solution**: Specify `--register technical/academic/personal/essay/critique/narrative`

## FAQ

**Q: Will this bypass AI detectors?**
A: Not the goal. Focus is quality improvement. Detection evasion is unreliable since detectors use different models.

**Q: Is this for academic cheating?**
A: No. Intended for professional writing improvement, not hiding authorship. Use ethically.

**Q: Can I use for commercial content?**
A: Yes. MIT license allows commercial use. Improves AI-assisted professional writing.

**Q: Does it work with non-English languages?**
A: Yes. Optimized for Russian, German, English, Spanish, French with language-specific patterns.

**Q: Will facts be preserved?**
A: Yes. Meaning preservation is priority #1. Interactive mode asks about constraints.

**Q: How is this different from QuillBot/Undetectable.ai?**
A: They focus on detection evasion (often losing meaning). This focuses on quality and authenticity.

**Q: Can I process long documents?**
A: Yes. No word limits unlike commercial tools (125-300 word limits common).

**Q: What if output needs refinement?**
A: Run again on specific sections, use explain mode to understand changes, or provide more context in interactive mode.

**Q: Does it add new information?**
A: No. Never invents facts. Only rewrites existing content more authentically.

**Q: Can I see what was changed?**
A: Yes. Use `--explain true` to get bullet list of AI tells removed.

## Version History

- **1.0.0** (2026-02-03): Initial release
  - Interactive context gathering
  - Russian, German, English, Spanish, French optimization
  - Meaning preservation focus
  - Transparent change explanation
  - 6-level AI tell diagnosis
  - Register-aware humanization

## Related Resources

- Original prompt: `Claude-Drafts/20260130-ai-writing-de-ai-prompt.md`
- Research: `ai-research/20260130-ai-writing-de-ai-research.md`
- Commercial tool analysis: `ai-research/20260203-de-ai-writing-tools-landscape-2026.md`
- Linguistic patterns: `AI Text Generation Patterns.md`

## Contributing

Suggestions for improvement:
- Additional language support
- New register types
- Better detection patterns
- Quality improvements

## License

MIT License - Free for personal and commercial use
