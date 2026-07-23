# Prompt-formulation fidelity tests (2026-07-21, draft quality, ~€0.5 spent)

Setup: fixed subject ("poster-style illustration of a human and an AI agent collaborating
over a design system"), 2 brands (ai-design carbon/krypton, Monaspace dark/coral),
2 models (gpt-image-2 `--draft`, Nano Banana 2 flash), 3 formulations. Palette adherence =
% of pixels within ΔRGB<60 of the brand palette (64×64 downsample).

| Formulation | gpt aid | gpt mon | nb aid | nb mon |
|---|---|---|---|---|
| A — comma clause (current brand_clause: "color palette: primary #… , typography: …") | 87 | 89 | 60 | 67 |
| B — strict constraint block ("Use ONLY these colors: …") | 88 | 86 | 88 | 58 |
| C — art-direction prose (mood + imagery style + hexes woven in with color words + Avoid list) | **96** | **90** | 81 | **71** |

## Findings

1. **C (extensions-enriched prose) wins overall** — best or near-best on both models and
   both brands, and produced the most on-brand *feel* (calm editorial, dot-grid, flat fills).
   This is the formulation the prompt door should emit by default; it requires the
   `$extensions` brand block (mood/imageryStyle/avoid/negativePrompt).
2. **gpt-image-2 is far more obedient than NB2 flash** (86–96 vs 58–88). It followed exact
   hexes, rendered clean monospace UI text, and honored "no gradients/no glows".
3. **Strict constraint blocks (B) are unreliable on Nano Banana** — best score on one brand
   (88), catastrophic on the other (58: background drifted to light paper, palette washed out).
   Don't use imperative blocks as the NB default.
4. **Naming the color in words next to the hex helps** ("soft violet (#BC9AFA)", "warm coral
   (#F5B8A5)") — models ground the word even when they misread the hex. → implemented in
   `brand_clause` via `_color_word()`.
5. NB2 flash sometimes renders the literal hex strings as visible labels in the image —
   fine for design-system posters, wrong for other subjects; note in prompts when unwanted.
6. Next (untested here): NB `--reference <brand image>` anchoring, `--model pro` for text-heavy
   subjects, and quality tiers above draft.
