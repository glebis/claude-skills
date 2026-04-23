"""Voice transcript ingest — map transcript chunks to JTBD schema fields.

Reads a transcript file (plain text or markdown), splits it into chunks
(by speaker turn or paragraph), and maps chunks to JTBD schema fields
with confidence scores. Also extracts Switch forces and verbatim quotes.

See references/switch_forces.md "One-minute pass (transcript mode)" for
the phrase patterns to match.

Usage:
    python ingest_transcript.py <path_to_transcript>

Output: JSON proposal to stdout.
"""

import json
import re
import sys
from typing import Optional


# --- Phrase patterns for JTBD schema field detection ---

SITUATION_PHRASES = [
    "when ", "every time", "last week", "during ", "last month",
    "yesterday", "this morning", "the other day", "last time",
    "whenever ", "at work", "in the meeting", "on monday",
]

MOTIVATION_PHRASES = [
    "i want", "i need", "i wish", "looking for", "trying to",
    "i'd like", "i would like", "we want", "we need", "hoping to",
    "my goal", "the goal",
]

OUTCOME_PHRASES = [
    "so that", "in order to", "that way", "goal is",
    "so i can", "so we can", "which means", "which would",
    "the result", "end up with", "outcome",
]

PAIN_PHRASES = [
    "frustrated", "frustrating", "annoying", "annoyed",
    "waste", "wasted", "wasting", "problem", "struggle",
    "struggling", "painful", "pain", "broken", "terrible",
    "awful", "hate", "hated", "worst", "nightmare",
    "can't stand", "drives me crazy", "unbearable",
]

WORKAROUND_PHRASES = [
    "currently using", "right now i", "right now we",
    "we use", "i use", "spreadsheet", "manually",
    "workaround", "hack", "duct tape", "cobbled together",
    "excel", "google sheets", "slack", "email",
    "copy and paste", "by hand",
]

# --- Switch force phrase patterns (from switch_forces.md) ---

PUSH_PHRASES = [
    "tired of", "frustrated", "can't believe", "every time", "wasted",
    "sick of", "fed up", "annoyed", "broken", "failing",
]

PULL_PHRASES = [
    "i wish", "imagine if", "what if i could", "finally",
    "dream of", "would be amazing", "picture this",
    "wouldn't it be great",
]

HABIT_PHRASES = [
    "we currently", "right now i", "i've been using", "for years",
    "we always", "our process", "the way we do it",
    "we've always done", "muscle memory",
]

ANXIETY_PHRASES = [
    "worried", "afraid", "what if", "last time we tried",
    "the team won't", "risky", "scared", "concerned",
    "might break", "could go wrong", "not sure if",
]

# --- Strong signal phrases for verbatim quote extraction ---

QUOTE_SIGNAL_PHRASES = (
    PAIN_PHRASES[:6] + PUSH_PHRASES[:5] + PULL_PHRASES[:4]
    + ["i want", "i need", "i wish", "the problem is",
       "what kills me", "the worst part", "if only"]
)


def split_into_chunks(text: str) -> list[dict]:
    """Split transcript into chunks by speaker turns or paragraphs.

    Returns a list of dicts: {"index": int, "text": str, "speaker": str|None}
    """
    lines = text.strip().split("\n")
    chunks: list[dict] = []

    # Detect format: speaker-turn (Q:/A:, Speaker:, Name:) or paragraph
    speaker_pattern = re.compile(
        r"^(?:([A-Za-z][A-Za-z0-9 ]*?)\s*:|([QA])\s*:)\s*(.*)", re.IGNORECASE
    )

    # Try speaker-turn parsing first
    current_speaker: Optional[str] = None
    current_lines: list[str] = []
    found_speakers = False

    for line in lines:
        m = speaker_pattern.match(line)
        if m:
            found_speakers = True
            # Save previous chunk
            if current_lines:
                chunks.append({
                    "index": len(chunks),
                    "text": " ".join(current_lines).strip(),
                    "speaker": current_speaker,
                })
            current_speaker = m.group(1) or m.group(2)
            current_lines = [m.group(3).strip()] if m.group(3).strip() else []
        else:
            if line.strip():
                current_lines.append(line.strip())

    # Flush last speaker chunk
    if found_speakers and current_lines:
        chunks.append({
            "index": len(chunks),
            "text": " ".join(current_lines).strip(),
            "speaker": current_speaker,
        })

    if found_speakers and chunks:
        return chunks

    # Fallback: paragraph-based splitting (double newline or blank line)
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return [
        {"index": i, "text": p.strip(), "speaker": None}
        for i, p in enumerate(paragraphs)
        if p.strip()
    ]


