// SCION 41 · Secondary Dynamics — the dynamics component library (v1).
// First-class primitives: springs, dampers, mass proxies, discrete/continuous integrators, collision boundaries,
// primary pose impulses. Units: metres, seconds, kilograms, radians. World axes: X along the porch (score x; the
// threshold at 0, outside positive), Y up, Z across the porch (positive toward the camera). Time base: the scene runs
// at 24 fps; every solver here is sub-stepped inside a frame (SUB substeps), never across frames.
'use strict';

const V = {
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
  sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
  mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
  dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
  len: a => Math.hypot(a[0], a[1], a[2]),
  norm: a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; },
  lerp: (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t],
  cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
};

// ---- material priors: natural frequency f (Hz), damping ratio zeta, mass proxy m (kg), air drag (1/s) --------------
// One prior per material; "none" is the no-secondary-motion alternative (the part follows its pose rigidly).
const MATERIALS = {
  hair:    { f: 2.4, zeta: 0.34, m: 0.03, drag: 0.8, note: 'tail plume: loose, follows late, two visible swings at most' },
  ear:     { f: 3.6, zeta: 0.30, m: 0.01, drag: 0.6, note: 'leather ear tip on a cartilage base: quick flick, settles in ~0.6 s' },
  fur:     { f: 3.0, zeta: 0.45, m: 0.02, drag: 0.5, note: 'coat tufts (ruff, belly fringe, breeches): small lag, no rebound' },
  cloth:   { f: 0.95, zeta: 0.22, m: 0.04, drag: 1.6, note: 'wool scarf: heavy, slow, swings and drapes' },
  paper:   { f: 1.6, zeta: 0.12, m: 0.002, drag: 5.0, note: 'paper note: light, air-dominated, flutters and lies flat' },
  wood:    { f: 0, zeta: 0, m: 14, drag: 0, note: 'door leaf: hinge inertia 3.9 kg·m², hinge friction, a doorstop that knocks' },
  foliage: { f: 2.2, zeta: 0.11, m: 0.05, drag: 0.4, note: 'shrub stems: springy, several decaying swings after contact' },
  metal:   { f: 0, zeta: 0.04, m: 0.008, drag: 0.15, note: 'collar tag: a pendulum that ticks against the chest' },
  none:    { f: Infinity, zeta: 1, m: 0, drag: 0, note: 'no secondary motion: follows the primary pose exactly' },
};
const omega = f => 2 * Math.PI * f;

// ---- continuous integrator: exact step of a linear damped oscillator x'' = -w²(x - x*) - 2ζw x' + a ------------------
// The closed-form solution over dt (target x* and forcing a held constant across the step). Unconditionally stable.
function exactStep(x, v, target, f, zeta, dt, a = 0) {
  const w = omega(f); if (!isFinite(w)) return [target, 0];
  const eq = target + a / (w * w); const y0 = x - eq;
  if (zeta < 1 - 1e-6) {
    const wd = w * Math.sqrt(1 - zeta * zeta), e = Math.exp(-zeta * w * dt), c = Math.cos(wd * dt), s = Math.sin(wd * dt);
    const A = y0, B = (v + zeta * w * y0) / wd;
    const y = e * (A * c + B * s);
    const vy = e * ((-zeta * w) * (A * c + B * s) + (-A * wd * s + B * wd * c));
    return [eq + y, vy];
  }
  if (zeta <= 1 + 1e-6) { // critical
    const e = Math.exp(-w * dt), A = y0, B = v + w * y0;
    return [eq + (A + B * dt) * e, (B - w * (A + B * dt)) * e];
  }
  const r = w * Math.sqrt(zeta * zeta - 1), r1 = -zeta * w + r, r2 = -zeta * w - r;
  const C2 = (v - r1 * y0) / (r2 - r1), C1 = y0 - C2;
  return [eq + C1 * Math.exp(r1 * dt) + C2 * Math.exp(r2 * dt), C1 * r1 * Math.exp(r1 * dt) + C2 * r2 * Math.exp(r2 * dt)];
}

// ---- discrete integrator: semi-implicit (symplectic) Euler for the same oscillator, for comparison and tests ---------
function eulerStep(x, v, target, f, zeta, dt, a = 0) {
  const w = omega(f); v += (-w * w * (x - target) - 2 * zeta * w * v + a) * dt; x += v * dt; return [x, v];
}

