// SCION 41 · the threshold scene as primary poses + secondary dynamics.  node build/scene.js [preset] [out.json]
// preset: tuned (the film) | none (no secondary motion: every part rides its pose) | loose (damping x0.35)
// Primary motion comes from the PAELEO score (the dog's x, state and acting intentions) plus this swarm's own timing of
// the turns, head and feet (the "primary pose impulses"). Everything else is solved: ears, tail, coat, collar tag,
// scarf, door leaf, shrub. Output: every frame's 3D draw list, camera, sound events and measured quantities.
'use strict';
const D = require('./dynamics.js'); const { V } = D; const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '../../../..');
const SCORE = JSON.parse(fs.readFileSync(path.join(ROOT, 'paeleo/handmade/score/threshold-score.json'), 'utf8'));
const FR = SCORE.frames, N = FR.length, DT = 1 / 24, SUB = 8, PI = Math.PI;
const PRESET = process.argv[2] || 'tuned';
const OUT = process.argv[3] || path.join(__dirname, 'cache', PRESET === 'tuned' ? 'sim.json' : `sim-${PRESET}.json`);
if (PRESET !== 'tuned') for (const k of Object.keys(D.MATERIALS)) { const m = D.MATERIALS[k];
  if (PRESET === 'none' && k !== 'wood') { m.f = Infinity; }
  if (PRESET === 'loose') { m.zeta *= 0.35; m.drag *= 0.35; } }

// ---------- helpers ----------
const clamp = (x, a, b) => Math.max(a, Math.min(b, x)), lerp = (a, b, t) => a + (b - a) * t;
const sm = x => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); }, seg = (t, a, b) => sm((t - a) / (b - a));
const table = (tb, x) => { if (x <= tb[0][0]) return tb[0][1]; for (let i = 1; i < tb.length; i++) if (x <= tb[i][0]) return lerp(tb[i - 1][1], tb[i][1], (x - tb[i - 1][0]) / (tb[i][0] - tb[i - 1][0])); return tb[tb.length - 1][1]; };
const r4 = x => Math.round(x * 1e4) / 1e4, P3 = p => [r4(p[0]), r4(p[1]), r4(p[2])];
const act = i => FR[clamp(i, 0, N - 1)].dog.act;

// ---------- the world (metres) ----------
const WORLD = { wallIn: 0.30, wallOut: 0.50, open: [-0.46, 0.46], lintel: 2.05, sill: [0.26, 0.66, 0.025], hinge: [0.31, 0, -0.46], hingeDir: 1, leaf: 0.90, leafStop: 2.90,
  porchEnd: 4.9, railZ: -1.32, lamp: [-1.05, 2.15, -0.1], shrub: [4.74, 0, -0.86], dogZ: 0.0 };

// ---------- the dog's own timing (primary), anchored to the score's choices ----------
// heading θ: F = (cos θ, 0, sin θ). θ = π faces the door (−X). The turns pass through θ = π/2 (facing the camera),
// so every frame of a turn is a dog seen from the front-quarter, never an edge-on card.
// The refusal turns away from the viewer (θ: π → 3π/2 → 2π): its rump and back come round to us as it turns its back
// on the door. The turn back to look goes the other way round, through the camera side (2π → 5π/2 → 3π), so its face
// comes round first. Angles are unwrapped (2π ≡ 0, 3π ≡ π).
function bodyYaw(t) {
  if (t < 3.417) return PI;
  if (t < 3.9) return PI * (1 + seg(t, 3.417, 3.9));
  if (t < 7.86) return 2 * PI;
  if (t < 8.62) return 2 * PI + PI * seg(t, 7.86, 8.62);
  return 3 * PI;
}
function headHeading(t, th) { // world heading of the head: it leads the body, and at 7.46 it comes round first
  if (t >= 3.3 && t < 3.95) return bodyYaw(t + 0.08);
  if (t >= 7.458 && t < 8.75) return Math.max(th, 2 * PI + lerp(0, 2.85, seg(t, 7.458, 7.66)));
  let y = th;
  if (t > 24.4) y += -1.25 * seg(t, 24.6, 25.4) * (1 - seg(t, 26.42, 26.85)) + 0.18 * seg(t, 26.5, 26.9) * (1 - seg(t, 28.3, 28.9)); // settles looking out along the porch, then turns in through the doorway, past the person
  return y;
}
function headRoll(t) { return 0.22 * seg(t, 10.45, 10.8) * (1 - seg(t, 11.5, 12.1)) + 0.12 * seg(t, 7.6, 7.9) * (1 - seg(t, 8.3, 8.8)); }

