#!/usr/bin/env node
// typo — deterministic typography (multi-locale) via the typograf library.
// Usage:
//   typo.js [options] [file ...]          (no files → read stdin)
// Options:
//   --locale=ru,en-US locale chain (first = primary). Supported: be bg ca cs da
//                     de el en-GB en-US eo es et fi fr ga hu it lv nl no pl ro
//                     ru sk sl sr sv tr uk
//   --in-place        rewrite files instead of printing to stdout
//   --html-entities   output &nbsp;/&mdash; etc. instead of Unicode chars
//   --check           exit 1 if any input would change (prints changed file names)
//   --diff            show a unified word-diff-ish preview instead of full output
//   --safe            disable rules that alter visible characters beyond
//                     quotes/dashes/spaces (no ё, no abbreviation changes)
//   --optalign        hanging punctuation: wrap «, ", commas in classed <span>s
//                     (ru locale, HTML output only; pair with assets/optalign.css)

const fs = require('fs');
const path = require('path');
const Typograf = require('typograf');

const args = process.argv.slice(2);
const opts = { inPlace: false, htmlEntities: false, check: false, diff: false, safe: false, locale: 'ru,en-US' };
const files = [];
for (const a of args) {
  if (a.startsWith('--locale=')) opts.locale = a.slice('--locale='.length);
  else if (a === '--in-place') opts.inPlace = true;
  else if (a === '--html-entities') opts.htmlEntities = true;
  else if (a === '--check') opts.check = true;
  else if (a === '--diff') opts.diff = true;
  else if (a === '--safe') opts.safe = true;
  else if (a === '--optalign') opts.optalign = true;
  else if (a === '--help' || a === '-h') { printHelp(); process.exit(0); }
  else if (a.startsWith('--')) { console.error(`Unknown option: ${a}`); process.exit(2); }
  else files.push(a);
}

function printHelp() {
  console.log(fs.readFileSync(__filename, 'utf8').split('\n').slice(1, 18).map(l => l.replace(/^\/\/ ?/, '')).join('\n'));
}

function makeTypograf() {
  const locales = opts.locale.split(',').map(s => s.trim()).filter(Boolean);
  const tp = new Typograf({
    locale: locales,
    htmlEntity: opts.htmlEntities ? { type: 'name' } : { type: 'default' },
  });
  const ru = locales[0] === 'ru';

  // Pinned rule choices (determinism: same input → same output, always):
  // afterShortWord glues short prepositions/articles to the next word. That's a
  // Slavic convention; in English it would bind "and the", "on the" and read wrong.
  if (ru) {
    tp.enableRule('common/nbsp/afterShortWord');
    tp.enableRule('common/nbsp/beforeShortLastWord');
  } else {
    // Western-European typography does not glue articles/prepositions to the
    // following word; leaving these on produces "and&nbsp;the" everywhere.
    tp.disableRule('common/nbsp/*');
  }
  tp.disableRule('common/html/*');               // never inject HTML tags
  if (ru) {
    tp.enableRule('ru/nbsp/afterNumberSign');    // № 5
    tp.enableRule('ru/other/phone-number');
    if (opts.optalign) tp.enableRule('ru/optalign/*'); // hanging punctuation spans
    else tp.disableRule('ru/optalign/*');
  }

  if (opts.safe) {
    tp.disableRule('ru/date/*');
    tp.disableRule('ru/money/*');
    tp.disableRule('common/number/*');
    tp.disableRule('common/symbols/*');
  }
  return tp;
}

const tp = makeTypograf();

// Deterministic post-rules for locales where typograf lacks native coverage.
// All regexes are idempotent (safe to re-run on already-processed text) and
// require a word character context so URLs/code-ish tokens are left alone.
const NNBSP = ' ', NBSP = ' ';
const SP = `[ ${NBSP}${NNBSP}]`; // any space flavor
function postProcess(text, primaryLocale) {
  if (primaryLocale === 'de') {
    // Gedankenstrich: spaced hyphen/em-dash between words → spaced en dash,
    // nbsp before so the dash never starts a line.
    text = text.replace(new RegExp(`(\\S)${SP}[-—]${SP}(?=\\S)`, 'gu'), `$1${NBSP}– `);
  }
  if (primaryLocale === 'fr') {
    // Tiret: spaced hyphen between words → em dash with nbsp before.
    text = text.replace(new RegExp(`(\\S)${SP}-${SP}(?=\\S)`, 'gu'), `$1${NBSP}— `);
    // Espace fine insécable before ! ? ; (insert after word char or »/) ).
    text = text.replace(new RegExp(`([\\p{L}\\p{N})»])${SP}*([!?;])`, 'gu'), `$1${NNBSP}$2`);
    // Before ':' only normalize/insert when a space or sentence context exists
    // (never touch URLs like https:// — those have no preceding space).
    text = text.replace(new RegExp(`([\\p{L}\\p{N})»])${SP}+(:)`, 'gu'), `$1${NNBSP}$2`);
    text = text.replace(new RegExp(`([\\p{L}\\p{N})»])(:)(?= )`, 'gu'), `$1${NNBSP}$2`);
    // Inside guillemets: narrow nbsp.
    text = text.replace(new RegExp(`«${SP}*`, 'gu'), `«${NNBSP}`)
               .replace(new RegExp(`${SP}*»`, 'gu'), `${NNBSP}»`);
  }
  return text;
}

function processText(text) {
  let out = postProcess(tp.execute(text), opts.locale.split(',')[0].trim());
  // typograf trims trailing whitespace; preserve the input's final newline
  if (text.endsWith('\n') && !out.endsWith('\n')) out += '\n';
  return out;
}

function showDiff(name, before, after) {
  const bl = before.split('\n'), al = after.split('\n');
  console.log(`--- ${name}`);
  for (let i = 0; i < Math.max(bl.length, al.length); i++) {
    if (bl[i] !== al[i]) {
      if (bl[i] !== undefined) console.log(`- ${bl[i]}`);
      if (al[i] !== undefined) console.log(`+ ${al[i]}`);
    }
  }
}

let changed = false;

if (files.length === 0) {
  const input = fs.readFileSync(0, 'utf8');
  const out = processText(input);
  if (out !== input) changed = true;
  if (opts.check) { if (changed) console.error('stdin: would change'); }
  else if (opts.diff) showDiff('stdin', input, out);
  else process.stdout.write(out);
} else {
  for (const f of files) {
    const input = fs.readFileSync(f, 'utf8');
    const out = processText(input);
    if (out !== input) changed = true;
    if (opts.check) { if (out !== input) console.log(f); }
    else if (opts.diff) showDiff(f, input, out);
    else if (opts.inPlace) { if (out !== input) fs.writeFileSync(f, out); }
    else process.stdout.write(out);
  }
}

process.exit(opts.check && changed ? 1 : 0);
