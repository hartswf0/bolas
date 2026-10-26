/* SCION-24 · the set (a house drawn in section, a porch at dusk) and the person (a small parametric portrait rig).
   All drawn here with canvas paths; nothing is loaded from outside. World metres as in rig.js. */
(function (G) {
  'use strict';
  const R = G.Rig, { lerp, clamp, smooth, rgb, mix, capsule, union, ellPoly, sPolys, smoothPath, ccw, clipTo, circlePts } = R;
  const KZ = R.KZ;
  const WALL = { inner: -0.22, outer: 0.4, head: 2.05, ceil: 2.48, cut: 0.45, jamb: 0.45 };
  const SILL = { x0: -0.22, x1: 0.5, h: 0.035 };
  const PORCH = { x1: 4.9, zf: -1.6, zn: 1.25, deck: 0, ground: -0.45 };
  const LAMP = [-1.95, 1.05, -1.25];

  function mk(cam) {
    const K = cam.S * cam.zoom;
    const P = (x, y, z = 0) => [cam.W / 2 + (x - cam.cx) * K, cam.H / 2 - (y - KZ * z - cam.cy) * K];
    return { K, P };
  }
  function poly(ctx, pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath(); }
  function rand(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

  // light: how much door light lands at a porch point (x, z), given door opening 0..1
  function spill(x, z, open, blockers) {
    if (x < WALL.outer - 0.05) return 0;
    const w0 = lerp(0.12, 0.45, open);              // half-width of the beam in z at the sill
    const zc = lerp(0.33, 0.0, open);               // ajar: the gap is on the near side of the opening
    const half = w0 + (x - WALL.outer) * 0.16;
    const inZ = 1 - smooth(half * 0.75, half * 1.15, Math.abs(z - zc));
    const fall = 1 / (1 + Math.pow(Math.max(0, x - 0.2) / 2.1, 2));
    return clamp(inZ * fall * lerp(0.28, 1, open) * (blockers === undefined ? 1 : blockers));
  }

  function drawSky(ctx, cam, t) {
    const { K, P } = mk(cam);
    const g = ctx.createLinearGradient(0, 0, 0, cam.H);
    g.addColorStop(0, '#141a3c'); g.addColorStop(0.35, '#2a3266'); g.addColorStop(0.62, '#6b5a86'); g.addColorStop(0.8, '#c98a7c'); g.addColorStop(1, '#e8b48a');
    ctx.fillStyle = g; ctx.fillRect(0, 0, cam.W, cam.H);
    // stars (fixed seed), twinkling slowly
    const r = rand(24);
    for (let i = 0; i < 70; i++) {
      const x = r() * cam.W, y = r() * cam.H * 0.45, a = 0.25 + 0.5 * r() * (0.7 + 0.3 * Math.sin(t * (0.5 + r()) + i));
      ctx.fillStyle = `rgba(235,235,255,${a * 0.7})`; ctx.fillRect(x, y, 1.4, 1.4);
    }
    // moon, waxing crescent, in the sky over the porch
    const m = P(3.9, 2.55, -6);
    ctx.save(); ctx.beginPath(); ctx.arc(m[0], m[1], 0.16 * K, 0, 7); ctx.fillStyle = '#f4ead2'; ctx.shadowColor = 'rgba(244,234,210,0.6)'; ctx.shadowBlur = 0.25 * K; ctx.fill(); ctx.restore();
    ctx.beginPath(); ctx.arc(m[0] + 0.07 * K, m[1] - 0.03 * K, 0.15 * K, 0, 7); ctx.fillStyle = '#2d3568'; ctx.fill();
  }
  function drawYard(ctx, cam, t) {
    const { K, P } = mk(cam);
    // far tree line and hills as layered silhouettes (drawn, seeded)
    const hz = P(0, 0.95, 0)[1];
    const r = rand(7);
    ctx.fillStyle = '#3c3a63';
    ctx.beginPath(); ctx.moveTo(0, hz + 30); for (let x = 0; x <= cam.W + 20; x += 20) ctx.lineTo(x, hz + 10 - 22 * Math.sin(x * 0.004 + 1) - 10 * Math.sin(x * 0.013)); ctx.lineTo(cam.W, cam.H); ctx.lineTo(0, cam.H); ctx.fill();
    // trees: clustered crowns on short trunks, a band at the yard's edge
    const trees = [[0.5, 1.5, 0.9], [1.4, 2.1, 1.2], [2.6, 1.4, 0.8], [3.4, 2.4, 1.3], [4.5, 1.8, 1.0], [5.6, 2.2, 1.2]];
    ctx.fillStyle = '#25264a';
    for (const [x, h, w] of trees) {
      const base = P(x, 0.55, -3);
      const sc = w * K * 0.5;
      ctx.fillRect(base[0] - 0.04 * K, base[1] - h * 0.45 * K, 0.08 * K, h * 0.45 * K);
      ctx.beginPath();
      for (let j = 0; j < 7; j++) { const ang = j / 7 * Math.PI * 2, rr = sc * (0.55 + 0.25 * r()); const cx = base[0] + Math.cos(ang) * sc * 0.55, cy = base[1] - h * 0.62 * K + Math.sin(ang) * h * 0.28 * K; ctx.moveTo(cx + rr, cy); ctx.arc(cx, cy, rr, 0, 7); }
      ctx.fill();
    }
    ctx.fillStyle = '#1c1d3a'; ctx.fillRect(0, hz + 28, cam.W, cam.H);
    const yg = ctx.createLinearGradient(0, hz + 20, 0, cam.H); yg.addColorStop(0, '#20223e'); yg.addColorStop(1, '#14152a');
    ctx.fillStyle = yg; ctx.fillRect(0, hz + 26, cam.W, cam.H);
  }
  function drawRailing(ctx, cam) {
    const { K, P } = mk(cam);
    const z = PORCH.zf, col = '#262640', line = '#14142a';
    ctx.fillStyle = col; ctx.strokeStyle = line; ctx.lineWidth = Math.max(1, 0.008 * K);
    for (let x = 0.7; x <= 4.85; x += 1.38) { const a = P(x - 0.05, 0, z), b = P(x + 0.05, 0.98, z); ctx.fillRect(a[0], b[1], b[0] - a[0], a[1] - b[1]); ctx.strokeRect(a[0], b[1], b[0] - a[0], a[1] - b[1]); }
    for (let x = 0.45; x <= 4.85; x += 0.23) { const a = P(x - 0.015, 0, z), b = P(x + 0.015, 0.9, z); ctx.fillRect(a[0], b[1], b[0] - a[0], a[1] - b[1]); }
    const a = P(WALL.outer, 0.9, z), b = P(PORCH.x1 + 0.1, 0.98, z); ctx.fillRect(a[0], b[1], b[0] - a[0], a[1] - b[1]); ctx.strokeRect(a[0], b[1], b[0] - a[0], a[1] - b[1]);
    const c = P(WALL.outer, 0.12, z), d = P(PORCH.x1 + 0.1, 0.16, z); ctx.fillRect(c[0], d[1], d[0] - c[0], c[1] - d[1]);
  }
  function drawInterior(ctx, cam, S) {
    const { K, P } = mk(cam);
    const xl = -6, xi = WALL.inner;
    // back wall (warm plaster, lamplit)
    const bw = [P(xl, 0, -1.6), P(xi, 0, -1.6), P(xi, WALL.ceil, -1.6), P(xl, WALL.ceil, -1.6)];
    const L0 = P(LAMP[0], LAMP[1], LAMP[2]);
    const g = ctx.createRadialGradient(L0[0], L0[1] - 0.2 * K, 0.05 * K, L0[0], L0[1], 2.6 * K);
    g.addColorStop(0, '#f6cf8e'); g.addColorStop(0.35, '#c98b52'); g.addColorStop(1, '#5e3a2a');
    poly(ctx, bw); ctx.fillStyle = g; ctx.fill();
    // wainscot
    const wa = [P(xl, 0, -1.6), P(xi, 0, -1.6), P(xi, 0.85, -1.6), P(xl, 0.85, -1.6)];
    poly(ctx, wa); ctx.fillStyle = 'rgba(70,36,24,0.45)'; ctx.fill();
    ctx.strokeStyle = 'rgba(60,30,20,0.6)'; ctx.lineWidth = Math.max(1, 0.01 * K); ctx.beginPath(); const w1 = P(xl, 0.86, -1.6), w2 = P(xi, 0.86, -1.6); ctx.moveTo(w1[0], w1[1]); ctx.lineTo(w2[0], w2[1]); ctx.stroke();
    // a framed picture
    const f1 = P(-1.15, 1.35, -1.6), f2 = P(-0.65, 1.75, -1.6);
    ctx.fillStyle = '#3b2416'; ctx.fillRect(f1[0], f2[1], f2[0] - f1[0], f1[1] - f2[1]);
    ctx.fillStyle = '#8a6a4a'; ctx.fillRect(f1[0] + 0.03 * K, f2[1] + 0.03 * K, f2[0] - f1[0] - 0.06 * K, f1[1] - f2[1] - 0.06 * K);
    ctx.fillStyle = 'rgba(60,70,60,0.7)'; ctx.beginPath(); ctx.moveTo(f1[0] + 0.03 * K, f1[1] - 0.03 * K); ctx.lineTo(lerp(f1[0], f2[0], 0.4), lerp(f1[1], f2[1], 0.6)); ctx.lineTo(lerp(f1[0], f2[0], 0.7), lerp(f1[1], f2[1], 0.4)); ctx.lineTo(f2[0] - 0.03 * K, f1[1] - 0.03 * K); ctx.fill();
    // floor (boards) from the back wall to the cut
    const fl = [P(xl, 0, -1.6), P(xi, 0, -1.6), P(xi, 0, WALL.cut), P(xl, 0, WALL.cut)];
    poly(ctx, fl); const fg = ctx.createLinearGradient(0, fl[0][1], 0, fl[2][1]); fg.addColorStop(0, '#7a4a2c'); fg.addColorStop(1, '#4a2c1c'); ctx.fillStyle = fg; ctx.fill();
    ctx.strokeStyle = 'rgba(40,20,12,0.5)'; ctx.lineWidth = 1;
    for (let z = -1.6; z < WALL.cut; z += 0.22) { const a = P(xl, 0, z), b = P(xi, 0, z); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    // rug
    const rg = [P(-1.7, 0.003, -0.7), P(-0.4, 0.003, -0.7), P(-0.4, 0.003, 0.35), P(-1.7, 0.003, 0.35)];
    poly(ctx, rg); ctx.fillStyle = 'rgba(120,40,34,0.75)'; ctx.fill(); ctx.strokeStyle = 'rgba(220,170,110,0.35)'; ctx.lineWidth = Math.max(1, 0.012 * K); ctx.stroke();
    // lamp: table + shade, glowing
    const tb = P(LAMP[0] - 0.22, 0.7, LAMP[2]), tb2 = P(LAMP[0] + 0.22, 0.74, LAMP[2]);
    ctx.fillStyle = '#3a2417'; ctx.fillRect(tb[0], tb2[1], tb2[0] - tb[0], 0.04 * K);
    for (const dx of [-0.17, 0.17]) { const a = P(LAMP[0] + dx, 0, LAMP[2]), b = P(LAMP[0] + dx, 0.7, LAMP[2]); ctx.fillRect(a[0] - 0.015 * K, b[1], 0.03 * K, a[1] - b[1]); }
    const lb = P(LAMP[0], 0.74, LAMP[2]), lt = P(LAMP[0], LAMP[1] - 0.12, LAMP[2]);
    ctx.fillStyle = '#2a1a12'; ctx.fillRect(lb[0] - 0.012 * K, lt[1], 0.024 * K, lb[1] - lt[1]);
    ctx.save(); ctx.shadowColor = 'rgba(255,200,120,0.9)'; ctx.shadowBlur = 0.5 * K;
    const s1 = P(LAMP[0] - 0.16, LAMP[1] - 0.12, LAMP[2]), s2 = P(LAMP[0] + 0.16, LAMP[1] - 0.12, LAMP[2]), s3 = P(LAMP[0] + 0.1, LAMP[1] + 0.12, LAMP[2]), s4 = P(LAMP[0] - 0.1, LAMP[1] + 0.12, LAMP[2]);
    poly(ctx, [s1, s2, s3, s4]); ctx.fillStyle = '#ffd99a'; ctx.fill(); ctx.restore();
  }
  function drawDoor(ctx, cam, S) {
    const { K, P } = mk(cam);
    // the door hangs on the inner face at the far jamb and swings into the room. ang: 0 shut .. 100 deg open
    const a = S.doorAng * Math.PI / 180, hx = WALL.inner, hz = -WALL.jamb, w = 0.88;
    const fx = hx - w * Math.sin(a), fz = hz + w * Math.cos(a);
    const q = [P(hx, 0.02, hz), P(fx, 0.02, fz), P(fx, 2.02, fz), P(hx, 2.02, hz)];
    poly(ctx, q); const g = ctx.createLinearGradient(q[0][0], 0, q[1][0], 0); g.addColorStop(0, '#6a3e24'); g.addColorStop(1, '#8a5530'); ctx.fillStyle = g; ctx.fill();
    ctx.strokeStyle = '#2a160c'; ctx.lineWidth = Math.max(1, 0.012 * K); ctx.stroke();
    // panels
    for (const [y0, y1] of [[0.2, 0.95], [1.1, 1.85]]) {
      const pp = [[0.15, y0], [0.85, y0], [0.85, y1], [0.15, y1]].map(([u, y]) => P(lerp(hx, fx, u), y, lerp(hz, fz, u)));
      poly(ctx, pp); ctx.strokeStyle = 'rgba(40,20,10,0.6)'; ctx.stroke();
    }
    const kn = P(lerp(hx, fx, 0.9), 1.0, lerp(hz, fz, 0.9)); ctx.beginPath(); ctx.arc(kn[0], kn[1], 0.022 * K, 0, 7); ctx.fillStyle = '#d8b060'; ctx.fill();
    S.doorHandle = [lerp(hx, fx, 0.9), 1.0, lerp(hz, fz, 0.9)];
  }
  function drawBench(ctx, cam) {
    const { K, P } = mk(cam);
    // bench beside the door (where the person sits)
    const bx = -1.42;
    const b1 = P(bx - 0.28, 0.42, 0.0), b2 = P(bx + 0.28, 0.42, 0.0), b3 = P(bx + 0.28, 0.42, 0.5), b4 = P(bx - 0.28, 0.42, 0.5);
    poly(ctx, [b1, b2, b3, b4]); ctx.fillStyle = '#5a3420'; ctx.fill();
    const bf = [P(bx - 0.28, 0.42, 0.5), P(bx + 0.28, 0.42, 0.5), P(bx + 0.28, 0.36, 0.5), P(bx - 0.28, 0.36, 0.5)]; poly(ctx, bf); ctx.fillStyle = '#3c2214'; ctx.fill();
    for (const dx of [-0.24, 0.24]) { const a = P(bx + dx, 0, 0.47), b = P(bx + dx, 0.36, 0.47); ctx.fillStyle = '#3c2214'; ctx.fillRect(a[0] - 0.02 * K, b[1], 0.04 * K, a[1] - b[1]); }
  }
  function drawReveal(ctx, cam, S) {
    // the doorway in section: we look at the far jamb's face between the inner and outer wall faces; door light grazes it
    const { K, P } = mk(cam);
    const q = [P(WALL.inner, 0, -WALL.jamb), P(WALL.outer, 0, -WALL.jamb), P(WALL.outer, WALL.head, -WALL.jamb), P(WALL.inner, WALL.head, -WALL.jamb)];
    poly(ctx, q);
    const g = ctx.createLinearGradient(q[0][0], 0, q[1][0], 0);
    const o = S.open;
    g.addColorStop(0, rgb(mix([96, 70, 60], [236, 178, 110], 0.35 + 0.6 * o))); g.addColorStop(1, rgb(mix([60, 56, 74], [190, 128, 82], 0.15 + 0.6 * o)));
    ctx.fillStyle = g; ctx.fill();
    // the doorway floor: the sill stone, both faces
    const s = [P(SILL.x0, SILL.h, -WALL.jamb), P(SILL.x1, SILL.h, -WALL.jamb), P(SILL.x1, SILL.h, WALL.cut + 0.02), P(SILL.x0, SILL.h, WALL.cut + 0.02)];
    poly(ctx, s); ctx.fillStyle = rgb(mix([110, 104, 112], [214, 170, 120], 0.25 + 0.55 * o)); ctx.fill();
    const sf = [P(SILL.x0, SILL.h, WALL.cut + 0.02), P(SILL.x1, SILL.h, WALL.cut + 0.02), P(SILL.x1, -0.05, WALL.cut + 0.02), P(SILL.x0, -0.05, WALL.cut + 0.02)];
    poly(ctx, sf); ctx.fillStyle = '#5c5662'; ctx.fill();
  }
  function drawFrame(ctx, cam) {
    const { K, P } = mk(cam);
    // the door frame: timber jambs at both faces and the head, seen in section (cut at the near jamb)
    ctx.fillStyle = '#4a2c1a'; ctx.strokeStyle = '#1e120a'; ctx.lineWidth = Math.max(1, 0.006 * K);
    for (const [xa, xb] of [[WALL.inner - 0.02, WALL.inner + 0.04], [WALL.outer - 0.045, WALL.outer + 0.02]]) {
      const q2 = [P(xa, SILL.h, WALL.cut), P(xb, SILL.h, WALL.cut), P(xb, WALL.head + 0.06, WALL.cut), P(xa, WALL.head + 0.06, WALL.cut)];
      poly(ctx, q2); ctx.fill(); ctx.stroke();
    }
    const hd = [P(WALL.inner - 0.02, WALL.head - 0.03, WALL.cut), P(WALL.outer + 0.03, WALL.head - 0.03, WALL.cut), P(WALL.outer + 0.03, WALL.head + 0.06, WALL.cut), P(WALL.inner - 0.02, WALL.head + 0.06, WALL.cut)];
    poly(ctx, hd); ctx.fill(); ctx.stroke();
  }
  function drawSection(ctx, cam, S) {
    // poché: the cut faces of wall, floor slab and ceiling/roof, at the section plane z = 0.45 (dark, with a pale edge)
    const { K, P } = mk(cam);
    const z = WALL.cut, fillc = '#1e1a22', edge = 'rgba(200,190,200,0.35)';
    const blocks = [
      [[WALL.inner, WALL.head], [WALL.outer, WALL.head], [WALL.outer, WALL.ceil + 0.25], [WALL.inner, WALL.ceil + 0.25]],
      [[-6, WALL.ceil], [WALL.inner, WALL.ceil], [WALL.inner, WALL.ceil + 0.25], [-6, WALL.ceil + 0.25]],
      [[-6, -0.0], [WALL.outer, -0.0], [WALL.outer, -0.5], [-6, -0.5]],
    ];
    ctx.lineWidth = Math.max(1, 0.006 * K);
    for (const b of blocks) { poly(ctx, b.map(([x, y]) => P(x, y, z))); ctx.fillStyle = fillc; ctx.fill(); ctx.strokeStyle = edge; ctx.stroke(); }
    // stone coursing in the wall cut
    ctx.strokeStyle = 'rgba(120,110,130,0.18)';
    for (let y = WALL.head + 0.12; y < WALL.ceil + 0.25; y += 0.14) { const a = P(WALL.inner, y, z), b = P(WALL.outer, y, z); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    // roof: a pitched section over the house, its eave reaching out over the porch
    const roof = [[-6, WALL.ceil + 0.25], [WALL.outer, WALL.ceil + 0.25], [1.15, WALL.ceil + 0.05], [1.15, WALL.ceil + 0.18], [WALL.outer + 0.1, WALL.ceil + 0.45], [-6, WALL.ceil + 1.6]];
    poly(ctx, roof.map(([x, y]) => P(x, y, z))); ctx.fillStyle = '#17131c'; ctx.fill(); ctx.strokeStyle = edge; ctx.stroke();
    // a little warm spill on the inner edge of the floor cut
  }
  function drawPorch(ctx, cam, S) {
    const { K, P } = mk(cam);
    const x0 = WALL.outer, x1 = PORCH.x1;
    const top = [P(x0, 0, PORCH.zf), P(x1, 0, PORCH.zf), P(x1, 0, PORCH.zn), P(x0, 0, PORCH.zn)];
    poly(ctx, top); const g = ctx.createLinearGradient(0, top[0][1], 0, top[2][1]); g.addColorStop(0, '#3a3a5c'); g.addColorStop(1, '#4a4868'); ctx.fillStyle = g; ctx.fill();
    // boards run along the porch (x); seams at regular z
    ctx.strokeStyle = 'rgba(20,20,40,0.55)'; ctx.lineWidth = Math.max(1, 0.006 * K);
    for (let z = PORCH.zf + 0.14; z < PORCH.zn; z += 0.14) { const a = P(x0, 0, z), b = P(x1, 0, z); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    // board ends, staggered
    const r = rand(3);
    for (let z = PORCH.zf; z < PORCH.zn - 0.1; z += 0.14) { const x = x0 + 0.5 + r() * 3.6; const a = P(x, 0, z), b = P(x, 0, z + 0.14); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    // door light on the boards
    const o = S.open, blk = S.lightBlock;
    if (S.lightAmt > 0.01) {
      ctx.save(); poly(ctx, top); ctx.clip();
      const cols = 60, rows = 18;
      for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
        const xa = x0 + (x1 - x0) * i / cols, xb = x0 + (x1 - x0) * (i + 1) / cols;
        const za = PORCH.zf + (PORCH.zn - PORCH.zf) * j / rows, zb = PORCH.zf + (PORCH.zn - PORCH.zf) * (j + 1) / rows;
        const v = spill((xa + xb) / 2, (za + zb) / 2, o, blk) * S.lightAmt;
        if (v < 0.01) continue;
        poly(ctx, [P(xa, 0, za), P(xb + 0.002, 0, za), P(xb + 0.002, 0, zb + 0.002), P(xa, 0, zb + 0.002)]);
        ctx.fillStyle = `rgba(255,178,92,${0.62 * v})`; ctx.fill();
      }
      ctx.restore();
    }
    // front fascia and the yard below it
    const fa = [P(x0, 0, PORCH.zn), P(x1, 0, PORCH.zn), P(x1, PORCH.ground, PORCH.zn), P(x0, PORCH.ground, PORCH.zn)];
    poly(ctx, fa); ctx.fillStyle = '#23223c'; ctx.fill();
    ctx.strokeStyle = 'rgba(150,150,200,0.25)'; ctx.beginPath(); ctx.moveTo(fa[0][0], fa[0][1]); ctx.lineTo(fa[1][0], fa[1][1]); ctx.stroke();
    // lattice under the porch
    ctx.strokeStyle = 'rgba(10,10,25,0.5)';
    for (let x = x0 + 0.1; x < x1; x += 0.25) { const a = P(x, -0.06, PORCH.zn), b = P(x + 0.25, PORCH.ground, PORCH.zn); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); const c = P(x + 0.25, -0.06, PORCH.zn), d = P(x, PORCH.ground, PORCH.zn); ctx.beginPath(); ctx.moveTo(c[0], c[1]); ctx.lineTo(d[0], d[1]); ctx.stroke(); }
    // steps at the porch end
    for (let k = 0; k < 3; k++) {
      const xs = x1 + k * 0.28, y = -0.15 * (k + 1);
      const st = [P(xs, y, PORCH.zf + 0.6), P(xs + 0.3, y, PORCH.zf + 0.6), P(xs + 0.3, y, PORCH.zn), P(xs, y, PORCH.zn)];
      poly(ctx, st); ctx.fillStyle = '#3e3d5e'; ctx.fill();
      const sf = [P(xs, y, PORCH.zn), P(xs + 0.3, y, PORCH.zn), P(xs + 0.3, y - 0.15, PORCH.zn), P(xs, y - 0.15, PORCH.zn)]; poly(ctx, sf); ctx.fillStyle = '#25243f'; ctx.fill();
    }
    // the near yard
    const yd = P(0, PORCH.ground, PORCH.zn)[1];
    const gg = ctx.createLinearGradient(0, yd, 0, cam.H); gg.addColorStop(0, '#191a30'); gg.addColorStop(1, '#0e0f1e');
    ctx.fillStyle = gg; ctx.fillRect(P(x0, 0, 0)[0], yd, cam.W, cam.H - yd);
  }
  function drawHaze(ctx, cam, S) {
    // a faint warm shaft in the dusk air outside the doorway
    if (S.lightAmt < 0.01) return;
    const { K, P } = mk(cam);
    const a = P(WALL.outer, 0.1, 0), b = P(WALL.outer, 2.0, 0);
    const g = ctx.createLinearGradient(a[0], 0, a[0] + 2.4 * K, 0);
    const v = S.lightAmt * lerp(0.25, 1, S.open) * S.lightBlock;
    g.addColorStop(0, `rgba(255,190,110,${0.16 * v})`); g.addColorStop(1, 'rgba(255,190,110,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(a[0], b[1]); ctx.lineTo(a[0] + 2.4 * K, b[1] + 0.5 * K); ctx.lineTo(a[0] + 2.4 * K, a[1] + 0.3 * K); ctx.lineTo(a[0], a[1] + 0.05 * K); ctx.closePath(); ctx.fill();
  }

  /* ---------------- the person: a parametric portrait rig ---------------- */
  // pose: {x, z, sit, lean, reach, low, push, step, headYaw, headPitch, mouth, vowel, blink, hair, breath, armTarget}
  const PCOL = { skin: [214, 160, 124], hair: [52, 34, 26], cardigan: [150, 76, 50], dress: [52, 66, 92], shoe: [30, 24, 22], line: [22, 15, 13], lip: [160, 80, 72] };
  function drawPerson(ctx, cam, p, L) {
    const { K, P } = mk(cam);
    const lw = Math.max(1, 0.008 * K), line = rgb(PCOL.line);
    const C = k => rgb(R.lit(PCOL[k], L));
    const x = p.x, z = p.z || 0;
    // skeleton (side view, facing +x toward the porch)
    const sit = p.sit, lean = p.lean;
    const hip = [x - 0.02 - 0.1 * sit, lerp(0.9, 0.5, sit)];
    const tl = 0.5, ta = (90 - lean - 4 * sit) * Math.PI / 180;
    const sh = [hip[0] + Math.cos(ta) * tl, hip[1] + Math.sin(ta) * tl + 0.004 * p.breath];
    const neck = [sh[0] + Math.cos(ta) * 0.07, sh[1] + Math.sin(ta) * 0.07];
    const hc = [neck[0] + 0.03 + Math.cos(ta) * 0.1, neck[1] + Math.sin(ta) * 0.1 + 0.02];
    const W = (q, dz = 0) => P(q[0], q[1], z + dz);
    // legs
    const legs = [];
    for (const side of [-1, 1]) {
      const dz = side * 0.09;
      let knee, foot;
      if (sit > 0.5) { const s2 = smooth(0.5, 1, sit); knee = [lerp(hip[0] + 0.03, hip[0] + 0.42, s2), lerp(0.47, 0.5, s2)]; foot = [knee[0] + 0.03, 0.04]; }
      else {
        const st = p.step * side;
        foot = [x + 0.08 * st + (side > 0 ? 0.04 : -0.02), 0.04 + 0.06 * Math.max(0, Math.sin((p.stepPh || 0) + (side > 0 ? 0 : Math.PI))) * (p.walking || 0)];
        const s2 = sit * 2; knee = [lerp((hip[0] + foot[0]) / 2 + 0.03, hip[0] + 0.3, s2), lerp((hip[1] + foot[1]) / 2, 0.48, s2)];
        if (s2 > 0) foot = [lerp(foot[0], knee[0] + 0.05, s2 * 0.6), foot[1]];
      }
      legs.push({ dz, pts: [hip, knee, foot] });
    }
    const items = [];
    const limb = (pts, dz, r) => { const S = pts.map(q => W(q, dz)); const out = []; for (let i = 0; i < S.length - 1; i++) out.push(capsule(S[i], r[i] * K, S[i + 1], r[i + 1] * K, 10)); return out; };
    for (const lg of legs) {
      const polys = limb(lg.pts, lg.dz, [0.075, 0.05, 0.04]);
      const f = W(lg.pts[2], lg.dz); const shoe = ellPoly(f[0] + 0.05 * K, f[1] + 0.005 * K, Math.pow(0.08 * K, 2), 0, Math.pow(0.03 * K, 2), 14);
      items.push({ d: lg.dz, f: () => { union(ctx, polys, C('dress'), line, lw); union(ctx, [shoe], C('shoe'), line, lw * 0.7); } });
    }
    // skirt and cardigan torso
    const kneeAvg = [(legs[0].pts[1][0] + legs[1].pts[1][0]) / 2, (legs[0].pts[1][1] + legs[1].pts[1][1]) / 2];
    const skirt = (() => {
      const w = [hip[0] - 0.14, hip[1] + 0.04], e = [hip[0] + 0.14, hip[1] + 0.04];
      if (sit > 0.5) { const s2 = smooth(0.5, 1, sit); const k = [kneeAvg[0] + 0.07, kneeAvg[1] + 0.02]; return [W(w), W(e), W([k[0], k[1] + 0.05]), W([k[0] + 0.02, lerp(0.35, 0.12, s2)]), W([k[0] - 0.12, lerp(0.3, 0.1, s2)]), W([hip[0] - 0.16, hip[1] - 0.12])]; }
      return [W(w), W(e), W([hip[0] + 0.2 + 0.08 * sit, 0.38 + 0.1 * sit]), W([hip[0] - 0.2, 0.38])];
    })();
    const torso = [W([hip[0] - 0.15, hip[1] + 0.02]), W([hip[0] + 0.15, hip[1] + 0.02]), W([sh[0] + 0.13, sh[1] - 0.12]), W([sh[0] + 0.08, sh[1] + 0.03]), W([sh[0] - 0.1, sh[1] + 0.03]), W([sh[0] - 0.14, sh[1] - 0.1])];
    items.push({ d: 0, f: () => { union(ctx, [skirt], C('dress'), line, lw); union(ctx, [torso], C('cardigan'), line, lw); ctx.save(); clipTo(ctx, [torso, skirt]); R.shade(ctx, [torso, skirt], L, K, 0.8); ctx.restore(); } });
    // arms: rotation deformers shoulder->elbow->wrist, solved to a target
    const arm = (side, target) => {
      const dz = side * 0.15, s0 = [sh[0], sh[1] - 0.03];
      const [el, wr] = R.ik2(s0, target, 0.29, 0.27, -1);
      const polys = limb([s0, el, wr], dz, [0.05, 0.04, 0.032]);
      const hw = W(wr, dz), dir = Math.atan2(-(wr[1] - el[1]), wr[0] - el[0]);
      const hand = ellPoly(hw[0] + Math.cos(dir) * 0.045 * K, hw[1] + Math.sin(dir) * 0.045 * K, Math.pow(0.055 * K, 2) * (Math.cos(dir) ** 2) + Math.pow(0.028 * K, 2) * (Math.sin(dir) ** 2), (Math.pow(0.055 * K, 2) - Math.pow(0.028 * K, 2)) * Math.cos(dir) * Math.sin(dir), Math.pow(0.055 * K, 2) * (Math.sin(dir) ** 2) + Math.pow(0.028 * K, 2) * (Math.cos(dir) ** 2), 14);
      return { d: dz, polys, hand, wr, el };
    };
    const rest = [sh[0] + 0.06 + 0.12 * sit, lerp(sh[1] - 0.52, hip[1] + 0.05, sit)];
    const T = p.armTarget || rest;
    const near = arm(1, T), far = arm(-1, p.armTarget2 || [rest[0] - 0.04, rest[1] + 0.02]);
    for (const a of [near, far]) items.push({ d: a.d * 2, f: () => { union(ctx, a.polys, C('cardigan'), line, lw); union(ctx, [a.hand], C('skin'), line, lw * 0.8); } });
    p.handW = [near.wr[0] + 0.06, near.wr[1], z + 0.15];
    // head: a small Live2D-style face. ParamAngleX turns it toward the viewer, features shift with the angle
    items.push({ d: 0.05, f: () => {
      const ax = clamp(p.headYaw, -1, 1), ay = clamp(p.headPitch, -1, 1);
      const hcS = W(hc), r = 0.105 * K;
      const rot = -ay * 0.35;
      const off = (u, v) => [hcS[0] + (u * Math.cos(rot) - v * Math.sin(rot)) * r, hcS[1] + (u * Math.sin(rot) + v * Math.cos(rot)) * r];
      // hair back + bun (pendulum)
      const bun = off(-0.95 + 0.1 * ax, -0.35 + 0.08 * (p.hair || 0));
      union(ctx, [circlePts(bun, 0.48 * r, 16)], C('hair'), line, lw);
      const skull = ellPoly(hcS[0], hcS[1], Math.pow(r * 0.98, 2), 0, Math.pow(r * 1.05, 2), 28);
      const face = ellPoly(off(0.32 + 0.12 * ax, 0.35)[0], off(0.32, 0.35)[1], Math.pow(r * 0.72, 2), 0, Math.pow(r * 0.85, 2), 24);
      const nose = circlePts(off(0.98 - 0.25 * ax, 0.15), r * 0.14, 10);
      union(ctx, [skull, face, nose], C('skin'), line, lw);
      // hair cap with fringe
      ctx.save(); clipTo(ctx, [skull, face]);
      ctx.beginPath(); const hp = [off(-1.2, 1), off(-1.2, -1.3), off(0.5, -1.3), off(0.9 - 0.2 * ax, -0.45), off(0.35, -0.62), off(-0.1, -0.3), off(-0.25, 0.1), off(-0.6, 0.6)];
      smoothPath(ctx, hp); ctx.fillStyle = C('hair'); ctx.fill();
      R.shade(ctx, [skull, face], L, K, 0.7);
      ctx.restore();
      // eye (blink), brow, mouth (open with the voice)
      const eo = clamp(1 - (p.blink || 0));
      const e = off(0.55 - 0.18 * ax, -0.12 + 0.1 * ay);
      ctx.beginPath(); ctx.ellipse(e[0], e[1], r * 0.12, Math.max(0.6, r * 0.09 * eo), rot, 0, 7); ctx.fillStyle = '#1a1210'; ctx.fill();
      ctx.beginPath(); ctx.moveTo(e[0] - r * 0.17, e[1] - r * 0.2); ctx.quadraticCurveTo(e[0], e[1] - r * 0.3 - (p.brow || 0) * r * 0.08, e[0] + r * 0.17, e[1] - r * 0.22); ctx.strokeStyle = C('hair'); ctx.lineWidth = lw * 1.3; ctx.stroke();
      if (ax > 0.15) { const e2 = off(0.95 - 0.1 * ax, -0.1 + 0.1 * ay); ctx.beginPath(); ctx.ellipse(e2[0], e2[1], r * 0.07 * ax, Math.max(0.5, r * 0.08 * eo), rot, 0, 7); ctx.fillStyle = '#1a1210'; ctx.fill(); }
      const mo = clamp(p.mouth || 0), m = off(0.78 - 0.15 * ax, 0.52);
      const vw = p.vowel || 0.5;
      ctx.beginPath(); ctx.ellipse(m[0], m[1], r * (0.12 + 0.08 * vw), Math.max(0.6, r * (0.02 + 0.13 * mo)), rot, 0, 7); ctx.fillStyle = mo > 0.08 ? '#4a1a18' : rgb(PCOL.lip); ctx.fill();
      // ear
      const ea = off(-0.15 + 0.1 * ax, 0.05); ctx.beginPath(); ctx.ellipse(ea[0], ea[1], r * 0.13, r * 0.2, 0.2, 0, 7); ctx.fillStyle = C('skin'); ctx.fill(); ctx.strokeStyle = line; ctx.lineWidth = lw * 0.8; ctx.stroke();
    } });
    items.sort((a, b) => a.d - b.d).forEach(i => i.f());
    return { head: W(hc), hip: W(hip) };
  }

  G.Scene = { drawFrame, drawBench, WALL, SILL, PORCH, LAMP, spill, drawSky, drawYard, drawRailing, drawInterior, drawDoor, drawReveal, drawSection, drawPorch, drawHaze, drawPerson, mk };
})(typeof window !== 'undefined' ? window : globalThis);