// ---------- primary pose of the dog: torso, neck, head frame, leg roots, ideal footholds ----------
function frameOf(th) { const F = [Math.cos(th), 0, Math.sin(th)], L = [F[2], 0, -F[0]]; return { F, L }; }
function bodyPose(i) {
  const t = i * DT, a = act(i), th = bodyYaw(t), { F, L } = frameOf(th), x = FR[i].dog.x;
  const root = [x, 0, WORLD.dogZ];
  const lb = sm((a.lie - 0.04) / 0.92), c = a.crouch;
  const pelvisC = lerp(0.47 - 0.12 * c, 0.165, lb), withersC = lerp(0.47 - 0.07 * c, 0.19, lb);
  const at = (u, y, w = 0) => V.add(root, V.add(V.mul(F, u), V.add([0, y, 0], V.mul(L, w))));
  const yAt = u => lerp(pelvisC, withersC, clamp((u + 0.30) / 0.52, 0, 1));
  const breath = 1 + 0.012 * Math.sin(2 * PI * t / 2.3) * (lb > 0.5 ? 1.4 : 1);
  const torso = [[-0.30, 0.00, 0.118], [-0.165, -0.01, 0.124], [0, -0.015, 0.135 * breath], [0.15, -0.01, 0.148 * breath], [0.235, -0.085, 0.118], [0.245, 0.04, 0.108]]
    .map(([u, dy, r]) => ({ c: at(u, yAt(u) + (dy < -0.05 ? lerp(dy, -0.065, lb) : dy)), r }));
  const neckBase = at(0.27, withersC + 0.075);
  return { t, a, th, F, L, root, lb, c, pelvisC, withersC, at, torso, neckBase, x };
}
function headPose(B) {
  const { t, a, th, lb } = B; const rest = a.rest * lb; let h = a.head;
  if (t > 14.3 && t < 15.3) h = Math.min(h, act(Math.round(t / DT) + 9).head); // the head goes down as it decides to come
  const hh = headHeading(t, th), rel = hh - th;
  let dy = table([[0, -0.33], [0.2, -0.27], [0.45, -0.13], [0.7, 0.15], [0.9, 0.26], [1.25, 0.32]], h);
  let fw = table([[0, 0.23], [0.45, 0.25], [0.9, 0.17], [1.25, 0.15]], h);
  let pitch = table([[0, -0.9], [0.45, -0.55], [0.9, -0.16], [1.25, 0.12]], h);
  const lookUp = 0.38 * Math.max(0, Math.min(1, (h - 0.9) / 0.3)) * lb; // lying, the raised head looks up and in, over her head
  const ly = lerp(table([[0.2, 0.31], [0.45, 0.37], [0.7, 0.44], [1.25, 0.56]], h), 0.108, rest);
  const lfw = lerp(0.17, 0.29, rest), lp = lerp(table([[0.2, -0.25], [0.7, -0.1], [1.25, 0.1]], h), -0.04, rest);
  const yAbs = lerp(B.withersC + dy, ly, lb); fw = lerp(fw, lfw, lb); pitch = lerp(pitch, lp, lb) + lookUp * (1 - rest);
  // neck carries the head round: offset from the neck base rotated by most of the relative yaw
  const ry = rel * 0.78, Fh = frameOf(th + ry);
  const N = B.neckBase; let H = V.add([N[0], 0, N[2]], V.add(V.mul(Fh.F, fw), [0, yAbs, 0]));
  H = V.add(N, V.mul(V.norm(V.sub(H, N)), NECK)); // the neck has one length: the head rotates about its base, it never stretches
  const hf = frameOf(hh), roll = headRoll(t);
  const fwd = V.norm(V.add(V.mul(hf.F, Math.cos(pitch)), [0, Math.sin(pitch), 0]));
  let up = V.norm(V.sub([0, 1, 0], V.mul(fwd, fwd[1]))), side = V.cross(up, fwd); // side = head's left
  up = V.norm(V.add(V.mul(up, Math.cos(roll)), V.mul(side, Math.sin(roll)))); side = V.cross(up, fwd);
  return { H, fwd, up, side, hh, rel, pitch };
}

// ideal footholds in the body frame (u forward, w left): standing, crouched (hind gathered under), lying (sphinx)
const NECK = 0.25;
const FEET = [{ n: 'LF', fore: 1, s: 1 }, { n: 'RF', fore: 1, s: -1 }, { n: 'LH', fore: 0, s: 1 }, { n: 'RH', fore: 0, s: -1 }];
function idealFoot(B, k) {
  const f = FEET[k], c = B.c;
  const u = f.fore ? 0.215 + 0.03 * c : -0.30 + 0.06 * c, w = 0.085 * f.s;
  return V.add(B.root, V.add(V.mul(B.F, u), V.mul(B.L, w)));
}
function lyingFoot(B, k) { const f = FEET[k]; return f.fore ? B.at(0.51, 0.03, 0.07 * f.s) : B.at(-0.12, 0.03, 0.15 * f.s); }

// ---------- 2-bone IK ----------
function ik2(A, C, l1, l2, pole) {
  let d = V.sub(C, A), L = V.len(d); const mx = l1 + l2 - 1e-4; if (L > mx) { C = V.add(A, V.mul(d, mx / L)); d = V.sub(C, A); L = mx; }
  L = Math.max(L, Math.abs(l1 - l2) + 1e-3);
  const a = (l1 * l1 - l2 * l2 + L * L) / (2 * L), h = Math.sqrt(Math.max(0, l1 * l1 - a * a)), dn = V.mul(d, 1 / L);
  const p = V.norm(V.sub(pole, V.mul(dn, V.dot(pole, dn))));
  return { B: V.add(A, V.add(V.mul(dn, a), V.mul(p, h))), C };
}

