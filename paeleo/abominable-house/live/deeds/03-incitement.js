// 03 · Incitement to Suicide — SCION 5 (Yuri Norstein, atmospheric multiplane)
// Built as a stack of glass planes at depths z. Every element (wall, floor, sacks, lamp,
// breath, fog panes, foreground occluders) lives on a plane; screen position, scale, blur
// and veiling all follow from z, the camera track camX(t) and the focus schedule zf(t).
// No method, no act: the doer breathes grey; panes of fog form between the victim and its
// lamp; the victim greys, sinks back through the panes, turns away; the lamp goes out.
(function () {
  const W = 1920, H = 1080;
  // ---------- deterministic hash + colour helpers ----------
  const hs = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const cl = (a, b, x) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  const sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u); };
  const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const mix = (a, b, u) => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
  const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
  const rgb = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a === undefined ? 1 : a})`;
  const lum = c => 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2];
  const greyOf = (c, u) => { const l = lum(c); return mix(c, [l * 0.92, l * 0.93, l * 0.97], u); };

  // ---------- fog plates: pre-built deterministic diffusion textures (glass with breath on it) ----------
  const TEX = {};
  function fogTex(key, seed, col, nb, soft) {
    if (TEX[key]) return TEX[key];
    const c = document.createElement('canvas'); c.width = 512; c.height = 256;
    const x = c.getContext('2d');
    for (let i = 0; i < nb; i++) {
      const px = hs(seed + i * 3.1) * 512, py = 40 + hs(seed + i * 7.7) * 176;
      const r = 30 + hs(seed + i * 1.9) * 90 * soft;
      const gr = x.createRadialGradient(px, py, 0, px, py, r);
      const a = 0.10 + 0.16 * hs(seed + i * 5.3);
      gr.addColorStop(0, rgb(col, a)); gr.addColorStop(1, rgb(col, 0));
      x.fillStyle = gr; x.fillRect(px - r, py - r, r * 2, r * 2);
    }
    // soft vertical falloff so plates have no hard edge
    x.globalCompositeOperation = 'destination-in';
    const v = x.createLinearGradient(0, 0, 0, 256);
    v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(0.25, 'rgba(0,0,0,1)'); v.addColorStop(0.8, 'rgba(0,0,0,1)'); v.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = v; x.fillRect(0, 0, 512, 256);
    const hz = x.createLinearGradient(0, 0, 512, 0);
    hz.addColorStop(0, 'rgba(0,0,0,0)'); hz.addColorStop(0.18, 'rgba(0,0,0,1)'); hz.addColorStop(0.82, 'rgba(0,0,0,1)'); hz.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = hz; x.fillRect(0, 0, 512, 256);
    return (TEX[key] = c);
  }
  function puffTex(key, col) {
    if (TEX[key]) return TEX[key];
    const c = document.createElement('canvas'); c.width = 128; c.height = 128;
    const x = c.getContext('2d');
    for (let i = 0; i < 9; i++) {
      const px = 64 + (hs(i * 9.1 + 4) - 0.5) * 50, py = 64 + (hs(i * 4.3 + 2) - 0.5) * 40, r = 22 + hs(i * 2.2) * 30;
      const gr = x.createRadialGradient(px, py, 0, px, py, r);
      gr.addColorStop(0, rgb(col, 0.32)); gr.addColorStop(1, rgb(col, 0));
      x.fillStyle = gr; x.fillRect(0, 0, 128, 128);
    }
    return (TEX[key] = c);
  }
  function grainTex() {
    if (TEX.grain) return TEX.grain;
    const c = document.createElement('canvas'); c.width = 256; c.height = 256;
    const x = c.getContext('2d'); const d = x.createImageData(256, 256);
    for (let i = 0; i < 256 * 256; i++) { const v = 100 + hs(i * 0.37 + 11) * 56; d.data[i * 4] = d.data[i * 4 + 1] = d.data[i * 4 + 2] = v; d.data[i * 4 + 3] = 255; }
    x.putImageData(d, 0, 0); return (TEX.grain = c);
  }

  // ---------- camera: track, dolly, focus pull ----------
  const cam = t => ({ x: lerp(-50, 70, sm(0.3, 5.6, t)), zoom: lerp(1.0, 1.045, sm(0.3, 5.8, t)) });
  const S0 = 1.2; // stage scale: the sack plane (z=1) is shot slightly close
  const proj = (C, X, z) => ({ x: W / 2 + (X - C.x) * S0 * C.zoom / z, y: 480 + 440 * C.zoom / z, s: S0 * C.zoom / z });
  const blurAt = (z, zf) => Math.min(12, 13 * Math.abs(1 / z - 1 / zf));

  // ---------- sack cutout: outline pins + hinged ear flaps + attribute layers on one glass ----------
  function outline(w, h, bulge, dip, seed, s, pinch) {
    const pw = v => 1 - (pinch || 0) * Math.exp(-Math.pow((v - 0.84) / 0.07, 2)); // carried 'cinched': neck pinched
    const P = [], N = 9;
    for (let i = 0; i <= N; i++) { const u = i / N; P.push([lerp(-0.47 * w, 0.47 * w, u), 2 * s * Math.sin(Math.PI * u)]); }
    for (let i = 1; i <= N; i++) { const v = i / N; P.push([pw(v) * 0.5 * w * (0.94 + bulge * Math.sin(Math.PI * (0.15 + 0.75 * v))) - (v > 0.94 ? 0.04 * w : 0), -h * v]); }
    for (let i = 1; i < N; i++) { const u = 1 - i / N; P.push([lerp(-0.46 * w, 0.46 * w, u), -h + dip * h * Math.sin(Math.PI * u)]); }
    for (let i = N; i >= 1; i--) { const v = i / N; P.push([-pw(v) * 0.5 * w * (0.94 + bulge * Math.sin(Math.PI * (0.15 + 0.75 * v))) + (v > 0.94 ? 0.04 * w : 0), -h * v]); }
    // deckle: a hand-cut paper edge, fixed per sack (never per frame)
    return P.map((p, i) => [p[0] + (hs(seed + i) - 0.5) * 1.6 * s, p[1] + (hs(seed + i * 2.3) - 0.5) * 1.6 * s]);
  }
  const EARS = { R: { L: 0.15, b: 0.20 }, B: { L: 0.11, b: 0.16 }, I: { L: 0.8, b: 0.13 }, O: { L: 0.10, b: 0.34 } };
  // ear angle in degrees (0 = +x, 90 = down). up-out for R,B,O; hanging for I.
  function earAngles(id, P) {
    if (id === 'I') return [103 + 55 * P.lift - 10 * P.droop, 77 - 55 * P.lift + 10 * P.droop];
    return [lerp(-118, -196, P.droop) - 12 * P.lift, lerp(-62, 16, P.droop) + 12 * P.lift];
  }
  function earTips(id, C, P) {
    const w = C.w * P.s * P.wide * P.wf, h = C.h * P.s * P.sq, E = EARS[id];
    const [aL, aR] = earAngles(id, P), L = E.L * C.h * P.s;
    const bl = [-0.44 * w, -h], br = [0.44 * w, -h];
    const tl = [bl[0] + L * Math.cos(aL * Math.PI / 180), bl[1] + L * Math.sin(aL * Math.PI / 180)];
    const tr = [br[0] + L * Math.cos(aR * Math.PI / 180), br[1] + L * Math.sin(aR * Math.PI / 180)];
    const sh = p => [P.x + p[0] - P.lean * p[1], P.y + p[1]];
    return { L: sh(tl), R: sh(tr), top: sh([0, -h]) };
  }
  function flap(g, base, ang, L, bw) {
    const a = ang * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
    const nx = -sa, ny = ca;
    g.beginPath();
    g.moveTo(base[0] - nx * bw / 2, base[1] - ny * bw / 2);
    g.quadraticCurveTo(base[0] + ca * L * 0.6 - nx * bw * 0.35, base[1] + sa * L * 0.6 - ny * bw * 0.35, base[0] + ca * L, base[1] + sa * L);
    g.quadraticCurveTo(base[0] + ca * L * 0.6 + nx * bw * 0.35, base[1] + sa * L * 0.6 + ny * bw * 0.35, base[0] + nx * bw / 2, base[1] + ny * bw / 2);
    g.closePath();
  }
  function strand(g, base, ang, L, bw, side) { // a hanging ear: a limp strand, out from the corner then down
    g.save(); g.translate(base[0], base[1]); g.rotate((ang - 90) * Math.PI / 180);
    const o = side * bw * 0.5;
    g.beginPath(); g.moveTo(-side * bw * 0.4, 0);
    g.quadraticCurveTo(o + side * bw * 0.6, L * 0.1, o + side * bw * 0.3, L * 0.55);
    g.quadraticCurveTo(o + side * bw * 0.4, L * 0.92, o, L);
    g.quadraticCurveTo(o - side * bw * 0.5, L * 0.95, o - side * bw * 0.45, L * 0.6);
    g.quadraticCurveTo(o - side * bw * 0.5, L * 0.25, -side * bw * 0.9, L * 0.12);
    g.closePath(); g.restore();
  }
  function drawSack(g, id, C, P) {
    const s = P.s, wf = P.wf, w = C.w * s * P.wide * wf, h = C.h * s * P.sq;
    const base = hex(C.fill);
    const back = sm(0.45, 0.6, P.turn), front = 1 - back;
    const lit = cl(0, 1.3, P.light);
    const tone = c => greyOf(mul(c, 0.22 + 0.85 * lit), P.grey);
    const toneA = c => greyOf(mul(c, 0.22 + 0.85 * lit), P.grey * 0.6); // attributes keep some hue: identity survives
    const colL = tone(mul(base, P.lampSide > 0 ? 0.62 : 1.0)), colR = tone(mul(base, P.lampSide > 0 ? 1.0 : 0.62));
    g.save();
    g.globalAlpha = P.alpha;
    if (P.blur > 0.4) g.filter = `blur(${P.blur.toFixed(1)}px)`;
    g.translate(P.x, P.y);
    // floor shadow: contact + cast away from lamp
    g.fillStyle = 'rgba(8,8,10,0.55)';
    g.beginPath(); g.ellipse(0, 2 * s, w * 0.58, 9 * s, 0, 0, Math.PI * 2); g.fill();
    if (P.cast > 0.02) {
      g.fillStyle = `rgba(6,6,8,${0.35 * P.cast})`;
      g.beginPath(); g.ellipse(-P.lampSide * w * 0.75, 6 * s, w * 0.9, 13 * s, 0, 0, Math.PI * 2); g.fill();
    }
    g.transform(1, 0, -P.lean, 1, 0, 0);
    const T = P.tags || [], has = k => T.indexOf(k) >= 0;
    const pts = outline(w, h, P.bulge, P.dip, id.charCodeAt(0) * 13.7, s, has('cinched') ? 0.22 : 0);
    const body = () => { g.beginPath(); g.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]); g.closePath(); };
    const grd = g.createLinearGradient(-w / 2, 0, w / 2, 0);
    grd.addColorStop(0, rgb(colL)); grd.addColorStop(0.55, rgb(mix(colL, colR, 0.6))); grd.addColorStop(1, rgb(colR));
    // ear flaps (hinged corner pieces) — behind the wig, in front of nothing
    const E = EARS[id], [aL, aR] = earAngles(id, P), L = E.L * C.h * s, bw = E.b * C.w * s * wf;
    g.fillStyle = grd;
    const ears = () => { flap(g, [-0.44 * w, -h + 2 * s], aL, L, bw); g.fill(); flap(g, [0.44 * w, -h + 2 * s], aR, L, bw); g.fill(); };
    if (id !== 'I') ears();
    body(); g.fillStyle = grd; g.fill();
    g.save(); body(); g.clip();
    // weight sits low: darker belly at the floor, a crease where cloth folds
    const vg = g.createLinearGradient(0, -h, 0, 0);
    vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(0.7, 'rgba(0,0,0,0.05)'); vg.addColorStop(1, 'rgba(10,8,6,0.32)');
    g.fillStyle = vg; g.fillRect(-w, -h - 10, w * 2, h + 12);
    if (id === 'I' || P.sq < 0.85) {
      g.strokeStyle = 'rgba(30,24,18,0.22)'; g.lineWidth = 2 * s;
      g.beginPath(); g.moveTo(-0.4 * w, -h * 0.55); g.quadraticCurveTo(0, -h * 0.45, 0.4 * w, -h * 0.6); g.stroke();
    }
    // attribute layers
    if (id === 'R') {
      g.fillStyle = rgb(toneA(hex('#6e3a33')));
      g.fillRect(-w, -h - 10 * s, w * 2, h * 0.2 + 10 * s);
      g.strokeStyle = rgb(tone(mul(hex('#6e3a33'), 0.7))); g.lineWidth = 1.5 * s;
      g.beginPath(); g.moveTo(-w, -h * 0.8); g.lineTo(w, -h * 0.8); g.stroke();
    }
    if (id === 'B') {
      g.fillStyle = rgb(tone(hex('#2a2622')));
      g.fillRect(-w, -h * 0.435, w * 2, h * 0.07);
      if (front > 0.02) {
        g.globalAlpha = P.alpha * front * 0.6;
        g.strokeStyle = rgb(tone(hex('#5a4630'))); g.lineWidth = 3.2 * s;
        const cy = -h * 0.68, r = 0.17 * C.w * s;
        g.beginPath(); g.arc(0, cy, r, 0, Math.PI * 2); g.stroke();
        g.beginPath(); g.moveTo(0, cy + r * 0.75); g.lineTo(0, cy - r * 0.7); g.stroke();
        for (let k = 0; k < 4; k++) { const yy = cy + r * 0.35 - k * r * 0.3; g.beginPath(); g.ellipse(-r * 0.2, yy, r * 0.17, r * 0.08, -0.6, 0, 6.3); g.stroke(); g.beginPath(); g.ellipse(r * 0.2, yy, r * 0.17, r * 0.08, 0.6, 0, 6.3); g.stroke(); }
        g.globalAlpha = P.alpha;
      }
    }
    // carried damage, cut as further paper pieces on the same glass
    if (has('rope') || has('cinched')) {
      g.strokeStyle = rgb(tone([58, 44, 30])); g.lineWidth = 3.4 * s;
      const ys = has('rope') ? [0.3, 0.64] : [];
      if (has('cinched')) ys.push(0.84);
      ys.forEach((yy, k) => { g.beginPath(); g.moveTo(-w, -h * yy + 3 * s); g.quadraticCurveTo(0, -h * yy + 7 * s, w, -h * yy + 2 * s); g.stroke(); });
    }
    if (has('gag')) { g.fillStyle = rgb(tone([196, 190, 176])); g.fillRect(-w, -h * (id === 'R' ? 0.72 : 0.86), w * 2, h * 0.09); }
    if (has('blot')) {
      g.fillStyle = rgb(tone([22, 22, 30]), 0.85); g.beginPath();
      for (let k = 0; k < 10; k++) { const a = k / 10 * 6.283, r = (0.09 + 0.05 * hs(k + id.charCodeAt(0))) * Math.min(w, h * 1.4); const px = -0.12 * w + Math.cos(a) * r, py = -h * 0.5 + Math.sin(a) * r * 0.8; k ? g.lineTo(px, py) : g.moveTo(px, py); }
      g.closePath(); g.fill();
    }
    if (has('torn')) {
      g.strokeStyle = rgb(tone([30, 24, 18])); g.lineWidth = 2 * s; g.beginPath();
      for (let k = 0; k <= 8; k++) { const px = 0.36 * w + (k % 2 ? 5 : -3) * s, py = -h * (0.25 + 0.05 * k); k ? g.lineTo(px, py) : g.moveTo(px, py); }
      g.stroke(); g.fillStyle = rgb(tone([251, 247, 238]), 0.7); g.fillRect(0.36 * w - 2 * s, -h * 0.4, 3 * s, h * 0.12);
    }
    if (back > 0.02) { // back of the sack: a stitched seam
      g.globalAlpha = P.alpha * back * 0.22; g.fillStyle = '#000'; g.fillRect(-w, -h - 10, w * 2, h + 12);
      g.globalAlpha = P.alpha * back * 0.7;
      g.strokeStyle = 'rgba(30,26,22,0.8)'; g.lineWidth = 1.6 * s; g.setLineDash([5 * s, 4 * s]);
      g.beginPath(); g.moveTo(0, -h * 0.96); g.lineTo(0, -3 * s); g.stroke(); g.setLineDash([]);
      g.globalAlpha = P.alpha;
    }
    // the poured darkness spreading inside, from the ear that listened
    if (P.ink > 0.01) {
      const tx = puffTex('ink', [26, 27, 30]);
      const ex = -0.44 * w * P.inkSide, ey = -h;
      const r = (0.4 + 2.2 * P.ink) * Math.max(w, h);
      g.globalAlpha = P.alpha * Math.min(1, P.ink * 1.6);
      g.drawImage(tx, ex - r, ey - r * 0.6, r * 2, r * 2);
      g.globalAlpha = P.alpha;
    }
    // lamp-side rim light: light through the glass grazing the cut edge
    if (lit > 0.05) {
      const rg = g.createLinearGradient(P.lampSide * w * 0.5, 0, P.lampSide * w * 0.25, 0);
      rg.addColorStop(0, rgb(greyOf([255, 214, 150], P.grey), 0.35 * lit * (1 - P.grey * 0.7))); rg.addColorStop(1, 'rgba(255,214,150,0)');
      g.fillStyle = rg; g.fillRect(-w, -h - 10, w * 2, h + 12);
    }
    g.restore();
    if (id === 'R') { // shawl knot and tail, outside the body edge on her right
      const sc = toneA(hex('#6e3a33')); g.fillStyle = rgb(mul(sc, 0.9));
      g.beginPath(); g.ellipse(0.42 * w, -h * 0.86, 0.06 * w, 0.06 * h, 0, 0, 6.3); g.fill();
      g.beginPath(); g.moveTo(0.4 * w, -h * 0.84); g.quadraticCurveTo(0.56 * w, -h * 0.6, 0.5 * w + 4 * s, -h * 0.42); g.lineTo(0.44 * w, -h * 0.46); g.quadraticCurveTo(0.48 * w, -h * 0.64, 0.36 * w, -h * 0.82); g.closePath(); g.fill();
    }
    if (id === 'I') { // long ears hang outside the body like unwashed hair, a shade darker
      const eg = g.createLinearGradient(-w / 2, 0, w / 2, 0); eg.addColorStop(0, rgb(mul(colL, 0.82))); eg.addColorStop(1, rgb(mul(colR, 0.82)));
      g.fillStyle = eg; g.strokeStyle = 'rgba(20,16,12,0.35)'; g.lineWidth = 1.2 * s;
      strand(g, [-0.46 * w, -h + 3 * s], aL, L, bw, -1); g.fill(); g.stroke();
      strand(g, [0.46 * w, -h + 3 * s], aR, L, bw, 1); g.fill(); g.stroke();
    }
    if (id === 'O') { // wig: cap and long hanks past the shoulders; on the back it covers more
      g.save(); if (has('wig')) { g.translate(0.2 * w, -h); g.rotate(-0.32); g.translate(-0.2 * w, h - 6 * s); } // carried: askew
      const wc = toneA(hex('#7a3b8f')), ww = w / 2 + 5 * s, hank = h * (0.56 + 0.12 * P.droop);
      g.fillStyle = rgb(wc);
      g.beginPath();
      g.moveTo(-ww - 3 * s, -h + hank);
      g.quadraticCurveTo(-ww - 6 * s, -h - 4 * s, -ww * 0.4, -h - 12 * s);
      g.quadraticCurveTo(0, -h - 16 * s, ww * 0.4, -h - 12 * s);
      g.quadraticCurveTo(ww + 6 * s, -h - 4 * s, ww + 3 * s, -h + hank);
      const inner = back > 0.5 ? 0.5 : 0.13;
      g.lineTo(ww - 9 * s, -h + hank - 4 * s);
      g.lineTo(ww - 9 * s, -h + h * inner);
      g.lineTo(-ww + 9 * s, -h + h * inner);
      g.lineTo(-ww + 9 * s, -h + hank - 4 * s);
      g.closePath(); g.fill();
      g.strokeStyle = rgb(mul(wc, 0.7), 0.6); g.lineWidth = 1.2 * s;
      for (let k = -2; k <= 2; k++) { g.beginPath(); g.moveTo(k * ww * 0.3, -h - 10 * s); g.quadraticCurveTo(k * ww * 0.5, -h + 20 * s, k * ww * 0.45, -h + (Math.abs(k) === 2 ? hank - 4 * s : h * inner)); g.stroke(); }
      g.restore();
    }
    if (has('tag')) { // a pinned paper label hanging from the left corner
      g.strokeStyle = rgb(tone([60, 50, 40])); g.lineWidth = 1 * s; g.beginPath(); g.moveTo(-0.4 * w, -h * 0.9); g.lineTo(-0.47 * w, -h * 0.7); g.stroke();
      g.save(); g.translate(-0.47 * w, -h * 0.7); g.rotate(0.15); g.fillStyle = rgb(tone([236, 228, 206])); g.fillRect(-9 * s, 0, 18 * s, 12 * s); g.restore();
    }
    if (has('emptied')) { g.fillStyle = rgb(tone([251, 247, 238]), 0.9); g.beginPath(); g.ellipse(0.55 * w, -2 * s, 0.16 * w, 6 * s, 0, Math.PI, 0); g.fill(); }
    if (has('coins')) { g.fillStyle = rgb(tone([200, 160, 70])); for (let k = 0; k < 3; k++) { g.beginPath(); g.ellipse(-0.3 * w + k * 8 * s, -3 * s - k * 2 * s, 6 * s, 2.6 * s, 0, 0, 6.3); g.fill(); } }
    g.restore();
  }

  // ---------- performances ----------
  const CONTACT = 2.4;
  const rest = (C, id) => ({ wide: 1, sq: 1, wf: 1, lean: 0, bulge: id === 'I' ? 0.1 : 0.05, dip: id === 'I' ? 0.16 : 0.07, droop: 0, lift: 0, turn: 0, grey: 0, ink: 0, inkSide: 1, alpha: 1 });

  function doerPose(A, V, t, CA, CV, Vx0) {
    const P = rest(CA, A);
    const x0 = -470, gapBy = { R: 34, B: 56, I: 170, O: 52 };
    const xT = Vx0 - CV.w / 2 - CA.w / 2 - gapBy[A];
    let prog, x;
    const wsp = sm(1.6, 2.2, t) * (1 - sm(3.6, 4.4, t)); // whisper posture
    if (A === 'R') { // deliberate counted steps, rocking
      const u = cl(0, 1, (t - 0.4) / 1.4) * 4, k = Math.floor(Math.min(u, 3.999)), f = u - k;
      prog = (k + sm(0.15, 0.85, f)) / 4; if (t > 1.8) prog = 1;
      P.lean = 0.07 * Math.sin(t * 2 * Math.PI * 1.15) * (1 - 0.4 * wsp);
      const tall = cl(0, 1, (CV.h - CA.h) / 90);
      P.sq = 1 + 0.12 * tall * wsp; P.wide = 1 - 0.07 * tall * wsp; P.lean += 0.12 * wsp;
      P.lift = 0.2 * wsp;
    } else if (A === 'B') { // lumber: heavy bob, then lean his bulk over the victim
      prog = sm(0.4, 1.9, t);
      const step = Math.abs(Math.sin((t - 0.4) * Math.PI * 1.9)) * (t > 0.4 && t < 1.9 ? 1 : 0);
      P.sq = 1 - 0.035 * step; P.wide = 1 + 0.02 * step;
      const over = cl(0.1, 0.3, (CA.h - CV.h) / 420 + 0.1);
      P.lean = 0.03 * Math.sin(t * 3.0) * (1 - wsp) + over * wsp;
      P.droop = 0.15 * wsp;
    } else if (A === 'I') { // careless: hardly comes over, lolls, breathes rings from afar
      prog = 0.35 * sm(0.4, 1.8, t);
      P.lean = 0.06 * Math.sin(t * 1.7) + 0.04 * wsp; P.sq = 0.97 + 0.03 * Math.sin(t * 1.3);
      P.lift = 0.35 * wsp * (0.6 + 0.4 * Math.sin(t * 5.0));
    } else { // O: precise glide, dead stop, a cold exact bend
      prog = K_eo(0.4, 1.7, t);
      const bend = cl(0.04, 0.42, (CA.h - CV.h) / CA.h * 1.15);
      P.lean = bend * sm(1.6, 2.0, t) * (1 - sm(3.6, 4.0, t)) + 0.02 * (1 - wsp);
      P.sq = 1 + (CV.h > CA.h ? 0.05 * wsp : 0);
    }
    x = lerp(x0, xT, prog);
    // afterwards: withdraws a little, stays in frame left
    x -= (A === 'I' ? 15 : 55) * sm(3.9, 5.1, t);
    if (A === 'R') P.lean = lerp(P.lean, 0.05 * Math.sin(t * 2 * Math.PI * 0.6), sm(4.0, 5.0, t));
    if (A === 'B') { P.droop = lerp(P.droop, 0.4, sm(4.2, 5.2, t)); }
    if (A === 'O') { P.lean = lerp(P.lean, -0.02, sm(4.0, 4.6, t)); }
    return { X: x, z: 0.98, P };
  }
  function K_eo(a, b, x) { const u = cl(0, 1, (x - a) / (b - a)); return 1 - Math.pow(1 - u, 3); }

  const VIC = { // sink window, depth reached, turn window
    R: { s0: 3.3, s1: 5.2, z: 1.5, t0: 3.8, t1: 4.8 },
    B: { s0: 3.7, s1: 5.35, z: 1.42, t0: 4.1, t1: 5.2 },
    I: { s0: 3.0, s1: 4.8, z: 1.6, t0: 3.4, t1: 4.3 },
    O: { s0: 3.4, s1: 5.0, z: 1.52, t0: 3.95, t1: 4.25 }
  };
  function victimPose(V, A, t, CV) {
    const P = rest(CV, V), S = VIC[V];
    const sink = sm(S.s0, S.s1, t), turn = sm(S.t0, S.t1, t);
    P.grey = sm(CONTACT, 4.6, t);
    P.ink = sm(CONTACT, 3.9, t);
    P.turn = turn;
    P.wf = 0.62 + 0.38 * Math.abs(Math.cos(Math.PI * turn));
    let dx = 0;
    if (V === 'R') { // rocking that slows and stops; hunches, ears fold in
      const amp = 0.05 * (1 - sm(2.6, 4.2, t));
      P.lean = amp * Math.sin(t * 2 * Math.PI * 0.9) + 0.06 * turn;
      P.sq = 1 - 0.13 * sm(3.2, 5.0, t); P.wide = 1 + 0.05 * sm(3.2, 5.0, t);
      P.droop = 0.85 * sm(3.0, 4.8, t);
    } else if (V === 'B') { // strength reflex: he swells against it, then sits down heavily
      const swell = sm(2.4, 2.75, t) * (1 - sm(2.9, 3.4, t));
      P.wide = 1 + 0.07 * swell + 0.1 * sm(3.3, 5.0, t); P.sq = 1 + 0.03 * swell - 0.22 * sm(3.3, 5.0, t);
      P.lift = 0.6 * swell; P.droop = 0.9 * sm(3.2, 4.9, t);
      P.lean = -0.05 * swell + 0.05 * turn; P.bulge = 0.05 + 0.08 * sm(3.3, 5.0, t);
    } else if (V === 'I') { // leans in to listen, amused; then folds over, ears to the floor
      const listen = sm(1.9, 2.4, t) * (1 - sm(2.8, 3.3, t));
      P.lean = -0.13 * listen + 0.12 * sm(3.0, 4.2, t);
      P.lift = 0.6 * listen; P.droop = 1.0 * sm(3.0, 4.2, t);
      P.sq = 1 - 0.36 * sm(3.0, 4.4, t); P.wide = 1 + 0.08 * sm(3.0, 4.4, t); P.dip = 0.16 + 0.1 * sm(3.0, 4.4, t);
    } else { // O: at her lamp as at a mirror; a sharp shiver; rigid; bends away; turns sharp
      const shiver = sm(2.4, 2.5, t) * (1 - sm(2.7, 3.0, t));
      dx = 3.5 * Math.sin(t * 95) * shiver;
      P.lean = 0.07 * (1 - sm(2.4, 2.6, t)) + 0.2 * sm(3.4, 4.2, t);
      P.sq = 1 - 0.1 * sm(3.4, 4.6, t); P.droop = 0.6 * sm(3.4, 4.4, t);
    }
    return { dX: dx, sinkX: 60 * sink, z: lerp(1.0, S.z, sink), P, sink };
  }

  // lamp: steady, then guttering, then out (stays out)
  function lampI(t) {
    const fl = 0.08 * Math.sin(t * 23) * Math.sin(t * 7.3) * sm(2.9, 3.4, t);
    const dim = 1 - 0.55 * sm(3.0, 4.4, t) - 0.45 * sm(4.4, 4.9, t);
    return cl(0, 1, dim + fl * dim);
  }

  // ---------- breath (the whisper), per doer ----------
  function bez(p0, p1, p2, u) { const a = 1 - u; return [a * a * p0[0] + 2 * a * u * p1[0] + u * u * p2[0], a * a * p0[1] + 2 * a * u * p1[1] + u * u * p2[1]]; }
  function drawBreath(g, A, t, m, e, s) {
    const dx = e[0] - m[0];
    if (A === 'R') { // counted puffs, small, one per forward rock
      const tx = puffTex('pR', [92, 88, 86]);
      const ctrl = [m[0] + dx * 0.5, Math.min(m[1], e[1]) - 40 * s];
      for (let k = 0; k < 7; k++) {
        const te = 1.8 + k * 0.27, u = (t - te) / 0.6;
        if (u < 0 || u > 1.25) continue;
        const p = bez(m, ctrl, e, Math.min(1, u)), r = (24 + 22 * Math.min(1, u)) * s * (u > 1 ? (1 - (u - 1) * 4) : 1);
        g.globalAlpha = 0.95 * Math.min(1, u * 5) * (u > 1 ? 1 - (u - 1) * 4 : 1);
        g.drawImage(tx, p[0] - r, p[1] - r, r * 2, r * 2);
      }
    } else if (A === 'B') { // heavy dark pour falling from above onto the victim
      const tx = puffTex('pB', [52, 52, 56]);
      const ctrl = [m[0] + dx * 0.7, m[1] - 30 * s];
      const head = sm(1.8, 2.4, t), tail = sm(2.6, 3.8, t);
      for (let k = 0; k < 22; k++) {
        const u = lerp(tail, head, k / 21); if (head - tail < 0.02) break;
        const p = bez(m, ctrl, [e[0] + 10 * s, e[1] + 20 * s], u);
        const r = (40 + 46 * u + 14 * hs(k)) * s;
        g.globalAlpha = 0.32;
        g.drawImage(tx, p[0] - r * 1.2, p[1] - r * 0.7 + u * u * 30 * s, r * 2.4, r * 1.5);
      }
    } else if (A === 'I') { // lazy rings drifting from a distance
      for (let k = 0; k < 5; k++) {
        const te = 1.8 + k * 0.36, u = (t - te) / 0.6;
        if (u < 0 || u > 1.3) continue;
        const uu = Math.min(1, u);
        const ctrl = [m[0] + dx * 0.5, m[1] - (60 + 40 * hs(k)) * s];
        const p = bez(m, ctrl, e, uu);
        const wob = Math.sin(t * 6 + k) * 6 * s;
        const r = (12 + 26 * uu) * s;
        g.globalAlpha = 0.8 * Math.min(1, u * 4) * (u > 1 ? 1 - (u - 1) / 0.3 : 1);
        g.strokeStyle = 'rgba(150,146,142,1)'; g.lineWidth = 5 * s;
        g.filter = 'blur(1.5px)';
        g.beginPath(); g.ellipse(p[0], p[1] + wob, r, r * 0.55, 0.3 * Math.sin(t + k), 0, Math.PI * 2); g.stroke();
        g.filter = 'none';
      }
    } else { // O: one thin exact line, cold, drawn straight to the ear, then running
      const head = K_eo(1.85, 2.4, t), fade = 1 - sm(3.6, 4.1, t);
      if (head <= 0 || fade <= 0) return;
      const q = [lerp(m[0], e[0], head), lerp(m[1], e[1], head)];
      g.globalAlpha = 0.85 * fade;
      g.strokeStyle = 'rgba(160,172,192,1)'; g.lineWidth = 4 * s; g.lineCap = 'round';
      g.beginPath(); g.moveTo(m[0], m[1]); g.lineTo(q[0], q[1]); g.stroke();
      g.setLineDash([10 * s, 14 * s]); g.lineDashOffset = -t * 120 * s;
      g.strokeStyle = 'rgba(225,232,245,1)'; g.lineWidth = 2 * s;
      g.beginPath(); g.moveTo(m[0], m[1]); g.lineTo(q[0], q[1]); g.stroke(); g.setLineDash([]);
      const tx = puffTex('pO', [120, 130, 146]);
      g.globalAlpha = 0.5 * fade;
      for (let k = 0; k < 6; k++) { const u = (k + 0.5) / 6 * head; const r = 26 * s; g.drawImage(tx, lerp(m[0], e[0], u) - r, lerp(m[1], e[1], u) - r, r * 2, r * 2); }
    }
    g.globalAlpha = 1;
  }

  // ---------- the room planes ----------
  function drawWall(g, C, L, moon) {
    const z = 3.0, fl = proj(C, 0, z);
    const warm = [70, 52, 34], cold = [24, 27, 33];
    const wc = mix(cold, warm, 0.75 * L);
    g.fillStyle = rgb(wc); g.fillRect(0, 0, W, fl.y + 2);
    // wainscot rail and panels
    const rail = fl.y - 150 * fl.s;
    g.fillStyle = rgb(mul(wc, 0.8)); g.fillRect(0, rail, W, fl.y - rail);
    g.strokeStyle = rgb(mul(wc, 0.62)); g.lineWidth = 2;
    g.beginPath(); g.moveTo(0, rail); g.lineTo(W, rail); g.stroke();
    for (let X = -1800; X < 2200; X += 260) { const p = proj(C, X, z); g.strokeRect(p.x + 12, rail + 12, 260 * p.s - 24, fl.y - rail - 22); }
    // window (moonlight, cold) and a door
    const wx0 = proj(C, -640, z), wx1 = proj(C, -260, z), wy0 = fl.y - 640 * fl.s, wy1 = fl.y - 260 * fl.s;
    const wg = g.createLinearGradient(0, wy0, 0, wy1);
    wg.addColorStop(0, rgb([70, 82, 100], 1)); wg.addColorStop(1, rgb([40, 48, 60], 1));
    g.fillStyle = wg; g.fillRect(wx0.x, wy0, wx1.x - wx0.x, wy1 - wy0);
    g.fillStyle = rgb(mul(wc, 0.5));
    g.fillRect((wx0.x + wx1.x) / 2 - 3, wy0, 6, wy1 - wy0); g.fillRect(wx0.x, (wy0 + wy1) / 2 - 3, wx1.x - wx0.x, 6);
    g.strokeStyle = rgb(mul(wc, 0.45)); g.lineWidth = 8; g.strokeRect(wx0.x, wy0, wx1.x - wx0.x, wy1 - wy0);
    const d0 = proj(C, 760, z), d1 = proj(C, 1060, z);
    g.fillStyle = rgb(mul(wc, 0.55)); g.fillRect(d0.x, fl.y - 690 * fl.s, d1.x - d0.x, 690 * fl.s);
    g.fillStyle = rgb(mul(wc, 0.42)); g.fillRect(d0.x + 10, fl.y - 680 * fl.s, d1.x - d0.x - 20, 680 * fl.s);
    // moonlight shaft from window falling into the room (cold, lives on)
    const mg = g.createLinearGradient(wx0.x, wy0, wx0.x - 120, fl.y + 200);
    mg.addColorStop(0, `rgba(120,140,170,${0.10 * moon})`); mg.addColorStop(1, 'rgba(120,140,170,0)');
    g.fillStyle = mg; g.beginPath(); g.moveTo(wx0.x, wy0); g.lineTo(wx1.x, wy0); g.lineTo(wx1.x - 60, H); g.lineTo(wx0.x - 360, H); g.closePath(); g.fill();
    return fl.y;
  }
  function drawFloor(g, C, L, wallY, lampX) {
    const fg = g.createLinearGradient(0, wallY, 0, H);
    fg.addColorStop(0, rgb(mix([20, 20, 22], [52, 38, 26], L * 0.8))); fg.addColorStop(1, rgb(mix([12, 12, 13], [36, 26, 18], L * 0.8)));
    g.fillStyle = fg; g.fillRect(0, wallY, W, H - wallY);
    g.strokeStyle = 'rgba(0,0,0,0.25)'; g.lineWidth = 1.5;
    for (let X = -2600; X < 2800; X += 150) { const a = proj(C, X, 3.0), b = proj(C, X, 0.7); g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke(); }
    const p = proj(C, lampX, 1.0);
    if (L > 0.01) {
      const pg = g.createRadialGradient(p.x, p.y, 10, p.x, p.y, 700 * p.s);
      pg.addColorStop(0, `rgba(255,190,110,${0.28 * L})`); pg.addColorStop(1, 'rgba(255,190,110,0)');
      g.save(); g.translate(p.x, p.y); g.scale(1, 0.32); g.translate(-p.x, -p.y);
      g.fillStyle = pg; g.fillRect(p.x - 800, p.y - 800, 1600, 1600); g.restore();
    }
  }
  function drawLamp(g, C, X, z, L, t, blur) {
    const p = proj(C, X, z), s = p.s;
    g.save(); if (blur > 0.4) g.filter = `blur(${blur.toFixed(1)}px)`;
    g.translate(p.x, p.y);
    const wood = mix([30, 24, 20], [92, 64, 40], 0.5 + 0.5 * L);
    g.fillStyle = rgb(wood);
    g.fillRect(-46 * s, -120 * s, 92 * s, 10 * s);             // stool top
    g.fillRect(-40 * s, -112 * s, 7 * s, 112 * s); g.fillRect(33 * s, -112 * s, 7 * s, 112 * s);
    g.fillStyle = rgb(mix([40, 34, 26], [140, 104, 60], L)); // lamp base (brass)
    g.beginPath(); g.ellipse(0, -126 * s, 22 * s, 7 * s, 0, 0, 6.3); g.fill();
    g.fillRect(-12 * s, -150 * s, 24 * s, 24 * s);
    // chimney glass
    g.fillStyle = `rgba(200,200,190,${0.10 + 0.25 * L})`;
    g.beginPath(); g.moveTo(-10 * s, -150 * s); g.quadraticCurveTo(-20 * s, -175 * s, -8 * s, -205 * s); g.lineTo(8 * s, -205 * s); g.quadraticCurveTo(20 * s, -175 * s, 10 * s, -150 * s); g.closePath(); g.fill();
    g.strokeStyle = `rgba(220,220,210,${0.25 + 0.2 * L})`; g.lineWidth = 1.2 * s; g.stroke();
    // flame
    if (L > 0.02) {
      const fh = (10 + 18 * L) * s, sway = Math.sin(t * 11) * 1.5 * s * (1 - L * 0.5);
      g.fillStyle = `rgba(255,220,150,${0.6 + 0.4 * L})`;
      g.beginPath(); g.moveTo(-4 * s * L - 1, -156 * s); g.quadraticCurveTo(-5 * s, -160 * s - fh * 0.6, sway, -156 * s - fh); g.quadraticCurveTo(5 * s, -160 * s - fh * 0.6, 4 * s * L + 1, -156 * s); g.closePath(); g.fill();
    }
    g.restore();
    // smoke after it goes out: one thin thread climbing
    const out = sm(4.85, 5.0, t);
    if (out > 0) {
      g.save(); g.translate(p.x, p.y); g.strokeStyle = `rgba(150,150,150,${0.45 * out * (1 - 0.5 * sm(5.4, 6, t))})`; g.lineWidth = 2 * s;
      g.filter = 'blur(1.5px)';
      g.beginPath(); const rise = (t - 4.85) * 140 * s;
      for (let k = 0; k <= 20; k++) { const v = k / 20, yy = -206 * s - v * (40 * s + rise); const xx = Math.sin(v * 7 + t * 2.2) * 10 * s * v; if (k) g.lineTo(xx, yy); else g.moveTo(xx, yy); }
      g.stroke(); g.restore();
    }
    return { x: p.x, y: p.y - 175 * s, s };
  }
  function drawGlow(g, lp, L) {
    if (L < 0.01) return;
    g.save(); g.globalCompositeOperation = 'lighter';
    const r = 520 * lp.s;
    const gg = g.createRadialGradient(lp.x, lp.y, 0, lp.x, lp.y, r);
    gg.addColorStop(0, `rgba(255,200,120,${0.38 * L})`); gg.addColorStop(0.15, `rgba(200,140,70,${0.18 * L})`); gg.addColorStop(1, 'rgba(120,70,30,0)');
    g.fillStyle = gg; g.fillRect(lp.x - r, lp.y - r, r * 2, r * 2); g.restore();
  }
  // a fog plate at depth z: glass with breath on it, drifting
  function fogPlate(g, C, z, X0, X1, yTop, yBot, a, key, seed, col, drift) {
    if (a < 0.005) return;
    const p0 = proj(C, X0 + drift, z), p1 = proj(C, X1 + drift, z), fl = p0.y;
    const tx = fogTex(key, seed, col, 46, 1.0);
    g.globalAlpha = a;
    g.drawImage(tx, p0.x, fl - yTop * p0.s, p1.x - p0.x, (yTop - yBot) * p0.s);
    g.globalAlpha = 1;
  }
  function drawForeground(g, C, t) {
    // nearest glass: a chair back lower-left, a curtain edge at right; out of focus
    const z = 0.5;
    g.save(); g.filter = 'blur(16px)';
    const bm = proj(C, 0, z); g.fillStyle = 'rgb(9,8,8)';
    g.beginPath(); g.moveTo(-100, -60); g.lineTo(W + 100, -60); g.lineTo(W + 100, 40 + 10 * Math.sin(bm.x * 0.001)); g.lineTo(-100, 70); g.closePath(); g.fill();
    const c = proj(C, -980, z);
    g.fillStyle = 'rgb(8,7,7)';
    g.fillRect(c.x - 40, c.y - 520 * c.s, 34 * c.s, 520 * c.s);
    g.fillRect(c.x - 40, c.y - 520 * c.s, 260 * c.s, 30 * c.s);
    g.fillRect(c.x + 190 * c.s, c.y - 520 * c.s, 34 * c.s, 520 * c.s);
    g.fillRect(c.x - 40, c.y - 300 * c.s, 260 * c.s, 22 * c.s);
    const cu = proj(C, 980, z);
    g.beginPath(); g.moveTo(cu.x, -40); g.quadraticCurveTo(cu.x - 30, 420, cu.x + 40, H + 40); g.lineTo(W + 400, H + 40); g.lineTo(W + 400, -40); g.closePath(); g.fill();
    g.restore();
  }

  // ---------- one scene state, shared by draw, marks and sound ----------
  const R_END = { R: 1.4, B: 1.32, I: 1.48, O: 1.42 }; // depth each victim sinks to (kept legible)
  function applyCarry(P, tags) {
    P.tags = tags || [];
    const has = k => P.tags.indexOf(k) >= 0;
    if (has('greyed')) P.grey = Math.max(P.grey, 0.5);
    if (has('drowsy')) P.droop = Math.min(1, P.droop + 0.35);
    if (has('emptied')) { P.sq *= 0.86; P.dip += 0.06; }
  }
  function state(t, A, V, Kit, carry) {
    const CA = Kit.CAST[A], CV = Kit.CAST[V];
    const C = cam(t), L = lampI(t), Vx0 = 250;
    const d = doerPose(A, V, t, CA, CV, Vx0);
    const v = victimPose(V, A, t, CV);
    v.z = lerp(1.0, R_END[V], v.sink);
    applyCarry(d.P, carry && carry[A]); applyCarry(v.P, carry && carry[V]);
    const lampX = Vx0 + CV.w / 2 + 120, lampZ = 1.0;
    const zf = lerp(1.0, 1.22, sm(3.3, 5.4, t));
    // sinking back: keep its screen place (and drift a little further right) as it recedes
    const vp = proj(C, C.x + (Vx0 + v.dX - C.x) * v.z + v.sinkX * v.z, v.z);
    Object.assign(v.P, { x: vp.x, y: vp.y, s: vp.s, blur: blurAt(v.z, zf), lampSide: 1, light: 0.46 + 0.8 * L * (1 - 0.5 * v.P.grey), cast: L });
    const dp = proj(C, d.X, d.z);
    Object.assign(d.P, { x: dp.x, y: dp.y, s: dp.s, blur: blurAt(d.z, zf), lampSide: 1, light: 0.3 + 0.7 * L * cl(0.25, 1, 1 - (lampX - d.X) / 1400), cast: L * 0.8 });
    return { CA, CV, C, L, Vx0, d, v, lampX, lampZ, zf, dp };
  }
  function box(id, C, P) {
    const w = C.w * P.s * P.wide * P.wf, h = C.h * P.s * P.sq, sh = P.lean * h;
    const ear = id === 'I' ? 0 : (id === 'O' ? 16 : EARS[id].L * C.h) * P.s;
    const side = id === 'I' ? 0.12 * w : id === 'O' ? 8 * P.s : 0;
    const x0 = P.x - w / 2 - side + Math.min(0, sh), x1 = P.x + w / 2 + side + Math.max(0, sh);
    return { x: Math.round(x0), y: Math.round(P.y - h - ear), w: Math.round(x1 - x0), h: Math.round(h + ear) };
  }
  const plates = [[1.07, 2.75], [1.15, 3.15], [1.22, 3.55], [1.29, 3.95], [1.36, 4.35]];

  DEED({
    n: 3, key: 'incitement', title: 'Incitement to Suicide',
    scion: 5, lineage: 'Yuri Norstein — Atmospheric Multiplane Cinema',
    op: 'The doer breathes grey into the victim\'s ear; plates of fog form between the victim and its lamp; the victim greys, sinks back through the plates, turns away, and its lamp goes out.',
    made: 'Every element is a cutout on a glass plane at a set depth: the back wall with a moonlit window, the floor, the two sacks as hand-cut paper with hinged ear flaps and attribute layers, the victim\'s lamp on a stool, and blurred foreground occluders. Fog is pre-built diffusion plates (soft breath on glass) that sit between planes, and grey breath textures that pass from doer to victim.',
    moved: 'A slow camera track and dolly drive parallax across the planes, and a focus pull follows the victim as it recedes; the doer\'s gait, lean and breath style are set per sack, the victim\'s greying, sinking depth and turn per sack. The lamp\'s intensity curve lights the wall, floor, rims and casts shadows, gutters, and goes out, leaving only the cold window.',
    contact: CONTACT,
    leaves: { A: [], V: ['greyed', 'drowsy'] },
    marks(t, A, V, Kit) { const S = state(t, A, V, Kit); return { A: box(A, S.CA, S.d.P), V: box(V, S.CV, S.v.P) }; },
    draw(g, t, A, V, Kit, opt) {
      const layer = opt && opt.layer, carry = opt && opt.carry;
      const S = state(t, A, V, Kit, carry);
      const { CA, CV, C, L, Vx0, d, v, lampX, lampZ, zf, dp } = S;
      const full = !layer, bg = layer === 'bg';
      const lamp = () => { const lp = drawLamp(g, C, lampX, lampZ, L, t, blurAt(lampZ, zf)); drawGlow(g, lp, L);
        const wrap = sm(4.0, 4.8, t) * (1 - 0.6 * sm(5.0, 6.0, t)); // the last breath curls round the flame
        if (wrap > 0) { const tx = puffTex('wrap', [60, 62, 66]); const r = 70 * lp.s * (0.6 + 0.6 * wrap); g.globalAlpha = 0.9 * wrap; g.drawImage(tx, lp.x - r + 18 * Math.sin(t * 2), lp.y - r * 0.8, r * 2, r * 1.6); g.globalAlpha = 1; } };
      const plate = ([z, tp], i) => { const a = 0.14 * sm(tp, tp + 0.55, t), drift = -80 + 80 * sm(tp, tp + 0.9, t) + 6 * Math.sin(t * 0.7 + i);
        fogPlate(g, C, z, Vx0 - CV.w / 2 - 200, Vx0 + CV.w / 2 + 700, 400, -30, a, 'pl' + i, 10 + i * 7, [78, 80, 88], drift); };
      const breath = () => { const m = earTips(A, CA, d.P).R, e = earTips(V, CV, v.P).L;
        drawBreath(g, A, t, A === 'I' ? [m[0] + 8, m[1] + 6] : m, [e[0] + 6, e[1] + 8], dp.s); };
      const nearHaze = () => fogPlate(g, C, 0.8, -1800, 2200, 260, -60, 0.25 + 0.2 * sm(3, 5.5, t), 'near', 77.1, [60, 62, 68], -t * 22);
      const grade = (withGrain) => {
        g.fillStyle = `rgba(4,5,8,${0.1 * (1 - L)})`; g.fillRect(0, 0, W, H);
        const vg = g.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
        vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.5)'); g.fillStyle = vg; g.fillRect(0, 0, W, H);
        if (withGrain) { g.save(); g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.12;
          const gt = grainTex(), off = Math.floor(hs(Math.floor(t * 12)) * 256);
          for (let x = -off; x < W; x += 512) for (let y = -off; y < H; y += 512) g.drawImage(gt, x, y, 512, 512);
          g.restore(); }
      };
      if (full || bg) {
        const wallY = drawWall(g, C, L, 1);
        fogPlate(g, C, 2.6, -2000, 2400, 700, -40, 0.3, 'far', 3.3, [70, 74, 82], t * 14);
        drawFloor(g, C, L, wallY, lampX);
        const items = [];
        if (full) items.push({ z: v.z, f: () => drawSack(g, V, CV, v.P) });
        plates.forEach((pl, i) => items.push({ z: pl[0], f: () => plate(pl, i) }));
        items.push({ z: lampZ - 0.001, f: lamp });
        if (full) { items.push({ z: d.z, f: () => drawSack(g, A, CA, d.P) }); items.push({ z: d.z - 0.01, f: breath }); }
        items.sort((a, b) => b.z - a.z).forEach(it => it.f());
        nearHaze(); drawForeground(g, C, t); grade(true);
        return;
      }
      // sack layers on a clear glass: the sack, then everything nearer than it is laid on with
      // source-atop (veils only its own pixels) or erased (opaque occluders), so bg -> V -> A matches the full frame
      if (layer === 'V') {
        drawSack(g, V, CV, v.P);
        g.save(); g.globalCompositeOperation = 'source-atop';
        plates.forEach((pl, i) => { if (pl[0] < v.z) plate(pl, i); });
        g.restore();
        g.save(); g.globalCompositeOperation = 'destination-out'; drawLamp(g, C, lampX, lampZ, Math.max(L, 0.6), t, blurAt(lampZ, zf)); g.restore();
      } else if (layer === 'A') {
        drawSack(g, A, CA, d.P); breath();
      } else return;
      g.save(); g.globalCompositeOperation = 'source-atop'; nearHaze(); drawForeground(g, C, t); grade(false); g.restore();
    },
    sound(ac, out, t0, A, V, Kit) {
      const master = ac.createGain(); master.gain.value = 1.7; master.connect(out); out = master; // headroom kept: peak ~0.5
      const SN = Kit.SND, say = SN.say, at = t => t0 + t;
      const panAt = (t, who) => { const S = state(t, A, V, Kit); return cl(-1, 1, (who === 'A' ? S.d.P.x : S.v.P.x) / 960 - 1); };
      const depth = t => { const S = state(t, A, V, Kit); return 1 / S.v.z; }; // the victim's sounds recede with it
      // room: a low hush behind the glass, thickening as the fog plates form
      SN.cloud(ac, out, at(0), 6, 30, { bp: 320, q: 0.8, a: 0.018, d: [0.2, 0.5], spread: 0.9 }, u => 0.6 + 0.6 * sm(0.4, 0.75, u));
      // the lamp: a small flame hiss, steady, guttering, gone at 4.9
      SN.cloud(ac, out, at(0), 4.9, 50, { bp: 3400, q: 2, a: 0.012, d: [0.02, 0.06], spread: 0.1 }, u => { const tt = u * 4.9; return lampI(tt) * (0.7 + 0.3 * Math.sin(tt * 23)); });
      const lpan = cl(-1, 1, proj(cam(4.9), 250 + Kit.CAST[V].w / 2 + 120, 1).x / 960 - 1);
      // doer's approach, per sack
      if (A === 'R') for (let k = 0; k < 4; k++) say(ac, out, 'R', at(0.4 + (k + 0.5) * 0.35), 'step', 0.8, panAt(0.4 + (k + 0.5) * 0.35, 'A'));
      if (A === 'B') for (let k = 0; k < 3; k++) say(ac, out, 'B', at(0.4 + (k + 1) * 0.526 - 0.05), 'step', 0.7, panAt(0.9 + k * 0.5, 'A'));
      if (A === 'I') say(ac, out, 'I', at(0.5), 'breathe', 1.2, panAt(1, 'A'));
      if (A === 'O') { say(ac, out, 'O', at(1.7), 'tick', 0.8, panAt(1.7, 'A')); SN.cloud(ac, out, at(0.4), 1.3, 30, { bp: 5200, q: 3, a: 0.01, d: [0.03, 0.08], spread: 0.2 }, u => Math.sin(Math.PI * u)); }
      // the whisper itself: the doer's voice made into breath, timed to the picture's emissions
      const pw = panAt(2.0, 'A') * 0.5 + panAt(2.0, 'V') * 0.5;
      if (A === 'R') for (let k = 0; k < 7; k++) SN.grain(ac, out, at(1.8 + k * 0.27), { bp: 600, q: 1.2, d: 0.22, a: 0.05, pan: pw, att: 0.3 });
      if (A === 'B') SN.cloud(ac, out, at(1.8), 2.0, 40, { bp: 180, q: 0.9, a: 0.05, d: [0.15, 0.35], spread: 0.2 }, u => Math.sin(Math.PI * Math.min(1, u * 1.3)));
      if (A === 'I') for (let k = 0; k < 5; k++) SN.grain(ac, out, at(1.8 + k * 0.36), { bp: 2400, q: 1, d: 0.35, a: 0.035, pan: pw, att: 0.6 });
      if (A === 'O') SN.cloud(ac, out, at(1.85), 1.9, 40, { f: 440 * Math.pow(2, (93 - 69) / 12), noise: 0.85, bp: 5200, q: 4, a: 0.02, d: [0.05, 0.12], spread: 0.15 }, u => Math.min(1, u * 4) * (1 - u));
      say(ac, out, A, at(1.7), 'breathe', 1.6, pw);
      // contact 2.4: the breath arrives — the shot's strongest sound: a low swell plus the victim's own reaction
      const pv = panAt(2.4, 'V');
      SN.thump(ac, out, at(2.4), 0.9, 48, pv);
      SN.cloud(ac, out, at(2.4), 0.8, 60, { bp: 260, q: 0.7, a: 0.07, d: [0.08, 0.25], spread: 0.3 }, u => Math.pow(1 - u, 2));
      say(ac, out, V, at(V === 'I' ? 2.2 : 2.45), 'react', 0.8, pv);
      if (V === 'B') say(ac, out, 'B', at(2.75), 'react', 0.5, pv);
      // each fog plate breathed in: a hush, quieter and darker as the plates go deeper
      plates.forEach(([z, tp], i) => SN.cloud(ac, out, at(tp), 0.7, 30, { bp: 700 - i * 90, q: 0.8, a: 0.03, d: [0.12, 0.3], spread: 0.4 }, u => Math.sin(Math.PI * u)));
      // victim sinks and turns away: its voice going down, filtered by distance
      const S0 = VIC[V];
      say(ac, out, V, at(S0.s0), 'sink', 1.1, panAt(S0.s0, 'V'));
      SN.grain(ac, out, at((S0.t0 + S0.t1) / 2), { bp: 900, q: 1, d: 0.25, a: 0.05 * depth(S0.t1), pan: panAt(S0.t1, 'V'), att: 0.4 });
      say(ac, out, V, at(S0.s1 - 0.1), 'land', 0.35 * depth(S0.s1), panAt(S0.s1, 'V'));
      // lamp out at 4.9: a soft puff and the wick's last tick; then only the room
      SN.cloud(ac, out, at(4.86), 0.3, 50, { bp: 1200, q: 0.8, a: 0.05, d: [0.03, 0.1], spread: 0.1 }, u => 1 - u);
      SN.grain(ac, out, at(4.9), { f: 1800, d: 0.02, a: 0.06, pan: lpan, att: 0.05 });
      if (A === 'R') for (let k = 0; k < 3; k++) say(ac, out, 'R', at(4.1 + k * 0.4), 'tick', 0.35, panAt(4.5, 'A')); // her rocking, resumed
    }
  });
})();
