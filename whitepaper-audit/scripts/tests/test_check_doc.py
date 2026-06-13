"""TDD suite for check_doc.py — deterministic lane of the whitepaper-audit skill.

Written BEFORE the implementation (RED phase). Behaviors per DESIGN.md v0.2.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_doc import (  # noqa: E402
    check_document,
    fk_grade,
    hardest_sentences,
    strip_markdown,
)

# ---------------------------------------------------------------- helpers

FULL_DOC = """# Great Paper

*Version 1.0 · 2026-06-03 · Jane Author*

## Abstract

We measure things carefully. The cat sat on the mat. NER (Named Entity Recognition)
tags names in text. Later we use NER again freely.

## Method

We did the work.

## Limitations

Small sample. Results are directional.

## Glossary

| Term | Meaning |
|---|---|
| **GDPR** | EU privacy law. |
"""


def findings_by_check(text, **kw):
    out = {}
    for f in check_document(text, **kw):
        out.setdefault(f["check_id"], []).append(f)
    return out


# ---------------------------------------------------------------- schema

def test_findings_conform_to_schema():
    doc = "# T\n\nUNDEFINEDACRO is used here without explanation.\n"
    for f in check_document(doc):
        assert f["lane"] == "script"
        assert f["severity"] in {"P0", "P1", "P2"}
        assert f["confidence"] in {"high", "medium", "low"}
        for key in ("check_id", "location", "evidence_quote", "rationale",
                    "suggested_fix"):
            assert key in f, f"missing {key}"


def test_malformed_markdown_does_not_crash():
    junk = "# x\n``` unclosed\n| a | b\n[link(](broke\n\x00weird"
    assert isinstance(check_document(junk), list)


# ---------------------------------------------------------------- readability

def test_fk_grade_simple_lower_than_complex():
    simple = "The cat sat. The dog ran. We like it. It is good."
    complex_ = ("Notwithstanding considerable epistemological heterogeneity, "
                "operationalization of multidimensional anonymization "
                "methodologies necessitates comprehensive interdisciplinary "
                "collaboration across institutional infrastructures.")
    assert fk_grade(simple) < fk_grade(complex_)


def test_strip_markdown_removes_code_tables_headings_urls():
    md = ("## Heading Words\n\n"
          "Real prose stays.\n\n"
          "```python\ncode_tokens_disappear()\n```\n\n"
          "| col | gone |\n|---|---|\n| x | y |\n\n"
          "A [link text](https://example.com/very-long-url) stays as text.\n")
    out = strip_markdown(md)
    assert "Real prose stays" in out
    assert "link text" in out
    assert "code_tokens_disappear" not in out
    assert "https://example.com" not in out
    assert "Heading Words" not in out
    assert "| col |" not in out


def test_hardest_sentences_returns_at_most_n_sorted_hard_first():
    text = ("The cat sat on the mat. "
            "Operationalization of multidimensional anonymization "
            "methodologies necessitates comprehensive interdisciplinary "
            "collaboration. "
            "Dogs run fast.")
    top = hardest_sentences(text, n=2)
    assert len(top) == 2
    assert "Operationalization" in top[0]


def test_readability_finding_emitted_when_over_target():
    hard = ("# T\n\n## Abstract\n\n" +
            ("Operationalization of multidimensional anonymization "
             "methodologies necessitates comprehensive interdisciplinary "
             "collaboration across heterogeneous institutional "
             "infrastructures. ") * 3)
    by = findings_by_check(hard, target_grade=8)
    assert "readability" in by


def test_no_readability_finding_for_simple_doc_with_high_target():
    by = findings_by_check(FULL_DOC, target_grade=30)
    assert "readability" not in by


# ---------------------------------------------------------------- acronyms

def test_acronym_defined_inline_not_flagged():
    doc = "# T\n\nNER (Named Entity Recognition) tags text. NER is useful.\n"
    assert "acronym-undefined" not in findings_by_check(doc)


def test_acronym_reverse_definition_not_flagged():
    doc = "# T\n\nNamed Entity Recognition (NER) tags text. NER is useful.\n"
    assert "acronym-undefined" not in findings_by_check(doc)


def test_undefined_acronym_flagged_P1_high():
    doc = "# T\n\nThe CQRS pattern is great. CQRS everywhere.\n"
    by = findings_by_check(doc)
    assert "acronym-undefined" in by
    f = by["acronym-undefined"][0]
    assert f["severity"] == "P1"
    assert f["confidence"] == "high"
    assert "CQRS" in f["evidence_quote"]


def test_allowlisted_acronyms_not_flagged():
    doc = "# T\n\nExport a PDF from the URL in the USA.\n"
    assert "acronym-undefined" not in findings_by_check(doc)


def test_glossary_entry_counts_as_definition():
    doc = ("# T\n\nGDPR applies here.\n\n## Glossary\n\n"
           "| Term | Meaning |\n|---|---|\n| **GDPR** | EU privacy law. |\n")
    assert "acronym-undefined" not in findings_by_check(doc)


def test_plural_acronym_use_after_definition_not_flagged():
    doc = "# T\n\nLLM (Large Language Model) tools. LLMs are everywhere.\n"
    assert "acronym-undefined" not in findings_by_check(doc)


# ---------------------------------------------------------------- structure

def test_complete_doc_has_no_structure_findings():
    assert "structure" not in findings_by_check(FULL_DOC)


def test_missing_limitations_is_P0_candidate():
    doc = FULL_DOC.replace("## Limitations\n\nSmall sample. Results are directional.\n\n", "")
    by = findings_by_check(doc)
    assert "structure" in by
    lim = [f for f in by["structure"] if "limitation" in f["rationale"].lower()
           or "limitation" in f["evidence_quote"].lower()]
    assert lim and lim[0]["severity"] == "P0" and lim[0]["confidence"] == "medium"


def test_missing_glossary_is_P2():
    doc = FULL_DOC.split("## Glossary")[0]
    by = findings_by_check(doc)
    gl = [f for f in by.get("structure", []) if "glossary" in
          (f["rationale"] + f["evidence_quote"]).lower()]
    assert gl and gl[0]["severity"] == "P2"


# ---------------------------------------------------------------- links

def test_relative_link_to_missing_file_flagged(tmp_path):
    doc = "# T\n\nSee [the data](data/gone.csv).\n"
    by = findings_by_check(doc, base_dir=tmp_path)
    assert "links" in by
    assert "data/gone.csv" in by["links"][0]["evidence_quote"]


def test_relative_link_to_existing_file_ok(tmp_path):
    (tmp_path / "real.md").write_text("hi")
    doc = "# T\n\nSee [real](real.md).\n"
    assert "links" not in findings_by_check(doc, base_dir=tmp_path)


def test_http_links_skipped_when_offline():
    doc = "# T\n\nSee [site](https://definitely-not-a-real-host-xyz.example).\n"
    assert "links" not in findings_by_check(doc, offline=True)


# ---------------------------------------------------------------- CLI

def test_cli_outputs_json_and_exits_zero(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# T\n\nCQRS everywhere.\n")
    script = Path(__file__).resolve().parents[1] / "check_doc.py"
    r = subprocess.run([sys.executable, str(script), str(p), "--offline"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert isinstance(data, list)
    assert any(f["check_id"] == "acronym-undefined" for f in data)
