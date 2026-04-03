"""
Interactive mode handler - generates questions for ambiguous fields
"""

import json


def generate_questions_leadgen(extracted_data):
    """
    Generate clarifying questions for leadgen meeting based on extracted data.

    Returns:
        list: Question objects for AskUserQuestion tool
    """
    questions = []

    # Check follow-up scheduling
    followup = extracted_data.get('followup', {})
    if not followup.get('scheduled'):
        questions.append({
            "question": "Was a follow-up call scheduled with this lead?",
            "header": "Follow-up",
            "multiSelect": False,
            "options": [
                {"label": "Yes, scheduled", "description": "Follow-up call has a confirmed date/time"},
                {"label": "No, not scheduled", "description": "No specific follow-up arranged"},
                {"label": "Tentative", "description": "Follow-up discussed but not confirmed"}
            ]
        })

    # Check budget discussion
    ctx = extracted_data.get('client_context', {})
    if not ctx.get('budget'):
        questions.append({
            "question": "Was budget discussed during this call?",
            "header": "Budget",
            "multiSelect": False,
            "options": [
                {"label": "Yes, specific range", "description": "Client mentioned specific budget amount/range"},
                {"label": "Yes, vague", "description": "Budget mentioned but no specific numbers"},
                {"label": "Not discussed", "description": "Budget topic not covered"}
            ]
        })

    # Check decision makers
    if not ctx.get('decision_makers'):
        questions.append({
            "question": "Were decision makers identified in the conversation?",
            "header": "Decision makers",
            "multiSelect": False,
            "options": [
                {"label": "Yes, identified", "description": "Specific people/roles mentioned"},
                {"label": "Not clear", "description": "Decision process unclear"},
                {"label": "Not discussed", "description": "Topic not covered"}
            ]
        })

    # Always ask for confidence assessment
    questions.append({
        "question": "What's your confidence level in closing this deal?",
        "header": "Confidence",
        "multiSelect": False,
        "options": [
            {"label": "Very high (5/5)", "description": "Strong buying signals, ready to move forward"},
            {"label": "High (4/5)", "description": "Interested and engaged, likely to proceed"},
            {"label": "Medium (3/5)", "description": "Some interest but unclear commitment"},
            {"label": "Low (2/5)", "description": "Lukewarm response, significant barriers"},
            {"label": "Very low (1/5)", "description": "Poor fit or low interest"}
        ]
    })

    return questions


def generate_questions_partnership(extracted_data):
    """
    Generate clarifying questions for partnership meeting.

    Returns:
        list: Question objects for AskUserQuestion tool
    """
    questions = []

    # Check follow-up
    followup = extracted_data.get('followup', {})
    if not followup.get('scheduled'):
        questions.append({
            "question": "Was a follow-up meeting scheduled?",
            "header": "Follow-up",
            "multiSelect": False,
            "options": [
                {"label": "Yes, scheduled", "description": "Next meeting has confirmed date/time"},
                {"label": "No, not scheduled", "description": "No specific follow-up arranged"},
                {"label": "Action needed first", "description": "Waiting on actions before scheduling"}
            ]
        })

    # Check resource requirements
    ctx = extracted_data.get('context', {})
    if not ctx.get('resource_requirements'):
        questions.append({
            "question": "Were resource requirements discussed?",
            "header": "Resources",
            "multiSelect": False,
            "options": [
                {"label": "Yes, specific", "description": "Clear resource needs identified"},
                {"label": "Yes, general", "description": "High-level resource discussion"},
                {"label": "Not discussed", "description": "Resources not covered"}
            ]
        })

    # Always ask for fit assessment
    questions.append({
        "question": "How would you assess the partnership fit?",
        "header": "Fit",
        "multiSelect": False,
        "options": [
            {"label": "Strong fit", "description": "Aligned goals, clear value exchange, both motivated"},
            {"label": "Medium fit", "description": "Some alignment but gaps to address"},
            {"label": "Weak fit", "description": "Misaligned priorities or unclear value"}
        ]
    })

    return questions