// ---------- precompute the primary body for all frames, then step the feet (no foot slides while planted) ----------
const BODY = []; for (let i = 0; i < N; i++) BODY.push(bodyPose(i));
const IDEAL = BODY.map(B => FEET.map((f, k) => idealFoot(B, k)));
const moving = i => { const a = FR[clamp(i, 0, N - 1)]; return Math.abs(a.dog.v) > 0.02 || Math.abs(bodyYaw((i + 1) * DT) - bodyYaw(i * DT)) > 1e-3; };
const feet = FEET.map((f, k) => ({ P: IDEAL[0][k].slice(), swing: null, last: -9 }));
const FOOT = [], EVENTS = [];
for (let i = 0; i < N; i++) {
  const t = i * DT, B = BODY[i], out = [];
  for (let k = 0; k < 4; k++) {
    const ft = feet[k], partner = feet[k ^ 1]; // k^1: the other foot of the same girdle
    if (ft.swing && t >= ft.swing.t1) { ft.P = ft.swing.B; ft.swing = null; ft.last = t; EVENTS.push({ t, tag: 'paw', k, speed: ft.speed || 0.3, x: ft.P[0] }); }
    if (!ft.swing && B.lb < 0.3) {
      const mv = moving(i) || moving(i + 3), thr = mv ? (Math.abs(FR[i].dog.v) > 0.5 ? 0.15 : 0.12) : 0.02, d = V.len(V.sub(IDEAL[i][k], ft.P));
      const swinging = feet.filter(q => q.swing).length;
      if (d > thr && !partner.swing && swinging < 2 && t - ft.last > 0.1) {
        const Tsw = Math.abs(FR[i].dog.v) > 0.5 ? 0.17 : (mv ? 0.22 : 0.26), j = clamp(Math.round(i + (Tsw + (mv ? 0.2 : 0)) / DT), 0, N - 1);
        ft.swing = { A: ft.P.slice(), B: IDEAL[j][k].slice(), t0: t, t1: t + Tsw }; ft.speed = V.len(V.sub(ft.swing.B, ft.P)) / Tsw;
      }
    }
    let p = ft.P;
    if (ft.swing) { const s = clamp((t - ft.swing.t0) / (ft.swing.t1 - ft.swing.t0), 0, 1), e = sm(s); p = V.add(V.lerp(ft.swing.A, ft.swing.B, e), [0, 0.065 * Math.sin(PI * s), 0]); }
    if (B.lb > 0) { p = V.lerp(p, lyingFoot(B, k), B.lb); if (B.lb > 0.3) { ft.P = IDEAL[i][k].slice(); ft.swing = null; } }
    out.push({ p, planted: !ft.swing && B.lb < 0.02 });
  }
  FOOT.push(out);
}

// ---------- the dog's full primary skeleton for frame i ----------
function dogSkeleton(i) {
  const B = BODY[i], Hp = headPose(B), { F, L, at } = B;
  const legs = FEET.map((f, k) => {
    const paw = FOOT[i][k].p, down = [0, -1, 0];
    if (f.fore) {
      const S = at(0.205, B.withersC - 0.075, 0.075 * f.s), pole = V.norm(V.add(V.mul(F, -1), V.mul(down, 0.3)));
      const wrist = V.add(paw, [0, 0.055, 0]); let { B: el } = ik2(S, wrist, 0.18, 0.162, pole);
      let j2 = wrist;
      if (B.lb > 0) { el = V.lerp(el, at(0.17, 0.045, 0.085 * f.s), B.lb); j2 = V.lerp(wrist, at(0.43, 0.035, 0.07 * f.s), B.lb); }
      return { fore: 1, s: f.s, root: S, j1: el, j2, paw };
    }
    const Hj = at(-0.285, B.pelvisC - 0.05, 0.078 * f.s);
    const hock = V.lerp(V.add(paw, V.add([0, 0.125, 0], V.mul(F, -0.012))), V.add(paw, V.add([0, 0.03, 0], V.mul(F, -0.15))), B.lb);
    const pole = V.norm(V.add(V.mul(F, 1), V.add(V.mul(L, 0.6 * f.s * B.lb), [0, 0.2, 0])));
    let { B: st } = ik2(Hj, hock, 0.16, 0.152, pole);
    if (B.lb > 0) st = V.lerp(st, at(-0.08, 0.11, 0.165 * f.s), B.lb);
    return { fore: 0, s: f.s, root: Hj, j1: st, j2: hock, paw };
  });
  return { B, Hp, legs };
}