// ---- mass proxy: a 3D inertial offset (fur tuft, coat). Driven by its anchor's acceleration (the pseudo-force). -----
class MassProxy {
  constructor(mat, gain = 1) { this.m = MATERIALS[mat]; this.o = [0, 0, 0]; this.v = [0, 0, 0]; this.gain = gain; this.prev = null; this.prevV = null; }
  step(anchor, dt) { // anchor: world position this frame; returns offset (m)
    if (this.prev) {
      const va = V.mul(V.sub(anchor, this.prev), 1 / dt); const aa = this.prevV ? V.mul(V.sub(va, this.prevV), 1 / dt) : [0, 0, 0];
      for (let k = 0; k < 3; k++) [this.o[k], this.v[k]] = exactStep(this.o[k], this.v[k], 0, this.m.f, this.m.zeta, dt, -aa[k] * this.gain);
      this.prevV = va;
    }
    this.prev = anchor.slice(); return this.o;
  }
  energy() { const w = omega(this.m.f); return 0.5 * V.dot(this.v, this.v) + 0.5 * w * w * V.dot(this.o, this.o); }
}

// ---- collision boundaries ---------------------------------------------------------------------------------------
// plane {n, d}: n·p ≥ d.  sphere {c, r}: outside.  capsule {a, b, r}: outside.  Optional v: the boundary's velocity (m/s),
// so that contact speeds (and the sounds they make) are relative to a moving body, not to the world.
function closestOnSeg(p, a, b) { const ab = V.sub(b, a), t = Math.max(0, Math.min(1, V.dot(V.sub(p, a), ab) / (V.dot(ab, ab) || 1))); return V.add(a, V.mul(ab, t)); }
function resolve(p, r, col) { // returns {p, n, depth} or null when not penetrating
  if (col.type === 'plane') { const s = V.dot(col.n, p) - col.d - r; return s < 0 ? { p: V.sub(p, V.mul(col.n, s)), n: col.n, depth: -s } : null; }
  const c = col.type === 'sphere' ? col.c : closestOnSeg(p, col.a, col.b);
  const d = V.sub(p, c), L = V.len(d), R = col.r + r;
  if (L >= R) return null; const n = L > 1e-9 ? V.mul(d, 1 / L) : [0, 1, 0];
  return { p: V.add(c, V.mul(n, R)), n, depth: R - L };
}
function signedGap(p, r, col) { // + outside, − penetrating (for tests and the no-interpenetration assertion)
  if (col.type === 'plane') return V.dot(col.n, p) - col.d - r;
  const c = col.type === 'sphere' ? col.c : closestOnSeg(p, col.a, col.b); return V.len(V.sub(p, c)) - col.r - r;
}

