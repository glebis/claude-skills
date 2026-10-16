# Styles

A style = one JSON in `assets/styles/` (schema = the presets). Resolve and check: `python3 scripts/style.py <name> [--tokens file]`.

| preset | look | cards | art | film |
|---|---|---|---|---|
| godard-riso | paper, riso red, Manrope Light + red EB Garamond italic | red/ink wipes, 0.6 s word | chaotic collage, slides | gate weave |
| calm-editorial | paper, black only, Helvetica Neue + black Garamond italic | none (dissolves) | centred, slow rise, fades | none |
| swiss-kinetic | white/black/signal blue, Helvetica Neue Bold + italic | hard 120 ms horizontal slams | chaotic, slides | none |

## Making a new style
Copy the closest preset, change: `color` (paper, ink, accent, on_accent, muted), `fonts` (family + CSS weight [+italic]; `ps` to force a PostScript name), `type` (sizes in Palmier points; `natural_line_height` of the context font), `motion` (cubic-bezier, durations), `cards`, `context.entrance` (slide|fade), `quote` (color role, exit blur|fade), `art` (layout chaotic|calm, entrance slide|rise), `film`, `paper.grain_sd` (0 = flat).

## Design tokens (DTCG)
`--tokens design.tokens.json` maps: color.background→paper, text→ink, primary→accent, on-primary→on_accent, muted; font.display→context (weight.display) and card (weight.wordmark); font.editorial→quote (italic); font.label→label; lineHeight.heading→context line height; motion easing (also from `$extensions.*.motion.easing`) and hero/reveal/header durations. Brand rules in tokens (e.g. "do not animate opacity of linework", "no texture behind long text") override preset habits — check `$extensions` and tell the user about conflicts.
