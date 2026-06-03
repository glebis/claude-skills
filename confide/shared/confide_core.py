#!/usr/bin/env python3
"""CONFIDE core — config, layered local PII detectors, span merge, redaction.

Shared by confide:anon and confide:red. Local-first: the deterministic regex layer and
redaction need no network; Natasha (RU NER) and the LLM layer load only if available.
Nothing here prints or returns raw PII to any caller that doesn't already have the text.
"""
import datetime
import hashlib
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
    # optional ensemble layer (off by default). Add "presidio" to layers to enable.
    # Needs `pip install presidio-analyzer` + `spacy download ru_core_news_sm`.
    "presidio_lang": "ru",
    "presidio_model": "ru_core_news_sm",
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
# Bare-domain URL (no scheme): host with a known TLD + optional path — e.g. example.ru,
# t.me/handle. ASCII-only host so Cyrillic abbreviations ("т.е.", "и т.д.") never match;
# alpha TLD from an allowlist so decimals ("2.5") never match.
_URL_BARE = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
    r"(?:ru|com|org|net|io|me|app|dev|ai|co|info|biz|tv|xyz|de|uk|fr|es|it|nl|pl|eu|su|рф)"
    r"(?:/[^\s)>\]]*)?\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\-\s().]{7,}\d)(?!\w)")
