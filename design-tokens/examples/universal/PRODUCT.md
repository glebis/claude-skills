# Product

## Register

brand

## Users

The author (and others adopting the design-tokens skill) building wikis, presentations, documentation, and demos that must change their entire look by swapping a token file. The reader's context is reading: long-form, text-dense, on a real screen, often for reference rather than conversion. The maker's context is authoring: they want to drop content into known blocks and trust that a theme override re-skins everything without touching markup.

## Product Purpose

A universal, theme-able content block kit driven entirely by DTCG design tokens. One block library (hero, section header, card grid, prose, list-rows, callout, steps, pull-quote, code, table, figure, colophon) renders as a light editorial wiki or a dark developer site, switched live, with no value hard-coded in the markup. Success is when a new theme is a small override file plus one merge command, and the same page reads as a credible hand-built editorial document in either polarity, not a template.

## Brand Personality

Editorial, restrained, typographic. Voice is dry, specific, and a little opinionated, the register of good documentation and print rather than marketing. Type carries the hierarchy; ornament that does not carry meaning is cut. Technical and precise underneath: it shows its own structure and is honest about being a token system. Emotional goal is quiet confidence and legibility, never hype.

## Anti-references

- **Generic SaaS landing**: centered hero, three identical feature cards, a gradient blob, everything rounded.
- **Gradient / AI-slop**: gradient text, glassmorphism, purple-to-blue washes, emoji bullets, hollow taglines, em-dash filler, over-symmetry.
- **Dashboard template**: hero-metric tiles, chart grids, the admin-panel look.
- **Corporate-cold stock**: stock photography, navy-and-gray, lifeless enterprise polish.
- **The unsteered-model default**: what a capable model (e.g. Fable 5) emits for "a landing page" with no direction. Concretely: **Inter or Roboto** as the typeface, **purple/violet gradients on a white ground**, minimal or no motion, and a layout that impresses at first glance but falls apart on the second look (placeholder copy, decorative elements with no job, symmetry standing in for hierarchy). Our token system and this file exist precisely to steer away from this default; naming it is the steer.

If a viewer could say "AI made that" without doubt, it has failed. The test is the *second* look, not the first.

## Design Principles

1. **The look lives in the tokens.** Every colour, size, and face resolves from a token file. Markup never hard-codes a value. Practice the skill the kit demonstrates.
2. **A theme is a delta.** A theme override states only what differs and inherits the rest. Favour small, legible overrides over restated palettes.
3. **Values become tokens, patterns become prose.** Tokenize what is a value (size, colour, measure, ratio); document what is a pattern (which side the illustration sits on, ruled-lines-vs-dots) in prose. Never fake composition as a token.
4. **Show the system, don't decorate it.** Structure is the aesthetic. Cut any element that does not carry meaning. No filler copy, no decorative cards, no slop.
5. **Earn every element and every word.** Editorial restraint over template completeness. If a block or a sentence is not doing work, remove it.

## Accessibility & Inclusion

- Target WCAG 2.1 AA. Body and UI text must meet contrast on both themes (paper accent on paper surface; ink accent on ink surface). Verify accent legibility as link/text colour, not just on large display type.
- Respect `prefers-reduced-motion`; theme transitions and any motion degrade to instant.
- Do not encode meaning in colour alone (themes differ in hue and polarity; roles must read from structure too).
- Semantic HTML: real headings, lists, `figure`/`figcaption`, `blockquote`/`cite`, `table` headers. Maintain a logical heading order across blocks.
