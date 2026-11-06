// 07 · Tying and Gagging — SCION-8 Constraint Sketchpad.
// Every sack is a ring of points solved each frame by iterated relaxation from its rest shape
// (fixed start, fixed iteration count => the picture is a pure function of t). Rope = constraint
// lines added to the victim's graph one by one; each is an inequality |x-cx| <= w + s*|dy| that the
// solver enforces hard after the shape-matching pass. The gag is a last constraint across the top.
// Pass 2: scene() computes the solved state once; draw() renders it whole or by layer ('bg','A','V');
// marks() gives screen boxes; sound() schedules grains (constraint ticks converge as each band locks).
(function () {
  const FLOOR = 820, VX = 1200, CONTACT = 3.2, Z = 1.7, CXw = 990, SY = 900;
  const PH = '#a9f2d2', PHd = 'rgba(169,242,210,', BG = '#04100c', OLD = 'rgba(150,190,170,';
  const DO = {
    R: { n: 2, t0: 1.05, t1: 2.75, order: 'up', ease: 'deliberate', tight: 0.56, rope: 3, sag: 0, tilt: 0 },
    B: { n: 4, t0: 1.0, t1: 2.45, order: 'mid', ease: 'yank', tight: 0.62, rope: 6, sag: 0, tilt: 0 },
    I: { n: 3, t0: 1.0, t1: 2.7, order: 'any', ease: 'hop', tight: 0.7, rope: 3.5, sag: 1, tilt: 1 },
    O: { n: 3, t0: 1.0, t1: 2.6, order: 'down', ease: 'even', tight: 0.6, rope: 2.2, sag: 0, tilt: 0 },
  };
  const scr = (x, y) => [(x - CXw) * Z + 960, (y - FLOOR) * Z + SY];
  const has = (carry, id, tag) => !!(carry && carry[id] && carry[id].indexOf(tag) >= 0);

  // ---------------- rest shapes: rings of points ----------------
  const REST = {};
  function rest(K, id) {
    if (REST[id]) return REST[id];
    const cl = K.cl, c = K.CAST[id], w = c.w, h = c.h, N = 40, pts = [];
    const rb = Math.min(w, h) * 0.22, P = 2 * (w + h);
    for (let i = 0; i < N; i++) {
      let s = (i / N) * P, x, y;
      if (s < w / 2) { x = s; y = 0; }
      else if ((s -= w / 2) < h) { x = w / 2; y = -s; }
      else if ((s -= h) < w) { x = w / 2 - s; y = -h; }
      else if ((s -= w) < h) { x = -w / 2; y = -h + s; }
      else { s -= h; x = -w / 2 + s; y = 0; }
      const ax = Math.abs(x), dyb = -y;
      if (ax > w / 2 - rb && dyb < rb) {
        const cx0 = (w / 2 - rb) * Math.sign(x), cy0 = -rb;
        const vx = x - cx0, vy = y - cy0, L = Math.hypot(vx, vy) || 1;
        x = cx0 + vx / L * rb; y = cy0 + vy / L * rb;
      }
      const f = -y / h;
      if (id === 'B') x *= 1 + 0.09 * Math.sin(Math.PI * cl(0, 1, f));
      if (id === 'I') { x *= 1 + 0.12 * (1 - f); if (f > 0.97) y += 16 * Math.sin(Math.PI * (x / w + 0.5)); }
      if (id === 'R') x *= 1 + 0.05 * Math.sin(Math.PI * cl(0, 1, f * 1.2));
      if (id === 'O' && f > 0.97) y += 4 * Math.sin(Math.PI * (x / w + 0.5));
      if (id !== 'I' && f > 0.97) y += 5 * Math.sin(Math.PI * (x / w + 0.5)) * (id === 'B' ? -0.6 : 1);
      pts.push([x, y]);
    }
    let iL = 0, iR = 0, dL = 1e9, dR = 1e9;
    pts.forEach((p, i) => {
      const a = Math.hypot(p[0] + w / 2, p[1] + h), b = Math.hypot(p[0] - w / 2, p[1] + h);
      if (a < dL) { dL = a; iL = i; } if (b < dR) { dR = b; iR = i; }
    });
    const edges = pts.map((p, i) => { const q = pts[(i + 1) % N]; return Math.hypot(q[0] - p[0], q[1] - p[1]); });
    return (REST[id] = { pts, iL, iR, edges, w, h });
  }

  // ---------------- the solver ----------------
  function solve(K, id, pose, cons, cx, earMode, iters) {
    const R = rest(K, id), N = R.pts.length, h = R.h, fl = pose.floor || FLOOR;
    const cr = Math.cos(pose.rot), sr = Math.sin(pose.rot);
    const piv = pose.rot >= 0 ? R.w / 2 : -R.w / 2;
    const goal = R.pts.map(([x, y]) => {
      let X = x * pose.sx + y * pose.shear, Y = y * pose.sy;
      X -= piv;
      const rx = X * cr - Y * sr, ry = X * sr + Y * cr;
      return [pose.x + rx + piv, fl - pose.lift + ry];
    });
    const p = goal.map(q => [q[0], q[1]]);
    const res = cons.map(() => 0);
    const lim = (c, x, y) => {
      const dy = y - (c.y + c.tilt * (x - cx));
      return c.kind === 'gag' ? (dy < 0 ? c.w + 0.15 * (-dy) : c.w + c.s * dy) : c.w + c.s * Math.abs(dy);
    };
    for (let it = 0; it < iters; it++) {
      const last = it === iters - 1;
      for (let i = 0; i < N; i++) { p[i][0] += (goal[i][0] - p[i][0]) * 0.3; p[i][1] += (goal[i][1] - p[i][1]) * 0.3; }
      for (let i = 0; i < N; i++) {
        const j = (i + 1) % N, a = p[i], b = p[j];
        const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, L0 = R.edges[i] * 1.04;
        if (L > L0) { const k = (L - L0) / L * 0.5; a[0] += dx * k; a[1] += dy * k; b[0] -= dx * k; b[1] -= dy * k; }
      }
      for (let i = 0; i < N; i++) {
        if (p[i][1] > fl) p[i][1] = fl;
        cons.forEach((c, k) => {
          const L = lim(c, p[i][0], p[i][1]), d = p[i][0] - cx;
          if (Math.abs(d) > L) { const nx = cx + Math.sign(d) * L; if (last) res[k] += Math.abs(goal[i][0] - nx); p[i][0] = nx; }
        });
      }
    }
    const ears = [R.iL, R.iR].map((ix, side) => {
      const sg = side ? 1 : -1, b = p[ix];
      let ang, L;
      if (earMode.down) { ang = Math.PI / 2 - sg * 0.22; L = h * 0.85; }
      else { ang = -Math.PI / 2 + sg * (0.75 + earMode.spread); L = Math.min(R.w, h) * 0.16 + 8; }
      ang += pose.rot + sg * earMode.flap;
      let tip = [b[0] + Math.cos(ang) * L, b[1] + Math.sin(ang) * L];
      for (let it = 0; it < 6; it++) {
        cons.forEach(c => {
          const d = tip[0] - cx, Lm = lim(c, tip[0], tip[1]) + 3;
          if (Math.abs(d) > Lm) tip[0] = cx + Math.sign(d) * Lm;
        });
        const dx = tip[0] - b[0], dy = tip[1] - b[1], D = Math.hypot(dx, dy) || 1;
        if (D > L) { tip[0] = b[0] + dx / D * L; tip[1] = b[1] + dy / D * L; }
      }
      return { base: ix, tip, b };
    });
    return { p, ears, res, R, lim, cx };
  }

  // carried constraints (old rope / gag / cinch from earlier shots): weaker, already-settled lines
  function carriedCons(K, id, carry, bottomY) {
    const c = K.CAST[id], out = [];
    if (has(carry, id, 'rope')) [0.3, 0.56].forEach(f => out.push({ y: bottomY - c.h * f, tilt: 0, w: c.w / 2 * 0.9, s: 1.25, kind: 'band', old: 1 }));
    if (has(carry, id, 'cinched')) out.push({ y: bottomY - c.h * 0.8, tilt: 0, w: c.w / 2 * 0.62, s: 1.25, kind: 'band', old: 2 });
    if (has(carry, id, 'gag')) out.push({ y: bottomY - c.h * (id === 'R' ? 0.74 : id === 'I' ? 0.86 : 0.9), tilt: 0, w: c.w / 2 * 0.8, s: 1.2, kind: 'gag', old: 1 });
    return out;
  }

  // ---------------- scene: the whole solved state at t ----------------
  function scene(t, A, V, K, carry) {
    const cl = K.cl, lerp = K.lerp, sm = K.sm, eo = K.eo, CA = K.CAST;
    const dp = DO[A], vc = CA[V], dc = CA[A];
    const n = dp.n, T0 = dp.t0, T1 = dp.t1, lap = (T1 - T0) / n;
    const Rx = vc.w / 2 + dc.w / 2 + 34;
    const startX = 540 + dc.w / 2, endX = 560 + dc.w / 2;
    const fr = [];
    for (let k = 0; k < n; k++) fr.push(0.16 + (0.62 - 0.16) * (n === 1 ? 0.5 : k / (n - 1)));
    let ord = fr.map((_, k) => k);
    if (dp.order === 'down') ord.reverse();
    if (dp.order === 'mid') ord = n === 4 ? [1, 2, 0, 3] : ord;
    if (dp.order === 'any') ord = [1, 0, 2];
    const bands = ord.map((k, j) => {
      const hgt = fr[k] * vc.h;
      const tilt = dp.tilt ? (K.hash(j * 7 + 3) - 0.5) * 0.28 : 0;
      return { j, y: FLOOR - hgt, hgt, tilt, a: T0 + j * lap, b: T0 + (j + 1) * lap };
    });
    const gagY = FLOOR - vc.h * (V === 'I' ? 0.86 : V === 'R' ? 0.74 : 0.9), gagA = T1 + 0.1;

    // doer path
    let dx, behind = 0, th = Math.PI, lift = 0, lean = 0, yank = 0, wind = -1, wu = 0;
    if (t < 0.4) dx = startX;
    else if (t < T0) dx = lerp(startX, VX - Rx, eo(0.4, T0, t));
    else if (t < T1) {
      wind = Math.min(n - 1, Math.floor((t - T0) / lap));
      let u = (t - T0 - wind * lap) / lap;
      if (dp.ease === 'deliberate') u = sm(0, 1, u);
      if (dp.ease === 'yank') u = cl(0, 1, u * 1.15);
      wu = u;
      th = Math.PI - 2 * Math.PI * u;
      dx = VX + Rx * Math.cos(th);
      behind = Math.sin(th);
      lift = Math.max(0, bands[wind].hgt - dc.h * 0.85);
      if (dp.ease === 'hop') lift += 46 * Math.abs(Math.sin(Math.PI * u * 2));
      lean = Math.cos(th - Math.PI / 2) * 0.12 * (A === 'O' ? 0.4 : 1);
    } else if (t < CONTACT + 0.25) {
      dx = VX - Rx;
      const up = sm(gagA - 0.05, gagA + 0.35, t) * (1 - sm(CONTACT, CONTACT + 0.25, t));
      lift = Math.max(0, (FLOOR - gagY) - dc.h * 0.7) * up + (A === 'I' ? 30 * up : 0);
      lean = 0.12 * up;
    } else {
      dx = lerp(VX - Rx, endX, eo(CONTACT + 0.35, 4.6, t));
      lean = -0.1 * Math.sin(Math.PI * sm(CONTACT + 0.25, 4.6, t));
    }
    const pulls = bands.map(b => b.b).concat([CONTACT]);
    pulls.forEach(pt => { const d = t - pt; if (d > 0 && d < 0.35) yank = Math.max(yank, Math.sin(Math.PI * d / 0.35) * (A === 'B' ? 1.6 : A === 'R' ? 1.0 : 0.7)); });
    const dscale = 1 - 0.14 * Math.max(0, behind) + 0.06 * Math.max(0, -behind);
    const dyDepth = -26 * Math.max(0, behind), dfront = 34 * Math.max(0, -behind);
    const doerPose = {
      x: dx, lift: lift - dyDepth, rot: 0, floor: FLOOR + dfront,
      sx: dscale * (1 + 0.05 * yank), sy: dscale * (1 - 0.05 * yank),
      shear: -(lean + 0.07 * yank),
    };
    if (A === 'R') doerPose.rot = 0.05 * Math.sin(t * 3.0) * sm(0.4, 0.9, t) * (1 - sm(4.6, 5.3, t));
    if (A === 'I') doerPose.sy *= 0.97;
    let dEarSp = A === 'B' ? 0.1 : 0;
    if (has(carry, A, 'emptied')) doerPose.sy *= 0.82;
    if (has(carry, A, 'drowsy')) { doerPose.sy *= 0.96; dEarSp -= 0.45; }
    const dCons = carriedCons(K, A, carry, doerPose.floor - doerPose.lift);
    const dsol = solve(K, A, doerPose, dCons, dx, { down: A === 'I', spread: dEarSp, flap: 0.15 * yank }, 8);

    // victim constraints
    const cons = carriedCons(K, V, carry, FLOOR);
    const halfW = vc.w / 2 * (V === 'B' || V === 'I' ? 1.08 : 1.03);
    bands.forEach(b => {
      if (t < b.b) return;
      const k = eo(b.b, b.b + (A === 'B' ? 0.18 : A === 'R' ? 0.45 : 0.3), t);
      cons.push({ y: b.y, tilt: b.tilt, w: lerp(halfW + 6, vc.w / 2 * dp.tight, k), s: 1.25, kind: 'band', ref: b });
    });
    if (t >= CONTACT) {
      const gk = eo(CONTACT, CONTACT + 0.25, t);
      cons.push({ y: gagY, tilt: 0, w: lerp(vc.w / 2 + 8, vc.w / 2 * (V === 'O' ? 0.8 : 0.55), gk), s: 1.2, kind: 'gag' });
    }
    const pre = sm(0.5, 1.2, t);
    const strainEnv = sm(1.1, 1.6, t) * (1 - sm(5.0, 5.35, t));
    const after = sm(CONTACT + 0.1, CONTACT + 0.4, t) * (1 - sm(5.0, 5.35, t));
    let vp = { x: VX, lift: 0, rot: 0, sx: 1, sy: 1, shear: 0 };
    let earFlap = 0, earSpread = 0;
    const osc = (f, ph) => Math.sin(2 * Math.PI * f * t + ph);
    if (V === 'R') {
      vp.rot = 0.04 * pre + strainEnv * 0.16 * osc(1.4, 0) + after * 0.05 * osc(2.8, 1);
      vp.sx = 1 + after * 0.08 * Math.abs(osc(1.4, 0));
      earFlap = 0.25 * strainEnv * osc(2.8, 0);
    }
    if (V === 'B') {
      const sw = Math.abs(osc(1.1, 0.4));
      vp.sx = 1 + 0.05 * pre + strainEnv * 0.2 * sw + after * 0.08 * sw;
      vp.sy = 1 + strainEnv * 0.05 * sw;
      vp.x = VX + strainEnv * 18 * osc(0.55, 0);
      earSpread = 0.15 * strainEnv * sw;
    }
    if (V === 'I') {
      vp.sy = 1 - 0.06 * pre; vp.sx = 1 + 0.04 * pre;
      const tw = Math.exp(-Math.pow((t - 4.1) / 0.12, 2)) + 0.6 * Math.exp(-Math.pow((t - 1.9) / 0.1, 2));
      vp.shear = 0.12 * tw; vp.sx += 0.1 * tw;
    }
    if (V === 'O') {
      vp.sy = 1 + 0.04 * pre;
      const jk = Math.sign(osc(0.9, 0)) * Math.pow(Math.abs(osc(0.9, 0)), 0.3);
      vp.shear = strainEnv * 0.22 * jk;
      vp.sx = 1 + after * 0.1 * Math.abs(jk);
    }
    if (has(carry, V, 'emptied')) vp.sy *= 0.82;
    if (has(carry, V, 'drowsy')) { vp.sy *= 0.96; earSpread -= 0.45; }
    const vsol = solve(K, V, vp, cons, VX, { down: V === 'I', spread: earSpread, flap: earFlap }, 22);
    return { t, A, V, dp, vc, dc, bands, gagY, gagA, T0, T1, n, dx, behind, wind, wu, dsol, vsol, cons, dCons, strainEnv, carry };
  }

  function boxOf(sol, id) {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    const add = q => { x0 = Math.min(x0, q[0]); y0 = Math.min(y0, q[1]); x1 = Math.max(x1, q[0]); y1 = Math.max(y1, q[1]); };
    sol.p.forEach(add); sol.ears.forEach(e => add(e.tip));
    if (id === 'O') { add([x0 - 18, y0 - 22]); add([x1 + 18, y0]); }
    const a = scr(x0, y0), b = scr(x1, y1);
    return { x: Math.round(a[0]), y: Math.round(a[1]), w: Math.round(b[0] - a[0]), h: Math.round(b[1] - a[1]) };
  }

  // ---------------- rendering ----------------
  function render(g, S, K, layer) {
    const { t, A, V, dp, vc, dc, bands, gagY, gagA, T1, dx, behind, wind, wu, dsol, vsol, cons, dCons, strainEnv, carry } = S;
    const W = K.W, H = K.H, cl = K.cl, lerp = K.lerp, sm = K.sm, CA = K.CAST;
    const all = !layer, LB = all || layer === 'bg', LA = all || layer === 'A', LV = all || layer === 'V';

    if (LB) {
      g.fillStyle = BG; g.fillRect(0, 0, W, H);
      g.fillStyle = PHd + '0.10)';
      for (let y = 30; y < H; y += 36) for (let x = 30; x < W; x += 36) g.fillRect(x, y, 2, 2);
    }
    g.save(); g.translate(W / 2, SY); g.scale(Z, Z); g.translate(-CXw, -FLOOR);
    if (LB) {
      const lampX = 840, lampY = 380;
      const glow = g.createRadialGradient(lampX, lampY + 60, 10, lampX, lampY + 160, 560);
      glow.addColorStop(0, 'rgba(120,200,160,0.18)'); glow.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = glow; g.fillRect(300, 200, 1400, 800);
      g.strokeStyle = PHd + '0.55)'; g.lineWidth = 2;
      g.beginPath(); g.moveTo(300, FLOOR + 2); g.lineTo(1700, FLOOR + 2); g.stroke();
      g.strokeStyle = PHd + '0.18)';
      for (let i = 0; i < 9; i++) { const x = 400 + i * 150; g.beginPath(); g.moveTo(x, FLOOR + 2); g.lineTo(x + (x - W / 2) * 0.35, H); g.stroke(); }
      g.strokeStyle = PHd + '0.6)'; g.lineWidth = 2;
      g.beginPath(); g.moveTo(lampX, 200); g.lineTo(lampX, lampY - 60); g.stroke();
      g.beginPath(); g.moveTo(lampX - 40, lampY - 60); g.lineTo(lampX + 40, lampY - 60); g.lineTo(lampX + 90, lampY); g.lineTo(lampX - 90, lampY); g.closePath(); g.stroke();
      g.fillStyle = 'rgba(230,255,240,0.8)'; g.beginPath(); g.arc(lampX, lampY + 8, 9, 0, 7); g.fill();
      g.strokeStyle = PHd + '0.22)';
      g.strokeRect(1470, 560, 110, 260);
    }
    if (layer === 'bg') { g.restore(); return; }

    // ----- helpers -----
    function ringPath(P) {
      g.beginPath();
      const N = P.length;
      g.moveTo((P[N - 1][0] + P[0][0]) / 2, (P[N - 1][1] + P[0][1]) / 2);
      for (let i = 0; i < N; i++) { const a = P[i], b = P[(i + 1) % N]; g.quadraticCurveTo(a[0], a[1], (a[0] + b[0]) / 2, (a[1] + b[1]) / 2); }
      g.closePath();
    }
    function drawSack(id, sol, dim, fillA) {
      if (fillA === undefined) fillA = 1;
      const c = CA[id], P = sol.p;
      const fill = has(carry, id, 'greyed') ? '#a9a79d' : c.fill;
      let minY = 1e9, maxY = -1e9, minX = 1e9, maxX = -1e9;
      P.forEach(q => { minY = Math.min(minY, q[1]); maxY = Math.max(maxY, q[1]); minX = Math.min(minX, q[0]); maxX = Math.max(maxX, q[0]); });
      const hh = maxY - minY;
      const drawEars = () => sol.ears.forEach((e, side) => {
        const ix = e.base, a = P[ix], b = P[(ix + (side ? -3 : 3) + P.length) % P.length];
        g.beginPath();
        if (id === 'I') { const sg = side ? 1 : -1; g.moveTo(a[0] - sg * 10, a[1]); g.quadraticCurveTo(a[0] + sg * 16, a[1] + 6, e.tip[0], e.tip[1]); g.lineTo(e.tip[0] - sg * 12, e.tip[1] - 4); g.quadraticCurveTo(a[0] - sg * 2, a[1] + 30, a[0] - sg * 22, a[1] + 2); }
        else { g.moveTo(b[0], b[1]); g.lineTo(e.tip[0], e.tip[1]); g.lineTo(a[0], a[1]); }
        g.closePath();
        g.fillStyle = fill; g.fill(); g.strokeStyle = PH; g.lineWidth = 2; g.stroke();
      });
      g.save();
      g.globalAlpha = dim * fillA;
      ringPath(P); g.fillStyle = fill; g.fill();
      g.save(); ringPath(P); g.clip();
      const sh = g.createLinearGradient(minX, 0, maxX, 0);
      sh.addColorStop(0, 'rgba(0,20,10,0.25)'); sh.addColorStop(0.5, 'rgba(0,0,0,0)'); sh.addColorStop(1, 'rgba(0,20,10,0.35)');
      g.fillStyle = sh; g.fillRect(minX - 10, minY - 10, maxX - minX + 20, hh + 20);
      if (id === 'R') { g.fillStyle = '#6e3a33'; g.fillRect(minX - 10, minY - 20, maxX - minX + 20, hh * 0.2 + 24); }
      if (id === 'B') {
        g.fillStyle = '#2a2622'; g.fillRect(minX - 10, minY + hh * 0.4 - 9, maxX - minX + 20, 18);
        const wx = (minX + maxX) / 2, wy = minY + hh * 0.68, rr = hh * 0.15;
        g.strokeStyle = '#8a6a3a'; g.lineWidth = 3; g.beginPath(); g.arc(wx, wy, rr, 0, 7); g.stroke();
        g.beginPath(); g.moveTo(wx, wy + rr * 0.8); g.lineTo(wx, wy - rr * 0.75); g.stroke();
        for (let k = 0; k < 4; k++) { const yy = wy - rr * 0.55 + k * rr * 0.3; g.beginPath(); g.moveTo(wx, yy + 8); g.lineTo(wx - 12, yy); g.moveTo(wx, yy + 8); g.lineTo(wx + 12, yy); g.stroke(); }
      }
      // carried marks inside the outline
      if (has(carry, id, 'blot')) { // ink: a filled point-cluster
        g.fillStyle = '#10131a';
        for (let k = 0; k < 7; k++) { const a = K.hash(k * 3.1) * 6.28, r = K.hash(k * 5.3) * hh * 0.12; g.beginPath(); g.arc(minX + (maxX - minX) * 0.62 + Math.cos(a) * r, minY + hh * 0.55 + Math.sin(a) * r, 5 + K.hash(k) * 7, 0, 7); g.fill(); }
      }
      g.restore();
      g.globalAlpha = dim;
      ringPath(P); g.strokeStyle = PH; g.lineWidth = 2.5; g.stroke();
      drawEars();
      g.fillStyle = PHd + '0.9)';
      P.forEach((q, i) => { if (i % 2 === 0) g.fillRect(q[0] - 2, q[1] - 2, 4, 4); });
      if (has(carry, id, 'torn')) { // seam open: a broken edge with the gap marked, flour points falling to the floor
        const a = P[Math.round(P.length * 0.18)], b = P[Math.round(P.length * 0.22)];
        g.strokeStyle = BG; g.lineWidth = 5; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
        g.strokeStyle = PH; g.lineWidth = 1.5; g.beginPath();
        for (let k = 0; k <= 6; k++) { const x = lerp(a[0], b[0], k / 6) + (k % 2 ? -5 : 5), y = lerp(a[1], b[1], k / 6); k ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke();
        g.fillStyle = '#fbf7ee'; for (let k = 0; k < 6; k++) g.fillRect(b[0] + 4 + K.hash(k) * 10, FLOOR - 3 - K.hash(k + 9) * 4, 3, 3);
      }
      if (has(carry, id, 'tag')) { // a pinned label: rectangle, pin point, constraint line
        const pin = P[sol.R.iR + 3] || P[0];
        g.strokeStyle = PH; g.lineWidth = 1.5; g.beginPath(); g.moveTo(pin[0], pin[1]); g.lineTo(pin[0] + 22, pin[1] + 18); g.stroke();
        g.fillStyle = '#e9e3cf'; g.fillRect(pin[0] + 14, pin[1] + 18, 26, 16); g.strokeRect(pin[0] + 14, pin[1] + 18, 26, 16);
        g.beginPath(); g.arc(pin[0], pin[1], 4, 0, 7); g.stroke();
      }
      if (has(carry, id, 'coins')) { // held coins: a stack of small ellipses at the foot
        g.fillStyle = '#d8c070'; g.strokeStyle = '#5a4a20'; g.lineWidth = 1.5;
        for (let k = 0; k < 4; k++) { g.beginPath(); g.ellipse(maxX + 12, FLOOR - 4 - k * 5, 9, 3.5, 0, 0, 7); g.fill(); g.stroke(); }
      }
      g.restore();
    }
    function drawWig(sol, cs, cx, dim) {
      const P = sol.p, R = sol.R, tl = P[R.iL], tr = P[R.iR];
      const askew = has(carry, 'O', 'wig') ? 1 : 0;
      g.save(); g.globalAlpha = dim;
      g.strokeStyle = '#7a3b8f'; g.lineCap = 'round'; g.fillStyle = '#7a3b8f';
      const midx = (tl[0] + tr[0]) / 2 + askew * 14, topy = Math.min(tl[1], tr[1]);
      g.beginPath(); g.ellipse(midx, topy + 2 - askew * 4, (tr[0] - tl[0]) / 2 + 12, 22, askew * 0.25, Math.PI, 0); g.fill();
      for (let s = 0; s < 8; s++) {
        const side = s < 4 ? -1 : 1, k = s % 4;
        if (askew && side < 0 && k > 1) continue; // thinned on the slipped side
        const base = side < 0 ? tl : tr;
        const pts = [];
        for (let j = 0; j <= 8; j++) {
          let x = base[0] + side * (6 + k * 5) + side * Math.sin(j * 0.4) * 4 + askew * 12;
          let y = base[1] - 6 + j * (R.h * (askew && side < 0 ? 0.35 : 0.62) / 8);
          cs.forEach(c => { const L = sol.lim(c, x, y) + 4 + k * 2; const d = x - cx; if (Math.abs(d) > L) x = cx + Math.sign(d) * L; });
          pts.push([x, y]);
        }
        g.lineWidth = 7; g.beginPath(); pts.forEach((q, i) => i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1])); g.stroke();
      }
      g.restore();
    }
    function spanAt(sol, c) {
      let L = 1e9, Rr = -1e9; const P = sol.p, N = P.length, cx = sol.cx;
      for (let i = 0; i < N; i++) {
        const a = P[i], b = P[(i + 1) % N];
        const fa = a[1] - (c.y + c.tilt * (a[0] - cx)), fb = b[1] - (c.y + c.tilt * (b[0] - cx));
        if ((fa <= 0) !== (fb <= 0)) { const u = fa / (fa - fb); const x = lerp(a[0], b[0], u); L = Math.min(L, x); Rr = Math.max(Rr, x); }
      }
      if (L > Rr) { L = cx - c.w; Rr = cx + c.w; }
      return [L, Rr];
    }
    function anchorMark(x, y, load) {
      if (load < 0.04) { g.fillStyle = PHd + '0.9)'; g.fillRect(x - 2.5, y - 2.5, 5, 5); return; }
      const r = 3 + 7 * load;
      g.strokeStyle = 'rgba(235,255,245,' + (0.6 + 0.4 * load) + ')'; g.lineWidth = 2;
      g.beginPath(); g.arc(x, y, r, 0, 7); g.stroke();
      g.beginPath(); g.moveTo(x - r - 4, y); g.lineTo(x + r + 4, y); g.moveTo(x, y - r - 4); g.lineTo(x, y + r + 4); g.stroke();
    }
    const ropeW = dp.rope * Math.min(1, 0.45 + vc.h / 300);
    function ropeLine(x1, y1, x2, y2, a, dash, sagAmt, col, wd) {
      g.save(); g.strokeStyle = (col || 'rgba(225,255,240,') + a + ')'; g.lineWidth = wd || ropeW; g.lineCap = 'round';
      if (dash) g.setLineDash([10, 9]);
      g.beginPath(); g.moveTo(x1, y1);
      if (sagAmt) g.quadraticCurveTo((x1 + x2) / 2, Math.max(y1, y2) + sagAmt, x2, y2); else g.lineTo(x2, y2);
      g.stroke(); g.restore();
    }
    function gagBand(L, Rr, gy, load, old) {
      g.save(); g.lineCap = 'round';
      const fl = (6 * Math.sin(t * 9) * load + 3 * Math.sin(t * 2.3)) * (1 - sm(5.0, 5.35, t)) * (old ? 0 : 1);
      const cloth = old ? '#9e9580' : '#c9b98f';
      g.strokeStyle = cloth; g.lineWidth = 7;
      g.beginPath(); g.moveTo(L - 6, gy + 2); g.quadraticCurveTo(L - 22, gy + 16, L - 30 + fl, gy + 40); g.stroke();
      g.beginPath(); g.moveTo(L - 6, gy + 2); g.quadraticCurveTo(L - 16, gy + 22, L - 14 - fl, gy + 48); g.stroke();
      g.strokeStyle = PH; g.lineWidth = 24; g.beginPath(); g.moveTo(L - 2, gy + 2); g.lineTo(Rr + 2, gy + 2); g.stroke();
      g.strokeStyle = cloth; g.lineWidth = 19; g.beginPath(); g.moveTo(L - 2, gy + 2); g.lineTo(Rr + 2, gy + 2); g.stroke();
      g.strokeStyle = 'rgba(40,30,20,0.45)'; g.lineWidth = 1.5;
      for (let x = L + 6; x < Rr - 2; x += 9) { g.beginPath(); g.moveTo(x, gy - 5); g.lineTo(x + 4, gy + 9); g.stroke(); }
      g.fillStyle = cloth; g.beginPath(); g.arc(L - 6, gy + 2, 10, 0, 7); g.fill();
      g.strokeStyle = PH; g.lineWidth = 2; g.stroke();
      g.restore();
    }
    // draw a sack's constraint set (carried old ones dim; this deed's bright)
    function drawCons(sol, cs, own) {
      cs.forEach((c, k) => {
        const [L, Rr] = spanAt(sol, c), cx = sol.cx;
        const load = own ? cl(0, 1, sol.res[k] / (c.kind === 'gag' ? 60 : 40)) : 0;
        if (c.old) {
          if (c.kind === 'gag') gagBand(L, Rr, c.y, 0, 1);
          else { ropeLine(L, c.y, Rr, c.y, 0.75, false, 0, OLD, 2.5); anchorMark(L, c.y, 0); anchorMark(Rr, c.y, 0); if (c.old === 2) { g.fillStyle = OLD + '0.9)'; g.beginPath(); g.arc(Rr, c.y, 5, 0, 7); g.fill(); } }
          return;
        }
        if (c.kind === 'band') {
          const q = load * 3.5 * Math.sin(t * 47 + k * 2) * (strainEnv > 0 ? sm(0, 0.3, strainEnv) : 0);
          const yl = c.y + c.tilt * (L - cx), yr = c.y + c.tilt * (Rr - cx);
          ropeLine(L, yl, Rr, yr, 0.95, false, q);
          if (A === 'O') {
            g.strokeStyle = PHd + '0.7)'; g.lineWidth = 1.5;
            for (let x = L + 10; x < Rr - 5; x += 12) { const y = lerp(yl, yr, (x - L) / (Rr - L)); g.beginPath(); g.moveTo(x, y - 5); g.lineTo(x, y + 5); g.stroke(); }
          }
          anchorMark(L, yl, load); anchorMark(Rr, yr, load);
          if (A === 'R' && c.ref && c.ref.j === 0) { g.fillStyle = '#e1fff0'; g.beginPath(); g.arc(Rr - 6, yr, 7, 0, 7); g.fill(); }
        } else {
          gagBand(L, Rr, c.y, load, 0);
          anchorMark(L - 4, c.y + 2, load); anchorMark(Rr + 4, c.y + 2, load);
        }
      });
    }

    const hand = dsol.ears[1].tip;
    const doerBehind = behind > 0.02;
    let freeBack = null, freeFront = null;
    if (wind >= 0) {
      const b = bands[wind];
      const [L, Rr] = spanAt(vsol, { y: b.y, tilt: b.tilt, w: vc.w / 2 });
      const yl = b.y + b.tilt * (L - VX), yr = b.y + b.tilt * (Rr - VX);
      if (wu < 0.5) freeBack = [L, yl, hand[0], hand[1]];
      else { freeBack = [L, yl, Rr, yr - 4]; freeFront = [Rr, yr, hand[0], hand[1]]; }
    }
    const sagA = dp.sag ? 26 : 0;
    const over = 1 - sm(vc.w / 2 + dc.w * 0.2, vc.w / 2 + dc.w * 0.55, Math.abs(dx - VX));
    const fa = 1 - 0.6 * over * (t < T1 ? 1 : 0);

    // --- A: the parts of the doer behind the victim ---
    const drawABack = () => {
      if (freeBack) ropeLine(freeBack[0], freeBack[1] - 3, freeBack[2], freeBack[3], 0.4, true, sagA);
      if (doerBehind) { drawSack(A, dsol, 0.55); if (A === 'O') drawWig(dsol, dCons, dx, 0.55); drawCons(dsol, dCons, false); }
    };
    // --- V: the victim with its bands ---
    const drawV = () => {
      cons.forEach(c => { if (c.kind !== 'band' || c.old) return; const [L, Rr] = spanAt(vsol, c); ropeLine(L, c.y + c.tilt * (L - VX) - 3, Rr, c.y + c.tilt * (Rr - VX) - 7, 0.35, true, 0); });
      drawSack(V, vsol, 1);
      if (V === 'O') drawWig(vsol, cons, VX, 1);
      drawCons(vsol, cons, true);
    };
    // --- A: the doer and what it holds, in front ---
    const drawAFront = () => {
      if (t >= gagA && t < CONTACT) {
        const gu = sm(gagA + 0.15, CONTACT, t);
        const [L, Rr] = spanAt(vsol, { y: gagY, tilt: 0, w: vc.w / 2 });
        const x2 = lerp(L, Rr + 10, gu);
        g.save(); g.strokeStyle = '#c9b98f'; g.lineWidth = 13; g.lineCap = 'round';
        g.beginPath(); g.moveTo(hand[0], hand[1]); g.lineTo(L, gagY - 6); g.lineTo(x2, gagY - 6 + 4 * gu); g.stroke(); g.restore();
        g.strokeStyle = PH; g.lineWidth = 2; g.beginPath(); g.arc(x2, gagY - 6, 14, 0, 7); g.stroke();
      }
      if (freeFront) ropeLine(freeFront[0], freeFront[1], freeFront[2], freeFront[3], 0.95, false, sagA);
      if (!doerBehind) { drawSack(A, dsol, 1, fa); if (A === 'O') drawWig(dsol, dCons, dx, fa); drawCons(dsol, dCons, false); }
      if (t >= S.T0 - 0.3 && t < CONTACT + 0.1) {
        g.strokeStyle = 'rgba(225,255,240,0.9)'; g.lineWidth = 2;
        for (let k = 0; k < 3; k++) { g.beginPath(); g.ellipse(hand[0] + 4, hand[1] + 10, 11 - k * 3, 7 - k * 2, 0.3, 0, 7); g.stroke(); }
      }
    };

    if (all) { drawABack(); drawV(); drawAFront(); }
    else if (layer === 'V') drawV();
    else if (layer === 'A') {
      // occlusion inside the doer's own layer: what is behind the victim is erased by the victim's silhouette
      drawABack();
      if (freeBack || doerBehind) {
        g.save(); g.globalCompositeOperation = 'destination-out'; g.fillStyle = '#000';
        ringPath(vsol.p); g.fill();
        vsol.ears.forEach((e, side) => { const a = vsol.p[e.base]; g.beginPath(); g.moveTo(a[0] - 14, a[1] + 6); g.lineTo(e.tip[0], e.tip[1]); g.lineTo(a[0] + 14, a[1] + 6); g.fill(); });
        g.restore();
      }
      drawAFront();
    }
    g.restore();
  }

  // ---------------- sound: grains ----------------
  function sound(ac, out, t0, A, V, K) {
    const mg = ac.createGain(); mg.gain.value = 1.6; mg.connect(out); out = mg;
    const SND = K.SND, H = K.hash, dp = DO[A];
    const S0 = scene(0, A, V, K), bands = S0.bands;
    const panAt = (x) => Math.max(-1, Math.min(1, scr(x, 0)[0] / 960 - 1));
    const dxAt = (t) => scene(t, A, V, K).dx;
    const vPan = panAt(VX);
    const tick = (when, f, a, pan) => SND.grain(ac, out, t0 + when, { f, d: 0.014, a, pan, att: 0.05, type: 'square', noise: 0.15 });
    // relaxation converging: ticks at shrinking intervals, rising toward a locked pitch
    const lock = (when, a, pan, base) => {
      let tt = when, dt = 0.07;
      for (let k = 0; k < 7; k++) { tick(tt, base * (1 + 0.5 * (1 - Math.pow(0.6, k))), a * (1 - k * 0.08), pan); tt += dt; dt *= 0.62; }
      SND.grain(ac, out, t0 + tt, { f: base * 1.5, d: 0.12, a: a * 0.6, pan, att: 0.05 });
    };
    // 1. doer steps on the approach and round the laps
    const stepGap = { R: 0.22, B: 0.3, I: 0.16, O: 0.14 }[A];
    for (let t = 0.45; t < S0.T0; t += stepGap) SND.say(ac, out, A, t0 + t, 'step', 0.8, panAt(dxAt(t)));
    bands.forEach((b, j) => {
      const lapD = b.b - b.a;
      // rope hiss as the line pays out behind and in front
      SND.cloud(ac, out, t0 + b.a + 0.05, lapD * 0.9, 90, { bp: 1500 + j * 200, q: 3, a: 0.025, d: [0.02, 0.06], spread: 0.5 }, u => Math.sin(Math.PI * u));
      if (A === 'I') [0.25, 0.75].forEach(u => SND.say(ac, out, 'I', t0 + b.a + u * lapD, 'land', 0.6, panAt(dxAt(b.a + u * lapD))));
      else for (let k = 0; k < 3; k++) { const tt = b.a + (k + 0.5) / 3 * lapD; SND.say(ac, out, A, t0 + tt, 'step', 0.55, panAt(dxAt(tt))); }
      // the band closes: a cinch grain, the constraint locks, the victim answers
      SND.grain(ac, out, t0 + b.b, { bp: 900, q: 2, d: 0.09, a: A === 'B' ? 0.32 : 0.2, pan: vPan, att: 0.1 });
      lock(b.b + 0.02, A === 'B' ? 0.11 : 0.08, vPan, 1600 + j * 180);
      if (j === 0) SND.say(ac, out, V, t0 + b.b + 0.08, V === 'I' ? 'breathe' : 'react', V === 'I' ? 0.6 : 0.7, vPan);
    });
    // 2. the gag drawn across: a cloth hiss, then CONTACT: cinch thump + locking burst + the victim muffled
    SND.cloud(ac, out, t0 + S0.gagA + 0.1, CONTACT - S0.gagA - 0.1, 110, { bp: 700, q: 1.2, a: 0.035, d: [0.02, 0.07], spread: 0.4 }, u => u);
    SND.thump(ac, out, t0 + CONTACT, 1.0, 70, vPan);
    SND.grain(ac, out, t0 + CONTACT, { bp: 600, q: 1.5, d: 0.16, a: 0.45, pan: vPan, att: 0.08 });
    lock(CONTACT + 0.01, 0.16, vPan, 1200);
    SND.grain(ac, out, t0 + CONTACT + 0.36, { f: 1800, d: 0.5, a: 0.07, pan: vPan, att: 0.03 });
    SND.grain(ac, out, t0 + CONTACT + 0.36, { f: 2700, d: 0.5, a: 0.05, pan: vPan, att: 0.03 });
    SND.say(ac, out, V, t0 + CONTACT + 0.1, V === 'I' ? 'breathe' : 'react', 0.55, vPan);
    // 3. the victim strains; at each push the constraints tick under load and hold
    const peaks = [];
    if (V === 'R') for (let k = 0; k < 12; k++) peaks.push((0.25 + k * 0.5) / 1.4);
    if (V === 'B') for (let k = 0; k < 14; k++) peaks.push(((0.5 + k) * Math.PI - 0.4) / (2 * Math.PI * 1.1));
    if (V === 'O') for (let k = 0; k < 11; k++) peaks.push((k * 0.5) / 0.9 + 0.02);
    if (V === 'I') peaks.push(1.9, 4.1);
    peaks.forEach((p, k) => {
      if (p < 1.5 || p > 5.2 || Math.abs(p - CONTACT) < 0.25) return;
      const after = p > CONTACT;
      const a = (after ? 0.11 : 0.07) * (V === 'B' ? 1.3 : V === 'I' ? 0.8 : 1);
      const nT = 2 + Math.floor(H(k * 3.7 + 1) * 3);
      for (let i = 0; i < nT; i++) tick(p + i * 0.025 + H(k * 11 + i) * 0.01, 2200 + H(k + i * 5) * 900, a, vPan);
      SND.say(ac, out, V, t0 + p, 'step', after ? 0.5 : 0.35, vPan);
      if (after && k % 3 === 0 && V !== 'I') SND.say(ac, out, V, t0 + p + 0.05, 'react', 0.3, vPan);
    });
    // 4. the doer walks back and settles; the victim breathes against the gag
    for (let t = CONTACT + 0.4; t < 4.6; t += stepGap * 1.2) SND.say(ac, out, A, t0 + t, 'step', 0.6, panAt(dxAt(t)));
    SND.say(ac, out, V, t0 + 4.7, 'breathe', 0.6, vPan);
  }

  DEED({
    n: 7, key: 'tying', title: 'Tying and Gagging',
    scion: 8, lineage: 'Ivan Sutherland — Constraint Sketchpad Swarm',
    op: 'The doer circles the victim and each lap adds a constraint line that the relaxation solver enforces, pinching the victim\'s point-ring until it cannot move; a last constraint closes across its top as a gag.',
    made: 'Each sack is a closed ring of about forty points with two ear flaps (and a wig of strand polylines for Ogiva), drawn as a light-pen vector figure over a dim cloth fill on a dark display. The room is a dot raster, a floor line and a line-drawn lamp; rope is bright constraint lines with Sketchpad-style anchor marks and the gag is a cloth band with a knot.',
    moved: 'Every frame, each ring starts at its rest shape and is relaxed for a fixed number of passes toward a goal pose (lean, rock, swell, hop) while floor, edge-length and rope inequality constraints are projected hard. The doer travels an ellipse round the victim, behind then in front, and every completed lap switches on and tightens a new band; the victim\'s straining is a goal the solver cannot reach.',
    contact: CONTACT,
    leaves: { A: [], V: ['rope', 'gag'] },
    layers: ['bg', 'V', 'A'],
    draw(g, t, A, V, K, opt) {
      opt = opt || {};
      render(g, scene(t, A, V, K, opt.carry), K, opt.layer);
    },
    marks(t, A, V, K, opt) {
      const S = scene(t, A, V, K, opt && opt.carry);
      return { A: boxOf(S.dsol, A), V: boxOf(S.vsol, V) };
    },
    sound,
  });
})();
