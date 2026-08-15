import { chromium } from 'file:///Users/wangzhi/.hermes/node/lib/node_modules/omniroute/node_modules/playwright-core/index.mjs';
const url = 'file://' + process.cwd() + '/spec-kit-workflow.bento.html';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(url, { waitUntil: 'load' });
await page.waitForTimeout(1500);

// 找按钮：标题含演示/播放/present/▶/全屏
const btns = await page.evaluate(() => {
  const out = [];
  document.querySelectorAll('button, [role="button"], [aria-label]').forEach(el => {
    const t = (el.textContent || '').trim().slice(0, 12);
    const aria = el.getAttribute('aria-label') || '';
    if (/演示|播放|present|全屏|▶|Play|Present/i.test(t + ' ' + aria)) {
      out.push({ tag: el.tagName, text: t, aria: aria.slice(0, 30) });
    }
  });
  return out.slice(0, 10);
});
console.log('PRESENT_BTNS:', JSON.stringify(btns));

// 尝试常见快捷键 F / P / Shift+F
for (const key of ['F', 'p', 'Shift+F']) {
  await page.keyboard.press(key).catch(()=>{});
  await page.waitForTimeout(400);
}
const after = await page.evaluate(() => document.body.innerText.slice(0, 60).replace(/\n+/g,' | '));
console.log('AFTER_KEYS:', after);
await page.screenshot({ path: 'reports/shots/p03-afterkeys.png' });
await browser.close();
