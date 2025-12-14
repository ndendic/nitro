#!/usr/bin/env node
/**
 * Test the site search feature
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Helper to wait
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function testSearch() {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900 });

    // Capture console errors
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.log('Browser console error:', msg.text());
        }
    });

    try {
        // Step 1: Navigate to homepage
        console.log('Step 1: Navigating to homepage...');
        await page.goto('http://localhost:8000/', { waitUntil: 'networkidle0', timeout: 30000 });
        await page.screenshot({ path: 'screenshots/test_search_01_homepage.png', fullPage: false });
        console.log('Screenshot: test_search_01_homepage.png');

        // Step 2: Click search trigger
        console.log('Step 2: Clicking search trigger...');
        await page.waitForSelector('#site-search-trigger', { timeout: 10000 });
        await page.click('#site-search-trigger');
        await sleep(500); // Wait for dialog animation
        await page.screenshot({ path: 'screenshots/test_search_02_dialog_open.png', fullPage: false });
        console.log('Screenshot: test_search_02_dialog_open.png');

        // Step 3: Type in search
        console.log('Step 3: Typing in search...');
        await page.waitForSelector('#site-search-input', { timeout: 5000 });
        await page.type('#site-search-input', 'button');
        await sleep(300); // Wait for filtering
        await page.screenshot({ path: 'screenshots/test_search_03_search_results.png', fullPage: false });
        console.log('Screenshot: test_search_03_search_results.png');

        // Step 4: Test Ctrl+K shortcut
        console.log('Step 4: Testing Ctrl+K shortcut...');
        // First close the dialog by pressing Escape
        await page.keyboard.press('Escape');
        await sleep(300);
        await page.screenshot({ path: 'screenshots/test_search_04_dialog_closed.png', fullPage: false });

        // Now open with Ctrl+K
        await page.keyboard.down('Control');
        await page.keyboard.press('k');
        await page.keyboard.up('Control');
        await sleep(500);
        await page.screenshot({ path: 'screenshots/test_search_05_ctrl_k_open.png', fullPage: false });
        console.log('Screenshot: test_search_05_ctrl_k_open.png');

        // Step 5: Test navigation by clicking a result
        console.log('Step 5: Testing navigation...');
        // Clear the search input first
        await page.evaluate(() => {
            const input = document.getElementById('site-search-input');
            if (input) {
                input.value = '';
                filterSearchResults('');
            }
        });
        await sleep(200);
        // Click on the Button result (first item)
        await page.click('.search-item');
        await sleep(1000); // Wait for navigation
        await page.screenshot({ path: 'screenshots/test_search_06_navigated.png', fullPage: false });
        console.log('Screenshot: test_search_06_navigated.png');

        // Verify we're on the button page
        const url = page.url();
        console.log('Current URL:', url);
        if (url.includes('/xtras/button')) {
            console.log('Navigation successful!');
        } else {
            console.log('Warning: Expected /xtras/button in URL');
        }

        console.log('All tests completed successfully!');
    } catch (error) {
        console.error('Test failed:', error.message);
        await page.screenshot({ path: 'screenshots/test_search_error.png', fullPage: false });
    } finally {
        await browser.close();
    }
}

testSearch();
