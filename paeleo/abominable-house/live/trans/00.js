// TRANSITION 00 · THE OPENING — SCION-50 · Library of Congress, Historical Print Stage.
// The film opens on a print: a hand-coloured engraved section of the boarding house, plate-marked,
// with the title engraved in its caption. The four sacks are engraved in their own rooms; the colourist's
// wash finds each one in turn and a catalogue bracket closes round it (solid corners = documented object).
// The moment a sack moves, its bracket turns dashed and its path is dotted (invented motion, marked as such).
// A scan crop closes on the parlour; the doer and victim of deed 0 come down through the house into it;
// the other two stay engraved in their rooms and are cropped out. Then the lamp is lit BEHIND the paper:
// transillumination. The paper glows amber, the ink spreads, and hatched poché becomes solid card — the
// print turns into the Reiniger shadow stage of deed 0 (the parlour is engraved on the deed's own set lines).
(function () {
const INK = '#2a1d14', PAPER = '#efe3c5', IDS = ['R', 'B', 'I', 'O'];
const FY = 862, DUR = 3.5;
const T_LIGHT = 2.5, T_FULL = 3.4;           // transillumination front: lamp lit behind the paper -> stage
const INTRO = { R: .22, B: .42, I: .62, O: .82 }; // colourist's wash + bracket per sack
const HOME = { R: [-560, FY], B: [2480, FY], I: [-160, -60], O: [1260, -60] };
const ATTR = { R: 'rgba(110,58,51,', B: 'rgba(42,38,34,', I: 'rgba(201,176,137,', O: 'rgba(122,59,143,' };
const off = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c };
let HOUSE = null; // {low, high}
const FIN = {};    // final composites per deed+pair

// ---------------- the engraved house (world coordinates; the parlour IS deed 0's stage, 1920x1080) ----------------
function hatch(q, x0, y0, x1, y1, ang, sp, lw, col) {
  q.save(); q.strokeStyle = col || INK; q.lineWidth = lw; q.beginPath();
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, r = Math.hypot(x1 - x0, y1 - y0) / 2 + 2;
  const ca = Math.cos(ang), sa = Math.sin(ang);
  for (let d = -r; d <= r; d += sp) { q.moveTo(cx - ca * r - sa * d, cy - sa * r + ca * d); q.lineTo(cx + ca * r - sa * d, cy + sa * r + ca * d) }
  q.stroke(); q.restore();
}
function poche(q, pathFn, bb, dense) { // section cut: outlined, double-hatched
  q.save(); q.beginPath(); pathFn(q); q.clip();
  q.fillStyle = 'rgba(42,29,20,.10)'; q.fillRect(bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]);
  hatch(q, bb[0], bb[1], bb[2], bb[3], .78, dense ? 7 : 9, 2.2);
  hatch(q, bb[0], bb[1], bb[2], bb[3], -.78, dense ? 9 : 13, 1.6);
  q.restore(); q.save(); q.beginPath(); pathFn(q); q.strokeStyle = INK; q.lineWidth = 4; q.stroke(); q.restore();
}
function wallTone(q, x0, y0, x1, y1, sp) { q.save(); q.beginPath(); q.rect(x0, y0, x1 - x0, y1 - y0); q.clip(); hatch(q, x0, y0, x1, y1, Math.PI / 2, sp || 14, 1.1, 'rgba(42,29,20,.45)'); q.restore() }
function drawHouse(q) {
  const H = K_.hash;
  // rooms: light vertical ruling for the back walls
  wallTone(q, -1060, -700, 900, -60, 16); wallTone(q, 960, -700, 3000, -60, 16);
  wallTone(q, -1060, 34, -60, FY, 15); wallTone(q, 1980, 34, 3000, FY, 15);
  // the parlour (deed 0's stage): radial ruling darker away from the lamp
  // the parlour (deed 0's stage): vertical ruling that swells away from the lamp (the engraver's tone for distance from light)
  q.save(); q.beginPath(); q.rect(34, 34, 1852, FY - 34); q.clip();
  for (let x = 40; x < 1886; x += 12) for (let y = 34; y < FY; y += 24) { const d = Math.hypot((x - 960) / 1.3, y - 260) / 1000; q.strokeStyle = `rgba(42,29,20,${Math.min(.75, .08 + d * .6)})`; q.lineWidth = .6 + 2.6 * d * d; q.beginPath(); q.moveTo(x, y); q.lineTo(x, y + 24); q.stroke() }
  q.restore();
  // parlour staircase: the deed's own step lines, engraved
  const stair = qq => { qq.moveTo(0, FY); for (let i = 0; i < 9; i++) { qq.lineTo(i * 34, FY - i * 46); qq.lineTo(i * 34 + 34, FY - i * 46) } qq.lineTo(306, FY - 9 * 46); qq.lineTo(0, FY - 9 * 46); qq.closePath() };
  q.save(); q.beginPath(); stair(q); q.clip(); hatch(q, 0, 400, 340, FY, .5, 8, 1.6); q.restore();
  q.beginPath(); stair(q); q.strokeStyle = INK; q.lineWidth = 3; q.stroke();
  q.fillStyle = INK; q.fillRect(0, FY - 9 * 46 - 14, 330, 14); for (let i = 1; i < 9; i++) q.fillRect(i * 34 + 20, FY - i * 46 - 70, 4, 70);
  // upper flight to the first floor through the stairwell
  q.save(); q.strokeStyle = INK; q.lineWidth = 3;
  q.beginPath(); for (let i = 0; i <= 11; i++) { const x = 330 + i * 30, y = 434 - i * 45; q.moveTo(x, y); q.lineTo(x + 30, y); q.lineTo(x + 30, y - 45) } q.stroke();
  q.beginPath(); q.moveTo(330, 434); q.lineTo(690, -60); q.lineWidth = 2; q.stroke(); q.restore();
  // arched door far right (same lines as the deed)
  const door = qq => { qq.moveTo(1590, FY); qq.lineTo(1590, 470); qq.arc(1680, 470, 90, Math.PI, 0); qq.lineTo(1770, FY); qq.closePath() };
  q.save(); q.beginPath(); door(q); q.clip(); hatch(q, 1580, 370, 1780, FY, Math.PI / 2, 7, 1.8); q.restore();
  q.beginPath(); door(q); q.lineWidth = 4; q.strokeStyle = INK; q.stroke(); q.strokeRect(1612, 480, 136, 380);
  q.beginPath(); q.arc(1735, 690, 7, 0, 7); q.fill(); q.fillRect(1732, 694, 6, 14); // keyhole (latent)
  // wallpaper sprigs
  for (let i = 0; i < 14; i++) { const x = 380 + i * 90, y = 300 + (i % 2) * 70; if (x > 1560) continue; q.lineWidth = 2; q.beginPath(); q.ellipse(x, y, 5, 11, .5, 0, 7); q.stroke(); q.beginPath(); q.ellipse(x + 9, y + 6, 5, 10, -.5, 0, 7); q.stroke() }
  // ceiling vault over the parlour = the deed's proscenium, cut in section
  const vault = qq => { qq.moveTo(-60, -60); qq.lineTo(1980, -60); qq.lineTo(1980, 300); qq.lineTo(1920, 300); qq.quadraticCurveTo(1880, 60, 1500, 34); qq.lineTo(420, 34); qq.quadraticCurveTo(40, 60, 0, 300); qq.lineTo(-60, 300); qq.closePath() };
  poche(q, qq => { vault(qq); }, [-60, -60, 1980, 300], true);
  // leaf scrolls of the cove
  q.fillStyle = INK; for (const s of [-1, 1]) for (let i = 0; i < 7; i++) { const x = s < 0 ? 60 + i * 52 : 1860 - i * 52, y = 60 + i * 6 + (i % 2) * 22; q.save(); q.translate(x, y); q.rotate(s * (.9 - i * .12)); q.beginPath(); q.ellipse(0, 18, 9, 22, 0, 0, 7); q.lineWidth = 2.4; q.stroke(); q.restore() }
  // stairwell opening
  q.fillStyle = PAPER; q.fillRect(340, -62, 360, 100); wallTone(q, 340, -60, 700, 34, 12);
  // walls and slabs in section
  for (const [x0, x1, y0, y1] of [[-60, 34, 34, 600], [1886, 1980, 34, 600], [-1120, -1060, -760, FY], [3000, 3060, -760, FY], [900, 960, -700, -60]]) poche(q, qq => qq.rect(x0, y0, x1 - x0, y1 - y0), [x0, y0, x1, y1]);
  for (const [x0, x1] of [[-1120, 340], [700, 3060]]) poche(q, qq => qq.rect(x0, -60, x1 - x0, 94), [x0, -60, x1, 34]);
  poche(q, qq => qq.rect(-1120, -760, 4180, 60), [-1120, -760, 3060, -700]);
  // floor slab and earth (= the deed's black floor)
  poche(q, qq => qq.rect(-1120, FY, 4180, 120), [-1120, FY, 3060, FY + 120], true);
  q.save(); q.beginPath(); q.rect(-1300, FY + 120, 4540, 110); q.clip(); for (let i = 0; i < 260; i++) { q.fillStyle = INK; q.beginPath(); q.arc(-1300 + H(i * 1.7) * 4540, FY + 125 + H(i * 2.9) * 100, 1.5 + H(i * 5.3) * 3, 0, 7); q.fill() } q.restore();
  q.strokeStyle = INK; q.lineWidth = 2.5; for (let x = -1100; x < 3040; x += 48) { if (x > -60 && x < 1980) { q.beginPath(); q.arc(x + 24, FY + 2, 9, Math.PI, 0); q.stroke() } }
  // the parlour lamp (unlit: a drawn wick)
  q.fillStyle = INK; q.fillRect(958, 30, 4, 58);
  q.beginPath(); q.moveTo(915, 120); q.quadraticCurveTo(960, 70, 1005, 120); q.lineTo(990, 128); q.lineTo(930, 128); q.closePath(); q.fill();
  for (let i = 0; i < 7; i++) { q.beginPath(); q.moveTo(926 + i * 11, 128); q.lineTo(931 + i * 11, 146); q.lineTo(936 + i * 11, 128); q.fill() }
  q.lineWidth = 2; q.beginPath(); q.ellipse(960, 140, 22, 14, 0, 0, 7); q.stroke();
  // doorways in the ground-floor party walls
  for (const x of [-60, 1886]) { q.fillStyle = PAPER; q.fillRect(x - 2, 600, 98, FY - 600); q.strokeStyle = INK; q.lineWidth = 3; q.strokeRect(x, 600, 94, FY - 600) }
  // roof, gable, chimney
  const roof = qq => { qq.moveTo(-1220, -760); qq.lineTo(970, -1420); qq.lineTo(3160, -760); qq.lineTo(3060, -760); qq.lineTo(970, -1340); qq.lineTo(-1120, -760); qq.closePath() };
  poche(q, roof, [-1220, -1420, 3160, -760]);
  q.save(); q.beginPath(); q.moveTo(-1120, -760); q.lineTo(970, -1340); q.lineTo(3060, -760); q.closePath(); q.clip();
  for (let y = -1330; y < -760; y += 34) { q.strokeStyle = 'rgba(42,29,20,.6)'; q.lineWidth = 1.4; q.beginPath(); q.moveTo(-1200, y); q.lineTo(3200, y); q.stroke(); for (let x = -1200 + ((y / 34) % 2) * 40; x < 3200; x += 80) { q.beginPath(); q.moveTo(x, y); q.lineTo(x, y + 34); q.stroke() } }
  // attic: an oval window
  q.fillStyle = PAPER; q.beginPath(); q.ellipse(970, -1010, 90, 120, 0, 0, 7); q.fill(); q.lineWidth = 5; q.strokeStyle = INK; q.stroke(); q.lineWidth = 2; q.beginPath(); q.moveTo(880, -1010); q.lineTo(1060, -1010); q.moveTo(970, -1130); q.lineTo(970, -890); q.stroke();
  q.restore();
  poche(q, qq => qq.rect(2200, -1300, 120, 330), [2200, -1300, 2320, -970]);
  q.strokeStyle = INK; q.lineWidth = 3; q.strokeRect(2185, -1320, 150, 26);
  // ---- the rooms' furniture: every later piece of evidence is already in the house, innocent ----
  q.lineWidth = 2.6; q.strokeStyle = INK; q.fillStyle = INK;
  // R's room (ground left): desk with inkwell and quill, coin box, flour sacks, the photograph on the wall
  q.strokeRect(-980, 700, 300, 18); q.beginPath(); q.moveTo(-970, 718); q.lineTo(-970, FY); q.moveTo(-690, 718); q.lineTo(-690, FY); q.stroke();
  q.beginPath(); q.ellipse(-900, 690, 16, 10, 0, 0, 7); q.fill(); q.beginPath(); q.moveTo(-895, 684); q.quadraticCurveTo(-870, 620, -840, 600); q.stroke();
  q.strokeRect(-800, 664, 70, 36); hatch(q, -800, 664, -730, 700, .8, 9, 1); q.beginPath(); q.arc(-765, 682, 5, 0, 7); q.stroke();
  for (const [x, w, h] of [[-310, 90, 120], [-215, 80, 104]]) { q.beginPath(); q.moveTo(x, FY); q.lineTo(x, FY - h); q.quadraticCurveTo(x + w / 2, FY - h - 20, x + w, FY - h); q.lineTo(x + w, FY); q.closePath(); q.fillStyle = PAPER; q.fill(); q.stroke(); q.save(); q.clip(); hatch(q, x, FY - h - 20, x + w, FY, .9, 10, 1.2); q.restore() }
  q.strokeRect(-860, 300, 130, 100); q.strokeRect(-848, 312, 106, 76); q.beginPath(); q.ellipse(-795, 345, 24, 20, 0, 0, 7); q.stroke(); q.beginPath(); q.moveTo(-860, 300); q.lineTo(-795, 260); q.lineTo(-730, 300); q.stroke();
  // B's room (ground right): a rope coiled on a hook, a chest of drawers with a keyhole (the gun is inside), a wrestler's bench
  q.beginPath(); q.moveTo(2240, 420); q.lineTo(2240, 450); q.stroke(); for (let i = 0; i < 4; i++) { q.beginPath(); q.ellipse(2240, 500, 36 - i * 5, 46 - i * 4, 0, 0, 7); q.stroke() } q.beginPath(); q.moveTo(2240, 546); q.quadraticCurveTo(2250, 620, 2230, 660); q.stroke();
  q.strokeRect(2700, 640, 240, 222); for (let i = 1; i < 3; i++) { q.beginPath(); q.moveTo(2700, 640 + i * 74); q.lineTo(2940, 640 + i * 74); q.stroke(); q.beginPath(); q.arc(2820, 640 + i * 74 - 37, 5, 0, 7); q.fill() }
  q.save(); q.beginPath(); q.rect(2700, 640, 240, 222); q.clip(); hatch(q, 2700, 640, 2940, 862, Math.PI / 2, 10, 1); q.restore();
  q.strokeRect(2050, 790, 160, 20); q.beginPath(); q.moveTo(2065, 810); q.lineTo(2065, FY); q.moveTo(2195, 810); q.lineTo(2195, FY); q.stroke();
  // I's room (upstairs left): a low bed, a cup on the nightstand, a window
  q.fillStyle = PAPER; q.fillRect(-960, -190, 520, 80); q.strokeRect(-960, -190, 520, 80); q.beginPath(); q.moveTo(-960, -260); q.lineTo(-960, -60); q.moveTo(-440, -110); q.lineTo(-440, -60); q.stroke();
  q.save(); q.beginPath(); q.rect(-960, -190, 520, 80); q.clip(); hatch(q, -960, -190, -440, -110, .6, 12, 1.2); q.restore();
  q.strokeRect(-400, -170, 90, 110); q.beginPath(); q.moveTo(-375, -170); q.lineTo(-370, -205); q.lineTo(-340, -205); q.lineTo(-335, -170); q.stroke(); q.beginPath(); q.arc(-330, -190, 10, -1.2, 1.2); q.stroke();
  q.fillStyle = PAPER; q.fillRect(-700, -560, 200, 240); q.strokeRect(-700, -560, 200, 240); q.beginPath(); q.moveTo(-600, -560); q.lineTo(-600, -320); q.moveTo(-700, -440); q.lineTo(-500, -440); q.stroke();
  // O's room (upstairs right): a tall mirror, a vase of flowers, a window with a curtain and its cord
  q.beginPath(); q.ellipse(1520, -330, 80, 190, 0, 0, 7); q.lineWidth = 5; q.stroke(); q.lineWidth = 2.6; q.save(); q.clip(); hatch(q, 1440, -520, 1600, -140, -.5, 16, 1); q.restore(); q.beginPath(); q.moveTo(1480, -140); q.lineTo(1460, -60); q.moveTo(1560, -140); q.lineTo(1580, -60); q.stroke();
  q.beginPath(); q.moveTo(1760, -60); q.lineTo(1745, -130); q.quadraticCurveTo(1775, -150, 1805, -130); q.lineTo(1790, -60); q.closePath(); q.stroke();
  for (let i = 0; i < 4; i++) { const a = -1.1 + i * .7; q.beginPath(); q.moveTo(1775, -135); q.quadraticCurveTo(1775 + Math.sin(a) * 30, -190, 1775 + Math.sin(a) * 50, -230 + Math.abs(a) * 20); q.stroke(); q.beginPath(); q.arc(1775 + Math.sin(a) * 50, -236 + Math.abs(a) * 20, 12, 0, 7); q.stroke() }
  q.fillStyle = PAPER; q.fillRect(2300, -560, 260, 280); q.strokeRect(2300, -560, 260, 280);
  q.save(); q.beginPath(); q.moveTo(2270, -580); q.quadraticCurveTo(2330, -420, 2290, -250); q.lineTo(2360, -250); q.quadraticCurveTo(2380, -420, 2350, -580); q.closePath(); q.fillStyle = PAPER; q.fill(); q.stroke(); q.clip(); hatch(q, 2260, -580, 2390, -250, Math.PI / 2, 8, 1.3); q.restore();
  q.beginPath(); q.moveTo(2580, -580); q.lineTo(2580, -300); q.stroke(); q.beginPath(); q.ellipse(2580, -290, 6, 12, 0, 0, 7); q.fill();
  q.strokeStyle = INK; q.lineWidth = 3; q.strokeRect(2240, -585, 380, 10);
  // the caption: the only words of the film, engraved under the plate; ruled lines and a collection stamp, no other words
  q.fillStyle = INK; q.textAlign = 'center'; q.textBaseline = 'alphabetic';
  q.font = '700 150px "DejaVu Serif", Georgia, serif';
  const title = 'THE ABOMINABLE HOUSE'; let sp = 26, tw = 0; for (const ch of title) tw += q.measureText(ch).width + sp; let x = 970 - (tw - sp) / 2;
  q.textAlign = 'left'; for (const ch of title) { q.fillText(ch, x, 1290); x += q.measureText(ch).width + sp }
  q.lineWidth = 3; q.beginPath(); q.moveTo(-500, 1330); q.lineTo(2440, 1330); q.stroke(); q.lineWidth = 1.5; q.beginPath(); q.moveTo(-200, 1345); q.lineTo(2140, 1345); q.stroke();
  q.strokeStyle = 'rgba(122,40,30,.7)'; q.lineWidth = 5; q.beginPath(); q.arc(2900, 1260, 60, 0, 7); q.stroke(); q.lineWidth = 2; q.beginPath(); q.arc(2900, 1260, 44, 0, 7); q.stroke();
  for (let i = 0; i < 16; i++) { const a = i / 16 * 6.283; q.beginPath(); q.moveTo(2900 + Math.cos(a) * 18, 1260 + Math.sin(a) * 18); q.lineTo(2900 + Math.cos(a) * 38, 1260 + Math.sin(a) * 38); q.stroke() }
  // plate mark (the copper plate's bevel pressed into the paper)
  q.strokeStyle = 'rgba(90,70,45,.55)'; q.lineWidth = 6; q.strokeRect(-1290, -1540, 4520, 2930); q.strokeStyle = 'rgba(255,250,235,.7)'; q.lineWidth = 3; q.strokeRect(-1282, -1532, 4520, 2930);
}
let K_ = null;
function houseCaches() {
  if (HOUSE) return HOUSE;
  const low = off(2270, 1480); let q = low.getContext('2d'); q.setTransform(.5, 0, 0, .5, 1300 * .5, 1560 * .5); drawHouse(q);
  const high = off(2120, 1300); q = high.getContext('2d'); q.setTransform(1, 0, 0, 1, 100, 120); drawHouse(q);
  HOUSE = { low, high }; return HOUSE;
}

