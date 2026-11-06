// 10 · SLANDER — SCION-TERRY-GILLIAM (Comic Cutout Metamorphosis)
// Every figure is a scissor-cut paper card: engraved hatching clipped to the card, ink outline, drop shadow.
// Sacks are built from pivoting cards (body, hinge-jaw lid, two ear flaps, attribute cards).
// Time is stepped at 12 cards per second (held frames), the way cutout animation is shot.
(function () {
const SL_DP = {
  R: { horn: 0.75, hand: 1.1, bits: 'coin', L: [1.35, 1.6, 1.85, 2.1, 2.3], D: 0.45, rock: 1, arc: 260, openAt: 0.9, hornCol: '#9a7a3a' },
  B: { horn: 1.7, hand: 1.9, bits: 'blot', L: [1.55, 1.55, 1.8, 1.8, 2.0], D: 0.33, rock: 0, arc: 160, openAt: 1.15, hornCol: '#b8893a' },
  I: { horn: 0.0, hand: 0.9, bits: 'fly', L: [1.15, 1.4, 1.85, 1.6, 2.0], D: 0.75, rock: 0, arc: 340, openAt: 0.7, hornCol: '#c9b48a' },
  O: { horn: 0.6, hand: 1.15, bits: 'rat', L: [1.65, 1.85, 2.05, 2.25, 2.4], D: 0.25, rock: 0, arc: 60, openAt: 1.0, hornCol: '#7a3b8f' }
};
const SL_CT = 2.75, SL_CROWDX = [760, 885, 1010, 1135, 1260];
DEED({
  n: 10, key: 'slander', title: 'Slander',
  scion: 1, lineage: 'Terry Gilliam — Comic Cutout Metamorphosis',
  op: 'The doer\'s lid hinges open, a horn and a pointing hand pop out, black cutout bits fly to each onlooker and the last one splats an ink blot and a pinned rat-tag on the victim; the onlookers turn their backs and the victim shrinks.',
  made: 'Scissor-cut paper cards with engraved hatching, ink outlines and drop shadows, laid on an engraved sepia room with a hanging lamp and a moonlit window. Each sack is a body card, a hinge-jaw lid card, two ear flaps and its attribute card; the onlookers are top-hat and bonnet profile silhouettes cut from black-hatched paper.',
  moved: 'Pivot joints and hard substitutions stepped at 12 cards per second: lids hinge open, horns and lazy-tong hands pop in at full size, onlookers flip like cards and slide away. Scale is the punchline: the marked victim is shrunk on its base pivot and the blot drips down its card.',
  contact: 2.75,
  leaves: { A: [], V: ['blot', 'tag'] },
  marks(t0, A, V, K) {
    const t = Math.floor(t0 * 12 + 1e-6) / 12, C = K.CAST, FY = 790, CT = SL_CT, DP = SL_DP[A], sm = K.sm, eo = K.eo;
    const BUL = { R: 0.10, B: 0.12, I: 0.16, O: 0.06 }, EXTRA = { R: 0, B: 0, I: 36, O: 18 };
    const lean = sm(0.4, DP.openAt, t) - sm(4.0, 4.6, t), after = sm(CT + 0.3, CT + 1.0, t);
    let aSy = 1, aDX = 0;
    if (A === 'B') { aSy = 1 + 0.05 * lean + 0.05 * after; aDX = 30 * lean; }
    if (A === 'O') aSy = 1 + 0.06 * lean;
    const box = (id, x, sc, sx, sy) => { const c = C[id], w = (c.w * (1 + 2 * BUL[id]) + 2 * EXTRA[id]) * sc * sx, h = c.h * 1.08 * sc * sy; return { x: x - w / 2, y: FY - h, w, h }; };
    const shrink = K.lerp(1, { R: 0.66, B: 0.5, I: 0.66, O: 0.64 }[V], eo(CT + 0.7, CT + 1.9, t));
    const recoil = t >= CT ? Math.max(0, 1 - (t - CT) * 4) : 0, droop = sm(CT, CT + 0.8, t);
    let vsx = 1, vsy = 1;
    if (V === 'R') vsx = 1 - 0.08 * droop; if (V === 'B') vsy = 1 - 0.05 * droop; if (V === 'I') { vsy = 1 - 0.22 * droop; vsx = 1 + 0.15 * droop; }
    return { A: box(A, 470 + aDX, 1, 1, aSy), V: box(V, 1450 + 90 * eo(CT + 0.7, CT + 1.9, t) + 16 * recoil, shrink, vsx, vsy) };
  },
  sound(ac, out, t0, A, V, K) {
    const S = K.SND, CT = SL_CT, DP = SL_DP[A], hs = K.hash, pan = x => Math.max(-1, Math.min(1, x / 960 - 1));
    const pA = pan(470), pV = pan(1450), mf = m => 440 * Math.pow(2, (m - 69) / 12);
    const T = x => t0 + x;
    // idle breath of both sacks
    S.say(ac, out, A, T(0.05), 'breathe', 0.5, pA);
    // doer's own body under the deed
    if (A === 'R') for (let x = 0.7; x < 4.3; x += 0.63) S.say(ac, out, 'R', T(x), 'step', 0.7, pA);
    if (A === 'B') { S.say(ac, out, 'B', T(0.9), 'step', 0.8, pA); }
    if (A === 'I') S.say(ac, out, 'I', T(0.6), 'breathe', 1.6, pA);
    if (A === 'O') S.say(ac, out, 'O', T(0.85), 'tick', 1, pA);
    // lid hinge creak, then the horn pops in (Inigo: his ear crinkles into a cone)
    S.cloud(ac, out, T(DP.openAt), 0.25, 90, { f: mf(50), glide: 0.6, noise: 0.6, bp: 900, a: 0.05, d: [0.02, 0.05], type: 'triangle', spread: 0.1 }, u => 1 - u * 0.5);
    if (A === 'I') S.cloud(ac, out, T(DP.openAt), 0.6, 120, { bp: 3200, a: 0.05, d: [0.006, 0.02], spread: 0.1 }, u => 1 - u);
    else { S.grain(ac, out, T(DP.openAt + 0.17), { f: 260, glide: 1.8, d: 0.07, a: 0.32, pan: pA, att: 0.1 }); S.grain(ac, out, T(DP.openAt + 0.17), { bp: 2200, d: 0.03, a: 0.25, pan: pA }); }
    // lazy-tong hand: ratchet out, ratchet back
    const t1 = DP.openAt + 0.5, hd = A === 'O' ? 0.2 : A === 'I' ? 0.8 : A === 'R' ? 0.6 : 0.3;
    for (let x = 0; x < hd; x += 1 / 24) S.grain(ac, out, T(t1 + x), { bp: 3600, q: 4, d: 0.012, a: 0.14, pan: pan(600 + 600 * x / hd) });
    for (let x = 0; x < 0.3; x += 1 / 20) S.grain(ac, out, T(4.2 + x), { bp: 3000, q: 4, d: 0.012, a: 0.1, pan: pan(1100 - 1500 * x) });
    // honks: each story bit leaves the horn with the doer's honk, flies on a slide whistle, lands with a pock and a murmur
    const honk = (when, big) => {
      const a = big ? 1.5 : 1;
      if (A === 'R') { for (let k = 0; k < 4; k++) S.grain(ac, out, when + k * 0.03, { f: 330, d: 0.06, a: 0.07 * a, type: 'square', pan: pA }); }
      if (A === 'B') { for (let k = 0; k < 6; k++) S.grain(ac, out, when + k * 0.035, { f: 98 * (1 - k * 0.01), d: 0.09, a: 0.06 * a, type: 'sawtooth', pan: pA }); S.thump(ac, out, when, 0.28 * a, 60, pA); }
      if (A === 'I') S.cloud(ac, out, when, 0.25, 60, { f: 220, noise: 0.8, bp: 1200, a: 0.06 * a, d: [0.03, 0.07], spread: 0.1 }, u => Math.sin(Math.PI * u));
      if (A === 'O') { S.grain(ac, out, when, { f: 1175, d: 0.09, a: 0.06 * a, type: 'square', pan: pA }); S.grain(ac, out, when + 0.05, { f: 1397, d: 0.06, a: 0.05 * a, type: 'square', pan: pA }); }
    };
    const whistle = (when, dur, x0, x1, big) => {
      const f0 = A === 'B' ? 400 : A === 'O' ? 1400 : 800;
      for (let k = 0; k < 8; k++) { const u = k / 8; S.grain(ac, out, when + u * dur, { f: f0 * (1 + 0.5 * Math.sin(Math.PI * u)) * (A === 'I' ? 1 + 0.08 * Math.sin(k * 3) : 1), d: dur / 7, a: (big ? 0.07 : 0.045), pan: pan(x0 + (x1 - x0) * u), att: 0.5 }); }
    };
    for (let k = 0; k < 5; k++) {
      const L = DP.L[k], hx = SL_CROWDX[k];
      honk(T(L), false);
      whistle(T(L), DP.D, 600, hx, false);
      S.grain(ac, out, T(L + DP.D), { f: 520 + 80 * k, glide: -0.4, d: 0.04, a: 0.2, pan: pan(hx), att: 0.1 });
      S.cloud(ac, out, T(L + DP.D + 0.03), 0.5, 50, { bp: 380 + 60 * hs(k), noise: 1, a: 0.035, d: [0.05, 0.12], spread: 0.2 }, u => Math.sin(Math.PI * u));
    }
    const DL = DP.D + 0.1;
    honk(T(CT - DL), true); whistle(T(CT - DL), DL, 600, 1450, true);
    S.say(ac, out, V, T(2.05), 'tick', 0.8, pV);
    // CONTACT: the splat (strongest sound), then the tag slapped on and pinned
    S.thump(ac, out, T(CT), 1.5, 70, pV);
    S.grain(ac, out, T(CT), { bp: 900, q: 0.8, d: 0.12, a: 0.55, pan: pV, att: 0.05 });
    S.cloud(ac, out, T(CT), 0.3, 260, { bp: 1400, noise: 1, a: 0.06, d: [0.008, 0.03], spread: 0.3 }, u => Math.pow(1 - u, 2));
    S.say(ac, out, V, T(CT + 0.06), 'react', 1, pV);
    S.grain(ac, out, T(CT + 0.25), { bp: 2600, q: 1, d: 0.045, a: 0.4, pan: pV, att: 0.05 });
    S.grain(ac, out, T(CT + 0.33), { f: 2400, d: 0.015, a: 0.12, pan: pV, att: 0.05 });
    for (const x of [0.6, 1.0, 1.45]) S.grain(ac, out, T(CT + x), { f: 1500, glide: -0.5, d: 0.05, a: 0.06, pan: pV, att: 0.1 });
    // onlookers flip their cards and shuffle away
    for (let k = 0; k < 5; k++) { const tw = CT + 0.45 + k * 0.12, x = SL_CROWDX[k];
      S.grain(ac, out, T(tw), { bp: 3200, q: 2, d: 0.02, a: 0.22, pan: pan(x) });
      S.cloud(ac, out, T(tw + 0.05), 0.8, 60, { bp: 1100, noise: 1, a: 0.018, d: [0.04, 0.1], spread: 0.15 }, u => 1 - u); }
    // the victim shrinks: a falling slide whistle on top of its own sink
    for (let k = 0; k < 10; k++) { const u = k / 10; S.grain(ac, out, T(CT + 0.7 + u * 1.2), { f: 900 * Math.pow(0.35, u), d: 0.14, a: 0.06, pan: pV, att: 0.5 }); }
    S.say(ac, out, V, T(CT + 0.75), 'sink', 1, pV);
    // horn pops back out, lid clacks shut, doer settles
    if (A !== 'I') S.grain(ac, out, T(4.17), { f: 520, glide: -0.6, d: 0.07, a: 0.22, pan: pA, att: 0.1 });
    S.grain(ac, out, T(4.4), { bp: 700, d: 0.05, a: 0.3, pan: pA, att: 0.05 });
    S.say(ac, out, A, T(4.42), 'land', 0.5, pA);
  },
  draw(g, t0, A, V, K, opt) {
    const LY = opt && opt.layer, SBG = !LY || LY === 'bg', SA = !LY || LY === 'A', SV = !LY || LY === 'V';
    const CARRY = (opt && opt.carry) || {};
    const W = K.W, H = K.H, cl = K.cl, lerp = K.lerp, sm = K.sm, eo = K.eo, hs = K.hash;
    const t = Math.floor(t0 * 12 + 1e-6) / 12;          // held frames
    const C = K.CAST, CT = 2.75, FY = 790;
    const INK = '#1b1410';

    // ---------- paper-cut primitives ----------
    function jit(pts, seed, a) { return pts.map((p, i) => [p[0] + (hs(seed + i * 3.1) - .5) * a, p[1] + (hs(seed + i * 7.7 + 1) - .5) * a]); }
    function path(pts) { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath(); }
    function bbox(pts) { let a = 1e9, b = 1e9, c = -1e9, d = -1e9; for (const p of pts) { a = Math.min(a, p[0]); b = Math.min(b, p[1]); c = Math.max(c, p[0]); d = Math.max(d, p[1]); } return [a, b, c, d]; }
    // card: fill + engraved hatch clipped + ink edge + lifted shadow
    function card(pts, fill, o) {
      o = o || {};
      const sp = o.sp || 7, ang = o.ang == null ? -0.8 : o.ang, ink = o.ink || INK;
      if (o.shadow !== false) { g.save(); g.translate(o.sx || 5, o.sy || 7); path(pts); g.fillStyle = 'rgba(20,12,6,.38)'; g.fill(); g.restore(); }
      path(pts); g.fillStyle = fill; g.fill();
      if (sp > 0) {
        g.save(); path(pts); g.clip();
        const [x0, y0, x1, y1] = bbox(pts), cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, R = Math.hypot(x1 - x0, y1 - y0) / 2 + 4;
        g.strokeStyle = o.hc || 'rgba(40,24,12,.30)'; g.lineWidth = o.hw || 1.2;
        const ca = Math.cos(ang), sa = Math.sin(ang);
        g.beginPath();
        for (let d = -R; d <= R; d += sp) {
          // engraving: lines thicken toward the shaded (right/bottom) side by being doubled
          const px = cx - sa * d, py = cy + ca * d;
          g.moveTo(px - ca * R, py - sa * R); g.lineTo(px + ca * R, py + sa * R);
        }
        g.stroke();
        if (o.shade) { // cross hatch on one side
          g.strokeStyle = 'rgba(30,18,8,.26)'; g.beginPath();
          for (let d = -R; d <= R; d += sp * 1.3) { const px = x1 - (x1 - x0) * o.shade + d * 0.2, py = cy + d; g.moveTo(px, py - R); g.lineTo(px + R, py - R * 0.2 + d * 0.1); }
          g.stroke();
        }
        g.restore();
      }
      path(pts); g.strokeStyle = ink; g.lineWidth = o.lw || 2.6; g.lineJoin = 'round'; g.stroke();
    }
    function blotPts(r, seed, n, spike) {
      const p = [];
      for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2; const k = hs(seed + i * 1.7); const rr = r * (0.7 + 0.3 * k + (i % 3 === 0 ? spike * hs(seed + i * 9.1) : 0)); p.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
      return p;
    }
    function inkBlot(x, y, r, seed, sc, drip) {
      if (sc <= 0) return;
      g.save(); g.translate(x, y); g.scale(sc, sc);
      g.fillStyle = INK;
      path(blotPts(r, seed, 22, 0.55)); g.fill();
      for (let i = 0; i < 6; i++) { const a = hs(seed + i * 4.3) * 6.28, d = r * (1.15 + hs(seed + i) * 0.5); g.beginPath(); g.arc(Math.cos(a) * d, Math.sin(a) * d, r * (0.06 + hs(seed + i * 2) * 0.1), 0, 7); g.fill(); }
      if (drip > 0) for (let i = 0; i < 3; i++) { const dx = (i - 1) * r * 0.45 + (hs(seed + i * 5) - .5) * r * .2, L = drip * r * (0.6 + hs(seed + 11 + i) * 0.9); g.fillRect(dx - r * .06, r * 0.4, r * .12, L); g.beginPath(); g.arc(dx, r * .4 + L, r * .1, 0, 7); g.fill(); }
      g.restore();
    }
    function ratSil(sc) { // black paper rat in profile facing +x, centred
      g.save(); g.scale(sc, sc); g.fillStyle = INK; g.beginPath();
      g.ellipse(0, 0, 30, 15, 0, 0, 7); g.fill();
      g.beginPath(); g.moveTo(22, -9); g.lineTo(48, 2); g.lineTo(22, 9); g.fill();
      g.beginPath(); g.arc(18, -13, 6, 0, 7); g.fill();
      g.lineWidth = 3; g.strokeStyle = INK; g.beginPath(); g.moveTo(-28, 2); g.quadraticCurveTo(-55, -8, -62, 14); g.stroke();
      g.lineWidth = 3.5; g.beginPath(); for (const fx of [-16, 12]) { g.moveTo(fx, 10); g.lineTo(fx - 3, 20); } g.stroke();
      g.restore();
    }
    function fly(sc, flap) {
      g.save(); g.scale(sc, sc); g.fillStyle = INK; g.beginPath(); g.ellipse(0, 0, 10, 6, 0, 0, 7); g.fill();
      g.fillStyle = 'rgba(30,20,12,.55)'; g.beginPath(); g.ellipse(-2, -8 - flap * 3, 9, 5, -0.5, 0, 7); g.fill(); g.beginPath(); g.ellipse(3, -8 + flap * 3, 9, 5, 0.5, 0, 7); g.fill();
      g.restore();
    }
    function coinBlack(sc) { g.save(); g.scale(sc, sc); g.fillStyle = INK; g.beginPath(); g.arc(0, 0, 13, 0, 7); g.fill(); g.strokeStyle = '#8a6a30'; g.lineWidth = 2; g.beginPath(); g.arc(0, 0, 9, 0, 7); g.stroke(); g.restore(); }
    function star(x, y, r, seed, col) { const p = []; for (let i = 0; i < 18; i++) { const a = i / 18 * 6.283, rr = r * (i % 2 ? 0.45 : 1) * (0.8 + hs(seed + i) * .3); p.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); } card(p, col, { sp: 0, lw: 3, shadow: false }); }

    // ---------- backdrop (engraved sepia room, cached; pure of t) ----------
    const BG = (this._bg = this._bg || (() => {
      const c = document.createElement('canvas'); c.width = W; c.height = H; const b = c.getContext('2d');
      const gg = g; g = b;
      b.fillStyle = '#cdb68c'; b.fillRect(0, 0, W, H);
      // wall: engraved horizontal hatching, denser at the top (night)
      for (let y = 0; y < FY; y += 4) { const k = 1 - y / FY; b.strokeStyle = `rgba(50,30,14,${0.10 + 0.32 * k * k})`; b.lineWidth = 1 + 1.2 * k; b.beginPath(); b.moveTo(0, y + Math.sin(y * .13) * .8); b.lineTo(W, y); b.stroke(); }
      // wallpaper lozenges (engraved pattern)
      b.strokeStyle = 'rgba(60,36,16,.18)'; b.lineWidth = 1.5;
      for (let y = 40; y < FY - 120; y += 90) for (let x = (y / 90 % 2) * 60; x < W; x += 120) { b.beginPath(); b.moveTo(x, y - 22); b.lineTo(x + 14, y); b.lineTo(x, y + 22); b.lineTo(x - 14, y); b.closePath(); b.stroke(); }
      // wainscot
      card([[0, FY - 150], [W, FY - 150], [W, FY], [0, FY]], '#a88b5c', { sp: 5, ang: Math.PI / 2, shadow: false, lw: 3 });
      for (let x = 60; x < W; x += 220) card([[x, FY - 128], [x + 170, FY - 128], [x + 170, FY - 22], [x, FY - 22]], '#b69a69', { sp: 6, ang: 0.0, shadow: false, lw: 2 });
      // window with cut-out moon
      card([[1180, 120], [1540, 120], [1540, 470], [1180, 470]], '#1e2a3a', { sp: 5, ang: -0.3, hc: 'rgba(150,170,200,.16)', lw: 6 });
      card(jit([[1300, 170], [1350, 165], [1385, 195], [1395, 240], [1375, 285], [1340, 305], [1300, 300], [1330, 275], [1345, 240], [1338, 200]], 91, 3), '#efe3bd', { sp: 8, ang: 0.6 });
      b.strokeStyle = INK; b.lineWidth = 10; b.beginPath(); b.moveTo(1360, 120); b.lineTo(1360, 470); b.moveTo(1180, 295); b.lineTo(1540, 295); b.stroke();
      card([[1160, 466], [1560, 466], [1572, 492], [1148, 492]], '#7d6038', { sp: 4, ang: 0 });
      // picture frame (engraved ancestor = blank oval, no face)
      card([[260, 160], [470, 160], [470, 420], [260, 420]], '#6b4b26', { sp: 4, ang: 0.8, lw: 3 });
      b.save(); b.beginPath(); b.ellipse(365, 290, 80, 105, 0, 0, 7); b.fillStyle = '#d8c49a'; b.fill(); b.strokeStyle = INK; b.lineWidth = 2; b.stroke(); b.restore();
      // floor boards in perspective
      b.fillStyle = '#8b6a40'; b.fillRect(0, FY, W, H - FY);
      for (let i = -20; i <= 20; i++) { b.strokeStyle = 'rgba(30,18,8,.55)'; b.lineWidth = 2; b.beginPath(); b.moveTo(W / 2 + i * 60, FY); b.lineTo(W / 2 + i * 260, H); b.stroke(); }
      for (let y = FY; y < H; y += 5) { b.strokeStyle = 'rgba(30,18,8,.16)'; b.lineWidth = 1; b.beginPath(); b.moveTo(0, y); b.lineTo(W, y); b.stroke(); }
      b.strokeStyle = INK; b.lineWidth = 4; b.beginPath(); b.moveTo(0, FY); b.lineTo(W, FY); b.stroke();
      // lamp pool + vignette
      const rg = b.createRadialGradient(900, 360, 40, 900, 420, 1100); rg.addColorStop(0, 'rgba(255,220,150,.28)'); rg.addColorStop(.5, 'rgba(255,200,120,.06)'); rg.addColorStop(1, 'rgba(10,6,2,.55)');
      b.fillStyle = rg; b.fillRect(0, 0, W, H);
      g = gg; return c;
    })());
    if (SBG) g.drawImage(BG, 0, 0);
    // hanging lamp (cutout, swings a little)
    if (SBG) {
      const sw = Math.sin(t * 2.1) * 0.03;
      g.save(); g.translate(900, 0); g.rotate(sw);
      g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 150); g.stroke();
      card([[-60, 150], [60, 150], [90, 230], [-90, 230]], '#8f6a2c', { sp: 5, ang: 0.4 });
      card([[-22, 230], [22, 230], [30, 290], [-30, 290]], '#f7e7b0', { sp: 9, ang: 0, hc: 'rgba(180,120,40,.25)' });
      g.restore();
    }

    // ---------- the four sacks as card rigs ----------
    const JF = { R: 0.22, B: 0.24, I: 0.26, O: 0.2 };
    function sackBody(id) {
      const c = C[id], w = c.w, h = c.h, sh = h * (1 - JF[id]);
      const bul = id === 'B' ? 0.12 : id === 'I' ? 0.16 : id === 'R' ? 0.10 : 0.06;
      const pts = []; const N = 9, rb = Math.min(w, h) * 0.18;
      // left side bottom-up, bulging belly, rounded bottom corners
      for (let i = 0; i <= N; i++) { const s = i / N; pts.push([-w / 2 - w * bul * Math.sin(Math.PI * (0.15 + 0.85 * s)) * (1 - s * 0.6) + (id === 'I' ? -w * 0.08 * (1 - s) : 0), -sh * s]); }
      for (let i = N; i >= 0; i--) { const s = i / N; pts.push([w / 2 + w * bul * Math.sin(Math.PI * (0.15 + 0.85 * s)) * (1 - s * 0.6) + (id === 'I' ? w * 0.08 * (1 - s) : 0), -sh * s]); }
      // round bottom: replace corners with arc points
      const bot = []; for (let i = 1; i < 8; i++) { const a = i / 8; bot.push([lerp(w / 2, -w / 2, a), 4 * Math.sin(Math.PI * a)]); }
      pts.push(...bot);
      return jit(pts, id.charCodeAt(0) * 13, 3);
    }
    function sackLid(id) { // local to hinge at (-w/2, -sh); top edge sags between two corner peaks
      const c = C[id], w = c.w, h = c.h, lh = h * JF[id];
      const sag = id === 'I' ? lh * 0.45 : lh * 0.28;
      const bul = id === 'B' ? 0.04 : 0.02;
      return jit([[-w * bul, 0], [w * (1 + bul), 0], [w + 4, -lh * 0.6], [w + 2, -lh * 1.12], [w - w * 0.12, -lh * 0.95], [w * 0.5, -lh + sag], [w * 0.12, -lh * 0.95], [-2, -lh * 1.12], [-4, -lh * 0.6]], id.charCodeAt(0) * 7, 2.5);
    }
    // pose: x, base y, sc (uniform), sx, sy, rot (about base), jaw (0..1), earA (0 rest .. +1 perk .. -1 droop), wigSlip, mark
    function drawSack(id, P) {
      const c = C[id], w = c.w, h = c.h, sh = h * (1 - JF[id]), lh = h * JF[id];
      const cy = CARRY[id] || [], has = k => cy.indexOf(k) >= 0;
      if (has('emptied')) P.sy = (P.sy || 1) * 0.82;
      if (has('drowsy')) { P.earA = (P.earA || 0) - 0.8; P.rot = (P.rot || 0) + 0.06; }
      if (has('wig') && id === 'O') { P.wigRot = Math.max(P.wigRot || 0, 0.38); P.wigDx = Math.max(P.wigDx || 0, 10); }
      g.save(); g.translate(P.x, P.y); g.rotate(P.rot || 0); g.scale((P.sc || 1) * (P.sx || 1), (P.sc || 1) * (P.sy || 1));
      // floor shadow
      g.save(); g.scale(1, 0.18); g.beginPath(); g.ellipse(8, 0, w * 0.62, w * 0.3, 0, 0, 7); g.fillStyle = 'rgba(20,10,4,.35)'; g.fill(); g.restore();
      const body = sackBody(id);
      card(body, c.fill, { sp: 6.5, ang: -0.9, shade: 0.25 });
      // stitched seam at lid
      g.strokeStyle = 'rgba(40,25,12,.6)'; g.lineWidth = 1.6; g.setLineDash([6, 5]); g.beginPath(); g.moveTo(-w / 2 + 4, -sh + 6); g.lineTo(w / 2 - 4, -sh + 6); g.stroke(); g.setLineDash([]);
      if (id === 'B') { // belt + wheat stencil
        const by = -h * 0.4;
        card(jit([[-w / 2 - w * 0.09, by + 12], [w / 2 + w * 0.09, by + 12], [w / 2 + w * 0.09, by - 12], [-w / 2 - w * 0.09, by - 12]], 55, 2), '#2a2622', { sp: 4, ang: 0, hc: 'rgba(200,180,150,.12)', shadow: false });
        card([[-14, by - 15], [14, by - 15], [14, by + 15], [-14, by + 15]], '#8c7a52', { sp: 0, shadow: false, lw: 2 });
        const wy = -h * 0.64; g.save(); g.translate(0, wy);
        g.strokeStyle = '#6a5132'; g.lineWidth = 3; g.beginPath(); g.arc(0, 0, 34, 0, 7); g.stroke();
        g.beginPath(); g.moveTo(0, 26); g.lineTo(0, -24); g.stroke();
        g.fillStyle = '#6a5132'; for (let k = 0; k < 4; k++) { const yy = -18 + k * 10; g.beginPath(); g.ellipse(-7, yy, 6, 3, -0.7, 0, 7); g.fill(); g.beginPath(); g.ellipse(7, yy, 6, 3, 0.7, 0, 7); g.fill(); }
        g.restore();
      }
      carried(cy, has, id, w, h, sh);
      if (P.mark) P.mark(w, h, sh);
      // lid on its hinge (back-left top corner)
      g.save(); g.translate(-w / 2, -sh); g.rotate(-(P.jaw || 0) * (id === 'B' ? 0.7 : 0.55));
      if (P.mouth) { g.save(); P.mouth(w, lh); g.restore(); }
      const lid = sackLid(id);
      card(lid, id === 'R' ? '#6e3a33' : c.fill, id === 'R' ? { sp: 4, ang: 0.9, hc: 'rgba(250,220,200,.14)' } : { sp: 6.5, ang: -0.9 });
      if (id === 'R') { g.fillStyle = '#6e3a33'; for (let k = 0; k < 9; k++) { const x = 10 + k * (w - 20) / 8; g.beginPath(); g.moveTo(x - 7, 0); g.lineTo(x + 7, 0); g.lineTo(x, 13); g.fill(); g.strokeStyle = INK; g.lineWidth = 1.2; g.stroke(); } }
      // ears: flaps at top corners
      const ea = P.earA || 0;
      for (const s of [-1, 1]) {
        const ex = s < 0 ? 4 : w - 4, ey = -lh + 4;
        g.save(); g.translate(ex, ey);
        if (id === 'I') {
          const L = h * 0.95; g.rotate(s * (0.22 - ea * 0.5));
          card(jit([[0, -4], [s * 26, 2], [s * 36, L * 0.55], [s * 30, L], [s * 14, L * 0.95], [s * 6, L * 0.45]], 70 + s, 2), '#d4bf93', { sp: 4.5, ang: 1.4, lw: 2.8 });
        } else {
          const L = (id === 'B' ? 40 : id === 'R' ? 30 : 24);
          g.rotate(s * (0.5 - ea * 0.55));
          card([[-10, 4], [10, 4], [s * 4, -L]], id === 'R' ? '#6e3a33' : c.fill, { sp: 5, ang: 0.3, lw: 2.2 });
        }
        g.restore();
      }
      if (id === 'O') { // purple wig card, long, past the shoulders
        g.save(); g.translate(w / 2, -lh); g.rotate(P.wigRot || 0); g.translate(P.wigDx || 0, 0);
        const wg = jit([[-w / 2 - 14, 20], [-w / 2 - 6, -12], [-w * 0.2, -30], [w * 0.2, -30], [w / 2 + 6, -12], [w / 2 + 14, 20], [w / 2 + 18, sh * 0.45], [w / 2 + 6, sh * 0.62], [w / 2 - 4, sh * 0.5], [w / 2 - 6, 22], [-w / 2 + 6, 22], [-w / 2 + 4, sh * 0.5], [-w / 2 - 6, sh * 0.62], [-w / 2 - 18, sh * 0.45]], 333, 2);
        card(wg, '#7a3b8f', { sp: 3.5, ang: 1.45, hc: 'rgba(20,0,30,.35)' });
        g.restore();
      }
      g.restore();
      if (has('cinched')) { cord(-w / 2 - 6, -sh + 4, w / 2 + 6, -sh + 4, 7); }
      if (has('greyed')) { path(sackBody(id)); g.fillStyle = 'rgba(80,80,84,.42)'; g.fill(); }
      g.restore();
    }
    // a cord cut from brown paper, with a knot card
    function cord(x0, y0, x1, y1, th) {
      card([[x0, y0 - th / 2], [x1, y1 - th / 2], [x1, y1 + th / 2], [x0, y0 + th / 2]], '#6b4a22', { sp: 3, ang: 0.8, lw: 1.6, shadow: false, hc: 'rgba(20,10,0,.4)' });
      const mx = (x0 + x1) / 2 + 10; card([[mx - 8, y0 - 9], [mx + 8, y0 - 9], [mx + 10, y0 + 9], [mx - 10, y0 + 9]], '#5a3c18', { sp: 0, lw: 1.6, shadow: false });
    }
    // carried damage from earlier shots, drawn as pasted paper, at the sack's own scale
    function carried(cy, has, id, w, h, sh) {
      if (!cy.length) return;
      if (has('rope')) { cord(-w / 2 - 10, -h * 0.3, w / 2 + 10, -h * 0.3, 8); cord(-w / 2 - 12, -h * 0.58, w / 2 + 12, -h * 0.58, 8); }
      if (has('gag')) { const y = -sh + 18; card([[-w / 2 - 8, y - 9], [w / 2 + 8, y - 7], [w / 2 + 8, y + 9], [-w / 2 - 8, y + 9]], '#efe6cf', { sp: 5, ang: 0, lw: 1.8, shadow: false }); card([[w / 2, y - 6], [w / 2 + 22, y + 14], [w / 2 + 12, y + 20]], '#efe6cf', { sp: 0, lw: 1.6, shadow: false }); }
      if (has('blot')) inkBlot(w * 0.22, -h * 0.3, Math.max(14, w * 0.16), 991 + id.charCodeAt(0), 1, 0.6);
      if (has('tag')) { g.save(); g.translate(-w * 0.2, -h * 0.22); g.rotate(0.2); const tw = Math.max(46, w * 0.34), th = tw * 0.62;
        card(jit([[-tw / 2, -th / 2], [tw / 2, -th / 2], [tw / 2, th / 2], [-tw / 2, th / 2]], 81, 3), '#efe6cf', { sp: 9, ang: 0.4, lw: 1.8 }); ratSil(tw / 150);
        g.fillStyle = '#b02a1a'; g.beginPath(); g.arc(-tw / 2 + 7, -th / 2 + 6, 4, 0, 7); g.fill(); g.restore(); }
      if (has('torn')) { g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); g.moveTo(w * 0.36, -h * 0.62); for (let k = 1; k <= 6; k++) g.lineTo(w * 0.36 + (k % 2 ? 9 : -4), -h * 0.62 + k * h * 0.06); g.stroke();
        card([[w * 0.3, 0], [w * 0.62, 0], [w * 0.5, -10]], '#fbf7ee', { sp: 0, lw: 1.2, shadow: false }); }
      if (has('emptied')) card(jit([[w * 0.42, 2], [w * 0.9, 2], [w * 0.7, -16], [w * 0.55, -14]], 61, 3), '#fbf7ee', { sp: 8, ang: 0, lw: 1.4, hc: 'rgba(120,100,70,.2)' });
      if (has('coins')) for (let k = 0; k < 3; k++) { g.save(); g.translate(w * 0.62 + k * 4, -6 - k * 8); g.scale(1, 0.4); g.beginPath(); g.arc(0, 0, 14, 0, 7); g.fillStyle = '#c9a23a'; g.fill(); g.strokeStyle = INK; g.lineWidth = 2.5; g.stroke(); g.restore(); }
    }

    // ---------- onlookers: profile cutout silhouettes ----------
    const CROWD = [
      { x: 760, k: 'hat', s: 1.2, d0: 1 }, { x: 885, k: 'bon', s: 1.1, d0: -1 }, { x: 1010, k: 'hat', s: 1.26, d0: 1 },
      { x: 1135, k: 'bow', s: 1.14, d0: -1 }, { x: 1260, k: 'bon', s: 1.2, d0: 1 }
    ];
    function onlooker(o, x, dir, neck, tilt, bob, hit) {
      g.save(); g.translate(x, H + 30 + bob - (tilt < 0 ? 18 : 0)); g.scale(o.s * dir, o.s * (tilt < 0 ? 1.06 : 1));
      const coat = o.k === 'bon' ? '#6a5466' : '#5a5248';
      // shoulders/coat
      card(jit([[-70, 0], [-62, -120], [-30, -165], [30, -165], [60, -125], [74, 0]], o.x, 3), coat, { sp: 4, ang: -0.6, hc: 'rgba(20,10,4,.35)' });
      // collar
      card([[-14, -168], [18, -168], [26, -140], [-6, -150]], '#e9dcc0', { sp: 0, lw: 1.6, shadow: false });
      // neck (stretches when gawking)
      g.save(); g.translate(4, -170); g.rotate(tilt);
      card([[-11, 0], [11, 0], [11, -18 - neck], [-11, -18 - neck]], '#3a332c', { sp: 0, lw: 1.8, shadow: false });
      g.translate(0, -18 - neck);
      // head in profile (nose bump gives direction; no features)
      const hp = [[-26, 2], [-30, -28], [-20, -52], [4, -58], [24, -48], [28, -36], [46, -26], [30, -18], [32, -8], [24, 2]];
      card(hp, '#4a4038', { sp: 4, ang: 0.7, hc: 'rgba(20,10,4,.35)', lw: 2.4 });
      if (o.k === 'hat') { card([[-38, -48], [38, -48], [36, -56], [24, -56], [24, -118], [-24, -118], [-24, -56], [-36, -56]], '#161210', { sp: 4, ang: 0, hc: 'rgba(230,210,180,.18)' }); }
      else if (o.k === 'bon') { card(jit([[-36, -10], [-40, -44], [-18, -72], [18, -70], [40, -46], [34, -36], [-8, -40], [-22, -8]], 7, 2), '#5a4258', { sp: 3.5, ang: 1.2, hc: 'rgba(240,220,230,.2)' }); }
      else { card([[-34, -50], [34, -50], [30, -58], [20, -58], [20, -82], [-20, -82], [-20, -58], [-30, -58]], '#251d18', { sp: 4, ang: 0, hc: 'rgba(230,210,180,.18)' }); }
      if (hit > 1) star(0, -40, 46, o.x, '#f4e7c4');
      if (hit > 0) { g.fillStyle = INK; g.beginPath(); g.arc(-22, -26, 5, 0, 7); g.fill(); }
      g.restore();
      g.restore();
    }

    // ---------- doer profile: how each sack slanders ----------
    const DP = SL_DP[A];
    const AX = 470, VX0 = 1450;
    const open = eo(DP.openAt, DP.openAt + 0.25, t) - eo(4.0, 4.4, t);
    const hornIn = (t >= DP.openAt + 0.17 && t < 4.17) ? 1 : 0;             // hard substitution pop
    const handIn = (t >= DP.openAt + 0.5 && t < 4.5) ? 1 : 0;
    // doer body action
    let aRot = 0, aSy = 1, aSx = 1, aEar = 0, aDX = 0;
    const lean = sm(0.4, DP.openAt, t) - sm(4.0, 4.6, t);
    const pulse = DP.L.reduce((s, L) => s + Math.max(0, 1 - Math.abs(t - L) * 8), 0);
    if (A === 'R') { aRot = 0.06 * Math.sin((t - 0.4) * 5) * sm(0.4, 0.9, t) * (1 - sm(4.2, 5.2, t)) + 0.04 * pulse; aEar = 0.6 * lean; }
    if (A === 'B') { aRot = -0.08 * lean + 0.1 * pulse; aSy = 1 + 0.05 * lean - 0.04 * pulse; aSx = 1 + 0.06 * pulse; aEar = 1 * lean; aDX = 30 * lean; }
    if (A === 'I') { aRot = -0.05 * lean + 0.02 * Math.sin(t * 3); aSy = 1 - 0.06 * Math.sin(t * 2.2) * lean; aEar = 0; }
    if (A === 'O') { aRot = -0.04 * lean + 0.02 * pulse; aSy = 1 + 0.06 * lean; aEar = 0.4 * lean; }
    // after the deed: doer's own satisfied beat
    const after = sm(CT + 0.3, CT + 1.0, t);
    if (A === 'R') aRot += 0.05 * Math.sin((t - CT) * 4) * after * (1 - sm(5.0, 5.4, t));
    if (A === 'B') aSy += 0.05 * after;
    if (A === 'O') aRot += -0.06 * after;
    if (A === 'I') aRot += -0.08 * after;

    // world position of the doer's mouth (lid hinge opening) — horn throat
    const cA = C[A], aSh = cA.h * (1 - JF[A]);
    const ax = AX + aDX;
    function mouthWorld() {
      const lx = cA.w * 0.75 * aSx, ly = -aSh * aSy;
      const c = Math.cos(aRot), s = Math.sin(aRot);
      return [ax + lx * c - ly * s, FY + lx * s + ly * c];
    }
    const M = mouthWorld();
    const hornLen = 110 + 160 * DP.horn;
    const hornAng = A === 'O' ? 0.05 : A === 'B' ? -0.38 : -0.42;
    const bell = A === 'I' ? [M[0] + 40, M[1] - 20] : [M[0] + Math.cos(hornAng) * hornLen, M[1] + Math.sin(hornAng) * hornLen];

    // crowd state
    const VSH = C[V];
    const hitT = DP.L.map(L => L + DP.D);
    const crowdState = CROWD.map((o, k) => {
      const ht = hitT[k];
      let dir = o.d0, neck = 0, tilt = 0, dx = 0, hit = 0;
      const turnAway = CT + 0.45 + k * 0.12;
      if (t >= ht) { dir = 1; hit = t < ht + 2 / 12 ? 1.4 : 1; neck = 60 * eo(ht, ht + 0.3, t) * (1 - sm(turnAway, turnAway + .25, t)); tilt = 0.12 * eo(ht, ht + .3, t); }
      if (t >= turnAway) { dir = -1; tilt = -0.32; neck = 0; dx = -(40 + k * 22) * eo(turnAway, turnAway + 0.8, t); }
      if (t >= turnAway && t < turnAway + 1 / 12) dir = -0.25;  // the card is edge-on for one frame
      const bob = (t < ht ? Math.sin(t * 3 + k) * 3 : 0);
      return { x: o.x + dx, dir, neck, tilt, bob, hit };
    });

    // victim state
    const vTarget = { R: 0.66, B: 0.5, I: 0.66, O: 0.64 }[V];
    const shrink = lerp(1, vTarget, eo(CT + 0.7, CT + 1.9, t));
    const recoil = t >= CT ? Math.max(0, 1 - (t - CT) * 4) : 0;
    const vP = { x: VX0 + 90 * eo(CT + 0.7, CT + 1.9, t) + 16 * recoil, y: FY, sc: shrink, rot: 0.1 * recoil, earA: 0, sx: 1, sy: 1 };
    // before contact the victim notices the crowd turning to it
    const notice = sm(1.9, 2.4, t) * (t < CT ? 1 : 0);
    const droop = sm(CT, CT + 0.8, t);
    if (V === 'R') { vP.rot += -0.03 * Math.sin(t * 5) * (1 - droop) * (t < 0.4 ? 0 : 1); vP.earA = 0.4 * notice - 1 * droop; vP.sx = 1 - 0.08 * droop; }
    if (V === 'B') { vP.rot += 0.04 * notice * Math.sin(t * 9); vP.earA = 0.5 * notice - 1 * droop; vP.sy = 1 - 0.05 * droop; }
    if (V === 'I') { vP.earA = 0.2 * notice - 0.3 * droop; vP.sy = 1 - 0.22 * droop; vP.sx = 1 + 0.15 * droop; }
    if (V === 'O') { vP.rot += 0.02 * notice; vP.earA = 0.3 * notice - 1 * droop; vP.wigRot = 0.38 * droop; vP.wigDx = 10 * droop; vP.rot += 0.08 * droop; }
    const vw = VSH.w, vh = VSH.h;
    const markY = V === 'I' ? -vh * 0.45 : V === 'O' ? -vh * 0.35 : -vh * 0.5;
    const blotR = { R: 50, B: 80, I: 44, O: 40 }[V];
    vP.mark = (w, h) => {
      if (t < CT) return;
      const u = t - CT;
      const sc = u < 1 / 12 ? 1.35 : u < 2 / 12 ? 0.92 : 1;
      inkBlot(-w * 0.05, markY, blotR, 77 + V.charCodeAt(0), sc, cl(0, 1.6, u * 0.9));
      if (u >= 0.25) { // the label card pasted on: torn paper with a black rat, and a pin
        const pu = u - 0.25; const ps = pu < 1 / 12 ? 1.7 : pu < 2 / 12 ? 0.9 : 1;
        g.save(); g.translate(w * 0.18, markY - blotR * 0.15); g.rotate(-0.22); g.scale(ps, ps);
        const tw = Math.max(80, w * 0.55), th = tw * 0.62;
        card(jit([[-tw / 2, -th / 2], [-tw * 0.1, -th / 2 - 3], [tw / 2, -th / 2], [tw / 2 + 3, th * 0.1], [tw / 2, th / 2], [-tw / 2, th / 2 + 2], [-tw / 2 - 2, 0]], 444, 4), '#efe6cf', { sp: 9, ang: 0.4, lw: 2.2 });
        ratSil(tw / 140);
        g.fillStyle = '#b02a1a'; g.beginPath(); g.arc(-tw / 2 + 9, -th / 2 + 8, 5, 0, 7); g.fill(); g.strokeStyle = INK; g.lineWidth = 1.5; g.stroke();
        g.restore();
      }
    };

    // ---------- the doer: horn, hand, lid ----------
    // pointing hand on lazy tongs from the doer toward the victim
    function pointingHand() {
      if (!handIn) return;
      const t1 = DP.openAt + 0.5, dur = A === 'O' ? 0.2 : A === 'I' ? 0.8 : A === 'R' ? 0.6 : 0.3;
      const ext = eo(t1, t1 + dur, t) * (1 - eo(4.2, 4.5, t));
      const base = A === 'O' ? [ax + cA.w * 0.3, FY - cA.h * 0.98] : A === 'I' ? [ax + cA.w * 0.4, FY - cA.h * 0.7] : [ax + cA.w * 0.1, FY - cA.h * 0.95];
      // the hand ends hovering above-left of the victim and points down at it
      const vtx = vP.x - vw * 0.25 * vP.sc, vty = FY - vh * vP.sc - 40;
      const reach = A === 'O' ? 1.0 : A === 'B' ? 0.82 : A === 'R' ? 0.7 : 0.62;
      const tx = lerp(base[0], lerp(base[0], vtx, reach), ext);
      const lift = A === 'O' ? -170 : A === 'B' ? -110 : A === 'R' ? -90 : 40;
      const ty = lerp(base[1], vty + lift * (1 - reach) - (A === 'O' ? 60 : 0), ext) + (A === 'I' ? 30 * Math.sin(t * 3) : 0);
      // lazy tongs: crossed cards
      const segs = A === 'O' ? 9 : A === 'B' ? 4 : 6, dx = (tx - base[0]) / segs, dy = (ty - base[1]) / segs;
      const len = Math.hypot(dx, dy) || 1, nx = -dy / len, ny = dx / len, amp = Math.max(6, 30 - len * 0.2) * (A === 'B' ? 1.6 : 1);
      for (let i = 0; i < segs; i++) {
        const p0 = [base[0] + dx * i, base[1] + dy * i], p1 = [base[0] + dx * (i + 1), base[1] + dy * (i + 1)];
        for (const sgn of [1, -1]) {
          const q0 = [p0[0] + nx * amp * sgn, p0[1] + ny * amp * sgn], q1 = [p1[0] - nx * amp * sgn, p1[1] - ny * amp * sgn];
          const ux = (q1[0] - q0[0]), uy = (q1[1] - q0[1]), ul = Math.hypot(ux, uy) || 1, wx = -uy / ul * 4, wy = ux / ul * 4;
          card([[q0[0] + wx, q0[1] + wy], [q1[0] + wx, q1[1] + wy], [q1[0] - wx, q1[1] - wy], [q0[0] - wx, q0[1] - wy]], sgn > 0 ? '#8a6a3a' : '#6e522a', { sp: 0, lw: 1.6, sx: 3, sy: 4 });
        }
        g.fillStyle = INK; g.beginPath(); g.arc(p1[0], p1[1], 3.5, 0, 7); g.fill();
      }
      const aim = Math.atan2((FY - vh * 0.6 * vP.sc) - ty, (vP.x) - tx);
      g.save(); g.translate(tx, ty); g.rotate(A === 'I' ? aim + 0.5 + Math.sin(t * 4) * 0.15 : aim);
      const hsz = DP.hand * (A === 'I' ? 1 : 1) * (0.6 + 0.4 * ext); g.scale(hsz, hsz);
      const glove = A === 'O' ? '#ece4f2' : A === 'R' ? '#e6d3b0' : '#f0e2c4';
      card([[-60, -26], [-18, -26], [-18, 26], [-60, 26]], A === 'O' ? '#7a3b8f' : A === 'R' ? '#6e3a33' : '#efe6cf', { sp: 5, ang: 1.57, lw: 2.2 });
      card(jit([[-20, -24], [12, -28], [26, -16], [96, -16], [104, -7], [96, 3], [30, 3], [32, 12], [24, 24], [-20, 26]], 9, 1.5), glove, { sp: 5, ang: -0.6, lw: 2.4, shade: 0.2 });
      g.strokeStyle = 'rgba(30,20,10,.75)'; g.lineWidth = 2; g.beginPath(); for (const y of [9, 17]) { g.moveTo(-2, y); g.lineTo(24, y); } g.moveTo(26, -16); g.lineTo(30, 3); g.stroke();
      g.restore();
    }
    function horn() {
      if (!hornIn) return;
      if (A === 'I') return; // Inigo uses his ear instead
      const kick = 1 + 0.12 * pulse;
      g.save(); g.translate(M[0], M[1]); g.rotate(hornAng); g.scale(kick, kick);
      const L = hornLen, r0 = 10, r1 = 30 + 55 * DP.horn;
      card(jit([[-8, -r0], [L * 0.6, -r0 - r1 * 0.2], [L, -r1], [L, r1], [L * 0.6, r0 + r1 * 0.2], [-8, r0]], 21, 2), DP.hornCol, { sp: 5, ang: 0.1, shade: 0.3, hc: 'rgba(40,20,0,.35)' });
      g.beginPath(); g.ellipse(L, 0, 14 + 8 * DP.horn, r1, 0, 0, 7); g.fillStyle = '#2a1a08'; g.fill(); g.strokeStyle = INK; g.lineWidth = 3; g.stroke();
      g.restore();
    }
    // Inigo: his ear lifts lazily and rolls into a paper cone (substitution)
    let aEarOverride = null;
    const doerPose = { x: ax, y: FY, rot: aRot, sx: aSx, sy: aSy, jaw: A === 'I' ? open * 0.25 : open, earA: aEar };
    if (A === 'I') {
      doerPose.mouth = null;
    }

    // ---------- story bits in flight ----------
    function bitAt(k, u, from, to, big) {
      const arcH = DP.arc + (big ? 60 : 0);
      for (let tr = 2; tr >= 0; tr--) {   // two held trail cards behind each bit
        const uu = u - tr * 0.07; if (uu < 0) continue;
        let x = lerp(from[0], to[0], uu), y = lerp(from[1], to[1], uu) - arcH * 4 * uu * (1 - uu);
        if (DP.bits === 'fly') { x += Math.sin(uu * 14 + k) * 30; y += Math.cos(uu * 11 + k * 2) * 24; }
        g.save(); g.translate(x, y); g.globalAlpha = tr ? 0.35 / tr : 1;
        const sc = (big ? 2.4 : 1.6) * (tr ? 0.7 : 1);
        if (DP.bits === 'coin') { g.rotate(uu * 8); coinBlack(sc * 1.1); }
        else if (DP.bits === 'blot') { g.rotate(uu * 5); inkBlot(0, 0, 16 * sc, k * 9, 1, 0); }
        else if (DP.bits === 'fly') { fly(sc * 1.4, Math.sin(t * 40 + k)); }
        else { g.rotate(Math.atan2(to[1] - from[1], to[0] - from[0])); ratSil(0.5 * sc); }
        g.restore();
      }
    }

    // ---------- draw order: bg (room, lamp, onlookers) -> V -> A ----------
    if (SBG) CROWD.forEach((o, k) => { const s = crowdState[k]; onlooker(o, s.x, s.dir, s.neck, s.tilt, s.bob, s.hit); });
    if (SV) {
      drawSack(V, vP);
      if (t >= CT && t < CT + 2 / 12) star(vP.x - vw * 0.05, FY + markY * vP.sc, blotR * 1.6, 5, '#f4e7c4');
    }
    if (SA) {
      drawSack(A, doerPose);
      if (A === 'I' && t >= DP.openAt) { // the rolled-ear cone on his right ear
        const lift = eo(DP.openAt, DP.openAt + 0.6, t) * (1 - eo(4.0, 4.5, t));
        g.save(); g.translate(ax + cA.w * 0.45, FY - cA.h * 0.92); g.rotate(-1.2 * lift + 0.6);
        if (lift > 0.3) card(jit([[0, -8], [120, -42], [126, 42], [0, 8]], 5, 2), '#e2cea5', { sp: 5, ang: 1.0, lw: 3 });
        if (lift > 0.3) { g.beginPath(); g.ellipse(123, 0, 12, 42, 0, 0, 7); g.fillStyle = '#3a2a18'; g.fill(); g.strokeStyle = INK; g.lineWidth = 3; g.stroke(); }
        g.restore();
      }
      horn();
      pointingHand();
      const from = A === 'I' ? [ax + cA.w * 0.45 + 125 * Math.cos(-0.6), FY - cA.h * 0.92 + 125 * Math.sin(-0.6)] : bell;
      for (let k = 0; k < 5; k++) {
        const L = DP.L[k], u = (t - L) / DP.D;
        if (u >= 0 && u < 1) { const cs = crowdState[k]; bitAt(k, u, from, [cs.x + 10, H + 30 - 240 * CROWD[k].s], false); }
      }
      const DL = DP.D + 0.1, L = CT - DL, u = (t - L) / DL;
      if (u >= 0 && u < 1) bitAt(9, u, from, [vP.x - vw * 0.05, FY + markY], true);
    }
    if (SBG) { // paper grain
      g.fillStyle = 'rgba(60,40,20,.05)';
      for (let i = 0; i < 40; i++) { const x = hs(i * 3.3 + Math.floor(t * 12)) * W, y = hs(i * 5.1 + 2) * H; g.fillRect(x, y, 2, 2); }
    }
  }
});
})();
