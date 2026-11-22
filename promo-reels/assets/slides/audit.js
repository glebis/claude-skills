// Text-fit audit for 1080x1920 Reels slides. Runs after fit.js.
// Checks: clipping, Instagram safe zone, overlap, min font size, contrast, copy length.
// Result: window.AUDIT and a JSON <pre id="audit-result"> (read via `chrome --dump-dom`).
const SAFE = { left: 60, right: 140, top: 250, bottom: 450 }; // px; clear of IG top bar, caption area, right buttons
const MIN_FONT = 48;    // px at 1080 wide ≈ 17pt on a phone
const FILL_MIN = 140;   // a fill headline below this stops reading as a headline
const SCALE_MIN = 0.8;  // whole-slide shrink below this = slide is overloaded
// Copy budget for a fill line depends on the font (a wide face fits fewer letters): style.py measures it
// per style and language into type.fill_chars; 10 is the condensed-grotesque default.
function fillBudget() {
  try { const f = D.theme.type.fill_chars; return (f && (f[D.lang] || f.en)) || 10; } catch (e) { return 10; }
}

function lum(rgb) {
  const [r, g, b] = rgb.map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function parse(c) { const m = c.match(/[\d.]+/g); return m ? m.slice(0, 4).map(Number) : null; }
function bgOf(el) {
  for (let n = el; n; n = n.parentElement) {
    const p = parse(getComputedStyle(n).backgroundColor);
    if (p && (p.length < 4 || p[3] > 0)) return p.slice(0, 3);
  }
  return [255, 255, 255];
}
// Horizontal extent from glyph rects; vertical from the element box (tight leading is intended).
function textRect(el) {
  const r = document.createRange(); r.selectNodeContents(el);
  const rs = [...r.getClientRects()].filter(x => x.width && x.height);
  const e = el.getBoundingClientRect();
  if (!rs.length) return e;
  return { left: Math.min(...rs.map(x => x.left)), right: Math.max(...rs.map(x => x.right)), top: e.top, bottom: e.bottom };
}

function audit() {
  const out = [];
  document.querySelectorAll('.slide').forEach(slide => {
    const S = slide.getBoundingClientRect(), k = S.width / 1080, name = slide.dataset.name;
    const rects = [];
    slide.querySelectorAll('[data-t]').forEach(el => {
      const t = textRect(el);
      const r = { l: (t.left - S.left) / k, r: (t.right - S.left) / k, t: (t.top - S.top) / k, b: (t.bottom - S.top) / k };
      rects.push([el, r]);
      const issues = [];
      if (r.l < 0 || r.t < 0 || r.r > 1080 || r.b > 1920) issues.push('CLIPPED outside slide');
      else if (r.l < SAFE.left || r.r > 1080 - SAFE.right || r.t < SAFE.top || r.b > 1920 - SAFE.bottom) {
        const where = [r.t < SAFE.top && 'top', r.b > 1920 - SAFE.bottom && 'bottom', r.l < SAFE.left && 'left', r.r > 1080 - SAFE.right && 'right'].filter(Boolean);
        issues.push('outside safe zone: ' + where.join(','));
      }
      const px = parseFloat(getComputedStyle(el).fontSize);
      if (px < MIN_FONT) issues.push(`small font ${Math.round(px)}px`);
      const lines = lineCount(el);  // from fit.js
      // contrast against the background behind the first text run
      const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, { acceptNode: n => n.textContent.trim() ? 1 : 3 });
      const inner = (tw.nextNode() || el).parentElement || el;
      const fg = parse(getComputedStyle(inner).color).slice(0, 3), bg = bgOf(inner);
      const L1 = lum(fg), L2 = lum(bg), cr = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
      const bold = +getComputedStyle(inner).fontWeight >= 700;
      const need = (px >= 67 || (bold && px >= 52)) ? 3 : 4.5; // WCAG large-text rule scaled to the 1080 frame
      if (cr < need) issues.push(`contrast ${cr.toFixed(2)} < ${need}`);
      // copy-length rules: fail loudly so the copy is rewritten instead of shrunk
      const n = el.textContent.trim().length;
      if (el.hasAttribute('data-fill') && px < FILL_MIN) issues.push(`REWRITE: fill line ${n} chars → ${Math.round(px)}px; keep ≤${fillBudget()} chars for this style`);
      if (el.dataset.wrap && lines > +el.dataset.wrap) issues.push(`REWRITE: ${lines} lines > ${el.dataset.wrap}; keep ≤${15 * el.dataset.wrap} chars`);
      out.push({ slide: name, text: el.textContent.trim().slice(0, 40), font: Math.round(px), lines, issues });
    });
    for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
      const [ea, a] = rects[i], [eb, b] = rects[j];
      if (ea.contains(eb) || eb.contains(ea)) continue;
      if (a.l < b.r && b.l < a.r && a.t < b.b && b.t < a.b)
        out.push({ slide: name, text: ea.textContent.trim().slice(0, 20) + ' × ' + eb.textContent.trim().slice(0, 20), issues: ['OVERLAP'] });
    }
    slide.querySelectorAll('.box').forEach(b => {
      if (b.dataset.overflow) out.push({ slide: name, text: '(box)', issues: ['BOX OVERFLOW'] });
      if (+b.dataset.scale < SCALE_MIN) out.push({ slide: name, text: '(box)', issues: [`REWRITE: slide shrunk to ${b.dataset.scale}; cut text`] });
    });
  });
  window.AUDIT = out;
  const pre = document.getElementById('audit-result') || document.body.appendChild(Object.assign(document.createElement('pre'), { id: 'audit-result' }));
  pre.style.display = 'none';
  pre.textContent = JSON.stringify(out);
  return out;
}
