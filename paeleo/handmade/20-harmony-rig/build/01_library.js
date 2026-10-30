// SCION 20 · Harmony rig foundry · 01: the drawing library and the palette.
// Every drawing is authored here in code, in metres, y up, as vector shapes with a colour style (fill),
// line paths (ink) and a drawing layer (under / main / over). Each drawing carries its anchors
// (where the next peg attaches), so substitutions align on stable pivots. The output is DATA:
//   scene/library.json  (drawings by element: dog_body, dog_head, dog_ear, dog_tail, person, person_mouth, door)
//   scene/palette.json  (named colour styles, in a dusk palette and a lamp palette)
// Nothing is traced, photographed or imported: the drawings are constructed from points written below.
'use strict';
const fs = require('fs');
const path = require('path');
const OUT = path.join(__dirname, '..', 'scene');

// ---------- geometry ----------
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const mul = (a, s) => [a[0] * s, a[1] * s];
const len = (a) => Math.hypot(a[0], a[1]);
const nrm = (a) => { const l = len(a) || 1; return [a[0] / l, a[1] / l]; };
const lerp = (a, b, t) => a + (b - a) * t;
const lerpP = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
const R = (p) => [Math.round(p[0] * 10000) / 10000, Math.round(p[1] * 10000) / 10000];
const rnd = (pts) => pts.map(R);
const ang = (deg) => [Math.cos(deg * Math.PI / 180), Math.sin(deg * Math.PI / 180)];

// Catmull-Rom through points; returns {pts, seg} where seg[i] = index in pts where segment i starts
function catmull(P, closed, n = 7) {
  const out = [], seg = [];
  const N = P.length, M = closed ? N : N - 1;
  const g = (i) => closed ? P[(i + N) % N] : P[Math.max(0, Math.min(N - 1, i))];
  for (let i = 0; i < M; i++) {
    seg.push(out.length);
    const p0 = g(i - 1), p1 = g(i), p2 = g(i + 1), p3 = g(i + 2);
    for (let k = 0; k < n; k++) {
      const t = k / n, t2 = t * t, t3 = t2 * t;
      out.push([
        0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)]);
    }
  }
  if (!closed) out.push(P[N - 1]);
  seg.push(out.length);
  return { pts: out, seg };
}
function ellipse(c, rx, ry, rot = 0, n = 28) {
  const o = [], cr = Math.cos(rot), sr = Math.sin(rot);
  for (let i = 0; i < n; i++) { const a = i / n * 2 * Math.PI, x = rx * Math.cos(a), y = ry * Math.sin(a); o.push([c[0] + x * cr - y * sr, c[1] + x * sr + y * cr]); }
  return o;
}
// tapered tube through joints; returns {fill, sides} ; caps rounded; openStart drops the start cap from the line
function tube(J, W, opt = {}) {
  const c = catmull(J, false, 6).pts;
  // widths along samples
  const segs = J.length - 1;
  const w = c.map((_, i) => { const u = i / (c.length - 1) * segs; const k = Math.min(segs - 1, Math.floor(u)); return lerp(W[k], W[k + 1], u - k); });
  const L = [], Rr = [];
  for (let i = 0; i < c.length; i++) {
    const a = c[Math.max(0, i - 1)], b = c[Math.min(c.length - 1, i + 1)];
    const d = nrm(sub(b, a)), n = [-d[1], d[0]];
    L.push(add(c[i], mul(n, w[i] / 2))); Rr.push(add(c[i], mul(n, -w[i] / 2)));
  }
  const cap = (center, from, to, k = 6) => { // semicircle from 'from' to 'to' around center
    const r = len(sub(from, center)), a0 = Math.atan2(from[1] - center[1], from[0] - center[0]);
    let a1 = Math.atan2(to[1] - center[1], to[0] - center[0]);
    let da = a1 - a0; while (da <= 0) da += 2 * Math.PI; if (da > 2 * Math.PI) da -= 2 * Math.PI;
    const o = []; for (let i = 1; i < k; i++) { const a = a0 - (2 * Math.PI - da) * 0 + (da) * i / k; o.push([center[0] + r * Math.cos(a), center[1] + r * Math.sin(a)]); }
    return o;
  };
  const e = c.length - 1;
  const endCap = cap(c[e], L[e], Rr[e]).reverse().map((p) => p); // goes from L to R around the end
  const endC = []; { const d = nrm(sub(c[e], c[e - 1])); const r = w[e] / 2; for (let i = 1; i < 6; i++) { const a = Math.PI / 2 - Math.PI * i / 6; const n = [-d[1], d[0]]; endC.push(add(c[e], add(mul(n, r * Math.sin(a)), mul(d, r * Math.cos(a))))); } }
  const stC = []; { const d = nrm(sub(c[1], c[0])); const r = w[0] / 2; for (let i = 1; i < 6; i++) { const a = -Math.PI / 2 - Math.PI * i / 6; const n = [-d[1], d[0]]; stC.push(add(c[0], add(mul(n, r * Math.sin(a)), mul(d, r * Math.cos(a))))); } }
  const fill = [...L, ...endC, ...Rr.slice().reverse(), ...stC];
  const line = opt.openStart ? [...L, ...endC, ...Rr.slice().reverse()] : [...fill, fill[0]];
  return { fill, line, center: c };
}
function ik(A, T, l1, l2, bend) { // two bone, bend = +1/-1 picks side
  let d = sub(T, A), D = len(d);
  D = Math.min(D, l1 + l2 - 1e-4); D = Math.max(D, Math.abs(l1 - l2) + 1e-4);
  const a = Math.acos((l1 * l1 + D * D - l2 * l2) / (2 * l1 * D));
  const base = Math.atan2(d[1], d[0]) + bend * a;
  return add(A, [l1 * Math.cos(base), l1 * Math.sin(base)]);
}
const smooth = (t) => t * t * (3 - 2 * t);

// ---------- shapes ----------
// shape: {s: fill style or null, f: fill points, l: [line polylines], lw: line weight, ly: layer, clip: shape id}
function S(style, fill, lines, o = {}) { return Object.assign({ s: style, f: fill ? rnd(fill) : null, l: (lines || []).map(rnd), lw: 1 }, o); }
function blob(style, P, o = {}) { const c = catmull(P, true, 7); return S(style, c.pts, [[...c.pts, c.pts[0]]], o); }
function blobOpen(style, P, gap, o = {}) { // closed fill, line omits segment gap=[i] (from point i to i+1)
  const c = catmull(P, true, 7); const g = gap; const s0 = c.seg[(g + 1) % P.length], s1 = c.seg[g];
  let line = [];
  if (g + 1 >= P.length) line = c.pts.slice(0, s1 + 1); else line = [...c.pts.slice(s0), ...c.pts.slice(0, s1 + 1)];
  return S(style, c.pts, [line], o);
}
function curve(P, lw = 0.7, o = {}) { return S(null, null, [catmull(P, false, 6).pts], Object.assign({ lw }, o)); }
function oval(style, c, rx, ry, rot = 0, o = {}) { const e = ellipse(c, rx, ry, rot); return S(style, e, o.noLine ? [] : [[...e, e[0]]], o); }

