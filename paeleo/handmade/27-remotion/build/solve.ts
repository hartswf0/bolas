// SCION-27 · the scene compiler, pass 1: score → typed scene manifest.
// node --experimental-strip-types build/solve.ts
// Reads the PAELEO score (the dog's decision trace) and compiles every frame's state: the dog's plan position (= score x),
// heading and head yaw (my acting layer over the score's intentions), the gait solver's paw positions, the person,
// the door and lamp, the spoken lines, and the sound events. Deterministic: no clock, no Math.random; seed 27.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import type {V3} from './src/lib/math.ts';
import {clamp, lerp, ramp, keyed, smooth, vnoise, deg} from './src/lib/math.ts';
import {FOOT_LOCAL, FOOT_LIE, toWorld} from './src/lib/dogRig.ts';
import {WORLD, doorAngle} from './src/lib/world.ts';
import {project, setCameraTime, camAt} from './src/lib/camera.ts';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../../..');
const SCORE = JSON.parse(fs.readFileSync(path.join(ROOT, 'paeleo/handmade/score/threshold-score.json'), 'utf8'));
const FR = SCORE.frames as any[];
const N = FR.length, FPS = 24, SEED = 27;
if (N !== 768) throw new Error('score must have 768 frames');

// ---------- the dog's acting layer: heading and head yaw (degrees) ----------
const REF_YAW = -175;                                          // refusal heading = 180 − 175 = 5°: back to the door, facing the yard
const yawAt = (i: number) => {
  const t = i / FPS;
  if (t < 3.42) return 180;
  if (t < 7.46) return 180 + REF_YAW * ramp(t, 3.43, 3.88);    // the turn away, retimed to read by 3.9 s
  return 180 + REF_YAW * (1 - ramp(t, 7.56, 8.4));             // the turn back: it rises and turns together (score turn: 7.9–8.7)
};
const HAND_LOW: V3 = [1.26, 0.16, -0.62];                       // where the person's low hand rests (world)
const headYawAt = (i: number, X: number, yaw: number) => {
  const t = i / FPS;
  let psi = 0;
  if (t >= 3.40 && t < 7.40) psi = keyed([[3.40, 0], [3.48, -50], [3.70, -40], [3.90, -10], [4.6, -8], [7.4, -8]], t);
  if (t >= 7.40 && t < 10) {
    const target = clamp(182 - yaw, 0, 140);                  // the head comes round toward the door first, over the shoulder
    psi = lerp(-8, target, ramp(t, 7.40, 7.60));
  }
  // passing the low hand on the way in: the head goes to it (sniff), then on
  if (t > 19 && t < 24) {
    const hx = X - 0.55, hz = WORLD.dogZ;                       // approx. head position
    const want = Math.atan2(HAND_LOW[2] - hz, HAND_LOW[0] - hx) / deg;    // world heading to the hand
    let d = want - yaw; while (d > 180) d -= 360; while (d < -180) d += 360;
    const w = smooth((X - 1.55) / 0.25) * (1 - smooth((X - 2.2) / 0.3));   // only while the head is near it
    psi = clamp(d, -55, 55) * w * 0.9;
  }
  if (t >= 26.3) psi = 18 * FR[i].dog.act.look;                // looking in: muzzle into the room, back of the head to us
  return psi;
};

