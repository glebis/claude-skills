#!/usr/bin/env python3
"""otfeat — deterministic OpenType feature inspector + CSS generator.

Commands:
  list <font.woff2|otf|ttf> [...]     List GSUB/GPOS features with descriptions.
  css --family NAME --features t1,t2[=N] [--selector SEL] [--class NAME]
                                      Emit CSS for the chosen features.

`css` prefers high-level font-variant-* properties where they exist and falls
back to font-feature-settings for the rest (both are emitted; the variant
properties win in supporting browsers and degrade gracefully).
"""
import argparse
import sys

TAG_INFO = {
    "calt": "Contextual alternates (Monaspace: texture healing)",
    "liga": "Standard ligatures",
    "dlig": "Discretionary ligatures",
    "case": "Case-sensitive forms (punctuation for ALL CAPS)",
    "frac": "Fractions (1/2 -> ½-style)",
    "numr": "Numerators", "dnom": "Denominators",
    "ordn": "Ordinals (1st, 2nd)",
    "subs": "Subscripts", "sups": "Superscripts", "sinf": "Scientific inferiors",
    "zero": "Slashed zero",
    "tnum": "Tabular figures", "pnum": "Proportional figures",
    "onum": "Oldstyle figures", "lnum": "Lining figures",
    "smcp": "Small caps", "c2sc": "Caps to small caps",
    "salt": "Stylistic alternates", "swsh": "Swashes", "titl": "Titling forms",
    "ital": "Italic forms", "kern": "Kerning", "locl": "Localized forms",
    "ccmp": "Glyph composition (required)", "aalt": "Access all alternates",
    "fina": "Final forms", "init": "Initial forms", "medi": "Medial forms",
    "fwid": "Full widths", "hlig": "Historical ligatures",
    # Monaspace stylistic sets (github.com/githubnext/monaspace)
    "ss01": "Ligatures: equals ===  !=  /=",
    "ss02": "Ligatures: comparison >=  <=",
    "ss03": "Ligatures: arrows ->  =>  ~>",
    "ss04": "Ligatures: markup </  />  </>",
    "ss05": "Ligatures: F# |>  <|",
    "ss06": "Ligatures: repeated ## ___",
    "ss07": "Ligatures: colons ::  :::",
    "ss08": "Ligatures: dots ..  ...  ..=",
    "ss09": "Ligatures: comparison chains >>= =<< <=>",
    "ss10": "Other tags: #! #(",
}

# tags with a high-level CSS property (preferred over font-feature-settings)
VARIANT_MAP = {
    "liga": ("font-variant-ligatures", "common-ligatures"),
    "dlig": ("font-variant-ligatures", "discretionary-ligatures"),
    "calt": ("font-variant-ligatures", "contextual"),
    "hlig": ("font-variant-ligatures", "historical-ligatures"),
    "smcp": ("font-variant-caps", "small-caps"),
    "c2sc": ("font-variant-caps", "all-small-caps"),
    "onum": ("font-variant-numeric", "oldstyle-nums"),
    "lnum": ("font-variant-numeric", "lining-nums"),
    "tnum": ("font-variant-numeric", "tabular-nums"),
    "pnum": ("font-variant-numeric", "proportional-nums"),
    "frac": ("font-variant-numeric", "diagonal-fractions"),
    "ordn": ("font-variant-numeric", "ordinal"),
    "zero": ("font-variant-numeric", "slashed-zero"),
    "subs": ("font-variant-position", "sub"),
    "sups": ("font-variant-position", "super"),
}


def list_features(paths):
    from fontTools.ttLib import TTFont
    for p in paths:
        f = TTFont(p, fontNumber=0, lazy=True)
        name = f["name"].getDebugName(4) or p
        tags = set()
        for table in ("GSUB", "GPOS"):
            if table in f:
                tags |= {r.FeatureTag for r in f[table].table.FeatureList.FeatureRecord}
        print(f"# {name} ({p})")
        for t in sorted(tags):
            desc = TAG_INFO.get(t) or (
                "Character variant" if t.startswith("cv") else "(no description)")
            print(f"  {t}  {desc}")
        print()


def emit_css(args):
    feats = []
    for item in args.features.split(","):
        item = item.strip()
        if not item:
            continue
        tag, _, val = item.partition("=")
        feats.append((tag, val or "1"))
    variant_props = {}
    low_level = []
    for tag, val in feats:
        if tag in VARIANT_MAP and val == "1" and not args.no_variant_props:
            prop, value = VARIANT_MAP[tag]
            variant_props.setdefault(prop, []).append(value)
        else:
            low_level.append(f'"{tag}" {val}' if val != "1" else f'"{tag}"')
    sel = args.selector or (f".{args.klass}" if args.klass else "body")
    lines = [f"{sel} {{"]
    if args.family:
        lines.append(f'  font-family: "{args.family}";')
    for prop, values in sorted(variant_props.items()):
        lines.append(f"  {prop}: {' '.join(values)};")
    if low_level:
        lines.append(f"  font-feature-settings: {', '.join(low_level)};")
    lines.append("}")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(prog="otfeat")
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("list")
    lp.add_argument("fonts", nargs="+")
    cp = sub.add_parser("css")
    cp.add_argument("--family", default=None)
    cp.add_argument("--features", required=True,
                    help="comma list, e.g. calt,ss03,tnum or cv01=2")
    cp.add_argument("--selector", default=None)
    cp.add_argument("--class", dest="klass", default=None)
    cp.add_argument("--no-variant-props", action="store_true",
                    help="emit only font-feature-settings")
    args = ap.parse_args()
    if args.cmd == "list":
        list_features(args.fonts)
    else:
        emit_css(args)


if __name__ == "__main__":
    sys.exit(main())