_ID = re.compile(r"\b\d{3,4}[- ]\d{3,4}[- ]\d{2,4}(?:[- ]\d{1,4})?\b")  # policy/SNILS/INN-like
_DATE_NUM = re.compile(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b")
_DATE_REL_EN = re.compile(r"\b(?:last|next|this)\s+(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\b|\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b", re.IGNORECASE)
_DATE_REL_RU = re.compile(r"\b\d{1,2}\s+(?:январ|феврал|март|апрел|ма[яй]|июн|июл|август|сентябр|октябр|ноябр|декабр)\w*\b", re.IGNORECASE)
# AGE — a quasi-identifier. Deterministic so it never depends on the (weak) LLM layer.
# RU digit: "67 лет" / "1 год" / "3 года". EN: "67 years old" / "41-year-old".
_AGE_RU_DIGIT = re.compile(r"\b\d{1,3}\s+(?:лет|год|года)\b", re.IGNORECASE)
_AGE_EN = re.compile(r"\b\d{1,3}\s*[- ]?\s*years?[- ]old\b|\b\d{1,3}\s+years?\s+old\b", re.IGNORECASE)
# RU spelled-out: "сорок лет", "шестьдесят семь лет" (tens [+ ones]) before лет/год/года.
_RU_TENS = r"(?:двадцат|тридцат|сорок|пятьдесят|шестьдесят|семьдесят|восемьдесят|девяност)\w*"
_RU_ONES = r"(?:один|одна|два|две|три|четыр\w+|пят\w+|шест\w+|сем\w+|восем\w+|девят\w+)"
_AGE_RU_WORD = re.compile(rf"\b(?:{_RU_TENS}(?:\s+{_RU_ONES})?|{_RU_ONES})\s+(?:лет|год|года)\b", re.IGNORECASE)


def detect_regex(text):
    """Deterministic detectors — no network, no deps required."""
    spans = []
    for rx, typ in [(_EMAIL, "EMAIL"), (_URL, "URL"), (_URL_BARE, "URL"), (_PHONE, "PHONE"), (_ID, "ID"),
                    (_DATE_NUM, "DATE"), (_DATE_REL_EN, "DATE"), (_DATE_REL_RU, "DATE"),
                    (_AGE_RU_DIGIT, "AGE"), (_AGE_EN, "AGE"), (_AGE_RU_WORD, "AGE")]:
        for m in rx.finditer(text):
            s = m.group().strip()
            if typ == "PHONE" and sum(c.isdigit() for c in s) < 7:
                continue
            # the phone char class includes '.', so it also matches dotted/slashed
            # numeric dates (15.01.2026). Those are DATE, not PHONE — yield.
            if typ == "PHONE" and _DATE_NUM.fullmatch(s):
                continue
            spans.append(Span(m.start(), m.start() + len(s), s, typ, "regex"))
    return spans


# ----------------------------------------------------------------- Natasha layer
# Transcript scaffolding that NER mis-tags as entities (esp. ORG): speaker labels +
# timestamp words from Fathom/Granola exports. These are structure, not PII.
_SCAFFOLD = re.compile(
    r"^(?:speaker\s*\d+|user|host|guest|me|ai|assistant|today|yesterday|"
    r"спикер\s*\d+|сегодня|вчера)$", re.IGNORECASE)


def filter_ner_scaffolding(spans):
    """Drop NER false positives from transcript structure: any span containing a
    newline (real inline entities never do) or matching a scaffolding stopword."""
    out = []
    for s in spans:
        if "\n" in s.text:
            continue
        if _SCAFFOLD.match(s.text.strip()):
            continue
        out.append(s)
    return out


def detect_natasha(text):
    """RU NER. Returns [] if natasha not installed."""
    try:
        from natasha import Segmenter, NewsEmbedding, NewsNERTagger, Doc
    except ImportError:
        return []
    seg, emb = Segmenter(), NewsEmbedding()
    doc = Doc(text); doc.segment(seg); doc.tag_ner(NewsNERTagger(emb))
    m = {"PER": "PERSON", "LOC": "LOCATION", "ORG": "ORG"}
    spans = [Span(sp.start, sp.stop, text[sp.start:sp.stop], m.get(sp.type, sp.type), "natasha")
             for sp in doc.spans]
    return filter_ner_scaffolding(spans)


# ----------------------------------------------------------------- Presidio layer (optional)
_PRESIDIO_MAP = {"PERSON": "PERSON", "LOCATION": "LOCATION", "GPE": "LOCATION", "NRP": "OTHER",
                 "DATE_TIME": "DATE", "PHONE_NUMBER": "PHONE", "EMAIL_ADDRESS": "EMAIL",
                 "URL": "URL", "IP_ADDRESS": "ID", "ORGANIZATION": "ORG", "ORG": "ORG"}
_PRESIDIO_ENGINE = {}


def detect_presidio(text, cfg=None):
    """Optional ensemble layer: Microsoft Presidio with a spaCy model. Off by default.
    Best at bare-domain URLs/dates/locations; complements regex+Natasha. Returns [] if
    presidio/the spaCy model isn't installed (never hard-fails the pipeline)."""
    cfg = cfg or DEFAULTS
    lang = cfg.get("presidio_lang", "ru")
    model = cfg.get("presidio_model", "ru_core_news_sm")
    try:
        if lang not in _PRESIDIO_ENGINE:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            nlp = NlpEngineProvider(nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": lang, "model_name": model}]}).create_engine()
            _PRESIDIO_ENGINE[lang] = AnalyzerEngine(nlp_engine=nlp, supported_languages=[lang])
        results = _PRESIDIO_ENGINE[lang].analyze(text=text, language=lang)
    except Exception:
        return []
    return [Span(r.start, r.end, text[r.start:r.end],
                 _PRESIDIO_MAP.get(r.entity_type, r.entity_type), "presidio") for r in results]


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
    if "presidio" in layers: spans += detect_presidio(text, cfg)
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


# ----------------------------------------------------------------- reversible (rehydrate)
#
# Reversible placeholders use a RESERVED SENTINEL grammar so they can never collide
# with real transcript prose:  [CONFIDE_<TYPE>_<NNNN>]  (zero-padded 4 digits), e.g.
# [CONFIDE_PERSON_0001]. A real document will essentially never contain that exact
# token, and the distinctive CONFIDE_ prefix means rehydrate never matches ordinary
# phrases like "Person 1" / "patient 1" / "section 2".
MAP_SCHEMA_VERSION = 1
_PH_PREFIX = "CONFIDE"

# canonical sentinel placeholder produced by redaction
_PH_CANON = re.compile(r"\[" + _PH_PREFIX + r"_([A-Z]+)_(\d{4})\]")


def make_placeholder(typ, n):
    """Canonical reversible placeholder for a type + 1-based index: [CONFIDE_PERSON_0001]."""
    return f"[{_PH_PREFIX}_{typ}_{n:04d}]"


def green_sha256(green_text):
    """sha256 hex of the GREEN text — lets a map be verified against its document."""
    return hashlib.sha256(green_text.encode("utf-8")).hexdigest()


def build_map(green_text, entries, doc_id=None, created=None):
    """Assemble the structured reversible-map dict.

    entries: list of {"placeholder","type","original"}. doc_id defaults to a short
    hash of the green text; created defaults to now (UTC, iso). Carries the green's
    sha256 so a wrong map for a document can be detected (--verify-green)."""
    sha = green_sha256(green_text)
    if doc_id is None:
        doc_id = sha[:12]
    if created is None:
        created = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": MAP_SCHEMA_VERSION,
        "doc_id": doc_id,
        "green_sha256": sha,
        "created": created,
        "entries": list(entries),
    }


def map_lookup(mapping):
    """Return a flat {placeholder: original} dict from either map schema (structured
    {"entries":[...]} or a legacy flat {placeholder: original})."""
    if isinstance(mapping, dict) and "entries" in mapping:
        return {e["placeholder"]: e["original"] for e in mapping["entries"]}
    return dict(mapping)


def redact_reversible(text, spans, doc_id=None, created=None):
    """Redact with UNIQUE, coreferent reserved-sentinel placeholders + a reversible map.

    Same EXACT (type, surface value) -> same [CONFIDE_TYPE_NNNN] (this is exact-value
    coreference, NOT entity coreference; inflected forms are distinct placeholders).
    Returns (green_text, map_dict) where map_dict is the structured schema from
    build_map(). The map is the secret — caller must keep it LOCAL, never ship it."""
    merged = merge_spans(spans)
    val2ph, counters, entries = {}, {}, []
    out, last = [], 0
    for s in merged:
        orig = text[s.start:s.end]
        key = (s.type, orig.lower())
        ph = val2ph.get(key)
        if ph is None:
            counters[s.type] = counters.get(s.type, 0) + 1
            ph = make_placeholder(s.type, counters[s.type])
            val2ph[key] = ph
            entries.append({"placeholder": ph, "type": s.type, "original": orig})
        out.append(text[last:s.start]); out.append(ph); last = s.end
    out.append(text[last:])
    green = "".join(out)
    return green, build_map(green, entries, doc_id=doc_id, created=created)


def _mangled_pattern(typ, num):
    """Regex matching the sentinel placeholder and tolerable LLM manglings that STILL
    contain the full CONFIDE_TYPE_NNNN core: optional brackets, a single space OR
    underscore between the 3 parts, case-insensitive on the word parts. The CONFIDE
    prefix is REQUIRED, so naked forms ("Person 1") are never matched. `num` must not
    be followed by another digit so 0001 never eats 0010."""
    sep = r"[ _]"  # exactly one space or underscore between parts
    return re.compile(
        r"\[?\s*" + _PH_PREFIX + sep + re.escape(typ) + sep + num + r"(?!\d)\s*\]?",
        re.IGNORECASE,
    )


def rehydrate(text, mapping):
    """Replace reserved-sentinel placeholders with originals, robust to LLM mangling
    that still contains the full CONFIDE_TYPE_NNNN core (optional brackets, single
    space/underscore separators, case-insensitive). Does NOT match naked "Person 1".

    Single-pass: all placeholders are matched in ONE scan, longest/most-specific core
    first, so _0001 never pre-empts _0010 and an already-restored original is never
    re-touched (idempotent — originals contain no sentinels). Accepts either map
    schema. Returns (restored_text, {restored, unmatched}). Local-only; never transmits."""
    flat = map_lookup(mapping)
    # Build one combined matcher; order alternatives most-specific (longest core) first.
    specs = []  # (pattern_str, original)
    for ph, orig in flat.items():
        m = _PH_CANON.match(ph)
        if not m:
            # legacy/non-sentinel key: literal match only (no fuzzy prose matching)
            specs.append((re.escape(ph), orig, len(ph)))
            continue
        typ, num = m.group(1), m.group(2)
        sep = r"[ _]"
        core = _PH_PREFIX + sep + re.escape(typ) + sep + num + r"(?!\d)"
        specs.append((r"\[?\s*" + core + r"\s*\]?", orig, len(typ) + len(num)))
    if not specs:
        unmatched = len(re.findall(r"\[" + _PH_PREFIX + r"_[A-Za-z]+_\d+\]", text))
        return text, {"restored": 0, "unmatched": unmatched}

    # longest core first => specific placeholders win over shorter ones
    specs.sort(key=lambda s: -s[2])
    repl = {}
    parts = []
    for i, (pat, orig, _w) in enumerate(specs):
        g = f"p{i}"
        parts.append(f"(?P<{g}>{pat})")
        repl[g] = orig
    combined = re.compile("|".join(parts), re.IGNORECASE)

    restored = 0

    def _sub(m):
        nonlocal restored
        restored += 1
        return repl[m.lastgroup]

    out = combined.sub(_sub, text)
    # remaining sentinel-shaped tokens that weren't in the map = hallucinated/unmatched
    unmatched = len(re.findall(r"\[" + _PH_PREFIX + r"_[A-Za-z]+_\d+\]", out))
    return out, {"restored": restored, "unmatched": unmatched}
