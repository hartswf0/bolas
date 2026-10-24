/* SCION through the dog. Each of the 54 SCION swarms shown as a lens on the same porch: the same machine, the same paper dog and
   person, the same loop of prompts, drawn or read the way that swarm's lineage would draw or read it. A lens is not the swarm's film;
   it is the swarm's first move, its native formal language made visible on a character everyone already knows.
   Needs paeleo/threshold/machine.js and stage.js. Scion.make(canvas) returns a runner: runner.draw(lensIndex, t). */
(function (root) {
  'use strict';
  const S = root.Stage, M = root.Threshold, C = S.C, W = 1280, H = 720, FPS = 24, LOOP = 32;
  const clamp = S.clamp, lerp = S.lerp, ease = S.ease;
  // the loop of prompts every lens watches: called, pressed, then the circumstances change and the dog comes to the sill; told to come in, it stays
  const TL = [[1.0, { voice: 'call' }], [2.3, { voice: 'none' }], [3.4, { voice: 'call', hand: 'reach' }], [4.6, { voice: 'none', hand: 'none' }],
    [5.4, { place: 'beside', posture: 'sit' }], [6.2, { door: 'open' }], [6.8, { hand: 'low' }], [7.4, { voice: 'soft' }], [9.4, { voice: 'none' }],
    [10.4, { voice: 'soft' }], [11.6, { voice: 'none' }], [26.4, { voice: 'soft' }], [27.4, { voice: 'none' }]];
  const PROMPT = [[0, ''], [.4, 'the person calls: Come here.'], [2.8, 'call again, and reach for it.'], [4.8, 'sit down beside the door.'], [5.8, 'open the door.'],
    [6.4, 'offer a hand, low.'], [7.0, "say it softly: it's all right."], [25.8, 'come in.']];

  // ------------------------------------------------------------------ drawing helpers (screen space)
  const P = pts => { const c = new Path2D(); pts.forEach((p, i) => i ? c.lineTo(p[0], p[1]) : c.moveTo(p[0], p[1])); c.closePath(); return c; };
  const parts = (E, pre) => E.rec.parts.filter(p => p.name.startsWith(pre || 'dog.'));
  const J = (E, n) => E.rec.joints[n] || [0, 0];
  const cen = pts => { let x = 0, y = 0; for (const p of pts) { x += p[0]; y += p[1]; } return [x / pts.length, y / pts.length]; };
  const bbox = pts => { let a = 1e9, b = 1e9, c = -1e9, d = -1e9; for (const p of pts) { a = Math.min(a, p[0]); b = Math.min(b, p[1]); c = Math.max(c, p[0]); d = Math.max(d, p[1]); } return [a, b, c, d]; };
  const allPts = (E, pre) => parts(E, pre).flatMap(p => p.pts);
  function rnd(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32); }
  function fillParts(ctx, E, pre, fill, stroke, lw) { for (const p of parts(E, pre)) { const q = P(p.pts); if (fill) { ctx.fillStyle = typeof fill === 'function' ? fill(p) : fill; ctx.fill(q); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 1.5; ctx.stroke(q); } } }
  function dot(ctx, p, r, c, ring) { ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7); if (ring) { ctx.strokeStyle = c; ctx.lineWidth = ring; ctx.stroke(); } else { ctx.fillStyle = c; ctx.fill(); } }
  function line(ctx, a, b, c, w, dash) { ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.strokeStyle = c; ctx.lineWidth = w || 1.5; ctx.setLineDash(dash || []); ctx.stroke(); ctx.setLineDash([]); }
  function label(ctx, x, y, s, o) {
    o = o || {}; ctx.font = `${o.w || 600} ${o.size || 15}px "JetBrains Mono", monospace`; const w = ctx.measureText(s).width;
    if (o.bg !== false) { ctx.fillStyle = o.bg || 'rgba(14,12,10,.82)'; ctx.fillRect(x - 5, y - (o.size || 15) - 3, w + 10, (o.size || 15) + 9); }
    ctx.fillStyle = o.c || '#fbf7ee'; ctx.fillText(s, x, y);
  }
  // triangulate a part: rings from the centroid out to the outline (a mesh, as a deformation system would see it)
  function mesh(pts, rings) { const c = cen(pts), T = []; rings = rings || 2; const R = []; for (let k = 0; k <= rings; k++) R.push(pts.map(p => [lerp(c[0], p[0], k / rings), lerp(c[1], p[1], k / rings)]));
    for (let k = 0; k < rings; k++) for (let i = 0; i < pts.length; i++) { const j = (i + 1) % pts.length; if (k === 0) T.push([c, R[1][i], R[1][j]]); else { T.push([R[k][i], R[k + 1][i], R[k + 1][j]]); T.push([R[k][i], R[k + 1][j], R[k][j]]); } } return T; }
  const CHAIN = [['dog.neck', 'dog.head'], ['dog.head', 'dog.nose'], ['dog.neck', 'dog.shoulder'], ['dog.shoulder', 'dog.hip'], ['dog.hip', 'dog.tailRoot'], ['dog.tailRoot', 'dog.tailTip'],
    ['dog.foreNear.root', 'dog.foreNear.knee'], ['dog.foreNear.knee', 'dog.foreNear.foot'], ['dog.hindNear.root', 'dog.hindNear.knee'], ['dog.hindNear.knee', 'dog.hindNear.foot'],
    ['dog.foreFar.root', 'dog.foreFar.knee'], ['dog.foreFar.knee', 'dog.foreFar.foot'], ['dog.hindFar.root', 'dog.hindFar.knee'], ['dog.hindFar.knee', 'dog.hindFar.foot'], ['dog.head', 'dog.earBase'], ['dog.earBase', 'dog.earTip']];
  function bones(ctx, E, col, w) { for (const [a, b] of CHAIN) { const A = J(E, a), B = J(E, b); if (!E.rec.joints[a] || !E.rec.joints[b]) continue; line(ctx, A, B, col, w || 3); dot(ctx, A, 4, col); } }
  function spineBone(ctx, A, B, col) { const dx = B[0] - A[0], dy = B[1] - A[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L * 6, ny = dx / L * 6;
    ctx.beginPath(); ctx.moveTo(A[0] + nx, A[1] + ny); ctx.lineTo(B[0], B[1]); ctx.lineTo(A[0] - nx, A[1] - ny); ctx.closePath(); ctx.fillStyle = col; ctx.globalAlpha = .7; ctx.fill(); ctx.globalAlpha = 1; dot(ctx, A, 5, '#fff', 2); }
  const hsl = (h, s, l, a) => `hsla(${h},${s}%,${l}%,${a === undefined ? 1 : a})`;
  const grey = c => { const m = /#(..)(..)(..)/.exec(c); if (!m) return c; const v = Math.round((parseInt(m[1], 16) * .3 + parseInt(m[2], 16) * .59 + parseInt(m[3], 16) * .11)); return `rgb(${v},${v},${v})`; };
  const tint = (c, r, g, b, k) => { const m = /#(..)(..)(..)/.exec(c); if (!m) return c; const f = (x, y) => Math.round(lerp(parseInt(x, 16), y, k)); return `rgb(${f(m[1], r)},${f(m[2], g)},${f(m[3], b)})`; };
  function hatch(ctx, path, ang, gap, col, lw) { ctx.save(); ctx.clip(path); ctx.strokeStyle = col; ctx.lineWidth = lw || 1; ctx.beginPath(); const c = Math.cos(ang), s = Math.sin(ang);
    for (let k = -1500; k < 1500; k += gap) { ctx.moveTo(640 + c * -1500 - s * k, 360 + s * -1500 + c * k); ctx.lineTo(640 + c * 1500 - s * k, 360 + s * 1500 + c * k); } ctx.stroke(); ctx.restore(); }
  function grain(ctx, amt, seed) { const r = rnd(seed); ctx.save(); for (let i = 0; i < 900; i++) { ctx.fillStyle = r() < .5 ? `rgba(0,0,0,${amt * r()})` : `rgba(255,255,255,${amt * r()})`; ctx.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); } ctx.restore(); }
  function stateChart(ctx, x, y, cur, col) {
    const N = [['watch', 0, 0], ['approach', 1, 0], ['lie_down', 2, 0], ['retreat', 0, 1], ['refuse', 1, 1]];
    for (const [n, i, j] of N) { const on = n === cur, X = x + i * 132, Y = y + j * 52; ctx.fillStyle = on ? (col || C.stamp) : 'rgba(14,12,10,.78)'; ctx.fillRect(X, Y, 122, 40);
      ctx.font = '600 15px "JetBrains Mono"'; ctx.fillStyle = on ? '#fff' : 'rgba(251,247,238,.7)'; ctx.fillText(n.replace('_', ' '), X + 10, Y + 26); }
  }

  // ------------------------------------------------------------------ backgrounds
  const SET = (ctx, E, st) => { const K = S.drawSet(ctx, E.cam, { door: E.door, light: .25 + .75 * E.door, windowLit: true }, W, H); return K; };
  function paper(ctx, col) { ctx.fillStyle = col; ctx.fillRect(0, 0, W, H); }
  function backdrop(ctx, a, b) { const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, a); g.addColorStop(1, b); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  function silhouetteSet(ctx, K, col) {
    ctx.fillStyle = col; ctx.fillRect(0, K.sy(0), W, H - K.sy(0));
    const x0 = K.sx(-.58), x1 = K.sx(.58), top = K.sy(2.22); ctx.fillRect(x0, top, x1 - x0, 18); ctx.fillRect(x0, top, 18, K.sy(0) - top); ctx.fillRect(x1 - 18, top, 18, K.sy(0) - top);
    // a lace of leaves along the top, the way a shadow-theatre border is cut
    const r = rnd(5); for (let x = -20; x < W + 40; x += 26) { const h = 30 + r() * 50; ctx.beginPath(); ctx.ellipse(x, 0, 16, h, r() - .5, 0, 7); ctx.fill(); }
    ctx.beginPath(); ctx.moveTo(K.sx(4.6), K.sy(0)); for (let i = 0; i <= 16; i++) { const a = i / 16 * Math.PI; ctx.lineTo(K.sx(4.9) + Math.cos(a) * 40 * (1 + (i % 2) * .5), K.sy(1.4) - Math.sin(a) * 70 * (1 + (i % 2) * .4)); } ctx.lineTo(K.sx(5.1), K.sy(0)); ctx.fill();
  }

  // ------------------------------------------------------------------ the 54 lenses (same order and numbers as the operator)
  const L = [];
  const add = (id, look, show, o) => L.push(Object.assign({ id, look, show }, o || {}));

  // ===== Artists & Directors
  add(1, 'engraved cut-outs, a hard substitution', 'The dog is an engraving cut from a book. When it is called, its head is swapped for the thing it wants least, a door, and the gag moves the smallest piece.', { still: 3.9,
    style: () => ({ fill: (c, n) => n ? '#efe6d2' : c, edge: '#1b1712', edgeWidth: .007, noTex: true }),
    after(ctx, E) { for (const p of parts(E)) { const q = P(p.pts); hatch(ctx, q, .7, 5, 'rgba(27,23,18,.55)', 1); if (p.name.includes('body') || p.name.includes('neck')) hatch(ctx, q, -.6, 7, 'rgba(27,23,18,.35)', 1); }
      const swap = E.d.state === 'retreat' || E.d.state === 'refuse'; if (swap) { const h = J(E, 'dog.skull'); ctx.save(); ctx.translate(h[0], h[1] - 6); ctx.fillStyle = '#6b2c22'; ctx.strokeStyle = '#1b1712'; ctx.lineWidth = 2;
        ctx.fillRect(-20, -34, 40, 62); ctx.strokeRect(-20, -34, 40, 62); ctx.fillStyle = '#c9a24a'; ctx.beginPath(); ctx.arc(12, 0, 3, 0, 7); ctx.fill(); ctx.restore(); label(ctx, h[0] - 30, h[1] - 52, 'HEAD → DOOR', { size: 12, c: '#ffd9b0' }); } }
  });
  add(2, 'shadow theatre, articulated silhouettes', 'Every piece becomes a black silhouette on a lit screen, so the dog\'s choice has to read from outline alone: the ears, the tail, the turned back.', { still: 29.5,
    bg(ctx, E) { backdrop(ctx, '#f0b45a', '#c2504a'); const K = S.camera(E.cam, W, H); return K; },
    style: () => ({ fill: () => '#0b0805', edge: null, noTex: true, noBrads: true }),
    under(ctx, E, K) { silhouetteSet(ctx, K, '#0b0805'); }
  });
  add(3, 'collage grammar, frottage parts', 'Each part of the dog is filled from a different found surface (bark, feathers, print, weave), so it reads as a dog made of other things.', {
    style: () => ({ noTex: true, edge: '#14110d' }),
    after(ctx, E) { const pats = [[.3, 4], [1.2, 3], [-.8, 6], [2.0, 5], [0, 3]]; parts(E).forEach((p, i) => { const q = P(p.pts); const [a, g] = pats[i % pats.length];
      ctx.fillStyle = ['#d9c7a3', '#a7b8a8', '#c8a07a', '#e5dccb', '#b9a48a'][i % 5]; ctx.fill(q); hatch(ctx, q, a, g, 'rgba(20,17,13,.6)', 1); if (i % 3 === 0) hatch(ctx, q, a + 1.4, g * 2, 'rgba(20,17,13,.35)', 1); ctx.strokeStyle = '#14110d'; ctx.lineWidth = 1.5; ctx.stroke(q); }); }
  });
  add(4, 'an autobiographical image torrent', 'The dog is built from a flood of tiny images, a new one every frame, and still reads as one dog choosing.', {
    after(ctx, E) { const b = bbox(allPts(E)); const r = rnd(Math.floor(E.t * 12)); ctx.save(); const clip = new Path2D(); for (const p of parts(E)) clip.addPath(P(p.pts)); ctx.clip(clip);
      for (let x = b[0]; x < b[2]; x += 9) for (let y = b[1]; y < b[3]; y += 9) { ctx.fillStyle = hsl(Math.floor(r() * 360), 45 + r() * 40, 35 + r() * 40); ctx.fillRect(x, y, 8, 8); ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.fillRect(x + 1 + r() * 4, y + 1 + r() * 4, 2, 2); } ctx.restore();
      label(ctx, 24, 120, `frame ${String(Math.floor(E.t * 24)).padStart(4, '0')} · ${Math.floor(b[2] - b[0]) * 2} images`, { size: 13 }); }
  });
  add(5, 'atmospheric multiplane', 'Glass plates in depth: haze between the house and the dog, the yard moving slower than the porch, so the dog sits inside air.', {
    under(ctx, E, K) { ctx.save(); ctx.fillStyle = 'rgba(190,200,215,.28)'; ctx.fillRect(0, 0, W, H); ctx.restore(); },
    after(ctx, E) { ctx.save(); ctx.globalAlpha = .55; fillParts(ctx, E, 'dog.', 'rgba(205,215,235,.75)'); ctx.restore(); ctx.save(); ctx.filter = 'blur(3px)'; ctx.globalAlpha = .5; fillParts(ctx, E, 'dog.', 'rgba(120,90,60,.6)'); ctx.restore(); const t = E.t; ctx.save(); for (let i = 0; i < 4; i++) { const g = ctx.createRadialGradient(((i * 400 + t * 30 * (i + 1)) % (W + 400)) - 200, 560 - i * 40, 20, ((i * 400 + t * 30 * (i + 1)) % (W + 400)) - 200, 560 - i * 40, 320);
      g.addColorStop(0, 'rgba(235,240,250,.30)'); g.addColorStop(1, 'rgba(235,240,250,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
      ctx.fillStyle = 'rgba(20,30,40,.65)'; for (let i = 0; i < 9; i++) { const x = ((i * 170 - t * 60) % (W + 200) + W + 200) % (W + 200) - 100; ctx.beginPath(); ctx.ellipse(x, 700, 70, 90, .2, 0, 7); ctx.fill(); } ctx.restore(); }
  });
  add(6, 'harmonic motion', 'The dog is redrawn as rings of points turning at harmonic rates, the way a motion-graphics machine draws; its walk and wag become the frequencies.', {
    bg(ctx, E) { paper(ctx, '#05060c'); return S.camera(E.cam, W, H); },
    style: () => ({ fill: () => 'rgba(0,0,0,0)', edge: null, noTex: true, noBrads: true }),
    after(ctx, E) { const tr = E.mem.whitney = E.mem.whitney || {}; ctx.save(); ctx.globalCompositeOperation = 'lighter';
      parts(E).forEach((p, pi) => { const n = p.pts.length; for (let i = 0; i < n; i++) { const q = p.pts[i], a = E.t * (1 + pi % 5) + i * 2 * Math.PI / n * (1 + pi % 3);
        dot(ctx, [q[0] + Math.cos(a) * 3, q[1] + Math.sin(a) * 3], 2.6, hsl(190 + pi * 9, 95, 62, .9)); } });
      parts(E, 'person.').forEach(p => p.pts.forEach((q, i) => i % 2 || dot(ctx, q, 1.6, 'rgba(120,140,255,.6)')));
      for (const n of ['dog.foreNear.foot', 'dog.hindNear.foot', 'dog.tailTip', 'dog.nose']) { const p = J(E, n); (tr[n] = tr[n] || []).push(p); if (tr[n].length > 60) tr[n].shift();
        ctx.beginPath(); tr[n].forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.strokeStyle = 'rgba(255,120,220,.7)'; ctx.lineWidth = 2; ctx.stroke(); }
      const g = J(E, 'dog.hip'); line(ctx, [0, E.K.sy(0)], [W, E.K.sy(0)], 'rgba(90,110,255,.5)', 1); ctx.restore(); }
  });
  add(7, 'drawn metamorphosis', 'The dog is a line drawing that boils and leaves its last positions behind, so every change of state is a drawing becoming the next drawing.', { still: 17.3,
    bg(ctx, E) { paper(ctx, '#f6f1e6'); return S.camera(E.cam, W, H); },
    style: () => ({ line: '#1b1712', lineWidth: .007, noBrads: true }),
    after(ctx, E) { const hist = E.mem.foldes = E.mem.foldes || []; if (Math.floor(E.t * 12) !== E.mem.fk) { E.mem.fk = Math.floor(E.t * 12); hist.push(parts(E).map(p => p.pts)); if (hist.length > 5) hist.shift(); }
      hist.forEach((h, i) => { ctx.strokeStyle = `rgba(212,42,30,${(i + 1) / 14})`; ctx.lineWidth = 1; for (const pts of h) ctx.stroke(P(pts)); });
      const r = rnd(Math.floor(E.t * 12)); ctx.strokeStyle = '#1b1712'; ctx.lineWidth = 1.2; for (const p of parts(E)) ctx.stroke(P(p.pts.map(q => [q[0] + (r() - .5) * 2.5, q[1] + (r() - .5) * 2.5]))); }
  });

  // ===== Research Pioneers
  add(8, 'constraints, points and lines (Sketchpad)', 'The dog becomes a constraint drawing on a phosphor screen: its feet are held to the floor and its lengths are kept, while the light pen moves the hand.', {
    bg(ctx, E) { paper(ctx, '#020a05'); return S.camera(E.cam, W, H); },
    style: () => ({ line: '#3dff8a', lineWidth: .006, noBrads: true }),
    after(ctx, E, K) { ctx.save(); ctx.shadowColor = '#3dff8a'; ctx.shadowBlur = 8; line(ctx, [0, K.sy(0)], [W, K.sy(0)], '#3dff8a', 1);
      for (const n of ['dog.foreNear.foot', 'dog.hindNear.foot', 'dog.foreFar.foot', 'dog.hindFar.foot']) { const p = J(E, n); ctx.strokeStyle = '#3dff8a'; ctx.strokeRect(p[0] - 5, K.sy(0) - 5, 10, 10); }
      bones(ctx, E, 'rgba(61,255,138,.6)', 1); const h = J(E, 'person.arm.hand'); dot(ctx, h, 14, '#b6ffd0', 1.5); line(ctx, [h[0] - 22, h[1]], [h[0] + 22, h[1]], '#b6ffd0', 1); line(ctx, [h[0], h[1] - 22], [h[0], h[1] + 22], '#b6ffd0', 1);
      label(ctx, 24, 120, 'FEET: ON FLOOR ✓  LENGTHS: KEPT ✓  HAND: TRACKED', { c: '#3dff8a', bg: 'rgba(0,0,0,.6)', size: 14 }); ctx.restore(); }
  });
  add(9, 'as-rigid-as-possible puppetry', 'The dog becomes a mesh of triangles that bend but try not to stretch; red triangles are the ones being stretched by the pose.', {
    after(ctx, E) { const prev = E.mem.arap = E.mem.arap || {}; for (const p of parts(E)) { const T = mesh(p.pts, 2); T.forEach((t, i) => { const k = p.name + i, a = Math.abs((t[1][0] - t[0][0]) * (t[2][1] - t[0][1]) - (t[2][0] - t[0][0]) * (t[1][1] - t[0][1]));
      const s = prev[k] ? clamp(Math.abs(a / prev[k] - 1) * 8) : 0; prev[k] = a; ctx.fillStyle = `rgba(212,42,30,${s * .6})`; ctx.fill(P(t)); ctx.strokeStyle = 'rgba(20,17,13,.55)'; ctx.lineWidth = .8; ctx.stroke(P(t)); }); } }
  });
  add(10, 'moving least squares deformation', 'A lattice is laid over the dog and pinned at six handles; as the dog moves, the lattice bends smoothly between the pins and the dog bends with it.', {
    after(ctx, E) { const hs = ['dog.nose', 'dog.shoulder', 'dog.hip', 'dog.tailTip', 'dog.foreNear.foot', 'dog.hindNear.foot'].map(n => J(E, n)); const b = bbox(allPts(E));
      const warp = (x, y) => { let dx = 0, dy = 0; for (const h of hs) { const w = Math.exp(-Math.hypot(h[0] - x, h[1] - y) / 50); dx += Math.sin(E.t * 2.2 + h[1] / 25) * 9 * w; dy += Math.cos(E.t * 1.7 + h[0] / 30) * 6 * w; } return [x + dx, y + dy]; };
      ctx.save(); const clip = new Path2D(); for (const p of parts(E)) clip.addPath(P(p.pts)); ctx.clip(clip);
      for (let x = b[0] - 20, i = 0; x < b[2] + 20; x += 12, i++) for (let y = b[1] - 20, j = 0; y < b[3] + 20; y += 12, j++) { const q = [warp(x, y), warp(x + 12, y), warp(x + 12, y + 12), warp(x, y + 12)];
        ctx.fillStyle = (i + j) % 2 ? 'rgba(15,143,128,.55)' : 'rgba(251,247,238,.5)'; ctx.fill(P(q)); } ctx.restore();
      ctx.strokeStyle = 'rgba(15,143,128,.9)'; ctx.lineWidth = 1; for (let x = b[0] - 20; x < b[2] + 20; x += 24) { ctx.beginPath(); for (let y = b[1] - 30; y < b[3] + 30; y += 4) { const q = warp(x, y); ctx.lineTo(q[0], q[1]); } ctx.stroke(); }
      hs.forEach(h => { dot(ctx, h, 8, '#0f8f80'); dot(ctx, h, 8, '#fff', 2); }); }
  });
  add(11, 'video puppetry on a tabletop', 'The paper dog is held on rods from above, the way a tabletop performer tracks and moves real cut-outs under a camera.', {
    after(ctx, E) { fillParts(ctx, E, 'dog.', p => ['rgba(255,210,63,.45)', 'rgba(255,90,90,.4)', 'rgba(90,200,255,.4)'][p.name.length % 3], '#ffd23f', 2); for (const n of ['dog.shoulder', 'dog.hip', 'dog.head']) { const p = J(E, n); line(ctx, p, [p[0] + 60, -10], 'rgba(40,30,20,.85)', 4); dot(ctx, p, 6, '#c9a24a'); }
      for (const n of ['dog.skull', 'dog.body']) { const p = n === 'dog.body' ? cen(parts(E, 'dog.body')[0].pts) : J(E, n); ctx.strokeStyle = '#ffd23f'; ctx.lineWidth = 2; ctx.strokeRect(p[0] - 12, p[1] - 12, 24, 24); }
      label(ctx, 24, 120, 'TRACKING 3 MARKERS · TOP CAMERA', { size: 13 }); }
  });
  add(12, 'localized deformation weights', 'Each bone owns the paper near it, and the colour shows how much: the weights that let one hand move without dragging the whole dog.', {
    after(ctx, E) { const bs = ['dog.head', 'dog.shoulder', 'dog.hip', 'dog.tailRoot'].map(n => J(E, n)); for (const p of parts(E)) { const c = cen(p.pts); let best = 0, bd = 1e9; bs.forEach((b, i) => { const d = Math.hypot(b[0] - c[0], b[1] - c[1]); if (d < bd) { bd = d; best = i; } });
      ctx.fillStyle = hsl([0, 45, 200, 280][best], 85, 55, .55 + .3 * Math.exp(-bd / 50)); ctx.fill(P(p.pts)); } bs.forEach((b, i) => dot(ctx, b, 7, hsl([0, 45, 200, 280][i], 90, 45))); }
  });
  add(13, 'secondary motion', 'The ears and tail lag behind the body and overshoot: their last positions trail behind them in colour, so the follow-through the dog\'s choices cause is visible.', { still: 17.0,
    after(ctx, E) { fillParts(ctx, E, 'dog.', p => /ear|tail|neck|skull|snout/.test(p.name) ? 'rgba(255,59,107,.65)' : 'rgba(255,59,107,.12)'); const hist = E.mem.sec = E.mem.sec || []; hist.push(parts(E).filter(p => /ear|tail|snout|skull/.test(p.name)).map(p => p.pts)); if (hist.length > 9) hist.shift();
      hist.forEach((h, i) => { ctx.fillStyle = hsl(10 + i * 25, 90, 60, .12 + i * .05); for (const pts of h) ctx.fill(P(pts)); });
      for (const p of parts(E).filter(p => /ear|tail/.test(p.name))) { ctx.strokeStyle = '#ff3b6b'; ctx.lineWidth = 3; ctx.stroke(P(p.pts)); }
      label(ctx, 24, 120, `follow-through · wag ${E.dog.p.wag.toFixed(2)} · ear ${E.dog.p.ear.toFixed(2)}`, { size: 13 }); }
  });
  add(14, 'pose to pose, cast from a library', 'Along the top, the dog\'s library of drawn poses; the one it is in now lights up, and the dog itself is outlined in that pose\'s colour. The machine chooses the state, the library supplies the drawing.', { still: 3.8,
    after(ctx, E) { const names = ['watch', 'approach', 'retreat', 'lie_down', 'refuse'], cols = ['#9aa', '#0f8f80', '#c88a00', '#2f6fd6', '#d42a1e'];
      fillParts(ctx, E, 'dog.', null, cols[names.indexOf(E.d.state)], 4);
      names.forEach((n, i) => { const x = 250 + i * 160, on = E.d.state === n; ctx.fillStyle = on ? cols[i] : 'rgba(14,12,10,.82)'; ctx.fillRect(x, 100, 150, 84);
      ctx.save(); ctx.translate(x + 75, 168); ctx.scale(-1, 1); const p = { lie: n === 'lie_down' || n === 'refuse' ? 1 : 0, crouch: n === 'retreat' ? .9 : n === 'approach' ? .3 : 0, ear: n === 'retreat' ? 0 : .9, tail: n === 'retreat' ? 1.3 : .5, wag: 0, head: n === 'watch' ? .9 : .4, rest: n === 'refuse' ? 1 : 0, turn: 1, phase: 0, moving: 0, sniff: n === 'approach' ? 1 : 0, look: 0 };
      ctx.scale(100, 100); const st = Object.assign({}, S.STYLE); Object.assign(S.STYLE, { line: '#fff', lineWidth: .014 }); const rec = S.REC.on; S.REC.on = false; S.drawDog(ctx, p, 0); S.REC.on = rec; for (const k in S.STYLE) delete S.STYLE[k]; Object.assign(S.STYLE, st); ctx.restore();
      label(ctx, x + 6, 120, n.replace('_', ' '), { bg: false, size: 14 }); }); }
  });
  add(15, 'a learned layered puppet', 'The dog pulled apart into the layers a model would have to learn from a few drawings: each part on its own plate, stacked in depth.', {
    after(ctx, E) { const ps = parts(E); const k = .5 + .5 * Math.sin(E.t * .8); ctx.save(); ps.forEach((p, i) => { const o = (i - ps.length / 2) * 9 * k; ctx.save(); ctx.translate(o * 1.4, -o); ctx.globalAlpha = .9; ctx.fillStyle = hsl(i * 23, 55, 60); ctx.fill(P(p.pts)); ctx.strokeStyle = '#14110d'; ctx.lineWidth = 1; ctx.stroke(P(p.pts)); ctx.restore(); }); ctx.restore();
      label(ctx, 24, 120, `${ps.length} layers · drawn in depth order`, { size: 13 }); }
  });

  // ===== Studios & Software
  add(16, 'recastable performance', 'The performance stays, the cast changes: the person\'s photographed face rides on the dog\'s head, and the dog acts exactly as before.', { still: 3.0,
    after(ctx, E) { fillParts(ctx, E, 'dog.', p => /body|neck|upper/.test(p.name) ? '#2f5d73' : null); for (const p of parts(E, 'dog.body')) { const c = cen(p.pts); [-14, 0, 14].forEach(o => dot(ctx, [c[0] + o, c[1] + 4], 3, '#c9a24a')); } const h = J(E, 'dog.skull'); ctx.save(); ctx.translate(h[0] + 2, h[1] - 4); ctx.rotate(Math.sin(E.t * 6) * .08); ctx.fillStyle = '#c99572'; ctx.beginPath(); ctx.ellipse(0, 0, 22, 25, 0, 0, 7); ctx.fill(); ctx.strokeStyle = '#3a2a1e'; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = '#2a1f1a'; ctx.beginPath(); ctx.ellipse(0, -16, 22, 10, 0, Math.PI, 0); ctx.fill(); dot(ctx, [-8, -2], 2.5, '#14110d'); dot(ctx, [6, -2], 2.5, '#14110d'); ctx.beginPath(); ctx.arc(-1, 9, 7, 0, Math.PI); ctx.strokeStyle = '#3a1712'; ctx.stroke(); ctx.restore(); }
  });
  add(17, 'a repeatable graphic grammar', 'Construction paper, flat colours, two-frame motion: the cheapest grammar that still lets the dog refuse with a turn of its body.', {
    style: () => ({ noTex: true, edge: null, noBrads: true, fill: (c, n) => n && n.startsWith('dog.') ? '#c8742e' : n && n.startsWith('person.') ? '#2d6ccd' : c }),
    after(ctx, E) { const h = J(E, 'dog.eye'); dot(ctx, h, 6, '#fff'); dot(ctx, h, 2.5, '#000'); const p = J(E, 'person.eye'); dot(ctx, p, 6, '#fff'); dot(ctx, p, 2.5, '#000'); }
  });
  add(18, 'painterly puppet discipline', 'The porch repainted as a flat, ornamental world in deep green and gold; the dog keeps its paper joints but is gilded and patterned with spirals, the way a painterly studio disciplines a puppet.', {
    style: () => ({ fill: (c, n) => n && n.startsWith('dog.') ? (/Far/.test(n) ? '#a8781e' : '#d9a634') : n && n.startsWith('person.') ? '#7a2e2a' : c, edge: '#1d1a12', edgeWidth: .01, noTex: true }),
    under(ctx, E) { ctx.save(); ctx.globalCompositeOperation = 'color'; ctx.fillStyle = '#1f5a48'; ctx.fillRect(0, 0, W, H); ctx.restore(); },
    after(ctx, E) { for (const p of parts(E).filter(p => /body|skull|neck/.test(p.name))) { ctx.save(); ctx.clip(P(p.pts)); const b = bbox(p.pts); ctx.strokeStyle = 'rgba(80,40,10,.7)'; ctx.lineWidth = 1.5;
        for (let x = b[0]; x < b[2] + 14; x += 18) for (let y = b[1]; y < b[3] + 14; y += 18) { ctx.beginPath(); for (let a = 0; a < 9; a += .3) ctx.lineTo(x + Math.cos(a) * a * .9, y + Math.sin(a) * a * .9); ctx.stroke(); } ctx.restore(); }
      ctx.save(); ctx.strokeStyle = '#d9a634'; ctx.lineWidth = 4; ctx.strokeRect(14, 94, W - 28, H - 108); for (let x = 40; x < W - 30; x += 40) { ctx.beginPath(); ctx.arc(x, 104, 7, 0, Math.PI); ctx.stroke(); ctx.beginPath(); ctx.arc(x, H - 24, 7, Math.PI, 0); ctx.stroke(); } ctx.restore(); }
  });
  add(19, 'smart bones', 'Bones with a dial: one value, ears up to ears flat, drives several pieces at once, the way a smart bone corrects a rig.', { still: 1.6,
    after(ctx, E) { fillParts(ctx, E, 'dog.', p => /ear/.test(p.name) ? 'rgba(255,159,26,.85)' : /tail/.test(p.name) ? 'rgba(255,159,26,.7)' : 'rgba(255,159,26,.3)', '#ff9f1a', 1.5); bones(ctx, E, '#ff9f1a', 3); const v = E.dog.p.ear; const x = 1050, y = 120; ctx.fillStyle = 'rgba(14,12,10,.82)'; ctx.fillRect(x - 70, y - 50, 200, 120);
      ctx.beginPath(); ctx.arc(x, y + 20, 34, Math.PI, 0); ctx.strokeStyle = '#555'; ctx.lineWidth = 6; ctx.stroke(); ctx.beginPath(); ctx.arc(x, y + 20, 34, Math.PI, Math.PI + clamp(v) * Math.PI); ctx.strokeStyle = '#ff9f1a'; ctx.stroke();
      label(ctx, x - 60, y - 20, 'ears', { bg: false, size: 13 }); label(ctx, x + 50, y + 26, clamp(v).toFixed(2), { bg: false, size: 16, c: '#ff9f1a' }); }
  });
  add(20, 'a production rig: pegs and nodes', 'The rig as a production pipeline sees it: every piece a node, pegged to its parent, and the node view beside the stage.', {
    after(ctx, E) { fillParts(ctx, E, 'dog.', p => ({ body: 'rgba(36,72,89,.6)', chest: 'rgba(36,72,89,.6)', neck: 'rgba(127,224,210,.5)', skull: 'rgba(127,224,210,.65)', snout: 'rgba(127,224,210,.65)', ear: 'rgba(200,255,250,.7)', earFar: 'rgba(200,255,250,.7)', tail: 'rgba(80,160,200,.6)' })[p.name.split('.')[1]] || 'rgba(60,120,150,.55)', '#7fe0d2', 1); const ns = [['dog', 980, 130], ['body', 980, 190], ['neck', 900, 250], ['head', 900, 310], ['ear', 900, 370], ['tail', 1060, 250], ['fore', 1140, 250], ['hind', 1060, 310]];
      ctx.fillStyle = 'rgba(14,12,10,.85)'; ctx.fillRect(860, 100, 380, 300); const at = n => ns.find(x => x[0] === n);
      [['dog', 'body'], ['body', 'neck'], ['neck', 'head'], ['head', 'ear'], ['body', 'tail'], ['body', 'fore'], ['body', 'hind']].forEach(([a, b]) => line(ctx, [at(a)[1] + 30, at(a)[2] + 14], [at(b)[1] + 30, at(b)[2]], '#7fe0d2', 1.5));
      ns.forEach(([n, x, y]) => { ctx.fillStyle = '#244859'; ctx.fillRect(x, y, 70, 22); label(ctx, x + 6, y + 16, n, { bg: false, size: 12 }); });
      for (const n of ['dog.shoulder', 'dog.hip', 'dog.neck', 'dog.head', 'dog.tailRoot']) { const p = J(E, n); ctx.strokeStyle = '#7fe0d2'; ctx.lineWidth = 2; ctx.strokeRect(p[0] - 6, p[1] - 6, 12, 12); } }
  });
  add(21, 'photo to actor', 'A flat picture becomes an actor: a sprite with its bounding box and part handles, ready to be told what to do.', {
    after(ctx, E) { fillParts(ctx, E, 'dog.', 'rgba(59,130,246,.38)', '#3b82f6', 1.5); const b = bbox(allPts(E)); ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 2; ctx.setLineDash([6, 4]); ctx.strokeRect(b[0] - 8, b[1] - 8, b[2] - b[0] + 16, b[3] - b[1] + 16); ctx.setLineDash([]);
      for (const [x, y] of [[b[0], b[1]], [b[2], b[1]], [b[0], b[3]], [b[2], b[3]]]) { ctx.fillStyle = '#fff'; ctx.fillRect(x - 13, y - 13, 10, 10); ctx.strokeRect(x - 13, y - 13, 10, 10); }
      for (const p of parts(E)) { const c = cen(p.pts); ctx.fillStyle = '#3b82f6'; ctx.fillRect(c[0] - 3, c[1] - 3, 6, 6); } label(ctx, b[0] - 8, b[1] - 16, 'ACTOR · dog', { size: 12, bg: '#3b82f6' }); }
  });
  add(22, 'live performance capture', 'A performer\'s face drives the dog live: the inset tracks a face, and its eyebrows become the dog\'s ears.', { still: 1.4,
    after(ctx, E) { const rec = Math.floor(E.t * 2) % 2; fillParts(ctx, E, 'dog.', p => /ear/.test(p.name) ? 'rgba(127,224,210,.85)' : 'rgba(212,42,30,.32)', rec ? '#d42a1e' : '#7fe0d2', 2); const x = 990, y = 110, v = E.dog.p.ear; ctx.fillStyle = '#111'; ctx.fillRect(x, y, 240, 180); ctx.strokeStyle = '#d42a1e'; ctx.strokeRect(x, y, 240, 180); dot(ctx, [x + 14, y + 14], 5, '#d42a1e');
      ctx.fillStyle = '#4a4a4a'; ctx.beginPath(); ctx.ellipse(x + 120, y + 100, 52, 64, 0, 0, 7); ctx.fill(); const by = y + 72 - v * 14; [[x + 95, by], [x + 145, by]].forEach(p => { line(ctx, [p[0] - 14, p[1]], [p[0] + 14, p[1] - 2], '#7fe0d2', 3); dot(ctx, p, 3, '#7fe0d2'); });
      [[x + 98, y + 92], [x + 142, y + 92], [x + 120, y + 112], [x + 120, y + 130]].forEach(p => dot(ctx, p, 3, '#7fe0d2')); line(ctx, [x + 95, by], J(E, 'dog.earTip'), 'rgba(127,224,210,.5)', 1, [4, 4]);
      label(ctx, x + 6, y + 172, `brows → ears ${clamp(v).toFixed(2)}`, { bg: false, size: 12 }); }
  });
  add(23, 'a skeletal runtime', 'The dog as a runtime ships it: bones, slots and attachments, the paper only skin hung on a skeleton the game engine plays.', {
    after(ctx, E) { ctx.save(); ctx.globalAlpha = .55; ctx.fillStyle = '#0b0d10'; for (const p of parts(E)) ctx.fill(P(p.pts)); ctx.restore(); for (const [a, b] of CHAIN) if (E.rec.joints[a] && E.rec.joints[b]) spineBone(ctx, J(E, a), J(E, b), '#ffd23f');
      label(ctx, 24, 120, `bones ${CHAIN.length} · slots ${parts(E).length} · state ${E.d.state}`, { size: 13 }); }
  });
  add(24, 'portrait volume illusion', 'Close on the dog\'s head: a flat drawing given volume by a deforming mesh, so it seems to turn toward the doorway.', { still: 27.0,
    cam: E => ({ x: E.d.x - .15, y: .15, zoom: 4.2 }),
    after(ctx, E) { for (const n of ['dog.skull', 'dog.snout', 'dog.ear']) for (const p of parts(E, n)) mesh(p.pts, 3).forEach(t => { ctx.strokeStyle = 'rgba(255,255,255,.45)'; ctx.lineWidth = .7; ctx.stroke(P(t)); }); const h = J(E, 'dog.skull'); dot(ctx, h, 9, '#ff5ab4', 3); }
  });
  add(25, 'interactive state machines', 'The rig answers to a state graph with inputs, the way an interactive runtime wires it: the dog is tinted by the state it is in, and the graph beside it shows the inputs that moved it there.', { still: 3.8,
    after(ctx, E) { const cols = { watch: '#7f8c8d', approach: '#1abc9c', retreat: '#f39c12', lie_down: '#3498db', refuse: '#e74c3c' }; ctx.save(); ctx.globalCompositeOperation = 'color'; fillParts(ctx, E, 'dog.', cols[E.d.state]); ctx.restore();
      const d = J(E, 'dog.skull'); const N = { watch: [0, 0], approach: [-1, -1], retreat: [1, -1], lie_down: [-1, 1], refuse: [1, 1] }; const c = [d[0], d[1] - 150];
      for (const [n, [i, j]] of Object.entries(N)) { const p = [c[0] + i * 95, c[1] + j * 45]; if (n !== 'watch') line(ctx, c, p, 'rgba(255,255,255,.5)', 1.5); }
      for (const [n, [i, j]] of Object.entries(N)) { const p = [c[0] + i * 95, c[1] + j * 45], on = n === E.d.state; ctx.beginPath(); ctx.ellipse(p[0], p[1], 46, 16, 0, 0, 7); ctx.fillStyle = on ? cols[n] : 'rgba(14,12,10,.85)'; ctx.fill(); ctx.strokeStyle = cols[n]; ctx.lineWidth = 2; ctx.stroke();
        ctx.font = '600 12px "JetBrains Mono"'; ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.fillText(n.replace('_', ' '), p[0], p[1] + 4); ctx.textAlign = 'left'; }
      ctx.fillStyle = 'rgba(14,12,10,.85)'; ctx.fillRect(24, 100, 220, 92); ['voice: ' + E.w.voice, 'hand: ' + E.w.hand, 'door: ' + E.w.door, 'trust: ' + E.d.trust.toFixed(2)].forEach((s, i) => label(ctx, 36, 122 + i * 20, s, { bg: false, size: 13, c: '#1abc9c' })); }
  });
  add(26, 'an archive stage renderer', 'The dog as a renderer batches it: cut into sprite tiles, each tile one texture sample, with the draw count running; at this resolution the dog is a grid the engine can push by the thousand.', {
    after(ctx, E) { const b = bbox(allPts(E, 'dog.')), s = 10; const x0 = Math.floor(b[0] / s) * s, y0 = Math.floor(b[1] / s) * s; const img = ctx.getImageData(x0, y0, Math.ceil((b[2] - x0) / s) * s + s, Math.ceil((b[3] - y0) / s) * s + s);
      const clip = new Path2D(); for (const p of parts(E, 'dog.')) clip.addPath(P(p.pts)); let n = 0; ctx.save();
      for (let y = 0; y + s <= img.height; y += s) for (let x = 0; x + s <= img.width; x += s) { const X = x0 + x + s / 2, Y = y0 + y + s / 2; if (!ctx.isPointInPath(clip, X, Y)) continue; const i = ((y + s / 2) * img.width + x + s / 2) * 4;
        ctx.fillStyle = `rgb(${img.data[i]},${img.data[i + 1]},${img.data[i + 2]})`; ctx.fillRect(x0 + x, y0 + y, s - 1, s - 1); ctx.strokeStyle = 'rgba(127,224,210,.35)'; ctx.strokeRect(x0 + x + .5, y0 + y + .5, s - 1, s - 1); n++; } ctx.restore();
      ctx.fillStyle = 'rgba(0,0,0,.8)'; ctx.fillRect(1010, 100, 230, 74); label(ctx, 1020, 126, `dog sprites ${n}`, { bg: false, size: 13, c: '#7fe0d2' }); label(ctx, 1020, 150, `draw calls 1 · ${(15 + 2 * Math.sin(E.t * 3)).toFixed(1)} ms`, { bg: false, size: 13, c: '#7fe0d2' }); }
  });
  add(27, 'a declarative film compiler', 'The film as code compiles it: tracks for the prompts, the dog\'s states and the camera, with a playhead running through, and the dog tinted by the track segment it is playing.', {
    after(ctx, E) { const cols = { watch: '#7f8c8d', approach: '#0f8f80', retreat: '#c88a00', lie_down: '#2f6fd6', refuse: '#d42a1e' }; ctx.save(); ctx.globalCompositeOperation = 'color'; fillParts(ctx, E, 'dog.', cols[E.d.state]); ctx.restore();
      const x0 = 120, x1 = 1160, y = 112, k = t => x0 + (x1 - x0) * t / LOOP; ctx.fillStyle = 'rgba(14,12,10,.88)'; ctx.fillRect(100, y - 10, 1080, 96);
      label(ctx, 108, y + 12, 'prompts', { bg: false, size: 11 }); PROMPT.slice(1).forEach(([t]) => { ctx.fillStyle = '#d42a1e'; ctx.fillRect(k(t), y + 2, 30, 14); });
      label(ctx, 108, y + 42, 'dog', { bg: false, size: 11 }); (E.mem.segs || []).forEach(s => { ctx.fillStyle = cols[s.s]; ctx.fillRect(k(s.a), y + 32, Math.max(2, k(s.b) - k(s.a)), 14); });
      label(ctx, 108, y + 72, 'camera', { bg: false, size: 11 }); ctx.fillStyle = '#7fe0d2'; ctx.fillRect(k(0), y + 62, k(LOOP) - k(0), 6); line(ctx, [k(E.t), y - 6], [k(E.t), y + 82], '#fff', 2); }
  });
  add(28, 'masks and performance plates', 'Masks drawn around the dog and the person, with the plate behind them: the compositor\'s view, where every piece is a matte.', {
    after(ctx, E) { const b = parts(E); ctx.save(); ctx.strokeStyle = '#ffd23f'; ctx.lineWidth = 1.5; for (const p of b) { ctx.stroke(P(p.pts)); p.pts.filter((_, i) => i % 4 === 0).forEach(q => { ctx.fillStyle = '#ffd23f'; ctx.fillRect(q[0] - 2, q[1] - 2, 4, 4); }); }
      ctx.fillStyle = 'rgba(14,12,10,.85)'; ctx.fillRect(1030, 100, 210, 130); ['dog · mask 1', 'person · mask 2', 'jamb · track matte', 'plate · porch'].forEach((s, i) => label(ctx, 1042, 128 + i * 28, s, { bg: false, size: 13, c: i < 2 ? '#ffd23f' : '#fbf7ee' })); ctx.restore(); }
  });

  // ===== Algorithms & Techniques
  add(29, 'GrabCut extraction', 'A rectangle around the dog and the algorithm splits foreground from background: blue is dog, red is porch.', { still: 29.5,
    after(ctx, E) { const b = bbox(allPts(E)); ctx.fillStyle = 'rgba(220,40,40,.25)'; ctx.fillRect(b[0] - 20, b[1] - 20, b[2] - b[0] + 40, b[3] - b[1] + 40); fillParts(ctx, E, 'dog.', 'rgba(40,120,255,.55)');
      ctx.strokeStyle = '#ff2e2e'; ctx.lineWidth = 2; ctx.strokeRect(b[0] - 20, b[1] - 20, b[2] - b[0] + 40, b[3] - b[1] + 40); label(ctx, b[0] - 20, b[1] - 28, 'GrabCut · 5 iterations', { size: 12 }); }
  });
  add(30, 'prompted mask proposals', 'Two clicks, one on the dog and one on the porch, and the model proposes a mask with a confidence; the dog is found by being pointed at.', {
    after(ctx, E) { fillParts(ctx, E, 'dog.', 'rgba(30,144,255,.45)', 'rgba(30,144,255,.9)', 1); const c = J(E, 'dog.shoulder'); dot(ctx, c, 8, '#2ecc71'); dot(ctx, c, 8, '#fff', 2);
      const n = [c[0] + 160, c[1] + 40]; dot(ctx, n, 8, '#e74c3c'); dot(ctx, n, 8, '#fff', 2); label(ctx, c[0] - 20, c[1] - 70, `mask 0 · IoU ${(.9 + .05 * Math.sin(E.t)).toFixed(2)}`, { size: 12 }); }
  });
  add(31, 'alpha matting: hair, lace and smoke', 'A trimap around the dog: black is surely porch, white surely dog, grey the fringe (ears, tail, paws) where the matte has to be solved.', { still: 29.0,
    after(ctx, E) { ctx.save(); ctx.fillStyle = 'rgba(0,0,0,.82)'; ctx.fillRect(0, 0, W, H); ctx.lineJoin = 'round'; for (const p of parts(E)) { ctx.strokeStyle = 'rgba(128,128,128,1)'; ctx.lineWidth = /ear|tail|paw/.test(p.name) ? 18 : 9; ctx.stroke(P(p.pts)); }
      for (const p of parts(E)) { ctx.fillStyle = '#fff'; ctx.fill(P(p.pts)); } ctx.restore(); label(ctx, 24, 120, 'TRIMAP  ·  white: dog  grey: unknown  black: porch', { size: 13 }); }
  });
  add(32, 'forward kinematics', 'Rotate the shoulder and everything below it follows: the dog drawn as a chain of joints, each angle added to its parent\'s, with the angles written on the joints.', {
    after(ctx, E) { ctx.save(); ctx.globalAlpha = .55; fillParts(ctx, E, 'dog.', '#0b0d10'); ctx.restore(); bones(ctx, E, '#ff6b3d', 6);
      for (const [a, b] of [['dog.foreNear.root', 'dog.foreNear.knee'], ['dog.foreNear.knee', 'dog.foreNear.foot'], ['dog.hindNear.root', 'dog.hindNear.knee'], ['dog.hindNear.knee', 'dog.hindNear.foot'], ['dog.neck', 'dog.head']]) {
        const A = J(E, a), B = J(E, b), ang = Math.atan2(B[1] - A[1], B[0] - A[0]); ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.arc(A[0], A[1], 22, Math.PI / 2, ang, ang < Math.PI / 2); ctx.closePath(); ctx.fillStyle = 'rgba(255,176,138,.45)'; ctx.fill();
        label(ctx, A[0] + 14, A[1] - 8, `${Math.round((ang - Math.PI / 2) * 180 / Math.PI)}°`, { size: 12, bg: 'rgba(255,107,61,.9)' }); } }
  });
  add(33, 'inverse kinematics: contact and reach', 'Targets first, joints after: each foot is a target pinned to the floor and the leg solves to reach it; the dog is shown as the solver sees it, chains and targets, nothing else.', { still: 17.0,
    bg(ctx, E) { paper(ctx, '#101418'); const K = S.camera(E.cam, W, H); ctx.fillStyle = '#1e252c'; ctx.fillRect(0, K.sy(0), W, H); return K; },
    style: () => ({ line: 'rgba(255,255,255,.18)', lineWidth: .005, noBrads: true }),
    after(ctx, E, K) { for (const n of ['dog.foreNear', 'dog.hindNear', 'dog.foreFar', 'dog.hindFar', 'person.leg', 'person.arm']) { const f = J(E, n + (n.startsWith('person.arm') ? '.hand' : '.foot')), r = J(E, n.startsWith('person') ? (n === 'person.arm' ? 'person.shoulder' : 'person.hip') : n + '.root'), k = J(E, n + (n.startsWith('person') ? (n === 'person.arm' ? '.elbow' : '.knee') : '.knee'));
        line(ctx, r, k, '#d42a1e', 5); line(ctx, k, f, '#d42a1e', 5); dot(ctx, k, 5, '#fff'); dot(ctx, f, 13, '#ffd23f', 3); line(ctx, [f[0] - 18, f[1]], [f[0] + 18, f[1]], '#ffd23f', 1.5); line(ctx, [f[0], f[1] - 18], [f[0], f[1] + 18], '#ffd23f', 1.5); }
      bones(ctx, E, 'rgba(212,42,30,.6)', 3); label(ctx, 24, 120, 'targets: 4 paws on the floor · 1 hand · solved per frame', { size: 13 }); }
  });
  add(34, 'preserve-shape deformation', 'The dog\'s body as rigid cells that rotate instead of stretching; each cell shows its local rotation as a tick.', {
    after(ctx, E) { for (const p of parts(E, 'dog.body').concat(parts(E, 'dog.neck'))) mesh(p.pts, 2).forEach(t => { const c = cen(t); ctx.strokeStyle = 'rgba(15,143,128,.7)'; ctx.lineWidth = 1; ctx.stroke(P(t));
      const a = Math.atan2(t[1][1] - t[0][1], t[1][0] - t[0][0]); line(ctx, c, [c[0] + Math.cos(a) * 6, c[1] + Math.sin(a) * 6], '#fff', 1.5); }); }
  });
  add(35, 'gesture warp: drag a handle, the body follows', 'One handle at a time is dragged and the dog stretches toward it like rubber, the rest pinned: a gesture made directly on the drawing.', {
    after(ctx, E) { const names = ['dog.nose', 'dog.tailTip', 'dog.earTip', 'dog.foreNear.foot'], i = Math.floor(E.t / 1.2) % names.length, h = J(E, names[i]); const a = E.t * 3, pull = [Math.cos(a) * 28, -Math.abs(Math.sin(a)) * 30];
      ctx.save(); for (const p of parts(E, 'dog.')) { const q = p.pts.map(v => { const w = Math.exp(-Math.hypot(v[0] - h[0], v[1] - h[1]) / 45); return [v[0] + pull[0] * w, v[1] + pull[1] * w]; }); ctx.fillStyle = 'rgba(255,90,140,.55)'; ctx.fill(P(q)); ctx.strokeStyle = '#ff2e7a'; ctx.lineWidth = 1.5; ctx.stroke(P(q)); } ctx.restore();
      names.forEach((n, k) => { const p = J(E, n); dot(ctx, p, 7, k === i ? '#ff2e7a' : '#fff'); }); line(ctx, h, [h[0] + pull[0], h[1] + pull[1]], '#ff2e7a', 3, [5, 4]); dot(ctx, [h[0] + pull[0], h[1] + pull[1]], 10, '#ff2e7a', 3); }
  });
  add(36, 'bounded biharmonic weights: an auto-rig', 'Weights computed for each handle, shown one handle at a time: the heat of how far one bone\'s influence reaches across the dog.', {
    after(ctx, E) { const names = ['dog.head', 'dog.shoulder', 'dog.hip', 'dog.tailRoot', 'dog.foreNear.foot']; const n = names[Math.floor(E.t / 1.5) % names.length], b = J(E, n);
      for (const p of parts(E)) for (const t of mesh(p.pts, 2)) { const c = cen(t), w = Math.exp(-Math.hypot(c[0] - b[0], c[1] - b[1]) / 45); ctx.fillStyle = `hsl(${(1 - w) * 240},90%,50%)`; ctx.fill(P(t)); }
      dot(ctx, b, 8, '#fff', 3); label(ctx, 24, 120, `weights for ${n.replace('dog.', '')}`, { size: 13 }); }
  });
  add(37, 'weighted skinning', 'Where the shoulder\'s influence meets the hip\'s, the paper is shared: the dog is split into two colours with a blended band between, the region skinning has to solve.', {
    after(ctx, E) { const A = J(E, 'dog.shoulder'), B = J(E, 'dog.hip'); const g = ctx.createLinearGradient(A[0], A[1], B[0], B[1]); g.addColorStop(0, 'rgba(255,59,59,.75)'); g.addColorStop(.35, 'rgba(255,59,59,.75)'); g.addColorStop(.65, 'rgba(59,76,255,.75)'); g.addColorStop(1, 'rgba(59,76,255,.75)');
      fillParts(ctx, E, 'dog.', g, '#fff', 1); for (const p of parts(E, 'dog.')) p.pts.forEach((q, i) => i % 2 || dot(ctx, q, 2.5, '#fff')); dot(ctx, A, 9, '#ff3b3b', 3); dot(ctx, B, 9, '#3b4cff', 3); line(ctx, A, B, '#fff', 2); }
  });
  add(38, 'dynamic pose selection from drawings', 'Instead of bending one drawing, the dog flips between whole drawings, each a numbered card in red pencil, chosen from its library each time it changes state and held on twos.', {
    after(ctx, E) { const b = bbox(allPts(E, 'dog.')); const k = Math.floor(E.t * 12); ctx.save(); ctx.fillStyle = '#fbf7ee'; ctx.fillRect(b[0] - 18, b[1] - 30, b[2] - b[0] + 36, b[3] - b[1] + 44); ctx.strokeStyle = '#14110d'; ctx.strokeRect(b[0] - 18, b[1] - 30, b[2] - b[0] + 36, b[3] - b[1] + 44);
      const r = rnd(Math.floor(k / 2)); ctx.strokeStyle = '#c0392b'; ctx.lineWidth = 1.6; for (const p of parts(E, 'dog.')) ctx.stroke(P(p.pts.map(q => [q[0] + (r() - .5) * 2, q[1] + (r() - .5) * 2]))); ctx.restore();
      label(ctx, b[0] - 12, b[1] - 12, `#${['watch', 'approach', 'retreat', 'lie_down', 'refuse'].indexOf(E.d.state) + 1}.${Math.floor(k / 2) % 4}  ${E.d.state.replace('_', ' ')}`, { size: 12, bg: false, c: '#c0392b' }); }
  });
  add(39, 'multiview drawing substitution', 'When the dog turns its back, the side view is swapped for a turn drawing and then the back view: the three views drawn as cards.', { still: 3.7,
    after(ctx, E) { const tv = E.dog.p.turn, vc = tv > .5 ? 'rgba(212,42,30,.5)' : tv < -.5 ? 'rgba(47,111,214,.5)' : 'rgba(200,138,0,.5)'; fillParts(ctx, E, 'dog.', vc, '#fff', 1.5); const tr = E.dog.p.turn; [['side', 1], ['¾', 0], ['back', -1]].forEach(([n, v], i) => { const on = Math.abs(tr - v) < .5; const x = 980 + i * 86; ctx.fillStyle = on ? '#d42a1e' : 'rgba(14,12,10,.8)'; ctx.fillRect(x, 110, 78, 56); label(ctx, x + 10, 146, n, { bg: false, size: 15 }); });
      label(ctx, 980, 196, `turn ${tr.toFixed(2)}`, { size: 13 }); }
  });
  add(40, 'physical tabletop capture', 'The scene is a real tabletop shot from above at an angle: the floor tilts away, a lamp pools on the paper, and the cut-outs cast long hard shadows.', {
    after(ctx, E) { const c = ctx.canvas, tmp = (E.mem.tab = E.mem.tab || Object.assign(document.createElement('canvas'), { width: W, height: H })), g = tmp.getContext('2d'); g.drawImage(c, 0, 0);
      ctx.fillStyle = '#4a321e'; ctx.fillRect(0, 0, W, H); for (let y = 0; y < H; y += 2) { const k = .62 + .38 * (y / H), w = W * k; ctx.drawImage(tmp, 0, y, W, 2, (W - w) / 2, 70 + y * .9, w, 2); }
      const lg = ctx.createRadialGradient(640, 420, 60, 640, 420, 620); lg.addColorStop(0, 'rgba(255,225,170,.25)'); lg.addColorStop(1, 'rgba(20,10,0,.6)'); ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H); grain(ctx, .07, Math.floor(E.t * 12));
      label(ctx, 24, 120, 'TABLETOP · overhead camera, 35° · one lamp', { size: 13 }); }
  });
  add(41, 'secondary dynamics: inertia and restraint', 'Springs on every loose part, drawn as coils: the ears and tail carry momentum after the dog stops, then settle.', { still: 2.0,
    after(ctx, E) { fillParts(ctx, E, 'dog.', p => /ear|tail|neck/.test(p.name) ? 'rgba(255,210,63,.8)' : 'rgba(255,210,63,.2)'); for (const [a, b] of [['dog.earBase', 'dog.earTip'], ['dog.tailRoot', 'dog.tailTip'], ['dog.neck', 'dog.head']]) { const A = J(E, a), B = J(E, b); ctx.beginPath(); for (let i = 0; i <= 30; i++) { const t = i / 30, x = lerp(A[0], B[0], t), y = lerp(A[1], B[1], t), o = Math.sin(t * Math.PI * 14) * 5;
      const dx = B[0] - A[0], dy = B[1] - A[1], L = Math.hypot(dx, dy) || 1; ctx.lineTo(x - dy / L * o, y + dx / L * o); } ctx.strokeStyle = '#ffd23f'; ctx.lineWidth = 1.5; ctx.stroke(); } label(ctx, 24, 120, `wag ${E.dog.p.wag.toFixed(2)} · ear ${E.dog.p.ear.toFixed(2)}`, { size: 13 }); }
  });
  add(42, 'a neural layered puppet: few-shot structure', 'The structure a model would infer from a few drawings: each part segmented and labelled, the dog as a graph of named regions.', {
    after(ctx, E) { const seen = {}; parts(E).forEach((p, i) => { const g = p.name.split('.')[1].replace(/Far|Near/, ''); const hue = { body: 30, chest: 50, neck: 90, skull: 200, snout: 220, ear: 280, earFar: 300, tail: 0, tailTip: 0 }[g] ?? (g.startsWith('fore') ? 140 : 170);
      ctx.fillStyle = hsl(hue, 70, 55, .7); ctx.fill(P(p.pts)); if (!seen[g]) { seen[g] = 1; const c = cen(p.pts); label(ctx, c[0], c[1], g, { size: 10 }); } }); }
  });
  add(43, 'collage graph rewriting', 'The dog as a graph of parts, and a rewriting rule that changes its identity: head ↦ door, so when the dog refuses, it closes itself.', { still: 4.4,
    after(ctx, E) { fillParts(ctx, E, 'dog.', p => hsl({ body: 30, chest: 30, neck: 120, skull: 200, snout: 200, ear: 200, earFar: 200, tail: 300 }[p.name.split('.')[1]] ?? 60, 80, 55, .55), '#fff', 1); const ns = ['dog.head', 'dog.neck', 'dog.shoulder', 'dog.hip', 'dog.tailRoot'].map(n => J(E, n)); for (let i = 0; i < ns.length - 1; i++) line(ctx, ns[i], ns[i + 1], '#fff', 2); ns.forEach(n => dot(ctx, n, 6, '#fff'));
      const on = E.d.state === 'refuse'; ctx.fillStyle = 'rgba(14,12,10,.85)'; ctx.fillRect(980, 110, 250, 70); label(ctx, 992, 140, 'rule: head ↦ door', { bg: false, size: 14, c: on ? '#d42a1e' : '#fbf7ee' }); label(ctx, 992, 166, on ? 'applied: the dog refuses' : 'waiting for: refuse', { bg: false, size: 12 });
      if (on) { const h = ns[0]; ctx.fillStyle = '#6b2c22'; ctx.fillRect(h[0] - 18, h[1] - 30, 36, 56); ctx.strokeStyle = '#fff'; ctx.strokeRect(h[0] - 18, h[1] - 30, 36, 56); } }
  });
  add(44, 'multiplane parallax', 'The set separated into planes at different depths, each moving at its own rate as the camera drifts: the dog\'s plane is the one in focus.', {
    cam: E => ({ x: 1.3 + .45 * Math.sin(E.t * .5), y: 0, zoom: 1.15 }),
    after(ctx, E) { ctx.save(); ctx.fillStyle = 'rgba(14,30,20,.75)'; const o = Math.sin(E.t * .5) * 140; for (let i = 0; i < 7; i++) { ctx.beginPath(); ctx.ellipse(((i * 230 - o * 2.2) % 1500 + 1500) % 1500 - 100, 690, 90, 120, .3, 0, 7); ctx.fill(); }
      ['plane 4 · sky ×0.2', 'plane 3 · house ×1', 'plane 2 · dog ×1', 'plane 1 · leaves ×2.2'].forEach((s, i) => label(ctx, 1010, 120 + i * 24, s, { size: 12 })); ctx.restore(); }
  });
  add(45, 'occlusion: who is in front?', 'The draw order made visible: the far legs, the body, the near legs, the jamb drawn over the dog\'s back, each numbered by depth.', {
    after(ctx, E) { const ps = parts(E); ps.forEach((p, i) => { const c = cen(p.pts); ctx.strokeStyle = hsl(i * 15, 80, 60); ctx.lineWidth = 1.5; ctx.stroke(P(p.pts)); if (i % 2 === 0) label(ctx, c[0] - 6, c[1] + 4, String(i + 1), { size: 10 }); });
      label(ctx, 24, 120, `${ps.length} pieces · back to front · the jamb last when the dog is on the sill`, { size: 13 }); }
  });
  add(46, 'face landmark registration', 'The dog\'s face is covered in numbered landmarks and a mesh between them, registered point for point to the person\'s, the anatomy a recasting needs.', {
    after(ctx, E) { ctx.save(); ctx.globalCompositeOperation = 'multiply'; fillParts(ctx, E, 'dog.', 'rgba(127,224,210,.55)'); ctx.restore(); for (const p of parts(E, 'dog.')) mesh(p.pts, 1).forEach(t => { ctx.strokeStyle = 'rgba(20,80,75,.6)'; ctx.lineWidth = .7; ctx.stroke(P(t)); }); const fp = parts(E).filter(p => /skull|snout|ear$/.test(p.name)).flatMap(p => p.pts.filter((_, i) => i % 2 === 0)); const pp = parts(E, 'person.head').flatMap(p => p.pts.filter((_, i) => i % 3 === 0));
      for (let i = 0; i < fp.length; i++) for (let j = i + 1; j < fp.length; j++) if (Math.hypot(fp[i][0] - fp[j][0], fp[i][1] - fp[j][1]) < 22) line(ctx, fp[i], fp[j], 'rgba(127,224,210,.6)', 1);
      fp.forEach((q, i) => { dot(ctx, q, 3.5, '#7fe0d2'); if (i % 4 === 0) label(ctx, q[0] + 4, q[1] - 4, String(i), { size: 9, bg: false, c: '#e9fffb' }); }); pp.forEach(q => dot(ctx, q, 2.5, '#7fe0d2'));
      for (const [a, b] of [['person.eye', 'dog.eye'], ['person.nose', 'dog.nose'], ['person.mouth', 'dog.mouth']]) line(ctx, J(E, a), J(E, b), 'rgba(127,224,210,.5)', 1, [5, 5]); label(ctx, 24, 120, `${fp.length} landmarks on the dog · ${pp.length} on the person`, { size: 13 }); }
  });
  add(47, 'sound to action', 'The voice drives the body: each call\'s waveform runs through the dog itself, and its ears and crouch answer it, a viseme for a dog.', { still: 1.4,
    after(ctx, E) { const vv = E.w.voice; fillParts(ctx, E, 'dog.', vv === 'call' ? 'rgba(255,46,46,.45)' : vv === 'soft' ? 'rgba(127,224,210,.4)' : 'rgba(14,12,10,.35)'); const v = E.w.voice, amp = v === 'call' ? 1 : v === 'soft' ? .4 : .05; const b = bbox(allPts(E, 'dog.')); ctx.save(); const clip = new Path2D(); for (const p of parts(E, 'dog.')) clip.addPath(P(p.pts)); ctx.clip(clip);
      for (let r = 0; r < 6; r++) { ctx.beginPath(); for (let x = b[0]; x < b[2]; x += 2) ctx.lineTo(x, (b[1] + b[3]) / 2 + (r - 2.5) * 10 + Math.sin(x * .25 + E.t * 30 + r) * 18 * amp * Math.sin((x - b[0]) / (b[2] - b[0]) * Math.PI)); ctx.strokeStyle = v === 'call' ? '#ff2e2e' : '#7fe0d2'; ctx.lineWidth = 2; ctx.stroke(); } ctx.restore();
      ctx.fillStyle = 'rgba(14,12,10,.85)'; ctx.fillRect(24, 100, 420, 54); ctx.beginPath(); for (let i = 0; i < 400; i++) ctx.lineTo(34 + i, 127 + Math.sin(i * .3 + E.t * 30) * 20 * amp * Math.sin(i / 400 * Math.PI)); ctx.strokeStyle = v === 'call' ? '#ff2e2e' : '#7fe0d2'; ctx.lineWidth = 2; ctx.stroke();
      label(ctx, 460, 133, `voice: ${v} → ears ${E.dog.p.ear.toFixed(2)} · crouch ${E.dog.p.crouch.toFixed(2)}`, { size: 13 }); }
  });
  add(48, 'characters that can refuse', 'The original swarm, the one PAE-00 was made with: the dog\'s state, its trust, and the guard that made its last choice.', { still: 3.8,
    after(ctx, E) { const tr = E.d.trust; fillParts(ctx, E, 'dog.', 'rgba(14,12,10,.55)'); { const all = bbox(allPts(E, 'dog.')); const lvl = all[3] - (all[3] - all[1]) * tr; ctx.save(); const cl = new Path2D(); for (const p of parts(E, 'dog.')) cl.addPath(P(p.pts)); ctx.clip(cl); ctx.fillStyle = tr > .6 ? 'rgba(15,143,128,.85)' : tr < .25 ? 'rgba(212,42,30,.85)' : 'rgba(200,138,0,.85)'; ctx.fillRect(all[0] - 5, lvl, all[2] - all[0] + 10, all[3] - lvl + 5); ctx.restore(); label(ctx, all[2] + 6, lvl, `trust ${tr.toFixed(2)}`, { size: 12 }); } stateChart(ctx, 860, 110, E.d.state); ctx.font = '500 13px "JetBrains Mono"'; const why = E.d.reason.length > 46 ? E.d.reason.slice(0, 46) + '…' : E.d.reason; label(ctx, 860, 236, why, { size: 12 }); }
  });

  // ===== Archives & Provenance
  add(49, 'open-content atelier', 'The dog photographed as a museum object: alone on a grey seamless, with a scale bar, a colour target and a catalogue label, offered as open content.', {
    bg(ctx, E) { const g = ctx.createRadialGradient(640, 420, 80, 640, 420, 800); g.addColorStop(0, '#d8d8d4'); g.addColorStop(1, '#8d8d89'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); return S.camera(E.cam, W, H); },
    style: () => ({ skip: n => !!n && n.startsWith('person.'), noBrads: false }),
    after(ctx, E) { ctx.save(); ctx.globalCompositeOperation = 'saturation'; fillParts(ctx, E, 'dog.', 'rgba(128,128,128,.7)'); ctx.restore(); fillParts(ctx, E, 'dog.', null, 'rgba(255,255,255,.9)', 2.5); const b = bbox(allPts(E, 'dog.')); const y = b[3] + 16; ctx.fillStyle = '#111'; for (let i = 0; i < 10; i++) ctx.fillRect(b[0] + i * 15, y, 15, 6 + (i % 2) * 0); for (let i = 0; i < 10; i += 2) { ctx.fillStyle = '#fff'; ctx.fillRect(b[0] + i * 15, y, 15, 6); }
      label(ctx, b[0], y + 22, '10 cm', { bg: false, size: 11, c: '#111' }); ['#735244', '#c29682', '#627a9d', '#576c43', '#8580b1', '#67bdaa', '#d67e2c', '#505ba6', '#c15a63', '#5e3c6c', '#9dbc40', '#e0a32e'].forEach((c, i) => { ctx.fillStyle = c; ctx.fillRect(1060 + (i % 6) * 26, 110 + Math.floor(i / 6) * 26, 24, 24); });
      ctx.fillStyle = '#efe6d2'; ctx.fillRect(1040, 180, 210, 70); ctx.fillStyle = '#14110d'; ctx.font = 'italic 400 15px Literata'; ctx.fillText('Dog at a Threshold, 2026', 1050, 204); ctx.font = '400 11px "JetBrains Mono"'; ctx.fillText('cut paper, brass brads · Bolas', 1050, 222); ctx.fillText('CC0 · open content', 1050, 240); }
  });
  add(50, 'a historical print stage', 'The dog printed the way the archive holds it: a halftone screen on newsprint, the dot doing the work the paper texture did.', {
    style: () => ({ fill: c => grey(c), noTex: true, edge: '#111' }),
    after(ctx, E) { ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = '#efe4c8'; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = 'source-over'; for (const p of parts(E)) { ctx.save(); ctx.clip(P(p.pts)); const b = bbox(p.pts); for (let x = b[0]; x < b[2]; x += 6) for (let y = b[1]; y < b[3]; y += 6) dot(ctx, [x + (y % 12 ? 3 : 0), y], 1.6, 'rgba(0,0,0,.55)'); ctx.restore(); } ctx.restore(); }
  });
  add(51, 'montage research', 'The dog\'s history as a montage: frames of its earlier choices strobe behind it, a collection read at speed.', {
    after(ctx, E) { fillParts(ctx, E, 'dog.', hsl((Math.floor(E.t * 8) * 47) % 360, 75, 55, .6)); const hist = E.mem.mont = E.mem.mont || []; if (Math.floor(E.t * 4) !== E.mem.mk) { E.mem.mk = Math.floor(E.t * 4); hist.push(parts(E).map(p => p.pts)); if (hist.length > 7) hist.shift(); }
      hist.forEach((h, i) => { ctx.save(); ctx.translate(-(hist.length - i) * 40, -(hist.length - i) * 6); ctx.globalAlpha = .12 + i * .04; ctx.fillStyle = hsl(i * 50, 60, 50); for (const pts of h) ctx.fill(P(pts)); ctx.restore(); }); }
  });
  add(52, 'reconstruct the method', 'The workbench behind the trick: the dog\'s parts laid out loose beside it, pinned and labelled, so the method can be rebuilt from them.', {
    after(ctx, E) { for (const p of parts(E, 'dog.')) { ctx.strokeStyle = '#d42a1e'; ctx.lineWidth = 2; ctx.setLineDash([5, 4]); ctx.stroke(P(p.pts)); ctx.setLineDash([]); ctx.fillStyle = 'rgba(239,230,210,.55)'; ctx.fill(P(p.pts)); dot(ctx, cen(p.pts), 3, '#d42a1e'); } ctx.fillStyle = 'rgba(239,230,210,.94)'; ctx.fillRect(820, 90, 430, 260); const ps = parts(E).filter(p => !/Far/.test(p.name)).slice(0, 12);
      ps.forEach((p, i) => { const b = bbox(p.pts), c = cen(p.pts), x = 860 + (i % 4) * 100, y = 140 + Math.floor(i / 4) * 75; ctx.save(); const k = Math.min(1, 60 / Math.max(b[2] - b[0], b[3] - b[1])); ctx.translate(x, y); ctx.scale(k, k); ctx.translate(-c[0], -c[1]);
        ctx.fillStyle = p.color; ctx.fill(P(p.pts)); ctx.strokeStyle = '#14110d'; ctx.lineWidth = 1 / k; ctx.stroke(P(p.pts)); ctx.restore(); dot(ctx, [x, y - 26], 3, '#d42a1e'); label(ctx, x - 30, y + 34, p.name.replace('dog.', ''), { bg: false, size: 10, c: '#14110d' }); }); }
  });
  add(53, 'civic footage performer', 'The dog performs inside archive footage: 16 mm grain, gate weave and sprocket holes, as if found in a city\'s film collection.', {
    style: () => ({ fill: c => grey(c) }),
    after(ctx, E) { ctx.save(); ctx.globalCompositeOperation = 'luminosity'; fillParts(ctx, E, 'dog.', 'rgba(40,40,40,.6)'); ctx.restore(); ctx.save(); ctx.globalCompositeOperation = 'color'; ctx.fillStyle = 'rgba(150,120,70,.8)'; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = 'source-over'; grain(ctx, .25, Math.floor(E.t * 24));
      ctx.fillStyle = '#0a0806'; ctx.fillRect(0, 0, 60, H); ctx.fillRect(W - 60, 0, 60, H); for (let y = (E.t * 400) % 80 - 80; y < H; y += 80) { ctx.fillStyle = '#d8d0c0'; ctx.fillRect(16, y, 28, 40); ctx.fillRect(W - 44, y, 28, 40); } ctx.restore(); }
  });
  add(54, 'a provenance graph', 'Every piece of the dog traced to where it came from: a hash for each part, linked back to the one source file and the operation that made it.', {
    after(ctx, E) { ctx.fillStyle = 'rgba(14,12,10,.88)'; ctx.fillRect(960, 100, 290, 70); label(ctx, 972, 128, 'source: stage.js @ 4585ee7', { bg: false, size: 12, c: '#7fe0d2' }); label(ctx, 972, 152, 'op: cut(), seed per part', { bg: false, size: 12 });
      const src = [1100, 170]; parts(E).filter(p => !/Far/.test(p.name)).slice(0, 9).forEach((p, i) => { const c = cen(p.pts); let h = 0; for (const ch of p.name) h = (h * 31 + ch.charCodeAt(0)) >>> 0; line(ctx, src, c, 'rgba(127,224,210,.5)', 1); dot(ctx, c, 4, '#7fe0d2'); label(ctx, c[0] + 6, c[1] - 6, h.toString(16).slice(0, 6), { size: 10 }); }); }
  });

  // ------------------------------------------------------------------ the runner: one machine, one loop, any lens
  function make(canvas, opts) {
    const ctx = canvas.getContext('2d'); opts = opts || {};
    let d, w, k, dog, per, door, t, mem, segs;
    const reset = () => { d = M.create(); w = Object.assign({}, M.WORLD); k = 0; dog = new S.DogAnim(); per = new S.PersonAnim(); door = 0; t = 0; mem = {}; segs = []; };
    reset();
    const step = () => {
      while (k < TL.length && TL[k][0] <= t + 1e-9) { Object.assign(w, TL[k][1]); k++; }
      M.step(d, w, 1 / FPS);
      if (!segs.length || segs[segs.length - 1].s !== d.state) segs.push({ s: d.state, a: t, b: t }); else segs[segs.length - 1].b = t;
      dog.update({ state: d.state, x: d.x, v: d.v, face: d.face, trust: d.trust, heard: d.t - d.heard }, 1 / FPS);
      per.update({ x: M.PERSON_X[w.place], sit: w.posture === 'sit' ? 1 : 0, reach: w.hand === 'reach' ? 1 : 0, low: w.hand === 'low' ? 1 : 0, mouth: w.voice === 'call' ? .9 : w.voice === 'soft' ? .35 : 0 }, 1 / FPS);
      door += ((w.door === 'open' ? 1 : 0) - door) * .08; t += 1 / FPS;
    };
    function draw(li, T) {
      T = ((T % LOOP) + LOOP) % LOOP; if (T < t - 1e-6) reset(); while (t < T - 1e-6) step();
      const lens = L[li]; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.clearRect(0, 0, W, H);
      mem.segs = segs;
      const span = d.x - per.x + 2.4, E = { t, d, w, dog, per, door, mem, rec: S.REC, cam: { x: (d.x + per.x) / 2 + .15, y: 0, zoom: clamp(8.4 / span, 1.15, 2.1) } };   // frames the person and the dog, closer as they come together
      if (lens.cam) E.cam = lens.cam(E);
      for (const key in S.STYLE) delete S.STYLE[key];
      const st = lens.style ? lens.style(E) : null;
      const K = lens.bg ? lens.bg(ctx, E) : SET(ctx, E); E.K = K;
      if (lens.under) lens.under(ctx, E, K);
      if (st) Object.assign(S.STYLE, st);
      S.REC.on = true; S.REC.parts = []; S.REC.joints = {}; S.REC.n = '';
      S.puppet(ctx, K, per.x, 1, 1, g => S.drawPerson(g, per.p), lens.bg ? 0 : .32);
      const turn = Math.abs(dog.p.turn) < .06 ? .06 * Math.sign(dog.p.turn || 1) : dog.p.turn;
      S.puppet(ctx, K, d.x, turn, 1, g => S.drawDog(g, dog.p, t), lens.bg ? 0 : .34);
      if (d.x < .9 && !lens.bg) S.jamb(ctx, K);
      S.REC.on = false; for (const key in S.STYLE) delete S.STYLE[key];
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      if (lens.after) lens.after(ctx, E, K);
      if (opts.caption !== false) caption(ctx, lens, E);
      return E;
    }
    return { draw, reset, get t() { return t; } };
  }
  function caption(ctx, lens, E) {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = 'rgba(14,12,10,.86)'; ctx.fillRect(0, 0, W, 84);
    ctx.font = '600 15px "JetBrains Mono"'; ctx.fillStyle = '#ff7a6b'; ctx.fillText(`SCION ${String(lens.id).padStart(2, '0')} · ${SW[lens.id - 1] ? SW[lens.id - 1].family.toUpperCase() : ''}`, 24, 30);
    ctx.font = '900 34px "Big Shoulders Display"'; ctx.fillStyle = '#fbf7ee'; ctx.fillText(SW[lens.id - 1] ? SW[lens.id - 1].title.split(' — ')[0].toUpperCase() : '', 24, 70);
    ctx.font = '400 16px "JetBrains Mono"'; ctx.fillStyle = 'rgba(251,247,238,.75)'; ctx.textAlign = 'right'; ctx.fillText(lens.look, W - 24, 70); ctx.textAlign = 'left';
    const pr = [...PROMPT].reverse().find(p => E.t >= p[0]); if (pr && pr[1]) { ctx.fillStyle = 'rgba(14,12,10,.8)'; ctx.fillRect(0, H - 44, W, 44); ctx.font = '600 18px "JetBrains Mono"'; ctx.fillStyle = '#d42a1e'; ctx.fillText('›', 24, H - 16); ctx.fillStyle = '#fbf7ee'; ctx.fillText(pr[1], 46, H - 16); }
    ctx.restore();
  }
  let SW = root.SWARMS || [];
  root.Scion = { TL, PROMPT, LENSES: L, LOOP, W, H, make, setSwarms: s => { SW = s; } };
})(typeof window !== 'undefined' ? window : globalThis);
