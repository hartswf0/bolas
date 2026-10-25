/* SCION 18 · the hybrid dog rig. Hand-authored drawings (SHEET.dog) are the dog; the rig only
   (a) in-betweens drawings of the same part (stand ⇄ crouch ⇄ lie, view ⇄ next view on the turnaround),
   (b) places heads (substituted from the expression/turn sheet) at the neck pivot, and
   (c) solves the selective rig: two-bone legs to planted feet, a six-link tail. Line is built in screen px (saloon.js). */
'use strict';
const D = SHEET.dog;
const N = 120;
const dense = {}; // cached resampled drawings
function dz(key, part, closed = true) {
  const k = key + '.' + part;
  if (!dense[k]) { const src = D[key][part]; dense[k] = src ? resample(crSample(src, closed), N, closed) : null; }
  return dense[k];
}
function denseStroke(s) { return resample(crSample(s, false, 8), 24, false); }
function mixP(a, b, t) { return lp(a, b, t); }

// body of one view family at (crouch, lie): returns {outline, bib, strokes, pivots}
function bodyL(cr, li) {
  const o = lerpPts(lerpPts(dz('L_stand', 'outline'), dz('L_crouch', 'outline'), cr), dz('L_lie', 'outline'), li);
  const b = lerpPts(lerpPts(dz('L_stand', 'bib'), dz('L_crouch', 'bib'), cr), dz('L_lie', 'bib'), li);
  const st = D.L_stand.strokes.map((s, i) => lerpPts(lerpPts(denseStroke(s), denseStroke(D.L_crouch.strokes[i]), cr), denseStroke(D.L_lie.strokes[i]), li));
  const pv = {};
  for (const k of ['shoulder', 'hip', 'neck', 'tail']) pv[k] = mixP(mixP(D.L_stand[k], D.L_crouch[k], cr), D.L_lie[k], li);
  return { outline: o, bib: b, strokes: st, pv, fam: 'L' };
}
function bodyQ1(li, mirror) {
  let o = lerpPts(dz('Q1_stand', 'outline'), dz('Q1_lie', 'outline'), li);
  const sA = D.Q1_stand.strokes, sB = D.Q1_lie.strokes;
  let st = sA.map((s, i) => sB[i] ? lerpPts(denseStroke(s), denseStroke(sB[i]), li) : denseStroke(s));
  if (li > 0.6) st = st.slice(0, sB.length);
  const pv = { neck: mixP(D.Q1_stand.neck, D.Q1_lie.neck, li), tail: mixP(D.Q1_stand.tail, D.Q1_lie.tail, li) };
  if (mirror) { o = mirrorPts(o); o = [o[0], ...o.slice(1).reverse()]; // keep the winding (and correspondence) of the unmirrored drawings
    st = st.map(mirrorPts); pv.neck = [-pv.neck[0], pv.neck[1]]; pv.tail = [-pv.tail[0], pv.tail[1]]; }
  return { outline: o, bib: null, strokes: st, pv, fam: mirror ? 'Q2' : 'Q1' };
}
function bodyRV() { return { outline: dz('RV_stand', 'outline'), bib: null, strokes: D.RV_stand.strokes.map(denseStroke), pv: { neck: D.RV_stand.neck, tail: D.RV_stand.tail }, fam: 'RV' }; }
function mixBody(A, B, t) {
  if (t <= 0) return A; if (t >= 1) return B;
  const pv = {}; for (const k in A.pv) if (B.pv[k]) pv[k] = mixP(A.pv[k], B.pv[k], t);
  return { outline: lerpPts(A.outline, B.outline, t), bib: t < 0.5 ? A.bib : B.bib, strokes: t < 0.5 ? A.strokes : B.strokes, pv, fam: t < 0.5 ? A.fam : B.fam, mixT: t, famA: A.fam, famB: B.fam };
}