// ---------------- the incoming picture: deed 0 at t=0, composited exactly as the film does (levers) ----------------
function finalFrame(X, K) {
  const e = X.ledger.ev[X.k], st = X.ledger.states[X.k], D = (X.DEEDS || window.DEEDS)[e.deed]; const key = e.deed + e.A + e.V;
  if (FIN[key]) return FIN[key];
  const cv = off(1920, 1080), g = cv.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, 1920, 1080);
  const out = { cv, marks: null };
  if (!D) { FIN[key] = out; return out }
  const lt = .001, carry = st.body, order = D.layers || ['bg', 'V', 'A'];
  const mk = D.marks ? D.marks(lt, e.A, e.V, K) : null; out.marks = mk;
  if (!mk) { g.save(); try { D.draw(g, lt, e.A, e.V, K, { carry }) } catch (err) { } g.restore(); FIN[key] = out; return out }
  for (const ly of order) {
    const L = off(1920, 1080), q = L.getContext('2d'); q.save(); try { D.draw(q, lt, e.A, e.V, K, { layer: ly, carry }) } catch (err) { } q.restore();
    if (ly === 'bg') { g.drawImage(L, 0, 0); out.bg = L; continue }
    const who = ly === 'A' ? e.A : e.V, lv = st.levers[who], b = mk[ly];
    const f = 1 + .14 * Math.max(-1, Math.min(1, lv.loom)) - .22 * lv.shrink, cx = b.x + b.w / 2, by = b.y + b.h;
    const fl = []; if (lv.grey > .05) fl.push(`grayscale(${Math.min(1, lv.grey)}) brightness(${1 - .25 * lv.grey})`); if (lv.halo > .15) fl.push(`drop-shadow(0 0 ${Math.round(28 * lv.halo)}px rgba(255,236,180,${Math.min(.9, lv.halo)}))`);
    if (lv.shadow > .15) fl.push(`drop-shadow(${Math.round(-60 * lv.shadow)}px ${Math.round(-30 * lv.shadow)}px ${Math.round(18 * lv.shadow)}px rgba(0,0,0,${Math.min(.8, .35 + lv.shadow * .4)}))`);
    g.save(); g.filter = fl.join(' ') || 'none'; g.translate(cx, by); g.scale(f, f); g.translate(-cx, -by); g.drawImage(L, 0, 0); g.restore();
    out[ly] = { x: cx - b.w * f / 2, y: by - b.h * f, w: b.w * f, h: b.h * f };
  }
  FIN[key] = out; return out;
}

