// SCION 20 · render driver: evaluates the node graph in Chromium for every frame and writes JPEGs to build/cache/frames,
// plus the render's own measurements (build/cache/measure.json). Usage: node render.js [first last]   (scene frames)
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const D = path.join(__dirname, '..'), C = path.join(__dirname, 'cache'), FR = path.join(C, 'frames');
const J = (f) => JSON.parse(fs.readFileSync(path.join(D, f)));
(async () => {
  fs.mkdirSync(FR, { recursive: true });
  const LIB = J('scene/library.json'), PAL = J('scene/palette.json'), XS = J('scene/xsheet.json'), GRAPH = J('scene/nodegraph.json');
  const onlyCards = process.argv[2] === 'cards';
  const a = onlyCards ? 0 : process.argv[2] != null ? +process.argv[2] : 0, b = onlyCards ? -1 : process.argv[3] != null ? +process.argv[3] : 767, cards = process.argv[2] == null || onlyCards;
  const br = await chromium.launch(); const pg = await br.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('console', (m) => console.log('page:', m.text())); pg.on('pageerror', (e) => { console.error('PAGE ERROR', e); process.exit(1); });
  await pg.goto('file://' + path.join(__dirname, 'render.html'));
  await pg.evaluate(([l, p, x, g]) => window.init(l, p, x, g), [LIB, PAL, XS, GRAPH]);
  const save = (name, url) => fs.writeFileSync(path.join(FR, name), Buffer.from(url.split(',')[1], 'base64'));
  const meas = {}; const t0 = Date.now();
  for (let f = a; f <= b; f++) {
    const r = await pg.evaluate((f) => window.renderScene(f, true), f);
    save(`s${String(f).padStart(4, '0')}.jpg`, r.url); meas[f] = r.m;
    if (f % 100 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(1) + 's');
  }
  const mf = path.join(C, 'measure.json');
  if (onlyCards) Object.keys(meas).forEach((k) => delete meas[k]); let old = {}; try { old = JSON.parse(fs.readFileSync(mf)); } catch (e) {}
  fs.writeFileSync(mf, JSON.stringify(Object.assign(old, meas)));
  if (cards) {
    const tsv = fs.readFileSync(path.join(D, 'scene/xsheet.tsv'), 'utf8').trim().split('\n').map((l) => l.split('\t'));
    const xs = [['frame', 'dog_body', 'dog_head', 'dog_ear', 'person'], ...tsv.slice(178, 206).map((r) => [r[0], r[2], r[3], r[4], r[6]])];
    const n = LIB.counts;
    const lines = [
      `Every drawing of the dog and the person is constructed in code (build/01_library.js): ${n.dog_body} body drawings (stand, crouch, 3 walk cycles of 16, lowering, lying,`,
      `front, 3/4 front, back, 3/4 back), ${n.dog_head} heads (profile, 3/4 front, front, 3/4 back, back, back-of-head looking in; eyes open/shut), ${n.dog_ear} ear and ${n.dog_tail} tail drawings, ${n.person} person poses, ${n.person_mouth} mouths.`,
      'Turns are whole-drawing substitutions on the exposure sheet; the neck (curve deformer) and tail (6-joint chain) flex in between. Tone, highlight and outline are node passes;',
      'the dusk and lamp palettes are mixed by the light node. Background painted in code. Sound synthesized (no recordings). No photographs, no web images.',
    ];
    for (let k = 0; k < 72; k++) save(`t${String(k).padStart(4, '0')}.jpg`, await pg.evaluate((k) => window.card('title', k, {}), k));
    for (let k = 0; k < 72; k++) save(`e${String(k).padStart(4, '0')}.jpg`, await pg.evaluate(([k, i]) => window.card('end', k, i), [k, { lines, xs }]));
  }
  await br.close(); console.log('rendered', a, b, ((Date.now() - t0) / 1000).toFixed(1) + 's');
})();
