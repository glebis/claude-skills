# Sketch - Collaborative SVG Canvas

## Description
Opens a Fabric.js-based SVG editor in the browser for collaborative visual prototyping. Claude can write and read SVG through MCP tools while the user edits interactively. Changes sync in real-time via WebSocket.

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

### SVG tips
- Use standard SVG elements: `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<path>`, `<text>`, `<polygon>`, `<polyline>`
- Include `xmlns="http://www.w3.org/2000/svg"` on the root `<svg>` element
- Set `width` and `height` on the root SVG (default: 1200x800)
- Colors: use hex colors (`#ff0000`) -- avoid `rgba()` as Fabric.js SVG parser may not handle it
- Text: `<text x="100" y="100" font-size="24">Hello</text>`
- Images: `<image href="data:image/png;base64,..." width="200" height="200"/>`
- Avoid `<defs>`, `<linearGradient>`, `<filter>` -- Fabric.js has limited support for these
