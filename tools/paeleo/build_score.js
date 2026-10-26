// The threshold score: the one description every handmade version must honour. Runs the machine on the shared prompt timeline and
// writes paeleo/handmade/score/threshold-score.json: per frame at 24 fps, the dog's state, position, facing and acting intentions,
// the person's circumstances, the prompt on screen, and the six choices. node tools/paeleo/build_score.js
global.window = global; global.DOMMatrix = class {}; global.Path2D = class {};
const fs = require('fs'), path = require('path');
const M = require('../../paeleo/threshold/machine.js'), S = require('../../paeleo/threshold/stage.js');
const FPS = 24, DUR = 32;
const TL = [[1.0, { voice: 'call' }], [2.3, { voice: 'none' }], [3.4, { voice: 'call', hand: 'reach' }], [4.6, { voice: 'none', hand: 'none' }],
  [5.4, { place: 'beside', posture: 'sit' }], [6.2, { door: 'open' }], [6.8, { hand: 'low' }], [7.4, { voice: 'soft' }], [9.4, { voice: 'none' }],
  [10.4, { voice: 'soft' }], [11.6, { voice: 'none' }], [26.4, { voice: 'soft' }], [27.4, { voice: 'none' }]];
const PROMPTS = [[0.4, 'the person calls: Come here.'], [2.8, 'call again, and reach for it.'], [4.8, 'sit down beside the door.'], [5.8, 'open the door.'],
  [6.4, 'offer a hand, low.'], [7.0, "say it softly: it's all right."], [25.8, 'come in.']];
const d = M.create(), w = Object.assign({}, M.WORLD), dog = new S.DogAnim(), per = new S.PersonAnim(); let k = 0; const frames = [];
for (let i = 0; i < DUR * FPS; i++) {
  const t = i / FPS; while (k < TL.length && TL[k][0] <= t + 1e-9) { Object.assign(w, TL[k][1]); k++; }
  M.step(d, w, 1 / FPS);
  const p = dog.update({ state: d.state, x: d.x, v: d.v, face: d.face, trust: d.trust, heard: d.t - d.heard }, 1 / FPS);
  const q = per.update({ x: M.PERSON_X[w.place], sit: w.posture === 'sit' ? 1 : 0, reach: w.hand === 'reach' ? 1 : 0, low: w.hand === 'low' ? 1 : 0, mouth: w.voice === 'call' ? .9 : w.voice === 'soft' ? .35 : 0 }, 1 / FPS);
  const r2 = v => Math.round(v * 1000) / 1000, pr = [...PROMPTS].reverse().find(x => t >= x[0]);
  frames.push({ i, t: r2(t), dog: { state: d.state, x: r2(d.x), v: r2(d.v), face: d.face, trust: r2(d.trust), threat: r2(d.threat), heard: r2(Math.min(99, d.t - d.heard)),
      act: { turn: r2(p.turn), lie: r2(p.lie), crouch: r2(p.crouch), ear: r2(p.ear), tail: r2(p.tail), wag: r2(p.wag), head: r2(p.head), rest: r2(p.rest), look: r2(p.look || 0), walk_phase: r2(p.phase % (2 * Math.PI)), moving: r2(p.moving) } },
    person: { x: r2(per.x), sit: r2(q.sit), reach: r2(q.reach), low: r2(q.low), mouth: r2(q.mouth), voice: w.voice, hand: w.hand, posture: w.posture, place: w.place }, door: w.door, prompt: pr ? pr[1] : '' });
}
const choices = d.events.filter(e => e.e === 'transition').map(e => ({ t: e.t, from: e.from, to: e.to, why: e.why, x: e.x }));
const out = { about: 'The PAELEO threshold score: one description, many operations. Every handmade version keeps these choices at these times (±0.25 s), the dog never enters the house (x ≥ ' + M.SILL + ' m), and its refusal shows its back.',
  units: { x: 'metres along the porch; the threshold is x = 0, inside is negative, the porch steps are at ' + M.PORCH_END, t: 'seconds', fps: FPS },
  places: { person_doorway: M.PERSON_X.doorway, person_beside: M.PERSON_X.beside, sill: M.SILL, door_opening: [-0.46, 0.46], porch_end: M.PORCH_END },
  act_meaning: { turn: '1 faces the person and the door, −1 its back turned', lie: '0 standing, 1 lying', crouch: '0 upright, 1 low and afraid', ear: '0 flat, 1 pricked', tail: '0 high, 1.35 tucked', wag: 'tail sweep amplitude', head: '0 down, 1 up and alert', rest: '1 chin on the paws', look: '1 head turned in through the door', walk_phase: 'radians; feet move with distance travelled', moving: '0 still, 1 walking' },
  timeline: TL, prompts: PROMPTS, choices, frames };
fs.writeFileSync(path.join(__dirname, '../../paeleo/handmade/score/threshold-score.json'), JSON.stringify(out));
console.log(frames.length, 'frames;', choices.map(c => c.t.toFixed(2) + ' ' + c.to).join(' · '));
