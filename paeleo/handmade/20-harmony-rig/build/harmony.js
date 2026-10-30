// SCION 20 · the node evaluator (runs in Chromium canvas). Loaded by render.html.
// Nodes implemented here: Peg (affine), Element (drawing column read through the xsheet), CurveDeformer, ChainDeformer,
// Composite, Tone, Highlight, Outline (matte dilation = the heavier outer line), CastShadow, Light (palette mix + spill),
// Background (painted once), Grade, Text, Write. The graph's wiring is in scene/nodegraph.json; the order of evaluation
// below follows it (see renderScene).
'use strict';
const W = 1280, H = 720;
const H$ = {};
H$.mk = (w = W, h = H) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
// affine: [a,b,c,d,e,f] maps (x,y) -> (a x + c y + e, b x + d y + f)
H$.mul = (m, n) => [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1], m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3], m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]];
H$.T = (x, y) => [1, 0, 0, 1, x, y];
H$.S = (sx, sy) => [sx, 0, 0, sy, 0, 0];
H$.Rot = (a) => [Math.cos(a), Math.sin(a), -Math.sin(a), Math.cos(a), 0, 0];
H$.ap = (m, p) => [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]];
H$.hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
H$.mix = (a, b, t) => { const A = H$.hex(a), B = H$.hex(b); return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`; };

// --- deformers: act on drawing-local points before the peg ---
// ChainDeformer: rest chain + per-joint added rotation (radians), FK
H$.chainDeformer = (chain, rots) => {
  const n = chain.length - 1, segs = [];
  for (let j = 0; j < n; j++) { const d = [chain[j + 1][0] - chain[j][0], chain[j + 1][1] - chain[j][1]], L = Math.hypot(d[0], d[1]); segs.push({ a: chain[j], d: [d[0] / L, d[1] / L], L }); }
  const def = []; let p = chain[0], acc = 0;
  for (let j = 0; j < n; j++) { acc += rots[j] || 0; const c = Math.cos(acc), s = Math.sin(acc), d = segs[j].d; const dd = [d[0] * c - d[1] * s, d[0] * s + d[1] * c]; def.push({ a: p, d: dd }); p = [p[0] + dd[0] * segs[j].L, p[1] + dd[1] * segs[j].L]; }
  return (q) => {
    let best = 0, bd = 1e9, bu = 0, bv = 0;
    for (let j = 0; j < n; j++) { const s = segs[j]; const r = [q[0] - s.a[0], q[1] - s.a[1]]; let u = r[0] * s.d[0] + r[1] * s.d[1]; const v = -r[0] * s.d[1] + r[1] * s.d[0]; const uc = Math.max(0, Math.min(s.L, u)); const dist = Math.hypot(u - uc, v); if (dist < bd - 1e-9) { bd = dist; best = j; bu = u; bv = v; } }
    const D = def[best]; return [D.a[0] + D.d[0] * bu - D.d[1] * bv, D.a[1] + D.d[1] * bu + D.d[0] * bv];
  };
};
// CurveDeformer: rest drawing along +y from (0,0) to (0,L); mapped onto a cubic bezier P0..P3
H$.curveDeformer = (L, P) => {
  const bz = (t) => { const u = 1 - t; return [u * u * u * P[0][0] + 3 * u * u * t * P[1][0] + 3 * u * t * t * P[2][0] + t * t * t * P[3][0], u * u * u * P[0][1] + 3 * u * u * t * P[1][1] + 3 * u * t * t * P[2][1] + t * t * t * P[3][1]]; };
  const tan = (t) => { const a = bz(Math.max(0, t - 0.01)), b = bz(Math.min(1, t + 0.01)); const d = [b[0] - a[0], b[1] - a[1]], l = Math.hypot(d[0], d[1]) || 1; return [d[0] / l, d[1] / l]; };
  return (q) => { const t = Math.max(0, Math.min(1, q[1] / L)), extra = q[1] - t * L; const p = bz(t), d = tan(t); const n = [d[1], -d[0]]; return [p[0] + n[0] * q[0] + d[0] * extra, p[1] + n[1] * q[0] + d[1] * extra]; };
};

// --- element rendering: one drawing through a peg, with Outline, Tone and Highlight nodes ---
const _matte = H$.mk(), _tmp = H$.mk(), _el = H$.mk();
H$.pathOf = (ctx, pts, M, def, close) => {
  ctx.beginPath();
  for (let i = 0; i < pts.length; i++) { const p = H$.ap(M, def ? def(pts[i]) : pts[i]); if (i) ctx.lineTo(p[0], p[1]); else ctx.moveTo(p[0], p[1]); }
  if (close) ctx.closePath();
};
H$.drawShapes = (ctx, dr, M, def, pal, o) => {
  const ids = {};
  for (const sh of dr.shapes) { if (sh.id) ids[sh.id] = sh; }
  const lw0 = o.lw || 1.9;
  for (const sh of dr.shapes) {
    if (o.layer && (sh.ly || 'main') !== o.layer) continue;
    if (sh.f && sh.s) {
      ctx.save();
      if (sh.clip && ids[sh.clip]) { H$.pathOf(ctx, ids[sh.clip].f, M, def, true); ctx.clip(); }
      H$.pathOf(ctx, sh.f, M, def, true);
      ctx.fillStyle = o.matte ? '#000' : pal(sh.s); ctx.fill();
      ctx.restore();
    }
    if (!o.matte && sh.l && sh.l.length) {
      ctx.strokeStyle = pal('ink'); ctx.lineWidth = lw0 * (sh.lw || 1); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      for (const L of sh.l) { H$.pathOf(ctx, L, M, def, false); ctx.stroke(); }
    }
  }
};
// parts: [{dr, M, def, layer}] rendered as ONE element node into target, with passes; returns nothing, accumulates matte into accum
H$.element = (target, parts, pal, light, o = {}) => {
  const m = _matte.getContext('2d'), e = _el.getContext('2d'), t = _tmp.getContext('2d');
  m.setTransform(1, 0, 0, 1, 0, 0); m.clearRect(0, 0, W, H);
  for (const p of parts) H$.drawShapes(m, p.dr, p.M, p.def, pal, { matte: true, layer: p.layer });
  e.setTransform(1, 0, 0, 1, 0, 0); e.clearRect(0, 0, W, H); e.globalCompositeOperation = 'source-over'; e.globalAlpha = 1;
  // Outline node: dilate the matte by ~1.3 px in ink (heavier silhouette line, lighter inner lines)
  const ow = o.outline == null ? 1.3 : o.outline;
  if (ow > 0) {
    for (let k = 0; k < 8; k++) { const a = k / 8 * 2 * Math.PI; e.drawImage(_matte, Math.cos(a) * ow, Math.sin(a) * ow); }
    e.globalCompositeOperation = 'source-in'; e.fillStyle = pal('ink'); e.fillRect(0, 0, W, H); e.globalCompositeOperation = 'source-over';
  }
  for (const p of parts) H$.drawShapes(e, p.dr, p.M, p.def, pal, { layer: p.layer, lw: o.lw });
  if (light && light.tone > 0) { // Tone node: matte minus matte shifted toward the light -> the side away from it
    t.setTransform(1, 0, 0, 1, 0, 0); t.globalCompositeOperation = 'source-over'; t.clearRect(0, 0, W, H);
    t.drawImage(_matte, 0, 0); t.globalCompositeOperation = 'destination-out';
    const d = light.toneD || 8; t.drawImage(_matte, light.L[0] * d, light.L[1] * d);
    t.globalCompositeOperation = 'source-in'; t.fillStyle = light.toneColor; t.fillRect(0, 0, W, H);
    e.globalCompositeOperation = 'multiply'; e.globalAlpha = light.tone; e.drawImage(_tmp, 0, 0); e.globalAlpha = 1; e.globalCompositeOperation = 'source-over';
  }
  if (light && light.hl > 0) { // Highlight node: a band 2..(2+w) px inside the lit edge
    t.setTransform(1, 0, 0, 1, 0, 0); t.globalCompositeOperation = 'source-over'; t.clearRect(0, 0, W, H);
    t.drawImage(_matte, -light.L[0] * 2.2, -light.L[1] * 2.2); t.globalCompositeOperation = 'destination-out';
    const w = light.hlW || 4.5; t.drawImage(_matte, -light.L[0] * (2.2 + w), -light.L[1] * (2.2 + w));
    t.globalCompositeOperation = 'destination-in'; t.drawImage(_matte, 0, 0);
    t.globalCompositeOperation = 'source-in'; t.fillStyle = light.hlColor; t.fillRect(0, 0, W, H);
    e.globalCompositeOperation = 'screen'; e.globalAlpha = light.hl; e.drawImage(_tmp, 0, 0); e.globalAlpha = 1; e.globalCompositeOperation = 'source-over';
  }
  target.drawImage(_el, 0, 0);
  if (o.accum) o.accum.getContext('2d').drawImage(_matte, 0, 0);
};
window.H$ = H$;
