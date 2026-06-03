#!/usr/bin/env python3
"""confide:red — residual re-identification RISK CHECK on already-redacted output.

DEFENSIVE / DUAL-USE. This is NOT a benchmark and has NO ground truth. It surfaces,
qualitatively, what an attacker could STILL do with text you have already redacted —
mapped to GDPR Art-29: singling-out, linkability, inference.

Load-bearing signal (deterministic, offline): re-run the CONFIDE detectors on the
REDACTED text. Anything they STILL find = a residual leak the redaction missed.

GUARDRAILS:
  * Run ONLY on your OWN redacted output. Do not use this to de-anonymize third-party data.
  * Output is risk CATEGORIES and COUNTS — never a step-by-step re-identification recipe.
  * Local attacker by default. Cloud inference probe is opt-in, synthetic/consented only.
  * Absence of a finding != safety. Human review is still required.

Pairs with confide:anon (run this AFTER redacting).
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))
import confide_core as C  # noqa: E402

# GDPR Art-29 singling-out surface.
# DIRECT identifiers can single a person out on their own -> HIGH if any survive.
# QUASI identifiers need linkage/combination -> MEDIUM if only these survive.
DIRECT_TYPES = {"EMAIL", "PHONE", "URL", "ID", "PERSON"}
QUASI_TYPES = {"LOCATION", "ORG", "DATE", "AGE", "PROFESSION", "MEDICATION", "OTHER"}

CAVEAT = (
    "This is a residual-risk signal, NOT a guarantee. Absence of a finding does not "
    "mean the text is safe to share: a weak local detector/attacker is a FLOOR, not a "
    "ceiling. Human review is still required."
)


def cfg():
    """Loaded config (defaults if no file)."""
    return C.load_config()


# --------------------------------------------------------------- singling-out
def singling_out(text, config=None):
    """Re-run deterministic detectors on the REDACTED text.

    Any span found = a SURVIVING identifier the redaction missed. Returns COUNTS
    by type only (no PII values), so this report can be shared safely.
    """
    config = config or cfg()
    spans = C.detect_regex(text)
    if "natasha" in config.get("layers", []):
        spans += C.detect_natasha(text)
    # Count one surviving identifier per non-overlapping region. merge_spans collapses
    # overlaps but blanks .type on merged regions, so recover the type from the raw
    # span that starts each merged region (longest contributor / earliest start).
    raw_by_start = {}
    for s in sorted(spans, key=lambda s: (s.start, -(s.end - s.start))):
        raw_by_start.setdefault(s.start, s.type)
    by_type = {}
    for m in C.merge_spans(spans):
        typ = m.type or raw_by_start.get(m.start)
        if not typ:
            continue
        by_type[typ] = by_type.get(typ, 0) + 1
    return {"by_type": by_type, "total": sum(by_type.values())}


def risk_tier(findings):
    """HIGH if any DIRECT identifier survives; MEDIUM if only QUASI survive; LOW if none.

    Counts/categories only — no re-identification steps.
    """
    by_type = findings.get("by_type", {})
    present = {t for t, n in by_type.items() if n > 0}
    if present & DIRECT_TYPES:
        return "HIGH"
    if present & QUASI_TYPES:
        return "MEDIUM"
    return "LOW"


# --------------------------------------------------------------- linkability
def _surviving_keys(text, config):
    """Set of surviving quasi-identifier surface strings (normalized) used only to
    detect potential CROSS-FILE linkage. Kept internal; never emitted in the report."""
    config = config or cfg()
    spans = C.detect_regex(text)
    if "natasha" in config.get("layers", []):
        spans += C.detect_natasha(text)
    return {(s.type, s.text.strip().lower()) for s in spans if s.text.strip()}


def linkability(texts, config=None):
    """Compare ALL file pairs for shared surviving identifiers.

    `texts` is {filename: redacted_text}. Returns a list of linkable-pair signals:
    {"files": (a, b), "shared_types": [...], "shared_count": n}. This flags that two
    files COULD be linked by a common surviving quasi-identifier — it is a risk signal,
    NOT a re-identification. Shared VALUES are never returned, only types and counts.
    """
    config = config or cfg()
    keys = {name: _surviving_keys(t, config) for name, t in texts.items()}
    names = sorted(keys)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            shared = keys[a] & keys[b]
            if shared:
                pairs.append({
                    "files": (a, b),
                    "shared_types": sorted({t for t, _ in shared}),
                    "shared_count": len(shared),
                })
    return pairs


# --------------------------------------------------------------- inference (LLM, optional)
_INFER_PROMPT = (
    "You are auditing ALREADY-REDACTED text for residual privacy risk. Placeholders like "
    "[PERSON] hide values. Do NOT guess the hidden values. List ONLY the broad CATEGORIES "
    "of personal attributes a reader could still infer about the subject (e.g. profession, "
    "approximate age band, location type, health condition area, relationship status). "
    'Return ONLY a JSON array of category strings, e.g. ["profession","location"]. No values, no prose.\n\nText:\n'
)


def inference_probe(text, config=None):
    """Ask the LOCAL attacker model what attribute CATEGORIES remain inferable.

    Returns {"ran": bool, "categories": [...], "note": str}. Degrades gracefully to
    ran=False if the model/engine is unavailable. Reports categories ONLY — never the
    inferred values, and never a re-identification recipe.
    """
    config = config or cfg()
    probe_cfg = dict(config)
    probe_cfg["anon_model"] = config.get("red_attacker_model", config.get("anon_model", "qwen2.5:3b"))
    out = _call_model(_INFER_PROMPT + text, probe_cfg)
    if out is None:
        return {"ran": False, "categories": [],
                "note": "Local attacker model unavailable; inference probe skipped."}
    cats = _parse_categories(out)
    return {"ran": True, "categories": cats,
            "note": ("Local attacker is a FLOOR, not a ceiling: a weak model UNDER-reports. "
                     "A stronger/cloud attacker may infer more.")}


def _call_model(prompt, config):
    """Thin call to the local engine. Returns text or None on any failure."""
    import urllib.request
    model = config.get("anon_model", "qwen2.5:3b")
    host = config.get("ollama_host", "http://localhost:11434").rstrip("/")
    api = "openai" if config.get("engine") == "openai" else "ollama"
    msgs = [{"role": "user", "content": prompt}]
    try:
        if api == "openai":
            url = config.get("llm_base_url", host).rstrip("/") + "/v1/chat/completions"
            body = {"model": model, "messages": msgs, "temperature": 0, "max_tokens": 512, "stream": False}
            headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            key = os.environ.get("OPENAI_API_KEY", "")
            if key:
                headers["Authorization"] = "Bearer " + key
        else:
            url = host + "/api/chat"
            body = {"model": model, "messages": msgs, "stream": False,
                    "options": {"temperature": 0, "num_predict": 512}}
            headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
        return d["choices"][0]["message"]["content"] if api == "openai" else d["message"]["content"]
    except Exception:
        return None


def _parse_categories(out):
    import re
    out = re.sub(r"<think>.*?</think>", "", out, flags=re.DOTALL)
    m = re.search(r"\[.*\]", out, re.DOTALL)
    if not m:
        return []
    try:
        items = json.loads(m.group())
    except json.JSONDecodeError:
        return []
    return sorted({str(x).strip().lower() for x in items if str(x).strip()})


# --------------------------------------------------------------- assessment
def assess_text(text, config=None, inference=False):
    """Per-file residual-risk report (categories/counts only)."""
    config = config or cfg()
    surviving = singling_out(text, config)
    tier = risk_tier(surviving)
    infer = inference_probe(text, config) if inference else {"ran": False, "categories": [],
                                                             "note": "Inference probe not requested."}
    return {
        "risk_tier": tier,
        "surviving": surviving,
        "inference": infer,
        "caveat": CAVEAT,
    }


def assess_folder(texts, config=None, inference=False):
    """Multi-file report: per-file assessment + cross-file linkability."""
    config = config or cfg()
    per_file = {name: assess_text(t, config, inference) for name, t in texts.items()}
    pairs = linkability(texts, config)
    tiers = [r["risk_tier"] for r in per_file.values()]
    overall = "HIGH" if "HIGH" in tiers else "MEDIUM" if "MEDIUM" in tiers else "LOW"
    if pairs and overall == "LOW":
        overall = "MEDIUM"  # linkable pairs raise the floor
    return {
        "overall_risk_tier": overall,
        "per_file": per_file,
        "linkable_pairs": pairs,
        "linkable_pair_count": len(pairs),
        "caveat": CAVEAT,
    }


# --------------------------------------------------------------- CLI
def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _collect(path):
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.md")) + glob.glob(os.path.join(path, "*.txt")))
        return {os.path.basename(p): _read(p) for p in files}
    return {os.path.basename(path): _read(path)}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="confide:red — residual re-identification RISK CHECK on YOUR OWN redacted output.")
    ap.add_argument("path", help="redacted file or folder (your own redacted output)")
    ap.add_argument("--inference", action="store_true",
                    help="opt-in LLM inference probe (synthetic/consented data only)")
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    args = ap.parse_args(argv)

    config = cfg()
    texts = _collect(args.path)

    if len(texts) > 1:
        report = assess_folder(texts, config, inference=args.inference)
    else:
        name, text = next(iter(texts.items()))
        report = {"file": name, **assess_text(text, config, inference=args.inference)}

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    _print_human(report)
    return report


def _print_human(report):
    print("=== confide:red — residual re-identification RISK CHECK ===")
    print("Defensive audit of YOUR OWN redacted output. Categories/counts only.\n")
    if "per_file" in report:
        print(f"OVERALL RISK TIER: {report['overall_risk_tier']}")
        print(f"Linkable pairs (shared surviving quasi-identifiers): {report['linkable_pair_count']}")
        for pr in report["linkable_pairs"]:
            a, b = pr["files"]
            print(f"  - {a} <-> {b}: {pr['shared_count']} shared ({', '.join(pr['shared_types'])})")
        print()
        for name, r in report["per_file"].items():
            _print_file(name, r)
    else:
        _print_file(report.get("file", "(file)"), report)
    print("\nCAVEAT:", report["caveat"])


def _print_file(name, r):
    print(f"[{name}] tier={r['risk_tier']}")
    bt = r["surviving"]["by_type"]
    if bt:
        print("  surviving identifiers (count by type): "
              + ", ".join(f"{t}={n}" for t, n in sorted(bt.items())))
    else:
        print("  surviving identifiers: none found by detectors (NOT a guarantee)")
    inf = r["inference"]
    if inf["ran"]:
        print("  inferable attribute categories: "
              + (", ".join(inf["categories"]) if inf["categories"] else "(none claimed)"))
        print("  note:", inf["note"])
    else:
        print("  inference probe:", inf["note"])


if __name__ == "__main__":
    main()
