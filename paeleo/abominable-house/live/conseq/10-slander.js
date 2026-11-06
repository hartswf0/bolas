// 10 · SLANDER — CONSEQUENCE · SCION-SOUTH-PARK (Repeatable Graphic Grammar)
// One stage template (the STREET: the boarding house front with four colour-coded doors, two neighbour houses, snow),
// one cutout shape kit (body, two ear triangles, attribute card, damage stickers), a facing-state set (F, L, R, BACK),
// an ear atlas (UP, NEU, DRP, FLAT) used in place of mouths, and a 12-card/s clock: every change is a slide or a swap.
(function () {
const S = 1.65, FY = 960, HB = 850, FPS = 12, DUR = 3.2;
const IDS = ['R', 'B', 'I', 'O'];
const DOORX = { R: 330, B: 730, I: 1130, O: 1530 };          // each sack owns one door: recurring asset, never moves
const DOORC = { R: '#6e3a33', B: '#2a2622', I: '#b9a888', O: '#7a3b8f' };
const INK = '#111015', SNOW = '#eef2f6';
const H = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const cl = (a, b, x) => Math.max(a, Math.min(b, x));
const sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u); };
const lin = (a, b, x) => cl(0, 1, (x - a) / (b - a));
const mixc = (c1, c2, u) => { const p = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)); const a = p(c1), b = p(c2);
  return '#' + a.map((v, i) => Math.round(v + (b[i] - v) * u).toString(16).padStart(2, '0')).join(''); };

// ---------- cutout shape kit: polygons with fixed scissor wobble (same jitter every frame: the asset is one asset) ----------
function cut(g, pts, fill, seed, line = 3, wob = 2.2) {
  g.beginPath();
  pts.forEach((p, i) => { const x = p[0] + (H(seed * 31 + i * 7.3) - .5) * wob * 2, y = p[1] + (H(seed * 17 + i * 3.1) - .5) * wob * 2; i ? g.lineTo(x, y) : g.moveTo(x, y); });
  g.closePath(); if (fill) { g.fillStyle = fill; g.fill(); } if (line) { g.lineWidth = line; g.strokeStyle = INK; g.lineJoin = 'round'; g.stroke(); }
}
function blob(g, x, y, r, seed, fill = INK, n = 11) {
  const pts = []; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, rr = r * (.7 + .5 * H(seed + i * 1.7)); pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); }
  cut(g, pts, fill, seed, 0, 0);
}
function disc(g, x, y, r, fill, line = 0) { g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fillStyle = fill; g.fill(); if (line) { g.lineWidth = line; g.strokeStyle = INK; g.stroke(); } }

// ---------- ear atlas (the sacks' mouths): direction vectors per state ----------
const EAR = { UP: [.35, -1], NEU: [1, -.55], DRP: [.25, 1], FLAT: [1, .15] };

