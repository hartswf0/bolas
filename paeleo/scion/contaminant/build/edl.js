/* SCION 093 · the paired editors. Two edit-decision lists from one shared source take (../rushes/film.mp4, frame record
   ../rushes/meta.json), each exactly the same length, in source order, with no added footage.
   A, the censor's cut, keeps the delivery: the jellyfish lifting, carrying and handing fragments on, and the clockwork
   school's images, briefly. The care strand never appears.
   B, the jellyfish's cut, keeps the peripheral life: the care strand's people and the archive's, held for their full
   length, with the moment before each opens and the moment after it goes. The handoffs never appear.
   Writes ../film093/edl_A.json, edl_B.json, source_map.json and checks.json. */
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..'), out = path.join(root, 'film093');
const { fps, frames, meta } = JSON.parse(fs.readFileSync(path.join(root, 'rushes', 'meta.json'), 'utf8'));
const D = 28, TARGET = D * fps, MINRUN = Math.round(.6 * fps), SKIP_OPEN = Math.round(1.6 * fps);  // skip the take's fade-in
fs.mkdirSync(out, { recursive: true });

// annotate each source frame: what it shows and what it is for
const ann = meta.map((m, i) => {
  if (i < SKIP_OPEN) return 'opening';
  if (m.shot === 'insert') return m.strand === 'pink' ? 'care' : m.strand === 'school' ? 'school' : 'archive';
  return {handoff: 'handoff', lift: 'lift', carry: 'carry', return: 'return'}[m.jelly] || 'forage';
});
// insert runs, so an editor can take the head of one, or the moment before or after it
const runs = []; for (let i = 0; i < frames; i++) if (!runs.length || ann[i] !== ann[i - 1]) runs.push({a: i, b: i + 1, k: ann[i]}); else runs[runs.length - 1].b = i + 1;

function cut(priorities, forbid = []) {
  const take = new Uint8Array(frames); let n = 0;
  const add = (a, b) => { for (let i = Math.max(0, a); i < Math.min(frames, b) && n < TARGET; i++) if (!take[i] && ann[i] !== 'opening' && !forbid.includes(ann[i])) { take[i] = 1; n++; } };
  for (const p of priorities) for (const r of runs) p(r, add);
  // no fragment shorter than MINRUN: drop slivers, then grow surviving runs forward until the length is exact
  let ivs = toIntervals(take);
  for (const iv of ivs) if (iv.b - iv.a < MINRUN) for (let i = iv.a; i < iv.b; i++) { take[i] = 0; n--; }
  for (let pass = 0; n < TARGET && pass < 200; pass++) for (const iv of toIntervals(take)) { if (n >= TARGET) break; const i = iv.b; if (i < frames && !take[i] && ann[i] !== 'opening' && !forbid.includes(ann[i])) { take[i] = 1; n++; } }
  return toIntervals(take);
}
function toIntervals(take) { const r = []; for (let i = 0; i < frames; i++) if (take[i]) { if (r.length && r[r.length - 1].b === i) r[r.length - 1].b++; else r.push({a: i, b: i + 1}); } return r; }

const A = cut([
  (r, add) => { if (r.k === 'handoff' || r.k === 'lift') add(r.a, r.b); },
  (r, add) => { if (r.k === 'school') add(r.a, r.a + Math.round(1.6 * fps)); },
  (r, add) => { if (r.k === 'carry' || r.k === 'return') add(r.a, r.b); },
], ['care', 'archive']);   // the censor never shows the care strand, nor the archive's people
const B = cut([
  (r, add) => { if (r.k === 'care') add(r.a, r.b); },
  (r, add) => { if (r.k === 'archive') add(r.a, r.b); },
  (r, add) => { if (r.k === 'care' || r.k === 'archive') { add(r.b, r.b + Math.round(1.1 * fps)); add(r.a - Math.round(.9 * fps), r.a); } },
  (r, add) => { if (r.k === 'forage' || r.k === 'return') add(r.a, r.b); },
], ['school', 'handoff', 'lift', 'carry']);   // B leaves the jellyfish's work out: it appears only drifting between people

const label = iv => { const c = {}; for (let i = iv.a; i < iv.b; i++) c[ann[i]] = (c[ann[i]] || 0) + 1; return Object.entries(c).sort((x, y) => y[1] - x[1]).map(([k]) => k).join('+'); };
const edl = (name, ivs) => ({version: name, source: 'rushes/film.mp4', fps, frames: ivs.reduce((s, v) => s + v.b - v.a, 0),
  intervals: ivs.map(iv => ({in_frame: iv.a, out_frame: iv.b, in_s: +(iv.a / fps).toFixed(4), out_s: +(iv.b / fps).toFixed(4), shows: label(iv)}))});
const eA = edl('A, the censor\'s cut: the delivery', A), eB = edl('B, the jellyfish\'s cut: the peripheral life', B);
fs.writeFileSync(path.join(out, 'edl_A.json'), JSON.stringify(eA, null, 1));
fs.writeFileSync(path.join(out, 'edl_B.json'), JSON.stringify(eB, null, 1));

// the source-time map: for each annotated stretch of the take, which version keeps how much of it
const inA = new Uint8Array(frames), inB = new Uint8Array(frames);
for (const v of A) for (let i = v.a; i < v.b; i++) inA[i] = 1;
for (const v of B) for (let i = v.a; i < v.b; i++) inB[i] = 1;
const map = runs.map(r => { let a = 0, b = 0; for (let i = r.a; i < r.b; i++) { a += inA[i]; b += inB[i]; } return {from_s: +(r.a / fps).toFixed(3), to_s: +(r.b / fps).toFixed(3), shows: r.k, kw: meta[r.a].kw, kept_by_A_s: +(a / fps).toFixed(2), kept_by_B_s: +(b / fps).toFixed(2)}; });
fs.writeFileSync(path.join(out, 'source_map.json'), JSON.stringify({source: 'rushes/film.mp4', fps, source_frames: frames, map}, null, 1));

// checks: same pool, in range, in source order, exact and equal length; and what each version gives its time to
const share = (ivs, k) => +(ivs.reduce((s, v) => { let c = 0; for (let i = v.a; i < v.b; i++) c += ann[i] === k; return s + c; }, 0) / fps).toFixed(2);
const kinds = ['care', 'archive', 'school', 'handoff', 'lift', 'carry', 'return', 'forage'];
const checks = {
  same_source_pool: true, in_range: [...A, ...B].every(v => v.a >= 0 && v.b <= frames),
  source_order: [A, B].every(ivs => ivs.every((v, i) => !i || ivs[i - 1].b <= v.a)),
  frames_A: eA.frames, frames_B: eB.frames, equal_length: eA.frames === eB.frames && eA.frames === TARGET,
  splices_A: A.length - 1, splices_B: B.length - 1,
  shared_source_s: +(Array.from(inA).reduce((s, x, i) => s + (x && inB[i]), 0) / fps).toFixed(2),
  seconds_by_kind: Object.fromEntries(kinds.map(k => [k, {A: share(A, k), B: share(B, k)}]))};
fs.writeFileSync(path.join(out, 'checks.json'), JSON.stringify(checks, null, 1));
console.log(JSON.stringify(checks, null, 1));