// ---------- the person: primary poses (keyframed acting) ----------
const PF = i => FR[clamp(i, 0, N - 1)].person;
const SEAT = { hip: [-0.95, 0.14, -0.12], heading: 0.18 };
const DOORWAY = { hip: [-0.20, 0.93, 0.12], heading: 0.0 };
function personPose(i) {
  const t = i * DT, p = PF(i);
  const walk = seg(t, 4.55, 5.25), sit = sm(seg(t, 4.98, 5.55)), // she sits first, then opens the door
    headingP = lerp(DOORWAY.heading, SEAT.heading, seg(t, 5.0, 5.8));
  const { F, L } = frameOf(headingP);
  // feet: planted in the doorway, three steps out and aside, then planted in front of the seat
  const seatFeet = s => V.add([SEAT.hip[0], 0, SEAT.hip[2]], V.add(V.mul(frameOf(SEAT.heading).F, 0.56), V.mul(frameOf(SEAT.heading).L, 0.12 * s)));
  const doorFeet = s => V.add([DOORWAY.hip[0], 0, DOORWAY.hip[2]], V.mul([0, 0, -1], 0.11 * s));
  const steps = [[4.55, 4.78, 1], [4.72, 4.96, -1], [4.9, 5.12, 1], [5.05, 5.28, -1]];
  const footAt = s => { // s: +1 left (far), −1 right (near)
    let p = doorFeet(s); const mid = V.lerp(doorFeet(s), seatFeet(s), 0.5);
    const mine = steps.filter(q => q[2] === s);
    const a1 = seg(t, mine[0][0], mine[0][1]), a2 = seg(t, mine[1][0], mine[1][1]);
    p = V.lerp(V.lerp(doorFeet(s), mid, a1), seatFeet(s), a2);
    const lift = Math.max(Math.sin(PI * clamp((t - mine[0][0]) / (mine[0][1] - mine[0][0]), 0, 1)), Math.sin(PI * clamp((t - mine[1][0]) / (mine[1][1] - mine[1][0]), 0, 1)));
    return V.add(p, [0, 0.09 * lift, 0]);
  };
  const fl = footAt(1), fr = footAt(-1);
  // hips: over the feet while standing and walking, then down and back to the wall
  const standHip = V.add(V.lerp(fl, fr, 0.5), [0, 0.93, 0]);
  let hip = [standHip[0], 0.93 - 0.02 * Math.abs(Math.sin(PI * 2 * walk)), standHip[2]];
  if (t < 4.62) hip = DOORWAY.hip.slice();
  hip = V.add(hip, [0.16 * p.reach, -0.03 * p.reach, 0]);
  hip = V.lerp(hip, SEAT.hip, sit);
  // upper body: lean toward the dog when calling, more when reaching; toward the door edge when pushing it
  const reach = p.reach, call = (t > 0.95 && t < 2.3 ? seg(t, 0.95, 1.15) * (1 - seg(t, 2.0, 2.3)) : 0);
  const push = seg(t, 5.36, 5.6) * (1 - seg(t, 5.72, 6.05)); // seated, she reaches out and pushes the door open
  const low = p.low;
  let lean = 0.10 * call + 0.30 * reach - 0.05 * sit + 0.34 * low * sit + 0.12 * push;
  let twist = 0.3 * push; // shoulders toward the door's edge
  const fwd = V.norm(V.add(V.mul(frameOf(headingP + twist * 0.5).F, Math.sin(lean)), [0, Math.cos(lean), 0])); // spine axis
  const Fs = frameOf(headingP + twist * 0.5).F, Ls = frameOf(headingP + twist * 0.5).L;
  const chest = V.add(hip, V.mul(fwd, 0.36)), neck = V.add(hip, V.mul(fwd, 0.53)), head = V.add(V.add(hip, V.mul(fwd, 0.665)), V.mul(Fs, 0.025));
  const shR = V.add(V.add(hip, V.mul(fwd, 0.49)), V.mul(Ls, -0.185)), shL = V.add(V.add(hip, V.mul(fwd, 0.49)), V.mul(Ls, 0.185));
  // hands: rest at sides / beckon / reach to the dog / push the door edge / offer low
  const restR = V.add(shR, [0, -0.62, 0]), restL = V.add(shL, [0, -0.62, 0]);
  const beckon = call * (0.5 + 0.5 * Math.sin(2 * PI * 1.8 * (t - 1.0)));
  let handR = V.lerp(restR, V.add(shR, V.add(V.mul(F, 0.34), [0, -0.12 + 0.12 * beckon, 0])), call);
  handR = V.lerp(handR, V.add(shR, V.add(V.mul(F, 0.62), [0, -0.12, 0.05])), reach);
  const leafF = doorEdge(DOOR_A[i] ?? 1.0, 0.85, 0.55);
  const lowHand = [-0.50, 0.15, -0.02];
  handR = V.lerp(handR, lowHand, low);
  let handL = V.lerp(restL, V.add(hip, V.add(V.mul(F, 0.30), V.add(V.mul(L, 0.24), [0, 0.07, 0]))), sit); // on the far knee
  handR = V.lerp(handR, leafF, push * (1 - low));
  // knees: standing straight, walking bend, sitting up
  const legPole = V.norm(V.add(F, [0, 0.35 * sit, 0]));
  const hipL = V.add(hip, V.mul(L, 0.1)), hipR = V.add(hip, V.mul(L, -0.1));
  let kL = ik2(hipL, fl, 0.46, 0.46, legPole).B, kR = ik2(hipR, fr, 0.46, 0.46, legPole).B;
  // sitting cross-legged on the floor: knees out and low, feet tucked in front of the hips
  const xs = sm((sit - 0.55) / 0.45); let flx = fl, frx = fr;
  if (xs > 0) { const Fq = frameOf(SEAT.heading); kL = V.lerp(kL, V.add(hip, V.add(V.mul(Fq.F, 0.36), V.add(V.mul(Fq.L, 0.27), [0, -0.05, 0]))), xs); kR = V.lerp(kR, V.add(hip, V.add(V.mul(Fq.F, 0.36), V.add(V.mul(Fq.L, -0.27), [0, -0.05, 0]))), xs);
    flx = V.lerp(fl, V.add([hip[0], 0.04, hip[2]], V.add(V.mul(Fq.F, 0.30), V.mul(Fq.L, -0.10))), xs); frx = V.lerp(fr, V.add([hip[0], 0.04, hip[2]], V.add(V.mul(Fq.F, 0.24), V.mul(Fq.L, 0.10))), xs); }
  const armPole = V.norm(V.add([0, -1, 0], V.mul(F, -0.5)));
  const eR = ik2(shR, handR, 0.31, 0.32, armPole), eL = ik2(shL, handL, 0.31, 0.32, armPole);
  const gaze = V.norm(V.sub(dogHeadAt(i), head));
  return { hip, chest, neck, head, shR, shL, elR: eR.B, handR: eR.C, elL: eL.B, handL: eL.C, hipL, hipR, kL, kR, fl: flx, fr: frx, F, L, Fs, fwd, gaze, sit, lean };
}
let DOGHEAD = []; const dogHeadAt = i => DOGHEAD[clamp(i, 0, N - 1)] || [3, 0.6, 0];
function doorEdge(a, u = 1, y = 0.98) { const h = WORLD.hinge; return [h[0] - WORLD.leaf * u * Math.sin(a), y, h[2] + WORLD.hingeDir * WORLD.leaf * u * Math.cos(a)]; }

