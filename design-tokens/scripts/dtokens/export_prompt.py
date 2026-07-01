"""The prompt door: resolved DTCG tokens -> ready-to-paste generation prompts.

This bridges the design-token spine to downstream generation skills so a brand
defined once flows into images and reports without manual re-translation:

  - gpt-image-2  : uses its UNIQUE style presets (bauhaus, isometric, poster,
                   editorial, ...) to explore a brand across moods.
  - nano-banana  : leans on its UNIQUE strengths -- accurate in-image text
                   (`--model pro`) and reference-image style anchoring -- over
                   the shared preset set.
  - tufte        : emits a CSS :root theme that maps brand roles onto the exact
                   variable names /tufte-report consumes (--ink, --bg,
                   --spark-primary/secondary/tertiary, --status-*, --accent).

EVERYTHING HERE IS A SKILL CONVENTION, not DTCG. Role inference, the curated
preset choices, and the tufte variable mapping are generation aids layered on
top of the standard; they are labelled as such wherever surfaced.
"""

from . import brand_summary as _bs

# Curated presets per image tool. gpt-image-2 gets a spread of its *unique*
# presets so one brand yields visibly different moods; nano-banana gets the
# shared presets it renders well, and is steered to its text/reference strengths.
_GPT_IMAGE_PRESETS = ["editorial", "bauhaus", "isometric", "poster"]
_NANO_PRESETS = ["editorial", "risograph", "brutalist"]

_IMAGE_TARGETS = {
    "gpt-image-2": {
        "script": "scripts/gpt_image_2.py",
        "presets": _GPT_IMAGE_PRESETS,
        "extra_flags": "--quality medium",
        "confirm": "-y",  # gpt-image-2 prompts for cost; -y auto-confirms
        "note": "gpt-image-2 unique presets explore the brand across moods. "
                "Add --thinking medium for infographic/diagram subjects; "
                "--quality high for finals (~$0.21/img).",
    },
    "nano-banana": {
        "script": "scripts/nano_banana.py",
        "presets": _NANO_PRESETS,
        "extra_flags": "--model pro",
        "confirm": "",  # nano-banana has no cost-confirm flag
        "note": "nano-banana's edge is accurate in-image TEXT (--model pro) and "
                "style anchoring via --reference <img>. Prefer it when the brand "
                "name/wordmark must render legibly. Add --dry-run to preview the "
                "composed prompt without an API call.",
    },
}

# tufte-report CSS variable <- brand role. Order is the emission order.
_TUFTE_MAP = [
    ("--ink", "text", "near-black primary text"),
    ("--bg", "background", "warm-white background"),
    ("--spark-primary", "primary", "primary data stream / effort"),
    ("--spark-secondary", "success", "growth / health signal"),
    ("--spark-tertiary", "accent", "social / secondary stream"),
    ("--status-red", "danger", "alerts, negative trend"),
    ("--status-amber", "warning", "watch-level signal"),
    ("--status-green", "success", "healthy baseline"),
    ("--accent", "accent", "aside markers, flyout diamonds"),
]

# tufte-report's own defaults, used when the brand has no token for a role.
_TUFTE_DEFAULTS = {
    "--ink": "#1a1a1a", "--bg": "#fffff8",
    "--spark-primary": "#c45a28", "--spark-secondary": "#2a7a5a",
    "--spark-tertiary": "#5a5aaa", "--status-red": "#a02a2a",
    "--status-amber": "#c89000", "--status-green": "#2a7a3a", "--accent": "#a00",
}


def _slug(name):
    out = "".join(c.lower() if c.isalnum() else "-" for c in name)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "brand"


