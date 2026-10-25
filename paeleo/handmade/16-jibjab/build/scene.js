// SCION 16 JibJab: the scene renderer. One performance (skeleton + channels), one face slot, any cast.
// Runs in Chromium (Playwright). All images arrive as data URLs from render.mjs. Nothing here is imported from the stage.
'use strict';
const W = 1280, H = 720, S = 205, CX = 290, FY = 615, K = 0.26, WALL = 0.55;
const HEADSCALE = 1.42, PPM = 400;
const P = (x, y, d) => [CX + S * x, FY - S * y - K * S * d];
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, u) => a + (b - a) * u;
const sstep = u => { u = clamp(u); return u * u * (3 - 2 * u); };
let IMG = {}, MAN = null, PERF = null, SK = null, QD = null;
let layers = {};

function mk(w = W, h = H) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
async function loadImg(src) { const im = new Image(); im.src = src; await im.decode(); return im; }

async function init(data) {
  MAN = data.manifest; PERF = data.perf; SK = data.skeleton; QD = data.qd;
  for (const [k, v] of Object.entries(data.images)) IMG[k] = await loadImg(v);
  for (const [name, b64] of Object.entries(data.fonts)) {
    const [fam, wt, st] = name.split('|');
    const ff = new FontFace(fam, `url(data:font/woff2;base64,${b64})`, { weight: wt, style: st });
    await ff.load(); document.fonts.add(ff);
  }
  layers.body = mk(); layers.head = mk(); layers.tmp = mk(); layers.person = mk();
  layers.mt = mk(320, 180); layers.mh = mk(320, 180); layers.md = mk(320, 180);
  layers.grain = [];
  let seed = 16;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  for (let g = 0; g < 6; g++) {
    const c = mk(640, 360), x = c.getContext('2d'), id = x.createImageData(640, 360);
    for (let p = 0; p < id.data.length; p += 4) { const v = 128 + (rnd() + rnd() + rnd() - 1.5) * 120; id.data[p] = id.data[p + 1] = id.data[p + 2] = v; id.data[p + 3] = 255; }
    x.putImageData(id, 0, 0); layers.grain.push(c);
  }
  return true;
}

