// node legcheck.js : runs the motion solver without drawing and reports leg over-extension (paw cannot reach its planted foot)
global.Scene = { spill: () => 0, WALL: { outer: 0.4 } };
require('./rig.js'); require('./motion.js');
const fs = require('fs');
const score = JSON.parse(fs.readFileSync(__dirname + '/../../score/threshold-score.json'));
const M = Motion.create(score), R = Rig;
const bad = [];
for (let i = 0; i < score.frames.length; i++) {
  const st = M.step(i), p = st.pose, fr = R.dogFrame(p);
  const legs = [[R.BODY.shoulder, 1, R.BODY.front[0] + R.BODY.front[1] + 0.045], [R.BODY.shoulder, -1, R.BODY.front[0] + R.BODY.front[1] + 0.045], [R.BODY.hip, 1, R.BODY.hind[0] + R.BODY.hind[1] + 0.12], [R.BODY.hip, -1, R.BODY.hind[0] + R.BODY.hind[1] + 0.12]];
  legs.forEach(([J, s, Lmax], k) => {
    const jw = fr.loc(J[0], J[1], J[2] * s), f = p.feet[k];
    const d = Math.hypot(jw[0] - f.x, jw[1] - (f.y || 0), jw[2] - f.z);
    if (f.planted && d > Lmax * 0.97) bad.push([i, k, +(d / Lmax).toFixed(2)]);
  });
}
const byF = {}; for (const [i, k, r] of bad) (byF[i] = byF[i] || []).push(k + ':' + r);
console.log('frames with a leg at >97% reach:', Object.keys(byF).length);
console.log(Object.entries(byF).slice(0, 80).map(([i, v]) => i + '[' + v.join(' ') + ']').join(' '));
