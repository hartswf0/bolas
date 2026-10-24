/* PAELEO-00 · Try it: change the circumstances and watch the dog choose. The machine and the stage are the film's own (machine.js, stage.js).
   Markup: an element with data-threshold containing canvas.stage, buttons [data-k][data-v], button[data-call], button[data-reset], and .st/.tr/.why/.log outputs. */
(() => {
  for (const root of document.querySelectorAll('[data-threshold]')) {
    const cv = root.querySelector('canvas.stage'), ctx = cv.getContext('2d'), W = 1280, H = 720, FPS = 30;
    let d, w, dog, per, door, callT, log, cam;
    const reset = () => { d = Threshold.create(); w = Object.assign({}, Threshold.WORLD); dog = new Stage.DogAnim(); per = new Stage.PersonAnim(); door = 0; callT = 0; log = []; cam = { x: 1.6, y: 0, zoom: 1.08 }; sync(); };
    const sync = () => root.querySelectorAll('button[data-k]').forEach(b => b.setAttribute('aria-pressed', String(w[b.dataset.k] === b.dataset.v)));
    root.querySelectorAll('button[data-k]').forEach(b => b.addEventListener('click', () => { w[b.dataset.k] = b.dataset.v; if (b.dataset.k === 'voice' && b.dataset.v !== 'call') callT = 0; sync(); }));
    root.querySelector('[data-call]').addEventListener('click', () => { w.voice = 'call'; callT = 1.4; sync(); });
    root.querySelector('[data-reset]').addEventListener('click', reset);
    const $ = s => root.querySelector(s);
    const WORD = { watch: 'watching', approach: 'coming closer', retreat: 'backing away', lie_down: 'lying down', refuse: 'turning its back' };
    let last = performance.now(), acc = 0, visible = true;
    new IntersectionObserver(es => { visible = es[0].isIntersecting; }).observe(cv);
    function tick(now) {
      requestAnimationFrame(tick);
      if (!visible) { last = now; return; }
      acc += Math.min(.25, (now - last) / 1000); last = now;
      while (acc >= 1 / FPS) {
        acc -= 1 / FPS;
        if (callT > 0) { callT -= 1 / FPS; if (callT <= 0 && w.voice === 'call') { w.voice = 'none'; sync(); } }
        const n0 = d.events.length; Threshold.step(d, w, 1 / FPS);
        for (const e of d.events.slice(n0)) if (e.e === 'transition') { log.unshift(`${d.t.toFixed(1)} s  ${e.from} → ${e.to}: ${e.why}`); log = log.slice(0, 6); }
        dog.update({ state: d.state, x: d.x, v: d.v, face: d.face, trust: d.trust, heard: d.t - d.heard }, 1 / FPS);
        per.update({ x: Threshold.PERSON_X[w.place], sit: w.posture === 'sit' ? 1 : 0, reach: w.hand === 'reach' ? 1 : 0, low: w.hand === 'low' ? 1 : 0, mouth: w.voice === 'call' ? .9 : w.voice === 'soft' ? .35 : 0 }, 1 / FPS);
        door += ((w.door === 'open' ? 1 : 0) - door) * .08;
      }
      const t = d.t;
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H);
      const K = Stage.drawSet(ctx, cam, { door, light: .25 + .75 * door, windowLit: true }, W, H);
      Stage.puppet(ctx, K, per.x, 1, 1, g => Stage.drawPerson(g, per.p), .32);
      const turn = Math.abs(dog.p.turn) < .06 ? .06 * Math.sign(dog.p.turn || 1) : dog.p.turn;
      Stage.puppet(ctx, K, d.x, turn, 1, g => Stage.drawDog(g, dog.p, t), .34);
      if (d.x < .9) Stage.jamb(ctx, K);
      if (w.voice !== 'none') Stage.bubble(ctx, K, [per.x + .05, per.p.sit > .5 ? .95 : 1.78], w.voice === 'call' ? 'Come here!' : "it's all right.", { loud: w.voice === 'call' });
      const lift = dog.p.lie > .5 ? .75 : 1;
      Stage.tag(ctx, K, [d.x - .25 * Math.sign(dog.p.turn || 1), lift * .62], [Math.min(d.x + .1, 4.4), lift + .55],
        ['dog · ' + (d.state === 'lie_down' && d.x < .5 ? 'lying on the sill' : WORD[d.state]), { t: 'trust', bar: d.trust, barc: d.trust > .6 ? Stage.C.teal : d.trust < .25 ? Stage.C.stamp : '#c88a00' }], { size: 24, top: 16, H: H + 74 });
      $('.st').textContent = WORD[d.state]; $('.tr').textContent = d.trust.toFixed(2); $('.th').textContent = d.threat.toFixed(2); $('.pr').textContent = d.pressure.toFixed(2);
      $('.why').textContent = d.reason; $('.log').textContent = log.join('\n') || 'no choices yet';
    }
    (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => { reset(); requestAnimationFrame(tick); });
  }
})();
