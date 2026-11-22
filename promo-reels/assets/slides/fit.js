// Proportional typesetting for 1080x1920 Reels slides.
//
// Roles (attributes on text elements inside .box):
//   data-fill          size the line so it spans the box width exactly (one line)
//   data-group="g"     lines in the same group share the smallest fill size
//   data-step="-2"     size = ref * RATIO^-2, ref = largest fill size on the slide
//                      (or .box[data-ref] when the slide has no fill line)
//   data-wrap="4"      largest size at which the text fits in N lines (binary search)
//   data-max / data-min  clamps in px
// If the content is taller than the box, every size on the slide is multiplied
// by one common factor, so the proportions survive.
const RATIO = 1.5;      // modular scale: perfect fifth
const FLOOR = 54;       // never below ≈19pt on a phone
const PROBE = 100;      // px used to measure natural width

function textWidth(el) {
  const r = document.createRange(); r.selectNodeContents(el);
  const rs = [...r.getClientRects()].filter(x => x.width > 0);
  return rs.length ? Math.max(...rs.map(x => x.right)) - Math.min(...rs.map(x => x.left)) : 0;
}
// Count visual lines from text-node rects only: a padded inline <span> adds its
// own rects at a different top, which would double-count every line.
function lineCount(el) {
  const tops = [];
  const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  for (let n; (n = tw.nextNode());) {
    const r = document.createRange(); r.selectNodeContents(n);
    for (const x of r.getClientRects()) if (x.width > 1) tops.push(x.top);
  }
  tops.sort((a, b) => a - b);
  const tol = parseFloat(getComputedStyle(el).fontSize) * 0.3;
  return tops.reduce((n, t, i) => n + (i === 0 || t - tops[i - 1] > tol ? 1 : 0), 0);
}
function clamp(v, el) {
  const max = +el.dataset.max || Infinity, min = +el.dataset.min || FLOOR;
  return Math.max(min, Math.min(max, v));
}
// The element's own horizontal padding and border eat into the available width; FILL_SLACK px stay free
// because letter-spacing (tracking token) is rounded per glyph and a line solved to the exact width overshoots.
const FILL_SLACK = 2;
function availWidth(el, box) {
  const cs = getComputedStyle(el);
  const extra = ['paddingLeft', 'paddingRight', 'borderLeftWidth', 'borderRightWidth'].reduce((a, p) => a + parseFloat(cs[p]), 0);
  return box.clientWidth - extra - FILL_SLACK;
}

function setSlide(box, k) {
  const sizes = new Map();
  // 1. fill-to-width, solved directly from one measurement (width is linear in font size)
  box.querySelectorAll('[data-fill]').forEach(el => {
    el.style.whiteSpace = 'nowrap';
    el.style.fontSize = PROBE + 'px';
    sizes.set(el, clamp(PROBE * availWidth(el, box) / textWidth(el), el));
  });
  const groups = {};
  sizes.forEach((s, el) => { const g = el.dataset.group; if (g) groups[g] = Math.min(groups[g] ?? Infinity, s); });
  sizes.forEach((s, el) => { if (el.dataset.group) sizes.set(el, groups[el.dataset.group]); });
  // the scale hangs off the headline marked [data-ref], else the largest fill line
  const anchor = box.querySelector('[data-fill][data-ref]');
  const ref = (anchor && sizes.get(anchor)) || Math.max(0, ...sizes.values()) || +box.dataset.ref || 200;
  // 2. modular steps from the largest fill
  box.querySelectorAll('[data-step]').forEach(el => sizes.set(el, clamp(ref * RATIO ** +el.dataset.step, el)));
  // apply with the common vertical factor k; floors still hold
  sizes.forEach((s, el) => { el.style.fontSize = Math.max(+el.dataset.min || FLOOR, s * k) + 'px'; });
  // a scaled fill line must still fit the width (padding is em-based)
  box.querySelectorAll('[data-fill]').forEach(el => {
    const over = textWidth(el) / availWidth(el, box);
    if (over > 1) el.style.fontSize = parseFloat(el.style.fontSize) / over + 'px';
  });
  // 3. wrapped captions: largest size that fits N lines and the width
  box.querySelectorAll('[data-wrap]').forEach(el => {
    let lo = +el.dataset.min || FLOOR, hi = (+el.dataset.max || 200) * k;
    for (let i = 0; i < 14; i++) {
      const mid = (lo + hi) / 2; el.style.fontSize = mid + 'px';
      const ok = lineCount(el) <= +el.dataset.wrap && textWidth(el) <= availWidth(el, box) + 0.5;
      ok ? lo = mid : hi = mid;
    }
    el.style.fontSize = Math.floor(lo) + 'px';
  });
}

function contentHeight(box) {
  return [...box.children].filter(c => !c.classList.contains('grow')).reduce((a, c) => {
    const cs = getComputedStyle(c);
    return a + c.getBoundingClientRect().height + parseFloat(cs.marginTop) + parseFloat(cs.marginBottom);
  }, 0);
}

function fitAll() {
  document.querySelectorAll('.box').forEach(box => {
    let k = 1;
    for (let i = 0; i < 6; i++) {
      setSlide(box, k);
      const h = contentHeight(box);
      if (h <= box.clientHeight + 1) break;
      k *= box.clientHeight / h;   // one proportional correction; repeat because floors don't scale
    }
    box.dataset.scale = k.toFixed(3);
    box.dataset.overflow = contentHeight(box) > box.clientHeight + 1 ? '1' : '';
  });
}
