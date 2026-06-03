#!/usr/bin/env python3
"""confide:view — build a self-contained interactive HTML that visualizes the
de-identification + restoration of a transcript.

Given an original text file (and optionally its <name>.map.json), it detects PII
with the shared local stack (default regex layer — offline-safe), assigns unique
reversible placeholders, and renders ONE standalone .html (inline CSS + JS, no
external/CDN deps) that lets you toggle between:

  - All       fully redacted (every PII span shown as its placeholder)
  - None      original (nothing masked)
  - Selected  mask only the PII types you check

Each PII span is a <mark class="pii TYPE" data-orig=... data-ph=...>, colored by
type, with original<->placeholder shown on hover. A legend + per-type counts and a
privacy banner are included.

PRIVACY: the HTML embeds REAL values (like a vault artifact). It is written LOCALLY,
a sibling .gitignore excludes *.view.html, and a banner marks it private. Never ship
it. stdout carries COUNTS ONLY — never PII values.

Usage:
    python3 view.py ORIGINAL.txt [--map MAP.json] [--layers regex,natasha,llm]
                    [--out DIR]
"""
import argparse
import html as _html
import json
import os
import sys

# Import the shared core via ../../../shared relative to this file (robust to cwd).
_HERE = os.path.dirname(os.path.abspath(__file__))
_SHARED = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "shared"))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)
import confide_core as core  # noqa: E402

# Stable TYPE -> color map (reused for CSS rules + legend swatches).
TYPE_COLORS = {
    "PERSON": "#ffb3ba",
    "LOCATION": "#bae1ff",
    "ORG": "#baffc9",
    "PHONE": "#ffdfba",
    "EMAIL": "#ffffba",
    "URL": "#e0baff",
    "ID": "#c9c9ff",
    "DATE": "#b5ead7",
    "MEDICATION": "#ffc8dd",
    "AGE": "#d8e2dc",
    "PROFESSION": "#fde2e4",
    "OTHER": "#dddddd",
}
_DEFAULT_COLOR = "#dddddd"


# --------------------------------------------------------------------- detection
def detect_spans(text, layers):
    """Run the requested local detection layers, merge overlaps, return spans."""
    spans = []
    if "regex" in layers:
        spans += core.detect_regex(text)
    if "natasha" in layers:
        spans += core.detect_natasha(text)
    if "llm" in layers:
        spans += core.detect_llm(text)
    return core.merge_spans(spans)


def _spans_from_map(text, mapping):
    """Build spans by locating each mapped placeholder's ORIGINAL value in `text`,
    OR (when the text itself still holds placeholders) the placeholders. Used when a
    caller supplies a <name>.map.json so we render exactly its known PII. Accepts both
    the structured map schema and a legacy flat {placeholder: original} dict, and both
    the reserved sentinel ([CONFIDE_TYPE_NNNN]) and legacy ([TYPE_n]) placeholders."""
    import re
    spans = []
    # sentinel first ([CONFIDE_PERSON_0001]), then legacy ([PERSON_1])
    ph_sentinel = re.compile(r"\[" + re.escape(core._PH_PREFIX) + r"_([A-Z]+)_\d+\]")
    ph_legacy = re.compile(r"\[([A-Z]+)_\d+\]")
    flat = core.map_lookup(mapping)
    for ph, orig in flat.items():
        m = ph_sentinel.match(ph) or ph_legacy.match(ph)
        typ = m.group(1) if m else "OTHER"
        for needle in (orig, ph):
            i = text.find(needle)
            while i != -1:
                spans.append(core.Span(i, i + len(needle), needle, typ, "map"))
                i = text.find(needle, i + len(needle))
            if i == -1 and needle in text:
                break
    return core.merge_spans(spans)


# --------------------------------------------------------------------- HTML build
def build_html(text, name="view", layers=("regex",), mapping=None):
    """Return (html, merged_spans, mapping).

    If `mapping` is provided, spans are derived from it; otherwise PII is detected
    with the local layers and a fresh reversible map is built.
    """
    layers = list(layers)
    if mapping:
        flat = core.map_lookup(mapping)
        spans = _spans_from_map(text, mapping)
        # ensure each span has a placeholder we can show; reuse the supplied map by
        # matching value -> placeholder where possible, else mint one.
        val2ph = {v.lower(): k for k, v in flat.items()}
        rendered = _render_with_map(text, spans, flat, val2ph)
    else:
        spans = detect_spans(text, layers)
        rendered, mapping = _render_fresh(text, spans)

    by_type = {}
    for s in spans:
        by_type[s.type] = by_type.get(s.type, 0) + 1
    types_present = sorted(by_type)

    html = _assemble(name, rendered, by_type, types_present)
    return html, spans, mapping


