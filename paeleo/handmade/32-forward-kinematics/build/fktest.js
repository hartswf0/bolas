// SCION 32 · the transform test suite. node fktest.js -> ../proof/fk_tests.json, ../proof/errors_by_joint.json, cache/curves.json
// T1 bone lengths: every joint's distance to its parent, in world, divided by the toy's scale, equals its pivot offset, every frame.
// T2 multiply order: world = parent_world x T(offset) x RY RZ RX, re-derived independently by walking each chain root-first.
// T3 propagation: change one hip / shoulder / waist / person-shoulder angle; every descendant (legs, cloth flaps, cuff, hand)
//    moves by exactly the parent's rigid delta, every non-descendant does not move at all.
// T4 contact: foot slip of every paw while the animator has declared it planted (walk, standing, turning), and its height.
const fs = require('fs'), path = require('path');
const R = require('./rig.js'), { M } = R;
const S = JSON.parse(fs.readFileSync(path.join(__dirname, '../../score/threshold-score.json')));
const tl = R.dogTimeline(S), N = S.frames.length;
const OUT = path.join(__dirname, '..', 'proof'); fs.mkdirSync(OUT, { recursive: true });
const pos = m => [m[12], m[13], m[14]];
const parentOf = g => Object.fromEntries(g.map(([n, p]) => [n, p]));
const offOf = (g, anchor) => Object.fromEntries(g.map(([n, p, o]) => [n, o === 'ANCHOR' ? anchor : o]));
const maxAbs = (a, b) => a.reduce((m, v, k) => Math.max(m, Math.abs(v - b[k])), 0);

const T1 = {}, T2 = { dog: 0, person: 0 }, anchorLen = { min: 1e9, max: -1e9 };
const poses = [];
for (let i = 0; i < N; i++) {
  const t = i / 24, cam = R.camera(t, S);
  const D = R.dogPose(S, tl, i, cam), P = R.personPose(S, i);
  poses.push({ D, P });
  for (const [who, g, W, sc, anchor] of [['dog', R.DOG, D.W, R.SC, D.anchor], ['person', R.PERSON, P.W, 1, null]]) {
    const par = parentOf(g), off = offOf(g, anchor);
    for (const [n, p] of g) {
      if (!p) continue;
      const L = Math.hypot(...off[n]), d = R.dist3(pos(W[n]), pos(W[p])) / sc;
      const key = who + '.' + n;
      if (n === 'head' && who === 'dog') { anchorLen.min = Math.min(anchorLen.min, d); anchorLen.max = Math.max(anchorLen.max, d); }
      const e = Math.abs(d - L);
      T1[key] = T1[key] || { joint: n, parent: p, length_m: +(L * sc).toFixed(4), max_err_m: 0, view_anchor: n === 'head' && who === 'dog' };
      if (n === 'head' && who === 'dog') continue;   // its offset changes by design (view anchor); checked against the anchor in use
      T1[key].max_err_m = Math.max(T1[key].max_err_m, e * sc);
    }
    // T2: independent chain walk
    for (const [n] of g) {
      const chain = []; let c = n; while (c) { chain.unshift(c); c = par[c]; }
      let A = null;
      for (const j of chain) {
        const a = (who === 'dog' ? D.ang : P.ang)[j] || [0, 0, 0];
        const Rm = M.mul(M.mul(M.RY(a[0]), M.RZ(a[1])), M.RX(a[2]));
        A = A ? M.mul(A, M.mul(M.T(...off[j]), Rm)) : M.mul(who === 'dog' ? D.rootWorld : P.rootWorld, Rm);
      }
      T2[who] = Math.max(T2[who], maxAbs(A, W[n]));
    }
  }
  // the head's anchor in use: distance neck->head equals the anchor length that frame
  const al = Math.hypot(...D.anchor), ad = R.dist3(pos(D.W.head), pos(D.W.neck)) / R.SC;
  T1['dog.head'].max_err_m = Math.max(T1['dog.head'].max_err_m, Math.abs(al - ad) * R.SC);
}

