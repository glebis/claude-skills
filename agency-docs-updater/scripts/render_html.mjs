#!/usr/bin/env node
// Render a local HTML file to an image with Playwright (file:// navigation, so
// relative fonts/images load, and we wait for document.fonts.ready).
// Playwright is borrowed from youtube-uploader's node_modules.
// Usage: render_html.mjs IN.html OUT.(jpg|png) WIDTH HEIGHT [quality]
import { createRequire } from 'module';
import { pathToFileURL } from 'url';
import path from 'path';
import os from 'os';

import { execSync } from 'child_process';

// Resolve playwright: youtube-uploader's node_modules first, then global npm root.
function loadPlaywright() {
  const uploader = process.env.YOUTUBE_UPLOADER_DIR || path.join(os.homedir(), 'ai_projects/youtube-uploader');
  const bases = [path.join(uploader, 'package.json')];
  try { bases.push(path.join(execSync('npm root -g').toString().trim(), 'noop.js')); } catch {}
  for (const base of bases) {
    try { return createRequire(base)('playwright'); } catch {}
  }
  console.error('playwright not found — run: cd $YOUTUBE_UPLOADER_DIR && npm install && npx playwright install chromium');
  process.exit(1);
}
const { chromium } = loadPlaywright();

const [input, output, w, h, q] = process.argv.slice(2);
if (!input || !output || !w || !h) {
  console.error('usage: render_html.mjs IN.html OUT.jpg WIDTH HEIGHT [quality]');
  process.exit(2);
}
// Bundled headless shell first; fall back to installed Chrome (a separate headless
// process — never touches the user's open browser).
let browser;
for (const opts of [{}, { channel: 'chrome' }, { channel: 'chrome-beta' }]) {
  try { browser = await chromium.launch(opts); break; } catch {}
}
if (!browser) {
  console.error('no Chromium available — run: npx playwright install chromium');
  process.exit(1);
}
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
await page.goto(pathToFileURL(path.resolve(input)).href, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);
const missing = await page.evaluate(() =>
  [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src.slice(-60)));
if (missing.length) console.warn('WARN images failed to load:', missing);
const type = /\.png$/i.test(output) ? 'png' : 'jpeg';
await page.screenshot({ path: output, type, ...(type === 'jpeg' ? { quality: +(q || 92) } : {}) });
await browser.close();
console.log(output);
