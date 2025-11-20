---
name: youtube-transcript
description: "Extract YouTube video transcripts with metadata and save as Markdown to Obsidian vault. Use this skill when the user requests downloading YouTube transcripts, converting YouTube videos to text, or extracting video subtitles. Does not download video/audio files, only metadata and subtitles."
---

# YouTube Transcript

## Overview

Extract YouTube video transcripts, metadata, and chapters using yt-dlp. Output formatted as Markdown with YAML frontmatter, saved to ~/Brains/brain/ (Obsidian vault).

## Quick Start

To extract a transcript from a YouTube video:

```bash
python scripts/extract_transcript.py <youtube_url>
```

Optional: Specify custom output filename:

```bash
python scripts/extract_transcript.py <youtube_url> custom_filename.md
```

## Output Format

### YAML Frontmatter

The generated Markdown includes comprehensive metadata:

- `title` - Video title
- `channel` - Channel name
- `url` - YouTube URL
- `upload_date` - Upload date (YYYY-MM-DD)
- `duration` - Video duration (HH:MM:SS)
- `description` - Video description (truncated to 500 chars)
- `tags` - Array of video tags
- `view_count` - View count
- `like_count` - Like count

### Body Structure

Transcript organized by video chapters (if available):

```markdown
## Chapter Title

**00:05:23** Transcript text for this segment.

**00:05:45** Next segment text.
```

If no chapters exist, all content appears under "## Transcript" heading.

Timestamps formatted as HH:MM:SS for consistency.

## Workflow

1. Extract metadata and subtitles using yt-dlp
2. Parse VTT subtitle format to extract timestamps and text
3. Group transcript segments by video chapters (if present)
4. Format as Markdown with YAML frontmatter
5. Save to ~/Brains/brain/ with sanitized filename based on video title
6. Clean up temporary subtitle files

## Deduplication

To remove duplicates from existing transcript files:

```bash
python scripts/deduplicate_transcript.py <markdown_file>
```

This removes transcript entries that are prefixes of subsequent entries (common in VTT files where subtitles accumulate).

## Requirements

Ensure yt-dlp is installed:

```bash
pip install yt-dlp
```

## Limitations

- Extracts subtitles in English first, falls back to Russian if English unavailable
- Requires video to have subtitles (auto-generated or manual)
- Does not download video or audio files
- Description truncated to 500 characters in frontmatter
