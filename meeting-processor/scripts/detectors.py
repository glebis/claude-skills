"""
Meeting type detection using LLM analysis
"""

import os
from openai import OpenAI


def detect_meeting_type(transcript_content, interactive=True):
    """
    Detect meeting type from transcript content.

    Args:
        transcript_content: The transcript text
        interactive: If True and uncertain, will ask user via AskUserQuestion

    Returns:
        str: Meeting type identifier (leadgen, partnership, coaching, internal)
    """

    client = OpenAI(
        api_key=os.environ.get('CEREBRAS_API_KEY'),
        base_url="https://api.cerebras.ai/v1"
    )

    # Use Claude to classify
    prompt = f"""Analyze this meeting transcript and classify it into ONE of these types:

1. **leadgen** - Sales/business development call with potential client
   - Discussing services/products
   - Exploring client needs
   - Pricing/budget discussions
   - Follow-up scheduling

2. **partnership** - Collaboration/partnership discussion
   - Exploring joint opportunities
   - Discussing mutual benefits
   - Technical integration talks
   - Strategic alignment

3. **coaching** - Coaching or mentoring session
   - Personal development
   - Goal setting
   - Reflective questions
   - Action planning

4. **internal** - Internal team meeting
   - Project updates
   - Team coordination
   - Internal planning
   - Status reviews

Respond with ONLY the type identifier (leadgen/partnership/coaching/internal) and confidence (high/medium/low) in format:
TYPE: <type>
CONFIDENCE: <confidence>

Transcript excerpt (first 2000 chars):
{transcript_content[:2000]}
"""

    response = client.chat.completions.create(
        model="qwen-3-235b-a22b-instruct-2507",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content.strip()

    # Parse response
    lines = result.split('\n')
    meeting_type = None
    confidence = None

    for line in lines:
        if line.startswith('TYPE:'):
            meeting_type = line.split(':', 1)[1].strip().lower()
        elif line.startswith('CONFIDENCE:'):
            confidence = line.split(':', 1)[1].strip().lower()

    # If low confidence and interactive, could use AskUserQuestion here
    # For now, return best guess
    if meeting_type not in ['leadgen', 'partnership', 'coaching', 'internal']:
        meeting_type = 'leadgen'  # Default fallback

    return meeting_type
