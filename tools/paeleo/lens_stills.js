// Stills of every SCION lens, each at its own moment (a lens's `still`, else T). node tools/paeleo/lens_stills.js OUTDIR [T]  (then resize into paeleo/media/scion/)
const { chromium } = require('playwright'), fs = require('fs'), path = require('path');
(async () => {
  const out = path.resolve(process.argv[2]); fs.mkdirSync(out, { recursive: true }); const T = +(process.argv[3] || 15.5);
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('file://' + path.join(__dirname, 'lens_render.html')); await p.evaluate(() => window.ready);
  const n = await p.evaluate(() => Scion.LENSES.length);
  for (let i = 0; i < n; i++) { const d = await p.evaluate(([i, t]) => shot(i, Scion.LENSES[i].still || t), [i, T]); fs.writeFileSync(path.join(out, `lens-${String(i + 1).padStart(2, '0')}.jpg`), Buffer.from(d.split(',')[1], 'base64')); }
  await b.close(); console.log(n, 'lenses');
})();
