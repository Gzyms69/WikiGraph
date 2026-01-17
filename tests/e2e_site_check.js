const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({ executablePath: require('chromium').path });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const url = 'https://gzyms69.github.io/WikiGraph/';
  console.log(`Visiting ${url}...`);
  
  try {
    await page.goto(url, { waitUntil: 'networkidle' });
    
    // 1. Test "View Documentation" button
    console.log('Testing "View Documentation" navigation...');
    await page.click('text=View Documentation');
    await page.waitForURL('**/docs', { timeout: 5000 });
    console.log(`Successfully navigated to: ${page.url()}`);
    
    // 2. Check for Docs content
    const docsHeading = await page.locator('h1').innerText();
    console.log(`Docs Heading: ${docsHeading}`);

    // 3. Navigate back to Home
    await page.goBack();
    
    // 4. Test "Explore" scroll
    console.log('Testing "Explore" scroll...');
    const initialY = await page.evaluate(() => window.scrollY);
    await page.click('text=Explore the Nebula');
    await page.waitForTimeout(1000); // Wait for smooth scroll
    const scrolledY = await page.evaluate(() => window.scrollY);
    console.log(`Initial Y: ${initialY}, Scrolled Y: ${scrolledY}`);
    console.log(`Scroll Success: ${scrolledY > initialY}`);

  } catch (err) {
    console.error(`FAILED: ${err.message}`);
  } finally {
    await browser.close();
  }
})();