// ======================================================================
// DOG. Native facing: LEFT (toward the door, -x). Origin: ground under mid-torso.
// ======================================================================
const TORSO = { // 10 keypoints, same order for every pose so poses can be blended into breakdown drawings
  stand: [[-0.25, 0.565], [-0.15, 0.535], [0.03, 0.51], [0.20, 0.505], [0.33, 0.455], [0.315, 0.32], [0.11, 0.31], [-0.15, 0.27], [-0.31, 0.37], [-0.325, 0.48]],
  crouch: [[-0.25, 0.47], [-0.14, 0.462], [0.04, 0.458], [0.19, 0.41], [0.30, 0.34], [0.275, 0.22], [0.09, 0.22], [-0.15, 0.20], [-0.31, 0.29], [-0.325, 0.40]],
  low: [[-0.26, 0.50], [-0.15, 0.49], [0.03, 0.50], [0.20, 0.495], [0.33, 0.445], [0.315, 0.31], [0.11, 0.30], [-0.15, 0.25], [-0.31, 0.34], [-0.33, 0.44]],
  lie: [[-0.25, 0.33], [-0.13, 0.315], [0.05, 0.295], [0.21, 0.27], [0.34, 0.19], [0.33, 0.06], [0.10, 0.035], [-0.16, 0.04], [-0.32, 0.16], [-0.335, 0.26]],
};
const ANCH = {
  stand: { sh: [-0.17, 0.42], hip: [0.20, 0.41], neck: [-0.27, 0.50], tail: [0.315, 0.47] },
  crouch: { sh: [-0.17, 0.35], hip: [0.18, 0.32], neck: [-0.27, 0.42], tail: [0.29, 0.37] },
  low: { sh: [-0.17, 0.385], hip: [0.20, 0.40], neck: [-0.28, 0.44], tail: [0.315, 0.46] },
  lie: { sh: [-0.18, 0.17], hip: [0.19, 0.15], neck: [-0.28, 0.27], tail: [0.33, 0.19] },
};
function blendPose(a, b, t) {
  const T = TORSO[a].map((p, i) => lerpP(p, TORSO[b][i], t));
  const A = {}; for (const k in ANCH[a]) A[k] = lerpP(ANCH[a][k], ANCH[b][k], t);
  return { T, A };
}
const STAND_FEET = { nf: [-0.175, 0], ff: [-0.125, 0.014], nh: [0.225, 0], fh: [0.27, 0.014] };

function foreLeg(S0, foot, style, sock) {
  const wr = add(foot, [0.02, 0.07]);
  const el = ik(S0, wr, 0.165, 0.20, -1); // elbow sits behind (+x)
  const t = tube([S0, el, wr, add(foot, [0.005, 0.03])], [0.11, 0.072, 0.05, 0.046], { openStart: true });
  const out = [S(style, t.fill, [t.line])];
  out.push(oval(sock, add(foot, [-0.012, 0.021]), 0.04, 0.022, 0));
  out.push(curve([add(foot, [-0.03, 0.006]), add(foot, [-0.028, 0.018])], 0.5));
  return out;
}
function hindLeg(H, foot, style, sock) {
  const hock = add(foot, [0.04, 0.12]);
  const kn = ik(H, hock, 0.18, 0.19, 1); // stifle forward (-x)
  const t = tube([H, kn, hock, add(foot, [0.01, 0.03])], [0.17, 0.09, 0.055, 0.047], { openStart: true });
  const out = [S(style, t.fill, [t.line])];
  out.push(oval(sock, add(foot, [-0.008, 0.021]), 0.042, 0.022, 0));
  out.push(curve([add(kn, [0.02, 0.04]), add(kn, [0.045, -0.01])], 0.55)); // thigh crease
  return out;
}
function torsoShapes(T, coat) {
  // gap 9 = no line between neckFront and neckTop (the neck joins there)
  const tor = blobOpen(coat, T, 9, { id: 'torso' });
  const saddle = blob('saddle', [lerpP(T[0], T[1], 0.6), T[1], T[2], T[3], lerpP(T[3], T[4], 0.4), add(lerpP(T[3], T[4], 0.3), [0, -0.07]), add(T[2], [0, -0.075]), add(T[1], [0.03, -0.07])], { clip: 'torso', l: [] });
  const bib = blob('white', [add(T[9], [0.0, -0.01]), add(T[8], [-0.02, 0]), add(T[7], [0.03, 0.0]), add(T[7], [0.09, 0.05]), add(T[8], [0.10, 0.04]), add(T[9], [0.07, -0.03])], { clip: 'torso', l: [] });
  const ribs = curve([add(T[7], [0.10, 0.03]), add(T[7], [0.16, 0.07]), add(T[6], [-0.06, 0.08])], 0.5);
  return [tor, saddle, bib, ribs];
}
function sideBody(T, A, feet, opt = {}) {
  const sh = [], coat = 'coat';
  // far legs first (darker style), torso, then near legs
  sh.push(...hindLeg(add(A.hip, [0.03, 0.0]), feet.fh, 'coat_far', 'white_far'));
  sh.push(...foreLeg(add(A.sh, [0.035, 0.0]), feet.ff, 'coat_far', 'white_far'));
  sh.push(...torsoShapes(T, coat));
  sh.push(...hindLeg(A.hip, feet.nh, coat, 'white'));
  sh.push(...foreLeg(A.sh, feet.nf, coat, 'white'));
  return sh;
}
function gaitFeet(phi, stride, lift, crouch) {
  const off = { nh: 0, nf: 0.25, fh: 0.5, ff: 0.75 }, duty = 0.62, o = {};
  for (const k in off) {
    const q = (phi + off[k]) % 1, n = STAND_FEET[k];
    let x, y = n[1];
    if (q < duty) { const u = q / duty; x = n[0] + (u - 0.5) * stride * duty; }
    else { const v = (q - duty) / (1 - duty); x = n[0] + (0.5 - smooth(v)) * stride * duty; y += lift * Math.sin(Math.PI * v); }
    o[k] = [x, y];
  }
  return o;
}
function lieBody(T, A, lift = 0) {
  const sh = [], up = [0, lift];
  // far forepaw (extended, a little behind the near one), far hind hidden
  const ff = tube([add(A.sh, [0.05, -0.04]), add([-0.20, 0.06], up), add([-0.40, 0.035], up)], [0.07, 0.05, 0.042], { openStart: true });
  sh.push(S('coat_far', ff.fill, [ff.line])); sh.push(oval('white_far', add([-0.415, 0.03], up), 0.042, 0.022));
  sh.push(...torsoShapes(T, 'coat'));
  // near haunch and tucked hind foot
  sh.push(oval('coat', add([0.19, 0.14], up), 0.135, 0.105, 0.15, { id: 'haunch' }));
  sh.push(curve([add([0.10, 0.20], up), add([0.17, 0.235], up), add([0.26, 0.22], up)], 0.55));
  const hf = tube([add([0.29, 0.07], up), add([0.17, 0.035], up), add([0.05, 0.028], up)], [0.06, 0.045, 0.04]);
  sh.push(S('coat', hf.fill, [hf.line])); sh.push(oval('white', add([0.035, 0.026], up), 0.045, 0.022));
  // near foreleg folded at the elbow, forearm flat on the ground, paw forward
  const nf = tube([add(A.sh, [0.0, 0.0]), add([-0.17, 0.06], up), add([-0.36, 0.035], up)], [0.09, 0.055, 0.044], { openStart: true });
  sh.push(S('coat', nf.fill, [nf.line])); sh.push(oval('white', add([-0.385, 0.026], up), 0.045, 0.023));
  sh.push(curve([add([-0.41, 0.012], up), add([-0.408, 0.026], up)], 0.5));
  return sh;
}

