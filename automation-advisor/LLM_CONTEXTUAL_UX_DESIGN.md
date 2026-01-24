# Enhanced UX: LLM-Driven Contextual Suggestions for Automation Advisor

## Executive Summary

Transform the Automation Advisor from a linear questionnaire into an intelligent, adaptive conversation by using LLMs to generate real-time contextual suggestions. Users can type/speak freely while the system proactively offers relevant follow-ups, missing context prompts, and quick-click options.

**Key Principle**: Hybrid input (freeform + suggestions) reduces cognitive load while maintaining user control.

---

## 1. Core UX Pattern: Contextual Suggestion Chips

### Visual Design

```
┌─────────────────────────────────────────────────────────┐
│ What task are you considering automating?              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  I generate invoices for clients every...              │
│  ▏                                                      │
│                                                         │
│  ┌─ Suggested context to add: ─────────────────────┐   │
│  │                                                  │   │
│  │  [+] How often? (weekly/monthly)                │   │
│  │  [+] Which tools do you use?                    │   │
│  │  [+] How long does it take?                     │   │
│  │  [+] What industry are you in?                  │   │
│  │                                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  🎤 Voice input    💬 Continue typing    ✓ Next        │
└─────────────────────────────────────────────────────────┘
```

### Component Breakdown

**Suggestion Pills** (clickable chips):
- Appear below text input as user types/pauses
- Styled as outlined buttons with subtle animation
- Max 3-5 suggestions visible at once
- Color-coded by type:
  - Blue: Missing context questions
  - Green: Specific detail prompts
  - Purple: Industry/role-specific suggestions

**Interaction Flow**:
1. User types partial answer
2. After 800ms pause, LLM analyzes partial input
3. Suggestions fade in above text area
4. User can:
   - Click suggestion → appends to text or opens sub-question
   - Ignore → continue typing
   - Click "Next" → proceed with current answer

---

## 2. When LLM Generates Suggestions

### Trigger Points

| Trigger | Example | LLM Action |
|---------|---------|------------|
| **Pause (800ms)** | User stops typing mid-sentence | Analyze partial text, suggest completion or follow-up |
| **Vague language detected** | "I do reports" | Ask: "What kind of reports? For whom?" |
| **Missing critical dimension** | "Invoice generation weekly" | Prompt: "How long does each invoice take?" |
| **Industry keyword** | "patient intake" | Suggest: "HIPAA compliance concern?" |
| **Tool mentioned** | "using Excel" | Ask: "Manual data entry or formula-driven?" |

### LLM Prompt Template

```
You are analyzing a user's partial answer to: "{question}"

Current user input: "{partial_answer}"

Task: Extract what's MISSING for complete automation assessment.

Output format:
- suggestion_type: "missing_context" | "clarification" | "follow_up"
- chips: ["Chip text 1", "Chip text 2", "Chip text 3"]
- reasoning: "Why these suggestions matter"

Focus on:
- Frequency, time, tools, pain points, error impact, industry constraints
- Specific bottlenecks, not generic questions

Max 3 suggestions. Be concise.
```

---

## 3. Context Extraction by Question Type

### Question 1: "What task are you considering?"

**LLM extracts**:
- Industry/domain (healthcare, finance, marketing)
- Role (founder, ops manager, developer)
- Tools mentioned (Excel, CRM, API)
- Stakeholders (clients, team, regulators)

**Example suggestions**:
- User: "Client onboarding emails"
  - Chips: `[+] B2B or B2C?` `[+] How many clients/month?` `[+] Using templates?`

### Question 2: "How do you currently do this?"

**LLM extracts**:
- Manual steps vs. tool-assisted
- Data sources (files, databases, APIs)
- Handoffs (solo vs. team collaboration)
- Time per step

**Example suggestions**:
- User: "Copy data from spreadsheet into CRM"
  - Chips: `[+] Always same fields?` `[+] Error-prone step?` `[+] Batch or one-by-one?`

### Question 3: "What frustrates you most?"

**LLM extracts**:
- Repetition vs. complexity
- Time wasted
- Error recovery effort
- Context switching

**Example suggestions**:
- User: "Takes forever and I mess up formulas"
  - Chips: `[+] How often do errors happen?` `[+] Impact on customers?` `[+] Hard to debug?`