// ---------------- the engraved sacks ----------------
function bodyPath(q, id, w, h) {
  const bul = { R: .56, B: .58, I: .52, O: .5 }[id], sag = { R: .08, B: .05, I: .26, O: .04 }[id];
  q.moveTo(-w * .5, -h * .25);
  q.quadraticCurveTo(-w * bul, -h * .7, -w * .44, -h);
  q.quadraticCurveTo(0, -h * (1 - sag) + h * .08, w * .44, -h);
  q.quadraticCurveTo(w * bul, -h * .7, w * .5, -h * .25);
  q.quadraticCurveTo(w * .52, 0, w * .3, 0); q.lineTo(-w * .3, 0); q.quadraticCurveTo(-w * .52, 0, -w * .5, -h * .25); q.closePath();
}
function engrSack(q, id, x, y, w, h, o, s) {
  const H = K_.hash, px = 1 / s; // px: one screen pixel in world units
  const lv = o.lv || {}; const wash = o.wash || 0;
  q.save(); q.translate(x, y); q.rotate(o.rot || 0); q.scale(o.sx || 1, o.sy || 1);
  // cast shadow, hatched (shadow lever lengthens it)
  const shL = 1 + 1.5 * (lv.shadow || 0);
  q.save(); q.beginPath(); q.ellipse(-w * .25 * shL, -2, w * .55 * shL, h * .07, 0, 0, 7); q.clip(); hatch(q, -w * 1.4, -h * .2, w * .6, h * .1, .7, 6, 1.4, 'rgba(42,29,20,.7)'); q.restore();
  // halo lever: an engraved glory of short rays
  if ((lv.halo || 0) > .15) { q.save(); q.strokeStyle = `rgba(160,120,40,${.6 * lv.halo})`; q.lineWidth = 2; q.beginPath(); for (let i = 0; i < 28; i++) { const a = Math.PI + i / 27 * Math.PI; const r0 = Math.max(w, h) * .62, r1 = r0 + 18 + 14 * (i % 2); q.moveTo(Math.cos(a) * r0 * (w / Math.max(w, h) * .9 + .3), -h * .5 + Math.sin(a) * r0); q.lineTo(Math.cos(a) * r1 * (w / Math.max(w, h) * .9 + .3), -h * .5 + Math.sin(a) * r1) } q.stroke(); q.restore() }
  // Inigo's ears hang down beside him, outside the body
  if (id === 'I') {
    for (const sd of [-1, 1]) { const sw = (o.ear || 0) * sd; q.save(); q.translate(sd * w * .44, -h); q.rotate(sw * .12);
      const ear = () => { q.beginPath(); q.moveTo(-sd * w * .04, 0); q.quadraticCurveTo(sd * w * .17, h * .25, sd * w * .12, h * .8); q.quadraticCurveTo(sd * w * .09, h * .94, sd * w * .03, h * .88); q.quadraticCurveTo(sd * w * .02, h * .4, -sd * w * .06, h * .1); q.closePath() }; ear();
      q.fillStyle = PAPER; q.fill(); q.save(); q.clip(); hatch(q, -w * .3, 0, w * .3, h * .8, Math.PI / 2 - .1, 6, 1.3); q.restore(); ear(); q.lineWidth = 2.6; q.strokeStyle = INK; q.stroke(); q.restore() }
  }
  // ear tufts for the others
  if (id !== 'I') for (const sd of [-1, 1]) { q.beginPath(); q.moveTo(sd * w * .36, -h * .97); q.lineTo(sd * w * .5, -h * 1.1 - (o.ear || 0) * h * .05); q.lineTo(sd * w * .47, -h * .9); q.closePath(); q.fillStyle = INK; q.fill() }
  // body: paper, hatching (sparser for the half-empty), cross-hatch on the side away from the lamp
  q.beginPath(); bodyPath(q, id, w, h); q.fillStyle = PAPER; q.fill();
  q.save(); q.clip();
  const sp = id === 'I' ? 11 : id === 'B' ? 7 : 8.5;
  hatch(q, -w * .7, -h * 1.1, w * .7, 0, .95, sp, 1.5);
  q.save(); q.beginPath(); q.rect(w * .05, -h * 1.1, w, h * 1.2); q.clip(); hatch(q, -w * .7, -h * 1.1, w * .7, 0, -.6, sp + 1, 1.3); q.restore();
  q.save(); q.beginPath(); q.rect(-w, -h * .16, w * 2, h * .2); q.clip(); hatch(q, -w * .7, -h * .2, w * .7, 0, .2, 5, 1.2); q.restore();
  // creases
  q.strokeStyle = INK; q.lineWidth = 2; for (let i = 0; i < 3; i++) { const cx = (H(i * 3.7 + id.charCodeAt(0)) - .5) * w * .6; q.beginPath(); q.moveTo(cx, -h * .92); q.quadraticCurveTo(cx + w * .06, -h * .65, cx - w * .02, -h * .4); q.stroke() }
  // hand-colouring: the colourist's wash brings each attribute in
  const gw = 1 - .7 * Math.min(1, lv.grey || 0);
  if (id === 'R') { q.fillStyle = ATTR.R + (.85 * wash * gw) + ')'; q.fillRect(-w, -h * 1.05, w * 2, h * .25); q.save(); q.beginPath(); q.rect(-w, -h * 1.05, w * 2, h * .25); q.clip(); hatch(q, -w, -h * 1.1, w, -h * .8, 0, 5, 1.4); q.restore(); q.strokeStyle = INK; q.lineWidth = 2; q.beginPath(); for (let xx = -w * .48; xx < w * .48; xx += 9) { q.moveTo(xx, -h * .8); q.lineTo(xx + 2, -h * .73) } q.stroke() }
  if (id === 'B') { q.fillStyle = INK; q.fillRect(-w, -h * .445, w * 2, h * .09); q.fillStyle = 'rgba(200,150,60,' + (.55 * wash * gw) + ')'; q.fillRect(-w, -h * 1.1, w * 2, h * .64);
    q.strokeStyle = INK; q.lineWidth = 3; q.beginPath(); q.arc(0, -h * .7, w * .15, 0, 7); q.stroke(); q.lineWidth = 2.2; q.beginPath(); q.moveTo(0, -h * .6); q.lineTo(0, -h * .82); for (let i = 0; i < 4; i++) { const yy = -h * .66 - i * h * .045; q.moveTo(0, yy); q.lineTo(-w * .05, yy - h * .04); q.moveTo(0, yy); q.lineTo(w * .05, yy - h * .04) } q.stroke() }
  if (id === 'I') { q.fillStyle = 'rgba(201,176,137,' + (.5 * wash * gw) + ')'; q.fillRect(-w, -h * 1.1, w * 2, h * 1.2) }
  q.restore();
  q.beginPath(); bodyPath(q, id, w, h); q.strokeStyle = INK; q.lineWidth = 3.4; q.stroke();
  // Ogiva's wig: long, past the shoulders, purple wash with strand lines
  if (id === 'O') { const sw = (o.wig || 0);
    const wig = qq => { qq.moveTo(-w * .62 + sw * 6, -h * .5); qq.quadraticCurveTo(-w * .66, -h * 1.12, 0, -h * 1.16); qq.quadraticCurveTo(w * .66, -h * 1.12, w * .62 + sw * 6, -h * .5); qq.lineTo(w * .4 + sw * 4, -h * .52); qq.quadraticCurveTo(w * .36, -h * .88, 0, -h * .9); qq.quadraticCurveTo(-w * .36, -h * .88, -w * .4 + sw * 4, -h * .52); qq.closePath() };
    q.beginPath(); wig(q); q.fillStyle = PAPER; q.fill(); q.fillStyle = 'rgba(122,59,143,' + (.85 * wash * gw) + ')'; q.fill();
    q.save(); q.clip(); q.strokeStyle = INK; q.lineWidth = 1.5; q.beginPath(); for (let i = -6; i <= 6; i++) { const xx = i * w * .1; q.moveTo(xx * .6, -h * 1.14); q.quadraticCurveTo(xx * 1.15, -h * .9, xx * 1.1 + sw * 5, -h * .45) } q.stroke(); q.restore();
    q.beginPath(); wig(q); q.lineWidth = 2.8; q.stroke() }
  q.restore();
}
// catalogue bracket: solid corners = documented object; dashed = invented motion; a small item tag hangs from it
function bracket(q, x, y, w, h, a, dashed, s, wiggle) {
  if (a <= 0) return; const px = 1 / s, p = 14 * px + 10, L = Math.min(w, h) * .3 + 10;
  q.save(); q.globalAlpha = a; q.strokeStyle = '#8a2a1c'; q.lineWidth = 2.4 * px; if (dashed) q.setLineDash([7 * px, 6 * px]); q.lineDashOffset = -(wiggle || 0);
  const x0 = x - w / 2 - p, x1 = x + w / 2 + p, y0 = y - h - p, y1 = y + p * .4;
  q.beginPath(); q.moveTo(x0, y0 + L); q.lineTo(x0, y0); q.lineTo(x0 + L, y0); q.moveTo(x1 - L, y0); q.lineTo(x1, y0); q.lineTo(x1, y0 + L); q.moveTo(x0, y1 - L); q.lineTo(x0, y1); q.lineTo(x0 + L, y1); q.moveTo(x1 - L, y1); q.lineTo(x1, y1); q.lineTo(x1, y1 - L); q.stroke();
  q.setLineDash([]); q.lineWidth = 1.6 * px; q.beginPath(); q.moveTo(x1, y0); q.lineTo(x1 + 16 * px, y0 - 18 * px); q.stroke();
  q.fillStyle = PAPER; q.fillRect(x1 + 6 * px, y0 - 40 * px, 34 * px, 22 * px); q.strokeRect(x1 + 6 * px, y0 - 40 * px, 34 * px, 22 * px);
  q.beginPath(); q.moveTo(x1 + 11 * px, y0 - 33 * px); q.lineTo(x1 + 35 * px, y0 - 33 * px); q.moveTo(x1 + 11 * px, y0 - 25 * px); q.lineTo(x1 + (dashed ? 22 : 31) * px, y0 - 25 * px); q.stroke();
  q.restore();
}

