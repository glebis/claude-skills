#!/usr/bin/env node
// Thin, dependency-free CLI over a running i18n Studio server (Node 18+ `fetch`).
// Start the server first (see SKILL.md), then drive it from the shell:
//
//   I18N_URL=http://localhost:4331 node i18n.mjs audit --to ru
//   node i18n.mjs get   Hero.ts en h1
//   node i18n.mjs suggest Hero.ts h1 --from en --to ru
//   node i18n.mjs set   Hero.ts ru h1 "Новый заголовок"
//
// Base URL: $I18N_URL or http://localhost:4331.

const BASE = process.env.I18N_URL || 'http://localhost:4331';
const argv = process.argv.slice(2);
const cmd = argv[0];

function opt(name, def) {
  const i = argv.indexOf(`--${name}`);
  return i !== -1 && i + 1 < argv.length ? argv[i + 1] : def;
}
const positional = argv.slice(1).filter((a, i, arr) => !a.startsWith('--') && !(i > 0 && arr[i - 1].startsWith('--')));

async function getStrings() {
  let res;
  try {
    res = await fetch(`${BASE}/api/strings`);
  } catch {
    die(`Cannot reach i18n Studio at ${BASE}. Start it first:\n  node ~/ai_projects/i18n-studio/server.mjs --dir <repo>/src/i18n/strings &`);
  }
  if (!res.ok) die(`GET /api/strings failed: ${res.status}`);
  return res.json();
}
function die(msg) { console.error(msg); process.exit(1); }
const isEmpty = (cell) => !cell || cell.value == null || String(cell.value).trim() === '';

async function audit() {
  const to = opt('to');
  const pendingToo = argv.includes('--pending'); // also list translated-but-unaccepted
  const { langs, files } = await getStrings();
  const targets = to ? [to] : langs;
  let total = 0;
  const stat = {}; targets.forEach((l) => (stat[l] = { total: 0, accepted: 0, pending: 0, empty: 0 }));
  for (const f of files) {
    const gaps = [];
    for (const e of f.entries) {
      for (const lang of targets) {
        const cell = e[lang];
        const source = langs.find((l) => l !== lang && e[l] && e[l].editable && !isEmpty(e[l]));
        if (cell && cell.editable) {
          stat[lang].total++;
          if (isEmpty(cell)) stat[lang].empty++;
          else if (cell.accepted) stat[lang].accepted++;
          else stat[lang].pending++;
        }
        if (source && cell && cell.editable && isEmpty(cell)) gaps.push(`  ${lang}  untranslated  ${e.path}   (from ${source}: ${JSON.stringify(e[source].value).slice(0, 50)})`);
        else if (source && !cell) gaps.push(`  ${lang}  missing-key   ${e.path}   (${source} has text)`);
        else if (pendingToo && cell && cell.editable && !isEmpty(cell) && !cell.accepted) gaps.push(`  ${lang}  pending       ${e.path}`);
      }
    }
    if (gaps.length) { console.log(`\n${f.file}  (${gaps.length})`); console.log(gaps.join('\n')); total += gaps.length; }
  }
  console.log('');
  for (const l of targets) { const s = stat[l]; console.log(`${l}: ${s.accepted} accepted · ${s.pending} pending · ${s.empty} untranslated · ${s.total} total`); }
  console.log(total ? `\n${total} item(s) need attention across ${targets.join(', ')}.` : `\nNothing flagged in ${targets.join(', ')}.`);
}

async function accept(on) {
  const [file, lang, path] = positional;
  if (!file || !lang || !path) die(`usage: ${on ? 'accept' : 'unaccept'} <file> <lang> <path>`);
  const { files } = await getStrings();
  const f = files.find((x) => x.file === file) || die(`no such file: ${file}`);
  const e = f.entries.find((x) => x.path === path) || die(`no such path: ${path}`);
  const cell = e[lang];
  if (!cell || !cell.editable) die(`not an editable cell: ${lang} ${path}`);
  const res = await fetch(`${BASE}/api/accept`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ file, lang, path, value: cell.value, accepted: on }),
  });
  const data = await res.json();
  if (!data.ok) die(`accept failed: ${data.error}`);
  console.log(`${on ? 'accepted' : 'unaccepted'} ${file} ${lang} ${path}`);
}

async function get() {
  const [file, lang, path] = positional;
  if (!file || !lang || !path) die('usage: get <file> <lang> <path>');
  const { files } = await getStrings();
  const f = files.find((x) => x.file === file) || die(`no such file: ${file}`);
  const e = f.entries.find((x) => x.path === path) || die(`no such path: ${path}`);
  const cell = e[lang];
  if (!cell) die(`no ${lang} value at ${path}`);
  console.log(JSON.stringify({ value: cell.value, editable: cell.editable }, null, 2));
}

async function suggest() {
  const [file, path] = positional;
  const from = opt('from'), to = opt('to');
  if (!file || !path || !from || !to) die('usage: suggest <file> <path> --from <lang> --to <lang>');
  const { files } = await getStrings();
  const f = files.find((x) => x.file === file) || die(`no such file: ${file}`);
  const e = f.entries.find((x) => x.path === path) || die(`no such path: ${path}`);
  const src = e[from];
  if (!src || isEmpty(src)) die(`no ${from} source text at ${path}`);
  const res = await fetch(`${BASE}/api/suggest`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ sourceText: src.value, from, to, path }),
  });
  const data = await res.json();
  if (!data.ok) die(`suggest failed: ${data.error}`);
  data.suggestions.forEach((s, i) => console.log(`${i + 1}. ${s}`));
}

async function set() {
  const [file, lang, path, ...rest] = positional;
  const value = rest.join(' ');
  if (!file || !lang || !path || value === '') die('usage: set <file> <lang> <path> <value>');
  const res = await fetch(`${BASE}/api/save`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ file, lang, path, value }),
  });
  const data = await res.json();
  if (!data.ok) die(`save failed: ${data.error}`);
  console.log(`saved ${file} ${lang} ${path}`);
}

const table = {
  audit, get, suggest, set,
  accept: () => accept(true),
  unaccept: () => accept(false),
};
if (!table[cmd]) die(
  'commands:\n' +
  '  audit [--to <lang>] [--pending]                     status breakdown + gaps\n' +
  '  get <file> <lang> <path>                            read a value\n' +
  '  suggest <file> <path> --from <lang> --to <lang>     3 candidates\n' +
  '  set <file> <lang> <path> <value>                    AST-safe write\n' +
  '  accept|unaccept <file> <lang> <path>                toggle review acceptance');
await table[cmd]();
