const puppeteer = require('puppeteer');

(async () => {
    console.log('Testing Playground...');
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    page.on('console', msg => {
        const text = msg.text();
        if (!text.includes('Persist') && !text.includes('WARN') && !text.includes('Failed to load')) {
            console.log('BROWSER:', text);
        }
    });
    page.on('pageerror', err => console.error('PAGE ERROR:', err));

    await page.goto('http://localhost:8000/playground/code', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    // Get initial output
    const initialOutput = await page.evaluate(() => {
        return document.querySelector('#output-console code').textContent;
    });
    console.log('Initial output:', initialOutput.substring(0, 50));

    // Click Run Code button
    console.log('Clicking Run Code button...');
    await page.click('#run-button');

    // Wait for SSE to complete
    await new Promise(r => setTimeout(r, 4000));

    // Get updated output
    const updatedOutput = await page.evaluate(() => {
        return document.querySelector('#output-console code').textContent;
    });
    console.log('Updated output:', updatedOutput);

    await page.screenshot({ path: 'playground_result.png', fullPage: true });

    await browser.close();

    if (updatedOutput.includes('Hello from the Nitro Playground')) {
        console.log('\n✅ SUCCESS: Playground is working!');
    } else {
        console.log('\n❌ FAIL: Playground did not execute code');
    }
})();
