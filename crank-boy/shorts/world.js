// The Town: the seven cards as one world, joined by a drawn power line from the crank boy's machine.
// Each card is a district with its own game, worked by an operator its short did not use. The same engine
// plays the cartoon (?film: every frame stepped from a fixed script, for shorts/tools/render.mjs) and the game.
// Card pixels are cut pieces; the drawn layer is real Quick, Draw! doodles (assets/shorts/doodles.json, CC BY 4.0).
(function () {
  const Q = new URLSearchParams(location.search), FILM = Q.has('film') || Q.has('render'), ONLY = Q.get('d');
  const CH = 300, GAP = 96, TOP = -40;   // each card is 300 world units tall; streets between; the line runs above
  const D = [
    { id: 'school', frame: [24, 26, 778, 458], title: 'À l’école', op: 'Video Puppetry: the crank is performed, not keyed', feed: [706, 60], slot: 'boy', perform: 'crank',
      goal: 'Turn the crank. Every full turn sends a book down a wire. Deliver twelve.' },
    { id: 'scrubber', frame: [44, 44, 912, 548], title: 'Un frotteur électrique', op: 'Sketchpad: drag a brush, the constraints keep the legs', feed: [408, 150], slot: 'maid', perform: 'push',
      goal: 'Drag the brushes across the floor. Polish two thirds of it and the floor becomes a mirror.' },
    { id: 'barber', frame: [4, 4, 582, 337], title: 'The barber', op: 'Character Animator: triggered states on a beat', feed: [548, 96], slot: 'op', perform: 'pull',
      goal: 'The gauge swings left and right. Pull the left or right arm as it lands. Sixteen clean cuts.' },
    { id: 'phono-cinema', frame: [6, 4, 956, 556], title: 'Phonograph and cinema', op: 'JibJab: recast the answer, keep the performance', feed: [100, 40],
      goal: 'Hold Speak, then let go: the screen answers for as long as you spoke. Choose who answers.' },
    { id: 'air-cabs', frame: [4, 4, 582, 337], title: 'Air cabs over Paris', op: 'Rive: a cab that runs on states', feed: [185, 20],
      goal: 'Steer the big cab up and down. Pick up a waving hand, set it down at the star over the Opéra. Wings tire.' },
    { id: 'firemen', frame: [6, 6, 954, 552], title: 'Flying firemen', op: 'State machines: flyers that refuse', feed: [305, 455],
      goal: 'Aim the hose at the flames. Keep the pressure up: without water the flyers will not go near the fire.' },
    { id: 'skates', frame: [4, 4, 582, 337], title: 'Motor skates', op: 'Drawing substitution: when a pose fails, swap the drawing', feed: [560, 22],
      goal: 'Stride left, right, left, right. Too fast, or the same foot twice, and the couple falls. Skate a hundred metres.' }
  ];
  let X = 0; for (const d of D) { d.s = CH / (d.frame[3] - d.frame[1]); d.w = (d.frame[2] - d.frame[0]) * d.s; d.x = X; X += d.w + GAP; }
  const WORLD_W = X - GAP;
  const byId = Object.fromEntries(D.map(d => [d.id, d]));
  // the recastable cast: three handle-holders, each an upper body that performs over planted legs
  const ACTORS = {
    boy: { card: 'school', up: 'boyUp', lo: 'boyLegs', hip: [520, 305], top: 180, feet: 446, name: 'the crank boy' },
    maid: { card: 'scrubber', up: 'maidUp', lo: 'maidLo', hip: [800, 300], top: 120, feet: 507, name: 'the maid' },
    op: { card: 'barber', up: 'opUp', lo: 'opLo', hip: [455, 178], top: 56, feet: 326, name: 'the lever man' }
  };
  const cast = { school: 'boy', scrubber: 'maid', barber: 'op' };

  // ---- the stage: all seven cards and the plates
  const PLATES = ['frigidaire', 'barbers', 'dancers1914', 'lecturer', 'hosedrill', 'shadowplay', 'cropduster', 'wildfire', 'smoke'];
  const S = Stage({ id: 'world', manual: true, cards: D.map(d => d.id), plates: PLATES, json: { doodles: '../assets/shorts/doodles.json' } });
  const ctx = S.ctx, W = S.W, H = S.H, clamp = S.clamp, lerp = S.lerp;
  let rng = 1; const rand = () => (rng = (rng * 16807) % 2147483647) / 2147483647;

  // ---- doodles: Quick, Draw! strokes in a 0..255 box, drawn with a slight boil
  function doodle(word, x, y, size, o = {}) {
    const dd = S.data.doodles.doodles[word]; if (!dd) return;
    const k = size / 255, boil = o.boil == null ? 1.2 : o.boil, f = Math.floor(T.t * 8);
    ctx.save(); ctx.translate(x, y); if (o.rot) ctx.rotate(o.rot); if (o.flip) ctx.scale(-1, 1);
    ctx.globalAlpha *= o.a == null ? 1 : o.a; ctx.strokeStyle = o.c || S.INK; ctx.lineWidth = (o.lw || 3.4) / (o.zoom || 1); ctx.lineCap = ctx.lineJoin = 'round';
    dd.drawing.forEach(([xs, ys], si) => { ctx.beginPath(); xs.forEach((px, i) => {
      const jx = S.noise(f * 1.7 + si * 3.1 + i) * boil, jy = S.noise(f * 2.3 + si * 5.7 + i + 40) * boil;
      const X2 = (px - 127) * k + jx / k * k, Y2 = (ys[i] - 127) * k + jy;
      i ? ctx.lineTo(X2, Y2) : ctx.moveTo(X2, Y2); }); ctx.stroke(); });
    ctx.restore();
  }
  // a hand-drawn line, wobbling like the doodles
  function wobbly(pts, o = {}) {
    const f = Math.floor(T.t * 8);
    ctx.save(); ctx.strokeStyle = o.c || S.INK; ctx.lineWidth = o.lw || 2; ctx.lineCap = ctx.lineJoin = 'round'; ctx.beginPath();
    pts.forEach(([x, y], i) => { const jx = S.noise(f + i * 1.3) * (o.boil || 1), jy = S.noise(f + i * 2.1 + 9) * (o.boil || 1); i ? ctx.lineTo(x + jx, y + jy) : ctx.moveTo(x + jx, y + jy); });
    ctx.stroke(); ctx.restore();
  }

  // ---- time, input, power
  const T = { t: 0, dt: 1 / 24 };
  const IN = { crank: 0, crankAngle: 0, down: false, px: 0, py: 0, wx: 0, wy: 0, keys: {}, tap: [], speak: false };
  const P = { turns: 0, omega: 0, power: 0, hist: [] };  // power history lets the line carry it with a delay
  function powerAt(dist) { const lag = dist / 900, i = P.hist.length - 1 - Math.round(lag / T.dt); return i >= 0 ? P.hist[i] : 0; }

  // ---- card space helpers
  const toCard = (d, wx, wy) => [d.frame[0] + (wx - d.x) / d.s, d.frame[1] + (wy) / d.s];
  const toWorld = (d, cx, cy) => [d.x + (cx - d.frame[0]) * d.s, (cy - d.frame[1]) * d.s];
  function inCard(d, fn) { ctx.save(); ctx.translate(d.x, 0); ctx.scale(d.s, d.s); ctx.translate(-d.frame[0], -d.frame[1]);
    ctx.beginPath(); ctx.rect(d.frame[0], d.frame[1], d.frame[2] - d.frame[0], d.frame[3] - d.frame[1]); ctx.clip(); fn(); ctx.restore(); }
  const part = (d, name, o) => S.drawPart(d.id + '/' + name, o || {});

  // ---- the performance, independent of who performs it (JibJab: the cast changes, the choreography does not)
  function perform(kind, ph, amp) {   // returns the upper body's offset as a fraction of the actor's height
    if (kind === 'crank') return { dx: .024 * Math.cos(ph) * amp, dy: .027 * Math.sin(ph) * amp, rot: .028 * Math.sin(ph) * amp };
    if (kind === 'push') return { dx: .03 * Math.sin(ph) * amp, dy: .006 * Math.abs(Math.sin(ph)) * amp, rot: .02 * Math.sin(ph) * amp };
    return { dx: -.015 * Math.sin(ph) * amp, dy: .01 * Math.max(0, Math.sin(ph)) * amp, rot: -.05 * Math.sin(ph) * amp };   // pull
  }
  function drawActor(d, slotActor, ph, amp) {
    const native = ACTORS[d.slot], who = ACTORS[cast[d.id]], perf = perform(d.perform, ph, amp);
    const hN = native.feet - native.top, hW = who.feet - who.top, k = hN / hW;
    // place the recast actor so its feet stand on the native feet and its height matches
    const ox = native.hip[0], oy = native.feet;
    ctx.save(); ctx.translate(ox, oy); ctx.scale(k, k); ctx.translate(-who.hip[0], -who.feet);
    S.drawPart(who.card + '/' + who.lo, {});
    S.drawPart(who.card + '/' + who.up, { dx: perf.dx * hW, dy: perf.dy * hW, rot: perf.rot });
    ctx.restore();
  }

  // ---------------------------------------------------------------- districts
  const G = {};   // per-district game state
  const IK = (H, Tt, L1, L2, near) => { const dx = Tt[0] - H[0], dy = Tt[1] - H[1], d0 = Math.hypot(dx, dy), d = clamp(d0, Math.abs(L1 - L2) + 1e-3, L1 + L2 - 1e-3);
    const b = Math.atan2(dy, dx), a = Math.acos((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d));
    const ks = [1, -1].map(s => [H[0] + L1 * Math.cos(b + s * a), H[1] + L1 * Math.sin(b + s * a)]);
    const K = Math.hypot(ks[0][0] - near[0], ks[0][1] - near[1]) < Math.hypot(ks[1][0] - near[0], ks[1][1] - near[1]) ? ks[0] : ks[1];
    return { K, F: [H[0] + d * Math.cos(b), H[1] + d * Math.sin(b)] }; };

  const DIST = {
    school: {
      init() { return { books: 0, flying: [], lastTurn: 0, lift: 0 }; },
      update(g, p, dt) {
        const whole = Math.floor(P.turns);
        if (whole > g.lastTurn) { g.lastTurn = whole; if (p > .3) { g.flying.push({ t: 0, pupil: whole % 6 }); sfx('blip', 660 + 60 * (whole % 6)); } }
        g.flying.forEach(b => b.t += dt * (.5 + p)); const done = g.flying.filter(b => b.t >= 1); g.books += done.length; g.flying = g.flying.filter(b => b.t < 1);
        if (done.length) sfx('bonk', 180);
        g.lift = clamp(g.lift + (p < .15 ? dt * 2 : -dt * 3));
        return `${Math.min(g.books, 12)} of 12 books delivered` + (g.books >= 12 ? '. The lesson is in. Keep turning or the heads come up.' : '');
      },
      draw(d, g, p) {
        S.bg(cast.school === 'boy' ? 'school/clean' : 'school/empty');
        drawActor(d, cast.school, P.turns * Math.PI * 2, Math.min(1, P.omega / .6));
        part(d, 'head', { dy: -14 * g.lift });
        // the crank, drawn on the printed axle
        const a = P.turns * Math.PI * 2 - Math.PI / 2, hx = 612 + 30 * Math.cos(a), hy = 338 + 16 * Math.sin(a);
        S.rod([[612, 338], [hx, hy]], { w: 3.4, fill: '#4F6A88' }); S.joint(612, 338, 3.2, { fill: '#4F6A88' });
        const pupils = [[42, 190], [112, 190], [190, 183], [270, 182], [325, 180], [405, 181]];
        g.flying.forEach(b => { const [x, y] = pupils[b.pupil], k = b.t;
          const px = k < .5 ? lerp(700, x, k * 2) : x, py = k < .5 ? 48 : lerp(48, y - 8, (k - .5) * 2);
          doodle('book', px, py, 26, { rot: k * 6, lw: 2.4 }); });
        if (g.books >= 12) doodle('light bulb', 200, 150, 40, { c: S.RED, a: .7 + .3 * Math.sin(T.t * 6) });
      }
    },
    scrubber: {
      init() { const c = document.createElement('canvas'); c.width = 960; c.height = 597;
        return { polish: c, broom: [318, 376], brush: [499, 352], grab: null, cover: 0, n: 0 }; },
      update(g, p, dt, act) {
        if (act) {   // drag the nearest brush; it can only go where the floor is and the legs reach
          const [cx, cy] = IN.card;
          if (IN.down && !g.grab) g.grab = Math.hypot(cx - g.broom[0], cy - g.broom[1]) < Math.hypot(cx - g.brush[0] - 40, cy - g.brush[1] - 20) ? 'broom' : 'brush';
          if (!IN.down) g.grab = null;
          if (g.grab) { const tgt = [clamp(cx, 160, 840), clamp(cy, 340, 520)], cur = g[g.grab];
            const sp = 260 * dt * (.25 + p); const dx = tgt[0] - cur[0], dy = tgt[1] - cur[1], L = Math.hypot(dx, dy);
            if (L > 0) { const m = Math.min(L, sp); cur[0] += dx / L * m; cur[1] += dy / L * m; } }
        } else { const t = T.t; g.broom = [318 + 60 * Math.sin(t * 1.3), 380 + 20 * Math.sin(t * .7)]; g.brush = [540 + 110 * Math.sin(t * 1.1 + 1), 380 + 40 * Math.sin(t * .5)]; }
        if (p > .2) { const pc = g.polish.getContext('2d'); pc.fillStyle = 'rgba(0,0,0,.25)';
          pc.beginPath(); pc.ellipse(g.broom[0], g.broom[1] + 22, 30, 11, 0, 0, 7); pc.fill(); pc.beginPath(); pc.ellipse(g.brush[0] + 34, g.brush[1] + 32, 56, 14, 0, 0, 7); pc.fill(); }
        if (++g.n % 12 === 0) { const im = g.polish.getContext('2d').getImageData(100, 330, 810, 222).data; let on = 0, all = 0;
          for (let i = 3; i < im.length; i += 4 * 37) { all++; if (im[i] > 120) on++; } g.cover = on / all; }
        return `${Math.round(g.cover * 100)}% of the floor polished` + (g.cover > .66 ? '. The floor is a mirror: Frigidaire Finale, 1957.' : '');
      },
      draw(d, g, p) {
        S.bg(cast.scrubber === 'maid' ? 'scrubber/clean' : 'scrubber/empty');
        const ra = clamp(g.cover * 1.3) * .85;
        if (ra > .02) { const src = S.plateFrame('frigidaire', { tone: ['#6a4234', '#ffffff'], keep: .45, contrast: 1.4, lift: .08, res: 200 });
          const r = mirror; r.width = 960; r.height = 597; const rc = r.getContext('2d'); rc.clearRect(0, 0, 960, 597);
          rc.save(); rc.translate(100, 552); rc.scale(1, -1); rc.drawImage(src, 0, 0, 810, 222); rc.restore();
          rc.globalCompositeOperation = 'destination-in'; rc.filter = 'blur(4px)'; rc.drawImage(g.polish, 0, 0); rc.filter = 'none';
          ctx.save(); ctx.globalAlpha = ra; ctx.drawImage(r, 0, 0); ctx.restore(); }
        const legs = { broom: { hip: [373, 177], knee0: [383, 253], L1: 80, L2: 160 }, brush: { hip: [472, 185], knee0: [495, 310], L1: 127, L2: 78 } };
        const sol = {}; for (const k in legs) { const L = legs[k], s = IK(L.hip, g[k], L.L1, L.L2, L.knee0); sol[k] = s; g[k] = s.F.slice(); S.rod([L.hip, s.K, s.F], { w: 4.2 }); S.joint(s.K[0], s.K[1], 3.6); }
        part(d, 'body'); part(d, 'broom', { dx: sol.broom.F[0] - 318, dy: sol.broom.F[1] - 376 }); part(d, 'brush', { dx: sol.brush.F[0] - 499, dy: sol.brush.F[1] - 352 });
        drawActor(d, cast.scrubber, T.t * 2.4, p);
        if (g.grab) { const b = g[g.grab]; ctx.save(); ctx.strokeStyle = S.RED; ctx.lineWidth = 2; ctx.setLineDash([5, 4]); ctx.beginPath(); ctx.arc(b[0] + (g.grab === 'brush' ? 40 : 0), b[1] + 20, 34, 0, 7); ctx.stroke(); ctx.restore(); }
        doodle('broom', 210, 470, 70, { rot: -.3 + .15 * Math.sin(T.t * 3), c: S.INK, a: .55 });
      }
    },
    barber: {
      init() { return { hits: 0, miss: 0, swing: { L: 0, R: 0 }, last: -1, flash: 0 }; },
      update(g, p, dt, act) {
        const per = 1 / 1.2, nb = Math.round(T.t / per), side = nb % 2 ? 'R' : 'L', off = T.t - nb * per, near = Math.abs(off) < .3 * per;
        g.beat = { side: Math.floor(T.t / per) % 2 ? 'R' : 'L', ph: (T.t / per) % 1 };
        const press = k => { if (near && k === side && g.last !== nb && p > .15) { g.hits++; g.last = nb; g.swing[k] = 1; sfx('snip'); } else { g.miss++; g.flash = 1; sfx('buzz'); } };
        if (act) { for (const k of IN.tap) if (k === 'L' || k === 'R') press(k); }
        else if (near && off > 0 && g.last !== nb && p > .15) { g.last = nb; g.hits++; g.swing[side] = 1; }
        g.swing.L = Math.max(0, g.swing.L - dt * 2.5); g.swing.R = Math.max(0, g.swing.R - dt * 2.5); g.flash = Math.max(0, g.flash - dt * 3);
        return `${g.hits} clean cuts, ${g.miss} slips` + (g.hits >= 16 ? '. Sixteen: the shop is done for the day.' : p < .15 ? '. No power: the arms will not answer.' : '');
      },
      draw(d, g, p) {
        S.bg(cast.barber === 'op' ? 'barber/clean' : 'barber/empty');
        const [cx, cy, rx, ry] = [50, 92, 37, 55];
        S.plate('barbers', [cx - rx, cy - ry, rx * 2, ry * 2], { crop: [40, 0, 164, 240], tone: ['#26331d', '#dfe4a6'], keep: .05, res: 90, clip: c => c.ellipse(cx, cy, rx, ry, 0, 0, 7) });
        const sL = Math.sin(g.swing.L * Math.PI), sR = Math.sin(g.swing.R * Math.PI);
        const rot = ([x, y], [px, py], a) => [px + (x - px) * Math.cos(a) - (y - py) * Math.sin(a), py + (x - px) * Math.sin(a) + (y - py) * Math.cos(a)];
        const a1 = .18 * sR, e = rot([333, 66], [287, 88], a1), b1 = -.14 * sL, f = rot([225, 35], [287, 88], b1);
        part(d, 'lever', { rot: .1 * (sR - sL) }); part(d, 'r1', { rot: a1 }); part(d, 'r2', { dx: e[0] - 333, dy: e[1] - 66, rot: a1 - .5 * sR });
        part(d, 'l1', { rot: b1 }); part(d, 'l2', { dx: f[0] - 225, dy: f[1] - 35, rot: b1 + .6 * sL }); S.joint(287, 88, 2.6);
        drawActor(d, cast.barber, (sR - sL) * 1.5, Math.max(sL, sR) + .2);
        const b = g.beat || { side: 'L', ph: 0 }, gx = 548, gy = 121, a = -Math.PI / 2 + (b.side === 'L' ? -1 : 1) * Math.sin(Math.PI * Math.min(1, b.ph * 2)) * 1.1;
        ctx.save(); ctx.strokeStyle = S.RED; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(gx + 7 * Math.cos(a), gy + 7 * Math.sin(a)); ctx.stroke(); ctx.restore();
        doodle('hand', b.side === 'L' ? 200 : 330, 150, 36, { flip: b.side === 'R', a: .4 + .6 * (b.ph < .22 || b.ph > .78), c: S.RED });
        if (g.flash) { ctx.save(); ctx.globalAlpha = g.flash * .35; ctx.fillStyle = S.RED; ctx.fillRect(0, 0, 586, 341); ctx.restore(); }
      }
    },
    'phono-cinema': {
      init() { return { env: [], answer: null, talks: 0, who: 'dancers1914', since: 0, plateT: 0 }; },
      update(g, p, dt, act) {
        const speaking = act ? IN.speak : (T.t % 7) < 2.4;
        if (speaking) { g.env.push(voiceEnv(T.t)); g.answer = null; }
        else if (g.env.length && !g.answer) { g.answer = { i: 0, env: g.env }; g.env = []; g.talks++; }
        g.v = speaking ? voiceEnv(T.t) : 0; g.a = 0;
        if (g.answer) { g.a = g.answer.env[g.answer.i++] || 0; if (g.answer.i >= g.answer.env.length) g.answer = null; }
        if (g.a > 0 && p > .1) g.plateT += dt;
        if (!act && g.talks && g.talks !== g.lastTalk) { g.lastTalk = g.talks; g.who = ANSWERERS[g.talks % ANSWERERS.length][0]; }
        return `${g.talks} answers. Answering: ${ANSWERERS.find(a => a[0] === g.who)[1]}` + (p < .1 ? '. No power: the projector is dark.' : '');
      },
      draw(d, g, p) {
        S.bg('phono-cinema/clean');
        const on = p > .1 && (g.a > 0 || g.answer), crop = { dancers1914: [88, 0, 143, 240], lecturer: [100, 0, 143, 240], hosedrill: [80, 0, 143, 240], shadowplay: [90, 0, 143, 240], barbers: [40, 0, 143, 240] }[g.who];
        if (on) S.plate(g.who, [752, 0, 206, 345], { crop, tone: ['#3b2f22', '#f6edc9'], keep: .08, contrast: 1.15, res: 110, a: .4 + .6 * Math.min(1, g.a * 2 + .3) });
        else part(d, 'woman', { a: p > .1 ? 1 : .35 });
        ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = p > .1 ? .08 + .14 * (on ? 1 : .3) : 0; ctx.fillStyle = '#E8D59A';
        ctx.beginPath(); ctx.moveTo(548, 88); ctx.lineTo(752, 0); ctx.lineTo(752, 345); ctx.closePath(); ctx.fill(); ctx.restore();
        part(d, 'head', { rot: -.05 * g.v }); part(d, 'receiver', { dx: 1.4 * g.v * Math.sin(T.t * 90), dy: -.9 * g.v });
        part(d, 'horn', { sc: 1 + .05 * g.v + .08 * g.a });
        doodle('microphone', 610, 200, 46, { a: .3 + .7 * g.v, c: S.RED, rot: .3 });
        doodle('television', 900, 380, 60, { a: .5, c: S.INK });
      }
    },
    'air-cabs': {
      init() { return { y: 0, vy: 0, stamina: 1, state: 'flying', carrying: false, fares: 0, hand: [420, 160], scroll: 0 }; },
      update(g, p, dt, act) {
        const target = act ? (IN.down ? IN.card[1] - 70 : IN.keys.ArrowUp ? g.y - 40 : IN.keys.ArrowDown ? g.y + 40 : g.y) : 60 + 60 * Math.sin(T.t * .6);
        const climb = target < g.y - 2 && g.state !== 'tired';
        g.y = clamp(climb ? g.y - 70 * dt * (.4 + p) : g.y + clamp(target - g.y, 0, 40 * dt) + 3 * dt, -10, 150);
        g.stamina = clamp(g.stamina + (climb ? -.3 : .1 + .3 * p) * dt);
        g.state = g.stamina <= .01 ? 'tired' : g.state === 'tired' && g.stamina < .35 ? 'tired' : g.y >= 149 ? 'landed' : climb ? 'climbing' : 'gliding';
        g.scroll += dt * 24;
        const cab = [185 + 40, 70 + g.y], hx = g.hand;
        if (!g.carrying && Math.hypot(cab[0] - hx[0] + 20 * Math.sin(g.scroll * .1), cab[1] - hx[1]) < 55) { g.carrying = true; sfx('blip', 880); }
        if (g.carrying && g.y > 60 && g.y < 110) { g.carrying = false; g.fares++; sfx('chime'); g.hand = [380 + rand() * 120, 40 + rand() * 120]; }
        return `${g.fares} fares. The cab is ${g.state}${g.carrying ? ', with a passenger: set them down by the star' : ''}. Wings ${Math.round(g.stamina * 100)}%`;
      },
      draw(d, g, p) {
        const f = Math.sin(T.t * 2 * Math.PI * (g.state === 'tired' ? .4 : 1.05)) * (g.state === 'landed' ? 0 : 1), py = g.y;
        S.bg('air-cabs/clean');
        const sh = Math.sin(g.scroll * .02);
        part(d, 'small1', { dx: (g.scroll * .7) % 600 - 40 }); part(d, 'small2', { dx: (g.scroll * .4) % 600 - 100 }); part(d, 'blimp', { dx: 20 * sh });
        part(d, 'plane', { dx: -((g.scroll * 1.2) % 700) + 100 });
        part(d, 'city', { dx: -6 * sh, dy: py * .05 });
        doodle('star', 425, 92, 28, { c: S.RED, a: g.carrying ? .5 + .5 * Math.sin(T.t * 8) : .45 });
        if (!g.carrying) doodle('hand', g.hand[0] + 20 * Math.sin(g.scroll * .1), g.hand[1], 30, { c: S.RED, rot: .3 * Math.sin(T.t * 5) });
        part(d, 'wingL', { dy: py, rot: -.13 * f }); part(d, 'wingR', { dy: py, rot: .11 * f }); part(d, 'cab', { dy: py });
        if (g.carrying) doodle('hat', 190, 40 + py, 22, { c: S.RED });
        part(d, 'near', { dx: 8 * sh, dy: py * .1 });
        doodle('cloud', 520 - (g.scroll * .3) % 600, 30, 60, { c: '#8b8578', a: .8 }); if (g.state === 'tired') doodle('rain', 200, 110 + py, 50, { c: '#4F6A88', a: .6 });
        ctx.fillStyle = S.INK; ctx.fillRect(10, 320, 80, 6); ctx.fillStyle = g.state === 'tired' ? S.RED : S.BRASS; ctx.fillRect(10, 320, 80 * g.stamina, 6);
      }
    },
    firemen: {
      init() { return { zones: [{ x: 820, y: 120, f: 1 }, { x: 900, y: 320, f: 1 }, { x: 760, y: 260, f: 1 }], aim: -.2, drops: [], pos: 0, state: 'hover' }; },
      update(g, p, dt, act) {
        let want = g.aim;
        if (act) { if (IN.down) want = Math.atan2(IN.card[1] - 221, IN.card[0] - 627); if (IN.keys.ArrowUp) want = g.aim - dt * 2; if (IN.keys.ArrowDown) want = g.aim + dt * 2; }
        else want = -.2 + .3 * Math.sin(T.t * .8);
        g.aim += (clamp(want, -.7, .5) - g.aim) * Math.min(1, dt * 6);
        const press = p;
        if (press > .2) for (let i = 0; i < 4; i++) g.drops.push({ x: 627, y: 221, vx: Math.cos(g.aim + (rand() - .5) * .06) * 700 * press, vy: Math.sin(g.aim + (rand() - .5) * .06) * 700 * press, t: 0 });
        g.drops.forEach(o => { o.vy += 520 * dt; o.x += o.vx * dt; o.y += o.vy * dt; o.t += dt; g.zones.forEach(z => { if (Math.hypot(o.x - z.x, o.y - z.y) < 60 && z.f > 0) { z.f = Math.max(0, z.f - .012); o.t = 9; } }); });
        g.drops = g.drops.filter(o => o.t < 1.2 && o.x < 980);
        g.zones.forEach(z => z.f = Math.min(1, z.f + dt * .015 * (z.f > 0)));
        g.state = press < .35 ? 'refuse' : 'advance';
        g.pos += ((g.state === 'advance' ? 1 : -1) * 30 - g.pos) * Math.min(1, dt * 1.5);
        const left = g.zones.reduce((a, z) => a + z.f, 0) / 3;
        return `Fire ${Math.round(left * 100)}%. Flyers: ${g.state === 'refuse' ? 'they refuse to go near the fire without water' : 'advancing on the water'}` + (left < .08 ? '. The fire is out.' : '');
      },
      draw(d, g, p) {
        S.bg('firemen/clean');
        const fire = g.zones.reduce((a, z) => a + z.f, 0) / 3, FIRE = [[735, 0], [960, 0], [960, 558], [905, 558], [878, 420], [860, 300], [795, 250], [765, 300], [700, 282], [688, 232], [758, 222], [800, 196], [762, 150], [742, 40]];
        S.softPlate('wildfire', [690, -10, 290, 580], FIRE, 14, { crop: [40, 0, 240, 240], blend: 'screen', a: .9 * fire, size: [960, 558], res: 120 });
        S.softPlate('smoke', [-20, 150, 440, 330], [[0, 235], [120, 225], [250, 245], [385, 300], [385, 430], [250, 440], [0, 430]], 30, { crop: [0, 0, 320, 240], tone: ['#000000', '#efe8d2'], contrast: 1.5, lift: -.2, blend: 'screen', a: .5, size: [960, 558], res: 120 });
        if (fire < .5) { ctx.save(); ctx.globalAlpha = (.5 - fire) * 1.2; ctx.fillStyle = '#8f9a7a'; ctx.globalCompositeOperation = 'color'; ctx.beginPath(); FIRE.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.fill(); ctx.restore(); }
        part(d, 'pair', { dx: g.pos + 4 * Math.sin(T.t * 1.3), dy: 5 * Math.sin(T.t * 1.7), rot: g.state === 'refuse' ? -.08 : .04 });
        part(d, 'flyer', { dx: g.pos * .4, dy: 4 * Math.sin(T.t * 1.1 + 1) });
        ctx.save(); ctx.strokeStyle = 'rgba(236,244,250,.8)'; ctx.lineCap = 'round';
        g.drops.forEach(o => { ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(o.x, o.y); ctx.lineTo(o.x - o.vx * .015, o.y - o.vy * .015); ctx.stroke(); }); ctx.restore();
        doodle('garden hose', 420, 470, 70, { a: .6 }); doodle('fire hydrant', 150, 470, 60, { a: .6, c: S.RED });
        if (g.state === 'refuse') doodle('hand', 300 + g.pos, 70, 34, { c: S.RED, a: .8 });
      }
    },
    skates: {
      init() { return { dist: 0, speed: 0, lastSide: null, lastT: -9, fall: 0, stride: 0, falls: 0 }; },
      update(g, p, dt, act) {
        const taps = act ? IN.tap.filter(k => k === 'L' || k === 'R') : ((T.t % .62) < dt ? [Math.floor(T.t / .62) % 2 ? 'R' : 'L'] : []);
        for (const k of taps) {
          if (g.fall > 0) continue;
          const gap = T.t - g.lastT;
          if (k === g.lastSide || gap < .24) { g.fall = 1.4; g.speed = 0; g.falls++; sfx('bonk', 120); }
          else { g.speed = Math.min(6, g.speed + (gap < 1 ? 1.4 : .6)); g.stride = k === 'L' ? 1 : -1; sfx('click'); }
          g.lastSide = k; g.lastT = T.t;
        }
        g.fall = Math.max(0, g.fall - dt); g.speed = Math.max(0, g.speed - dt * 1.4 * (p > .1 ? .7 : 1.4));
        g.dist += g.speed * dt; g.stride *= Math.pow(.2, dt);
        return `${g.dist.toFixed(0)} of 100 metres, ${g.falls} falls` + (g.fall ? '. Down: the drawing is swapped for the fallen one.' : g.dist >= 100 ? '. A hundred metres.' : '');
      },
      draw(d, g, p) {
        S.bg('skates/clean');
        const gx = 6 * Math.sin(g.dist * .4), st = Math.sin(T.t * 7) * Math.min(1, g.speed / 3), run = g.dist * 9;
        part(d, 'trees', { dx: -(run * .15 % 40) }); part(d, 'lamp1', { dx: -(run % 420) + (run % 420 > 300 ? 420 : 0) });
        part(d, 'lady', { dx: -(run * 1.3 % 520) + 40, rot: .04 * Math.sin(T.t * 4) });
        const fx = -(run * 1.1 % 640) + 60; part(d, 'hat', { dx: fx }); part(d, 'fallenLegs', { dx: fx }); part(d, 'fallen', { dx: fx });
        if (g.fall > 0) {   // drawing substitution: the couple's drawing is replaced by the fallen man's, then back
          ctx.save(); ctx.globalAlpha = .35; part(d, 'couple', { dx: gx, dy: 30, rot: .5 }); ctx.restore();
          part(d, 'fallen', { dx: gx - 160, dy: 120 }); part(d, 'fallenLegs', { dx: gx - 160, dy: 120 });
          doodle('star', 330 + gx, 150, 26, { c: S.RED, rot: T.t * 4 });
        } else {
          part(d, 'legsW', { dx: gx, rot: .26 * st }); part(d, 'legsM', { dx: gx, rot: -.24 * st }); part(d, 'couple', { dx: gx, dy: -2 * Math.abs(st), rot: .02 * st });
        }
        part(d, 'lamp2');
        doodle('skateboard', 330 + gx, 330, 60, { a: .5 + .5 * Math.min(1, g.speed / 3) }); doodle('wheel', 120, 300, 30, { rot: g.dist, a: .5 });
      }
    }
  };
  const ANSWERERS = [['dancers1914', 'dancers, 1914'], ['lecturer', 'a lecturer'], ['barbers', 'a barber, 1959'], ['hosedrill', 'a hose crew, 1947'], ['shadowplay', 'a shadow play']];
  const mirror = document.createElement('canvas');
  const voiceEnv = t => { const u = t * 4.2; return Math.pow(Math.max(0, Math.min(1, Math.sin(Math.PI * (u % 1)) * 1.6)), .7) * (.6 + .4 * (Math.sin(2 * Math.PI * .31 * t) > -.6)); };

  // ---------------------------------------------------------------- the town: frame, line, streets, camera
  const cam = { x: 0, y: CH / 2 - 20, z: 1 };
  const PX = H / 430;   // world units to pixels at zoom 1
  function view() { const k = PX * cam.z; ctx.setTransform(k, 0, 0, k, W / 2 - cam.x * k, H / 2 - cam.y * k); }
  function drawTown(status) {
    S.screen(); ctx.fillStyle = S.TABLE; ctx.fillRect(0, 0, W, H);
    view();
    const k = PX * cam.z, x0 = cam.x - W / 2 / k, x1 = cam.x + W / 2 / k;
    // the line: from the school's machine, over every card, down into each machine
    const feedW = D.map(d => toWorld(d, d.feed[0], d.feed[1]));
    const line = [[feedW[0][0], feedW[0][1]], [feedW[0][0], TOP + 10]];
    D.forEach((d, i) => { if (i) line.push([d.x - GAP / 2, TOP + 4], [feedW[i][0], TOP + 14]); });
    line.push([WORLD_W + 40, TOP + 8]);
    wobbly(line, { lw: 2.2, boil: 1.2 });
    D.forEach((d, i) => { if (i) wobbly([[feedW[i][0], TOP + 14], [feedW[i][0], Math.max(TOP + 14, feedW[i][1])]], { lw: 1.6, c: '#5a4c40' }); });
    // the poles in the streets are streetlight doodles
    D.forEach((d, i) => { if (i) doodle('streetlight', d.x - GAP / 2, TOP + 66, 120, { c: '#5a4c40', lw: 3 }); });
    // power pulses along the line
    let acc = 0; const segs = []; for (let i = 1; i < line.length; i++) { const L = Math.hypot(line[i][0] - line[i - 1][0], line[i][1] - line[i - 1][1]); segs.push([acc, L, line[i - 1], line[i]]); acc += L; }
    for (let n = 0; n < 60; n++) { const dd = (P.turns * 140 + n * acc / 60) % acc, pw = powerAt(dd); if (pw < .05) continue;
      const sg = segs.find(s => dd >= s[0] && dd < s[0] + s[1]); if (!sg) continue; const u = (dd - sg[0]) / sg[1];
      const x = lerp(sg[2][0], sg[3][0], u), y = lerp(sg[2][1], sg[3][1], u); if (x < x0 - 20 || x > x1 + 20) continue;
      ctx.fillStyle = `rgba(180,74,60,${pw})`; ctx.beginPath(); ctx.arc(x, y, 3.2, 0, 7); ctx.fill(); }
    // each card as a postcard, with its game inside
    D.forEach((d, i) => {
      if (d.x + d.w < x0 - 10 || d.x > x1 + 10) return;
      ctx.fillStyle = 'rgba(43,35,32,.35)'; ctx.fillRect(d.x + 5, 5, d.w, CH); ctx.fillStyle = S.PAPER; ctx.fillRect(d.x - 8, -8, d.w + 16, CH + 30);
      const dist = D.slice(0, i + 1).reduce((a, q, j) => a + (j ? q.x - D[j - 1].x : 0), 0) + 120, pw = powerAt(dist);
      inCard(d, () => DIST[d.id].draw(d, G[d.id], pw));
      ctx.strokeStyle = S.INK; ctx.lineWidth = 1.2; ctx.strokeRect(d.x, 0, d.w, CH);
      ctx.fillStyle = S.INK; ctx.font = '15px "IM Fell English SC", Georgia, serif'; ctx.textAlign = 'left'; ctx.fillText(d.title, d.x + 2, CH + 17);
      ctx.fillStyle = '#6E5F4F'; ctx.font = '11px "IM Fell English", Georgia, serif'; ctx.textAlign = 'right'; ctx.fillText(d.op, d.x + d.w - 2, CH + 17);
    });
    doodle('clock', cam.x + (W / 2 / k) - 40, TOP - 10 + 20, 40, { c: '#5a4c40', a: .7 });
    S.grain(.12);
    if (status) { S.screen(); ctx.font = '17px "IM Fell English", Georgia, serif'; ctx.textAlign = 'center'; const w = ctx.measureText(status).width + 24;
      ctx.fillStyle = 'rgba(243,236,216,.92)'; ctx.fillRect(W / 2 - w / 2, 10, w, 28); ctx.fillStyle = S.INK; ctx.fillText(status, W / 2, 29); }
  }

  // ---------------------------------------------------------------- sound for play (the film's sound is synthesised offline)
  let AC = null; const sfx = (kind, f) => {
    if (FILM || !AC) return; const t = AC.currentTime, o = AC.createOscillator(), g = AC.createGain(); o.connect(g); g.connect(AC.destination);
    const spec = { blip: ['sine', f || 700, .08, .12], bonk: ['triangle', f || 160, .2, .25], snip: ['square', 2400, .04, .05], buzz: ['sawtooth', 90, .2, .08], click: ['square', 1300, .02, .06], chime: ['sine', 1046, .5, .15] }[kind];
    o.type = spec[0]; o.frequency.setValueAtTime(spec[1], t); if (kind === 'bonk') o.frequency.exponentialRampToValueAtTime(spec[1] * .5, t + spec[2]);
    g.gain.setValueAtTime(spec[3], t); g.gain.exponentialRampToValueAtTime(.0001, t + spec[2]); o.start(t); o.stop(t + spec[2] + .02);
  };
  let ratchetPhase = 0;

  // ---------------------------------------------------------------- one step of the world
  let focus = ONLY ? byId[ONLY] : null, statusText = '';
  function step(dt, scriptIn) {
    T.t += dt; T.dt = dt;
    if (scriptIn) Object.assign(IN, scriptIn);
    // the crank: from the dial (or the script); a little inertia
    P.omega += ((IN.crank || 0) - P.omega) * Math.min(1, dt * 4); P.turns += P.omega * dt;
    P.power = clamp(P.omega / .8); P.hist.push(P.power); if (P.hist.length > 24 * 40) P.hist.shift();
    if (!FILM && AC && Math.floor(P.turns * 6) !== ratchetPhase) { ratchetPhase = Math.floor(P.turns * 6); sfx('click'); }
    let status = '';
    D.forEach((d, i) => {
      const dist = D.slice(0, i + 1).reduce((a, q, j) => a + (j ? q.x - D[j - 1].x : 0), 0) + 120, pw = powerAt(dist);
      if (focus === d && IN.wx != null) IN.card = toCard(d, IN.wx, IN.wy);
      const s = DIST[d.id].update(G[d.id], pw, dt, focus === d && !scriptIn);
      if (focus === d || (!focus && nearest() === d)) status = s;
    });
    IN.tap = [];
    statusText = status;
  }
  const nearest = () => D.reduce((a, d) => Math.abs(d.x + d.w / 2 - cam.x) < Math.abs(a.x + a.w / 2 - cam.x) ? d : a, D[0]);

  // ---------------------------------------------------------------- the film: a script of camera and inputs
  const FDUR = 96, SEG = 11.2;
  const film = {
    camera(t) {
      if (t < 6) return { x: D[0].x + D[0].w / 2, y: 120, z: lerp(.4, 1.02, S.ease(S.seg(t, 0, 5.5))) };
      const i = Math.min(D.length - 1, Math.floor((t - 6) / SEG)), u = (t - 6 - i * SEG) / SEG;
      const a = D[i], b = D[Math.min(D.length - 1, i + 1)], m = S.ease(S.seg(u, .78, 1));
      if (t > 6 + D.length * SEG) { const v = S.ease(S.seg(t, 6 + D.length * SEG, FDUR - 3)); return { x: lerp(D[6].x + D[6].w / 2, WORLD_W / 2, v), y: lerp(CH / 2 - 20, CH / 2 - 60, v), z: lerp(1.02, .15, v) }; }
      return { x: lerp(a.x + a.w / 2, b.x + b.w / 2, m), y: CH / 2 - 20, z: 1.02 + .1 * Math.sin(Math.PI * Math.min(1, u * 1.3)) };
    },
    input(t) { const cr = t < 2 ? 0 : t > FDUR - 6 ? .2 : 1.1; return { crank: cr }; },
    recast(t) {   // the JibJab moment: in the school, the maid and then the lever man take the crank; same turn, new cast
      cast.school = t > 9.5 && t < 12 ? 'maid' : t >= 12 && t < 14.5 ? 'op' : 'boy';
      cast.scrubber = t > 19 && t < 22 ? 'boy' : 'maid';
      cast.barber = t > 30 && t < 33 ? 'maid' : 'op';
    },
    caption(t) {
      const i = Math.floor((t - 6) / SEG); if (t < 6) return 'En l’an 2000: the town that runs on one crank';
      if (t > 9.5 && t < 14.5) return 'Recast: the same turn of the handle, a different hand on it';
      if (i >= 0 && i < 7) return D[i].title + ' · ' + D[i].op;
      return 'One line, seven machines, one boy turning';
    }
  };

  // ---------------------------------------------------------------- run
  S.ready.then(() => {
    D.forEach(d => G[d.id] = DIST[d.id].init());
    if (FILM) {
      let done = -1;
      window.SHORT = { id: 'world', dur: FDUR, fps: 24, poster: 40, ready: Promise.resolve(), cues: filmCues(),
        frame: async i => {
          while (done < i) { done++; const t = done / 24; film.recast(t); step(1 / 24, film.input(t)); }
          const t = i / 24; Object.assign(cam, film.camera(t));
          // plates are seeked to the frame's time so the film is the same every render
          await Promise.all(PLATES.map(k => S.seek(S.vid[k], (t * .9) % Math.max(.1, S.vid[k].duration - .1))));
          drawTown(film.caption(t));
          S.card([['En l’an 2000', 20, 'sc dim'], ['The Town', 58, 'sc'], ['seven cards, one crank', 22]], 1 - S.seg(t, 2.2, 3.2));
          S.card([['The Town', 34, 'sc'], ['The seven cards of the series as one world, joined by a drawn line.', 18], ['Doodles: Quick, Draw! (Google Creative Lab, CC BY 4.0), chosen by Secondhand Motion', 16, 'dim'],
            ['Archive: the cineosis-lab shot library · Cards: En l’an 2000, about 1910', 16, 'dim'], ['Every district is a game: shorts/world.html', 16, 'dim']], S.seg(t, FDUR - 3.2, FDUR - 2.4));
          return S.cv.toDataURL('image/jpeg', .9);
        } };
      return;
    }
    // play
    PLATES.forEach(k => { const v = S.vid[k]; v.loop = true; v.play().catch(() => {}); });
    const cv = S.cv;
    const toWorldPt = e => { const r = cv.getBoundingClientRect(), sx = (e.clientX - r.left) / r.width * W, sy = (e.clientY - r.top) / r.height * H, k = PX * cam.z;
      return [(sx - W / 2) / k + cam.x, (sy - H / 2) / k + cam.y]; };
    cv.addEventListener('pointerdown', e => { IN.down = true; [IN.wx, IN.wy] = toWorldPt(e); cv.setPointerCapture(e.pointerId); wake();
      if (!focus) { const d = D.find(d => IN.wx > d.x && IN.wx < d.x + d.w); if (d) setFocus(d); } });
    cv.addEventListener('pointermove', e => { [IN.wx, IN.wy] = toWorldPt(e); });
    cv.addEventListener('pointerup', () => { IN.down = false; });
    addEventListener('keydown', e => { IN.keys[e.key] = true; wake();
      if (e.key === 'f' || e.key === 'F') IN.tap.push('L'); if (e.key === 'j' || e.key === 'J') IN.tap.push('R');
      if (e.key === 'ArrowLeft' && focus && focus.id === 'skates') IN.tap.push('L'); if (e.key === 'ArrowRight' && focus && focus.id === 'skates') IN.tap.push('R');
      if (e.key === ' ') { IN.speak = true; e.preventDefault(); } });
    addEventListener('keyup', e => { IN.keys[e.key] = false; if (e.key === ' ') IN.speak = false; });
    UI.init({ D, cast, ACTORS, setFocus, IN, ANSWERERS, G, getFocus: () => focus, wake });
    if (focus) setFocus(focus);
    let last = performance.now();
    const loop = now => { const dt = Math.min(.05, (now - last) / 1000); last = now; step(dt);
      const tgt = focus ? { x: focus.x + focus.w / 2, y: CH / 2 + 4, z: 1.18 } : { x: cam.tx == null ? D[0].x + D[0].w / 2 : cam.tx, y: CH / 2 - 20, z: .95 };
      cam.x += (tgt.x - cam.x) * Math.min(1, dt * 4); cam.y += (tgt.y - cam.y) * Math.min(1, dt * 4); cam.z += (tgt.z - cam.z) * Math.min(1, dt * 3);
      drawTown(statusText); UI.update(statusText, P); requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  });
  function setFocus(d) { focus = d; if (d) cam.tx = d.x + d.w / 2; UI.focus && UI.focus(d); }
  function wake() { if (!AC) { try { AC = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} } }
  window.TOWN = { get status() { return statusText; }, T, D, setFocus, cam, IN, G, cast, ACTORS, perform, step: dt => step(dt), get focus() { return focus; }, pan: dx => { focus = null; cam.tx = clamp((cam.tx == null ? cam.x : cam.tx) + dx, D[0].x + D[0].w / 2, D[6].x + D[6].w / 2); } };

  function filmCues() {
    const c = [{ t: .3, k: 'chime', notes: [60, 64, 67, 72], step: .3, a: .12 }, { t: 2, k: 'ratchet', d: FDUR - 8, rate: 7.2, a: .1, f: 1300 }, { t: 2, k: 'hum', d: FDUR - 6, f: 55, a: .05, att: 2, rel: 2 },
      { t: FDUR - 3, k: 'chime', notes: [72, 67, 64, 60], step: .3, a: .14 }];
    D.forEach((d, i) => { const t0 = 6 + i * SEG;
      c.push({ t: t0 + .2, k: 'whoosh', d: .8, f: 700, a: .2 });
      if (d.id === 'scrubber') c.push({ t: t0, k: 'bed', d: SEG, lp: 2200, pulse: .8, a: .08 });
      if (d.id === 'barber') for (let s = t0; s < t0 + SEG; s += 1 / 1.2) c.push({ t: s, k: 'click', a: .2, f: 4800 });
      if (d.id === 'phono-cinema') for (let s = t0; s < t0 + SEG; s += 7) c.push({ t: s - (s % 7) + (7 - t0 % 7) % 7, k: 'babble', d: 2.4, f0: 118, rate: 4.2, a: .2 });
      if (d.id === 'air-cabs') c.push({ t: t0, k: 'flap', d: SEG, rate: 2.1, a: .14 }, { t: t0, k: 'bed', d: SEG, lp: 500, a: .12 });
      if (d.id === 'firemen') c.push({ t: t0, k: 'crackle', d: SEG, a: .14 }, { t: t0, k: 'bed', d: SEG, lp: 6000, a: .06 });
      if (d.id === 'skates') for (let s = t0; s < t0 + SEG; s += .62) c.push({ t: s, k: 'click', a: .15, f: 900 });
      if (d.id === 'school') for (let s = t0; s < t0 + SEG; s += 1 / 1.1) c.push({ t: s, k: 'tone', f: 660, d: .1, a: .05 });
    });
    c.push({ t: 9.5, k: 'bonk', f: 300, a: .3 }, { t: 12, k: 'bonk', f: 260, a: .3 }, { t: 14.5, k: 'bonk', f: 220, a: .3 });
    return c;
  }
})();
