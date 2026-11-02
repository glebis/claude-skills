# Cover configuration

`assets/example.json` is the latest approved composition, expressed as editable geometry. Coordinates use a 1200 px square canvas; graph nodes use a 980 × 520 viewbox.

- `title`: two lines. `title.first` is Manrope; `title.emphasis` is EB Garamond Italic. Sizes and colours are configurable.
- `graph`: `x`, `y`, `width`, `height`, `rotation` in CSS degrees (negative = counterclockwise). Default final rotation is −20°, after a −25° version and a 5° clockwise adjustment.
- `nodes`: unique `id`, centre `x`/`y`, `size`, shape `circle|square|triangle`, ink `black|red`. Optional `label` appears beneath a node; labelled graphs need more space.
- `edges`: pairs of existing node IDs. Deduplicate undirected edges. These relationships are illustrative unless built from resolved source links.
- `footer`: `name`, `profile` (e.g. `/in/glebkalinin/`), `opacity` 0–1, `align` left/right. Set `enabled` false to omit. Default opacity .24 reflects the user's 20% visibility increase from .2.

Optional `canvas` stores width, height, format and background. Title additionally supports x/y/rotation/scale, first_font/emphasis_font, first_italic/emphasis_italic and first_color. Graph scale and footer x/y/rotation/scale are also saved by the editor.

The renderer exports `cover.png`; the builder writes `index.html`, a copy of `cover.json`, and local assets. All text is escaped. It renders local assets without fetching a remote service.

For aspect ratios beyond the three built-in presets or entirely different illustration arrangements, adapt a new template while preserving the original example. Do not force a complex labelled graph into this square cover template.

## Independent formats and PNG blocks

Saved `layouts` maps format keys to independent complete configurations. The active configuration remains at the top level for backward compatibility. Built-in formats are square, horizontal, vertical and story. Text offsets (`first_x/y`, `emphasis_x/y`) are relative to the headline layer.

`blocks` contains id/name/src, centre x/y, width/height, rotation and scale. Uploaded PNGs use embedded data URLs. Bundled blocks use relative `assets/` URLs. Preserve all layouts when editing saved JSON. `graph_kind: source` prevents decorative regeneration; otherwise Regenerate graph creates local random geometry without a model request.

## Text items

`texts` is an ordered array of id/text/x/y/font/size/weight/italic/bold/color/rotation/scale. Existing two-line `title` inputs migrate on load when `texts` is absent. Once present, `texts` controls rendering. Inline editing commits with Enter or blur; Shift+Enter inserts a new line. Selection outlines and resize handles are excluded from PNG exports. Multiple added text items remain independent for every format.

Font weight is numeric and independent per text item and format. Bundled faces support Manrope 200–800, EB Garamond 400/500 (regular and italic), and variable Paper Mono 100–900. The dropdown offers only supported weights. Legacy bold maps to 800 when available; otherwise 400.

The editor saves a local browser draft after edits and restores all format layouts on reload. Save design remains the portable JSON backup. Browser storage can be unavailable or full, especially with large embedded PNGs; the editor reports this and warns before leaving. Escape cancels inline editing. The mobile layout places the preview above the controls. Loading failures disable editing and provide Retry loading.

## Templates

The template picker offers Connected (mixed graph), Orbit (large circle with small satellites), Stepping stones (ascending squares), Constellation (small sparse nodes), Quiet crescent (PNG crescent and red accent), and Shape conversation (oval, triangle and square collage). Applying a template affects the active format only, preserves text content and fonts, and sets format-adapted default object/text positions and sizes. Undo restores the entire previous design. Templates persist in draft and portable JSON via `template`. Source-derived graphs preserve nodes and edges instead of replacing them with decorative geometry. PNG blocks retain the actual image aspect ratio.

Double-click a PNG block or graph to show a rotated bounding box with four corner handles. Dragging a handle scales uniformly around the opposite corner, preserving aspect ratio. Dragging inside still moves the layer. Selection UI never appears in exported PNGs. Undo and local draft recovery preserve artwork transforms.

Generation settings are separate from saved designs: provider keys stay in the generation server process. Generated artwork is inserted as a data-URL block, so it survives draft recovery and portable JSON export. Prompt and provider are sent only when Generate image is clicked.

The editor uses a compact tool rail, canvas and context panel. Text selection exposes a text-first toolbar with named weights. Transform fields provide coordinates, angle, scale and proportional W/H sizing; footer dimensions are unavailable. Mobile stacks canvas, tool navigation and controls. Shift+. toggles canvas-only editing, Escape restores controls, and typing fields suppress the shortcut.

Generation inserts the result automatically into the format where the request started, without changing the active tool. Undo reverses insertion. generatedImages stores the reusable gallery in portable JSON and the local draft. Reference selection sends that image to the chosen provider only upon generation: OpenAI uses image edits and Gemini receives inline image data.
