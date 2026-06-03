"""Offline tests for confide:anon (force layers=['regex'] -> no network/models).

Synthetic PII only; never reads real files. Verifies: planted PII absent from the
redacted GREEN text, typed placeholders present, stats are COUNTS-only (no PII
substrings), folder mode produces .green.md + .stats.json without touching originals,
and --dry-run writes nothing.
"""
import json
import os
import sys

# import the skill script module (scripts/anon.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "anon", "scripts"))
import anon  # noqa: E402

# regex-only config: fully offline, deterministic
CFG = {"layers": ["regex"], "redaction_style": "typed_placeholder"}

# synthetic fixture with planted direct identifiers
FIXTURE = (
    "Client jane.doe@example.com called +1-415-555-0198 last Tuesday. "
    "We met 15 March. Notes at https://clinic.example.org/records were reviewed."
)
PLANTED = [
    "jane.doe@example.com",
    "+1-415-555-0198",
    "last Tuesday",
    "15 March",
    "https://clinic.example.org/records",
]


def _anonymize(text):
    from confide_core import anonymize  # via shared path added by anon.py
    return anonymize(text, CFG)


def test_planted_pii_absent_and_placeholders_present():
    r = _anonymize(FIXTURE)
    red = r["redacted_text"]
    for leak in PLANTED:
        assert leak not in red, f"leaked: {leak}"
    for ph in ["[EMAIL]", "[PHONE]", "[DATE]", "[URL]"]:
        assert ph in red, f"missing placeholder: {ph}"


def test_stats_contain_no_pii_substrings():
    r = _anonymize(FIXTURE)
    blob = json.dumps(r["stats"])
    for leak in PLANTED + ["jane", "415", "clinic.example.org"]:
        assert leak not in blob, f"stats leaked: {leak}"
    # stats are counts: ints only in the by_type / by_layer maps
    assert r["stats"]["by_type"].get("EMAIL", 0) >= 1
    assert all(isinstance(v, int) for v in r["stats"]["by_type"].values())
    assert all(isinstance(v, int) for v in r["stats"]["by_layer"].values())


def test_summarize_emits_counts_only_no_pii():
    r = _anonymize(FIXTURE)
    line = anon.summarize(r["stats"], name="fixture")
    for leak in PLANTED:
        assert leak not in line
    assert "EMAIL" in line  # type label is fine; value is not


def test_process_file_writes_green_and_stats(tmp_path):
    src = tmp_path / "session.md"
    src.write_text(FIXTURE, encoding="utf-8")
    res = anon.process_file(str(src), CFG)
    green = tmp_path / "session.green.md"
    stats = tmp_path / "session.stats.json"
    assert green.exists() and stats.exists()
    # green has redacted text only; original PII never written
    gtext = green.read_text(encoding="utf-8")
    for leak in PLANTED:
        assert leak not in gtext
    assert "[EMAIL]" in gtext
    # stats file is counts-only valid json
    sdata = json.loads(stats.read_text(encoding="utf-8"))
    assert "by_type" in sdata and "redaction_rate" in sdata
    sblob = json.dumps(sdata)
    for leak in PLANTED:
        assert leak not in sblob
    # original untouched
    assert src.read_text(encoding="utf-8") == FIXTURE
    # returned paths point at the written files
    assert res["green"] == str(green) and res["stats_path"] == str(stats)


def test_folder_mode_two_files(tmp_path):
    f1 = tmp_path / "a.md"
    f2 = tmp_path / "b.md"
    f1.write_text("Mail a@x.com", encoding="utf-8")
    f2.write_text("Call +1-415-555-0198", encoding="utf-8")
    results = anon.process_path(str(tmp_path), CFG)
    assert len(results) == 2
    greens = sorted(p.name for p in tmp_path.glob("*.green.md"))
    stats = sorted(p.name for p in tmp_path.glob("*.stats.json"))
    assert greens == ["a.green.md", "b.green.md"]
    assert stats == ["a.stats.json", "b.stats.json"]
    # originals untouched
    assert f1.read_text(encoding="utf-8") == "Mail a@x.com"
    assert f2.read_text(encoding="utf-8") == "Call +1-415-555-0198"
    # green copies are not re-processed as inputs
    assert "a@x.com" not in (tmp_path / "a.green.md").read_text(encoding="utf-8")


def test_dry_run_writes_no_files(tmp_path):
    src = tmp_path / "session.md"
    src.write_text(FIXTURE, encoding="utf-8")
    res = anon.process_file(str(src), CFG, dry=True)
    assert list(tmp_path.glob("*.green.md")) == []
    assert list(tmp_path.glob("*.stats.json")) == []
    # still returns stats for the summary
    assert res["stats"]["by_type"].get("EMAIL", 0) >= 1
    assert res["green"] is None and res["stats_path"] is None


def test_out_dir_override(tmp_path):
    src = tmp_path / "session.md"
    src.write_text(FIXTURE, encoding="utf-8")
    out = tmp_path / "redacted"
    anon.process_file(str(src), CFG, out=str(out))
    assert (out / "session.green.md").exists()
    assert (out / "session.stats.json").exists()
