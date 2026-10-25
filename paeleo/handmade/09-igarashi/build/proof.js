// Proof images for the method (not the film): node build/proof.js → proof/*.png, proof/proof.json
//  1. mesh_and_handles.png   every source drawing with its triangle mesh, its handles (yellow) and feature-protect masks (cyan)
//  2. arap_vs_skinning.png   the film's most extreme poses solved two ways on the same mesh and the same handle targets:
//                            ARAP (this film) and weighted linear-blend skinning (inverse-distance weights, each handle given
//                            the rotation ARAP found for it, so the comparison is not against a straw man)
//  3. feature_protect.png    the head under a hard pose with and without the feature-protect weights on eye, nose and tag
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const HERE = __dirname, ROOT = path.join(HERE, '..'), OUT = path.join(ROOT, 'proof');
fs.mkdirSync(OUT, { recursive: true });
const ARAP = require('./arap.js'), RIG = require('./rig.js');
const SCORE = JSON.parse(fs.readFileSync(path.join(ROOT, '..', 'score', 'threshold-score.json'), 'utf8'));
const MESH = {};
for (const f of fs.readdirSync(path.join(ROOT, 'assets', 'mesh'))) MESH[f.replace('.json', '')] = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets', 'mesh', f), 'utf8'));
const rig = RIG.Rig(SCORE, MESH);

function handlesFor(piece) {
  const m = MESH[piece.mesh], hs = [];
  for (const [name, at] of Object.entries(piece.handles)) {
    if (!m.handles[name] || typeof at === 'string') continue;
    hs.push({ name, verts: m.handles[name], at: at.slice() });
  }
  return hs;
}
function stats(sol, X) { return sol.diagnose(X); }
function diagLBS(mesh, X) { // inversions and feature distortion for a skinned result, measured the same way
  const s = new ARAP.Solver(mesh); s.solve([{ verts: [0], at: [mesh.verts[0][0], mesh.verts[0][1]] }], Float64Array.from(X), 1); // fills R
  // recompute local rotations for X without moving it
  const Y = Float64Array.from(X); const nt = s.T.length / 3;
  for (let t = 0; t < nt; t++) { let m00 = 0, m01 = 0, m10 = 0, m11 = 0; for (let k = 0; k < 3; k++) { const i = s.T[3 * t + (k + 1) % 3], j = s.T[3 * t + (k + 2) % 3], c = s.C[3 * t + k]; const ex = s.P[2 * i] - s.P[2 * j], ey = s.P[2 * i + 1] - s.P[2 * j + 1], fx = Y[2 * i] - Y[2 * j], fy = Y[2 * i + 1] - Y[2 * j + 1]; m00 += c * ex * fx; m01 += c * ex * fy; m10 += c * ey * fx; m11 += c * ey * fy; } const th = Math.atan2(m01 - m10, m00 + m11); s.R[2 * t] = Math.cos(th); s.R[2 * t + 1] = Math.sin(th); }
  return s.diagnose(Y);
}
const cases = [
  { label: 'coming, head low (19.0 s)', t: 19.0 },
  { label: 'crouching onto the sill (24.08 s)', t: 24.08 },
  { label: 'backing away, cowering (1.8 s)', t: 1.8 },
  { label: 'the back view swinging round (3.67 s)', t: 3.67 },
];
const results = [];
for (const c of cases) {
  const i = Math.round(c.t * 24), d = rig.dog(i), body = d.pieces[0], mesh = MESH[body.mesh];
  const sol = new ARAP.Solver(mesh), hs = handlesFor(body);
  const X = sol.initFrom(hs); sol.solve(hs, X, 60);
  const da = stats(sol, X);
  // per-handle rotation from the ARAP result, handed to skinning
  for (const h of hs) { let cx = 0, cy = 0, rx = 0, ry = 0; for (const v of h.verts) { cx += X[2 * v]; cy += X[2 * v + 1]; rx += mesh.verts[v][0]; ry += mesh.verts[v][1]; } cx /= h.verts.length; cy /= h.verts.length; rx /= h.verts.length; ry /= h.verts.length; let a = 0, b = 0; for (const v of h.verts) { const ex = mesh.verts[v][0] - rx, ey = mesh.verts[v][1] - ry, fx = X[2 * v] - cx, fy = X[2 * v + 1] - cy; a += ex * fx + ey * fy; b += ex * fy - ey * fx; } h.ang = h.verts.length > 1 ? Math.atan2(b, a) : 0; }
  const Ls = ARAP.skin(mesh, hs, X);
  const dl = diagLBS(mesh, Ls);
  results.push({ label: c.label, t: c.t, mesh: body.mesh, arap: da, skinning: dl, X: Array.from(X), L: Array.from(Ls), handles: hs.map(h => h.at) });
}
// feature protection: the side head with the muzzle pushed back and up and the ear pulled down hard
const fp = {};
{
  const m = MESH.head_side, hp = m.handle_points;
  const H = [{ name: 'muzzle', at: [hp.muzzle[0] + 34, hp.muzzle[1] - 30] }, { name: 'skull', at: [hp.skull[0] - 6, hp.skull[1] + 10] }, { name: 'neck', at: hp.neck.slice() }, { name: 'ear_tip', at: [hp.ear_tip[0] + 40, hp.ear_tip[1] + 50] }, { name: 'ear_base', at: hp.ear_base.slice() }]
    .map(h => ({ ...h, verts: m.handles[h.name] }));
  for (const mode of ['protected', 'unprotected']) {
    const mm = mode === 'protected' ? m : Object.assign({}, m, { weight: m.weight.map(() => 1) });
    const s = new ARAP.Solver(mm), hs = H.map(h => ({ ...h, at: h.at.slice() }));
    const X = s.initFrom(hs); s.solve(hs, X, 80);
    const sp = new ARAP.Solver(m); // measure the eye/nose/tag triangles in both cases with the protected mesh's masks
    sp.R = s.R; const d = sp.diagnose(X);
    fp[mode] = { X: Array.from(X), ...d };
  }
}
const proofJson = { cases: results.map(r => ({ label: r.label, t: r.t, mesh: r.mesh, arap: r.arap, skinning: r.skinning })), feature_protect: { protected: { ...fp.protected, X: undefined }, unprotected: { ...fp.unprotected, X: undefined } } };
fs.writeFileSync(path.join(OUT, 'proof.json'), JSON.stringify(proofJson, null, 1));
console.log(JSON.stringify(proofJson, null, 1));

