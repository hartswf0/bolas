// 2-D drawing primitives for projected capsules. A capsule = two discs and their outer tangents.
import type {V3} from '../lib/math.ts';
import {project, CAM} from '../lib/camera.ts';
export type Cap2 = {x1: number; y1: number; r1: number; x2: number; y2: number; r2: number; depth: number};
export const cap2 = (a: V3, ra: number, b: V3, rb: number, grow = 0): Cap2 => {
  const p = project(a), q = project(b);
  return {x1: p[0], y1: p[1], r1: ra * CAM.focal / p[2] + grow, x2: q[0], y2: q[1], r2: rb * CAM.focal / q[2] + grow, depth: (p[2] + q[2]) / 2};
};
const f = (v: number) => v.toFixed(1);
export const capPath = (c: Cap2) => {
  const dx = c.x2 - c.x1, dy = c.y2 - c.y1, d = Math.hypot(dx, dy);
  const circ = (x: number, y: number, r: number) => `M${f(x - r)},${f(y)}a${f(r)},${f(r)} 0 1,0 ${f(2 * r)},0a${f(r)},${f(r)} 0 1,0 ${f(-2 * r)},0Z`;
  if (d < Math.abs(c.r1 - c.r2) + 0.01) return c.r1 >= c.r2 ? circ(c.x1, c.y1, c.r1) : circ(c.x2, c.y2, c.r2);
  const ux = dx / d, uy = dy / d, nx = -uy, ny = ux;
  const s = (c.r1 - c.r2) / d, co = Math.sqrt(Math.max(0, 1 - s * s));
  const ax = nx * co + ux * s, ay = ny * co + uy * s, bx = -nx * co + ux * s, by = -ny * co + uy * s;
  const p1 = [c.x1 + ax * c.r1, c.y1 + ay * c.r1], p2 = [c.x2 + ax * c.r2, c.y2 + ay * c.r2];
  const p3 = [c.x2 + bx * c.r2, c.y2 + by * c.r2], p4 = [c.x1 + bx * c.r1, c.y1 + by * c.r1];
  const big2 = s < 0 ? 1 : 0, big1 = s > 0 ? 1 : 0;
  return `M${f(p1[0])},${f(p1[1])}L${f(p2[0])},${f(p2[1])}A${f(c.r2)},${f(c.r2)} 0 ${big2},0 ${f(p3[0])},${f(p3[1])}L${f(p4[0])},${f(p4[1])}A${f(c.r1)},${f(c.r1)} 0 ${big1},0 ${f(p1[0])},${f(p1[1])}Z`;
};
/** mix two #rrggbb colours */
export const mixc = (a: string, b: string, t: number) => {
  const pa = [1, 3, 5].map(i => parseInt(a.slice(i, i + 2), 16)), pb = [1, 3, 5].map(i => parseInt(b.slice(i, i + 2), 16));
  return '#' + pa.map((v, i) => Math.round(v + (pb[i] - v) * Math.max(0, Math.min(1, t))).toString(16).padStart(2, '0')).join('');
};