// ---------------- motion: paths through the house (invented, so dotted) ----------------
function pathFor(id, dest) {
  const h = HOME[id]; const p = [h];
  if (id === 'R') p.push([-13, FY]);
  if (id === 'B') p.push([1933, FY]);
  if (id === 'I' || id === 'O') { p.push([690, -60], [330, 434], [400, FY]) }
  p.push(dest); return p;
}
function along(pts, d) { let acc = 0; for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1], l = Math.hypot(b[0] - a[0], b[1] - a[1]); if (acc + l >= d || i === pts.length - 2) { const u = l ? Math.max(0, Math.min(1, (d - acc) / l)) : 1; return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, Math.atan2(b[1] - a[1], b[0] - a[0])] } acc += l } return pts[pts.length - 1] }
function plen(pts) { let s = 0; for (let i = 0; i < pts.length - 1; i++)s += Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); return s }
const GAIT = { R: { hop: 150, lift: 34, d: .1 }, B: { hop: 300, lift: 30, d: .1 }, I: { hop: 230, lift: 70, d: 0 }, O: { hop: 190, lift: 60, d: -.05 } };
// the victim comes into the parlour first and is standing there when the doer arrives
const WIN = { V: [.85, 2.25], A: [1.05, 2.5] };
const win = (id, role) => [WIN[role][0] + GAIT[id].d, WIN[role][1]];
function travel(id, role, dest, u, K) {
  const G = GAIT[id], Wn = win(id, role), pts = pathFor(id, dest), Lt = plen(pts);
  const v = K.sm(Wn[0], Wn[1], u), d = v * Lt; const p = along(pts, d);
  const n = Math.max(1, Math.round(Lt / G.hop)), ph = v * n, fr = ph - Math.floor(ph);
  const air = v > 0 && v < 1 ? Math.sin(Math.PI * fr) : 0;
  const lift = air * G.lift * (1 + .3 * (id === 'I' ? Math.sin(ph * 2.1) : 0));
  const squash = v > 0 && v < 1 ? Math.pow(1 - air, 6) : 0;
  return { x: p[0], y: p[1] - lift, d, Lt, pts, moving: v > 0 && v < 1, started: v > 0, sx: 1 + .08 * squash - .04 * air, sy: 1 - .1 * squash + .06 * air, rot: (v > 0 && v < 1) ? Math.cos(p[2]) * .06 * Math.sin(ph * Math.PI * 2) : 0, steps: n };
}

