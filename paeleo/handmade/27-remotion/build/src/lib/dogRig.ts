// The dog, as a typed joint graph. No mesh, no image: 3-D joints solved per frame from the manifest, then drawn by
// <Dog> as tapered round-capped strokes ("capsules"). A capsule seen end-on is a disc, so a turn passes through
// views (front, back, three-quarter) that are still a body, not a flattened card.
// Proportions are measured from the archive dog's rig keys (kit/archive-dog/pose_agent_v8.json, 10 side-on keys,
// medians normalised by chest→tail length): neck height 0.88 L, chest 0.48 L, tail root 0.76 L, nose→neck 0.71 L.
import type {V3} from './math.ts';
import {add, sub, mul, norm, cross, len, dot, lerp, clamp, keyed, deg, mix3} from './math.ts';

export const L = 0.72;                                   // chest→tail, metres (a shepherd-sized dog)
export const MEASURED = {neck_h: 0.881, chest_h: 0.475, tail_h: 0.76, nose_neck: 0.706, neck_chest: 0.425};
export type DogPose = {
  X: number; Z: number; yaw: number; headYaw: number;    // plan position (body centre), heading (deg), head yaw rel. body
  lie: number; crouch: number; head: number; ear: number; tail: number; wag: number; wagPh: number;
  rest: number; look: number; breath: number; bob: number; feet: V3[];  // paws FL FR HL HR, world (from the gait solver)
};
export type Tone = 'coat' | 'saddle' | 'tan' | 'dark' | 'nose' | 'eye' | 'ear';
export type Matte = 'body' | 'neck' | 'skull' | 'muzzle';
export type Part = {kind: 'cap'; a: V3; ra: number; b: V3; rb: number; tone: Tone; matte: Matte; far?: boolean; bias?: number}
  | {kind: 'tri'; pts: V3[]; tone: Tone; matte: Matte; far?: boolean; bias?: number};

/** neutral standing paw positions, local (forward, side) */
export const FOOT_LOCAL: [number, number][] = [[0.24, 0.085], [0.24, -0.085], [-0.27, 0.09], [-0.27, -0.09]];
/** sphinx (lying) paw positions, local */
export const FOOT_LIE: [number, number][] = [[0.50, 0.07], [0.50, -0.07], [-0.10, 0.17], [-0.10, -0.17]];

export const frameOf = (yaw: number) => {
  const a = yaw * deg; const f: V3 = [Math.cos(a), 0, Math.sin(a)]; const s: V3 = [-Math.sin(a), 0, Math.cos(a)];
  return {f, s, u: [0, 1, 0] as V3};
};
export const toWorld = (root: V3, yaw: number, l: [number, number, number]): V3 => {
  const {f, s} = frameOf(yaw);
  return [root[0] + f[0] * l[0] + s[0] * l[2], l[1], root[2] + f[2] * l[0] + s[2] * l[2]];
};
/** two-bone IK: from a to c with lengths l1, l2, bending toward hint */
export const ik = (a: V3, c: V3, l1: number, l2: number, hint: V3): V3 => {
  const d0 = sub(c, a); let d = len(d0); const n = norm(d0);
  d = clamp(d, Math.abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3);
  const along = (l1 * l1 - l2 * l2 + d * d) / (2 * d), h = Math.sqrt(Math.max(0, l1 * l1 - along * along));
  let m = sub(hint, mul(n, dot(hint, n))); m = norm(m);
  return add(add(a, mul(n, along)), mul(m, h));
};

