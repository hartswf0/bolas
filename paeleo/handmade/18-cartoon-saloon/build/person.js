/* SCION 18 · the person: two authored drawings (standing, sitting) in-betweened, a selectively rigged near arm
   (two bones to a hand target: rest, reach, low), a head placed at the neck pivot. Faces right, toward the dog. */
'use strict';
const PS = SHEET.person;
const PN = 90;
const pd = {};
function pz(pose, part) { const k = pose + part; if (!pd[k]) pd[k] = resample(crSample(PS[pose][part], true, 8), PN, true); return pd[k]; }
function personX(x) { return 0.25 + (x + 0.28) * 1.443; } // score person x (doorway -0.28 -> 0.25, beside -1.25 -> -1.15) on this film's floor
function rotAbout(p, c, a) { const dx = p[0] - c[0], dy = p[1] - c[1], ca = Math.cos(a), sa = Math.sin(a); return [c[0] + dx * ca - dy * sa, c[1] + dx * sa + dy * ca]; }

/* Q: {x (score), sit, reach, low, mouth, lean (deg, + toward the dog), nod (deg), blink, bob} */
function drawPerson(ctx, Q) {
  const rootX = sx(personX(Q.x)), rootY = FLOOR - (Q.bob || 0) * K;
  const toS = p => [rootX + p[0] * K, rootY - p[1] * K];
  const s = Q.sit;
  const A = PS.stand, B = PS.sit;
  const waist = lp([0, 100], [0, 62], s);
  const lean = -(Q.lean || 0) * Math.PI / 180; // clockwise in y-up tips the top toward +x (the dog)
  const up = p => rotAbout(p, waist, lean);
  const dress = lerpPts(pz('stand', 'dress'), pz('sit', 'dress'), s);
  const bodice = lerpPts(pz('stand', 'bodice'), pz('sit', 'bodice'), s).map(up);
  const shawl = lerpPts(pz('stand', 'shawl'), pz('sit', 'shawl'), s).map(up);
  const neck = up(lp(A.neck, B.neck, s)), shN = up(lp(A.shoulderN, B.shoulderN, s)), shF = up(lp(A.shoulderF, B.shoulderF, s));
  const shoe = lp(A.shoe, B.shoe, s);
  const anchor = [rootX, rootY];
  // far arm (behind)
  const handF = lp(A.handF, B.handF, s);
  drawArm(ctx, toS, shF, handF, -1, PAL.dressLine, '#244a47');
  ink(ctx, toS2(toS, crSample([[shoe[0] - 6, 0.5], [shoe[0] + 7, 0.5], [shoe[0] + 5, 4], [shoe[0] - 5, 4.5]], true, 4)), { fill: '#2b1d17', line: '#120b08', lw: 1.5, seed: 200, tex: null });
  ink(ctx, dress.map(toS), { fill: PAL.dress, line: PAL.dressLine, lw: 2.2, seed: 201, tex: 0, anchor });
  // embroidered hem band (a running spiral, clipped to the dress)
  ctx.save(); polyPath(ctx, dress.map(toS)); ctx.clip();
  const hy = toS([0, 12])[1];
  ctx.fillStyle = 'rgba(169,69,46,0.85)'; ctx.fillRect(rootX - 60 * K, hy - 5, 140 * K, 10);
  for (let k = -6; k < 12; k++) spiral(ctx, rootX + k * 11, hy, 4, 1.2, k, 'rgba(230,190,120,0.9)', 1.1, 210 + k);
  ctx.restore();
  ink(ctx, bodice.map(toS), { fill: '#28524f', line: PAL.dressLine, lw: 2.0, seed: 202, tex: 1, anchor });
  ink(ctx, shawl.map(toS), { fill: PAL.shawl, line: PAL.shawlLine, lw: 2.0, seed: 203, tex: 2, anchor });
  // head
  const HD = PS.head, ha = -((Q.nod || 0)) * Math.PI / 180 + lean;
  const hT = p => toS(rotAbout([neck[0] + p[0], neck[1] + 4 + p[1]], [neck[0], neck[1] + 4], ha));
  ink(ctx, crSample(HD.face, true, 8).map(hT), { fill: PAL.skin, line: PAL.skinLine, lw: 1.8, seed: 204, tex: 2, texA: 0.35, anchor });
  ink(ctx, crSample(HD.hair, true, 8).map(hT), { fill: PAL.hair, line: '#150c09', lw: 1.6, seed: 205, tex: 1, anchor });
  const bp = []; for (let k = 0; k < 16; k++) { const a = k / 16 * 6.283; bp.push(hT([HD.bun[0] + HD.bun[2] * Math.cos(a), HD.bun[1] + HD.bun[2] * Math.sin(a)])); }
  ink(ctx, bp, { fill: PAL.hair, line: '#150c09', lw: 1.6, seed: 206, tex: 1 });
  const e = HD.eye;
  if ((Q.blink || 0) > 0.5) brush(ctx, [[e[0] - 1.6, e[1]], [e[0] + 1.6, e[1] - 0.2]].map(hT), false, 1.5, '#1b100b', 207);
  else { const ep = hT(e); ctx.fillStyle = '#1b100b'; ctx.beginPath(); ctx.ellipse(ep[0], ep[1], 1.6, 2.0, 0, 0, 6.283); ctx.fill(); }
  brush(ctx, HD.brow.map(hT), false, 1.4, '#2a1a12', 208);
  const m = HD.mouth, mo = Q.mouth || 0;
  if (mo > 0.08) { const mp = []; for (let k = 0; k < 12; k++) { const a = k / 12 * 6.283; mp.push(hT([m[0] + 1.4 * Math.cos(a), m[1] + 1.8 * mo * Math.sin(a)])); } ink(ctx, mp, { fill: '#5a1f17', line: '#2a0f0b', lw: 1, seed: 209, tex: null }); }
  else brush(ctx, [[m[0] - 1.8, m[1] + 0.3], [m[0] + 0.6, m[1]]].map(hT), false, 1.3, PAL.skinLine, 209);
  // near arm (the selectively rigged part)
  const rest = lp(A.hand, B.hand, s);
  const reachT = [shN[0] + 50, shN[1] + 2];
  let hand = lp(rest, reachT, Q.reach || 0);
  hand = lp(hand, B.hand, (Q.low || 0) * s);
  drawArm(ctx, toS, shN, hand, 1, PAL.shawlLine, PAL.shawl, Q.low > 0.5);
  return { root: [rootX, rootY], hand: toS(hand), head: hT([2, 8]) };
}
function toS2(toS, pts) { return pts.map(toS); }
function drawArm(ctx, toS, sh, hand, near, line, fill, palmUp) {
  const l1 = PS.arm.len[0], l2 = PS.arm.len[1];
  const elbow = ik(sh, hand, l1, l2, -1, 1);
  const w = PS.arm.width;
  const segs = [[sh[0], sh[1] + 3], sh, elbow, hand], ws = [w[0], w[0], w[1], w[2]];
  const L = [], R = [];
  for (let i = 0; i < segs.length; i++) {
    const a = segs[Math.max(0, i - 1)], b = segs[Math.min(3, i + 1)];
    let tx = b[0] - a[0], ty = b[1] - a[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
    L.push([segs[i][0] - ty * ws[i] / 2, segs[i][1] + tx * ws[i] / 2]); R.push([segs[i][0] + ty * ws[i] / 2, segs[i][1] - tx * ws[i] / 2]);
  }
  ink(ctx, crSample([...L, ...R.reverse()], true, 5).map(toS), { fill, line, lw: 1.9, seed: 220 + near, tex: 2 });
  // hand: when offered low it is an open palm, turned up and held level toward the dog, with a pale cuff so it reads apart from the sleeve
  let dir = Math.atan2(hand[1] - elbow[1], hand[0] - elbow[0]);
  const sc = palmUp ? 1.55 : 1;
  if (palmUp) dir = dir * 0.25;
  const shape = palmUp ? [[-1, -2.4], [4, -3], [9, -2.6], [12, -1.4], [12.6, 0.2], [9.4, 0.7], [9.8, 1.9], [6.2, 1.5], [3.4, 4.2], [1.4, 2.4], [-1, 2.4]]
                       : [[0, -2.4], [5.5, -2.2], [7.5, 0], [5.5, 2.2], [1, 2.6], [2.5, 4.6], [-1, 2.8]];
  const rot = p => { const c = Math.cos(dir), s2 = Math.sin(dir); return [hand[0] + sc * (p[0] * c - p[1] * s2), hand[1] + sc * (p[0] * s2 + p[1] * c)]; };
  ink(ctx, crSample(shape.map(rot), true, 5).map(toS), { fill: PAL.skin, line: PAL.skinLine, lw: 1.7, seed: 230 + near, tex: null });
  if (palmUp) brush(ctx, [[-1.5, -3], [-1.2, 3]].map(rot).map(toS), false, 3, '#efd9ad', 232);
}
if (typeof window !== 'undefined') Object.assign(window, { drawPerson, personX });
