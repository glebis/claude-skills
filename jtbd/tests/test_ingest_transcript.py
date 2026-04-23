"""Tests for ingest_transcript.py — transcript parsing, field mapping,
switch force detection, quote extraction, and confidence scoring."""

import sys
import os

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from ingest_transcript import (
    split_into_chunks,
    _score_chunk,
    map_field,
    map_switch_force,
    extract_quotes,
    identify_gaps,
    ingest,
    SITUATION_PHRASES,
    MOTIVATION_PHRASES,
    OUTCOME_PHRASES,
    PAIN_PHRASES,
    WORKAROUND_PHRASES,
    PUSH_PHRASES,
    PULL_PHRASES,
    HABIT_PHRASES,
    ANXIETY_PHRASES,
)


# ── Sample transcripts ──────────────────────────────────────────────

QA_TRANSCRIPT = """Q: Tell me about the problem you're facing.
A: Every time I need to generate a report, I have to manually copy data from three different spreadsheets. It's incredibly frustrating and I waste at least two hours every week on it.

Q: What are you trying to achieve?
A: I want a single dashboard so that I can see all metrics in one place. Right now I use Excel and it's painful.

Q: What worries you about switching?
A: I'm worried that the team won't adopt a new tool. Last time we tried something new, it was a disaster.

Q: What would the ideal solution look like?
A: I wish I could just click a button and have everything updated. Imagine if I never had to touch a spreadsheet again. Finally, I could focus on actual analysis."""

SPEAKER_TRANSCRIPT = """Interviewer: What brought you here today?
Sarah: When our team grew past 10 people, the old process broke. I need a way to track everyone's tasks without manually checking in.

Interviewer: How do you handle it now?
Sarah: We currently use a shared Google Sheet. I've been using it for years but it's terrible. Drives me crazy.

Interviewer: What's your biggest fear about changing?
Sarah: I'm afraid the team won't learn the new system. What if we lose data during migration?"""

PARAGRAPH_TRANSCRIPT = """The problem started last week when we had three client calls back to back. I was trying to find the notes from previous meetings but everything was scattered across email, Slack, and random documents.

I want a single place where all meeting notes live. I need to search across all of them quickly. The goal is to never lose context between calls.

The worst part is that I waste at least 30 minutes before every call just hunting for old notes. It's frustrating and makes me look unprepared. I can't stand it.

Right now I use a combination of Apple Notes and Google Docs. I copy and paste between them manually. It's a terrible workaround but I've been using it for years."""


# ── Chunk splitting tests ────────────────────────────────────────────

