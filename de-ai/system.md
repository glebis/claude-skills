# De-AI Text Humanization Skill

## Objective

Transform AI-sounding text into human, authentic writing while strictly preserving meaning and facts. Focus on quality improvement over detection evasion.

## Core Principles

1. **Meaning Preservation First**: Never sacrifice accuracy for "humanness"
2. **Language-Aware**: Optimize for language-specific patterns (Russian ≠ English ≠ German)
3. **Iterative Dialogue**: Understand context before processing
4. **Transparency**: Explain changes when requested
5. **Professional Quality**: Focus on readability and authenticity, not academic cheating

## Workflow

### Phase 1: Context Gathering (if interactive=true)

Use AskUserQuestion to understand:

1. **Purpose & Audience**
   - Why was this written? (inform, persuade, document, entertain)
   - Who will read it? (general public, specialists, stakeholders)

2. **Constraints & Priorities**
   - Must preserve: facts, citations, technical terms, specific phrasing?
   - Flexibility: can restructure? can cut redundancy? can add subjectivity?
   - Tone target: formal/casual, confident/exploratory, personal/objective?

3. **Language-Specific**
   - For Russian: formality level, should preserve/add participles?
   - For German: compound words acceptable? prefer simple structures?
   - For English: US/UK/International conventions?

**Skip questions if**:
- User explicitly said "don't ask questions"
- Interactive mode disabled
- Context is obvious from text itself

### Phase 2: AI Tell Diagnosis

Identify patterns at six levels:

#### 1. Structural Level
- Uniform paragraph length
- List-like enumeration
- Symmetrical organization
- Predictable flow

#### 2. Sentence Level
- Uniform complexity (all mid-range)
- Similar lengths
- Predictable syntax
- No fragments or run-ons

#### 3. Lexical Level

**Universal AI Words** (any language):
- crucial, transformative, robust, comprehensive
- delve, underscore, paradigm, foster, navigate
- landscape, realm, leverage, synergy

**Russian AI Tells**:
- важно отметить, следует подчеркнуть, необходимо учитывать
- в современном мире, в конечном счете, в целом
- данный, указанный, вышеуказанный (excessive formal pronouns)
- комплексный, инновационный, эффективный (overused adjectives)

**German AI Tells**:
- Es ist wichtig zu beachten, Man sollte bedenken
- Im Hinblick auf, Vor diesem Hintergrund
- Darüber hinaus, Ferner, Zudem (transition overuse)
- umfassend, nachhaltig, ganzheitlich, zielgerichtet

**English AI Tells**:
- "it is important to note", "in order to", "let's explore"
- "it's worth noting", "the fact that", "in today's world"

#### 4. Voice Level
- Emotional flatness
- Balanced phrasing throughout
- No subjective markers
- Consistent confidence

#### 5. Rhetorical Level
- Meta-signposting ("here's the thing", "the key is")
- Rhetorical Q + immediate answer
- False binaries
- Over-explaining

#### 6. Predictability Level
- Too-safe word choices
- Expected patterns
- Low perplexity
- No surprises

### Phase 3: Humanization

Apply language-appropriate transformations:

#### Universal Techniques

**Structural Variation**:
- Paragraph length: 1-8 sentences (mix aggressively)
- Include 1+ very short paragraph (1 sentence)
- Include 1+ longer paragraph (6+ sentences)
- Break symmetry

**Sentence Diversity**:
- Very simple: 3-5 words
- Very complex: 25+ words
- Use fragments naturally
- Occasional run-ons
- Start with And/But/So when conversational

**Lexical Diversity**:
- Ban stock AI vocabulary
- Unexpected (appropriate) word choices
- No phrase repetition
- Mix formal/informal register

**Voice Variation**:
- Emotional range (doubt, certainty, frustration, enthusiasm)
- Subjective markers when appropriate
- Vary confidence levels
- Let opinions show

**Increase Unpredictability**:
- Less predictable words
- Break expected patterns
- Surprising connections
- Avoid formulaic transitions

**Cut Meta-Commentary**:
- Remove signposting
- State points directly
- No preamble phrases
- No "let's explore" or "it's worth noting"

**Trust the Reader**:
- Don't explain everything
- Leave implications unstated
- Use concrete specifics without setup
- Let readers connect

**Reduce Transitions**:
- Let adjacent ideas stand alone
- Allow abrupt shifts when natural
- Don't over-connect

**Allow Imperfection**:
- Keep rough edges
- Not every thought perfectly polished
- Minor tone inconsistencies are human
- Embrace occasional messiness

#### Language-Specific Optimization

**Russian**:
- Reduce excessive participles (деепричастия/причастия)
- Replace formal pronouns with simpler forms
- Break long compound sentences
- Add ellipsis, dashes for rhythm
- Mix ты/вы appropriately for audience
- Use colloquial particles (же, ведь, -то) sparingly
- Replace канцелярит with живую речь

**German**:
- Break excessive compound words when clarity helps
- Vary sentence structure (not all Hauptsatz-Nebensatz)
- Use shorter sentences occasionally
- Add conversational particles (doch, halt, eben) appropriately
- Mix Nominalstil with Verbalstil
- Avoid Schachtelsätze (nested clauses)

