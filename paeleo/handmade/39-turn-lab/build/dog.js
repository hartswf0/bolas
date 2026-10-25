/* SCION 39 · Turn Lab — the dog.
   A drawing atlas of discrete views (not a 3D model). Native formal language:
     ORIENTATION STATES  body views V0 (profile, facing the door), V45 (rear three-quarter), V90 (rear);
                         V135 / V180 are the same drawings flipped (the dog is drawn symmetric: saddle, collar, tail).
                         head views H-45 (front three-quarter), H0 (profile), H45 (rear three-quarter), H90 (rear);
                         H135 / H180 / H-135 are flips. A view is chosen by SUBSTITUTION, never by squashing one drawing.
     VIEW-SPECIFIC PIVOTS neck base, neck joint, tail root, shoulders, hips: placed in every view from one set of canonical
                         dog dimensions (RIG, metres), so the head stays attached and nothing changes scale at a swap.
     TOPOLOGY CORRESPONDENCES every part has the same id in every view (torso, saddle, collar, tail, ear_n, ear_f, eye_n …);
                         a part that a view cannot show is listed as hidden, not faked.
     DRAWING ATLAS       VIEWS and HEADS below: hand-placed outline points (Catmull-Rom closed curves), one drawing per view,
                         a standing and a lying drawing with the same point count (so lying is a safe in-view interpolation).
     TURN CHOREOGRAPHY   lives in controller.js: head leads, body follows, feet step at each swap.
   Units: metres, dog-local, y up, origin on the ground under the body centre. Screen-local x is lateral (left = toward the door). */
