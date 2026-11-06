// 08 · Rape (implied) — SCION-ALPHA-COMPOSITING (swarm 45, Occlusion Compositing — Who Is In Front?)
// The deed is the part of the composite that is held out. Nothing is drawn or heard behind the curtain
// while it is down; the only evidence is what the matte releases.
//
// LAYER DAG (back to front; every layer reads only from layers below it; no cycles)
//   bg layer  : L0 room (wall, wainscot, floor, corner, doorway, sconce + candle + halo)
//               L6 drop curtain + L7 pelmet          <- the curtain lives in bg (it is set dressing),
//               L8 grade + vignette                     and acts on the sack layers only as a HOLDOUT MATTE
//   V layer   : victim contact shadow, victim RGBA, doer-shadow darkening (source-atop), cold tint,
//               grade; then curtain holdout (destination-out)
//   A layer   : doer's projected wall shadow (minus the victim's alpha), doer contact shadow, doer RGBA,
//               doorway darkening, grade; then jamb holdout + curtain holdout (destination-out)
//   full frame = bg, then V, then A  (draw() composites exactly these three canvases, so layers == full).
// Numeric invariant: for 2.95<=t<=4.75 the curtain matte covers both sacks' full boxes unless a sack's
// left edge is already left of the curtain's pulled edge (the doer slipping out from ~4.0 s).
(function () {
  const W = 1920, H = 1080, FLOOR = 880, CX = 720, CORNER = 1700, TOP = 150;
  const DOOR = { x0: 190, x1: 400, top: 520 };
  const LX = 560, LY = 400;
  const CAM = { s: 1.2, px: 780, py: 940 }; // camera: world -> screen  (x' = px + (x-px)*s)
  const sxw = x => CAM.px + (x - CAM.px) * CAM.s, syw = y => CAM.py + (y - CAM.py) * CAM.s;

  // ---------------- poses (pure function of t; shared by draw, marks and sound)
  function poses(t, A, V, K) {
    const cl = K.cl, lerp = K.lerp, sm = K.sm, eo = K.eo;
    const CA = K.CAST[A], CV = K.CAST[V];
    const fall = cl(0, 1, (t - 2.45) / 0.45);
    let d = fall * fall;
    if (t > 2.9) d = 1 - Math.abs(Math.sin((t - 2.9) * 9)) * Math.exp(-(t - 2.9) * 7) * 0.035;
    const rise = sm(4.8, 5.4, t);
    const hem = lerp(TOP + 70, 1100, d * (1 - rise));
    const pull = sm(3.75, 4.15, t) * (1 - sm(4.5, 4.9, t)) * (CA.w * 0.5 + 40);
    const hidden = t > 3.0;
    const leave = sm(3.55, 5.3, t);

    const vCorner = CORNER - CV.w / 2 - 12;
    const back = sm(0.6, 1.7, t), fear = sm(0.5, 1.6, t);
    const vp = { id: V, x: lerp(1300, vCorner, back), by: FLOOR, sq: 1, lean: 0, jit: 0, slump: V === 'I' ? 0.6 : 0, turned: false, tear: 0, shawlUp: 0, shawlSlip: 0, wigOff: 0, fold: 0, ears: 0, rot: 0 };
    if (!hidden) {
      const tr = Math.sin(t * 47) * 2.2 * fear * sm(1.6, 2.4, t);
      vp.jit = tr;
      if (V === 'R') { vp.sq = 1 - 0.12 * fear; vp.lean = 10 * fear + Math.sin(t * 5) * 6 * (1 - fear * 0.5); vp.shawlUp = fear; }
      if (V === 'B') { vp.sq = 1 - 0.22 * fear; vp.lean = 36 * fear; vp.fold = 12 * fear; }
      if (V === 'I') { vp.sq = 1 - 0.22 * fear; vp.lean = 18 * fear; vp.ears = fear; }
      if (V === 'O') { vp.sq = 1 + 0.05 * fear; vp.lean = 4 * fear; vp.jit = tr * 0.5; }
    } else {
      vp.x = vCorner + 4; vp.turned = true; vp.tear = 1;
      const br = Math.sin(t * 2.2) * 0.006;
      if (V === 'R') { vp.sq = 0.7 + br; vp.lean = 14; vp.rot = 0.1; vp.slump = 1; vp.shawlSlip = 1; vp.fold = 10; }
      if (V === 'B') { vp.sq = 0.74 + br; vp.lean = 18; vp.rot = 0.09; vp.slump = 1; vp.fold = 16; }
      if (V === 'I') { vp.sq = 0.55 + br; vp.lean = 12; vp.rot = 0.12; vp.slump = 1; vp.fold = 12; vp.ears = 2; }
      if (V === 'O') { vp.sq = 0.66 + br; vp.lean = 22; vp.rot = 0.14; vp.slump = 1; vp.fold = 10; vp.wigOff = 1; }
    }

    const dTarget = vCorner - CV.w / 2 - CA.w / 2 - 72;
    const dEnd = DOOR.x0 + CA.w * 0.06 + 4;
    const dp = { id: A, x: 640, by: FLOOR, sq: 1, lean: 0, jit: 0, rot: 0, ears: 0, slump: A === 'I' ? 0.6 : 0 };
    const loom = sm(1.85, 2.5, t) * (1 - sm(3.4, 3.7, t));
    let approach;
    if (A === 'R') {
      const u = sm(0.4, 2.0, t);
      approach = u + Math.sin(u * Math.PI * 6) * 0.018 * (1 - u);
      dp.rot = Math.sin(t * 6.3) * 0.05 * (1 - sm(1.9, 2.2, t)) * sm(0.35, 0.6, t);
      dp.sq = 1 + 0.32 * loom; dp.lean = 30 * loom;
    } else if (A === 'B') {
      approach = eo(0.4, 1.75, t);
      dp.by = FLOOR - Math.abs(Math.sin(t * Math.PI * 2.6)) * 7 * (1 - sm(1.6, 1.8, t)) * sm(0.35, 0.5, t);
      dp.sq = 1 + 0.08 * loom; dp.lean = 70 * loom;
    } else if (A === 'I') {
      const u = sm(0.45, 2.05, t);
      approach = u;
      dp.x += Math.sin(t * 3.1) * 50 * (1 - u) * sm(0.4, 0.8, t);
      dp.sq = 0.84 + 0.46 * loom; dp.lean = 22 * loom + Math.sin(t * 4) * 8 * (1 - loom);
      dp.ears = 0.6 * loom;
    } else {
      const u = cl(0, 1, (t - 0.5) / 1.3);
      approach = u < 0.9 ? u : 0.9 + (1 - Math.pow(1 - (u - 0.9) / 0.1, 2)) * 0.1;
      dp.sq = 1 + 0.12 * loom; dp.lean = (CV.h > CA.h ? 26 : 42) * loom;
    }
    dp.x = lerp(dp.x, dTarget, approach);
    if (t > 3.55) {
      let lx = lerp(dTarget, dEnd, leave);
      if (A === 'R') dp.rot = Math.sin(t * 6.3) * 0.045 * (1 - sm(5.1, 5.3, t));
      if (A === 'B') dp.by = FLOOR - Math.abs(Math.sin(t * Math.PI * 2.6)) * 6 * (1 - sm(5.0, 5.3, t));
      if (A === 'I') { lx += Math.sin(t * 2.7) * 22 * (1 - leave); dp.sq = 0.84; dp.ears = 0; dp.lean = -10; }
      if (A === 'O') dp.lean = -6;
      dp.x = lx;
    }
    // curtain occludes a sack fully when the hem is below the floor and its left edge is right of the curtain edge
    const curtainEdge = CX + pull;
    const occl = p => hem > FLOOR + 10 && (p.x - K.CAST[p.id].w * 0.6) > curtainEdge;
    return { vp, dp, loom, hem, pull, hidden, leave, CA, CV, dVis: !occl(dp), vVis: !occl(vp) };
  }

  // ---------------- carried damage: incoming tags become extra sublayers / pose offsets
  function applyCarry(p, tags) {
    if (!tags) return;
    p.tags = tags;
    if (tags.includes('emptied')) { p.sq *= 0.86; p.slump = Math.max(p.slump || 0, 0.5); }
    if (tags.includes('drowsy')) { p.lean += 8; p.sq *= 0.96; }
    if (tags.includes('torn')) p.tear = Math.max(p.tear || 0, 0.6);
  }

  DEED({
    n: 8, key: 'assault', title: 'Rape',
    scion: 45, lineage: 'Occlusion Compositing — Who Is In Front?',
    op: 'The doer corners the victim, its projected shadow covers the victim, a foreground drop curtain is composited over both, and when the matte lifts the victim is alone and torn while the doer goes out through a doorway.',
    made: 'Each sack is a separate RGBA layer built from a body matte plus attribute sublayers (shawl band, belt and wheat stencil, hanging ears, wig split into a behind-layer and a cap). The room, a projected wall shadow, floor contact shadows, a doorway holdout and a foreground drop curtain are separate layers composited in a fixed back-to-front order.',
    moved: 'Each sack is moved by its own approach curve (Roessler rocks, Belindo stamps, Inigo meanders, Ogiva glides straight) and a loom term that stretches and leans its matte toward the victim while its shadow, scaled about the sconce, grows over the victim. A single curtain value then lowers the foreground matte, holds it while the candle burns down, and raises it on the aftermath pose.',
    contact: 2.9,
    leaves: { A: [], V: ['torn', 'wig'] }, // victim: torn seam (+ flour spilled); 'wig' only means something for Ogiva (wig off)

    marks(t, A, V, K) {
      const P = poses(t, A, V, K);
      const box = p => {
        const C = K.CAST[p.id], h = C.h * p.sq, w = C.w;
        let x0 = p.x - w * 0.56 + Math.min(0, p.lean * 0.4), x1 = p.x + w * 0.56 + Math.max(0, p.lean);
        let y0 = p.by - h - (p.id === 'I' ? 6 : 20), y1 = p.by + 2;
        if (p.id === 'I') { x0 -= 30; x1 += 30; }
        if (p.id === 'O' && !p.wigOff) { x0 -= 16; x1 += 16; y0 -= 14; }
        const X0 = sxw(x0), X1 = sxw(x1), Y0 = syw(y0), Y1 = syw(y1);
        return { x: Math.round(X0), y: Math.round(Y0), w: Math.round(X1 - X0), h: Math.round(Y1 - Y0) };
      };
      return { A: box(P.dp), V: box(P.vp) };
    },

    draw(g, t, A, V, K, opt) {
      opt = opt || {};
      const lerp = K.lerp, sm = K.sm;
      const P = poses(t, A, V, K);
      const { vp, dp, loom, hem, pull, hidden, CA, CV } = P;
      const carry = opt.carry || {};
      applyCarry(vp, carry[V]); applyCarry(dp, carry[A]);
      const coldK = sm(3.0, 4.4, t);

      const S = this._L || (this._L = (() => {
        const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return c; };
        return { bg: mk(), vic: mk(), doer: mk(), shad: mk() };
      })());
      const ctxOf = (c, cam) => {
        const x = c.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.clearRect(0, 0, W, H);
        if (cam) x.setTransform(CAM.s, 0, 0, CAM.s, CAM.px * (1 - CAM.s), CAM.py * (1 - CAM.s));
        return x;
      };
      const gradeCol = `rgb(${Math.round(lerp(255, 215, coldK))},${Math.round(lerp(245, 222, coldK))},${Math.round(lerp(230, 238, coldK))})`;
      const vign = x => { const v = x.createRadialGradient(W / 2, H / 2, 400, W / 2, H / 2, 1200); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.55)'); return v; };
      // grade a transparent sack layer without painting its empty pixels
      const gradeLayer = c => {
        const x = c.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0);
        // (multiply would repaint semi-transparent pixels; a source-atop tint keeps the layer's alpha exact)
        x.globalCompositeOperation = 'source-atop'; x.fillStyle = `rgba(24,30,48,${0.05 + 0.13 * coldK})`; x.fillRect(0, 0, W, H);
        x.fillStyle = vign(x); x.fillRect(0, 0, W, H);
        x.globalCompositeOperation = 'source-over';
      };
      // curtain matte path (world coords)
      const curtainPath = () => {
        const Q = new Path2D();
        const sway = Math.sin(t * 2.1) * 6 * sm(2.9, 3.3, t);
        Q.moveTo(CX, TOP + 60); Q.lineTo(W + 200, TOP + 60); Q.lineTo(W + 200, hem);
        for (let x = W + 160; x >= CX + pull; x -= 60) Q.lineTo(x + sway * 0.5, hem + Math.sin(x * 0.05) * 6);
        if (pull > 1) { Q.lineTo(CX + pull, hem); Q.quadraticCurveTo(CX + pull * 0.15, FLOOR - 200, CX, TOP + 60); }
        else Q.quadraticCurveTo(CX, (TOP + 60 + hem) / 2 + 80, CX, TOP + 60);
        Q.closePath();
        return Q;
      };
      const curtainOn = hem > TOP + 72;

      // ================= bg layer
      const bx = ctxOf(S.bg, true);
      const wax = lerp(64, 22, sm(2.9, 4.6, t));
      const fl = 1 + Math.sin(t * 23) * 0.06 + Math.sin(t * 37) * 0.04;
      const fy = LY + 40 - wax - 12;
      {
        const g2 = bx;
        let wg = g2.createLinearGradient(0, 0, 0, FLOOR); wg.addColorStop(0, '#3a3226'); wg.addColorStop(1, '#6a583e');
        g2.fillStyle = wg; g2.fillRect(-400, -400, W + 800, FLOOR + 400);
        g2.globalAlpha = 0.18; g2.fillStyle = '#6b5a40'; for (let x = -66; x < CORNER; x += 96) g2.fillRect(x, -400, 6, 1060); g2.globalAlpha = 1;
        g2.fillStyle = '#463927'; g2.fillRect(-400, 660, W + 800, FLOOR - 660);
        g2.fillStyle = '#5b4a35'; g2.fillRect(-400, 656, W + 800, 8);
        let fg = g2.createLinearGradient(0, FLOOR, 0, H); fg.addColorStop(0, '#3b2f22'); fg.addColorStop(1, '#17120d');
        g2.fillStyle = fg; g2.fillRect(-400, FLOOR, W + 800, H);
        g2.strokeStyle = 'rgba(0,0,0,.35)'; g2.lineWidth = 2;
        for (let i = 1; i < 6; i++) { const y = FLOOR + i * i * 7; g2.beginPath(); g2.moveTo(-400, y); g2.lineTo(W + 400, y); g2.stroke(); }
        g2.fillStyle = '#1f1b16'; g2.beginPath(); g2.moveTo(CORNER, -400); g2.lineTo(W + 400, -400); g2.lineTo(W + 400, H + 200); g2.lineTo(CORNER, FLOOR); g2.closePath(); g2.fill();
        g2.strokeStyle = '#120f0c'; g2.lineWidth = 3; g2.beginPath(); g2.moveTo(CORNER, -400); g2.lineTo(CORNER, FLOOR); g2.stroke();
        let dg = g2.createLinearGradient(DOOR.x0, 0, DOOR.x1, 0); dg.addColorStop(0, '#050404'); dg.addColorStop(1, '#0e0b09');
        g2.fillStyle = dg; g2.fillRect(DOOR.x0, DOOR.top, DOOR.x1 - DOOR.x0, FLOOR - DOOR.top);
        g2.fillStyle = '#2a1f15';
        g2.fillRect(DOOR.x0 - 22, DOOR.top - 22, 22, FLOOR - DOOR.top + 22);
        g2.fillRect(DOOR.x1, DOOR.top - 22, 22, FLOOR - DOOR.top + 22);
        g2.fillRect(DOOR.x0 - 22, DOOR.top - 22, DOOR.x1 - DOOR.x0 + 44, 22);
        g2.fillStyle = '#7a6142'; g2.fillRect(DOOR.x1 + 18, DOOR.top - 22, 4, FLOOR - DOOR.top + 22); g2.fillRect(DOOR.x0 - 22, DOOR.top - 22, DOOR.x1 - DOOR.x0 + 44, 3);
        g2.fillStyle = '#7a6440'; g2.fillRect(LX - 22, LY + 40, 44, 8); g2.fillRect(LX - 4, LY + 48, 8, 26);
        g2.fillStyle = '#efe6cf'; g2.fillRect(LX - 7, LY + 40 - wax, 14, wax);
        let halo = g2.createRadialGradient(LX, fy, 4, LX, fy, 720 * fl);
        halo.addColorStop(0, 'rgba(255,214,150,.5)'); halo.addColorStop(0.45, 'rgba(255,190,120,.16)'); halo.addColorStop(1, 'rgba(255,190,120,0)');
        g2.globalCompositeOperation = 'lighter'; g2.fillStyle = halo; g2.fillRect(-400, -400, W + 800, H + 800); g2.globalCompositeOperation = 'source-over';
        g2.fillStyle = '#ffe9b0'; g2.beginPath(); g2.ellipse(LX, fy, 5 * fl, 12 * fl, 0, 0, Math.PI * 2); g2.fill();
        // L6 curtain
        if (curtainOn) {
          g2.save(); g2.clip(curtainPath());
          let cgr = g2.createLinearGradient(CX, 0, W + 200, 0);
          for (let i = 0; i <= 26; i++) cgr.addColorStop(i / 26, i % 2 ? '#1f2a37' : '#34475b');
          g2.fillStyle = cgr; g2.fillRect(CX, TOP + 60, W + 200 - CX, H);
          let cl2 = g2.createRadialGradient(LX, fy, 10, LX, fy, 900);
          cl2.addColorStop(0, `rgba(255,200,130,${0.22 * (1 - coldK * 0.6)})`); cl2.addColorStop(1, 'rgba(255,200,130,0)');
          g2.globalCompositeOperation = 'lighter'; g2.fillStyle = cl2; g2.fillRect(CX, 0, W + 200 - CX, H); g2.globalCompositeOperation = 'source-over';
          g2.fillStyle = '#141b24'; g2.fillRect(CX - 10, hem - 26, W + 220 - CX, 26);
          g2.restore();
          if (hem > FLOOR) { g2.fillStyle = 'rgba(0,0,0,.35)'; g2.fillRect(CX + pull, Math.min(hem, H + 10) - 4, W + 200, 6); }
        }
        // L7 pelmet
        g2.fillStyle = '#2b2118'; g2.fillRect(CX - 30, -400, W + 230 - CX, TOP + 470);
        g2.fillStyle = '#4a3a28'; g2.fillRect(CX - 30, TOP + 62, W + 230 - CX, 8);
        if (!curtainOn) { g2.fillStyle = '#26333f'; g2.fillRect(CX - 10, TOP + 44, W + 210 - CX, 22); }
        // L8 grade (screen space)
        g2.setTransform(1, 0, 0, 1, 0, 0);
        g2.globalCompositeOperation = 'multiply'; g2.fillStyle = gradeCol; g2.fillRect(0, 0, W, H);
        g2.globalCompositeOperation = 'source-over'; g2.fillStyle = vign(g2); g2.fillRect(0, 0, W, H);
      }

      // ---------------- sack builder (body matte + sublayers)
      function sackPath(p, C) {
        const w = C.w, h = C.h * p.sq, cx = p.x + p.jit, by = p.by, ln = p.lean, fo = p.fold || 0;
        const Pp = new Path2D();
        const tl = [cx - w * 0.43 + ln, by - h], tr = [cx + w * 0.43 + ln, by - h];
        const earUp = (p.id === 'I') ? 4 : 18 * (1 - (p.turned ? 0.7 : 0));
        Pp.moveTo(cx - w / 2, by);
        Pp.quadraticCurveTo(cx - w * 0.6 + ln * 0.35 + fo, by - h * 0.52, tl[0], tl[1]);
        Pp.lineTo(tl[0] - w * 0.07, tl[1] - earUp);
        Pp.quadraticCurveTo(cx + ln, by - h + 14 + h * 0.3 * (p.slump || 0), tr[0] + w * 0.07, tr[1] - earUp);
        Pp.lineTo(tr[0], tr[1]);
        Pp.quadraticCurveTo(cx + w * 0.6 + ln * 0.35 + fo, by - h * 0.52, cx + w / 2, by);
        Pp.quadraticCurveTo(cx, by + 6, cx - w / 2, by);
        Pp.closePath();
        return { P: Pp, tl, tr, w, h, cx, by, ln };
      }
      function drawSack(x, p) {
        const C = K.CAST[p.id];
        const s = sackPath(p, C);
        const tags = p.tags || [];
        const wigAskew = p.id === 'O' && tags.includes('wig') && !p.wigOff;
        x.save();
        if (p.rot) { x.translate(s.cx, s.by); x.rotate(p.rot); x.translate(-s.cx, -s.by); }
        if (p.id === 'O' && !p.wigOff) {
          x.save(); if (wigAskew) { x.translate(s.cx, s.tl[1]); x.rotate(-0.22); x.translate(-s.cx + 8, -s.tl[1] + 6); }
          x.fillStyle = '#5e2c70';
          const wl = s.h * 0.62;
          x.beginPath();
          x.moveTo(s.tl[0] - 10, s.tl[1] - 10);
          x.quadraticCurveTo(s.tl[0] - 26, s.tl[1] + wl * 0.5, s.tl[0] - 16 + s.ln * -0.2, s.tl[1] + wl);
          x.lineTo(s.tr[0] + 16 + s.ln * -0.2, s.tr[1] + wl);
          x.quadraticCurveTo(s.tr[0] + 26, s.tr[1] + wl * 0.5, s.tr[0] + 10, s.tr[1] - 10);
          x.closePath(); x.fill(); x.restore();
        }
        let cg = x.createLinearGradient(s.cx - s.w / 2, 0, s.cx + s.w / 2, 0);
        cg.addColorStop(0, C.fill); cg.addColorStop(0.55, '#c8b088'); cg.addColorStop(1, '#8f7a58');
        x.fillStyle = cg; x.fill(s.P);
        x.save(); x.clip(s.P);
        x.globalAlpha = 0.09; x.strokeStyle = '#3a2f20'; x.lineWidth = 1;
        for (let yy = s.by - s.h; yy < s.by; yy += 7) { x.beginPath(); x.moveTo(s.cx - s.w, yy); x.lineTo(s.cx + s.w, yy + 3); x.stroke(); }
        x.globalAlpha = 1;
        let tg = x.createLinearGradient(0, s.by - s.h, 0, s.by - s.h + 40);
        tg.addColorStop(0, 'rgba(60,45,28,.45)'); tg.addColorStop(1, 'rgba(60,45,28,0)');
        x.fillStyle = tg; x.fillRect(s.cx - s.w, s.by - s.h - 30, s.w * 2, 80);
        if (p.id === 'R') {
          x.fillStyle = '#6e3a33';
          const band = s.h * 0.2 * (1 + (p.shawlUp || 0) * 0.35);
          if (p.shawlSlip) { x.save(); x.translate(s.cx, s.by - s.h * 0.55); x.rotate(-0.28); x.fillRect(-s.w, -band * 0.5, s.w * 2, band); x.restore(); }
          else x.fillRect(s.cx - s.w, s.by - s.h - 20, s.w * 2, band + 20);
          x.fillStyle = 'rgba(0,0,0,.25)';
          if (!p.shawlSlip) x.fillRect(s.cx - s.w, s.by - s.h + band - 3, s.w * 2, 3);
        }
        if (p.id === 'B') {
          x.fillStyle = '#2a2622';
          const by0 = s.by - s.h * 0.4 + (p.turned ? 10 : 0);
          x.save(); if (p.turned) { x.translate(s.cx, by0); x.rotate(0.08); x.translate(-s.cx, -by0); }
          x.fillRect(s.cx - s.w, by0 - 11, s.w * 2, 22);
          x.fillStyle = '#7a6a48'; x.fillRect(s.cx + s.ln * 0.5 - 12, by0 - 9, 24, 18);
          x.restore();
          if (!p.turned) {
            const wx = s.cx + s.ln * 0.4, wy = s.by - s.h * 0.68;
            x.strokeStyle = 'rgba(80,58,30,.7)'; x.lineWidth = 3;
            x.beginPath(); x.arc(wx, wy, 30, 0, Math.PI * 2); x.stroke();
            x.beginPath(); x.moveTo(wx, wy + 22); x.lineTo(wx, wy - 22); x.stroke();
            for (let k = -2; k <= 2; k++) { const yy = wy - k * 8; x.beginPath(); x.moveTo(wx, yy); x.lineTo(wx - 10, yy - 7); x.moveTo(wx, yy); x.lineTo(wx + 10, yy - 7); x.stroke(); }
          }
        }
        if (p.turned) {
          x.strokeStyle = 'rgba(60,44,26,.55)'; x.lineWidth = 2; x.setLineDash([6, 6]);
          x.beginPath(); x.moveTo(s.cx + s.ln * 0.2 + 6, s.by - 4); x.quadraticCurveTo(s.cx + s.ln * 0.7, s.by - s.h * 0.5, s.cx + s.ln + 6, s.by - s.h + 10); x.stroke();
          x.setLineDash([]);
        }
        // ---- carried tags drawn as matte sublayers clipped to the body
        if (tags.includes('greyed')) { x.fillStyle = 'rgba(120,124,130,.45)'; x.fillRect(s.cx - s.w, s.by - s.h - 40, s.w * 2.4, s.h + 60); }
        if (tags.includes('blot')) { x.fillStyle = 'rgba(20,18,30,.85)'; x.beginPath(); x.ellipse(s.cx - s.w * 0.12 + s.ln * 0.5, s.by - s.h * 0.45, s.w * 0.11, s.w * 0.08, 0.4, 0, Math.PI * 2); x.fill(); x.beginPath(); x.arc(s.cx - s.w * 0.02 + s.ln * 0.5, s.by - s.h * 0.36, 5, 0, Math.PI * 2); x.fill(); }
        if (tags.includes('rope')) { x.strokeStyle = '#6b5432'; x.lineWidth = 7; for (const f of [0.3, 0.62]) { const yy = s.by - s.h * f; x.beginPath(); x.moveTo(s.cx - s.w, yy + 6); x.lineTo(s.cx + s.w, yy - 6); x.stroke(); } }
        if (tags.includes('gag')) { x.fillStyle = '#9a9286'; x.fillRect(s.cx - s.w, s.by - s.h * (p.id === 'R' ? 0.7 : 0.86), s.w * 2, Math.max(10, s.h * 0.08)); }
        x.restore(); // unclip
        if (tags.includes('cinched')) { // a cord pinching the neck
          const yy = s.by - s.h * 0.84; x.strokeStyle = '#4a3a24'; x.lineWidth = 5;
          x.beginPath(); x.moveTo(s.tl[0] - 2, yy); x.quadraticCurveTo(s.cx + s.ln * 0.8, yy + 8, s.tr[0] + 2, yy); x.stroke();
          x.beginPath(); x.moveTo(s.tr[0], yy); x.lineTo(s.tr[0] + 14, yy + 18); x.stroke();
        }
        if (tags.includes('tag')) { const tx = s.tr[0] + 6, ty = s.by - s.h * 0.55; x.strokeStyle = '#3a2f20'; x.lineWidth = 2; x.beginPath(); x.moveTo(tx - 8, ty); x.lineTo(tx + 4, ty + 10); x.stroke(); x.fillStyle = '#efe7d2'; x.fillRect(tx, ty + 8, 26, 18); x.strokeRect(tx, ty + 8, 26, 18); }
        if (tags.includes('coins')) { x.fillStyle = '#c9a23a'; x.strokeStyle = '#7a5f1c'; x.lineWidth = 1.5; for (let k = 0; k < 4; k++) { x.beginPath(); x.ellipse(s.cx + s.w / 2 + 14, s.by - 3 - k * 5, 11, 4, 0, 0, Math.PI * 2); x.fill(); x.stroke(); } }
        if (p.id === 'O' && !p.wigOff) {
          x.save(); if (wigAskew) { x.translate(s.cx, s.tl[1]); x.rotate(-0.22); x.translate(-s.cx + 8, -s.tl[1] + 6); }
          x.fillStyle = '#7a3b8f';
          x.beginPath();
          x.moveTo(s.tl[0] - 12, s.tl[1] + 30);
          x.quadraticCurveTo(s.cx + s.ln, s.tl[1] - 34, s.tr[0] + 12, s.tr[1] + 30);
          x.quadraticCurveTo(s.cx + s.ln, s.tl[1] + 12, s.tl[0] - 12, s.tl[1] + 30);
          x.fill();
          x.fillRect(s.tl[0] - 14, s.tl[1] + 6, 10, s.h * 0.55);
          x.fillRect(s.tr[0] + 4, s.tr[1] + 6, 10, s.h * 0.55);
          x.restore();
        }
        if (p.id === 'I') {
          const e = (p.ears || 0) + (tags.includes('drowsy') ? 0 : 0);
          x.fillStyle = '#bfa277'; x.strokeStyle = 'rgba(50,36,20,.75)'; x.lineWidth = 2.5;
          for (const sd of [-1, 1]) {
            const ex = (sd < 0 ? s.tl[0] : s.tr[0]) + sd * 4, ey = s.tl[1] - 2;
            const sw = Math.sin(t * 4.2 + sd) * 7 * (1 - Math.min(1, e));
            let tipx, tipy;
            if (e > 1.5) { tipx = ex + sd * 78; tipy = s.by - 4; }
            else { tipx = ex + sd * (26 - 50 * e) + sw; tipy = ey + s.h * (0.96 - 0.3 * e); }
            const nx = sd * 17;
            x.beginPath();
            x.moveTo(ex - nx, ey);
            x.bezierCurveTo(ex + nx * 1.6, ey + 10, tipx + nx * 0.8, tipy - 30, tipx + nx * 0.5, tipy);
            x.quadraticCurveTo(tipx - nx * 0.2, tipy + 8, tipx - nx * 0.9, tipy - 2);
            x.bezierCurveTo(tipx - nx * 0.6, tipy - 30, ex, ey + 30, ex - nx * 1.6, ey + 14);
            x.closePath(); x.fill(); x.stroke();
          }
        }
        if (p.tear) {
          const big = p.tear >= 1;
          const sx = s.cx - s.w / 2 + 6 + (p.fold || 0) * 0.5, y0 = s.by - s.h * (big ? 0.62 : 0.5), y1 = s.by - s.h * 0.2;
          x.strokeStyle = '#2a1f14'; x.lineWidth = 3; x.beginPath(); x.moveTo(sx + 4, y0);
          for (let i = 1; i <= 8; i++) x.lineTo(sx + (i % 2 ? -3 : 9), y0 + (y1 - y0) * i / 8);
          x.stroke();
          x.fillStyle = '#fbf7ee';
          x.beginPath(); x.moveTo(sx + 2, y0 + 12); x.lineTo(sx - 8, y1); x.lineTo(sx + 6, y1 - 6); x.closePath(); x.fill();
          if (big) {
            x.globalAlpha = 0.9;
            x.beginPath(); x.ellipse(sx - 26, s.by + 2, 46, 9, 0, 0, Math.PI * 2); x.fill();
            for (let i = 0; i < 14; i++) { const hx = K.hash(i + 31), hy = K.hash(i + 77); x.fillRect(sx - 70 + hx * 80, s.by - 2 + hy * 10, 3, 2); }
            x.globalAlpha = 1;
          }
        }
        if (p.id === 'O' && p.wigOff) {
          x.fillStyle = '#7a3b8f';
          const wx = s.cx - s.w / 2 - 110, wy = s.by;
          x.beginPath(); x.moveTo(wx - 50, wy + 4); x.quadraticCurveTo(wx - 30, wy - 30, wx + 10, wy - 26); x.quadraticCurveTo(wx + 50, wy - 18, wx + 56, wy + 4); x.closePath(); x.fill();
          x.fillStyle = '#5e2c70'; x.fillRect(wx - 40, wy - 6, 90, 10);
        }
        x.restore();
        return s;
      }
      const contact = (x, p, C, a) => {
        const w = C.w * (1 + (p.fold || 0) / 80);
        let r = x.createRadialGradient(p.x, p.by + 4, 4, p.x, p.by + 4, w * 0.7);
        r.addColorStop(0, `rgba(0,0,0,${a})`); r.addColorStop(1, 'rgba(0,0,0,0)');
        x.fillStyle = r; x.save(); x.translate(0, p.by + 4); x.scale(1, 0.16); x.translate(0, -(p.by + 4));
        x.beginPath(); x.arc(p.x, p.by + 4, w * 0.7, 0, Math.PI * 2); x.fill(); x.restore();
      };
      const holdCurtain = x => { if (!curtainOn) return; x.save(); x.globalCompositeOperation = 'destination-out'; x.fillStyle = '#000'; x.fill(curtainPath()); x.fillRect(CX - 30, -400, W + 230 - CX, TOP + 470); x.restore(); };

      // shadow pass (doer silhouette scaled about the sconce)
      const shx = ctxOf(S.shad, true);
      const shadA = (0.02 + 0.67 * loom) * (1 - sm(3.0, 3.3, t));
      if (shadA > 0.01) {
        shx.save();
        shx.beginPath(); shx.rect(CX - 300, -400, CORNER - CX + 300, FLOOR + 400); shx.clip();
        shx.translate(LX, FLOOR - 30); shx.scale(lerp(1.06, Math.max(1.06, (vp.x - LX) / (dp.x - LX)), loom * 0.85), lerp(1.1, Math.max(2.0, 1.7 * CV.h / CA.h), loom)); shx.translate(-LX, -(FLOOR - 30));
        const ps = Object.assign({}, dp); ps.by = dp.by - 30; ps.lean = dp.lean * 1.4;
        shx.fillStyle = '#000'; shx.fill(sackPath(ps, CA).P);
        shx.restore();
      }

      // ================= V layer
      const vx = ctxOf(S.vic, true);
      contact(vx, vp, CV, 0.6);
      drawSack(vx, vp);
      vx.setTransform(1, 0, 0, 1, 0, 0);
      if (shadA > 0.01) { vx.save(); vx.globalCompositeOperation = 'source-atop'; vx.globalAlpha = shadA * 0.9; vx.drawImage(S.shad, 0, 0); vx.restore(); }
      if (hidden) { vx.save(); vx.globalCompositeOperation = 'source-atop'; vx.fillStyle = 'rgba(30,40,60,.18)'; vx.fillRect(0, 0, W, H); vx.restore(); }
      gradeLayer(S.vic);
      vx.setTransform(CAM.s, 0, 0, CAM.s, CAM.px * (1 - CAM.s), CAM.py * (1 - CAM.s)); holdCurtain(vx);

      // ================= A layer
      const dx = ctxOf(S.doer, false);
      if (shadA > 0.01) {
        dx.globalAlpha = shadA; dx.drawImage(S.shad, 0, 0); dx.globalAlpha = 1;
        dx.globalCompositeOperation = 'destination-out'; dx.drawImage(S.vic, 0, 0); dx.globalCompositeOperation = 'source-over';
      }
      dx.setTransform(CAM.s, 0, 0, CAM.s, CAM.px * (1 - CAM.s), CAM.py * (1 - CAM.s));
      contact(dx, dp, CA, 0.6);
      drawSack(dx, dp);
      const inDoor = sm(DOOR.x1 + 40, DOOR.x0 + 60, dp.x);
      if (inDoor > 0) {
        dx.save(); dx.globalCompositeOperation = 'source-atop';
        let dd = dx.createLinearGradient(DOOR.x0, 0, DOOR.x1 + 120, 0);
        dd.addColorStop(0, `rgba(5,4,3,${0.45 * inDoor})`); dd.addColorStop(1, 'rgba(5,4,3,0)');
        dx.fillStyle = dd; dx.fillRect(-400, -400, W + 800, H + 800); dx.restore();
      }
      gradeLayer(S.doer);
      dx.setTransform(CAM.s, 0, 0, CAM.s, CAM.px * (1 - CAM.s), CAM.py * (1 - CAM.s));
      // jamb holdout: the wall left of the doorway is in front of anything inside the door
      dx.save(); dx.globalCompositeOperation = 'destination-out'; dx.fillStyle = '#000'; dx.fillRect(-400, DOOR.top - 22, DOOR.x0 + 400, FLOOR - DOOR.top + 22); dx.restore();
      holdCurtain(dx);

      // ================= output
      g.setTransform(1, 0, 0, 1, 0, 0);
      if (!opt.layer) { g.drawImage(S.bg, 0, 0); g.drawImage(S.vic, 0, 0); g.drawImage(S.doer, 0, 0); }
      else if (opt.layer === 'bg') g.drawImage(S.bg, 0, 0);
      else if (opt.layer === 'V') g.drawImage(S.vic, 0, 0);
      else if (opt.layer === 'A') g.drawImage(S.doer, 0, 0);
    },

    // ---------------- sound: grains only. While the curtain is down only time passes.
    sound(ac, out, t0, A, V, K) {
      const SND = K.SND, H2 = K.hash, sm = K.sm;
      const pan = x => Math.max(-1, Math.min(1, sxw(x) / 960 - 1));
      const at = t => t0 + t;
      // sample poses at 100 Hz once
      const N = 600, T = [];
      for (let i = 0; i <= N; i++) T.push(poses(i / 100, A, V, K));
      const vis = (i, who) => who === 'A' ? T[i].dVis : T[i].vVis;
      const sackOK = (i, who) => i / 100 < 2.9 ? true : vis(i, who) && (i / 100 > 3.0);
      // --- time bed: candle (whole shot), clock (whole shot, louder in the hold), rain (the hold)
      SND.cloud(ac, out, at(0), 6, 26, { bp: 3200, q: 2, a: 0.018, d: [0.004, 0.012], spread: 0.1 }, u => 1); // candle
      for (let k = 0; k * 0.5 < 6; k++) {
        const t = 0.25 + k * 0.5, hold = sm(2.95, 3.2, t) * (1 - sm(4.6, 5.0, t));
        SND.grain(ac, out, at(t), { f: k % 2 ? 1900 : 1700, d: 0.018, a: 0.035 + 0.06 * hold, pan: 0.55, att: 0.05, noise: 0.4, bp: 2500 });
      }
      SND.cloud(ac, out, at(2.95), 2.0, 260, { bp: 4200, q: 0.8, a: 0.03, d: [0.003, 0.01], spread: 0.9 }, u => Math.sin(Math.PI * u)); // rain
      // --- doer footfalls, gated by visibility
      let acc = 0, last = -1;
      const stride = { R: 22, B: 0, I: 30, O: 40 }[A];
      for (let i = 1; i <= N; i++) {
        const dxv = Math.abs(T[i].dp.x - T[i - 1].dp.x);
        if (A === 'B') { // stamps land at the bob's zero crossings
          const tt = i / 100, ph = Math.floor(tt * 2.6), ph0 = Math.floor((tt - 0.01) * 2.6);
          if (ph !== ph0 && dxv > 0.4 && sackOK(i, 'A')) SND.say(ac, out, 'B', at(tt), 'step', 0.8, pan(T[i].dp.x));
          continue;
        }
        acc += dxv;
        let st = stride; if (A === 'I') st = 24 + H2(i * 0.37) * 22;
        if (acc >= st) {
          acc = 0;
          if (sackOK(i, 'A') && i - last > 8) { SND.say(ac, out, A, at(i / 100), 'step', A === 'O' ? 0.9 : 0.8, pan(T[i].dp.x)); last = i; }
        }
      }
      // --- victim: backs away, fear breathing
      let vacc = 0;
      const vStride = { R: 26, B: 70, I: 30, O: 40 }[V];
      for (let i = 1; i < 290; i++) { vacc += Math.abs(T[i].vp.x - T[i - 1].vp.x); if (vacc > vStride) { vacc = 0; SND.say(ac, out, V, at(i / 100), 'step', 0.5, pan(T[i].vp.x)); } }
      SND.say(ac, out, V, at(0.55), 'react', 0.7, pan(T[55].vp.x));
      SND.say(ac, out, V, at(1.65), 'breathe', 0.7, pan(T[165].vp.x));
      // --- loom: the shadow matte spreading, a low swell of grains; doer's breath
      SND.cloud(ac, out, at(1.85), 0.65, 90, { f: 70, glide: 0.2, noise: 0.6, bp: 220, a: 0.05, d: [0.06, 0.16], spread: 0.3 }, u => u * u);
      SND.say(ac, out, A, at(1.95), 'breathe', 0.5, pan(T[195].dp.x));
      // --- curtain falls: cloth hush (grains rising), then the hem lands = contact (strongest)
      SND.cloud(ac, out, at(2.45), 0.45, 220, { bp: 900, q: 0.7, a: 0.06, d: [0.01, 0.04], spread: 0.6 }, u => u * u);
      SND.thump(ac, out, at(2.9), 2.4, 52, 0.35);
      SND.cloud(ac, out, at(2.9), 0.35, 120, { bp: 500, q: 0.8, a: 0.07, d: [0.01, 0.05], spread: 0.7 }, u => Math.pow(1 - u, 2));
      // --- doer slips out: curtain-edge rustle at the frame the edge lifts
      SND.cloud(ac, out, at(3.8), 0.4, 80, { bp: 1400, a: 0.03, d: [0.01, 0.04], spread: 0.2 }, u => Math.sin(Math.PI * u));
      // --- doorway: the jamb takes the doer, a dry wood tick
      SND.grain(ac, out, at(5.3), { f: 330, d: 0.05, a: 0.08, noise: 0.6, bp: 700, pan: pan(DOOR.x0), att: 0.1 });
      // --- curtain rises: softer hush, then the victim heard only once visible
      SND.cloud(ac, out, at(4.8), 0.6, 120, { bp: 1100, q: 0.7, a: 0.03, d: [0.01, 0.04], spread: 0.6 }, u => Math.sin(Math.PI * u));
      SND.say(ac, out, V, at(5.25), 'sink', 0.6, pan(T[525].vp.x));
      SND.say(ac, out, V, at(5.5), 'breathe', 0.4, pan(T[550].vp.x));
    }
  });
})();
