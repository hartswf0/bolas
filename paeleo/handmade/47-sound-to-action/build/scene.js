// The stage, the composition and the visible sound (mix editor's picture side). Draws one frame from the exposure
// sheet: dusk porch, the doorway and its light, the person, the dog sprite, the voice made visible at the mouth and at
// the dog's ear, and the small marks of the world's sounds. Also draws an ID pass (flat colours) for measurement.
const SCENE = (() => {
  const DS = 1.2;  // the dog is drawn 1.2x life against the stage: a stylistic exception, so its acting reads
  const W = 1280, H = 720, K = 180, X0 = 360, YF = 505, EL = 16 * Math.PI / 180, CE = Math.cos(EL), SE = Math.sin(EL);
  const P = (X, Y, Z) => [X0 + X * K, YF - Y * K * CE + Z * K * SE];
  const lerp = (a, b, t) => a + (b - a) * t, cl = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  let XS = null, rng = null;
  const STARS = [];
  function setup(xs) {
    XS = xs; let s = 7; rng = () => (s = (s * 16807) % 2147483647) / 2147483647;
    for (let k = 0; k < 40; k++) STARS.push([700 + rng() * 580, rng() * 260, rng()]);
  }
  const buf = document.createElement('canvas'); buf.width = W; buf.height = H; const bx = buf.getContext('2d');

  function sky(ctx, t) {
    const d = cl(t / 32) * 0.18;
    const g = ctx.createLinearGradient(0, 0, 0, 470);
    g.addColorStop(0, `rgb(${24 - 8 * d},${28 - 8 * d},${58 - 12 * d})`); g.addColorStop(0.55, `rgb(${70 - 25 * d},${64 - 20 * d},${98 - 25 * d})`);
    g.addColorStop(0.85, `rgb(${150 - 50 * d},${108 - 35 * d},${118 - 30 * d})`); g.addColorStop(1, `rgb(${196 - 60 * d},${142 - 45 * d},${112 - 30 * d})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, 480);
    for (const [x, y, b] of STARS) { const a = cl((t / 32) * 1.2 + b - 0.6) * 0.8; if (a > 0) { ctx.fillStyle = `rgba(230,230,255,${a})`; ctx.fillRect(x, y, 1.5, 1.5); } }
    // thin moon
    ctx.save(); ctx.translate(1150, 92); ctx.fillStyle = '#efe6c8'; ctx.beginPath();
    ctx.arc(0, 0, 16, -2.2, 2.0, true); ctx.arc(7, -2, 14.2, 1.75, -1.95, false); ctx.closePath(); ctx.fill(); ctx.restore();
    // far tree line
    ctx.fillStyle = '#1a1a2c'; ctx.beginPath(); ctx.moveTo(640, 480);
    for (let x = 640; x <= W; x += 8) { const y = 418 + 14 * Math.sin(x * 0.031) + 9 * Math.sin(x * 0.087 + 1) + 6 * Math.sin(x * 0.21); ctx.lineTo(x, y); }
    ctx.lineTo(W, 480); ctx.fill();
    ctx.fillStyle = '#121220'; ctx.fillRect(640, 466, W - 640, 60);
  }

  function house(ctx, fr) {
    const L = fr.door.light;
    // facade: clapboard
    const fx1 = P(1.75, 0, 0)[0];
    ctx.fillStyle = '#28304a'; ctx.fillRect(0, 0, fx1, YF);
    ctx.strokeStyle = 'rgba(10,12,24,.55)'; ctx.lineWidth = 2;
    for (let y = YF - 6; y > 0; y -= 22) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(fx1, y); ctx.stroke(); }
    ctx.fillStyle = 'rgba(255,255,255,.04)'; for (let y = YF - 6; y > 0; y -= 22) ctx.fillRect(0, y - 20, fx1, 3);
    // corner board and eave shadow
    ctx.fillStyle = '#3a4362'; ctx.fillRect(fx1 - 14, 0, 14, YF);
    const eg = ctx.createLinearGradient(0, 0, 0, 60); eg.addColorStop(0, 'rgba(5,6,14,.85)'); eg.addColorStop(1, 'rgba(5,6,14,0)'); ctx.fillStyle = eg; ctx.fillRect(0, 0, fx1, 60);
    // window (beside the door, above where the person will sit)
    const [wx0, wy1] = P(-1.75, 1.05, 0), [wx1, wy0] = P(-0.95, 1.85, 0);
    ctx.fillStyle = '#16192a'; ctx.fillRect(wx0 - 8, wy0 - 8, wx1 - wx0 + 16, wy1 - wy0 + 16);
    const wg = ctx.createLinearGradient(0, wy0, 0, wy1); wg.addColorStop(0, `rgba(${90 + 150 * L},${70 + 100 * L},${50 + 40 * L},1)`); wg.addColorStop(1, `rgba(${60 + 120 * L},${45 + 70 * L},${35 + 25 * L},1)`);
    ctx.fillStyle = wg; ctx.fillRect(wx0, wy0, wx1 - wx0, wy1 - wy0);
    ctx.fillStyle = '#16192a'; ctx.fillRect((wx0 + wx1) / 2 - 3, wy0, 6, wy1 - wy0); ctx.fillRect(wx0, (wy0 + wy1) / 2 - 3, wx1 - wx0, 6);
    // doorway: interior, door panel, frame
    const [dx0, dy1] = P(-0.46, 0, 0), [dx1, dy0] = P(0.46, 2.05, 0);
    ctx.save(); ctx.beginPath(); ctx.rect(dx0, dy0, dx1 - dx0, dy1 - dy0); ctx.clip();
    const ig = ctx.createRadialGradient(P(0.25, 1.0, -2.5)[0], P(0.25, 1.0, -2.5)[1], 10, P(0.25, 1.0, -2.5)[0], P(0.25, 1.0, -2.5)[1], 330);
    ig.addColorStop(0, `rgb(${70 + 185 * L},${50 + 150 * L},${30 + 90 * L})`); ig.addColorStop(0.5, `rgb(${45 + 130 * L},${32 + 92 * L},${22 + 50 * L})`); ig.addColorStop(1, `rgb(${22 + 60 * L},${18 + 38 * L},${18 + 20 * L})`);
    ctx.fillStyle = ig; ctx.fillRect(dx0, dy0, dx1 - dx0, dy1 - dy0);
    // interior floor boards receding
    const backY = P(0, 0, -3)[1];
    const fg = ctx.createLinearGradient(0, backY, 0, dy1); fg.addColorStop(0, `rgba(${40 + 90 * L},${28 + 60 * L},${20 + 30 * L},1)`); fg.addColorStop(1, `rgba(${60 + 150 * L},${42 + 100 * L},${26 + 50 * L},1)`);
    ctx.fillStyle = fg; ctx.fillRect(dx0, backY, dx1 - dx0, dy1 - backY);
    ctx.strokeStyle = `rgba(20,12,8,${0.35})`; ctx.lineWidth = 1; for (let z = -3; z < 0; z += 0.25) { const y = P(0, 0, z)[1]; ctx.beginPath(); ctx.moveTo(dx0, y); ctx.lineTo(dx1, y); ctx.stroke(); }
    // lamp deep in the room
    const [lx, ly] = P(0.22, 0.95, -2.6);
    ctx.fillStyle = '#20140e'; ctx.fillRect(lx - 2, ly, 4, P(0, 0, -2.6)[1] - ly);
    ctx.fillStyle = `rgb(${120 + 135 * L},${90 + 120 * L},${50 + 60 * L})`; ctx.beginPath(); ctx.moveTo(lx - 26, ly + 4); ctx.lineTo(lx + 26, ly + 4); ctx.lineTo(lx + 15, ly - 30); ctx.lineTo(lx - 15, ly - 30); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#20140e'; ctx.fillRect(lx - 14, P(0, 0, -2.6)[1] - 4, 28, 4);
    // door panel, hinged at the left jamb, swinging in
    const a = fr.door.ang * Math.PI / 180, fX = -0.46 + 0.92 * Math.cos(a), fZ = -0.92 * Math.sin(a);
    const b0 = P(-0.46, 0, 0), b1 = P(fX, 0, fZ), t1 = P(fX, 2.0, fZ), t0 = P(-0.46, 2.0, 0);
    const lit = 0.25 + 0.5 * L * Math.min(1, Math.sin(a) * 1.4);
    ctx.fillStyle = `rgb(${Math.round(70 * lit + 30)},${Math.round(45 * lit + 20)},${Math.round(30 * lit + 16)})`;
    ctx.beginPath(); ctx.moveTo(...b0); ctx.lineTo(...b1); ctx.lineTo(...t1); ctx.lineTo(...t0); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(10,6,4,.7)'; ctx.lineWidth = 2; ctx.stroke();
    // panel mouldings
    for (const [u0, u1, v0, v1] of [[0.15, 0.85, 0.1, 0.45], [0.15, 0.85, 0.55, 0.92]]) {
      const q = (u, v) => { const X = -0.46 + (fX + 0.46) * u, Z = fZ * u; return P(X, 2.0 * v, Z); };
      ctx.beginPath(); ctx.moveTo(...q(u0, v0)); ctx.lineTo(...q(u1, v0)); ctx.lineTo(...q(u1, v1)); ctx.lineTo(...q(u0, v1)); ctx.closePath(); ctx.strokeStyle = 'rgba(10,6,4,.45)'; ctx.stroke();
    }
    const kn = P(-0.46 + (fX + 0.46) * 0.9, 1.0, fZ * 0.9); ctx.fillStyle = '#b89a5a'; ctx.beginPath(); ctx.arc(kn[0], kn[1], 3, 0, 7); ctx.fill();
    ctx.restore();
    // frame trim
    ctx.fillStyle = '#5c5246'; ctx.fillRect(dx0 - 16, dy0 - 16, 16, dy1 - dy0 + 16); ctx.fillRect(dx1, dy0 - 16, 16, dy1 - dy0 + 16); ctx.fillRect(dx0 - 22, dy0 - 22, dx1 - dx0 + 44, 12);
    ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.fillRect(dx0 - 16, dy0 - 16, 4, dy1 - dy0 + 16);
    // warm edge light on the frame when open
    ctx.fillStyle = `rgba(255,190,110,${0.25 * L})`; ctx.fillRect(dx1, dy0, 3, dy1 - dy0); ctx.fillRect(dx0 - 3, dy0, 3, dy1 - dy0);
  }

  function porch(ctx, fr) {
    const L = fr.door.light;
    const [x0, y0] = P(-2.1, 0, 0), [x1, y1] = P(5.0, 0, 1.55);
    // deck
    const dg = ctx.createLinearGradient(0, y0, 0, y1); dg.addColorStop(0, '#2e2a33'); dg.addColorStop(1, '#3c3640');
    ctx.fillStyle = dg; ctx.fillRect(0, y0, x1, y1 - y0);
    ctx.strokeStyle = 'rgba(12,10,16,.6)'; ctx.lineWidth = 1.2;
    for (let z = 0.14; z < 1.55; z += 0.14) { const y = P(0, 0, z)[1]; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(x1, y); ctx.stroke(); }
    // board joints
    for (let k = 0; k < 40; k++) { const z = 0.07 + (k % 10) * 0.14, X = -2 + ((k * 1.37) % 7); const p = P(X, 0, z); ctx.beginPath(); ctx.moveTo(p[0], p[1] - 3); ctx.lineTo(p[0], p[1] + 3); ctx.stroke(); }
    // fascia and the ground below
    ctx.fillStyle = '#221f27'; ctx.fillRect(0, y1, x1, 26); ctx.fillStyle = '#101018'; ctx.fillRect(0, y1 + 26, W, H - y1 - 26);
    // steps at the porch end
    for (let k = 0; k < 3; k++) { const sx = x1 + k * 26, sy = y1 + k * 22; ctx.fillStyle = k % 2 ? '#2b2730' : '#34303a'; ctx.fillRect(sx, y0 + k * 22 + 20, W - sx, sy - y0 - k * 22); }
    // sill (threshold stone)
    const [sx0, sy0] = P(-0.56, 0.04, 0), [sx1, sy1] = P(0.56, 0, 0.12);
    ctx.fillStyle = '#6b6158'; ctx.fillRect(sx0, sy0 - 2, sx1 - sx0, sy1 - sy0 + 4); ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.fillRect(sx0, sy1, sx1 - sx0, 3);
    // light out of the door onto the porch
    if (L > 0.12) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const a = P(-0.46, 0, 0.02), b = P(0.46, 0, 0.02), c = P(1.05, 0, 1.55), d = P(-0.62, 0, 1.55);
      const g = ctx.createLinearGradient(0, a[1], 0, c[1]); g.addColorStop(0, `rgba(170,110,50,${0.55 * L})`); g.addColorStop(1, `rgba(120,70,30,${0.12 * L})`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.lineTo(...c); ctx.lineTo(...d); ctx.closePath(); ctx.fill();
      ctx.restore();
    } else {
      // the ajar door leaks a sliver
      const a = P(0.38, 0, 0.02), b = P(0.46, 0, 0.02), c = P(0.62, 0, 1.4), d = P(0.48, 0, 1.4);
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = 'rgba(120,80,40,.25)'; ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.lineTo(...c); ctx.lineTo(...d); ctx.closePath(); ctx.fill(); ctx.restore();
    }
  }

  function post(ctx) {  // porch roof post at the front corner, in front of everything
    const [px, py] = P(4.72, 0, 1.5);
    ctx.fillStyle = '#1c1a22'; ctx.fillRect(px - 9, 0, 18, py); ctx.fillStyle = 'rgba(255,255,255,.05)'; ctx.fillRect(px - 9, 0, 4, py);
    ctx.fillStyle = '#16141b'; ctx.fillRect(0, 0, W, 12);
  }

  // tint a character drawn into buf: dusk shadow plus warm light from the door
  function tintAndBlit(ctx, warm, dusk, back) {
    bx.globalCompositeOperation = 'source-atop';
    bx.fillStyle = `rgba(22,26,58,${dusk})`; bx.fillRect(0, 0, W, H);
    if (back > 0) { bx.fillStyle = `rgba(20,14,22,${0.45 * back})`; bx.fillRect(0, 0, W, H); }
    if (warm > 0) { bx.fillStyle = `rgba(255,170,80,${0.32 * warm})`; bx.fillRect(0, 0, W, H); }
    bx.globalCompositeOperation = 'source-over';
    if (back > 0) { ctx.save(); ctx.shadowColor = `rgba(255,196,120,${0.9 * back})`; ctx.shadowBlur = 10; ctx.drawImage(buf, 0, 0); ctx.restore(); }
    else ctx.drawImage(buf, 0, 0);
  }

  function dogLight(x, L) { return L * cl(1 - Math.max(0, Math.abs(x - 0.2) - 0.55) / 0.5); }

  function drawPerson(ctx, fr, id) {
    const p = fr.person, [px, py] = P(p.x, 0, p.z);
    const target = id ? ctx : bx;
    if (!id) bx.clearRect(0, 0, W, H);
    target.save(); target.translate(px, py);
    if (p.dir === 0) target.scale(0.42, 1);
    if (p.dir < 0) target.scale(-1, 1);
    target.scale(K, K);
    PERSON.draw(target, p, K, id);
    target.restore();
    if (!id) tintAndBlit(ctx, 0.3 * fr.door.light, 0.36 - 0.06 * fr.door.light);
  }

  function dogScreen(fr) { const d = fr.dog; return P(d.x, 0, d.z); }

  function drawDog(ctx, fr, id) {
    const d = fr.dog, [px, py] = dogScreen(fr);
    if (id) { const s = DOG.sprite(d.key, K * DS, 'id'); ctx.drawImage(s.c, Math.round(px - s.ox), Math.round(py - s.oy)); return; }
    // contact shadow
    ctx.fillStyle = 'rgba(5,5,12,.45)'; ctx.beginPath(); ctx.ellipse(px, py + 2, 84, 10, 0, 0, 7); ctx.fill();
    bx.clearRect(0, 0, W, H);
    const s = DOG.sprite(d.key, K * DS, 'ink'); bx.drawImage(s.c, Math.round(px - s.ox), Math.round(py - s.oy));
    const L = dogLight(d.x, fr.door.light), back = fr.door.light * cl(1 - Math.max(0, d.x - 0.9) / 0.5);
    tintAndBlit(ctx, 0.35 * L, 0.42 - 0.12 * L, back);
  }

  // ---- visible sound
  function level(db) { return cl((db + 42) / 30); }
  function mouthScreen(fr) {
    const p = fr.person, m = PERSON.mouthAt(p); const sc = p.dir === 0 ? 0.42 : p.dir;
    return P(p.x + m[0] * sc, m[1], p.z);
  }
  function earScreen(fr) {
    const d = fr.dog, b = DOG.build(DOG.parse(d.key)), pk = DOG.parse(d.key), ps = pk.yaw * Math.PI / 180;
    const f = [-Math.cos(ps), -Math.sin(ps)], l = [-Math.sin(ps), Math.cos(ps)], q = b.sk.map(v => v * DS);
    return P(d.x + q[0] * f[0] + q[2] * l[0], q[1] + 0.06, d.z + q[0] * f[1] + q[2] * l[1]);
  }
  function voiceMarks(ctx, i) {
    const fr = XS.frames[i];
    const m = mouthScreen(fr), e = earScreen(fr);
    const ang = Math.atan2(e[1] - m[1], e[0] - m[0]);
    for (let j = Math.max(0, i - 9); j <= i; j++) {
      const v = XS.frames[j].voice; if (!v) continue;
      const age = i - j, lv = level(v.db); if (lv <= 0) continue;
      const call = v.style === 'call';
      const a = lv * (1 - age / 10) * (call ? 0.9 : 0.55);
      // at the mouth: arcs opening toward the dog
      ctx.strokeStyle = call ? `rgba(225,235,255,${a})` : `rgba(255,205,140,${a})`;
      ctx.lineWidth = call ? 1.5 + 2.5 * lv : 1.2;
      const r = (call ? 10 : 7) + age * (call ? 9 : 5);
      ctx.beginPath(); ctx.arc(m[0], m[1], r, ang - (call ? 0.5 : 0.35), ang + (call ? 0.5 : 0.35)); ctx.stroke();
      // at the dog's ear: the same sound arriving (heard now; answered LAT later)
      if (age < 6) {
        const r2 = (call ? 34 : 22) - age * (call ? 5 : 3);
        ctx.strokeStyle = call ? `rgba(225,235,255,${a * 0.9})` : `rgba(255,205,140,${a * 0.9})`; ctx.lineWidth = call ? 1 + 1.6 * lv : 1;
        ctx.beginPath(); ctx.arc(e[0], e[1], Math.max(3, r2), ang + Math.PI - 0.6, ang + Math.PI + 0.6); ctx.stroke();
      }
    }
  }
  function words(ctx, i) {
    const t = i / 24, fr = XS.frames[i], m = mouthScreen(fr);
    XS.lines.forEach((L, n) => {
      const nx = XS.lines[n + 1], tEnd = Math.min(L.t1 + 0.9, nx ? nx.t0 - 0.03 : 99);
      if (t < L.t0 - 0.02 || t > tEnd) return;
      const ws = XS.words.filter(w => w.line === L.id);
      const call = L.style === 'call';
      ctx.font = call ? '800 46px "Big Shoulders Display"' : 'italic 400 30px Literata';
      const fade = Math.min(t > L.t1 + 0.3 ? 1 - (t - L.t1 - 0.3) / 0.6 : 1, cl((tEnd - t) / 0.08));
      let x = m[0] + (fr.person.dir < 0 ? -40 : 22), y = m[1] - (call ? 62 : 46);
      if (fr.person.sit > 5) { y = m[1] - 40; x = m[0] + 18; }
      let text = '';
      ws.forEach((w, k) => { if (t >= w.t0 - 0.02) text += (k ? ' ' : '') + display(L.text, k); });
      if (!text) return;
      ctx.fillStyle = call ? `rgba(236,240,255,${0.95 * fade})` : `rgba(255,218,168,${fade})`;
      ctx.shadowColor = 'rgba(0,0,0,.9)'; ctx.shadowBlur = 8; ctx.fillText(text, x, y); ctx.shadowBlur = 0;
    });
  }
  function display(text, k) { // the line's own spelling, word by word
    const parts = text.replace("It's", "It's").split(' ');
    const map = { "It's all right.": ["It's", '', 'all', 'right.'], "It's okay.": ["It's", '', 'okay.'] };
    if (map[text]) return map[text][k] || '';
    return parts[k] || '';
  }
  function foleyMarks(ctx, i) {
    const t = i / 24;
    for (const f of XS.foley) {
      const age = t - f.t0; if (age < 0 || age > 0.25) continue;
      const a = 1 - age / 0.25;
      if (f.kind === 'paw') {
        const fr = XS.frames[i]; const [px, py] = P(f.x, 0, 0.32);
        ctx.strokeStyle = `rgba(220,220,235,${0.35 * a})`; ctx.lineWidth = 1;
        const off = { FL: -38, FR: -30, HL: 34, HR: 42 }[f.leg] * (fr.dog.plan === 'retreat' ? 1 : 1);
        ctx.beginPath(); ctx.moveTo(px + off - 5, py + 12); ctx.lineTo(px + off - 9, py + 16); ctx.moveTo(px + off + 5, py + 12); ctx.lineTo(px + off + 9, py + 16); ctx.stroke();
      } else if (f.kind === 'sniff') {
        const e = earScreen(XS.frames[i]); const d = DOG.parse(XS.frames[i].dog.key);
        const nx = e[0] - 30, ny = e[1] + 18; ctx.strokeStyle = `rgba(220,220,235,${0.6 * a})`; ctx.lineWidth = 1;
        for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.arc(nx - 6 - k * 5 - age * 30, ny, 3 + k, 0, 7); ctx.stroke(); }
      } else if (f.kind === 'thump' || f.kind === 'tailthump') {
        const [px, py] = P(f.x + (f.kind === 'tailthump' ? 0.0 : 0), 0, 0.32);
        ctx.strokeStyle = `rgba(220,220,235,${0.35 * a})`; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.ellipse(px, py + 6, 20 + age * 120, 3 + age * 10, 0, 0, Math.PI, false); ctx.stroke();
      }
    }
    // the creak: a scratchy line at the hinge while the door swings
    const dv = XS.door_creak; if (t >= dv[0] && t <= dv[1]) {
      const [hx, hy] = P(-0.46, 1.2, 0); ctx.strokeStyle = 'rgba(230,220,200,.55)'; ctx.lineWidth = 1;
      for (let k = 0; k < 3; k++) { ctx.beginPath(); const yy = hy - 60 + k * 50 + ((i * 7 + k * 13) % 9); ctx.moveTo(hx - 24, yy); for (let s = 0; s < 6; s++) ctx.lineTo(hx - 24 - s * 7, yy + ((s + i + k) % 2 ? -4 : 4)); ctx.stroke(); }
    }
  }

  function frame(ctx, i) {
    const fr = XS.frames[i], t = i / 24;
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    sky(ctx, t); house(ctx, fr); porch(ctx, fr);
    drawPerson(ctx, fr, false);
    drawDog(ctx, fr, false);
    post(ctx);
    voiceMarks(ctx, i); words(ctx, i); foleyMarks(ctx, i);
    // grain + vignette
    const vg = ctx.createRadialGradient(W / 2, H / 2, 300, W / 2, H / 2, 800); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,.45)');
    ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  }
  function idFrame(ctx, i) {
    const fr = XS.frames[i];
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    drawDog(ctx, fr, true); drawPerson(ctx, fr, true);
  }
  return { setup, frame, idFrame, P, K, W, H, dogScreen };
})();