// --- dog body drawings (side views, generated at their poses) ---
const LIB = { dog_body: {}, dog_head: {}, dog_ear: {}, dog_tail: {}, person: {}, person_mouth: {}, door: {} };
function addBody(id, shapes, A, meta) { LIB.dog_body[id] = Object.assign({ view: 'profile', anchors: { neck: R(A.neck), tail: R(A.tail) }, shapes }, meta); }

{ const T = TORSO.stand, A = ANCH.stand; addBody('stand', sideBody(T, A, STAND_FEET), A, { posture: 'stand' }); }
{ const T = TORSO.crouch, A = ANCH.crouch; const f = { nf: [-0.20, 0], ff: [-0.15, 0.014], nh: [0.19, 0], fh: [0.235, 0.014] }; addBody('crouch', sideBody(T, A, f), A, { posture: 'crouch' }); }
// walk cycles: 16 drawings each, feet planted by construction (stride 0.55 m per cycle)
const STRIDE = 0.55, NWALK = 16;
for (const [set, pose, lift] of [['walk', 'stand', 0.07], ['cwalk', 'crouch', 0.05], ['lwalk', 'low', 0.06]]) {
  for (let i = 0; i < NWALK; i++) {
    const phi = i / NWALK, bob = 0.009 * Math.cos(4 * Math.PI * phi);
    const T = TORSO[pose].map((p) => add(p, [0, bob])), A = {}; for (const k in ANCH[pose]) A[k] = add(ANCH[pose][k], [0, bob]);
    const feet = gaitFeet(phi, STRIDE, lift, pose === 'crouch');
    if (pose === 'crouch') for (const k in feet) feet[k] = add(feet[k], [k.endsWith('h') ? -0.03 : -0.02, 0]);
    addBody(`${set}${String(i).padStart(2, '0')}`, sideBody(T, A, feet), A, { posture: pose === 'crouch' ? 'crouch_walk' : pose === 'low' ? 'low_walk' : 'walk', phase: phi, feet: Object.fromEntries(Object.entries(feet).map(([k, v]) => [k, R(v)])) });
  }
}
// breakdowns between standing and lying (lowering / rising)
{ const { T, A } = blendPose('crouch', 'lie', 0.22); const f = { nf: [-0.27, 0], ff: [-0.22, 0.014], nh: [0.12, 0], fh: [0.16, 0.014] }; addBody('lower1', sideBody(T, A, f), A, { posture: 'lowering' }); }
{ const { T, A } = blendPose('crouch', 'lie', 0.78); addBody('lower2', lieBody(T, A, 0.035), A, { posture: 'lowering' }); }
{ const T = TORSO.lie, A = ANCH.lie; addBody('lie', lieBody(T, A, 0), A, { posture: 'lie' }); }

