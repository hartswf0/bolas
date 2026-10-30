/* SCION 18 · Cartoon Saloon — painterly puppet renderer (browser canvas). Draws from SHEET (sheet.js) and the score.
   Shot style contract (one shot, locked camera, side elevation of a cut-away house and its porch):
     world x in metres = the score's x (threshold 0, porch steps 4.9). screen x = X0 + S·x, floor at y = FLOOR.
     Line: tapered brush ribbons built in SCREEN pixels (width never scales with a part), self-coloured (darker than fill).
     Fill: flat pigment + an attached watercolour wash (multiply) + pooled edge. Light: compositing palette per layer
     (cool dusk outside, warm lamplight inside / in the door's light pool). Paper grain is applied once, in screen space. */
'use strict';
const W = 1280, H = 720, S = 180, X0 = 320, FLOOR = 600, K = S / 100; // K: px per cm
const WALL = [0.47, 0.69];             // the cut wall (door frame) in score metres; sill at 0.56 sits inside it
const sx = x => X0 + x * S, sy = y => FLOOR - y * S;
const TEX = {};
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ss = (a, b, t) => { const u = clamp((t - a) / (b - a)); return u * u * (3 - 2 * u); };
const lp = (p, q, t) => [lerp(p[0], q[0], t), lerp(p[1], q[1], t)];

// ---------- seeded smooth noise (fixed per drawing, so lines never boil)
function noise1(seed, s) {
  let v = 0, a = 1, n = 0;
  for (let k = 1; k <= 3; k++) { const ph = Math.sin(seed * 12.9898 * k + k * 78.233) * 43758.5453; v += a * Math.sin(s * k * 2.1 + (ph - Math.floor(ph)) * 6.283); n += a; a *= 0.55; }
  return v / n; // -1..1
}
function rnd(seed) { const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }

// ---------- curves
function crSample(P, closed, per = 10) {
  const out = [], n = P.length;
  const get = i => closed ? P[(i + n) % n] : P[Math.max(0, Math.min(n - 1, i))];
  const segs = closed ? n : n - 1;
  for (let i = 0; i < segs; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    for (let j = 0; j < per; j++) {
      const t = j / per, t2 = t * t, t3 = t2 * t;
      out.push([0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)]);
    }
  }
  if (!closed) out.push(P[n - 1]);
  return out;
}
function resample(pts, N, closed = true) { // arclength resampling, starting at point 0 (the authored start = correspondence)
  const L = [0]; const m = pts.length; const segs = closed ? m : m - 1;
  for (let i = 0; i < segs; i++) { const a = pts[i], b = pts[(i + 1) % m]; L.push(L[i] + Math.hypot(b[0] - a[0], b[1] - a[1])); }
  const tot = L[L.length - 1], out = []; let j = 0;
  for (let k = 0; k < N; k++) {
    const d = tot * k / (closed ? N : N - 1);
    while (j < segs - 1 && L[j + 1] < d) j++;
    const a = pts[j], b = pts[(j + 1) % m], u = (d - L[j]) / Math.max(1e-9, L[j + 1] - L[j]);
    out.push(lp(a, b, clamp(u)));
  }
  return out;
}
// in-between two authored drawings of the same part (dense, resampled), t in 0..1
function between(A, B, t, closed = true, N = 120) {
  const a = resample(crSample(A, closed), N, closed);
  if (!B || t <= 0) return a;
  const b = resample(crSample(B, closed), N, closed);
  return a.map((p, i) => lp(p, b[i], t));
}
function lerpPts(A, B, t) { return A.map((p, i) => lp(p, B[i], t)); }
function mirrorPts(A) { return A.map(p => [-p[0], p[1]]); }

