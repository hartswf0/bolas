// Render PAELEO-00 to frames piped into ffmpeg, and write the sound cues and the decision trace.
// node tools/paeleo/render.js OUTDIR [from] [to] [step]   (from/to/step for test stills: writes JPEGs instead of a film)
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
(async () => {
  const out = path.resolve(process.argv[2]); fs.mkdirSync(out, { recursive: true });
  const from = process.argv[3] !== undefined ? +process.argv[3] : null, to = +process.argv[4], step = +(process.argv[5] || 1);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => console.log('console', m.text()));
  await p.goto('file://' + path.join(__dirname, 'render.html')); await p.evaluate(() => window.ready);
  const N = await p.evaluate(() => FILM.N);
  if (from !== null) {
    for (let i = 0; i <= to; i++) { const keep = i >= from && (i - from) % step === 0; const d = await p.evaluate(([i, k]) => frame(i, k ? .9 : 0), [i, keep]);
      if (keep) fs.writeFileSync(path.join(out, `f${String(i).padStart(5, '0')}.jpg`), Buffer.from(d.split(',')[1], 'base64')); }
  } else {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', path.join(out, 'picture.mp4')]);
    for (let i = 0; i < N; i++) {
      const d = await p.evaluate(i => frame(i, .95), i); const ok = ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'));
      if (!ok) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 240 === 0) console.log('frame', i, '/', N);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  const info = await p.evaluate(() => ({ sfx: FILM.SFX, events: FILM.RUN.events, tl: FILM.TL, prompts: FILM.PROMPTS, T0: FILM.T0, dur: FILM.DUR,
    trace: FILM.RUN.frames.filter((f, i) => i % 6 === 0).map(f => ({ t: f.t, state: f.state, x: f.x, trust: f.trust, threat: f.threat, invite: f.invite, pressure: f.pressure })) }));
  fs.writeFileSync(path.join(out, 'cues.json'), JSON.stringify(info));
  await b.close(); console.log('done', N, 'frames');
})();
