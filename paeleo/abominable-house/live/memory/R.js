// MEMORY · R · WIDOW ROESSLER — SCION-38 · Dynamic Pose Selection (drawing library + DP decoder).
// The widow remembers like a ledger keeper: every memory is an index card in a wooden card file.
// She is never interpolated: she is a LIBRARY of ten fixed drawings (pose features + a fixed line
// seed, so a drawing is identical every time it is shown). A Viterbi decoder picks one drawing per
// 1/12 s step from a target action script built from the ledger (which card, what feeling, how much),
// a transition matrix (feature distance + forbidden jumps) and minimum-duration holds. Key poses
// (the stamp of a grudge, the recoil of fear, the turn-away of guilt) are protected in the emission
// cost so the optimizer cannot average them away. The decoded path is inked on the ledger page at
// her feet: rows = drawings, columns = steps.
// Invariants (numeric, checked by _test): every drawing in the decoded path is held >= HMIN steps
// (except the last run), and every protected key pose is on the path at its key step.
// Grudges are filed forever (the card stays crisp at any age, red-edged, stamped, the owed counted
// in tally strokes); guilt barely surfaces (the card half-rises, blurred, and is pushed back).
(function () {
  const IDS = ['R', 'B', 'I', 'O'];
  const D2R = Math.PI / 180;
  const sig = x => 1 / (1 + Math.exp(-x));
  const cl = (a, b, x) => Math.max(a, Math.min(b, x));
  const sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u) };
  const hs = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s) };

  // ---------------- POSE LIBRARY: ten drawings of the widow ----------------
  // h,w: height/width multipliers; lean: shear (top toward the card file is +); bend: top sag;
  // eL/eR: ear [angle from vertical, outward +, deg ; length as fraction of height]; turn: 0 front, 1 turned away;
  // dx: root offset (fraction of width), the feet stay on the floor line in every drawing.
  const LIB = [
    { id: 'IDLE',    h: 1.00, w: 1.00, lean: 0.00, bend: .06, eL: [40, .22],  eR: [40, .22],  turn: 0, dx: 0 },
    { id: 'LOOK',    h: .90,  w: 1.06, lean: .26,  bend: .14, eL: [62, .20],  eR: [98, .24],  turn: 0, dx: .05 },
    { id: 'REACH',   h: 1.10, w: .94,  lean: .30,  bend: .03, eL: [30, .20],  eR: [58, .62],  turn: 0, dx: .1 },
    { id: 'HOLD',    h: 1.03, w: 1.00, lean: .12,  bend: .02, eL: [16, .32],  eR: [16, .32],  turn: 0, dx: .05 },
    { id: 'RECOIL',  h: 1.14, w: .88,  lean: -.30, bend: 0.0, eL: [-4, .36],  eR: [-4, .36],  turn: 0, dx: -.18 },
    { id: 'CLUTCH',  h: .80,  w: 1.12, lean: -.06, bend: .18, eL: [152, .26], eR: [152, .26], turn: 0, dx: -.12 },
    { id: 'STAMP',   h: .70,  w: 1.24, lean: .22,  bend: .10, eL: [72, .20],  eR: [86, .36],  turn: 0, dx: .12 },
    { id: 'COUNT',   h: .95,  w: 1.04, lean: .10,  bend: .08, eL: [44, .20],  eR: [112, .30], turn: 0, dx: .06 },
    { id: 'TURN',    h: .98,  w: .78,  lean: -.12, bend: .06, eL: [40, .20],  eR: [124, .18], turn: 1, dx: -.08 },
    { id: 'RETREAT', h: .78,  w: 1.08, lean: -.20, bend: .16, eL: [122, .18], eR: [122, .18], turn: .6, dx: -.38 }
  ];
  const P = {}; LIB.forEach((p, i) => P[p.id] = i);
  const feat = p => [p.h * 2, p.w * 2, p.lean * 3, Math.cos(p.eL[0] * D2R) + Math.cos(p.eR[0] * D2R), p.eR[1] * 2, p.turn * 1.5, p.dx * 2];
  const F = LIB.map(feat);
  const dist = (a, b) => { let s = 0; for (let i = 0; i < a.length; i++) s += (a[i] - b[i]) * (a[i] - b[i]); return Math.sqrt(s) };
  // transition matrix: cost of cutting from drawing a to drawing b (0 to stay)
  const FORBID = [['IDLE', 'STAMP'], ['IDLE', 'RECOIL'], ['CLUTCH', 'REACH'], ['RETREAT', 'STAMP'], ['TURN', 'STAMP'], ['RETREAT', 'REACH'], ['CLUTCH', 'STAMP']];
  const T = LIB.map((a, i) => LIB.map((b, j) => i === j ? 0 : .6 + dist(F[i], F[j]) * .55));
  for (const [a, b] of FORBID) { T[P[a]][P[b]] += 6; T[P[b]][P[a]] += 3 }
  const FPS = 12;

  // Viterbi over (drawing, steps-held) with minimum-duration holds and protected keys
  function decode(target, keys, hmin) {
    const N = target.length, M = LIB.length, Hc = hmin;
    const INF = 1e9; let cost = [], back = [];
    const emit = (i, p) => { const tg = target[i]; let c = tg ? dist(F[p], F[tg.p]) * tg.w : 0; if (keys[i] !== undefined) c += keys[i] === p ? -40 : 40; return c };
    // state index p*(Hc+1)+d, d = min(held,Hc)
    let cur = new Array(M * (Hc + 1)).fill(INF);
    for (let p = 0; p < M; p++) cur[p * (Hc + 1) + 1] = emit(0, p) + (p === P.IDLE ? 0 : 3);
    cost.push(cur);
    for (let i = 1; i < N; i++) {
      const nx = new Array(M * (Hc + 1)).fill(INF), bk = new Array(M * (Hc + 1)).fill(-1);
      for (let p = 0; p < M; p++) for (let d = 1; d <= Hc; d++) {
        const c0 = cur[p * (Hc + 1) + d]; if (c0 >= INF) continue;
        // stay
        const sd = Math.min(Hc, d + 1), si = p * (Hc + 1) + sd, sc = c0 + emit(i, p);
        if (sc < nx[si]) { nx[si] = sc; bk[si] = p * (Hc + 1) + d }
        // cut (only after the minimum hold)
        if (d >= Hc) for (let q = 0; q < M; q++) if (q !== p) {
          const qi = q * (Hc + 1) + Math.min(Hc, 1), qc = c0 + T[p][q] + emit(i, q);
          if (qc < nx[qi]) { nx[qi] = qc; bk[qi] = p * (Hc + 1) + d }
        }
      }
      cost.push(nx); back.push(bk); cur = nx;
    }
    let bi = 0; for (let s = 1; s < cur.length; s++) if (cur[s] < cur[bi]) bi = s;
    const path = new Array(N); for (let i = N - 1; i >= 0; i--) { path[i] = Math.floor(bi / (Hc + 1)); if (i > 0) bi = back[i - 1][bi] }
    return path;
  }

  // ---------------- what she feels about a card ----------------
  const FEEL_COL = { dead: '#0c0907', grudge: '#9a2316', fear: '#24406e', guilt: '#8a867a', desire: '#b65a72', pride: '#b08a22', debt: '#8a6a12', witness: '#6d7a64', none: '#b9ae94' };
  function feelOf(m, st) {
    if (!m) return { f: 'none', amt: 0 };
    if (m.role === 'witness') return { f: 'witness', amt: .35 };
    const md = st && st.mind && st.mind.R && st.mind.R[m.other] || {};
    const c = m.role === 'doer'
      ? { guilt: (md.guilt || 0) * .55, pride: (md.pride || 0) * .9, desire: (md.desire || 0) * .8 }
      : { fear: md.fear || 0, grudge: (md.grudge || 0) * 1.15, desire: (md.desire || 0) * .8, debt: (md.debt || 0) * .7 };
    let f = 'none', v = -1; for (const k in c) if (c[k] > v) { v = c[k]; f = k }
    if (v <= .02) f = m.role === 'doer' ? 'pride' : 'grudge';
    return { f, amt: cl(.25, 1, v), all: c };
  }
  const LV0 = { loom: 0, weight: 0, tempo: 0, halo: 0, shadow: 0, shrink: 0, grey: 0 };

  // ---------------- the script: target drawings per step for a feeling ----------------
  function script(feel, dur, lv, weight) {
    const N = Math.round(dur * FPS), target = new Array(N).fill(null), keys = {};
    const put = (a, b, id, w) => { for (let i = Math.round(a * FPS); i < Math.min(N, Math.round(b * FPS)); i++) target[i] = { p: P[id], w } };
    const key = (t, id) => { const i = Math.min(N - 1, Math.round(t * FPS)); keys[i] = P[id] };
    const k = 1 / (1 + (lv.tempo || 0) * .4); // tempo: crisper, everything earlier
    put(0, .4, 'IDLE', 2);
    if (feel === 'none') { put(.4, 1.0, 'LOOK', 1); put(1.0, 1.6, 'COUNT', 1.5); put(1.6, 2.1, 'IDLE', 1); put(2.1, dur, 'COUNT', 1); return { target, keys, N } }
    if (feel === 'dead') { return { target, keys, N } }
    put(.4 * k, .72 * k, 'LOOK', 1.4); put(.72 * k, 1.0 * k, 'REACH', 1.6); key(.82 * k, 'REACH');
    if (feel === 'grudge') { put(1.0 * k, 1.3 * k, 'HOLD', 1.2); key(1.38 * k, 'STAMP'); put(1.38 * k, 1.6 * k, 'STAMP', 1.5); put(1.6 * k, 2.15, 'COUNT', 1.5); put(2.15, dur, 'HOLD', 1) }
    else if (feel === 'fear') { key(1.08 * k, 'RECOIL'); put(1.08 * k, 1.35 * k, 'RECOIL', 2); put(1.45 * k, dur, 'CLUTCH', 1.6) }
    else if (feel === 'guilt') { put(1.0 * k, 1.2 * k, 'HOLD', .8); key(1.3 * k, 'TURN'); put(1.3 * k, 1.75, 'TURN', 1.6); put(1.85, dur, 'RETREAT', 1.2) }
    else if (feel === 'desire') { put(1.0 * k, 1.6, 'HOLD', 1.4); put(1.6, 2.1, 'LOOK', 1.2); put(2.1, dur, 'HOLD', 1.2) }
    else if (feel === 'pride' || feel === 'debt') { put(1.0 * k, 1.25 * k, 'HOLD', 1.2); put(1.3 * k, dur, 'COUNT', 1.6); key(1.5 * k, 'COUNT') }
    else { put(1.0 * k, 1.8, 'HOLD', 1.2); put(1.9, dur, 'IDLE', 1) } // witness
    return { target, keys, N };
  }
  const CACHE = {};
  function schedule(feel, dur, lv, weight) {
    const hmin = cl(1, 4, Math.round(2 + (lv.weight || 0) * 1.6 - (lv.tempo || 0) * 1.2));
    const ck = [feel, dur, hmin, (lv.tempo || 0).toFixed(2)].join('|');
    if (CACHE[ck]) return CACHE[ck];
    const s = script(feel, dur, lv, weight);
    const path = feel === 'dead' ? new Array(s.N).fill(P.IDLE) : decode(s.target, s.keys, hmin);
    return CACHE[ck] = { path, keys: s.keys, hmin, N: s.N };
  }

  // ---------------- drawing a sack from a library drawing ----------------
  function contour(p, W0, H0) {
    const H = H0 * p.h, Wd = W0 * p.w, pts = [];
    const q = (a, c, b, n) => { for (let i = 1; i <= n; i++) { const u = i / n, v = 1 - u; pts.push([v * v * a[0] + 2 * u * v * c[0] + u * u * b[0], v * v * a[1] + 2 * u * v * c[1] + u * u * b[1]]) } };
    const sR = [Wd * .46, -H * .9], sL = [-Wd * .46, -H * .9];
    const ear = (s, e, side) => { const a = e[0] * D2R, L = e[1] * H; return [s[0] + side * Math.sin(a) * L, s[1] - Math.cos(a) * L] };
    const tR = ear(sR, p.eR, 1), tL = ear(sL, p.eL, -1);
    const inR = [Wd * .26, -H * (.93 - p.bend * .3)], inL = [-Wd * .26, -H * (.93 - p.bend * .3)], top = [0, -H * (.93 - p.bend)];
    pts.push([-Wd * .5, -2]);
    q([-Wd * .5, -2], [0, 8], [Wd * .5, -2], 8);
    q([Wd * .5, -2], [Wd * .56, -H * .5], sR, 7);
    q(sR, [(sR[0] + tR[0]) / 2 + 12, (sR[1] + tR[1]) / 2 - 6], tR, 5);
    q(tR, [(tR[0] + inR[0]) / 2 - 4, (tR[1] + inR[1]) / 2 + 8], inR, 5);
    q(inR, [Wd * .12, top[1] + 2], top, 3); q(top, [-Wd * .12, top[1] + 2], inL, 3);
    q(inL, [(tL[0] + inL[0]) / 2 + 4, (tL[1] + inL[1]) / 2 + 8], tL, 5);
    q(tL, [(sL[0] + tL[0]) / 2 - 12, (sL[1] + tL[1]) / 2 - 6], sL, 5);
    q(sL, [-Wd * .56, -H * .5], [-Wd * .5, -2], 7);
    return { pts, H, Wd };
  }
  function wob(pts, seed, amp) { return pts.map((pt, i) => [pt[0] + (hs(seed + i * 1.7) - .5) * amp, pt[1] + (hs(seed + i * 3.1 + 9) - .5) * amp]) }
  function path(g, pts) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath() }
  const GREYMIX = (hex, gr) => { const n = parseInt(hex.slice(1), 16), r = n >> 16, gg = (n >> 8) & 255, b = n & 255, y = (r * .3 + gg * .59 + b * .11); const m = c => Math.round(c + (y - c) * gr); return `rgb(${m(r)},${m(gg)},${m(b)})` };

  // draws the widow from library drawing index pi at floor point (x,y), scale S; o: {grey, lamp:+1 right, body:[tags], ink}
  function drawWidow(g, pi, x, y, S, o) {
    o = o || {}; const p = LIB[pi], seed = 100 + pi * 37; // a drawing's line seed is its own: stable art
    const { pts, H, Wd } = contour(p, 168 * S, 122 * S);
    const gr = o.grey || 0, body = o.body || [];
    g.save(); g.translate(x + p.dx * Wd, y); g.transform(1, 0, -p.lean, 1, 0, 0);
    const P1 = wob(pts, seed, 3.2), P2 = wob(pts, seed + 50, 4.5);
    // cloth
    path(g, P1);
    const gd = g.createLinearGradient(-Wd * .5 * (o.lamp || 1), 0, Wd * .5 * (o.lamp || 1), 0);
    gd.addColorStop(0, GREYMIX('#9d8662', gr)); gd.addColorStop(.55, GREYMIX('#d6bf96', gr)); gd.addColorStop(1, GREYMIX('#ecdcb6', gr));
    g.fillStyle = gd; g.fill();
    g.save(); path(g, P1); g.clip();
    // hatching on the shadow side (fixed lines per drawing)
    g.strokeStyle = GREYMIX('#5b4a33', gr); g.globalAlpha = .35; g.lineWidth = 2;
    for (let i = 0; i < 16; i++) { const u = hs(seed + i * 5.3), xx = -Wd * .5 + u * Wd * .38, y0 = -H * (.1 + hs(seed + i) * .6); g.beginPath(); g.moveTo(xx, y0); g.lineTo(xx + 26, y0 - 30); g.stroke() }
    g.globalAlpha = 1;
    // shawl band: the top fifth (turned: it wraps wider)
    const by = -H * .76;
    g.fillStyle = GREYMIX('#6e3a33', gr); g.fillRect(-Wd, -H * 1.6, Wd * 2, H * 1.6 + by);
    g.strokeStyle = GREYMIX('#3d1d19', gr); g.lineWidth = 3;
    g.beginPath(); for (let i = 0; i <= 24; i++) { const xx = -Wd * .5 + i / 24 * Wd; g.moveTo(xx, by); g.lineTo(xx + (hs(seed + i) - .5) * 4, by + 10 + hs(seed + i * 2) * 6) } g.stroke();
    if (p.turn > 0) { g.fillStyle = 'rgba(30,18,12,' + (.28 * p.turn) + ')'; g.fillRect(-Wd * .5, -H * 1.6, Wd * (.25 + .3 * p.turn), H * 1.7) }
    // seam (turned away: the back seam shows)
    g.strokeStyle = GREYMIX('#7a6546', gr); g.lineWidth = 2; g.setLineDash([7, 6]);
    g.beginPath(); const sx = p.turn > 0 ? Wd * .05 : Wd * .3; g.moveTo(sx, -6); g.lineTo(sx * .9, by + 6); g.stroke(); g.setLineDash([]);
    // carried damage, drawn as drawing marks
    if (body.includes('torn')) { g.strokeStyle = '#2a1a10'; g.lineWidth = 3; g.beginPath(); for (let i = 0; i < 7; i++) g.lineTo(-Wd * .2 + i * 12, -H * .45 + (i % 2 ? 9 : -9)); g.stroke(); g.fillStyle = '#fbf7ee'; g.fillRect(-Wd * .2, -H * .45 - 2, 70, 4) }
    if (body.includes('blot')) { g.fillStyle = '#14100c'; g.beginPath(); for (let i = 0; i < 14; i++) { const a = i / 14 * 6.283, r = 26 + hs(i * 4.1) * 16; g.lineTo(Wd * .12 + Math.cos(a) * r, -H * .4 + Math.sin(a) * r) } g.fill() }
    if (body.includes('rope') || body.includes('cinched')) { g.strokeStyle = '#8a6a3a'; g.lineWidth = 7; for (const fy of body.includes('rope') ? [.3, .55] : [.7]) { g.beginPath(); g.moveTo(-Wd * .6, -H * fy); g.quadraticCurveTo(0, -H * fy + 14, Wd * .6, -H * fy); g.stroke() } }
    if (body.includes('gag')) { g.fillStyle = '#ddd2bb'; g.fillRect(-Wd * .55, -H * .7, Wd * 1.1, 18) }
    g.restore();
    // ink line: drawn twice (two fixed passes) like a pencil drawing
    g.strokeStyle = o.ink || '#1c130c'; g.lineJoin = 'round';
    g.lineWidth = 5; path(g, P1); g.stroke(); g.globalAlpha = .45; g.lineWidth = 2; path(g, P2); g.stroke(); g.globalAlpha = 1;
    if (body.includes('tag')) { g.fillStyle = '#efe6cf'; g.fillRect(-Wd * .35, -H * .35, 44, 30); g.strokeStyle = '#1c130c'; g.lineWidth = 2; g.strokeRect(-Wd * .35, -H * .35, 44, 30) }
    g.restore();
    return { H, Wd, x: x + p.dx * Wd, earR: [x + p.dx * Wd + Wd * .46 + Math.sin(p.eR[0] * D2R) * p.eR[1] * H + p.lean * H * .9, y - H * .9 - Math.cos(p.eR[0] * D2R) * p.eR[1] * H] };
  }

  // a small drawn silhouette of any sack (for the card margins: the other, as she believes it)
  function drawOther(g, id, x, y, s, o) {
    o = o || {}; const c = { R: [168, 122], B: [244, 214], I: [128, 98], O: [80, 184] }[id], w = c[0] * s, h = c[1] * s, sd = id.charCodeAt(0);
    const p = id === 'I' ? { h: 1, w: 1, lean: 0, bend: .2, eL: [160, .7], eR: [160, .7], turn: 0, dx: 0 } : id === 'O' ? { h: 1, w: 1, lean: 0, bend: .02, eL: [8, .1], eR: [8, .1], turn: 0, dx: 0 } : { h: 1, w: 1, lean: 0, bend: .06, eL: [30, .18], eR: [30, .18], turn: 0, dx: 0 };
    const { pts } = contour(p, w, h);
    g.save(); g.translate(x, y);
    const PP = wob(pts, sd * 11 + (o.seed || 0), o.wob || 2);
    path(g, PP);
    if (o.fill) { g.fillStyle = o.fill; g.fill() }
    if (o.attr !== false) {
      g.save(); path(g, PP); g.clip();
      if (id === 'R') { g.fillStyle = o.attrCol || '#6e3a33'; g.fillRect(-w, -h * 1.3, w * 2, h * .54) }
      if (id === 'B') { g.fillStyle = o.attrCol || '#2a2622'; g.fillRect(-w, -h * .44, w * 2, h * .07); g.strokeStyle = o.attrCol || '#2a2622'; g.lineWidth = Math.max(1, 3 * s); g.beginPath(); g.arc(0, -h * .68, w * .14, 0, 6.283); g.stroke() }
      g.restore();
      if (id === 'O') { g.fillStyle = o.attrCol || '#7a3b8f'; g.beginPath(); g.moveTo(-w * .62, -h * .55); g.quadraticCurveTo(-w * .7, -h * 1.12, 0, -h * 1.08); g.quadraticCurveTo(w * .7, -h * 1.12, w * .62, -h * .55); g.lineTo(w * .4, -h * .58); g.lineTo(w * .4, -h * .92); g.lineTo(-w * .4, -h * .92); g.lineTo(-w * .4, -h * .58); g.closePath(); g.fill() }
    }
    if (o.stroke) { g.strokeStyle = o.stroke; g.lineWidth = o.lw || 2; if (o.dash) g.setLineDash(o.dash); path(g, PP); g.stroke(); g.setLineDash([]) }
    g.restore();
  }

  // ---------------- the card: the remembered still, transformed by her filing ----------------
  const CARDC = {};
  function photo(still, m, feel, ago, pw, ph, K) {
    const key = m.k + m.deed + m.A + m.V + feel + ago + pw + 'x' + ph;
    if (CARDC[key]) return CARDC[key];
    const cv = document.createElement('canvas'); cv.width = pw; cv.height = ph; const q = cv.getContext('2d');
    // crop: around both sacks of the remembered frame (deed marks), leaning toward the other
    let bx = { x: 160, y: 140, w: 1600, h: 800 };
    try {
      const D = window.DEEDS && DEEDS[m.deed];
      if (D && D.marks) {
        const mk = D.marks(D.contact + .3, m.A, m.V, K), a = mk.A, b = mk.V;
        const x0 = Math.min(a.x, b.x), y0 = Math.min(a.y, b.y), x1 = Math.max(a.x + a.w, b.x + b.w), y1 = Math.max(a.y + a.h, b.y + b.h);
        let w = (x1 - x0) * 1.35 + 120, h = (y1 - y0) * 1.35 + 120; const ar = pw / ph; if (w / h < ar) w = h * ar; else h = w / ar;
        // fear: closer on the other (the threat fills the card)
        const o = m.other === m.A ? a : b; let cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
        if (feel === 'fear' || feel === 'grudge') { cx = cx * .5 + (o.x + o.w / 2) * .5; cy = cy * .6 + (o.y + o.h / 2) * .4; w *= .82; h *= .82 }
        w = Math.min(w, 1920); h = Math.min(h, 1080);
        bx = { x: cl(0, 1920 - w, cx - w / 2), y: cl(0, 1080 - h, cy - h / 2), w, h };
      }
    } catch (e) { }
    // how she files it: grudge = sharp, inked, never ages; guilt = blurred, pale; others age into sepia
    const age = feel === 'grudge' ? 0 : cl(0, 1, ago / 6);
    let flt = '';
    if (feel === 'grudge') flt = 'grayscale(1) contrast(1.9) brightness(1.05)';
    else if (feel === 'dead') flt = 'grayscale(1) brightness(.75) contrast(1.2)';
    else if (feel === 'guilt') flt = `grayscale(1) blur(${1.4 + ago * .6}px) contrast(.85) brightness(1.12)`;
    else if (feel === 'fear') flt = `grayscale(1) contrast(1.35) brightness(1.25) blur(${ago * .5}px)`;
    else if (feel === 'desire') flt = `sepia(.8) saturate(1.4) contrast(1.1) blur(${ago * .4}px)`;
    else flt = `sepia(${.6 + age * .4}) contrast(${1.2 - age * .3}) blur(${ago * .5}px)`;
    q.fillStyle = '#efe6cf'; q.fillRect(0, 0, pw, ph);
    q.filter = flt; q.drawImage(still, bx.x, bx.y, bx.w, bx.h, 0, 0, pw, ph); q.filter = 'none';
    // grudge: the image is inked over in red-brown, like a ledger entry underlined twice
    if (feel === 'grudge') { q.globalCompositeOperation = 'multiply'; q.fillStyle = '#e4b8a0'; q.fillRect(0, 0, pw, ph); q.globalCompositeOperation = 'source-over' }
    if (feel === 'fear') { q.globalCompositeOperation = 'multiply'; q.fillStyle = '#9fb0cc'; q.fillRect(0, 0, pw, ph); q.globalCompositeOperation = 'source-over' }
    // age: foxing spots
    q.fillStyle = 'rgba(120,80,30,.22)'; for (let i = 0; i < Math.round(age * 30); i++) { q.beginPath(); q.arc(hs(m.k * 7 + i) * pw, hs(m.k * 3 + i * 2.3) * ph, 2 + hs(i) * 7, 0, 6.283); q.fill() }
    return CARDC[key] = cv;
  }

  // one index card at (x,y) size cw×ch; rise 0..1 shows from the bottom (the drawer slot)
  function drawCard(g, x, y, cw, ch, m, fl, X, K, o) {
    o = o || {}; const feel = fl.f, col = FEEL_COL[feel], st0 = o.st;
    g.save(); g.translate(x, y); if (o.rot) g.rotate(o.rot);
    if (feel === 'desire') { g.save(); g.shadowColor = 'rgba(255,170,190,.7)'; g.shadowBlur = 60; g.fillStyle = '#efe6cf'; g.fillRect(0, 0, cw, ch); g.restore() }
    // paper
    g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(8, 10, cw, ch);
    g.fillStyle = feel === 'guilt' ? '#d9d3c4' : '#efe6cf'; g.fillRect(0, 0, cw, ch);
    // index-card rules: one red head rule, blue rules
    g.strokeStyle = 'rgba(70,110,170,.35)'; g.lineWidth = 1.5; for (let yy = ch * .2; yy < ch; yy += ch * .08) { g.beginPath(); g.moveTo(0, yy); g.lineTo(cw, yy); g.stroke() }
    g.strokeStyle = 'rgba(190,60,50,.7)'; g.lineWidth = 2.5; g.beginPath(); g.moveTo(0, ch * .13); g.lineTo(cw, ch * .13); g.stroke();
    // feeling edge (grudge: thick red border, kept)
    g.strokeStyle = col; g.lineWidth = feel === 'grudge' ? 10 : 5; g.strokeRect(0, 0, cw, ch);
    // the photograph of the remembered moment
    const pw = Math.round(cw * .64), ph = Math.round(ch * .74), px = cw * .03, py = ch * .19;
    if (m && m.still) { const ph0 = photo(m.still, m, feel, m.ago || 0, pw, ph, K); g.drawImage(ph0, px, py, pw, ph) }
    g.strokeStyle = '#1c130c'; g.lineWidth = 2; g.strokeRect(px, py, pw, ph);
    // corner pin marks holding the photo
    g.fillStyle = '#1c130c'; for (const [a, b] of [[px, py], [px + pw, py], [px, py + ph], [px + pw, py + ph]]) { g.beginPath(); g.moveTo(a - 8, b); g.lineTo(a, b - 8); g.lineTo(a + 8, b); g.lineTo(a, b + 8); g.fill() }
    // filing tab: who it was (the other's attribute colour), and the role: doer card tab left, victim right
    if (m) {
      const tc = { R: '#6e3a33', B: '#2a2622', I: '#c9b48a', O: '#7a3b8f' }[m.other];
      const tx = m.role === 'doer' ? cw * .05 : m.role === 'victim' ? cw * .62 : cw * .34;
      g.fillStyle = '#efe6cf'; g.fillRect(tx, -ch * .1, cw * .3, ch * .11); g.strokeStyle = col; g.lineWidth = 3; g.strokeRect(tx, -ch * .1, cw * .3, ch * .11);
      g.fillStyle = tc; g.fillRect(tx + 6, -ch * .085, cw * .3 - 12, ch * .08);
    }
    // the margin: her estimate of the other (PLoT): pencil = before the event, ink = after
    if (m && X && X.ledger && o.belief !== false) {
      const L = X.ledger, b0 = L.states[m.k].belief.R[m.other], b1 = L.states[Math.min(12, m.k + 1)].belief.R[m.other];
      const u = o.grow === undefined ? 1 : o.grow;
      // size = believed strength; the change is drawn at twice its size so one event reads
      const z = v => .45 + 1.1 * sig(v);
      const s0 = z(b0.str.m), s1 = cl(.35, 1.7, s0 + 2 * (z(b1.str.m) - s0)), s = s0 + (s1 - s0) * u;
      const mx = cw * .835, my = ch * .8;
      const sc = (ch * .36) / (214 * 1.5); // one scale for all four, so believed size and true size both read
      const gone = st0 && st0.alive && st0.alive[m.other] === false;
      g.save(); g.beginPath(); g.rect(cw * .68, ch * .16, cw * .31, ch * .66); g.clip();
      if (gone) { g.translate(mx, my); g.rotate(-Math.PI / 2); g.translate(-mx, -my + 0) }
      // uncertainty: as many trembling pencil outlines as she is unsure
      const nv = Math.round(1 + b1.str.v * 3);
      drawOther(g, m.other, mx, my, sc * s, gone ? { stroke: '#6a645a', lw: 3, attr: false } : { fill: 'rgba(28,19,12,.9)', stroke: '#1c130c', lw: 2, attrCol: { R: '#a04a40', B: '#6a5a48', I: '#2a1c14', O: '#a35bbf' }[m.other] });
      // the earlier estimate stays pencilled over it (light where it falls on ink), as many outlines as she is unsure
      for (let j = 0; j < nv; j++) { drawOther(g, m.other, mx, my, sc * s0, { stroke: 'rgba(40,30,20,.55)', lw: 2, dash: [6, 4], seed: j * 13, wob: 3 + j * 2, attr: false }); }
      for (let j = 0; j < nv; j++) drawOther(g, m.other, mx, my, sc * s0, { stroke: s1 >= s0 ? 'rgba(239,230,207,.8)' : 'rgba(40,30,20,.6)', lw: 1.5, dash: [3, 6], seed: j * 13 + 5, wob: 3 + j * 2, attr: false });
      g.restore();
      // danger: red tally strokes beneath (what she now thinks the other can do)
      const hm = b0.harm.m + (b1.harm.m - b0.harm.m) * u, nt = Math.round(hm * 10);
      g.strokeStyle = '#a3261a'; g.lineWidth = 3;
      for (let j = 0; j < nt; j++) { const gx = cw * .7 + (j % 5) * 11 + Math.floor(j / 5) * 70, gy = ch * .86; if (j % 5 === 4) { g.beginPath(); g.moveTo(gx - 50, gy + 20); g.lineTo(gx + 4, gy - 2); g.stroke() } else { g.beginPath(); g.moveTo(gx, gy); g.lineTo(gx + 2, gy + 24); g.stroke() } }
    }
    // tally of what is owed (grudge/debt): black strokes on the header, revealed by o.tally (count)
    if (o.tally) {
      g.strokeStyle = '#1c130c'; g.lineWidth = 4;
      for (let j = 0; j < o.tally; j++) { const gx = cw * .07 + (j % 5) * 16 + Math.floor(j / 5) * 100, gy = ch * .025; if (j % 5 === 4) { g.beginPath(); g.moveTo(gx - 72, gy + 26); g.lineTo(gx + 6, gy + 2); g.stroke() } else { g.beginPath(); g.moveTo(gx, gy); g.lineTo(gx + 3, gy + 28); g.stroke() } }
    }
    // the stamp: a red ring pressed on the photograph (grudge), filed for good
    if (o.stamp) {
      const a = o.stamp; g.save(); g.globalAlpha = Math.min(1, a * 1.5); g.translate(px + pw * .74, py + ph * .3); g.rotate(-.25); g.scale(1 + (1 - a) * .6, 1 + (1 - a) * .6);
      g.strokeStyle = '#b3261a'; g.lineWidth = 9; g.beginPath(); g.arc(0, 0, ch * .13, 0, 6.283); g.stroke(); g.lineWidth = 4; g.beginPath(); g.arc(0, 0, ch * .09, 0, 6.283); g.stroke();
      g.lineWidth = 8; g.beginPath(); g.moveTo(-ch * .07, 0); g.lineTo(ch * .07, 0); g.stroke(); g.restore();
    }
    // a hole punched through (grudge cards are punched to be kept on the spike)
    if (feel === 'grudge') { g.fillStyle = '#120c08'; g.beginPath(); g.arc(cw * .5, ch * .065, ch * .028, 0, 6.283); g.fill() }
    // coins: pride/debt, stacked by the card
    if (o.coins) { for (let j = 0; j < o.coins; j++) { g.fillStyle = '#c9a23a'; g.strokeStyle = '#5a4210'; g.lineWidth = 2; g.beginPath(); g.ellipse(px + pw * .5 + (j % 2) * 6, py + ph - 24 - j * 11, 34, 11, 0, 0, 6.283); g.fill(); g.stroke() } }
    if (o.mourn) { g.fillStyle = '#0c0907'; g.beginPath(); g.moveTo(cw * .5, 0); g.lineTo(cw * .66, 0); g.lineTo(cw, ch * .5); g.lineTo(cw, ch * .74); g.closePath(); g.fill() }
    if (o.veil) { g.fillStyle = `rgba(20,14,10,${o.veil})`; g.fillRect(0, 0, cw, ch) }
    g.restore();
  }

  // ---------------- the room ----------------
  function room(g, K, lv, dim, t) {
    const W = 1920, H = 1080, FY = 868;
    g.fillStyle = '#20170f'; g.fillRect(0, 0, W, H);
    // wallpaper: faint ledger columns on the wall (the house as ledger)
    g.strokeStyle = 'rgba(120,90,60,.12)'; g.lineWidth = 2; for (let x = 40; x < W; x += 96) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, FY - 120); g.stroke() }
    g.fillStyle = '#2c2015'; g.fillRect(0, FY - 120, W, 120);
    g.fillStyle = '#3a2a1b'; g.fillRect(0, FY - 124, W, 8);
    g.fillStyle = '#120d09'; g.fillRect(0, FY, W, H - FY);
    // lamp: hangs above her; halo lever = how much light finds her
    const lx = 700, ly = 250, hal = cl(0, 1, .55 + (lv.halo || 0) * .8) * (1 - (dim || 0));
    const rg = g.createRadialGradient(lx, FY - 40, 20, lx, FY - 40, 720);
    rg.addColorStop(0, `rgba(255,214,140,${.38 * hal})`); rg.addColorStop(.5, `rgba(255,190,110,${.12 * hal})`); rg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = rg; g.fillRect(0, 0, W, H);
    g.strokeStyle = '#0c0805'; g.lineWidth = 3; g.beginPath(); g.moveTo(lx, 0); g.lineTo(lx, ly - 40); g.stroke();
    g.fillStyle = '#3b2c1c'; g.beginPath(); g.moveTo(lx - 70, ly); g.lineTo(lx - 22, ly - 46); g.lineTo(lx + 22, ly - 46); g.lineTo(lx + 70, ly); g.closePath(); g.fill();
    g.fillStyle = `rgba(255,226,160,${.4 + .6 * hal})`; g.beginPath(); g.ellipse(lx, ly + 2, 66, 12, 0, 0, 6.283); g.fill();
    return FY;
  }
  function cabinet(g, x, y, w, h, open) {
    // a card catalogue: oak case, 3x4 drawers with brass pulls; the top drawer slot open
    g.fillStyle = '#4a321d'; g.fillRect(x, y, w, h); g.fillStyle = '#5c4026'; g.fillRect(x - 12, y - 18, w + 24, 22);
    g.strokeStyle = '#24170c'; g.lineWidth = 4; g.strokeRect(x, y, w, h);
    const cols = Math.max(3, Math.round(w / 170)), rows = 4;
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const dx = x + 14 + c * (w - 28) / cols, dy = y + 30 + r * (h - 44) / rows, dw = (w - 28) / cols - 12, dh = (h - 44) / rows - 14;
      g.fillStyle = '#5a3e24'; g.fillRect(dx, dy, dw, dh); g.strokeStyle = '#2b1b0e'; g.lineWidth = 3; g.strokeRect(dx, dy, dw, dh);
      g.fillStyle = '#b8913e'; g.fillRect(dx + dw / 2 - 18, dy + dh / 2 - 5, 36, 10);
      g.fillStyle = '#d9cfb3'; g.fillRect(dx + dw / 2 - 20, dy + 10, 40, 16);
    }
    // the slot on top where cards rise
    g.fillStyle = '#0d0805'; g.fillRect(x + 40, y - 12, w - 80, 10 + open * 8);
  }

  function lvOf(st, who) { return (st && st.levers && st.levers[who]) || LV0 }

  // ---------------- beat: the widow alone with her card file ----------------
  function beat(g, t, mems, st, K, X) {
    const lv = lvOf(st, 'R'), dead = st && st.alive && st.alive.R === false;
    const m0 = mems && mems[0], m1 = mems && mems[1], m2 = mems && mems[2];
    const fl = dead ? { f: 'dead', amt: 0 } : feelOf(m0, st), feel = fl.f;
    const dur = 2.5, sch = schedule(feel, dur, lv, m0 ? m0.weight : 0);
    const step = Math.min(sch.N - 1, Math.floor(t * FPS + 1e-6)), pi = sch.path[step];
    const FY = room(g, K, lv, dead ? .6 : 0, t);
    // cabinet and card geometry
    const CX = 900, CY = 560, CW = 900, CH = FY - CY;
    // the widow's scale: loom grows her, shrink lessens her
    const S = 2.6 * (1 + (lv.loom || 0) * .18 - (lv.shrink || 0) * .22);
    const hx = 500 + (lv.loom || 0) * 60;
    // card timing (seconds), scaled by tempo as the script is
    const k = 1 / (1 + (lv.tempo || 0) * .4);
    const rise = feel === 'guilt' ? sm(.85 * k, 1.15 * k, t) * .55 * (1 - sm(1.35 * k, 1.75, t) * .85) : feel === 'none' ? sm(.6, 1.0, t) * .45 * (1 - sm(2.0, 2.4, t)) : feel === 'dead' ? sm(.5, 1.4, t) : sm(.85 * k, 1.2 * k, t);
    // weight: the stamp shakes the room
    const stampT = 1.38 * k, shake = feel === 'grudge' ? Math.exp(-Math.max(0, t - stampT) * 14) * (t > stampT ? 1 : 0) * (6 + (lv.weight || 0) * 12) : 0;
    g.save(); g.translate(0, shake * Math.sin(t * 90));
    // wall shadow of the widow: the shadow lever lengthens and darkens it
    if (!dead) {
      const sh = lv.shadow || 0, p = LIB[pi];
      g.save(); g.globalAlpha = .22 + sh * .4; g.translate(hx - 30 + p.dx * 168 * S, FY - 4); g.transform(1, 0, .35 + sh * .25, 1, 0, 0); g.scale(1.02 + sh * .2, 1.0 + sh * .7); g.transform(1, 0, -p.lean, 1, 0, 0);
      const { pts } = contour(p, 168 * S, 122 * S); g.fillStyle = '#050302'; path(g, pts); g.fill(); g.restore();
    }
    // the slot clip: cards exist only above the cabinet top
    const slot = () => { g.beginPath(); g.rect(0, 0, 1920, CY - 12); g.clip() };
    // second and third memories: cards standing behind in the file (the backlog), coloured by feeling
    const backs = dead ? [] : [m1, m2].filter(Boolean);
    backs.forEach((mb, j) => {
      const fb = feelOf(mb, st), up = (.3 + .55 * sm(1.6 + j * .25, 2.1 + j * .25, t)) * (fb.f === 'guilt' ? .45 : 1);
      const bw = 300, bh = 220, bx = 1420 + j * 110, by = CY - 14 - bh * up;
      g.save(); slot(); drawCard(g, bx, by, bw, bh, mb, fb, X, K, { belief: false, veil: .3 + j * .15 }); g.restore();
    });
    cabinet(g, CX, CY, CW, CH, rise);
    // main card, rising from the slot
    let mc = m0, mf = fl;
    if (dead && X && X.ledger && st.deadAt && st.deadAt.R !== undefined) { // the card of her own end, filed by no one
      const e = X.ledger.ev[st.deadAt.R]; mc = { k: e.k, deed: e.deed, A: e.A, V: e.V, role: 'victim', other: e.A, ago: st.k - 1 - e.k, weight: 1, still: X.still(e) }; mf = { f: 'dead', amt: 1 };
    }
    if (mc && rise > 0.002 && (m0 || dead)) {
      const cw = 740, ch = 480, cx = 940, cy = CY - 14 - ch * rise;
      g.save(); slot();
      const tr = feel === 'fear' ? (hs(step * 3.7) - .5) * 12 * fl.amt : 0;
      const owed = Math.round(cl(0, 15, ((fl.all && (fl.all.grudge || 0) + (fl.all.debt || 0)) || .5) * 8));
      const tally = (feel === 'grudge' || feel === 'debt' || feel === 'pride') ? Math.min(owed, Math.max(0, Math.floor((t - 1.6 * k) * FPS / 1.2))) : 0;
      const coins = (feel === 'pride' || feel === 'debt' || (st.body && st.body.R && st.body.R.includes('coins'))) ? Math.min(6, Math.max(0, Math.floor((t - 1.3 * k) * 6))) : 0;
      drawCard(g, cx + tr, cy, cw, ch, mc, mf, X, K, { grow: sm(1.25 * k, 1.9, t), tally, stamp: feel === 'grudge' && t > stampT ? Math.min(1, (t - stampT) * 5) : 0, coins, veil: feel === 'guilt' ? .25 : 0, belief: !dead, mourn: dead, st });
      g.restore();
    }
    if (feel === 'none' && rise > .002) { // a blank card: nothing owed, nothing filed
      g.save(); slot(); drawCard(g, CX + 60, CY - 14 - 300 * rise, 420, 300, null, { f: 'none' }, X, K, {}); g.restore();
    }
    // the widow (or, dead, her shawl left folded on the floor where she sat)
    if (!dead) {
      const rock = (LIB[pi].id === 'COUNT' || LIB[pi].id === 'IDLE') ? Math.sin(step * 1.1) * 5 : 0; // she rocks on held drawings
      drawWidow(g, pi, hx + rock, FY, S, { grey: lv.grey || 0, lamp: 1, body: (st.body && st.body.R) || [] });
    } else {
      g.fillStyle = '#6e3a33'; g.beginPath(); g.moveTo(hx - 200, FY); g.lineTo(hx - 150, FY - 46); g.lineTo(hx + 150, FY - 52); g.lineTo(hx + 210, FY); g.closePath(); g.fill();
      g.strokeStyle = '#3d1d19'; g.lineWidth = 3; g.beginPath(); g.moveTo(hx - 150, FY - 30); g.lineTo(hx + 160, FY - 34); g.stroke();
      g.beginPath(); for (let i = 0; i < 24; i++) { g.moveTo(hx - 195 + i * 17, FY); g.lineTo(hx - 193 + i * 17, FY + 16) } g.stroke();
    }
    g.restore();
    // the ledger page at her feet: the decoded path (rows = drawings, columns = steps)
    ledgerPage(g, sch, step, 40, 900, 600, 160, lv);
  }

  function ledgerPage(g, sch, step, x, y, w, h, lv) {
    g.save(); g.translate(x, y); g.transform(1, 0, -.18, 1, 0, 0);
    g.fillStyle = '#d9ccaa'; g.fillRect(0, 0, w, h); g.strokeStyle = '#5b4a33'; g.lineWidth = 2; g.strokeRect(0, 0, w, h);
    const rows = LIB.length, cols = sch.N, rh = (h - 16) / rows, cwid = (w - 60) / cols;
    g.strokeStyle = 'rgba(70,110,170,.35)'; g.lineWidth = 1;
    for (let r = 0; r <= rows; r++) { g.beginPath(); g.moveTo(54, 8 + r * rh); g.lineTo(w - 4, 8 + r * rh); g.stroke() }
    g.strokeStyle = 'rgba(190,60,50,.6)'; g.beginPath(); g.moveTo(54, 4); g.lineTo(54, h - 4); g.stroke();
    // thumbnails of the ten drawings at the row heads
    for (let r = 0; r < rows; r++) { drawWidow(g, r, 26, 8 + (r + 1) * rh - 1, .065, { ink: '#2a1c10' }) }
    // protected keys: red boxes
    g.strokeStyle = '#b3261a'; g.lineWidth = 2;
    for (const i in sch.keys) { g.strokeRect(58 + i * cwid, 8 + sch.keys[i] * rh, cwid, rh) }
    // the path, inked up to now
    g.strokeStyle = '#1c130c'; g.lineWidth = 3; g.beginPath();
    for (let i = 0; i <= step; i++) { const px = 58 + (i + .5) * cwid, py = 8 + (sch.path[i] + .5) * rh; if (i === 0) g.moveTo(px, py); else g.lineTo(px, py) } g.stroke();
    g.fillStyle = '#b3261a'; g.beginPath(); g.arc(58 + (step + .5) * cwid, 8 + (sch.path[step] + .5) * rh, 5, 0, 6.283); g.fill();
    g.restore();
  }

  // ---------------- flash: a card surfaces above her when she meets someone again ----------------
  function flash(g, t, mark, mems, K, X) {
    const st = X && X.state, lv = lvOf(st, 'R');
    const m0 = mems && mems[0];
    if (st && st.alive && st.alive.R === false && !(st.impossible || []).length) { /* dead and not acting: no flash */ }
    const fl = feelOf(m0, st), feel = fl.f;
    const W = 1920, H = 1080;
    const cw = cl(420, 600, Math.max(mark.w * 2, 440)) * (.85 + .3 * (m0 ? m0.weight : .3)), ch = cw * .66;
    // timing: grudge cards stay up and are stamped; guilt cards barely rise and are pushed back
    const up = feel === 'guilt' ? sm(0, .25, t) * .5 * (1 - sm(.55, .85, t)) : feel === 'none' ? sm(0, .3, t) * .4 * (1 - sm(.7, 1.0, t)) : sm(0, .28, t) * (1 - (feel === 'grudge' ? 0 : sm(1.1, 1.42, t)));
    if (up <= .002) return;
    // card anchored on her top edge: the slot is drawn as a thin maroon line on her shawl
    const sx = mark.x + mark.w / 2;
    let cx = cl(20, W - cw - 20, sx - cw / 2), cy = mark.y - 30 - ch;
    if (cy < 40) cy = cl(40, H - ch - 40, mark.y - ch / 2), cx = sx < W / 2 ? cl(20, W - cw - 20, mark.x + mark.w + 40) : cl(20, W - cw - 20, mark.x - cw - 40);
    // her shadow on the frame grows with the shadow lever (the house reads her as miser/predator)
    if (lv.shadow > .05) { g.save(); g.globalAlpha = Math.min(.5, lv.shadow * .5) * up; g.fillStyle = '#000'; g.beginPath(); g.ellipse(sx - mark.w * .4, mark.y + mark.h * .95, mark.w * (.8 + lv.shadow), mark.h * .12, 0, 0, 6.283); g.fill(); g.restore() }
    // ledger rules across her: the sack is being looked up
    g.save(); g.globalAlpha = .55 * up; g.strokeStyle = FEEL_COL[feel]; g.lineWidth = 3;
    g.strokeRect(mark.x - 8, mark.y - 8, mark.w + 16, mark.h + 16);
    g.beginPath(); g.moveTo(sx, mark.y - 8); g.lineTo(sx, cy + ch); g.stroke(); g.restore();
    // the card slides out of her (and back into her): clipped at the top of her box when it sits above her
    const yy = cy + ch * (1 - up), above = cy + ch <= mark.y + 2;
    // grudge: at the end the card is not filed back but pinned, shrunk onto a spike above her, kept
    const k2 = feel === 'grudge' ? sm(1.12, 1.42, t) : 0, P0 = [cx + cw / 2, yy], P1 = [cl(60, W - 60, mark.x + mark.w * .85), Math.max(40, mark.y - 30)];
    g.save();
    if (k2 > 0) { g.translate(P0[0] + (P1[0] - P0[0]) * k2, P0[1] + (P1[1] - P0[1]) * k2); g.scale(1 - .72 * k2, 1 - .72 * k2); g.translate(-P0[0], -P0[1]); g.globalAlpha = 1 - sm(1.44, 1.5, t) }
    else { g.beginPath(); g.rect(0, 0, W, above ? cy + ch : H); g.clip(); if (!above) g.globalAlpha = cl(0, 1, up * 1.6) }
    // the backlog: edges of the next cards behind, coloured by their feeling
    const backs = [mems[1], mems[2]].filter(Boolean);
    backs.forEach((mb, j) => { const fb = feelOf(mb, st); g.save(); g.translate(cx + (j + 1) * 22, yy - (j + 1) * 16); g.fillStyle = '#e4dac0'; g.fillRect(0, 0, cw, ch); g.strokeStyle = FEEL_COL[fb.f]; g.lineWidth = 5; g.strokeRect(0, 0, cw, ch); g.restore() });
    const tr = feel === 'fear' ? (hs(Math.floor(t * 12) * 3.7) - .5) * 12 : 0;
    const owed = Math.round(cl(0, 10, ((fl.all && (fl.all.grudge || 0) + (fl.all.debt || 0)) || .4) * 6));
    drawCard(g, cx + tr, yy, cw, ch, m0, fl, X, K, {
      grow: sm(.35, .9, t), tally: (feel === 'grudge' || feel === 'debt' || feel === 'pride') ? Math.min(owed, Math.max(0, Math.floor((t - .45) * 14))) : 0,
      stamp: feel === 'grudge' && t > .7 ? Math.min(1, (t - .7) * 5) : 0, coins: (feel === 'pride' || feel === 'debt') ? Math.min(5, Math.max(0, Math.floor((t - .4) * 8))) : 0,
      veil: feel === 'guilt' ? .3 : 0, belief: !!m0, st
    });
    // grudge: a spike pins the card in place for good
    if (feel === 'grudge' && t > .7) { g.fillStyle = '#2a2a2a'; g.fillRect(cx + cw / 2 - 3, yy - 40, 6, 60); g.beginPath(); g.arc(cx + cw / 2, yy - 40, 9, 0, 6.283); g.fill() }
    g.restore();
  }

  // ---------------- sound: card file, stamp, tallies; the remembered shot muffled behind the drawer ----------------
  function sound(ac, out, t0, kind, mems, K) {
    const S = K.SND, m0 = mems && mems[0];
    const o2 = ac.createGain(); o2.gain.value = 3.2; o2.connect(out); out = o2;
    const HARD = { knifing: 1, incitement: 1, strangling: 1, assault: 1 };
    const feel = !m0 ? 'none' : m0.role === 'witness' ? 'witness' : m0.deed === 'seduction' ? 'desire' : m0.role === 'doer' ? (HARD[m0.deed] ? 'guilt' : 'pride') : (m0.deed === 'gun' ? 'fear' : 'grudge');
    const isB = kind === 'beat', reveal = isB ? 1.0 : .25, pan = isB ? .1 : 0;
    // drawer slide + card flick
    S.cloud(ac, out, t0 + (isB ? .7 : 0), .3, 90, { bp: 900, q: 2, a: .05, d: [.01, .03] }, u => Math.sin(Math.PI * u));
    S.grain(ac, out, t0 + reveal, { bp: 3200, q: 3, d: .03, a: .25, pan });
    S.say(ac, out, 'R', t0 + .05, 'breathe', .8, pan);
    if (!m0) { for (let i = 0; i < 4; i++) S.say(ac, out, 'R', t0 + .5 + i * .45, 'tick', .5, pan); return }
    // the remembered shot returns, muffled through the drawer: the deed's own soundtrack is scheduled so its
    // contact lands on the card's reveal, low-passed, and gated open only while the card is up
    try {
      const D = window.DEEDS && DEEDS[m0.deed], op = t0 + reveal, dt0 = op - (D ? D.contact : 0);
      if (D && D.sound && dt0 >= 0) {
        const len = (isB ? 1.2 : .9) * (feel === 'guilt' ? .5 : 1);
        const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = m0.role === 'victim' ? 900 : 500;
        const gg = ac.createGain(); gg.gain.setValueAtTime(0, Math.max(0, dt0)); gg.gain.setValueAtTime(0, op);
        gg.gain.linearRampToValueAtTime(.8 * (m0.weight || .4), op + .08); gg.gain.linearRampToValueAtTime(0, op + len);
        lp.connect(gg); gg.connect(out); D.sound(ac, lp, dt0, m0.A, m0.V, K);
      }
    } catch (e) { }
    if (feel === 'grudge') {
      const st = t0 + (isB ? 1.38 : .7); S.say(ac, out, 'R', st, 'land', 1, pan); S.thump(ac, out, st, .8, 70, pan);
      for (let i = 0; i < 6; i++) S.say(ac, out, 'R', st + .25 + i * .1, 'tick', .8, pan);
    } else if (feel === 'guilt') { S.cloud(ac, out, t0 + reveal + .3, .4, 60, { bp: 1400, a: .04, d: [.01, .04] }, u => 1 - u); S.say(ac, out, 'R', t0 + reveal + .4, 'sink', .6, pan) }
    else if (feel === 'pride') { for (let i = 0; i < 5; i++) S.grain(ac, out, t0 + reveal + .3 + i * .12, { f: 2400 + i * 140, d: .05, a: .1, pan }) }
    else if (feel === 'fear') { S.say(ac, out, 'R', t0 + reveal + .1, 'react', 1, pan); for (let i = 0; i < 10; i++) S.grain(ac, out, t0 + reveal + .3 + i * .083, { bp: 3000, q: 4, d: .02, a: .08, pan }) } // the card rattles
    else if (feel === 'desire') S.pluck(ac, out, t0 + reveal + .1, 64, .25, 1, pan);
    else S.say(ac, out, 'R', t0 + reveal + .1, 'react', .6, pan);
  }

  // numeric invariants: min hold respected and protected keys on the path
  function _test() {
    const out = [];
    for (const f of ['grudge', 'fear', 'guilt', 'desire', 'pride', 'debt', 'witness', 'none'])
      for (const lv of [LV0, { weight: 1, tempo: 0 }, { weight: 0, tempo: 1 }]) {
        const s = schedule(f, 2.5, lv, .8); let run = 1, ok = true;
        for (let i = 1; i < s.N; i++) { if (s.path[i] === s.path[i - 1]) run++; else { if (run < s.hmin) ok = false; run = 1 } }
        let keys = true; for (const i in s.keys) if (s.path[i] !== s.keys[i]) keys = false;
        out.push({ f, hmin: s.hmin, holds: ok, keys, path: s.path.map(p => LIB[p].id[0] + LIB[p].id[1]).join(' ') });
      }
    return out;
  }

  MEMORY({
    who: 'R', scion: 38, lineage: 'Dynamic Pose Selection — Drawing Library Swarm',
    op: 'A Viterbi decoder chooses one of ten fixed drawings of the widow per 1/12 s to act out the card she pulls from her file, with protected key poses and minimum holds.',
    made: 'The widow is a library of ten pencil drawings (fixed lines, maroon shawl band), never in-betweened; her memories are index cards in an oak card catalogue, each holding a cropped, re-filtered still of the remembered shot. The card margin carries her estimate of the other as a pencil outline (before) and an inked silhouette (after), with red tally strokes for danger.',
    moved: 'A target action script built from the ledger (which card, whether she did it or suffered it, grudge/fear/guilt/desire/pride, its weight) is decoded by dynamic programming over a transition matrix with minimum-duration holds; tempo shortens holds, weight lengthens them and shakes the stamp. Cards rise from the slot on a fixed schedule: grudge cards are stamped, punched and counted and never age; guilt cards half-rise blurred and are pushed back.',
    flash, beat, sound, _test, _lib: LIB, _decode: decode
  });
})();
