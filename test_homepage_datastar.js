const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    page.on('console', msg => console.log('BROWSER:', msg.text()));

    await page.goto('http://localhost:8000/', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    // Try to change theme
    const initialTheme = await page.evaluate(() => {
        return document.documentElement.getAttribute('data-theme');
    });
    console.log('Initial theme:', initialTheme);

    // Click theme selector (if it exists and works)
    const hasThemeSelect = await page.evaluate(() => {
        const select = document.querySelector('select[data-bind="theme"]');
        return !!select;
    });
    console.log('Has theme select:', hasThemeSelect);

    if (hasThemeSelect) {
        await page.select('select[data-bind="theme"]', 'candy');
        await new Promise(r => setTimeout(r, 500));

        const updatedTheme = await page.evaluate(() => {
            return document.documentElement.getAttribute('data-theme');
        });
        console.log('Updated theme:', updatedTheme);
        console.log(initialTheme === updatedTheme ? 'FAIL: Theme did not change' : 'SUCCESS: Theme changed!');
    }

    await browser.close();
})();