// ---------- the voice (shared with the sound): syllables, loudness, mouth ----------
const VOICE = [
  { t: 1.04, level: 'call', text: 'Come here!', syl: [['k', 'ah', 0.20, 0.9], ['h', 'ih', 0.42, 1.0]] },
  { t: 1.78, level: 'call', text: 'come on!', syl: [['k', 'ah', 0.16, 0.8], ['', 'aw', 0.30, 0.85]] },
  { t: 3.44, level: 'call', text: 'Come HERE!', syl: [['k', 'ah', 0.18, 1.0], ['h', 'ih', 0.50, 1.1]] },
  { t: 7.48, level: 'soft', text: "it's all right", syl: [['', 'ih', 0.16, 0.55], ['', 'aw', 0.26, 0.6], ['r', 'ay', 0.42, 0.5]] },
  { t: 10.48, level: 'soft', text: "it's all right", syl: [['', 'ih', 0.15, 0.5], ['', 'aw', 0.26, 0.55], ['r', 'ay', 0.46, 0.45]] },
  { t: 26.45, level: 'soft', text: 'come in', syl: [['k', 'ah', 0.20, 0.55], ['', 'ih', 0.44, 0.5]] },
];
function mouthAt(t) { let m = 0; for (const v of VOICE) { let s = v.t; for (const [c, vw, d, amp] of v.syl) { const g = clamp((t - s - 0.03) / d, 0, 1); if (g > 0 && g < 1) m = Math.max(m, Math.sin(PI * g) * (v.level === 'call' ? 1 : 0.45) * amp); s += d + 0.04; } } return m; }

// ---------- door leaf (wood): hinge with friction and a doorstop; the person's hand gives the impulses ----------
const DOOR_A = [];
function runDoor(J) { const d = new D.Hinge({ I: 3.9, k: 0, c: 0.5, friction: 0.9, min: 0.0, max: WORLD.leafStop, restitution: 0.06, tag: 'door' }); d.a = 1.0; const A = [];
  for (let i = 0; i < N; i++) { if (i === Math.round(5.62 / DT)) d.impulse(J); d.step(DT, SUB, i * DT); A.push(d.a); } return { d, A }; }
let lo = 0.5, hi = 40; for (let it = 0; it < 40; it++) { const m = (lo + hi) / 2, s0 = runDoor(m).d.events.find(e => e.tag === 'door-stop'); if (!s0 || s0.t > 6.2) lo = m; else hi = m; }
const DOORJ = (lo + hi) / 2, door = runDoor(DOORJ).d; DOOR_A.push(...runDoor(DOORJ).A);
EVENTS.push(...door.events);

// ---------- run the secondary systems frame by frame ----------
const M = D.MATERIALS;
const earL = new D.Chain('ear', 3, { r: [0.008, 0.008, 0.008], sag: 0.25, tipSoft: 0.35 }), earR = new D.Chain('ear', 3, { r: [0.008, 0.008, 0.008], sag: 0.25, tipSoft: 0.35 });
const tail = new D.Chain('hair', 7, { r: Array(7).fill(0.026), sag: 0.35, tipSoft: 0.6 });
const tag = new D.Chain('metal', 2, { r: [0.006, 0.009], sag: 1, stiff: [0, 0.35] });
const coat = { ruff: new D.MassProxy('fur', 2.2), belly: new D.MassProxy('fur', 2.6), breech: new D.MassProxy('fur', 2.4), neck: new D.MassProxy('fur', 0.8) };
const scarfA = new D.Chain('cloth', 8, { r: Array(8).fill(0.03), sag: 1.0, tipSoft: 0.75 }), scarfB = new D.Chain('cloth', 7, { r: Array(7).fill(0.03), sag: 1.0, tipSoft: 0.75 });
// shrub: arching stems from a planter in the back corner, leaning over the porch where the dog backs up
const STEMS = [[0.00, [4.36, 0.60, -0.16]], [0.08, [4.47, 0.76, -0.30]], [-0.07, [4.55, 0.50, -0.10]], [0.12, [4.62, 0.86, -0.44]], [-0.12, [4.40, 0.44, -0.30]], [0.05, [4.70, 0.68, -0.22]]]
  .map(([dz, tip]) => { const base = V.add(WORLD.shrub, [0.02, 0.2, dz]); const ctl = V.add(V.lerp(base, tip, 0.45), [0, 0.22, 0]);
    const pts = [0, 1, 2, 3, 4].map(k => { const u = k / 4; return V.add(V.add(V.mul(base, (1 - u) * (1 - u)), V.mul(ctl, 2 * u * (1 - u))), V.mul(tip, u * u)); });
    return { pts, chain: new D.Chain('foliage', 5, { r: [0.02, 0.03, 0.035, 0.04, 0.045], sag: 0.15, tipSoft: 0.35 }) }; });
const floor = { type: 'plane', n: [0, 1, 0], d: 0, tag: 'floor' };
const FRAMES = [], ENERGY = [], GAPS = [], CHECK = [];
const smoothYaw = []; // not used: yaw is already eased

