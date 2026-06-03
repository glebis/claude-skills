"""Offline round-trip tests for confide:rehydrate.

anon (reversible) -> green + map, then rehydrate(analysis, map):
- exact placeholders restore to the original masked values
- mangled placeholders ("Person 1", "[DATE 1]") still restore
- a placeholder absent from the map is reported as unmatched and left in place
- the restore summary is counts-only; restored file written locally
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "anon", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "rehydrate", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import anon  # noqa: E402
import rehydrate  # noqa: E402
import confide_core as C  # noqa: E402

P = C.make_placeholder
CFG = {"layers": ["regex"]}
FIXTURE = (
    "Client jane.doe@example.com called +1-415-555-0198 last Tuesday. We met 15 March."
)


def _anon(tmp_path):
    src = tmp_path / "session.md"
    src.write_text(FIXTURE, encoding="utf-8")
    res = anon.process_file(str(src), CFG)
    green = (tmp_path / "session.green.md").read_text(encoding="utf-8")
    mapping = json.loads((tmp_path / "session.map.json").read_text(encoding="utf-8"))
    return res, green, mapping


def test_roundtrip_restores_masked_values(tmp_path):
    _, green, mapping = _anon(tmp_path)
    restored, summary = rehydrate.rehydrate_text(green, mapping)
    assert "jane.doe@example.com" in restored
    assert "+1-415-555-0198" in restored
    assert summary["restored"] >= 2
    assert summary["unmatched"] == 0


def test_mangled_placeholders_restore(tmp_path):
    _, _, mapping = _anon(tmp_path)
    flat = C.map_lookup(mapping)
    # simulate a cloud analysis that mangled the sentinel placeholders (core preserved)
    analysis = (f"The client {P('EMAIL',1)} called CONFIDE_PHONE_0001 on "
                f"[CONFIDE PHONE 0001]; see {P('DATE',1)}.")
    restored, summary = rehydrate.rehydrate_text(analysis, mapping)
    assert flat[P("EMAIL", 1)] in restored
    assert flat[P("PHONE", 1)] in restored
    # at least the email/phone restored
    assert summary["restored"] >= 2


def test_unknown_placeholder_reported_unmatched(tmp_path):
    _, _, mapping = _anon(tmp_path)
    flat = C.map_lookup(mapping)
    analysis = f"Known {P('EMAIL',1)} but hallucinated {P('PERSON',9)}."
    restored, summary = rehydrate.rehydrate_text(analysis, mapping)
    assert flat[P("EMAIL", 1)] in restored
    assert P("PERSON", 9) in restored  # left in place
    assert summary["unmatched"] >= 1


def test_process_writes_restored_file_counts_only(tmp_path, capsys):
    res, green, mapping = _anon(tmp_path)
    analysis = tmp_path / "analysis.md"
    analysis.write_text(green, encoding="utf-8")
    out = rehydrate.process(str(analysis), map_path=str(tmp_path / "session.map.json"))
    restored_file = tmp_path / "analysis.restored.md"
    assert restored_file.exists()
    assert out["restored_path"] == str(restored_file)
    # restored file has the originals
    rtext = restored_file.read_text(encoding="utf-8")
    assert "jane.doe@example.com" in rtext
    # stdout never echoes the PII, only counts
    captured = capsys.readouterr().out
    assert "jane.doe@example.com" not in captured
    assert "restored" in captured.lower()


def test_auto_find_sibling_map(tmp_path):
    _, green, _ = _anon(tmp_path)
    analysis = tmp_path / "session.green.md"  # sibling of session.map.json
    out = rehydrate.process(str(analysis))  # no --map; auto-find
    assert out["restored"] >= 2
