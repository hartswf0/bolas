/* SCION-25 RIVE · the film host: the world artboards (porch, house in section, door, light, person puppet) and the frame
   loop that drives the dog's state machine from the score, draws everything from primitives, and measures the dog from its
   own rendered layer. Browser only (canvas). Exposes window.FILM and window.frame(i). */
(function () {
  'use strict';
  const { clamp, lerp, ease, smooth, capsule, shade } = RIVE;
  const W = 1280, H = 720, S = 210, OX = 355, OY = 598; let KX = 0.28, KY = 0.30;
  const P = (X, Y, Z) => [OX + S * (X + KX * Z), OY - S * Y + S * KY * Z];
  const TITLE = 72, SCENE = 768, END = 72, N = TITLE + SCENE + END;
  const FILM = window.FILM = { N, TITLE, SCENE, END, trace: [], events: [], ready: false };
  let score, puppet, drive, cv, ctx, dogCv, dg, perCv, pg, noise;
  const lastStep = { i: -1 };

  function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
  function poly(c, pts) { c.beginPath(); c.moveTo(pts[0][0], pts[0][1]); for (let k = 1; k < pts.length; k++) c.lineTo(pts[k][0], pts[k][1]); c.closePath(); }
  function quad(c, a, b, d, e) { poly(c, [P(...a), P(...b), P(...d), P(...e)]); }

  /* ---------- the world, in metres ---------- */
  const HOUSE = { inX: -0.25, outX: 0.25, back: -1.7, cut: 0.45, doorZ0: -0.45, doorZ1: 0.45, doorH: 2.05, ceil: 2.6, leafW: 0.88, leafH: 2.0 };
  const PORCH = { x1: 5.2, zb: -1.3, zf: 0.85 };
  let stars = [];
  function sky(t) {
    const k = clamp(t / 32);
    const g = ctx.createLinearGradient(0, 0, 0, 520);
    g.addColorStop(0, `rgb(${lerp(28, 16, k)|0},${lerp(34, 22, k)|0},${lerp(66, 46, k)|0})`);
    g.addColorStop(0.55, `rgb(${lerp(70, 44, k)|0},${lerp(66, 48, k)|0},${lerp(104, 82, k)|0})`);
    g.addColorStop(0.86, `rgb(${lerp(176, 118, k)|0},${lerp(112, 78, k)|0},${lerp(98, 86, k)|0})`);
    g.addColorStop(1, `rgb(${lerp(198, 132, k)|0},${lerp(132, 92, k)|0},${lerp(96, 84, k)|0})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, 540);
    for (const s of stars) { const a = clamp((t - s.t0) / 6) * s.a; if (a <= 0) continue; ctx.fillStyle = `rgba(235,232,255,${a})`; ctx.fillRect(s.x, s.y, s.r, s.r); }
    // a thin moon, drawn
    ctx.save(); ctx.fillStyle = 'rgba(244,232,200,0.9)'; ctx.beginPath(); ctx.arc(1010, 205, 17, Math.PI * 0.32, Math.PI * 1.68, false);
    ctx.arc(1021, 198, 15.5, Math.PI * 1.55, Math.PI * 0.45, true); ctx.closePath(); ctx.fill(); ctx.restore();
    // far tree line and a field, authored silhouettes
    const r = rng(7); ctx.fillStyle = `rgb(${lerp(36, 24, k)|0},${lerp(40, 28, k)|0},${lerp(58, 44, k)|0})`; ctx.beginPath(); ctx.moveTo(380, 540);
    for (let x = 380; x <= W + 20; x += 18) { const h = 70 + 40 * Math.sin(x * 0.013) + 26 * Math.sin(x * 0.041 + 1) + r() * 16; ctx.lineTo(x, 470 - h * 0.6); }
    ctx.lineTo(W, 540); ctx.closePath(); ctx.fill();
    ctx.fillStyle = `rgb(${lerp(30, 20, k)|0},${lerp(34, 24, k)|0},${lerp(44, 34, k)|0})`; ctx.fillRect(380, 470, W - 380, 80);
  }
  function porch(t, L) {
    // back railing behind the dog (balusters), then the floor boards, then the front fascia
    const zr = PORCH.zb + 0.06; ctx.strokeStyle = 'rgb(44,40,48)';
    ctx.fillStyle = 'rgb(52,46,52)'; quad(ctx, [0.25, 0.86, zr], [PORCH.x1, 0.86, zr], [PORCH.x1, 0.92, zr], [0.25, 0.92, zr]); ctx.fill();
    quad(ctx, [0.25, 0.08, zr], [PORCH.x1, 0.08, zr], [PORCH.x1, 0.13, zr], [0.25, 0.13, zr]); ctx.fill();
    ctx.fillStyle = 'rgb(46,41,48)';
    for (let x = 0.55; x < PORCH.x1; x += 0.17) quad(ctx, [x, 0.1, zr], [x + 0.045, 0.1, zr], [x + 0.045, 0.88, zr], [x, 0.88, zr]), ctx.fill();
    ctx.fillStyle = 'rgb(58,50,54)'; for (const x of [0.4, 2.7, 5.0]) { quad(ctx, [x, 0, zr], [x + 0.11, 0, zr], [x + 0.11, 2.6, zr], [x, 2.6, zr]); ctx.fill(); }
    // floor
    const g = ctx.createLinearGradient(0, P(0, 0, PORCH.zb)[1], 0, P(0, 0, PORCH.zf)[1]); g.addColorStop(0, 'rgb(64,56,60)'); g.addColorStop(1, 'rgb(84,72,72)');
    ctx.fillStyle = g; quad(ctx, [0.25, 0, PORCH.zb], [PORCH.x1, 0, PORCH.zb], [PORCH.x1, 0, PORCH.zf], [0.25, 0, PORCH.zf]); ctx.fill();
    ctx.strokeStyle = 'rgba(30,24,28,0.55)'; ctx.lineWidth = 1;
    for (let z = PORCH.zb + 0.14; z < PORCH.zf; z += 0.14) { const a = P(0.25, 0, z), b = P(PORCH.x1, 0, z); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    ctx.fillStyle = 'rgb(38,32,36)'; quad(ctx, [0.25, 0, PORCH.zf], [PORCH.x1, 0, PORCH.zf], [PORCH.x1, -0.3, PORCH.zf], [0.25, -0.3, PORCH.zf]); ctx.fill();
    ctx.fillStyle = 'rgb(24,22,28)'; ctx.fillRect(0, P(0, -0.3, PORCH.zf)[1], W, H);
    // porch roof soffit and fascia across the top
    ctx.fillStyle = 'rgb(26,22,28)'; quad(ctx, [-3, 2.74, PORCH.zf + 0.3], [PORCH.x1 + 1, 2.74, PORCH.zf + 0.3], [PORCH.x1 + 1, 3.2, PORCH.zf + 0.3], [-3, 3.2, PORCH.zf + 0.3]); ctx.fill();
    ctx.fillStyle = 'rgba(200,150,110,0.25)'; quad(ctx, [-3, 2.74, PORCH.zf + 0.3], [PORCH.x1 + 1, 2.74, PORCH.zf + 0.3], [PORCH.x1 + 1, 2.755, PORCH.zf + 0.3], [-3, 2.755, PORCH.zf + 0.3]); ctx.fill();
  }
  function interior(t, L, lamp) {
    const h = HOUSE;
    // back wall, warm plaster lit by a lamp
    const lp = P(-1.55, 1.05, h.back + 0.2), g = ctx.createRadialGradient(lp[0], lp[1], 6, lp[0], lp[1], 360);
    g.addColorStop(0, `rgb(${196 * lamp|0},${142 * lamp|0},${88 * lamp|0})`); g.addColorStop(1, 'rgb(70,44,34)');
    ctx.fillStyle = g; quad(ctx, [-3, 0, h.back], [h.inX, 0, h.back], [h.inX, h.ceil, h.back], [-3, h.ceil, h.back]); ctx.fill();
    // the facade wall's own thickness seen from the room side, between the back wall and the far reveal
    ctx.fillStyle = 'rgb(96,62,44)'; quad(ctx, [h.inX, 0, h.back], [h.inX, 0, h.doorZ0], [h.inX, h.ceil, h.doorZ0], [h.inX, h.ceil, h.back]); ctx.fill();
    // picture on the wall, skirting, floor boards
    ctx.fillStyle = 'rgb(58,36,28)'; quad(ctx, [-1.05, 1.25, h.back + 0.01], [-0.6, 1.25, h.back + 0.01], [-0.6, 1.62, h.back + 0.01], [-1.05, 1.62, h.back + 0.01]); ctx.fill();
    ctx.fillStyle = 'rgb(120,96,70)'; quad(ctx, [-1.0, 1.3, h.back + 0.02], [-0.65, 1.3, h.back + 0.02], [-0.65, 1.57, h.back + 0.02], [-1.0, 1.57, h.back + 0.02]); ctx.fill();
    const fg = ctx.createLinearGradient(0, P(0, 0, h.back)[1], 0, P(0, 0, h.cut)[1]); fg.addColorStop(0, 'rgb(104,66,42)'); fg.addColorStop(1, 'rgb(70,44,32)');
    ctx.fillStyle = fg; quad(ctx, [-3, 0, h.back], [h.inX, 0, h.back], [h.inX, 0, h.cut], [-3, 0, h.cut]); ctx.fill();
    ctx.strokeStyle = 'rgba(40,22,14,0.5)'; for (let z = h.back + 0.16; z < h.cut; z += 0.16) { const a = P(-3, 0, z), b = P(h.inX, 0, z); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    // rug inside the door
    ctx.fillStyle = 'rgba(120,50,40,0.8)'; quad(ctx, [-1.0, 0.005, -0.4], [-0.3, 0.005, -0.4], [-0.3, 0.005, 0.38], [-1.0, 0.005, 0.38]); ctx.fill();
    // lamp on a small table
    ctx.fillStyle = 'rgb(46,30,24)'; quad(ctx, [-1.75, 0, h.back + 0.25], [-1.68, 0, h.back + 0.25], [-1.68, 0.7, h.back + 0.25], [-1.75, 0.7, h.back + 0.25]); ctx.fill();
    quad(ctx, [-1.95, 0.7, h.back + 0.25], [-1.45, 0.7, h.back + 0.25], [-1.45, 0.75, h.back + 0.25], [-1.95, 0.75, h.back + 0.25]); ctx.fill();
    ctx.fillStyle = `rgb(${250 * lamp|0},${206 * lamp|0},${140 * lamp|0})`; poly(ctx, [P(-1.85, 1.15, h.back + 0.25), P(-1.55, 1.15, h.back + 0.25), P(-1.5, 0.92, h.back + 0.25), P(-1.9, 0.92, h.back + 0.25)]); ctx.fill();
    // the stool beside the door
    ctx.fillStyle = 'rgb(62,40,30)'; quad(ctx, [-1.42, 0.36, 0.08], [-1.08, 0.36, 0.08], [-1.08, 0.40, 0.08], [-1.42, 0.40, 0.08]); ctx.fill();
    for (const x of [-1.4, -1.12]) { quad(ctx, [x, 0, 0.1], [x + 0.04, 0, 0.1], [x + 0.04, 0.36, 0.1], [x, 0.36, 0.1]); ctx.fill(); }
  }
  function doorway(t, L, phi) {
    const h = HOUSE;
    // the facade's outer face behind the doorway, the far reveal of the opening, the sill
    ctx.fillStyle = 'rgb(86,72,74)'; quad(ctx, [h.outX, 0, h.back], [h.outX, 0, h.doorZ0], [h.outX, h.ceil, h.doorZ0], [h.outX, h.ceil, h.back]); ctx.fill();
    ctx.fillStyle = 'rgb(92,78,80)'; quad(ctx, [h.outX, h.doorH, h.doorZ0], [h.outX, h.doorH, h.cut], [h.outX, h.ceil, h.cut], [h.outX, h.ceil, h.doorZ0]); ctx.fill();
    // clapboard lines on the facade
    ctx.strokeStyle = 'rgba(40,32,36,0.45)'; for (let y = 0.2; y < h.ceil; y += 0.2) { const a = P(h.outX, y, h.back), b = P(h.outX, y, h.doorZ0); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    const rv = ctx.createLinearGradient(P(h.inX, 0, h.doorZ0)[0], 0, P(h.outX, 0, h.doorZ0)[0], 0);
    rv.addColorStop(0, `rgba(${150 * L.inside|0},${104 * L.inside|0},${70 * L.inside|0},1)`); rv.addColorStop(1, 'rgb(74,60,58)');
    ctx.fillStyle = rv; quad(ctx, [h.inX, 0, h.doorZ0], [h.outX, 0, h.doorZ0], [h.outX, h.doorH, h.doorZ0], [h.inX, h.doorH, h.doorZ0]); ctx.fill();
    // door frame casing on the facade
    ctx.fillStyle = 'rgb(168,150,130)'; quad(ctx, [h.outX + 0.01, 0, h.doorZ0 - 0.1], [h.outX + 0.01, 0, h.doorZ0], [h.outX + 0.01, h.doorH + 0.1, h.doorZ0], [h.outX + 0.01, h.doorH + 0.1, h.doorZ0 - 0.1]); ctx.fill();
    quad(ctx, [h.outX + 0.01, h.doorH, h.doorZ0 - 0.1], [h.outX + 0.01, h.doorH, h.cut], [h.outX + 0.01, h.doorH + 0.1, h.cut], [h.outX + 0.01, h.doorH + 0.1, h.doorZ0 - 0.1]); ctx.fill();
    // sill: a pale stone across the opening
    ctx.fillStyle = 'rgb(150,138,124)'; quad(ctx, [h.inX, 0.012, h.doorZ0], [h.outX + 0.06, 0.012, h.doorZ0], [h.outX + 0.06, 0.012, h.doorZ1], [h.inX, 0.012, h.doorZ1]); ctx.fill();
    ctx.fillStyle = 'rgb(110,100,92)'; quad(ctx, [h.inX, 0.012, h.doorZ1], [h.outX + 0.06, 0.012, h.doorZ1], [h.outX + 0.06, -0.03, h.doorZ1], [h.inX, -0.03, h.doorZ1]); ctx.fill();
  }
  function leaf(phi) {
    const h = HOUSE, a = phi * Math.PI / 180, hx = h.inX, hz = h.doorZ0, fx = hx - h.leafW * Math.sin(a), fz = hz + h.leafW * Math.cos(a);
    ctx.fillStyle = 'rgb(84,52,34)'; quad(ctx, [hx, 0, hz], [fx, 0, fz], [fx, h.leafH, fz], [hx, h.leafH, hz]); ctx.fill();
    ctx.strokeStyle = 'rgba(40,22,14,0.7)'; ctx.lineWidth = 2;
    const L = (u, y) => [lerp(hx, fx, u), y, lerp(hz, fz, u)];
    for (const [u0, u1, y0, y1] of [[0.14, 0.86, 1.1, 1.82], [0.14, 0.86, 0.15, 0.95]]) { quad(ctx, L(u0, y0), L(u1, y0), L(u1, y1), L(u0, y1)); ctx.stroke(); }
    ctx.fillStyle = 'rgb(200,170,100)'; const k = P(...L(0.9, 1.0)); ctx.beginPath(); ctx.arc(k[0], k[1], 4, 0, 7); ctx.fill();
    return [fx, fz];
  }
  function casing() {   // the outer door casing on the near side: a thin post in front of the dog, the threshold line made visible
    const h = HOUSE, z0 = h.cut, z1 = h.cut + 0.05, x0 = h.outX, x1 = h.outX + 0.075;
    ctx.fillStyle = 'rgb(150,134,118)'; quad(ctx, [x0, -0.02, z1], [x1, -0.02, z1], [x1, h.doorH + 0.1, z1], [x0, h.doorH + 0.1, z1]); ctx.fill();
    ctx.fillStyle = 'rgb(108,96,88)'; quad(ctx, [x1, -0.02, z0], [x1, -0.02, z1], [x1, h.doorH + 0.1, z1], [x1, h.doorH + 0.1, z0]); ctx.fill();
  }
  function cutFaces() {   // the section: where the house is cut away, drawn as dark poche with a thin edge
    const h = HOUSE, z = h.cut;
    ctx.fillStyle = 'rgb(20,16,20)';
    poly(ctx, [P(-3, h.ceil, z), P(h.outX, h.ceil, z), P(h.outX, h.doorH, z), P(h.inX, h.doorH, z), P(h.inX, h.ceil - 0.0, z), P(-3, h.ceil, z)]); ctx.fill();
    poly(ctx, [P(-3, h.ceil, z), P(0.6, h.ceil, z), P(0.6, h.ceil + 0.35, z), P(-3, h.ceil + 0.35, z)]); ctx.fill();
    poly(ctx, [P(-3, 0, z), P(h.outX + 0.06, 0, z), P(h.outX + 0.06, -0.3, z), P(-3, -0.3, z)]); ctx.fill();
    // the house above the ceiling, cut: one dark mass from the ceiling to the top of the frame, over the lintel
    poly(ctx, [P(-3, h.ceil, z), P(h.outX + 0.075, h.ceil, z), P(h.outX + 0.075, 4, z), P(-3, 4, z)]); ctx.fill();
    // lintel cut face
    ctx.fillStyle = 'rgb(28,22,26)'; poly(ctx, [P(h.inX, h.doorH, z), P(h.outX, h.doorH, z), P(h.outX, h.ceil, z), P(h.inX, h.ceil, z)]); ctx.fill();
    ctx.strokeStyle = 'rgba(220,170,120,0.35)'; ctx.lineWidth = 1.5; ctx.beginPath(); const a = P(h.inX, h.doorH, z), b = P(h.outX, h.doorH, z); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    const c = P(-3, 0, z), d = P(h.outX + 0.06, 0, z); ctx.beginPath(); ctx.moveTo(c[0], c[1]); ctx.lineTo(d[0], d[1]); ctx.stroke();
  }
  function lightPool(L) {
    const h = HOUSE, I = L.door; if (I <= 0.001) return;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const len = 3.6, a = P(h.outX, 0, 0), b = P(h.outX + len, 0, 0);
    const g = ctx.createLinearGradient(a[0], 0, b[0], 0); g.addColorStop(0, `rgba(255,190,110,${0.42 * I})`); g.addColorStop(0.5, `rgba(240,160,90,${0.16 * I})`); g.addColorStop(1, 'rgba(240,150,80,0)');
    ctx.fillStyle = g; poly(ctx, [P(h.inX, 0.013, h.doorZ0), P(h.outX, 0.013, h.doorZ0 + 0.02), P(h.outX + len, 0, -0.95), P(h.outX + len, 0, PORCH.zf), P(h.outX, 0.013, h.doorZ1), P(h.inX, 0.013, h.doorZ1)]); ctx.fill();
    // haze in the doorway
    const hz = ctx.createLinearGradient(P(h.inX, 1, 0)[0], 0, P(h.outX + 1.2, 1, 0)[0], 0); hz.addColorStop(0, `rgba(255,190,120,${0.15 * I})`); hz.addColorStop(1, 'rgba(255,190,120,0)');
    ctx.fillStyle = hz; ctx.filter = 'blur(14px)'; poly(ctx, [P(h.inX, 0, 0), P(h.inX, h.doorH * 0.9, 0), P(h.outX + 0.5, h.doorH * 0.7, 0), P(h.outX + 1.6, 0.1, 0), P(h.outX + 1.6, 0, 0)]); ctx.fill(); ctx.filter = 'none';
    ctx.restore();
    if (L.block > 0.01) {   // the standing person blocks the doorway: their shadow lies across the pool toward the dog
      ctx.save(); ctx.globalAlpha = 0.55 * L.block * clamp(I * 2); ctx.fillStyle = 'rgb(18,14,20)';
      poly(ctx, [P(h.outX, 0.014, -0.1), P(h.outX, 0.014, 0.25), P(h.outX + 2.9, 0, 0.6), P(h.outX + 2.9, 0, -0.45)]); ctx.filter = 'blur(6px)'; ctx.fill(); ctx.restore();
    }
  }

  /* ---------- the person: a second puppet (2D profile on a plane at depth z, facing the porch) ---------- */
  function ik2(r, t, a, b, bendSign) {
    const dx = t[0] - r[0], dy = t[1] - r[1]; let L = Math.hypot(dx, dy); const Lc = Math.min(L, (a + b) * 0.999);
    const ux = dx / L, uy = dy / L, pr = (a * a - b * b + Lc * Lc) / (2 * Lc), hh = Math.sqrt(Math.max(0, a * a - pr * pr));
    return [r[0] + ux * pr - uy * hh * bendSign, r[1] + uy * pr + ux * hh * bendSign];
  }
  function personPose(p, st) {
    const s = ease(p.sit), x = p.x, walk = st.walk;
    const J = {};
    const stand = { hip: [x, 0.93], sh: [x + 0.01, 1.43], head: [x + 0.035, 1.635] };
    const sit = { hip: [x - 0.02, 0.45], sh: [x + 0.07, 0.95], head: [x + 0.12, 1.15] };
    J.hip = [lerp(stand.hip[0], sit.hip[0], s), lerp(stand.hip[1], sit.hip[1], s)];
    let sh = [lerp(stand.sh[0], sit.sh[0], s), lerp(stand.sh[1], sit.sh[1], s)], hd = [lerp(stand.head[0], sit.head[0], s), lerp(stand.head[1], sit.head[1], s)];
    const callK = p.voice === 'call' ? clamp(p.mouth / 0.9) : 0, softK = p.voice === 'soft' ? 1 : 0;
    const lean = (5 * callK + 13 * ease(p.reach) + 6 * st.softLean + 4 * ease(p.low)) * Math.PI / 180;
    const rot = q => { const dx = q[0] - J.hip[0], dy = q[1] - J.hip[1]; return [J.hip[0] + dx * Math.cos(lean) + dy * Math.sin(lean), J.hip[1] - dx * Math.sin(lean) + dy * Math.cos(lean)]; };
    J.sh = rot(sh); J.head = rot(hd); J.headTilt = lean + st.softLean * 0.12;
    // legs
    const legs = [];
    for (const side of [1, -1]) {
      const ph = walk * Math.PI * 2 + (side > 0 ? 0 : Math.PI), stepA = st.walking * 0.1;
      const ankStand = [x + Math.sin(ph) * stepA, 0.07 + Math.max(0, Math.cos(ph)) * stepA * 0.5], ankSit = [x + 0.32 + (side > 0 ? 0.02 : -0.04), 0.07];
      const ank = [lerp(ankStand[0], ankSit[0], s), lerp(ankStand[1], ankSit[1], s)];
      const hipS = [J.hip[0] + side * 0.0, J.hip[1]];
      const knee = ik2(hipS, ank, 0.45, 0.43, 1);
      legs.push({ side, hip: hipS, knee, ank, toe: [ank[0] + 0.13, Math.max(0.03, ank[1] - 0.02)] });
    }
    J.legs = legs;
    // arms: near (side 1) and far (side -1)
    const rest = [J.sh[0] + 0.03, J.sh[1] - 0.56], restSit = [legs[0].knee[0] - 0.08, legs[0].knee[1] + 0.06];
    const handRest = [lerp(rest[0], restSit[0], s), lerp(rest[1], restSit[1], s)];
    const mouth = [J.head[0] + 0.11, J.head[1] - 0.05];
    const reachT = [J.sh[0] + 0.56, J.sh[1] - 0.16];
    const lowT = [x + 0.52, 0.26];
    const pushT = st.doorEdge ? [st.doorEdge[0] + 0.02, 0.72] : handRest;
    const mixT = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
    let near = handRest, far = handRest;
    if (p.reach > 0.01) { near = mixT(handRest, reachT, ease(p.reach)); far = mixT(handRest, mouth, callK); }
    else near = mixT(handRest, mouth, callK);
    if (st.push > 0) far = mixT(far, pushT, st.push);
    if (p.low > 0.01) near = mixT(near, lowT, ease(p.low));
    J.arms = [{ side: 1, hand: near }, { side: -1, hand: far }].map(A => ({ side: A.side, sh: J.sh, hand: A.hand, el: ik2(J.sh, A.hand, 0.31, 0.29, -1) }));
    J.mouth = p.mouth; J.softK = softK; J.palmUp = ease(p.low);
    return J;
  }
  const PC = { coat: '#33415f', coatFar: '#232c42', skirt: '#4b3833', skirtFar: '#36282a', skin: '#d8a27e', skinFar: '#a87a5e', hair: '#2a1c17', shoe: '#1d1716', leg: '#2e2626' };
  function drawPerson(c, J, z) {
    const q = (pt) => P(pt[0], pt[1], z), sc = S;
    c.lineCap = 'round'; c.lineJoin = 'round';
    const seg = (a, b, w, col) => { const A = q(a), B = q(b); c.strokeStyle = col; c.lineWidth = w * sc; c.beginPath(); c.moveTo(A[0], A[1]); c.lineTo(B[0], B[1]); c.stroke(); };
    const arm = (A, far) => { seg(A.sh, A.el, 0.085, far ? PC.coatFar : PC.coat); seg(A.el, A.hand, 0.07, far ? PC.coatFar : PC.coat);
      const h = q(A.hand); c.fillStyle = far ? PC.skinFar : PC.skin; c.beginPath(); c.ellipse(h[0], h[1], 0.045 * sc, 0.032 * sc, 0, 0, 7); c.fill(); };
    const leg = (L, far) => { seg(L.hip, L.knee, 0.13, far ? PC.skirtFar : PC.leg); seg(L.knee, L.ank, 0.085, far ? '#211b1b' : PC.leg);
      seg(L.ank, L.toe, 0.07, PC.shoe); };
    arm(J.arms[1], true); leg(J.legs[1], true);
    // torso: a tapered body between shoulder and hip
    const sh = q(J.sh), hp = q(J.hip), ang = Math.atan2(hp[1] - sh[1], hp[0] - sh[0]), nx = -Math.sin(ang), ny = Math.cos(ang);
    c.fillStyle = PC.coat; c.beginPath(); c.moveTo(sh[0] + nx * 0.13 * sc, sh[1] + ny * 0.13 * sc); c.lineTo(hp[0] + nx * 0.15 * sc, hp[1] + ny * 0.15 * sc);
    c.lineTo(hp[0] - nx * 0.15 * sc, hp[1] - ny * 0.15 * sc); c.lineTo(sh[0] - nx * 0.11 * sc, sh[1] - ny * 0.11 * sc); c.closePath(); c.fill();
    c.beginPath(); c.arc(sh[0], sh[1], 0.12 * sc, 0, 7); c.fill();
    // skirt over the near thigh
    const k = q(J.legs[0].knee); c.fillStyle = PC.skirt; c.beginPath(); c.moveTo(hp[0] - 0.16 * sc, hp[1] - 0.05 * sc); c.lineTo(hp[0] + 0.15 * sc, hp[1] - 0.06 * sc);
    c.lineTo(k[0] + 0.07 * sc, k[1] + 0.02 * sc); c.lineTo(k[0] - 0.09 * sc, k[1] + 0.05 * sc); c.closePath(); c.fill();
    leg(J.legs[0], false);
    // head: neck, skull, hair, profile
    const hd = q(J.head); seg([J.sh[0] + 0.01, J.sh[1]], [J.head[0] - 0.005, J.head[1] - 0.05], 0.075, PC.skinFar);
    c.save(); c.translate(hd[0], hd[1]); c.rotate(J.headTilt);
    c.fillStyle = PC.skin; c.beginPath(); c.ellipse(0, 0, 0.098 * sc, 0.115 * sc, 0, 0, 7); c.fill();
    c.beginPath(); c.moveTo(0.085 * sc, -0.02 * sc); c.lineTo(0.125 * sc, 0.015 * sc); c.lineTo(0.088 * sc, 0.03 * sc); c.fill();   // nose
    c.fillStyle = PC.hair; c.beginPath(); c.ellipse(-0.03 * sc, -0.035 * sc, 0.095 * sc, 0.092 * sc, 0, Math.PI * 0.75, Math.PI * 1.78); c.lineTo(-0.03 * sc, -0.035 * sc); c.closePath(); c.fill();
    c.beginPath(); c.arc(-0.1 * sc, -0.045 * sc, 0.045 * sc, 0, 7); c.fill();   // bun
    c.fillStyle = '#20140f'; c.beginPath(); c.arc(0.055 * sc, -0.01 * sc, 0.011 * sc, 0, 7); c.fill();   // eye
    const mo = J.mouth; c.fillStyle = '#5a2520'; c.beginPath(); c.ellipse(0.07 * sc, 0.06 * sc, 0.022 * sc, (0.004 + 0.022 * mo) * sc, 0, 0, 7); c.fill();
    c.restore();
    arm(J.arms[0], false);
    if (J.palmUp > 0.3) { const h = q(J.arms[0].hand); c.strokeStyle = 'rgba(255,220,180,0.5)'; c.lineWidth = 1.2; c.beginPath(); c.arc(h[0], h[1] - 2, 0.04 * sc, Math.PI * 1.1, Math.PI * 1.9); c.stroke(); }
  }

  /* ---------- light on a puppet layer (rim from the door, dusk ambient) ---------- */
  function lightLayer(c, bb, warm, amb, fromLeft) {
    if (!bb) return; c.save(); c.globalCompositeOperation = 'source-atop';
    c.fillStyle = `rgba(30,40,80,${amb})`; c.fillRect(bb.x0 - 4, bb.y0 - 4, bb.x1 - bb.x0 + 8, bb.y1 - bb.y0 + 8);
    if (warm > 0.005) { const g = c.createLinearGradient(bb.x0, 0, bb.x0 + (bb.x1 - bb.x0) * 0.75, 0); g.addColorStop(0, `rgba(255,178,96,${0.62 * warm})`); g.addColorStop(0.35, `rgba(255,170,90,${0.25 * warm})`); g.addColorStop(1, 'rgba(255,170,90,0)');
      c.fillStyle = g; c.fillRect(bb.x0 - 4, bb.y0 - 4, bb.x1 - bb.x0 + 8, bb.y1 - bb.y0 + 8); }
    c.restore();
  }
  function measure(c, rx0, ry0, rx1, ry1) {
    rx0 = Math.max(0, rx0 | 0); ry0 = Math.max(0, ry0 | 0); rx1 = Math.min(W, rx1 | 0); ry1 = Math.min(H, ry1 | 0);
    const im = c.getImageData(rx0, ry0, rx1 - rx0, ry1 - ry0).data, w = rx1 - rx0; let n = 0, sx = 0, sy = 0, x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let y = 0; y < ry1 - ry0; y++) for (let x = 0; x < w; x++) { if (im[(y * w + x) * 4 + 3] > 127) { n++; sx += x; sy += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } }
    if (!n) return null; return { n, cx: rx0 + sx / n, cy: ry0 + sy / n, x0: rx0 + x0, y0: ry0 + y0, x1: rx0 + x1, y1: ry0 + y1 };
  }

  /* ---------- typed prompts, shown as the host's input panel ---------- */
  function prompt(i, f) {
    const t = f.t; let cur = null; for (const p of score.prompts) if (p[0] <= t + 1e-6) cur = p;
    if (!cur || t - cur[0] > 5.5) return;
    const age = t - cur[0], txt = cur[1], nch = Math.min(txt.length, Math.floor(age * 34)), a = clamp(1 - (age - 4.4) / 1.1);
    ctx.save(); ctx.globalAlpha = a; ctx.font = '400 17px "JetBrains Mono"'; ctx.fillStyle = 'rgba(14,12,18,0.55)';
    const wpx = ctx.measureText(txt).width; ctx.fillRect(28, 664, wpx + 50, 32);
    ctx.fillStyle = '#e8c48c'; ctx.fillText('›', 40, 686); ctx.fillStyle = '#efe6da'; ctx.fillText(txt.slice(0, nch), 60, 686); ctx.restore();
  }

  /* ---------- cards ---------- */
  function card(lines, a) {
    ctx.fillStyle = '#0f0d13'; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = a; ctx.textAlign = 'center';
    for (const [txt, font, col, y] of lines) { ctx.font = font; ctx.fillStyle = col; ctx.fillText(txt, W / 2, y); }
    ctx.globalAlpha = 1; ctx.textAlign = 'left';
  }
  function titleCard(i) {
    const a = clamp(i / 12) * clamp((TITLE - i) / 12);
    card([['PAE-02 · SCION 25 · RIVE', '800 64px "Big Shoulders Display"', '#efe6da', 320],
      ['Interactive puppet state machines', '400 30px Literata', '#d9b98a', 372],
      ['The threshold, handmade', '400 18px "JetBrains Mono"', '#9d93a6', 430]], a);
  }
  function endCard(i) {
    const a = clamp(i / 12) * clamp((END - i) / 12), m = '400 17px "JetBrains Mono"', c = '#cfc5d6';
    card([['What it is made of', '800 40px "Big Shoulders Display"', '#efe6da', 206],
      ['A dog authored here as a puppet: bones, round shapes bound to them, IK legs,', m, c, 270],
      ['keyed poses and loops, driven by its own state machine (Facing · Body · Attention)', m, c, 298],
      ['whose inputs are set each frame from the PAELEO score. The head leads the turns.', m, c, 326],
      ['Feet are planted by a stepping solver; nothing slides. Every transition and footfall is an event.', m, c, 354],
      ['House, door, light and person: drawn primitives. Sound: synthesized from the event trace.', m, c, 382],
      ['Proportions studied from Amateur Film New Jersey C (Internet Archive, public domain); no archive pixels.', m, '#9d93a6', 430],
      ['No found footage, no doodles, no generated images.', m, '#9d93a6', 458]], a);
  }

  /* ---------- the frame ---------- */
  let doorT0 = null;
  function sceneState(i) {
    const f = score.frames[i], t = f.t;
    if (doorT0 === null) { const k = score.frames.findIndex(g => g.door === 'open'); doorT0 = score.frames[k].t; }
    const openK = ease(clamp((t - doorT0 + 0.15) / 0.75));
    const phi = lerp(48, 106, openK);
    const p = f.person, block = (1 - ease(p.sit)) * clamp((p.x + 0.75) / 0.45);
    const Ldoor = lerp(0.38, 1.0, openK) * (1 - 0.7 * block);
    const push = clamp((t - (doorT0 - 0.5)) / 0.4) * clamp((doorT0 + 0.7 - t) / 0.35);
    return { f, t, phi, openK, block, Ldoor, push, lamp: 0.85 + 0.15 * openK };
  }
  function drawScene(si, out) {
    const st = sceneState(si), f = st.f, t = st.t;
    if (si < lastStep.i) { drive = DRIVE.make(score, puppet); FILM.drive = drive; lastStep.i = -1; FILM._walk = 0; FILM._soft = 0; }
    while (lastStep.i < si) { const r = drive.step(); lastStep.i = r.i; lastStep.r = r; FILM.events.push(...r.newEvents); }
    const r = lastStep.r, Sd = r.S;
    ctx.save(); sky(t); porch(t, st); interior(t, st, st.lamp);
    const L = { inside: 0.7 + 0.3 * st.openK, door: st.Ldoor, block: st.block };
    doorway(t, L, st.phi); const edge = leaf(st.phi);
    // person
    const p = f.person, z = lerp(0.04, 0.22, clamp((-p.x - 0.28) / 0.97));
    const prev = score.frames[Math.max(0, si - 1)].person; const walking = Math.abs(p.x - prev.x) > 1e-4 ? 1 : 0;
    FILM._walk = (FILM._walk || 0) + Math.abs(p.x - prev.x) / 0.55;
    const softLean = p.voice === 'soft' ? 1 : (FILM._soft || 0) * 0.9; FILM._soft = softLean;
    const J = personPose(p, { walk: FILM._walk, walking, softLean: Math.min(1, softLean), push: st.push, doorEdge: edge });
    pg.setTransform(1, 0, 0, 1, 0, 0); pg.clearRect(0, 0, W, H); drawPerson(pg, J, z);
    const pb = { x0: P(p.x - 0.3, 0, z)[0], x1: P(p.x + 0.8, 0, z)[0], y0: P(0, 1.9, z)[1], y1: P(0, 0, z)[1] };
    lightLayer(pg, pb, 0.45 * st.lamp, 0.18, true); ctx.drawImage(perCv, 0, 0);
    lightPool(L);
    // dog: draw into its own layer, measure it, cast its shadows, light it, composite
    dg.setTransform(1, 0, 0, 1, 0, 0); dg.clearRect(0, 0, W, H);
    RIVE.drawDog(dg, Sd, P, S, puppet.palette);
    const c0 = P(Sd.X, 0.35, 0); const m = measure(dg, c0[0] - 260, c0[1] - 220, c0[0] + 260, c0[1] + 150);
    const warmK = st.Ldoor / (1 + Math.pow(Math.max(0, Sd.X - 0.25) / 2.4, 2));
    // contact shadow
    const g0 = P(Sd.X, 0, 0); ctx.save(); ctx.fillStyle = 'rgba(10,8,14,0.45)'; ctx.filter = 'blur(5px)'; ctx.beginPath();
    ctx.ellipse(g0[0], g0[1] + 4, (m ? (m.x1 - m.x0) / 2 + 8 : 80), 11, 0, 0, 7); ctx.fill(); ctx.restore();
    // long shadow thrown away from the door by the door light (the dog's own layer, flattened onto the floor)
    if (warmK > 0.03 && m) { ctx.save(); ctx.globalAlpha = clamp(0.5 * warmK); ctx.filter = 'brightness(0) blur(3px)';
      const fy = g0[1] + 2; ctx.setTransform(1, 0, -1.6 * (0.6 + 0.4 * st.openK), -0.22, 1.6 * (0.6 + 0.4 * st.openK) * fy, fy * 1.22); ctx.drawImage(dogCv, 0, 0); ctx.restore(); }
    const db = m ? { x0: m.x0, x1: m.x1, y0: m.y0, y1: m.y1 } : null;
    lightLayer(dg, db, clamp(warmK * 0.95), 0.26 - 0.1 * clamp(warmK), true);
    ctx.save(); ctx.filter = 'drop-shadow(0 0 1.2px rgba(22,12,10,0.95))'; ctx.drawImage(dogCv, 0, 0); ctx.restore();
    cutFaces(); casing();
    // vignette and grain
    const v = ctx.createRadialGradient(W / 2, H * 0.55, H * 0.35, W / 2, H * 0.55, H * 0.95); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(6,4,10,0.5)');
    ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = 0.025; ctx.drawImage(noise, 0, 0); ctx.globalAlpha = 1;
    prompt(si, f);
    ctx.restore();
    // measured trace (from the rendered dog layer and the solved, drawn pose)
    if (out && !FILM.trace[si]) {
      const Pj = q => P(q[0], q[1], q[2]), nose = Pj(Sd.nose), sk = Pj(Sd.skull.p), ch = Pj(Sd.chest.p), rp = Pj(Sd.rump.p);
      const bodyMid = (ch[0] + rp[0]) / 2, facing = nose[0] < bodyMid ? 1 : -1;   // +1: muzzle toward the door and the person
      const backTop = Math.min(ch[1] - Sd.chest.r * S, (Pj(Sd.waist.p)[1] - Sd.waist.r * S));
      const headTop = sk[1] - Sd.skull.r * S;
      const hw = Sd.headFw, muzzleIn = Sd.muzzleTip.p[2] - Sd.skull.p[2];
      const lieMeasured = m ? (m.y1 - m.y0) / S : null;
      const F = drive.dog.sm.layers.map(l => l.state);
      FILM.trace[si] = { i: si, t: +t.toFixed(4), state: f.dog.state, x_score: f.dog.x, x_screen: m ? +m.cx.toFixed(2) : null, y_screen: m ? +m.cy.toFixed(2) : null,
        facing, posture: F[1] === 'Down' ? (r.inp.lie > 0.9 ? 'lying' : 'lying_down_or_rising') : F[1] === 'Walk' ? 'walking' : F[1] === 'Backing' ? 'backing' : (r.inp.crouch > 0.4 ? 'crouched' : 'standing'),
        sm: { facing: F[0], body: F[1], attention: F[2] }, yaw: +drive.dog.yaw.toFixed(2), head_rel: +drive.dog.headRel.toFixed(2),
        bbox: m ? [m.x0, m.y0, m.x1, m.y1] : null, height_m: lieMeasured !== null ? +lieMeasured.toFixed(3) : null,
        head_below_back_px: +(headTop - backTop).toFixed(1), nose_screen: [+nose[0].toFixed(1), +nose[1].toFixed(1)],
        muzzle_depth_m: +muzzleIn.toFixed(3), head_world_yaw: +(drive.dog.yaw + drive.dog.headRel + (Sd.ch.headYawAdd || 0)).toFixed(1),
        front_x_world: +Math.min(...Sd.legs.map(l => l.paw[0]), Sd.nose[0]).toFixed(3), tail_x_world: +Math.max(...Sd.tail.map(q => q[0])).toFixed(3),
        feet: Sd.legs.map(l => ({ n: l.n, x: +l.paw[0].toFixed(4), z: +l.paw[2].toFixed(4), y: +l.paw[1].toFixed(4), planted: l.planted })) };
    }
  }
  window.frame = function (n, q) {
    if (n < TITLE) titleCard(n);
    else if (n < TITLE + SCENE) drawScene(n - TITLE, true);
    else endCard(n - TITLE - SCENE);
    return q ? cv.toDataURL('image/jpeg', q) : '';
  };
  FILM.setView = (kx, ky) => { KX = kx; KY = ky; };
  FILM.dogState = () => ({ layers: drive.dog.sm.layers.map(l => [l.name, l.state]), inputs: Object.assign({}, drive.dog.inputs.v), bbox: FILM.trace[lastStep.i] && FILM.trace[lastStep.i].bbox });
  FILM.init = async function () {
    if (window.__DATA) { score = window.__DATA.score; puppet = window.__DATA.puppet; }
    else { const B = window.FILM_BASE || { score: '../../score/threshold-score.json', puppet: 'puppet.json' }; score = await (await fetch(B.score)).json(); puppet = await (await fetch(B.puppet)).json(); }
    drive = DRIVE.make(score, puppet); FILM.drive = drive;
    cv = document.getElementById('c'); ctx = cv.getContext('2d');
    dogCv = document.createElement('canvas'); dogCv.width = W; dogCv.height = H; dg = dogCv.getContext('2d', { willReadFrequently: true });
    perCv = document.createElement('canvas'); perCv.width = W; perCv.height = H; pg = perCv.getContext('2d');
    noise = document.createElement('canvas'); noise.width = W + 256; noise.height = H + 256; const nc = noise.getContext('2d'), id = nc.createImageData(noise.width, noise.height), rr = rng(3);
    for (let k = 0; k < id.data.length; k += 4) { const v = rr() * 255; id.data[k] = id.data[k + 1] = id.data[k + 2] = v; id.data[k + 3] = 255; } nc.putImageData(id, 0, 0);
    const rs = rng(11); stars = Array.from({ length: 70 }, () => ({ x: 380 + rs() * 900, y: 130 + rs() * 260, r: rs() < 0.15 ? 2 : 1, a: 0.3 + rs() * 0.6, t0: 4 + rs() * 24 }));
    await document.fonts.ready; FILM.ready = true;
  };
  window.ready = FILM.init();
})();
