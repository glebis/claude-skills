# Slide Types Reference

Each slide type has a specific HTML structure within the `<div class="slide">` wrapper.

## title

The opening slide. Large title, subtitle, meta info.

```html
<div class="slide active" data-slide="0" data-audio="slide-title" data-read-time="8">
  <div class="slide-inner">
    <div class="slide-label">Category Label</div>
    <h2 style="font-size:3.8rem;">Main Title Here</h2>
    <p style="font-style:italic;color:var(--ink-light);font-size:1.3rem;margin-top:1rem;">Subtitle or tagline</p>
    <p style="font-family:'DM Sans';font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:var(--ink-light);margin-top:2rem;">Date &bull; Source count &bull; Key sources</p>
  </div>
</div>
```

## summary

Executive summary with key takeaway. Large text, highlighted numbers.

```html
<div class="slide" data-slide="1" data-audio="slide-exec" data-read-time="18">
  <div class="slide-inner">
    <div class="slide-label">Executive Summary</div>
    <p style="font-size:1.5rem;line-height:1.45;max-width:30em;">Main finding with <strong style="color:var(--accent-1)">highlighted stat</strong> inline.</p>
    <p style="font-size:1.2rem;margin-top:1.5rem;max-width:34em;color:var(--ink-light)">Supporting context paragraph.</p>
  </div>
</div>
```

## stat

Big numbers in a row. 2-4 statistics with labels.

```html
<div class="slide" data-slide="2" data-audio="slide-numbers" data-read-time="15">
  <div class="slide-inner">
    <div class="slide-label">Section Label</div>
    <h2>Section Title</h2>
    <div class="slide-stat-row">
      <div class="slide-stat"><div class="number" style="color:var(--accent-1)">39%</div><div class="label">Description</div></div>
      <div class="slide-stat"><div class="number" style="color:var(--accent-2)">67%</div><div class="label">Description</div></div>
      <!-- more stats... -->
    </div>
  </div>
</div>
```

## evidence

Text + image side by side. For presenting findings with supporting visuals.

```html
<div class="slide" data-slide="3" data-audio="slide-gap" data-read-time="14">
  <div class="slide-inner" style="display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;">
    <div>
      <div class="slide-label">Label</div>
      <h2 style="font-size:2.2rem;">Heading</h2>
      <p>Body text with <em>emphasis</em> as needed.</p>
    </div>
    <img src="path/to/image.png" alt="Description" style="width:100%;max-height:400px;object-fit:contain;">
  </div>
</div>
```

## comparison

Two images or concepts side by side.

```html
<div class="slide" data-slide="4" data-audio="slide-compare" data-read-time="16">
  <div class="slide-inner">
    <div class="slide-label">Section Label</div>
    <h2>Comparison Title</h2>
    <div class="slide-two-col">
      <img src="path/to/left.png" alt="Option A" style="width:100%;max-height:280px;object-fit:contain;border:1px solid var(--rule);">
      <img src="path/to/right.png" alt="Option B" style="width:100%;max-height:280px;object-fit:contain;border:1px solid var(--rule);">
    </div>
    <p style="font-size:1.2rem;font-weight:600;margin-top:1rem;">Key takeaway statement.</p>
  </div>
</div>
```

## framework

Two-column layout with parallel lists (problems/solutions, before/after, etc.)

```html
<div class="slide" data-slide="5" data-audio="slide-framework" data-read-time="16">
  <div class="slide-inner">
    <div class="slide-label">Section Label</div>
    <h2>Framework Title</h2>
    <p style="margin-bottom:1.5rem;">Brief context.</p>
    <div class="slide-two-col">
      <div>
        <h3 style="font-size:1.1rem;margin-top:0;">Column A</h3>
        <div class="slide-finding"><h4>Point 1</h4><p>Detail</p></div>
        <div class="slide-finding"><h4>Point 2</h4><p>Detail</p></div>
      </div>
      <div>
        <h3 style="font-size:1.1rem;margin-top:0;">Column B</h3>
        <div class="slide-finding"><h4>Point 1</h4><p>Detail</p></div>
        <div class="slide-finding"><h4>Point 2</h4><p>Detail</p></div>
      </div>
    </div>
  </div>
</div>
```

## quote

A single powerful statement. Large text, attribution.

```html
<div class="slide" data-slide="6" data-audio="slide-quote" data-read-time="14">
  <div class="slide-inner">
    <div class="slide-label">Key Insight</div>
    <h2 style="font-size:2.6rem;max-width:18em;">The quote or key statement goes here.</h2>
    <p style="font-size:1.2rem;margin-top:1.5rem;max-width:30em;color:var(--ink-light)">Supporting context. — Attribution</p>
  </div>
</div>
```

## recommendation

Grid of 4-6 action items.

```html
<div class="slide" data-slide="9" data-audio="slide-recs" data-read-time="18">
  <div class="slide-inner">
    <div class="slide-label">Playbook</div>
    <h2 style="font-size:2rem;">Recommendations Title</h2>
    <div class="slide-grid-3x2">
      <div class="slide-card"><div class="card-num">01</div><h4>Title</h4><p>Description</p></div>
      <div class="slide-card"><div class="card-num">02</div><h4>Title</h4><p>Description</p></div>
      <!-- 4-6 cards total -->
    </div>
  </div>
</div>
```

## case-study

Narrative with supporting detail. Text-heavy with optional image.

Use the `evidence` layout with longer text in the left column.

## sources

Grid of source links. Final slide.

```html
<div class="slide" data-slide="11" data-audio="slide-sources" data-read-time="12">
  <div class="slide-inner">
    <div class="slide-label">Section Label</div>
    <h2 style="font-size:2rem;">Sources</h2>
    <table class="sources-table">
      <tr><td><a href="url">Source 1</a></td><td><a href="url">Source 2</a></td></tr>
      <!-- more rows... -->
    </table>
    <p style="font-family:'DM Sans';font-size:0.65rem;color:var(--ink-light);margin-top:2rem;text-transform:uppercase;letter-spacing:0.1em;">Attribution line</p>
  </div>
</div>
```

## Data Attributes

Every slide MUST have:
- `data-slide="N"` — zero-indexed slide number
- `data-audio="slide-id"` — matches the audio filename (without .mp3)
- `data-read-time="N"` — seconds for an average English reader to absorb the visual content

The first slide MUST have `class="slide active"`. All others are just `class="slide"`.