export function dogParts(p: DogPose): Part[] {
  const root: V3 = [p.X, 0, p.Z];
  const {f, s} = frameOf(p.yaw); const up: V3 = [0, 1, 0];
  const W = (fw: number, h: number, sd: number) => toWorld(root, p.yaw, [fw, h, sd]);
  const lie = clamp(p.lie), cr = clamp(p.crouch);
  // torso heights: standing → lying (sphinx), crouch lowers the rump more than the chest (fear)
  const hc = lerp(0.445, 0.175, lie) - cr * 0.06 + p.bob + p.breath * 0.006;
  const hr = lerp(0.455, 0.145, lie) - cr * 0.10 + p.bob;
  const parts: Part[] = [];
  const cap = (a: V3, ra: number, b: V3, rb: number, tone: Tone, matte: Matte = 'body', far = false, bias = 0) =>
    parts.push({kind: 'cap', a, ra, b, rb, tone, matte, far, bias});
  // torso
  const chestA = W(0.27, hc - 0.01, 0), chestB = W(0.10, hc + 0.01, 0);
  const barrelA = W(0.12, hc + 0.015, 0), barrelB = W(-0.10, lerp(hc, hr, 0.5) + 0.02, 0);
  const loinA = W(-0.08, lerp(hc, hr, 0.6) + 0.03, 0), loinB = W(-0.30, hr, 0);
  cap(chestA, 0.168 + p.breath * 0.004, chestB, 0.16, 'coat');
  cap(barrelA, 0.152, barrelB, 0.135, 'coat');
  cap(loinA, 0.125, loinB, 0.13, 'coat');
  cap(W(-0.33, hr - 0.005, 0), 0.128, W(-0.33, hr - 0.005, 0), 0.128, 'coat');
  // saddle: the dark band along the back (drawn just above the torso)
  cap(W(0.16, hc + 0.105, 0), 0.07, W(-0.27, hr + 0.07, 0), 0.07, 'saddle', 'body', false, -0.02);
  cap(W(0.20, hc - 0.05, 0), 0.125, W(0.02, hc - 0.03, 0), 0.11, 'coat');                       // deep chest (keel)
  cap(W(0.29, hc - 0.06, 0), 0.10, W(0.22, hc - 0.11, 0), 0.08, 'tan', 'body', false, -0.01);   // chest front, lighter
  // neck and head
  let phi = keyed([[0, -58], [0.15, -50], [0.45, -44], [0.7, 12], [0.9, 38], [1.25, 54]], p.head, false);
  phi = lerp(phi, -42, clamp(p.rest)); phi = lerp(phi, 20, clamp(p.look));
  const reach = 0.25 * (1 + 0.14 * clamp(p.look));
  const neckBase = W(0.25 + 0.05 * clamp(p.look), hc + 0.09, 0);
  const hy = (p.yaw + p.headYaw) * deg, ny = (p.yaw + p.headYaw * 0.55) * deg;
  const hdir: V3 = [Math.cos(hy), 0, Math.sin(hy)], ndir: V3 = [Math.cos(ny), 0, Math.sin(ny)];
  const skull = add(neckBase, add(mul(ndir, reach * Math.cos(phi * deg)), mul(up, reach * Math.sin(phi * deg))));
  cap(neckBase, 0.105, skull, 0.08, 'coat', 'neck');
  let beta = keyed([[-58, -62], [-44, -48], [12, -14], [54, -6]], phi, false);
  beta = lerp(beta, -4, clamp(p.rest));
  const md = norm(add(mul(hdir, Math.cos(beta * deg)), mul(up, Math.sin(beta * deg))));
  const hs = norm(cross(up, hdir));                       // head side axis
  const hu = norm(cross(md, hs));                         // head up axis (perpendicular to muzzle)
  cap(add(skull, mul(hu, -0.025)), 0.098, add(add(skull, mul(md, 0.03)), mul(hu, -0.03)), 0.085, 'tan', 'skull');   // cheeks
  cap(add(skull, mul(hu, 0.02)), 0.092, add(skull, mul(md, -0.02)), 0.094, 'coat', 'skull', false, -0.002);        // crown
  const mU0 = add(add(skull, mul(md, 0.06)), mul(hu, 0.012)), mU1 = add(add(skull, mul(md, 0.185)), mul(hu, -0.008));
  cap(add(add(skull, mul(md, 0.06)), mul(hu, -0.03)), 0.05, add(add(skull, mul(md, 0.165)), mul(hu, -0.035)), 0.03, 'tan', 'muzzle', false, -0.004);
  cap(mU0, 0.056, mU1, 0.037, 'saddle', 'muzzle', false, -0.006);
  const mB = mU1;
  cap(add(mB, mul(md, 0.016)), 0.022, add(mB, mul(md, 0.016)), 0.022, 'nose', 'muzzle', false, -0.03);
  // eyes (one per side) and ears
  for (const sd of [1, -1]) {
    const e = add(add(add(skull, mul(md, 0.07)), mul(hs, 0.055 * sd)), mul(hu, 0.03));
    cap(e, 0.013, e, 0.013, 'eye', 'skull', false, -0.05);
    const pip = add(add(e, mul(hu, 0.03)), mul(md, -0.008));
    cap(pip, 0.011, pip, 0.011, 'tan', 'skull', false, -0.045);
    const pr = clamp(p.ear * (0.6 + 0.4 * clamp(p.head)), -0.1, 1.05);   // 1 pricked, 0 flat back; a low head carries its ears lower
    const base1 = add(add(add(skull, mul(hs, 0.025 * sd)), mul(hu, 0.08)), mul(md, -0.01));
    const base2 = add(add(add(skull, mul(hs, 0.088 * sd)), mul(hu, 0.035)), mul(md, -0.04));
    const tipUp = add(add(add(skull, mul(hs, 0.09 * sd)), mul(hu, 0.23)), mul(md, -0.035));
    const tipFlat = add(add(add(skull, mul(hs, 0.085 * sd)), mul(hu, 0.06)), mul(md, -0.17));
    parts.push({kind: 'tri', pts: [base1, base2, mix3(tipFlat, tipUp, pr)], tone: 'ear', matte: 'skull', bias: -0.01});
  }
  // legs: shoulders and hips follow the torso; paws come from the gait solver
  const legs: {base: V3; paw: V3; front: boolean; sd: number}[] = [
    {base: W(0.22, hc + 0.02, 0.085), paw: p.feet[0], front: true, sd: 1},
    {base: W(0.22, hc + 0.02, -0.085), paw: p.feet[1], front: true, sd: -1},
    {base: W(-0.30, hr + 0.0, 0.09), paw: p.feet[2], front: false, sd: 1},
    {base: W(-0.30, hr + 0.0, -0.09), paw: p.feet[3], front: false, sd: -1},
  ];
  for (const lg of legs) {
    const side = mul(s, lg.sd);
    if (lg.front) {
      const wrist = add(lg.paw, add(mul(up, lerp(0.06, 0.03, lie)), mul(f, lerp(-0.015, -0.08, lie))));
      const elbow = ik(lg.base, wrist, 0.20, 0.21, add(mul(f, -1), mul(up, -0.3)));
      cap(lg.base, 0.085, elbow, 0.058, 'coat', 'body', false, 0);
      cap(elbow, 0.05, wrist, 0.04, 'tan');
      cap(wrist, 0.04, add(lg.paw, mul(f, 0.05)), 0.04, 'tan');
    } else {
      const hock = add(lg.paw, add(mul(up, lerp(0.125, 0.025, lie)), mul(f, lerp(-0.05, -0.26, lie))));
      const knee = ik(lg.base, hock, 0.22, 0.23, norm(add(add(f, mul(up, -0.1)), mul(side, 0.9 * lie))));
      cap(lg.base, 0.12, knee, 0.07, 'coat');
      cap(knee, 0.06, hock, 0.038, 'coat');
      cap(hock, 0.036, add(lg.paw, mul(f, 0.05)), 0.04, 'tan');
    }
  }
  // tail: five segments; carriage from the score (0 high, 0.5 easy, 1.35 tucked), wag sweeps it sideways
  const tailBase = W(-0.41, hr + 0.03, 0);
  const carriage = keyed([[0, 35], [0.5, -32], [1.0, -62], [1.4, -78]], p.tail, false);
  let pt = tailBase; let ang = lerp(carriage, -5, lie * 0.9); let lat = 0;
  const sweep = p.wag * Math.sin(p.wagPh) * 38;
  for (let k = 0; k < 5; k++) {
    const segL = 0.085 * (1 - k * 0.04);
    ang += lerp(-6, 4, lie) - clamp(p.tail - 0.8, 0, 1) * 14;    // tucked tails curl under
    lat = sweep * (0.35 + k * 0.2);
    const yawT = (p.yaw + 180 + lat) * deg;
    const dir: V3 = norm([Math.cos(yawT) * Math.cos(ang * deg), Math.sin(ang * deg), Math.sin(yawT) * Math.cos(ang * deg)]);
    let nxt = add(pt, mul(dir, segL)); if (nxt[1] < 0.03) nxt = [nxt[0], 0.03, nxt[2]];
    cap(pt, 0.05 + 0.012 * Math.sin(k * 0.8), nxt, 0.052 + 0.01 * Math.sin((k + 1) * 0.8) - (k === 4 ? 0.02 : 0), k === 4 ? 'saddle' : 'coat');
    pt = nxt;
  }
  return parts;
}
