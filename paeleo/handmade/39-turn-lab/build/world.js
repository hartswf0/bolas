/* SCION 39 · Turn Lab — the place and the person, drawn for this film (no found pixels).
   A flat stage: the house front faces the camera; the porch floor is an oblique (depth lifts by K per metre), so nothing in
   the set implies a perspective the drawings do not have. The door is a true plane, so its swing is the one continuous
   rotation in the film (a plane may foreshorten; a dog may not). */
(function (G) {
  'use strict';
  const { K, crClosed, crOpen, tube, noise } = G.DOG;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const S = 225, OX = 290, WALL_Y = 556;        // px per metre; door centre; wall base on screen
  const DOOR = { half: 0.46, h: 2.05 };
  const CORNER = 1.75, PORCH_END = 4.31, PORCH_DEPTH = 2.5;
  const sx = u => OX + u * S;
  const gy = d => WALL_Y + d * K * S;            // ground y of a depth
  const INK = '#15110e';

  function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

  // ---- static backdrop, rendered once
  function backdrop(W, H) {
    const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
    // dusk sky
    const g = x.createLinearGradient(0, 0, 0, WALL_Y);
    g.addColorStop(0, '#1b2140'); g.addColorStop(0.45, '#3a3c63'); g.addColorStop(0.75, '#7a5a6e'); g.addColorStop(0.93, '#c7866a'); g.addColorStop(1, '#d9a070');
    x.fillStyle = g; x.fillRect(0, 0, W, WALL_Y + 4);
    // a few early stars
    const r = rng(7); x.fillStyle = 'rgba(235,230,255,0.7)';
    for (let i = 0; i < 26; i++) { const px = sx(CORNER) + r() * (W - sx(CORNER)), py = 60 + r() * 200; x.beginPath(); x.arc(px, py, 0.6 + r() * 0.9, 0, 7); x.fill(); }
    // the moon, low
    x.fillStyle = 'rgba(244,233,205,0.92)'; x.beginPath(); x.arc(1085, 168, 17, 0, 7); x.fill();
    x.fillStyle = '#3a3c63'; x.globalAlpha = 0.9; x.beginPath(); x.arc(1093, 162, 15, 0, 7); x.fill(); x.globalAlpha = 1;
    // far tree line and fields beyond the porch (hand-placed silhouettes)
    x.fillStyle = '#2a2a3f';
    x.beginPath(); x.moveTo(sx(CORNER) - 10, WALL_Y);
    const r2 = rng(11); let px = sx(CORNER) - 10;
    while (px < W + 20) { const w = 18 + r2() * 40, h = 30 + r2() * 55; x.quadraticCurveTo(px + w * 0.5, WALL_Y - 40 - h, px + w, WALL_Y - 34 - r2() * 20); px += w; }
    x.lineTo(W + 20, WALL_Y); x.closePath(); x.fill();
    x.fillStyle = '#20202f'; x.fillRect(sx(CORNER), WALL_Y - 36, W, 40);
    // one near tree, right, by the steps
    x.strokeStyle = '#18182a'; x.lineWidth = 9; x.beginPath(); x.moveTo(1235, WALL_Y); x.quadraticCurveTo(1225, 380, 1240, 250); x.stroke();
    x.fillStyle = '#1c1c2c'; for (const [cx, cy, rr] of [[1240, 230, 70], [1190, 270, 52], [1275, 290, 58], [1210, 190, 46], [1268, 175, 44]]) { x.beginPath(); x.arc(cx, cy, rr, 0, 7); x.fill(); }
    // the house front
    const wall = x.createLinearGradient(0, 0, sx(CORNER), 0); wall.addColorStop(0, '#3b4459'); wall.addColorStop(1, '#46506a');
    x.fillStyle = wall; x.fillRect(0, 0, sx(CORNER), WALL_Y);
    // clapboards
    for (let y = 70; y < WALL_Y; y += 17) { x.fillStyle = 'rgba(20,24,36,0.35)'; x.fillRect(0, y, sx(CORNER), 2); x.fillStyle = 'rgba(140,150,175,0.07)'; x.fillRect(0, y + 2, sx(CORNER), 3); }
    // corner board and post
    x.fillStyle = '#5b6479'; x.fillRect(sx(CORNER) - 16, 40, 16, WALL_Y - 40); x.strokeStyle = INK; x.lineWidth = 2; x.strokeRect(sx(CORNER) - 16, 40, 16, WALL_Y - 40);
    // window, left of the door
    const wx0 = sx(-1.85), wx1 = sx(-1.30), wy0 = WALL_Y - 330, wy1 = WALL_Y - 150;
    x.fillStyle = '#d7d0bf'; x.fillRect(wx0 - 12, wy0 - 12, wx1 - wx0 + 24, wy1 - wy0 + 26);
    x.fillStyle = '#2b3042'; x.fillRect(wx0, wy0, wx1 - wx0, wy1 - wy0);
    x.strokeStyle = '#d7d0bf'; x.lineWidth = 7; x.beginPath(); x.moveTo((wx0 + wx1) / 2, wy0); x.lineTo((wx0 + wx1) / 2, wy1); x.moveTo(wx0, (wy0 + wy1) / 2); x.lineTo(wx1, (wy0 + wy1) / 2); x.stroke();
    x.strokeStyle = INK; x.lineWidth = 2; x.strokeRect(wx0 - 12, wy0 - 12, wx1 - wx0 + 24, wy1 - wy0 + 26);
    // porch roof beam and ceiling edge
    x.fillStyle = '#23283a'; x.fillRect(0, 0, W, 42); x.fillStyle = '#4b546a'; x.fillRect(0, 36, W, 10); x.strokeStyle = INK; x.lineWidth = 2; x.beginPath(); x.moveTo(0, 46); x.lineTo(W, 46); x.stroke();
    // porch floor (boards run along the house)
    const fy1 = gy(PORCH_DEPTH);
    const fl = x.createLinearGradient(0, WALL_Y, 0, fy1); fl.addColorStop(0, '#4a4039'); fl.addColorStop(1, '#5c4f44');
    x.fillStyle = fl; x.fillRect(0, WALL_Y, sx(PORCH_END) + 6, fy1 - WALL_Y);
    for (let d = 0.11; d < PORCH_DEPTH; d += 0.11) { const y = gy(d); x.fillStyle = 'rgba(18,14,12,0.38)'; x.fillRect(0, y, sx(PORCH_END) + 6, 1.4); }
    const r3 = rng(5);
    for (let d = 0; d < PORCH_DEPTH; d += 0.11) for (let k = 0; k < 4; k++) { const px2 = r3() * sx(PORCH_END); x.fillStyle = 'rgba(18,14,12,0.35)'; x.fillRect(px2, gy(d) + 1, 1.3, 0.11 * K * S - 1); }
    // porch front edge and steps
    x.fillStyle = '#2e2622'; x.fillRect(0, fy1, sx(PORCH_END) + 6, 16); x.fillStyle = '#151110'; x.fillRect(0, fy1 + 16, W, H - fy1);
    for (let k = 0; k < 3; k++) { const y = fy1 + 4 + k * 22, x0 = sx(PORCH_END) + 6 + k * 0; x.fillStyle = k % 2 ? '#3a302a' : '#4a3e36'; x.fillRect(x0, gy(0.3) + k * 34, 90, 34); x.strokeStyle = INK; x.lineWidth = 1.5; x.strokeRect(x0, gy(0.3) + k * 34, 90, 34); }
    // corner and end posts (the end post stands at the porch front)
    x.fillStyle = '#545d72'; x.fillRect(sx(PORCH_END) - 4, 40, 15, gy(PORCH_DEPTH) - 40 - 6); x.strokeStyle = INK; x.lineWidth = 2; x.strokeRect(sx(PORCH_END) - 4, 40, 15, gy(PORCH_DEPTH) - 46);
    return c;
  }

  // ---- the doorway: interior, leaf, frame, sill
  function doorway(x, door, t) {
    const L = sx(-DOOR.half), R = sx(DOOR.half), T = WALL_Y - DOOR.h * S, B = WALL_Y;
    const lit = door.light;
    x.save(); x.beginPath(); x.rect(L, T, R - L, B - T); x.clip();
    // interior: a lit room (back wall, a lamp to the left, the floor going in)
    const iw = x.createLinearGradient(L, 0, R, 0);
    iw.addColorStop(0, `rgb(${lerp(70, 238, lit) | 0},${lerp(50, 176, lit) | 0},${lerp(40, 104, lit) | 0})`);
    iw.addColorStop(1, `rgb(${lerp(50, 205, lit) | 0},${lerp(36, 134, lit) | 0},${lerp(30, 78, lit) | 0})`);
    x.fillStyle = iw; x.fillRect(L, T, R - L, B - T);
    const backY = B - 3.0 * K * S;
    x.fillStyle = `rgba(${lerp(40, 150, lit) | 0},${lerp(28, 92, lit) | 0},${lerp(22, 54, lit) | 0},1)`; x.fillRect(L, backY, R - L, B - backY);
    for (let d = 0.25; d < 3; d += 0.25) { x.fillStyle = 'rgba(60,32,18,0.35)'; x.fillRect(L, B - d * K * S, R - L, 1.2); }
    // lamp glow
    const lg = x.createRadialGradient(L + 30, backY - 120, 4, L + 30, backY - 120, 170);
    lg.addColorStop(0, `rgba(255,236,190,${0.95 * lit})`); lg.addColorStop(1, 'rgba(255,200,130,0)');
    x.fillStyle = lg; x.fillRect(L, T, R - L, B - T);
    x.fillStyle = '#4a2c18'; x.fillRect(L + 4, backY - 46, 64, 46); x.fillStyle = '#5c3a22'; x.fillRect(L + 2, backY - 50, 68, 6);
    x.fillStyle = '#3a2618'; x.fillRect(L + 33, backY - 112, 5, 62); x.beginPath(); x.ellipse(L + 35, backY - 50, 12, 4, 0, 0, 7); x.fill();
    x.fillStyle = `rgba(252,232,178,${0.45 + 0.55 * lit})`; x.beginPath(); x.moveTo(L + 16, backY - 150); x.lineTo(L + 54, backY - 150); x.lineTo(L + 66, backY - 110); x.lineTo(L + 4, backY - 110); x.closePath(); x.fill(); x.strokeStyle = 'rgba(80,50,30,0.7)'; x.lineWidth = 1.5; x.stroke();
    // a picture on the back wall
    x.strokeStyle = 'rgba(70,40,20,0.8)'; x.lineWidth = 3; x.strokeRect(R - 70, backY - 150, 42, 52);
    // the door leaf, hinged on the right jamb, swinging in
    const a = door.angle * Math.PI / 180, w = 2 * DOOR.half;
    const fxu = DOOR.half - w * Math.cos(a), fdy = w * Math.sin(a) * K * S;
    if (Math.cos(a) > 0.02) {
      const XF = sx(fxu);
      x.fillStyle = '#28414a'; x.beginPath(); x.moveTo(R, B); x.lineTo(R, T); x.lineTo(XF, T - fdy); x.lineTo(XF, B - fdy); x.closePath(); x.fill();
      x.strokeStyle = 'rgba(10,20,24,0.8)'; x.lineWidth = 2; x.stroke();
      // panels on the leaf
      const P = (fu, fv) => [lerp(R, XF, fu), lerp(B, T, fv) - fdy * fu];
      x.strokeStyle = 'rgba(90,120,126,0.5)'; x.lineWidth = 2;
      for (const [u0, u1, v0, v1] of [[0.15, 0.85, 0.08, 0.45], [0.15, 0.85, 0.55, 0.92]]) {
        const p = [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]; x.beginPath(); x.moveTo(...p[0]); for (const q of p.slice(1)) x.lineTo(...q); x.closePath(); x.stroke();
      }
      const kn = P(0.9, 0.47); x.fillStyle = '#c8a860'; x.beginPath(); x.arc(kn[0], kn[1], 3.5, 0, 7); x.fill();
    }
    x.restore();
    // frame (casing) and sill
    x.fillStyle = '#cfc7b3'; x.fillRect(L - 16, T - 18, R - L + 32, 18); x.fillRect(L - 16, T, 16, B - T); x.fillRect(R, T, 16, B - T);
    x.strokeStyle = INK; x.lineWidth = 2; x.strokeRect(L - 16, T - 18, R - L + 32, B - T + 18); x.strokeRect(L, T, R - L, B - T);
    x.fillStyle = '#8c7a62'; x.beginPath(); x.moveTo(L - 18, B); x.lineTo(R + 18, B); x.lineTo(R + 22, B + 7); x.lineTo(L - 22, B + 7); x.closePath(); x.fill(); x.stroke();
  }

  // light out of the door onto the porch, and onto the window
  function doorLight(x, door) {
    const lit = door.light; if (lit < 0.01) return;
    const L = sx(-DOOR.half), R = sx(DOOR.half), B = WALL_Y + 7;
    x.save(); x.globalCompositeOperation = 'lighter';
    const g = x.createLinearGradient(0, B, 0, gy(PORCH_DEPTH));
    g.addColorStop(0, `rgba(255,190,110,${0.55 * lit})`); g.addColorStop(0.5, `rgba(240,150,80,${0.22 * lit})`); g.addColorStop(1, 'rgba(200,110,60,0)');
    x.fillStyle = g; x.beginPath(); x.moveTo(L, B); x.lineTo(R, B); x.lineTo(R + 210, gy(PORCH_DEPTH)); x.lineTo(L + 40, gy(PORCH_DEPTH)); x.closePath(); x.fill();
    const g2 = x.createRadialGradient((L + R) / 2, WALL_Y - 150, 20, (L + R) / 2, WALL_Y - 150, 420);
    g2.addColorStop(0, `rgba(255,170,90,${0.10 * lit})`); g2.addColorStop(1, 'rgba(255,170,90,0)');
    x.fillStyle = g2; x.fillRect(0, 40, sx(CORNER), WALL_Y + 200 - 40);
    x.restore();
  }

  // ---- the person (a small drawing set of their own: R profile facing the dog, F front, L walking; standing and sitting)
  const SKIN = '#b48e74', COAT = '#2a3242', COAT2 = '#353e52', TROU = '#1f2430', HAIR = '#1b1714';
  function person(x, P, lit) {
    const X = sx(P.u), Y = gy(P.depth);
    x.save(); x.translate(X, Y); x.scale(S, -S);
    const flip = P.view === 'L' ? -1 : 1;
    const sit = P.sit;
    // skeleton (profile facing +x), standing → sitting
    const hip = [lerp(0, -0.05, sit), lerp(0.92, 0.13, sit)];
    const lean = P.lean * 0.25 + sit * 0.05;
    const sh = [hip[0] + Math.sin(lean) * 0.5, hip[1] + Math.cos(lean) * 0.5];
    const head = [sh[0] + Math.sin(lean) * 0.2 + 0.015, sh[1] + Math.cos(lean) * 0.2];
    const st = P.step || 0, sw = Math.sin(st * Math.PI * 2) * 0.16;
    const kneeA = [lerp(0.03 + sw * 0.5, 0.34, sit), lerp(0.48, 0.40, sit)], kneeB = [lerp(-0.02 - sw * 0.5, 0.30, sit), lerp(0.48, 0.38, sit)];
    const ftA = [lerp(0.02 + sw, 0.56, sit), lerp(0.05, 0.04, sit)], ftB = [lerp(-0.02 - sw, 0.52, sit), lerp(0.05, 0.04, sit)];
    // arm targets
    let hand = [sh[0] + 0.05, sh[1] - 0.48], elb = [sh[0] + 0.04, sh[1] - 0.25];
    if (sit > 0.5) { hand = [0.34, 0.44]; elb = [0.16, 0.42]; }
    const reachH = [sh[0] + 0.55, sh[1] - 0.22], reachE = [sh[0] + 0.28, sh[1] - 0.05];
    hand = [lerp(hand[0], reachH[0], P.reach), lerp(hand[1], reachH[1], P.reach)]; elb = [lerp(elb[0], reachE[0], P.reach), lerp(elb[1], reachE[1], P.reach)];
    const pushH = [0.62, 0.98], pushE = [0.32, 0.86];
    hand = [lerp(hand[0], pushH[0], P.push), lerp(hand[1], pushH[1], P.push)]; elb = [lerp(elb[0], pushE[0], P.push), lerp(elb[1], pushE[1], P.push)];
    const lowH = [0.66, 0.20], lowE = [0.36, 0.38];
    const lo = P.low * (1 - P.push);
    hand = [lerp(hand[0], lowH[0], lo), lerp(hand[1], lowH[1], lo)]; elb = [lerp(elb[0], lowE[0], lo), lerp(elb[1], lowE[1], lo)];
    const F = p => [p[0] * flip, p[1]];
    const stroke = (w) => { x.lineWidth = w || 0.011; x.strokeStyle = INK; x.lineJoin = 'round'; x.lineCap = 'round'; x.stroke(); };
    const limb = (pts, ws, col) => { const t = tube(pts.map(F), ws); x.beginPath(); crClosed(x, [...t.L, ...t.R.slice().reverse()]); x.fillStyle = col; x.fill(); stroke(0.009); };
    const front = P.view === 'F';
    // far leg, far arm
    if (!front) limb([hip, kneeB, ftB], [0.15, 0.11, 0.09], '#171b24');
    // legs (front view: both side by side)
    if (front) { limb([[hip[0] - 0.08, hip[1]], [-0.08, 0.48], [-0.08, 0.05]], [0.14, 0.11, 0.09], TROU); limb([[hip[0] + 0.08, hip[1]], [0.08, 0.48], [0.08, 0.05]], [0.14, 0.11, 0.09], TROU); }
    else limb([hip, kneeA, ftA], [0.16, 0.12, 0.095], TROU);
    // shoes
    const shoe = (p, dx) => { x.beginPath(); x.ellipse(F(p)[0] + dx * flip * 0.06, p[1] - 0.01, 0.10, 0.04, 0, 0, 7); x.fillStyle = '#100d0b'; x.fill(); };
    if (front) { shoe([-0.08, 0.04], 0); shoe([0.08, 0.04], 0); } else { shoe(ftB, 1); shoe(ftA, 1); }
    // coat
    const cw = front ? 0.21 : 0.14;
    const hem = [hip[0], lerp(0.70, 0.10, sit)];
    const coat = front ? [[-cw, sh[1] + 0.02], [cw, sh[1] + 0.02], [cw + 0.03, hip[1]], [cw + 0.05, hem[1]], [-cw - 0.05, hem[1]], [-cw - 0.03, hip[1]]]
      : [[sh[0] - cw, sh[1]], [sh[0] + 0.05, sh[1] + 0.04], [sh[0] + cw, sh[1] - 0.12], [hip[0] + cw + 0.02, hip[1] + 0.05], [hem[0] + cw + 0.05 + sit * 0.08, hem[1] + sit * 0.05], [hip[0] - cw - 0.04, hem[1]], [hip[0] - cw - 0.03, hip[1] + 0.05]];
    x.beginPath(); crClosed(x, coat.map(F)); const cg = x.createLinearGradient(0, sh[1], 0, hem[1]); cg.addColorStop(0, COAT2); cg.addColorStop(1, COAT); x.fillStyle = cg; x.fill(); stroke();
    // head
    x.beginPath(); x.ellipse(F(head)[0], head[1], 0.095, 0.115, 0, 0, 7); x.fillStyle = SKIN; x.fill(); stroke();
    if (!front) { x.beginPath(); x.moveTo(...F([head[0] + 0.09, head[1] + 0.01])); x.lineTo(...F([head[0] + 0.125, head[1] - 0.025])); x.lineTo(...F([head[0] + 0.088, head[1] - 0.035])); x.fillStyle = SKIN; x.fill(); stroke(0.007); }
    x.beginPath(); x.ellipse(F([head[0] - 0.02, 0])[0], head[1] + 0.045, 0.10, 0.08, 0, 0, Math.PI, false); x.fillStyle = HAIR; x.fill();
    x.beginPath(); crClosed(x, [[head[0] - 0.10, head[1] + 0.03], [head[0] - 0.02, head[1] + 0.125], [head[0] + 0.08, head[1] + 0.06], [head[0] - 0.01, head[1] + 0.07], [head[0] - 0.09, head[1] - 0.06]].map(F)); x.fillStyle = HAIR; x.fill();
    // near arm and hand
    if (front) { limb([[sh[0] - cw + 0.02, sh[1] - 0.02], [-cw - 0.02, sh[1] - 0.27], [-cw, sh[1] - 0.50]], [0.10, 0.085, 0.07], COAT2); limb([[cw - 0.02, sh[1] - 0.02], [cw + 0.02, sh[1] - 0.27], [cw, sh[1] - 0.50]], [0.10, 0.085, 0.07], COAT2); }
    else {
      limb([[sh[0], sh[1] - 0.03], elb, hand], [0.105, 0.085, 0.07], COAT2);
      const hp = F(hand); x.beginPath(); x.ellipse(hp[0], hp[1], 0.05, 0.035, (lo > 0.5 ? 0 : -0.6) * flip, 0, 7); x.fillStyle = SKIN; x.fill(); stroke(0.008);
    }
    x.restore();
    // warm light on the person once the door is open
    return { X, Y };
  }

  // ---- subtitles for the spoken lines (the voice is synthesized; the words are given as text)
  const LINES = [[1.0, 2.2, 'Come here.', 1], [3.4, 4.6, 'Come here!', 1], [7.4, 9.3, 'It’s all right.', 0], [10.4, 11.6, 'It’s all right.', 0], [26.4, 27.6, 'Come in.', 0]];
  function subtitle(x, t, W, H) {
    for (const [a, b, s, loud] of LINES) {
      if (t < a || t > b) continue;
      const al = clamp((t - a) / 0.15) * clamp((b - t) / 0.25);
      x.save(); x.globalAlpha = al; x.font = (loud ? '600 30px' : 'italic 400 26px') + ' Literata, Georgia, serif'; x.textAlign = 'center';
      x.fillStyle = 'rgba(0,0,0,0.55)'; x.fillText(s, W / 2 + 1.5, H - 30 + 1.5); x.fillStyle = loud ? '#f2eadb' : '#e8d9be'; x.fillText(s, W / 2, H - 30); x.restore();
    }
  }

  G.WORLD = { S, OX, WALL_Y, K, sx, gy, backdrop, doorway, doorLight, person, subtitle, DOOR, CORNER, PORCH_END };
})(typeof window !== 'undefined' ? window : globalThis);
