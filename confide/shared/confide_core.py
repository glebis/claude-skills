#!/usr/bin/env python3
"""CONFIDE core — config, layered local PII detectors, span merge, redaction.

Shared by confide:anon and confide:red. Local-first: the deterministic regex layer and
redaction need no network; Natasha (RU NER) and the LLM layer load only if available.
Nothing here prints or returns raw PII to any caller that doesn't already have the text.
"""
import json
import os
import re
import urllib.request
from dataclasses import dataclass, asdict

CONFIG_PATH = os.path.expanduser("~/.config/confide/config.json")

DEFAULTS = {
    "engine": "ollama",
    "anon_model": "qwen2.5:3b",
    "red_attacker_model": "qwen2.5:3b",
    "languages": ["ru", "en"],
    "layers": ["regex", "natasha", "llm"],
    "redaction_style": "typed_placeholder",
    "privacy": {"local_only": True, "cloud_apis": False, "cloud_only_on_synthetic": True},
    "ollama_host": "http://localhost:11434",
}

# canonical PII types
TYPES = ["PERSON", "LOCATION", "ORG", "PHONE", "EMAIL", "URL", "ID", "DATE", "MEDICATION", "AGE", "PROFESSION"]


def load_config(path=CONFIG_PATH):
    """Return config merged over DEFAULTS (defaults win for missing keys)."""
    cfg = dict(DEFAULTS)
    try:
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k] = {**cfg[k], **v}
            else:
                cfg[k] = v
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return cfg


def write_config(cfg, path=CONFIG_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return path


@dataclass
class Span:
    start: int
    end: int
    text: str
    type: str
    source: str


# ----------------------------------------------------------------- regex layer
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_URL = re.compile(r"\bhttps?://[^\s)>\]]+", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\-\s().]{7,}\d)(?!\w)")
_ID = re.compile(r"\b\d{3,4}[- ]\d{3,4}[- ]\d{2,4}(?:[- ]\d{1,4})?\b")  # policy/SNILS/INN-like
_DATE_NUM = re.compile(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b")
_DATE_REL_EN = re.compile(r"\b(?:last|next|this)\s+(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\b|\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b", re.IGNORECASE)
_DATE_REL_RU = re.compile(r"\b\d{1,2}\s+(?:январ|феврал|март|апрел|ма[яй]|июн|июл|август|сентябр|октябр|ноябр|декабр)\w*\b", re.IGNORECASE)


def detect_regex(text):
    """Deterministic detectors — no network, no deps required."""
    spans = []
    for rx, typ in [(_EMAIL, "EMAIL"), (_URL, "URL"), (_PHONE, "PHONE"), (_ID, "ID"),
                    (_DATE_NUM, "DATE"), (_DATE_REL_EN, "DATE"), (_DATE_REL_RU, "DATE")]:
        for m in rx.finditer(text):
            s = m.group().strip()
            if typ == "PHONE" and sum(c.isdigit() for c in s) < 7:
                continue
            spans.append(Span(m.start(), m.start() + len(s), s, typ, "regex"))
    return spans


# ----------------------------------------------------------------- Natasha layer
def detect_natasha(text):
    """RU NER. Returns [] if natasha not installed."""
    try:
        from natasha import Segmenter, NewsEmbedding, NewsNERTagger, Doc
    except ImportError:
        return []
    seg, emb = Segmenter(), NewsEmbedding()
    doc = Doc(text); doc.segment(seg); doc.tag_ner(NewsNERTagger(emb))
    m = {"PER": "PERSON", "LOC": "LOCATION", "ORG": "ORG"}
    return [Span(sp.start, sp.stop, text[sp.start:sp.stop], m.get(sp.type, sp.type), "natasha")
            for sp in doc.spans]


# ----------------------------------------------------------------- LLM layer (engine-agnostic)
_LLM_PROMPT = ("Extract ALL personally identifying information including quasi-identifiers "
    "(medications, ages, professions, contextual dates/names). Return ONLY a JSON array of "
    '[{"text":"...","type":"PERSON|LOCATION|ORG|PHONE|EMAIL|DATE|MEDICATION|AGE|PROFESSION|ID"}]. '
    "No prose.\n\nText:\n")


def detect_llm(text, cfg=None):
    """Local LLM layer. cfg.engine 'ollama' (/api/chat) or 'openai' (/v1/chat/completions).
    Returns [] on any error so the deterministic layers still produce output."""
    cfg = cfg or DEFAULTS
    model = cfg.get("anon_model", "qwen2.5:3b")
    host = cfg.get("ollama_host", "http://localhost:11434").rstrip("/")
    api = "openai" if cfg.get("engine") == "openai" else "ollama"
    msgs = [{"role": "user", "content": _LLM_PROMPT + text}]
    try:
        if api == "openai":
            url = cfg.get("llm_base_url", host).rstrip("/") + "/v1/chat/completions"
            body = {"model": model, "messages": msgs, "temperature": 0, "max_tokens": 2048, "stream": False}
            headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            key = os.environ.get("OPENAI_API_KEY", "")
            if key: headers["Authorization"] = "Bearer " + key
        else:
            url = host + "/api/chat"
            body = {"model": model, "messages": msgs, "stream": False, "options": {"temperature": 0, "num_predict": 2048}}
            headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read())
        out = d["choices"][0]["message"]["content"] if api == "openai" else d["message"]["content"]
    except Exception:
        return []
    out = re.sub(r"<think>.*?</think>", "", out, flags=re.DOTALL)
    m = re.search(r"\[.*\]", out, re.DOTALL)
    if not m:
        return []
    try:
        items = json.loads(m.group())
    except json.JSONDecodeError:
        return []
    spans, low = [], text.lower()
    for it in items:
        t = str(it.get("text", "")).strip()
        if not t:
            continue
        typ = str(it.get("type", "")).upper()
        typ = typ if typ in TYPES else "OTHER"
        i = low.find(t.lower())
        while i != -1:
            spans.append(Span(i, i + len(t), text[i:i + len(t)], typ, "llm"))
            i = low.find(t.lower(), i + 1)
    return spans


