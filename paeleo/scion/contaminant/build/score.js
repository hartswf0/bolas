/* The score for the cinema cut: an original piece composed in code, laid on the run's own events (../cinema/events.json).
   Opening: a drone and three celesta notes as the jellyfish wakes. Hot: A minor pad with tremolo, a pulse in the bass,
   the projector's hum and flutter; each censor's bell is an inharmonic bell with a low thud, and the cut crackles as it
   burns. Cool: water, slow chords (Am F C G), the theme on celesta; each rescue is a harp arpeggio, each seam a shimmering
   dyad. The reel: the theme in C major over warm chords, one chord per returned frame, rising; projector clatter and the
   splices. Coda: C major held, the theme's last phrase, a high note over the afterimage.
   Writes sound-cinema.wav (48 kHz, 16-bit stereo). */
const fs = require('fs'), path = require('path');
const { duration, events } = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'cinema', 'events.json'), 'utf8'));
const SR = 48000, N = Math.round(SR * duration);
const dry = [new Float32Array(N), new Float32Array(N)], send = [new Float32Array(N), new Float32Array(N)];
let seed = 11; const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32) * 2 - 1;
const m2f = m => 440 * 2 ** ((m - 69) / 12), TAU = 2 * Math.PI;
const at = type => events.filter(e => e.type === type);
const SW = (at('switch')[0] || { t: 12 }).t, PROJ = at('projector')[0] || { t: 26.5, dur: 11.7 }, R0 = PROJ.t, R1 = PROJ.t + PROJ.dur;
const END = duration - 3.4;

// add a voice: fn(t) -> sample, panned (-1 left .. 1 right), with a share sent to the reverb
function voice(t0, len, fn, pan = 0, wet = .35) {
  const a = Math.max(0, Math.round(t0 * SR)), b = Math.min(N, Math.round((t0 + len) * SR));
  const gl = Math.cos((pan + 1) * Math.PI / 4), gr = Math.sin((pan + 1) * Math.PI / 4);
  for (let i = a; i < b; i++) {
    const v = fn((i - a) / SR + (a / SR - t0)); if (!v) continue;
    dry[0][i] += v * gl * (1 - wet); dry[1][i] += v * gr * (1 - wet); send[0][i] += v * gl * wet; send[1][i] += v * gr * wet;
  }
}
const env = (t, len, att, rel) => Math.min(1, t / att, Math.max(0, (len - t) / rel));

// instruments
function pad(t0, len, notes, amp, bright = 5, trem = 0, pan = 0) {
  notes.forEach((m, j) => {
    const f = m2f(m);
    for (const det of [-.004, .004]) voice(t0, len + 1.6, t => {
      let s = 0; for (let h = 1; h <= bright; h++) s += Math.sin(TAU * f * (1 + det) * h * t + h) / h;
      return amp * .5 * s * env(t, len + 1.6, 1.4, 1.6) * (1 - trem * (.5 + .5 * Math.sin(TAU * 6 * t)));
    }, pan + (det > 0 ? .35 : -.35) * (j % 2 ? 1 : -1), .45);
  });
}
function celesta(t0, m, amp = .16, pan = .35) {
  const f = m2f(m);
  voice(t0, 3.2, t => amp * Math.exp(-t / 1.1) * Math.sin(TAU * f * t + 2.2 * Math.exp(-t / .25) * Math.sin(TAU * f * 3.5 * t)), pan, .5);
}
function lead(t0, len, m, amp = .13, pan = -.1) {
  const f = m2f(m);
  voice(t0, len + .5, t => {
    const vib = 1 + .004 * Math.sin(TAU * 5.2 * t) * Math.min(1, t / .4), ph = TAU * f * vib * t;
    return amp * env(t, len + .5, .12, .5) * (Math.sin(ph) + .22 * Math.sin(3 * ph) + .08 * Math.sin(5 * ph));
  }, pan, .4);
}
function harp(t0, m, amp = .2, pan = 0) {   // Karplus-Strong
  const f = m2f(m), L = Math.round(SR / f), buf = new Float32Array(L).map(() => rnd()); let k = 0;
  voice(t0, 2.6, () => { const v = buf[k % L], nxt = buf[(k + 1) % L]; buf[k % L] = .498 * (v + nxt); k++; return amp * v; }, pan, .45);
}
function bass(t0, len, m, amp = .22) { const f = m2f(m); voice(t0, len, t => amp * env(t, len, .02, .3) * Math.exp(-t / 1.5) * (Math.sin(TAU * f * t) + .3 * Math.sin(TAU * 2 * f * t)), 0, .15); }
function click(t0, amp, tau, pan = 0, wet = .15) { voice(t0, tau * 6, t => amp * Math.exp(-t / tau) * rnd(), pan, wet); }

