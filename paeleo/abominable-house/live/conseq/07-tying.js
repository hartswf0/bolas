// 07 · Tying and Gagging — CONSEQUENCE · SCION-32 Forward Kinematics, hierarchical body logic.
// Every sack is a joint tree: root (floor pivot) -> four spine bones -> top joint -> two ear chains
// (and, for Ogiva, wig strand chains). World frames are products of parent * local matrices, in order.
// Rope bands and the gag are ATTACHMENTS parented to a spine frame at an arc height; when a band is
// released its parent changes (body -> floor, or body -> an untier's ear tip). The rope's imprint is a
// child of the same frame and never leaves. Stiffness after untying = joint angles that unbend in steps,
// bottom joint first, so the correction propagates up the hierarchy.
// Invariant (numerically testable): bone lengths |J(i+1)-J(i)| equal REST length * view scale every frame.
(function () {
  const FLOOR = 940, Z = 2.25, VX = 1230, AX = 500, DOORX = 1790, DUR = 3.4;
  const WARD = { x0: 1250, x1: 1690, y0: 330 };            // wardrobe against the back wall (hiding place)
  const IDS = ['R', 'B', 'I', 'O'];
  const ROPE = '#b4945a', ROPEd = '#5a4424', INK = '#2b2016', GAGC = '#d9ccb0';
  // ---------- 2D affine matrices [a,b,c,d,e,f], canvas convention ----------
  const mul = (m, n) => [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1], m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3], m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]];
  const T = (x, y) => [1, 0, 0, 1, x, y], Rm = a => [Math.cos(a), Math.sin(a), -Math.sin(a), Math.cos(a), 0, 0], Sm = s => [s, 0, 0, s, 0, 0];
  const ap = (m, p) => [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]];
  const ang = m => Math.atan2(m[1], m[0]);
  const has = (body, id, tg) => !!(body && body[id] && body[id].indexOf(tg) >= 0);

  // ---------- typed skeleton per sack ----------
  const WID = { R: [0.96, 1.04, 1.05, 1.0, 0.93], B: [0.93, 1.07, 1.1, 1.03, 0.9], I: [1.12, 1.07, 0.98, 0.9, 0.84], O: [0.94, 1.0, 1.0, 0.98, 0.95] };
  const FRAC = [0.27, 0.26, 0.25, 0.22];
  function skeleton(K, id, body) {
    const c = K.CAST[id], H = c.h * Z * (has(body, id, 'emptied') ? 0.8 : 1), W = c.w * Z;
    const len = FRAC.map(f => f * H), cum = [0]; len.forEach((l, i) => cum.push(cum[i] + l));
    const earL = id === 'I' ? [H * 0.45, H * 0.42] : [(Math.min(W, H) * 0.17 + 9 * Z) * 0.6, (Math.min(W, H) * 0.17 + 9 * Z) * 0.45];
    return { id, H, W, len, cum, wid: WID[id].map(f => f * W / 2), earL, earW: id === 'I' ? 22 * Z : id === 'B' ? 30 * Z : 20 * Z };
  }
  // pose: {x, y(lift), tilt, pv(pivot offset), bend[3] (joints 1..3), top (joint 4), swell, sc, pinch:[{s,d,sig}], ear:[[a0,a1],[a0,a1]]}
  function fk(sk, P) {
    const fr = [];
    // world <- root: translate to floor point, scale (lever), rotate about pivot
    let M = mul(T(P.x + (P.pv || 0) * P.sc, FLOOR - (P.y || 0)), mul(Sm(P.sc), mul(Rm(P.tilt || 0), T(-(P.pv || 0), 0))));
    fr.push(M);
    const bends = [P.bend[0] || 0, P.bend[1] || 0, P.bend[2] || 0, P.top || 0];
    for (let i = 0; i < 4; i++) { M = mul(M, mul(T(0, -sk.len[i]), Rm(bends[i]))); fr.push(M); }
    const hw = s => { const a = s * sk.H; let j = 0; while (j < 3 && a > sk.cum[j + 1]) j++; const u = (a - sk.cum[j]) / sk.len[j]; let w = sk.wid[j] + (sk.wid[j + 1] - sk.wid[j]) * u; w *= P.swell || 1; let pin = 0; (P.pinch || []).forEach(q => { const d = (a - q.s * sk.H) / (q.sig || 7 * Z); pin += q.d * Math.exp(-d * d); }); return w * (1 - Math.min(0.6, pin)); };
    const at = (s, x) => { const a = Math.max(0, Math.min(sk.H, s * sk.H)); let j = 0; while (j < 3 && a > sk.cum[j + 1]) j++; return ap(fr[j], [x, -(a - sk.cum[j])]); };
    const frameAt = s => { const a = Math.max(0, Math.min(sk.H, s * sk.H)); let j = 0; while (j < 3 && a > sk.cum[j + 1]) j++; return mul(fr[j], T(0, -(a - sk.cum[j]))); };
    const edge = s => { const w = hw(s); return [at(s, -w), at(s, w)]; };
    // outline: right edge bottom->top, top cap, left edge top->bottom, bottom
    const out = [], N = 22;
    for (let k = 0; k <= N; k++) out.push(edge(k / N)[1]);
    const top = fr[4], tw = sk.wid[4] * (P.swell || 1);
    out.push(ap(top, [tw * 0.4, 5 * Z]), ap(top, [0, 7 * Z]), ap(top, [-tw * 0.4, 5 * Z]));
    for (let k = N; k >= 0; k--) out.push(edge(k / N)[0]);
    out.push(ap(fr[0], [-sk.wid[0] * 0.5, 2]), ap(fr[0], [sk.wid[0] * 0.5, 2]));
    // ear chains: child of the top frame at a pivot offset (the top corner)
    const ears = [-1, 1].map((sd, i) => {
      const e = P.ear[i];
      const E0 = mul(top, mul(T(sd * tw, 0), Rm(sd * e[0])));
      const E1 = mul(E0, mul(T(0, -sk.earL[0]), Rm(sd * e[1])));
      return { sd, E0, E1, base: ap(E0, [0, 0]), mid: ap(E1, [0, 0]), tip: ap(E1, [0, -sk.earL[1]]) };
    });
    return { sk, P, fr, hw, at, edge, frameAt, out, ears };
  }
  // bone-length invariant (exposed for the transform test)
  function boneErr(b) { let e = 0; for (let i = 0; i < 4; i++) { const p = ap(b.fr[i], [0, 0]), q = ap(b.fr[i + 1], [0, 0]); e = Math.max(e, Math.abs(Math.hypot(q[0] - p[0], q[1] - p[1]) - b.sk.len[i] * b.P.sc)); } return e; }

  // ---------- reading the ledger: which branch ----------
  function plan(ev, st, K) {
    const A = ev.A, V = ev.V, H = K.hash;
    const thirds = IDS.filter(s => s !== A && s !== V);
    const alive = s => !!st.alive[s];
    const mind = (a, b) => (st.mind[a] && st.mind[a][b]) || { fear: 0, guilt: 0, grudge: 0, desire: 0, debt: 0, pride: 0 };
    const BASE = { R: 0.13, B: 0.3, I: 0.04, O: 0.0 };     // who comes on their own: the landlady for the rent, the giant out of kindness
    let best = null, bs = -1;
    thirds.filter(alive).forEach(c => { const s = BASE[c] + mind(c, V).desire + 0.5 * mind(c, V).debt + 0.6 * mind(c, A).grudge - 0.4 * mind(c, A).fear + 0.02 * H(ev.k * 7 + c.charCodeAt(0)); if (s > bs) { bs = s; best = c; } });
    let witness = null, wf = -1;
    thirds.filter(alive).forEach(c => { const s = mind(c, A).fear + 0.1 + 0.05 * H(c.charCodeAt(0) + ev.k); if (s > wf) { wf = s; witness = c; } });
    const g = mind(A, V).guilt;
    let br;
    if (!alive(V)) br = 'hide';
    else if (!alive(A)) br = 'loose';
    else if (V === 'B' && !has(st.body, 'B', 'drowsy')) br = 'burst';
    else if (g >= 0.45) br = 'return';
    else if (best && bs > 0.15) br = 'rescue';
    else br = 'alone';
    const LV = s => st.levers[s] || { loom: 0, weight: 0, tempo: 0, halo: 0, shadow: 0, shrink: 0, grey: 0 };
    const n = { R: 2, B: 4, I: 3, O: 3 }[A];               // the deed's band count, by who tied
    const fr = []; for (let k = 0; k < n; k++) fr.push(0.16 + 0.46 * (n === 1 ? 0.5 : k / (n - 1)));
    const gagS = V === 'I' ? 0.86 : V === 'R' ? 0.74 : 0.9;
    return { br, A, V, C: br === 'rescue' ? best : br === 'alone' ? witness : null, fr, gagS, LV, g, pride: mind(A, V).pride, fearAC: best ? mind(A, best).fear : 0, vFearA: mind(V, A).fear, vGrudgeA: mind(V, A).grudge };
  }

  // ---------- timelines ----------
  function steps(K, t, t0, n, dt) { // a stiff joint: n small eased steps with holds, total 1
    let s = 0; for (let k = 0; k < n; k++) s += K.sm(t0 + k * dt, t0 + k * dt + dt * 0.45, t) / n; return s;
  }
  function stage(t, ev, st, K) {
    const Pn = plan(ev, st, K), { br, A, V, C } = Pn, sm = K.sm, eo = K.eo, cl = K.cl, lerp = K.lerp, H = K.hash;
    const LA = Pn.LV(A), LVv = Pn.LV(V);
    const body = st.body;
    const skA = skeleton(K, A, body), skV = skeleton(K, V, body), skC = C ? skeleton(K, C, body) : null;
    const sc = L => cl(0.84, 1.18, 1 + 0.12 * L.loom - 0.14 * L.shrink);
    const tempo = L => 1 + 0.3 * cl(-1, 1, L.tempo);
    const earUp = (id, L, extra) => id === 'I' ? [2.78 + 0.05 * L.shrink, 0.12] : [0.7 - 0.9 * L.shrink + (extra || 0), 0.25];
    const drowsy = id => has(body, id, 'drowsy') ? 0.5 : 0;
    const S = { t, Pn, actors: [], bands: [], gag: null, coils: [], ward: 0, door: 0, dawn: 0, lamp: 1, flyers: [] };
    const sAt = sk => sk.W;
    // ---- victim base pose: bound (bones compressed into a stiff zigzag, ears pinned to its sides) ----
    const vsc = sc(LVv);
    const bound = id => id === 'I' ? [0.05, -0.07, 0.06] : id === 'B' ? [0.04, -0.05, 0.04] : [0.05, -0.06, 0.05];
    const pinned = id => id === 'I' ? [2.95, 0.05] : [2.55, 0.35];
    let vP = { x: VX, y: 0, tilt: 0, pv: 0, bend: bound(V), top: -0.03, swell: 1, sc: vsc, pinch: [], ear: [pinned(V), pinned(V)] };
    // bands: attachments at arc heights fr on the victim
    const tight = { R: 0.11, B: 0.15, I: 0.09, O: 0.1 }[A];
    const bands = Pn.fr.map((s, k) => ({ s, k, rel: 9, snap: 9, mode: 'tied' }));
    let gag = { s: Pn.gagS, rel: 9, carrier: null, drop: 9, mode: 'on' };
    let straight = 0, straightT = 9;                    // 0 bound .. 1 free; joint unbending
    let aP = null, cP = null, aAlpha = 1, cAlpha = 1, vAlpha = 1;
    const aX0 = AX, dw = skA.W * sc(LA), vw = skV.W * vsc;
    const reachX = VX - (vw + dw) / 2 - 22;
    const idleA = (x, extraTilt) => ({ x, y: 0, tilt: (extraTilt || 0), pv: 0, bend: [0, 0, 0], top: 0, swell: 1, sc: sc(LA), pinch: [], ear: [earUp(A, LA, drowsy(A)), earUp(A, LA, drowsy(A))] });
    const walk = (P, t, t0, t1, x0, x1, id, L) => { // root motion with a step bob (weight lever)
      const u = sm(t0, t1, t); P.x = lerp(x0, x1, u);
      const moving = t > t0 && t < t1 ? Math.sin(Math.PI * (t - t0) / (t1 - t0)) : 0;
      const rate = id === 'B' ? 5 : id === 'I' ? 9 : id === 'O' ? 10 : 7;
      const bob = Math.abs(Math.sin(Math.PI * rate * (t - t0) / 2));
      P.y += moving * (id === 'I' ? 14 : 6) * bob * (1 - 0.4 * cl(0, 1, L.weight));
      P.tilt += moving * 0.06 * Math.sign(x1 - x0) * (id === 'R' ? Math.sin(t * 14) * 0.6 + 0.4 : 1);
      P.swell *= 1 + 0.04 * cl(0, 1, L.weight + 0.3) * (1 - bob) * moving;
    };
    const aimEar = (b, side, target) => { // set ear base angle so the chain points at target (aim, not IK)
      const e = b.ears[side], th = ang(b.fr[4]); const phi = Math.atan2(target[0] - e.base[0], -(target[1] - e.base[1]));
      return [(phi - th) * e.sd, 0.2];
    };
    const T0 = x => x / tempo(LA);
    // ---------- branches ----------
    if (br === 'rescue' || br === 'return' || br === 'loose') {
      let tArr, tGag, tB0, dB;
      if (br === 'rescue') { tArr = 1.05; tGag = 1.15; tB0 = 1.55; dB = 0.26; }
      else if (br === 'return') { tArr = T0(1.0) + 0.1; tGag = tArr + 0.12; tB0 = tGag + 0.4; dB = 0.26; }
      else { tArr = 0.5; tGag = 0.7; tB0 = 0.95; dB = 0.3; }
      gag.rel = tGag; gag.mode = 'off';
      bands.slice().reverse().forEach((b, j) => { b.rel = tB0 + j * dB; b.mode = 'slide'; });
      straightT = tB0 + bands.length * dB - 0.1; S.straightT = straightT;
      if (br === 'rescue') {
        const cL = Pn.LV(C), csc = sc(cL), cw = skC.W * csc;
        const xC = VX + (vw + cw) * 0.56 + 26;
        S.door = sm(0.0, 0.3, t) * (1 - sm(2.7, 3.1, t));
        cP = { x: DOORX, y: 0, tilt: 0, pv: 0, bend: [0, 0, 0], top: 0, swell: 1, sc: csc, pinch: [], ear: [earUp(C, cL, drowsy(C)), earUp(C, cL, drowsy(C))] };
        walk(cP, t, 0.2, tArr, DOORX + 40, xC, C, cL);
        // reach: lean toward the victim; a small rescuer hops to reach a tall gag (root lift)
        const reach = sm(tArr - 0.1, tGag, t) * (1 - sm(straightT, straightT + 0.4, t));
        const need = Math.max(0, Pn.gagS * skV.H * vsc - skC.H * csc * 0.95);
        const hopping = t > tGag - 0.15 && t < tGag + 0.35 ? Math.sin(Math.PI * (t - tGag + 0.15) / 0.5) : 0;
        cP.y += need * (C === 'I' ? 1.1 : 0.8) * hopping;
        const lean = -(C === 'B' ? 0.035 : C === 'O' && V !== 'O' ? 0.13 : 0.07) * reach;
        cP.bend = [lean * 0.5, lean, lean * 0.8]; cP.tilt += lean * 0.3;
        const bC = fk(skC, cP);
        // the ear that works the knots: aim at whatever attachment is being released now
        let tgt = null, tgtS = null;
        if (t < tB0 - 0.05) tgtS = Pn.gagS; else { const cur = bands.slice().sort((a, b) => a.rel - b.rel).find(b => t < b.rel + dB); if (cur) tgtS = cur.s; }
        if (tgtS !== null && reach > 0.01) {
          const bv = fk(skV, vP); const pt = bv.edge(tgtS)[1];
          tgt = [pt[0] + 6, pt[1]];
          const aim = aimEar(bC, 0, tgt); const e0 = earUp(C, cL, drowsy(C));
          cP.ear[0] = [lerp(e0[0], aim[0], reach), lerp(e0[1], aim[1], reach)];
        }
        // after: rescuer stands back a little, holding the gag, then drops it
        cP.x += 30 * sm(straightT, straightT + 0.5, t);
        gag.carrier = 'C'; gag.drop = 2.75;
        // the doer: pride stands its ground (looms), otherwise it turns from the scene; per-sack manner
        aP = idleA(aX0);
        const watch = sm(0.5, 1.2, t);
        if (A === 'R') { aP.tilt = 0.05 * Math.sin(t * 5) * watch - 0.05 * watch; aP.sc *= 1 + 0.04 * Pn.pride * watch; }
        if (A === 'I') { aP.bend = [0.04, 0.06 * Math.sin(t * 3), 0.05]; aP.ear[1] = [2.6 + 0.15 * Math.sin(t * 4), 0.2]; aP.x += -40 * watch; }
        if (A === 'O') { const turn = sm(1.0, 1.25, t); aP.tilt = -0.1 * turn; aP.x -= 70 * sm(1.0, 1.8, t); }
        if (A === 'B') { aP.ear = [earUp(A, LA, 0.9 * watch), earUp(A, LA, 0.9 * watch)]; aP.bend = [0.05 * watch, 0.08 * watch, 0.08 * watch]; }
        aP.sc *= 1 - 0.06 * Pn.fearAC * watch;
      } else if (br === 'return') {
        // the doer goes back; guilt: ears down, slow; undoes what it did and backs away holding the gag
        aP = idleA(aX0);
        walk(aP, t, 0.3, tArr, aX0, reachX, A, LA);
        const reach = sm(tArr - 0.15, tGag, t) * (1 - sm(straightT, straightT + 0.3, t));
        const need = Math.max(0, Pn.gagS * skV.H * vsc - skA.H * aP.sc * 0.95);
        const hopping = t > tGag - 0.15 && t < tGag + 0.35 ? Math.sin(Math.PI * (t - tGag + 0.15) / 0.5) : 0;
        aP.y += need * 0.9 * hopping;
        const lean = (A === 'B' ? 0.035 : A === 'O' && V !== 'O' ? 0.13 : 0.07) * reach;
        aP.bend = [lean * 0.6, lean, lean * 0.8]; aP.tilt += lean * 0.4;
        const ears0 = earUp(A, LA, 1.0); aP.ear = [ears0, ears0];
        const bA = fk(skA, aP);
        let tgtS = null; if (t < tB0 - 0.05) tgtS = Pn.gagS; else { const cur = bands.slice().sort((a, b) => a.rel - b.rel).find(b => t < b.rel + dB); if (cur) tgtS = cur.s; }
        if (tgtS !== null && reach > 0.01) { const bv = fk(skV, vP); const pt = bv.edge(tgtS)[0]; const aim = aimEar(bA, 1, [pt[0] - 6, pt[1]]); aP.ear[1] = [lerp(ears0[0], aim[0], reach), lerp(ears0[1], aim[1], reach)]; }
        aP.x -= 150 * eo(straightT, straightT + 0.7, t);
        aP.tilt -= 0.05 * sm(straightT, straightT + 0.3, t);
        gag.carrier = 'A'; gag.drop = 3.0;
      } else { // loose: the doer is dead (a ghost does the deed); nobody's hand, the knots let go on their own
        aP = idleA(aX0); aAlpha = 0.35 + 0.2 * Math.sin(t * 3);
        aP.y = 10 + 6 * Math.sin(t * 2);
        gag.carrier = null;
      }
    } else if (br === 'burst') {
      // Belindo: strength is his only vocabulary. He swells; the bands break; the gag is pushed off.
      const n = bands.length;
      bands.forEach((b, j) => { b.snap = 1.0 + j * 0.16; b.mode = 'snap'; });
      gag.rel = 1.0 + n * 0.16 + 0.1; gag.mode = 'push';
      straightT = gag.rel + 0.2; S.straightT = straightT;
      const sw = sm(0.35, 1.0, t) * (1 - 0.6 * sm(gag.rel, gag.rel + 0.5, t));
      vP.swell = 1 + 0.16 * sw + 0.03 * Math.sin(t * 30) * sm(0.35, 0.8, t) * (1 - sm(1.0, 1.2, t));
      aP = idleA(aX0);
      const rec = eo(1.0, 1.6, t);
      aP.x -= 110 * rec; aP.tilt = -0.14 * rec * (1 - 0.5 * sm(2.2, 3.0, t)); aP.sc *= 1 - 0.1 * rec;
      aP.ear = [earUp(A, LA, -0.25 * rec), earUp(A, LA, -0.25 * rec)];  // ears up: alarm
      if (A === 'I') aP.y += 20 * Math.sin(Math.PI * cl(0, 1, (t - 1.0) / 0.4));
    } else if (br === 'hide') {
      // the victim was already dead: the doer has a bound still sack. It pushes it into the wardrobe.
      vAlpha = 1;
      aP = idleA(aX0);
      walk(aP, t, 0.2, 0.8, aX0, reachX, A, LA);
      const push = sm(0.9, 2.1, t), into = (WARD.x0 + WARD.x1) / 2;
      const dx = (into - VX) * push;
      aP.x += dx; walk(aP, t, 0.9, 2.1, aP.x, aP.x, A, LA);
      aP.bend = [0.05 * sm(0.8, 0.95, t), 0.1 * sm(0.8, 0.95, t), 0.06]; aP.tilt += 0.12 * sm(0.8, 0.95, t) * (1 - sm(2.1, 2.5, t));
      aP.x -= 160 * eo(2.4, 3.1, t);
      vP.x = VX + dx;
      vP.tilt = 0.12 * Math.sin(Math.PI * push); vP.pv = skV.W / 2;
      S.ward = sm(0.4, 0.85, t) * (1 - sm(2.15, 2.6, t));
      S.wardClosed = t > 2.15;
    } else { // alone: no one comes. The night passes, the rope holds, the cloth takes the rope's shape.
      S.dawn = sm(0.2, 3.2, t); S.lamp = 1 - 0.55 * sm(0.4, 3.0, t);
      aP = idleA(aX0);
      walk(aP, t, 0.3, 1.4, aX0, aX0 - 230, A, LA);
      aP.tilt -= 0.06 * sm(1.3, 1.6, t);
      if (A === 'R') aP.tilt += 0.04 * Math.sin(t * 4) * sm(1.4, 1.7, t);
      if (C) { // a witness opens the door, looks, and turns away
        const cL = Pn.LV(C), csc = sc(cL);
        S.door = sm(0.8, 1.05, t) * (1 - sm(2.3, 2.6, t));
        cP = { x: DOORX, y: 0, tilt: 0, pv: 0, bend: [0, 0, 0], top: 0, swell: 1, sc: csc * 0.92, pinch: [], ear: [earUp(C, cL), earUp(C, cL)] };
        const look = sm(1.05, 1.3, t), away = sm(1.9, 2.3, t);
        cP.x = DOORX - 40 * look + 50 * away;
        cP.ear = [earUp(C, cL, -0.3 * look * (1 - away)), earUp(C, cL, -0.3 * look * (1 - away))];
        cP.tilt = -0.05 * look * (1 - away) + 0.12 * away;
        cAlpha = 1 - sm(2.2, 2.45, t);
        S.witness = true;
      }
      // straining: each try rocks the root and the joints, less each time (the joints stiffen)
      const tries = [0.6, 1.3, 2.0, 2.6];
      tries.forEach((p, k) => { const d = (t - p) / 0.35; if (d > 0 && d < 1) { const a = Math.sin(Math.PI * d) * (1 - k * 0.22); vP.tilt += 0.05 * a * (k % 2 ? -1 : 1); vP.swell *= 1 + 0.05 * a; } });
      // the gag works a little loose, never off
      gag.slip = 0.04 * sm(1.3, 2.7, t);
    }
    // ---------- victim after release: stiff joints unbend in steps, bottom first ----------
    if (straightT < 9) {
      const b0 = bound(V), nS = V === 'I' ? 2 : V === 'B' ? 3 : 4;
      const s = [0, 1, 2].map(j => steps(K, t, straightT + j * 0.14, nS, 0.16));
      const tremor = (1 - s[2]) * 0.012 * Math.sin(t * 41) * (t > straightT ? 1 : 0);
      straight = s[2];
      vP.bend = b0.map((a, j) => a * (1 - s[j]) + tremor);
      vP.top = -0.03 * (1 - s[2]);
      // ears are joints too: they come up last, in hitches (Inigo's stay down; they always hang)
      const eS = steps(K, t, straightT + 0.35, 2, 0.22);
      const eu = earUp(V, LVv, drowsy(V));
      vP.ear = [0, 1].map(() => [lerp(pinned(V)[0], eu[0], eS), lerp(pinned(V)[1], eu[1], eS)]);
      // each sack's first free movement
      const f = sm(straightT + 0.45, straightT + 0.9, t);
      if (V === 'R') { vP.tilt += 0.06 * Math.sin((t - straightT) * 6) * f * (1 - sm(3.0, 3.35, t)); }
      if (V === 'B') { vP.swell *= 1 + 0.06 * f * (1 - sm(3.0, 3.3, t)); }
      if (V === 'I') { vP.bend = vP.bend.map((a, j) => a + 0.06 * f * (j === 1 ? 1 : 0.5)); vP.top += 0.08 * f; }  // slumps straight back down
      if (V === 'O') { vP.tilt += -0.025 * Math.sin((t - straightT) * 14) * f * (1 - sm(2.9, 3.2, t)); }
      // lean away from the one it fears (the doer), toward a rescuer it has no grudge against
      vP.tilt += 0.05 * Pn.vFearA * f * (br === 'return' ? 1.6 : 1);
    }
    // pinches: tied bands bite; released ones leave a shallow groove that stays (the imprint)
    bands.forEach(b => {
      const relU = b.mode === 'slide' ? sm(b.rel, b.rel + 0.12, t) : b.mode === 'snap' ? sm(b.snap, b.snap + 0.05, t) : 0;
      const press = br === 'alone' ? 1 + 0.4 * sm(0.5, 3.0, t) : 1;
      vP.pinch.push({ s: b.s, d: tight * press * (1 - relU) + 0.06 * relU, sig: 7 * Z });
    });
    const gRel = gag.mode === 'off' ? sm(gag.rel, gag.rel + 0.1, t) : gag.mode === 'push' ? sm(gag.rel, gag.rel + 0.08, t) : 0;
    vP.pinch.push({ s: gag.s - (gag.slip || 0), d: 0.2 * (1 - gRel) + 0.05 * gRel, sig: 9 * Z });
    vP.x += 0; S.vP = vP;
    S.actors.push({ id: V, role: 'V', sk: skV, P: vP, alpha: vAlpha, L: LVv, dead: !st.alive[V] });
    if (aP) S.actors.push({ id: A, role: 'A', sk: skA, P: aP, alpha: aAlpha, L: LA });
    if (cP) S.actors.push({ id: C, role: 'C', sk: skC, P: cP, alpha: cAlpha, L: Pn.LV(C) });
    S.bands = bands; S.gag = gag; S.straight = straight; S.tight = tight;
    return S;
  }

  // ---------- render ----------
  function draw(g, t, ev, st, K, layer) {
    const S = stage(t, ev, st, K), { Pn } = S, sm = K.sm, lerp = K.lerp, cl = K.cl, H = K.hash, W = 1920, Hh = 1080;
    const bodies = {}; S.actors.forEach(a => { a.b = fk(a.sk, a.P); bodies[a.role] = a; });
    const lampX = 880, lampY = 110, lamp = S.lamp;
    // ---- room ----
    g.fillStyle = '#17110d'; g.fillRect(0, 0, W, Hh);
    const wall = g.createLinearGradient(0, 0, 0, FLOOR); wall.addColorStop(0, '#2a1f19'); wall.addColorStop(1, '#3b2c22');
    g.fillStyle = wall; g.fillRect(0, 0, W, FLOOR);
    g.strokeStyle = 'rgba(0,0,0,0.18)'; g.lineWidth = 2; for (let x = 20; x < W; x += 64) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, FLOOR); g.stroke(); }
    // window: night, or the grey of morning when nobody came
    const dn = S.dawn;
    g.fillStyle = `rgb(${lerp(18, 120, dn) | 0},${lerp(26, 132, dn) | 0},${lerp(48, 150, dn) | 0})`; g.fillRect(250, 200, 230, 300);
    if (dn < 0.6) { g.fillStyle = `rgba(230,226,200,${0.8 * (1 - dn / 0.6)})`; g.beginPath(); g.arc(410, 260, 22, 0, 7); g.fill(); }
    g.strokeStyle = '#120c09'; g.lineWidth = 10; g.strokeRect(250, 200, 230, 300); g.beginPath(); g.moveTo(365, 200); g.lineTo(365, 500); g.moveTo(250, 350); g.lineTo(480, 350); g.stroke();
    // wardrobe
    const wd = WARD;
    g.fillStyle = '#21160f'; g.fillRect(wd.x0, wd.y0, wd.x1 - wd.x0, FLOOR - wd.y0);
    g.fillStyle = '#4a3324'; g.fillRect(wd.x0 - 14, wd.y0 - 22, wd.x1 - wd.x0 + 28, 24);
    if (Pn.br === 'hide' && !S.wardClosed) { const wdw = wd.x1 - wd.x0, pw = wdw / 2 * (1 - S.ward); g.fillStyle = '#4a3326'; g.fillRect(wd.x0, wd.y0, pw, FLOOR - wd.y0); g.fillRect(wd.x1 - pw, wd.y0, pw, FLOOR - wd.y0); g.fillStyle = '#5c4130'; g.fillRect(wd.x0 - 30 * S.ward, wd.y0, 30 * S.ward, FLOOR - wd.y0); g.fillRect(wd.x1, wd.y0, 30 * S.ward, FLOOR - wd.y0); }
    if (Pn.br !== 'hide') {
      const wdw = wd.x1 - wd.x0; g.fillStyle = '#4a3326'; g.fillRect(wd.x0, wd.y0, wdw, FLOOR - wd.y0);
      g.strokeStyle = '#2a1c13'; g.lineWidth = 5; g.strokeRect(wd.x0 + 14, wd.y0 + 14, wdw / 2 - 20, FLOOR - wd.y0 - 28); g.strokeRect(wd.x0 + wdw / 2 + 6, wd.y0 + 14, wdw / 2 - 20, FLOOR - wd.y0 - 28);
    }
    // door (for whoever comes)
    const dx0 = 1710, dx1 = 1890, dy0 = 330;
    g.fillStyle = '#0d0907'; g.fillRect(dx0, dy0, dx1 - dx0, FLOOR - dy0);
    if (S.door > 0) { g.fillStyle = `rgba(200,150,80,${0.35 * S.door})`; g.fillRect(dx0, dy0, dx1 - dx0, FLOOR - dy0); }
    g.fillStyle = '#5a3f2b'; const dw = (dx1 - dx0) * (1 - 0.82 * S.door); g.fillRect(dx1 - dw, dy0, dw, FLOOR - dy0);
    g.strokeStyle = '#2a1c13'; g.lineWidth = 6; g.strokeRect(dx0 - 4, dy0 - 4, dx1 - dx0 + 8, FLOOR - dy0 + 4);
    // floor
    const fl = g.createLinearGradient(0, FLOOR, 0, Hh); fl.addColorStop(0, '#4a3627'); fl.addColorStop(1, '#22180f');
    g.fillStyle = fl; g.fillRect(0, FLOOR, W, Hh - FLOOR);
    g.strokeStyle = 'rgba(0,0,0,0.3)'; g.lineWidth = 2; for (let k = 0; k < 4; k++) { const y = FLOOR + 22 + k * k * 14; g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
    // lamp light
    const lg = g.createRadialGradient(lampX, lampY + 120, 20, lampX, lampY + 300, 1100);
    lg.addColorStop(0, `rgba(255,205,130,${0.30 * lamp})`); lg.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = lg; g.fillRect(0, 0, W, Hh);
    // ---- shadows on the wall (shadow lever): each silhouette projected away from the lamp ----
    S.actors.forEach(a => {
      const L = a.L, len = 0.35 + 0.6 * cl(0, 1.2, L.shadow), al = (0.08 + 0.26 * cl(0, 1, L.shadow)) * a.alpha * (0.5 + 0.5 * lamp);
      g.save(); g.fillStyle = `rgba(6,3,2,${al})`; g.beginPath();
      a.b.out.forEach((p, i) => { const dxl = p[0] - lampX, hy = FLOOR - p[1]; const q = [p[0] + dxl * 0.18 * (1 + len), FLOOR - 40 - hy * (1 + len) * 0.95]; i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]); });
      g.closePath(); g.fill(); g.restore();
    });
    // halos (halo lever): the light finds it
    S.actors.forEach(a => { const h = cl(0, 1, a.L.halo); if (h < 0.05) return; const x = a.P.x; const rg = g.createRadialGradient(x, FLOOR - a.sk.H * 0.5, 10, x, FLOOR - a.sk.H * 0.5, a.sk.H * 1.1); rg.addColorStop(0, `rgba(255,230,170,${0.28 * h * a.alpha})`); rg.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = rg; g.fillRect(x - a.sk.H * 1.2, FLOOR - a.sk.H * 1.7, a.sk.H * 2.4, a.sk.H * 2.2); });
    // floor contact shadows
    S.actors.forEach(a => { g.fillStyle = `rgba(0,0,0,${0.4 * a.alpha})`; g.beginPath(); g.ellipse(a.P.x, FLOOR + 4, a.sk.W * a.P.sc * 0.55, 10, 0, 0, 7); g.fill(); });

    // ---- rope coils on the floor (released bands re-parented to the floor) ----
    const vb = bodies.V.b, vsk = bodies.V.sk;
    S.bands.forEach((bd, j) => {
      if (bd.mode === 'slide' && t > bd.rel + 0.35) coil(g, vb.P.x + (j - 1) * 70 - 40 + H(j) * 30, FLOOR + 14 + j * 7, 1.6 + 0.3 * H(j + 4), 1, H(j * 3));
      if (bd.mode === 'snap' && t > bd.snap) { // two halves flung: ballistic, land and lie
        const d = t - bd.snap;
        [-1, 1].forEach(sd => {
          const vx = sd * (240 + 120 * H(j * 5 + sd)), vy = -280 - 160 * H(j * 7 + sd), y0 = vb.at(bd.s, 0)[1];
          let x = vb.P.x + sd * vsk.W * 0.5 + vx * d, y = y0 + vy * d + 900 * d * d;
          const land = y >= FLOOR + 6; if (land) { const tl = (-vy + Math.sqrt(vy * vy + 3600 * (FLOOR + 6 - y0))) / 1800; x = vb.P.x + sd * vsk.W * 0.5 + vx * tl + sd * 20 * Math.min(1, (d - tl) * 4); y = FLOOR + 6; }
          g.save(); g.translate(x, y); g.rotate(land ? sd * 0.1 : d * 9 * sd); g.strokeStyle = ROPEd; g.lineWidth = 10; g.lineCap = 'round'; g.beginPath(); g.moveTo(-34, 0); g.quadraticCurveTo(0, -12, 34, 2); g.stroke(); g.strokeStyle = ROPE; g.lineWidth = 6; g.stroke();
          g.strokeStyle = '#e8d6a8'; g.lineWidth = 2; for (let k = 0; k < 5; k++) { g.beginPath(); g.moveTo(34 * sd + k * -sd * 2, -4 + k * 2); g.lineTo(40 * sd + k * -sd * 1, -8 + k * 4); g.stroke(); }
          g.restore();
        });
      }
    });

    // ---- sacks (back to front: witness/rescuer, victim, doer) ----
    const order = ['C', 'V', 'A'].filter(r => bodies[r]);
    const carry = st.body;
    order.forEach(r => {
      const a = bodies[r];
      if (r === 'A') wardFront();
      if (r === 'V' && S.wardClosed) return;          // the body is inside, behind the closed door
      g.save(); g.globalAlpha = a.alpha;
      drawSack(g, a, K, carry);
      if (r === 'V') drawAttach(g, S, a, K, bodies);
      g.restore();
    });
    // the wardrobe door closed over the body, a rope end caught under it (drawn before the doer)
    function wardFront() { if (Pn.br !== 'hide') return;
      const o = S.ward, wdw = (wd.x1 - wd.x0);
      if (S.wardClosed) {
        g.fillStyle = '#5c4130'; g.fillRect(wd.x0, wd.y0, wdw, FLOOR - wd.y0);
        g.strokeStyle = '#2a1c13'; g.lineWidth = 5; g.strokeRect(wd.x0 + 14, wd.y0 + 14, wdw / 2 - 20, FLOOR - wd.y0 - 28); g.strokeRect(wd.x0 + wdw / 2 + 6, wd.y0 + 14, wdw / 2 - 20, FLOOR - wd.y0 - 28);
        const shut = sm(2.15, 2.6, t); g.fillStyle = `rgba(0,0,0,${0.5 * (1 - shut)})`; g.fillRect(wd.x0 + wdw * shut, wd.y0, wdw * (1 - shut), FLOOR - wd.y0);
        // rope tail
        g.strokeStyle = ROPEd; g.lineWidth = 9; g.lineCap = 'round'; g.beginPath(); g.moveTo(wd.x0 + 40, FLOOR - 6); g.quadraticCurveTo(wd.x0 - 10, FLOOR + 8, wd.x0 - 70, FLOOR + 14); g.stroke(); g.strokeStyle = ROPE; g.lineWidth = 5; g.stroke();
      }
    }
    // lamp
    g.strokeStyle = '#120c09'; g.lineWidth = 3; g.beginPath(); g.moveTo(lampX, 0); g.lineTo(lampX, lampY - 40); g.stroke();
    g.fillStyle = '#3a2a1c'; g.beginPath(); g.moveTo(lampX - 34, lampY - 40); g.lineTo(lampX + 34, lampY - 40); g.lineTo(lampX + 70, lampY); g.lineTo(lampX - 70, lampY); g.closePath(); g.fill();
    g.fillStyle = `rgba(255,225,160,${0.4 + 0.6 * lamp})`; g.beginPath(); g.arc(lampX, lampY + 6, 10, 0, 7); g.fill();
    const vig = g.createRadialGradient(W / 2, Hh * 0.55, 400, W / 2, Hh * 0.55, 1200); vig.addColorStop(0, 'rgba(0,0,0,0)'); vig.addColorStop(1, `rgba(0,0,0,${0.45 + 0.25 * (1 - lamp)})`);
    g.fillStyle = vig; g.fillRect(0, 0, W, Hh);
    return S;
  }

  function coil(g, x, y, s, a, h) {
    g.save(); g.translate(x, y); g.scale(s, s * 0.45); g.globalAlpha *= a;
    g.lineCap = 'round';
    for (let k = 0; k < 3; k++) { g.strokeStyle = ROPEd; g.lineWidth = 15; g.beginPath(); g.ellipse(4 * k - 4, -k * 6, 30 - k * 4, 30 - k * 4, h, 0.3, 6.0); g.stroke(); g.strokeStyle = ROPE; g.lineWidth = 9; g.stroke(); }
    g.restore();
    g.save(); g.translate(x, y); g.strokeStyle = ROPE; g.lineWidth = 5; g.lineCap = 'round'; g.beginPath(); g.moveTo(26 * s, -2); g.quadraticCurveTo(46 * s, 6, 64 * s, 2); g.stroke(); g.restore();
  }
  function ringPath(g, P) {
    g.beginPath(); const N = P.length; g.moveTo((P[N - 1][0] + P[0][0]) / 2, (P[N - 1][1] + P[0][1]) / 2);
    for (let i = 0; i < N; i++) { const a = P[i], b = P[(i + 1) % N]; g.quadraticCurveTo(a[0], a[1], (a[0] + b[0]) / 2, (a[1] + b[1]) / 2); }
    g.closePath();
  }
  function greyed(hex, k) { const n = parseInt(hex.slice(1), 16), r = n >> 16, gg = (n >> 8) & 255, b = n & 255, m = (r + gg + b) / 3 * 0.85; return `rgb(${(r + (m - r) * k) | 0},${(gg + (m - gg) * k) | 0},${(b + (m - b) * k) | 0})`; }
  // a band strip across the body at arc s (in the frame of that bone): polygon, widened past the outline
  function strip(b, s0, s1, ext) { const p = []; for (let k = 0; k <= 4; k++) { const s = s0 + (s1 - s0) * k / 4; p.push(b.at(s, b.hw(s) + ext)); } for (let k = 4; k >= 0; k--) { const s = s0 + (s1 - s0) * k / 4; p.push(b.at(s, -b.hw(s) - ext)); } return p; }
  function poly(g, p) { g.beginPath(); p.forEach((q, i) => i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1])); g.closePath(); }

  function drawSack(g, a, K, carry) {
    const b = a.b, id = a.id, sk = a.sk, c = K.CAST[id], L = a.L;
    const gk = Math.min(1, L.grey + (has(carry, id, 'greyed') ? 0.6 : 0) + (a.dead ? 0.7 : 0));
    const fill = greyed(c.fill, gk);
    const ears = () => b.ears.forEach(e => {
      const bw = sk.earW * b.P.sc, f0 = ap(e.E0, [-bw / 2, 0]), f1 = ap(e.E0, [bw / 2, 0]), m0 = ap(e.E1, [-bw * 0.28, 0]), m1 = ap(e.E1, [bw * 0.28, 0]);
      g.beginPath(); g.moveTo(f0[0], f0[1]); g.lineTo(m0[0], m0[1]); g.lineTo(e.tip[0], e.tip[1]); g.lineTo(m1[0], m1[1]); g.lineTo(f1[0], f1[1]); g.closePath();
      g.fillStyle = id === 'R' ? greyed('#6e3a33', gk) : id === 'I' ? greyed('#a8915f', gk) : fill; g.fill(); g.strokeStyle = INK; g.lineWidth = 3; g.lineJoin = 'round'; g.stroke();
    });
    if (id !== 'I') ears();
    ringPath(g, b.out); g.fillStyle = fill; g.fill();
    g.save(); ringPath(g, b.out); g.clip();
    // cloth shading across the body (in the root frame), and the seams at the joints
    const x0 = b.P.x - sk.W, x1 = b.P.x + sk.W;
    const sh = g.createLinearGradient(x0, 0, x1, 0); sh.addColorStop(0.2, 'rgba(40,20,5,0.25)'); sh.addColorStop(0.5, 'rgba(255,240,210,0.08)'); sh.addColorStop(0.8, 'rgba(40,20,5,0.32)');
    g.fillStyle = sh; g.fillRect(x0, FLOOR - sk.H * 2, x1 - x0, sk.H * 2 + 20);
    if (id === 'R') { g.fillStyle = greyed('#6e3a33', gk); poly(g, strip(b, 0.8, 1.02, 30)); g.fill(); g.strokeStyle = 'rgba(0,0,0,0.25)'; g.lineWidth = 2; for (let k = 1; k < 4; k++) { const p = b.at(0.8, -b.hw(0.8) + k * b.hw(0.8) / 2); const q = ap(b.fr[4], [-b.hw(1) + k * b.hw(1) / 2, 0]); g.beginPath(); g.moveTo(p[0], p[1]); g.lineTo(q[0], q[1]); g.stroke(); } }
    if (id === 'B') {
      g.fillStyle = greyed('#2a2622', gk); poly(g, strip(b, 0.37, 0.43, 30)); g.fill();
      const F = b.frameAt(0.68); g.save(); g.transform(F[0], F[1], F[2], F[3], F[4], F[5]); const rr = sk.H * 0.14;
      g.strokeStyle = '#8a6a3a'; g.lineWidth = 4; g.beginPath(); g.arc(0, 0, rr, 0, 7); g.stroke(); g.beginPath(); g.moveTo(0, rr * 0.8); g.lineTo(0, -rr * 0.75); g.stroke();
      for (let k = 0; k < 4; k++) { const yy = -rr * 0.55 + k * rr * 0.3; g.beginPath(); g.moveTo(0, yy + 9); g.lineTo(-14, yy); g.moveTo(0, yy + 9); g.lineTo(14, yy); g.stroke(); }
      g.restore();
    }
    // joint seams: stitched lines across the body where one bone hands over to the next
    g.strokeStyle = 'rgba(60,40,20,0.35)'; g.lineWidth = 2; g.setLineDash([6, 7]);
    for (let j = 1; j < 4; j++) { const s = sk.cum[j] / sk.H, e = b.edge(s); g.beginPath(); g.moveTo(e[0][0], e[0][1]); g.lineTo(e[1][0], e[1][1]); g.stroke(); }
    g.setLineDash([]);
    // carried marks
    if (has(carry, id, 'torn')) { const p = b.at(0.45, b.hw(0.45) * 0.7), q = b.at(0.25, b.hw(0.25) * 0.85); g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); for (let k = 0; k <= 6; k++) { const x = lerp2(p[0], q[0], k / 6) + (k % 2 ? -7 : 7), y = lerp2(p[1], q[1], k / 6); k ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); }
    if (has(carry, id, 'blot')) { g.fillStyle = '#14161c'; for (let k = 0; k < 6; k++) { const p = b.at(0.5 + 0.1 * K.hash(k), b.hw(0.5) * (0.3 * K.hash(k + 3) - 0.1)); g.beginPath(); g.arc(p[0], p[1], 6 + 8 * K.hash(k + 7), 0, 7); g.fill(); } }
    g.restore();
    ringPath(g, b.out); g.strokeStyle = INK; g.lineWidth = 3.5; g.stroke();
    // pivots: the rig's joints shown as small stitched rings on the centre line (hierarchy made visible)
    g.strokeStyle = 'rgba(60,40,20,0.45)'; g.lineWidth = 2;
    for (let j = 1; j < 4; j++) { const p = ap(b.fr[j], [0, 0]); g.beginPath(); g.arc(p[0], p[1], 4, 0, 7); g.stroke(); }
    if (id === 'I') ears();   // Inigo's ears hang in front of him like long unwashed hair
    if (id === 'O') drawWig(g, b, K, carry, gk);
    if (has(carry, id, 'coins')) { g.fillStyle = '#d8c070'; g.strokeStyle = '#5a4a20'; g.lineWidth = 1.5; const p = b.at(0.02, b.hw(0) + 16); for (let k = 0; k < 4; k++) { g.beginPath(); g.ellipse(p[0], FLOOR - 4 - k * 6, 11, 4, 0, 0, 7); g.fill(); g.stroke(); } }
    if (has(carry, id, 'tag')) { const p = b.at(0.75, b.hw(0.75)); g.fillStyle = '#e9e3cf'; g.strokeStyle = INK; g.lineWidth = 2; g.fillRect(p[0] + 4, p[1] + 10, 30, 20); g.strokeRect(p[0] + 4, p[1] + 10, 30, 20); g.beginPath(); g.moveTo(p[0] - 4, p[1]); g.lineTo(p[0] + 12, p[1] + 10); g.stroke(); }
  }
  const lerp2 = (a, b, u) => a + (b - a) * u;
  function drawWig(g, b, K, carry, gk) {
    // the wig is a child of the top frame: cap, then strand chains that hang under gravity from it
    const top = b.fr[4], tw = b.hw(1), sk = b.sk, sl = has(carry, 'O', 'wig') ? 1 : 0;
    const col = greyed('#7a3b8f', gk * 0.7);
    g.save(); g.fillStyle = col; g.strokeStyle = col; g.lineCap = 'round';
    g.save(); g.transform(top[0], top[1], top[2], top[3], top[4], top[5]); g.beginPath(); g.ellipse(sl * 10, 2, tw + 14, 24 * Z * 0.8, sl * 0.2, Math.PI, 0); g.fill(); g.restore();
    const th = ang(top);
    for (let s = 0; s < 10; s++) {
      const sd = s < 5 ? -1 : 1, k = s % 5; let p = ap(top, [sd * (tw - 4 + k * 3) + sl * 8, -2]);
      g.lineWidth = 7; g.beginPath(); g.moveTo(p[0], p[1]);
      const n = 6, segL = sk.H * (sl && sd < 0 ? 0.3 : 0.6) / n;
      let a = th * 0.5 + sd * (0.18 + k * 0.05);
      for (let j = 0; j < n; j++) { a *= 0.75; p = [p[0] - Math.sin(a) * segL + sd * 1.2, p[1] + Math.cos(a) * segL]; g.lineTo(p[0], p[1]); }
      g.stroke();
    }
    g.restore();
  }
  // attachments on the victim: bands, gag, and the rope's imprint pressed into the cloth
  function drawAttach(g, S, a, K, bodies) {
    const b = a.b, t = S.t, sm = K.sm, sk = a.sk;
    const rw = 9 * Z * 0.75;
    // imprints first (they belong to the cloth): visible wherever the rope has been
    S.bands.forEach(bd => {
      const gone = bd.mode === 'slide' ? sm(bd.rel + 0.05, bd.rel + 0.2, t) : bd.mode === 'snap' ? sm(bd.snap, bd.snap + 0.1, t) : (S.Pn.br === 'alone' ? sm(1.2, 3.0, t) * 0.4 : 0);
      if (gone <= 0) return;
      const e = b.edge(bd.s);
      g.save(); g.globalAlpha *= gone;
      g.strokeStyle = 'rgba(90,60,30,0.55)'; g.lineWidth = 2.5;
      [-1, 1].forEach(o => { const p = b.at(bd.s + o * 0.018, -b.hw(bd.s) * 0.97), q = b.at(bd.s + o * 0.018, b.hw(bd.s) * 0.97); g.beginPath(); g.moveTo(p[0], p[1]); g.lineTo(q[0], q[1]); g.stroke(); });
      g.strokeStyle = 'rgba(110,75,40,0.6)'; g.lineWidth = 2;
      const n = Math.floor(b.hw(bd.s) * 2 / 11);
      for (let k = 0; k < n; k++) { const u = -1 + (2 * k + 1) / n; const p = b.at(bd.s - 0.014, b.hw(bd.s) * u * 0.95), q = b.at(bd.s + 0.014, b.hw(bd.s) * u * 0.95 + 6); g.beginPath(); g.moveTo(p[0], p[1]); g.lineTo(q[0], q[1]); g.stroke(); }
      // a reddened rub at each knot side
      const kn = e[0]; g.fillStyle = 'rgba(150,80,50,0.25)'; g.beginPath(); g.arc(kn[0] + 6, kn[1], 9, 0, 7); g.fill();
      g.restore();
    });
    // bands still on (or sliding down to the floor)
    S.bands.forEach(bd => {
      let s = bd.s, al = 1, slack = 0;
      if (bd.mode === 'slide') { if (t > bd.rel + 0.35) return; const u = sm(bd.rel, bd.rel + 0.35, t); s = bd.s * (1 - u); slack = 14 * Math.min(1, u * 3); }
      if (bd.mode === 'snap' && t > bd.snap) return;
      const e = b.edge(Math.max(0.02, s)), ext = 4;
      const L = [e[0][0] - ext, e[0][1]], Rr = [e[1][0] + ext, e[1][1]];
      const strain = bd.mode === 'snap' ? sm(bd.snap - 0.5, bd.snap, t) : 0;
      g.lineCap = 'round';
      g.strokeStyle = ROPEd; g.lineWidth = rw + 4; g.beginPath(); g.moveTo(L[0], L[1]); g.quadraticCurveTo((L[0] + Rr[0]) / 2, (L[1] + Rr[1]) / 2 + slack, Rr[0], Rr[1]); g.stroke();
      g.strokeStyle = strain > 0.5 ? '#d8bd85' : ROPE; g.lineWidth = rw * (1 - 0.35 * strain); g.stroke();
      // twist marks
      g.strokeStyle = 'rgba(70,50,25,0.7)'; g.lineWidth = 1.5;
      for (let k = 1; k < 9; k++) { const u = k / 9, x = L[0] + (Rr[0] - L[0]) * u, y = L[1] + (Rr[1] - L[1]) * u + slack * 4 * u * (1 - u); g.beginPath(); g.moveTo(x - 3, y - rw / 2); g.lineTo(x + 3, y + rw / 2); g.stroke(); }
      // the knot on the doer's side, with two ends
      g.fillStyle = ROPE; g.strokeStyle = ROPEd; g.lineWidth = 3;
      g.beginPath(); g.arc(L[0] + 2, L[1], rw * 0.95, 0, 7); g.fill(); g.stroke();
      g.beginPath(); g.moveTo(L[0], L[1] + 3); g.quadraticCurveTo(L[0] - 14, L[1] + 14, L[0] - 10, L[1] + 30); g.moveTo(L[0] + 4, L[1] + 3); g.quadraticCurveTo(L[0] - 2, L[1] + 18, L[0] + 6, L[1] + 32); g.strokeStyle = ROPEd; g.lineWidth = rw * 0.7; g.stroke();
    });
    // the gag: on the top frame, then re-parented to an ear tip, then dropped on the floor
    const gg = S.gag, br = S.Pn.br;
    const gs = gg.s - (gg.slip || 0);
    const offT = gg.mode === 'off' || gg.mode === 'push' ? gg.rel : 9;
    if (t < offT + 0.05) {
      const e = b.edge(gs), L = [e[0][0] - 3, e[0][1]], Rr = [e[1][0] + 3, e[1][1]];
      const lift = gg.mode === 'push' ? sm(offT - 0.4, offT, t) * 10 : 0;
      g.lineCap = 'round'; g.strokeStyle = INK; g.lineWidth = 24; g.beginPath(); g.moveTo(L[0], L[1] - lift); g.lineTo(Rr[0], Rr[1] - lift); g.stroke();
      g.strokeStyle = GAGC; g.lineWidth = 19; g.stroke();
      g.strokeStyle = 'rgba(80,60,40,0.4)'; g.lineWidth = 1.5; for (let x = 8; x < Rr[0] - L[0] - 4; x += 10) { const u = x / (Rr[0] - L[0]); g.beginPath(); g.moveTo(L[0] + x, L[1] + (Rr[1] - L[1]) * u - 7 - lift); g.lineTo(L[0] + x + 4, L[1] + (Rr[1] - L[1]) * u + 7 - lift); g.stroke(); }
      // knot and tails
      g.fillStyle = GAGC; g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); g.arc(L[0] - 4, L[1] - lift, 12, 0, 7); g.fill(); g.stroke();
      const fl = 4 * Math.sin(t * 5);
      g.lineWidth = 9; g.strokeStyle = GAGC; g.beginPath(); g.moveTo(L[0] - 8, L[1] + 4); g.quadraticCurveTo(L[0] - 26, L[1] + 18, L[0] - 30 + fl, L[1] + 44); g.stroke();
      g.beginPath(); g.moveTo(L[0] - 4, L[1] + 6); g.quadraticCurveTo(L[0] - 12, L[1] + 26, L[0] - 8 - fl, L[1] + 50); g.stroke();
      // under the gag: once removed the cloth keeps a crease (drawn later)
    } else {
      // crease where the gag bit
      const e = b.edge(gs);
      g.strokeStyle = 'rgba(90,60,30,0.5)'; g.lineWidth = 2.5; [-1, 1].forEach(o => { const p = b.at(gs + o * 0.025, -b.hw(gs) * 0.96), q = b.at(gs + o * 0.025, b.hw(gs) * 0.96); g.beginPath(); g.moveTo(p[0], p[1]); g.lineTo(q[0], q[1]); g.stroke(); });
      // where is the gag now: hanging from the carrier's ear tip, or on the floor
      const car = gg.carrier ? bodies[gg.carrier] : null;
      let p, hanging = false;
      if (car && t < gg.drop) { const e2 = car.b.ears[gg.carrier === 'C' ? 0 : 1]; p = e2.tip; hanging = true; }
      else if (br === 'burst') { const d = t - offT; p = [e[1][0] + 30 + 160 * Math.min(d, 0.7), Math.min(FLOOR - 6, e[1][1] - 80 * d + 500 * d * d)]; hanging = p[1] < FLOOR - 7; }
      else { const ref = car ? car.b.ears[gg.carrier === 'C' ? 0 : 1] : null; const x = ref ? ref.tip[0] : e[0][0] - 30; const d = Math.max(0, t - gg.drop); p = [x, Math.min(FLOOR - 6, (ref ? ref.tip[1] : e[0][1]) + 700 * d * d)]; hanging = p[1] < FLOOR - 7; }
      g.lineCap = 'round';
      if (hanging) { g.strokeStyle = INK; g.lineWidth = 24; g.beginPath(); g.moveTo(p[0], p[1]); g.quadraticCurveTo(p[0] + 14, p[1] + 50, p[0] - 6, p[1] + 110); g.stroke(); g.strokeStyle = GAGC; g.lineWidth = 18; g.stroke(); g.fillStyle = GAGC; g.strokeStyle = INK; g.lineWidth = 3; g.beginPath(); g.arc(p[0], p[1], 12, 0, 7); g.fill(); g.stroke(); }
      else { g.strokeStyle = INK; g.lineWidth = 15; g.beginPath(); g.moveTo(p[0] - 40, FLOOR + 4); g.quadraticCurveTo(p[0], FLOOR - 6, p[0] + 40, FLOOR + 6); g.stroke(); g.strokeStyle = GAGC; g.lineWidth = 11; g.stroke(); }
    }
  }

  // ---------- sound: grains; rope slithers, knots pop, joints creak in steps ----------
  function sound(ac, out, t0, ev, st, K) {
    const mg = ac.createGain(); mg.gain.value = 2.6; mg.connect(out); out = mg;
    const SND = K.SND, H = K.hash, Pn = plan(ev, st, K), { br, A, V, C } = Pn;
    const pan = x => Math.max(-1, Math.min(1, x / 960 - 1));
    const S0 = stage(0, ev, st, K), vp = pan(VX), ap0 = pan(AX);
    const knot = (w, a, p) => { SND.grain(ac, out, t0 + w, { bp: 1100, q: 3, d: 0.05, a, pan: p, att: 0.1 }); SND.grain(ac, out, t0 + w + 0.02, { f: 300, d: 0.04, a: a * 0.5, pan: p, att: 0.05 }); };
    const slither = (w, d, a, p) => SND.cloud(ac, out, t0 + w, d, 120, { bp: 1800, q: 2, a, d: [0.01, 0.04], spread: 0.3 }, u => Math.sin(Math.PI * u));
    const creak = (w, a, p, f) => SND.grain(ac, out, t0 + w, { f: f || 140, d: 0.12, a, pan: p, att: 0.2, type: 'sawtooth', noise: 0.5, glide: 0.25 });
    // muffled breathing under the gag at the start (always)
    SND.say(ac, out, V, t0 + 0.05, 'breathe', 0.5, vp);
    const stiff = T => { for (let j = 0; j < 3; j++) for (let k = 0; k < 3; k++) creak(T + j * 0.14 + k * 0.16, 0.07, vp, 110 + j * 30 + H(j * 3 + k) * 20); };
    if (br === 'rescue' || br === 'return' || br === 'loose') {
      const S = stage(1.0, ev, st, K);
      if (br === 'rescue') { SND.grain(ac, out, t0 + 0.05, { f: 90, d: 0.4, a: 0.12, pan: 0.85, type: 'sawtooth', noise: 0.6, glide: 0.4 }); for (let w = 0.25; w < 1.05; w += 0.2) SND.say(ac, out, C, t0 + w, 'step', 0.7, pan(DOORX - (w - 0.2) * 500)); }
      if (br === 'return') for (let w = 0.35; w < 1.1; w += 0.25) SND.say(ac, out, A, t0 + w, 'step', 0.6, pan(AX + (w - 0.3) * 600));
      const gr = S.gag.rel; slither(gr - 0.05, 0.25, 0.05, vp); knot(gr, 0.35, vp);
      SND.say(ac, out, V, t0 + gr + 0.15, V === 'I' ? 'breathe' : 'react', 0.7, vp);    // first free breath / cry
      S.bands.forEach(b => { knot(b.rel, 0.28, vp); slither(b.rel + 0.02, 0.3, 0.04, vp); SND.thump(ac, out, t0 + b.rel + 0.35, 0.25, 110, vp); });
      stiff(S.straightT);
      if (br === 'return') SND.say(ac, out, A, t0 + S.straightT + 0.3, 'sink', 0.6, ap0);
      if (S.gag.carrier) SND.say(ac, out, S.gag.carrier === 'C' ? C : A, t0 + S.gag.drop + 0.15, 'tick', 0.6, vp);
    } else if (br === 'burst') {
      SND.cloud(ac, out, t0 + 0.35, 0.7, 60, { f: 55, glide: 0.3, a: 0.05, d: [0.08, 0.2], type: 'triangle' }, u => u);
      const S = stage(1.0, ev, st, K);
      S.bands.forEach((b, j) => { SND.grain(ac, out, t0 + b.snap, { bp: 2500, q: 1, d: 0.07, a: 0.5, pan: vp, att: 0.02 }); SND.thump(ac, out, t0 + b.snap, 0.5, 60, vp); knot(b.snap + 0.4, 0.15, vp - 0.2); knot(b.snap + 0.45, 0.15, vp + 0.2); });
      SND.say(ac, out, 'B', t0 + S.gag.rel, 'react', 1.0, vp);
      SND.say(ac, out, A, t0 + 1.05, 'react', 0.6, ap0);
      stiff(S.straightT);
    } else if (br === 'hide') {
      for (let w = 0.25; w < 0.8; w += 0.18) SND.say(ac, out, A, t0 + w, 'step', 0.6, pan(AX + (w - 0.2) * 1100));
      SND.cloud(ac, out, t0 + 0.9, 1.2, 70, { bp: 400, q: 1, a: 0.06, d: [0.05, 0.15], noise: 1 }, u => Math.sin(Math.PI * u));
      for (let w = 0.95; w < 2.1; w += 0.3) SND.say(ac, out, A, t0 + w, 'step', 0.8, pan(1300));
      SND.grain(ac, out, t0 + 0.45, { f: 80, d: 0.4, a: 0.1, pan: 0.5, type: 'sawtooth', noise: 0.6, glide: 0.5 });
      SND.thump(ac, out, t0 + 2.55, 0.9, 70, pan(1490));
      SND.grain(ac, out, t0 + 2.58, { bp: 800, q: 2, d: 0.12, a: 0.3, pan: pan(1490), att: 0.05 });
    } else {
      for (let k = 0; k < 13; k++) SND.grain(ac, out, t0 + 0.2 + k * 0.25, { f: k % 2 ? 2100 : 1900, d: 0.015, a: 0.06, pan: -0.6, att: 0.05 });   // the clock
      for (let w = 0.35; w < 1.4; w += 0.26) SND.say(ac, out, A, t0 + w, 'step', 0.5, pan(AX - (w - 0.3) * 200));
      [0.6, 1.3, 2.0, 2.6].forEach((p, k) => { SND.say(ac, out, V, t0 + p + 0.1, 'step', 0.5 - k * 0.08, vp); creak(p + 0.15, 0.16 - k * 0.025, vp, 160); SND.grain(ac, out, t0 + p + 0.12, { bp: 900, q: 2, d: 0.08, a: 0.22 - k * 0.03, pan: vp, att: 0.1 }); SND.say(ac, out, V, t0 + p + 0.2, 'breathe', 0.5, vp); });
      if (C) { SND.grain(ac, out, t0 + 0.82, { f: 90, d: 0.35, a: 0.1, pan: 0.85, type: 'sawtooth', noise: 0.6, glide: 0.4 }); SND.say(ac, out, C, t0 + 1.2, 'tick', 0.5, 0.85); SND.say(ac, out, C, t0 + 2.0, 'step', 0.6, 0.85); SND.thump(ac, out, t0 + 2.6, 0.4, 90, 0.85); }
    }
  }

  // ---------- trace: a coiled rope with its knot, fading/aging with shots since ----------
  function trace(g, box, age, K) {
    const a = Math.max(0.25, 1 - age * 0.1), s = Math.min(box.w / 140, box.h / 70);
    g.save(); g.globalAlpha *= a;
    coil(g, box.x + box.w * 0.45, box.y + box.h * 0.7, s, 1, 0.3 + age * 0.2);
    // the knot, kept tied
    g.fillStyle = ROPE; g.strokeStyle = ROPEd; g.lineWidth = 2.5; g.beginPath(); g.arc(box.x + box.w * 0.45 - 28 * s, box.y + box.h * 0.62, 7 * s, 0, 7); g.fill(); g.stroke();
    g.restore();
  }

  CONSEQ({
    deed: 'tying', n: 7, scion: 32, lineage: 'Forward Kinematics — Hierarchical Body Logic',
    op: 'Each sack is a joint tree whose world frames are parent-times-local matrices; rope and gag are attachments parented to a spine frame, released by re-parenting to the floor or an untier\'s ear, leaving an imprint child that stays, while the freed joints unbend in stiff steps from the root up.',
    made: 'Sacks are four-bone spines with fixed bone lengths, width profiles hung on the bones, ear chains (and wig strands) parented to the top joint; stitched seams and pivot rings show where one bone hands to the next. Rope bands, knots, the gag and the pressed rope marks are attachments in a bone\'s local frame, in a lamplit boarding-house room with a door, a wardrobe and a window.',
    moved: 'Joint angles and root motion are authored per sack and per ledger branch (who comes, who unties, who bursts, who hides a body), and every child follows its parent; ears are aimed at the knots being undone. The archetype levers scale and lean the sacks, lengthen their wall shadows, light them, shrink their ears and drain their colour.',
    dur: DUR,
    beat(g, t, ev, st, K, X) { draw(g, t, ev, st, K); },
    sound, trace,
    _test: { fk, skeleton, boneErr, plan, stage },
  });
})();
