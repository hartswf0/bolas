// The stage the shorts are drawn on. One composition per page: Stage({...}) builds the canvas, loads the card,
// its cut parts and the archive plates, and draws any frame from its time alone, so the same page previews in the
// browser and renders frame by frame (shorts/tools/render.py). Card pixels are drawn as cut; plates are drawn as
// found, only toned and masked. Everything else on screen is drawn here and is listed in each page's ledger.
(function () {
  const INK = '#2B2320', PAPER = '#F3ECD8', TABLE = '#D6C69E', RED = '#B44A3C', BRASS = '#C9A23E';
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const seg = (t, a, b) => clamp((t - a) / (b - a));
  const ease = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
  const easeOut = k => 1 - Math.pow(1 - k, 3);
  const easeIn = k => k * k * k;
  const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const noise = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; };
  const hexRGB = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));

  function loadImg(src) {
    return new Promise((ok, no) => { const im = new Image(); im.onload = () => ok(im); im.onerror = () => no(new Error(src)); im.src = src; });
  }
  function loadVid(src) {
    return new Promise((ok, no) => {
      const v = document.createElement('video');
      v.muted = true; v.preload = 'auto'; v.playsInline = true; v.crossOrigin = 'anonymous';
      v.onloadeddata = () => ok(v); v.onerror = () => no(new Error(src)); v.src = src;
    });
  }
  function seek(v, t) {
    t = clamp(t, 0, v.duration - 0.03);
    if (Math.abs(v.currentTime - t) < 0.004 && v.readyState >= 2) return Promise.resolve();
    return new Promise(ok => { const f = () => { v.removeEventListener('seeked', f); ok(); }; v.addEventListener('seeked', f); v.currentTime = t; });
  }

  window.Stage = function (cfg) {
    const W = cfg.w || 960, H = cfg.h || 540, FPS = cfg.fps || 24, DUR = cfg.dur;
    const base = cfg.base || '../assets/shorts/';
    const cv = document.getElementById('stage');
    cv.width = W; cv.height = H;
    const ctx = cv.getContext('2d');
    const S = { W, H, FPS, DUR, ctx, cv, clamp, lerp, seg, ease, easeOut, easeIn, hash, noise, INK, PAPER, TABLE, RED, BRASS,
      img: {}, part: null, parts: {}, vid: {}, cam: { x: 0, y: 0, z: 1, r: 0 }, t: 0 };
    const off = document.createElement('canvas'), octx = off.getContext('2d', { willReadFrequently: true });
    const grain = document.createElement('canvas'); grain.width = grain.height = 256;
    { const g = grain.getContext('2d'), d = g.createImageData(256, 256);
      for (let i = 0; i < d.data.length; i += 4) { const v = 200 + hash(i * .37) * 55; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
      g.putImageData(d, 0, 0); }

    S.seek = seek;
    S.ready = (async () => {
      await document.fonts.load('40px "IM Fell English"'); await document.fonts.load('40px "IM Fell English SC"');
      if (cfg.card) {
        const m = await (await fetch(base + 'parts/' + cfg.card + '/parts.json')).json();
        S.manifest = m;
        S.img.clean = await loadImg(base + 'parts/' + cfg.card + '/clean.jpg');
        S.img.card = await loadImg('../' + m.card);
        for (const [k, p] of Object.entries(m.parts)) { S.parts[k] = p; p.im = await loadImg(base + 'parts/' + cfg.card + '/' + k + '.png'); }
      }
      // several cards at once (the world): parts are 'card/name', plates are '<card>/clean', '<card>/empty', '<card>/card'
      S.cards = {};
      for (const c of cfg.cards || []) {
        const m = await (await fetch(base + 'parts/' + c + '/parts.json')).json(); S.cards[c] = m;
        S.img[c + '/clean'] = await loadImg(base + 'parts/' + c + '/clean.jpg');
        S.img[c + '/card'] = await loadImg('../' + m.card);
        S.img[c + '/empty'] = m.empty ? await loadImg(base + 'parts/' + c + '/empty.jpg') : S.img[c + '/clean'];
        await Promise.all(Object.entries(m.parts).map(async ([k, p]) => { S.parts[c + '/' + k] = p; p.im = await loadImg(base + 'parts/' + c + '/' + k + '.png'); }));
      }
      for (const [k, src] of Object.entries(cfg.images || {})) S.img[k] = await loadImg(src);
      for (const k of cfg.plates || []) S.vid[k] = await loadVid(base + 'plates/' + k + '.mp4');
      S.data = {}; for (const [k, src] of Object.entries(cfg.json || {})) S.data[k] = await (await fetch(src)).json();
      const f = cfg.frame || [0, 0, S.img.card ? S.img.card.width : W, S.img.card ? S.img.card.height : H];   // the world sets its own
      S.frameRect = f;
      S.fit = Math.max(W / (f[2] - f[0]), H / (f[3] - f[1]));
      S.home = { x: (f[0] + f[2]) / 2, y: (f[1] + f[3]) / 2, z: 1, r: 0 };
      if (cfg.setup) await cfg.setup(S);
      if (typeof cfg.cues === 'function') window.SHORT.cues = cfg.cues(S);
    })();

    // camera: card point (x, y) at the centre of the screen, zoom z on top of the fit, roll r
    S.view = (c = S.cam) => { const k = S.fit * c.z; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.translate(W / 2, H / 2); ctx.rotate(c.r || 0); ctx.scale(k, k); ctx.translate(-c.x, -c.y); };
    S.screen = () => ctx.setTransform(1, 0, 0, 1, 0, 0);
    S.layer = (depth, c = S.cam) => {
      // a multiplane level: depth 1 moves with the camera, larger depth moves less (farther), smaller moves more
      const h = S.home, p = { x: h.x + (c.x - h.x) / depth, y: h.y + (c.y - h.y) / depth, z: 1 + (c.z - 1) / depth, r: c.r };
      S.view(p);
    };
    S.bg = (which = 'clean') => ctx.drawImage(S.img[which], 0, 0);
    // a cut part, moved about its pivot: dx, dy in card pixels, rot in radians, sc scale, a alpha
    S.drawPart = (name, o = {}) => {
      const p = S.parts[name]; if (!p) return;
      const [px, py] = o.pivot || p.pivot, ctx = o.ctx || S.ctx;
      ctx.save(); ctx.globalAlpha *= o.a == null ? 1 : o.a;
      ctx.translate(px + (o.dx || 0), py + (o.dy || 0)); ctx.rotate(o.rot || 0); ctx.scale(o.sx || o.sc || 1, o.sy || o.sc || 1);
      ctx.drawImage(o.im || p.im, p.x - px, p.y - py);
      ctx.restore();
    };
    // an archive plate frame, toned between two inks (a gradient map), into a card-space rect
    S.plateFrame = (name, o = {}) => {
      const v = S.vid[name]; const vw = v.videoWidth, vh = v.videoHeight;
      const [sx, sy, sw, sh] = o.crop || [0, 0, vw, vh];
      const ow = Math.max(2, Math.round(o.res || sw)), oh = Math.max(2, Math.round(ow * sh / sw));
      off.width = ow; off.height = oh;
      octx.drawImage(v, sx, sy, sw, sh, 0, 0, ow, oh);
      if (o.tone) {
        const d = octx.getImageData(0, 0, ow, oh), a = hexRGB(o.tone[0]), b = hexRGB(o.tone[1]);
        const c = o.contrast || 1, lift = o.lift || 0;
        for (let i = 0; i < d.data.length; i += 4) {
          let l = (d.data[i] * .3 + d.data[i + 1] * .59 + d.data[i + 2] * .11) / 255;
          l = clamp((l - .5) * c + .5 + lift);
          const m = o.keep ? o.keep : 0;
          for (let j = 0; j < 3; j++) d.data[i + j] = lerp(a[j] + (b[j] - a[j]) * l, d.data[i + j], m);
          if (o.lumaAlpha) d.data[i + 3] = 255 * clamp(o.lumaAlpha === 'dark' ? (1 - l) * 1.6 - .2 : l * 1.6 - .3);
          if (o.fade) d.data[i + 3] *= clamp((1 - Math.floor(i / 4 / ow) / oh) / o.fade);   // soften the bottom edge
        }
        octx.putImageData(d, 0, 0);
      }
      return off;
    };
    S.plate = (name, rect, o = {}) => {
      const src = S.plateFrame(name, o);
      ctx.save(); ctx.globalAlpha *= o.a == null ? 1 : o.a;
      if (o.blend) ctx.globalCompositeOperation = o.blend;
      if (o.clip) { ctx.beginPath(); o.clip(ctx); ctx.clip(); }
      ctx.drawImage(src, rect[0], rect[1], rect[2], rect[3]);
      ctx.restore();
    };
    // a plate inside a soft-edged region of the card: the region is blurred into a mask so no hard edge shows
    const soft = document.createElement('canvas'), sctx = soft.getContext('2d');
    S.softPlate = (name, rect, pts, blur, o = {}) => {
      const [cw, ch] = o.size || S.manifest.size; soft.width = cw; soft.height = ch;
      sctx.drawImage(S.plateFrame(name, o), rect[0], rect[1], rect[2], rect[3]);
      sctx.globalCompositeOperation = 'destination-in'; sctx.filter = `blur(${blur}px)`; sctx.fillStyle = '#000';
      sctx.beginPath(); pts.forEach(([x, y], i) => i ? sctx.lineTo(x, y) : sctx.moveTo(x, y)); sctx.closePath(); sctx.fill();
      sctx.filter = 'none'; sctx.globalCompositeOperation = 'source-over';
      ctx.save(); ctx.globalAlpha *= o.a == null ? 1 : o.a; if (o.blend) ctx.globalCompositeOperation = o.blend; ctx.drawImage(soft, 0, 0); ctx.restore();
    };
    // a drawn brass member, inked then filled a hair off register, like the card's two plates
    S.rod = (pts, o = {}) => {
      const w = o.w || 4;
      ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
      ctx.strokeStyle = o.ink || INK; ctx.lineWidth = w + 2.2; ctx.stroke();
      ctx.translate(.7, .5); ctx.strokeStyle = o.fill || BRASS; ctx.lineWidth = w; ctx.stroke();
      ctx.restore();
    };
    S.joint = (x, y, r = 3.5, o = {}) => {
      ctx.save(); ctx.beginPath(); ctx.arc(x, y, r + 1.1, 0, 7); ctx.fillStyle = o.ink || INK; ctx.fill();
      ctx.beginPath(); ctx.arc(x + .6, y + .4, r, 0, 7); ctx.fillStyle = o.fill || BRASS; ctx.fill();
      ctx.beginPath(); ctx.arc(x, y, r * .35, 0, 7); ctx.fillStyle = INK; ctx.fill(); ctx.restore();
    };
    // print grain over everything, shifted per frame like film
    S.grain = (amt = .13) => {
      S.screen(); ctx.save(); ctx.globalAlpha = amt; ctx.globalCompositeOperation = 'multiply';
      const f = Math.floor(S.t * FPS), ox = (hash(f) * 256) | 0, oy = (hash(f + 9) * 256) | 0;
      const pat = ctx.createPattern(grain, 'repeat'); ctx.translate(-ox, -oy); ctx.fillStyle = pat; ctx.fillRect(0, 0, W + 256, H + 256);
      ctx.restore();
    };
    S.vignette = (amt = .35) => {
      S.screen(); const g = ctx.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, H * .85);
      g.addColorStop(0, 'rgba(43,35,32,0)'); g.addColorStop(1, `rgba(43,35,32,${amt})`);
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    };
    // title and end cards, set like the series' captions
    S.card = (lines, a = 1, o = {}) => {
      if (a <= 0) return;
      S.screen(); ctx.save(); ctx.globalAlpha = a;
      ctx.fillStyle = o.bg || PAPER; ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = INK; ctx.lineWidth = 2; ctx.strokeRect(28, 28, W - 56, H - 56); ctx.lineWidth = .8; ctx.strokeRect(36, 36, W - 72, H - 72);
      ctx.fillStyle = INK; ctx.textAlign = 'center';
      // a line is [text, size, style]; style is any of 'sc' (small capitals) and 'dim'
      const L = lines.map(l => Array.isArray(l) ? l : [l, 26, '']);
      const hs = L.map(([, size]) => size * 1.5), total = hs.reduce((a, b) => a + b, 0);
      let y = (o.y || H / 2) - total / 2;
      L.forEach(([txt, size, st = ''], i) => {
        ctx.font = `${size}px "IM Fell English${/sc/.test(st) ? ' SC' : ''}", Georgia, serif`;
        ctx.globalAlpha = a * (/dim/.test(st) ? .72 : 1);
        ctx.fillText(txt, W / 2, y + hs[i] * .72); y += hs[i];
      });
      ctx.restore(); S.grain(.1);
    };
    S.caption = (txt, a = 1, y = H - 34) => {
      if (a <= 0) return;
      S.screen(); ctx.save(); ctx.globalAlpha = a; ctx.font = '22px "IM Fell English", Georgia, serif'; ctx.textAlign = 'center';
      const w = ctx.measureText(txt).width + 28;
      ctx.fillStyle = 'rgba(243,236,216,.88)'; ctx.fillRect(W / 2 - w / 2, y - 22, w, 32);
      ctx.fillStyle = INK; ctx.fillText(txt, W / 2, y); ctx.restore();
    };

    // precomputed simulations: step(state, dt, t) from t = 0 at 1/(FPS*sub) and keep a snapshot per frame
    S.simulate = (init, step, sub = 4) => {
      const n = Math.ceil(DUR * FPS) + 1, out = new Array(n); let s = init(); const dt = 1 / (FPS * sub);
      for (let f = 0; f < n; f++) { out[f] = JSON.parse(JSON.stringify(s)); for (let k = 0; k < sub; k++) step(s, dt, f / FPS + k * dt); }
      return t => out[clamp(Math.round(t * FPS), 0, n - 1)];
    };

    S.drawAt = async t => {
      S.t = t;
      const clocks = cfg.clock ? cfg.clock(t, S) : {};
      await Promise.all(Object.entries(clocks).map(([k, s]) => seek(S.vid[k], s)));
      S.cam = Object.assign({}, S.home, cfg.camera ? cfg.camera(t, S) : {});
      if (!cfg.freeCamera) { // keep the view on the card
        const f = S.frameRect, hw = W / (2 * S.fit * S.cam.z), hh = H / (2 * S.fit * S.cam.z);
        S.cam.x = clamp(S.cam.x, f[0] + hw, Math.max(f[0] + hw, f[2] - hw)); S.cam.y = clamp(S.cam.y, f[1] + hh, Math.max(f[1] + hh, f[3] - hh));
      }
      S.screen(); ctx.fillStyle = TABLE; ctx.fillRect(0, 0, W, H);
      cfg.draw(S, t);
    };

    if (cfg.manual) return S;   // the page runs its own loop and sets window.SHORT itself
    window.SHORT = { id: cfg.id, dur: DUR, fps: FPS, poster: cfg.poster || 0, cues: Array.isArray(cfg.cues) ? cfg.cues : [], ready: S.ready, frame: async i => { await S.ready; await S.drawAt(i / FPS); return cv.toDataURL('image/jpeg', .93); } };

    // preview: play, pause and scrub without sound (the rendered film has the sound)
    if (!cfg.manual && !/render/.test(location.search)) S.ready.then(() => {
      const bar = document.getElementById('scrub'), btn = document.getElementById('play'), tc = document.getElementById('tc');
      let playing = false, t0 = 0, start = 0, busy = false;
      const show = async t => { if (busy) return; busy = true; await S.drawAt(t); busy = false; if (bar) bar.value = t / DUR * 1000; if (tc) tc.textContent = t.toFixed(1) + ' s'; };
      const loop = async now => { if (!playing) return; const t = t0 + (now - start) / 1000; if (t >= DUR) { playing = false; btn && (btn.textContent = 'Play'); return; } await show(t); requestAnimationFrame(loop); };
      if (btn) btn.onclick = () => { playing = !playing; btn.textContent = playing ? 'Pause' : 'Play'; if (playing) { t0 = (bar ? bar.value / 1000 * DUR : 0) % DUR; start = performance.now(); requestAnimationFrame(loop); } };
      if (bar) bar.oninput = () => { playing = false; btn && (btn.textContent = 'Play'); show(bar.value / 1000 * DUR); };
      show(cfg.poster || 0);
    });
    return S;
  };
})();
