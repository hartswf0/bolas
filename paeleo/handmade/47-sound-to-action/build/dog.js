// The dog's sprite set (mouth-shape designer + body-gesture choreographer).
// A sprite is ONE drawing, named by a discrete key. The film never interpolates between sprites: the exposure sheet
// (build/xsheet.py) names a key per frame and the renderer exposes that drawing, so a hold is the same drawing and a
// change is a substitution. Each drawing is laid out from a small pose guide (points in metres, used only to place my
// ink shapes: spheres, tapered capsules, ear and nose shapes) and inked by the two-pass outline method below.
// Key fields: yaw (deg, 0 = facing the door/screen-left, 90 = facing into the house wall, 180 = facing screen-right),
// hy (head yaw, absolute, deg), hp (head pitch 0 low .. 1 alert, in tenths), ear (0 flat .. 2 pricked), tl (tail tuck in
// tenths: 0 high .. 13 tucked), wag (-1,0,1), cr (crouch tenths), lie (lie tenths), g (gait drawing 0..11, -1 = standing
// square), br (breath 0/1), rs (rest: chin on paws tenths), sn (sniff 0/1).
const DOG = (() => {
  const EL = 16 * Math.PI / 180, CE = Math.cos(EL), SE = Math.sin(EL);
  const STRIDE = 0.55, DUTY = 0.62, NG = 12;
  const lerp = (a, b, t) => a + (b - a) * t, cl = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]], mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
  const L3 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
  const rad = d => d * Math.PI / 180;

  function parse(key) { const o = {}; key.split(',').forEach(kv => { const [k, v] = kv.split('='); o[k] = +v; }); return o; }
  function keyOf(o) { return ['yaw', 'hy', 'hp', 'ear', 'tl', 'wag', 'cr', 'lie', 'g', 'br', 'rs', 'sn', 'st'].map(k => k + '=' + (o[k] ?? 0)).join(','); }

  // 2-bone IK in the sagittal plane (x fwd, y up); bend = +1 knee ahead of the line, -1 behind
  function ik(top, end, l1, l2, bend) {
    const dx = end[0] - top[0], dy = end[1] - top[1]; let d = Math.hypot(dx, dy); d = Math.min(d, l1 + l2 - 1e-4);
    const a = Math.acos(cl((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)), base = Math.atan2(dy, dx);
    const ang = base + bend * a; return [top[0] + l1 * Math.cos(ang), top[1] + l1 * Math.sin(ang), top[2]];
  }

  // ---- the pose guide: returns shapes in dog-local metres
  function build(p) {
    const cr = p.cr / 10, lie = p.lie / 10, rs = p.rs / 10, hp = p.hp / 10, tl = p.tl / 10, br = p.br;
    const lr = cl(lie * 1.7), lf = cl((lie - 0.3) / 0.7);          // rear folds first, then the front
    const dropR = 0.11 * cr, dropF = 0.06 * cr;
    // spine: [x, y, r] standing; lying target y
    const S = [[0.27, 0.43, 0.10, 0.20], [0.14, 0.40, 0.145, 0.15], [0.00, 0.425, 0.115, 0.15], [-0.12, 0.445, 0.10, 0.155], [-0.24, 0.45, 0.115, 0.15]];
    const sp = S.map(([x, y, r, yl], k) => {
      const w = k / 4, f = lerp(lf, lr, w), drop = lerp(dropF, dropR, w);
      const yy = lerp(y - drop, yl, f) + (k === 1 ? 0.006 * br : 0);
      return [x + 0.02 * f * (k - 2) * -0.5, yy, 0, r + (k === 1 || k === 2 ? 0.005 * br : 0)];
    });
    const withers = [sp[0][0] - 0.03, sp[0][1] + 0.08, 0];
    // head: absolute yaw hy vs body yaw -> relative, limited; neck takes 55 %, head the rest
    let rel = ((p.hy - p.yaw + 540) % 360) - 180; rel = cl(rel, -160, 160);
    const nr = rad(rel * 0.55), hr = rad(rel);
    const neckA = lerp(rad(lerp(-25, 62, hp)) - rad(18) * lf * (1 - hp), rad(-12), rs);
    const n0 = [sp[0][0] - 0.04, sp[0][1] + 0.06, 0];
    const nl = 0.21 + 0.03 * rs;
    const n1 = [n0[0] + nl * Math.cos(neckA) * Math.cos(nr), n0[1] + nl * Math.sin(neckA), n0[2] - nl * Math.cos(neckA) * Math.sin(nr)];
    const hf = [Math.cos(hr), 0, -Math.sin(hr)];                     // head forward (horizontal)
    const hs = [Math.sin(hr), 0, Math.cos(hr)];                      // head left
    const pitchDown = lerp(rad(lerp(35, 5, hp)), rad(8), rs) - rad(p.sn ? 12 : 0);
    const sk = add(n1, [hf[0] * 0.04, 0.03, hf[2] * 0.04]);
    const mzLen = 0.15;
    const mz = add(sk, [hf[0] * mzLen * Math.cos(pitchDown), -mzLen * Math.sin(pitchDown) - 0.01, hf[2] * mzLen * Math.cos(pitchDown)]);
    if (rs > 0) { const floor = 0.075; if (mz[1] < floor) mz[1] = floor; if (sk[1] < floor + 0.06) sk[1] = floor + 0.06; }
    const earUp = lerp(0.02, 0.11, p.ear / 2), earBack = lerp(0.10, 0.02, p.ear / 2);
    const ears = [1, -1].map(s => {
      const b0 = add(sk, add(mul(hs, s * 0.03), [-hf[0] * 0.01, 0.055, -hf[2] * 0.01]));
      const b1 = add(b0, add(mul(hf, -0.05), mul(hs, s * 0.02)));
      const tip = add(b0, add(add(mul(hf, -earBack), [0, earUp, 0]), mul(hs, s * 0.035)));
      return { side: s, pts: [b0, tip, b1] };
    });
    const eyes = [1, -1].map(s => ({ side: s, c: add(sk, add(add(mul(hf, 0.055), mul(hs, s * 0.045)), [0, 0.012, 0])), n: mul(hs, s) }));
    // legs: neutral stand paws, gait offsets, lying targets
    const legs = [];
    const defs = [
      { n: 'FL', side: 1, front: true, off: 0.25 }, { n: 'FR', side: -1, front: true, off: 0.75 },
      { n: 'HL', side: 1, front: false, off: 0.0 }, { n: 'HR', side: -1, front: false, off: 0.5 }];
    for (const d of defs) {
      const z = d.side * 0.07;
      const top = d.front ? [0.17, sp[1][1], z] : [-0.24, sp[4][1] - 0.01, z];
      let px = (d.front ? 0.175 : -0.285) + (p.g >= 0 ? 0.02 : 0.025 * d.side), py = 0.025;
      if (p.g >= 0) {
        const u = ((p.g / NG + d.off) % 1 + 1) % 1;
        const SL = STRIDE * ((p.st ?? 10) / 10);
        if (u < DUTY) px += SL * DUTY * (0.5 - u / DUTY);
        else { const s = (u - DUTY) / (1 - DUTY); px += SL * DUTY * (-0.5 + s); py += 0.07 * Math.sin(Math.PI * s); }
      }
      if (cr > 0) px += (d.front ? 0.03 : 0.05) * cr;
      const paw = [px, py, z];
      let j1, j2;
      if (d.front) { j2 = [paw[0] - 0.012, paw[1] + 0.07, z]; j1 = ik(top, j2, 0.155, 0.17, -1); }
      else { j2 = [paw[0] - 0.035, paw[1] + 0.11, z]; j1 = ik(top, j2, 0.18, 0.175, 1); }
      // lying targets
      let LT;
      if (d.front) LT = { j1: [0.10, 0.06, z * 1.2], j2: [0.27, 0.035, z * 1.2], paw: [0.36, 0.03, z * 1.2] };
      else LT = { j1: [-0.08, 0.11, z * 1.9], j2: [-0.31, 0.04, z * 1.7], paw: [-0.14, 0.03, z * 1.8] };
      const f = d.front ? lf : lr;
      // fold by moving the paw and the lower joint, and solving the upper joint by IK: bone lengths hold throughout
      const zz = lerp(z, LT.paw[2], f), pw = [lerp(paw[0], LT.paw[0], f), lerp(paw[1], LT.paw[1], f), zz];
      const off = d.front ? [lerp(-0.012, LT.j2[0] - LT.paw[0], f), lerp(0.07, LT.j2[1] - LT.paw[1], f)]
                          : [lerp(-0.035, LT.j2[0] - LT.paw[0], f), lerp(0.11, LT.j2[1] - LT.paw[1], f)];
      const jj2 = [pw[0] + off[0], pw[1] + off[1], zz];
      const tp2 = [top[0], top[1], zz];
      const jj1 = d.front ? ik(tp2, jj2, 0.155, 0.17, -1) : ik(tp2, jj2, 0.18, 0.175, 1);
      legs.push({ n: d.n, side: d.side, front: d.front, top: tp2, j1: f > 0 ? jj1 : j1, j2: f > 0 ? jj2 : j2, paw: f > 0 ? pw : paw });
    }
    // tail: base and three segments; angle from horizontal-back, down is negative
    const t0 = [sp[4][0] - 0.10, sp[4][1] + 0.04, 0];
    let ang = rad(lerp(30, -105, cl(tl / 1.35))), wagA = rad(28 * p.wag);
    const tail = [t0];
    let cur = t0;
    for (let k = 0; k < 3; k++) {
      const a = ang - rad(14) * k * (1 - lie);
      const seg = 0.13;
      let nx = cur[0] - seg * Math.cos(a) * Math.cos(wagA), ny = cur[1] + seg * Math.sin(a), nz = cur[2] + seg * Math.cos(a) * Math.sin(wagA) * (k + 1) * 0.6;
      if (lie > 0.5) { ny = Math.max(ny, 0.03); nz += 0.05 * (k + 1) * lie; nx += 0.025 * k * lie; }
      if (tl > 0.9) nx = Math.max(nx, cur[0] - 0.05 * (k + 1)); // tucked: tail curls under
      cur = [nx, ny, nz]; tail.push(cur);
    }
    return { sp, n0, n1, sk, mz, ears, eyes, legs, tail };
  }

  // ---- projection of local points to sprite pixels
  function projector(p, K) {
    const ps = rad(p.yaw), f = [-Math.cos(ps), -Math.sin(ps)], l = [-Math.sin(ps), Math.cos(ps)];
    return q => {
      const X = q[0] * f[0] + q[2] * l[0], Z = q[0] * f[1] + q[2] * l[1], Y = q[1];
      return { x: X * K, y: -Y * K * CE + Z * K * SE, d: Z * CE + Y * SE, Z };
    };
  }

  // shapes: {c: [circles], q: [quads]} in pixels
  function capsule(sh, a, ra, b, rb) { (sh.k || (sh.k = [])).push([a.x, a.y, ra, b.x, b.y, rb]); }
  function capQuad(ax, ay, ra, bx, by, rb) {
    const dx = bx - ax, dy = by - ay, d = Math.hypot(dx, dy); if (d < Math.abs(ra - rb) + 0.01) return null;
    const th = Math.atan2(dy, dx), be = Math.acos(cl((ra - rb) / d, -1, 1));
    let q = [[ax + ra * Math.cos(th + be), ay + ra * Math.sin(th + be)], [bx + rb * Math.cos(th + be), by + rb * Math.sin(th + be)],
             [bx + rb * Math.cos(th - be), by + rb * Math.sin(th - be)], [ax + ra * Math.cos(th - be), ay + ra * Math.sin(th - be)]];
    let ar = 0; for (let k = 0; k < 4; k++) { const u = q[k], v = q[(k + 1) % 4]; ar += u[0] * v[1] - v[0] * u[1]; }
    if (ar < 0) q = q.reverse();   // same winding as the arcs, so the nonzero union has no holes
    return q;
  }
  function pathOf(sh, grow) {
    const P = new Path2D();
    for (const [x, y, r] of sh.c) { P.moveTo(x + r + grow, y); P.arc(x, y, Math.max(0.5, r + grow), 0, Math.PI * 2); }
    for (const [ax, ay, ra, bx, by, rb] of sh.k || []) {
      const r1 = Math.max(0.5, ra + grow), r2 = Math.max(0.5, rb + grow);
      P.moveTo(ax + r1, ay); P.arc(ax, ay, r1, 0, Math.PI * 2); P.moveTo(bx + r2, by); P.arc(bx, by, r2, 0, Math.PI * 2);
      const q = capQuad(ax, ay, r1, bx, by, r2); if (q) { P.moveTo(q[0][0], q[0][1]); for (let k = 1; k < 4; k++) P.lineTo(q[k][0], q[k][1]); P.closePath(); }
    }
    for (let t of sh.t || []) {
      let ar = 0; for (let k = 0; k < t.length; k++) { const u = t[k], v = t[(k + 1) % t.length]; ar += u[0] * v[1] - v[0] * u[1]; }
      if (ar < 0) t = t.slice().reverse();
      if (grow) { const cx = t.reduce((s, q) => s + q[0], 0) / t.length, cy = t.reduce((s, q) => s + q[1], 0) / t.length;
        t = t.map(q => { const dx = q[0] - cx, dy = q[1] - cy, d = Math.hypot(dx, dy) || 1; return [q[0] + dx / d * grow * 1.4, q[1] + dy / d * grow * 1.4]; }); }
      P.moveTo(t[0][0], t[0][1]); for (let k = 1; k < t.length; k++) P.lineTo(t[k][0], t[k][1]); P.closePath(); }
    return P;
  }

  const PAL = { ink: '#1a120d', tan: '#b07a43', tanD: '#8a5a30', saddle: '#33241a', cream: '#d9bd8c', ear: '#2c1f17', nose: '#0d0907', eye: '#0d0907' };
  const PAL_ID = { body: '#ff0000', head: '#00ff00', muzzle: '#0000ff' };

  // draw one sprite into ctx at origin (anchor = dog ground point); id=true draws flat ID colours
  function draw(ctx, key, K, id) {
    const p = typeof key === 'string' ? parse(key) : key, G = build(p), pr = projector(p, K), R = r => r * K;
    const groups = [];
    const grp = (name, kind) => { const g = { name, kind, sh: { c: [], q: [], t: [] }, ds: [], extra: [] }; groups.push(g); return g; };
    // torso + neck
    const T = grp('torso', 'body');
    const spP = G.sp.map(s => pr(s));
    const CR = (p0, p1, p2, p3, u) => 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u);
    const SPn = G.sp.length, smp = [];
    for (let k = 0; k < SPn - 1; k++) for (let j = 0; j < 4; j++) {
      const u = j / 4, q = i => G.sp[Math.max(0, Math.min(SPn - 1, i))];
      smp.push([0, 1, 2, 3].map(c => CR(q(k - 1)[c], q(k)[c], q(k + 1)[c], q(k + 2)[c], u)));
    }
    smp.push(G.sp[SPn - 1]);
    for (let k = 0; k < smp.length - 1; k++) capsule(T.sh, pr(smp[k]), R(smp[k][3]), pr(smp[k + 1]), R(smp[k + 1][3]));
    const n0 = pr(G.n0), n1 = pr(G.n1);
    capsule(T.sh, n0, R(0.10), n1, R(0.072));
    T.ds.push(...spP.map(s => s.d));
    // legs
    for (const L of G.legs) {
      const g = grp('leg' + L.n, 'body');
      const a = pr(L.top), b = pr(L.j1), c = pr(L.j2), d = pr(L.paw);
      const r0 = L.front ? 0.055 : 0.075, r1 = L.front ? 0.036 : 0.045;
      capsule(g.sh, a, R(r0), b, R(r1)); capsule(g.sh, b, R(r1), c, R(0.026)); capsule(g.sh, c, R(0.026), d, R(0.028));
      g.ds.push(a.d, b.d, c.d, d.d); g.leg = { a, b, c, d, front: L.front };
    }
    // tail
    const Tl = grp('tail', 'body'); const tp = G.tail.map(pr);
    const tr = [0.042, 0.034, 0.026, 0.012];
    for (let k = 0; k < 3; k++) for (let j = 0; j < 3; j++) {
      const u0 = j / 3, u1 = (j + 1) / 3, A = L3(G.tail[k], G.tail[k + 1], u0), Bq = L3(G.tail[k], G.tail[k + 1], u1);
      capsule(Tl.sh, pr(A), R(lerp(tr[k], tr[k + 1], u0)), pr(Bq), R(lerp(tr[k], tr[k + 1], u1)));
    }
    Tl.ds.push(...tp.map(t => t.d));
    // head: skull + muzzle (muzzle is its own ID colour so the head's facing can be measured)
    const H = grp('head', 'head'); const sk = pr(G.sk), mz = pr(G.mz);
    H.sh.c.push([sk.x, sk.y, R(0.078)]);
    const M = { c: [], q: [] }; capsule(M, sk, R(0.055), mz, R(0.03));
    H.muzzle = M; H.ds.push(sk.d, mz.d); H.sk = sk; H.mz = mz;
    // ears (separate groups: the far ear sits behind the skull)
    for (const e of G.ears) {
      const g = grp('ear', 'head'); const pts = e.pts.map(pr);
      g.sh.t.push(pts.map(q => [q.x, q.y])); g.ds.push(pts[1].d + 0.001);
      g.sh.c.push([pts[0].x * 0.5 + pts[2].x * 0.5, pts[0].y * 0.5 + pts[2].y * 0.5, R(0.022)]);
    }
    const depth = g => g.ds.reduce((s, v) => s + v, 0) / g.ds.length;
    groups.sort((a, b) => depth(a) - depth(b));
    const LW = id ? 1.6 : Math.max(1.6, K / 80);
    for (const g of groups) {
      const P = pathOf(g.sh, 0), Pg = pathOf(g.sh, LW);
      const PM = g.muzzle ? pathOf(g.muzzle, 0) : null, PMg = g.muzzle ? pathOf(g.muzzle, LW) : null;
      if (id) {
        ctx.fillStyle = g.kind === 'head' ? PAL_ID.head : PAL_ID.body; ctx.fill(Pg);
        if (PM) { ctx.fillStyle = PAL_ID.muzzle; ctx.fill(PMg); }
        continue;
      }
      const muzzleBehind = g.muzzle && g.mz.d < g.sk.d - 0.01;
      if (g.name === 'head') {
        const skull = () => { ctx.fillStyle = PAL.ink; ctx.fill(Pg); ctx.fillStyle = PAL.tan; ctx.fill(P);
          ctx.save(); ctx.clip(P); ctx.fillStyle = PAL.saddle; const top = pr(add(G.sk, [0, 0.06, 0]));
          ctx.beginPath(); ctx.arc(top.x, top.y, R(0.06), 0, 7); ctx.fill(); ctx.restore(); };
        const muzzle = () => { ctx.fillStyle = PAL.ink; ctx.fill(PMg); ctx.fillStyle = PAL.tan; ctx.fill(PM);
          ctx.save(); ctx.clip(PM); ctx.fillStyle = PAL.saddle; const mt = pr(add(G.mz, [0, 0.02, 0])); ctx.beginPath(); ctx.arc(mt.x, mt.y, R(0.035), 0, 7); ctx.fill(); ctx.restore();
          if (!muzzleBehind) { ctx.fillStyle = PAL.nose; ctx.beginPath(); ctx.arc(g.mz.x, g.mz.y - R(0.006), R(0.017), 0, 7); ctx.fill(); } };
        if (muzzleBehind) { muzzle(); skull(); } else { skull(); muzzle(); }
        for (const e of G.eyes) {
          const c = pr(e.c), look = add(mul(e.n, 0.55), mul([G.mz[0] - G.sk[0], 0, G.mz[2] - G.sk[2]], 5));
          const z = pr(add(G.sk, look)).Z - pr(G.sk).Z;
          if (z > 0.08) { ctx.fillStyle = PAL.eye; ctx.beginPath(); ctx.ellipse(c.x, c.y, R(0.012), R(0.009), 0, 0, 7); ctx.fill(); }
        }
        continue;
      }
      ctx.fillStyle = PAL.ink; ctx.fill(Pg);
      if (g.name === 'torso') {
        ctx.fillStyle = PAL.tan; ctx.fill(P);
        ctx.save(); ctx.clip(P);
        // cream underside and bib, dark saddle over the back: offsets in 3-D so they turn with the body
        ctx.fillStyle = PAL.cream;
        for (let k = 0; k < 3; k++) { const s = G.sp[k]; const q = pr([s[0], s[1] - s[3] * 0.85, 0]); ctx.beginPath(); ctx.arc(q.x, q.y, R(s[3] * 0.62), 0, 7); ctx.fill(); }
        const nb = pr(L3(G.n0, G.n1, 0.4)); ctx.beginPath(); ctx.arc(nb.x, nb.y + R(0.03), R(0.05), 0, 7); ctx.fill();
        {
          const sad = { c: [], q: [] };
          const top = k => { const q = G.sp[k]; return [q[0], q[1] + q[3] * 0.62, 0]; };
          const nt = t => add(L3(G.n0, G.n1, t), [0, 0.05 - 0.02 * t, 0]);
          const chain = [[nt(0.75), 0.03], [nt(0.25), 0.05], [top(0), 0.06], [top(1), 0.11], [top(2), 0.095], [top(3), 0.08], [top(4), 0.075]];
          for (let k = 0; k < chain.length - 1; k++) capsule(sad, pr(chain[k][0]), R(chain[k][1]), pr(chain[k + 1][0]), R(chain[k + 1][1]));
          ctx.fillStyle = PAL.saddle; ctx.fill(pathOf(sad, 0));
        }
        // fur strokes along the back
        ctx.strokeStyle = 'rgba(20,12,8,.55)'; ctx.lineWidth = Math.max(1, K / 160);
        for (let k = 1; k < 5; k++) { const s = G.sp[k]; const a = pr([s[0] + 0.03, s[1] + s[3] * 0.2, 0]), b = pr([s[0] - 0.03, s[1] - s[3] * 0.15, 0]); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
        ctx.restore();
      } else if (g.name.startsWith('leg')) {
        ctx.fillStyle = PAL.tan; ctx.fill(P);
        ctx.save(); ctx.clip(P); ctx.fillStyle = PAL.cream;
        const { c, d } = g.leg; ctx.beginPath(); ctx.arc(c.x, c.y, R(0.05), 0, 7); ctx.arc(d.x, d.y, R(0.05), 0, 7); ctx.fill();
        ctx.restore();
        // far legs read darker
        const near = depth(g) > depth(groups.find(q => q.name === 'torso'));
        if (!near) { ctx.fillStyle = 'rgba(30,18,10,.35)'; ctx.fill(P); }
      } else if (g.name === 'tail') {
        ctx.fillStyle = PAL.tanD; ctx.fill(P);
        const e = tp[3]; ctx.fillStyle = PAL.saddle; ctx.beginPath(); ctx.arc(e.x, e.y, R(0.02), 0, 7); ctx.fill();
      } else if (g.name === 'head') {
        ctx.fillStyle = PAL.tan; ctx.fill(P);
        ctx.save(); ctx.clip(P); ctx.fillStyle = PAL.saddle; const top = pr(add(G.sk, [0, 0.05, 0]));
        ctx.beginPath(); ctx.arc(top.x, top.y, R(0.06), 0, 7); ctx.fill(); ctx.restore();
        ctx.fillStyle = PAL.tan; ctx.fill(PM);
        ctx.save(); ctx.clip(PM); ctx.fillStyle = PAL.saddle; ctx.beginPath(); ctx.arc(g.mz.x, g.mz.y, R(0.055), 0, 7); ctx.fill(); ctx.restore();
        // nose, eyes, mouth line
        ctx.fillStyle = PAL.nose; ctx.beginPath(); ctx.arc(g.mz.x, g.mz.y, R(0.022), 0, 7); ctx.fill();
        for (const e of G.eyes) {
          const c = pr(e.c), nn = pr(add(G.sk, e.n)); const facing = (nn.Z - pr(G.sk).Z) * CE > -0.25;
          if (facing) { ctx.fillStyle = '#e8d4a6'; ctx.beginPath(); ctx.arc(c.x, c.y, R(0.016), 0, 7); ctx.fill(); ctx.fillStyle = PAL.eye; ctx.beginPath(); ctx.arc(c.x, c.y, R(0.011), 0, 7); ctx.fill(); }
        }
      } else if (g.name === 'ear') {
        ctx.fillStyle = PAL.ear; ctx.fill(P);
      }
    }
  }

  // sprite cache: one drawing per key and variant
  const cache = new Map();
  let made = 0;
  function sprite(key, K, variant) {
    const ck = key + '|' + K + '|' + variant; let s = cache.get(ck);
    if (s) return s;
    const W = Math.ceil(K * 1.9), H = Math.ceil(K * 1.4), ox = W / 2, oy = H * 0.86;
    const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
    x.translate(ox, oy); draw(x, key, K, variant === 'id');
    s = { c, ox, oy }; cache.set(ck, s); if (variant === 'ink') made++; return s;
  }
  return { draw, sprite, parse, keyOf, build, STRIDE, NG, DUTY, EL, made: () => made, cache };
})();
if (typeof module !== 'undefined') module.exports = DOG;