function earTargets(Hp, s, e) {
  const { H, fwd, up, side } = Hp; const base = V.add(H, V.add(V.add(V.mul(up, 0.066), V.mul(side, 0.046 * s)), V.mul(fwd, -0.02)));
  const dPr = V.norm(V.add(V.add(V.mul(up, 0.92), V.mul(side, 0.32 * s)), V.mul(fwd, 0.06)));
  const dFl = V.norm(V.add(V.add(V.mul(fwd, -0.88), V.mul(side, 0.38 * s)), V.mul(up, 0.12)));
  const d1 = V.norm(V.lerp(dFl, dPr, e)); const mid = V.add(base, V.mul(d1, 0.068));
  const tipD = V.norm(V.lerp(V.add(V.mul(dFl, 1), [0, -0.25, 0]), V.add(V.mul(up, 0.35), V.add(V.mul(fwd, 0.75), V.mul(side, 0.15 * s))), e));
  return [base, mid, V.add(mid, V.mul(tipD, 0.058))];
}
function tailTargets(Sk, t) {
  const { B } = Sk, a = B.a; const base = B.at(-0.405, B.pelvisC + 0.055);
  let phi = table([[0, 0.75], [0.5, -0.62], [0.8, -0.95], [1.15, -1.42], [1.4, -1.72]], a.tail);
  phi = lerp(phi, -0.28, B.lb);
  const curl = lerp(table([[0, -0.08], [0.5, -0.12], [1.0, -0.2], [1.4, -0.3]], a.tail), -0.02, B.lb);
  const wag = a.wag * 0.75 * Math.sin(2 * PI * 2.1 * t) + 0.12 * Math.sin(2 * PI * 0.9 * t) * a.wag;
  const back = V.mul(B.F, -1), pts = [base]; let ang = phi, p = base;
  for (let k = 1; k < 7; k++) {
    const dir = V.norm(V.add(V.add(V.mul(back, Math.cos(ang) * Math.cos(wag)), V.mul(B.L, Math.sin(wag) * Math.cos(ang))), [0, Math.sin(ang), 0]));
    p = V.add(p, V.mul(dir, 0.066)); pts.push(p); ang += curl;
  }
  return pts;
}