def _score_chunk(text: str, phrases: list[str]) -> float:
    """Score how well a chunk matches a set of phrases. Returns 0.0-1.0."""
    text_lower = text.lower()
    matches = sum(1 for p in phrases if p in text_lower)
    if matches == 0:
        return 0.0
    # Scale: 1 match = 0.5, 2 = 0.7, 3 = 0.9, 4+ = 1.0
    return min(0.3 + matches * 0.2, 1.0)


def map_field(chunks: list[dict], phrases: list[str]) -> dict:
    """Find the best chunk for a given field. Returns mapping dict."""
    best_score = 0.0
    best_chunk = None
    best_index = -1

    for chunk in chunks:
        score = _score_chunk(chunk["text"], phrases)
        if score > best_score:
            best_score = score
            best_chunk = chunk["text"]
            best_index = chunk["index"]

    if best_chunk is None or best_score == 0.0:
        return {"text": "", "confidence": 0.0, "source_chunk": -1}

    return {
        "text": best_chunk,
        "confidence": round(best_score, 2),
        "source_chunk": best_index,
    }


def map_switch_force(chunks: list[dict], phrases: list[str]) -> dict:
    """Find the best chunk for a switch force. Returns mapping dict."""
    best_score = 0.0
    best_chunk = None

    for chunk in chunks:
        score = _score_chunk(chunk["text"], phrases)
        if score > best_score:
            best_score = score
            best_chunk = chunk["text"]

    if best_chunk is None or best_score == 0.0:
        return {"text": "", "confidence": 0.0}

    return {"text": best_chunk, "confidence": round(best_score, 2)}


def extract_quotes(chunks: list[dict]) -> list[str]:
    """Extract verbatim sentences that contain strong signal phrases."""
    quotes: list[str] = []
    seen: set[str] = set()

    for chunk in chunks:
        # Split chunk into sentences
        sentences = re.split(r"(?<=[.!?])\s+", chunk["text"])
        for sentence in sentences:
            s_lower = sentence.lower()
            for phrase in QUOTE_SIGNAL_PHRASES:
                if phrase in s_lower:
                    normalized = sentence.strip()
                    if normalized and normalized not in seen:
                        quotes.append(normalized)
                        seen.add(normalized)
                    break  # one match per sentence is enough

    return quotes


def identify_gaps(fields: dict) -> list[str]:
    """Return field names with confidence < 0.3 that need follow-up."""
    return [
        f"{name} (confidence: {info['confidence']})"
        for name, info in fields.items()
        if info["confidence"] < 0.3
    ]


def ingest(text: str) -> dict:
    """Main entry point: ingest transcript text and return JSON proposal."""
    chunks = split_into_chunks(text)

    if not chunks:
        return {
            "fields": {
                "situation": {"text": "", "confidence": 0.0, "source_chunk": -1},
                "motivation": {"text": "", "confidence": 0.0, "source_chunk": -1},
                "outcome": {"text": "", "confidence": 0.0, "source_chunk": -1},
                "what_hurts": {"text": "", "confidence": 0.0, "source_chunk": -1},
                "current_workaround": {"text": "", "confidence": 0.0, "source_chunk": -1},
            },
            "switch_forces": {
                "push": {"text": "", "confidence": 0.0},
                "pull": {"text": "", "confidence": 0.0},
                "habit": {"text": "", "confidence": 0.0},
                "anxiety": {"text": "", "confidence": 0.0},
            },
            "quotes": [],
            "gaps": [
                "situation (confidence: 0.0)",
                "motivation (confidence: 0.0)",
                "outcome (confidence: 0.0)",
                "what_hurts (confidence: 0.0)",
                "current_workaround (confidence: 0.0)",
            ],
        }

    fields = {
        "situation": map_field(chunks, SITUATION_PHRASES),
        "motivation": map_field(chunks, MOTIVATION_PHRASES),
        "outcome": map_field(chunks, OUTCOME_PHRASES),
        "what_hurts": map_field(chunks, PAIN_PHRASES),
        "current_workaround": map_field(chunks, WORKAROUND_PHRASES),
    }

    switch_forces = {
        "push": map_switch_force(chunks, PUSH_PHRASES),
        "pull": map_switch_force(chunks, PULL_PHRASES),
        "habit": map_switch_force(chunks, HABIT_PHRASES),
        "anxiety": map_switch_force(chunks, ANXIETY_PHRASES),
    }

    quotes = extract_quotes(chunks)
    gaps = identify_gaps(fields)

    return {
        "fields": fields,
        "switch_forces": switch_forces,
        "quotes": quotes,
        "gaps": gaps,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python ingest_transcript.py <path_to_transcript>",
              file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    result = ingest(text)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
