#!/usr/bin/env node
// Render a short to film: node shorts/tools/render.mjs <id or path without .html, e.g. play/v9> [--stills 1.5,8,12]
// Serves the repository locally, opens shorts/<id>.html?render in Chromium, draws every frame from its time,
// pipes the frames to ffmpeg with the synthesised soundtrack (soundtrack.py), and writes
// assets/shorts/films/<id>.mp4 and <id>.jpg (the poster). --stills writes only those frames, to $STILLS or the temp folder.
import { createRequire } from 'module';
import http from 'http'; import fs from 'fs'; import path from 'path'; import os from 'os'; import { spawn, execFileSync } from 'child_process';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const here = path.dirname(fileURLToPath(import.meta.url)), root = path.resolve(here, '../..');
const page = process.argv[2], id = path.basename(page), si = process.argv.indexOf('--stills');
const stills = si > 0 ? process.argv[si + 1].split(',').map(Number) : null;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml', '.mp4': 'video/mp4', '.ttf': 'font/ttf' };
const srv = http.createServer((q, r) => {
  const f = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { r.writeHead(404); return r.end(); }
  const st = fs.statSync(f), range = q.headers.range, type = types[path.extname(f)] || 'application/octet-stream';
  if (range) { const [a, b] = range.replace('bytes=', '').split('-'); const s = +a, e = b ? +b : st.size - 1;
    r.writeHead(206, { 'Content-Type': type, 'Content-Range': `bytes ${s}-${e}/${st.size}`, 'Accept-Ranges': 'bytes', 'Content-Length': e - s + 1 });
    return fs.createReadStream(f, { start: s, end: e }).pipe(r); }
  r.writeHead(200, { 'Content-Type': type, 'Content-Length': st.size, 'Accept-Ranges': 'bytes' }); fs.createReadStream(f).pipe(r);
});
await new Promise(ok => srv.listen(0, '127.0.0.1', ok));
const browser = await chromium.launch();
const tab = await browser.newPage({ viewport: { width: 1000, height: 700 } });
tab.on('console', m => m.type() === 'error' && console.log('page:', m.text()));
tab.on('pageerror', e => console.log('page error:', e.message));
await tab.goto(`http://127.0.0.1:${srv.address().port}/${page.includes('/') ? page : 'shorts/' + page}.html?render`);
await tab.waitForFunction(() => window.SHORT && window.SHORT.ready);
await tab.evaluate(() => SHORT.ready);
const meta = await tab.evaluate(() => ({ dur: SHORT.dur, fps: SHORT.fps, cues: SHORT.cues, poster: SHORT.poster }));
const grab = async i => Buffer.from((await tab.evaluate(i => SHORT.frame(i), i)).split(',')[1], 'base64');
if (stills) {
  const out = process.env.STILLS || os.tmpdir();
  for (const s of stills) { const f = path.join(out, `${id}-${s.toFixed(1).padStart(4, '0')}.jpg`); fs.writeFileSync(f, await grab(Math.round(s * meta.fps))); console.log(f); }
} else {
  const films = path.join(root, 'assets/shorts/films'); fs.mkdirSync(films, { recursive: true });
  const cues = path.join(os.tmpdir(), id + '.cues.json'), wav = path.join(os.tmpdir(), id + '.wav');
  fs.writeFileSync(cues, JSON.stringify(meta.cues));
  execFileSync('python3', [path.join(here, 'soundtrack.py'), cues, String(meta.dur), wav], { stdio: 'inherit' });
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(meta.fps), '-c:v', 'mjpeg', '-i', '-', '-i', wav,
    '-c:v', 'libx264', '-crf', '25', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart',
    path.join(films, id + '.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(meta.dur * meta.fps);
  for (let i = 0; i < n; i++) {
    const buf = await grab(i);
    if (!ff.stdin.write(buf)) await new Promise(ok => ff.stdin.once('drain', ok));
    if (i % 96 === 0) console.log(`${id} ${i}/${n}`);
  }
  ff.stdin.end(); await new Promise(ok => ff.on('close', ok));
  const poster = path.join(os.tmpdir(), id + '-poster.jpg');
  fs.writeFileSync(poster, await grab(Math.round(meta.poster * meta.fps)));
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', poster, '-q:v', '6', path.join(films, id + '.jpg')]);
  console.log('wrote', path.join(films, id + '.mp4'));
}
await browser.close(); srv.close();