let prevTail = null, prevEars = null;
for (let i = 0; i < N; i++) {
  const t = i * DT, Sk = dogSkeleton(i), { B, Hp, legs } = Sk; DOGHEAD[i] = Hp.H;
}
const PREVC = {}; // previous collider positions (for boundary velocities)
const PREV = {}; // previous pose targets per secondary part, for the relative (secondary) energy
const vel = (key, tgt) => { const pv = PREV[key]; PREV[key] = tgt; return pv ? tgt.map((q, k) => V.mul(V.sub(q, pv[k]), 1 / DT)) : tgt.map(() => [0, 0, 0]); };
function simFrame(i, record) {
  const t = record ? i * DT : 0, Sk = dogSkeleton(i), { B, Hp, legs } = Sk, a = B.a;
  // ears: pricked by attention; flattened by fear; a voice onset adds a small prick impulse
  let e = clamp(Math.max(a.ear, 0.45 * B.lb), 0, 1); for (const v of VOICE) e = clamp(e + 0.35 * seg(t, v.t, v.t + 0.12) * (1 - seg(t, v.t + 0.25, v.t + 0.7)) * (v.level === 'soft' ? 1 : 0), 0, 1);
  const skull = { type: 'sphere', c: Hp.H, r: 0.074 };
  const eLt = earTargets(Hp, 1, e), eRt = earTargets(Hp, -1, e); earL.step(eLt, [skull], DT, SUB, t); earR.step(eRt, [skull], DT, SUB, t);
  // tail: collides with the floor, the rump and both thighs (a tucked tail lies between the legs, not through them)
  const thighs = legs.filter(l => !l.fore).map(l => ({ type: 'capsule', a: l.root, b: l.j1, r: 0.075 }));
  const tailCols = [{ ...floor, tag: 'tail-floor' }, { type: 'sphere', c: B.torso[0].c, r: B.torso[0].r * 0.92 }, ...thighs];
  const tt = tailTargets(Sk, t); tail.step(tt, tailCols, DT, SUB, t);
  // collar tag: a pendulum under the throat that ticks on the chest
  const neckA = B.neckBase; let ring = V.add(V.lerp(neckA, Hp.H, 0.28), [0, -0.078, 0]); // just outside the neck's surface
  { const hit = D.resolve(ring, 0.014, { type: 'sphere', c: B.torso[4].c, r: B.torso[4].r }); if (hit) ring = hit.p; } // the collar rides on the chest, never inside it
  const vB = PREVC.brisket ? V.mul(V.sub(B.torso[4].c, PREVC.brisket), 1 / DT) : [0, 0, 0], vN = PREVC.neck ? V.mul(V.sub(neckA, PREVC.neck), 1 / DT) : [0, 0, 0];
  PREVC.brisket = B.torso[4].c; PREVC.neck = neckA;
  const tagT = [ring, V.add(ring, [0, -0.045, 0])]; tag.step(tagT, [{ type: 'sphere', c: B.torso[4].c, r: B.torso[4].r, tag: 'tag', v: vB }, { type: 'capsule', a: neckA, b: Hp.H, r: 0.06, tag: 'tag', v: vN }], DT, SUB, t);
  // coat mass proxies
  const coatO = { ruff: coat.ruff.step(B.torso[4].c, DT).slice(), belly: coat.belly.step(B.torso[2].c, DT).slice(), breech: coat.breech.step(B.torso[0].c, DT).slice(), neck: coat.neck.step(B.torso[5].c, DT).slice() };
  // person + scarf: hangs from the collar of the coat, drapes on the chest and the lap, never through them
  const Pp = personPose(i);
  const scarfRoot = V.add(Pp.neck, V.add(V.mul(Pp.Fs, 0.07), [0, -0.03, 0]));
  const sT = (n, off) => { const pts = []; for (let k = 0; k < n; k++) pts.push(V.add(V.add(scarfRoot, V.mul(Pp.L, off)), V.add(V.mul(Pp.fwd, -0.075 * k), V.mul(Pp.Fs, 0.012 * k)))); return pts; };
  const body = [{ type: 'sphere', c: Pp.chest, r: 0.16 }, { type: 'capsule', a: Pp.hip, b: Pp.chest, r: 0.15 }, { type: 'capsule', a: Pp.hipL, b: Pp.kL, r: 0.075 }, { type: 'capsule', a: Pp.hipR, b: Pp.kR, r: 0.075 }, floor,
    { type: 'capsule', a: Pp.shR, b: Pp.elR, r: 0.05 }, { type: 'capsule', a: Pp.elR, b: Pp.handR, r: 0.045 }];
  const sAt = sT(8, -0.05), sBt = sT(7, 0.05); scarfA.step(sAt, body, DT, SUB, t); scarfB.step(sBt, body, DT, SUB, t);
  // shrub stems: springs that the dog's head and body can push aside
  const vBody = PREVC.body ? V.mul(V.sub(B.torso[2].c, PREVC.body), 1 / DT) : [0, 0, 0]; PREVC.body = B.torso[2].c;
  const dogCols = [{ type: 'sphere', c: Hp.H, r: 0.10, tag: 'leaf', v: vBody }, { type: 'sphere', c: V.add(Hp.H, V.mul(Hp.fwd, 0.13)), r: 0.07, tag: 'leaf', v: vBody }, ...B.torso.map(s => ({ type: 'sphere', c: s.c, r: s.r + 0.02, tag: 'leaf', v: vBody }))];
  for (const st of STEMS) st.chain.step(st.pts, dogCols, DT, SUB, t);
  // energies (secondary kinetic energy relative to each part's pose motion) and gaps (collision assertions)
  if (!record) { for (const k of ['tail', 'eL', 'eR', 'tag', 'sA', 'sB']) delete PREV[k]; for (const k in PREVC) delete PREVC[k]; return; }
  ENERGY.push({ t: r4(t), tail: tail.energy(tt, vel('tail', tt)), ears: earL.energy(eLt, vel('eL', eLt)) + earR.energy(eRt, vel('eR', eRt)), tag: tag.energy(tagT, vel('tag', tagT)),
    scarf: scarfA.energy(sAt, vel('sA', sAt)) + scarfB.energy(sBt, vel('sB', sBt)), shrub: STEMS.reduce((s, q) => s + q.chain.energy(), 0), door: door.I * 0 + 0.5 * 3.9 * Math.pow(((DOOR_A[i] - (DOOR_A[i - 1] ?? DOOR_A[i])) / DT), 2),
    coat: Object.values(coat).reduce((s, q) => s + q.energy(), 0) });
  let gTail = 9; for (let k = 1; k < 7; k++) gTail = Math.min(gTail, D.signedGap(tail.p[k], tail.r[k], floor));
  let gScarf = 9; for (const ch of [scarfA, scarfB]) for (let k = 1; k < ch.n; k++) for (const c of body) gScarf = Math.min(gScarf, D.signedGap(ch.p[k], ch.r[k], c));
  // dog vs the house: inside the wall's thickness every dog sphere must stay within the door opening
  let gJamb = 9; const dogS = [...B.torso, { c: Hp.H, r: 0.085 }, ...legs.flatMap(l => [{ c: l.j1, r: 0.04 }, { c: l.paw, r: 0.03 }])];
  for (const s of dogS) if (s.c[0] + s.r > WORLD.wallIn && s.c[0] - s.r < WORLD.wallOut) gJamb = Math.min(gJamb, WORLD.open[1] - Math.abs(s.c[2]) - s.r);
  let gFloor = 9; for (const s of B.torso) gFloor = Math.min(gFloor, s.c[1] - s.r + 0.012); // 12 mm of coat may press on the boards
  GAPS.push({ t: r4(t), tail: r4(gTail), scarf: r4(gScarf), jamb: r4(gJamb), body_floor: r4(gFloor) });
  FRAMES.push(emit(i, Sk, Pp, coatO, tt));
}
// rest state: every secondary part is solved at its frame-0 pose before the shot starts (no settling on camera)
for (let w = 0; w < 72; w++) simFrame(0, false);
for (const c of [earL, earR, tail, tag, scarfA, scarfB, ...STEMS.map(q => q.chain)]) { c.events = []; c.v = c.v.map(() => [0, 0, 0]); }
for (const q of Object.values(coat)) { q.o = [0, 0, 0]; q.v = [0, 0, 0]; }
for (let i = 0; i < N; i++) simFrame(i, true);
EVENTS.push(...tail.events.filter(e => e.speed > 0.15), ...tag.events.filter(e => e.speed > 0.08), ...STEMS.flatMap(s => s.chain.events.filter(e => e.speed > 0.05)), ...earL.events.slice(0, 0));
// the body settling when the dog lies down (twice: the refusal, and across the sill)
for (let i = 1; i < N; i++) { if (BODY[i - 1].lb < 0.9 && BODY[i].lb >= 0.9) EVENTS.push({ t: i * DT, tag: 'lie', speed: 0.5, x: BODY[i].x }); if (BODY[i - 1].lb > 0.5 && BODY[i].lb <= 0.5) EVENTS.push({ t: i * DT, tag: 'rise', speed: 0.5 }); }

