// SCION-27 · reproducibility test: render the same scene frames twice, in two fresh bundles/browser sessions,
// as lossless PNG, and compare SHA-256. Also compares with the hashes of the previous accepted build (../repro.json).
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import {HERE, serve, stills} from './rlib.mjs';
const FRAMES = [0, 30, 86, 100, 180, 216, 456, 576, 650, 767];
const FOLDER = path.resolve(HERE, '..');
const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const runs = [];
for (const k of [0, 1]) {
  const dir = path.join(HERE, `cache/repro${k}/`); fs.rmSync(dir, {recursive: true, force: true}); fs.mkdirSync(dir, {recursive: true});
  const s = await serve();
  runs.push((await stills(s, 'Scene', FRAMES, dir, 'png')).map(sha));
}
const manifestHash = sha(path.join(HERE, 'cache/manifest.json'));
let prev = null; try { prev = JSON.parse(fs.readFileSync(path.join(FOLDER, 'repro.json'), 'utf8')); } catch {}
const rows = FRAMES.map((f, j) => ({frame: f, a: runs[0][j], same_in_two_runs: runs[0][j] === runs[1][j],
  same_as_previous_build: prev ? (prev.frames.find(r => r.frame === f) || {}).a === runs[0][j] : null}));
const out = {schema: 'scion27.repro/1', manifest_sha256: manifestHash, renderer: 'remotion 4.0.538 + chrome-headless-shell 1243 (playwright), swangle',
  machines: 'one machine only; cross-machine equality not tested', all_equal_two_runs: rows.every(r => r.same_in_two_runs),
  previous_build_manifest_same: prev ? prev.manifest_sha256 === manifestHash : null, frames: rows};
fs.writeFileSync(path.join(FOLDER, 'repro.json'), JSON.stringify(out, null, 1));
console.log('repro: two runs equal =', out.all_equal_two_runs, ' frames', FRAMES.length);
