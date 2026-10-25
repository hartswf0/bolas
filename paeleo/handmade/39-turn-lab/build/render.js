// Render the film's frames: node build/render.js [--only i0,i1,...] [--out dir]
// Writes build/cache/frames/title_###.jpg, scene_###.jpg, end_###.jpg and build/cache/measure.json (the id-mask measurements).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const HERE = __dirname, CACHE = path.join(HERE, 'cache');
const args = process.argv.slice(2);
const only = args.includes('--only') ? args[args.indexOf('--only') + 1].split(',').map(Number) : null;
const outDir = args.includes('--out') ? path.resolve(args[args.indexOf('--out') + 1]) : path.join(CACHE, 'frames');
(async () => {
  const plan = JSON.parse(fs.readFileSync(path.join(CACHE, 'plan.json')));
  fs.mkdirSync(outDir, { recursive: true });
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await pg.goto('file://' + path.join(HERE, 'page.html'));
  await pg.evaluate(async () => { await document.fonts.load('800 64px "Big Shoulders Display"'); await document.fonts.load('400 20px "JetBrains Mono"'); await document.fonts.load('400 21px Literata'); await document.fonts.load('italic 400 26px Literata'); await document.fonts.load('600 30px Literata'); await document.fonts.ready; });
  await pg.evaluate(p => R.init(p), plan);
  const save = (name, url) => fs.writeFileSync(path.join(outDir, name), Buffer.from(url.split(',')[1], 'base64'));
  const meas = [];
  const idx = only || plan.map((_, i) => i);
  for (const i of idx) {
    const r = await pg.evaluate(i => R.frame(i, true), i);
    save(`scene_${String(i).padStart(3, '0')}.jpg`, r.jpg); meas.push(r.m);
    if (i % 96 === 0) process.stdout.write(`scene ${i}\n`);
  }
  if (!only) {
    fs.writeFileSync(path.join(CACHE, 'measure.json'), JSON.stringify(meas));
    for (let k = 0; k < 72; k++) save(`title_${String(k).padStart(3, '0')}.jpg`, await pg.evaluate(([k]) => R.card('title', k, 72), [k]));
    for (let k = 0; k < 72; k++) save(`end_${String(k).padStart(3, '0')}.jpg`, await pg.evaluate(([k]) => R.card('end', k, 72), [k]));
  }
  await b.close();
})();