# ----------------------------------------------------------------- merge + redact
def merge_spans(spans):
    """Interval-merge overlapping spans; merged type = longest contributor (ties: earliest)."""
    if not spans:
        return []
    ss = sorted(spans, key=lambda s: (s.start, -(s.end - s.start)))
    out = [ss[0]]
    for s in ss[1:]:
        last = out[-1]
        if s.start < last.end:
            if (s.end - s.start) > (last.end - last.start):
                out[-1] = Span(last.start, max(last.end, s.end), "", s.type, "merge")
            else:
                out[-1] = Span(last.start, max(last.end, s.end), "", last.type, "merge")
        else:
            out.append(s)
    return out


def redact(text, spans, style="typed_placeholder"):
    """Replace merged spans. typed_placeholder -> [TYPE]; else [REDACTED]."""
    merged = merge_spans(spans)
    out, last = [], 0
    for s in merged:
        out.append(text[last:s.start])
        out.append(f"[{s.type}]" if style == "typed_placeholder" else "[REDACTED]")
        last = s.end
    out.append(text[last:])
    return "".join(out)


def anonymize(text, cfg=None):
    """Run enabled layers, merge, redact. Returns dict (stats carry COUNTS only, no PII)."""
    cfg = cfg or load_config()
    layers = cfg.get("layers", DEFAULTS["layers"])
    spans = []
    if "regex" in layers: spans += detect_regex(text)
    if "natasha" in layers: spans += detect_natasha(text)
    if "llm" in layers: spans += detect_llm(text, cfg)
    merged = merge_spans(spans)
    by_type, by_layer = {}, {}
    for s in spans:
        by_type[s.type] = by_type.get(s.type, 0) + 1
        by_layer[s.source] = by_layer.get(s.source, 0) + 1
    redacted = redact(text, spans, cfg.get("redaction_style", "typed_placeholder"))
    masked = sum(s.end - s.start for s in merged)
    return {
        "redacted_text": redacted,
        "stats": {"chars": len(text), "spans_total": len(spans), "spans_merged": len(merged),
                  "by_type": by_type, "by_layer": by_layer,
                  "redaction_rate": round(masked / len(text), 4) if text else 0.0},
    }
