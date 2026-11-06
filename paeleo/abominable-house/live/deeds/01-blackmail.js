// 01 · BLACKMAIL — SCION-2 · Lotte Reiniger lineage: articulated shadow theater.
// Every sack is a black cut-card puppet of pinned pieces (lower body, upper body hinged at a
// waist pin, two ears hinged at the top-corner pins, Ogiva's wig hinged at the crown).
// Attributes are coloured gels set into cut-outs. Poses come from an exposure sheet
// (keyframed joint angles per sack per role), stepped at 12 fps like stop-frame camera work.
// Joint angles are clamped to per-sack hinge limits (testable invariant: every angle in range,
// every child pin coincides with its parent's pin point). The fullness of a sack is changed only
// by REPLACEMENT PROFILES (discrete cut pieces 0..3), never by stretching.
(function () {
function run(g0, t, A, V, K, opt) {
    const W = K.W, H = K.H, S = 1.7, FY = 862;
    const D2R = Math.PI / 180;
    const tq = Math.floor(t * 12 + 1e-6) / 12; // 12 fps exposure steps
    opt = opt || {};
    let g = g0; const measure = !g0;
    const base = g0 ? g0.getTransform() : new DOMMatrix();
    const CA = opt.carry || {};
    const has = (id, tag) => (CA[id] || []).indexOf(tag) >= 0;
    const baseProf = id => has(id, 'emptied') ? 1 : 0;
    // ---------- helpers ----------
    const sm = u => { u = Math.max(0, Math.min(1, u)); return u * u * (3 - 2 * u) };
    const snap = u => { u = Math.max(0, Math.min(1, u)); return 1 - Math.pow(1 - u, 4) };
    function kf(t, ks, ease) { // flat [t0,v0,t1,v1,...]
      ease = ease || sm;
      if (t <= ks[0]) return ks[1];
      for (let i = 0; i < ks.length - 2; i += 2) {
        if (t <= ks[i + 2]) { const u = ease((t - ks[i]) / (ks[i + 2] - ks[i])); return ks[i + 1] + (ks[i + 3] - ks[i + 1]) * u }
      }
      return ks[ks.length - 1];
    }
    const bump = (t, c, w) => { const u = (t - c) / w; return (u > -1 && u < 1) ? 0.5 + 0.5 * Math.cos(u * Math.PI) : 0 };
    const cl = (a, b, x) => Math.max(a, Math.min(b, x));
    const M0 = () => new DOMMatrix();
    const P = (m, x, y) => { const p = m.transformPoint(new DOMPoint(x, y)); return { x: p.x, y: p.y } };
    const BACK = '#f3c766', INK = '#0b0604';
    // ---------- rig: puppet cutter + hinge engineer ----------
    const RIG = {
      R: { wy: .5, earL: .26, earW: .2, earRest: 42, lim: { lean: [-20, 20], waist: [-25, 30], ear: [-35, 170] } },
      B: { wy: .5, earL: .2, earW: .16, earRest: 32, lim: { lean: [-20, 22], waist: [-25, 30], ear: [-35, 170] } },
      I: { wy: .46, earL: .62, earW: .2, earRest: 150, lim: { lean: [-20, 20], waist: [-10, 65], ear: [40, 178] } },
      O: { wy: .55, earL: .15, earW: .3, earRest: 30, lim: { lean: [-18, 18], waist: [-12, 12], ear: [-35, 150] } }
    };
    // replacement profiles: [hScale, wScale, slack]
    const PROF = [[1, 1, 0], [.9, 1.05, .35], [.8, 1.1, .65], [.7, 1.16, 1]];
    function dims(id, prof) {
      const c = K.CAST[id], pr = PROF[cl(0, 3, prof | 0)];
      return { w: c.w * S * pr[1], h: c.h * S * pr[0], slack: id === 'I' ? Math.max(.6, pr[2]) : pr[2] };
    }
    // ---------- payment schedule (victim decides how much and how) ----------
    const FL = .35;
    const PAY = {
      R: [2.45, 3.1, 3.8, 4.35].map(d => ({ d, f: FL, k: 'c' })),
      B: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => ({ d: 2.45 + i * .17, f: FL, k: 'c' })),
      I: [{ d: 2.45, f: FL, k: 'c' }, { d: 2.75, f: 1.0, k: 'n' }, { d: 3.35, f: FL, k: 'c' }, { d: 3.95, f: FL, k: 'c' }],
      O: [0, 1, 2, 3, 4, 5].map(i => ({ d: 2.45 + i * .3, f: FL, k: 'c' }))
    }[V];
    const N = PAY.length;
    const paidAt = tt => { let n = 0; for (const c of PAY) if (c.d + c.f <= tt) n++; return n };
    const arrivals = PAY.map(c => c.d + c.f);
    // ---------- exposure sheets ----------
    const gapBase = 300;
    const xD0 = W / 2 - gapBase / 2 - K.CAST[A].w * S / 2;
    const xV0 = W / 2 + gapBase / 2 + K.CAST[V].w * S / 2;
    function doerPose(t) {
      const p = { x: xD0, lift: 0, lean: 0, waist: 0, eN: RIG[A].earRest, eF: RIG[A].earRest, prof: baseProf(A), wig: 0, wigSlip: 0, photoEar: 'N', hold: 1, photoBehind: t < .85, toss: 0 };
      const pull = V === 'O' ? 22 * bump(t, 2.02, .22) : 0; // yank evidence away from Ogiva's snatch
      if (A === 'R') { // miserly, deliberate, rocks; shows it close
        p.lean = 3 * Math.sin(t * 2 * Math.PI * .8) + kf(t, [1.2, 0, 1.7, 6, 4.6, 6, 5.3, 2]);
        for (const a of arrivals) p.lean += 6 * bump(t, a + .08, .18); // nods each coin in
        p.x += kf(t, [1.2, 0, 1.9, 55]);
        p.eN = kf(t, [.5, 42, 1.2, 105, 1.6, 72, 4.6, 72, 5.3, 100]) - pull;
        p.eF = kf(t, [.5, 42, 1.0, 60, 4.6, 60, 5.3, 30]);
      } else if (A === 'B') { // looms, holds it over his head, leans on the victim
        p.photoEar = 'F';
        p.x += kf(t, [1.1, 0, 2.2, 150]);
        p.lean = kf(t, [1.1, 0, 2.2, 13, 4.5, 13, 5.2, 3]);
        const pump = (t > 2.3 && t < 4.5) ? Math.sin((t - 2.3) * 2 * Math.PI * 3) : 0;
        p.lean += 2.5 * pump;
        p.eF = kf(t, [.5, 32, 1.2, -12, 1.6, -28, 4.6, -28, 5.3, 10]) - pull;
        p.eN = kf(t, [1.8, 32, 2.25, 95]); p.aimN = (t > 2.0 && t < 4.6); p.pump = pump;
        p.eNend = kf(t, [4.5, 0, 5.1, 1]);
      } else if (A === 'I') { // listless, dangles it, tosses it playfully
        p.waist = 16; p.lean = -7 + 2 * Math.sin(t * 1.3);
        p.x += kf(t, [1.2, 0, 2.0, 20]);
        p.eN = kf(t, [.5, 150, 1.2, 95, 1.6, 72, 4.6, 72, 5.3, 92]) + (t > 1.2 ? 14 * Math.sin((t - 1.2) * 2 * Math.PI * .6) : 0) - pull;
        p.eF = 150;
        p.toss = (t > 3.25 && t < 3.95) ? (t - 3.25) / .7 : 0;
      } else { // Ogiva: rigid, cold, at arm's length, snaps
        p.lean = kf(t, [1.0, 0, 1.3, -5], snap);
        p.eN = kf(t, [.6, 30, .8, 70, 1.15, 70, 1.3, 22, 4.9, 22, 5.1, 60], snap) - pull;
        p.eF = 30;
        p.x += kf(t, [4.9, 0, 5.2, -15], snap);
        p.wigFlip = bump(t, 5.15, .25);
      }
      return carryPose(A, p);
    }
    function victimPose(t) {
      const p = { x: xV0, lift: 0, lean: 0, waist: 0, eN: RIG[V].earRest, eF: RIG[V].earRest, prof: 0, wig: 0, wigSlip: 0 };
      const n = paidAt(t); p.prof = Math.min(3, baseProf(V) + Math.floor(3 * n / N + 1e-6));
      let give = 0; for (const c of PAY) give = Math.max(give, bump(t, c.d - .04, .2));
      let jolt = 0; for (let k = 1; k <= 3; k++) { const ti = arrivals[Math.ceil(k * N / 3) - 1]; jolt = Math.max(jolt, bump(t, ti + .05, .15)) }
      if (V === 'R') { // clutches her shawl, rocks, pays coin by coin
        p.lean = kf(t, [1.6, 0, 1.95, -11, 2.35, -6, 2.6, 3, 4.5, 3, 5.3, -13]);
        p.lean += (t > 1.9 && t < 4.5) ? 3.5 * Math.sin(t * 2 * Math.PI * 2) : 0;
        p.x += kf(t, [1.6, 0, 2.0, 25]);
        const clutch = kf(t, [1.6, 42, 1.95, -25, 4.4, -20, 5.2, 150]);
        p.eN = clutch + 105 * give; p.eF = clutch;
      } else if (V === 'B') { // flares up, sees the picture, caves, pours
        p.lift = kf(t, [1.5, 0, 1.8, 22, 2.1, 0]);
        p.lean = kf(t, [1.5, 0, 1.8, 10, 2.25, -8, 4.4, -5, 5.2, -9]);
        p.x += kf(t, [1.5, 0, 1.8, -18, 2.3, 30]);
        const e = kf(t, [1.5, 32, 1.75, -5, 2.2, 60, 2.6, 85, 4.4, 95, 5.2, 168]);
        p.eN = e + 20 * give; p.eF = e;
      } else if (V === 'I') { // barely reacts, shrugs, turns out what he has
        p.waist = kf(t, [0, 12, 2.2, 14, 4.4, 18, 5.2, 24]); p.lift = -kf(t, [4.4, 0, 5.2, 4]);
        p.lean = kf(t, [1.6, 0, 2.0, -4, 5.2, -12]);
        p.eN = kf(t, [1.6, 150, 1.9, 110, 2.2, 150]) - 70 * give; p.eF = kf(t, [4.4, 150, 5.2, 165]);
        if (t > 4.4) p.eN = kf(t, [4.4, 150, 5.2, 165]);
      } else { // Ogiva: snaps upright, snatches, misses, pays precisely, wig slips
        p.lean = kf(t, [1.6, 0, 1.75, -7, 1.95, 9, 2.2, -4, 4.3, -4, 5.1, -13], snap);
        p.x += kf(t, [1.75, 0, 1.95, -45, 2.3, 10], snap);
        p.eN = kf(t, [1.7, 30, 1.85, 75, 2.2, 40], snap) + 50 * give; p.eF = 30;
        p.aimN = (t > 1.82 && t < 2.15);
        p.wigSlip = kf(t, [4.2, 0, 5.1, 1], snap);
      }
      p.lean -= 4 * jolt; p.lift -= 6 * jolt;
      return carryPose(V, p);
    }
    function carryPose(id, p) { // carried damage that changes the hinge state
      if (has(id, 'drowsy') && id !== 'I') { p.eN += 28; p.eF += 28; p.lean -= 3 }
      if (has(id, 'cinched') && id !== 'I') { p.eF += 15 }
      if (id === 'O' && has('O', 'wig')) p.wigSlip = Math.max(p.wigSlip || 0, .7);
      return p;
    }
    // ---------- forward kinematics (pins) ----------
    function fk(id, p, dir, sc) {
      sc = sc || 1;
      const r = RIG[id], L = r.lim, d = dims(id, p.prof);
      const w = d.w * sc, h = d.h * sc;
      const lean = cl(L.lean[0], L.lean[1], p.lean), waist = cl(L.waist[0], L.waist[1], p.waist);
      let eN = cl(L.ear[0], L.ear[1], p.eN), eF = cl(L.ear[0], L.ear[1], p.eF);
      if (id === 'I') { const rot = lean + waist; eN = cl(-60, 240, eN - rot); eF = cl(-60, 240, eF + rot) } // long ears hang by gravity
      const mB = M0().translate(p.x, FY - p.lift * sc).scale(dir, 1).rotate(lean);
      const wyh = r.wy * h;
      const mU = mB.translate(0, -wyh).rotate(waist);
      const hu = h - wyh, cw = .43 * w;
      const mEN = mU.translate(cw, -hu + .03 * h).rotate(eN);
      const mEF = mU.translate(-cw, -hu + .03 * h).rotate(-eF);
      const eL = r.earL * h;
      return { id, w, h, hu, wyh, cw, eL, mB, mU, mEN, mEF, dir, slack: d.slack, lean, waist, eN, eF,
        tipN: P(mEN, 0, -eL), tipF: P(mEF, 0, -eL), top: P(mU, 0, -hu), waistPin: P(mB, 0, -wyh) };
    }
    // aim-solve an ear (hinge engineer): choose angle so the ear points at a world target
    function aim(F, which, target) {
      const m = which === 'N' ? F.mEN : F.mEF;
      const pin = P(m, 0, 0);
      const inv = (which === 'N' ? F.mU.translate(F.cw, -F.hu + .03 * F.h) : F.mU.translate(-F.cw, -F.hu + .03 * F.h)).inverse();
      const q = inv.transformPoint(new DOMPoint(target.x, target.y));
      let a = Math.atan2(q.x, -q.y) / D2R; // angle from local up, toward local +x
      return which === 'N' ? a : -a;
    }
    // ---------- drawing: pieces ----------
    function setM(m) { g.setTransform(base.multiply(m)) }
    function lowerPath(F) { // lower card; its top is an overlapping dome round the waist pin (no gap when the hinge turns)
      const hw = F.w / 2, h = F.h, sl = F.slack, py = -F.wyh;
      const rx = hw * .9, ry = Math.min(hw * .9, F.hu * .75);
      g.beginPath();
      g.moveTo(-hw * .9, 0);
      g.quadraticCurveTo(0, 3, hw * .9, 0);
      g.quadraticCurveTo(hw * (1.08 - .1 * sl), -.06 * h, hw * (1.04 - .08 * sl), -.3 * h);
      g.quadraticCurveTo(hw * (1.0 - .06 * sl), py * .85, hw * .9, py);
      g.ellipse(0, py, rx, ry, 0, 0, Math.PI, true);
      g.quadraticCurveTo(-hw * (1.0 - .06 * sl), py * .85, -hw * (1.04 - .08 * sl), -.3 * h);
      g.quadraticCurveTo(-hw * (1.08 - .1 * sl), -.06 * h, -hw * .9, 0);
      g.closePath();
    }
    function upperPath(F) {
      const hw = F.w / 2, h = F.h, hu = F.hu, sl = F.slack, cw = F.cw;
      const bot = .11 * h, dip = (.03 + .07 * sl) * h;
      g.beginPath();
      g.moveTo(-hw * .9, bot * .2);
      g.quadraticCurveTo(0, bot * 1.6, hw * .9, bot * .2);
      g.quadraticCurveTo(hw * (1.0 - .05 * sl), -hu * .5, cw + .05 * F.w, -hu + .02 * h);
      g.quadraticCurveTo(cw * .5, -hu + dip * .4, 0, -hu + dip);
      g.quadraticCurveTo(-cw * .5, -hu + dip * .4, -cw - .05 * F.w, -hu + .02 * h);
      g.quadraticCurveTo(-hw * (1.0 - .05 * sl), -hu * .5, -hw * .9, bot * .2);
      g.closePath();
    }
    function earPath(F, side) {
      const r = RIG[F.id], L = F.eL, bw = r.earW * F.w * .5, k = side * .12 * L;
      g.beginPath();
      if (F.id === 'I') { // long, ragged, hair-like
        g.moveTo(-bw, 0);
        for (let i = 1; i <= 6; i++) { const u = i / 6, wv = bw * (1 - .7 * u) * (i % 2 ? 1.15 : .85); g.lineTo(-wv + k * u * u, -L * u) }
        g.lineTo(k, -L - 4);
        for (let i = 6; i >= 1; i--) { const u = i / 6, wv = bw * (1 - .7 * u) * (i % 2 ? .85 : 1.15); g.lineTo(wv + k * u * u, -L * u) }
        g.lineTo(bw, 0);
      } else {
        g.moveTo(-bw, 0);
        g.quadraticCurveTo(-bw * .9 + k * .3, -L * .6, -bw * .25 + k, -L);
        g.quadraticCurveTo(k, -L - bw * .4, bw * .25 + k, -L);
        g.quadraticCurveTo(bw * .9 + k * .3, -L * .6, bw, 0);
      }
      g.arc(0, 0, bw, 0, Math.PI);
      g.closePath();
    }
    function cutOn() { g.globalCompositeOperation = 'destination-out'; g.fillStyle = '#000'; g.strokeStyle = '#000' }
    function cutOff() { g.globalCompositeOperation = 'source-over' }
    function pinHole(m, x, y, rr) { setM(m); cutOn(); g.beginPath(); g.arc(x, y, rr, 0, 7); g.fill(); cutOff() }
    function offscreen(rx, ry, rw, rh) { // each puppet is cut on its own card, then laid on the glass
      const cv = g0.canvas, w = cv.width || 1920, h = cv.height || 1080;
      if (!run.oc || run.oc.width !== w || run.oc.height !== h) { run.oc = document.createElement('canvas'); run.oc.width = w; run.oc.height = h }
      const og = run.oc.getContext('2d'); og.setTransform(1, 0, 0, 1, 0, 0); og.globalAlpha = 1; og.globalCompositeOperation = 'source-over'; og.clearRect(rx, ry, rw, rh);
      return og;
    }
    function wheat(r) {
      g.fillStyle = '#eab64c'; g.beginPath(); g.arc(0, 0, r, 0, 7); g.fill();
      g.strokeStyle = INK; g.lineWidth = r * .13; g.beginPath(); g.arc(0, 0, r * .93, 0, 7); g.stroke();
      g.fillStyle = INK; g.lineWidth = r * .07; g.beginPath(); g.moveTo(0, r * .75); g.lineTo(0, -r * .55); g.stroke();
      for (let i = 0; i < 4; i++) { const y = r * (.3 - i * .24); for (const s of [-1, 1]) { g.save(); g.translate(s * r * .11, y); g.rotate(s * .55); g.beginPath(); g.ellipse(0, 0, r * .08, r * .17, 0, 0, 7); g.fill(); g.restore() } }
      g.beginPath(); g.ellipse(0, -r * .66, r * .07, r * .15, 0, 0, 7); g.fill();
    }
    function drawPuppet(id, p, dir, sc, F) {
      F = F || fk(id, p, dir, sc);
      if (sc !== 1) { drawCard(id, p, sc, F); return F } // miniatures inside the photograph: no cut-outs
      const main = g, a0 = main.globalAlpha, bb = bbox(F, p), m = 160;
      // the card's working area in canvas pixels (box + margin for cords, tags, coins)
      const q0 = base.transformPoint(new DOMPoint(bb.x - m, bb.y - m)), q1 = base.transformPoint(new DOMPoint(bb.x + bb.w + m, bb.y + bb.h + m));
      const rx = Math.max(0, Math.floor(Math.min(q0.x, q1.x))), ry = Math.max(0, Math.floor(Math.min(q0.y, q1.y)));
      const rw = Math.ceil(Math.abs(q1.x - q0.x)), rh = Math.ceil(Math.abs(q1.y - q0.y));
      g = offscreen(rx, ry, rw, rh);
      drawCard(id, p, sc, F);
      drawCarry(id, F);
      g = main;
      main.save(); main.setTransform(1, 0, 0, 1, 0, 0); main.globalAlpha = a0 * (has(id, 'greyed') ? .6 : 1);
      const cw = Math.min(rw, run.oc.width - rx), ch = Math.min(rh, run.oc.height - ry);
      if (cw > 0 && ch > 0) main.drawImage(run.oc, rx, ry, cw, ch, rx, ry, cw, ch);
      main.restore();
      return F;
    }
    function drawCarry(id, F) { // incoming damage, drawn as cut card and cord
      const h = F.h, w = F.w, hw = w / 2;
      if (has(id, 'rope')) {
        setM(F.mB); cutOn(); g.lineWidth = 3.5;
        for (const y of [-.16, -.3]) { g.beginPath(); g.moveTo(-hw * .98, y * h); g.quadraticCurveTo(0, y * h + 8, hw * .98, y * h); g.stroke() }
        cutOff(); g.strokeStyle = INK; g.lineWidth = 5; g.lineCap = 'round';
        g.beginPath(); g.moveTo(-hw * 1.0, -.23 * h); g.quadraticCurveTo(-hw * 1.25, -.12 * h, -hw * 1.18, .0 * h - 6); g.stroke();
        g.beginPath(); g.arc(-hw * 1.02, -.23 * h, 7, 0, 7); g.fillStyle = INK; g.fill();
      }
      if (has(id, 'gag')) {
        setM(F.mU); const y = -F.hu * .55; cutOn(); g.lineWidth = 3.5;
        g.beginPath(); g.moveTo(-hw * .95, y - 6); g.lineTo(hw * .95, y - 6); g.moveTo(-hw * .95, y + 6); g.lineTo(hw * .95, y + 6); g.stroke(); cutOff();
        g.fillStyle = INK; g.beginPath(); g.moveTo(-hw * .9, y - 6); g.lineTo(-hw * 1.35, y - 16); g.lineTo(-hw * 1.3, y); g.lineTo(-hw * 1.4, y + 14); g.lineTo(-hw * .9, y + 6); g.fill();
      }
      if (has(id, 'cinched') && id !== 'B') {
        setM(F.mU); const y = -F.hu + .24 * h; cutOn();
        for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(sd * hw * 1.05, y - 12); g.lineTo(sd * hw * .78, y); g.lineTo(sd * hw * 1.05, y + 12); g.fill() }
        g.lineWidth = 3; g.beginPath(); g.moveTo(-hw * .8, y); g.lineTo(hw * .8, y); g.stroke(); cutOff();
      }
      if (has(id, 'torn')) {
        setM(F.mB); cutOn(); g.lineWidth = 3; g.beginPath(); g.moveTo(hw * .55, -.45 * h);
        for (let i = 1; i <= 6; i++) g.lineTo(hw * (.55 + (i % 2 ? .12 : -.02)), -.45 * h + i * .055 * h); g.stroke(); cutOff();
        g.fillStyle = '#fbf7ee'; for (let i = 0; i < 7; i++) { g.beginPath(); g.arc(hw * (.7 + .4 * K.hash(i + 3)), -2 - 3 * K.hash(i * 5), 2.5 + 2 * K.hash(i * 9), 0, 7); g.fill() }
      }
      if (has(id, 'blot')) {
        setM(F.mB); g.fillStyle = '#3d3f96';
        for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(-hw * .3 + (K.hash(i * 2.1) - .5) * .25 * w, -.3 * h + (K.hash(i * 3.7) - .5) * .14 * h, (.04 + .05 * K.hash(i * 1.3)) * w, 0, 7); g.fill() }
      }
      if (has(id, 'tag')) {
        const pin = P(F.mEF, 0, 0); setM(M0());
        g.strokeStyle = INK; g.lineWidth = 2; g.beginPath(); g.moveTo(pin.x, pin.y); g.lineTo(pin.x - F.dir * 30, pin.y + 46); g.stroke();
        g.save(); g.translate(pin.x - F.dir * 30, pin.y + 46); g.rotate(-F.dir * .2);
        g.fillStyle = INK; g.fillRect(-24, 0, 48, 32); g.fillStyle = '#efe2c0'; g.fillRect(-20, 4, 40, 24); g.fillStyle = INK; g.beginPath(); g.arc(0, 8, 3, 0, 7); g.fill(); g.restore();
      }
      if (has(id, 'coins')) { const q = P(F.mB, -(hw + 30), 0); for (let k = 0; k < 3; k++) coinEdge(q.x, FY - 7 - 12 * k, 22) }
    }
    function drawCard(id, p, sc, F) {
      const h = F.h, w = F.w;
      g.fillStyle = INK;
      // far ear sits behind the upper piece; near ear in front
      setM(F.mEF); earPath(F, -1); g.fill();
      setM(F.mB); lowerPath(F); g.fill();
      if (id === 'B' && sc === 1) { // belt slits + buckle cut-out at 40% height
        const y = -.4 * h, hw = w / 2 * 1.0;
        cutOn();
        g.fillRect(-hw * .9, y - .045 * h, hw * 1.8, Math.max(1.5, 2.5 * sc));
        g.fillRect(-hw * .9, y + .045 * h, hw * 1.8, Math.max(1.5, 2.5 * sc));
        g.lineWidth = Math.max(1.2, 2.4 * sc); g.strokeRect(-.07 * w, y - .03 * h, .14 * w, .06 * h); cutOff();
      }
      if (id === 'I' && sc === 1) { // patch stitches cut through the cloth
        cutOn();
        for (let i = 0; i < 5; i++) g.fillRect(-.22 * w + i * .07 * w, -.22 * h, .035 * w, Math.max(1, 2 * sc));
        for (let i = 0; i < 4; i++) g.fillRect(.12 * w, -.34 * h + i * .05 * h, Math.max(1, 2 * sc), .028 * h);
        cutOff();
      }
      g.fillStyle = INK;
      setM(F.mU); upperPath(F); g.fill();
      if (id === 'R') { // shawl gel band across the top fifth, black lace and fringe
        const hu = F.hu, y0 = -hu + .03 * h, y1 = -hu + .2 * h * 1.05;
        g.save(); upperPath(F); g.clip();
        g.fillStyle = '#a24a3d'; g.fillRect(-w, y0, 2 * w, y1 - y0);
        g.fillStyle = INK;
        for (let i = -6; i <= 6; i++) { const x = i * w * .085; g.beginPath(); g.moveTo(x, y0 + (y1 - y0) * .2); g.lineTo(x + w * .025, (y0 + y1) / 2); g.lineTo(x, y1 - (y1 - y0) * .2); g.lineTo(x - w * .025, (y0 + y1) / 2); g.fill() }
        g.restore();
        g.fillStyle = '#a24a3d'; // fringe teeth hanging below the band
        for (let i = -5; i <= 5; i++) { const x = i * w * .085; g.beginPath(); g.moveTo(x - w * .03, y1 - 1); g.lineTo(x + w * .03, y1 - 1); g.lineTo(x, y1 + .07 * h); g.fill() }
      }
      if (id === 'B') { setM(F.mU.translate(0, -(.66 * h - F.wyh))); wheat(.13 * h) }
      setM(F.mEN); g.fillStyle = INK; earPath(F, 1); g.fill();
      if (id === 'O') drawWig(F, p, sc);
      if (sc === 1) { // pins: tiny pricks of backlight through the card
        pinHole(F.mU, 0, 0, 2.6); pinHole(F.mEN, 0, 0, 2.2); pinHole(F.mEF, 0, 0, 2.2);
      }
    }
    function drawWig(F, p, sc) {
      const h = F.h, w = F.w;
      const ang = (p.wig || 0) + 28 * (p.wigSlip || 0);
      const m = F.mU.translate(.0, -F.hu + .02 * h).translate(p.wigSlip * .12 * w, p.wigSlip * .12 * h).rotate(ang);
      setM(m);
      const L = .5 * h, hw = w * .62;
      g.fillStyle = '#9a4fba';
      g.beginPath();
      g.moveTo(-hw * .7, .02 * h);
      g.quadraticCurveTo(-hw * .8, -.12 * h, 0, -.11 * h);
      g.quadraticCurveTo(hw * .8, -.12 * h, hw * .7, .02 * h);
      g.quadraticCurveTo(hw * 1.05, L * .5, hw * .95, L);
      g.lineTo(hw * .55, L * .96); g.quadraticCurveTo(hw * .62, L * .4, hw * .32, .07 * h);
      g.lineTo(-hw * .32, .07 * h); g.quadraticCurveTo(-hw * .62, L * .4, -hw * .55, L * .96);
      g.lineTo(-hw * .95, L); g.quadraticCurveTo(-hw * 1.05, L * .5, -hw * .7, .02 * h);
      g.closePath(); g.fill();
      g.strokeStyle = INK; g.lineWidth = Math.max(1, 2.2 * sc);
      for (const s of [-1, 1]) for (let i = 0; i < 3; i++) { const x = s * hw * (.66 + i * .1); g.beginPath(); g.moveTo(s * hw * (.45 + i * .1), .0); g.quadraticCurveTo(x + s * hw * .1, L * .5, x, L * .92); g.stroke() }
      g.beginPath(); g.moveTo(-hw * .5, -.06 * h); g.quadraticCurveTo(0, -.02 * h, hw * .5, -.06 * h); g.stroke();
      if (sc === 1) pinHole(m, 0, -.04 * h, 2.2);
    }
    function bbox(F, p) { // screen box of the sack's body (pieces, ears, wig)
      const hw = F.w / 2, h = F.h, pts = [];
      for (const sd of [-1, 1]) {
        pts.push(P(F.mB, sd * hw * 1.08, 0), P(F.mB, sd * hw * 1.04, -.3 * h), P(F.mU, sd * hw, .11 * h), P(F.mU, sd * (F.cw + .05 * F.w), -F.hu));
      }
      pts.push(P(F.mB, 0, -F.wyh - Math.min(hw * .9, F.hu * .75)), F.tipN, F.tipF);
      if (F.id === 'O') { pts.push(P(F.mU, -hw * .62, .5 * h - F.hu), P(F.mU, hw * .62, .5 * h - F.hu), P(F.mU, 0, -F.hu - .11 * h)) }
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for (const q of pts) { x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.x); y1 = Math.max(y1, q.y) }
      y1 = Math.min(y1, FY);
      return { x: Math.round(x0), y: Math.round(y0), w: Math.round(x1 - x0), h: Math.round(y1 - y0) };
    }
    // ---------- the evidence ----------
    function drawPhotoAt(mm, gw, gh, sc, alpha) {
      setM(mm);
      g.globalAlpha = alpha;
      g.fillStyle = INK; g.fillRect(-gw / 2 - 6 * sc, -gh / 2 - 6 * sc, gw + 12 * sc, gh + 12 * sc);
      g.fillStyle = '#f7e6bd'; g.fillRect(-gw / 2, -gh / 2, gw, gh);
      // inner scene
      const vs = (gh * .5) / (K.CAST[V].h * S), ss = (gh * .55) / (150 * S);
      const by = mm.translate(0, gh / 2 - gh * .08);
      const vx = by.translate(gw * .2, 0), sx = by.translate(-gw * .22, 0);
      const pv = { x: 0, lift: 0, lean: 12, waist: 6, eN: 60, eF: RIG[V].earRest, prof: 0, wig: 0, wigSlip: 0 };
      const save = base;
      // victim mini (faces left, toward the stranger)
      const Fv = fkAt(V, pv, -1, vs, vx);
      drawPuppetAt(V, pv, Fv, vs);
      // stranger: plain sack leaning in
      setM(sx.rotate(14)); g.fillStyle = INK;
      const sw = 110 * S * ss, sh = 150 * S * ss;
      g.beginPath(); g.moveTo(-sw / 2, 0); g.lineTo(sw / 2, 0); g.quadraticCurveTo(sw * .58, -sh * .5, sw * .45, -sh); g.lineTo(sw * .3, -sh * 1.12); g.lineTo(sw * .15, -sh * .97); g.lineTo(-sw * .15, -sh * .97); g.lineTo(-sw * .3, -sh * 1.12); g.lineTo(-sw * .45, -sh); g.quadraticCurveTo(-sw * .58, -sh * .5, -sw / 2, 0); g.fill();
      // heart cut between them
      setM(mm.translate(0, -gh * .28)); g.fillStyle = '#c4473a';
      const hr = gh * .09; g.beginPath(); g.moveTo(0, hr * 1.1); g.bezierCurveTo(-hr * 1.6, -hr * .1, -hr * .6, -hr * 1.3, 0, -hr * .35); g.bezierCurveTo(hr * .6, -hr * 1.3, hr * 1.6, -hr * .1, 0, hr * 1.1); g.fill();
      g.globalAlpha = 1;
    }
    function fkAt(id, p, dir, sc, mm) {
      const F = fk(id, Object.assign({}, p, { x: 0, lift: 0 }), dir, sc);
      const pre = mm;
      for (const k of ['mB', 'mU', 'mEN', 'mEF']) F[k] = pre.multiply(new DOMMatrix().translate(0, -FY)).multiply(fk(id, Object.assign({}, p, { x: 0, lift: 0 }), dir, sc)[k]);
      return F;
    }
    function drawPuppetAt(id, p, F, sc) { drawPuppet(id, p, F.dir, sc, F) }
    // ---------- world: light and negative-space compositor ----------
    function backdrop() {
      g.setTransform(base);
      const fl = 1 + .025 * (K.hash(Math.floor(t * 12) * 3.1) - .5);
      const gr = g.createRadialGradient(960, 210, 40, 960, 470, 1250);
      gr.addColorStop(0, '#fff0b8'); gr.addColorStop(.22, '#f6cd70'); gr.addColorStop(.6, '#d98d32'); gr.addColorStop(1, '#5e2a0b');
      g.fillStyle = gr; g.fillRect(0, 0, W, H);
      g.globalAlpha = .08 * (fl - .975) / .05; g.fillStyle = '#fff'; g.fillRect(0, 0, W, H); g.globalAlpha = 1;
      // midground cards: grey, stepped back
      g.fillStyle = 'rgba(40,16,4,.30)';
      // staircase, far left
      g.beginPath(); g.moveTo(0, FY);
      for (let i = 0; i < 9; i++) { g.lineTo(i * 34, FY - i * 46); g.lineTo(i * 34 + 34, FY - i * 46) }
      g.lineTo(306, FY - 9 * 46); g.lineTo(0, FY - 9 * 46); g.closePath(); g.fill();
      g.fillRect(0, FY - 9 * 46 - 14, 330, 14);
      for (let i = 1; i < 9; i++) g.fillRect(i * 34 + 20, FY - i * 46 - 70, 5, 70);
      // door with arched head, far right
      g.beginPath(); g.moveTo(1590, FY); g.lineTo(1590, 470); g.arc(1680, 470, 90, Math.PI, 0); g.lineTo(1770, FY); g.closePath(); g.fill();
      g.fillStyle = 'rgba(40,16,4,.18)'; g.fillRect(1612, 480, 136, 380);
      g.fillStyle = INK; g.fillRect(0, FY, W, H - FY);
      for (let x = 0; x < W; x += 48) { g.beginPath(); g.arc(x + 24, FY + 2, 9, Math.PI, 0); g.fill() }
      // a framed picture on the wall and wallpaper sprigs
      g.fillStyle = 'rgba(40,16,4,.22)';
      for (let i = 0; i < 14; i++) { const x = 380 + i * 90, y = 300 + (i % 2) * 70; if (x > 1560) continue; g.beginPath(); g.ellipse(x, y, 5, 11, .5, 0, 7); g.fill(); g.beginPath(); g.ellipse(x + 9, y + 6, 5, 10, -.5, 0, 7); g.fill() }
    }
    function projection(F) { // the photograph's picture thrown large on the wall
      const a = kf(tq, [1.3, 0, 1.75, 1, 3.1, 1, 3.7, 0]);
      if (a <= 0) return;
      const gw = 480, gh = 340;
      const mm = M0().translate(960, 300);
      g.save();
      drawPhotoAt(mm, gw, gh, 3, .38 * a);
      g.restore();
      g.setTransform(base);
    }
    function foreground() {
      g.setTransform(base); g.fillStyle = INK;
      // arched proscenium with leaf scrolls
      g.beginPath(); g.moveTo(0, 0); g.lineTo(W, 0); g.lineTo(W, 300); g.quadraticCurveTo(W - 40, 60, W - 420, 34); g.lineTo(420, 34); g.quadraticCurveTo(40, 60, 0, 300); g.closePath(); g.fill();
      g.fillRect(0, 0, 34, H); g.fillRect(W - 34, 0, 34, H);
      for (const s of [-1, 1]) for (let i = 0; i < 7; i++) {
        const x = s < 0 ? 60 + i * 52 : W - 60 - i * 52, y = 60 + i * 6 + (i % 2) * 22;
        g.save(); g.translate(x, y); g.rotate(s * (.9 - i * .12)); g.beginPath(); g.ellipse(0, 18, 9, 22, 0, 0, 7); g.fill(); g.restore();
      }
      // hanging lamp, centre
      g.fillRect(958, 30, 4, 58);
      g.beginPath(); g.moveTo(915, 120); g.quadraticCurveTo(960, 70, 1005, 120); g.lineTo(990, 128); g.lineTo(930, 128); g.closePath(); g.fill();
      g.fillStyle = '#fff6d0'; g.beginPath(); g.ellipse(960, 140, 22, 14, 0, 0, 7); g.fill();
      g.fillStyle = INK; for (let i = 0; i < 7; i++) { g.beginPath(); g.moveTo(926 + i * 11, 128); g.lineTo(931 + i * 11, 146); g.lineTo(936 + i * 11, 128); g.fill() }
      // vignette
      const v = g.createRadialGradient(960, 520, 520, 960, 520, 1150);
      v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.5)');
      g.fillStyle = v; g.fillRect(0, 0, W, H);
    }
    // ---------- coins ----------
    function coinFace(x, y, r, spin) {
      g.setTransform(base); g.save(); g.translate(x, y); g.scale(Math.max(.15, Math.abs(Math.cos(spin))), 1);
      g.fillStyle = INK; g.beginPath(); g.arc(0, 0, r + 2.5, 0, 7); g.fill();
      g.fillStyle = '#f2c24a'; g.beginPath(); g.arc(0, 0, r, 0, 7); g.fill();
      g.strokeStyle = INK; g.lineWidth = 2; g.beginPath(); g.arc(0, 0, r * .55, 0, 7); g.stroke(); g.restore();
    }
    function coinEdge(x, y, r) {
      g.setTransform(base); g.fillStyle = INK; g.beginPath(); g.ellipse(x, y, r + 3, 6.5, 0, 0, 7); g.fill();
      g.fillStyle = '#f2c24a'; g.beginPath(); g.ellipse(x, y - 1, r, 3.6, 0, 0, 7); g.fill();
    }
    function note(x, y, rot, sx) {
      g.setTransform(base); g.save(); g.translate(x, y); g.rotate(rot); g.scale(sx, 1);
      g.fillStyle = INK; g.fillRect(-36, -20, 72, 40); g.fillStyle = '#d9dc9a'; g.fillRect(-32, -16, 64, 32);
      g.fillStyle = INK; g.beginPath(); g.ellipse(0, 0, 10, 12, 0, 0, 7); g.fill(); g.fillRect(-28, -12, 8, 24); g.fillRect(20, -12, 8, 24); g.restore();
    }
    // ================= compose =================
    let pd = doerPose(tq), pv = victimPose(tq);
    // contact plane: keep a minimum gap (bodies do not interpenetrate)
    const wA = dims(A, pd.prof).w, wV = dims(V, pv.prof).w;
    const minGap = A === 'B' ? 36 : 60;
    if ((pv.x - wV / 2) - (pd.x + wA / 2) < minGap) pd.x = pv.x - wV / 2 - wA / 2 - minGap;
    let FD = fk(A, pd, 1), FV = fk(V, pv, -1);
    // Belindo leans his near ear down onto the victim's crown
    if (A === 'B' && pd.aimN) {
      const tgt = { x: FV.top.x - 10, y: FV.top.y + 6 + 6 * (pd.pump || 0) };
      pd.eN = aim(FD, 'N', tgt); FD = fk(A, pd, 1);
    }
    if (A === 'B' && pd.eNend > 0) { pd.eN = pd.eN + (40 - pd.eN) * pd.eNend; FD = fk(A, pd, 1) }
    // photo placement
    const PW = 124, PH = 94;
    const tipH = pd.photoEar === 'N' ? FD.tipN : FD.tipF;
    const earAng = pd.photoEar === 'N' ? FD.eN + FD.lean + FD.waist : -(FD.eF) + FD.lean + FD.waist; // world direction of the holding ear
    const hang = Math.abs(earAng) > 105;
    let phx = tipH.x, phy = tipH.y, phr;
    if (hang) { phr = Math.sin(tq * 2.1) * 8; phy += PH / 2 + 4 } else { phr = earAng * .22; phy -= PH / 2 - 6 }
    if (pd.toss > 0) { const u = pd.toss; phy -= 260 * 4 * u * (1 - u); phx += 30 * Math.sin(u * Math.PI); phr += 360 * u }
    const photoA = A === 'R' || A === 'I' || A === 'B' ? kf(tq, [.55, 0, .75, 1]) : kf(tq, [.6, 0, .7, 1]);
    // Ogiva victim's ear snatches at the photo (and misses)
    if (V === 'O' && pv.aimN) { pv.eN = aim(FV, 'N', { x: phx + 30, y: phy + 40 }); FV = fk(V, pv, -1) }
    // wig secondary motion: lag of the body angle (evaluated from the exposure sheet a beat earlier)
    for (const [who, F, poseFn, pp] of [[A, FD, doerPose, pd], [V, FV, victimPose, pv]]) {
      if (who !== 'O') continue;
      const prev = poseFn(Math.max(0, tq - 1 / 12));
      const vel = (pp.lean + pp.waist) - (prev.lean + prev.waist);
      pp.wig = cl(-14, 14, -vel * 1.6) + 18 * Math.sin((pp.wigFlip || 0) * Math.PI) * (pp.wigFlip ? 1 : 0);
    }
    const fin = doerPose(5.9); const wAf = dims(A, 0).w;
    let stackX = Math.min(fin.x, (xV0 - wV / 2) - wAf / 2 - minGap) + wAf / 2 + 34;
    if (A === 'B') stackX -= 60;
    if (measure) return { A: bbox(FD, pd), V: bbox(FV, pv), FD, FV, pd, pv, PAY, arrivals, stackX, phx, phy };
    const L = opt.layer, doBG = !L || L === 'bg', doA = !L || L === 'A', doV = !L || L === 'V';
    // layers: bg (glass, midground, wall projection, proscenium) -> A (doer, photo, coin stack) -> V (victim, money in flight)
    if (doBG) { backdrop(); projection(); foreground() }
    const phM = M0().translate(phx, phy).rotate(phr);
    if (doA) {
      if (pd.photoBehind && photoA > 0) drawPhotoAt(phM, PW, PH, 1, 1);
      drawPuppet(A, pd, 1, 1, FD);
      if (!pd.photoBehind && photoA > 0) drawPhotoAt(phM, PW, PH, 1, 1);
      g.setTransform(base);
    }
    if (doV) drawPuppet(V, pv, -1, 1, FV);
    // payment: flights from the victim, landing on the doer's stack
    const srcAt = d => {
      const pv2 = victimPose(Math.floor(d * 12) / 12); const F2 = fk(V, pv2, -1);
      if (A === 'B') return { x: F2.top.x, y: F2.top.y + 10 };
      return F2.tipN;
    };
    let landed = 0;
    PAY.forEach((c, i) => {
      const arr = c.d + c.f;
      const scatter = V === 'I' ? (K.hash(i * 7.3 + 1) - .5) * 90 : 0;
      if (c.k === 'n') {
        const dx = stackX + 40, dy = FY - 8;
        if (tq < c.d) return;
        if (tq >= arr) { if (doA) note(dx, dy - 2, .06, 1); return }
        if (!doV) return;
        const u = (tq - c.d) / c.f, s = srcAt(c.d);
        const x = s.x + (dx - s.x) * u + 30 * Math.sin(u * 9), y = s.y + (dy - s.y) * u * u - 60 * Math.sin(u * Math.PI);
        note(x, y, Math.sin(u * 11) * .6, Math.cos(u * 8));
        return;
      }
      const k = landed;
      const dx = stackX + scatter, dy = V === 'I' ? FY - 4 : FY - 7 - 12 * k;
      if (tq >= arr) { if (doA) coinEdge(dx, dy, 25); landed++; return }
      if (tq < c.d || !doV) return;
      const u = (tq - c.d) / c.f, s = srcAt(c.d);
      const peak = Math.min(s.y, dy) - 90;
      const x = s.x + (dx - s.x) * u;
      const y = (1 - u) * (1 - u) * s.y + 2 * u * (1 - u) * peak + u * u * dy;
      coinFace(x, y, 25, u * 9 + i);
    });
    g.setTransform(base);
}

