/* SCION-26 · PixiJS archive stage.  A GPU 2D scene graph of small transparent archive fragments.
   Runtime: PixiJS 7.4.2 (MIT), WebGL 1 in headless Chromium (SwiftShader).  Driven frame by frame by build/render.js.

   Coordinates.  World in metres: x along the porch (threshold 0, steps 4.9; the score's x), y up, z depth (the house wall is
   the plane z = 0, the porch runs toward the viewer, z < 0; inside the house z > 0).  The camera is a fixed, pitched
   orthographic stage camera:  screen = (OX + S*x,  FY - S*(y*cos + z*sin)).  Depth key = z*cos - y*sin (bigger is farther).
   Time base: scene frame i (0..767) at 24 fps, aligned to the score frame i.

   Scene graph (six depth planes, back to front):
     sky        gradient + cloud-bank cut-outs + star cut-outs + Quick, Draw! chalk moon
     yard       chalk trees and fence, fog sprites
     house      clapboard wall of fence-rail strips, door trim, window; INTERIOR container (render behind an alpha mask = the
                door opening) holding the room, the lantern, the picture, pinned doodles and the door leaf mesh
     floor      porch boards, sill, LIGHT render texture (door light polygon + shadow fragments, blurred) added on top,
                contact shadows
     actors     the person (render texture + consolidation filter), the archive hand, the crate, the dog (render texture +
                consolidation filter)
     front      porch edge, hanging leaves
   then the whole stage goes into STAGE render texture -> grain/flicker/vignette filter -> screen. */
