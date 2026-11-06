// 06 · Threatening with a Gun — SCION 33 · Inverse Kinematics, Contact and Reach
// Every sack is a FABRIK spine chain rooted between two floor contacts (planted-foot locks);
// every ear is an analytic two-bone IK chain solved to a world-space target with a pole vector.
// The revolver is a prop that changes owner at a grip contact; the wall is a contact plane.
(function () {
  const S = 1.3, FLOOR = 880, WALLBASE = 822, WALL = 1700, NSEG = 6, CONTACT = 2.4;
  const G = 2.9; // revolver scale
  const EARL = { R: 72, B: 112, I: 92, O: 78 };
  const OUT = '#3a2d20';

  // ---------- vector + solver primitives ----------
  const V2 = (x, y) => ({ x, y });
  const add = (a, b) => V2(a.x + b.x, a.y + b.y), sub = (a, b) => V2(a.x - b.x, a.y - b.y);
  const mul = (a, s) => V2(a.x * s, a.y * s), len = a => Math.hypot(a.x, a.y);
  const nrm = a => { const l = len(a) || 1; return V2(a.x / l, a.y / l); };
  const mix = (a, b, u) => V2(a.x + (b.x - a.x) * u, a.y + (b.y - a.y) * u);
  const sm = (a, b, x) => { const u = Math.max(0, Math.min(1, (x - a) / (b - a))); return u * u * (3 - 2 * u); };
  const cl = (a, b, x) => Math.max(a, Math.min(b, x));
  // damped spring response to an event at s=0 (0 before, overshoots, settles to 0)
  const ring = (s, k, w) => s <= 0 ? 0 : Math.exp(-k * s) * Math.sin(w * s);
  // step response with overshoot (0 -> 1)
  const rise = (s, k, w) => s <= 0 ? 0 : 1 - Math.exp(-k * s) * Math.cos(w * s);

  // FABRIK spine: root locked (contact), top drawn to target; bias picks bend side
  function fabrik(root, n, seg, target, bias) {
    const p = [];
    for (let i = 0; i <= n; i++) p.push(V2(root.x + bias * Math.sin(Math.PI * i / n), root.y - seg * i));
    for (let it = 0; it < 12; it++) {
      p[n] = V2(target.x, target.y);
      for (let i = n - 1; i >= 0; i--) p[i] = add(p[i + 1], mul(nrm(sub(p[i], p[i + 1])), seg));
      p[0] = V2(root.x, root.y);
      for (let i = 1; i <= n; i++) p[i] = add(p[i - 1], mul(nrm(sub(p[i], p[i - 1])), seg));
    }
    return p;
  }
  // analytic two-bone IK with pole vector; returns joints + residual
  function twoBone(P, T, a, b, pole) {
    const D = sub(T, P), d = len(D);
    const dc = cl(Math.abs(a - b) + 0.01, a + b - 0.01, d);
    const base = Math.atan2(D.y, D.x);
    const A = Math.acos(cl(-1, 1, (a * a + dc * dc - b * b) / (2 * a * dc)));
    let E = null, best = -1e9;
    const mid = mix(P, T, 0.5);
    for (const s of [1, -1]) {
      const ang = base + s * A, e = V2(P.x + a * Math.cos(ang), P.y + a * Math.sin(ang));
      const sc = (e.x - mid.x) * pole.x + (e.y - mid.y) * pole.y;
      if (sc > best) { best = sc; E = e; }
    }
    const tip = add(E, mul(nrm(sub(T, E)), b));
    return { P, E, tip, res: len(sub(tip, T)) };
  }
  // planted-foot stepping: alternate half-steps, one foot locked while the other swings
  function feetAt(t, cx, w, plan, D) {
    const n = Math.max(plan.n, plan.slide ? 1 : Math.ceil(Math.abs(D) / (w * 0.4))), half = n * 2, dt = (plan.t1 - plan.t0) / half;
    const lead = D >= 0 ? 1 : -1; // foot on the side of travel moves first
    let movL = 0, movR = 0, liftL = 0, liftR = 0, swingL = false, swingR = false;
    const stepD = D / n;
    for (let k = 0; k < half; k++) {
      const a = plan.t0 + k * dt, u = plan.crisp ? sm(a, a + dt * 0.7, t) : sm(a, a + dt, t);
      const isLead = k % 2 === 0, side = isLead ? lead : -lead;
      const live = t > a && t < a + dt;
      const lift = Math.sin(Math.PI * u) * plan.lift;
      if (side > 0) { movR += stepD * u; if (live) { liftR = lift; swingR = true; } }
      else { movL += stepD * u; if (live) { liftL = lift; swingL = true; } }
    }
    if (n === 1 && plan.slide) { // a slide: both feet drag together, no lock released
      const u = sm(plan.t0, plan.t1, t); movL = movR = D * u; liftL = liftR = 0; swingL = swingR = false;
    }
    return {
      L: V2(cx - w / 2 + movL, FLOOR - liftL), R: V2(cx + w / 2 + movR, FLOOR - liftR),
      lockL: !swingL, lockR: !swingR
    };
  }

  // ---------- a sack: solve body from feet + top target ----------
  function solveSack(id, feet, lean, squash, bias) {
    const c = K_.CAST[id], w = c.w * S, h = c.h * S;
    const root = mix(feet.L, feet.R, 0.5);
    // squash shortens the chain (flour settles); bias only chooses the bend side
    squash *= (has(id, 'emptied') ? 0.84 : 1) * (has(id, 'drowsy') ? 0.96 : 1);
    const seg = h * squash / NSEG;
    const tgt = V2(root.x + lean, root.y - h * squash * 0.995);
    const p = fabrik(root, NSEG, seg, tgt, bias);
    const Ls = [], Rs = [];
    for (let i = 0; i <= NSEG; i++) {
      const a = p[Math.max(0, i - 1)], b = p[Math.min(NSEG, i + 1)];
      const tg = nrm(sub(b, a)), nl = V2(tg.y, -tg.x);
      const u = i / NSEG;
      let half = w / 2 * (1 + 0.07 * Math.sin(Math.PI * u) - (u > 0.8 ? (u - 0.8) * 0.35 : 0));
      if (id === 'I') half *= 1.12 - 0.3 * u; // half empty: the flour has pooled at the bottom
      if (has(id, 'emptied')) half *= 1.06 - 0.12 * u;
      if (has(id, 'cinched')) half *= 1 - 0.3 * Math.exp(-Math.pow((u - 0.84) / 0.07, 2)); // neck pinched
      Ls.push(add(p[i], mul(nl, half))); Rs.push(sub(p[i], mul(nl, half)));
    }
    Ls[0] = feet.L; Rs[0] = feet.R;
    return { id, w, h, p, Ls, Rs, feet, cornerL: Ls[NSEG], cornerR: Rs[NSEG], top: p[NSEG] };
  }
  // point on body edge at fractional height u (0..1)
  function edgeAt(arr, u) {
    const f = u * NSEG, i = Math.min(NSEG - 1, Math.floor(f));
    return mix(arr[i], arr[i + 1], f - i);
  }
  function smoothPoly(g, pts, move) {
    if (move) g.moveTo(pts[0].x, pts[0].y); else g.lineTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length - 1; i++) {
      const m = mix(pts[i], pts[i + 1], 0.5); g.quadraticCurveTo(pts[i].x, pts[i].y, m.x, m.y);
    }
    const l = pts[pts.length - 1]; g.lineTo(l.x, l.y);
  }
  function bodyPath(g, s) {
    g.beginPath();
    const left = s.Ls.slice(0), right = s.Rs.slice(0).reverse();
    smoothPoly(g, left, true);
    // gathered top edge: dips between the two ears
    const tc = add(s.top, mul(nrm(sub(s.p[NSEG - 1], s.top)), -s.h * 0.02));
    const dip = add(mix(s.cornerL, s.cornerR, 0.5), mul(nrm(sub(s.p[NSEG - 1], s.top)), s.h * 0.05));
    g.quadraticCurveTo(dip.x, dip.y, s.cornerR.x, s.cornerR.y);
    smoothPoly(g, right, false);
    g.closePath();
  }
  function earShape(g, ch, wr) {
    const { P, E, tip } = ch;
    const d1 = nrm(sub(E, P)), d2 = nrm(sub(tip, E)), dm = nrm(add(d1, d2));
    const n1 = V2(-d1.y, d1.x), nm = V2(-dm.y, dm.x), n2 = V2(-d2.y, d2.x);
    const we = wr * 0.62, wt = wr * 0.72; // narrow forearm, rounded mitten tip
    g.beginPath();
    g.moveTo(P.x + n1.x * wr, P.y + n1.y * wr);
    g.quadraticCurveTo(E.x + nm.x * we * 1.1, E.y + nm.y * we * 1.1, tip.x + n2.x * wt * 0.7 - d2.x * wt, tip.y + n2.y * wt * 0.7 - d2.y * wt);
    g.lineTo(tip.x + n2.x * wt, tip.y + n2.y * wt);
    g.arc(tip.x, tip.y, wt, Math.atan2(n2.y, n2.x), Math.atan2(n2.y, n2.x) - Math.PI, true);
    g.lineTo(tip.x - n2.x * wt * 0.7 - d2.x * wt, tip.y - n2.y * wt * 0.7 - d2.y * wt);
    g.quadraticCurveTo(E.x - nm.x * we * 1.1, E.y - nm.y * we * 1.1, P.x - n1.x * wr, P.y - n1.y * wr);
    g.closePath();
  }
  let K_ = null, CUR = null;
  const tagsOf = id => (CUR && CUR[id]) || [];
  const has = (id, tag) => tagsOf(id).indexOf(tag) >= 0;
  const fillOf = id => {
    const f = K_.CAST[id].fill;
    if (!has(id, 'greyed')) return f;
    const n = parseInt(f.slice(1), 16), r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255, m = (r + g + b) / 3 * 0.8;
    return '#' + [r, g, b].map(v => (Math.round(v * 0.35 + m * 0.65) | 0).toString(16).padStart(2, '0')).join('');
  };
  const earW = s => cl(10, 21, s.w * 0.1) * (s.id === 'I' ? 0.8 : 1);

  function drawSack(g, s, ears, lit) {
    const c = { fill: fillOf(s.id) };
    const wr = earW(s);
    // ears behind body edge (root hidden by body), then body, then attributes
    for (const e of ears) if (e.behind) { earShape(g, e.ch, wr); g.fillStyle = c.fill; g.fill(); g.strokeStyle = OUT; g.lineWidth = 3; g.stroke(); }
    bodyPath(g, s);
    const gr = g.createLinearGradient(s.top.x - s.w * 0.6 * lit, 0, s.top.x + s.w * 0.6 * lit, 0);
    gr.addColorStop(0, shade(c.fill, 0.72)); gr.addColorStop(0.55, c.fill); gr.addColorStop(1, shade(c.fill, 1.06));
    g.fillStyle = gr; g.fill();
    g.save(); bodyPath(g, s); g.clip();
    // flour weight sinks to the bottom: darker, fuller base
    const vg = g.createLinearGradient(0, s.top.y, 0, FLOOR);
    vg.addColorStop(0, 'rgba(255,250,235,0.10)'); vg.addColorStop(0.7, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(40,25,10,0.28)');
    g.fillStyle = vg; g.fillRect(s.top.x - s.w * 2, s.top.y - 40, s.w * 4, FLOOR - s.top.y + 60);
    // seams along the IK chain, stitched at every joint
    g.strokeStyle = 'rgba(80,60,35,0.32)'; g.lineWidth = 2;
    for (const f of [0.28, 0.72]) {
      const pts = s.p.map((q, i) => mix(s.Ls[i], s.Rs[i], f));
      g.beginPath(); smoothPoly(g, pts.slice(1), true); g.stroke();
      for (let i = 1; i < NSEG; i++) { const q = pts[i]; g.beginPath(); g.moveTo(q.x - 5, q.y - 2); g.lineTo(q.x + 5, q.y + 2); g.stroke(); }
    }
    // identity attributes, carried by the chain frames
    if (s.id === 'R') band(g, s, 0.8, 1.02, '#6e3a33', true);
    if (s.id === 'B') { band(g, s, 0.37, 0.44, '#2a2622', false); wheat(g, s); }
    carriedInside(g, s);
    g.restore();
    bodyPath(g, s); g.strokeStyle = OUT; g.lineWidth = 3.5; g.stroke();
    if (s.id === 'O') wig(g, s);
    carriedOutside(g, s);
    for (const e of ears) if (!e.behind) {
      earShape(g, e.ch, wr); g.fillStyle = shade(c.fill, 0.9); g.fill(); g.strokeStyle = OUT; g.lineWidth = 3; g.stroke();
    }
    if (has(s.id, 'coins') && ears.length) coinsAt(g, ears[0].ch.tip);
  }
  // ---- carried damage, drawn in the chain's own frames (edge points at height u) ----
  const across = (s, u, f) => mix(edgeAt(s.Ls, u), edgeAt(s.Rs, u), f);
  function carriedInside(g, s) {
    const id = s.id;
    if (has(id, 'blot')) { const q = across(s, 0.5, 0.62); g.fillStyle = 'rgba(20,20,40,0.85)'; g.beginPath(); g.ellipse(q.x, q.y, s.w * 0.09, s.w * 0.07, 0.4, 0, 7); g.fill(); g.beginPath(); g.arc(q.x + s.w * 0.1, q.y + 8, 4, 0, 7); g.fill(); }
    if (has(id, 'torn')) { // torn seam on the side, flour showing
      g.strokeStyle = OUT; g.lineWidth = 2.5; g.fillStyle = '#fbf7ee'; g.beginPath();
      for (let k = 0; k <= 6; k++) { const q = across(s, 0.25 + k * 0.05, k % 2 ? 0.1 : 0.17); k ? g.lineTo(q.x, q.y) : g.moveTo(q.x, q.y); }
      g.closePath(); g.fill(); g.stroke();
    }
    if (has(id, 'gag')) band(g, s, 0.8, 0.88, '#8f8778', false, true);
  }
  function carriedOutside(g, s) {
    const id = s.id;
    const cord = (u) => { // a rope is a taut constraint between the two edge points at height u
      const a = add(edgeAt(s.Ls, u), V2(-3, 0)), b = add(edgeAt(s.Rs, u), V2(3, 0));
      g.strokeStyle = '#8a6a3c'; g.lineWidth = 6; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
      g.strokeStyle = '#4a3418'; g.lineWidth = 1.5; for (let k = 1; k < 10; k++) { const q = mix(a, b, k / 10); g.beginPath(); g.moveTo(q.x - 3, q.y - 3); g.lineTo(q.x + 3, q.y + 3); g.stroke(); }
      return b;
    };
    if (has(id, 'rope')) {
      cord(0.3); const k = cord(0.62);
      const tail = twoBone(k, V2(k.x + 10, k.y + s.h * 0.3), s.h * 0.12, s.h * 0.12, V2(1, 0)); // the loose end hangs as a chain
      g.strokeStyle = '#8a6a3c'; g.lineWidth = 5; g.beginPath(); g.moveTo(k.x, k.y); g.lineTo(tail.E.x, tail.E.y); g.lineTo(tail.tip.x, tail.tip.y); g.stroke();
      g.fillStyle = '#6b4f28'; g.beginPath(); g.arc(k.x, k.y, 7, 0, 7); g.fill();
    }
    if (has(id, 'cinched')) { const a = edgeAt(s.Ls, 0.84), b = edgeAt(s.Rs, 0.84); g.strokeStyle = '#5a4022'; g.lineWidth = 4; g.beginPath(); g.moveTo(a.x - 2, a.y); g.lineTo(b.x + 2, b.y); g.stroke(); }
    if (has(id, 'tag')) {
      const pin = across(s, 0.72, 0.35), q = add(pin, V2(-8, 22));
      g.strokeStyle = '#ddd'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(pin.x, pin.y); g.lineTo(q.x + 14, q.y); g.stroke();
      g.save(); g.translate(q.x, q.y); g.rotate(-0.15); g.fillStyle = '#efe6cf'; g.fillRect(0, 0, 30, 20); g.strokeStyle = '#7a6a50'; g.strokeRect(0, 0, 30, 20); g.restore();
      g.fillStyle = '#c33'; g.beginPath(); g.arc(pin.x, pin.y, 3, 0, 7); g.fill();
    }
  }
  function coinsAt(g, p) {
    for (let k = 0; k < 3; k++) { g.fillStyle = '#d9b44a'; g.strokeStyle = '#7a5a14'; g.lineWidth = 1.5; g.beginPath(); g.ellipse(p.x + k * 3, p.y - 10 - k * 5, 9, 4, 0, 0, 7); g.fill(); g.stroke(); }
  }
  function shade(hex, k) {
    const n = parseInt(hex.slice(1), 16);
    const r = cl(0, 255, ((n >> 16) & 255) * k) | 0, gg = cl(0, 255, ((n >> 8) & 255) * k) | 0, b = cl(0, 255, (n & 255) * k) | 0;
    return `rgb(${r},${gg},${b})`;
  }
  function band(g, s, u0, u1, col, fringe, plain) {
    g.beginPath();
    const a = [], b = [];
    for (let k = 0; k <= 8; k++) { const u = u0 + (Math.min(1, u1) - u0) * k / 8; a.push(edgeAt(s.Ls, Math.min(1, u))); b.push(edgeAt(s.Rs, Math.min(1, u))); }
    const ext = u1 > 1 ? 30 : 0;
    g.moveTo(a[0].x - 20, a[0].y); a.forEach(q => g.lineTo(q.x - 20, q.y));
    if (ext) { g.lineTo(s.cornerL.x - 20, s.cornerL.y - ext); g.lineTo(s.cornerR.x + 20, s.cornerR.y - ext); }
    b.slice().reverse().forEach(q => g.lineTo(q.x + 20, q.y)); g.closePath();
    g.fillStyle = col; g.fill();
    if (fringe) {
      g.strokeStyle = 'rgba(40,15,12,0.8)'; g.lineWidth = 2;
      for (let k = 1; k < 12; k++) { const q = mix(a[0], b[0], k / 12); g.beginPath(); g.moveTo(q.x, q.y); g.lineTo(q.x + 1, q.y + 9); g.stroke(); }
    } else if (!plain) { // buckle
      const q = mix(mix(a[4], b[4], 0.5), mix(a[4], b[4], 0.5), 0); g.strokeStyle = '#a08a5a'; g.lineWidth = 3; g.strokeRect(q.x - 10, q.y - 9, 20, 18);
    }
  }
  function wheat(g, s) {
    const cL = edgeAt(s.Ls, 0.64), cR = edgeAt(s.Rs, 0.64), c = mix(cL, cR, 0.5), r = s.w * 0.17;
    const up = nrm(sub(edgeAt(s.Ls, 0.8), edgeAt(s.Ls, 0.5)));
    g.strokeStyle = 'rgba(120,80,35,0.6)'; g.lineWidth = 3;
    g.beginPath(); g.arc(c.x, c.y, r, 0, Math.PI * 2); g.stroke();
    const a = add(c, mul(up, -r * 0.75)), b = add(c, mul(up, r * 0.8));
    g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
    const nn = V2(-up.y, up.x);
    for (let k = 0; k < 4; k++) {
      const q = mix(c, b, 0.1 + k * 0.22);
      for (const sd of [-1, 1]) { const e = add(q, add(mul(nn, sd * r * 0.28), mul(up, r * 0.14))); g.beginPath(); g.ellipse((q.x + e.x) / 2, (q.y + e.y) / 2, r * 0.16, r * 0.07, Math.atan2(e.y - q.y, e.x - q.x), 0, Math.PI * 2); g.stroke(); }
    }
  }
  function wig(g, s) {
    if (has('O', 'wig')) { g.save(); g.translate(s.top.x, s.top.y); g.rotate(0.28); g.translate(-s.top.x + 16, -s.top.y + 4); }
    const sway = s.sway || 0;
    const tl = s.cornerL, tr = s.cornerR, up = nrm(sub(s.top, s.p[NSEG - 2]));
    const crown = add(s.top, mul(up, s.h * 0.1));
    const hl = add(edgeAt(s.Ls, 0.38), V2(-10 + sway, 0)), hr = add(edgeAt(s.Rs, 0.38), V2(10 + sway, 0));
    g.beginPath();
    g.moveTo(hl.x, hl.y);
    const ml = add(edgeAt(s.Ls, 0.72), V2(-14 + sway * 0.5, 0)), mr = add(edgeAt(s.Rs, 0.72), V2(14 + sway * 0.5, 0));
    g.quadraticCurveTo(ml.x, ml.y, tl.x - 10, tl.y - 4);
    g.quadraticCurveTo(crown.x - s.w * 0.4, crown.y, crown.x, crown.y);
    g.quadraticCurveTo(crown.x + s.w * 0.4, crown.y, tr.x + 10, tr.y - 4);
    g.quadraticCurveTo(mr.x, mr.y, hr.x, hr.y);
    // inner edge back up, framing the front
    const il = edgeAt(s.Rs, 0.55), ir = edgeAt(s.Rs, 0.86);
    g.quadraticCurveTo(hr.x - 16, hr.y - 50, mix(tr, s.top, 0.35).x, mix(tr, s.top, 0.35).y + 22);
    g.quadraticCurveTo(s.top.x, s.top.y + 6, mix(tl, s.top, 0.35).x, mix(tl, s.top, 0.35).y + 22);
    g.quadraticCurveTo(hl.x + 16, hl.y - 50, hl.x, hl.y);
    g.closePath();
    g.fillStyle = '#7a3b8f'; g.fill(); g.strokeStyle = '#3c1748'; g.lineWidth = 3; g.stroke();
    g.strokeStyle = 'rgba(200,150,220,0.35)'; g.lineWidth = 2;
    for (const f of [-0.25, 0, 0.25]) { g.beginPath(); g.moveTo(crown.x + f * s.w, crown.y + 8); g.quadraticCurveTo(crown.x + f * s.w * 1.6, crown.y + 40, crown.x + f * s.w * 2.2 + sway, crown.y + 90); g.stroke(); }
    if (has('O', 'wig')) g.restore();
  }
  // revolver: origin at grip, barrel along +x
  function revolver(g, x, y, ang) {
    g.save(); g.translate(x, y); g.rotate(ang); g.scale(G, G);
    g.fillStyle = '#3c3e46'; g.strokeStyle = '#08080a'; g.lineWidth = 1.2;
    g.beginPath(); g.moveTo(-3, -8); g.lineTo(-12, 12); g.quadraticCurveTo(-11, 17, -4, 16); g.lineTo(5, -2); g.closePath(); g.fill(); // grip
    g.fillStyle = '#5a4030'; g.beginPath(); g.moveTo(-4, -4); g.lineTo(-10, 11); g.lineTo(-5, 13); g.lineTo(2, -2); g.closePath(); g.fill();
    g.fillStyle = '#5d606b';
    g.fillRect(-2, -13, 16, 10); // frame
    g.beginPath(); g.arc(8, -8, 6.5, 0, Math.PI * 2); g.fill(); // cylinder
    g.fillRect(12, -12, 34, 5); // barrel
    g.fillRect(43, -14, 3, 3); // sight
    g.fillStyle = '#1d1c1f'; g.beginPath(); g.moveTo(-3, -13); g.lineTo(-7, -17); g.lineTo(-1, -14); g.fill(); // hammer
    g.strokeStyle = '#2a292e'; g.lineWidth = 1.5; g.beginPath(); g.arc(6, -1, 4, 0.2, Math.PI - 0.2); g.stroke(); // guard
    g.strokeStyle = 'rgba(235,225,205,0.7)'; g.lineWidth = 1; g.beginPath(); g.moveTo(13, -11.5); g.lineTo(45, -11.5); g.stroke();
    g.beginPath(); g.arc(8, -8, 6.5, 3.6, 5.6); g.stroke();
    g.strokeStyle = 'rgba(240,228,205,0.55)'; g.lineWidth = 0.8;
    g.beginPath(); g.moveTo(-3, -13); g.lineTo(46, -13); g.lineTo(46, -7); g.lineTo(14, -7); g.moveTo(-12, 12); g.quadraticCurveTo(-11, 17, -4, 16); g.lineTo(5, -2); g.stroke();
    g.restore();
  }
  const muzzleOf = (x, y, ang) => V2(x + Math.cos(ang) * 46 * G - Math.sin(ang) * -9.5 * G, y + Math.sin(ang) * 46 * G + Math.cos(ang) * -9.5 * G);

  // ---------- performances ----------
  // victim plans: how each sack backs away to the wall (contact plane at WALL)
  const VP = {
    R: { t0: 2.75, t1: 4.55, n: 3, lift: 6, upDelay: 0.08, k: 5, w: 9, upH: 0.5, spread: 0.5, rock: 7, impact: 0.5 },
    B: { t0: 2.6, t1: 4.2, n: 2, lift: 15, upDelay: 0.0, k: 6, w: 12, upH: 0.62, spread: 0.42, rock: 0, impact: 1.6 },
    I: { t0: 2.95, t1: 4.6, n: 1, lift: 0, slide: true, upDelay: 0.22, k: 2.6, w: 5, upH: 0.42, spread: 0.55, rock: 0, impact: 0.4 },
    O: { t0: 2.55, t1: 3.95, n: 4, lift: 9, crisp: true, upDelay: 0.03, k: 9, w: 16, upH: 0.64, spread: 0.34, rock: 0, impact: 0.8 }
  };
  // doer plans: reach for the revolver, raise, aim, advance
  const DP = {
    R: { reach: [0.5, 1.3], aim: [1.45, 2.3], hold: 0.8, adv: { t0: 2.9, t1: 4.75, n: 3, lift: 5 }, cap: 210, thrust: 10, pole: V2(0, -1) },
    B: { reach: [0.4, 0.95], aim: [2.1, 2.36], hold: 0.86, adv: { t0: 2.8, t1: 4.45, n: 2, lift: 18 }, cap: 300, thrust: 34, pole: V2(0, -1) },
    I: { reach: [0.55, 1.3], aim: [1.95, 2.35], hold: 0.7, adv: { t0: 3.0, t1: 4.5, n: 1, lift: 0, slide: true }, cap: 100, thrust: 6, pole: V2(0, 1) },
    O: { reach: [0.95, 1.3], aim: [1.4, 2.0], hold: 0.99, adv: { t0: 2.85, t1: 4.35, n: 3, lift: 10, crisp: true }, cap: 290, thrust: 16, pole: V2(0, -1) }
  };

  // idle: ears hang at the sides like resting arms (Inigo's hang long and close, like hair)
  function idleEarTarget(id, corner, side, Le, t, ph) {
    const ang = Math.min(3.05, { R: 2.55, B: 2.6, I: 2.75, O: 2.85 }[id] + (has(id, 'drowsy') ? 0.3 : 0)) + 0.03 * Math.sin(t * 2 + ph);
    const r = { R: 0.9, B: 0.9, I: 0.97, O: 0.92 }[id];
    return floorClamp(add(corner, V2(side * Math.sin(ang) * Le * r, -Math.cos(ang) * Le * r)));
  }
  const floorClamp = T => V2(T.x, Math.min(T.y, FLOOR - 8));
  // interpolate a target in polar form about the ear root so the chain swings, never folds
  function swing(root, A, B, u) {
    const a = sub(A, root), b = sub(B, root);
    const ra = len(a), rb = len(b), aa = Math.atan2(a.y, a.x);
    let ab = Math.atan2(b.y, b.x), dd = ab - aa;
    while (dd > Math.PI) dd -= 2 * Math.PI; while (dd < -Math.PI) dd += 2 * Math.PI;
    const r = ra + (rb - ra) * u, an = aa + dd * u;
    return add(root, V2(Math.cos(an) * r, Math.sin(an) * r));
  }
  const earPoleIdle = (id, side) => V2(side, 0.3);

  function victimPose(id, t) {
    const c = K_.CAST[id], w = c.w * S, h = c.h * S, P = VP[id], Le = EARL[id] * S;
    const x0 = 1300, xf = WALL - w / 2 - 4;
    const feet = feetAt(t, x0, w, P, xf - x0);
    const imp = P.t1 + 0.02;
    const hit = ring(t - imp, 3.2, 14);
    // attention: lean back before the aim lands, jolt at contact, rock while backing
    let lean = -0 + 10 * sm(1.5, 2.3, t) + 14 * ring(t - CONTACT - P.upDelay, 4, 9) + P.rock * Math.sin((t - P.t0) * 7) * sm(P.t0, P.t0 + 0.2, t) * (1 - sm(P.t1 - 0.2, P.t1, t));
    lean -= hit * 14 * P.impact; // the wall pushes back
    const mid = (feet.L.x + feet.R.x) / 2;
    lean = Math.min(lean, WALL - w / 2 - mid - 2); // top cannot pass the wall plane
    let squash = 1 - 0.008 * Math.sin(t * 2.3 + 1) - 0.05 * Math.abs(hit) * P.impact;
    if (id === 'I') squash -= 0.05 + 0.06 * sm(P.t1, P.t1 + 0.6, t);
    if (id === 'R') squash -= 0.05 * sm(P.t1, P.t1 + 0.5, t); // shrinks against the wall
    const s = solveSack(id, feet, lean, squash, 3);
    const up = rise(t - CONTACT - P.upDelay, P.k, P.w);
    const ears = [-1, 1].map(side => {
      const corner = side < 0 ? s.cornerL : s.cornerR;
      const idle = idleEarTarget(id, corner, side, Le, t, side);
      const hands = add(corner, V2(side * P.spread * Le, -P.upH * Le));
      // trembling stops when frozen against the wall
      const trem = (1 - sm(P.t1 + 0.3, P.t1 + 0.6, t)) * sm(CONTACT, CONTACT + 0.4, t) * 3 * Math.sin(t * 31 + side);
      const T = add(swing(corner, idle, hands, cl(-0.2, 1.25, up)), V2(trem, 0));
      const pole = id === 'I' ? V2(side, 1) : V2(side, 0.7);
      return { ch: twoBone(corner, T, Le * 0.52, Le * 0.48, pole), behind: false };
    });
    s.hit = hit; s.arrive = imp;
    return { s, ears };
  }

  function doerPose(id, t, vic) {
    const c = K_.CAST[id], w = c.w * S, h = c.h * S, P = DP[id], Le = EARL[id] * S;
    const x0 = 700 - w / 2;
    const vFinalLeft = WALL - vic.s.w - 4;
    const need = (vFinalLeft - 170 - Le * 0.9 - 40 * G) - (x0 + w / 2);
    const D = cl(0, P.cap, need);
    const feet = feetAt(t, x0, w, P.adv, D);
    const grip0 = V2(700 + 74, FLOOR - 236); // revolver resting on the wall shelf
    // target on the victim: its top, a little down
    const aimPt = add(vic.s.top, V2(0, vic.s.h * 0.18));
    const thrustP = sm(CONTACT - 0.12, CONTACT, t) * (1 - 0.6 * sm(CONTACT + 0.05, CONTACT + 0.5, t));
    let lean = 0, squash = 1 - 0.01 * Math.sin(t * 2.1);
    if (id === 'R') lean += 6 * Math.sin(t * 2.4) * sm(0.4, 1.0, t);
    if (id === 'B') lean += 30 * thrustP - 10 * sm(1.0, 1.6, t) * (1 - sm(2.0, 2.3, t));
    if (id === 'I') squash -= 0.08;
    if (id === 'O') lean += 4 * thrustP;
    // pass 1: body, then gun-ear target, then counterbalance lean to reach
    let s = solveSack(id, feet, lean, squash, 3);
    const gunTarget = (s) => {
      const corner = s.cornerR;
      const dir = nrm(sub(aimPt, corner));
      let H = add(corner, mul(dir, P.hold * Le));
      if (id === 'I') H = add(H, V2(0, 10 + 6 * Math.sin(t * 3.3)));
      H = add(H, mul(dir, P.thrust * thrustP));
      let ang = Math.atan2(aimPt.y - H.y, aimPt.x - H.x);
      if (id === 'I') ang += 0.09 * Math.sin(t * 4.7);
      if (id === 'R') ang += 0.02 * Math.sin(t * 2.4);
      // phases
      const idle = idleEarTarget(id, corner, 1, Le, t, 1);
      const r = sm(P.reach[0], P.reach[1], t);
      let T, gx, gy, ga, held = t >= P.reach[1];
      if (!held) { T = swing(corner, idle, add(grip0, V2(-2, 4)), r); gx = grip0.x; gy = grip0.y; ga = 0; }
      else {
        if (id === 'B') { // lifts it shyly, pointing at the floor; then set off
          const low = add(corner, V2(Le * 0.55, Le * 0.45));
          const T1 = mix(grip0, low, sm(P.reach[1], 1.6, t));
          T = mix(T1, H, sm(P.aim[0], P.aim[1], t));
          const a1 = 1.0 * sm(P.reach[1], 1.6, t);
          ga = a1 + (ang - a1) * sm(P.aim[0], P.aim[1], t);
        } else if (id === 'I') { // dangles it, twirls it, then points it lazily
          const dang = add(corner, V2(Le * 0.35, Le * 0.25));
          const T1 = mix(grip0, dang, sm(P.reach[1], 1.55, t));
          T = mix(T1, H, sm(P.aim[0], P.aim[1], t));
          const a1 = 1.45 * sm(P.reach[1], 1.45, t) + 2 * Math.PI * sm(1.45, 1.9, t);
          ga = a1 + (ang + 2 * Math.PI - a1) * sm(P.aim[0], P.aim[1], t);
        } else {
          const u = sm(P.reach[1], P.aim[1], t);
          T = mix(grip0, H, u); ga = ang * sm(P.reach[1] + 0.05, P.aim[1], t);
          if (id === 'R') T = add(T, V2(0, -18 * Math.sin(Math.PI * u))); // deliberate arc up and over
        }
        gx = T.x; gy = T.y;
      }
      return { T, gx, gy, ga, held, corner };
    };
    let gt = gunTarget(s);
    const ex = len(sub(gt.T, gt.corner)) - 0.96 * Le;
    if (ex > 0) { // counterbalance: the whole chain leans toward the reach
      const d = nrm(sub(gt.T, gt.corner));
      s = solveSack(id, feet, lean + d.x * ex * 1.1, squash - Math.max(0, d.y) * ex / h * 1.1 + Math.max(0, -d.y) * ex / h * 0.3, 3);
      gt = gunTarget(s);
    }
    const gunEar = twoBone(s.cornerR, gt.T, Le * 0.52, Le * 0.48, P.pole);
    if (gt.held) { gt.gx = gunEar.tip.x; gt.gy = gunEar.tip.y; }
    // free ear: counterbalances the reach (swings back/out), Ogiva touches her wig first
    const ext = cl(0, 1, (gunEar.tip.x - s.cornerR.x) / Le);
    let fT = idleEarTarget(id, s.cornerL, -1, Le, t, -1);
    if (id !== 'I') fT = floorClamp(swing(s.cornerL, fT, add(s.cornerL, V2(-Le * 0.7, -Le * 0.45)), ext * 0.6));
    if (id === 'O') {
      const wt = add(mix(s.cornerL, s.top, 0.6), V2(0, -s.h * 0.08));
      fT = mix(fT, wt, sm(0.4, 0.6, t) * (1 - sm(0.75, 0.95, t)));
    }
    const freeEar = twoBone(s.cornerL, fT, Le * 0.52, Le * 0.48, earPoleIdle(id, -1));
    if (id === 'O') { const lt = DP.O; s.sway = 10 * ring(t - 0.95, 3, 8) - 14 * ring(t - CONTACT + 0.1, 3, 9) - 8 * Math.sin(Math.PI * sm(lt.adv.t0, lt.adv.t1, t) * 6) * sm(lt.adv.t0, lt.adv.t0 + 0.2, t) * (1 - sm(lt.adv.t1 - 0.2, lt.adv.t1, t)); }
    return { s, ears: [{ ch: freeEar, behind: false }, { ch: gunEar, behind: false }], gun: gt, aimPt, grip0 };
  }

  // ---------- world ----------
  function room(g, t, A, V, vic, d) {
    const W = 1920, H = 1080;
    g.fillStyle = '#231c18'; g.fillRect(0, 0, W, H);
    // back wall paper
    const wg = g.createLinearGradient(0, 0, 0, WALLBASE);
    wg.addColorStop(0, '#1a1513'); wg.addColorStop(1, '#3a2e25');
    g.fillStyle = wg; g.fillRect(0, 0, WALL, WALLBASE);
    for (let i = 0; i < 44; i++) { const x = i * 40 + 6; g.fillStyle = i % 2 ? 'rgba(255,230,190,0.025)' : 'rgba(0,0,0,0.05)'; g.fillRect(x, 0, 18, WALLBASE); }
    // wainscot
    g.fillStyle = '#251c16'; g.fillRect(0, 640, WALL, WALLBASE - 640);
    g.fillStyle = '#4a3a2c'; g.fillRect(0, 634, WALL, 8);
    for (let x = 30; x < WALL; x += 180) { g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 2; g.strokeRect(x, 662, 150, 140); }
    // side wall (the contact plane)
    g.fillStyle = '#17120f'; g.beginPath(); g.moveTo(WALL, 0); g.lineTo(W, 0); g.lineTo(W, H); g.lineTo(WALL, FLOOR + 4); g.lineTo(WALL, 0); g.fill();
    g.strokeStyle = '#4a3a2c'; g.lineWidth = 3; g.beginPath(); g.moveTo(WALL, 0); g.lineTo(WALL, FLOOR + 4); g.stroke();
    g.fillStyle = '#211a15'; g.beginPath(); g.moveTo(WALL, 640); g.lineTo(W, 610); g.lineTo(W, 980); g.lineTo(WALL, FLOOR + 4); g.fill();
    // floor
    const fg = g.createLinearGradient(0, WALLBASE, 0, H);
    fg.addColorStop(0, '#3b2c21'); fg.addColorStop(1, '#1c140f');
    g.fillStyle = fg; g.beginPath(); g.moveTo(0, WALLBASE); g.lineTo(WALL, WALLBASE); g.lineTo(WALL, FLOOR + 4); g.lineTo(W, H); g.lineTo(0, H); g.fill();
    g.strokeStyle = 'rgba(0,0,0,0.3)'; g.lineWidth = 2;
    for (const y of [850, 905, 975, 1060]) { g.beginPath(); g.moveTo(0, y); g.lineTo(Math.min(W, WALL + (y - FLOOR) * 2.8), y); g.stroke(); }
    g.fillStyle = '#4a3a2c'; g.fillRect(0, WALLBASE - 6, WALL, 6);
    // picture on the back wall by the corner: shakes when the victim hits the wall
    const tilt = 0.05 + vic.s.hit * 0.09 * VP[V].impact;
    g.save(); g.translate(1560, 300); g.rotate(tilt);
    g.strokeStyle = '#6b5236'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(0, -60); g.lineTo(-40, -10); g.moveTo(0, -60); g.lineTo(40, -10); g.stroke();
    g.fillStyle = '#5b4430'; g.fillRect(-58, -10, 116, 140); g.fillStyle = '#2b3330'; g.fillRect(-46, 2, 92, 116);
    g.fillStyle = '#44504a'; g.beginPath(); g.moveTo(-46, 118); g.lineTo(-10, 60); g.lineTo(20, 90); g.lineTo(46, 50); g.lineTo(46, 118); g.fill();
    g.restore();
    // lamp on a table, far left, and its pool
    const lx = 170, ly = 560;
    const glow = g.createRadialGradient(lx, ly, 10, lx, ly, 900);
    glow.addColorStop(0, 'rgba(255,200,120,0.32)'); glow.addColorStop(0.35, 'rgba(255,170,90,0.10)'); glow.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = glow; g.fillRect(0, 0, W, H);
    g.fillStyle = '#2b211a'; g.fillRect(100, 690, 140, 14); g.fillRect(112, 704, 10, 176); g.fillRect(218, 704, 10, 176);
    g.fillStyle = '#5c4630'; g.fillRect(160, 600, 20, 90);
    g.fillStyle = '#f3c983'; g.beginPath(); g.moveTo(120, 600); g.lineTo(220, 600); g.lineTo(195, 535); g.lineTo(145, 535); g.closePath(); g.fill();
    // shelf on the back wall where the revolver waits
    g.fillStyle = '#5a4532'; g.fillRect(d.grip0.x - 70, FLOOR - 236 + 16 * G + 2, 150, 10);
    g.fillStyle = '#3c2e22'; g.beginPath(); g.moveTo(d.grip0.x - 50, FLOOR - 236 + 16 * G + 12); g.lineTo(d.grip0.x - 50, FLOOR - 236 + 16 * G + 50); g.lineTo(d.grip0.x - 20, FLOOR - 236 + 16 * G + 12); g.fill();
    g.beginPath(); g.moveTo(d.grip0.x + 50, FLOOR - 236 + 16 * G + 12); g.lineTo(d.grip0.x + 50, FLOOR - 236 + 16 * G + 50); g.lineTo(d.grip0.x + 20, FLOOR - 236 + 16 * G + 12); g.fill();
  }
  // shadows thrown up the back wall from the lamp
  function wallShadow(g, pose, gun) {
    const L = V2(170, 560), k = 1.22;
    g.save();
    g.beginPath(); g.rect(0, 0, WALL, WALLBASE); g.clip();
    g.translate(L.x, L.y); g.scale(k, k); g.translate(-L.x, -L.y); g.translate(40, -30);
    g.fillStyle = 'rgba(5,3,2,0.22)';
    bodyPath(g, pose.s); g.fill();
    const wr = earW(pose.s);
    for (const e of pose.ears) { earShape(g, e.ch, wr); g.fill(); }
    if (gun) { g.globalAlpha = 0.9; revolverShadow(g, gun); }
    g.restore();
  }
  function revolverShadow(g, gun) {
    g.save(); g.translate(gun.gx, gun.gy); g.rotate(gun.ga); g.scale(G, G);
    g.fillStyle = 'rgba(5,3,2,0.3)';
    g.beginPath(); g.moveTo(-3, -8); g.lineTo(-12, 12); g.lineTo(-4, 16); g.lineTo(5, -2); g.closePath(); g.fill();
    g.fillRect(-2, -13, 16, 10); g.beginPath(); g.arc(8, -8, 6.5, 0, 7); g.fill(); g.fillRect(12, -12, 34, 5);
    g.restore();
  }
  function contactMarks(g, s) {
    // planted-foot locks read as pressed shadow wedges; a swinging foot leaves none
    for (const [f, lock] of [[s.feet.L, s.feet.lockL], [s.feet.R, s.feet.lockR]]) {
      const a = lock ? 0.55 : 0.18;
      g.fillStyle = `rgba(0,0,0,${a})`; g.beginPath(); g.ellipse(f.x, FLOOR + 3, 26, 6, 0, 0, Math.PI * 2); g.fill();
    }
    g.fillStyle = 'rgba(0,0,0,0.35)'; g.beginPath();
    g.ellipse((s.feet.L.x + s.feet.R.x) / 2, FLOOR + 4, s.w * 0.62, 11, 0, 0, Math.PI * 2); g.fill();
  }

  function doerAdvance(A, V) {
    const w = K_.CAST[A].w * S, Le = EARL[A] * S, wv = K_.CAST[V].w * S;
    const x0 = 700 - w / 2, vFinalLeft = WALL - wv - 4;
    return cl(0, DP[A].cap, (vFinalLeft - 170 - Le * 0.9 - 40 * G) - (x0 + w / 2));
  }
  // the times a swinging foot re-plants (same schedule as feetAt)
  function stepEvents(plan, cx, w, D) {
    if (plan.slide) return [];
    const n = Math.max(plan.n, Math.ceil(Math.abs(D) / (w * 0.4))), half = n * 2, dt = (plan.t1 - plan.t0) / half;
    const ev = [], lead = D >= 0 ? 1 : -1;
    for (let k = 0; k < half; k++) {
      const a = plan.t0 + k * dt, side = k % 2 === 0 ? lead : -lead;
      ev.push({ t: a + dt * (plan.crisp ? 0.7 : 1), x: cx + side * w / 2 + D * (Math.floor(k / 2) + 1) / n });
    }
    return ev;
  }

  DEED({
    n: 6, key: 'gun', title: 'Threatening with a Gun',
    scion: 33, lineage: 'Inverse Kinematics — Contact and Reach Swarm',
    op: 'The doer\'s ear chain is solved to a revolver on a shelf, grips it, and is re-targeted to the victim\'s head; the victim\'s ear chains are re-targeted above its head and its planted feet step back until its body meets the wall plane and locks.',
    made: 'Each sack is a six-segment spine chain rooted on two floor contacts, skinned with a width profile and stitched at every joint; its two ears are two-bone chains with poles. The room is a lamp-lit boarding-house corner whose side wall is a contact plane, with a shelf, a picture and wall shadows.',
    moved: 'Every pose is solved from world-space targets: FABRIK for the spine, analytic two-bone IK for the ears, alternating planted-foot locks for steps, and a counterbalance lean whenever a reach exceeds the ear length. The revolver changes state at the grip contact and the victim\'s wall contact clamps its lean and rings the picture.',
    contact: CONTACT,
    leaves: { A: [], V: [] },
    draw(g, t, A, V, K, opt) {
      K_ = K; opt = opt || {}; CUR = opt.carry || null;
      const L = opt.layer;
      const vic = victimPose(V, t);
      const d = doerPose(A, t, vic);
      if (!L || L === 'bg') {
        room(g, t, A, V, vic, d);
        const vg = g.createRadialGradient(960, 560, 500, 960, 560, 1250);
        vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.55)');
        g.fillStyle = vg; g.fillRect(0, 0, 1920, 1080);
      }
      if (!L || L === 'V') {
        wallShadow(g, vic, null); contactMarks(g, vic.s);
        drawSack(g, vic.s, vic.ears, 1);
      }
      if (!L || L === 'A') {
        wallShadow(g, d, d.gun); contactMarks(g, d.s);
        if (!d.gun.held) revolver(g, d.grip0.x, d.grip0.y, 0); // on the shelf until the grip contact
        drawSack(g, d.s, [d.ears[0]], 1);
        if (d.gun.held) { // line of aim (the IK target vector); never a shot
          const m = muzzleOf(d.gun.gx, d.gun.gy, d.gun.ga);
          const a = 0.22 * sm(CONTACT - 0.1, CONTACT + 0.2, t);
          if (a > 0.01) {
            g.save(); g.setLineDash([4, 14]); g.strokeStyle = `rgba(255,220,160,${a})`; g.lineWidth = 2;
            g.beginPath(); g.moveTo(m.x, m.y); g.lineTo(d.aimPt.x, d.aimPt.y); g.stroke(); g.restore();
          }
          revolver(g, d.gun.gx, d.gun.gy, d.gun.ga);
        }
        const wr = earW(d.s); // gun ear over the grip so the ear tip wraps it
        earShape(g, d.ears[1].ch, wr); g.fillStyle = shade(fillOf(A), 0.9); g.fill(); g.strokeStyle = OUT; g.lineWidth = 3; g.stroke();
      }
    },
    marks(t, A, V, K, opt) {
      K_ = K; CUR = (opt && opt.carry) || null;
      const vic = victimPose(V, t), d = doerPose(A, t, vic);
      const box = s => {
        const pts = s.Ls.concat(s.Rs);
        let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
        for (const q of pts) { x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.x); y1 = Math.max(y1, q.y); }
        y1 = Math.max(y1, FLOOR);
        return { x: Math.round(x0), y: Math.round(y0), w: Math.round(x1 - x0), h: Math.round(y1 - y0) };
      };
      return { A: box(d.s), V: box(vic.s) };
    },
    sound(ac, out, t0, A, V, K) {
      K_ = K; const SN = K.SND, H = K.hash;
      const pan = x => cl(-1, 1, x / 960 - 1);
      const mf = m => 440 * Math.pow(2, (m - 69) / 12);
      const vP = VP[V], dP = DP[A];
      const wV = K.CAST[V].w * S, wA = K.CAST[A].w * S, LeA = EARL[A] * S;
      const xV0 = 1300, DV = (WALL - wV / 2 - 4) - xV0;
      const xA0 = 700 - wA / 2, DA = doerAdvance(A, V);
      const at = (u, f, ...r) => { if (u >= 0) f(t0 + u, ...r); };
      // idle breath, both sacks
      at(0.02, w => SN.say(ac, out, A, w, 'breathe', 1.1, pan(xA0)));
      at(0.05, w => SN.say(ac, out, V, w, 'breathe', 1.1, pan(xV0)));
      // Ogiva touches her wig: a brush of cloth grains
      if (A === 'O') SN.cloud(ac, out, t0 + 0.42, 0.4, 70, { bp: 5000, a: 0.03, d: [0.01, 0.03], spread: 0.1 }, u => Math.sin(Math.PI * u));
      // reach: the ear chain travels (soft cloth), then locks on the grip (constraint tick + metal)
      SN.cloud(ac, out, t0 + dP.reach[0], dP.reach[1] - dP.reach[0], 40, { bp: K.SND.VOICE[A].bp * 1.5, a: 0.02, d: [0.02, 0.06], spread: 0.15 }, u => Math.sin(Math.PI * u));
      at(dP.reach[1], w => { SN.say(ac, out, A, w, 'tick', 1.3, pan(774)); SN.grain(ac, out, w + 0.01, { bp: 3200, q: 6, d: 0.03, a: 0.22, pan: pan(774), att: 0.1 }); });
      SN.cloud(ac, out, t0 + dP.reach[1] + 0.02, 0.14, 120, { bp: 2600, q: 3, a: 0.03, d: [0.005, 0.015], spread: 0.1 }, u => 1 - u); // lifted off the shelf
      if (A === 'I') SN.cloud(ac, out, t0 + 1.45, 0.45, 90, { bp: 3400, q: 4, a: 0.04, d: [0.006, 0.02], spread: 0.3 }, u => Math.sin(Math.PI * u)); // the twirl
      if (A === 'B') { at(dP.aim[0], w => SN.say(ac, out, 'B', w, 'land', 0.6, pan(700))); } // set off
      // residual sonified: grains spread in pitch while the aim chain is still solving, converge to unison at contact
      const aim0 = A === 'B' ? 1.6 : dP.reach[1] + 0.1, base = K.SND.VOICE[A].base + 24;
      for (let k = 0; k < 70; k++) {
        const u = H(k * 3.17 + 11), tt = aim0 + (CONTACT - aim0) * u;
        const dev = (H(k * 7.7) - 0.5) * 2 * 7 * (1 - u);
        SN.grain(ac, out, t0 + tt, { f: mf(base + dev), d: 0.06 + 0.06 * u, a: 0.012 + 0.03 * u, pan: pan(900), type: 'triangle', att: 0.4 });
      }
      // hammer: ratchet just before, the click itself is the contact (never a shot)
      for (let k = 0; k < 4; k++) SN.grain(ac, out, t0 + CONTACT - 0.22 + k * 0.025, { bp: 4200, q: 8, d: 0.008, a: 0.14, pan: pan(950), att: 0.1 });
      SN.grain(ac, out, t0 + CONTACT, { bp: 2600, q: 3, d: 0.02, a: 1.5, pan: pan(950), att: 0.05 });
      SN.grain(ac, out, t0 + CONTACT + 0.004, { f: mf(base), d: 0.05, a: 0.25, pan: pan(950), att: 0.05 });
      SN.thump(ac, out, t0 + CONTACT, 1.05, 70, pan(950));
      // the locked aim holds: a thin unison of grains, fading through the freeze
      SN.cloud(ac, out, t0 + CONTACT + 0.05, 6 - CONTACT - 0.25, 22, { pitches: [base], a: 0.025, d: [0.12, 0.25], spread: 0.2, type: 'triangle' }, u => 1 - u * 0.8);
      // the victim's ears go up
      at(CONTACT + vP.upDelay, w => SN.say(ac, out, V, w, 'react', 1.4, pan(xV0)));
      // footfalls on planted-foot lock events
      for (const e of stepEvents(dP.adv, xA0, wA, DA)) at(e.t, w => SN.say(ac, out, A, w, 'step', 1, pan(e.x)));
      for (const e of stepEvents(vP, xV0, wV, DV)) at(e.t, w => SN.say(ac, out, V, w, 'step', 1, pan(e.x)));
      if (dP.adv.slide) SN.cloud(ac, out, t0 + dP.adv.t0, dP.adv.t1 - dP.adv.t0, 60, { bp: 900, a: 0.03, d: [0.03, 0.08], spread: 0.1 }, u => Math.sin(Math.PI * u));
      if (vP.slide) SN.cloud(ac, out, t0 + vP.t0, vP.t1 - vP.t0, 60, { bp: 900, a: 0.03, d: [0.03, 0.08], spread: 0.1 }, u => Math.sin(Math.PI * u));
      // the wall contact: body lands on the plane, the picture rattles
      const xw = WALL - 20, ti = vP.t1 + 0.02;
      at(ti, w => SN.say(ac, out, V, w, 'land', 0.6 + 0.3 * vP.impact, pan(xw)));
      SN.cloud(ac, out, t0 + ti + 0.03, 0.2 + 0.25 * vP.impact, 70, { bp: 1500, q: 4, a: 0.02 + 0.02 * vP.impact, d: [0.005, 0.02], spread: 0.1 }, u => 1 - u);
      at(5.0, w => SN.say(ac, out, V, w, 'breathe', 0.9, pan(xw)));
    }
  });
})();
