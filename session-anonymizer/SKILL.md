---
name: session-anonymizer
description: Three-layer PII anonymization for session transcripts (therapy, coaching, consulting, mentoring). Runs Natasha (Russian NER), OpenAI Privacy Filter, and local LLM (Ollama) in sequence for maximum coverage. Fully local by default. This skill should be used when anonymizing session transcripts, notes, or any text containing client PII before AI analysis. Triggers on "anonymize", "redact PII", "anonymize session", "protect client data", "strip personal data", "anonymize transcript".
---

# Therapy Anonymizer

Three-layer PII detection and anonymization for therapy session transcripts. Supports Russian and English. Fully local by default — no data leaves the machine.

## Architecture

Three detection layers run in sequence, each catching what others miss:

| Layer | Tool | Catches | Size | Speed |
|-------|------|---------|------|-------|
| 1 | Natasha | Russian names, locations, organizations | 27 MB | instant |
| 2 | OpenAI Privacy Filter (opf) | Phones, accounts, addresses, emails | 2.8 GB | ~1.5s |
| 3 | Ollama LLM | Medications, dates, contextual IDs | 2.5-7 GB | ~10s |

Spans from all layers are merged, overlaps resolved, and a unified redacted output is produced.

## Prerequisites

```bash
pip install natasha setuptools pymorphy2-dicts-ru
pip install 'opf @ git+https://github.com/openai/privacy-filter.git'
ollama pull qwen3:4b
```

Each layer is optional — the script gracefully skips unavailable layers and warns.

## Usage

### Single file

```bash
python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py session.txt
```

### Stdin pipe

```bash
cat session.txt | python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py
```

### Batch processing

```bash
python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py --batch ~/sessions/ -o ~/sessions_clean/
```

### JSON report

```bash
python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py session.txt --json
```

### Pseudonyms instead of tags

```bash
python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py session.txt --pseudonyms
```

### Select layers / model

```bash
# Fast — Natasha only
python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py session.txt --layers natasha

# LLM only — maximum coverage
python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py session.txt --layers ollama --model gemma4:e2b
```

### Encrypt output (AES-256)

```bash
python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py session.txt -o clean.txt --encrypt "password"
```

## Invoking from Claude Code

To anonymize text already in context, pipe it through the script:

```bash
echo '<text>' | python3 ~/.claude/skills/therapy-anonymizer/scripts/anonymize.py --json
```

For files, pass the path directly. Always recommend manual review after automated anonymization.

## Limitations

- Contextual identifiers ("the only red-haired architect in Kostroma") are NOT detected by any automated tool
- OPF is English-focused — Russian coverage is partial
- Medications detected only by Layer 3 (requires Ollama)
- Does not assess re-identification risk from combinations of non-PII fields

## Guardrails

- NEVER send raw transcripts to cloud services
- Cloud verification only on already-anonymized text
- Always recommend manual review for therapy data
- Never log original PII values
