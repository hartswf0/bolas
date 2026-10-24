/* PAELEO-00 · The threshold. The stage: a porch at dusk, a door, a person and a dog, all cut from paper.
   Drawn on a 2D canvas in metres. The same code draws the film (tools/paeleo/render.html) and the Try it page.
   DogAnim turns the machine's state into a pose (ears, tail, crouch, lie, turn) with springs, so every change has anticipation. */
(function (root, factory) { if (typeof module === 'object' && module.exports) module.exports = factory(); else root.Stage = factory(); })(this, function () {
  'use strict';
  const C = {
    skyTop: '#1d2a4a', skyMid: '#3c4f7c', skyLow: '#e7956b', ground: '#2b2a33', facade: '#9fb0bd', facadeLine: '#7f919f', trim: '#e9e3d6',
    door: '#6b2c22', doorDark: '#4a1d16', inside: '#ffcf7a', insideDeep: '#e9a54b', boards: '#6f6a72', boardsLine: '#57525b', step: '#5d5862',
    dog: '#d39a5a', dogFar: '#a87443', dogEar: '#6e4325', dogChest: '#f3e2c4', collar: '#d42a1e', nose: '#24170f',
    shirt: '#2f5d73', shirtFar: '#244859', skin: '#c99572', skinFar: '#a87a5b', trousers: '#34302d', trousersFar: '#26231f', shoe: '#1b1816', hair: '#2a1f1a',
    brad: '#c9a24a', paper: '#fbf7ee', ink: '#14110d', stamp: '#d42a1e', teal: '#0f8f80'
  };
  const lerp = (a, b, t) => a + (b - a) * t, clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const ease = t => t < 0 ? 0 : t > 1 ? 1 : t * t * (3 - 2 * t);

  // seeded jitter so every cut edge is the same in every frame (scissors, not boiling)
  function hash(n) { n = Math.sin(n * 127.1 + 311.7) * 43758.5453; return n - Math.floor(n); }
  function cut(pts, amt, seed) { return pts.map((p, i) => [p[0] + (hash(seed + i * 1.7) - .5) * amt, p[1] + (hash(seed + i * 2.3 + 9) - .5) * amt]); }
  function ellipse(cx, cy, rx, ry, n, seed, amt) {
    const pts = []; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, k = 1 + (hash(seed + i) - .5) * (amt || .05); pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]); } return pts;
  }

  let PAT = null;
  function pattern(ctx) {
    if (PAT) return PAT;
    const c = (typeof OffscreenCanvas !== 'undefined') ? new OffscreenCanvas(256, 256) : Object.assign(document.createElement('canvas'), { width: 256, height: 256 });
    const g = c.getContext('2d'), im = g.createImageData(256, 256);
    for (let i = 0; i < 256 * 256; i++) {
      const x = i % 256, y = (i / 256) | 0;
      const fib = Math.sin(x * .9 + Math.sin(y * .13) * 4) * .5 + .5;                       // faint paper fibres
      const v = 200 + hash(i * .37) * 55 - fib * 18;
      im.data[i * 4] = v; im.data[i * 4 + 1] = v * .97; im.data[i * 4 + 2] = v * .92; im.data[i * 4 + 3] = 255;
    }
    g.putImageData(im, 0, 0); PAT = ctx.createPattern(c, 'repeat'); return PAT;
  }
  // fill a path as a piece of paper: colour, fibre texture fixed to the piece, a darker cut edge
  /* Hooks for the SCION lenses (paeleo/scion/lenses.js), off by default so the film draws as it always has.
     STYLE changes how a piece is cut and filled; REC, when on, records every piece and joint in screen space under its name. */
  const STYLE = {}, REC = { on: false, n: '', parts: [], joints: {} };
  function xf(ctx, p) { const m = ctx.getTransform(); return [m.a * p[0] + m.c * p[1] + m.e, m.b * p[0] + m.d * p[1] + m.f]; }
  function mark(ctx, name, p) { if (REC.on) REC.joints[name] = xf(ctx, p); }
  function piece(ctx, pts, color, edge, texScale) {
    if (REC.on && REC.n) REC.parts.push({ name: REC.n, color, pts: pts.map(p => xf(ctx, p)) });
    if (STYLE.fill) color = STYLE.fill(color, REC.n);
    if (STYLE.edge !== undefined) edge = typeof STYLE.edge === 'function' ? STYLE.edge(edge, REC.n) : STYLE.edge;
    ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.closePath();
    if (STYLE.line) { ctx.strokeStyle = STYLE.line; ctx.lineWidth = STYLE.lineWidth || .008; ctx.lineJoin = 'round'; ctx.stroke(); return; }
    ctx.fillStyle = color; ctx.fill();
    if (STYLE.noTex) { if (edge) { ctx.strokeStyle = edge; ctx.lineWidth = STYLE.edgeWidth || .006; ctx.stroke(); } return; }
    const pat = pattern(ctx); ctx.save(); ctx.clip();
    if (pat.setTransform) pat.setTransform(new DOMMatrix().scale(texScale || 1 / 260));
    ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = .55; ctx.fillStyle = pat; ctx.fill(); ctx.restore();
    if (edge) { ctx.strokeStyle = edge; ctx.lineWidth = .006; ctx.lineJoin = 'round'; ctx.stroke(); }
  }
  function capsule(a, b, wa, wb, seed) {   // a tapered limb from a to b, round at both ends
    const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1e-6, ux = dx / L, uy = dy / L, nx = -uy, ny = ux, pts = [];
    for (let i = 0; i <= 6; i++) { const t = -Math.PI / 2 + i / 6 * Math.PI; pts.push([b[0] + wb * (Math.cos(t) * ux + Math.sin(t) * nx), b[1] + wb * (Math.cos(t) * uy + Math.sin(t) * ny)]); }
    for (let i = 0; i <= 6; i++) { const t = Math.PI / 2 + i / 6 * Math.PI; pts.push([a[0] + wa * (Math.cos(t) * ux + Math.sin(t) * nx), a[1] + wa * (Math.cos(t) * uy + Math.sin(t) * ny)]); }
    return cut(pts, .004, seed);
  }
  function brad(ctx, p, r) {
    if (STYLE.noBrads) return;
    r = r || .013; ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7); ctx.fillStyle = C.brad; ctx.fill();
    ctx.beginPath(); ctx.arc(p[0] - r * .3, p[1] - r * .3, r * .38, 0, 7); ctx.fillStyle = 'rgba(255,248,214,.85)'; ctx.fill();
  }
  // two-bone IK; the middle joint sits on the side given by `side` (+1: to the right of the root-to-target direction)
  function ik(root, target, l1, l2, side) {
    let dx = target[0] - root[0], dy = target[1] - root[1], d = Math.hypot(dx, dy);
    const dd = clamp(d, Math.abs(l1 - l2) + 1e-4, l1 + l2 - 1e-4), ux = dx / (d || 1), uy = dy / (d || 1);
    const a = (l1 * l1 - l2 * l2 + dd * dd) / (2 * dd), h = Math.sqrt(Math.max(0, l1 * l1 - a * a));
    const mid = [root[0] + ux * a - uy * h * side, root[1] + uy * a + ux * h * side];
    const end = [root[0] + ux * dd, root[1] + uy * dd];
    return [mid, end];
  }
  const rot = (p, a) => [p[0] * Math.cos(a) - p[1] * Math.sin(a), p[0] * Math.sin(a) + p[1] * Math.cos(a)];
  const add = (a, b) => [a[0] + b[0], a[1] + b[1]];

  /* ------------------------------------------------------------------ the dog */
  const BODY = cut([[-.30, -.075], [-.15, -.095], [.05, -.088], [.22, -.095], [.33, -.065], [.365, -.01], [.345, .05], [.22, .062], [.08, .04], [-.08, .07], [-.22, .11], [-.32, .09], [-.375, .03], [-.365, -.035]], .006, 11);
  const CHEST = cut([[-.36, -.02], [-.30, .0], [-.24, .07], [-.30, .1], [-.37, .04]], .004, 23);
  const SKULL = ellipse(0, 0, .085, .07, 22, 31, .04);
  const SNOUT = cut([[-.05, -.035], [-.16, -.012], [-.185, .012], [-.17, .035], [-.11, .05], [-.04, .05]], .004, 41);
  const EAR = cut([[0, 0], [.035, -.115], [.06, -.005]], .003, 51);
  const TAIL = (len, curl) => { const pts = [], n = 8; for (let i = 0; i <= n; i++) { const t = i / n, a = curl * t; pts.push([Math.cos(a) * len * t, Math.sin(a) * len * t, lerp(.028, .006, t)]); }
    const L = [], R = []; for (let i = 0; i <= n; i++) { const p = pts[i], q = pts[Math.min(n, i + 1)], r = pts[Math.max(0, i - 1)], dx = q[0] - r[0], dy = q[1] - r[1], k = Math.hypot(dx, dy) || 1; L.push([p[0] - dy / k * p[2], p[1] + dx / k * p[2]]); R.push([p[0] + dy / k * p[2], p[1] - dx / k * p[2]]); }
    return L.concat(R.reverse()); };

  function DogAnim() {
    this.p = { lie: 0, crouch: 0, ear: .8, tail: .5, wag: 0, head: .9, rest: 0, turn: 1, phase: 0, moving: 0, sniff: 0, look: 0 };
    this.v = {}; for (const k in this.p) this.v[k] = 0;
    this.lastX = null; this.steps = []; this.t = 0; this.stateT = 0; this.state = 'watch'; this.thumps = [];
  }
  // springs: a high-ish stiffness with damping gives an anticipation-free but weighted settle; turn is faster (a cut-out flip)
  DogAnim.prototype.update = function (f, dt) {
    this.t += dt; if (f.state !== this.state) { this.state = f.state; this.stateT = 0; } else this.stateT += dt;
    const s = f.state, tr = f.trust, T = {};
    T.lie = (s === 'lie_down' || (s === 'refuse' && this.stateT > .9)) ? 1 : 0;
    T.crouch = s === 'retreat' ? .9 : s === 'refuse' ? .5 : s === 'approach' ? .35 * (1 - tr) : .15 * (1 - tr);
    T.ear = s === 'retreat' ? 0 : s === 'refuse' ? .15 : s === 'lie_down' ? .45 + .3 * tr : s === 'approach' ? .55 : .95;
    T.tail = s === 'retreat' ? 1.35 : s === 'refuse' ? 1.15 : s === 'approach' ? .55 - .4 * tr : s === 'lie_down' ? .25 : .6 - .5 * tr;
    T.wag = (s === 'approach' || s === 'lie_down') ? clamp((tr - .5) * 2) * .35 : s === 'watch' ? clamp((tr - .6) * 2) * .25 : 0;
    T.head = s === 'retreat' ? .35 : s === 'refuse' ? .15 : s === 'approach' ? .45 : s === 'lie_down' ? (this.stateT < 1.6 ? .7 : .3) : .9;
    T.rest = (s === 'refuse' && this.stateT > 2.2) || (s === 'lie_down' && this.stateT > 2.4) ? 1 : 0;
    T.sniff = s === 'approach' ? 1 : 0;
    const h = f.heard === undefined ? 99 : f.heard;
    T.look = 0;
    if (s === 'lie_down' && h < this.stateT) {                                       // spoken to after it lay down
      if (h < 1.6) { T.head = 1.2; T.ear = 1; T.rest = 0; T.wag = .8; T.look = 1; }  // hears it: head up and turned in through the door, ears up, tail sweeping
      else { T.head = .2; T.ear = .4; T.rest = 1; T.wag = 0; T.look = 0; }          // then turns back out and puts its chin on its paws, and stays
    }
    // turn only when standing: a lying dog gets up first, then turns (no flip while lying)
    T.turn = (Math.sign(f.face) !== Math.sign(this.p.turn) && (this.p.lie > .15 || this.stateT < .5)) ? Math.sign(this.p.turn) : f.face;
    if (s === 'refuse' && Math.sign(this.p.turn) > 0) T.lie = 0;
    const sp = { turn: [42, 13], lie: [38, 11], ear: [120, 14], tail: [60, 10], head: [55, 11], crouch: [70, 13], rest: [30, 10], wag: [60, 12], sniff: [30, 10], look: [70, 14] };
    for (const k in T) { const [K, D] = sp[k]; const a = K * (T[k] - this.p[k]) - D * this.v[k]; this.v[k] += a * dt; this.p[k] += this.v[k] * dt; }
    // walk phase follows the distance actually travelled: feet never outrun the body
    if (this.lastX !== null) { const dx = f.x - this.lastX, prev = this.p.phase; this.p.phase += Math.abs(dx) / .55 * Math.PI * 2;
      const legs = [0, Math.PI, Math.PI * .5, Math.PI * 1.5];
      for (const off of legs) { const a = Math.sin(prev + off), b = Math.sin(this.p.phase + off); if (a > 0 && b <= 0) this.steps.push(this.t); } }
    this.p.moving = lerp(this.p.moving, clamp(Math.abs(f.v) / .15), .25);
    this.lastX = f.x; this.x = f.x;
    if (s === 'lie_down' && this.p.wag > .4) { const ph = Math.sin(this.t * Math.PI * 2 * 2.2); if (this._lastWag > 0 && ph <= 0) this.thumps.push(this.t); this._lastWag = ph; }
    return this.p;
  };

  function drawDog(ctx, P, t) {
    const lie = clamp(P.lie), cr = clamp(P.crouch, 0, 1.2) * .085 * (1 - lie);
    const hipY = lerp(-.405 + cr, -.15, lie), shY = lerp(-.415 + cr * .55, -.165, lie);
    const hip = [.22, hipY], sh = [-.21, shY];
    const pitch = Math.atan2(hipY - shY, .43);
    const O = [(hip[0] + sh[0]) / 2, (hip[1] + sh[1]) / 2 - .035];
    const B = p => add(O, rot(p, pitch));
    const mov = P.moving * (1 - lie);
    const foot = (root, off, far, front) => {
      const ph = P.phase + off, A = .1 * mov, lift = .055 * mov * Math.max(0, Math.sin(ph));
      const stand = [root[0] + Math.cos(ph) * A + (front ? -.02 : .02) + (far ? .03 : 0), -lift];
      const lieF = front ? [-.55 + (far ? .05 : 0), -.025] : [-.06 + (far ? .05 : 0), -.025];
      return [lerp(stand[0], lieF[0], lie), lerp(stand[1], lieF[1], lie)];
    };
    const leg = (root, off, far, front) => {
      const l1 = front ? .19 : .2, l2 = front ? .21 : .215, tgt = foot(root, off, far, front);
      let [mid, end] = ik(root, tgt, l1, l2, -1);
      if (!front && lie > 0) { const m2 = ik(root, tgt, l1, l2, 1)[0], k = ease(lie); mid = [lerp(mid[0], m2[0], k), lerp(mid[1], m2[1], k)]; }   // lying: the hind knee folds forward, up the flank
      const col = far ? C.dogFar : C.dog;
      const ln = 'dog.' + (front ? 'fore' : 'hind') + (far ? 'Far' : 'Near');
      REC.n = ln + '.upper'; piece(ctx, capsule(root, mid, .045, .033, front ? 61 : 71), col, 'rgba(60,30,10,.45)');
      REC.n = ln + '.lower'; piece(ctx, capsule(mid, end, .032, .024, front ? 81 : 91), col, 'rgba(60,30,10,.45)');
      REC.n = ln + '.paw'; mark(ctx, ln + '.root', root); mark(ctx, ln + '.knee', mid); mark(ctx, ln + '.foot', end); piece(ctx, ellipse(end[0] - .022, end[1] - .012, .038, .02, 12, front ? 3 : 5, .05), col, 'rgba(60,30,10,.45)');
      if (!far) brad(ctx, mid, .009);
    };
    const tailRoot = B([.345, -.06]);
    const wag = Math.sin(t * Math.PI * 2 * 2.2) * P.wag;
    const tailA = -.9 + P.tail * 1.6 + wag;      // radians below horizontal, pointing back (+x)
    // far legs, tail, body, chest, near legs, neck and head
    leg(add(sh, [.03, -.01]), Math.PI * 1.5, true, true); leg(add(hip, [.03, -.01]), Math.PI * .5, true, false);
    ctx.save(); ctx.translate(tailRoot[0], tailRoot[1]); ctx.rotate(tailA); REC.n = 'dog.tail'; mark(ctx, 'dog.tailTip', [.27 * Math.cos(-.5 + P.tail * .3), .27 * Math.sin(-.5 + P.tail * .3)]); piece(ctx, cut(TAIL(.27, -.5 + P.tail * .3), .003, 7), C.dog, 'rgba(60,30,10,.45)'); ctx.restore();
    ctx.save(); ctx.translate(O[0], O[1]); ctx.rotate(pitch); REC.n = 'dog.body'; piece(ctx, BODY, C.dog, 'rgba(50,25,8,.85)'); REC.n = 'dog.chest'; piece(ctx, CHEST, C.dogChest, null); ctx.restore();
    leg(sh, Math.PI * .5, false, true); leg(hip, Math.PI * 1.5, false, false);
    // head on the neck: head param 1 = up and alert, 0 = down; rest = chin on the paws
    const rl = clamp(P.rest) * lie;   // chin on the paws: the neck base comes forward and down to the chest, so the neck lies along the floor
    const neck = B([lerp(-.29, -.35, rl), lerp(-.06, .03, rl)]);
    const phi = lerp(.15, 1.0, clamp(P.head)) - .25 * P.sniff;
    let hc = [neck[0] - Math.cos(phi) * .17, neck[1] - Math.sin(phi) * .17];
    const restC = [-.47, -.075]; hc = [lerp(hc[0], restC[0], P.rest * lie), lerp(hc[1], restC[1], P.rest * lie)];
    const tilt = lerp(-.15, .35, 1 - clamp(P.head)) + .25 * P.sniff - .2 * P.rest * lie + Math.sin(t * 1.3) * .02;
    REC.n = 'dog.neck'; piece(ctx, capsule(neck, hc, lerp(.07, .06, rl), .055, 101), C.dog, 'rgba(50,25,8,.5)');
    mark(ctx, 'dog.neck', neck); mark(ctx, 'dog.shoulder', sh); mark(ctx, 'dog.hip', hip); mark(ctx, 'dog.tailRoot', tailRoot); mark(ctx, 'dog.head', hc);
    ctx.save(); ctx.translate(neck[0], neck[1]); ctx.rotate(Math.atan2(hc[1] - neck[1], hc[0] - neck[0]));
    ctx.fillStyle = C.collar; ctx.beginPath(); ctx.rect(.03, -.06, .028, .12); ctx.fill(); ctx.restore();
    ctx.save(); ctx.translate(hc[0], hc[1]); ctx.rotate(tilt - .25 * (P.look || 0)); ctx.scale(1 - .45 * clamp(P.look || 0), 1);
    // far ear, skull, snout, near ear
    const earA = lerp(1.25, -.15, clamp(P.ear));
    ctx.save(); ctx.translate(.03, -.045); ctx.rotate(earA + .1); REC.n = 'dog.earFar'; piece(ctx, EAR, C.dogFar, null); ctx.restore();
    REC.n = 'dog.skull'; piece(ctx, SKULL, C.dog, 'rgba(50,25,8,.85)'); REC.n = 'dog.snout'; piece(ctx, SNOUT, C.dog, 'rgba(50,25,8,.85)');
    mark(ctx, 'dog.nose', [-.178, .008]); mark(ctx, 'dog.eye', [-.06, -.018]); mark(ctx, 'dog.mouth', [-.12, .04]); mark(ctx, 'dog.skull', [0, 0]);
    ctx.beginPath(); ctx.ellipse(-.178, .008, .017, .013, 0, 0, 7); ctx.fillStyle = C.nose; ctx.fill();
    ctx.beginPath(); ctx.moveTo(-.16, .036); ctx.quadraticCurveTo(-.12, .044, -.085, .036); ctx.strokeStyle = 'rgba(40,20,10,.7)'; ctx.lineWidth = .005; ctx.stroke();
    ctx.beginPath(); ctx.arc(-.06, -.018, .012, 0, 7); ctx.fillStyle = C.nose; ctx.fill(); ctx.beginPath(); ctx.arc(-.064, -.022, .004, 0, 7); ctx.fillStyle = '#fff'; ctx.fill();
    ctx.save(); ctx.translate(.015, -.05); ctx.rotate(earA); REC.n = 'dog.ear'; mark(ctx, 'dog.earTip', [.035, -.115]); mark(ctx, 'dog.earBase', [0, 0]); piece(ctx, EAR, C.dogEar, 'rgba(40,20,10,.5)'); ctx.restore();
    brad(ctx, [.015, -.05], .008);
    ctx.restore();
    brad(ctx, neck, .011); brad(ctx, sh, .012); brad(ctx, hip, .012); brad(ctx, tailRoot, .009); REC.n = '';
  }

  /* ------------------------------------------------------------------ the person */
  const TORSO = cut([[-.13, -.02], [-.15, -.3], [-.12, -.52], [.0, -.56], [.12, -.52], [.15, -.3], [.13, -.02]], .006, 201);
  const HEAD = ellipse(0, 0, .105, .118, 24, 211, .03);
  function PersonAnim() { this.p = { sit: 0, reach: 0, low: 0, mouth: 0, phase: 0, moving: 0, lean: 0 }; this.v = {}; for (const k in this.p) this.v[k] = 0; this.x = null; this.steps = []; this.t = 0; }
  PersonAnim.prototype.update = function (target, dt) {   // target: {x, sit, reach, low, mouth}
    this.t += dt;
    if (this.x === null) this.x = target.x;
    const dx = clamp(target.x - this.x, -1.1 * dt, 1.1 * dt), prev = this.p.phase; this.x += dx; this.p.phase += Math.abs(dx) / .7 * Math.PI * 2;
    if (Math.sin(prev) > 0 !== Math.sin(this.p.phase) > 0 && Math.abs(dx) > 0) this.steps.push(this.t);
    this.p.moving = lerp(this.p.moving, Math.abs(dx) > 1e-4 ? 1 : 0, .2);
    const sp = { sit: [8, 5.6], reach: [70, 13], low: [50, 12], mouth: [300, 30], lean: [40, 11] };
    const T = { sit: target.sit, reach: target.reach, low: target.low, mouth: target.mouth, lean: target.reach * .25 + target.low * (target.sit > .5 ? .18 : .3) };
    for (const k in sp) { const [K, D] = sp[k]; this.v[k] += (K * (T[k] - this.p[k]) - D * this.v[k]) * dt; this.p[k] += this.v[k] * dt; }
    return this.p;
  };
  function drawPerson(ctx, P) {
    const s = clamp(P.sit), mv = P.moving * (1 - s);
    const sDown = ease(clamp(s * 1.25)), sOut = ease(clamp((s - .45) / .55));   // sitting: squat down first, then the legs go out
    const hip = [lerp(0, -.08, sOut), lerp(-.95, -.12, sDown)];
    const lean = P.lean;
    const up = rot([0, -.56], lean), neck = add(hip, up);
    const shoulder = add(hip, rot([.0, -.5], lean));
    const headC = add(neck, rot([.03, -.15], lean * .6));
    const legT = (far) => {
      const ph = P.phase + (far ? Math.PI : 0), sw = .16 * mv * Math.sin(ph), lift = .06 * mv * Math.max(0, Math.cos(ph));
      const st = [sw + (far ? -.02 : .02), -lift], sitF = [far ? .78 : .72, -.04];
      const sq = [st[0] + .12 * sDown * (1 - sOut), st[1]];
      return [lerp(sq[0], sitF[0], sOut), lerp(sq[1], sitF[1], sOut)];
    };
    const leg = far => { const tg = legT(far), side = s > .5 ? -1 : -1; const [k, f] = ik(add(hip, [far ? -.03 : .03, 0]), tg, .47, .47, side);
      const col = far ? C.trousersFar : C.trousers;
      REC.n = far ? 'person.legFar' : 'person.leg'; mark(ctx, REC.n + '.knee', k); mark(ctx, REC.n + '.foot', f);
      piece(ctx, capsule(add(hip, [far ? -.03 : .03, 0]), k, .075, .06, far ? 221 : 231), col, 'rgba(0,0,0,.4)');
      piece(ctx, capsule(k, f, .058, .045, far ? 241 : 251), col, 'rgba(0,0,0,.4)');
      piece(ctx, cut([[f[0] - .05, f[1] - .055], [f[0] + .15, f[1] - .04], [f[0] + .16, f[1]], [f[0] - .06, f[1]]], .004, far ? 261 : 271), C.shoe, null);
      if (!far) brad(ctx, k, .012); };
    const handT = far => {
      const down = add(shoulder, [.06 + (far ? -.04 : 0), .58]);
      const reach = add(shoulder, [.6, -.02]);
      const low = s > .5 ? [.62, -.06] : add(shoulder, [.42, .5]);
      let h = [lerp(down[0], reach[0], P.reach), lerp(down[1], reach[1], P.reach)];
      if (!far) h = [lerp(h[0], low[0], P.low), lerp(h[1], low[1], P.low)];
      const knee = add(hip, [far ? .2 : .32, -.18]), r = sOut * clamp(1 - P.low * 2) * clamp(1 - P.reach * 2);   // sitting: hands come to rest on the knees
      return [lerp(h[0], knee[0], r), lerp(h[1], knee[1], r)];
    };
    const arm = far => { const tg = handT(far); const [e, h] = ik(add(shoulder, [far ? -.02 : .02, 0]), tg, .3, .29, 1);
      const col = far ? C.shirtFar : C.shirt;
      REC.n = far ? 'person.armFar' : 'person.arm'; mark(ctx, REC.n + '.elbow', e); mark(ctx, REC.n + '.hand', h);
      piece(ctx, capsule(add(shoulder, [far ? -.02 : .02, 0]), e, .055, .045, far ? 281 : 291), col, 'rgba(0,0,0,.4)');
      piece(ctx, capsule(e, h, .043, .036, far ? 301 : 311), col, 'rgba(0,0,0,.4)');
      const ang = Math.atan2(h[1] - e[1], h[0] - e[0]);
      ctx.save(); ctx.translate(h[0], h[1]); ctx.rotate(ang); piece(ctx, cut([[0, -.035], [.09, -.03], [.11, .0], [.08, .035], [0, .03]], .004, far ? 321 : 331), far ? C.skinFar : C.skin, 'rgba(0,0,0,.35)'); ctx.restore();
      if (!far) brad(ctx, e, .011); };
    leg(true); arm(true);
    ctx.save(); ctx.translate(hip[0], hip[1]); ctx.rotate(lean); REC.n = 'person.torso'; piece(ctx, TORSO, C.shirt, 'rgba(0,0,0,.45)'); ctx.restore();
    // head
    ctx.save(); ctx.translate(headC[0], headC[1]); ctx.rotate(lean * .6);
    REC.n = 'person.head'; mark(ctx, 'person.head', [0, 0]); mark(ctx, 'person.eye', [.055, -.015]); mark(ctx, 'person.mouth', [.07, .055]); mark(ctx, 'person.nose', [.13, .015]);
    piece(ctx, cut([[-.02, .08], [.05, .1], [.04, .16], [-.05, .16]], .004, 341), C.skin, null);
    piece(ctx, HEAD, C.skin, 'rgba(0,0,0,.4)');
    piece(ctx, cut([[-.11, -.02], [-.1, -.09], [-.03, -.13], [.06, -.12], [.11, -.06], [.07, -.075], [-.02, -.07], [-.06, -.02]], .004, 351), C.hair, null);
    piece(ctx, cut([[.1, -.02], [.135, .02], [.1, .035]], .003, 361), C.skin, 'rgba(0,0,0,.35)');
    ctx.beginPath(); ctx.arc(.055, -.015, .011, 0, 7); ctx.fillStyle = C.ink; ctx.fill();
    const m = clamp(P.mouth); ctx.beginPath(); ctx.ellipse(.07, .055, .022 + .008 * m, .004 + .022 * m, 0, 0, 7); ctx.fillStyle = m > .15 ? '#3a1712' : 'rgba(40,20,15,.8)'; ctx.fill();
    ctx.restore();
    leg(false);
    brad(ctx, hip, .014);
    arm(false); brad(ctx, shoulder, .014); brad(ctx, neck, .011); mark(ctx, 'person.hip', hip); mark(ctx, 'person.shoulder', shoulder); REC.n = '';
  }

  /* ------------------------------------------------------------------ the set */
  // world: x along the porch (threshold 0, porch +), y up in metres; screen via camera
  function camera(cam, W, H) { const ppm = 150 * cam.zoom, ox = cam.ox || 0, oy = cam.oy || 0; return { ppm, sx: x => (x - cam.x) * ppm + W / 2 + ox, sy: y => H * .84 - (y - cam.y) * ppm + oy }; }
  function drawSet(ctx, cam, S, W, H) {
    const K = camera(cam, W, H), ppm = K.ppm;
    ctx.save();
    // sky
    const g = ctx.createLinearGradient(0, cam.oy || 0, 0, (cam.oy || 0) + H); g.addColorStop(0, C.skyTop); g.addColorStop(.55, C.skyMid); g.addColorStop(.9, C.skyLow); ctx.fillStyle = g; ctx.fillRect(cam.ox || 0, cam.oy || 0, W, H);
    ctx.setTransform(ppm, 0, 0, -ppm, K.sx(0), K.sy(0));   // world units, y up
    const P = (pts, c, e, ts) => { piece(ctx, pts, c, e, ts || 1 / 2.2); };
    // moon and a tree in the yard, cut from paper
    ctx.save(); ctx.scale(1, -1);
    P(ellipse(5.4, -3.7, .26, .26, 26, 401, .03), '#f6ead0', null);
    P(cut([[4.6, 0], [4.75, -1.6], [4.55, -1.7], [4.8, -1.75], [4.6, -2.4], [5.05, -1.9], [5.35, -2.55], [5.3, -1.85], [5.6, -1.75], [5.25, -1.6], [5.3, 0]], .05, 411), '#24304a', null);
    P(cut([[2.2, .4], [8, .4], [8, 0.02], [2.2, 0.02]], .02, 421), C.ground, null);
    ctx.restore();
    // facade (house front) from far left to the corner at x = 2.25
    ctx.save(); ctx.scale(1, -1);
    P([[-6, -3.3], [2.25, -3.3], [2.25, 0], [-6, 0]], C.facade, null);
    ctx.strokeStyle = C.facadeLine; ctx.lineWidth = .012;
    for (let y = .18; y < 3.3; y += .2) { ctx.beginPath(); ctx.moveTo(-6, -y); ctx.lineTo(2.25, -y); ctx.stroke(); }
    P(cut([[2.12, -3.3], [2.3, -3.3], [2.3, 0], [2.12, 0]], .01, 431), C.trim, 'rgba(0,0,0,.25)');
    // window to the left of the door
    P(cut([[-2.55, -2.05], [-1.65, -2.05], [-1.65, -1.05], [-2.55, -1.05]], .01, 441), C.trim, 'rgba(0,0,0,.3)');
    P([[-2.47, -1.97], [-1.73, -1.97], [-1.73, -1.13], [-2.47, -1.13]], S.windowLit ? '#f2c46b' : '#55607a', null);
    ctx.fillStyle = C.trim; ctx.fillRect(-2.13, -1.97, .05, .84); ctx.fillRect(-2.47, -1.58, .74, .05);
    // the doorway: frame, lit inside, door panel narrowing toward its hinge as it opens
    const dw = .92, dh = 2.08, x0 = -dw / 2, x1 = dw / 2;
    const ig = ctx.createLinearGradient(0, -dh, 0, 0); ig.addColorStop(0, C.insideDeep); ig.addColorStop(1, C.inside);
    ctx.fillStyle = ig; ctx.fillRect(x0, -dh, dw, dh);
    // a glimpse inside: a lamp and the far wall's skirting
    ctx.fillStyle = 'rgba(120,70,20,.35)'; ctx.fillRect(x0, -.12, dw, .04);
    P(cut([[.12, -1.25], [.3, -1.25], [.26, -1.05], [.16, -1.05]], .01, 451), '#fff1c9', null); ctx.fillStyle = 'rgba(90,50,10,.6)'; ctx.fillRect(.2, -1.05, .02, .8);
    const open = clamp(S.door), pw = dw * lerp(.62, .07, ease(open));
    P(cut([[x0, -dh], [x0 + pw, -dh + .02 * open], [x0 + pw, -.01 * open], [x0, 0]], .006, 461), C.door, 'rgba(0,0,0,.4)');
    if (pw > .2) { ctx.fillStyle = C.doorDark; ctx.fillRect(x0 + pw * .15, -dh * .85, pw * .7, dh * .32); ctx.fillRect(x0 + pw * .15, -dh * .45, pw * .7, dh * .32); }
    ctx.beginPath(); ctx.arc(x0 + pw * .86, -1.0, .025, 0, 7); ctx.fillStyle = C.brad; ctx.fill();
    P(cut([[x0 - .12, -dh - .14], [x1 + .12, -dh - .14], [x1 + .12, 0], [x1, 0], [x1, -dh], [x0, -dh], [x0, 0], [x0 - .12, 0]], .008, 471), C.trim, 'rgba(0,0,0,.3)');
    // porch roof beam and post
    P(cut([[-6, -3.3], [5.0, -3.3], [5.0, -3.05], [-6, -3.05]], .01, 481), '#3d3843', null);
    P(cut([[4.66, -3.05], [4.8, -3.05], [4.8, 0], [4.66, 0]], .01, 491), C.trim, 'rgba(0,0,0,.3)');
    // light spilling out of the door onto the porch floor and the night
    const L = clamp(S.light);
    if (L > 0.01) {   // the doorway glows into the dusk
      ctx.save(); ctx.globalCompositeOperation = 'screen';
      const rg = ctx.createRadialGradient(0, -1.0, .3, 0, -1.0, 2.2); rg.addColorStop(0, `rgba(255,200,110,${.30 * L})`); rg.addColorStop(1, 'rgba(255,200,110,0)');
      ctx.fillStyle = rg; ctx.fillRect(-2.4, -3.2, 4.8, 3.2); ctx.restore();
    }
    ctx.restore();
    // porch floor boards (drawn slightly below 0 so feet stand on its top edge) and the sill
    ctx.save(); ctx.scale(1, -1);
    P(cut([[-6, 0], [4.95, 0], [4.95, .42], [-6, .42]], .01, 501), C.boards, null);
    ctx.strokeStyle = C.boardsLine; ctx.lineWidth = .01; for (let y = .1; y < .42; y += .1) { ctx.beginPath(); ctx.moveTo(-6, y); ctx.lineTo(4.95, y); ctx.stroke(); }
    for (let x = -5.7, i = 0; x < 4.9; x += .9, i++) { ctx.beginPath(); ctx.moveTo(x + (i % 2) * .45, 0); ctx.lineTo(x + (i % 2) * .45, .1); ctx.stroke(); }
    if (L > .01) { ctx.fillStyle = `rgba(255,205,120,${.28 * L})`; ctx.beginPath(); ctx.moveTo(x0 + pw, 0); ctx.lineTo(3.8, 0); ctx.lineTo(4.4, .42); ctx.lineTo(x0 + pw + .3, .42); ctx.closePath(); ctx.fill(); }
    P(cut([[x0 - .05, -.035], [x1 + .05, -.035], [x1 + .07, .02], [x0 - .07, .02]], .006, 511), '#8a6a4c', 'rgba(0,0,0,.35)');
    P(cut([[4.95, .0], [5.6, .0], [5.6, .2], [5.2, .2], [5.2, .42], [4.95, .42]], .01, 521), C.step, null);
    P([[-6, .42], [9, .42], [9, 3], [-6, 3]], '#1c1a22', null);
    ctx.strokeStyle = 'rgba(160,150,170,.18)'; ctx.lineWidth = .03;
    for (let x = -6; x < 5; x += .3) { ctx.beginPath(); ctx.moveTo(x, .45); ctx.lineTo(x + .6, 1.05); ctx.moveTo(x + .6, .45); ctx.lineTo(x, 1.05); ctx.stroke(); }
    ctx.restore();
    ctx.restore();
    return K;
  }

  // draw a puppet with a cut-out shadow (paper lifted off the backdrop)
  function puppet(ctx, K, x, face, scale, fn, shadow) {
    ctx.save();
    ctx.shadowColor = 'rgba(10,8,20,.42)'; ctx.shadowBlur = 8; ctx.shadowOffsetX = 5; ctx.shadowOffsetY = 6;
    ctx.setTransform(K.ppm * face * scale, 0, 0, K.ppm * scale, K.sx(x), K.sy(0));
    fn(ctx); ctx.restore();
    if (shadow) { ctx.save(); ctx.setTransform(K.ppm, 0, 0, K.ppm, K.sx(x), K.sy(0)); ctx.beginPath(); ctx.ellipse(0, .02, shadow, .03, 0, 0, 7); ctx.fillStyle = 'rgba(0,0,0,.22)'; ctx.fill(); ctx.restore(); }
  }

  /* ------------------------------------------------------------------ environment text: paper tags pinned to the world */
  function tag(ctx, K, anchor, at, lines, o) {
    o = o || {}; const a = [K.sx(anchor[0]), K.sy(anchor[1])], p = [K.sx(at[0]), K.sy(at[1])];
    const alpha = o.alpha === undefined ? 1 : o.alpha; if (alpha <= .01) return;
    ctx.save(); ctx.globalAlpha = alpha; ctx.setTransform(1, 0, 0, 1, 0, 0);
    const fs = o.size || 17, lh = fs * 1.32;
    ctx.font = `600 ${fs}px "JetBrains Mono", monospace`;
    const w = Math.max(...lines.map(l => ctx.measureText(typeof l === 'string' ? l : l.t).width + (l.bar !== undefined ? 92 : 0))) + 26, h = lines.length * lh + 18;
    const x = clamp(p[0] - w / 2, 12, (o.W || 1280) - w - 12), y = clamp(p[1] - h, o.top || 86, (o.H || 720) - h - 90);
    ctx.strokeStyle = 'rgba(251,247,238,.75)'; ctx.lineWidth = 1.5; ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(clamp(p[0], x + 14, x + w - 14), y + h); ctx.lineTo(a[0], a[1]); ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.arc(a[0], a[1], 4, 0, 7); ctx.fillStyle = C.stamp; ctx.fill();
    ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.rotate(o.rot || 0); ctx.translate(-(x + w / 2), -(y + h / 2));
    ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 6; ctx.shadowOffsetY = 3;
    ctx.fillStyle = C.paper; ctx.beginPath(); ctx.moveTo(x + 10, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + h); ctx.lineTo(x, y + h); ctx.lineTo(x, y + 10); ctx.closePath(); ctx.fill();
    ctx.shadowColor = 'transparent';
    if (o.flash) { ctx.fillStyle = `rgba(212,42,30,${.22 * o.flash})`; ctx.fill(); }
    ctx.beginPath(); ctx.arc(x + 12, y + 11, 3.2, 0, 7); ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fill();
    lines.forEach((l, i) => {
      const L = typeof l === 'string' ? { t: l } : l;
      ctx.fillStyle = L.c || (i === 0 ? C.ink : '#4a4237'); ctx.font = `${i === 0 ? 700 : 500} ${fs}px "JetBrains Mono", monospace`;
      ctx.fillText(L.t, x + 13 + (i === 0 ? 9 : 0), y + 14 + lh * (i + .72));
      if (L.bar !== undefined) { const bw = 70, bx = x + w - bw - 12, by = y + 14 + lh * (i + .2); ctx.fillStyle = 'rgba(0,0,0,.12)'; ctx.fillRect(bx, by, bw, 8); ctx.fillStyle = L.barc || C.teal; ctx.fillRect(bx, by, bw * clamp(L.bar), 8); }
    });
    ctx.restore(); ctx.restore();
  }
  function bubble(ctx, K, at, text, o) {
    o = o || {}; const alpha = o.alpha === undefined ? 1 : o.alpha; if (alpha <= .01) return;
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = alpha;
    const fs = o.loud ? 30 : 23; ctx.font = `${o.loud ? '700' : 'italic 400'} ${fs}px Literata, Georgia, serif`;
    const w = ctx.measureText(text).width + 34, h = fs + 26, x = K.sx(at[0]) + 14, y = K.sy(at[1]) - h - 22;
    ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = 6; ctx.shadowOffsetY = 3; ctx.fillStyle = C.paper;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + h); ctx.lineTo(x + 34, y + h); ctx.lineTo(x + 4, y + h + 20); ctx.lineTo(x + 16, y + h); ctx.lineTo(x, y + h); ctx.closePath(); ctx.fill();
    ctx.shadowColor = 'transparent'; ctx.fillStyle = o.loud ? C.stamp : C.ink; ctx.fillText(text, x + 17, y + h / 2 + fs * .36); ctx.restore();
  }

  // the right jamb of the doorway, drawn again over a dog lying across the sill so it reads as through the door, not in front of it
  function jamb(ctx, K) {
    ctx.save(); ctx.setTransform(K.ppm, 0, 0, K.ppm, K.sx(0), K.sy(0));
    piece(ctx, cut([[.46, -2.08], [.58, -2.08], [.58, 0], [.46, 0]], .006, 473), C.trim, 'rgba(0,0,0,.3)', 1 / 2.2); ctx.restore();
  }
  return { STYLE, REC, mark, jamb, C, lerp, clamp, ease, hash, DogAnim, PersonAnim, drawDog, drawPerson, drawSet, puppet, tag, bubble, camera, piece, cut, ellipse };
});