def apply_answers_leadgen(extracted_data, answers):
    """
    Apply user answers to leadgen extracted data.

    Args:
        extracted_data: Original extraction from LLM
        answers: Dict of answers from AskUserQuestion

    Returns:
        dict: Updated extraction data
    """
    # Follow-up
    if 'followup' in answers:
        if answers['followup'] == 'Yes, scheduled':
            # Already has date from transcript or ask for specific date
            if not extracted_data.get('followup', {}).get('date'):
                extracted_data.setdefault('followup', {})['scheduled'] = True
                extracted_data['followup']['date'] = 'Date to be confirmed'
        else:
            extracted_data['followup'] = {'scheduled': False, 'date': None}

    # Budget
    if 'budget' in answers:
        if answers['budget'] in ['Yes, specific range', 'Yes, vague']:
            extracted_data.setdefault('client_context', {})['budget'] = answers['budget']

    # Decision makers
    if 'decision_makers' in answers:
        if answers['decision_makers'] == 'Yes, identified':
            if not extracted_data.get('client_context', {}).get('decision_makers'):
                extracted_data.setdefault('client_context', {})['decision_makers'] = ['Mentioned in call']

    # Confidence
    if 'confidence' in answers:
        confidence_map = {
            'Very high (5/5)': 5,
            'High (4/5)': 4,
            'Medium (3/5)': 3,
            'Low (2/5)': 2,
            'Very low (1/5)': 1
        }
        prob = confidence_map.get(answers['confidence'], 3)
        extracted_data.setdefault('deal_assessment', {})['probability'] = prob

    return extracted_data


def generate_questions_coaching(extracted_data):
    """
    Generate clarifying questions for coaching session.

    Returns:
        list: Question objects for AskUserQuestion tool
    """
    questions = []

    # Check follow-up
    followup = extracted_data.get('followup', {})
    if not followup.get('scheduled'):
        questions.append({
            "question": "Was a follow-up session scheduled?",
            "header": "Follow-up",
            "multiSelect": False,
            "options": [
                {"label": "Yes, scheduled", "description": "Next session has confirmed date/time"},
                {"label": "No, not scheduled", "description": "No specific follow-up arranged"},
                {"label": "Regular cadence", "description": "Follows existing recurring schedule"}
            ]
        })

    # Always ask for session depth assessment
    questions.append({
        "question": "How would you rate the depth of this session?",
        "header": "Depth",
        "multiSelect": False,
        "options": [
            {"label": "High", "description": "Breakthrough insights, deep emotional work"},
            {"label": "Medium", "description": "Good progress, some new understanding"},
            {"label": "Low", "description": "Surface-level, mostly check-in"}
        ]
    })

    return questions


def apply_answers_coaching(extracted_data, answers):
    """
    Apply user answers to coaching extracted data.
    """
    # Follow-up
    if 'followup' in answers:
        if answers['followup'] == 'Yes, scheduled':
            extracted_data.setdefault('followup', {})['scheduled'] = True
            if not extracted_data['followup'].get('date'):
                extracted_data['followup']['date'] = 'Date to be confirmed'
        elif answers['followup'] == 'Regular cadence':
            extracted_data.setdefault('followup', {})['scheduled'] = True
            extracted_data['followup']['date'] = 'Regular recurring schedule'
        else:
            extracted_data['followup'] = {'scheduled': False, 'date': None}

    # Depth
    if 'depth' in answers:
        depth_map = {
            'High': 'high',
            'Medium': 'medium',
            'Low': 'low'
        }
        depth = depth_map.get(answers['depth'], 'medium')
        extracted_data.setdefault('session_quality', {})['depth'] = depth

    return extracted_data


def apply_answers_partnership(extracted_data, answers):
    """
    Apply user answers to partnership extracted data.
    """
    # Follow-up
    if 'followup' in answers:
        if answers['followup'] == 'Yes, scheduled':
            extracted_data.setdefault('followup', {})['scheduled'] = True
            if not extracted_data['followup'].get('date'):
                extracted_data['followup']['date'] = 'Date to be confirmed'
        else:
            extracted_data['followup'] = {'scheduled': False, 'date': None}

    # Resources
    if 'resources' in answers:
        if answers['resources'] in ['Yes, specific', 'Yes, general']:
            extracted_data.setdefault('context', {}).setdefault('resource_requirements', []).append(
                'Resource requirements discussed'
            )

    # Fit
    if 'fit' in answers:
        fit_map = {
            'Strong fit': 'strong',
            'Medium fit': 'medium',
            'Weak fit': 'weak'
        }
        fit = fit_map.get(answers['fit'], 'medium')
        extracted_data.setdefault('assessment', {})['fit'] = fit

    return extracted_data