// ---------- one sack, assembled from the kit ----------
// o: {x, y, sc, face:'F'|'L'|'R'|'B', ear, grey, alpha, tags, dead, lean, squash}
function sack(g, id, o) {
  const C = { R: [168, 122], B: [244, 214], I: [128, 98], O: [80, 184] }[id];
  let w = C[0] * S * o.sc, h = C[1] * S * o.sc;
  const tags = o.tags || [];
  if (tags.includes('emptied')) h *= .8;
  const sq = o.squash || 0; w *= 1 + sq * .12; h *= 1 - sq * .12;
  const seed = { R: 11, B: 23, I: 37, O: 41 }[id];
  const greyU = cl(0, 1, (o.grey || 0) + (tags.includes('greyed') ? .4 : 0));
  const base = mixc({ R: '#d6bf96', B: '#e8d5ae', I: '#e2cea5', O: '#f0e4c8' }[id], '#8d8f94', greyU * .85);
  const back = mixc(base, '#6d6458', .22);
  const face = o.face;
  g.save(); g.globalAlpha *= (o.alpha ?? 1);
  if (o.dead) { g.translate(o.x, o.y); w *= 1.2; h *= .42; }   // a still sack: slumped flat on the snow, ears flat
  else { g.translate(o.x, o.y); g.rotate((o.lean || 0) + (tags.includes('drowsy') ? .07 : 0)); }
  const side = face === 'L' ? -1 : face === 'R' ? 1 : 0;
  const bw = side ? w * .8 : w;
  const sag = id === 'I' ? h * .14 : id === 'B' ? -h * .03 : 0;
  // ears (drawn first, under the body edge)
  let es = o.ear || 'NEU'; if (id === 'I' && es === 'NEU') es = 'DRP';
  const elen = (id === 'I' ? (es === 'DRP' ? h * .75 : h * .42) : id === 'R' ? h * .2 : id === 'O' ? h * .12 : h * .2) * (es === 'DRP' && id !== 'I' ? 1.3 : 1);
  const earAt = (sx, dark) => { const d = EAR[es], cx = sx * bw / 2, cy = -h + (sx ? 0 : 0); const L = Math.hypot(d[0], d[1]);
    const tx = cx + sx * d[0] / L * elen, ty = cy + d[1] / L * elen, b = Math.min(bw, h) * .2;
    if (es === 'DRP') cut(g, [[cx - sx * b * 1.1, cy - 2], [cx + sx * 10, cy + 4], [cx + sx * (10 + elen * .12), cy + elen], [cx + sx * (elen * .06 - 4), cy + elen * .92]], dark ? back : base, seed + (sx > 0 ? 5 : 9), 3, 1.5);
    else cut(g, [[cx - sx * b, cy + 2], [tx, ty], [cx, cy + b]], dark ? back : base, seed + (sx > 0 ? 5 : 9), 3, 1.5); };
  if (side) { earAt(-side, true); } else { earAt(-1, face === 'B'); earAt(1, face === 'B'); }
  // body
  const pts = [[-bw / 2, -h], [-bw * .2, -h + sag], [bw * .2, -h + sag], [bw / 2, -h], [bw / 2 + (side > 0 ? 6 : 0), -h * .5], [bw / 2, -h * .14], [bw * .4, 0], [-bw * .4, 0], [-bw / 2, -h * .14], [-bw / 2 - (side < 0 ? 6 : 0), -h * .5]];
  if (tags.includes('cinched')) { pts.splice(4, 0, [bw * .36, -h * .84]); pts.splice(11, 0, [-bw * .36, -h * .84]); }
  cut(g, pts, face === 'B' ? back : base, seed, 3.2);
  g.save(); g.beginPath(); pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.closePath(); g.clip();
  // attribute cards
  if (id === 'R') { cut(g, [[-bw, -h * 1.1], [bw, -h * 1.1], [bw, -h * .79], [-bw, -h * .79]], mixc('#6e3a33', '#5a5458', greyU * .6), 51, 2, 1);
    for (let i = 0; i < 9; i++) { const fx = -bw / 2 + (i + .5) * bw / 9; cut(g, [[fx - 7, -h * .8], [fx + 7, -h * .8], [fx, -h * .7]], mixc('#6e3a33', '#5a5458', greyU * .6), 60 + i, 0, .5); } }
  if (id === 'B') { cut(g, [[-bw, -h * .44], [bw, -h * .44], [bw, -h * .36], [-bw, -h * .36]], '#2a2622', 52, 0, 1);
    if (face !== 'B') { const sx = side ? .6 : 1, cx = side * bw * .18; g.save(); g.translate(cx, -h * .68); g.scale(sx, 1);
      g.lineWidth = 5; g.strokeStyle = '#6b5a3a'; g.beginPath(); g.arc(0, 0, h * .17, 0, Math.PI * 2); g.stroke();
      g.beginPath(); g.moveTo(0, h * .12); g.lineTo(0, -h * .12); for (let k = 0; k < 3; k++) { g.moveTo(0, -h * .02 - k * h * .04); g.lineTo(-h * .06, -h * .07 - k * h * .04); g.moveTo(0, -h * .02 - k * h * .04); g.lineTo(h * .06, -h * .07 - k * h * .04); } g.stroke(); g.restore(); }
    else { g.fillStyle = '#4a3f33'; g.fillRect(-6, -h * .46, 12, h * .12); } }
  if (face === 'B') { g.setLineDash([8, 8]); g.lineWidth = 2; g.strokeStyle = 'rgba(20,16,12,.55)'; g.beginPath(); g.moveTo(0, -h + sag); g.lineTo(0, 0); g.stroke(); g.setLineDash([]); }
  if (id === 'I') { g.lineWidth = 2; g.strokeStyle = 'rgba(60,45,30,.5)'; for (let k = 0; k < 3; k++) { g.beginPath(); g.moveTo(-bw * .3 + k * bw * .25, -h * .7); g.lineTo(-bw * .2 + k * bw * .25, -h * .35); g.stroke(); } }
  // damage stickers (ledger body tags)
  if (face !== 'B') {
    if (tags.includes('blot')) { blob(g, side * bw * .1 + bw * .12, -h * .45, Math.min(bw, h) * .17, seed + 70); blob(g, side * bw * .1 + bw * .14, -h * .26, Math.min(bw, h) * .05, seed + 75); }
    if (tags.includes('tag')) { g.save(); g.translate(-bw * .2 + side * bw * .1, -h * .6); g.rotate(-.25); cut(g, [[-14, -10], [16, -10], [16, 14], [-14, 14]], '#fbfbf4', seed + 80, 2, 1); disc(g, -8, -4, 4, '#c8322c'); g.restore(); }
    if (tags.includes('torn')) { g.lineWidth = 3; g.strokeStyle = INK; g.beginPath(); for (let k = 0; k < 7; k++) g.lineTo(-bw * .38 + (k % 2) * 10, -h * .62 + k * h * .06); g.stroke(); }
    if (tags.includes('coins')) { for (let k = 0; k < 3; k++) disc(g, bw * .25 - k * 14, -14 - k * 4, 8, '#e6c24a', 2); }
  }
  if (tags.includes('rope')) { cut(g, [[-bw, -h * .55], [bw, -h * .55], [bw, -h * .47], [-bw, -h * .47]], '#8a6a3a', seed + 90, 2, 1); }
  if (tags.includes('gag')) { cut(g, [[-bw, -h * .9], [bw, -h * .9], [bw, -h * .82], [-bw, -h * .82]], '#efe9dd', seed + 91, 2, 1); }
  g.restore();
  // Ogiva's wig: over the top, falling past the shoulders; at BACK it covers half the card
  if (id === 'O') { const wc = mixc('#7a3b8f', '#55505a', greyU * .6), wl = face === 'B' ? h * .55 : h * .5;
    if (side) cut(g, [[-bw / 2 - 6, -h - 8], [bw / 2 + 4, -h - 8], [bw / 2 + 4, -h * .86], [-side * bw * .1, -h * .86], [-side * (bw / 2 + 12), -h + wl], [-side * (bw / 2 - 8), -h + wl + 6]].map(p => side > 0 ? p : [p[0], p[1]]), wc, 66, 2.5, 1.5);
    else if (face === 'B') cut(g, [[-bw / 2 - 10, -h - 10], [bw / 2 + 10, -h - 10], [bw / 2 + 12, -h + wl], [-bw / 2 - 12, -h + wl]], wc, 67, 2.5, 1.5);
    else cut(g, [[-bw / 2 - 10, -h - 10], [bw / 2 + 10, -h - 10], [bw / 2 + 12, -h + wl], [bw / 2 - 6, -h + wl + 4], [bw / 2 - 8, -h * .86], [-bw / 2 + 8, -h * .86], [-bw / 2 + 6, -h + wl + 4], [-bw / 2 - 12, -h + wl]], wc, 68, 2.5, 1.5); }
  if (id === 'R' && face === 'B') cut(g, [[-6, -h * .82], [8, -h * .82], [14, -h * .55], [-10, -h * .6]], '#6e3a33', 69, 2, 1);
  g.restore();
  return { w, h };
}

