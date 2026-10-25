// node build/render.js MODE [frames...]
//   MODE film   : title (72) + scene (768) + end card (72) -> build/cache/picture.mp4, and build/cache/measure.json
//   MODE stills : the listed scene frames -> build/cache/frames/fNNN.jpg (and idNNN.png with --id)
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const B = __dirname, CACHE = path.join(B, 'cache');
(async () => {
  const mode = process.argv[2], args = process.argv.slice(3);
  const xs = JSON.parse(fs.readFileSync(path.join(B, 'xsheet.json')));
  xs.foley = JSON.parse(fs.readFileSync(path.join(B, 'foley.json')));
  const at = JSON.parse(fs.readFileSync(path.join(B, 'audio_timeline.json')));
  const door = at.events.find(e => e.id === 'door'); xs.door_creak = [door.t0, door.t1];
  const endLines = JSON.parse(fs.readFileSync(path.join(B, 'endcard.json')));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => console.log('console', m.text()));
  await p.goto('file://' + path.join(B, 'render.html'));
  const N = await p.evaluate(x => init(x), xs);
  const jpg = d => Buffer.from(d.split(',')[1], 'base64');
  if (mode === 'stills') {
    const dir = path.join(CACHE, 'frames'); fs.mkdirSync(dir, { recursive: true });
    const wantId = args.includes('--id');
    for (const a of args.filter(a => !a.startsWith('--'))) {
      const i = +a; const r = await p.evaluate(i => scene(i, true), i);
      fs.writeFileSync(path.join(dir, `f${String(i).padStart(3, '0')}.jpg`), jpg(r.jpg));
      if (wantId) fs.writeFileSync(path.join(dir, `id${String(i).padStart(3, '0')}.png`), jpg(await p.evaluate(i => idImage(i), i)));
      console.log(i, JSON.stringify(r.m));
    }
  } else {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', path.join(CACHE, 'picture.mp4')]);
    const put = async d => { if (!ff.stdin.write(jpg(d))) await new Promise(r => ff.stdin.once('drain', r)); };
    const meas = [];
    for (let k = 0; k < 72; k++) await put(await p.evaluate(k => titleCard(k), k));
    for (let i = 0; i < N; i++) { const r = await p.evaluate(i => scene(i, true), i); await put(r.jpg); meas.push({ i, ...r.m }); if (i % 192 === 0) console.log('scene frame', i); }
    for (let k = 0; k < 72; k++) await put(await p.evaluate(([k, l]) => endCard(k, l), [k, endLines]));
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    fs.writeFileSync(path.join(CACHE, 'measure.json'), JSON.stringify(meas));
    const made = await p.evaluate(() => DOG.made());
    fs.writeFileSync(path.join(CACHE, 'sprites_used.json'), JSON.stringify({ dog_drawings_made: made }));
    console.log('done', 72 + N + 72, 'frames; dog drawings made', made);
  }
  await b.close();
})();