// --- turn drawings (front, three-quarter front, back, three-quarter back): dedicated drawings, never a squash ---
function legDown(top, foot, W, style, sock) { const t = tube([top, lerpP(top, foot, 0.55), add(foot, [0, 0.03])], W, { openStart: true }); return [S(style, t.fill, [t.line]), oval(sock, add(foot, [0, 0.02]), 0.04, 0.022)]; }
function frontBody(c) { // facing the camera; c lowers it
  const dy = -0.07 * c, sh = [];
  sh.push(...legDown([-0.12, 0.30 + dy], [-0.125, 0.05], [0.07, 0.05, 0.04], 'coat_far', 'white_far'));
  sh.push(...legDown([0.12, 0.30 + dy], [0.125, 0.05], [0.07, 0.05, 0.04], 'coat_far', 'white_far'));
  sh.push(blob('coat', [[-0.15, 0.44 + dy], [0, 0.52 + dy], [0.15, 0.44 + dy], [0.16, 0.36 + dy], [0.09, 0.30 + dy], [-0.09, 0.30 + dy], [-0.16, 0.36 + dy]], { id: 'barrel' }));
  sh.push(blob('saddle', [[-0.13, 0.47 + dy], [0, 0.53 + dy], [0.13, 0.47 + dy], [0.07, 0.45 + dy], [-0.07, 0.45 + dy]], { clip: 'barrel', l: [] }));
  sh.push(blob('coat', [[-0.11, 0.47 + dy], [0, 0.50 + dy], [0.11, 0.47 + dy], [0.12, 0.36 + dy], [0.06, 0.26 + dy], [0, 0.245 + dy], [-0.06, 0.26 + dy], [-0.12, 0.36 + dy]], { id: 'chest' }));
  sh.push(blob('white', [[-0.06, 0.48 + dy], [0, 0.49 + dy], [0.06, 0.48 + dy], [0.07, 0.34 + dy], [0, 0.25 + dy], [-0.07, 0.34 + dy]], { clip: 'chest', l: [] }));
  sh.push(...legDown([-0.07, 0.36 + dy], [-0.075, 0.0], [0.08, 0.055, 0.045], 'coat', 'white'));
  sh.push(...legDown([0.07, 0.36 + dy], [0.075, 0.0], [0.08, 0.055, 0.045], 'coat', 'white'));
  return { shapes: sh, A: { neck: [0, 0.46 + dy], tail: [0.10, 0.50 + dy] } };
}
function q3frontBody(c) { // three-quarter, head toward camera-left
  const dy = -0.07 * c, sh = [];
  sh.push(...legDown([0.17, 0.32 + dy], [0.19, 0.045], [0.10, 0.055, 0.04], 'coat_far', 'white_far'));
  sh.push(...legDown([0.0, 0.32 + dy], [-0.005, 0.04], [0.07, 0.05, 0.04], 'coat_far', 'white_far'));
  sh.push(blobOpen('coat', [[-0.20, 0.50 + dy], [-0.08, 0.535 + dy], [0.10, 0.51 + dy], [0.21, 0.46 + dy], [0.22, 0.35 + dy], [0.12, 0.31 + dy], [-0.05, 0.25 + dy], [-0.19, 0.31 + dy], [-0.215, 0.42 + dy]], 8, { id: 'tq' }));
  sh.push(blob('saddle', [[-0.10, 0.53 + dy], [0.10, 0.515 + dy], [0.21, 0.465 + dy], [0.10, 0.45 + dy], [-0.06, 0.47 + dy]], { clip: 'tq', l: [] }));
  sh.push(blob('white', [[-0.20, 0.45 + dy], [-0.215, 0.38 + dy], [-0.13, 0.27 + dy], [-0.06, 0.29 + dy], [-0.09, 0.40 + dy], [-0.15, 0.47 + dy]], { clip: 'tq', l: [] }));
  sh.push(...legDown([0.12, 0.36 + dy], [0.13, 0.0], [0.13, 0.06, 0.045], 'coat', 'white'));
  sh.push(curve([[0.09, 0.40 + dy], [0.12, 0.43 + dy], [0.17, 0.42 + dy]], 0.5));
  sh.push(...legDown([-0.13, 0.36 + dy], [-0.135, 0.0], [0.085, 0.055, 0.045], 'coat', 'white'));
  return { shapes: sh, A: { neck: [-0.16, 0.47 + dy], tail: [0.21, 0.47 + dy] } };
}
function backBody(c) { // rump toward the camera, head away
  const dy = -0.09 * c, sh = [];
  sh.push(...legDown([-0.10, 0.30 + dy * 0.6], [-0.115, 0.05], [0.06, 0.045, 0.038], 'coat_far', 'white_far'));
  sh.push(...legDown([0.10, 0.30 + dy * 0.6], [0.115, 0.05], [0.06, 0.045, 0.038], 'coat_far', 'white_far'));
  sh.push(blob('coat', [[-0.13, 0.48 + dy * 0.5], [0, 0.54 + dy * 0.5], [0.13, 0.48 + dy * 0.5], [0.12, 0.40], [-0.12, 0.40]], { id: 'back' }));
  sh.push(blob('saddle', [[-0.12, 0.49 + dy * 0.5], [0, 0.545 + dy * 0.5], [0.12, 0.49 + dy * 0.5], [0.05, 0.45 + dy * 0.5], [-0.05, 0.45 + dy * 0.5]], { clip: 'back', l: [] }));
  sh.push(blob('coat', [[-0.16, 0.40 + dy], [-0.09, 0.47 + dy], [0, 0.48 + dy], [0.09, 0.47 + dy], [0.16, 0.40 + dy], [0.15, 0.30 + dy], [0.0, 0.27 + dy], [-0.15, 0.30 + dy]], { id: 'rump' }));
  sh.push(curve([[0, 0.43 + dy], [0, 0.33 + dy], [0.0, 0.28 + dy]], 0.6));
  for (const s of [-1, 1]) {
    const t = tube([[0.085 * s, 0.37 + dy], [0.095 * s, 0.22 + dy * 0.5], [0.085 * s, 0.12], [0.08 * s, 0.03]], [0.13, 0.08, 0.045, 0.04], { openStart: true });
    sh.push(S('coat', t.fill, [t.line])); sh.push(oval('white', [0.08 * s, 0.02], 0.04, 0.022));
  }
  return { shapes: sh, A: { neck: [0, 0.49 + dy * 0.5], tail: [0, 0.455 + dy] } };
}
function q3backBody(c) { // rump toward camera-right, head away-left
  const dy = -0.09 * c, sh = [];
  sh.push(...legDown([-0.17, 0.32 + dy * 0.6], [-0.19, 0.05], [0.065, 0.045, 0.038], 'coat_far', 'white_far'));
  sh.push(...legDown([-0.05, 0.30 + dy * 0.6], [-0.06, 0.045], [0.065, 0.045, 0.038], 'coat_far', 'white_far'));
  sh.push(blob('coat', [[-0.24, 0.50 + dy * 0.5], [-0.14, 0.53 + dy * 0.5], [0.02, 0.50 + dy * 0.7], [0.16, 0.47 + dy], [0.20, 0.37 + dy], [0.15, 0.28 + dy], [0.0, 0.27 + dy], [-0.16, 0.30 + dy * 0.6], [-0.25, 0.40 + dy * 0.5]], { id: 'qb' }));
  sh.push(blob('saddle', [[-0.22, 0.51 + dy * 0.5], [-0.14, 0.535 + dy * 0.5], [0.02, 0.505 + dy * 0.7], [0.12, 0.47 + dy], [0.0, 0.46 + dy * 0.7], [-0.14, 0.48 + dy * 0.5]], { clip: 'qb', l: [] }));
  sh.push(curve([[0.04, 0.44 + dy], [0.03, 0.34 + dy], [0.05, 0.29 + dy]], 0.6));
  const t1 = tube([[0.0, 0.38 + dy], [0.0, 0.22 + dy * 0.5], [0.0, 0.12], [-0.005, 0.03]], [0.12, 0.075, 0.045, 0.04], { openStart: true });
  sh.push(S('coat_far', t1.fill, [t1.line])); sh.push(oval('white_far', [-0.005, 0.02], 0.04, 0.022));
  const t2 = tube([[0.12, 0.38 + dy], [0.135, 0.22 + dy * 0.5], [0.125, 0.11], [0.12, 0.02]], [0.14, 0.085, 0.05, 0.042], { openStart: true });
  sh.push(S('coat', t2.fill, [t2.line])); sh.push(oval('white', [0.115, 0.01], 0.042, 0.022));
  return { shapes: sh, A: { neck: [-0.22, 0.48 + dy * 0.5], tail: [0.15, 0.45 + dy] } };
}
for (const [id, fn, c, view, post] of [['front', frontBody, 0, 'front', 'stand'], ['q3front', q3frontBody, 0, 'q3front', 'stand'], ['back_c', backBody, 0.6, 'back', 'crouch'], ['q3back_c', q3backBody, 0.6, 'q3back', 'crouch']]) {
  const b = fn(c); LIB.dog_body[id] = { view, posture: post, anchors: { neck: rnd([b.A.neck])[0], tail: rnd([b.A.tail])[0] }, shapes: b.shapes };
}

