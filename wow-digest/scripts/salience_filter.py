#!/usr/bin/env python3
"""Cheap salience filter: drop obvious noise before expensive WOW scoring.

Removes marketing, payment confirmations, holiday greetings, and other
patterns from email-rules.md. Permissive — false positives OK.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Patterns that signal noise — matched case-insensitively against source_name + title + snippet
NOISE_SENDER_PATTERNS = [
    r"noreply@.*\.paypal\.",
    r"no-reply@revolut\.com",
    r"billing@zoom\.us",
    r"noreply@.*bybit\.com",
    r"no-reply@.*wise\.com",
    r"noreply@.*vodafone",
    r"@news\.paypal\.",
]

NOISE_TITLE_PATTERNS = [
    r"receipt for your payment",
    r"payment processed",
    r"withdrawal success",
    r"withdrawals have been sent",
    r"С Днем Победы",
    r"С Днём Победы",
    r"frohe weihnachten",
    r"happy holidays",
    r"your? (?:order|shipment|delivery)",
    r"bereit für ihren",
    r"mehr sicherheit mit passkeys",
    r"remember the tech you were dreaming",
]

NOISE_SOURCE_TYPES = {
    "email": NOISE_SENDER_PATTERNS,
}


def is_noise(candidate):
    """Return True if candidate matches known noise patterns."""
    source = candidate.get("source_name", "").lower()
    title = candidate.get("title", "").lower()
    snippet = candidate.get("snippet", "").lower()

    for pattern in NOISE_SENDER_PATTERNS:
        if re.search(pattern, source, re.IGNORECASE):
            return True

    for pattern in NOISE_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return True
        if re.search(pattern, snippet[:200], re.IGNORECASE):
            return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Filter noise from candidates")
    parser.add_argument("--input", "-i", required=True, help="Input JSONL")
    parser.add_argument("--output", "-o", required=True, help="Output JSONL (filtered)")
    args = parser.parse_args()

    candidates = []
    with open(args.input) as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))

    filtered = [c for c in candidates if not is_noise(c)]
    dropped = len(candidates) - len(filtered)

    with open(args.output, "w") as f:
        for c in filtered:
            f.write(json.dumps(c) + "\n")

    print(f"Salience filter: {len(candidates)} → {len(filtered)} ({dropped} dropped)", file=sys.stderr)


if __name__ == "__main__":
    main()
