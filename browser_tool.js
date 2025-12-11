#!/usr/bin/env node

/**
 * Enhanced browser automation tool for testing
 * Usage:
 *   node browser_tool.js navigate <url> <screenshot>
 *   node browser_tool.js click <selector> <screenshot>
 *   node browser_tool.js type <selector> <text> <screenshot>
 *   node browser_tool.js wait <ms>
 */

const puppeteer = require('puppeteer');

let browser;
let page;

async function launchBrowser() {
  if (!browser) {
    browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu'
      ]
    });
    page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 1024 });
  }
  return { browser, page };
}

async function navigate(url, screenshotPath) {
  const { page } = await launchBrowser();
  console.log(`Navigating to: ${url}`);
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
  await new Promise(resolve => setTimeout(resolve, 1000));

  if (screenshotPath) {
    console.log(`Taking screenshot: ${screenshotPath}`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
  }
  console.log('Navigation complete');
}

async function click(selector, screenshotPath) {
  const { page } = await launchBrowser();
  console.log(`Clicking: ${selector}`);
  await page.waitForSelector(selector, { timeout: 10000 });
  await page.click(selector);
  await new Promise(resolve => setTimeout(resolve, 1500));

  if (screenshotPath) {
    console.log(`Taking screenshot: ${screenshotPath}`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
  }
  console.log('Click complete');
}

async function type(selector, text, screenshotPath) {
  const { page } = await launchBrowser();
  console.log(`Typing into: ${selector}`);
  await page.waitForSelector(selector, { timeout: 10000 });
  await page.click(selector);
  await page.keyboard.type(text);
  await new Promise(resolve => setTimeout(resolve, 500));

  if (screenshotPath) {
    console.log(`Taking screenshot: ${screenshotPath}`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
  }
  console.log('Typing complete');
}

async function wait(ms) {
  console.log(`Waiting ${ms}ms...`);
  await new Promise(resolve => setTimeout(resolve, parseInt(ms)));
  console.log('Wait complete');
}

async function getText(selector) {
  const { page } = await launchBrowser();
  console.log(`Getting text from: ${selector}`);
  await page.waitForSelector(selector, { timeout: 10000 });
  const text = await page.$eval(selector, el => el.textContent);
  console.log(`Text: ${text}`);
  return text;
}

async function closeBrowser() {
  if (browser) {
    await browser.close();
    browser = null;
    page = null;
  }
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage:');
    console.error('  node browser_tool.js navigate <url> <screenshot>');
    console.error('  node browser_tool.js click <selector> <screenshot>');
    console.error('  node browser_tool.js type <selector> <text> <screenshot>');
    console.error('  node browser_tool.js wait <ms>');
    console.error('  node browser_tool.js getText <selector>');
    console.error('  node browser_tool.js close');
    process.exit(1);
  }

  const command = args[0];

  try {
    switch (command) {
      case 'navigate':
        await navigate(args[1], args[2]);
        break;
      case 'click':
        await click(args[1], args[2]);
        break;
      case 'type':
        await type(args[1], args[2], args[3]);
        break;
      case 'wait':
        await wait(args[1]);
        break;
      case 'getText':
        await getText(args[1]);
        break;
      case 'close':
        await closeBrowser();
        break;
      default:
        console.error(`Unknown command: ${command}`);
        process.exit(1);
    }

    // Don't close browser automatically - allows chaining commands
    console.log('Success!');
  } catch (error) {
    console.error('Error:', error.message);
    await closeBrowser();
    process.exit(1);
  }
}

main();
