// 03 · Incitement to Suicide — CONSEQUENCE · SCION 18 (Cartoon Saloon — Painterly Puppet Discipline)
// The household after. Built as layered drawings over a hand-painted, patterned interior:
//   PAINT  : cached backdrop plates (wallpaper of spirals, floorboards, window, door, mantel) painted once per palette;
//   PALETTE: compositing palettes (NIGHT -> DAWN) are swapped over the same drawings, never re-drawn;
//   DRAWING: each sack is a fixed set of drawings from a turn sheet (front / three-quarter / back) and an ear sheet
//            (up, perk, flat, down, hang, lift) — key drawings are REPLACED, never interpolated;
//   RIG    : a selective deformable rig only where the shot needs it: body shear (lean) and squash, and the sheet (a cloth
//            drawing morphed from folded to draped). Ears, wig, shawl, belt, stencil ride on the body as overlays.
//   LINE   : invariant (numerically testable) — every ink line is LW px on screen whatever the pose, scale or deformation
//            (no transforms on stroked paths; points are mapped, then stroked at constant width).
// Branches read the ledger: guilt (st.mind[A][V].guilt) decides whether the doer goes back with a sheet or goes cold;
// a living third sack may appear in the doorway with a candle (grief vs suspicion from its mind & beliefs); two or more
// dead bring the police lamp and the knock; an already-dead victim or a dead doer play as contradictions (old sheet / ghost).
// Myth levers: shadow (doer's wall shadow grows from its before- to after-value), loom, shrink, grey, halo, weight, tempo.
(function () {
  const W = 1920, H = 1080, LW = 3.2, FLOOR = 930, WALLB = 720;
  const hs = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const cl = (a, b, x) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  const sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u); };
  const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const mix = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
  const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
  const rgb = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a === undefined ? 1 : a})`;
  const grey = (c, u) => { const l = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]; return mix(c, [l * .95, l * .96, l * 1.02], u); };
  const IDS = ['R', 'B', 'I', 'O'];
  const DUR = 3.4;

  // ---------- compositing palettes (shot style contract: two palettes, one set of drawings) ----------
  const PAL = {
    night: { wall: hex('#1e2334'), pat: hex('#2a3047'), patLine: hex('#343b56'), floor: hex('#191b25'), board: hex('#101219'), win: hex('#3e4d74'), sky: hex('#1b2440'), amb: 0.5, ink: hex('#07080d'), cold: hex('#5a6a92') },
    dawn: { wall: hex('#434a5b'), pat: hex('#4d5568'), patLine: hex('#5a637a'), floor: hex('#30333d'), board: hex('#24262e'), win: hex('#c6d1df'), sky: hex('#9fb0c8'), amb: 0.86, ink: hex('#14161d'), cold: hex('#d8e2ee') }
  };
  // sack fills and attribute colours (identity survives every palette)
  const FILL = { R: hex('#d6bf96'), B: hex('#e8d5ae'), I: hex('#e2cea5'), O: hex('#f0e4c8') };
  const SHAWL = hex('#6e3a33'), BELT = hex('#2a2622'), WIG = hex('#7a3b8f'), LINEN = hex('#efeae0');
  // turn/expression sheet constants per sack: body construction (side bulge, top dip, top narrowing) and ear sheet
  const BUILD = { R: { side: .56, dip: .07, top: .46, earL: .26 }, B: { side: .55, dip: .04, top: .45, earL: .17 }, I: { side: .64, dip: .24, top: .38, earL: .78 }, O: { side: .52, dip: .03, top: .44, earL: .16 } };
  // ear drawings: angle of the right ear in degrees (0 = right, -90 = up, 90 = down); left is mirrored
  const EAR = { up: -58, perk: -82, flat: -14, down: 42, hang: 84, lift: -6 };

  // ---------- painted texture (hand-painted, cached once, locked to each sack, never boils) ----------
  const TEX = {};
  function paperTex() {
    if (TEX.paper) return TEX.paper;
    const c = document.createElement('canvas'); c.width = 512; c.height = 512; const x = c.getContext('2d');
    x.fillStyle = '#fff'; x.fillRect(0, 0, 512, 512);
    for (let i = 0; i < 70; i++) { // watercolour blooms
      const px = hs(i * 3.7 + 1) * 512, py = hs(i * 5.1 + 2) * 512, r = 30 + hs(i * 2.9) * 110;
      const gr = x.createRadialGradient(px, py, r * .2, px, py, r); const a = .05 + .09 * hs(i * 7.3);
      gr.addColorStop(0, `rgba(120,100,80,${a})`); gr.addColorStop(.85, `rgba(90,70,55,${a * 1.4})`); gr.addColorStop(1, 'rgba(90,70,55,0)');
      x.fillStyle = gr; x.fillRect(px - r, py - r, 2 * r, 2 * r);
    }
    for (let i = 0; i < 900; i++) { // dry-brush fibre strokes
      const px = hs(i * .73 + 9) * 512, py = hs(i * 1.31 + 4) * 512, l = 6 + hs(i * 2.1) * 22;
      x.strokeStyle = `rgba(70,55,40,${.04 + .06 * hs(i * 4.4)})`; x.lineWidth = 1; x.beginPath(); x.moveTo(px, py); x.lineTo(px + l, py + (hs(i) - .5) * 4); x.stroke();
    }
    return (TEX.paper = c);
  }

  // ---------- backdrop plates: painted once per palette, then cross-faded ----------
  function spiral(x, cx, cy, r, turns, ph) {
    x.beginPath(); for (let k = 0; k <= 40; k++) { const u = k / 40, a = ph + u * turns * Math.PI * 2, rr = r * (1 - u * .85); const px = cx + Math.cos(a) * rr, py = cy + Math.sin(a) * rr; k ? x.lineTo(px, py) : x.moveTo(px, py); } x.stroke();
  }
  function plate(name) {
    if (TEX['bg' + name]) return TEX['bg' + name];
    const P = PAL[name], c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
    x.fillStyle = rgb(P.wall); x.fillRect(0, 0, W, WALLB);
    // wallpaper: a hand-repeated motif (triple spiral in a ring), slightly irregular placement
    x.lineCap = 'round'; x.lineWidth = 2.2;
    for (let j = 0; j < 9; j++) for (let i = 0; i < 17; i++) {
      const cx = 60 + i * 118 + (j % 2) * 59 + (hs(i * 13 + j) - .5) * 6, cy = 40 + j * 84 + (hs(i + j * 17) - .5) * 6;
      x.strokeStyle = rgb(P.pat); x.beginPath(); x.arc(cx, cy, 30, 0, Math.PI * 2); x.stroke();
      x.strokeStyle = rgb(P.patLine);
      for (let q = 0; q < 3; q++) { const a = q * 2.094 + .4, sx = cx + Math.cos(a) * 11, sy = cy + Math.sin(a) * 11; spiral(x, sx, sy, 10, 1.3, a + Math.PI); }
    }
    // dado rail and skirting
    x.fillStyle = rgb(mul(P.wall, .7)); x.fillRect(0, WALLB - 140, W, 14); x.fillRect(0, WALLB - 22, W, 22);
    x.fillStyle = rgb(mul(P.wall, .82)); x.fillRect(0, WALLB - 126, W, 104);
    // window (left) — outside sky only; police lamp and neighbours are drawn live over it
    x.fillStyle = rgb(P.sky); x.fillRect(250, 150, 240, 290);
    x.fillStyle = rgb(mul(P.wall, .55)); x.fillRect(236, 136, 268, 14); x.fillRect(236, 440, 268, 18);
    // door (centre back)
    x.fillStyle = rgb(mul(P.wall, .5)); x.fillRect(1650, 300, 170, WALLB - 300);
    x.fillStyle = rgb(mul(P.wall, .25)); x.fillRect(1664, 314, 142, WALLB - 314);
    // mantel shelf (right)
    x.fillStyle = rgb(mul(P.wall, .45)); x.fillRect(640, 440, 360, 16); x.fillRect(660, 456, 18, 40); x.fillRect(962, 456, 18, 40);
    // floor: boards converging, painted
    x.fillStyle = rgb(P.floor); x.fillRect(0, WALLB, W, H - WALLB);
    x.strokeStyle = rgb(P.board); x.lineWidth = 3;
    for (let i = -14; i <= 14; i++) { x.beginPath(); x.moveTo(W / 2 + i * 70, WALLB); x.lineTo(W / 2 + i * 210, H); x.stroke(); }
    for (let j = 0; j < 5; j++) { const y = WALLB + 30 + j * j * 16; x.globalAlpha = .4; x.beginPath(); x.moveTo(0, y); x.lineTo(W, y); x.stroke(); x.globalAlpha = 1; }
    // rug under the victim's place: concentric painted bands
    x.save(); x.translate(1290, 955); x.scale(1, .2);
    [[330, .5], [290, .35], [250, .55], [170, .4]].forEach(([r, k], i) => { x.fillStyle = rgb(mix(P.floor, i % 2 ? hex('#5a2f2c') : hex('#3b4a5c'), k)); x.beginPath(); x.arc(0, 0, r, 0, Math.PI * 2); x.fill(); });
    x.restore();
    // paint the whole plate with the paper texture
    x.globalCompositeOperation = 'multiply'; x.globalAlpha = .55; const tx = paperTex();
    for (let px = 0; px < W; px += 512) for (let py = 0; py < H; py += 512) x.drawImage(tx, px, py);
    return (TEX['bg' + name] = c);
  }

  // ---------- the sack drawing: points mapped through the rig, then stroked at constant width ----------
  function mapper(P) { // local (x right, y up-negative from base centre) -> screen, with shear lean
    return (x, y) => [P.x + x - P.lean * y, P.y + y];
  }
  function dims(id, P) {
    const C = CAST(id); let w = C.w * P.s, h = C.h * P.s;
    if (P.view === 'tq') w *= .9;
    w *= 1 + P.squash * .55; h *= 1 - P.squash;
    if (P.tags && P.tags.includes('emptied')) { h *= .84; w *= 1.05; }
    return { w, h };
  }
  function bodyPath(g, id, P, M) {
    const B = BUILD[id], { w, h } = dims(id, P);
    const p = (x, y) => M(x, y), tw = w * B.top;
    const pinch = P.tags && P.tags.includes('cinched') ? .1 : 0;
    g.beginPath();
    let a = p(-w / 2, 0); g.moveTo(a[0], a[1]);
    let c1 = p(-w * .2, 5 * P.s), c2 = p(w * .2, 5 * P.s), e = p(w / 2, 0); g.bezierCurveTo(c1[0], c1[1], c2[0], c2[1], e[0], e[1]);
    c1 = p(w * B.side, -h * .35); c2 = p(w * (B.side - .04 - pinch), -h * .8); e = p(tw, -h); g.bezierCurveTo(c1[0], c1[1], c2[0], c2[1], e[0], e[1]);
    c1 = p(0, -h * (1 - B.dip * 2)); e = p(-tw, -h); g.quadraticCurveTo(c1[0], c1[1], e[0], e[1]);
    c1 = p(-w * (B.side - .04 - pinch), -h * .8); c2 = p(-w * B.side, -h * .35); e = p(-w / 2, 0); g.bezierCurveTo(c1[0], c1[1], c2[0], c2[1], e[0], e[1]);
    g.closePath();
  }
  function earPath(g, id, P, M, side) {
    const B = BUILD[id], { w, h } = dims(id, P), tw = w * B.top;
    let ang = EAR[P.ears] ?? EAR.up; if (side < 0) ang = 180 - ang;
    const r = ang * Math.PI / 180, L = B.earL * CAST(id).h * P.s * (id === 'I' ? 1 : 1);
    const base = [side * tw, -h], bw = id === 'I' ? .16 * w : .11 * w;
    const tip = [base[0] + Math.cos(r) * L, base[1] + Math.sin(r) * L];
    const b1 = [base[0] - side * bw, base[1] + 2], b2 = [base[0] + side * 2, base[1] + bw * .9];
    const q = (pt) => M(pt[0], pt[1]);
    const A1 = q(b1), T = q(tip), A2 = q(b2), mid1 = q([(b1[0] + tip[0]) / 2 - Math.sin(r) * bw * .3 * side, (b1[1] + tip[1]) / 2 - bw * .2]), mid2 = q([(b2[0] + tip[0]) / 2 + bw * .2 * side, (b2[1] + tip[1]) / 2 + bw * .1]);
    g.beginPath(); g.moveTo(A1[0], A1[1]); g.quadraticCurveTo(mid1[0], mid1[1], T[0], T[1]); g.quadraticCurveTo(mid2[0], mid2[1], A2[0], A2[1]); g.closePath();
    return T;
  }
  function inkOf(c) { return mul(c, .38); }
  function paintFill(g, id, base, alpha) { // flat painted fill + locked texture
    g.fillStyle = rgb(base, alpha); g.fill();
    g.save(); g.clip(); g.globalCompositeOperation = 'multiply'; g.globalAlpha = .5 * alpha;
    const tx = paperTex(), o = { R: 0, B: 130, I: 260, O: 390 }[id]; g.drawImage(tx, o, o, 512, 512, 0, 0, W, H); g.restore();
  }
  function drawSack(g, id, P, pal) {
    const M = mapper(P), { w, h } = dims(id, P), a = P.alpha ?? 1;
    let base = mul(FILL[id], pal.amb * (P.lit ?? 1)); base = grey(base, P.grey || 0);
    const ink = rgb(inkOf(base), a);
    g.lineJoin = 'round'; g.lineCap = 'round';
    // ears behind the body (drawn first so the body overlaps their base)
    for (const s of [-1, 1]) { earPath(g, id, P, M, s); paintFill(g, id, mul(base, .93), a); g.strokeStyle = ink; g.lineWidth = LW; g.stroke(); }
    bodyPath(g, id, P, M); paintFill(g, id, base, a); g.save(); g.lineWidth = LW; g.strokeStyle = ink; g.stroke(); g.restore();
    // halo lever: the light finds it (rim line on the window side)
    if (P.halo > .05) { g.save(); bodyPath(g, id, P, M); g.clip(); g.strokeStyle = rgb(pal.cold, .55 * P.halo * a); g.lineWidth = LW * 3; g.translate(5, 0); bodyPath(g, id, P, M); g.stroke(); g.restore(); }
    g.save(); bodyPath(g, id, P, M); g.clip();
    const shade = (pts, col, al) => { g.beginPath(); pts.forEach((q, i) => { const m = M(q[0], q[1]); i ? g.lineTo(m[0], m[1]) : g.moveTo(m[0], m[1]); }); g.closePath(); g.fillStyle = rgb(col, al * a); g.fill(); };
    // painted core shadow away from the window
    shade([[w * .1, 6], [w * .7, 6], [w * .7, -h * 1.1], [w * .25, -h * 1.1]], mul(base, .78), .55);
    const ofs = P.view === 'tq' ? -P.face * w * .14 : 0;
    const gcol = c => grey(mul(c, pal.amb * 1.15 * (P.lit ?? 1)), (P.grey || 0) * .55); // attributes keep identity while the cloth greys
    if (id === 'R') { shade([[-w, -h * .8], [w, -h * .8], [w, -h * 1.2], [-w, -h * 1.2]], gcol(SHAWL), 1);
      if (P.view !== 'back') shade([[ofs - w * .06, -h * .8], [ofs + w * .08, -h * .8], [ofs + w * .13, -h * .55], [ofs - w * .02, -h * .58]], gcol(SHAWL), 1); }
    if (id === 'B') { shade([[-w, -h * .37], [w, -h * .37], [w, -h * .45], [-w, -h * .45]], gcol(BELT), 1);
      if (P.view !== 'back') { const cx = ofs, cy = -h * .68, r = w * .15; const m = M(cx, cy); g.strokeStyle = rgb(mul(gcol(BELT), 1.3), .7 * a); g.lineWidth = LW; g.beginPath(); g.arc(m[0], m[1], r, 0, Math.PI * 2); g.stroke();
        g.beginPath(); g.moveTo(m[0], m[1] + r * .8); g.lineTo(m[0], m[1] - r * .7); for (let k = 0; k < 3; k++) { const yy = m[1] - r * .5 + k * r * .35; g.moveTo(m[0], yy + r * .2); g.lineTo(m[0] - r * .35, yy); g.moveTo(m[0], yy + r * .2); g.lineTo(m[0] + r * .35, yy); } g.stroke(); } }
    if (P.view === 'back') { const m1 = M(0, -4), m2 = M(0, -h * .95); g.strokeStyle = rgb(inkOf(base), .5 * a); g.lineWidth = LW * .7; g.setLineDash([6, 7]); g.beginPath(); g.moveTo(m1[0], m1[1]); g.lineTo(m2[0], m2[1]); g.stroke(); g.setLineDash([]); }
    g.restore();
    // carried damage, modestly, as painted marks
    const T = P.tags || [];
    const line = (pts, col, lw) => { g.beginPath(); pts.forEach((q, i) => { const m = M(q[0], q[1]); i ? g.lineTo(m[0], m[1]) : g.moveTo(m[0], m[1]); }); g.strokeStyle = rgb(col, a); g.lineWidth = lw; g.stroke(); };
    if (T.includes('rope')) { line([[-w * .52, -h * .3], [w * .52, -h * .22]], hex('#8a6a3c'), LW * 1.3); line([[-w * .5, -h * .58], [w * .5, -h * .5]], hex('#8a6a3c'), LW * 1.3); }
    if (T.includes('gag')) line([[-w * .45, -h * .9], [w * .45, -h * .9]], hex('#cfc6b4'), LW * 2.4);
    if (T.includes('cinched')) line([[-w * .48, -h * .84], [w * .48, -h * .84]], hex('#5a4630'), LW);
    if (T.includes('torn')) { const pts = []; for (let k = 0; k <= 6; k++) pts.push([w * (.12 + (k % 2) * .06), -h * (.2 + k * .07)]); line(pts, inkOf(base), LW * .8); }
    if (T.includes('blot')) { const m = M(-w * .15, -h * .45); g.fillStyle = rgb(hex('#14182a'), .85 * a); g.beginPath(); g.ellipse(m[0], m[1], w * .1, w * .07, .4, 0, Math.PI * 2); g.fill(); }
    if (T.includes('tag')) { const m = M(w * .18, -h * .62); g.fillStyle = rgb(mul(hex('#e9e2cf'), pal.amb), a); g.fillRect(m[0] - 14, m[1] - 9, 28, 18); g.strokeStyle = ink; g.lineWidth = LW * .6; g.strokeRect(m[0] - 14, m[1] - 9, 28, 18); }
    if (T.includes('coins')) for (let k = 0; k < 3; k++) { const m = M(-w * .45 - 16 - k * 3, -4 - k * 7); g.fillStyle = rgb(mul(hex('#c9a640'), pal.amb * 1.2), a); g.strokeStyle = rgb(hex('#5d4a18'), a); g.lineWidth = 2; g.beginPath(); g.ellipse(m[0], m[1], 13, 5, 0, 0, Math.PI * 2); g.fill(); g.stroke(); }
    // Ogiva's wig: drawn over the top, hanging past the shoulders
    if (id === 'O') {
      const skew = T.includes('wig') ? .12 : 0, wg = gcol(WIG), M2 = (x, y) => M(x + skew * w * (-y / h), y);
      const pts = P.view === 'back' ? [[-w * .6, -h * .38], [-w * .58, -h * 1.03], [0, -h * 1.15], [w * .58, -h * 1.03], [w * .6, -h * .38], [0, -h * .42]]
        : [[-w * .62, -h * .4], [-w * .57, -h * 1.03], [0, -h * 1.15], [w * .57, -h * 1.03], [w * .62, -h * .4], [w * .34, -h * .5], [w * .3, -h * .86], [0, -h * .9], [-w * .3, -h * .86], [-w * .34, -h * .5]];
      const sw = P.wigSwing || 0;
      g.beginPath(); pts.forEach((q, i) => { const yy = q[1], sx = sw * (1 + yy / h) * 14; const m = M2(q[0] + sx, yy); i ? g.lineTo(m[0], m[1]) : g.moveTo(m[0], m[1]); }); g.closePath();
      paintFill(g, 'O', wg, a); g.strokeStyle = rgb(inkOf(wg), a); g.lineWidth = LW; g.stroke();
      // painted strand lines
      g.strokeStyle = rgb(mul(wg, 1.35), .6 * a); g.lineWidth = LW * .6;
      for (const sx of [-.48, -.4, .4, .48]) { const m1 = M2(w * sx * .95, -h * 1.0), m2 = M2(w * sx + sw * 10, -h * .46); g.beginPath(); g.moveTo(m1[0], m1[1]); g.lineTo(m2[0], m2[1]); g.stroke(); }
    }
  }
  function castShadows(g, id, P, pal, wallLen, wallA) {
    const { w } = dims(id, P), a = P.alpha ?? 1;
    // floor contact shadow
    g.fillStyle = rgb(mul(pal.floor, .35), .7 * a); g.beginPath(); g.ellipse(P.x + w * .1, P.y + 4, w * .62, 12 * P.s, 0, 0, Math.PI * 2); g.fill();
    // wall shadow (myth lever 'shadow'): the silhouette thrown up the wall, away from the window, growing with the lever
    if (wallA > .01) {
      const k = wallLen, dx = 170 + 80 * k;
      const M = (x, y) => [P.x + dx + x * (1 + .25 * k) - (-y) * .25 * k, P.y - 165 + y * (1 + .9 * k)];
      g.save(); g.beginPath(); g.rect(0, 0, W, WALLB); g.clip();
      bodyPath(g, id, P, M); g.fillStyle = rgb(hex('#04050a'), wallA * a); g.fill();
      for (const s of [-1, 1]) { earPath(g, id, P, M, s); g.fill(); }
      g.restore();
    }
  }
  function CAST(id) { return { R: { w: 168, h: 122 }, B: { w: 244, h: 214 }, I: { w: 128, h: 98 }, O: { w: 80, h: 184 } }[id]; }
  function hbox(id, P) { const { w, h } = dims(id, P); const e = BUILD[id].earL * CAST(id).h * P.s; return { x: P.x - w * .6 + Math.min(0, P.lean * h), y: P.y - h - e * .8, w: w * 1.2 + Math.abs(P.lean * h), h: h + e * .8 }; }

  // ---------- props: the cold lamp, the sheet, the laundry basket, the mantel lamps, the candle ----------
  function drawLamp(g, x, y, s, pal, smoke, t, seed, lit) {
    const brass = mul(hex('#8c6c3a'), pal.amb), glass = mul(hex('#9aa6b4'), pal.amb), ink = rgb(mul(brass, .35));
    g.lineWidth = LW; g.strokeStyle = ink; g.lineJoin = 'round';
    g.fillStyle = rgb(brass); g.beginPath(); g.ellipse(x, y - 8 * s, 30 * s, 10 * s, 0, 0, Math.PI * 2); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(x - 22 * s, y - 10 * s); g.quadraticCurveTo(x - 30 * s, y - 40 * s, x - 12 * s, y - 52 * s); g.lineTo(x + 12 * s, y - 52 * s); g.quadraticCurveTo(x + 30 * s, y - 40 * s, x + 22 * s, y - 10 * s); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = rgb(glass, .55); g.beginPath(); g.moveTo(x - 10 * s, y - 52 * s); g.quadraticCurveTo(x - 24 * s, y - 80 * s, x - 9 * s, y - 104 * s); g.lineTo(x + 9 * s, y - 104 * s); g.quadraticCurveTo(x + 24 * s, y - 80 * s, x + 10 * s, y - 52 * s); g.closePath(); g.fill(); g.stroke();
    if (lit) { const gr = g.createRadialGradient(x, y - 75 * s, 0, x, y - 75 * s, 160 * s); gr.addColorStop(0, `rgba(255,200,120,${.5 * lit})`); gr.addColorStop(1, 'rgba(255,200,120,0)'); g.fillStyle = gr; g.fillRect(x - 160 * s, y - 235 * s, 320 * s, 320 * s); }
    else { g.fillStyle = rgb(hex('#0b0b0b')); g.fillRect(x - 2 * s, y - 64 * s, 4 * s, 9 * s); }
    if (smoke > .01) { // the thread of smoke from the wick (hand-drawn sinuous line)
      g.strokeStyle = rgb(mul(pal.cold, .9), .5 * smoke); g.lineWidth = LW * .8; g.beginPath();
      for (let k = 0; k <= 24; k++) { const u = k / 24, yy = y - 104 * s - u * 220 * s * (0.5 + 0.5 * smoke), xx = x + Math.sin(u * 7 + t * 2.2 + seed) * 18 * s * u; k ? g.lineTo(xx, yy) : g.moveTo(xx, yy); }
      g.stroke();
    }
  }
  function drawStool(g, x, pal) {
    const wood = mul(hex('#5a3d28'), pal.amb), ink = rgb(mul(wood, .4));
    g.fillStyle = rgb(wood); g.strokeStyle = ink; g.lineWidth = LW;
    g.beginPath(); g.rect(x - 60, FLOOR - 170, 120, 18); g.fill(); g.stroke();
    for (const dx of [-48, 40]) { g.beginPath(); g.rect(x + dx, FLOOR - 152, 9, 152); g.fill(); g.stroke(); }
  }
  // the sheet: one cloth drawing with a deformable rig — u=0 folded (carried), u=1 draped over a body box
  function drawSheet(g, pal, u, carry, vb, age, flutter) {
    const lin = grey(mul(LINEN, pal.amb), age * .5), ink = rgb(mul(lin, .45));
    const fx = carry.x, fy = carry.y; // folded square, sitting on top of the carrier
    const F = [[fx - 55, fy], [fx + 55, fy], [fx + 55, fy - 26], [fx - 55, fy - 26]];
    const cx = vb.x + vb.w / 2, top = vb.y - 14, L = vb.x - 40, R = vb.x + vb.w + 40;
    const D = [[L - 10, FLOOR + 6], [R + 14, FLOOR + 8], [R - vb.w * .12, top + vb.h * .25], [L + vb.w * .12, top + vb.h * .2]];
    const lift = Math.sin(Math.PI * u) * 160; // arc of the throw
    const P = F.map((p, i) => [lerp(p[0], D[i][0], u), lerp(p[1], D[i][1], u) - lift + (i > 1 ? flutter * Math.sin(u * 12 + i) * 10 * (1 - u) : 0)]);
    const apex = [lerp(fx, cx, u), lerp(fy - 30, top, u) - lift];
    g.beginPath(); g.moveTo(P[0][0], P[0][1]);
    // hem (wavy), right side, crown, left side
    for (let k = 1; k <= 6; k++) { const q = k / 6; g.lineTo(lerp(P[0][0], P[1][0], q), lerp(P[0][1], P[1][1], q) + Math.sin(q * 9) * 5 * u); }
    g.quadraticCurveTo(lerp(P[1][0], P[2][0], .2) + 10 * u, lerp(P[1][1], P[2][1], .5), P[2][0], P[2][1]);
    g.quadraticCurveTo(apex[0] + vb.w * .35 * u, apex[1], apex[0], apex[1]);
    g.quadraticCurveTo(apex[0] - vb.w * .35 * u, apex[1], P[3][0], P[3][1]);
    g.quadraticCurveTo(lerp(P[0][0], P[3][0], .2) - 10 * u, lerp(P[0][1], P[3][1], .5), P[0][0], P[0][1]);
    g.closePath(); g.fillStyle = rgb(lin); g.fill(); g.strokeStyle = ink; g.lineWidth = LW; g.lineJoin = 'round'; g.stroke();
    if (u > .6) { // fold lines
      g.save(); g.globalAlpha = sm(.6, 1, u); g.strokeStyle = rgb(mul(lin, .7)); g.lineWidth = LW * .8;
      for (const f of [-.3, .05, .35]) { g.beginPath(); g.moveTo(cx + f * vb.w, top + vb.h * .35); g.quadraticCurveTo(cx + f * vb.w * 1.3, top + vb.h * .7, cx + f * vb.w * 1.5, FLOOR); g.stroke(); }
      g.restore();
    }
  }
  function drawBasket(g, x, pal, hasSheet) {
    const wick = mul(hex('#7a5a34'), pal.amb), ink = rgb(mul(wick, .4));
    if (hasSheet) { g.fillStyle = rgb(mul(LINEN, pal.amb)); g.strokeStyle = rgb(mul(LINEN, pal.amb * .45)); g.lineWidth = LW; g.beginPath(); g.ellipse(x, FLOOR - 62, 62, 20, 0, Math.PI, 0); g.fill(); g.stroke(); }
    g.fillStyle = rgb(wick); g.strokeStyle = ink; g.lineWidth = LW;
    g.beginPath(); g.moveTo(x - 70, FLOOR - 62); g.lineTo(x + 70, FLOOR - 62); g.lineTo(x + 56, FLOOR); g.lineTo(x - 56, FLOOR); g.closePath(); g.fill(); g.stroke();
    g.strokeStyle = rgb(mul(wick, .7)); for (let k = 1; k < 4; k++) { g.beginPath(); g.moveTo(x - 70 + k * 3.5, FLOOR - 62 + k * 15); g.lineTo(x + 70 - k * 3.5, FLOOR - 62 + k * 15); g.stroke(); }
  }
  // the household's four lamps on the mantel: each holder is a little cast of its sack's silhouette
  function mantel(g, pal, alive, outAt, t, dim) {
    IDS.forEach((s, i) => {
      const x = 690 + i * 90, y = 440, C = CAST(s), w = C.w * .26, h = C.h * .26;
      const col = s === 'R' ? SHAWL : s === 'B' ? BELT : s === 'O' ? WIG : hex('#b8a27a');
      g.fillStyle = rgb(mul(col, pal.amb * 1.2)); g.strokeStyle = rgb(mul(col, .35)); g.lineWidth = LW * .7;
      g.beginPath(); g.rect(x - w / 2, y - h, w, h); g.fill(); g.stroke();
      g.fillStyle = rgb(mul(hex('#e8e0cc'), pal.amb)); g.fillRect(x - 4, y - h - 24, 8, 24); g.strokeRect(x - 4, y - h - 24, 8, 24);
      let f = s in outAt ? 1 - sm(outAt[s], outAt[s] + .25, t) : (alive[s] ? 1 : 0);
      if (dim && s === dim) f = lerp(1, .32, sm(.4, 1.0, t)) * (1 + .15 * Math.sin(t * 9)); // guttering low, not out
      if (f > .02) { const fl = 1 + .08 * Math.sin(t * 17 + i * 3);
        const gr = g.createRadialGradient(x, y - h - 34, 0, x, y - h - 34, 34 * f); gr.addColorStop(0, `rgba(255,205,130,${.55 * f})`); gr.addColorStop(1, 'rgba(255,205,130,0)'); g.fillStyle = gr; g.fillRect(x - 40, y - h - 74, 80, 80);
        g.fillStyle = `rgba(255,226,160,${f})`; g.beginPath(); g.ellipse(x, y - h - 32, 4.5 * f, 9 * f * fl, 0, 0, Math.PI * 2); g.fill(); }
      else { g.fillStyle = '#0b0b0b'; g.fillRect(x - 1, y - h - 29, 2, 5); }
      if (s in outAt) { const u = sm(outAt[s], outAt[s] + 1.4, t); if (u > 0 && u < 1) { g.strokeStyle = rgb(pal.cold, .5 * (1 - u)); g.lineWidth = 2; g.beginPath(); for (let k = 0; k <= 12; k++) { const q = k / 12; const yy = y - h - 30 - q * 90 * u, xx = x + Math.sin(q * 6 + t * 3) * 8 * q; k ? g.lineTo(xx, yy) : g.moveTo(xx, yy); } g.stroke(); } }
    });
  }

  // ---------- the plan: every branch chosen from the ledger, shared by beat and sound ----------
  function endMarks(A, V) {
    try { const D = window.DEEDS && DEEDS.incitement; if (D && D.marks) { const m = D.marks(6, A, V, window.K); return { a: m.A.x + m.A.w / 2, v: m.V.x + m.V.w / 2 }; } } catch (e) { }
    return { a: 700, v: 1260 };
  }
  function plan(ev, st, before) {
    const A = ev.A, V = ev.V, imp = (st.impossible || []).filter(q => q.k === ev.k);
    const em = endMarks(A, V);
    const p = { A, V, ax: cl(380, 860, em.a), vx: cl(1160, 1320, em.v) };
    p.lampX = p.vx + 250; p.basket = p.ax - 300;
    if (p.basket < 120) { p.basket = 120; }
    const ghost = imp.some(q => q.who === A), already = imp.some(q => q.who === V) || (before && !before.alive[V]);
    const m = st.mind[A][V], guilt = m.guilt, pride = m.pride;
    p.mode = ghost ? 'ghost' : already ? 'already' : guilt >= .6 ? 'mourn' : 'cold';
    p.guilt = guilt; p.pride = pride;
    // the third sack: who comes to the door, and how it reads the room
    let best = null;
    for (const o of IDS) { if (o === A || o === V || !st.alive[o]) continue;
      const grief = (st.mind[o][V].desire || 0) + .5 * (st.mind[o][V].debt || 0) + (o === 'B' ? .6 : 0) + (o === 'I' ? .1 : 0);
      const bel = st.belief && st.belief[o] && st.belief[o][A] ? st.belief[o][A].harm.m : 0;
      const susp = (st.mind[o][A].grudge || 0) + .5 * (st.mind[o][A].fear || 0) + bel + .3 * ({ R: .9, B: .4, I: .2, O: .8 }[o]);
      const sc = Math.max(grief, susp); if (sc > .4 && (!best || sc > best.sc)) best = { who: o, sc, kind: susp > grief ? 'suspect' : 'grieve' };
    }
    p.wit = best;
    p.dead = IDS.filter(s => !st.alive[s]).length;
    p.police = p.dead >= 2;
    // a sack that held money brings the insurance agent to the window, and his knock
    p.survive = !!st.alive[V]; // the usual case now: the victim lives through the night, grey and turned away
    p.agent = !p.survive && st.body[V].includes('coins');
    p.knock = p.police || p.agent;
    p.drowsy = st.body[A].includes('drowsy');
    // what the room still holds of this sack's earlier deeds: the photograph, the cup
    p.props = (st.evidence || []).filter(e => e.k < ev.k && (e.V === V || e.A === V) && (e.kind === 'photograph' || e.kind === 'cup')).map(e => e.kind);
    p.neighbours = (st.evidence || []).some(e => e.kind === 'gun' && e.k < ev.k);
    p.alive = st.alive;
    // tempo lever retimes the doer's whole performance
    const lv = st.levers[A]; p.tf = cl(.8, 1.3, 1 + .35 * (lv.tempo || 0));
    return p;
  }
  const TP = (p, t) => .45 + Math.max(0, t - .45) * p.tf; // doer's local time
  const WALKR = { R: .34, B: .5, I: .62, O: .26 }; // stride period
  function walkX(x0, x1, t0, t1, t) { return lerp(x0, x1, sm(t0, t1, t)); }
  function steps(id, x0, x1, t0, t1, tf) { const out = []; const per = WALKR[id] / tf; for (let s = t0 + per * .5; s < t1; s += per) out.push(s); return out; }

  // doer's pose and props at beat time t
  function doerPose(p, t, st) {
    const A = p.A, V = p.V, u = TP(p, t), lv = st.levers[A];
    const P = { x: p.ax, y: FLOOR, s: 1.25 * (1 + .1 * (lv.loom || 0) - .12 * (lv.shrink || 0)), lean: 0, squash: 0, view: 'front', face: 1, ears: A === 'I' ? 'hang' : 'flat', grey: lv.grey || 0, halo: lv.halo || 0, tags: st.body[A] };
    const wa = lv.weight || 0, bob = x => Math.abs(Math.sin(x)) * (4 + 8 * wa);
    const vW = CAST(V).w * 1.25, aW = CAST(A).w * P.s;
    const besideV = p.vx - vW / 2 - aW / 2 - 50;
    p.sheetU = 0; p.carry = null; p.lampHeld = false; p.walk = [];
    if (p.mode === 'mourn') {
      // pick the folded sheet from the basket, carry it, throw it over, stay
      const t0 = .5, t1 = .85, t2 = 1.45, t3 = 2.05;
      P.x = walkX(p.ax, p.basket + 110, .45, t0 + .02, u);
      P.x = u < t1 ? P.x : walkX(p.basket + 110, besideV, t1, t2, u);
      P.squash = .14 * Math.sin(Math.PI * sm(t0, t1, u)) * (A === 'O' ? .5 : 1); // bends to take it
      P.lean = u < t1 ? -.15 * Math.sin(Math.PI * sm(t0, t1, u)) : .06 * Math.sin(Math.PI * sm(t1, t2, u));
      if (u > t1 && u < t2) P.y -= bob((u - t1) / WALKR[A] * Math.PI);
      P.ears = A === 'I' ? 'hang' : u < t2 ? 'flat' : 'down';
      p.sheetU = sm(t2, t3, u); p.sheetFrom = { x: P.x, y: P.y - dims(A, P).h };
      p.walk = steps(A, p.basket, besideV, t1, t2, 1).map(s => (s - .45) / p.tf + .45);
      // the after-pose, by temperament
      if (u > t3) { const k = sm(t3, t3 + .4, u);
        if (A === 'B') { P.squash = .12 * k; P.lean = .05 * k; P.y += Math.sin((u - t3) * 3) * 3 * k; }
        if (A === 'R') { P.squash = .1 * k; P.lean = .07 * k * Math.sin((u - t3) * 4.5); }
        if (A === 'I') { P.squash = .3 * k; P.lean = .12 * k; }
        if (A === 'O') { P.view = k > .5 ? 'tq' : 'front'; P.face = -1; P.lean = -.04 * k; }
      }
    } else if (p.mode === 'cold') {
      if (A === 'R') { // business: she takes the lamp off the dead sack's stool and keeps it
        const t0 = .55, t1 = 1.55, t2 = 1.85, t3 = 2.8;
        P.view = u < t0 ? 'front' : u < t2 ? 'tq' : u < t3 ? 'tq' : 'front'; P.face = u < t2 ? 1 : -1;
        const near = p.lampX - 120;
        P.x = u < t2 ? walkX(p.ax, near, t0, t1, u) : walkX(near, p.ax + 40, t2, t3, u);
        P.behind = u > t0 + .3 && u < t3 - .2; if (P.behind) { P.y -= 34; P.s *= .93; }
        P.y -= (u > t0 && u < t1) || (u > t2 && u < t3) ? bob(u / WALKR.R * Math.PI) * .6 : 0;
        P.ears = u > t1 && u < t2 ? 'up' : 'flat';
        P.squash = .1 * Math.sin(Math.PI * sm(t1, t2, u));
        p.lampHeld = u > (t1 + t2) / 2; p.lampTop = { x: P.x, y: P.y - dims('R', P).h };
        if (u > t3) { P.lean = .05 * Math.sin((u - t3) * 5); } // rocks, satisfied
        p.walk = steps('R', 0, 0, t0, t1, 1).concat(steps('R', 0, 0, t2, t3, 1)).map(s => (s - .45) / p.tf + .45);
        p.pick = (t1 + t2) / 2;
      } else if (A === 'O') { // vanity: turns to the window, smooths the wig, walks away without a look
        P.view = u < .6 ? 'front' : u < .8 ? 'tq' : 'back'; P.face = -1;
        P.wigSwing = Math.sin(Math.PI * sm(.95, 1.5, u)) * Math.sin(u * 14);
        P.ears = 'up';
        P.x = walkX(p.ax, p.ax - 170, 1.6, 2.7, u); P.y -= u > 1.6 && u < 2.7 ? bob(u / WALKR.O * Math.PI) * .5 : 0;
        P.lean = -.04;
        p.walk = steps('O', 0, 0, 1.6, 2.7, 1).map(s => (s - .45) / p.tf + .45);
      } else if (A === 'I') { // listless, careless: drifts over, pokes the still sack with an ear, sags where it is
        P.x = walkX(p.ax, besideV - 10, .5, 1.6, u); P.y -= u > .5 && u < 1.6 ? bob(u / WALKR.I * Math.PI) * .4 : 0;
        P.ears = u > 1.7 && u < 2.15 ? 'lift' : 'hang'; P.lean = u > 1.7 && u < 2.15 ? .12 : 0;
        P.squash = .28 * sm(2.2, 2.6, u);
        p.poke = [1.75, 1.95];
        p.walk = steps('I', 0, 0, .5, 1.6, 1).map(s => (s - .45) / p.tf + .45);
      } else { // B without guilt: turns his back to it and stands, enormous and still
        P.view = u < .8 ? 'front' : u < 1.0 ? 'tq' : 'back'; P.face = -1; P.ears = 'down'; P.squash = .06 * sm(1, 1.6, u);
      }
    } else if (p.mode === 'already') { // the whisper reached nothing: leans in, starts, backs off, turns away
      P.lean = .16 * Math.sin(Math.PI * sm(.5, 1.3, u)) * (u < 1.3 ? 1 : 0);
      P.ears = u > 1.25 && u < 1.9 ? 'perk' : A === 'I' ? 'hang' : 'flat';
      P.x = p.ax - 90 * sm(1.3, 1.8, u);
      P.view = u > 2.0 ? 'tq' : 'front'; P.face = -1;
      p.walk = [1.4, 1.6];
    } else { // ghost: the doer was already dead; it fades as it rises, casting nothing
      P.alpha = lerp(.65, 0, sm(.6, 2.6, u)); P.y -= 60 * sm(.6, 2.6, u); P.grey = 1; P.ears = 'down';
    }
    // drugged earlier: the doer still staggers through all of it
    if (p.drowsy && p.mode !== 'ghost') { P.lean += .06 * Math.sin(t * 2.6 + 1); P.y += 3 * Math.sin(t * 5.2); }
    // the knock: the doer freezes and turns its ears to the window
    if (p.knock && t > 2.02 && p.mode !== 'ghost') { P.ears = A === 'I' ? 'lift' : 'perk'; if (p.mode === 'cold') { P.view = 'tq'; P.face = 1; } }
    // a witness that suspects: the doer is caught in its candlelight
    if (p.wit && p.wit.kind === 'suspect' && t > 2.35 && p.mode !== 'ghost') { P.ears = p.mode === 'mourn' ? 'down' : (A === 'I' ? 'lift' : 'perk'); }
    return P;
  }
  function victimPose(p, t, st) {
    const V = p.V, lv = st.levers[V];
    const k = p.mode === 'already' ? 1 : sm(.35, 1.0, t);
    const P = { x: p.vx, y: FLOOR, s: 1.25 * (1 - .12 * (lv.shrink || 0)), view: 'back', face: 1, ears: V === 'I' ? 'hang' : 'down', lean: .1 * k + .04, squash: .14 + .14 * k, grey: Math.max(.55, lv.grey || 0) + .2 * k, halo: 0, tags: st.body[V], lit: .85 };
    P.grey = Math.min(1, P.grey);
    if (p.survive) { // alive: grey, turned away, not getting up; it only breathes
      P.grey = Math.min(.8, P.grey); P.squash += .018 * Math.sin(t * 2.1);
      if (p.poke) { const tp = (p.poke[0] - .45) / p.tf + .45, k = Math.exp(-Math.pow((t - tp - .12) / .12, 2)); P.squash -= .06 * k; P.lean += .05 * k; if (k > .3 && V !== 'I') P.ears = 'flat'; }
      if (p.blanket && t > p.blanketAt) { P.squash -= .03 * Math.exp(-Math.pow((t - p.blanketAt - .2) / .2, 2)); }
    }
    return P;
  }
  function witnessPose(p, t, st) {
    if (!p.wit) return null; const o = p.wit.who, lv = st.levers[o];
    const show = sm(1.3, 1.75, t);
    const P = { x: 1735, y: WALLB + 6, s: .7 * (1 + .1 * (lv.loom || 0) - .12 * (lv.shrink || 0)), view: 'front', face: 1, ears: o === 'I' ? 'hang' : 'up', lean: 0, squash: 0, grey: lv.grey || 0, halo: .6, tags: st.body[o], alpha: show, lit: .55 + .5 * show };
    if (t > 1.95) {
      if (p.wit.kind === 'grieve') { const k = sm(1.95, 2.5, t); P.squash = .16 * k; P.ears = o === 'I' ? 'hang' : 'down'; P.lean = .05 * k; }
      else { const k = sm(1.95, 2.35, t); P.view = 'tq'; P.face = -1; P.lean = -.12 * k; P.ears = o === 'I' ? 'lift' : 'perk'; }
    }
    return P;
  }

  // ---------- the beat ----------
  function beat(g, t, ev, st, Kit, X) {
    const L = X && X.ledger, before = L ? L.states[ev.k] : null;
    const p = plan(ev, st, before);
    const dawn = sm(.3, 1.3, t);
    const pal = blendPal(dawn);
    // painted plates, cross-faded (palette swap over identical drawings)
    g.globalAlpha = 1; g.drawImage(plate('night'), 0, 0); g.globalAlpha = dawn; g.drawImage(plate('dawn'), 0, 0); g.globalAlpha = 1;
    // window: outside, neighbours, police lamp, the hat
    windowLife(g, p, t, pal);
    // door leaf: opens for the witness
    door(g, p, t, pal);
    // window light shaft across the room (stronger at dawn)
    g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = rgb(mul(pal.cold, .12), .5 * dawn + .15);
    g.beginPath(); g.moveTo(250, 150); g.lineTo(490, 150); g.lineTo(1150, FLOOR + 60); g.lineTo(560, FLOOR + 60); g.closePath(); g.fill(); g.restore();
    // mantel: four lamps; the victim's goes out now (unless it was already out)
    const outAt = {}; if (p.mode !== 'already' && !p.survive) outAt[p.V] = .5;
    mantel(g, pal, p.alive, outAt, t, p.survive ? p.V : null);
    const D = doerPose(p, t, st); p.blanket = p.mode === 'mourn' && p.survive; p.blanketAt = (2.05 - .45) / p.tf + .45; const Vp = victimPose(p, t, st), Wp = witnessPose(p, t, st);
    // myth lever: the doer's shadow grows on the wall from its before-value to its after-value
    const sb = before ? before.levers[p.A].shadow || 0 : 0, sa = st.levers[p.A].shadow || 0;
    const shd = p.mode === 'ghost' ? 0 : lerp(sb, sa, sm(.8, 2.6, t));
    // witness in the doorway (behind everything on the floor)
    if (Wp && Wp.alpha > .01) { drawSack(g, p.wit.who, Wp, pal); candle(g, p, Wp, t, pal); }
    // floor-level drawing order
    const vb = hbox(p.V, Vp);
    castShadows(g, p.V, Vp, pal, 0, 0);
    if (D.behind) { castShadows(g, p.A, D, pal, shd, .18 + .4 * shd); drawSack(g, p.A, D, pal); if (p.lampHeld) drawLamp(g, p.lampTop.x + 10, p.lampTop.y + 4, .9, pal, .3, t, 3, 0); }
    else castShadows(g, p.A, D, pal, shd, (.18 + .4 * shd) * (D.alpha ?? 1));
    drawStool(g, p.lampX, pal);
    const smoke = p.mode === 'already' ? 0 : 1 - sm(.4, 3, t);
    if (!p.lampHeld) drawLamp(g, p.lampX, FLOOR - 170, 1, pal, smoke, t, 1.3, 0);
    drawSack(g, p.V, Vp, pal);
    props(g, p, pal);
    // the sheet
    if (p.mode === 'already') drawSheet(g, pal, 1, { x: 0, y: 0 }, vb, .7, 0);
    const cover = p.survive ? { x: vb.x + vb.w * .05, y: vb.y + vb.h * .5, w: vb.w * .9, h: vb.h * .5 } : vb; // alive: a blanket over its lower half, the ears left free
    if (p.mode === 'mourn' && p.sheetU > 0) drawSheet(g, pal, p.sheetU, p.sheetFrom, cover, 0, 1);
    drawBasket(g, p.basket, pal, !(p.mode === 'mourn' && TP(p, t) > .62));
    if (p.mode === 'mourn' && TP(p, t) > .62 && p.sheetU <= 0) { const h = dims(p.A, D).h; drawSheet(g, pal, 0, { x: D.x, y: D.y - h + 4 }, vb, 0, 0); }
    if (!D.behind) { drawSack(g, p.A, D, pal); if (p.lampHeld) drawLamp(g, p.lampTop.x + 10, p.lampTop.y + 4, .9, pal, .3, t, 3, 0); }
    // police lamp sweeping the room
    if (p.police) { const u = sm(1.0, 2.9, t), bx = lerp(200, 1500, u), a = Math.sin(Math.PI * u) * .22;
      const gr = g.createRadialGradient(bx, 420, 0, bx, 420, 260); gr.addColorStop(0, `rgba(255,236,190,${a})`); gr.addColorStop(1, 'rgba(255,236,190,0)'); g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = gr; g.fillRect(bx - 260, 160, 520, 520); g.restore(); }
    // grade: painterly vignette, cool at dawn
    const vg = g.createRadialGradient(W / 2, H * .55, H * .3, W / 2, H * .55, H * 1.05); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(3,4,8,${.62 - .2 * dawn})`); g.fillStyle = vg; g.fillRect(0, 0, W, H);
  }
  function blendPal(u) { const a = PAL.night, b = PAL.dawn, o = {}; for (const k in a) o[k] = Array.isArray(a[k]) ? mix(a[k], b[k], u) : lerp(a[k], b[k], u); return o; }
  function windowLife(g, p, t, pal) {
    g.save(); g.beginPath(); g.rect(250, 150, 240, 290); g.clip();
    const shake = p.knock ? [2.0, 2.2, 2.4].reduce((s, k) => s + Math.exp(-Math.pow((t - k) / .03, 2)) * 3, 0) : 0;
    g.translate(shake, 0);
    // the house across the street
    g.fillStyle = rgb(mul(pal.sky, .45)); g.fillRect(250, 300, 240, 140);
    if (p.neighbours) { // neighbours still up since the gun: their windows lit
      [[275, 330], [345, 330], [415, 330], [310, 385], [450, 385]].forEach(([x, y], i) => { const on = hs(i * 7.7) > .25 ? 1 : 0; if (on) { g.fillStyle = `rgba(255,210,130,${.75 - .35 * sm(.5, 2.5, t)})`; g.fillRect(x, y, 26, 30); } });
    }
    if (p.knock) {
      const u = sm(1.0, 2.9, t), lx = lerp(200, 560, u);
      if (p.police) { const gr = g.createRadialGradient(lx, 330, 0, lx, 330, 90); gr.addColorStop(0, 'rgba(255,245,210,.95)'); gr.addColorStop(.25, 'rgba(255,230,170,.5)'); gr.addColorStop(1, 'rgba(255,230,170,0)'); g.fillStyle = gr; g.fillRect(lx - 90, 240, 180, 180); }
      // the insurance agent's hat passing under the sill
      const hx = lerp(640, 330, sm(1.2, 2.0, t)); g.fillStyle = '#07080c'; g.beginPath(); g.ellipse(hx, 440, 120, 60, 0, Math.PI, 0); g.fill(); g.beginPath(); g.ellipse(hx, 372, 72, 14, 0, 0, Math.PI * 2); g.fill(); g.beginPath(); g.ellipse(hx, 352, 44, 40, 0, Math.PI, 0); g.fill(); g.fillRect(hx - 44, 352, 88, 14);
    }
    g.restore();
    // mullions (drawn over, constant line)
    g.strokeStyle = rgb(mul(pal.wall, .5)); g.lineWidth = 12; g.beginPath(); g.moveTo(370 + shake, 150); g.lineTo(370 + shake, 440); g.moveTo(250, 295); g.lineTo(490, 295); g.stroke();
  }
  function door(g, p, t, pal) {
    const open = p.wit ? sm(1.15, 1.6, t) : 0; if (open <= 0) return;
    // dark gap shows a warmer corridor; the leaf swings in (drawn as a narrowing panel)
    g.fillStyle = rgb(mix(mul(pal.wall, .2), hex('#3a2a1c'), .6 * open)); g.fillRect(1664, 314, 142, WALLB - 314);
    const lw = 142 * (1 - open * .82); g.fillStyle = rgb(mul(pal.wall, .42)); g.strokeStyle = rgb(mul(pal.wall, .2)); g.lineWidth = LW;
    g.beginPath(); g.rect(1806 - lw, 314, lw, WALLB - 314); g.fill(); g.stroke();
  }
  function candle(g, p, P, t, pal) {
    const { h } = dims(p.wit.who, P), a = P.alpha ?? 1, side = P.face < 0 ? -1 : 1;
    const x = P.x + side * (dims(p.wit.who, P).w * .5 + 10), y = P.y - h * .55 + (p.wit.kind === 'grieve' ? 14 * sm(1.95, 2.5, t) : 0);
    g.fillStyle = rgb(mul(hex('#ece4d0'), pal.amb), a); g.fillRect(x - 4, y - 26, 8, 26);
    const f = (p.wit.kind === 'grieve' ? 1 - .4 * sm(2, 2.6, t) : 1) * a;
    const gr = g.createRadialGradient(x, y - 34, 0, x, y - 34, 120); gr.addColorStop(0, `rgba(255,205,130,${.45 * f})`); gr.addColorStop(1, 'rgba(255,205,130,0)'); g.fillStyle = gr; g.fillRect(x - 120, y - 154, 240, 240);
    g.fillStyle = `rgba(255,230,160,${f})`; g.beginPath(); g.ellipse(x, y - 33, 4, 9, 0, 0, Math.PI * 2); g.fill();
    if (p.wit.kind === 'suspect') { // the candle's light thrown down across the floor onto the doer
      const k = sm(2.0, 2.4, t) * a, D = doerPose(p, t, ST_CACHE.st), tx = D.x, ty = D.y;
      g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = `rgba(255,190,110,${.2 * k})`;
      g.beginPath(); g.moveTo(x, y - 30); g.lineTo(tx - 190, ty + 20); g.lineTo(tx + 190, ty + 20); g.closePath(); g.fill(); g.restore();
    }
  }
  const ST_CACHE = { st: null };
  function props(g, p, pal) { // the earlier evidence still lying about the dead sack's place
    if (p.props.includes('photograph')) { const x = p.vx - 190, y = FLOOR + 40; g.save(); g.translate(x, y); g.rotate(-.18);
      g.fillStyle = rgb(mul(hex('#e9e2cf'), pal.amb)); g.strokeStyle = rgb(mul(pal.ink, 1)); g.lineWidth = LW * .8; g.fillRect(-38, -26, 76, 52); g.strokeRect(-38, -26, 76, 52);
      g.fillStyle = rgb(mul(hex('#3a3a40'), pal.amb)); g.fillRect(-30, -19, 60, 38); g.fillStyle = rgb(mul(FILL[p.V], pal.amb * .9)); g.fillRect(-10, -6, 20, 22); g.restore(); }
    if (p.props.includes('cup')) { const x = p.lampX + 40, y = FLOOR - 170; g.fillStyle = rgb(mul(hex('#d8d2c4'), pal.amb)); g.strokeStyle = rgb(mul(hex('#d8d2c4'), .3)); g.lineWidth = LW * .8;
      g.beginPath(); g.moveTo(x - 14, y - 26); g.lineTo(x + 14, y - 26); g.lineTo(x + 10, y); g.lineTo(x - 10, y); g.closePath(); g.fill(); g.stroke(); g.beginPath(); g.arc(x + 17, y - 14, 7, -1.4, 1.4); g.stroke(); }
  }

  // ---------- sound: grains only ----------
  function sound(ac, out, t0, ev, st, Kit) {
    const master = ac.createGain(); master.gain.value = 3.2; master.connect(out); out = master; // proof peak ~0.4-0.55
    const SN = Kit.SND, say = SN.say, at = x => t0 + x, pan = x => cl(-1, 1, x / 960 - 1);
    const p = plan(ev, st, null); ST_CACHE.st = st;
    // the house at dawn: a clock grain every half second, a low room hush
    for (let k = 0; k < 7; k++) SN.grain(ac, out, at(.1 + k * .5), { f: 2400, d: .012, a: .05, pan: .6, att: .1 });
    SN.cloud(ac, out, at(0), DUR, 22, { bp: 300, q: .7, a: .014, d: [.2, .5], spread: .8 });
    // the dead sack's mantel flame goes out: a breath of air and a wick tick
    if (p.survive) { // its candle gutters low; the sack breathes, slow and shallow, and does not get up
      SN.cloud(ac, out, at(.4), .7, 40, { bp: 3200, q: 2, a: .025, d: [.02, .06], spread: .1 }, u => 1 - .7 * u);
      for (let k = 0; k < 3; k++) say(ac, out, p.V, at(.3 + k * 1.0), 'breathe', .6, pan(p.vx));
      if (p.mode === 'cold' && p.A === 'I') say(ac, out, p.V, at((1.87 - .45) / p.tf + .45), 'react', .3, pan(p.vx)); // it moves a little
    } else if (p.mode !== 'already') { SN.cloud(ac, out, at(.5), .3, 50, { bp: 1100, q: .9, a: .05, d: [.03, .1], spread: .1 }, u => 1 - u); SN.grain(ac, out, at(.62), { f: 1900, d: .02, a: .07, pan: .7, att: .05 }); }
    else SN.cloud(ac, out, at(.2), 2.5, 18, { f: 110, glide: -.05, a: .02, d: [.3, .6], spread: .2 }); // hollow: nothing left to put out
    const D0 = doerPose(p, 0, st);
    for (const s of (p.walk || [])) { const D = doerPose(p, s, st); say(ac, out, p.A, at(s), 'step', .7 * (1 + .5 * (st.levers[p.A].weight || 0)), pan(D.x)); }
    if (p.mode === 'mourn') {
      const tu = x => (x - .45) / p.tf + .45;
      SN.cloud(ac, out, at(tu(.5)), .35, 40, { bp: 2600, q: .8, a: .03, d: [.04, .12], spread: .2 }, u => Math.sin(Math.PI * u)); // lifts the linen
      SN.cloud(ac, out, at(tu(1.45)), (.6) / p.tf, 70, { bp: 3200, q: .7, a: .05, d: [.05, .14], spread: .5 }, u => Math.sin(Math.PI * u)); // the throw
      SN.thump(ac, out, at(tu(2.05)), .55, 70, pan(p.vx)); // the sheet settles (the beat's strongest)
      SN.cloud(ac, out, at(tu(2.05)), .5, 50, { bp: 900, a: .05, d: [.05, .15], spread: .3 }, u => 1 - u);
      say(ac, out, p.A, at(tu(2.15)), p.A === 'B' ? 'react' : 'sink', .7, pan(p.vx - 200));
      say(ac, out, p.A, at(tu(2.5)), 'breathe', .8, pan(p.vx - 200));
    } else if (p.mode === 'cold') {
      const tu = x => (x - .45) / p.tf + .45;
      if (p.A === 'R') { SN.grain(ac, out, at(tu(p.pick)), { f: 1500, d: .05, a: .16, pan: pan(p.lampX), type: 'triangle', att: .05 }); SN.grain(ac, out, at(tu(p.pick) + .07), { f: 2250, d: .04, a: .09, pan: pan(p.lampX), att: .05 });
        for (let k = 0; k < 3; k++) say(ac, out, 'R', at(tu(2.85) + k * .2), 'tick', .4, pan(p.ax)); }
      if (p.A === 'O') { say(ac, out, 'O', at(tu(.62)), 'tick', .6, pan(p.ax)); say(ac, out, 'O', at(tu(.8)), 'tick', .5, pan(p.ax));
        SN.cloud(ac, out, at(tu(.95)), .55, 50, { bp: 6000, q: 2, a: .03, d: [.02, .06], spread: .2 }, u => Math.sin(Math.PI * u)); // the wig flicked
        SN.thump(ac, out, at(tu(.7)), .3, 120, pan(p.ax)); }
      if (p.A === 'I') { say(ac, out, 'I', at(tu(.5)), 'breathe', 1.1, pan(p.ax)); SN.grain(ac, out, at(tu(1.85)), { bp: 700, q: 1.5, d: .09, a: .09, pan: pan(p.vx), att: .2 }); // the poke, answered by nothing
        say(ac, out, 'I', at(tu(2.25)), 'sink', .8, pan(p.vx - 150)); }
      if (p.A === 'B') say(ac, out, 'B', at(tu(1)), 'sink', 1, pan(p.ax));
    } else if (p.mode === 'already') {
      say(ac, out, p.A, at(1.25), 'react', .6, pan(p.ax));
    } else { // ghost
      SN.cloud(ac, out, at(.6), 2, 30, { f: 330, glide: .3, noise: .4, a: .02, d: [.2, .5], spread: .6 }, u => Math.sin(Math.PI * u));
    }
    if (p.wit) { const o = p.wit.who;
      SN.grain(ac, out, at(1.2), { f: 220, d: .3, a: .05, noise: .6, bp: 400, pan: 0.05 }); // the door
      say(ac, out, o, at(1.6), 'step', .5, .05);
      if (p.wit.kind === 'grieve') say(ac, out, o, at(2.0), 'sink', .9, .05); else { say(ac, out, o, at(2.05), 'react', .5, .05); SN.cloud(ac, out, at(2.1), 1.1, 20, { f: 98, a: .02, d: [.3, .6], spread: .1 }, u => Math.sin(Math.PI * u)); }
    }
    if (p.knock) { for (const k of [2.0, 2.2, 2.4]) SN.thump(ac, out, at(k), .45, 85, -.8); SN.cloud(ac, out, at(1.5), 1.3, 20, { bp: 450, a: .02, d: [.04, .1], spread: .2 }); }
    if (p.neighbours) SN.cloud(ac, out, at(.2), 2.2, 10, { bp: 1500, a: .012, d: [.1, .3], spread: .3 }); // a far murmur
  }

  // ---------- trace: the lamp that stays out, small, aging with the shots ----------
  function trace(g, box, age, Kit) {
    const s = Math.min(box.w / 70, box.h / 120), x = box.x + box.w / 2, y = box.y + box.h, a = Math.max(.25, 1 - age * .08);
    g.save(); g.globalAlpha = a; const pal = blendPal(.5);
    drawLamp(g, x, y, s, pal, Math.max(0, .6 - age * .15), age * 1.3, 2.1, 0);
    // dust on the chimney: a pale film thickening with age
    g.fillStyle = `rgba(200,200,190,${Math.min(.35, age * .04)})`; g.fillRect(x - 14 * s, y - 104 * s, 28 * s, 50 * s);
    g.restore();
  }

  CONSEQ({
    deed: 'incitement', n: 3, scion: 18, lineage: 'Cartoon Saloon — Painterly Puppet Discipline',
    op: 'At dawn the room is the same painted drawing recoloured: the victim lies still and grey with its back to us, its lamp cold, its candle on the mantel goes out; the ledger then decides whether the doer goes back with a sheet, goes cold in its own way, is found out by a third sack in the doorway, or is overtaken by the police lamp and the knock.',
    made: 'A hand-painted patterned interior (spiral wallpaper, boards, window, door, a mantel with four candles whose holders are little casts of the four sacks) cached as two palette plates, night and dawn, cross-faded over the same drawings. The sacks are flat painted shapes with a locked watercolour texture and constant-width ink line, drawn from a turn sheet (front, three-quarter, back) and an ear sheet, with shawl, belt and stencil, wig and carried damage as overlay drawings; the sheet is one cloth drawing with a deformable rig.',
    moved: 'Key drawings are replaced, not interpolated (ear and turn drawings swap on the beat); only lean, squash and the sheet morph are rigged, and the doer\'s timeline is retimed by its tempo lever. Branches come from the ledger: the doer\'s guilt toward the victim, whether the victim or doer was already dead, the third sack\'s grief or suspicion, the count of the dead and earlier gun evidence; the doer\'s wall shadow grows from its before- to after-shadow lever.',
    dur: DUR,
    beat(g, t, ev, st, Kit, X) { ST_CACHE.st = st; beat(g, t, ev, st, Kit, X); },
    sound, trace
  });
})();