### Question 4: "Consequences of errors?"

**LLM extracts**:
- Customer impact (lost trust, revenue)
- Regulatory risk (HIPAA, GDPR)
- Internal cost (re-work hours)

**Example suggestions**:
- User: "Clients get wrong invoices"
  - Chips: `[+] Payment delays?` `[+] Lost clients?` `[+] Legal liability?`

---

## 4. Implementation Approach

### Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │─────▶│  Flask API   │─────▶│ Claude API  │
│  (Vue/React)│      │  /suggest    │      │  (Streaming)│
└─────────────┘      └──────────────┘      └─────────────┘
      ▲                     │                      │
      │                     │                      │
      │              ┌──────▼──────────┐           │
      └──────────────│  Suggestion     │◀──────────┘
                     │  Cache (Redis)  │
                     └─────────────────┘
```

### API Endpoint

**POST /api/suggest**

Request:
```json
{
  "session_id": "uuid",
  "question": "What task are you considering?",
  "partial_answer": "I generate invoices for",
  "context": {
    "phase": "start",
    "previous_answers": []
  }
}
```

Response:
```json
{
  "suggestions": [
    {
      "type": "missing_context",
      "text": "How often? (daily/weekly/monthly)",
      "append_to_input": false,
      "opens_subquestion": false
    },
    {
      "type": "clarification",
      "text": "Which clients? (new/existing/all)",
      "append_to_input": false
    },
    {
      "type": "tool_probe",
      "text": "Using QuickBooks or manual?",
      "append_to_input": false
    }
  ],
  "confidence": 0.85,
  "cache_hit": false
}
```

### Caching Strategy

```python
# Cache key: hash(question + partial_answer_normalized)
# TTL: 15 minutes
# Reduces API calls by ~60% for common patterns

CACHE_PATTERNS = {
    "invoice": ["frequency", "tool", "client_type", "error_impact"],
    "report": ["stakeholders", "data_sources", "update_frequency"],
    "email": ["recipients", "template_based", "personalization_level"]
}

def get_cached_suggestions(question, partial_answer):
    normalized = normalize_input(partial_answer)
    cache_key = f"suggest:{hash(question + normalized)}"

    # Check cache
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Generate via LLM
    suggestions = llm_generate_suggestions(question, partial_answer)

    # Cache for 15min
    redis.setex(cache_key, 900, json.dumps(suggestions))

    return suggestions
```

---

## 5. Streaming Suggestions (Advanced)

### Pattern: Suggestions Arrive Incrementally

Instead of waiting for all suggestions, stream them as LLM generates:

```javascript
// Frontend: Server-Sent Events (SSE)
const eventSource = new EventSource(`/api/suggest-stream?session_id=${sessionId}`);

eventSource.addEventListener('suggestion', (event) => {
  const chip = JSON.parse(event.data);

  // Append chip to UI with fade-in animation
  addSuggestionChip(chip);
});

eventSource.addEventListener('complete', () => {
  eventSource.close();
});
```

**Backend: Streaming Response**

```python
from anthropic import Anthropic

@app.route('/api/suggest-stream')
def suggest_stream():
    def generate():
        prompt = build_suggestion_prompt(session)

        with client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                # Parse JSON fragments
                if chip := extract_chip(text):
                    yield f"data: {json.dumps(chip)}\n\n"

        yield f"event: complete\ndata: {{}}\n\n"

    return Response(generate(), mimetype='text/event-stream')