// ---------- the ledger reading: everything the beat does is chosen here ----------
function plan(ev, st) {
  const A = ev.A, V = ev.V, others = IDS.filter(s => s !== A && s !== V);
  const live = others.filter(s => st.alive[s]);
  const mean = (arr, f) => arr.length ? arr.reduce((a, s) => a + f(s), 0) / arr.length : 0;
  const hA = mean(live, o => st.belief[o][A].harm.m), hV = mean(live, o => st.belief[o][V].harm.m);
  const gA = mean(live, o => st.mind[o][A].grudge);
  const mA = st.myth[A], mV = st.myth[V];
  // does the story come back on the doer? the house weighs who the teller already is against who the victim is
  const bf = (mA.PREDATOR || 0) + (mA.SPY || 0) * .5 + (mA.GHOST || 0) + (hA - hV) + gA * .8
    + (st.alive[V] ? 0 : .35) + ((mV.IDOL || 0) + (mV.INVULNERABLE || 0) + (mV['GENTLE GIANT'] || 0)) * .45 - (mV.PREDATOR || 0) * .6 - (mV.SCAPEGOAT || 0) * .3;
  const back = bf > .9 ? 2 : bf > .5 ? 1 : 0;          // 0 sticks · 1 falls in the snow between them · 2 comes back
  const mind = st.mind[A][V];
  const react = !st.alive[A] ? 'ghost' : mind.guilt >= .5 ? 'guilt' : (mind.pride >= .4 && A !== 'I') ? 'pride' : 'careless';
  const role = {}; for (const o of live) { const m = st.mind[o][V]; role[o] = m.grudge > .4 ? 'join' : m.desire > .4 ? 'linger' : 'avoid'; }
  return { A, V, others, live, back, bf, react, role, vDead: !st.alive[V], aDead: !st.alive[A], L: st.levers };
}