function sound(ac, out, t0, A, V, K) {
  const S = K.SND, H = K.hash;
  const st = tt => run(null, Math.max(0, Math.min(5.99, tt)), A, V, K, {});
  const s0 = st(0), PAY = s0.PAY, arr = s0.arrivals, N = PAY.length;
  const pan = x => Math.max(-1, Math.min(1, x / 960 - 1));
  const pA = tt => pan(st(tt).FD.waistPin.x), pV = tt => pan(st(tt).FV.waistPin.x), pS = pan(s0.stackX);
  const at = tt => t0 + tt;
  const click = (tt, a, p) => { S.grain(ac, out, at(tt), { bp: 2600, q: 5, d: .012, a: a, pan: p, att: .1 }); S.grain(ac, out, at(tt), { f: 1900, d: .01, a: a * .3, pan: p, att: .1 }) };
  // the stop-frame camera: a faint shutter tick on every exposure (12 a second); the lamp hum of the glass table
  for (let k = 0; k < 72; k++) S.grain(ac, out, at(k / 12 + .001), { bp: 5200, q: 6, d: .006, a: .012, pan: 0, att: .2 });
  S.cloud(ac, out, at(0), 6, 14, { f: 98, a: .012, d: [.3, .6], spread: .1 });
  S.say(ac, out, A, at(.02), 'breathe', .5, pA(0)); S.say(ac, out, V, at(.05), 'breathe', .5, pV(0));
  // the photograph slides out from behind the card and is pinned up
  S.cloud(ac, out, at(.55), .3, 90, { bp: 3600, a: .03, d: [.01, .03], spread: .2 }, u => u);
  click(.85, .22, pA(.85)); click(1.27, .2, pA(1.27));
  // the picture is thrown on the wall: a soft harmonium of grains
  S.cloud(ac, out, at(1.3), 1.9, 40, { pitches: [57, 60, 64, 69], a: .022, d: [.15, .4], spread: .3 }, u => Math.sin(Math.PI * u));
  // doer's way of coming
  const steps = { R: [1.35, 1.6, 1.85], B: [1.35, 1.7, 2.05], I: [1.4, 1.85], O: [5.0] }[A];
  for (const s of steps) S.say(ac, out, A, at(s), 'step', A === 'I' ? .5 : .8, pA(s));
  if (A === 'R') for (const a of arr) S.say(ac, out, 'R', at(a + .1), 'tick', .5, pA(a));
  if (A === 'B') for (let k = 0; ; k++) { const tt = 2.3 + (.25 + k) / 3; if (tt > 4.45) break; S.say(ac, out, 'B', at(tt), 'step', .3, pA(tt)) }
  if (A === 'I') { S.grain(ac, out, at(3.25), { bp: 1400, q: 1, d: .4, a: .05, pan: pA(3.3) }); click(3.95, .2, pA(3.95)); S.say(ac, out, 'I', at(4.0), 'breathe', .6, pA(4)) }
  if (A === 'O') { S.say(ac, out, 'O', at(.8), 'tick', .7, pA(.8)); S.say(ac, out, 'O', at(1.3), 'tick', .7, pA(1.3)); S.cloud(ac, out, at(5.05), .22, 80, { bp: 5200, a: .03, d: [.01, .03], spread: .2 }, u => Math.sin(Math.PI * u)) }
  // victim sees it
  const react = { R: 1.65, B: 1.55, I: 1.75, O: 1.62 }[V];
  S.say(ac, out, V, at(react), 'react', V === 'I' ? .6 : 1, pV(react));
  if (V === 'B') S.say(ac, out, 'B', at(2.1), 'land', .7, pV(2.1));
  if (V === 'R') S.say(ac, out, 'R', at(1.85), 'step', .6, pV(1.85));
  if (V === 'O') { S.grain(ac, out, at(1.83), { bp: 2600, q: 1.2, d: .18, a: .07, pan: pV(1.85) }); click(2.02, .25, pV(2.02)); S.say(ac, out, 'O', at(1.92), 'step', .6, pV(1.92)) }
  // payment: tick out of the victim, a whistle in the air, a clink on the stack; the coins walk down a scale
  const scale = [76, 74, 72, 69, 67, 64, 62, 60, 57, 55];
  PAY.forEach((c, i) => {
    const a = c.d + c.f, ps = pV(c.d);
    S.say(ac, out, V, at(c.d), 'tick', .35, ps);
    if (c.k === 'n') { S.cloud(ac, out, at(c.d), c.f, 60, { bp: 2000, a: .02, d: [.01, .04], spread: .3 }); S.grain(ac, out, at(a), { bp: 1500, d: .05, a: .08, pan: pS }); return }
    S.grain(ac, out, at(c.d + .02), { f: 1700 + 300 * H(i + 1), d: c.f * .9, a: .012, glide: -.35, pan: (ps + pS) / 2 });
    S.grain(ac, out, at(a), { f: 2400 + 900 * H(i * 3 + 2), d: .07, a: .11, att: .05, type: 'triangle', pan: pS });
    S.grain(ac, out, at(a), { bp: 6500, q: 3, d: .03, a: .1, pan: pS, att: .1 });
    S.pluck(ac, out, at(a), scale[Math.min(i, 9)], .1, .5, pS);
  });
  // contact: the first coin lands — the deed is done
  const c0 = arr[0];
  S.thump(ac, out, at(c0), .9, 70, pS); S.say(ac, out, A, at(c0 + .02), 'land', .5, pS);
  for (const m of [64, 69, 76]) S.pluck(ac, out, at(c0 + .01), m, .14, .9, pS);
  // replacement profiles swapped in: a card slap and the victim's sinking voice
  for (let k = 1; k <= 3; k++) { const tt = arr[Math.ceil(k * N / 3) - 1] + .05; S.grain(ac, out, at(tt), { bp: 900, q: 2, d: .04, a: .18, pan: pV(tt), att: .1 }); S.say(ac, out, V, at(tt), 'sink', .45, pV(tt)) }
  S.say(ac, out, V, at(5.0), 'sink', .8, pV(5)); S.say(ac, out, A, at(5.4), 'breathe', .5, pA(5.4));
}

