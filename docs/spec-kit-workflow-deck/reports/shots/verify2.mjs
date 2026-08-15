import { chromium } from 'file:///Users/wangzhi/.hermes/node/lib/node_modules/omniroute/node_modules/playwright-core/index.mjs';
const url = 'file://' + process.cwd() + '/spec-kit-workflow.bento.html';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(url, { waitUntil: 'load' });
await page.waitForTimeout(1500);

// 检查 bento 全局 API
const api = await page.evaluate(() => {
  const w = window;
  return {
    hasBento: !!w.bento,
    bentoKeys: w.bento ? Object.keys(w.bento) : [],
    hasPresent: !!(w.bento && typeof w.bento.present === 'function'),
  };
});
console.log('API:', JSON.stringify(api));

// 尝试用 API 进入演示模式
await page.evaluate(() => { try { window.bento?.present?.(); } catch(e) {} });
await page.waitForTimeout(1200);
const inPresent = await page.evaluate(() => {
  const body = document.body.innerText.slice(0, 80);
  const hasToolbar = /文本|形状|图片|媒体|表格/.test(document.body.innerText.slice(0, 200));
  return { snippet: body.replace(/\n+/g,' | '), toolbarStillVisible: hasToolbar };
});
console.log('AFTER_PRESENT:', JSON.stringify(inPresent));

// 数一下当前可见的 slide 或 page 指示器
const pageInfo = await page.evaluate(() => {
  const nums = [...document.querySelectorAll('*')].map(e=>e.textContent).filter(t=>/^\d+\s*\/\s*\d+$/.test(t.trim()));
  return nums.slice(0,3);
});
console.log('PAGE_INDICATOR:', JSON.stringify(pageInfo));
await page.screenshot({ path: 'reports/shots/p02-present-check.png' });
await browser.close();