// ---------- stage template: STREET (one template, reused by every pair) ----------
function street(g, tq, P, doors, lights, marks) {
  g.fillStyle = '#1b2748'; g.fillRect(0, 0, 1920, 1080);
  for (let i = 0; i < 30; i++) { const x = H(i * 3.7) * 1920, y = H(i * 5.1) * 200; disc(g, x, y, 2 + H(i) * 2, '#cfd6e6'); }
  disc(g, 1790, 90, 50, '#f3eed2', 3);
  cut(g, [[-20, 860], [1940, 860], [1940, 1100], [-20, 1100]], SNOW, 8, 3, 3);
  g.fillStyle = '#d6dde6'; g.fillRect(0, 1010, 1920, 6);
  // neighbour houses at the frame edges (the street)
  cut(g, [[-20, HB], [-20, 330], [60, 250], [150, 330], [150, HB]], '#9a5b45', 120, 3, 3);
  cut(g, [[1770, HB], [1770, 330], [1860, 250], [1940, 330], [1940, HB]], '#5f7f9a', 130, 3, 3);
  win(g, 70, 420, lights.N0, 123, 0, 100); win(g, 1850, 420, lights.N1, 133, 1, 100);
  // the boarding house
  cut(g, [[170, HB], [170, 330], [1750, 330], [1750, HB]], '#8e7a62', 140, 3.5, 3);
  cut(g, [[140, 340], [960, 140], [1780, 340]], '#5a3e34', 141, 3.5, 3);
  cut(g, [[130, 346], [960, 128], [1790, 346], [1770, 360], [960, 152], [150, 360]], SNOW, 142, 3, 2);
  cut(g, [[1350, 240], [1350, 160], [1410, 160], [1410, 255]], '#5a3e34', 143, 3, 2);
  for (const id of IDS) {
    door(g, DOORX[id], 200, 330, doors[id], DOORC[id], 150 + IDS.indexOf(id), id === 'B');
    win(g, DOORX[id], 380, lights[id], 160 + IDS.indexOf(id), id, 110);
    if (marks[id] > 0) markX(g, DOORX[id], HB - 180, marks[id], 170 + IDS.indexOf(id));
  }
}
// door states: 1 shut (its owner's colour) · 0 open (dark room, lamplight on the floor, the leaf flat on the wall) · swapped, never tweened
function door(g, x, w, h, open, col, seed, wheat) {
  const y0 = HB - h;
  cut(g, [[x - w / 2 - 12, HB], [x - w / 2 - 12, y0 - 12], [x + w / 2 + 12, y0 - 12], [x + w / 2 + 12, HB]], '#5e4d3c', seed + 299, 3, 1);
  if (open > 0) { cut(g, [[x - w / 2, HB], [x - w / 2, y0], [x + w / 2, y0], [x + w / 2, HB]], '#24170e', seed + 300, 3, 1.5);
    cut(g, [[x - w / 2 + 10, HB], [x - w * .2, y0 + h * .45], [x + w * .25, y0 + h * .45], [x + w / 2 - 6, HB]], '#f2c75c', seed + 303, 0, 1);
    cut(g, [[x - w / 2, y0], [x - w / 2 - 46, y0 + 22], [x - w / 2 - 46, HB + 14], [x - w / 2, HB]], col, seed + 301, 3, 1.5); }
  else { cut(g, [[x - w / 2, HB], [x - w / 2, y0], [x + w / 2, y0], [x + w / 2, HB]], col, seed + 302, 3, 1.5); disc(g, x + w * .34, y0 + h * .55, 9, '#d9b24a', 2);
    if (wheat) { g.lineWidth = 5; g.strokeStyle = '#8a7650'; g.beginPath(); g.arc(x, y0 + h * .28, 34, 0, Math.PI * 2); g.stroke(); } }
}
// window: 0 dark, (0,1] lit; who peeks: a townsperson silhouette (neighbours) or the owner's colour card (house)
function win(g, x, y, lit, seed, who, w = 120) {
  const h = w * .9;
  cut(g, [[x - w / 2, y + h], [x - w / 2, y], [x + w / 2, y], [x + w / 2, y + h]], lit > 0 ? '#f6d872' : '#1c2338', seed, 3, 1.5);
  if (lit > 0) {
    if (who === 0 || who === 1) { disc(g, x + (lit > .5 ? (who === 0 ? 10 : -10) : 0), y + 50, 22, '#1e1a1a'); cut(g, [[x - 34, y + h], [x - 26, y + 70], [x + 26, y + 70], [x + 34, y + h]], '#1e1a1a', seed + 9, 0, 1);
      if (lit > .5) cut(g, [[x - 26 + (who === 0 ? 18 : -18), y + 30], [x + 26 + (who === 0 ? 18 : -18), y + 30], [x + 18 + (who === 0 ? 18 : -18), y + 22], [x - 18 + (who === 0 ? 18 : -18), y + 22]], '#1e1a1a', seed + 8, 0, 1); }
    else if (lit > 1) { cut(g, [[x - w / 2 + 4, y + 4], [x + w / 2 - 4, y + 4], [x + w / 2 - 4, y + h - 4], [x - w / 2 + 4, y + h - 4]], DOORC[who], seed + 6, 2, 1); }
    else cut(g, [[x - w / 2 + 4, y + 4], [x - 6, y + 4], [x - 16, y + h - 4], [x - w / 2 + 4, y + h - 4]], DOORC[who], seed + 7, 2, 1);
  }
  g.lineWidth = 4; g.strokeStyle = INK; g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + h); g.moveTo(x - w / 2, y + h / 2); g.lineTo(x + w / 2, y + h / 2); g.stroke();
  if (lit <= 0) { cut(g, [[x - w / 2 - 30, y + h], [x - w / 2 - 30, y], [x - w / 2, y], [x - w / 2, y + h]], '#3f4c38', seed + 20, 3, 1); cut(g, [[x + w / 2, y + h], [x + w / 2, y], [x + w / 2 + 30, y], [x + w / 2 + 30, y + h]], '#3f4c38', seed + 21, 3, 1); }
}
// the mark: two brush strokes of ink, painted on in two frames
function markX(g, x, y, u, seed) {
  const r = 70;
  const s1 = cl(0, 1, u * 2), s2 = cl(0, 1, u * 2 - 1);
  g.lineCap = 'round';
  for (const [c, lw] of [['#f4f1e6', 34], [INK, 22]]) { g.strokeStyle = c; g.lineWidth = lw;
  g.beginPath(); g.moveTo(x - r, y - r); g.lineTo(x - r + 2 * r * s1, y - r + 2 * r * s1); g.stroke();
  if (s2 > 0) { g.beginPath(); g.moveTo(x + r, y - r); g.lineTo(x + r - 2 * r * s2, y - r + 2 * r * s2); g.stroke(); } }
  if (u >= 1) for (let k = 0; k < 3; k++) { const dx = x - 40 + k * 38 + H(seed + k) * 10; g.lineWidth = 7; g.beginPath(); g.moveTo(dx, y + r * .6); g.lineTo(dx, y + r + 20 + H(seed + k * 3) * 40); g.stroke(); }
  g.lineCap = 'butt';
}
// a story-bit in flight: a black ink blot hopping on a parabola (a slide, stepped at 12/s)
function hop(g, x0, y0, x1, y1, u, seed, r = 16) {
  if (u <= 0 || u >= 1) return;
  const at = v => [x0 + (x1 - x0) * v, y0 + (y1 - y0) * v - Math.sin(Math.PI * v) * 200];
  for (let k = 2; k >= 1; k--) { const v = u - k * .09; if (v > 0) { const q = at(v); g.save(); g.globalAlpha *= .3 / k; blob(g, q[0], q[1], r * (1 - k * .2), seed); g.restore(); } }
  const q = at(u); blob(g, q[0], q[1], r * 1.6, seed);
}

