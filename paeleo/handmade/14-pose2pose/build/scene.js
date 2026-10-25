// The threshold, as staged for SCION 14: a front elevation of a porch at dusk, the door in the house wall, the dog on
// the boards. The camera does not move. The dog and the person are drawings from the bank, placed where the decoded
// path says; everything here is drawn with canvas paths (no images).
const W = 1280, H = 720, S = 190, X0 = 300, GY = 628, WB = 560, PY = 566;
const X = x => X0 + x * S;
const DOOR_L = X(-0.46), DOOR_R = X(0.46), DOOR_T = 168, CORNER = X(2.6), PORCH_END = X(4.9);
const TITLE_N = 72, SCENE_N = 768, END_N = 72, N = TITLE_N + SCENE_N + END_N;
let D = null;
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const mk = (w, h, o) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d', o || {})]; };
const [dc, dx] = mk(640, 360, { willReadFrequently: true }), DOX = 320, DOY = 300;           // dog layer
const [sc, sx] = mk(640, 360);                                 // dog silhouette (shadow)
const [pc, px] = mk(420, 440), POX = 210, POY = 420;           // person layer
const [gc, gx] = mk(W, H);                                     // static grain
const sm = a => { a = Math.max(0, Math.min(1, a)); return a * a * (3 - 2 * a); };
const mix = (a, b, u) => a + (b - a) * u;
const rgb = (c, k = 1) => `rgb(${c.map(v => Math.round(Math.max(0, Math.min(255, v * k)))).join(',')})`;
const lerpC = (a, b, u) => a.map((v, i) => v + (b[i] - v) * u);
let rngS = 7;
const rnd = () => (rngS = (rngS * 16807) % 2147483647) / 2147483647;

function setData(d) {
  D = d;
  // grain: fixed for the whole film (it never boils)
  rngS = 11;
  for (let k = 0; k < 26000; k++) { gx.fillStyle = rnd() < .5 ? 'rgba(255,240,220,.05)' : 'rgba(0,0,0,.07)'; gx.fillRect(rnd() * W, rnd() * H, 1 + rnd() * 1.5, 1 + rnd() * 1.5); }
  window.STONE = []; rngS = 5; for (let k = 0; k < 240; k++) STONE.push([rnd(), rnd(), rnd()]);
  window.STARS = []; rngS = 3; for (let k = 0; k < 40; k++) STARS.push([CORNER + 20 + rnd() * (W - CORNER - 20), 40 + rnd() * 300, rnd()]);
}

// ------------------------------------------------------------------ circumstances over time
function doorAngle(t) { return t < 6.2 ? 52 : 52 + 35 * sm((t - 6.2) / 0.9); }          // degrees, hinged on the right jamb
function freeEdge(t) { return DOOR_R - (DOOR_R - DOOR_L) * Math.cos(doorAngle(t) * Math.PI / 180); }
function interior(t) { return t < 6.2 ? .5 : .5 + .5 * sm((t - 6.2) / 0.7); }
function personAt(i) { return D.path.frames[i].person_x; }
function doorLight(i, t) {
  const gap = (freeEdge(t) - DOOR_L) / (DOOR_R - DOOR_L);
  const px = personAt(i); const block = px > -0.55 ? .55 : 1;
  return gap * interior(t) * block;
}
function lightAt(xs, i, t) {         // warm light from the doorway falling on the porch at screen x
  const I = doorLight(i, t), c = (DOOR_L + freeEdge(t)) / 2;
  const d = Math.abs(xs - c);
  return I * Math.max(0, 1 - Math.max(0, d - 70) / 230);
}
function dusk(t) { return t / 32; }