'use strict';
const W = 1280, H = 720, FPS = 24, NS = 768;
const S = 200, OX = 330, FY = 520, SIN = 0.36, COS = Math.sqrt(1 - SIN * SIN);
const proj = (p) => [OX + S * p.x, FY - S * (p.y * COS + p.z * SIN)];
const dep = (p) => p.z * COS - p.y * SIN;
const TOCAM = { x: 0, y: SIN, z: -COS };
const V = (x, y, z) => ({ x, y, z });
const add = (a, b) => V(a.x + b.x, a.y + b.y, a.z + b.z), sub = (a, b) => V(a.x - b.x, a.y - b.y, a.z - b.z);
const mul = (a, k) => V(a.x * k, a.y * k, a.z * k), dot = (a, b) => a.x * b.x + a.y * b.y + a.z * b.z;
const cross = (a, b) => V(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x);
const len = (a) => Math.hypot(a.x, a.y, a.z), norm = (a) => { const l = len(a) || 1; return mul(a, 1 / l); };
const lerpV = (a, b, t) => V(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t);
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v)), lerp = (a, b, t) => a + (b - a) * t;
const ss = (a, b, t) => { const u = clamp((t - a) / (b - a)); return u * u * (3 - 2 * u); };
const D2R = Math.PI / 180;
function RNG(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function interp(x, xs, ys) { if (x <= xs[0]) return ys[0]; for (let k = 1; k < xs.length; k++) if (x <= xs[k]) return lerp(ys[k - 1], ys[k], (x - xs[k - 1]) / (xs[k] - xs[k - 1])); return ys[ys.length - 1]; }
const rgbHex = (c) => (Math.round(clamp(c[0]) * 255) << 16) | (Math.round(clamp(c[1]) * 255) << 8) | Math.round(clamp(c[2]) * 255);

let R, TEX = {}, CLS = {}, SC, ATL, DRAWS = 0;
const pick = (cls, r) => TEX[CLS[cls][Math.floor(r() * CLS[cls].length)]];

/* ------------------------------------------------------------------ the fragment body (shared by dog and person) */
class FragBody {
  constructor(seed, cellPx) { this.r = RNG(seed); this.frags = []; this.c = new PIXI.Container(); this.c.sortableChildren = true; this.cell = cellPx; }
  // n surface fragments on a capsule part; u in [-cap, 1+cap]; th around the axis
  capsule(part, n, size, classes, color, opt = {}) {
    for (let k = 0; k < n; k++) {
      const r = this.r, cls = classes[Math.floor(r() * classes.length)];
      const f = { part, kind: 'surf', u: lerp(-0.14, 1.14, (k + r()) / n), th: r() * 2 * Math.PI, size: size * lerp(0.85, 1.2, r()),
        rot: (r() - 0.5) * 0.9, color, jit: (r() - 0.5) * 0.12, sp: new PIXI.Sprite(pick(cls, r)), side: opt.side || 0 };
      f.sp.anchor.set(0.5); this.c.addChild(f.sp); this.frags.push(f);
    }
  }
  core(part, n, size, color) {   // larger dark fills along the axis, drawn just behind the surface (no holes)
    for (let k = 0; k < n; k++) {
      const r = this.r, f = { part, kind: 'core', u: (k + 0.5) / n, th: 0, size, rot: r() * 6.28, color, jit: 0, sp: new PIXI.Sprite(TEX.soft) };
      f.sp.anchor.set(0.5); this.c.addChild(f.sp); this.frags.push(f);
    }
  }
  point(part, size, tex, color, opt = {}) {
    const f = { part, kind: 'point', size, rot: opt.rot || 0, color, jit: 0, sp: new PIXI.Sprite(tex), stretch: opt.stretch || 1, front: opt.front || 0 };
    f.sp.anchor.set(0.5); this.c.addChild(f.sp); this.frags.push(f);
    return f;
  }
  // G: part -> {p0,p1,r0:[lat,up],r1:[lat,up],hint} or for points {p, n, vis}
  update(G, env, off) {
    const geo = {};
    for (const k in G) {
      const g = G[k]; if (g.p) continue;
      const ax = sub(g.p1, g.p0), L = len(ax), a = L > 1e-6 ? mul(ax, 1 / L) : V(1, 0, 0);
      let e2 = sub(g.hint, mul(a, dot(g.hint, a))); if (len(e2) < 1e-4) e2 = Math.abs(a.y) < 0.9 ? V(0, 1, 0) : V(1, 0, 0), e2 = sub(e2, mul(a, dot(e2, a)));
      e2 = norm(e2); const e1 = cross(a, e2);
      const s0 = proj(g.p0), s1 = proj(g.p1), pl = Math.hypot(s1[0] - s0[0], s1[1] - s0[1]);
      geo[k] = { a, e1, e2, L, ang: Math.atan2(s1[1] - s0[1], s1[0] - s0[0]), fs: clamp(pl / (S * Math.max(L, 1e-3))) };
    }
    let measured = [];
    for (const f of this.frags) {
      const g = G[f.part]; if (!g) { f.sp.visible = false; continue; }
      let p, n, ang = f.rot, stretch = 1, squash = 1;
      if (f.kind === 'point') {
        if (g.vis === 0) { f.sp.visible = false; continue; }
        p = g.p; n = g.n || TOCAM; ang = (g.ang || 0) + f.rot; stretch = f.stretch;
      } else {
        const q = geo[f.part];
        let u = f.u, ext = 0, rs = 1; const capL = Math.max(g.r0[1], g.r1[1]) * 0.9;
        if (u < 0) { const k = u / 0.14; ext = k * capL; rs = Math.sqrt(Math.max(0, 1 - k * k)); u = 0; }
        if (u > 1) { const k = (u - 1) / 0.14; ext = k * capL; rs = Math.sqrt(Math.max(0, 1 - k * k)); u = 1; }
        const rl = lerp(g.r0[0], g.r1[0], u) * rs, ru = lerp(g.r0[1], g.r1[1], u) * rs;
        const c = add(lerpV(g.p0, g.p1, u), mul(q.a, ext));
        if (f.kind === 'core') { p = c; n = TOCAM; }
        else {
          const ct = Math.cos(f.th), st = Math.sin(f.th);
          p = add(c, add(mul(q.e1, ct * rl), mul(q.e2, st * ru)));
          n = norm(add(add(mul(q.e1, ct), mul(q.e2, st)), mul(q.a, ext / (capL || 1))));
          if (p.y < 0.006) p.y = 0.006;
        }
        ang = q.ang + f.rot; stretch = 1 + 0.35 * q.fs; squash = 1 - 0.12 * q.fs;
        if (f.kind === 'core') { stretch = 1; squash = 1; }
        f._st = f.kind === 'surf' ? Math.sin(f.th) : 0;
        f._r = Math.max(rl, ru);
      }
      const sp = f.sp, s = proj(p);
      sp.visible = true;
      sp.position.set(s[0] - off[0], s[1] - off[1]);
      sp.rotation = ang;
      const sz = (f.kind === 'core' ? f._r * 2.6 : f.size) * S / this.cell;
      sp.scale.set(sz * stretch, sz * squash);
      sp.zIndex = -(dep(p) + (f.kind === 'core' ? f._r * 0.9 : 0) - (f.front || 0)) * 1000;
      const base = typeof f.color === 'function' ? f.color(f) : f.color;
      sp.tint = rgbHex(shade(base, p, n, env, f.kind === 'core', f.jit));
      if (f.kind === 'surf' && f.part !== 'tail') measured.push(p);
    }
    return measured;
  }
}

/* ------------------------------------------------------------------ light: dusk sky + the door */
const LAMP = V(-0.1, 2.3, 1.4);
function shade(c, p, n, env, isCore, jit) {
  const sky = 0.42 + 0.26 * Math.max(0, n.y);
  const key = 0.32 * Math.max(0, dot(n, norm(V(0.55, 0.55, 0.6))));
  const vc = Math.max(0, dot(n, TOCAM));
  let k = (sky + key) * (0.62 + 0.38 * vc) * (1 + jit);
  if (isCore) k *= 0.8;
  const dc = env.cool;
  let r = c[0] * k * dc[0], g = c[1] * k * dc[1], b = c[2] * k * dc[2];
  if (env.door > 0) {
    const toL = sub(V(0, 0.9, 0.25), p), d = len(toL), l = mul(toL, 1 / d);
    const pool = env.inPool ? env.inPool(p) : 1;
    const I = env.door * (0.25 + 1.5 * pool) / (1 + 0.55 * d * d) * Math.max(0, dot(n, l) * 0.8 + 0.2) * (isCore ? 0.4 : 1);
    r += c[0] * I * 1.25; g += c[1] * I * 0.9; b += c[2] * I * 0.55;
  }
  const G = env.gain || 1; r *= G; g *= G; b *= G;
  const m = Math.max(r, g, b, 1); return [r / m, g / m, b / m];
}

/* ------------------------------------------------------------------ the dog: timeline (pose per frame) */
const DOG = {};
function zPath(x) { return -0.85 + 0.70 * ss(1.95, 0.5, x); }
function buildDogTimeline() {
  const F = SC.frames, n = NS;
  const T = []; let phase = 0;
  for (let i = 0; i < n; i++) {
    const f = F[i], t = f.t, a = f.dog.act, x = f.dog.x;
    const xb = x - 0.24 * ss(22.6, 24.6, t);   // the body centre creeps forward onto the sill as it lies
    const z = zPath(xb);
    // body yaw (deg). 168 = toward the door. Turn away through the camera side (270) to 345; back the same way.
    let psi = 168;
    if (t >= 3.44 && t < 7.86) psi = lerp(168, 345, ss(3.44, 3.98, t));
    if (t >= 7.86) psi = t < 8.75 ? lerp(345, 528, ss(8.0, 8.75, t)) : 168;     // rises, then turns back through its far side (528 = 168 + 360)
    if (t >= 14.6) {
      const dzdx = (zPath(xb + 0.01) - zPath(xb - 0.01)) / 0.02;
      let tan = Math.atan2(-dzdx, -1) / D2R; if (tan < 0) tan += 360;   // heading when moving toward -x along the path
      psi = lerp(168, tan, ss(14.6, 15.3, t));
      psi = lerp(psi, 138, ss(23.4, 24.3, t));           // lies across the sill in depth
    }
    // head yaw, world
    let psiH = psi;
    if (t >= 3.3 && t < 7.4) psiH = t < 3.98 ? lerp(168, 345, ss(3.38, 3.88, t)) : psi;       // the head goes first
    // head-led look back: the head swings over the far shoulder (never face-on to the camera) to point at the door while the body is still down
    if (t >= 7.38 && t < 8.75) psiH = Math.max(lerp(345, 530, ss(7.38, 7.6, t)), psi);
    if (t >= 8.0 && t < 8.75) psiH = lerp(530, 528, ss(8.0, 8.75, t));
    if (t >= 23.5) psiH = lerp(psi, 92, a.look);                                             // looking in: muzzle into the room (+z)
    // head pitch (neck angle, deg)
    let hd = a.head;
    let neck = interp(hd, [0, 0.15, 0.45, 0.7, 0.9, 1.2], [-52, -46, -34, 6, 38, 48]);
    if (t > 7.4 && t < 7.9) neck = Math.max(neck, lerp(-46, 42, ss(7.4, 7.7, t)));
    if (t > 3.4 && t < 4.1) neck = Math.max(neck, 12 * Math.sin(Math.PI * clamp((t - 3.4) / 0.7)));        // head comes up with the look
    if (t >= 14.6 && t < 23.8) neck = Math.min(neck, lerp(-30, -46, ss(14.6, 15.2, t)));     // head low (below the back) for the whole approach
    neck = lerp(neck, -40, a.rest);
    if (t > 7.95 && t < 8.85) neck = Math.min(neck, lerp(38, 14, Math.sin(Math.PI * clamp((t - 7.95) / 0.9))));   // keep the head level through the turn (no giraffe)
    if (t >= 23.5) neck = Math.min(neck, lerp(8, 2, a.look));
    let lie = a.lie;
    if (t >= 7.0 && t < 9.0) lie = 1 - ss(7.74, 8.1, t);                                      // stays down while the head looks; then rises
    if (t >= 23.0) lie = ss(23.70, 24.30, t);                                                // lies down on the sill, own timing
    const crouch = a.crouch;
    T.push({ i, t, x: xb, xs: x, z, psi, psiH, neck, lie, crouch, rest: a.rest, look: a.look, ear: (t >= 14.6 && t < 23.8) ? Math.min(a.ear, 0.2) : a.ear, tail: a.tail, wag: a.wag, moving: a.moving });
  }
  // gait phase from distance travelled + turning (feet account for travel and for turning on the spot)
  for (let i = 0; i < n; i++) {
    if (i > 0) { const p = T[i - 1], c = T[i]; phase += (Math.hypot(c.x - p.x, c.z - p.z) + 0.24 * Math.abs(((c.psi - p.psi + 540) % 360) - 180) * D2R) * 2 * Math.PI / 0.55; }
    T[i].phase = phase;
  }
  DOG.T = T;
  // feet: plant each foot at the neutral spot it will have at mid-stance, swing between plants
  const LEGS = [{ k: 'LH', off: 0, fore: false, side: 1 }, { k: 'LF', off: 0.25, fore: true, side: 1 }, { k: 'RH', off: 0.5, fore: false, side: -1 }, { k: 'RF', off: 0.75, fore: true, side: -1 }];
  const BETA = 0.62;
  DOG.LEGS = LEGS;
  for (const L of LEGS) {
    const st = T.map(q => ((q.phase / (2 * Math.PI) + L.off) % 1) < BETA);
    const neutral = (q) => { const fw = V(Math.cos(q.psi * D2R), 0, Math.sin(q.psi * D2R)), lat = cross(fw, V(0, 1, 0)); return add(V(q.x, 0, q.z), add(mul(fw, L.fore ? 0.235 : -0.245), mul(lat, 0.075 * L.side))); };
    const ivs = []; let s0 = null;
    for (let i = 0; i <= n; i++) { if (i < n && st[i]) { if (s0 === null) s0 = i; } else if (s0 !== null) { ivs.push([s0, i - 1]); s0 = null; } }
    const plant = ivs.map(([a, b]) => neutral(T[Math.round((a + b) / 2)]));
    const foot = new Array(n);
    for (let j = 0; j < ivs.length; j++) for (let i = ivs[j][0]; i <= ivs[j][1]; i++) foot[i] = { p: plant[j], lift: 0 };
    for (let i = 0; i < n; i++) if (!foot[i]) {
      const jb = ivs.findIndex(v => v[0] > i), ja = jb === -1 ? ivs.length - 1 : jb - 1;
      if (ja < 0 || jb === -1) { foot[i] = { p: neutral(T[i]), lift: 0 }; continue; }
      const e = ivs[ja][1], s = ivs[jb][0], u = (i - e) / (s - e);
      foot[i] = { p: lerpV(plant[ja], plant[jb], ss(0, 1, u)), lift: 0.075 * Math.sin(Math.PI * u) };
    }
    L.foot = foot;
  }
}

/* the dog's skeleton at frame i -> capsule parts (world) */
function dogParts(i) {
  const q = DOG.T[i], t = q.t;
  const fw = V(Math.cos(q.psi * D2R), 0, Math.sin(q.psi * D2R)), up = V(0, 1, 0), lat = cross(fw, up);
  const base = V(q.x, 0, q.z);
  const L = (a, b, c) => add(base, add(mul(fw, a), add(mul(up, b), mul(lat, c))));
  const lie = q.lie, cr = q.crouch * (1 - lie);
  const hb = lerp(0.43 - 0.085 * cr, 0.155, lie);
  const breathe = 0.004 * Math.sin(t * 2 * Math.PI * (lie > 0.5 ? 0.35 : 0.5));
  const chest = L(0.19, hb + 0.015 + breathe, 0), mid = L(-0.03, hb + 0.03 + breathe * 0.5, 0), rump = L(-0.25, hb + 0.035 - 0.05 * cr + 0.01 * lie, 0);
  const G = {};
  G.torsoF = { p0: mid, p1: chest, r0: [0.08, 0.105], r1: [0.098, 0.14 - 0.02 * lie], hint: up };
  G.torsoR = { p0: rump, p1: mid, r0: [0.09, 0.112 - 0.015 * lie], r1: [0.08, 0.105], hint: up };
  // neck and head; yaw local = head yaw - body yaw
  const yl = (q.psiH - q.psi) * D2R, nk = q.neck * D2R;
  const hfw = V(Math.cos(q.psiH * D2R), 0, Math.sin(q.psiH * D2R)), hlat = cross(hfw, up);
  const n0 = L(0.27, hb + 0.09 - 0.02 * lie, 0);
  const ndir = norm(add(mul(norm(add(mul(fw, Math.cos(yl * 0.72)), mul(lat, Math.sin(yl * 0.72)))), Math.cos(nk)), mul(up, Math.sin(nk))));
  let n1 = add(n0, mul(ndir, 0.2));
  if (n1.y < 0.11) n1.y = 0.11;
  const hp = (q.neck * 0.45 - 18) * D2R;    // muzzle pitch
  const hdir = norm(add(mul(hfw, Math.cos(hp)), mul(up, Math.sin(hp))));
  const skull = add(n1, add(mul(hdir, 0.035), mul(up, 0.03)));
  let muz = add(skull, mul(hdir, 0.15));
  if (muz.y < 0.04) muz.y = 0.04;
  G.neck = { p0: n0, p1: n1, r0: [0.072, 0.085], r1: [0.058, 0.064], hint: fw };
  G.skull = { p0: add(skull, mul(hdir, -0.03)), p1: add(skull, mul(hdir, 0.02)), r0: [0.062, 0.066], r1: [0.064, 0.066], hint: up };
  G.muzzle = { p0: add(skull, mul(hdir, 0.03)), p1: muz, r0: [0.042, 0.044], r1: [0.024, 0.026], hint: up };
  // ears: base on the skull, tip pricked (ear 1) or folded back (ear 0)
  const ear = clamp(q.ear, 0, 1);
  for (const sd of [1, -1]) {
    const eb = add(skull, add(mul(up, 0.05), add(mul(hdir, -0.015), mul(hlat, 0.036 * sd))));
    const tipDir = norm(add(add(mul(up, lerp(0.15, 1.0, ear)), mul(hdir, lerp(-1.0, -0.15, ear))), mul(hlat, 0.35 * sd)));
    G['ear' + (sd > 0 ? 'L' : 'R')] = { p0: eb, p1: add(eb, mul(tipDir, 0.085)), r0: [0.03, 0.026], r1: [0.006, 0.006], hint: hdir };
  }
  // eyes + nose (points; eyes only on the side facing the camera)
  for (const sd of [1, -1]) {
    const ep = add(skull, add(mul(hdir, 0.05), add(mul(up, 0.022), mul(hlat, 0.042 * sd))));
    const en = norm(add(mul(hlat, sd), mul(hdir, 0.6)));
    G['eye' + (sd > 0 ? 'L' : 'R')] = { p: ep, n: en, vis: dot(en, TOCAM) > 0.15 ? 1 : 0, ang: 0 };
  }
  G.nose = { p: add(muz, mul(hdir, 0.006)), n: hdir, vis: 1, ang: 0 };
  // tail: 4-segment chain
  const tl = q.tail, wagA = q.wag * 0.6 * Math.sin(t * 2 * Math.PI * 2.1);
  let tp = L(-0.33, hb + 0.07 - 0.04 * cr, 0), tang = lerp(25, -75, tl / 1.35) * D2R;
  if (lie > 0.5) tang = lerp(tang, -8, ss(0.5, 1, lie));
  const camSide = dot(lat, TOCAM) >= 0 ? 1 : -1, lw = ss(0.5, 1, lie);   // a lying tail curls round on the camera side
  for (let k = 0; k < 4; k++) {
    const a2 = tang - k * 0.18 * (1 - tl / 1.35 * 0.5) + k * 0.12 * lw;
    const sway = wagA * (k + 1) / 4 + camSide * (0.9 + 0.3 * (k / 3)) * lw;
    const dir = norm(add(add(mul(fw, -Math.cos(a2) * Math.cos(sway)), mul(up, Math.sin(a2))), mul(lat, Math.sin(sway))));
    let tq = add(tp, mul(dir, 0.085)); if (tq.y < 0.02) tq.y = 0.02;
    G['tail' + k] = { p0: tp, p1: tq, r0: [0.042 - k * 0.007, 0.046 - k * 0.007], r1: [0.035 - k * 0.007, 0.038 - k * 0.007], hint: up };
    tp = tq;
  }
  // legs (IK). Fore: shoulder->elbow->paw, elbow points back. Hind: hip->stifle->hock->paw, stifle forward.
  const feet = [];
  for (const Lg of DOG.LEGS) {
    const sd = Lg.side, fo = Lg.fore;
    const hip = fo ? L(0.2, hb - 0.03, 0.062 * sd) : L(-0.235, hb - 0.0 - 0.04 * cr, 0.068 * sd);
    const fe = Lg.foot[i];
    let paw = add(fe.p, V(0, fe.lift, 0));
    const lieP = fo ? L(0.47, 0.03, 0.06 * sd) : L(0.05, 0.03, (sd > 0 ? 0.16 : 0.10) * sd);
    const wl = ss(0, 0.85, lie);
    paw = lerpV(paw, lieP, wl);
    let hint = fo ? mul(fw, -1) : fw;
    if (wl > 0) hint = norm(lerpV(hint, fo ? add(mul(fw, -1), mul(up, -0.6)) : add(add(mul(fw, 0.6), mul(lat, 0.9 * sd)), mul(up, -0.2)), wl));
    let end = paw, L1, L2, hock = null;
    if (fo) { L1 = 0.19; L2 = 0.24; }
    else { hock = add(paw, lerpV(add(mul(fw, -0.05), mul(up, 0.115)), add(mul(fw, -0.12), mul(up, 0.02)), wl)); end = hock; L1 = 0.2; L2 = 0.17; }
    let d = sub(end, hip), dl = len(d); const dn = mul(d, 1 / dl); dl = clamp(dl, 0.04, L1 + L2 - 0.002);
    const aa = (L1 * L1 + dl * dl - L2 * L2) / (2 * dl), hh = Math.sqrt(Math.max(0, L1 * L1 - aa * aa));
    const bend = norm(sub(hint, mul(dn, dot(hint, dn))));
    const knee = add(hip, add(mul(dn, aa), mul(bend, hh)));
    const endR = add(hip, mul(dn, dl));
    const kk = Lg.k;
    G[kk + 'u'] = { p0: hip, p1: knee, r0: fo ? [0.05, 0.06] : [0.06, 0.075], r1: [0.034, 0.036], hint: fw };
    G[kk + 'l'] = { p0: knee, p1: endR, r0: [0.026, 0.028], r1: [0.019, 0.02], hint: fw };
    if (!fo) G[kk + 'm'] = { p0: endR, p1: paw, r0: [0.019, 0.02], r1: [0.017, 0.018], hint: fw };
    const pawTip = add(paw, mul(fw, 0.035)); pawTip.y = Math.max(pawTip.y, 0.012);
    G[kk + 'p'] = { p0: add(paw, V(0, 0.012, 0)), p1: add(pawTip, V(0, 0.004, 0)), r0: [0.02, 0.016], r1: [0.017, 0.013], hint: up };
    feet.push({ p: paw, down: fe.lift < 0.01 || wl > 0.5, side: sd });
  }
  return { G, feet, fw, lat, chest, rump, skull, muz, hdir, q };
}

/* the dog's fragments: about 600 small cut pieces */
function buildDog() {
  const B = new FragBody(2601, 48);
  const coat = [1.0, 0.78, 0.52], saddle = [0.55, 0.42, 0.30], pale = [1.0, 0.86, 0.64], darkC = [0.22, 0.18, 0.16];
  const torsoCol = (f) => f._st > 0.55 ? saddle : f._st < -0.45 ? pale : coat;
  const furs = ['fur_dog', 'fur_dog', 'fur_lion', 'fur_dog'];
  B.core('torsoF', 6, 0, [0.66, 0.5, 0.36]); B.core('torsoR', 6, 0, [0.66, 0.5, 0.36]);
  B.capsule('torsoF', 120, 0.07, furs, torsoCol); B.capsule('torsoR', 110, 0.07, furs, torsoCol);
  B.core('neck', 3, 0, [0.66, 0.5, 0.36]);
  B.capsule('neck', 40, 0.06, furs, (f) => f._st > 0.4 ? saddle : coat);
  const Hd = new FragBody(2603, 48); B.head = Hd;    // the head is its own layer: own render texture, own outline
  Hd.core('skull', 2, 0, [0.66, 0.5, 0.36]); Hd.core('muzzle', 2, 0, [0.3, 0.24, 0.2]);
  Hd.capsule('skull', 46, 0.05, ['fur_dog', 'fur_lion'], (f) => f._st > 0.3 ? [0.70, 0.52, 0.36] : coat);
  Hd.capsule('muzzle', 26, 0.04, ['fur_dog', 'fur_lion'], (f) => f.u > 0.75 ? darkC : [0.80, 0.62, 0.46]);
  for (const e of ['earL', 'earR']) { Hd.capsule(e, 12, 0.04, ['dark'], [0.42, 0.32, 0.26]); Hd.core(e, 2, 0, [0.25, 0.2, 0.17]); }
  for (let k = 0; k < 4; k++) { B.core('tail' + k, 1, 0, [0.45, 0.35, 0.26]); B.capsule('tail' + k, 10, 0.045, ['fur_lion', 'fur_dog'], k >= 2 ? saddle : [0.8, 0.6, 0.42]); }
  for (const kk of ['LH', 'LF', 'RH', 'RF']) {
    B.core(kk + 'u', 3, 0, [0.62, 0.48, 0.34]); B.core(kk + 'l', 7, 0, [0.7, 0.58, 0.44]); B.core(kk + 'p', 2, 0, [0.5, 0.4, 0.3]);
    if (kk[1] === 'H') B.core(kk + 'm', 5, 0, [0.7, 0.58, 0.44]);
    B.capsule(kk + 'u', 20, 0.045, furs, coat);
    B.capsule(kk + 'l', 12, 0.028, ['fur_lion', 'fur_dog'], [0.95, 0.82, 0.64]);
    if (kk[1] === 'H') B.capsule(kk + 'm', 7, 0.026, ['fur_lion'], [0.95, 0.82, 0.64]);
    B.capsule(kk + 'p', 4, 0.024, ['fur_dog'], [0.62, 0.5, 0.38]);
  }
  Hd.point('eyeL', 0.026, TEX.dot, [0.05, 0.04, 0.03], { front: 0.03 }); Hd.point('eyeR', 0.026, TEX.dot, [0.05, 0.04, 0.03], { front: 0.03 });
  Hd.point('nose', 0.04, TEX[CLS.dark[3]], [0.1, 0.08, 0.07], { front: 0.02 });
  return B;
}

/* ------------------------------------------------------------------ the person (profile, facing the porch) */
const PER = {};
function personPose(i) {
  const f = SC.frames[i], t = f.t, p = f.person;
  // own staging: steps aside 5.40-6.30 (sidesteps toward -x and out onto the porch), sits 5.9-7.2
  const walkU = ss(5.40, 6.30, t);
  const x = lerp(-0.28, -1.25, walkU), z = lerp(0.12, -0.32, walkU);
  const sit = ss(5.95, 7.0, t);
  const reach = p.reach, low = ss(6.75, 7.35, t), call = p.voice === 'call' ? 1 : 0, soft = p.voice === 'soft' ? 1 : 0;
  return { t, x, z, sit, reach, low, call, soft, walkU, mouth: p.mouth };
}
function personParts(i) {
  const q = personPose(i), t = q.t;
  const fw = V(1, 0, 0), up = V(0, 1, 0), lat = V(0, 0, -1);    // facing +x, near side toward the camera
  const base = V(q.x, 0, q.z);
  const L = (a, b, c) => add(base, V(a, b, -c));
  const step = Math.sin(q.walkU * Math.PI * 4) * (q.walkU > 0 && q.walkU < 1 ? 1 : 0);
  const lean = (5 * q.call + 18 * q.reach + 26 * q.low * q.sit + 4 * q.soft) * D2R;
  const hipS = L(0, 0.93, 0), hipC = L(-0.07, 0.47, 0);
  const hip = lerpV(hipS, hipC, q.sit);
  const tlen = 0.55, tdir = V(Math.sin(lean), Math.cos(lean), 0);
  const sh = add(hip, mul(tdir, tlen));
  const neckT = add(sh, mul(tdir, 0.1));
  const headC = add(neckT, add(mul(tdir, 0.11), V(0.03 + 0.03 * q.call, 0, 0)));
  const G = {};
  G.ptorso = { p0: hip, p1: sh, r0: [0.13, 0.15], r1: [0.15, 0.13], hint: fw };
  G.pneck = { p0: sh, p1: neckT, r0: [0.05, 0.05], r1: [0.045, 0.045], hint: fw };
  G.phead = { p0: add(headC, V(-0.02, -0.02, 0)), p1: add(headC, V(0.02, 0.03, 0)), r0: [0.09, 0.1], r1: [0.085, 0.09], hint: fw };
  G.pnose = { p0: add(headC, V(0.07, 0.0, 0)), p1: add(headC, V(0.1, -0.02, 0)), r0: [0.025, 0.025], r1: [0.015, 0.015], hint: fw };
  // legs
  const legs = [];
  for (const sd of [1, -1]) {
    const hp = add(hip, V(0, -0.02, -0.08 * sd));
    let foot = add(base, V(0.04 + 0.12 * step * sd, 0.05, -0.09 * sd));
    let footSit = add(base, V(0.4, 0.05, -0.1 * sd));
    foot = lerpV(foot, footSit, q.sit);
    const lift = q.walkU > 0 && q.walkU < 1 ? Math.max(0, Math.sin(q.walkU * Math.PI * 4 + (sd > 0 ? 0 : Math.PI))) * 0.08 : 0;
    foot = add(foot, V(0, lift, 0));
    const L1 = 0.46, L2 = 0.44; const d = sub(foot, hp); let dl = len(d); const dn = mul(d, 1 / dl); dl = clamp(dl, 0.05, L1 + L2 - 0.002);
    const aa = (L1 * L1 + dl * dl - L2 * L2) / (2 * dl), hh = Math.sqrt(Math.max(0, L1 * L1 - aa * aa));
    const hint = fw; const bend = norm(sub(hint, mul(dn, dot(hint, dn))));
    const knee = add(hp, add(mul(dn, aa), mul(bend, hh))), ank = add(hp, mul(dn, dl));
    const k = sd > 0 ? 'N' : 'F';
    G['pthigh' + k] = { p0: hp, p1: knee, r0: [0.085, 0.085], r1: [0.065, 0.065], hint: up };
    G['pshin' + k] = { p0: knee, p1: ank, r0: [0.06, 0.06], r1: [0.045, 0.045], hint: up };
    G['pfoot' + k] = { p0: add(ank, V(-0.03, -0.02, 0)), p1: add(ank, V(0.15, -0.035, 0)), r0: [0.04, 0.035], r1: [0.035, 0.025], hint: up };
    legs.push(ank);
  }
  // arms: near arm does the acting; far arm rests
  let hand = null, handAng = 0;
  for (const sd of [1, -1]) {
    const s0 = add(sh, V(-0.01, -0.03, -0.17 * sd));
    let tgt;
    const hang = add(s0, V(0.06, -0.55, 0));
    if (sd > 0) {
      const beck = add(s0, V(0.32, -0.25 + 0.05 * Math.sin(t * 9), 0));
      const reachT = add(s0, V(0.56, -0.2, 0));
      const lowT = add(base, V(0.78, 0.22, -0.2));
      tgt = hang;
      tgt = lerpV(tgt, beck, q.call * (1 - q.reach) * 0.85);
      tgt = lerpV(tgt, reachT, q.reach);
      tgt = lerpV(tgt, lowT, q.low);
    } else {
      const knee = lerpV(add(hip, V(0.1, -0.35, 0.1)), add(hip, V(0.38, 0.02, 0.1)), q.sit);
      tgt = lerpV(add(s0, V(0.02, -0.55, 0)), add(knee, V(0, 0.05, 0)), q.sit);
    }
    const L1 = 0.3, L2 = 0.28; const d = sub(tgt, s0); let dl = len(d); const dn = mul(d, 1 / dl); dl = clamp(dl, 0.05, L1 + L2 - 0.002);
    const aa = (L1 * L1 + dl * dl - L2 * L2) / (2 * dl), hh = Math.sqrt(Math.max(0, L1 * L1 - aa * aa));
    const hint = V(-0.3, -1, 0); const bend = norm(sub(hint, mul(dn, dot(hint, dn))));
    const el = add(s0, add(mul(dn, aa), mul(bend, hh))), wr = add(s0, mul(dn, dl));
    const k = sd > 0 ? 'N' : 'F';
    G['puarm' + k] = { p0: s0, p1: el, r0: [0.055, 0.055], r1: [0.045, 0.045], hint: fw };
    G['pfarm' + k] = { p0: el, p1: wr, r0: [0.045, 0.045], r1: [0.035, 0.035], hint: fw };
    if (sd > 0) { hand = wr; const a = proj(el), b = proj(wr); handAng = Math.atan2(b[1] - a[1], b[0] - a[0]); }
    else G.pfistF = { p0: wr, p1: add(wr, mul(dn, 0.06)), r0: [0.035, 0.035], r1: [0.03, 0.03], hint: fw };
  }
  return { G, hand, handAng, q, legs, hip };
}
function buildPerson() {
  const B = new FragBody(2602, 48);
  const coat = [0.42, 0.38, 0.44], coatD = [0.30, 0.27, 0.32], trous = [0.30, 0.29, 0.30], hair = [0.22, 0.18, 0.16], skin = [0.78, 0.6, 0.5];
  B.core('ptorso', 6, 0, coatD); B.capsule('ptorso', 130, 0.085, ['coat'], (f) => f._st > 0.6 ? coatD : coat);
  B.capsule('pneck', 10, 0.05, ['fur_lion'], skin);
  B.core('phead', 2, 0, hair); B.capsule('phead', 50, 0.06, ['fur_cat', 'dark'], (f) => (Math.cos(f.th) > 0.2 && f._st < 0.5) ? skin : hair);
  B.capsule('pnose', 6, 0.035, ['fur_lion'], skin);
  for (const k of ['N', 'F']) {
    const c = k === 'N' ? 1 : 0.75;
    B.core('pthigh' + k, 3, 0, trous); B.capsule('pthigh' + k, 34, 0.07, ['coat'], trous.map(v => v * c));
    B.capsule('pshin' + k, 26, 0.06, ['coat'], trous.map(v => v * c));
    B.capsule('pfoot' + k, 10, 0.05, ['dark'], [0.3, 0.26, 0.24]);
    B.capsule('puarm' + k, 20, 0.06, ['coat'], coat.map(v => v * c));
    B.capsule('pfarm' + k, 16, 0.055, ['coat'], coat.map(v => v * c));
  }
  B.capsule('pfistF', 6, 0.05, ['fur_lion'], skin.map(v => v * 0.75));
  return B;
}

/* ------------------------------------------------------------------ consolidation and grain filters (shader stages) */
const FRAG_CONSOLIDATE = `
precision highp float;
varying vec2 vTextureCoord;
uniform sampler2D uSampler;
uniform vec4 inputSize;
uniform vec3 uLine;
uniform float uLo, uHi, uRad, uLineA, uRim;
float A(vec2 o){ return smoothstep(uLo, uHi, texture2D(uSampler, vTextureCoord + o).a); }
void main(){
  vec4 c = texture2D(uSampler, vTextureCoord);
  float a = smoothstep(uLo, uHi, c.a);
  vec2 px = inputSize.zw * uRad;
  float dil = 0.0, ero = 1.0;
  for (int k = 0; k < 8; k++) {
    float an = float(k) * 0.7853982;
    vec2 o = vec2(cos(an), sin(an)) * px;
    float v = A(o); dil = max(dil, v);
    float w = A(o * 1.6); ero = min(ero, w);
  }
  vec3 col = c.a > 0.002 ? c.rgb / c.a : uLine;
  col = mix(col * uRim, col, ero);
  float alpha = max(a, dil * uLineA);
  vec3 outc = mix(uLine, col, alpha > 0.0 ? a / alpha : 0.0);
  gl_FragColor = vec4(outc * alpha, alpha);
}`;
const FRAG_GRAIN = `
precision highp float;
varying vec2 vTextureCoord;
uniform sampler2D uSampler;
uniform vec4 inputSize;
uniform vec4 outputFrame;
uniform float uTime, uGain, uGrain;
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
void main(){
  vec2 uv = vTextureCoord;
  vec4 c = texture2D(uSampler, uv);
  vec2 sc = uv * inputSize.xy / outputFrame.zw;
  vec2 cell = floor(uv * inputSize.xy / 2.0);
  float g = hash(cell + vec2(uTime * 7.13, uTime * 3.71)) - 0.5;
  float d = length((sc - 0.5) * vec2(1.0, 0.75));
  float vig = 1.0 - smoothstep(0.32, 0.78, d) * 0.55;
  vec3 col = c.rgb * vig * uGain + g * uGrain;
  gl_FragColor = vec4(col, 1.0);
}`;

/* ------------------------------------------------------------------ the stage */
const ST = {};
function T_(name) { return TEX[name]; }
function strip(cls, r) { return pick(cls, r); }
function quadSprite(tex, p0, p1, thick, tint, cont) {   // a strip sprite from p0 to p1 (world), thickness in px
  const a = proj(p0), b = proj(p1);
  const sp = new PIXI.Sprite(tex); sp.anchor.set(0, 0.5);
  sp.position.set(a[0], a[1]); sp.rotation = Math.atan2(b[1] - a[1], b[0] - a[0]);
  sp.scale.set(Math.hypot(b[0] - a[0], b[1] - a[1]) / tex.width, thick / tex.height);
  sp.tint = rgbHex(tint); cont.addChild(sp); return sp;
}
function poly(g, pts) { g.drawPolygon(pts.flatMap(p => proj(p))); }

function buildStage() {
  const r = RNG(2626);
  const stage = new PIXI.Container();
  const L = {}; for (const k of ['sky', 'yard', 'house', 'floor', 'actors', 'front']) { L[k] = new PIXI.Container(); stage.addChild(L[k]); }
  ST.L = L; ST.stage = stage;
  // --- sky: gradient bands (computed), cloud-bank and star cut-outs, chalk moon
  const sky = new PIXI.Graphics();
  for (let y = 0; y < 420; y += 6) {
    const u = y / 420;
    const c = [lerp(0.10, 0.62, u ** 1.6), lerp(0.11, 0.36, u ** 1.4), lerp(0.24, 0.36, u)];
    sky.beginFill(rgbHex(c)); sky.drawRect(600, y, 700, 6); sky.endFill();
  }
  L.sky.addChild(sky);
  const banks = [['cloudbank_0', 640, 250, 1.1, [0.75, 0.42, 0.40]], ['cloudbank_1', 900, 270, 1.0, [0.82, 0.48, 0.38]], ['cloudbank_2', 1060, 205, 0.8, [0.45, 0.36, 0.5]]];
  ST.banks = [];
  for (const [n, x, y, s, c] of banks) { const sp = new PIXI.Sprite(T_(n)); sp.position.set(x, y); sp.scale.set(s, s * 0.6); sp.tint = rgbHex(c); sp.alpha = 0.75; L.sky.addChild(sp); ST.banks.push([sp, x]); }
  for (let k = 0; k < 40; k++) { const sp = new PIXI.Sprite(pick('sky', r)); sp.anchor.set(0.5); sp.position.set(680 + r() * 620, 230 + r() * 140); sp.scale.set(1.2 + r() * 1.5, 0.5 + r() * 0.4); sp.tint = rgbHex([0.9, 0.55 + r() * 0.1, 0.45]); sp.alpha = 0.25; L.sky.addChild(sp); }
  for (let k = 0; k < 14; k++) { const sp = new PIXI.Sprite(pick('star', r)); sp.anchor.set(0.5); sp.position.set(700 + r() * 570, 10 + r() * 150); sp.scale.set(0.12 + r() * 0.18); sp.tint = 0xdde4ff; sp.alpha = 0.7; L.sky.addChild(sp); }
  const moon = new PIXI.Sprite(T_('qd_moon_0')); moon.anchor.set(0.5); moon.position.set(1150, 70); moon.scale.set(0.45); moon.tint = 0xf2e6c8; L.sky.addChild(moon);
  // --- yard: dark ground band beyond the porch, chalk trees and fence, fog
  const yard = new PIXI.Graphics(); for (let y = 360; y < 540; y += 6) { const u = (y - 360) / 180; yard.beginFill(rgbHex([lerp(0.42, 0.17, u), lerp(0.36, 0.17, u), lerp(0.44, 0.23, u)])); yard.drawRect(600, y, 700, 6); yard.endFill(); } L.yard.addChild(yard);
  for (const [n, x, y, s] of [['qd_tree_0', 820, 300, 0.95], ['qd_tree_1', 1215, 330, 0.75], ['qd_tree_0', 1010, 340, 0.55]]) { const sp = new PIXI.Sprite(T_(n)); sp.anchor.set(0.5, 1); sp.position.set(x, y + 90); sp.scale.set(s); sp.tint = 0x8a8fa8; sp.alpha = 0.55; L.yard.addChild(sp); }
  const fence = new PIXI.Sprite(T_('qd_fence_0')); fence.position.set(700, 388); fence.scale.set(1.9, 0.6); fence.tint = 0x7d8298; fence.alpha = 0.45; L.yard.addChild(fence);
  ST.fog = [];
  for (let k = 0; k < 10; k++) { const sp = new PIXI.Sprite(TEX.soft); sp.anchor.set(0.5); const x0 = 620 + r() * 700; sp.position.set(x0, 420 + r() * 80); sp.scale.set(5 + r() * 4, 1.2 + r()); sp.tint = 0xb8b0c4; sp.alpha = 0.16; L.yard.addChild(sp); ST.fog.push([sp, x0, 6 + r() * 8]); }
  // back rail of the porch (z = 0, x 1.75..5)
  for (const y of [0.42, 0.78]) for (let x = 1.75; x < 5.1; x += 1.1) quadSprite(strip('wood', r), V(x, y, 0.02), V(x + 1.12, y, 0.02), 9, [0.30, 0.27, 0.27], L.yard);
  for (let x = 1.9; x < 5.2; x += 0.42) quadSprite(strip('wood', r), V(x, 0, 0.03), V(x, 0.8, 0.03), 7, [0.24, 0.22, 0.23], L.yard);
  // --- house: clapboards, trim, window, interior behind the opening mask
  const wallTint = () => [0.36 + r() * 0.05, 0.38 + r() * 0.05, 0.47 + r() * 0.05];
  for (let row = 0; row < 19; row++) {
    const y = row * 0.155; let x = -1.75 - r() * 0.6;
    while (x < 1.75) {
      const x1 = Math.min(1.75, x + 0.8 + r() * 0.4);
      const inDoor = (xx) => xx > -0.58 && xx < 0.58 && y < 2.2;
      if (inDoor(x) && inDoor(x1)) { x = x1; continue; }
      if (y < 2.2 && x < 0.58 && x1 > -0.58) {  // split around the door
        if (x < -0.58) quadSprite(strip('wood', r), V(x, y + 0.078, 0), V(-0.58, y + 0.078, 0), 0.165 * S * COS, wallTint(), L.house);
        if (x1 > 0.58) quadSprite(strip('wood', r), V(0.58, y + 0.078, 0), V(x1, y + 0.078, 0), 0.165 * S * COS, wallTint(), L.house);
      } else quadSprite(strip('wood', r), V(x, y + 0.078, 0), V(x1, y + 0.078, 0), 0.165 * S * COS, wallTint(), L.house);
      x = x1;
    }
  }
  // corner board
  quadSprite(strip('wood', r), V(1.72, 0, 0), V(1.72, 3.2, 0), 18, [0.30, 0.31, 0.37], L.house);
  // window (left), dim warm glow + bars
  const win = new PIXI.Graphics(); win.beginFill(0x3a2a1c); poly(win, [V(-1.5, 1.05, 0), V(-0.95, 1.05, 0), V(-0.95, 1.85, 0), V(-1.5, 1.85, 0)]); win.endFill(); L.house.addChild(win);
  const wg = new PIXI.Sprite(TEX.soft); wg.anchor.set(0.5); const wc = proj(V(-1.22, 1.45, 0)); wg.position.set(wc[0], wc[1]); wg.scale.set(2.6, 3.4); wg.tint = 0xffb066; wg.alpha = 0.5; L.house.addChild(wg); ST.winGlow = wg;
  for (const x of [-1.5, -1.225, -0.95]) quadSprite(strip('wood', r), V(x, 1.02, 0), V(x, 1.88, 0), 7, [0.28, 0.28, 0.33], L.house);
  for (const y of [1.05, 1.45, 1.85]) quadSprite(strip('wood', r), V(-1.53, y, 0), V(-0.92, y, 0), 7, [0.28, 0.28, 0.33], L.house);
  // interior (the lit room) — its own container under an alpha mask = the door opening
  const room = new PIXI.Container(); ST.room = room;
  const rg = new PIXI.Graphics();
  rg.beginFill(0x7a4a26); poly(rg, [V(-0.8, 0, 0), V(0.8, 0, 0), V(0.8, 0, 3.2), V(-0.8, 0, 3.2)]); rg.endFill();
  rg.beginFill(0xc28a52); poly(rg, [V(-0.8, 0, 3.2), V(0.8, 0, 3.2), V(0.8, 2.6, 3.2), V(-0.8, 2.6, 3.2)]); rg.endFill();
  room.addChild(rg);
  for (let z = 0.1; z < 3.2; z += 0.16) for (let x = -0.8; x < 0.8; x += 0.7) quadSprite(strip('wood', r), V(x, 0, z), V(x + 0.72, 0, z), 0.16 * S * SIN + 1, [0.85, 0.55, 0.32], room);
  for (let k = 0; k < 40; k++) { const sp = new PIXI.Sprite(pick('coat', r)); sp.anchor.set(0.5); const p = proj(V(-0.8 + r() * 1.6, r() * 2.6, 3.2)); sp.position.set(p[0], p[1]); sp.scale.set(0.9); sp.tint = rgbHex([1, 0.78, 0.5]); sp.alpha = 0.35; room.addChild(sp); }
  const pic = new PIXI.Sprite(T_('picture')); const pp = proj(V(-0.42, 1.75, 3.2)); pic.position.set(pp[0], pp[1]); pic.scale.set(0.42); pic.tint = 0xf0c890; room.addChild(pic);
  const doodles = ['qd_dog_0', 'qd_dog_2', 'qd_dog_4'];
  doodles.forEach((n, k) => { const sp = new PIXI.Sprite(T_(n)); const p = proj(V(0.1 + k * 0.22, 1.5 - (k % 2) * 0.25, 3.2)); sp.position.set(p[0], p[1]); sp.scale.set(0.32); sp.tint = 0x5a3a20; room.addChild(sp); });
  const table = new PIXI.Graphics(); table.beginFill(0x3a2414); poly(table, [V(-0.3, 0.7, 2.4), V(0.25, 0.7, 2.4), V(0.25, 0.66, 2.4), V(-0.3, 0.66, 2.4)]); table.endFill();
  table.beginFill(0x3a2414); for (const x of [-0.27, 0.21]) poly(table, [V(x, 0, 2.4), V(x + 0.04, 0, 2.4), V(x + 0.04, 0.68, 2.4), V(x, 0.68, 2.4)]); table.endFill(); room.addChild(table);
  const lant = new PIXI.Sprite(T_('lantern')); lant.anchor.set(0.5, 1); const lp = proj(V(-0.05, 0.7, 2.4)); lant.position.set(lp[0], lp[1]); lant.scale.set(0.42); room.addChild(lant);
  const lg = new PIXI.Sprite(TEX.soft); lg.anchor.set(0.5); lg.position.set(lp[0], lp[1] - 30); lg.scale.set(6); lg.tint = 0xffc070; lg.blendMode = PIXI.BLEND_MODES.ADD; lg.alpha = 0.5; room.addChild(lg);
  // the door leaf: the archive door, a 2-triangle mesh whose corners are the projected leaf (hinged on the left jamb, swings in)
  ST.leaf = new PIXI.SimpleMesh(T_('doorleaf'), new Float32Array(8), new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]), new Uint16Array([0, 1, 2, 0, 2, 3]));
  const lt = T_('doorleaf');
  // uvs are 0..1 over the frame; the mesh material's uvMatrix maps them into the atlas sub-rect
  room.addChild(ST.leaf);
  const mask = new PIXI.Graphics(); mask.beginFill(0xffffff); poly(mask, [V(-0.46, 0, 0), V(0.46, 0, 0), V(0.46, 2.05, 0), V(-0.46, 2.05, 0)]); mask.endFill();
  room.mask = mask; L.house.addChild(mask); L.house.addChild(room);
  // dark until the light spills: a shade over the room (fades as the door opens)
  ST.roomShade = new PIXI.Graphics(); ST.roomShade.beginFill(0x000000); poly(ST.roomShade, [V(-0.46, 0, 0), V(0.46, 0, 0), V(0.46, 2.05, 0), V(-0.46, 2.05, 0)]); ST.roomShade.endFill(); ST.roomShade.alpha = 0.0; L.house.addChild(ST.roomShade);
  // door trim (jambs and head)
  quadSprite(strip('wood', r), V(-0.52, 0, 0), V(-0.52, 2.2, 0), 0.12 * S, [0.62, 0.6, 0.62], L.house);
  quadSprite(strip('wood', r), V(0.52, 0, 0), V(0.52, 2.2, 0), 0.12 * S, [0.62, 0.6, 0.62], L.house);
  quadSprite(strip('wood', r), V(-0.6, 2.12, 0), V(0.6, 2.12, 0), 0.16 * S, [0.62, 0.6, 0.62], L.house);
  // --- floor: porch boards
  for (let row = 0; row < 15; row++) {
    const z = -row * 0.145 - 0.07; let x = -1.8 - r() * 0.8;
    while (x < 5.2) { const x1 = x + 1.0 + r() * 0.5; quadSprite(strip('wood', r), V(x, 0, z), V(x1, 0, z), 0.15 * S * SIN + 1.5, [0.33 + r() * 0.05, 0.29 + r() * 0.04, 0.27 + r() * 0.03], L.floor); x = x1; }
  }
  // the sill: a raised oak board across the door (top face + front edge)
  const sillT = [0.62, 0.48, 0.34];
  quadSprite(strip('wood', r), V(-0.58, 0.03, 0.03), V(0.58, 0.03, 0.03), 0.3 * S * SIN, sillT, L.floor);
  quadSprite(strip('wood', r), V(-0.58, 0.015, -0.12), V(0.58, 0.015, -0.12), 0.03 * S * COS + 2, [0.35, 0.27, 0.2], L.floor);
  // light render texture (half res) -> added over the floor
  ST.lightRT = PIXI.RenderTexture.create({ width: W / 2, height: H / 2 });
  ST.lightC = new PIXI.Container();
  ST.lightPoly = new PIXI.Graphics(); ST.lightC.addChild(ST.lightPoly);
  ST.shadowC = new PIXI.Container(); ST.lightC.addChild(ST.shadowC);
  ST.shadowSp = []; for (let k = 0; k < 900; k++) { const sp = new PIXI.Sprite(TEX.soft); sp.anchor.set(0.5); sp.tint = 0x000000; sp.visible = false; ST.shadowC.addChild(sp); ST.shadowSp.push(sp); }
  ST.lightC.filters = [new PIXI.BlurFilter(2, 2)];
  ST.lightSp = new PIXI.Sprite(ST.lightRT); ST.lightSp.scale.set(2); ST.lightSp.blendMode = PIXI.BLEND_MODES.ADD; ST.lightSp.tint = 0xffb878; L.floor.addChild(ST.lightSp);
  // contact shadows (multiplied darkness under feet and body)
  ST.contact = new PIXI.Container(); L.floor.addChild(ST.contact);
  ST.contactSp = []; for (let k = 0; k < 12; k++) { const sp = new PIXI.Sprite(TEX.soft); sp.anchor.set(0.5); sp.tint = 0x000000; ST.contact.addChild(sp); ST.contactSp.push(sp); }
  // --- actors: crate, person (RT), hand, dog (RT)
  ST.crate = new PIXI.Container(); L.actors.addChild(ST.crate);
  for (let k = 0; k < 4; k++) quadSprite(strip('wood', r), V(-1.52, 0.06 + k * 0.1, -0.28), V(-0.98, 0.06 + k * 0.1, -0.28), 0.1 * S * COS, [0.4, 0.32, 0.25], ST.crate);
  for (let k = 0; k < 3; k++) quadSprite(strip('wood', r), V(-1.52, 0.42, -0.28 + k * 0.12 + 0.06), V(-0.98, 0.42, -0.28 + k * 0.12 + 0.06), 0.12 * S * SIN + 1, [0.5, 0.4, 0.3], ST.crate);
  ST.crate.alpha = 1;
  ST.personRT = PIXI.RenderTexture.create({ width: 512, height: 560 });
  ST.personSp = new PIXI.Sprite(ST.personRT);
  ST.personSp.filters = [mkConsolidate([0.05, 0.04, 0.06], 0.9)];
  L.actors.addChild(ST.personSp);
  ST.hand = new PIXI.Sprite(T_('hand')); ST.hand.anchor.set(0.12, 0.45); L.actors.addChild(ST.hand);
  ST.dogRT = PIXI.RenderTexture.create({ width: 512, height: 384 });
  ST.dogSp = new PIXI.Sprite(ST.dogRT);
  ST.dogSp.filters = [mkConsolidate([0.07, 0.05, 0.04], 0.95)];
  L.actors.addChild(ST.dogSp);
  ST.headRT = PIXI.RenderTexture.create({ width: 320, height: 280 });
  ST.headSp = new PIXI.Sprite(ST.headRT);
  ST.headSp.filters = [mkConsolidate([0.07, 0.05, 0.04], 0.95)];
  L.actors.addChild(ST.headSp);
  // --- front: porch edge + hanging leaves
  const fe = new PIXI.Graphics(); fe.beginFill(0x15120f); fe.drawRect(0, proj(V(0, 0, -2.15))[1], W, 80); fe.endFill(); L.front.addChild(fe);
  for (let x = -1.8; x < 5.2; x += 0.9) quadSprite(strip('wood', r), V(x, -0.02, -2.15), V(x + 0.92, -0.02, -2.15), 14, [0.22, 0.19, 0.17], L.front);
  for (let k = 0; k < 12; k++) { const sp = new PIXI.Sprite(pick('dark', r)); sp.anchor.set(0.5); sp.position.set(1120 + r() * 170, -5 + Math.pow(r(), 1.8) * 120 * (1 - (k % 5) / 8)); sp.scale.set(0.35 + r() * 0.35, 0.25 + r() * 0.2); sp.rotation = r() * 6; sp.tint = rgbHex([0.16, 0.2 + r() * 0.06, 0.14]); L.front.addChild(sp); }
  // final: stage -> RT -> grain
  ST.stageRT = PIXI.RenderTexture.create({ width: W, height: H });
  ST.finalC = new PIXI.Container();
  ST.finalSp = new PIXI.Sprite(ST.stageRT);
  ST.grain = new PIXI.Filter(undefined, FRAG_GRAIN, { uTime: 0, uGain: 1, uGrain: 0.05 });
  ST.finalSp.filters = [ST.grain];
  ST.finalC.addChild(ST.finalSp);
}
function mkConsolidate(line, rim) {
  const f = new PIXI.Filter(undefined, FRAG_CONSOLIDATE, { uLine: new Float32Array(line), uLo: 0.28, uHi: 0.5, uRad: 1.4, uLineA: 0.9, uRim: rim * 0.7 });
  f.padding = 4; return f;
}

