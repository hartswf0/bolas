// node keyform_test.js : numerical invariants of the head rig, written to ../proof/keyform_test.json
//  1 view interpolation (the keyform blend) stays within a small error of the turnaround guide at every in-between angle
//  2 face proportions stable: the blended skull keeps its area against the guide
//  3 lips never drift into the wrong depth: wherever the mouth is drawn, the near lip corner lies inside the muzzle/jowl/cheek meshes
//  4 silhouette appropriate to view: the far eye is hidden in profile, both eyes show in the front view
global.Scene = {}; require('./rig.js');
const R = Rig, fs = require('fs');
const keys = ['muzB', 'muzT', 'nose', 'eyeA', 'eyeB', 'earAi', 'earAt', 'earBt', 'lipA', 'lipB', 'lipF', 'chin'];
let maxErr = 0, at = null, areaDev = 0, lipBad = [], lipTested = 0;
const inPoly = (p, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const a = poly[i], b = poly[j]; if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; };
for (let yaw = -180; yaw < 180; yaw += 2.5) for (const pitch of [-30, -17.5, -5, 0, 5, 17.5, 30]) {
  const k = R.headKey(yaw, pitch), g = R.guideKey(((yaw % 360) + 360) % 360, pitch);
  for (const n of keys) { const e = Math.hypot(k[n][0] - g[n][0], k[n][1] - g[n][1]) / 0.08; if (e > maxErr) { maxErr = e; at = [yaw, pitch, n]; } }
  const area = s => Math.sqrt(Math.max(0, s[3] * s[5] - s[4] * s[4]));
  areaDev = Math.max(areaDev, Math.abs(area(k.skull) / area(g.skull) - 1));
  const vis = Math.max(k.f_eyeA[0], k.f_eyeB[0]);
  const mouthVis = R.smooth(-0.05, 0.2, vis);
  if (mouthVis > 0.05) {
    lipTested++;
    const K = 1000, P = q => [q[0] * K, -q[1] * K];
    const ell = e => R.ellPoly(e[0] * K, -e[1] * K, e[3] * K * K, -e[4] * K * K, e[5] * K * K, 40);
    const polys = [R.capsule(P(k.muzB), R.HG.radius.muzB * K, P(k.muzT), R.HG.radius.muzT * K, 20), ell(k.jowl), ell(k.cheekA), ell(k.cheekB), ell(k.skull)];
    const near = k.lipA[2] > k.lipB[2] ? k.lipA : k.lipB;
    // allow the drawn line its half width (1.2 mm) beyond the mesh edge
    const ok = [[0, 0], [1.2, 0], [-1.2, 0], [0, 1.2], [0, -1.2]].some(([dx, dy]) => polys.some(pp => inPoly([near[0] * K + dx, -near[1] * K + dy], pp)));
    if (!ok) lipBad.push([yaw, pitch]);
  }
}
const prof = [-10, -5, 0, 5, 10].map(y => { const k = R.headKey(y, 0); return Math.min(k.f_eyeA[0], k.f_eyeB[0]); });
const front = R.headKey(90, 0);
const out = {
  view_interpolation_max_error_of_skull_radius: +maxErr.toFixed(3), worst_at: at, keyforms: { yaw: R.YAW_KEYS.length, pitch: R.PITCH_KEYS.length },
  skull_area_max_deviation: +areaDev.toFixed(3),
  lips_inside_muzzle: { tested_views: lipTested, outside: lipBad.length, examples: lipBad.slice(0, 6) },
  far_eye_facing_in_profile_max: +Math.max(...prof).toFixed(3), far_eye_hidden_in_profile: Math.max(...prof) < 0.06,
  both_eyes_in_front_view: front.f_eyeA[0] > 0.3 && front.f_eyeB[0] > 0.3,
  pass: maxErr < 0.15 && areaDev < 0.08 && lipBad.length === 0 && Math.max(...prof) < 0.06,
};
fs.mkdirSync(__dirname + '/../proof', { recursive: true });
fs.writeFileSync(__dirname + '/../proof/keyform_test.json', JSON.stringify(out, null, 1));
console.log(JSON.stringify(out));
