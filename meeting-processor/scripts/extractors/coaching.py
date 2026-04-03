"""
Coaching session processor - extracts coaching-specific information
"""

import os
import json
import sys
from pathlib import Path
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from interactive import generate_questions_coaching, apply_answers_coaching


def process(transcript_content, mode='interactive', user_answers=None):
    """
    Process coaching session transcript.

    Args:
        transcript_content: The transcript text
        mode: 'interactive' or 'batch'
        user_answers: Dict of answers from interactive mode

    Returns:
        str: Formatted markdown analysis
    """

    client = OpenAI(
        api_key=os.environ.get('CEREBRAS_API_KEY'),
        base_url="https://api.cerebras.ai/v1"
    )

    prompt = f"""Analyze this coaching/mentoring session transcript and extract:

1. **Key Insights** - Main realizations and discoveries (3-5 items)
   - What did the coachee learn or understand?

2. **Decisions Made** - Concrete choices and commitments
   - What was decided during the session?

3. **Action Items** - Specific next steps
   - Format: Action item (Owner) [urgency: high/medium/low]

4. **Session Themes** - Recurring topics and patterns (2-4 themes)

5. **Emotional Arc** - How energy/mood shifted during the session

6. **Coaching Techniques Used** - Methods the coach employed

7. **Follow-up**
   - Next session scheduled? When?

Return as JSON:
{{
  "insights": ["..."],
  "decisions": ["..."],
  "action_items": [
    {{"action": "...", "owner": "...", "urgency": "high/medium/low"}}
  ],
  "themes": ["..."],
  "emotional_arc": "...",
  "techniques": ["..."],
  "followup": {{"scheduled": true/false, "date": "YYYY-MM-DD HH:MM timezone or null"}},
  "session_quality": {{
    "engagement": "high/medium/low",
    "depth": "high/medium/low",
    "sentiment": "positive/neutral/negative",
    "sentiment_reason": "..."
  }}
}}

Transcript:
{transcript_content}
"""

    response = client.chat.completions.create(
        model="qwen-3-235b-a22b-instruct-2507",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    result_text = response.choices[0].message.content.strip()

    # Parse JSON response
    try:
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        data = json.loads(result_text)
    except json.JSONDecodeError:
        return f"**Error:** Could not parse analysis\n\n```\n{result_text}\n```"

    # Interactive mode: apply user answers if provided
    if mode == 'interactive' and user_answers:
        data = apply_answers_coaching(data, user_answers)

    # Interactive mode: check if questions needed
    if mode == 'interactive' and not user_answers:
        questions = generate_questions_coaching(data)
        if questions:
            return {
                'needs_interaction': True,
                'questions': questions,
                'partial_data': data
            }

    # Format output
    output = []

    output.append("### Type")
    output.append("Coaching Session\n")

    # Key Insights
    if data.get('insights'):
        output.append("### Key Insights")
        for insight in data['insights']:
            output.append(f"- {insight}")
        output.append("")

    # Decisions
    if data.get('decisions'):
        output.append("### Decisions Made")
        for decision in data['decisions']:
            output.append(f"- {decision}")
        output.append("")

    # Action Items
    if data.get('action_items'):
        output.append("### Action Items")
        for item in data['action_items']:
            urgency = f" [{item['urgency']}]" if item.get('urgency') else ""
            output.append(f"- {item['action']} ({item['owner']}){urgency}")
        output.append("")

    # Themes
    if data.get('themes'):
        output.append("### Session Themes")
        for theme in data['themes']:
            output.append(f"- {theme}")
        output.append("")

    # Emotional Arc
    if data.get('emotional_arc'):
        output.append("### Emotional Arc")
        output.append(data['emotional_arc'])
        output.append("")

    # Techniques
    if data.get('techniques'):
        output.append("### Coaching Techniques")
        for technique in data['techniques']:
            output.append(f"- {technique}")
        output.append("")

    # Follow-up
    if data.get('followup', {}).get('scheduled'):
        output.append("### Follow-up")
        output.append(f"Next session: {data['followup']['date']}\n")

    # Session Quality
    quality = data.get('session_quality', {})
    if quality:
        output.append("### Session Quality")
        output.append(f"**Engagement:** {quality.get('engagement', 'unknown').capitalize()}")
        output.append(f"**Depth:** {quality.get('depth', 'unknown').capitalize()}")
        sentiment = quality.get('sentiment', 'neutral').capitalize()
        reason = quality.get('sentiment_reason', '')
        output.append(f"**Sentiment:** {sentiment} - {reason}")

    return '\n'.join(output)
