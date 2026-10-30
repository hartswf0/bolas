/* Sound for the contaminant jelly film, synthesized from the run's own events (../events.json), so every sound has a cause:
   lift = a small high pluck, hand = two wooden ticks, seam = a low tone with a pink shimmer, return = the gear's ratchet,
   switch = a soft two-note chime when contamination turns on. Under it, a quiet water bed. Writes sound.wav (48 kHz, 16-bit mono). */
const fs = require('fs'), path = require('path');
const { duration, events } = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'events.json'), 'utf8'));
const SR = 48000, N = Math.round(SR * duration), buf = new Float32Array(N);
let s = 7; const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32) * 2 - 1;

function voice(t0, len, fn) {
  const a = Math.round(t0 * SR), b = Math.min(N, a + Math.round(len * SR));
  for (let i = Math.max(0, a); i < b; i++) buf[i] += fn((i - a) / SR);
}
const sine = (f, t) => Math.sin(2 * Math.PI * f * t);
const SOUNDS = {
  lift: t0 => voice(t0, .2, t => .16 * Math.exp(-t / .04) * (sine(1320, t) + .3 * sine(1980, t))),
  hand: t0 => [0, .07].forEach(d => voice(t0 + d, .15, t => .24 * Math.exp(-t / .028) * (sine(660, t) + .4 * sine(990, t)))),
  seam: t0 => voice(t0, 2.2, t => Math.min(1, t / .05) * Math.exp(-t / .6) * (.12 * sine(110, t) + .08 * sine(165, t) + .04 * sine(220, t))
    + .035 * Math.exp(-t / .3) * sine(880, t) * (1 + .5 * sine(6, t))),
  return: t0 => { for (let k = 0; k < 5; k++) voice(t0 + k * .06, .012, t => .14 * Math.exp(-t / .004) * rnd()); },
  switch: t0 => [[523.25, 0], [783.99, .18]].forEach(([f, d]) => voice(t0 + d, 1.8, t => .12 * Math.exp(-t / .55) * sine(f, t)))};

// water bed: low-passed noise and a slow two-tone drone
let lp = 0;
for (let i = 0; i < N; i++) {
  const t = i / SR, swell = .5 + .5 * Math.sin(2 * Math.PI * t / 9);
  lp += .02 * (rnd() - lp);
  buf[i] = .05 * lp * (.6 + .4 * swell) + .018 * (sine(55, t) + .6 * sine(82.5, t)) * (.7 + .3 * swell);
}
for (const e of events) if (SOUNDS[e.type]) SOUNDS[e.type](e.t);

// fade in and out, normalize to -1 dBFS peak
let peak = 0;
for (let i = 0; i < N; i++) {
  const t = i / SR; buf[i] *= Math.min(1, t / .8, (duration - t) / 1.2);
  peak = Math.max(peak, Math.abs(buf[i]));
}
const g = peak ? .89 / peak : 1, pcm = Buffer.alloc(44 + N * 2);
pcm.write('RIFF', 0); pcm.writeUInt32LE(36 + N * 2, 4); pcm.write('WAVEfmt ', 8); pcm.writeUInt32LE(16, 16);
pcm.writeUInt16LE(1, 20); pcm.writeUInt16LE(1, 22); pcm.writeUInt32LE(SR, 24); pcm.writeUInt32LE(SR * 2, 28);
pcm.writeUInt16LE(2, 32); pcm.writeUInt16LE(16, 34); pcm.write('data', 36); pcm.writeUInt32LE(N * 2, 40);
for (let i = 0; i < N; i++) pcm.writeInt16LE(Math.round(Math.max(-1, Math.min(1, buf[i] * g)) * 32767), 44 + i * 2);
fs.writeFileSync(path.join(__dirname, 'sound.wav'), pcm);
const count = type => events.filter(e => e.type === type).length;
console.log(`sound.wav: ${duration} s; lift ${count('lift')}, hand ${count('hand')}, seam ${count('seam')}, return ${count('return')}, switch ${count('switch')}`);