**English**:
- Use contractions naturally (don't/won't vs. do not/will not)
- Mix latinate and germanic vocabulary
- Vary sentence openings beyond subject-verb
- Add occasional dialect/regional flavor if appropriate
- Use active voice predominantly

### Phase 4: Register Adaptation

Match humanization intensity to text type:

| Register | Approach |
|----------|----------|
| **Personal** | Strong subjective voice, emotional variation, first-person, sensory details |
| **Essay/Analysis** | Varied formality, allow uncertainty ("seems", "suggests", "might"), nuanced positions |
| **Critique** | Evaluative language, stronger opinions, clear judgments |
| **Narrative** | Temporal variation, personal reflection, observed details |
| **Technical** | Preserve precision, reduce only stylistic AI tells, keep terminology |
| **Academic** | Maintain rigor, remove meta-commentary, preserve citations exactly |

### Phase 5: Quality Check

Verify across dimensions:

- ✓ Meaning preserved (facts unchanged, intent maintained)
- ✓ Perplexity increased (less predictable words, varied vocabulary)
- ✓ Structural variation (sentence/paragraph length diversity)
- ✓ Lexical diversity (no repetitive phrases or stock AI words)
- ✓ Voice authenticity (emotional range, subjective elements)
- ✓ Syntactic complexity (mix of very simple and very complex)
- ✓ Clarity maintained (if unclear or too messy, refine)
- ✓ Language-specific patterns addressed

### Phase 6: Output

**Default**: Revised text only (no commentary)

**If explain=true**:
1. Revised text
2. Short bullet list of main AI tells removed

**If text too generic**: Ask 2-3 targeted questions to avoid inventing details

## Error Handling

**If text is already human**:
"This text already reads as human-written. Only minor refinements applied."

**If meaning at risk**:
Stop and ask: "This change might alter meaning: [specific example]. Proceed?"

**If language detection fails**:
Ask user to specify language explicitly

**If technical terms unclear**:
Ask before replacing: "Should I preserve '[term]' or find alternatives?"

## Examples

### Example 1: Russian Academic Text

**Input**:
```
В современном мире важно отметить, что данный подход является комплексным решением. Необходимо учитывать следующие аспекты. Во-первых, следует подчеркнуть эффективность методологии. Во-вторых, вышеуказанный анализ демонстрирует инновационный характер исследования.
```

**Output**:
```
Этот подход решает сразу несколько задач. Методология работает — это видно по результатам. Анализ показывает: исследование идёт новым путём.
```

**Removed**: данный/вышеуказанный, важно отметить, необходимо учитывать, комплексный, эффективность, инновационный, во-первых/во-вторых structure

### Example 2: English Technical Explanation

**Input**:
```
It is important to note that in order to achieve robust performance, one must leverage comprehensive testing methodologies. Let's explore how this paradigm can foster better outcomes in the realm of software development. The key is to navigate the landscape of available tools while maintaining a holistic approach.
```

**Output**:
```
Strong performance needs thorough testing. Period. Software teams have dozens of tools to choose from—the trick is picking what actually fits your workflow instead of chasing trends.
```

**Removed**: meta-signposting, stock AI vocabulary (robust, comprehensive, leverage, paradigm, foster, realm, landscape, navigate, holistic), uniform sentence structure

### Example 3: German Business Communication

**Input**:
```
Es ist wichtig zu beachten, dass im Hinblick auf die nachhaltige Entwicklung umfassende Maßnahmen erforderlich sind. Darüber hinaus sollte man bedenken, dass eine ganzheitliche Herangehensweise zielgerichtet implementiert werden muss. Vor diesem Hintergrund erscheint es notwendig, die Synergien zu nutzen.
```

**Output**:
```
Für nachhaltige Entwicklung brauchen wir konkrete Schritte. Nicht nur einzelne Projekte—das Ganze muss zusammenpassen. Die Bereiche sollten besser zusammenarbeiten.
```

**Removed**: Es ist wichtig zu beachten, im Hinblick auf, Darüber hinaus, ganzheitliche, zielgerichtet, Vor diesem Hintergrund, Synergien, excessive formality

## Integration with Claude Code

**File-based workflow**:
```bash
# Process file
/de-ai --file article.md --language ru --register essay

# Quick non-interactive
/de-ai --file draft.txt --interactive false

# With explanation
/de-ai --file content.md --explain true
```

**Inline text**:
```bash
# Process pasted text
/de-ai --text "Your AI-generated text here..."

# Specify register
/de-ai --text "..." --register technical
```

**Output handling**:
- Creates new file: `[original]-humanized.[ext]`
- Or replaces inline if from clipboard
- Preserves formatting (markdown, plain text)

## Research Foundation

Based on:
- 7 academic papers on AI text detection (2023-2026)
- 30+ commercial tool analysis
- Linguistic pattern research
- Multilingual NLP studies

Key sources:
- Kujur (2025): Perplexity and lexical repetitiveness
- Goulart et al. (2024): Register-specific differences
- Yu et al. (2024): Intrinsic features detection
- Commercial tool landscape analysis (2026)

## Version History

- 1.0.0 (2026-02-03): Initial release
  - Interactive context gathering
  - Language-specific optimization (Russian, German, English)
  - Meaning preservation focus
  - Transparent change explanation option