def _render_fresh(text, spans):
    """Walk spans, mint unique coreferent placeholders, emit <mark> HTML.
    Returns (html_fragment, mapping)."""
    val2ph, counters, mapping = {}, {}, {}
    out, last = [], 0
    for s in spans:
        orig = text[s.start:s.end]
        key = (s.type, orig.lower())
        ph = val2ph.get(key)
        if ph is None:
            counters[s.type] = counters.get(s.type, 0) + 1
            ph = f"[{s.type}_{counters[s.type]}]"
            val2ph[key] = ph
            mapping[ph] = orig
        out.append(_esc(text[last:s.start]))
        out.append(_mark(s.type, orig, ph))
        last = s.end
    out.append(_esc(text[last:]))
    return "".join(out), mapping


def _render_with_map(text, spans, mapping, val2ph):
    """Emit <mark> HTML using a supplied map. For each span, show the original value;
    if the span text is itself a placeholder, the original comes from the map."""
    counters, minted = {}, {}
    out, last = [], 0
    for s in spans:
        surface = text[s.start:s.end]
        if surface in mapping:               # span IS a placeholder -> orig from map
            ph, orig = surface, mapping[surface]
        else:                                # span is an original value
            ph = val2ph.get(surface.lower())
            orig = surface
            if ph is None:
                key = (s.type, surface.lower())
                if key not in minted:
                    counters[s.type] = counters.get(s.type, 0) + 1
                    minted[key] = f"[{s.type}_{counters[s.type]}]"
                ph = minted[key]
        out.append(_esc(text[last:s.start]))
        out.append(_mark(s.type, orig, ph))
        last = s.end
    out.append(_esc(text[last:]))
    return "".join(out)


def _esc(s):
    return _html.escape(s, quote=True)


def _mark(typ, orig, ph):
    return (
        f'<mark class="pii {typ}" '
        f'data-type="{_esc(typ)}" '
        f'data-orig="{_esc(orig)}" '
        f'data-ph="{_esc(ph)}" '
        f'title="{_esc(orig)} ↔ {_esc(ph)}">{_esc(orig)}</mark>'
    )


def _css_rules(types_present):
    rules = [
        "body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#fafafa;color:#1a1a1a;}",
        ".banner{background:#7a0010;color:#fff;padding:10px 16px;font-weight:600;font-size:14px;}",
        ".wrap{max-width:920px;margin:0 auto;padding:20px;}",
        ".controls{position:sticky;top:0;background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:12px 16px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);}",
        ".controls h2{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:#666;margin:0 0 8px;}",
        ".states label{margin-right:14px;font-weight:600;cursor:pointer;}",
        ".legend{margin-top:12px;display:flex;flex-wrap:wrap;gap:10px;}",
        ".legend .item{display:flex;align-items:center;gap:6px;font-size:13px;}",
        ".legend .item label{display:flex;align-items:center;gap:6px;cursor:pointer;}",
        ".sw{display:inline-block;width:14px;height:14px;border-radius:3px;border:1px solid rgba(0,0,0,.2);}",
        "#transcript{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:20px;white-space:pre-wrap;line-height:1.7;font-size:15px;}",
        "mark.pii{border-radius:3px;padding:0 2px;cursor:help;}",
        "mark.pii.masked{font-family:ui-monospace,Menlo,monospace;font-size:.92em;background:#222!important;color:#eee;}",
    ]
    for typ in core.TYPES + ["OTHER"]:
        if typ in types_present:
            color = TYPE_COLORS.get(typ, _DEFAULT_COLOR)
            rules.append(f".pii.{typ}{{background:{color};}}")
    return "\n".join(rules)


def _legend_html(by_type, types_present):
    items = []
    for typ in types_present:
        color = TYPE_COLORS.get(typ, _DEFAULT_COLOR)
        n = by_type.get(typ, 0)
        items.append(
            f'<span class="item"><label>'
            f'<input type="checkbox" data-type-toggle="{_esc(typ)}" checked> '
            f'<span class="sw" style="background:{color}"></span>'
            f'{_esc(typ)} <strong>{n}</strong></label></span>'
        )
    return "\n".join(items)


def _assemble(name, rendered, by_type, types_present):
    total = sum(by_type.values())
    css = _css_rules(types_present)
    legend = _legend_html(by_type, types_present)
    js = _JS
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex,noarchive">
<title>confide:view — {_esc(name)} (PRIVATE)</title>
<style>
{css}
</style>
</head>
<body>
<div class="banner">\U0001f512 PRIVATE — this file embeds REAL personal data (local vault artifact).
Do not share. Never shipped / committed. For local review only.</div>
<div class="wrap">
  <div class="controls">
    <h2>State</h2>
    <div class="states">
      <label><input type="radio" name="state" data-state="All"> <b>All</b> (fully redacted)</label>
      <label><input type="radio" name="state" data-state="None" checked> <b>None</b> (originals)</label>
      <label><input type="radio" name="state" data-state="Selected"> <b>Selected</b> (mask checked types)</label>
    </div>
    <h2 style="margin-top:12px">Legend &amp; counts &mdash; {total} PII spans</h2>
    <div class="legend">
{legend}
    </div>
  </div>
  <div id="transcript">{rendered}</div>
