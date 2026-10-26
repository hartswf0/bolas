// PAE-01 · SCION through the dog. Renders every lens in operator order, 1.6 s each, centred on that lens's moment, between a title and an end card.
// node tools/paeleo/reel.js OUTDIR   ->  OUTDIR/picture.mp4 and OUTDIR/reel.json (the cut list, for reel_sound.py)
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const FPS = 24, EACH = 1.6, HEAD = 4.0, TAIL = 5.0;
(async () => {
  const out = path.resolve(process.argv[2]); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('file://' + path.join(__dirname, 'lens_render.html')); await p.evaluate(() => window.ready);
  const lenses = await p.evaluate(() => Scion.LENSES.map(l => ({ id: l.id, still: l.still || 18.5 })));
  const N = Math.round((HEAD + lenses.length * EACH + TAIL) * FPS);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', path.join(out, 'picture.mp4')]);
  const cuts = [];
  for (let i = 0; i < N; i++) {
    const T = i / FPS; let d;
    if (T < HEAD) d = await p.evaluate(T => card(T, 'head'), T);
    else if (T >= HEAD + lenses.length * EACH) d = await p.evaluate(T => card(T, 'tail'), T - HEAD - lenses.length * EACH);
    else { const k = Math.floor((T - HEAD) / EACH), u = T - HEAD - k * EACH, L = lenses[k]; const lt = Math.max(0, L.still - EACH / 2) + u;
      if (!cuts[k]) cuts[k] = { id: L.id, at: +(HEAD + k * EACH).toFixed(3), from: +Math.max(0, L.still - EACH / 2).toFixed(3) };
      d = await p.evaluate(([k, t]) => shot(k, t, .93), [k, lt]); }
    if (!ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  fs.writeFileSync(path.join(out, 'reel.json'), JSON.stringify({ fps: FPS, each: EACH, head: HEAD, tail: TAIL, dur: N / FPS, cuts, tl: await p.evaluate(() => Scion.TL) }));
  await b.close(); console.log('reel', N, 'frames');
})();
