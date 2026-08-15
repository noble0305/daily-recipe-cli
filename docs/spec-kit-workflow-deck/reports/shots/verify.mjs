import { chromium } from 'file:///Users/wangzhi/.hermes/node/lib/node_modules/omniroute/node_modules/playwright-core/index.mjs';

const url = 'file://' + process.cwd() + '/spec-kit-workflow.bento.html';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

await page.goto(url, { waitUntil: 'load' });
await page.waitForTimeout(1800);

const info = await page.evaluate(() => {
  const slides = document.querySelectorAll('[class*="slide"]');
  const title = document.querySelector('title')?.textContent;
  const body = document.body.innerText.slice(0, 100);
  return { slideCount: slides.length, title, bodySnippet: body.replace(/\n+/g, ' | ') };
});
console.log('INFO:', JSON.stringify(info));

await page.keyboard.press('F').catch(() => {});
await page.waitForTimeout(800);
await page.screenshot({ path: 'reports/shots/p01-present.png' });

const overflow = await page.evaluate(() => {
  const vw = window.innerWidth;
  const bad = [];
  document.querySelectorAll('*').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.right > vw + 2 && r.width > 0) bad.push(String(el.className).slice(0, 40) + ' right=' + Math.round(r.right));
  });
  return bad.slice(0, 12);
});
console.log('OVERFLOW:', JSON.stringify(overflow));
console.log('ERRORS:', JSON.stringify(errors));
await browser.close();