</div>
<script>
{js}
</script>
</body>
</html>
"""


# Inline JS: pure DOM, no deps. Exposes window.__setState / __setSelected for tests.
_JS = r"""
(function () {
  var marks = Array.prototype.slice.call(document.querySelectorAll('mark.pii'));
  var state = 'None';
  var selected = {}; // type -> bool (mask?) when in Selected mode

  function applyMark(m) {
    var orig = m.getAttribute('data-orig');
    var ph = m.getAttribute('data-ph');
    var type = m.getAttribute('data-type');
    var mask;
    if (state === 'All') mask = true;
    else if (state === 'None') mask = false;
    else mask = !!selected[type];
    m.textContent = mask ? ph : orig;
    if (mask) m.classList.add('masked'); else m.classList.remove('masked');
  }

  function render() { marks.forEach(applyMark); }

  function setState(s) { state = s; render(); }

  function setSelected(typesToMask) {
    selected = {};
    (typesToMask || []).forEach(function (t) { selected[t] = true; });
    state = 'Selected';
    // reflect into the radio + checkboxes so the UI stays consistent
    var r = document.querySelector('input[data-state="Selected"]');
    if (r) r.checked = true;
    document.querySelectorAll('input[data-type-toggle]').forEach(function (cb) {
      cb.checked = !!selected[cb.getAttribute('data-type-toggle')];
    });
    render();
  }

  // wire state radios
  document.querySelectorAll('input[name="state"]').forEach(function (r) {
    r.addEventListener('change', function () {
      if (r.checked) setState(r.getAttribute('data-state'));
    });
  });

  // wire per-type checkboxes: in Selected mode a CHECKED box masks that type
  document.querySelectorAll('input[data-type-toggle]').forEach(function (cb) {
    cb.addEventListener('change', function () {
      selected[cb.getAttribute('data-type-toggle')] = cb.checked;
      var sel = document.querySelector('input[data-state="Selected"]');
      if (sel) sel.checked = true;
      state = 'Selected';
      render();
    });
  });

  // expose for tests / programmatic control
  window.__setState = setState;
  window.__setSelected = setSelected;

  render();
  window.__VIEW_OK__ = true;
})();
"""


# --------------------------------------------------------------------- CLI
def _out_path(src, out_dir=None):
    base = os.path.splitext(os.path.basename(src))[0]
    d = out_dir or os.path.dirname(os.path.abspath(src))
    return os.path.join(d, base + ".view.html")


def _ensure_gitignore(directory):
    """Write/extend a sibling .gitignore so the private artifact is never committed."""
    gi = os.path.join(directory, ".gitignore")
    needed = ["*.view.html", "*.map.json"]
    existing = ""
    if os.path.exists(gi):
        existing = open(gi, encoding="utf-8").read()
    add = [p for p in needed if p not in existing]
    if add:
        with open(gi, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("# confide:view — private artifacts (embed real PII)\n")
            f.write("\n".join(add) + "\n")
    return gi


def _load_map(src, explicit):
    path = explicit
    if not path:
        cand = os.path.splitext(os.path.abspath(src))[0] + ".map.json"
        if os.path.exists(cand):
            path = cand
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build an interactive de-id visualization HTML (LOCAL/private).")
    ap.add_argument("input", help="original text file (.txt/.md)")
    ap.add_argument("--map", help="path to <name>.map.json (auto-detected next to input if omitted)")
    ap.add_argument("--layers", default="regex",
                    help="comma list of detection layers (default: regex, offline-safe)")
    ap.add_argument("--out", help="output directory (default: next to the input)")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.input):
        print(f"error: not a file: {args.input}", file=sys.stderr)
        return 2

    with open(args.input, encoding="utf-8") as f:
        text = f.read()
    layers = [x.strip() for x in args.layers.split(",") if x.strip()]
    mapping = _load_map(args.input, args.map)

    name = os.path.splitext(os.path.basename(args.input))[0]
    html, spans, used_map = build_html(text, name=name, layers=layers, mapping=mapping)

    out_path = _out_path(args.input, args.out)
    out_dir = os.path.dirname(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    _ensure_gitignore(out_dir)

    # COUNTS ONLY to stdout — never PII values.
    by_type = {}
    for s in spans:
        by_type[s.type] = by_type.get(s.type, 0) + 1
    print(f"wrote {out_path}")
    print(f"PII spans: {len(spans)} | by type: {json.dumps(by_type, sort_keys=True)}")
    print("PRIVATE: this HTML embeds real values — local only, gitignored, do not share.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
