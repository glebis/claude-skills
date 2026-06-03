#!/usr/bin/env python3
"""confide:audit — corpus-scale, STATS-ONLY PII audit over a folder of sessions.

Mirrors the real_session_eval privacy contract:
  - Reads real transcript text ONLY inside this process.
  - Emits ONLY aggregate statistics — span COUNTS by type/layer, per-session
    redaction-rate distribution, document lengths, and a coarse residual proxy.
  - It NEVER prints, logs, or writes any transcript substring, any detected PII
    value, or any original FILENAME. Per-file records are keyed by an anonymized
    id (own-00, own-01, ...) only. The output is safe to surface to a cloud agent;
    the raw PII never leaves the machine.

Runs the layered LOCAL detector stack from shared/confide_core.py over each file.
Default config uses the full stack; --layers narrows it (e.g. --layers regex for a
fully offline, deterministic pass). Audit a RED (raw) corpus to size the PII, or a
GREEN (already-redacted) corpus to check residual leakage.

Usage:
    python3 audit.py FOLDER [--list paths.txt] [--layers regex,natasha,llm]
                     [--out report.md] [--html]
"""
import argparse
import json
import os
import sys

# Import the shared core via ../../../shared relative to this file (robust to cwd).
_HERE = os.path.dirname(os.path.abspath(__file__))
_SHARED = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "shared"))
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)
import confide_core as core  # noqa: E402

INPUT_EXTS = (".md", ".txt")
# outputs of confide:anon we never want to (re)audit as raw inputs unless explicit.
_SKIP_SUFFIXES = (".green.md", ".stats.json")

# PRIVACY: only canonical labels may ever appear in output. Anything else is
# bucketed as OTHER so a stray value in a `type` field can never escape as a label.
ALLOWED_TYPES = set(core.TYPES) | {"OTHER", "UNKNOWN"}


def _safe_type(label):
    t = str(label).upper()
    return t if t in ALLOWED_TYPES else "OTHER"


def _force_local(cfg):
    """FORCE a local-only config so a RED-corpus scan can NEVER hit a cloud LLM.

    Audit runs over real (possibly un-redacted) transcripts, so it must never send
    text to a cloud engine. We strip any cloud engine / cloud flags and pin the
    engine to a local value regardless of what the user's config said."""
    cfg = dict(cfg)
    # any non-local engine (e.g. 'openai') is overridden to local Ollama
    if cfg.get("engine") != "ollama":
        cfg["engine"] = "ollama"
    # remove any cloud transport hints that could redirect the LLM layer off-box
    for k in ("llm_base_url", "openai_api_base", "api_base"):
        cfg.pop(k, None)
    priv = dict(cfg.get("privacy", {}))
    priv["local_only"] = True
    priv["cloud_apis"] = False
    cfg["privacy"] = priv
    return cfg


def build_config(layers=None, base=None):
    """Build a config dict; `layers` may be a comma string or a list. Defaults to
    the configured/full stack. ALWAYS forced local-only (audit may read RED data).
    Used by main() and by tests (layers='regex')."""
    cfg = dict(base) if base else core.load_config()
    if layers:
        if isinstance(layers, str):
            layers = [x.strip() for x in layers.split(",") if x.strip()]
        cfg = {**cfg, "layers": list(layers)}
    return _force_local(cfg)


def _length_bucket(n):
    """Bucket a doc length into a coarse range so an exact per-doc char count (a weak
    fingerprint / linkage signal) never appears in the report."""
    if n < 5000:
        return "0-5k"
    if n < 20000:
        return "5-20k"
    return "20k+"


_LENGTH_BUCKETS = ("0-5k", "5-20k", "20k+")