// --- heads. Origin: the head joint (top of the neck). Anchors for the ears. ---
function headProfile(eye) {
  const sh = [];
  sh.push(blob('coat', [[0.03, 0.035], [0.025, 0.10], [-0.025, 0.138], [-0.085, 0.122], [-0.112, 0.092], [-0.152, 0.079], [-0.192, 0.069], [-0.209, 0.047], [-0.197, 0.022], [-0.15, 0.013], [-0.10, -0.004], [-0.04, -0.014]], { id: 'skull' }));
  sh.push(blob('white', [[-0.215, 0.052], [-0.15, 0.052], [-0.105, 0.04], [-0.07, 0.004], [-0.12, -0.025], [-0.225, -0.005]], { clip: 'skull', l: [] }));
  sh.push(blob('saddle', [[0.04, 0.05], [0.035, 0.11], [-0.02, 0.15], [-0.05, 0.13], [-0.02, 0.10], [0.0, 0.05]], { clip: 'skull', l: [] }));
  sh.push(blob('nose', [[-0.186, 0.071], [-0.212, 0.064], [-0.216, 0.045], [-0.199, 0.034], [-0.182, 0.047]], { lw: 0.7 }));
  sh.push(curve([[-0.198, 0.024], [-0.16, 0.017], [-0.125, 0.022]], 0.7));
  sh.push(curve([[-0.098, 0.108], [-0.078, 0.113], [-0.058, 0.105]], 0.75));
  if (eye === 'open') { sh.push(oval('eye', [-0.077, 0.088], 0.0125, 0.0155, 0.2, { lw: 0.6 })); sh.push(oval('eye_hl', [-0.081, 0.094], 0.0042, 0.0042, 0, { noLine: true })); }
  else sh.push(curve([[-0.09, 0.09], [-0.077, 0.083], [-0.063, 0.089]], 0.9));
  sh.push(curve([[0.0, 0.015], [0.012, 0.035], [0.012, 0.055]], 0.45));
  return { shapes: sh, anchors: { ear_near: [-0.02, 0.125], ear_far: [0.005, 0.13] } };
}
function headQ3front(eye) {
  const sh = [];
  sh.push(blob('coat', [[0.045, 0.04], [0.048, 0.10], [0.005, 0.145], [-0.06, 0.138], [-0.098, 0.10], [-0.13, 0.068], [-0.158, 0.046], [-0.152, 0.016], [-0.115, -0.004], [-0.06, -0.018], [0.0, -0.012], [0.035, 0.008]], { id: 'skull' }));
  sh.push(blob('white', [[-0.165, 0.05], [-0.115, 0.07], [-0.085, 0.05], [-0.08, 0.0], [-0.12, -0.03], [-0.17, 0.0]], { clip: 'skull', l: [] }));
  sh.push(blob('white', [[-0.075, 0.13], [-0.06, 0.135], [-0.075, 0.07], [-0.09, 0.075]], { clip: 'skull', l: [] }));
  sh.push(blob('nose', [[-0.14, 0.062], [-0.165, 0.058], [-0.168, 0.04], [-0.148, 0.032], [-0.13, 0.044]], { lw: 0.7 }));
  sh.push(curve([[-0.155, 0.025], [-0.13, 0.012], [-0.10, 0.016]], 0.7));
  if (eye === 'open') {
    sh.push(oval('eye', [-0.035, 0.088], 0.0125, 0.0155, 0.1, { lw: 0.6 })); sh.push(oval('eye_hl', [-0.039, 0.094], 0.004, 0.004, 0, { noLine: true }));
    sh.push(oval('eye', [-0.098, 0.092], 0.0085, 0.013, 0.1, { lw: 0.6 })); sh.push(oval('eye_hl', [-0.1, 0.097], 0.003, 0.003, 0, { noLine: true }));
  } else { sh.push(curve([[-0.047, 0.09], [-0.035, 0.084], [-0.022, 0.09]], 0.9)); sh.push(curve([[-0.105, 0.093], [-0.097, 0.088], [-0.09, 0.093]], 0.8)); }
  sh.push(curve([[-0.05, 0.11], [-0.035, 0.113], [-0.02, 0.107]], 0.7));
  return { shapes: sh, anchors: { ear_near: [0.02, 0.128], ear_far: [-0.065, 0.135] } };
}
function headFront(eye) {
  const sh = [];
  sh.push(blob('coat', [[0.078, 0.05], [0.072, 0.11], [0.036, 0.146], [-0.036, 0.146], [-0.072, 0.11], [-0.078, 0.05], [-0.05, 0.0], [0, -0.016], [0.05, 0.0]], { id: 'skull' }));
  sh.push(blob('white', [[-0.055, 0.03], [-0.012, 0.07], [-0.008, 0.13], [0.008, 0.13], [0.012, 0.07], [0.055, 0.03], [0.03, -0.02], [-0.03, -0.02]], { clip: 'skull', l: [] }));
  sh.push(oval('nose', [0, 0.045], 0.022, 0.015, 0, { lw: 0.7 }));
  sh.push(curve([[0, 0.03], [0, 0.015]], 0.6)); sh.push(curve([[-0.032, 0.012], [0, 0.015], [0.032, 0.012]], 0.7));
  for (const s of [-1, 1]) {
    if (eye === 'open') { sh.push(oval('eye', [0.035 * s, 0.088], 0.012, 0.015, 0, { lw: 0.6 })); sh.push(oval('eye_hl', [0.035 * s - 0.004, 0.094], 0.004, 0.004, 0, { noLine: true })); }
    else sh.push(curve([[0.035 * s - 0.012, 0.09], [0.035 * s, 0.084], [0.035 * s + 0.012, 0.09]], 0.9));
    sh.push(curve([[0.05 * s, 0.108], [0.035 * s, 0.114], [0.02 * s, 0.108]], 0.7));
  }
  return { shapes: sh, anchors: { ear_near: [0.055, 0.128], ear_far: [-0.055, 0.128] } };
}
function headQ3back() {
  const sh = [];
  sh.push(blob('coat', [[0.05, 0.03], [0.062, 0.10], [0.025, 0.145], [-0.04, 0.142], [-0.078, 0.112], [-0.104, 0.09], [-0.13, 0.08], [-0.128, 0.062], [-0.09, 0.035], [-0.05, 0.002], [0.0, -0.012]], { id: 'skull' }));
  sh.push(blob('saddle', [[0.055, 0.04], [0.06, 0.11], [0.02, 0.15], [-0.03, 0.14], [0.0, 0.09], [0.01, 0.04]], { clip: 'skull', l: [] }));
  sh.push(blob('white', [[-0.135, 0.07], [-0.10, 0.085], [-0.085, 0.06], [-0.10, 0.03], [-0.14, 0.04]], { clip: 'skull', l: [] }));
  sh.push(blob('nose', [[-0.122, 0.085], [-0.136, 0.083], [-0.138, 0.07], [-0.126, 0.066]], { lw: 0.6 }));
  sh.push(curve([[-0.085, 0.10], [-0.07, 0.085], [-0.07, 0.06]], 0.55)); // cheek line, the muzzle turning away
  sh.push(curve([[0.0, 0.03], [0.02, 0.07]], 0.45));
  return { shapes: sh, anchors: { ear_near: [0.03, 0.13], ear_far: [-0.045, 0.138] } };
}
function headDeep() { // looking IN: we see the back of the skull and the far cheek; the nose is a sliver, level, going away
  const sh = [];
  sh.push(blob('coat', [[0.055, 0.025], [0.07, 0.09], [0.04, 0.14], [-0.02, 0.15], [-0.07, 0.12], [-0.10, 0.085], [-0.118, 0.06], [-0.11, 0.04], [-0.08, 0.02], [-0.04, -0.005], [0.01, -0.012]], { id: 'skull' }));
  sh.push(blob('saddle', [[0.06, 0.03], [0.072, 0.09], [0.04, 0.145], [-0.02, 0.152], [-0.05, 0.12], [-0.03, 0.06], [0.0, 0.02]], { clip: 'skull', l: [] }));
  sh.push(blob('white', [[-0.125, 0.06], [-0.095, 0.072], [-0.08, 0.05], [-0.09, 0.025], [-0.125, 0.035]], { clip: 'skull', l: [] }));
  sh.push(blob('nose', [[-0.111, 0.062], [-0.124, 0.06], [-0.125, 0.049], [-0.113, 0.046]], { lw: 0.6 }));
  sh.push(curve([[-0.06, 0.115], [-0.045, 0.085], [-0.05, 0.045]], 0.6));
  sh.push(curve([[0.02, 0.02], [0.035, 0.06]], 0.45));
  return { shapes: sh, anchors: { ear_near: [0.035, 0.135], ear_far: [-0.04, 0.143] } };
}
function headBack() {
  const sh = [];
  sh.push(blob('coat', [[0.064, 0.04], [0.066, 0.10], [0.032, 0.142], [-0.032, 0.142], [-0.066, 0.10], [-0.064, 0.04], [0, -0.004]], { id: 'skull' }));
  sh.push(blob('saddle', [[0.0, 0.0], [0.04, 0.06], [0.03, 0.14], [-0.03, 0.14], [-0.04, 0.06]], { clip: 'skull', l: [] }));
  sh.push(curve([[0, 0.02], [0, 0.07]], 0.45));
  return { shapes: sh, anchors: { ear_near: [0.05, 0.13], ear_far: [-0.05, 0.13] } };
}
const HEADS = { profile: headProfile, q3front: headQ3front, front: headFront };
for (const v in HEADS) for (const e of ['open', 'closed']) { const h = HEADS[v](e); LIB.dog_head[`${v}_${e}`] = { view: v, eye: e, anchors: h.anchors, shapes: h.shapes }; }
{ const h = headQ3back(); LIB.dog_head['q3back'] = { view: 'q3back', eye: 'hidden', anchors: h.anchors, shapes: h.shapes }; }
{ const h = headDeep(); LIB.dog_head['deep'] = { view: 'deep', eye: 'hidden', anchors: h.anchors, shapes: h.shapes }; }
{ const h = headBack(); LIB.dog_head['back'] = { view: 'back', eye: 'hidden', anchors: h.anchors, shapes: h.shapes }; }