// ---------- the beat ----------
function beat(g, t, ev, st, K) {
  const tq = Math.floor(t * FPS + 1e-6) / FPS, f = Math.floor(t * FPS + 1e-6);
  const P = plan(ev, st), A = P.A, V = P.V, Lv = P.L;
  const CT = 1.35;                                  // the mark lands on the victim's door
  // --- the spread: story bits hop from the doer to every listener (living bystanders, the neighbours, the windows)
  const listeners = [];
  P.live.forEach((o, i) => listeners.push({ kind: 'sack', id: o, t: .4 + i * .2 }));
  listeners.push({ kind: 'N', id: 'N0', t: .55 }, { kind: 'N', id: 'N1', t: .75 });
  const dur = 0.34 / (1 + .4 * cl(0, 1, Lv[A].tempo + .2));
  // positions
  const pos = {};
  pos[A] = { x: 470, y: FY }; pos[V] = { x: 1450, y: FY };
  const homeX = { }; P.others.forEach((o, i) => { homeX[o] = [860, 1130][i]; });
  // doors and lights
  const doors = { R: 0, B: 0, I: 0, O: 0 }, lights = { R: 1, B: 1, I: 1, O: 1, N0: 0, N1: 0 }, marks = { R: 0, B: 0, I: 0, O: 0 };
  for (const o of P.others) if (!st.alive[o]) lights[o] = 0;
  if (P.vDead) { lights[V] = 0; }
  // neighbours: window lights when the story reaches it, silhouette turns to the victim, then shutters slam
  const nShut = { N0: 1.7, N1: 1.9 };
  for (const L of listeners) if (L.kind === 'N') { if (tq >= L.t + dur) lights[L.id] = tq >= L.t + dur + .25 ? 1 : .4; if (tq >= nShut[L.id]) lights[L.id] = 0; }
  // the mark
  const mk = lin(CT, CT + 2 / FPS, tq); marks[V] = Math.floor(mk * 2) / 2;
  if (tq >= CT + .3) lights[V] = 0;
  // backfire: the second mark on the doer's own door
  const RB0 = 2.05, RB1 = RB0 + .42;
  if (P.back === 2) marks[A] = Math.floor(lin(RB1, RB1 + 2 / FPS, tq) * 2) / 2;
  // bystanders: turn their backs (swap), slide to their own doors, go in; door swaps shut
  const by = {};
  P.live.forEach((o, i) => {
    const r = P.role[o], heard = .4 + i * .2 + dur;
    const tTurn = r === 'linger' ? 1.95 : 1.5 + i * .1, tGo = tTurn + .08, tIn = tGo + (r === 'linger' ? .6 : .55);
    const go = lin(tGo, tIn, tq);
    let x = homeX[o] + (DOORX[o] - homeX[o]) * go, y = FY + (HB + 8 - FY) * go;
    let face = tq < heard ? 'F' : tq < tTurn ? (r === 'join' ? 'R' : 'R') : (DOORX[o] < x ? 'L' : 'R');
    if (tq >= tTurn && Math.abs(DOORX[o] - x) < 30) face = 'B';
    if (r === 'linger' && tq >= 1.5 && tq < 1.95) face = (f % 6 < 3) ? 'R' : 'L';
    let ear = tq < heard ? 'NEU' : tq < tTurn ? (r === 'join' ? 'UP' : 'UP') : 'FLAT';
    if (r === 'linger' && tq >= 1.5 && tq < 1.95) ear = 'DRP';
    // walking bob: up on every other card
    const bob = go > 0 && go < 1 && f % 2 ? -8 * (1 - .5 * cl(0, 1, Lv[o].weight)) : 0;
    const inside = tq >= tIn;
    by[o] = { x, y: y + bob, face, ear, inside, sc: .95 - .08 * go, tIn };
    doors[o] = tq >= tGo && tq < tIn + 1 / FPS ? 1 : 0;
    if (tq >= tIn + .25) lights[o] = 2;   // safe inside, its curtain drawn
  });
  // the dead bystanders: their doors are already shut, nothing comes out
  // --- stage
  street(g, tq, P, doors, lights, marks);
  // snow stain where a returning story falls short
  if (P.back === 1 && tq >= RB1) { g.save(); g.transform(1, 0, 0, .3, 0, FY * .7 + 10); blob(g, 960, FY + 30, 80, 401); blob(g, 900, FY + 10, 22, 402); blob(g, 1040, FY + 50, 18, 403); g.restore(); }
  // --- shadows (moon upper right: shadows fall left; PREDATOR/SPY lengthen them)
  const shadow = (id, x, y, w) => { const s = cl(0, 1.4, Lv[id].shadow); g.save(); g.globalAlpha = .28 + .35 * cl(0, 1, s); g.fillStyle = '#3b4a6a';
    g.beginPath(); g.ellipse(x - w * (.3 + .9 * s), y + 6, w * (.6 + 1.1 * s), 14 + 6 * s, 0, 0, Math.PI * 2); g.fill(); g.restore(); };
  const halo = (id, x, y, h) => { const a = cl(0, 1, Lv[id].halo); if (a < .15) return; g.save(); g.globalAlpha = .4 * a; g.beginPath(); g.ellipse(x, y - h * .5, h * .55 + 30, h * .62 + 20, 0, 0, Math.PI * 2); g.fillStyle = '#fff3b0'; g.fill(); g.restore(); };
  const scaleOf = id => (1 + .14 * cl(-1, 1.2, Lv[id].loom)) * (1 - .28 * cl(0, 1, Lv[id].shrink));
  const earOf = (id, def) => Lv[id].shrink > .45 && def === 'NEU' ? 'DRP' : def;
  // bystanders behind the principals
  for (const o of P.live) { const b = by[o]; if (b.inside) continue; const sc = b.sc * scaleOf(o);
    shadow(o, b.x, FY, 60 * sc); sack(g, o, { x: b.x, y: b.y, sc, face: b.face, ear: earOf(o, b.ear), grey: Lv[o].grey, tags: st.body[o] }); }
  // the joiner adds its own bit (it uses the story)
  P.live.forEach((o, i) => { if (P.role[o] === 'join') { const t0 = .4 + i * .2 + dur + .15; hop(g, homeX[o], FY - 160, DOORX[V], HB - 180, lin(t0, t0 + dur, tq), 500 + i, 12); } });
  // --- the victim
  {
    const id = V, sc0 = scaleOf(id);
    const startle = tq >= CT && tq < CT + .25;
    const shrinkMore = sm(CT + .3, CT + 1.3, tq);
    const sc = sc0 * (1 - .18 * shrinkMore);
    let face = tq < CT + .5 ? 'F' : (tq < 2.5 ? (DOORX[V] < 1450 ? 'L' : 'R') : 'B');
    let ear = startle ? 'UP' : tq < CT ? 'NEU' : 'DRP', lean = 0, vsq = startle ? -.3 : 0;
    let x = 1450 + (startle && f % 2 ? 10 : 0) - (tq >= 2.5 && !P.vDead ? 40 * sm(2.5, 3.0, tq) : 0);
    // each victim takes the mark its own way
    if (id === 'R' && tq >= 2.5) { lean = (Math.floor(f / 3) % 2 ? .06 : -.06); ear = 'FLAT'; }            // rocks, ears pinned: keeps her accounts
    if (id === 'B' && tq >= 1.85 && !P.vDead) { const u = Math.floor(sm(1.85, 2.3, tq) * 4) / 4; x -= 140 * u; face = tq < 2.4 ? 'L' : 'B';  // goes after them; the door shuts in his face
      if (tq >= 2.3 && tq < 2.45) { vsq = .35; ear = 'UP'; } }
    if (id === 'I' && tq >= CT + .5) { face = 'F'; vsq = .25 * sm(CT + .5, 2.2, tq); ear = 'DRP'; }      // does not even turn; slumps into the snow
    if (id === 'O' && tq >= CT + .35) { face = 'B'; ear = 'FLAT'; if (tq >= 2.55 && tq < 2.8) face = 'L'; } // turns her back at once; one look over the shoulder
    if (P.back === 2 && tq >= RB1 && tq < RB1 + .25) { face = 'L'; ear = 'UP'; }
    const C = { R: [168, 122], B: [244, 214], I: [128, 98], O: [80, 184] }[id];
    shadow(id, x, FY, C[0] * S * sc * .5);
    if (P.vDead) sack(g, id, { x, y: FY, sc: sc0, face: 'F', ear: 'DRP', grey: 1, tags: st.body[id], dead: true });
    else { halo(id, x, FY, C[1] * S * sc); sack(g, id, { x, y: FY, sc, face, ear, lean, grey: Lv[id].grey + .25 * shrinkMore, tags: st.body[id], squash: vsq }); }
    // the others' avoidance made literal: every bystander's facing points away (already), the house lights go off around it
  }
  // --- the doer
  {
    const id = A, sc = scaleOf(id), C = { R: [168, 122], B: [244, 214], I: [128, 98], O: [80, 184] }[id];
    let x = 470, face = 'R', ear = 'NEU', lean = 0, squash = 0, alpha = 1, y = FY;
    const talking = tq >= .3 && tq < 1.25;
    if (talking) { ear = f % 2 ? 'UP' : 'NEU'; y -= f % 2 ? 7 : 0; lean = .05 * cl(0, 1, Lv[id].loom + .3); }
    if (tq >= 1.25 && tq < 2.0) { ear = 'UP'; }
    if (tq >= 2.0) {
      if (P.react === 'guilt') { const u = sm(2.15, 2.6, tq); x = 470 + 150 * Math.floor(u * 4) / 4; face = 'R'; ear = tq > 2.6 ? 'DRP' : 'NEU'; if (tq > 2.75) face = 'F'; }
      else if (P.react === 'pride') { face = 'F'; ear = 'UP'; y -= (f % 4 < 2 ? 10 : 0) * (1 - .5 * cl(0, 1, Lv[id].weight)); squash = f % 4 < 2 ? -.2 : .1; }
      else if (P.react === 'careless') { face = 'L'; ear = 'DRP'; x = 470 - 90 * sm(2.2, 2.9, tq); y -= f % 2 ? 5 : 0; }
      else { face = 'F'; ear = 'FLAT'; alpha = .55 + .15 * (f % 2); }
    }
    if (P.aDead) alpha = Math.min(alpha, .55 + .1 * (f % 2));
    if (P.back === 2 && tq >= RB1) { ear = tq < RB1 + .25 ? 'UP' : 'DRP'; face = tq < RB1 + .25 ? 'F' : 'L'; squash = tq < RB1 + .12 ? .35 : 0; }
    const shrinkB = P.back === 2 ? .14 * sm(RB1, RB1 + .5, tq) : 0;
    shadow(id, x, FY, C[0] * S * sc * .5);
    halo(id, x, FY, C[1] * S * sc);
    const tg = st.body[id].slice(); if (P.back === 2 && tq >= RB1 + 1 / FPS && !tg.includes('blot')) tg.push('blot');
    sack(g, id, { x, y, sc: sc * (1 - shrinkB), face, ear, lean, squash, alpha, grey: Lv[id].grey, tags: tg });
  }
  // --- flying story bits (drawn on top)
  listeners.forEach((L, i) => {
    let x1, y1; if (L.kind === 'sack') { x1 = homeX[L.id]; y1 = FY - 170; } else { x1 = L.id === 'N0' ? 70 : 1850; y1 = 460; }
    hop(g, 520, FY - 200, x1, y1, lin(L.t, L.t + dur, tq), 600 + i, 14);
  });
  hop(g, 520, FY - 200, DOORX[V], HB - 180, lin(CT - .38, CT, tq), 700, 26);       // the big one: onto the victim's door
  if (P.back >= 1) {
    const tx = P.back === 2 ? DOORX[A] : 960, ty = P.back === 2 ? HB - 180 : FY + 30;
    hop(g, DOORX[V], HB - 180, tx, ty, lin(RB0, RB1, tq), 710, 24);
  }
  // --- the outside: a vanished victim brings the insurance man's hat to the neighbour's doorway
  if (P.vDead && tq >= 2.3) { const u = Math.floor(lin(2.3, 2.6, tq) * 3) / 3; g.save(); g.translate(1700, HB - 250 + 20); cut(g, [[-50, 0], [50, 0], [50, -14], [26, -14], [22, -70], [-22, -70], [-26, -14], [-50, -14]].map(p => [p[0], p[1] + 80 * (1 - u)]), '#1a1a1e', 801, 2, 1); g.restore(); }
}

