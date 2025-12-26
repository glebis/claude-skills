#!/usr/bin/env node
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// Template configurations with dimensions
const TEMPLATES = {
  // Instagram
  'instagram/story-announcement': { width: 1080, height: 1920 },
  'instagram/story-quote': { width: 1080, height: 1920 },
  'instagram/post-title': { width: 1080, height: 1350 },
  'instagram/post-tips': { width: 1080, height: 1350 },
  'instagram/post-event': { width: 1080, height: 1350 },
  // YouTube
  'youtube/thumbnail': { width: 1280, height: 720 },
  'youtube/shorts-cover': { width: 1080, height: 1920 },
  // Social
  'social/cover-banner': { width: 1584, height: 396 },
  'social/tiktok': { width: 1080, height: 1920 },
  'social/twitter-post': { width: 1200, height: 675 },
  'social/pinterest-pin': { width: 1000, height: 1500 },
};

async function renderTemplate(templateName, outputPath) {
  const config = TEMPLATES[templateName];
  if (!config) {
    console.error(`Unknown template: ${templateName}`);
    console.log('Available templates:', Object.keys(TEMPLATES).join(', '));
    process.exit(1);
  }

  const templatePath = path.resolve(__dirname, '..', 'assets', 'templates', `${templateName}.html`);

  if (!fs.existsSync(templatePath)) {
    console.error(`Template file not found: ${templatePath}`);
    process.exit(1);
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: config.width, height: config.height },
    deviceScaleFactor: 1,
  });

  const page = await context.newPage();
  await page.goto(`file://${templatePath}`, { waitUntil: 'networkidle' });

  // Wait for fonts to load
  await page.waitForTimeout(1000);

  const finalOutput = outputPath || path.resolve(__dirname, '..', 'output', 'templates', `${templateName.replace('/', '-')}.png`);

  // Ensure output directory exists
  const outputDir = path.dirname(finalOutput);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  await page.screenshot({ path: finalOutput, type: 'png' });

  await browser.close();

  console.log(`Rendered: ${templateName} -> ${finalOutput}`);
  return finalOutput;
}

async function renderAll() {
  console.log('Rendering all templates...\n');

  for (const templateName of Object.keys(TEMPLATES)) {
    await renderTemplate(templateName);
  }

  console.log('\nAll templates rendered!');
}

// CLI handling
const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Social Media Template Renderer
==============================

Usage:
  node render-templates.js                     Render all templates
  node render-templates.js --template NAME     Render specific template
  node render-templates.js --list              List available templates

Options:
  --template, -t NAME   Template to render (e.g., instagram/story-announcement)
  --output, -o PATH     Custom output path for the PNG
  --list, -l            List all available templates
  --help, -h            Show this help

Examples:
  node render-templates.js --template instagram/story-announcement
  node render-templates.js -t youtube/thumbnail -o custom-thumbnail.png
`);
  process.exit(0);
}

if (args.includes('--list') || args.includes('-l')) {
  console.log('Available templates:\n');
  for (const [name, config] of Object.entries(TEMPLATES)) {
    console.log(`  ${name.padEnd(35)} ${config.width}x${config.height}`);
  }
  process.exit(0);
}

const templateIndex = args.findIndex(a => a === '--template' || a === '-t');
const outputIndex = args.findIndex(a => a === '--output' || a === '-o');

if (templateIndex !== -1) {
  const templateName = args[templateIndex + 1];
  const outputPath = outputIndex !== -1 ? args[outputIndex + 1] : null;
  renderTemplate(templateName, outputPath).catch(console.error);
} else {
  renderAll().catch(console.error);
}
