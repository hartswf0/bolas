// model sheets of the drawing library -> proof/library_*.jpg
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const D = path.join(__dirname, '..'); const LIB = JSON.parse(fs.readFileSync(D + '/scene/library.json')); const PAL = JSON.parse(fs.readFileSync(D + '/scene/palette.json'));
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.goto('file://' + __dirname + '/sheet.html');
  const E = LIB.elements; const sel = (el, f) => Object.keys(E[el]).filter(f || (() => true)).map((id) => [el, id]);
  const sheets = {
    body: [sel('dog_body', (k) => !/^(walk|cwalk|lwalk)/.test(k)), 6, 360],
    walk: [sel('dog_body', (k) => /^lwalk/.test(k)), 8, 300],
    heads: [[...sel('dog_head'), ...sel('dog_tail')], 8, 520],
    ears: [sel('dog_ear'), 8, 700],
    person: [sel('person'), 5, 150],
  };
  for (const k in sheets) {
    const [which, cols, sc] = sheets[k];
    const url = await p.evaluate(([L, P, w, c, s]) => window.sheet(L, P, w, c, s, 0.6), [LIB, PAL, which, cols, sc]);
    fs.writeFileSync(D + `/proof/library_${k}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
  }
  await b.close();
})();
