/* SCION-25 RIVE · the integrator: turns each score frame into typed inputs for the dog's state machine.
   The score (the PAELEO machine's decision trace) decides; this file only feeds the puppet its inputs, exactly as a Rive
   host app would set inputs on a running state machine. Mapping of space: the score's x (metres from the threshold, centre
   of the dog's body) is placed in the world at X = x - XOFF, so the dog's front half lies inside the door frame at the end. */
(function (root, factory) { if (typeof module === 'object' && module.exports) module.exports = factory(require('./rive.js')); else root.DRIVE = factory(root.RIVE); })(this, function (RIVE) {
  'use strict';
  const XOFF = 0.24, FPS = 24;
  function make(score, puppet) {
    const F = score.frames, dog = new RIVE.Dog(puppet, { X: F[0].dog.x - XOFF, Z: 0 });
    let lastVoice = 'none', i = -1, lastDoor = F[0].door;
    function inputsFor(f) {
      const a = f.dog.act, p = f.person, inp = {
        mood: RIVE.MOODS.indexOf(f.dog.state), speed: f.dog.v, crouch: a.crouch, lie: a.lie, rest: a.rest, head: a.head,
        ear: a.ear, tail: a.tail, wag: a.wag, look: a.look, doorOpen: f.door === 'open' };
      if (p.voice !== 'none' && lastVoice === 'none') inp.heard = true;
      if (p.voice === 'call' && lastVoice !== 'call') inp.call = true;
      lastVoice = p.voice; return inp;
    }
    function step() {   // advance one frame (call in order 0..N-1)
      i++; const f = F[i], dt = i === 0 ? 1e-6 : 1 / FPS;
      const inp = inputsFor(f);
      const before = dog.events.length;
      dog.X = f.dog.x - XOFF;
      dog.step(dt, inp); const S = dog.solve(dt);
      if (f.door !== lastDoor) { dog.events.push({ t: +dog.t.toFixed(4), kind: 'world', door: f.door }); lastDoor = f.door; }
      return { i, f, S, inp, dog, newEvents: dog.events.slice(before) };
    }
    return { step, dog, XOFF };
  }
  return { make, XOFF, FPS };
});
