// MEMORY · O · OGIVA — SCION 26 · PixiJS, Archive Stage Rendering Engine
// Ogiva remembers in reflections. The remembered stills are TEXTURES; each memory is a mirror SHARD:
// a Container with a polygon ALPHA MASK, its content rendered to a RENDER TEXTURE and passed through a
// FILTER STAGE chosen by the feeling (grudge = cold high-contrast etch, fear = dark tremor + displacement,
// desire = rose bloom, pride = gilt and bright, guilt = frosted and turned away, debt = sepia, witness = keyhole slit).
// Shards are cut from the vanity mirror by half-plane clipping (invariant: shard areas sum to the mirror area).
// Each shard has a wig on a stand: a different self that saw it. Belief (PLoT) = the other's etched silhouette
// in the strongest shard growing/shrinking from prior to posterior strength, blurred by uncertainty, shadowed by danger.
(function () {
  const W = 1920, H = 1080;
  const cl = (a, b, x) => Math.max(a, Math.min(b, x));
  const sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u); };
  const lerp = (a, b, u) => a + (b - a) * u;
  const sig = x => 1 / (1 + Math.exp(-x));
  const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const WIG = '#7a3b8f';
  const CAST = { R: { w: 168, h: 122, fill: '#d6bf96' }, B: { w: 244, h: 214, fill: '#e8d5ae' }, I: { w: 128, h: 98, fill: '#e2cea5' }, O: { w: 80, h: 184, fill: '#f0e4c8' } };

  // ---------------- render textures (scratch pool; always fully overwritten, so output is a pure function of t) ----------------
  const POOL = {}, KEYS = {};
  function RT(id, w, h) {
    w = Math.max(2, Math.ceil(w)); h = Math.max(2, Math.ceil(h));
    let c = POOL[id];
    if (!c) { c = document.createElement('canvas'); POOL[id] = c; }
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; } KEYS[id] = null;
    const x = c.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.filter = 'none';
    x.clearRect(0, 0, w, h); return c;
  }
  // ---------------- filter stages (operate on a render texture in pixel space) ----------------
  const F = {
    css(rt, s) { if (!s) return; const tmp = RT('_tmp', rt.width, rt.height), q = tmp.getContext('2d'); q.filter = s; q.drawImage(rt, 0, 0); q.filter = 'none'; const x = rt.getContext('2d'); x.clearRect(0, 0, rt.width, rt.height); x.drawImage(tmp, 0, 0); },
    tint(rt, col, a) { if (a <= 0) return; const x = rt.getContext('2d'); x.save(); x.globalCompositeOperation = 'source-atop'; x.globalAlpha = a; x.fillStyle = col; x.fillRect(0, 0, rt.width, rt.height); x.restore(); },
    bloom(rt, px, a) { if (a <= 0) return; const tmp = RT('_tmp', rt.width, rt.height), q = tmp.getContext('2d'); q.filter = `blur(${px}px) brightness(1.3)`; q.drawImage(rt, 0, 0); q.filter = 'none'; const x = rt.getContext('2d'); x.save(); x.globalCompositeOperation = 'lighter'; x.globalAlpha = a; x.drawImage(tmp, 0, 0); x.restore(); },
    displace(rt, amp, seed) { // horizontal band displacement (a cracked-glass shiver)
      if (amp < .3) return; const tmp = RT('_tmp', rt.width, rt.height), q = tmp.getContext('2d'); q.drawImage(rt, 0, 0);
      const x = rt.getContext('2d'); x.clearRect(0, 0, rt.width, rt.height); const n = 14, bh = rt.height / n;
      for (let i = 0; i < n; i++) { const dx = (hash(seed + i * 7.3) - .5) * 2 * amp; x.drawImage(tmp, 0, i * bh, rt.width, bh + 1, dx, i * bh, rt.width, bh + 1); }
    },
    focus(rt, cx, cy, r, dark) { // vignette whose clear centre is the thing the feeling looks at
      const x = rt.getContext('2d'); const gr = x.createRadialGradient(cx, cy, r * .35, cx, cy, r * 1.6);
      gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, `rgba(5,2,10,${dark})`); x.save(); x.globalCompositeOperation = 'source-atop'; x.fillStyle = gr; x.fillRect(0, 0, rt.width, rt.height); x.restore();
    },
    slit(rt, cx, wd) { const x = rt.getContext('2d'); x.save(); x.globalCompositeOperation = 'destination-in'; const gr = x.createLinearGradient(cx - wd, 0, cx + wd, 0); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(.3, 'rgba(0,0,0,1)'); gr.addColorStop(.7, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); x.fillStyle = gr; x.fillRect(0, 0, rt.width, rt.height); x.restore(); }
  };
  // feeling -> filter stage recipe
  const FEEL = {
    grudge: { css: 'grayscale(1) contrast(1.8) brightness(1.08)', tint: ['#86c8ff', .30], wig: '#4f4fa8', edge: '#dff3ff', note: [88, 89, 95] },
    fear: { css: 'saturate(.5) brightness(1.6) contrast(1.25)', tint: ['#7a1850', .2], wig: '#3a1f4a', edge: '#b07ab8', note: [69, 70, 76] },
    desire: { css: 'sepia(.35) saturate(1.5) hue-rotate(-18deg) brightness(1.15)', tint: ['#ff8fb0', .16], wig: '#c0508a', edge: '#ffd2e2', note: [81, 85, 88] },
    pride: { css: 'saturate(1.35) brightness(1.22) contrast(1.12)', tint: ['#ffd27a', .12], wig: '#a24ad0', edge: '#ffe39a', note: [81, 88, 93] },
    guilt: { css: 'blur(5px) grayscale(.7) brightness(1.25)', tint: ['#e8e4f0', .34], wig: '#8d8398', edge: '#ffffff', note: [76, 79, 83] },
    debt: { css: 'sepia(.9) brightness(1.15) contrast(1.15)', tint: ['#6b4a1f', .18], wig: '#7a4f62', edge: '#e6c48a', note: [74, 77, 81] },
    witness: { css: 'grayscale(1) brightness(1.1)', tint: ['#9fb0c8', .12], wig: '#b9b2c6', edge: '#c8d0dc', note: [86, 93, 98] }
  };
  const FKEYS = ['grudge', 'fear', 'desire', 'pride', 'guilt', 'debt'];
  function feelOf(m, st) {
    if (m.role === 'witness') return { kind: 'witness', amt: .35, f: {} };
    const R = (window.LEDGER && LEDGER.RULE[m.deed]) || {};
    const rule = m.role === 'doer' ? (R.mindA || {}) : (R.mindV || {});
    const mind = (st && st.mind && st.mind.O && st.mind.O[m.other]) || {};
    const f = {}; let best = 'grudge', bv = -1;
    for (const k of FKEYS) { const v = (rule[k] ? (mind[k] || 0) * (.5 + rule[k]) : 0); f[k] = v; if (v > bv) { bv = v; best = k; } }
    if (bv <= .02) best = m.role === 'doer' ? 'pride' : 'grudge';
    return { kind: best, amt: cl(.25, 1, bv), f };
  }

  // ---------------- scene graph: containers with transform, alpha, mask and filters ----------------
  function render(g, n) {
    if (!n || n.a <= .003) return;
    g.save(); g.translate(n.x || 0, n.y || 0); if (n.r) g.rotate(n.r); g.scale(n.sx ?? 1, n.sy ?? 1); g.globalAlpha *= (n.a ?? 1);
    if (n.mask) { g.beginPath(); n.mask(g); g.clip(); }
    if (n.rt) { // render-texture pass: draw subtree into RT over local box, run filter stages, composite back
      const b = n.rt.box, res = n.rt.res || .6; let rt = n.rt.key && KEYS[n.rt.id] === n.rt.key ? POOL[n.rt.id] : null;
      if (!rt) {
        rt = RT(n.rt.id, b.w * res, b.h * res); const x = rt.getContext('2d');
        x.setTransform(res, 0, 0, res, -b.x * res, -b.y * res); if (n.draw) n.draw(x); for (const k of n.kids || []) render(x, k);
        x.setTransform(1, 0, 0, 1, 0, 0); for (const st of n.rt.stages || []) st(rt, res); KEYS[n.rt.id] = n.rt.key;
      }
      const sv = n.rt.shiver;
      if (sv && sv.amp > .3) { const nb = 14, bh = rt.height / nb; for (let i = 0; i < nb; i++) { const dx = (hash(sv.seed + i * 7.3) - .5) * 2 * sv.amp; g.drawImage(rt, 0, i * bh, rt.width, bh + 1, b.x + dx, b.y + i * bh / res, b.w, (bh + 1) / res); } }
      else g.drawImage(rt, b.x, b.y, b.w, b.h);
    } else { if (n.draw) n.draw(g); for (const k of n.kids || []) render(g, k); }
    if (n.over) n.over(g);
    g.restore();
  }
  // ---------------- geometry: half-plane polygon clip (mirror cracking) ----------------
  function clipHalf(P, nx, ny, d) { const o = []; for (let i = 0; i < P.length; i++) { const a = P[i], b = P[(i + 1) % P.length]; const da = a[0] * nx + a[1] * ny - d, db = b[0] * nx + b[1] * ny - d; if (da <= 0) o.push(a); if ((da < 0) !== (db < 0)) { const u = da / (da - db); o.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]); } } return o; }
  const area = P => { let s = 0; for (let i = 0; i < P.length; i++) { const a = P[i], b = P[(i + 1) % P.length]; s += a[0] * b[1] - b[0] * a[1]; } return Math.abs(s) / 2; };
  const cen = P => { let x = 0, y = 0; for (const p of P) { x += p[0]; y += p[1]; } return [x / P.length, y / P.length]; };
  const bbox = P => { let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; for (const p of P) { x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]); x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]); } return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 }; };
  function crack(rect, n, seed) { // cut the largest piece through its centroid at a hashed angle until n pieces
    let pcs = [[[rect.x, rect.y], [rect.x + rect.w, rect.y], [rect.x + rect.w, rect.y + rect.h], [rect.x, rect.y + rect.h]]];
    for (let i = 1; i < n; i++) {
      pcs.sort((a, b) => area(b) - area(a)); const P = pcs.shift(), c = cen(P), bb = bbox(P);
      const base = bb.w > bb.h ? 0 : Math.PI / 2, ang = base + (hash(seed + i * 3.7) - .5) * .7;
      const nx = Math.cos(ang), ny = Math.sin(ang), d = c[0] * nx + c[1] * ny + (hash(seed + i * 9.1) - .5) * 40;
      pcs.push(clipHalf(P, nx, ny, d), clipHalf(P, -nx, -ny, -d));
    }
    return pcs.sort((a, b) => area(b) - area(a));
  }
  const poly = (g, P, ox = 0, oy = 0) => { g.moveTo(P[0][0] - ox, P[0][1] - oy); for (let i = 1; i < P.length; i++) g.lineTo(P[i][0] - ox, P[i][1] - oy); g.closePath(); };

  // ---------------- the sacks as drawn silhouettes ----------------
  function greyMix(hex, gr) { const n = parseInt(hex.slice(1), 16); let r = n >> 16, g2 = (n >> 8) & 255, b = n & 255; const y = .3 * r + .59 * g2 + .11 * b; r = lerp(r, y, gr); g2 = lerp(g2, y, gr); b = lerp(b, y, gr); return `rgb(${r | 0},${g2 | 0},${b | 0})`; }
  function sackPath(g, w, h, earUp, lean) { // origin at bottom-centre
    const hw = w / 2, e = h * .13 * earUp;
    g.moveTo(-hw, 0); g.quadraticCurveTo(-hw - w * .05, -h * .5, -hw + lean, -h); g.lineTo(-hw + lean - w * .06, -h - e);
    g.quadraticCurveTo(lean, -h + h * .05, hw + lean + w * .06, -h - e); g.lineTo(hw + lean, -h);
    g.quadraticCurveTo(hw + w * .05, -h * .5, hw, 0); g.closePath();
  }
  // Ogiva (and anyone) drawn at scale; o = {s, lean, ear, grey, wig, body tags, sx}
  function drawSack(g, who, x, y, o) {
    const C = CAST[who], s = o.s || 1, w = C.w * s * (o.sx ?? 1), h = C.h * s * (o.emptied ? .82 : 1), lean = (o.lean || 0) * s;
    g.save(); g.translate(x, y);
    const gr = o.grey || 0;
    if (o.etch) { // etched-glass outline (belief silhouettes)
      g.beginPath(); sackPath(g, w, h, who === 'I' ? -.5 : 1, 0); g.fillStyle = o.etch; g.fill(); g.lineWidth = o.lw || 3; g.strokeStyle = o.edge || '#fff'; g.stroke();
      g.lineWidth = Math.max(4, h * .07); g.strokeStyle = o.edge || '#fff';
      if (who === 'R') { g.beginPath(); g.moveTo(-w * .5, -h * .83); g.lineTo(w * .5, -h * .83); g.stroke(); }
      if (who === 'B') { g.beginPath(); g.moveTo(-w * .52, -h * .4); g.lineTo(w * .52, -h * .4); g.stroke(); g.lineWidth = 3; g.beginPath(); g.arc(0, -h * .7, h * .12, 0, 7); g.stroke(); }
      if (who === 'I') { g.lineWidth = 6; g.beginPath(); g.moveTo(-w * .5, -h * .95); g.quadraticCurveTo(-w * .7, -h * .5, -w * .62, -h * .15); g.moveTo(w * .5, -h * .95); g.quadraticCurveTo(w * .7, -h * .5, w * .62, -h * .15); g.stroke(); }
      if (who === 'O') { g.lineWidth = 7; g.beginPath(); g.moveTo(-w * .62, -h * .45); g.lineTo(-w * .6, -h * 1.05); g.lineTo(w * .6, -h * 1.05); g.lineTo(w * .62, -h * .45); g.stroke(); }
      g.restore(); return;
    }
    // body
    g.beginPath(); sackPath(g, w, h, o.ear ?? 1, lean);
    const gd = g.createLinearGradient(-w / 2, 0, w / 2, 0); gd.addColorStop(0, greyMix('#cdb68f', gr)); gd.addColorStop(.55, greyMix(C.fill, gr)); gd.addColorStop(1, greyMix('#bfa77f', gr));
    g.fillStyle = gd; g.fill(); g.lineWidth = 3 * Math.min(1.5, s); g.strokeStyle = '#2b2030'; g.stroke();
    // weave lines
    g.save(); g.clip(); g.globalAlpha = .18; g.strokeStyle = '#6b5638'; g.lineWidth = 1.2; for (let i = 1; i < 9; i++) { g.beginPath(); g.moveTo(-w, -h * i / 9); g.lineTo(w, -h * i / 9 - w * .05); g.stroke(); } g.restore();
    const tags = o.tags || [];
    if (tags.includes('cinched')) { g.strokeStyle = '#3a2a20'; g.lineWidth = 5 * s; g.beginPath(); g.moveTo(-w * .42, -h * .86); g.lineTo(w * .42 + lean, -h * .86); g.stroke(); }
    if (tags.includes('rope')) { g.strokeStyle = '#a08250'; g.lineWidth = 5 * s; for (const f of [.3, .62]) { g.beginPath(); g.moveTo(-w * .56, -h * f); g.quadraticCurveTo(0, -h * f + 8 * s, w * .56 + lean * f, -h * f); g.stroke(); } }
    if (tags.includes('torn')) { g.strokeStyle = '#2b2030'; g.lineWidth = 2.5 * s; g.beginPath(); for (let i = 0; i < 6; i++) g.lineTo(w * .1 + (i % 2 ? 6 : -6) * s, -h * (.35 + i * .05)); g.stroke(); g.fillStyle = 'rgba(251,247,238,.8)'; for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(w * .12 + (hash(i) - .5) * 14 * s, -h * .3 + hash(i + 3) * 18 * s, 2.2 * s, 0, 7); g.fill(); } }
    if (tags.includes('blot')) { g.fillStyle = '#141020'; g.beginPath(); g.ellipse(-w * .12, -h * .52, w * .16, w * .12, .4, 0, 7); g.fill(); }
    if (tags.includes('tag')) { g.fillStyle = '#efe6cf'; g.strokeStyle = '#2b2030'; g.lineWidth = 1.5; g.fillRect(w * .05, -h * .7, w * .32, w * .2); g.strokeRect(w * .05, -h * .7, w * .32, w * .2); }
    if (tags.includes('gag')) { g.fillStyle = '#8b7a66'; g.fillRect(-w * .52, -h * .78, w * 1.04 + lean * .2, h * .06); }
    // wig: long strands hanging past the shoulders (Ogiva's attribute)
    if (who === 'O' && !o.noWig) {
      const wc = greyMix(o.wig || WIG, gr * .8), toss = o.toss || 0, droop = o.droop || 0;
      g.save(); g.translate(lean, -h);
      g.fillStyle = wc; g.strokeStyle = '#2a1030'; g.lineWidth = 2;
      g.beginPath(); g.moveTo(-w * .66, h * .02); g.quadraticCurveTo(-w * .5, -h * .26 + droop * h * .08, w * .05, -h * .17 + droop * h * .06); g.quadraticCurveTo(w * .55, -h * .24 + droop * h * .08, w * .68, h * .03);
      g.lineTo(w * .7 + toss * w * .3, h * (.55 + droop * .1)); g.lineTo(w * .42 + toss * w * .2, h * (.5 + droop * .1)); g.lineTo(w * .4, h * .1);
      g.lineTo(-w * .4, h * .1); g.lineTo(-w * .42 + toss * w * .1, h * (.52 + droop * .1)); g.lineTo(-w * .7 + toss * w * .2, h * (.58 + droop * .1)); g.closePath(); g.fill(); g.stroke();
      g.globalAlpha = .35; g.strokeStyle = '#d9a6ee'; g.lineWidth = 1.5; for (let i = 0; i < 5; i++) { const xx = -w * .55 + i * w * .27; g.beginPath(); g.moveTo(xx * .6, h * .0); g.lineTo(xx + toss * w * .2, h * .48); g.stroke(); }
      g.restore();
    }
    g.restore();
  }
  function wigStand(g, x, y, s, col, lit, empty) { // a bald head form on a stalk, wearing one remembered self's wig
    g.save(); g.translate(x, y);
    g.fillStyle = '#2a2230'; g.fillRect(-4 * s, -60 * s, 8 * s, 60 * s); g.fillRect(-22 * s, -6 * s, 44 * s, 6 * s);
    g.fillStyle = '#d8ccd8'; g.beginPath(); g.ellipse(0, -84 * s, 20 * s, 26 * s, 0, 0, 7); g.fill();
    if (!empty) { g.fillStyle = col; g.strokeStyle = '#1a0c20'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(-24 * s, -84 * s); g.quadraticCurveTo(0, -128 * s, 24 * s, -84 * s); g.lineTo(28 * s, -40 * s); g.lineTo(14 * s, -44 * s); g.lineTo(12 * s, -76 * s); g.lineTo(-12 * s, -76 * s); g.lineTo(-14 * s, -44 * s); g.lineTo(-28 * s, -40 * s); g.closePath(); g.fill(); g.stroke(); }
    if (lit > 0) { g.globalCompositeOperation = 'lighter'; const gr = g.createRadialGradient(0, -84 * s, 4, 0, -84 * s, 70 * s); gr.addColorStop(0, `rgba(255,240,255,${.45 * lit})`); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(-80 * s, -170 * s, 160 * s, 170 * s); }
    g.restore();
  }

  // ---------------- textures from the remembered stills ----------------
  const MK = {};
  function marksOf(m, K) {
    const ck = m.deed + m.A + m.V; if (MK[ck]) return MK[ck];
    const D = window.DEEDS && DEEDS[m.deed]; let mk = null;
    try { if (D && D.marks) mk = D.marks(D.contact + .3, m.A, m.V, K); } catch (e) { mk = null; }
    if (!mk || !mk.A || !mk.V) mk = { A: { x: 500, y: 560, w: 260, h: 320 }, V: { x: 1150, y: 560, w: 260, h: 320 } };
    return (MK[ck] = mk);
  }
  function crops(m, K) { // her box, the other's box, and the union crop (texture frame) in still pixels
    const mk = marksOf(m, K); const me = m.role === 'doer' ? mk.A : m.role === 'victim' ? mk.V : null, ot = m.role === 'doer' ? mk.V : mk.A;
    const U = me ? { x0: Math.min(me.x, ot.x), y0: Math.min(me.y, ot.y), x1: Math.max(me.x + me.w, ot.x + ot.w), y1: Math.max(me.y + me.h, ot.y + ot.h) } : { x0: Math.min(mk.A.x, mk.V.x), y0: Math.min(mk.A.y, mk.V.y), x1: Math.max(mk.A.x + mk.A.w, mk.V.x + mk.V.w), y1: Math.max(mk.A.y + mk.A.h, mk.V.y + mk.V.h) };
    const p = 70; return { me, ot, frame: { x: U.x0 - p, y: U.y0 - p * 1.4, w: U.x1 - U.x0 + 2 * p, h: U.y1 - U.y0 + p * 2.4 } };
  }
  // draw texture frame cover-fit into box; returns the mapping so marks can be located inside
  function cover(g, tex, fr, box, zoom = 1, fx, fy) {
    const sc = Math.min(box.w / fr.w, box.h / fr.h) * 1.08 * zoom; const cx = fx ?? fr.x + fr.w / 2, cy = fy ?? fr.y + fr.h / 2;
    const ox = box.x + box.w / 2 - cx * sc, oy = box.y + box.h / 2 - cy * sc;
    if (tex && g) g.drawImage(tex, ox, oy, 1920 * sc, 1080 * sc);
    return (x, y) => [ox + x * sc, oy + y * sc];
  }
  // the memory layer of one shard: texture + feeling-specific marks, then the filter stages
  function memoryNode(m, fe, box, t, id, K, amt, extraOver, res) {
    const cr = crops(m, K), P = FEEL[fe.kind];
    const focusBox = (fe.kind === 'pride' || fe.kind === 'desire' || fe.kind === 'guilt') ? (cr.me || cr.ot) : cr.ot;
    let map = null;
    const zoom = fe.kind === 'pride' ? 1.15 : fe.kind === 'grudge' ? 1.08 : .95;
    // the texture frame is centred between the moment and herself: the memory is how she looked in it
    const fr = cr.frame, me = cr.me, fb = zoom > 1 && focusBox ? focusBox : me;
    const fx = fb ? lerp(fr.x + fr.w / 2, fb.x + fb.w / 2, .4) : undefined, fy = fb ? lerp(fr.y + fr.h / 2, fb.y + fb.h / 2, .3) : undefined;
    const age = m.ago || 0;
    // the static part (texture + filter stages) is a cached render texture keyed by everything it depends on;
    // only time-dependent work (fear shiver, grudge scoring) runs per frame
    map = cover(null, null, cr.frame, box, zoom, fx, fy);
    const key = [m.deed, m.A, m.V, m.k, fe.kind, amt.toFixed(2), age, box.w | 0, box.h | 0, res || .55].join('|');
    return {
      rt: {
        id, box, res: res || .55, key,
        shiver: fe.kind === 'fear' ? { amp: 12 * amt * (.5 + .5 * Math.sin(t * 23)), seed: Math.floor(t * 12) } : null,
        stages: [
          rt => F.css(rt, P.css + (age > 1 ? ` blur(${Math.min(1.2, (age - 1) * .15).toFixed(2)}px)` : '')),
          rt => F.tint(rt, P.tint[0], P.tint[1] * (.6 + amt * .6)),
          (rt, res) => { if (fe.kind === 'desire') F.bloom(rt, 6, .55); if (fe.kind === 'pride') F.bloom(rt, 4, .3); },
          (rt, res) => { if (focusBox) { const c = map(focusBox.x + focusBox.w / 2, focusBox.y + focusBox.h / 2); F.focus(rt, (c[0] - box.x) * res, (c[1] - box.y) * res, Math.max(focusBox.w, focusBox.h) * .9 * res * (box.w / cr.frame.w), fe.kind === 'fear' ? .45 : fe.kind === 'grudge' ? .45 : .3); } },
          (rt, res) => { if (fe.kind === 'witness') F.slit(rt, rt.width / 2, rt.width * .22); },
          rt => { if (age > 2) { const x = rt.getContext('2d'); x.save(); x.globalCompositeOperation = 'source-atop'; x.globalAlpha = Math.min(.55, (age - 2) * .07); x.fillStyle = '#20182a'; x.fillRect(0, 0, rt.width, rt.height); x.restore(); } }
        ]
      },
      draw(g) {
        g.fillStyle = '#0c0812'; g.fillRect(box.x, box.y, box.w, box.h);
        cover(g, m.still, cr.frame, box, zoom, fx, fy);
      },
      over(g) {
        if (fe.kind === 'grudge' && cr.ot) { // she has scored the other: exact etched lines across it, crisp over the filtered texture
          const a = map(cr.ot.x, cr.ot.y), b = map(cr.ot.x + cr.ot.w, cr.ot.y + cr.ot.h);
          g.save(); g.strokeStyle = 'rgba(240,250,255,.9)'; g.lineWidth = 2.2; g.beginPath();
          const n = 3 + Math.round(amt * 4), grow = sm(.0, .6, t);
          for (let i = 0; i < n; i++) { const u = hash(m.k * 13 + i), v = hash(m.k * 7 + i * 2.1); const x0 = lerp(a[0], b[0], u), y0 = lerp(a[1], b[1], v * .4); const x1 = lerp(a[0], b[0], 1 - v), y1 = lerp(a[1], b[1], .6 + u * .4); g.moveTo(x0, y0); g.lineTo(lerp(x0, x1, grow), lerp(y0, y1, grow)); }
          g.stroke(); g.restore();
        }
        if (extraOver) extraOver(g, map, cr);
      }
    };
  }

  // ---------------- belief (PLoT) silhouettes: her estimate of the other ----------------
  function beliefOf(L, k, st, other) {
    const pre = L && L.states[k] ? L.states[k].belief.O[other] : null, post = st && st.belief ? st.belief.O[other] : null;
    const sp = L && L.states[k] ? L.states[k].belief.O.O.str.m : -.4, so = st && st.belief ? st.belief.O.O.str.m : sp;
    return { pre: pre || { str: { m: 0, v: 1 }, harm: { m: 0, v: 1 } }, post: post || pre || { str: { m: 0, v: 1 }, harm: { m: 0, v: 1 } }, selfPre: sp, self: so };
  }
  function beliefGlyph(g, other, cx, floorY, unit, b, u, edge) { // her etched self (fixed) and the other sized by believed strength
    const str = lerp(b.pre.str.m, b.post.str.m, u), v = lerp(b.pre.str.v, b.post.str.v, u), harm = lerp(b.pre.harm.m, b.post.harm.m, u);
    const s = unit * (.45 + 1.1 * sig(str));
    const sSelf = unit * (.45 + 1.1 * sig(lerp(b.selfPre ?? -.4, b.self ?? -.4, u)));
    // danger: the other's shadow thrown long across the floor of the shard
    g.save(); g.globalAlpha = .55 * cl(0, 1, harm * 1.2); g.fillStyle = '#5a0f2a';
    g.beginPath(); g.moveTo(cx + 60 * unit, floorY); g.lineTo(cx + 60 * unit - CAST[other].w * s * (.8 + harm * 2.2), floorY - 6); g.lineTo(cx + 60 * unit - CAST[other].w * s * (.8 + harm * 2.2), floorY + 10 * unit); g.lineTo(cx + 60 * unit, floorY + 6); g.fill(); g.restore();
    drawSack(g, 'O', cx - 40 * unit - 40 * sSelf, floorY, { s: sSelf, etch: 'rgba(200,170,230,.2)', edge: '#e6c8ff' });
    blurredSack(g, other, cx + 60 * unit + CAST[other].w * s * .5, floorY, s, v * 4, cl(.55, 1, 1.2 - v * .5), edge);
    g.fillStyle = edge; g.globalAlpha = .7; g.fillRect(cx - 150 * unit, floorY, 300 * unit, 2);
    g.globalAlpha = 1;
  }

  // an etched silhouette rendered to its own texture and blurred there (filter stage), then composited
  function blurredSack(g, who, x, floor, s, blur, alpha, edge) {
    // fixed-size render texture (no per-frame reallocation); the figure is drawn into it at a reduced scale and composited back up
    const N = 360, ow = CAST[who].w * s * 1.4 + 80, oh = CAST[who].h * s * 1.4 + 80, k = Math.min(1, N / Math.max(ow, oh));
    const rt = RT('etch', N, N), q = rt.getContext('2d');
    drawSack(q, who, N / 2, N - 40 * k, { s: s * k, etch: 'rgba(225,240,255,.10)', edge, lw: 5 * k });
    if (blur * k > .3) F.css(rt, `blur(${Math.min(3, blur * .7 * k).toFixed(1)}px)`);
    g.save(); g.globalAlpha *= alpha; g.drawImage(rt, x - N / 2 / k, floor - (N - 40 * k) / k, N / k, N / k); g.restore();
  }
  function beliefMirror(g, other, b, u, pose, edge) {
    const str = lerp(b.pre.str.m, b.post.str.m, u), v = lerp(b.pre.str.v, b.post.str.v, u), harm = lerp(b.pre.harm.m, b.post.harm.m, u);
    const self = lerp(b.selfPre ?? -.4, b.self ?? -.4, u);
    const rs = pose.s * .78, f = (.45 + 1.1 * sig(str)) / (.45 + 1.1 * sig(self)), s = rs * .45 * f;
    const floor = MIR.y + MIR.h - 40, ow = CAST[other].w * s, x = 1300 - CAST.O.w * rs * .5 - 24 - ow / 2;
    { const dk = g.createLinearGradient(0, floor - CAST[other].h * s * 1.6, 0, floor); dk.addColorStop(0, 'rgba(8,5,14,0)'); dk.addColorStop(.4, 'rgba(8,5,14,.7)'); dk.addColorStop(1, 'rgba(8,5,14,.8)'); g.fillStyle = dk; g.fillRect(x - ow, floor - CAST[other].h * s * 1.6, ow * 2, CAST[other].h * s * 1.6 + 40); }
    // danger: its shadow thrown up the glass behind it, darker and longer with believed harm
    g.save(); g.globalAlpha = cl(0, .75, harm * .9); const sg = g.createLinearGradient(0, floor, 0, floor - 520); sg.addColorStop(0, 'rgba(70,8,40,.95)'); sg.addColorStop(1, 'rgba(70,8,40,0)'); g.fillStyle = sg;
    g.beginPath(); g.moveTo(x - ow * .5, floor); g.lineTo(x - ow * (.6 + harm * .6), floor - CAST[other].h * s * (1.2 + harm * 1.4)); g.lineTo(x + ow * (.6 + harm * .6), floor - CAST[other].h * s * (1.2 + harm * 1.4)); g.lineTo(x + ow * .5, floor); g.fill(); g.restore();
    // certainty: blur and opacity of the etched figure (uncertain = fogged, far)
    blurredSack(g, other, x, floor, s, v * 5, cl(.55, 1, 1.25 - v * .5), edge);
    g.save(); g.globalAlpha = .6; g.fillStyle = edge; g.fillRect(x - ow * .6, floor + 2, ow * 1.2, 3); g.restore();
  }
  // ---------------- room ----------------
  const MIR = { x: 820, y: 120, w: 700, h: 720 };
  function room(g, lv, t, dim) {
    const bg = g.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, '#160d1c'); bg.addColorStop(.85, '#0b0710'); bg.addColorStop(1, '#07050a'); g.fillStyle = bg; g.fillRect(0, 0, W, H);
    g.strokeStyle = 'rgba(120,90,140,.10)'; g.lineWidth = 2; for (let x = 60; x < W; x += 140) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 860); g.stroke(); }
    g.fillStyle = '#100a14'; g.fillRect(0, 930, W, 150);
    // vanity table
    g.fillStyle = '#2a1a22'; g.fillRect(740, 840, 1120, 30); g.fillStyle = '#1a1016'; g.fillRect(760, 870, 1080, 60);
    // mirror frame + bulbs (halo lever: the light finds her)
    g.fillStyle = '#2b1d2c'; g.fillRect(MIR.x - 34, MIR.y - 34, MIR.w + 68, MIR.h + 40);
    const lit = (.45 + .55 * cl(0, 1, lv.halo * 1.4)) * (1 - dim);
    for (let i = 0; i < 9; i++) for (const side of [0, 1]) {
      const x = side ? MIR.x + MIR.w + 17 : MIR.x - 17, y = MIR.y + 20 + i * (MIR.h - 40) / 8; const fl = lit * (.85 + .15 * Math.sin(t * 3 + i * 1.7 + side));
      const gr = g.createRadialGradient(x, y, 2, x, y, 46); gr.addColorStop(0, `rgba(255,236,200,${.95 * fl})`); gr.addColorStop(.25, `rgba(255,210,160,${.35 * fl})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = gr; g.fillRect(x - 46, y - 46, 92, 92); g.fillStyle = `rgba(255,245,225,${.4 + .6 * fl})`; g.beginPath(); g.arc(x, y, 9, 0, 7); g.fill();
    }
    const wash = g.createRadialGradient(1170, 520, 100, 1170, 520, 1100); wash.addColorStop(0, `rgba(255,220,190,${.10 * lit})`); wash.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = wash; g.fillRect(0, 0, W, H);
  }
  function reflection(g, lv, pose, alive, ghost) { // the mirror's present: dark glass with her (mirrored, further away)
    const gr = g.createLinearGradient(MIR.x, MIR.y, MIR.x + MIR.w, MIR.y + MIR.h); gr.addColorStop(0, '#2a2534'); gr.addColorStop(.5, '#17131f'); gr.addColorStop(1, '#221c2a'); g.fillStyle = gr; g.fillRect(MIR.x, MIR.y, MIR.w, MIR.h);
    g.fillStyle = 'rgba(40,26,34,.8)'; g.fillRect(MIR.x, MIR.y + MIR.h - 90, MIR.w, 90);
    if (alive || ghost) { g.save(); g.globalAlpha = alive ? .5 : .25 * ghost; g.translate(1300, 0); g.scale(-1, 1); drawSack(g, 'O', 0, MIR.y + MIR.h - 40, { ...pose, s: pose.s * .78, lean: -(pose.lean || 0) }); g.restore(); }
    g.save(); g.globalAlpha = .07; g.fillStyle = '#fff'; g.beginPath(); g.moveTo(MIR.x + 80, MIR.y); g.lineTo(MIR.x + 200, MIR.y); g.lineTo(MIR.x + 40, MIR.y + MIR.h); g.lineTo(MIR.x - 80, MIR.y + MIR.h); g.fill(); g.restore();
  }
  function herPose(lv, st, t, extra) {
    const tags = (st && st.body && st.body.O) || [];
    const shrink = cl(0, 1, lv.shrink), loom = cl(-1, 1, lv.loom);
    return Object.assign({
      s: 2.35 * (1 - shrink * .28) * (1 + Math.max(0, loom) * .12), lean: 10 + loom * 26, ear: 1 - shrink * 1.2, grey: cl(0, 1, lv.grey + (tags.includes('greyed') ? .6 : 0)),
      tags, emptied: tags.includes('emptied'), droop: shrink + (tags.includes('drowsy') ? .5 : 0), toss: 0
    }, extra || {});
  }
  function figure(g, x, pose, lv, t) {
    const sh = cl(0, 1.2, lv.shadow), len = 140 + sh * 520;
    g.save(); g.fillStyle = `rgba(0,0,0,${.35 + sh * .45})`; g.beginPath(); g.moveTo(x + 50, 930); g.lineTo(x - len, 948); g.lineTo(x - len - 30, 985); g.lineTo(x + 60, 945); g.fill(); g.restore();
    if (lv.halo > .05) { g.save(); g.globalCompositeOperation = 'lighter'; const cone = g.createLinearGradient(0, 0, 0, 930); cone.addColorStop(0, `rgba(255,230,255,0)`); cone.addColorStop(1, `rgba(255,225,245,${.16 * cl(0, 1, lv.halo)})`); g.fillStyle = cone; g.beginPath(); g.moveTo(x - 30, 0); g.lineTo(x + 30, 0); g.lineTo(x + 190, 940); g.lineTo(x - 190, 940); g.fill(); g.restore(); }
    g.save(); g.translate(x, 930); g.rotate((pose.rot || 0)); drawSack(g, 'O', 0, 0, pose); g.restore();
  }

  // ---------------- BEAT: alone before the vanity ----------------
  function beat(g, t, mems, st, K, X) {
    const L = X && X.ledger, lv = (st && st.levers && st.levers.O) || { loom: 0, weight: 0, tempo: 0, halo: .5, shadow: 0, shrink: 0, grey: 0 };
    const alive = !st || !st.alive || st.alive.O !== false;
    const ghost = st && st.myth && st.myth.O ? (st.myth.O.GHOST || 0) * 2 : 0;
    const T = t * (1 + cl(-.3, .5, lv.tempo) * .5); // tempo lever: crisper timing
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
    room(g, lv, t, alive ? 0 : .55);
    const top = mems.slice(0, 5); const fes = top.map(m => feelOf(m, st));
    const lead = top[0], lf = fes[0];
    // her motion: idle, the crack flinch, then the lead feeling's acting
    let rot = 0, sx = 1, toss = 0, lean = 0, jit = 0;
    const flinch = sm(.45, .55, T) * (1 - sm(.6, 1.0, T));
    if (lf) {
      const u = sm(.9, 1.5, T), a = lf.amt;
      if (lf.kind === 'grudge') { rot = .02 * u; lean = 18 * u; }                                // rigid, leans in, exact
      if (lf.kind === 'fear') { rot = -.08 * u * a; jit = 4 * u * a; lean = -20 * u; }           // recoils, trembles
      if (lf.kind === 'desire') { rot = Math.sin(T * 2.4) * .05 * u; toss = .4 * u; }           // sways
      if (lf.kind === 'pride') { toss = (.7 * Math.sin(Math.min(1, u) * Math.PI)) + .2 * u; rot = .03 * u; } // the wig toss
      if (lf.kind === 'guilt') { sx = 1 - .45 * u; rot = -.04 * u; }                             // turns edge-on, away
      if (lf.kind === 'debt') { rot = -.05 * u; lean = -6 * u; }
      if (lf.kind === 'witness') { lean = 12 * u; }
    } else { rot = Math.sin(T * 1.6) * .035; toss = .25 + .25 * Math.sin(T * 1.6); }
    const pose = herPose(lv, st, T, { rot: rot + flinch * -.03 + (jit ? (hash(Math.floor(T * 30)) - .5) * .02 * jit : 0), sx, toss, lean: herPose(lv, st, T).lean + lean });
    // mirror: the present reflection, then shards of the past
    const seed = (lead ? lead.k * 17 + lead.deed.length : 3) + top.length * 101 + (st ? st.k : 0) * 7;
    // the present reflection is rendered once per frame into a render texture and sampled by every shard
    const mirRT = RT('mirror', MIR.w * .7, MIR.h * .7); { const q = mirRT.getContext('2d'); q.setTransform(.7, 0, 0, .7, -MIR.x * .7, -MIR.y * .7); reflection(q, lv, pose, alive, ghost); }
    g.drawImage(mirRT, MIR.x, MIR.y, MIR.w, MIR.h);
    const cracked = sm(.42, .62, T);
    if (!alive) { deadBeat(g, t, st, L, K, X, ghost); g.restore(); return; }
    if (!top.length) { // at peace, or bored: the mirror stays whole; she preens
      wigRow(g, [], t, 0); figure(g, 470, pose, lv, T); g.restore(); return;
    }
    const pcs = crack(MIR, top.length + 1, seed);
    // the piece holding her present reflection stays "now"; the others take memories, biggest for strongest
    const nowIdx = pcs.findIndex(P => { const b = bbox(P); return 1200 > b.x && 1200 < b.x + b.w && 600 > b.y && 600 < b.y + b.h; });
    const order = pcs.map((P, i) => i).filter(i => i !== (nowIdx < 0 ? pcs.length - 1 : nowIdx));
    const lift = sm(1.0, 1.6, T); // the strongest shard lifts off the glass toward her
    const shards = [];
    order.forEach((pi, j) => {
      const m = top[j]; if (!m) return; const fe = fes[j], P = pcs[pi], c = cen(P), bb = bbox(P), amt = cl(.25, 1, m.weight);
      const appear = sm(.55 + j * .12, .95 + j * .12, T);
      const isLead = j === 0;
      let dx = (c[0] - 1170) * .03 * cracked, dy = (c[1] - 480) * .03 * cracked, r = (hash(seed + j) - .5) * .06 * cracked, s = 1, ssx = 1;
      if (isLead) { // pop: lift the shard out toward the room, enlarge, feeling-specific behaviour
        const tx = 1000 - c[0], ty = 330 - c[1]; dx += tx * lift; dy += ty * lift; s = lerp(1, Math.min(2.0, 540 / Math.max(bb.w, bb.h)), lift); r *= 1 - lift;
        if (fe.kind === 'fear') { dx += (hash(Math.floor(T * 40)) - .5) * 12 * lift; dy += (hash(Math.floor(T * 40) + 9) - .5) * 8 * lift; }
        if (fe.kind === 'desire') { r += Math.sin(T * 2.4) * .03 * lift; }
        if (fe.kind === 'guilt') { ssx = 1 - .55 * lift; }
        if (fe.kind === 'pride') { s *= 1 + .05 * Math.sin(T * 3) * lift; }
      }
      const box = { x: bb.x - c[0], y: bb.y - c[1], w: bb.w, h: bb.h };
      const node = memoryNode(m, fe, box, T - .6, 'sh' + j, K, amt, null, isLead ? 1.1 : .55);
      shards.push({ j, P, c, s, ssx, dx, dy, r, node, fe, appear, isLead, amt, m });
    });
    // shards behind lead first
    shards.sort((a, b) => (a.isLead ? 1 : 0) - (b.isLead ? 1 : 0));
    const drawShard = S => {
      const Pl = S.P.map(p => [p[0] - S.c[0], p[1] - S.c[1]]);
      if (S.isLead && lift > 0) { // a hard shadow under the lifted shard
        g.save(); g.globalAlpha = .3 * lift; g.fillStyle = '#000'; g.translate(S.c[0] + S.dx + 26, S.c[1] + S.dy + 30); g.rotate(S.r); g.scale(S.s * S.ssx, S.s); g.beginPath(); poly(g, Pl); g.fill(); g.restore();
      }
      // present reflection under the memory, cross-faded by `appear`
      render(g, {
        x: S.c[0] + S.dx, y: S.c[1] + S.dy, r: S.r, sx: S.s * S.ssx, sy: S.s, a: 1, mask: q => poly(q, Pl),
        draw(q) { q.drawImage(mirRT, MIR.x - S.c[0], MIR.y - S.c[1], MIR.w, MIR.h); },
        kids: [Object.assign(S.node, { a: S.appear * (S.isLead ? 1 : lerp(1, .7, lift)) })],
        over(q) { q.beginPath(); poly(q, Pl); q.lineWidth = (S.isLead ? 3 : 2) / S.s; q.strokeStyle = FEEL[S.fe.kind].edge; q.globalAlpha = .5 + .5 * cracked; q.stroke(); if (S.fe.kind === 'pride' && S.isLead) { q.lineWidth = 8 / S.s; q.strokeStyle = 'rgba(230,190,90,.85)'; q.stroke(); } }
      });
    };
    for (const S of shards) if (!S.isLead) drawShard(S);
    // crack lines on the glass (the impact)
    if (cracked > 0) { g.save(); g.strokeStyle = 'rgba(235,240,255,.7)'; g.lineWidth = 1.5; for (const P of pcs) { if (shards.some(S => S.isLead && S.P === P) && lift > .05) continue; g.globalAlpha = cracked * .8; g.beginPath(); poly(g, P); g.stroke(); } g.restore(); }
    // belief update (PLoT) in the present glass: beside her reflection stands the other, as big as she now believes it is
    if (L && lead) {
      const bu = sm(1.3, 2.2, T), b = beliefOf(L, lead.k, st, lead.other), ap = sm(1.0, 1.4, T);
      g.save(); g.beginPath(); g.rect(MIR.x, MIR.y, MIR.w, MIR.h); g.clip(); g.globalAlpha = ap;
      beliefMirror(g, lead.other, b, bu, pose, FEEL[lf.kind].edge); g.restore();
    }
    for (const S of shards) if (S.isLead) drawShard(S);
    wigRow(g, shards, T, lift);
    figure(g, 470, pose, lv, T);
    g.restore();
  }
  // one wig stand per remembered self, on the table's right wing; the lead's stand is lit
  function wigRow(g, shards, T, lift) {
    const n = Math.max(3, shards.length); const sorted = shards.slice().sort((a, b) => a.j - b.j);
    for (let i = 0; i < n; i++) { const S = sorted[i]; const x = 1590 + i * 74 - (n - 3) * 34; wigStand(g, x, 840, 1.05, S ? FEEL[S.fe.kind].wig : WIG, S && S.isLead ? lift : 0, !S && i > 0); }
  }
  // dead: the dressing room with no one in it; the wig left on its stand; the mirror keeps the moment, with her cut out
  function deadBeat(g, t, st, L, K, X, ghost) {
    wigStand(g, 1650, 840, 1.1, WIG, sm(1.2, 2.2, t) * .6, false);
    wigStand(g, 1760, 840, .85, WIG, 0, true);
    const k = st.deadAt ? st.deadAt.O : undefined; if (k === undefined || !L || !X.still) return;
    const e = L.ev[k]; const m = { k, deed: e.deed, A: e.A, V: e.V, role: e.A === 'O' ? 'doer' : 'victim', other: e.A === 'O' ? e.V : e.A, ago: 0, weight: 1, still: X.still(e) };
    const cr = crops(m, K); const box = { x: 940, y: 220, w: 460, h: 420 }; const u = sm(.5, 1.4, t);
    g.save(); g.globalAlpha = u; g.beginPath(); const P = [[960, 210], [1390, 250], [1370, 640], [990, 610]]; poly(g, P); g.clip();
    const map = cover(g, m.still, cr.frame, box); F.css; g.filter = 'grayscale(1) brightness(.75)'; cover(g, m.still, cr.frame, box); g.filter = 'none';
    if (cr.me) { // her place in the moment is cut out of the glass: a sack-and-wig shaped absence
      const a = map(cr.me.x, cr.me.y), b = map(cr.me.x + cr.me.w, cr.me.y + cr.me.h), w = b[0] - a[0], h = b[1] - a[1];
      g.save(); g.translate((a[0] + b[0]) / 2, b[1]); g.beginPath(); sackPath(g, w * .9, h * .9, 1, 0); g.moveTo(-w * .6, -h * .5); g.lineTo(-w * .6, -h * 1.0); g.lineTo(w * .6, -h * 1.0); g.lineTo(w * .6, -h * .5); g.closePath();
      g.fillStyle = '#07040c'; g.fill('nonzero'); g.strokeStyle = 'rgba(200,180,230,.7)'; g.lineWidth = 2; g.stroke(); g.restore(); }
    g.restore(); g.save(); g.globalAlpha = u * .8; g.strokeStyle = '#cfc6e0'; g.lineWidth = 2; g.beginPath(); poly(g, P); g.stroke(); g.restore();
  }

  // ---------------- FLASH: the shards fan out of her wig when she meets someone again ----------------
  function flash(g, t, mark, mems, K, X) {
    const st = X && X.state, L = X && X.ledger, lv = (st && st.levers && st.levers.O) || { halo: .5, grey: 0, shadow: 0, loom: 0, shrink: 0, tempo: 0 };
    const mk = mark || { x: 900, y: 500, w: 100, h: 230 };
    const env = sm(0, .25, t) * (1 - sm(1.25, 1.5, t));
    const top = mems.slice(0, 3); const fes = top.map(m => feelOf(m, st));
    const cx = mk.x + mk.w / 2, headY = mk.y + mk.h * .08;
    const side = cx < 960 ? 1 : -1;
    g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
    // the room dims around her: everything else becomes the dark behind the glass
    if (top.length) { const gr = g.createRadialGradient(cx, mk.y + mk.h / 2, Math.max(mk.w, mk.h) * .6, cx, mk.y + mk.h / 2, 1100); gr.addColorStop(0, 'rgba(8,4,14,0)'); gr.addColorStop(1, `rgba(8,4,14,${.55 * env})`); g.fillStyle = gr; g.fillRect(0, 0, W, H); }
    // glint across her body: a cold strip of reflection
    const gu = sm(.0, .45, t);
    if (gu > 0 && gu < 1) { g.save(); g.beginPath(); g.rect(mk.x - 10, mk.y - 20, mk.w + 20, mk.h + 20); g.clip(); g.globalCompositeOperation = 'lighter'; const gx = lerp(mk.x - mk.w, mk.x + mk.w * 2, gu); const lg = g.createLinearGradient(gx - 40, 0, gx + 40, 0); lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(.5, `rgba(240,230,255,${.55 * (.4 + .6 * cl(0, 1, lv.halo + .3))})`); lg.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = lg; g.translate(gx, mk.y); g.transform(1, 0, -.35, 1, 0, 0); g.translate(-gx, -mk.y); g.fillRect(mk.x - mk.w, mk.y - 20, mk.w * 4, mk.h + 40); g.restore(); }
    if (!top.length) { // vanity only: a hand-mirror of herself, lifted from the very frame (a render texture of the live stage)
      const u = env; const rt = RT('fl_self', mk.w + 40, mk.h + 40); rt.getContext('2d').drawImage(g.canvas, mk.x - 20, mk.y - 20, mk.w + 40, mk.h + 40, 0, 0, mk.w + 40, mk.h + 40);
      const hx = cx + side * (mk.w * .9 + 70), hy = mk.y + mk.h * .35, rw = Math.max(70, mk.w * .65), rh = rw * 1.35;
      g.save(); g.globalAlpha = u; g.translate(hx, hy); g.beginPath(); g.ellipse(0, 0, rw, rh, 0, 0, 7); g.fillStyle = '#1a1422'; g.fill(); g.save(); g.clip(); g.scale(-1, 1); g.drawImage(rt, -rw, -rh * .9, rw * 2, rw * 2 * rt.height / rt.width); g.restore(); g.lineWidth = 5; g.strokeStyle = '#c9b4dc'; g.stroke(); g.fillStyle = '#c9b4dc'; g.fillRect(-6, rh, 12, rh * .7); g.restore();
      g.restore(); return;
    }
    // fan of shards from her wig toward the open side of the frame
    const S0 = cl(.7, 1.25, 1080 / 1080) * 1;
    for (let j = top.length - 1; j >= 0; j--) {
      const m = top[j], fe = fes[j], amt = cl(.3, 1, m.weight);
      const u = sm(.1 + j * .08, .5 + j * .08, t) * (1 - sm(1.2 + j * .03, 1.45, t));
      if (u <= 0) continue;
      const sw = (j === 0 ? 360 : 250) * (.75 + .35 * amt), sh = sw * 1.15;
      // shards fan on an arc around the direction from her head toward the upper middle of the frame (continuous as she moves)
      const dir = Math.atan2(330 - headY, 960 - cx) + [0, -.75, .75][j];
      const rad = Math.max(mk.w, 90) * .5 + (j === 0 ? sw * .62 : sw * .8 + 120);
      const ang = side * (-.5 + j * .55);
      const tx = cl(sw * .55 + 10, W - sw * .55 - 10, cx + Math.cos(dir) * rad), ty = cl(sh * .55 + 10, H - sh * .55 - 10, headY + 60 + Math.sin(dir) * rad);
      const x = lerp(cx, tx, u), y = lerp(headY, ty, u), sc = u;
      let jx = 0, jy = 0; if (fe.kind === 'fear') { jx = (hash(Math.floor(t * 40) + j) - .5) * 10; jy = (hash(Math.floor(t * 40) + j + 5) - .5) * 8; }
      const P = []; const nv = 5 + Math.floor(hash(m.k * 3 + j) * 2); for (let i = 0; i < nv; i++) { const a = i / nv * Math.PI * 2 + hash(m.k + i) * .6; const rr = .78 + hash(m.k * 5 + i * 1.3) * .3; P.push([Math.cos(a) * sw * .5 * rr * 1.08, Math.sin(a) * sh * .5 * rr * 1.08]); }
      const bb = bbox(P), box = { x: bb.x, y: bb.y, w: bb.w, h: bb.h };
      const node = memoryNode(m, fe, box, t, 'fl' + j, K, amt, j === 0 && L ? (q) => { const bu = sm(.6, 1.15, t); if (bu <= 0) return; const b = beliefOf(L, m.k, st, m.other); q.save(); q.globalAlpha = .9; q.fillStyle = 'rgba(6,3,12,.5)'; q.fillRect(box.x, box.y + box.h * .55, box.w, box.h * .45); q.restore(); beliefGlyph(q, m.other, box.x + box.w * .42, box.y + box.h * .9, box.h * .36 / 330, b, bu, FEEL[fe.kind].edge); } : null);
      g.save(); g.globalAlpha = .4 * u; g.translate(x + jx + 14, y + jy + 18); g.rotate(ang * .15 * (1 - (fe.kind === 'grudge' ? 1 : 0))); g.scale(sc * (fe.kind === 'guilt' ? .55 : 1), sc); g.beginPath(); poly(g, P); g.fillStyle = '#000'; g.fill(); g.restore();
      render(g, { x: x + jx, y: y + jy, r: fe.kind === 'grudge' ? 0 : ang * .15, sx: sc * (fe.kind === 'guilt' ? .55 : 1), sy: sc, a: u, mask: q => poly(q, P), kids: [node], over(q) { q.beginPath(); poly(q, P); q.lineWidth = 3; q.strokeStyle = FEEL[fe.kind].edge; q.stroke(); if (fe.kind === 'pride') { q.lineWidth = 7; q.strokeStyle = 'rgba(230,190,90,.85)'; q.stroke(); } } });
      // a thread of light from her wig to the shard: this self saw it
      g.save(); g.globalAlpha = .45 * u; g.strokeStyle = FEEL[fe.kind].wig; g.lineWidth = 4; g.beginPath(); g.moveTo(cx, headY); g.lineTo(x, y); g.stroke(); g.restore();
    }
    // her wig flares in the lead self's colour
    const lw = FEEL[fes[0].kind].wig; g.save(); g.globalCompositeOperation = 'lighter'; const wr = g.createRadialGradient(cx, headY, 4, cx, headY, mk.w * 1.2); wr.addColorStop(0, hexA(lw, .7 * env)); wr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = wr; g.fillRect(cx - mk.w * 1.3, headY - mk.w * 1.3, mk.w * 2.6, mk.w * 2.6); g.restore();
    g.restore();
  }
  function hexA(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; }

  // ---------------- SOUND: glass grains; the remembered shot's sound returns through a mirror (high-passed, echoed) ----------------
  function sound(ac, out, t0, kind, mems, K) {
    const S = K.SND, mf = m => 440 * Math.pow(2, (m - 69) / 12);
    const top = mems.slice(0, kind === 'flash' ? 3 : 5), fes = top.map(m => feelOf(m, null));
    const crackT = t0 + (kind === 'flash' ? .12 : .5);
    if (!top.length) { S.say(ac, out, 'O', t0 + .15, 'tick', 1.2, -.3); S.say(ac, out, 'O', t0 + .6, 'breathe', 1.5, -.3); for (let i = 0; i < 3; i++) S.grain(ac, out, t0 + .2 + i * .18 + (kind === 'beat' ? .9 : 0), { f: mf(81 + [0, 4, 7][i]), d: .5, a: .14, pan: -.3, att: .05 }); return; }
    // the crack: a dry burst of high grains, then the O voice
    S.cloud(ac, out, crackT, .18, 260, { bp: 6500, q: 3, a: .09, d: [.004, .02], spread: .5 }, u => Math.pow(1 - u, 2));
    S.say(ac, out, 'O', crackT + .02, 'react', .8, -.4);
    top.forEach((m, j) => {
      const fe = fes[j], when = t0 + (kind === 'flash' ? .15 + j * .08 : .6 + j * .12), a = .07 + .09 * cl(0, 1, m.weight), notes = FEEL[fe.kind].note, pan = kind === 'flash' ? .2 * j : (j - 2) * .25;
      // each shard chimes its feeling (grudge: a cold minor second; fear: low beating; desire/pride: open intervals)
      for (let i = 0; i < notes.length; i++) S.grain(ac, out, when + i * (fe.kind === 'grudge' ? .004 : .05), { f: mf(notes[i]), d: fe.kind === 'guilt' ? .9 : .5, a: a * (i ? .6 : 1), pan, att: fe.kind === 'guilt' ? .5 : .03 });
      if (fe.kind === 'fear') S.cloud(ac, out, when, .9, 30, { f: mf(57), glide: -.05, a: .03, d: [.06, .12], type: 'triangle' }, u => Math.sin(Math.PI * u));
      if (j === 0) S.say(ac, out, m.other, when + .25, 'tick', .7, .5); // the other's voice, small, inside the glass
    });
    // the remembered contact returns through a glass mirror: the two voices of that shot, high-passed and echoed
    // (the doer's landing, the victim's cry), and once more, fainter, as the reflection of the reflection in a beat
    const m = top[0];
    try {
      const hp = ac.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 1600; hp.Q.value = .9;
      const dl = ac.createDelay(1); dl.delayTime.value = .11; const fb = ac.createGain(); fb.gain.value = .38; const wet = ac.createGain(); wet.gain.value = 1.6;
      hp.connect(wet); wet.connect(out); wet.connect(dl); dl.connect(fb); fb.connect(dl); dl.connect(out);
      const w0 = t0 + (kind === 'flash' ? .5 : 1.1);
      S.say(ac, hp, m.A, w0, 'land', 1, -.2); S.say(ac, hp, m.V, w0 + .1, 'react', 1, .3);
      if (kind === 'beat') { S.say(ac, hp, m.A, w0 + .6, 'land', .45, -.5); S.say(ac, hp, m.V, w0 + .7, 'react', .4, .6); }
    } catch (e) { }
    if (kind === 'beat') S.say(ac, out, 'O', t0 + 2.0, 'breathe', .5, -.4);
  }

  MEMORY({
    who: 'O', scion: 26, lineage: 'PixiJS — Archive Stage Rendering Engine (textures, containers, filters and masks)',
    op: 'Crop each remembered still around Ogiva into a mirror shard (polygon mask), push it through the filter stage of its feeling, and lift the strongest shard to show the other at the size she now believes it to be.',
    made: 'A dark dressing room with a bulb-lit vanity mirror that cracks into polygon shards; each shard is a render texture of a remembered still, masked and filtered, with a wig on a stand for each remembered self. Ogiva is a tall drawn sack with a purple wig; the others appear only as etched-glass outlines sized by her belief.',
    moved: 'The mirror cracks on a fixed beat and shards drift apart; the strongest lifts off the glass toward her and trembles, sways, turns away or holds dead still by feeling. Her pose comes from the feeling and the archetype levers (loom leans her in, shrink lowers her and droops the wig, halo lights the bulbs and her cone, shadow lengthens her floor shadow, grey drains her, tempo speeds the crack).',
    flash, beat, sound
  });
})();
