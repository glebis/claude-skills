"""
Partnership/collaboration call processor
"""

import os
import json
import sys
from pathlib import Path
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from interactive import generate_questions_partnership, apply_answers_partnership


def process(transcript_content, mode='interactive', user_answers=None):
    """
    Process partnership/collaboration call transcript.

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

    prompt = f"""Analyze this partnership/collaboration call transcript and extract:

1. **Opportunity Overview**
   - What collaboration/partnership was discussed?
   - Main value proposition for each party

2. **Commitments & Actions** (with deadlines if mentioned)
   - Format: [DEADLINE: YYYY-MM-DD] Action item (Owner)
   - Include both parties' commitments

3. **Follow-up**
   - Next meeting scheduled? When?

4. **Partnership Context**
   - Strategic alignment points
   - Technical integration needs (if any)
   - Resource requirements
   - Potential challenges/concerns raised

5. **Opportunity Assessment**
   - Fit: strong/medium/weak
   - Readiness: both ready/needs work/unclear
   - Key success factors
   - Meeting sentiment: positive/neutral/negative with brief reason

Return as JSON:
{{
  "opportunity": {{
    "description": "...",
    "value_proposition": {{
      "our_side": "...",
      "their_side": "..."
    }}
  }},
  "commitments": [
    {{"action": "...", "owner": "...", "deadline": "YYYY-MM-DD or null"}}
  ],
  "followup": {{"scheduled": true/false, "date": "YYYY-MM-DD HH:MM timezone or null"}},
  "context": {{
    "strategic_alignment": ["..."],
    "technical_needs": ["... or empty list"],
    "resource_requirements": ["... or empty list"],
    "challenges": ["... or empty list"]
  }},
  "assessment": {{
    "fit": "strong/medium/weak",
    "readiness": "both ready/needs work/unclear",
    "success_factors": ["..."],
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
        data = apply_answers_partnership(data, user_answers)

    # Interactive mode: check if questions needed
    if mode == 'interactive' and not user_answers:
        questions = generate_questions_partnership(data)
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
    output.append("Partnership/Collaboration Call\n")

    # Opportunity overview
    opp = data.get('opportunity', {})
    if opp:
        output.append("### Opportunity")
        output.append(opp.get('description', 'N/A'))
        output.append("")

        vp = opp.get('value_proposition', {})
        if vp:
            output.append("**Value Proposition:**")
            if vp.get('our_side'):
                output.append(f"- *Our side:* {vp['our_side']}")
            if vp.get('their_side'):
                output.append(f"- *Their side:* {vp['their_side']}")
            output.append("")

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

    # Context
    ctx = data.get('context', {})
    if any(ctx.values()):
        output.append("### Partnership Context")

        if ctx.get('strategic_alignment'):
            output.append("**Strategic Alignment:**")
            for point in ctx['strategic_alignment']:
                output.append(f"- {point}")
            output.append("")

        if ctx.get('technical_needs'):
            output.append("**Technical Integration:**")
            for need in ctx['technical_needs']:
                output.append(f"- {need}")
            output.append("")

        if ctx.get('resource_requirements'):
            output.append("**Resource Requirements:**")
            for req in ctx['resource_requirements']:
                output.append(f"- {req}")
            output.append("")

        if ctx.get('challenges'):
            output.append("**Challenges/Concerns:**")
            for challenge in ctx['challenges']:
                output.append(f"- {challenge}")
            output.append("")

    # Assessment
    assess = data.get('assessment', {})
    if assess:
        output.append("### Opportunity Assessment")
        output.append(f"**Fit:** {assess.get('fit', 'unknown').capitalize()}")
        output.append(f"**Readiness:** {assess.get('readiness', 'unclear').capitalize()}")

        if assess.get('success_factors'):
            output.append("\n**Key Success Factors:**")
            for factor in assess['success_factors']:
                output.append(f"- {factor}")

        output.append("")
        sentiment = assess.get('sentiment', 'neutral').capitalize()
        reason = assess.get('sentiment_reason', '')
        output.append(f"**Sentiment:** {sentiment} - {reason}")

    return '\n'.join(output)
