// 01 · BLACKMAIL · CONSEQUENCE — SCION-54 · Provenance Graph (archive-to-puppet lineage).
// The beat is a derivative DAG drawn on archive paper. Every thing on screen is a typed node with an
// immutable source id (a hash dot-code), a parent edge and an operation glyph:
//   SRC  the deed's own last frame (the source record)  --crop-->  the two sack puppets (lifted from the
//   deed's layers, re-cast here) ; SRC --crop V,recolour--> PHOTO (the evidence) --copy--> COPIES ;
//   V --pay--> A --spend--> PURCHASE (coins' trail) ; PHOTO --debt--> V (rings still owed) ;
//   PHOTO ..inferred..> future holders / fates read from the whole film's ledger (dashed = inferred).
// Rights status: every derivative of the photograph carries a red blocked-permission tick (the depicted
// sack never consented). Invariant (numeric): every node except SRC has exactly one parent edge drawn.
(function () {
  const IDS = ['R', 'B', 'I', 'O'];
  const PAPER = '#ebe2cc', PAPER2 = '#ded2b6', INK = '#1d1813', BLUE = '#46688a', RED = '#b3372c', GOLD = '#c99b2e';
  const COINS = { R: 4, B: 10, I: 4, O: 6 };           // what each victim paid in the deed (its payment schedule)
  const CACHE = {};
  function layerCanvas(A, V, layer, K, tt) {            // derivative of the deed: its after-state layer
    tt = tt == null ? 5.99 : tt;
    const key = A + V + layer + tt; if (CACHE[key]) return CACHE[key];
    const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080;
    const q = cv.getContext('2d');
    try { DEEDS.blackmail.draw(q, tt, A, V, K, { layer }) } catch (e) { }
    return CACHE[key] = cv;
  }
  function marks(A, V, K, tt) {
    tt = tt == null ? 5.99 : tt;
    const key = 'm' + A + V + tt; if (CACHE[key]) return CACHE[key];
    let m = null; try { m = DEEDS.blackmail.marks(tt, A, V, K) } catch (e) { }
    if (!m) m = { A: { x: 520, y: 560, w: 300, h: 300 }, V: { x: 1100, y: 560, w: 300, h: 300 } };
    return CACHE[key] = m;
  }
  // ---- provenance primitives ----
  function hcode(g, x, y, seed, K, n, cell, col, a) {   // immutable source id as a dot-code
    n = n || 12; cell = cell || 7; g.save(); g.globalAlpha *= (a == null ? 1 : a); g.fillStyle = col || INK;
    for (let i = 0; i < n; i++) { const b = K.hash(seed * 13.7 + i * 3.1) > .5; g.fillRect(x + i * cell, y + (b ? 0 : cell * .5), cell * .7, cell * (b ? 1 : .5)) }
    g.restore();
  }
  function edge(g, x0, y0, x1, y1, u, o) {               // a dependency edge drawn from parent to child, u=0..1 grown
    o = o || {}; if (u <= 0) return null; u = Math.min(1, u);
    const bx = (x0 + x1) / 2 + (o.bend || 0), by = (y0 + y1) / 2 - (o.lift || 0);
    const pt = s => ({ x: (1 - s) * (1 - s) * x0 + 2 * (1 - s) * s * bx + s * s * x1, y: (1 - s) * (1 - s) * y0 + 2 * (1 - s) * s * by + s * s * y1 });
    g.save(); g.strokeStyle = o.col || INK; g.lineWidth = o.w || 3; g.globalAlpha *= (o.a == null ? 1 : o.a);
    if (o.dash) g.setLineDash(o.dash);
    g.beginPath(); g.moveTo(x0, y0); for (let s = .04; s <= u + 1e-6; s += .04) { const p = pt(s); g.lineTo(p.x, p.y) } g.stroke();
    g.setLineDash([]);
    const e = pt(u), e0 = pt(Math.max(0, u - .04)), ang = Math.atan2(e.y - e0.y, e.x - e0.x);
    if (u >= 1 && !o.noHead) { g.fillStyle = o.col || INK; g.beginPath(); g.moveTo(e.x, e.y); g.lineTo(e.x - 18 * Math.cos(ang - .4), e.y - 18 * Math.sin(ang - .4)); g.lineTo(e.x - 18 * Math.cos(ang + .4), e.y - 18 * Math.sin(ang + .4)); g.fill() }
    g.restore();
    return pt;
  }
  function opGlyph(g, x, y, kind, a, col) {             // operation signature, a diamond on the edge
    if (a <= 0) return; g.save(); g.globalAlpha *= Math.min(1, a); g.translate(x, y);
    g.fillStyle = PAPER; g.strokeStyle = col || INK; g.lineWidth = 3;
    g.beginPath(); g.moveTo(0, -22); g.lineTo(22, 0); g.lineTo(0, 22); g.lineTo(-22, 0); g.closePath(); g.fill(); g.stroke();
    g.lineWidth = 2.5;
    if (kind === 'crop') { g.setLineDash([4, 3]); g.strokeRect(-9, -9, 18, 18); g.setLineDash([]) }
    if (kind === 'tint') { g.beginPath(); g.arc(0, 0, 9, 0, 7); g.stroke(); g.fillStyle = col || INK; g.beginPath(); g.arc(0, 0, 9, -Math.PI / 2, Math.PI / 2); g.fill() }
    if (kind === 'copy') { g.strokeRect(-10, -9, 13, 13); g.strokeRect(-3, -3, 13, 13) }
    if (kind === 'pay') { g.fillStyle = GOLD; g.beginPath(); g.arc(0, 0, 9, 0, 7); g.fill(); g.stroke() }
    if (kind === 'spend') { g.beginPath(); g.moveTo(-9, 0); g.lineTo(8, 0); g.moveTo(3, -6); g.lineTo(9, 0); g.lineTo(3, 6); g.stroke() }
    if (kind === 'debt') { g.beginPath(); g.arc(-4, 0, 6, 0, 7); g.stroke(); g.beginPath(); g.arc(5, 0, 6, 0, 7); g.stroke() }
    if (kind === 'tear') { g.beginPath(); g.moveTo(-8, -9); g.lineTo(-2, -2); g.lineTo(-6, 3); g.lineTo(0, 9); g.stroke() }
    if (kind === 'lose') { g.beginPath(); g.moveTo(-8, -6); g.quadraticCurveTo(0, -12, 8, 6); g.stroke(); g.fillStyle = col || INK; g.fillRect(4, 4, 5, 5) }
    if (kind === 'know') { g.beginPath(); g.ellipse(0, 0, 11, 6, 0, 0, 7); g.stroke(); g.fillStyle = col || INK; g.beginPath(); g.arc(0, 0, 3.5, 0, 7); g.fill() }
    g.restore();
  }
  function blocked(g, x, y, a) {                        // rights status: no consent from the depicted sack
    if (a <= 0) return; g.save(); g.globalAlpha *= a; g.strokeStyle = RED; g.lineWidth = 3;
    g.strokeRect(x - 9, y - 9, 18, 18); g.beginPath(); g.moveTo(x - 9, y + 9); g.lineTo(x + 9, y - 9); g.stroke(); g.restore();
  }
  // the photograph: a crop of the source record over the victim, recoloured sepia; torn/aged by options
  function photo(g, src, vb, x, y, w, h, o, K) {
    o = o || {}; g.save(); g.translate(x, y); g.rotate(o.rot || 0); g.globalAlpha *= (o.a == null ? 1 : o.a);
    const pad = 70, sx = vb.x - pad, sy = vb.y - pad * 1.3, sw = vb.w + pad * 2, sh = sw * h / w;
    g.fillStyle = '#f6f0e2'; g.shadowColor = 'rgba(0,0,0,.25)'; g.shadowBlur = 10; g.shadowOffsetY = 4;
    g.fillRect(-w / 2 - 8, -h / 2 - 8, w + 16, h + 16); g.shadowColor = 'transparent';
    g.save(); g.beginPath(); g.rect(-w / 2, -h / 2, w, h); g.clip();
    g.filter = 'sepia(1) contrast(1.1) brightness(' + (1.05 + (o.age || 0) * .2) + ')';
    if (src) g.drawImage(src, sx, sy, sw, sh, -w / 2, -h / 2, w, h);
    g.filter = 'none'; g.restore();
    if (o.tear) {                                         // a torn photograph: the paper behind shows through a jagged gap
      g.fillStyle = PAPER; g.beginPath(); g.moveTo(-6, -h / 2 - 10);
      for (let i = 0; i <= 8; i++) g.lineTo((i % 2 ? 6 : -6) + o.tear * 14, -h / 2 - 10 + (h + 20) * i / 8);
      for (let i = 8; i >= 0; i--) g.lineTo((i % 2 ? 6 : -6) - o.tear * 14, -h / 2 - 10 + (h + 20) * i / 8);
      g.fill();
    }
    g.restore();
  }
  function sackPuppet(g, cv, box, cx, floorY, sc, o, K) { // the sack cast from its crop; filters = levers
    const pad = 60, sx = box.x - pad, sy = box.y - pad, sw = box.w + pad * 2, sh = box.h + pad;
    const w = sw * sc, h = sh * sc;
    g.save();
    if (o.shadow > 0) {                                   // shadow lever: the silhouette thrown long on the floor
      g.save(); g.globalAlpha = Math.min(.55, .12 + o.shadow * .9); g.translate(cx, floorY);
      g.transform(1, 0, o.shadowDir * (1.2 + o.shadow * 3), .25, 0, 0); g.filter = 'brightness(0)';
      g.drawImage(cv, sx, sy, sw, sh, -w / 2, -h, w, h); g.restore();
    }
    if (o.halo > 0) {                                     // halo lever: the light finds it
      const r = h * .9, gr = g.createRadialGradient(cx, floorY - h * .5, 10, cx, floorY - h * .5, r);
      gr.addColorStop(0, 'rgba(255,236,170,' + Math.min(.8, o.halo) + ')'); gr.addColorStop(1, 'rgba(255,236,170,0)');
      g.fillStyle = gr; g.fillRect(cx - r, floorY - h * .5 - r, r * 2, r * 2);
    }
    g.translate(cx, floorY); g.rotate(o.lean || 0); if (o.flip) g.scale(-1, 1);
    g.filter = o.grey > 0 ? 'grayscale(' + Math.min(1, o.grey) + ')' : 'none';
    g.drawImage(cv, sx, sy, sw, sh, -w / 2, -h, w, h);
    g.filter = 'none'; g.restore();
    return { x: cx - w / 2, y: floorY - h, w, h, top: floorY - (box.h * sc) };
  }
  function coin(g, x, y, r, a) { g.save(); g.globalAlpha *= a; g.fillStyle = GOLD; g.strokeStyle = INK; g.lineWidth = 2; g.beginPath(); g.ellipse(x, y, r, r * .85, 0, 0, 7); g.fill(); g.stroke(); g.beginPath(); g.arc(x, y, r * .45, 0, 7); g.stroke(); g.restore() }
  function ring(g, x, y, r, a) { g.save(); g.globalAlpha *= a; g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); g.arc(x, y, r, 0, 7); g.stroke(); g.restore() }
  function nodeFrame(g, x, y, w, h, seed, K, a) {
    g.save(); g.globalAlpha *= a; g.fillStyle = '#f4eddc'; g.strokeStyle = INK; g.lineWidth = 3;
    g.fillRect(x, y, w, h); g.strokeRect(x, y, w, h); g.restore();
    hcode(g, x + 8, y + h + 8, seed, K, 10, 6, INK, a * .8);
  }
  // purchases: where the coins go next, one per doer's temperament (vector icons)
  function purchase(g, who, x, y, a, fill, K) {
    g.save(); g.globalAlpha *= a; g.translate(x, y); g.strokeStyle = INK; g.lineWidth = 4; g.fillStyle = INK;
    if (who === 'R') {   // a strongbox: the miser's
      g.fillStyle = '#5a4632'; g.fillRect(-60, -40, 120, 80); g.strokeRect(-60, -40, 120, 80);
      g.fillStyle = GOLD; g.fillRect(-60, -40, 120, 14 + 0 * fill); g.strokeRect(-60, -40, 120, 14);
      g.fillStyle = INK; g.beginPath(); g.arc(0, 6, 9, 0, 7); g.fill(); g.fillRect(-3, 6, 6, 16);
    } else if (who === 'B') { // a loaf: strength eats
      g.fillStyle = '#b4844a'; g.beginPath(); g.ellipse(0, 0, 70, 38, 0, 0, 7); g.fill(); g.stroke();
      g.lineWidth = 3; for (let i = -1; i <= 1; i++) { g.beginPath(); g.moveTo(i * 26 - 10, -20); g.lineTo(i * 26 + 10, 12); g.stroke() }
    } else if (who === 'I') { // a bottle: spent on nothing
      g.fillStyle = '#3e5e48'; g.beginPath(); g.moveTo(-22, 45); g.lineTo(-22, -5); g.quadraticCurveTo(-22, -22, -8, -30); g.lineTo(-8, -55); g.lineTo(8, -55); g.lineTo(8, -30); g.quadraticCurveTo(22, -22, 22, -5); g.lineTo(22, 45); g.closePath(); g.fill(); g.stroke();
    } else {             // a new wig on a stand: vanity
      g.fillStyle = INK; g.fillRect(-4, 0, 8, 50); g.fillRect(-30, 46, 60, 8);
      g.fillStyle = '#7a3b8f'; g.beginPath(); g.ellipse(0, -20, 42, 34, 0, Math.PI, 0); g.lineTo(42, 30); g.lineTo(26, 30); g.lineTo(26, -10); g.lineTo(-26, -10); g.lineTo(-26, 30); g.lineTo(-42, 30); g.closePath(); g.fill(); g.stroke();
    }
    g.restore();
  }

  function render(g, t, ev, st, K, X) {
    const { A, V, k } = ev, W = K.W, H = K.H;
    const sm = K.sm, eo = K.eo, cl = K.cl, lerp = K.lerp;
    const LA = st.levers[A] || {}, LV = st.levers[V] || {};
    const mA = st.mind[A][V], mV = st.mind[V][A];
    const tp = 1 + (LA.tempo || 0) * .6;                 // tempo lever: the doer's operations run faster
    const ta = t * tp;
    const M = marks(A, V, K), cvA = layerCanvas(A, V, 'A', K), cvV = layerCanvas(A, V, 'V', K);
    const src = X && X.still ? X.still(ev, 5.99) : null;
    const FLOOR = 862;
    // ---------- branches from the state ----------
    const doerB = !st.alive[V] ? 'orphan' : mA.guilt >= .25 ? 'return' : mA.pride >= .4 ? 'copies' : 'lose';
    const victB = !st.alive[V] ? 'none' : mV.grudge >= .4 ? 'watch' : mV.fear >= .3 ? 'cower' : 'shrug';
    const wits = IDS.filter(s => s !== A && s !== V && st.alive[s] && st.know[s].includes(k));   // documented holders
    let fut = [], fates = [];                              // inferred afterlife from the whole film
    if (X && X.ledger) {
      const L = X.ledger, last = L.states[L.states.length - 1];
      fut = IDS.filter(s => s !== A && s !== V && !wits.includes(s) && last.know[s].includes(k)).map(s => {
        let at = 11; for (let j = k + 1; j < L.states.length; j++) if (L.states[j].know[s].includes(k)) { at = j - 1; break }
        return { s, at };
      });
      for (const s of [A, V]) if (!last.alive[s] && last.deadAt[s] != null && last.deadAt[s] > k) fates.push({ s, at: last.deadAt[s] });
    }
    // ---------- 0. ground: archive paper with the room as a faint survey drawing ----------
    g.fillStyle = PAPER; g.fillRect(0, 0, W, H);
    g.strokeStyle = 'rgba(70,104,138,.18)'; g.lineWidth = 1;
    for (let x = 0; x <= W; x += 60) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke() }
    for (let y = 0; y <= H; y += 60) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke() }
    g.strokeStyle = 'rgba(70,104,138,.55)'; g.lineWidth = 2.5;
    g.beginPath(); g.moveTo(0, FLOOR); g.lineTo(W, FLOOR); g.stroke();
    g.strokeRect(1690, 520, 150, 342);                    // the door, surveyed
    g.beginPath(); for (let i = 0; i < 9; i++) { g.moveTo(40 + i * 30, FLOOR - i * 34); g.lineTo(70 + i * 30, FLOOR - i * 34); g.lineTo(70 + i * 30, FLOOR - (i + 1) * 34) } g.stroke(); // stairs
    const night = g.createLinearGradient(0, 0, 0, H); night.addColorStop(0, 'rgba(20,24,40,.32)'); night.addColorStop(.5, 'rgba(20,24,40,0)'); night.addColorStop(1, 'rgba(20,24,40,.18)');
    g.fillStyle = night; g.fillRect(0, 0, W, H);
    // timeline ruler: the film's 12 events; this one filled; inferred future slots dashed
    const RX = 360, RW = 1200, RY = 1010, slot = i => RX + RW * (i + .5) / 12;
    const ru = sm(.3, 1.0, t);
    g.save(); g.globalAlpha = ru; g.strokeStyle = INK; g.lineWidth = 2;
    g.beginPath(); g.moveTo(RX, RY); g.lineTo(RX + RW, RY); g.stroke();
    for (let i = 0; i < 12; i++) { const x = slot(i); g.beginPath(); g.moveTo(x, RY - 10); g.lineTo(x, RY + 10); g.stroke(); if (i === k) { g.fillStyle = RED; g.fillRect(x - 11, RY - 11, 22, 22) } }
    g.restore();
    // ---------- 1. the source record: the deed's last frame shrinks into a card ----------
    const SC = { x: 760, y: 34, w: 400, h: 225 };
    const su = eo(.25, 1.0, t);
    const sr = { x: lerp(0, SC.x, su), y: lerp(0, SC.y, su), w: lerp(W, SC.w, su), h: lerp(H, SC.h, su) };
    if (src) {
      g.save(); g.shadowColor = 'rgba(0,0,0,.3)'; g.shadowBlur = 16 * su; g.drawImage(src, sr.x, sr.y, sr.w, sr.h); g.restore();
      g.save(); g.globalAlpha = su; g.strokeStyle = INK; g.lineWidth = 4; g.strokeRect(sr.x, sr.y, sr.w, sr.h); g.restore();
    }
    hcode(g, SC.x, SC.y + SC.h + 10, 1000 + k * 17 + IDS.indexOf(A) * 4 + IDS.indexOf(V), K, 16, 8, INK, sm(.8, 1.1, t));
    // crop masks drawn on the source over each sack (their parent region)
    const sx = b => ({ x: SC.x + b.x / W * SC.w, y: SC.y + b.y / H * SC.h, w: b.w / W * SC.w, h: b.h / H * SC.h });
    const cmA = sx(M.A), cmV = sx(M.V), cu = sm(.9, 1.2, t);
    g.save(); g.globalAlpha = cu; g.setLineDash([6, 4]); g.lineWidth = 3; g.strokeStyle = BLUE; g.strokeRect(cmA.x - 4, cmA.y - 4, cmA.w + 8, cmA.h + 8);
    g.strokeStyle = RED; g.strokeRect(cmV.x - 4, cmV.y - 4, cmV.w + 8, cmV.h + 8); g.restore();
    // ---------- 2. the sacks, cast from their crops (levers drive scale, lean, shadow, halo, grey) ----------
    const acx0 = M.A.x + M.A.w / 2, vcx0 = M.V.x + M.V.w / 2;
    // doer motion by branch
    let acx = acx0, aLean = 0, aFlip = false;
    const loom = Math.max(0, LA.loom || 0), weight = Math.max(0, LA.weight || 0);
    if (doerB === 'return') acx = acx0 + 120 * sm(1.4, 1.9, ta) - 120 * sm(2.35, 2.8, ta);     // he goes back
    if (doerB === 'copies') acx = acx0 - 70 * sm(1.3, 2.0, ta);                                  // steps back to its hoard
    if (doerB === 'lose') aLean = -.06 * Math.sin(t * 2.4);
    aLean += loom * .25 * sm(.8, 1.6, ta);                    // loom: leans toward the victim
    const bob = weight * 10 * Math.abs(Math.sin(ta * Math.PI * 2.2)) * sm(1.4, 1.8, ta) * (1 - sm(2.6, 2.9, ta));
    const aScale = 1 + loom * .35 * sm(.6, 1.6, t);
    // victim response
    let vLean = 0, vFlip = false, vcx = vcx0;
    const vScale = 1 - (LV.shrink || 0) * 1.1 * sm(1.0, 2.2, t);  // shrink lever: smaller under the debt
    if (victB === 'cower') { vFlip = t > 1.9; vcx = vcx0 + 60 * sm(1.6, 2.4, t); vLean = .05 * sm(1.6, 2.4, t) }
    if (victB === 'shrug') vLean = .07 * Math.sin(t * 1.8);
    if (victB === 'watch') vLean = -.05 * sm(1.6, 2.2, t);
    const debtN = 2 + Math.round((mV.debt || 0) * 4);
    const hang = sm(1.4, 2.0, t);
    vLean += .04 * debtN / 6 * hang;                           // the debt pulls it down toward the photo
    const fadeIn = 1; // sacks are present from frame 0 (continuity)
    const pa = sackPuppet(g, cvA, M.A, acx, FLOOR - bob, aScale, { lean: aLean, flip: aFlip, shadow: (LA.shadow || 0) * 1.5 * sm(.6, 1.8, t), shadowDir: -1, halo: (LA.halo || 0) * sm(.6, 1.6, t), grey: LA.grey || 0 }, K);
    const pv = sackPuppet(g, cvV, M.V, vcx, FLOOR, vScale, { lean: vLean, flip: vFlip, shadow: (LV.shadow || 0) * 1.5, shadowDir: 1, halo: (LV.halo || 0) * (1 - sm(1.2, 2.4, t)), grey: (LV.grey || 0) + .35 * sm(1.4, 2.6, t) * (victB === 'cower' ? 1 : .5) }, K);
    // crop edges from the source masks down to each cast puppet (derivation)
    const de = sm(1.0, 1.6, t), dfade = 1 - .8 * sm(1.7, 2.2, t);
    edge(g, cmA.x + cmA.w / 2, cmA.y + cmA.h + 6, pa.x + pa.w / 2, pa.y + 30, de, { col: BLUE, w: 2.5, a: dfade, bend: -120, dash: [10, 6] });
    edge(g, cmV.x + cmV.w / 2, cmV.y + cmV.h + 6, pv.x + pv.w / 2, pv.y + 30, de, { col: BLUE, w: 2.5, a: dfade, bend: 120, dash: [10, 6] });
    // ---------- 3. the photograph: derivative of SRC (crop V, tint), held over the doer ----------
    const PH = { w: 200, h: 150 };
    const phHome = { x: pa.x + pa.w / 2 + 40, y: Math.max(330, pa.top - 150) };
    const pu = eo(.7, 1.5, t);
    let ph = { x: lerp(cmV.x + cmV.w / 2, phHome.x, pu), y: lerp(cmV.y + cmV.h / 2, phHome.y, pu), rot: lerp(0, -.08, pu), a: sm(.6, .8, t), tear: 0 };
    if (doerB === 'return') { ph.x = phHome.x + 120 * sm(1.4, 1.9, ta) - 120 * sm(2.35, 2.8, ta); ph.tear = sm(1.9, 2.2, ta) }
    if (doerB === 'lose') { // it slips from Inigo's ear and slides out under the door
      const lu = sm(1.5, 2.7, t); ph.x = lerp(phHome.x, 1765, lu); ph.y = lerp(phHome.y, 840, sm(1.5, 1.9, t)) + 20 * Math.sin(t * 9) * (1 - lu) * lu; ph.rot = lerp(-.08, 1.3, sm(1.5, 1.9, t)) + 6 * lu; ph.a *= 1 - sm(2.55, 2.85, t);
    }
    const phW = PH.w * lerp(.6, 1, pu), phH = PH.h * lerp(.6, 1, pu);
    // the edge SRC->PHOTO with crop + tint operation signatures
    const pe = edge(g, cmV.x + cmV.w / 2, cmV.y + cmV.h / 2, ph.x, ph.y - phH / 2 - 14, sm(.7, 1.3, t), { col: RED, w: 3.5, bend: -60, lift: 30, a: 1 - .5 * sm(2.2, 2.8, t) });
    if (pe) { const p1 = pe(.55), p2 = pe(.8); opGlyph(g, p1.x, p1.y, 'crop', sm(1.0, 1.2, t), RED); opGlyph(g, p2.x, p2.y, 'tint', sm(1.1, 1.3, t), RED) }
    // ---------- 4. debt: the hanging chain of rings still owed, from the photograph to the victim ----------
    if (st.alive[V]) {
      const x0 = ph.x + phW / 2 - 10, y0 = ph.y + phH / 2, x1 = pv.x + pv.w * .5, y1 = pv.y + pv.h * .35;
      const sag = 40 + 10 * debtN + (victB === 'shrug' ? 60 : 0);
      for (let i = 0; i < debtN; i++) {
        const u = (i + 1) / (debtN + 1), app = sm(1.4 + i * .08, 1.6 + i * .08, t);
        const sw = Math.sin(t * 3 + i) * 4 * (1 - u);
        const x = lerp(x0, x1, u) + sw, y = Math.min(FLOOR - 24, lerp(y0, y1, u) + sag * 4 * u * (1 - u) * hang);
        ring(g, x, y, 15, app);
      }
      edge(g, x0, y0, x1, y1, hang, { a: .35, w: 2, lift: -sag * 2 * hang, noHead: true, dash: [3, 7] }); // (chain guide)
      const dm = { x: lerp(x0, x1, .5), y: Math.min(FLOOR - 70, lerp(y0, y1, .5) + sag * hang) };
      opGlyph(g, dm.x, dm.y - 44, 'debt', hang, INK);
    }
    // ---------- 5. coins' trail: V --pay--> A --spend--> purchase ----------
    const nC = COINS[V] || 4;
    const vx = pv.x + pv.w * .3, vy = pv.y + pv.h * .55, axp = pa.x + pa.w * .75, ayp = pa.y + pa.h * .55;
    edge(g, vx, vy, axp, ayp, sm(1.1, 1.5, t), { col: GOLD, w: 3, lift: 120, a: .9 });
    opGlyph(g, (vx + axp) / 2, Math.min(vy, ayp) - 60, 'pay', sm(1.3, 1.5, t), INK);
    const PUR = { x: 210, y: 430 };
    const spendN = doerB === 'return' ? nC - 1 : nC;
    const pa2 = sm(1.9, 2.2, ta);
    nodeFrame(g, PUR.x - 95, PUR.y - 85, 190, 170, 77 + IDS.indexOf(A), K, pa2);
    edge(g, pa.x + pa.w * .3, pa.y + pa.h * .3, PUR.x + 100, PUR.y + 20, sm(1.8, 2.2, ta), { col: GOLD, w: 3, lift: 40, a: .9 });
    opGlyph(g, (pa.x + pa.w * .3 + PUR.x + 100) / 2, (pa.y + pa.h * .3 + PUR.y) / 2 - 30, 'spend', sm(2.0, 2.2, ta), INK);
    let arrived = 0;
    for (let i = 0; i < nC; i++) {
      const t0 = 1.3 + i * (.7 / nC), u1 = sm(t0, t0 + .35, ta);
      const back = doerB === 'return' && i === nC - 1;
      const t1 = 2.0 + i * (.5 / nC), u2 = sm(t1, t1 + .35, ta);
      let x, y, a = sm(t0 - .05, t0, ta);
      if (u2 <= 0 || back) { x = lerp(vx, axp, u1); y = lerp(vy, ayp, u1) - 240 * u1 * (1 - u1) }
      else { x = lerp(axp, PUR.x, u2); y = lerp(ayp, PUR.y, u2) - 160 * u2 * (1 - u2); if (u2 >= 1) { arrived++; a = 0 } }
      if (back) { const ub = sm(2.0, 2.4, ta); x = lerp(x, pv.x + pv.w * .2, ub); y = lerp(y, FLOOR - 14, ub) - 120 * ub * (1 - ub) }
      if (u1 >= 1 && u2 <= 0 && !back) { y = ayp + 30 - i * 9; x = axp + 10 } // stacked in hand
      coin(g, x, y, 15, a);
    }
    purchase(g, A, PUR.x, PUR.y, pa2 * (doerB === 'copies' && A !== 'R' ? 1 : 1) * sm(2.1, 2.5, ta) * (arrived > 0 ? 1 : 0) + 0 * pa2, arrived / spendN, K);
    // ---------- 6. the doer's own branch ----------
    if (doerB === 'copies') {           // pride: the evidence is duplicated (fan-out in the DAG)
      const nCopy = A === 'O' ? 3 : 2;
      for (let i = 0; i < nCopy; i++) {
        const cu2 = eo(1.7 + i * .25, 2.2 + i * .25, ta);
        if (cu2 <= 0) continue;
        let tx, ty, rot;
        if (A === 'R') { tx = PUR.x - 20 + i * 40; ty = PUR.y - 10; rot = .1 * i }           // filed in the strongbox
        else { tx = 130 + i * 175; ty = 170; rot = (i - 1) * .06 }                                // pinned up for show
                const cx2 = lerp(ph.x, tx, cu2), cy2 = lerp(ph.y, ty, cu2);
        const ce = edge(g, ph.x - phW / 2, ph.y, cx2 + 70, cy2, cu2, { w: 2.5, bend: 30 });
        if (ce) { const p = ce(.5); opGlyph(g, p.x, p.y, 'copy', sm(1.9 + i * .25, 2.1 + i * .25, ta)) }
        const shrinkIn = A === 'R' ? 1 - .6 * sm(2.5, 2.9, ta) : 1;
        photo(g, src, M.V, cx2, cy2, 150 * shrinkIn, 112 * shrinkIn, { rot, a: A === 'R' ? 1 - sm(2.75, 2.95, ta) : 1 }, K);
        blocked(g, cx2 + 66 * shrinkIn, cy2 - 52 * shrinkIn, A === 'R' ? 1 - sm(2.75, 2.95, ta) : 1);
        hcode(g, cx2 - 70, cy2 + 66, 300 + i * 9 + IDS.indexOf(A), K, 9, 6, INK, A === 'R' ? 1 - sm(2.75, 2.95, ta) : 1);
      }
      if (A === 'R') { // counting: a tally of marks under the box, one per coin
        for (let i = 0; i < arrived; i++) { g.fillStyle = INK; g.fillRect(PUR.x - 80 + i * 14, PUR.y + 120, 5, 26) }
      }
    }
    if (doerB === 'lose') {             // the evidence leaves the house: a window lights outside
      const ou = sm(2.6, 2.9, t);
      edge(g, phHome.x, phHome.y, 1765, 845, sm(1.5, 2.6, t), { dash: [12, 8], w: 2.5, lift: 160, a: .9 });
      opGlyph(g, (phHome.x + 1765) / 2, Math.min(phHome.y, 845) - 120, 'lose', sm(1.6, 1.9, t));
      g.save(); g.globalAlpha = ou; g.fillStyle = '#222a3c'; g.fillRect(1700, 120, 160, 200);
      g.fillStyle = '#f4d77a'; g.fillRect(1730, 160, 40, 55); g.fillRect(1790, 160, 40, 55); g.fillRect(1730, 235, 40, 55);
      g.strokeStyle = INK; g.lineWidth = 4; g.strokeRect(1700, 120, 160, 200); g.restore();
      edge(g, 1765, 520, 1780, 330, sm(2.6, 2.95, t), { dash: [12, 8], w: 2.5 });
      blocked(g, 1850, 130, ou);
    }
    if (doerB === 'return') {           // guilt: he goes back, tears it, sets one coin down; the tear is a new node, the lineage stays
      if (sm(1.9, 2.2, ta) > 0) opGlyph(g, ph.x, ph.y - phH / 2 - 44, 'tear', sm(1.9, 2.1, ta));
    }
    // the photograph itself (drawn last so it sits on its edges)
    if (ph.a > 0) {
      photo(g, src, M.V, ph.x, ph.y, phW, phH, { rot: ph.rot, a: ph.a, tear: ph.tear }, K);
      blocked(g, ph.x + phW / 2 - 6, ph.y - phH / 2 + 6, ph.a * sm(1.2, 1.4, t));
      hcode(g, ph.x - phW / 2, ph.y + phH / 2 + 14, 200 + IDS.indexOf(A) * 4 + IDS.indexOf(V), K, 12, 6, INK, ph.a * sm(1.2, 1.4, t));
    }
    // ---------- 7. the victim's branch ----------
    if (victB === 'watch') {            // grudge: it marks where the evidence went (a knowledge edge of its own)
      let tx = ph.x, ty = ph.y;
      if (doerB === 'copies') { tx = A === 'R' ? PUR.x : 540; ty = A === 'R' ? PUR.y : 160 }
      if (doerB === 'lose') { tx = 1765; ty = 845 }
      const we = edge(g, pv.x + pv.w * .5, pv.y + 20, tx, ty, sm(2.2, 2.75, t), { col: RED, w: 3, dash: [4, 8], lift: 260, bend: -100 });
      if (we) { const p = we(.5); opGlyph(g, p.x, p.y, 'know', sm(2.4, 2.6, t), RED) }
    }
    // ---------- 8. holders: documented (solid) and inferred from the film (dashed) ----------
    const holders = wits.map(s => ({ s, at: k, inf: false })).concat(fut.map(f => ({ ...f, inf: true })));
    holders.forEach((hd, i) => {
      const hu = sm(2.3 + i * .15, 2.7 + i * .15, t); if (hu <= 0) return;
      // the holder is itself lifted from a source (the deed's idle frame with it as doer), ghosted when inferred
      const oth = IDS.find(o => o !== hd.s), hb = marks(hd.s, oth, K, 0).A, hcv = layerCanvas(hd.s, oth, 'A', K, 0);
      const s2 = .62, hx = 1600 + i * 150, w = (hb.w + 120) * s2, h = (hb.h + 60) * s2, hy = FLOOR;
      g.save(); g.globalAlpha = hu * (hd.inf ? .5 : 1); g.filter = hd.inf ? 'grayscale(1) contrast(.6) brightness(1.6)' : 'none';
      g.drawImage(hcv, hb.x - 60, hb.y - 60, hb.w + 120, hb.h + 60, hx - w / 2, hy - h, w, h); g.filter = 'none'; g.restore();
      g.save(); g.globalAlpha = hu; g.strokeStyle = hd.inf ? INK : BLUE; g.lineWidth = 3; g.setLineDash(hd.inf ? [10, 7] : []);
      g.strokeRect(hx - w / 2 + 14, hy - h + 14, w - 28, h - 14); g.setLineDash([]); g.restore();
      hcode(g, hx - w / 2 + 14, hy + 10, 500 + IDS.indexOf(hd.s) * 7, K, 8, 6, INK, hu);
      edge(g, ph.x + phW / 2, ph.y - 20, hx, hy - h + 6, hu, { dash: hd.inf ? [10, 8] : null, w: 3, lift: 140, a: .85 });
      edge(g, hx, hy + 22, slot(hd.at), RY - 14, hu, { dash: [4, 6], w: 2, a: .55, noHead: true });
      g.save(); g.globalAlpha = hu; g.strokeStyle = INK; g.lineWidth = 3; g.strokeRect(slot(hd.at) - 10, RY - 10, 20, 20); g.restore();
    });
    fates.forEach((f, i) => {           // inferred: a holder of the debt will not survive the film
      const fu = sm(2.5 + i * .15, 2.9 + i * .15, t); if (fu <= 0) return;
      const from = f.s === A ? pa : pv;
      edge(g, from.x + from.w / 2, FLOOR + 10, slot(f.at), RY - 14, fu, { dash: [10, 8], w: 2.5, a: .7, noHead: true, lift: -40 });
      g.save(); g.globalAlpha = fu; g.fillStyle = INK; g.fillRect(slot(f.at) - 10, RY - 10, 20, 20); g.strokeStyle = PAPER; g.lineWidth = 3;
      g.beginPath(); g.moveTo(slot(f.at) - 7, RY - 7); g.lineTo(slot(f.at) + 7, RY + 7); g.moveTo(slot(f.at) + 7, RY - 7); g.lineTo(slot(f.at) - 7, RY + 7); g.stroke(); g.restore();
    });
    // first 0.25 s: the deed's final frame exactly (continuity); everything above is under it until it shrinks
    if (src && t < .25) g.drawImage(src, 0, 0, W, H);
  }

  CONSEQ({
    deed: 'blackmail', n: 1, scion: 54, lineage: 'Provenance Graph — Archive-to-Puppet Lineage',
    op: 'The deed\'s last frame becomes a source record; the photograph, the coins and the debt are drawn as derivatives of it, each with a parent edge, an operation mark and an id, so you can see where the evidence went and who holds it.',
    made: 'Archive paper with the room as a faint blue survey drawing. The sacks are lifted from the deed\'s own after-state layers through crop masks marked on the shrunken source frame; the photograph is a sepia crop of the victim from that frame, and the coins, rings, purchase and holders are typed nodes with dot-code ids and red permission marks.',
    moved: 'Edges grow from parent to child on a schedule, coins fly along the pay and spend edges, and copies or tears are new nodes on new edges. Which branch runs comes from the ledger state (doer guilt or pride, victim grudge or fear, debt, who knows); the myth levers set loom, weight, tempo, halo, shadow, shrink and grey, and the whole film\'s ledger supplies the dashed inferred holders and fates on the timeline.',
    dur: 3.0,
    beat(g, t, ev, st, K, X) { render(g, t, ev, st, K, X) },
    sound(ac, out, t0, ev, st, K) {
      const bus = ac.createGain(); bus.gain.value = 2.4; bus.connect(out); out = bus;
      const S = K.SND, A = ev.A, V = ev.V, mA = st.mind[A][V], mV = st.mind[V][A];
      const doerB = !st.alive[V] ? 'orphan' : mA.guilt >= .25 ? 'return' : mA.pride >= .4 ? 'copies' : 'lose';
      const tp = 1 + ((st.levers[A] || {}).tempo || 0) * .6, at = x => t0 + x / tp;
      // shrink of the source frame: a paper slide
      S.cloud(ac, out, t0 + .25, .75, 60, { bp: 3000, a: .035, d: [.02, .06], noise: 1 }, u => Math.sin(Math.PI * u));
      // edges being drawn: pencil grains
      S.cloud(ac, out, t0 + .9, .8, 45, { bp: 5200, q: 3, a: .03, d: [.01, .03] }, u => 1 - u * .5);
      S.grain(ac, out, t0 + 1.0, { bp: 1800, d: .02, a: .25 }); // crop: a click
      S.grain(ac, out, t0 + 1.12, { f: 880, d: .04, a: .12 });
      // coins: pay then spend
      const nC = COINS[V] || 4;
      for (let i = 0; i < nC; i++) {
        const ta = 1.3 + i * (.7 / nC) + .35; S.grain(ac, out, at(ta), { f: 2200 + K.hash(i) * 600, d: .05, a: .2, pan: .2, att: .05 });
        S.grain(ac, out, at(2.0 + i * (.5 / nC) + .35), { f: 1700 + K.hash(i + 9) * 500, d: .05, a: .14, pan: -.7, att: .05 });
      }
      S.say(ac, out, V, t0 + 1.5, 'sink', .9, .35);
      S.say(ac, out, A, at(1.45), 'step', 1, -.3);
      // debt rings: low ticks
      const dN = 2 + Math.round((mV.debt || 0) * 4);
      for (let i = 0; i < dN; i++) S.grain(ac, out, t0 + 1.5 + i * .08, { f: 220 - i * 10, d: .06, a: .1, pan: .2, att: .1 });
      if (doerB === 'copies') for (let i = 0; i < (A === 'O' ? 3 : 2); i++) { const w = at(1.95 + i * .25); S.grain(ac, out, w, { bp: 1400, d: .03, a: .3 }); S.grain(ac, out, w + .03, { f: 1320, d: .05, a: .1 }) }
      if (doerB === 'return') { S.say(ac, out, A, at(1.6), 'step', 1, 0); S.cloud(ac, out, at(1.9), .3, 120, { bp: 2500, a: .07, d: [.005, .02] }, u => 1 - u); S.grain(ac, out, at(2.4), { f: 2400, d: .08, a: .22, pan: .3 }); S.say(ac, out, A, at(2.45), 'react', .5, 0) }
      if (doerB === 'lose') { S.cloud(ac, out, t0 + 1.5, 1.2, 50, { bp: 2400, a: .04, d: [.02, .08] }, u => Math.sin(Math.PI * u)); S.say(ac, out, A, t0 + 1.6, 'breathe', .8, -.3); S.pluck(ac, out, t0 + 2.65, 76, .12, .8, .8) }
      if (mV.grudge >= .4) S.say(ac, out, V, t0 + 2.3, 'tick', 1, .4); else S.say(ac, out, V, t0 + 2.0, 'react', .6, .4);
    },
    trace(g, box, age, K) {             // a small photograph card with its id, yellowing and curling with age
      const a = Math.max(.25, 1 - age * .06), yl = Math.min(1, age * .1);
      const w = Math.min(box.w, box.h * 1.33), h = w * .75, x = box.x + (box.w - w) / 2, y = box.y + (box.h - h) / 2;
      g.save(); g.globalAlpha = a; g.translate(x + w / 2, y + h / 2); g.rotate(-.06 - age * .01);
      g.fillStyle = 'rgb(' + (246 - yl * 20) + ',' + (240 - yl * 40) + ',' + (226 - yl * 80) + ')'; g.fillRect(-w / 2, -h / 2, w, h);
      g.fillStyle = 'rgba(90,60,30,' + (.55 - yl * .25) + ')'; g.fillRect(-w / 2 + w * .1, -h / 2 + h * .12, w * .8, h * .62);
      g.fillStyle = '#1d1813'; g.fillRect(-w * .1, -h * .05, w * .28, h * .3);
      g.strokeStyle = '#b3372c'; g.lineWidth = Math.max(1, w * .02); g.strokeRect(w / 2 - w * .16, -h / 2 + h * .04, w * .12, w * .12);
      g.fillStyle = '#ded2b6'; g.beginPath(); g.moveTo(w / 2, h / 2); g.lineTo(w / 2 - w * (.1 + yl * .15), h / 2); g.lineTo(w / 2, h / 2 - w * (.1 + yl * .15)); g.fill();
      for (let i = 0; i < 8; i++) { g.fillStyle = '#1d1813'; const b = K.hash(i * 3.1 + 7) > .5; g.fillRect(-w / 2 + w * .1 + i * w * .09, h / 2 - h * .16 + (b ? 0 : h * .04), w * .05, h * (b ? .1 : .05)) }
      g.restore();
    }
  });
})();
