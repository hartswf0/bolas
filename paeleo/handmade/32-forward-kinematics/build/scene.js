// SCION 32 · the carved and painted parts: every visible piece is a mesh in the local frame of one joint.
// Vertex layout: position(3) normal(3) colour(3) material(1) uv(2) = 12 floats. Flat facets: the parts are carved, not turned.
(function (G) {
  'use strict';
  // materials: 0 painted wood, 1 felt, 2 brass, 3 bare/varnished wood, 4 emissive, 5 knit, 6 sky, 7 gloss black paint,
  //            8 grass/earth, 9 painted siding, 10 painted wood with hand-painted patches (the dog)
  const MAT = { paint: 0, felt: 1, brass: 2, wood: 3, glow: 4, knit: 5, sky: 6, gloss: 7, grass: 8, siding: 9, patch: 10 };
  const hex = h => [parseInt(h.slice(1, 3), 16) / 255, parseInt(h.slice(3, 5), 16) / 255, parseInt(h.slice(5, 7), 16) / 255];

  function Mesh() { this.v = []; }
  Mesh.prototype.tri = function (a, b, c, col, mat, ua, ub, uc, center) {
    const e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    let n = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
    const l = Math.hypot(...n); if (l < 1e-12) return; n = n.map(x => x / l);
    if (center) { const m = [(a[0] + b[0] + c[0]) / 3 - center[0], (a[1] + b[1] + c[1]) / 3 - center[1], (a[2] + b[2] + c[2]) / 3 - center[2]]; if (m[0] * n[0] + m[1] * n[1] + m[2] * n[2] < 0) n = n.map(x => -x); }
    for (const [p, u] of [[a, ua], [b, ub], [c, uc]]) this.v.push(p[0], p[1], p[2], n[0], n[1], n[2], col[0], col[1], col[2], mat, u[0], u[1]);
  };
  const sp = (x, e) => Math.sign(x) * Math.pow(Math.abs(x), e);
  // superquadric "carved block": r radii, e roundness (small = boxy), n facets
  Mesh.prototype.block = function (c, r, col, mat, e = [0.45, 0.45], n = [8, 12], taper = null) {
    const P = (i, j) => {
      const th = -Math.PI / 2 + Math.PI * i / n[0], ph = -Math.PI + 2 * Math.PI * j / n[1];
      let x = r[0] * sp(Math.cos(th), e[0]) * sp(Math.cos(ph), e[1]), y = r[1] * sp(Math.sin(th), e[0]), z = r[2] * sp(Math.cos(th), e[0]) * sp(Math.sin(ph), e[1]);
      if (taper) { const k = 1 + taper[0] * (y / r[1]); x *= k; z *= 1 + taper[1] * (y / r[1]); }
      return [c[0] + x, c[1] + y, c[2] + z];
    };
    for (let i = 0; i < n[0]; i++) for (let j = 0; j < n[1]; j++) {
      const a = P(i, j), b = P(i + 1, j), cc = P(i + 1, j + 1), d = P(i, j + 1);
      const ua = [j / n[1], i / n[0]], ub = [j / n[1], (i + 1) / n[0]], uc = [(j + 1) / n[1], (i + 1) / n[0]], ud = [(j + 1) / n[1], i / n[0]];
      this.tri(a, b, cc, col, mat, ua, ub, uc, c); this.tri(a, cc, d, col, mat, ua, uc, ud, c);
    }
    return this;
  };
  // cylinder along an axis ('x','y','z') from s to e, radius r
  Mesh.prototype.cyl = function (c, axis, s, e, r, col, mat, n = 14) {
    const pt = (t, ang) => { const u = r * Math.cos(ang), w = r * Math.sin(ang); if (axis === 'z') return [c[0] + u, c[1] + w, t]; if (axis === 'y') return [c[0] + u, t, c[2] + w]; return [t, c[1] + u, c[2] + w]; };
    const mid = axis === 'z' ? [c[0], c[1], (s + e) / 2] : axis === 'y' ? [c[0], (s + e) / 2, c[2]] : [(s + e) / 2, c[1], c[2]];
    for (let k = 0; k < n; k++) {
      const a0 = 2 * Math.PI * k / n, a1 = 2 * Math.PI * (k + 1) / n;
      const p00 = pt(s, a0), p01 = pt(s, a1), p10 = pt(e, a0), p11 = pt(e, a1);
      this.tri(p00, p10, p11, col, mat, [0, 0], [0, 1], [1, 1], mid); this.tri(p00, p11, p01, col, mat, [0, 0], [1, 1], [1, 0], mid);
      const cs = pt(s, 0), ce = pt(e, 0);
      const C0 = axis === 'z' ? [c[0], c[1], s] : axis === 'y' ? [c[0], s, c[2]] : [s, c[1], c[2]];
      const C1 = axis === 'z' ? [c[0], c[1], e] : axis === 'y' ? [c[0], e, c[2]] : [e, c[1], c[2]];
      this.tri(C0, p01, p00, col, mat, [0.5, 0.5], [0, 0], [0, 0], mid); this.tri(C1, p10, p11, col, mat, [0.5, 0.5], [0, 0], [0, 0], mid);
    }
    return this;
  };
  Mesh.prototype.box = function (mn, mx, col, mat, uvScale = 1) {
    const c = [(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2];
    const V = (i, j, k) => [i ? mx[0] : mn[0], j ? mx[1] : mn[1], k ? mx[2] : mn[2]];
    const faces = [[[0, 0, 0], [0, 1, 0], [0, 1, 1], [0, 0, 1]], [[1, 0, 0], [1, 1, 0], [1, 1, 1], [1, 0, 1]], [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]], [[0, 1, 0], [1, 1, 0], [1, 1, 1], [0, 1, 1]], [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]]];
    for (const f of faces) {
      const p = f.map(q => V(...q));
      const uvs = p.map(q => [(q[0] + q[2]) * uvScale, q[1] * uvScale]);
      this.tri(p[0], p[1], p[2], col, mat, uvs[0], uvs[1], uvs[2], c); this.tri(p[0], p[2], p[3], col, mat, uvs[0], uvs[2], uvs[3], c);
    }
    return this;
  };
  // a disc facing +/- an axis (painted eyes, buttons)
  Mesh.prototype.disc = function (c, axis, r, col, mat, n = 16) {
    for (let k = 0; k < n; k++) {
      const a0 = 2 * Math.PI * k / n, a1 = 2 * Math.PI * (k + 1) / n;
      const q = a => axis === 'z' ? [c[0] + r * Math.cos(a), c[1] + r * Math.sin(a), c[2]] : axis === 'x' ? [c[0], c[1] + r * Math.cos(a), c[2] + r * Math.sin(a)] : [c[0] + r * Math.cos(a), c[1], c[2] + r * Math.sin(a)];
      const p0 = q(a0), p1 = q(a1);
      const n0 = axis === 'z' ? [c[0], c[1], c[2] - Math.sign(c[2] || 1)] : axis === 'x' ? [c[0] - 1, c[1], c[2]] : [c[0], c[1] - 1, c[2]];
      this.tri(c, p0, p1, col, mat, [0, 0], [1, 0], [1, 1], n0);
    }
    return this;
  };

  // ---------------- the dog: a carved, painted, pinned wooden toy ----------------
  const CREAM = hex('#efe4cf'), BLACK = hex('#1d1a1a'), RED = hex('#b3262a'), BRASS = hex('#c99a3c'), GOLD = hex('#e6b84a');
  const FELT = hex('#9e1f2c'), STITCH = hex('#f0c75a');
  function dogParts(R) {
    const P = {}, add = (j, fn) => { P[j] = P[j] || new Mesh(); fn(P[j]); };
    const L1 = R.L1, L2 = R.L2, PH = R.PAW_H;
    add('pelvis', m => { m.block([-0.035, 0.02, 0], [0.13, 0.092, 0.086], CREAM, MAT.patch, [0.45, 0.45], [8, 14], [0.0, 0.1]); m.cyl([0, 0, 0], 'z', -0.098, 0.098, 0.012, BRASS, MAT.brass); });
    add('waist', m => {
      m.block([0.112, 0.018, 0], [0.14, 0.104, 0.092], CREAM, MAT.paint, [0.45, 0.45], [8, 14], [-0.12, 0.08]);
      m.cyl([0, 0.0, 0], 'z', -0.1, 0.1, 0.013, BRASS, MAT.brass);   // the waist pin, both sides
      m.cyl([0.17, -0.037, 0], 'z', -0.1, 0.1, 0.012, BRASS, MAT.brass);  // shoulder axle
    });
    add('neck', m => { m.block([0.055, 0.0, 0], [0.075, 0.05, 0.045], CREAM, MAT.paint, [0.5, 0.5], [6, 10]); m.cyl([0, 0, 0], 'z', -0.058, 0.058, 0.01, BRASS, MAT.brass); });
    add('head', m => {
      m.block([0.0, 0.0, 0], [0.08, 0.07, 0.064], CREAM, MAT.paint, [0.5, 0.5], [8, 12]);
      m.block([0.095, -0.024, 0], [0.075, 0.038, 0.04], CREAM, MAT.paint, [0.5, 0.5], [6, 10], [0.15, 0.1]);
      m.block([0.168, -0.008, 0], [0.019, 0.017, 0.021], BLACK, MAT.gloss, [0.8, 0.8], [6, 8]);       // nose bead
      m.block([0.12, -0.056, 0], [0.045, 0.008, 0.03], RED, MAT.paint, [0.5, 0.5], [4, 8]);          // painted mouth line
      for (const s of [1, -1]) {
        m.block([0.04, 0.02, s * 0.057], [0.016, 0.016, 0.007], hex('#fbf6ea'), MAT.paint, [0.9, 0.9], [6, 10]);
        m.block([0.045, 0.02, s * 0.0635], [0.009, 0.01, 0.003], BLACK, MAT.gloss, [0.9, 0.9], [6, 10]);
        m.cyl([-0.03, 0.058, 0], 'z', s * 0.03, s * 0.066, 0.007, BRASS, MAT.brass, 10);           // ear pins
      }
      m.cyl([0, 0, 0], 'y', -0.075, -0.05, 0.016, BRASS, MAT.brass, 12);                             // swivel peg
    });
    for (const s of ['R', 'L']) {
      const sg = s === 'R' ? 1 : -1;
      add('ear' + s + '0', m => m.block([0.0, -0.03, 0], [0.04, 0.038, 0.008], BLACK, MAT.paint, [0.6, 0.45], [6, 8], [0.25, 0]));
      add('ear' + s + '1', m => { m.block([0.0, -0.028, 0], [0.04, 0.034, 0.007], BLACK, MAT.paint, [0.7, 0.6], [6, 8], [0.3, 0]); m.cyl([0, 0, 0], 'z', -0.009, 0.009, 0.005, BRASS, MAT.brass, 8); });
      // legs: flat carved boards with a brass pin at every pivot, each child one board further out
      for (const [hip, knee, paw, front] of [['shoulder' + s, 'elbow' + s, 'fpaw' + s, true], ['hip' + s, 'knee' + s, 'hpaw' + s, false]]) {
        add(hip, m => { m.block([front ? 0.004 : 0.0, -L1 / 2 + 0.012, 0], [front ? 0.038 : 0.048, L1 / 2 + 0.034, 0.017], CREAM, MAT.paint, [0.35, 0.5], [6, 10], front ? null : [0.35, 0]); m.cyl([0, 0, 0], 'z', 0, sg * 0.03, 0.0125, BRASS, MAT.brass); });
        add(knee, m => { m.block([0, -L2 / 2, 0], [0.029, L2 / 2 + 0.016, 0.0155], CREAM, MAT.paint, [0.35, 0.5], [6, 10]); m.cyl([0, 0, 0], 'z', 0, sg * 0.026, 0.0105, BRASS, MAT.brass); });
        add(paw, m => { m.block([0.02, -PH / 2 + 0.002, 0], [0.045, PH / 2 + 0.002, 0.024], BLACK, MAT.paint, [0.35, 0.5], [6, 10]); m.cyl([0, 0, 0], 'z', 0, sg * 0.03, 0.009, BRASS, MAT.brass); });
      }
      add('flap' + s + '0', m => { m.box([-0.125, -0.06, -0.006], [0.125, 0.004, 0.006], FELT, MAT.felt); });
      add('flap' + s + '1', m => { m.box([-0.118, -0.05, -0.0055], [0.118, 0.002, 0.0055], FELT, MAT.felt); m.box([-0.118, -0.052, -0.0065], [0.118, -0.044, 0.0065], STITCH, MAT.felt); });
    }
    add('cloth', m => { m.box([-0.13, -0.004, -0.088], [0.13, 0.01, 0.088], FELT, MAT.felt); m.cyl([0, 0.01, 0], 'y', 0.006, 0.02, 0.016, GOLD, MAT.brass, 12); });
    const beads = [[0.026, RED], [0.024, CREAM], [0.022, RED], [0.02, CREAM], [0.019, BLACK]];
    beads.forEach(([r, col], k) => add('tail' + k, m => { m.block([-0.024, 0, 0], [r * 1.1, r, r], col, MAT.paint, [0.75, 0.75], [6, 8]); m.cyl([0, 0, 0], 'x', -0.05, 0.0, 0.0045, hex('#3a2a20'), MAT.paint, 6); }));
    return P;
  }

  // ---------------- the person: a carved figure in a knitted cardigan ----------------
  const SKIN = hex('#d9a27a'), HAIR = hex('#3b2418'), MUSTARD = hex('#c58b23'), NAVY = hex('#27304d'), SHOE = hex('#4a2c1c'), SHIRT = hex('#e9e3d3');
  function personParts() {
    const P = {}, add = (j, fn) => { P[j] = P[j] || new Mesh(); fn(P[j]); };
    add('pelvis', m => { m.block([0, 0.0, 0], [0.12, 0.1, 0.17], NAVY, MAT.paint, [0.35, 0.4], [8, 12]); m.cyl([0, -0.04, 0], 'z', -0.2, 0.2, 0.018, BRASS, MAT.brass); });
    add('spine', m => { m.block([0, 0.1, 0], [0.125, 0.12, 0.18], MUSTARD, MAT.knit, [0.35, 0.4], [8, 12]); m.cyl([0, 0, 0], 'z', -0.19, 0.19, 0.016, BRASS, MAT.brass); });
    add('chest', m => {
      m.block([0, 0.1, 0], [0.135, 0.15, 0.205], MUSTARD, MAT.knit, [0.35, 0.4], [8, 12]);
      m.block([0.1, 0.12, 0], [0.04, 0.12, 0.05], SHIRT, MAT.paint, [0.5, 0.5], [6, 8]);
      for (const y of [0.04, 0.12, 0.2]) m.cyl([0.135, y, 0.055], 'x', 0.12, 0.142, 0.012, hex('#6b3a14'), MAT.wood, 10);   // cardigan buttons
      m.cyl([0, 0.16, 0], 'z', -0.215, 0.215, 0.02, BRASS, MAT.brass);
    });
    add('neck', m => m.block([0, 0.04, 0], [0.045, 0.05, 0.045], SKIN, MAT.paint, [0.6, 0.6], [6, 10]));
    add('head', m => {
      m.block([0.0, 0.11, 0], [0.098, 0.12, 0.092], SKIN, MAT.paint, [0.55, 0.6], [8, 12]);
      m.block([-0.02, 0.16, 0], [0.104, 0.09, 0.098], HAIR, MAT.paint, [0.5, 0.5], [8, 12]);
      m.block([-0.075, 0.11, 0], [0.04, 0.08, 0.08], HAIR, MAT.paint, [0.5, 0.5], [6, 10]);
      for (const s of [1, -1]) m.block([0.093, 0.125, s * 0.036], [0.006, 0.011, 0.009], BLACK, MAT.gloss, [0.9, 0.9], [6, 8]);
      m.block([0.102, 0.09, 0], [0.018, 0.022, 0.014], SKIN, MAT.paint, [0.6, 0.6], [6, 8]);
      m.block([0.06, 0.03, 0], [0.04, 0.02, 0.055], hex('#3a1212'), MAT.paint, [0.6, 0.6], [6, 8]);   // the mouth, behind the jaw
    });
    add('jaw', m => { m.block([0.03, -0.012, 0], [0.05, 0.022, 0.07], SKIN, MAT.paint, [0.55, 0.55], [6, 10]); m.cyl([0, 0, 0], 'z', -0.078, 0.078, 0.007, BRASS, MAT.brass, 8); });
    for (const s of ['R', 'L']) {
      const sg = s === 'R' ? 1 : -1;
      add('hem' + s, m => m.box([-0.02, -0.2, -0.07], [0.012, 0.0, 0.07], MUSTARD, MAT.knit));
      add('shoulder' + s, m => { m.block([0, -0.14, 0], [0.058, 0.165, 0.058], MUSTARD, MAT.knit, [0.45, 0.5], [6, 10]); });
      add('elbow' + s, m => { m.block([0, -0.1, 0], [0.05, 0.125, 0.05], MUSTARD, MAT.knit, [0.45, 0.5], [6, 10]); m.cyl([0, 0, 0], 'z', 0, sg * 0.065, 0.014, BRASS, MAT.brass); });
      add('cuff' + s, m => m.block([0, -0.03, 0], [0.064, 0.045, 0.064], hex('#a8731a'), MAT.knit, [0.6, 0.35], [6, 12], [0.25, 0.25]));
      add('wrist' + s, m => m.block([0.005, -0.065, 0], [0.042, 0.072, 0.024], SKIN, MAT.paint, [0.5, 0.55], [6, 10]));
      add('thumb' + s, m => m.block([0.0, -0.02, 0], [0.013, 0.03, 0.013], SKIN, MAT.paint, [0.6, 0.6], [4, 8]));
      add('hip' + s, m => { m.block([0, -0.21, 0], [0.078, 0.23, 0.078], NAVY, MAT.paint, [0.45, 0.5], [6, 10]); });
      add('knee' + s, m => { m.block([0, -0.21, 0], [0.064, 0.225, 0.064], NAVY, MAT.paint, [0.45, 0.5], [6, 10]); m.cyl([0, 0, 0], 'z', 0, sg * 0.08, 0.015, BRASS, MAT.brass); });
      add('ankle' + s, m => m.block([0.055, -0.045, 0], [0.12, 0.042, 0.052], SHOE, MAT.paint, [0.4, 0.5], [6, 10]));
    }
    return P;
  }

  // ---------------- the place: a painted wooden house and porch at dusk ----------------
  function world() {
    const m = new Mesh();
    const WALL = hex('#3c5a66'), TRIM = hex('#e8dcc2'), PORCH = hex('#6f7f86'), DOOR = hex('#7c2b23'), INWALL = hex('#e0b36a'), INFLOOR = hex('#9a6234');
    // porch boards (run out from the wall), with a gap between boards
    for (let k = 0; k < 48; k++) {
      const x0 = -3.6 + k * 0.146, sh = 0.86 + 0.14 * ((k * 37) % 7) / 7;
      m.box([x0, -0.045, 0.0], [x0 + 0.138, 0.0, 4.75], PORCH.map(c => c * sh), MAT.wood, 1.0);
    }
    m.box([-3.62, -0.5, 0], [3.42, -0.045, 4.78], hex('#2a2f38'), MAT.paint);            // porch skirt
    for (const [z0, y0] of [[4.78, -0.17], [5.08, -0.34]]) m.box([-1.0, y0 - 0.16, z0], [1.2, y0, z0 + 0.3], PORCH.map(c => c * 0.9), MAT.wood);
    // ground and distant toy trees, picket fence
    m.box([-30, -0.62, -30], [30, -0.5, 30], hex('#2f3a2c'), MAT.grass, 0.2);
    const trees = [[-6.5, -3.5, 1.6], [-8.6, -6.2, 2.2], [-5.4, -8.5, 1.9], [-11, -2.5, 2.6], [-9.5, 1.5, 1.8], [-13, -9, 3.0], [-7.8, 4.5, 2.1], [6.5, -6, 2.5], [-15, 3, 2.4]];
    for (const [x, z, h] of trees) {
      const tm = new Mesh(); tm.block([x, -0.5 + h * 0.62, z], [h * 0.3, h * 0.42, h * 0.3], hex('#22422f'), MAT.paint, [1.4, 1.0], [6, 8]);
      m.v.push(...tm.v); m.cyl([x, 0, z], 'y', -0.5, -0.5 + h * 0.3, 0.06 * h, hex('#4b3323'), MAT.wood, 8);
    }
    for (let k = 0; k < 26; k++) { const x = -4.2 - k * 0.28; m.box([x, -0.5, 3.0], [x + 0.09, 0.35 + 0.05 * (k % 2), 3.04], TRIM.map(c => c * 0.75), MAT.paint); }
    m.box([-11.5, 0.05, 2.98], [-4.1, 0.11, 3.0], TRIM.map(c => c * 0.7), MAT.paint);
    // house: front wall with a door hole and a window hole (Z from -0.12 to 0), painted siding
    const Z0 = -0.12, H = 2.62;
    m.box([-3.6, 0, Z0], [-0.53, H, 0], WALL, MAT.siding);
    m.box([0.53, 0, Z0], [1.15, H, 0], WALL, MAT.siding);
    m.box([2.15, 0, Z0], [3.4, H, 0], WALL, MAT.siding);
    m.box([1.15, 0, Z0], [2.15, 0.92, 0], WALL, MAT.siding);
    m.box([1.15, 1.86, Z0], [2.15, H, 0], WALL, MAT.siding);
    m.box([-0.53, 2.06, Z0], [0.53, H, 0], WALL, MAT.siding);
    // side wall (left corner) and back, so the house reads as a box
    m.box([-3.6, 0, -4.2], [-3.48, H, Z0], WALL.map(c => c * 0.8), MAT.siding);
    m.box([3.28, 0, -4.2], [3.4, H, Z0], WALL.map(c => c * 0.8), MAT.siding);
    // roof: two slabs
    const roof = hex('#2b2328');
    for (let k = 0; k < 10; k++) { const y = H + k * 0.09, z = 0.35 - k * 0.24; m.box([-3.8, y, z - 0.3], [3.6, y + 0.1, z + 0.02], roof.map(c => c * (0.9 + 0.1 * (k % 2))), MAT.wood); }
    // door frame (trim), sill board, window frame
    m.box([-0.6, 0, -0.14], [-0.46, 2.12, 0.035], TRIM, MAT.paint); m.box([0.46, 0, -0.14], [0.6, 2.12, 0.035], TRIM, MAT.paint);
    m.box([-0.66, 2.0, -0.14], [0.66, 2.16, 0.045], TRIM, MAT.paint);
    m.box([-0.5, 0, -0.15], [0.5, 0.024, 0.07], hex('#b49268'), MAT.wood);                       // the sill
    m.box([1.08, 0.86, -0.13], [2.22, 0.94, 0.06], TRIM, MAT.paint); m.box([1.08, 1.86, -0.13], [2.22, 1.94, 0.03], TRIM, MAT.paint);
    m.box([1.08, 0.92, -0.13], [1.16, 1.88, 0.03], TRIM, MAT.paint); m.box([2.14, 0.92, -0.13], [2.22, 1.88, 0.03], TRIM, MAT.paint);
    m.box([1.62, 0.92, -0.08], [1.68, 1.88, -0.04], TRIM, MAT.paint); m.box([1.16, 1.37, -0.08], [2.14, 1.42, -0.04], TRIM, MAT.paint);
    m.box([1.15, 0.92, -0.1], [2.15, 1.87, -0.09], hex('#ffb35a'), MAT.glow);
    // interior: floor, walls, ceiling, rug, lamp, chair, picture
    m.box([-3.48, -0.04, -4.2], [3.28, 0.0, Z0], INFLOOR, MAT.wood, 1.0);
    m.box([-3.48, 0, -3.1], [3.28, H, -3.0], INWALL, MAT.siding);
    m.box([-3.48, H - 0.05, -3.1], [3.28, H, Z0], INWALL.map(c => c * 0.8), MAT.paint);
    m.box([-1.6, 0, -3.0], [-1.5, H, Z0], INWALL.map(c => c * 0.95), MAT.siding);       // inner side walls framing the room
    m.box([1.9, 0, -3.0], [2.0, H, Z0], INWALL.map(c => c * 0.95), MAT.siding);
    m.box([-0.75, 0.0, -1.9], [0.75, 0.008, -0.35], hex('#8c2a2a'), MAT.felt);                     // rug
    m.box([-0.68, 0.0, -1.83], [0.68, 0.01, -0.42], hex('#b5493a'), MAT.felt);
    m.cyl([-0.02, 0, -1.45], 'y', 2.08, 2.62, 0.008, hex('#222222'), MAT.paint, 6);                       // pendant lamp
    const shade = new Mesh(); shade.block([-0.02, 2.06, -1.45], [0.17, 0.08, 0.17], hex('#ffd9a0'), MAT.glow, [1.0, 1.0], [6, 12], [-0.5, -0.5]); m.v.push(...shade.v);
    m.cyl([-1.05, 0, -2.4], 'y', 0, 0.75, 0.2, hex('#5a3a28'), MAT.wood, 14);                                // a round side table
    m.cyl([-1.05, 0, -2.4], 'y', 0.75, 0.79, 0.32, hex('#6a442c'), MAT.wood, 18);
    m.cyl([-1.05, 0, -2.4], 'y', 0.79, 0.95, 0.06, hex('#d8d0c0'), MAT.paint, 10);
    m.box([0.6, 0.0, -2.6], [1.1, 0.45, -2.15], hex('#6a3e22'), MAT.wood);                              // chair
    m.box([0.6, 0.45, -2.66], [1.1, 1.0, -2.6], hex('#6a3e22'), MAT.wood);
    m.box([-0.35, 1.25, -2.995], [0.35, 1.75, -2.98], hex('#3b2a1c'), MAT.wood);                           // picture
    m.box([-0.3, 1.3, -2.98], [0.3, 1.7, -2.975], hex('#4d7a6a'), MAT.paint);
    // sky dome
    const sky = new Mesh(); sky.block([0, 0, 0], [60, 60, 60], [1, 1, 1], MAT.sky, [1, 1], [10, 20]);
    m.v.push(...sky.v);
    return m;
  }
  function doorLeaf() { // in the hinge frame: hinge pin at origin, the leaf runs along +x
    const m = new Mesh(), DOOR = hex('#7c2b23');
    m.box([0.0, 0.0, -0.022], [0.92, 1.99, 0.022], DOOR, MAT.paint);
    for (const [x0, y0, x1, y1] of [[0.1, 1.08, 0.43, 1.88], [0.5, 1.08, 0.83, 1.88], [0.1, 0.12, 0.43, 0.94], [0.5, 0.12, 0.83, 0.94]]) {
      m.box([x0, y0, 0.022], [x1, y1, 0.03], DOOR.map(c => c * 1.15), MAT.paint); m.box([x0, y0, -0.03], [x1, y1, -0.022], DOOR.map(c => c * 1.15), MAT.paint);
    }
    m.block([0.84, 1.0, 0.045], [0.026, 0.026, 0.02], GOLD, MAT.brass, [0.8, 0.8], [6, 10]); m.block([0.84, 1.0, -0.045], [0.026, 0.026, 0.02], GOLD, MAT.brass, [0.8, 0.8], [6, 10]);
    m.cyl([0, 0, 0], 'y', 0.2, 0.32, 0.012, BRASS, MAT.brass, 8); m.cyl([0, 0, 0], 'y', 1.65, 1.77, 0.012, BRASS, MAT.brass, 8);
    return m;
  }
  const api = { MAT, Mesh, dogParts, personParts, world, doorLeaf, hex };
  if (typeof module !== 'undefined') module.exports = api; else G.SCENE = api;
})(typeof window !== 'undefined' ? window : globalThis);
