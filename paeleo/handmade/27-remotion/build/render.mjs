// SCION-27 · render engineer. node build/render.mjs [film] [matte] [stills]
// One bundle; the Film composition (title + 768-frame scene + end card, with the synthesised mix) is rendered by Remotion,
// the DogMatte composition (same Dog component, flat matte colours, same clipping) is rendered to PNGs for measurement.
import fs from 'fs';
import path from 'path';
import {HERE, R, serve, stills, browserExecutable, chromiumOptions} from './rlib.mjs';

const want = new Set(process.argv.slice(2).length ? process.argv.slice(2) : ['film', 'matte', 'stills']);
const FOLDER = path.resolve(HERE, '..');
const t0 = Date.now();
const serveUrl = await serve();
console.log('bundled', ((Date.now() - t0) / 1000).toFixed(1), 's');
const conc = Number(process.env.SCION27_CONCURRENCY || 3);

if (want.has('film')) {
  const composition = await R.selectComposition({serveUrl, id: 'Film', browserExecutable, chromiumOptions, logLevel: 'error'});
  let last = -1;
  await R.renderMedia({composition, serveUrl, codec: 'h264', crf: 16, outputLocation: path.join(HERE, 'cache/film_raw.mp4'),
    browserExecutable, chromiumOptions, concurrency: conc, audioCodec: 'aac', logLevel: 'error',
    onProgress: ({progress}) => { const p = Math.floor(progress * 10); if (p !== last) { last = p; console.log('film', p * 10, '%'); } }});
  console.log('film_raw.mp4 done', ((Date.now() - t0) / 1000).toFixed(1), 's');
}
if (want.has('matte')) {
  const dir = path.join(HERE, 'cache/matte'); fs.rmSync(dir, {recursive: true, force: true}); fs.mkdirSync(dir, {recursive: true});
  const composition = await R.selectComposition({serveUrl, id: 'DogMatte', browserExecutable, chromiumOptions, logLevel: 'error'});
  await R.renderFrames({composition, serveUrl, outputDir: dir, imageFormat: 'png', inputProps: {}, concurrency: conc,
    browserExecutable, chromiumOptions, logLevel: 'error', onStart: () => {}, onFrameUpdate: (n) => { if (n % 128 === 0) console.log('matte', n); }});
  console.log('matte done', fs.readdirSync(dir).length, 'frames', ((Date.now() - t0) / 1000).toFixed(1), 's');
}
if (want.has('stills')) {
  const dir = path.join(FOLDER, 'stills'); fs.mkdirSync(dir, {recursive: true});
  const tmp = path.join(HERE, 'cache/stills'); fs.mkdirSync(tmp, {recursive: true});
  const map = {86: 'still_03.6s.jpg', 216: 'still_09.0s.jpg', 456: 'still_19.0s.jpg', 672: 'still_28.0s.jpg'};
  const outs = await stills(serveUrl, 'Scene', Object.keys(map).map(Number), tmp + '/');
  for (const o of outs) { const fr = Number(path.basename(o).match(/(\d{4})/)[1]); fs.copyFileSync(o, path.join(dir, map[fr])); }
  console.log('stills', Object.values(map).join(' '));
}