// --- ears: one drawing per (view, state); far ear on the UNDER layer, near ear on the OVER layer ---
function earShape(base, dirDeg, L0, wb, style, layer, fold = 0, inner = false) {
  const L = L0 * 0.88; const d = ang(dirDeg), n = [-d[1], d[0]];
  const tip = add(base, mul(d, L));
  const tipF = fold ? add(add(base, mul(d, L * 0.62)), mul(ang(dirDeg + 100 * Math.sign(fold)), L * 0.42 * Math.abs(fold))) : tip;
  const P = [add(base, mul(n, wb / 2)), add(add(base, mul(d, L * 0.55)), mul(n, wb * 0.42)), tipF, add(add(base, mul(d, L * 0.55)), mul(n, -wb * 0.3)), add(base, mul(n, -wb / 2))];
  const out = [blob(style, P, { ly: layer, id: `ear_${layer}` })];
  if (inner) out.push(blob('ear_inner', [add(base, mul(n, wb * 0.2)), add(add(base, mul(d, L * 0.5)), mul(n, wb * 0.15)), add(base, mul(d, L * 0.75)), add(add(base, mul(d, L * 0.5)), mul(n, -wb * 0.1)), add(base, mul(n, -wb * 0.15))], { ly: layer, clip: `ear_${layer}`, l: [] }));
  return out;
}
const EAR_DEF = { // [dir far, dir near, length, fold] per state, for a left-facing head (+x = back of head)
  profile: { pricked: [[88, 82], 0.088, 0], half: [[70, 66], 0.085, 0.8], flat: [[18, 14], 0.08, 0] },
  q3front: { pricked: [[100, 78], 0.085, 0], half: [[115, 62], 0.082, 0.7], flat: [[150, 22], 0.075, 0] },
  front: { pricked: [[100, 80], 0.085, 0], half: [[125, 55], 0.08, 0.7], flat: [[165, 15], 0.072, 0] },
  q3back: { pricked: [[95, 80], 0.085, 0], half: [[110, 65], 0.082, 0.7], flat: [[160, 25], 0.075, 0] },
  back: { pricked: [[100, 80], 0.085, 0], half: [[120, 60], 0.08, 0.7], flat: [[165, 15], 0.072, 0] },
  deep: { pricked: [[105, 75], 0.08, 0], half: [[120, 60], 0.076, 0.7], flat: [[160, 20], 0.07, 0] },
};
for (const v in EAR_DEF) {
  const h = (v === 'q3back' ? headQ3back() : v === 'back' ? headBack() : v === 'deep' ? headDeep() : HEADS[v]('open'));
  for (const st in EAR_DEF[v]) {
    const [[df, dn], L, fold] = EAR_DEF[v][st];
    const sym = v === 'front' || v === 'back';
    const sh = [];
    const showInner = (v === 'front' || v === 'q3front');
    if (v === 'profile') {
      sh.push(...earShape(h.anchors.ear_far, df, L * 0.9, 0.05, 'ear_far', 'under', fold ? -fold : 0));
      sh.push(...earShape(h.anchors.ear_near, dn, L, 0.055, 'ear', 'over', fold ? -fold : 0));
    } else {
      // far ear on screen-left (-x), near ear on screen-right; for symmetric views both on the over layer
      sh.push(...earShape(h.anchors.ear_far, df, L * (sym ? 1 : 0.9), 0.05, sym ? 'ear' : 'ear_far', sym ? 'over' : 'under', fold, showInner && sym));
      sh.push(...earShape(h.anchors.ear_near, dn, L, 0.055, 'ear', 'over', fold ? -fold : 0, showInner));
    }
    LIB.dog_ear[`${v}_${st}`] = { view: v, state: st, shapes: sh };
  }
}

// --- tails: rest chains (a deformation chain bends them per frame); white tip ---
function tailDrawing(angles, Ltot = 0.33) {
  const n = angles.length; const segL = Ltot / n; const chain = [[0, 0]]; let a = 0, p = [0, 0];
  for (let i = 0; i < n; i++) { a = angles[i]; p = add(p, mul(ang(a), segL)); chain.push(p); }
  const W = chain.map((_, i) => lerp(0.055, 0.014, i / n));
  const t = tube(chain, W, { openStart: true });
  const sh = [S('coat', t.fill, [t.line], { id: 'tail' })];
  const tipC = catmull(chain, false, 6).pts; const k = Math.floor(tipC.length * 0.78);
  const tp = tipC[k]; sh.push(oval('white', tp, 0.05, 0.05, 0, { clip: 'tail', l: [] }));
  // the white tip is clipped to the tail; keep only the far part
  sh[1].f = rnd(ellipse(chain[n], 0.07, 0.07)); sh[1].clip = 'tail';
  return { shapes: sh, chain: rnd(chain) };
}
const TAILS = { high: [40, 52, 62, 70, 76, 80], mid: [25, 20, 10, 0, -10, -15], low: [-40, -55, -65, -70, -72, -70], tucked: [-75, -95, -115, -135, -150, -160], lie: [-55, -35, -12, 0, 5, 8], up_back: [95, 100, 100, 95, 90, 85], tucked_back: [-90, -92, -95, -95, -92, -90] };
for (const k in TAILS) { const d = tailDrawing(TAILS[k], k.endsWith('back') ? 0.22 : 0.33); LIB.dog_tail[k] = { state: k, chain: d.chain, shapes: d.shapes }; }

