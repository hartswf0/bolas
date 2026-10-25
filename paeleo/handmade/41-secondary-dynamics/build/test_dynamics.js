// Unit tests for the dynamics library.  node build/test_dynamics.js   (exit code 1 on any failure)
'use strict';
const D = require('./dynamics.js'); const { V } = D;
let fails = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fails++; };

// 1. the continuous (exact) integrator matches the analytic underdamped solution at any step size
{ const f = 2, z = 0.2, w = 2 * Math.PI * f, wd = w * Math.sqrt(1 - z * z); let x = 1, v = 0; const dt = 1 / 24;
  for (let i = 0; i < 48; i++) [x, v] = D.exactStep(x, v, 0, f, z, dt);
  const t = 2, xa = Math.exp(-z * w * t) * (Math.cos(wd * t) + z * w / wd * Math.sin(wd * t));
  ok(Math.abs(x - xa) < 1e-9, `exact step = analytic oscillator after 2 s (err ${Math.abs(x - xa).toExponential(1)})`); }
// 2. critically and over-damped branches are continuous with the underdamped one near zeta = 1
{ const a = D.exactStep(1, 0, 0, 2, 0.999, 0.1), b = D.exactStep(1, 0, 0, 2, 1, 0.1), c = D.exactStep(1, 0, 0, 2, 1.001, 0.1);
  ok(Math.abs(a[0] - b[0]) < 1e-3 && Math.abs(c[0] - b[0]) < 1e-3, 'damping branches agree near critical'); }
// 3. the discrete integrator converges to the continuous one as the step shrinks, and blows up when too coarse at high f
{ let x = 1, v = 0, y = 1, u = 0; for (let i = 0; i < 2400; i++) [x, v] = D.eulerStep(x, v, 0, 3, 0.3, 1 / 2400); for (let i = 0; i < 24; i++) [y, u] = D.exactStep(y, u, 0, 3, 0.3, 1 / 24);
  ok(Math.abs(x - y) < 2e-3, 'semi-implicit Euler at 1/2400 s ≈ exact at 1/24 s');
  let p = 1, q = 0; for (let i = 0; i < 48; i++) [p, q] = D.eulerStep(p, q, 0, 9, 0.05, 1 / 24);
  ok(!(Math.abs(p) < 10), 'Euler at 1/24 s on a 9 Hz spring is unstable (why the chains sub-step)'); }
// 4. energy of every material decays to < 1e-4 of its start within 3 s once the source stops
for (const m of ['hair', 'ear', 'fur', 'cloth', 'paper', 'foliage']) {
  const M = D.MATERIALS[m]; let x = 0.1, v = 0; const w = 2 * Math.PI * M.f, E0 = 0.5 * w * w * x * x, ze = M.zeta + M.drag / (2 * w); // air drag adds damping
  for (let i = 0; i < 72; i++) [x, v] = D.exactStep(x, v, 0, M.f, ze, 1 / 24);
  const E = 0.5 * v * v + 0.5 * w * w * x * x; ok(E / E0 < 1e-4, `${m}: energy ratio after 3 s ${(E / E0).toExponential(1)}`);
}
// 5. a chain released from a swung pose settles (energy → 0) and never goes through the floor
{ const c = new D.Chain('hair', 6, { r: Array(6).fill(0.02), sag: 1 }); const tg = []; for (let i = 0; i < 6; i++) tg.push([i * 0.07, 0.3, 0]);
  c.init(tg); c.v = c.v.map((v, i) => [0, -3 * i, 0]); let minGap = 1, E = []; const floor = { type: 'plane', n: [0, 1, 0], d: 0, tag: 'floor' };
  for (let f = 0; f < 120; f++) { c.step(tg, [floor], 1 / 24, 8, f / 24); for (let i = 1; i < 6; i++) minGap = Math.min(minGap, D.signedGap(c.p[i], c.r[i], floor)); E.push(c.energy()); }
  ok(minGap > -1e-6, `chain never penetrates the floor (min gap ${minGap.toFixed(5)} m)`);
  ok(E[E.length - 1] < 1e-4 * Math.max(...E), `chain energy decays (last/peak ${(E[E.length - 1] / Math.max(...E)).toExponential(1)})`);
  ok(c.events.length > 0, `floor contacts reported as sound events (${c.events.length})`);
  let maxStretch = 0; for (let i = 1; i < 6; i++) maxStretch = Math.max(maxStretch, Math.abs(V.len(V.sub(c.p[i], c.p[i - 1])) - c.rest[i - 1]));
  ok(maxStretch < 2e-3, `segments stay inextensible (max stretch ${(maxStretch * 1000).toFixed(2)} mm)`); }
// 6. follow-through: a chain's tip responds after its anchor moves (momentum response begins after primary motion)
{ const c = new D.Chain('hair', 6, { r: Array(6).fill(0.01) }); const pose = x => [0, 1, 2, 3, 4, 5].map(i => [x + i * 0.07, 0.5, 0]);
  c.init(pose(0)); let tipLagFrames = null, anchorStart = 2;
  for (let f = 0; f < 48; f++) { const x = f < anchorStart ? 0 : Math.min(0.3, (f - anchorStart) * 0.05); c.step(pose(x), [], 1 / 24, 8);
    const dev = c.p[5][0] - pose(x)[5][0]; if (tipLagFrames === null && Math.abs(dev) > 0.01) tipLagFrames = f - anchorStart; }
  ok(tipLagFrames !== null && tipLagFrames >= 1, `tip deviation appears ${tipLagFrames} frame(s) after the anchor starts`); }
// 7. the door hinge stops at its doorstop with a knock, rebounds less, and comes to rest (friction)
{ const h = new D.Hinge({ I: 3.9, c: 0.6, friction: 0.9, min: 0, max: 1.75, restitution: 0.3, tag: 'door' }); h.impulse(9);
  for (let f = 0; f < 96; f++) h.step(1 / 24, 8, f / 24);
  ok(h.events.some(e => e.tag === 'door-stop'), 'door knocks on its stop'); ok(h.a <= 1.75 && h.a > 1.0 && h.w === 0, `door rests open at ${h.a.toFixed(2)} rad, ω=0`); }
// 8. collision resolution: sphere and capsule boundaries push a point exactly to their surface
{ const s = D.resolve([0, 0.05, 0], 0.01, { type: 'sphere', c: [0, 0, 0], r: 0.1 }); ok(Math.abs(V.len(s.p) - 0.11) < 1e-9, 'sphere boundary');
  const q = D.resolve([0.5, 0.02, 0], 0, { type: 'capsule', a: [0, 0, 0], b: [1, 0, 0], r: 0.05 }); ok(Math.abs(q.p[1] - 0.05) < 1e-9, 'capsule boundary'); }
// 9. mass proxy: no offset while the anchor moves at constant velocity; offset opposite to acceleration; decays at rest
{ const p = new D.MassProxy('fur'); let o; for (let f = 0; f < 24; f++) o = p.step([f * 0.02, 0, 0], 1 / 24); ok(Math.abs(o[0]) < 1e-3, 'proxy quiet at constant velocity');
  const q = new D.MassProxy('fur'); for (let f = 0; f < 8; f++) o = q.step([0.5 * (f / 24) ** 2 * 6, 0, 0], 1 / 24); ok(o[0] < 0, 'proxy lags behind an acceleration');
  for (let f = 0; f < 72; f++) o = q.step([1, 0, 0], 1 / 24); ok(q.energy() < 1e-6, 'proxy energy decays at rest'); }
console.log(fails ? `${fails} FAILED` : 'all dynamics tests pass'); process.exit(fails ? 1 : 0);