// legs of a view family in its own (display-local) frame: [{root, foot, near}] in order LF RF LH RH
function legsOf(fam, body, cr, li, feetL) {
  const LG = D.legs;
  if (fam === 'L') return LG.L.map((g, i) => {
    const r = body.pv[g.root]; const root = [r[0] + g.dx, r[1]];
    const stand = feetL ? feetL[i] : g.foot;
    return { root, foot: mixP(stand, LG.L_lie_feet[i], li), lift: feetL ? feetL[i][2] || 0 : 0, near: g.near, depth: 1 };
  });
  if (fam === 'RV') return LG.RV.map(g => ({ root: g.root, foot: g.foot, lift: 0, near: g.near, depth: 0.15 }));
  const q = LG.Q1.map((g, i) => ({ root: mixP(g.root, LG.Q1_lie[i].root, li), foot: mixP(g.foot, LG.Q1_lie[i].foot, li), lift: 0, near: g.near, depth: 0.45 }));
  if (fam === 'Q1') return q;
  // Q2: mirror, and the dog's right side now faces the viewer (swap left/right identities)
  const m = l => ({ root: [-l.root[0], l.root[1]], foot: [-l.foot[0], l.foot[1]], lift: 0, near: l.near, depth: l.depth });
  return [m(q[1]), m(q[0]), m(q[3]), m(q[2])];
}

// two-bone solve; knee side: fore elbow goes back (+x when facing left), hind stifle forward. depth squashes the lateral bend
function ik(root, foot, l1, l2, side, depth) {
  const dx = foot[0] - root[0], dy = foot[1] - root[1]; let d = Math.hypot(dx, dy);
  const dd = Math.min(d, l1 + l2 - 0.01), a = Math.atan2(dy, dx);
  const cosA = clamp((l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd), -1, 1);
  const ang = a + side * Math.acos(cosA);
  const k = [root[0] + l1 * Math.cos(ang), root[1] + l1 * Math.sin(ang)];
  // lateral displacement off the root→foot line, squashed for foreshortened views
  const ux = dx / (d || 1), uy = dy / (d || 1), px = k[0] - root[0], py = k[1] - root[1];
  const along = px * ux + py * uy, lat = -px * uy + py * ux;
  return [root[0] + along * ux - lat * depth * uy, root[1] + along * uy + lat * depth * ux];
}