```

**Benefits**:
- First suggestion appears in ~400ms (vs. 1200ms for full response)
- User sees "thinking" feedback
- Reduces perceived latency

---

## 6. Visual Examples (Text-Based Mockups)

### Example Flow: Invoice Generation

**Step 1: Initial Input**
```
┌─────────────────────────────────────────────┐
│ What task are you considering automating?  │
├─────────────────────────────────────────────┤
│                                             │
│  Invoice generation                         │
│  ▏                                          │
│                                             │
│  💡 Suggestions loading...                  │
└─────────────────────────────────────────────┘
```

**Step 2: Suggestions Appear (800ms later)**
```
┌─────────────────────────────────────────────┐
│ What task are you considering automating?  │
├─────────────────────────────────────────────┤
│                                             │
│  Invoice generation                         │
│  ▏                                          │
│                                             │
│  Missing context:                           │
│  [+] How often?          [+] Which tool?    │
│  [+] For how many clients?                  │
└─────────────────────────────────────────────┘
```

**Step 3: User Clicks Chip**
```
┌─────────────────────────────────────────────┐
│ What task are you considering automating?  │
├─────────────────────────────────────────────┤
│                                             │
│  Invoice generation weekly for 20 clients   │
│  ▏                                          │
│                                             │
│  Great! Now tell me:                        │
│  [+] Using QuickBooks?   [+] Manual entry?  │
└─────────────────────────────────────────────┘
```

### Example Flow: Report Creation

**User Types: "Monthly sales reports"**

Suggestions:
```
┌─────────────────────────────────────────────┐
│  [+] Who receives the report?               │
│  [+] How long to compile data?              │
│  [+] Using Excel/Google Sheets/BI tool?     │
└─────────────────────────────────────────────┘
```

**User Clicks: "How long to compile data?"**

Auto-expands:
```
┌─────────────────────────────────────────────┐
│  Monthly sales reports                      │
│                                             │
│  Time to compile:                           │
│  ○ Under 30 min   ○ 1-2 hours               │
│  ○ Half a day     ○ Full day                │
└─────────────────────────────────────────────┘
```

---

## 7. Prompt Engineering for Context Extraction

### System Prompt

```markdown
You are an automation advisor assistant analyzing user responses.

Your role: Extract MISSING critical information for automation decision-making.

Context dimensions to probe:
- **Frequency**: How often task is performed
- **Time**: Duration per instance
- **Tools**: Software/platforms used
- **Stakeholders**: Who's impacted (customers, team, regulators)
- **Error impact**: Consequences of mistakes
- **Pain points**: Specific bottlenecks or frustrations
- **Industry constraints**: HIPAA, GDPR, SOX, creative authenticity

Rules:
1. Generate 3-5 short, actionable suggestions
2. Focus on MISSING info, not repeating what user said
3. Use plain language, avoid jargon
4. Prioritize high-impact dimensions (error cost, frequency)
5. If industry detected (healthcare, finance), probe compliance

Output format:
{
  "suggestions": [
    {"text": "...", "type": "missing_context|clarification|follow_up"},
    ...
  ],
  "detected_context": {
    "industry": "...",
    "tools": [...],
    "frequency_hint": "..."
  }
}
```

### Example Prompt

```
Question: "What task are you considering automating?"
User input: "Client onboarding emails when someone signs up"

Extract missing context for automation decision.
```

**LLM Output**:
```json
{
  "suggestions": [
    {"text": "How many signups per week?", "type": "missing_context"},
    {"text": "Same email template or customized?", "type": "clarification"},
    {"text": "Using Mailchimp/SendGrid or manual?", "type": "tool_probe"},
    {"text": "B2B or B2C customers?", "type": "clarification"}
  ],
  "detected_context": {
    "industry": "SaaS/software",
    "tools": [],
    "frequency_hint": "event-triggered"
  }
}
```

---

## 8. Graceful Degradation

### Fallback When LLM Unavailable

```javascript
// Client-side fallback suggestions (static)
const FALLBACK_SUGGESTIONS = {
  "what_task": [
    "How often do you do this?",
    "Which tools do you use?",
    "How long does it take?"
  ],
  "how_done": [
    "Are there manual copy-paste steps?",
    "Do you use templates?",
    "Is it the same every time?"
  ],
  "frustrations": [
    "How much time does it waste?",
    "Do you make mistakes often?",
    "Is it repetitive or complex?"
  ]
};

