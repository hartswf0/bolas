// The person, in the same vocabulary as the dog: a joint graph drawn as capsules. They are a circumstance, not a performer
// of the dog's choices: calls, a reach, stepping aside and sitting, a push at the door, a hand offered low.
import type {V3} from './math.ts';
import {add, sub, mul, norm, lerp, clamp, deg, mix3} from './math.ts';
import {ik, frameOf} from './dogRig.ts';
export type PersonPose = {X: number; Z: number; yaw: number; walk: number; moving: number; sit: number; lean: number;
  beckon: number; wavePh: number; reach: number; push: number; low: number; mouth: number; tilt: number;
  pushTo: V3; lowTo: V3};
export type PTone = 'cloth' | 'cloth2' | 'skin' | 'hair' | 'shoe';
export type PPart = {kind: 'cap'; a: V3; ra: number; b: V3; rb: number; tone: PTone};

export function personParts(p: PersonPose): PPart[] {
  const {f, s} = frameOf(p.yaw); const up: V3 = [0, 1, 0];
  const root: V3 = [p.X, 0, p.Z];
  const W = (fw: number, h: number, sd: number): V3 => [root[0] + f[0] * fw + s[0] * sd, h, root[2] + f[2] * fw + s[2] * sd];
  const sit = clamp(p.sit);
  const out: PPart[] = [];
  const cap = (a: V3, ra: number, b: V3, rb: number, tone: PTone) => out.push({kind: 'cap', a, ra, b, rb, tone});
  // pelvis: standing 0.93 high; sitting on the porch boards, back to the wall
  const hip = W(lerp(0, 0.05, sit), lerp(0.93, 0.13, sit), 0);
  const lean = (p.lean + lerp(0, -12, sit)) * deg;          // + forward
  const spineDir = norm(add(mul(up, Math.cos(lean)), mul(f, Math.sin(lean))));
  const chest = add(hip, mul(spineDir, 0.5));
  const neck = add(hip, mul(spineDir, 0.6));
  const tilt = p.tilt * deg;
  const headDir = norm(add(mul(spineDir, Math.cos(tilt)), mul(f, Math.sin(tilt))));
  const head = add(neck, mul(headDir, 0.14));
  // legs
  for (const sd of [1, -1]) {
    const hp = add(hip, mul(s, 0.1 * sd));
    const ph = p.walk + (sd > 0 ? 0 : Math.PI);
    const stride = 0.22 * p.moving;
    const standFoot = W(Math.sin(ph) * stride, Math.max(0, Math.cos(ph)) * 0.07 * p.moving + 0.04, 0.11 * sd);
    const sitFoot = W(0.62, 0.05, 0.16 * sd);
    const foot = mix3(standFoot, sitFoot, sit);
    const knee = ik(hp, foot, 0.46, 0.46, norm(add(f, mul(up, 0.4 * sit))));
    cap(hp, 0.085, knee, 0.068, 'cloth2');
    cap(knee, 0.062, foot, 0.05, 'cloth2');
    cap(foot, 0.045, add(foot, mul(f, 0.13)), 0.045, 'shoe');
  }
  // torso and head
  cap(add(hip, mul(spineDir, 0.06)), 0.15, chest, 0.17, 'cloth');
  cap(add(chest, mul(spineDir, 0.06)), 0.05, neck, 0.045, 'skin');
  cap(add(head, mul(f, 0.012)), 0.092, add(head, mul(headDir, -0.03)), 0.088, 'skin');
  cap(add(add(head, mul(f, 0.088)), mul(headDir, -0.01)), 0.02, add(add(head, mul(f, 0.098)), mul(headDir, -0.03)), 0.018, 'skin');   // nose
  cap(add(head, add(mul(headDir, 0.035), mul(f, -0.03))), 0.094, add(head, add(mul(headDir, -0.02), mul(f, -0.06))), 0.085, 'hair');
  // arms: the near-side arm (side +1) acts; the other rests
  for (const sd of [1, -1]) {
    const sh = add(add(hip, mul(spineDir, 0.46)), mul(s, 0.2 * sd));
    let hand = add(add(sh, mul(up, -0.55)), mul(f, 0.05));
    if (sit > 0.5) hand = add(add(hip, mul(f, 0.35)), add(mul(up, 0.3), mul(s, 0.17 * sd)));   // on the knees
    if (sd > 0) {
      const bk = add(add(sh, mul(f, 0.36 - 0.1 * (0.5 + 0.5 * Math.sin(p.wavePh)))), mul(up, 0.02));
      hand = mix3(hand, bk, clamp(p.beckon));
      hand = mix3(hand, add(add(sh, mul(f, 0.6)), mul(up, -0.28)), clamp(p.reach));
      hand = mix3(hand, p.pushTo, clamp(p.push));
      hand = mix3(hand, p.lowTo, clamp(p.low));
    }
    const d = sub(hand, sh); const dl = Math.hypot(d[0], d[1], d[2]);
    if (dl > 0.6) hand = add(sh, mul(d, 0.6 / dl));
    const elbow = ik(sh, hand, 0.31, 0.3, norm(add(mul(up, -1), mul(s, 0.5 * sd))));
    cap(sh, 0.07, elbow, 0.055, 'cloth');
    cap(elbow, 0.05, hand, 0.04, 'cloth');
    cap(hand, 0.045, hand, 0.045, 'skin');
  }
  return out;
}
