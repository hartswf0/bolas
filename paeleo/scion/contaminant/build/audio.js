/* Sound for the contaminant jelly film, synthesized from the run's own events (../events.json), so every sound has a cause.
   Hot, until the switch: a projector's hum and shutter flutter. Cool, after it: a quiet water bed.
   bell = the censor's bell over the care strand, cut = the fragment sinking into the tank, rescue = the tape snip as the jelly
   lifts a cut, lift = a small pluck, hand = two wooden ticks, seam = a low tone with a pink shimmer, return = the gear's ratchet,
   switch = a two-note chime as the projector cools, projector = the reel's clatter and a held chord, splice = each join on the reel.
   Writes sound.wav (48 kHz, 16-bit mono). */
const fs = require('fs'), path = require('path');
const MOOD = !!process.env.MOOD, tag = MOOD ? '-mood' : '';
const { duration, events } = JSON.parse(fs.readFileSync(path.join(__dirname, '..', MOOD ? 'mood' : '', 'events.json'), 'utf8'));
const SR = 48000, N = Math.round(SR * duration), buf = new Float32Array(N);
let s = 7; const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32) * 2 - 1;

function voice(t0, len, fn) {
  const a = Math.round(t0 * SR), b = Math.min(N, a + Math.round(len * SR));
  for (let i = Math.max(0, a); i < b; i++) buf[i] += fn((i - a) / SR);
}
const sine = (f, t) => Math.sin(2 * Math.PI * f * t);
const click = (t0, amp, tau) => voice(t0, tau * 6, t => amp * Math.exp(-t / tau) * rnd());
const SOUNDS = {
  lift: e => voice(e.t, .2, t => .16 * Math.exp(-t / .04) * (sine(1320, t) + .3 * sine(1980, t))),
  hand: e => [0, .07].forEach(d => voice(e.t + d, .15, t => .24 * Math.exp(-t / .028) * (sine(660, t) + .4 * sine(990, t)))),
  seam: e => voice(e.t, 2.2, t => Math.min(1, t / .05) * Math.exp(-t / .6) * (.12 * sine(110, t) + .08 * sine(165, t) + .04 * sine(220, t))
    + .035 * Math.exp(-t / .3) * sine(880, t) * (1 + .5 * sine(6, t))),
  return: e => { for (let k = 0; k < 5; k++) click(e.t + k * .06, .14, .002); },
  bell: e => voice(e.t, 2, t => Math.exp(-t / .7) * (.13 * sine(880, t) + .05 * sine(1763, t) + .06 * sine(2429, t) + .025 * sine(4752, t)) * (1 + .15 * sine(4.5, t))),
  cut: e => { click(e.t, .25, .006); voice(e.t, .7, t => .3 * Math.exp(-t / .12) * sine(70, t) + .06 * Math.exp(-t / .35) * Math.sin(2 * Math.PI * (300 * t - 90 * t * t))); },
  rescue: e => { click(e.t, .22, .004); click(e.t + .03, .16, .004); voice(e.t + .05, .25, t => .1 * Math.exp(-t / .06) * sine(1500, t)); },
  switch: e => [[523.25, 0], [783.99, .18]].forEach(([f, d]) => voice(e.t + d, 1.8, t => .12 * Math.exp(-t / .55) * sine(f, t))),
  projector: e => {
    for (let k = 0; k < e.dur * 24; k++) click(e.t + k / 24, .045, .003);
    voice(e.t, e.dur + .6, t => Math.min(1, t / 1.2, (e.dur + .6 - t) / .8) * (.035 * sine(220, t) + .028 * sine(277.18, t) + .025 * sine(329.63, t) + .012 * sine(440, t)));
  },
  splice: e => { click(e.t, .2, .003); voice(e.t, .12, t => .12 * Math.exp(-t / .03) * sine(90, t)); }};

// the bed: projector hum and shutter flutter while hot, crossfading to the water once the switch to cool arrives
const sw = (events.find(e => e.type === 'switch' && e.to === 'cool') || { t: duration }).t;
let lp = 0;
for (let i = 0; i < N; i++) {
  const t = i / SR, cool = Math.max(0, Math.min(1, (t - sw) / 1.5)), swell = .5 + .5 * Math.sin(2 * Math.PI * t / 9);
  lp += .02 * (rnd() - lp);
  const water = .05 * lp * (.6 + .4 * swell) + .018 * (sine(55, t) + .6 * sine(82.5, t)) * (.7 + .3 * swell);
  const hum = .02 * sine(50, t) + .012 * sine(100, t) + .008 * sine(150, t) + .02 * Math.exp(-((t * 24) % 1) * 9) * rnd();
  buf[i] = cool * water + (1 - cool) * hum;
}
for (const e of events) if (SOUNDS[e.type]) SOUNDS[e.type](e);

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
fs.writeFileSync(path.join(__dirname, `sound${tag}.wav`), pcm);
const counts = {}; for (const e of events) counts[e.type] = (counts[e.type] || 0) + 1;
console.log(`sound.wav: ${duration} s; switch to cool at ${sw.toFixed(2)} s;`, JSON.stringify(counts));
