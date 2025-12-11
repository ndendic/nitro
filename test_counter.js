const puppeteer = require('puppeteer');

(async () => {
    console.log('Testing simple counter page...');
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('pageerror', err => console.error('PAGE ERROR:', err));

    await page.goto('http://localhost:8000/test/signals', { waitUntil: 'networkidle2' });
    await page.screenshot({ path: 'test_counter_1.png' });

    // Get initial counter value
    const initialText = await page.evaluate(() => {
        return document.querySelector('code').textContent;
    });
    console.log('Initial text:', initialText);

    // Click increment button
    await page.click('button');
    await new Promise(r => setTimeout(r, 500));
    await page.screenshot({ path: 'test_counter_2.png' });

    // Get updated counter value
    const updatedText = await page.evaluate(() => {
        return document.querySelector('code').textContent;
    });
    console.log('Updated text:', updatedText);

    await browser.close();
    console.log(initialText === updatedText ? 'FAIL: Counter did not increment' : 'SUCCESS: Counter incremented!');
})();
