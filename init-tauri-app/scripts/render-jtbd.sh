#!/usr/bin/env bash
# Render a jtbd template by substituting fields from a jtbd.json.
# Usage: render-jtbd.sh <jtbd.json> <template> <source_path_label>
# Prints the rendered text to stdout. Exit 3 = invalid/missing required fields.
set -euo pipefail
JSON="$1"; TPL="$2"; SRC="${3:-$1}"
node - "$JSON" "$TPL" "$SRC" <<'NODE'
const fs = require('fs');
const [json, tpl, src] = process.argv.slice(2);
let data;
try { data = JSON.parse(fs.readFileSync(json, 'utf8')); }
catch (e) { console.error('invalid JSON'); process.exit(3); }
if (!data.name || !data.hook || !data.jtbd) { console.error('missing required fields'); process.exit(3); }
data.__source_path__ = src;
const get = (obj, path) => path.split('.').reduce((o,k)=> (o==null?undefined:o[k]), obj);
let t = fs.readFileSync(tpl, 'utf8');
// expand each-blocks
t = t.replace(/<!-- each:([\w.]+) -->\n([\s\S]*?)<!-- \/each -->\n?/g, (_, field, body) => {
  const arr = get(data, field);
  if (!Array.isArray(arr) || arr.length === 0) return '';
  return arr.map(el => body.replace(/\{\{item(?:\.([\w]+))?\}\}/g,
    (_, k) => String(k ? (el?.[k] ?? '') : el))).join('');
});
// scalars
t = t.replace(/\{\{([\w.]+)\}\}/g, (_, f) => { const v = get(data, f); return v==null ? '' : String(v); });
process.stdout.write(t);
NODE
