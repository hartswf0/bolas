// The person: a profile figure built from capsules, and a viseme sprite set for the mouth (profile shapes).
// The exposure sheet names a pose (reach, beckon, walk drawing, sit, push, low hand) and a viseme per frame.
const PERSON = (() => {
  const lerp = (a, b, t) => a + (b - a) * t, rad = d => d * Math.PI / 180;
  const VIS = { // jaw (0..1), lip gap (0..1), rounding (0..1), pressed (0/1), spread (0..1)
    X: [0.04, 0, 0, 0, 0], MBP: [0, 0, 0.1, 1, 0], AA: [1, 1, 0, 0, 0.2], OO: [0.45, 0.45, 1, 0, 0], EE: [0.3, 0.4, 0, 0, 1],
    R: [0.3, 0.3, 0.7, 0, 0], FV: [0.15, 0.12, 0, 0, 0], L: [0.5, 0.6, 0, 0, 0.3], TS: [0.15, 0.25, 0, 0, 0.6], KG: [0.5, 0.55, 0, 0, 0.2]
  };
  const PAL = { ink: '#120f12', coat: '#34405a', coatD: '#283148', trou: '#20263a', skin: '#c79473', hair: '#1c1513', shoe: '#141214', scarf: '#8b3a33', lip: '#8e4f45', mouth: '#2a0d10' };

  // joints in person-local metres (x forward, y up), origin = between the feet on the floor
  function joints(p) {
    const s = p.sit / 10, rch = p.rch / 10, bk = p.bk / 10, push = p.push / 10, low = p.low / 10, rest = (p.rest || 0) / 10;
    const lean = rad(p.lean * 4 + push * 22 + low * 30 * (1 - rest));
    const hip = [lerp(0, -0.06, s), lerp(0.92, 0.14, s)];
    const S = (a, l, from) => [from[0] + l * Math.cos(a), from[1] + l * Math.sin(a)];
    // torso
    const tA = rad(90) - lean - rad(4) * s;
    const sh = S(tA, 0.50, hip), nk = S(tA, 0.60, hip);
    // legs
    const legs = [];
    for (const side of [1, -1]) { // 1 = near leg
      let knee, ank;
      if (p.w >= 0 && s === 0) {
        const ph = (p.w / 8) * Math.PI * 2 + (side > 0 ? 0 : Math.PI);
        const a = rad(-90) + rad(24) * Math.sin(ph), kb = Math.max(0, Math.cos(ph)) * rad(30);
        knee = S(a, 0.44, hip); ank = S(a - kb, 0.42, knee);
      } else {
        const kneeS = [0.02 * side, 0.49], ankS = [0.03 + 0.03 * side, 0.07];
        const kneeT = side > 0 ? [0.21, 0.45] : [0.17, 0.47], ankT = side > 0 ? [0.26, 0.07] : [0.21, 0.07];
        const kneeM = [0.25, 0.42], ankM = [0.12, 0.07];   // crouching on the way down
        knee = s < 0.5 ? [lerp(kneeS[0], kneeM[0], s * 2), lerp(kneeS[1], kneeM[1], s * 2)] : [lerp(kneeM[0], kneeT[0], s * 2 - 1), lerp(kneeM[1], kneeT[1], s * 2 - 1)];
        ank = s < 0.5 ? [lerp(ankS[0], ankM[0], s * 2), 0.07] : [lerp(ankM[0], ankT[0], s * 2 - 1), 0.07];
      }
      legs.push({ side, hip, knee, ank, toe: [ank[0] + 0.13, Math.max(0.03, ank[1] - 0.04)] });
    }
    // arms: near arm acts, far arm hangs (or rests on the far knee when sitting)
    const arms = [];
    for (const side of [1, -1]) {
      let ua, fa;
      if (side > 0) {
        ua = lerp(rad(-96), rad(-4), rch); fa = lerp(rad(-92), rad(-8), rch);
        if (bk > 0) { ua = lerp(ua, rad(-80), bk); fa = lerp(fa, rad(-28), bk); }
        if (s > 0) { ua = lerp(ua, rad(-62), s); fa = lerp(fa, rad(-20), s); }
        if (push > 0) { ua = lerp(ua, rad(-2), push); fa = lerp(fa, rad(8), push); }
        if (low > 0) { ua = lerp(ua, rad(-28), low); fa = lerp(fa, rad(-52), low); }
        if (rest > 0) { ua = lerp(ua, rad(-40), rest); fa = lerp(fa, rad(-15), rest); }
        ua -= lean * 0.3; fa -= lean * 0.2;
      } else {
        ua = rad(-98) - lean; fa = rad(-90) - lean;
        if (s > 0) { ua = lerp(ua, rad(-35), s); fa = lerp(fa, rad(-50), s); }
      }
      const el = S(ua, 0.30, sh), wr = S(fa, 0.27, el), hd = S(fa, 0.08, wr);
      arms.push({ side, sh, el, wr, hd });
    }
    return { hip, sh, nk, legs, arms, tA };
  }

  // capsule list helpers (stroke-then-fill union)
  function cap(P, a, b, ra, rb) {
    const dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy) || 1e-6;
    const th = Math.atan2(dy, dx), be = Math.acos(Math.max(-1, Math.min(1, (ra - rb) / d)));
    P.moveTo(a[0] + ra, a[1]); P.arc(a[0], a[1], ra, 0, Math.PI * 2);
    P.moveTo(b[0] + rb, b[1]); P.arc(b[0], b[1], rb, 0, Math.PI * 2);
    const q = [[a[0] + ra * Math.cos(th + be), a[1] + ra * Math.sin(th + be)], [b[0] + rb * Math.cos(th + be), b[1] + rb * Math.sin(th + be)],
      [b[0] + rb * Math.cos(th - be), b[1] + rb * Math.sin(th - be)], [a[0] + ra * Math.cos(th - be), a[1] + ra * Math.sin(th - be)]];
    let ar = 0; for (let k = 0; k < 4; k++) ar += q[k][0] * q[(k + 1) % 4][1] - q[(k + 1) % 4][0] * q[k][1];
    const Q = ar < 0 ? q.reverse() : q; P.moveTo(...Q[0]); for (let k = 1; k < 4; k++) P.lineTo(...Q[k]); P.closePath();
  }
  function blob(ctx, P, fill, lw) { ctx.lineJoin = 'round'; ctx.strokeStyle = PAL.ink; ctx.lineWidth = lw * 2; ctx.stroke(P); ctx.fillStyle = fill; ctx.fill(P); }

  // draw in local metres; caller sets transform (scale K, flip for dir, y up -> down)
  function draw(ctx, p, K, id) {
    const J = joints(p), lw = 1.3 / K;
    const T = q => [q[0], -q[1]];   // y up -> canvas down (we draw in metres with y flipped)
    const P = () => new Path2D();
    const order = [];
    // far arm, far leg, torso+coat, near leg, head, near arm
    const farArm = J.arms[1], nearArm = J.arms[0], farLeg = J.legs[1], nearLeg = J.legs[0];
    const limb = (L, fill, r0, r1) => { const Q = P(); cap(Q, T(L.hip), T(L.knee), r0, r1); cap(Q, T(L.knee), T(L.ank), r1, 0.045); blob(ctx, Q, fill, lw);
      const S2 = P(); cap(S2, T(L.ank), T(L.toe), 0.045, 0.035); blob(ctx, S2, PAL.shoe, lw); };
    const arm = (A, fill) => { const Q = P(); cap(Q, T(A.sh), T(A.el), 0.055, 0.048); cap(Q, T(A.el), T(A.wr), 0.048, 0.038); blob(ctx, Q, fill, lw);
      const H = P(); cap(H, T(A.wr), T(A.hd), 0.034, 0.038); blob(ctx, H, PAL.skin, lw); };
    if (id) { // ID pass: only the mouth interior matters (measured), drawn by drawHead
      drawHead(ctx, p, J, lw, true); return;
    }
    arm(farArm, PAL.coatD);
    limb(farLeg, PAL.trou, 0.075, 0.06);
    // torso + coat skirt
    const Q = P(); cap(Q, T(J.hip), T(J.sh), 0.15, 0.16);
    const sk = p.sit / 10;
    if (sk < 0.6) { const kn = J.legs[0].knee, kf = J.legs[1].knee; const a = T(J.hip); const mk = T([(kn[0] + kf[0]) / 2, lerp((kn[1] + kf[1]) / 2 + 0.08, J.hip[1], sk)]);
      cap(Q, a, mk, 0.15, 0.13); }
    blob(ctx, Q, PAL.coat, lw);
    limb(nearLeg, PAL.trou, 0.075, 0.06);
    // neck and scarf
    const Nk = P(); cap(Nk, T(J.sh), T(J.nk), 0.06, 0.05); blob(ctx, Nk, PAL.skin, lw);
    const Sc = P(); cap(Sc, T([J.sh[0] + 0.01, J.sh[1] + 0.02]), T([J.sh[0] + 0.04, J.sh[1] + 0.06]), 0.075, 0.06); blob(ctx, Sc, PAL.scarf, lw);
    drawHead(ctx, p, J, lw, false);
    arm(nearArm, PAL.coat);
  }

  function drawHead(ctx, p, J, lw, id) {
    const HS = 1.25, v = VIS[p.vis] || VIS.X, em = 0.55 + 0.45 * (p.em || 0);
    const jaw = v[0] * em, gap = v[1] * em, rnd = v[2], press = v[3], spr = v[4];
    const tilt = rad((p.ht || 0) * -7) + (J.tA - Math.PI / 2) * 0.5;
    ctx.save();
    ctx.translate(J.nk[0], -J.nk[1]); ctx.rotate(-tilt); ctx.scale(HS, HS);
    const C = [0.0, -0.11];
    const pt = (x, y) => [x, -y];
    const piv = [-0.035, -0.03], ja = rad(20) * jaw;
    const rot = (q) => { const dx = q[0] - piv[0], dy = q[1] - piv[1], c = Math.cos(ja), s = Math.sin(ja); return [piv[0] + dx * c - dy * s, piv[1] + dx * s + dy * c]; };
    // face points (y up, relative to C) -> canvas
    const up = [[0.07, 0.07], [0.092, 0.03], [0.09, 0.012], [0.124, -0.024], [0.097, -0.036], [0.104 + 0.006 * rnd - 0.004 * spr, -0.048]];
    const stU = [0.098 + 0.009 * rnd - 0.006 * spr, -0.058 - 0.004 * press];
    const stL0 = [0.097 + 0.009 * rnd - 0.006 * spr, -0.060 - 0.022 * gap + 0.002 * press];
    const lo0 = [[0.101 + 0.007 * rnd, -0.071 - 0.012 * gap], [0.087, -0.084 - 0.012 * gap], [0.094, -0.101 - 0.012 * gap], [0.072, -0.122 - 0.01 * gap], [-0.02, -0.085]];
    const toC = q => [C[0] + q[0], C[1] - q[1]];
    const stL = rot(toC(stL0)), lo = lo0.map(q => rot(toC(q)));
    const face = new Path2D();
    const all = [toC([-0.02, 0.095]), ...up.map(toC), toC(stU), stL, ...lo, toC([-0.07, -0.03])];
    face.moveTo(...all[0]); for (const q of all.slice(1)) face.lineTo(...q); face.closePath();
    const skull = new Path2D(); skull.arc(C[0], C[1], 0.095, 0, Math.PI * 2);
    const mouth = new Path2D(); mouth.moveTo(...toC(stU)); mouth.lineTo(...toC([0.074, -0.06])); mouth.lineTo(...stL); mouth.closePath();
    if (id) { if (gap > 0.02 && !press) { ctx.fillStyle = '#00ffff'; ctx.fill(mouth); } ctx.restore(); return; }
    ctx.lineJoin = 'round'; ctx.strokeStyle = PAL.ink; ctx.lineWidth = lw * 2 / HS; ctx.stroke(skull); ctx.stroke(face);
    ctx.fillStyle = PAL.skin; ctx.fill(skull); ctx.fill(face);
    // hair cap
    ctx.save(); ctx.clip(skull); ctx.fillStyle = PAL.hair; ctx.beginPath(); ctx.arc(C[0] - 0.035, C[1] - 0.03, 0.1, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    ctx.fillStyle = PAL.hair; ctx.beginPath(); ctx.ellipse(C[0] - 0.05, C[1] - 0.01, 0.07, 0.085, 0.3, 0, Math.PI * 2); ctx.fill();
    // ear, eye, brow
    ctx.fillStyle = PAL.skin; ctx.strokeStyle = PAL.ink; ctx.lineWidth = lw / HS; ctx.beginPath(); ctx.ellipse(C[0] - 0.005, C[1] + 0.005, 0.017, 0.026, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = PAL.ink; ctx.beginPath(); ctx.ellipse(C[0] + 0.07, C[1] - 0.012, 0.009, 0.006, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(C[0] + 0.055, C[1] - 0.03); ctx.lineTo(C[0] + 0.088, C[1] - 0.034); ctx.lineWidth = lw * 1.4 / HS; ctx.stroke();
    // mouth: interior when open, lips line always
    if (gap > 0.02 && !press) { ctx.fillStyle = PAL.mouth; ctx.fill(mouth); }
    ctx.strokeStyle = PAL.lip; ctx.lineWidth = lw * (press ? 2.2 : 1.2) / HS;
    ctx.beginPath(); ctx.moveTo(...toC([0.074, -0.06])); ctx.lineTo(...toC(stU)); ctx.stroke();
    ctx.restore();
  }
  // mouth point in local metres (for the sound marks)
  function mouthAt(p) {
    const J = joints(p), HS = 1.25, th = -(rad((p.ht || 0) * -7) + (J.tA - Math.PI / 2) * 0.5);
    const lx = 0.105 * HS, ly = (-0.11 + 0.058) * HS, c = Math.cos(th), s = Math.sin(th);
    const X = lx * c - ly * s, Y = lx * s + ly * c;
    return [J.nk[0] + X, J.nk[1] - Y];
  }
  return { draw, joints, mouthAt, VIS };
})();
if (typeof module !== 'undefined') module.exports = PERSON;
