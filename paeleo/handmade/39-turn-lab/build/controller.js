/* SCION 39 · Turn Lab — the ORIENTATION CONTROLLER.
   Score frame (paeleo/handmade/score/threshold-score.json) → a pose for every frame: which body drawing (orientation state),
   which head drawing (world head yaw), the neck and head pitch, lie, crouch, ears, tail, feet; plus the person and the door.
   TURN CHOREOGRAPHY: each turn is a short list of keys. The head leads (attention), the body follows a view at a time, the feet
   step at the swaps. Body views are discrete (substitution); the head yaw is continuous but drawn from the nearest head view.
   Time base: score frames, 24 fps, t = i / 24. Mapping: lateral u (m, door centre = 0) = score x − 0.59; the dog walks a line
   0.55 m out from the wall. Runs in node (writes build/cache/plan.json) and in the page. */
(function (G) {
  'use strict';
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smooth = t => { t = clamp(t); return t * t * (3 - 2 * t); };
  const X0 = 0.39;                    // score x that sits at the door centre (the sill, where it lies)
  const DEPTH = 0.55;                 // the dog's walking line, metres in front of the wall

  // ---- turn choreography (the turn animator's table) ---------------------------------------------------------------
  // body view: held until the next key (substitution, never in-between squash)
  const BODY_KEYS = [[0, 0], [3.50, 45], [3.58, 90], [3.71, 135], [8.10, 90], [8.22, 45], [8.34, 0], [23.10, 45]];
  // head yaw (world, deg): piecewise linear; the drawing is the nearest of the head views
  const HEAD_KEYS = [[0, 0], [3.42, 0], [3.46, 45], [3.52, 135], [3.62, 180], [7.46, 180], [7.50, 135], [7.54, 90],
    [7.58, 45], [7.64, 0], [22.95, 0], [23.06, 45], [24.72, 45], [24.86, 0], [26.55, 0], [26.65, 45], [26.76, 90], [28.24, 90], [28.36, 45],
    [28.48, 0], [40, 0]];
  // chin on the paws (0 … 1)
  const REST_KEYS = [[0, 0], [5.55, 0], [6.15, 1], [7.46, 1], [7.60, 0], [25.30, 0], [26.05, 1], [26.46, 1], [26.66, 0], [28.46, 0],
    [29.20, 1], [40, 1]];
  const BLINKS = [0.72, 2.95, 6.60, 9.35, 12.10, 13.85, 17.40, 20.90, 25.15, 29.70, 31.10];
  const EAR_FLICKS = [[6.26, 1], [7.40, 0.8], [10.42, 0.7], [26.42, 1]];
  const LEGIDS = ['hf', 'ff', 'hn', 'fn'];
  const GAIT = { hf: 0, ff: 0.25, hn: 0.5, fn: 0.75 };
  const NEUTRAL = { hf: [0.33, -0.09], ff: [-0.29, -0.08], hn: [0.33, 0.09], fn: [-0.29, 0.08] };
  const STRIDE = 0.55, DUTY = 0.70;

  function keyStep(keys, t) { let v = keys[0][1]; for (const k of keys) if (t >= k[0]) v = k[1]; return v; }
  function keyLin(keys, t) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 0; i < keys.length - 1; i++) { const a = keys[i], b = keys[i + 1]; if (t <= b[0]) return lerp(a[1], b[1], (t - a[0]) / (b[0] - a[0] || 1)); }
    return keys[keys.length - 1][1];
  }
  function pulse(t, t0, dur) { const u = (t - t0) / dur; return u < 0 || u > 1 ? 0 : Math.sin(Math.PI * u); }

  function feetAt(s, moving) {
    const feet = {}, lift = {};
    for (const id of LEGIDS) {
      const o = GAIT[id], c = -NEUTRAL[id][0];      // neutral, in forward coordinates
      const q = s / STRIDE + o, n = Math.floor(q), f = q - n;
      const Wn = (n - o) * STRIDE + DUTY * STRIDE / 2 + c;
      let W, lf = 0;
      if (f < DUTY) W = Wn;
      else { const p = (f - DUTY) / (1 - DUTY); W = lerp(Wn, Wn + STRIDE, smooth(p)); lf = Math.sin(Math.PI * p) * moving; }
      feet[id] = [-(W - s), 0, NEUTRAL[id][1]];
      lift[id] = lf;
    }
    return { feet, lift };
  }

  function plan(score) {
    const fr = score.frames, out = [];
    let wagPh = 0;
    for (let i = 0; i < fr.length; i++) {
      const f = fr[i], t = f.t, a = f.dog.act;
      const xs = f.dog.x, u = xs - X0;
      const xp = fr[Math.max(0, i - 1)].dog.x, xn = fr[Math.min(fr.length - 1, i + 1)].dog.x;
      const v = (xn - xp) / (2 / 24);
      const moving = clamp(Math.abs(v) / 0.12);
      const s = -u;
      // orientation
      const body = keyStep(BODY_KEYS, t);
      let headYaw = keyLin(HEAD_KEYS, t);
      // head: neck angle alpha and pitch beta from the score's head, rest, look — and the approach held low
      const h = clamp(a.head, 0, 1.2);
      let alpha = lerp(-8, 58, clamp(h)), beta = lerp(-22, 2, clamp(h));
      const appr = smooth((t - 14.6) / 0.5) * (1 - smooth((t - 23.2) / 0.5));
      alpha = lerp(alpha, -7, appr); beta = lerp(beta, -16, appr);
      const lying = a.lie;
      if (lying > 0.5 && t > 23.5) { alpha = lerp(alpha, 34, smooth((t - 24.0) / 0.4)); beta = lerp(beta, -4, smooth((t - 24.0) / 0.4)); }
      if (t > 7.46 && t < 8.6) { alpha = Math.max(alpha, lerp(10, 40, smooth((t - 7.46) / 0.2))); beta = Math.max(beta, -8); }
      const look = smooth((t - 26.5) / 0.25) * (1 - smooth((t - 28.2) / 0.25));
      alpha = lerp(alpha, 50, look); beta = lerp(beta, 8, look);
      const rest = keyLin(REST_KEYS, t);
      const restA = lying > 0.5 ? -30 : -10;
      alpha = lerp(alpha, restA, rest); beta = lerp(beta, -6, rest);
      // ears: score ear, pricked when looking in, flicks when something is heard
      let ear = clamp(a.ear, 0, 1); ear = lerp(ear, 1, look);
      let earFlick = 0; for (const [t0, k] of EAR_FLICKS) earFlick = Math.max(earFlick, k * pulse(t, t0, 0.35));
      let blink = 0; for (const b of BLINKS) blink = Math.max(blink, pulse(t, b, 0.17));
      // crouch only reads in the profile drawing; in the rear views it is halved
      const crouch = a.crouch * (body === 0 || body === 180 ? 1 : 0.5) * (1 - lying);
      // tail
      wagPh += 2 * Math.PI * 2.6 / 24;
      const tail = a.tail, wag = a.wag;
      // feet
      const ft = feetAt(s, moving);
      // turn steps: the feet scrabble at each body swap (a turn on the spot is made of steps)
      for (const [kt] of BODY_KEYS.slice(1)) {
        if (Math.abs(t - kt) < 0.2) {
          ft.lift.fn = Math.max(ft.lift.fn, 0.55 * pulse(t, kt - 0.07, 0.15)); ft.lift.hf = Math.max(ft.lift.hf, 0.45 * pulse(t, kt - 0.07, 0.15));
          ft.lift.ff = Math.max(ft.lift.ff, 0.55 * pulse(t, kt + 0.02, 0.15)); ft.lift.hn = Math.max(ft.lift.hn, 0.45 * pulse(t, kt + 0.02, 0.15));
        }
      }
      if (lying > 0.02) for (const id of LEGIDS) ft.lift[id] *= (1 - lying);
      const bob = -0.012 * Math.abs(Math.sin(2 * Math.PI * s / STRIDE)) * moving;
      const breath = 0.006 * Math.sin(2 * Math.PI * t / 2.9) * lying + 0.003 * Math.sin(2 * Math.PI * t / 1.7) * (1 - lying) * (1 - moving);
      // drift onto the door centre during the last turn so it lies square in the doorway
      const uDog = u;
      const depth = lerp(DEPTH, 0.32, smooth((t - 22.9) / 0.9));
      const dog = { u: uDog, depth, body, headYaw, alpha, beta, ear, earFlick, blink, lie: lying, crouch, tail, wag, wagPh,
        feet: ft.feet, lift: ft.lift, bob, breath, state: f.dog.state, x_score: xs, moving };
      // ---- the person
      const P = personAt(t, f);
      // ---- the door: ajar until 6.2, then swings in
      const doorA = lerp(25, 100, smooth((t - 6.18) / 0.6));
      const light = lerp(0.18, 1, smooth((t - 6.18) / 0.8));
      out.push({ i, t, dog, person: P, door: { angle: doorA, light }, voice: f.person.voice, score: { x: xs, state: f.dog.state } });
    }
    return out;
  }

  // the person: stands in the doorway, calls; calls and reaches; steps aside and sits; pushes the door; offers a hand low
  function personAt(t, f) {
    const P = { u: -0.20, depth: 0.06, view: 'R', sit: 0, reach: 0, push: 0, low: 0, lean: 0, walk: 0, step: 0 };
    P.lean = 0.25 * pulse(t, 0.95, 0.9) + 0.35 * (smooth((t - 3.35) / 0.25) * (1 - smooth((t - 4.5) / 0.4)));
    P.reach = smooth((t - 3.38) / 0.3) * (1 - smooth((t - 4.45) / 0.35));
    if (t >= 4.9 && t < 5.0) P.view = 'F';
    if (t >= 5.0 && t < 5.45) { P.view = 'L'; P.walk = (t - 5.0) / 0.45; P.u = lerp(-0.20, -1.02, smooth(P.walk)); P.step = P.walk; }
    if (t >= 5.45 && t < 5.55) { P.view = 'F'; P.u = -1.02; }
    if (t >= 5.45) { P.u = -1.02; P.depth = lerp(0.06, 0.30, smooth((t - 5.0) / 0.5)); }
    else if (t >= 5.0) P.depth = lerp(0.06, 0.30, smooth((t - 5.0) / 0.5));
    if (t >= 5.55) { P.view = 'R'; P.sit = smooth((t - 5.55) / 0.45); }
    P.push = pulse(t, 5.95, 0.7);
    P.low = smooth((t - 6.6) / 0.45);
    P.lean += 0.12 * (pulse(t, 7.35, 1.6) + pulse(t, 10.35, 1.4) + pulse(t, 26.35, 1.2));
    return P;
  }

  const API = { plan, personAt, BODY_KEYS, HEAD_KEYS, REST_KEYS, BLINKS, X0, DEPTH, STRIDE };
  G.CONTROLLER = API;
  if (typeof module !== 'undefined') module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);

if (typeof require !== 'undefined' && typeof module !== 'undefined' && require.main === module) {
  const fs = require('fs'), path = require('path');
  const root = path.resolve(__dirname, '../../../..');
  const score = JSON.parse(fs.readFileSync(path.join(root, 'paeleo/handmade/score/threshold-score.json')));
  const p = module.exports.plan(score);
  fs.mkdirSync(path.join(__dirname, 'cache'), { recursive: true });
  fs.writeFileSync(path.join(__dirname, 'cache/plan.json'), JSON.stringify(p));
  console.log('plan', p.length, 'frames');
}