function legOutline(root, knee, foot, w, toeDir, lift) {
  const ankle = [foot[0], foot[1] + 3.2 + lift];
  const segs = [[root[0], root[1] + 7], root, knee, ankle];
  const ws = [w[0], w[0], w[1], w[2]];
  const L = [], R = [];
  for (let i = 0; i < segs.length; i++) {
    const a = segs[Math.max(0, i - 1)], b = segs[Math.min(segs.length - 1, i + 1)];
    let tx = b[0] - a[0], ty = b[1] - a[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
    L.push([segs[i][0] - ty * ws[i] / 2, segs[i][1] + tx * ws[i] / 2]); R.push([segs[i][0] + ty * ws[i] / 2, segs[i][1] - tx * ws[i] / 2]);
  }
  const fy = foot[1] + lift, td = toeDir;
  const pawFront = td === 0 ? [[ankle[0] - 3.4, fy + 1.2], [ankle[0] - 2.6, fy], [ankle[0] + 2.6, fy], [ankle[0] + 3.4, fy + 1.2]]
    : [[ankle[0] + td * 5.5, fy + 1.6], [ankle[0] + td * 4.2, fy], [ankle[0] - td * 2.6, fy], [ankle[0] - td * 3.4, fy + 1.5]];
  // order so the outline goes down one side, round the paw, up the other
  const sideToe = td >= 0 ? R : L, sideHeel = td >= 0 ? L : R;
  const pts = [...sideHeel, ...[...pawFront].reverse(), ...[...sideToe].reverse()];
  return td >= 0 ? pts : [...sideToe, ...pawFront, ...[...sideHeel].reverse()];
}

function tailChain(root, a0, curl, wagA, seg) {
  const pts = [root]; let a = a0, p = root;
  for (let i = 0; i < D.tail.segs; i++) { a += (curl + wagA * 0.25) * Math.PI / 180; p = [p[0] + seg * Math.cos(a), p[1] + seg * Math.sin(a)]; pts.push(p); }
  return pts;
}
function ribbonOutline(c, widths) {
  const L = [], R = [];
  for (let i = 0; i < c.length; i++) {
    const a = c[Math.max(0, i - 1)], b = c[Math.min(c.length - 1, i + 1)];
    let tx = b[0] - a[0], ty = b[1] - a[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
    const w = widths[i] / 2;
    L.push([c[i][0] - ty * w, c[i][1] + tx * w]); R.push([c[i][0] + ty * w, c[i][1] - tx * w]);
  }
  return [...L, ...R.reverse()];
}

// ---------- head drawing (substitution from the sheet), returns screen geometry for measurement
function headPts(H, part, ear) {
  if (part === 'earNear' || part === 'earFar') return lerpPts(H[part].flat, H[part].prick, clamp(ear));
  return H[part];
}

/* P: {x, u, lie, crouch, h, pitch, head:'prof'|'back34'|'rear'|'front34', headFace:+1 left/-1 right, headFront,
       headPivot (optional override in display-local cm), ear, eye, brow, mouth, T, wag, t, feet (L gait), bob, tint} */
function drawDog(ctx, P) {
  const root = [sx(P.x), FLOOR - (P.bob || 0) * K];
  const L = bodyL(P.crouch, P.fam === 'L' || P.u < 1 ? P.lie : 0);
  let body, famA, famB, t;
  const u = P.u;
  const Q1 = () => bodyQ1(P.lie, false), Q2 = () => bodyQ1(P.lie, true);
  if (u <= 0) { body = L; famA = famB = 'L'; t = 0; }
  else if (u < 1) { body = mixBody(L, Q1(), u); famA = 'L'; famB = 'Q1'; t = u; }
  else if (u < 2) { body = mixBody(Q1(), bodyRV(), u - 1); famA = 'Q1'; famB = 'RV'; t = u - 1; }
  else if (u < 3) { body = mixBody(bodyRV(), Q2(), u - 2); famA = 'RV'; famB = 'Q2'; t = u - 2; }
  else { body = Q2(); famA = famB = 'Q2'; t = 0; }
  const fam = t < 0.5 ? famA : famB;
  const toS = p => [root[0] + p[0] * K, root[1] - p[1] * K];
  const toSs = pts => pts.map(toS);

  // legs: in-between the two views' leg placements
  const lA = legsOf(famA, famA === 'L' ? L : body, P.crouch, P.lie, P.feet), lB = legsOf(famB, famB === 'L' ? L : body, P.crouch, P.lie, P.feet);
  const legs = lA.map((a, i) => {
    const b = lB[i];
    const near = t < 0.5 ? a.near : b.near;
    return { root: mixP(a.root, b.root, t), foot: mixP(a.foot, b.foot, t), lift: lerp(a.lift, b.lift, t) + (P.turnLift ? P.turnLift[i] : 0), near, depth: lerp(a.depth, b.depth, t), fore: i < 2 };
  });
  const toeDirOf = f => f === 'L' || f === 'Q1' ? -1 : f === 'Q2' ? 1 : 0;
  const toeDir = toeDirOf(fam);
  const tint = P.tint || null;

  function drawLegs(nearPass) {
    for (const g of legs) {
      if ((g.near ? 1 : 0) !== nearPass) continue;
      const len = g.fore ? D.legs.len.fore : D.legs.len.hind, w = g.fore ? D.legs.width.fore : D.legs.width.hind;
      const side = (g.fore ? 1 : -1) * (fam === 'Q2' ? -1 : 1);
      const foot = [g.foot[0], g.foot[1] + g.lift];
      const knee = ik(g.root, [foot[0], foot[1] + 3.2], len[0], len[1], side, g.depth);
      if (knee[1] < 2.5) knee[1] = 2.5; // a folded leg rests on the boards, never through them
      const ol = legOutline(g.root, knee, g.foot, w, toeDir, g.lift);
      const pts = toSs(crSample(ol, true, 4));
      ink(ctx, pts, { fill: g.near ? PAL.coat : PAL.coatFar, line: PAL.coatLine, lw: 2.1, seed: g.fore ? 3 : 4, tex: 1, anchor: root, texA: 0.5 });
    }
  }
  // tail
  function drawTail() {
    const isL = fam === 'L';
    const aL = 30 - 110 * P.T, aQ = 40 - 140 * P.T;
    const wagA = (P.wag || 0) * 24 * Math.sin(2 * Math.PI * 2.1 * P.t);
    // Q2 is the mirror of Q1: angle a -> 180 - a, taken on the side nearest the unmirrored angle (no long-way swing)
    const mirA = a => { let m = 180 - a; while (m - a > 180) m -= 360; while (a - m > 180) m += 360; return m; };
    const wv = (f) => f === 'L' ? aL : (f === 'Q2' ? mirA(aQ) : aQ);
    let a0 = lerp(wv(famA), wv(famB), t) + wagA;
    let curl = (P.T > 0.8 ? -9 : 8) * (fam === 'Q2' ? -1 : 1);
    if (!isL && P.lie > 0) { // lying with its back turned: the tail curls round in front of the body, along the boards
      const s2 = fam === 'Q2' ? 1 : -1;
      a0 = lerp(a0, s2 > 0 ? -70 : -110, P.lie) + wagA * 0.3; curl = lerp(curl, 16 * s2, P.lie);
    }
    if (P.tailCurl !== undefined) curl = P.tailCurl;
    const r = body.pv.tail;
    const c = tailChain(r, a0 * Math.PI / 180, curl, isL ? 0 : 0, D.tail.len * (isL ? 1 : 0.85));
    const ol = ribbonOutline(c, D.tail.width);
    ink(ctx, toSs(crSample(ol, true, 4)), { fill: PAL.coat, line: PAL.coatLine, lw: 2.0, seed: 7, tex: 2, anchor: root });
    // cream tail tip
    const tip = c.slice(4), tipOl = ribbonOutline(tip, D.tail.width.slice(4));
    ink(ctx, toSs(crSample(tipOl, true, 4)), { fill: PAL.cream, line: PAL.coatLine, lw: 0, tex: null });
    return c;
  }
  // head
  const Hk = P.head || 'prof', H = D.heads[Hk];
  const hs = (Hk === 'prof' || Hk === 'front34') ? 1.15 : Hk === 'in34' ? 1.1 : 1.05;
  const nk = body.pv.neck;
  let pivot = P.headPivot;
  if (!pivot) {
    const h = P.h;
    const offL = h < 0.5 ? lp([-14, -14], [-13, 3], h / 0.5) : lp([-13, 3], [-8, 15], (h - 0.5) / 0.5);
    const offQ = lp([-5, -6], [-6, 8], h), offR = lp([0, -4], [0, 8], h);
    const offOf = f => f === 'L' ? offL : f === 'Q1' ? offQ : f === 'Q2' ? [-offQ[0], offQ[1]] : offR;
    const o = lp(offOf(famA), offOf(famB), t);
    pivot = [nk[0] + o[0], nk[1] + o[1]];
  }
  const hf = P.headFace === undefined ? (fam === 'Q2' ? -1 : 1) : P.headFace; // +1: the drawing as authored (muzzle left)
  const pr = (P.pitch || 0) * Math.PI / 180, cp = Math.cos(pr), sp = Math.sin(pr);
  // pitch > 0 drops the muzzle (authored frame faces left: rotate counter-clockwise in y-up), then face left/right
  const hT = p => { const x = p[0] * hs, y = p[1] * hs; const rx = x * cp - y * sp, ry = x * sp + y * cp; return toS([pivot[0] + hf * rx, pivot[1] + ry]); };
  function drawNeck() {
    const a = nk, b = pivot; let tx = b[0] - a[0], ty = b[1] - a[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
    const w0 = 9, w1 = 6.8;
    const pts = [[a[0] - ty * w0, a[1] + tx * w0], [lerp(a[0], b[0], .5) - ty * 8, lerp(a[1], b[1], .5) + tx * 8], [b[0] - ty * w1, b[1] + tx * w1],
                 [b[0] + tx * 3, b[1] + ty * 3], [b[0] + ty * w1, b[1] - tx * w1], [lerp(a[0], b[0], .5) + ty * 8.5, lerp(a[1], b[1], .5) - tx * 8.5], [a[0] + ty * w0, a[1] - tx * w0], [a[0] - tx * 4, a[1] - ty * 4]];
    ink(ctx, toSs(crSample(pts, true, 6)), { fill: PAL.coat, line: PAL.coatLine, lw: 2.1, seed: 9, tex: 0, anchor: root });
  }
  const geo = {};
  function drawHead() {
    const pc = part => crSample(headPts(H, part, P.ear), true, 8).map(hT);
    ink(ctx, pc('earFar'), { fill: PAL.ear, line: PAL.coatLine, lw: 1.9, seed: 11, tex: 1, anchor: root });
    const sk = crSample(H.skull, true, 8).map(hT);
    ink(ctx, sk, { fill: PAL.coat, line: PAL.coatLine, lw: 2.2, seed: 12, tex: 0, anchor: root });
    if (H.cream) ink(ctx, crSample(H.cream, true, 8).map(hT), { fill: PAL.cream, line: PAL.coatLine, lw: 0, tex: 2, anchor: root, texA: 0.35, pool: 0.12 });
    if (H.strokes) for (const s of H.strokes) brush(ctx, crSample(s, false, 8).map(hT), false, 1.6, PAL.coatLine, 13);
    if (H.nose) { const [nx, ny, rx, ry] = H.nose; const np = []; for (let k = 0; k < 16; k++) { const a = k / 16 * 6.283; np.push(hT([nx + rx * Math.cos(a), ny + ry * Math.sin(a)])); } ink(ctx, np, { fill: PAL.nose, line: PAL.nose, lw: 1, seed: 14, tex: null }); }
    const eo = P.eye === undefined ? 1 : P.eye;
    for (const e of H.eyes) {
      const [ex, ey, es] = e;
      if (eo < 0.15) { brush(ctx, [[ex - 2 * es, ey + 0.3], [ex, ey - 0.9], [ex + 2 * es, ey + 0.3]].map(hT), false, 1.7, PAL.eye, 15); continue; }
      const ep = []; for (let k = 0; k < 16; k++) { const a = k / 16 * 6.283; ep.push(hT([ex + 1.9 * es * Math.cos(a), ey + 1.5 * es * Math.min(eo, 1.25) * Math.sin(a)])); }
      ink(ctx, ep, { fill: PAL.eye, line: PAL.eye, lw: 0.8, seed: 16, tex: null });
      const hl = hT([ex - 0.6 * es * hf, ey + 0.5 * es]); ctx.fillStyle = 'rgba(255,240,210,0.9)'; ctx.beginPath(); ctx.arc(hl[0], hl[1], 0.9, 0, 6.283); ctx.fill();
      // upper lid line
      brush(ctx, [[ex - 2.3 * es, ey + 0.2], [ex - 0.3 * es, ey + 1.9 * es * Math.min(eo, 1.2)], [ex + 2.2 * es, ey + 0.9 * es]].map(hT), false, 1.6, PAL.coatLine, 17);
    }
    if (H.brow) { const bw = P.brow || 0; const b = [[H.brow[0][0], H.brow[0][1] + bw * 1.4], [H.brow[1][0], H.brow[1][1] - bw * 0.5]]; brush(ctx, crSample(b, false, 6).map(hT), false, 1.6, PAL.coatLine, 18); }
    if (H.mouth) { const m = H.mouth.map((p, i) => [p[0], p[1] - (i === 1 ? (P.mouth || 0) * 1.2 : 0)]); brush(ctx, crSample(m, false, 6).map(hT), false, 1.5, PAL.coatLine, 19); }
    ink(ctx, pc('earNear'), { fill: PAL.ear, line: PAL.coatLine, lw: 2.0, seed: 20, tex: 1, anchor: root });
    geo.skullC = hT(H.center); geo.tip = hT(H.tip); geo.pivot = toS(pivot);
    let cx = 0, cy = 0; for (const p of sk) { cx += p[0]; cy += p[1]; } geo.headC = [cx / sk.length, cy / sk.length];
    geo.headTop = Math.min(...sk.map(p => p[1]));
  }
  function drawTorso() {
    const o = toSs(body.outline);
    ink(ctx, o, { fill: PAL.coat, line: PAL.coatLine, lw: 2.3, seed: 21, tex: 0, anchor: root });
    if (body.bib) ink(ctx, toSs(crSample(resample(body.bib, 6, true), true, 8)), { fill: PAL.cream, line: PAL.coatLine, lw: 0, tex: 2, anchor: root, texA: 0.35, pool: 0.1 });
    for (const s of body.strokes) brush(ctx, toSs(s), false, 1.7, PAL.coatLine, 22);
    geo.backTop = Math.min(...o.map(p => p[1]));
  }
  const isL = fam === 'L';
  const headFront = P.headFront !== undefined ? P.headFront : isL;
  const tailFront = !isL;
  drawLegs(0);
  if (!tailFront) geo.tail = drawTail();
  if (!headFront) { drawNeck(); drawHead(); }
  if (headFront) drawNeck();
  drawLegs(1);
  drawTorso();
  if (tailFront) geo.tail = drawTail();
  if (headFront) drawHead();
  geo.fam = fam; geo.root = root;
  return geo;
}
if (typeof window !== 'undefined') Object.assign(window, { drawDog, bodyL });