def _percentile(sorted_vals, q):
    """Linear-interpolated percentile q in [0,1] over a pre-sorted non-empty list."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return float(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)


def audit_paths(paths, cfg=None):
    """Audit each file in `paths`; return a counts-only aggregate dict.

    PRIVACY: never stores or returns any transcript substring, PII value, or
    filename. Per-file records use anonymized own-NN ids and carry counts/rates
    only. On any read/processing failure, only the index + exception CLASS name is
    kept (never the path or content).
    """
    cfg = cfg or core.load_config()

    per_file = []
    spans_by_type = {}
    spans_by_layer = {}
    rates = []
    total_chars = 0
    masked_chars_total = 0
    spans_total_all = 0
    residual_spans_total = 0
    length_hist = {b: 0 for b in _LENGTH_BUCKETS}
    errors = []

    for idx, p in enumerate(paths):
        # Exception-safe: a traceback must never echo the path/filename or content.
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
            res = core.anonymize(text, cfg)
        except Exception as e:  # noqa: BLE001 — class name only, never the path
            errors.append({"i": len(errors), "error": type(e).__name__})
            continue

        st = res["stats"]
        n = st["chars"]
        rate = st["redaction_rate"]
        doc_id = f"own-{len(per_file):02d}"

        # per-type / per-layer, with labels passed through _safe_type()
        pf_by_type = {}
        for raw_t, c in st.get("by_type", {}).items():
            t = _safe_type(raw_t)
            pf_by_type[t] = pf_by_type.get(t, 0) + c
            spans_by_type[t] = spans_by_type.get(t, 0) + c
        pf_by_layer = {}
        for lyr, c in st.get("by_layer", {}).items():
            pf_by_layer[lyr] = pf_by_layer.get(lyr, 0) + c
            spans_by_layer[lyr] = spans_by_layer.get(lyr, 0) + c

        # coarse residual proxy: spans still detectable in the redacted GREEN text.
        # On a RED corpus this is ~0; on a GREEN corpus it sizes leftover leakage.
        try:
            residual = core.anonymize(res["redacted_text"], cfg)["stats"]["spans_total"]
        except Exception:  # noqa: BLE001
            residual = 0

        masked = int(round(rate * n))
        total_chars += n
        masked_chars_total += masked
        spans_total_all += st["spans_total"]
        residual_spans_total += residual
        rates.append(rate)
        bucket = _length_bucket(n)
        length_hist[bucket] += 1

        # PRIVACY: per-doc length is bucketed (no exact char count — a weak fingerprint).
        per_file.append({
            "doc": doc_id,
            "length_bucket": bucket,
            "spans_total": st["spans_total"],
            "spans_by_type": pf_by_type,
            "spans_by_layer": pf_by_layer,
            "redaction_rate": rate,
            "residual_proxy": residual,
        })

    n_files = len(per_file)
    srt = sorted(rates)
    rate_dist = {
        "min": round(min(srt), 4) if srt else 0.0,
        "median": round(_percentile(srt, 0.5), 4) if srt else 0.0,
        "mean": round(sum(srt) / len(srt), 4) if srt else 0.0,
        "max": round(max(srt), 4) if srt else 0.0,
    }
    return {
        "privacy": "stats-only; no transcript text, PII values, filenames, or exact per-doc lengths emitted",
        "n_files": n_files,
        "n_errors": len(errors),
        "total_chars": total_chars,
        "mean_chars": round(total_chars / n_files, 1) if n_files else 0.0,
        "length_buckets": length_hist,
        "spans_total": spans_total_all,
        "spans_by_type": dict(sorted(spans_by_type.items())),
        "spans_by_layer": dict(sorted(spans_by_layer.items())),
        "overall_redaction_rate": round(masked_chars_total / total_chars, 4) if total_chars else 0.0,
        "redaction_rate": rate_dist,
        "residual_proxy": residual_spans_total,
        "layers": list(cfg.get("layers", core.DEFAULTS["layers"])),
        "per_file": per_file,
    }


def _bar(count, total, width=24):
    if total <= 0:
        return ""
    filled = int(round(width * count / total))
    return "█" * filled + "·" * (width - filled)


def render_report(agg):
    """Render the aggregate dict as a counts-only markdown report. Contains ZERO
    PII values, transcript substrings, or filenames — only own-NN ids and counts."""
    L = []
    L.append("# confide:audit — corpus PII stats")
    L.append("")
    L.append("> stats-only; no transcript text, PII values, or filenames in this report.")
    L.append("")
    L.append("## Corpus")
    L.append("")
    L.append(f"- files audited: **{agg['n_files']}**" +
             (f" ({agg['n_errors']} unreadable)" if agg.get("n_errors") else ""))
    L.append(f"- layers: `{', '.join(agg.get('layers', []))}`")
    lb = agg.get("length_buckets", {})
    L.append(f"- total chars (corpus): **{agg['total_chars']:,}** (mean/doc ~{agg['mean_chars']:,})")
    L.append(f"- doc-length buckets: " +
             " · ".join(f"{b}: {lb.get(b, 0)}" for b in _LENGTH_BUCKETS))
    L.append(f"- total PII spans detected: **{agg['spans_total']}**")
    L.append(f"- coarse residual proxy (spans still detectable post-redaction): "
             f"**{agg['residual_proxy']}**")
    L.append("")

    L.append("## Redaction rate (per-session distribution)")
    L.append("")
    d = agg["redaction_rate"]
    L.append(f"- overall (chars masked / total): **{agg['overall_redaction_rate']:.2%}**")
    L.append(f"- per-session — min {d['min']:.2%} · median {d['median']:.2%} · "
             f"mean {d['mean']:.2%} · max {d['max']:.2%}")
    L.append("")

    L.append("## Spans by type")
    L.append("")
    bt = agg["spans_by_type"]
    tot = sum(bt.values()) or 1
    L.append("| type | count | share |")
    L.append("|------|------:|-------|")
    for t, c in sorted(bt.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"| {t} | {c} | `{_bar(c, tot)}` {c / tot:.0%} |")
    L.append("")

    L.append("## Spans by layer")
    L.append("")
    bl = agg["spans_by_layer"]
    ltot = sum(bl.values()) or 1
    L.append("| layer | count | share |")
    L.append("|-------|------:|-------|")
    for lyr, c in sorted(bl.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"| {lyr} | {c} | `{_bar(c, ltot)}` {c / ltot:.0%} |")
    L.append("")

    L.append("## Per-session (anonymized ids)")
    L.append("")
    L.append("| id | length | spans | redaction | residual |")
    L.append("|----|--------|------:|-----------|---------:|")
    for pf in agg["per_file"]:
        L.append(f"| {pf['doc']} | {pf['length_bucket']} | {pf['spans_total']} | "
                 f"{pf['redaction_rate']:.2%} | {pf['residual_proxy']} |")
    L.append("")
    return "\n".join(L)


def render_html(agg):
    """Optional Tufte-ish, counts-only HTML dashboard. No PII, no filenames."""
    bt = agg["spans_by_type"]
    tot = sum(bt.values()) or 1
    bl = agg["spans_by_layer"]
    ltot = sum(bl.values()) or 1
    d = agg["redaction_rate"]

    def rows(mapping, total):
        out = []
        for k, c in sorted(mapping.items(), key=lambda kv: (-kv[1], kv[0])):
            pct = c / total
            out.append(
                f'<tr><td>{k}</td><td class="num">{c}</td>'
                f'<td class="barcell"><span class="bar" style="width:{pct*100:.1f}%"></span></td>'
                f'<td class="num">{pct:.0%}</td></tr>'
            )
        return "\n".join(out)

    pf_rows = "\n".join(
        f'<tr><td>{pf["doc"]}</td><td>{pf["length_bucket"]}</td>'
        f'<td class="num">{pf["spans_total"]}</td>'
        f'<td class="num">{pf["redaction_rate"]:.2%}</td>'
        f'<td class="num">{pf["residual_proxy"]}</td></tr>'
        for pf in agg["per_file"]
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>confide:audit — corpus PII stats</title>
<style>
  :root {{ --ink:#1a1a1a; --rule:#cfc9bd; --bar:#7a8b6f; --bg:#fdfcf8; }}
  body {{ background:var(--bg); color:var(--ink); max-width:48em; margin:3rem auto;
    padding:0 1.5rem; font:16px/1.55 "EB Garamond", Georgia, serif; }}
  h1 {{ font-weight:600; font-size:1.7rem; margin:.2rem 0; }}
  .note {{ color:#6b6256; font-style:italic; }}
  .kpis {{ display:flex; flex-wrap:wrap; gap:1.5rem; margin:1.5rem 0; }}
  .kpi {{ }}
  .kpi b {{ display:block; font:600 1.9rem/1 "Monaspace Argon", ui-monospace, monospace; }}
  .kpi span {{ color:#6b6256; font-size:.85rem; text-transform:uppercase; letter-spacing:.05em; }}
  table {{ border-collapse:collapse; width:100%; margin:1rem 0 2rem; }}
  th, td {{ text-align:left; padding:.3rem .6rem; border-bottom:1px solid var(--rule); }}
  th {{ font-weight:600; font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; color:#6b6256; }}
  .num {{ text-align:right; font-family:"Monaspace Argon", ui-monospace, monospace; }}
  .barcell {{ width:40%; }}
  .bar {{ display:inline-block; height:.7em; background:var(--bar); border-radius:1px; }}
  h2 {{ font-size:1.1rem; border-bottom:2px solid var(--ink); padding-bottom:.2rem; }}
</style></head>
<body>
  <h1>confide:audit — corpus PII stats</h1>
  <p class="note">Stats-only. No transcript text, PII values, or filenames appear in this dashboard.</p>
  <div class="kpis">
    <div class="kpi"><b>{agg['n_files']}</b><span>files</span></div>
    <div class="kpi"><b>{agg['total_chars']:,}</b><span>chars</span></div>
    <div class="kpi"><b>{agg['spans_total']}</b><span>PII spans</span></div>
    <div class="kpi"><b>{agg['overall_redaction_rate']:.1%}</b><span>redacted</span></div>
    <div class="kpi"><b>{agg['residual_proxy']}</b><span>residual</span></div>
  </div>
  <h2>Redaction rate (per session)</h2>
  <p>min {d['min']:.2%} · median {d['median']:.2%} · mean {d['mean']:.2%} · max {d['max']:.2%}</p>
  <h2>Spans by type</h2>
  <table><thead><tr><th>type</th><th class="num">count</th><th>share</th><th class="num">%</th></tr></thead>
  <tbody>{rows(bt, tot)}</tbody></table>
  <h2>Spans by layer</h2>
  <table><thead><tr><th>layer</th><th class="num">count</th><th>share</th><th class="num">%</th></tr></thead>
  <tbody>{rows(bl, ltot)}</tbody></table>
  <h2>Per session (anonymized ids)</h2>
  <table><thead><tr><th>id</th><th>length</th><th class="num">spans</th>
  <th class="num">redaction</th><th class="num">residual</th></tr></thead>
  <tbody>{pf_rows}</tbody></table>
</body></html>"""


