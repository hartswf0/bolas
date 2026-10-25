// Render the film picture (38 s, 912 frames) and measure the dog in every scene frame.
// node build/render.js film            -> build/cache/picture.mp4, build/cache/meas.json
// node build/render.js stills t1,t2..  -> build/cache/stills/s_<t>.jpg   (scene seconds)
const { chromium } = require('/opt/node-tools/node_modules/playwright'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const B = __dirname, C = path.join(B, 'cache'), FOLD = path.join(B, '..');
(async () => {
  const mode = process.argv[2] || 'film';
  const bank = JSON.parse(fs.readFileSync(path.join(FOLD, 'bank', 'bank.json')));
  const pth = JSON.parse(fs.readFileSync(path.join(C, 'path.json')));
  const cues = JSON.parse(fs.readFileSync(path.join(C, 'cues.json')));
  const dogN = Object.values(bank.drawings).filter(d => d.meta.group !== 'person').length;
  const used = pth.summary.drawings_used.length;
  const DATA = {
    bank, path: pth, lines: cues.lines,
    titleStrip: ['watch', 'back_2', 'q45_low', 'f90_low', 'q135_low', 'lie_R', 'lookback_R', 'rise_R', 'f90_qleft', 'walk_3', 'lie_up', 'look_in', 'rest'],
    endKeys: cues.end_keys,
    endText: [
      `The dog is ${dogN} drawings in one illustration bank, inked for this film (${used} were chosen), studied from a`,
      'home-movie dog (Amateur Film New Jersey C, public domain). No drawing is warped or tweened.',
      'It moves only by choosing one drawing per frame: a Viterbi path over pose distance to the PAELEO score plus a',
      'transition penalty; its walks are set on a gait chart so a planted paw stays on its board.',
      'Person, door and porch are drawn in the same ink; the person is cast from its own bank by the same search.',
      'The voice and every sound were synthesized here; nothing was recorded.',
    ],
  };
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => console.log('console', m.text()));
  await p.goto('file://' + path.join(B, 'render.html'));
  await p.evaluate(() => window.ready);
  await p.evaluate(async () => { for (const f of ['800 64px "Big Shoulders Display"', 'italic 400 30px Literata', '400 21px Literata', '600 34px Literata', '400 15px "JetBrains Mono"']) await document.fonts.load(f); });
  await p.evaluate(d => setData(d), DATA);
  const N = await p.evaluate(() => N);
  if (mode === 'stills') {
    fs.mkdirSync(path.join(C, 'stills'), { recursive: true });
    const ts = process.argv[3].split(',');
    for (const s of ts) {
      let n; if (s.startsWith('f')) n = +s.slice(1); else n = 72 + Math.round(+s * 24);
      const r = await p.evaluate(n => frame(n, .92), n);
      fs.writeFileSync(path.join(C, 'stills', `s_${s}.jpg`), Buffer.from(r.img.split(',')[1], 'base64'));
    }
    await b.close(); console.log('stills', ts.length); return;
  }
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p', path.join(C, 'picture.mp4')]);
  const meas = [];
  for (let n = 0; n < N; n++) {
    const r = await p.evaluate(n => frame(n, .93), n);
    if (r.meas) meas.push({ i: n - 72, ...r.meas });
    const ok = ff.stdin.write(Buffer.from(r.img.split(',')[1], 'base64'));
    if (!ok) await new Promise(res => ff.stdin.once('drain', res));
    if (n % 120 === 0) console.log('frame', n, '/', N);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  fs.writeFileSync(path.join(C, 'meas.json'), JSON.stringify(meas));
  await b.close(); console.log('done', N, 'frames');
})();