// ------------------------------------------------------------------ the world
function sky(t) {
  const u = dusk(t);
  const g = ctx.createLinearGradient(0, 0, 0, 548);
  g.addColorStop(0, rgb(lerpC([38, 44, 82], [14, 18, 40], u)));
  g.addColorStop(.55, rgb(lerpC([86, 74, 112], [38, 36, 70], u)));
  g.addColorStop(.86, rgb(lerpC([196, 122, 96], [92, 60, 74], u)));
  g.addColorStop(1, rgb(lerpC([228, 160, 110], [126, 80, 74], u)));
  ctx.fillStyle = g; ctx.fillRect(CORNER, 0, W - CORNER, 560);
  for (const [sx_, sy_, b] of STARS) { const a = Math.max(0, (u - .25 - b * .5)) * 1.4; if (a > 0) { ctx.fillStyle = `rgba(255,245,225,${Math.min(.8, a)})`; ctx.fillRect(sx_, sy_, 1.6, 1.6); } }
  // a thin moon
  ctx.save(); ctx.translate(1118, 112); ctx.fillStyle = `rgba(250,236,200,${.55 + .35 * u})`;
  ctx.beginPath(); ctx.arc(0, 0, 17, 0, Math.PI * 2); ctx.fill();
  ctx.globalCompositeOperation = 'destination-out'; ctx.beginPath(); ctx.arc(7, -4, 16, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  // far trees and the yard, low enough to leave the dog against the sky
  ctx.fillStyle = rgb(lerpC([46, 42, 66], [22, 22, 38], u));
  ctx.beginPath(); ctx.moveTo(CORNER, 548);
  for (let x = CORNER; x <= W; x += 6) ctx.lineTo(x, 532 - 9 * Math.abs(Math.sin(x * .021)) - 7 * Math.abs(Math.sin(x * .057 + 1)) - (x > 1150 ? 30 * Math.exp(-((x - 1205) ** 2) / 900) : 0));
  ctx.lineTo(W, 560); ctx.lineTo(CORNER, 560); ctx.fill();
  ctx.fillStyle = rgb(lerpC([40, 38, 46], [20, 20, 28], u)); ctx.fillRect(CORNER, 546, W - CORNER, 14);
}

function wall(i, t) {
  const u = dusk(t);
  ctx.fillStyle = rgb(lerpC([74, 80, 100], [44, 48, 64], u)); ctx.fillRect(0, 30, CORNER, WB - 30);
  ctx.strokeStyle = rgb(lerpC([58, 62, 80], [34, 37, 50], u)); ctx.lineWidth = 2;
  for (let y = 46; y < WB; y += 15) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(CORNER, y); ctx.stroke(); }
  // warm wash on the wall around the door, from the room
  const I = doorLight(i, t) + .12 * interior(t);
  const g = ctx.createRadialGradient(X(0), 470, 20, X(0), 470, 420);
  g.addColorStop(0, `rgba(255,176,96,${.32 * I})`); g.addColorStop(1, 'rgba(255,176,96,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 30, CORNER, WB - 30);
  // window, dimly lit
  const wl = .35 + .25 * interior(t);
  ctx.fillStyle = rgb([150, 100, 58], wl); ctx.fillRect(522, 252, 148, 166);
  ctx.fillStyle = rgb([230, 196, 140], wl * .6);
  ctx.beginPath(); ctx.moveTo(522, 252); ctx.quadraticCurveTo(560, 330, 540, 418); ctx.lineTo(522, 418); ctx.fill();
  ctx.beginPath(); ctx.moveTo(670, 252); ctx.quadraticCurveTo(632, 330, 652, 418); ctx.lineTo(670, 418); ctx.fill();
  ctx.strokeStyle = '#1a130e'; ctx.lineWidth = 2.2; ctx.strokeRect(522, 252, 148, 166);
  ctx.fillStyle = rgb([120, 124, 136], 1 - .4 * u);
  ctx.fillRect(514, 244, 164, 8); ctx.fillRect(510, 418, 172, 10); ctx.fillRect(594, 252, 5, 166); ctx.fillRect(522, 333, 148, 5);
  ctx.strokeRect(514, 244, 164, 8); ctx.strokeRect(510, 418, 172, 10);
  // corner board
  ctx.fillStyle = rgb([110, 114, 128], 1 - .4 * u); ctx.fillRect(CORNER - 10, 30, 12, WB - 30); ctx.strokeRect(CORNER - 10, 30, 12, WB - 30);
}

function room(i, t) {
  const L = interior(t);
  ctx.save(); ctx.beginPath(); ctx.rect(DOOR_L, DOOR_T, DOOR_R - DOOR_L, WB - DOOR_T); ctx.clip();
  const g = ctx.createRadialGradient(DOOR_L + 30, 400, 10, DOOR_L + 40, 400, 260);
  g.addColorStop(0, rgb([255, 214, 150], L)); g.addColorStop(.5, rgb([214, 150, 84], L)); g.addColorStop(1, rgb([150, 96, 54], L));
  ctx.fillStyle = g; ctx.fillRect(DOOR_L, DOOR_T, DOOR_R - DOOR_L, WB - DOOR_T);
  // far floor, a rug, a picture, a lamp on a table
  ctx.fillStyle = rgb([128, 82, 48], L); ctx.beginPath(); ctx.moveTo(DOOR_L, 506); ctx.lineTo(DOOR_R, 500); ctx.lineTo(DOOR_R, WB); ctx.lineTo(DOOR_L, WB); ctx.fill();
  ctx.strokeStyle = rgb([100, 62, 36], L); ctx.lineWidth = 1.5;
  for (const y of [516, 530, 546]) { ctx.beginPath(); ctx.moveTo(DOOR_L, y); ctx.lineTo(DOOR_R, y - 3); ctx.stroke(); }
  ctx.fillStyle = rgb([150, 60, 46], L); ctx.beginPath(); ctx.ellipse(X(0.05), 534, 70, 14, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = rgb([96, 60, 36], L); ctx.fillRect(X(0.05) - 22, 300, 44, 54);
  ctx.fillStyle = rgb([200, 170, 120], L); ctx.fillRect(X(0.05) - 16, 306, 32, 42);
  ctx.fillStyle = rgb([84, 52, 30], L); ctx.fillRect(DOOR_L + 10, 446, 46, 6); ctx.fillRect(DOOR_L + 14, 452, 5, 56); ctx.fillRect(DOOR_L + 48, 452, 5, 56);
  ctx.fillStyle = rgb([255, 236, 190], L); ctx.beginPath(); ctx.moveTo(DOOR_L + 22, 412); ctx.lineTo(DOOR_L + 44, 412); ctx.lineTo(DOOR_L + 50, 434); ctx.lineTo(DOOR_L + 16, 434); ctx.fill();
  ctx.fillStyle = rgb([90, 60, 40], L); ctx.fillRect(DOOR_L + 31, 434, 4, 12);
  const lg = ctx.createRadialGradient(DOOR_L + 33, 424, 4, DOOR_L + 33, 424, 120);
  lg.addColorStop(0, `rgba(255,240,200,${.55 * L})`); lg.addColorStop(1, 'rgba(255,240,200,0)'); ctx.fillStyle = lg; ctx.fillRect(DOOR_L, DOOR_T, DOOR_R - DOOR_L, WB - DOOR_T);
  // the door: hinged on the right jamb, swung into the room
  const a = doorAngle(t) * Math.PI / 180, xf = freeEdge(t), dl = 16 * Math.sin(a);
  const shade = .62 - .32 * Math.sin(a);
  ctx.fillStyle = rgb([214, 204, 182], shade * (.6 + .4 * L)); ctx.strokeStyle = '#1a130e'; ctx.lineWidth = 2.2;
  ctx.beginPath(); ctx.moveTo(DOOR_R, DOOR_T); ctx.lineTo(xf, DOOR_T + dl); ctx.lineTo(xf, WB - dl * .5); ctx.lineTo(DOOR_R, WB); ctx.closePath(); ctx.fill(); ctx.stroke();
  const P = (u, v) => [mix(DOOR_R, xf, u), mix(mix(DOOR_T, DOOR_T + dl, u), mix(WB, WB - dl * .5, u), v)];
  ctx.lineWidth = 1.4; ctx.strokeStyle = 'rgba(26,19,14,.7)';
  for (const [v0, v1] of [[.08, .46], [.54, .92]]) { ctx.beginPath(); const q = [P(.18, v0), P(.82, v0), P(.82, v1), P(.18, v1)]; ctx.moveTo(...q[0]); for (const r of q.slice(1)) ctx.lineTo(...r); ctx.closePath(); ctx.stroke(); }
  ctx.fillStyle = '#c8a050'; const kn = P(.88, .52); ctx.beginPath(); ctx.arc(kn[0], kn[1], 3, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
  // frame and trim
  const u = dusk(t);
  ctx.fillStyle = rgb([170, 164, 150], (1 - .35 * u) * (.75 + .25 * doorLight(i, t)));
  ctx.strokeStyle = '#1a130e'; ctx.lineWidth = 2.2;
  ctx.fillRect(DOOR_L - 14, DOOR_T - 16, 14, WB - DOOR_T + 16); ctx.strokeRect(DOOR_L - 14, DOOR_T - 16, 14, WB - DOOR_T + 16);
  ctx.fillRect(DOOR_R, DOOR_T - 16, 14, WB - DOOR_T + 16); ctx.strokeRect(DOOR_R, DOOR_T - 16, 14, WB - DOOR_T + 16);
  ctx.fillRect(DOOR_L - 22, DOOR_T - 28, DOOR_R - DOOR_L + 44, 14); ctx.strokeRect(DOOR_L - 22, DOOR_T - 28, DOOR_R - DOOR_L + 44, 14);
}

function roofAndPost(t) {
  const u = dusk(t);
  ctx.fillStyle = rgb([38, 40, 52], 1 - .3 * u); ctx.fillRect(0, 0, W, 30);
  ctx.fillStyle = rgb([92, 96, 110], 1 - .4 * u); ctx.fillRect(0, 26, W, 8);
  ctx.strokeStyle = '#1a130e'; ctx.lineWidth = 2; ctx.strokeRect(-2, 26, W + 4, 8);
  ctx.fillStyle = rgb([84, 88, 102], 1 - .4 * u); ctx.fillRect(1226, 34, 18, 660); ctx.strokeRect(1226, 34, 18, 660);
}

function floor(i, t) {
  const u = dusk(t);
  ctx.fillStyle = rgb(lerpC([86, 72, 62], [52, 44, 40], u)); ctx.fillRect(0, WB, PORCH_END, 130);
  ctx.strokeStyle = rgb(lerpC([62, 52, 46], [36, 30, 28], u)); ctx.lineWidth = 1.6;
  for (const y of [568, 577, 587, 598, 610, 623, 637, 652, 668, 685]) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(PORCH_END, y); ctx.stroke(); }
  for (let k = 0; k < 60; k++) { const y = [568, 577, 587, 598, 610, 623, 637, 652, 668][k % 9]; const x = (k * 197.3) % PORCH_END; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + 8 + (k % 9)); ctx.stroke(); }
  // the sill: a flat threshold stone in front of the door
  ctx.fillStyle = rgb(lerpC([98, 94, 90], [66, 63, 60], u));
  ctx.beginPath(); ctx.moveTo(X(-0.55), WB); ctx.lineTo(X(0.55), WB); ctx.lineTo(X(0.6), 648); ctx.lineTo(X(-0.6), 648); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#1a130e'; ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = rgb(lerpC([84, 78, 72], [52, 50, 48], u)); ctx.fillRect(X(-0.6), 648, X(0.6) - X(-0.6), 7); ctx.strokeRect(X(-0.6), 648, X(0.6) - X(-0.6), 7);
  for (const [a, b, c] of STONE) { ctx.fillStyle = c < .5 ? 'rgba(0,0,0,.12)' : 'rgba(255,255,255,.06)'; ctx.fillRect(X(-0.55) + a * (X(0.55) - X(-0.55)), WB + 4 + b * 82, 2, 2); }
  // the yard beyond the end of the porch
  ctx.fillStyle = rgb(lerpC([34, 34, 40], [18, 18, 24], u)); ctx.fillRect(PORCH_END, 546, W - PORCH_END, 174);
  // front edge and skirt, steps at the end of the porch
  ctx.fillStyle = rgb(lerpC([110, 96, 82], [62, 54, 48], u)); ctx.fillRect(0, 690, PORCH_END, 9);
  ctx.strokeStyle = '#1a130e'; ctx.strokeRect(-2, 690, PORCH_END + 2, 9);
  ctx.fillStyle = '#1b1714'; ctx.fillRect(0, 699, PORCH_END, 21);
  ctx.strokeStyle = 'rgba(80,70,60,.5)'; ctx.lineWidth = 1.5;
  for (let x = -20; x < PORCH_END; x += 18) { ctx.beginPath(); ctx.moveTo(x, 699); ctx.lineTo(x + 21, 720); ctx.moveTo(x + 21, 699); ctx.lineTo(x, 720); ctx.stroke(); }
  ctx.fillStyle = rgb(lerpC([90, 78, 66], [54, 46, 42], u));
  ctx.fillRect(PORCH_END, 690, W - PORCH_END, 9); ctx.fillRect(PORCH_END + 10, 704, W - PORCH_END, 8); ctx.fillRect(PORCH_END + 22, 716, W - PORCH_END, 6);
  ctx.strokeStyle = '#1a130e'; ctx.lineWidth = 1.6; ctx.strokeRect(PORCH_END, 690, W, 9); ctx.strokeRect(PORCH_END + 10, 704, W, 8);
  // bench beside the door
  ctx.fillStyle = rgb([70, 54, 44], 1 - .35 * u);
  const b0 = X(-1.64), b1 = X(-0.86);
  ctx.fillRect(b0, 478, b1 - b0, 9); ctx.fillRect(b0 + 8, 487, 7, 79); ctx.fillRect(b1 - 15, 487, 7, 79);
  ctx.strokeStyle = '#1a130e'; ctx.lineWidth = 2; ctx.strokeRect(b0, 478, b1 - b0, 9);
}

function spill(i, t) {
  const I = doorLight(i, t); if (I <= 0.01) return;
  const xr = freeEdge(t);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const g = ctx.createLinearGradient(0, WB, 0, 700);
  g.addColorStop(0, `rgba(255,170,90,${.34 * I})`); g.addColorStop(.5, `rgba(255,150,80,${.16 * I})`); g.addColorStop(1, 'rgba(255,150,80,0)');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(DOOR_L, WB); ctx.lineTo(xr, WB); ctx.lineTo(xr + 150, 700); ctx.lineTo(DOOR_L - 70, 700); ctx.closePath(); ctx.fill();
  ctx.restore();
}

// ------------------------------------------------------------------ figures
function lightLayer(c, x, ox, i, t, base) {
  // dusk on the figure, then the door's warm light where it falls
  x.save(); x.globalCompositeOperation = 'source-atop';
  x.fillStyle = `rgba(16,22,44,${base + .08 * dusk(t)})`; x.fillRect(0, 0, c.width, c.height);
  const g = x.createLinearGradient(0, 0, c.width, 0);
  for (let k = 0; k <= 8; k++) { const sx_ = ox - (c.width / 2) + k * c.width / 8; g.addColorStop(k / 8, `rgba(255,172,96,${.27 * lightAt(sx_, i, t)})`); }
  x.fillStyle = g; x.fillRect(0, 0, c.width, c.height);
  x.restore();
}

function person(i, t) {
  const r = D.path.frames[i], d = D.bank.drawings[r.person];
  px.clearRect(0, 0, pc.width, pc.height); px.save(); px.translate(POX, POY); drawDrawing(px, d.parts); px.restore();
  const xs = X(r.person_x);
  lightLayer(pc, px, xs, i, t, .18);
  ctx.drawImage(pc, xs - POX, PY - POY);
}

function measureDog() {
  const im = dx.getImageData(0, 0, dc.width, dc.height).data;
  let n = 0, sxv = 0, syv = 0, x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1;
  for (let y = 0; y < dc.height; y += 2) for (let x = 0; x < dc.width; x += 2) {
    if (im[(y * dc.width + x) * 4 + 3] > 60) { n++; sxv += x; syv += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  return { n, cx: sxv / n, cy: syv / n, x0, x1, y0, y1 };
}

function dog(i, t) {
  const r = D.path.frames[i], d = D.bank.drawings[r.dog];
  dx.clearRect(0, 0, dc.width, dc.height); dx.save(); dx.translate(DOX, DOY); drawDrawing(dx, d.parts); dx.restore();
  const m = measureDog();
  const xs = X(r.x_place);
  // contact shadow on the boards
  ctx.save(); ctx.fillStyle = 'rgba(8,8,14,.38)'; ctx.beginPath();
  ctx.ellipse(xs + (m.x0 + m.x1) / 2 - DOX, GY + 2, (m.x1 - m.x0) / 2 * .92, 6.5, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  // cast shadow, thrown toward us by the doorway light
  const L = lightAt(xs, i, t);
  if (L > .03) {
    sx.clearRect(0, 0, sc.width, sc.height); sx.drawImage(dc, 0, 0); sx.globalCompositeOperation = 'source-in'; sx.fillStyle = '#05040a'; sx.fillRect(0, 0, sc.width, sc.height); sx.globalCompositeOperation = 'source-over';
    const k = Math.max(-.9, Math.min(.9, (xs - (DOOR_L + freeEdge(t)) / 2) / 160));
    ctx.save(); ctx.beginPath(); ctx.rect(0, GY - 2, PORCH_END, 690 - GY + 2); ctx.clip();
    ctx.globalAlpha = Math.min(.34, .5 * L); ctx.filter = 'blur(2.5px)';
    ctx.setTransform(1, 0, -k * .6, -.26, xs - DOX + k * .6 * DOY, GY + .26 * DOY);
    ctx.drawImage(sc, 0, 0); ctx.restore();
  }
  lightLayer(dc, dx, xs, i, t, .1);
  ctx.drawImage(dc, xs - DOX, GY - DOY);
  const nose = d.meta.nose ? [xs + d.meta.nose[0], GY + d.meta.nose[1]] : null;
  return { cx: xs - DOX + m.cx, cy: GY - DOY + m.cy, x0: xs - DOX + m.x0, x1: xs - DOX + m.x1, y0: GY - DOY + m.y0, y1: GY - DOY + m.y1, area: m.n * 4, nose };
}

// ------------------------------------------------------------------ words
function words(t) {
  for (const [a, b, txt, kind] of D.lines) {
    if (t < a || t > b + .35) continue;
    const f = Math.min(1, (t - a) / .12, (b + .35 - t) / .25);
    ctx.save(); ctx.globalAlpha = f; ctx.textAlign = 'center';
    ctx.font = kind === 'call' ? '600 34px Literata' : 'italic 400 25px Literata';
    ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillText(txt, W / 2 + 2, 674 + 2);
    ctx.fillStyle = kind === 'call' ? '#f3e6cf' : 'rgba(236,222,196,.8)'; ctx.fillText(txt, W / 2, 674);
    ctx.restore();
  }
}

function scene(i) {
  const t = i / 24;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  sky(t); wall(i, t); floor(i, t);
  // dusk deepens over the exterior
  ctx.fillStyle = `rgba(8,10,24,${.12 + .22 * dusk(t)})`; ctx.fillRect(0, 0, W, H);
  room(i, t); spill(i, t);
  person(i, t);
  const m = dog(i, t);
  roofAndPost(t);
  const vg = ctx.createRadialGradient(W / 2, H * .55, 300, W / 2, H * .55, 820);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,.5)'); ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  ctx.drawImage(gc, 0, 0);
  words(t);
  return m;
}

// ------------------------------------------------------------------ cards
function strip(y, h, ids, x0, x1, sc_) {
  const n = ids.length, w = (x1 - x0) / n;
  ids.forEach((id, k) => {
    const d = D.bank.drawings[id]; if (!d) return;
    ctx.save(); ctx.translate(x0 + w * (k + .5), y + h); ctx.scale(sc_, sc_); drawDrawing(ctx, d.parts); ctx.restore();
  });
}
function card(kind, k) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#16130f'; ctx.fillRect(0, 0, W, H);
  const fade = Math.min(1, k / 10, (END_N - 1 - k) / 10);
  ctx.globalAlpha = Math.max(0, fade);
  ctx.textAlign = 'left';
  if (kind === 'title') {
    ctx.fillStyle = '#e9dcc2'; ctx.font = '800 54px "Big Shoulders Display"'; ctx.fillText('PAE-02 · SCION 14 · Nora Willett — Pose2Pose Casting', 90, 250);
    ctx.font = 'italic 400 30px Literata'; ctx.fillStyle = '#cdbb9a'; ctx.fillText('The threshold, handmade: drawing to drawing, chosen frame by frame.', 92, 304);
    ctx.font = '400 15px "JetBrains Mono"'; ctx.fillStyle = '#8f8270'; ctx.fillText('A lineage of method, not an endorsement.', 94, 342);
    strip(410, 150, D.titleStrip, 90, 1190, .62);
    ctx.font = '400 14px "JetBrains Mono"'; ctx.fillStyle = '#8f8270'; ctx.fillText('drawings from the illustration bank', 94, 600);
  } else {
    ctx.fillStyle = '#e9dcc2'; ctx.font = '800 40px "Big Shoulders Display"'; ctx.fillText('What it is made of', 90, 96);
    ctx.font = '400 21px Literata'; ctx.fillStyle = '#d8c9ad';
    D.endText.forEach((ln, j) => ctx.fillText(ln, 90, 146 + j * 32));
    // the decoded path, revealed: which drawing was on screen when
    const y0 = 470, x0 = 90, x1 = 1190, fr = D.path.frames, n = fr.length;
    ctx.font = '400 13px "JetBrains Mono"'; ctx.fillStyle = '#9a8c76'; ctx.fillText('the selected path: one drawing per frame, 0 to 32 s', x0, y0 - 116);
    const col = { stand: '#b08d62', walk: '#d1b07e', back: '#8b5d45', turn: '#c9774f', lie: '#7c8aa0', lieR: '#5c6680', look: '#e0c060' };
    for (let j = 0; j < n; j++) { const g = D.bank.drawings[fr[j].dog].meta.group; ctx.fillStyle = col[g] || '#888'; ctx.fillRect(x0 + (x1 - x0) * j / n, y0 + 70, (x1 - x0) / n + .6, 16); }
    let prev = null; let lastX = -1e9;
    for (let j = 0; j < n; j++) { if (fr[j].dog !== prev) { const xx = x0 + (x1 - x0) * j / n; ctx.fillStyle = '#16130f'; ctx.fillRect(xx, y0 + 70, 1, 16); prev = fr[j].dog; } }
    const K = D.endKeys.length;
    D.endKeys.forEach((j, q) => {
      const xx = x0 + (x1 - x0) * j / n, tx = x0 + 40 + (x1 - x0 - 80) * q / (K - 1), d = D.bank.drawings[fr[j].dog];
      ctx.strokeStyle = 'rgba(200,180,150,.35)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(tx, y0 + 20); ctx.lineTo(xx, y0 + 68); ctx.stroke();
      ctx.save(); ctx.translate(tx, y0 + 12); ctx.scale(.36, .36); drawDrawing(ctx, d.parts); ctx.restore();
      ctx.fillStyle = '#9a8c76'; ctx.fillText((j / 24).toFixed(2) + 's', tx - 16, y0 - 52);
    });
  }
  ctx.globalAlpha = 1;
}

function frame(n, q) {
  let meas = null;
  if (n < TITLE_N) card('title', n);
  else if (n < TITLE_N + SCENE_N) meas = scene(n - TITLE_N);
  else card('end', n - TITLE_N - SCENE_N);
  return { img: cv.toDataURL('image/jpeg', q || .92), meas };
}
window.ready = document.fonts.ready;
