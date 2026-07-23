/* Runtime hanging punctuation — no source-markup changes.
   Uses native CSS hanging-punctuation where supported (Safari); otherwise
   wraps a leading quote of each block in a negatively-margined span.
   Configure via data attribute or the HANG_PUNCT global before load:
     window.HANG_PUNCT = { selector: 'p, h1, h2, h3, blockquote, li' } */
(function () {
  var cfg = window.HANG_PUNCT || {};
  var selector = cfg.selector || 'p, h1, h2, h3, blockquote';
  // Fallback: hang the leading quote via a span with a negative margin.
  var HANG = { '«': '-0.44em', '„': '-0.38em', '“': '-0.38em', '‘': '-0.25em', '"': '-0.38em' };

  function run() {
    if (CSS.supports && CSS.supports('hanging-punctuation', 'first')) {
      document.querySelectorAll(selector).forEach(function (el) {
        el.style.hangingPunctuation = 'first allow-end';
      });
      return;
    }
    document.querySelectorAll(selector).forEach(function (el) {
      var n = el.firstChild;
      if (!n || n.nodeType !== Node.TEXT_NODE) return;
      var ch = n.textContent.charAt(0);
      if (!(ch in HANG)) return;
      var span = document.createElement('span');
      span.textContent = ch;
      span.style.marginLeft = HANG[ch];
      span.setAttribute('aria-hidden', 'false');
      n.textContent = n.textContent.slice(1);
      el.insertBefore(span, n);
    });
  }

  // exposed so a language swap can re-hang the new copy
  window.HangPunct = { refresh: run };
  run();
})();
