#!/usr/bin/env node
/**
 * Simple browser automation tool for visual testing
 * Usage: node browser_tool.js <command> [args...]
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Store browser instance for session persistence
const BROWSER_DATA_PATH = '/tmp/browser_tool_data';

async function getBrowser() {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    return browser;
}

async function navigate(url, screenshotPath) {
    const browser = await getBrowser();
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 2000 });

    // Capture console errors
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.log('Browser console error:', msg.text());
        }
    });

    // Capture request failures
    page.on('requestfailed', request => {
        console.log('Request failed:', request.url(), request.failure().errorText);
    });

    try {
        await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });

        if (screenshotPath) {
            const dir = path.dirname(screenshotPath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            await page.screenshot({ path: screenshotPath, fullPage: true });
            console.log(`Screenshot saved to: ${screenshotPath}`);
        }

        console.log(`Navigated to: ${url}`);
    } finally {
        await browser.close();
    }
}

async function click(selector, screenshotPath, url) {
    const browser = await getBrowser();
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    try {
        // Navigate to URL if provided
        if (url) {
            await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
        }
        await page.waitForSelector(selector, { timeout: 10000 });
        await page.click(selector);

        if (screenshotPath) {
            const dir = path.dirname(screenshotPath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            await page.screenshot({ path: screenshotPath, fullPage: true });
            console.log(`Screenshot saved to: ${screenshotPath}`);
        }

        console.log(`Clicked: ${selector}`);
    } finally {
        await browser.close();
    }
}

async function typeText(selector, text, screenshotPath) {
    const browser = await getBrowser();
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    try {
        await page.waitForSelector(selector, { timeout: 10000 });
        await page.type(selector, text);

        if (screenshotPath) {
            const dir = path.dirname(screenshotPath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            await page.screenshot({ path: screenshotPath, fullPage: true });
            console.log(`Screenshot saved to: ${screenshotPath}`);
        }

        console.log(`Typed "${text}" into: ${selector}`);
    } finally {
        await browser.close();
    }
}

async function getText(selector) {
    const browser = await getBrowser();
    const page = await browser.newPage();

    try {
        await page.waitForSelector(selector, { timeout: 10000 });
        const text = await page.$eval(selector, el => el.textContent);
        console.log(`Text content: ${text}`);
        return text;
    } finally {
        await browser.close();
    }
}

async function wait(ms) {
    await new Promise(resolve => setTimeout(resolve, parseInt(ms)));
    console.log(`Waited ${ms}ms`);
}

async function hover(selector, screenshotPath, url) {
    const browser = await getBrowser();
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    try {
        // Navigate to URL if provided
        if (url) {
            await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
        }
        await page.waitForSelector(selector, { timeout: 10000 });
        await page.hover(selector);

        // Wait a bit for CSS transitions
        await new Promise(resolve => setTimeout(resolve, 500));

        if (screenshotPath) {
            const dir = path.dirname(screenshotPath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            await page.screenshot({ path: screenshotPath, fullPage: false });
            console.log(`Screenshot saved to: ${screenshotPath}`);
        }

        console.log(`Hovered: ${selector}`);
    } finally {
        await browser.close();
    }
}

async function scrollAndCapture(url, screenshotPath, scrollAmount) {
    const browser = await getBrowser();
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    try {
        await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });

        // Debug: Check body dimensions
        const dimensions = await page.evaluate(() => {
            const main = document.querySelector('main');
            const allSections = document.querySelectorAll('section');
            const mainDiv = main?.querySelector('div.px-8 > div');
            const children = mainDiv ? Array.from(mainDiv.children).slice(0, 8).map(c => ({
                tag: c.tagName,
                offsetHeight: c.offsetHeight,
                cls: c.className?.substring(0, 50) || '',
                text: c.textContent?.substring(0, 30) || ''
            })) : [];
            return {
                bodyHeight: document.body.scrollHeight,
                mainHeight: main?.scrollHeight,
                mainDivChildren: mainDiv?.children?.length,
                childrenInfo: children,
                dialogCount: document.querySelectorAll('dialog').length,
                dialogOpenCount: document.querySelectorAll('dialog[open]').length
            };
        });
        console.log('Page dimensions:', JSON.stringify(dimensions, null, 2));

        // Scroll down
        await page.evaluate((amount) => {
            window.scrollBy(0, amount);
        }, parseInt(scrollAmount || 500));

        // Wait a bit for rendering
        await new Promise(resolve => setTimeout(resolve, 500));

        if (screenshotPath) {
            const dir = path.dirname(screenshotPath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            await page.screenshot({ path: screenshotPath, fullPage: false });
            console.log(`Screenshot saved to: ${screenshotPath}`);
        }

        console.log(`Scrolled ${scrollAmount}px and captured: ${url}`);
    } finally {
        await browser.close();
    }
}

// Main command router
const command = process.argv[2];
const args = process.argv.slice(3);

switch (command) {
    case 'navigate':
        navigate(args[0], args[1]).catch(console.error);
        break;
    case 'scrollCapture':
        scrollAndCapture(args[0], args[1], args[2]).catch(console.error);
        break;
    case 'click':
        click(args[0], args[1], args[2]).catch(console.error);
        break;
    case 'type':
        typeText(args[0], args[1], args[2]).catch(console.error);
        break;
    case 'getText':
        getText(args[0]).catch(console.error);
        break;
    case 'wait':
        wait(args[0]).catch(console.error);
        break;
    case 'hover':
        hover(args[0], args[1], args[2]).catch(console.error);
        break;
    default:
        console.log(`
Browser Testing Tool

Usage:
  node browser_tool.js navigate <url> [screenshot_path]
  node browser_tool.js click <selector> [screenshot_path]
  node browser_tool.js type <selector> <text> [screenshot_path]
  node browser_tool.js getText <selector>
  node browser_tool.js wait <milliseconds>
        `);
}
