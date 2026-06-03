"""Offline tests for confide:audit (force layers=['regex'] -> no network/models).

Synthetic PII only; never reads real files. confide:audit is a corpus-scale,
STATS-ONLY PII audit: it reads transcript text only in-process and emits ONLY
aggregates (counts by type/layer, per-session redaction-rate distribution, doc
lengths, a coarse residual proxy). It must NEVER print or write any transcript
substring, any PII value, or any original filename.

These tests assert:
  - aggregate per-type counts are correct (e.g. EMAIL == sum of planted emails),
  - n_files is correct and redaction-rate distribution fields are present,
  - PRIVACY: no planted PII value and no original filename leaks anywhere in the
    serialized report (json + markdown) — only anonymized own-NN ids.
"""
import json
import os
import sys

# import the skill script module (scripts/audit.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "audit", "scripts"))
import audit  # noqa: E402

# regex-only config: fully offline, deterministic
CFG = {"layers": ["regex"], "redaction_style": "typed_placeholder"}

# three synthetic fixtures with planted direct identifiers.
# we deliberately use distinctive, recognisable filenames + values so the privacy
# assertion would catch any leakage.
FIXTURES = {
    "alice-real-name-session.md": (
        "Client alice.smith@example.com called +1-415-555-0198 last Tuesday.\n"
        "Follow-up booked for 15 March."
    ),
    "bob-secret-2024.md": (
        "Bob wrote from bob.jones@mail.example.org and rang +44 20 7946 0958.\n"
        "Records at https://clinic.example.org/records were reviewed on 3/4/2024."
    ),
    "carol-notes.txt": (
        "No email here, just a phone +1-202-555-0147 and a date 01/02/2023."
    ),
}

# every literal PII value planted across the corpus (must NOT appear in any report)
PLANTED = [
    "alice.smith@example.com", "+1-415-555-0198", "last Tuesday", "15 March",
    "bob.jones@mail.example.org", "+44 20 7946 0958",
    "https://clinic.example.org/records", "3/4/2024",
    "+1-202-555-0147", "01/02/2023",
    "Bob", "alice", "carol",
]

# original filenames (must NOT appear — only own-NN ids are allowed)
FILENAMES = list(FIXTURES.keys())

# planted EMAIL count across the corpus (alice + bob; carol has none)
EXPECTED_EMAIL = 2


def _build_corpus(tmp_path):
    for name, body in FIXTURES.items():
        (tmp_path / name).write_text(body, encoding="utf-8")
    return [str(tmp_path / n) for n in FIXTURES]


def test_aggregate_per_type_counts(tmp_path):
    paths = _build_corpus(tmp_path)
    agg = audit.audit_paths(paths, CFG)
    assert agg["n_files"] == 3
    assert agg["spans_by_type"].get("EMAIL", 0) == EXPECTED_EMAIL
    # phones planted in all three files
    assert agg["spans_by_type"].get("PHONE", 0) >= 3
    # all counts are ints
    assert all(isinstance(v, int) for v in agg["spans_by_type"].values())
    assert all(isinstance(v, int) for v in agg["spans_by_layer"].values())


def test_redaction_rate_distribution_fields(tmp_path):
    paths = _build_corpus(tmp_path)
    agg = audit.audit_paths(paths, CFG)
    dist = agg["redaction_rate"]
    for k in ("min", "median", "mean", "max"):
        assert k in dist, f"missing redaction-rate field: {k}"
        assert isinstance(dist[k], (int, float))
    assert 0.0 <= dist["min"] <= dist["max"] <= 1.0
    assert "overall_redaction_rate" in agg
    # doc length stats present
    assert agg["total_chars"] > 0
    assert "mean_chars" in agg


