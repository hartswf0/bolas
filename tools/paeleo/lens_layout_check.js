// Computed layout check for the lenses, every 4th frame of each lens's reel window: text boxes never intersect,
// stay inside the frame (below the caption, above the prompt line), and cover at most 15% of the dog. node tools/paeleo/lens_layout_check.js
const { chromium } = require('playwright'), path = require('path');
(async () => { const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('file://' + path.join(__dirname, 'lens_render.html')); await p.evaluate(() => window.ready);
  const bad = await p.evaluate(() => { const out = []; const c = document.getElementById('c'), g = c.getContext('2d');
    for (let i = 0; i < 54; i++) { const L = Scion.LENSES[i], t0 = Math.max(0, (L.still || 18.5) - .8); const R = Scion.make(c);
      for (let f = 0; f < 39; f += 4) { R.draw(i, t0 + f / 24); const bx = Scion.LAYOUT.boxes, d = Scion.LAYOUT.dog;
        for (let a = 0; a < bx.length; a++) { const r = bx[a];
          if (r.ratio !== undefined && r.ratio < 4.5) out.push([i + 1, f, 'contrast', +r.ratio.toFixed(2)]);
          if (r[0] < 0 || r[2] > 1280 || r[1] < 100 || r[3] > 670) out.push([i + 1, f, 'edge', r.map(Math.round)]);
          for (let k = a + 1; k < bx.length; k++) { const q = bx[k]; if (r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1]) out.push([i + 1, f, 'overlap']); }
          let n = 0; for (let x = r[0] + 3; x < r[2]; x += 6) for (let y = r[1] + 3; y < r[3]; y += 6) if (g.isPointInPath(d.path, x, y)) n++;
          if (d.area && n * 36 / d.area > .15) out.push([i + 1, f, 'dog', +(n * 36 / d.area).toFixed(2)]); } } }
    return out; });
  const by = {}; for (const [l, f, k] of bad) (by[l] = by[l] || new Set()).add(k);
  console.log(bad.length ? 'problems: ' + Object.entries(by).map(([l, s]) => l + ':' + [...s].join('/')).join(' ') : 'layout clean: no overlaps, nothing off-frame, no label over 15% of the dog, every label at 4.5:1 or better');
  await b.close(); })();
