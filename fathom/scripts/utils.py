#!/usr/bin/env python3
"""Fathom API client utilities."""

import os
import time
import requests
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

API_KEY = os.getenv('FATHOM_API_KEY')
BASE_URL = 'https://api.fathom.ai/external/v1'
RATE_LIMIT_DELAY = 1.0  # seconds between requests (60/min limit)

class FathomClient:
    """Client for Fathom API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or API_KEY
        if not self.api_key:
            raise ValueError("FATHOM_API_KEY not set")
        self.headers = {'X-Api-Key': self.api_key}
        self._last_request_time = 0

    def _rate_limit(self):
        """Ensure we don't exceed rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request to API."""
        self._rate_limit()
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def list_meetings(
        self,
        created_after: str = None,
        created_before: str = None,
        recorded_by: List[str] = None,
        include_transcript: bool = False,
        limit: int = 50
    ) -> List[dict]:
        """
        List meetings with optional filters.

        Args:
            created_after: ISO date string (YYYY-MM-DD)
            created_before: ISO date string (YYYY-MM-DD)
            recorded_by: List of email addresses
            include_transcript: Include full transcript in response
            limit: Max number of meetings to return

        Returns:
            List of meeting objects
        """
        params = {'include_transcript': str(include_transcript).lower()}
        if created_after:
            params['created_after'] = created_after
        if created_before:
            params['created_before'] = created_before
        if recorded_by:
            params['recorded_by[]'] = recorded_by

        meetings = []
        cursor = None

        while len(meetings) < limit:
            if cursor:
                params['cursor'] = cursor

            data = self._get('meetings', params)
            items = data.get('items', [])
            meetings.extend(items)

            cursor = data.get('next_cursor')
            if not cursor or not items:
                break

        return meetings[:limit]

    def get_meeting(self, recording_id: str, include_transcript: bool = True) -> dict:
        """Get a specific meeting by recording ID."""
        params = {'include_transcript': str(include_transcript).lower()}
        # Meeting details are in the list endpoint, filtered
        meetings = self._get('meetings', params)
        for meeting in meetings.get('items', []):
            if str(meeting.get('recording_id')) == recording_id or recording_id in meeting.get('url', ''):
                return meeting
        return None

    def get_summary(self, recording_id: str) -> str:
        """Get AI summary for a recording."""
        data = self._get(f'recordings/{recording_id}/summary')
        summary = data.get('summary', {})
        if isinstance(summary, dict):
            return summary.get('markdown_formatted', '')
        return str(summary) if summary else ''

    def get_transcript(self, recording_id: str) -> str:
        """Get full transcript for a recording."""
        data = self._get(f'recordings/{recording_id}/transcript')
        return data.get('markdown', data.get('transcript', ''))

    def get_today_meetings(self) -> List[dict]:
        """Get all meetings from today."""
        today = date.today().isoformat()
        return self.list_meetings(created_after=today, include_transcript=True)

    def get_meetings_since(self, since_date: str) -> List[dict]:
        """Get all meetings since a specific date."""
        return self.list_meetings(created_after=since_date, include_transcript=True)


def format_meeting_markdown(meeting: dict, summary: str = None, transcript: str = None) -> str:
    """
    Format a meeting as markdown for Obsidian.

    Args:
        meeting: Meeting object from API
        summary: Optional pre-fetched summary
        transcript: Optional pre-fetched transcript

    Returns:
        Markdown string
    """
    # Extract metadata
    title = meeting.get('meeting_title') or meeting.get('title', 'Untitled Meeting')
    recording_id = str(meeting.get('recording_id', ''))
    created = meeting.get('created_at', '')[:10]  # YYYY-MM-DD

    # Parse participants
    invitees = meeting.get('calendar_invitees', [])
    participants = [inv.get('name') or inv.get('email', '') for inv in invitees]

    # Calculate duration
    start = meeting.get('recording_start_time', '')
    end = meeting.get('recording_end_time', '')
    duration = ''
    if start and end:
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            delta = end_dt - start_dt
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes = remainder // 60
            duration = f"{hours:02d}:{minutes:02d}"
        except:
            pass

    # Get summary from meeting object if not provided
    if not summary:
        default_summary = meeting.get('default_summary', {})
        summary = default_summary.get('markdown', '')

    # Get transcript from meeting object if not provided
    if not transcript:
        transcript_data = meeting.get('transcript', [])
        if isinstance(transcript_data, list):
            transcript_lines = []
            for entry in transcript_data:
                speaker = entry.get('speaker', {}).get('name', 'Unknown')
                text = entry.get('text', '')
                transcript_lines.append(f"**{speaker}**: {text}")
            transcript = '\n\n'.join(transcript_lines)
        else:
            transcript = str(transcript_data)

    # Build action items
    action_items = meeting.get('action_items', [])
    action_items_md = ''
    if action_items:
        items = []
        for item in action_items:
            desc = item.get('description', '')
            assignee = item.get('assignee', {}).get('name', '')
            completed = item.get('completed', False)
            checkbox = '[x]' if completed else '[ ]'
            assignee_str = f" (@{assignee})" if assignee else ''
            items.append(f"- {checkbox} {desc}{assignee_str}")
        action_items_md = '\n'.join(items)

    # Build frontmatter
    frontmatter = f"""---
fathom_id: {recording_id}
title: "{title}"
date: {created}
participants: {participants}
duration: {duration}
fathom_url: {meeting.get('url', '')}
share_url: {meeting.get('share_url', '')}
---"""

    # Build document
    sections = [frontmatter, f"# {title}"]

    if summary:
        sections.append("## Summary")
        sections.append(summary)

    if action_items_md:
        sections.append("## Action Items")
        sections.append(action_items_md)

    if transcript:
        sections.append("## Transcript")
        sections.append(transcript)

    return '\n\n'.join(sections)


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def meeting_filename(meeting: dict) -> str:
    """Generate filename for a meeting."""
    title = meeting.get('meeting_title') or meeting.get('title', 'meeting')
    created = meeting.get('created_at', '')[:10].replace('-', '')
    slug = slugify(title)[:50]  # Limit length
    return f"{created}-{slug}.md"
