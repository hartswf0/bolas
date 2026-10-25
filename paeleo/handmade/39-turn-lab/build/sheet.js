// Proof sheet of the drawing atlas: node build/sheet.js out.png '[pose,...]' — each pose drawn in its own cell with its pivots marked.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const out = process.argv[2] || 'sheet.png';
  const poses = JSON.parse(process.argv[3] || '[]');
  const cols = +(process.argv[4] || 5);
  const b = await chromium.launch(); const pg = await b.newPage();
  await pg.setContent('<canvas id=c></canvas>');
  await pg.addScriptTag({ path: path.join(__dirname, 'dog.js') });
  const data = await pg.evaluate(({ poses, cols }) => {
    const cw = 300, ch = 300, rows = Math.ceil(poses.length / cols);
    const c = document.getElementById('c'); c.width = cw * cols; c.height = ch * rows; const ctx = c.getContext('2d');
    ctx.fillStyle = '#efe7d6'; ctx.fillRect(0, 0, c.width, c.height);
    poses.forEach((p, i) => {
      const ox = (i % cols) * cw + cw / 2, oy = Math.floor(i / cols) * ch + ch * 0.78, S = 190;
      ctx.save(); ctx.strokeStyle = '#c9bca2'; ctx.strokeRect((i % cols) * cw, Math.floor(i / cols) * ch, cw, ch);
      ctx.beginPath(); ctx.moveTo(ox - 140, oy); ctx.lineTo(ox + 140, oy); ctx.stroke();
      ctx.fillStyle = '#7a6a50'; ctx.font = '12px monospace'; ctx.fillText(p.label || JSON.stringify({ b: p.body, h: p.headYaw, lie: p.lie }), (i % cols) * cw + 6, Math.floor(i / cols) * ch + 14);
      ctx.translate(ox, oy); ctx.scale(S, -S);
      const m = DOG.build(p); DOG.paintDog(ctx, m, { seed: 1 });
      if (p.pivots) { ctx.fillStyle = 'red'; for (const q of [m.Bs, m.Ns, m.Ts]) { ctx.beginPath(); ctx.arc(q[0], q[1], 0.01, 0, 7); ctx.fill(); } }
      ctx.restore();
    });
    return c.toDataURL('image/png');
  }, { poses, cols });
  fs.writeFileSync(out, Buffer.from(data.split(',')[1], 'base64'));
  await b.close();
})();