function getSuggestions(question, partial_answer) {
  // Try LLM first
  try {
    return await fetch('/api/suggest', { ... });
  } catch (error) {
    // Fallback to static suggestions
    return FALLBACK_SUGGESTIONS[question_type];
  }
}
```

---

## 9. Performance Benchmarks

### Target Metrics

| Metric | Target | Current (Baseline) |
|--------|--------|-------------------|
| First suggestion appears | < 500ms | N/A (no suggestions) |
| Full suggestions loaded | < 1000ms | N/A |
| Cache hit rate | > 60% | N/A |
| User acceptance rate | > 40% | N/A |
| Median session time | 3-4 min | 5-6 min (manual typing) |

### A/B Test Hypotheses

1. **Suggestion timing**: 800ms pause vs. 1200ms vs. 1500ms
   - Hypothesis: 800ms feels responsive without being intrusive

2. **Chip count**: 3 chips vs. 5 chips vs. dynamic (1-5)
   - Hypothesis: 3-4 chips optimal (not overwhelming)

3. **Chip placement**: Above input vs. below vs. sidebar
   - Hypothesis: Below input (closer to thumb on mobile)

---

## 10. Code Pseudocode

### Frontend Component (React/Vue)

```javascript
// SuggestionChips.vue
<template>
  <div class="suggestion-container">
    <!-- Text input -->
    <textarea
      v-model="userInput"
      @input="debouncedSuggest"
      placeholder="Type your answer or click suggestions..."
    />

    <!-- Suggestion chips -->
    <transition-group name="fade" class="chips" v-if="suggestions.length">
      <button
        v-for="chip in suggestions"
        :key="chip.text"
        @click="handleChipClick(chip)"
        :class="`chip chip-${chip.type}`"
      >
        <span class="chip-icon">+</span>
        {{ chip.text }}
      </button>
    </transition-group>

    <!-- Voice input -->
    <button @click="startVoiceInput" class="voice-btn">
      🎤 Voice
    </button>
  </div>
</template>

<script>
import { ref, watch } from 'vue';
import { debounce } from 'lodash';

export default {
  props: ['question', 'sessionId'],
  setup(props) {
    const userInput = ref('');
    const suggestions = ref([]);
    const isLoading = ref(false);

    // Debounced suggestion fetcher
    const debouncedSuggest = debounce(async () => {
      if (userInput.value.length < 5) return; // Min 5 chars

      isLoading.value = true;

      const response = await fetch('/api/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: props.sessionId,
          question: props.question,
          partial_answer: userInput.value
        })
      });

      const data = await response.json();
      suggestions.value = data.suggestions;
      isLoading.value = false;
    }, 800); // 800ms pause

    // Handle chip click
    function handleChipClick(chip) {
      if (chip.append_to_input) {
        userInput.value += ' ' + chip.text;
      } else {
        // Emit event to parent to show sub-question
        emit('chip-selected', chip);
      }

      // Clear suggestions after click
      suggestions.value = [];
    }

    return {
      userInput,
      suggestions,
      isLoading,
      debouncedSuggest,
      handleChipClick
    };
  }
};
</script>

<style scoped>
.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  margin: 4px;
  border: 1px solid #4299e1;
  border-radius: 20px;
  background: transparent;
  color: #4299e1;
  cursor: pointer;
  transition: all 0.2s;
}

.chip:hover {
  background: #4299e1;
  color: white;
  transform: translateY(-2px);
}

