/* SCION-24 · Live2D lineage · the dog rig.
   A parametric 2D portrait rig built from scratch (no Cubism SDK here): parameter axes -> keyforms -> deformers -> art meshes.

   Coordinates. World metres: x along the porch (threshold 0, inside negative, steps 4.9), y up, z toward the viewer.
   The set is drawn in a raised side projection: a point's depth z lowers it on screen by KZ*z (planes x-y are seen undistorted,
   so a profile drawing is exact in profile). Screen pixels come from the camera: S px per metre times zoom.

   What is keyformed and what is solved:
   - HEAD: the drawing of the head (skull, cheeks, muzzle, jowl, nose, eyes, brows, ears, mouth, markings) is stored as a KEYFORM
     TABLE over two angle axes (ParamAngleX yaw, 16 keys every 22.5 deg; ParamAngleY pitch, 3 keys) and two control axes
     (ear prick, mouth open, interpolated inside the keyform). At run time the head is the bilinear blend of the four nearest
     keyforms (view interpolation), then a rotation deformer (ParamAngleZ roll) and the eye/brow/mouth controls.
     The keyforms were authored from a turnaround guide (named landmarks on the head, rotated and projected once at load) and
     then corrected per key (KEY_FIX); the guide is never drawn.
   - BODY: art meshes (torso volumes, neck, legs, paws, tail, markings) hung on a hierarchy of rotation deformers
     (body yaw about the torso middle, body pitch, neck, leg joints by two-bone solve to planted feet, tail chain).
   - PHYSICS (ears, tail, collar tag) and gait are solver passes in motion.js; this file only draws a pose. */