// ---------- the gait solver: paws stay planted unless a step carries them ----------
type Swing = {from: V3; to: V3; f0: number; dur: number} | null;
const feet: V3[][] = [], swingP: number[][] = [], plants: {i: number; k: number; speed: number}[] = [];
const rootAt = (i: number): V3 => [FR[Math.min(N - 1, i)].dog.x, 0, WORLD.dogZ];
const target = (i: number, k: number): V3 => { const j = Math.min(N - 1, i); const [fw, sd] = FOOT_LOCAL[k]; return toWorld(rootAt(j), yawAt(j), [fw, 0, sd]); };
const lieTarget = (i: number, k: number): V3 => { const [fw, sd] = FOOT_LIE[k]; return toWorld(rootAt(i), yawAt(i), [fw, 0.0, sd]); };
let P: V3[] = [0, 1, 2, 3].map(k => target(0, k));
let S: Swing[] = [null, null, null, null];
let lastStart = -99, lieAnchor: V3[] | null = null, prevLie = 0;
const dist = (a: V3, b: V3) => Math.hypot(a[0] - b[0], a[2] - b[2]);
const idle = [0, 0, 0, 0];
for (let i = 0; i < N; i++) {
  const lie = FR[i].dog.act.lie;
  const speed = Math.abs(FR[Math.min(N - 1, i + 1)].dog.x - FR[Math.max(0, i - 1)].dog.x) * FPS / 2;
  const out: V3[] = [], sp: number[] = [];
  if (lie > 0.02) {
    // lying down / getting up: paws travel between the planted stance and the sphinx pose with the body
    if (!lieAnchor) lieAnchor = P.map(p => [...p] as V3);
    const rising = lie < prevLie - 1e-4;
    for (let k = 0; k < 4; k++) {
      const from = rising ? target(i, k) : lieAnchor[k];
      const q = smooth(clamp(lie / 0.9));
      const a = [lerp(from[0], lieTarget(i, k)[0], q), 0, lerp(from[2], lieTarget(i, k)[2], q)] as V3;
      a[1] = (k < 2 ? 0.05 : 0.02) * Math.sin(Math.PI * q);  // a paw lifts as it is placed
      out.push(a); sp.push(0);
    }
    P = out.map(p => [p[0], 0, p[2]] as V3); S = [null, null, null, null];
    if (rising) lieAnchor = P.map(p => [...p] as V3);
  } else {
    if (lieAnchor) { lieAnchor = null; P = [0, 1, 2, 3].map(k => target(i, k)); }
    for (let k = 0; k < 4; k++) {
      const sw = S[k];
      if (sw && i >= sw.f0 + sw.dur) { P[k] = sw.to; S[k] = null; plants.push({i, k, speed}); idle[k] = 0; }
    }
    // start a step: the paw farthest from where the body now wants it, if its side is free
    const dur = Math.round(clamp(7 - speed * 3.5, 4, 7));
    const thr = 0.075;
    const cand = [0, 1, 2, 3].filter(k => !S[k]).map(k => ({k, e: dist(P[k], target(i, k))})).sort((a, b) => b.e - a.e);
    for (const c of cand) {
      if (i - lastStart < 2) break;
      const swinging = [0, 1, 2, 3].filter(k => S[k]);
      if (swinging.length >= 2) break;
      const side = c.k % 2;                                          // 0: FL/HL side (+), 1: FR/HR side (−)
      if (swinging.some(k => k % 2 === side)) continue;
      idle[c.k] = c.e > 0.025 ? idle[c.k] + 1 : 0;
      if (c.e > thr || (idle[c.k] > 14 && c.e > 0.025)) {
        const lead = Math.round(dur + 5 * clamp(speed / 0.4));
        S[c.k] = {from: P[c.k], to: target(i + lead, c.k), f0: i, dur}; lastStart = i; idle[c.k] = 0;
        break;
      }
    }
    for (let k = 0; k < 4; k++) {
      const sw = S[k];
      if (sw) {
        const u = (i - sw.f0) / sw.dur, q = smooth(u);
        out.push([lerp(sw.from[0], sw.to[0], q), 0.065 * Math.sin(Math.PI * u), lerp(sw.from[2], sw.to[2], q)]); sp.push(u);
      } else { out.push([...P[k]] as V3); sp.push(-1); }
    }
  }
  prevLie = lie;
  feet.push(out); swingP.push(sp);
}