// ---------------- camera: the scan crop ----------------
const CAM0 = { s: .34, ox: 630, oy: 563 }, CAM1 = { s: 1, ox: 0, oy: 0 };
function cam(u, K) {
  const z = K.sm(1.15, 2.5, u); const s = Math.exp(Math.log(CAM0.s) * (1 - z));
  const k = (s - CAM0.s) / (1 - CAM0.s); return { s, ox: CAM0.ox * (1 - k), oy: CAM0.oy * (1 - k), z };
}

// ---------------- one print frame ----------------
function drawPrint(g, u, X, K, F) {
  const e = X.ledger.ev[X.k], st = X.ledger.states[X.k];
  const C = cam(u, K), Hc = houseCaches();
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = PAPER; g.fillRect(0, 0, 1920, 1080);
  // paper foxing (world-anchored)
  g.setTransform(C.s, 0, 0, C.s, C.ox, C.oy);
  for (let i = 0; i < 40; i++) { const x = -1300 + K.hash(i * 4.1) * 4540, y = -1560 + K.hash(i * 6.3) * 2960; g.fillStyle = `rgba(150,110,60,${.05 + .06 * K.hash(i)})`; g.beginPath(); g.arc(x, y, 8 + 30 * K.hash(i * 2.2), 0, 7); g.fill() }
  // the press pull: the impression darkens in over the first 0.25 s
  const imp = K.sm(0, .22, u);
  g.globalAlpha = .25 + .75 * imp;
  g.setTransform(C.s / .5, 0, 0, C.s / .5, C.ox - 1300 * C.s, C.oy - 1560 * C.s); g.drawImage(Hc.low, 0, 0);
  if (C.s > .42) { g.setTransform(C.s, 0, 0, C.s, C.ox - 100 * C.s, C.oy - 120 * C.s); g.globalAlpha = (.25 + .75 * imp) * K.sm(.42, .55, C.s); g.drawImage(Hc.high, 0, 0) }
  g.globalAlpha = 1; g.setTransform(C.s, 0, 0, C.s, C.ox, C.oy);
  // the four
  const fin = F.marks ? F : null;
  const rank = id => id === e.V ? 2 : id === e.A ? 1 : 0; const order = IDS.slice().sort((a, b) => rank(a) - rank(b));
  for (const id of order) {
    const lv = st.levers[id]; const f = 1 + .14 * Math.max(-1, Math.min(1, lv.loom)) - .22 * lv.shrink;
    const travelling = id === e.A || id === e.V; const role = id === e.A ? 'A' : 'V';
    let w = K.CAST[id].w * 1.7 * f, h = K.CAST[id].h * 1.7 * f;
    let x = HOME[id][0], y = HOME[id][1], o = { lv, wash: K.sm(INTRO[id], INTRO[id] + .22, u) }, dashed = false, moving = false;
    // each sack's introducing gesture (in its own way), right after its wash
    const gi = u - INTRO[id] - .1;
    if (gi > 0 && gi < .5) { const b = Math.sin(Math.PI * gi / .5); dashed = true;
      if (id === 'R') o.rot = .07 * Math.sin(gi * 18) * b;                // rocks, miserly
      if (id === 'B') { o.sx = 1 + .05 * b; o.sy = 1 + .03 * b }           // swells, full to bursting
      if (id === 'I') { o.ear = Math.sin(gi * 12) * b; o.sy = 1 - .05 * b } // slumps, ears sway
      if (id === 'O') { o.wig = Math.sin(gi * 14) * b * 2; o.sy = 1 + .03 * b } // stands taller, tosses the wig
    }
    if (travelling && fin && fin[role]) {
      const b = fin[role]; const dest = [b.x + b.w / 2, b.y + b.h];
      const T = travel(id, role, dest, u, K); const Wn = win(id, role); const k2 = K.sm(Wn[0], Wn[1], u);
      w = K.lerp(w, b.w, k2); h = K.lerp(h, b.h, k2);
      if (T.started) {
        // dotted path behind it: the invented motion is marked
        g.save(); g.fillStyle = '#8a2a1c'; const step = 26; for (let d = 0; d < T.d - 40; d += step) { const p = along(T.pts, d); g.globalAlpha = .55 * (1 - K.sm(2.25, 2.5, u)); g.beginPath(); g.arc(p[0], p[1] - 6, 3.2 / Math.max(.6, C.s) + 1.5, 0, 7); g.fill() } g.restore();
        x = T.x; y = T.y; o.sx = T.sx; o.sy = T.sy; o.rot = T.rot; if (T.moving) { dashed = true; moving = true }
        if (id === 'I') o.ear = T.moving ? Math.sin(u * 20) * .8 : 0;
        if (id === 'O') o.wig = T.moving ? Math.sin(u * 16) * 1.2 : 0;
      }
    } else if (!travelling && u > 1.0) {
      // the two not in the coming scene turn toward the parlour and stay in the print
      const toward = HOME[id][0] < 960 ? 1 : -1; o.rot = toward * .06 * K.sm(1.0, 1.5, u); o.ear = .4 * K.sm(1.0, 1.5, u); dashed = true;
    }
    engrSack(g, id, x, y, w, h, o, C.s);
    const ba = K.sm(INTRO[id] + .05, INTRO[id] + .2, u) * (1 - K.sm(2.25, 2.5, u));
    bracket(g, x, y, w, h, ba, dashed, C.s, moving ? u * 60 : 0);
  }
  // the scan crop closing on the parlour: registration corners, then the frame becomes the screen
  const ca = K.sm(1.05, 1.3, u) * (1 - K.sm(2.2, 2.5, u));
  if (ca > 0) { g.save(); g.globalAlpha = ca; g.strokeStyle = '#8a2a1c'; g.lineWidth = 3 / C.s; const L = 140, m = 6 / C.s;
    for (const [cx, cy, sx, sy] of [[0, 0, 1, 1], [1920, 0, -1, 1], [0, 1080, 1, -1], [1920, 1080, -1, -1]]) { g.beginPath(); g.moveTo(cx + sx * m, cy + sy * (m + L)); g.lineTo(cx + sx * m, cy + sy * m); g.lineTo(cx + sx * (m + L), cy + sy * m); g.stroke(); g.beginPath(); g.moveTo(cx - sx * 40, cy); g.lineTo(cx - sx * 4, cy); g.moveTo(cx, cy - sy * 40); g.lineTo(cx, cy - sy * 4); g.stroke() }
    g.setLineDash([12 / C.s, 10 / C.s]); g.lineWidth = 1.5 / C.s; g.strokeRect(0, 0, 1920, 1080); g.restore() }
  // outside the crop the print dims a little (the scan's tray)
  if (C.z > 0 && C.z < 1) { g.save(); g.fillStyle = `rgba(60,45,30,${.25 * K.sm(1.2, 1.6, u) * (1 - C.z)})`; g.beginPath(); g.rect(-4000, -4000, 12000, 12000); g.rect(0, 1080, 1920, -1080); g.fill('evenodd'); g.restore() }
  g.setTransform(1, 0, 0, 1, 0, 0);
}

