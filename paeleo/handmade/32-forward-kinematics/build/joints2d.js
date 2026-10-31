// SCION 32 · project every dog joint of given frames through that frame's camera (for the proof overlays)
const R = require('./rig.js'), { M } = R, S = require('../../score/threshold-score.json');
function lookAt(e, t, up = [0, 1, 0]) { let z = [e[0] - t[0], e[1] - t[1], e[2] - t[2]]; let l = Math.hypot(...z); z = z.map(v => v / l); let x = [up[1] * z[2] - up[2] * z[1], up[2] * z[0] - up[0] * z[2], up[0] * z[1] - up[1] * z[0]]; l = Math.hypot(...x); x = x.map(v => v / l); const y = [z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]]; return [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -(x[0] * e[0] + x[1] * e[1] + x[2] * e[2]), -(y[0] * e[0] + y[1] * e[1] + y[2] * e[2]), -(z[0] * e[0] + z[1] * e[1] + z[2] * e[2]), 1]; }
function persp(f, a, n, fa) { const t = 1 / Math.tan(f * Math.PI / 360); return [t / a, 0, 0, 0, 0, t, 0, 0, 0, 0, (fa + n) / (n - fa), -1, 0, 0, 2 * fa * n / (n - fa), 0]; }
function proj(VP, p) { const x = VP[0] * p[0] + VP[4] * p[1] + VP[8] * p[2] + VP[12], y = VP[1] * p[0] + VP[5] * p[1] + VP[9] * p[2] + VP[13], w = VP[3] * p[0] + VP[7] * p[1] + VP[11] * p[2] + VP[15]; return [(x / w * .5 + .5) * 1280, (1 - (y / w * .5 + .5)) * 720]; }
const tl = R.dogTimeline(S), out = {};
for (const s of process.argv[2].split(',')) {
  const i = +s, cam = R.camera(i / 24, S), VP = M.mul(persp(cam.fov, 16 / 9, .05, 200), lookAt(cam.pos, cam.tgt));
  const D = R.dogPose(S, tl, i, cam);
  out[i] = { joints: R.DOG.map(([n, p]) => ({ n, p, xy: proj(VP, M.p(D.W[n], [0, 0, 0])) })), anchor: D.weights };
  // a perturbed copy: hipR +12 deg, shoulderL -15 deg: descendants follow
  const ang = JSON.parse(JSON.stringify(D.ang)); ang.hipR[1] += 12 * R.D2R; ang.shoulderR[1] -= 15 * R.D2R;
  const W2 = R.fk(R.DOG, D.rootWorld, ang, D.anchor);
  out[i].perturbed = R.DOG.map(([n, p]) => ({ n, p, xy: proj(VP, M.p(W2[n], [0, 0, 0])) }));
}
console.log(JSON.stringify(out));