(function (G) {
  'use strict';
  const K = 0.25;                     // the porch floor's oblique: screen rise per metre of depth (camera a little above)
  const D2R = Math.PI / 180;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smooth = t => { t = clamp(t); return t * t * (3 - 2 * t); };
  const L2 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];

  // project a dog-local 3D point (X back, Y up, Z camera side when in profile) for a body yaw th → [x, y, depth]
  function proj(th, X, Y, Z) {
    const c = Math.cos(th * D2R), s = Math.sin(th * D2R);
    const u = X * c - Z * s, d = X * s + Z * c;
    return [u, Y - K * d, d];
  }

  // ---- canonical dimensions (the pivot alignment engineer's table): standing and lying, w = 0 fore … 1 hind
  const RIG = {
    B: { s: [-0.33, 0.50, 0], l: [-0.31, 0.29, 0], w: 0 },     // neck base
    T: { s: [0.40, 0.51, 0], l: [0.42, 0.19, 0], w: 1 },       // tail root
    S: { s: [-0.29, 0.40, 0.09], l: [-0.28, 0.16, 0.10], w: 0 }, // shoulder pivot (±Z)
    H: { s: [0.31, 0.44, 0.09], l: [0.28, 0.17, 0.12], w: 1 },   // hip pivot (±Z)
  };
  const NECK = 0.21;
  const FOOT_LIE = { fore: [-0.62, 0.02, 0.07], hind: [0.02, 0.02, 0.17] };
  const LEGS = [
    { id: 'hf', type: 'hind', side: -1 }, { id: 'ff', type: 'fore', side: -1 },
    { id: 'hn', type: 'hind', side: 1 }, { id: 'fn', type: 'fore', side: 1 }];

  // ---- the drawing atlas: torso outlines per body view. [x, y, w]; lie lists have the same count (correspondence)
  const VIEWS = {
    0: {
      torso: [[-0.40, 0.50, 0], [-0.425, 0.40, 0], [-0.36, 0.30, 0], [-0.20, 0.262, 0.15], [0.03, 0.295, 0.5], [0.19, 0.345, 0.8],
        [0.29, 0.305, 1], [0.40, 0.33, 1], [0.445, 0.44, 1], [0.39, 0.525, 1], [0.16, 0.535, 0.75], [-0.10, 0.556, 0.3],
        [-0.24, 0.588, 0], [-0.345, 0.572, 0]],
      saddle: [[-0.25, 0.60, 0], [-0.05, 0.575, 0.3], [0.20, 0.545, 0.8], [0.40, 0.53, 1], [0.37, 0.44, 1], [0.18, 0.43, 0.75],
        [-0.02, 0.45, 0.4], [-0.21, 0.49, 0]],
      pale: [[-0.43, 0.53, 0], [-0.445, 0.38, 0], [-0.37, 0.28, 0], [-0.27, 0.27, 0], [-0.30, 0.39, 0], [-0.33, 0.49, 0]],
      lines: [[[0.17, 0.36], [0.20, 0.44], [0.29, 0.49]], [[-0.27, 0.30], [-0.26, 0.36]]],
    },
    45: {
      torso: [[0.10, 0.17, 0.9], [-0.01, 0.27, 0.6], [-0.14, 0.29, 0.2], [-0.28, 0.36, 0], [-0.30, 0.47, 0], [-0.28, 0.56, 0],
        [-0.235, 0.62, 0], [-0.16, 0.648, 0], [0.02, 0.585, 0.4], [0.18, 0.515, 0.8], [0.29, 0.47, 1], [0.355, 0.40, 1],
        [0.36, 0.29, 1], [0.31, 0.19, 1], [0.235, 0.155, 1], [0.17, 0.14, 1]],
      lie: [[0.10, 0.00], [-0.02, 0.06], [-0.15, 0.10], [-0.29, 0.14], [-0.31, 0.24], [-0.29, 0.32], [-0.24, 0.375], [-0.16, 0.405],
        [0.02, 0.34], [0.18, 0.27], [0.29, 0.215], [0.36, 0.15], [0.36, 0.06], [0.31, 0.0], [0.235, -0.02], [0.17, -0.02]],
      saddle: [[-0.17, 0.665, 0], [0.02, 0.60, 0.4], [0.19, 0.53, 0.8], [0.31, 0.48, 1], [0.26, 0.42, 1], [0.09, 0.46, 0.6],
        [-0.07, 0.51, 0.3], [-0.24, 0.575, 0]],
      saddleLie: [[-0.17, 0.42], [0.02, 0.355], [0.19, 0.285], [0.31, 0.225], [0.26, 0.17], [0.09, 0.22], [-0.07, 0.27], [-0.24, 0.335]],
      pale: null,
      lines: [[[0.12, 0.19], [0.115, 0.29], [0.19, 0.40]]],
      linesLie: [[[0.12, 0.01], [0.11, 0.10], [0.18, 0.19]]],
    },
    90: {
      torso: symm([0, 0.16, 1], [[0.06, 0.10, 1], [0.13, 0.12, 1], [0.168, 0.22, 1], [0.165, 0.36, 1], [0.15, 0.44, 0.9],
        [0.165, 0.52, 0.5], [0.145, 0.60, 0.2], [0.11, 0.65, 0], [0.055, 0.675, 0]]),
      lie: symm([0, 0.05], [[0.07, 0.0], [0.17, 0.0], [0.21, 0.08], [0.20, 0.17], [0.172, 0.23], [0.175, 0.29], [0.15, 0.345],
        [0.105, 0.39], [0.05, 0.41]]),
      saddle: symm([0, 0.425, 1], [[0.06, 0.428, 1], [0.11, 0.445, 1], [0.135, 0.53, 0.5], [0.105, 0.62, 0], [0.055, 0.69, 0]]),
      saddleLie: symm([0, 0.17], [[0.06, 0.172], [0.12, 0.19], [0.15, 0.28], [0.11, 0.37], [0.05, 0.425]]),
      pale: null,
      lines: [[[-0.11, 0.12], [-0.075, 0.25], [-0.02, 0.33]], [[0.11, 0.12], [0.075, 0.25], [0.02, 0.33]]],
      linesLie: [[[-0.15, 0.02], [-0.11, 0.09], [-0.05, 0.12]], [[0.15, 0.02], [0.11, 0.09], [0.05, 0.12]]],
    },
  };
  function symm(c, R) { const M = R.slice().reverse().map(p => [-p[0], p[1], p[2]]); return [c, ...R, ...M]; }

  // ---- head atlas (head-local, origin at the neck joint; profile drawings face left)
  const HEADS = {
    0: {
      skull: [[0.05, 0.00], [0.035, 0.07], [-0.035, 0.108], [-0.105, 0.09], [-0.15, 0.058], [-0.225, 0.038], [-0.268, 0.024],
        [-0.278, -0.006], [-0.245, -0.036], [-0.17, -0.052], [-0.08, -0.076], [0.012, -0.062]],
      mask: [[-0.185, 0.05], [-0.272, 0.024], [-0.27, -0.02], [-0.21, -0.044], [-0.165, 0.00]],
      pale: [[-0.04, -0.03], [-0.13, -0.05], [-0.06, -0.078], [0.02, -0.06]],
      nose: [-0.268, 0.004, 0.022, 0.017], mouth: [[-0.255, -0.03], [-0.205, -0.042], [-0.155, -0.036]],
      eyes: [[-0.112, 0.046, 0.022, 0.012, 1]],
      brows: [[-0.105, 0.072, 0.011]],
      ears: { far: { b1: [-0.075, 0.088], b2: [-0.012, 0.102], up: [-0.045, 0.215], flat: [0.085, 0.118] },
        near: { b1: [-0.04, 0.094], b2: [0.03, 0.074], up: [0.012, 0.232], flat: [0.135, 0.098] } },
      pitch: 1, inner: false,
    },
    '-45': {
      skull: [[0.06, 0.00], [0.062, 0.07], [0.012, 0.118], [-0.07, 0.118], [-0.13, 0.082], [-0.18, 0.045], [-0.208, 0.012],
        [-0.196, -0.03], [-0.14, -0.06], [-0.05, -0.08], [0.032, -0.06]],
      mask: [[-0.13, 0.05], [-0.205, 0.015], [-0.19, -0.035], [-0.12, -0.05], [-0.10, 0.0]],
      pale: [[0.04, -0.03], [-0.03, -0.075], [-0.10, -0.06], [-0.02, -0.02]],
      nose: [-0.193, 0.012, 0.028, 0.02], mouth: [[-0.19, -0.03], [-0.15, -0.048], [-0.10, -0.045]],
      eyes: [[-0.045, 0.052, 0.02, 0.012, 1], [-0.125, 0.056, 0.015, 0.01, 0.8]],
      brows: [[-0.04, 0.076, 0.01], [-0.12, 0.078, 0.008]],
      ears: { far: { b1: [-0.10, 0.10], b2: [-0.04, 0.116], up: [-0.115, 0.232], flat: [-0.02, 0.148] },
        near: { b1: [0.0, 0.112], b2: [0.06, 0.07], up: [0.075, 0.228], flat: [0.15, 0.11] } },
      pitch: 0.6, inner: true,
    },
    45: {
      skull: [[0.06, 0.00], [0.062, 0.062], [0.022, 0.104], [-0.045, 0.112], [-0.098, 0.088], [-0.152, 0.064], [-0.186, 0.048],
        [-0.184, 0.022], [-0.13, 0.002], [-0.085, -0.04], [0.0, -0.056]],
      mask: [[-0.15, 0.064], [-0.186, 0.046], [-0.18, 0.02], [-0.145, 0.01]],
      pale: null,
      nose: [-0.18, 0.042, 0.012, 0.012], mouth: null,
      eyes: [], brows: [],
      ears: { far: { b1: [-0.105, 0.092], b2: [-0.045, 0.11], up: [-0.088, 0.222], flat: [-0.02, 0.14] },
        near: { b1: [-0.012, 0.106], b2: [0.058, 0.066], up: [0.048, 0.218], flat: [0.13, 0.09] } },
      pitch: 0.6, inner: false, earsFront: true,
    },
    90: {
      skull: [[0.075, 0.00], [0.072, 0.066], [0.032, 0.104], [-0.032, 0.104], [-0.072, 0.066], [-0.075, 0.00], [-0.05, -0.05],
        [0.05, -0.05]],
      mask: null, pale: null, nose: null, mouth: null, eyes: [], brows: [],
      ears: { far: { b1: [-0.07, 0.06], b2: [-0.02, 0.10], up: [-0.077, 0.212], flat: [-0.122, 0.072] },
        near: { b1: [0.02, 0.10], b2: [0.07, 0.06], up: [0.077, 0.212], flat: [0.122, 0.072] } },
      pitch: 0, inner: false, earsFront: true,
    },
  };
  // which drawing and whether flipped, for a world head yaw (deg)
  function headKey(yaw) {
    let y = ((yaw % 360) + 540) % 360 - 180;           // (-180, 180]
    const keys = [-135, -45, 0, 45, 90, 135, 180, -180];
    let best = 0, bd = 1e9; for (const k of keys) { const d = Math.abs(y - k); if (d < bd) { bd = d; best = k; } }
    if (best === -180) best = 180;
    const map = { '-135': ['-45', true], '-45': ['-45', false], 0: ['0', false], 45: ['45', false], 90: ['90', false], 135: ['45', true], 180: ['0', true] };
    return { key: map[best][0], flip: map[best][1], snapped: best };
  }
  function bodyKey(th) { const map = { 0: [0, false], 45: [45, false], 90: [90, false], 135: [45, true], 180: [0, true] }; return { key: map[th][0], flip: map[th][1] }; }

  // ---- small geometry
  function noise(seed) { let x = Math.sin(seed * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
  function jit(pts, seed, amp) {
    if (!amp) return pts;
    return pts.map((p, i) => [p[0] + (noise(seed + i * 7.3) - 0.5) * 2 * amp, p[1] + (noise(seed + i * 3.1 + 99) - 0.5) * 2 * amp]);
  }
  function crClosed(ctx, P) {             // closed Catmull-Rom through P
    const n = P.length; ctx.moveTo(P[0][0], P[0][1]);
    for (let i = 0; i < n; i++) {
      const p0 = P[(i - 1 + n) % n], p1 = P[i], p2 = P[(i + 1) % n], p3 = P[(i + 2) % n];
      ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1]);
    }
    ctx.closePath();
  }
  function crOpen(ctx, P) {
    const n = P.length; ctx.moveTo(P[0][0], P[0][1]);
    for (let i = 0; i < n - 1; i++) {
      const p0 = P[Math.max(0, i - 1)], p1 = P[i], p2 = P[i + 1], p3 = P[Math.min(n - 1, i + 2)];
      ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1]);
    }
  }
  // a tapered tube along a polyline: returns left and right edges
  function tube(pts, widths) {
    const L = [], R = [];
    for (let i = 0; i < pts.length; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      let dx = b[0] - a[0], dy = b[1] - a[1]; const m = Math.hypot(dx, dy) || 1; dx /= m; dy /= m;
      const w = widths[i] / 2; L.push([pts[i][0] - dy * w, pts[i][1] + dx * w]); R.push([pts[i][0] + dy * w, pts[i][1] - dx * w]);
    }
    return { L, R };
  }
  function ik2(P, F, l1, l2, pick) {     // 2-bone IK in a plane; both solutions, the one with the lower pick() score wins
    let dx = F[0] - P[0], dy = F[1] - P[1]; let d = Math.hypot(dx, dy) || 1e-6;
    const dd = Math.min(d, l1 + l2 - 1e-4); const ux = dx / d, uy = dy / d;
    const a = Math.acos(clamp((l1 * l1 + dd * dd - l2 * l2) / (2 * l1 * dd), -1, 1));
    const nx = -uy, ny = ux;   // perpendicular
    const J = sg => [P[0] + l1 * (ux * Math.cos(a) + nx * Math.sin(a) * sg), P[1] + l1 * (uy * Math.cos(a) + ny * Math.sin(a) * sg)];
    const A = J(1), Bq = J(-1); return pick(A) <= pick(Bq) ? A : Bq;
  }

  // ---- pose → the drawing, in screen-local metres (x lateral, y up). Returns a list of parts with depth keys.
  // pose: { body (0|45|90|135|180), headYaw (deg, world), alpha (neck deg), beta (head pitch deg), ear (0..1), earFlick,
  //         blink (0..1), lie (0..1), crouch (0..1), tail (score scale 0 high … 1.35 tucked), wag, wagPh, feet: {id: [X,Y,Z]} dog-local,
  //         lift: {id: 0..1}, bob, breath, seed }
  function build(pose) {
    const th = pose.body, bk = bodyKey(th), V = VIEWS[bk.key], fx = bk.flip ? -1 : 1;
    const lie = pose.lie || 0, cr = pose.crouch || 0;
    const lieH = smooth(lie * 1.7), lieF = smooth((lie - 0.35) / 0.65);
    const ph = w => lerp(lieF, lieH, w);
    const dyCrouch = w => -(lerp(0.075, 0.13, w)) * cr + (pose.bob || 0);
    const breath = (pose.breath || 0);
    const rig = {};
    for (const k in RIG) {
      const r = RIG[k], t = ph(r.w);
      rig[k] = [lerp(r.s[0], r.l[0], t), lerp(r.s[1], r.l[1], t) + dyCrouch(r.w) * (1 - t), lerp(r.s[2], r.l[2], t)];
    }
    const shape = (st, li) => st.map((p, i) => {
      const w = p[2] === undefined ? 0.5 : p[2], t = li ? ph(w) : 0;
      const q = li ? L2(p, li[i], t) : [p[0], p[1]];
      return [q[0] * fx, q[1] + dyCrouch(w) * (1 - t) + breath * (1 - w) * (q[1] > 0.2 ? 1 : 0)];
    });
    const parts = [];
    // torso, saddle, pale chest, detail lines
    const torso = shape(V.torso, V.lie), saddle = shape(V.saddle, V.saddleLie);
    const pale = V.pale ? shape(V.pale, null) : null;
    const lines = (lie > 0.5 && V.linesLie ? V.linesLie : V.lines).map(l => l.map(p => [p[0] * fx, p[1] + dyCrouch(0.8) * (1 - lieH)]));
    parts.push({ id: 'torso', key: 0, torso, saddle, pale, lines });
    // legs
    for (const leg of LEGS) {
      const piv3 = leg.type === 'fore' ? rig.S : rig.H;
      const P3 = [piv3[0], piv3[1], piv3[2] * leg.side];
      let F3 = (pose.feet && pose.feet[leg.id]) ? pose.feet[leg.id].slice() : [leg.type === 'fore' ? -0.29 : 0.33, 0, 0.08 * leg.side];
      const fl = FOOT_LIE[leg.type], tl = leg.type === 'fore' ? lieF : lieH;
      F3 = [lerp(F3[0], fl[0], tl), lerp(F3[1], fl[1], tl), lerp(F3[2], fl[2] * leg.side, tl)];
      F3[1] += 0.07 * ((pose.lift && pose.lift[leg.id]) || 0);
      let joints3;
      if (leg.type === 'fore') {
        const J = ik2([P3[0], P3[1]], [F3[0], F3[1]], 0.20, 0.215, q => -q[0] * (1 - tl) + q[1] * tl * 2);
        joints3 = [P3, [J[0], J[1], lerp(P3[2], F3[2], 0.5)], F3];
      } else {
        const md = [lerp(0.26, 1, tl), lerp(1, 0.06, tl)]; const mm = Math.hypot(md[0], md[1]);
        const Hk = [F3[0] + 0.13 * md[0] / mm, F3[1] + 0.13 * md[1] / mm];
        const J = ik2([P3[0], P3[1]], Hk, 0.21, 0.22, q => q[0] * (1 - tl) + q[1] * tl * 2);
        joints3 = [P3, [J[0], J[1], lerp(P3[2], F3[2], 0.4)], [Hk[0], Hk[1], lerp(P3[2], F3[2], 0.85)], F3];
      }
      if (leg.type === 'hind' && tl > 0.55) {
        // lying: the hind leg is a different drawing — a haunch on the ground and the hock laid flat (substitution, not a fold)
        const hc = [P3[0] - 0.07, P3[1] - 0.045, P3[2] + 0.03 * leg.side];
        const pc = proj(th, hc[0], hc[1], hc[2]);
        const hk = proj(th, P3[0] - 0.11, 0.035, F3[2]), pw2 = proj(th, F3[0], F3[1] + 0.012, F3[2]);
        const ax = proj(th, hc[0] + 0.15, hc[1], hc[2]);
        const mid = proj(th, hc[0], hc[1], 0)[2], isNear = pc[2] >= mid;
        parts.push({ id: 'haunch_' + leg.id, key: isNear ? 0.3 : -0.3, near: isNear, c: [pc[0], pc[1]],
          rx: Math.max(0.07, Math.hypot(ax[0] - pc[0], ax[1] - pc[1])), ry: 0.095, low: [[hk[0], hk[1]], [pw2[0], pw2[1]]] });
        continue;
      }
      const pj = joints3.map(j => proj(th, j[0], j[1], j[2]));
      const paw3 = [F3[0] - 0.025, F3[1] + 0.016, F3[2]];
      const pw = proj(th, paw3[0], paw3[1], paw3[2]);
      const toe = proj(th, F3[0] - 0.07, F3[1] + 0.01, F3[2]);
      parts.push({ id: 'leg_' + leg.id, key: pj[0][2] * 0.9 + 0.001 * leg.side, leg: leg.type, near: pj[0][2] > -0.02 || (th === 90 && leg.type === 'hind'),
        pts: pj.map(p => [p[0], p[1]]), widths: leg.type === 'fore' ? [0.09, 0.06, 0.048] : [0.15, 0.10, 0.058, 0.05],
        paw: [pw[0], pw[1]], toe: [toe[0], toe[1]], lifted: (pose.lift && pose.lift[leg.id]) || 0 });
    }
    // neck + head
    const Bs = proj(th, rig.B[0], rig.B[1], rig.B[2]);
    const a = (pose.alpha === undefined ? 45 : pose.alpha) * D2R, hy = pose.headYaw * D2R;
    const Nw = [Bs[0] + NECK * Math.cos(a) * -Math.cos(hy), 0, 0];
    const Ndepth = Bs[2] + NECK * Math.cos(a) * -Math.sin(hy);
    const NY = (rig.B[1]) + NECK * Math.sin(a);
    const Ns = [Nw[0], NY - K * Ndepth];
    const hk = headKey(pose.headYaw);
    parts.push({ id: 'neck', key: Math.min(Ndepth + 0.04, -0.0005), B: [Bs[0], Bs[1]], N: Ns });
    parts.push({ id: 'head', key: Ndepth + 0.04, B: [Bs[0], Bs[1]], N: Ns, hk, beta: pose.beta || 0, ear: pose.ear === undefined ? 1 : pose.ear,
      earFlick: pose.earFlick || 0, blink: pose.blink || 0, lie });
    // tail: three segments drooping, lateral wag in the body's Z
    const Ts = proj(th, rig.T[0], rig.T[1], rig.T[2]);
    const phi0 = (25 - 95 * (pose.tail === undefined ? 0.5 : pose.tail)) * D2R;
    const wz = Math.sin(pose.wagPh || 0) * (pose.wag || 0) * 0.9;
    const tp = [[rig.T[0], rig.T[1], rig.T[2]]];
    let ang = phi0, cur = tp[0].slice();
    for (let k = 0; k < 3; k++) {
      const l = 0.135; const zc = Math.sin(wz * (k + 1) * 0.5) * l;
      cur = [cur[0] + Math.cos(ang) * l * Math.cos(wz * 0.6), cur[1] + Math.sin(ang) * l, cur[2] + zc];
      cur[1] = Math.max(cur[1], 0.035 - K * 0); tp.push(cur.slice()); ang -= (0.30 + 0.12 * k) * (phi0 > -1.2 ? 1 : 0.3);
    }
    const tps = tp.map(p => proj(th, p[0], p[1], p[2]));
    parts.push({ id: 'tail', key: Ts[2] - 0.04, pts: tps.map(p => [p[0], p[1]]), widths: [0.06, 0.085, 0.07, 0.022] });
    parts.sort((p, q) => p.key - q.key);
    // the parent-frame anchor: the torso's area centroid. The page places this point on the score's x in every view, so a
    // substitution never moves the body sideways (the body stays put; only the drawing changes).
    let A2 = 0, cxs = 0;
    for (let k = 0; k < torso.length; k++) { const p = torso[k], q = torso[(k + 1) % torso.length]; const c = p[0] * q[1] - q[0] * p[1]; A2 += c; cxs += (p[0] + q[0]) * c; }
    const anchor = A2 ? cxs / (3 * A2) : 0;
    return { parts, rig, Bs, Ns, Ts, th, flip: bk.flip, anchor };
  }

  // ---- painting
  const PAL = {
    ink: '#1d1611', fawn: '#b88a58', fawnDark: '#8d6740', fawnFar: '#7c5a39', saddle: '#3a2a1f', pale: '#eadcc0',
    collar: '#e9e2cf', nose: '#120e0c', ear: '#2f231a', earIn: '#c99a7c', eye: '#1a120c',
  };
  function paintDog(ctx, model, opt) {
    opt = opt || {};
    const ID = opt.mask;   // mask mode: flat id colours, no ink
    const seed = opt.seed || 0, amp = ID ? 0 : (opt.boil === undefined ? 0.0032 : opt.boil);
    const lw = 0.0115;
    const fill = (col, idc) => { ctx.fillStyle = ID ? idc : col; ctx.fill(); };
    const ink = (w) => { if (ID) return; ctx.lineWidth = w || lw; ctx.strokeStyle = PAL.ink; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke(); };
    for (const p of model.parts) {
      if (opt.torsoOnly && p.id !== 'torso') continue;
      if (p.id === 'torso') {
        const T = jit(p.torso, seed + 1, amp);
        ctx.beginPath(); crClosed(ctx, T);
        if (!ID) { const g = ctx.createLinearGradient(0, 0.62, 0, 0.1); g.addColorStop(0, PAL.fawn); g.addColorStop(1, PAL.fawnDark); ctx.fillStyle = g; ctx.fill(); }
        else fill(null, ID.torso);
        ctx.save(); ctx.beginPath(); crClosed(ctx, T); ctx.clip();
        ctx.beginPath(); crClosed(ctx, jit(p.saddle, seed + 2, amp)); fill(PAL.saddle, ID ? ID.saddle : null);
        if (p.pale) { ctx.beginPath(); crClosed(ctx, jit(p.pale, seed + 3, amp)); fill(PAL.pale, ID ? ID.torso : null); }
        ctx.restore();
        ctx.beginPath(); crClosed(ctx, T); ink();
        if (!ID) for (const l of p.lines) { ctx.beginPath(); crOpen(ctx, jit(l, seed + 4, amp)); ink(lw * 0.7); }
      } else if (p.id.startsWith('leg_')) {
        const t = tube(jit(p.pts, seed + 10 + p.key * 50, amp * 0.6), p.widths);
        const col = p.near ? PAL.fawn : PAL.fawnFar;
        ctx.beginPath(); crClosed(ctx, [...t.L, ...t.R.slice().reverse()]); fill(col, ID ? ID.leg : null);
        // paw
        const pc = [(p.paw[0] + p.toe[0]) / 2, (p.paw[1] + p.toe[1]) / 2];
        const rx = Math.max(0.026, Math.abs(p.toe[0] - p.paw[0]) * 0.7 + 0.018);
        ctx.beginPath(); ctx.ellipse(pc[0], pc[1] - 0.006, rx, 0.02, 0, 0, Math.PI * 2); fill(p.near ? '#cfae80' : '#9c7a52', ID ? ID.leg : null); ink(lw * 0.8);
        if (!ID) { // side contours only (no seam where the leg enters the body)
          const cut = 1;
          ctx.save(); ctx.beginPath(); ctx.rect(-5, -5, 10, 10); ctx.arc(p.pts[0][0], p.pts[0][1], p.widths[0] * 0.75, 0, 7, true); ctx.clip('evenodd');
          ctx.beginPath(); crClosed(ctx, [...t.L, ...t.R.slice().reverse()]); ink(lw * 0.9); ctx.restore();
        }
      } else if (p.id.startsWith('haunch_')) {
        const col = p.near ? PAL.fawn : PAL.fawnFar;
        const t = tube(p.low, [0.05, 0.045]);
        ctx.beginPath(); crClosed(ctx, [...t.L, ...t.R.slice().reverse()]); fill(col, ID ? ID.leg : null); ink(lw * 0.85);
        ctx.beginPath(); ctx.ellipse(p.low[1][0], p.low[1][1] - 0.004, 0.03, 0.019, 0, 0, Math.PI * 2); fill(p.near ? '#cfae80' : '#9c7a52', ID ? ID.leg : null); ink(lw * 0.8);
        ctx.beginPath(); ctx.ellipse(p.c[0], p.c[1], p.rx, p.ry, 0, 0, Math.PI * 2);
        if (!ID) { const g = ctx.createLinearGradient(0, p.c[1] + p.ry, 0, p.c[1] - p.ry); g.addColorStop(0, PAL.fawn); g.addColorStop(1, PAL.fawnDark); ctx.fillStyle = g; ctx.fill(); }
        else fill(null, ID.leg);
        ctx.save(); ctx.beginPath(); ctx.rect(-5, p.c[1] - 0.02, 10, 10); ctx.clip(); ctx.beginPath(); ctx.ellipse(p.c[0], p.c[1], p.rx, p.ry, 0, 0, Math.PI * 2); ink(lw * 0.9); ctx.restore();
      } else if (p.id === 'tail') {
        const pts = jit(p.pts, seed + 20, amp);
        const t = tube(pts, p.widths);
        ctx.beginPath(); ctx.moveTo(t.L[0][0], t.L[0][1]); crOpen(ctx, t.L);
        const tip = pts[pts.length - 1]; ctx.lineTo(tip[0], tip[1]);
        const Rr = t.R.slice().reverse(); for (const q of Rr) ctx.lineTo(q[0], q[1]);
        ctx.closePath();
        if (!ID) { const g = ctx.createLinearGradient(pts[0][0], pts[0][1], tip[0], tip[1]); g.addColorStop(0, PAL.fawnDark); g.addColorStop(0.55, PAL.saddle); g.addColorStop(1, '#241a13'); ctx.fillStyle = g; ctx.fill(); }
        else fill(null, ID.tail);
        if (!ID) { ctx.beginPath(); crOpen(ctx, t.L.slice(1)); ink(lw * 0.85); ctx.beginPath(); crOpen(ctx, t.R.slice(1)); ink(lw * 0.85); }
      } else if (p.id === 'neck') {
        paintNeck(ctx, p, { ID, seed, amp, lw, fill, ink });
      } else if (p.id === 'head') {
        paintHead(ctx, p, model, { ID, seed, amp, lw, fill, ink });
      }
    }
  }
  function paintNeck(ctx, p, o) {
    const { ID, seed, amp, lw, fill, ink } = o;
    // neck tube from base B to joint N with the collar ring
    const B = p.B, N = p.N, mid = [lerp(B[0], N[0], 0.5), lerp(B[1], N[1], 0.5) + 0.01];
    const t = tube([B, mid, N], [0.25, 0.20, 0.16]);
    ctx.beginPath(); ctx.moveTo(t.L[0][0], t.L[0][1]); crOpen(ctx, t.L); ctx.lineTo(t.R[2][0], t.R[2][1]);
    crOpen(ctx, t.R.slice().reverse()); ctx.closePath(); fill(PAL.fawn, ID ? ID.neck : null);
    // saddle carries up the neck top in views from behind
    if (!ID) { ctx.beginPath(); crOpen(ctx, t.L); ink(); ctx.beginPath(); crOpen(ctx, t.R); ink(); }
    // collar: the protected identity feature, visible in every view
    const c0 = L2(B, N, 0.66), c1 = L2(B, N, 0.82);
    const tc = tube([c0, c1], [0.205, 0.18]);
    ctx.beginPath(); ctx.moveTo(tc.L[0][0], tc.L[0][1]); ctx.lineTo(tc.L[1][0], tc.L[1][1]); ctx.lineTo(tc.R[1][0], tc.R[1][1]); ctx.lineTo(tc.R[0][0], tc.R[0][1]); ctx.closePath();
    fill(PAL.collar, ID ? ID.collar : null); ink(lw * 0.8);
  }
  function paintHead(ctx, p, model, o) {
    const { ID, seed, amp, lw, fill, ink } = o; const N = p.N;
    // head drawing
    const H = HEADS[p.hk.key], fx = p.hk.flip ? -1 : 1;
    const beta = p.beta * D2R * H.pitch;
    const rot = q => { const x = q[0], y = q[1]; const c = Math.cos(-beta), s = Math.sin(-beta); return [(x * c - y * s) * fx + N[0], (x * s + y * c) + N[1] + (H.pitch === 0 ? p.beta * 0.0012 : 0)]; };
    const tr = pts => pts.map(rot);
    const ear = (E, front) => {
      const e = clamp(p.ear + p.earFlick * 0.6, 0, 1.15);
      const tip = L2(E.flat, E.up, e);
      const b1 = rot(E.b1), b2 = rot(E.b2), tp = rot(tip);
      const m1 = L2(b1, tp, 0.5), m2 = L2(tp, b2, 0.5);
      const bulge = 0.018;
      const n1 = [-(tp[1] - b1[1]), tp[0] - b1[0]], n2 = [-(b2[1] - tp[1]), b2[0] - tp[0]];
      const k1 = Math.hypot(n1[0], n1[1]) || 1, k2 = Math.hypot(n2[0], n2[1]) || 1;
      ctx.beginPath(); ctx.moveTo(b1[0], b1[1]);
      ctx.quadraticCurveTo(m1[0] - n1[0] / k1 * bulge * fx, m1[1] - n1[1] / k1 * bulge, tp[0], tp[1]);
      ctx.quadraticCurveTo(m2[0] - n2[0] / k2 * bulge * fx, m2[1] - n2[1] / k2 * bulge, b2[0], b2[1]);
      ctx.closePath(); fill(PAL.ear, ID ? ID.head : null); ink(lw * 0.85);
      if (!ID && H.inner && front) {
        const ib1 = L2(b1, b2, 0.25), ib2 = L2(b1, b2, 0.75), itp = L2(tp, L2(b1, b2, 0.5), 0.25);
        ctx.beginPath(); ctx.moveTo(ib1[0], ib1[1]); ctx.lineTo(itp[0], itp[1]); ctx.lineTo(ib2[0], ib2[1]); ctx.closePath(); ctx.fillStyle = PAL.earIn; ctx.fill();
      }
    };
    if (!H.earsFront) ear(H.ears.far, false);
    const S = jit(tr(H.skull), seed + 30, amp * 0.7);
    ctx.beginPath(); crClosed(ctx, S); fill(PAL.fawn, ID ? ID.head : null);
    if (!ID) {
      ctx.save(); ctx.beginPath(); crClosed(ctx, S); ctx.clip();
      if (H.mask) { ctx.beginPath(); crClosed(ctx, tr(H.mask)); ctx.fillStyle = PAL.saddle; ctx.fill(); }
      if (H.pale) { ctx.beginPath(); crClosed(ctx, tr(H.pale)); ctx.fillStyle = PAL.pale; ctx.fill(); }
      if (p.hk.key === '90' || p.hk.key === '45') { // the saddle's dark crown seen from behind
        ctx.beginPath(); crClosed(ctx, tr([[0.05, 0.02], [0.03, 0.09], [-0.04, 0.095], [-0.06, 0.03], [0, -0.01]])); ctx.fillStyle = 'rgba(58,42,31,0.55)'; ctx.fill();
      }
      ctx.restore();
    }
    ctx.beginPath(); crClosed(ctx, S); ink();
    if (H.earsFront) { ear(H.ears.far, false); ear(H.ears.near, true); } else ear(H.ears.near, true);
    if (ID) { if (H.nose) { const n = rot([H.nose[0], H.nose[1]]); ctx.beginPath(); ctx.ellipse(n[0], n[1], H.nose[2], H.nose[3], 0, 0, Math.PI * 2); fill(null, ID.nose); } return; }
    if (H.nose) { const n = rot([H.nose[0], H.nose[1]]); ctx.beginPath(); ctx.ellipse(n[0], n[1], H.nose[2], H.nose[3], 0, 0, Math.PI * 2); ctx.fillStyle = PAL.nose; ctx.fill(); }
    if (H.mouth) { ctx.beginPath(); crOpen(ctx, tr(H.mouth)); ink(lw * 0.7); }
    for (const b of H.brows) { const q = rot([b[0], b[1]]); ctx.beginPath(); ctx.arc(q[0], q[1], b[2], 0, Math.PI * 2); ctx.fillStyle = '#d8b07a'; ctx.fill(); }
    for (const e of H.eyes) {
      const q = rot([e[0], e[1]]), bl = clamp(p.blink);
      if (bl > 0.6) { ctx.beginPath(); ctx.moveTo(q[0] - e[2], q[1]); ctx.quadraticCurveTo(q[0], q[1] - e[3] * 0.8, q[0] + e[2], q[1]); ink(lw * 0.8); }
      else {
        ctx.beginPath(); ctx.ellipse(q[0], q[1], e[2], e[3] * (1 - bl), -beta * fx * 0.5, 0, Math.PI * 2); ctx.fillStyle = PAL.eye; ctx.fill();
        ctx.beginPath(); ctx.arc(q[0] - 0.006 * fx, q[1] + 0.004, 0.0045 * e[4], 0, Math.PI * 2); ctx.fillStyle = 'rgba(255,240,210,0.9)'; ctx.fill();
      }
    }
  }

  G.DOG = { K, RIG, VIEWS, HEADS, LEGS, NECK, proj, build, paintDog, headKey, bodyKey, PAL, crClosed, crOpen, tube, jit, noise };
})(typeof window !== 'undefined' ? window : globalThis);
