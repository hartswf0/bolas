// SCION 13 · Secondary Motion — drawing. Projects the solved rig (scene.js) with an orthographic diorama camera
// (yaw −16°, pitch 12°) onto a 1280×720 canvas as torn tissue and crepe paper, and measures the dog from a mask pass
// of the same drawn geometry. Exposes window.init(score, preset), window.frame(i, draw, label) and window.card(kind).
'use strict';
const W = 1280, H = 720, cv = document.getElementById('c'), g = cv.getContext('2d');
const MW = 320, MH = 180, MS = MW / W;
const masks = ['torso', 'head', 'limb', 'm_snout', 'm_skull'].map(() => { const c = document.createElement('canvas'); c.width = MW; c.height = MH; return { c, x: c.getContext('2d', { willReadFrequently: true }) }; });
const U = SCENE.util, { clamp, lerp, ss, add, sub, mul, dot, len, norm, lerp3, rng } = U;
const PL = SCENE.PLACE;
const PSI = 0.28, PHI = 0.21, cP = Math.cos(PSI), sP = Math.sin(PSI), cF = Math.cos(PHI), sF = Math.sin(PHI);
let CAM = { cx: 2, cy: 0.9, s: 195 };
function camAt(t) {
  const a = ss(t, 4.6, 6.4), b = ss(t, 14.8, 24.2);
  const c1 = { cx: lerp(2.15, 1.72, a), cy: lerp(0.95, 0.98, a), s: lerp(208, 186, a) };
  return { cx: lerp(c1.cx, 0.22, b), cy: lerp(c1.cy, 0.84, b), s: lerp(c1.s, 340, b) };
}
function P3(p) { // world -> [u, v, depth]
  const xr = p[0] * cP - p[2] * sP, zr = p[0] * sP + p[2] * cP, yr = p[1] * cF - zr * sF, d = zr * cF + p[1] * sF;
  return [W / 2 + (xr - CAM.cx) * CAM.s, H / 2 - (yr - CAM.cy) * CAM.s, d];
}
const depth = p => (p[0] * sP + p[2] * cP) * cF + p[1] * sF;
const VIEW = [sP * cF, sF, cP * cF];           // direction toward the camera (for eye visibility)
function unprojectZ0(u, v) { // screen -> world assuming Z = 0 (the dog's path)
  const xr = (u - W / 2) / CAM.s + CAM.cx, X = xr / cP, zr = X * sP, yr = CAM.cy - (v - H / 2) / CAM.s; return [X, (yr + zr * sF) / cF];
}

// ---------- palette (tissue and crepe paper) ----------
const COL = {
  oat: [216, 196, 152], ochre: [196, 145, 63], rust: [156, 85, 48], cream: [239, 226, 196], char: [78, 60, 52],
  madder: [176, 58, 46], saffron: [214, 160, 58], rose: [200, 112, 104], reedA: [120, 112, 70], reedB: [150, 128, 78],
  hair: [48, 34, 30], scarf: [214, 168, 46], coat: [52, 86, 92], skin: [158, 104, 74], trouser: [44, 44, 58],
};
let LIGHT = { open: 0, z1: 0.3 };
function warmAt(p) { // warm lamp light reaching a point: room glow indoors, a wedge through the doorway on the porch
  if (p[0] < PL.wallIn) return 0.85;
  const Lx = PL.lamp[0], Lz = PL.lamp[2], f = (p[0] - Lx) / (-Lx);
  const zlo = Lz + (LIGHT.z1 - Lz) * f, zhi = Lz + (0.46 - Lz) * f, soft = 0.12 * f;
  const inW = ss(p[2], zlo - soft, zlo + soft) * (1 - ss(p[2], zhi - soft, zhi + soft));
  const fall = Math.exp(-Math.max(0, p[0]) / 2.0) * (p[1] < 2.0 ? 1 : 0.4);
  return LIGHT.amt * inW * fall;
}
function shade(rgb, w, dark = 1, a = 1) {
  const amb = [0.68, 0.71, 0.88], wm = [0.85, 0.66, 0.42];
  const r = rgb[0] * (amb[0] + w * wm[0]) * dark, gg = rgb[1] * (amb[1] + w * wm[1]) * dark, b = rgb[2] * (amb[2] + w * wm[2]) * dark;
  return `rgba(${clamp(r, 0, 255) | 0},${clamp(gg, 0, 255) | 0},${clamp(b, 0, 255) | 0},${a})`;
}

