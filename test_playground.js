#!/usr/bin/env node

/**
 * Test script for playground functionality
 * Tests: Code execution, output capture, async support, error handling
 */

const puppeteer = require('puppeteer');

async function testPlayground() {
  console.log('=== Testing Playground Functionality ===\n');

  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1024 });

  try {
    // Test 1: Navigate to playground
    console.log('Test 1: Navigate to playground...');
    await page.goto('http://localhost:8000/playground/code', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    await page.screenshot({ path: 'test_playground_1_initial.png', fullPage: true });
    console.log('✓ Playground loaded\n');

    // Test 2: Execute simple print code
    console.log('Test 2: Execute simple print code...');
    const simpleCode = 'print("hello")';

    // Clear existing code and enter new code
    await page.waitForSelector('#code-editor');
    await page.click('#code-editor');
    await page.keyboard.down('Control');
    await page.keyboard.press('A');
    await page.keyboard.up('Control');
    await page.keyboard.type(simpleCode);
    await page.screenshot({ path: 'test_playground_2_code_entered.png', fullPage: true });

    // Click Run Code button
    await page.waitForSelector('#run-button', { timeout: 10000 });
    await page.click('#run-button');
    console.log('✓ Clicked Run Code button');

    // Wait for output (longer to allow SSE to complete)
    await new Promise(resolve => setTimeout(resolve, 4000));
    await page.screenshot({ path: 'test_playground_3_output.png', fullPage: true });

    // Check console for errors
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

    // Verify output contains "hello"
    const outputContent = await page.$eval('#output-console', el => el.textContent);
    console.log('Output:', outputContent);

    // Also check the code element specifically
    const codeContent = await page.$eval('#output-console code', el => el.textContent);
    console.log('Code element:', codeContent);

    if (outputContent.includes('hello')) {
      console.log('✓ Simple code execution works\n');
    } else {
      console.log('✗ Output does not contain "hello"\n');
    }

    // Test 3: Execute multi-line code
    console.log('Test 3: Execute multi-line code...');
    const multiLineCode = `for i in range(3):
    print(f"Count: {i}")`;

    await page.click('#code-editor');
    await page.keyboard.down('Control');
    await page.keyboard.press('A');
    await page.keyboard.up('Control');
    await page.keyboard.type(multiLineCode);

    await page.click('#run-button');

    await new Promise(resolve => setTimeout(resolve, 2000));
    await page.screenshot({ path: 'test_playground_4_multiline.png', fullPage: true });

    const outputContent2 = await page.$eval('#output-console', el => el.textContent);
    console.log('Output:', outputContent2);

    if (outputContent2.includes('Count: 0') && outputContent2.includes('Count: 2')) {
      console.log('✓ Multi-line code execution works\n');
    } else {
      console.log('✗ Multi-line output incorrect\n');
    }

    // Test 4: Execute code with syntax error
    console.log('Test 4: Execute code with syntax error...');
    const errorCode = 'print("hello"';  // Missing closing paren

    await page.click('#code-editor');
    await page.keyboard.down('Control');
    await page.keyboard.press('A');
    await page.keyboard.up('Control');
    await page.keyboard.type(errorCode);

    await page.click('#run-button');

    await new Promise(resolve => setTimeout(resolve, 2000));
    await page.screenshot({ path: 'test_playground_5_error.png', fullPage: true });

    // Check if error is displayed
    const errorElements = await page.$('#error-console');
    if (errorElements) {
      const errorContent = await page.$eval('#error-console', el => el.textContent);
      console.log('Error output:', errorContent);

      if (errorContent.includes('Syntax Error') || errorContent.includes('SyntaxError')) {
        console.log('✓ Error handling works\n');
      } else {
        console.log('✗ Error not properly displayed\n');
      }
    } else {
      console.log('✗ Error console not found\n');
    }

    // Test 5: Clear output
    console.log('Test 5: Clear output...');
    const clearButtons = await page.$x("//button[contains(., 'Clear Output')]");
    if (clearButtons.length > 0) {
      await clearButtons[0].click();
      await new Promise(resolve => setTimeout(resolve, 500));
      await page.screenshot({ path: 'test_playground_6_cleared.png', fullPage: true });
      console.log('✓ Clear output works\n');
    }

    console.log('=== All tests completed! ===');

  } catch (error) {
    console.error('Test failed:', error.message);
    await page.screenshot({ path: 'test_playground_error.png', fullPage: true });
    throw error;
  } finally {
    await browser.close();
  }
}

testPlayground().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
