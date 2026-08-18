---
name: sketch
description: 'Open a Fabric.js-based SVG editor in the browser for collaborative visual prototyping. Codex writes and reads SVG through MCP tools while the user edits interactively. Changes sync in real-time via WebSocket. Use for wireframes, diagrams, schemes, UI mockups, and visual sketches. Triggers on "open sketch", "sketch canvas", "draw in browser", "fabric canvas".'
---

# Sketch - Collaborative SVG Canvas

## Description
Opens a Fabric.js-based SVG editor in the browser for collaborative visual prototyping. Codex can write and read SVG through MCP tools while the user edits interactively. Changes sync in real-time via WebSocket.

## Preflight
If the editor shows "disconnected" or WebSocket errors occur, stale server processes may be blocking. Run this before retrying:
```bash
pkill -f 'sketch-mcp-server/dist/index.js'
```
Then reconnect the MCP server (the next tool call will restart it). The server now auto-kills stale instances on startup, but orphaned processes from before this fix may still linger.

## Tools Available (via sketch-mcp-server)
- `sketch_open_canvas` - Open a named canvas (creates if new), launches browser editor
- `sketch_get_svg` - Read current SVG from a canvas
- `sketch_set_svg` - Replace entire canvas with new SVG
- `sketch_add_element` - Add SVG elements without clearing existing content
- `sketch_add_textbox` - Add a fixed-width text area (Textbox) with word wrapping
- `sketch_lock_objects` - Lock all current objects (non-selectable, non-movable)
- `sketch_unlock_objects` - Unlock all objects
- `sketch_save_template` - Save canvas as reusable JSON template (preserves Textbox widths + lock state)
- `sketch_load_template` - Load a saved JSON template into a canvas
- `sketch_list_templates` - List all saved templates
- `sketch_set_zoom` - Set zoom level (1.0 = 100%), optionally zoom toward a specific point
- `sketch_pan_to` - Pan the viewport so (x, y) is at the top-left
- `sketch_zoom_to_fit` - Fit all content in view with padding (call after drawing)
- `sketch_capture_screenshot` - Capture a PNG screenshot of the canvas (returns image for visual verification)
- `sketch_clear_canvas` - Clear canvas to blank state (use before streaming)
- `sketch_focus_canvas` - Bring canvas window to foreground
- `sketch_list_canvases` - List all active canvases
- `sketch_close_canvas` - Close a canvas and its browser tab

## Usage Patterns

### Quick sketch
1. `sketch_open_canvas` with a name
2. `sketch_set_svg` or `sketch_add_element` to draw
3. User edits in browser
4. `sketch_get_svg` to see changes

### Streaming (real-time build-up)
1. `sketch_open_canvas` with a name
2. `sketch_focus_canvas` to bring window to front
3. `sketch_clear_canvas` to start fresh
4. Call `sketch_add_element` multiple times -- each fragment appears instantly
5. User watches the UI build up in real-time

### Multiple canvases
Each canvas opens in its own browser tab. Use different names for different drawings.

## Default Visual Style

When generating prototypes, wireframes, diagrams, or schemes, use a minimalist style unless the user specifies otherwise:

- **Colors**: White/light gray background, black/dark gray for strokes and text. No fills on shapes unless semantically meaningful. Avoid decorative color.
- **Strokes**: Thin (1-2px), consistent weight. Use slightly heavier weight (2-3px) for emphasis only.
- **Typography**: Clean, sans-serif. Use size hierarchy for structure (e.g., 24px headings, 16px body, 12px labels). Black or `#333` text.
- **Shapes**: Simple rectangles, lines, circles. Rounded corners (rx=4-8) for UI elements. No drop shadows or gradients.
- **Layout**: Generous whitespace. Align elements to a grid. Clear visual hierarchy through size and spacing, not color.
- **Annotations**: Use thin arrows and small labels. Keep secondary to the content.

Only introduce color when it carries meaning (e.g., red for errors, green for success, blue for interactive elements) or when the user explicitly requests a colored/branded style.

### SVG tips
- Use standard SVG elements: `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<path>`, `<text>`, `<polygon>`, `<polyline>`
- Include `xmlns="http://www.w3.org/2000/svg"` on the root `<svg>` element
- Set `width` and `height` on the root SVG (default: 1200x800)
- Colors: use hex colors (`#ff0000`) -- avoid `rgba()` as Fabric.js SVG parser may not handle it
- Text: `<text x="100" y="100" font-size="24">Hello</text>`
- Images: `<image href="data:image/png;base64,..." width="200" height="200"/>`
- Avoid `<defs>`, `<linearGradient>`, `<filter>` -- Fabric.js has limited support for these