// ---------- torn paper helpers ----------
function tornPoly3(pts, seed, amp = 0.012, step = 0.06) { // subdivide a world polygon's edges, jitter in its plane (fixed)
  const R = rng(seed), out = [];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length], d = sub(b, a), L = len(d), n = Math.max(1, Math.round(L / step));
    for (let k = 0; k < n; k++) { const q = lerp3(a, b, k / n), j = (R() - 0.5) * 2 * amp; out.push(k === 0 ? q : [q[0] + j * (R() - 0.5), q[1] + j, q[2] + j * (R() - 0.5)]); }
  }
  return out;
}
function fillPoly(ctx, pts3, style) { ctx.beginPath(); pts3.forEach((p, i) => { const q = P3(p); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }); ctx.closePath(); ctx.fillStyle = style; ctx.fill(); }
function ribbon(ctx, pts3, w0, w1, seed, fill, crease, tornTip = true) {
  const P = pts3.map(P3), n = P.length, Ls = [], Rs = [], R = rng(seed);
  for (let k = 0; k < n; k++) {
    const a = P[Math.max(0, k - 1)], b = P[Math.min(n - 1, k + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1]; const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;
    const w = lerp(w0, w1, k / (n - 1)) * CAM.s * 0.5 * (1 + 0.18 * (R() - 0.5));
    Ls.push([P[k][0] - dy * w, P[k][1] + dx * w]); Rs.push([P[k][0] + dy * w, P[k][1] - dx * w]);
  }
  ctx.beginPath(); ctx.moveTo(Ls[0][0], Ls[0][1]);
  for (let k = 1; k < n; k++) ctx.lineTo(Ls[k][0], Ls[k][1]);
  const e = P[n - 1], prev = P[n - 2] || P[0]; let tx = e[0] - prev[0], ty = e[1] - prev[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
  if (tornTip) { const lw = Math.max(1.5, w1 * CAM.s * 0.5); for (let j = 1; j <= 3; j++) { const q = lerp(Ls[n - 1][0], Rs[n - 1][0], j / 4), r = lerp(Ls[n - 1][1], Rs[n - 1][1], j / 4), ex = (j % 2 ? 1.3 : 0.4) * lw * (0.6 + R()); ctx.lineTo(q + tx * ex, r + ty * ex); } }
  for (let k = n - 1; k >= 0; k--) ctx.lineTo(Rs[k][0], Rs[k][1]);
  ctx.closePath(); ctx.fillStyle = fill; ctx.fill();
  if (crease) { ctx.beginPath(); P.forEach((p, k) => k ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.strokeStyle = crease; ctx.lineWidth = Math.max(0.6, CAM.s * 0.0035); ctx.stroke(); }
  return P;
}
const BLOBN = 18, BLOBJ = {};
function blob(ctx, c3, r, seed, fill, sq = 1) { // a torn tissue disc (spheres project to discs)
  const q = P3(c3), R = BLOBJ[seed] || (BLOBJ[seed] = (() => { const rr = rng(seed); return Array.from({ length: BLOBN }, () => 0.9 + 0.16 * rr()); })());
  ctx.beginPath(); for (let k = 0; k < BLOBN; k++) { const a = k / BLOBN * Math.PI * 2, rr = r * CAM.s * R[k]; const x = q[0] + Math.cos(a) * rr, y = q[1] + Math.sin(a) * rr * sq; k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
  ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); return q;
}

// ---------- static set: built once in world coordinates ----------
let SET = null;
function buildSet() {
  const S = []; let sd = 11;
  const flat = pts => pts.map(p => { const zr = p[0] * sP + p[2] * cP; return [p[0], p[1] + zr * sF / cF, p[2]]; }); // far flats: keep their height on screen
  const add_ = (pts, col, opt = {}) => { if (opt.fixed) pts = flat(pts); S.push({ pts: opt.clean ? pts : tornPoly3(pts, sd++, opt.amp || 0.02, opt.step || 0.12), col, ...opt }); };
  // sky: torn tissue bands, far behind
  const bands = [[-9, 12, [22, 24, 50]], [-1.2, 4.2, [36, 34, 70]], [-1.2, 3.1, [60, 46, 88]], [-1.2, 2.3, [96, 62, 100]], [-1.2, 1.6, [140, 84, 96]], [-1.2, 1.05, [186, 112, 92]]];
  bands.forEach(([y0, y1, c], k) => add_([[-12, y0, -14], [16, y0, -14], [16, y1 + (k ? 0.25 * Math.sin(k) : 0), -14], [-12, y1, -14]], c, { kind: 'sky', amp: k ? 0.12 : 0, step: 0.5, fixed: 1 }));
  // distant hills and a tree line of torn tissue
  add_([[-12, -0.6, -11], [16, -0.6, -11], [16, 0.9, -11], [11, 1.3, -11], [8, 0.8, -11], [5.5, 1.5, -11], [3, 1.0, -11], [0, 1.4, -11], [-4, 0.9, -11], [-12, 1.2, -11]], [42, 48, 72], { kind: 'far', amp: 0.08, step: 0.3, fixed: 1 });
  add_([[-12, -0.6, -9], [16, -0.6, -9], [16, 0.5, -9], [12, 0.8, -9], [9.5, 0.4, -9], [7, 1.0, -9], [6.2, 0.6, -9], [4, 0.75, -9], [1, 0.3, -9], [-12, 0.5, -9]], [30, 38, 56], { kind: 'far', amp: 0.1, step: 0.25, fixed: 1 });
  // yard ground
  add_([[-6, PL.yardY, -9], [16, PL.yardY, -9], [16, PL.yardY, 4], [-6, PL.yardY, 4]], [36, 44, 44], { kind: 'ground', step: 0.8 });
  SET = { back: S.splice(0), porch: [], room: [], front: [] };
  // porch floor, boards, fascia, steps, rail
  const pz0 = PL.porchZ[0], pz1 = PL.porchZ[1], pe = PL.porchEnd;
  add_([[0, 0, pz0], [pe, 0, pz0], [pe, 0, pz1], [0, 0, pz1]], [92, 92, 112], { amp: 0.01 });
  add_([[0, 0, pz1], [pe, 0, pz1], [pe, PL.yardY, pz1], [0, PL.yardY, pz1]], [50, 50, 66], { amp: 0.012 });
  for (let k = 0; k < 3; k++) { const x0 = pe + k * 0.2, y = -0.15 * (k + 1); add_([[x0, y + 0.15, pz0 + 0.3], [x0, y, pz0 + 0.3], [x0, y, pz1], [x0, y + 0.15, pz1]], [62, 60, 76], { amp: 0.006 }); add_([[x0, y, pz0 + 0.3], [x0 + 0.2, y, pz0 + 0.3], [x0 + 0.2, y, pz1], [x0, y, pz1]], [86, 84, 104], { amp: 0.006 }); }
  SET.porch = S.splice(0);
  SET.boards = []; for (let z = pz0 + 0.14; z < pz1; z += 0.14) SET.boards.push([[0.02, 0.001, z], [pe - 0.02, 0.001, z]]);
  SET.rail = { z: pz0 + 0.03, x0: 0.05, x1: pe - 0.1 };
  // the house in section: room floor, back wall, wall face with the doorway, ceiling and roof, cut edges
  const wi = PL.wallIn, wo = PL.wallOut, cz = PL.cutZ, bz = PL.roomBackZ, lx = PL.roomLeftX, dz0 = PL.doorZ[0], dz1 = PL.doorZ[1], dh = PL.doorH, top = 2.62;
  add_([[lx, 0, bz], [wi, 0, bz], [wi, 0, cz], [lx, 0, cz]], [128, 82, 56], { kind: 'roomfloor', amp: 0.008 });
  add_([[lx, 0, bz], [wi, 0, bz], [wi, top, bz], [lx, top, bz]], [190, 128, 76], { kind: 'roomwall', amp: 0.008 });
  add_([[-2.7, 0.002, -1.6], [-0.45, 0.002, -1.6], [-0.45, 0.002, 0.42], [-2.7, 0.002, 0.42]], [150, 52, 42], { kind: 'rug', amp: 0.03, step: 0.08 });
  add_([[-2.3, 1.15, bz + 0.01], [-1.5, 1.15, bz + 0.01], [-1.5, 1.75, bz + 0.01], [-2.3, 1.75, bz + 0.01]], [96, 70, 54], { kind: 'pic', amp: 0.004 });
  add_([[-2.22, 1.22, bz + 0.02], [-1.58, 1.22, bz + 0.02], [-1.58, 1.68, bz + 0.02], [-2.22, 1.68, bz + 0.02]], [120, 140, 128], { kind: 'pic', amp: 0.01 });
  SET.room = S.splice(0);
  // the outside face of the wall (X = wo, dusk siding) around the doorway, and the far jamb's thickness
  add_([[wo, 0, bz], [wo, 0, dz0], [wo, dh, dz0], [wo, dh, dz1], [wo, top, dz1], [wo, top, bz]], [64, 72, 100], { kind: 'outside', amp: 0.006 });
  add_([[wi, 0, dz0], [wo, 0, dz0], [wo, dh, dz0], [wi, dh, dz0]], [150, 120, 90], { kind: 'jamb', amp: 0.003 });
  add_([[wi, dh, dz0], [wo, dh, dz0], [wo, dh, dz1], [wi, dh, dz1]], [120, 96, 74], { kind: 'jamb', amp: 0.003 });
  SET.wall = S.splice(0);
  SET.clap = []; for (let y = 0.18; y < top; y += 0.18) SET.clap.push(y);
  // sill (threshold board) across the doorway
  add_([[wi - 0.02, 0.026, dz0], [wo + 0.03, 0.026, dz0], [wo + 0.03, 0.026, dz1 + 0.1], [wi - 0.02, 0.026, dz1 + 0.1]], [170, 140, 100], { kind: 'sill', amp: 0.004 });
  add_([[wi - 0.02, 0.0, dz1 + 0.1], [wo + 0.03, 0.0, dz1 + 0.1], [wo + 0.03, 0.026, dz1 + 0.1], [wi - 0.02, 0.026, dz1 + 0.1]], [120, 96, 70], { kind: 'sill', amp: 0.002 });
  SET.sill = S.splice(0);
  // the cut (near jamb and wall section, card), the ceiling/roof section above
  add_([[wi, dh, cz], [wo, dh, cz], [wo, top, cz], [wi, top, cz]], [226, 214, 190], { kind: 'cut', amp: 0.004, step: 0.1 });
  add_([[lx - 0.1, top, cz], [wo + 0.7, top, cz], [wo + 0.7, top + 0.1, cz], [(lx + wo) / 2, top + 1.3, cz], [lx - 0.1, top + 0.1, cz]], [58, 46, 52], { kind: 'roof', amp: 0.02 });
  add_([[lx, top - 0.04, cz], [wo, top - 0.04, cz], [wo, top + 0.04, cz], [lx, top + 0.04, cz]], [226, 214, 190], { kind: 'cut', amp: 0.004 });
  add_([[lx - 0.06, -0.12, cz], [wo + 0.02, -0.12, cz], [wo + 0.02, 0.0, cz], [lx - 0.06, 0.0, cz]], [226, 214, 190], { kind: 'cut', amp: 0.004 });
  SET.front = S.splice(0);
  // porch post near the steps (behind the dog's path), lantern-less
  SET.posts = [[pe - 0.15, pz0 + 0.05], [pe - 0.15, pz1 - 0.06]];
}
function drawSetList(list) {
  for (const o of list) {
    let col = o.col, w = 0;
    if (o.kind === 'roomfloor' || o.kind === 'roomwall' || o.kind === 'rug' || o.kind === 'wallface' || o.kind === 'pic') w = 0.75;
    if (o.kind === 'sill' || o.kind === 'jamb') w = 0.3 + 0.6 * LIGHT.amt;
    if (o.kind === 'cut') { fillPoly(g, o.pts, `rgb(${col.map(v => v * 0.86 | 0)})`); continue; }
    if (o.kind === 'sky' || o.kind === 'far') { fillPoly(g, o.pts, `rgb(${col})`); continue; }
    fillPoly(g, o.pts, shade(col, w));
  }
}
let GRAIN = null;
function buildGrain() {
  const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'), R = rng(5);
  x.fillStyle = 'rgb(128,128,128)'; x.fillRect(0, 0, W, H);
  for (let k = 0; k < 9000; k++) { const px = R() * W, py = R() * H, a = R() * Math.PI, l = 3 + R() * 14, v = R() < 0.5 ? 150 + R() * 40 : 90 + R() * 30; x.strokeStyle = `rgba(${v | 0},${v | 0},${v | 0},0.35)`; x.lineWidth = 0.6 + R() * 0.8; x.beginPath(); x.moveTo(px, py); x.lineTo(px + Math.cos(a) * l, py + Math.sin(a) * l); x.stroke(); }
  GRAIN = c;
}

// ---------- dynamic items ----------
const BUF = [];
function item(d, fn, tag) { BUF.push({ d, fn, tag }); }
function dogItems(st) {
  const { g: dg, P } = st, D = SCENE.DOG;
  const bodyD = depth(dg.cores[3].c);
  const furCol = (s, p, dark = 1) => shade(COL[s.col], warmAt(p), dark * (0.92 + 0.16 * s.jit), 0.93);
  const creaseCol = p => shade([60, 40, 30], warmAt(p), 1, 0.35);
  // core spheres (the underlayer the fringe hangs from)
  dg.cores.forEach((c, k) => item(depth(c.c) - 0.001, ctx => blob(ctx, c.c, c.r, 900 + k, shade(k < 2 ? COL.rust : k > 3 ? COL.oat : COL.ochre, warmAt(c.c), 0.82)), 'torso'));
  dg.neck.forEach((c, k) => item(depth(c.c) - 0.001, ctx => blob(ctx, c.c, c.r, 920 + k, shade(COL.oat, warmAt(c.c), 0.85)), 'torso'));
  // legs: crepe tubes with dark paws
  dg.legs.forEach((lg, k) => {
    let d = depth(lg.J) - 0.1 + (lg.near ? 0.0 : -0.02); if (lg.fore) d = Math.min(d, depth(dg.head.c) - 0.05);
    item(d, ctx => {
      const P = [lg.J, lg.knee, lg.paw].map(P3);
      ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = shade(lg.fore ? COL.oat : COL.ochre, warmAt(lg.knee), lg.near ? 0.8 : 0.62);
      ctx.lineWidth = 0.085 * CAM.s; ctx.beginPath(); ctx.moveTo(P[0][0], P[0][1]); ctx.lineTo(P[1][0], P[1][1]); ctx.stroke();
      ctx.lineWidth = 0.062 * CAM.s; ctx.beginPath(); ctx.moveTo(P[1][0], P[1][1]); ctx.lineTo(P[2][0], P[2][1]); ctx.stroke();
      if (!(lg.fore && P.lieF > 0.5)) blob(ctx, lg.paw, 0.042, 940 + k, shade(COL.char, warmAt(lg.paw), lg.near ? 1 : 0.8), 0.7);
    }, 'limb');
    if (lg.fore && P.lieF > 0.5) item(depth(dg.head.c) + 0.08 + (lg.near ? 0.01 : 0), ctx => {
      const a = P3(lerp3(lg.knee, lg.paw, 0.35)), b = P3(lg.paw); ctx.lineCap = 'round'; ctx.strokeStyle = shade(COL.oat, warmAt(lg.paw), lg.near ? 0.85 : 0.7); ctx.lineWidth = 0.06 * CAM.s; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
      blob(ctx, lg.paw, 0.048, 940 + k, shade(COL.char, warmAt(lg.paw), lg.near ? 1 : 0.85), 0.62);
      const q = P3(lg.paw); ctx.strokeStyle = 'rgba(20,14,12,0.6)'; ctx.lineWidth = 1.2; for (let j = -1; j <= 1; j++) { ctx.beginPath(); ctx.moveTo(q[0] + j * 0.014 * CAM.s - 0.03 * CAM.s, q[1] - 0.008 * CAM.s); ctx.lineTo(q[0] + j * 0.014 * CAM.s - 0.045 * CAM.s, q[1] + 0.01 * CAM.s); ctx.stroke(); }
    }, 'limb');
  });
  // fringe strands
  const strandItem = (s, tag, bias = 0, w0 = s.w, w1 = s.w * 0.55) => {
    const anchorD = depth(s.p[0]); item(anchorD + bias, ctx => ribbon(ctx, s.p, w0, w1, s.seed, furCol(s, s.p[1], anchorD < bodyD - 0.05 ? 0.78 : 1), creaseCol(s.p[1])), tag);
  };
  // body fringe: overlapping crepe shingles; upper rows lie over lower ones (key = depth + height above the body axis)
  D.body.forEach(s => {
    const c = dg.ring(s.f).c, key = depth(s.p[0]) + 1.0 * (s.p[0][1] - c[1]) + 0.004;
    const dark = depth(s.p[0]) < depth(c) - 0.06 ? 0.8 : 1;
    item(key, ctx => {
      const fill = furCol(s, s.p[1], dark), q = P3(s.p[0]);
      ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(q[0], q[1], s.w * 0.5 * CAM.s, 0, 7); ctx.fill();
      ribbon(ctx, s.p, s.w, s.w * 0.55, s.seed, fill, creaseCol(s.p[1]));
    }, 'torso');
  });
  D.ruff.forEach(s => strandItem(s, 'torso', 0.004, 0.075, 0.045));
  D.legFeathers.forEach(s => strandItem(s, 'limb', 0.003));
  // tail link + plume
  item(depth(D.tail.p[2]) - 0.01, ctx => ribbon(ctx, D.tail.p, 0.06, 0.035, 77, shade(COL.ochre, warmAt(D.tail.p[2]), 0.9), null, false), 'limb');
  D.tailFeathers.forEach(s => strandItem(s, 'limb', 0.002 * (s.j - 1)));
  // head: skull, muzzle, nose, eyes; ears; head fringe; dewlap
  const hd = depth(dg.head.c);
  item(hd, ctx => {
    const hdD = depth(dg.head.c), mz = dg.muz.map((m, k) => ({ m, d: depth(m.c), k })).sort((a, b) => a.d - b.d);
    const muzzle = () => { for (const { m, k } of mz) blob(ctx, m.c, m.r, 961 + k, shade(COL.cream, warmAt(m.c), 0.98)); blob(ctx, dg.nose.c, dg.nose.r, 965, shade([34, 26, 24], warmAt(dg.nose.c))); };
    const away = depth(dg.nose.c) < hdD - 0.04;   // muzzle pointing away from us: it goes behind the skull
    if (away) muzzle();
    blob(ctx, dg.head.c, dg.head.r, 960, shade(COL.cream, warmAt(dg.head.c), 0.93));
    if (away) { // the back of the skull: a darker crown patch between the ears
      blob(ctx, add(dg.head.c, mul(dg.Uh, 0.045)), dg.head.r * 0.72, 966, shade(COL.char, warmAt(dg.head.c), 0.9), 0.8);
    } else muzzle();
    for (const e of dg.eyes) { const f = dot(e.n, VIEW); if (f > 0.05) { const q = P3(e.c), r = 0.017 * CAM.s * clamp(f * 1.6, 0.35, 1); ctx.fillStyle = 'rgb(22,16,14)'; ctx.beginPath(); ctx.ellipse(q[0], q[1], r * clamp(f * 1.4, 0.4, 1), r, 0, 0, 7); ctx.fill(); ctx.fillStyle = `rgba(255,236,200,${0.5 * LIGHT.amt + 0.3})`; ctx.beginPath(); ctx.arc(q[0] + r * 0.3, q[1] - r * 0.35, r * 0.28, 0, 7); ctx.fill(); } }
  }, 'head');
  D.head.forEach(s => strandItem(s, 'head', s.where === 'fore' ? 0.06 : 0.01));
  item(0, ctx => { for (const m of dg.muz) blob(ctx, m.c, m.r, 961, '#fff'); blob(ctx, dg.nose.c, dg.nose.r, 965, '#fff'); }, 'm_snout');
  item(0, ctx => blob(ctx, dg.head.c, dg.head.r, 960, '#fff'), 'm_skull');
  D.dewlap.forEach(s => strandItem(s, 'head', -0.002, 0.07, 0.04));
  D.ears.forEach((e, k) => {
    const headAway = depth(dg.nose.c) < hd - 0.04;
    const d = headAway ? hd + 0.03 + 0.001 * k : depth(e.p[1]) + (depth(e.p[0]) > hd ? 0.02 : -0.02);
    item(d, ctx => ribbon(ctx, e.p, 0.12, 0.1, 980 + k, shade(COL.rust, warmAt(e.p[1]), 0.95), shade([30, 20, 18], 0.3, 1, 0.4)), 'head');
  });
  const hAway = depth(dg.nose.c) < hd - 0.04;
  D.earFeathers.forEach(s => { const hostD = hAway ? hd + 0.031 : depth(s.host.p[1]) + (depth(s.host.p[0]) > hd ? 0.021 : -0.019); item(hostD, ctx => ribbon(ctx, s.p, s.w, s.w * 0.5, s.seed, furCol(s, s.p[1]), null), 'head'); });
  // contact shadow on the floor
  const M = dg.cores[3].c, R = dg.F;
  item(-99, ctx => { const q = P3([M[0], 0.002, M[2]]); ctx.fillStyle = 'rgba(10,10,24,0.35)'; ctx.beginPath(); ctx.ellipse(q[0], q[1], (0.62 * Math.abs(R[0]) + 0.3) * CAM.s * cP, 0.09 * CAM.s, 0, 0, 7); ctx.fill(); }, 'shadow');
}
function curtainItems() {
  SCENE.CURTAIN.forEach((s, k) => { const d = depth([s.p[0][0], 0.95, s.p[0][2]]) - (ST && ST.P.lieF > 0.05 ? 1 : 0); item(d, ctx => ribbon(ctx, s.p, s.w, s.w * 0.92, s.seed, shade(COL[s.col], 0.15 + 0.35 * warmAt([-0.2, 1, s.z]), 0.8, 0.5), shade([90, 40, 30], 0.4, 1, 0.25)), 'curtain'); });
}
function reedItems(back) {
  SCENE.REEDS.forEach(s => {
    if ((s.z < -1.4) !== back) return;
    const fn = ctx => {
      const P = ribbon(ctx, s.p, s.w * 1.4, s.w * 0.5, s.seed, shade(COL[s.col], 0.05, 0.9), null, false);
      if (s.head) { const a = P[P.length - 2], b = P[P.length - 1]; const ang = Math.atan2(b[1] - a[1], b[0] - a[0]); ctx.fillStyle = shade([92, 62, 40], 0.05, 0.9); ctx.beginPath(); ctx.ellipse((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, Math.hypot(b[0] - a[0], b[1] - a[1]) * 0.5, 0.022 * CAM.s, ang, 0, 7); ctx.fill(); }
    };
    if (back) fn(g); else item(depth(s.p[0]), fn, 'reed');
  });
}
function personItems(st) {
  const pg = st.pg, PR = SCENE.PERSON, w = warmAt([pg.pelvis[0], 1, pg.z]) * 0.8 + 0.15;
  const d = depth(pg.pelvis);
  item(d, ctx => {
    const line = (a, b, wd, col) => { const A = P3(a), B = P3(b); ctx.strokeStyle = col; ctx.lineWidth = wd * CAM.s; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke(); };
    const far = 0.72;
    // far limbs
    line(pg.hipF, pg.kneeF, 0.13, shade(COL.trouser, w, far)); line(pg.kneeF, pg.footF, 0.11, shade(COL.trouser, w, far));
    blob(ctx, add(pg.footF, [0.05, 0, 0]), 0.055, 31, shade([30, 26, 28], w, far), 0.6);
    line(pg.shF, pg.elbF, 0.095, shade(COL.coat, w, far)); line(pg.elbF, pg.handF, 0.085, shade(COL.coat, w, far)); blob(ctx, pg.handF, 0.045, 32, shade(COL.skin, w, far));
    // hair behind the head
    PR.hair.forEach(s => ribbon(ctx, s.p, s.w, s.w * 0.6, s.seed, shade(COL.hair, w, 0.95), null));
    PR.scarf[1] && ribbon(ctx, PR.scarf[1].p, PR.scarf[1].w, PR.scarf[1].w * 0.9, 51, shade(COL.scarf, w, 0.8), shade([120, 80, 20], w, 1, 0.4));
    // coat tails and torso
    PR.coat.forEach((s, k) => ribbon(ctx, s.p, s.w, s.w * 1.15, 60 + k, shade(COL.coat, w, k === 1 ? 0.9 : 0.8), shade([20, 40, 44], w, 1, 0.35)));
    const lean = pg.lean, nx = Math.sin(lean), ny = Math.cos(lean), px = ny, py = -nx; // torso axis and its perpendicular (in X,Y)
    const tz = pg.z, pv = pg.pelvis, nk = pg.neck;
    fillPoly(ctx, tornPoly3([[pv[0] - 0.19 * px, pv[1] - 0.19 * py + 0.02, tz], [pv[0] + 0.19 * px, pv[1] + 0.19 * py + 0.02, tz], [nk[0] + 0.15 * px, nk[1] + 0.15 * py - 0.04, tz], [nk[0] - 0.15 * px, nk[1] - 0.15 * py - 0.04, tz]], 71, 0.01, 0.08), shade(COL.coat, w, 0.95));
    // near leg
    line(pg.hipN, pg.kneeN, 0.135, shade(COL.trouser, w)); line(pg.kneeN, pg.footN, 0.115, shade(COL.trouser, w));
    blob(ctx, add(pg.footN, [0.05, 0, 0]), 0.058, 33, shade([30, 26, 28], w), 0.6);
    // head: a torn disc in profile with a nose, an eye, a hair cap
    const hc = pg.headC;
    blob(ctx, hc, 0.108, 34, shade(COL.skin, w));
    blob(ctx, add(hc, [0.1, -0.005, 0.02]), 0.022, 35, shade(COL.skin, w, 0.97));
    blob(ctx, add(hc, [-0.05, 0.05, 0]), 0.095, 36, shade(COL.hair, w), 0.85);
    const ey = P3(add(hc, [0.055, 0.025, 0.06])); ctx.fillStyle = 'rgb(28,20,18)'; ctx.beginPath(); ctx.arc(ey[0], ey[1], 0.012 * CAM.s, 0, 7); ctx.fill();
    const m = st.Q.mouth; if (m > 0.05) { const mq = P3(add(hc, [0.085, -0.055, 0.04])); ctx.fillStyle = 'rgb(60,24,24)'; ctx.beginPath(); ctx.ellipse(mq[0], mq[1], 0.012 * CAM.s, 0.016 * CAM.s * m, 0, 0, 7); ctx.fill(); }
    // scarf around the neck and its front tail
    line(add(nk, [-0.08, -0.02, 0]), add(nk, [0.08, -0.03, 0]), 0.09, shade(COL.scarf, w));
    ribbon(ctx, PR.scarf[0].p, PR.scarf[0].w, PR.scarf[0].w * 0.95, 52, shade(COL.scarf, w), shade([120, 80, 20], w, 1, 0.4));
    // near arm
    line(pg.shN, pg.elbN, 0.1, shade(COL.coat, w, 1.05)); line(pg.elbN, pg.handN, 0.088, shade(COL.coat, w, 1.05)); blob(ctx, pg.handN, 0.047, 37, shade(COL.skin, w));
  }, 'person');
}

// ---------- frame ----------
let ST = null, PRE = 'tuned';
window.init = (scoreJSON, preset) => { SCENE.init(JSON.parse(scoreJSON), preset); PRE = preset; buildSet(); buildGrain(); return 768; };
function drawScene(st, label) {
  const t = st.t; CAM = camAt(t);
  LIGHT = { amt: 0.18 + 0.82 * st.door.open, z1: clamp(st.door.edge[2], -0.46, 0.46) };
  g.globalCompositeOperation = 'source-over'; g.fillStyle = '#121426'; g.fillRect(0, 0, W, H);
  drawSetList(SET.back);
  // moon
  const mq = P3([7.6, 3.6, -14]); g.fillStyle = 'rgba(236,220,170,0.92)'; g.beginPath(); g.arc(mq[0], mq[1], 0.34 * CAM.s, 0, 7); g.fill(); g.fillStyle = 'rgba(40,36,74,0.55)'; g.beginPath(); g.arc(mq[0] + 0.12 * CAM.s, mq[1] - 0.05 * CAM.s, 0.3 * CAM.s, 0, 7); g.fill();
  reedItems(true);
  // back rail of the porch
  const rz = SET.rail.z; g.lineCap = 'butt';
  const seg = (a, b, wd, c) => { const A = P3(a), B = P3(b); g.strokeStyle = c; g.lineWidth = wd * CAM.s; g.beginPath(); g.moveTo(A[0], A[1]); g.lineTo(B[0], B[1]); g.stroke(); };
  // the room, the lamp, its glow, the door leaf
  drawSetList(SET.room);
  const lp = PL.lamp; seg([lp[0], 0, lp[2]], [lp[0], 1.55, lp[2]], 0.025, 'rgb(40,30,26)');
  fillPoly(g, [[lp[0] - 0.2, 1.5, lp[2]], [lp[0] + 0.2, 1.5, lp[2]], [lp[0] + 0.13, 1.82, lp[2]], [lp[0] - 0.13, 1.82, lp[2]]], 'rgba(255,214,140,0.95)');
  const glow = P3([lp[0], 1.6, lp[2]]), gr = g.createRadialGradient(glow[0], glow[1], 5, glow[0], glow[1], 2.4 * CAM.s);
  gr.addColorStop(0, 'rgba(255,200,120,0.45)'); gr.addColorStop(1, 'rgba(255,200,120,0)'); g.globalCompositeOperation = 'lighter'; g.fillStyle = gr; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over';
  const hg = PL.hinge, e = st.door.edge;
  fillPoly(g, [[hg[0], 0.01, hg[1]], [e[0], 0.01, e[2]], [e[0], PL.doorH - 0.02, e[2]], [hg[0], PL.doorH - 0.02, hg[1]]], shade([110, 70, 52], 0.55));
  fillPoly(g, [[lerp(hg[0], e[0], 0.15), 0.35, lerp(hg[1], e[2], 0.15)], [lerp(hg[0], e[0], 0.85), 0.35, lerp(hg[1], e[2], 0.85)], [lerp(hg[0], e[0], 0.85), 1.75, lerp(hg[1], e[2], 0.85)], [lerp(hg[0], e[0], 0.15), 1.75, lerp(hg[1], e[2], 0.15)]], shade([128, 84, 60], 0.55));
  drawSetList(SET.wall);
  for (const y of SET.clap) { if (y < PL.doorH) { seg([0, y, PL.roomBackZ], [0, y, PL.doorZ[0]], 0.006, 'rgba(30,34,54,0.55)'); } else seg([0, y, PL.roomBackZ], [0, y, PL.doorZ[1]], 0.006, 'rgba(30,34,54,0.55)'); }
  drawSetList(SET.porch);
  for (const b of SET.boards) seg(b[0], b[1], 0.006, 'rgba(40,40,56,0.6)');
  for (let x = SET.rail.x0; x < SET.rail.x1; x += 0.24) seg([x, 0, rz], [x, 0.86, rz], 0.035, shade([70, 66, 86], warmAt([x, 0.5, rz]) * 0.5));
  seg([SET.rail.x0, 0.88, rz], [SET.rail.x1, 0.88, rz], 0.06, shade([84, 78, 98], 0.1));
  for (const [x, z] of SET.posts) seg([x, -0.45, z], [x, 2.5, z], 0.1, shade([70, 64, 84], 0.05));
  // light out of the doorway onto the porch (a wedge from the lamp through the opening)
  {
    const Lx = lp[0], Lz = lp[2], z1 = LIGHT.z1, x1 = PL.porchEnd, f = (x1 - Lx) / (-Lx);
    const q = [[0, 0.003, z1], [0, 0.003, 0.46], [x1, 0.003, clamp(Lz + (0.46 - Lz) * f, -1.3, PL.porchZ[1])], [x1, 0.003, clamp(Lz + (z1 - Lz) * f, PL.porchZ[0], 1.1)]].map(P3);
    const a = P3([0, 0, 0]), b = P3([3.2, 0, 0]), lg = g.createLinearGradient(a[0], a[1], b[0], b[1]);
    lg.addColorStop(0, `rgba(255,190,110,${0.42 * LIGHT.amt})`); lg.addColorStop(1, 'rgba(255,190,110,0)');
    g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = lg; g.beginPath(); q.forEach((p, k) => k ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath(); g.fill(); g.restore();
  }
  drawSetList(SET.sill);
  // dynamic: dog, person, curtain, near reeds — painter's order by view depth
  BUF.length = 0; dogItems(st); personItems(st); curtainItems(); reedItems(false);
  BUF.sort((a, b) => a.d - b.d);
  for (const it of BUF) if (!it.tag.startsWith('m_')) it.fn(g);
  // the near cut of the house (card) and roof section, in front of everything at the doorway
  drawSetList(SET.front);
  // paper grain and a soft vignette
  g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.32; g.drawImage(GRAIN, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  const vg = g.createRadialGradient(W / 2, H * 0.55, H * 0.45, W / 2, H * 0.55, H * 0.95); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(6,6,16,0.45)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
  if (label) { g.font = '600 26px "Big Shoulders Display"'; g.fillStyle = 'rgba(240,230,210,0.9)'; g.fillText(label, 24, 40); }
}
function measure() {
  const out = {};
  const groups = { torso: ['torso'], head: ['head'], limb: ['limb'], m_snout: ['m_snout'], m_skull: ['m_skull'] };
  masks.forEach((m, k) => {
    const name = Object.keys(groups)[k]; m.x.setTransform(1, 0, 0, 1, 0, 0); m.x.clearRect(0, 0, MW, MH); m.x.setTransform(MS, 0, 0, MS, 0, 0);
    for (const it of BUF) if (it.tag === name) it.fn(m.x);
    const d = m.x.getImageData(0, 0, MW, MH).data; let n = 0, sx = 0, sy = 0, x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let y = 0; y < MH; y++) for (let x = 0; x < MW; x++) if (d[(y * MW + x) * 4 + 3] > 100) { n++; sx += x; sy += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    out[name] = n ? { n, cx: sx / n / MS, cy: sy / n / MS, bbox: [x0 / MS, y0 / MS, (x1 + 1) / MS, (y1 + 1) / MS] } : null;
  });
  return out;
}
window.frame = (i, draw, label) => {
  const st = SCENE.frame(i); ST = st;
  CAM = camAt(st.t);
  if (draw) drawScene(st, label); else { BUF.length = 0; dogItems(st); }
  const m = measure();
  const all = ['torso', 'head', 'limb'].map(k => m[k]).filter(Boolean);
  const N = all.reduce((a, o) => a + o.n, 0), cx = all.reduce((a, o) => a + o.cx * o.n, 0) / N, cy = all.reduce((a, o) => a + o.cy * o.n, 0) / N;
  const bb = [Math.min(...all.map(o => o.bbox[0])), Math.min(...all.map(o => o.bbox[1])), Math.max(...all.map(o => o.bbox[2])), Math.max(...all.map(o => o.bbox[3]))];
  const wc = unprojectZ0(cx, cy), wt = m.torso ? unprojectZ0(m.torso.cx, m.torso.cy) : null, wh = m.head ? unprojectZ0(m.head.cx, m.head.cy) : null;
  const wtop = m.torso ? unprojectZ0(m.torso.cx, m.torso.bbox[1]) : null;
  const res = {
    i, t: st.t, cam: CAM, x_screen: +cx.toFixed(1), y_screen: +cy.toFixed(1), bbox: bb.map(v => Math.round(v)), x_world_measured: +wc[0].toFixed(3),
    snout_px: m.m_snout && [+m.m_snout.cx.toFixed(1), +m.m_snout.cy.toFixed(1)], skull_px: m.m_skull && [+m.m_skull.cx.toFixed(1), +m.m_skull.cy.toFixed(1)],
    torso_px: m.torso && [+m.torso.cx.toFixed(1), +m.torso.cy.toFixed(1)], head_px: m.head && [+m.head.cx.toFixed(1), +m.head.cy.toFixed(1)],
    torso_y_world: wt && +wt[1].toFixed(3), back_top_y_world: wtop && +wtop[1].toFixed(3), head_y_world: wh && +wh[1].toFixed(3), head_x_world: wh && +wh[0].toFixed(3), torso_x_world: wt && +wt[0].toFixed(3),
    energy: st.energy, wind: st.wind, draft: st.draft, door: st.door.a, door_open: st.door.open, paws: st.paws, ear_tip_y: SCENE.DOG.ears.map(e => +e.p[3][1].toFixed(3)),
    tail_tip: SCENE.DOG.tail.p[5].map(v => +v.toFixed(3)), fur_tip_mean_y: +(SCENE.DOG.body.reduce((a, s) => a + s.p[3][1], 0) / SCENE.DOG.body.length).toFixed(4),
    fur_radial: +(() => { let a = 0; const F = st.g.F; for (const s of SCENE.DOG.body) { const c = st.g.ring(s.f).c, v = sub(s.p[3], c), along = dot(v, F); a += len(sub(v, mul(F, along))); } return a / SCENE.DOG.body.length; })().toFixed(4),
    fur_spread: +(() => { const c = st.g.cores[3].c; let a = 0; for (const s of SCENE.DOG.body) a += Math.hypot(s.p[3][0] - c[0], s.p[3][2] - c[2]); return a / SCENE.DOG.body.length; })().toFixed(4),
    prim: { th: st.P.th, hw: st.P.hw, lieF: st.P.lieF, lieR: st.P.lieR, fear: st.P.fear, ear: st.P.ear, rest: st.P.rest, look: st.P.look },
  };
  const img = draw ? cv.toDataURL('image/jpeg', 0.93) : null;
  return { img, m: res };
};
const fitText = (txt, x, y, font, px, maxW) => { let p = px; do { g.font = font.replace('{px}', p + 'px'); p -= 1; } while (g.measureText(txt).width > maxW && p > 10); g.fillText(txt, x, y); };
window.card = (kind, lines) => {
  g.globalCompositeOperation = 'source-over'; g.fillStyle = '#15172a'; g.fillRect(0, 0, W, H);
  // a few torn tissue strips as the card's ground
  const R = rng(kind === 'title' ? 3 : 4), cols = [[196, 145, 63], [156, 85, 48], [239, 226, 196], [78, 60, 52], [216, 196, 152]];
  for (let k = 0; k < 46; k++) { const x = 80 + R() * 1120, y = kind === 'title' ? 470 + R() * 160 : 600 + R() * 80, l = 60 + R() * 120, w = 10 + R() * 12, a = Math.PI / 2 + (R() - 0.5) * 0.5; const c = cols[k % 5]; g.fillStyle = `rgba(${c},0.8)`; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l - w / 2, y + Math.sin(a) * l * 0.6); for (let j = 0; j < 4; j++) g.lineTo(x + Math.cos(a) * l + (j - 2) * w / 4, y + Math.sin(a) * l * 0.6 + (j % 2 ? 6 : 0)); g.lineTo(x + w, y); g.closePath(); g.fill(); }
  g.fillStyle = '#efe2c2';
  if (kind === 'title') {
    fitText('PAE-02 · SCION 13 · Nora Willett — Secondary Motion', 80, 250, '800 {px} "Big Shoulders Display"', 64, 1120);
    g.fillStyle = 'rgba(239,226,196,0.85)'; fitText('The threshold. A dog of crepe-paper fringe; every strip a spring-damper.', 80, 320, '400 {px} Literata', 30, 1120);
  } else {
    g.font = '800 44px "Big Shoulders Display"'; g.fillText('What this is made of', 80, 110);
    g.fillStyle = 'rgba(239,226,196,0.9)'; (lines || []).forEach((l, k) => fitText(l, 80, 170 + k * 38, '400 {px} Literata', 23, 1120));
  }
  g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.3; g.drawImage(GRAIN, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  return cv.toDataURL('image/jpeg', 0.95);
};
window.ready = Promise.all(['800 64px "Big Shoulders Display"', '600 26px "Big Shoulders Display"', '400 30px Literata'].map(f => document.fonts.load(f))).then(() => document.fonts.ready).then(() => document.fonts.check('400 30px Literata') && document.fonts.check('800 64px "Big Shoulders Display"'));