.chip-missing_context { border-color: #4299e1; color: #4299e1; }
.chip-clarification { border-color: #48bb78; color: #48bb78; }
.chip-tool_probe { border-color: #9f7aea; color: #9f7aea; }

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
```

### Backend API Handler

```python
# server_web.py additions

from anthropic import Anthropic
import redis
import hashlib

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@app.route('/api/suggest', methods=['POST'])
def suggest_context():
    """Generate contextual suggestions for partial answer"""
    data = request.json
    session_id = data.get('session_id')
    question = data.get('question')
    partial_answer = data.get('partial_answer', '').strip()

    if len(partial_answer) < 5:
        return jsonify({"suggestions": []})

    # Check cache
    cache_key = f"suggest:{hashlib.md5((question + partial_answer).encode()).hexdigest()}"
    cached = redis_client.get(cache_key)

    if cached:
        return jsonify(json.loads(cached))

    # Generate suggestions via Claude
    prompt = f"""You are analyzing a user's partial answer to: "{question}"

Current user input: "{partial_answer}"

Task: Extract MISSING critical information for automation assessment.

Context dimensions:
- Frequency (daily/weekly/monthly)
- Time per instance (minutes/hours)
- Tools/platforms used
- Error impact (low/medium/high)
- Industry constraints (HIPAA, GDPR, etc.)

Output ONLY valid JSON:
{{
  "suggestions": [
    {{"text": "...", "type": "missing_context"}},
    {{"text": "...", "type": "clarification"}},
    {{"text": "...", "type": "tool_probe"}}
  ],
  "detected_context": {{
    "industry": "...",
    "tools": [...],
    "frequency_hint": "..."
  }}
}}

Max 4 suggestions. Be concise and actionable."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse JSON response
    result = json.loads(response.content[0].text)

    # Cache for 15 minutes
    redis_client.setex(cache_key, 900, json.dumps(result))

    return jsonify(result)
```

---

## 11. User Research Patterns

### Inspired by Real-World Patterns

**GitHub Copilot**:
- Ghost text (dimmed) for low-confidence suggestions
- Tab to accept, Esc to dismiss
- Syntax highlighting in ghost text (2025 update)

**Google Search Autocomplete**:
- Instant suggestions after 2-3 characters
- Keyboard navigation (arrow keys)
- Click or Enter to accept

**Claude Artifacts**:
- Proactive suggestions: "Would you like me to create X?"
- User approves/rejects before generation
- Keeps user in control

**Notion AI**:
- Floating toolbar with context-aware prompts
- "Continue writing", "Summarize", "Translate"
- Appears on text selection

### Key Learnings

1. **Timing is critical**: Post-pause suggestions more accepted than mid-typing
2. **Visual distinction**: Dimmed/outlined UI signals "suggestion, not command"
3. **Escape hatch**: Always allow "ignore and continue"
4. **Feedback loop**: Track accept/reject for model improvement

---

## 12. Next Steps

### Phase 1: MVP (Week 1-2)
- [ ] Build `/api/suggest` endpoint with Claude integration
- [ ] Add suggestion chips to freeform questions
- [ ] Implement 800ms debounce trigger
- [ ] Add static fallback suggestions

### Phase 2: Optimization (Week 3-4)
- [ ] Add Redis caching layer
- [ ] Implement streaming suggestions (SSE)
- [ ] A/B test pause timing (800ms vs. 1200ms)
- [ ] Track acceptance rates

### Phase 3: Advanced Features (Week 5-6)
- [ ] Industry-specific suggestion templates
- [ ] Multi-language support
- [ ] Voice input integration with suggestions
- [ ] User feedback loop (upvote/downvote chips)

---

## 13. Success Metrics

### Primary KPIs
- **Suggestion acceptance rate**: > 40%
- **Time to complete questionnaire**: Reduce by 30% (from 5-6min to 3-4min)
- **User satisfaction**: "Felt helpful, not intrusive" > 80%

### Secondary Metrics
- Cache hit rate: > 60%
- LLM API cost per session: < $0.02
- Mobile completion rate: > 85%

---

## Related Documents

- [Automation Decision Matrix](/Users/glebkalinin/Brains/brain/Automation Decision Matrix.md)
- [Current Web Server Guide](/Users/glebkalinin/Brains/brain/.claude/skills/automation-advisor/WEB_SERVER_GUIDE.md)
- [Prompt Engineering Guide](/Users/glebkalinin/Brains/brain/.claude/skills/automation-advisor/prompt.md)

---

## Sources

- [Responsible use of GitHub Copilot inline suggestions - GitHub Docs](https://docs.github.com/en/copilot/responsible-use/copilot-code-completion)
- [Inline suggestions from GitHub Copilot in VS Code](https://code.visualstudio.com/docs/copilot/ai-powered-suggestions)
- [Evolving GitHub Copilot's next edit suggestions through custom model training - The GitHub Blog](https://github.blog/ai-and-ml/github-copilot/evolving-github-copilots-next-edit-suggestions-through-custom-model-training/)
- [LLM Design Patterns: Part 1 - Re-Stating](https://www.uxforai.com/p/llm-design-patterns-re-stating-auto-complete-talk-back-suggestions-nest-steps-regen-tweaks-and-guard)
- [Developer Interaction Patterns with Proactive AI: A Five-Day Field Study](https://arxiv.org/html/2601.10253)
- [Patterns for Building LLM-based Systems & Products](https://eugeneyan.com/writing/llm-patterns/)
- [Real-Time Feedback Techniques for LLM Optimization](https://latitude-blog.ghost.io/blog/real-time-feedback-techniques-for-llm-optimization/)