// ---------- the person ----------
const DOORWAY: V3 = [0.24, 0, 0.05], SEAT: V3 = [0.66, 0, -1.02];
const PUSH_TO: V3 = [0.14, 0.82, -0.40];
const personAt = (i: number) => {
  const t = i / FPS, sp = FR[i].person;
  const walkU = ramp(t, 4.65, 5.45);
  const a = DOORWAY, m: V3 = [0.74, 0, -0.45], b = SEAT;
  const u = walkU;   // quadratic path through the doorway and aside
  const X = (1 - u) * (1 - u) * a[0] + 2 * (1 - u) * u * m[0] + u * u * b[0];
  const Z = (1 - u) * (1 - u) * a[2] + 2 * (1 - u) * u * m[2] + u * u * b[2];
  const moving = clamp(Math.sin(Math.PI * clamp((t - 4.65) / 0.8)) * 1.6);
  const travelYaw = keyed([[4.6, 0], [4.85, -40], [5.2, -95], [5.5, 0]], t);
  const sit = ramp(t, 5.45, 6.15);
  const callW = (t0: number, t1: number) => ramp(t, t0 - 0.1, t0 + 0.12) * (1 - ramp(t, t1 - 0.05, t1 + 0.25));
  const beckon = callW(1.0, 2.3) * (1 - sp.reach);
  const reach = sp.reach;
  const push = 0;                                              // the door swings on a draught; nobody pushes it
  const low = ramp(t, 6.75, 7.25);
  const soft = sp.voice === 'soft' ? 1 : 0;
  return {X, Z, yaw: travelYaw, walk: walkU * Math.PI * 4, moving, sit, lean: 7 * beckon + 24 * reach + 30 * low,
    beckon, wavePh: t * Math.PI * 2 * 2.2, reach, push, low, mouth: sp.mouth, tilt: 10 * low + 6 * soft,
    pushTo: PUSH_TO, lowTo: HAND_LOW};
};

// ---------- words, door, lamp ----------
const LINES: [number, number, string, 'call' | 'soft'][] = [
  [1.0, 2.3, 'Come here.', 'call'], [3.4, 4.6, 'Come here!', 'call'],
  [7.4, 9.4, 'It’s all right.', 'soft'], [10.4, 11.6, 'It’s all right.', 'soft'], [26.4, 27.4, 'Come in.', 'soft']];

const frames = FR.map((F, i) => {
  const t = i / FPS, A = F.dog.act;
  const yaw = yawAt(i), X = F.dog.x;
  const sw = swingP[i].filter(v => v >= 0);
  const bob = -0.012 * sw.reduce((s, u) => s + Math.sin(Math.PI * u), 0) * (1 - A.lie);
  const sniff = (t > 19 && t < 24) ? 0.12 * smooth((X - 1.55) / 0.25) * (1 - smooth((X - 2.2) / 0.3)) : 0;
  const dog = {X, Z: WORLD.dogZ, yaw, headYaw: headYawAt(i, X, yaw), lie: A.lie, crouch: A.crouch,
    // the head goes low as it sets off
    head: (t > 14.4 && t < 15.3 ? Math.min(A.head, keyed([[14.4, 0.9], [14.72, 0.45]], t)) : A.head) - sniff,
    ear: A.ear + 0.1 * (vnoise(SEED, t * 1.7) - 0.5) * (1 - A.crouch), tail: A.tail,
    wag: A.wag, wagPh: t * Math.PI * 2 * 2.3, rest: A.rest, look: A.look,
    breath: Math.sin(t * Math.PI * 2 * 0.33), bob, feet: feet[i].map(p => p.map(v => +v.toFixed(4))), swing: swingP[i]};
  const open01 = ramp(t, 6.2, 6.85);
  const line = LINES.find(l => t >= l[0] - 0.05 && t < l[1] + 0.4);
  const cam = camAt(t);
  return {i, t: +t.toFixed(4), score_state: F.dog.state, camera: {pos: cam.pos.map(v => +v.toFixed(5)), target: cam.target.map(v => +v.toFixed(5)), focal: +cam.focal.toFixed(4)}, dog, person: personAt(i),
    door: {open01, angle: doorAngle(open01), lamp: lerp(0.5, 1, open01)},
    caption: line ? {text: line[2], kind: line[3], alpha: ramp(t, line[0] - 0.05, line[0] + 0.12) * (1 - ramp(t, line[1] + 0.1, line[1] + 0.4))} : null};
});