// beds: projector hum and shutter flutter while hot; water once cool; a soft clatter under the reel
let lp = 0, lp2 = 0;   // two one-pole stages: the water is a low wash, not hiss
for (let i = 0; i < N; i++) {
  const t = i / SR, cool = Math.max(0, Math.min(1, (t - SW) / 2)), fade = Math.min(1, t / 1.5, Math.max(0, (END + 1.5 - t) / 2));
  lp += .01 * (rnd() - lp); lp2 += .03 * (lp - lp2);
  const hot = (1 - cool) * (t > 1.5 ? 1 : t / 1.5) * (.012 * Math.sin(TAU * 50 * t) + .007 * Math.sin(TAU * 100 * t) + .008 * Math.exp(-((t * 24) % 1) * 9) * rnd());
  const water = cool * (t < R0 ? 1 : .4) * .22 * lp2;
  const reelClatter = t > R0 && t < R1 + .5 ? .012 * Math.exp(-((t * 24) % 1) * 12) * rnd() : 0;
  const v = (hot + water + reelClatter) * fade;
  dry[0][i] += v; dry[1][i] += v;
}

// opening: the drone, and three notes as the jellyfish wakes
pad(0, 5.5, [45, 52], .1, 4);
[[1.0, 76], [2.3, 72], [3.6, 69]].forEach(([t, m]) => celesta(t, m, .14));
// hot: A minor with tremolo, then F, growing; a pulse in the bass
pad(5, 3.6, [57, 60, 64], .08, 5, .35, -.2); pad(8.6, 3.6, [53, 57, 60, 65], .1, 5, .45, .2);
for (let t = 5.4; t < SW - .2; t += .9) bass(t, .8, t < 8.6 ? 33 : 29, .16);
// cool: slow chords and the theme, sparse
const COOL = [[SW, [45, 57, 60, 64]], [SW + 3.6, [41, 57, 60, 65]], [SW + 7.2, [48, 55, 60, 64]], [SW + 10.8, [43, 55, 59, 62]]];
COOL.forEach(([t, ns]) => { if (t < R0) pad(t, Math.min(3.6, R0 - t), ns, .085, 3); });
[[SW + .8, 76], [SW + 1.7, 74], [SW + 2.6, 72], [SW + 3.5, 71], [SW + 4.4, 72], [SW + 5.3, 69], [SW + 8.0, 76], [SW + 8.9, 79], [SW + 9.8, 76], [SW + 11.2, 74]]
  .forEach(([t, m]) => { if (t < R0 - .5) celesta(t, m, .12); });
// the reel: one chord per returned frame, rising; the theme in C major fitted to the reel
const nReel = Math.max(1, at('splice').length), per = (PROJ.dur - .4) / nReel;
const REELCH = [[41, 53, 57, 60, 65], [48, 55, 60, 64, 67], [45, 57, 60, 64, 69], [43, 55, 59, 62, 67], [48, 55, 60, 64, 72]];
for (let k = 0; k < nReel; k++) { const ch = REELCH[k % REELCH.length]; pad(R0 + .2 + k * per, per, ch, .07 + .025 * k, 6); bass(R0 + .2 + k * per, per, ch[0] - 12, .2); }
const THEME = [[76, 2], [79, 1], [76, 1], [74, 2], [72, 1], [74, 1], [76, 3], [72, 2], [74, 1], [76, 1], [79, 2], [81, 2], [79, 4]];
const beats = THEME.reduce((s, [, b]) => s + b, 0), bt = (PROJ.dur - .6) / beats;
let tt = R0 + .3; for (const [m, b] of THEME) { lead(tt, b * bt * .95, m, .1 + .05 * (tt - R0) / PROJ.dur); tt += b * bt; }
// coda: C major held; the theme's close; a high note over the afterimage
pad(R1 + .3, END - R1 + .6, [36, 48, 55, 60, 64], .1, 4);
[[R1 + .6, 76, 1.2], [R1 + 1.9, 74, 1.2], [R1 + 3.2, 72, 3.0]].forEach(([t, m, l]) => lead(t, l, m, .11));
celesta(END + .3, 88, .1, .5); celesta(END + 1.4, 84, .07, -.4);

