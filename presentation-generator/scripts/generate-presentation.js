#!/usr/bin/env node
/**
 * Presentation Generator
 *
 * Generates interactive HTML presentations from JSON/YAML content
 * with neobrutalism styling from brand-agency skill.
 */

const fs = require('fs');
const path = require('path');

// Template directory
const TEMPLATES_DIR = path.join(__dirname, '..', 'templates');

// Read CSS styles
const styles = fs.readFileSync(path.join(TEMPLATES_DIR, 'styles.css'), 'utf-8');

// Slide type renderers
const slideRenderers = {
  // Title slide - big title with optional subtitle
  title: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'primary'}">
    ${slide.label ? `<div class="label">${slide.label}</div>` : ''}
    <h1>${slide.title}</h1>
    ${slide.subtitle ? `<p class="subtitle">${slide.subtitle}</p>` : ''}
    ${slide.footer ? `<div class="footer">${slide.footer}</div>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Content slide - heading + body + optional bullets
  content: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'light'}">
    ${slide.label ? `<div class="label">${slide.label}</div>` : ''}
    <h2>${slide.title}</h2>
    ${slide.body ? `<p style="font-size: 1.3rem; max-width: 800px;">${slide.body}</p>` : ''}
    ${slide.bullets ? `
    <ul style="margin-top: 1.5rem; font-size: 1.2rem;">
      ${slide.bullets.map(b => `<li>${b}</li>`).join('\n      ')}
    </ul>` : ''}
    ${slide.tags ? `
    <div style="margin-top: 2rem;">
      ${slide.tags.map(t => `<span class="tag tag--${t.type || ''}">${t.text}</span>`).join('')}
    </div>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Two-column slide
  'two-col': (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'light'}">
    ${slide.label ? `<div class="label">${slide.label}</div>` : ''}
    ${slide.title ? `<h2>${slide.title}</h2>` : ''}
    <div class="two-col" style="margin-top: 2rem;">
      <div>
        ${slide.left.title ? `<h3>${slide.left.title}</h3>` : ''}
        ${slide.left.body ? `<p>${slide.left.body}</p>` : ''}
        ${slide.left.bullets ? `
        <ul>
          ${slide.left.bullets.map(b => `<li>${b}</li>`).join('\n          ')}
        </ul>` : ''}
        ${slide.left.code ? `<pre><code>${escapeHtml(slide.left.code)}</code></pre>` : ''}
      </div>
      <div>
        ${slide.right.title ? `<h3>${slide.right.title}</h3>` : ''}
        ${slide.right.body ? `<p>${slide.right.body}</p>` : ''}
        ${slide.right.bullets ? `
        <ul>
          ${slide.right.bullets.map(b => `<li>${b}</li>`).join('\n          ')}
        </ul>` : ''}
        ${slide.right.code ? `<pre><code>${escapeHtml(slide.right.code)}</code></pre>` : ''}
        ${slide.right.ascii ? `<div class="ascii-box">${slide.right.ascii}</div>` : ''}
      </div>
    </div>
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Code slide - dark background with code block
  code: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--dark">
    ${slide.label ? `<div class="label" style="color: var(--color-success);">${slide.label}</div>` : ''}
    <h2>${slide.title}</h2>
    ${slide.description ? `<p style="opacity: 0.8; margin-bottom: 1.5rem;">${slide.description}</p>` : ''}
    <pre style="max-width: 900px;"><code>${highlightCode(slide.code, slide.language)}</code></pre>
    ${slide.tags ? `
    <div style="margin-top: 1.5rem;">
      ${slide.tags.map(t => `<span class="tag tag--${t.type || ''}">${t.text}</span>`).join('')}
    </div>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Stats slide - big numbers with labels
  stats: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'light'} centered">
    ${slide.label ? `<div class="label">${slide.label}</div>` : ''}
    ${slide.title ? `<h2>${slide.title}</h2>` : ''}
    <div class="stats-row">
      ${slide.items.map(item => `
      <div class="stat">
        <div class="stat-value">${item.value}</div>
        <div class="stat-label">${item.label}</div>
      </div>`).join('')}
    </div>
    ${slide.subtitle ? `<p class="subtitle" style="margin-top: 2rem;">${slide.subtitle}</p>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Grid slide - task/feature cards
  grid: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'light'}">
    ${slide.label ? `<div class="label">${slide.label}</div>` : ''}
    <h2>${slide.title}</h2>
    ${slide.body ? `<p style="font-size: 1.2rem; max-width: 700px;">${slide.body}</p>` : ''}
    <div class="task-grid">
      ${slide.items.map(item => `
      <div class="task-card">
        <div class="task-number">${item.number || ''}</div>
        <div class="task-title">${item.title}</div>
        <div class="task-desc">${item.desc || ''}</div>
        ${item.tags ? `
        <div>
          ${item.tags.map(t => `<span class="tag tag--${t.type || ''}">${t.text}</span>`).join('')}
        </div>` : ''}
      </div>`).join('')}
    </div>
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // ASCII art slide
  ascii: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'dark'}">
    ${slide.label ? `<div class="label" style="color: var(--color-secondary);">${slide.label}</div>` : ''}
    ${slide.title ? `<h2>${slide.title}</h2>` : ''}
    <div class="ascii-box" style="margin-top: 2rem; ${slide.bg === 'dark' ? 'background: rgba(255,255,255,0.1); color: var(--color-background);' : ''}">${slide.ascii}</div>
    ${slide.caption ? `<p style="margin-top: 1.5rem; font-family: var(--font-mono);">${slide.caption}</p>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Terminal slide
  terminal: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'muted'}">
    ${slide.label ? `<div class="label">${slide.label}</div>` : ''}
    ${slide.title ? `<h2>${slide.title}</h2>` : ''}
    <div class="terminal" style="max-width: 800px; margin-top: 2rem;">
      <div class="terminal-header">
        <span class="terminal-btn terminal-btn--close"></span>
        <span class="terminal-btn terminal-btn--minimize"></span>
        <span class="terminal-btn terminal-btn--maximize"></span>
      </div>
      <div class="terminal-content">
        ${slide.lines.map(line => {
          if (line.type === 'prompt') {
            return `<div><span class="terminal-prompt">$ </span>${escapeHtml(line.text)}</div>`;
          } else if (line.type === 'output') {
            return `<div class="terminal-output">${escapeHtml(line.text)}</div>`;
          } else if (line.type === 'comment') {
            return `<div style="color: #888;"># ${escapeHtml(line.text)}</div>`;
          }
          return `<div>${escapeHtml(line.text || line)}</div>`;
        }).join('\n        ')}
      </div>
    </div>
    ${slide.note ? `<p style="margin-top: 1.5rem; font-family: var(--font-mono); opacity: 0.7;">${slide.note}</p>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Image slide
  image: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'light'}">
    ${slide.label ? `<div class="label">${slide.label}</div>` : ''}
    ${slide.title ? `<h2>${slide.title}</h2>` : ''}
    <div class="image-container" style="max-width: ${slide.maxWidth || '800px'}; margin-top: 2rem;">
      <img src="${slide.src}" alt="${slide.alt || slide.title || ''}" />
    </div>
    ${slide.caption ? `<p style="margin-top: 1rem; font-family: var(--font-mono); font-size: 0.9rem; opacity: 0.7;">${slide.caption}</p>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Quote slide
  quote: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'secondary'} centered">
    <div class="ascii-border" style="font-size: 2rem; margin-bottom: 1rem;">╔══════════════════════════════════════╗</div>
    <blockquote style="font-size: 2rem; font-style: italic; max-width: 800px; line-height: 1.4;">
      "${slide.quote}"
    </blockquote>
    <div class="ascii-border" style="font-size: 2rem; margin-top: 1rem;">╚══════════════════════════════════════╝</div>
    ${slide.author ? `<p style="margin-top: 2rem; font-family: var(--font-mono);">— ${slide.author}</p>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Comparison slide (before/after, pros/cons)
  comparison: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--${slide.bg || 'muted'}">
    ${slide.label ? `<div class="label">${slide.label}</div>` : ''}
    <h2>${slide.title}</h2>
    <div class="two-col" style="margin-top: 2rem;">
      <div class="card" style="border-color: ${slide.leftColor || 'var(--color-error)'};">
        <h3 style="color: ${slide.leftColor || 'var(--color-error)'};">${slide.leftTitle || 'Before'}</h3>
        ${slide.left.map(item => `<p style="margin-top: 0.5rem;">- ${item}</p>`).join('')}
      </div>
      <div class="card" style="border-color: ${slide.rightColor || 'var(--color-success)'};">
        <h3 style="color: ${slide.rightColor || 'var(--color-success)'};">${slide.rightTitle || 'After'}</h3>
        ${slide.right.map(item => `<p style="margin-top: 0.5rem;">+ ${item}</p>`).join('')}
      </div>
    </div>
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`
};

