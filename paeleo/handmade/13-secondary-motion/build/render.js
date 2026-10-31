// Drive render.html in headless Chromium (Playwright).
//   node build/render.js film [preset]               -> build/cache/scene.mp4 (768 frames, no sound) + build/cache/measure.json
//   node build/render.js stills OUTDIR t1 t2 ...     -> JPEG frames at those scene times (seconds), tuned preset
//   node build/render.js clip PRESET OUT.mp4 f0 f1 [label]  -> a comparison clip of scene frames f0..f1
//   node build/render.js cards ENDLINES.json         -> build/cache/title.jpg, build/cache/end.jpg
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const HERE = __dirname, CACHE = path.join(HERE, 'cache'), SCORE = path.join(HERE, '../../score/threshold-score.json');
fs.mkdirSync(CACHE, { recursive: true });
const ffmpeg = out => { const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] }); return ff; };
const write = (ff, buf) => new Promise(r => { if (!ff.stdin.write(buf)) ff.stdin.once('drain', r); else r(); });
(async () => {
  const mode = process.argv[2];
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => { console.log('PAGE ERR', e.message); process.exitCode = 1; }); p.on('console', m => console.log('console', m.text()));
  await p.goto('file://' + path.join(HERE, 'render.html')); await p.evaluate(() => window.ready);
  const score = fs.readFileSync(SCORE, 'utf8');
  const grab = async (k, draw, label) => { const r = await p.evaluate(([k, d, l]) => window.frame(k, d, l), [k, draw, label || '']); return { buf: r.img && Buffer.from(r.img.split(',')[1], 'base64'), m: r.m }; };
  if (mode === 'film') {
    const preset = process.argv[3] || 'tuned';
    const N = await p.evaluate(([s, pr]) => window.init(s, pr), [score, preset]);
    const out = path.join(CACHE, preset === 'tuned' ? 'scene.mp4' : `scene-${preset}.mp4`), ff = ffmpeg(out), meas = [];
    for (let k = 0; k < N; k++) { const { buf, m } = await grab(k, true); meas.push(m); await write(ff, buf); if (k % 96 === 0) console.log('frame', k); }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    fs.writeFileSync(path.join(CACHE, preset === 'tuned' ? 'measure.json' : `measure-${preset}.json`), JSON.stringify(meas));
    console.log('wrote', out, meas.length, 'frames');
  } else if (mode === 'stills') {
    const dir = process.argv[3], ts = process.argv.slice(4).map(Number); fs.mkdirSync(dir, { recursive: true });
    const want = new Map(ts.map(t => [Math.round(t * 24), t]));
    await p.evaluate(([s]) => window.init(s, 'tuned'), [score]);
    const last = Math.max(...want.keys());
    for (let k = 0; k <= last; k++) { const w = want.has(k); const { buf } = await grab(k, w); if (w) fs.writeFileSync(path.join(dir, `f${String(k).padStart(3, '0')}_${want.get(k).toFixed(2)}s.jpg`), buf); }
  } else if (mode === 'clip') {
    const [preset, out, f0, f1, label] = process.argv.slice(3);
    await p.evaluate(([s, pr]) => window.init(s, pr), [score, preset]);
    const ff = ffmpeg(out);
    for (let k = 0; k <= +f1; k++) { const draw = k >= +f0; const { buf } = await grab(k, draw, label); if (draw) await write(ff, buf); }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  } else if (mode === 'cards') {
    const lines = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
    await p.evaluate(([s]) => window.init(s, 'tuned'), [score]);
    for (const kind of ['title', 'end']) { const d = await p.evaluate(([k, l]) => window.card(k, l), [kind, lines]); fs.writeFileSync(path.join(CACHE, kind + '.jpg'), Buffer.from(d.split(',')[1], 'base64')); }
  }
  await b.close();
})();
