# Reel spec (JSON)

```json
{
  "project": "My Reels",                               // optional: open or create
  "timeline": "Small habits — v1",
  "style": "godard-riso",                              // preset name or path to a style JSON
  "tokens": "design.tokens.json",                      // optional DTCG tokens overlaid on the style
  "lang": "en",                                        // typesetting glue rules (ru|en)
  "workdir": "reel-work",                              // relative to the spec
  "music": {"path": "~/Downloads/track.wav", "start": 11.32, "volume_db": -3},   // start omitted = first downbeat ≥ min_start
  "bars": [2,3,3,2,2,2,3],                             // optional; otherwise auto from reading load
  "max_seconds": 50,
  "end_card": {"text": "GOAL-DRIVEN AI", "ms": 1200},
  "sfx_prompts": {"hit-accent": ["deep 808 drop", 1.3]},   // optional overrides of the transition kit
  "scenes": [
    {"card": "WEEK 01", "label": "12 October 2026",
     "context": "We started with one question:",
     "text": "why do good intentions fade by Wednesday?", "quote": false,
     "art": "art/01-candle-a.png", "art_aspect": 1.0,
     "art_layout": {"cx": 0.63, "cy": 0.71, "w": 0.86, "rot": [-9, -5], "from": [1, 0]},
     "sfx": "match striking, candle wick catching"}
  ]
}
```

- `context` = editorial line (sans, ink). `text` = emphasis/quote (serif italic, style quote colour). Quotes carry «» in the text itself.
- `card` = theme word on the colour card (≥ 0.6 s); `label` = small line under it (dates).
- `art` should already be alpha (scripts/art.py). `art_layout.from`: [dx,dy] slide direction, [0,0] = grow.
- Missing `music` → fixed `scene_seconds` (default 6 s, longer if reading load needs it).
- See `assets/examples/small-habits.json` for a full example (art/music paths are placeholders).
