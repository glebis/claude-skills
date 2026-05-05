#!/usr/bin/env python3
"""Three-layer PII anonymization for therapy transcripts.

Layer 1: Natasha (Russian NER — names, locations, orgs)
Layer 2: OpenAI Privacy Filter (phones, accounts, addresses)
Layer 3: Local LLM via Ollama (medications, dates, contextual IDs)

All layers run locally by default. No data leaves the machine.
"""

import argparse
import json
import subprocess
import sys
import os
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Span:
    start: int
    end: int
    text: str
    label: str
    source: str
    confidence: float = 1.0


@dataclass
class AnonymizationResult:
    original_length: int
    redacted_text: str
    spans: list
    stats: dict
    warnings: list


def run_natasha(text: str) -> list[Span]:
    """Layer 1: Natasha NER for Russian text."""
    try:
        from natasha import Segmenter, NewsEmbedding, NewsNERTagger, Doc
    except ImportError:
        return []

    segmenter = Segmenter()
    emb = NewsEmbedding()
    ner_tagger = NewsNERTagger(emb)

    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)

    label_map = {"PER": "PERSON", "LOC": "LOCATION", "ORG": "ORG"}
    spans = []
    for span in doc.spans:
        mapped = label_map.get(span.type, span.type)
        spans.append(Span(
            start=span.start, end=span.stop,
            text=text[span.start:span.stop],
            label=mapped, source="natasha"
        ))
    return spans


def run_opf(text: str) -> list[Span]:
    """Layer 2: OpenAI Privacy Filter."""
    try:
        result = subprocess.run(
            ["opf", "redact", "--device", "cpu", "--format", "json",
             "--no-print-color-coded-text", "--json-indent", "0"],
            input=text, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return []

        output = result.stdout.strip()
        json_start = output.find("{")
        if json_start == -1:
            return []
        try:
            data = json.loads(output[json_start:])
        except json.JSONDecodeError:
            return []

        spans = []
        for s in data.get("detected_spans", []):
            spans.append(Span(
                start=s["start"], end=s["end"],
                text=s["text"], label=s["label"].upper(),
                source="opf"
            ))
        return spans
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return []


def run_ollama(text: str, model: str = "qwen2.5:3b") -> list[Span]:
    """Layer 3: Local LLM via Ollama HTTP API for medications, dates, contextual IDs."""
    import re
    try:
        import urllib.request

        prompt = 'Extract ALL PII. Include MEDICATIONS with dosages. Return ONLY JSON array [{\"text\":\"...\",\"type\":\"PERSON|LOCATION|ORG|PHONE|DATE|ADDRESS|MEDICATION|ID\"}]. No explanations.\n\nText: ' + text

        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 2048}
        }).encode()

        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())

        output = data.get("message", {}).get("content", "")
        output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL)

        match = re.search(r'\[.*\]', output, re.DOTALL)
        if not match:
            return []

        entities = json.loads(match.group())
        spans = []
        for ent in entities:
            ent_text = ent.get("text", "")
            idx = text.find(ent_text)
            if idx == -1:
                for i in range(max(0, len(text) - len(ent_text) + 1)):
                    if text[i:i+len(ent_text)].lower() == ent_text.lower():
                        idx = i
                        break
            if idx == -1:
                for stem in [ent_text[:max(3, len(ent_text)-2)]]:
                    pos = text.lower().find(stem.lower())
                    if pos >= 0:
                        end_pos = min(pos + len(ent_text) + 5, len(text))
                        word_end = text.find(" ", pos + len(stem))
                        if word_end == -1:
                            word_end = end_pos
                        idx = pos
                        ent_text = text[pos:word_end]
                        break
            if idx >= 0:
                spans.append(Span(
                    start=idx, end=idx + len(ent_text),
                    text=ent_text,
                    label=ent.get("type", "UNKNOWN"),
                    source="ollama",
                    confidence=0.85
                ))
        return spans
    except Exception as e:
        import sys
        print(f"Ollama error: {type(e).__name__}: {e}", file=sys.stderr)
        return []


def merge_spans(all_spans: list[Span]) -> list[Span]:
    """Merge overlapping spans, preferring higher-confidence or more specific labels."""
    if not all_spans:
        return []

    sorted_spans = sorted(all_spans, key=lambda s: (s.start, -(s.end - s.start)))
    merged = [sorted_spans[0]]

    for span in sorted_spans[1:]:
        prev = merged[-1]
        if span.start < prev.end:
            if span.end > prev.end:
                prev.end = span.end
                prev.text = prev.text  # keep original
            if span.confidence > prev.confidence:
                prev.label = span.label
                prev.source = span.source
        else:
            merged.append(span)

    return merged


def pseudonym_map(spans: list[Span], seed: str = "") -> dict[str, str]:
    """Generate consistent pseudonyms for detected entities."""
    names = ["Алексей", "Мария", "Дмитрий", "Елена", "Сергей", "Анна", "Павел", "Ольга"]
    cities = ["Город-А", "Город-Б", "Город-В", "Город-Г"]
    orgs = ["Организация-1", "Организация-2", "Организация-3"]

    mapping = {}
    name_idx = city_idx = org_idx = 0

    for span in spans:
        key = span.text.strip()
        if key in mapping:
            continue
        if span.label == "PERSON" or span.label == "PRIVATE_PERSON":
            mapping[key] = f"[{names[name_idx % len(names)]}]"
            name_idx += 1
        elif span.label in ("LOCATION", "ADDRESS", "PRIVATE_ADDRESS"):
            mapping[key] = f"[{cities[city_idx % len(cities)]}]"
            city_idx += 1
        elif span.label == "ORG":
            mapping[key] = f"[Организация-{org_idx + 1}]"
            org_idx += 1
        elif span.label in ("PHONE", "PRIVATE_PHONE"):
            mapping[key] = "[ТЕЛЕФОН]"
        elif span.label == "DATE" or span.label == "PRIVATE_DATE":
            mapping[key] = "[ДАТА]"
        elif span.label == "MEDICATION":
            mapping[key] = "[ПРЕПАРАТ]"
        elif span.label in ("ACCOUNT_NUMBER", "ID"):
            mapping[key] = "[ID-НОМЕР]"
        else:
            mapping[key] = f"[{span.label}]"
    return mapping


