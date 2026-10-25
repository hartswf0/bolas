// node sheet.js <out_dir> : renders the extreme-view diagnostic sheets
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const out = process.argv[2] || '.';
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1600, height: 1000 } });
  p.on('console', m => console.log('page:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('file://' + path.join(__dirname, 'sheet.html'));
  for (const k of (process.argv[3] || 'body,head,pose').split(',')) {
    const d = await p.evaluate(k => window.sheet(k), k);
    fs.writeFileSync(path.join(out, 'sheet_' + k + '.png'), Buffer.from(d.split(',')[1], 'base64'));
  }
  await b.close();
})();
