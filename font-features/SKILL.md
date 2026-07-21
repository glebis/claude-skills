---
name: font-features
description: This skill should be used when inspecting or applying advanced OpenType features of a font (woff2/otf/ttf) — ligatures, stylistic sets (ss01–ss20), character variants (cvXX), texture healing, slashed zero, tabular/oldstyle figures, fractions, small caps, case-sensitive forms — and generating the CSS to enable them. Interviews the user via cenno to pick features. Triggers on "OpenType features", "font features", "stylistic sets", "ligatures", "texture healing", "tabular figures", "what can this font do".
---

# Font Features (OpenType → CSS)

Inspect a font's real OpenType feature inventory and generate CSS to enable chosen features. Never guess what a font supports — always run `scripts/otfeat.py list` first; only features present in the dump may be offered or enabled.

Requires `fontTools` (`pip install fonttools` if missing).

## Workflow

1. **Inspect** the actual font files in the project:
   ```bash
   python3 <skill-dir>/scripts/otfeat.py list path/to/Font-Regular.woff2 [more fonts...]
   ```
   Output lists each font's GSUB/GPOS tags with human descriptions (Monaspace stylistic sets are described precisely; unknown `cvXX` are labelled generically).

2. **Interview the user via cenno** (`mcp__cenno__ask_user`, or `ask_sequence` for several questions). Offer ONLY features found in step 1, grouped sensibly, with a recommendation. Typical question set:
   - Coding ligatures: which sets? (arrows ss03, colons ss07, comparison ss02...) — for code samples only, usually off for prose
   - Numerals: tabular (`tnum`) for tables/timers, oldstyle (`onum`) for prose, slashed zero (`zero`)
   - Texture healing (`calt`) — for Monaspace, recommend ON everywhere
   - Caps: `case` for uppercase labels/buttons, `smcp` if present
   Use `input: {kind: "choice"}` with a text option, mark optional questions low-urgency, and respect a "skip" answer.

3. **Generate CSS** deterministically:
   ```bash
   python3 <skill-dir>/scripts/otfeat.py css --family "Monaspace Neon" \
     --features calt,liga,tnum,case --class prose
   # cvXX with a value: --features cv01=2
   ```
   High-level `font-variant-*` properties are preferred automatically (they cascade and combine better); remaining tags fall back to `font-feature-settings`. `--no-variant-props` forces the low-level form only.

4. **Apply**: paste the block into the project stylesheet; scope per element role (e.g. `tnum` on tables/stat tiles only, ligature sets on `code` only). Verify in a browser with real content.

## Gotchas

- `font-feature-settings` is all-or-nothing per declaration — a second declaration on a nested element REPLACES the inherited list; repeat the full list. This is the main reason to prefer `font-variant-*`.
- CSS accepts any tag, browsers silently ignore ones the font lacks — which is why step 1 is mandatory (e.g. Monaspace has NO `tnum`/`zero`/`smcp`; it's a monospace family and zero is already slashed).
- Stylistic-set meanings are font-specific; never reuse Monaspace's ss-descriptions for another family.
- A feature tag being present does not mean it covers the glyphs assumed: dump the actual GSUB substitutions before writing demo copy (e.g. Monaspace's `case` only raises `: ¡ ¿ ‽` and combining accents — NOT quotes, brackets, or dashes).
- Texture healing needs `calt` AND ligatures left enabled; `font-variant-ligatures: none` kills it.
