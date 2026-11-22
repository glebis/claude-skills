# Brand covers (thumbnail_style: "brand")

Token-driven covers for labs that have their own site + `design.tokens.json`. One
command composes the site's own art kit, fonts and colours into YouTube / OG /
square covers. No recolouring, no hand-edited HTML.

## Pieces

| File | Role | Change it when |
|---|---|---|
| `labs.json` → `brand`, `cover_formats` | Which profile a lab uses, which formats to render | New lab |
| `brands/<brand>.json` | Paths (site, tokens, fonts, assets), compositions, topic→composition keywords, generation prompt, transform pipelines, copy rules, formats | New look, new art, new format |
| `templates/covers/token-cover.html` | Layout only; every brand value arrives as `--token` CSS vars (`--color-primary`, `--font-editorial`, …) | Layout change. Per-brand override: `"template": "path.html"` in the profile |
| `scripts/brand_cover.py` | tokens / prompt / generate / render | Rarely |
| `scripts/image_transforms.py` | Ordered op pipeline for any raster (generated art, portraits, legacy overlays) | New op type (or use `shell` / `python` escape hatches) |
| `scripts/render_html.mjs` | file:// Playwright render; waits for fonts; falls back to installed Chrome headless | Never |

## Pipeline Step 3b (brand path)

```bash
S=${SKILLS_LOCAL_DIR}/agency-docs-updater/scripts
LAYOUT=$(python3 $S/lab_layout.py ${LAB_SLUG} --lab ${LAB_NUMBER} --meeting ${MEETING_NUMBER} --json)
BRAND=$(echo $LAYOUT | jq -r .brand); FORMATS=$(echo $LAYOUT | jq -r .cover_formats)

# 1. Copy (in the lab language, brand voice): hero = topic (≤ ~30 chars), emphasis = short
#    italic tail, kicker = one concrete line. No full stops on headings (auto-stripped).
# 2. Composition: --composition auto picks from topic keywords; override when the topic says
#    otherwise (hero | program | pricing | portrait | generated). Prefer kit art — it IS the brand.
python3 $S/brand_cover.py render $BRAND --meeting ${MEETING_NUMBER} --date DD.MM.YYYY \
  --hero "…" --emphasis "…" --kicker "…" --topic "<summary headings>" \
  --formats $FORMATS --out-prefix ${YOUTUBE_UPLOADER_DIR}/processed/thumbnails/${VIDEO_NAME}
# → ${VIDEO_NAME}.youtube.jpg (upload this), ${VIDEO_NAME}.og.png (optional page/social card)
```

Read the rendered image before uploading. Upload `${VIDEO_NAME}.youtube.jpg` with the
snippet in `thumbnail-guide.md` §5.

### Optional: a topic-specific generated layer

Only when no kit composition fits. The prompt is built from the tokens' brand extension
(`imageryStyle`, `subjects`, `avoid`, palette hex), and the kit PNGs are passed as
`--reference` images so the output matches the print texture.

```bash
python3 $S/brand_cover.py prompt   $BRAND --subject "two forms passing a task along a curve"   # inspect
python3 $S/brand_cover.py generate $BRAND --subject "…" --out /tmp/gen.png                  # nano-banana + transforms.generated
python3 $S/brand_cover.py render   $BRAND --composition generated --generated /tmp/gen.png …
```

`transforms.generated` keys out the paper colour (token ref `{color.background}`) and trims,
so the layer composites with `multiply` like the kit.

## Customising: what goes where

- **Move/resize art per format**: layer `by_format: {"square": {...}}`; `null` unsets a key.
- **Cutout with a hard edge**: anchor with `bottom: -1` so it bleeds off-canvas; where it
  can't (square), `fade_bottom: 18`.
- **Any raster transformation**: add steps to a `transforms.<slot>` list:
  `recolor`, `level`, `negate`, `key_out`, `trim`, `resize`, `grain`, `halftone`, raw
  `magick` args, `shell` (`{in}`/`{out}`), or `python` (`{"file": "x.py", "func": "f"}` →
  `f(in, out, **args)`). Test standalone:
  `image_transforms.py in.png out.png --pipeline '[{"op":"grain","amount":5}]'`.
  Token refs like `"{color.primary}"` resolve inside transform args.
- **Copy constraints**: `copy_rules` (full-stop stripping, length warnings).
- **New format** (e.g. Telegram 1280×640): add to `formats`, then list it in the lab's
  `cover_formats`. The template is vw/vh-based; aspect ≤ 1 switches to stacked layout.
- **New lab**: copy a profile, point `site`/`tokens`/`fonts_css`/`assets` at the new site,
  rewrite compositions to that site's art, add `"brand"` + `"thumbnail_style": "brand"` in
  `labs.json`.

## Respect the tokens' don'ts

Read `$extensions.community.design-tokens.brand` (`donts`, `avoid`) before adding
transforms. Goal-Driven AI explicitly says **do not recolour raster artwork to force flat
swatches** — so the legacy Claude Code orange-recolour step must never run on its art.
