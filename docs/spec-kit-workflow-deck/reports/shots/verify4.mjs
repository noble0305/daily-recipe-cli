import { chromium } from 'file:///Users/wangzhi/.hermes/node/lib/node_modules/omniroute/node_modules/playwright-core/index.mjs';
const url = 'file://' + process.cwd() + '/spec-kit-workflow.bento.html';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(url, { waitUntil: 'load' });
await page.waitForTimeout(1500);

// 点击「在此标签页中演示」
await page.getByText('在此标签页中演示').click().catch(async () => {
  await page.evaluate(() => {
    [...document.querySelectorAll('button')].find(b => b.textContent.includes('演示'))?.click();
  });
});
await page.waitForTimeout(1500);

const presentState = await page.evaluate(() => {
  const body = document.body.innerText.slice(0, 120);
  return { toolbarGone: !/文本|形状|图片|媒体/.test(body), snippet: body.replace(/\n+/g, ' | ') };
});
console.log('PRESENT_STATE:', JSON.stringify(presentState));

// 截图演示态封面
await page.screenshot({ path: 'reports/shots/p04-present-cover.png' });

// 翻页到目录页（第 2 页）：按 ArrowRight
await page.keyboard.press('ArrowRight');
await page.waitForTimeout(900);
const agenda = await page.evaluate(() => document.body.innerText.slice(0, 150).replace(/\n+/g,' | '));
console.log('AGENDA_PAGE:', agenda);
await page.screenshot({ path: 'reports/shots/p05-present-agenda.png' });

// 验证目录链接可点击跳转：点击「03 主链路六步」所在卡片区域
await page.mouse.click(300, 330); // agenda 第二行第一列卡片附近
await page.waitForTimeout(1000);
const flowPage = await page.evaluate(() => document.body.innerText.slice(0, 120).replace(/\n+/g,' | '));
console.log('AFTER_CLICK_AGENDA2:', flowPage);

// 点击流程节点 1（specify）
await page.mouse.click(160, 350);
await page.waitForTimeout(1000);
const specifyState = await page.evaluate(() => document.body.innerText.slice(0, 150).replace(/\n+/g,' | '));
console.log('AFTER_CLICK_FLOW1:', specifyState);
await page.screenshot({ path: 'reports/shots/p06-state-specify.png' });

// ← 应返回父页
await page.keyboard.press('ArrowLeft');
await page.waitForTimeout(900);
const backToFlow = await page.evaluate(() => document.body.innerText.slice(0, 80).replace(/\n+/g,' | '));
console.log('AFTER_ARROWLEFT:', backToFlow);

await browser.close();
