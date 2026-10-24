/* The Crank Boy: opening film.
   Crank Boy turns a 1910 hand-cranked projector. What he cranks is what you see:
   the screen's light, the reels and the clatter all follow his crank speed.
   Data: window.CRANK (registry), window.CRANK_LINES (captions + voice lengths).
   Voices: assets/film/vo/<id>.mp3, recorded with Kokoro by registry/voices.py. */
window.CrankFilm = (() => {
  const R = window.CRANK, L = window.CRANK_LINES || {};
  const $ = id => document.getElementById(id);
  const el = $('film'), cv = $('fcv'), ctx = cv.getContext('2d');
  const TAU = Math.PI * 2, INK = '#2B2320';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ease = u => u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
  const cl = (u, a, b) => Math.max(0, Math.min(1, (u - a) / (b - a)));
  const lerp = (a, b, t) => a + (b - a) * t;
  const rnd = (a = 1) => Math.random() * a;

  /* ---------- assets ---------- */
  const img = src => { const i = new Image(); i.src = src; return i; };
  const SERIES = Object.fromEntries(R.series.map(s => [s.id, img(s.image)]));
  const PAN = ['air-cabs', 'skates', 'phono-cinema', 'firemen', 'barber', 'scrubber'];
  const ROWS = ['argon', 'claude'], COLS = ['ludic', 'hist', 'studio'];
  const M = Object.fromEntries(R.models.map(m => [m.id, m])), P = Object.fromEntries(R.prompts.map(p => [p.id, p]));
  const cellOf = (c, r) => { const a = R.agents.find(x => x.prompt === c && x.model === r); return a && R.versions.filter(v => v.agent === a.id).sort((x, y) => (y.date || '').localeCompare(x.date || ''))[0]; };
  const GRID = ROWS.flatMap((r, ri) => COLS.map((c, ci) => { const v = cellOf(c, r); return { r, c, ri, ci, v, im: v ? img(v.card) : null, crank: v ? /crank/i.test(v.youPlay) : false }; }));
  const SHOT = { crank: img('assets/film/shots/v1-crank.jpg'), stop: img('assets/film/shots/v1-stop.jpg') };
  const filmRef = (R.lab && R.lab.films || []).find(f => f.video);
  let video = null, poster = filmRef && filmRef.poster ? img(filmRef.poster) : null;
  function ensureVideo() {
    if (video || !filmRef) return;
    video = document.createElement('video');
    video.muted = true; video.playsInline = true; video.preload = 'auto'; video.src = filmRef.video;
    video.addEventListener('error', () => { video = null; });
  }

  /* ---------- sound ---------- */
  let sound = true, AC = null, master, proj, projGain, music, musicGain, analyser = null, abuf = null;
  const VO = {};
  Object.keys(L).forEach(id => { const a = new Audio(); a.preload = 'auto'; a.src = 'assets/film/vo/' + id + '.mp3'; VO[id] = a; });
  function audioInit() {
    if (AC) return;
    try {
      AC = new (window.AudioContext || window.webkitAudioContext)();
      master = AC.createGain(); master.gain.value = .9; master.connect(AC.destination);
      // projector clatter: looped noise through a band-pass, gated per frame by crank speed
      const len = AC.sampleRate * 2, b = AC.createBuffer(1, len, AC.sampleRate), d = b.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      proj = AC.createBufferSource(); proj.buffer = b; proj.loop = true;
      const bp = AC.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1800; bp.Q.value = .7;
      projGain = AC.createGain(); projGain.gain.value = 0;
      proj.connect(bp).connect(projGain).connect(master); proj.start();
      musicGain = AC.createGain(); musicGain.gain.value = 0; musicGain.connect(master);
      // voice level for Crank Boy's mouth (only same-origin http; file:// would silence the voice)
      if (location.protocol.startsWith('http')) {
        analyser = AC.createAnalyser(); analyser.fftSize = 512; abuf = new Uint8Array(analyser.fftSize); analyser.connect(master);
        Object.values(VO).forEach(a => { try { AC.createMediaElementSource(a).connect(analyser); } catch (e) {} });
      }
    } catch (e) { AC = null; }
  }
  function tone(f, dur, vol, type = 'sine', when = 0) {
    if (!AC || !sound) return;
    const t0 = AC.currentTime + when, o = AC.createOscillator(), g = AC.createGain();
    o.type = type; o.frequency.value = f; g.gain.setValueAtTime(vol, t0); g.gain.exponentialRampToValueAtTime(.0001, t0 + dur);
    o.connect(g).connect(master); o.start(t0); o.stop(t0 + dur + .05);
  }
  function noiseHit(dur, vol, freq, type = 'highpass') {
    if (!AC || !sound) return;
    const n = AC.createBufferSource(), len = Math.floor(AC.sampleRate * dur), b = AC.createBuffer(1, len, AC.sampleRate), d = b.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
    n.buffer = b; const f = AC.createBiquadFilter(); f.type = type; f.frequency.value = freq; const g = AC.createGain(); g.gain.value = vol;
    n.connect(f).connect(g).connect(master); n.start();
  }
  const click = () => noiseHit(.03, .18, 3000);
  const thump = () => { tone(70, .35, .35, 'sine'); noiseHit(.08, .2, 600, 'lowpass'); };
  const whoosh = () => { if (!AC || !sound) return; const n = AC.createBufferSource(), len = AC.sampleRate * .6, b = AC.createBuffer(1, len, AC.sampleRate), d = b.getChannelData(0); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.sin(Math.PI * i / len); n.buffer = b; const f = AC.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 1.5; f.frequency.setValueAtTime(400, AC.currentTime); f.frequency.exponentialRampToValueAtTime(3000, AC.currentTime + .5); const g = AC.createGain(); g.gain.value = .22; n.connect(f).connect(g).connect(master); n.start(); };
  const bell = () => [0, .3, .6].forEach(w => { tone(1320, 1.4, .12, 'sine', w); tone(1980, .9, .04, 'sine', w); });
  // a small music box waltz, played only under the title and the postcards
  const TUNE = [72, 76, 79, 76, 77, 81, 79, 76, 74, 77, 76, 72, 71, 74, 72, 67];
  let musicOn = false, musicStep = 0, musicNext = 0;
  function musicTick() {
    if (!AC || !musicOn || !sound) return;
    while (musicNext < AC.currentTime + .25) {
      const n = TUNE[musicStep % TUNE.length], f = 440 * Math.pow(2, (n - 69) / 12), t0 = Math.max(musicNext, AC.currentTime);
      const o = AC.createOscillator(), g = AC.createGain(); o.type = 'sine'; o.frequency.value = f; g.gain.setValueAtTime(.06, t0); g.gain.exponentialRampToValueAtTime(.0001, t0 + .9);
      o.connect(g).connect(musicGain); o.start(t0); o.stop(t0 + 1);
      const o2 = AC.createOscillator(), g2 = AC.createGain(); o2.type = 'sine'; o2.frequency.value = f * 2; g2.gain.setValueAtTime(.02, t0); g2.gain.exponentialRampToValueAtTime(.0001, t0 + .4);
      o2.connect(g2).connect(musicGain); o2.start(t0); o2.stop(t0 + .5);
      musicStep++; musicNext = t0 + .34;
    }
  }
  let speaking = null, capUntil = 0;
  function say(id) {
    const ln = L[id]; if (!ln) return;
    speaking = { id, t0: performance.now(), dur: ln.dur * 1000 }; capUntil = performance.now() + ln.dur * 1000 + 1400;
    $('fcap').innerHTML = (ln.who === 'Crank Boy' ? '<b>Crank Boy</b>' : ln.who === 'Title' ? '<b>Title card</b>' : '') + esc(ln.cap);
    $('fcap').hidden = false;
    if (sound && VO[id]) { try { VO[id].currentTime = 0; VO[id].play().catch(() => {}); } catch (e) {} }
  }
  function silenceAll() { Object.values(VO).forEach(a => { try { a.pause(); } catch (e) {} }); speaking = null; }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function voiceLevel() {
    if (!speaking) return 0;
    const el2 = performance.now() - speaking.t0; if (el2 > speaking.dur + 150) { speaking = null; return 0; }
    if (analyser && sound) { analyser.getByteTimeDomainData(abuf); let s = 0; for (let i = 0; i < abuf.length; i++) { const v = (abuf[i] - 128) / 128; s += v * v; } return Math.min(1, Math.sqrt(s / abuf.length) * 6); }
    return .5 + .5 * Math.sin(el2 / 55) * Math.sin(el2 / 130);
  }

  /* ---------- layout ---------- */
  let W = 1, H = 1, DPR = 1, LY = null;
  function layout() {
    const r = el.getBoundingClientRect(); W = r.width; H = r.height; DPR = Math.min(2, devicePixelRatio || 1);
    cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR);
    if (W / H >= 1.15) {
      const s = H / 900, sw = Math.min(W - W * .045 - 400 * s, W * .62, H * .74 * 1.6), sh = sw / 1.6;
      const screen = { x: W - sw - W * .045, y: H * .07, w: sw, h: sh };
      const floor = H * .9, projX = screen.x - 165 * s;
      LY = { portrait: false, s, screen, floor, projX, cbX: projX - 160 * s };
      $('fcap').style.top = ''; $('fcap').style.bottom = '64px';
    } else {
      const sw = W * .92, sh = sw / 1.6, screen = { x: W * .04, y: Math.max(54, H * .07), w: sw, h: sh };
      const capTop = screen.y + sh + 10, floor = H - 70;
      const s = Math.max(.45, Math.min(W / 520, (floor - capTop - 80) / 400));
      const projX = W * .66;
      LY = { portrait: true, s, screen, floor, projX, cbX: projX - 160 * s };
      $('fcap').style.top = capTop + 'px'; $('fcap').style.bottom = 'auto';
    }
    LY.lens = { x: LY.projX + 150 * LY.s, y: LY.floor - 205 * LY.s };
  }

  /* ---------- state ---------- */
  const S = { t: 0, scene: 0, playing: false, angle: 0, speed: 0, target: 0, light: 0, user: false,
    cb: { x: -400, face: 1, pose: 'idle', point: 0, rub: 0, offer: 0, walk: 0, brow: 0, blink: 0, nextBlink: 2 }, frozen: null, dust: [] };
  for (let i = 0; i < 70; i++) S.dust.push({ u: rnd(), v: rnd(), w: rnd(), sp: .02 + rnd(.05) });

  /* ---------- drawing helpers ---------- */
  function blob(build, fill, lw = 2, off = 1.8) {
    if (fill) { ctx.save(); ctx.translate(off, off * .7); ctx.beginPath(); build(); ctx.fillStyle = fill; ctx.fill(); ctx.restore(); }
    if (lw) { ctx.beginPath(); build(); ctx.lineWidth = lw; ctx.strokeStyle = INK; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke(); }
  }
  function hatch(build, gap, a, lw = .8) {
    ctx.save(); ctx.beginPath(); build(); ctx.clip(); ctx.strokeStyle = `rgba(43,35,32,${a})`; ctx.lineWidth = lw; ctx.beginPath();
    for (let i = -2000; i < 2000; i += gap) { ctx.moveTo(i, -2000); ctx.lineTo(i + 2000, 2000); } ctx.stroke(); ctx.restore();
  }
  const grain = document.createElement('canvas'); grain.width = grain.height = 160;
  { const g = grain.getContext('2d'), d = g.createImageData(160, 160); for (let i = 0; i < d.data.length; i += 4) { const v = rnd(255); d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } g.putImageData(d, 0, 0); }
  let grainPat = null;

  /* the wall: dark stone with negative hand stencils (pAELo's cave) */
  const HANDS = [[.08, .2, .9, -.3], [.18, .58, .7, .2], [.92, .82, .8, .4], [.52, .9, .6, -.1], [.3, .12, .55, .6]];
  function wall() {
    const g = ctx.createRadialGradient(W * .5, H * .4, 0, W * .5, H * .5, Math.max(W, H) * .8);
    g.addColorStop(0, '#3a2e25'); g.addColorStop(1, '#17110d'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.globalAlpha = .5;
    HANDS.forEach(([x, y, k, r]) => hand(x * W, y * H, Math.min(W, H) * .07 * k, r));
    ctx.restore();
  }
  function hand(x, y, s, rot) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
    const g = ctx.createRadialGradient(0, 0, s * .2, 0, 0, s * 2); g.addColorStop(0, 'rgba(160,60,35,.75)'); g.addColorStop(1, 'rgba(160,60,35,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, s * 2, 0, TAU); ctx.fill();
    ctx.fillStyle = '#2a211b'; ctx.beginPath(); ctx.ellipse(0, s * .25, s * .55, s * .62, 0, 0, TAU); ctx.fill();
    [[-.48, -.35, -.5], [-.2, -.75, -.15], [.08, -.85, 0], [.34, -.72, .15], [.62, -.15, .9]].forEach(([fx, fy, a]) => {
      ctx.save(); ctx.translate(fx * s, fy * s); ctx.rotate(a); ctx.beginPath(); ctx.ellipse(0, 0, s * .13, s * .42, 0, 0, TAU); ctx.fill(); ctx.restore();
    });
    ctx.restore();
  }
  /* Tecti, pAELo's mascot: a tectiform (roof-shaped Ice Age sign) with two eyes and counting dots */
  function tecti(x, y, s, t) {
    ctx.save(); ctx.translate(x, y); ctx.strokeStyle = '#C0573A'; ctx.fillStyle = '#C0573A'; ctx.lineWidth = s * .09; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.shadowColor = 'rgba(230,110,70,.6)'; ctx.shadowBlur = s * .4;
    ctx.beginPath(); ctx.moveTo(-s, 0); ctx.lineTo(0, -s * .9); ctx.lineTo(s, 0); ctx.moveTo(-s * .78, -s * .02); ctx.lineTo(-s * .78, s * .95); ctx.moveTo(s * .78, -s * .02); ctx.lineTo(s * .78, s * .95); ctx.moveTo(0, -s * .9); ctx.lineTo(0, -s * .55); ctx.stroke();
    const blink = (t % 4) < .14;
    [-.3, .3].forEach(ex => { ctx.beginPath(); if (blink) { ctx.moveTo(ex * s - s * .1, s * .28); ctx.lineTo(ex * s + s * .1, s * .28); ctx.stroke(); } else { ctx.arc(ex * s, s * .28, s * .1, 0, TAU); ctx.fill(); } });
    for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(-s * .45 + i * s * .3, s * 1.25, s * .06, 0, TAU); ctx.fill(); }
    ctx.restore();
  }

  /* the projector, origin at the base of its stand, in stage units */
  function projector() {
    const s = LY.s; ctx.save(); ctx.translate(LY.projX, LY.floor); ctx.scale(s, s);
    ctx.strokeStyle = INK; ctx.lineWidth = 7; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(0, -140); ctx.lineTo(-70, 0); ctx.moveTo(0, -140); ctx.lineTo(70, 0); ctx.moveTo(0, -140); ctx.lineTo(0, 0); ctx.stroke();
    ctx.strokeStyle = '#8C6A44'; ctx.lineWidth = 4; ctx.stroke();
    [-45, 45].forEach((rx, i) => {
      ctx.save(); ctx.translate(rx, -300); ctx.rotate(S.angle * (i ? 1.1 : .9));
      blob(() => ctx.arc(0, 0, 56, 0, TAU), '#4F6A88', 3); blob(() => ctx.arc(0, 0, 40, 0, TAU), '#3B5270', 2);
      ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.beginPath(); for (let k = 0; k < 3; k++) { const a = k / 3 * TAU; ctx.moveTo(Math.cos(a) * 10, Math.sin(a) * 10); ctx.lineTo(Math.cos(a) * 52, Math.sin(a) * 52); } ctx.stroke();
      blob(() => ctx.arc(0, 0, 9, 0, TAU), '#C9A23E', 2); ctx.restore();
    });
    ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-45, -300); ctx.lineTo(-20, -260); ctx.moveTo(45, -300); ctx.lineTo(20, -260); ctx.stroke();
    blob(() => ctx.rect(-90, -262, 180, 122), '#4F6A88', 3); hatch(() => ctx.rect(20, -262, 70, 122), 7, .3);
    blob(() => ctx.rect(-80, -250, 46, 28), '#C9A23E', 2);
    blob(() => ctx.rect(90, -224, 52, 38), '#3B5270', 3); blob(() => ctx.ellipse(146, -205, 10, 22, 0, 0, TAU), '#DCE7E2', 3);
    // crank on the left face
    blob(() => ctx.arc(-90, -205, 12, 0, TAU), '#3B5270', 3);
    const h = crankHandle(true); ctx.strokeStyle = INK; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(-90, -205); ctx.lineTo(h.x, h.y); ctx.stroke(); ctx.strokeStyle = '#6F86A2'; ctx.lineWidth = 4; ctx.stroke();
    blob(() => ctx.arc(h.x, h.y, 9, 0, TAU), '#8C6A44', 2.5);
    ctx.restore();
  }
  function crankHandle(local) { const x = -90 + 30 * Math.cos(S.angle - Math.PI / 2), y = -205 + 30 * Math.sin(S.angle - Math.PI / 2); return local ? { x, y } : { x: LY.projX + x * LY.s, y: LY.floor + y * LY.s }; }

  /* ---------- Crank Boy ---------- */
  function ik(sx, sy, hx, hy, l1, l2, bend) {
    let dx = hx - sx, dy = hy - sy, d = Math.min(Math.hypot(dx, dy), l1 + l2 - .5); d = Math.max(d, .5);
    const a = Math.atan2(dy, dx), c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), an = a + bend * Math.acos(Math.max(-1, Math.min(1, c)));
    return [sx + l1 * Math.cos(an), sy + l1 * Math.sin(an)];
  }
  function limb(x1, y1, x2, y2, bend, l1, l2, w, col) {
    const [ex, ey] = ik(x1, y1, x2, y2, l1, l2, bend);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.strokeStyle = INK; ctx.lineWidth = w + 6; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(ex, ey); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.strokeStyle = col; ctx.lineWidth = w; ctx.stroke();
  }
  function crankBoy(dt) {
    const c = S.cb, s = LY.s, vl = voiceLevel(), talking = speaking && L[speaking.id] && L[speaking.id].who === 'Crank Boy';
    c.blink -= dt; if (c.blink < -.12) { c.blink = 2.5 + rnd(3); }
    ctx.save(); ctx.translate(c.x, LY.floor); ctx.scale(s, s);
    const walking = c.pose === 'walk', crank = c.pose === 'crank';
    const ph = S.t * 9, step = walking ? Math.sin(ph) : 0, bob = walking ? Math.abs(Math.cos(ph)) * 6 : crank ? Math.sin(S.angle) * 3 * Math.min(1, S.speed) : Math.sin(S.t * 2) * 1.5;
    const lean = crank ? .1 : walking ? .05 : 0;
    const hip = { x: 0, y: -150 - bob }, sh = { x: 18 * lean * 10, y: -290 - bob };
    // legs
    limb(hip.x - 12, hip.y, -26 + step * 28, -4, 1, 78, 76, 22, '#8EA3BC');
    limb(hip.x + 12, hip.y, 22 - step * 28, -4, 1, 78, 76, 22, '#8EA3BC');
    [[-26 + step * 28], [22 - step * 28]].forEach(([fx]) => blob(() => ctx.ellipse(fx + 10, 2, 22, 9, 0, 0, TAU), '#5C3F28', 2.5));
    // back arm (left)
    let lh;
    if (c.pose === 'rub' || c.rub > 0) lh = { x: sh.x + 34 + Math.sin(S.t * 20) * 6 * c.rub, y: sh.y + 70 };
    else if (crank) lh = { x: sh.x + 40, y: sh.y + 105 };
    else if (c.pose === 'shrug') lh = { x: sh.x - 70, y: sh.y - 10 };
    else lh = { x: sh.x - 22 + (walking ? -step * 22 : 0), y: sh.y + 128 };
    limb(sh.x - 6, sh.y + 10, lh.x, lh.y, -1, 75, 72, 18, '#B9652F');
    blob(() => ctx.arc(lh.x, lh.y, 12, 0, TAU), '#EDC8A2', 2.5);
    // torso
    const torso = () => { ctx.moveTo(sh.x - 40, sh.y + 6); ctx.quadraticCurveTo(sh.x, sh.y - 14, sh.x + 40, sh.y + 6); ctx.lineTo(hip.x + 42, hip.y + 12); ctx.lineTo(hip.x - 42, hip.y + 12); ctx.closePath(); };
    blob(torso, '#C9733A', 3.2); hatch(torso, 7, .22);
    blob(() => { ctx.moveTo(sh.x - 12, sh.y + 2); ctx.lineTo(sh.x + 12, sh.y + 2); ctx.lineTo(sh.x, sh.y + 24); ctx.closePath(); }, '#F3ECD8', 2);
    [0, 1, 2].forEach(i => blob(() => ctx.arc(sh.x + 3 - i * 2, sh.y + 44 + i * 30, 3.5, 0, TAU), '#C9A23E', 1.5));
    // front arm (right)
    let rh;
    if (crank) { const hpt = crankHandle(false); rh = { x: (hpt.x - c.x) / s, y: (hpt.y - LY.floor) / s }; }
    else if (c.pose === 'point') rh = { x: sh.x + 120 * c.face, y: sh.y - 95 };
    else if (c.pose === 'offer') rh = { x: sh.x + 70, y: sh.y + 40 };
    else if (c.pose === 'rub' || c.rub > 0) rh = { x: sh.x + 40 - Math.sin(S.t * 20) * 6 * c.rub, y: sh.y + 72 };
    else if (c.pose === 'shrug') rh = { x: sh.x + 70, y: sh.y - 10 };
    else rh = { x: sh.x + 24 + (walking ? step * 22 : 0), y: sh.y + 128 };
    limb(sh.x + 14, sh.y + 12, rh.x, rh.y, crank ? -1 : 1, 75, 72, 18, '#C9733A');
    blob(() => ctx.arc(rh.x, rh.y, c.pose === 'offer' ? 17 : 12, 0, TAU), '#EDC8A2', 2.5);
    if (c.pose === 'point') { ctx.strokeStyle = INK; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(rh.x, rh.y); ctx.lineTo(rh.x + 16, rh.y - 12); ctx.stroke(); ctx.strokeStyle = '#EDC8A2'; ctx.lineWidth = 3.5; ctx.stroke(); }
    // head: big, 3/4 view toward c.face (1 right, 0 front, -1 left)
    const hx = sh.x + 6 + c.face * 4, hy = sh.y - 52 + (crank ? 6 : 0), f = c.face;
    blob(() => ctx.ellipse(hx, hy, 50, 54, 0, 0, TAU), '#EDC8A2', 3.2);
    blob(() => { ctx.moveTo(hx - 52, hy - 4); ctx.bezierCurveTo(hx - 56, hy - 70, hx + 50, hy - 78, hx + 52, hy - 10); ctx.bezierCurveTo(hx + 30 - f * 20, hy - 34, hx - 20 - f * 20, hy - 40, hx - 52, hy - 4); ctx.closePath(); }, '#6B4A2E', 2.8);
    hatch(() => ctx.ellipse(hx - 30 * f, hy, 50, 54, 0, 0, TAU), 9, .12);
    (f ? [-f * 44] : [-48, 48]).forEach(o => blob(() => ctx.ellipse(hx + o, hy + 6, 9, 13, 0, 0, TAU), '#E2B48E', 2.2));
    const ex = hx + f * 14, eyeY = hy + 2;
    const look = c.pose === 'point' ? -3 : 0;
    ctx.fillStyle = INK; ctx.strokeStyle = INK; ctx.lineWidth = 3;
    [-17, 17].forEach(o => {
      const x = ex + o * (f ? .8 : 1);
      if (c.blink < 0) { ctx.beginPath(); ctx.moveTo(x - 6, eyeY); ctx.lineTo(x + 6, eyeY); ctx.stroke(); }
      else { ctx.beginPath(); ctx.ellipse(x + f * 2, eyeY + look, 4.5, 6, 0, 0, TAU); ctx.fill(); }
      ctx.beginPath(); ctx.moveTo(x - 9, eyeY - 14 - c.brow * 7 + (o < 0 ? 2 : 0)); ctx.lineTo(x + 9, eyeY - 14 - c.brow * 7 + (o < 0 ? 0 : 2)); ctx.stroke();
    });
    // nose and mouth
    ctx.beginPath(); ctx.moveTo(ex + f * 16, eyeY + 6); ctx.quadraticCurveTo(ex + f * 26 + (f ? 0 : 4), eyeY + 18, ex + f * 14, eyeY + 20); ctx.stroke();
    const m = talking ? vl : 0, mx = ex + f * 8, my = hy + 34;
    if (m > .08) { blob(() => ctx.ellipse(mx, my, 12, 3 + m * 12, 0, 0, TAU), '#7A2E24', 2.5); }
    else { ctx.beginPath(); ctx.arc(mx, my - 6, 13, .25 * Math.PI, .75 * Math.PI); ctx.stroke(); }
    ctx.restore();
  }

  /* ---------- the screen ---------- */
  const SW = 1000, SH = 625;
  function toScreen() { const k = LY.screen.w / SW; ctx.translate(LY.screen.x, LY.screen.y); ctx.scale(k, k); }
  function beam() {
    if (S.light <= .01) return;
    const l = LY.lens, sc = LY.screen;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const g = ctx.createLinearGradient(l.x, l.y, sc.x + sc.w / 2, sc.y + sc.h / 2);
    g.addColorStop(0, `rgba(255,236,190,${.22 * S.light})`); g.addColorStop(1, `rgba(255,236,190,${.05 * S.light})`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(l.x, l.y);
    const pts = [[sc.x, sc.y], [sc.x + sc.w, sc.y], [sc.x + sc.w, sc.y + sc.h], [sc.x, sc.y + sc.h]].sort((a, b) => Math.atan2(a[1] - l.y, a[0] - l.x) - Math.atan2(b[1] - l.y, b[0] - l.x));
    ctx.lineTo(pts[0][0], pts[0][1]); ctx.lineTo(pts[3][0], pts[3][1]); ctx.closePath(); ctx.fill();
    ctx.fillStyle = `rgba(255,240,210,${.5 * S.light})`;
    S.dust.forEach(d => { const tx = sc.x + d.u * sc.w, ty = sc.y + d.v * sc.h, k = d.w; ctx.beginPath(); ctx.arc(lerp(l.x, tx, k), lerp(l.y, ty, k), 1.2, 0, TAU); ctx.fill(); });
    ctx.restore();
  }
  function card(im, x, y, w, rot, label) {
    const h = im && im.naturalWidth ? w * im.naturalHeight / im.naturalWidth : w * .6;
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot || 0);
    ctx.fillStyle = 'rgba(20,12,4,.35)'; ctx.fillRect(-w / 2 + 6, -h / 2 + 8, w, h);
    ctx.fillStyle = '#FBF7EA'; ctx.fillRect(-w / 2 - 8, -h / 2 - 8, w + 16, h + 16);
    if (im && im.complete && im.naturalWidth) ctx.drawImage(im, -w / 2, -h / 2, w, h); else { ctx.fillStyle = '#E8D59A'; ctx.fillRect(-w / 2, -h / 2, w, h); }
    ctx.strokeStyle = INK; ctx.lineWidth = 1.5; ctx.strokeRect(-w / 2, -h / 2, w, h);
    if (label) { ctx.fillStyle = '#F3ECD8'; ctx.font = 'italic 24px "IM Fell English", Georgia, serif'; ctx.textAlign = 'center'; ctx.fillText(label, 0, h / 2 + 40); }
    ctx.restore(); return h;
  }
  function slip(g, flip, hl) {
    const w = 250, h = 156, x = 300 + g.ci * 265, y = 250 + g.ri * 190;
    const sx = Math.abs(Math.cos(Math.PI * flip)), photo = flip >= .5;
    ctx.save(); ctx.translate(x, y); ctx.scale(Math.max(.03, sx), 1);
    ctx.fillStyle = 'rgba(20,12,4,.35)'; ctx.fillRect(-w / 2 + 6, -h / 2 + 8, w, h);
    ctx.fillStyle = '#FBF7EA'; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.strokeStyle = INK; ctx.lineWidth = 2; ctx.strokeRect(-w / 2, -h / 2, w, h);
    if (photo && g.im && g.im.complete && g.im.naturalWidth) { ctx.drawImage(g.im, -w / 2 + 7, -h / 2 + 7, w - 14, h - 14); }
    else { ctx.strokeStyle = 'rgba(43,35,32,.25)'; ctx.lineWidth = 1.5; ctx.beginPath(); for (let i = 0; i < 5; i++) { ctx.moveTo(-w / 2 + 20, -h / 2 + 30 + i * 24); ctx.lineTo(w / 2 - 20 - (i === 4 ? 90 : 0), -h / 2 + 30 + i * 24); } ctx.stroke(); }
    ctx.restore();
    if (hl > 0) { ctx.save(); ctx.globalAlpha = hl; ctx.strokeStyle = '#C9733A'; ctx.lineWidth = 7; ctx.strokeRect(x - w / 2 - 8, y - h / 2 - 8, w + 16, h + 16); ctx.restore(); }
  }
  function automaton(kind, x, y, k) { // two original 1910-style automata standing for the two programs
    ctx.save(); ctx.translate(x, y); ctx.scale(k, k);
    if (kind === 'argon') { // a brass column with a glass dome and a glowing coil
      blob(() => ctx.rect(-12, -10, 24, 70), '#C9A23E', 2.2); blob(() => ctx.rect(-26, 58, 52, 12), '#8C6A44', 2);
      blob(() => ctx.arc(0, -34, 26, 0, TAU), 'rgba(220,235,240,.9)', 2.2);
      ctx.strokeStyle = '#C9733A'; ctx.lineWidth = 2.5; ctx.beginPath(); for (let i = 0; i < 7; i++) ctx.lineTo(-12 + i * 4, -34 + (i % 2 ? -8 : 8)); ctx.stroke();
      ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-12, 8); ctx.lineTo(-36, -6); ctx.moveTo(12, 8); ctx.lineTo(36, 20); ctx.stroke();
    } else { // a typewriter body with round eyes and a paper tape
      blob(() => ctx.rect(-34, 0, 68, 46), '#3B5270', 2.2); ctx.fillStyle = '#F3ECD8'; for (let r = 0; r < 2; r++) for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.arc(-25 + i * 10, 14 + r * 14, 3, 0, TAU); ctx.fill(); }
      blob(() => ctx.arc(0, -24, 24, 0, TAU), '#C9A23E', 2.2);
      [-9, 9].forEach(o => { blob(() => ctx.arc(o, -26, 7, 0, TAU), '#F3ECD8', 1.8); ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(o, -26, 2.5, 0, TAU); ctx.fill(); });
      blob(() => { ctx.moveTo(-6, -48); ctx.lineTo(6, -48); ctx.lineTo(10, -78); ctx.lineTo(-2, -78); ctx.closePath(); }, '#FBF7EA', 1.6);
    }
    ctx.restore();
  }
  function sheet(ci, drop) {
    const p = P[COLS[ci]], th = p.theory || {}, x = 300 + ci * 265, y = lerp(-200, 92, ease(drop)), w = 250, h = 96;
    ctx.save(); ctx.translate(x, y);
    ctx.fillStyle = 'rgba(20,12,4,.35)'; ctx.fillRect(-w / 2 + 6, -h / 2 + 8, w, h);
    ctx.fillStyle = '#FBF7EA'; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.strokeStyle = INK; ctx.lineWidth = 2; ctx.strokeRect(-w / 2, -h / 2, w, h);
    ctx.fillStyle = ['#B44A3C', '#5E7F4E', '#4F6A88'][ci]; ctx.fillRect(-w / 2, -h / 2, w, 8);
    ctx.fillStyle = INK; ctx.textAlign = 'left'; ctx.font = '30px "IM Fell English SC", Georgia, serif'; ctx.fillText(p.letter + '  ' + p.title, -w / 2 + 14, -6, w - 24);
    ctx.font = 'italic 19px "IM Fell English", Georgia, serif'; ctx.fillStyle = '#4b3f35';
    ctx.fillText(th.work || '', -w / 2 + 14, 20, w - 24); ctx.fillText((th.by || '') + (th.year && th.by !== 'Soyoun Jang' ? ', ' + th.year : ''), -w / 2 + 14, 40, w - 24);
    ctx.restore();
  }
  function rowLabel(ri, slide) {
    const m = M[ROWS[ri]], y = 250 + ri * 190, x = lerp(-200, 72, ease(slide));
    automaton(ROWS[ri], x - 40, y - 4, .9);
    ctx.fillStyle = '#F3ECD8'; ctx.textAlign = 'left'; ctx.font = '30px "IM Fell English SC", Georgia, serif'; ctx.fillText(m.short, x - 8, y - 4);
    ctx.font = 'italic 16px "IM Fell English", Georgia, serif'; ctx.fillText('by ' + m.maker, x - 8, y + 20);
  }
  function filmFx(on) { // scratches, specks, gate weave
    if (reduce || !on) return;
    ctx.save(); ctx.globalAlpha = .35; ctx.strokeStyle = 'rgba(255,250,235,.7)'; ctx.lineWidth = 1.5;
    if (rnd() < .5) { const x = rnd(SW); ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + rnd(6) - 3, SH); ctx.stroke(); }
    ctx.fillStyle = 'rgba(20,12,4,.6)'; for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(rnd(SW), rnd(SH), rnd(2.5), 0, TAU); ctx.fill(); }
    ctx.restore();
  }

  /* ---------- the scenes ---------- */
  const NAMES = (R.lab && R.lab.names) || ['Phantom Augmented Environments Lab for Emergent Otherworlds'];
  let nameIx = 0, nameT = 0;
  function wordmark(x, y, size, alpha, t) {
    const jit = reduce ? 0 : (rnd() < .08 ? rnd(10) - 5 : 0);
    ctx.save(); ctx.textAlign = 'center'; ctx.globalAlpha = alpha;
    ctx.font = `${size}px "IM Fell English SC", Georgia, serif`;
    [['rgba(255,80,60,.55)', -3], ['rgba(80,220,255,.45)', 3], ['#F6E7C8', 0]].forEach(([c, o]) => {
      ctx.fillStyle = c; ctx.fillText('p', x - size * 1.15 + o + jit, y); ctx.fillText('o', x + size * 1.15 + o + jit, y);
      ctx.font = `${size * 1.15}px "IM Fell English SC", Georgia, serif`; ctx.fillText('AEL', x + o + jit, y); ctx.font = `${size}px "IM Fell English SC", Georgia, serif`;
    });
    ctx.restore();
  }
  function flickerName(x, y, size, t, alpha) {
    nameT += 1 / 60; if (nameT > .38) { nameT = 0; nameIx = (nameIx + 1 + Math.floor(rnd(3))) % NAMES.length; }
    const n = NAMES[nameIx]; ctx.save(); ctx.textAlign = 'center'; ctx.font = `italic ${size}px "IM Fell English", Georgia, serif`;
    ctx.globalAlpha = alpha * (reduce ? 1 : .55 + rnd(.45));
    ctx.fillStyle = 'rgba(120,230,255,.5)'; ctx.fillText(n, x + 2, y); ctx.fillStyle = '#F6E7C8'; ctx.fillText(n, x, y);
    ctx.restore();
  }
  const SC = [
    { // 0: the wall of pAELo
      dur: 7.6, cues: [[1, 'n0']], cb: () => ({ x: -400, pose: 'idle' }),
      screen: null,
      over(t) {
        const sc = LY.screen, cx = sc.x + sc.w / 2, cy = sc.y + sc.h * .45, a = cl(t, .3, 1.2) * (1 - cl(t, 6.8, 7.6));
        tecti(sc.x + sc.w * .5, sc.y + sc.h * .12 + sc.h * .02, sc.h * .07, t);
        wordmark(cx, cy + sc.h * .06, sc.h * .2, a, t);
        flickerName(cx, cy + sc.h * .24, Math.max(13, sc.h * .045), t, a);
      }
    },
    { // 1: enter Crank Boy; leader countdown
      dur: 7, cues: [[2.7, 'cb1']],
      cb: t => t < 1.7 ? { x: lerp(-260 * LY.s, LY.cbX, ease(cl(t, 0, 1.7))), pose: 'walk', face: 1 } : t < 2.6 ? { x: LY.cbX, pose: 'rub', face: 0, brow: 1 } : t < 4.2 ? { x: LY.cbX, pose: 'idle', face: 0 } : { x: LY.cbX, pose: 'crank', face: 1, crank: 1.2 },
      screen(t) {
        const n = 3 - Math.floor(cl(t, 4.4, 6.9) * 3);
        ctx.fillStyle = '#d8c79a'; ctx.fillRect(0, 0, SW, SH);
        if (t < 4.4) return;
        const u = ((t - 4.4) / (2.5 / 3)) % 1;
        ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(SW / 2, SH / 2, 230, 0, TAU); ctx.arc(SW / 2, SH / 2, 190, 0, TAU); ctx.moveTo(0, SH / 2); ctx.lineTo(SW, SH / 2); ctx.moveTo(SW / 2, 0); ctx.lineTo(SW / 2, SH); ctx.stroke();
        ctx.fillStyle = 'rgba(43,35,32,.25)'; ctx.beginPath(); ctx.moveTo(SW / 2, SH / 2); ctx.arc(SW / 2, SH / 2, 230, -Math.PI / 2, -Math.PI / 2 + u * TAU); ctx.fill();
        ctx.fillStyle = INK; ctx.font = '260px "IM Fell English SC", Georgia, serif'; ctx.textAlign = 'center'; ctx.fillText(String(Math.max(1, n)), SW / 2, SH / 2 + 90);
      }
    },
    { // 2: title, a letter per half-turn of the crank
      dur: 7.4, cues: [[4.6, 'fr1']], music: true, cb: () => ({ x: LY.cbX, pose: 'crank', face: 1, crank: 1.25 }),
      screen(t) {
        ctx.fillStyle = '#F3ECD8'; ctx.fillRect(0, 0, SW, SH);
        ctx.strokeStyle = '#B44A3C'; ctx.lineWidth = 3; ctx.strokeRect(30, 30, SW - 60, SH - 60); ctx.lineWidth = 1.2; ctx.strokeRect(42, 42, SW - 84, SH - 84);
        [[42, 42], [SW - 42, 42], [42, SH - 42], [SW - 42, SH - 42]].forEach(([x, y]) => { ctx.beginPath(); ctx.arc(x, y, 18, 0, TAU); ctx.stroke(); });
        ctx.textAlign = 'center'; ctx.fillStyle = '#6E5F4F'; ctx.font = 'italic 30px "IM Fell English", Georgia, serif'; ctx.globalAlpha = cl(t, .2, .9); ctx.fillText('a pAELo picture', SW / 2, 150); ctx.globalAlpha = 1;
        const words = 'THE CRANK BOY'.split(''), shown = Math.floor(cl(t, .6, 3.6) * words.length + .001);
        ctx.font = '112px "IM Fell English SC", Georgia, serif';
        const total = ctx.measureText('THE CRANK BOY').width; let x = SW / 2 - total / 2;
        words.forEach((ch, i) => {
          const w = ctx.measureText(ch).width;
          if (i < shown) { const age = (t - .6 - i * 3 / words.length); const drop = reduce ? 0 : Math.max(0, 1 - age * 6) * -60;
            ctx.textAlign = 'left'; ctx.fillStyle = 'rgba(80,140,200,.45)'; ctx.fillText(ch, x + 4, 330 + drop + 3); ctx.fillStyle = '#B44A3C'; ctx.fillText(ch, x, 330 + drop); }
          x += w;
        });
        if (t > 4.4) { ctx.textAlign = 'center'; ctx.fillStyle = INK; ctx.font = '44px "IM Fell English SC", Georgia, serif'; ctx.globalAlpha = cl(t, 4.4, 4.9); ctx.fillText("EN L'AN 2000", SW / 2, 440); ctx.globalAlpha = 1; }
      },
      tick(t, prev) { const n = 13, a = Math.floor(cl(prev, .6, 3.6) * n), b = Math.floor(cl(t, .6, 3.6) * n); if (b > a && 'THE CRANK BOY'[b - 1] !== ' ') thump(); if (prev < 4.4 && t >= 4.4) thump(); }
    },
    { // 3: the series of cards
      dur: 11.6, cues: [[.6, 'n2']], music: true, cb: () => ({ x: LY.cbX, pose: 'crank', face: 1, crank: 1.1 }),
      screen(t) {
        ctx.fillStyle = '#2b2119'; ctx.fillRect(0, 0, SW, SH);
        const at = [1.5, 3.4, 5.3, 7.4, 8.6, 9.8], gap = 640;
        let pos = 0; for (let i = 0; i < at.length; i++) { if (t >= at[i]) pos = i; }
        const i0 = Math.min(at.length - 1, pos), i1 = Math.min(at.length - 1, pos + 1);
        const k = i1 === i0 ? 0 : ease(cl(t, at[i0] + .35, at[i1] - .25));
        const camX = t < at[0] ? lerp(-gap * .6, 0, ease(cl(t, 0, at[0]))) : (i0 + k) * gap;
        PAN.forEach((id, i) => { const s = R.series.find(x => x.id === id); card(SERIES[id], SW / 2 + i * gap - camX, SH / 2 - 20, 560, (i % 2 ? .02 : -.02), s ? s.title.replace(/ \(.*\)/, '') : ''); });
      },
      tick(t, prev) { [1.5, 3.4, 5.3, 7.4, 8.6, 9.8].forEach(a => { if (prev < a - .1 && t >= a - .1) whoosh(); }); }
    },
    { // 4: the school card, push in to the boy
      dur: 12.2, cues: [[.4, 'fr2'], [1.6, 'n3'], [8.1, 'cb2']],
      cb: t => t < 8 ? { x: LY.cbX, pose: 'crank', face: 1, crank: 1.05 } : t < 11.6 ? { x: LY.cbX, pose: 'point', face: 1, crank: .8, brow: .6 } : { x: LY.cbX, pose: 'crank', face: 1, crank: 1 },
      screen(t) {
        ctx.fillStyle = '#2b2119'; ctx.fillRect(0, 0, SW, SH);
        const im = SERIES.school, iw = 820, ih = iw * 499 / 800;
        const slide = ease(cl(t, 0, .8)), push = ease(cl(t, 7.4, 8.8)), slow = cl(t, .8, 7.4) * .06;
        const z = lerp(1 + slow, 1.85, push), fx = lerp(.5, .64, push), fy = lerp(.5, .6, push);
        ctx.save(); ctx.translate(SW / 2 + (1 - slide) * 900, SH / 2); ctx.scale(z, z); ctx.translate(-(fx - .5) * iw, -(fy - .5) * ih);
        card(im, 0, 0, iw, 0);
        if (t > 8.4) { const p = ease(cl(t, 8.4, 9.4)); ctx.strokeStyle = '#B44A3C'; ctx.lineWidth = 5 / z; ctx.beginPath(); ctx.ellipse((.648 - .5) * iw, (.64 - .5) * ih, 66, 150, -.05, -Math.PI / 2, -Math.PI / 2 + TAU * p * 1.04); ctx.stroke(); }
        ctx.restore();
      },
      tick(t, prev) { if (prev < .05 && t >= .05) whoosh(); }
    },
    { // 5: if he stops, everything stops
      dur: 5.8, cues: [[.2, 'cb3a'], [2.7, 'cb3b']],
      cb: t => t < 1.45 ? { x: LY.cbX, pose: 'crank', face: 0, crank: .9, brow: 1 } : t < 3.9 ? { x: LY.cbX, pose: 'shrug', face: 0, crank: 0, brow: .3 } : { x: LY.cbX, pose: 'crank', face: 1, crank: 1.15 },
      freezeFrom: 1.45,
      screen(t) {
        ctx.fillStyle = '#2b2119'; ctx.fillRect(0, 0, SW, SH);
        const iw = 820, ih = iw * 499 / 800, z = 1.85;
        ctx.save(); ctx.translate(SW / 2, SH / 2); ctx.scale(z, z); ctx.translate(-(.64 - .5) * iw, -(.6 - .5) * ih); card(SERIES.school, 0, 0, iw, 0);
        ctx.strokeStyle = '#B44A3C'; ctx.lineWidth = 5 / z; ctx.beginPath(); ctx.ellipse((.648 - .5) * iw, (.64 - .5) * ih, 66, 150, -.05, 0, TAU); ctx.stroke(); ctx.restore();
      }
    },
    { // 6: six programs, two makers
      dur: 10, cues: [[.5, 'n4']], cb: () => ({ x: LY.cbX, pose: 'crank', face: 1, crank: 1.05 }),
      screen(t) {
        ctx.fillStyle = '#3a2c20'; ctx.fillRect(0, 0, SW, SH);
        GRID.forEach((g, i) => { const k = ease(cl(t, 1 + i * .25, 1.7 + i * .25)); if (k <= 0) return; ctx.save(); ctx.translate(0, (1 - k) * 600); slip(g, 0, 0); ctx.restore(); });
        rowLabel(0, cl(t, 4.4, 5.2)); rowLabel(1, cl(t, 6.9, 7.7));
      },
      tick(t, prev) { for (let i = 0; i < 6; i++) { const a = 1 + i * .25; if (prev < a && t >= a) click(); } }
    },
    { // 7: three instructions, three theories
      dur: 14.8, cues: [[.3, 'n5']], cb: () => ({ x: LY.cbX, pose: 'crank', face: 1, crank: 1 }),
      screen(t) {
        ctx.fillStyle = '#3a2c20'; ctx.fillRect(0, 0, SW, SH);
        GRID.forEach(g => slip(g, 0, 0)); rowLabel(0, 1); rowLabel(1, 1);
        [6.1, 9.2, 12].forEach((a, i) => sheet(i, cl(t, a, a + .55)));
      },
      tick(t, prev) { [6.1, 9.2, 12].forEach(a => { if (prev < a + .5 && t >= a + .5) thump(); }); }
    },
    { // 8: six different games
      dur: 9.6, cues: [[.2, 'n6'], [4.1, 'cb4']],
      cb: t => t < 4 ? { x: LY.cbX, pose: 'crank', face: 1, crank: 1 } : { x: LY.cbX, pose: 'crank', face: 0, crank: .9, brow: t < 6.3 ? .8 : .1 },
      screen(t) {
        ctx.fillStyle = '#3a2c20'; ctx.fillRect(0, 0, SW, SH);
        rowLabel(0, 1); rowLabel(1, 1); [0, 1, 2].forEach(i => sheet(i, 1));
        GRID.forEach((g, i) => { const hl = g.crank ? cl(t, 4.1, 4.5) * (1 - cl(t, 6.2, 6.5)) : cl(t, 6.4, 6.8); slip(g, cl(t, .5 + i * .45, 1 + i * .45), hl); });
        if (t > 4.1) { ctx.fillStyle = '#F3ECD8'; ctx.textAlign = 'center'; ctx.font = 'italic 26px "IM Fell English", Georgia, serif'; ctx.fillText(t < 6.3 ? 'you play the crank boy' : 'you sit with the class', 565, SH - 26); }
      },
      tick(t, prev) { for (let i = 0; i < 6; i++) { const a = .75 + i * .45; if (prev < a && t >= a) click(); } }
    },
    { // 9: the lab's own films
      dur: 7.6, cues: [[.5, 'n7']], cb: () => ({ x: LY.cbX, pose: 'crank', face: 1, crank: 1 }),
      enter() { ensureVideo(); if (video) { try { video.currentTime = 137; video.play().catch(() => {}); } catch (e) {} } },
      leave() { if (video) try { video.pause(); } catch (e) {} },
      screen(t) {
        ctx.fillStyle = '#111'; ctx.fillRect(0, 0, SW, SH);
        if (video && video.readyState >= 2) { const vw = video.videoWidth || 16, vh = video.videoHeight || 9, k = Math.min(SW / vw, SH / vh); ctx.drawImage(video, (SW - vw * k) / 2, (SH - vh * k) / 2, vw * k, vh * k); }
        else if (poster && poster.complete && poster.naturalWidth) { const k = Math.min(SW / poster.naturalWidth, SH / poster.naturalHeight); ctx.drawImage(poster, (SW - poster.naturalWidth * k) / 2, (SH - poster.naturalHeight * k) / 2, poster.naturalWidth * k, poster.naturalHeight * k); }
        else { ctx.fillStyle = '#d8c79a'; ctx.textAlign = 'center'; ctx.font = '60px "IM Fell English SC", Georgia, serif'; ctx.fillText('a pAELo film', SW / 2, SH / 2); }
        ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(0, SH - 46, SW, 46); ctx.fillStyle = '#F3ECD8'; ctx.textAlign = 'left'; ctx.font = 'italic 24px "IM Fell English", Georgia, serif'; ctx.fillText('archive footage, a drawn crash-test dummy, edited by hand', 20, SH - 16);
      }
    },
    { // 10: how to play, then one game actually played
      dur: 11.4, cues: [[.3, 'n8']], cb: t => t < 5.6 ? { x: LY.cbX, pose: 'crank', face: 1, crank: 1 } : t < 8.4 ? { x: LY.cbX, pose: 'crank', face: 1, crank: 1.1 } : { x: LY.cbX, pose: 'crank', face: 0, crank: .9, brow: .7 },
      screen(t) {
        if (t < 3.4) {
          ctx.fillStyle = '#EFE6CC'; ctx.fillRect(0, 0, SW, SH);
          GRID.forEach(g => slip(g, 1, 0));
          const tgt = { x: 300, y: 440 }, p = ease(cl(t, .3, 1.6)), px = lerp(800, tgt.x + 40, p), py = lerp(620, tgt.y + 30, p);
          if (t > 1.7) { ctx.strokeStyle = '#B44A3C'; ctx.lineWidth = 6; ctx.strokeRect(tgt.x - 133, tgt.y - 86, 266, 172); }
          ctx.save(); ctx.translate(px, py); blob(() => { ctx.moveTo(0, 0); ctx.lineTo(0, 46); ctx.lineTo(12, 36); ctx.lineTo(22, 58); ctx.lineTo(30, 54); ctx.lineTo(20, 32); ctx.lineTo(36, 32); ctx.closePath(); }, '#FBF7EA', 2.5, 1); ctx.restore();
          if (t > 2.2) { const k = ease(cl(t, 2.2, 3.4)); ctx.fillStyle = `rgba(30,22,15,${k})`; ctx.fillRect(0, 0, SW, SH); }
          return;
        }
        const stopped = t > 7.6, im = stopped ? SHOT.stop : SHOT.crank;
        if (im.complete && im.naturalWidth) ctx.drawImage(im, 0, 0, SW, SH); else { ctx.fillStyle = '#E8D59A'; ctx.fillRect(0, 0, SW, SH); }
        const lab = stopped ? 'Stop turning: the lesson stops, and the class looks at you.' : 'Turn the crank: the book goes down the wires to the class.';
        const a = cl(t, stopped ? 7.7 : 3.7, stopped ? 8.1 : 4.1);
        const big = LY.portrait, bh = big ? 150 : 92; ctx.globalAlpha = a; ctx.fillStyle = 'rgba(20,14,10,.82)'; ctx.fillRect(0, SH - bh, SW, bh);
        ctx.fillStyle = '#F3ECD8'; ctx.textAlign = 'center'; ctx.font = (big ? '52px' : '36px') + ' "IM Fell English", Georgia, serif';
        if (big) { const parts = lab.split(': '); ctx.fillText(parts[0] + ':', SW / 2, SH - 82); ctx.fillText(parts[1], SW / 2, SH - 26, SW - 30); } else ctx.fillText(lab, SW / 2, SH - 34, SW - 40);
        if (!big) { ctx.font = '22px "IM Fell English SC", Georgia, serif'; ctx.fillStyle = '#e9a888'; ctx.fillText('Version 1 · Lesson One', SW / 2, SH - 68); } ctx.globalAlpha = 1;
      },
      tick(t, prev) { if (prev < 1.7 && t >= 1.7) click(); if (prev < 7.6 && t >= 7.6) thump(); }
    },
    { // 11: your turn
      dur: 9999, cues: [[.3, 'cb5']], final: true,
      cb: t => t < 2.6 ? { x: LY.cbX, pose: 'idle', face: 0, brow: .4, crank: 0 } : { x: LY.cbX, pose: 'offer', face: 0, brow: .2, crank: 0 },
      enter() { $('fturn').hidden = false; },
      screen(t) {
        ctx.fillStyle = '#F3ECD8'; ctx.fillRect(0, 0, SW, SH);
        ctx.fillStyle = INK; ctx.textAlign = 'center'; ctx.font = '72px "IM Fell English SC", Georgia, serif'; ctx.fillText('The Crank Boy', SW / 2, 250);
        ctx.font = 'italic 32px "IM Fell English", Georgia, serif'; ctx.fillStyle = '#6E5F4F'; ctx.fillText('six games, one postcard', SW / 2, 310);
        ctx.font = '30px "IM Fell English SC", Georgia, serif'; ctx.fillStyle = '#B44A3C'; ctx.fillText(S.user ? 'keep turning' : 'turn the crank to enter', SW / 2, 420);
      }
    }
  ];
  let starts = []; { let a = 0; starts = SC.map(s => { const r = a; a += s.dur; return r; }); }

  /* ---------- run ---------- */
  let raf = 0, last = 0, prevLocal = 0, fired = new Set();
  function sceneAt(i) { S.scene = i; prevLocal = 0; fired = new Set(); const sc = SC[i]; silenceAll(); $('fcap').hidden = true; if (sc.enter) sc.enter(); musicOn = !!sc.music; if (musicOn && AC) musicNext = AC.currentTime; S.frozen = null; updateBar(); }
  function next() { const sc = SC[S.scene]; if (sc.leave) sc.leave(); if (S.scene < SC.length - 1) sceneAt(S.scene + 1); }
  function prev() { const sc = SC[S.scene]; if (sc.leave) sc.leave(); sceneAt(Math.max(0, S.scene - 1)); S.t = starts[S.scene]; }
  function updateBar() { $('fbar').style.width = (Math.min(1, starts[S.scene] / starts[SC.length - 1]) * 100) + '%'; }
  function frame(now) {
    const dt = Math.min(.05, (now - last) / 1000 || 0); last = now;
    const sc = SC[S.scene];
    if (S.playing) {
      const local = prevLocal + dt;
      sc.cues.forEach(([at, id]) => { if (!fired.has(id) && local >= at) { fired.add(id); say(id); } });
      if (sc.tick) sc.tick(local, prevLocal);
      prevLocal = local; S.t += dt;
      if (!sc.final && local >= sc.dur) next();
    }
    const local = prevLocal;
    // Crank Boy's targets for this moment
    const tg = sc.cb ? sc.cb(local) : { pose: 'idle' };
    const c = S.cb; c.pose = tg.pose || 'idle'; if (tg.x != null) c.x = tg.x; c.face = tg.face == null ? 1 : tg.face; c.brow += ((tg.brow || 0) - c.brow) * Math.min(1, dt * 6); c.rub = c.pose === 'rub' ? 1 : 0;
    let target = S.user ? S.userSpeed : (tg.crank || 0);
    if (!S.playing && !S.user) target = 0;
    S.speed += (target - S.speed) * Math.min(1, dt * (target < S.speed ? 3 : 2.2));
    S.angle += S.speed * TAU * dt;
    // ratchet click every quarter turn
    const q = Math.floor(S.angle / (TAU / 4)); if (q !== S.lastQ) { S.lastQ = q; if (S.speed > .15) click(); }
    // light follows the crank; the wall scene has no projection yet
    const lightTarget = sc.screen ? Math.max(sc.final ? .45 : 0, Math.min(1, S.speed / .9)) : 0;
    S.light += (lightTarget - S.light) * Math.min(1, dt * 4);
    if (AC) { projGain.gain.setTargetAtTime(sound ? Math.min(.12, S.speed * .1) * (.6 + .4 * Math.abs(Math.sin(S.angle * 4))) : 0, AC.currentTime, .02); musicGain.gain.setTargetAtTime(sound && musicOn ? (speaking ? .35 : .9) : 0, AC.currentTime, .2); musicTick(); }
    if (!reduce) S.dust.forEach(d => { d.w += d.sp * dt * S.speed; if (d.w > 1) { d.w = 0; d.u = rnd(); d.v = rnd(); } });
    draw(sc, local, dt);
    if (S.user) userTick(dt);
    if (capUntil && now > capUntil && S.playing) { $('fcap').hidden = true; capUntil = 0; }
    if (!el.hidden) raf = requestAnimationFrame(frame);
  }
  function draw(sc, local, dt) {
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    wall();
    const scr = LY.screen;
    // the screen
    ctx.save(); ctx.beginPath(); ctx.rect(scr.x, scr.y, scr.w, scr.h); ctx.clip();
    ctx.fillStyle = '#1b1510'; ctx.fillRect(scr.x, scr.y, scr.w, scr.h);
    if (sc.screen) {
      ctx.save(); const weave = reduce ? 0 : (rnd() - .5) * 2 * S.light; ctx.translate(weave, weave * .5); toScreen();
      // freeze-frame: when the crank stops, the picture holds its last frame and darkens
      sc.screen(sc.freezeFrom != null && local > sc.freezeFrom && local < 3.9 ? sc.freezeFrom : local);
      filmFx(S.light > .3); ctx.restore();
      ctx.fillStyle = `rgba(10,6,3,${(1 - S.light) * .92 + (reduce ? 0 : rnd(.05) * S.light)})`; ctx.fillRect(scr.x, scr.y, scr.w, scr.h);
    }
    ctx.restore();
    ctx.strokeStyle = '#0d0a07'; ctx.lineWidth = 6; ctx.strokeRect(scr.x - 3, scr.y - 3, scr.w + 6, scr.h + 6);
    if (sc.over) sc.over(local);
    beam();
    projector();
    crankBoy(dt);
    // stage darkness when everything stops
    const dark = sc.freezeFrom != null && local > sc.freezeFrom && local < 3.9 ? Math.min(.55, (local - sc.freezeFrom) * .8) : 0;
    if (dark) { ctx.fillStyle = `rgba(0,0,0,${dark})`; ctx.fillRect(0, 0, W, H); }
    if (!grainPat) grainPat = ctx.createPattern(grain, 'repeat');
    ctx.globalAlpha = .06; ctx.globalCompositeOperation = 'overlay'; ctx.fillStyle = grainPat; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  }

  /* ---------- the viewer's crank (final scene) ---------- */
  let turned = 0, lastA = null, dragging = false;
  const dial = () => $('fdial');
  function dialAngle(e) { const r = dial().getBoundingClientRect(); return Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)); }
  function userTick(dt) {
    S.userSpeed *= Math.exp(-1.5 * dt);
    $('fknob').setAttribute('transform', `rotate(${(S.angle * 180 / Math.PI) % 360})`);
    if (turned >= 2 * TAU && !S.entering) { S.entering = true; bell(); setTimeout(close, 900); }
  }
  function bindDial() {
    const d = dial();
    d.addEventListener('pointerdown', e => { audioInit(); dragging = true; lastA = dialAngle(e); S.user = true; S.userSpeed = S.userSpeed || 0; d.setPointerCapture(e.pointerId); e.preventDefault(); });
    d.addEventListener('pointermove', e => { if (!dragging) return; const a = dialAngle(e); let dd = a - lastA; if (dd > Math.PI) dd -= TAU; if (dd < -Math.PI) dd += TAU; lastA = a; if (dd > 0) { turned += dd; S.userSpeed = Math.min(2.4, S.userSpeed + dd * 1.6); } });
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(ev => d.addEventListener(ev, () => { dragging = false; }));
    d.addEventListener('keydown', e => { if (e.key === ' ' || e.key === 'Enter' || e.key === 'ArrowRight') { e.preventDefault(); audioInit(); S.user = true; turned += TAU / 4; S.userSpeed = Math.min(2.4, (S.userSpeed || 0) + .6); } });
  }

  /* ---------- open / close ---------- */
  function start(withSound) {
    sound = withSound; if (withSound) { audioInit(); if (AC && AC.state === 'suspended') AC.resume(); }
    $('fgate').hidden = true; $('fctl').hidden = false; $('fsound').textContent = sound ? 'Sound off' : 'Sound on';
    S.playing = true; S.t = 0; S.user = false; S.entering = false; turned = 0; S.userSpeed = 0; $('fturn').hidden = true; sceneAt(0);
  }
  function open() {
    el.hidden = false; document.documentElement.classList.add('filming');
    $('fgate').hidden = false; $('fctl').hidden = true; $('fcap').hidden = true; $('fturn').hidden = true;
    S.playing = false; S.cb.x = -400; S.speed = 0; S.light = 0; S.scene = 0; prevLocal = 0;
    layout(); last = performance.now(); cancelAnimationFrame(raf); raf = requestAnimationFrame(frame);
    setTimeout(() => $('fstart').focus(), 30);
  }
  function close() {
    silenceAll(); const sc = SC[S.scene]; if (sc && sc.leave) sc.leave(); musicOn = false;
    if (AC) { projGain.gain.value = 0; musicGain.gain.value = 0; }
    el.hidden = true; document.documentElement.classList.remove('filming'); cancelAnimationFrame(raf);
    try { localStorage.setItem('crankboy.filmSeen', '1'); } catch (e) {}
    if (window.CrankSite) window.CrankSite.afterFilm();
  }
  $('fstart').onclick = () => start(true);
  $('fquiet').onclick = () => start(false);
  $('fskip0').onclick = close; $('fskip').onclick = close; $('fenter').onclick = close;
  $('fpause').onclick = () => { S.playing = !S.playing; $('fpause').textContent = S.playing ? 'Pause' : 'Play'; if (!S.playing) silenceAll(); };
  $('fsound').onclick = () => { sound = !sound; if (sound) audioInit(); else silenceAll(); $('fsound').textContent = sound ? 'Sound off' : 'Sound on'; };
  $('fnext').onclick = () => { if (!SC[S.scene].final) next(); };
  $('fprev').onclick = prev;
  window.addEventListener('keydown', e => {
    if (el.hidden) return;
    if (e.key === 'Escape') { e.preventDefault(); close(); }
    else if (!$('fgate').hidden) return;
    else if (e.key === 'ArrowRight' && document.activeElement !== dial()) $('fnext').click();
    else if (e.key === 'ArrowLeft') prev();
    else if (e.key === 'p' || e.key === 'P') $('fpause').click();
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden && !el.hidden && S.playing) $('fpause').click(); });
  window.addEventListener('resize', () => { if (!el.hidden) layout(); });
  bindDial();
  return { open, close };
})();
