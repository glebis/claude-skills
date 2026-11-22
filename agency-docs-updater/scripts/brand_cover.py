#!/usr/bin/env python3
"""Token-driven cover generator (thumbnail_style: "brand").

Reads a brand profile (brands/<name>.json) that points at a site's
design.tokens.json (DTCG), self-hosted fonts and reusable art assets, then
composes covers in any declared format (youtube / og / square).

Subcommands:
  brand_cover.py tokens   BRAND                       # print resolved CSS vars
  brand_cover.py prompt   BRAND --subject "..."       # brand-faithful image prompt
  brand_cover.py generate BRAND --subject "..." --out art.png [--dry-run]
        # nano-banana with kit references, then the brand's "generated" transforms
  brand_cover.py render   BRAND --meeting 01 --date 10.10.2026 \
        --hero "Работайте с агентами" --emphasis "над вашими задачами" \
        [--kicker "..."] [--topic "..."] [--composition auto|hero|program|...] \
        [--generated art.png] [--formats youtube,og] --out-prefix /path/NAME
        # writes NAME.youtube.jpg, NAME.og.png, ... and NAME.<fmt>.html
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from string import Template

SKILL = Path(__file__).resolve().parent.parent
BRANDS = SKILL / "brands"
TEMPLATE = SKILL / "templates" / "covers" / "token-cover.html"


# ── brand + tokens ────────────────────────────────────────────────────────
def load_brand(name):
    path = Path(name) if name.endswith(".json") else BRANDS / f"{name}.json"
    brand = json.loads(path.read_text(encoding="utf-8"))
    site = str(Path(os.path.expanduser(brand.get("site", "."))))

    def expand(v):
        if isinstance(v, str):
            return os.path.expanduser(v.replace("{site}", site))
        if isinstance(v, dict):
            return {k: expand(x) for k, x in v.items()}
        if isinstance(v, list):
            return [expand(x) for x in v]
        return v

    brand = expand(brand)
    brand["_tokens_raw"] = json.loads(Path(brand["tokens"]).read_text(encoding="utf-8"))
    brand["_tokens"] = flatten_tokens(brand["_tokens_raw"])
    return brand


def _fmt(value):
    if isinstance(value, dict) and "value" in value:
        return f'{value["value"]}{value.get("unit", "")}'
    if isinstance(value, list):
        return ", ".join(f'"{v}"' if " " in v else v for v in value)
    return str(value)


def flatten_tokens(node, prefix=()):
    """DTCG tree -> {"color.background": "#f3f0e8", ...} (skips $extensions)."""
    out = {}
    for key, val in node.items():
        if key.startswith("$"):
            continue
        if isinstance(val, dict) and "$value" in val:
            out[".".join(prefix + (key,))] = _fmt(val["$value"])
        elif isinstance(val, dict):
            out.update(flatten_tokens(val, prefix + (key,)))
    return out


def css_vars(tokens):
    return " ".join(f"--{k.replace('.', '-')}: {v};" for k, v in tokens.items())


def resolve_refs(obj, tokens):
    """Replace "{color.background}"-style token refs inside transform args."""
    if isinstance(obj, str):
        return re.sub(r"\{([a-zA-Z0-9_.-]+)\}", lambda m: tokens.get(m.group(1), m.group(0)), obj)
    if isinstance(obj, dict):
        return {k: resolve_refs(v, tokens) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_refs(v, tokens) for v in obj]
    return obj


def brand_ext(brand):
    return brand["_tokens_raw"].get("$extensions", {}).get("community.design-tokens.brand", {})


# ── composition choice ────────────────────────────────────────────────────
def pick_composition(topic, brand, headline=""):
    """Pick a composition name for a meeting.

    brand["topic_compositions"] maps composition -> keyword stems. Headline hits
    (hero + emphasis — what the cover says) count double; topic hits (summary
    headings, which mention everything) count once. Ties keep the profile's
    declared order; no hits -> "hero".
    """
    head, text = (headline or "").lower(), (topic or "").lower()
    best, best_score = "hero", 0
    for name, stems in brand.get("topic_compositions", {}).items():
        score = sum(2 * (s.lower() in head) + (s.lower() in text) for s in stems)
        if score > best_score:
            best, best_score = name, score
    return best


# ── copy rules ────────────────────────────────────────────────────────────
def apply_copy_rules(fields, rules):
    warnings = []
    if rules.get("strip_heading_full_stop", True):
        for k in ("hero", "emphasis"):
            v = fields.get(k, "")
            if v.endswith(".") and not v.endswith("..."):
                fields[k] = v.rstrip(".")
                warnings.append(f"stripped trailing full stop from {k}")
    for k, lim in (("hero", rules.get("max_hero_chars")), ("emphasis", rules.get("max_emphasis_chars"))):
        if lim and len(fields.get(k, "")) > lim:
            warnings.append(f"{k} is {len(fields[k])} chars (> {lim}) — may wrap to 3+ lines")
    return warnings


# ── generation ────────────────────────────────────────────────────────────
def build_prompt(brand, subject):
    ext, t = brand_ext(brand), brand["_tokens"]
    palette = ", ".join(f"{k.split('.', 1)[1]} {v}" for k, v in t.items()
                        if k in ("color.primary", "color.text", "color.background", "color.muted"))
    tpl = brand.get("generation", {}).get("prompt_template", "{subject}. {imageryStyle}")
    return tpl.format(subject=subject, imageryStyle=ext.get("imageryStyle", ""),
                      subjects="; ".join(ext.get("subjects", [])), palette=palette,
                      background=t.get("color.background", ""),
                      avoid="; ".join(ext.get("avoid", [])))


def generate(brand, subject, out, dry_run=False):
    from image_transforms import run_pipeline
    gen = brand.get("generation", {})
    nb = Path(os.environ.get("SKILLS_LOCAL_DIR", "~/.claude/skills")).expanduser() / "nano-banana/scripts/nano_banana.py"
    raw = Path(out).with_suffix(".raw.png")
    cmd = [sys.executable, str(nb), "--platform", "slides", "--model", gen.get("model", "pro"), "--no-metadata"]
    for ref in gen.get("references", []):
        cmd += ["--reference", brand["assets"][ref]]
    if dry_run:
        cmd.append("--dry-run")
    cmd += [build_prompt(brand, subject), str(raw)]
    subprocess.run(cmd, check=True)
    if dry_run:
        return None
    steps = resolve_refs(brand.get("transforms", {}).get("generated", []), brand["_tokens"])
    return run_pipeline(raw, out, steps)


# ── render ────────────────────────────────────────────────────────────────
def layers_html(brand, comp_name, slots, fmt="youtube"):
    """Layers use left/width + top OR bottom (bottom lets a cutout bleed off-canvas);
    optional opacity, blend, rotate, z, fade_bottom (% of height).
    A layer may carry "by_format": {"square": {...}} overrides."""
    comp = brand["compositions"][comp_name]
    html = []
    for i, L in enumerate(comp["layers"]):
        L = {**L, **L.get("by_format", {}).get(fmt, {})}
        L = {k: v for k, v in L.items() if v is not None}  # null in an override = unset
        src = slots.get(L["slot"]) if "slot" in L else brand["assets"][L["asset"]]
        if not src:
            sys.exit(f"composition '{comp_name}' needs slot '{L.get('slot')}' (pass --generated)")
        vert = f"bottom:{L['bottom']}%" if "bottom" in L else f"top:{L['top']}%"
        style = (f"left:{L['left']}%;{vert};width:{L['width']}%;z-index:{L.get('z', i + 1)};"
                 f"opacity:{L.get('opacity', 1)};mix-blend-mode:{L.get('blend', 'normal')};"
                 f"transform:rotate({L.get('rotate', 0)}deg)")
        if "fade_bottom" in L:  # soften a hard cutout edge that can't bleed off-canvas
            m = f"linear-gradient(to bottom, #000 {100 - L['fade_bottom']}%, transparent)"
            style += f";-webkit-mask-image:{m};mask-image:{m}"
        html.append(f'<img src="{Path(src).resolve().as_uri()}" style="{style}" alt="">')
    return "\n".join(html)


def render(brand, a):
    fields = {"hero": a.hero, "emphasis": a.emphasis or "", "kicker": a.kicker or ""}
    for w in apply_copy_rules(fields, brand.get("copy_rules", {})):
        print("copy:", w, file=sys.stderr)
    comp = pick_composition(a.topic or a.kicker, brand, f"{a.hero} {a.emphasis}") \
        if a.composition == "auto" else a.composition
    print(f"composition: {comp}", file=sys.stderr)
    # --label overrides the brand's meeting label: a second track in the same cohort
    # (GDA 01 Sunday advanced group) or another language (goal-driven-ai-en: "Session {meeting}")
    label = (a.label or brand.get("meeting_label", "Meeting {meeting}")).format(meeting=a.meeting)
    if a.date:
        label += f" · {a.date}"
    hero_len = max(len(fields["hero"]), len(fields["emphasis"]))
    size = "6.4vw" if hero_len <= 22 else "5.4vw" if hero_len <= 30 else "4.6vw"
    tpl = Template(Path(brand.get("template", TEMPLATE)).read_text(encoding="utf-8"))
    outputs = []
    renderer = Path(__file__).with_name("render_html.mjs")
    for fmt in a.formats.split(","):
        spec = brand["formats"][fmt]
        html = tpl.safe_substitute(
            lang=brand.get("lang", "ru"), fonts_css=Path(brand["fonts_css"]).resolve().as_uri(),
            token_vars=css_vars(brand["_tokens"]), wordmark=brand.get("wordmark", brand["name"]),
            label=label, hero_size=size,
            layers=layers_html(brand, comp, {"generated": a.generated}, fmt), **fields)
        ext = "png" if spec.get("type") == "png" else "jpg"
        page = Path(f"{a.out_prefix}.{fmt}.html")
        page.write_text(html, encoding="utf-8")
        out = Path(f"{a.out_prefix}.{fmt}.{ext}")
        subprocess.run(["node", str(renderer), str(page), str(out), str(spec["width"]),
                        str(spec["height"]), str(spec.get("quality", 92))], check=True,
                       stdout=subprocess.DEVNULL)
        outputs.append(out)
    return outputs


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["tokens", "prompt", "generate", "render"])
    p.add_argument("brand")
    p.add_argument("--subject"); p.add_argument("--out"); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--meeting", default="01"); p.add_argument("--date")
    p.add_argument("--hero"); p.add_argument("--emphasis"); p.add_argument("--kicker")
    p.add_argument("--topic"); p.add_argument("--composition", default="auto")
    p.add_argument("--label", help='meeting label template, e.g. "Продвинутая группа · {meeting}"')
    p.add_argument("--generated"); p.add_argument("--formats", default="youtube")
    p.add_argument("--out-prefix")
    a = p.parse_args()
    sys.path.insert(0, str(Path(__file__).parent))
    brand = load_brand(a.brand)
    if a.cmd == "tokens":
        print(css_vars(brand["_tokens"]).replace("; ", ";\n"))
    elif a.cmd == "prompt":
        print(build_prompt(brand, a.subject or "abstract composition"))
    elif a.cmd == "generate":
        print(generate(brand, a.subject, a.out, a.dry_run))
    else:
        if not (a.hero and a.out_prefix):
            p.error("render needs --hero and --out-prefix")
        for o in render(brand, a):
            print(o)


if __name__ == "__main__":
    main()
