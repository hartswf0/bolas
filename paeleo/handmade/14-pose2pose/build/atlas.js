// Render the illustration bank as an atlas sheet (the pose atlas), using the same drawing core as the film.
// node build/atlas.js bank/bank.json proof/pose_atlas.png [cols] [scale] [only-ids,comma]
const { chromium } = require('/opt/node-tools/node_modules/playwright'), fs = require('fs'), path = require('path');
(async () => {
  const bank = JSON.parse(fs.readFileSync(process.argv[2]));
  const out = process.argv[3], cols = +(process.argv[4] || 6), sc = +(process.argv[5] || 1);
  const only = process.argv[6] ? process.argv[6].split(',') : null;
  const ids = Object.keys(bank.drawings).filter(k => !only || only.includes(k));
  const cw = 270 * sc, ch = 230 * sc, rows = Math.ceil(ids.length / cols);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: cw * cols, height: ch * rows } });
  await p.setContent('<canvas id=c></canvas>');
  await p.addScriptTag({ path: path.join(__dirname, 'draw.js') });
  await p.evaluate(([bank, ids, cols, cw, ch, sc]) => {
    const c = document.getElementById('c'); c.width = cw * cols; c.height = ch * Math.ceil(ids.length / cols);
    const x = c.getContext('2d'); x.fillStyle = '#d8d2c4'; x.fillRect(0, 0, c.width, c.height);
    ids.forEach((id, i) => {
      const ox = (i % cols) * cw, oy = Math.floor(i / cols) * ch, d = bank.drawings[id];
      x.save(); x.translate(ox + cw / 2, oy + ch - 34 * sc); x.scale(sc * (id.startsWith('P_') ? .6 : 1), sc * (id.startsWith('P_') ? .6 : 1));
      x.strokeStyle = 'rgba(0,0,0,.25)'; x.beginPath(); x.moveTo(-130, 0); x.lineTo(130, 0); x.stroke();
      drawDrawing(x, d.parts); x.restore();
      x.fillStyle = '#222'; x.font = `${12 * sc}px monospace`; x.fillText(id, ox + 6, oy + ch - 10 * sc);
      if (d.meta && d.meta.note) { x.fillStyle = '#555'; x.fillText(d.meta.note.slice(0, 40), ox + 6, oy + 14 * sc); }
    });
  }, [bank, ids, cols, cw, ch, sc]);
  await p.locator('#c').screenshot({ path: out }); await b.close(); console.log('atlas', ids.length, out);
})();