// ======================================================================
// PERSON. Native facing RIGHT (+x, toward the porch). Origin: ground between the feet.
// ======================================================================
function personDrawing(P) {
  // P: joints {pelvis, chest, neck, head, shN, elN, haN, shF, elF, haF, hipN, knN, anN, toN, hipF, knF, anF, toF}, lean
  const sh = [];
  const limb = (pts, W, style, o = {}) => { const t = tube(pts, W, { openStart: true }); return S(style, t.fill, [t.line], o); };
  // far leg, far arm
  sh.push(limb([P.hipF, P.knF, P.anF], [0.15, 0.12, 0.10], 'trousers_far'));
  sh.push(blob('shoe_far', [add(P.anF, [-0.05, 0.03]), add(P.anF, [0.03, 0.035]), add(P.toF, [0.0, 0.03]), add(P.toF, [0.01, 0.0]), add(P.anF, [-0.06, 0.0])]));
  sh.push(limb([P.shF, P.elF, P.haF], [0.10, 0.085, 0.07], 'cardigan_far'));
  sh.push(oval('skin_far', P.haF, 0.045, 0.04, 0));
  // near leg
  sh.push(limb([P.hipN, P.knN, P.anN], [0.16, 0.125, 0.10], 'trousers'));
  sh.push(blob('shoe', [add(P.anN, [-0.05, 0.03]), add(P.anN, [0.03, 0.035]), add(P.toN, [0.0, 0.03]), add(P.toN, [0.01, 0.0]), add(P.anN, [-0.06, 0.0])]));
  // torso: cardigan
  const up = nrm(sub(P.neck, P.pelvis)), side = [up[1], -up[0]];
  const tor = [add(P.neck, mul(side, -0.07)), add(P.neck, mul(side, 0.07)), add(P.chest, mul(side, 0.15)), add(P.pelvis, add(mul(side, 0.15), mul(up, -0.08))), add(P.pelvis, add(mul(side, -0.15), mul(up, -0.08))), add(P.chest, mul(side, -0.15))];
  sh.push(blob('cardigan', tor, { id: 'tor' }));
  sh.push(blob('shirt', [add(P.neck, mul(side, -0.035)), add(P.neck, mul(side, 0.06)), add(lerpP(P.neck, P.chest, 0.6), mul(side, 0.08)), add(lerpP(P.neck, P.chest, 0.7), mul(side, 0.05))], { clip: 'tor', l: [] }));
  sh.push(curve([add(lerpP(P.neck, P.chest, 0.6), mul(side, 0.075)), add(P.pelvis, add(mul(side, 0.12), mul(up, -0.05)))], 0.6));
  // head (profile, facing right): skull + face, ear, hair
  const H = P.head, tilt = P.headTilt || 0, rot = (p) => { const c = Math.cos(tilt), s = Math.sin(tilt); return add(H, [p[0] * c - p[1] * s, p[0] * s + p[1] * c]); };
  const hp = (pts) => pts.map(rot);
  sh.push(limb([add(P.neck, [0, -0.02]), add(H, [-0.01, -0.06])], [0.075, 0.07], 'skin'));
  sh.push(blob('skin', hp([[-0.085, 0.0], [-0.07, 0.075], [0.0, 0.105], [0.07, 0.07], [0.085, 0.02], [0.105, -0.005], [0.085, -0.02], [0.085, -0.05], [0.07, -0.09], [0.02, -0.105], [-0.04, -0.08]]), { id: 'face' }));
  sh.push(blob('hair', hp([[-0.10, -0.02], [-0.095, 0.07], [-0.02, 0.12], [0.06, 0.105], [0.085, 0.06], [0.04, 0.07], [-0.01, 0.045], [-0.03, -0.01], [-0.07, -0.06]]), {}));
  sh.push(oval('hair', rot([-0.11, 0.035]), 0.035, 0.035, 0));
  sh.push(oval('skin_shade', rot([-0.02, 0.0]), 0.022, 0.03, 0));
  sh.push(curve(hp([[0.03, 0.035], [0.045, 0.042], [0.06, 0.04]]), 0.7));
  sh.push(oval('eye', rot([0.045, 0.02]), 0.008, 0.01, 0, { lw: 0.5 }));
  sh.push(curve(hp([[0.07, -0.085], [0.04, -0.1]]), 0.5));
  // near arm on top
  sh.push(limb([P.shN, P.elN, P.haN], [0.105, 0.09, 0.072], 'cardigan'));
  sh.push(blob('skin', [add(P.haN, [-0.04, 0.03]), add(P.haN, [0.04, 0.035]), add(P.haN, mul(nrm(sub(P.haN, P.elN)), 0.075)), add(P.haN, [0.03, -0.035]), add(P.haN, [-0.04, -0.03])]));
  return { shapes: sh, anchors: { mouth: R(rot([0.085, -0.045])), hand: R(P.haN) }, tilt };
}
function personPose(o) {
  // o: lean (rad, forward = +x), sit (0..1), arm (near: 'down'|'mouth'|'reach'|'low'), step (-1..1)
  const lean = o.lean || 0, sit = o.sit || 0;
  const pelvis = [0.0 - 0.05 * sit, lerp(0.93, 0.50, sit)];
  const up = [Math.sin(lean), Math.cos(lean)];
  const chest = add(pelvis, mul(up, 0.36)), neck = add(pelvis, mul(up, 0.52)), head = add(pelvis, mul(up, 0.66));
  const shN = add(pelvis, mul(up, 0.48)), shF = add(shN, [-0.02, 0.0]);
  let elN, haN, elF, haF;
  const down = (sh, dx) => { const el = add(sh, [0.02 + dx, -0.28]); return [el, add(el, [0.05 + dx, -0.26])]; };
  if (o.arm === 'mouth') { elN = add(shN, [0.14, -0.16]); haN = add(head, [0.10, -0.06]); }
  else if (o.arm === 'reach') { elN = add(shN, [0.25, -0.12]); haN = add(shN, [0.52, -0.22]); }
  else if (o.arm === 'low') { elN = add(shN, [0.20, -0.20]); haN = add(shN, [0.45, -0.40]); }
  else if (o.arm === 'knee') { elN = add(shN, [0.10, -0.25]); haN = add(pelvis, [0.32, 0.05]); }
  else[elN, haN] = down(shN, 0);
  if (o.armF === 'knee') { elF = add(shF, [0.08, -0.25]); haF = add(pelvis, [0.28, 0.03]); }
  else if (o.armF === 'back') { elF = add(shF, [-0.12, -0.22]); haF = add(shF, [-0.16, -0.48]); }
  else[elF, haF] = down(shF, -0.02);
  const hipN = add(pelvis, [0.02, 0]), hipF = add(pelvis, [-0.02, 0]);
  let knN, anN, knF, anF;
  if (sit > 0.5) { knN = add(pelvis, [0.42, 0.02]); anN = [0.40, 0.08]; knF = add(pelvis, [0.38, 0.02]); anF = [0.34, 0.09]; }
  else if (sit > 0) { knN = add(pelvis, [0.28, -0.25]); anN = [0.28, 0.08]; knF = add(pelvis, [0.24, -0.25]); anF = [0.20, 0.09]; }
  else {
    const st = o.step || 0;
    anN = [0.08 + 0.16 * st, 0.08]; anF = [-0.06 - 0.16 * st, 0.09];
    knN = ik(hipN, anN, 0.44, 0.44, 1); knF = ik(hipF, anF, 0.44, 0.44, 1);
  }
  const toN = add(anN, [0.17, -0.08]), toF = add(anF, [0.16, -0.08]);
  return personDrawing({ pelvis, chest, neck, head, shN, elN, haN, shF, elF, haF, hipN, knN, anN, toN, hipF, knF, anF, toF, headTilt: o.tilt || 0 });
}
const PERSON_POSES = {
  stand: { arm: 'down' }, call: { lean: 0.06, arm: 'mouth', tilt: 0.06 }, reach1: { lean: 0.12, arm: 'reach', step: 0.4, tilt: -0.05 }, reach2: { lean: 0.2, arm: 'reach', step: 0.8, armF: 'back', tilt: -0.1 },
  step1: { lean: -0.04, step: -0.6, arm: 'down' }, step2: { lean: -0.02, step: 0.5, arm: 'down' }, sitdown: { sit: 0.4, lean: 0.25, arm: 'knee', armF: 'knee' },
  sit: { sit: 1, lean: 0.12, arm: 'knee', armF: 'knee' }, sit_low1: { sit: 1, lean: 0.28, arm: 'knee', armF: 'knee', tilt: -0.05 }, sit_low: { sit: 1, lean: 0.38, arm: 'low', armF: 'knee', tilt: -0.12 },
};
for (const k in PERSON_POSES) { const d = personPose(PERSON_POSES[k]); LIB.person[k] = { pose: k, anchors: d.anchors, shapes: d.shapes }; }
// mouths (in the person's head frame, placed at the mouth anchor)
LIB.person_mouth = {
  closed: { shapes: [curve([[-0.012, 0.004], [0.006, 0.0]], 0.8)] },
  open: { shapes: [blob('mouth', [[-0.014, 0.008], [0.008, 0.01], [0.012, -0.012], [-0.006, -0.02]], { lw: 0.6 })] },
  wide: { shapes: [blob('mouth', [[-0.016, 0.012], [0.01, 0.014], [0.016, -0.02], [-0.008, -0.03]], { lw: 0.6 })] },
  soft: { shapes: [oval('mouth', [0.0, -0.004], 0.008, 0.007, 0, { lw: 0.6 })] },
};
// door panel: drawn flat (its own frame: hinge at x=0, panel toward -x), a peg foreshortens it by the swing angle
LIB.door.panel = { shapes: [
  S('door', [[0, 0], [-0.92, 0], [-0.92, 2.05], [0, 2.05]], [[[0, 0], [-0.92, 0], [-0.92, 2.05], [0, 2.05], [0, 0]]], { id: 'door' }),
  S('door_dark', [[-0.12, 1.15], [-0.80, 1.15], [-0.80, 1.85], [-0.12, 1.85]], [[[-0.12, 1.15], [-0.80, 1.15], [-0.80, 1.85], [-0.12, 1.85], [-0.12, 1.15]]], { lw: 0.6 }),
  S('door_dark', [[-0.12, 0.15], [-0.80, 0.15], [-0.80, 0.95], [-0.12, 0.95]], [[[-0.12, 0.15], [-0.80, 0.15], [-0.80, 0.95], [-0.12, 0.95], [-0.12, 0.15]]], { lw: 0.6 }),
  oval('brass', [-0.82, 1.02], 0.03, 0.03),
] };

