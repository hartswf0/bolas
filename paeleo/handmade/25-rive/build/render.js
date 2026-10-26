// node build/render.js OUT_DIR [from to step]  - with from/to: writes scene stills (scene frame numbers) as JPEG; else pipes the film into ffmpeg.
// Always writes trace (full) and events to OUT_DIR/render-trace.json.
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
(async () => {
  const out = path.resolve(process.argv[2]); fs.mkdirSync(out, { recursive: true });
  const from = process.argv[3] !== undefined ? +process.argv[3] : null, to = +process.argv[4], step = +(process.argv[5] || 1);
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] }); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const R = path.resolve(__dirname, '../../../..');
  await p.addInitScript(d => { window.__DATA = d; }, { score: JSON.parse(fs.readFileSync(path.join(R, 'paeleo/handmade/score/threshold-score.json'))), puppet: JSON.parse(fs.readFileSync(path.join(__dirname, 'puppet.json'))) });
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => console.log('console', m.text()));
  await p.goto('file://' + path.join(__dirname, 'page.html')); await p.evaluate(() => Promise.all([window.ready, window.__fonts]));
  const N = await p.evaluate(() => FILM.N), T = await p.evaluate(() => FILM.TITLE);
  if (from !== null) {
    for (let s = 0; s <= to; s++) { const keep = s >= from && (s - from) % step === 0; const d = await p.evaluate(([n, k]) => frame(n, k ? .9 : 0), [T + s, keep]);
      if (keep) fs.writeFileSync(path.join(out, `s${String(s).padStart(4, '0')}.jpg`), Buffer.from(d.split(',')[1], 'base64')); }
  } else {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-maxrate', '3200k', '-bufsize', '6400k', '-tune', 'animation', '-pix_fmt', 'yuv420p', path.join(out, 'picture.mp4')]);
    for (let n = 0; n < N; n++) {
      const d = await p.evaluate(n => frame(n, .93), n); const ok = ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'));
      if (!ok) await new Promise(r => ff.stdin.once('drain', r));
      if (n % 120 === 0) console.log('frame', n, '/', N);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  const info = await p.evaluate(() => ({ trace: FILM.trace.filter(Boolean), events: FILM.events }));
  fs.writeFileSync(path.join(out, 'render-trace.json'), JSON.stringify(info));
  await b.close(); console.log('done', info.trace.length, 'scene frames traced');
})();
