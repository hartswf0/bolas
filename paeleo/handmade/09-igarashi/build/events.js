// Sound events from the rig: every paw that lands (from the stepping simulation), the sit, the rise, the lie, tail thumps.
// node build/events.js → build/cache/events.json
const fs = require('fs'), path = require('path');
const HERE = __dirname, ROOT = path.join(HERE, '..');
const { Rig, X0, S } = require('./rig.js');
const SCORE = JSON.parse(fs.readFileSync(path.join(ROOT, '..', 'score', 'threshold-score.json'), 'utf8'));
const MESH = {};
for (const f of fs.readdirSync(path.join(ROOT, 'assets', 'mesh'))) MESH[f.replace('.json', '')] = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets', 'mesh', f), 'utf8'));
const rig = Rig(SCORE, MESH), F = SCORE.frames;
const ev = { paws: [], thumps: [], sighs: [], tail: [], whine: [] };
const xs = i => X0 + F[i].dog.x * S;
for (let i = 1; i < F.length; i++) {
  const a = rig.feetOff[i - 1], b = rig.feetOff[i];
  if (a && b) for (const k of Object.keys(b)) if (a[k][1] < -0.5 && b[k][1] >= -0.01) ev.paws.push({ t: F[i].t, x: xs(i), foot: k, s: Math.abs(F[i].dog.x - F[i - 1].dog.x) * 24 > 0.5 ? 1.2 : 0.9 });
  const sa = rig.segment(F[i - 1].t), sb = rig.segment(F[i].t);
  if (sa.body !== sb.body) {
    // a drawing swap is a shift of weight: paws shuffle, or the body meets the boards
    if (sb.body === 'dog_sit_back') ev.thumps.push({ t: F[i].t, x: xs(i), s: 0.5 });
    else if (sb.body === 'dog_lie') { ev.thumps.push({ t: F[i].t, x: xs(i), s: 0.9 }); ev.sighs.push({ t: F[i].t + 0.55, x: xs(i) }); }
    else for (const d of [0, 0.07, 0.15]) ev.paws.push({ t: F[i].t + d, x: xs(i), s: 0.8 });
  }
}
ev.whine.push({ t: 3.47, x: xs(83) });
for (const tt of [29.3]) ev.sighs.push({ t: tt, x: xs(700) });
// lying with a wag: the tail knocks the boards at the top of each sweep
let last = -1;
for (let i = 0; i < F.length; i++) {
  const t = F[i].t, w = F[i].dog.act.wag;
  if (rig.segment(t).body !== 'dog_lie' || w < 0.3) continue;
  const ph = Math.abs(Math.sin(t * 2 * Math.PI * 2.2));
  if (ph > 0.97 && t - last > 0.15) { ev.tail.push({ t, x: xs(i) + 130 }); last = t; }
}
fs.mkdirSync(path.join(HERE, 'cache'), { recursive: true });
fs.writeFileSync(path.join(HERE, 'cache', 'events.json'), JSON.stringify(ev, null, 1));
console.log('events: paws', ev.paws.length, 'thumps', ev.thumps.length, 'tail', ev.tail.length);