DEED({
  n: 1, key: 'blackmail', title: 'Blackmail',
  scion: 2, lineage: 'SCION-LOTTE-REINIGER · Articulated Shadow Theater',
  op: 'The doer raises a photograph of the victim to the light; the victim pays coins across to the doer\'s side and is swapped for an emptier cut piece.',
  made: 'Black card silhouettes pinned at waist and ear-corners, with coloured gels set into cut-outs (shawl, belt slits and wheat stencil, wig), on an amber backlit glass table with grey midground cards and a black foreground frame and lamp. The evidence is a small framed photograph whose picture is also thrown large on the back wall; the money is gold-gel discs and one paper note.',
  moved: 'An exposure sheet of keyed joint angles per sack and role, stepped at 12 frames a second and clamped to each hinge\'s limits, with ears acting as hands and simple aim-solves for reaching. Payment is a schedule of coin flights; each landed share swaps the victim for a lower, slacker replacement profile.',
  contact: 2.8,
  leaves: { A: ['coins'], V: ['emptied', 'wig'] }, // 'wig' only applies when the victim is Ogiva
  draw(g, t, A, V, K, opt) { run(g, t, A, V, K, opt) },
  marks(t, A, V, K) { const m = run(null, t, A, V, K, {}); return { A: m.A, V: m.V } },
  sound(ac, out, t0, A, V, K) { sound(ac, out, t0, A, V, K) }
});
})();
