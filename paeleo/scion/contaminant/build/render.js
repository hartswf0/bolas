/* Renders the contaminant jelly film: steps contaminant.html?render=1 at a fixed 1/24 s, pipes every frame to ffmpeg,
   and writes the run's events, ledger and invariant counts beside the film. Run through make.sh. */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const CINE = !!process.env.CINEMA, FPS = 24, DUR = CINE ? 47 : 41, N = FPS * DUR, SEED = 8;
// MOOD=1 renders the textless cut (archive frames instead of words) into ../mood/
// CINEMA=1 renders the film as cinema (camera, inserts, intercut reel, coda) into ../cinema/
const MOOD = !!process.env.MOOD, kind = CINE ? 'cinema' : MOOD ? 'mood' : '', tag = kind ? '-' + kind : '';
const here = __dirname, out = path.join(here, '..', kind), page = path.resolve(here, '../../contaminant.html');
fs.mkdirSync(out, { recursive: true });

// serve the repository over http so archive images load same-origin (file:// would taint the canvas)
const http = require('http'), ROOT = path.resolve(here, '../../../..');
const TYPES = {'.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.png': 'image/png', '.json': 'application/json', '.css': 'text/css'};
const server = http.createServer((req, res) => {
  const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, {'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream'}); fs.createReadStream(f).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}/${path.relative(ROOT, page)}`;
  const browser = await chromium.launch();
  const p = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(`${base}?render=1&seed=${SEED}${CINE ? '&cinema=1' : MOOD ? '&mood=1' : ''}`);
  await p.waitForFunction(() => window.SCION_CONTAMINANT && window.SCION_CONTAMINANT.ledger().length > 0);

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', CINE ? '27' : '24', '-preset', 'slow', '-tune', CINE ? 'grain' : 'animation', path.join(here, `video${tag}.mp4`)],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const closed = new Promise(r => ff.on('close', r));
  for (let i = 0; i < N; i++) {
    const url = await p.evaluate(([i, f, d]) => window.SCION_CONTAMINANT.frame(i, f, d), [i, FPS, DUR]);
    if (!ff.stdin.write(Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 96 === 0) process.stdout.write(`frame ${i}/${N}\n`);
  }
  ff.stdin.end();
  const code = await closed;

  const events = await p.evaluate(() => window.SCION_CONTAMINANT.events());
  const stats = await p.evaluate(() => window.SCION_CONTAMINANT.stats());
  const ledger = await p.evaluate(() => window.SCION_CONTAMINANT.ledger());
  await browser.close(); server.close();
  fs.writeFileSync(path.join(out, 'events.json'), JSON.stringify({ fps: FPS, duration: DUR, seed: SEED, events }, null, 1));
  fs.writeFileSync(path.join(out, 'ledger.txt'), ledger.join('\n') + '\n');
  const violations = stats.v1 + stats.v2 + stats.v3 + stats.v4 + stats.v5;
  fs.writeFileSync(path.join(out, 'invariants.json'), JSON.stringify({
    seed: SEED, fps: FPS, frames: N, pageErrors: errors, violations,
    I1_provenance: { seams: stats.contam, violations: stats.v1 },
    I2_in_frame: { checks: stats.checks, violations: stats.v2 },
    I3_stage_monotone: { transitions: stats.trans, violations: stats.v3 },
    I4_population_cap: { final: stats.population, violations: stats.v4 },
    I5_cuts_kept: { cuts: stats.cuts, rescued: stats.rescued, violations: stats.v5 },
    I6_open_card_clear: { framesShown: stats.focusFrames, maxOverlapWithJellyfish: +stats.ovMax.toFixed(3), framesOver10pct: stats.ovFrames },
    returns: stats.returns }, null, 1));
  console.log(`ffmpeg exit ${code}; ${events.length} events; ${stats.cuts} cuts; ${stats.rescued} rescued; ${stats.contam} seams; ${violations} violations; ${errors.length} page errors`);
  if (code !== 0 || errors.length || violations) process.exit(1);
})().catch(e => { console.error(e); process.exit(1); });
