/* SCION 19 · the scene renderer: one variable-width ink line over flat fills, on paper.
   Every shape in the film (dog, person, door, house, porch, sky) is a vector shape drawn here: a group's ink is the union of
   its shapes swollen by the line weight, laid twice with a down-right offset so the line is thin where light falls and heavy
   on the shadow side; the flat fill is laid on top; patches are clipped to the fill; detail strokes are tapered polygons.
   Exposes Scene.init(score), Scene.draw(ctx, i) -> measurements, Scene.drawMask(ctx, i), Scene.card(ctx, which). */
(function (root) {
  'use strict';
  const Rig = root.Rig, Perform = root.Perform;
  const { clamp, lerp, sm, tab } = Rig;
  const W = 1280, H = 720;
  const INK = '#1b1714', PAPER = '#efe4cc';
  const COL = {
    sky: '#8d8fb0', skyHi: '#6d6f96', skyLow: '#d6a58f', hills: '#5d6378', trees: '#454b5c',
    porch: '#8a7b86', porchLine: '#5b4f5d', fascia: '#5b4e59', ground: '#4f5a55',
    wallCut: '#e7dcc2', jamb: '#cbb79a', jambLit: '#f0d79a',
    roomDim: '#b98d5a', room: '#efc77a', roomFloorDim: '#8a5d3a', roomFloor: '#b9804c', rug: '#9a3f33',
    door: '#4d6d68', doorLit: '#6d8f86', beam: '#4a4150', post: '#6b5d68',
    light: '#f2d28a', moon: '#f5e9c8',
    sweater: '#3f4f75', trousers: '#5e5249', skin: '#dfae88', hair: '#3b2a22', shoe: '#2e2724', stool: '#8c5a35',
  };
  let S = null;   // state after init

  /* ------------------------------------------------------------------ camera: one scale s (px per metre), a left edge, a ground line */
  function makeCamera(perf) {
    const cams = []; let R = 4.5;
    const K = 0.18, G = 600;
    for (let i = 0; i < perf.length; i++) {
      const t = perf[i].t, U = perf[i].U;
      let target = 4.5;
      if (t > 14.6) target = Math.min(4.5, Math.max(2.05, U + 1.0));
      R = R + (target - R) * 0.06;            // a slow follow
      const zp = clamp((4.5 - R) / (4.5 - 2.05));
      const L = lerp(-1.9, -1.72, zp);
      const s = W / (R - L);
      cams.push({ L, R, s, G: G + 15 * zp, K });
    }
    return cams;
  }
  const P = (c, p) => [(p[0] - c.L) * c.s, c.G - (p[1] - c.K * p[2]) * c.s];

  /* ------------------------------------------------------------------ drawing primitives */
  function capPath(ctx, a, ra, b, rb) {
    const dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy);
    if (d < 1e-6 || d <= Math.abs(ra - rb)) { const [c, r] = ra >= rb ? [a, ra] : [b, rb]; ctx.moveTo(c[0] + r, c[1]); ctx.arc(c[0], c[1], r, 0, 2 * Math.PI); return; }
    const ang = Math.atan2(dy, dx), off = Math.acos((ra - rb) / d);
    ctx.moveTo(a[0] + ra * Math.cos(ang + off), a[1] + ra * Math.sin(ang + off));
    ctx.arc(a[0], a[1], ra, ang + off, ang - off + 2 * Math.PI, false);
    ctx.arc(b[0], b[1], rb, ang - off, ang + off, false);
    ctx.closePath();
  }
  function smoothClosed(ctx, pts) {
    const n = pts.length; if (n < 3) return;
    const m = (p, q) => [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
    let s = m(pts[n - 1], pts[0]); ctx.moveTo(s[0], s[1]);
    for (let k = 0; k < n; k++) { const p = pts[k], q = m(pts[k], pts[(k + 1) % n]); ctx.quadraticCurveTo(p[0], p[1], q[0], q[1]); }
    ctx.closePath();
  }
  function partPath(ctx, c, part, grow, ox, oy) {
    const s = c.s;
    if (part.t === 'cap') { const a = P(c, part.a), b = P(c, part.b); capPath(ctx, [a[0] + ox, a[1] + oy], part.ra * s + grow, [b[0] + ox, b[1] + oy], part.rb * s + grow); }
    else if (part.t === 'circ') { const a = P(c, part.c), r = part.r * s + grow; ctx.moveTo(a[0] + ox + r, a[1] + oy); ctx.arc(a[0] + ox, a[1] + oy, r, 0, 2 * Math.PI); }
    else if (part.t === 'poly') { const pts = part.pts.map(p => { const q = P(c, p); return [q[0] + ox, q[1] + oy]; }); if (part.smooth) smoothClosed(ctx, pts); else { ctx.moveTo(...pts[0]); pts.slice(1).forEach(p => ctx.lineTo(...p)); ctx.closePath(); } }
  }
  function polyGrow(ctx, c, part, grow, ox, oy) {     // polygons swell by stroking
    ctx.beginPath(); partPath(ctx, c, part, 0, ox, oy); ctx.fill();
    if (grow > 0) { ctx.lineWidth = grow * 2; ctx.lineJoin = 'round'; ctx.stroke(); }
  }
  function lineW(c) { return 1.5 + 0.0068 * c.s; }
  function inkOff(c) { return 0.7 + 0.0042 * c.s; }
  // tapered stroke: an open polyline drawn as a polygon whose half-width swells in the middle
  function taper(ctx, c, pts2, w, color) {
    const pts = []; // resample with quadratic smoothing
    for (let k = 0; k < pts2.length - 1; k++) for (let j = 0; j < 6; j++) { const u = j / 6; pts.push([lerp(pts2[k][0], pts2[k + 1][0], u), lerp(pts2[k][1], pts2[k + 1][1], u)]); }
    pts.push(pts2[pts2.length - 1]);
    if (pts.length < 2) return;
    const n = pts.length, L = [], Rr = [];
    for (let k = 0; k < n; k++) {
      const p = pts[Math.max(0, k - 1)], q = pts[Math.min(n - 1, k + 1)];
      let dx = q[0] - p[0], dy = q[1] - p[1]; const d = Math.hypot(dx, dy) || 1; dx /= d; dy /= d;
      const u = k / (n - 1), hw = w * Math.sin(Math.PI * (0.08 + 0.84 * u)) * (1 + 0.25 * (1 - u));
      L.push([pts[k][0] - dy * hw, pts[k][1] + dx * hw]); Rr.push([pts[k][0] + dy * hw, pts[k][1] - dx * hw]);
    }
    ctx.fillStyle = color || INK; ctx.beginPath(); ctx.moveTo(...L[0]); L.forEach(p => ctx.lineTo(...p)); Rr.reverse().forEach(p => ctx.lineTo(...p)); ctx.closePath(); ctx.fill();
  }
  function drawGroup(ctx, c, g, opt) {
    opt = opt || {};
    const lw = (opt.lw || lineW(c)) * (g.thin || 1), off = opt.off != null ? opt.off : inkOff(c);
    const parts = g.parts || [];
    if (parts.length) {
      ctx.fillStyle = INK; ctx.strokeStyle = INK;
      for (const [ox, oy, gr] of [[0, 0, lw * 0.55], [off * 0.7, off, lw * 0.55]]) {
        const caps = parts.filter(p => p.t !== 'poly');
        if (caps.length) { ctx.beginPath(); caps.forEach(p => partPath(ctx, c, p, gr, ox, oy)); ctx.fill('nonzero'); }
        parts.filter(p => p.t === 'poly').forEach(p => polyGrow(ctx, c, p, gr, ox, oy));
      }
      ctx.fillStyle = g.fill;
      const caps = parts.filter(p => p.t !== 'poly');
      if (caps.length) { ctx.beginPath(); caps.forEach(p => partPath(ctx, c, p, 0, 0, 0)); ctx.fill('nonzero'); }
      parts.filter(p => p.t === 'poly').forEach(p => { ctx.beginPath(); partPath(ctx, c, p, 0, 0, 0); ctx.fill(); });
      if (g.patches && g.patches.length) {
        ctx.save(); ctx.beginPath(); parts.forEach(p => partPath(ctx, c, p, -0.4, 0, 0)); ctx.clip('nonzero');
        g.patches.forEach(p => { ctx.fillStyle = p.fill; ctx.beginPath(); partPath(ctx, c, p, 0, 0, 0); ctx.fill(); });
        ctx.restore();
      }
    }
    (g.details || []).forEach(d => {
      if (d.t === 'stroke') taper(ctx, c, d.pts.map(p => P(c, p)), lw * 0.75 * d.w + 0.4, d.color);
      else if (d.t === 'dot') { const a = P(c, d.c); ctx.fillStyle = d.fill; ctx.beginPath(); ctx.arc(a[0], a[1], Math.max(1.2, d.r * c.s), 0, 2 * Math.PI); ctx.fill(); }
    });
  }

  /* ------------------------------------------------------------------ the person (same line, same primitives) */
  function ik2(R, T, L1, L2, sign) { const s = Rig.ik2(R, T, L1, L2, sign); return s; }
  function person(pd, t, i) {
    const sit = sm(pd.sit), reach = sm(pd.reach), low = sm(pd.low), U = pd.U;
    const walkPhase = S.personWalk[i];
    const moving = S.personSpeed[i] > 0.05 ? 1 : 0;
    const hipY = lerp(0.93, 0.47, sit);
    const lean = lerp(0.06 * reach + 0.03 * clamp(pd.mouth), 0.38 * low + 0.1, sit);     // radians, forward toward the dog
    const hip = [U, hipY], spineLen = 0.52;
    const sh = [U + Math.sin(lean) * spineLen, hipY + Math.cos(lean) * spineLen];
    const neck = [sh[0] + Math.sin(lean * 0.7) * 0.10, sh[1] + Math.cos(lean * 0.7) * 0.10];
    const headC = [neck[0] + 0.03, neck[1] + 0.11];
    const legs = [], arms = [];
    for (const side of [-1, 1]) {     // -1 far, +1 near
      const sw = moving ? Math.sin(walkPhase + (side > 0 ? 0 : Math.PI)) : 0;
      let foot;
      if (sit < 0.5) foot = [U + 0.04 + 0.22 * sw - 0.02 * side, Math.max(0, 0.05 * Math.cos(walkPhase + (side > 0 ? 0 : Math.PI))) * moving];
      else foot = [U + 0.47 + 0.05 * side, 0];
      foot = [lerp(foot[0], U + 0.47 + 0.05 * side, sit), foot[1] * (1 - sit)];
      const ankle = [foot[0], foot[1] + 0.07];
      const k = ik2(hip, ankle, 0.45, 0.43, 1);
      legs.push({ side, hip, knee: k.J, ankle: k.E, toe: [k.E[0] + 0.19, Math.max(0.02, k.E[1] - 0.05)] });
    }
    for (const side of [-1, 1]) {
      let hand;
      const shp = [sh[0] - 0.02 * side, sh[1] - 0.03];
      if (side > 0) {
        const down = [shp[0] + 0.05, shp[1] - 0.56], fwd = [shp[0] + 0.56, shp[1] - 0.08];
        hand = [lerp(down[0], fwd[0], reach), lerp(down[1], fwd[1], reach)];
        if (sit > 0.5) { const rest = [U + 0.42, 0.62], lowH = [shp[0] + 0.32, shp[1] - 0.47]; hand = [lerp(rest[0], lowH[0], low), lerp(rest[1], lowH[1], low)]; }
      } else {
        hand = sit > 0.5 ? [U + 0.36, 0.60] : [shp[0] - 0.02, shp[1] - 0.55];
        if (sit > 0.5) { const k = sm((t - 5.85) / 0.3) * (1 - sm((t - 6.75) / 0.35)); hand = [lerp(hand[0], U - 0.32, k), lerp(hand[1], 0.72, k)]; }   // pushes the door open
        if (sit < 0.5 && t < 4.6) hand = [shp[0] - 0.30, shp[1] - 0.42];   // holding the door edge
      }
      const k = ik2(shp, hand, 0.30, 0.28, -1);
      arms.push({ side, sh: shp, el: k.J, wr: k.E, hand: [k.E[0] + (k.E[0] - k.J[0]) * 0.3, k.E[1] + (k.E[1] - k.J[1]) * 0.3] });
    }
    const w3 = (p, w) => [p[0], p[1], w];
    const Wp = pd.W;
    const G = [];
    const cap = (a, ra, b, rb, w) => ({ t: 'cap', a: w3(a, w), ra, b: w3(b, w), rb });
    // far limbs
    const lf = legs[0], af = arms[0];
    G.push({ fill: '#4a4039', parts: [cap(lf.hip, 0.085, lf.knee, 0.07, Wp - 0.1), cap(lf.knee, 0.065, lf.ankle, 0.05, Wp - 0.1)], details: [] });
    G.push({ fill: COL.shoe, parts: [cap(lf.ankle, 0.045, lf.toe, 0.04, Wp - 0.1)], details: [] });
    G.push({ fill: '#33405f', parts: [cap(af.sh, 0.06, af.el, 0.05, Wp - 0.1), cap(af.el, 0.048, af.wr, 0.04, Wp - 0.1)], details: [] });
    G.push({ fill: COL.skin, parts: [cap(af.wr, 0.035, af.hand, 0.038, Wp - 0.1)], details: [] });
    // torso and head
    const chestF = [sh[0] + 0.06, sh[1] - 0.10];
    G.push({ fill: COL.trousers, parts: [cap(hip, 0.15, [hip[0] + 0.02, hip[1] + 0.1], 0.14, Wp)], details: [] });
    G.push({ fill: COL.sweater, parts: [cap([hip[0] + 0.01, hip[1] + 0.08], 0.15, sh, 0.15, Wp), cap(chestF, 0.12, sh, 0.13, Wp), cap(sh, 0.11, neck, 0.06, Wp)], details: [{ t: 'stroke', pts: [w3([hip[0] - 0.13, hip[1] + 0.06], Wp), w3([hip[0] + 0.05, hip[1] + 0.03], Wp), w3([hip[0] + 0.15, hip[1] + 0.07], Wp)], w: 0.6 }] });
    const nose = [headC[0] + 0.105, headC[1] - 0.005], mouthO = clamp(pd.mouth);
    G.push({ fill: COL.skin, parts: [cap(neck, 0.05, headC, 0.05, Wp), { t: 'circ', c: w3(headC, Wp), r: 0.098 }, cap([headC[0] + 0.05, headC[1] - 0.04], 0.05, [headC[0] + 0.07, headC[1] - 0.075], 0.04, Wp), cap(headC, 0.05, nose, 0.018, Wp)],
      patches: [{ t: 'cap', a: w3([headC[0] - 0.05, headC[1] + 0.05], Wp), ra: 0.085, b: w3([headC[0] + 0.03, headC[1] + 0.085], Wp), rb: 0.06, fill: COL.hair }],
      details: [
        { t: 'dot', c: w3([headC[0] + 0.055, headC[1] + 0.02], Wp), r: 0.011, fill: INK },
        { t: 'stroke', pts: [w3([headC[0] + 0.03, headC[1] + 0.045], Wp), w3([headC[0] + 0.075, headC[1] + 0.05], Wp)], w: 0.55 },
        { t: 'stroke', pts: [w3([headC[0] - 0.015, headC[1] + 0.02], Wp), w3([headC[0] - 0.03, headC[1] - 0.01], Wp), w3([headC[0] - 0.01, headC[1] - 0.03], Wp)], w: 0.5 },
      ] });
    if (mouthO > 0.05) G[G.length - 1].details.push({ t: 'dot', c: w3([headC[0] + 0.08, headC[1] - 0.05], Wp), r: 0.008 + 0.017 * mouthO, fill: '#4a1f1a' });
    else G[G.length - 1].details.push({ t: 'stroke', pts: [w3([headC[0] + 0.065, headC[1] - 0.052], Wp), w3([headC[0] + 0.095, headC[1] - 0.048], Wp)], w: 0.45 });
    // near limbs
    const ln = legs[1], an = arms[1];
    G.push({ fill: COL.trousers, parts: [cap(ln.hip, 0.09, ln.knee, 0.072, Wp + 0.1), cap(ln.knee, 0.067, ln.ankle, 0.052, Wp + 0.1)], details: [] });
    G.push({ fill: COL.shoe, parts: [cap(ln.ankle, 0.047, ln.toe, 0.042, Wp + 0.1)], details: [] });
    G.push({ fill: COL.sweater, parts: [cap(an.sh, 0.065, an.el, 0.052, Wp + 0.1), cap(an.el, 0.05, an.wr, 0.042, Wp + 0.1)], details: [] });
    G.push({ fill: COL.skin, parts: [cap(an.wr, 0.036, an.hand, 0.04, Wp + 0.1)], details: low > 0.5 && sit > 0.5 ? [{ t: 'stroke', pts: [w3([an.hand[0] - 0.02, an.hand[1] + 0.03], Wp + 0.1), w3([an.hand[0] + 0.04, an.hand[1] + 0.035], Wp + 0.1)], w: 0.45 }] : [] });
    return { groups: G, hand: an.hand, head: headC };
  }

  /* ------------------------------------------------------------------ the place */
  function poly(ctx, c, pts, fill, ink, lw) {
    const q = pts.map(p => P(c, p)); ctx.beginPath(); ctx.moveTo(...q[0]); q.slice(1).forEach(p => ctx.lineTo(...p)); ctx.closePath();
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (ink) { ctx.strokeStyle = INK; ctx.lineWidth = lw || lineW(c) * 0.7; ctx.lineJoin = 'round'; ctx.stroke(); }
  }
  function line(ctx, c, a, b, w, col) { const p = P(c, a), q = P(c, b); ctx.strokeStyle = col || INK; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(...p); ctx.lineTo(...q); ctx.stroke(); }
  function inkLine(ctx, c, pts, w) { taper(ctx, c, pts.map(p => P(c, p)), w); }

  function drawPlace(ctx, c, t, open, i) {
    const lit = open;     // 0 ajar .. 1 open
    const lw = lineW(c);
    // sky: flat bands
    ctx.fillStyle = COL.skyHi; ctx.fillRect(0, 0, W, H);
    const yHz = P(c, [0, 0.85, -6])[1];
    ctx.fillStyle = COL.sky; ctx.fillRect(0, yHz - 0.75 * c.s, W, 0.75 * c.s + 2);
    ctx.fillStyle = COL.skyLow; ctx.fillRect(0, yHz - 0.28 * c.s, W, 0.3 * c.s);
    // moon
    const mo = P(c, [3.0, 2.15, -6]);
    ctx.fillStyle = COL.moon; ctx.strokeStyle = INK; ctx.lineWidth = lw * 0.6; ctx.beginPath(); ctx.arc(mo[0], mo[1], 0.13 * c.s, 0, 7); ctx.fill(); ctx.stroke();
    // distant hills and trees: ink-lined flat silhouettes
    ctx.fillStyle = COL.hills; ctx.beginPath(); ctx.moveTo(0, yHz + 4);
    for (let u = -2; u <= 7; u += 0.25) { const p = P(c, [u, 0.85 + 0.18 * Math.sin(u * 1.3) + 0.1 * Math.sin(u * 3.1 + 1), -6]); ctx.lineTo(p[0], p[1]); }
    ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = lw * 0.5; ctx.stroke();
    for (const [u, h, r] of [[1.2, 1.7, 0.34], [1.75, 1.45, 0.26], [3.7, 1.9, 0.4], [4.25, 1.55, 0.3]]) {
      const tr = P(c, [u, 0.9, -6]), cr = P(c, [u, h, -6]);
      ctx.strokeStyle = INK; ctx.lineWidth = lw * 0.9; ctx.beginPath(); ctx.moveTo(tr[0], tr[1] + 10); ctx.lineTo(cr[0], cr[1]); ctx.stroke();
      ctx.fillStyle = COL.trees; ctx.beginPath();
      for (let k = 0; k < 7; k++) { const a = k / 7 * 2 * Math.PI; const rr = r * c.s * (0.75 + 0.25 * Math.sin(k * 2.3 + u)); ctx.moveTo(cr[0] + Math.cos(a) * r * c.s * 0.6 + rr * 0.55, cr[1] + Math.sin(a) * r * c.s * 0.5); ctx.arc(cr[0] + Math.cos(a) * r * c.s * 0.6, cr[1] + Math.sin(a) * r * c.s * 0.5, rr * 0.55, 0, 7); }
      ctx.fill(); ctx.lineWidth = lw * 0.5; ctx.stroke();
    }
    // porch floor (U from 0 to the steps), W from -1.45 (rail) to +0.9 (front edge)
    const U0 = 0, U1 = 4.55, Wf = -1.45, Wn = 0.95;
    poly(ctx, c, [[U0, 0, Wf], [U1, 0, Wf], [U1, 0, Wn], [U0, 0, Wn]], COL.porch, false);
    for (let w = Wf; w <= Wn + 1e-6; w += 0.13) line(ctx, c, [U0, 0, w], [U1, 0, w], lw * 0.35, COL.porchLine);
    for (let k = 0; k < 18; k++) { const w = Wf + (k % 9) * 0.26 + 0.065, u = 0.4 + ((k * 1.37) % 4); line(ctx, c, [u, 0, w], [u, 0, w + 0.13], lw * 0.3, COL.porchLine); }
    // light from the open door on the boards
    if (lit > 0.01) {
      ctx.save(); ctx.globalAlpha = 0.72 * lit;
      poly(ctx, c, [[0, 0, -0.45], [0, 0, 0.45], [2.7, 0, 1.0], [3.3, 0, 0.1], [2.5, 0, -1.2]], COL.light, false);
      ctx.restore();
    }
    // porch front fascia and the ground below
    poly(ctx, c, [[U0, 0, Wn], [U1, 0, Wn], [U1, -0.35, Wn], [U0, -0.35, Wn]], COL.fascia, true);
    ctx.fillStyle = COL.ground; const gy = P(c, [0, -0.35, Wn])[1]; ctx.fillRect(0, gy, W, H - gy);
    // steps at the far end
    for (let k = 0; k < 3; k++) poly(ctx, c, [[U1 + k * 0.28, -k * 0.12, Wf], [U1 + 0.28 + k * 0.28, -k * 0.12, Wf], [U1 + 0.28 + k * 0.28, -k * 0.12, Wn], [U1 + k * 0.28, -k * 0.12, Wn]], k % 2 ? COL.porch : '#7d6f7a', true);
    // railing and posts at the far side of the porch
    for (const u of [0.15, 2.3, 4.45]) poly(ctx, c, [[u - 0.06, 0, Wf], [u + 0.06, 0, Wf], [u + 0.06, 2.55, Wf], [u - 0.06, 2.55, Wf]], COL.post, true);
    poly(ctx, c, [[0.15, 0.86, Wf], [4.5, 0.86, Wf], [4.5, 0.93, Wf], [0.15, 0.93, Wf]], COL.post, true);
    poly(ctx, c, [[0.15, 0.10, Wf], [4.5, 0.10, Wf], [4.5, 0.15, Wf], [0.15, 0.15, Wf]], COL.post, true);
    for (let u = 0.35; u < 4.45; u += 0.2) if (Math.abs(u - 2.3) > 0.1) line(ctx, c, [u, 0.15, Wf], [u, 0.86, Wf], lw * 0.55, '#3a3240');
    // porch roof beam
    poly(ctx, c, [[-0.3, 2.55, Wf], [4.7, 2.55, Wf], [4.7, 2.75, Wn], [-0.3, 2.75, Wn]], COL.beam, true);
    // the room (cut away): back wall, floor, lamp, picture
    const RL = -3.2, RW = -0.25, Rb = -2.2;
    const roomCol = lerpCol(COL.roomDim, COL.room, lit), floorCol = lerpCol(COL.roomFloorDim, COL.roomFloor, lit);
    poly(ctx, c, [[RL, 0, Rb], [RW, 0, Rb], [RW, 3.2, Rb], [RL, 3.2, Rb]], roomCol, false);
    poly(ctx, c, [[RL, 0, Rb], [RW, 0, Rb], [RW, 0, 1.0], [RL, 0, 1.0]], floorCol, false);
    for (let w = Rb; w < 1; w += 0.16) line(ctx, c, [RL, 0, w], [RW, 0, w], lw * 0.3, '#6b4528');
    line(ctx, c, [RL, 0, Rb], [RW, 0, Rb], lw * 0.8);
    poly(ctx, c, [[RL, 0, Rb], [RW, 0, Rb], [RW, 0.1, Rb], [RL, 0.1, Rb]], '#a47344', true);
    poly(ctx, c, [[-1.55, 0.002, -1.4], [-0.45, 0.002, -1.4], [-0.45, 0.002, 0.2], [-1.55, 0.002, 0.2]], COL.rug, true);
    // picture on the back wall
    poly(ctx, c, [[-1.0, 1.25, Rb], [-0.55, 1.25, Rb], [-0.55, 1.65, Rb], [-1.0, 1.65, Rb]], '#c9b48b', true);
    poly(ctx, c, [[-0.94, 1.31, Rb], [-0.61, 1.31, Rb], [-0.61, 1.59, Rb], [-0.94, 1.59, Rb]], '#7e8c6e', true);
    // lamp at the back of the room: the room's light
    const lb = [-1.25, 0, -2.0];
    line(ctx, c, lb, [-1.25, 1.35, -2.0], lw * 1.0);
    poly(ctx, c, [[-1.45, 1.3, -2.0], [-1.05, 1.3, -2.0], [-1.15, 1.62, -2.0], [-1.35, 1.62, -2.0]], lerpCol('#c99a56', '#fff0b8', lit), true);
    // the door: hinged at the inner face of the far jamb; ajar (22 deg) -> open (165 deg, back against the inner wall so the lit room shows)
    const phi = lerp(22, 165, open) * Math.PI / 180, hU = -0.25, hW = -0.45, Dw = 0.88;
    const eU = hU - Dw * Math.sin(phi), eW = hW + Dw * Math.cos(phi);
    poly(ctx, c, [[hU, 0, hW], [eU, 0, eW], [eU, 2.02, eW], [hU, 2.02, hW]], lerpCol(COL.door, COL.doorLit, lit * 0.6), true);
    const pp = (a, b, y) => [lerp(hU, eU, a), y, lerp(hW, eW, a)];
    poly(ctx, c, [pp(0.18, 0, 1.15), pp(0.82, 0, 1.15), pp(0.82, 0, 1.85), pp(0.18, 0, 1.85)], null, true, lw * 0.4);
    poly(ctx, c, [pp(0.18, 0, 0.2), pp(0.82, 0, 0.2), pp(0.82, 0, 0.95), pp(0.18, 0, 0.95)], null, true, lw * 0.4);
    const kn = pp(0.9, 0, 1.0), kp = P(c, kn); ctx.fillStyle = '#d9b860'; ctx.beginPath(); ctx.arc(kp[0], kp[1], Math.max(2, 0.025 * c.s), 0, 7); ctx.fill();
  }
  // the wall section and the sill: drawn over the room and under the dog
  function drawWall(ctx, c, lit) {
    const lw = lineW(c);
    // the cut wall above the door, hatched (section)
    const top = 3.6;
    poly(ctx, c, [[-0.25, 2.05, 0], [0, 2.05, 0], [0, top, 0], [-0.25, top, 0]], COL.wallCut, true, lw * 1.2);
    const a = P(c, [-0.25, 2.05, 0]), b = P(c, [0, top, 0]);
    ctx.save(); ctx.beginPath(); ctx.rect(a[0], b[1], b[0] - a[0], a[1] - b[1]); ctx.clip(); ctx.strokeStyle = INK; ctx.lineWidth = lw * 0.35;
    for (let k = -40; k < 80; k++) { const x = a[0] + k * 9; ctx.beginPath(); ctx.moveTo(x, a[1]); ctx.lineTo(x + (a[1] - b[1]), b[1]); ctx.stroke(); }
    ctx.restore();
    poly(ctx, c, [[-0.25, 2.05, 0], [0.02, 2.05, 0], [0.02, 2.12, 0], [-0.25, 2.12, 0]], '#8a6a4a', true);   // lintel/head of the frame
    // foundation below the floor, hatched
    poly(ctx, c, [[-0.25, -0.35, 0.95], [0, -0.35, 0.95], [0, 0, 0.95], [-0.25, 0, 0.95]], COL.wallCut, true);
    // the sill: a raised board across the doorway (U -0.27 .. 0.05)
    poly(ctx, c, [[-0.27, 0, -0.45], [0.06, 0, -0.45], [0.06, 0.035, -0.45], [-0.27, 0.035, -0.45]], '#9b7048', true);
    poly(ctx, c, [[-0.27, 0.035, -0.45], [0.06, 0.035, -0.45], [0.06, 0.035, 0.45], [-0.27, 0.035, 0.45]], '#b58757', true);
    poly(ctx, c, [[-0.27, 0, 0.45], [0.06, 0, 0.45], [0.06, 0.035, 0.45], [-0.27, 0.035, 0.45]], '#7d5734', true);
  }
  function drawStool(ctx, c, U, w) {
    poly(ctx, c, [[U - 0.22, 0.38, w], [U + 0.18, 0.38, w], [U + 0.18, 0.44, w], [U - 0.22, 0.44, w]], COL.stool, true);
    for (const du of [-0.18, 0.14]) poly(ctx, c, [[U + du, 0, w], [U + du + 0.04, 0, w], [U + du + 0.04, 0.38, w], [U + du, 0.38, w]], '#6e4426', true);
  }
  function lerpCol(a, b, t) {
    const p = x => [parseInt(x.slice(1, 3), 16), parseInt(x.slice(3, 5), 16), parseInt(x.slice(5, 7), 16)];
    const A = p(a), B = p(b); return '#' + A.map((v, k) => Math.round(lerp(v, B[k], clamp(t))).toString(16).padStart(2, '0')).join('');
  }

  /* ------------------------------------------------------------------ paper grain */
  function makeGrain() {
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H; const g = cv.getContext('2d');
    const id = g.createImageData(W, H); let seed = 19;
    const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
    for (let k = 0; k < W * H; k++) { const v = 128 + (rnd() - 0.5) * 70; id.data[k * 4] = v; id.data[k * 4 + 1] = v * 0.97; id.data[k * 4 + 2] = v * 0.9; id.data[k * 4 + 3] = 255; }
    g.putImageData(id, 0, 0);
    // fibres
    g.strokeStyle = 'rgba(90,70,40,0.25)'; g.lineWidth = 0.6;
    for (let k = 0; k < 900; k++) { const x = rnd() * W, y = rnd() * H, a = rnd() * 6.3, l = 4 + rnd() * 14; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + Math.cos(a) * l * 0.5 + 3, y + Math.sin(a) * l * 0.5, x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke(); }
    return cv;
  }

  /* ------------------------------------------------------------------ init and per-frame */
  function init(score) {
    const perf = Perform.perform(score), pd = Perform.personDoor(score);
    const cams = makeCamera(perf);
    // door opening fraction (eases over 0.75 s after the score's door turns 'open')
    const tOpen = (score.frames.find(f => f.door === 'open') || { t: 99 }).t;
    // person walk phase
    const pw = [], ps = []; let acc = 0;
    for (let i = 0; i < pd.length; i++) { const d = i ? Math.abs(pd[i].U - pd[i - 1].U) : 0; acc += d; pw.push(acc / 0.35 * Math.PI); ps.push(d * 24); }
    S = { score, perf, pd, cams, tOpen, personWalk: pw, personSpeed: ps, grain: makeGrain() };
    return S;
  }
  const LINES = [[1.0, 2.25, 'Come here.'], [3.4, 4.6, 'Come here!'], [7.4, 9.3, 'It’s all right.'], [10.4, 11.6, 'It’s all right.'], [26.4, 27.6, 'Come in.']];

  function dogParams(i) { const p = S.perf[i]; return Object.assign({}, p, { colors: null }); }

  function draw(ctx, i, opts) {
    opts = opts || {};
    const c = S.cams[i], p = S.perf[i], t = p.t;
    const open = sm((t - S.tOpen) / 0.75);
    ctx.save();
    drawPlace(ctx, c, t, open, i);
    poly(ctx, c, [[-0.25, 0, -0.45], [0, 0, -0.45], [0, 2.05, -0.45], [-0.25, 2.05, -0.45]], lerpCol(COL.jamb, COL.jambLit, open), true);   // far jamb face
    drawStool(ctx, c, S.pd[767].U, S.pd[767].W);
    // person (inside, by the door)
    const per = person(S.pd[i], t, i);
    per.groups.forEach(g => drawGroup(ctx, c, g));
    drawWall(ctx, c, open);
    // dog shadow: a flat ellipse on the boards
    const rig = Rig.frame(p);
    const m = rig.meas;
    const shU = (m.pelvisW[0] + m.withersW[0]) / 2, shWd = Math.abs(m.pelvisW[0] - m.withersW[0]) + 0.3;
    const sp = P(c, [shU, 0, 0.0]);
    ctx.fillStyle = 'rgba(40,30,45,0.28)'; ctx.beginPath(); ctx.ellipse(sp[0], sp[1] + 2, shWd * c.s * 0.62, 0.075 * c.s, 0, 0, 7); ctx.fill();
    rig.groups.forEach(g => drawGroup(ctx, c, g));
    // dialogue (the person's words), set small at the foot of the frame
    const ln = LINES.find(l => t >= l[0] && t < l[1]);
    if (ln && !opts.noText) {
      ctx.font = 'italic 400 30px Literata'; ctx.textAlign = 'center';
      const soft = /all right|Come in/.test(ln[2]);
      ctx.fillStyle = soft ? 'rgba(245,234,205,0.92)' : 'rgba(250,240,215,1)';
      const a = clamp((t - ln[0]) / 0.15) * clamp((ln[1] - t) / 0.2);
      ctx.globalAlpha = a; ctx.fillText(ln[2], W / 2, 690); ctx.globalAlpha = 1;
    }
    // paper grain over everything
    ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = 0.22; ctx.drawImage(S.grain, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    ctx.restore();
    return { cam: c, meas: m, per: { hand: per.hand, head: per.head } };
  }
  // mask pass: the dog's fills only, in one flat colour, for measurement from pixels
  function drawMask(ctx, i, scale) {
    const c0 = S.cams[i], c = Object.assign({}, c0, { s: c0.s * scale, L: c0.L, G: c0.G * scale });
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W * scale, H * scale);
    const rig = Rig.frame(S.perf[i]);
    ctx.fillStyle = '#fff';
    rig.groups.forEach(g => { (g.parts || []).forEach(p => { ctx.beginPath(); partPath(ctx, c, p, 0, 0, 0); ctx.fill(); }); });
    return c;
  }

  root.Scene = { init, draw, drawMask, drawGroup, P, COL, INK, PAPER, lineW, inkOff, lerpCol, get state() { return S; } };
})(typeof window !== 'undefined' ? window : globalThis);