(async () => {
  const b = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-accelerated-2d-canvas'] });
  const p = await b.newPage();
  await p.goto('file://' + path.join(HERE, 'render.html').replace('render.html', 'proof_page.html'));
  await p.addScriptTag({ content: fs.readFileSync(path.join(HERE, 'drawings.js'), 'utf8') });
  const imgs = await p.evaluate(async ({ MESH, results, fp }) => {
    const load = async src => { const im = new Image(); im.src = src; await im.decode(); return im; };
    const tex = {}; for (const [k, m] of Object.entries(MESH)) tex[k] = await load('../' + m.texture);
    function drawMesh(g, m, X, ox, oy, sc, im, wire, col = 'rgba(0,0,0,.35)') {
      for (const t of m.tris) {
        const [a, b2, c] = t, P = [a, b2, c].map(v => [ox + X[2 * v] * sc, oy + X[2 * v + 1] * sc]), U = [a, b2, c].map(v => m.verts[v]);
        // affine map from texture triangle to screen triangle
        const [u0, u1, u2] = U, [p0, p1, p2] = P;
        const d = (u1[0] - u0[0]) * (u2[1] - u0[1]) - (u2[0] - u0[0]) * (u1[1] - u0[1]); if (Math.abs(d) < 1e-9) continue;
        const A = ((p1[0] - p0[0]) * (u2[1] - u0[1]) - (p2[0] - p0[0]) * (u1[1] - u0[1])) / d, B = ((p2[0] - p0[0]) * (u1[0] - u0[0]) - (p1[0] - p0[0]) * (u2[0] - u0[0])) / d;
        const C = ((p1[1] - p0[1]) * (u2[1] - u0[1]) - (p2[1] - p0[1]) * (u1[1] - u0[1])) / d, D2 = ((p2[1] - p0[1]) * (u1[0] - u0[0]) - (p1[1] - p0[1]) * (u2[0] - u0[0])) / d;
        g.save(); g.beginPath(); const cx = (p0[0] + p1[0] + p2[0]) / 3, cy = (p0[1] + p1[1] + p2[1]) / 3;
        P.forEach((q, k) => { const x = q[0] + (q[0] - cx) * 0.04, y = q[1] + (q[1] - cy) * 0.04; k ? g.lineTo(x, y) : g.moveTo(x, y); }); g.closePath(); g.clip();
        g.setTransform(A, C, B, D2, p0[0] - A * u0[0] - B * u0[1], p0[1] - C * u0[0] - D2 * u0[1]); g.drawImage(im, 0, 0); g.restore();
      }
      if (wire) { g.save(); g.lineWidth = 0.5; g.strokeStyle = col; g.beginPath(); for (const t of m.tris) { const P = t.map(v => [ox + X[2 * v] * sc, oy + X[2 * v + 1] * sc]); g.moveTo(...P[0]); g.lineTo(...P[1]); g.lineTo(...P[2]); g.closePath(); } g.stroke(); g.restore(); }
      // inverted triangles in red
      g.save(); g.fillStyle = 'rgba(255,0,0,.75)';
      for (const t of m.tris) { const P = t.map(v => [ox + X[2 * v] * sc, oy + X[2 * v + 1] * sc]); const ar = (P[1][0] - P[0][0]) * (P[2][1] - P[0][1]) - (P[1][1] - P[0][1]) * (P[2][0] - P[0][0]); if (ar <= 0) { g.beginPath(); g.moveTo(...P[0]); g.lineTo(...P[1]); g.lineTo(...P[2]); g.fill(); } }
      g.restore();
    }
    const out = {};
    // 1. meshes
    { const c = document.createElement('canvas'); c.width = 1800; c.height = 1250; const g = c.getContext('2d'); g.fillStyle = '#e9e4da'; g.fillRect(0, 0, c.width, c.height);
      let x = 10, y = 10, rh = 0;
      for (const [k, m] of Object.entries(MESH)) { if (k.endsWith('.arm')) continue; const sc = k.startsWith('person') ? 0.55 : 1; const w = m.w * sc, h = m.h * sc; if (x + w > 1800) { x = 10; y += rh + 14; rh = 0; }
        const X = m.verts.flat(); drawMesh(g, m, X, x, y, sc, tex[k], true);
        const arm = MESH[k.replace('.body', '.arm')]; if (k.endsWith('.body')) drawMesh(g, arm, arm.verts.flat(), x, y, sc, tex[k.replace('.body', '.arm')], true, 'rgba(0,0,120,.4)');
        g.fillStyle = '#e0b000'; for (const vs of Object.values(m.handles)) for (const v of vs) { g.beginPath(); g.arc(x + m.verts[v][0] * sc, y + m.verts[v][1] * sc, 2.2, 0, 7); g.fill(); }
        g.fillStyle = 'rgba(0,170,200,.5)'; for (const ts of Object.values(m.features)) for (const ti of ts) { const P = m.tris[ti].map(v => [x + m.verts[v][0] * sc, y + m.verts[v][1] * sc]); g.beginPath(); g.moveTo(...P[0]); g.lineTo(...P[1]); g.lineTo(...P[2]); g.fill(); }
        g.fillStyle = '#222'; g.font = '15px monospace'; g.fillText(`${k}  ${m.verts.length} v  ${m.tris.length} tri  cell ${m.cell}px`, x + 4, y + 16);
        x += w + 14; rh = Math.max(rh, h); }
      out.mesh = c.toDataURL('image/png'); }
    // 2. ARAP vs skinning
    { const c = document.createElement('canvas'); c.width = 1400; c.height = 300 * results.length + 40; const g = c.getContext('2d'); g.fillStyle = '#e9e4da'; g.fillRect(0, 0, c.width, c.height);
      g.fillStyle = '#222'; g.font = 'bold 18px monospace'; g.fillText('ARAP (this film)', 120, 26); g.fillText('weighted skinning, same handles + ARAP’s handle rotations', 760, 26);
      results.forEach((r, k) => { const m = MESH[r.mesh], y = 40 + k * 300;
        drawMesh(g, m, r.X, 40, y, 0.78, tex[r.mesh], false); drawMesh(g, m, r.L, 720, y, 0.78, tex[r.mesh], false);
        g.fillStyle = '#c00'; for (const h of r.handles) for (const ox of [40, 720]) { g.beginPath(); g.arc(ox + h[0] * .78, y + h[1] * .78, 3, 0, 7); g.fill(); }
        g.fillStyle = '#222'; g.font = '14px monospace';
        g.fillText(`${r.label}`, 40, y + 14);
        g.fillText(`inverted ${r.arap.inverted}  energy ${r.arap.energy.toFixed(4)}  min area ${r.arap.min_area_ratio.toFixed(2)}`, 40, y + 290);
        g.fillText(`inverted ${r.skinning.inverted}  energy ${r.skinning.energy.toFixed(4)}  min area ${r.skinning.min_area_ratio.toFixed(2)}`, 720, y + 290); });
      out.cmp = c.toDataURL('image/png'); }
    // 3. feature protection
    { const m = MESH.head_side, c = document.createElement('canvas'); c.width = 760; c.height = 330; const g = c.getContext('2d'); g.fillStyle = '#e9e4da'; g.fillRect(0, 0, c.width, c.height);
      drawMesh(g, m, fp.protected.X, 40, 40, 1.4, tex.head_side, false); drawMesh(g, m, fp.unprotected.X, 420, 40, 1.4, tex.head_side, false);
      g.fillStyle = '#222'; g.font = '14px monospace';
      g.fillText(`protected (w=40 on eye, nose, tag): max |σ-1| ${fp.protected.feature_distortion.toFixed(3)}`, 10, 18);
      g.fillText(`unprotected (w=1): max |σ-1| ${fp.unprotected.feature_distortion.toFixed(3)}`, 420, 318);
      out.fp = c.toDataURL('image/png'); }
    return out;
  }, { MESH, results, fp });
  const W = (f, d) => fs.writeFileSync(path.join(OUT, f), Buffer.from(d.split(',')[1], 'base64'));
  W('mesh_and_handles.png', imgs.mesh); W('arap_vs_skinning.png', imgs.cmp); W('feature_protect.png', imgs.fp);
  await b.close();
})();
