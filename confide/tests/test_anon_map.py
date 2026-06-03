"""Offline tests for confide:anon reversible-map mode (force layers=['regex']).

Verifies the DEFAULT reversible behavior: anon writes a GREEN file with UNIQUE,
coreferent placeholders ([EMAIL_1], [PERSON_1]...) and a sibling <name>.map.json
that is the ONLY artifact containing originals. Asserts:
- green has no originals; placeholders are the unique [TYPE_n] form
- map.json contains the originals and round-trips
- same surface value -> same placeholder (coreference)
- map.json perms are 0600 and a .gitignore (*.map.json) is written in the out dir
- --no-map (style=typed_placeholder) writes NO map.json
"""
import json
import os
import stat
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "anon", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import anon  # noqa: E402
import confide_core as C  # noqa: E402

P = C.make_placeholder
CFG = {"layers": ["regex"]}

FIXTURE = (
    "Client jane.doe@example.com called +1-415-555-0198 last Tuesday. "
    "Reply to jane.doe@example.com. We met 15 March."
)
PLANTED = ["jane.doe@example.com", "+1-415-555-0198", "last Tuesday", "15 March"]


def test_default_writes_green_with_unique_placeholders_and_map(tmp_path):
    src = tmp_path / "session.md"
    src.write_text(FIXTURE, encoding="utf-8")
    res = anon.process_file(str(src), CFG)

    green = tmp_path / "session.green.md"
    mapp = tmp_path / "session.map.json"
    assert green.exists() and mapp.exists()
    assert res["map_path"] == str(mapp)

    gtext = green.read_text(encoding="utf-8")
    # no originals in green
    for leak in PLANTED:
        assert leak not in gtext, f"leaked into green: {leak}"
    # unique coreferent reserved-sentinel placeholders
    assert P("EMAIL", 1) in gtext
    assert P("PHONE", 1) in gtext

    # map.json is the structured schema; has the originals and round-trips
    mapping = json.loads(mapp.read_text(encoding="utf-8"))
    assert mapping["schema_version"] == C.MAP_SCHEMA_VERSION
    assert mapping["green_sha256"] == C.green_sha256(gtext)
    flat = C.map_lookup(mapping)
    assert flat[P("EMAIL", 1)] == "jane.doe@example.com"
    assert flat[P("PHONE", 1)] == "+1-415-555-0198"
    # every planted value lives somewhere in the map values
    mvals = set(flat.values())
    for leak in PLANTED:
        assert leak in mvals, f"missing from map: {leak}"


def test_same_value_same_placeholder(tmp_path):
    src = tmp_path / "s.md"
    src.write_text(FIXTURE, encoding="utf-8")
    anon.process_file(str(src), CFG)
    gtext = (tmp_path / "s.green.md").read_text(encoding="utf-8")
    # the duplicate email collapses to a single placeholder used twice
    assert gtext.count(P("EMAIL", 1)) == 2
    assert P("EMAIL", 2) not in gtext


def test_map_perms_are_0600(tmp_path):
    src = tmp_path / "s.md"
    src.write_text(FIXTURE, encoding="utf-8")
    anon.process_file(str(src), CFG)
    mode = stat.S_IMODE(os.stat(tmp_path / "s.map.json").st_mode)
    assert mode == 0o600, f"map perms {oct(mode)} != 0o600"


def test_gitignore_written_for_maps(tmp_path):
    src = tmp_path / "s.md"
    src.write_text(FIXTURE, encoding="utf-8")
    anon.process_file(str(src), CFG)
    gi = tmp_path / ".gitignore"
    assert gi.exists()
    gtxt = gi.read_text(encoding="utf-8")
    # all three local-only artifact globs must be covered
    for glob in ("*.map.json", "*.view.html", "*.restored.md"):
        assert glob in gtxt, f"missing gitignore glob: {glob}"


def test_cloud_folder_emits_warning(tmp_path, monkeypatch):
    """If the output dir looks cloud-synced, anon flags that the secret map would be
    uploaded. We point --out at a fake Dropbox path under tmp and check the warning."""
    src = tmp_path / "s.md"
    src.write_text(FIXTURE, encoding="utf-8")
    out = tmp_path / "Dropbox" / "sessions"
    out.mkdir(parents=True)
    res = anon.process_file(str(src), CFG, out=str(out))
    assert res["cloud_warning"] and "cloud-synced" in res["cloud_warning"]


def test_local_folder_no_cloud_warning(tmp_path):
    src = tmp_path / "s.md"
    src.write_text(FIXTURE, encoding="utf-8")
    res = anon.process_file(str(src), CFG)
    assert res["cloud_warning"] is None


def test_no_map_flag_writes_no_map(tmp_path):
    src = tmp_path / "s.md"
    src.write_text(FIXTURE, encoding="utf-8")
    res = anon.process_file(str(src), CFG, reversible=False)
    assert list(tmp_path.glob("*.map.json")) == []
    assert res["map_path"] is None
    gtext = (tmp_path / "s.green.md").read_text(encoding="utf-8")
    # falls back to non-unique typed placeholders
    assert "[EMAIL]" in gtext
    for leak in PLANTED:
        assert leak not in gtext


def test_stats_still_counts_only(tmp_path):
    src = tmp_path / "s.md"
    src.write_text(FIXTURE, encoding="utf-8")
    anon.process_file(str(src), CFG)
    sdata = json.loads((tmp_path / "s.stats.json").read_text(encoding="utf-8"))
    blob = json.dumps(sdata)
    for leak in PLANTED:
        assert leak not in blob
