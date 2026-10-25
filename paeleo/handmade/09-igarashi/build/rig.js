// SCION 09 · Igarashi — the rig handle designer's artifact.
// Turns one frame of the PAELEO score into handle targets on the source drawings, then solves each piece by ARAP.
// The world: the porch runs left→right along the house front; screen x = X0 + x·S (x in metres from the threshold),
// every figure stands on the line y = YG. Drawings are authored at 364 px/m and shown at S px/m (scale K).
// A dog frame is 1–2 pieces: a body drawing (stand / rear / sit_back / lie) and a head drawing (side / back) attached at
// the body's neck socket. Swapping drawings is the explicit "draw swap" of the method; everything between swaps is ARAP.
(function (root) {
  const X0 = 320, S = 190, YG = 590, DPM = 364, K = S / DPM, DOGX = 1.15, KD = K * DOGX, DPMD = DPM / DOGX;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, u) => a + (b - a) * u;
  const ss = u => { u = clamp(u); return u * u * (3 - 2 * u); };
  const win = (t, a, b) => ss((t - a) / (b - a));
  const frac = v => v - Math.floor(v);
  const add = (p, q) => [p[0] + q[0], p[1] + q[1]];
  const rot = (v, a) => [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a)];

  // where each body drawing is anchored on the porch (drawing x of the body centre, drawing y of the ground)
  const ANCHOR = { dog_stand: [254, 321], dog_rear: [216, 322], dog_sit_back: [262, 320], dog_lie: [262, 273], 'person_stand.body': [128, 622], 'person_sit.body': [100, 458] };

  // two-bone IK: top T, foot F, rest lengths from rest points, keep the rest bend side
  function ik(T, F, T0, M0, F0, dir) {
    const a = Math.hypot(M0[0] - T0[0], M0[1] - T0[1]), b = Math.hypot(F0[0] - M0[0], F0[1] - M0[1]);
    const side = Math.sign((F0[0] - T0[0]) * (M0[1] - T0[1]) - (F0[1] - T0[1]) * (M0[0] - T0[0])) || 1;
    let dx = F[0] - T[0], dy = F[1] - T[1], d = Math.hypot(dx, dy);
    const dm = Math.min(Math.max(d, Math.abs(a - b) + 1e-3), a + b - 1e-3);
    const ux = dx / (d || 1), uy = dy / (d || 1);
    const x = (a * a - b * b + dm * dm) / (2 * dm), h = Math.sqrt(Math.max(0, a * a - x * x));
    // perpendicular with the rest side: cross(u, perp)*side > 0
    let px = -uy, py = ux; if (Math.sign(ux * py - uy * px) !== side) { px = -px; py = -py; }
    if (dir) { if (Math.sign(px) !== dir) { px = -px; py = -py; } } // explicit bend direction (knee forward / hock back)
    return [T[0] + ux * x + px * h, T[1] + uy * x + py * h];
  }

  function Rig(SCORE, MESH) {
    const F = SCORE.frames, N = F.length, FPS = 24;
    const HP = name => MESH[name].handle_points;

    // ── the dog's own timeline: which drawings, when (the choices are the score's; the swaps are ours) ──
    const T_RETREAT = 1.0, T_WATCH1 = 2.333, T_REFUSE = 3.417, T_WATCH2 = 7.458, T_APPROACH = 14.708, T_LIE = 23.792, T_COMEIN = 26.4;
    function segment(t) {
      if (t < T_REFUSE) return { body: 'dog_stand', head: 'head_side' };
      if (t < T_REFUSE + 0.085) return { body: 'dog_stand', head: 'head_side', flinch: true };
      if (t < T_REFUSE + 0.21) return { body: 'dog_stand', head: 'head_back', turning: true };
      if (t < 4.75) return { body: 'dog_rear', head: 'head_back' };
      if (t < T_WATCH2) return { body: 'dog_sit_back', head: 'head_back' };
      if (t < 7.75) return { body: 'dog_sit_back', head: 'head_side', lookback: true };
      if (t < 8.04) return { body: 'dog_rear', head: 'head_side', lookback: true };
      if (t < 8.21) return { body: 'dog_rear', head: 'head_side', swing: true, lookback: true };
      if (t < T_LIE + 0.33) return { body: 'dog_stand', head: 'head_side' };
      if (t >= T_COMEIN + 0.05 && t < 28.1) return { body: 'dog_lie', head: 'head_back', headMirror: true, lookin: true };
      return { body: 'dog_lie', head: 'head_side' };
    }

    // cumulative forward distance (drawing px) walked by the standing drawing → gait phase (feet planted by construction)
    const walkS = new Float64Array(N), moving = new Float64Array(N);
    for (let i = 1; i < N; i++) {
      const dx = F[i].dog.x - F[i - 1].dog.x; // metres, +x is away from the door
      walkS[i] = walkS[i - 1] + (-dx) * DPMD;   // the stand drawing faces the door (-x): forward = -dx
      moving[i] = Math.min(1, Math.abs(dx) * FPS / 0.25);
    }
    const sm = new Float64Array(N); for (let i = 0; i < N; i++) { let s = 0, w = 0; for (let j = -4; j <= 4; j++) { const k = Math.min(N - 1, Math.max(0, i + j)); s += moving[k]; w++; } sm[i] = s / w; }

    function gait(i, stride, duty, lift) {
      const phase = walkS[i] / stride, off = { h2: 0, f1: 0.25, h1: 0.5, f2: 0.75 }, o = {};
      for (const [k, of] of Object.entries(off)) {
        const p = frac(phase + of);
        let fwd, up = 0;
        if (p < duty) fwd = stride * (duty / 2 - p);
        else { const u = (p - duty) / (1 - duty); fwd = stride * (-duty / 2 + u * duty); up = Math.sin(Math.PI * u) * lift * sm[i]; }
        o[k] = [-fwd, -up]; // drawing faces -x
      }
      return o;
    }

    // ── feet: a stepping simulation over the frames that show the standing drawing. A foot is either planted (fixed on
    // the boards) or in the air on a step; it never slides. A foot steps when the body has carried it too far from its
    // rest place (walking) or, once the body is still, to settle back under it. Front and hind pairs alternate.
    const FEET = ['h2', 'f1', 'h1', 'f2'], PAIR = { f1: 'F', f2: 'F', h1: 'H', h2: 'H' };
    const feetOff = new Array(N).fill(null);
    {
      const hp = HP('dog_stand'), ax = ANCHOR.dog_stand[0];
      let st = null;
      for (let i = 0; i < N; i++) {
        const t = F[i].t;
        if (segment(t).body !== 'dog_stand') { st = null; continue; }
        const bx = F[i].dog.x * DPMD, v = i > 0 ? (F[i].dog.x - F[i - 1].dog.x) * DPMD * FPS : 0;
        const shift = footShiftAt(t);
        const rest = k => bx + (hp[k][0] - ax) + (shift[k] ? shift[k][0] : 0);
        if (!st) { st = {}; for (const k of FEET) st[k] = { pos: rest(k), step: null, last: -9 }; }
        const fast = Math.abs(v) > 0.45 * DPMD, dur = fast ? 0.2 : 0.28, lead = 0.8;
        for (const k of FEET) { // advance steps in the air
          const f = st[k]; if (!f.step) continue;
          const u = (t - f.step.t0) / f.step.dur;
          const to = rest(k) + v * f.step.dur * lead;
          if (u >= 1) { f.pos = to; f.step = null; f.last = t; } else { f.pos = lerp(f.step.from, to, ss(u)); f.step.u = u; }
        }
        const still = Math.abs(v) < 0.02 * DPMD;
        const thr = still ? 5 : 0.06 * DPMD;
        const busy = FEET.filter(k => st[k].step);
        const cand = FEET.filter(k => !st[k].step && !busy.some(b => PAIR[b] === PAIR[k]) && t - st[k].last > 0.06)
          .map(k => [k, Math.abs(rest(k) - st[k].pos)]).filter(c => c[1] > thr).sort((a, b) => b[1] - a[1]);
        if (busy.length < (fast ? 2 : 1) && cand.length) { const k = cand[0][0]; st[k].step = { t0: t, dur: still ? 0.22 : dur, from: st[k].pos, u: 0 }; }
        const o = {};
        for (const k of FEET) { const f = st[k]; const lift = f.step ? Math.sin(Math.PI * clamp(f.step.u || 0)) * (fast ? 16 : 12) : 0; o[k] = [f.pos - (bx + (hp[k][0] - ax)), -lift]; }
        feetOff[i] = o;
      }
    }
    function footShiftAt(t) {
      if (t < T_LIE) return {};
      const u = win(t, T_LIE, T_LIE + 0.3);
      return { f1: [-50 * u, 0], f2: [-44 * u, 0], h1: [-22 * u, 0], h2: [-16 * u, 0] };
    }

    function standHandles(i, P) {
      const hp = HP('dog_stand'), t = F[i].t;
      const c = P.crouch, dyw = c * (c > 1 ? 20 : 13) + P.bob, dyh = c * (c > 1 ? 30 : 24) + P.bob * 0.6, lean = P.lean || 0;
      const trunk = p => { const u = clamp((p[0] - 178) / (330 - 178)); return [p[0] + lean, p[1] + lerp(dyw, dyh, u)]; };
      const H = {};
      for (const k of ['withers', 'back', 'hip', 'belly']) H[k] = trunk(hp[k]);
      H.back[1] += Math.sin(t * 2 * Math.PI * 0.45) * 1.2; // breath
      // neck socket: lowered with the head
      const hd = P.head;
      H.socket = add(trunk(hp.socket), [-(0.9 - hd) * 10, (0.9 - hd) * 34]);
      // tail
      const B = trunk([372, 138]), th = 0.98 + Math.min(0.62, (P.tail - 0.5) * 1.15) + (P.wag || 0) * 0.38 * Math.sin(t * 2 * Math.PI * 2.4), L = 133;
      H.tail_tip = add(B, [Math.cos(th) * L, Math.sin(th) * L]);
      H.tail_mid = add(B, [Math.cos(th - 0.28) * L * 0.55, Math.sin(th - 0.28) * L * 0.55]);
      // legs: feet from the gait (or given), knees by IK from the trunk-carried leg tops
      const g = feetOff[i] || {};
      const legs = { f1: [[128, 214], 'f1k', -1], f2: [[180, 214], 'f2k', -1], h1: [[276, 212], 'h1k', 1], h2: [[344, 214], 'h2k', 1] };
      for (const [k, [top0, kn, dir]] of Object.entries(legs)) {
        const foot = add(hp[k], g[k] || [0, 0]);
        H[k] = foot;
        H[kn] = ik(trunk(top0), foot, top0, hp[kn], hp[k], dir);
      }
      return H;
    }

    // dog acting parameters per frame: the score's acts, re-read by this swarm for legibility
    function dogParams(i) {
      const f = F[i], a = f.dog.act, t = f.t;
      const P = { crouch: a.crouch, head: a.head, ear: a.ear, tail: a.tail, wag: a.wag, bob: 0, lean: 0 };
      if (t >= T_APPROACH) {
        const u = win(t, T_APPROACH, T_APPROACH + 0.35);
        P.head = lerp(a.head, 0.2, u); P.ear = lerp(a.ear, 0.35, u); P.crouch = lerp(a.crouch, 0.22, u);
        P.tail = lerp(a.tail, 0.72, u); P.wag = Math.max(a.wag, 0.25 * u);
      }
      if (t >= T_RETREAT && t < T_WATCH1 + 0.4) P.head = Math.max(P.head, 0.58);
      if (t >= T_RETREAT && t < T_WATCH1 + 0.3) P.lean = 10 * win(t, T_RETREAT, T_RETREAT + 0.2) * (1 - win(t, T_WATCH1, T_WATCH1 + 0.3));
      // walking bob
      const fo = feetOff[i]; P.bob = fo ? 1.6 * Object.values(fo).reduce((s, o) => s + Math.min(1, -o[1] / 10), 0) : 0;
      return P;
    }

    function headHandles(name, P, t) {
      const hp = HP(name), H = {};
      for (const k of ['skull', 'muzzle', 'ear_base', 'neck']) if (hp[k]) H[k] = hp[k].slice();
      const flat = (1 - clamp(P.ear, -0.2, 1.1)) * (name === 'head_side' ? 1.0 : 0.7);
      const eb = hp.ear_base;
      if (name === 'head_side') H.ear_tip = add(eb, rot([hp.ear_tip[0] - eb[0], hp.ear_tip[1] - eb[1]], flat));
      else {
        H.ear_tip = add(eb, rot([hp.ear_tip[0] - eb[0], hp.ear_tip[1] - eb[1]], flat));
        const eb2 = [72, 70]; H.ear2_tip = add(eb2, rot([hp.ear2_tip[0] - eb2[0], hp.ear2_tip[1] - eb2[1]], -flat));
      }
      return H;
    }

    // squeeze every handle toward (or away from) a vertical line: the in-between bend that bridges a drawing swap
    function squeeze(H, cx, f) { for (const k of Object.keys(H)) H[k] = [cx + (H[k][0] - cx) * f, H[k][1]]; }

    // ── one dog frame: list of pieces with handle targets (drawing coords) and placement ──
    function dog(i) {
      const f = F[i], t = f.t, x = f.dog.x, sg = segment(t), P = dogParams(i);
      const ax = X0 + x * S;
      const pieces = [];
      let H, headPitch, headOff = [0, 0], headScale = 1, mirror = !!sg.mirror, state = f.dog.state, facing = 1, posture = 'stand';
      if (sg.body === 'dog_stand') {
        // the stand drawing also covers the flinch, the first instant of the turn, and the crouch into lying
        if (sg.flinch || sg.turning) { P.crouch = Math.max(P.crouch, 0.55); P.head = 0.3; P.ear = 0; P.tail = 1.2; }
        let feet = null;
        if (t >= T_LIE) { // crouch down onto the sill: legs fold, the forefeet reach forward
          const u = win(t, T_LIE, T_LIE + 0.33);
          P.crouch = lerp(P.crouch, 1.9, u); P.head = lerp(P.head, 0.45, u);
        }
        H = standHandles(i, P);
        // bridges: the profile foreshortens as it turns away (3.50–3.625) and unfolds after the back view (8.21–8.33)
        // (the paws lift while the body pivots: a shuffle, not a slide)
        const shuffle = (u) => { for (const k of ['f1', 'f2', 'h1', 'h2']) H[k][1] -= 7 * Math.sin(Math.PI * clamp(u)) * (k === 'f1' || k === 'h1' ? 1 : 0.6); };
        if (sg.turning) { const u = win(t, T_REFUSE + 0.083, T_REFUSE + 0.208); squeeze(H, 254, 1 - 0.34 * u); shuffle(u * 2 > 1 ? 2 - u * 2 : u * 2); }
        if (t >= 8.21 && t < 8.4) { const u = win(t, 8.21, 8.34); squeeze(H, 254, lerp(0.66, 1, u)); shuffle(u); }
        headPitch = -0.95 + 1.0 * P.head;
        headOff = [-(0.9 - P.head) * 14, (0.9 - P.head) * 30];
        if (sg.turning) { headPitch = 0; headOff = [26, 22]; headScale = 0.84; }
        posture = t >= T_LIE ? 'lying_down' : (P.crouch > 0.5 ? 'crouch' : 'stand');
        if (sg.turning) { facing = -1; posture = 'turning_away'; }
      } else if (sg.body === 'dog_rear') {
        const hp = HP('dog_rear'); H = {};
        for (const k of Object.keys(hp)) H[k] = hp[k].slice();
        let low = 0;
        if (!sg.lookback) low = 10 * win(t, 4.35, 4.75);          // starts to sit
        else low = 10 * (1 - win(t, 7.75, 7.95));                  // rising from the sit
        const settle = sg.lookback ? 0 : 8 * Math.exp(-(t - (T_REFUSE + 0.21)) * 9) * Math.cos((t - (T_REFUSE + 0.21)) * 26);
        H.hip[1] += low;
        H.back[1] += low * 0.5 + settle * 0.3; H.withers[1] += settle; H.socket[1] += settle + 6;
        H.tail_tip = add(hp.tail_tip, [0, low * 0.3]);
        // bridges: arriving from the profile still wide (3.625–3.71); the tail goes out onto the boards before the sit
        // (4.55–4.75) and comes in from the boards after rising (7.75–7.86)
        if (!sg.lookback) {
          if (t < T_REFUSE + 0.3) squeeze(H, 216, lerp(1.3, 1, win(t, T_REFUSE + 0.208, T_REFUSE + 0.3)));
          squeeze(H, 216, 1 + 0.16 * win(t, 4.55, 4.75));   // the haunches spread as it goes down
        } else {
          squeeze(H, 216, 1 + 0.16 * (1 - win(t, 7.75, 7.86)));
        }
        headPitch = 0; headOff = [12, 24]; headScale = 0.8;
        if (sg.lookback) { headPitch = 0.1; headOff = [-4, 16]; headScale = 0.86; }
        // the front end swings round: entering the back view it is still coming from the door side (left); leaving it,
        // it swings back toward the door before the profile drawing takes over
        let sw = 0;
        if (!sg.lookback) sw = 1 - win(t, T_REFUSE + 0.21, T_REFUSE + 0.42);
        else sw = win(t, 7.95, 8.21);
        H.socket = add(H.socket, [-44 * sw, 6 * sw]); H.withers = add(H.withers, [-30 * sw, 4 * sw]); H.back = add(H.back, [-14 * sw, 2 * sw]);
        if (sg.lookback) headOff = add(headOff, [-10 * sw, 0]);
        facing = sg.lookback ? 1 : -1; posture = sg.lookback ? 'rising_looking_back' : 'back_turned';
      } else if (sg.body === 'dog_sit_back') {
        const hp = HP('dog_sit_back'); H = {};
        for (const k of Object.keys(hp)) H[k] = hp[k].slice();
        const br = Math.sin(t * 2 * Math.PI * 0.32) * 2.2;
        H.back[1] += br * 0.5; H.withers[1] += br; H.socket[1] += br;
        // bridges: the haunches spread and the tail sweeps out after the swap (4.75–4.9), and gather in before rising (7.62–7.75)
        const gather = Math.max(1 - win(t, 4.75, 4.9), win(t, 7.62, 7.75));
        H.h1 = [lerp(H.h1[0], 206, gather), H.h1[1]]; H.h2 = [lerp(H.h2[0], 318, gather), H.h2[1]];
        H.withers[1] -= 10 * win(t, 7.62, 7.75); H.socket[1] -= 10 * win(t, 7.62, 7.75);
        const sink = 14 * (1 - win(t, 4.75, 5.05));                // arrives from the half-sit
        H.withers[1] -= sink; H.socket[1] -= sink; H.back[1] -= sink * 0.6;
        // head droops while refusing (rest), comes round at the choice
        const rest = sg.lookback ? 0 : F[i].dog.act.rest;
        headPitch = 0; headOff = [0, 6 + 16 * rest]; headScale = 0.92;
        if (sg.lookback) { const u = win(t, T_WATCH2, T_WATCH2 + 0.25); headPitch = lerp(-0.25, 0.08, u); headOff = [lerp(-2, -10, u), lerp(14, 4, u)]; headScale = 0.95; H.socket = add(H.socket, [-8 * u, -4 * u]); }
        facing = sg.lookback ? 1 : -1; posture = sg.lookback ? 'sitting_looking_back' : 'sitting_back_turned';
      } else { // dog_lie
        const hp = HP('dog_lie'); H = {};
        for (const k of Object.keys(hp)) H[k] = hp[k].slice();
        const t0 = T_LIE + 0.33, u = win(t, t0, t0 + 0.45);
        // arriving from the crouch: back and hips higher, forefeet not yet out
        H.withers[1] -= 30 * (1 - u); H.back[1] -= 36 * (1 - u); H.hip[1] -= 44 * (1 - u); H.socket[1] -= 28 * (1 - u); H.belly[1] -= 22 * (1 - u);
        H.f1[0] += 50 * (1 - u); H.f2[0] += 44 * (1 - u); H.f1[1] -= 10 * (1 - u); H.f2[1] -= 8 * (1 - u);
        const br = Math.sin(t * 2 * Math.PI * 0.3) * 1.8; H.back[1] += br; H.withers[1] += br * 0.6;
        const wag = F[i].dog.act.wag;
        H.tail_tip = add(hp.tail_tip, [-6 * wag * Math.abs(Math.sin(t * 2 * Math.PI * 2.2)), -10 * wag * Math.abs(Math.sin(t * 2 * Math.PI * 2.2))]);
        H.tail_mid = add(hp.tail_mid, [0, -3 * wag * Math.abs(Math.sin(t * 2 * Math.PI * 2.2))]);
        const rest = F[i].dog.act.rest, hd = F[i].dog.act.head;
        if (sg.lookin) {
          const v = win(t, T_COMEIN + 0.05, T_COMEIN + 0.4);
          headPitch = 0; headOff = [lerp(-10, 6, v), lerp(4, -22, v)]; headScale = 0.95;
        } else {
          // head up watching (hd ~0.7), chin to the paws when resting
          headPitch = lerp(-0.08, -0.3, rest) + (hd - 0.7) * 0.4 * (1 - rest);
          headOff = [lerp(0, -22, rest), lerp(0, 60, rest)];
        }
        posture = sg.lookin ? 'lying_looking_in' : (rest > 0.5 ? 'lying_resting' : 'lying');
      }
      const anc = ANCHOR[sg.body];
      // lying across the sill, the front half is further in (on the hall floor): the sheet tips a little, front up
      const tip = sg.body === 'dog_lie' ? 0.025 * win(t, T_LIE + 0.33, T_LIE + 0.8) : 0;
      pieces.push({ id: 'dog_body', mesh: sg.body, mirror, place: { tx: ax, ty: YG, ox: anc[0], oy: anc[1], k: KD, rot: tip }, handles: H, z: 20 });
      const hh = headHandles(sg.head, P, t);
      pieces.push({ id: 'dog_head', mesh: sg.head, mirror: sg.headMirror === undefined ? mirror : sg.headMirror, attach: { to: 'dog_body', pitch: headPitch, off: headOff, scale: headScale }, handles: hh, z: 21 });
      return { pieces, state, facing, posture, headLow: sg.body === 'dog_stand' && t >= T_APPROACH && t < T_LIE };
    }

    // ── the person ──
    const PX = i => F[i].person.x;
    function person(i) {
      const f = F[i], t = f.t, p = f.person;
      const pieces = [];
      const sitting = t >= 6.05;
      if (!sitting) {
        const hp = HP('person_stand.body'), H = {};
        for (const k of ['head', 'chest', 'hip', 'knee', 'foot_a', 'foot_b', 'shoulder']) H[k] = hp[k].slice();
        // calling: lean in and nod on the syllables
        const call = p.voice === 'call' ? 1 : 0, mouth = p.mouth;
        const reach = p.reach;
        const lean = 10 * mouth + 22 * reach;
        H.head = add(H.head, [lean * 1.1 + 4 * Math.sin(t * 9) * call, -4 * mouth + 10 * reach]);
        H.chest = add(H.chest, [lean * 0.6, 6 * reach]);
        H.shoulder = add(H.shoulder, [lean * 0.65, 6 * reach]);
        // stepping aside (5.4–5.95): four short steps to the left, back foot leading; a foot is planted or in the air
        const u = win(t, 5.4, 5.85), D = -(1.25 - 0.28) * DPM, dx = D * u;
        const stepTo = (u, k0) => { let o = 0, lift = 0; for (const [a, b] of k0) { const v = clamp((u - a) / (b - a)); o += D / 3 * ss(v); lift = Math.max(lift, Math.sin(Math.PI * v)); } return [o, lift]; };
        const [ob, lb] = stepTo(u, [[0, 1 / 6], [2 / 6, 3 / 6], [4 / 6, 5 / 6]]), [oa, la] = stepTo(u, [[1 / 6, 2 / 6], [3 / 6, 4 / 6], [5 / 6, 1]]);
        H.foot_b = add(H.foot_b, [ob - dx, -12 * lb]); H.foot_a = add(H.foot_a, [oa - dx, -12 * la]);
        H.hip = add(H.hip, [0, -4 * (lb + la)]); H.chest = add(H.chest, [0, -4 * (lb + la)]); H.head = add(H.head, [0, -4 * (lb + la)]); H.shoulder = add(H.shoulder, [0, -4 * (lb + la)]);
        const pxs = -0.28 + (1.25 - 0.28) * -u;
        // beginning to sit (5.85–6.05): hips go down and back, knees forward
        const s = win(t, 5.85, 6.05);
        H.hip = add(H.hip, [-30 * s, 56 * s]); H.knee = add(H.knee, [44 * s, 22 * s]);
        H.chest = add(H.chest, [18 * s, 52 * s]); H.head = add(H.head, [26 * s, 54 * s]); H.shoulder = add(H.shoulder, [18 * s, 52 * s]);
        pieces.push({ id: 'person_body', mesh: 'person_stand.body', place: { tx: X0 + pxs * S, ty: YG, ox: ANCHOR['person_stand.body'][0], oy: 622, k: K, rot: 0 }, handles: H, z: 10 });
        // arm: shoulder follows the body; hand by IK toward the reach / beckon target
        const ah = HP('person_stand.arm'), A = {};
        let hand = ah.hand.slice();
        const beck = p.voice === 'call' && reach < 0.1 ? 1 : 0;
        if (beck) hand = add(hand, [30, -60 + 14 * Math.sin(t * 14)]);
        hand = [lerp(hand[0], 330, reach), lerp(hand[1], 250, reach)];
        hand = add(hand, [lean * 0.65, 6 * reach + 80 * s]);
        A.shoulder = 'from:person_body:shoulder';
        A.hand = hand; A.elbowIK = true;
        pieces.push({ id: 'person_arm', mesh: 'person_stand.arm', place: 'same:person_body', handles: A, z: 12 });
        return { pieces, posture: s > 0 ? 'sitting_down' : (reach > 0.2 ? 'reaching' : 'standing') };
      } else {
        const hp = HP('person_sit.body'), H = {};
        for (const k of ['head', 'chest', 'hip', 'knee', 'foot_a', 'shoulder']) H[k] = hp[k].slice();
        const s = 1 - win(t, 6.05, 6.35);
        H.head = add(H.head, [-6 * s, -40 * s]); H.chest = add(H.chest, [-4 * s, -36 * s]); H.shoulder = add(H.shoulder, [-4 * s, -36 * s]); H.hip = add(H.hip, [-6 * s, -34 * s]);
        // soft voice: the head bows a little toward the dog
        const soft = p.voice === 'soft' ? 1 : 0, m = p.mouth;
        H.head = add(H.head, [8 * m + 2 * Math.sin(t * 5) * soft, 6 * m]);
        pieces.push({ id: 'person_body', mesh: 'person_sit.body', place: { tx: X0 + -1.25 * S, ty: YG, ox: ANCHOR['person_sit.body'][0], oy: 458, k: K, rot: 0 }, handles: H, z: 10 });
        const ah = HP('person_sit.arm'), A = {};
        // hand resting on the knee, then offered low toward the porch (6.8)
        const knee = [250, 300];
        const low = p.low;
        let hand = [lerp(knee[0], 318, low), lerp(knee[1], 352, low)];
        hand = add(hand, [3 * Math.sin(t * 0.9) * low, 2 * Math.sin(t * 1.3) * low]);
        A.shoulder = 'from:person_body:shoulder'; A.hand = hand; A.elbowIK = true;
        pieces.push({ id: 'person_arm', mesh: 'person_sit.arm', place: 'same:person_body', handles: A, z: 12 });
        return { pieces, posture: low > 0.5 ? 'sitting_hand_low' : 'sitting' };
      }
    }

    function world(i) {
      const t = F[i].t;
      const open = win(t, 6.2, 6.85);
      return { t, door: lerp(0.32, 1.38, open), open, dusk: clamp(t / 32) };
    }

    return { dog, person, world, N, segment, feetOff, X0, S, YG, K, ik, times: { T_RETREAT, T_WATCH1, T_REFUSE, T_WATCH2, T_APPROACH, T_LIE, T_COMEIN } };
  }

  // ── solving a frame: ARAP per piece, warm-started from the same piece's previous solution ──
  function Stage(MESH, ARAP) {
    const solvers = {}, prev = {};
    const get = n => solvers[n] || (solvers[n] = new ARAP.Solver(MESH[n]));
    function toScreen(pl, p) {
      const m = pl.mirror ? -1 : 1, dx = (p[0] - pl.ox) * pl.k, dy = (p[1] - pl.oy) * pl.k;
      const c = Math.cos(pl.rot), s = Math.sin(pl.rot);
      return [pl.tx + m * (c * dx - s * dy), pl.ty + (s * dx + c * dy)];
    }
    function vtxMean(X, vs) { let x = 0, y = 0; for (const v of vs) { x += X[2 * v]; y += X[2 * v + 1]; } return [x / vs.length, y / vs.length]; }
    function nearest(mesh, p) { let b = 0, bd = 1e18; mesh.verts.forEach((v, i) => { const d = (v[0] - p[0]) ** 2 + (v[1] - p[1]) ** 2; if (d < bd) { bd = d; b = i; } }); return b; }

    function solveFrame(list, iters = 8) {
      const out = {}, diag = {};
      const order = list.slice().sort((a, b) => (a.attach || a.place === undefined || typeof a.place === 'string' ? 1 : 0) - (b.attach || typeof b.place === 'string' ? 1 : 0));
      for (const pc of order) {
        const mesh = MESH[pc.mesh], sol = get(pc.mesh);
        let place = pc.place;
        if (pc.attach) { // place the head at the parent's deformed socket, rotated with the neck
          const par = out[pc.attach.to], pm = MESH[par.mesh];
          const sk = pm.socket; const sv = pm._sock || (pm._sock = [nearest(pm, sk.at), nearest(pm, sk.toward)]);
          const a0 = Math.atan2(pm.verts[sv[1]][1] - pm.verts[sv[0]][1], pm.verts[sv[1]][0] - pm.verts[sv[0]][0]);
          const a1 = Math.atan2(par.X[2 * sv[1] + 1] - par.X[2 * sv[0] + 1], par.X[2 * sv[1]] - par.X[2 * sv[0]]);
          let neck = a1 - a0; while (neck > Math.PI) neck -= 2 * Math.PI; while (neck < -Math.PI) neck += 2 * Math.PI;
          const at = [par.X[2 * sv[0]] + pc.attach.off[0], par.X[2 * sv[0] + 1] + pc.attach.off[1]];
          const scr = toScreen(par.place, at);
          // pitch: positive = nose up for the drawing's own facing (rotation is applied before the mirror)
          const hs = mesh.socket.at, r = pc.attach.pitch + 0.6 * neck * (!!pc.mirror === !!par.place.mirror ? 1 : -1);
          place = { tx: scr[0], ty: scr[1], ox: hs[0], oy: hs[1], k: par.place.k * (pc.attach.scale || 1), rot: r, mirror: !!pc.mirror };
        } else if (typeof pc.place === 'string') {
          place = out[pc.place.split(':')[1]].place;
        } else place = Object.assign({ mirror: !!pc.mirror }, pc.place);
        // handles → vertex sets
        const hs = [];
        let elbowIK = false;
        for (const [name, at0] of Object.entries(pc.handles)) {
          if (name === 'elbowIK') { elbowIK = true; continue; }
          let at = at0;
          if (typeof at0 === 'string') { const [, pid, hn] = at0.split(':'); const par = out[pid]; at = vtxMean(par.X, MESH[par.mesh].handles[hn]); }
          if (!mesh.handles[name]) continue;
          // feet keep their paws level on the boards (fixed rotation); every other handle's rotation is estimated
          const fixed = pc.mesh.startsWith('dog_') && /^[fh][12]$/.test(name) ? 0 : undefined;
          hs.push({ name, verts: mesh.handles[name], at: at.slice(), ang: fixed });
        }
        if (elbowIK) { // arm: elbow from shoulder and hand
          const hp = mesh.handle_points, sh = hs.find(h => h.name === 'shoulder').at, hd = hs.find(h => h.name === 'hand').at;
          hs.push({ name: 'elbow', verts: mesh.handles.elbow, at: ik(sh, hd, hp.shoulder, hp.elbow, hp.hand) });
        }
        let X = prev[pc.id] && prev[pc.id].mesh === pc.mesh && prev[pc.id].mirror === !!pc.mirror ? prev[pc.id].X : null;
        let it = iters;
        if (!X) { X = sol.initFrom(hs); it = 40; }
        sol.solveRepair(hs, X, it);
        const d = sol.diagnose(X);
        out[pc.id] = { id: pc.id, mesh: pc.mesh, X, place, z: pc.z, handles: hs };
        diag[pc.id] = d;
        prev[pc.id] = { mesh: pc.mesh, mirror: !!pc.mirror, X };
      }
      for (const id of Object.keys(prev)) if (!out[id]) delete prev[id];
      return { pieces: out, diag, toScreen };
    }
    return { solveFrame, toScreen, solvers };
  }

  const api = { Rig, Stage, ik, K, X0, S, YG };
  if (typeof module !== 'undefined') module.exports = api; else root.RIG = api;
})(typeof window !== 'undefined' ? window : globalThis);