// ---------- palette: named colour styles in two lighting palettes ----------
const BASE = {
  ink: '#2a1710', coat: '#c98c4e', coat_far: '#a8703d', saddle: '#7a4a28', white: '#f1e6d2', white_far: '#d3c3a9', nose: '#2b1c17', eye: '#24150f', eye_hl: '#fffaf0',
  ear: '#6e4224', ear_far: '#5a361d', ear_inner: '#b9776a',
  skin: '#e2b08c', skin_far: '#c79474', skin_shade: '#cf9676', hair: '#8d8a86', cardigan: '#8a6a2f', cardigan_far: '#6e5323', shirt: '#e8e1cf', trousers: '#3d4658', trousers_far: '#2f3646', shoe: '#3a2a20', shoe_far: '#2c2018', mouth: '#5a2622',
  door: '#7d5a3c', door_dark: '#6a4a30', brass: '#d8b45a',
};
function hex2rgb(h) { return [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)); }
function rgb2hex(c) { return '#' + c.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join(''); }
function grade(h, m, add_) { const c = hex2rgb(h); return rgb2hex(c.map((v, i) => v * m[i] + add_[i])); }
const PALETTE = { about: 'Named colour styles. The renderer mixes the DUSK palette (cool, outdoor, under the moon) and the LAMP palette (warm, the light from the door) per element by the light node\'s amount at that element.', styles: Object.keys(BASE), palettes: { base: BASE, dusk: {}, lamp: {} } };
for (const k in BASE) {
  PALETTE.palettes.dusk[k] = k === 'ink' ? '#1b1420' : grade(BASE[k], [0.78, 0.74, 0.86], [8, 8, 22]);
  PALETTE.palettes.lamp[k] = k === 'ink' ? '#2a1408' : grade(BASE[k], [1.06, 0.95, 0.78], [10, 4, 0]);
}
PALETTE.passes = { tone_dusk: '#3c3f74', tone_lamp: '#7a4628', highlight_dusk: '#b9c6ff', highlight_lamp: '#ffd79a' };

// ---------- write ----------
fs.mkdirSync(OUT, { recursive: true });
const count = Object.fromEntries(Object.entries(LIB).map(([k, v]) => [k, Object.keys(v).length]));
fs.writeFileSync(path.join(OUT, 'library.json'), JSON.stringify({ about: 'SCION 20 drawing library: every drawing in metres, y up, built in build/01_library.js. Elements are columns of the exposure sheet; drawings are substituted whole, never cross-dissolved.', units: 'metres', counts: count, stride_m: STRIDE, walk_drawings_per_cycle: NWALK, elements: LIB }));
fs.writeFileSync(path.join(OUT, 'palette.json'), JSON.stringify(PALETTE, null, 1));
console.log('library', JSON.stringify(count), 'total', Object.values(count).reduce((a, b) => a + b, 0));
