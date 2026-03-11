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
    <div class="code-container">
      <button class="copy-btn" onclick="copyCode(this)" aria-label="Copy code">
        <svg class="copy-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <svg class="check-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" style="display:none;">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span class="copy-text">Copy</span>
      </button>
      <pre style="max-width: 900px;"><code>${highlightCode(slide.code, slide.language)}</code></pre>
    </div>
    ${slide.tags ? `
    <div style="margin-top: 1.5rem;">
      ${slide.tags.map(t => `<span class="tag tag--${t.type || ''}">${t.text}</span>`).join('')}
    </div>` : ''}
    <div class="slide-number">${index + 1} / ${total}</div>
  </section>`,

  // Repo slide - GitHub repository link
  repo: (slide, index, total) => `
  <section id="slide-${index + 1}" class="slide slide--dark centered">
    ${slide.label ? `<div class="label" style="color: var(--color-secondary);">${slide.label}</div>` : ''}
    <div style="margin-top: 2rem;">
      <svg viewBox="0 0 24 24" width="80" height="80" fill="var(--color-background)">
        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
      </svg>
    </div>
    ${slide.title ? `<h2 style="margin-top: 1.5rem; color: var(--color-background);">${slide.title}</h2>` : ''}
    ${slide.body ? `<p style="color: rgba(255,255,255,0.8); font-size: 1.3rem; margin-top: 1rem;">${slide.body}</p>` : ''}
    <a href="${slide.url}" target="_blank" rel="noopener noreferrer" class="repo-link" style="
      display: inline-block;
      margin-top: 2rem;
      padding: 1rem 2rem;
      background: var(--color-background);
      color: var(--color-primary);
      text-decoration: none;
      font-family: var(--font-mono);
      font-weight: bold;
      font-size: 1.2rem;
      border-radius: 8px;
      border: 3px solid var(--color-secondary);
      transition: transform 0.2s, box-shadow 0.2s;
    " onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 0 var(--color-secondary)';" onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='none';">
      ${slide.url}
    </a>
    <div class="slide-number" style="color: rgba(255,255,255,0.5);">${index + 1} / ${total}</div>
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
      <div class="task-card${item.target ? ' clickable' : ''}"${item.target ? ` onclick="navigateToSlide('${item.target.replace(/'/g, "\\'")}')"` : ''}>
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

// Helper: escape HTML (preserve $ for JSON regex patterns)
function escapeHtml(str, preserveDollar = false) {
  if (!str) return '';
  if (preserveDollar) {
    // For JSON - don't escape $ to preserve regex patterns
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/'/g, '&#039;');
  }
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
  const isJson = language === 'json';

  // For JSON, preserve $ to avoid breaking regex patterns in strings
  let escaped = escapeHtml(code, isJson);

  if (isJson) {
    // For JSON: only highlight strings (skip comments to avoid // in URLs being matched)
    escaped = escaped.replace(/(".*?")/g, '<span class="code-string">$1</span>');
    return escaped;
  }

  // For other languages: process in correct order
  // 1. Strings FIRST - so comments don't match inside strings
  escaped = escaped.replace(/(".*?"|'.*?'|`.*?`)/g, '<span class="code-string">$1</span>');

  // 2. Comments AFTER strings (// and # won't match inside strings now)
  escaped = escaped.replace(/(\/\/.*$)/gm, '<span class="code-comment">$1</span>');
  escaped = escaped.replace(/(\/\*[\s\S]*?\*\/)/g, '<span class="code-comment">$1</span>');
  escaped = escaped.replace(/(#.*$)/gm, '<span class="code-comment">$1</span>');

  // 3. Keywords
  const keywords = ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'import', 'export', 'from', 'class', 'extends', 'async', 'await', 'try', 'catch', 'throw', 'new', 'this', 'true', 'false', 'null', 'undefined'];
  keywords.forEach(kw => {
    escaped = escaped.replace(new RegExp(`\\b(${kw})\\b`, 'g'), '<span class="code-keyword">$1</span>');
  });

  // 4. Numbers
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
