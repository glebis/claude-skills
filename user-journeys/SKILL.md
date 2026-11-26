---
name: user-journeys
description: Read a product (code, docs, UI screenshots) and produce a customer journey map (CJM) and user stories ranked as candidate scenes for a product video — every story has an action in the interface and a visible result. Outputs journeys.json, cjm.png, stories.png and stories.md. Use when planning a product video or demo of existing software ("what should the video show", "user journeys", "CJM", "user stories for the demo", "which scenes"), as step two of the interface-to-video chain (ui-tokens → user-journeys → ui-motion → raea-animate).
---

# user-journeys

A product video is a few user stories played back. Pick them from what the product really does, not from its
marketing: every control in a scene must exist in the code.

## Steps

1. **Inventory the real controls.**
   `python3 ~/.claude/skills/user-journeys/scripts/inventory.py OUT/inventory.json <templates, server, cli, docs...>`
   lists button labels, aria-labels, keyboard shortcuts, modes, `/api/` endpoints, CLI subcommands and doc headings.
   Read the README/HANDOVER/docs too: they say what is shipped and what is only planned. Look at 2–3 screenshots.
2. **Write `journeys.json`** (schema below) by hand — this is the thinking step:
   - one persona and one job ("When …, I want …, so …"), in the product's own terms;
   - 5–8 stages: what the person does, where (touchpoint, a real control or endpoint), how they feel, the pain;
     mark planned features as planned, never show them as shipped;
   - 5–8 stories, `As a …, I …` with **`action`** (one gesture in the UI: a click, a key, a typed line) and
     **`result`** (what changes on screen, visibly, within a second or two);
   - score each 0–3 on `visible` (can a viewer see the result without narration?), `unique` (would a competitor's
     video show the same thing?) and `short` (fits in its `seconds`). Rank by total; ties → the earlier stage.
   - `video_arc`: 3–5 story ids in journey order that fit the target length (sum of `seconds` ≈ length − 6 s for a
     hook and an end card). The top story goes first or becomes the hook.
3. **Render.** `python3 ~/.claude/skills/user-journeys/scripts/render.py OUT/journeys.json OUT --tokens tokens.json --fonts assets/fonts`
   → `cjm.png` (stages × doing/touchpoint/feeling/pain + the arc), `stories.png` (ranked, score bars), `stories.md`.
4. **Hand to ui-motion**: each story in the arc becomes one motion component (action → result).

## journeys.json

```json
{"product": "", "persona": "", "job": "",
 "stages": [{"name": "", "doing": "", "touchpoint": "", "feeling": "", "pain": ""}],
 "stories": [{"rank": 1, "id": "agree", "story": "As a …", "action": "", "result": "",
              "scores": {"visible": 3, "unique": 3, "short": 2}, "seconds": 6}],
 "video_arc": ["agree", "card", "apply"]}
```

Worked example: `~/raea/showreel/projects/prose-video/lecture/user-journeys/journeys.json` (prose-eval).