// ---------- the manifest contract: every dog/person channel is a finite number in every frame ----------
const DOG_KEYS = ['X', 'Z', 'yaw', 'headYaw', 'lie', 'crouch', 'head', 'ear', 'tail', 'wag', 'wagPh', 'rest', 'look', 'breath', 'bob'];
for (const f of frames) {
  for (const k of DOG_KEYS) if (typeof (f.dog as any)[k] !== 'number' || !Number.isFinite((f.dog as any)[k])) throw new Error(`frame ${f.i}: dog.${k} = ${(f.dog as any)[k]}`);
  if (f.dog.feet.flat().some((v: number) => !Number.isFinite(v))) throw new Error(`frame ${f.i}: feet`);
  for (const [k, v] of Object.entries(f.person)) if (typeof v === 'number' && !Number.isFinite(v)) throw new Error(`frame ${f.i}: person.${k}`);
}

// ---------- the audio manifest (synthesised by build/sound.py) ----------
const events: any[] = [];
for (const p of plants) events.push({t: +(p.i / FPS).toFixed(4), kind: 'paw', k: p.k, gain: 0.5 + 0.5 * clamp(p.speed / 0.7)});
for (const l of LINES) events.push({t: l[0], t1: l[1], kind: l[3] === 'call' ? 'voice_call' : 'voice_soft', text: l[2]});
events.push({t: 5.95, t1: 6.9, kind: 'wind_gust'}, {t: 6.2, t1: 6.85, kind: 'door_creak'});
events.push({t: 4.72, kind: 'person_step'}, {t: 5.05, kind: 'person_step'}, {t: 5.35, kind: 'person_step'});
events.push({t: 5.6, t1: 6.15, kind: 'person_sit'});
// the dog's body meets the boards when it lies (refusal and sill), and lets out a breath
for (const [t0, t1] of [[4.3, 5.1], [23.8, 24.6]]) {
  const hit = frames.find(f => f.t >= t0 && f.dog.lie > 0.85); if (hit) events.push({t: hit.t, kind: 'body_down'});
  const sigh = frames.find(f => f.t >= t0 + 0.4 && f.dog.lie > 0.97); if (sigh) events.push({t: sigh.t + 0.25, kind: 'sigh'});
}
// the tail thumps the boards when it wags lying down: one thump at each extreme of the sweep
for (let i = 1; i < N; i++) {
  const f = frames[i], g = frames[i - 1];
  if (f.dog.lie > 0.9 && f.dog.wag > 0.3) {
    const a = Math.sin(g.dog.wagPh), b = Math.sin(f.dog.wagPh);
    if ((a < 0.95 && b >= 0.95) || (a > -0.95 && b <= -0.95)) events.push({t: f.t, kind: 'tail_thump', gain: f.dog.wag});
  }
}
events.push({t: 28.3, kind: 'sigh'});
// stereo position of each dog sound = where the dog is on screen
for (const e of events) if (['paw', 'body_down', 'sigh', 'tail_thump'].includes(e.kind)) {
  const f = frames[Math.min(N - 1, Math.round(e.t * FPS))]; setCameraTime(f.t);
  e.pan = +clamp((project([f.dog.X, 0.3, f.dog.Z])[0] / 640 - 1) * 0.8, -0.8, 0.8).toFixed(2);
}
events.sort((a, b) => a.t - b.t);

const manifest = {
  schema: 'scion27.manifest/1', seed: SEED, fps: FPS, frames_n: N, score: 'paeleo/handmade/score/threshold-score.json',
  world: WORLD, hand_low: HAND_LOW, lines: LINES, frames,
};
fs.mkdirSync(path.join(HERE, 'cache'), {recursive: true});
fs.writeFileSync(path.join(HERE, 'cache/manifest.json'), JSON.stringify(manifest));
fs.writeFileSync(path.join(HERE, 'cache/audio.json'), JSON.stringify({fps: FPS, offset_s: 3, scene_s: 32, total_s: 38, events}, null, 1));
console.log('manifest', N, 'frames; paw plants', plants.length, '; audio events', events.length);
