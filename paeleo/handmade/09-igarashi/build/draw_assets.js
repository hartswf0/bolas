// Render every source drawing (build/drawings.js) to a transparent PNG in assets/drawings/, plus a contact sheet.
// node build/draw_assets.js
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const HERE = __dirname, OUT = path.join(HERE, '..', 'assets', 'drawings');
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.setContent('<html><body></body></html>');
  await p.addScriptTag({ content: fs.readFileSync(path.join(HERE, 'drawings.js'), 'utf8') });
  const res = await p.evaluate(() => {
    const out = {};
    for (const [id, d] of Object.entries(window.DRAWINGS.D)) {
      for (const layer of (d.layers || [null])) {
        const c = document.createElement('canvas'); c.width = d.w; c.height = d.h;
        const ctx = c.getContext('2d'); d.draw(ctx, layer);
        const key = layer ? id + '.' + layer : id;
        out[key] = c.toDataURL('image/png');
      }
    }
    // contact sheet on a dusk-grey ground with the handles marked
    const sheet = document.createElement('canvas'); sheet.width = 1600; sheet.height = 1200;
    const s = sheet.getContext('2d'); s.fillStyle = '#6d7480'; s.fillRect(0, 0, 1600, 1200);
    let x = 10, y = 10, rowH = 0;
    for (const [id, d] of Object.entries(window.DRAWINGS.D)) {
      if (x + d.w > 1600) { x = 10; y += rowH + 10; rowH = 0; }
      for (const layer of (d.layers || [null])) { s.save(); s.translate(x, y); d.draw(s, layer); s.restore(); }
      s.fillStyle = '#ff0'; for (const [k, h] of Object.entries(d.handles)) { s.beginPath(); s.arc(x + h[0], y + h[1], 3, 0, 7); s.fill(); }
      s.strokeStyle = '#0ff'; for (const f of d.features || []) { s.beginPath(); s.arc(x + f.c[0], y + f.c[1], f.r, 0, 7); s.stroke(); }
      s.fillStyle = '#fff'; s.font = '14px monospace'; s.fillText(id, x + 4, y + 14);
      x += d.w + 10; rowH = Math.max(rowH, d.h);
    }
    out.__sheet = sheet.toDataURL('image/png');
    return out;
  });
  for (const [k, v] of Object.entries(res)) {
    const f = k === '__sheet' ? path.join(HERE, 'cache', 'drawings_sheet.png') : path.join(OUT, k + '.png');
    fs.mkdirSync(path.dirname(f), { recursive: true });
    fs.writeFileSync(f, Buffer.from(v.split(',')[1], 'base64'));
  }
  console.log('drawings:', Object.keys(res).filter(k => k !== '__sheet').join(' '));
  await b.close();
})();
