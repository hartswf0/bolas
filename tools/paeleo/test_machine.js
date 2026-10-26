// Model-based tests for the threshold dog (paeleo/threshold/machine.js). Run: node tools/paeleo/test_machine.js
// The bar from SCION-STATE-MACHINES: no unreachable or absorbing unintended states, choices conditioned on declared state,
// locomotion continuity, refusal has a visible consequence, and the dog is not a button (commands alone never earn approach).
const M = require('../../paeleo/threshold/machine.js');
const DT = 1 / 24;
let fails = 0, checks = 0;
const ok = (c, msg) => { checks++; if (!c) { fails++; console.log('FAIL', msg); } };
function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32); }
const pick = (r, a) => a[Math.floor(r() * a.length)];
const EARN = { posture: 'sit', place: 'beside', door: 'open', voice: 'none', hand: 'low' };

// 1. random operators: 400 episodes of 60 s, the world changing every 0.5 to 4 s
const seen = new Set(), pairs = new Set(), snaps = [];
for (let ep = 0; ep < 400; ep++) {
  const r = rng(1000 + ep), d = M.create(), w = Object.assign({}, M.WORLD); let next = 0, prevX = d.x, prevV = d.v;
  for (let i = 0; i < 60 * 24; i++) {
    if (d.t >= next) { const k = pick(r, Object.keys(M.OPTIONS)); w[k] = pick(r, M.OPTIONS[k]); next = d.t + 0.5 + r() * 3.5; }
    const before = d.state; M.step(d, w, DT); seen.add(d.state); if (before !== d.state) pairs.add(before + '>' + d.state);
    ok(Math.abs(d.x - prevX) <= 0.8 * DT + 1e-9, `ep ${ep} t ${d.t.toFixed(2)}: moved ${(d.x - prevX).toFixed(4)} m in one frame`);
    ok(Math.abs(d.v - prevV) <= 2.2 * DT + 1e-9, `ep ${ep}: speed jumped`);
    ok(d.x >= M.SILL - 1e-9 && d.x <= M.PORCH_END + 1e-9, `ep ${ep}: left the porch (x ${d.x})`);
    if (d.state === 'refuse') ok(d.face === -1, `ep ${ep}: refusing but still facing the person`);
    prevX = d.x; prevV = d.v;
    if (i % 97 === 0) snaps.push(JSON.parse(JSON.stringify(d)));
  }
}
for (const s of M.STATES) ok(seen.has(s), `state ${s} never reached`);
console.log('states reached:', [...seen].join(', '));
console.log('transitions seen:', [...pairs].sort().join(' '));

// 2. no absorbing states: from every snapshot, a patient operator (sit beside the open door, hand low, silent) earns the sill within 90 s
let worst = 0;
snaps.forEach((s, i) => {
  const d = Object.assign(M.create(), s); d.events = []; let t = 0;
  while (t < 90 && !(d.state === 'lie_down' && Math.abs(d.x - M.SILL) < 0.05)) { M.step(d, EARN, DT); t += DT; }
  worst = Math.max(worst, t);
  ok(t < 90, `snapshot ${i} (${s.state}, trust ${s.trust.toFixed(2)}, pressure ${s.pressure.toFixed(2)}) never reached the sill`);
});
console.log(`recovery: ${snaps.length} snapshots, slowest reached the sill in ${worst.toFixed(1)} s`);

// 3. not a button: a standing person in the doorway who calls, again and again, or reaches, never earns an approach
for (const w of [{ voice: 'call' }, { hand: 'reach' }, { voice: 'call', hand: 'reach' }]) {
  const d = M.create(); const world = Object.assign({}, M.WORLD, w); let approached = false;
  for (let i = 0; i < 60 * 24; i++) {
    if (w.voice === 'call') world.voice = (i % 96) < 30 ? 'call' : 'none';   // calls for 1.25 s every 4 s
    M.step(d, world, DT); if (d.state === 'approach') approached = true;
  }
  ok(!approached, `commands alone (${JSON.stringify(w)}) earned an approach`);
}

// 4. choices are conditioned on declared state: the same world gives different choices with different trust or memory
{ const w = Object.assign({}, M.WORLD, { posture: 'sit', place: 'beside', door: 'open' });
  const a = M.create({ trust: 0.2 }), b = M.create({ trust: 0.8 });
  for (let i = 0; i < 48; i++) { M.step(a, w, DT); M.step(b, w, DT); }
  ok(a.state !== 'approach' && b.state === 'approach', `trust does not change the choice (${a.state} / ${b.state})`);
  const c = M.create({ trust: 0.5 }), e = M.create({ trust: 0.5, refusals: 3 });
  let tc = 0, te = 0; const W = Object.assign({}, w, { hand: 'low' });
  while (c.state !== 'approach' && tc < 60) { M.step(c, W, DT); tc += DT; }
  while (e.state !== 'approach' && te < 60) { M.step(e, W, DT); te += DT; }
  ok(te > tc + 1, `a dog that has refused three times warms up no slower (${tc.toFixed(1)} s vs ${te.toFixed(1)} s)`);
  console.log(`memory: approach after ${tc.toFixed(1)} s, or ${te.toFixed(1)} s for a dog that has refused three times`); }

// 5. determinism: the film can be re-rendered from its timeline
{ const TL = [[1, { voice: 'call' }], [2, { voice: 'none' }], [5, { posture: 'sit', place: 'beside' }]];
  ok(JSON.stringify(M.run(TL, 20)) === JSON.stringify(M.run(TL, 20)), 'two runs of one timeline differ'); }

console.log(`${checks - fails}/${checks} checks passed`);
process.exit(fails ? 1 : 0);
