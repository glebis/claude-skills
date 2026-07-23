import json
import urllib.request

import pytest

from dtokens import annotate


@pytest.fixture
def imgdir(tmp_path):
    # 1x1 valid PNG
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d4944415478da63f8ffff3f0005fe02fea72d1ec80000000049454e44ae426082"
    )
    for name in ("b.png", "a.png"):
        (tmp_path / name).write_bytes(png)
    (tmp_path / "notes.txt").write_text("not an image")
    return tmp_path


def test_list_images_sorted_and_filtered(imgdir):
    assert annotate.list_images(imgdir) == ["a.png", "b.png"]


def test_merged_entries_carries_existing_annotations(imgdir):
    (imgdir / "refs.json").write_text(json.dumps(
        {"images": [{"file": "a.png", "take": ["palette"], "note": "hex source"},
                    {"file": "gone.png", "take": ["style"], "note": "stale"}]}))
    entries = annotate.merged_entries(imgdir)
    assert entries[0] == {"file": "a.png", "take": ["palette"], "note": "hex source"}
    assert entries[1] == {"file": "b.png", "take": [], "note": ""}  # fresh default
    assert all(e["file"] != "gone.png" for e in entries)


def test_save_manifest_validates_roles_and_files(imgdir):
    annotate.save_manifest(imgdir, [
        {"file": "a.png", "take": ["palette", "bogus-role"], "note": "n"},
        {"file": "../evil.png", "take": ["style"], "note": ""},
    ])
    saved = json.loads((imgdir / "refs.json").read_text())
    assert saved == {"images": [{"file": "a.png", "take": ["palette"], "note": "n"}]}


def test_annotator_html_embeds_entries_and_roles(imgdir):
    html = annotate.to_annotator_html(annotate.merged_entries(imgdir), voice=True)
    assert '"a.png"' in html and '"b.png"' in html
    assert '"voice": true' in html
    for role in annotate.ROLES:
        assert role in html


def test_server_serves_page_and_saves(imgdir, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    httpd, url = annotate.annotate(imgdir, open_browser=False, _block=False)
    try:
        page = urllib.request.urlopen(url).read().decode()
        assert "Reference annotator" in page and '"voice": false' in page
        body = json.dumps({"images": [{"file": "b.png", "take": ["composition"], "note": "layout"}]}).encode()
        req = urllib.request.Request(url + "save", data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req).read())
        assert resp["saved"].endswith("refs.json")
        saved = json.loads((imgdir / "refs.json").read_text())
        assert saved["images"] == [{"file": "b.png", "take": ["composition"], "note": "layout"}]
    finally:
        httpd.shutdown()
        httpd.server_close()
