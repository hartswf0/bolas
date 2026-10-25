// usage: node shootmany.mjs <outdir> <crop x,y,w,h|full> t1 t2 ...   (renders scene times in one session, writes a tiled contact sheet)
import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const { chromium } = require(require.resolve('playwright', { paths: ['/opt/node-tools/node_modules'] }));
import path from 'path'; import fs from 'fs';
const here = path.dirname(new URL(import.meta.url).pathname);
const [outdir, crop, ...ts] = process.argv.slice(2);
fs.mkdirSync(outdir, { recursive: true });
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => console.log('page:', m.text()));
await p.addInitScript(`window.SCORE=${fs.readFileSync(path.join(here, '../../score/threshold-score.json'))};`);
const texd = {}; for (const n of ['wash0', 'wash1', 'wash2', 'paper', 'wood', 'speck']) texd[n] = 'data:image/png;base64,' + fs.readFileSync(path.join(here, 'cache', n + '.png')).toString('base64');
await p.addInitScript(`window.TEXDATA=${JSON.stringify(texd)};`);
await p.goto('file://' + path.join(here, 'stage.html'));
await p.evaluate(async () => { await loadTextures('cache/'); await document.fonts.ready; await initScene(); });
const files = [];
for (const t of ts) {
  const f = 72 + Math.round(parseFloat(t) * 24);
  const r = await p.evaluate(([f, crop]) => { const m = renderFrame(f); let c = document.getElementById('c');
    if (crop !== 'full') { const [x, y, w, h] = crop.split(',').map(Number); const o = document.createElement('canvas'); o.width = w; o.height = h; const g = o.getContext('2d'); g.drawImage(c, x, y, w, h, 0, 0, w, h); g.fillStyle = '#fff'; g.font = '14px monospace'; g.fillText((f - 72) / 24 + 's', 6, 16); c = o; }
    return { url: c.toDataURL('image/png'), m: m ? { facing: m.facing, fam: m.fam, u: m.u, cx: m.meas && m.meas.cx, line: m.dogLineMean } : null }; }, [f, crop]);
  const fn = path.join(outdir, `t${t}.png`); fs.writeFileSync(fn, Buffer.from(r.url.split(',')[1], 'base64')); files.push(fn);
  console.log(t, JSON.stringify(r.m));
}
await b.close();
fs.writeFileSync(path.join(outdir, 'list.txt'), files.join('\n'));