(function (G) {
  'use strict';
  const KZ = 0.2;
  const VIEW = norm3([0, KZ, 1]);
  const DEG = Math.PI / 180;

  function norm3(v) { const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; }
  const add3 = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const sc3 = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
  const dot3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross3 = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const smooth = (a, b, v) => { const t = clamp((v - a) / (b - a)); return t * t * (3 - 2 * t); };
  const proj = v => [v[0], v[1] - KZ * v[2]];
  const depth = v => dot3(v, VIEW);

  /* ---------------- parameter axes (the parameter table) ---------------- */
  const PARAMS = [
    ['ParamBodyAngleX', -180, 180, 0, 'deg', 'body yaw: 0 = profile facing the door (screen left), 90 = toward the viewer, 180 = facing away from the door (screen right)'],
    ['ParamAngleX', -180, 360, 0, 'deg', 'head yaw in the world, same convention; -45 = head turned into the depth of the room (back of the head to the viewer)'],
    ['ParamAngleY', -35, 35, 0, 'deg', 'head pitch (nose up +)'],
    ['ParamAngleZ', -25, 25, 0, 'deg', 'head roll, a rotation deformer after the keyform blend'],
    ['ParamEyeBallX', -1, 1, 0, '', 'gaze along the eye (toward the muzzle +); separate from the head'],
    ['ParamEyeBallY', -1, 1, 0, '', 'gaze up +'],
    ['ParamEyeOpen', 0, 1.25, 1, '', 'lid opening; 0 closed (blink), 1.25 wide'],
    ['ParamBrowWorry', 0, 1, 0, '', 'brow pips raised and drawn in (worry)'],
    ['ParamMouthOpen', 0, 1, 0, '', 'jaw drop'],
    ['ParamEarPrick', 0, 1, 1, '', '0 flat back, 1 pricked (score act.ear) + ear physics'],
    ['ParamTail', 0, 1.35, 0.5, '', '0 high, 0.5 hanging, 1.35 tucked (score act.tail) + tail physics'],
    ['ParamWag', 0, 1, 0, '', 'tail sweep amplitude (score act.wag), driven by the tail pendulum'],
    ['ParamCrouch', 0, 1, 0, '', 'body lowered, rear lower (score act.crouch)'],
    ['ParamLie', 0, 1, 0, '', 'standing 0 to sphinx lying 1 (score act.lie)'],
    ['ParamRest', 0, 1, 0, '', 'chin down onto the forepaws (score act.rest)'],
    ['ParamNeck', -0.3, 1.25, 0.9, '', 'neck raise: 0 head low, 1 head up (score act.head)'],
    ['ParamBreath', 0, 1, 0, '', 'chest swell'],
  ];

  /* ---------------- the head: turnaround guide -> keyform table ---------------- */
  // named head landmarks in head frame (F forward, U up, L to the dog's left), metres; ellipsoids as centre + radii
  const HG = {
    skull: { c: [-0.012, 0.006, 0], r: [0.086, 0.074, 0.067] },
    cheekA: { c: [0.03, -0.028, 0.038], r: [0.052, 0.042, 0.034] },
    cheekB: { c: [0.03, -0.028, -0.038], r: [0.052, 0.042, 0.034] },
    jowl: { c: [0.118, -0.056, 0], r: [0.062, 0.026, 0.036] },
    cap: { c: [-0.03, 0.052, 0], r: [0.1, 0.052, 0.074] },          // dark crown marking
    mask: { c: [0.2, -0.03, 0], r: [0.05, 0.04, 0.042] },            // dark muzzle tip
    pts: {
      muzB: [0.082, -0.026, 0], muzT: [0.186, -0.036, 0], nose: [0.213, -0.024, 0], noseUp: [0.208, -0.006, 0],
      eyeA: [0.064, 0.02, 0.04], eyeB: [0.064, 0.02, -0.04],
      eyeAi: [0.077, 0.019, 0.031], eyeAo: [0.05, 0.023, 0.05], eyeBi: [0.077, 0.019, -0.031], eyeBo: [0.05, 0.023, -0.05],
      browA: [0.06, 0.044, 0.033], browB: [0.06, 0.044, -0.033],
      earAi: [0.006, 0.058, 0.024], earAo: [-0.036, 0.04, 0.064], earAt: [-0.03, 0.178, 0.064], earAf: [-0.15, 0.06, 0.05],
      earBi: [0.006, 0.058, -0.024], earBo: [-0.036, 0.04, -0.064], earBt: [-0.03, 0.178, -0.064], earBf: [-0.15, 0.06, -0.05],
      lipA: [0.08, -0.062, 0.03], lipB: [0.08, -0.062, -0.03], lipF: [0.196, -0.058, 0], chin: [0.16, -0.08, 0], hinge: [0.02, -0.045, 0],
      throat: [-0.03, -0.07, 0],
    },
    normals: { eyeA: [0.55, 0.15, 0.82], eyeB: [0.55, 0.15, -0.82], earA: [0.7, 0.05, 0.72], earB: [0.7, 0.05, -0.72], nose: [1, 0.15, 0] },
    radius: { muzB: 0.047, muzT: 0.031, nose: 0.021 },
  };
  // per-key hand corrections found at view tests (yaw key -> landmark -> [dx, dy] metres in the picture)
  const KEY_FIX = {
    90: { cheekA: [0.004, 0], cheekB: [-0.004, 0] },
    270: { cheekA: [-0.004, 0], cheekB: [0.004, 0] },
  };
  const YAW_KEYS = Array.from({ length: 16 }, (_, k) => k * 22.5), PITCH_KEYS = [-35, 0, 35];

  function headFrame(yaw, pitch) {
    const y = yaw * DEG, p = pitch * DEG;
    const F = [-Math.cos(y) * Math.cos(p), Math.sin(p), Math.sin(y) * Math.cos(p)];
    const L = [Math.sin(y), 0, Math.cos(y)];
    const U = cross3(F, L);
    return { F, U, L };
  }
  const toW = (fr, v) => add3(add3(sc3(fr.F, v[0]), sc3(fr.U, v[1])), sc3(fr.L, v[2]));
  function ellCov(fr, e) {   // projected ellipsoid: centre and 2x2 covariance (exact for parallel projection)
    const m = [proj(sc3(fr.F, e.r[0])), proj(sc3(fr.U, e.r[1])), proj(sc3(fr.L, e.r[2]))];
    let a = 0, b = 0, c = 0; for (const v of m) { a += v[0] * v[0]; b += v[0] * v[1]; c += v[1] * v[1]; }
    const w = toW(fr, e.c), p = proj(w);
    return [p[0], p[1], depth(w), a, b, c];
  }
  // one keyform: a flat record of numbers (so keyforms can be blended)
  const ELLS = ['skull', 'cheekA', 'cheekB', 'jowl', 'cap', 'mask'];
  const PTS = Object.keys(HG.pts);
  function guideKey(yaw, pitch) {
    const fr = headFrame(yaw, pitch), out = {};
    for (const k of ELLS) out[k] = ellCov(fr, HG[k]);
    for (const k of PTS) { const w = toW(fr, HG.pts[k]); const p = proj(w); out[k] = [p[0], p[1], depth(w)]; }
    for (const k in HG.normals) out['f_' + k] = [dot3(norm3(toW(fr, HG.normals[k])), VIEW)];
    const fix = KEY_FIX[((Math.round(yaw) % 360) + 360) % 360];
    if (fix) for (const k in fix) { out[k] = out[k].slice(); out[k][0] += fix[k][0]; out[k][1] += fix[k][1]; }
    return out;
  }
  const TABLE = YAW_KEYS.map(y => PITCH_KEYS.map(p => guideKey(y, p)));
  function blendKeys(list) {   // list of [key, weight]
    const out = {};
    for (const k in list[0][0]) { const n = list[0][0][k].length, v = new Array(n).fill(0); for (const [key, w] of list) for (let i = 0; i < n; i++) v[i] += key[k][i] * w; out[k] = v; }
    return out;
  }
  function headKey(yaw, pitch) {   // view interpolation: bilinear between the 4 nearest keyforms
    const yw = ((yaw % 360) + 360) % 360, fy = yw / 22.5, i0 = Math.floor(fy) % 16, i1 = (i0 + 1) % 16, ty = fy - Math.floor(fy);
    const pc = clamp(pitch, -35, 35), j0 = pc < 0 ? 0 : 1, j1 = j0 + 1, tp = (pc - PITCH_KEYS[j0]) / 35;
    return blendKeys([[TABLE[i0][j0], (1 - ty) * (1 - tp)], [TABLE[i1][j0], ty * (1 - tp)], [TABLE[i0][j1], (1 - ty) * tp], [TABLE[i1][j1], ty * tp]]);
  }

  /* ---------------- 2D mesh helpers (screen px) ---------------- */
  function ellPoly(cx, cy, a, b, c, n = 28) {   // covariance -> polygon
    const tr = a + c, det = a * c - b * b, disc = Math.sqrt(Math.max(0, tr * tr / 4 - det));
    const l1 = tr / 2 + disc, l2 = Math.max(1e-12, tr / 2 - disc);
    let vx = b, vy = l1 - a; if (Math.abs(vx) + Math.abs(vy) < 1e-12) { vx = 1; vy = 0; }
    const vl = Math.hypot(vx, vy); vx /= vl; vy /= vl;
    const r1 = Math.sqrt(l1), r2 = Math.sqrt(l2), out = [];
    for (let i = 0; i < n; i++) { const t = i / n * 2 * Math.PI, u = Math.cos(t) * r1, v = Math.sin(t) * r2; out.push([cx + u * vx - v * vy, cy + u * vy + v * vx]); }
    return out;
  }
  function circlePts(c, r, n = 16) { const o = []; for (let i = 0; i < n; i++) { const t = i / n * 2 * Math.PI; o.push([c[0] + r * Math.cos(t), c[1] + r * Math.sin(t)]); } return o; }
  function hull(pts) {
    const p = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]); if (p.length < 3) return p;
    const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lo = [], up = [];
    for (const q of p) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
    for (let i = p.length - 1; i >= 0; i--) { const q = p[i]; while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
    up.pop(); lo.pop(); return lo.concat(up);
  }
  const capsule = (c1, r1, c2, r2, n = 14) => hull(circlePts(c1, r1, n).concat(circlePts(c2, r2, n)));
  function pathPolys(ctx, polys) { ctx.beginPath(); for (const p of polys) { if (!p || p.length < 2) continue; ctx.moveTo(p[0][0], p[0][1]); for (let i = 1; i < p.length; i++) ctx.lineTo(p[i][0], p[i][1]); ctx.closePath(); } }
  function smoothPath(ctx, p, closed = true) {   // quadratic smoothing through midpoints
    const n = p.length; if (n < 3) return;
    const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    if (closed) { let m = mid(p[n - 1], p[0]); ctx.moveTo(m[0], m[1]); for (let i = 0; i < n; i++) { const q = p[i], m2 = mid(q, p[(i + 1) % n]); ctx.quadraticCurveTo(q[0], q[1], m2[0], m2[1]); } ctx.closePath(); }
    else { ctx.moveTo(p[0][0], p[0][1]); for (let i = 1; i < n - 1; i++) { const m2 = mid(p[i], p[i + 1]); ctx.quadraticCurveTo(p[i][0], p[i][1], m2[0], m2[1]); } ctx.lineTo(p[n - 1][0], p[n - 1][1]); }
  }
  function sPolys(ctx, polys) { ctx.beginPath(); for (const p of polys) if (p && p.length > 2) smoothPath(ctx, p); }
  // ensure all polygons wind the same way so a nonzero fill is their union
  function ccw(p) { let s = 0; for (let i = 0; i < p.length; i++) { const a = p[i], b = p[(i + 1) % p.length]; s += a[0] * b[1] - b[0] * a[1]; } return s < 0 ? p.slice().reverse() : p; }
  function union(ctx, polys, fill, line, lw) {
    polys = polys.filter(p => p && p.length > 2).map(ccw);
    if (line && lw > 0) { sPolys(ctx, polys); ctx.lineJoin = 'round'; ctx.strokeStyle = line; ctx.lineWidth = lw * 2; ctx.stroke(); }
    sPolys(ctx, polys); ctx.fillStyle = fill; ctx.fill();
    return polys;
  }
  function clipTo(ctx, polys) { sPolys(ctx, polys.map(ccw)); ctx.clip(); }

  /* ---------------- palette (lit by the scene: sky and door light) ---------------- */
  function mix(c1, c2, t) { return [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)]; }
  const rgb = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
  function lit(base, L) {   // L: {dusk: 0..1 (blue dimming), warm: 0..1 door light}
    const dusk = mix(base, [base[0] * 0.42 + 18, base[1] * 0.5 + 24, base[2] * 0.62 + 52], L.dusk);
    return mix(dusk, [Math.min(255, base[0] * 1.08 + 30), base[1] * 0.92 + 14, base[2] * 0.62], L.warm);
  }
  const COAT = { tan: [176, 122, 70], cream: [222, 190, 140], saddle: [40, 29, 24], ear: [44, 32, 27], earIn: [150, 98, 84], nose: [24, 18, 18], line: [22, 15, 13], iris: [70, 40, 18], sclera: [236, 226, 206], tongue: [196, 92, 96], collar: [140, 36, 32], tag: [214, 182, 96] };

  /* ---------------- the body: rotation-deformer hierarchy ---------------- */
  const BODY = {
    halfLen: 0.22,                // withers at +0.22, hip top at -0.22 along the dog from the torso middle (the rig root)
    vols: { chest: [0.17, -0.16, 0.18, 0.19, 0.135], waist: [-0.03, -0.1, 0.15, 0.12, 0.118], rump: [-0.2, -0.09, 0.15, 0.15, 0.125] },
    saddle: [-0.01, 0.02, 0.29, 0.115, 0.145], blaze: [0.32, -0.22, 0.07, 0.13, 0.075], belly: [0.0, -0.27, 0.2, 0.06, 0.09],
    shoulder: [0.19, -0.18, 0.085], hip: [-0.21, -0.12, 0.08], neckBase: [0.27, -0.03], tailRoot: [-0.33, -0.02],
    front: [0.18, 0.175], hind: [0.19, 0.18, 0.12],
  };
  function dogFrame(pose) {
    const th = pose.bodyYaw * DEG;
    const Fw = [-Math.cos(th), 0, Math.sin(th)], Sw = [Math.sin(th), 0, Math.cos(th)], Uw = [0, 1, 0];
    const root = [pose.x, 0, pose.z || 0];
    const c = pose.crouch, l = pose.lie;
    let hw = 0.565 - 0.08 * c, hh = 0.535 - 0.14 * c;
    hw = lerp(hw, 0.3, l); hh = lerp(hh, 0.22, l);
    hw += 0.004 * pose.breath;
    const phi = Math.atan2(hw - hh, 2 * BODY.halfLen);
    const ef = [Math.cos(phi), Math.sin(phi)], eu = [-Math.sin(phi), Math.cos(phi)];
    const mid = [0, (hw + hh) / 2];
    const loc = (a, b, s) => { const f = mid[0] + a * ef[0] + b * eu[0], u = mid[1] + a * ef[1] + b * eu[1]; return add3(add3(add3(root, sc3(Fw, f)), sc3(Uw, u)), sc3(Sw, s)); };
    const fu = (f, u, s) => add3(add3(add3(root, sc3(Fw, f)), sc3(Uw, u)), sc3(Sw, s));
    const toLocal = w => { const d = [w[0] - root[0], w[1] - root[1], w[2] - root[2]]; return [dot3(d, Fw), d[1], dot3(d, Sw)]; };
    return { Fw, Sw, Uw, root, loc, fu, toLocal, phi, ef, eu, hw, hh };
  }
  // two-bone solve in the leg's sagittal plane; bend = +1 joint toward forward, -1 backward
  function ik2(j, t, L1, L2, bend) {
    let dx = t[0] - j[0], dy = t[1] - j[1], d = Math.hypot(dx, dy);
    const dm = Math.min(d, (L1 + L2) * 0.999); if (d < 1e-6) { dx = 0; dy = -1; d = 1; }
    const ux = dx / d, uy = dy / d;
    const a = (L1 * L1 - L2 * L2 + dm * dm) / (2 * dm), h = Math.sqrt(Math.max(0, L1 * L1 - a * a));
    const px = j[0] + ux * a, py = j[1] + uy * a;
    let nx = -uy, ny = ux; if (nx * bend < 0) { nx = -nx; ny = -ny; }
    const k = [px + nx * h, py + ny * h];
    const end = [j[0] + ux * dm, j[1] + uy * dm];
    return [k, end];
  }

  /* ---------------- drawing a pose ---------------- */
  // pose: {x,z,bodyYaw,headYaw,headPitch,headRoll,neck,crouch,lie,rest,breath, eyeX,eyeY,eyeOpen,brow,mouth, ear:[a,b], earSwing:[a,b],
  //        tail:[{p,w}...], feet:[{x,z,y}*4] (front A, front B, hind A, hind B; A = +s side), tag:angle}
  // cam: {S, zoom, cx, cy, W, H}; L: lighting {dusk, warm, rim}
  function drawDog(ctx, cam, pose, L) {
    const K = cam.S * cam.zoom;
    const scr = w => { const p = proj(w); return [cam.W / 2 + (p[0] - cam.cx) * K, cam.H / 2 - (p[1] - cam.cy) * K]; };
    const fr = dogFrame(pose);
    const lw = Math.max(1.1, 0.0085 * K);
    const line = rgb(lit(COAT.line, { dusk: L.dusk * 0.4, warm: 0 }));
    const C = k => rgb(lit(COAT[k], L));
    const meas = { parts: {} };
    const items = [];   // {d, fn}
    const v = VIEW;
    const dF = dot3(fr.Fw, v), dS = dot3(fr.Sw, v);

    // ---- torso volumes (ellipsoids hung on the body pitch deformer)
    const ellOf = (vol) => {
      const [a, b, ra, rb, rs] = vol;
      const c = fr.loc(a, b, 0);
      const ax = [sc3([fr.Fw[0] * fr.ef[0], fr.ef[1], fr.Fw[2] * fr.ef[0]], ra), sc3([fr.Fw[0] * fr.eu[0], fr.eu[1], fr.Fw[2] * fr.eu[0]], rb), sc3(fr.Sw, rs)];
      let A = 0, B = 0, Cc = 0; for (const x of ax) { const p = proj(x); A += p[0] * p[0]; B += p[0] * p[1]; Cc += p[1] * p[1]; }
      const pc = scr(c);
      return ellPoly(pc[0], pc[1], A * K * K, -B * K * K, Cc * K * K, 30);
    };
    const chest = ellOf(BODY.vols.chest.map((q, i) => i === 3 ? q * (1 + 0.03 * pose.breath) : q)), waist = ellOf(BODY.vols.waist), rump = ellOf(BODY.vols.rump);
    const torsoPolys = [hull(chest.concat(waist)), hull(waist.concat(rump))];
    // neck: capsule from neck base to the head pivot
    const nb = fr.loc(BODY.neckBase[0], BODY.neckBase[1], 0);
    const relYaw = wrap180(pose.headYaw - pose.bodyYaw);
    const nAng = (lerp(-28, 58, clamp(pose.neck, -0.3, 1.3)) - 12 * pose.lie) * DEG + fr.phi;
    const nYaw = clamp(relYaw, -165, 165) * 0.55 * DEG;
    const nLen = 0.16 * (1 - 0.25 * pose.lie);
    const ndirL = [Math.cos(nAng) * Math.cos(nYaw), Math.sin(nAng), Math.cos(nAng) * Math.sin(nYaw)];
    const ndirW = add3(add3(sc3(fr.Fw, ndirL[0]), sc3(fr.Uw, ndirL[1])), sc3(fr.Sw, ndirL[2]));
    let hp = add3(nb, sc3(ndirW, nLen));
    // rest: chin down to the forepaws
    if (pose.rest > 0) { const g = fr.fu(0.47, 0.12, 0); hp = add3(sc3(hp, 1 - pose.rest * 0.75), sc3(g, pose.rest * 0.75)); }
    const nbS = scr(nb), hpS = scr(hp);
    const neckPoly = capsule(nbS, 0.085 * K, hpS, 0.06 * K);
    const torsoAll = torsoPolys.concat([neckPoly]);
    const torsoD = depth(fr.loc(0, -0.1, 0));
    meas.root = scr(fr.loc(0, 0, 0)); meas.rootW = fr.loc(0, 0, 0);
    meas.withers = scr(fr.loc(BODY.halfLen, 0, 0)); meas.hip = scr(fr.loc(-BODY.halfLen, 0, 0));

    items.push({
      d: torsoD, name: 'torso', fn: () => {
        union(ctx, torsoAll, C('tan'), line, lw);
        ctx.save(); clipTo(ctx, torsoAll);
        // markings: saddle (dark cap over the back), chest blaze, pale belly
        sPolys(ctx, [ccw(ellOf(BODY.saddle))]); ctx.fillStyle = C('saddle'); ctx.fill();
        const nbk = capsule(nbS, 0.06 * K, hpS, 0.04 * K).map(p => [p[0], p[1] - 0.03 * K]);
        sPolys(ctx, [ccw(nbk)]); ctx.fill();
        sPolys(ctx, [ccw(ellOf(BODY.blaze))]); ctx.fillStyle = C('cream'); ctx.fill();
        sPolys(ctx, [ccw(ellOf(BODY.belly))]); ctx.fillStyle = rgb(lit(COAT.cream, L), 0.55); ctx.fill();
        shade(ctx, torsoAll, L, K);
        ctx.restore();
        // collar on the neck
        const cpt = [lerp(nbS[0], hpS[0], 0.62), lerp(nbS[1], hpS[1], 0.62)];
        const nd = [hpS[0] - nbS[0], hpS[1] - nbS[1]], nl = Math.hypot(nd[0], nd[1]) || 1, nn = [-nd[1] / nl, nd[0] / nl];
        const r = 0.072 * K;
        ctx.beginPath(); ctx.moveTo(cpt[0] + nn[0] * r, cpt[1] + nn[1] * r); ctx.lineTo(cpt[0] - nn[0] * r, cpt[1] - nn[1] * r);
        ctx.strokeStyle = rgb(lit(COAT.collar, L)); ctx.lineWidth = 0.022 * K; ctx.lineCap = 'round'; ctx.stroke();
        const low = nn[1] > 0 ? 1 : -1, tp = [cpt[0] + nn[0] * r * low * 0.95, cpt[1] + nn[1] * r * low * 0.95];
        const ta = (pose.tag || 0);
        const tq = [tp[0] + Math.sin(ta) * 0.025 * K, tp[1] + Math.cos(ta) * 0.025 * K];
        ctx.beginPath(); ctx.arc(tq[0], tq[1], 0.011 * K, 0, 7); ctx.fillStyle = rgb(lit(COAT.tag, L)); ctx.fill(); ctx.strokeStyle = line; ctx.lineWidth = lw * 0.6; ctx.stroke();
        meas.parts.collar = tq;
      }
    });

    // ---- legs: rotation deformers solved to the planted feet
    const legs = [['frontA', 0, 1], ['frontB', 1, -1], ['hindA', 2, 1], ['hindB', 3, -1]];
    meas.feet = [];
    for (const [name, k, side] of legs) {
      const front = k < 2, J = front ? BODY.shoulder : BODY.hip;
      const jw = fr.loc(J[0], J[1], J[2] * side);
      const foot = pose.feet[k];
      const fw = [foot.x, foot.y || 0, foot.z];
      const jl = fr.toLocal(jw), fl = fr.toLocal(fw);
      let pts, radii;
      if (front) {
        const wristT = [fl[0] + lerp(-0.005, -0.075, pose.lie), fl[1] + lerp(0.045, 0.028, pose.lie)];
        const [el, wr] = ik2([jl[0], jl[1]], wristT, BODY.front[0], BODY.front[1], -1);
        const toe = [fl[0] + lerp(0.035, 0.03, pose.lie), fl[1] + 0.014];
        const sAt = t => lerp(jl[2], fl[2], t);
        pts = [[jl[0], jl[1], sAt(0)], [el[0], el[1], sAt(0.45)], [wr[0], wr[1], sAt(0.9)], [toe[0], toe[1], fl[2]]];
        radii = [0.058, 0.04, 0.026, 0.022];
      } else {
        const hockT = [fl[0] + lerp(-0.05, -0.12, pose.lie), fl[1] + lerp(0.11, 0.022, pose.lie)];
        const [kn, hk] = ik2([jl[0], jl[1]], hockT, BODY.hind[0], BODY.hind[1], 1);
        const toe = [fl[0] + 0.035, fl[1] + 0.014];
        const sAt = t => lerp(jl[2], fl[2], t);
        pts = [[jl[0], jl[1], sAt(0)], [kn[0], kn[1], sAt(0.4)], [hk[0], hk[1], sAt(0.8)], [fl[0], fl[1] + 0.022, fl[2]], [toe[0], toe[1], fl[2]]];
        radii = [0.072, 0.045, 0.026, 0.022, 0.021];
      }
      const W = pts.map(p => fr.fu(p[0], p[1], p[2])), Sp = W.map(scr);
      const polys = [];
      for (let i = 0; i < Sp.length - 1; i++) polys.push(capsule(Sp[i], radii[i] * K, Sp[i + 1], radii[i + 1] * K, 10));
      // paw: a flattened oval along the dog's forward direction
      const pawC = Sp[Sp.length - 1];
      const fwd2 = proj(fr.Fw), sd2 = proj(fr.Sw);
      const pa = [fwd2[0] * 0.036 * K, -fwd2[1] * 0.036 * K], pb = [sd2[0] * 0.026 * K, -sd2[1] * 0.026 * K];
      const e2 = Math.pow(0.011 * K, 2);
      const pawRound = ellPoly(pawC[0], pawC[1] - 0.008 * K, pa[0] * pa[0] + pb[0] * pb[0] + e2, pa[0] * pa[1] + pb[0] * pb[1], pa[1] * pa[1] + pb[1] * pb[1] * 0.25 + e2, 16);
      polys.push(pawRound);
      const m = side * J[2] * dS + ((front ? J[0] : J[0]) - (-0.02)) * dF * 0.5;
      const near = m > 0;
      meas.feet.push(scr(fw));
      items.push({
        d: torsoD + m * 3 + (near ? 0.001 : -0.001), name, fn: () => {
          const base = near ? 'tan' : 'tan';
          union(ctx, polys, C(base), line, lw);
          ctx.save(); clipTo(ctx, polys);
          // lower leg cream, upper leg darkened toward the saddle; far legs in shadow
          const lower = []; for (let i = Math.max(1, Sp.length - 3); i < Sp.length - 1; i++) lower.push(capsule(Sp[i], radii[i] * K * 1.05, Sp[i + 1], radii[i + 1] * K * 1.05, 8));
          lower.push(pawRound);
          sPolys(ctx, lower.map(ccw)); ctx.fillStyle = rgb(lit(COAT.cream, L), 0.6); ctx.fill();
          if (!front) { sPolys(ctx, [ccw(circlePts([Sp[0][0], Sp[0][1] - 0.025 * K], 0.06 * K, 14))]); ctx.fillStyle = rgb(lit(COAT.saddle, L), 0.85); ctx.fill(); }
          if (!near) { pathPolys(ctx, polys); ctx.fillStyle = 'rgba(10,12,30,0.34)'; ctx.fill(); }
          shade(ctx, polys, L, K, 0.6);
          ctx.restore();
          // toe lines
          ctx.beginPath(); for (let q = -1; q <= 1; q += 2) { const o = [pawC[0] + pa[0] * 0.7 + pb[0] * 0.3 * q, pawC[1] + pa[1] * 0.7 + pb[1] * 0.3 * q]; ctx.moveTo(o[0], o[1] - 0.004 * K); ctx.lineTo(o[0] + pa[0] * 0.15, o[1] + 0.008 * K); }
          ctx.strokeStyle = line; ctx.lineWidth = lw * 0.6; ctx.stroke();
        }
      });
    }

    // ---- tail: a chain of rotation deformers (angles come from the tail pendulum)
    {
      const tr = fr.loc(BODY.tailRoot[0], BODY.tailRoot[1], 0);
      let p = tr; const W = [p];
      const segs = pose.tail;
      for (const sg of segs) {
        const pa = sg.p * DEG + fr.phi, wa = sg.w * DEG;
        const dl = [-Math.cos(pa) * Math.cos(wa), Math.sin(pa), Math.cos(pa) * Math.sin(wa)];
        const dw = add3(add3(sc3(fr.Fw, dl[0]), sc3(fr.Uw, dl[1])), sc3(fr.Sw, dl[2]));
        p = add3(p, sc3(dw, 0.058)); W.push(p);
      }
      const Sp = W.map(scr);
      const R = [0.034, 0.036, 0.04, 0.042, 0.04, 0.034, 0.024, 0.01];
      const polys = []; for (let i = 0; i < Sp.length - 1; i++) polys.push(capsule(Sp[i], R[i] * K, Sp[i + 1], R[i + 1] * K, 10));
      const td = depth(W[3]) - torsoD;
      const behind = (-dF) > 0.25 ? false : true;   // tail toward the viewer when the dog faces away
      meas.parts.tailTip = Sp[Sp.length - 1];
      items.push({
        d: behind ? torsoD - 0.5 : torsoD + 0.5, name: 'tail', fn: () => {
          union(ctx, polys, C('saddle'), line, lw);
          ctx.save(); clipTo(ctx, polys);
          // pale underside
          const under = Sp.map((q, i) => [q[0], q[1] + R[Math.min(i, R.length - 1)] * K * 0.9]);
          ctx.beginPath(); smoothPath(ctx, under, false); ctx.strokeStyle = rgb(lit(COAT.tan, L), 0.9); ctx.lineWidth = 0.028 * K; ctx.stroke();
          shade(ctx, polys, L, K, 0.5);
          ctx.restore();
        }
      });
    }

    // ---- head: keyform blend + rotation deformer (roll) + controls
    {
      const hk = headKey(pose.headYaw, pose.headPitch);
      const roll = (pose.headRoll || 0) * DEG, cr = Math.cos(roll), sr = Math.sin(roll);
      const sk = hk.skull;  // skull centre (in metres relative to head origin), relative frame
      const origin = add3(hp, [0, 0, 0]);
      const oS = scr(origin);
      // map a keyform point (metres, picture plane, y up, relative to head origin) through the roll deformer to screen
      const H = q => { const x = q[0], y = q[1]; const rx = x * cr - y * sr, ry = x * sr + y * cr; return [oS[0] + rx * K, oS[1] - ry * K]; };
      const Hell = (e, n = 26) => {   // ellipse record -> polygon, rotated by roll
        const c = H(e); const a = e[3], b = e[4], c2 = e[5];
        // rotate covariance by roll (picture y up -> screen y down handled by flipping b)
        const R = [[cr, -sr], [sr, cr]];
        const M = [[a, b], [b, c2]];
        const RM = [[R[0][0] * M[0][0] + R[0][1] * M[1][0], R[0][0] * M[0][1] + R[0][1] * M[1][1]], [R[1][0] * M[0][0] + R[1][1] * M[1][0], R[1][0] * M[0][1] + R[1][1] * M[1][1]]];
        const RMR = [[RM[0][0] * R[0][0] + RM[0][1] * R[0][1], RM[0][0] * R[1][0] + RM[0][1] * R[1][1]], [RM[1][0] * R[0][0] + RM[1][1] * R[0][1], RM[1][0] * R[1][0] + RM[1][1] * R[1][1]]];
        return ellPoly(c[0], c[1], RMR[0][0] * K * K, -RMR[0][1] * K * K, RMR[1][1] * K * K, n);
      };
      const hd = depth(origin);
      const skull = Hell(hk.skull), cheekA = Hell(hk.cheekA), cheekB = Hell(hk.cheekB), jowl = Hell(hk.jowl);
      const mB = H(hk.muzB), mT = H(hk.muzT);
      const muzzle = capsule(mB, HG.radius.muzB * K, mT, HG.radius.muzT * K, 14);
      const muzD = (hk.muzB[2] + hk.muzT[2]) / 2;
      const flesh = [skull, cheekA, cheekB, jowl];
      // ears: tip blended between flat and pricked by the ear control, plus the pendulum swing
      const earPoly = (s) => {
        const e = pose.ear[s === 'A' ? 0 : 1], sw = pose.earSwing ? pose.earSwing[s === 'A' ? 0 : 1] : 0;
        const bi = H(hk['ear' + s + 'i']), bo = H(hk['ear' + s + 'o']);
        const tU = hk['ear' + s + 't'], tF = hk['ear' + s + 'f'];
        let tip = H([lerp(tF[0], tU[0], e), lerp(tF[1], tU[1], e)]);
        const bm = [(bi[0] + bo[0]) / 2, (bi[1] + bo[1]) / 2];
        const ang = sw, ca = Math.cos(ang), sa = Math.sin(ang);
        tip = [bm[0] + (tip[0] - bm[0]) * ca - (tip[1] - bm[1]) * sa, bm[1] + (tip[0] - bm[0]) * sa + (tip[1] - bm[1]) * ca];
        // leaf shape: each edge bulges away from the other base point (robust to mirroring)
        const q = (a, b, t, o, away) => { const m = [lerp(a[0], b[0], t), lerp(a[1], b[1], t)]; const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; let nx = -dy / l, ny = dx / l; if (nx * (away[0] - a[0]) + ny * (away[1] - a[1]) > 0) { nx = -nx; ny = -ny; } return [m[0] + nx * o, m[1] + ny * o]; };
        const wv = Math.max(Math.hypot(bi[0] - bo[0], bi[1] - bo[1]), 0.03 * K);
        const pts = [bi, q(bi, tip, 0.45, wv * 0.3, bo), q(bi, tip, 0.8, wv * 0.12, bo), tip, q(bo, tip, 0.8, wv * 0.12, bi), q(bo, tip, 0.45, wv * 0.32, bi), bo];
        const inner = [q(bi, bo, 0.5, 0, tip), q(bi, tip, 0.5, wv * 0.1, bo), [lerp(tip[0], bm[0], 0.12), lerp(tip[1], bm[1], 0.12)], q(bo, tip, 0.5, wv * 0.12, bi)];
        return { pts, inner, facing: hk['f_ear' + s][0], d: hk['ear' + s + 'i'][2], tip };
      };
      const ears = ['A', 'B'].map(earPoly);
      const eyes = ['A', 'B'].map(s => ({ s, c: H(hk['eye' + s]), i: H(hk['eye' + s + 'i']), o: H(hk['eye' + s + 'o']), f: hk['f_eye' + s][0], d: hk['eye' + s][2], brow: H(hk['brow' + s]) }));
      const noseC = H(hk.nose), noseF = hk.f_nose[0], noseD = hk.nose[2];
      meas.parts.nose = noseC; meas.parts.head = H([sk[0], sk[1]]); meas.parts.muzzleTip = mT;
      meas.headFacing = { eyeA: eyes[0].f, eyeB: eyes[1].f, nose: noseF };
      const headPolys = flesh.concat([muzzle]);
      meas.headPolys = headPolys;
      const skD = sk[2];
      const drawEar = (er) => {
        const poly = er.pts;
        ctx.beginPath(); smoothPath(ctx, poly); ctx.lineJoin = 'round'; ctx.strokeStyle = line; ctx.lineWidth = lw * 2; ctx.stroke();
        ctx.fillStyle = C('ear'); ctx.fill();
        if (er.facing > 0.05) {
          ctx.save(); ctx.beginPath(); smoothPath(ctx, poly); ctx.clip();
          ctx.beginPath(); smoothPath(ctx, er.inner); ctx.fillStyle = rgb(lit(COAT.earIn, L), clamp(er.facing * 1.6)); ctx.fill();
          ctx.restore();
        }
      };
      const drawEye = (e) => {
        const vis = smooth(0.06, 0.32, e.f); if (vis <= 0.01) return;
        const ax = [e.o[0] - e.i[0], e.o[1] - e.i[1]], al = Math.hypot(ax[0], ax[1]) || 1;
        const u = [ax[0] / al, ax[1] / al]; let n = [u[1], -u[0]]; if (n[1] > 0) n = [-n[0], -n[1]];   // n points up on screen
        const a = Math.max(al * 0.8, 0.008 * K), open = clamp(pose.eyeOpen, 0, 1.3), b = 0.0135 * K * open * (0.55 + 0.45 * vis);
        const c = [(e.i[0] + e.o[0]) / 2, (e.i[1] + e.o[1]) / 2];
        const P2 = (s, t) => [c[0] + u[0] * s + n[0] * t, c[1] + u[1] * s + n[1] * t];
        const almond = []; for (let i = 0; i <= 12; i++) { const s = -1 + 2 * i / 12; almond.push(P2(s * a, b * Math.pow(1 - s * s, 0.75) * (1 + 0.15 * s))); }
        for (let i = 11; i >= 1; i--) { const s = -1 + 2 * i / 12; almond.push(P2(s * a, -b * 0.8 * Math.pow(1 - s * s, 0.9))); }
        ctx.save(); ctx.globalAlpha = vis;
        // dark eye rim (dog eyes are framed by dark skin)
        ctx.beginPath(); pathPolys(ctx, [almond]); ctx.strokeStyle = line; ctx.lineWidth = lw * 1.5; ctx.stroke();
        if (open > 0.12) {
          ctx.fillStyle = rgb(COAT.sclera); ctx.fill();
          ctx.save(); pathPolys(ctx, [almond]); ctx.clip();
          const gx = clamp(pose.eyeX, -1.2, 1.2), gy = clamp(pose.eyeY, -1, 1);
          const ic = P2(-gx * a * 0.45, gy * b * 0.35 + b * 0.05);
          const ir = Math.max(b * 1.0, a * 0.6);
          ctx.beginPath(); ctx.arc(ic[0], ic[1], ir, 0, 7); ctx.fillStyle = rgb(lit(COAT.iris, { dusk: L.dusk * 0.3, warm: L.warm })); ctx.fill();
          ctx.beginPath(); ctx.arc(ic[0], ic[1], ir * 0.55, 0, 7); ctx.fillStyle = '#0b0705'; ctx.fill();
          ctx.beginPath(); ctx.arc(ic[0] - ir * 0.32, ic[1] - ir * 0.38, Math.max(0.9, ir * 0.24), 0, 7); ctx.fillStyle = 'rgba(255,250,235,0.92)'; ctx.fill();
          ctx.restore();
        }
        // upper lid line
        ctx.beginPath(); for (let i = 0; i <= 12; i++) { const s = -1 + 2 * i / 12; const p = P2(s * a * 1.05, b * Math.pow(1 - s * s, 0.75) * (1 + 0.15 * s) + 0.0012 * K); i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); }
        ctx.strokeStyle = line; ctx.lineWidth = lw * 1.4; ctx.lineCap = 'round'; ctx.stroke();
        // brow pip (tan spot), raised and drawn in by worry
        const w = pose.brow || 0;
        const bp = [e.brow[0] + n[0] * w * 0.008 * K - u[0] * w * 0.004 * K, e.brow[1] + n[1] * w * 0.008 * K - u[1] * w * 0.004 * K];
        const bang = Math.atan2(u[1], u[0]) + (e.s === 'A' ? 1 : -1) * w * 0.35;
        ctx.beginPath(); ctx.ellipse(bp[0], bp[1], 0.011 * K * (0.4 + 0.6 * vis), 0.0065 * K, bang, 0, 7); ctx.fillStyle = rgb(lit(COAT.tan, L), 0.95); ctx.fill();
        ctx.restore();
      };
      const drawNose = () => {
        const vis = smooth(-0.35, -0.05, noseF); if (vis <= 0.01) return;
        const r = HG.radius.nose * K, c = noseC;
        ctx.save(); ctx.globalAlpha = vis;
        ctx.beginPath(); ctx.ellipse(c[0], c[1], r * (0.75 + 0.35 * Math.abs(noseF)), r * 0.72, 0, 0, 7); ctx.fillStyle = rgb(COAT.nose); ctx.fill();
        ctx.beginPath(); ctx.ellipse(c[0] - r * 0.25, c[1] - r * 0.35, r * 0.28, r * 0.15, -0.3, 0, 7); ctx.fillStyle = 'rgba(200,210,230,0.45)'; ctx.fill();
        if (noseF > 0.4) { ctx.beginPath(); for (const q of [-1, 1]) { ctx.moveTo(c[0] + q * r * 0.35, c[1] + r * 0.05); ctx.arc(c[0] + q * r * 0.35, c[1] + r * 0.05, r * 0.15, 0, 7); } ctx.fillStyle = '#000'; ctx.fill(); }
        ctx.restore();
      };
      const drawMouth = () => {
        // lip line from the near lip corner to the front, jaw drops about the hinge
        const nearA = hk.lipA[2] > hk.lipB[2];
        const corner = H(nearA ? hk.lipA : hk.lipB), front = H(hk.lipF), chin = H(hk.chin), hinge = H(hk.hinge);
        const mo = clamp(pose.mouth, 0, 1);
        const rot = (p, a) => { const dx = p[0] - hinge[0], dy = p[1] - hinge[1], c = Math.cos(a), s = Math.sin(a); return [hinge[0] + dx * c - dy * s, hinge[1] + dx * s + dy * c]; };
        const dirSign = (front[0] < hinge[0]) ? -1 : 1;
        const ja = mo * 0.38 * dirSign;
        const lowerF = rot(front, ja), lowerC = rot(chin, ja);
        if (mo > 0.03) {
          ctx.beginPath(); ctx.moveTo(corner[0], corner[1]); ctx.lineTo(front[0], front[1]); ctx.lineTo(lowerF[0], lowerF[1]); ctx.closePath();
          ctx.fillStyle = '#2a0c0c'; ctx.fill();
          ctx.beginPath(); ctx.moveTo(lerp(corner[0], lowerF[0], 0.4), lerp(corner[1], lowerF[1], 0.4)); ctx.quadraticCurveTo(lerp(front[0], lowerF[0], 0.6), lerp(front[1], lowerF[1], 0.6) + 0.004 * K, lowerF[0], lowerF[1]);
          ctx.strokeStyle = rgb(COAT.tongue); ctx.lineWidth = 0.012 * K * mo; ctx.stroke();
          ctx.beginPath(); ctx.moveTo(corner[0], corner[1]); ctx.quadraticCurveTo(lerp(lowerF[0], lowerC[0], 0.5), lerp(lowerF[1], lowerC[1], 0.5) + 0.006 * K, lowerF[0], lowerF[1]);
          ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.stroke();
        }
        ctx.beginPath(); ctx.moveTo(corner[0], corner[1]); ctx.quadraticCurveTo(lerp(corner[0], front[0], 0.55), lerp(corner[1], front[1], 0.55) + 0.006 * K, front[0], front[1]);
        ctx.strokeStyle = line; ctx.lineWidth = lw * 1.1; ctx.lineCap = 'round'; ctx.stroke();
        meas.parts.lipCorner = corner; meas.parts.lipFront = front;
      };
      const mouthVis = smooth(-0.05, 0.2, Math.max(eyes[0].f, eyes[1].f));
      meas.mouthVis = mouthVis;
      const headBehind = depth(hp) - depth(nb) < -0.035;
      meas.headBehind = headBehind;
      items.push({
        d: headBehind ? torsoD - 0.2 : hd + 0.4, name: 'head', fn: () => {
          // ears behind the skull first
          for (const er of ears) if (er.d < skD - 0.004) drawEar(er);
          // eyes and features sorted against the muzzle
          union(ctx, headPolys, C('tan'), line, lw);
          ctx.save(); clipTo(ctx, headPolys);
          sPolys(ctx, [ccw(Hell(hk.cap))]); ctx.fillStyle = C('saddle'); ctx.fill();
          shade(ctx, headPolys, L, K, 0.8);
          ctx.restore();
          const feats = [];
          for (const e of eyes) feats.push({ d: e.d, f: () => drawEye(e) });
          feats.push({ d: muzD, f: () => {
            ctx.save(); sPolys(ctx, [ccw(muzzle)]); ctx.fillStyle = C('tan'); ctx.fill();
            ctx.clip(); sPolys(ctx, [ccw(Hell(hk.mask))]); ctx.fillStyle = C('saddle'); ctx.fill();
            sPolys(ctx, [ccw(jowl)]); ctx.fillStyle = rgb(lit(COAT.saddle, L), 0.55); ctx.fill();
            shade(ctx, [muzzle], L, K, 0.5);
            ctx.restore();
            // muzzle contour where it lies over the skull
            ctx.save(); clipTo(ctx, flesh); ctx.beginPath(); smoothPath(ctx, ccw(muzzle)); ctx.strokeStyle = line; ctx.lineWidth = lw * 0.9; ctx.stroke(); ctx.restore();
          } });
          feats.push({ d: noseD + 0.001, f: drawNose });
          feats.push({ d: muzD + 0.0005, f: () => { if (mouthVis > 0.05) drawMouth(); } });
          feats.sort((a, b) => a.d - b.d).forEach(q => q.f());
          for (const er of ears) if (er.d >= skD - 0.004) drawEar(er);
        }
      });
    }

    items.sort((a, b) => a.d - b.d);
    meas.order = items.map(i => i.name);
    for (const it of items) if (!pose.only || pose.only.includes(it.name)) it.fn();
    meas.lw = lw;
    // measured extents of what was drawn
    return meas;
  }
  function shade(ctx, polys, L, K, k = 1) {
    // cool rim of sky light along the upper edges
    rim(ctx, polys, 0.008 * K, `rgba(175,195,255,${0.3 * k})`);
    // form shading: sky light from above, shadow beneath, warm door light from the left (the doorway side)
    const b = bbox(polys);
    const g = ctx.createLinearGradient(0, b[1], 0, b[3]);
    g.addColorStop(0, `rgba(170,190,255,${0.1 * k * (1 - L.warm)})`); g.addColorStop(0.55, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(8,8,30,${0.38 * k})`);
    ctx.fillStyle = g; ctx.fillRect(b[0] - 2, b[1] - 2, b[2] - b[0] + 4, b[3] - b[1] + 4);
    if (L.warm > 0.02) {
      const gx = ctx.createLinearGradient(b[0], 0, b[0] + (b[2] - b[0]) * 0.7, 0);
      gx.addColorStop(0, `rgba(255,186,96,${0.42 * L.warm * k})`); gx.addColorStop(1, 'rgba(255,186,96,0)');
      ctx.fillStyle = gx; ctx.fillRect(b[0] - 2, b[1] - 2, b[2] - b[0] + 4, b[3] - b[1] + 4);
    }
  }
  // rim light: the union minus itself shifted down, so only the outer upper silhouette lights (no inner mesh edges)
  let OFF = null;
  function rim(ctx, polys, d, color) {
    const b = bbox(polys), x0 = Math.floor(b[0] - 4), y0 = Math.floor(b[1] - 4), w = Math.ceil(b[2] - b[0] + 8), h = Math.ceil(b[3] - b[1] + 8);
    if (w <= 0 || h <= 0) return;
    if (!OFF) OFF = (typeof OffscreenCanvas !== 'undefined') ? new OffscreenCanvas(1400, 900) : null;
    if (!OFF) return;
    if (OFF.width < w || OFF.height < h) { OFF.width = Math.max(OFF.width, w); OFF.height = Math.max(OFF.height, h); }
    const o = OFF.getContext('2d');
    o.setTransform(1, 0, 0, 1, 0, 0); o.clearRect(0, 0, w, h); o.globalCompositeOperation = 'source-over';
    o.translate(-x0, -y0); sPolys(o, polys.map(ccw)); o.fillStyle = color; o.fill();
    o.globalCompositeOperation = 'destination-out'; o.translate(0, d); sPolys(o, polys.map(ccw)); o.fillStyle = '#000'; o.fill();
    o.setTransform(1, 0, 0, 1, 0, 0); o.globalCompositeOperation = 'source-over';
    ctx.drawImage(OFF, 0, 0, w, h, x0, y0, w, h);
  }
  function bbox(polys) { let a = 1e9, b = 1e9, c = -1e9, d = -1e9; for (const p of polys) for (const q of p) { a = Math.min(a, q[0]); b = Math.min(b, q[1]); c = Math.max(c, q[0]); d = Math.max(d, q[1]); } return [a, b, c, d]; }
  function wrap180(a) { a = ((a + 180) % 360 + 360) % 360 - 180; return a; }

  function homeFeet(pose, which) {
    const fr = dogFrame(pose), l = pose.lie, c = pose.crouch || 0;
    const H = [[lerp(0.165, 0.47, l), 0.07], [lerp(0.165, 0.47, l), -0.07], [lerp(-0.24 + 0.05 * c, -0.14, l), lerp(0.075, 0.1, l)], [lerp(-0.24 + 0.05 * c, -0.14, l), lerp(-0.075, -0.1, l)]];
    const out = H.map(([f, s]) => { const w = fr.fu(f, 0, s); return { x: w[0], z: w[2], y: 0 }; });
    return which === undefined ? out : out[which];
  }
  G.Rig = { homeFeet, PARAMS, HG, KEY_FIX, YAW_KEYS, PITCH_KEYS, TABLE, headKey, guideKey, drawDog, dogFrame, BODY, KZ, VIEW, proj, depth, wrap180, lit, rgb, mix, ellPoly, capsule, hull, union, clipTo, sPolys, smoothPath, ccw, shade, bbox, circlePts, ik2, COAT, lerp, clamp, smooth };
})(typeof window !== 'undefined' ? window : globalThis);
