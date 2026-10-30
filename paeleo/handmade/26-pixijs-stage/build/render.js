/* SCION-26 · drive the PixiJS stage in headless Chromium, frame by frame.
   node build/render.js proof 0,86,180,456,672      -> build/cache/proof_<i>.jpg (scene frames)
   node build/render.js film                         -> build/cache/video.mp4 (912 frames: 72 title + 768 scene + 72 end),
                                                        build/cache/measure.json (per-frame measurements, draw calls, ms)
   The page is served from a private origin (page.route) so WebGL may sample the atlas. */
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const PW = (() => { try { return require('playwright'); } catch (e) { return require('/opt/node22/lib/node_modules/playwright'); } })();
const HERE = __dirname, ROOT = path.resolve(HERE, '../../../..');
const CACHE = path.join(HERE, 'cache'); fs.mkdirSync(CACHE, { recursive: true });
const MAP = {
  '/stage.html': path.join(HERE, 'stage.html'), '/engine.js': path.join(HERE, 'engine.js'),
  '/pixi.min.js': path.join(HERE, 'node_modules/pixi.js/dist/pixi.min.js'),
  '/score.json': path.join(ROOT, 'paeleo/handmade/score/threshold-score.json'),
};
const TYPES = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json', '.png': 'image/png', '.css': 'text/css', '.woff2': 'font/woff2' };
function resolve(u) {
  const p = new URL(u).pathname;
  if (MAP[p]) return MAP[p];
  if (p.startsWith('/atlas/')) return path.join(HERE, p);
  if (p.startsWith('/fonts/')) return path.join(ROOT, 'tools/paeleo', p);
  return null;
}
function endText(b, mean, lo, hi) {
  return `The dog: ${b.dogFrags} small cut fragments (body and head in two render textures), placed each frame on a 3-D skeleton, depth-sorted and held together by an alpha-threshold + outline shader. The person: ${b.personFrags} fragments.\n\n` +
  `Coat cut inside the SAM masks of the archive dog (Amateur Film New Jersey C), a lion and a tiger (Andy's Animal Alphabet); hair from a cat (Gateways to the Mind). Coats and the door leaf: Straight Talk. Boards: fence rails (Billie, the Buffalo Baby) and a ladder (Robinson Crusoe C). The offered hand: The Door to Heaven. Lantern: Anthracite. Picture: Golden Gate City. Sky: Top of the Cloud; stars: Gift of Green. All public domain. Chalk lines: Quick, Draw! drawings, CC BY 4.0, Google Creative Lab and contributors.\n\n` +
  `${b.atlasFrames} fragments in one 2048 px texture atlas. PixiJS ${b.version} (MIT), WebGL in headless Chromium (SwiftShader). ${mean.toFixed(1)} draw calls per scene frame (measured; min ${lo}, max ${hi}).\n` +
  `Computed, not cut: the sky gradient, the light polygon and its blur, the door-opening mask, the room's flat colours, and the sound (formant voice, room tone, paws timed to the rendered feet).`;
}
(async () => {
  const mode = process.argv[2] || 'proof';
  const browser = await PW.chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.log('[page error]', e.message));
  await page.route('http://stage.local/**', async (route) => {
    const f = resolve(route.request().url());
    if (!f || !fs.existsSync(f)) return route.fulfill({ status: 404, body: 'nf' });
    route.fulfill({ status: 200, body: fs.readFileSync(f), headers: { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' } });
  });
  await page.goto('http://stage.local/stage.html');
  const info = await page.evaluate(() => window.STAGE.boot());
  console.log('boot', JSON.stringify(info));
  const grab = async () => Buffer.from((await page.evaluate(() => window.STAGE.jpeg(0.94))).split(',')[1], 'base64');
  if (mode === 'proof') {
    const list = (process.argv[3] || '0,86,180,456,672').split(',').map(Number);
    for (const i of list) {
      const r = await page.evaluate(([i]) => window.STAGE.scene(i, true), [i]);
      fs.writeFileSync(path.join(CACHE, `proof_${String(i).padStart(3, '0')}.jpg`), await grab());
      console.log(i, 'draws', r.draws, 'ms', r.ms.toFixed(1), JSON.stringify(r.m), 'psi', r.q.psi.toFixed(0), 'psiH', r.q.psiH.toFixed(0), 'mdx', r.muzzleDx.toFixed(1), 'headY', r.headY.toFixed(0), 'backY', r.backY.toFixed(0));
    }
  } else {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', process.env.CRF || '21', '-pix_fmt', 'yuv420p', '-r', '24', path.join(CACHE, 'video.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
    const write = (b) => new Promise(res => { if (!ff.stdin.write(b)) ff.stdin.once('drain', res); else res(); });
    const meas = { boot: info, title: [], scene: [], end: [] };
    const t0 = Date.now();
    for (let k = 0; k < 72; k++) { const r = await page.evaluate(([k]) => window.STAGE.card('title', k), [k]); meas.title.push(r.draws); await write(await grab()); }
    for (let i = 0; i < 768; i++) {
      const r = await page.evaluate(([i]) => window.STAGE.scene(i, true), [i]);
      meas.scene.push(r); await write(await grab());
      if (i % 96 === 0) console.log('scene', i, 'draws', r.draws, 'ms', r.ms.toFixed(0), ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
    const dr = meas.scene.map(r => r.draws), mean = dr.reduce((a, b) => a + b, 0) / dr.length;
    const info2 = endText(info, mean, Math.min(...dr), Math.max(...dr));
    meas.endText = info2;
    for (let k = 0; k < 72; k++) { const r = await page.evaluate(([k, s]) => window.STAGE.card('end', k, s), [k, info2]); meas.end.push(r.draws); await write(await grab()); }
    ff.stdin.end();
    await new Promise(res => ff.on('close', res));
    fs.writeFileSync(path.join(CACHE, 'measure.json'), JSON.stringify(meas));
    console.log('done', ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  await browser.close();
})();
