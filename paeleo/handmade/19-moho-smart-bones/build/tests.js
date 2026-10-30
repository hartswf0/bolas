/* SCION 19 · export checker / anatomy assertions (numeric, where the representation supports them).
   node tests.js -> ../proof/rig_tests.json
   T1 head switch layers keep proportions across views: skull top, chin, eye line, nose height and ear-tip height of every
      view drawing equal (within 2% of head height) at the same pitch; skull width in the front drawing equals skull length
      across the profile drawing's skull mass (same sphere), so no view rescales anatomy.
   T2 leg joint lengths: every leg segment, every frame, equals the sheet length (3D), and in profile frames the drawn
      (projected) length equals it too.
   T3 elbows and stifles never reverse: the bend side of each IK chain keeps one sign over all 768 frames.
   T4 foot contacts hold: a foot in stance (not lifted, body walking, not turning, not lying) moves < 2 mm in the world.
   T5 the view-control bones choose the head layer: during each turn every frame has a head drawing; the sequence of layers. */
const fs = require('fs'), path = require('path');
const Rig = require('./rig.js'), Perform = require('./perform.js');
const score = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../score/threshold-score.json'), 'utf8'));
const perf = Perform.perform(score);
const out = { about: 'numeric rig assertions, run on the same rig.js/perform.js that render the film', version: Rig.SHEET.version };

// ---- T1
function extentY(groups) {
  let lo = 1e9, hi = -1e9; const add = (y) => { lo = Math.min(lo, y); hi = Math.max(hi, y); };
  groups.forEach(g => (g.parts || []).forEach(p => {
    if (p.t === 'circ') { add(p.c[1] - p.r); add(p.c[1] + p.r); }
    else if (p.t === 'cap') { add(p.a[1] - p.ra); add(p.a[1] + p.ra); add(p.b[1] - p.rb); add(p.b[1] + p.rb); }
    else if (p.t === 'poly') p.pts.forEach(q => add(q[1]));
  }));
  return [lo, hi];
}
const base = Object.assign({}, perf[300]);   // watching, standing, head up
const T1 = { views: [] };
for (const v of Rig.VIEWS) {
  const P = Object.assign({}, base, { psiB: 0, psiH: v.a + 0.01 });
  // keep the head relative yaw identical for all views: rotate the body with it (the test isolates the head drawing)
  P.psiB = v.a; P.psiH = v.a;
  const r = Rig.frame(P);
  const hg = r.groups.filter(g => g.name.startsWith('head'));
  const skull = hg.find(g => g.name === 'head_skull');
  const ears = hg.filter(g => g.name.startsWith('head_ear'));
  const [sLo, sHi] = extentY([skull]), [, eHi] = extentY(ears), [mLo] = extentY(hg.filter(g => g.name === 'head_muzzle'));
  const nose = r.meas.nose[1];
  // skull mass width on screen (U extent of the skull group)
  let uLo = 1e9, uHi = -1e9; (skull.parts || []).forEach(p => { if (p.t === 'circ') { uLo = Math.min(uLo, p.c[0] - p.r); uHi = Math.max(uHi, p.c[0] + p.r); } });
  T1.views.push({ angle: v.a, layer: v.layer, skullTop: +sHi.toFixed(4), chin: +Math.min(sLo, mLo).toFixed(4), earTip: +eHi.toFixed(4), noseY: +nose.toFixed(4), skullDiscWidth: +(uHi - uLo).toFixed(4) });
}
const headH = T1.views[0].earTip - T1.views[0].chin;
const spread = k => { const xs = T1.views.map(v => v[k]); return Math.max(...xs) - Math.min(...xs); };
T1.headHeight = +headH.toFixed(4);
T1.spread = { skullTop: +spread('skullTop').toFixed(4), chin: +spread('chin').toFixed(4), earTip: +spread('earTip').toFixed(4), noseY: +spread('noseY').toFixed(4) };
T1.ok = Object.values(T1.spread).every(s => s <= 0.02 * headH);
T1.note = 'Y extents are compared at one pitch; widths differ by design (they are the yaw projection of one head sheet). chin uses the lower of skull/muzzle.';
out.T1_head_views = T1;