// ---------------- transillumination: the lamp lit behind the paper ----------------
function glow(g, a) { // the paper lit from behind takes the stage glass's gradient
  if (a <= 0) return; g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'multiply'; g.globalAlpha = a;
  const gr = g.createRadialGradient(960, 210, 40, 960, 470, 1250); gr.addColorStop(0, '#fff0b8'); gr.addColorStop(.22, '#f6cd70'); gr.addColorStop(.6, '#d98d32'); gr.addColorStop(1, '#5e2a0b');
  g.fillStyle = gr; g.fillRect(0, 0, 1920, 1080); g.restore();
}
function front(g, R, K, pad) { const n = 140; g.moveTo(960 + R + pad, 140); for (let i = 1; i <= n; i++) { const a = i / n * 6.2832; const rr = R + pad + 22 * (K.hash(i * 3.3) - .5) + 14 * Math.sin(a * 7 + 1); g.lineTo(960 + Math.cos(a) * rr, 140 + Math.sin(a) * rr) } g.closePath() }
let PRINT = null;
function draw(g, u, X, K) {
  K_ = K; const F = finalFrame(X, K);
  const lit = K.sm(2.1, T_LIGHT, u);
  if (u < T_LIGHT) { drawPrint(g, u, X, K, F); glow(g, .85 * lit); flame(g, u, K); return }
  // from T_LIGHT on the print no longer changes (camera, sacks, marks all settled): freeze it once, with its ink-spread copy
  const key = X.ledger.ev[X.k].deed + X.ledger.ev[X.k].A + X.ledger.ev[X.k].V;
  if (!PRINT || PRINT.key !== key) { const cv = off(1920, 1080), P = cv.getContext('2d'); drawPrint(P, T_LIGHT, X, K, F); glow(P, .85);
    const th = off(1920, 1080), T = th.getContext('2d'); T.drawImage(cv, 0, 0); T.globalCompositeOperation = 'darken'; for (const [dx, dy] of [[-3, 0], [3, 0], [0, -3], [0, 3], [-2, 2], [2, -2]]) T.drawImage(cv, dx, dy);
    PRINT = { key, cv, th } }
  const v = K.cl(0, 1, (u - T_LIGHT) / (T_FULL - T_LIGHT)); const R = 1700 * Math.pow(v, 1.35) - 60;
  g.setTransform(1, 0, 0, 1, 0, 0); g.drawImage(F.cv, 0, 0);
  if (v >= 1) return;
  // the print where the light hasn't reached yet; just ahead of the light the ink spreads (lines thicken)
  g.save(); g.beginPath(); g.rect(0, 0, 1920, 1080); front(g, R, K, 170); g.clip('evenodd'); g.drawImage(PRINT.cv, 0, 0); g.restore();
  g.save(); g.beginPath(); front(g, R, K, 170); front(g, R, K, 0); g.clip('evenodd'); g.drawImage(PRINT.th, 0, 0); g.restore();
  // inside the light, the engraving lingers a moment and dissolves into the card (lines first, then nothing)
  for (let i = 0; i < 3; i++) { g.save(); g.beginPath(); front(g, R, K, -60 * i); front(g, R, K, -60 * (i + 1)); g.clip('evenodd'); g.globalCompositeOperation = 'multiply'; g.globalAlpha = .7 * (1 - i / 3); g.drawImage(PRINT.cv, 0, 0); g.restore() }
  // the light itself coming through the paper: a soft warm rim, not an edge
  g.save(); g.globalCompositeOperation = 'screen'; const rg = g.createRadialGradient(960, 140, Math.max(1, R - 120), 960, 140, R + 90);
  rg.addColorStop(0, 'rgba(255,220,150,0)'); rg.addColorStop(.6, 'rgba(255,226,160,.45)'); rg.addColorStop(1, 'rgba(255,220,150,0)'); g.fillStyle = rg; g.fillRect(0, 0, 1920, 1080); g.restore();
  flame(g, u, K);
}
function flame(g, u, K) { // the lamp catching, behind the paper
  const a = K.sm(2.1, 2.45, u) * (1 - K.sm(3.2, T_FULL, u)); if (a <= 0) return; const C = cam(u, K);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); const x = C.ox + 960 * C.s, y = C.oy + 140 * C.s; g.globalCompositeOperation = 'lighter';
  const gr = g.createRadialGradient(x, y, 2, x, y, 260 * C.s); gr.addColorStop(0, `rgba(255,246,208,${a})`); gr.addColorStop(.3, `rgba(255,200,110,${.5 * a})`); gr.addColorStop(1, 'rgba(255,160,60,0)');
  g.fillStyle = gr; g.fillRect(x - 300, y - 300, 600, 600); g.restore();
}

