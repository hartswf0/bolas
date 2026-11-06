// 12 · STRANGLING — SCION-ARAP (id 34): preserve-shape deformation swarm.
// Each sack is a triangulated rest mesh (9x11 grid, 160 triangles). Every frame the pose is a set of
// soft handle targets (floor row, two neck-ring vertices, three crown vertices); a local-global
// as-rigid-as-possible solve (cotangent edge weights, per-vertex rotations, cached Cholesky) bends
// the cloth to them. The cord is two handles pulling the neck ring inward. Rigidity is character:
// Belindo's mesh carries 30x the edge stiffness and a weak neck handle, so the ring cannot close.
(function () {
  const NX = 9, NY = 13, NECK = 9, TOP = NY - 1, VN = NECK / (NY - 1);
  const S = 2.0, FLOOR = 915, VX = 1330, AX0 = 500, LAMPX = 960;
  const idx = (i, j) => j * NX + i;

  // per-sack material: s = edge stiffness, ln = neck-handle weight, pinch = rest neck gather
  const MAT = {
    R: { cd: 0.52, s: 1.6, ln: 14, pinch: 0.10, head: 0.04, flare: 0.05, ear: { a: 0.55, len: 0.17, wb: 0.15, o: 0.3 }, cloth: '#d6bf96' },
    B: { cd: 0.64, s: 40, ln: 3, pinch: 0.035, head: 0.0, flare: 0.03, ear: { a: 0.9, len: 0.14, wb: 0.12, o: 0.2 }, cloth: '#e8d5ae' },
    I: { sag: 0.07, cd: 0.5, s: 0.45, ln: 14, pinch: 0.10, head: 0.05, flare: 0.04, ear: { a: -1.52, len: 0.8, wb: 0.2, o: 0.12 }, cloth: '#e2cea5' },
    O: { cd: 0.64, s: 1.0, ln: 14, pinch: 0.14, head: 0.06, flare: 0.02, ear: { a: 0.6, len: 0.07, wb: 0.32, o: 0.4 }, cloth: '#f0e4c8' },
  };
  const CORD = {
    R: { c: '#8e4a3f', hi: '#b36a5c', w: 8 },
    B: { c: '#4a3b2b', hi: '#8a7356', w: 12 },
    I: { c: '#aab6bd', hi: '#dfe7ea', w: 6 },
    O: { c: '#8f47a8', hi: '#c48ad8', w: 4.5 },
  };

  // ---------- tiny linear algebra ----------
  function cholesky(A, n) {
    const L = new Float64Array(n * n);
    for (let i = 0; i < n; i++) {
      for (let j = 0; j <= i; j++) {
        let s = A[i * n + j];
        for (let k = 0; k < j; k++) s -= L[i * n + k] * L[j * n + k];
        if (i === j) L[i * n + i] = Math.sqrt(Math.max(s, 1e-12));
        else L[i * n + j] = s / L[j * n + j];
      }
    }
    return L;
  }
  function cholSolve(L, n, b, x) {
    for (let i = 0; i < n; i++) { let s = b[i]; for (let k = 0; k < i; k++) s -= L[i * n + k] * x[k]; x[i] = s / L[i * n + i]; }
    for (let i = n - 1; i >= 0; i--) { let s = x[i]; for (let k = i + 1; k < n; k++) s -= L[k * n + i] * x[k]; x[i] = s / L[i * n + i]; }
    return x;
  }

  // ---------- mesh tessellator ----------
  const MESH = {};
  function mesh(id, CAST) {
    if (MESH[id]) return MESH[id];
    const C = CAST[id], M = MAT[id], w = C.w, h = C.h, n = NX * NY;
    const P = new Float64Array(2 * n), U = new Float64Array(n), Vv = new Float64Array(n);
    for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
      const u = i / (NX - 1) - 0.5, v = j / (NY - 1), k = idx(i, j);
      let prof = 0.92 + 0.08 * Math.sin(Math.PI * Math.min(1, v * 1.15)) - M.pinch * Math.exp(-(((v - VN) / 0.075) ** 2)) + M.head * Math.exp(-(((v - 0.86) / 0.08) ** 2)) + M.flare * Math.max(0, (v - 0.85) / 0.15);
      let y = v * h;
      if (j === TOP) y = h * (1 - (M.sag || 0.05) * (1 - 4 * u * u));
      P[2 * k] = u * w * prof; P[2 * k + 1] = y; U[k] = u; Vv[k] = v;
    }
    const T = [];
    for (let j = 0; j < NY - 1; j++) for (let i = 0; i < NX - 1; i++) {
      const a = idx(i, j), b = idx(i + 1, j), c = idx(i, j + 1), d = idx(i + 1, j + 1);
      if ((i + j) % 2 === 0) T.push([a, b, d], [a, d, c]); else T.push([a, b, c], [b, d, c]);
    }
    // cotangent weights
    const W = new Map(); const key = (a, b) => a < b ? a * 1000 + b : b * 1000 + a;
    for (const t of T) for (let q = 0; q < 3; q++) {
      const o = t[q], a = t[(q + 1) % 3], b = t[(q + 2) % 3];
      const ax = P[2 * a] - P[2 * o], ay = P[2 * a + 1] - P[2 * o + 1], bx = P[2 * b] - P[2 * o], by = P[2 * b + 1] - P[2 * o + 1];
      const cot = (ax * bx + ay * by) / Math.abs(ax * by - ay * bx);
      W.set(key(a, b), (W.get(key(a, b)) || 0) + 0.5 * cot);
    }
    const NB = Array.from({ length: n }, () => []);
    for (const [kk, wv] of W) { const a = Math.floor(kk / 1000), b = kk % 1000, ww = Math.max(wv, 0.03); NB[a].push(b, ww); NB[b].push(a, ww); }
    // handles: floor row, neck ring sides, crown
    const H = [], LAM = [];
    for (let i = 0; i < NX; i++) { H.push(idx(i, 0)); LAM.push(600); }
    for (let i = 0; i < NX; i++) { H.push(idx(i, NECK)); LAM.push(i === 0 || i === NX - 1 ? M.ln : M.ln * 0.5); }
    H.push(idx(0, TOP), idx((NX - 1) / 2, TOP), idx(NX - 1, TOP)); LAM.push(6, 6, 6);
    const A = new Float64Array(n * n);
    for (let i = 0; i < n; i++) { const nb = NB[i]; for (let q = 0; q < nb.length; q += 2) { A[i * n + i] += M.s * nb[q + 1]; A[i * n + nb[q]] -= M.s * nb[q + 1]; } }
    H.forEach((hv, q) => { A[hv * n + hv] += LAM[q]; });
    const tA = T.map(t => area(P, t));
    return (MESH[id] = { id, n, P, U, Vv, T, NB, H, LAM, L: cholesky(A, n), s: M.s, w, h, tA, stencil: id === 'B' ? stencil(P, T, w, h) : null });
  }
  function area(P, t) { const [a, b, c] = t; return 0.5 * ((P[2 * b] - P[2 * a]) * (P[2 * c + 1] - P[2 * a + 1]) - (P[2 * c] - P[2 * a]) * (P[2 * b + 1] - P[2 * a + 1])); }
  // Belindo's wheat stencil: protected feature points bound by barycentric coordinates
  function stencil(P, T, w, h) {
    const pts = [], cx = 0, cy = 0.63 * h, r = 0.19 * w, strokes = [];
    const ring = []; for (let q = 0; q <= 28; q++) { const a = q / 28 * 2 * Math.PI; ring.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
    strokes.push(ring);
    strokes.push([[cx, cy - r * 0.75], [cx, cy + r * 0.7]]);
    for (let q = 0; q < 4; q++) { const yy = cy - r * 0.25 + q * r * 0.24; strokes.push([[cx - r * 0.38, yy - r * 0.12], [cx, yy + r * 0.08], [cx + r * 0.38, yy - r * 0.12]]); }
    return strokes.map(st => st.map(([x, y]) => bary(P, T, x, y)));
  }
  function bary(P, T, x, y) {
    for (let k = 0; k < T.length; k++) {
      const [a, b, c] = T[k];
      const x0 = P[2 * a], y0 = P[2 * a + 1], x1 = P[2 * b], y1 = P[2 * b + 1], x2 = P[2 * c], y2 = P[2 * c + 1];
      const d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2);
      const l0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / d, l1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / d, l2 = 1 - l0 - l1;
      if (l0 >= -1e-6 && l1 >= -1e-6 && l2 >= -1e-6) return [a, b, c, l0, l1, l2];
    }
    return [0, 0, 0, 1, 0, 0];
  }

  // ---------- local-global solver ----------
  // pose: {lean, drop, lift, cinch, shake, crownLift, reachL, reachR} in fractions of h (lift, in local px)
  function targets(M, po) {
    const out = [], h = M.h;
    // neck centre target and head rotation: the crown is carried rigidly about the neck
    const vn = VN, ncx = po.lean * h * vn * vn, ncy = (M.P[2 * idx((NX - 1) / 2, NECK) + 1]) - po.drop * h * vn + (po.lift || 0);
    const rc = [M.P[2 * idx((NX - 1) / 2, NECK)], M.P[2 * idx((NX - 1) / 2, NECK) + 1]];
    const phi = -Math.atan(2 * po.lean * vn) + (po.hang || 0);
    const cph = Math.cos(phi), sph = Math.sin(phi), p0 = -Math.atan(1.4 * po.lean * vn), c0 = Math.cos(p0), s0 = Math.sin(p0);
    for (const hv of M.H) {
      const v = M.Vv[hv];
      let x, y;
      if (v > 0.95) {
        const dx = M.P[2 * hv] - rc[0], dy = M.P[2 * hv + 1] - rc[1];
        x = ncx + cph * dx - sph * dy + po.shake * h; y = ncy + sph * dx + cph * dy;
        y += (po.crownLift || 0) * h; if (M.U[hv] > 0.2) y += (po.reachR || 0) * h; if (M.U[hv] < -0.2) y += (po.reachL || 0) * h;
      } else if (Math.abs(v - vn) < 1e-6) { // neck ring: cinched about its centre, then turned with the body
        const dx = M.P[2 * hv] * (1 - MAT[M.id].cd * po.cinch) - rc[0], dy = M.P[2 * hv + 1] - rc[1];
        x = ncx + c0 * dx - s0 * dy + po.shake * 0.5 * h; y = ncy + s0 * dx + c0 * dy;
      } else {
        x = M.P[2 * hv] + (po.lean + po.shake * 0.6 * v) * h * v * v;
        y = M.P[2 * hv + 1] - po.drop * h * v + (po.lift || 0);
      }
      out.push(x, y);
    }
    return out;
  }
  function solve(M, po, iters) {
    const n = M.n, P = M.P, h = M.h, tg = targets(M, po);
    const p = new Float64Array(2 * n), th = new Float64Array(n);
    for (let k = 0; k < n; k++) { const v = M.Vv[k]; p[2 * k] = P[2 * k] + po.lean * h * v * v; p[2 * k + 1] = P[2 * k + 1] * (1 - po.drop) + (po.lift || 0); }
    const bx = new Float64Array(n), by = new Float64Array(n), xs = new Float64Array(n), ys = new Float64Array(n);
    const cs = new Float64Array(n), sn = new Float64Array(n);
    for (let it = 0; it < iters; it++) {
      for (let i = 0; i < n; i++) {           // local step: best rotation per vertex
        const nb = M.NB[i]; let a = 0, b = 0;
        for (let q = 0; q < nb.length; q += 2) {
          const j = nb[q], w = nb[q + 1];
          const ex = P[2 * i] - P[2 * j], ey = P[2 * i + 1] - P[2 * j + 1], fx = p[2 * i] - p[2 * j], fy = p[2 * i + 1] - p[2 * j + 1];
          a += w * (ex * fx + ey * fy); b += w * (ex * fy - ey * fx);
        }
        th[i] = Math.atan2(b, a); cs[i] = Math.cos(th[i]); sn[i] = Math.sin(th[i]);
      }
      for (let i = 0; i < n; i++) {           // global step: rhs
        const nb = M.NB[i]; let sx = 0, sy = 0;
        for (let q = 0; q < nb.length; q += 2) {
          const j = nb[q], w = nb[q + 1];
          const ex = P[2 * i] - P[2 * j], ey = P[2 * i + 1] - P[2 * j + 1];
          const c = 0.5 * (cs[i] + cs[j]), s = 0.5 * (sn[i] + sn[j]);
          sx += w * (c * ex - s * ey); sy += w * (s * ex + c * ey);
        }
        bx[i] = M.s * sx; by[i] = M.s * sy;
      }
      M.H.forEach((hv, q) => { bx[hv] += M.LAM[q] * tg[2 * q]; by[hv] += M.LAM[q] * tg[2 * q + 1]; });
      cholSolve(M.L, n, bx, xs); cholSolve(M.L, n, by, ys);
      for (let i = 0; i < n; i++) { p[2 * i] = xs[i]; p[2 * i + 1] = ys[i]; }
    }
    return { p, th };
  }

  // ---------- helpers ----------
  const hex = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const rgb = (c, k, a) => `rgba(${Math.round(c[0] * k)},${Math.round(c[1] * k)},${Math.round(c[2] * k)},${a == null ? 1 : a})`;
  const mixc = (a, b, u) => [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u];
  const C01 = x => Math.max(0, Math.min(1, x));

  function makeK(K) {
    const sm = K.sm, bump = (a, b, c, d, t) => sm(a, b, t) * (1 - sm(c, d, t));
    return { sm, eo: K.eo, bump, lerp: K.lerp };
  }

  // ---------- performance: doer ----------
  function doerPose(A, V, t, k) {
    const { sm, eo, bump } = k; const C = MATc(A);
    const po = { lean: 0, drop: 0, lift: 0, cinch: 0, shake: 0, crownLift: 0, reachR: 0, reachL: 0 };
    let prog = 0, back = 0;
    const fail = V === 'B';
    if (A === 'R') { // miserly, deliberate: four rocking steps, then two heaves
      const u = C01((t - 0.4) / 1.3), st = 4; prog = (Math.floor(Math.min(u * st, st - 1e-9)) + sm(0, 1, (u * st) % 1)) / st; if (u >= 1) prog = 1;
      po.lean = 0.06 * Math.sin(2 * Math.PI * 1.55 * (t - 0.4)) * bump(0.4, 0.6, 1.5, 1.8, t);
      po.lean += 0.16 * bump(1.55, 1.75, 1.9, 2.05, t);
      po.reachR = 0.25 * bump(1.5, 1.75, 1.95, 2.1, t);
      po.lean -= 0.18 * sm(2.2, 2.38, t) + 0.14 * sm(2.45, 2.6, t);
      po.drop = 0.06 * sm(2.2, 2.6, t);
      if (!fail) { po.lean += 0.03 * Math.sin(2 * Math.PI * 1.2 * (t - 2.6)) * bump(2.6, 2.8, 3.6, 4.2, t); po.lean += 0.26 * sm(4.2, 4.9, t); }
      back = 60 * sm(4.3, 5.0, t);
    } else if (A === 'B') { // three heavy stomps, looms over, one yank that lifts
      const u = C01((t - 0.4) / 0.9), st = 3; prog = (Math.floor(Math.min(u * st, st - 1e-9)) + eo(0, 1, (u * st) % 1)) / st; if (u >= 1) prog = 1;
      const ph = (u * st) % 1; po.drop = (t > 0.4 && t < 1.3) ? 0.07 * Math.pow(Math.max(0, 1 - ph * 3), 2) + 0.07 * sm(0.85, 1, ph) : 0;
      po.lean = 0.3 * bump(1.3, 1.7, 2.15, 2.4, t);
      po.reachR = 0.1 * bump(1.3, 1.6, 2.0, 2.3, t);
      po.lean -= 0.27 * eo(2.4, 2.6, t);
      if (!fail) { po.lean += 0.37 * sm(4.2, 4.9, t); po.drop += 0.05 * sm(4.2, 4.9, t); }
      back = 30 * sm(4.3, 5.0, t);
    } else if (A === 'I') { // listless drift, twirls the cord, then flops backward as dead weight
      prog = sm(0.4, 1.6, t) * 0.92 + 0.08 * sm(1.6, 2.0, t);
      po.lean = 0.07 * Math.sin(2 * Math.PI * 0.9 * (t - 0.4)) * bump(0.4, 0.7, 1.7, 2.0, t);
      po.lean += 0.12 * bump(1.75, 1.9, 2.0, 2.15, t);
      po.reachR = 0.3 * bump(1.0, 1.2, 1.9, 2.1, t);
      po.lean -= 0.42 * sm(2.25, 2.6, t);
      po.drop = 0.21 * sm(2.25, 2.6, t);
      if (!fail) { po.lean += 0.12 * sm(4.3, 5.0, t); po.drop -= 0.04 * sm(4.3, 5.0, t); }
      back = 20 * sm(4.3, 5.0, t);
    } else { // Ogiva: precise glide, bends over (or tosses up at Belindo), one sharp cold pull
      prog = eo(0.4, 1.05, t);
      const over = V === 'B' ? 0.12 : 0.34;
      po.lean = over * bump(1.25, 1.65, 2.1, 2.35, t);
      po.reachR = (V === 'B' ? 0.18 : 0.05) * bump(1.3, 1.6, 1.9, 2.15, t);
      po.lean -= 0.1 * eo(2.47, 2.6, t);
      po.crownLift = 0.03 * eo(2.47, 2.6, t);
      if (!fail) { po.lean += 0.1 * sm(4.2, 4.6, t); po.crownLift -= 0.03 * sm(4.2, 4.6, t); }
      back = 75 * sm(4.3, 4.75, t);
    }
    if (A === 'I') { po.drop += 0.07; po.lean -= 0.03; } // half empty: always slumped
    if (fail) { // tug of war that is lost: strain, the cord pops, fall back, recover
      const strain = bump(2.6, 2.7, 3.45, 3.55, t);
      po.lean += -0.06 * strain + 0.025 * Math.sin(2 * Math.PI * 9 * t) * strain;
      const fk = A === 'I' ? 0.2 : 1, f = fk * bump(3.55, 3.8, 4.5, 5.3, t), f2 = fk * sm(3.55, 3.8, t);
      po.lean += -0.14 * f + 0.12 * sm(4.5, 5.3, t) * f2;
      po.drop += 0.14 * f + 0.04 * sm(4.5, 5.3, t) * f2;
      back = 55 * sm(3.55, 4.0, t);
    }
    return { po, prog, back };
  }
  function MATc(id) { return MAT[id]; }

  // ---------- performance: victim ----------
  function cinchOf(A, t, k) {
    const { sm, eo } = k;
    if (A === 'R') return 0.55 * sm(2.22, 2.38, t) + 0.45 * sm(2.45, 2.6, t);
    if (A === 'B') return eo(2.42, 2.6, t);
    if (A === 'I') return sm(2.25, 2.6, t);
    return eo(2.47, 2.6, t);
  }
  function victimPose(V, A, t, k) {
    const { sm, bump } = k;
    const po = { lean: 0, drop: 0, lift: 0, cinch: 0, shake: 0, crownLift: 0, reachR: 0, reachL: 0 };
    let c = cinchOf(A, t, k), pullX = 0;
    if (V === 'B') { // refusal: the ring stays open, he shrugs it off, then turns toward the doer
      po.cinch = c * (1 - sm(3.45, 3.6, t));
      po.crownLift = 0.12 * bump(3.3, 3.48, 3.62, 3.95, t);
      po.reachL = po.reachR = 0.08 * bump(3.3, 3.48, 3.62, 3.95, t);
      po.lean = -0.015 * c * (1 - sm(3.45, 3.6, t)) - 0.07 * sm(4.3, 5.1, t);
      return { po, c, alarm: 0.5 * bump(3.38, 3.5, 3.6, 3.9, t), dead: 0, pullX: 0 };
    }
    po.cinch = c;
    if (V === 'I') { po.drop += 0.07; po.lean += 0.03; }
    const pk = { R: 0.10, I: 0.24, O: 0.14 }[V];
    po.lean = -pk * c;
    if (A === 'B') { po.lift = 22 * bump(2.5, 2.65, 3.0, 3.25, t); pullX = -26 * bump(2.5, 2.7, 3.1, 3.4, t); }
    const sh = bump(2.55, 2.65, 3.0, 3.45, t), tt = t - 2.6;
    if (V === 'R') { po.shake = 0.07 * Math.sin(2 * Math.PI * 3 * tt) * sh; }
    if (V === 'I') { po.shake = 0.05 * Math.sin(2 * Math.PI * 5 * tt) * sh; }
    if (V === 'O') { po.shake = 0.09 * Math.sin(2 * Math.PI * 6 * tt) * sh; }
    const sl = sm(3.25, 4.1, t);
    if (V === 'R') { po.drop += 0.14 * sl; po.lean += 0.12 * sl; po.hang = -0.2 * sl; }
    if (V === 'I') { po.drop += 0.13 * sl; po.lean += 0.1 * sl; po.hang = 0.2 * sl; }
    if (V === 'O') { po.drop += 0.30 * sl; po.lean += 0.52 * sl; }
    return { po, c, alarm: bump(2.3, 2.5, 3.15, 3.5, t), dead: sm(3.35, 4.0, t), pullX };
  }

  // ---------- drawing ----------
  function toScreen(p, X, lift) { const n = p.length / 2, o = new Float64Array(2 * n); for (let i = 0; i < n; i++) { o[2 * i] = X + S * p[2 * i]; o[2 * i + 1] = FLOOR - S * p[2 * i + 1]; } return o; }
  function V2(o, i) { return [o[2 * i], o[2 * i + 1]]; }

  function earGeom(M, sol, X, side, mood, aimLocal) {
    // side: +1 right, -1 left. angle measured in local y-up frame.
    const E = MAT[M.id].ear, h = M.h, w = M.w;
    const ci = side > 0 ? idx(NX - 1, TOP) : idx(0, TOP);
    const cx = sol.p[2 * ci], cy = sol.p[2 * ci + 1], th = sol.th[ci];
    let a = E.a; // right ear base angle
    a = a + (1.45 - a) * mood.alarm * (M.id === 'I' ? 0.95 : 0.6);
    a = a + (-1.6 - a) * mood.dead * 0.8;
    if (mood.drowsy) a = a + (-1.3 - a) * 0.45;
    const thE = E.a < 0 ? th * 0.25 : th; // hanging ears obey gravity more than the cloth's rotation
    let ang = side > 0 ? a + thE : Math.PI - a + thE;
    let len = E.len * h * (1 + 0.15 * mood.alarm);
    if (aimLocal && aimLocal.k > 0) {
      const ta = Math.atan2(aimLocal.y - cy, aimLocal.x - cx);
      let d = ta - ang; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
      ang += d * aimLocal.k;
    }
    const ex = cx + Math.cos(ang) * len, ey = cy + Math.sin(ang) * len;
    const ox = side * 1, oy = 0.35 * (E.a > 0 ? 1 : -0.6); const ol = Math.hypot(ox, oy);
    const qx = cx + (Math.cos(th) * ox - Math.sin(th) * oy) / ol * len * E.o, qy = cy + (Math.sin(th) * ox + Math.cos(th) * oy) / ol * len * E.o;
    return { c: [cx, cy], q: [qx, qy], e: [ex, ey], wb: E.wb * w, X, hang: E.a < 0 };
  }
  function drawEar(g, eg, col, outline) {
    const pts = [], N = 12;
    for (let q = 0; q <= N; q++) {
      const u = q / N, a = (1 - u) * (1 - u), b = 2 * u * (1 - u), c = u * u;
      pts.push([a * eg.c[0] + b * eg.q[0] + c * eg.e[0], a * eg.c[1] + b * eg.q[1] + c * eg.e[1]]);
    }
    const L = [], R = [];
    for (let q = 0; q <= N; q++) {
      const p0 = pts[Math.max(0, q - 1)], p1 = pts[Math.min(N, q + 1)];
      let tx = p1[0] - p0[0], ty = p1[1] - p0[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
      const uu = q / N, hw = (eg.wb * 0.5) * (eg.hang ? (0.3 + 0.7 * Math.sin(Math.PI * Math.min(1, 0.12 + uu * 0.75))) : (1 - uu * 0.65));
      L.push([pts[q][0] - ty * hw, pts[q][1] + tx * hw]); R.push([pts[q][0] + ty * hw, pts[q][1] - tx * hw]);
    }
    g.beginPath();
    const sp = ([x, y]) => [eg.X + S * x, FLOOR - S * y];
    let s0 = sp(L[0]); g.moveTo(s0[0], s0[1]);
    for (const p of L) { const s = sp(p); g.lineTo(s[0], s[1]); }
    for (let q = R.length - 1; q >= 0; q--) { const s = sp(R[q]); g.lineTo(s[0], s[1]); }
    g.closePath(); g.fillStyle = col; g.fill(); g.lineWidth = 2; g.strokeStyle = outline; g.stroke();
    return sp(pts[N]);
  }

  function drawSack(g, id, M, sol, X, mood, aim, K, tags) {
    const askew = id === 'O' && tags && tags.indexOf('wig') >= 0;
    const o = toScreen(sol.p, X);
    const base = hex(MAT[id].cloth), dark = [70, 52, 38], shawl = hex('#6e3a33'), wig = hex('#7a3b8f');
    const lampSide = X < LAMPX ? 1 : -1;
    const ears = [];
    // ears behind body for long hanging ones (Inigo), else after
    const earCol = rgb(mixc(base, dark, 0.12), 1), earOut = 'rgba(60,44,32,0.7)';
    const eR = earGeom(M, sol, X, 1, mood, aim), eL = earGeom(M, sol, X, -1, mood, null);
    let grip = null;
    if (id === 'O') { // wig strands hang outside the body, behind
      wigStrands(g, M, o, wig, 1); if (!askew) wigStrands(g, M, o, wig, -1);
    }
    if (id === 'I') { drawEar(g, eL, earCol, earOut); }
    // triangles
    for (let k = 0; k < M.T.length; k++) {
      const [a, b, c] = M.T[k];
      const ar = (0.5 * ((o[2 * b] - o[2 * a]) * (o[2 * c + 1] - o[2 * a + 1]) - (o[2 * c] - o[2 * a]) * (o[2 * b + 1] - o[2 * a + 1]))) / (-M.tA[k] * S * S);
      const u = (M.U[a] + M.U[b] + M.U[c]) / 3, v = (M.Vv[a] + M.Vv[b] + M.Vv[c]) / 3;
      let col = base;
      const vmin = Math.min(M.Vv[a], M.Vv[b], M.Vv[c]);
      if (id === 'R' && vmin > 0.8) col = shawl;
      if (id === 'O' && vmin > 0.74) col = wig;
      let crease = C01((1 - ar) * 1.6) * 0.55, light = 0.80 + 0.22 * Math.cos(Math.PI * (u - lampSide * 0.22));
      light *= 0.92 + 0.08 * v;
      const cc = mixc(col, dark, crease);
      const f = rgb(cc, light * (1 - 0.25 * Math.max(mood.dead * (id === 'B' ? 0 : 1), mood.grey || 0)));
      g.beginPath(); g.moveTo(o[2 * a], o[2 * a + 1]); g.lineTo(o[2 * b], o[2 * b + 1]); g.lineTo(o[2 * c], o[2 * c + 1]); g.closePath();
      g.fillStyle = f; g.fill(); g.strokeStyle = f; g.lineWidth = 1; g.stroke();
    }
    // mesh hatching: rows (weave) and columns, thin
    g.lineWidth = 1.1; g.strokeStyle = 'rgba(70,50,35,0.22)';
    for (let j = 1; j < NY - 1; j++) { g.beginPath(); for (let i = 0; i < NX; i++) { const q = idx(i, j); i ? g.lineTo(o[2 * q], o[2 * q + 1]) : g.moveTo(o[2 * q], o[2 * q + 1]); } g.stroke(); }
    g.strokeStyle = 'rgba(70,50,35,0.12)';
    for (let i = 1; i < NX - 1; i++) { g.beginPath(); for (let j = 0; j < NY; j++) { const q = idx(i, j); j ? g.lineTo(o[2 * q], o[2 * q + 1]) : g.moveTo(o[2 * q], o[2 * q + 1]); } g.stroke(); }
    // outline
    g.beginPath();
    const ring = [];
    for (let i = 0; i < NX; i++) ring.push(idx(i, 0));
    for (let j = 1; j < NY; j++) ring.push(idx(NX - 1, j));
    for (let i = NX - 2; i >= 0; i--) ring.push(idx(i, TOP));
    for (let j = NY - 2; j > 0; j--) ring.push(idx(0, j));
    ring.forEach((q, z) => z ? g.lineTo(o[2 * q], o[2 * q + 1]) : g.moveTo(o[2 * q], o[2 * q + 1]));
    g.closePath(); g.lineWidth = 3; g.strokeStyle = 'rgba(48,34,26,0.85)'; g.stroke();
    if (id === 'B') { // belt: a band carried by mesh row 4 (40% height)
      g.lineCap = 'butt'; g.lineJoin = 'round';
      const br = 0.4 * (NY - 1), j0 = Math.floor(br), bf = br - j0;
      g.beginPath(); for (let i = 0; i < NX; i++) { const q = idx(i, j0), q2 = idx(i, j0 + 1), x = o[2 * q] * (1 - bf) + o[2 * q2] * bf, y = o[2 * q + 1] * (1 - bf) + o[2 * q2 + 1] * bf; i ? g.lineTo(x, y) : g.moveTo(x, y); }
      g.strokeStyle = '#2a2622'; g.lineWidth = 0.075 * M.h * S; g.stroke();
      g.strokeStyle = 'rgba(160,140,110,0.35)'; g.lineWidth = 2; g.stroke();
    }
    if (id === 'B' && M.stencil) { // protected feature: wheat stencil carried by barycentrics
      g.strokeStyle = 'rgba(120,70,40,0.75)'; g.lineWidth = 4;
      for (const st of M.stencil) {
        g.beginPath();
        st.forEach(([a, b, c, l0, l1, l2], z) => { const x = l0 * o[2 * a] + l1 * o[2 * b] + l2 * o[2 * c], y = l0 * o[2 * a + 1] + l1 * o[2 * b + 1] + l2 * o[2 * c + 1]; z ? g.lineTo(x, y) : g.moveTo(x, y); });
        g.stroke();
      }
    }
    if (id === 'O') { if (askew) { g.save(); g.translate(14, 6); wigCap(g, M, o, wig); g.restore(); } else wigCap(g, M, o, wig); }
    if (id !== 'I') drawEar(g, eL, id === 'O' ? rgb(wig, 1) : id === 'R' ? rgb(shawl, 1.05) : earCol, earOut);
    grip = drawEar(g, eR, id === 'O' ? rgb(wig, 1) : id === 'R' ? rgb(shawl, 1.05) : earCol, earOut);
    return { o, grip };
  }
  function wigStrands(g, M, o, wig, side) {
    const i0 = side > 0 ? NX - 1 : 0, pts = [];
    for (let j = TOP; j >= 4; j--) { const q = idx(i0, j); pts.push([o[2 * q] + side * 9, o[2 * q + 1]]); }
    const inner = [];
    for (let j = 4; j <= TOP; j++) { const q = idx(i0, j), q2 = idx(i0 - side, j); inner.push([o[2 * q] * 0.6 + o[2 * q2] * 0.4, o[2 * q + 1]]); }
    g.beginPath(); pts.forEach(([x, y], z) => z ? g.lineTo(x, y) : g.moveTo(x, y));
    const last = pts[pts.length - 1]; g.quadraticCurveTo(last[0] + side * 4, last[1] + 26, inner[0][0], inner[0][1] + 10);
    inner.forEach(([x, y]) => g.lineTo(x, y));
    g.closePath(); g.fillStyle = rgb(wig, 0.9); g.fill(); g.strokeStyle = 'rgba(40,16,50,0.8)'; g.lineWidth = 2; g.stroke();
    g.strokeStyle = 'rgba(190,130,210,0.35)'; g.lineWidth = 2;
    g.beginPath(); pts.forEach(([x, y], z) => z ? g.lineTo(x - side * 5, y) : g.moveTo(x - side * 5, y)); g.stroke();
  }
  function wigCap(g, M, o, wig) {
    g.beginPath();
    const q0 = idx(0, TOP), q1 = idx(NX - 1, TOP), qc = idx((NX - 1) / 2, TOP), qn = idx((NX - 1) / 2, TOP - 1);
    const nx = o[2 * qc] - o[2 * qn], ny = o[2 * qc + 1] - o[2 * qn + 1], nl = Math.hypot(nx, ny) || 1;
    g.moveTo(o[2 * q0], o[2 * q0 + 1]);
    g.quadraticCurveTo(o[2 * qc] + nx / nl * 46, o[2 * qc + 1] + ny / nl * 46, o[2 * q1], o[2 * q1 + 1]);
    for (let i = NX - 1; i >= 0; i--) { const q = idx(i, TOP); g.lineTo(o[2 * q], o[2 * q + 1]); }
    g.closePath(); g.fillStyle = rgb(wig, 1.05); g.fill(); g.strokeStyle = 'rgba(40,16,50,0.8)'; g.lineWidth = 2; g.stroke();
  }

  function backdrop(g, t, K) {
    const W = K.W, H = K.H;
    let gr = g.createLinearGradient(0, 0, 0, FLOOR);
    gr.addColorStop(0, '#15131b'); gr.addColorStop(1, '#2a2430');
    g.fillStyle = gr; g.fillRect(0, 0, W, FLOOR);
    // wallpaper: the rest-mesh lattice, faint
    g.strokeStyle = 'rgba(200,180,150,0.045)'; g.lineWidth = 1;
    const cs = 54;
    for (let y = 0; y < FLOOR - 160; y += cs) for (let x = 0; x < W; x += cs) {
      g.beginPath(); g.moveTo(x, y); g.lineTo(x + cs, y); g.lineTo(x + cs, y + cs); g.closePath(); g.stroke();
    }
    g.fillStyle = '#231c20'; g.fillRect(0, FLOOR - 160, W, 160);
    g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(0, FLOOR - 164, W, 6);
    for (let x = 40; x < W; x += 220) { g.strokeStyle = 'rgba(255,230,190,0.05)'; g.strokeRect(x, FLOOR - 140, 180, 115); }
    gr = g.createLinearGradient(0, FLOOR, 0, H); gr.addColorStop(0, '#2c2119'); gr.addColorStop(1, '#16100c');
    g.fillStyle = gr; g.fillRect(0, FLOOR, W, H - FLOOR);
    g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 2;
    for (let q = -12; q <= 12; q++) { g.beginPath(); g.moveTo(LAMPX + q * 60, FLOOR); g.lineTo(LAMPX + q * 190, H); g.stroke(); }
    // hanging lamp
    g.strokeStyle = '#0c0b0e'; g.lineWidth = 3; g.beginPath(); g.moveTo(LAMPX, 0); g.lineTo(LAMPX, 170); g.stroke();
    const rg = g.createRadialGradient(LAMPX, 220, 10, LAMPX, 420, 900);
    rg.addColorStop(0, 'rgba(255,214,140,0.42)'); rg.addColorStop(0.4, 'rgba(255,190,110,0.12)'); rg.addColorStop(1, 'rgba(255,190,110,0)');
    g.fillStyle = rg; g.fillRect(0, 0, W, H);
    g.fillStyle = '#3a2e22'; g.beginPath(); g.moveTo(LAMPX - 26, 170); g.lineTo(LAMPX + 26, 170); g.lineTo(LAMPX + 70, 228); g.lineTo(LAMPX - 70, 228); g.closePath(); g.fill();
    g.fillStyle = '#ffe3a8'; g.beginPath(); g.ellipse(LAMPX, 230, 30, 9, 0, 0, Math.PI * 2); g.fill();
    const fl = g.createRadialGradient(LAMPX, FLOOR + 30, 10, LAMPX, FLOOR + 30, 700);
    fl.addColorStop(0, 'rgba(255,200,120,0.16)'); fl.addColorStop(1, 'rgba(255,200,120,0)');
    g.fillStyle = fl; g.fillRect(0, FLOOR - 40, W, H - FLOOR + 40);
  }
  function shadow(g, o, M) {
    const a = idx(0, 0), b = idx(NX - 1, 0), y = Math.max(o[2 * a + 1], o[2 * b + 1]);
    const lift = FLOOR - y;
    g.fillStyle = `rgba(0,0,0,${0.45 - Math.min(0.25, lift / 200)})`;
    g.beginPath(); g.ellipse((o[2 * a] + o[2 * b]) / 2, FLOOR + 6, (o[2 * b] - o[2 * a]) / 2 + 24, 14, 0, 0, Math.PI * 2); g.fill();
  }

  // cord rendering
  function stroke2(g, path, cd, w) {
    g.lineCap = 'round'; g.lineJoin = 'round';
    g.strokeStyle = 'rgba(10,6,4,0.55)'; g.lineWidth = (w || cd.w) + 3; path(); g.stroke();
    g.strokeStyle = cd.c; g.lineWidth = w || cd.w; path(); g.stroke();
    g.strokeStyle = cd.hi; g.lineWidth = Math.max(1, (w || cd.w) * 0.3); path(); g.stroke();
  }
  function tail(g, a, b, taut, cd) {
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const sag = (1 - taut) * (40 + len * 0.35);
    const cy = Math.min(my + sag, FLOOR + 4);
    stroke2(g, () => { g.beginPath(); g.moveTo(a[0], a[1]); g.quadraticCurveTo(mx, cy, b[0], b[1]); }, cd);
  }
  function loopEllipse(g, cx, cy, rx, ry, cd, front) {
    stroke2(g, () => { g.beginPath(); g.ellipse(cx, cy, rx, ry, 0, front ? 0 : Math.PI, front ? Math.PI : 2 * Math.PI); }, cd);
  }

  // ---------- pose stage: one solve shared by picture, marks and sound ----------
  function stage(t, A, V, K, carry) {
    const k = makeK(K), CA = K.CAST[A], CV = K.CAST[V];
    const tagA = (carry && carry[A]) || [], tagV = (carry && carry[V]) || [];
    const MA = mesh(A, K.CAST), MV = mesh(V, K.CAST);
    const vp = victimPose(V, A, t, k), dp = doerPose(A, V, t, k);
    carryPose(vp.po, tagV, V); carryPose(dp.po, tagA, A);
    const vsol = solve(MV, vp.po, 9), asol = solve(MA, dp.po, 9);
    const vX = VX + vp.pullX;
    const AXc = VX - S * (CA.w / 2 + CV.w / 2) - 46;
    const aX = AX0 + (AXc - AX0) * dp.prog - dp.back;
    return { vp, dp, vsol, asol, vX, aX, vo: toScreen(vsol.p, vX), ao: toScreen(asol.p, aX), tagA, tagV, MA, MV };
  }
  // carried damage as handle targets: a cinched neck keeps a partial pinch; an emptied sack sits lower
  function carryPose(po, tags, id) {
    if (!tags.length) return;
    if (tags.indexOf('cinched') >= 0 && id !== 'B') po.cinch = Math.max(po.cinch, 0.45);
    if (tags.indexOf('emptied') >= 0) po.drop += id === 'I' ? 0 : 0.04;
  }
  function bbox(o) {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    for (let i = 0; i < o.length; i += 2) { x0 = Math.min(x0, o[i]); x1 = Math.max(x1, o[i]); y0 = Math.min(y0, o[i + 1]); y1 = Math.max(y1, o[i + 1]); }
    return { x: Math.round(x0), y: Math.round(y0), w: Math.round(x1 - x0), h: Math.round(y1 - y0) };
  }
  // carried tags drawn on the solved mesh: marks bound to rows, vertices or barycentric points, so they bend with the cloth
  function carryMarks(g, id, M, o, tags, t) {
    if (!tags || !tags.length) return;
    const P = (i, j) => [o[2 * idx(i, j)], o[2 * idx(i, j) + 1]];
    const row = (j, f) => { g.beginPath(); for (let i = 0; i < NX; i++) { const a = P(i, j); i ? g.lineTo(a[0], a[1] + (f || 0)) : g.moveTo(a[0], a[1] + (f || 0)); } };
    const mid = (i, j) => { const a = P(i, j), b = P(i + 1, j + 1); return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; };
    g.save(); g.lineCap = 'round'; g.lineJoin = 'round';
    for (const tg of tags) {
      if (tg === 'rope') { for (const j of [3, 6]) { row(j); g.strokeStyle = 'rgba(20,12,6,0.6)'; g.lineWidth = 9; g.stroke(); row(j); g.strokeStyle = '#7a6244'; g.lineWidth = 6; g.stroke(); } }
      else if (tg === 'gag') { row(TOP - 1); g.strokeStyle = 'rgba(30,20,10,0.5)'; g.lineWidth = 16; g.stroke(); row(TOP - 1); g.strokeStyle = '#ece6da'; g.lineWidth = 12; g.stroke(); }
      else if (tg === 'blot') { const c = mid(5, 6); g.fillStyle = 'rgba(28,30,70,0.85)'; g.beginPath(); for (let q = 0; q < 14; q++) { const a = q / 14 * 2 * Math.PI, r = 16 + 9 * K0(q * 3.1); q ? g.lineTo(c[0] + r * Math.cos(a), c[1] + r * Math.sin(a)) : g.moveTo(c[0] + r * Math.cos(a), c[1] + r * Math.sin(a)); } g.closePath(); g.fill(); }
      else if (tg === 'tag') { const c = mid(2, 5), d = mid(3, 4); const ang = Math.atan2(d[1] - c[1], d[0] - c[0]) * 0.3; g.save(); g.translate(c[0], c[1]); g.rotate(ang); g.fillStyle = '#efe7c9'; g.strokeStyle = '#5a4a32'; g.lineWidth = 2; g.fillRect(-24, 0, 48, 32); g.strokeRect(-24, 0, 48, 32); g.fillStyle = '#a33'; g.beginPath(); g.arc(0, 3, 3.5, 0, 7); g.fill(); g.restore(); }
      else if (tg === 'torn') { const s = id === 'O' ? 0 : NX - 1; g.strokeStyle = '#3a2a1c'; g.lineWidth = 5; g.beginPath(); for (let j = 3; j <= 7; j++) { const a = P(s, j), b = P(s + (s ? -1 : 1), j); const z = (j % 2 ? 0.25 : 0.05); const x = a[0] * (1 - z) + b[0] * z, y = a[1]; j === 3 ? g.moveTo(x, y) : g.lineTo(x, y); } g.stroke();
        g.fillStyle = '#fbf7ee'; const a = P(s, 3); for (let q = 0; q < 5; q++) { g.beginPath(); g.arc(a[0] + (K0(q) - 0.5) * 10, a[1] + q * 4, 2.5, 0, 7); g.fill(); } }
      else if (tg === 'coins') { const a = P(NX - 1, 1); for (let q = 0; q < 3; q++) { g.fillStyle = '#c9a23a'; g.strokeStyle = '#6b5212'; g.lineWidth = 1.5; g.beginPath(); g.ellipse(a[0] + 14 + q * 9, FLOOR + 2 - q * 5, 9, 4, 0, 0, 7); g.fill(); g.stroke(); } }
      else if (tg === 'emptied') { row(1, 0); g.strokeStyle = 'rgba(251,247,238,0.55)'; g.lineWidth = 3; g.setLineDash([3, 7]); g.stroke(); g.setLineDash([]); }
      else if (tg === 'cinched' && id === 'B') { row(NECK); g.strokeStyle = 'rgba(80,60,40,0.7)'; g.lineWidth = 4; g.setLineDash([10, 8]); g.stroke(); g.setLineDash([]); } // the cord never bit Belindo
      else if (tg === 'cinched') { row(NECK); g.strokeStyle = 'rgba(40,24,14,0.75)'; g.lineWidth = 5; g.stroke(); }
    }
    g.restore();
  }
  function K0(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }

  // ---------- sound: grains, with the cord's creak pitched by the solved neck width ----------
  function soundtrack(ac, out0, t0, A, V, K) {
    const out = ac.createGain(); out.gain.value = 1.3; out.connect(out0);
    const SND = K.SND, k = makeK(K), { sm } = k, fail = V === 'B';
    const pan = x => Math.max(-1, Math.min(1, x / 960 - 1));
    const at = (t) => t0 + t;
    const P0 = stage(0, A, V, K, null), vPan = pan(P0.vX);
    const doerX = t => stage(t, A, V, K, null).aX;
    // idle breath, both sacks
    SND.say(ac, out, A, at(0.02), 'breathe', 0.35, pan(P0.aX)); SND.say(ac, out, V, at(0.05), 'breathe', 0.35, vPan);
    // doer approach: footfalls at the frames the steps land
    let steps = [];
    if (A === 'R') steps = [1, 2, 3, 4].map(q => 0.4 + 1.3 * q / 4);
    if (A === 'B') steps = [1, 2, 3].map(q => 0.4 + 0.9 * q / 3 - 0.02);
    if (A === 'I') steps = [0.75, 1.2, 1.6];
    if (A === 'O') steps = [0.55, 0.8];
    steps.forEach((ts, q) => SND.say(ac, out, A, at(ts), 'step', A === 'I' ? 0.6 : A === 'B' ? 0.7 : 1, pan(doerX(ts))));
    if (A === 'O') SND.say(ac, out, A, at(1.05), 'tick', 0.8, pan(doerX(1.05))); // she stops exactly
    if (A === 'R') for (let q = 0; q < 4; q++) SND.say(ac, out, A, at(0.55 + q * 0.32), 'tick', 0.25, pan(doerX(0.55 + q * 0.32))); // the rocking
    // the throw: a swish of cloth grains moving from doer to victim
    const tT = { R: 1.6, B: 1.55, I: 1.75, O: 1.45 }[A];
    if (A === 'I') SND.cloud(ac, out, at(1.0), 0.75, 40, { bp: 1400, q: 3, a: 0.03, d: [0.02, 0.05], spread: 0.3 }, u => 0.5 + 0.5 * Math.sin(u * 2 * Math.PI * 7)); // twirl
    SND.cloud(ac, out, at(tT), 2.05 - tT, 90, { bp: 900, q: 1.2, a: 0.045, d: [0.02, 0.06], spread: 0.5 }, u => Math.sin(Math.PI * u));
    // the loop settles on the neck
    SND.grain(ac, out, at(2.22), { bp: 700, q: 2, d: 0.05, a: 0.15, pan: vPan });
    // creak: the cord under tension; pitch follows how far the ARAP solve has closed the neck ring
    const MV = mesh(V, K.CAST), w0 = MV.P[2 * idx(NX - 1, NECK)] - MV.P[2 * idx(0, NECK)];
    const relT = fail ? 3.45 : 4.35;
    for (let q = 0, tt = 2.2; tt < relT; tt += 0.035, q++) {
      const P = stage(tt, A, V, K, null);
      const s = P.vsol.p, wn = Math.hypot(s[2 * idx(NX - 1, NECK)] - s[2 * idx(0, NECK)], s[2 * idx(NX - 1, NECK) + 1] - s[2 * idx(0, NECK) + 1]) / w0;
      const tension = sm(2.2, 2.6, tt) * (1 - sm(relT - 0.25, relT, tt)) * (fail ? 1 : (1 - 0.7 * sm(3.2, 4.0, tt)));
      if (tension < 0.03) continue;
      const f = fail ? 180 + 260 * sm(2.6, 3.45, tt) : 220 + 900 * (1 - wn);
      const jit = K.hash(q * 3.7 + 11);
      if (jit > 0.25 + 0.5 * (1 - tension)) SND.grain(ac, out, at(tt + jit * 0.02), { f, type: 'sawtooth', noise: 0.55, bp: f * 2.2, q: 4, d: 0.025 + 0.02 * jit, a: 0.09 * tension, pan: vPan * 0.8, att: 0.2 });
    }
    // the contact: the cinch lands; for Belindo the same pull meets a wall
    const cP = pan(stage(2.6, A, V, K, null).vo[2 * idx(0, NECK)]);
    SND.thump(ac, out, at(2.6), fail ? 0.9 : 0.75, fail ? 48 : 70, cP);
    SND.grain(ac, out, at(2.6), { f: fail ? 260 : 640, type: 'sawtooth', noise: 0.5, bp: fail ? 520 : 1500, q: 3, d: 0.12, a: 0.32, pan: cP, att: 0.08 });
    if (A === 'R') SND.grain(ac, out, at(2.38), { f: 420, type: 'sawtooth', noise: 0.5, bp: 1000, q: 3, d: 0.08, a: 0.16, pan: cP, att: 0.1 }); // her first heave
    if (A === 'B') SND.say(ac, out, V, at(2.66), 'land', 0.5, vPan); // victim lifted and set down
    if (A === 'B') SND.say(ac, out, V, at(3.22), 'land', 0.7, vPan);
    if (A === 'I') SND.say(ac, out, A, at(2.56), 'land', 0.7, pan(doerX(2.56))); // he flops as dead weight
    if (!fail) {
      SND.say(ac, out, V, at(2.64), 'react', 0.8, vPan);   // brief, then nothing
      SND.say(ac, out, V, at(3.3), 'sink', 0.9, vPan);
      SND.grain(ac, out, at(4.62), { bp: 400, q: 1, d: 0.08, a: 0.07, pan: pan(doerX(4.6)) }); // tail laid on the floor; after this, silence
      if (A === 'B' || A === 'R') SND.say(ac, out, A, at(4.75), 'step', 0.5, pan(doerX(4.75)));
      if (A === 'O') SND.say(ac, out, A, at(4.6), 'step', 0.6, pan(doerX(4.6)));
    } else {
      // Belindo: the strain, the shrug, the twang and the pop
      SND.cloud(ac, out, at(2.65), 0.8, 30, { f: 130, glide: 0.3, type: 'sawtooth', noise: 0.6, bp: 600, q: 3, a: 0.035, d: [0.03, 0.07], spread: 0.2 }, u => u);
      SND.say(ac, out, 'B', at(3.32), 'react', 0.5, vPan);
      SND.pluck(ac, out, at(3.46), 52, 0.12, 0.7, cP);
      SND.grain(ac, out, at(3.47), { bp: 3000, q: 0.8, d: 0.03, a: 0.3, pan: cP, att: 0.05 });
      SND.grain(ac, out, at(3.47), { f: 900, glide: -0.6, d: 0.09, a: 0.2, pan: cP, att: 0.05 });
      SND.say(ac, out, A, at(3.72), 'land', 0.6, pan(doerX(3.72))); // the doer falls back
      SND.grain(ac, out, at(4.33), { bp: 600, q: 1, d: 0.1, a: 0.1, pan: vPan - 0.2 }); // the loop lands on the floor
      SND.say(ac, out, A, at(5.0), 'step', 0.5, pan(doerX(5.0)));
      SND.say(ac, out, 'B', at(4.5), 'breathe', 0.6, vPan);
    }
  }

  DEED({
    n: 12, key: 'strangling', title: 'Strangling',
    scion: 34, lineage: 'ARAP — Preserve-Shape Deformation Swarm',
    op: 'Two handle constraints on the victim\'s neck-ring vertices are pulled toward the centreline while an as-rigid-as-possible solve keeps every other triangle of the sack as close to its rest shape as it can.',
    made: 'Each sack is a 9x13 triangulated cloth mesh (192 triangles) with cotangent edge weights, its shawl, belt, wig and wheat stencil bound to the mesh as triangle colours and barycentric feature points. The room is a night boarding-house wall papered in the same rest-triangle lattice under one hanging lamp.',
    moved: 'Every frame a local-global ARAP solver (per-vertex best rotations, then one cached Cholesky solve) bends each mesh toward soft handle targets: the floor row, the two neck-ring vertices, the three crown vertices. The cord is drawn on the solved neck row and pulled by the doer\'s near ear; Belindo\'s mesh is forty times stiffer with a weak neck handle, so the same pull barely dents him.',
    contact: 2.6,
    leaves: { A: [], V: ['cinched', 'greyed'] },
    leavesFor(A, V) { return V === 'B' ? { A: [], V: [] } : { A: [], V: ['cinched', 'greyed'] }; },
    marks(t, A, V, K) { const P = stage(t, A, V, K, null); return { A: bbox(P.ao), V: bbox(P.vo) }; },
    sound(ac, out, t0, A, V, K) { soundtrack(ac, out, t0, A, V, K); },
    draw(g, t, A, V, K, opt) {
      const k = makeK(K), { sm, bump } = k;
      const layer = opt && opt.layer, on = x => !layer || layer === x;
      const carry = opt && opt.carry;
      const CA = K.CAST[A], CV = K.CAST[V];
      const MA = mesh(A, K.CAST), MV = mesh(V, K.CAST);
      if (on('bg')) backdrop(g, t, K);
      if (layer === 'bg') return;
      const fail = V === 'B';
      const P = stage(t, A, V, K, carry);
      const { vp, dp, vsol, asol, vX, aX, vo, ao, tagA, tagV } = P;

      // cord state
      const cd = CORD[A];
      const nL = V2(vo, idx(0, NECK)), nR = V2(vo, idx(NX - 1, NECK));
      const vTop = V2(vo, idx((NX - 1) / 2, TOP));
      const neckC = [(nL[0] + nR[0]) / 2, (nL[1] + nR[1]) / 2], neckHW = (nR[0] - nL[0]) / 2;
      // grip aim: doer's near ear points at the knot from reach to release
      const throwT0 = { R: 1.6, B: 1.55, I: 1.75, O: 1.45 }[A], throwT1 = 2.05, dropT1 = 2.22;
      const releaseT = fail ? 3.55 : 4.35;
      const aimK = sm(throwT0 - 0.3, throwT0, t) * (1 - sm(releaseT, releaseT + 0.25, t));
      const aim = { k: aimK * 0.85, x: (nL[0] - aX) / S, y: (FLOOR - nL[1]) / S };
      const has = (T, x) => T.indexOf(x) >= 0;
      const moodA = { alarm: 0, dead: 0, grey: has(tagA, 'greyed') ? 1 : 0, drowsy: has(tagA, 'drowsy') ? 1 : 0 }, moodV = { alarm: vp.alarm, dead: vp.dead, grey: has(tagV, 'greyed') ? 1 : 0, drowsy: has(tagV, 'drowsy') ? 1 : 0 };


      // loop position
      let loopMode = 'coil', L = null;
      if (t >= throwT0 && t < throwT1) loopMode = 'fly';
      else if (t >= throwT1 && t < dropT1) loopMode = 'drop';
      else if (t >= dropT1) loopMode = 'band';
      if (fail && t >= 3.45) loopMode = t < 3.75 ? 'pop' : 'floor';

      // victim body (back arc of a flying loop behind it)
      const preGrip = { x: 0, y: 0 };
      const aboveHead = [vTop[0], vTop[1] - 50];
      // we need the grip before drawing; compute ear geometry once from the solve
      const eRg = earGeom(MA, asol, aX, 1, moodA, aim);
      const gripS = [aX + S * eRg.e[0], FLOOR - S * eRg.e[1]];
      let lc = null, lrx = neckHW + 14, lry = 10;
      if (loopMode === 'fly') {
        const u = sm(throwT0, throwT1, t);
        const arcH = Math.max(60, gripS[1] - aboveHead[1] + 70);
        lc = [K.lerp(gripS[0], aboveHead[0], u), K.lerp(gripS[1], aboveHead[1], u) - arcH * Math.sin(Math.PI * u) * (A === 'O' && V !== 'B' ? 0.35 : 1)];
        lrx = K.lerp(16, neckHW + 22, u); lry = K.lerp(16, 9, u);
        if (A === 'I') lry = K.lerp(16, 9, u) * (0.6 + 0.4 * Math.abs(Math.cos(t * 18)));
      } else if (loopMode === 'drop') {
        const u = sm(throwT1, dropT1, t);
        lc = [K.lerp(aboveHead[0], neckC[0], u), K.lerp(aboveHead[1], neckC[1], u)];
        lrx = K.lerp(neckHW + 22, neckHW + 6, u); lry = 10;
      } else if (loopMode === 'pop') {
        const u = sm(3.45, 3.75, t);
        lc = [K.lerp(neckC[0], vTop[0] - 30, u), K.lerp(neckC[1], vTop[1] - 70, u) - 40 * Math.sin(Math.PI * u)];
        lrx = neckHW + 10 + 20 * u; lry = 12;
      } else if (loopMode === 'floor') {
        const u = sm(3.75, 4.35, t);
        const land = [vX - S * CV.w / 2 - 40, FLOOR + 10];
        const st = [vTop[0] - 30, vTop[1] - 70];
        lc = [K.lerp(st[0], land[0], u), K.lerp(st[1], land[1], u) - 120 * Math.sin(Math.PI * u)];
        lrx = K.lerp(neckHW + 30, 70, u); lry = K.lerp(12, 7, u);
      }
      // layer V: victim shadow, back arc of a flying loop, victim, its carried marks (and the cord once it is left on the neck)
      // layer A: doer shadow, doer, its carried marks, the cord while held. Full frame = bg, V, A.
      const cordOnV = !fail && t >= releaseT;
      if (on('V')) {
        shadow(g, vo, MV);
        if (lc && loopMode !== 'band' && loopMode !== 'floor') loopEllipse(g, lc[0], lc[1], lrx, lry, { c: cd.c, hi: cd.c, w: cd.w * 0.8 }, false);
        drawSack(g, V, MV, vsol, vX, moodV, null, K, tagV);
        carryMarks(g, V, MV, vo, tagV, t);
      }
      const grip = [aX + S * eRg.e[0], FLOOR - S * eRg.e[1]];
      if (on('V') && cordOnV) drawCord();
      if (on('A')) {
        shadow(g, ao, MA);
        drawSack(g, A, MA, asol, aX, moodA, aim, K, tagA);
        carryMarks(g, A, MA, ao, tagA, t);
        if (!cordOnV) { if (loopMode === 'floor') loopEllipse(g, lc[0], lc[1], lrx, lry, { c: cd.c, hi: cd.c, w: cd.w * 0.8 }, false); drawCord(); }
      }
      function drawCord() {
      let knot;
      if (loopMode === 'band') {
        // band lies on the solved neck row
        // the band lies on the solved neck row; on Belindo it cannot bite and rides up the head
        const rr = fail ? NECK + 2.4 * sm(2.65, 3.45, t) : NECK, r0 = Math.min(TOP - 1, Math.floor(rr)), rf = rr - r0;
        const row = []; for (let i = 0; i < NX; i++) { const a = V2(vo, idx(i, r0)), b = V2(vo, idx(i, r0 + 1)); row.push([a[0] * (1 - rf) + b[0] * rf, a[1] * (1 - rf) + b[1] * rf]); }
        const gap = fail ? 10 + 8 * sm(2.65, 3.4, t) : 0;
        stroke2(g, () => { g.beginPath(); row.forEach(([x, y], z) => { const xx = fail ? neckC[0] + (x - neckC[0]) * 1.07 : x; z ? g.lineTo(xx, y - (fail ? 3 : 0)) : g.moveTo(xx + gap, y - (fail ? 3 : 0)); }); }, cd);
        knot = [row[0][0] - (fail ? 8 : 2), row[0][1]];
        if (fail) { const hcx = neckC[0]; stroke2(g, () => { g.beginPath(); g.moveTo(row[0][0] - 8, row[0][1]); g.quadraticCurveTo(row[0][0] - 2, row[0][1] + 16, row[0][0] + gap + 4, row[0][1] + 4); }, cd, cd.w * 0.8); }
        g.fillStyle = cd.c; g.beginPath(); g.arc(knot[0], knot[1], cd.w * 0.9, 0, 2 * Math.PI); g.fill();
      } else if (lc) {
        loopEllipse(g, lc[0], lc[1], lrx, lry, cd, true);
        knot = [lc[0] - lrx, lc[1]];
      }
      // tail from knot to grip (or to floor once released)
      const gp = grip;
      if (loopMode === 'coil') {
        const sw = A === 'I' ? 0.25 * Math.sin(t * 3) : 0;
        if (A === 'I' && t > 1.0) { // twirl
          const ph = (t - 1.0) * 14;
          loopEllipse(g, gp[0] + 18 * Math.cos(ph), gp[1] - 10 + 6 * Math.sin(ph), 18, 9, cd, true);
          loopEllipse(g, gp[0] + 18 * Math.cos(ph), gp[1] - 10 + 6 * Math.sin(ph), 18, 9, cd, false);
        } else {
          stroke2(g, () => { g.beginPath(); g.ellipse(gp[0] + 4 + sw * 10, gp[1] + 18, 12, 18, sw, 0, Math.PI * 2); }, cd);
        }
      } else {
        let end = gp, taut = 0;
        if (loopMode === 'band') taut = sm(dropT1, 2.45, t) * (1 - sm(releaseT, releaseT + 0.3, t));
        const rel = sm(releaseT, releaseT + 0.45, t);
        if (rel > 0) { const fe = [K.lerp(gp[0], (knot[0] + gp[0]) / 2 - 10, rel), K.lerp(gp[1], FLOOR + 8, rel)]; end = fe; }
        if (loopMode === 'floor' || loopMode === 'pop') { end = [K.lerp(gp[0], gp[0] + 20, rel), K.lerp(gp[1], FLOOR + 8, rel)]; taut = 0; }
        tail(g, knot, end, taut, cd);
        if (rel > 0.98) { // tail end lies on the floor
          stroke2(g, () => { g.beginPath(); g.moveTo(end[0], end[1]); g.lineTo(end[0] - 26, end[1] + 3); }, cd);
        }
      }
      }
    },
  });
})();
