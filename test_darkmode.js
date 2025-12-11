const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    page.on('console', msg => console.log('BROWSER:', msg.text()));

    await page.goto('http://localhost:8000/test/signals', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    // Check initial dark mode
    const initialHasDark = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark');
    });
    console.log('Initial dark mode:', initialHasDark);

    // Click dark mode toggle
    await page.click('button[data-on\\:click*="darkMode"]');
    await new Promise(r => setTimeout(r, 500));

    // Check updated dark mode
    const updatedHasDark = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark');
    });
    console.log('Updated dark mode:', updatedHasDark);
    console.log(initialHasDark === updatedHasDark ? 'FAIL: Dark mode did not toggle' : 'SUCCESS: Dark mode toggled!');

    await browser.close();
})();
