// node build/tools/sheet.js OUT.png K cols key1 key2 ...   (preview a set of dog sprites)
const { chromium } = require('playwright'), fs = require('fs'), path = require('path');
(async () => {
  const [out, K, cols, ...keys] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => console.log('console', m.text()));
  await p.goto('file://' + path.join(__dirname, '..', 'sheet.html'));
  const full = keys.map(k => { const o = {}; k.split(',').forEach(kv => { const [a, v] = kv.split('='); o[a] = +v; });
    return ['yaw','hy','hp','ear','tl','wag','cr','lie','g','br','rs','sn'].map(a => a + '=' + (o[a] ?? (a === 'g' ? -1 : 0))).join(','); });
  const d = await p.evaluate(([k, K, c]) => sheet(k, c, K), [full, +K, +cols]);
  fs.writeFileSync(out, Buffer.from(d.split(',')[1], 'base64')); await b.close();
})();
