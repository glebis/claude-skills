"""Tests for confide:view — the interactive de-id visualization HTML.

OFFLINE unit tests build the HTML from a synthetic fixture and assert on its
structure (the script forces layers=['regex'] so nothing touches the network or
loads models). A separate BROWSER test drives the produced HTML with system Chrome
via Playwright and asserts zero JS errors + working toggles.

Synthetic PII only — never reads real files.
"""
import json
import os
import re
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPT = os.path.join(_HERE, "..", "skills", "view", "scripts", "view.py")
sys.path.insert(0, os.path.join(_HERE, "..", "skills", "view", "scripts"))
import view as V  # noqa: E402

# A synthetic transcript with several PII types the regex layer detects offline.
FIXTURE = (
    "Client emailed marina@example.com on 15 January about the appointment.\n"
    "Call back at +44 7700 900123 or visit https://clinic.example.org today."
)


# --------------------------------------------------------------------- helpers
def _build():
    """Build HTML offline (regex layer only) and return (html, spans, mapping)."""
    return V.build_html(FIXTURE, name="fixture", layers=["regex"])


# --------------------------------------------------------------------- spans
def test_detects_expected_pii_spans():
    html, spans, mapping = _build()
    types = {s.type for s in spans}
    # regex layer should find at least email, date, phone, url
    assert {"EMAIL", "DATE", "PHONE", "URL"} <= types


# --------------------------------------------------------------------- originals + placeholders embedded
def test_html_embeds_original_values():
    html, spans, mapping = _build()
    assert "marina@example.com" in html
    assert "https://clinic.example.org" in html


def test_html_embeds_placeholders():
    html, spans, mapping = _build()
    # reversible map -> unique placeholders, each must appear in a data-ph attribute
    assert any(re.match(r"\[EMAIL_\d+\]", ph) for ph in mapping)
    for ph in mapping:
        assert ph in html


# --------------------------------------------------------------------- mark spans per type
def test_mark_span_per_detected_type():
    html, spans, mapping = _build()
    for typ in {"EMAIL", "DATE", "PHONE", "URL"}:
        assert f'<mark class="pii {typ}"' in html
    # each mark carries both data-orig and data-ph
    assert "data-orig=" in html and "data-ph=" in html


# --------------------------------------------------------------------- color per type
def test_types_are_colored():
    html, spans, mapping = _build()
    # a CSS rule colors each detected type via .pii.TYPE
    for typ in {"EMAIL", "DATE", "PHONE", "URL"}:
        assert re.search(r"\.pii\.%s\s*\{" % typ, html)


# --------------------------------------------------------------------- toggle controls (All/None/Selected)
def test_toggle_controls_present():
    html, spans, mapping = _build()
    for state in ("All", "None", "Selected"):
        assert state in html
    # radio-style state inputs
    assert 'data-state="All"' in html
    assert 'data-state="None"' in html
    assert 'data-state="Selected"' in html
    # per-type checkboxes for the Selected mode
    for typ in {"EMAIL", "DATE", "PHONE", "URL"}:
        assert f'data-type-toggle="{typ}"' in html


# --------------------------------------------------------------------- legend + counts
def test_legend_with_counts():
    html, spans, mapping = _build()
    assert "Legend" in html or "legend" in html
    # counts by type rendered
    by_type = {}
    for s in spans:
        by_type[s.type] = by_type.get(s.type, 0) + 1
    for typ, n in by_type.items():
        assert typ in html


# --------------------------------------------------------------------- self-contained / privacy
def test_self_contained_no_external_deps():
    html, spans, mapping = _build()
    assert "<style" in html and "<script" in html
    # no CDN / external resources
    assert "http://" not in html.split("<body")[0].replace("http://www.w3.org", "")
    assert "cdn" not in html.lower()
    assert "src=\"http" not in html


def test_privacy_banner_present():
    html, spans, mapping = _build()
    low = html.lower()
    assert "private" in low or "local" in low
    assert "do not share" in low or "never shipped" in low or "not for sharing" in low


def test_view_ok_flag_at_end():
    html, spans, mapping = _build()
    assert "window.__VIEW_OK__" in html and "true" in html


