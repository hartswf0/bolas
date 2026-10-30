/* SCION 19 · Moho Pro — Smart-Bone Character Laboratory.
   The dog rig, as a Moho-style project in code: a bone hierarchy, IK constraints on the legs, Smart-Bone corrective actions
   (a bone's angle drives a sculpted point offset on the vector mesh), and switch layers for the head drawn per view
   (profile, three-quarter front, front, three-quarter back, back), chosen by a view-control bone.

   Units: metres. Dog-local frame: x forward, y up, z the dog's right side. World: U along the porch (screen right),
   Y up, W toward the camera. A view angle psi (the view-control bone) maps dog-local to world:
     forward f = (-cos psi, sin psi) in (U, W): psi 0 = profile facing the door (screen left), 90 = front (toward us),
     180 = profile facing away from the door, 270 = back (facing away from us).
   Pure geometry: no canvas here. rig.frame(params) returns drawable groups (world coordinates) and measurements. */
(function (root, factory) { if (typeof module === 'object' && module.exports) module.exports = factory(); else root.Rig = factory(); })(this, function () {
  'use strict';
  const D = Math.PI / 180;
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const sm = t => { t = clamp(t); return t * t * (3 - 2 * t); };
  const ramp = (x, a, b) => sm((x - a) / (b - a));
  const tab = (T, x) => { if (x <= T[0][0]) return T[0][1]; for (let k = 1; k < T.length; k++) if (x <= T[k][0]) { const [x0, y0] = T[k - 1], [x1, y1] = T[k]; return y0 + (y1 - y0) * (x - x0) / (x1 - x0); } return T[T.length - 1][1]; };
  const wrap = a => { a = ((a % 360) + 360) % 360; return a; };
  const rel180 = a => { a = wrap(a); return a > 180 ? a - 360 : a; };

  /* ------------------------------------------------------------------ the model sheet (rest pose, standing) */
  const SHEET = {
    version: 'rig-v3',
    bones: {
      // name: [parent, rest head (x,y), note]
      root: [null, [0, 0], 'ground under mid-spine; carries U and the body view-control bone'],
      pelvis: ['root', [-0.28, 0.50], 'hip girdle'],
      spine: ['pelvis', [0.0, 0.52], 'mid back; its curl is a Smart Bone (spine-curl)'],
      withers: ['spine', [0.24, 0.55], 'shoulder blades'],
      neck: ['withers', [0.31, 0.52], 'neck base; its pitch is a Smart Bone (head-down)'],
      head: ['neck', [0.46, 0.73], 'atlas; head yaw relative to the body is a Smart Bone (neck-turn)'],
      view_body: ['root', [0, 0], 'view-control bone: body yaw psi_b'],
      view_head: ['head', [0, 0], 'view-control bone: head yaw psi_h; selects the head switch layer'],
      fore_upper: ['withers', [0.21, 0.42], 'humerus, IK chain to the wrist'], fore_lower: ['fore_upper', null, 'radius'], fore_paw: ['fore_lower', null, 'pastern+paw; its fold (elbow angle) is a Smart Bone (leg-fold, fore)'],
      hind_upper: ['pelvis', [-0.27, 0.44], 'femur, IK chain to the hock'], hind_lower: ['hind_upper', null, 'tibia'], hind_paw: ['hind_lower', null, 'metatarsus+paw; the stifle angle is a Smart Bone (leg-fold, hind)'],
      tail1: ['pelvis', [-0.38, 0.53], 'tail root'], tail2: ['tail1', null, ''], tail3: ['tail2', null, ''],
      ear_L: ['head', null, 'ear prick/flatten'], ear_R: ['head', null, ''],
    },
    len: { neck: 0.25, fore: [0.17, 0.20, 0.075], hind: [0.21, 0.21, 0.11], tail: [0.12, 0.12, 0.11] },
    side: { fore: 0.075, hind: 0.085 },
  };

  /* head landmarks in the head bone's frame (origin at the atlas; x toward the nose, y up, z right) */
  const HEAD = {
    K: [0.05, 0.035, 0], rK: 0.078,          // skull
    C: [0.10, -0.005, 0.045], rC: 0.05,       // cheeks (mirrored in z)
    M0: [0.15, 0.0, 0], rM0: 0.05,            // muzzle base (stop)
    M1: [0.245, -0.02, 0], rM1: 0.034,        // muzzle tip
    NT: [0.272, -0.006, 0], rN: 0.022,        // nose pad
    J: [0.19, -0.05, 0], rJ: 0.026,           // chin
    E: [0.118, 0.047, 0.043],                 // eyes (mirrored)
    EBf: [0.07, 0.092, 0.036], EBb: [-0.015, 0.082, 0.066],  // ear base front / back (mirrored)
    ETup: [0.0, 0.22, 0.088], ETflat: [-0.10, 0.11, 0.115], // ear tip pricked / flattened back (mirrored)
    OCC: [-0.03, 0.06, 0],
  };
  // the head is drawn 1.22x its anatomical sheet: a cartoon head reads at film scale (applied once, to every view alike)
  const HS = 1.22; Object.keys(HEAD).forEach(k => { HEAD[k] = Array.isArray(HEAD[k]) ? HEAD[k].map(v => v * HS) : HEAD[k] * HS; });

  /* the head switch layers: one drawing per canonical view, chosen by the view_head bone's angle relative to camera */
  const VIEWS = [
    { a: 0, layer: 'profile' }, { a: 45, layer: 'three_quarter_front' }, { a: 90, layer: 'front' }, { a: 135, layer: 'three_quarter_front' },
    { a: 180, layer: 'profile' }, { a: 225, layer: 'three_quarter_back' }, { a: 270, layer: 'back' }, { a: 315, layer: 'three_quarter_back' },
  ];
  function headLayer(psiH) { const a = wrap(Math.round(wrap(psiH) / 45) * 45); return VIEWS.find(v => v.a === a) || VIEWS[0]; }

  /* Smart-Bone corrective actions: the versioned correction table. Each action is keyed on one bone's angle; its weight is a
     smoothstep of that angle between a0 and a1; the action moves named mesh points (offsets in metres, dog-local) or adds a
     sculpted shape. These are applied in buildDog below; the table is exported so tests and the method can read it. */
  const CORRECTIONS = [
    { id: 'neck-turn', driver: 'head yaw relative to body (deg, |rel|)', a0: 25, a1: 120, effect: 'shoulder bulge on the turning side (+0.045 m radius at the neck base, pushed 0.05 m toward the turn), neck shortened 12% so the jaw clears the shoulder, a skin fold stroke at the neck base, ears swing back 30% (they lead the turn)' },
    { id: 'spine-curl', driver: 'spine bone curl = crouch (0..1, 0.5 == 18 deg of hunch)', a0: 0.1, a1: 0.9, effect: 'waist point raised 0.035 m (arched back), belly tucked (waist radius -0.018 m), rump dropped 0.03 m, tail tucks' },
    { id: 'leg-fold-hind', driver: 'stifle angle (deg between femur and tibia)', a0: 100, a1: 40, effect: 'haunch mass grows (+0.035 m thigh radius at the hip, +0.03 m at mid thigh) and moves 0.03 m forward; hip point lowered so the folded thigh reads round, not as a stick' },
    { id: 'leg-fold-fore', driver: 'elbow angle (deg between humerus and radius)', a0: 120, a1: 60, effect: 'elbow nub (0.032 m) appears behind the joint; chest point drops 0.06 m and shrinks 0.025 m so the chest lies on the floor between the forearms' },
    { id: 'head-down', driver: 'neck pitch (deg, below horizontal)', a0: -10, a1: -45, effect: 'nape crest raised 0.02 m and neck base thickened 0.015 m so the line of the back flows into the lowered head; a throat fold stroke' },
    { id: 'jaw-rest', driver: 'rest (chin on paws, 0..1) through head pitch', a0: 0.2, a1: 0.9, effect: 'chin pushed back 0.01 m and the jowl flattened onto the paw; eye lid half closed' },
  ];
  const cw = (id, v) => { const c = CORRECTIONS.find(c => c.id === id); return sm((v - c.a0) / (c.a1 - c.a0)); };

  /* ------------------------------------------------------------------ two-bone IK (sagittal plane), the knee/elbow side fixed */
  function ik2(R, T, L1, L2, bendSign) {
    let dx = T[0] - R[0], dy = T[1] - R[1]; let d = Math.hypot(dx, dy);
    const dmax = (L1 + L2) * 0.9995, dmin = Math.abs(L1 - L2) + 1e-4;
    let reach = true;
    if (d > dmax) { reach = false; } const dd = clamp(d, dmin, dmax);
    const ux = dx / d, uy = dy / d;
    const a = (L1 * L1 - L2 * L2 + dd * dd) / (2 * dd), h = Math.sqrt(Math.max(0, L1 * L1 - a * a));
    // perpendicular (rotated +90) is (-uy, ux); choose the one whose x has the requested sign
    let px = -uy, py = ux; if (Math.sign(px || 1) !== bendSign) { px = -px; py = -py; }
    const J = [R[0] + ux * a + px * h, R[1] + uy * a + py * h];
    const E = [R[0] + ux * dd, R[1] + uy * dd];
    return { J, E, reach, d };
  }

  /* ------------------------------------------------------------------ build the dog for one frame
     P: { U, psiB, psiH, crouch, lie, head, rest, look, ear, tail, wag, t, gait: [{x, lift} x4 local foot offsets], turnLift } */
  function buildDog(P) {
    const psiB = P.psiB, fb = [-Math.cos(psiB * D), Math.sin(psiB * D)], rb = [-Math.sin(psiB * D), -Math.cos(psiB * D)];
    const toW = (p) => [P.U + p[0] * fb[0] + p[2] * rb[0], p[1], p[0] * fb[1] + p[2] * rb[1]];   // dog-local -> world [U, Y, W]
    const lie = sm(P.lie), cr = clamp(P.crouch), restW = clamp(P.rest);
    const sCurl = cw('spine-curl', cr);
    // --- spine heights
    const bob = P.bob || 0;
    const pel = [-0.28 + 0.02 * lie, lerp(0.50 - 0.085 * cr - 0.03 * sCurl, 0.235, lie) + bob, 0];
    const mid = [0.0, lerp(0.52 - 0.075 * cr + 0.035 * sCurl, 0.25, lie) + bob, 0];
    const wit = [0.24, lerp(0.55 - 0.10 * cr, 0.295, lie) + bob * 0.7, 0];
    const nb = [wit[0] + 0.07, wit[1] - 0.03, 0];
    // --- neck and head
    let alpha = tab([[0, -58], [0.15, -48], [0.3, -40], [0.45, -32], [0.6, -5], [0.7, 12], [0.9, 40], [1.25, 48]], P.head);
    let beta = tab([[0, -50], [0.15, -42], [0.45, -24], [0.7, -14], [0.9, -8], [1.25, -2]], P.head);
    alpha = lerp(alpha, -36, restW); beta = lerp(beta, 2, restW);       // chin on the paws
    if (P.look > 0) { alpha = lerp(alpha, 8, clamp(P.look)); beta = lerp(beta, -10, clamp(P.look)); }   // looking in: level, not lifted
    const rel = rel180(P.psiH - psiB);                 // continuous head yaw relative to the body
    const wNeck = cw('neck-turn', Math.abs(rel));
    const wDown = cw('head-down', alpha);
    const lam = 0.5 * rel * D;                          // the neck carries half the turn, the head the rest
    const nLen = SHEET.len.neck * (1 - 0.12 * wNeck);
    const nv = [Math.cos(alpha * D) * Math.cos(lam), Math.sin(alpha * D), -Math.cos(alpha * D) * Math.sin(lam)];
    const H = [nb[0] + nv[0] * nLen, nb[1] + nv[1] * nLen, nb[2] + nv[2] * nLen];
    const nmid = [nb[0] + nv[0] * nLen * 0.5, nb[1] + nv[1] * nLen * 0.5 + 0.02 * (1 - wDown) * 0 + 0.018 * wDown, nb[2] + nv[2] * nLen * 0.5];
    // --- head switch layer: snapped view, landmarks pitched (beta) and yawed by the snapped relative yaw
    const view = headLayer(P.psiH);
    const relS = rel180(view.a - psiB);
    const lamS = relS * D, cb = Math.cos(beta * D), sb = Math.sin(beta * D);
    const hf = [Math.cos(lamS), 0, -Math.sin(lamS)], hr = [Math.sin(lamS), 0, Math.cos(lamS)];
    const headPt = (q, mirror) => {
      const z = mirror ? -q[2] : q[2];
      const x1 = q[0] * cb - q[1] * sb, y1 = q[0] * sb + q[1] * cb;   // pitch about z
      return [H[0] + x1 * hf[0] + z * hr[0], H[1] + y1, H[2] + x1 * hf[2] + z * hr[2]];
    };
    // --- legs: IK to the foot targets; foot targets blend from the gait (standing) to the folded lying pose
    const legs = [];
    const LEGS = [
      { id: 'fore_L', fore: true, z: -SHEET.side.fore, ph: 0.25 }, { id: 'fore_R', fore: true, z: SHEET.side.fore, ph: 0.75 },
      { id: 'hind_L', fore: false, z: -SHEET.side.hind, ph: 0.0 }, { id: 'hind_R', fore: false, z: SHEET.side.hind, ph: 0.5 },
    ];
    LEGS.forEach((L, k) => {
      const len = L.fore ? SHEET.len.fore : SHEET.len.hind;
      const R = L.fore ? [wit[0] - 0.03, wit[1] - 0.13] : [pel[0] + 0.01, pel[1] - 0.06];
      const g = (P.gait && P.gait[k]) || { x: 0, lift: 0 };
      const standX = (L.fore ? 0.235 : -0.265) + g.x, standY = g.lift;
      const lieX = L.fore ? 0.53 : -0.12, lieZ = L.z;
      const F = [lerp(standX, lieX, lie), lerp(standY, 0, lie), lerp(L.z, lieZ, lie)];
      // bottom segment direction: near vertical standing, flat forward lying
      const angStand = L.fore ? -78 : -84, ang = lerp(angStand, 0, lie) + (L.fore ? 0 : 0) + (g.lift > 0 ? (L.fore ? -25 : 20) * clamp(g.lift / 0.06) : 0);
      const d3 = [Math.cos(ang * D), Math.sin(ang * D)];
      const T = [F[0] - d3[0] * len[2], F[1] - d3[1] * len[2]];
      const s = ik2(R, T, len[0], len[1], L.fore ? -1 : 1);
      const ang12 = (() => { const a = [R[0] - s.J[0], R[1] - s.J[1]], b = [s.E[0] - s.J[0], s.E[1] - s.J[1]]; return Math.acos(clamp((a[0] * b[0] + a[1] * b[1]) / (Math.hypot(...a) * Math.hypot(...b)), -1, 1)) / D; })();
      const cross = (s.J[0] - R[0]) * (s.E[1] - R[1]) - (s.J[1] - R[1]) * (s.E[0] - R[0]);
      const Fe = [s.E[0] + d3[0] * len[2], s.E[1] + d3[1] * len[2]];   // paw contact actually reached
      legs.push({ ...L, R: [R[0], R[1], L.z], J: [s.J[0], s.J[1], L.z], E: [s.E[0], s.E[1], F[2]], F: [Fe[0], Fe[1], F[2]], reach: s.reach, angle: ang12, bendCross: cross, len, dir: d3 });
    });
    // --- tail
    const tl = SHEET.len.tail; const tailBase = [pel[0] - 0.10, pel[1] + 0.03 - 0.02 * sCurl, 0];
    let ta = tab([[0, 45], [0.25, 20], [0.5, -18], [0.8, -48], [1.0, -62], [1.35, -100]], P.tail);
    const tc = tab([[0, -8], [0.5, -14], [1.0, -20], [1.35, 35]], P.tail);
    ta = lerp(ta, -40, lie * (P.tail < 0.9 ? 1 : 0.6));
    const wagA = (P.wag || 0) * 38 * Math.sin(2 * Math.PI * 3.1 * (P.t || 0));
    const tailPts = [tailBase]; let a = ta;
    for (let k = 0; k < 3; k++) {
      const segA = lie > 0.5 ? lerp(a, [-40, -12, -2][k], lie) : a;
      const yaw = wagA * D * (0.4 + 0.3 * k);
      const p = tailPts[k];
      const lyingFloor = lie > 0.3;
      let nx = p[0] - Math.cos(segA * D) * tl[k] * Math.cos(yaw), ny = p[1] + Math.sin(segA * D) * tl[k], nz = p[2] + Math.sin(yaw) * tl[k] * Math.cos(segA * D);
      if (lyingFloor) ny = Math.max(ny, 0.025 + 0.02 * (2 - k));
      tailPts.push([nx, ny, nz]); a += tc;
    }
    // --- correction weights from the legs
    const hindNear = legs[2], foreNear = legs[0];
    const wHind = Math.max(cw('leg-fold-hind', legs[2].angle), cw('leg-fold-hind', legs[3].angle));
    const wFore = Math.max(cw('leg-fold-fore', legs[0].angle), cw('leg-fold-fore', legs[1].angle));
    const wJaw = cw('jaw-rest', restW);
    // --- torso nodes (the vector mesh of the body: a chain of sculpted masses bound to the spine bones)
    const turnSide = Math.sign(rel) || 1;    // +: the head turns toward the dog's left (-z)... (see lam convention: z = -sin(lam))
    const tN = [
      ['rump', [pel[0] - 0.075, pel[1] - 0.01 - 0.03 * sCurl, 0], 0.095],
      ['hip', [pel[0] + 0.02 + 0.03 * wHind, pel[1] - 0.03 - 0.02 * wHind, 0], 0.118 + 0.02 * wHind],
      ['waist', [mid[0] - 0.02, mid[1] - 0.02, 0], 0.095 - 0.018 * sCurl],
      ['ribs', [wit[0] - 0.10, wit[1] - 0.09 + 0.03 * lie, 0], 0.15 - 0.01 * lie],
      ['chest', [wit[0] + 0.02, wit[1] - 0.12 + 0.06 * wFore * lie, 0], 0.155 - 0.03 * wFore],
      ['withers', [wit[0], wit[1] - 0.01, 0], 0.085],
      ['neckbase', [nb[0] + 0.02, nb[1] - 0.05, 0], 0.10 + 0.015 * wDown],
      ['neck0', [nb[0], nb[1] + 0.012 * wDown, nb[2]], 0.098 + 0.015 * wDown],
      ['neckmid', nmid, 0.088],
      ['neck1', [H[0] - 0.01 * hf[0], H[1] + 0.01, H[2]], 0.078],
    ];
    const node = n => tN.find(q => q[0] === n);
    const links = [['rump', 'hip'], ['hip', 'waist'], ['waist', 'ribs'], ['ribs', 'chest'], ['ribs', 'withers'], ['withers', 'neckbase'], ['chest', 'neckbase'], ['neckbase', 'neck0'], ['neck0', 'neckmid'], ['neckmid', 'neck1'], ['withers', 'neck0']];
    // neck-turn corrective: the shoulder bulges toward the turn
    if (wNeck > 0.01) {
      const side = -Math.sin(lam) >= 0 ? 1 : -1;     // z side the neck swings to
      tN.push(['shoulderbulge', [nb[0] - 0.03, nb[1] - 0.01, side * 0.05 * wNeck], 0.045 * wNeck + 0.04]);
      links.push(['withers', 'shoulderbulge'], ['shoulderbulge', 'neckmid']);
    }

    /* ---------------- drawable groups (world coordinates) */
    const groups = [];
    const COL = P.colors || {};
    const coat = COL.coat || '#c8843f', coatFar = COL.coatFar || '#9a5f2d', cream = COL.cream || '#f3e6c4', earBack = COL.earBack || '#6e4026', earIn = COL.earIn || '#d99a86', ink = COL.ink || '#1b1714';
    const cap = (a, ra, b, rb) => ({ t: 'cap', a: toW(a), ra, b: toW(b), rb });
    const circ = (c, r) => ({ t: 'circ', c: toW(c), r });
    // torso
    const torso = { name: 'torso', w: toW([0, 0, 0])[2], fill: coat, parts: [], patches: [], details: [] };
    links.forEach(([a1, b1]) => { const A = node(a1), B = node(b1); torso.parts.push(cap(A[1], A[2], B[1], B[2])); });
    // chest bib patch (cream) when the chest front is not turned away
    const chestFront = [wit[0] + 0.13, wit[1] - 0.12, 0];
    // switch: the bib exists only while the chest front is toward the camera (W component of the body's forward >= -0.3)
    const chestVisible = Math.sin(psiB * D) > -0.3;
    if (chestVisible) torso.patches.push({ ...circ(chestFront, 0.10), fill: cream });
    if (chestVisible) torso.patches.push({ ...cap([nb[0] + 0.07, nb[1] - 0.06, 0], 0.06, [nb[0] + nv[0] * nLen * 0.7 + 0.03, nb[1] + nv[1] * nLen * 0.7 - 0.04, nv[2] * nLen * 0.7], 0.045), fill: cream });
    // flank fold line (spine-curl) and neck-turn fold, drawn as tapered strokes
    if (sCurl > 0.05) torso.details.push({ t: 'stroke', pts: [toW([mid[0] - 0.05, mid[1] - 0.05, -0.1]), toW([mid[0] + 0.02, mid[1] - 0.09, -0.1]), toW([mid[0] + 0.08, mid[1] - 0.10, -0.1])], w: 0.6 * sCurl, side: 'near' });
    if (wNeck > 0.15) {
      const side = -Math.sin(lam) >= 0 ? 1 : -1;
      torso.details.push({ t: 'stroke', pts: [toW([nb[0] - 0.05, nb[1] + 0.05, side * 0.07]), toW([nb[0] + 0.0, nb[1] + 0.02, side * 0.09]), toW([nb[0] + 0.05, nb[1] - 0.04, side * 0.08])], w: 0.9 * wNeck, side: 'free' });
    }
    if (wDown > 0.2) torso.details.push({ t: 'stroke', pts: [toW([nb[0] + 0.07, nb[1] - 0.02, -0.06]), toW([nb[0] + 0.10, nb[1] - 0.06, -0.06])], w: 0.6 * wDown, side: 'near' });
    groups.push(torso);
    // tail
    const tail = { name: 'tail', w: toW(tailPts[1])[2] - 0.002, fill: coat, parts: [], patches: [], details: [] };
    const tr = [0.034, 0.03, 0.024, 0.016];
    for (let k = 0; k < 3; k++) tail.parts.push(cap(tailPts[k], tr[k], tailPts[k + 1], tr[k + 1]));
    tail.patches.push({ ...circ(tailPts[3], 0.03), fill: cream });
    groups.push(tail);
    // legs
    legs.forEach((L) => {
      const far = (toW(L.R)[2] < toW([L.R[0], L.R[1], 0])[2]);
      const g = { name: L.id, w: toW(L.R)[2] + (L.fore ? 0.001 : 0), fill: far ? coatFar : coat, parts: [], patches: [], details: [], leg: true, far };
      if (L.fore) {
        g.parts.push(cap(L.R, 0.088, L.J, 0.052), cap(L.J, 0.049, L.E, 0.037), cap(L.E, 0.035, L.F, 0.031));
        if (wFore > 0.05) g.parts.push(circ([L.J[0] - 0.012, L.J[1] + 0.005, L.J[2]], 0.032 * wFore + 0.01));
      } else {
        const thighR = 0.112 + 0.035 * wHind, midT = [lerp(L.R[0], L.J[0], 0.45), lerp(L.R[1], L.J[1], 0.45), L.z];
        g.parts.push(cap(L.R, thighR, midT, 0.075 + 0.03 * wHind), cap(midT, 0.082 + 0.03 * wHind, L.J, 0.056), cap(L.J, 0.052, L.E, 0.036), cap(L.E, 0.034, L.F, 0.031));
      }
      // paw: an oval pad forward of the contact, cream sock
      const fwd = L.dir[0] > 0.6 ? 0.035 : 0.03;
      const pawC = [L.F[0] + fwd * 0.6, L.F[1] + 0.022, L.F[2]];
      g.parts.push(cap([L.F[0] - 0.01, L.F[1] + 0.024, L.F[2]], 0.026, [L.F[0] + fwd, L.F[1] + 0.02, L.F[2]], 0.024));
      g.patches.push({ ...cap([L.F[0] - 0.02, L.F[1] + 0.03, L.F[2]], 0.03, [L.F[0] + fwd + 0.01, L.F[1] + 0.02, L.F[2]], 0.03), fill: cream });
      if (!far) g.details.push({ t: 'stroke', pts: [toW([pawC[0] + 0.012, pawC[1] + 0.012, L.F[2]]), toW([pawC[0] + 0.02, pawC[1] - 0.012, L.F[2]])], w: 0.5, side: 'free' });
      groups.push(g);
    });
    // head (switch layer)
    const headGroups = drawHead(P, view, headPt, { coat, cream, earBack, earIn, ink }, wNeck, wJaw, rel);
    const Kw = headPt(HEAD.K);
    const headW = Kw[2] - toW([0, 0, 0])[2];
    headGroups.forEach((g, k) => { g.w = headW + 0.0005 + k * 1e-5; groups.push(g); });
    // depth order: far first. Torso is at 0; legs at their root depth; head ahead of the torso unless it faces away.
    const faceAway = view.layer === 'back' || view.layer === 'three_quarter_back';
    groups.forEach(g => { g.wz = g.w - toW([0, 0, 0])[2]; if (g.name.startsWith('head')) g.wz = faceAway ? -0.5 + g.wz * 1e-3 : 0.02 + g.wz * 1e-3; if (g.name === 'torso') g.wz = 0; if (g.name === 'tail') g.wz = (toW(tailPts[2])[2] - toW([0, 0, 0])[2]) - 0.003; });
    groups.sort((a, b) => a.wz - b.wz);

    /* ---------------- measurements (dog-local -> world) */
    const top = (p, r) => p[1] + r;
    const meas = {
      psiB, psiH: wrap(P.psiH), rel, layer: view.layer, viewA: view.a,
      facing: Math.cos(psiB * D) >= 0 ? 1 : -1,                 // +1 faces the door (screen left)
      headFacing: Math.cos(P.psiH * D) >= 0 ? 1 : -1,
      backY: Math.max(top(node('withers')[1], 0.085), top(node('hip')[1], node('hip')[2])),
      headTopY: Math.max(headPt(HEAD.K)[1] + HEAD.rK, headPt(lerp3(HEAD.ETflat, HEAD.ETup, clamp(P.ear)))[1]),
      skullTopY: headPt(HEAD.K)[1] + HEAD.rK,
      nose: headPt(HEAD.NT), skull: headPt(HEAD.K), atlas: H,
      noseW: toWorldPt(toW, headPt(HEAD.NT)), skullW: toWorldPt(toW, headPt(HEAD.K)),
      pelvisW: toW(pel), withersW: toW(wit), tailTipW: toW(tailPts[3]), tailRootW: toW(tailPts[0]),
      legs: legs.map(L => ({ id: L.id, R: toW(L.R), J: toW(L.J), E: toW(L.E), F: toW(L.F), angle: L.angle, cross: L.bendCross, reach: L.reach, len: L.len, lift: L.F[1] })),
      corrections: { 'neck-turn': wNeck, 'spine-curl': sCurl, 'leg-fold-hind': wHind, 'leg-fold-fore': wFore, 'head-down': wDown, 'jaw-rest': wJaw },
      lie, alpha, beta,
    };
    return { groups, meas };
  }
  const lerp3 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
  const toWorldPt = (toW, p) => toW(p);

  /* ------------------------------------------------------------------ the head drawings, one per switch layer */
  function drawHead(P, view, hp, C, wNeck, wJaw, rel) {
    const toW = P._toW;
    const ear = clamp(P.ear), earBackSwing = 0.3 * wNeck;
    const tipOf = (m) => hp(lerp3(lerp3(HEAD.ETflat, HEAD.ETup, ear), HEAD.ETflat, earBackSwing), m);
    const E = P._toWorld;
    const W = p => E(p);
    const g = (name, fill, parts, patches, details) => ({ name, fill, parts: parts || [], patches: patches || [], details: details || [] });
    const cap = (a, ra, b, rb) => ({ t: 'cap', a: W(a), ra, b: W(b), rb });
    const circ = (c, r) => ({ t: 'circ', c: W(c), r });
    const poly = (pts, extra) => ({ t: 'poly', pts: pts.map(W), ...(extra || {}) });
    const stroke = (pts, w, extra) => ({ t: 'stroke', pts: pts.map(W), w, ...(extra || {}) });
    const dot = (c, r, fill) => ({ t: 'dot', c: W(c), r, fill });
    const K = hp(HEAD.K), M0 = hp(HEAD.M0), M1 = hp([HEAD.M1[0] - 0.008 * wJaw, HEAD.M1[1], 0]), NT = hp(HEAD.NT), J = hp([HEAD.J[0] - 0.01 * wJaw, HEAD.J[1] + 0.008 * wJaw, 0]);
    const CL = hp(HEAD.C, true), CR = hp(HEAD.C, false), EL = hp(HEAD.E, true), ER = hp(HEAD.E, false);
    const earPoly = (m, inner) => {
      const bf = hp(HEAD.EBf, m), bb = hp(HEAD.EBb, m), tp = tipOf(m);
      if (!inner) {
        const mid1 = lerp3(bf, tp, 0.5), mid2 = lerp3(bb, tp, 0.5);
        const bulge = (p, q, s) => [p[0] + (p[0] - q[0]) * s, p[1] + (p[1] - q[1]) * s, p[2] + (p[2] - q[2]) * s];
        return [bf, bulge(mid1, lerp3(bf, bb, 0.5), 0.30), tp, bulge(mid2, lerp3(bf, bb, 0.5), 0.30), bb];
      }
      const c = lerp3(lerp3(bf, bb, 0.5), tp, 0.35);
      return [lerp3(bf, c, 0.35), lerp3(tp, c, 0.3), lerp3(bb, c, 0.45)];
    };
    // which ear is nearer the camera (world W)
    const wL = W(hp(HEAD.EBb, true))[2], wR = W(hp(HEAD.EBb, false))[2];
    const nearM = wL > wR, farM = !nearM;     // mirror=true is the left ear
    const skull = (extra) => g('head_skull', C.coat, [circ(K, HEAD.rK), cap(K, HEAD.rK * 0.92, hp(HEAD.OCC), 0.055), circ(CL, HEAD.rC), circ(CR, HEAD.rC), cap(CL, HEAD.rC * 0.9, M0, HEAD.rM0 * 0.95), cap(CR, HEAD.rC * 0.9, M0, HEAD.rM0 * 0.95)], [], extra || []);
    const muzzle = (extra, patchFill) => g('head_muzzle', C.cream, [cap(M0, HEAD.rM0, M1, HEAD.rM1), cap(M1, HEAD.rM1 * 0.8, J, HEAD.rJ), cap(M0, HEAD.rM0 * 0.8, J, HEAD.rJ)], [], extra || []);
    const earG = (m, front, name) => g(name, front ? C.coat : C.earBack, [poly(earPoly(m, false), { smooth: true })], front ? [{ ...poly(earPoly(m, true), { smooth: true }), fill: C.earIn }] : [], []);
    const nose = () => g('head_nose', '#221c18', [circ(NT, HEAD.rN)], [], []);
    const eyeDots = (list, lid) => list.map(([c, r]) => dot(c, r, '#16110e')).concat(list.map(([c, r]) => dot([c[0] + r * 0.2, c[1] + r * 0.35, c[2]], r * 0.28, '#f6efe0')))
      .concat(lid > 0.3 ? list.map(([c, r]) => stroke([[c[0] - 0.014, c[1] + 0.002, c[2]], [c[0], c[1] + 0.006, c[2]], [c[0] + 0.012, c[1] + 0.002, c[2]]], 0.7)) : []);
    let out = [];
    const L = view.layer;
    if (L === 'profile') {
      const nearE = nearM ? EL : ER;
      const mouth = stroke([hp([0.255, -0.03, 0]), hp([0.20, -0.032, 0]), hp([0.15, -0.022, 0])].map(p => p), 0.55);
      const brow = stroke([hp([0.095, 0.092, nearM ? -0.04 : 0.04]), hp([0.125, 0.09, nearM ? -0.045 : 0.045]), hp([0.148, 0.078, nearM ? -0.04 : 0.04])], 0.45);
      const jowl = stroke([hp([0.13, -0.035, 0]), hp([0.105, -0.05, 0]), hp([0.07, -0.04, 0])], 0.45);
      out = [earG(farM, false, 'head_ear_far'), skull([brow, jowl]), muzzle([mouth]), nose(), earG(nearM, true, 'head_ear_near'), g('head_eyes', null, [], [], eyeDots([[nearE, 0.017]], wJaw))];
    } else if (L === 'three_quarter_front') {
      const nearE = nearM ? EL : ER, farE = nearM ? ER : EL;
      const stop = stroke([hp([0.13, 0.065, 0]), hp([0.15, 0.03, 0]), hp([0.155, 0.0, 0])], 0.5);
      const mouth = stroke([hp([0.265, -0.035, 0]), hp([0.22, -0.04, nearM ? -0.02 : 0.02]), hp([0.17, -0.025, nearM ? -0.04 : 0.04])], 0.55);
      out = [earG(farM, true, 'head_ear_far'), skull([stroke([hp([0.1, 0.085, nearM ? -0.03 : 0.03]), hp([0.13, 0.075, nearM ? -0.05 : 0.05])], 0.5)]), muzzle([stop, mouth]), nose(), earG(nearM, true, 'head_ear_near'), g('head_eyes', null, [], [], eyeDots([[nearE, 0.017], [farE, 0.014]], wJaw))];
    } else if (L === 'front') {
      const blaze = { ...cap(hp([0.06, 0.10, 0]), 0.016, M0, 0.03), fill: C.cream };
      const mouth = stroke([hp([0.20, -0.04, -0.03]), hp([0.235, -0.045, 0]), hp([0.20, -0.04, 0.03])], 0.6);
      const philtrum = stroke([hp([0.27, -0.02, 0]), hp([0.255, -0.04, 0])], 0.5);
      const sk = skull([]); sk.patches.push(blaze);
      out = [earG(true, true, 'head_ear_L'), earG(false, true, 'head_ear_R'), sk, muzzle([mouth, philtrum]), nose(), g('head_eyes', null, [], [], eyeDots([[EL, 0.016], [ER, 0.016]], wJaw))];
    } else if (L === 'three_quarter_back') {
      // the muzzle and the far eye fall behind the skull; we see the back of the skull, the cheek edge and the ears from behind
      const nape = stroke([hp([-0.02, 0.0, nearM ? -0.03 : 0.03]), hp([0.0, -0.04, nearM ? -0.05 : 0.05]), hp([0.05, -0.06, nearM ? -0.06 : 0.06])], 0.55);
      const cheekEdge = stroke([hp([0.09, 0.07, nearM ? -0.07 : 0.07]), hp([0.12, 0.02, nearM ? -0.075 : 0.075]), hp([0.12, -0.03, nearM ? -0.06 : 0.06])], 0.5);
      out = [nose(), muzzle([]), earG(farM, false, 'head_ear_far'), skull([nape, cheekEdge]), earG(nearM, false, 'head_ear_near')];
    } else { // back
      const part = stroke([hp([0.04, 0.11, 0]), hp([-0.02, 0.07, 0]), hp([-0.04, 0.0, 0])], 0.55);
      const nape = stroke([hp([-0.03, -0.01, -0.04]), hp([-0.035, -0.04, 0])], 0.45);
      out = [muzzle([]), skull([part, nape]), earG(true, false, 'head_ear_L'), earG(false, false, 'head_ear_R')];
    }
    return out;
  }

  /* the public frame function: wraps buildDog so drawHead sees the dog-local->world transform */
  function frame(P) {
    const psiB = P.psiB, fb = [-Math.cos(psiB * D), Math.sin(psiB * D)], rb = [-Math.sin(psiB * D), -Math.cos(psiB * D)];
    const toW = (p) => [P.U + p[0] * fb[0] + p[2] * rb[0], p[1], p[0] * fb[1] + p[2] * rb[1]];
    return buildDog(Object.assign({}, P, { _toWorld: toW }));
  }

  return { SHEET, HEAD, VIEWS, CORRECTIONS, headLayer, frame, ik2, tab, sm, ramp, clamp, lerp, wrap, rel180, D };
});