// ---------- the brush: a tapered ribbon in screen px, width independent of the part's size or deformation
const LINE_LOG = { sum: 0, n: 0 };
const CAM = { z: 1, tx: 0, ty: 0 }; // camera: screen = z*world + t. Lines are divided by z so they keep their screen weight.
function brush(ctx, pts, closed, w, color, seed, opt = {}) {
  const n = pts.length; if (n < 2) return;
  w = w / CAM.z;
  let L = 0; const acc = [0];
  for (let i = 1; i < n; i++) { L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); acc.push(L); }
  if (closed) L += Math.hypot(pts[0][0] - pts[n - 1][0], pts[0][1] - pts[n - 1][1]);
  const left = [], right = [];
  const gap = opt.gap === undefined ? rnd(seed) : opt.gap; // where the hand lifted (closed lines only)
  for (let i = 0; i < n; i++) {
    const a = pts[(i - 1 + n) % n], b = pts[(i + 1) % n];
    const pa = (!closed && i === 0) ? pts[0] : a, pb = (!closed && i === n - 1) ? pts[n - 1] : b;
    let tx = pb[0] - pa[0], ty = pb[1] - pa[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
    const s = acc[i] / Math.max(1, L);
    let ww = w * (0.82 + 0.3 * noise1(seed, acc[i] / 9)); // pressure varies with arclength in px (stable per drawing)
    if (!closed) ww *= Math.min(1, s / 0.18, (1 - s) / 0.18) * 0.85 + 0.15;
    else { const d = Math.abs(((s - gap + 1.5) % 1) - 0.5); ww *= d < 0.035 ? 0.25 + 0.75 * d / 0.035 : 1; }
    LINE_LOG.sum += ww * CAM.z; LINE_LOG.n++; // logged in screen px
    left.push([pts[i][0] - ty * ww / 2, pts[i][1] + tx * ww / 2]); right.push([pts[i][0] + ty * ww / 2, pts[i][1] - tx * ww / 2]);
  }
  ctx.beginPath();
  if (closed) {
    ctx.moveTo(left[0][0], left[0][1]); for (const p of left) ctx.lineTo(p[0], p[1]); ctx.closePath();
    ctx.moveTo(right[0][0], right[0][1]); for (let i = n - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]); ctx.closePath();
    ctx.fillStyle = color; ctx.fill('evenodd');
  } else {
    ctx.moveTo(left[0][0], left[0][1]); for (const p of left) ctx.lineTo(p[0], p[1]);
    for (let i = n - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]); ctx.closePath();
    ctx.fillStyle = color; ctx.fill();
  }
}
function polyPath(ctx, pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath(); }
// painted shape: pigment + attached wash + pooled edge + brush line
function ink(ctx, pts, st) {
  polyPath(ctx, pts); ctx.fillStyle = st.fill; ctx.fill();
  if (st.tex !== null) {
    ctx.save(); polyPath(ctx, pts); ctx.clip();
    const pat = TEX.pat[st.tex === undefined ? 0 : st.tex];
    const ax = st.anchor ? st.anchor[0] : 0, ay = st.anchor ? st.anchor[1] : 0;
    pat.setTransform(new DOMMatrix().translate(ax, ay));
    ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = st.texA === undefined ? 0.55 : st.texA;
    ctx.fillStyle = pat; let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (const p of pts) { x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]); }
    ctx.fillRect(x0 - 2, y0 - 2, x1 - x0 + 4, y1 - y0 + 4);
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = st.pool === undefined ? 0.22 : st.pool;
    ctx.lineWidth = 6 / CAM.z; ctx.strokeStyle = st.line; ctx.lineJoin = 'round'; polyPath(ctx, pts); ctx.stroke();
    ctx.restore();
  }
  if (st.lw) brush(ctx, pts, true, st.lw, st.line, st.seed || 1);
}

// ---------- palette (the compositing palettes)
const PAL = {
  coat: '#c17a3a', coatFar: '#9a5a2c', coatLine: '#3d2112', cream: '#efd9ad', ear: '#7a4224', nose: '#21140f', eye: '#1a110c',
  dress: '#2e5f5b', dressLine: '#14302e', shawl: '#a9452e', shawlLine: '#4c1a10', skin: '#e3b48b', skinLine: '#6b3b22', hair: '#3a2621',
  wallIn: '#7e2f26', wallInLit: '#a8442f', motif: '#d9a24a', floorIn: '#5b3a24', rug: '#355a4c',
  section: '#3a2a2a', frame: '#c9a06a', frameLine: '#4a2d18', door: '#2f4f3f', doorLine: '#14241b',
  plank: '#6d4f3a', plankLine: '#2b1c14', skyTop: '#1f2346', skyMid: '#4b3f6c', skyLow: '#c07a74', skyHorizon: '#e7ab73',
  hill: '#2a2f52', tree: '#203a44', treeLine: '#0f1d24', moon: '#f4e6c3',
};

// ---------- texture loading
async function loadTextures(base) {
  const names = ['wash0', 'wash1', 'wash2', 'paper', 'wood', 'speck'];
  const c = document.createElement('canvas').getContext('2d');
  for (const n of names) { const im = new Image(); im.src = (window.TEXDATA && window.TEXDATA[n]) || (base + n + '.png'); await im.decode(); TEX[n] = im; }
  TEX.pat = [c.createPattern(TEX.wash0, 'repeat'), c.createPattern(TEX.wash1, 'repeat'), c.createPattern(TEX.wash2, 'repeat')];
  TEX.woodPat = c.createPattern(TEX.wood, 'repeat');
}
if (typeof window !== 'undefined') Object.assign(window, { W, H, S, X0, FLOOR, K, WALL, sx, sy, TEX, lerp, clamp, ss, lp, noise1, rnd, crSample, resample, between, lerpPts, mirrorPts, brush, ink, polyPath, PAL, loadTextures, LINE_LOG, CAM });
