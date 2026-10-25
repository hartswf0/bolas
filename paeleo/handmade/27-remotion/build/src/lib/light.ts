// The doorway light as geometry: a wedge cast from the lamp through the unblocked part of the opening onto the porch.
import type {V3} from './math.ts';
import {clamp, smooth} from './math.ts';
import {WORLD, spillInterval, floorHit} from './world.ts';
export const spillPoly = (angle: number, xEnd = WORLD.porch.x1): V3[] => {
  const [z1, z2] = spillInterval(angle);
  const a = floorHit(z1, WORLD.wallOut), b = floorHit(z2, WORLD.wallOut), c = floorHit(z2, xEnd), d = floorHit(z1, xEnd);
  const cl = (p: V3): V3 => [p[0], 0.002, clamp(p[2], WORLD.porch.z0, WORLD.porch.z1)];
  return [cl(a), cl(b), cl(c), cl(d)];
};
/** light reaching a point on/above the porch (plan), 0..1 before the lamp level */
export const spillAt = (X: number, Z: number, angle: number) => {
  if (X < WORLD.wallOut - 0.05) return 0.9;                   // inside the frame: lit
  const [z1, z2] = spillInterval(angle);
  const lo = floorHit(z1, X)[2], hi = floorHit(z2, X)[2];
  const edge = 0.08 + 0.03 * X;
  const inside = smooth((Z - lo) / edge + 0.5) * smooth((hi - Z) / edge + 0.5);
  return inside / (1 + 0.32 * (X - WORLD.wallOut));
};
/** project a point from the lamp onto the floor (for cast shadows) */
export const shadowOf = (p: V3): V3 => {
  const L = WORLD.lamp; const s = L[1] / Math.max(0.05, L[1] - p[1]);
  return [L[0] + (p[0] - L[0]) * s, 0.003, L[2] + (p[2] - L[2]) * s];
};
