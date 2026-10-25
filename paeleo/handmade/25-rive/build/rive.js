/* SCION-25 RIVE · a small puppet runtime built here because the Rive runtime is not available in this environment.
   Its primitives are Rive's: an artboard of bones and shapes bound to bones (puppet.json), keyed clips (single-key poses and
   loops), typed inputs (number / boolean / trigger), a state machine of layers whose transitions are checked in explicit
   priority order, 1D blend states, IK constraints for the legs, and a deterministic event trace (every transition, footfall
   and contact is an event with a time). No pixels come from anywhere: the dog is drawn from these primitives every frame.
   Runs in node (for the event tests) and in the browser (for the film and the playable page). */
(function (root, factory) { if (typeof module === 'object' && module.exports) module.exports = factory(); else root.RIVE = factory(); })(this, function () {
  'use strict';
  const D2R = Math.PI / 180, clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v)), lerp = (a, b, k) => a + (b - a) * k;
  const ease = k => { k = clamp(k); return k * k * (3 - 2 * k); };
  const smooth = (a, b, v) => ease((v - a) / (b - a));

  /* ---------- inputs ---------- */
  class Inputs {
    constructor(defs) { this.defs = {}; this.v = {}; this.fired = {}; for (const d of defs) { this.defs[d.name] = d.type; this.v[d.name] = d.type === 'boolean' ? false : 0; } }
    set(name, value) { if (!(name in this.defs)) throw new Error('no input ' + name); if (this.defs[name] === 'trigger') { if (value) this.fired[name] = true; } else this.v[name] = value; }
    fire(name) { this.set(name, true); }
    get(name) { return this.defs[name] === 'trigger' ? !!this.fired[name] : this.v[name]; }
    consume() { this.fired = {}; }
  }

  /* ---------- state machine: layers, priorities, events ---------- */
  function test(inputs, layer, c) {
    if (c[0] === '@done') return layer.done;
    const v = inputs.get(c[0]), w = c[2];
    switch (c[1]) { case '==': return v === w; case '!=': return v !== w; case '>': return v > w; case '<': return v < w; case '>=': return v >= w; case '<=': return v <= w; }
    throw new Error('bad op ' + c[1]);
  }
  class StateMachine {
    constructor(def, inputs) {
      this.def = def; this.inputs = inputs; this.t = 0; this.events = [];
      this.layers = def.layers.map(L => ({ def: L, name: L.name, state: L.entry, since: 0, done: false,
        trans: L.transitions.slice().sort((a, b) => a.priority - b.priority) }));
    }
    advance(dt) {
      this.t += dt; const out = [];
      for (const L of this.layers) {
        const sd = L.def.states[L.state];
        L.done = sd.duration ? (this.t - L.since) >= sd.duration : true;
        for (const tr of L.trans) {   // first transition (lowest priority number) whose conditions all hold wins; no self-transitions
          if (tr.from !== '*' && tr.from !== L.state) continue;
          if (tr.to === L.state) continue;
          if (!tr.when.every(c => test(this.inputs, L, c))) continue;
          const ev = { t: +this.t.toFixed(4), kind: 'transition', layer: L.name, from: L.state, to: tr.to, priority: tr.priority, event: tr.event || null };
          L.state = tr.to; L.since = this.t; L.done = false; out.push(ev); break;
        }
      }
      this.inputs.consume(); this.events.push(...out); return out;
    }
    layer(name) { return this.layers.find(l => l.name === name); }
    local(name) { const L = this.layer(name); return { state: L.state, k: L.def.states[L.state].duration ? clamp((this.t - L.since) / L.def.states[L.state].duration) : 1, sd: L.def.states[L.state] }; }
  }

  /* ---------- clips and blends ---------- */
  function clipAt(clip, t) {   // single-key pose, or a looping keyed clip sampled at t
    if (!clip.keys) return clip;
    const T = clip.loop, u = ((t % T) + T) % T; const K = clip.keys;
    for (let i = 0; i < K.length - 1; i++) if (u >= K[i][0] && u <= K[i + 1][0]) {
      const k = ease((u - K[i][0]) / (K[i + 1][0] - K[i][0])), o = {};
      for (const c in K[i][1]) o[c] = lerp(K[i][1][c], K[i + 1][1][c], k); return o;
    }
    return K[0][1];
  }
  function mix(a, b, k) { const o = Object.assign({}, a); for (const c in b) o[c] = lerp(a[c] !== undefined ? a[c] : 0, b[c], k); return o; }
  function addv(a, b, k) { const o = Object.assign({}, a); for (const c in b) o[c] = (a[c] || 0) + b[c] * k; return o; }
  function blend1D(points, v) {   // points: [[value, pose], ...] sorted
    if (v <= points[0][0]) return points[0][1];
    for (let i = 0; i < points.length - 1; i++) if (v <= points[i + 1][0]) return mix(points[i][1], points[i + 1][1], ease((v - points[i][0]) / (points[i + 1][0] - points[i][0])));
    return points[points.length - 1][1];
  }

  /* ---------- the dog: artboard + state machine + solver ---------- */
  const MOODS = ['watch', 'approach', 'retreat', 'lie_down', 'refuse'];
  function yawVia(a, b, k) { return lerp(a, b, ease(k)); }   // the 'front' path: 180 -> 90 -> 0 and back passes the face toward the camera (+Z)

  class Dog {
    constructor(puppet, opt) {
      this.P = puppet; this.B = puppet.bones; this.C = puppet.clips; this.pal = puppet.palette;
      this.inputs = new Inputs(puppet.inputs); this.sm = new StateMachine(puppet.stateMachine, this.inputs);
      this.X = opt.X; this.Z = opt.Z || 0; this.t = 0; this.yaw = 180; this.headRel = 0; this.events = this.sm.events;
      this.earFlick = 0; this.feet = null; this.lastSpeed = 0; this.foldFrom = null;
    }
    /* channels from the blend graph */
    channels() {
      const I = this.inputs.v, C = this.C;
      let body = mix(C.stand, C.crouch, clamp(I.crouch));
      body = mix(body, C.lie, ease(clamp(I.lie)));
      let pose = Object.assign({ neckLenAdd: 0, headYawAdd: 0, chestR: 0 }, body);
      const head = blend1D([[0, C.headDown], [0.45, C.headLow], [0.9, C.headAlert], [1.2, C.headHigh]], I.head);
      pose.neckAng = head.neckAng;
      // while standing on the approach the head is held below the back line whatever 'head' says (the slink is part of Walk)
      const att = this.sm.local('Attention').state;
      pose = addv(pose, { neckAdd: C.rest.neckAdd, headPitch: C.rest.headPitch, neckLenAdd: C.rest.neckLenAdd }, ease(clamp(I.rest)) * clamp(I.lie));
      pose = addv(pose, C.lookIn, ease(clamp(I.look)));
      const tail = blend1D([[0, C.tailHigh], [0.5, C.tailNeutral], [1.35, C.tailTucked]], I.tail);
      pose.tailAng = tail.tailAng; pose.tailCurl = tail.tailCurl;
      pose.wag = clipAt(C.wag, this.t).wag * clamp(I.wag) * (0.35 + 0.2 * clamp(I.lie));
      pose.chestR = clipAt(C.breath, this.t).chestR * (1 + clamp(I.lie));
      pose.earUp = clamp(I.ear + this.earFlick * 0.5, -0.1, 1.1);
      pose.att = att; return pose;
    }
    /* body frame -> world */
    W(f, y, l, yaw) { const a = (yaw === undefined ? this.yaw : yaw) * D2R; return [this.X + f * Math.cos(a) - l * Math.sin(a), y, this.Z + f * Math.sin(a) + l * Math.cos(a)]; }
    step(dt, frameInputs) {
      for (const k in frameInputs) this.inputs.set(k, frameInputs[k]);
      if (frameInputs.heard) this.earFlick = 1;
      this.earFlick = Math.max(0, this.earFlick - dt * 2.2);
      const tr = this.sm.advance(dt); this.t = this.sm.t;
      // Facing layer output
      const F = this.sm.local('Facing'), sd = F.sd;
      if (sd.from) {
        const k = F.k; this.yaw = yawVia(sd.from.yaw, sd.to.yaw, k);
        if (sd.keepHeadWorld) { const hw = lerp(sd.from.yaw + sd.from.headRel, sd.to.yaw + sd.to.headRel, ease(k)); this.headRel = hw - this.yaw; }
        else this.headRel = lerp(sd.from.headRel, sd.to.headRel, ease(clamp(k + (sd.headLag || 0))));
      } else { this.yaw = sd.yaw; this.headRel = sd.headRel; }
      return tr;
    }
    /* full solve: returns 3D points and leg chains; gait keeps planted feet fixed in the world */
    solve(dt) {
      const B = this.B, ch = this.channels(), yaw = this.yaw, I = this.inputs.v;
      const pc = 0.4, pr = ch.pitch * D2R;
      const bp = (f, y) => {   // body pose transform: pitch about the centre, rear drop, height
        const dy = y - pc, f2 = f * Math.cos(pr) - dy * Math.sin(pr), y2 = pc + f * Math.sin(pr) + dy * Math.cos(pr);
        return [f2, y2 + ch.bodyY - ch.rearDrop * clamp(-f / 0.3, 0, 1.2)];
      };
      const S = {}; S.ch = ch;
      const P3 = (f, y, l) => { const q = bp(f, y); return this.W(q[0], q[1], l || 0); };
      S.chest = { p: P3(B.chest.f, B.chest.y), r: B.chest.r + ch.chestR };
      S.waist = { p: P3(B.waist.f, B.waist.y), r: B.waist.r + ch.chestR * 0.5 };
      S.rump = { p: P3(B.rump.f, B.rump.y), r: B.rump.r };
      const so = B.saddleOffset;
      S.saddle = [P3(B.chest.f - 0.04, B.chest.y + so), P3(B.waist.f, B.waist.y + so * 0.9), P3(B.rump.f + 0.02, B.rump.y + so * 0.85)];
      // neck and head (head yaw relative to body, from the Facing layer, plus look-in)
      const nb = bp(B.neckBase.f, B.neckBase.y), na = Math.max(-52, ch.neckAng + (ch.neckAdd || 0)) * D2R, psi = (this.headRel + (ch.headYawAdd || 0)) * D2R;
      const nl = B.neckLen + (ch.neckLenAdd || 0);
      const reach = Math.max(Math.cos(na), 0.55 * Math.abs(Math.sin(psi)));
      const hf = nb[0] + reach * Math.cos(psi) * nl, hy = nb[1] + Math.sin(na) * nl * (1 - 0.3 * Math.abs(Math.sin(psi))), hl = reach * Math.sin(psi) * nl * 1.25;
      S.neckBase = this.W(nb[0], nb[1], 0); S.skull = { p: this.W(hf, hy, hl), r: B.skullR };
      const hyaw = yaw + this.headRel + (ch.headYawAdd || 0), hp = (ch.headPitch + (I.lie > 0.5 ? 0 : 0)) * D2R;
      const fw = [Math.cos(hyaw * D2R), 0, Math.sin(hyaw * D2R)], lat = [-Math.sin(hyaw * D2R), 0, Math.cos(hyaw * D2R)];
      const md = [fw[0] * Math.cos(hp), -Math.sin(hp), fw[2] * Math.cos(hp)];
      const add = (p, v, k) => [p[0] + v[0] * k, p[1] + v[1] * k, p[2] + v[2] * k];
      const up = [0, 1, 0], sk = S.skull.p;
      S.muzzleMid = { p: add(sk, md, 0.07), r: 0.05 }; S.muzzleTip = { p: add(sk, md, B.muzzleLen), r: B.muzzleR };
      S.nose = add(add(sk, md, B.muzzleLen + 0.012), up, 0.008);
      S.eyes = [1, -1].map(s => add(add(add(sk, fw, 0.04), up, 0.028), lat, 0.042 * s));
      const e = clamp(ch.earUp, -0.1, 1.1);
      S.ears = [1, -1].map(s => {
        const r0 = add(add(add(sk, up, 0.05), fw, -0.015), lat, 0.04 * s);
        const tip = add(add(add(r0, up, 0.03 + 0.085 * e), fw, -(0.015 + 0.075 * (1 - e))), lat, 0.022 * s * (0.5 + e));
        return { a: add(r0, fw, 0.03), b: add(r0, fw, -0.03), tip, s };
      });
      S.headFw = fw; S.headLat = lat;
      // tail chain
      const tb = bp(B.tailBase.f, B.tailBase.y); let ang = ch.tailAng * D2R, wagA = ch.wag * 0.6;
      let p = this.W(tb[0], tb[1], 0); S.tail = [p];
      for (let i = 0; i < B.tailSegs.length; i++) {
        const lw = wagA * (0.4 + i * 0.25) + clamp(I.lie) * (0.25 + i * 0.32) * (this.yaw > 90 ? -1 : 1);
        const dir = this.W(-Math.cos(ang) * Math.cos(lw), Math.sin(ang), Math.cos(ang) * Math.sin(lw) * (1), yaw);
        const d = [dir[0] - this.X, dir[1], dir[2] - this.Z];
        p = add(p, d, B.tailSegs[i]); S.tail.push(p); ang += ch.tailCurl * D2R * (1 - clamp(I.lie) * 0.5);
      }
      // lying lays the tail on the floor
      if (I.lie > 0) S.tail = S.tail.map(q => [q[0], Math.max(q[1], 0.03), q[2]]);
      // legs: roots, gait targets (planted feet stay fixed in the world), folds, IK
      S.legs = this.legs(dt, bp, ch); S.yaw = yaw; S.X = this.X; S.Z = this.Z;
      return S;
    }
    legs(dt, bp, ch) {
      const B = this.B, I = this.inputs.v, lie = ease(clamp(I.lie)), defs = [
        { n: 'LF', front: 1, s: 1 }, { n: 'RF', front: 1, s: -1 }, { n: 'LH', front: 0, s: 1 }, { n: 'RH', front: 0, s: -1 }];
      const speed = I.speed, a = this.yaw * D2R;
      const vel = [speed, 0];   // world X velocity (score v), Z none
      const home = d => { const h = d.front ? B.homeFront : B.homeHind; const ff = h.f + (d.front ? ch.frontPawF : ch.hindPawF) * 0.25; const w = this.W(ff, 0, h.l * d.s); return [w[0], w[2]]; };
      const fold = d => { const h = d.front ? B.homeFront : B.homeHind; const ff = h.f + (d.front ? ch.frontPawF : ch.hindPawF);
        const l = d.front ? 0.06 * d.s : (h.l + ch.hindPawL) * d.s; const w = this.W(ff, 0, l); return [w[0], w[2]]; };
      if (!this.feet) this.feet = defs.map(d => ({ n: d.n, P: home(d), swing: null, stillErr: 0 }));
      const swinging = this.feet.filter(f => f.swing).length;
      const out = [];
      defs.forEach((d, i) => {
        const ft = this.feet[i], H = home(d);
        const lead = [H[0] + vel[0] * 0.16, H[1] + vel[1] * 0.16];
        let pos, lift = 0;
        if (!this.lyingFeet && I.lie > 0.02) { this.lyingFeet = true; this.foldFrom = this.feet.map(f => f.P.slice()); this.feet.forEach(f => { f.swing = null; }); }
        if (this.lyingFeet && I.lie < 0.12 && I.lie < (this.prevLie || 0) && i === 0) { this.lyingFeet = false; this.feet.forEach((f, j) => { f.P = f.lastPos ? f.lastPos.slice() : f.P; }); this.foldFrom = null; }
        if (this.lyingFeet) {   // lying: the feet fold toward the authored lying pose; stepping is off
          const F0 = this.foldFrom[i], Fd = fold(d); pos = [lerp(F0[0], Fd[0], lie), lerp(F0[1], Fd[1], lie)];
        } else {
          const err = Math.hypot(ft.P[0] - lead[0], ft.P[1] - lead[1]);
          const moving = Math.abs(speed) > 0.03 || this.sm.local('Facing').sd.from;
          ft.stillErr = !moving && err > 0.05 ? ft.stillErr + dt : 0;
          const partner = this.feet[d.front ? (d.s > 0 ? 1 : 0) : (d.s > 0 ? 3 : 2)], turning = !!this.sm.local('Facing').sd.from && this.sm.local('Facing').sd.to.yaw !== this.sm.local('Facing').sd.from.yaw;
          const thr = turning ? 0.05 : moving ? 0.15 : 0.05;
          if (!ft.swing && (err > thr && (moving || ft.stillErr > 0.35)) && this.feet.filter(f => f.swing).length < 2 && (turning || !partner.swing)) {
            const dur = turning ? 0.14 : Math.abs(speed) > 0.5 ? 0.22 : 0.27;
            ft.swing = { from: ft.P.slice(), t: 0, dur };
          }
          if (ft.swing) {
            ft.swing.t += dt; const k = clamp(ft.swing.t / ft.swing.dur), tgt = [H[0] + vel[0] * 0.24, H[1] + vel[1] * 0.24];
            pos = [lerp(ft.swing.from[0], tgt[0], ease(k)), lerp(ft.swing.from[1], tgt[1], ease(k))]; lift = Math.sin(Math.PI * k) * (d.front ? 0.07 : 0.06);
            if (k >= 1) { ft.P = pos.slice(); ft.swing = null; this.events.push({ t: +this.t.toFixed(4), kind: 'footfall', foot: d.n, x: +pos[0].toFixed(4) }); }
          } else pos = ft.P.slice();
        }
        ft.lastPos = pos.slice();
        // IK
        const root = d.front ? B.shoulder : B.hip, rq = bp(root.f, root.y), R = this.W(rq[0], rq[1], root.l * d.s);
        const paw = [pos[0], 0.028 + lift, pos[1]];
        const fwd = [Math.cos(a), 0, Math.sin(a)];
        let mid;   // wrist / hock
        if (d.front) { const fl = ch.pasternFlat * lie; mid = [paw[0] - fwd[0] * (0.01 + 0.05 * fl), paw[1] + B.pastern * (1 - fl) + 0.018 * fl, paw[2] - fwd[2] * (0.01 + 0.05 * fl)]; }
        else { const fl = Math.max(ch.metaFlat * lie, (ch.metaFlat || 0) * 0.15); mid = [paw[0] - fwd[0] * (0.035 + B.hindMeta * fl * 0.9), paw[1] + B.hindMeta * (1 - fl) + 0.02 * fl, paw[2] - fwd[2] * (0.035 + B.hindMeta * fl * 0.9)]; }
        const la = d.front ? B.frontUpper : B.hindThigh, lb = d.front ? B.frontLower : B.hindShin;
        const pole = d.front ? [-fwd[0], -0.25, -fwd[2]] : [fwd[0], 0.15, fwd[2]];
        let knee = ik(R, mid, la, lb, pole);
        if (knee[1] < 0.03) knee[1] = 0.03;
        out.push({ n: d.n, front: d.front, s: d.s, root: R, knee, mid, paw, planted: !ft.swing && !this.lyingFeet });
      });
      this.prevLie = I.lie; return out;
    }
  }
  function ik(R, T, a, b, pole) {
    let d = [T[0] - R[0], T[1] - R[1], T[2] - R[2]]; let L = Math.hypot(d[0], d[1], d[2]); const Lc = Math.min(L, (a + b) * 0.995);
    const u = [d[0] / L, d[1] / L, d[2] / L];
    const proj = (a * a - b * b + Lc * Lc) / (2 * Lc), h = Math.sqrt(Math.max(0, a * a - proj * proj));
    const pd = pole[0] * u[0] + pole[1] * u[1] + pole[2] * u[2]; let n = [pole[0] - pd * u[0], pole[1] - pd * u[1], pole[2] - pd * u[2]];
    const nl = Math.hypot(n[0], n[1], n[2]) || 1; n = [n[0] / nl, n[1] / nl, n[2] / nl];
    return [R[0] + u[0] * proj + n[0] * h, R[1] + u[1] * proj + n[1] * h, R[2] + u[2] * proj + n[2] * h];
  }

  /* ---------- drawing the solved dog with a projection (x,y,z)->[sx,sy] and scale S px/m ---------- */
  function hull(pts) {
    pts = pts.slice().sort((p, q) => p[0] - q[0] || p[1] - q[1]); const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lo = [], hi = []; for (const p of pts) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
    for (let i = pts.length - 1; i >= 0; i--) { const p = pts[i]; while (hi.length >= 2 && cr(hi[hi.length - 2], hi[hi.length - 1], p) <= 0) hi.pop(); hi.push(p); }
    return lo.slice(0, -1).concat(hi.slice(0, -1));
  }
  function circlePts(c, r, n) { const o = []; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2; o.push([c[0] + Math.cos(a) * r, c[1] + Math.sin(a) * r]); } return o; }
  function capsule(ctx, a, ra, b, rb) { const h = hull(circlePts(a, ra, 28).concat(circlePts(b, rb, 28))); ctx.moveTo(h[0][0], h[0][1]); for (const p of h) ctx.lineTo(p[0], p[1]); ctx.closePath(); }
  function shade(hex, k) { const n = parseInt(hex.slice(1), 16); const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255; return `rgb(${Math.round(clamp(r * k, 0, 255))},${Math.round(clamp(g * k, 0, 255))},${Math.round(clamp(b * k, 0, 255))})`; }

  function drawDog(ctx, S, proj, sc, pal) {
    const items = [], Pj = p => proj(p[0], p[1], p[2]);
    const Zc = S.Z + (S.chest.p[2] + S.rump.p[2]) / 2 - S.Z;
    // torso: union of two capsules (chest-waist, waist-rump); the waist sits higher, which gives the tuck
    items.push({ z: Zc, f: () => {
      const c = Pj(S.chest.p), w = Pj(S.waist.p), r = Pj(S.rump.p);
      ctx.fillStyle = pal.coat; ctx.beginPath(); capsule(ctx, c, S.chest.r * sc, w, S.waist.r * sc); capsule(ctx, w, S.waist.r * sc, r, S.rump.r * sc); ctx.fill('nonzero');
      ctx.save(); ctx.clip('nonzero');
      // pale chest
      ctx.fillStyle = pal.chest; const cf = Pj([S.chest.p[0], S.chest.p[1] - 0.05, S.chest.p[2]]); ctx.beginPath();
      const fw = [Math.cos(S.yaw * D2R), 0, Math.sin(S.yaw * D2R)]; const cp = Pj([S.chest.p[0] + fw[0] * 0.09, S.chest.p[1] - 0.06, S.chest.p[2] + fw[2] * 0.09]);
      ctx.arc(cp[0], cp[1], S.chest.r * sc * 0.85, 0, 7); ctx.fill();
      // dark saddle along the back
      ctx.fillStyle = pal.saddle; ctx.beginPath(); const s0 = Pj(S.saddle[0]), s1 = Pj(S.saddle[1]), s2 = Pj(S.saddle[2]);
      capsule(ctx, s0, S.chest.r * sc * 0.9, s1, S.waist.r * sc * 1.0); capsule(ctx, s1, S.waist.r * sc, s2, S.rump.r * sc * 0.95); ctx.fill('nonzero');
      // belly shade
      ctx.fillStyle = 'rgba(40,20,10,0.18)'; ctx.beginPath(); const bl = Pj([S.waist.p[0], S.waist.p[1] - 0.13, S.waist.p[2]]); ctx.ellipse(bl[0], bl[1], S.waist.r * sc * 2.2, S.waist.r * sc * 0.8, 0, 0, 7); ctx.fill();
      ctx.restore();
    } });
    // neck
    items.push({ z: (S.neckBase[2] + S.skull.p[2]) / 2 + 0.01, f: () => {
      const a = Pj(S.neckBase), b = Pj(S.skull.p); ctx.fillStyle = pal.coat; ctx.beginPath(); capsule(ctx, a, 0.1 * sc, b, 0.07 * sc); ctx.fill();
      ctx.fillStyle = pal.saddle; ctx.beginPath(); const a2 = Pj([S.neckBase[0], S.neckBase[1] + 0.05, S.neckBase[2]]), b2 = Pj([S.skull.p[0], S.skull.p[1] + 0.03, S.skull.p[2]]);
      ctx.save(); ctx.beginPath(); capsule(ctx, a, 0.1 * sc, b, 0.07 * sc); ctx.clip(); ctx.beginPath(); capsule(ctx, a2, 0.07 * sc, b2, 0.045 * sc); ctx.fill(); ctx.restore();
    } });
    // head parts, each with its own depth so a head turned away shows the back of the skull
    const hz = S.skull.p[2] + 0.02;
    items.push({ z: hz, f: () => { const c = Pj(S.skull.p); ctx.fillStyle = pal.coat; ctx.beginPath(); ctx.arc(c[0], c[1], S.skull.r * sc, 0, 7); ctx.fill();
      ctx.fillStyle = pal.saddle; ctx.save(); ctx.beginPath(); ctx.arc(c[0], c[1], S.skull.r * sc, 0, 7); ctx.clip(); const t = Pj([S.skull.p[0] - S.headFw[0] * 0.03, S.skull.p[1] + 0.05, S.skull.p[2] - S.headFw[2] * 0.03]); ctx.beginPath(); ctx.arc(t[0], t[1], S.skull.r * sc * 0.85, 0, 7); ctx.fill(); ctx.restore(); } });
    items.push({ z: S.muzzleMid.p[2] + 0.021, f: () => { const a = Pj(S.muzzleMid.p), b = Pj(S.muzzleTip.p); ctx.fillStyle = pal.coat; ctx.beginPath(); capsule(ctx, Pj(S.skull.p), S.skull.r * sc * 0.75, b, S.muzzleTip.r * sc); ctx.fill();
      ctx.fillStyle = pal.mask; ctx.beginPath(); capsule(ctx, a, S.muzzleMid.r * sc * 0.82, b, S.muzzleTip.r * sc); ctx.fill(); } });
    items.push({ z: S.muzzleTip.p[2] + 0.03, f: () => { const n = Pj(S.nose); ctx.fillStyle = pal.nose; ctx.beginPath(); ctx.arc(n[0], n[1], 0.021 * sc, 0, 7); ctx.fill(); } });
    S.eyes.forEach(e => { const vis = e[2] - S.skull.p[2] > -0.004; if (!vis) return; items.push({ z: hz + 0.015, f: () => { const p = Pj(e); ctx.fillStyle = pal.eye; ctx.beginPath(); ctx.arc(p[0], p[1], 0.0125 * sc, 0, 7); ctx.fill(); ctx.fillStyle = pal.eyeLight; ctx.beginPath(); ctx.arc(p[0] - 0.004 * sc, p[1] - 0.004 * sc, 0.0035 * sc, 0, 7); ctx.fill(); } }); });
    S.ears.forEach(E => items.push({ z: (E.a[2] + E.b[2] + E.tip[2]) / 3 + 0.02 + (E.tip[2] > S.skull.p[2] ? 0.01 : -0.03), f: () => {
      const a = Pj(E.a), b = Pj(E.b), t = Pj(E.tip); ctx.fillStyle = pal.ear; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo((a[0] + t[0]) / 2 + (a[1] - t[1]) * 0.12, (a[1] + t[1]) / 2, t[0], t[1]); ctx.quadraticCurveTo((b[0] + t[0]) / 2, (b[1] + t[1]) / 2, b[0], b[1]); ctx.closePath(); ctx.fill(); } }));
    // tail: a tapered chain of round strokes
    items.push({ z: S.tail[1][2] - 0.012, f: () => { const T = S.tail.map(Pj), w = [0.072, 0.07, 0.062, 0.05, 0.034];
      ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.beginPath(); ctx.moveTo(T[0][0], T[0][1]); for (let i = 1; i < T.length; i++) ctx.lineTo(T[i][0], T[i][1]);
      for (let i = 0; i < T.length - 1; i++) { ctx.strokeStyle = pal.coat; ctx.lineWidth = w[i] * sc; ctx.beginPath(); ctx.moveTo(T[i][0], T[i][1]); ctx.lineTo(T[i + 1][0], T[i + 1][1]); ctx.stroke(); }
      for (let i = 0; i < T.length - 1; i++) { ctx.strokeStyle = i >= T.length - 3 ? pal.tailTip : pal.saddle; ctx.lineWidth = w[i] * sc * 0.55; ctx.beginPath(); ctx.moveTo(T[i][0], T[i][1] - w[i] * sc * 0.2); ctx.lineTo(T[i + 1][0], T[i + 1][1] - w[i + 1 < w.length ? i + 1 : i] * sc * 0.2); ctx.stroke(); } } });
    // legs
    for (const L of S.legs) {
      const near = L.root[2] > S.Z + (L.front ? (S.chest.p[2] - S.Z) : (S.rump.p[2] - S.Z));
      const z = (L.root[2] + L.knee[2] + L.paw[2]) / 3 + (near ? 0.004 : -0.004);
      items.push({ z, f: () => {
        const col = near ? pal.coat : pal.coatFar, r = Pj(L.root), k = Pj(L.knee), m = Pj(L.mid), p = Pj(L.paw);
        ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = col;
        const w = L.front ? [0.085, 0.05, 0.042] : [0.115, 0.062, 0.044];
        ctx.lineWidth = w[0] * sc; ctx.beginPath(); ctx.moveTo(r[0], r[1]); ctx.lineTo(k[0], k[1]); ctx.stroke();
        ctx.lineWidth = w[1] * sc; ctx.beginPath(); ctx.moveTo(k[0], k[1]); ctx.lineTo(m[0], m[1]); ctx.stroke();
        ctx.lineWidth = w[2] * sc; ctx.strokeStyle = near ? pal.paw : shade(pal.paw, 0.7); ctx.beginPath(); ctx.moveTo(m[0], m[1]); ctx.lineTo(p[0], p[1]); ctx.stroke();
        ctx.fillStyle = near ? pal.paw : shade(pal.paw, 0.7); ctx.beginPath(); ctx.ellipse(p[0], p[1] + 0.004 * sc, 0.034 * sc, 0.022 * sc, 0, 0, 7); ctx.fill();
      } });
    }
    items.sort((a, b) => a.z - b.z); for (const it of items) it.f();
  }

  return { Inputs, StateMachine, Dog, drawDog, MOODS, ease, clamp, lerp, smooth, hull, capsule, circlePts, shade, clipAt, blend1D, mix };
});
