// usage: node shoot.mjs <out.png> <js expression run in page after init>
import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const { chromium } = require(require.resolve('playwright', { paths: [process.env.NODE_PATH || '', '/opt/node-tools/node_modules'].filter(Boolean) }));
import path from 'path'; import fs from 'fs';
const here = path.dirname(new URL(import.meta.url).pathname);
const [out, expr] = process.argv.slice(2);
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
p.on('console', m => console.log('page:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
await p.addInitScript(`window.SCORE=${fs.readFileSync(path.join(here, '../../score/threshold-score.json'))};`);
const texd={}; for (const n of ['wash0','wash1','wash2','paper','wood','speck']) texd[n]='data:image/png;base64,'+fs.readFileSync(path.join(here,'cache',n+'.png')).toString('base64');
await p.addInitScript(`window.TEXDATA=${JSON.stringify(texd)};`);
await p.goto('file://' + path.join(here, process.env.PAGE || 'stage.html'));
await p.evaluate(async () => { await loadTextures('cache/'); await document.fonts.ready; if (window.initScene) await initScene(); });
await p.evaluate(expr);
const url = await p.evaluate(() => document.getElementById('c').toDataURL('image/png'));
fs.writeFileSync(out, Buffer.from(url.split(',')[1], 'base64'));
await b.close();