def test_per_file_ids_are_anonymized(tmp_path):
    paths = _build_corpus(tmp_path)
    agg = audit.audit_paths(paths, CFG)
    ids = [pf["doc"] for pf in agg["per_file"]]
    assert ids == [f"own-{i:02d}" for i in range(len(FIXTURES))]
    # per-file records carry counts/rates only, never a path/name/text/exact-length key
    for pf in agg["per_file"]:
        assert set(pf).issubset({
            "doc", "length_bucket", "redaction_rate", "spans_by_type", "spans_by_layer",
            "spans_total", "residual_proxy",
        })
        # length is BUCKETED, never an exact char count
        assert "chars" not in pf
        assert pf["length_bucket"] in ("0-5k", "5-20k", "20k+")


def test_residual_proxy_present(tmp_path):
    paths = _build_corpus(tmp_path)
    agg = audit.audit_paths(paths, CFG)
    assert "residual_proxy" in agg
    assert isinstance(agg["residual_proxy"], (int, float))


def test_privacy_no_pii_or_filename_leak_in_report(tmp_path):
    """The ENTIRE report (json + markdown) must contain ZERO planted PII values
    and ZERO original filenames — only anonymized own-NN ids and counts."""
    paths = _build_corpus(tmp_path)
    agg = audit.audit_paths(paths, CFG)
    md = audit.render_report(agg)
    blob = json.dumps(agg, ensure_ascii=False) + "\n" + md

    for leak in PLANTED:
        assert leak not in blob, f"PII leaked into report: {leak}"
    for fname in FILENAMES:
        assert fname not in blob, f"filename leaked into report: {fname}"
        # also the stem without extension
        stem = os.path.splitext(fname)[0]
        assert stem not in blob, f"filename stem leaked into report: {stem}"
    # the anonymized ids ARE present
    assert "own-00" in blob
    # lengths are BUCKETED — no exact per-doc char count appears in any per-file record
    for pf in agg["per_file"]:
        assert "chars" not in pf and pf["length_bucket"] in ("0-5k", "5-20k", "20k+")
    # report exposes a bucket histogram, not exact min/max single-doc lengths
    assert "length_buckets" in agg
    assert "min_chars" not in agg and "max_chars" not in agg
    # each exact source length must NOT appear as a standalone per-doc figure in the md table
    md_lower = md.lower()
    assert "| length |" in md_lower  # bucketed column header, not "chars"


def test_render_report_is_markdown_counts_only(tmp_path):
    paths = _build_corpus(tmp_path)
    agg = audit.audit_paths(paths, CFG)
    md = audit.render_report(agg)
    assert isinstance(md, str) and md.strip()
    # mentions the key aggregate sections
    assert "EMAIL" in md  # a type label is fine; a value is not
    assert "redaction" in md.lower()
    assert "own-00" in md


def test_layers_override_forces_regex(tmp_path):
    """--layers handling: passing regex-only must not require network/models."""
    paths = _build_corpus(tmp_path)
    cfg = audit.build_config(layers="regex")
    assert cfg["layers"] == ["regex"]
    agg = audit.audit_paths(paths, cfg)
    assert agg["n_files"] == 3


def test_build_config_forces_local_only():
    """A cloud config must be overridden so a RED-corpus scan can never hit a cloud LLM."""
    cloud = {
        "engine": "openai",
        "llm_base_url": "https://api.openai.com",
        "privacy": {"local_only": False, "cloud_apis": True},
        "layers": ["regex", "llm"],
    }
    cfg = audit.build_config(base=cloud)
    assert cfg["engine"] == "ollama"            # cloud engine overridden
    assert "llm_base_url" not in cfg            # cloud transport stripped
    assert cfg["privacy"]["local_only"] is True
    assert cfg["privacy"]["cloud_apis"] is False


def test_missing_file_recorded_by_index_not_path(tmp_path):
    paths = _build_corpus(tmp_path)
    bad = str(tmp_path / "this-name-should-not-leak.md")
    agg = audit.audit_paths(paths + [bad], CFG)
    # the good files still counted
    assert agg["n_files"] == 3
    blob = json.dumps(agg, ensure_ascii=False) + "\n" + audit.render_report(agg)
    assert "this-name-should-not-leak" not in blob
