# Design Tokens

## CSS Variables

```css
:root {
  --ink: #1a1a1a;          /* Primary text */
  --ink-light: #555;       /* Secondary text, aside narratives */
  --ink-muted: #888;       /* Tertiary text, captions, labels */
  --bg: #fffff8;           /* Background (warm white, not pure white) */
  --bg-aside: #f9f6ee;    /* Flyout/callout background */
  --accent: #a00;          /* Accent markers (aside-marker, flyout diamond) */
  --rule: #ccc;            /* Borders, rules, separator color */

  /* Semantic chart colors */
  --spark-primary: #c45a28;   /* Primary data stream (orange) */
  --spark-secondary: #2a7a5a; /* Secondary/growth (green) */
  --spark-tertiary: #5a5aaa;  /* Social/communication (purple) */

  /* Status colors */
  --status-red: #a02a2a;
  --status-amber: #c89000;
  --status-green: #2a7a3a;
  --status-blue: rgba(42,80,140,0.7);
}
```

## Typography Scale

| Element | Font | Size | Weight | Style |
|---------|------|------|--------|-------|
| h1 | EB Garamond | 2.2rem | 400 | small-caps |
| h2 | EB Garamond | 1.5rem | 400 | small-caps |
| h3 | EB Garamond | 1.15rem | 400 | small-caps, --ink-light |
| body | EB Garamond | 18px / 1.6 | 400 | normal |
| state-line | EB Garamond | 1.5rem / 1.45 | 400 | italic, --ink-light |
| overview lede | EB Garamond | 1.25rem / 1.6 | 400 | drop cap first letter |
| aside | EB Garamond | 0.85rem / 1.5 | 400 | italic, --ink-light |
| caption | EB Garamond | 0.82rem | 400 | italic, --ink-muted, centered |
| table header | EB Garamond | 0.92rem | 400 | small-caps, --ink-muted |
| table numbers | Monaspace Argon | 0.85rem | 400 | tabular-nums |
| big number | Monaspace Argon | 2.6rem | 400 | letter-spacing: -0.02em |
| status value | Monaspace Argon | 1.5rem | 400 | tabular-nums |
| source tags | Monaspace Argon | 0.65rem | 400 | --rule color |
| ornament | Monaspace Argon | 0.9rem | 400 | ligatures enabled |

## Font Loading

```html
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">
<style>
  @font-face {
    font-family: 'Monaspace Argon';
    src: url('https://cdn.jsdelivr.net/gh/githubnext/monaspace@v1.101/fonts/webfonts/MonaspaceArgon-Regular.woff2') format('woff2');
    font-weight: 400; font-display: swap;
  }
  @font-face {
    font-family: 'Monaspace Argon';
    src: url('https://cdn.jsdelivr.net/gh/githubnext/monaspace@v1.101/fonts/webfonts/MonaspaceArgon-Bold.woff2') format('woff2');
    font-weight: 700; font-display: swap;
  }
</style>
```

## Layout Grid

- Max width: 1200px, centered
- Padding: 2rem 1.5rem 4rem
- Aside-container: `1fr 280px` with 2rem gap
- TOC layout: `1fr 180px` with 2rem gap
- Summary cards: `repeat(3, 1fr)` with 1.5rem gap
- Status strip: `repeat(4, 1fr)` with no gap
- Mobile breakpoint: 800px (collapses all grids to single column)

## Spacing

- Between sections (ornament): 2rem
- Chart container margin: 2rem 0
- Chart side padding: 5% left/right
- Table margin: 1.5rem 0
- State-line margin: 1.5rem 0 2rem
- Flyout margin: 1.5rem 0

## Transitions

- Hover on cards/flyouts: `border-color 0.3s ease, box-shadow 0.3s ease`
- Table row hover: `background 0.2s ease`
- Back-to-top arrow: `color 0.3s ease, transform 0.3s ease` (translateY -2px)
- Scroll reveal: `opacity 0.6s cubic-bezier(0.25,0.1,0.25,1), transform 0.6s` (translateY 16px)
- Reduced motion: all transitions disabled via `prefers-reduced-motion`