// events: the censor's bell and thud, the burn's crackle, rescues, seams, splices
for (const e of at('bell')) {
  voice(e.t, 2.2, t => Math.exp(-t / .75) * (.12 * Math.sin(TAU * 880 * t) + .05 * Math.sin(TAU * 1763 * t) + .06 * Math.sin(TAU * 2429 * t) + .025 * Math.sin(TAU * 4752 * t)) * (1 + .15 * Math.sin(TAU * 4.5 * t)), .2, .5);
  voice(e.t, .5, t => .35 * Math.exp(-t / .1) * Math.sin(TAU * (48 - 20 * t) * t), 0, .1);   // the hard cut's thud
}
for (const e of at('cut')) for (let k = 0; k < 40; k++) { const dt = Math.abs(rnd()) * 1.1; click(e.t + dt, .06 + .1 * Math.abs(rnd()), .0015, rnd() * .6, .2); }
for (const e of at('rescue')) {
  const ch = [57, 60, 64, 69, 72, 76]; ch.forEach((m, k) => harp(e.t + .1 + k * .07, m, .16, -.4 + k * .16));
}
for (const e of at('seam')) for (const m of [76, 81]) voice(e.t + .15, 2.4, t => .05 * env(t, 2.4, .3, 1.2) * Math.sin(TAU * m2f(m) * t) * (1 + .5 * Math.sin(TAU * 7 * t)), m > 78 ? .5 : -.5, .6);
for (const e of at('splice')) { click(e.t, .18, .003); voice(e.t, .12, t => .1 * Math.exp(-t / .03) * Math.sin(TAU * 90 * t), 0, .05); }

// reverb: Schroeder, four combs and two allpasses per channel, slightly different lengths left and right
function reverb(x, offs) {
  const y = new Float32Array(N), combs = [1557, 1617, 1491, 1422].map(d => Math.round((d + offs) * SR / 44100));
  for (const d of combs) { const b = new Float32Array(d); let k = 0, lpf = 0; for (let i = 0; i < N; i++) { const o = b[k]; lpf = o * .8 + lpf * .2; b[k] = x[i] + lpf * .84; y[i] += o * .25; k = (k + 1) % d; } }
  for (const d of [225, 556].map(d => Math.round((d + offs / 3) * SR / 44100))) { const b = new Float32Array(d); let k = 0; for (let i = 0; i < N; i++) { const o = b[k], v = y[i] + o * .5; b[k] = v; y[i] = o - v * .5; k = (k + 1) % d; } }
  return y;
}
const wet = [reverb(send[0], 0), reverb(send[1], 23)];
const L = new Float32Array(N), Rr = new Float32Array(N); let peak = 0;
for (let i = 0; i < N; i++) {
  const t = i / SR, f = Math.min(1, t / .6, Math.max(0, (duration - t) / 1.0));
  L[i] = (dry[0][i] + wet[0][i] * .9) * f; Rr[i] = (dry[1][i] + wet[1][i] * .9) * f;
  peak = Math.max(peak, Math.abs(L[i]), Math.abs(Rr[i]));
}
const g = peak ? .89 / peak : 1, pcm = Buffer.alloc(44 + N * 4);
pcm.write('RIFF', 0); pcm.writeUInt32LE(36 + N * 4, 4); pcm.write('WAVEfmt ', 8); pcm.writeUInt32LE(16, 16);
pcm.writeUInt16LE(1, 20); pcm.writeUInt16LE(2, 22); pcm.writeUInt32LE(SR, 24); pcm.writeUInt32LE(SR * 4, 28);
pcm.writeUInt16LE(4, 32); pcm.writeUInt16LE(16, 34); pcm.write('data', 36); pcm.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) {
  pcm.writeInt16LE(Math.round(Math.max(-1, Math.min(1, L[i] * g)) * 32767), 44 + i * 4);
  pcm.writeInt16LE(Math.round(Math.max(-1, Math.min(1, Rr[i] * g)) * 32767), 46 + i * 4);
}
fs.writeFileSync(path.join(__dirname, 'sound-cinema.wav'), pcm);
console.log(`sound-cinema.wav: ${duration} s stereo; cool at ${SW.toFixed(2)} s; reel ${R0.toFixed(2)}-${R1.toFixed(2)} s; ${nReel} reel chords; peak gain ${g.toFixed(2)}`);