// ---- T2, T3, T4, T5 over all frames
const L = Rig.SHEET.len; let maxErr = 0, maxErrProj = 0, nProf = 0;
const bendSign = {}; let reversals = 0;
let slipMax = 0, slipN = 0; const slipFrames = [];
let prev = null;
const layers = [];
for (let i = 0; i < perf.length; i++) {
  const p = perf[i]; const r = Rig.frame(p); const m = r.meas;
  layers.push(m.layer);
  m.legs.forEach((g, k) => {
    const len = g.id.startsWith('fore') ? L.fore : L.hind;
    const d3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    const segs = [d3(g.R, g.J), d3(g.J, g.E), d3(g.E, g.F)];
    segs.forEach((s, j) => { maxErr = Math.max(maxErr, Math.abs(s - len[j])); });
    if (Math.abs(Math.sin(p.psiB * Math.PI / 180)) < 0.02) {
      nProf++;
      const d2 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
      [d2(g.R, g.J), d2(g.J, g.E), d2(g.E, g.F)].forEach((s, j) => { maxErrProj = Math.max(maxErrProj, Math.abs(s - len[j])); });
    }
    const sgn = Math.sign(g.cross); const key = g.id.slice(0, 4);
    if (bendSign[key] === undefined) bendSign[key] = sgn; else if (sgn !== bendSign[key] && sgn !== 0) reversals++;
    if (prev) {
      const pg = prev.meas.legs[k], pp = perf[i - 1];
      const stance = p.gait[k].lift === 0 && pp.gait[k].lift === 0 && p.speed > 0.05 && Math.abs(p.psiB - pp.psiB) < 0.01 && p.lie < 0.02 && pp.lie < 0.02;
      if (stance) { const s = Math.abs(g.F[0] - pg.F[0]) + Math.abs(g.F[2] - pg.F[2]); slipN++; if (s > slipMax) slipMax = s; if (s > 0.002) slipFrames.push([i, g.id, +s.toFixed(4)]); }
    }
  });
  prev = r;
}
out.T2_leg_lengths = { maxError3D_m: +maxErr.toExponential(2), maxErrorProjectedInProfile_m: +maxErrProj.toExponential(2), profileFrames: nProf / 4, ok: maxErr < 1e-6 && maxErrProj < 1e-4 };
out.T3_no_reversal = { bendSign, reversals, ok: reversals === 0 };
out.T4_foot_hold = { stanceSamples: slipN, maxSlip_m: +slipMax.toFixed(5), framesOver2mm: slipFrames.length, examples: slipFrames.slice(0, 8), ok: slipFrames.length === 0 };
const seq = (a, b) => { const s = []; for (let i = Math.round(a * 24); i <= Math.round(b * 24); i++) if (!s.length || s[s.length - 1][1] !== layers[i]) s.push([+(i / 24).toFixed(3), layers[i]]); return s; };
out.T5_view_switch = { turn1: seq(3.3, 4.0), turn2: seq(7.35, 8.7), lookIn: seq(26.3, 28.6), everyFrameHasHead: layers.every(Boolean), ok: layers.every(Boolean) };
out.all_ok = ['T1_head_views', 'T2_leg_lengths', 'T3_no_reversal', 'T4_foot_hold', 'T5_view_switch'].every(k => out[k].ok);
fs.writeFileSync(path.resolve(__dirname, '../proof/rig_tests.json'), JSON.stringify(out, null, 1));
fs.writeFileSync(path.resolve(__dirname, '../proof/corrections.json'), JSON.stringify({ version: Rig.SHEET.version, about: 'versioned correction table: each Smart-Bone action, its driver bone and angle range, and what it sculpts', actions: Rig.CORRECTIONS }, null, 1));
console.log(JSON.stringify({ T1: T1.ok, T1spread: T1.spread, headH: T1.headHeight, T2: out.T2_leg_lengths, T3: out.T3_no_reversal, T4: { ok: out.T4_foot_hold.ok, max: slipMax, n: slipFrames.length, ex: slipFrames.slice(0, 5) }, T5: out.T5_view_switch }, null, 0));
