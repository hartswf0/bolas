// 12 · STRANGLING — consequence beat · SCION-MAX-ERNST (id 3): surreal collage grammar.
// Everything is an engraved plate: hatch lines clipped to cut-out silhouettes, pasted over a night
// engraving of the boarding-house stairwell. Seams are emphasised (cut edges, paper shadows).
// Recurring motif in changed function: THE CORD — murder cord -> tow rope -> flour-sack tie (the body
// becomes a hybrid noun, a sack among flour sacks) ... or, when Belindo refuses, -> a serpent.
// Hybrid noun #2: the doer's wall shadow grows the bird head of the PREDATOR (Loplop) as its myth shifts.
(function () {
  const W = 1920, H = 1080, FY = 905, S = 1.8, DUR = 3.2;
  const INK = '#1b1714', PAPER = '#e9dfc8';
  const hs = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const cl = (a, b, x) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  const sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u); };
  const eo = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return 1 - Math.pow(1 - u, 3); };
  const bump = (a, b, x) => Math.sin(Math.PI * cl(0, 1, (x - a) / (b - a)));
  const CORD = '#6b4a2c';

  // ---------- the staircase (fixed geometry, shared by plate, pile and witnesses) ----------
  const ST0 = [1000, FY], ST1 = [40, 170];
  const stairY = x => FY - (ST0[0] - x) * ((ST0[1] - ST1[1]) / (ST0[0] - ST1[0])); // underside top line
  const PILE = [{ x: 140, w: 160, h: 280, s: 1 }, { x: 285, w: 168, h: 300, s: 2 }, { x: 588, w: 150, h: 250, s: 3 }, { x: 712, w: 128, h: 178, s: 4 }];
  const GAPX = 432;

  // ---------- engraving primitives ----------
  function hatch(g, x0, y0, x1, y1, ang, sp, lw, col, alpha, wob) {
    const c = Math.cos(ang), s = Math.sin(ang), cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, R = Math.hypot(x1 - x0, y1 - y0) / 2 + 2;
    g.strokeStyle = col; g.lineWidth = lw; g.globalAlpha = alpha; g.beginPath();
    for (let d = -R, q = 0; d <= R; d += sp, q++) {
      const ox = cx - s * d, oy = cy + c * d, w = wob ? (hs(q * 1.7) - 0.5) * wob : 0;
      g.moveTo(ox - c * R, oy - s * R + w); g.lineTo(ox + c * R, oy + s * R - w);
    }
    g.stroke(); g.globalAlpha = 1;
  }
  function poly(g, pts) { g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath(); }
  function rope(g, pts, w, col) { // engraved rope: dark core + diagonal twist ticks
    g.lineCap = 'round'; g.lineJoin = 'round';
    g.strokeStyle = INK; g.lineWidth = w + 3; g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke();
    g.strokeStyle = col || CORD; g.lineWidth = w; g.stroke();
    g.strokeStyle = 'rgba(20,14,8,.8)'; g.lineWidth = 1.3; g.beginPath();
    let acc = 0;
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i], L = Math.hypot(b[0] - a[0], b[1] - a[1]), nx = -(b[1] - a[1]) / (L || 1), ny = (b[0] - a[0]) / (L || 1);
      for (let d = (7 - acc % 7); d < L; d += 7) { const u = d / L, x = lerp(a[0], b[0], u), y = lerp(a[1], b[1], u); g.moveTo(x - nx * w * .5 - 2, y - ny * w * .5 - 2); g.lineTo(x + nx * w * .5 + 2, y + ny * w * .5 + 2); }
      acc += L;
    }
    g.stroke();
  }
  function curve(a, c, b, n) { const o = []; for (let i = 0; i <= n; i++) { const u = i / n; o.push([(1 - u) * (1 - u) * a[0] + 2 * u * (1 - u) * c[0] + u * u * b[0], (1 - u) * (1 - u) * a[1] + 2 * u * (1 - u) * c[1] + u * u * b[1]]); } return o; }

  // ---------- the sack as an engraved cut-out (built bottom up from a profile function) ----------
  const DIM = { R: [168, 122], B: [244, 214], I: [128, 98], O: [80, 184], F: [1, 1] };
  function sack(id, o) { // o: x, fy, sc, lean, cinch, slump, sq, w,h override
    const [w0, h0] = id === 'F' ? [o.w, o.h] : DIM[id];
    const sc = (id === 'F' ? 1 : S) * (o.sc || 1), sq = o.sq || 0;
    const w = w0 * sc * (1 + sq * 0.6), h = h0 * sc * (1 - sq) * (1 - (o.slump || 0) * 0.18);
    const cinch = o.cinch || 0, lean = o.lean || 0, neckV = id === 'R' ? 0.8 : id === 'O' ? 0.82 : 0.8;
    const hw = v => w / 2 * (0.84 + 0.16 * Math.sin(Math.PI * Math.min(1, v * 1.05 + 0.08))) * (1 - cinch * 0.5 * Math.exp(-(((v - neckV) / 0.055) ** 2))) * (v > neckV ? 1 - 0.12 * (v - neckV) / (1 - neckV) * (1 + cinch) : 1) * (1 + (o.slump || 0) * 0.12 * (1 - v));
    const X = v => o.x + lean * h * Math.pow(v, 1.6) + (o.droop || 0) * h * Math.max(0, v - 0.75) * 2;
    const Y = v => o.fy - v * h;
    const pts = [], N = 18;
    for (let i = 0; i <= N; i++) { const v = i / N; pts.push([X(v) + hw(v), Y(v)]); }
    // gathered top: shallow dip
    for (let i = 1; i < 6; i++) { const u = i / 6; pts.push([lerp(X(1) + hw(1), X(1) - hw(1), u), Y(1) + Math.sin(Math.PI * u) * h * 0.035 * (1 - cinch * 0.5)]); }
    for (let i = N; i >= 0; i--) { const v = i / N; pts.push([X(v) - hw(v), Y(v)]); }
    return { id, pts, X, Y, hw, w, h, o, neckV, top: [X(1), Y(1)], cx: X(0.5), box: { x: X(0) - w / 2, y: Y(1), w, h } };
  }
  // sack ears (two top corners) as hatched flaps: up = 1 pricked, 0 level, -1 hanging
  function ears(g, s, up, len, tint) {
    for (const side of [-1, 1]) {
      const bx = s.X(1) + side * s.hw(1) * 0.98, by = s.Y(1), a = side > 0 ? lerp(Math.PI / 2, -Math.PI * 0.4, (up + 1) / 2) : lerp(Math.PI / 2, Math.PI * 1.4, (up + 1) / 2);
      const L = len * s.h, tx = bx + Math.cos(a) * L * (side > 0 ? 1 : 1), ty = by + Math.sin(a) * L;
      const ix = s.X(1) + side * s.hw(1) * 0.55, iy = by + s.h * 0.02;
      if (up < -0.5) { const hang = -(up + 0.5) * 2; const tx2 = bx + side * s.w * 0.18 * hang + side * 6, ty2 = by + L; const P2 = [[bx - side * 4, by], [tx2, ty2], [bx + side * (10 + s.w * 0.1), ty2 - 14], [bx + side * 14, by + 10]];
        g.fillStyle = tint; poly(g, P2); g.fill(); g.save(); poly(g, P2); g.clip(); hatch(g, Math.min(bx, tx2) - 40, by - 4, Math.max(bx, tx2) + 40, ty2 + 4, 0.25 * side, 4, 1, INK, 0.7); g.restore(); g.strokeStyle = INK; g.lineWidth = 2.6; poly(g, P2); g.stroke(); continue; }
      const P = [[bx, by + 2], [tx, ty], [ix, iy]];
      g.fillStyle = tint; poly(g, P); g.fill();
      g.save(); poly(g, P); g.clip(); hatch(g, Math.min(bx, tx, ix) - 4, Math.min(by, ty, iy) - 4, Math.max(bx, tx, ix) + 4, Math.max(by, ty, iy) + 4, 0.9 * side, 4.5, 1, INK, 0.7); g.restore();
      g.strokeStyle = INK; g.lineWidth = 2.6; poly(g, P); g.stroke();
    }
  }
  function mixHex(a, b, u) { const p = x => [1, 3, 5].map(i => parseInt(x.slice(i, i + 2), 16)); const A = p(a), B = p(b); return 'rgb(' + A.map((v, i) => Math.round(lerp(v, B[i], u))).join(',') + ')'; }
  const TINT = { R: '#d9c49c', B: '#e6d3ab', I: '#e0cba2', O: '#efe2c6', F: '#ddd0b2' };
  // draw an engraved sack; m = {grey, lampX, ear, tags, ghost, alpha}
  function drawSack(g, s, m) {
    const id = s.id, grey = cl(0, 1, m.grey || 0);
    const tint = mixHex(TINT[id], '#9d9890', grey * 0.8);
    g.save(); if (m.alpha != null) g.globalAlpha = m.alpha;
    if (m.ghost) { // excised: a hole cut out of the engraving, only its cut line remains
      g.fillStyle = '#f6f1e4'; poly(g, s.pts); g.fill();
      g.setLineDash([9, 7]); g.strokeStyle = 'rgba(30,24,20,.65)'; g.lineWidth = 2; poly(g, s.pts); g.stroke(); g.setLineDash([]);
      g.restore(); return;
    }
    // ears behind body for I (hanging, long), in front for others after
    g.fillStyle = tint; poly(g, s.pts); g.fill();
    g.save(); poly(g, s.pts); g.clip();
    const { x, y, w, h } = s.box, bx0 = x - 60, bx1 = x + w + 60;
    // cross-contour lines (bulging across the cloth)
    g.strokeStyle = INK; g.globalAlpha = 0.55 + grey * 0.2; g.lineWidth = 1.15; g.beginPath();
    const sp = 6.2 - grey * 1.2;
    for (let yy = y + 3; yy < y + h; yy += sp) { const v = (s.o.fy - yy) / h, cx = s.X(v), hw = s.hw(v); g.moveTo(cx - hw - 4, yy); g.quadraticCurveTo(cx, yy + 7 + hw * 0.06, cx + hw + 4, yy); }
    g.stroke(); g.globalAlpha = 1;
    // shadow side away from the lamp: diagonal hatch
    const away = (m.lampX ?? 1100) > s.cx ? -1 : 1;
    g.save(); g.beginPath(); g.rect(away > 0 ? s.cx + w * 0.12 : bx0, y - 20, away > 0 ? bx1 - s.cx : s.cx - w * 0.12 - bx0, h + 40); g.clip();
    hatch(g, bx0, y - 20, bx1, y + h + 20, away > 0 ? 1.0 : 2.1, 5, 1.2, INK, 0.6); g.restore();
    // floor shade
    g.save(); g.beginPath(); g.rect(bx0, s.o.fy - h * 0.14, bx1 - bx0, h); g.clip(); hatch(g, bx0, s.o.fy - h * 0.2, bx1, s.o.fy + 10, 0.45, 4, 1.1, INK, 0.6); g.restore();
    if (grey > 0.05) { g.globalAlpha = grey * 0.5; hatch(g, bx0, y, bx1, y + h, 1.57, 3.5, 1, '#2a2a2e', 1); g.globalAlpha = 1; }
    // attributes (hand-tinted, as in coloured plates)
    if (id === 'R') { const v0 = m.shawlUp ? 0.8 - 0.35 * m.shawlUp : 0.8, ya = s.Y(v0) + 6, yb = y - 12;
      g.fillStyle = mixHex('#6e3a33', '#5a5450', grey * 0.6); g.fillRect(bx0, yb, bx1 - bx0, ya - yb); hatch(g, bx0, yb, bx1, ya, 0.6, 3.4, 1.2, '#2b120e', 0.8);
      g.strokeStyle = '#2b120e'; g.lineWidth = 1.4; g.beginPath(); for (let xx = bx0; xx < bx1; xx += 7) { g.moveTo(xx, ya); g.lineTo(xx + 2, ya + 9); } g.stroke(); }
    if (id === 'B') { const yb = s.Y(0.4); g.fillStyle = '#2a2622'; g.fillRect(bx0, yb - h * 0.04, bx1 - bx0, h * 0.075); g.strokeStyle = 'rgba(230,220,200,.45)'; g.lineWidth = 1; g.beginPath(); g.moveTo(bx0, yb - h * 0.025); g.lineTo(bx1, yb - h * 0.025); g.stroke();
      const cx = s.X(0.64), cy = s.Y(0.64), r = h * 0.13; g.strokeStyle = 'rgba(60,40,20,.85)'; g.lineWidth = 3; g.beginPath(); g.arc(cx, cy, r, 0, 7); g.stroke();
      g.lineWidth = 2.2; g.beginPath(); g.moveTo(cx, cy + r * 0.8); g.lineTo(cx, cy - r * 0.75); g.stroke();
      for (let q = 0; q < 4; q++) for (const sd of [-1, 1]) { g.beginPath(); g.ellipse(cx + sd * r * 0.2, cy - r * 0.55 + q * r * 0.3, r * 0.12, r * 0.24, sd * 0.5, 0, 7); g.stroke(); } }
    if (id === 'F' && s.o.ring) { const cx = s.X(0.45), cy = s.Y(0.45), r = s.w * 0.24; g.strokeStyle = 'rgba(70,50,30,.6)'; g.lineWidth = 2.5; g.beginPath(); g.arc(cx, cy, r, 0, 7); g.stroke(); g.beginPath(); for (let q = -1; q <= 1; q++) { g.moveTo(cx - r * 0.6, cy + q * r * 0.35); g.lineTo(cx + r * 0.6, cy + q * r * 0.35); } g.stroke(); }
    g.restore();
    g.strokeStyle = INK; g.lineWidth = 3; poly(g, s.pts); g.stroke();
    // bottom seam stitches
    g.lineWidth = 1.4; g.beginPath(); for (let xx = s.X(0) - s.hw(0) + 10; xx < s.X(0) + s.hw(0) - 8; xx += 11) { g.moveTo(xx, s.o.fy - 9); g.lineTo(xx + 5, s.o.fy - 5); } g.stroke();
    if (id === 'I') ears(g, s, Math.min(-0.6, m.ear ?? -1), 0.7, tint);
    else if (id !== 'F') ears(g, s, m.ear ?? 0.4, id === 'B' ? 0.08 : id === 'O' ? 0.06 : 0.13, tint);
    if (id === 'O') wig(g, s, m);
    if (m.tags) tagMarks(g, s, m.tags);
    g.restore();
  }
  function wig(g, s, m) { // purple engraved hair mass over the crown, hanging past the shoulders
    const top = s.Y(1) - 14, hw = s.hw(1) * 1.35, cx = s.X(1) + (m.wigOff || 0), cy = top, len = s.h * 0.5, rot = m.wigRot || 0;
    g.save(); g.translate(cx, cy); g.rotate(rot); g.translate(-cx, -cy);
    const col = mixHex('#7a3b8f', '#6a6470', cl(0, 1, m.grey || 0) * 0.6);
    const P = [[cx - hw * 0.95, cy + 16]];
    for (let i = 0; i <= 10; i++) { const a = Math.PI + Math.PI * i / 10; P.push([cx + Math.cos(a) * hw, cy + 14 + Math.sin(a) * 30]); }
    P.push([cx + hw * 1.05, cy + len]); P.push([cx + hw * 0.55, cy + len * 0.92]); P.push([cx + hw * 0.5, cy + 30]); P.push([cx - hw * 0.5, cy + 30]); P.push([cx - hw * 0.55, cy + len * 0.95]); P.push([cx - hw * 1.05, cy + len]);
    g.fillStyle = col; poly(g, P); g.fill();
    g.save(); poly(g, P); g.clip(); g.strokeStyle = '#2a0f33'; g.lineWidth = 1.2; g.globalAlpha = 0.8; g.beginPath();
    for (let q = -10; q <= 10; q++) { const x0 = cx + q * hw / 10; g.moveTo(x0, cy - 20); g.bezierCurveTo(x0 + 6, cy + len * 0.3, x0 - 6, cy + len * 0.6, x0 + q * 1.2, cy + len + 4); }
    g.stroke(); g.restore();
    g.strokeStyle = INK; g.lineWidth = 2.4; poly(g, P); g.stroke(); g.restore();
  }
  // carried damage drawn as engraved marks
  function tagMarks(g, s, tags) {
    const has = t => tags.indexOf(t) >= 0;
    g.save();
    if (has('rope')) for (const v of [0.3, 0.58]) rope(g, curve([s.X(v) - s.hw(v), s.Y(v)], [s.X(v), s.Y(v) + 10], [s.X(v) + s.hw(v), s.Y(v)], 8), 5, '#7a6244');
    if (has('gag')) { const v = 0.9; g.fillStyle = '#efe9da'; g.strokeStyle = INK; g.lineWidth = 2; g.fillRect(s.X(v) - s.hw(v), s.Y(v) - 9, s.hw(v) * 2, 18); g.strokeRect(s.X(v) - s.hw(v), s.Y(v) - 9, s.hw(v) * 2, 18); }
    if (has('blot')) { const cx = s.X(0.5) - s.hw(0.5) * 0.25, cy = s.Y(0.5); g.fillStyle = 'rgba(16,14,30,.88)'; g.beginPath(); for (let q = 0; q < 16; q++) { const a = q / 16 * 6.283, r = 15 + 10 * hs(q * 3.1); q ? g.lineTo(cx + r * Math.cos(a), cy + r * Math.sin(a)) : g.moveTo(cx + r * Math.cos(a), cy + r * Math.sin(a)); } g.closePath(); g.fill(); }
    if (has('tag')) { const cx = s.X(0.62) + s.hw(0.62) * 0.3, cy = s.Y(0.62); g.fillStyle = '#f3ecd6'; g.strokeStyle = INK; g.lineWidth = 2; g.save(); g.translate(cx, cy); g.rotate(0.2); g.fillRect(-20, 0, 40, 28); g.strokeRect(-20, 0, 40, 28); g.beginPath(); g.moveTo(-14, 10); g.lineTo(14, 10); g.moveTo(-14, 18); g.lineTo(8, 18); g.stroke(); g.restore(); }
    if (has('torn')) { const xs = s.X(0.5) + s.hw(0.5) * 0.85; g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); for (let q = 0; q <= 8; q++) { const v = 0.28 + q * 0.04; g.lineTo(s.X(v) + s.hw(v) * (q % 2 ? 0.78 : 0.9), s.Y(v)); } g.stroke();
      g.lineWidth = 1.5; g.beginPath(); for (let q = 0; q < 8; q++) { const v = 0.29 + q * 0.04, xx = s.X(v) + s.hw(v) * 0.84; g.moveTo(xx - 7, s.Y(v) - 3); g.lineTo(xx + 7, s.Y(v) + 3); } g.stroke(); }
    if (has('coins')) for (let q = 0; q < 3; q++) { const cx = s.X(0) + s.hw(0) + 18, cy = s.o.fy - 4 - q * 6; g.fillStyle = '#c8a64a'; g.strokeStyle = INK; g.lineWidth = 1.5; g.beginPath(); g.ellipse(cx, cy, 13, 5, 0, 0, 7); g.fill(); g.stroke(); }
    if (has('emptied')) { g.strokeStyle = 'rgba(250,246,236,.8)'; g.setLineDash([2, 6]); g.lineWidth = 3; g.beginPath(); g.moveTo(s.X(0) - s.hw(0) * 0.8, s.o.fy + 6); g.lineTo(s.X(0) + s.hw(0) * 1.3, s.o.fy + 8); g.stroke(); g.setLineDash([]); }
    if (has('cinched')) { const v = s.neckV; rope(g, curve([s.X(v) - s.hw(v) - 3, s.Y(v)], [s.X(v), s.Y(v) + 7], [s.X(v) + s.hw(v) + 3, s.Y(v)], 6), 4, CORD); }
    g.restore();
  }

  // ---------- the plate: night stairwell engraving (cached; a pure function of nothing) ----------
  let PLATE = null;
  function plate() {
    if (PLATE) return PLATE;
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H; const g = cv.getContext('2d');
    g.fillStyle = PAPER; g.fillRect(0, 0, W, H);
    const LX = 1100, LY = 270, dark = (x, y) => cl(0.12, 1, Math.hypot(x - LX, (y - LY) * 1.3) / 1050);
    // wall: vertical engraved lines whose weight grows away from the lamp
    g.strokeStyle = INK;
    for (let x = 2; x < W; x += 5.5) for (let y = 0; y < FY; y += 36) { g.lineWidth = 0.35 + 2.7 * dark(x, y + 18); g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + 37); g.stroke(); }
    // wallpaper ornament rows (small engraved lozenges)
    g.lineWidth = 1.2; g.strokeStyle = 'rgba(27,23,20,.55)';
    for (let y = 70; y < 620; y += 110) for (let x = 40 + (y % 220 ? 55 : 0); x < W; x += 110) { g.beginPath(); g.moveTo(x, y - 12); g.lineTo(x + 8, y); g.lineTo(x, y + 12); g.lineTo(x - 8, y); g.closePath(); g.stroke(); }
    // dado rail + wainscot panels
    g.fillStyle = 'rgba(30,24,20,.35)'; g.fillRect(0, 640, W, 10); g.strokeStyle = INK; g.lineWidth = 2; g.beginPath(); g.moveTo(0, 640); g.lineTo(W, 640); g.moveTo(0, 652); g.lineTo(W, 652); g.stroke();
    for (let x = 30; x < W; x += 240) { g.strokeRect(x, 680, 200, 190); g.save(); g.beginPath(); g.rect(x, 680, 200, 190); g.clip(); hatch(g, x, 680, x + 200, 870, 0.78, 6, 0.9 + dark(x, 780) * 1.6, INK, 0.7); g.restore(); }
    // floor: boards in perspective
    g.fillStyle = '#d9cdb2'; g.fillRect(0, FY, W, H - FY);
    for (let y = FY + 4, k = 0; y < H; y += 6 + k * 1.3, k++) { g.lineWidth = 0.6 + dark(960, y) * 2; g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
    g.lineWidth = 1.6; g.beginPath(); for (let q = -14; q <= 14; q++) { g.moveTo(960 + q * 70, FY); g.lineTo(960 + q * 260, H); } g.stroke();
    g.lineWidth = 3; g.beginPath(); g.moveTo(0, FY); g.lineTo(W, FY); g.stroke();
    // under-stair cavity: dense cross-hatch (the dark where things are hidden)
    const cav = [[ST1[0], ST1[1] + 40], [ST0[0], ST0[1]], [ST1[0], FY]];
    g.save(); poly(g, [[0, ST1[1] + 40], [ST1[0], ST1[1] + 40], [ST0[0] - 30, FY], [0, FY]]); g.clip();
    g.fillStyle = '#7b7062'; g.fillRect(0, 0, ST0[0], FY); hatch(g, 0, 150, ST0[0], FY, 0.5, 4, 1.4, INK, 0.9); hatch(g, 0, 150, ST0[0], FY, -0.7, 5, 1.2, INK, 0.8); hatch(g, 0, 150, ST0[0], FY, 1.57, 7, 1, INK, 0.5);
    g.restore();
    // stringer band and steps
    const sx = x => [x, stairY(x)];
    g.fillStyle = '#bfb39a'; poly(g, [[ST1[0], ST1[1]], [ST0[0], ST0[1] - 2], [ST0[0] - 30, ST0[1]], [ST1[0], ST1[1] + 40]]); g.fill();
    g.save(); poly(g, [[ST1[0], ST1[1]], [ST0[0], ST0[1] - 2], [ST0[0] - 30, ST0[1]], [ST1[0], ST1[1] + 40]]); g.clip(); hatch(g, 0, 100, ST0[0], FY, -0.65, 4, 1, INK, 0.8); g.restore();
    g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); g.moveTo(ST1[0], ST1[1] + 40); g.lineTo(ST0[0] - 30, ST0[1]); g.stroke();
    // treads: zigzag above the stringer
    const n = 13, dx = (ST0[0] - ST1[0]) / n;
    const zz = [[ST0[0], FY]];
    for (let i = 0; i < n; i++) { const x = ST0[0] - i * dx, y = stairY(x); zz.push([x, y - 52]); zz.push([x - dx, y - 52]); }
    g.fillStyle = '#cfc3a8'; poly(g, [...zz, [ST1[0], ST1[1]], [ST0[0], FY]]); g.fill();
    for (let i = 0; i < n; i++) { const x = ST0[0] - i * dx, y = stairY(x); g.save(); g.beginPath(); g.rect(x - dx, y - 52, dx, 52 + (y - stairY(x - dx))); g.clip(); hatch(g, x - dx, y - 60, x, y + 60, 1.57, 4, 1 + 0.6 * dark(x, y), INK, 0.75); g.restore(); }
    g.lineWidth = 2.6; g.beginPath(); zz.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke();
    // balusters + handrail
    g.lineWidth = 2.2; g.beginPath(); for (let i = 0; i < n; i++) { const x = ST0[0] - i * dx - dx * 0.5, y = stairY(x + dx * 0.5) - 52; g.moveTo(x, y); g.lineTo(x, y - 170); } g.stroke();
    g.lineWidth = 7; g.beginPath(); g.moveTo(ST0[0] + 10, FY - 52 - 175); g.lineTo(ST1[0] - 20, ST1[1] - 52 - 175 + 10); g.stroke(); g.strokeStyle = '#8f8270'; g.lineWidth = 2; g.stroke(); g.strokeStyle = INK;
    g.fillStyle = '#3a312a'; g.fillRect(ST0[0] - 4, FY - 260, 18, 260); hatch(g, ST0[0] - 4, FY - 260, ST0[0] + 14, FY, 1.57, 3, 1, '#000', .6); g.strokeRect(ST0[0] - 4, FY - 260, 18, 260);
    // flour sacks hidden under the stairs, each tied with cord
    // the door (right) with keyhole
    g.fillStyle = '#5c5146'; g.fillRect(1610, 300, 240, FY - 300);
    g.save(); g.beginPath(); g.rect(1610, 300, 240, FY - 300); g.clip(); hatch(g, 1610, 300, 1850, FY, 1.57, 3.2, 1.3, INK, 0.9); g.restore();
    g.lineWidth = 4; g.strokeRect(1610, 300, 240, FY - 300); g.lineWidth = 2; g.strokeRect(1640, 340, 180, 220); g.strokeRect(1640, 600, 180, 270);
    g.lineWidth = 10; g.strokeStyle = '#2a231d'; g.strokeRect(1598, 290, 264, FY - 285); g.strokeStyle = INK;
    g.fillStyle = '#b89a4a'; g.beginPath(); g.arc(1648, 610, 9, 0, 7); g.fill(); g.stroke();
    // window with the neighbours' house beyond
    g.fillStyle = '#2c2a33'; g.fillRect(1260, 170, 250, 330); g.save(); g.beginPath(); g.rect(1260, 170, 250, 330); g.clip(); hatch(g, 1260, 170, 1510, 500, 0.2, 3, 1, '#000', .8);
    g.fillStyle = '#4a4650'; g.fillRect(1270, 330, 120, 170); g.fillRect(1400, 290, 110, 210); for (const [wx, wy] of WINS) { g.fillStyle = '#26232b'; g.fillRect(wx, wy, 22, 30); g.strokeStyle = '#111'; g.strokeRect(wx, wy, 22, 30); } g.restore();
    g.strokeStyle = '#3b332c'; g.lineWidth = 14; g.strokeRect(1253, 163, 264, 344); g.lineWidth = 6; g.beginPath(); g.moveTo(1385, 170); g.lineTo(1385, 500); g.moveTo(1260, 335); g.lineTo(1510, 335); g.stroke(); g.strokeStyle = INK;
    // ceiling lamp
    g.lineWidth = 2; g.beginPath(); g.moveTo(LX, 0); g.lineTo(LX, 200); g.stroke();
    g.fillStyle = '#bfa66a'; poly(g, [[LX - 60, 250], [LX - 30, 205], [LX + 30, 205], [LX + 60, 250]]); g.fill(); g.lineWidth = 2.5; g.stroke();
    g.save(); poly(g, [[LX - 60, 250], [LX - 30, 205], [LX + 30, 205], [LX + 60, 250]]); g.clip(); hatch(g, LX - 60, 200, LX + 60, 252, 1.57, 5, 1, INK, .6); g.restore();
    g.fillStyle = '#fff3cf'; g.beginPath(); g.ellipse(LX, 262, 22, 16, 0, 0, 7); g.fill(); g.stroke();
    const gr = g.createRadialGradient(LX, LY + 30, 10, LX, LY + 160, 900); gr.addColorStop(0, 'rgba(255,240,200,.35)'); gr.addColorStop(1, 'rgba(255,240,200,0)'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const vg = g.createRadialGradient(LX, LY + 200, 250, LX, LY + 200, 1250); vg.addColorStop(0, 'rgba(12,10,8,0)'); vg.addColorStop(0.45, 'rgba(14,10,18,.25)'); vg.addColorStop(1, 'rgba(14,10,18,.72)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'multiply'; const mg = g.createRadialGradient(LX, LY + 120, 120, LX, LY + 200, 1300); mg.addColorStop(0, '#ffffff'); mg.addColorStop(0.5, '#a49aa8'); mg.addColorStop(1, '#4e4660'); g.fillStyle = mg; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over';
    PLATE = cv; return cv;
  }
  let PILECV = null;
  function pileLayer() { // the flour sacks under the stairs, each tied with cord (a separate cut-out sheet, pasted above the shadows)
    if (PILECV) return PILECV;
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H; const g = cv.getContext('2d');
    for (const p of PILE) { const s = sack('F', { x: p.x, fy: FY, w: p.w, h: p.h, cinch: 0.75, ring: true }); drawSack(g, s, { lampX: 1100, grey: 0.55 }); flourTie(g, s, 1); }
    g.globalCompositeOperation = 'source-atop'; g.fillStyle = 'rgba(28,22,38,.42)'; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over';
    PILECV = cv; return cv;
  }
  const WINS = [[1285, 360], [1330, 360], [1285, 420], [1330, 420], [1420, 320], [1465, 320], [1420, 390], [1465, 390]];
  function flourTie(g, s, u) { // the cord tie and bow on a gathered top: the disguise
    if (u <= 0) return; const v = s.neckV, x = s.X(v), y = s.Y(v), hw = s.hw(v);
    rope(g, curve([x - hw - 2, y], [x, y + 6], [x + hw + 2, y], 5), 4, CORD);
    g.save(); g.globalAlpha = cl(0, 1, u);
    rope(g, curve([x + 2, y + 2], [x + 30, y - 22], [x + 34, y + 8], 6), 3.5, CORD); rope(g, curve([x + 2, y + 2], [x - 26, y - 20], [x - 30, y + 8], 6), 3.5, CORD);
    rope(g, [[x + 4, y + 4], [x + 14, y + 40]], 3, CORD); rope(g, [[x, y + 4], [x - 8, y + 44]], 3, CORD); g.restore();
  }

  // ---------- reading the ledger ----------
  function readState(ev, st, X) {
    const A = ev.A, V = ev.V, evd = st.evidence[ev.k] || {};
    const imp = (st.impossible || []).find(q => q.k === ev.k);
    let mode = 'hide';
    if (imp) mode = 'ghost'; else if (evd.refused) mode = 'refuse';
    const ghostWho = imp ? imp.who : null;
    const dead = ['R', 'B', 'I', 'O'].filter(s => !st.alive[s]).length;
    // witnesses: a living third sack that snooped on a participant looks through the keyhole; one who knows the doer's earlier deeds appears at the stair head
    let keyhole = null, stairW = null;
    const sn = st.evidence[10];
    if (sn && sn.A !== A && sn.A !== V && st.alive[sn.A] && (sn.V === A || sn.V === V)) keyhole = sn.A;
    const L = X && X.ledger;
    for (const o of ['R', 'B', 'I', 'O']) {
      if (o === A || o === V || o === keyhole || !st.alive[o]) continue;
      const knowsDoer = (st.know[o] || []).some(i => L && L.ev[i] && L.ev[i].A === A && i !== ev.k);
      const m = st.mind[o] && st.mind[o][A] || {};
      if (knowsDoer || (m.fear || 0) + (m.grudge || 0) > 0.5) { stairW = o; break; }
    }
    const mA = (st.mind[A] && st.mind[A][V]) || {};
    const lv = st.levers || {};
    return { mode, ghostWho, dead, keyhole, stairW, guilt: mA.guilt || 0, pride: mA.pride || 0, lvA: lv[A] || {}, lvV: lv[V] || {}, bodyA: st.body[A] || [], bodyV: st.body[V] || [] };
  }
  const SC = {};
  function starts(ev, K) { // continuity with the deed shot's end positions (cached: a pure function of the pair)
    const key = ev.A + ev.V; if (SC[key]) return SC[key];
    let xa = 560, xv = 1330;
    try { const D = window.DEEDS && DEEDS.strangling; if (D && D.marks) { const m = D.marks(6, ev.A, ev.V, K); xa = m.A.x + m.A.w / 2; xv = m.V.x + m.V.w / 2; } } catch (e) {}
    return (SC[key] = { xa: cl(260, 820, xa), xv: cl(1080, 1460, xv) });
  }

  // ---------- poses per branch: one function shared by picture and sound ----------
  function pose(t, ev, R, K) {
    const A = ev.A, V = ev.V, { xa, xv } = starts(ev, K), lA = R.lvA, lV = R.lvV;
    const loomA = cl(-0.3, 1, lA.loom || 0), shrinkA = cl(0, 1, lA.shrink || 0);
    const P = { A: { x: xa, sc: 1 + loomA * 0.06 - shrinkA * 0.1, lean: 0, sq: 0, ear: 0.4, cinch: 0, slump: 0 },
      V: { x: xv, sc: 1, lean: 0, sq: 0, ear: 0.2, cinch: 0, slump: 0 }, cord: null, tie: 0, trail: 0, snake: 0, halo: 0, inset: 0, shadowGrow: 0, tally: 0, mirror: 0, step: [] };
    if (A === 'I') P.A.ear = -1;
    if (V === 'I') P.V.ear = -1;
    if (R.mode === 'hide') {
      const pull = sm(0.55, 1.55, t);
      P.V.cinch = 1; P.V.slump = 0.55; P.V.ear = V === 'I' ? -1 : -0.6; P.V.x = lerp(xv, GAPX, pull); P.V.lean = -0.18 * bump(0.5, 1.6, t) + 0.03 * (1 - pull);
      const toL = eo(0.5, 1.45, t), back = sm(1.45, 2.05, t);
      const big = A === 'B', xL = big ? 330 : 250; P.A.x = lerp(lerp(xa, xL, toL), big ? 1080 : 980, back);
      P.A.lean = -0.12 * bump(0.45, 1.5, t) + 0.06 * bump(1.45, 2.05, t);
      P.A.sq = 0.05 * Math.abs(Math.sin((t - 0.5) * 10)) * bump(0.5, 1.5, t);
      P.trail = pull; P.tie = sm(1.55, 1.95, t); P.inset = bump(1.5, 2.55, t);
      P.cord = t < 1.6 ? 'tow' : 'tie';
      P.shadowGrow = sm(1.9, 3.0, t);
      // reckoning, by temperament
      const r = sm(2.0, 2.4, t), tt = t - 2.0;
      if (A === 'B') { P.A.x = lerp(P.A.x, 900, sm(2.1, 2.9, t) * (0.5 + 0.5 * R.guilt)); P.A.lean = lerp(P.A.lean, -0.1, r); P.A.sq = 0.1 * r; P.A.ear = lerp(0.4, -0.8, r); }
      if (A === 'R') { P.A.lean = lerp(P.A.lean, 0.05 * Math.sin(tt * 9), r); P.A.ear = lerp(0.4, 0.9, r); P.tally = cl(0, 5, (t - 2.15) / 0.2); }
      if (A === 'O') { P.A.x = lerp(P.A.x, 880, r); P.mirror = sm(1.9, 2.3, t); P.A.lean = lerp(P.A.lean, 0.04, r); P.A.wigRot = 0.08 * Math.sin(tt * 6) * r; P.A.ear = 0.8; }
      if (A === 'I') { P.A.sq = lerp(P.A.sq, 0.22, r); P.A.lean = lerp(P.A.lean, -0.05, r); P.A.ear = -1 + 0.22 * r * (0.5 + 0.5 * Math.sin(tt * 5)); P.A.droop = 0.12 * r; }
      P.step = [0.62, 0.86, 1.1, 1.34, 1.62, 1.86];
    } else if (R.mode === 'refuse') {
      const rec = eo(0.25, 1.1, t), fl = bump(1.75, 2.3, t);
      const xa2 = Math.max(700, xa - 170);
      P.A.x = lerp(xa, xa2, rec) - 60 * sm(1.75, 2.0, t);
      P.A.sc *= 1 - 0.14 * rec - 0.06 * shrinkA; P.A.sq = 0.12 * rec + 0.12 * fl; P.A.ear = lerp(0.4, -0.9, rec);
      P.A.lean = -0.08 * rec + (K.hash(Math.floor(t * 24) + 3) - 0.5) * 0.05 * rec;
      P.A.shawlUp = A === 'R' ? sm(0.7, 1.4, t) : 0; P.A.wigRot = A === 'O' ? -0.35 * sm(0.4, 1.0, t) : 0; P.A.wigOff = A === 'O' ? -14 * sm(0.4, 1.0, t) : 0;
      if (A === 'I') { P.A.sq = 0.3 * rec; P.A.droop = -0.1 * rec; }
      P.V.x = xv - 110 * eo(1.6, 2.0, t); P.V.ear = lerp(0.2, 0.9, sm(0.4, 1.0, t)) - 0.8 * sm(2.3, 3.0, t);
      P.V.sc = 1 + 0.04 * sm(0.4, 1.4, t) + 0.03 * cl(0, 1, lV.loom || 0); P.V.lean = -0.05 * bump(1.6, 2.4, t);
      P.halo = sm(0.35, 1.3, t); P.snake = sm(0.3, 1.6, t); P.shadowGrow = sm(0.4, 2.2, t);
      P.step = [1.92];
    } else { // ghost: one of them was already dead; a held tableau, one intrusion (the cord moves alone)
      P.V.cinch = R.ghostWho === V ? 0 : sm(0.2, 1.2, t); P.V.slump = R.ghostWho === V ? 0 : 0.5 * sm(0.4, 1.4, t);
      if (R.ghostWho === V) { P.A.x = xa - 50 * eo(0.9, 1.8, t); P.A.sq = 0.1 * bump(0.9, 1.8, t); P.A.ear = lerp(0.4, 1, sm(0.8, 1.2, t)); }
      P.cord = 'alone'; P.shadowGrow = sm(0.5, 2.5, t);
    }
    return P;
  }

  function shapes(t, ev, R, P) {
    const sa = sack(ev.A, { x: P.A.x, fy: FY, sc: P.A.sc, lean: P.A.lean, sq: P.A.sq, cinch: (R.bodyA.indexOf('cinched') >= 0 ? 0.45 : 0), slump: R.bodyA.indexOf('emptied') >= 0 ? 0.4 : 0, droop: P.A.droop });
    const sv = sack(ev.V, { x: P.V.x, fy: FY, sc: P.V.sc, lean: P.V.lean, sq: P.V.sq, cinch: P.V.cinch, slump: P.V.slump + (R.bodyV.indexOf('emptied') >= 0 ? 0.3 : 0) });
    return { sa, sv };
  }

  // the doer's wall shadow: grows with the shadow lever; past a threshold the PREDATOR's bird head crowns it
  function wallShadow(g, s, grow, lv, lampX, fear) {
    const sh = cl(0, 1.2, lv.shadow || 0), dir = s.cx < lampX ? -1 : 1;
    const k = (1.12 + 0.55 * sh * grow) * (1 - 0.3 * (fear || 0));
    const off = dir * (40 + 70 * sh * grow);
    const P = s.pts.map(([x, y]) => [lampX + (x - lampX) * (1 + (k - 1) * 0.6) + off, FY - (FY - y) * k]);
    g.save(); g.globalAlpha = 0.32 + 0.3 * cl(0, 1, sh * grow); poly(g, P); g.clip();
    const bx = s.box.x - 400, by = FY - s.h * k * 1.2 - 40;
    hatch(g, bx, by, bx + s.w + 800, FY, 0.8, 3.2, 1.5, '#0d0b0a', 1); hatch(g, bx, by, bx + s.w + 800, FY, -0.8, 3.8, 1.3, '#0d0b0a', 1);
    g.restore();
    const top = P.reduce((a, b) => b[1] < a[1] ? b : a, P[0]);
    const ox = P.reduce((a, b) => a + b[0], 0) / P.length, hgt = FY - top[1];
    const bird = cl(0, 1, (sh - 0.25) / 0.5) * grow;
    if (bird > 0.02) { // Loplop: a bird-head silhouette grows out of the shadow's crown, beak toward the hidden body
      const hx = ox, hy = top[1] - 30 * bird, r = 58 * k * bird + 6, bd = -dir;
      const B = [];
      for (let i = 0; i <= 14; i++) { const a = Math.PI * 0.95 + i / 14 * Math.PI * 1.1; B.push([hx + Math.cos(a) * r * bd * -1, hy + Math.sin(a) * r]); }
      B.push([hx + bd * r * 2.4, hy + r * 0.25]); B.push([hx + bd * r * 0.7, hy + r * 0.9]); B.push([hx - bd * r * 0.4, hy + r * 1.6]);
      g.save(); g.globalAlpha = 0.75 * bird; poly(g, B); g.clip(); hatch(g, hx - r * 3, hy - r * 2, hx + r * 3, hy + r * 2, 0.8, 3, 1.6, '#0d0b0a', 1); hatch(g, hx - r * 3, hy - r * 2, hx + r * 3, hy + r * 2, -0.8, 3.6, 1.4, '#0d0b0a', 1); g.restore();
      g.save(); g.globalAlpha = 0.9 * bird; g.fillStyle = '#e9dfc8'; g.beginPath(); g.arc(hx + bd * r * 0.35, hy - r * 0.2, Math.max(2, r * 0.13), 0, 7); g.fill(); g.restore();
    }
  }
  function haloRays(g, s, u, lv) { // a sunburst engraving cut in a circle and pasted behind Belindo
    if (u <= 0) return; const cx = s.cx, cy = s.Y(0.55), r = (s.h * 0.68 + 30) * (0.4 + 0.6 * u) * (1 + 0.15 * cl(0, 1, lv.halo || 0));
    g.save(); g.globalAlpha = cl(0, 1, u * 1.2);
    g.fillStyle = '#f4ead0'; g.beginPath(); g.arc(cx, cy, r, 0, 7); g.fill();
    g.save(); g.beginPath(); g.arc(cx, cy, r, 0, 7); g.clip(); g.strokeStyle = INK; g.lineWidth = 1.4;
    g.beginPath(); for (let q = 0; q < 96; q++) { const a = q / 96 * 6.283; const r0 = r * 0.25; const r1 = r * (q % 2 ? 0.92 : 1.2); g.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); g.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1); } g.stroke();
    g.restore();
    g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); for (let q = 0; q <= 60; q++) { const a = q / 60 * 6.283, rr = r + (hs(q * 4.1) - 0.5) * 5; q ? g.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr) : g.moveTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr); } g.closePath(); g.stroke();
    g.restore();
  }
  function serpent(g, x0, x1, u, t) { // the dropped cord coils, lifts a head and slides toward the doer
    const n = 30, head = lerp(x0, x1, u), len = 340, pts = [];
    for (let i = 0; i <= n; i++) { const q = i / n, x = head + q * len, y = FY + 16 - 16 * Math.sin(q * 9 - t * 9) * (0.3 + 0.7 * u) * (1 - q * 0.5); pts.push([x, y]); }
    const lift = 70 * sm(0.15, 0.6, u); pts.unshift([head - 14, FY + 10 - lift * 0.6]); pts.unshift([head - 22, FY + 4 - lift]);
    rope(g, pts, 9, CORD);
    // head: a knot shaped like a serpent's head
    const hx = head - 24, hy = FY + 2 - lift; g.fillStyle = CORD; g.strokeStyle = INK; g.lineWidth = 2.4;
    g.beginPath(); g.ellipse(hx, hy, 26, 14, -0.25, 0, 7); g.fill(); g.stroke(); g.fillStyle = '#efe6cf'; g.beginPath(); g.arc(hx - 8, hy - 4, 3, 0, 7); g.fill();
    if (lift > 10) { g.lineWidth = 1.5; g.beginPath(); g.moveTo(hx - 25, hy); g.lineTo(hx - 42, hy - 3); g.lineTo(hx - 50, hy - 10); g.moveTo(hx - 42, hy - 3); g.lineTo(hx - 50, hy + 4); g.stroke(); }
  }

  // ---------- the beat ----------
  function beat(g, t, ev, st, K, X) {
    const R = readState(ev, st, X), P = pose(t, ev, R, K), { sa, sv } = shapes(t, ev, R, P);
    const A = ev.A, V = ev.V, LX = 1100;
    g.drawImage(plate(), 0, 0);
    // outside: one lit neighbour window per dead sack in the house
    for (let q = 0; q < Math.min(WINS.length, R.dead * 2); q++) { const on = sm(0.6 + q * 0.35, 0.8 + q * 0.35, t); if (on <= 0) continue; const [wx, wy] = WINS[(q * 3) % WINS.length]; g.fillStyle = `rgba(255,214,120,${0.9 * on})`; g.fillRect(wx + 2, wy + 2, 18, 26); }
    // witness at the head of the stairs: appears, sees, turns away
    if (R.stairW) {
      const u = sm(1.6, 2.0, t), away = sm(2.6, 3.1, t);
      if (u > 0 && away < 1) { const wx = 250 - 120 * away, sw = sack(R.stairW, { x: wx, fy: stairY(wx) - 50, sc: 0.55, lean: -0.12 * away }); drawSack(g, sw, { lampX: LX, alpha: u * (1 - away), ear: R.stairW === 'I' ? -1 : 1 - 2 * away, grey: 0.2 }); }
    }
    // keyhole witness: the snooper's colour behind the keyhole
    if (R.keyhole) {
      const u = sm(1.2, 1.6, t); const KC = { R: '#6e3a33', B: '#2a2622', I: '#e2cea5', O: '#7a3b8f' }[R.keyhole];
      g.save(); g.fillStyle = '#f2d98a'; g.beginPath(); g.arc(1648, 640, 9 + 5 * u, 0, 7); g.moveTo(1640, 642); g.lineTo(1656, 642); g.lineTo(1652 + 4 * u, 676 + 10 * u); g.lineTo(1644 - 4 * u, 676 + 10 * u); g.fill();
      g.globalAlpha = u; g.fillStyle = KC; g.beginPath(); g.arc(1648, 646, 8 + 4 * u, 0, 7); g.fill(); g.restore();
      // a thin wedge of light from the door crack
      g.save(); g.globalAlpha = 0.35 * u; g.fillStyle = '#ffe9b0'; poly(g, [[1610, 320], [1616, 320], [1400, FY + 175], [1250, FY + 175]]); g.fill(); g.restore();
    }
    // the insurance agent's hat at the door once the house has lost two
    if (R.dead >= 2) { const u = sm(2.3, 2.8, t); if (u > 0) { g.save(); g.fillStyle = '#efe3c2'; g.fillRect(1850 - 22 * u, 300, 22 * u, FY - 300);
      g.translate(1858 - 30 * u, 520); g.fillStyle = '#16120f'; g.beginPath(); g.ellipse(0, 0, 46, 10, 0, 0, 7); g.fill(); g.beginPath(); g.ellipse(0, -26, 28, 30, 0, Math.PI, 0); g.lineTo(28, -6); g.lineTo(-28, -6); g.fill(); g.restore(); } }
    // flour trail from where the body lay to the stairs
    if (P.trail > 0) { g.fillStyle = 'rgba(251,247,238,.85)'; const xs = starts(ev, K).xv, xe = sv.cx; for (let q = 0; q < 70; q++) { const x = lerp(xs, xe, q / 70); if ((x - xe) * (xs - xe) < 0) continue; g.beginPath(); g.arc(x + (hs(q) - 0.5) * 20, FY + 14 + (hs(q * 2.3) - 0.5) * 18, 1.5 + 2 * hs(q * 7), 0, 7); g.fill(); } }
    // shadows on the wall
    wallShadow(g, sv, R.mode === 'refuse' ? P.shadowGrow : 0, R.lvV, LX, 0);
    wallShadow(g, sa, P.shadowGrow, R.mode === 'refuse' ? { shadow: 0 } : R.lvA, LX, R.mode === 'refuse' ? sm(0.3, 1.2, t) : 0);
    // the mirror (Ogiva's reckoning): an oval engraving pasted on the wall, her reflection preening
    g.drawImage(pileLayer(), 0, 0);
    if (P.mirror > 0) { const mx = 1130, my = 520; g.save(); g.globalAlpha = P.mirror; g.fillStyle = '#c9c4b8'; g.beginPath(); g.ellipse(mx, my, 92, 128, 0, 0, 7); g.fill(); g.save(); g.clip(); hatch(g, mx - 100, my - 130, mx + 100, my + 130, 0.4, 7, 0.8, INK, 0.4);
      const rs = sack('O', { x: mx, fy: my + 120, sc: 0.62, lean: -P.A.lean }); drawSack(g, rs, { lampX: LX, wigRot: -(P.A.wigRot || 0) }); g.restore();
      g.strokeStyle = '#6b5a2a'; g.lineWidth = 10; g.beginPath(); g.ellipse(mx, my, 92, 128, 0, 0, 7); g.stroke(); g.strokeStyle = INK; g.lineWidth = 2; g.stroke(); g.restore(); }
    if (P.halo > 0) haloRays(g, sv, P.halo, R.lvV);
    // victim, then cord, then doer (doer in front)
    const vTags = R.mode === 'hide' ? R.bodyV.filter(x => x !== 'cinched') : R.bodyV.filter(x => !(V === 'B' && x === 'cinched'));
    const ghostV = R.mode === 'ghost' && R.ghostWho === V, ghostA = R.mode === 'ghost' && R.ghostWho === A;
    drawSack(g, sv, { lampX: LX, grey: (R.mode === 'hide' ? 0.45 * sm(0, 1.5, t) + 0.25 : 0) + (R.lvV.grey || 0) * 0.5, ear: P.V.ear, tags: vTags, ghost: ghostV });
    if (R.mode === 'hide') {
      const v = sv.neckV, nx = sv.X(v), ny = sv.Y(v), hw = sv.hw(v);
      rope(g, curve([nx - hw - 3, ny], [nx, ny + 7], [nx + hw + 3, ny], 6), 4.5, CORD);
      // attribute peeking from the disguise (only those who look closely)
      if (P.tie > 0) flourTie(g, sv, P.tie);
      if (P.cord === 'tow') { const ex = sa.X(1) + sa.hw(1) * 0.9, ey = sa.Y(1) + 10; const taut = sm(0.45, 0.65, t) * (1 - sm(1.45, 1.6, t)); rope(g, curve([nx - hw - 3, ny], [(nx + ex) / 2, Math.min(FY, Math.max(ny, ey) + 90 * (1 - taut))], [ex, ey], 14), 4.5, CORD); }
    }
    if (R.mode === 'refuse') serpent(g, sv.box.x - 280, sa.cx + sa.w * 0.5 + 30, P.snake * 0.8, t);
    if (R.mode === 'ghost') { // the cord lies across, tightening around nothing / held by nothing
      const v = sv.neckV, nx = sv.X(v), ny = sv.Y(v), hw = sv.hw(v);
      if (ghostV) { const fall = sm(0.6, 1.4, t); rope(g, curve([nx - hw - 10, lerp(ny, FY + 10, fall)], [nx, lerp(ny + 14, FY + 18, fall)], [nx + hw + 10, lerp(ny, FY + 10, fall)], 8), 4.5, CORD); rope(g, curve([nx - hw - 10, lerp(ny, FY + 10, fall)], [lerp(nx - 300, sa.cx + 120, 0.5), FY - 40 + 40 * fall], [sa.cx + sa.w * 0.4, lerp(sa.Y(0.9), FY + 8, fall)], 12), 4, CORD); }
      else { rope(g, curve([nx - hw - 3, ny], [nx, ny + 7], [nx + hw + 3, ny], 6), 4.5, CORD); const sway = Math.sin(t * 2.2) * 30; rope(g, curve([nx - hw - 3, ny], [(nx + sa.cx) / 2 + sway, ny - 60], [sa.X(1) + sa.hw(1), sa.Y(1)], 12), 4, CORD); }
    }
    drawSack(g, sa, { lampX: LX, grey: (R.lvA.grey || 0) * 0.6 + (R.mode === 'refuse' ? 0.15 * sm(0.5, 1.5, t) : 0), ear: P.A.ear, tags: R.bodyA, ghost: ghostA, shawlUp: P.A.shawlUp, wigRot: P.A.wigRot, wigOff: P.A.wigOff });
    // Roessler counts the sacks: an engraved tally stroke over each, one by one
    if (P.tally > 0) { g.strokeStyle = INK; g.lineWidth = 4; g.lineCap = 'round'; const xs = [PILE[0].x, PILE[1].x, GAPX, PILE[2].x, PILE[3].x]; for (let q = 0; q < Math.floor(P.tally); q++) { const x = xs[q], y = stairY(x) + 70; g.beginPath(); g.moveTo(x - 6, y + 18); g.lineTo(x + 6, y - 18); g.stroke(); } }
    // Inigo's careless loop: a spare end of cord twirled
    if (R.mode === 'hide' && A === 'I' && t > 2.1) { const ph = (t - 2.1) * 11, ex = sa.X(1) + sa.hw(1), ey = sa.Y(1) - 10; g.save(); g.translate(ex + 30, ey - 20); rope(g, curve([-40, 30], [0, -10], [0, 0], 6), 3, CORD); g.strokeStyle = CORD; g.lineWidth = 4; g.beginPath(); g.ellipse(Math.cos(ph) * 14, -20 + Math.sin(ph) * 5, 22, 8 + 5 * Math.abs(Math.sin(ph)), 0, 0, 7); g.stroke(); g.restore(); }
    // the inset: a magnified fragment of the hiding place, pasted as a separate plate (the hybrid noun close up)
    if (P.inset > 0.01) inset(g, P.inset, sv, () => { drawSack(g, sv, { lampX: LX, grey: 0.45 * sm(0, 1.5, t) + 0.25 + (R.lvV.grey || 0) * 0.5, ear: P.V.ear, tags: vTags }); const v = sv.neckV, nx = sv.X(v), ny = sv.Y(v), hw = sv.hw(v); rope(g, curve([nx - hw - 3, ny], [nx, ny + 7], [nx + hw + 3, ny], 6), 4.5, CORD); flourTie(g, sv, P.tie); });
    // the opening paste: the deed's own last frame is cut away along a ragged seam
    const seam = eo(0, 0.42, t);
    if (seam < 1 && X && X.still) {
      let cv = null; try { cv = X.still(ev, 5.95); } catch (e) {}
      if (cv) { const sx = seam * (W + 60) - 30; g.save(); g.beginPath(); g.moveTo(sx, 0); for (let q = 0; q <= 18; q++) g.lineTo(sx + (hs(q * 5.3) - 0.5) * 26, q * 60); g.lineTo(W, H); g.lineTo(W, 0); g.closePath(); g.save(); g.clip(); g.drawImage(cv, 0, 0); g.restore();
        g.strokeStyle = 'rgba(0,0,0,.45)'; g.lineWidth = 10; g.stroke(); g.strokeStyle = '#f3ead6'; g.lineWidth = 3; g.stroke(); g.restore(); }
    }
  }
  function inset(g, u, sv, drawV) { // re-engraves the hiding place at 1.5x on a separate pasted plate
    const sw = 470, sh = 260, sx = cl(0, W - sw, sv.cx - sw / 2), sy = cl(0, FY + 60 - sh, sv.Y(sv.neckV) - 120), dx = 1150, dy = 130 - 20 * u, dw = 700, dh = 387;
    g.save(); g.globalAlpha = cl(0, 1, u * 2); g.translate(dx + dw / 2, dy + dh / 2); g.rotate(0.035 - 0.02 * u); g.translate(-dw / 2, -dh / 2);
    g.fillStyle = 'rgba(0,0,0,.4)'; g.fillRect(12, 14, dw, dh);
    g.fillStyle = PAPER; g.fillRect(-10, -10, dw + 20, dh + 20);
    g.save(); g.beginPath(); g.rect(0, 0, dw, dh); g.clip();
    g.drawImage(plate(), sx, sy, sw, sh, 0, 0, dw, dh); g.drawImage(pileLayer(), sx, sy, sw, sh, 0, 0, dw, dh);
    g.scale(dw / sw, dh / sh); g.translate(-sx, -sy); drawV(); g.restore();
    g.strokeStyle = INK; g.lineWidth = 3; g.strokeRect(0, 0, dw, dh); g.lineWidth = 1; g.strokeRect(-6, -6, dw + 12, dh + 12);
    g.restore();
  }

  // ---------- sound: grains (the burin's scratch, paper pasted, cord, cloth) ----------
  function sound(ac, out0, t0, ev, st, K) {
    const out = ac.createGain(); out.gain.value = 3.4; out.connect(out0);
    const SND = K.SND, R = readState(ev, st, null), A = ev.A, V = ev.V;
    const pan = x => cl(-1, 1, x / 960 - 1), at = s => t0 + s;
    const P = s => pose(s, ev, R, K);
    // the seam cut: a burin scratch running left to right, then the paper laid down
    SND.cloud(ac, out, at(0), 0.42, 60, { bp: 5200, q: 2, a: 0.03, d: [0.01, 0.03], spread: 0.9 }, u => 1 - u * 0.5);
    SND.grain(ac, out, at(0.43), { bp: 900, q: 0.7, d: 0.07, a: 0.14, pan: 0.6 });
    if (R.mode === 'hide') {
      SND.grain(ac, out, at(0.55), { f: 160, type: 'sawtooth', noise: 0.6, bp: 500, q: 3, d: 0.1, a: 0.12, pan: pan(P(0.55).A.x) }); // the cord tightens as tow rope
      SND.cloud(ac, out, at(0.6), 0.95, 55, { bp: 700, q: 1.2, a: 0.05, d: [0.03, 0.08], spread: 0.3 }, u => Math.sin(Math.PI * u)); // the body scrapes the boards
      for (const s of P(0).step) SND.say(ac, out, A, at(s), 'step', 0.8, pan(P(s).A.x));
      SND.say(ac, out, V, at(1.55), 'land', 0.6, pan(GAPX)); // it settles among the sacks
      for (let q = 0; q < 5; q++) SND.grain(ac, out, at(1.6 + q * 0.07), { f: 300 + 40 * q, type: 'sawtooth', noise: 0.6, bp: 1100, q: 4, d: 0.03, a: 0.07, pan: pan(GAPX) }); // the knot pulled
      SND.grain(ac, out, at(1.52), { bp: 1500, q: 0.6, d: 0.05, a: 0.12, pan: 0.4 }); SND.grain(ac, out, at(2.53), { bp: 1800, q: 0.6, d: 0.05, a: 0.08, pan: 0.4 }); // inset pasted / lifted
      const xr = pan(P(2.6).A.x);
      if (A === 'R') for (let q = 0; q < 5; q++) SND.say(ac, out, 'R', at(2.15 + q * 0.2), 'tick', 0.9, pan([PILE[0].x, PILE[1].x, GAPX, PILE[2].x, PILE[3].x][q]));
      if (A === 'B') { SND.say(ac, out, 'B', at(2.2), 'sink', 0.8, xr); SND.say(ac, out, 'B', at(2.5), 'step', 0.5, xr); }
      if (A === 'O') { SND.pluck(ac, out, at(2.0), 93, 0.08, 0.4, 0.1); for (let q = 0; q < 3; q++) SND.say(ac, out, 'O', at(2.4 + q * 0.18), 'tick', 0.6, xr); }
      if (A === 'I') { SND.say(ac, out, 'I', at(2.1), 'breathe', 0.9, xr); SND.cloud(ac, out, at(2.2), 0.9, 30, { bp: 1500, q: 3, a: 0.025, d: [0.02, 0.05], spread: 0.2 }, u => 0.5 + 0.5 * Math.sin(u * 6.283 * 4)); }
      if (R.stairW) SND.say(ac, out, R.stairW, at(2.65), 'step', 0.4, -0.85);
      if (R.dead >= 2) { SND.grain(ac, out, at(2.35), { bp: 300, q: 2, d: 0.06, a: 0.16, pan: 0.85 }); SND.grain(ac, out, at(2.55), { bp: 300, q: 2, d: 0.06, a: 0.16, pan: 0.85 }); } // a knock
    } else if (R.mode === 'refuse') {
      SND.cloud(ac, out, at(0.3), 1.3, 40, { bp: 1200, q: 2, a: 0.035, d: [0.03, 0.08], spread: 0.4 }, u => Math.sin(Math.PI * u)); // the serpent slides
      SND.say(ac, out, A, at(0.3), 'react', 0.8, pan(P(0.3).A.x));
      SND.cloud(ac, out, at(0.4), 1.0, 45, { pitches: [57, 64, 69, 76], a: 0.018, d: [0.08, 0.2], spread: 0.3 }, u => Math.sin(Math.PI * u)); // the rays engrave themselves
      SND.say(ac, out, 'B', at(1.92), 'step', 1, pan(P(1.92).V.x));
      SND.say(ac, out, A, at(2.0), 'land', 0.5, pan(P(2.0).A.x)); // the doer cowers
      SND.say(ac, out, 'B', at(2.4), 'breathe', 0.8, pan(P(2.4).V.x));
      if (A === 'O') SND.say(ac, out, 'O', at(0.7), 'tick', 0.7, pan(P(0.7).A.x)); // the wig slips
    } else {
      SND.cloud(ac, out, at(0.4), 2.0, 22, { bp: 600, q: 2, a: 0.06, d: [0.05, 0.12], spread: 0.3 }, u => 1 - u); // the cord, moving by itself
      SND.say(ac, out, R.ghostWho === A ? V : A, at(1.0), R.ghostWho === A ? 'sink' : 'react', 0.7, 0);
      SND.grain(ac, out, at(1.4), { bp: 500, q: 1, d: 0.1, a: 0.2, pan: 0.3 }); SND.thump(ac, out, at(1.4), 0.5, 70, 0.3);
    }
  }

  // ---------- trace: a small engraved coil of cord with a knot, fading with age ----------
  function trace(g, box, age, K) {
    const a = cl(0.2, 1, 1 - age * 0.09), cx = box.x + box.w / 2, cy = box.y + box.h / 2, r = Math.min(box.w, box.h) * 0.32;
    g.save(); g.globalAlpha = a; const pts = []; for (let i = 0; i <= 40; i++) { const u = i / 40, ang = u * Math.PI * 4.2, rr = r * (0.35 + 0.65 * u); pts.push([cx + Math.cos(ang) * rr, cy + Math.sin(ang) * rr * 0.55]); }
    pts.push([cx + r * 1.4, cy + r * 0.3]); rope(g, pts, Math.max(2, r * 0.12), CORD);
    g.fillStyle = INK; g.beginPath(); g.arc(cx + r * 1.4, cy + r * 0.3, Math.max(2, r * 0.12), 0, 7); g.fill(); g.restore();
  }

  CONSEQ({
    deed: 'strangling', n: 12, scion: 3, lineage: 'Max Ernst — Surreal Collage Grammar',
    op: 'Cut the strangled sack out of the deed\'s last frame and paste it into an engraving of the stairwell, where the same cord that killed it becomes the tie that makes it one more flour sack; if Belindo refused, the dropped cord becomes a serpent and a sunburst plate is pasted behind him.',
    made: 'Every surface is an engraved plate drawn in code: parallel and cross-contour hatch lines clipped to cut-out silhouettes, hand-tinted only on the shawl, belt, wheat stencil and wig. The world is a night stairwell engraving with tied flour sacks under the stairs, a door with a keyhole, a window onto the neighbours, and plates (an inset close-up, a mirror, a sunburst, a bird head) pasted on with visible seams.',
    moved: 'The ledger state picks the branch (hidden body, Belindo\'s refusal, or a contradiction with a dead participant) and the levers set scale, ear angle, grey and the length of each wall shadow; shadow past a threshold grows the PREDATOR\'s bird head. One pose function of t drives the cut-outs (tow, tie, reckoning by temperament) and the grain sounds at the same instants.',
    dur: DUR,
    beat, sound, trace,
  });
})();
