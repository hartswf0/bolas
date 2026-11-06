// 09 · SEDUCTION — consequence beat · SCION-23 Spine, Skeletal Motion Runtime
// Every sack is a skeleton (root -> hip -> chest -> earL/earR) with its cloth as a weighted mesh attachment
// skinned to hip and chest. Its idle cycle is an animation clip on its own clock. After the seduction the
// AnimationState of each sack carries TWO tracks: track 0 its own idle, track 1 the partner's idle on the
// partner's clock, mixed in with alpha = the desire the ledger gives it (st.mind[s][o].desire). Crossfades
// are alpha ramps. A calculating doer crossfades the victim's track out; the victim keeps the doer's.
// The partner's track is drawn as a coloured thread along the bones: you carry the other's rhythm in you.
// The flower is an attachment that changes slot: from the doer's slot to the victim's (kept), or wilts.
// Invariant (numerical): every vertex weight pair sums to 1; every track alpha is in [0,1]; pose(t) is pure.
(function () {
  const TAU = Math.PI * 2, G = 850, DUR = 3.2;
  const IDLE = {                       // clip parameters: the sack's own rhythm (Hz), sway, breath, ear swing
    R: { f: 0.5, hip: 0.07, ch: -0.03, br: 0.012, ear: 0.10, rock: 1, acc: '#c86a5e', cloth: '#cdb48a', n: 4 },
    B: { f: 0.375, hip: 0.025, ch: 0.02, br: 0.04, ear: 0.06, rock: 0, acc: '#e0ac48', cloth: '#e3cfa6', n: 3 },
    I: { f: 0.75, hip: 0.09, ch: 0.13, br: 0.02, ear: 0.35, rock: 0, acc: '#93b6dc', cloth: '#d9c59c', n: 6 },
    O: { f: 1.0, hip: 0.03, ch: 0.025, br: 0.008, ear: 0.05, rock: 0, acc: '#b872d8', cloth: '#efe2c4', n: 8 }
  };
  const JEAL = { R: 0.5, B: 0.25, I: 0.12, O: 0.7 };   // how readily each sack turns noticing into jealousy
  const has = (st, id, tag) => !!(st && st.body && st.body[id] && st.body[id].indexOf(tag) >= 0);
  const cl = (a, b, x) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  const sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u); };
  const eo = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return 1 - Math.pow(1 - u, 3); };

  // ---------- animation clips: pose = {x, y, sx, sy, hip, chest, earL, earR}; all relative, mixed by alpha
  function clipIdle(id, time, lev) {
    const c = IDLE[id], w = TAU * c.f * time, wt = 1 + 0.6 * (lev ? lev.weight : 0);
    return { hip: c.hip * Math.sin(w), chest: c.ch * Math.sin(w - 0.9), sy: 1 + c.br * wt * Math.sin(2 * w), sx: 1 - 0.5 * c.br * Math.sin(2 * w),
      earL: c.ear * Math.sin(w + 0.6), earR: -c.ear * Math.sin(w + 0.3), x: c.rock ? 9 * Math.sin(w) : 0, y: 0 };
  }
  function clipWalk(id, time) {      // heavy hops for B, shuffles for the small ones
    const f = { R: 1.6, B: 1.1, I: 1.4, O: 2.0 }[id], w = TAU * f * time, hop = { R: 6, B: 10, I: 4, O: 8 }[id];
    return { hip: 0.08 * Math.sin(w), chest: -0.05 * Math.sin(w), sy: 1 - 0.04 * Math.abs(Math.sin(w)), sx: 1, earL: 0.2 * Math.sin(w), earR: 0.2 * Math.sin(w + 1), x: 0, y: hop * Math.abs(Math.sin(w)) };
  }
  function clipWatch(id, time, dir) { // stiffened, leaning toward what it sees, ears pressed flat
    return { hip: 0.12 * dir, chest: 0.06 * dir + 0.008 * Math.sin(TAU * 7 * time), sy: 1.03, sx: 0.97, earL: -0.5, earR: 0.5, x: 0, y: 0 };
  }
  function clipDead() { return { hip: 0.22, chest: 0.18, sy: 0.84, sx: 1.08, earL: -0.8, earR: 0.8, x: 0, y: 0 }; }
  const ZERO = { hip: 0, chest: 0, sy: 1, sx: 1, earL: 0, earR: 0, x: 0, y: 0 };
  // AnimationState.apply: tracks in order, each lerps the current pose toward its clip by alpha
  function apply(tracks) {
    const p = Object.assign({}, ZERO);
    for (const tr of tracks) { const a = cl(0, 1, tr.alpha); if (a <= 0) continue; for (const k in p) p[k] = lerp(p[k], tr.pose[k], a); }
    return p;
  }

  // ---------- the ledger reading: which branch this film is in
  function plan(ev, st) {
    const A = ev.A, V = ev.V, mAV = st.mind[A][V], mVA = st.mind[V][A];
    const calc = mAV.pride * 1.6 + mAV.grudge + 0.5 * mAV.debt + 0.3 * mAV.fear, des = mAV.desire;
    const deadV = !st.alive[V], deadA = !st.alive[A];
    let T = null, best = -1;
    for (const o of ['R', 'B', 'I', 'O']) {
      if (o === A || o === V || !st.alive[o]) continue;
      const mo = st.mind[o], s = JEAL[o] + 0.6 * (mo[A].grudge + mo[V].grudge) + 0.4 * (mo[A].fear + mo[V].fear) + 0.8 * (mo[A].desire + mo[V].desire);
      if (s > best) { best = s; T = o; }
    }
    return { A, V, calculating: !deadV && !deadA && calc > des, deadV, deadA, calc, des,
      mixV: deadV ? 0 : cl(0, 0.85, mVA.desire), mixA: deadV ? 0.35 : cl(0, 0.7, des), T, jealous: !!T && !deadV && !deadA && best > 0.45, finds: !!T && deadV, jscore: best,
      guilt: st.mind[A][V].guilt, lev: st.levers };
  }

  // ---------- skeleton: dimensions from cast + carried damage + levers
  function dims(id, st, K) {
    const k = K.CAST[id], L = st.levers[id] || {};
    const sc = 1 + 0.12 * cl(-1, 1, L.loom || 0) - 0.18 * cl(0, 1, L.shrink || 0);
    const em = has(st, id, 'emptied') ? 0.8 : 1;
    return { w: k.w * sc * (em < 1 ? 1.05 : 1), h: k.h * sc * em, sc };
  }
  // world transform of the bones; mesh = superellipse contour with hip/chest weights (linear blend skinning)
  const SQ = { R: 4.2, B: 2.7, I: 3.4, O: 7 };
  function skin(id, dm, pose, rootX) {
    const { w, h } = dm, H2 = h * 0.5, p = SQ[id];
    const ch = Math.cos(pose.hip), sh = Math.sin(pose.hip), a2 = pose.hip + pose.chest, cc = Math.cos(a2), sc2 = Math.sin(a2);
    const hipTip = [sh * H2, ch * H2];         // local, y up; rotation positive leans toward +x (right)
    const M = (x, y) => {
      const wc = sm(0.2, 0.8, y / h), wh = 1 - wc;            // weights sum to 1
      const hx = x * ch + y * sh, hy = -x * sh + y * ch;       // hip bone (rotate about root)
      const ly = y - H2, cx = hipTip[0] + x * cc + ly * sc2, cy = hipTip[1] - x * sc2 + ly * cc;  // chest bone
      // NB: rotation sign — positive hip rotates top toward +x
      const X = wh * hx + wc * cx, Y = wh * hy + wc * cy;
      return [rootX + pose.x + X * pose.sx, G - pose.y - Y * pose.sy];
    };
    // mesh vertices (cloth)
    const pts = [], N = 88;
    for (let i = 0; i < N; i++) {
      const al = i / N * TAU, cs = Math.cos(al), sn = Math.sin(al);
      const x = w / 2 * Math.sign(cs) * Math.pow(Math.abs(cs), 2 / p);
      const yl = Math.sign(sn) * Math.pow(Math.abs(sn), 2 / p);
      let y = h / 2 + h / 2 * yl;
      if (id === 'I' && yl > 0) y -= 0.2 * h * (1 - Math.pow(2 * x / w, 2)) * Math.pow(yl, 3);
      pts.push(M(x, y));
    }
    // bones as world segments: root, hip tip, chest tip, ear tips (ears hang from chest top corners)
    const root = M(0, 0), hipT = M(0, H2), top = M(0, h);
    const earBase = (sd) => M(sd * w * 0.42, h * (id === 'I' ? 0.8 : 0.98));
    return { id, w, h, M, pts, root, hipT, top, earBase, pose };
  }

  // ---------- drawing
  function path(g, pts) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath(); }
  function dotsAlong(g, pts, step, r, col, closed) {
    g.fillStyle = col; let acc = 0; const n = pts.length, L = closed ? n : n - 1;
    for (let i = 0; i < L; i++) { const p = pts[i], q = pts[(i + 1) % n], dx = q[0] - p[0], dy = q[1] - p[1], d = Math.hypot(dx, dy) || 1e-6;
      while (acc < d) { const f = acc / d; g.beginPath(); g.arc(p[0] + dx * f, p[1] + dy * f, r, 0, TAU); g.fill(); acc += step; } acc -= d; }
  }
  function dot(g, p, r, col) { g.fillStyle = col; g.beginPath(); g.arc(p[0], p[1], r, 0, TAU); g.fill(); }
  function mixHex(a, b, u) { const A = parseInt(a.slice(1), 16), B = parseInt(b.slice(1), 16); const c = (s) => Math.round(lerp((A >> s) & 255, (B >> s) & 255, u));
    return 'rgb(' + c(16) + ',' + c(8) + ',' + c(0) + ')'; }
  function band(g, S, y0, y1, col) {
    const P = []; for (let i = 0; i <= 12; i++) P.push(S.M(-S.w + 2 * S.w * i / 12, y0)); for (let i = 12; i >= 0; i--) P.push(S.M(-S.w + 2 * S.w * i / 12, y1));
    g.save(); path(g, S.pts); g.clip(); g.fillStyle = col; path(g, P); g.fill(); g.restore();
  }
  function earChain(S, sd, rot, len, droop) {   // ear bone chain (IK-free FK chain hanging from the corner)
    const P = [S.earBase(sd)]; let a = droop ? Math.PI / 2 - 0.15 : -0.6;
    for (let j = 1; j <= 10; j++) { a += rot * 0.08; const q = P[j - 1]; P.push([q[0] + sd * Math.cos(a) * len / 10 * (droop ? 0.25 : 1), q[1] + Math.sin(a) * len / 10 * (droop ? 1 : -0.4)]); }
    return P;
  }
  // the sack: mesh + slots (ears behind, cloth, shawl/belt/stencil, damage, outline, wig in front)
  function drawSack(g, S, st, o) {
    const id = S.id, lev = st.levers[id] || {}, greyAmt = cl(0, 1, (lev.grey || 0) + (has(st, id, 'greyed') ? 0.6 : 0) + (o.grey || 0));
    const cloth = mixHex(IDLE[id].cloth, '#8f8b84', greyAmt), dark = mixHex('#6d5c44', '#45433f', greyAmt);
    g.save(); g.globalAlpha = o.alpha == null ? 1 : o.alpha;
    // shadow on floor; wall shadow from the lamp grows with the SHADOW lever
    const sh = cl(0, 1.5, (lev.shadow || 0)) + (o.shadowX || 0);
    g.fillStyle = 'rgba(0,0,0,0.45)'; g.beginPath(); g.ellipse(S.root[0], G + 4, S.w * 0.62, 10, 0, 0, TAU); g.fill();
    if (sh > 0.05) {      // soft wall shadow thrown up and away from the lamp
      const dx = (S.root[0] - 960) * (0.12 + 0.25 * sh), k = 1 + 0.35 * sh;
      g.save(); g.globalAlpha *= cl(0, 0.5, 0.15 + 0.22 * sh); g.fillStyle = '#020205'; g.filter = 'blur(9px)';
      g.translate(S.root[0] + dx, G - 6); g.scale(k, k); g.translate(-S.root[0], -G);
      path(g, S.pts); g.fill(); g.restore();
    }
    // HALO lever: the lamp finds it
    const halo = cl(0, 1, lev.halo || 0) * (o.haloMul == null ? 1 : o.haloMul);
    if (halo > 0.05) { const c = S.M(0, S.h * 0.6), r = S.h * 1.1; const gr = g.createRadialGradient(c[0], c[1], 5, c[0], c[1], r);
      gr.addColorStop(0, 'rgba(255,232,180,' + (0.32 * halo) + ')'); gr.addColorStop(1, 'rgba(255,232,180,0)'); g.fillStyle = gr; g.fillRect(c[0] - r, c[1] - r, 2 * r, 2 * r); }
    const drowsy = has(st, id, 'drowsy'), shrink = cl(0, 1, lev.shrink || 0);
    const P = S.pose, earDown = (drowsy ? 0.5 : 0) + shrink * 0.6;
    // ears: I's hang down like hair; the others are corners raised by the ear bones
    if (id === 'I') for (const sd of [-1, 1]) {
      const E = earChain(S, sd, (sd < 0 ? P.earL : P.earR) * 3, S.h * 0.9, true);
      g.strokeStyle = cloth; g.lineWidth = 15; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath(); E.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke();
      g.strokeStyle = 'rgba(60,45,30,0.35)'; g.lineWidth = 2; g.stroke(); dotsAlong(g, E, 7, 1.6, 'rgba(251,247,238,0.75)', false);
    }
    const lit = g.createLinearGradient(S.root[0] - S.w, G - S.h, S.root[0] + S.w, G); lit.addColorStop(0, cloth); lit.addColorStop(1, dark);
    path(g, S.pts); g.fillStyle = lit; g.fill();
    if (id !== 'I' && id !== 'O') for (const sd of [-1, 1]) {   // ear corners
      const b = S.earBase(sd), r = (sd < 0 ? P.earL : P.earR) * sd - earDown, L = id === 'B' ? 22 : 16;
      const tip = [b[0] + sd * (6 + 4 * r), b[1] - L * (1 + r) * 0.8];
      g.fillStyle = cloth; g.beginPath(); g.moveTo(b[0] - sd * 18, b[1] + 4); g.quadraticCurveTo(tip[0] - sd * 6, tip[1], tip[0], tip[1]); g.lineTo(b[0] + sd * 6, b[1] + 8); g.closePath(); g.fill();
      dotsAlong(g, [[b[0] - sd * 18, b[1] + 2], tip, [b[0] + sd * 6, b[1] + 8]], 7, 1.7, 'rgba(251,247,238,0.85)', false);
    }
    if (id === 'R') { band(g, S, S.h * 0.8, S.h * 1.4, mixHex('#6e3a33', '#55504a', greyAmt)); const B = []; for (let i = 0; i <= 16; i++) B.push(S.M(-S.w / 2 + S.w * i / 16, S.h * 0.8 - 3)); dotsAlong(g, B, 9, 2.2, '#a8574c', false); }
    if (id === 'B') {
      band(g, S, S.h * 0.37, S.h * 0.44, '#2a2622');
      const cy = S.h * 0.68, R0 = S.w * 0.15, ring = []; for (let i = 0; i < 40; i++) ring.push(S.M(R0 * Math.cos(i / 40 * TAU), cy + R0 * Math.sin(i / 40 * TAU)));
      dotsAlong(g, ring, 7, 2.4, '#7a5a30', true);
      for (let j = 0; j < 6; j++) { const p0 = S.M(0, cy - R0 * 0.7 + j * R0 * 0.26); dot(g, p0, 2.6, '#7a5a30'); }
    }
    damage(g, S, st);
    // the bone threads: own rhythm in dark stitch; the partner's track in the partner's colour, alpha = mix
    const bonesPts = [S.root, S.hipT, S.top];
    g.save(); path(g, S.pts); g.clip();
    g.strokeStyle = 'rgba(70,52,34,0.35)'; g.lineWidth = 2; g.setLineDash([5, 6]); g.beginPath(); bonesPts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); g.setLineDash([]);
    if (o.thread && o.thread.a > 0.02) {
      g.globalAlpha *= cl(0, 1, o.thread.a * 1.2);
      for (const off of [-S.w * 0.18, 0, S.w * 0.18]) {
        const Q = []; for (let i = 0; i <= 14; i++) { const v = i / 14; Q.push(S.M(off * (1 - v * 0.4) + 6 * Math.sin(v * 9 + o.thread.ph), v * S.h * 0.96)); }
        g.strokeStyle = o.thread.col; g.lineWidth = off ? 2.5 : 4; g.beginPath(); Q.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke();
        dotsAlong(g, Q, 11, off ? 2 : 3, o.thread.col, false);
      }
    }
    g.restore();
    dotsAlong(g, S.pts, 7, 1.9, 'rgba(251,247,238,' + (0.9 - 0.4 * greyAmt) + ')', true);
    if (id === 'O') {        // wig slot, in front
      const off = has(st, 'O', 'wig'), cap = [];
      for (let i = 0; i <= 20; i++) { const a = Math.PI * i / 20; cap.push(S.M(-Math.cos(a) * (S.w / 2 + 6), S.h * 0.74 + Math.sin(a) * (S.h * 0.26 + 14))); }
      g.save(); if (off) { const p = S.top; g.translate(p[0], p[1]); g.rotate(0.38); g.translate(-p[0] + 10, -p[1] + 6); }
      const wig = mixHex('#7a3b8f', '#5a5560', greyAmt); g.fillStyle = wig; path(g, cap); g.fill();
      g.strokeStyle = wig; g.lineCap = 'round'; g.lineWidth = 7;
      for (const sd of [-1, 1]) for (let q = 0; q < 4; q++) { const anc = S.M(sd * (S.w / 2 + 2 - q * 6), S.h * (0.9 - q * 0.04)); g.beginPath(); g.moveTo(anc[0], anc[1]); let X = anc[0], Y = anc[1];
        for (let j = 1; j <= 10; j++) { X += sd * 1.2 + 2.4 * Math.sin(P.hip * 20 - j * 0.5 - q * 0.4) - P.hip * 8; Y += S.h * 0.05; g.lineTo(X, Y); } g.stroke(); }
      dotsAlong(g, cap, 8, 1.8, '#c79ad8', false); g.restore();
    }
    g.restore();
  }
  function damage(g, S, st) {
    const id = S.id, w = S.w, h = S.h, M = S.M;
    const row = (y, x0, x1, n) => { const P = []; for (let i = 0; i <= n; i++) P.push(M(lerp(x0, x1, i / n), y)); return P; };
    if (has(st, id, 'rope')) for (const yy of [0.3, 0.62]) { const P = row(h * yy, -w / 2, w / 2, 14); g.save(); path(g, S.pts); g.clip(); g.strokeStyle = '#8a6a3e'; g.lineWidth = 5; g.beginPath(); P.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); g.restore(); dotsAlong(g, P, 6, 1.6, '#c9a46a', false); }
    if (has(st, id, 'gag')) band(g, S, h * 0.7, h * 0.78, '#4a4038');
    if (has(st, id, 'blot')) for (let i = 0; i < 18; i++) { const a = i * 2.39996, r = 3 + Math.sqrt(i) * 5; dot(g, M(-w * 0.15 + r * Math.cos(a), h * 0.5 + r * Math.sin(a)), 3.2, '#16182a'); }
    if (has(st, id, 'tag')) { const p = M(w * 0.22, h * 0.72); g.fillStyle = '#f4efe2'; g.fillRect(p[0] - 11, p[1] - 7, 22, 15); dot(g, p, 2.4, '#b23a2e'); }
    if (has(st, id, 'torn')) { const P = []; for (let i = 0; i <= 8; i++) P.push(M(w * 0.36 + (i % 2 ? 6 : -6), h * (0.25 + i * 0.06))); g.strokeStyle = '#3b3026'; g.lineWidth = 2.5; g.beginPath(); P.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); }
    if (has(st, id, 'coins')) for (let i = 0; i < 3; i++) dot(g, M(-w * 0.2 + i * 9, 6 + (i % 2) * 5), 5, '#d8b247');
    if (has(st, id, 'cinched')) dotsAlong(g, row(h * 0.8, -w * 0.42, w * 0.42, 8), 5, 1.8, '#8a6a3e', false);
  }

  // the rose attachment: r = cos(k a), k from the pair's harmonic ratio (continuity with the deed shot)
  function rose(g, c, cA, cV, R, wilt, rot, K, t) {
    let n = Math.max(cA.n, cV.n), d = Math.min(cA.n, cV.n); const gcd = (a, b) => b ? gcd(b, a % b) : a; const q = gcd(n, d); n /= q; d /= q;
    const k = n / d, span = ((n * d) % 2 ? Math.PI : TAU) * d, P = 220 * d;
    if (wilt < 0.3) { g.fillStyle = 'rgba(255,230,200,' + (0.12 * (1 - wilt)) + ')'; g.beginPath(); g.arc(c[0], c[1], R * 1.15, 0, TAU); g.fill(); }
    for (let i = 0; i < P; i++) {
      const a = i / P * span, r = R * Math.cos(k * a) * (1 - 0.45 * wilt);
      let x = c[0] + r * Math.cos(a + rot), y = c[1] + r * Math.sin(a + rot) * (1 - 0.4 * wilt) + wilt * Math.abs(r) * 0.5;
      const fall = K.hash(i * 3.7 + 11);            // wilting petals fall to the floor, each at its own time
      const ft = fall < 0.6 ? cl(0, 1, (wilt - fall) * 3) : 0;
      if (ft > 0) { y = lerp(y, G - 2 - 3 * K.hash(i), ft * ft); x += (K.hash(i * 1.3) - 0.5) * 60 * ft; }
      const col = (Math.floor(i / 7) % 2) ? cA.acc : cV.acc;
      g.fillStyle = wilt > 0.05 ? mixHex(col, '#6b5a44', cl(0, 1, wilt * 1.2)) : col; g.globalAlpha = 0.9;
      g.beginPath(); g.arc(x, y, 1.9, 0, TAU); g.fill();
    }
    g.globalAlpha = 1; dot(g, c, 3 + 3 * (1 - wilt), wilt > 0.5 ? '#9a8a6a' : '#fff3d6');
  }

  // ---------- the room: wall, floor, the lamp (as in the deed shot), and the door on the right
  function room(g, t, Pn, K) {
    const W = K.W, H = K.H;
    const wall = g.createLinearGradient(0, 0, 0, G); wall.addColorStop(0, '#07080f'); wall.addColorStop(1, '#171a28'); g.fillStyle = wall; g.fillRect(0, 0, W, G);
    const fl = g.createLinearGradient(0, G, 0, H); fl.addColorStop(0, '#221d16'); fl.addColorStop(1, '#0b0a08'); g.fillStyle = fl; g.fillRect(0, G, W, H - G);
    const lampOn = Pn.deadV ? 1 - 0.45 * sm(1.8, 2.6, t) : 1;
    const pool = g.createRadialGradient(960, G, 20, 960, G, 700); pool.addColorStop(0, 'rgba(255,214,150,' + 0.22 * lampOn + ')'); pool.addColorStop(1, 'rgba(255,214,150,0)'); g.fillStyle = pool; g.fillRect(0, 0, W, H);
    const glow = g.createRadialGradient(960, 190, 10, 960, 190, 900); glow.addColorStop(0, 'rgba(255,220,160,' + 0.28 * lampOn + ')'); glow.addColorStop(1, 'rgba(255,220,160,0)'); g.fillStyle = glow; g.fillRect(0, 0, W, H);
    g.fillStyle = 'rgba(251,247,238,0.18)'; for (let x = 6; x < W; x += 14) { g.beginPath(); g.arc(x, G, 1.4, 0, TAU); g.fill(); }
    g.strokeStyle = '#2a2a30'; g.lineWidth = 3; g.beginPath(); g.moveTo(960, 0); g.lineTo(960, 160); g.stroke();
    g.fillStyle = '#fff3d6'; g.globalAlpha = lampOn; g.beginPath(); g.arc(960, 196, 14, 0, TAU); g.fill(); g.globalAlpha = 1;
    g.fillStyle = '#3a2f28'; g.beginPath(); g.moveTo(915, 190); g.lineTo(1005, 190); g.lineTo(980, 150); g.lineTo(940, 150); g.closePath(); g.fill();
    // door at the right: closed frame, opens when a third is there
    const dx0 = 1560, dx1 = 1760, dy = 470;
    g.fillStyle = '#0d0e15'; g.fillRect(dx0 - 14, dy - 14, dx1 - dx0 + 28, G - dy + 14);
    const open = Pn.T ? Pn.doorOpen(t) : 0;
    if (open > 0.01) {
      const lg = g.createLinearGradient(dx0, 0, dx1, 0); lg.addColorStop(0, 'rgba(255,196,120,0.55)'); lg.addColorStop(1, 'rgba(255,170,90,0.35)');
      g.fillStyle = lg; g.fillRect(dx0, dy, (dx1 - dx0) * open, G - dy);
      // spill of door light across the floor toward the couple
      g.fillStyle = 'rgba(255,190,110,' + 0.16 * open + ')'; g.beginPath(); g.moveTo(dx0, G); g.lineTo(dx0 + (dx1 - dx0) * open, G); g.lineTo(dx0 - 260 * open, H); g.lineTo(dx0 - 700 * open, H); g.closePath(); g.fill();
    }
    // door leaf (hinged on the right; swings in)
    g.fillStyle = '#2a2118'; const lw = (dx1 - dx0) * (1 - open); g.fillRect(dx1 - lw, dy, lw, G - dy);
    if (lw > 20) { g.fillStyle = '#b08a4a'; g.beginPath(); g.arc(dx1 - lw + 18, 690, 5, 0, TAU); g.fill(); }
    g.strokeStyle = 'rgba(251,247,238,0.15)'; g.lineWidth = 2; g.strokeRect(dx0, dy, dx1 - dx0, G - dy);
  }

  // ---------- the whole beat as a pure function of t: positions, tracks, poses
  function score(t, ev, st, K) {
    const Pn = plan(ev, st), { A, V, T } = Pn, lev = st.levers;
    const dA = dims(A, st, K), dV = dims(V, st, K);
    const tempo = (id) => 1 + 0.35 * cl(-1, 1, (lev[id] || {}).tempo || 0);
    const clk = (id) => t * tempo(id) + 0.4;
    const cx = 900 + (dA.w - dV.w) * 0.1;
    const lean = 0.18 + 0.1 * cl(-1, 1, (lev[A] || {}).loom || 0);
    // part slightly after the deed's lean, then (desire) lean back in; (calculating) turn and leave
    const part = sm(0.35, 1.1, t);
    let xA = cx - dA.w / 2 - 2 - 28 * part, xV = cx + dV.w / 2 + 2 + 24 * part;
    let leanA = lean * (1 - 0.6 * part), leanV = -lean * (1 - 0.6 * part);
    let sxA = 1, walkA = 0, ghostA = 0, alphaA = 1;
    let mixA = Pn.mixA * (1 - (Pn.calculating ? sm(1.5, 2.2, t) : 0));
    if (Pn.deadV) mixA *= 1 - sm(0.9, 1.6, t);
    let mixV = Pn.mixV;
    const back = !Pn.calculating && !Pn.deadV ? sm(1.9, 2.7, t) : 0;
    leanA += back * lean * 0.8; leanV -= back * lean * 0.8; xA += back * 24; xV -= back * 20;
    let leaveA = 0;
    if (Pn.calculating || (Pn.deadV && Pn.guilt < 0.9 && A !== 'B')) {
      const tt = Pn.deadV ? 1.7 : 1.9;
      const f = sm(tt, tt + 0.35, t); sxA = Math.cos(Math.PI * f) >= 0 ? Math.max(0.08, Math.cos(Math.PI * f)) : -Math.max(0.08, -Math.cos(Math.PI * f));
      leaveA = eo(tt + 0.3, DUR - 0.1, t); walkA = sm(tt + 0.25, tt + 0.5, t) * (1 - sm(DUR - 0.5, DUR - 0.2, t));
      xA -= leaveA * (A === 'B' ? 360 : 430); leanA *= 1 - f;
    }
    if (Pn.deadA) { ghostA = 1; alphaA = 0.55 - 0.35 * sm(0.6, DUR - 0.3, t); }
    // the corpse victim: no idle clip on its tracks; the doer's ear bends to it (guilt) or it leaves
    const tracksA = [
      { pose: clipIdle(A, clk(A), lev[A]), alpha: Pn.deadA ? 0.4 : 1 },
      { pose: clipIdle(V, clk(V), lev[V]), alpha: mixA },
      { pose: clipWalk(A, t), alpha: walkA }
    ];
    const tracksV = Pn.deadV ? [{ pose: clipDead(), alpha: 1 }] : [
      { pose: clipIdle(V, clk(V), lev[V]), alpha: 1 },
      { pose: clipIdle(A, clk(A), lev[A]), alpha: mixV }
    ];
    const pA = apply(tracksA), pV = apply(tracksV);
    pA.hip += leanA; pV.hip += Pn.deadV ? 0 : leanV;
    if (Pn.deadV && A === 'B' || (Pn.deadV && Pn.guilt >= 0.9)) { const bow = sm(1.4, 2.4, t); pA.chest += 0.25 * bow; pA.hip += 0.08 * bow; pA.earL -= 0.6 * bow; pA.earR += 0.6 * bow; }
    pA.sx *= sxA;
    // a jealous third makes the couple's ears go up (they notice being watched)
    const seen = T && !Pn.deadV ? sm(1.5, 2.0, t) : 0;
    pA.earL += 0.4 * seen; pA.earR -= 0.4 * seen; if (!Pn.deadV) { pV.earL += 0.4 * seen; pV.earR -= 0.4 * seen; }
    const SA = skin(A, dA, pA, xA), SV = skin(V, dV, pV, xV);
    // onion skins: each body posed by the partner's clip alone (track 1 soloed), drawn where the mix pulls it
    const solo = (id, other, pBase, x, dm) => { const q = Object.assign({}, pBase), c = clipIdle(other, clk(other), lev[other]); for (const k of ['hip', 'chest', 'earL', 'earR']) q[k] = pBase[k] + (c[k] - pBase[k]) * 1.6; q.sy = pBase.sy + (c.sy - pBase.sy) * 2; return skin(id, dm, q, x); };
    const EA = mixA > 0.04 ? solo(A, V, pA, xA, dA) : null, EV = Pn.mixV > 0.04 ? solo(V, A, pV, xV, dV) : null;
    // the third: in the doorway, crossfades idle -> watch, then looms in (jealous) or turns away (door closes)
    let ST3 = null, t3 = null;
    if (T) {
      const dT = dims(T, st, K), arrive = sm(0.8, 1.4, t);
      // four ways a third takes it: jealous (looms in), finds the body (crosses to it, ears up), spooked by a ghost or indifferent (turns, door shuts)
      const watch = sm(1.3, 1.8, t), jl = Pn.jealous ? sm(1.9, 2.8, t) : 0, fd = Pn.finds ? eo(1.8, 2.9, t) : 0;
      const away = Pn.jealous || Pn.finds ? 0 : sm(2.1, 2.5, t);
      let xT = 1660 + 120 * (1 - arrive) - (Pn.jealous ? 260 * eo(1.9, 2.9, t) : 0) + (away ? 40 * sm(2.4, 2.9, t) : 0);
      if (Pn.finds) xT = lerp(xT, SV.root[0] + SV.w / 2 + dT.w / 2 + 70, fd);
      const tr = [{ pose: clipIdle(T, clk(T), lev[T]), alpha: 1 - 0.5 * fd }, { pose: clipWatch(T, t, -1), alpha: watch * (1 - away) },
        { pose: clipWalk(T, t), alpha: Pn.jealous ? sm(1.9, 2.1, t) * (1 - sm(2.7, 2.9, t)) : Pn.finds ? sm(1.8, 2.0, t) * (1 - sm(2.7, 2.95, t)) : away * (1 - sm(2.8, 3.0, t)) }];
      const pT = apply(tr); if (Pn.finds) { const al = sm(2.6, 2.9, t); pT.earL += 0.9 * al; pT.earR -= 0.9 * al; pT.hip -= 0.1 * al; pT.sy *= 1 + 0.06 * al; } pT.sx *= away ? (Math.cos(Math.PI * away) >= 0 ? Math.max(0.08, Math.cos(Math.PI * away)) : -Math.max(0.08, -Math.cos(Math.PI * away))) : 1;
      ST3 = skin(T, dT, pT, xT); t3 = { arrive, jl, away, fd, alpha: arrive * (1 - sm(2.7, 3.05, t) * (away > 0 ? 1 : 0)) };
    }
    Pn.doorOpen = (tt) => T ? sm(0.6, 1.1, tt) * (1 - (Pn.jealous || Pn.finds ? 0 : sm(2.75, 3.1, tt))) : 0;
    return { Pn, SA, SV, EA, EV, ST3, t3, mixA, mixV, alphaA, ghostA, clk, leaveA };
  }

  // flower: where it is, attached to whose slot, how wilted
  function flower(t, ev, st, Sc, K) {
    const { Pn, SA, SV } = Sc, V = ev.V;
    const mid = [(SA.top[0] + SV.top[0]) / 2 + 4, Math.min(SA.top[1], SV.top[1]) - 98];
    let target, wilt = 0, keep = 1, R = 66;
    if (Pn.deadV) { target = SV.M(0, SV.h + 6); wilt = sm(1.6, 3.0, t); R = 50; }
    else if (Pn.deadA) { target = SV.M(SV.w * 0.1, SV.h + 70); }
    else {
      const slot = { R: SV.M(SV.w * 0.18, SV.h * 0.88), B: SV.M(SV.w * 0.42, SV.h + 52), I: [SV.root[0] - SV.w * 0.6, G - 30], O: SV.M(SV.w * 0.5 + 8, SV.h * 0.82) }[V];
      target = slot; R = { R: 44, B: 50, I: 44, O: 40 }[V];
      if (Pn.calculating) wilt = sm(2.2, 3.15, t);
    }
    const u = eo(0.7, 1.6, t);
    const c = [lerp(mid[0], target[0], u), lerp(mid[1], target[1], u)];
    return { c, R: lerp(66, R, u), wilt, u, stemFrom: Pn.deadA ? null : null };
  }

  CONSEQ({
    deed: 'seduction', n: 9, scion: 23, lineage: 'Spine — Skeletal Motion Runtime (Esoteric Software 2D skeletal animation, mesh skinning, runtime mixing)',
    op: 'Each sack\'s idle cycle is a clip on its own clock; after the seduction each skeleton plays two tracks, its own idle and the partner\'s, mixed by the desire the ledger gives it — a calculating doer crossfades the partner\'s track out and walks off while the victim keeps swaying to the doer\'s rhythm.',
    made: 'Each sack is a five-bone skeleton (root, hip, chest, two ears) with its cloth as a superellipse mesh linearly skinned to hip and chest, drawn in the deed shot\'s cotton-and-stitched-dots idiom; the partner\'s mixed-in track is drawn as a thread of the partner\'s colour running along the bones inside the cloth. The rose from the deed is an attachment that moves from the doer\'s slot to the victim\'s (shawl, ear, wig, or dropped at the feet), or wilts and sheds; the room is the same lamp-lit wall, with a door on the right where a third can appear.',
    moved: 'AnimationState mixing: per-bone lerp of idle, partner-idle, walk, watch and dead clips by track alphas that are crossfaded over time and read from the ledger (desire, pride, grudge, guilt, alive) and the myth levers (tempo scales the clock, weight the breath, loom/shrink the size, shadow the wall shadow, halo the light, grey the cloth). A facing flip (root scaleX through zero) turns the calculating doer away; a third crossfades from idle to a stiff watching lean, then either looms in on a walk track or turns and the door closes.',
    dur: DUR,
    beat(g, t, ev, st, K, X) {
      const Sc = score(t, ev, st, K), { Pn, SA, SV, ST3, t3 } = Sc, A = ev.A, V = ev.V;
      room(g, t, Pn, K);
      // the third, behind the couple (slot order: door, third, victim, doer, flower)
      if (ST3) {
        if (t3.jl > 0.02) {   // jealousy: lit from the door behind it, its shadow stretches left across the wall onto the couple
          const x1 = ST3.root[0] + ST3.w / 2;
          g.save(); g.globalAlpha = 0.42 * t3.jl; g.fillStyle = '#000'; g.filter = 'blur(6px)';
          g.translate(x1, G); g.transform(1 + 3.2 * t3.jl, 0, 0.35 * t3.jl, 1 + 0.9 * t3.jl, 0, 0); g.translate(-x1, -G);
          path(g, ST3.pts); g.fill(); g.restore();
        }
        drawSack(g, ST3, st, { alpha: t3.alpha, shadowX: 0, haloMul: 0.3,
          thread: null });
      }
      const fl = flower(t, ev, st, Sc, K);
      if (Sc.EV) { g.globalAlpha = 0.55 * Sc.mixV; dotsAlong(g, Sc.EV.pts, 9, 2.1, IDLE[A].acc, true); g.globalAlpha = 1; }
      if (Sc.EA) { g.globalAlpha = 0.55 * Sc.mixA * Sc.alphaA; dotsAlong(g, Sc.EA.pts, 9, 2.1, IDLE[V].acc, true); g.globalAlpha = 1; }
      drawSack(g, SV, st, { grey: Pn.deadV ? 0.8 : 0, thread: { a: Sc.mixV, col: IDLE[A].acc, ph: TAU * IDLE[A].f * Sc.clk(A) } });
      // the stem from the doer's slot to the bloom, until the flower changes slot
      if (!Pn.deadA && fl.u < 1) { const s0 = SA.M(SA.w * 0.3, SA.h * 0.95); g.strokeStyle = '#4f6b3c'; g.lineWidth = 3; g.globalAlpha = 1 - fl.u;
        g.beginPath(); g.moveTo(s0[0], s0[1]); g.quadraticCurveTo(s0[0] + 6, fl.c[1] + 10, fl.c[0], fl.c[1]); g.stroke(); g.globalAlpha = 1; }
      drawSack(g, SA, st, { alpha: Sc.alphaA, grey: Sc.ghostA * 0.9, haloMul: Pn.deadA ? 0 : 1,
        thread: { a: Sc.mixA, col: IDLE[V].acc, ph: TAU * IDLE[V].f * Sc.clk(V) } });
      // the flower's short stem in its new slot, then the rose
      if (fl.u > 0.5) { g.strokeStyle = mixHex('#4f6b3c', '#5a4a34', fl.wilt); g.lineWidth = 3; g.beginPath(); g.moveTo(fl.c[0], fl.c[1]); g.lineTo(fl.c[0] - 6, fl.c[1] + 26 + 10 * fl.wilt); g.stroke(); }
      rose(g, fl.c, IDLE[A], IDLE[V], fl.R, fl.wilt, 0.3 + 0.6 * fl.wilt, K, t);
      if (Pn.deadA) {  // the ghost doer: its outline lingers as dots only
        g.globalAlpha = 0.35 * Sc.alphaA; dotsAlong(g, SA.pts, 12, 2, '#cfd6e6', true); g.globalAlpha = 1;
      }
    },
    sound(ac, out, t0, ev, st, K) {
      const SND = K.SND, bus = ac.createGain(); bus.gain.value = 1.15; bus.connect(out); out = bus;
      const A = ev.A, V = ev.V, Pn = plan(ev, st);
      const pan = (x) => cl(-1, 1, x / 960 - 1);
      const mid = (f) => 69 + 12 * Math.log2(f / 440);
      const sc = (tt) => score(tt, ev, st, K);
      // each sack ticks at its own idle half-cycles in its own voice; the partner's track adds the partner's ticks
      // into this sack's position, at the mix weight: you hear one body carrying the other's beat.
      for (const [who, other, role] of [[A, V, 'A'], [V, A, 'V']]) {
        if (role === 'V' && Pn.deadV) continue;
        let prevOwn = null, prevOther = null;
        for (let i = 0; i <= DUR * 200; i++) {
          const tt = i / 200, S = sc(tt), Sk = role === 'A' ? S.SA : S.SV, mix = role === 'A' ? S.mixA : S.mixV;
          const qo = Math.floor(TAU * IDLE[who].f * S.clk(who) / Math.PI), qp = Math.floor(TAU * IDLE[other].f * S.clk(other) / Math.PI);
          const amp = role === 'A' && Pn.deadA ? 0.4 : 1;
          if (prevOwn !== null && qo !== prevOwn) { SND.say(ac, out, who, t0 + tt, 'tick', 0.5 * amp, pan(Sk.root[0])); SND.grain(ac, out, t0 + tt, { f: 110 * IDLE[who].n, d: 0.14, a: 0.05 * amp, pan: pan(Sk.root[0]), att: 0.08, type: 'triangle' }); }
          if (prevOther !== null && qp !== prevOther && mix > 0.05) SND.grain(ac, out, t0 + tt + 0.01, { f: 110 * IDLE[other].n, d: 0.14, a: 0.06 * mix * amp, pan: pan(Sk.root[0]), att: 0.08, type: 'triangle' });
          prevOwn = qo; prevOther = qp;
        }
      }
      const S0 = sc(0.1);
      SND.say(ac, out, A, t0 + 0.15, 'breathe', 0.9, pan(S0.SA.root[0]));
      if (!Pn.deadV) SND.say(ac, out, V, t0 + 0.35, 'breathe', 0.9, pan(S0.SV.root[0]));
      // the flower passes into the victim's slot: a pluck of the pair's chord
      const Sf = sc(1.6), pf = pan(Sf.SV.root[0]);
      if (!Pn.deadV) { SND.pluck(ac, out, t0 + 1.55, mid(110 * IDLE[A].n), 0.26, 1.4, pf); SND.pluck(ac, out, t0 + 1.6, mid(110 * IDLE[V].n), 0.2, 1.2, pf); }
      if (!Pn.deadV && !Pn.calculating) { SND.cloud(ac, out, t0 + 2.0, 1.1, 40, { pitches: [mid(110 * IDLE[A].n), mid(110 * IDLE[A].n) + 12], a: 0.03, d: [0.08, 0.2], spread: 0.25 }, u => Math.sin(Math.PI * u)); SND.say(ac, out, V, t0 + 2.3, 'land', 0.4, pf); }
      // calculating: the doer's track crossfades out (its tone glides away), footsteps leaving; the wilt is a falling cloud
      if (Pn.calculating || (Pn.deadV && A !== 'B' && Pn.guilt < 0.9)) {
        SND.grain(ac, out, t0 + 1.6, { f: 110 * IDLE[V].n, glide: -0.3, d: 0.6, a: 0.07, pan: pan(Sf.SA.root[0]), att: 0.2 });
        const t1 = Pn.deadV ? 2.0 : 2.2; const f = { R: 1.6, B: 1.1, I: 1.4, O: 2.0 }[A];
        for (let tt = t1; tt < DUR - 0.3; tt += 0.5 / f) SND.say(ac, out, A, t0 + tt, 'step', 0.8, pan(sc(tt).SA.root[0]));
      }
      if (Pn.calculating || Pn.deadV) { const tw = Pn.deadV ? 1.8 : 2.3; SND.cloud(ac, out, t0 + tw, 1.0, 35, { f: 110 * IDLE[A].n * 2, glide: -0.5, a: 0.03, d: [0.06, 0.16], spread: 0.3 }, u => 1 - u); }
      if (Pn.deadV) { SND.say(ac, out, A, t0 + 1.5, 'sink', 0.8, pan(Sf.SA.root[0])); SND.pluck(ac, out, t0 + 1.6, mid(110 * IDLE[A].n) - 12, 0.3, 1.6, pf); SND.say(ac, out, V, t0 + 1.62, 'land', 0.6, pf); }
      if (Pn.calculating) SND.pluck(ac, out, t0 + 2.25, mid(110 * IDLE[V].n) - 1, 0.22, 1.2, pf);
      if (Pn.deadA) SND.cloud(ac, out, t0 + 0.3, DUR - 0.5, 18, { bp: 3000, a: 0.02, d: [0.2, 0.4], spread: 0.3 }, u => 1 - u);
      // the third: the door, its steps, its cry if jealous
      if (Pn.T) {
        const S3 = sc(1.2), p3 = pan(1660);
        SND.grain(ac, out, t0 + 0.65, { bp: 400, q: 4, d: 0.5, a: 0.12, pan: p3, att: 0.6 });   // door hinge
        SND.say(ac, out, Pn.T, t0 + 0.9, 'step', 0.7, p3); SND.say(ac, out, Pn.T, t0 + 1.2, 'step', 0.7, p3);
        SND.say(ac, out, Pn.T, t0 + 1.55, 'react', Pn.jealous ? 0.9 : 0.4, p3);
        if (Pn.jealous) for (let k = 0; k < 4; k++) SND.say(ac, out, Pn.T, t0 + 2.0 + k * 0.22, 'step', 1, pan(1660 - 70 * k));
        else if (Pn.finds) { for (let k = 0; k < 4; k++) SND.say(ac, out, Pn.T, t0 + 1.95 + k * 0.22, 'step', 0.8, pan(1600 - 120 * k)); SND.say(ac, out, Pn.T, t0 + 2.75, 'react', 1, pan(1200)); }
        else { SND.say(ac, out, Pn.T, t0 + 2.4, 'step', 0.6, p3); SND.thump(ac, out, t0 + 3.0, 0.5, 70, p3); }  // the door shuts
        void S3;
      }
    },
    trace(g, box, age, K) {   // a pressed rose: the pair's curve, browning and losing dots with age
      const c = [box.x + box.w / 2, box.y + box.h / 2], R = Math.min(box.w, box.h) * 0.42, fade = cl(0, 1, age / 8);
      const k = 4 / 3, P = 260;
      for (let i = 0; i < P; i++) {
        if (K.hash(i * 5.1 + 2) < fade * 0.7) continue;
        const a = i / P * TAU * 3, r = R * Math.cos(k * a);
        g.fillStyle = mixHex(i % 14 < 7 ? '#c86a5e' : '#b872d8', '#6b5a44', fade); g.globalAlpha = 0.85 - 0.4 * fade;
        g.beginPath(); g.arc(c[0] + r * Math.cos(a), c[1] + r * Math.sin(a) * 0.8, Math.max(1, R * 0.05), 0, TAU); g.fill();
      }
      g.globalAlpha = 0.8; g.strokeStyle = '#4f6b3c'; g.lineWidth = Math.max(1, R * 0.06);
      g.beginPath(); g.moveTo(c[0], c[1]); g.lineTo(c[0] - R * 0.3, c[1] + R * 1.1); g.stroke(); g.globalAlpha = 1;
    }
  });
})();