// ---------- sound: grains, timed to the 12-card clock ----------
function sound(ac, out, t0, ev, st, K) {
  const SND = K.SND, P = plan(ev, st), A = P.A, V = P.V, pan = x => cl(-1, 1, x / 960 - 1), T = x => t0 + x;
  const CT = 1.35, RB0 = 2.05, RB1 = RB0 + .42, dur = 0.34 / (1 + .4 * cl(0, 1, P.L[A].tempo + .2));
  SND.say(ac, out, A, T(.05), 'breathe', .5, pan(470));
  // the telling: doer's tick on every lifted card + a whisper hush
  for (let x = .3; x < 1.25; x += 2 / FPS) SND.say(ac, out, A, T(x), 'tick', .6, pan(470));
  SND.cloud(ac, out, T(.3), .95, 60, { bp: 3200, q: 2, a: .045, d: [.02, .06], spread: .3 }, u => Math.sin(Math.PI * u));
  // each bit: pop on leaving, papery pat + echoed hush where it lands
  const L = []; P.live.forEach((o, i) => L.push([.4 + i * .2, [860, 1130][P.others.indexOf(o)]])); L.push([.55, 90], [.75, 1850]);
  for (const [tt, x] of L) { SND.grain(ac, out, T(tt), { f: 900, glide: .6, d: .05, a: .08, pan: pan(520) }); SND.grain(ac, out, T(tt + dur), { bp: 1200, d: .04, a: .16, pan: pan(x) });
    SND.cloud(ac, out, T(tt + dur + .03), .35, 50, { bp: 2600, a: .03, d: [.02, .05], spread: .1 }, u => 1 - u); }
  P.live.forEach((o, i) => SND.say(ac, out, o, T(.4 + i * .2 + dur + .05), 'react', .4, pan([860, 1130][P.others.indexOf(o)])));
  // contact: the slap of the mark on the door, in two brush cards
  SND.grain(ac, out, T(CT - .38), { f: 700, glide: .9, d: .1, a: .08, pan: pan(520) });
  SND.thump(ac, out, T(CT), .9, 70, pan(DOORX[V]));
  SND.grain(ac, out, T(CT), { bp: 700, q: .8, d: .12, a: .7, pan: pan(DOORX[V]), att: .05 });
  SND.grain(ac, out, T(CT + 1 / FPS), { bp: 900, q: .8, d: .1, a: .4, pan: pan(DOORX[V]), att: .05 });
  if (!P.vDead) SND.say(ac, out, V, T(CT + .02), 'react', 1, pan(1450));
  // shutters (neighbours) and doors (bystanders)
  for (const [tt, x] of [[1.7, 90], [1.9, 1850]]) { SND.grain(ac, out, T(tt), { bp: 1500, q: 3, d: .03, a: .35, pan: pan(x) }); SND.grain(ac, out, T(tt + .05), { bp: 1300, q: 3, d: .03, a: .3, pan: pan(x) }); SND.thump(ac, out, T(tt + .2), .4, 80, pan(x)); }
  P.live.forEach((o, i) => { const r = P.role[o], tTurn = r === 'linger' ? 1.95 : 1.5 + i * .1, tIn = tTurn + .08 + (r === 'linger' ? .6 : .55);
    SND.say(ac, out, o, T(tTurn), 'tick', .8, pan(DOORX[o]));
    for (let x = tTurn + .08; x < tIn; x += 2 / FPS) SND.say(ac, out, o, T(x), 'step', .6, pan(DOORX[o]));
    SND.thump(ac, out, T(tIn), .75, 60, pan(DOORX[o])); SND.grain(ac, out, T(tIn + 1 / FPS), { bp: 1800, q: 4, d: .03, a: .3, pan: pan(DOORX[o]) }); });
  if (!P.vDead) SND.say(ac, out, V, T(2.45), 'sink', .9, pan(1450));
  else SND.cloud(ac, out, T(.2), 2.8, 30, { bp: 500, q: .7, a: .03, d: [.2, .5], spread: .9 }, u => Math.sin(Math.PI * u));
  if (P.back >= 1) { SND.grain(ac, out, T(RB0), { f: 500, glide: P.back === 2 ? -.5 : -.7, d: RB1 - RB0, a: .09, pan: pan(1000), type: 'triangle' });
    if (P.back === 2) { SND.grain(ac, out, T(RB1), { bp: 700, q: .8, d: .12, a: .5, pan: pan(DOORX[A]), att: .05 }); SND.thump(ac, out, T(RB1), .7, 70, pan(DOORX[A])); SND.say(ac, out, A, T(RB1 + .03), 'react', .9, pan(470)); }
    else SND.grain(ac, out, T(RB1), { bp: 300, q: .7, d: .15, a: .3, pan: 0 }); }
  if (P.react === 'guilt') { SND.say(ac, out, A, T(2.15), 'breathe', .8, pan(520)); for (let k = 0; k < 4; k++) SND.say(ac, out, A, T(2.15 + k * .11), 'step', .5, pan(520)); SND.say(ac, out, A, T(2.7), 'sink', .5, pan(620)); }
  if (P.react === 'pride') for (let x = 2.0; x < DUR; x += 4 / FPS) SND.say(ac, out, A, T(x), 'step', .7, pan(470));
  if (P.react === 'careless') SND.say(ac, out, A, T(2.2), 'breathe', 1, pan(430));
  if (P.vDead) for (let k = 0; k < 3; k++) SND.grain(ac, out, T(2.3 + k / 12), { bp: 2200, q: 4, d: .02, a: .12, pan: pan(1700) });
}

