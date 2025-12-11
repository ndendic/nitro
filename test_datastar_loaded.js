const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    page.on('console', msg => console.log('BROWSER:', msg.text()));

    await page.goto('http://localhost:8000/test/signals', { waitUntil: 'networkidle2' });

    // Wait a bit for modules to load
    await new Promise(r => setTimeout(r, 2000));

    // Check if Datastar loaded
    const datastarCheck = await page.evaluate(() => {
        // Check various ways Datastar might be available
        const checks = {
            windowDatastar: typeof window.Datastar,
            dataAttributes: document.querySelectorAll('[data-on-click]').length,
            signalAttributes: document.querySelectorAll('[data-signals]').length,
            datastarScript: !!document.querySelector('script[src*="datastar"]'),
        };
        return checks;
    });

    console.log('Datastar checks:', JSON.stringify(datastarCheck, null, 2));

    await browser.close();
})();
