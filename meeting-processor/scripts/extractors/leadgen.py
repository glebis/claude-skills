"""
Leadgen call processor - extracts sales-specific information
"""

import os
import json
import sys
from pathlib import Path
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from interactive import generate_questions_leadgen, apply_answers_leadgen


def process(transcript_content, mode='interactive', user_answers=None):
    """
    Process leadgen call transcript.

    Args:
        transcript_content: The transcript text
        mode: 'interactive' or 'batch'

    Returns:
        str: Formatted markdown analysis
    """

    client = OpenAI(
        api_key=os.environ.get('CEREBRAS_API_KEY'),
        base_url="https://api.cerebras.ai/v1"
    )

    prompt = f"""Analyze this leadgen/sales call transcript and extract:

1. **Commitments & Actions** (with deadlines if mentioned)
   - Format: [DEADLINE: YYYY-MM-DD] Action item (Owner)
   - Include both sides' commitments

2. **Follow-up**
   - Next meeting scheduled? When?

3. **Client Context**
   - Pain points mentioned
   - Budget discussed (if any)
   - Timeline mentioned
   - Decision makers identified

4. **Deal Assessment**
   - Stage: cold/warm/hot
   - Probability: 1-5 (your assessment)
   - Main blocker (if any)
   - Meeting sentiment: positive/neutral/negative with brief reason

Return as JSON:
{{
  "commitments": [
    {{"action": "...", "owner": "...", "deadline": "YYYY-MM-DD or null"}}
  ],
  "followup": {{"scheduled": true/false, "date": "YYYY-MM-DD HH:MM timezone or null"}},
  "client_context": {{
    "pain_points": ["..."],
    "budget": "... or null",
    "timeline": "... or null",
    "decision_makers": ["name/role"]
  }},
  "deal_assessment": {{
    "stage": "cold/warm/hot",
    "probability": 1-5,
    "blocker": "... or null",
    "sentiment": "positive/neutral/negative",
    "sentiment_reason": "..."
  }}
}}

Transcript:
{transcript_content}
"""

    response = client.chat.completions.create(
        model="qwen-3-235b-a22b-instruct-2507",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    result_text = response.choices[0].message.content.strip()

    # Parse JSON response
    try:
        # Extract JSON from markdown code blocks if present
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        data = json.loads(result_text)
    except json.JSONDecodeError:
        return f"**Error:** Could not parse analysis\n\n```\n{result_text}\n```"

    # Interactive mode: apply user answers if provided
    if mode == 'interactive' and user_answers:
        data = apply_answers_leadgen(data, user_answers)

    # Interactive mode: check if questions needed
    if mode == 'interactive' and not user_answers:
        questions = generate_questions_leadgen(data)
        if questions:
            # Return questions for Claude to ask
            return {
                'needs_interaction': True,
                'questions': questions,
                'partial_data': data
            }

    # Format output
    output = []

    output.append("### Type")
    output.append("Leadgen Call\n")

    # Commitments
    if data.get('commitments'):
        output.append("### Commitments & Actions")
        for item in data['commitments']:
            deadline = f"[DEADLINE: {item['deadline']}] " if item.get('deadline') else ""
            output.append(f"- {deadline}{item['action']} ({item['owner']})")
        output.append("")

    # Follow-up
    if data.get('followup', {}).get('scheduled'):
        output.append("### Follow-up")
        output.append(f"Next call: {data['followup']['date']}\n")

    # Client context
    ctx = data.get('client_context', {})
    if any(ctx.values()):
        output.append("### Client Context")

        if ctx.get('pain_points'):
            output.append("**Pain Points:**")
            for point in ctx['pain_points']:
                output.append(f"- {point}")
            output.append("")

        if ctx.get('budget'):
            output.append(f"**Budget:** {ctx['budget']}")
        if ctx.get('timeline'):
            output.append(f"**Timeline:** {ctx['timeline']}")
        if ctx.get('decision_makers'):
            output.append(f"**Decision Makers:** {', '.join(ctx['decision_makers'])}")
        output.append("")

    # Deal assessment
    assess = data.get('deal_assessment', {})
    if assess:
        output.append("### Deal Assessment")
        output.append(f"**Stage:** {assess.get('stage', 'unknown').capitalize()}")
        output.append(f"**Probability:** {assess.get('probability', '?')}/5")
        if assess.get('blocker'):
            output.append(f"**Main Blocker:** {assess['blocker']}")
        output.append("")
        sentiment = assess.get('sentiment', 'neutral').capitalize()
        reason = assess.get('sentiment_reason', '')
        output.append(f"**Sentiment:** {sentiment} - {reason}")

    return '\n'.join(output)