def _by_role(summary):
    """role -> hex. A token whose flattened name exactly equals the role
    (an explicit role alias like `text`/`background`) is authoritative and
    wins over tokens that merely contain a role keyword (`ink-900`); among
    keyword-only matches the first in token order wins."""
    roles = {}
    exact = {}
    for c in summary["colors"]:
        role = c["role"]
        if not role:
            continue
        if c["name"].lower() == role and role not in exact:
            exact[role] = c["hex"]
        elif role not in roles:
            roles[role] = c["hex"]
    roles.update(exact)
    return roles


# Canonical order so palette prose reads brand-first, then semantic states.
_ROLE_ORDER = ["primary", "accent", "text", "background", "success", "warning", "danger", "muted"]


def brand_clause(summary):
    """A compact, paste-ready description of the brand for an image subject."""
    parts = []
    roles = _by_role(summary)
    if roles:
        ordered = sorted(roles, key=lambda r: _ROLE_ORDER.index(r) if r in _ROLE_ORDER else 99)
        palette = ", ".join(f"{role} {roles[role]}" for role in ordered)
        parts.append(f"color palette: {palette}")
    elif summary["colors"]:
        palette = ", ".join(c["hex"] for c in summary["colors"][:5])
        parts.append(f"colors: {palette}")
    if summary["fonts"]:
        parts.append("typography: " + ", ".join(summary["fonts"][:3]))
    if summary["shape"]:
        shape_word = {"sharp": "sharp square corners", "soft": "softly rounded corners",
                      "rounded": "rounded corners", "pill": "fully rounded pill shapes"}
        parts.append(shape_word.get(summary["shape"], summary["shape"]))
    return ", ".join(parts)


def _image_prompts(summary, name, target, presets, platform, subject):
    cfg = _IMAGE_TARGETS[target]
    clause = brand_clause(summary)
    subject = subject or f"abstract brand mood board for {name}, geometric composition expressing the brand's character"
    slug = _slug(name)
    lines = [
        f"# {target} -- brand exploration for {name}",
        f"# {cfg['note']}",
        "# DO use the exact hex codes and fonts below. DON'T add logos, real",
        "#   brand names, or text unless the preset is text-oriented.",
        "",
    ]
    full_subject = f"{subject}, {clause}" if clause else subject
    tail = f" {cfg['confirm']}".rstrip()
    for preset in presets:
        out = f"{slug}-{preset}.png"
        lines.append(
            f"{cfg['script']} --preset {preset} --platform {platform} "
            f"{cfg['extra_flags']}{tail} \\\n"
            f"  \"{full_subject}\" \\\n"
            f"  {out}"
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def to_image_prompts(resolved, name, target, presets=None, platform="square", subject=None):
    if target not in _IMAGE_TARGETS:
        raise ValueError(f"unknown image target: {target}")
    summary = _bs.summarize(resolved)
    presets = presets or _IMAGE_TARGETS[target]["presets"]
    return _image_prompts(summary, name, target, presets, platform, subject)


def to_tufte_theme(resolved, name):
    """Emit a CSS :root block mapping brand roles -> tufte-report variables."""
    summary = _bs.summarize(resolved)
    roles = _by_role(summary)
    fonts = summary["fonts"]
    lines = [
        f"/* tufte-report theme for {name}",
        "   Maps brand token roles onto /tufte-report's CSS variables (SKILL",
        "   CONVENTION, not DTCG). Paste into the report's :root, or hand to",
        "   /tufte-report as the palette. Roles with no matching token fall back",
        "   to tufte-report's own defaults. */",
        ":root {",
    ]
    for var, role, comment in _TUFTE_MAP:
        hex_ = roles.get(role) or _TUFTE_DEFAULTS[var]
        provenance = "from token" if role in roles else "tufte default"
        lines.append(f"  {var}: {hex_};   /* {comment} ({provenance}) */")
    lines.append("}")
    if fonts:
        lines += [
            "",
            "/* tufte-report uses EB Garamond (text) + Monaspace Argon (numbers).",
            f"   Brand fonts available to swap in: {', '.join(fonts)}. */",
        ]
    return "\n".join(lines) + "\n"
