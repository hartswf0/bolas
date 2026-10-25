// Event tester: runs the score through the puppet state machine headless and prints/asserts the event trace.
const fs = require('fs'), path = require('path'), DRIVE = require('./drive.js');
const R = path.resolve(__dirname, '../../../..');
const score = JSON.parse(fs.readFileSync(path.join(R, 'paeleo/handmade/score/threshold-score.json')));
const puppet = JSON.parse(fs.readFileSync(path.join(__dirname, 'puppet.json')));
const D = DRIVE.make(score, puppet); let maxSlide = 0; const plant = {};
for (let k = 0; k < score.frames.length; k++) {
  const r = D.step();
  for (const L of r.S.legs) { if (L.planted) { if (plant[L.n]) maxSlide = Math.max(maxSlide, Math.hypot(L.paw[0] - plant[L.n][0], L.paw[2] - plant[L.n][1])); plant[L.n] = [L.paw[0], L.paw[2]]; } else plant[L.n] = null; }
}
const ev = D.dog.events;
if (process.argv[2] === 'all') console.log(ev.filter(e => e.kind !== 'footfall').map(e => JSON.stringify(e)).join('\n'));
console.log('footfalls', ev.filter(e => e.kind === 'footfall').length, 'max planted-foot slide (m)', maxSlide.toFixed(5));
module.exports = { events: ev };
