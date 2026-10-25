// SCION 16 JibJab: drive scene.js in Chromium, pipe JPEG frames to ffmpeg, write the render's own measurements.
// node build/render.mjs film  <cast> <out.mp4> <measure.json>
// node build/render.mjs grid  <out.mp4>                      (comparison viewer: paper | doodle | home | plate)
// node build/render.mjs stills <cast> <outdir> t1,t2,...     (scene times in seconds)
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }
const HERE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const FONTS = '/home/user/bolas/tools/paeleo/fonts';
const [mode, ...args] = process.argv.slice(2);

const b64 = p => fs.readFileSync(p).toString('base64');
const dataUrl = p => 'data:image/png;base64,' + b64(p);
const manifest = JSON.parse(fs.readFileSync(path.join(HERE, 'cast/manifest.json')));
const images = { door: dataUrl(path.join(HERE, 'plates/door.png')), fur: dataUrl(path.join(HERE, 'plates/fur.png')) };
for (const [c, cast] of Object.entries(manifest.casts)) {
  for (const [v, vw] of Object.entries(cast.views)) images[`${c}/${v}`] = dataUrl(path.join(HERE, vw.png));
  for (const f of fs.readdirSync(path.join(HERE, 'cast', c))) if (f.startsWith('ear')) images[`${c}/${f.replace('.png', '')}`] = dataUrl(path.join(HERE, 'cast', c, f));
}
// fonts: parse local.css for the faces we use
const css = fs.readFileSync(path.join(FONTS, 'local.css'), 'utf8');
const fonts = {};
for (const blk of css.split('@font-face').slice(1)) {
  const fam = /font-family:\s*'([^']+)'/.exec(blk)[1], st = /font-style:\s*(\w+)/.exec(blk)[1], wt = /font-weight:\s*(\d+)/.exec(blk)[1];
  const src = /url\(([^)]+)\)/.exec(blk)[1];
  const key = `${fam}|${wt}|${st}`;
  if (!fonts[key] && /U\+0000-00FF/.test(blk)) fonts[key] = b64(path.join(FONTS, src));
}
const data = {
  manifest, images, fonts,
  perf: JSON.parse(fs.readFileSync(path.join(HERE, 'performance.json'))),
  skeleton: JSON.parse(fs.readFileSync(path.join(HERE, 'build/cache/skeleton.json'))),
  qd: JSON.parse(fs.readFileSync(path.join(HERE, 'plates/qd.json'))),
};

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => { console.error('[pageerror]', e); process.exit(2); });
await page.setContent(`<html><body style="margin:0;background:#000"><canvas id=c width=1280 height=720></canvas></body></html>`);
await page.addScriptTag({ content: fs.readFileSync(path.join(HERE, 'build/scene.js'), 'utf8') });
await page.evaluate(async d => { await window.SCENE.init(d); }, data);

function ffmpeg(out) {
  const p = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-preset', 'medium', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  return p;
}
async function put(p, buf) { if (!p.stdin.write(buf)) await new Promise(r => p.stdin.once('drain', r)); }
const done = p => new Promise(r => { p.on('close', r); p.stdin.end(); });

if (mode === 'film') {
  const [cast, out, mout] = args;
  const ff = ffmpeg(out);
  const meas = [];
  // end-card thumbnails: the three casts at the look-in (27.2 s)
  await page.evaluate(() => {
    const S = window.SCENE; S.card.thumbs = [];
    for (const c of ['paper', 'doodle', 'home']) {
      const cv = S.mk(1280, 720), x = cv.getContext('2d');
      S.renderScene(x, Math.round(27.2 * 24), c, { nocaption: true });
      const th = S.mk(480, 270); const tx = th.getContext('2d');
      tx.drawImage(cv, 100, 250, 640, 360, 0, 0, 480, 270); S.card.thumbs.push(th);
    }
  });
  for (let f = 0; f < 912; f++) {
    const r = await page.evaluate(([f, cast]) => {
      const S = window.SCENE, c = document.getElementById('c'), x = c.getContext('2d');
      let m = null;
      if (f < 72) S.card(x, 'title', f / 72);
      else if (f < 840) m = S.renderScene(x, f - 72, cast, { measure: true });
      else S.card(x, 'end', (f - 840) / 72);
      return { m, url: c.toDataURL('image/jpeg', 0.9) };
    }, [f, cast]);
    if (r.m) meas.push({ i: f - 72, ...r.m });
    await put(ff, Buffer.from(r.url.split(',')[1], 'base64'));
    if (f % 100 === 0) console.log('frame', f);
  }
  await done(ff);
  fs.writeFileSync(mout, JSON.stringify(meas));
} else if (mode === 'grid') {
  const [out] = args;
  const ff = ffmpeg(out);
  for (let i = 0; i < 768; i++) {
    const url = await page.evaluate(i => {
      const S = window.SCENE, c = document.getElementById('c'), x = c.getContext('2d');
      if (!S.q) S.q = S.mk(1280, 720);
      const q = S.q.getContext('2d');
      const tiles = [['paper', {}], ['doodle', {}], ['home', {}], ['none', { plate: true, measure: true }]];
      tiles.forEach(([cast, o], k) => {
        S.renderScene(q, i, cast, { nocaption: true, ...o });
        x.drawImage(S.q, (k % 2) * 640, Math.floor(k / 2) * 360, 640, 360);
        x.font = '600 22px JetBrains Mono'; x.fillStyle = 'rgba(255,240,220,0.95)';
        x.fillText(['cast: paper', 'cast: doodle (Quick, Draw!)', 'cast: home movie (archive)', 'plate + slot + mattes'][k], (k % 2) * 640 + 14, Math.floor(k / 2) * 360 + 30);
      });
      x.fillStyle = 'rgba(0,0,0,0.6)'; x.fillRect(0, 358, 1280, 4); x.fillRect(638, 0, 4, 720);
      x.font = '400 18px JetBrains Mono'; x.fillStyle = 'rgba(255,255,255,0.85)'; x.fillText((i / 24).toFixed(2) + ' s', 1180, 700);
      return c.toDataURL('image/jpeg', 0.85);
    }, i);
    await put(ff, Buffer.from(url.split(',')[1], 'base64'));
  }
  await done(ff);
} else if (mode === 'stills') {
  const [cast, outdir, times] = args;
  fs.mkdirSync(outdir, { recursive: true });
  for (const ts of times.split(',')) {
    const t = parseFloat(ts), i = Math.round(t * 24);
    const url = await page.evaluate(([i, cast]) => {
      const S = window.SCENE, c = document.getElementById('c'), x = c.getContext('2d');
      S.renderScene(x, i, cast, {}); return c.toDataURL('image/jpeg', 0.92);
    }, [i, cast]);
    const name = args[3] === 'named' ? `still_${t.toFixed(1).padStart(4, '0')}s.jpg` : `f${String(i).padStart(3, '0')}_${cast}.jpg`;
    fs.writeFileSync(path.join(outdir, name), Buffer.from(url.split(',')[1], 'base64'));
  }
}
await browser.close();