def _gather_paths(folder, list_file):
    """Collect input file paths from a folder and/or a --list file. Skips confide
    output artifacts (*.green.md, *.stats.json)."""
    paths = []
    if folder:
        if os.path.isdir(folder):
            for root, _dirs, files in os.walk(folder):
                for fn in sorted(files):
                    if fn.endswith(_SKIP_SUFFIXES):
                        continue
                    if fn.lower().endswith(INPUT_EXTS):
                        paths.append(os.path.join(root, fn))
        elif os.path.isfile(folder):
            paths.append(folder)
    if list_file:
        with open(list_file, encoding="utf-8") as f:
            for line in f:
                p = line.strip()
                if p:
                    paths.append(p)
    # de-dup, preserve order
    seen, out = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Corpus-scale, stats-only PII audit (local).")
    ap.add_argument("folder", nargs="?", help="folder of .md/.txt sessions (or a single file)")
    ap.add_argument("--list", dest="list_file", help="file with absolute paths, one per line")
    ap.add_argument("--layers", help="comma list, e.g. regex,natasha,llm (default: config/full)")
    ap.add_argument("--out", default="audit-report.md", help="markdown report path (json sibling written too)")
    ap.add_argument("--html", action="store_true", help="also write a Tufte-ish HTML dashboard")
    args = ap.parse_args(argv)

    if not args.folder and not args.list_file:
        ap.error("provide a FOLDER and/or --list")

    cfg = build_config(layers=args.layers)
    paths = _gather_paths(args.folder, args.list_file)
    agg = audit_paths(paths, cfg)

    md = render_report(agg)
    out_md = args.out
    out_json = os.path.splitext(out_md)[0] + ".json"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md + "\n")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(agg, f, ensure_ascii=False, indent=2)
    if args.html:
        out_html = os.path.splitext(out_md)[0] + ".html"
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(render_html(agg))

    # console: COUNTS ONLY (basenames so an --out path can't surface personal info)
    a = agg
    print(f"[audit] files={a['n_files']} (errors={a['n_errors']}) total_chars={a['total_chars']}")
    print(f"[audit] spans total={a['spans_total']} by layer={a['spans_by_layer']}")
    print(f"[audit] spans by type={a['spans_by_type']}")
    print(f"[audit] overall redaction rate={a['overall_redaction_rate']:.2%} "
          f"(per-session min/median/mean/max="
          f"{a['redaction_rate']['min']:.1%}/{a['redaction_rate']['median']:.1%}/"
          f"{a['redaction_rate']['mean']:.1%}/{a['redaction_rate']['max']:.1%})")
    print(f"[audit] residual proxy (spans still detectable post-redaction)={a['residual_proxy']}")
    print(f"[audit] wrote {os.path.basename(out_md)} + {os.path.basename(out_json)}"
          + (f" + {os.path.splitext(os.path.basename(out_md))[0]}.html" if args.html else "")
          + " (stats only; no text/PII/filenames)")


if __name__ == "__main__":
    main()
