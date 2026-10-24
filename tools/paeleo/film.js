/* PAELEO-00 · The threshold. The film's score: shots, prompts, camera, text, and the sound cues they leave behind.
   Loaded by render.html after machine.js and stage.js. FILM.draw(i) must be called for i = 0, 1, 2 ... in order (the puppets have springs).
   The dog is never keyed. Its whole performance comes from Threshold.run() on the circumstances the prompts set. */
(function () {
  const W = 1280, H = 720, FPS = 24, S = Stage, M = Threshold, C = S.C;
  const lerp = S.lerp, clamp = S.clamp, ease = S.ease;
  const T0 = 18;                    // machine time 0 = film time T0 (after the lineage opening and the title)
  const TYPE = 24;                  // characters typed per second

  // ---------------------------------------------------------------- the prompts (P), and what each one changes in the world
  const PROMPTS = [
    { t: 0.4, text: 'the person stands in the doorway and calls: Come here.', set: { voice: 'call' }, then: [[1.4, { voice: 'none' }]], say: ['Come here!', true] },
    { t: 5.2, text: 'call again, and reach for it.', set: { voice: 'call', hand: 'reach' }, then: [[1.7, { voice: 'none', hand: 'none' }]], say: ['Come HERE!', true] },
    { t: 10.0, text: 'step back. sit down beside the door. say nothing.', walk: true, set: { place: 'beside', posture: 'sit' }, lag: 1.25 },
    { t: 14.6, text: 'open the door.', set: { door: 'open' } },
    { t: 20.4, text: 'offer a hand, low.', set: { hand: 'low' } },
    { t: 23.0, text: "say it softly: it's all right.", set: { voice: 'soft' }, then: [[1.9, { voice: 'none' }]], say: ["it's all right.", false] },
    { t: 37.3, text: 'come in.', set: { voice: 'soft' }, then: [[1.2, { voice: 'none' }]], say: ['come in.', false] },
  ];
  const TL = [];
  for (const p of PROMPTS) { p.done = p.t + p.text.length / TYPE + .35; p.fx = p.done + (p.lag || 0); TL.push([p.fx, p.set]); for (const [dt, w] of p.then || []) TL.push([p.fx + dt, w]); }
  TL.sort((a, b) => a[0] - b[0]);
  const RUN = M.run(TL, 44, 1 / FPS);
  const TRANS = RUN.events.filter(e => e.e === 'transition');
  const DUR = 82, N = DUR * FPS;

  // ---------------------------------------------------------------- state
  const dogA = new S.DogAnim(), perA = new S.PersonAnim();
  const SFX = [];
  const cue = (t, k, o) => SFX.push(Object.assign({ t: +t.toFixed(3), k }, o || {}));
  let lastSteps = 0, lastPSteps = 0, lastThumps = 0, lastState = 'lie_down', camS = null;

  // cues that follow straight from the score
  for (const p of PROMPTS) {
    for (let i = 0; i < p.text.length; i++) if (p.text[i] !== ' ' || i % 3 === 0) cue(T0 + p.t + i / TYPE, 'key', { n: i });
    cue(T0 + p.done - .2, 'return');
    if (p.say) cue(T0 + p.fx, p.say[1] ? 'call' : 'soft', { text: p.say[0] });
    if (p.set.door === 'open') cue(T0 + p.fx, 'creak');
    if (p.set.posture === 'sit') cue(T0 + p.fx + .65, 'sit');
    cue(T0 + p.fx + .15, 'flick');
  }
  for (const e of TRANS) cue(T0 + e.t, 'state', { to: e.to, from: e.from });
  [[0, 'page'], [4.6, 'unfold'], [11.3, 'pulse'], [14.5, 'title'], [T0 + 41.2, 'reply'], [64, 'scales'], [71.5, 'lockup']].forEach(([t, k]) => cue(t, k));

  // ---------------------------------------------------------------- helpers
  const at = (T, a, b) => clamp((T - a) / (b - a));
  // camera keys in machine time: [from, x, zoom, cut]. A cut snaps; otherwise the camera eases toward the key. The approach tracks the dog.
  const CAM = [[-99, 1.5, 1.15], [0, 1.55, 1.22], [2.4, 1.8, 1.2], [7.4, 3.45, 2.15, 1], [10.2, 1.5, 1.2, 1], [14.95, 1.85, 1.25], [19.2, 1.45, 1.14], [21, 1.5, 1.14]];
  function camAt(tau, dogX) {
    let c = CAM[0]; for (const k of CAM) if (tau >= k[0]) c = k;
    let x = c[1], z = c[2];
    if (tau > 25.5) { const k = ease(at(tau, 25.5, 33)); x = lerp(x, Math.min(1.6, (dogX + M.PERSON_X.beside) / 2 + .3), k); z = lerp(z, 1.55, k); }
    if (tau > 34) { const k = ease(at(tau, 34, 38)); x = lerp(x, -.35, k); z = lerp(z, 1.85, k); }
    return [x, z, c[3] && tau - c[0] < 1 / FPS + 1e-6 ? 1 : 0];
  }
  function smoothCam(target) { if (!camS || target[2]) camS = target.slice(); camS[0] += (target[0] - camS[0]) * .05; camS[1] += (target[1] - camS[1]) * .05; return { x: camS[0], y: 0, zoom: camS[1] }; }
  function kicker(ctx, n, title, sub, a) {
    if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(20,17,13,.78)'; ctx.font = '600 15px "JetBrains Mono"';
    const w1 = ctx.measureText(n).width; ctx.font = '900 52px "Big Shoulders Display"'; const w = Math.max(w1, ctx.measureText(title).width) + 40;
    ctx.fillRect(28, 26, w, 100); ctx.fillStyle = C.paper; ctx.fillText(title, 46, 108);
    ctx.font = '600 18px "JetBrains Mono"'; ctx.fillStyle = '#ff7a6b'; ctx.fillText(n, 46, 56); ctx.restore();
  }
  function peoChips(ctx, lit, a) {   // P / E / O, the one that is happening now lit
    if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
    const L = [['P', 'prompt'], ['E', 'ekphrasis'], ['O', 'operation']];
    L.forEach(([k, w], i) => { const x = 28 + i * 150, on = lit[i];
      ctx.fillStyle = on ? C.stamp : 'rgba(20,17,13,.7)'; ctx.fillRect(x, 26, 140, 44);
      ctx.fillStyle = on ? '#fff' : 'rgba(251,247,238,.55)'; ctx.font = '900 30px "Big Shoulders Display"'; ctx.fillText(k, x + 12, 60);
      ctx.font = '600 14px "JetBrains Mono"'; ctx.fillText(w, x + 38, 54); });
    ctx.restore();
  }
  function promptBar(ctx, text, n, caret, a, reply, dim) {
    if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(14,12,10,.86)'; ctx.fillRect(0, H - 78, W, 78);
    ctx.font = '600 27px "JetBrains Mono"'; ctx.fillStyle = reply ? '#7fe0d2' : C.stamp; ctx.fillText(reply ? '=' : '›', 34, H - 30);
    ctx.fillStyle = reply ? '#bff1e9' : C.paper; const s = text.slice(0, n); ctx.globalAlpha = a * (1 - .6 * (dim || 0)); ctx.fillText(s, 66, H - 30); ctx.globalAlpha = a;
    if (caret) { const w = ctx.measureText(s).width; ctx.fillStyle = C.paper; ctx.fillRect(68 + w, H - 52, 14, 28); }
    ctx.restore();
  }
  function paperBg(ctx, color) { ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); S.piece(ctx, [[0, 0], [W, 0], [W, H], [0, H]], color, null, 1); ctx.restore(); }
  function textC(ctx, s, x, y, font, color, align) { ctx.font = font; ctx.fillStyle = color; ctx.textAlign = align || 'left'; ctx.fillText(s, x, y); ctx.textAlign = 'left'; }

  // the caption is snipped out of the page (a paper slip), lifts off and flies to the doorway, where it becomes the door's tag
  function slip(ctx, T, K) {
    if (T > 6.5) return;
    const k = ease(at(T, 4.5, 6.3)), lift = ease(at(T, 4.2, 4.6));
    const x0 = W / 2, y0 = 512, x1 = K ? K.sx(1.3) : W * .66, y1 = K ? K.sy(2.62) - 34 : 120;
    const x = lerp(x0, x1, k), y = lerp(y0, y1, k) - 14 * lift * (1 - k), fs = lerp(34, 22, k);
    ctx.save(); ctx.globalAlpha = (T < .4 ? T / .4 : 1) * (1 - at(T, 6.36, 6.42)); ctx.translate(x, y); ctx.rotate(Math.sin(k * Math.PI) * -.06);
    ctx.font = `italic 400 ${fs}px Literata`; const w = ctx.measureText('A dog at a door.').width + 30, h = fs + 22;
    if (lift > 0) { ctx.shadowColor = `rgba(0,0,0,${.3 * lift})`; ctx.shadowBlur = 10 * lift; ctx.shadowOffsetY = 6 * lift; ctx.fillStyle = `rgba(251,247,238,${lift})`; ctx.fillRect(-w / 2, -h / 2 - fs * .3, w, h); ctx.shadowColor = 'transparent'; }
    ctx.fillStyle = C.ink; ctx.textAlign = 'center'; ctx.fillText('A dog at a door.', 0, fs * .05); ctx.restore();
  }
  const DOG_WORD = { watch: 'watching', approach: 'coming closer', retreat: 'backing away', lie_down: 'lying down', refuse: 'turning its back' };

  // the set and cast, with a world `w` and dog frame `f`, inside an optional window rect (for the page)
  function scene(ctx, cam, f, w, T, tags, rect) {
    ctx.save();
    if (rect) { ctx.beginPath(); ctx.rect(rect[0], rect[1], rect[2], rect[3]); ctx.clip(); cam = Object.assign({}, cam, { ox: rect[0], oy: rect[1] }); }
    const RW = rect ? rect[2] : W, RH = rect ? rect[3] : H;
    const doorOpen = w._door === undefined ? (w.door === 'open' ? 1 : 0) : w._door;
    const K = S.drawSet(ctx, cam, { door: doorOpen, light: .25 + .75 * doorOpen, windowLit: true }, RW, RH);
    // person
    const per = w._person;
    S.puppet(ctx, K, perA.x, 1, 1, g => S.drawPerson(g, per), .32);
    // dog
    S.puppet(ctx, K, f.x, Math.abs(dogA.p.turn) < .06 ? .06 * Math.sign(dogA.p.turn || 1) : dogA.p.turn, 1, g => S.drawDog(g, dogA.p, T), .34);
    if (f.x < .45) S.jamb(ctx, K);
    if (w._bubble) S.bubble(ctx, K, [perA.x + .05, per.sit > .5 ? .95 : 1.78], w._bubble[0], { loud: w._bubble[1], alpha: w._bubble[2] });
    for (const tg of tags || []) S.tag(ctx, K, tg.anchor, tg.at, tg.lines, tg);
    ctx.restore();
    return K;
  }

  // ---------------------------------------------------------------- one frame
  let curW = Object.assign({}, M.WORLD), doorV = 0, doorX = 0;
  function draw(i, ctx) {
    const T = i / FPS, tau = T - T0;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.clearRect(0, 0, W, H);
    // the machine frame for this moment (before T0 the dog rests, then rises when the text reaches it)
    let f;
    if (tau < 0) f = { state: T < 11.5 ? 'lie_down' : 'watch', x: 3.0, v: 0, face: 1, trust: .2 };
    else f = RUN.frames[Math.min(RUN.frames.length - 1, Math.round(tau * FPS))];
    // the person's target pose from the world
    const wd = tau < 0 ? M.WORLD : f.world;
    const pw = PROMPTS.find(p => p.walk), walking = tau >= pw.done && tau < pw.fx;
    const place = walking ? 'beside' : wd.place;
    const voiceNow = wd.voice;
    const target = { x: M.PERSON_X[place], sit: wd.posture === 'sit' ? 1 : 0, reach: wd.hand === 'reach' ? 1 : 0, low: wd.hand === 'low' ? 1 : 0, mouth: voiceNow === 'call' ? (Math.sin(T * 14) > -.2 ? .9 : .3) : voiceNow === 'soft' ? (Math.sin(T * 9) > 0 ? .4 : .1) : 0 };
    const pp = perA.update(target, 1 / FPS);
    const dp = dogA.update(f, 1 / FPS);
    // the door opens on a spring
    const dt = wd.door === 'open' ? 1 : 0; doorV += (40 * (dt - doorX) - 9 * doorV) / FPS; doorX += doorV / FPS;
    // sound cues from the puppets
    for (; lastSteps < dogA.steps.length; lastSteps++) cue(dogA.steps[lastSteps] - 1 / FPS + 0, 'paw', { x: f.x });
    for (; lastPSteps < perA.steps.length; lastPSteps++) cue(perA.steps[lastPSteps], 'step');
    for (; lastThumps < dogA.thumps.length; lastThumps++) cue(dogA.thumps[lastThumps], 'thump');
    if (tau < 0 && f.state !== lastState) { cue(T, 'rise'); } lastState = f.state;

    const say = PROMPTS.find(p => p.say && tau >= p.fx && tau < p.fx + ((p.then || [[1.4]])[0][0]) + .5);
    const bub = say ? [say.say[0], say.say[1], clamp((p => Math.min((tau - p.fx) / .12, (p.fx + p.then[0][0] + .5 - tau) / .3))(say))] : null;
    const world = { door: wd.door, _door: clamp(doorX, 0, 1.05), _person: pp, _bubble: bub };

    // ------------------------------------------------ A · IMAGETEXT: a picture with a caption on a page (0 to 5.8)
    if (T < 5.8) {
      const u = ease(at(T, 4.4, 5.8));
      paperBg(ctx, '#efe7d6');
      const r0 = [340, 120, 600, 338], rect = [lerp(r0[0], 0, u), lerp(r0[1], 0, u), lerp(r0[2], W, u), lerp(r0[3], H, u)];
      ctx.save(); ctx.globalAlpha = 1 - u; textC(ctx, '1 · text beside a picture · the page', 340, 92, '600 16px "JetBrains Mono"', '#6b5f4e');
      textC(ctx, 'IMAGETEXT', 940, 92, '900 34px "Big Shoulders Display"', C.ink, 'right'); ctx.restore();
      ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.25)'; ctx.shadowBlur = 12; ctx.shadowOffsetY = 5; ctx.fillStyle = '#fff'; ctx.fillRect(rect[0] - 10 * (1 - u), rect[1] - 10 * (1 - u), rect[2] + 20 * (1 - u), rect[3] + 20 * (1 - u)); ctx.restore();
            scene(ctx, { x: lerp(1.3, 1.5, u), y: 0, zoom: lerp(.6, 1.15, u) }, f, world, T, [], rect);
      // the caption, which is about to leave the page
      ctx.save(); ctx.globalAlpha = (1 - u) * (T < .4 ? T / .4 : 1); ctx.font = '400 15px "JetBrains Mono"'; ctx.fillStyle = '#6b5f4e'; ctx.textAlign = 'center'; ctx.fillText('fig. 1', W / 2, 548); ctx.textAlign = 'left'; ctx.restore();
      slip(ctx, T, null);
      if (T < .5) { ctx.fillStyle = `rgba(0,0,0,${1 - T / .5})`; ctx.fillRect(0, 0, W, H); }
      return;
    }

    // ------------------------------------------------ the set, full frame, from here on
    const camT = camAt(tau, f.x);
    const cam = smoothCam(camT);
    const tags = [];
    // environment text: tags pinned to the door, the person and the dog
    const tagIn = (a, b) => ease(at(T, a, b));
    const doorLines = T < 7.0 ? ['a dog at a door'] : tau < 0 ? ['threshold', 'the door is ajar'] : ['threshold', wd.door === 'open' ? 'the door is open' : 'the door is ajar'];
    const flashOf = key => { const p = [...PROMPTS].reverse().find(p => tau >= p.fx && key in p.set); return p ? clamp(1 - (tau - p.fx) / .8) : 0; };
    tags.push({ anchor: [.3, 2.08], at: [1.3, 2.62], lines: doorLines, alpha: at(T, 6.36, 6.42), size: 26, flash: flashOf('door'), rot: -.015 });
    if (T > 6.6) {
      const per = tau < 0 ? ['a person', 'standing in the doorway'] :
        [wd.posture === 'sit' ? 'person · sitting' : 'person · standing', wd.place === 'doorway' ? 'in the doorway' : 'beside the door',
          wd.voice === 'call' ? 'calling' : wd.voice === 'soft' ? 'speaking softly' : wd.hand === 'reach' ? 'reaching' : wd.hand === 'low' ? 'a hand offered, low' : 'silent'];
      tags.push({ anchor: [perA.x, pp.sit > .5 ? .95 : 1.8], at: [perA.x - .55, pp.sit > .5 ? 1.75 : 2.45], lines: per, alpha: tagIn(6.6, 7.3), size: 26, flash: Math.max(flashOf('voice'), flashOf('hand'), flashOf('posture')), rot: .012 });
    }
    if (T > 7.6) {
      let lines;
      if (T < 10.6) lines = ['a dog', 'lying on the porch'];
      else if (tau < 0) lines = ['a dog', { t: 'trust', bar: .2 }, T < 11.2 ? 'may watch, approach,' : 'may watch, approach,', 'back away, lie down,', { t: 'or refuse', c: C.stamp }];
      else lines = ['dog · ' + (f.state === 'lie_down' && f.x < .5 ? 'lying on the sill' : DOG_WORD[f.state]), { t: 'trust', bar: f.trust, barc: f.trust > .6 ? C.teal : f.trust < .25 ? C.stamp : '#c88a00' }];
      const lift = f.state === 'lie_down' || (f.state === 'refuse' && dogA.p.lie > .5) ? .75 : 1.0;
      const lastTr = TRANS.filter(e => e.t <= tau).pop();
      tags.push({ anchor: [f.x - .25 * Math.sign(dogA.p.turn || 1), lift * .62], at: [Math.min(f.x + (f.x < .8 ? .3 : .1), 4.4), lift + (tau < 0 && T > 10.6 ? .95 : f.x < .8 ? 1.25 : .55)], lines, alpha: tagIn(7.6, 8.3), size: 26, flash: lastTr ? clamp(1 - (tau - lastTr.t) / .8) : 0, rot: -.01 });
    }
    // the caption flies from the page to the door tag
    const hideT = 1 - clamp(at(T, 13.9, 14.3) - at(T, 17.7, 18.1));
    for (const tg of tags) { tg.alpha = (tg.alpha === undefined ? 1 : tg.alpha) * hideT; if (T < 14.6) tg.top = 142; }
    const K = scene(ctx, cam, f, world, T, tags);
    if (T < 6.6) slip(ctx, T, K);
    // a pulse runs down the dog's pin into the dog (the description operates)
    if (T > 11.0 && T < 11.9) { const k = ease(at(T, 11.0, 11.6)), a = [K.sx(3.0 + .1), K.sy(1.95)], b = [K.sx(3.0 - .25), K.sy(.62)];
      ctx.save(); ctx.fillStyle = C.stamp; ctx.shadowColor = C.stamp; ctx.shadowBlur = 18; ctx.beginPath(); ctx.arc(lerp(a[0], b[0], k), lerp(a[1], b[1], k), 9 * (1 - at(T, 11.6, 11.9)) + 2, 0, 7); ctx.fill(); ctx.restore(); }

    // ------------------------------------------------ kickers for B and C, the title D
    kicker(ctx, '2 · text pinned to a place · AEL', 'ENVIRONMENT TEXT', '', clamp(at(T, 6.4, 6.8) - at(T, 9.7, 10.0)));
    kicker(ctx, '3 · text the place runs on · PAELEO', 'WORLDTEXT', '', clamp(at(T, 10.1, 10.5) - at(T, 14.0, 14.4)));
    if (T > 14.3 && T < 18.6) {
      const a = clamp(at(T, 14.35, 14.9) - at(T, 17.0, 17.6));
      ctx.save(); ctx.fillStyle = `rgba(10,9,8,${.72 * a})`; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = a;
      textC(ctx, 'PAELEO-00', W / 2, 250, '600 20px "JetBrains Mono"', C.stamp, 'center');
      textC(ctx, 'THE THRESHOLD', W / 2, 352, '900 118px "Big Shoulders Display"', C.paper, 'center');
      textC(ctx, 'prompt  ·  ekphrasis  ·  operation', W / 2, 414, '600 26px "JetBrains Mono"', 'rgba(251,247,238,.8)', 'center');
      ctx.restore();
    }

    // ------------------------------------------------ E · the PEO cycle, the prompt bar
    if (tau >= -.2 && T < 64) {
      const cur = [...PROMPTS].reverse().find(p => tau >= p.t);
      let n = 0, text = '', caret = false, reply = false;
      if (cur) { n = Math.min(cur.text.length, Math.floor((tau - cur.t) * TYPE)); text = cur.text; caret = tau < cur.done + .5 && Math.floor(T * 2.5) % 2 === 0 || tau < cur.done; }
      if (tau > 41.2) { reply = true; text = 'the dog stays on the sill. the description let it choose.'; n = Math.floor((tau - 41.2) * TYPE); caret = false; }
      if (!cur && !reply) caret = Math.floor(T * 2.5) % 2 === 0;
      const lastTr = TRANS.filter(e => e.t <= tau).pop();
      const P = cur && tau < cur.done, E = cur && tau >= cur.fx && tau < cur.fx + .9, O = (lastTr && tau - lastTr.t < 1.6) || reply;
      const a = clamp(at(tau, -.2, .3)) * (1 - at(T, 62.6, 63.6));
      const dim = cur && !reply ? clamp((tau - cur.fx - 2.5) / 1.0) : 0;
      peoChips(ctx, [!!P, !!E, !!O], a); promptBar(ctx, text, n, caret, a, reply, dim);
    }

    // ------------------------------------------------ G · three scales; the lockup; credits
    if (T >= 63) {
      const a = at(T, 63, 64);
      ctx.save(); ctx.globalAlpha = a; paperBg(ctx, '#14110d'); ctx.restore();
      if (T < 71.6) {
        const g = ctx; g.save(); g.globalAlpha = clamp(at(T, 64, 64.6) - at(T, 71.0, 71.6));
        const box = (x, y, w, h, k, code, name, line, col, d) => {
          const v = ease(at(T, d, d + .9)); if (v <= 0) return;
          g.save(); g.globalAlpha *= v; g.strokeStyle = col; g.lineWidth = 3; g.strokeRect(x, y, w, h);
          g.fillStyle = col; g.fillRect(x, y - 34, g.measureText ? 0 : 0, 0);
          g.font = '900 48px "Big Shoulders Display"'; g.fillStyle = col; g.fillText(code, x + 18, y + 52);
          g.font = '600 18px "JetBrains Mono"'; g.fillStyle = col; g.fillText(k, x + 18, y + 78);
          g.font = 'italic 400 25px Literata'; g.fillStyle = 'rgba(251,247,238,.9)'; g.fillText(name, x + 18, y + 108); g.font = '400 22px Literata'; g.fillStyle = 'rgba(251,247,238,.66)'; g.fillText(line, x + 18, y + 136); g.restore(); };
        textC(g, 'ONE RESEARCH PROGRAM · THREE SCALES OF OPERATION', W / 2, 56, '600 20px "JetBrains Mono"', C.stamp, 'center');
        box(60, 80, 1160, 600, 'THE PLACE', 'AEL', 'Augmented Environments Lab', 'where situated worlds are investigated and made', '#c99a60', 64.3);
        box(120, 230, 1040, 430, 'THE LANGUAGE AND STUDIO', 'PAELEO', 'Promptable Augmented Environments Lab / Language for Ekphrastic Operations', 'where the method operates across environments, archives, games, films and agents', '#7fe0d2', 65.6);
        box(180, 390, 920, 250, 'THE METHOD', 'PEO', 'Prompt · Ekphrasis · Operation', 'how descriptions become consequential actions', C.stamp, 66.9);
        // the cycle inside PEO: intent → description → consequence → (a changed situation) → intent
        const v = ease(at(T, 68.0, 69.0)); if (v > 0) { g.save(); g.globalAlpha *= v; const cx = 880, cy = 515, r = 58;
          [['P', 'intent', -Math.PI / 2], ['E', 'description', Math.PI / 6], ['O', 'consequence', Math.PI * 5 / 6]].forEach(([k, w2, an]) => {
            const x = cx + Math.cos(an) * r, y = cy + Math.sin(an) * r; g.beginPath(); g.arc(x, y, 22, 0, 7); g.fillStyle = C.stamp; g.fill();
            g.font = '900 26px "Big Shoulders Display"'; g.fillStyle = '#fff'; g.textAlign = 'center'; g.fillText(k, x, y + 9); g.font = '600 17px "JetBrains Mono"'; g.fillStyle = 'rgba(251,247,238,.8)'; g.fillText(w2, x + (an > 1 ? -60 : an > 0 ? 40 : 0), y + (an < 0 ? -30 : 42)); g.textAlign = 'left'; });
          g.strokeStyle = 'rgba(251,247,238,.5)'; g.lineWidth = 2; g.beginPath(); g.arc(cx, cy, r, -Math.PI / 2 + .35, -Math.PI / 2 + .35 + (Math.PI * 2 - .7) * clamp(at(T, 68.2, 69.6))); g.stroke(); g.restore(); }
        g.restore();
      } else if (T < 77.4) {
        const g = ctx, a2 = clamp(at(T, 71.7, 72.3) - at(T, 76.8, 77.4)); g.save(); g.globalAlpha = a2;
        textC(g, 'PAELEO', W / 2, 330, '900 210px "Big Shoulders Display"', C.paper, 'center');
        textC(g, 'PROMPTABLE AUGMENTED ENVIRONMENTS LAB', W / 2, 392, '600 24px "JetBrains Mono"', 'rgba(251,247,238,.85)', 'center');
        textC(g, 'EKPHRASTIC OPERATIONS', W / 2, 428, '600 24px "JetBrains Mono"', C.stamp, 'center');
        g.globalAlpha = a2 * ease(at(T, 72.8, 73.6)); textC(g, 'From describing worlds to operating within them.', W / 2, 512, 'italic 400 30px Literata', 'rgba(251,247,238,.9)', 'center');
        g.restore();
      } else {
        const g = ctx, a3 = clamp(at(T, 77.5, 78.1) - at(T, 81.2, 82)); g.save(); g.globalAlpha = a3;
        textC(g, 'PAELEO-00 · THE THRESHOLD', W / 2, 200, '900 52px "Big Shoulders Display"', C.paper, 'center');
        const L = ['made with SCION 48 · State Machines',
          'the dog: watch · approach · retreat · lie down · refuse',
          'nothing it does is keyed; it follows the prompts',
          'made from code by Claude · checked by independent critics',
          'Bolas · CRASH LAB · October 2026'];
        L.forEach((s, k) => textC(g, s, W / 2, 280 + k * 58, k === 0 ? '600 26px "JetBrains Mono"' : '400 24px "JetBrains Mono"', k === 0 ? C.stamp : 'rgba(251,247,238,.8)', 'center'));
        g.restore();
      }
    }
  }
  window.FILM = { W, H, FPS, N, DUR, T0, draw, SFX, RUN, PROMPTS, TL, TRANS };
})();