// Helper: escape HTML
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Helper: basic syntax highlighting
function highlightCode(code, language) {
  if (!code) return '';
  let escaped = escapeHtml(code);

  // Comments
  escaped = escaped.replace(/(\/\/.*$|#.*$)/gm, '<span class="code-comment">$1</span>');
  escaped = escaped.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="code-comment">$1</span>');

  // Strings
  escaped = escaped.replace(/(".*?"|'.*?'|`.*?`)/g, '<span class="code-string">$1</span>');

  // Keywords
  const keywords = ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'import', 'export', 'from', 'class', 'extends', 'async', 'await', 'try', 'catch', 'throw', 'new', 'this', 'true', 'false', 'null', 'undefined'];
  keywords.forEach(kw => {
    escaped = escaped.replace(new RegExp(`\\b(${kw})\\b`, 'g'), '<span class="code-keyword">$1</span>');
  });

  // Numbers
  escaped = escaped.replace(/\b(\d+)\b/g, '<span class="code-number">$1</span>');

  return escaped;
}

// Generate navigation dots
function generateNavigation(slideCount) {
  let nav = '';
  for (let i = 1; i <= slideCount; i++) {
    nav += `    <a href="#slide-${i}" class="nav-dot${i === 1 ? ' active' : ''}"></a>\n`;
  }
  return nav;
}

// Main generator function
function generatePresentation(content, outputPath) {
  const { title, lang, footer, slides } = content;

  // Render all slides
  const renderedSlides = slides.map((slide, index) => {
    const renderer = slideRenderers[slide.type];
    if (!renderer) {
      console.warn(`Unknown slide type: ${slide.type}`);
      return '';
    }
    // Add global footer to slides if not specified
    if (!slide.footer && footer && slide.type === 'title') {
      slide.footer = footer;
    }
    return renderer(slide, index, slides.length);
  }).join('\n\n');

  // Generate navigation
  const navigation = generateNavigation(slides.length);

  // Read base template
  const baseTemplate = fs.readFileSync(path.join(TEMPLATES_DIR, 'base.html'), 'utf-8');

  // Replace placeholders
  const html = baseTemplate
    .replace('{{title}}', title || 'Presentation')
    .replace('{{lang}}', lang || 'en')
    .replace('{{styles}}', styles)
    .replace('{{navigation}}', navigation)
    .replace('{{slides}}', renderedSlides);

  // Write output
  fs.writeFileSync(outputPath, html);
  console.log(`Generated: ${outputPath}`);

  return outputPath;
}

// CLI handling
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Presentation Generator
======================

Usage:
  node generate-presentation.js --input content.json --output presentation.html
  node generate-presentation.js -i content.json -o presentation.html

Options:
  --input, -i   Input JSON/YAML file with presentation content
  --output, -o  Output HTML file path
  --help, -h    Show this help

Content format (JSON):
{
  "title": "Presentation Title",
  "lang": "en",
  "footer": "Company / Date",
  "slides": [
    { "type": "title", "bg": "primary", "title": "...", "subtitle": "..." },
    { "type": "content", "title": "...", "body": "...", "bullets": [...] },
    { "type": "code", "title": "...", "code": "...", "language": "javascript" },
    { "type": "stats", "items": [{ "value": "10", "label": "items" }] }
  ]
}

Slide types: title, content, two-col, code, stats, grid, ascii, terminal, image, quote, comparison
`);
    process.exit(0);
  }

  const inputIndex = args.findIndex(a => a === '--input' || a === '-i');
  const outputIndex = args.findIndex(a => a === '--output' || a === '-o');

  if (inputIndex === -1) {
    console.error('Error: --input is required');
    process.exit(1);
  }

  const inputPath = args[inputIndex + 1];
  const outputPath = outputIndex !== -1 ? args[outputIndex + 1] : inputPath.replace(/\.(json|yaml|yml)$/, '.html');

  // Read input
  let content;
  try {
    const inputContent = fs.readFileSync(inputPath, 'utf-8');
    if (inputPath.endsWith('.yaml') || inputPath.endsWith('.yml')) {
      // Simple YAML parsing (for basic cases)
      // For full YAML support, use js-yaml package
      console.error('YAML support requires js-yaml package. Please use JSON for now.');
      process.exit(1);
    } else {
      content = JSON.parse(inputContent);
    }
  } catch (err) {
    console.error(`Error reading input: ${err.message}`);
    process.exit(1);
  }

  generatePresentation(content, outputPath);
}

module.exports = { generatePresentation };
