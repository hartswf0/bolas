// 06 · Threatening with a Gun — CONSEQUENCE · SCION 44 · Multiplane Parallax (spatial collage)
// Depth scene graph: every element is a flat cutout on a plane at depth z; one camera {x,y,z} projects
// each plane with scale s = ZS/(z - cam.z), so near planes slide more than far ones (parallax ratio = 1/z).
// The back wall is an occlusion plane with two holes (window, door); the yard, neighbours, fog and the
// police lamp live on planes beyond it. The revolver is a cutout that changes plane when it is hidden.
(function () {
  const W = 1920, H = 1080, ZS = 10, ZW = 14, SC = 1.3, FL = 340, DUR = 3.4, G = 2.9;
  const XA = -560, XV = 540;                       // doer left, victim right (deed continuity)
  const WIN = { x0: -80, x1: 620, y0: -380, y1: 200 }, DOOR = { x0: -520, x1: -300, y0: -330 };
  const EAR = { R: 70, B: 96, I: 92, O: 66 };
  const PAIRIDX = { R: 0, B: 1, I: 2, O: 3 };
  const cl = (a, b, x) => Math.max(a, Math.min(b, x));
  const sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u); };
  const lerp = (a, b, u) => a + (b - a) * u;
  const bump = (a, b, c, d, x) => sm(a, b, x) * (1 - sm(c, d, x));
  const D2R = Math.PI / 180;
  let C = { x: 0, y: 0, z: 0 }, HS = Math.sin;

  // ---------- camera + plane projection ----------
  function cam(t) {
    const u = sm(0.35, DUR - 0.45, t);
    return { x: 120 * u, y: -18 * u, z: 0.85 * u };
  }
  const sOf = z => ZS / (z - C.z);
  function plane(g, z) { const s = sOf(z); g.setTransform(s, 0, 0, s, W / 2 - C.x * s, H / 2 - C.y * s); return s; }
  const scr = (X, Y, z) => { const s = sOf(z); return { x: W / 2 + (X - C.x) * s, y: H / 2 + (Y - C.y) * s }; };
  // world X on plane z that projects to the same screen x as X on plane z0 (re-projection for hidden objects)
  const reproj = (X, z0, z1) => C.x + (X - C.x) * (z1 - C.z) / (z0 - C.z);

  // ---------- colour ----------
  const hx = c => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  function tone(c, grey, dark) {
    const [r, g, b] = hx(c), y = 0.3 * r + 0.59 * g + 0.11 * b;
    const f = v => Math.round(lerp(v, y * 0.85, grey) * (1 - dark));
    return `rgb(${f(r)},${f(g)},${f(b)})`;
  }

  // ---------- the revolver cutout: origin at grip, barrel along +x ----------
  function revolver(g, x, y, ang, sc, a) {
    g.save(); g.translate(x, y); g.rotate(ang); g.scale(G * sc, G * sc); g.globalAlpha *= a ?? 1;
    g.fillStyle = '#3c3e46'; g.beginPath(); g.moveTo(-3, -8); g.lineTo(-12, 12); g.quadraticCurveTo(-11, 17, -4, 16); g.lineTo(5, -2); g.closePath(); g.fill();
    g.fillStyle = '#5a4030'; g.beginPath(); g.moveTo(-4, -4); g.lineTo(-10, 11); g.lineTo(-5, 13); g.lineTo(2, -2); g.closePath(); g.fill();
    g.fillStyle = '#5d606b'; g.fillRect(-2, -13, 16, 10); g.beginPath(); g.arc(8, -8, 6.5, 0, 7); g.fill(); g.fillRect(12, -12, 34, 5); g.fillRect(43, -14, 3, 3);
    g.fillStyle = '#1d1c1f'; g.beginPath(); g.moveTo(-3, -13); g.lineTo(-7, -17); g.lineTo(-1, -14); g.fill();
    g.strokeStyle = '#2a292e'; g.lineWidth = 1.5; g.beginPath(); g.arc(6, -1, 4, 0.2, Math.PI - 0.2); g.stroke();
    g.strokeStyle = 'rgba(235,225,205,0.7)'; g.lineWidth = 1; g.beginPath(); g.moveTo(13, -11.5); g.lineTo(45, -11.5); g.stroke();
    g.restore();
  }

  // ---------- sack cutout: ears are two-segment tapered horns, body a soft sack, attribute layers on top ----------
  const dir = a => ({ x: Math.sin(a), y: -Math.cos(a) });
  function ear(g, bx, by, a1, a2, L, bw, side) {
    const d1 = dir(a1), d2 = dir(a2), m = { x: bx + d1.x * L * 0.5, y: by + d1.y * L * 0.5 }, tp = { x: m.x + d2.x * L * 0.5, y: m.y + d2.y * L * 0.5 };
    const n0 = { x: -d1.y, y: d1.x }, n1 = { x: -(d1.y + d2.y) / 2, y: (d1.x + d2.x) / 2 };
    g.beginPath();
    g.moveTo(bx + n0.x * bw / 2 - d1.x * 8, by + n0.y * bw / 2 - d1.y * 8);
    g.quadraticCurveTo(m.x + n1.x * bw * 0.36, m.y + n1.y * bw * 0.36, tp.x, tp.y);
    g.quadraticCurveTo(m.x - n1.x * bw * 0.36, m.y - n1.y * bw * 0.36, bx - n0.x * bw / 2 - d1.x * 8, by - n0.y * bw / 2 - d1.y * 8);
    g.closePath(); g.fill();
    return tp;
  }
  function bodyPath(g, w, h, id) {
    const r = Math.min(18, w * 0.12), sag = id === 'I' ? h * 0.2 : h * 0.05, wb = id === 'I' ? w * 0.54 : w / 2;
    g.beginPath(); g.moveTo(-wb + r, 0); g.lineTo(wb - r, 0); g.quadraticCurveTo(wb, 0, wb, -r);
    g.bezierCurveTo(wb + w * 0.04, -h * 0.4, w / 2 + w * 0.02, -h * 0.8, w / 2 * 0.94, -h);
    g.quadraticCurveTo(0, -h + sag, -w / 2 * 0.94, -h);
    g.bezierCurveTo(-w / 2 - w * 0.02, -h * 0.8, -wb - w * 0.04, -h * 0.4, -wb, -r);
    g.quadraticCurveTo(-wb, 0, -wb + r, 0); g.closePath();
  }
  // P: {sc, sq, lean, rot, aL:[a1,a2], aR:[a1,a2], grey, dark, alpha, halo, wig, tags, gunEar}
  function sack(g, K, id, X, Y, P) {
    const c = K.CAST[id], w = c.w * SC * P.sc, h = c.h * SC * P.sc * (P.sq || 1), L = EAR[id] * SC * P.sc * (P.earLen || 1);
    const bw = Math.min(w * 0.3, 44 * SC * P.sc) * (P.earW || 1), grey = P.grey || 0, dark = P.dark || 0;
    g.save(); g.translate(X, Y); if (P.rot) g.rotate(P.rot); g.transform(1, 0, -(P.lean || 0), 1, 0, 0); g.globalAlpha *= P.alpha ?? 1;
    const fill = tone(c.fill, grey, dark), seam = tone('#9c8360', grey, dark);
    g.save(); g.shadowColor = 'rgba(0,0,0,0.5)'; g.shadowBlur = 22; g.shadowOffsetX = 9; g.shadowOffsetY = 6;
    g.fillStyle = fill;
    const cxL = -w / 2 * 0.9, cxR = w / 2 * 0.9, cy = -h + 4;
    const tipL = ear(g, cxL, cy, -P.aL[0] * D2R, -P.aL[1] * D2R, L, bw, -1);
    const tipR = ear(g, cxR, cy, P.aR[0] * D2R, P.aR[1] * D2R, L, bw, 1);
    bodyPath(g, w, h, id); g.fill(); g.restore();
    // shading: lamp at left, so the right side and the base fall into shade
    bodyPath(g, w, h, id); g.save(); g.clip();
    const gr = g.createLinearGradient(-w / 2, 0, w / 2, 0); gr.addColorStop(0, 'rgba(255,230,180,0.18)'); gr.addColorStop(0.6, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(20,10,0,0.35)');
    g.fillStyle = gr; g.fillRect(-w, -h - 10, 2 * w, h + 10);
    const gb = g.createLinearGradient(0, -h * 0.3, 0, 0); gb.addColorStop(0, 'rgba(0,0,0,0)'); gb.addColorStop(1, 'rgba(20,10,0,0.25)'); g.fillStyle = gb; g.fillRect(-w, -h * 0.3, 2 * w, h * 0.3);
    if (id === 'R') { // maroon shawl band, top fifth, with fringe
      g.fillStyle = tone('#6e3a33', grey, dark); g.fillRect(-w, -h - 10, 2 * w, h * 0.2 + 10);
      for (let i = -6; i <= 6; i++) { g.beginPath(); g.moveTo(i * w / 13 - 6, -h * 0.8); g.lineTo(i * w / 13, -h * 0.8 + 10); g.lineTo(i * w / 13 + 6, -h * 0.8); g.fill(); }
      if (P.lump) { g.fillStyle = tone('#5a2d28', grey, dark); g.beginPath(); g.ellipse(w * 0.12, -h * 0.84, w * 0.2 * P.lump, h * 0.12 * P.lump, 0, 0, 7); g.fill(); g.fillStyle = tone('#5d606b', grey, dark); g.fillRect(w * 0.12 + w * 0.16 * P.lump, -h * 0.85, 22 * P.lump, 7); }
    }
    if (id === 'B') { // belt at 40% and the wheat stencil
      g.fillStyle = tone('#2a2622', grey, dark); g.fillRect(-w, -h * 0.4 - h * 0.045, 2 * w, h * 0.09);
      g.fillStyle = tone('#8a7a50', grey, dark); g.fillRect(-10, -h * 0.4 - h * 0.035, 20, h * 0.07);
      g.strokeStyle = tone('#8a6a3c', grey, dark); g.lineWidth = 4; g.beginPath(); g.arc(0, -h * 0.68, h * 0.14, 0, 7); g.stroke();
      g.beginPath(); g.moveTo(0, -h * 0.57); g.lineTo(0, -h * 0.79);
      for (let k = 0; k < 4; k++) { const yy = -h * (0.64 + k * 0.04); g.moveTo(0, yy); g.lineTo(-12, yy - 10); g.moveTo(0, yy); g.lineTo(12, yy - 10); } g.stroke();
    }
    if (id === 'I') { // patched, half empty
      g.fillStyle = tone('#c4ad84', grey, dark); g.fillRect(w * 0.08, -h * 0.55, w * 0.22, h * 0.24);
      g.strokeStyle = seam; g.setLineDash([4, 5]); g.lineWidth = 2; g.strokeRect(w * 0.08, -h * 0.55, w * 0.22, h * 0.24); g.setLineDash([]);
    }
    if ((P.tags || []).includes('torn')) { g.strokeStyle = '#3a2d20'; g.lineWidth = 3; g.beginPath(); g.moveTo(-w * 0.2, -h * 0.5); for (let k = 1; k < 6; k++) g.lineTo(-w * 0.2 + k * w * 0.06, -h * 0.5 + (k % 2 ? 9 : -9)); g.stroke(); }
    g.restore();
    // side seams
    g.strokeStyle = seam; g.lineWidth = 2; g.setLineDash([5, 7]);
    g.beginPath(); g.moveTo(-w / 2 + 10, -8); g.lineTo(-w / 2 * 0.88, -h + 10); g.moveTo(w / 2 - 10, -8); g.lineTo(w / 2 * 0.88, -h + 10); g.stroke(); g.setLineDash([]);
    // halo lever: the light finds its edge
    if (P.halo > 0.02) { bodyPath(g, w, h, id); g.strokeStyle = `rgba(255,226,160,${0.15 + 0.6 * P.halo})`; g.lineWidth = 3 + 5 * P.halo; g.stroke(); }
    if (id === 'O') { // purple wig, long past the shoulders; lifts when it hides something
      const wl = P.wig || 0, bumpW = P.wigBump || 0;
      g.save(); g.translate(0, -wl * 70); g.rotate(-wl * 0.12);
      g.fillStyle = tone('#7a3b8f', grey, dark); g.strokeStyle = tone('#3c1748', grey, dark); g.lineWidth = 3;
      g.beginPath(); g.moveTo(-w * 0.62, -h * 0.42); g.quadraticCurveTo(-w * 0.72, -h * 0.9, -w * 0.4, -h - 14 - bumpW * 16);
      g.quadraticCurveTo(0, -h - 34 - bumpW * 30, w * 0.4, -h - 14 - bumpW * 16); g.quadraticCurveTo(w * 0.72, -h * 0.9, w * 0.62, -h * 0.42);
      g.lineTo(w * 0.36, -h * 0.46); g.quadraticCurveTo(w * 0.4, -h * 0.86, 0, -h * 0.9); g.quadraticCurveTo(-w * 0.4, -h * 0.86, -w * 0.36, -h * 0.46); g.closePath();
      g.fill(); g.stroke();
      g.strokeStyle = 'rgba(200,150,220,0.35)'; g.lineWidth = 2;
      for (const f of [-0.5, -0.25, 0.25, 0.5]) { g.beginPath(); g.moveTo(f * w * 0.8, -h - 10); g.quadraticCurveTo(f * w * 1.2, -h * 0.8, f * w * 1.25, -h * 0.48); g.stroke(); }
      g.restore();
    }
    g.restore();
    const sh = (p) => ({ x: X + p.x - (P.lean || 0) * p.y, y: Y + p.y });
    return { tipL: sh(tipL), tipR: sh(tipR), top: { x: X, y: Y - h }, w, h };
  }

  function sackGeom(K, id, X, Y, P) {
    const c = K.CAST[id], w = c.w * SC * P.sc, h = c.h * SC * P.sc * (P.sq || 1), L = EAR[id] * SC * P.sc * (P.earLen || 1);
    const tipOf = (bx, by, a1, a2) => { const d1 = dir(a1), d2 = dir(a2); return { x: bx + (d1.x + d2.x) * L / 2, y: by + (d1.y + d2.y) * L / 2 }; };
    const sh = p => ({ x: X + p.x - (P.lean || 0) * p.y, y: Y + p.y });
    return { tipL: sh(tipOf(-w / 2 * 0.9, -h + 4, -P.aL[0] * D2R, -P.aL[1] * D2R)), tipR: sh(tipOf(w / 2 * 0.9, -h + 4, P.aR[0] * D2R, P.aR[1] * D2R)), top: { x: X, y: Y - h }, w, h };
  }
  // ---------- reading the ledger into the beat's branch state ----------
  function readState(ev, st, X) {
    const A = ev.A, V = ev.V, L = X && X.ledger;
    const before = L ? L.states[ev.k] : st;
    const aDead = !st.alive[A], vDead = !st.alive[V];
    const ids = ['R', 'B', 'I', 'O'], nDead = ids.filter(s => !st.alive[s]).length;
    const killer = st.evidence.some(e => e.A === A && e.k < ev.k && !e.refused && st.deadAt[e.V] === e.k);
    const police = nDead >= 1 || killer; // a disappearance, or a killer holding the gun, brings the lamp to the fence
    // the house's estimate of the doer's danger raises how many neighbours wake
    let harm = 0; for (const o of ids) harm += st.belief[o][A].harm.m; harm /= 4;
    const nWin = cl(3, 16, Math.round(4 + 4 * nDead + 6 * harm + (killer ? 3 : 0)));
    let wit = null, best = -1;
    for (const s of ids) if (s !== A && s !== V && st.alive[s]) { const m = st.mind[s][A] || {}; const sc = (m.fear || 0) + (m.grudge || 0) + 0.1 * st.know[s].length + (s === 'R' ? 0.05 : 0); if (sc > best) { best = sc; wit = s; } }
    const wm = wit ? st.mind[wit][A] : null;
    const witFlees = wit ? (wm.fear + 0.2 >= wm.grudge + wm.desire) : false;
    const mA = st.mind[A][V], guilty = mA.guilt > mA.pride, fear = vDead ? 0 : cl(0.35, 1, st.mind[V][A].fear);
    const LA = st.levers[A], LV = st.levers[V], LA0 = before.levers[A], LV0 = before.levers[V];
    return { A, V, aDead, vDead, nDead, killer, police, harm, nWin, wit, witFlees, guilty, fear, LA, LV, LA0, LV0, tagsA: st.body[A], tagsV: st.body[V] };
  }

  // ---------- the outside: houses, windows, fog, lamp (planes beyond the wall) ----------
  const HOUSES = [ // z, x0 (window-fraction world units at z=24 scale), width, roofY, rows, cols, groundY
    { z: 24, x0: -360, w: 520, top: -560, rows: 2, cols: 2, tone: '#1b2230' },
    { z: 34, x0: 380, w: 700, top: -720, rows: 2, cols: 3, tone: '#182030' },
    { z: 60, x0: -900, w: 1300, top: -520, rows: 1, cols: 4, tone: '#161d2a' },
    { z: 60, x0: 900, w: 1100, top: -640, rows: 2, cols: 3, tone: '#141b28' }];
  const GROUND = 400;
  function windowsList() {
    const out = []; HOUSES.forEach((hs, hi) => {
      for (let r = 0; r < hs.rows; r++) for (let c = 0; c < hs.cols; c++) {
        const ww = hs.w / (hs.cols * 2 + 1), wh = Math.min(170, (GROUND - hs.top) / (hs.rows * 2 + 1.5));
        const x = hs.x0 + ww * (1 + c * 2), y = hs.top + 120 + wh * (0.4 + r * 2);
        out.push({ hi, z: hs.z, x, y, w: ww, h: wh, ord: hs.z + 40 * K0hash(hi * 13 + r * 5 + c * 3) });
      }
    });
    out.sort((a, b) => a.ord - b.ord); return out;
  }
  let K0hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const WINS = windowsList();
  const winOn = (i, t) => 0.3 + i * 0.14;
  function lampPath(t, B) {
    if (B.police) { const u = sm(0.6, 2.3, t); return { z: lerp(85, 19.5, u), X: lerp(1500, 420, u), Y: GROUND - 120 - 8 * Math.abs(Math.sin(t * 7)), a: sm(0.6, 0.9, t), swing: Math.sin(t * 3.2) * 0.25 }; }
    const u = sm(0.6, 3.2, t); return { z: 70, X: lerp(2600, -900, u), Y: GROUND - 120 - 6 * Math.abs(Math.sin(t * 7)), a: sm(0.6, 0.9, t) * (1 - sm(2.4, 3.1, t)), swing: 0 };
  }
  function fogPlane(g, z, t, a, seed) {
    plane(g, z); const sp = 1.2 * z;
    for (let k = 0; k < 9; k++) {
      const x = (K0hash(seed + k) - 0.3) * 120 * z + t * 9 * z * (K0hash(seed + k * 3) - 0.5), y = GROUND - 120 + (K0hash(seed + k * 7) - 0.5) * 18 * z;
      const r = (40 + 50 * K0hash(seed + k * 11)) * z * 0.4;
      const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, `rgba(120,135,150,${a})`); gr.addColorStop(1, 'rgba(120,135,150,0)');
      g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r);
    }
    g.fillStyle = `rgba(90,105,120,${a * 0.5})`; g.fillRect(-sp * 60, GROUND - 260, sp * 120, 600);
  }
  function drawLamp(g, t, B, lp) {
    if (lp.a <= 0.01) return;
    const s = plane(g, lp.z), near = cl(0, 1, (60 - lp.z) / 40);
    g.save(); g.translate(lp.X, lp.Y); g.rotate(lp.swing);
    const R = 260 * (1 + near), gr = g.createRadialGradient(0, 0, 0, 0, 0, R);
    gr.addColorStop(0, `rgba(255,236,190,${0.95 * lp.a})`); gr.addColorStop(0.08, `rgba(255,210,140,${0.6 * lp.a})`); gr.addColorStop(1, 'rgba(255,200,120,0)');
    g.globalCompositeOperation = 'lighter'; g.fillStyle = gr; g.fillRect(-R, -R, 2 * R, 2 * R);
    if (B.police) { // the beam, swinging toward the house window
      const ang = -Math.PI * 0.62 + Math.sin(t * 1.7) * 0.25 + sm(1.8, 2.4, t) * 0.5;
      g.rotate(ang); const bl = 1400, bg = g.createLinearGradient(0, 0, bl, 0); bg.addColorStop(0, `rgba(255,230,170,${0.35 * lp.a})`); bg.addColorStop(1, 'rgba(255,230,170,0)');
      g.fillStyle = bg; g.beginPath(); g.moveTo(0, 0); g.lineTo(bl, -260); g.lineTo(bl, 260); g.closePath(); g.fill();
    }
    g.globalCompositeOperation = 'source-over';
    g.fillStyle = '#0b0d12'; g.fillRect(-14, -26, 28, 40); g.fillStyle = '#ffe9b8'; g.globalAlpha = lp.a; g.fillRect(-9, -18, 18, 24); g.globalAlpha = 1;
    // the constable: a cut silhouette carrying the lamp
    g.fillStyle = '#07090d'; g.beginPath(); g.moveTo(30, 120); g.lineTo(34, -60); g.quadraticCurveTo(70, -110, 106, -60); g.lineTo(110, 120); g.closePath(); g.fill();
    g.beginPath(); g.ellipse(70, -96, 30, 24, 0, 0, 7); g.fill(); g.fillRect(44, -124, 52, 18); g.fillRect(36, -110, 68, 6);
    g.strokeStyle = `rgba(255,220,160,${0.7 * lp.a})`; g.lineWidth = 5; g.beginPath(); g.moveTo(34, 110); g.lineTo(36, -58); g.quadraticCurveTo(52, -84, 66, -86); g.moveTo(40, -96); g.quadraticCurveTo(42, -116, 60, -124); g.stroke();
    g.restore();
  }
  function outside(g, t, B) {
    // sky + far valley (z 200 / 120)
    plane(g, 200); const sk = g.createLinearGradient(0, -6000, 0, 3000); sk.addColorStop(0, '#05070d'); sk.addColorStop(0.7, '#1a2333'); sk.addColorStop(1, '#2a3444');
    g.fillStyle = sk; g.fillRect(-30000, -20000, 60000, 40000);
    g.fillStyle = '#d8dccf'; g.beginPath(); g.arc(4200, -3800, 260, 0, 7); g.fill();
    g.fillStyle = 'rgba(216,220,207,0.12)'; g.beginPath(); g.arc(4200, -3800, 700, 0, 7); g.fill();
    plane(g, 120); g.fillStyle = '#121925'; g.beginPath(); g.moveTo(-20000, 900); for (let k = 0; k <= 40; k++) g.lineTo(-20000 + k * 1000, 300 - 300 * K0hash(k * 2.3)); g.lineTo(20000, 900); g.closePath(); g.fill();
    for (let k = 0; k < 70; k++) { const x = (K0hash(k * 1.7) - 0.5) * 16000, y = 260 + 200 * K0hash(k * 3.1); g.fillStyle = `rgba(255,200,120,${0.25 + 0.35 * K0hash(k * 5.3)})`; g.fillRect(x, y, 22, 14); }
    fogPlane(g, 85, t, 0.3, 3);
    // houses back to front, lamp and fog interleaved in depth
    const lp = lampPath(t, B); let lampDrawn = false;
    const layers = [{ z: 60, f: () => { houses(g, t, B, 60); } }, { z: 45, f: () => fogPlane(g, 45, t, 0.3, 11) }, { z: 34, f: () => houses(g, t, B, 34) },
      { z: 28, f: () => fogPlane(g, 28, t, 0.26, 17) }, { z: 24, f: () => houses(g, t, B, 24) }, { z: 20.5, f: () => fogPlane(g, 20.5, t, 0.2, 23) }, { z: 17.5, f: () => yard(g, t) }];
    for (const Ly of layers) { if (!lampDrawn && lp.z > Ly.z) { drawLamp(g, t, B, lp); lampDrawn = true; } Ly.f(); }
    if (!lampDrawn) drawLamp(g, t, B, lp);
  }
  function houses(g, t, B, z) {
    plane(g, z); const k = z / 24;
    HOUSES.forEach((hs, hi) => {
      if (hs.z !== z) return; const x0 = hs.x0 * k, w = hs.w * k;
      g.fillStyle = hs.tone; g.beginPath(); g.moveTo(x0, GROUND + 900); g.lineTo(x0, hs.top); g.lineTo(x0 + w * 0.5, hs.top - 220 * k); g.lineTo(x0 + w, hs.top); g.lineTo(x0 + w, GROUND + 900); g.closePath(); g.fill();
      g.fillRect(x0 + w * 0.7, hs.top - 300 * k, 50 * k, 200 * k); // chimney
    });
    WINS.forEach((wd, i) => {
      if (wd.z !== z) return; const x = wd.x * k, w = wd.w * k, h = wd.h;
      const on = i < B.nWin ? sm(winOn(i), winOn(i) + 0.12, t) : 0;
      g.fillStyle = '#0a0e15'; g.fillRect(x, wd.y, w, h);
      if (on > 0) {
        g.fillStyle = `rgba(242,196,106,${on})`; g.fillRect(x, wd.y, w, h);
        // someone at the curtain: a sliver of silhouette in the lit pane
        const pk = K0hash(i * 9.1); g.fillStyle = `rgba(30,20,10,${on * 0.8})`; g.beginPath(); g.ellipse(x + w * (0.3 + 0.4 * pk), wd.y + h * 0.75, w * 0.18, h * 0.45, 0, Math.PI, 0); g.fill();
        g.globalCompositeOperation = 'lighter'; const R = Math.max(w, h) * 1.6, cxw = x + w / 2, cyw = wd.y + h / 2;
        const gr = g.createRadialGradient(cxw, cyw, 0, cxw, cyw, R); gr.addColorStop(0, `rgba(242,180,90,${0.35 * on})`); gr.addColorStop(1, 'rgba(242,180,90,0)'); g.fillStyle = gr; g.fillRect(cxw - R, cyw - R, 2 * R, 2 * R);
        g.globalCompositeOperation = 'source-over';
      }
      g.strokeStyle = '#06080c'; g.lineWidth = 4 * k; g.strokeRect(x, wd.y, w, h); g.beginPath(); g.moveTo(x + w / 2, wd.y); g.lineTo(x + w / 2, wd.y + h); g.stroke();
    });
  }
  function yard(g, t) { // fence, clothesline, bare tree: the nearest outdoor plane
    plane(g, 17.5);
    g.fillStyle = '#0c1018';
    for (let x = -800; x < 1400; x += 46) { g.beginPath(); g.moveTo(x, GROUND + 400); g.lineTo(x, 130); g.lineTo(x + 14, 112); g.lineTo(x + 28, 130); g.lineTo(x + 28, GROUND + 400); g.fill(); }
    g.fillRect(-800, 170, 2200, 14); g.fillRect(-800, 300, 2200, 14);
    g.strokeStyle = '#0c1018'; g.lineWidth = 16; g.beginPath(); g.moveTo(1040, GROUND + 400); g.lineTo(1020, -200); g.moveTo(1022, -60); g.lineTo(880, -360); g.moveTo(1020, -150); g.lineTo(1180, -420); g.moveTo(940, -240); g.lineTo(860, -300); g.stroke();
    g.lineWidth = 3; g.beginPath(); g.moveTo(-600, -150); g.quadraticCurveTo(200, -90, 1020, -160); g.stroke();
    g.fillStyle = '#1a202b'; g.fillRect(-120, -132, 70, 110); g.fillRect(140, -120, 90, 70);
  }

  // ---------- the room ----------
  function backWall(g, t, B, shadowFn) {
    plane(g, ZW);
    const hole = () => { g.beginPath(); g.rect(-6000, -4000, 12000, 8000); g.rect(WIN.x0, WIN.y0, WIN.x1 - WIN.x0, WIN.y1 - WIN.y0); g.rect(DOOR.x0, DOOR.y0, DOOR.x1 - DOOR.x0, FL - DOOR.y0); };
    g.fillStyle = '#2b1f17'; hole(); g.fill('evenodd');
    g.save(); hole(); g.clip('evenodd');
    g.fillStyle = 'rgba(0,0,0,0.18)'; for (let x = -3000; x < 3000; x += 70) g.fillRect(x, -4000, 26, 8000);
    g.fillStyle = '#3a2a1e'; g.fillRect(-6000, 160, 12000, 12); g.fillStyle = '#231910'; g.fillRect(-6000, FL - 40, 12000, 40);
    // lamp pool on the wall
    const lp = g.createRadialGradient(-860, 120, 0, -860, 120, 1100); lp.addColorStop(0, 'rgba(255,190,110,0.32)'); lp.addColorStop(1, 'rgba(255,190,110,0)'); g.fillStyle = lp; g.fillRect(-3000, -2000, 6000, 4000);
    g.restore();
    // window frame, sill, mullions (occlusion edges)
    g.fillStyle = '#17100b'; g.fillRect(WIN.x0 - 20, WIN.y0 - 20, WIN.x1 - WIN.x0 + 40, 20); g.fillRect(WIN.x0 - 20, WIN.y1, WIN.x1 - WIN.x0 + 40, 26);
    g.fillRect(WIN.x0 - 20, WIN.y0, 20, WIN.y1 - WIN.y0); g.fillRect(WIN.x1, WIN.y0, 20, WIN.y1 - WIN.y0);
    g.fillRect((WIN.x0 + WIN.x1) / 2 - 7, WIN.y0, 14, WIN.y1 - WIN.y0); g.fillRect(WIN.x0, (WIN.y0 + WIN.y1) / 2 - 6, WIN.x1 - WIN.x0, 12);
    // door frame
    g.fillRect(DOOR.x0 - 16, DOOR.y0 - 16, DOOR.x1 - DOOR.x0 + 32, 16); g.fillRect(DOOR.x0 - 16, DOOR.y0, 16, FL - DOOR.y0); g.fillRect(DOOR.x1, DOOR.y0, 16, FL - DOOR.y0);
    // the picture-rail shelf above the doer (Belindo's hiding place)
    g.fillStyle = '#1c130d'; g.fillRect(-800, -70, 260, 16); g.fillRect(-780, -54, 14, 30); g.fillRect(-574, -54, 14, 30);
  }
  function curtains(g, t) {
    plane(g, 13.3);
    for (const [x0, sgn] of [[WIN.x0 - 70, 1], [WIN.x1 + 70, -1]]) {
      g.fillStyle = '#4a1f1c'; g.beginPath(); g.moveTo(x0, WIN.y0 - 40); g.lineTo(x0 + sgn * 130, WIN.y0 - 40);
      g.quadraticCurveTo(x0 + sgn * 70, (WIN.y0 + WIN.y1) / 2, x0 + sgn * 120 + Math.sin(t * 1.3) * 4, WIN.y1 + 60); g.lineTo(x0, WIN.y1 + 60); g.closePath(); g.fill();
      g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 4; for (let k = 1; k < 4; k++) { g.beginPath(); g.moveTo(x0 + sgn * k * 28, WIN.y0 - 40); g.lineTo(x0 + sgn * k * 24, WIN.y1 + 60); g.stroke(); }
    }
    g.fillStyle = '#160e0a'; g.fillRect(WIN.x0 - 90, WIN.y0 - 54, WIN.x1 - WIN.x0 + 180, 14);
  }
  function hall(g, t, B, K) {
    // the hall behind the door: its own plane, seen only through the door hole
    const z = 17.2, s = plane(g, z), x0 = reproj(DOOR.x0, ZW, z) - 60, x1 = reproj(DOOR.x1, ZW, z) + 60;
    const open = B.wit ? sm(0.45, 0.95, t) * (B.witFlees ? 1 - sm(1.95, 2.55, t) : 1) : 0;
    const gr = g.createLinearGradient(x0, 0, x1, 0); gr.addColorStop(0, '#5a3b20'); gr.addColorStop(1, '#2a1a10');
    g.fillStyle = open > 0.01 ? gr : '#120c08'; g.fillRect(x0, -1200, x1 - x0, 2000);
    g.fillStyle = open > 0.01 ? '#2a1a0e' : '#0c0806'; g.fillRect(x0, FL, x1 - x0, 900); g.fillStyle = 'rgba(0,0,0,0.4)'; g.fillRect(x0, FL - 26, x1 - x0, 26);
    if (B.wit && open > 0.01) {
      const wm = B.wit, Lw = B.wl, lean = B.witFlees ? -0.05 * sm(1.6, 2.0, t) : 0.12 * sm(1.0, 1.8, t) * (1 + Lw.loom);
      const turn = B.witFlees ? sm(1.5, 2.0, t) : 0;
      const ears = B.witFlees ? [lerp(20, 140, turn), lerp(30, 170, turn)] : [lerp(30, 12, sm(1.0, 1.6, t)), lerp(40, 8, sm(1.0, 1.6, t))];
      const earI = wm === 'I' ? [100, 168] : ears;
      sack(g, K, wm, reproj((DOOR.x0 + DOOR.x1) / 2, ZW, z) + (B.witFlees ? -40 * turn : 0), FL, { sc: 0.9 * (1 - 0.15 * Lw.shrink), lean, aL: earI, aR: earI, grey: Lw.grey, dark: 0.15, halo: 0, tags: [] });
    }
    return open;
  }
  function doorLeaf(g, open) {
    plane(g, ZW); const w = DOOR.x1 - DOOR.x0, cover = w * (1 - open);
    g.fillStyle = '#20150d'; g.fillRect(DOOR.x0, DOOR.y0, cover, FL - DOOR.y0);
    g.fillStyle = 'rgba(255,200,120,0.12)'; g.fillRect(DOOR.x0 + cover - 6, DOOR.y0, 6, FL - DOOR.y0);
    g.fillStyle = '#b08a4a'; if (cover > 40) { g.beginPath(); g.arc(DOOR.x0 + cover - 26, 60, 7, 0, 7); g.fill(); }
    if (open < 0.02) { g.fillStyle = 'rgba(255,190,110,0.25)'; g.fillRect(DOOR.x0, FL - 5, w, 5); }
  }
  function floorAndSide(g, t) {
    g.setTransform(1, 0, 0, 1, 0, 0);
    const a = scr(-6000, FL, ZW), b = scr(6000, FL, ZW);
    const fg = g.createLinearGradient(0, a.y, 0, H); fg.addColorStop(0, '#1d140e'); fg.addColorStop(1, '#3a2a1c');
    g.fillStyle = fg; g.fillRect(0, a.y, W, H - a.y + 2);
    // boards recede between the wall plane and the landing edge: true perspective from the plane projection
    g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 2;
    for (let X = -2400; X <= 2400; X += 150) { const p = scr(X, FL, ZW), q = scr(X, FL, 6.2); g.beginPath(); g.moveTo(p.x, p.y); g.lineTo(q.x, q.y); g.stroke(); }
    for (const z of [13, 12, 11.2, 10.4, 9.6, 8.6, 7.6]) { const p = scr(0, FL, z); g.globalAlpha = 0.25; g.beginPath(); g.moveTo(0, p.y); g.lineTo(W, p.y); g.stroke(); g.globalAlpha = 1; }
    // right side wall: a quad spanning z 14 -> 5
    const X = 800, p1 = scr(X, -1600, ZW), p2 = scr(X, FL, ZW), p3 = scr(X, FL, 5), p4 = scr(X, -1600, 5);
    g.fillStyle = '#1a120c'; g.beginPath(); g.moveTo(p1.x, p1.y); g.lineTo(p2.x, p2.y); g.lineTo(p3.x, p3.y); g.lineTo(p4.x, p4.y); g.closePath(); g.fill();
    g.strokeStyle = 'rgba(0,0,0,0.5)'; g.lineWidth = 3; g.beginPath(); g.moveTo(p1.x, p1.y); g.lineTo(p2.x, p2.y); g.stroke();
  }
  function furniture(g, t, K) {
    plane(g, 10.8);
    // sideboard with the lamp: the room's light source
    g.fillStyle = '#24180f'; g.fillRect(-1060, 200, 240, 140); g.fillStyle = '#1a110a'; g.fillRect(-1050, 215, 220, 50); g.fillRect(-1050, 275, 220, 50);
    g.fillStyle = '#3b2a18'; g.fillRect(-950, 160, 18, 40); g.fillStyle = '#e0b878'; g.beginPath(); g.moveTo(-1000, 165); g.lineTo(-880, 165); g.lineTo(-905, 95); g.lineTo(-975, 95); g.closePath(); g.fill();
    g.globalCompositeOperation = 'lighter'; const gl = g.createRadialGradient(-940, 150, 0, -940, 150, 520); gl.addColorStop(0, 'rgba(255,200,120,0.35)'); gl.addColorStop(1, 'rgba(255,200,120,0)'); g.fillStyle = gl; g.fillRect(-1500, -400, 1100, 1000); g.globalCompositeOperation = 'source-over';
  }
  function rug(g, lift) { // Inigo's hiding place: a rug on the floor, drawn as a floor-plane quad
    g.setTransform(1, 0, 0, 1, 0, 0);
    const p = [scr(-470, FL, 10.7), scr(-110, FL, 10.7), scr(-60, FL, 9.4), scr(-500, FL, 9.4)];
    g.fillStyle = '#4a2420'; g.beginPath(); g.moveTo(p[0].x, p[0].y); for (const q of p.slice(1)) g.lineTo(q.x, q.y); g.closePath(); g.fill();
    g.strokeStyle = '#7a4a2a'; g.lineWidth = 4; g.stroke();
    return p;
  }
  function landing(g, t) { // foreground plane z 5.6: the stair balusters we watch through (shield)
    const s = plane(g, 5.6); g.fillStyle = '#0d0907';
    g.fillRect(-1200, 236, 2600, 18);
    for (let x = -1000; x <= 1400; x += 150) { g.beginPath(); g.moveTo(x - 7, 254); g.lineTo(x + 7, 254); g.lineTo(x + 10, 300); g.lineTo(x + 4, 316); g.lineTo(x + 8, 600); g.lineTo(x - 8, 600); g.lineTo(x - 4, 316); g.lineTo(x - 10, 300); g.closePath(); g.fill(); }
  }

  // ---------- performances ----------
  function victimPose(B, t, K) {
    const V = B.V, Lv = B.LV, f = B.fear, h = K.hash;
    const P = { sc: 1 - 0.14 * lerp(B.LV0.shrink, Lv.shrink, sm(0.4, 2.4, t)), grey: Math.max(Lv.grey, B.tagsV.includes('greyed') ? 0.6 : 0), halo: Lv.halo * 0.6, tags: B.tagsV };
    if (B.tagsV.includes('emptied')) P.sq = 0.72;
    if (B.vDead) { // a still sack: the hands never go up
      P.grey = Math.max(P.grey, 0.75); P.sq = (P.sq || 1) * 0.78; P.rot = 0.12; P.lean = 0.05;
      const e = V === 'I' ? [110, 175] : [100, 150]; P.aL = e; P.aR = e; return P;
    }
    // hands up, long after: they sag a little and are thrown back up when the lamp light passes
    const sag = (1 - f) * 0.5 * sm(1.0, 3.2, t), flinch = B.police ? bump(2.0, 2.15, 2.4, 2.9, t) : 0;
    const up = cl(0, 1, 1 - sag + flinch);
    const tr = Math.sin(t * (V === 'B' ? 23 : V === 'O' ? 41 : 17)) * (V === 'B' ? 3 : V === 'O' ? 1.2 : 2) * f;
    if (V === 'R') { const rock = Math.sin(t * 2.4) * 0.05; P.lean = rock; P.aL = [lerp(40, 6, up) + tr, lerp(50, 0, up) + tr]; P.aR = [lerp(40, 6, up) - tr, lerp(50, 0, up) - tr]; }
    if (V === 'B') { P.sq = (P.sq || 1) * (1 - 0.03 * up); P.aL = [lerp(45, 10, up) + tr, lerp(55, 4, up) + tr]; P.aR = [lerp(45, 10, up) - tr, lerp(55, 4, up) - tr]; P.lean = -0.04 * up; }
    if (V === 'I') { const flop = 8 + 26 * (0.5 + 0.5 * Math.sin(t * 2.2)) * (1 - flinch); P.aL = [lerp(100, 12, up), lerp(170, 12 + flop, up)]; P.aR = [lerp(100, 12, up), lerp(170, 12 + flop, up)]; P.earLen = 1; }
    if (V === 'O') { P.aL = [lerp(30, 4, up) + tr, lerp(30, 2, up) + tr]; P.aR = [lerp(30, 4, up) - tr, lerp(30, 2, up) - tr]; P.wig = 0.04 * Math.abs(Math.sin(t * 19)) * f; }
    P.earLen = (V === 'I' ? 1.1 : 1.35) * (0.8 + 0.3 * up); P.earW = 1.25;
    if (B.tagsV.includes('drowsy')) P.lean = (P.lean || 0) + Math.sin(t * 1.1) * 0.06;
    return P;
  }
  // the hide: each doer takes the gun somewhere in depth
  function doerAct(B, t, K) {
    const A = B.A, La = B.LA, tempo = 1 + 0.5 * cl(-0.5, 1, La.tempo);
    const h0 = (B.guilty ? 0.95 : 1.25) / tempo, h1 = h0 + 0.95 / tempo;
    const u = sm(h0, h1, t);
    const loom = lerp(B.LA0.loom, La.loom, sm(0.4, 2.6, t));
    const P = { sc: 1 + 0.12 * cl(-0.5, 1.2, loom), grey: Math.max(La.grey, B.tagsA.includes('greyed') ? 0.6 : 0), halo: La.halo * 0.7, tags: B.tagsA, lean: 0.05 * cl(0, 1.2, loom) };
    if (B.tagsA.includes('emptied')) P.sq = 0.72;
    let X = XA;
    const lower = B.guilty ? sm(0.45, h0, t) : 0;   // guilt lowers the aim before the hide
    let aim = lerp(86, 140, lower) + Math.sin(t * 5) * 1.2;
    const freeE = A === 'I' ? [100, 168] : [32, 42];
    P.aL = freeE; P.aR = A === 'I' ? [lerp(86, 120, sm(h0, h0 + 0.3, t)), lerp(88, 165, sm(h0, h0 + 0.3, t))] : [aim, aim + 2];
    let gun = { mode: 'ear', z: 10, a: 1 };
    if (B.aDead) { // a ghost doer: the gun falls through it and lies on the floor
      P.alpha = 0.32; P.grey = 1; P.halo = 0; P.lean = 0; P.aR = [lerp(86, 150, sm(0.5, 0.9, t)), lerp(88, 170, sm(0.5, 0.9, t))];
      gun = { mode: 'fall', t0: 0.55, x1: XA + 200, z: 10 };
      return { P, X, gun, u: 0, h0: 0.55, h1: 1.2 };
    }
    if (A === 'R') { // tucks it under her shawl: kept on her, like the takings
      P.aR = [lerp(aim, 10, sm(h0, h0 + 0.4, t)), lerp(aim + 2, -40, sm(h0, h0 + 0.4, t))];
      gun = { mode: 'path', to: 'shawl', u, z: 10 };
      P.lump = sm(0.6, 0.85, u);
      if (!B.guilty) P.aR = u > 0.85 ? [lerp(10, 30, sm(0.85, 1, u)), lerp(-40, 30, sm(0.85, 1, u)) + 12 * Math.sin(t * 9) * sm(0.85, 1, u) * (1 - sm(h1 + 0.4, h1 + 0.8, t))] : P.aR; // pats it
      P.lean += Math.sin(t * 2.2) * 0.03;
    }
    if (A === 'B') { // lifts it onto the shelf behind his own bulk: his body is the shield
      const up = sm(h0, h0 + 0.45, t), back = sm(h0 + 0.35, h1, t);
      P.aR = [lerp(aim, 8, up), lerp(aim + 2, -6, up)]; if (back > 0.9) P.aR = [lerp(8, 34, sm(0.9, 1, back)), lerp(-6, 44, sm(0.9, 1, back))];
      P.lean += -0.06 * bump(h0, h0 + 0.4, h1 - 0.1, h1 + 0.2, t);
      gun = { mode: 'shelf', u, up, back, z: lerp(10, 13.7, back) };
    }
    if (A === 'I') { // drops it, then idly nudges it half under the rug: in plain view
      gun = { mode: 'drop', t0: h0 + 0.1, u, z: 10 };
      P.aL = [lerp(100, 140, bump(h0 + 0.5, h0 + 0.7, h1, h1 + 0.2, t)), lerp(168, 175, 0)];
    }
    if (A === 'O') { // lifts the wig and hides it there: bald underneath
      const lift = bump(h0 + 0.05, h0 + 0.35, h0 + 0.65, h0 + 0.85, t);
      P.wig = lift; P.wigBump = sm(h0 + 0.6, h0 + 0.85, t);
      P.aR = [lerp(aim, 2, sm(h0, h0 + 0.35, t)), lerp(aim + 2, -20, sm(h0, h0 + 0.35, t))];
      if (t > h0 + 0.85) P.aR = [lerp(2, 30, sm(h0 + 0.85, h1, t)), lerp(-20, 38, sm(h0 + 0.85, h1, t))];
      P.aL = [lerp(32, 2, lift), lerp(42, 20, lift)];
      gun = { mode: 'wig', u, z: 10, lift };
    }
    // after-state: a corpse in front of it and the lamp coming makes the doer back away; else guilt goes back, pride looms
    if (B.vDead) {
      const go = sm(h1, h1 + 0.8, t); X -= 150 * go; P.sc *= 1 - 0.06 * go; P.lean -= 0.1 * go;
    } else if (B.guilty) {
      const go = sm(h1 + 0.05, h1 + 0.7, t); X += 90 * go * (A === 'B' ? 1.4 : 1);
      if (A !== 'I') P.aL = [lerp(P.aL[0], 70, go * 0.8), lerp(P.aL[1], 85, go * 0.8)];
      P.lean += 0.08 * go; P.sc *= 1 - 0.04 * go;
    } else {
      const st = sm(h1, h1 + 0.5, t); P.lean -= 0.05 * st; P.sc *= 1 + 0.03 * st * (1 + La.weight);
      const settle = Math.exp(-(t - h1) * 5) * Math.sin((t - h1) * 18) * (t > h1 ? 1 : 0); P.sq = (P.sq || 1) * (1 - 0.02 * settle * (1 + La.weight));
    }
    return { P, X, gun, u, h0, h1 };
  }
  function drawGun(g, t, K, act, mk, B) {
    const G0 = act.gun; if (!mk) return;
    const tip = mk.tipR, grip = (x, y, ang, z, a, sc) => { plane(g, z); revolver(g, x, y, ang, sc || 1, a); };
    const aimAng = (p) => Math.atan2(p.y - mk.top.y - mk.h * 0.0, 1) * 0;
    const earAng = (act.P.aR[1] - 90) * D2R;
    if (G0.mode === 'ear') { grip(tip.x - 8, tip.y + 10, earAng, 10, 1); return; }
    if (G0.mode === 'fall' || G0.mode === 'drop') {
      const t0 = G0.t0, s = cl(0, 1, (t - t0) / 0.42), x0 = XA + mk.w * 0.45 + 30;
      const y = s < 1 ? lerp(tip.y + 10, FL - 8, s * s) : FL - 8 - 14 * Math.abs(Math.sin((t - t0 - 0.42) * 9)) * Math.exp(-(t - t0 - 0.42) * 6);
      let x = t < t0 ? tip.x - 8 : lerp(tip.x - 8, x0 + 40, Math.min(1, (t - t0) / 0.6));
      let ang = t < t0 ? earAng : lerp(earAng, 0.08 + 0.9 * Math.PI, sm(t0, t0 + 0.5, t));
      if (G0.mode === 'drop') { const nud = sm(act.h0 + 0.7, act.h1 + 0.1, t); x += 70 * nud; }
      grip(x, y, ang, 10, 1); return;
    }
    if (G0.mode === 'path') { // Roessler: into the shawl
      const s = sm(0.25, 0.7, G0.u); if (s >= 1) return;
      const tx = mk.top.x + mk.w * 0.1, ty = mk.top.y + mk.h * 0.14;
      grip(lerp(tip.x - 8, tx, s), lerp(tip.y + 10, ty, s) - 40 * Math.sin(Math.PI * s), lerp(earAng, 1.4, s), 10, 1 - sm(0.55, 0.7, G0.u), 1 - 0.4 * s);
      return;
    }
    if (G0.mode === 'shelf') { // Belindo: up, then back in depth onto the wall shelf
      const z = G0.z, s0 = { x: tip.x - 8, y: tip.y + 10 };
      if (G0.back <= 0) { grip(s0.x, s0.y, earAng, 10, 1); return; }
      const shelf = { x: -700, y: -74 }, zx = lerp(reproj(s0.x, 10, z), shelf.x, G0.back), zy = lerp(s0.y, shelf.y, G0.back);
      grip(zx, zy, lerp(earAng, 0.02, G0.back), z, 1);
      return;
    }
    if (G0.mode === 'wig') {
      const s = sm(0.15, 0.55, G0.u); if (s >= 1) return;
      const tx = mk.top.x, ty = mk.top.y - 30;
      grip(lerp(tip.x - 8, tx, s), lerp(tip.y + 10, ty, s) - 30 * Math.sin(Math.PI * s), lerp(earAng, 0, s), 10, 1 - sm(0.45, 0.55, G0.u), 1 - 0.35 * s);
    }
  }
  function wallShadow(g, B, act, t, K) { // the doer's shadow on the wall: myth made visible (PREDATOR/BRUTE grows it)
    const sh = lerp(B.LA0.shadow, B.LA.shadow, sm(0.4, 2.6, t)), c = K.CAST[B.A];
    const k = 1.9 + 1.1 * cl(0, 1.5, sh), X = act.X + 330 + 80 * sh, a = B.aDead ? 0.1 : 0.3 + 0.3 * cl(0, 1, sh);
    g.save(); g.globalAlpha = a; g.translate(X, FL - 30); g.scale(k, k);
    const P = { ...act.P, grey: 1, dark: 0.95, halo: 0, alpha: 1, tags: [] };
    
    const m = sack(g, K, B.A, 0, 0, P);
    if (act.gun.mode === 'ear') { g.fillStyle = '#000'; g.save(); g.translate(m.tipR.x, m.tipR.y); g.rotate((act.P.aR[1] - 90) * D2R); g.fillRect(-6, -10, 60, 14); g.fillRect(-10, 0, 14, 30); g.restore(); }
    g.restore();
  }
  function beam(g, t, B) { // the police lamp's light coming through the window, sweeping the room
    if (!B.police) return;
    const a = bump(1.9, 2.15, 2.85, 3.25, t), x = lerp(900, -900, sm(1.95, 3.1, t));
    if (a < 0.01) return;
    plane(g, 10); g.save(); g.globalCompositeOperation = 'lighter';
    const gr = g.createLinearGradient(x - 160, 0, x + 160, 0); gr.addColorStop(0, 'rgba(255,230,170,0)'); gr.addColorStop(0.5, `rgba(255,230,170,${0.32 * a})`); gr.addColorStop(1, 'rgba(255,230,170,0)');
    g.fillStyle = gr; g.beginPath(); g.moveTo(x - 160, -260); g.lineTo(x + 60, -260); g.lineTo(x + 260, FL + 200); g.lineTo(x - 20, FL + 200); g.closePath(); g.fill();
    g.restore();
  }
  function dust(g, t, K) { // depth motes between planes: they show the air has thickness
    for (let k = 0; k < 40; k++) {
      const z = 6.5 + 7 * K.hash(k * 3.3); plane(g, z);
      const x = (K.hash(k * 7.7) - 0.5) * 2600 + t * 12 * (K.hash(k) - 0.5), y = -400 + 800 * K.hash(k * 1.9) + Math.sin(t * 0.8 + k) * 10;
      g.fillStyle = `rgba(255,220,170,${0.05 + 0.1 * K.hash(k * 5.1)})`; g.beginPath(); g.arc(x, y, 2.5, 0, 7); g.fill();
    }
  }

  function beat(g, t, ev, st, K, X) {
    C = cam(t); const B = readState(ev, st, X); B.wl = B.wit ? st.levers[B.wit] : null;
    g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    outside(g, t, B);
    const open = hall(g, t, B, K);
    const act = doerAct(B, t, K);
    backWall(g, t, B, null);
    doorLeaf(g, open);
    // the doer's shadow lives on the wall plane (door leaf included): it parallaxes with the wall, not the sack
    plane(g, ZW); g.save(); g.beginPath(); g.rect(-6000, -4000, 12000, 8000); g.rect(WIN.x0 - 20, WIN.y0 - 20, WIN.x1 - WIN.x0 + 40, WIN.y1 - WIN.y0 + 46); if (open > 0.02) { const cv = (DOOR.x1 - DOOR.x0) * (1 - open); g.rect(DOOR.x0 + cv, DOOR.y0, DOOR.x1 - DOOR.x0 - cv, FL - DOOR.y0); } g.clip('evenodd'); wallShadow(g, B, act, t, K); g.restore();
    curtains(g, t);
    floorAndSide(g, t); furniture(g, t, K);
    rug(g, 0);
    // subject plane: victim, doer, the revolver
    plane(g, 10);
    const vp = victimPose(B, t, K); sack(g, K, B.V, XV, FL, vp);
    if (B.vDead && B.tagsV.includes('emptied')) { g.fillStyle = 'rgba(251,247,238,0.7)'; g.beginPath(); g.ellipse(XV + 40, FL + 4, 170, 16, 0, 0, 7); g.fill(); }
    // the gun behind Belindo goes first (shield), every other gun in front
    let mk = null;
    if (act.gun.mode === 'shelf' && act.gun.back > 0) { drawGun(g, t, K, act, sackGeom(K, B.A, act.X, FL, act.P), B); plane(g, 10); }
    mk = sack(g, K, B.A, act.X, FL, act.P);
    if (B.A === 'I' && !B.aDead) { /* the rug lip drawn over the gun once nudged */ }
    if (!(act.gun.mode === 'shelf' && act.gun.back > 0)) drawGun(g, t, K, act, mk, B);
    if (B.A === 'I' && !B.aDead && t > act.h0 + 0.9) { // rug flap over the grip: half hidden, half in plain view
      g.setTransform(1, 0, 0, 1, 0, 0); const a = scr(XA + 200, FL - 22, 10), b2 = scr(XA + 330, FL + 6, 10);
      g.fillStyle = '#4a2420'; g.beginPath(); g.moveTo(a.x, b2.y); g.quadraticCurveTo((a.x + b2.x) / 2, a.y, b2.x, b2.y); g.closePath(); g.fill();
    }
    // coins on the floor if the doer carries them (blackmail/prostitution earlier)
    if (B.tagsA.includes('coins') && !B.aDead) { plane(g, 10); for (let k = 0; k < 5; k++) { g.fillStyle = '#c9a548'; g.beginPath(); g.ellipse(act.X - 120 + k * 14, FL - 4 - k * 6, 14, 5, 0, 0, 7); g.fill(); g.strokeStyle = '#7a5f20'; g.lineWidth = 2; g.stroke(); } }
    beam(g, t, B);
    dust(g, t, K);
    landing(g, t);
    // atmosphere: night vignette in screen space
    g.setTransform(1, 0, 0, 1, 0, 0);
    const vg = g.createRadialGradient(W * 0.45, H * 0.5, H * 0.3, W * 0.5, H * 0.5, H * 1.05); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.6)');
    g.fillStyle = vg; g.fillRect(0, 0, W, H);
  }

  // ---------- sound: depth audio — far events are quieter, duller and narrower ----------
  function sound(ac, out, t0, ev, st, K) {
    const S = K.SND, B = readState(ev, st, null), A = ev.A, V = ev.V;
    S.cloud(ac, out, t0, DUR, 30, { bp: 260, a: 0.012, d: [0.2, 0.5], spread: 1 }, u => 0.6 + 0.4 * Math.sin(Math.PI * u)); // fog bed
    for (let i = 0; i < B.nWin; i++) { // latches and shutters across the yard, nearer = louder, brighter
      const w = WINS[i], near = 24 / w.z, when = t0 + winOn(i) + 0.02, pan = cl(-1, 1, (w.x * w.z / 24 - 300) / 900);
      S.grain(ac, out, when, { bp: 900 + 2200 * near, q: 3, d: 0.03, a: 0.16 * near, pan, att: 0.1 });
      S.grain(ac, out, when + 0.05, { bp: 500 + 900 * near, q: 2, d: 0.08, a: 0.07 * near, pan });
    }
    if (B.police) { // boots on wet ground coming closer through the fog, then a whistle at the fence
      for (let k = 0; k < 12; k++) { const u = k / 11, when = t0 + 0.75 + u * 1.5; S.grain(ac, out, when, { bp: 300 + 900 * u, q: 2, d: 0.05, a: 0.03 + 0.12 * u * u, pan: 0.6 - 0.5 * u }); }
      S.grain(ac, out, t0 + 2.35, { f: 2350, d: 0.28, a: 0.06, glide: 0.06, noise: 0.25, pan: 0.15 });
      S.grain(ac, out, t0 + 2.68, { f: 2100, d: 0.4, a: 0.05, glide: -0.04, noise: 0.25, pan: 0.15 });
    } else { for (let k = 0; k < 8; k++) S.grain(ac, out, t0 + 0.8 + k * 0.28, { bp: 320, q: 2, d: 0.04, a: 0.025 * (1 - Math.abs(k - 4) / 5), pan: 1 - k * 0.25 }); }
    if (!B.vDead) { for (let k = 0; k < 4; k++) S.say(ac, out, V, t0 + 0.2 + k * 0.8, 'breathe', 0.6, 0.5); if (B.police) S.say(ac, out, V, t0 + 2.1, 'react', 0.6, 0.5); }
    const h0 = (B.guilty ? 0.95 : 1.25) / (1 + 0.5 * cl(-0.5, 1, st.levers[A].tempo));
    if (B.aDead || A === 'I') { const tt = B.aDead ? 0.55 : h0 + 0.1; S.grain(ac, out, t0 + tt + 0.42, { bp: 3200, q: 4, d: 0.05, a: 0.2, pan: -0.5 }); S.grain(ac, out, t0 + tt + 0.52, { bp: 2600, q: 4, d: 0.04, a: 0.1, pan: -0.5 }); }
    if (!B.aDead) { S.say(ac, out, A, t0 + h0 + 0.3, 'step', 0.8, -0.5); S.say(ac, out, A, t0 + h0 + 0.9, 'tick', 0.7, -0.5); if (B.guilty) { S.say(ac, out, A, t0 + h0 + 1.3, 'step', 0.6, -0.3); S.say(ac, out, A, t0 + h0 + 1.6, 'sink', 0.6, -0.3); } }
    if (B.wit) { S.say(ac, out, B.wit, t0 + 0.6, 'tick', 0.4, -0.2); if (B.witFlees) S.grain(ac, out, t0 + 2.5, { bp: 400, q: 2, d: 0.12, a: 0.1, pan: -0.2 }); }
  }

  // ---------- trace: the revolver's mark, wherever it was put, aging ----------
  function trace(g, box, age, K) {
    const a = Math.max(0.2, 1 - age * 0.09), s = Math.min(box.w / 150, box.h / 90);
    g.save(); g.translate(box.x + box.w * 0.25, box.y + box.h * 0.6); g.scale(s / G * 1.0, s / G * 1.0);
    revolver(g, 0, 0, -0.05 - age * 0.02, 1, a);
    // two raised marks above the barrel: the hands that went up and stayed up
    g.globalAlpha = a * 0.7; g.strokeStyle = '#d6bf96'; g.lineWidth = 6; g.lineCap = 'round';
    g.beginPath(); g.moveTo(170, -20); g.lineTo(180, -70 + age * 3); g.moveTo(205, -20); g.lineTo(198, -70 + age * 3); g.stroke();
    g.restore();
  }

  CONSEQ({
    deed: 'gun', n: 6, scion: 44, lineage: 'Multiplane Parallax — Spatial Collage Swarm',
    op: 'A camera glides and pushes past six depth planes (landing balusters, the sacks, the wall with window and door, the yard, neighbour houses in fog, the far valley) while the never-fired gun is moved to a hiding plane, neighbour windows light in depth order, and a police lamp walks forward through the fog planes when the ledger counts two dead or the doer is a killer.',
    made: 'Every element is a flat cutout on a plane at a depth z, projected by one camera; the back wall is an occluding plane with a window and a door cut in it, and the yard, three rows of neighbour houses, fog banks and the valley stand on planes behind it. The sacks are paper cutouts with tapered ears and their attribute layers, and the doer\'s shadow is a second cutout pinned to the wall plane, so it moves at the wall\'s parallax, not the sack\'s.',
    moved: 'Movement comes from the camera: a lateral glide with a slow push-in, so near planes slide fastest and the far valley barely moves, and the gun on Belindo\'s shelf or behind his bulk is revealed only by that parallax. The ledger moves the rest: how many windows light (deaths, the house\'s danger estimate), whether the lamp comes or passes, whether a third sack opens the door and stays or shuts it, guilt versus pride in the doer, fear in the victim\'s raised ears, and the myth levers (shadow, loom, shrink, halo, grey, tempo, weight).',
    dur: DUR, beat, sound, trace
  });
})();