// ---------------- sound: paper and press, the four voices, the burin, the lamp catching ----------------
function sound(ac, out0, t0, X, K) {
  const out = ac.createGain(); out.gain.value = 4; out.connect(out0); // one bus for the opening's grains
  const S = K.SND, e = X.ledger.ev[X.k], st = X.ledger.states[X.k]; K_ = K; const D = (X.DEEDS || window.DEEDS)[e.deed];
  // the marks the two will stand on (deed 0 at t=0, lever-scaled as the film composites them) — no rendering needed for sound
  const F = {}; const mk = D && D.marks ? D.marks(.001, e.A, e.V, K) : null;
  if (mk) for (const ly of ['A', 'V']) { const lv = st.levers[e[ly]], b = mk[ly], f = 1 + .14 * Math.max(-1, Math.min(1, lv.loom)) - .22 * lv.shrink; F[ly] = { x: b.x + b.w / 2 - b.w * f / 2, y: b.y + b.h - b.h * f, w: b.w * f, h: b.h * f } }
  const panAt = (wx, tt) => { const C = cam(tt, K); return K.cl(-1, 1, (C.ox + wx * C.s) / 960 - 1) };
  // the press pull: a soft heavy thump and paper lifting off the plate
  S.thump(ac, out, t0 + .02, .5, 52, 0);
  S.cloud(ac, out, t0 + .05, .35, 50, { bp: 3200, a: .03, d: [.01, .05], spread: .6 }, uu => 1 - uu);
  // each sack introduced by its own voice as the colour finds it, and a brush stroke of wash
  for (const id of IDS) { const tt = INTRO[id], p = panAt(HOME[id][0], tt);
    S.grain(ac, out, t0 + tt, { bp: 1800, q: 1, d: .2, a: .05, pan: p, att: .6 });
    S.grain(ac, out, t0 + tt + .06, { bp: 2600, q: 6, d: .015, a: .08, pan: p, att: .1 }); // bracket set
    const gt = tt + .1 + .25;
    if (id === 'R') { S.say(ac, out, 'R', t0 + gt - .1, 'step', .6, p); S.say(ac, out, 'R', t0 + gt + .08, 'step', .5, p) }
    if (id === 'B') S.say(ac, out, 'B', t0 + gt, 'breathe', .4, p);
    if (id === 'I') S.say(ac, out, 'I', t0 + gt, 'breathe', .35, p);
    if (id === 'O') { S.say(ac, out, 'O', t0 + gt, 'tick', .7, p); S.say(ac, out, 'O', t0 + gt + .09, 'tick', .5, p) }
  }
  // the scan crop: four burin scratches as the corners set
  for (let i = 0; i < 4; i++) S.grain(ac, out, t0 + 1.08 + i * .05, { bp: 4200, q: 3, d: .05, a: .05, pan: [-.8, .8, -.8, .8][i], glide: -.2 });
  // the two who come down through the house: a footfall at every landing of the hop
  for (const role of ['A', 'V']) { const id = e[role]; if (!F[role]) continue; const b = F[role], dest = [b.x + b.w / 2, b.y + b.h];
    const G = GAIT[id], Wn = win(id, role), Lt = plen(pathFor(id, dest)), n = Math.max(1, Math.round(Lt / G.hop));
    for (let j = 1; j <= n; j++) { // find time when progress v = j/n (invert smoothstep by bisection)
      let lo = Wn[0], hi = Wn[1]; for (let it = 0; it < 18; it++) { const m = (lo + hi) / 2; if (K.sm(Wn[0], Wn[1], m) < j / n) lo = m; else hi = m }
      const p = along(pathFor(id, dest), j / n * Lt); const amt = id === 'B' ? .45 : .7 * (j === n ? 1.2 : .8);
      if (id === 'B' && j % 2 && j !== n) continue;
      S.say(ac, out, id, t0 + lo, 'step', amt, panAt(p[0], lo)) }
  }
  // the lamp catches behind the paper: a warm swell rising into the stage's own hum and shutter
  S.grain(ac, out, t0 + 2.12, { bp: 900, q: .8, d: .35, a: .06, pan: 0, att: .2 });
  S.cloud(ac, out, t0 + 2.2, 1.3, 30, { f: 98, a: .035, d: [.2, .5], spread: .15 }, uu => Math.sin(Math.PI * Math.min(1, uu * 1.4)));
  S.cloud(ac, out, t0 + 2.5, .95, 40, { bp: 2200, a: .025, d: [.01, .04], spread: .9 }, uu => Math.sin(Math.PI * uu)); // paper crackling at the light's edge
  for (let k = 0; k < 12; k++) S.grain(ac, out, t0 + 2.5 + k / 12, { bp: 5200, q: 6, d: .006, a: .004 + .008 * k / 11, pan: 0, att: .2 });
}

TRANSITION({
  k: 0, scion: 50, lineage: 'SCION-LOC-PRINT-ARCHIVE · Library of Congress, Historical Print Stage',
  op: 'Transillumination: a hand-coloured engraved print of the house is cropped to the parlour and the lamp is lit behind the paper, so hatched ink thickens into black card and the paper becomes the backlit glass of the shadow stage.',
  made: 'An engraved, plate-marked section of the boarding house on laid paper (hatched poché walls and slabs, ruled wall tones, latent furniture holding every later piece of evidence), with the title engraved in the caption; the four sacks are engraved figures with the colourist\'s wash for their attributes. Catalogue brackets mark each as an item: solid corners for the documented figure, dashed corners and dotted paths for invented motion.',
  moved: 'A scan-crop camera closes from the whole plate onto the parlour, whose lines are drawn on deed 0\'s own set; the doer and the victim hop down through the house along dotted paths to their marks while the other two turn toward the parlour and are cropped out. A ragged light front spreading from the lamp turns the print into the deed\'s first frame, which is composited with the film\'s levers.',
  dur: DUR,
  draw(g, u, X, K) { draw(g, u, X, K) },
  sound(ac, out, t0, X, K) { sound(ac, out, t0, X, K) }
});
})();