# --------------------------------------------------------------------- CLI writes file + sibling .gitignore
def test_cli_writes_view_html_and_gitignore(tmp_path):
    src = tmp_path / "session.txt"
    src.write_text(FIXTURE, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, _SCRIPT, str(src), "--layers", "regex"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    out = tmp_path / "session.view.html"
    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "<mark class=\"pii" in html
    # sibling gitignore protecting the artifact
    gi = tmp_path / ".gitignore"
    assert gi.exists()
    assert "*.view.html" in gi.read_text(encoding="utf-8")
    # stdout must not leak PII values (counts only)
    assert "marina@example.com" not in r.stdout
    assert "+1 415 555 0199" not in r.stdout


# --------------------------------------------------------------------- uses a provided map.json when present
def test_cli_uses_existing_map(tmp_path):
    src = tmp_path / "session.txt"
    src.write_text("Hello [PERSON_1].", encoding="utf-8")
    mp = tmp_path / "session.map.json"
    mp.write_text(json.dumps({"[PERSON_1]": "Marina"}), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, _SCRIPT, str(src), "--layers", "regex"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    html = (tmp_path / "session.view.html").read_text(encoding="utf-8")
    # the original value from the map should be visible in the rendering
    assert "Marina" in html


# --------------------------------------------------------------------- SKILL.md triggers
def test_skill_md_has_triggers():
    p = os.path.join(_HERE, "..", "skills", "view", "SKILL.md")
    txt = open(p, encoding="utf-8").read()
    assert "name: view" in txt
    for phrase in [
        "show me what was redacted",
        "visualize the de-id",
        "compare original and redacted",
        "highlight the PII",
        "view redaction diff",
        "see what rehydrate restored",
    ]:
        assert phrase in txt


# --------------------------------------------------------------------- BROWSER test (system Chrome, 0 JS errors)
def _have_browser_stack():
    try:
        root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
        return os.path.isdir(os.path.join(root, "playwright"))
    except Exception:
        return False


@pytest.mark.skipif(not _have_browser_stack(), reason="playwright not installed globally")
def test_browser_no_js_errors_and_toggles(tmp_path):
    src = tmp_path / "session.txt"
    src.write_text(FIXTURE, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, _SCRIPT, str(src), "--layers", "regex"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    html_file = tmp_path / "session.view.html"
    assert html_file.exists()

    driver = tmp_path / "drive.js"
    driver.write_text(_BROWSER_DRIVER, encoding="utf-8")
    root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    env = dict(os.environ, NODE_PATH=root)
    res = subprocess.run(
        ["node", str(driver), str(html_file)],
        capture_output=True, text=True, env=env, timeout=120,
    )
    assert res.returncode == 0, "browser driver failed:\nSTDOUT:%s\nSTDERR:%s" % (res.stdout, res.stderr)
    report = json.loads(res.stdout.strip().splitlines()[-1])
    assert report["view_ok"] is True
    assert report["mark_count"] >= 4
    assert report["js_errors"] == [], report["js_errors"]
    # None state shows originals; All state shows placeholders
    assert "marina@example.com" in report["text_none"]
    assert "[EMAIL_1]" in report["text_all"]
    # Selected with EMAIL only masks email but not the url
    assert "[EMAIL_1]" in report["text_selected_email"]
    assert "https://clinic.example.org" in report["text_selected_email"]


_BROWSER_DRIVER = r"""
const { chromium } = require('playwright');
(async () => {
  const file = process.argv[2];
  const errors = [];
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: true,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  const page = await browser.newPage();
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto('file://' + file, { waitUntil: 'load' });
  await page.waitForTimeout(300);

  const view_ok = await page.evaluate(() => window.__VIEW_OK__ === true);
  const mark_count = await page.evaluate(() => document.querySelectorAll('mark.pii').length);

  // helper to read the visible transcript text
  const readText = () => page.evaluate(() => document.getElementById('transcript').innerText);

  // None -> originals
  await page.evaluate(() => window.__setState('None'));
  await page.waitForTimeout(50);
  const text_none = await readText();

  // All -> placeholders
  await page.evaluate(() => window.__setState('All'));
  await page.waitForTimeout(50);
  const text_all = await readText();

  // Selected, only EMAIL masked
  await page.evaluate(() => window.__setSelected(['EMAIL']));
  await page.waitForTimeout(50);
  const text_selected_email = await readText();

  console.log(JSON.stringify({ view_ok, mark_count, js_errors: errors,
    text_none, text_all, text_selected_email }));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
"""
