# Lab-Style Thumbnail Generation (Lab 04+)

Replace the generic thumbnail from `process_video.py` with the lab-style dark editorial template. Do this BEFORE Step 4b (YouTube metadata update), or upload separately after.

## 1. Generate overlay image

```bash
~/ai_projects/claude-skills/nano-banana/scripts/generate_image.sh \
  "Abstract minimalist technical diagram: [topic-specific shape]. Thin line art on pure black background. No text, no words. Geometric, architectural blueprint style. Wireframe aesthetic." \
  /tmp/overlay-raw.png
```

Prompt patterns by meeting topic:
- Agents / MCP → "network graph with interconnected nodes radiating outward"
- Plan mode / terminal → "tree structure branching from root node, terminal cursor at top"
- Skills / context engineering → "layered concentric rings, knowledge graph"
- Live coding → "abstract code flow, brackets and indentation, architectural"

## 2. Inspect + recolor

Read the raw image (Read tool) to confirm background color before recoloring.

```bash
# If black-bg + light lines (usual case with "pure black background" prompt):
magick /tmp/overlay-raw.png \
  -fuzz 35% -fill '#e85d04' -opaque '#0080ff' \
  -fuzz 35% -fill '#e85d04' -opaque '#2090ff' \
  -fuzz 30% -fill '#e85d04' -opaque '#0070e0' \
  -fuzz 30% -fill '#e85d04' -opaque 'cyan' \
  -fuzz 30% -fill '#e85d04' -opaque '#4a90e2' \
  -fuzz 25% -fill '#e85d04' -opaque '#c0c0c0' \
  ${YOUTUBE_UPLOADER_DIR}/processed/thumbnails/${VIDEO_NAME}.overlay.png

# If white-bg + dark lines (fallback):
magick /tmp/overlay-raw.png -negate -level 15%,100% /tmp/overlay-neg.png
# ... then same color swap on /tmp/overlay-neg.png
```

If the whole image floods with orange, the background got color-swapped — revert and re-generate.

## 3. Edit the template

Edit `${YOUTUBE_UPLOADER_DIR}/templates/images/lab-meeting.html`:
- `<span class="top-left" data-field="title">` → `Claude Code Lab · XX`
- `<span class="top-right" data-field="subtitle">` → short session descriptor
- `<div class="meeting-label" data-field="meeting_number">` → `Meeting NN`
- `.topic-hero` three lines: short topic phrase, highlighted word, tail
- `.bullets` three one-line descriptions
- `<span data-field="date">` → `DD.MM.YYYY`

Keep topic-hero to 3 short lines — font sizes are fixed and long phrases overflow.

## 4. Render with Playwright

```bash
cat > /tmp/render-thumb.json <<EOF
{
  "template": "${YOUTUBE_UPLOADER_DIR}/templates/images/lab-meeting.html",
  "jobs": [
    {
      "name": "youtube_maxres",
      "width": 1280,
      "height": 720,
      "format": "jpeg",
      "quality": 95,
      "output": "${YOUTUBE_UPLOADER_DIR}/processed/thumbnails/${VIDEO_NAME}.jpg",
      "data": {
        "imagePath": "${YOUTUBE_UPLOADER_DIR}/processed/thumbnails/${VIDEO_NAME}.overlay.png",
        "imageAlt": "Meeting topic"
      }
    }
  ]
}
EOF
cd ${YOUTUBE_UPLOADER_DIR} && node scripts/render-thumbnails.mjs --config /tmp/render-thumb.json
```

Read the rendered `.jpg` to verify layout before uploading.

## 5. Upload thumbnail to YouTube

```bash
cd ${YOUTUBE_UPLOADER_DIR} && PYTHONPATH=. python3 - <<PY
from auth import get_authenticated_service
from googleapiclient.http import MediaFileUpload
youtube = get_authenticated_service()
media = MediaFileUpload("processed/thumbnails/${VIDEO_NAME}.jpg", mimetype="image/jpeg")
youtube.thumbnails().set(videoId="${VIDEO_ID}", media_body=media).execute()
PY
```

Style: dark editorial (#0f0f0f bg), EB Garamond italic hero text, JetBrains Mono labels, orange #e85d04 accents, overlay image at 0.3 opacity positioned at right 50% of frame.
