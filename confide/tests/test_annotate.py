"""Offline tests for confide:annotate.

Covers:
  - bundled assets exist and are non-empty (annotator.html carries the UI/I18N,
    codebook.md is real prose).
  - score_iaa.py runs standalone over two mock annotator-export label files,
    computes a Cohen's kappa, flags >=1 disagreement, and drafts an adjudicated gold.

Synthetic data only. No network, no confide_eval package.
"""
import importlib.util
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ANNOTATE = os.path.join(ROOT, "skills", "annotate")
SCRIPTS = os.path.join(ANNOTATE, "scripts")
ASSETS = os.path.join(ANNOTATE, "assets")
REFS = os.path.join(ANNOTATE, "references")


def _load_score_iaa():
    path = os.path.join(SCRIPTS, "score_iaa.py")
    spec = importlib.util.spec_from_file_location("score_iaa", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Small synthetic transcript. Char offsets below index into this exact string.
TEXT = "Hi, my name is Marina and I live in Kostroma near the river."
#       0123456789...  "Marina" -> [15,21), "Kostroma" -> [36,44)
MARINA = (15, 21)
KOSTROMA = (36, 44)


def _span(start, end, type_, note=""):
    return {
        "start": start,
        "end": end,
        "text": TEXT[start:end],
        "type": type_,
        "identifier_class": "direct",
        "entity_id": "",
        "person_role": "client",
        "harm": "medium",
        "note": note,
    }


def _write_labels(d):
    """Two annotators: agree on Marina/PERSON, disagree on Kostroma (LOCATION vs ORG)."""
    a = {
        "doc_id": "docX",
        "annotator": "A",
        "codebook": "v1",
        "text": TEXT,
        "spans": [_span(*MARINA, "PERSON"), _span(*KOSTROMA, "LOCATION")],
    }
    b = {
        "doc_id": "docX",
        "annotator": "B",
        "codebook": "v1",
        "text": TEXT,
        "spans": [_span(*MARINA, "PERSON"), _span(*KOSTROMA, "ORG", note="QUESTION: gym or city?")],
    }
    json.dump(a, open(os.path.join(d, "labels.docX.A.json"), "w"), ensure_ascii=False)
    json.dump(b, open(os.path.join(d, "labels.docX.B.json"), "w"), ensure_ascii=False)


# ---------------------------------------------------------------- bundled assets


def test_annotator_html_bundled_and_non_empty():
    p = os.path.join(ASSETS, "annotator.html")
    assert os.path.exists(p), "annotator.html not bundled"
    html = open(p, encoding="utf-8").read()
    assert len(html) > 5000, "annotator.html looks truncated"
    low = html.lower()
    assert "<html" in low
    # the annotator UI: I18N strings + a notion of spans/annotator
    assert ("i18n" in low) or ("annotat" in low)


def test_codebook_bundled_and_non_empty():
    p = os.path.join(REFS, "codebook.md")
    assert os.path.exists(p)
    txt = open(p, encoding="utf-8").read()
    assert len(txt) > 1000
    assert "PERSON" in txt  # the type taxonomy is present


def test_tool_guide_and_scripts_bundled():
    assert os.path.getsize(os.path.join(REFS, "tool-guide.md")) > 0
    assert os.path.getsize(os.path.join(SCRIPTS, "score_iaa.py")) > 0
    assert os.path.getsize(os.path.join(SCRIPTS, "gold_to_labels.py")) > 0


def test_scripts_are_standalone_no_confide_eval_import():
    for name in ("score_iaa.py", "gold_to_labels.py"):
        src = open(os.path.join(SCRIPTS, name), encoding="utf-8").read()
        assert "confide_eval" not in src, f"{name} still imports confide_eval"


# ---------------------------------------------------------------- IAA scoring


def test_score_iaa_functions_compute_kappa_and_disagreement(tmp_path):
    mod = _load_score_iaa()
    a = [_span(*MARINA, "PERSON"), _span(*KOSTROMA, "LOCATION")]
    b = [_span(*MARINA, "PERSON"), _span(*KOSTROMA, "ORG")]
    n = len(TEXT)
    la = mod.char_labels(n, a)
    lb = mod.char_labels(n, b)
    k = mod.cohen_kappa(la, lb)
    assert k is not None
    assert 0.0 < k < 1.0  # partial agreement -> kappa strictly between 0 and 1

    # cluster_spans groups the overlapping Kostroma spans into one adjudication cluster
    tagged = [dict(s, _by="A") for s in a] + [dict(s, _by="B") for s in b]
    clusters = mod.cluster_spans(tagged)
    # Marina cluster + Kostroma cluster
    assert len(clusters) == 2
    multi_type = [c for c in clusters if len({s["type"] for s in c}) > 1]
    assert len(multi_type) == 1, "the Kostroma LOCATION-vs-ORG disagreement should surface"


def test_score_iaa_cli_produces_kappa_disagreements_and_draft_gold(tmp_path):
    labels = tmp_path / "labels"
    labels.mkdir()
    _write_labels(str(labels))
    out = tmp_path / "out"

    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "score_iaa.py"),
         "--labels-dir", str(labels), "--out-dir", str(out), "--out-prefix", "test-"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr

    results = json.load(open(out / "test-iaa-results.json"))
    overall = results["overall"]
    assert overall["n_docs_scored"] == 1
    k = overall["cohen_kappa_pairwise_mean"]
    assert k is not None and 0.0 < k < 1.0

    dis = json.load(open(out / "test-iaa-disagreements.json"))["disagreements"]
    assert len(dis) >= 1, "expected the Kostroma disagreement flagged"

    draft = json.load(open(out / "test-adjudicated-gold-draft.json"))["draft_gold"]
    assert len(draft) >= 2  # Marina + Kostroma clusters
    # Marina is unanimous -> not flagged; Kostroma is disputed -> flagged
    marina = [g for g in draft if g["text"] == "Marina"]
    assert marina and marina[0]["needs_review"] is False
    kostroma = [g for g in draft if g["text"] == "Kostroma"]
    assert kostroma and kostroma[0]["needs_review"] is True
