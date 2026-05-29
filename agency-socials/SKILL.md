---
name: agency-socials
description: Generate social media covers and assets for AGENCY Community events, meetups, and YouTube recordings. Use when creating event covers, YouTube thumbnails, or social posts for the AGENCY Community.
---

# AGENCY Community Social Assets Generator

Generate covers and visual assets for AGENCY Community events using the established design system.

## Design System

### Colors
- **Background**: `#0f0f0f`
- **Frame/borders**: `#2a2a2a`
- **Accent (orange)**: `#e85d04`
- **Primary text**: `#f0f0f0`
- **Secondary text**: `#999`
- **Muted text**: `#555` / `#444`
- **Grid lines**: `rgba(42,42,42,0.12)`

### Typography
- **Title/Header**: Geist Bold (700) — large, high-impact headlines
- **Metadata (top bar, bottom bar)**: JetBrains Mono — monospace, uppercase, letter-spaced
- **Speaker/people names**: EB Garamond — elegant serif
- **Handles/technical labels**: JetBrains Mono — monospace, orange accent

### Font loading
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&family=JetBrains+Mono:wght@300;400;500&display=swap&subset=cyrillic" rel="stylesheet">
<link rel="preload" href="https://cdn.jsdelivr.net/npm/geist@1.3.1/dist/fonts/geist-sans/Geist-Bold.woff2" as="font" type="font/woff2" crossorigin>
```
```css
@font-face {
  font-family: 'Geist';
  src: url('https://cdn.jsdelivr.net/npm/geist@1.3.1/dist/fonts/geist-sans/Geist-Bold.woff2') format('woff2');
  font-weight: 700;
}
```

### Layout Principles
- **Frame**: 1px solid `#2a2a2a` border, inset 12px from edges
- **Top bar**: JetBrains Mono, label left, date/time right (orange)
- **Bottom bar**: JetBrains Mono, metadata left and right, uppercase
- **Background grid**: subtle 40px grid lines
- **Accent line**: 3px orange bar below titles
- **Photos**: off-grid placement, fade to background on edges (left, bottom, top), slight scanline effect, fully desaturated `grayscale(1) contrast(1.1) brightness(0.95)`
- **Text**: left-aligned, can overlap photo slightly, large and readable at thumbnail size

### Minimum font sizes (must be readable at thumbnail)
- Top/bottom bar: 13-15px
- Speaker names: 28px+
- Handles: 20px+
- Titles: 62px+ (square), 76px+ (YouTube 16:9)

## Asset Sizes

### lu.ma Event Cover (square)
- **Dimensions**: 800×800px
- **Viewport**: `--viewport-size="800,800"`

### YouTube Thumbnail (16:9)
- **Dimensions**: 1280×720px
- **Viewport**: `--viewport-size="1280,720"`
- **Style reference**: matches `lab-meeting.html` template in youtube-uploader
- Uses same design tokens but wider layout

### Telegram Post Image
- **Dimensions**: 1080×1080px or 1280×720px

## Generation Process

1. Create HTML file at `~/Desktop/agency-{type}-cover.html`
2. Place speaker photo next to the HTML (same directory)
3. If speaker photo is in clipboard, save with: `osascript -e 'set theFile to POSIX file "/path/to/photo.png"' -e 'set theImage to the clipboard as «class PNGf»' -e 'set fileRef to open for access theFile with write permission' -e 'write theImage to fileRef' -e 'close access fileRef'`
4. Render at 2x scale for crisp text using Node.js script:
```js
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: W, height: H },
    deviceScaleFactor: 2
  });
  const page = await context.newPage();
  await page.goto('file:///path/to/html');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/output/path.png', fullPage: true });
  await browser.close();
})();
```
5. Review output, iterate on layout

## Template Structure

```html
<!-- Standard structure for all asset types -->
<body>
  <div class="bg-grid"></div>
  <div class="frame"></div>
  <div class="top-bar">
    <span class="top-left">{event type}</span>
    <span class="top-right">{date · time}</span>
  </div>
  <div class="photo-area"><!-- speaker photo with effects --></div>
  <div class="content">
    <div class="title">{headline with .highlight spans}</div>
    <div class="accent-line"></div>
    <div class="speaker"><strong>{name}</strong> <span class="handle">@{handle}</span></div>
  </div>
  <div class="bottom-bar">
    <span>{format · price}</span>
    <span>agency · community</span>
  </div>
</body>
```

## Photo Effects
- Fade from left edge: `linear-gradient(to right, #0f0f0f, transparent)` width 200px
- Fade from bottom: `linear-gradient(to top, #0f0f0f, transparent)` height 250px
- Fade from top: `linear-gradient(to bottom, #0f0f0f, transparent)` height 80px
- Scanlines: `repeating-linear-gradient(transparent, transparent 2px, rgba(0,0,0,0.05) 2px, rgba(0,0,0,0.05) 4px)`
- Orange accent border on left edge: `linear-gradient(transparent, #e85d04, transparent)` opacity 0.4
- Photo filters: `grayscale(1) contrast(1.1) brightness(0.95)` (fully B&W)
- Photo positioned off-grid (partially bleeding off right edge)

## Example Invocations
- "Create a cover for the AGENCY meetup with Vlad about browser automation"
- "Generate a YouTube thumbnail for tonight's meetup recording"
- "Make a Telegram announcement image for the next community event"
