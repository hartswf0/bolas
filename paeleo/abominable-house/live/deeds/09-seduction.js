// 09 · SEDUCTION — SCION-6 John Whitney, Harmonic Motion Orchestra
// Every moving quantity is a sinusoid of a phase. Each sack is an oscillator with its own rate
// (B 3/8 Hz, R 1/2 Hz, I 3/4 Hz, O 1 Hz: the harmonic numbers 3, 4, 6, 8 over 1/8 Hz). The doer's phase pulls
// the victim's phase: phiV = phiV_free + s(t) * (phiA - phiV_free - 2*pi*m). When s reaches 1 they are in unison.
// Sound uses the same numbers: each sack's tone is 110 Hz x its harmonic number, pulsed at every half-cycle of
// its sway; the victim's pitch and pulse slide onto the doer's until they sound as one.
// The rose that blooms is r = cos(k*theta) with k = the pair's harmonic ratio.
// Invariant (numerical): for t >= contact, phiV(t) - phiA(t) is an exact multiple of 2*pi.
(function () {
  const TAU = Math.PI * 2, G = 850, TC = 3.0, SC = 1.0;
  const CH = {
    R: { f: 0.5,   n: 4, a: 0.10, p: 4.2, ear: 15, acc: '#c86a5e', cloth: '#cdb48a', share: 0.22, dly: 0.25, rock: 1, sag: 0,   flop: 0 },
    B: { f: 0.375, n: 3, a: 0.07, p: 2.7, ear: 18, acc: '#e0ac48', cloth: '#e3cfa6', share: 0.12, dly: -0.15, rock: 0, sag: 0,  flop: 0 },
    I: { f: 0.75,  n: 6, a: 0.15, p: 3.4, ear: 0,  acc: '#93b6dc', cloth: '#d9c59c', share: 0.42, dly: -0.4, rock: 0, sag: 0.2, flop: 1 },
    O: { f: 1.0,   n: 8, a: 0.05, p: 7,   ear: 4,  acc: '#b872d8', cloth: '#efe2c4', share: 0.3,  dly: 0.75, rock: 0, sag: 0,   flop: 0 }
  };
  const has = (carry, id, tag) => !!(carry && carry[id] && carry[id].indexOf(tag) >= 0);

  // ---- the score: every quantity of the shot as a function of t (pure)
  function ST(t, A, V, K, carry) {
    const cA = CH[A], cV = CH[V];
    const kA = dims(A, K, carry), kV = dims(V, K, carry);
    const te = Math.min(Math.max(t, 0), 5.4);            // held after-state: oscillators stop advancing
    const t0 = 1.0 + cV.dly;
    let u = K.cl(0, 1, (te - t0) / (TC - t0));
    if (A === 'B') u = 1 - Math.pow(1 - u, 2.4);           // strong: takes hold at once
    else if (A === 'R') u = u * u * (3 - 2 * u);            // deliberate
    else if (A === 'I') u = K.cl(0, 1, u * u * (3 - 2 * u) + 0.09 * Math.sin(u * Math.PI * 3) * (1 - u)); // playful
    else u = u * u * u * (u * (u * 6 - 15) + 10);           // precise
    if (V === 'O') u = Math.pow(u, 3.2);                    // vain: holds out, then snaps
    else if (V === 'I') u = Math.pow(u, 0.55);              // listless: gives in at once
    else if (V === 'B') u = Math.pow(u, 0.75);              // impressionable
    const s = u;
    const phA = TAU * cA.f * te;
    const pVf = TAU * cV.f * te + 2.1;
    const dAt = (T) => TAU * (cA.f - cV.f) * T - 2.1;
    const m = Math.round(dAt(TC) / TAU);
    const phV = pVf + s * (dAt(te) - TAU * m);
    const env = 1 - 0.75 * K.sm(TC, 5.3, te);
    const aU = 0.5 * (cA.a + cV.a) * 0.7;
    const drA = has(carry, A, 'drowsy') ? 0.6 : 1, drV = has(carry, V, 'drowsy') ? 0.6 : 1;
    const ampA = K.lerp(cA.a * drA, aU, s) * env, ampV = K.lerp(cV.a * drV, aU, s) * env;
    const sL = K.sm(TC - 0.9, TC + 0.5, te);
    const th = 0.2, hS = Math.min(kA.h, kV.h);
    const shA = hS * Math.tan(th) * (hS / kA.h), shV = hS * Math.tan(th) * (hS / kV.h);
    const Dfin = (kA.w + kV.w) / 2 + shA + shV - 8;
    const xA0 = 700, xV0 = 1220, tot = (xV0 - xA0) - Dfin;
    const sM = K.sm(t0 - 0.1, TC + 0.15, te) * 0.35 + s * 0.65;
    const xA = xA0 + cA.share * tot * sM, xV = xV0 - (1 - cA.share) * tot * sM;
    const wA = TAU * cA.f, wV = K.lerp(TAU * cV.f, TAU * cA.f, s);
    return { A, V, cA, cV, kA, kV, te, t0, s, phA, phV, ampA, ampV, sL, th, xA, xV, wA, wV, carry, K };
  }
  function dims(id, K, carry) {
    const k = K.CAST[id];
    return has(carry, id, 'emptied') ? { w: k.w * 1.04, h: k.h * 0.8, emptied: 1 } : { w: k.w, h: k.h, emptied: 0 };
  }

  // ---- body: a deformation field D(x,y) driven by the body's phase
  function body(S, id, role, ph, lean, amp) {
    const c = CH[id], k = role === 'A' ? S.kA : S.kV, h = k.h, w = k.w;
    let cx = role === 'A' ? S.xA : S.xV;
    const theta = lean + amp * Math.sin(ph);
    if (c.rock) cx += theta * h * 0.45;
    const br = Math.sin(2 * ph);
    const D = (x, y) => {
      const yy = y * (1 + 0.014 * br), b = yy / h;
      let X = cx + x * (1 - 0.01 * br) + yy * Math.tan(theta) * b;
      if (c.flop) X += h * 0.1 * Math.sin(2 * ph + 1.2) * b * b * b;
      return [X, G - yy];
    };
    const cin = has(S.carry, id, 'cinched'), drowsy = has(S.carry, id, 'drowsy');
    const earPerk = (role === 'V' ? 1 + 0.8 * S.sL : 1) * (drowsy ? 0.4 : 1);
    const sag = c.sag + (k.emptied ? 0.12 : 0);
    const pts = [], N = 96;
    for (let i = 0; i < N; i++) {
      const al = i / N * TAU, cs = Math.cos(al), sn = Math.sin(al);
      let x = w / 2 * Math.sign(cs) * Math.pow(Math.abs(cs), 2 / c.p);
      const yl = Math.sign(sn) * Math.pow(Math.abs(sn), 2 / c.p);
      let y = h / 2 + h / 2 * yl;
      if (yl > 0 && sag) y -= sag * h * (1 - Math.pow(2 * x / w, 2)) * Math.pow(yl, 3);
      if (cin) x *= 1 - 0.28 * Math.exp(-Math.pow((y / h - 0.8) / 0.07, 2));
      const e = Math.exp(-Math.pow((al - Math.PI / 4) / 0.12, 2)) + Math.exp(-Math.pow((al - 3 * Math.PI / 4) / 0.12, 2));
      y += c.ear * earPerk * e; x += Math.sign(cs) * c.ear * 0.45 * e;
      pts.push(D(x, y));
    }
    return { id, role, c, k, D, pts, h, w, ph, theta, sag };
  }
  function bodies(S) {
    return {
      bA: body(S, S.A, 'A', S.phA, S.th * S.sL, S.ampA),
      bV: body(S, S.V, 'V', S.phV, -S.th * S.sL, S.ampV)
    };
  }
  function box(Bd) {
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (const p of Bd.pts) { x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]); }
    const pad = Bd.id === 'I' ? 16 : Bd.id === 'O' ? 10 : 2;
    x0 -= pad; x1 += pad; if (Bd.id === 'O') y0 -= 14;
    // stage scale about (960, G)
    const X = (x) => 960 + (x - 960) * SC, Y = (y) => G + (y - G) * SC;
    return { x: Math.round(X(x0)), y: Math.round(Y(y0)), w: Math.round((x1 - x0) * SC), h: Math.round((y1 - y0) * SC) };
  }

  // ---- drawing helpers
  function path(g, pts) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath(); }
  function band(g, Bd, y0, y1, col) {
    const P = [];
    for (let i = 0; i <= 12; i++) P.push(Bd.D(-Bd.w + 2 * Bd.w * i / 12, y0));
    for (let i = 12; i >= 0; i--) P.push(Bd.D(-Bd.w + 2 * Bd.w * i / 12, y1));
    g.save(); path(g, Bd.pts); g.clip(); g.fillStyle = col; path(g, P); g.fill(); g.restore();
  }
  function dotsAlong(g, pts, step, r, col, closed) {
    g.fillStyle = col; let acc = 0;
    const n = pts.length, L = closed ? n : n - 1;
    for (let i = 0; i < L; i++) {
      const p = pts[i], q = pts[(i + 1) % n], dx = q[0] - p[0], dy = q[1] - p[1], d = Math.hypot(dx, dy);
      while (acc < d) { const f = acc / d; g.beginPath(); g.arc(p[0] + dx * f, p[1] + dy * f, r, 0, TAU); g.fill(); acc += step; }
      acc -= d;
    }
  }
  function dot(g, p, r, col) { g.fillStyle = col; g.beginPath(); g.arc(p[0], p[1], r, 0, TAU); g.fill(); }

  function drawBody(g, S, Bd) {
    const { c, D, w, h, ph, id } = Bd, K = S.K, carry = S.carry;
    const grey = has(carry, id, 'greyed');
    const cloth = grey ? '#a39f95' : c.cloth;
    const base = D(0, 0);
    g.fillStyle = 'rgba(0,0,0,0.45)'; g.beginPath(); g.ellipse(base[0], G + 4, w * 0.62, 10, 0, 0, TAU); g.fill();
    if (id === 'I') {
      for (const side of [-1, 1]) {
        const top = D(side * w * 0.42, h * (1 - Bd.sag * 0.6) - 2);
        const P = [top];
        const lift = (Bd.role === 'V' && !has(carry, id, 'drowsy')) ? S.sL * (side === (S.xA < S.xV ? -1 : 1) ? 1.25 : 0.25) : 0;
        for (let j = 1; j <= 11; j++) {
          const a = lift * (1 - j / 16);
          const sw = 2.4 * Math.sin(ph - j * 0.45) * (j / 11);
          const q = P[j - 1]; P.push([q[0] + side * (Math.sin(a) * 6.5) + side * 0.9 + sw, q[1] + Math.cos(a) * 6.5]);
        }
        g.strokeStyle = cloth; g.lineWidth = 15; g.lineCap = 'round'; g.lineJoin = 'round';
        g.beginPath(); g.moveTo(P[0][0], P[0][1]); P.forEach(p => g.lineTo(p[0], p[1])); g.stroke();
        g.strokeStyle = 'rgba(60,45,30,0.35)'; g.lineWidth = 2; g.stroke();
        dotsAlong(g, P, 7, 1.6, 'rgba(251,247,238,0.75)', false);
      }
    }
    const lit = g.createLinearGradient(base[0] - w, G - h, base[0] + w, G);
    lit.addColorStop(0, cloth); lit.addColorStop(1, grey ? '#55534e' : '#6d5c44');
    path(g, Bd.pts); g.fillStyle = lit; g.fill();
    if (id === 'R') {
      band(g, Bd, h * 0.8, h + 40, '#6e3a33');
      const P = []; for (let i = 0; i <= 16; i++) P.push(D(-w / 2 + w * i / 16, h * 0.8 - 3));
      dotsAlong(g, P, 9, 2.2, '#a8574c', false);
    }
    if (id === 'B') {
      band(g, Bd, h * 0.37, h * 0.44, '#2a2622');
      const cy = h * 0.68, R0 = w * 0.15, ring = [];
      for (let i = 0; i < 40; i++) ring.push(D(R0 * Math.cos(i / 40 * TAU), cy + R0 * Math.sin(i / 40 * TAU)));
      dotsAlong(g, ring, 7, 2.4, '#7a5a30', true);
      g.fillStyle = '#7a5a30';
      for (let j = 0; j < 6; j++) {
        const yy = cy - R0 * 0.7 + j * R0 * 0.26;
        const p0 = D(0, yy); g.beginPath(); g.arc(p0[0], p0[1], 2.6, 0, TAU); g.fill();
        if (j > 0) for (const sd of [-1, 1]) { const p1 = D(sd * R0 * 0.3, yy + R0 * 0.12); g.beginPath(); g.ellipse(p1[0], p1[1], 5, 2.4, sd * 0.6, 0, TAU); g.fill(); }
      }
    }
    carried(g, S, Bd);
    dotsAlong(g, Bd.pts, 7, 1.9, 'rgba(251,247,238,0.9)', true);
    if (id === 'O') {
      const off = has(carry, 'O', 'wig');
      g.save();
      if (off) { const p = D(0, h); g.translate(p[0], p[1]); g.rotate(0.38); g.translate(-p[0] + 10, -p[1] + 6); }
      const cap = [];
      for (let i = 0; i <= 20; i++) { const a = Math.PI * i / 20; cap.push(D(-Math.cos(a) * (w / 2 + 6), h * 0.74 + Math.sin(a) * (h * 0.26 + 14))); }
      g.fillStyle = '#7a3b8f'; path(g, cap); g.fill();
      g.strokeStyle = '#7a3b8f'; g.lineCap = 'round'; g.lineWidth = 7;
      for (const sd of [-1, 1]) for (let q = 0; q < 4; q++) {
        const anc = D(sd * (w / 2 + 2 - q * 6), h * (0.9 - q * 0.04));
        g.beginPath(); g.moveTo(anc[0], anc[1]); let X = anc[0], Y = anc[1];
        for (let j = 1; j <= 10; j++) { X += sd * 1.2 + 2.4 * Math.sin(ph - j * 0.5 - q * 0.4) + Math.tan(Bd.theta) * -5; Y += h * 0.05; g.lineTo(X, Y); }
        g.stroke();
      }
      dotsAlong(g, cap, 8, 1.8, '#c79ad8', false);
      g.restore();
    }
  }

  // carried damage, drawn as dotted marks mapped through the same harmonic bend
  function carried(g, S, Bd) {
    const { D, w, h, id } = Bd, cr = S.carry;
    if (!cr || !cr[id]) return;
    const row = (y, x0, x1, n) => { const P = []; for (let i = 0; i <= n; i++) P.push(D(K_lerp(x0, x1, i / n), y)); return P; };
    if (has(cr, id, 'rope')) for (const yy of [0.3, 0.62]) {
      const P = row(h * yy, -w / 2, w / 2, 14); g.save(); path(g, Bd.pts); g.clip();
      g.strokeStyle = '#8a6a3e'; g.lineWidth = 5; g.beginPath(); P.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); g.restore();
      dotsAlong(g, P, 6, 1.6, '#c9a46a', false); dot(g, D(w * 0.18, h * yy), 5, '#8a6a3e');
    }
    if (has(cr, id, 'gag')) band(g, Bd, h * 0.7, h * 0.78, '#4a4038');
    if (has(cr, id, 'blot')) for (let i = 0; i < 18; i++) {
      const a = i * 2.39996, r = 3 + Math.sqrt(i) * 5; dot(g, D(-w * 0.15 + r * Math.cos(a), h * 0.5 + r * Math.sin(a)), 3.2, '#16182a');
    }
    if (has(cr, id, 'tag')) {
      const p = D(w * 0.22, h * 0.72); g.save(); g.translate(p[0], p[1]); g.rotate(0.15 + Bd.theta);
      g.fillStyle = '#f4efe2'; g.fillRect(-11, -7, 22, 15); g.restore(); dot(g, p, 2.4, '#b23a2e');
    }
    if (has(cr, id, 'torn')) {
      const P = []; for (let i = 0; i <= 8; i++) P.push(D(w * 0.36 + (i % 2 ? 6 : -6), h * (0.25 + i * 0.06)));
      g.strokeStyle = '#3b3026'; g.lineWidth = 2.5; g.beginPath(); P.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke();
      for (let i = 0; i < 7; i++) dot(g, D(w * 0.4 + i * 2, h * (0.25 - i * 0.035)), 2, '#fbf7ee');
    }
    if (has(cr, id, 'coins')) for (let i = 0; i < 3; i++) dot(g, D(-w * 0.2 + i * 9, 6 + (i % 2) * 5), 5, '#d8b247');
    if (has(cr, id, 'cinched')) dotsAlong(g, row(h * 0.8, -w * 0.42, w * 0.42, 8), 5, 1.8, '#8a6a3e', false);
  }
  const K_lerp = (a, b, u) => a + (b - a) * u;

  function drawBG(g, S) {
    const { K, cA, cV, phA, phV, te } = S, W = K.W, H = K.H;
    const wall = g.createLinearGradient(0, 0, 0, G); wall.addColorStop(0, '#07080f'); wall.addColorStop(1, '#171a28');
    g.fillStyle = wall; g.fillRect(0, 0, W, G);
    const fl = g.createLinearGradient(0, G, 0, H); fl.addColorStop(0, '#221d16'); fl.addColorStop(1, '#0b0a08');
    g.fillStyle = fl; g.fillRect(0, G, W, H - G);
    const pool = g.createRadialGradient(960, G, 20, 960, G, 700);
    pool.addColorStop(0, 'rgba(255,214,150,0.22)'); pool.addColorStop(1, 'rgba(255,214,150,0)');
    g.fillStyle = pool; g.fillRect(0, 0, W, H);
    const glow = g.createRadialGradient(960, 190, 10, 960, 190, 900);
    glow.addColorStop(0, 'rgba(255,220,160,0.28)'); glow.addColorStop(1, 'rgba(255,220,160,0)');
    g.fillStyle = glow; g.fillRect(0, 0, W, H);
    g.fillStyle = 'rgba(251,247,238,0.18)';
    for (let x = 6; x < W; x += 14) { g.beginPath(); g.arc(x, G, 1.4, 0, TAU); g.fill(); }
    g.strokeStyle = '#2a2a30'; g.lineWidth = 3; g.beginPath(); g.moveTo(960, 0); g.lineTo(960, 160); g.stroke();
    const lock = K.sm(TC - 0.5, TC + 0.2, te);
    for (let j = 0; j < 6; j++) {
      const r = 70 + j * 30, M = 24, useA = j % 2 === 0;
      const rot = (useA ? phA : phV) / 8;
      g.fillStyle = useA ? cA.acc : cV.acc; g.globalAlpha = 0.25 + 0.35 * lock;
      for (let q = 0; q < M; q++) {
        const a = rot + q / M * TAU, y = 190 + r * Math.sin(a) * 0.62;
        if (y > 520) continue;
        g.beginPath(); g.arc(960 + r * Math.cos(a), y, 2.3, 0, TAU); g.fill();
      }
    }
    g.globalAlpha = 1;
    g.fillStyle = '#fff3d6'; g.beginPath(); g.arc(960, 196, 14, 0, TAU); g.fill();
    g.fillStyle = '#3a2f28'; g.beginPath(); g.moveTo(915, 190); g.lineTo(1005, 190); g.lineTo(980, 150); g.lineTo(940, 150); g.closePath(); g.fill();
  }

  // phase echoes: the outline at earlier moments, so each body's rate is visible in a still frame
  function echo(g, S, role) {
    const id = role === 'A' ? S.A : S.V, c = CH[id];
    const ph = role === 'A' ? S.phA : S.phV, w = role === 'A' ? S.wA : S.wV;
    const lean = (role === 'A' ? 1 : -1) * S.th * S.sL, amp = role === 'A' ? S.ampA : S.ampV;
    for (let j = 4; j >= 1; j--) {
      const E = body(S, id, role, ph - j * 0.13 * w, lean, amp);
      g.globalAlpha = 0.5 * (1 - j / 5); dotsAlong(g, E.pts, 9, 2, c.acc, true);
    }
    g.globalAlpha = 1;
  }

  // the doer's offering: stem, bud, thread of the pull, rose
  function drawGift(g, S, bA, bV) {
    const { K, A, V, cA, cV, kA, kV, te, s, phA, phV } = S;
    const topA = bA.D(0, kA.h), topV = bV.D(0, kV.h);
    const SB = bA.D(kA.w * 0.3, kA.h * (1 - bA.sag) * 0.97);
    const grow = K.eo(0.45, 2.0, te);
    const lift = { R: 60, B: 55, I: 75, O: 50 }[A];
    const F0 = [K.lerp(SB[0], topV[0], 0.42), Math.min(SB[1], topV[1]) - lift - 30];
    const F1 = [(SB[0] + topV[0]) / 2 + 4, Math.min(topA[1], topV[1]) - 98];
    const swing = 1 - 0.75 * s;
    const F = [K.lerp(F0[0], F1[0], s) + 14 * Math.sin(phA) * swing, K.lerp(F0[1], F1[1], s) + 7 * Math.sin(2 * phA) * swing];
    const stem = [];
    const cpx = A === 'O' ? (SB[0] + F[0]) / 2 : SB[0] + 6, cpy = A === 'O' ? (SB[1] + F[1]) / 2 : F[1] + 10;
    for (let i = 0; i <= 40; i++) {
      const v = i / 40 * grow, w1 = 1 - v;
      let x = w1 * w1 * SB[0] + 2 * w1 * v * cpx + v * v * F[0], y = w1 * w1 * SB[1] + 2 * w1 * v * cpy + v * v * F[1];
      if (A === 'I') x += 9 * Math.sin(v * 14 - phA) * v * (1 - v) * 4;
      stem.push([x, y]);
    }
    const tip = stem[stem.length - 1];
    if (grow > 0.02) {
      g.strokeStyle = '#4f6b3c'; g.lineWidth = A === 'B' ? 5 : 3; g.lineCap = 'round';
      g.beginPath(); g.moveTo(stem[0][0], stem[0][1]); stem.forEach(p => g.lineTo(p[0], p[1])); g.stroke();
      dotsAlong(g, stem, 8, A === 'B' ? 2.4 : 1.7, '#8fb36c', false);
    }
    const thrA = K.sm(1.2, 1.7, te) * (1 - K.sm(TC - 0.3, TC + 0.3, te));
    if (thrA > 0.01) {
      const N = 46;
      for (let j = 0; j < N; j++) {
        const v = j / (N - 1);
        const bx = K.lerp(tip[0], topV[0], v), by = K.lerp(tip[1], topV[1] - 8, v) + 26 * Math.sin(Math.PI * v);
        const o = 13 * (1 - v) * Math.sin(phA * 2 - v * 9) + 13 * v * Math.sin(phV * 2 - (1 - v) * 9);
        g.globalAlpha = thrA * (0.55 + 0.45 * Math.sin(Math.PI * v));
        g.fillStyle = (v < 0.5 + 0.5 * s) ? cA.acc : cV.acc;
        g.beginPath(); g.arc(bx, by + o, 2.4, 0, TAU); g.fill();
      }
      g.globalAlpha = 1;
    }
    if (grow > 0.6) {
      let n = Math.max(cA.n, cV.n), d = Math.min(cA.n, cV.n);
      const gcd = (a, b) => b ? gcd(b, a % b) : a; const q = gcd(n, d); n /= q; d /= q;
      const k = n / d, span = ((n * d) % 2 ? Math.PI : TAU) * d;
      const bloom = K.eo(TC - 0.15, TC + 0.7, te);
      const Rr = 9 + 58 * bloom;
      const rot = phA * 0.04 * (1 - s) + s * 0.3;
      const P = 280 * d;
      if (bloom > 0.01) { g.fillStyle = 'rgba(255,230,200,' + (0.12 * bloom) + ')'; g.beginPath(); g.arc(tip[0], tip[1], Rr * 1.15, 0, TAU); g.fill(); }
      for (let i = 0; i < P; i++) {
        const a = i / P * span, r = Rr * Math.cos(k * a);
        g.fillStyle = (Math.floor(i / 7) % 2) ? cA.acc : cV.acc;
        g.globalAlpha = bloom > 0.01 ? 0.9 : 0.8;
        g.beginPath(); g.arc(tip[0] + r * Math.cos(a + rot), tip[1] + r * Math.sin(a + rot), bloom > 0.01 ? 1.9 : 1.3, 0, TAU); g.fill();
      }
      g.globalAlpha = 1;
      dot(g, tip, 3 + 3 * bloom, '#fff3d6');
    }
  }

  DEED({
    n: 9, key: 'seduction', title: 'Seduction',
    scion: 6, lineage: 'John Whitney — Harmonic Motion Orchestra',
    op: 'The doer sways at its own frequency and the victim at another; the doer\'s rhythm pulls the victim\'s phase and frequency until they lock in unison, lean together, and a rose of their frequency ratio blooms between them.',
    made: 'Each sack is a superellipse contour bent and breathed by sinusoids of its own phase, drawn as a filled cloth body with an engraved dotted outline; shawl, belt, wheat stencil, ears and wig are mapped through the same harmonic bend. The room is a dark boarding-house wall under a hanging lamp whose halo is a bank of dotted rings, alternate rings turning with the doer\'s and the victim\'s phase.',
    moved: 'Each sack sways at a fixed rational frequency and amplitude that is its character; the doer grows a stem whose bud and dotted thread vibrate at the doer\'s rate, and the victim\'s phase is interpolated onto the doer\'s until the two lock, glide together and lean in. At lock the lamp rings align into spokes and a rose with k equal to their frequency ratio blooms between their heads.',
    contact: TC,
    leaves: { A: [], V: ['drowsy'] },
    draw(g, t, A, V, K, opt) {
      opt = opt || {};
      const L = opt.layer, S = ST(t, A, V, K, opt.carry);
      if (!L || L === 'bg') drawBG(g, S);
      if (L === 'bg') return;
      const { bA, bV } = bodies(S);
      g.save(); g.translate(960, G); g.scale(SC, SC); g.translate(-960, -G);
      if (!L || L === 'V') { echo(g, S, 'V'); drawBody(g, S, bV); }
      if (!L || L === 'A') { echo(g, S, 'A'); drawBody(g, S, bA); drawGift(g, S, bA, bV); }
      g.restore();
    },
    marks(t, A, V, K) {
      const S = ST(t, A, V, K), { bA, bV } = bodies(S);
      return { A: box(bA), V: box(bV) };
    },
    // Sound: one harmonic series on 110 Hz. Each sack's tone = 110 x its harmonic number (B 3, R 4, I 6, O 8),
    // struck as a grain at every half-cycle of its sway. The victim's tone and pulse slide onto the doer's;
    // at contact both sound the same pitch on the same beat and the rose sounds as a chord of the pair's ratio.
    sound(ac, out, t0, A, V, K) {
      const bus = ac.createGain(); bus.gain.value = 0.8; bus.connect(out); out = bus;
      const SND = K.SND, cA = CH[A], cV = CH[V];
      const pan = (x) => K.cl(-1, 1, (960 + (x - 960) * SC) / 960 - 1);
      const mid = (f) => 69 + 12 * Math.log2(f / 440);
      const fA = 110 * cA.n, fV0 = 110 * cV.n;
      // sway pulses: detect half-cycle crossings of each phase
      let prevA = null, prevV = null, prevX = null;
      for (let i = 0; i <= 5400; i++) {
        const t = i / 1000, S = ST(t, A, V, K);
        const qA = Math.floor(S.phA / Math.PI), qV = Math.floor(S.phV / Math.PI);
        const fV = fV0 * Math.pow(fA / fV0, S.s);             // victim's pitch slides onto the doer's
        const lockA = 0.5 + 0.5 * S.s;
        if (prevA !== null && qA !== prevA && t > 0.05) {
          SND.grain(ac, out, t0 + t, { f: fA, d: 0.16, a: 0.09, pan: pan(S.xA), att: 0.08, type: 'triangle' });
          SND.say(ac, out, A, t0 + t, 'tick', 0.6, pan(S.xA));
        }
        if (prevV !== null && qV !== prevV && t > 0.05) {
          SND.grain(ac, out, t0 + t, { f: fV, d: 0.16, a: 0.09 * (S.s > 0.98 ? 0.8 : 1), pan: pan(S.xV), att: 0.08, type: 'triangle' });
          SND.say(ac, out, V, t0 + t, 'tick', 0.6, pan(S.xV));
          // steps while the victim is pulled across the floor, on its own beat
          if (prevX !== null && Math.abs(S.xV - prevX) > 0.08) SND.say(ac, out, V, t0 + t, 'step', 0.6, pan(S.xV));
        }
        prevA = qA; prevV = qV; prevX = S.xV;
        // sustained tones: a light cloud of grains at each current pitch, the victim's drifting
        if (i % 40 === 0) {
          SND.grain(ac, out, t0 + t, { f: fA, d: 0.09, a: 0.018 * lockA, pan: pan(S.xA), type: 'sine' });
          SND.grain(ac, out, t0 + t + 0.02, { f: fV, d: 0.09, a: 0.018, pan: pan(S.xV), type: 'sine' });
        }
      }
      // the stem grows: rising harmonics of the doer's tone
      for (let j = 0; j < 7; j++) {
        const tt = 0.5 + j * 0.22, S = ST(tt, A, V, K);
        SND.grain(ac, out, t0 + tt, { f: fA * (j + 2) / 2, d: 0.12, a: 0.05, pan: pan(S.xA + 40), att: 0.1, type: 'sine' });
      }
      // breaths as they sway near
      SND.say(ac, out, A, t0 + 1.4, 'breathe', 1.0, pan(ST(1.4, A, V, K).xA));
      SND.say(ac, out, V, t0 + 2.2, 'breathe', 0.8, pan(ST(2.2, A, V, K).xV));
      // contact: they touch and the rose sounds as a chord of their ratio (unison + both original tones + octave)
      const Sc = ST(TC, A, V, K), pc = pan((Sc.xA + Sc.xV) / 2);
      SND.say(ac, out, V, t0 + TC, 'land', 0.5, pc);
      SND.pluck(ac, out, t0 + TC, mid(fA), 0.32, 1.6, pc);
      SND.pluck(ac, out, t0 + TC + 0.03, mid(fV0), 0.22, 1.4, pc);
      SND.pluck(ac, out, t0 + TC + 0.06, mid(fA) + 12, 0.16, 1.8, pc);
      SND.cloud(ac, out, t0 + TC, 2.2, 45, { pitches: [mid(fA), mid(fA) + 12, mid(fA) + 19], a: 0.03, d: [0.08, 0.25], spread: 0.3 }, u => Math.pow(1 - u, 2));
      SND.say(ac, out, A, t0 + 4.4, 'breathe', 1.2, pc);
    }
  });
})();
