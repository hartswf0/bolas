// Mobile acceptance test of the operator page: serves the repo over http (own PID), opens index.html at phone size,
// taps to play, checks the live puppet advances, scrubs, switches view, taps the dog's hit area. Writes ../proof/mobile-*.png and mobile-test.json.
const { chromium, devices } = require('playwright'), { spawn } = require('child_process'), path = require('path'), fs = require('fs');
(async () => {
  const R = path.resolve(__dirname, '../../../..'), port = 8725 + Math.floor(Math.random() * 200);
  const srv = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { cwd: R, stdio: 'ignore' });
  await new Promise(r => setTimeout(r, 1200)); const res = { port, server_pid: srv.pid };
  try {
    const b = await chromium.launch(); const ctx = await b.newContext({ ...devices['iPhone 13'] }); const p = await ctx.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    await p.goto(`http://127.0.0.1:${port}/paeleo/handmade/25-rive/index.html`); await p.evaluate(() => window.ready);
    const t0 = Date.now(); await p.tap('#tap'); await p.waitForFunction(() => +document.getElementById('scrub').value > 0); res.tap_to_first_advance_ms = Date.now() - t0;
    await p.waitForTimeout(2500); res.scene_frame_after_2_5s = +(await p.$eval('#scrub', e => e.value));
    res.ms_per_drawn_frame = await p.evaluate(() => { const a = performance.now(); for (let k = 0; k < 5; k++) frame(FILM.TITLE + 300 + k); return (performance.now() - a) / 5; });
    await p.screenshot({ path: path.join(__dirname, '../proof/mobile-playing.png') });
    await p.tap('#pp'); await p.$eval('#scrub', e => { e.value = 650; e.dispatchEvent(new Event('input')); }); await p.waitForTimeout(300);
    await p.tap('#view'); await p.waitForTimeout(300);
    const box = await p.evaluate(() => FILM.dogState().bbox), cb = await p.$eval('#c', e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; });
    await p.touchscreen.tap(cb[0] + (box[0] + box[2]) / 2 * cb[2] / 1280, cb[1] + (box[1] + box[3]) / 2 * cb[3] / 720); await p.waitForTimeout(200);
    res.hit_area_text = await p.$eval('#state', e => e.textContent);
    await p.screenshot({ path: path.join(__dirname, '../proof/mobile-view-change.png') });
    res.layers_after_view_change = await p.evaluate(() => FILM.dogState().layers);
    res.page_errors = errs; res.no_horizontal_scroll = await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
    await b.close();
  } finally { srv.kill(); }
  res.pass = res.scene_frame_after_2_5s > 50 && res.tap_to_first_advance_ms < 1500 && res.hit_area_text.startsWith('You touched the dog') && !res.page_errors.length && res.no_horizontal_scroll;
  fs.writeFileSync(path.join(__dirname, '../proof/mobile-test.json'), JSON.stringify(res, null, 1)); console.log(JSON.stringify(res));
})();