def redact(text: str, spans: list[Span], use_pseudonyms: bool = False) -> str:
    """Replace detected spans with placeholders or pseudonyms."""
    if use_pseudonyms:
        mapping = pseudonym_map(spans)

    result = []
    last_end = 0
    for span in sorted(spans, key=lambda s: s.start):
        result.append(text[last_end:span.start])
        if use_pseudonyms:
            key = span.text.strip()
            result.append(mapping.get(key, f"<{span.label}>"))
        else:
            result.append(f"<{span.label}>")
        last_end = span.end
    result.append(text[last_end:])
    return "".join(result)


def anonymize(text: str, layers: list[str] = None, model: str = "qwen2.5:3b",
              pseudonyms: bool = False) -> AnonymizationResult:
    """Run all anonymization layers and produce result."""
    if layers is None:
        layers = ["natasha", "ollama", "opf"]

    all_spans = []
    warnings = []

    if "natasha" in layers:
        natasha_spans = run_natasha(text)
        all_spans.extend(natasha_spans)
        if not natasha_spans:
            warnings.append("Natasha returned no entities — may not be installed")

    if "ollama" in layers:
        ollama_spans = run_ollama(text, model)
        all_spans.extend(ollama_spans)
        if not ollama_spans:
            warnings.append("Ollama returned no entities — is the model running?")
        elif "opf" in layers:
            try:
                import urllib.request
                urllib.request.urlopen(urllib.request.Request(
                    "http://localhost:11434/api/generate",
                    data=json.dumps({"model": model, "keep_alive": 0}).encode(),
                    headers={"Content-Type": "application/json"}
                ), timeout=5)
            except Exception:
                pass

    if "opf" in layers:
        opf_spans = run_opf(text)
        all_spans.extend(opf_spans)
        if not opf_spans:
            warnings.append("OPF returned no entities — may not be installed or model not downloaded")

    merged = merge_spans(all_spans)
    redacted_text = redact(text, merged, pseudonyms)

    stats = {}
    for span in merged:
        stats[span.label] = stats.get(span.label, 0) + 1

    warnings.append("Manual review recommended: contextual identifiers (unique life situations) cannot be detected automatically")

    return AnonymizationResult(
        original_length=len(text),
        redacted_text=redacted_text,
        spans=[asdict(s) for s in merged],
        stats=stats,
        warnings=warnings
    )


def encrypt_file(filepath: str, password: str) -> str:
    """AES-256 encrypt a file using openssl."""
    out_path = filepath + ".enc"
    result = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2",
         "-in", filepath, "-out", out_path, "-pass", f"pass:{password}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Encryption failed: {result.stderr}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Three-layer therapy transcript anonymizer")
    parser.add_argument("input", nargs="?", help="Input file (or stdin if omitted)")
    parser.add_argument("-o", "--output", help="Output file (stdout if omitted)")
    parser.add_argument("--layers", default="natasha,opf,ollama",
                        help="Comma-separated layers to run (default: natasha,opf,ollama)")
    parser.add_argument("--model", default="qwen3:4b", help="Ollama model (default: qwen3:4b)")
    parser.add_argument("--pseudonyms", action="store_true", help="Use consistent pseudonyms instead of tags")
    parser.add_argument("--json", action="store_true", help="Output full JSON report")
    parser.add_argument("--encrypt", metavar="PASSWORD", help="Encrypt output with AES-256")
    parser.add_argument("--batch", metavar="DIR", help="Process all .txt/.md files in directory")
    args = parser.parse_args()

    layers = [l.strip() for l in args.layers.split(",")]

    if args.batch:
        import glob
        files = glob.glob(os.path.join(args.batch, "*.txt")) + glob.glob(os.path.join(args.batch, "*.md"))
        out_dir = args.output or args.batch + "_anonymized"
        os.makedirs(out_dir, exist_ok=True)

        total_stats = {}
        for f in sorted(files):
            with open(f) as fh:
                text = fh.read()
            result = anonymize(text, layers, args.model, args.pseudonyms)
            out_file = os.path.join(out_dir, os.path.basename(f))
            with open(out_file, "w") as fh:
                fh.write(result.redacted_text)
            for k, v in result.stats.items():
                total_stats[k] = total_stats.get(k, 0) + v
            print(f"  {os.path.basename(f)}: {sum(result.stats.values())} entities", file=sys.stderr)

        print(json.dumps({"files": len(files), "output_dir": out_dir, "total_stats": total_stats}, indent=2, ensure_ascii=False))
        return

    if args.input:
        with open(args.input) as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result = anonymize(text, layers, args.model, args.pseudonyms)

    if args.json:
        output = json.dumps(asdict(result), indent=2, ensure_ascii=False)
    else:
        output = result.redacted_text

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        if args.encrypt:
            enc_path = encrypt_file(args.output, args.encrypt)
            print(f"Encrypted: {enc_path}", file=sys.stderr)
    else:
        print(output)

    print(f"\nEntities found: {result.stats}", file=sys.stderr)
    for w in result.warnings:
        print(f"⚠ {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
