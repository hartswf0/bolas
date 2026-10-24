/* PAELEO-00 · The threshold. The dog's state machine.
   One file runs the film (tools/paeleo/film.js, in node) and the Try it page (in the browser), so the dog you play with is the dog in the film.

   The world is a side view along the floor, in metres. The threshold (the door sill) is x = 0; inside is negative, the porch positive.
   The operator never moves the dog. It changes circumstances (the person's posture and place, the door, the voice, the hand) and the
   dog reads them through what it perceives, what it trusts and what it remembers. Five states: watch, approach, retreat, lie_down, refuse. */
(function (root, factory) { if (typeof module === 'object' && module.exports) module.exports = factory(); else root.Threshold = factory(); })(this, function () {
  'use strict';
  const STATES = ['watch', 'approach', 'retreat', 'lie_down', 'refuse'];
  const SILL = 0.12;          // the closest the dog will come: lying across the sill, front half in the doorway, back half out
  const PORCH_END = 4.9;      // the porch steps
  const PERSON_X = { doorway: -0.28, beside: -1.25 };
  // minimum time in a state before a lower-priority guard may take it out (action windows: no flicker)
  const DWELL = { watch: 1.0, approach: 0.7, retreat: 1.1, lie_down: 2.2, refuse: 3.5 };
  const WORLD = { posture: 'stand', place: 'doorway', door: 'ajar', voice: 'none', hand: 'none' };
  const OPTIONS = { posture: ['stand', 'sit'], place: ['doorway', 'beside'], door: ['ajar', 'open'], voice: ['call', 'soft', 'none'], hand: ['none', 'low', 'reach'] };
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));

  function create(over) {
    return Object.assign({ t: 0, state: 'watch', since: 0, x: 3.0, v: 0, face: 1, trust: 0.2, pressure: 0, calls: 0, refusals: 0, lastVoice: 'none', heard: -99,
      threat: 0, invite: 0, settle: 0, reason: 'starts on the porch, watching', events: [] }, over || {});
  }

  /* what the dog perceives: how much the scene presses on it, and how much it invites */
  function perceive(d, w) {
    const px = PERSON_X[w.place], dist = Math.max(0, d.x - px);
    const near = 1 + 1.3 * clamp((2.6 - dist) / 2.6);
    const blocking = w.place === 'doorway' && w.posture === 'stand';
    let threat = (w.hand === 'reach' ? 0.55 : 0) + (w.voice === 'call' ? 0.42 : 0) + (blocking ? 0.22 : 0) + (w.place === 'doorway' && w.posture === 'sit' ? 0.08 : 0);
    threat = clamp(threat * near + d.pressure * 0.35);
    const invite = clamp((w.voice === 'soft' ? 0.25 : 0) + (w.hand === 'low' ? 0.35 : 0) + (w.posture === 'sit' ? 0.3 : 0) + (w.door === 'open' ? 0.15 : 0) + (w.place === 'beside' ? 0.15 : 0) - (w.voice === 'call' ? 0.3 : 0));
    return { px, dist, threat, invite, blocking, clear: w.place === 'beside' || w.posture === 'sit' };
  }

  /* guards in priority order; the first whose condition holds (and whose state may be entered now) wins */
  function decide(d, w, p) {
    const S = d.state, dwelt = d.t - d.since >= DWELL[S];
    const G = [];
    // refuse: pressed again after it has already backed off, or pressure built from repeated calls
    if (S === 'refuse') {
      if (dwelt && d.pressure < 0.2 && p.invite > 0.5 && p.threat < 0.25) G.push(['watch', `pressure ${d.pressure.toFixed(2)} gone, invitation ${p.invite.toFixed(2)}: turns back to look`]);
      else G.push(['refuse', 'keeps its back turned']);
    } else if (d.pressure > 0.62) G.push(['refuse', `pressure ${d.pressure.toFixed(2)} > 0.62 after ${d.calls} calls: turns its back`]);
    else if (p.threat > 0.55 && ((S !== 'retreat' && p.dist >= 3.6) || d.x >= PORCH_END - 0.05)) G.push(['refuse', `threat ${p.threat.toFixed(2)} and already ${p.dist.toFixed(1)} m away: turns its back`]);
    if (S !== 'refuse') {
      if (p.threat > 0.55 && p.dist < 3.6 && d.x < PORCH_END - 0.05) G.push(['retreat', `threat ${p.threat.toFixed(2)} > 0.55 at ${p.dist.toFixed(1)} m: backs away`]);
      if ((S === 'approach' || (d.trust > 0.6 && p.threat < 0.3)) && S !== 'lie_down' && Math.abs(d.x - SILL) < 0.03) G.push(['lie_down', 'reached the sill: lies down there, half in and half out']);
      if (S === 'lie_down' && p.threat > 0.45) G.push(['watch', `threat ${p.threat.toFixed(2)} while lying: gets up`]);
      if (d.trust > 0.6 && p.threat < 0.3 && p.clear && d.x > SILL + 0.03) G.push(['approach', `trust ${d.trust.toFixed(2)} > 0.6, threat ${p.threat.toFixed(2)}, threshold clear: ${S === 'lie_down' ? 'gets up and ' : ''}comes closer`]);
      if (S === 'lie_down') G.push(['lie_down', 'stays down']);
      if (S === 'approach' && (p.threat >= 0.3 || d.trust < 0.5)) G.push(['watch', `threat ${p.threat.toFixed(2)} on the way: stops to look`]);
      if (S === 'approach') G.push(['approach', 'keeps coming']);
      if (S === 'retreat' && p.threat > 0.35 && d.x < PORCH_END - 0.05) G.push(['retreat', 'keeps backing']);
      if (d.settle > 6) G.push(['lie_down', 'nothing asked of it for a while: settles where it is']);
      G.push(['watch', 'watches']);
    }
    for (const [to, why] of G) {
      if (to === S) return [S, why];
      // a higher-priority guard may cut a dwell short only for retreat and refuse (danger interrupts); the rest wait their window
      if (dwelt || to === 'retreat' || to === 'refuse') return [to, why];
    }
    return [S, 'holds'];
  }

  function step(d, w, dt) {
    dt = dt || 1 / 24;
    // memory: a new call (silence or softness, then a call) is remembered
    if (w.voice === 'call' && d.lastVoice !== 'call') { d.calls++; d.pressure = clamp(d.pressure + (d.state === 'retreat' || d.state === 'refuse' ? 0.5 : 0.3)); d.events.push({ t: d.t, e: 'call', n: d.calls }); }
    if (w.voice !== 'none' && d.lastVoice === 'none') d.heard = d.t;   // anything said, soft or loud, is noticed
    d.lastVoice = w.voice;
    if (w.hand === 'reach' && d.state !== 'refuse') d.pressure = clamp(d.pressure + 0.12 * dt);
    d.pressure = clamp(d.pressure - (w.voice === 'call' ? 0.02 : 0.09) * dt);
    const p = perceive(d, w); d.threat = p.threat; d.invite = p.invite;
    // trust: rises with invitation, falls with threat; a dog that has refused warms up more slowly (it remembers)
    const gain = 0.16 / (1 + 0.6 * d.refusals), loss = 0.28;
    d.trust = clamp(d.trust + dt * (gain * p.invite * (1 - d.trust) * (p.threat < 0.3 ? 1 : 0.2) - loss * p.threat * d.trust));
    d.settle = p.threat < 0.15 && w.voice === 'none' && w.hand === 'none' ? d.settle + dt : 0;

    const [next, why] = decide(d, w, p);
    if (next !== d.state) {
      d.events.push({ t: +d.t.toFixed(3), e: 'transition', from: d.state, to: next, why, trust: +d.trust.toFixed(3), threat: +p.threat.toFixed(3), x: +d.x.toFixed(3) });
      if (next === 'refuse') d.refusals++;
      d.state = next; d.since = d.t; d.reason = why;
    } else d.reason = why;

    // locomotion: the state sets a target speed; the dog accelerates toward it (no teleporting, no instant stops)
    let target = 0, face = d.face;
    if (d.state === 'approach') { const sp = 0.25 + 0.55 * clamp((d.trust - 0.6) / 0.4); target = -Math.min(sp, Math.max(0.12, (d.x - SILL) * 1.6)); face = 1; }
    if (d.state === 'retreat') { target = Math.min(0.75, (PORCH_END - d.x) * 1.6); face = 1; }                     // backs away still facing the person
    if (d.state === 'refuse') face = -1;                                          // the refusal is visible: its back
    if (d.state === 'watch' || d.state === 'lie_down') face = 1;
    const acc = 2.2;
    d.v += clamp(target - d.v, -acc * dt, acc * dt);
    d.x += d.v * dt;
    if (d.x < SILL) { d.x = SILL; d.v = Math.max(0, d.v); }
    if (d.x > PORCH_END) { d.x = PORCH_END; d.v = Math.min(0, d.v); }
    d.face = face; d.t += dt;
    return d;
  }

  /* run a timeline of circumstance changes: [[t, {posture:'sit',...}], ...] */
  function run(timeline, T, dt, init) {
    dt = dt || 1 / 24; const d = create(init); const w = Object.assign({}, WORLD); const frames = []; let k = 0;
    for (let i = 0; i * dt <= T; i++) {
      while (k < timeline.length && timeline[k][0] <= d.t + 1e-9) { Object.assign(w, timeline[k][1]); d.events.push({ t: +d.t.toFixed(3), e: 'world', set: timeline[k][1] }); k++; }
      step(d, w, dt);
      frames.push({ t: +d.t.toFixed(4), state: d.state, x: +d.x.toFixed(4), v: +d.v.toFixed(4), face: d.face, trust: +d.trust.toFixed(4), threat: +d.threat.toFixed(4), invite: +d.invite.toFixed(4), pressure: +d.pressure.toFixed(4), heard: +(d.t - d.heard).toFixed(3), world: Object.assign({}, w) });
    }
    return { frames, events: d.events };
  }

  return { STATES, OPTIONS, WORLD, SILL, PORCH_END, PERSON_X, DWELL, create, perceive, step, run };
});