// ------------------------------------------------------------------ world
function sky(ctx, t) {
  const dusk = clamp(t / 32);
  const g = ctx.createLinearGradient(0, 0, 0, 560);
  g.addColorStop(0, `rgb(${lerp(28, 16, dusk)},${lerp(36, 22, dusk)},${lerp(66, 46, dusk)})`);
  g.addColorStop(0.55, `rgb(${lerp(92, 60, dusk)},${lerp(80, 56, dusk)},${lerp(116, 92, dusk)})`);
  g.addColorStop(0.86, `rgb(${lerp(206, 150, dusk)},${lerp(140, 98, dusk)},${lerp(112, 96, dusk)})`);
  g.addColorStop(1, `rgb(${lerp(214, 150, dusk)},${lerp(160, 110, dusk)},${lerp(120, 100, dusk)})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, 600);
  // the moon: a stranger's Quick, Draw! moon (key_id in plates/qd.json), chalk on the sky
  const m = QD.moon.drawing; ctx.save(); ctx.translate(1105, 52); ctx.scale(0.34, 0.34);
  ctx.strokeStyle = 'rgba(244,236,214,0.92)'; ctx.fillStyle = 'rgba(240,232,206,0.28)'; ctx.lineWidth = 7; ctx.lineJoin = ctx.lineCap = 'round';
  for (const s of m) { ctx.beginPath(); s[0].forEach((x, k) => k ? ctx.lineTo(x, s[1][k]) : ctx.moveTo(x, s[1][k])); ctx.closePath(); ctx.fill(); ctx.stroke(); }
  ctx.restore();
  // distant trees and hedge: flat cut silhouettes
  ctx.fillStyle = 'rgb(30,34,52)';
  ctx.beginPath(); ctx.moveTo(800, 600);
  for (let x = 800; x <= 1290; x += 10) ctx.lineTo(x, 455 + 14 * Math.sin(x * 0.045) + 9 * Math.sin(x * 0.11 + 1));
  ctx.lineTo(1290, 600); ctx.fill();
  ctx.fillStyle = 'rgb(22,26,40)';
  for (const [x, y, r] of [[930, 395, 58], [985, 360, 70], [1050, 400, 50], [1215, 380, 64], [1260, 420, 44]]) { ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }
  ctx.fillRect(978, 380, 14, 120); ctx.fillRect(1210, 400, 12, 100);
}

function house(ctx, t, fr) {
  const wb = FY - K * S * WALL;           // wall base (screen y) 572
  // facade
  ctx.fillStyle = 'rgb(54,62,84)'; ctx.fillRect(0, 70, 820, wb - 70);
  ctx.strokeStyle = 'rgba(20,24,38,0.55)'; ctx.lineWidth = 2;
  for (let y = 90; y < wb; y += 26) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(820, y); ctx.stroke(); }
  ctx.fillStyle = 'rgba(255,255,255,0.04)';
  for (let y = 90; y < wb; y += 26) ctx.fillRect(0, y + 2, 820, 3);
  // eave and corner board
  ctx.fillStyle = 'rgb(34,38,56)'; ctx.fillRect(0, 50, 850, 30);
  ctx.fillStyle = 'rgb(70,78,100)'; ctx.fillRect(806, 70, 18, wb - 70);
  // window (dark, curtained)
  ctx.fillStyle = 'rgb(28,30,44)'; ctx.fillRect(560, 230, 150, 190);
  ctx.strokeStyle = 'rgb(92,100,124)'; ctx.lineWidth = 10; ctx.strokeRect(560, 230, 150, 190);
  ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(635, 230); ctx.lineTo(635, 420); ctx.moveTo(560, 325); ctx.lineTo(710, 325); ctx.stroke();
  // the doorway
  const [x0, yb] = P(-0.46, 0, WALL), [x1] = P(0.46, 0, WALL), yt = yb - S * 2.05;
  const open = fr.door_angle;
  const light = clamp((open - 12) / 60);
  // interior: a lit room through the opening
  ctx.save(); ctx.beginPath(); ctx.rect(x0, yt, x1 - x0, yb - yt); ctx.clip();
  const lv = 0.35 + 0.65 * light;
  const g = ctx.createLinearGradient(0, yt, 0, yb);
  g.addColorStop(0, `rgb(${120 * lv + 40},${80 * lv + 26},${46 * lv + 20})`);
  g.addColorStop(0.62, `rgb(${236 * lv},${178 * lv},${108 * lv})`);
  g.addColorStop(0.63, `rgb(${176 * lv},${110 * lv},${62 * lv})`);
  g.addColorStop(1, `rgb(${214 * lv},${142 * lv},${80 * lv})`);
  ctx.fillStyle = g; ctx.fillRect(x0, yt, x1 - x0, yb - yt);
  // a lamp glow on the far wall
  const lg = ctx.createRadialGradient(x0 + 70, yt + 150, 4, x0 + 70, yt + 150, 140);
  lg.addColorStop(0, `rgba(255,236,190,${0.9 * lv})`); lg.addColorStop(1, 'rgba(255,200,120,0)');
  ctx.fillStyle = lg; ctx.fillRect(x0, yt, x1 - x0, yb - yt);
  // floorboards inside, receding
  ctx.strokeStyle = `rgba(90,50,24,${0.5 * lv})`; ctx.lineWidth = 2;
  for (let k = 1; k < 6; k++) { const y = lerp(yt + 0.63 * (yb - yt), yb, (k / 6) ** 1.4); ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke(); }
  // the door plate (Straight Talk f028), hinged on the right jamb, swinging in
  const a = open * Math.PI / 180, dw = 0.92;
  const hx = x1, iw = IMG.door.width, ih = IMG.door.height;
  ctx.save();
  ctx.setTransform(-S * dw * Math.cos(a) / iw, -K * S * dw * Math.sin(a) / iw, 0, S * 2.05 / ih, hx, yt);
  ctx.filter = `brightness(${0.42 + 0.25 * light}) sepia(0.35)`;
  ctx.drawImage(IMG.door, 0, 0);
  ctx.filter = 'none';
  ctx.restore();
  ctx.restore();
  // trim
  ctx.fillStyle = 'rgb(108,116,140)';
  ctx.fillRect(x0 - 16, yt - 16, 16, yb - yt + 16); ctx.fillRect(x1, yt - 16, 16, yb - yt + 16); ctx.fillRect(x0 - 22, yt - 22, x1 - x0 + 44, 14);
  // the sill
  ctx.fillStyle = 'rgb(122,104,86)'; ctx.fillRect(x0 - 10, yb - 3, x1 - x0 + 20, 9);
  return { x0, x1, yb, yt, light };
}

function porch(ctx, t, D) {
  const wb = FY - K * S * WALL, fe = FY + K * S * 0.85;
  const g = ctx.createLinearGradient(0, wb, 0, fe);
  g.addColorStop(0, 'rgb(66,60,64)'); g.addColorStop(1, 'rgb(96,84,80)');
  ctx.fillStyle = g; ctx.fillRect(0, wb, W, fe - wb);
  // boards run along the porch; seams recede to the wall
  ctx.strokeStyle = 'rgba(30,24,26,0.55)'; ctx.lineWidth = 1.6;
  for (let k = 0; k <= 7; k++) { const y = lerp(wb, fe, k / 7); ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  // a back railing beyond the house corner, against the sky
  ctx.fillStyle = 'rgb(40,40,52)';
  ctx.fillRect(824, 470, W - 824, 10);
  for (let x = 840; x < W; x += 34) ctx.fillRect(x, 478, 9, wb - 478);
  ctx.fillRect(824, 470, 12, wb - 470);
  // front edge and the yard
  ctx.fillStyle = 'rgb(46,40,44)'; ctx.fillRect(0, fe, W, 12);
  ctx.fillStyle = 'rgb(24,26,32)'; ctx.fillRect(0, fe + 12, W, H - fe);
  // the steps at the far right
  const [sx] = P(4.9, 0, 0);
  ctx.fillStyle = 'rgba(20,18,22,0.5)'; ctx.fillRect(sx, wb, W - sx, fe - wb);
  // wall-base shadow
  const sh = ctx.createLinearGradient(0, wb, 0, wb + 26); sh.addColorStop(0, 'rgba(0,0,0,0.35)'); sh.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = sh; ctx.fillRect(0, wb, 820, 26);
}

function spill(ctx, hs) {
  if (hs.light <= 0.01) {
    // ajar: a sliver of light at the free (left) edge
    ctx.save(); ctx.globalCompositeOperation = 'screen';
    ctx.fillStyle = 'rgba(200,140,70,0.35)';
    ctx.beginPath(); ctx.moveTo(hs.x0 + 4, hs.yb); ctx.lineTo(hs.x0 + 22, hs.yb); ctx.lineTo(hs.x0 + 60, hs.yb + 90); ctx.lineTo(hs.x0 + 10, hs.yb + 90); ctx.fill();
    ctx.restore(); return;
  }
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const L = hs.light;
  const g = ctx.createLinearGradient(0, hs.yb, 0, hs.yb + 110);
  g.addColorStop(0, `rgba(236,170,92,${0.62 * L})`); g.addColorStop(1, 'rgba(236,170,92,0)');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(hs.x0, hs.yb); ctx.lineTo(hs.x1, hs.yb); ctx.lineTo(hs.x1 + 150, hs.yb + 110); ctx.lineTo(hs.x0 - 60, hs.yb + 110); ctx.fill();
  const r = ctx.createRadialGradient((hs.x0 + hs.x1) / 2, hs.yb, 10, (hs.x0 + hs.x1) / 2, hs.yb, 520);
  r.addColorStop(0, `rgba(200,130,60,${0.25 * L})`); r.addColorStop(1, 'rgba(200,130,60,0)');
  ctx.fillStyle = r; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// ------------------------------------------------------------------ the person: a cut-paper body plate with a doodle face slot and a hair matte
function person(ctx, fr, t, hs) {
  const p = fr.person, sit = sstep(p.sit), xw = p.x * 0.74, d = 0.42;
  const q = (dx, y, dd = 0) => P(xw + dx, y, d + dd);
  const lean = (p.voice === 'call' ? 0.05 : 0) + 0.08 * p.reach + 0.06 * p.low;
  const hip = [lerp(0, 0.02, sit), lerp(0.93, 0.13, sit)];
  const sh = [hip[0] + lean * 0.6, hip[1] + lerp(0.5, 0.5, sit)];
  const head = [sh[0] + lean * 0.4, sh[1] + 0.22];
  const c = layers.person, x = c.getContext('2d'); x.clearRect(0, 0, W, H);
  const cap = (a, b, r1, r2, col) => { capsule(x, a, b, r1 * S, r2 * S); x.fillStyle = col; x.fill(); };
  const OUT = 'rgb(24,18,20)';
  // legs
  for (const s of [-1, 1]) {
    const foot = [lerp(s * 0.11, 0.5 + s * 0.03, sit), 0.03, lerp(0, -0.08 + s * 0.04, sit)];
    const knee = [lerp(s * 0.1, 0.36 + s * 0.02, sit), lerp(0.48, 0.44 + s * 0.02, sit), lerp(0, -0.05 + s * 0.04, sit)];
    const hp = [hip[0] + s * 0.09, hip[1], 0];
    x.lineWidth = 3; x.strokeStyle = OUT;
    cap(q(...hp), q(...knee), 0.075, 0.06, 'rgb(40,44,60)'); x.stroke();
    cap(q(...knee), q(...foot), 0.06, 0.05, 'rgb(40,44,60)'); x.stroke();
    const fp = q(...foot); x.fillStyle = 'rgb(24,22,26)'; x.beginPath(); x.ellipse(fp[0] + s * 8, fp[1] + 4, 16, 8, 0, 0, 7); x.fill();
  }
  // torso: a sweater cut from paper
  const tq = [q(sh[0] - 0.2, sh[1]), q(sh[0] + 0.2, sh[1]), q(hip[0] + 0.17, hip[1] - 0.02), q(hip[0] - 0.17, hip[1] - 0.02)];
  x.beginPath(); tq.forEach((v, k) => k ? x.lineTo(...v) : x.moveTo(...v)); x.closePath();
  x.fillStyle = 'rgb(132,58,52)'; x.fill(); x.lineWidth = 3; x.strokeStyle = OUT; x.stroke();
  // arms: right arm (toward the dog) carries the commands and the offer
  const shR = [sh[0] + 0.19, sh[1] - 0.04], shL = [sh[0] - 0.19, sh[1] - 0.04];
  const rest = [shR[0] + 0.05, shR[1] - 0.63];
  const sitRest = [0.34, 0.5];
  let hand = [lerp(rest[0], sitRest[0], sit), lerp(rest[1], sitRest[1], sit)];
  const reach = [shR[0] + 0.64, shR[1] - 0.02], low = [0.72, 0.1], push = [-0.4 - xw, 0.86];
  hand = [lerp(hand[0], reach[0], p.reach), lerp(hand[1], reach[1], p.reach)];
  hand = [lerp(hand[0], push[0], p.push), lerp(hand[1], push[1], p.push)];
  hand = [lerp(hand[0], low[0], p.low), lerp(hand[1], low[1], p.low)];
  const handD = lerp(0, -0.12, p.low);
  const armL = 0.66, el = ik2(shR, hand, 0.33, 0.33, 1);
  x.lineWidth = 3;
  cap(q(...shR), q(...el), 0.055, 0.048, 'rgb(132,58,52)'); x.stroke();
  cap(q(...el), q(hand[0], hand[1], handD), 0.048, 0.04, 'rgb(132,58,52)'); x.stroke();
  const hq = q(hand[0], hand[1], handD);
  x.fillStyle = 'rgb(214,160,130)'; x.beginPath(); x.ellipse(hq[0] + 6, hq[1], 15, p.low > 0.5 ? 8 : 12, 0, 0, 7); x.fill(); x.stroke();
  // left arm: cupped to the mouth when calling
  const callUp = p.voice === 'call' ? clamp(p.mouth * 2) : 0;
  let lh = [lerp(shL[0] - 0.05, 0.3, sit), lerp(shL[1] - 0.63, 0.47, sit)];
  lh = [lerp(lh[0], head[0] - 0.1, callUp), lerp(lh[1], head[1] - 0.06, callUp)];
  const elL = ik2(shL, lh, 0.33, 0.33, -1);
  cap(q(...shL), q(...elL), 0.055, 0.048, 'rgb(122,52,48)'); x.stroke();
  cap(q(...elL), q(...lh), 0.048, 0.04, 'rgb(122,52,48)'); x.stroke();
  const lq = q(...lh); x.fillStyle = 'rgb(204,150,122)'; x.beginPath(); x.ellipse(lq[0], lq[1], 13, 11, 0, 0, 7); x.fill(); x.stroke();
  // neck, hair matte (behind), the doodle face sticker, hair matte (front fringe)
  const hc = q(...head), hr = 0.125 * S;
  x.fillStyle = 'rgb(200,146,118)'; x.fillRect(hc[0] - 12, hc[1] + hr * 0.6, 24, 22);
  x.fillStyle = 'rgb(46,30,24)'; x.beginPath(); x.ellipse(hc[0], hc[1] + 6, hr * 1.12, hr * 1.18, 0, 0, 7); x.fill();
  x.fillStyle = 'rgb(250,246,236)'; x.beginPath(); x.ellipse(hc[0], hc[1] + 4, hr * 0.9, hr * 1.02, 0, 0, 7); x.fill();
  const fd = QD.person_face.drawing; x.save(); x.translate(hc[0] - hr * 0.82, hc[1] - hr * 0.92); x.scale(hr * 1.64 / 255, hr * 1.94 / 255);
  x.strokeStyle = 'rgb(22,22,26)'; x.lineWidth = 255 / (hr * 1.64) * 2.6; x.lineJoin = x.lineCap = 'round';
  fd.forEach((s, k) => {
    if (k === 0) return;               // the face's own outline is replaced by the sticker edge
    x.beginPath();
    const my = k === 6 ? 179 : 0, open = k === 6 ? 1 + 2.4 * p.mouth : 1;
    s[0].forEach((px, j) => { const py = my + (s[1][j] - my) * open; j ? x.lineTo(px, py) : x.moveTo(px, py); });
    if (k === 6 && p.mouth > 0.25) x.closePath();
    x.stroke();
  });
  x.restore();
  x.fillStyle = 'rgb(46,30,24)'; x.beginPath(); x.ellipse(hc[0] + 4, hc[1] - hr * 0.86, hr * 0.95, hr * 0.34, -0.12, Math.PI, 2 * Math.PI); x.fill();
  // light: dusk on the body, warm from the door at its right side
  x.save(); x.globalCompositeOperation = 'source-atop';
  x.fillStyle = 'rgba(20,26,60,0.30)'; x.fillRect(0, 0, W, H);
  if (hs.light > 0) { const g = x.createRadialGradient(hs.x0 + 40, hs.yb - 160, 10, hs.x0 + 40, hs.yb - 160, 260); g.addColorStop(0, `rgba(255,180,100,${0.38 * hs.light})`); g.addColorStop(1, 'rgba(255,180,100,0)'); x.fillStyle = g; x.fillRect(0, 0, W, H); }
  x.restore();
  ctx.drawImage(c, 0, 0);
}

function ik2(a, b, l1, l2, s) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.min(Math.hypot(dx, dy), l1 + l2 - 1e-3) || 1e-3;
  const xx = (l1 * l1 - l2 * l2 + L * L) / (2 * L), h = Math.sqrt(Math.max(0, l1 * l1 - xx * xx));
  const ex = dx / (Math.hypot(dx, dy) || 1), ey = dy / (Math.hypot(dx, dy) || 1);
  return [a[0] + ex * xx - ey * h * s, a[1] + ey * xx + ex * h * s];
}

function capsule(x, a, b, r1, r2) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1e-3, ang = Math.atan2(dy, dx);
  const s = Math.asin(clamp((r1 - r2) / L, -1, 1));
  x.beginPath();
  x.arc(a[0], a[1], r1, ang + Math.PI / 2 + s, ang + 3 * Math.PI / 2 - s);
  x.arc(b[0], b[1], r2, ang - Math.PI / 2 - s, ang + Math.PI / 2 + s);
  x.closePath();
}

// ------------------------------------------------------------------ the dog: body plate + face slot + collar (neck matte)
const BODY = 'rgb(186,130,80)', BODYFAR = 'rgb(150,100,62)', OUTL = 'rgb(40,26,16)';
function viewFor(yaw) {
  const opts = [[180, 'L', 1], [135, 'BL', 1], [90, 'B', 1], [45, 'BL', -1], [0, 'L', -1]];
  let best = opts[0], bd = 1e9;
  for (const o of opts) { const dd = Math.abs(o[0] - yaw); if (dd < bd) { bd = dd; best = o; } }
  return { name: best[1], mir: best[2], key: best[0] };
}

function drawDog(ctx, i, castName, opts = {}) {
  const sk = SK.frames[i], fr = PERF.frames[i], t = fr.t;
  const B = layers.body, bx = B.getContext('2d'); bx.clearRect(0, 0, W, H);
  const Hc = layers.head, hx = Hc.getContext('2d'); hx.clearRect(0, 0, W, H);
  const pr = p => P(p[0], p[1], p[2]);
  // body parts in depth order (far first). depth = d
  const parts = [];
  const meanD = sk.spine.reduce((s, p) => s + p[2], 0) / sk.spine.length;
  parts.push({ d: meanD, kind: 'torso' });
  for (const [L, g] of Object.entries(sk.legs)) parts.push({ d: g.s[2], kind: 'leg', L, g });
  parts.push({ d: sk.tail[0][2] - 0.005, kind: 'tail' });
  parts.push({ d: sk.neck[2] - 0.004, kind: 'neck' });
  parts.sort((a, b) => b.d - a.d);
  const yaw = sk.yaw * Math.PI / 180;
  const outlineW = 3;
  for (const pt of parts) {
    if (pt.kind === 'torso') {
      const cs = sk.spine.map(p => [...pr(p), p[3] * S]);
      bx.fillStyle = OUTL;
      for (let k = 0; k < cs.length; k++) { bx.beginPath(); bx.arc(cs[k][0], cs[k][1], cs[k][2] + outlineW, 0, 7); bx.fill(); }
      bx.fillStyle = BODY;
      for (let k = 0; k < cs.length; k++) { bx.beginPath(); bx.arc(cs[k][0], cs[k][1], cs[k][2], 0, 7); bx.fill(); }
      // a lit plate: light from above, the belly in shade
      const ys = cs.map(c => c[1] - c[2]), ye = cs.map(c => c[1] + c[2]);
      const g = bx.createLinearGradient(0, Math.min(...ys), 0, Math.max(...ye));
      g.addColorStop(0, 'rgba(255,230,190,0.22)'); g.addColorStop(0.45, 'rgba(255,230,190,0)'); g.addColorStop(0.75, 'rgba(50,28,14,0.10)'); g.addColorStop(1, 'rgba(50,28,14,0.38)');
      bx.save(); bx.globalCompositeOperation = 'source-atop'; bx.fillStyle = g; bx.fillRect(0, 0, W, H); bx.restore();
    } else if (pt.kind === 'leg') {
      const g = pt.g, far = pt.d > meanD + 0.01;
      const s = pr(g.s), k = pr(g.k), f = pr(g.f), hind = pt.L[0] === 'H';
      const col = far ? BODYFAR : BODY;
      const r1 = (hind ? 0.085 : 0.062) * S, r2 = (hind ? 0.045 : 0.042) * S, r3 = 0.034 * S;
      bx.lineWidth = outlineW * 2; bx.strokeStyle = OUTL; bx.fillStyle = col;
      if (hind && fr.lie > 0.55) {
        // lying: the hind leg is drawn as one folded haunch (substitution, not a bent stick)
        const hm = [lerp(s[0], f[0], 0.45), lerp(s[1], f[1], 0.45) + 2];
        capsule(bx, s, hm, r1 * 1.15, r1 * 0.8); bx.stroke(); capsule(bx, hm, f, r1 * 0.8, r3); bx.stroke();
        capsule(bx, s, hm, r1 * 1.15, r1 * 0.8); bx.fill(); capsule(bx, hm, f, r1 * 0.8, r3); bx.fill();
      } else {
      capsule(bx, s, k, r1, r2); bx.stroke(); capsule(bx, k, f, r2 * 0.92, r3); bx.stroke();
      capsule(bx, s, k, r1, r2); bx.fill(); capsule(bx, k, f, r2 * 0.92, r3); bx.fill();
      }
      // paw: points along the body's forward direction (screen x sign)
      const fx = Math.cos(yaw), pw = 0.07 * S * (0.45 + 0.55 * Math.abs(fx));
      bx.lineWidth = outlineW; bx.beginPath(); bx.ellipse(f[0] + fx * pw * 0.45, f[1] + 1, pw, 0.03 * S, 0, 0, 7);
      bx.fillStyle = far ? 'rgb(120,80,50)' : 'rgb(150,104,66)'; bx.fill(); bx.stroke();
    } else if (pt.kind === 'tail') {
      const ps = sk.tail.map(pr);
      bx.lineCap = bx.lineJoin = 'round';
      for (const [w, c] of [[0.06 * S + outlineW * 2, OUTL], [0.06 * S, BODY]]) {
        for (let k = 0; k < ps.length - 1; k++) {
          bx.strokeStyle = c; bx.lineWidth = w * (1 - 0.55 * k / ps.length);
          bx.beginPath(); bx.moveTo(...ps[k]); bx.lineTo(...ps[k + 1]); bx.stroke();
        }
      }
      // pale tail tip
      const tp = ps[ps.length - 1]; bx.fillStyle = 'rgb(236,214,176)'; bx.beginPath(); bx.arc(tp[0], tp[1], 0.022 * S, 0, 7); bx.fill();
    } else if (pt.kind === 'neck') {
      const a = pr(sk.neck), b = pr(sk.head.collar);
      capsule(bx, a, b, 0.105 * S, 0.075 * S); bx.lineWidth = outlineW; bx.strokeStyle = OUTL; bx.stroke(); bx.fillStyle = BODY; bx.fill();
    }
  }
  // the fur: the archive dog's own torso (Amateur Film New Jersey C f008) laid into the plate
  if (!opts.flat) {
    const tx = layers.tmp.getContext('2d'); tx.clearRect(0, 0, W, H);
    tx.globalCompositeOperation = 'source-over';
    tx.fillStyle = tx.createPattern(IMG.fur, 'repeat'); tx.fillRect(0, 0, W, H);
    tx.globalCompositeOperation = 'destination-in'; tx.drawImage(B, 0, 0); tx.globalCompositeOperation = 'source-over';
    bx.save(); bx.globalCompositeOperation = 'multiply'; bx.globalAlpha = 0.7; bx.drawImage(layers.tmp, 0, 0); bx.restore();
    bx.save(); bx.globalCompositeOperation = 'destination-in'; bx.drawImage(layers.tmp, 0, 0); bx.restore();
  }
  // face slot
  const hd = sk.head, v = viewFor(hd.yaw);
  const cast = MAN.casts[castName];
  const cpt = pr(hd.collar);
  const sc = S * HEADSCALE / PPM;
  const pitch = hd.pitch * Math.PI / 180;
  const neckDir = (() => { const a = pr(sk.neck), b = cpt; const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1; return [(b[0] - a[0]) / l, (b[1] - a[1]) / l]; })();
  function collar() {
    // the neck matte: a leather collar where the face slot meets the body plate; its tag hangs and swings
    const perp = [-neckDir[1], neckDir[0]];
    const rx = 0.088 * S, ry = 0.026 * S, ca = Math.atan2(perp[1], perp[0]);
    const c0 = [cpt[0] - neckDir[0] * 9, cpt[1] - neckDir[1] * 9];
    hx.save(); hx.translate(c0[0], c0[1]); hx.rotate(ca);
    hx.fillStyle = 'rgb(104,30,30)'; hx.strokeStyle = OUTL; hx.lineWidth = 2.5;
    hx.beginPath(); hx.ellipse(0, 0, rx, ry, 0, 0, 7); hx.fill(); hx.stroke();
    hx.restore();
    const swing = Math.sin(t * 9) * 0.25 * (fr.lie < 0.5 ? 1 : 0.2);
    const tg = [c0[0] + Math.sin(swing) * 6, c0[1] + 0.03 * S];
    hx.fillStyle = 'rgb(200,164,78)'; hx.lineWidth = 2; hx.beginPath(); hx.arc(tg[0], tg[1], 5, 0, 7); hx.fill(); hx.stroke();
  }
  let headInfo = { view: v.name + (v.mir < 0 ? '~' : ''), yaw: hd.yaw };
  if (cast) {
    const vw = cast.views[v.name], im = IMG[`${castName}/${v.name}`];
    hx.save(); hx.translate(cpt[0], cpt[1]);
    let rot = 0, sy = 1;
    if (v.name === 'L') rot = v.mir > 0 ? pitch : -pitch;
    else if (v.name === 'BL') rot = (v.mir > 0 ? pitch : -pitch) * 0.6;
    else { sy = 1 + hd.pitch / 260; hx.translate(0, -hd.pitch * 0.35); }
    hx.rotate(rot); hx.scale(v.mir * sc, sc * sy);
    const ears = vw.ears || [];
    const ang = cast.ear_angles;
    const earAng = e => { if (!ang) return 0; return e < 0.5 ? lerp(ang.flat, ang.hang, e / 0.5) : lerp(ang.hang, ang.prick, Math.min(1.2, (e - 0.5) / 0.5)); };
    const drawEar = (e) => {
      const ei = IMG[e.png.replace('cast/', '').replace('.png', '')];
      hx.save(); hx.translate(e.at[0] - vw.socket[0], e.at[1] - vw.socket[1]);
      let a = earAng(hd.ear) * Math.PI / 180;
      if (v.name === 'B') a = a * 0.45 * e.side; else a = -a;
      hx.rotate(a); if (e.side < 0 && v.name !== 'L') hx.scale(-1, 1);
      hx.scale(e.scale || 1, e.scale || 1);
      hx.drawImage(ei, -e.pivot_in_ear[0], -e.pivot_in_ear[1]); hx.restore();
    };
    for (const e of ears) if (!e.front) drawEar(e);
    hx.restore(); collar(); hx.save(); hx.translate(cpt[0], cpt[1]); hx.rotate(rot); hx.scale(v.mir * sc, sc * sy);
    if (v.name === 'B') hx.translate(0, 0);
    hx.drawImage(im, -vw.socket[0], -vw.socket[1]);
    for (const e of ears) if (e.front) drawEar(e);
    // nose landmark, for the trace
    const nx = (vw.nose[0] - vw.socket[0]), ny = (vw.nose[1] - vw.socket[1]);
    const m = hx.getTransform(); headInfo.nose = [m.a * nx + m.c * ny + m.e, m.b * nx + m.d * ny + m.f];
    hx.restore();
  } else {
    // the empty face slot (plate view): socket, slot outline, landmarks
    hx.save(); hx.translate(cpt[0], cpt[1]); hx.rotate(v.name === 'L' ? (v.mir > 0 ? pitch : -pitch) : 0); hx.scale(v.mir * sc, sc);
    hx.setLineDash([10, 8]); hx.lineWidth = 4 / sc; hx.strokeStyle = 'rgb(120,230,255)';
    hx.beginPath(); hx.ellipse(0, -46, 48, 44, 0, 0, 7); hx.stroke();
    if (v.name !== 'B') { hx.beginPath(); hx.ellipse(-62 * (v.name === 'L' ? 1 : 0.55), -24, 44, 22, 0, 0, 7); hx.stroke(); }
    hx.setLineDash([]); hx.fillStyle = 'rgb(255,90,200)';
    hx.fillRect(-6, -6, 12, 12);
    hx.restore();
    headInfo.nose = cpt;
  }
  if (!cast) collar();
  // light the dog: dusk ambient, the door's warmth by distance
  const hs = opts.hs;
  for (const [L, cx] of [[B, bx], [Hc, hx]]) {
    cx.save(); cx.globalCompositeOperation = 'source-atop';
    cx.fillStyle = 'rgba(24,30,70,0.26)'; cx.fillRect(0, 0, W, H);
    if (hs && hs.light > 0) {
      const gx = (hs.x0 + hs.x1) / 2, gy = hs.yb - 60;
      const g = cx.createRadialGradient(gx, gy, 20, gx, gy, 520);
      g.addColorStop(0, `rgba(255,166,84,${0.22 * hs.light})`); g.addColorStop(0.5, `rgba(255,160,80,${0.09 * hs.light})`); g.addColorStop(1, 'rgba(255,170,90,0)');
      cx.fillStyle = g; cx.fillRect(0, 0, W, H);
    }
    cx.restore();
  }
  // contact shadow on the boards (no floating)
  const fs = Object.values(sk.legs).map(g => pr([g.f[0], 0, g.f[2]]));
  ctx.save(); ctx.fillStyle = 'rgba(10,8,14,0.36)';
  const sxs = fs.map(p => p[0]), sys = fs.map(p => p[1]);
  const mx = (Math.min(...sxs) + Math.max(...sxs)) / 2, my = Math.max(...sys) + 2;
  ctx.beginPath(); ctx.ellipse(mx, my, (Math.max(...sxs) - Math.min(...sxs)) / 2 + 26, 10 + 6 * fr.lie, 0, 0, 7); ctx.filter = 'blur(4px)'; ctx.fill(); ctx.filter = 'none';
  for (const p of fs) { ctx.beginPath(); ctx.ellipse(p[0], p[1] + 2, 12, 4, 0, 0, 7); ctx.fill(); }
  ctx.restore();
  // occlusion: a head that faces away sits behind the torso; otherwise in front
  const headBehind = hd.collar[2] > meanD + 0.04;
  if (headBehind) { ctx.drawImage(Hc, 0, 0); ctx.drawImage(B, 0, 0); } else { ctx.drawImage(B, 0, 0); ctx.drawImage(Hc, 0, 0); }
  // mattes for measurement (1/4 scale)
  if (opts.measure) {
    const mt = layers.mt.getContext('2d'), mh = layers.mh.getContext('2d'), md = layers.md.getContext('2d');
    mt.clearRect(0, 0, 320, 180); mh.clearRect(0, 0, 320, 180); md.clearRect(0, 0, 320, 180);
    mt.save(); mt.scale(0.25, 0.25); mt.fillStyle = '#fff';
    for (const p of sk.spine) { const q = pr(p); mt.beginPath(); mt.arc(q[0], q[1], p[3] * S, 0, 7); mt.fill(); }
    mt.restore();
    mh.drawImage(Hc, 0, 0, 320, 180); md.drawImage(B, 0, 0, 320, 180); md.drawImage(Hc, 0, 0, 320, 180);
    const st = a => { const d = a.getImageData(0, 0, 320, 180).data; let n = 0, sx = 0, sy = 0, x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1;
      for (let y = 0; y < 180; y++) for (let x = 0; x < 320; x++) { if (d[(y * 320 + x) * 4 + 3] > 100) { n++; sx += x; sy += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } }
      return n ? { n: n * 16, cx: sx / n * 4 + 2, cy: sy / n * 4 + 2, x0: x0 * 4, x1: x1 * 4 + 4, y0: y0 * 4, y1: y1 * 4 + 4 } : null; };
    return { torso: st(mt), head: st(mh), dog: st(md), headInfo, headBehind, view: headInfo.view };
  }
  return { headInfo, headBehind };
}

// ------------------------------------------------------------------ the frame
function caption(ctx, fr) {
  const v = fr.person.voice; if (v === 'none') return;
  const t = fr.t;
  let txt = '', soft = v === 'soft';
  if (v === 'call') txt = 'Come here.';
  if (v === 'soft') txt = t > 25 ? 'Come in.' : 'It’s all right.';
  ctx.save(); ctx.textAlign = 'center';
  ctx.font = soft ? 'italic 400 25px Literata' : '600 40px Literata';
  ctx.fillStyle = soft ? 'rgba(246,226,196,0.86)' : 'rgba(255,246,232,1)';
  ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 6;
  const jx = soft ? 0 : Math.sin(t * 40) * 1.2;
  ctx.fillText(txt, 520 + jx, 706);
  ctx.restore();
}

function finishFrame(ctx, i) {
  // grain: changes every other frame (12 grain fields a second), vignette
  ctx.save(); ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = 0.10;
  ctx.drawImage(layers.grain[Math.floor(i / 2) % 6], 0, 0, W, H); ctx.restore();
  const v = ctx.createRadialGradient(W / 2, H / 2, 300, W / 2, H / 2, 820);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.42)');
  ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
}

function renderScene(ctx, i, castName, opts = {}) {
  const fr = PERF.frames[i], t = fr.t;
  ctx.save(); ctx.clearRect(0, 0, W, H);
  sky(ctx, t);
  const hs = house(ctx, t, fr);
  porch(ctx, t);
  spill(ctx, hs);
  person(ctx, fr, t, hs);
  const m = drawDog(ctx, i, castName, { measure: opts.measure, hs, flat: opts.flat });
  if (!opts.nocaption) caption(ctx, fr);
  finishFrame(ctx, i);
  if (opts.plate) {
    ctx.save(); ctx.globalAlpha = 0.5; ctx.drawImage(layers.mt, 0, 0, W, H); ctx.restore();
    ctx.font = '400 30px JetBrains Mono'; ctx.fillStyle = 'rgb(120,230,255)';
    ctx.fillText(`slot view ${m.headInfo ? m.headInfo.view : ''} · head ${m.headBehind ? 'behind' : 'in front of'} torso`, 30, 120);
  }
  ctx.restore();
  return m;
}

function card(ctx, kind, u) {
  ctx.fillStyle = 'rgb(16,18,28)'; ctx.fillRect(0, 0, W, H);
  ctx.textAlign = 'center'; ctx.fillStyle = 'rgb(240,228,206)';
  const fade = Math.min(1, u * 4, (1 - u) * 4); ctx.globalAlpha = clamp(fade);
  if (kind === 'title') {
    ctx.font = '800 66px "Big Shoulders Display"'; ctx.fillText('PAE-02 · SCION 16 · JibJab', W / 2, 300);
    ctx.font = '600 34px "Big Shoulders Display"'; ctx.fillStyle = 'rgb(214,170,110)'; ctx.fillText('RECASTABLE PERFORMANCE STUDIO', W / 2, 352);
    ctx.font = 'italic 400 28px Literata'; ctx.fillStyle = 'rgb(220,214,200)'; ctx.fillText('The threshold, handmade: one performance, a face slot, any cast', W / 2, 430);
  } else {
    ctx.font = '600 30px "Big Shoulders Display"'; ctx.fillStyle = 'rgb(214,170,110)'; ctx.fillText('WHAT IT IS MADE OF', W / 2, 120);
    ctx.font = '400 21px Literata'; ctx.fillStyle = 'rgb(232,224,208)';
    const L = ['The dog is a body plate cut here, furred with the archive dog’s own coat (Amateur Film New Jersey C, public domain),',
      'moved by one performance solved from the PAELEO score, with a collar where the head meets it.',
      'Its head is a face slot. In this cut: a paper head cut here. Recast with no new performance:',
      'two strangers’ Quick, Draw! dogs (CC BY 4.0), or the home-movie dog’s own face (public domain).',
      'The door is the empty door from Straight Talk (NTIS, public domain); the person is cut paper with a Quick, Draw! face.',
      'The moon is a Quick, Draw! moon. Every voice and sound is synthesized here. No real person’s face is used.'];
    L.forEach((s, k) => ctx.fillText(s, W / 2, 190 + k * 40));
    // the three casts in the same slot, same frame
    if (card.thumbs) card.thumbs.forEach((c, k) => { ctx.drawImage(c, 160 + k * 330, 450, 300, 169); });
    ctx.font = '400 16px JetBrains Mono'; ctx.fillStyle = 'rgb(170,170,180)';
    ['paper', 'doodle', 'home movie'].forEach((s, k) => ctx.fillText(s, 310 + k * 330, 640));
  }
  ctx.globalAlpha = 1;
}

window.SCENE = { init, renderScene, card, W, H, mk, layers: () => layers };
