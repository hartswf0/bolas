// 08 · Rape — CONSEQUENCE BEAT · SCION-TOON-BOOM-HARMONY (swarm 20, Production Rig Foundry)
// Nothing of the act. Only the aftermath: the victim bolts its door, keeps its distance, mends its torn
// side seam with needle and thread held in one ear, and flinches when the doer's shadow crosses the light
// under the door. The doer, in the hallway, returns in guilt, hesitates, or denies, by temperament and ledger.
//
// RIG (Harmony primitives, as code):
//   PALETTES   one palette per sack {cloth, shade, line, attr...}; the ledger's grey lever is a palette swap
//              (colours mixed toward grey in the palette), never a pixel filter.
//   DRAWINGS   substitution libraries per element (ears, bolt, wig, stitch, witness door). An element shows
//              exactly one drawing per exposure; drawings are anchored at stable pivots (ear corners, bolt keeper).
//   X-SHEET    drawings are exposed on twos (12 drawings/s: frame2 = floor(t*12)); pegs and deformers on ones.
//   PEGS       per-sack peg {x, y, s, sx, sy} + parent stage peg; drawings live under pegs.
//   DEFORMER   each sack body is a rest outline bent by a spine curve deformer (lean u^2, squash with volume
//              preservation, side pinch for 'cinched'); the mending ear is a 2-point chain to the needle.
//   NODE NET   the frame is composited by a small DAG (topologically sorted): set -> hallLight -> shadowA ->
//              witness -> victim -> doer -> partition(door, gap light) -> grade.
// Numeric invariant (testable): stitches(t) is non-decreasing in t, and the bolt drawing is 'shut' for all t>=0.5
// whenever the victim is alive.  Artistic test (viewing only): the flinch reads as caused by the shadow.
(function () {
  const W = 1920, H = 1080, FLOOR = 862, S = 1.55;
  const PART = { x0: 884, x1: 948 };            // partition wall (cut), door leaf inside it
  const DOOR = { top: 440, gap: 12, x0: 900, x1: 932 };
  const LAMP = { x: 300, y: 450 };               // hallway sconce: the shadow source
  const WDOOR = { x0: 92, x1: 262, top: 520 };   // a neighbour's door in the hallway back wall
  const CANDLE = { x: 1610, y: 478 };
  const DUR = 3.2;

  // ---------------- small maths
  const mix = (a, b, u) => a + (b - a) * u;
  const hex = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const rgb = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a == null ? 1 : a})`;
  const greyMix = (c, u, dim) => { const l = c[0] * .3 + c[1] * .59 + c[2] * .11; return [mix(c[0], l, u) * dim, mix(c[1], l, u) * dim, mix(c[2], l * 1.02, u) * dim]; };

  // ---------------- PALETTES (palette node: grey lever and darkness are palette operations)
  const BASE = {
    R: { cloth: '#d6bf96', attr: '#6e3a33' }, B: { cloth: '#e8d5ae', attr: '#2a2622' },
    I: { cloth: '#e2cea5', attr: '#8a7656' }, O: { cloth: '#f0e4c8', attr: '#7a3b8f' }
  };
  function palette(id, grey, dim, warm) {
    const b = BASE[id]; const c = hex(b.cloth), a = hex(b.attr);
    const cl = greyMix(c, grey, dim), at = greyMix(a, grey * .45, dim);
    const w = warm || 0;
    const clw = [cl[0] + 40 * w, cl[1] + 24 * w, cl[2] + 4 * w];
    return { cloth: rgb(clw), shade: rgb([clw[0] * .72, clw[1] * .7, clw[2] * .72]), line: rgb([60 * dim, 46 * dim, 34 * dim]),
      attr: rgb(at), attrDark: rgb([at[0] * .7, at[1] * .7, at[2] * .7]), flour: rgb([251 * dim, 247 * dim, 238 * dim]), seam: 'rgba(30,20,14,0.85)' };
  }

  // ---------------- DRAWING SUBSTITUTIONS: ear library (tip offset from the corner anchor, in units of w,h)
  const EAR = {
    up: [.0, -.32], perk: [.10, -.09], flat: [.15, -.01], down: [.15, .07], hang: [.08, .36], drape: [.05, .55]
  };
  const EAR_I = Object.assign({}, EAR, { perk: [.12, .3], flat: [.12, .45], down: [.1, .6], hang: [.09, .7], drape: [.06, .85], up: [.1, -.1] });
  const EAR_O = Object.assign({}, EAR, { up: [.02, -.14], perk: [.03, -.03], flat: [.05, .02] });
  const BOLT = { open: 0, half: .5, shut: 1 };
  const WDR = { shut: 0, crack: .18, open: .55 };
  const WIG = { set: 0, lift: -.13, tilt: -.05 };

  // X-SHEET helper: pick a drawing by exposure on twos
  const f2 = t => Math.floor(t * 12);
  const onTwos = t => f2(t) / 12;

  // ---------------- DEFORMER: rest outline points of a sack, bent by the spine chain
  function deformer(P) { // P: {w,h,lean,sx,sy,pinch}
    return (x, y) => {
      const u = Math.max(0, -y / P.h);
      let xx = x * (1 - (P.pinch || 0) * Math.max(0, u - .7) * 2.2) + P.lean * P.h * u * u;
      return [xx * P.sx, y * P.sy];
    };
  }
  function sackOutline(g, P, earL, earR, D) {
    const w = P.w, h = P.h;
    const pts = (x, y) => D(x, y);
    const cl = [-w * .34, -h * .97], cr = [w * .34, -h * .97];
    const hl = earL[1] > .2, hr = earR[1] > .2; // hanging ears are separate lobe drawings, not outline spikes
    const tipL = hl ? [-w * .5, -h * .88] : [-w * .48 - earL[0] * w, -h * .9 + earL[1] * h], tipR = hr ? [w * .5, -h * .88] : [w * .48 + earR[0] * w, -h * .9 + earR[1] * h];
    g.beginPath();
    let p = pts(-w * .5, 0); g.moveTo(p[0], p[1]);
    p = pts(w * .5, 0); let c = pts(0, h * .02); g.quadraticCurveTo(c[0], c[1], p[0], p[1]);
    c = pts(w * .57, -h * .45); p = pts(w * .47, -h * .86); g.quadraticCurveTo(c[0], c[1], p[0], p[1]);
    p = pts(tipR[0], tipR[1]); g.lineTo(p[0], p[1]);
    p = pts(cr[0], cr[1]); g.lineTo(p[0], p[1]);
    c = pts(0, -h * .9); p = pts(cl[0], cl[1]); g.quadraticCurveTo(c[0], c[1], p[0], p[1]);
    p = pts(tipL[0], tipL[1]); g.lineTo(p[0], p[1]);
    p = pts(-w * .47, -h * .86); g.lineTo(p[0], p[1]);
    c = pts(-w * .57, -h * .45); p = pts(-w * .5, 0); g.quadraticCurveTo(c[0], c[1], p[0], p[1]);
    g.closePath();
  }
  function poly(g, D, arr) { g.beginPath(); arr.forEach((q, i) => { const p = D(q[0], q[1]); i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]); }); g.closePath(); }
  function strip(g, D, w, y0, y1) { const a = []; for (let i = 0; i <= 10; i++) a.push([-w + i * w * .2, y0]); for (let i = 10; i >= 0; i--) a.push([-w + i * w * .2, y1]); poly(g, D, a); }

  // draws one sack under its peg. R = rig state
  function drawSack(g, R, K) {
    const id = R.id, C = K.CAST[id];
    const w = C.w * S * R.s, h = C.h * S * R.s * (R.emptied ? .78 : 1);
    const P = { w, h, lean: R.lean, sx: R.sx, sy: R.sy, pinch: R.cinched ? .35 : 0 };
    const D = deformer(P);
    const pal = R.pal;
    g.save(); g.translate(R.x, R.y); if (R.alpha != null) g.globalAlpha *= R.alpha;
    // halo (light finds it)
    if (R.halo > .05) { const hg = g.createRadialGradient(0, -h * .5, 10, 0, -h * .5, h * 1.1); hg.addColorStop(0, `rgba(255,220,160,${.18 * R.halo})`); hg.addColorStop(1, 'rgba(255,220,160,0)'); g.fillStyle = hg; g.fillRect(-h * 1.2, -h * 1.6, h * 2.4, h * 2); }
    // contact shadow
    g.fillStyle = 'rgba(0,0,0,0.35)'; g.beginPath(); g.ellipse(R.lean * h * .1, 2, w * .58 * R.sx, 9, 0, 0, Math.PI * 2); g.fill();
    const lib = id === 'I' ? EAR_I : id === 'O' ? EAR_O : EAR; const eL = lib[R.earL] || lib.perk, eR = lib[R.earR] || lib.perk;
    sackOutline(g, P, eL, eR, D);
    const gr = g.createLinearGradient(-w * .5, 0, w * .5, 0); gr.addColorStop(0, pal.shade); gr.addColorStop(.45, pal.cloth); gr.addColorStop(1, pal.shade);
    g.fillStyle = gr; g.fill();
    g.save(); g.clip();
    // attribute drawings (pegged to the body, deformed with it)
    if (id === 'R') { g.fillStyle = pal.attr; strip(g, D, w, -h * .79, -h * 1.4); g.fill(); g.strokeStyle = pal.attrDark; g.lineWidth = 3; strip(g, D, w, -h * .79, -h * .8); g.stroke(); }
    if (id === 'B') { g.fillStyle = pal.attr; strip(g, D, w, -h * .37, -h * .44); g.fill();
      if (!R.back) { const c = D(0, -h * .66); g.strokeStyle = pal.line; g.globalAlpha *= .55; g.lineWidth = 3; g.beginPath(); g.arc(c[0], c[1], w * .13, 0, Math.PI * 2); g.stroke();
        g.beginPath(); g.moveTo(c[0], c[1] + w * .1); g.lineTo(c[0], c[1] - w * .1); for (let k = -2; k <= 2; k++) { g.moveTo(c[0], c[1] + k * w * .03); g.lineTo(c[0] - w * .05, c[1] + k * w * .03 - w * .03); g.moveTo(c[0], c[1] + k * w * .03); g.lineTo(c[0] + w * .05, c[1] + k * w * .03 - w * .03); } g.stroke(); g.globalAlpha /= .55; } }
    // carried damage marks
    if (R.rope) { g.strokeStyle = 'rgba(120,90,50,0.9)'; g.lineWidth = 4; [-.3, -.62].forEach(v => { strip(g, D, w, h * v, h * v - 3); g.stroke(); }); }
    if (R.gag) { g.fillStyle = 'rgba(200,190,170,0.9)'; strip(g, D, w, -h * .82, -h * .88); g.fill(); }
    if (R.blot) { const c = D(w * .18, -h * .5); g.fillStyle = 'rgba(20,16,30,0.8)'; g.beginPath(); for (let k = 0; k < 9; k++) { const a = k / 9 * Math.PI * 2, r = w * (.06 + K.hash(k + 3) * .04); g.lineTo(c[0] + Math.cos(a) * r, c[1] + Math.sin(a) * r); } g.fill(); }
    if (R.tag) { const c = D(w * .05, -h * .3); g.fillStyle = 'rgba(230,225,205,0.95)'; g.fillRect(c[0] - 14, c[1] - 9, 28, 18); g.strokeStyle = pal.line; g.lineWidth = 1.5; g.strokeRect(c[0] - 14, c[1] - 9, 28, 18); }
    // the torn side seam and its mending (victim only)
    if (R.torn) drawSeam(g, R, D, w, h, pal, K);
    g.restore();
    sackOutline(g, P, eL, eR, D); g.strokeStyle = pal.line; g.lineWidth = 2.5; g.lineJoin = 'round'; g.stroke();
    // hanging ear lobes (Inigo's long unwashed ears; anyone's ears when they droop that far)
    [[eL, -1], [eR, 1]].forEach(([e, sg]) => { if (e[1] <= .2) return;
      const b0 = D(sg * w * .2, -h * .97), b1 = D(sg * w * .5, -h * .8), tp = D(sg * (w * .52 + e[0] * w), -h * .9 + e[1] * h), cc = D(sg * (w * .72 + e[0] * w), -h * .9 + e[1] * h * .45);
      g.beginPath(); g.moveTo(b0[0], b0[1]); g.quadraticCurveTo(cc[0], cc[1] - h * .1, tp[0], tp[1]); g.quadraticCurveTo(cc[0] - sg * w * .1, cc[1], b1[0], b1[1]); g.closePath();
      g.fillStyle = pal.shade; g.fill(); g.strokeStyle = pal.line; g.lineWidth = 2.5; g.stroke(); });
    // wig: Ogiva's attribute, drawn over the top and hanging past the shoulders (substitution set/lift/tilt)
    if (id === 'O') {
      const lift = (WIG[R.wig] || 0) * h, tilt = R.wig === 'tilt' ? .18 : 0;
      const a = [[-w * .62, -h * .45], [-w * .66, -h * .82], [-w * .5, -h * 1.03], [0, -h * 1.1], [w * .5, -h * 1.03], [w * .66, -h * .82], [w * .62, -h * .45], [w * .44, -h * .5], [w * .4, -h * .86], [0, -h * .93], [-w * .4, -h * .86], [-w * .44, -h * .5]];
      g.fillStyle = pal.attr; poly(g, (x, y) => D(x + tilt * h * (y / h + 1), y + lift), a); g.fill(); g.strokeStyle = pal.attrDark; g.lineWidth = 2; g.stroke();
    }
    if (R.coins) { g.fillStyle = 'rgba(200,170,80,0.9)'; for (let k = 0; k < 3; k++) { g.beginPath(); g.ellipse(-w * .3 + k * 14, -3, 8, 4, 0, 0, Math.PI * 2); g.fill(); } }
    // mending ear: a deformation chain from the top-left corner to the needle (drawn over the body)
    if (R.needle) {
      const base = D(-w * .42, -h * .9), nd = R.needle; const mid = [mix(base[0], nd[0], .5) - w * .28, mix(base[1], nd[1], .45)];
      g.strokeStyle = pal.line; g.fillStyle = pal.cloth; g.lineWidth = 2.5;
      g.beginPath(); g.moveTo(base[0] - 9, base[1] + 4); g.quadraticCurveTo(mid[0] - 10, mid[1], nd[0], nd[1]); g.quadraticCurveTo(mid[0] + 12, mid[1], base[0] + 12, base[1] + 2); g.closePath(); g.fill(); g.stroke();
      // needle (steel) and the thread from its eye to the last stitch
      g.strokeStyle = 'rgba(210,215,225,0.95)'; g.lineWidth = 2; g.beginPath(); g.moveTo(nd[0], nd[1]); g.lineTo(nd[0] + R.needleDir[0] * 22, nd[1] + R.needleDir[1] * 22); g.stroke();
      if (R.threadTo) { g.strokeStyle = R.threadCol; g.lineWidth = 1.3; g.beginPath(); g.moveTo(nd[0], nd[1]); g.quadraticCurveTo((nd[0] + R.threadTo[0]) / 2 - 10, Math.max(nd[1], R.threadTo[1]) + 18, R.threadTo[0], R.threadTo[1]); g.stroke(); }
    }
    g.restore();
    return { w: w * R.sx, h: h * R.sy };
  }

  // seam: a jagged tear along the left side, closed stitch by stitch. Stitch drawing is chosen by temperament.
  function drawSeam(g, R, D, w0, h, pal, K) {
    let w = w0;
    const u0 = .12, u1 = .5, N = R.nStitch;
    const sx = u => -w0 * .5 + w0 * .06 + Math.sin(u * 40) * w0 * .012;
    const open = R.dead ? 1 : 1;
    // the gap (open where not yet stitched)
    g.fillStyle = 'rgba(25,18,12,0.85)';
    const done = R.stitches / N; // fraction from bottom
    g.beginPath(); let first = true;
    for (let i = 0; i <= 16; i++) { const u = u0 + (u1 - u0) * i / 16; const op = (u - u0) / (u1 - u0) < done ? .18 : 1; const p = D(sx(u) + w * .045 * op * open, -h * u); first ? g.moveTo(p[0], p[1]) : g.lineTo(p[0], p[1]); first = false; }
    for (let i = 16; i >= 0; i--) { const u = u0 + (u1 - u0) * i / 16; const op = (u - u0) / (u1 - u0) < done ? .18 : 1; const p = D(sx(u) - w * .02 * op * open - (K.hash(i * 7.3) * w * .03 * op), -h * u); g.lineTo(p[0], p[1]); }
    g.closePath(); g.fill(); g.strokeStyle = pal.flour; g.globalAlpha *= .55; g.lineWidth = 2; g.stroke(); g.globalAlpha /= .55;
    // flour that came out (dots at the lower lip)
    g.fillStyle = pal.flour; for (let k = 0; k < 7; k++) { const p = D(sx(u0 + .03 * k) + (K.hash(k * 3.1) - .5) * w * .06, -h * (u0 - .02 + .04 * K.hash(k))); g.globalAlpha *= .6; g.beginPath(); g.arc(p[0], p[1], 2.2, 0, Math.PI * 2); g.fill(); g.globalAlpha /= .6; }
    // stitches (drawing substitution by the victim's hand)
    g.strokeStyle = R.threadCol; g.lineCap = 'round';
    for (let i = 0; i < R.stitches; i++) {
      const u = u0 + (u1 - u0) * (i + .5) / N, x = sx(u), y = -h * u, st = R.stitchDraw, j = K.hash(i * 11.7 + R.seed) - .5; w = Math.max(w, 300);
      g.lineWidth = st === 'crude' ? 4.5 : st === 'loose' ? 2.6 : 3.2;
      g.beginPath();
      if (st === 'cross') { let a = D(x - w * .05, y - h * .02), b = D(x + w * .05, y + h * .02); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); a = D(x - w * .05, y + h * .02); b = D(x + w * .05, y - h * .02); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); }
      else if (st === 'neat') { const a = D(x - w * .045, y), b = D(x + w * .045, y); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); }
      else if (st === 'crude') { const a = D(x - w * .07, y + h * .03 * j), b = D(x + w * .08, y - h * .04); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); }
      else { const a = D(x - w * .06, y + h * .05 * j), b = D(x + w * .05, y + h * .06 * j), c = D(x, y + h * .05); g.moveTo(a[0], a[1]); g.quadraticCurveTo(c[0], c[1], b[0], b[1]); }
      g.stroke();
    }
  }

  // ---------------- LEDGER READ: everything the beat chooses comes from the state
  function readState(ev, st, K) {
    const A = ev.A, V = ev.V, IDS = ['R', 'B', 'I', 'O'];
    const mAV = (st.mind[A] && st.mind[A][V]) || {}, mVA = (st.mind[V] && st.mind[V][A]) || {};
    const LA = st.levers[A] || {}, LV = st.levers[V] || {};
    const aliveA = st.alive[A], aliveV = st.alive[V];
    const guilt = mAV.guilt || 0;
    const doerMode = !aliveA ? 'ghost' : guilt >= .6 ? 'return' : guilt >= .3 ? 'hesitate' : 'deny';
    const fear = mVA.fear || 0, grudge = mVA.grudge || 0;
    // the distance the victim now keeps: fear and grudge push it into the far corner
    const dist = K.cl(0, 1, fear * .55 + grudge * .3 + (LV.shrink || 0) * .4);
    // witness: a living third sack who knows something of either, or reads as a SPY
    let wit = null, best = 0;
    for (const o of IDS) {
      if (o === A || o === V || !st.alive[o]) continue;
      let sc = 0; for (const k of st.know[o]) { const e = st.evidence[k]; if (e && (e.A === A || e.V === A || e.A === V || e.V === V)) sc += 1; }
      sc += ((st.myth[o] && st.myth[o].SPY) || 0) * 3;
      if (sc > best + 1e-6) { best = sc; wit = o; }
    }
    let witMode = 'none', witId = null;
    if (wit) {
      const fA = ((st.mind[wit][A] || {}).fear || 0) + (((st.belief[wit] || {})[A] || {}).harm || { m: 0 }).m * .6;
      witMode = fA > .45 ? 'turn' : 'watch'; witId = wit;
    } else { witId = IDS.find(o => o !== A && o !== V && st.alive[o]) || null; }
    const tagsV = st.body[V] || [], tagsA = st.body[A] || [];
    return { A, V, guilt, doerMode, fear, grudge, dist, wit: witId, witMode, LA, LV, aliveA, aliveV, tagsV, tagsA, impossible: !aliveV || !aliveA };
  }

  // stitch hand per victim temperament (drawing substitution set)
  const HAND = { R: { draw: 'cross', N: 8, rate: 1.0, thread: 'rgba(236,150,128,0.95)' }, B: { draw: 'crude', N: 5, rate: .8, thread: 'rgba(250,244,226,0.95)' },
    I: { draw: 'loose', N: 6, rate: .7, thread: 'rgba(240,226,180,0.95)' }, O: { draw: 'neat', N: 9, rate: 1.3, thread: 'rgba(222,170,245,0.95)' } };

  // ---------------- DOER performance: peg x over time per mode (pure function)
  function doerPeg(t, s, K) {
    const tempo = 1 + (s.LA.tempo || 0) * .4;
    const tt = t * tempo;
    const id = s.A, C = K.CAST[id];
    const half = C.w * S * .5;
    let x, earL = 'perk', earR = 'perk', lean = 0, bob = 0, sy = 1, back = false, wig = 'set', alpha = 1, sit = 0;
    const weight = 1 + (s.LA.weight || 0) * 1.2;
    if (s.doerMode === 'return') {
      const go = K.sm(.4, 1.9, tt);
      x = mix(470, PART.x0 - half - 6, go);
      bob = Math.abs(Math.sin(tt * 7)) * 6 * weight * (go > 0 && go < 1 ? 1 : 0);
      lean = .12 * go;
      // raises an ear to knock, cannot, lets it fall; then sits down against the door
      const knock = K.sm(1.95, 2.1, tt) * (1 - K.sm(2.35, 2.5, tt));
      earR = knock > .5 ? 'up' : knock > .1 ? 'perk' : (tt > 2.45 ? 'down' : 'perk');
      sit = K.sm(2.5, 2.95, tt); sy = 1 - .16 * sit; lean = mix(lean, .2, sit); earL = tt > 2.45 ? 'down' : 'perk';
      if (id === 'I') { earL = 'drape'; earR = knock > .5 ? 'perk' : 'drape'; }
    } else if (s.doerMode === 'hesitate') {
      const go = K.sm(.5, 1.75, tt), away = K.sm(2.2, 3.1, tt);
      x = mix(mix(480, 760, go), 470, away);
      bob = Math.abs(Math.sin(tt * 6)) * 5 * weight * ((go > 0 && go < 1) || (away > 0 && away < 1) ? 1 : 0);
      lean = .1 * go - .14 * away;
      const look = K.sm(1.7, 1.8, tt) * (1 - K.sm(2.1, 2.2, tt));
      earR = look > .5 ? 'up' : 'perk'; earL = look > .5 ? 'perk' : 'flat';
      if (id === 'I') { earL = look > .5 ? 'hang' : 'drape'; earR = look > .5 ? 'perk' : 'drape'; lean += Math.sin(tt * 3) * .05; }
    } else if (s.doerMode === 'deny') {
      const away = K.sm(2.2, 3.1, tt);
      x = mix(600, 440, away);
      bob = Math.abs(Math.sin(tt * 6)) * 5 * weight * (away > 0 && away < 1 ? 1 : 0);
      lean = -.1 * away;
      // preening: Ogiva resets her wig, Roessler straightens and rocks, others shake out their ears
      const fr = f2(tt);
      if (id === 'O') { wig = tt < 2.1 ? ['set', 'lift', 'lift', 'tilt', 'set', 'set'][fr % 6] : 'set'; earL = earR = 'up'; lean += -.04; }
      else if (id === 'R') { lean += Math.sin(tt * 4) * .06 * (1 - away); earL = earR = (tt < 1.6 && fr % 4 < 2) ? 'flat' : 'perk'; }
      else if (id === 'B') { earL = earR = fr % 6 < 3 ? 'perk' : 'flat'; }
      else { earL = earR = fr % 6 < 3 ? 'drape' : 'hang'; lean += Math.sin(tt * 3) * .06; }
      back = away > .3;
    } else { // ghost: the doer is already dead in this film; it drifts, casts no shadow
      x = mix(560, 640, K.sm(0, DUR, tt)); alpha = .38; earL = earR = id === 'I' ? 'drape' : 'down'; lean = Math.sin(tt * 2) * .04;
    }
    if (id === 'I' && s.doerMode !== 'ghost') { if (earL === 'perk' || earL === 'flat') earL = 'hang'; if (earR === 'flat') earR = 'hang'; }
    if (s.tagsA.includes('drowsy')) lean += Math.sin(t * 2.2) * .05;
    const loom = s.LA.loom || 0;
    return { id, x, y: FLOOR - bob, s: 1 + K.cl(-.15, .35, loom) * .25, sx: 1 / Math.sqrt(sy), sy, lean: lean + loom * .05, earL, earR, back, wig, alpha };
  }
  function shadowTip(t, s, K) {
    if (s.doerMode === 'ghost') return 0;
    const P = doerPeg(t, s, K);
    let k = .38 * (1 + 1.6 * (s.LA.shadow || 0)) * P.s;
    if (s.doerMode === 'deny') k *= mix(1, 1.9, K.sm(1.0, 2.0, t)) * (1 - .25 * K.sm(2.2, 2.9, t)); // the PREDATOR's shadow grows while it preens
    if (s.doerMode === 'return') k *= 1 - .3 * K.sm(2.5, 2.95, t);  // sitting: the shadow settles but stays under the door
    return P.x + Math.max(0, P.x - LAMP.x) * k;
  }
  function flinchTime(s, K) { // first exposure (on ones, 24 fps) where the doer's shadow crosses the light under the door
    if (!s.aliveV || s.doerMode === 'ghost') return null;
    const base = Math.max(PART.x0 + 4, shadowTip(1.25, s, K) + 50); // the shadow must ADVANCE under the door once she has sat down
    for (let f = 30; f < DUR * 24; f++) { const t = f / 24; if (shadowTip(t, s, K) > base) return t; }
    return null;
  }

  // ---------------- VICTIM performance
  function victimPeg(t, s, K, tf) {
    const id = s.V, C = K.CAST[id], half = C.w * S * .5 * (1 - (s.LV.shrink || 0) * .25);
    const shrink = s.LV.shrink || 0, fear = s.fear;
    const far = mix(1320, 1840 - half, s.dist);
    const R = { id, s: 1 - shrink * .22, sy: 1, sx: 1, lean: 0, earL: 'perk', earR: 'perk', torn: true, seed: 3, needle: null };
    if (!s.aliveV) { // already dead in this film: the still sack, the needle and spool untouched beside it
      Object.assign(R, { x: 1640, y: FLOOR, sy: .62, sx: 1.25, lean: .25, earL: 'down', earR: 'down', stitches: 0, nStitch: 6, stitchDraw: 'loose', threadCol: '#999', dead: true });
      if (id === 'I') R.earL = R.earR = 'drape';
      return R;
    }
    const hand = HAND[id];
    // 0..0.5 bolt the door; 0.5..1.05 back away into the far corner; then sit and mend
    const back = K.sm(.5, 1.05, t);
    let x = mix(PART.x1 + half + 18, far, back);
    let fl = 0; if (tf != null) fl = Math.exp(-Math.max(0, t - tf) * 3.2) * (t >= tf ? 1 : 0);
    const recoil = tf != null && t >= tf ? K.sm(tf, tf + .2, t) * (30 + 50 * fear) : 0;
    x = Math.min(1850 - half, x + recoil);
    const sit = K.sm(.9, 1.2, t);
    R.x = x + Math.sin(t * 60) * 4 * fl; R.y = FLOOR - 22 * fl * Math.min(1, (t - (tf || 0)) * 8);
    R.sy = (1 - .14 * sit) * (1 + .08 * fl) * (1 - shrink * .08) * (id === 'I' ? .9 : 1); R.sx = 1 / Math.sqrt(R.sy);
    R.lean = (.14 * sit + .12 * fl) * Math.min(1, 1.3 * C.w / C.h);   // turned toward the wall, away from the door
    // ears: drawing substitutions on twos; up like hands at the flinch, then held low
    const tt = onTwos(t);
    let ears = t < .5 ? 'perk' : fl > .55 ? 'up' : fl > .2 ? 'perk' : (shrink > .2 || fear > .7 ? 'down' : 'flat');
    if (id === 'I') ears = fl > .55 ? 'perk' : 'drape';
    R.earL = R.earR = ears;
    R.wig = fl > .4 ? 'lift' : 'set';
    // bolt: the near ear pushes it shut
    if (t < .55) R.earL = t < .3 ? 'perk' : 'flat';
    // stitching progress (stops during the flinch window, then resumes)
    const rate = hand.rate * (1 - fear * .35);
    let work = Math.max(0, tt - 1.15);
    if (tf != null && tt > tf) work -= Math.min(tt, tf + .55 + fear * .4) - tf;
    const N = hand.N, prog = K.cl(0, N, work * rate * 4);
    R.stitches = Math.floor(prog); R.nStitch = N; R.stitchDraw = hand.draw; R.threadCol = hand.thread; R.seed = id.charCodeAt(0);
    // needle: rides the mending ear, in-out cycle per stitch (pegged on ones)
    if (t > 1.1) {
      const C2 = K.CAST[id]; const w = C2.w * S * R.s, h = C2.h * S * R.s;
      const ph = prog - Math.floor(prog), i = Math.min(N - 1, Math.floor(prog));
      const u = .12 + .38 * (i + .5) / N;
      const D = deformer({ w, h, lean: R.lean, sx: R.sx, sy: R.sy });
      const pin = D(-w * .5 + w * .06, -h * u);
      const pull = Math.sin(ph * Math.PI) * (fl > .2 ? 0 : 1);
      R.needle = [pin[0] - 18 - pull * w * .32, pin[1] - pull * h * .18];
      R.needleDir = [-.7, -.7];
      R.threadTo = [pin[0], pin[1]];
      R.earL = 'perk';
    }
    return R;
  }

  // ---------------- WITNESS (the neighbour's door in the hallway back wall)
  function witnessState(t, s) {
    if (!s.wit) return null;
    if (s.witMode === 'none') return { door: 'shut', light: 1 - Math.min(1, Math.max(0, (t - 1.4) / .1)), show: false };
    const fr = f2(t);
    let door = t < .8 ? 'shut' : t < .9 ? 'crack' : 'open';
    if (s.witMode === 'turn' && t > 2.1) door = t < 2.25 ? 'crack' : 'shut';
    return { door, light: 1, show: door !== 'shut', fr };
  }

  // ---------------- NODE NETWORK
  function topo(nodes) { const out = [], seen = {}; const by = {}; nodes.forEach(n => by[n.id] = n);
    const visit = n => { if (seen[n.id]) return; seen[n.id] = 1; (n.in || []).forEach(i => visit(by[i])); out.push(n); }; nodes.forEach(visit); return out; }

  function scene(g, t, ev, st, K) {
    const s = readState(ev, st, K);
    const tf = flinchTime(s, K);
    const Dp = doerPeg(t, s, K), Vp = victimPeg(t, s, K, tf);
    const tip = shadowTip(t, s, K);
    const ws = witnessState(t, s);
    const dimV = s.aliveV ? 1 : .8;
    // palettes (the grey lever is a palette swap; the hallway is warm, the room is cold)
    Dp.pal = palette(s.A, Math.max(s.LA.grey || 0, s.doerMode === 'ghost' ? .9 : 0), .78, .35);
    Vp.pal = palette(s.V, Math.max(s.LV.grey || 0, s.aliveV ? 0 : .85) + (s.tagsV.includes('greyed') ? .5 : 0), .8 * dimV, .12);
    Dp.halo = (s.LA.halo || 0); Vp.halo = (s.LV.halo || 0) * .6;
    for (const tg of s.tagsA) if (['rope', 'gag', 'blot', 'tag', 'coins', 'emptied', 'cinched'].includes(tg)) Dp[tg] = true;
    for (const tg of s.tagsV) if (['rope', 'gag', 'blot', 'tag', 'coins', 'emptied', 'cinched'].includes(tg)) Vp[tg] = true;
    const boltU = s.aliveV ? BOLT[t < .3 ? 'open' : t < .42 ? 'half' : 'shut'] : 0;
    const underDoor = K.cl(0, 1, (tip - PART.x0) / 60); // how much of the light line the shadow takes

    const nodes = [
      { id: 'set', run() {
        // hallway (warm) | partition | room (cold)
        let gr = g.createLinearGradient(0, 0, 0, FLOOR); gr.addColorStop(0, '#2a2119'); gr.addColorStop(1, '#4a3a2a'); g.fillStyle = gr; g.fillRect(0, 0, PART.x0, FLOOR);
        gr = g.createLinearGradient(0, 0, 0, FLOOR); gr.addColorStop(0, '#181c26'); gr.addColorStop(1, '#2e3240'); g.fillStyle = gr; g.fillRect(PART.x1, 0, W - PART.x1, FLOOR);
        g.fillStyle = '#2b2018'; g.fillRect(0, FLOOR, PART.x0, H - FLOOR); g.fillStyle = '#15171d'; g.fillRect(PART.x1, FLOOR, W - PART.x1, H - FLOOR);
        g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 2; for (let y = FLOOR + 40; y < H; y += 46) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
        // wainscot lines
        g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(0, 640, PART.x0, 6); g.fillRect(PART.x1, 640, W - PART.x1, 6);
        // the room's window (moon), the stool and candle
        g.fillStyle = '#0c1018'; g.fillRect(1560, 230, 190, 240); g.fillStyle = 'rgba(120,140,180,0.25)'; g.fillRect(1572, 242, 78, 104); g.fillRect(1660, 242, 78, 104); g.fillRect(1572, 356, 78, 104); g.fillRect(1660, 356, 78, 104);
        g.fillStyle = '#20180f'; g.fillRect(1545, 470, 220, 16); // the sill the candle stands on
        // neighbour's door in the hall back wall
        g.fillStyle = '#1a130d'; g.fillRect(WDOOR.x0 - 10, WDOOR.top - 10, WDOOR.x1 - WDOOR.x0 + 20, FLOOR - WDOOR.top + 10);
      } },
      { id: 'hallLight', in: ['set'], run() {
        const hg = g.createRadialGradient(LAMP.x, LAMP.y, 6, LAMP.x, LAMP.y, 620); hg.addColorStop(0, 'rgba(255,200,120,0.42)'); hg.addColorStop(1, 'rgba(255,200,120,0)'); g.fillStyle = hg; g.fillRect(0, 0, PART.x0, H);
        g.fillStyle = '#c9a46a'; g.fillRect(LAMP.x - 5, LAMP.y + 6, 10, 26); g.fillStyle = '#fff1c8'; g.beginPath(); g.ellipse(LAMP.x, LAMP.y - 4, 7, 13, 0, 0, Math.PI * 2); g.fill();
        // candle in the room
        const c = g.createRadialGradient(CANDLE.x, CANDLE.y - 30, 4, CANDLE.x, CANDLE.y - 30, 520); c.addColorStop(0, 'rgba(255,190,110,0.3)'); c.addColorStop(1, 'rgba(255,190,110,0)'); g.fillStyle = c; g.fillRect(PART.x1, 0, W - PART.x1, H);
        g.fillStyle = '#e8dcc0'; g.fillRect(CANDLE.x - 5, CANDLE.y - 22, 10, 30); const fl = 1 + Math.sin(t * 23) * .08; g.fillStyle = '#ffd890'; g.beginPath(); g.ellipse(CANDLE.x, CANDLE.y - 32, 4, 9 * fl, 0, 0, Math.PI * 2); g.fill();
        // the light under the door: a line and a fan on the room floor, cut by the doer's shadow
        const lit = 1 - underDoor * .92;
        const fan = g.createLinearGradient(PART.x1, 0, PART.x1 + 420, 0); fan.addColorStop(0, `rgba(255,200,120,${.5 * lit})`); fan.addColorStop(1, 'rgba(255,200,120,0)');
        g.fillStyle = fan; g.beginPath(); g.moveTo(PART.x1, FLOOR - 2); g.lineTo(PART.x1 + 440, FLOOR + 70); g.lineTo(PART.x1 + 440, FLOOR + 200); g.lineTo(PART.x1, FLOOR + 10); g.closePath(); g.fill();
        if (underDoor > 0) { // the shadow itself, entering the room as a dark tongue
          const L = Math.min(500, tip - PART.x0); g.fillStyle = 'rgba(0,0,0,0.55)'; g.beginPath(); g.moveTo(PART.x1, FLOOR + 2); g.lineTo(PART.x1 + L, FLOOR + 30 + L * .12); g.lineTo(PART.x1 + L * .9, FLOOR + 60 + L * .2); g.lineTo(PART.x1, FLOOR + 10); g.closePath(); g.fill(); }
      } },
      { id: 'shadowA', in: ['hallLight'], run() {
        if (s.doerMode === 'ghost') return;
        const C = K.CAST[s.A]; const w = C.w * S * Dp.s, hh = C.h * S * Dp.s;
        const L = Math.min(tip, PART.x0) - Dp.x;
        const dk = .45 + .4 * K.cl(0, 1, s.LA.shadow || 0);
        g.fillStyle = `rgba(0,0,0,${dk})`; g.beginPath(); g.moveTo(Dp.x - w * .4, FLOOR + 6); g.lineTo(Dp.x + w * .4, FLOOR - 2); g.lineTo(Dp.x + L, FLOOR + 6 + L * .06); g.lineTo(Dp.x + L * .92, FLOOR + 22 + L * .1); g.closePath(); g.fill();
      } },
      { id: 'witness', in: ['shadowA'], run() {
        if (!ws) return;
        const op = WDR[ws.door];
        // the light behind the neighbour's door
        g.fillStyle = `rgba(255,196,120,${.85 * ws.light * (op > 0 ? 1 : 0)})`; g.fillRect(WDOOR.x0, WDOOR.top, (WDOOR.x1 - WDOOR.x0) * op * 1.6, FLOOR - WDOOR.top);
        if (ws.show) {
          const C = K.CAST[s.wit]; const ww = palette(s.wit, (st.levers[s.wit] || {}).grey || 0, .55, .1);
          g.save(); g.beginPath(); g.rect(WDOOR.x0, WDOOR.top, (WDOOR.x1 - WDOOR.x0) * op * 1.6, FLOOR - WDOOR.top); g.clip();
          drawSack(g, { id: s.wit, x: WDOOR.x0 + 62, y: FLOOR, s: .62, sx: 1, sy: 1, lean: s.witMode === 'turn' && t > 1.9 ? -.12 : .06, earL: s.wit === 'I' ? 'drape' : 'perk', earR: s.wit === 'I' ? 'drape' : (t > 1.2 && t < 1.9 ? 'up' : 'perk'), pal: ww, halo: 0, wig: 'set' }, K);
          g.restore();
        }
        // door leaf (drawing substitution shut/crack/open: the leaf narrows as it swings in)
        const lw = (WDOOR.x1 - WDOOR.x0) * (1 - op);
        g.fillStyle = '#3e2c1d'; g.fillRect(WDOOR.x1 - lw, WDOOR.top, lw, FLOOR - WDOOR.top);
        g.strokeStyle = 'rgba(0,0,0,0.4)'; g.lineWidth = 3; if (lw > 30) { g.strokeRect(WDOOR.x1 - lw + 14, WDOOR.top + 20, lw - 28, 120); g.strokeRect(WDOOR.x1 - lw + 14, WDOOR.top + 170, lw - 28, 140); }
        if (ws.door === 'shut' && ws.light > 0) { g.fillStyle = `rgba(255,196,120,${.9 * ws.light})`; g.fillRect(WDOOR.x0, FLOOR - 7, WDOOR.x1 - WDOOR.x0, 7); const lg = g.createLinearGradient(0, FLOOR, 0, FLOOR + 60); lg.addColorStop(0, `rgba(255,196,120,${.35 * ws.light})`); lg.addColorStop(1, 'rgba(255,196,120,0)'); g.fillStyle = lg; g.fillRect(WDOOR.x0 - 30, FLOOR, WDOOR.x1 - WDOOR.x0 + 60, 60); }
      } },
      { id: 'victim', in: ['witness'], run() {
        g.beginPath(); g.rect(PART.x1, 0, W - PART.x1, H); g.clip();
        if (s.aliveV || true) { // flour that ran out of the seam: a small white heap on the floor under it
          const C = K.CAST[s.V], w = C.w * S * Vp.s; const fx = Vp.x - w * .5 - 6; g.fillStyle = 'rgba(251,247,238,0.75)'; g.beginPath(); g.ellipse(fx, FLOOR + 2, 26, 7, 0, Math.PI, 0); g.fill(); for (let k = 0; k < 9; k++) { g.beginPath(); g.arc(fx - 30 + K.hash(k * 5.1) * 60, FLOOR + 4 + K.hash(k * 2.3) * 10, 2, 0, Math.PI * 2); g.fill(); } }
        drawSack(g, Vp, K);
        if (!s.aliveV) { // needle and spool, untouched
          g.fillStyle = '#6b5a44'; g.fillRect(1250, FLOOR - 22, 26, 22); g.fillStyle = HAND[s.V].thread; g.fillRect(1250, FLOOR - 18, 26, 14);
          g.strokeStyle = 'rgba(210,215,225,0.9)'; g.lineWidth = 2; g.beginPath(); g.moveTo(1290, FLOOR - 3); g.lineTo(1320, FLOOR - 6); g.stroke();
        } else { // spool on the floor beside the victim, its thread running up to the work
          g.fillStyle = '#6b5a44'; g.fillRect(Vp.x - 150, FLOOR - 22, 26, 22); g.fillStyle = HAND[s.V].thread; g.fillRect(Vp.x - 150, FLOOR - 18, 26, 14);
        }
      } },
      { id: 'doer', in: ['shadowA'], run() { g.beginPath(); g.rect(0, 0, PART.x0, H); g.clip(); drawSack(g, Dp, K); } },
      { id: 'partition', in: ['victim', 'doer'], run() {
        g.fillStyle = '#0d0a08'; g.fillRect(PART.x0, 0, PART.x1 - PART.x0, FLOOR + 4);
        // the door leaf, cut in section, with the light gap beneath it
        const bulge = s.doerMode === 'return' && s.A === 'B' ? K.sm(2.5, 2.8, t) * 6 : 0;
        g.fillStyle = '#4a3423'; g.fillRect(DOOR.x0 + bulge, DOOR.top, DOOR.x1 - DOOR.x0, FLOOR - DOOR.gap - DOOR.top);
        g.fillStyle = `rgba(255,205,130,${.85 * (1 - underDoor * .92)})`; g.fillRect(DOOR.x0, FLOOR - DOOR.gap, DOOR.x1 - DOOR.x0 + 16, DOOR.gap - 2);
        g.fillStyle = '#b89356'; g.beginPath(); g.arc(DOOR.x0 - 6, 650, 7, 0, Math.PI * 2); g.fill(); // hall-side knob
        // the bolt on the room side: keeper on the jamb, slide pegged to the door
        g.fillStyle = '#8d7a5e'; g.fillRect(PART.x1 + 6, 592, 30, 30); g.fillStyle = '#1a1410'; g.fillRect(PART.x1 + 10, 602, 22, 10);
        g.fillStyle = '#e0c890'; g.fillRect(PART.x1 - 22 + boltU * 40, 600, 44, 14);
        g.fillStyle = '#b09a70'; g.fillRect(PART.x1 - 6 + boltU * 40, 588, 8, 14);
      } },
      { id: 'grade', in: ['partition'], run() {
        const vg = g.createRadialGradient(W / 2, H * .55, H * .3, W / 2, H * .55, H * 1.05); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.6)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
        if (s.impossible) { g.fillStyle = 'rgba(40,50,70,0.18)'; g.fillRect(0, 0, W, H); }
      } }
    ];
    for (const n of topo(nodes)) { g.save(); n.run(); g.restore(); }
    return { s, tf, Dp, Vp };
  }

  CONSEQ({
    deed: 'assault', n: 8, scion: 20, lineage: 'Toon Boom Harmony — Production Rig Foundry',
    op: 'Expose the aftermath on twos: a bolt drawing swaps to shut, the victim peg retreats to a distance set by fear, a seam drawing is replaced stitch by stitch, and the doer peg walks back, hesitates or preens by its guilt.',
    made: 'Each sack is a rest outline bent by a spine deformer under a peg, with its ears, wig, bolt, stitches and the neighbour\'s door as substitution drawings exposed on twos from per-sack palettes. A hallway lamp and a cut partition wall with a lit gap under the door are composited by a small node network.',
    moved: 'Ledger state picks the branch: the doer\'s guilt toward the victim (return to the door, hesitate, deny), the victim\'s fear and grudge (how far into the corner it sits, how long it stops sewing), a third sack\'s knowledge (opens its door and watches, turns away, or its light goes out), and whether either is dead. The doer\'s shadow, lengthened by its shadow lever, crosses the light under the door and that crossing makes the victim flinch.',
    dur: DUR,
    beat(g, t, ev, st, K, X) { scene(g, t, ev, st, K); },
    branch(ev, st, K) { const s = readState(ev, st, K); return { sh: +(s.LA.shadow || 0).toFixed(2), doer: s.doerMode, wit: s.wit, witMode: s.witMode, dist: +s.dist.toFixed(2), flinch: flinchTime(s, K), aliveV: s.aliveV }; },
    sound(ac, out, t0, ev, st, K) {
      const bus = ac.createGain(); bus.gain.value = 3.2; bus.connect(out); out = bus; // grains are quiet; one bus gain brings the beat to the proof level
      const SND = K.SND, s = readState(ev, st, K), tf = flinchTime(s, K), pan = x => x / 960 - 1;
      const at = (dt, fn) => { if (dt >= 0) fn(t0 + dt); };
      // the house: a clock, slow, once a second; rain on the window
      for (let k = 0; k < 4; k++) at(.2 + k * 1, w => SND.grain(ac, out, w, { f: 1800, d: .015, a: .05, pan: .6 }));
      SND.cloud(ac, out, t0, DUR, 30, { bp: 3200, a: .012, d: [.01, .03], spread: .5 }, u => .6 + .4 * u);
      if (s.aliveV) {
        // the bolt: two clacks, the second the strongest sound of the beat
        at(.3, w => SND.grain(ac, out, w, { bp: 1400, q: 4, d: .03, a: .25, pan: pan(930) }));
        at(.42, w => { SND.grain(ac, out, w, { bp: 900, q: 3, d: .05, a: .45, pan: pan(930) }); SND.thump(ac, out, w, .5, 70, pan(930)); });
        // backing away, then sitting
        for (let k = 0; k < 3; k++) at(.55 + k * .17, w => SND.say(ac, out, s.V, w, 'step', .6, pan(1400)));
        at(1.15, w => SND.say(ac, out, s.V, w, 'land', .4, pan(1600)));
        // needle through cloth: a short rising hiss per stitch, thread drawn out as a longer falling one
        const h = HAND[s.V]; const rate = h.rate * (1 - s.fear * .35) * 4;
        let tt = 1.15;
        for (let i = 0; i < h.N; i++) {
          let ts = 1.15 + (i + .5) / rate;
          if (tf != null && ts > tf) ts += .55 + s.fear * .4;
          if (ts > DUR - .1) break;
          at(ts, w => { SND.grain(ac, out, w, { bp: 4200, q: 3, d: .04, a: .07, glide: .3, pan: pan(1650) }); SND.grain(ac, out, w + .08, { bp: 2600, q: 2, d: .22, a: .04, pan: pan(1600) }); });
        }
        SND.say(ac, out, s.V, t0 + 1.3, 'breathe', 1.2, pan(1650));
        if (tf != null) at(tf, w => { SND.say(ac, out, s.V, w, 'react', .8, pan(1650)); SND.grain(ac, out, w, { f: 120, d: .4, a: .08, glide: -.3, pan: pan(930) }); });
      }
      // the doer, by mode
      if (s.doerMode === 'return') {
        for (let k = 0; k < 5; k++) at(.5 + k * .3, w => SND.say(ac, out, s.A, w, 'step', .7, pan(500 + k * 80)));
        at(2.75, w => { SND.say(ac, out, s.A, w, 'sink', 1, pan(840)); SND.grain(ac, out, w, { f: 90, d: .5, a: .1, glide: -.2, noise: .4, pan: pan(900) }); }); // the door creaks under its weight
      } else if (s.doerMode === 'hesitate') {
        for (let k = 0; k < 4; k++) at(.55 + k * .3, w => SND.say(ac, out, s.A, w, 'step', .5, pan(500 + k * 70)));
        at(1.75, w => SND.say(ac, out, s.A, w, 'tick', .6, pan(760)));
        for (let k = 0; k < 4; k++) at(2.25 + k * .24, w => SND.say(ac, out, s.A, w, 'step', .45, pan(740 - k * 70)));
      } else if (s.doerMode === 'deny') {
        for (let k = 0; k < 6; k++) at(.3 + k * .2, w => SND.say(ac, out, s.A, w, 'tick', .4, pan(640)));
        for (let k = 0; k < 4; k++) at(2.25 + k * .24, w => SND.say(ac, out, s.A, w, 'step', .6, pan(620 - k * 50)));
      } else { SND.say(ac, out, s.A, t0 + .4, 'breathe', 2, pan(600)); }
      // the witness door
      if (s.wit && s.witMode !== 'none') { at(.82, w => SND.grain(ac, out, w, { f: 300, d: .3, a: .06, glide: .4, noise: .5, pan: pan(170) })); if (s.witMode === 'turn') at(2.22, w => SND.grain(ac, out, w, { bp: 700, q: 3, d: .05, a: .2, pan: pan(170) })); }
    },
    trace(g, box, age, K) { // a seam closed badly: a jagged scar with cross-stitches and a loose thread end, yellowing with age
      const a = Math.max(.15, 1 - age * .12), x = box.x + box.w * .5, y0 = box.y + box.h * .15, y1 = box.y + box.h * .85;
      g.save(); g.globalAlpha *= a; g.lineCap = 'round';
      g.strokeStyle = 'rgba(40,28,18,0.9)'; g.lineWidth = Math.max(2, box.w * .04); g.beginPath();
      for (let i = 0; i <= 10; i++) { const y = mix(y0, y1, i / 10), xx = x + (i % 2 ? 1 : -1) * box.w * .05; i ? g.lineTo(xx, y) : g.moveTo(xx, y); } g.stroke();
      const th = age > 4 ? 'rgba(170,150,90,0.9)' : 'rgba(200,190,170,0.95)';
      g.strokeStyle = th; g.lineWidth = Math.max(1.2, box.w * .025);
      for (let i = 0; i < 6; i++) { const y = mix(y0, y1, (i + .5) / 6), d = box.w * .14; g.beginPath(); g.moveTo(x - d, y - d * .4); g.lineTo(x + d, y + d * .4); g.moveTo(x - d, y + d * .4); g.lineTo(x + d, y - d * .4); g.stroke(); }
      g.beginPath(); g.moveTo(x + box.w * .1, y1); g.quadraticCurveTo(x + box.w * .35, y1 + box.h * .05, x + box.w * .3, Math.min(box.y + box.h, y1 + box.h * .14)); g.stroke();
      g.restore();
    }
  });
})();