class TestSplitIntoChunks:

    def test_qa_format(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        assert len(chunks) >= 4
        # Should detect Q and A as speakers
        speakers = {c["speaker"] for c in chunks}
        assert "Q" in speakers or "A" in speakers

    def test_speaker_format(self):
        chunks = split_into_chunks(SPEAKER_TRANSCRIPT)
        assert len(chunks) >= 4
        speakers = {c["speaker"] for c in chunks}
        assert "Interviewer" in speakers or "Sarah" in speakers

    def test_paragraph_format(self):
        chunks = split_into_chunks(PARAGRAPH_TRANSCRIPT)
        assert len(chunks) == 4
        # No speakers in paragraph mode
        assert all(c["speaker"] is None for c in chunks)

    def test_chunk_indices(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        indices = [c["index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_empty_text(self):
        chunks = split_into_chunks("")
        assert chunks == []

    def test_single_paragraph(self):
        chunks = split_into_chunks("Just one paragraph with no breaks.")
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Just one paragraph with no breaks."


# ── Scoring tests ────────────────────────────────────────────────────

class TestScoreChunk:

    def test_no_match(self):
        score = _score_chunk("The weather is nice today.", PAIN_PHRASES)
        assert score == 0.0

    def test_single_match(self):
        score = _score_chunk("This is really frustrating.", PAIN_PHRASES)
        assert 0.4 <= score <= 0.6

    def test_multiple_matches(self):
        score = _score_chunk(
            "I'm frustrated and it's a waste of time. The problem is painful.",
            PAIN_PHRASES,
        )
        assert score >= 0.7

    def test_case_insensitive(self):
        score = _score_chunk("I WANT this to work. I NEED it now.", MOTIVATION_PHRASES)
        assert score > 0.0

    def test_max_cap(self):
        # Even with many matches, score caps at 1.0
        text = "frustrated annoying waste problem struggle painful broken terrible"
        score = _score_chunk(text, PAIN_PHRASES)
        assert score <= 1.0


# ── Field mapping tests ─────────────────────────────────────────────

class TestFieldMapping:

    def test_situation_detected(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        result = map_field(chunks, SITUATION_PHRASES)
        assert result["confidence"] > 0.0
        assert result["source_chunk"] >= 0
        assert "every time" in result["text"].lower() or "right now" in result["text"].lower()

    def test_motivation_detected(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        result = map_field(chunks, MOTIVATION_PHRASES)
        assert result["confidence"] > 0.0
        assert "want" in result["text"].lower() or "need" in result["text"].lower()

    def test_outcome_detected(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        result = map_field(chunks, OUTCOME_PHRASES)
        assert result["confidence"] > 0.0
        assert "so that" in result["text"].lower() or "so i can" in result["text"].lower()

    def test_pain_detected(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        result = map_field(chunks, PAIN_PHRASES)
        assert result["confidence"] > 0.0
        assert "frustrat" in result["text"].lower() or "waste" in result["text"].lower()

    def test_workaround_detected(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        result = map_field(chunks, WORKAROUND_PHRASES)
        assert result["confidence"] > 0.0

    def test_no_match_returns_empty(self):
        chunks = [{"index": 0, "text": "Hello world.", "speaker": None}]
        result = map_field(chunks, PAIN_PHRASES)
        assert result["confidence"] == 0.0
        assert result["text"] == ""
        assert result["source_chunk"] == -1


# ── Switch force detection tests ─────────────────────────────────────

class TestSwitchForces:

    def test_push_detected(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        result = map_switch_force(chunks, PUSH_PHRASES)
        assert result["confidence"] > 0.0
        assert "frustrated" in result["text"].lower() or "every time" in result["text"].lower()

    def test_pull_detected(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        result = map_switch_force(chunks, PULL_PHRASES)
        assert result["confidence"] > 0.0
        assert "wish" in result["text"].lower() or "imagine" in result["text"].lower()

    def test_habit_detected(self):
        chunks = split_into_chunks(SPEAKER_TRANSCRIPT)
        result = map_switch_force(chunks, HABIT_PHRASES)
        assert result["confidence"] > 0.0

    def test_anxiety_detected(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        result = map_switch_force(chunks, ANXIETY_PHRASES)
        assert result["confidence"] > 0.0
        assert "worried" in result["text"].lower() or "last time we tried" in result["text"].lower()

    def test_no_force_match(self):
        chunks = [{"index": 0, "text": "The sky is blue.", "speaker": None}]
        result = map_switch_force(chunks, PUSH_PHRASES)
        assert result["confidence"] == 0.0
        assert result["text"] == ""


# ── Quote extraction tests ───────────────────────────────────────────

class TestQuoteExtraction:

    def test_extracts_pain_quotes(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        quotes = extract_quotes(chunks)
        assert len(quotes) > 0
        # Should find at least one quote with frustration language
        has_pain = any("frustrat" in q.lower() or "waste" in q.lower() for q in quotes)
        assert has_pain

    def test_no_duplicates(self):
        chunks = split_into_chunks(QA_TRANSCRIPT)
        quotes = extract_quotes(chunks)
        assert len(quotes) == len(set(quotes))

    def test_empty_transcript_no_quotes(self):
        quotes = extract_quotes([])
        assert quotes == []

    def test_preserves_verbatim(self):
        text = "I wish I could just click a button."
        chunks = [{"index": 0, "text": text, "speaker": None}]
        quotes = extract_quotes(chunks)
        assert any(text in q for q in quotes)


# ── Gap identification tests ─────────────────────────────────────────

class TestGapIdentification:

    def test_low_confidence_flagged(self):
        fields = {
            "situation": {"text": "context", "confidence": 0.8, "source_chunk": 0},
            "motivation": {"text": "", "confidence": 0.0, "source_chunk": -1},
        }
        gaps = identify_gaps(fields)
        assert len(gaps) == 1
        assert "motivation" in gaps[0]

    def test_all_high_confidence_no_gaps(self):
        fields = {
            "situation": {"text": "x", "confidence": 0.5, "source_chunk": 0},
            "motivation": {"text": "y", "confidence": 0.4, "source_chunk": 1},
        }
        gaps = identify_gaps(fields)
        assert gaps == []

    def test_threshold_at_03(self):
        fields = {
            "f1": {"text": "x", "confidence": 0.3, "source_chunk": 0},
            "f2": {"text": "y", "confidence": 0.29, "source_chunk": 1},
        }
        gaps = identify_gaps(fields)
        assert len(gaps) == 1
        assert "f2" in gaps[0]


# ── Full ingest integration tests ────────────────────────────────────

class TestIngest:

    def test_qa_transcript_full(self):
        result = ingest(QA_TRANSCRIPT)
        assert "fields" in result
        assert "switch_forces" in result
        assert "quotes" in result
        assert "gaps" in result

        # All 5 fields present
        assert set(result["fields"].keys()) == {
            "situation", "motivation", "outcome", "what_hurts", "current_workaround"
        }

        # All 4 switch forces present
        assert set(result["switch_forces"].keys()) == {
            "push", "pull", "habit", "anxiety"
        }

        # This transcript has strong signals, so most fields should map
        high_conf = sum(
            1 for f in result["fields"].values() if f["confidence"] >= 0.3
        )
        assert high_conf >= 3

    def test_speaker_transcript_full(self):
        result = ingest(SPEAKER_TRANSCRIPT)
        assert result["fields"]["what_hurts"]["confidence"] > 0.0
        assert result["switch_forces"]["habit"]["confidence"] > 0.0
        assert result["switch_forces"]["anxiety"]["confidence"] > 0.0

    def test_paragraph_transcript_full(self):
        result = ingest(PARAGRAPH_TRANSCRIPT)
        assert result["fields"]["motivation"]["confidence"] > 0.0
        assert result["fields"]["current_workaround"]["confidence"] > 0.0
        assert len(result["quotes"]) > 0

    def test_empty_transcript(self):
        result = ingest("")
        assert all(f["confidence"] == 0.0 for f in result["fields"].values())
        assert all(f["confidence"] == 0.0 for f in result["switch_forces"].values())
        assert result["quotes"] == []
        assert len(result["gaps"]) == 5

    def test_confidence_scores_bounded(self):
        result = ingest(QA_TRANSCRIPT)
        for f in result["fields"].values():
            assert 0.0 <= f["confidence"] <= 1.0
        for f in result["switch_forces"].values():
            assert 0.0 <= f["confidence"] <= 1.0

    def test_output_structure_matches_spec(self):
        result = ingest(QA_TRANSCRIPT)
        # Fields have text, confidence, source_chunk
        for f in result["fields"].values():
            assert "text" in f
            assert "confidence" in f
            assert "source_chunk" in f
        # Switch forces have text, confidence
        for f in result["switch_forces"].values():
            assert "text" in f
            assert "confidence" in f
        # Quotes is a list of strings
        assert isinstance(result["quotes"], list)
        # Gaps is a list of strings
        assert isinstance(result["gaps"], list)
