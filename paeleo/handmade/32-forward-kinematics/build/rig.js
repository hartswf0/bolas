// SCION 32 · Forward Kinematics: the typed skeleton, the local transforms, and the pose of every joint at every score frame.
// Pure forward kinematics: every world transform is parent_world x T(pivot offset) x R(local angles), evaluated root-first.
// There is no IK solve at runtime. Planted feet come from the animator's key angles (stride keys, see GAIT below).
// Runs in Node (tests, trace) and in the browser (render). Units: metres, radians, seconds; 24 fps score frames.
(function (G) {
  'use strict';
  const D2R = Math.PI / 180;
  // ---------- 4x4 column-major matrices ----------
  const M = {
    I: () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    mul(a, b) {
      const o = new Array(16);
      for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
        o[c * 4 + r] = a[r] * b[c * 4] + a[4 + r] * b[c * 4 + 1] + a[8 + r] * b[c * 4 + 2] + a[12 + r] * b[c * 4 + 3];
      }
      return o;
    },
    T: (x, y, z) => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1],
    RX(a) { const c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]; },
    RY(a) { const c = Math.cos(a), s = Math.sin(a); return [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]; },
    RZ(a) { const c = Math.cos(a), s = Math.sin(a); return [c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]; },
    S: (x, y, z) => [x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0, 0, 0, 0, 1],
    p(m, v) { return [m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12], m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13], m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14]]; },
    d(m, v) { return [m[0] * v[0] + m[4] * v[1] + m[8] * v[2], m[1] * v[0] + m[5] * v[1] + m[9] * v[2], m[2] * v[0] + m[6] * v[1] + m[10] * v[2]]; },
    inv(m) { // inverse of a similarity (uniform scale x rotation + translation)
      const s2 = m[0] * m[0] + m[1] * m[1] + m[2] * m[2];
      const r = [m[0] / s2, m[4] / s2, m[8] / s2, 0, m[1] / s2, m[5] / s2, m[9] / s2, 0, m[2] / s2, m[6] / s2, m[10] / s2, 0, 0, 0, 0, 1];
      const t = M.d(r, [m[12], m[13], m[14]]);
      r[12] = -t[0]; r[13] = -t[1]; r[14] = -t[2]; return r;
    },
  };
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const ease = t => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
  const ramp = (t, a, b) => ease((t - a) / (b - a));
  const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);

  // ---------- the typed joint graph ----------
  // Each joint: parent, pivot offset in the parent's frame (metres), rotation order of its local angles.
  // Dog local axes: +x toward the muzzle, +y up, +z the dog's right side. Pitch = rotation about z (positive lifts +x / swings a
  // hanging limb forward), yaw = about y, roll = about x. Child limb segments sit 13 mm further out on their pins, as a real toy.
  const L1 = 0.15, L2 = 0.15, PAW_H = 0.034, PIN = 0.014;
  const DOG = [
    ['root', null, [0, 0, 0]],
    ['pelvis', 'root', [0, 0, 0]],
    ['waist', 'pelvis', [0.18, 0.012, 0]],          // the pin between the hind block and the chest block
    ['neck', 'waist', [0.215, 0.075, 0]],
    ['head', 'neck', 'ANCHOR'],                      // view-specific anchor: offset chosen per view (see HEAD_ANCHORS)
    ['earR0', 'head', [-0.03, 0.058, 0.05]], ['earR1', 'earR0', [0, -0.06, 0.003]],
    ['earL0', 'head', [-0.03, 0.058, -0.05]], ['earL1', 'earL0', [0, -0.06, -0.003]],
    ['cloth', 'waist', [-0.035, 0.088, 0]],         // felt saddle cloth, buttoned to the waist pin
    ['flapR0', 'cloth', [0, -0.004, 0.083]], ['flapR1', 'flapR0', [0, -0.055, 0.002]],
    ['flapL0', 'cloth', [0, -0.004, -0.083]], ['flapL1', 'flapL0', [0, -0.055, -0.002]],
    ['shoulderR', 'waist', [0.17, -0.037, 0.074]], ['elbowR', 'shoulderR', [0, -L1, PIN]], ['fpawR', 'elbowR', [0, -L2, PIN]],
    ['shoulderL', 'waist', [0.17, -0.037, -0.074]], ['elbowL', 'shoulderL', [0, -L1, -PIN]], ['fpawL', 'elbowL', [0, -L2, -PIN]],
    ['hipR', 'pelvis', [-0.005, -0.025, 0.074]], ['kneeR', 'hipR', [0, -L1, PIN]], ['hpawR', 'kneeR', [0, -L2, PIN]],
    ['hipL', 'pelvis', [-0.005, -0.025, -0.074]], ['kneeL', 'hipL', [0, -L1, -PIN]], ['hpawL', 'kneeL', [0, -L2, -PIN]],
    ['tail0', 'pelvis', [-0.105, 0.06, 0]], ['tail1', 'tail0', [-0.052, 0, 0]], ['tail2', 'tail1', [-0.048, 0, 0]],
    ['tail3', 'tail2', [-0.044, 0, 0]], ['tail4', 'tail3', [-0.04, 0, 0]],
  ];
  // View-specific anchors for the head swivel: where the head's pivot sits on the neck dowel in each view class.
  // profile: pivot behind the ear pin so the skull hangs forward of the neck; rear: pivot raised and centred so, seen from behind,
  // the back of the skull sits square over the neck with both ears clear; three-quarter between. Blended continuously by the
  // head's angle to the camera (weights below), so a view change never pops.
  const HEAD_ANCHORS = { profile: [0.118, 0.026, 0], threeq: [0.108, 0.036, 0], rear: [0.094, 0.05, 0] };
  function anchorWeights(cosToCam) { // cosToCam: cos(angle between head forward and head->camera); -1 = we see the back
    const a = Math.abs(cosToCam);
    const wRear = cosToCam < 0 ? ease((a - 0.45) / 0.4) : 0;
    const wProf = 1 - ease(a / 0.6);
    const wQ = Math.max(0, 1 - wRear - wProf);
    const s = wRear + wProf + wQ; return { profile: wProf / s, threeq: wQ / s, rear: wRear / s };
  }
  function blendAnchor(w) {
    const o = [0, 0, 0];
    for (const k of ['profile', 'threeq', 'rear']) for (let j = 0; j < 3; j++) o[j] += w[k] * HEAD_ANCHORS[k][j];
    return o;
  }

  // Person: a carved figure. Local axes: +x forward (the way the face looks), +y up, +z the figure's right.
  const PERSON = [
    ['root', null, [0, 0, 0]],
    ['pelvis', 'root', [0, 0, 0]],
    ['spine', 'pelvis', [0, 0.12, 0]],
    ['chest', 'spine', [0, 0.2, 0]],
    ['neck', 'chest', [0, 0.2, 0]],
    ['head', 'neck', [0.0, 0.07, 0]],
    ['jaw', 'head', [0.035, 0.035, 0]],
    ['hemR', 'spine', [0.07, -0.02, 0.085]], ['hemL', 'spine', [0.07, -0.02, -0.085]],   // cardigan front panels
    ['shoulderR', 'chest', [0, 0.16, 0.19]], ['elbowR', 'shoulderR', [0, -0.29, 0]], ['wristR', 'elbowR', [0, -0.25, 0]],
    ['cuffR', 'elbowR', [0, -0.2, 0]], ['thumbR', 'wristR', [0.03, -0.03, -0.02]],
    ['shoulderL', 'chest', [0, 0.16, -0.19]], ['elbowL', 'shoulderL', [0, -0.29, 0]], ['wristL', 'elbowL', [0, -0.25, 0]],
    ['cuffL', 'elbowL', [0, -0.2, 0]], ['thumbL', 'wristL', [0.03, -0.03, 0.02]],
    ['hipR', 'pelvis', [0, -0.04, 0.1]], ['kneeR', 'hipR', [0, -0.42, 0]], ['ankleR', 'kneeR', [0, -0.42, 0]],
    ['hipL', 'pelvis', [0, -0.04, -0.1]], ['kneeL', 'hipL', [0, -0.42, 0]], ['ankleL', 'kneeL', [0, -0.42, 0]],
  ];
  const P_HIP_H = 0.92; // standing pelvis height (ankle 0.08 above the floor)

  // ---------- forward kinematics ----------
  // angles[j] = [yaw, pitch, roll] applied as R = RY(yaw) RZ(pitch) RX(roll); root gets a full world matrix.
  function fk(graph, rootWorld, angles, anchorOffset) {
    const W = {};
    for (const [name, parent, off0] of graph) {
      const off = off0 === 'ANCHOR' ? anchorOffset : off0;
      const a = angles[name] || [0, 0, 0];
      const R = M.mul(M.RY(a[0]), M.mul(M.RZ(a[1]), M.RX(a[2])));
      const local = M.mul(M.T(off[0], off[1], off[2]), R);
      W[name] = parent ? M.mul(W[parent], local) : M.mul(rootWorld, R);
    }
    return W;
  }

  // ---------- GAIT: the animator's stride keys ----------
  // A walk cycle of STRIDE metres. Each leg's local phase p in [0,1): stance [0, DUTY), swing [DUTY, 1).
  // The animator laid out 8 key poses per cycle for two body heights (upright H_UP, crouched H_LOW): five through stance,
  // three through swing. The key angles were worked out once, on paper style, with the law of cosines for where the paw should
  // be at that key (below: keyAngles). At render time the hip and knee angles are only *interpolated* between these keys
  // (periodic Catmull-Rom over phase) and blended by crouch; nothing is solved per frame, so the paw drifts a little between
  // keys. That drift is the measured foot slip (fktest.js).
  const STRIDE = 0.40, DUTY = 0.6, LIFT = 0.05, H_UP = 0.28, H_LOW = 0.225;
  const KEY_P = [0, 0.15, 0.3, 0.45, 0.6 - 1e-3, 0.7, 0.8, 0.9];
  function pawTarget(p, H) { // where the animator wants the ankle pin, relative to the hip pin, at key phase p
    const a = DUTY * STRIDE / 2;
    let u, v = -(H - PAW_H);
    if (p < DUTY) u = a - 2 * a * (p / DUTY);
    else { const s = (p - DUTY) / (1 - DUTY); u = -a + 2 * a * (s * s * (3 - 2 * s)); v += LIFT * Math.sin(Math.PI * s); }
    return [u, v];
  }
  function keyAngles(u, v, bendSign) { // two-link layout of a key pose (done once per key, at build time)
    const d = Math.min(Math.hypot(u, v), L1 + L2 - 1e-4);
    const cosK = (L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2);
    const knee = (Math.PI - Math.acos(clamp(cosK, -1, 1))) * bendSign;
    const base = Math.atan2(u, -v);
    const cosA = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d);
    const hip = base - bendSign * Math.acos(clamp(cosA, -1, 1));
    return [hip, knee];
  }
  // front legs: elbow behind the line (bendSign +1: the knee angle swings the forearm forward); hind: stifle forward (-1)
  const KEYS = {};
  for (const [leg, bend] of [['front', 1], ['hind', -1]]) {
    KEYS[leg] = {};
    for (const [hk, H] of [['up', H_UP], ['low', H_LOW]]) KEYS[leg][hk] = KEY_P.map(p => { const [u, v] = pawTarget(p, H); return keyAngles(u, v, bend); });
  }
  function catmull(p0, p1, p2, p3, t) {
    const t2 = t * t, t3 = t2 * t;
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
  }
  function keyInterp(keys, p) { // periodic Catmull-Rom over the non-uniform key phases
    p = ((p % 1) + 1) % 1;
    const n = KEY_P.length;
    let k = n - 1; for (let i = 0; i < n; i++) if (KEY_P[i] <= p) k = i;
    const p1 = KEY_P[k], p2 = k + 1 < n ? KEY_P[k + 1] : 1;
    const t = (p - p1) / (p2 - p1);
    const g = i => keys[((i % n) + n) % n];
    return [0, 1].map(c => catmull(g(k - 1)[c], g(k)[c], g(k + 1)[c], g(k + 2)[c], t));
  }
  const LEG_PHASE = { hipL: 0, shoulderL: 0.25, hipR: 0.5, shoulderR: 0.75 };

  // ---------- the score -> the dog's local angles ----------
  // World axes: X along the house wall (+ to the right seen from the porch), Y up, Z out of the house across the porch.
  // The threshold (score x = 0) is the outer face of the wall, Z = 0. The dog walks the line X = 0. Mapping: Z_root = x - X_OFF,
  // with the root at the hind pin; so at the score's sill (x = 0.59) the chest and head are inside the door frame.
  const X_OFF = 0.12;
  const SC = 1.4;                                      // the toy is built in its own units; it stands on the porch at 1.25x
  const HEAD_DOOR = Math.PI / 2;                       // yaw of the dog facing the door (heading -Z)
  const HEAD_AWAY = HEAD_DOOR + 155 * D2R;             // turned back: heading +Z swung 25 deg toward -X (rump to the door)

  function dogTimeline(score) { // per-frame integrated quantities (gait phase from distance travelled)
    const F = score.frames, out = [];
    let ph = 0, turnPh = 0, prevYaw = null;
    for (let i = 0; i < F.length; i++) {
      const x = F[i].dog.x, x0 = i ? F[i - 1].dog.x : x;
      ph += -(x - x0) / (STRIDE * SC);             // approaching (x falls) walks forward; retreating walks backward
      out.push({ ph });
    }
    return out;
  }

  function yawAt(t) { // the body's heading, authored: turn away 3.45-4.05 (head leads), turn back 7.95-8.75
    const away = ramp(t, 3.47, 4.05) - ramp(t, 7.95, 8.75);
    return { yaw: lerp(HEAD_DOOR, HEAD_AWAY, away), away };
  }

  function dogPose(score, tl, i, cam) {
    const f = score.frames[i], a = f.dog.act, t = f.t;
    const ang = {};
    const { yaw, away } = yawAt(t);
    const dyaw = (yawAt(t + 1 / 24).yaw - yawAt(t - 1 / 24).yaw) * 12; // rad/s
    // body height: lie and crouch
    let lie = a.lie;
    if (t > 7.4 && t < 8.3) lie = 1 - ramp(t, 7.62, 8.05);  // rises after the head has come round
    const crouch = clamp(a.crouch, 0, 1);
    const H = lerp(H_UP, H_LOW, crouch);
    const lieE = ease(lie);
    const rootY = lerp(H + 0.025, 0.098, lieE);  // the hip pins ride at H; the root sits 25 mm above them
    const Zr = f.dog.x - X_OFF;
    // the body turns about its middle (halfway between the hip and shoulder pins), so turning in place sweeps the paws least;
    // facing the door the hind pin sits at Zr exactly
    const MID = 0.175, Zmid = Zr - MID * SC;
    const rootWorld = M.mul(M.mul(M.mul(M.T(0, rootY * SC, Zmid), M.RY(yaw)), M.S(SC, SC, SC)), M.T(-MID, 0, 0));
    ang.root = [0, 0, 0];
    ang.pelvis = [0, 0, 0];
    ang.waist = [clamp(dyaw * 0.10, -0.3, 0.3), 0, 0];
    // turning in place: the walk cycle does not advance (the root does not travel); instead the animator steps each paw up
    // in turn through the swing of the heading (a lift wave keyed to the heading). Planted paws are dragged by the rotation:
    // that slip is measured and reported separately as turn slip.
    const turnU = (yaw - HEAD_DOOR) / (HEAD_AWAY - HEAD_DOOR);       // 0 facing the door .. 1 turned away
    const turning = (Math.abs(dyaw) > 0.01 || (t > 3.44 && t < 4.12) || (t > 7.93 && t < 8.8)) && lieE < 0.5;
    const mv = clamp(a.moving, 0, 1);
    const legs = {};
    const TURN_OFF = { shoulderR: 0, hipL: 0.25, shoulderL: 0.5, hipR: 0.75 };
    for (const [hipName, kneeName, pawName, kind] of [['shoulderR', 'elbowR', 'fpawR', 'front'], ['shoulderL', 'elbowL', 'fpawL', 'front'], ['hipR', 'kneeR', 'hpawR', 'hind'], ['hipL', 'kneeL', 'hpawL', 'hind']]) {
      const pp = (((tl[i].ph + LEG_PHASE[hipName]) % 1) + 1) % 1;
      const up = keyInterp(KEYS[kind].up, pp), lo = keyInterp(KEYS[kind].low, pp);
      let hip = lerp(up[0], lo[0], crouch), knee = lerp(up[1], lo[1], crouch);
      if (pp >= DUTY && mv < 1) { // standing still mid-swing: the raised paw is set down at its touchdown key
        const tu = KEYS[kind].up[0], tlw = KEYS[kind].low[0];
        const th = lerp(tu[0], tlw[0], crouch), tk = lerp(tu[1], tlw[1], crouch);
        hip = lerp(hip, th, 1 - mv); knee = lerp(knee, tk, 1 - mv);
      }
      let paw = -(hip + knee);                     // the paw block is counter-rotated to stay flat (an authored choice)
      if (pp >= DUTY) paw += 0.45 * Math.sin(Math.PI * (pp - DUTY) / (1 - DUTY)) * mv; // toe flick in swing
      // turn steps: a lift wave, each paw up for a quarter of the turn
      let tlift = 0;
      if (turning && Math.abs(dyaw) > 0.05) { const q = (turnU * 3 + TURN_OFF[hipName]) % 1; tlift = q < 0.55 ? Math.sin(Math.PI * q / 0.55) : 0; }
      const bend = kind === 'front' ? 1 : -1;
      knee += bend * 0.55 * tlift; hip -= bend * 0.22 * tlift; paw -= bend * 0.33 * tlift;
      // lying fold (authored key pose), blended in by lie
      const fold = kind === 'front' ? [80 * D2R, 12 * D2R, -92 * D2R] : [102 * D2R, -170 * D2R, 70 * D2R];
      hip = lerp(hip, fold[0], lieE); knee = lerp(knee, fold[1], lieE); paw = lerp(paw, fold[2], lieE);
      ang[hipName] = [0, hip, 0]; ang[kneeName] = [0, knee, 0]; ang[pawName] = [0, paw, 0];
      const swinging = (pp >= DUTY && mv > 0.05) || tlift > 0.02;
      legs[hipName] = { p: pp, paw: pawName, planted: !swinging && lieE < 0.02, turning, tlift };
    }
    // head and neck: head 0 down .. 1 up; the head leads the body in both turns
    let head = clamp(a.head, 0, 1);
    let neckPitch = lerp(-80, 26, Math.pow(head, 1.5)) * D2R;
    let headPitch = -0.3 * neckPitch - 8 * D2R;
    let neckYaw = 0, headYaw = 0, headRoll = 0;
    // coming, head low: while approaching, the neck is carried well below the line of the back
    const lowCarry = f.dog.state === 'approach' ? clamp(a.moving * 1.2, 0, 1) * (1 - lieE) : 0;
    neckPitch = lerp(neckPitch, -58 * D2R, lowCarry); headPitch = lerp(headPitch, 8 * D2R, lowCarry);
    // refusal: the head swings away first (3.42), the body follows
    const leadAway = ramp(t, 3.42, 3.66) - ramp(t, 3.85, 4.1);
    neckYaw += 0.55 * leadAway; headYaw += 0.35 * leadAway;
    // turning back to look (7.46): head comes round over the shoulder, muzzle level, while the body still lies
    const lookBack = ramp(t, 7.44, 7.72) * (1 - ramp(t, 8.0, 8.7));
    if (lookBack > 0) {
      neckYaw = lerp(neckYaw, -88 * D2R, lookBack); headYaw = lerp(headYaw, -58 * D2R, lookBack);
      neckPitch = lerp(neckPitch, 4 * D2R, lookBack); headPitch = lerp(headPitch, -4 * D2R, lookBack); headRoll = lerp(0, -0.12, lookBack);
    }
    // lying: rest = chin on the paws
    if (lieE > 0) {
      const rest = clamp(a.rest, 0, 1);
      const lyingNeck = lerp(lerp(-8, 14, clamp(head, 0, 1)) * D2R, -40 * D2R, rest);
      const lyingHead = lerp(-6 * D2R, 18 * D2R, rest);
      const w = lieE * (1 - lookBack);
      neckPitch = lerp(neckPitch, lyingNeck, w); headPitch = lerp(headPitch, lyingHead, w);
    }
    // looking in (26.4): the head pushes level into the doorway and turns into the room, away from the camera
    const look = clamp(a.look, 0, 1);
    if (look > 0) {
      neckPitch = lerp(neckPitch, 2 * D2R, look); headPitch = lerp(headPitch, -3 * D2R, look);
      neckYaw = lerp(neckYaw, 16 * D2R, look); headYaw = lerp(headYaw, 22 * D2R, look);
    }
    ang.neck = [neckYaw, neckPitch, 0];
    ang.head = [headYaw, headPitch, headRoll];
    // ears: 0 flat back .. 1 pricked; the outer leaf droops
    const ear = clamp(a.ear, -0.1, 1.05);
    // drop ears hinged at the top of the skull: alert lifts the leaf out and forward, flat presses it back along the neck
    const eRoll = lerp(0.12, 1.25, ear), ePitch = lerp(0.95, -0.25, ear);
    ang.earR0 = [0, ePitch, eRoll]; ang.earL0 = [0, ePitch, -eRoll];
    const eTip = lerp(0.1, -0.55, ear);
    ang.earR1 = [0, 0, eTip]; ang.earL1 = [0, 0, -eTip];
    // tail: 0 high .. 1.35 tucked; wag is an authored yaw wave travelling down the chain (each bead lags its parent)
    const tail = clamp(a.tail, 0, 1.4);
    const base = lerp(-48, 72, tail / 1.35) * D2R;
    const wagA = clamp(a.wag, 0, 1) * 0.42;
    for (let k = 0; k < 5; k++) {
      const wag = wagA * Math.sin(2 * Math.PI * 2.1 * t - k * 0.7) * (k === 0 ? 0.7 : 0.45);
      const curl = k === 0 ? base : lerp(10, 16, tail / 1.35) * D2R * (tail > 0.8 ? 1.2 : -0.4);
      ang['tail' + k] = [wag, curl, 0];
    }
    if (lieE > 0) ang.tail0[1] = lerp(ang.tail0[1], 60 * D2R, lieE * 0.85); // lying: the tail lies along the floor
    // saddle cloth: flaps hang toward gravity: the animator counter-rotates them against the body roll, with a lagged sway
    const sway = 0.12 * Math.sin(2 * Math.PI * tl[i].ph + 0.9) * clamp(a.moving, 0, 1) + clamp(-dyaw * 0.06, -0.25, 0.25);
    ang.cloth = [0, 0, 0];
    ang.flapR0 = [0, 0, -sway]; ang.flapR1 = [0, 0, 0.1 - sway * 0.6];
    ang.flapL0 = [0, 0, -sway]; ang.flapL1 = [0, 0, -0.1 - sway * 0.6];
    if (lieE > 0) { ang.flapR0[2] -= 0.55 * lieE; ang.flapL0[2] += 0.55 * lieE; ang.flapR1[2] -= 0.5 * lieE; ang.flapL1[2] += 0.5 * lieE; }

    // view-specific head anchor: classify the head's view from the camera with a provisional FK pass
    let anchor = HEAD_ANCHORS.threeq, weights = { profile: 0, threeq: 1, rear: 0 };
    if (cam) {
      const W0 = fk(DOG, rootWorld, ang, HEAD_ANCHORS.threeq);
      const hp = M.p(W0.head, [0, 0, 0]), hf = M.d(W0.head, [1, 0, 0]);
      const tc = [cam.pos[0] - hp[0], cam.pos[1] - hp[1], cam.pos[2] - hp[2]], n = Math.hypot(...tc);
      const c = (hf[0] * tc[0] + hf[1] * tc[1] + hf[2] * tc[2]) / n;
      weights = anchorWeights(c); anchor = blendAnchor(weights);
    }
    const W = fk(DOG, rootWorld, ang, anchor);
    return { W, ang, rootWorld, anchor, weights, legs, yaw, away, lie: lieE, rootY, Zr, Zmid };
  }

  // ---------- the person ----------
  const DOOR_POS = [0, 0, -0.16];                  // standing on the threshold
  const SEAT = [-1.15, 0, 0.42];                   // sitting against the wall, left of the door
  const SEAT_YAW = 68 * D2R;                        // facing out across the porch, turned toward the dog's line
  function personPose(score, i) {
    const f = score.frames[i], P = f.person, t = f.t;
    const ang = {};
    // where: doorway until 4.6, steps out and left (4.65-5.45), sits (5.4-6.6)
    const w = ramp(t, 4.65, 5.45);
    const pathX = lerp(DOOR_POS[0], SEAT[0], w), pathZ = lerp(DOOR_POS[2], SEAT[2], ease(w) * 0.6 + w * 0.4) + 0.25 * Math.sin(Math.PI * w);
    const heading = lerp(-Math.PI / 2, -Math.PI / 2 + SEAT_YAW, ease(ramp(t, 4.6, 5.6)));
    // turning toward the seat while walking (face where it goes), then back to face the porch
    const walkTurn = -1.05 * Math.sin(Math.PI * w);
    const yaw = heading + walkTurn;
    const sit = clamp(P.sit, 0, 1), sitE = ease(sit);
    const pelvisY = lerp(P_HIP_H, 0.13, sitE);
    const rootWorld = M.mul(M.T(pathX, pelvisY, pathZ), M.RY(yaw));
    const reach = clamp(P.reach, 0, 1), low = clamp(P.low, 0, 1), mouth = clamp(P.mouth, 0, 1);
    const call = P.voice === 'call' ? 1 : 0;
    ang.pelvis = [0, 0, 0];
    // lean: reach leans forward; sitting leans back on the wall a little
    const lean = 0.42 * ease(reach) - 0.10 * sitE + 0.22 * low * sitE;
    ang.spine = [0, -lean * 0.5, 0]; ang.chest = [0, -lean * 0.5, 0];
    ang.neck = [0, 0.12 * reach - 0.06 * low * sitE, 0];
    ang.head = [0.18 * low * sitE, 0.05 * call - 0.12 * low * sitE, 0.06 * low * sitE];
    ang.jaw = [0, -0.42 * mouth, 0];
    // legs: walking steps (authored) then the sit (hips flex, knees fold up)
    const stepPh = w * 3 * Math.PI;
    const walking = Math.sin(Math.PI * w) > 0.05 && w < 1 ? Math.sin(Math.PI * w) : 0;
    const legSwing = 0.38 * Math.sin(stepPh) * walking;
    const hipSit = 2.3, kneeSit = -1.5;
    ang.hipR = [-0.55 * sitE, lerp(legSwing, 1.52, sitE), lerp(0, -0.12, sitE)];      // the near leg lies out straight
    ang.hipL = [0, lerp(-legSwing, hipSit - 0.2, sitE), lerp(0, 0.22, sitE)];
    ang.kneeR = [0, lerp(-Math.max(0, Math.sin(stepPh)) * 0.6 * walking, -0.12, sitE), 0];
    ang.kneeL = [0, lerp(-Math.max(0, -Math.sin(stepPh)) * 0.6 * walking, kneeSit + 0.25, sitE), 0];
    ang.ankleR = [0, -(ang.hipR[1] + ang.kneeR[1]) * (1 - sitE) - sitE * 0.2, 0];
    ang.ankleL = [0, -(ang.hipL[1] + ang.kneeL[1]) * (1 - sitE) + sitE * 0.4, 0];
    // arms. Right arm (toward the dog): calls with a beckon, reaches (3.4-4.6), then offers the hand low (6.8 ->)
    const beckon = call * (1 - reach) * (0.5 + 0.5 * Math.sin(2 * Math.PI * 1.6 * t));
    let shR = [0.0, 0.25 * call * (1 - reach) + 1.35 * reach, -0.12];
    let elR = [0, 0.9 * beckon * (1 - reach) + 0.12 * reach, 0];
    let wrR = [0, 0.3 * beckon - 0.2 * reach, 0];
    // seated: the low hand: arm forward and down, forearm near the floor, palm up
    const lowA = low * sitE;
    const restR = [0.0, 0.5, 0.12], restEl = [0, 0.7, 0];
    shR = shR.map((v, k) => lerp(v, restR[k], sitE * (1 - lowA)));
    elR = elR.map((v, k) => lerp(v, restEl[k], sitE * (1 - lowA)));
    const lowSh = [0.1, 0.62, -0.18], lowEl = [0, 0.22, 0], lowWr = [0, 0.15, -1.5];
    shR = shR.map((v, k) => lerp(v, lowSh[k], lowA)); elR = elR.map((v, k) => lerp(v, lowEl[k], lowA));
    wrR = wrR.map((v, k) => lerp(v, lowWr[k], lowA));
    ang.shoulderR = shR; ang.elbowR = elR; ang.wristR = wrR;
    // left arm: at the side; seated, it rests on the raised knee
    const armSwingL = -legSwing * 0.6;
    ang.shoulderL = [0, lerp(armSwingL, 0.55, sitE), lerp(0.06, -0.15, sitE)];
    ang.elbowL = [0, lerp(0.15, 0.75, sitE), 0];
    ang.wristL = [0, lerp(0, -0.2, sitE), 0];
    // sleeve cuffs: the cardigan cuff hangs; the animator counter-rotates it partly against its forearm, so it droops
    for (const s of ['R', 'L']) {
      const sh = ang['shoulder' + s], el = ang['elbow' + s];
      const armPitch = sh[1] + el[1];
      ang['cuff' + s] = [0, -0.35 * Math.sin(armPitch), 0];
      ang['thumb' + s] = [0, 0, 0];
    }
    // cardigan front panels hang open; sitting folds them over the lap
    const hemDrop = -(ang.spine[1]) * 0.8 + sitE * 1.0;
    ang.hemR = [0, -lean * 0.4 + hemDrop * 0.3, -0.05]; ang.hemL = [0, -lean * 0.4 + hemDrop * 0.3, 0.05];
    const W = fk(PERSON, rootWorld, ang, null);
    return { W, ang, rootWorld, sit: sitE, reach, low: lowA, mouth };
  }

  function doorAngle(t) { // hinge on the left jamb, opening inward; ajar 22 deg, swings to 104 deg at 6.2
    return lerp(22, 104, ease((t - 6.2) / 0.9)) * D2R + 0.02 * Math.sin(Math.PI * clamp((t - 7.1) / 0.6, 0, 1));
  }

  // ---------- camera ----------
  // A: wide, low, three-quarter from the porch (0-14.6). Then a slow dolly that keeps the dog in a near-profile three-quarter
  // through the approach and settles behind its right shoulder at the sill (from 23.6), where the doorway is seen in depth.
  function camera(t, score) {
    const A = { pos: [4.1, 0.58, 5.3], tgt: [-0.35, 0.6, 2.25], fov: 34 };
    const B = { pos: [1.22, 0.98, 2.15], tgt: [-0.12, 0.2, -0.05], fov: 38 };
    if (t < 14.6) return A;
    // tracking: keep a low near-profile on the walking dog (so head-below-back reads), then swing behind its shoulder at the sill
    const dz = score ? dogZAt(score, t) : 2.0;
    const T = { pos: [2.45, 0.5, dz + 0.75], tgt: [-0.1, 0.34, dz - 0.55], fov: 36 };
    const u1 = ease((t - 14.6) / 2.6), u2 = ease((t - 21.6) / 2.6);
    const mix = (P, Q, u) => ({ pos: P.pos.map((v, k) => lerp(v, Q.pos[k], u)), tgt: P.tgt.map((v, k) => lerp(v, Q.tgt[k], u)), fov: lerp(P.fov, Q.fov, u) });
    return mix(mix(A, T, u1), B, u2);
  }
  let _dz = null;
  function dogZAt(score, t) { // smoothed root Z (a camera operator follows smoothly)
    if (!_dz || _dz.score !== score) {
      const F = score.frames, raw = F.map(f => f.dog.x - X_OFF), sm = raw.map((_, i) => { let s = 0, n = 0; for (let k = -18; k <= 18; k++) { const j = Math.max(0, Math.min(F.length - 1, i + k)); s += raw[j]; n++; } return s / n; });
      _dz = { score, sm };
    }
    const i = Math.max(0, Math.min(_dz.sm.length - 1, Math.round(t * 24))); return _dz.sm[i];
  }

  const api = { SC, M, D2R, DOG, PERSON, HEAD_ANCHORS, anchorWeights, fk, dogPose, dogTimeline, personPose, doorAngle, camera, KEYS, KEY_P, STRIDE, DUTY, LIFT, H_UP, H_LOW, L1, L2, PAW_H, X_OFF, LEG_PHASE, ease, lerp, clamp, ramp, dist3, keyInterp };
  if (typeof module !== 'undefined') module.exports = api; else G.RIG = api;
})(typeof window !== 'undefined' ? window : globalThis);
