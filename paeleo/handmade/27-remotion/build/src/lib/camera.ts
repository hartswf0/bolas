// The camera: pin-hole, 1280x720, a pure function of scene time. World: X along the porch (metres, = score x),
// Y up, Z across the porch (+Z toward the camera side). Wide and still until 15.4 s; then, while the dog comes,
// a slow push-in (zoom 1500 → 2550 px, a small dolly) to the doorway (15.4 → 23.6 s); held to the end. The dog's world X is measured back through this
// camera from the matte (x_world_measured), so the checker can follow it while the camera moves.
import type {V3, V2} from './math.ts';
import {sub, dot, norm, cross, mix3, ramp} from './math.ts';
export const W = 1280, H = 720;
const WIDE = {pos: [6.0, 1.3, 5.6] as V3, target: [2.0, 0.6, -0.5] as V3};
const NEAR = {pos: [5.6, 1.25, 5.2] as V3, target: [0.95, 0.55, -0.6] as V3};
export const camAt = (t: number) => {
  const u = ramp(t, 15.4, 23.6);
  return {pos: mix3(WIDE.pos, NEAR.pos, u), target: mix3(WIDE.target, NEAR.target, u), focal: 1500 + 1050 * u};
};
type Cam = {pos: V3; target: V3; focal: number; fwd: V3; right: V3; up: V3};
const build = (c: {pos: V3; target: V3; focal: number}): Cam => {
  const fwd = norm(sub(c.target, c.pos)); const right = norm(cross(fwd, [0, 1, 0])); return {...c, fwd, right, up: cross(right, fwd)};
};
// the current camera: set once per frame by <Scene> (and by the solver/measure) before anything is projected
let C: Cam = build(camAt(0));
export const setCameraTime = (t: number) => { C = build(camAt(t)); };
export const CAM = {get pos() { return C.pos; }, get focal() { return C.focal; }};
/** world point → [sx, sy, depth]; depth in metres along the view axis */
export const project = (p: V3): [number, number, number] => {
  const d = sub(p, C.pos); const z = dot(d, C.fwd);
  return [W / 2 + C.focal * dot(d, C.right) / z, H / 2 - C.focal * dot(d, C.up) / z, z];
};
/** screen point → world X on the horizontal plane through the dog's line (Z = z0) at height y0: the inverse used by measure */
export const unprojectToZ = (sx: number, sy: number, z0: number) => {
  const dir = norm([C.fwd[0] + ((sx - W / 2) / C.focal) * C.right[0] - ((sy - H / 2) / C.focal) * C.up[0],
    C.fwd[1] + ((sx - W / 2) / C.focal) * C.right[1] - ((sy - H / 2) / C.focal) * C.up[1],
    C.fwd[2] + ((sx - W / 2) / C.focal) * C.right[2] - ((sy - H / 2) / C.focal) * C.up[2]]);
  const s = (z0 - C.pos[2]) / dir[2]; return [C.pos[0] + dir[0] * s, C.pos[1] + dir[1] * s, z0];
};
export const p2 = (p: V3): V2 => { const q = project(p); return [q[0], q[1]]; };
export const scaleAt = (p: V3) => C.focal / project(p)[2];
export const poly = (pts: V3[]) => pts.map(p => p2(p).map(v => v.toFixed(1)).join(',')).join(' ');
const NEARZ = 0.15;
const depthOf = (p: V3) => dot(sub(p, C.pos), C.fwd);
/** clip a polygon against the near plane (Sutherland–Hodgman), so geometry behind the lens never folds onto the screen */
export const clipNear = (pts: V3[]): V3[] => {
  const out: V3[] = [];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length], da = depthOf(a) - NEARZ, db = depthOf(b) - NEARZ;
    if (da >= 0) out.push(a);
    if ((da >= 0) !== (db >= 0)) { const u = da / (da - db); out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u]); }
  }
  return out;
};
export const pathOf = (pts: V3[]) => { const q = clipNear(pts); return q.length < 3 ? '' : 'M' + q.map(p => p2(p).map(v => v.toFixed(1)).join(',')).join('L') + 'Z'; };
/** a clipped segment as [x1, y1, x2, y2] or null */
export const seg = (a: V3, b: V3): [number, number, number, number] | null => {
  let da = depthOf(a) - NEARZ, db = depthOf(b) - NEARZ;
  if (da < 0 && db < 0) return null;
  if (da < 0) { const u = da / (da - db); a = [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u]; }
  else if (db < 0) { const u = db / (db - da); b = [b[0] + (a[0] - b[0]) * u, b[1] + (a[1] - b[1]) * u, b[2] + (a[2] - b[2]) * u]; }
  const p = p2(a), q = p2(b); return [p[0], p[1], q[0], q[1]];
};
/** screen offset of a very distant point relative to the opening camera: the sky and tree line move by this (parallax ~ 0) */
const farDir = (c: Cam): [number, number] => { const d: V3 = [-400, 0, -760]; const z = dot(d, c.fwd);
  return [W / 2 + c.focal * dot(d, c.right) / z, H / 2 - c.focal * dot(d, c.up) / z]; };
const FAR0 = farDir(build(camAt(0)));
export const farShift = (): [number, number] => { const f = farDir(C); return [f[0] - FAR0[0], f[1] - FAR0[1]]; };