// ---- spring chain: a hair / ear / cloth / foliage strand with pose springs, length constraints, collisions --------
// node 0 is kinematic (the anchor on the primary body). Every other node is a mass proxy pulled toward its pose target
// by a spring (frequency falls toward the tip), damped relative to the moving pose (follow) and against the air (drag).
class Chain {
  constructor(mat, n, opts = {}) {
    this.mat = mat; this.M = MATERIALS[mat]; this.n = n; this.opts = opts;
    this.p = null; this.v = null; this.rest = []; this.r = opts.r || Array(n).fill(0.01);
    this.tipSoft = opts.tipSoft ?? 0.55; this.g = opts.gravity ?? 9.81; this.events = []; this.stiff = opts.stiff || null;
  }
  init(targets) { this.p = targets.map(q => q.slice()); this.v = targets.map(() => [0, 0, 0]); this.rest = []; for (let i = 1; i < this.n; i++) this.rest.push(V.len(V.sub(targets[i], targets[i - 1]))); this.prevT = targets.map(q => q.slice()); }
  // targets: pose positions for every node this frame; colliders: list; dt frame time; sub substeps; tag for events
  step(targets, colliders, dt, sub = 8, t0 = 0) {
    if (!this.p) this.init(targets);
    if (this.M.f === Infinity) { this.p = targets.map(q => q.slice()); this.v = targets.map(() => [0, 0, 0]); this.prevT = targets.map(q => q.slice()); return; }
    const h = dt / sub;
    for (let s = 0; s < sub; s++) {
      const a = (s + 1) / sub, T = targets.map((q, i) => V.lerp(this.prevT[i], q, a)), Tp = targets.map((q, i) => V.lerp(this.prevT[i], q, s / sub));
      const prev = this.p.map(q => q.slice());
      this.p[0] = T[0].slice(); this.v[0] = V.mul(V.sub(T[0], Tp[0]), 1 / h);
      for (let i = 1; i < this.n; i++) {
        const u = (i - 1) / Math.max(1, this.n - 2), f = this.stiff ? this.stiff[i] : this.M.f * (1 - this.tipSoft * u), w = omega(f), z = this.M.zeta;
        const vt = V.mul(V.sub(T[i], Tp[i]), 1 / h); // pose velocity
        const acc = V.add(V.add(V.mul(V.sub(T[i], this.p[i]), w * w), V.mul(V.sub(vt, this.v[i]), 2 * z * w)), V.add([0, -this.g * (this.opts.sag ?? 0.15), 0], V.mul(this.v[i], -this.M.drag)));
        this.v[i] = V.add(this.v[i], V.mul(acc, h)); this.p[i] = V.add(this.p[i], V.mul(this.v[i], h));
      }
      for (let it = 0; it < 3; it++) for (let i = 1; i < this.n; i++) { // inextensible segments (PBD projection)
        const d = V.sub(this.p[i], this.p[i - 1]), L = V.len(d) || 1e-9, e = (L - this.rest[i - 1]) / L;
        if (i === 1) this.p[i] = V.sub(this.p[i], V.mul(d, e)); else { this.p[i] = V.sub(this.p[i], V.mul(d, e * 0.5)); this.p[i - 1] = V.add(this.p[i - 1], V.mul(d, e * 0.5)); }
      }
      if (!this.touch) this.touch = {};
      for (let i = 1; i < this.n; i++) for (let ci = 0; ci < colliders.length; ci++) { // collision boundaries: project out
        const c = colliders[ci], key = i * 64 + ci, hit = resolve(this.p[i], this.r[i], c);
        if (!hit) { if (this.touch[key] && signedGap(this.p[i], this.r[i], c) > 0.008) this.touch[key] = 0; continue; } // hysteresis: a contact ends only 8 mm clear
        const vn = V.dot(V.sub(V.mul(V.sub(this.p[i], prev[i]), 1 / h), c.v || [0, 0, 0]), hit.n); this.p[i] = hit.p; // normal speed relative to the (moving) boundary
        if (!this.touch[key] && vn < -0.05 && c.tag) this.events.push({ t: t0 + (s + 1) * h, tag: c.tag, node: i, speed: -vn }); // contact onset only
        this.touch[key] = 1;
      }
      for (let i = 1; i < this.n; i++) this.v[i] = V.mul(V.sub(this.p[i], prev[i]), 1 / h); // velocities from positions
    }
    this.prevT = targets.map(q => q.slice());
  }
  // secondary energy: kinetic energy relative to the pose's own motion (zero when the strand rides its pose rigidly)
  energy(targets, vtargets) { let e = 0; for (let i = 1; i < this.n; i++) { const dv = V.sub(this.v[i], vtargets ? vtargets[i] : [0, 0, 0]); e += 0.5 * V.dot(dv, dv); } return e; }
}

// ---- hinge: a rotational mass-spring-damper with friction and a limit (the door leaf, a stem) ----------------------
class Hinge {
  constructor({ I, k = 0, c = 0, friction = 0, min = -Infinity, max = Infinity, restitution = 0.3, tag = 'hinge' }) {
    Object.assign(this, { I, k, c, friction, min, max, restitution, tag }); this.a = 0; this.w = 0; this.target = 0; this.events = []; this.pending = 0;
  }
  impulse(J) { this.pending += J; } // primary pose impulse (N·m·s)
  step(dt, sub = 8, t0 = 0, torque = 0) {
    const h = dt / sub;
    for (let s = 0; s < sub; s++) {
      this.w += this.pending / this.I; this.pending = 0;
      let tq = torque - this.k * (this.a - this.target) - this.c * this.w;
      if (Math.abs(this.w) > 1e-4) tq -= Math.sign(this.w) * this.friction; else if (Math.abs(tq) <= this.friction) { this.w = 0; continue; }
      const w0 = this.w; this.w += tq / this.I * h;
      if (w0 !== 0 && Math.sign(this.w) !== Math.sign(w0) && Math.abs(torque - this.k * (this.a - this.target)) <= this.friction) this.w = 0; // static friction holds
      this.a += this.w * h;
      if (this.a > this.max) { this.a = this.max; if (this.w > 0.05) this.events.push({ t: t0 + (s + 1) * h, tag: this.tag + '-stop', speed: this.w }); this.w = -this.w * this.restitution; }
      if (this.a < this.min) { this.a = this.min; if (this.w < -0.05) this.events.push({ t: t0 + (s + 1) * h, tag: this.tag + '-close', speed: -this.w }); this.w = -this.w * this.restitution; }
    }
  }
  energy() { return 0.5 * this.I * this.w * this.w; }
}

module.exports = { V, MATERIALS, omega, exactStep, eulerStep, MassProxy, Chain, Hinge, resolve, signedGap, closestOnSeg };