// T3 propagation
function descendants(g, j) { const out = new Set([j]); let grew = true; while (grew) { grew = false; for (const [n, p] of g) if (p && out.has(p) && !out.has(n)) { out.add(n); grew = true; } } return out; }
const T3 = [];
for (const [who, g, joint, axis, deg, i] of [['dog', R.DOG, 'hipR', 1, 12, 400], ['dog', R.DOG, 'shoulderL', 1, -15, 400], ['dog', R.DOG, 'waist', 0, 20, 216], ['dog', R.DOG, 'pelvis', 1, 8, 700], ['person', R.PERSON, 'shoulderR', 1, 10, 600], ['person', R.PERSON, 'spine', 1, -8, 600]]) {
  const t = i / 24, base = who === 'dog' ? R.dogPose(S, tl, i, R.camera(t, S)) : R.personPose(S, i);
  const ang = JSON.parse(JSON.stringify(base.ang)); ang[joint] = ang[joint] || [0, 0, 0]; ang[joint][axis] += deg * R.D2R;
  const W2 = R.fk(g, base.rootWorld, ang, who === 'dog' ? base.anchor : null);
  const delta = M.mul(W2[joint], M.inv(base.W[joint]));
  const desc = descendants(g, joint);
  let follow = 0, still = 0, moved = 0, maxMove = 0; const names = [];
  for (const [n] of g) {
    if (desc.has(n)) { const pred = M.mul(delta, base.W[n]); follow = Math.max(follow, maxAbs(pred, W2[n])); const mv = R.dist3(pos(W2[n]), pos(base.W[n])); maxMove = Math.max(maxMove, mv); if (n !== joint) names.push(n); }
    else still = Math.max(still, maxAbs(W2[n], base.W[n]));
  }
  T3.push({ who, joint, change_deg: deg, axis: ['yaw', 'pitch', 'roll'][axis], frame: i, descendants: names, children_follow_max_err: follow, non_descendants_max_change: still, largest_descendant_move_m: +maxMove.toFixed(4) });
}

