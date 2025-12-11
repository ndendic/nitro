#!/usr/bin/env node

/**
 * Simple browser automation tool for headless environments
 * Usage: node simple_browser.js <url> <screenshot_path>
 */

const puppeteer = require('puppeteer');

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: node simple_browser.js <url> <screenshot_path>');
    process.exit(1);
  }

  const [url, screenshotPath] = args;

  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu'
    ]
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 1024 });

    console.log(`Navigating to: ${url}`);
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });

    // Wait a bit for any dynamic content
    await new Promise(resolve => setTimeout(resolve, 1000));

    console.log(`Taking screenshot: ${screenshotPath}`);
    await page.screenshot({ path: screenshotPath, fullPage: true });

    console.log('Success!');
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

main();
