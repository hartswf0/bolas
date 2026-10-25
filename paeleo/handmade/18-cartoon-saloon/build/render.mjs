// Renders every film frame in Chromium canvas and pipes JPEGs to ffmpeg. Writes cache/picture.mp4, cache/meas.json,
// cache/events.json (paw contacts from the gait solver), cache/voice.json (syllables shared with the mouth).
import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const { chromium } = require(require.resolve('playwright', { paths: ['/opt/node-tools/node_modules', process.env.NODE_PATH || '.'] }));
import path from 'path'; import fs from 'fs'; import { spawn } from 'child_process';
const here = path.dirname(new URL(import.meta.url).pathname), cache = path.join(here, 'cache');
const only = process.argv[2] ? process.argv[2].split(':').map(Number) : null; // optional f0:f1 for partial renders
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
p.on('pageerror', e => { console.log('ERR', e.message); process.exit(1); });
await p.addInitScript(`window.SCORE=${fs.readFileSync(path.join(here, '../../score/threshold-score.json'))};`);
const texd = {}; for (const n of ['wash0', 'wash1', 'wash2', 'paper', 'wood', 'speck']) texd[n] = 'data:image/png;base64,' + fs.readFileSync(path.join(cache, n + '.png')).toString('base64');
await p.addInitScript(`window.TEXDATA=${JSON.stringify(texd)};`);
await p.goto('file://' + path.join(here, 'stage.html'));
await p.evaluate(async () => { await loadTextures('cache/'); await document.fonts.ready; await initScene(); });
const total = await p.evaluate(() => TOTAL);
const [f0, f1] = only || [0, total];
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '2050k', '-maxrate', '2600k', '-bufsize', '5000k', '-pix_fmt', 'yuv420p', '-r', '24', path.join(cache, only ? 'partial.mp4' : 'picture.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
const meas = [];
const t0 = Date.now();
for (let f = f0; f < f1; f++) {
  const r = await p.evaluate(f => { const m = renderFrame(f); return { m, url: document.getElementById('c').toDataURL('image/jpeg', 0.93) }; }, f);
  if (r.m) meas.push(r.m);
  const buf = Buffer.from(r.url.split(',')[1], 'base64');
  if (!ff.stdin.write(buf)) await new Promise(res => ff.stdin.once('drain', res));
  if (f % 96 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
ff.stdin.end(); await new Promise(res => ff.on('close', res));
if (!only) {
  fs.writeFileSync(path.join(cache, 'meas.json'), JSON.stringify(meas));
  fs.writeFileSync(path.join(cache, 'events.json'), JSON.stringify(await p.evaluate(() => getEvents())));
  fs.writeFileSync(path.join(cache, 'voice.json'), JSON.stringify(await p.evaluate(() => VOICE)));
}
console.log('rendered', f1 - f0, 'frames,', meas.length, 'scene frames measured');
await b.close();