/* ------------------------------------------------------------------ per-frame update */
function doorAngle(t) { return lerp(32, 86, ss(6.2, 7.05, t)); }
function poolPoly(t) {   // the floor light: lamp projected through the effective opening onto the porch (z >= -2.15)
  const a = doorAngle(t) * D2R, xl = Math.min(0.455, -0.46 + 0.92 * Math.cos(a));
  const far = (xe) => { const tt = 1 + 2.15 / LAMP.z; return V(LAMP.x + tt * (xe - LAMP.x), 0, -2.15); };
  return [V(xl, 0, 0.0), V(0.46, 0, 0.0), far(0.46), far(xl)];
}
function inPoolFn(t) {
  const P = poolPoly(t), x0 = P[0].x, x1 = P[1].x;
  return (p) => { if (p.z > 0.2) return 1; const u = clamp(-p.z / 2.15), lx = lerp(x0, P[3].x, u), rx = lerp(x1, P[2].x, u); return ss(lx - 0.15, lx + 0.05, p.x) * (1 - ss(rx - 0.05, rx + 0.15, p.x)); };
}

let DOGB, PERB;
function renderScene(i) {
  const t = i / FPS;
  const open = ss(6.2, 7.05, t);
  const env = { door: 0.18 + 0.82 * open, cool: [0.86, 0.9, 1.08], inPool: inPoolFn(t) };
  // door leaf corners
  const a = doorAngle(t) * D2R, hx = -0.46, wdt = 0.92;
  const c = [V(hx, 2.04, 0.04), V(hx + wdt * Math.cos(a), 2.04, 0.04 + wdt * Math.sin(a)), V(hx + wdt * Math.cos(a), 0, 0.04 + wdt * Math.sin(a)), V(hx, 0, 0.04)];
  const vb = ST.leaf.geometry.getBuffer('aVertexPosition'); vb.data = new Float32Array(c.flatMap(p => proj(p))); vb.update();
  ST.leaf.tint = rgbHex([0.62 + 0.25 * open, 0.5 + 0.2 * open, 0.4 + 0.1 * open]);
  ST.roomShade.alpha = 0.0;
  // drift: fog, clouds
  for (const [sp, x0, v] of ST.fog) sp.x = 600 + ((x0 - 600 + v * t) % 720);
  for (const [sp, x0] of ST.banks) sp.x = x0 - 2.5 * t;
  ST.winGlow.alpha = 0.45 + 0.04 * Math.sin(t * 3.1) + 0.03 * Math.sin(t * 7.7);
  // --- dog
  const D = dogParts(i);
  const cx = proj(V(D.q.x, 0.3, D.q.z));
  const offD = [Math.round(cx[0] - 256), Math.round(cx[1] - 210)];
  const envD = Object.assign({}, env, { gain: 1.55 });
  const dogPts = DOGB.update(D.G, envD, offD);
  ST.dogSp.position.set(offD[0], offD[1]);
  const hc = proj(D.skull), offH = [Math.round(hc[0] - 160), Math.round(hc[1] - 140)];
  dogPts.push(...DOGB.head.update(D.G, envD, offH));
  ST.headSp.position.set(offH[0], offH[1]);
  const headBehind = dep(D.skull) > dep(add(D.chest, V(0, 0.1, 0))) + 0.02 && D.q.look > 0.3;
  // --- person
  const Pp = personParts(i);
  const pc = proj(V(Pp.q.x, 0.9, Pp.q.z));
  const offP = [Math.round(pc[0] - 230), Math.round(pc[1] - 280)];
  const perPts = PERB.update(Pp.G, Object.assign({}, env, { cool: [0.72, 0.74, 0.9] }), offP);
  ST.personSp.position.set(offP[0], offP[1]);
  // the archive hand at the near wrist
  const hs = proj(Pp.hand); ST.hand.position.set(hs[0], hs[1]); ST.hand.rotation = Pp.handAng; ST.hand.scale.set(0.62);
  ST.hand.tint = rgbHex(shade([0.95, 0.8, 0.7], Pp.hand, V(0, 0.5, -0.5), env, false, 0));
  // actor order by depth (z)
  const dz = D.q.z, pz = Pp.q.z;
  ST.L.actors.removeChildren();
  const pers = [ST.crate, ST.personSp, ST.hand], dogs = headBehind ? [ST.headSp, ST.dogSp] : [ST.dogSp, ST.headSp];
  for (const o of (pz > dz ? [...pers, ...dogs] : [...dogs, ...pers])) ST.L.actors.addChild(o);
  // --- light pass: pool polygon + shadows of fragments projected from the lamp
  const g = ST.lightPoly; g.clear();
  const P = poolPoly(t);
  g.beginFill(0xffffff, 0.30 + 0.70 * open); g.drawPolygon(P.flatMap(p => { const s = proj(p); return [s[0] / 2, s[1] / 2]; })); g.endFill();
  g.beginFill(0xffffff, 0.5 * (0.3 + 0.7 * open)); const d0 = proj(V(0, 0, 0)); g.drawEllipse(d0[0] / 2, d0[1] / 2 + 6, 70 * (0.2 + 0.8 * open), 14); g.endFill();
  const castPts = dogPts.concat(perPts.filter((_, k) => k % 2 === 0));
  let sk = 0;
  for (const p of castPts) {
    if (sk >= ST.shadowSp.length) break;
    if (p.y >= LAMP.y - 0.05) continue;
    const tt = LAMP.y / (LAMP.y - p.y), s = add(LAMP, mul(sub(p, LAMP), tt));
    if (s.z > 0.05 || s.z < -2.3) continue;
    const sp = ST.shadowSp[sk++], q = proj(s);
    sp.visible = true; sp.position.set(q[0] / 2, q[1] / 2); sp.scale.set(0.075 * Math.min(tt, 2.2) * S / 2 / 48 * 1.5, 0.05 * Math.min(tt, 2.2) * S / 2 / 48 * 1.5); sp.alpha = 0.6;
  }
  for (; sk < ST.shadowSp.length; sk++) ST.shadowSp[sk].visible = false;
  ST.lightSp.alpha = 0.9;
  // --- contact shadows: four paws + body
  let ck = 0;
  for (const ft of D.feet) { const sp = ST.contactSp[ck++], q = proj(V(ft.p.x, 0, ft.p.z)); sp.position.set(q[0], q[1] + 1); const h = clamp(ft.p.y / 0.08); sp.scale.set(0.55 * (1 - 0.4 * h), 0.18 * (1 - 0.4 * h)); sp.alpha = 0.65 * (1 - 0.6 * h); }
  { const sp = ST.contactSp[ck++], m = lerpV(D.chest, D.rump, 0.5), q = proj(V(m.x, 0, m.z)); sp.position.set(q[0], q[1] + 2); sp.scale.set(2.2 + 0.8 * D.q.lie, 0.42 + 0.25 * D.q.lie); sp.alpha = 0.35 + 0.3 * D.q.lie; }
  for (const lg of Pp.legs) { const sp = ST.contactSp[ck++], q = proj(V(lg.x + 0.05, 0, lg.z)); sp.position.set(q[0], q[1] + 1); sp.scale.set(0.9, 0.22); sp.alpha = 0.6; }
  { const sp = ST.contactSp[ck++], q = proj(V(-1.25, 0, -0.28)); sp.position.set(q[0], q[1] + 2); sp.scale.set(3.4, 0.5); sp.alpha = 0.45; }
  for (; ck < ST.contactSp.length; ck++) ST.contactSp[ck].alpha = 0;
  // --- passes
  R.render(DOGB.c, { renderTexture: ST.dogRT, clear: true });
  R.render(DOGB.head.c, { renderTexture: ST.headRT, clear: true });
  R.render(PERB.c, { renderTexture: ST.personRT, clear: true });
  R.render(ST.lightC, { renderTexture: ST.lightRT, clear: true });
  R.render(ST.stage, { renderTexture: ST.stageRT, clear: true });
  ST.grain.uniforms.uTime = (i * 0.618) % 1 * 100; ST.grain.uniforms.uGain = 1 + 0.018 * Math.sin(i * 1.7) * Math.sin(i * 0.37); ST.grain.uniforms.uGrain = 0.045;
  R.render(ST.finalC);
  return { D, Pp, offD };
}

