// SCION 32 · drive the WebGL renderer in headless Chromium (SwiftShader), pipe JPEG frames into ffmpeg, keep the measurements.
// node render.js scene            -> cache/scene.mp4 (768 frames) + cache/measure.json
// node render.js frames 0,86,...   -> cache/probe/f_<i>.jpg (look at single frames)
const path = require('path'), fs = require('fs'), { spawn } = require('child_process');
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const HERE = __dirname, CACHE = path.join(HERE, 'cache');
const SCORE = JSON.parse(fs.readFileSync(path.join(HERE, '../../score/threshold-score.json')));
fs.mkdirSync(CACHE, { recursive: true });

async function open() {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => console.log('[page error]', e.message));
  await page.goto('file://' + path.join(HERE, 'render.html'));
  console.log(await page.evaluate(s => window.init(s), SCORE));
  if (process.env.CAM) await page.evaluate(c => { window.CAM_OVERRIDE = JSON.parse(c); }, process.env.CAM);
  return { browser, page };
}
const strip = d => Buffer.from(d.slice(d.indexOf(',') + 1), 'base64');

(async () => {
  const mode = process.argv[2] || 'scene';
  const { browser, page } = await open();
  if (mode === 'frames') {
    const dir = path.join(CACHE, 'probe'); fs.mkdirSync(dir, { recursive: true });
    for (const s of process.argv[3].split(',')) {
      const i = Math.round(parseFloat(s)); const t0 = Date.now();
      const r = await page.evaluate(i => window.renderFrame(i, { q: 0.92 }), i);
      fs.writeFileSync(path.join(dir, `f_${String(i).padStart(3, '0')}.jpg`), strip(r.jpeg));
      console.log(i, (Date.now() - t0) + 'ms', JSON.stringify({ dog: r.meas.dog, head: r.meas.head, nose: r.meas.nose.slice(0, 2).map(Math.round) }));
    }
  } else if (mode === 'scene') {
    const out = path.join(CACHE, 'scene.mp4');
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const meas = []; const t0 = Date.now();
    const N = SCORE.frames.length;
    for (let i = 0; i < N; i++) {
      const r = await page.evaluate(i => window.renderFrame(i, { q: 0.93 }), i);
      meas.push(r.meas);
      if (!ff.stdin.write(strip(r.jpeg))) await new Promise(res => ff.stdin.once('drain', res));
      if (i % 48 === 0) console.log('frame', i, ((Date.now() - t0) / (i + 1)).toFixed(0) + ' ms/frame');
    }
    ff.stdin.end(); await new Promise(res => ff.on('close', res));
    fs.writeFileSync(path.join(CACHE, 'measure.json'), JSON.stringify(meas));
    console.log('scene frames', N, 'written', out);
  } else if (mode === 'cards') {
    const R = require('./rig.js');
    const T = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'proof', 'fk_tests.json')));
    const curves = JSON.parse(fs.readFileSync(path.join(CACHE, 'curves.json')));
    const tr = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'trace.json')));
    const snd = JSON.parse(fs.readFileSync(path.join(CACHE, 'sound_levels.json')));
    // tree layout of the dog's joint graph
    const kids = {}; R.DOG.forEach(([n, p]) => { if (p) (kids[p] = kids[p] || []).push(n); });
    const order = ['waist', 'tail0', 'hipR', 'hipL', 'neck', 'cloth', 'shoulderR', 'shoulderL', 'earR0', 'earL0', 'flapR0', 'flapL0'];
    for (const k in kids) kids[k].sort((a, b) => (order.indexOf(a) + 99) % 99 - (order.indexOf(b) + 99) % 99);
    const nodes = []; let leaf = 0;
    const short = { root: 'root', pelvis: 'pelvis', waist: 'waist', neck: 'neck', head: 'head*', cloth: 'cloth', tail0: 'tail', tail4: 'x5 beads' };
    (function lay(n, d, parent) {
      const ch = kids[n] || []; let y;
      if (!ch.length) { y = leaf++ * 26; }
      else { const ys = ch.map(c => lay(c, d + 1, n)); y = (ys[0] + ys[ys.length - 1]) / 2; }
      const prop = /^cloth|^flap/.test(n);
      let label = short[n] || ((/(R|L)1$/.test(n) || /paw/.test(n)) ? n : (/^(hip|shoulder)/.test(n) ? n : null));
      if (/^tail[123]$/.test(n)) label = null;
      nodes.push({ name: n, parent, x: d * 74, y, prop, label });
      return y;
    })('root', 0, null);
    const ons = tr.summary.onsets_measured;
    const f1 = v => v.toFixed(2);
    const T4 = T.T4_contact;
    const lines = [
      'The dog: a carved, painted wooden toy drawn in code: 30 blocks on brass pins, joints set by local angles only.',
      'Every pose = parent x pivot offset x local rotation, multiplied down the tree from the root. No IK solve anywhere.',
      'Its felt saddle cloth, ear leaves and bead tail are chains on the same tree; the person\'s cuffs and hem too.',
      '!Bone lengths constant over 768 frames: max error ' + T.T1_bone_lengths.max_err_m.toExponential(0) + ' m.  Turn a hip 12 deg: every descendant',
      '!moves by exactly the hip\'s own change (max error ' + Math.max(...T.T3_propagation.map(x => x.children_follow_max_err)).toExponential(0) + '); nothing else moves (0).',
      '!Planted paws, from hand-keyed hip/knee angles: walking slip ' + T4.walk.mean_mm.toFixed(1) + ' mm/frame (max ' + T4.walk.max_mm.toFixed(0) + '), drift <= ' + T4.stance_drift.max_mm.toFixed(0) + ' mm per step;',
      '!turning in place they slide (max ' + T4.turn.max_mm.toFixed(0) + ' mm/frame): measured, not hidden.',
      'Choices measured on the render: back away ' + f1(ons[0].t) + ' s, turn its back ' + f1(ons[2].t) + ', head round ' + f1(ons[3].t) + ', come ' + f1(ons[4].t) + ', lie ' + f1(ons[5].t) + ', look in ' + f1(ons[6].t) + '.',
      'Sound synthesized: soft voice ' + snd.soft_vs_call_db.toFixed(0) + ' dB under the calls; the paw taps fall on the rig\'s own footfalls.',
    ];
    const marks = [[1.0, 'away'], [3.42, 'back'], [7.46, 'look'], [14.71, 'come'], [23.79, 'lie'], [26.4, 'in']];
    const dir = CACHE;
    const shot = await page.evaluate(() => { window.CAM_OVERRIDE = { pos: [1.15, 0.42, 2.95], tgt: [-0.05, 0.36, 2.28], fov: 34 }; const r = window.renderFrame(470, { q: 0.92, noMeasure: true }); window.CAM_OVERRIDE = null; return r.jpeg; });
    fs.writeFileSync(path.join(dir, 'title_bg.jpg'), strip(shot));
    const title = await page.evaluate(img => window.drawCard('title', { img }), shot);
    fs.writeFileSync(path.join(dir, 'title.png'), strip(title));
    const end = await page.evaluate(d => window.drawCard('end', d), { lines, graph: { nodes }, curves, marks });
    fs.writeFileSync(path.join(dir, 'end.png'), strip(end));
    console.log('cards written');
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
