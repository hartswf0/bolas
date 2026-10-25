// SCION-27 shared math. Pure functions only: everything in this film is a function of (frame, manifest, seed).
export type V3 = [number, number, number];
export type V2 = [number, number];
export const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const smooth = (t: number) => { t = clamp(t); return t * t * (3 - 2 * t); };
export const ramp = (t: number, t0: number, t1: number) => smooth((t - t0) / (t1 - t0));
export const add = (a: V3, b: V3): V3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
export const mul = (a: V3, s: number): V3 => [a[0] * s, a[1] * s, a[2] * s];
export const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
export const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
export const len = (a: V3) => Math.hypot(a[0], a[1], a[2]);
export const norm = (a: V3): V3 => { const l = len(a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
export const mix3 = (a: V3, b: V3, t: number): V3 => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
export const deg = Math.PI / 180;
/** piecewise-linear keyed curve: keys [[x, y], ...] sorted by x; smooth between keys */
export const keyed = (keys: [number, number][], x: number, ease = true) => {
  if (x <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (x <= keys[i][0]) {
    const [x0, y0] = keys[i - 1], [x1, y1] = keys[i]; const u = (x - x0) / (x1 - x0);
    return lerp(y0, y1, ease ? smooth(u) : u);
  }
  return keys[keys.length - 1][1];
};
/** deterministic hash noise in [0,1): same seed+key → same value on every machine */
export const hash = (seed: number, k: number) => { let h = (seed * 374761393 + k * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177 | 0; h ^= h >>> 16; return ((h >>> 0) % 100000) / 100000; };
/** smooth 1-D value noise from the hash: continuous in t */
export const vnoise = (seed: number, t: number) => { const i = Math.floor(t), u = smooth(t - i); return lerp(hash(seed, i), hash(seed, i + 1), u); };
