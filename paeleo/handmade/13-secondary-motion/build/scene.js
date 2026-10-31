// SCION 13 · Secondary Motion — rig and solver for the threshold scene.
// Two layers, as in Willett et al. 2017: (1) PRIMARY trajectories of rigid paper pieces (the dog's torso rings, neck, skull,
// muzzle, legs; the person's torso, head, limbs; the door leaf), performed from the score; (2) SECONDARY rig links: chains of
// point masses hung from those pieces, each an inertial spring-damper pulled toward a rest shape that the primary piece
// carries, under gravity and wind (air drag toward the wind velocity), with collision masks (floor, the dog's body spheres,
// the person's limbs). Time base: score frames at 24 fps, 4 solver substeps per frame. World units: metres; X along the
// porch (score x), Y up, Z toward the viewer. Deterministic (seeded); no pixels are produced here.
(function (G) {
  'use strict';
  const PI = Math.PI, TAU = 2 * PI;
  const clamp = (x, a, b) => x < a ? a : x > b ? b : x, lerp = (a, b, t) => a + (b - a) * t;
  const ss = (t, a, b) => { const x = clamp((t - a) / (b - a), 0, 1); return x * x * (3 - 2 * x); };
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]], sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k], dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const len = a => Math.hypot(a[0], a[1], a[2]), norm = a => { const l = len(a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const lerp3 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
  const comb = (...a) => { const r = [0, 0, 0]; for (let i = 0; i < a.length; i += 2) { r[0] += a[i][0] * a[i + 1]; r[1] += a[i][1] * a[i + 1]; r[2] += a[i][2] * a[i + 1]; } return r; };
  const wrap = a => { while (a > PI) a -= TAU; while (a < -PI) a += TAU; return a; };
  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  // heading φ: 0 faces the door (−X), π/2 faces the viewer (+Z), π faces away from the house (+X)
  const HD = φ => [-Math.cos(φ), 0, Math.sin(φ)], LAT = φ => [Math.sin(φ), 0, Math.cos(φ)];
  const DP = (φ, p) => [-Math.cos(φ) * Math.cos(p), Math.sin(p), Math.sin(φ) * Math.cos(p)];
  const UP = [0, 1, 0], DOWN = [0, -1, 0];
  function track(t, keys) { // smoothstep between keys [[t,v],...]
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) { const [t0, v0] = keys[i - 1], [t1, v1] = keys[i]; return lerp(v0, v1, ss(t, t0, t1)); }
    return keys[keys.length - 1][1];
  }

  // ---------- the place ----------
  const PLACE = {
    wallIn: -0.14, wallOut: 0, doorZ: [-0.46, 0.46], doorH: 2.0, cutZ: 0.46, roomBackZ: -2.6, roomLeftX: -3.4,
    porchEnd: 4.9, porchZ: [-1.25, 1.05], yardY: -0.45, curtainX: -0.03, hinge: [-0.14, -0.46], leafW: 0.92,
    lamp: [-2.1, 2.2, -1.2],
  };
  const floorY = (x, z) => (x > PLACE.porchEnd + 0.02 ? (x < PLACE.porchEnd + 0.62 ? -0.15 * Math.ceil((x - PLACE.porchEnd) / 0.2) : PLACE.yardY) : 0);

  // ---------- presets (material-specific secondary parameters) ----------
  // k: spring toward the rest shape the primary piece carries (1/s^2), c: damping relative to that rest motion (1/s),
  // grav: gravity scale, drag: air drag toward the wind velocity (1/s). 'none' pins every secondary node to its rest shape;
  // 'generic' gives every link the same oscillator and ignores intention (no flattening, no flick).
  const MAT = {
    fur:     { k: 70, kFear: 230, c: 7, cFear: 17, grav: 0.35, drag: 1.4 },  // crepe-paper fringe: light, papery, quick to settle
    ruff:    { k: 60, kFear: 210, c: 6.5, cFear: 16, grav: 0.35, drag: 1.4 },
    ear:     { k: 120, c: 7.5, grav: 0.55, drag: 0.6 },                       // layered tissue flap, a little heavier
    feather: { k: 45, c: 6, grav: 0.45, drag: 1.6 },                          // fringe hung on a moving link (2nd order)
    tail:    { k: 95, c: 8, grav: 0.25, drag: 0.7 },
    dewlap:  { k: 22, c: 3.2, grav: 0.8, drag: 0.8 },                         // loose, swings and lags
    curtain: { k: 6, c: 2.2, grav: 1, drag: 2.4 },                            // long tissue strips, gravity-hung
    reed:    { k: 140, c: 2.6, grav: 0.15, drag: 0.9 },                       // springy stem, little damping
    hair:    { k: 28, c: 4.2, grav: 0.9, drag: 0.9 },
    scarf:   { k: 9, c: 4.2, grav: 1, drag: 1.0 },
    coat:    { k: 30, c: 6, grav: 1, drag: 0.5 },                             // heavier sugar-paper coat tails
  };
  const GENERIC = { k: 60, c: 4, grav: 0.5, drag: 1.0 };

  // ---------- score + performance curves ----------
  let SC = null, PRESET = 'tuned';
  const SOFT = [7.40, 10.40, 26.40];       // soft-voice onsets (score timeline)
  function dogPrimary(i) {
    const f = SC.frames[i], a = f.dog.act, t = f.t;
    // body heading: turns its back 3.47–3.90 (through facing the viewer, head leading); turns back 8.05–8.80
    let th = PI * ss(t, 3.44, 3.78); if (t >= 7.9) th = PI * (1 - ss(t, 8.05, 8.80));
    // head heading in the world (leads the body)
    let hw = PI * ss(t, 3.40, 3.70);
    if (t >= 7.38) hw = lerp(PI, 0.42, ss(t, 7.44, 7.68));          // over the shoulder to the door, muzzle level, body still down
    if (t >= 8.0) hw = lerp(0.42, 0, ss(t, 8.05, 8.8));
    if (t >= 26.3) hw = lerp(0, -1.05, ss(t, 26.45, 26.95));          // looks in: turns its head deeper into the room, away from us
    if (t >= 28.15) hw = lerp(-1.05, -0.5, ss(t, 28.2, 28.9));
    // lying: refusal (lies down with its back turned), stands at 7.9; lies across the sill from 23.79
    let lieF = ss(t, 4.25, 4.75) * (1 - ss(t, 7.86, 8.25)), lieR = ss(t, 4.40, 4.95) * (1 - ss(t, 7.92, 8.36));
    if (t >= 23.0) { lieF = ss(t, 23.79, 24.30); lieR = ss(t, 23.92, 24.55); }
    let rest = ss(t, 5.5, 6.3) * (1 - ss(t, 7.40, 7.56));
    if (t >= 23) rest = ss(t, 25.3, 26.0) * (1 - ss(t, 26.42, 26.65)) + ss(t, 28.3, 29.0) * 0.92;
    const look = ss(t, 26.45, 26.95) * (1 - 0.6 * ss(t, 28.25, 28.9));
    const hh = track(t, [[0, 0.9], [0.98, 0.9], [1.3, 0.25], [2.33, 0.3], [2.9, 0.85], [3.42, 0.85], [3.8, 0.15], [7.42, 0.15], [7.62, 0.62], [8.3, 0.62], [8.9, 0.9], [14.62, 0.9], [15.15, 0.0], [23.79, 0.0], [24.4, 0.62], [25.3, 0.55], [26.0, 0.35], [26.45, 0.35], [26.9, 0.42], [28.2, 0.42], [28.9, 0.25]]);
    const fear = track(t, [[0, 0], [0.98, 0], [1.25, 1], [2.33, 1], [2.9, 0.35], [3.42, 0.35], [3.62, 1], [7.42, 1], [8.6, 0.25], [14.7, 0.12], [23.79, 0.12], [24.5, 0]]);
    let ear = a.ear; if (t > 26.3) ear = Math.min(ear, 0.72);
    if (t > 7.38 && t < 8.6) ear = Math.max(ear, 0.95 * ss(t, 7.42, 7.52));
    const crouch = (t > 23.5 ? 0 : a.crouch) * (1 - Math.max(lieF, lieR));
    const turnStep = Math.max(ss(t, 3.42, 3.55) * (1 - ss(t, 3.75, 3.9)), ss(t, 8.05, 8.2) * (1 - ss(t, 8.7, 8.85)));
    return { t, i, x: f.dog.x, th, hw, lieF, lieR, rest, look, hh, fear, ear, crouch, tail: a.tail, wag: a.wag, moving: a.moving, turnStep, state: f.dog.state };
  }
  function personPrimary(i) {
    const f = SC.frames[i], p = f.person, t = f.t;
    const mv = clamp((p.x - (-0.28)) / (-1.25 - (-0.28)), 0, 1);
    const call = Math.max(ss(t, 0.95, 1.15) * (1 - ss(t, 2.1, 2.5)), ss(t, 3.35, 3.55) * (1 - ss(t, 4.5, 4.8)));
    const push = ss(t, 5.85, 6.12) * (1 - ss(t, 6.35, 6.75));
    return { t, x: p.x, z: lerp(0.05, 0.38, mv), mv, sit: p.sit, reach: p.reach, low: p.low, call, push, mouth: p.mouth, voice: p.voice };
  }

  // ---------- dog primary geometry (rigid paper pieces) ----------
  const CORES = [[-0.44, 0.12], [-0.31, 0.155], [-0.15, 0.165], [0.02, 0.17], [0.18, 0.18], [0.32, 0.165]];
  const coreR = f => { if (f <= CORES[0][0]) return CORES[0][1]; for (let k = 1; k < CORES.length; k++) if (f <= CORES[k][0]) return lerp(CORES[k - 1][1], CORES[k][1], (f - CORES[k - 1][0]) / (CORES[k][0] - CORES[k - 1][0])); return CORES[CORES.length - 1][1] * clamp(1 - (f - 0.32) * 2, 0.6, 1); };
  const LEGS = [{ f: 0.27, l: 0.095, off: 0.25, fore: 1 }, { f: 0.27, l: -0.095, off: 0.75, fore: 1 }, { f: -0.30, l: 0.105, off: 0.0, fore: 0 }, { f: -0.30, l: -0.105, off: 0.5, fore: 0 }];
  const STRIDE = 0.56;
  function ik(J, P, a, b, hint) {
    let d = sub(P, J), dl = len(d); const maxd = (a + b) * 0.999; if (dl > maxd) { P = add(J, mul(d, maxd / dl)); d = sub(P, J); dl = maxd; }
    const u = norm(d), x = (a * a - b * b + dl * dl) / (2 * dl), h = Math.sqrt(Math.max(0, a * a - x * x));
    let pp = sub(hint, mul(u, dot(hint, u))); pp = norm(pp);
    return { knee: add(add(J, mul(u, x)), mul(pp, h)), paw: P };
  }
  function dogGeom(P, dist) {
    const F = HD(P.th), L = LAT(P.th), t = P.t;
    const bob = 0.012 * Math.sin(TAU * 2 * dist / STRIDE) * P.moving;
    const breath = (1 - P.moving) * 0.018 * Math.sin(TAU * t / 2.6);
    const at = (f, y, l) => [P.x + F[0] * f + L[0] * l, y, F[2] * f + L[2] * l];
    const lieAt = f => lerp(P.lieR, P.lieF, clamp((f + 0.44) / 0.8, 0, 1));
    const backY = f => lerp(0.56 - 0.035 * clamp((-f - 0.3) / 0.15, 0, 1) - 0.07 * P.crouch - 0.10 * P.crouch * clamp(-f / 0.44, 0, 1) + bob, 0.30 - 0.03 * clamp((-f - 0.3) / 0.15, 0, 1), lieAt(f));
    const cores = CORES.map(([f, r]) => { const rr = r * (1 + breath); return { c: at(f, backY(f) - rr, 0), r: rr, f }; });
    const ring = f => { const r = coreR(f) * (1 + breath); return { c: at(f, backY(f) - r, 0), r }; };
    // neck and head
    const lie = Math.max(P.lieF, P.lieR) * 0.5 + P.lieF * 0.5;
    const Nb = at(0.36, backY(0.36) - 0.05, 0);
    const hy = wrap(P.hw - P.th), nh = P.th + lerp(0.62, 0.3, P.look) * hy;
    let alpha = lerp(-0.55, 0.85, P.hh), beta = lerp(-0.45, 0.04, P.hh);
    alpha = lerp(alpha, -0.62, P.rest); beta = lerp(beta, -0.08, P.rest);
    alpha = lerp(alpha, -0.12, P.look); beta = lerp(beta, -0.02, P.look);
    const nl = lerp(0.27, 0.35, lie) + 0.27 * P.look;
    let Hc = add(Nb, mul(DP(nh, alpha), nl)); if (Hc[1] < 0.108) Hc[1] = 0.108;
    const md = DP(P.hw, beta), Lh = LAT(P.hw), Uh = norm(sub(UP, mul(md, dot(UP, md))));
    const neck = [{ c: lerp3(Nb, Hc, 0.36), r: 0.112 }, { c: lerp3(Nb, Hc, 0.7), r: 0.1 }];
    const head = { c: Hc, r: 0.12 };
    const muz = [{ c: comb(Hc, 1, md, 0.105, Uh, -0.025), r: 0.08 }, { c: comb(Hc, 1, md, 0.18, Uh, -0.035), r: 0.062 }];
    const nose = { c: comb(Hc, 1, md, 0.238, Uh, -0.022), r: 0.034 };
    const eyes = [1, -1].map(s => ({ c: comb(Hc, 1, md, 0.08, Uh, 0.04, Lh, 0.066 * s), n: norm(comb(md, 0.55, Lh, s, Uh, 0.2)) }));
    // legs: stance feet stay planted (offset falls exactly as the body advances), swing feet lift
    const legs = LEGS.map(lg => {
      const lieL = lg.fore ? P.lieF : P.lieR;
      const J = at(lg.f, backY(lg.f) - 0.12, lg.l * 0.9);
      const ph = ((dist / STRIDE + lg.off) % 1 + 1) % 1;
      let o, lift = 0;
      if (ph < 0.62) o = STRIDE * (0.31 - ph); else { const q = (ph - 0.62) / 0.38; o = STRIDE * (-0.31 + 0.62 * q); lift = 0.075 * Math.sin(PI * q); }
      lift = lift * P.moving + P.turnStep * 0.06 * Math.max(0, Math.sin(TAU * (t * 2.6 + lg.off)));
      const stand = at(lg.f + (lg.fore ? 0.02 : -0.02) + o * P.moving, 0.03 + lift, lg.l * 1.05);
      const lying = lg.fore ? at(0.75 + 0.1 * P.look, 0.035, lg.l * 0.85) : at(-0.03, 0.04, lg.l * 2.0);
      const paw = lerp3(stand, lying, lieL);
      const hint = lg.fore ? comb(F, -1, UP, -0.15 * lieL) : comb(F, 1, L, Math.sign(lg.l) * 1.2 * lieL, UP, -0.4 * lieL);
      const k = ik(J, paw, lg.fore ? 0.22 : 0.24, lg.fore ? 0.245 : 0.25, hint);
      return { J, knee: k.knee, paw: k.paw, near: lg.l > 0, fore: lg.fore, lift };
    });
    const tailRoot = at(-0.5, backY(-0.44) - 0.035, 0);
    return { F, L, at, backY, ring, cores, neck, head, muz, nose, eyes, md, Lh, Uh, Nb, Hc, legs, tailRoot, lie };
  }

  // ---------- secondary links ----------
  const strands = [];      // every secondary chain in the scene
  function Strand(o) {
    const s = Object.assign({ n: 4, seg: 0.06, grav: 1, drag: 1, k: 50, c: 5, mask: {}, curl: 0.2, kTip: 0.55, rad: 0.006 }, o);
    s.p = []; s.v = []; s.R = null; s.Rprev = null; s.kick = [0, 0, 0];
    strands.push(s); return s;
  }
  function restShape(s, root, dir) {
    const R = [root.slice()]; let p = root;
    for (let k = 1; k < s.n; k++) { const d = norm(add(dir, mul(DOWN, s.curl * k))); p = add(p, mul(d, s.seg)); R.push(p); }
    return R;
  }

  // wind velocity field (m/s): gusts from the yard toward the house; none indoors; a draft out of the door when it opens
  function gust(t) {
    const g = (c, w, a) => a * Math.exp(-0.5 * ((t - c) / w) ** 2);
    return 0.35 + 0.18 * Math.sin(TAU * t / 3.7) + 0.1 * Math.sin(TAU * t / 1.3 + 1) + g(5.4, 0.7, 1.6) + g(12.8, 0.8, 1.9) + g(19.6, 0.6, 0.9) + g(30.4, 0.7, 1.2);
  }
  let DRAFT = 0;
  function wind(t, p) {
    const out = ss(p[0], -0.2, 0.7) * (p[0] > PLACE.porchEnd + 2 ? 1 : 1);
    const g = gust(t) * (1 + 0.15 * Math.sin(p[0] * 1.7 + t * 2.3) + 0.1 * Math.sin(p[2] * 2.1 - t * 3.1));
    const w = [-1.6 * g * out, 0.12 * g * out * Math.sin(t * 4 + p[0]), 0.35 * g * out];
    const inDoor = Math.exp(-((p[0] - 0.1) ** 2) / 0.5) * (Math.abs(p[2]) < 0.6 ? 1 : 0.3);
    w[0] += DRAFT * 0.9 * inDoor;
    return w;
  }

  // ---------- build the rig ----------
  const DOG = { body: [], ruff: [], head: [], ears: [], earFeathers: [], tail: null, tailFeathers: [], dewlap: [], legFeathers: [] };
  const PERSON = { hair: [], scarf: [], coat: [] };
  const CURTAIN = [], REEDS = [];
  const FUR_COL = ['oat', 'ochre', 'rust', 'cream', 'char'];
  function buildRig() {
    const R = rng(1313);
    // body fringe: 9 rings × 12 angles of crepe strips hung from the torso
    const NR = 15, rings = Array.from({ length: NR }, (_, k) => lerp(-0.48, 0.38, k / (NR - 1)));
    const angs = [-160, -132, -104, -76, -48, -20, 8, 36, 64, 92, 120, 148].map(d => d * PI / 180);
    const ROWC = ['cream', 'oat', 'oat', 'ochre', 'rust', 'char', 'char', 'rust', 'ochre', 'oat', 'oat', 'cream'];
    const ALT = { cream: 'oat', oat: 'ochre', ochre: 'oat', rust: 'char', char: 'rust' };
    rings.forEach((f0, ri) => angs.forEach((a0, ai) => {
      const f = f0 + (R() - 0.5) * 0.045, a = a0 + (R() - 0.5) * 0.3 + (ri % 2) * 0.24;
      const top = Math.cos(a);
      const col = R() < 0.28 ? ALT[ROWC[ai]] : ROWC[ai];
      const L0 = (top > -0.3 ? 0.17 : 0.11) + 0.08 * R() + (f > 0.25 ? 0.03 : 0);
      DOG.body.push(Strand({ kind: 'fur', group: 'dog', part: 'body', mat: 'fur', f, a, ai, ri, n: 4, seg: L0 / 3, col, w: 0.06 + 0.03 * R(), seed: R() * 1e6 | 0, jit: R(), mask: { floor: 1, dog: 1, reed: 0 } }));
    }));
    // neck ruff: 2 rings × 10
    [0.3, 0.66].forEach((u, ri) => { for (let k = 0; k < 10; k++) { const a = -PI + (k + 0.5) * TAU / 10; DOG.ruff.push(Strand({ kind: 'fur', group: 'dog', part: 'neck', mat: 'ruff', u, a, n: 4, seg: (0.17 + 0.04 * R()) / 3, col: Math.cos(a) > 0.3 ? 'char' : (R() < 0.5 ? 'cream' : 'oat'), w: 0.055, seed: R() * 1e6 | 0, jit: R(), mask: { floor: 1, dog: 1 } })); } });
    // head: forelock, cheek tufts, beard
    const hs = [['fore', 0, 0.08], ['fore', 0.045, 0.075], ['fore', -0.045, 0.075], ['cheek', 1, 0.12], ['cheek', -1, 0.12], ['cheekb', 1, 0.13], ['cheekb', -1, 0.13], ['beard', 0.025, 0.08], ['beard', -0.025, 0.08], ['beard', 0, 0.095]];
    hs.forEach(([w, v, l]) => DOG.head.push(Strand({ kind: 'fur', group: 'dog', part: 'head', mat: 'ruff', where: w, q: v, n: 3, seg: l / 2, col: w === 'beard' ? 'cream' : w === 'fore' ? 'oat' : 'cream', w: 0.045, seed: R() * 1e6 | 0, jit: R(), mask: { floor: 1, dog: 1 } })));
    // ears: a 4-node tissue flap per side, with 2 feather strips per node
    [1, -1].forEach(sg => {
      const e = Strand({ kind: 'ear', group: 'dog', part: 'head', mat: 'ear', sg, n: 5, seg: 0.062, curl: 0.05, kTip: 0.7, col: 'rust', w: 0.075, mask: { floor: 1, dog: 1 } });
      DOG.ears.push(e);
      for (let k = 1; k < 5; k++) for (let j = 0; j < 2; j++) DOG.earFeathers.push(Strand({ kind: 'fur', group: 'dog', part: 'head', mat: 'feather', host: e, hk: k, sg, n: 3, seg: 0.035 + 0.01 * R(), col: R() < 0.6 ? 'rust' : 'ochre', w: 0.035, seed: R() * 1e6 | 0, jit: R(), mask: { floor: 1, dog: 1 } }));
    });
    // tail: 6-node link with a feathered plume
    DOG.tail = Strand({ kind: 'tail', group: 'dog', part: 'tail', mat: 'tail', n: 6, seg: 0.075, curl: -0.04, kTip: 0.6, col: 'oat', w: 0.05, mask: { floor: 1, dog: 1 } });
    for (let k = 1; k < 6; k++) for (let j = 0; j < 4; j++) DOG.tailFeathers.push(Strand({ kind: 'fur', group: 'dog', part: 'tail', mat: 'feather', host: DOG.tail, hk: k, j, n: 3, seg: (0.03 + 0.035 * R()) * (k < 5 ? 1 : 0.8), col: j === 1 ? 'cream' : (R() < 0.5 ? 'oat' : 'ochre'), w: 0.07, seed: R() * 1e6 | 0, jit: R(), mask: { floor: 1, dog: 1 } }));
    // dewlap: loose throat fringe
    for (let k = 0; k < 3; k++) DOG.dewlap.push(Strand({ kind: 'fur', group: 'dog', part: 'head', mat: 'dewlap', q: (k - 1) * 0.03, n: 4, seg: 0.045, curl: 0.05, col: 'cream', w: 0.06, seed: R() * 1e6 | 0, jit: R(), mask: { floor: 1, dog: 1 } }));
    // leg feathering (trousers) on the upper legs
    LEGS.forEach((lg, li) => { for (let j = 0; j < 3; j++) DOG.legFeathers.push(Strand({ kind: 'fur', group: 'dog', part: 'leg', mat: 'feather', li, j, n: 3, seg: 0.05, col: lg.fore ? 'oat' : 'ochre', w: 0.04, seed: R() * 1e6 | 0, jit: R(), mask: { floor: 1, dog: 0 } })); });
    // curtain: 13 tissue strips hung from the lintel
    for (let k = 0; k < 8; k++) { const z = lerp(-0.42, -0.04, k / 7); CURTAIN.push(Strand({ kind: 'curtain', group: 'curtain', mat: 'curtain', z, n: 10, seg: 0.2, curl: 0, kTip: 1, col: k % 3 === 0 ? 'madder' : k % 3 === 1 ? 'saffron' : 'rose', w: 0.05, seed: R() * 1e6 | 0, jit: R(), rad: 0.02, mask: { floor: 1, dog: 1, person: 1 } })); }
    // reeds by the porch steps (yard) and behind the porch rail
    const RD = rng(77);
    for (let k = 0; k < 34; k++) {
      let x, z; if (k < 20) { x = 5.0 + RD() * 1.6; z = lerp(-1.5, 1.35, RD()); } else { x = 0.6 + RD() * 5.2; z = -1.55 - RD() * 0.8; }
      const h = 0.8 + 0.6 * RD();
      REEDS.push(Strand({ kind: 'reed', group: 'reed', mat: 'reed', x, z, lean: (RD() - 0.5) * 0.25, n: 6, seg: h / 5, curl: 0, kTip: 0.35, col: RD() < 0.5 ? 'reedA' : 'reedB', w: 0.022, head: RD() < 0.55, seed: RD() * 1e6 | 0, jit: RD(), rad: 0.015, mask: { floor: 0, dog: 1 } }));
    }
    // the person's hair, scarf and coat tails
    for (let k = 0; k < 7; k++) PERSON.hair.push(Strand({ kind: 'hair', group: 'person', mat: 'hair', q: k / 6, n: 5, seg: 0.07 + 0.012 * R(), curl: 0.1, col: 'hair', w: 0.045, seed: R() * 1e6 | 0, jit: R(), mask: { floor: 1, phead: 1 } }));
    PERSON.scarf.push(Strand({ kind: 'scarf', group: 'person', mat: 'scarf', which: 0, n: 7, seg: 0.07, curl: 0, col: 'scarf', w: 0.075, mask: { floor: 1, pbody: 1 } }));
    PERSON.scarf.push(Strand({ kind: 'scarf', group: 'person', mat: 'scarf', which: 1, n: 5, seg: 0.07, curl: 0, col: 'scarf', w: 0.07, mask: { floor: 1, pbody: 1 } }));
    for (let k = 0; k < 3; k++) PERSON.coat.push(Strand({ kind: 'coat', group: 'person', mat: 'coat', q: k, n: 4, seg: 0.105, curl: 0, col: 'coat', w: 0.13, mask: { floor: 1, pleg: 1 } }));
  }

  // ---------- per-frame rest shapes from the primary pieces ----------
  function matOf(s) { if (PRESET === 'generic') return GENERIC; return MAT[s.mat]; }
  function dogRest(s, g, P) {
    const fear = PRESET === 'generic' ? 0 : P.fear;
    if (s.part === 'body') {
      const rg = g.ring(s.f), n = add(mul(UP, Math.cos(s.a)), mul(g.L, Math.sin(s.a)));
      const root = add(rg.c, mul(n, rg.r * 0.97));
      const lie = lerp(P.lieR, P.lieF, clamp((s.f + 0.44) / 0.8, 0, 1)), sa = Math.abs(Math.sin(s.a));
      const calm = norm(comb(n, 0.55 + 2.2 * lie * sa, DOWN, 1.0 - 0.8 * lie, g.F, -0.18 - 0.8 * lie));
      const flat = norm(comb(n, 0.08, DOWN, 0.35, g.F, -1.25));
      return { root, dir: norm(lerp3(calm, flat, fear)) };
    }
    if (s.part === 'neck') {
      const ax = norm(sub(g.Hc, g.Nb)), r1 = norm(sub(UP, mul(ax, dot(UP, ax)))), r2 = cross(ax, r1);
      const n = add(mul(r1, Math.cos(s.a)), mul(r2, Math.sin(s.a)));
      const c = lerp3(g.Nb, g.Hc, s.u), r = lerp(0.115, 0.1, s.u);
      const calm = norm(comb(n, 0.6, DOWN, 1, ax, -0.35)), flat = norm(comb(n, 0.1, ax, -1.2, DOWN, 0.4));
      return { root: add(c, mul(n, r * 0.95)), dir: norm(lerp3(calm, flat, fear)) };
    }
    if (s.part === 'head' && s.kind === 'fur' && !s.host) {
      const { Hc, md, Lh, Uh } = g;
      if (s.where === 'fore') return { root: comb(Hc, 1, Uh, 0.095, md, 0.035, Lh, s.q), dir: norm(comb(md, 0.75, DOWN, 0.6, Lh, s.q * 4)) };
      if (s.where === 'cheek') return { root: comb(Hc, 1, Lh, 0.09 * s.q, Uh, 0.0, md, 0.03), dir: norm(comb(Lh, 0.5 * s.q, DOWN, 1, md, -0.3)) };
      if (s.where === 'cheekb') return { root: comb(Hc, 1, Lh, 0.085 * s.q, Uh, 0.03, md, -0.05), dir: norm(comb(Lh, 0.4 * s.q, DOWN, 1, md, -0.6)) };
      if (s.where === 'beard') return { root: comb(g.muz[1].c, 1, Uh, -0.045, Lh, s.q, md, 0.02), dir: norm(comb(DOWN, 1, md, 0.25)) };
      if (s.mat === 'dewlap') return { root: comb(g.Hc, 1, Uh, -0.085, md, -0.02, Lh, s.q), dir: norm(comb(DOWN, 1, md, -0.2)) };
    }
    if (s.kind === 'ear') {
      const { Hc, md, Lh, Uh } = g;
      const root = comb(Hc, 1, Uh, 0.075, Lh, 0.088 * s.sg, md, -0.035);
      const e = PRESET === 'generic' ? 0.6 : P.ear;
      const flat = norm(comb(md, -0.75, Uh, -0.45, Lh, 0.3 * s.sg));
      const prick = norm(comb(Uh, 0.55, md, 0.35, Lh, 0.8 * s.sg));
      return { root, dir: norm(lerp3(flat, prick, 0.85 * clamp(e, 0, 1))) };
    }
    if (s.kind === 'tail') {
      const tau = PRESET === 'generic' ? 0.5 : P.tail;
      const gam = 0.55 - 1.85 * tau;
      const wag = (PRESET === 'generic' ? 0 : P.wag) * 0.95 * Math.sin(TAU * 2.1 * P.t);
      return { root: g.tailRoot, dir: norm(comb(g.F, -Math.cos(gam), UP, Math.sin(gam), g.L, wag)) };
    }
    if (s.host) { // feather on a moving link
      const h = s.host, k = s.hk, p = h.p[k], pd = norm(sub(h.p[k], h.p[k - 1]));
      if (s.part === 'tail') { const side = s.j === 0 ? g.L : s.j === 2 ? mul(g.L, -1) : s.j === 3 ? UP : [0, 0, 0]; return { root: p, dir: norm(comb(DOWN, 0.35, pd, 1.0, side, 0.6)) }; }
      return { root: p, dir: norm(comb(DOWN, 1, pd, 0.5, g.Lh, 0.4 * s.sg)) };
    }
    if (s.part === 'leg') {
      const lg = g.legs[s.li], p = lerp3(lg.J, lg.knee, 0.35 + 0.25 * s.j);
      return { root: p, dir: norm(comb(DOWN, 1, g.F, -0.5)) };
    }
    if (s.mat === 'dewlap') return { root: comb(g.Hc, 1, g.Uh, -0.085, g.md, -0.02, g.Lh, s.q), dir: norm(comb(DOWN, 1, g.md, -0.2)) };
    throw new Error('no rest for ' + s.kind + s.part);
  }

  // ---------- person primary (rigid paper pieces) ----------
  function personGeom(Q, door) {
    const z = Q.z, x = Q.x, sit = ss(Q.sit, 0, 1);
    const stepPh = Q.mv * 5.2 * PI;                             // two backward steps while moving aside
    const walking = (Q.mv > 0.01 && Q.mv < 0.99) ? 1 : 0;
    const pelvis = [x - 0.02 * sit, lerp(0.95, 0.14, sit) - 0.02 * walking * Math.abs(Math.sin(stepPh)), z];
    const lean = 0.2 * Q.call + 0.12 * Q.reach + 0.18 * Q.low * sit;
    const tor = [Math.sin(lean) * 0.54, Math.cos(lean) * 0.54];
    const neck = [pelvis[0] + tor[0], pelvis[1] + tor[1], z];
    const headC = [neck[0] + 0.05 + 0.08 * Q.call, neck[1] + 0.17 - 0.02 * Q.low * sit, z];
    const shN = [neck[0] - 0.02, neck[1] - 0.05, z + 0.13], shF = [neck[0] - 0.02, neck[1] - 0.05, z - 0.13];
    // near arm: rest -> reach toward the dog -> hand low to the floor
    let handN = [shN[0] + 0.06, shN[1] - 0.56, z + 0.15];
    handN = lerp3(handN, [shN[0] + 0.6, shN[1] - 0.08, z + 0.17], Q.reach);
    handN = lerp3(handN, [x + 0.55, 0.12, z + 0.16], Q.low * sit);
    handN = lerp3(handN, [shN[0] + 0.25, shN[1] - 0.2, z + 0.14], Q.call * (1 - Q.reach) * 0.5);
    let handF = [shF[0] - 0.02, shF[1] - 0.55, z - 0.15];
    if (door) handF = lerp3(handF, [door.edge[0] + 0.02, 0.55, door.edge[2] - 0.0], Q.push);
    const armN = ik(shN, handN, 0.3, 0.29, [0.1, -1, 0]), armF = ik(shF, handF, 0.3, 0.29, [-0.2, -1, 0]);
    // legs: standing (two steps while moving aside), squat, seated on the floor with legs out
    const hipN = [pelvis[0], pelvis[1], z + 0.08], hipF = [pelvis[0], pelvis[1], z - 0.08];
    const stepA = 0.16 * Math.sin(stepPh) * walking, liftA = 0.06 * Math.max(0, Math.sin(stepPh)) * walking, liftB = 0.06 * Math.max(0, -Math.sin(stepPh)) * walking;
    const footStandN = [x + 0.06 + stepA, 0.04 + liftA, z + 0.09], footStandF = [x - 0.04 - stepA, 0.04 + liftB, z - 0.09];
    const footSitN = [x + 0.6, 0.05, z + 0.1], footSitF = [x + 0.5, 0.05, z - 0.08];
    const fN = lerp3(footStandN, footSitN, ss(sit, 0.35, 1)), fF = lerp3(footStandF, footSitF, ss(sit, 0.45, 1));
    const legN = ik(hipN, fN, 0.45, 0.45, [1, 0.25, 0]), legF = ik(hipF, fF, 0.45, 0.45, [1, 0.3, 0]);
    const torso = [{ c: lerp3(pelvis, neck, 0.3), r: 0.16 }, { c: lerp3(pelvis, neck, 0.75), r: 0.15 }];
    const armSph = []; [[shN, armN.knee], [armN.knee, handN]].forEach(([a, b]) => { for (let k = 0; k <= 3; k++) armSph.push({ c: lerp3(a, b, k / 3), r: 0.05 }); });
    const legSph = []; [[hipN, legN.knee], [hipF, legF.knee], [legN.knee, fN], [legF.knee, fF]].forEach(([a, b]) => { for (let k = 0; k <= 2; k++) legSph.push({ c: lerp3(a, b, k / 2), r: 0.075 }); });
    return { pelvis, neck, headC, shN, shF, handN, handF, elbN: armN.knee, elbF: armF.knee, hipN, hipF, kneeN: legN.knee, kneeF: legF.knee, footN: fN, footF: fF, torso, armSph, legSph, lean, z, sit };
  }
  function personRest(s, pg) {
    const fwd = [Math.cos(pg.lean), -Math.sin(pg.lean), 0], up = [Math.sin(pg.lean), Math.cos(pg.lean), 0];
    if (s.kind === 'hair') return { root: comb(pg.headC, 1, [1, 0, 0], -0.06 - 0.03 * s.q, UP, 0.08 - 0.12 * s.q, [0, 0, 1], (s.q - 0.5) * 0.12), dir: norm(comb(DOWN, 1, [1, 0, 0], -0.35)) };
    if (s.kind === 'scarf') return s.which === 0 ? { root: comb(pg.neck, 1, [1, 0, 0], 0.07, UP, -0.03, [0, 0, 1], 0.06), dir: norm(comb(DOWN, 1, fwd, 0.15)) } : { root: comb(pg.neck, 1, [1, 0, 0], -0.08, UP, -0.02, [0, 0, 1], -0.04), dir: norm(comb(DOWN, 1, [1, 0, 0], -0.2)) };
    if (s.kind === 'coat') return { root: comb(pg.pelvis, 1, [1, 0, 0], -0.11 + 0.11 * s.q, UP, 0.02, [0, 0, 1], (s.q - 1) * 0.06), dir: norm(comb(DOWN, 1, [1, 0, 0], -0.15 + 0.1 * s.q)) };
  }

  // ---------- the solver ----------
  const SUB = 4, DT = 1 / 24 / SUB, GRAV = [0, -9.81, 0];
  function stepStrand(s, t0, colliders) {
    const m = matOf(s);
    let k0 = m.k, c = m.c;
    if ((s.mat === 'fur' || s.mat === 'ruff') && m.kFear) { const fr = PRESET === 'generic' ? 0 : s._fear || 0; k0 = lerp(m.k, m.kFear, fr); c = lerp(m.c, m.cFear, fr); }
    const n = s.n, R0 = s.Rprev, R1 = s.R;
    const vR = R1.map((r, k) => mul(sub(r, R0[k]), 24));
    if (PRESET === 'none') { for (let k = 0; k < n; k++) { s.p[k] = R1[k].slice(); s.v[k] = vR[k]; } return; }
    for (let j = 1; j <= SUB; j++) {
      const a = j / SUB, t = t0 + a / 24;
      const R = R0.map((r, k) => lerp3(r, R1[k], a));
      const old = s.p.map(p => p.slice());
      s.p[0] = R[0]; s.v[0] = vR[0];
      for (let k = 1; k < n; k++) {
        const kk = k0 * lerp(1, s.kTip, (k - 1) / Math.max(1, n - 2));
        const p = s.p[k], v = s.v[k], w = wind(t, p);
        const acc = comb(sub(R[k], p), kk, sub(v, vR[k]), -c, GRAV, m.grav, sub(w, v), m.drag);
        if (j === 1 && k > 0) { const kk2 = s.kick; v[0] += kk2[0] * k / n; v[1] += kk2[1] * k / n; v[2] += kk2[2] * k / n; }
        v[0] += acc[0] * DT; v[1] += acc[1] * DT; v[2] += acc[2] * DT;
        s.p[k] = [p[0] + v[0] * DT, p[1] + v[1] * DT, p[2] + v[2] * DT];
      }
      // inextensible links (follow-the-leader)
      for (let k = 1; k < n; k++) { const d = sub(s.p[k], s.p[k - 1]), l = len(d) || 1e-9; s.p[k] = add(s.p[k - 1], mul(d, s.seg / l)); }
      // collisions (mask-selected)
      for (let k = 1; k < n; k++) {
        const p = s.p[k];
        if (s.mask.floor) { const fy = floorY(p[0], p[2]) + s.rad; if (p[1] < fy) { p[1] = fy; } }
        for (const grp in colliders) if (s.mask[grp]) for (const sp of colliders[grp]) {
          const d = sub(p, sp.c), l = len(d), r = sp.r + s.rad;
          if (l < r && l > 1e-9) { const q = add(sp.c, mul(d, r / l)); p[0] = q[0]; p[1] = q[1]; p[2] = q[2]; }
        }
        if (s.wall) { /* curtain strips stay on their side of nothing */ }
      }
      for (let k = 1; k < n; k++) {
        s.v[k] = mul(sub(s.p[k], old[k]), 1 / DT);
        const sp = len(s.v[k]), vmax = s.kind === 'curtain' ? 2.2 : 4; if (sp > vmax) s.v[k] = mul(s.v[k], vmax / sp);
        if (s.mask.floor && s.p[k][1] <= floorY(s.p[k][0], s.p[k][2]) + s.rad + 1e-4) { s.v[k][0] *= 0.7; s.v[k][2] *= 0.7; if (s.v[k][1] < 0) s.v[k][1] = 0; }
      }
    }
    s.kick = [0, 0, 0];
  }

  // ---------- door leaf: a driven hinge with spring-damper ----------
  const DOOR = { a: 0.62, w: 0 };
  function doorStep(t) {
    const target = t < 6.12 ? 0.62 : 1.78;
    for (let j = 0; j < SUB; j++) { const acc = 16 * (target - DOOR.a) - 4.2 * DOOR.w; DOOR.w += acc * DT; DOOR.a += DOOR.w * DT; }
    const h = PLACE.hinge;
    return { a: DOOR.a, w: DOOR.w, edge: [h[0] - PLACE.leafW * Math.sin(DOOR.a), 0, h[1] + PLACE.leafW * Math.cos(DOOR.a)], open: clamp((DOOR.a - 0.62) / (1.6 - 0.62), 0, 1) };
  }

  // ---------- frame driver ----------
  let I = -1, state = null;
  function init(score, preset) {
    SC = score; PRESET = preset || 'tuned';
    strands.length = 0; DOG.body = []; DOG.ruff = []; DOG.head = []; DOG.ears = []; DOG.earFeathers = []; DOG.tailFeathers = []; DOG.dewlap = []; DOG.legFeathers = [];
    PERSON.hair = []; PERSON.scarf = []; PERSON.coat = []; CURTAIN.length = 0; REEDS.length = 0; DOOR.a = 0.62; DOOR.w = 0;
    buildRig(); I = -1; state = null;
  }
  function restAll(P, g, Q, pg) {
    const dogOrder = [...DOG.body, ...DOG.ruff, ...DOG.head, ...DOG.dewlap, ...DOG.ears, DOG.tail, ...DOG.legFeathers];
    for (const s of dogOrder) { const r = dogRest(s, g, P); s.R = restShape(s, r.root, r.dir); s._fear = P.fear; }
    for (const s of CURTAIN) s.R = restShape(s, [PLACE.curtainX, PLACE.doorH - 0.02, s.z], DOWN);
    for (const s of REEDS) s.R = restShape(s, [s.x, floorY(s.x, s.z), s.z], norm([s.lean, 1, 0.1 * s.lean]));
    for (const s of [...PERSON.hair, ...PERSON.scarf, ...PERSON.coat]) { const r = personRest(s, pg); s.R = restShape(s, r.root, r.dir); }
  }
  function restHosted(P, g) { for (const s of [...DOG.earFeathers, ...DOG.tailFeathers]) { const r = dogRest(s, g, P); s.R = restShape(s, r.root, r.dir); } }
  function frame(i) {
    if (i !== I + 1) throw new Error('frames must be stepped in order; asked ' + i + ' after ' + I);
    I = i;
    const t = SC.frames[i].t, P = dogPrimary(i), Q = personPrimary(i);
    const dist = -(P.x - SC.frames[0].dog.x);   // signed distance travelled toward the door; feet follow it
    const g = dogGeom(P, dist);
    const door = doorStep(t);
    DRAFT = ss(t, 6.15, 6.5) * (1 - ss(t, 7.0, 8.2));
    const pg = personGeom(Q, door);
    restAll(P, g, Q, pg);
    const first = !state;
    if (first) for (const s of strands) { if (!s.R) continue; s.Rprev = s.R.map(r => r.slice()); s.p = s.R.map(r => r.slice()); s.v = s.R.map(() => [0, 0, 0]); }
    // ear flick: an impulse 60 ms after each soft-voice onset (the voice comes first)
    if (PRESET === 'tuned') for (const tv of SOFT) if (Math.abs(t - (tv + 0.06)) < 0.021) for (const e of DOG.ears) e.kick = comb(g.Uh, 4.2, g.md, 1.4, g.Lh, 1.2 * e.sg);
    const dogSph = [...g.cores, ...g.neck, g.head, ...g.muz];
    const col = { dog: dogSph, person: [...pg.armSph, ...pg.torso, { c: pg.headC, r: 0.12 }], phead: [{ c: pg.headC, r: 0.115 }, ...pg.torso], pbody: pg.torso, pleg: pg.legSph };
    const t0 = t - 1 / 24;
    const primaryLinks = [...DOG.body, ...DOG.ruff, ...DOG.head, ...DOG.dewlap, ...DOG.ears, DOG.tail, ...DOG.legFeathers, ...CURTAIN, ...REEDS, ...PERSON.hair, ...PERSON.scarf, ...PERSON.coat];
    for (const s of primaryLinks) if (!first) stepStrand(s, t0, col);
    restHosted(P, g);   // feathers hang from the ear and tail links as they now are
    if (first) for (const s of [...DOG.earFeathers, ...DOG.tailFeathers]) { s.Rprev = s.R.map(r => r.slice()); s.p = s.R.map(r => r.slice()); s.v = s.R.map(() => [0, 0, 0]); }
    else for (const s of [...DOG.earFeathers, ...DOG.tailFeathers]) stepStrand(s, t0, col);
    for (const s of strands) s.Rprev = s.R.map(r => r.slice());
    // energies for the sound (kinetic energy of the secondary nodes relative to their rest motion)
    const en = grp => { let e = 0; for (const s of grp) for (let k = 1; k < s.n; k++) { const v = s.v[k]; e += v[0] * v[0] + v[1] * v[1] + v[2] * v[2]; } return e; };
    const energy = { body: en(DOG.body), fur: en([...DOG.body, ...DOG.ruff, ...DOG.head, ...DOG.tailFeathers, ...DOG.earFeathers]), ears: en(DOG.ears), curtain: en(CURTAIN), reeds: en(REEDS), person: en([...PERSON.hair, ...PERSON.scarf, ...PERSON.coat]), door: Math.abs(door.w) };
    state = { i, t, P, Q, g, pg, door, energy, wind: gust(t), draft: DRAFT, paws: g.legs.map(l => l.paw[1]) };
    return state;
  }
  G.SCENE = { init, frame, PLACE, DOG, PERSON, CURTAIN, REEDS, MAT, GENERIC, SOFT, floorY, wind, gust, util: { clamp, lerp, ss, add, sub, mul, dot, len, norm, cross, lerp3, comb, rng, HD, LAT, DP, track } };
})(typeof window !== 'undefined' ? window : globalThis);