// ---------- trace: the ink X on a little door, washing out with every shot ----------
function trace(g, box, age, K) {
  const a = 1 / (1 + age * .35), x = box.x + box.w / 2, y = box.y + box.h / 2, s = Math.min(box.w, box.h) / 300;
  g.save(); g.globalAlpha *= .5 + .5 * a; g.translate(x, y); g.scale(s, s); g.translate(-x, -y);
  cut(g, [[x - 75, y + 140], [x - 75, y - 140], [x + 75, y - 140], [x + 75, y + 140]], '#8e7a62', 901, 3, 2);
  g.globalAlpha *= a; markX(g, x, y - 20, 1, 902); g.restore();
}

CONSEQ({
  deed: 'slander', n: 10, scion: 17, lineage: 'South Park — Repeatable Graphic Grammar', dur: DUR,
  op: 'On one reusable street template, black story-blots hop from the doer to every listener, an ink X lands on the victim\'s own door, the others swap to their backs and shut themselves in, the neighbours\' shutters slam, and a returning blot either misses, falls in the snow, or marks the doer\'s door too.',
  made: 'Flat construction-paper cutouts with a fixed scissor wobble and black outlines: a night street with snow, two neighbour houses, and the boarding house front with four doors, each in its owner\'s colour (maroon, belt-dark with wheat, faded tan, purple). Each sack is one kit: body card, two ear triangles from an ear atlas, its attribute card, and damage stickers read from the ledger.',
  moved: 'A 12-card-per-second clock of slides and substitutions: facing states swap (front, side, back), ears flip between UP, NEU, DROOP and FLAT in place of mouths, talkers bob on every other card, doors and shutters swap open to shut in two cards. The ledger chooses who joins in, who lingers, who goes in, how the doer reacts, and whether the story comes back; the archetype levers set size, shadow, halo, bob weight and grey.',
  beat, sound, trace
});
})();