// ---------- camera: what must be visible, followed by a critically damped spring (no overshoot) ----------
function need(i) { // [left X, right X] that must be in frame
  const t = i * DT, x = FR[i].dog.x;
  const l = lerp(-0.95, -1.78, seg(t, 4.7, 5.9));
  if (t < 14.6) return [l, 5.25];
  return [l, Math.max(x + 1.15, 1.62)];
}
const CAM = []; { let c = 2.0, cv = 0, w = 5.9, wv = 0; const f = 0.32;
  for (let i = 0; i < N; i++) { const [l, r] = need(i), tc = (l + r) / 2, tw = (r - l);
    if (i === 0) { c = tc; w = tw; }
    [c, cv] = D.exactStep(c, cv, tc, f, 1.0, DT); [w, wv] = D.exactStep(w, wv, tw, f, 1.0, DT);
    CAM.push({ c, w }); } }
function camera(i) {
  const { c, w } = CAM[i], hfov = 38 * PI / 180, dist = (w / 2) / Math.tan(hfov / 2), vfov = 2 * Math.atan(Math.tan(hfov / 2) * 9 / 16);
  const yaw = 0.10, elev = 0.10, H = w * 9 / 16, cy = 0.33 * H - 0.02;
  const at = [c, cy, 0]; const pos = [c + dist * Math.sin(yaw), cy + dist * Math.sin(elev), dist * Math.cos(yaw)];
  return { pos: P3(pos), at: P3(at), vfov: r4(vfov) };
}

function emit(i, Sk, Pp, coatO, tt) {
  const { B, Hp, legs } = Sk;
  return { i, t: r4(i * DT),
    dog: { torso: B.torso.map(s => [...P3(s.c), r4(s.r)]), neck: P3(B.neckBase), head: P3(Hp.H), fwd: P3(Hp.fwd), up: P3(Hp.up), side: P3(Hp.side), F: P3(B.F), L: P3(B.L),
      legs: legs.map(l => ({ fore: l.fore, s: l.s, root: P3(l.root), j1: P3(l.j1), j2: P3(l.j2), paw: P3(l.paw) })),
      earL: earL.p.map(P3), earR: earR.p.map(P3), tail: tail.p.map(P3), tailPose: tt.map(P3), tag: tag.p.map(P3),
      coat: Object.fromEntries(Object.entries(coatO).map(([k, v]) => [k, P3(v)])), lie: r4(B.lb), mouth: r4(Math.max(0, B.a.wag * 0.0)) },
    person: { hip: P3(Pp.hip), chest: P3(Pp.chest), neck: P3(Pp.neck), head: P3(Pp.head), shR: P3(Pp.shR), shL: P3(Pp.shL), elR: P3(Pp.elR), handR: P3(Pp.handR), elL: P3(Pp.elL), handL: P3(Pp.handL),
      hipL: P3(Pp.hipL), hipR: P3(Pp.hipR), kL: P3(Pp.kL), kR: P3(Pp.kR), fl: P3(Pp.fl), fr: P3(Pp.fr), F: P3(Pp.Fs), gaze: P3(Pp.gaze), mouth: r4(mouthAt(i * DT)),
      scarfA: scarfA.p.map(P3), scarfB: scarfB.p.map(P3) },
    door: r4(DOOR_A[i]), stems: STEMS.map(s => s.chain.p.map(P3)) };
}

FRAMES.forEach((f, i) => { f.cam = camera(i); });
// measured quantities for the trace and the bar
const MEAS = FRAMES.map((f, i) => { const B = BODY[i]; const H = f.dog.head, topBack = Math.max(...B.torso.slice(1, 4).map(s => s.c[1] + s.r));
  const headTop = H[1] + 0.085; const planted = FOOT[i].filter(q => q.planted).map(q => q.p);
  return { head_top: r4(headTop), back_top: r4(topBack), head_below_back: headTop < topBack, lie: r4(B.lb), pelvis_y: r4(B.pelvisC), withers_y: r4(B.withersC) }; });
// foot slide: the largest movement of any foot across consecutive frames in which it stays planted
let slide = 0; for (let i = 1; i < N; i++) for (let k = 0; k < 4; k++) if (FOOT[i][k].planted && FOOT[i - 1][k].planted) slide = Math.max(slide, V.len(V.sub(FOOT[i][k].p, FOOT[i - 1][k].p)));
const out = { preset: PRESET, N, fps: 24, world: WORLD, voice: VOICE, events: EVENTS.map(e => ({ ...e, t: r4(e.t), speed: r4(e.speed) })).sort((a, b) => a.t - b.t), frames: FRAMES, energy: ENERGY, gaps: GAPS, meas: MEAS, foot_slide_max: slide,
  materials: D.MATERIALS };
fs.mkdirSync(path.dirname(OUT), { recursive: true }); fs.writeFileSync(OUT, JSON.stringify(out));
console.log('door pull impulse', DOORJ.toFixed(3), 'N·m·s');
console.log('wrote', OUT, 'frames', N, 'events', out.events.length, 'foot slide max (m)', slide.toFixed(4),
  'min gaps', ['tail', 'scarf', 'jamb', 'body_floor'].map(k => k + ' ' + Math.min(...GAPS.map(g => g[k])).toFixed(4)).join(', '));
