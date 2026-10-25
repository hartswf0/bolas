// The camera: fixed, pin-hole, 1280x720. World: X along the porch (metres, = score x; threshold region at X≈0.2..0.62),
// Y up, Z across the porch (+Z toward the camera side). The camera does not move, so x_screen is a monotone image of X.
import type {V3, V2} from './math.ts';
import {sub, dot, norm, cross} from './math.ts';
export const W = 1280, H = 720;
export const CAM = {pos: [6.0, 1.3, 5.6] as V3, target: [2.0, 0.6, -0.5] as V3, focal: 1500};
const fwd = norm(sub(CAM.target, CAM.pos));
const right = norm(cross(fwd, [0, 1, 0]));
const up = cross(right, fwd);
/** world point → [sx, sy, depth]; depth in metres along the view axis */
export const project = (p: V3): [number, number, number] => {
  const d = sub(p, CAM.pos); const z = dot(d, fwd);
  return [W / 2 + CAM.focal * dot(d, right) / z, H / 2 - CAM.focal * dot(d, up) / z, z];
};
export const p2 = (p: V3): V2 => { const q = project(p); return [q[0], q[1]]; };
export const scaleAt = (p: V3) => CAM.focal / project(p)[2];
export const poly = (pts: V3[]) => pts.map(p => p2(p).map(v => v.toFixed(1)).join(',')).join(' ');
export const pathOf = (pts: V3[]) => 'M' + pts.map(p => p2(p).map(v => v.toFixed(1)).join(',')).join('L') + 'Z';
