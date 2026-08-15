import { chromium } from 'file:///Users/wangzhi/.hermes/node/lib/node_modules/omniroute/node_modules/playwright-core/index.mjs';
const url = 'file://' + process.cwd() + '/spec-kit-workflow.bento.html';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage();
await page.goto(url, { waitUntil: 'load' });
await page.waitForTimeout(1500);
const model = await page.evaluate(() => {
  const doc = window.bento.doc;
  const slides = doc.slides;
  const ids = new Set(slides.map(s => s.id));
  const linkTargets = slides.flatMap(s => s.elements.filter(e => e.link).map(e => e.link));
  const missing = [...new Set(linkTargets)].filter(t => !ids.has(t));
  const stateParents = slides.filter(s => s.stateOf).map(s => ({ s: s.id, p: s.stateOf }));
  const orphanStates = stateParents.filter(x => !ids.has(x.p));
  const emptyNotes = slides.filter(s => !s.notes || !s.notes.trim()).map(s => s.id);
  const docId = doc.docId;
  return {
    slideCount: slides.length,
    linkTargets: [...new Set(linkTargets)],
    missingLinks: missing,
    stateSlides: stateParents.length,
    orphanStates,
    emptyNotes,
    docIdPresent: !!docId,
  };
});
console.log('MODEL:', JSON.stringify(model, null, 1));
await browser.close();
