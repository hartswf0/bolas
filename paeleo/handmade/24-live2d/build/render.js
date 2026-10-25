// node render.js [--frames a:b] [--stills] [--debug] : renders the film picture (title 3 s + scene 768 frames + end 3 s) to cache/picture.mp4
// and writes cache/raw.json (per-frame measurements of the drawn dog) and cache/events.json (sound cues measured from the render)
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const HERE = __dirname, CACHE = path.join(HERE, 'cache');
const score = JSON.parse(fs.readFileSync(path.join(HERE, '../../score/threshold-score.json')));
const args = process.argv.slice(2);
const debug = args.includes('--debug');
const only = args.includes('--frames') ? args[args.indexOf('--frames') + 1].split(':').map(Number) : null;
const shots = args.includes('--shots') ? args[args.indexOf('--shots') + 1].split(',').map(Number) : null;
(async () => {
  fs.mkdirSync(CACHE, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => { console.log('PAGE ERROR', e.message); process.exit(1); });
  p.on('console', m => console.log('page:', m.text()));
  await p.goto('file://' + path.join(HERE, 'page.html'));
  await p.evaluate(() => document.fonts.ready);
  const N = await p.evaluate(s => window.init(s), score);
  if (shots) {   // render sequentially (physics needs history) but only save chosen frames
    const last = Math.max(...shots);
    for (let i = 0; i <= last; i++) { await p.evaluate(([i, d]) => window.frame(i, { debug: d }), [i, debug]); if (shots.includes(i)) { const d = await p.evaluate(() => window.grab(0.92)); fs.writeFileSync(path.join(CACHE, `shot_${String(i).padStart(3, '0')}.jpg`), Buffer.from(d.split(',')[1], 'base64')); } }
    await b.close(); return;
  }
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', path.join(CACHE, 'picture.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  const put = async () => { const d = await p.evaluate(() => window.grab(0.93)); const buf = Buffer.from(d.split(',')[1], 'base64'); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); };
  const fade = (k, n) => Math.min(1, k / 10, (n - 1 - k) / 10);
  const title = [['PAE-02 · SCION 24', '600 64px "Big Shoulders Display"', 300], ['Live2D Cubism — Portrait Volume Illusion', '400 34px Literata', 360], ['The threshold, handmade', 'italic 400 26px Literata', 420, '#b9ae9c']];
  for (let k = 0; k < 72; k++) { await p.evaluate(([l, a]) => window.card(l, a), [title, fade(k, 72)]); await put(); }
  const raw = [];
  for (let i = 0; i < N; i++) {
    raw.push(await p.evaluate(([i, d]) => window.frame(i, { debug: d }), [i, debug]));
    await put();
    if (i % 96 === 0) console.log('frame', i);
  }
  const end = [['What it is made of', '600 40px "Big Shoulders Display"', 190],
    ['A dog drawn as a parametric 2D rig: angle axes, a keyform table for the head,', '400 23px Literata', 250],
    ['rotation and warp deformers, eye, brow, ear and mouth controls, pendulum physics', '400 23px Literata', 284],
    ['for ears, tail and collar tag, and feet solved to planted steps.', '400 23px Literata', 318],
    ['The house in section, the porch and the person are drawn the same way, in code.', '400 23px Literata', 370],
    ['The voice, paws, door and dusk are synthesized. Nothing is filmed or traced;', '400 23px Literata', 422],
    ['the archive dog (Amateur Film New Jersey C, public domain) was studied for its coat.', '400 23px Literata', 456],
    ['The dog follows the PAELEO score: six choices, never inside the house.', 'italic 400 23px Literata', 520, '#b9ae9c']];
  for (let k = 0; k < 72; k++) { await p.evaluate(([l, a]) => window.card(l, a), [end, fade(k, 72)]); await put(); }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  fs.writeFileSync(path.join(CACHE, 'raw.json'), JSON.stringify(raw));
  fs.writeFileSync(path.join(CACHE, 'events.json'), JSON.stringify({ events: await p.evaluate(() => window.events()), speech: await p.evaluate(() => window.speech()) }, null, 1));
  await b.close();
  console.log('done', raw.length);
})();
