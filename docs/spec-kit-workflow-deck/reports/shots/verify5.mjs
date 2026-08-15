import { chromium } from 'file:///Users/wangzhi/.hermes/node/lib/node_modules/omniroute/node_modules/playwright-core/index.mjs';
const url = 'file://' + process.cwd() + '/spec-kit-workflow.bento.html';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(url, { waitUntil: 'load' });
await page.waitForTimeout(1500);

const [popup] = await Promise.all([
  page.waitForEvent('popup', { timeout: 4000 }).catch(() => null),
  page.getByText('在此标签页中演示').click().catch(() => {}),
]);
if (popup) {
  await popup.waitForLoadState('domcontentloaded').catch(()=>{});
  await popup.waitForTimeout(1200);
  const p = await popup.evaluate(() => document.body.innerText.slice(0, 100).replace(/\n+/g,' | '));
  console.log('POPUP_PRESENT:', p);
  await popup.screenshot({ path: 'reports/shots/p07-popup-present.png' });
  // 翻页
  await popup.keyboard.press('ArrowRight');
  await popup.waitForTimeout(800);
  const p2 = await popup.evaluate(() => document.body.innerText.slice(0, 120).replace(/\n+/g,' | '));
  console.log('POPUP_AFTER_RIGHT:', p2);
  await popup.screenshot({ path: 'reports/shots/p08-popup-agenda.png' });
} else {
  console.log('NO_POPUP — 尝试页面内翻页');
  await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(800);
  console.log(await page.evaluate(() => document.body.innerText.slice(0, 100).replace(/\n+/g,' | ')));
}
await browser.close();
