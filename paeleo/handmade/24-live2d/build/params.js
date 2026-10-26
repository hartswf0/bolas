// node params.js : writes ../proof/params.json, the parameter table of the rig (axes, keyform grid, what drives each axis)
global.Scene = {}; require('./rig.js'); require('./motion.js');
const fs = require('fs');
const drive = {
  ParamBodyAngleX: 'acting sheet (motion.js A.bodyYaw): the refusal turn 3.47-3.93 s and the return 8.06-8.78 s, both through 90 (toward the viewer)',
  ParamAngleX: 'acting sheet A.headYaw: leads the body by 2-3 frames; over the shoulder at 7.47-7.92 s; into the room 26.62-27.2 s',
  ParamAngleY: 'acting sheet A.headPitch, minus 6 deg per unit of score act.rest', ParamAngleZ: 'acting sheet A.headRoll',
  ParamEyeBallX: 'acting sheet A.eyeX: the eyes move first (whale eye at 3.46, 6.3, 7.5 s)', ParamEyeBallY: 'acting sheet A.eyeY',
  ParamEyeOpen: 'blinks (motion.js BLINKS), widening on the calls, heavier lids while refusing and when settled', ParamBrowWorry: 'acting sheet A.brow',
  ParamMouthOpen: 'acting sheet A.mouth (relaxed open mouth lying, the exhale at 29.2 s)', ParamEarPrick: 'score act.ear + one-ear lags (earLag) + ear pendulum',
  ParamTail: 'score act.tail -> tail chain targets; tail pendulum', ParamWag: 'score act.wag -> tail chain lateral target', ParamCrouch: 'score act.crouch',
  ParamLie: 'score act.lie', ParamRest: 'score act.rest (held 25.9-26.42 s so the look-in starts from stillness)', ParamNeck: 'score act.head through a piecewise map (head low on the approach)',
  ParamBreath: 'breath oscillator, faster when afraid; the sigh at 29.15 s',
};
const out = {
  about: 'SCION-24 parameter table. Ranges are the allowed ranges (source-sensitive limits); keyformed axes interpolate between true angle drawings.',
  params: Rig.PARAMS.map(([id, min, max, def, unit, what]) => ({ id, min, max, default: def, unit, what, driven_by: drive[id] })),
  head_keyform_grid: { ParamAngleX_keys_deg: Rig.YAW_KEYS, ParamAngleY_keys_deg: Rig.PITCH_KEYS, inner_axes: ['ParamEarPrick (flat/pricked tip per key)', 'ParamMouthOpen (jaw rotation about the hinge landmark)'], per_key_corrections: Rig.KEY_FIX, landmarks: Object.keys(Rig.HG.pts), ellipsoids: ['skull', 'cheekA', 'cheekB', 'jowl', 'cap', 'mask'] },
  deformer_hierarchy: ['root (score x, torso middle) -> ParamBodyAngleX yaw', ' -> body pitch/height (ParamCrouch, ParamLie, ParamBreath)', '   -> torso art meshes (chest, waist, rump volumes; saddle, blaze, belly markings clipped to the torso)', '   -> neck (ParamNeck, 0.55 of the head-body yaw difference) -> head keyform blend -> roll (ParamAngleZ) -> eyes, brows, ears, nose, mouth', '   -> 4 legs: shoulder/hip -> elbow/knee -> wrist/hock -> paw, two-bone solve to the planted foot', '   -> tail: 7 rotation segments from the tail pendulum', '   -> collar tag pendulum'],
  body: Rig.BODY,
  camera_keys: Motion.create ? undefined : undefined,
};
fs.writeFileSync(__dirname + '/../proof/params.json', JSON.stringify(out, null, 1));
console.log('params', out.params.length);
