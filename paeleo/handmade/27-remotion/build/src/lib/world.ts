// The place, as data. Metres. The score's sill (0.56) lies on the threshold stone: the dog's body centre lies at
// score x = 0.59, so its chest and head are inside the door frame (X < 0.50) and its hindquarters and tail on the porch.
import type {V3} from './math.ts';
export const WORLD = {
  wallOut: 0.50, wallIn: 0.34,             // façade outer and inner face (plane X = const)
  door: {z0: -0.48, z1: 0.48, h: 2.06},     // opening in Z, height
  sill: {x0: 0.34, x1: 0.64, h: 0.045},     // threshold stone
  porch: {x1: 4.9, z0: -1.9, z1: 1.6},      // porch boards end at the steps (score porch_end 4.9)
  room: {x0: -3.6, z0: -1.9, z1: 1.9, h: 2.7},
  lamp: [-1.7, 2.45, 0.25] as V3,           // the interior light: the spill is cast from here through the opening
  dogZ: -0.30,                              // the dog's line across the porch
  hingeZ: 0.48,                             // the door hangs on the near jamb and swings into the room
};
/** door leaf angle (deg, into the room): ajar 55, open 106 */
export const doorAngle = (open01: number) => 55 + 51 * open01;
/** plan-view unblocked interval of the opening seen from the lamp, given the door angle; returns [zmin, zmax] at X = wallOut */
export const spillInterval = (angDeg: number): [number, number] => {
  const L = WORLD.lamp, a = angDeg * Math.PI / 180;
  const hx = WORLD.wallIn, hz = WORLD.hingeZ;
  const ex = hx - 0.96 * Math.sin(a), ez = hz - 0.96 * Math.cos(a);   // free edge of the leaf (plan)
  const ok: number[] = [];
  for (let i = 0; i <= 96; i++) {
    const z = WORLD.door.z0 + (WORLD.door.z1 - WORLD.door.z0) * i / 96;
    // ray lamp → (wallOut, z); blocked if it crosses the leaf segment (hx,hz)-(ex,ez) or a jamb at the inner face
    const zin = L[2] + (z - L[2]) * (WORLD.wallIn - L[0]) / (WORLD.wallOut - L[0]);
    if (zin < WORLD.door.z0 || zin > WORLD.door.z1) continue;
    const dx = WORLD.wallOut - L[0], dz = z - L[2], sx = ex - hx, sz = ez - hz;
    const den = dx * sz - dz * sx; let blocked = false;
    if (Math.abs(den) > 1e-9) {
      const t = ((hx - L[0]) * sz - (hz - L[2]) * sx) / den, u = ((hx - L[0]) * dz - (hz - L[2]) * dx) / den;
      blocked = t > 0 && t < 1 && u > 0 && u < 1;
    }
    if (!blocked) ok.push(z);
  }
  return ok.length ? [Math.min(...ok), Math.max(...ok)] : [0, 0];
};
/** where the ray from the lamp through (wallOut, y, z) meets the floor, plan coords */
export const floorHit = (z: number, X: number): V3 => {
  const L = WORLD.lamp; const s = (X - L[0]) / (WORLD.wallOut - L[0]);
  return [X, 0, L[2] + (z - L[2]) * s];
};
