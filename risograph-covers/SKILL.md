---
name: risograph-covers
description: Create and visually edit LinkedIn covers or presentation graphics using Gleb's paper, textured geometric shapes, Manrope, EB Garamond, and Paper Mono visual style. Supports decorative node graphs and source-grounded concept graphs.
---

# Risograph Covers

Produce an editable HTML cover and a inspected PNG. Use the bundled fonts and print textures to preserve this established style. The static renderer composes existing artwork. The optional local generation server connects the editor to OpenAI or Gemini image APIs. Use the available image-generation tool for genuinely new illustrations, then place the resulting artwork in this framework.

## Visual direction

- Warm paper `#f3f0e8`, black `#090909`, red `#d01920`.
- Large Manrope headline; emphasis in EB Garamond Italic, often red. No full stops after headers.
- Textured circles, squares, triangles; thin muted graph edges. Generous empty space. Minimal text; default no eyebrow or decorative document illustration.
- Graph may sit partly behind the heading, but inspect word legibility. Rotation affects the graph only, never the footer logo.
- Square 1200 × 1200, horizontal 1600 × 900, or vertical 1200 × 1500, or story 1080 × 1920. Right-aligned footer: name, middot, LinkedIn icon, profile path; make it optional.
- Opacity and transparency are inverses: 80% transparency = 0.2 opacity. “20% more visible” multiplies opacity by 1.2, rather than adding 20 percentage points. Follow explicit user correction.

## Create or revise

Read [references/config.md](references/config.md) for the editable input. Copy `assets/example.json` to the output directory, update wording and composition, and run:

```sh
python3 scripts/build.py /absolute/path/cover.json /absolute/path/output
node scripts/render.cjs /absolute/path/output
```

The generated `index.html` is a visual editor. Serve the output over localhost, for example `python3 scripts/serve.py OUTPUT --port 8899`, and open that URL in the browser. Direct file URLs can display the editor but prevent canvas PNG export due to browser origin restrictions. The automated renderer starts its own temporary loopback server and closes it afterwards.

In the editor: click text/artwork and drag it directly, double-click text to edit it inline, and drag the selected text’s corner handle to resize its font. Add text creates another independent item. Text items are numbered in sequence, each with its own font dropdown, weight, size, italic and colour controls. Choose a format, adjust layer rotation/scale, background, or footer visibility. The mono choice is the user-supplied Paper Mono; the footer uses it too. Each format keeps an independent layout, including text, fonts, transforms, footer and PNG blocks. New formats start from the original preset, not another format’s edits. Returning to a format restores its own work. Save design includes all format layouts. Save design downloads editable JSON; Open design restores it; Download PNG exports full canvas dimensions. Edits are automatically saved to a local browser draft and restored on reload; Save design downloads a portable backup. Draft storage failure is reported. Edits they do not overwrite the source JSON or original image. Keep the browser open when the user is editing. The template picker offers six graph and sculptural compositions with independent format-specific defaults. Applying a template preserves words, changes the active format only, and supports Undo. Artwork settings can regenerate a decorative graph locally, add bundled PNG blocks, or embed an uploaded PNG. Selected blocks support move, rotation, scaling and removal. PNG uploads stay in the local browser draft and saved design JSON. Regeneration reshuffles geometry; it is not an AI image-generation connection. Do not regenerate source-derived relationships as decorative data.

Resolve script paths against this skill. The builder copies fonts and artwork into the output so the HTML is portable. The renderer needs Playwright and Chrome (or a supplied executable). It searches normal module resolution, then `PLAYWRIGHT_MODULE`, then `npm root -g`; it does not install software automatically. Inspect the PNG through an image viewer before reporting completion. Look for clipped lettering, unreadable overlaps, accidental icon rotation, missing artwork/fonts, and footer visibility. Keep the prior approved version when revising.

For real vault graphs: inspect the chosen talk/source scope, select meaningful concepts, resolve actual links, and exclude generic maps, sources, people, frameworks unless requested. Include isolated relevant concepts rather than invent edges. Keep source paths and selection details in a separate local evidence file. Do not attribute the user's ideas to guest speakers based only on folder membership. Decorative graphs must be described as illustration, not real vault data.

Deliver the PNG with an absolute file link and inline preview. Do not publish the image or skill without authorization. Bundled asset provenance is in [references/assets.md](references/assets.md); check licences before redistributing the fonts or textures publicly.

## API image generation

Run scripts/serve.py to enable Generate image. It binds to loopback and keeps keys in process memory. Use OPENAI_API_KEY or GEMINI_API_KEY/GOOGLE_API_KEY in the server environment, or enter a session-only key in Generation settings. Never copy keys into design JSON, browser storage, reports or prompts. Only clicking Generate image sends a prompt and bills the chosen provider. The style checkbox appends the established risograph direction. The result is immediately inserted as a movable/resizable block into the request’s original format; the active tool stays open. Undo reverses insertion. Choose a prior generated image in the reference gallery to send it with the next request. Current typography remains editable. Reference-assisted generation uses OpenAI image edits or Gemini inline image input; it does not send the whole canvas automatically.

OpenAI uses standard square/landscape/portrait dimensions closest to the selected ratio. Gemini uses the requested ratio. Provider errors and absent output are shown without changing the design. Model availability and billing depend on the user's provider account. Tests can mock responses; do not claim a live paid generation succeeded without a real result.