/* ------------------------------------------------------------------ measurement from the dog render texture */
function measureDog(offD) {
  const px = R.extract.pixels(ST.dogRT);
  const w = ST.dogRT.width, h = ST.dogRT.height;
  let n = 0, sx = 0, sy = 0, x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) {
    const a = px[(y * w + x) * 4 + 3];
    if (a > 100) { n++; sx += x; sy += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  if (!n) return null;
  return { x: sx / n + offD[0], y: sy / n + offD[1], bbox: [x0 + offD[0], y0 + offD[1], x1 + offD[0], y1 + offD[1]], area: n * 4 };
}

/* ------------------------------------------------------------------ cards */
function buildCards() {
  const r = RNG(77);
  const C = new PIXI.Container();
  const bg = new PIXI.Graphics(); bg.beginFill(0x0d0e14); bg.drawRect(0, 0, W, H); bg.endFill(); C.addChild(bg);
  ST.cardFrags = [];
  const classes = ['fur_dog', 'fur_lion', 'fur_cat', 'dark', 'coat', 'sky', 'wood'];
  for (let k = 0; k < 420; k++) {
    const cls = classes[Math.floor(r() * classes.length)];
    const sp = new PIXI.Sprite(pick(cls, r)); sp.anchor.set(0.5);
    const x = r() * W, y = r() * H; sp.position.set(x, y); sp.scale.set(cls === 'wood' ? 0.4 : 0.3 + r() * 0.25); sp.rotation = r() * 6.28; sp.alpha = 0.16 + r() * 0.12;
    sp.tint = rgbHex([0.8, 0.66, 0.5]); C.addChild(sp); ST.cardFrags.push([sp, x, y, (r() - 0.5) * 8, (r() - 0.5) * 5, (r() - 0.5) * 0.4]);
  }
  const shade2 = new PIXI.Graphics(); shade2.beginFill(0x0d0e14, 0.55); shade2.drawRect(140, 0, 1000, H); shade2.endFill(); C.addChild(shade2);
  ST.cardText = new PIXI.Container(); C.addChild(ST.cardText);
  ST.cards = C;
}
function txt(s, size, fam, col, w, x, y, opt = {}) {
  const t = new PIXI.Text(s, Object.assign({ fontFamily: fam, fontSize: size, fill: col, wordWrap: !!w, wordWrapWidth: w || 1000, lineHeight: size * 1.35, fontWeight: opt.weight || 400, letterSpacing: opt.ls || 0 }, opt.style || {}));
  t.position.set(x, y); ST.cardText.addChild(t); return t;
}
function renderCard(kind, k, info) {
  const t = k / FPS;
  for (const [sp, x, y, vx, vy, vr] of ST.cardFrags) { sp.position.set(x + vx * t, y + vy * t); sp.rotation += 0; }
  if (ST.cardKind !== kind) {
    ST.cardText.removeChildren(); ST.cardKind = kind;
    if (kind === 'title') {
      txt('PAE-02 · SCION 26 · PixiJS — Archive Stage Rendering Engine', 50, 'Big Shoulders Display', 0xf0e2c8, 1000, 160, 200, { weight: 800 });
      txt('The threshold. A dog at a door that may refuse, staged as a scene graph of small transparent archive fragments.', 26, 'Literata', 0xcfc4b0, 960, 400);
      txt('cohort 7 · 32 s at 24 fps, aligned frame for frame to the PAELEO score', 18, 'JetBrains Mono', 0x9a937f, 960, 500);
    } else {
      txt('What it is made of', 40, 'Big Shoulders Display', 0xf0e2c8, 1000, 160, 70, { weight: 800 });
      txt(info, 19, 'Literata', 0xd8cdb8, 980, 160, 140);
    }
  }
  ST.cards.alpha = clamp(Math.min(k / 10, (71 - k) / 10));
  R.render(ST.cards);
}

/* ------------------------------------------------------------------ boot + API for render.js */
async function boot() {
  PIXI.settings.ROUND_PIXELS = false;
  const app = new PIXI.Application({ width: W, height: H, backgroundColor: 0x000000, preserveDrawingBuffer: true, antialias: false, autoStart: false });
  document.body.appendChild(app.view);
  R = app.renderer;
  const gl = R.gl;
  for (const fn of ['drawElements', 'drawArrays']) { const o = gl[fn].bind(gl); gl[fn] = (...a) => { DRAWS++; return o(...a); }; }
  ATL = await (await fetch('atlas/atlas.json')).json();
  SC = await (await fetch('score.json')).json();
  const base = await PIXI.Assets.load('atlas/atlas.png');
  for (const [k, f] of Object.entries(ATL.frames)) TEX[k] = new PIXI.Texture(base.baseTexture, new PIXI.Rectangle(f.x, f.y, f.w, f.h));
  CLS = ATL.classes;
  await document.fonts.load('800 40px "Big Shoulders Display"'); await document.fonts.load('26px Literata'); await document.fonts.load('18px "JetBrains Mono"');
  buildDogTimeline(); DOGB = buildDog(); PERB = buildPerson(); buildStage(); buildCards();
  return { dogFrags: DOGB.frags.length + DOGB.head.frags.length, personFrags: PERB.frags.length, atlasFrames: Object.keys(ATL.frames).length, version: PIXI.VERSION,
    glRenderer: gl.getParameter(gl.RENDERER), stageSprites: countSprites(ST.stage) };
}
function countSprites(c) { let n = 0; c.children.forEach(ch => { if (ch instanceof PIXI.Sprite) n++; if (ch.children && ch.children.length) n += countSprites(ch); }); return n; }

window.STAGE = {
  boot,
  scene(i, measure) {
    DRAWS = 0; const t0 = performance.now();
    const res = renderScene(i);
    const dt = performance.now() - t0; const draws = DRAWS;
    const out = { i, draws, ms: dt };
    if (measure) {
      const m = measureDog(res.offD); const D = res.D;
      const sk = proj(D.skull), mz = proj(D.muz);
      out.m = m; out.q = { x: D.q.x, z: D.q.z, psi: D.q.psi, psiH: D.q.psiH, lie: D.q.lie, neck: D.q.neck, look: D.q.look };
      out.muzzleDx = mz[0] - sk[0]; out.muzzleDy = mz[1] - sk[1];
      out.muzzleDepth = dep(D.muz) - dep(D.skull);
      out.headY = proj(D.skull)[1]; out.backY = Math.min(proj(D.chest)[1], proj(D.rump)[1]) - D.G.torsoF.r1[1] * S * COS;
      const upv = V(0, 1, 0), G = D.G;
      out.headTopY = Math.min(proj(G.earL.p1)[1], proj(G.earR.p1)[1], proj(add(D.skull, mul(upv, 0.066)))[1]);
      out.backTopY = Math.min(proj(add(G.torsoF.p1, mul(upv, G.torsoF.r1[1])))[1], proj(add(G.torsoF.p0, mul(upv, G.torsoF.r0[1])))[1], proj(add(G.torsoR.p0, mul(upv, G.torsoR.r0[1])))[1]);
      out.chestY = D.chest.y; out.feet = D.feet.map(f => [+f.p.x.toFixed(3), +f.p.y.toFixed(3), +f.p.z.toFixed(3)]);
      out.personX = res.Pp.q.x;
    }
    return out;
  },
  card(kind, k, info) { DRAWS = 0; renderCard(kind, k, info); return { draws: DRAWS }; },
  jpeg(q) { return R.view.toDataURL('image/jpeg', q || 0.93); },
};
