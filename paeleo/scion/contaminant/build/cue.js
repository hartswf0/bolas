/* SCION 093 · the added music, identical under both versions so the score cannot favour either (the controlled
   variable). cue.wav: 28 s, A minor to C major, a pad under a celesta statement of the theme that a soft lead then
   completes. diag.wav: the diagnostic's bed, one held chord and a slow pulse, quiet, so the comparison is seen, not
   scored. Both 48 kHz 16-bit stereo, newly composed here. Usage: node cue.js <cue seconds> <diagnostic seconds> */
const fs = require('fs'), path = require('path');
const SR = 48000, TAU = 2 * Math.PI, m2f = m => 440 * 2 ** ((m - 69) / 12);
let seed = 5; const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32) * 2 - 1;

function render(dur, compose) {
  const N = Math.round(dur * SR), L = new Float32Array(N), R = new Float32Array(N);
  const voice = (t0, len, fn, pan = 0) => {
    const a = Math.max(0, Math.round(t0 * SR)), b = Math.min(N, Math.round((t0 + len) * SR)), gl = Math.cos((pan + 1) * Math.PI / 4), gr = Math.sin((pan + 1) * Math.PI / 4);
    for (let i = a; i < b; i++) { const v = fn((i - a) / SR); L[i] += v * gl; R[i] += v * gr; }
  };
  const env = (t, len, att, rel) => Math.min(1, t / att, Math.max(0, (len - t) / rel));
  const I = {
    pad: (t0, len, notes, amp) => notes.forEach((m, j) => { for (const det of [-.004, .004]) voice(t0, len + 1.4, t => { let s = 0; for (let h = 1; h <= 4; h++) s += Math.sin(TAU * m2f(m) * (1 + det) * h * t + h) / h; return amp * .5 * s * env(t, len + 1.4, 1.2, 1.4); }, (det > 0 ? .4 : -.4) * (j % 2 ? 1 : -1)); }),
    celesta: (t0, m, amp) => voice(t0, 3, t => amp * Math.exp(-t / 1.1) * Math.sin(TAU * m2f(m) * t + 2.2 * Math.exp(-t / .25) * Math.sin(TAU * m2f(m) * 3.5 * t)), .35),
    lead: (t0, len, m, amp) => voice(t0, len + .5, t => { const ph = TAU * m2f(m) * (1 + .004 * Math.sin(TAU * 5.2 * t) * Math.min(1, t / .4)) * t; return amp * env(t, len + .5, .12, .5) * (Math.sin(ph) + .22 * Math.sin(3 * ph)); }, -.1),
    bass: (t0, len, m, amp) => voice(t0, len, t => amp * env(t, len, .02, .3) * Math.exp(-t / 1.6) * Math.sin(TAU * m2f(m) * t), 0)};
  compose(I, dur);
  // a short stereo room: two cross-fed delays, enough to place the instruments without blurring the cut
  for (const [d, g] of [[Math.round(.031 * SR), .22], [Math.round(.047 * SR), .18], [Math.round(.083 * SR), .12]])
    for (let i = N - 1; i >= d; i--) { L[i] += R[i - d] * g; R[i] += L[i - d] * g; }
  let peak = 0; for (let i = 0; i < N; i++) { const f = Math.min(1, i / SR / .3, (N - i) / SR / .6); L[i] *= f; R[i] *= f; peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); }
  return {N, L, R, g: peak ? .7 / peak : 1};
}
function wav(file, {N, L, R, g}) {
  const b = Buffer.alloc(44 + N * 4);
  b.write('RIFF', 0); b.writeUInt32LE(36 + N * 4, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(2, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 4, 28); b.writeUInt16LE(4, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(N * 4, 40);
  for (let i = 0; i < N; i++) { b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, L[i] * g)) * 32767), 44 + i * 4); b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, R[i] * g)) * 32767), 46 + i * 4); }
  fs.writeFileSync(path.join(__dirname, file), b);
}
const [cueS, diagS] = process.argv.slice(2).map(Number);
wav('cue.wav', render(cueS, (I, dur) => {
  const CH = [[45, 57, 60, 64], [41, 57, 60, 65], [48, 55, 60, 64], [43, 55, 59, 62], [45, 57, 60, 64], [41, 57, 60, 65], [43, 55, 59, 62], [48, 55, 60, 64]];
  const step = dur / CH.length;
  CH.forEach((ch, k) => { I.pad(k * step, step, ch, .07 + .01 * k); I.bass(k * step, step, ch[0] - 12, .16); });
  [[.6, 76], [1.5, 74], [2.4, 72], [3.3, 71], [4.2, 72], [5.1, 69], [7.4, 76], [8.3, 79], [9.2, 76], [10.6, 74]].forEach(([t, m]) => I.celesta(t * dur / 28, m, .13));
  let t = dur * .5; for (const [m, b] of [[76, 2], [79, 1], [76, 1], [74, 2], [72, 1], [74, 1], [76, 2], [72, 4]]) { I.lead(t, b * dur / 28 * .55 * .95, m, .1); t += b * dur / 28 * .55; }
}));
wav('diag.wav', render(diagS, (I, dur) => {
  I.pad(0, dur - 1.2, [45, 52, 57, 64], .05);
  for (let t = 1; t < dur - 1; t += 2) I.celesta(t, 88, .03);
}));
console.log(`cue.wav ${cueS} s and diag.wav ${diagS} s written`);
