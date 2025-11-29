#!/usr/bin/env node
/**
 * Export Slides
 *
 * Export presentation HTML to PNG slides, PDF, or video using Playwright.
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function exportSlides(htmlPath, options = {}) {
  const { format = 'png', output, width = 1920, height = 1080, duration = 6 } = options;

  if (!fs.existsSync(htmlPath)) {
    console.error(`File not found: ${htmlPath}`);
    process.exit(1);
  }

  const absolutePath = path.resolve(htmlPath);

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: 1,
  });

  const page = await context.newPage();
  await page.goto(`file://${absolutePath}`, { waitUntil: 'networkidle' });

  // Wait for fonts to load
  await page.waitForTimeout(1500);

  if (format === 'pdf') {
    // Export as PDF
    const pdfPath = output || htmlPath.replace('.html', '.pdf');
    await page.pdf({
      path: pdfPath,
      width: `${width}px`,
      height: `${height}px`,
      printBackground: true,
      preferCSSPageSize: true,
    });
    console.log(`Exported PDF: ${pdfPath}`);

  } else if (format === 'png') {
    // Export individual slides as PNGs
    const outputDir = output || path.dirname(htmlPath);
    const baseName = path.basename(htmlPath, '.html');

    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Get all slides
    const slides = await page.$$('.slide');
    console.log(`Found ${slides.length} slides`);

    for (let i = 0; i < slides.length; i++) {
      // Scroll to slide
      await page.evaluate((index) => {
        const slides = document.querySelectorAll('.slide');
        slides[index].scrollIntoView({ behavior: 'instant' });
      }, i);

      await page.waitForTimeout(300);

      // Screenshot the slide
      const slideNum = String(i + 1).padStart(2, '0');
      const pngPath = path.join(outputDir, `${baseName}-slide-${slideNum}.png`);

      await page.screenshot({
        path: pngPath,
        clip: {
          x: 0,
          y: i * height,
          width: width,
          height: height,
        },
      });

      console.log(`Exported: ${pngPath}`);
    }

  } else if (format === 'video' || format === 'webm') {
    // Export as video with auto-scrolling slides
    await browser.close();

    const videoDir = path.dirname(output || htmlPath.replace('.html', '.webm'));
    if (!fs.existsSync(videoDir)) {
      fs.mkdirSync(videoDir, { recursive: true });
    }

    const videoBrowser = await chromium.launch();

    // First, create a prep page WITHOUT video recording to pre-load fonts
    const prepContext = await videoBrowser.newContext({
      viewport: { width, height },
      deviceScaleFactor: 1,
    });

    const prepPage = await prepContext.newPage();
    await prepPage.goto(`file://${absolutePath}`, { waitUntil: 'networkidle' });
    await prepPage.waitForTimeout(2000); // Wait for fonts

    const slideCount = await prepPage.evaluate(() => {
      return document.querySelectorAll('.slide').length;
    });

    console.log(`Recording video: ${slideCount} slides, ${duration}s per slide`);
    console.log(`Total duration: ~${slideCount * duration}s`);

    await prepPage.close();
    await prepContext.close();

    // Create the video recording context
    const videoContext = await videoBrowser.newContext({
      viewport: { width, height },
      deviceScaleFactor: 1,
      recordVideo: {
        dir: videoDir,
        size: { width, height },
      },
    });

    const videoPage = await videoContext.newPage();

    // Set video recording mode flag before loading
    await videoPage.addInitScript(() => {
      window.videoRecordingMode = true;
    });

    // Load presentation - elements are hidden by CSS in the template itself
    await videoPage.goto(`file://${absolutePath}`, { waitUntil: 'networkidle' });

    // Set up for video mode
    await videoPage.evaluate(() => {
      // Disable scroll-snap for smooth programmatic scrolling
      document.documentElement.style.scrollSnapType = 'none';
      document.documentElement.style.scrollBehavior = 'auto';

      // Mark all slides as not animated
      document.querySelectorAll('.slide').forEach(slide => {
        slide.dataset.animated = 'false';
      });

      // Set first nav dot as active
      const dots = document.querySelectorAll('.nav-dot');
      if (dots[0]) dots[0].classList.add('active');
    });

    // Wait for fonts to fully load
    await videoPage.waitForTimeout(500);

    // Auto-scroll through slides with animation triggers
    for (let i = 0; i < slideCount; i++) {
      console.log(`Recording slide ${i + 1}/${slideCount}...`);

      // Scroll to slide using window.scrollTo for reliable positioning
      await videoPage.evaluate(({ index, viewportHeight }) => {
        window.scrollTo({
          top: index * viewportHeight,
          behavior: 'instant'
        });

        // Update navigation dots manually
        const dots = document.querySelectorAll('.nav-dot');
        dots.forEach((dot, j) => {
          dot.classList.toggle('active', j === index);
        });
      }, { index: i, viewportHeight: height });

      // Brief pause to ensure scroll completed
      await videoPage.waitForTimeout(200);

      // Trigger animations for current slide
      await videoPage.evaluate((index) => {
        const slides = document.querySelectorAll('.slide');
        const slide = slides[index];

        // Call the animateSlide function if available
        if (typeof animateSlide === 'function') {
          animateSlide(slide);
        }
      }, i);

      // Wait for animations to play + remaining slide duration
      await videoPage.waitForTimeout(duration * 1000);
    }

    // Small pause at the end
    await videoPage.waitForTimeout(1000);

    // Close page to finalize video
    await videoPage.close();

    // Get the recorded video path
    const video = videoPage.video();
    if (video) {
      const tempVideoPath = await video.path();
      const finalVideoPath = output || htmlPath.replace('.html', '.webm');

      // Move video to final destination
      fs.renameSync(tempVideoPath, finalVideoPath);
      console.log(`Exported video: ${finalVideoPath}`);
    }

    await videoBrowser.close();
    return;

  } else {
    console.error(`Unknown format: ${format}. Use 'png', 'pdf', or 'video'.`);
  }

  await browser.close();
}

// CLI handling
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.includes('--help')) {
    console.log(`
Export Slides
=============

Export presentation HTML to PNG slides, PDF, or video.

Usage:
  node export-slides.js presentation.html --format png --output ./slides/
  node export-slides.js presentation.html --format pdf --output output.pdf
  node export-slides.js presentation.html --format video --output output.webm

Options:
  --format, -f    Output format: png, pdf, or video (default: png)
  --output, -o    Output path (directory for PNG, file for PDF/video)
  --width, -w     Slide width in pixels (default: 1920)
  --height        Slide height in pixels (default: 1080)
  --duration, -d  Seconds per slide for video (default: 6)
  --help          Show this help

Examples:
  node export-slides.js deck.html -f png -o ./export/
  node export-slides.js deck.html -f pdf -o deck.pdf
  node export-slides.js deck.html -f video -o deck.webm -d 5
`);
    process.exit(0);
  }

  const htmlPath = args.find(a => !a.startsWith('-'));
  if (!htmlPath) {
    console.error('Error: HTML file path is required');
    process.exit(1);
  }

  const formatIndex = args.findIndex(a => a === '--format' || a === '-f');
  const outputIndex = args.findIndex(a => a === '--output' || a === '-o');
  const widthIndex = args.findIndex(a => a === '--width' || a === '-w');
  const heightIndex = args.findIndex(a => a === '--height');
  const durationIndex = args.findIndex(a => a === '--duration' || a === '-d');

  const options = {
    format: formatIndex !== -1 ? args[formatIndex + 1] : 'png',
    output: outputIndex !== -1 ? args[outputIndex + 1] : null,
    width: widthIndex !== -1 ? parseInt(args[widthIndex + 1]) : 1920,
    height: heightIndex !== -1 ? parseInt(args[heightIndex + 1]) : 1080,
    duration: durationIndex !== -1 ? parseInt(args[durationIndex + 1]) : 6,
  };

  exportSlides(htmlPath, options).catch(console.error);
}

module.exports = { exportSlides };
