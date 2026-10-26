// Drive render.html in headless Chromium.
//   node build/render.js film  [sim.json] [out.mp4]       -> picture (no sound) + build/cache/measure.json
//   node build/render.js stills OUTDIR t1 t2 ...          -> scene-time JPEG stills (t in scene seconds)
//   node build/render.js range OUTDIR from to step [sim]   -> scene frames from..to (frame indices)
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const HERE = __dirname;
(async () => {
  const mode = process.argv[2];
  const simPath = mode === 'clip' ? process.argv[3] : mode === 'film' ? (process.argv[3] || path.join(HERE, 'cache/sim.json')) : mode === 'range' ? (process.argv[7] || path.join(HERE, 'cache/sim.json')) : path.join(HERE, 'cache/sim.json');
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.log('PAGE ERR', e.message)); p.on('console', m => console.log('console', m.text()));
  await p.goto('file://' + path.join(HERE, 'render.html')); await p.evaluate(() => window.ready);
  const N = await p.evaluate(j => window.load(j), fs.readFileSync(simPath, 'utf8'));
  const label = process.env.LABEL || '';
  const grab = async k => { const r = await p.evaluate(([k, l]) => window.frame(k, 0.93, l), [k, label]); return { buf: Buffer.from(r.img.split(',')[1], 'base64'), m: r.m }; };
  if (mode === 'clip') { // node build/render.js clip SIM OUT.mp4 fromFrame toFrame   (scene frames, with LABEL)
    const [sim, out, f0, f1] = process.argv.slice(3); const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', out]);
    for (let i = +f0; i <= +f1; i++) { const { buf } = await grab(72 + i); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); }
    ff.stdin.end(); await new Promise(r => ff.on('close', r)); console.log('clip', out); await b.close(); return; }
  if (mode === 'stills' || mode === 'range') {
    const out = path.resolve(process.argv[3]); fs.mkdirSync(out, { recursive: true });
    const ks = mode === 'stills' ? process.argv.slice(4).map(t => ({ k: 72 + Math.round(+t * 24), name: `s_${(+t).toFixed(2)}s.jpg` }))
      : (() => { const a = [], [f0, f1, st] = process.argv.slice(4, 7).map(Number); for (let i = f0; i <= f1; i += st) a.push({ k: 72 + i, name: `f${String(i).padStart(4, '0')}.jpg` }); return a; })();
    for (const { k, name } of ks) { const { buf } = await grab(k); fs.writeFileSync(path.join(out, name), buf); }
    console.log('wrote', ks.length, 'stills to', out);
  } else {
    const outMp4 = process.argv[4] || path.join(HERE, 'cache/picture.mp4'), total = 72 + N + 72, meas = [];
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p', outMp4]);
    const t0 = Date.now();
    for (let k = 0; k < total; k++) { const { buf, m } = await grab(k); if (m) meas.push({ i: k - 72, ...m });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); if (k % 120 === 0) console.log('frame', k, '/', total, ((Date.now() - t0) / 1000).toFixed(0) + 's'); }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    fs.writeFileSync(path.join(path.dirname(outMp4), path.basename(outMp4, '.mp4') + '-measure.json'), JSON.stringify(meas));
    console.log('wrote', outMp4, total, 'frames');
  }
  await b.close();
})();