// T4 contact
const PAWS = { shoulderR: 'fpawR', shoulderL: 'fpawL', hipR: 'hpawR', hipL: 'hpawL' };
const contact = (W, paw) => M.p(W[paw], [0.02, -R.PAW_H, 0]);
const slip = {}; const curves = { t: [], hip: [], knee: [], planted: [], ph: [], slip: [] };
for (const leg in PAWS) slip[leg] = { walk: [], stand: [], turn: [], height: [], perStance: [] };
for (let i = 1; i < N; i++) {
  const a = poses[i - 1].D, b = poses[i].D;
  for (const leg in PAWS) {
    const la = a.legs[leg], lb = b.legs[leg];
    const pa = contact(a.W, PAWS[leg]), pb = contact(b.W, PAWS[leg]);
    if (lb.planted) slip[leg].height.push(pb[1]);
    if (la.planted && lb.planted) {
      const d = Math.hypot(pb[0] - pa[0], pb[2] - pa[2]);
      const moving = S.frames[i].dog.act.moving > 0.05;
      (lb.turning ? slip[leg].turn : moving ? slip[leg].walk : slip[leg].stand).push(d);
    }
  }
  const L = b.legs.hipR; const pa = contact(a.W, 'hpawR'), pb = contact(b.W, 'hpawR');
  curves.t.push(+(i / 24).toFixed(3)); curves.hip.push(+(b.ang.hipR[1] / R.D2R).toFixed(2)); curves.knee.push(+(b.ang.kneeR[1] / R.D2R).toFixed(2));
  curves.planted.push(L.planted ? 1 : 0); curves.slip.push(+(1000 * Math.hypot(pb[0] - pa[0], pb[2] - pa[2])).toFixed(2));
}
// per-stance drift: accumulated displacement from the paw's touchdown to lift-off (walk only)
for (const leg in PAWS) {
  let start = null;
  for (let i = 0; i < N; i++) {
    const L = poses[i].D.legs[leg], c = contact(poses[i].D.W, PAWS[leg]);
    const walking = S.frames[i].dog.act.moving > 0.05 && !L.turning;
    if (L.planted && walking) { if (!start) start = c; else slip[leg].lastDrift = Math.hypot(c[0] - start[0], c[2] - start[2]); }
    else if (start) { if (slip[leg].lastDrift != null) slip[leg].perStance.push(slip[leg].lastDrift); start = null; slip[leg].lastDrift = null; }
  }
}
const st = arr => arr.length ? { n: arr.length, max_mm: +(1000 * Math.max(...arr)).toFixed(2), mean_mm: +(1000 * arr.reduce((s, v) => s + v, 0) / arr.length).toFixed(3) } : { n: 0 };
const T4 = {};
for (const leg in PAWS) {
  const h = slip[leg].height;
  T4[PAWS[leg]] = { walk_slip_per_frame: st(slip[leg].walk), stand_slip_per_frame: st(slip[leg].stand), turn_slip_per_frame: st(slip[leg].turn), stance_drift: st(slip[leg].perStance), planted_height_mm: h.length ? { min: +(1000 * Math.min(...h)).toFixed(1), max: +(1000 * Math.max(...h)).toFixed(1) } : null };
}
const all = k => Object.values(slip).flatMap(s => s[k]);
const summary = {
  T1_bone_lengths: { max_err_m: Math.max(...Object.values(T1).map(v => v.max_err_m)), joints: Object.keys(T1).length, frames: N, head_anchor_length_range_m: [+(anchorLen.min * R.SC).toFixed(4), +(anchorLen.max * R.SC).toFixed(4)], note: 'every bone keeps its length to float precision; the neck->head pivot is a view-specific anchor whose offset is blended between three authored values, so its length is checked against the anchor in use that frame' },
  T2_multiply_order: { max_abs_matrix_err: T2, order: 'world = parent_world * T(pivot offset) * RY(yaw) * RZ(pitch) * RX(roll), root first' },
  T3_propagation: T3,
  T4_contact: { per_paw: T4, walk: st(all('walk')), stand: st(all('stand')), turn: st(all('turn')), stance_drift: st(all('perStance')), how: 'contact point = paw block sole; planted = the animator\'s stance phase while walking, or standing, or not lifted in a turn step; slip = horizontal world displacement between consecutive frames while planted in both; stance drift = displacement from touchdown to lift-off' },
};
fs.writeFileSync(path.join(OUT, 'fk_tests.json'), JSON.stringify(summary, null, 1));
fs.writeFileSync(path.join(OUT, 'errors_by_joint.json'), JSON.stringify(Object.values(T1).map(v => ({ ...v, max_err_m: +v.max_err_m.toExponential(2) })), null, 1));
fs.mkdirSync(path.join(__dirname, 'cache'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'cache', 'curves.json'), JSON.stringify(curves));
// footfalls (touchdown events) for the sound: frame where a paw goes from lifted to planted while walking or turning
const steps = [];
for (let i = 1; i < N; i++) for (const leg in PAWS) { const a = poses[i - 1].D.legs[leg], b = poses[i].D.legs[leg]; if (!a.planted && b.planted && poses[i].D.lie < 0.02) steps.push({ t: +(i / 24).toFixed(3), paw: PAWS[leg] }); }
fs.writeFileSync(path.join(__dirname, 'cache', 'footfalls.json'), JSON.stringify(steps));
console.log(JSON.stringify({ T1: summary.T1_bone_lengths.max_err_m, T2, T3: T3.map(x => [x.joint, x.children_follow_max_err.toExponential(1), x.non_descendants_max_change]), walk: summary.T4_contact.walk, stand: summary.T4_contact.stand, turn: summary.T4_contact.turn, drift: summary.T4_contact.stance_drift, steps: steps.length }, null, 0));
