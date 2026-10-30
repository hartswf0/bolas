/* SCION 19 renderer driver (Node + Playwright Chromium).
   node render.js scene <outdir> [from] [to] [step]   -> JPEG frames s_%04d.jpg + measures.json (one record per frame)
   node render.js card <title|end> <out.jpg>                                                                           */
const fs = require('fs'), path = require('path');
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const HERE = __dirname, ROOT = path.resolve(HERE, '../../../..');
const score = JSON.parse(fs.readFileSync(path.join(ROOT, 'paeleo/handmade/score/threshold-score.json'), 'utf8'));
(async () => {
  const [mode, a1, a2, a3, a4] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exitCode = 2; });
  await page.goto('file://' + path.join(HERE, 'scene.html'));
  await page.evaluate(async () => { await document.fonts.load('italic 400 30px Literata'); await document.fonts.load('400 23px Literata'); await document.fonts.load('600 22px "JetBrains Mono"'); await document.fonts.load('800 92px "Big Shoulders Display"'); await document.fonts.ready; });
  if (mode === 'scene') {
    const out = a1; fs.mkdirSync(out, { recursive: true });
    await page.evaluate(s => Scene.init(s), score);
    const from = +(a2 || 0), to = +(a3 || score.frames.length - 1), step = +(a4 || 1);
    const meas = [];
    for (let i = from; i <= to; i += step) {
      const r = await page.evaluate(i => window.renderFrame(i, 0.9), i);
      fs.writeFileSync(path.join(out, 's_' + String(i).padStart(4, '0') + '.jpg'), Buffer.from(r.url.split(',')[1], 'base64'));
      delete r.url; r.i = i; meas.push(r);
      if (i % 96 === 0) console.log('frame', i);
    }
    fs.writeFileSync(path.join(out, 'measures.json'), JSON.stringify(meas));
  } else if (mode === 'card') {
    const lines = a1 === 'end' ? JSON.parse(fs.readFileSync(path.join(HERE, 'endcard.json'), 'utf8')) : [];
    const url = await page.evaluate(([w, l]) => { const c = document.getElementById('c').getContext('2d'); Cards.draw(c, w, l); return document.getElementById('c').toDataURL('image/jpeg', 0.92); }, [a1, lines]);
    fs.writeFileSync(a2, Buffer.from(url.split(',')[1], 'base64'));
  }
  await browser.close();
})();
