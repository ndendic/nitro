const puppeteer = require('puppeteer');

(async () => {
    console.log('Launching browser...');
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // Enable console logging
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('error', err => console.error('ERROR:', err));
    page.on('pageerror', err => console.error('PAGE ERROR:', err));

    console.log('Navigating to playground...');
    await page.goto('http://localhost:8000/playground/code', { waitUntil: 'networkidle2' });

    console.log('Taking initial screenshot...');
    await page.screenshot({ path: 'test_pg_1_initial.png', fullPage: true });

    // Check if Datastar is loaded
    const datastarLoaded = await page.evaluate(() => {
        return typeof window.Datastar !== 'undefined' || document.querySelector('[data-signals]') !== null;
    });
    console.log('Datastar loaded:', datastarLoaded);

    // Get initial signal values
    const initialSignals = await page.evaluate(() => {
        const el = document.querySelector('[data-signals*="output"]');
        return el ? el.getAttribute('data-signals') : 'Not found';
    });
    console.log('Initial signals:', initialSignals);

    console.log('Clicking Test Simple button...');

    // Listen for network requests
    page.on('request', request => {
        if (request.url().includes('playground/execute')) {
            console.log('REQUEST:', request.url());
        }
    });

    page.on('response', async response => {
        if (response.url().includes('playground/execute')) {
            console.log('RESPONSE:', response.status(), response.statusText());
            const text = await response.text();
            console.log('RESPONSE BODY:', text);
        }
    });

    await page.click('#test-button');

    console.log('Waiting for SSE response...');
    await new Promise(r => setTimeout(r, 3000));

    console.log('Taking after-click screenshot...');
    await page.screenshot({ path: 'test_pg_2_after_click.png', fullPage: true });

    // Get output text
    const outputText = await page.evaluate(() => {
        const output = document.querySelector('#output-console code');
        return output ? output.textContent : 'Not found';
    });
    console.log('Output text:', outputText);

    // Get signal values after click
    const afterSignals = await page.evaluate(() => {
        const el = document.querySelector('[data-signals*="output"]');
        return el ? el.getAttribute('data-signals') : 'Not found';
    });
    console.log('After signals:', afterSignals);

    await browser.close();
    console.log('Done!');
})();
