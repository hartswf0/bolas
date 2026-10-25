// Drive build/render.html in headless Chromium.
//   node build/render.js --film            → build/cache/picture.mp4 (title 3 s + scene 768 frames + end card 3 s) and build/cache/measure.json
//   node build/render.js --at 3.6,9,19,28  → build/cache/preview/t_<t>.jpg (frames solved in sequence from the start)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const HERE = __dirname, ROOT = path.join(HERE, '..'), CACHE = path.join(HERE, 'cache');
const SCORE = JSON.parse(fs.readFileSync(path.join(ROOT, '..', 'score', 'threshold-score.json'), 'utf8'));
const MESH = {};
for (const f of fs.readdirSync(path.join(ROOT, 'assets', 'mesh'))) MESH[f.replace('.json', '')] = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets', 'mesh', f), 'utf8'));
const QD = fs.readFileSync(path.join(ROOT, 'assets', 'quickdraw.ndjson'), 'utf8').trim().split('\n').map(l => JSON.parse(l));
const args = process.argv.slice(2);

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--allow-file-access-from-files', '--disable-accelerated-2d-canvas'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
  p.on('pageerror', e => console.error('pageerror:', e.message));
  await p.goto('file://' + path.join(HERE, 'render.html'));
  const n = await p.evaluate(d => init(d), { score: SCORE, mesh: MESH, qd: QD });
  console.log('meshes', n);
  const W = (f, d) => fs.writeFileSync(f, Buffer.from(d.split(',')[1], 'base64'));
  if (args[0] === '--at' || args[0] === '--frames') {
    const dir = path.join(CACHE, 'preview'); fs.mkdirSync(dir, { recursive: true });
    const want = args[1].split(',').map(Number).map(v => args[0] === '--at' ? Math.round(v * 24) : v);
    const last = Math.max(...want);
    for (let i = 0; i <= last; i++) {
      const draw = want.includes(i);
      if (!draw && !args.includes('--seq')) continue;
      const r = await p.evaluate(([i, draw]) => { const r = renderFrame(i); return { r, img: draw ? grab(0.88) : null }; }, [i, draw]);
      if (draw) { W(path.join(dir, `f${String(i).padStart(3, '0')}_t${(i / 24).toFixed(2)}.jpg`), r.img); console.log(i, (i / 24).toFixed(2), JSON.stringify(r.r.dog), JSON.stringify(r.r.diag)); }
    }
  } else if (args[0] === '--film') {
    fs.mkdirSync(CACHE, { recursive: true });
    const ff = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p', '-r', '24', path.join(CACHE, 'picture.mp4')]);
    const put = d => new Promise(res => { if (!ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) ff.stdin.once('drain', res); else res(); });
    const meas = [], t0 = Date.now();
    for (let k = 0; k < 72; k++) await put(await p.evaluate(u => { card('title', u); return grab(0.92); }, k / 24));
    for (let i = 0; i < SCORE.frames.length; i++) {
      const r = await p.evaluate(i => { const t = performance.now(); const r = renderFrame(i); r.ms = performance.now() - t; return { r, img: grab(0.92) }; }, i);
      meas.push(Object.assign({ i }, r.r));
      await put(r.img);
      if (i % 96 === 0) console.log('frame', i, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
    for (let k = 0; k < 72; k++) await put(await p.evaluate(u => { card('end', u); return grab(0.92); }, k / 24));
    ff.stdin.end(); await new Promise(res => ff.on('close', res));
    fs.writeFileSync(path.join(CACHE, 'measure.json'), JSON.stringify(meas));
    console.log('film frames', 72 + SCORE.frames.length + 72, 'in', ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  await b.close();
})();
