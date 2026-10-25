// measures foot slip: world x of each planted (unlifted) foot between consecutive frames, from the gait solver output
import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const { chromium } = require(require.resolve('playwright', { paths: ['/opt/node-tools/node_modules'] }));
import path from 'path'; import fs from 'fs';
const here = path.dirname(new URL(import.meta.url).pathname);
const b = await chromium.launch(); const p = await b.newPage();
await p.addInitScript(`window.SCORE=${fs.readFileSync(path.join(here, '../../score/threshold-score.json'))};`);
await p.goto('file://' + path.join(here, 'stage.html'));
const r = await p.evaluate(() => { initGait(); const G = getGait(), F = SCORE.frames; let maxSlip = 0, at = null, n = 0, maxReach = 0;
  for (let i = 1; i < G.length; i++) { if (!G[i] || !G[i - 1]) continue; for (let k = 0; k < 4; k++) {
    maxReach = Math.max(maxReach, Math.abs(G[i][k][0]));
    if (G[i][k][2] === 0 && G[i - 1][k][2] === 0) { const w1 = F[i].dog.x * 100 + G[i][k][0], w0 = F[i - 1].dog.x * 100 + G[i - 1][k][0]; const s = Math.abs(w1 - w0); n++; if (s > maxSlip) { maxSlip = s; at = [i, k]; } } } }
  return { maxSlipCm: maxSlip, at, pairs: n, maxFootOffsetCm: maxReach }; });
console.log(JSON.stringify(r)); fs.writeFileSync(path.join(here, 'cache', 'gaitcheck.json'), JSON.stringify(r));
await b.close();
