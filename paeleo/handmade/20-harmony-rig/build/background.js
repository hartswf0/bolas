// SCION 20 · the painted background (BG node). Painted once in code: flat washes and gradients, then ~60k gouache
// dabs that sample the wash underneath (the brush texture). No line: in cel production the background is painted, the
// characters are inked. Screen units; the camera maps metres with X0=330, K=200, FLOOR=620.
'use strict';
window.paintBackground = (cam) => {
  const { X0, K, FLOOR } = cam; const sx = (x) => X0 + K * x;
  const c = H$.mk(2560, 1440), g = c.getContext('2d'); g.scale(2, 2);
  let seed = 20; const rnd = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296; };
  const IN = sx(0.34), OUT = sx(0.62), DOORTOP = FLOOR - K * 2.05, CEIL = 110, BACK = 560;
  const rect = (x, y, w, h, col) => { g.fillStyle = col; g.fillRect(x, y, w, h); };
  const lin = (x0, y0, x1, y1, stops) => { const gr = g.createLinearGradient(x0, y0, x1, y1); stops.forEach(([o, c_]) => gr.addColorStop(o, c_)); return gr; };
  // --- outside: dusk sky
  g.fillStyle = lin(0, 0, 0, BACK, [[0, '#161a3a'], [0.42, '#35305f'], [0.74, '#7c5371'], [0.9, '#c47a5e'], [1, '#e09a63']]);
  g.fillRect(OUT, 0, 1280 - OUT, BACK);
  for (let k = 0; k < 40; k++) { const x = OUT + rnd() * (1280 - OUT), y = 80 + rnd() * 200; g.fillStyle = `rgba(255,250,230,${0.3 + 0.5 * rnd()})`; g.beginPath(); g.arc(x, y, 0.6 + rnd() * 0.9, 0, 7); g.fill(); }
  // moon
  const mg = g.createRadialGradient(1090, 150, 10, 1090, 150, 120); mg.addColorStop(0, 'rgba(240,232,205,0.55)'); mg.addColorStop(1, 'rgba(240,232,205,0)');
  g.fillStyle = mg; g.fillRect(960, 20, 260, 260); g.fillStyle = '#efe6c8'; g.beginPath(); g.arc(1090, 150, 22, 0, 7); g.fill();
  g.fillStyle = 'rgba(200,190,170,0.5)'; g.beginPath(); g.arc(1084, 146, 5, 0, 7); g.arc(1097, 157, 3.5, 0, 7); g.fill();
  // hills and the far fence
  const hill = (base, amp, col, f) => { g.fillStyle = col; g.beginPath(); g.moveTo(OUT, BACK); for (let x = OUT; x <= 1280; x += 8) g.lineTo(x, base - amp * (0.5 + 0.5 * Math.sin(x * f + base)) - 6 * Math.sin(x * f * 3.7)); g.lineTo(1280, BACK); g.fill(); };
  hill(495, 34, '#3a3458', 0.006); hill(520, 22, '#2b2a46', 0.011);
  g.fillStyle = '#252338'; g.fillRect(OUT, 528, 1280 - OUT, BACK - 528);
  for (let x = OUT + 10; x < 1280; x += 34) { g.fillStyle = '#1e1d30'; g.fillRect(x, 512, 4, 20); }
  g.fillRect(OUT, 516, 1280 - OUT, 3);
  // trees (silhouettes, painted with dabs)
  const tree = (cx, top, w, col) => { g.fillStyle = col; g.fillRect(cx - 5, top + 120, 10, 420 - top); for (let k = 0; k < 260; k++) { const a = rnd() * 6.28, r = Math.sqrt(rnd()); g.beginPath(); g.ellipse(cx + Math.cos(a) * r * w, top + 80 + Math.sin(a) * r * w * 0.8, 10 + rnd() * 14, 8 + rnd() * 10, rnd() * 3, 0, 7); g.fill(); } };
  tree(1215, 250, 95, '#1b1b2e'); tree(700, 360, 60, '#232239');
  // --- porch roof (underside), post
  g.fillStyle = lin(0, 0, 0, 80, [[0, '#2a2024'], [1, '#3b2c2c']]); g.fillRect(OUT, 0, 1280 - OUT, 72);
  for (let x = OUT; x < 1280; x += 26) rect(x, 0, 2, 64, 'rgba(0,0,0,0.25)');
  rect(OUT, 62, 1280 - OUT, 18, '#4b3833'); rect(OUT, 78, 1280 - OUT, 4, '#2a1f22');
  const post = (x) => { rect(x - 11, 80, 22, BACK - 78, '#4f3f3a'); rect(x + 4, 80, 7, BACK - 78, '#3c302e'); rect(x - 15, BACK - 14, 30, 14, '#3f322f'); rect(x - 15, 80, 30, 10, '#3f322f'); };
  post(sx(2.65));
  // porch floor: boards run along the porch, seams and nail heads
  g.fillStyle = lin(0, BACK, 0, 640, [[0, '#4c3f48'], [1, '#6a5552']]); g.fillRect(OUT - 4, BACK, 1280 - OUT + 4, 640 - BACK);
  let yy = BACK; for (let k = 0; k < 7; k++) { const h = 8 + k * 2.2; yy += h; rect(OUT, yy, 1280 - OUT, 1.5, 'rgba(25,18,26,0.45)'); for (let j = 0; j < 7; j++) rect(OUT + rnd() * (1280 - OUT), yy - h, 1.4, h, 'rgba(25,18,26,0.35)'); }
  rect(OUT, 640, 1280 - OUT, 26, '#3a2e36'); rect(OUT, 640, 1280 - OUT, 3, '#7b6461');
  rect(OUT, 666, 1280 - OUT, 54, '#17141d');
  g.strokeStyle = 'rgba(70,58,66,0.7)'; g.lineWidth = 3; for (let x = OUT - 60; x < 1340; x += 26) { g.beginPath(); g.moveTo(x, 668); g.lineTo(x + 52, 720); g.moveTo(x + 52, 668); g.lineTo(x, 720); g.stroke(); }
  // --- inside: the room (cutaway)
  rect(0, 0, IN, CEIL, '#2e211d'); rect(0, CEIL - 6, IN, 8, '#5a3f2e');
  g.fillStyle = lin(0, CEIL, 0, 470, [[0, '#8e6a49'], [1, '#b08257']]); g.fillRect(0, CEIL, IN, 470 - CEIL);
  for (let x = 6; x < IN; x += 22) { rect(x, CEIL, 7, 470 - CEIL, 'rgba(120,70,40,0.18)'); for (let y = CEIL + 14; y < 470; y += 30) { g.fillStyle = 'rgba(240,210,160,0.18)'; g.beginPath(); g.arc(x + 14, y + (x % 44 ? 15 : 0), 2.4, 0, 7); g.fill(); } }
  rect(0, 466, IN, 8, '#5d3e29'); rect(0, 474, IN, 86, '#6e4a31'); for (let x = 12; x < IN - 20; x += 64) { g.strokeStyle = 'rgba(40,24,16,0.5)'; g.lineWidth = 2; g.strokeRect(x, 486, 50, 58); }
  rect(0, 548, IN, 12, '#4a3021');
  g.fillStyle = lin(0, BACK, 0, 640, [[0, '#5c3b28'], [1, '#7d5236']]); g.fillRect(0, BACK, IN, 640 - BACK);
  yy = BACK; for (let k = 0; k < 7; k++) { const h = 8 + k * 2.2; yy += h; rect(0, yy, IN, 1.5, 'rgba(30,16,10,0.45)'); }
  g.fillStyle = lin(0, BACK, 0, 640, [[0, '#5a4038'], [1, '#77553e']]); g.fillRect(IN, FLOOR - 4, OUT - IN, 644 - FLOOR);
  // floor and foundation cut (hatched section) under the room
  rect(0, 640, OUT, 80, '#21160f'); g.strokeStyle = 'rgba(120,90,70,0.35)'; g.lineWidth = 1.5; for (let x = -80; x < OUT; x += 12) { g.beginPath(); g.moveTo(x, 720); g.lineTo(x + 80, 640); g.stroke(); }
  rect(0, 638, OUT, 4, '#9a7457');
  // picture on the wall, rug, the stool, a lamp on a little table
  rect(112, 230, 70, 54, '#3d2a1e'); rect(117, 235, 60, 44, '#6f7d78'); g.fillStyle = '#c9a36b'; g.beginPath(); g.arc(150, 266, 7, 0, 7); g.fill(); rect(117, 268, 60, 11, '#4f5d50');
  // an inner doorway in the back wall: a lit hall going away into the house (the depth the dog looks into)
  { const hx0 = 236, hx1 = 340, hy0 = 330, hy1 = BACK;
    rect(hx0 - 9, hy0 - 10, hx1 - hx0 + 18, hy1 - hy0 + 10, '#5a3a24');
    g.fillStyle = lin(0, hy0, 0, hy1, [[0, '#e9b673'], [1, '#c98b4c']]); g.fillRect(hx0, hy0, hx1 - hx0, hy1 - hy0);
    const vx = 292, vy = 450; // vanishing point: walls, ceiling and floor of the hall converge
    g.fillStyle = '#b77a42'; g.beginPath(); g.moveTo(hx0, hy0); g.lineTo(vx - 16, vy - 40); g.lineTo(vx - 16, vy + 34); g.lineTo(hx0, hy1); g.fill();
    g.fillStyle = '#c88d52'; g.beginPath(); g.moveTo(hx1, hy0); g.lineTo(vx + 16, vy - 40); g.lineTo(vx + 16, vy + 34); g.lineTo(hx1, hy1); g.fill();
    g.fillStyle = '#9a6036'; g.beginPath(); g.moveTo(hx0, hy1); g.lineTo(vx - 16, vy + 34); g.lineTo(vx + 16, vy + 34); g.lineTo(hx1, hy1); g.fill();
    g.fillStyle = '#ffe2a8'; g.fillRect(vx - 16, vy - 40, 32, 74); g.fillStyle = '#f6c77e'; g.fillRect(vx - 7, vy - 22, 14, 56);
    g.strokeStyle = 'rgba(90,50,25,0.5)'; g.lineWidth = 1.2; for (let k = 1; k < 5; k++) { const yk = hy1 - (hy1 - vy - 34) * k / 5; g.beginPath(); g.moveTo(hx0 + (vx - 16 - hx0) * k / 5, yk); g.lineTo(hx1 - (hx1 - vx - 16) * k / 5, yk); g.stroke(); } }
  g.fillStyle = '#7a2e2a'; g.beginPath(); g.ellipse(250, 612, 120, 12, 0, 0, 7); g.fill(); g.strokeStyle = 'rgba(230,190,120,0.5)'; g.lineWidth = 2; g.beginPath(); g.ellipse(250, 612, 108, 9, 0, 0, 7); g.stroke();
  const stx = sx(-1.25); rect(stx - 38, FLOOR - 0.47 * K, 76, 10, '#6b4528'); rect(stx - 32, FLOOR - 0.47 * K + 10, 7, 0.47 * K - 10, '#55361f'); rect(stx + 25, FLOOR - 0.47 * K + 10, 7, 0.47 * K - 10, '#55361f'); rect(stx - 28, FLOOR - 40, 56, 5, '#55361f');
  rect(4, 470, 56, 6, '#5a3a24'); rect(10, 476, 5, 84, '#4a2e1c'); rect(50, 476, 5, 84, '#4a2e1c');
  rect(28, 430, 6, 40, '#c9a050'); g.fillStyle = '#e8c27a'; g.beginPath(); g.moveTo(10, 432); g.lineTo(52, 432); g.lineTo(44, 396); g.lineTo(18, 396); g.closePath(); g.fill();
  // --- the wall in section: cut above the door (hatched), the lintel, the far jamb face, the sill
  rect(IN, 0, OUT - IN, DOORTOP, '#3a2820'); g.strokeStyle = 'rgba(15,8,6,0.7)'; g.lineWidth = 2;
  g.save(); g.beginPath(); g.rect(IN, 0, OUT - IN, DOORTOP); g.clip(); for (let y = -80; y < DOORTOP + 80; y += 11) { g.beginPath(); g.moveTo(IN, y + 56); g.lineTo(OUT, y); g.stroke(); } g.restore();
  rect(IN - 6, DOORTOP - 14, OUT - IN + 12, 16, '#6e4b33'); rect(IN - 6, DOORTOP + 2, OUT - IN + 12, 3, '#2a1a12');
  g.fillStyle = lin(IN, 0, OUT, 0, [[0, '#6c5242'], [1, '#55413d']]); g.fillRect(IN, DOORTOP + 5, OUT - IN, FLOOR - DOORTOP - 5);
  rect(IN - 6, DOORTOP, 8, FLOOR - DOORTOP, '#5e412d'); rect(OUT - 2, DOORTOP, 8, FLOOR - DOORTOP, '#4a3428');
  // --- painting pass: dabs that sample the wash (gouache texture)
  const id = g.getImageData(0, 0, 2560, 1440).data;
  for (let k = 0; k < 90000; k++) {
    const x = rnd() * 1280, y = rnd() * 720, o = (((y * 2) | 0) * 2560 + ((x * 2) | 0)) * 4;
    const j = (rnd() - 0.5) * 22;
    g.fillStyle = `rgba(${id[o] + j | 0},${id[o + 1] + j | 0},${id[o + 2] + j * 1.2 | 0},0.22)`;
    g.beginPath(); g.ellipse(x, y, 2 + rnd() * 5, 1.2 + rnd() * 2.5, rnd() * 0.6 - 0.3, 0, 7); g.fill();
  }
  // the sill (threshold board) painted crisp on top
  rect(IN - 10, FLOOR - 10, OUT - IN + 22, 12, '#8a6646'); rect(IN - 10, FLOOR - 10, OUT - IN + 22, 2.5, '#b48a5e'); rect(IN - 10, FLOOR + 2, OUT - IN + 22, 3, '#3a2618');
  return c;
};
// the Light node's per-frame drawing: lamp glow in the room, the door's spill on the jamb, sill and porch
window.drawLight = (g, cam, fr, t) => {
  const { X0, K, FLOOR } = cam; const sx = (x) => X0 + K * x; const s = fr.spill;
  const IN = sx(0.34), OUT = sx(0.62), DOORTOP = FLOOR - K * 2.05;
  g.save(); g.globalCompositeOperation = 'lighter';
  const flick = 1 + 0.02 * Math.sin(t * 13) * Math.sin(t * 5.3);
  let rg = g.createRadialGradient(31, 420, 8, 31, 420, 330); rg.addColorStop(0, `rgba(255,190,110,${0.38 * flick})`); rg.addColorStop(0.4, 'rgba(160,90,40,0.12)'); rg.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = rg; g.fillRect(0, 0, IN, 720);
  // through the doorway: the jamb face and the opening, a sliver when ajar, full when open
  const a = 0.12 + 0.88 * s;
  let lg = g.createLinearGradient(IN, 0, OUT + 40, 0); lg.addColorStop(0, `rgba(255,190,110,${0.42 * a})`); lg.addColorStop(1, `rgba(255,170,90,${0.12 * a})`);
  g.fillStyle = lg; g.fillRect(IN, DOORTOP + 5, OUT - IN, FLOOR - DOORTOP - 5);
  // the spill on the porch floor and into the dusk
  if (s > 0.01) {
    const reach = OUT + (60 + 760 * s);
    g.beginPath(); g.moveTo(OUT, FLOOR - 64); g.lineTo(reach, 556); g.lineTo(reach + 120 * s, 646); g.lineTo(OUT, 646); g.closePath();
    const pg = g.createLinearGradient(OUT, 0, reach + 120, 0); pg.addColorStop(0, `rgba(255,185,105,${0.55 * s})`); pg.addColorStop(0.5, `rgba(230,140,70,${0.25 * s})`); pg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = pg; g.fill();
    const hg = g.createRadialGradient(OUT, FLOOR - 140, 10, OUT, FLOOR - 140, 420); hg.addColorStop(0, `rgba(255,170,90,${0.22 * s})`); hg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = hg; g.fillRect(OUT, FLOOR - 560, 460, 600);
  }
  // fireflies in the yard
  for (let k = 0; k < 6; k++) {
    const ph = t * (0.3 + 0.07 * k) + k * 1.7, x = 560 + ((k * 137) % 640) + 30 * Math.sin(ph * 1.3), y = 470 + 40 * Math.sin(ph + k), on = Math.max(0, Math.sin(t * (1.1 + 0.2 * k) + k * 2));
    const fg = g.createRadialGradient(x, y, 0, x, y, 7); fg.addColorStop(0, `rgba(230,255,150,${0.8 * on})`); fg.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = fg; g.fillRect(x - 8, y - 8, 16, 16);
  }
  g.restore();
};
