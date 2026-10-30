/* SCION 19 · the action librarian + view-switch choreographer: reads the score (per frame) and writes the rig's controls.
   The score gives position x, state and acting intentions; this file decides how the rig performs them:
   - the two turns are view-bone animations (psi_b, psi_h), head leading the body;
   - the gait is a footfall planner: each foot is world-fixed during stance (distance travelled drives the phase);
   - the look-in turns the head bone's view to three-quarter back (back of the head toward us, muzzle into the room).
   Output: per-frame params for rig.frame(), plus the person and door controls. */
(function (root, factory) { if (typeof module === 'object' && module.exports) module.exports = factory(require('./rig.js')); else root.Perform = factory(root.Rig); })(this, function (Rig) {
  'use strict';
  const { clamp, lerp, sm } = Rig;
  const ease = (t, a, b) => sm((t - a) / (b - a));
  const MAP = { offset: 0.42 };                       // my world: U = x_score - 0.42 (the dog's mid-spine); outer wall face at U = 0
  const xToU = x => x - MAP.offset;
  // choreography (seconds). Choice onsets are the score's; the visible action starts on them.
  const CH = {
    retreat: 1.0, watch1: 2.333, refuse: 3.417, watch2: 7.458, approach: 14.708, lie: 23.792, comeIn: 26.4,
    headTurn1: [3.40, 3.60], bodyTurn1: [3.43, 3.64],
    headTurn2: [7.44, 7.72], bodyRise2: [7.70, 8.05], bodyTurn2: [8.02, 8.55],
    lookIn: [26.38, 26.62], lookOut: [28.05, 28.40],
  };

  function perform(score) {
    const F = score.frames, N = F.length, out = [];
    let sFwd = 0, prevU = xToU(F[0].dog.x);
    for (let i = 0; i < N; i++) {
      const f = F[i], t = f.t, a = f.dog.act;
      const U = xToU(f.dog.x);
      // ---- body and head view bones
      let psiB = 0, psiH = 0;
      psiB = 180 * ease(t, ...CH.bodyTurn1) + 180 * ease(t, ...CH.bodyTurn2);
      psiH = 180 * ease(t, ...CH.headTurn1) + 180 * ease(t, ...CH.headTurn2);
      if (t >= CH.bodyTurn2[1]) { psiB = 0; psiH = 0; }
      // look in (lying across the sill): the head view goes to three-quarter back, into the room's depth
      psiH -= 45 * ease(t, ...CH.lookIn) * (1 - ease(t, ...CH.lookOut));
      // ---- lie: the score's, except at the turn back where the head must lead: the body stays down until 7.70
      let lie = a.lie;
      if (t >= 7.2 && t < 8.3) lie = 1 - ease(t, ...CH.bodyRise2);
      // ---- rest (chin on paws): lifts with the head turn at 7.44
      let rest = a.rest;
      if (t >= 7.3 && t < 8.3) rest = Math.min(rest, 1 - ease(t, 7.40, 7.56));
      let head = a.head;
      if (t >= 7.3 && t < 8.3) head = Math.max(head, lerp(0.15, 0.85, ease(t, 7.42, 7.62)));
      // refusal: the head drops as the body turns away
      if (t >= 3.4 && t < 4.5) head = t < 3.9 ? Math.max(0.8, Math.min(head, 0.9)) : Math.min(head, lerp(0.8, 0.2, ease(t, 3.88, 4.25)));
      // approach: head low (below the back) from the first step to the sill
      if (f.dog.state === 'approach') head = Math.min(head, 0.42);
      if (t >= 14.6 && t < 14.9) head = Math.min(head, lerp(0.9, 0.42, ease(t, 14.70, 14.90)));
      // look in: level head, not raised toward the light
      let look = a.look;
      // ---- gait: distance travelled along the dog's own forward axis
      const dU = U - prevU; prevU = U;
      const fU = -Math.cos(psiB * Rig.D);
      sFwd += dU * fU;
      out.push({ i, t, state: f.dog.state, U, psiB, psiH, crouch: a.crouch, lie, head, rest, look, ear: a.ear, tail: a.tail, wag: a.wag, sFwd, speed: 0 });
    }
    // speeds (m/s) and gait offsets, smoothed
    for (let i = 0; i < N; i++) { const j0 = Math.max(0, i - 1), j1 = Math.min(N - 1, i + 1); out[i].speed = Math.abs(out[j1].sFwd - out[j0].sFwd) / ((j1 - j0) / 24); }
    const SL = 0.46, DS = 0.62;   // stride (one full cycle of a foot) and stance fraction
    const PH = [0.25, 0.75, 0.0, 0.5];
    for (let i = 0; i < N; i++) {
      const p = out[i];
      const lf = clamp(p.speed / 0.12);
      // turn-in-place stepping: during a body turn the feet lift in turn
      const turnRate = i > 0 ? Math.abs(p.psiB - out[i - 1].psiB) : 0;
      p.gait = PH.map((o, k) => {
        let ph = ((p.sFwd / SL + o) % 1 + 1) % 1, x, lift = 0;
        if (ph < DS) x = SL * (DS / 2 - ph);
        else { const q = (ph - DS) / (1 - DS); x = SL * (-DS / 2 + DS * q); lift = 0.065 * Math.sin(Math.PI * q) * lf; }
        const tq = ((p.psiB / 45 + o * 2) % 1 + 1) % 1;
        if (turnRate > 0.5 && p.lie < 0.3) lift = Math.max(lift, 0.05 * Math.max(0, Math.sin(Math.PI * tq * 2)) * clamp(turnRate / 8));
        return { x, lift, ph };
      });
      p.bob = -0.012 * lf * Math.abs(Math.sin(2 * Math.PI * (p.sFwd / SL) * 2));
      p.stance = p.gait.map(g => g.lift === 0);
    }
    return out;
  }

  /* the person and the door, from the score's circumstances */
  function personDoor(score) {
    return score.frames.map(f => {
      const pr = f.person;
      // doorway (score -0.28) -> U -0.12, in the door frame; beside (score -1.25) -> sits on the porch with the house wall at its back,
      // just beside the door (U 0.42, W -1.0): out of the doorway, so the dog's look into the room points away from the person
      const q = Math.max(0, Math.min(1, (pr.x + 0.28) / (-1.25 + 0.28)));
      const U = -0.12 + 0.54 * q, Wd = -1.0 * q;
      return { t: f.t, U, W: Wd, sit: pr.sit, reach: pr.reach, low: pr.low, mouth: pr.mouth, voice: pr.voice, door: f.door };
    });
  }
  return { perform, personDoor, MAP, CH, xToU };
});
