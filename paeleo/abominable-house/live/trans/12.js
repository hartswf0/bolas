// TRANSITION 12 · Strangling (ARAP mesh sacks before wallpaper) -> THE FIRE
// SCION-47 · Sound-to-Action (viseme and gesture swarm). The picture is driven by the sound we schedule.
// SCORE FIRST: from the ledger we compute one event list for the whole transition (a pure function of the film):
//   CLOCK   the hall clock's ticks; the pendulum's zero crossings ARE the ticks, it stops on the last one
//   INDEX   the copybook read aloud: entries k = 0..11 struck as a descending scale; each strike is the moment the
//           light finds evidence k where it was left (in its victim's room); a refused deed is struck muted
//   REACT   every living sack that KNOWS event k (st.know) answers that strike with its own voice, amplitude =
//           its memory weight (LEDGER.memories): it flinches and leans toward the room where it happened.
//           Sacks that don't know don't move. The dead make no sound and do not move at all.
//   GHOST   each contradiction (a dead sack acting) is struck with a glass glide in that sack's register; the
//           ghost's opacity is that grain's envelope
//   BREATH  the living breathe at a rate set by their tempo lever; the picture swells on each breath grain
//   DUST    each flour grain heard is one puff of flour leaving a source (spilled flour, emptied/torn sacks, the
//           bodies, the stores); the motes on screen are exactly the dust grains scheduled so far
//   HOLD    silence: breath, clock and dust stop; nothing moves but the dust already in the air (thought)
//   SPARK   the thirteenth note of the index scale: the missing last entry. A spark drops from the parlour lamp.
// The camera pulls out from the strangling frame to the whole house (a section of nine rooms papered in the deed's
// mesh lattice) and returns to the same frame; draw() reads the same envelopes the sound() schedules.
// Invariants (numeric): u=0 equals the outgoing levered end frame; u=dur equals the fire's first frame
// (strangling t=5.99, carry states[11].body) plus the spark; every dust mote has a scheduled grain.
(function () {
const DUR = 3.5, IDS = ['R', 'B', 'I', 'O'];
const CW = 1920, CH = 1080, GAP = 110, FLOOR = 915;
const T_OUT0 = .12, T_OUT1 = .95, T_IN0 = 2.5, T_IN1 = 3.2, T_IDX0 = .82, T_IDXD = .085, T_DUST0 = 1.45, T_DUST1 = 2.98, T_HOLD = 3.0, T_SPARK = 3.2;
const SPARK0 = [960, 232], SPARK1 = [960, 620];
const cl = (a, b, x) => Math.max(a, Math.min(b, x)), sm = (a, b, x) => { const u = cl(0, 1, (x - a) / (b - a)); return u * u * (3 - 2 * u) };
const H = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s) };
const mkc = (w, h) => { const c = document.createElement('canvas'); c.width = w || 1920; c.height = h || 1080; return c };
// attack-decay kernel: the shape a grain gives the picture
const ad = (u, te, a, d) => u < te ? 0 : (u - te < a ? (u - te) / a : Math.exp(-(u - te - a) / d));

// ---------- the house: 3 x 3 rooms, the parlour is the strangling stage ----------
const ROOMS = { I: [0, 0], store: [1, 0], O: [2, 0], R: [0, 1], B: [1, 1], landing: [2, 1], kitchen: [0, 2], parlour: [1, 2], hall: [2, 2] };
const cx0 = c => c * (CW + GAP), cy0 = r => r * (CH + GAP);
const roomO = k => [cx0(ROOMS[k][0]), cy0(ROOMS[k][1])];
const HX0 = -GAP, HX1 = 3 * CW + 3 * GAP, HY0 = -GAP, HY1 = 3 * CH + 3 * GAP, ROOF = 640;
const S0 = Math.min(1920 / 6900, 1080 / (HY1 - HY0 + ROOF + 320)), HC = [(HX0 + HX1) / 2, (HY0 - ROOF + HY1 + 120) / 2];
const P0 = roomO('parlour'), PC = [P0[0] + 960, P0[1] + 540];
function camera(u) {
  const z = sm(T_OUT0, T_OUT1, u) * (1 - sm(T_IN0, T_IN1, u));
  const s = Math.exp(Math.log(S0) * z), f = (1 / s - 1) / (1 / S0 - 1);
  return { s, c: [PC[0] + (HC[0] - PC[0]) * f, PC[1] + (HC[1] - PC[1]) * f], z };
}
const toScr = (cam, p) => [(p[0] - cam.c[0]) * cam.s + 960, (p[1] - cam.c[1]) * cam.s + 540];
const WIDE = { s: S0, c: HC };
const panOf = p => cl(-1, 1, toScr(WIDE, p)[0] / 960 - 1);

const WALL = { photograph: 1, ink: 1, keyhole: 1, curtain: 1 };
const FLOORSLOTS = [[150, 0], [1770, 0], [360, 0], [1560, 0], [560, 0], [1360, 0], [250, 1], [1660, 1]];
const WALLSLOTS = [[300, 380], [1620, 380], [620, 300], [1300, 300], [180, 560], [1740, 560]];
const EVW = 300, EVH = 220;

let CACHE = null;
function build(X, K) {
  const L = X.ledger, key = X.film.join(',');
  if (CACHE && CACHE.key === key) return CACHE;
  const D = (X.DEEDS || window.DEEDS).strangling, e = L.ev[11], st11 = L.states[11], st = L.states[12];
  const C = { key, e, st };
  // --- the two parlour frames: levered end of the deed (what was on screen) and the fire's plain first frame ---
  C.FL = mkc(); C.LY = {};
  { const q = C.FL.getContext('2d'); q.fillStyle = '#000'; q.fillRect(0, 0, 1920, 1080);
    const order = D.layers || ['bg', 'V', 'A'], mk = D.marks ? D.marks(5.99, e.A, e.V, K) : null; C.MK = mk;
    for (const ly of order) {
      const c = mkc(), qq = c.getContext('2d'); try { D.draw(qq, 5.99, e.A, e.V, K, { layer: ly, carry: st11.body }) } catch (err) { } C.LY[ly] = c;
      if (ly === 'bg' || !mk) { q.drawImage(c, 0, 0); continue }
      const who = ly === 'A' ? e.A : e.V, lv = st11.levers[who], b = mk[ly];
      const f = 1 + .14 * cl(-1, 1, lv.loom) - .22 * lv.shrink, cx = b.x + b.w / 2, by = b.y + b.h;
      q.save(); q.filter = levFilter(lv, 1); q.translate(cx, by); q.scale(f, f); q.translate(-cx, -by); q.drawImage(c, 0, 0); q.restore();
    }
    C.FE = mkc(); C.FE.getContext('2d').drawImage(C.FL, 0, 0);   // the fire's first frame: levered, no contradiction scanlines
    if (st.impossible.find(qq => qq.k === 11)) { q.fillStyle = 'rgba(120,220,150,.06)'; for (let y = 0; y < 1080; y += 6) q.fillRect(0, y, 1920, 2) }
  }
  C.BG = C.LY.bg || C.FE;
  // --- the sacks outside the parlour, cut from the same mesh solver (victim layer at rest, with their damage) ---
  C.SP = {};
  for (const id of IDS) {
    const Y = IDS.find(o => o !== id), carry = { R: [], B: [], I: [], O: [] }; carry[id] = st.body[id];
    const full = mkc(), q = full.getContext('2d'); try { D.draw(q, 0, Y, id, K, { layer: 'V', carry }) } catch (err) { }
    const b = D.marks(0, Y, id, K).V, m = 90, x0 = Math.floor(b.x - m), y0 = Math.floor(b.y - m), w = Math.ceil(b.w + 2 * m), h = Math.ceil(b.h + m + 40);
    const c = mkc(w, h); c.getContext('2d').drawImage(full, -x0, -y0);
    C.SP[id] = { c, ox: b.x - x0, oy: b.y - y0, w: b.w, h: b.h };
  }
  // --- where everyone is ---
  const inP = id => id === e.A || id === e.V;
  C.where = {};
  for (const id of IDS) {
    if (inP(id) && (st.alive[id] || st.deadAt[id] === 11)) { C.where[id] = { kind: 'parlour' }; continue }
    if (st.alive[id]) { const o = roomO(id); C.where[id] = { kind: 'alive', room: id, p: [o[0] + 960, o[1] + FLOOR] }; continue }
    const hide = Math.floor(H(st.deadAt[id] * 7.3 + IDS.indexOf(id) * 1.9) * 3);
    const room = ['own', 'store', 'hall'][hide] === 'own' ? id : ['own', 'store', 'hall'][hide];
    const o = roomO(room), x = room === 'store' ? 1060 : room === 'hall' ? 520 : 960;
    C.where[id] = { kind: 'body', room, p: [o[0] + x, o[1] + FLOOR], ghostP: inP(id) };
  }
  // --- evidence: every trace in its victim's room (the cord stays in the parlour frame) ---
  const used = {}; C.evid = [];
  for (const ev of st.evidence) {
    if (ev.k === 11) { const mv = C.MK ? C.MK.V : { x: 1250, y: 600, w: 200, h: 300 }; C.evid.push({ ...ev, parlour: true, p: [P0[0] + mv.x + mv.w / 2, P0[1] + mv.y + mv.h * .25] }); continue }
    const room = ev.V, o = roomO(room), wall = !!WALL[ev.kind];
    used[room] = used[room] || { w: 0, f: 0 };
    let p, box;
    if (wall) { const s = WALLSLOTS[used[room].w++ % WALLSLOTS.length]; p = [o[0] + s[0], o[1] + s[1]] }
    else { const s = FLOORSLOTS[used[room].f++ % FLOORSLOTS.length]; p = [o[0] + s[0], o[1] + FLOOR + 30 - s[1] * 120] }
    box = { x: p[0] - EVW / 2, y: p[1] - EVH + (wall ? EVH / 2 : 0), w: EVW, h: EVH };
    C.evid.push({ ...ev, room, p, box });
  }
  // ---------- THE SCORE: computed once; sound() schedules it, draw() reads its envelopes ----------
  const S = C.score = { clock: [], idx: [], react: [], ghost: [], breath: [], dust: [], spark: T_SPARK };
  for (let t = .22; t < T_HOLD - .01; t += .5) S.clock.push(t);
  const SCALE = [79, 77, 76, 74, 72, 71, 69, 67, 65, 64, 62, 60, 55];   // 12 entries + the missing thirteenth
  for (const ev of C.evid) S.idx.push({ k: ev.k, t: T_IDX0 + ev.k * T_IDXD, m: SCALE[ev.k], muted: !!ev.refused, p: ev.p, kind: ev.kind });
  for (const id of IDS) {
    const w = C.where[id]; if (w.kind !== 'alive') continue;
    const mems = X.ledger && LEDGER.memories(L, id, 12);
    for (const ix of S.idx) {
      if (!st.know[id].includes(ix.k)) continue;
      const m = mems.find(q => q.k === ix.k), amt = cl(.15, 1, m ? m.weight : .2);
      S.react.push({ id, k: ix.k, t: ix.t + .06 + .04 * (1 - amt), amt, toward: Math.sign(ix.p[0] - w.p[0]) || 0, p: w.p });
    }
    const P = cl(.7, 1.4, 1.1 - .35 * st.levers[id].tempo);
    for (let t = .25 + H(IDS.indexOf(id) * 3.1) * .4; t < T_HOLD - .3; t += P) S.breath.push({ id, t, P, p: w.p });
  }
  for (const q of st.impossible) {
    const ev = C.evid.find(v => v.k === q.k); if (!ev) continue;
    const gp = ev.parlour ? null : [ev.p[0] + (ev.p[0] % CW < 960 ? 330 : -330) - 0, roomO(ev.room)[1] + FLOOR];
    S.ghost.push({ k: q.k, who: q.who, t: T_IDX0 + q.k * T_IDXD + .03, p: gp || ev.p, parlour: !!ev.parlour });
  }
  // dust sources: spilled flour, emptied / torn sacks, the bodies, the flour stores
  const src = [];
  const addS = (p, w, room) => src.push({ p, w, room });
  const ko = roomO('kitchen'), so = roomO('store');
  addS([ko[0] + 380, ko[1] + FLOOR - 60], 1, 'kitchen'); addS([so[0] + 1500, so[1] + FLOOR - 80], 1.2, 'store'); addS([so[0] + 400, so[1] + FLOOR - 60], .8, 'store');
  for (const ev of C.evid) if (ev.kind === 'flour') addS([ev.p[0], ev.p[1] - 30], 2.2, ev.room);
  for (const id of IDS) {
    const w = C.where[id], b = st.body[id], fl = (b.includes('emptied') ? 1.5 : 0) + (b.includes('torn') ? 1 : 0) + (w.kind === 'body' ? .8 : 0);
    if (!fl) continue;
    if (w.kind === 'parlour') { const mk = C.MK && C.MK[id === e.A ? 'A' : 'V']; if (mk) addS([P0[0] + mk.x + mk.w / 2, P0[1] + mk.y + mk.h * .5], fl, 'parlour') }
    else addS([w.p[0], w.p[1] - 80], fl, w.room);
  }
  addS([P0[0] + 700, P0[1] + FLOOR - 20], .6, 'parlour'); addS([P0[0] + 1500, P0[1] + FLOOR - 20], .5, 'parlour');
  const tw = src.reduce((a, s) => a + s.w, 0);
  const ND = 96;
  for (let i = 0; i < ND; i++) {
    const t = T_DUST0 + (T_DUST1 - T_DUST0) * Math.sqrt(H(i * 2.17 + 4)); let r = H(i * 5.3 + 1) * tw, s = src[0];
    for (const c of src) { r -= c.w; if (r <= 0) { s = c; break } }
    S.dust.push({ i, t, p: s.p, room: s.room });
  }
  S.dust.sort((a, b) => a.t - b.t);
  CACHE = C; return C;
}
function levFilter(lv, s) {
  const fl = []; if (lv.grey > .05) fl.push(`grayscale(${Math.min(1, lv.grey)}) brightness(${1 - .25 * lv.grey})`);
  if (lv.halo > .15) fl.push(`drop-shadow(0 0 ${Math.max(1, Math.round(28 * lv.halo * s))}px rgba(255,236,180,${Math.min(.9, lv.halo)}))`);
  if (lv.shadow > .15) fl.push(`drop-shadow(${Math.round(-60 * lv.shadow * s)}px ${Math.round(-30 * lv.shadow * s)}px ${Math.max(1, Math.round(18 * lv.shadow * s))}px rgba(0,0,0,${Math.min(.8, .35 + lv.shadow * .4)}))`);
  return fl.join(' ') || 'none';
}

// ---------- furniture (drawn in room-local coords, the ARAP deed's palette: plum wall, umber floor, cloth) ----------
function furniture(g, room, C) {
  const dk = '#120e12', wd = '#3a2b22', cloth = '#c9b48b';
  g.fillStyle = dk;
  if (room === 'kitchen') { g.fillStyle = wd; g.fillRect(700, 700, 560, 26); g.fillRect(730, 726, 22, 190); g.fillRect(1208, 726, 22, 190); flourStack(g, 260, 3); g.fillStyle = '#1c1517'; g.fillRect(1500, 360, 320, 555) }
  if (room === 'store') { flourStack(g, 1420, 4); flourStack(g, 300, 2); g.fillStyle = wd; g.fillRect(0, 600, 1920, 16) }
  if (room === 'hall') {
    // front door, cupboard under the stairs, clock (pendulum drawn later from the score)
    g.fillStyle = '#1a1214'; g.fillRect(1580, 380, 230, 535); g.fillStyle = '#d9a64a'; g.beginPath(); g.arc(1610, 660, 8, 0, 7); g.fill();
    g.fillStyle = 'rgba(255,214,140,.18)'; g.fillRect(1610, 420, 170, 90);
    g.fillStyle = wd; g.beginPath(); g.moveTo(0, FLOOR); for (let i = 0; i < 9; i++) { g.lineTo(240 + i * 80, FLOOR - i * 100); g.lineTo(320 + i * 80, FLOOR - i * 100) } g.lineTo(980, -40); g.lineTo(1060, -40); g.lineTo(1060, -20); g.lineTo(320, FLOOR); g.closePath(); g.fill();
    g.fillStyle = '#0d0a0c'; g.fillRect(250, 640, 440, 275); g.fillStyle = '#251a17'; g.fillRect(250, 640, 150, 275);
    g.fillStyle = '#2a1f1a'; g.fillRect(1240, 300, 120, 470); g.fillStyle = '#e9dcbc'; g.beginPath(); g.arc(1300, 360, 44, 0, 7); g.fill();
  }
  if (room === 'landing') { g.fillStyle = wd; g.beginPath(); g.moveTo(1060, FLOOR + 165); g.lineTo(1060, FLOOR); for (let i = 0; i < 9; i++) { g.lineTo(1100 + i * 90, FLOOR - i * 100); g.lineTo(1190 + i * 90, FLOOR - i * 100) } g.lineTo(1920, -60); g.lineTo(1920, FLOOR + 165); g.closePath(); g.fill() }
  if (room === 'R') { g.fillStyle = wd; g.fillRect(1380, 700, 420, 215); g.fillStyle = '#6e3a33'; g.fillRect(1380, 690, 420, 40); g.fillStyle = '#2b2018'; g.fillRect(160, 760, 220, 155); g.fillStyle = '#d9a64a'; g.fillRect(250, 800, 40, 30) }
  if (room === 'B') { g.fillStyle = wd; g.fillRect(1260, 720, 600, 195); g.fillStyle = cloth; g.globalAlpha = .4; g.fillRect(1260, 700, 600, 40); g.globalAlpha = 1; g.fillStyle = '#2a2622'; g.fillRect(120, 860, 300, 22); g.beginPath(); g.arc(140, 871, 34, 0, 7); g.arc(400, 871, 34, 0, 7); g.fill() }
  if (room === 'I') { g.fillStyle = cloth; g.globalAlpha = .35; g.fillRect(1250, 850, 560, 65); g.globalAlpha = 1; g.fillStyle = 'rgba(120,140,190,.22)'; g.beginPath(); g.moveTo(300, 120); g.lineTo(700, 120); g.lineTo(640, 340); g.lineTo(360, 340); g.closePath(); g.fill() }
  if (room === 'O') { g.fillStyle = '#2b2230'; g.fillRect(1440, 260, 300, 520); g.fillStyle = 'rgba(200,210,230,.14)'; g.fillRect(1470, 290, 240, 460); g.fillStyle = wd; g.fillRect(230, 700, 40, 215); g.fillStyle = '#7a3b8f'; g.beginPath(); g.ellipse(250, 650, 70, 90, 0, 0, 7); g.fill() }
}
function flourStack(g, x, n) {
  for (let r = 0; r < n; r++) for (let i = 0; i < n - r; i++) {
    const cx = x + (i - (n - r - 1) / 2) * 150, cy = FLOOR - 55 - r * 100;
    g.fillStyle = r % 2 ? '#cdb68c' : '#d8c39b'; g.beginPath(); g.ellipse(cx, cy, 72, 52, 0, 0, 7); g.fill();
    g.strokeStyle = 'rgba(60,40,30,.5)'; g.lineWidth = 3; g.stroke();
  }
}

// ---------- a sack sprite placed in the house ----------
function drawSprite(g, C, id, p, opt) {
  const sp = C.SP[id]; if (!sp) return;
  const lv = C.st.levers[id], f = (1 + .14 * cl(-1, 1, lv.loom) - .22 * lv.shrink) * (opt.scale || 1);
  g.save(); g.translate(p[0], p[1]);
  if (opt.lying) { g.scale(f * 1.2, f * .55); g.translate(0, -sp.w / 2 + 8); g.rotate(opt.lying); g.translate(0, sp.h / 2); g.filter = opt.filter; g.drawImage(sp.c, -sp.ox - sp.w / 2, -sp.oy - sp.h); g.restore(); return }
  g.rotate(opt.lean || 0); g.scale(f * (opt.sx || 1), f * (opt.sy || 1));
  g.filter = opt.filter || levFilter(lv, opt.cs || 1); g.globalAlpha = opt.alpha ?? 1;
  g.drawImage(sp.c, -sp.ox - sp.w / 2, -sp.oy - sp.h);
  g.restore();
}

function draw(g, u, X, K) {
  const C = build(X, K), S = C.score, st = C.st, cam = camera(u), s = cam.s;
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.filter = 'none';
  const wideK = cam.z;                       // 0 in the parlour, 1 at the whole house
  // night outside
  if (wideK > 0.001) { const gr = g.createLinearGradient(0, 0, 0, 1080); gr.addColorStop(0, '#05060c'); gr.addColorStop(1, '#0d0a0c'); g.fillStyle = gr; g.fillRect(0, 0, 1920, 1080) }
  g.save(); g.translate(960, 540); g.scale(s, s); g.translate(-cam.c[0], -cam.c[1]);
  const vis = (x0, y0, x1, y1) => { const a = toScr(cam, [x0, y0]), b = toScr(cam, [x1, y1]); return b[0] > 0 && a[0] < 1920 && b[1] > 0 && a[1] < 1080 };
  // house body, roof, chimney, ground
  if (wideK > 0.001) {
    g.fillStyle = '#060508'; g.fillRect(-4000, HY1, 14000, 2000);
    g.fillStyle = '#0b0809'; g.beginPath(); g.moveTo(HX0 - 180, HY0 + 10); g.lineTo((HX0 + HX1) / 2, HY0 - ROOF); g.lineTo(HX1 + 180, HY0 + 10); g.closePath(); g.fill();
    g.fillRect(HX1 - 900, HY0 - ROOF + 40, 200, ROOF); g.fillStyle = '#17110f'; g.fillRect(HX0, HY0, HX1 - HX0, HY1 - HY0);
  }
  // rooms
  const order = ['I', 'store', 'O', 'R', 'B', 'landing', 'kitchen', 'parlour', 'hall'];
  for (const rm of order) {
    const [ox, oy] = roomO(rm); if (!vis(ox, oy, ox + CW, oy + CH)) continue;
    g.save(); g.beginPath(); g.rect(ox, oy, CW, CH); g.clip(); g.translate(ox, oy);
    if (rm === 'parlour') {
      // the deed's end frame (with its contradiction scanlines) -> the fire's first frame (same levers, no scanlines)
      g.drawImage(u < T_OUT1 ? C.FL : C.FE, 0, 0);
    } else {
      g.drawImage(C.BG, 0, 0); furniture(g, rm, C);
      const occ = IDS.find(id => C.where[id].kind === 'alive' && C.where[id].room === rm);
      const lampOut = C.evid.some(v => v.kind === 'lamp' && v.room === rm);
      const dark = lampOut ? .72 : occ ? 0 : rm === 'hall' || rm === 'kitchen' || rm === 'landing' ? .28 : .5;
      if (dark) { g.fillStyle = `rgba(2,1,4,${dark})`; g.fillRect(0, 0, CW, CH) }
      if (rm === 'hall') pendulum(g, u, S);
    }
    g.restore();
  }
  // evidence: dim where it was left until its index strike; the light finds it, then it stays found
  for (const ev of C.evid) {
    const ix = S.idx.find(q => q.k === ev.k), e = ad(u, ix.t, .025, .32), found = u >= ix.t ? 1 : 0;
    const glowA = (ix.muted ? .45 : 1) * e;
    if (glowA > .01 || found) {
      const r = 260 * (1 + .6 * e), gr = g.createRadialGradient(ev.p[0], ev.p[1] - 40, 4, ev.p[0], ev.p[1] - 40, r);
      gr.addColorStop(0, `rgba(255,220,150,${.18 * found + .55 * glowA})`); gr.addColorStop(1, 'rgba(255,220,150,0)'); g.fillStyle = gr; g.fillRect(ev.p[0] - r, ev.p[1] - 40 - r, 2 * r, 2 * r);
    }
    if (ev.parlour) continue;
    const pop = 1 + .22 * e, b = ev.box, bx = { x: ev.p[0] - b.w * pop / 2, y: ev.p[1] - (ev.p[1] - b.y) * pop, w: b.w * pop, h: b.h * pop };
    g.save(); g.globalAlpha = .5 + .5 * found; try { X.CONSEQS[ev.deed] && X.CONSEQS[ev.deed].trace(g, bx, (11 - ev.k) * .3, K) } catch (err) { } g.restore();
  }
  // the dead: still, grey, where they lie or are hidden; no grain touches them
  for (const id of IDS) {
    const w = C.where[id]; if (w.kind !== 'body') continue;
    const sp = C.SP[id], len = sp.h * 1.1;
    g.fillStyle = 'rgba(251,247,238,.35)'; g.beginPath(); g.ellipse(w.p[0] + 40, w.p[1] + 8, len * .75, 30, 0, 0, 7); g.fill();
    const disg = w.room === 'store' ? 'grayscale(.45) brightness(.8)' : 'grayscale(.85) brightness(.62)';   // in the store it passes for one more flour sack
    if (id === 'O') drawSprite(g, C, id, w.p, { lying: -Math.PI / 2, filter: disg, cs: s });
    else drawSprite(g, C, id, w.p, { sx: 1.22, sy: .5, filter: disg, cs: s });
    if (w.room === 'hall') { const o = roomO('hall'); g.fillStyle = '#251a17'; g.fillRect(o[0] + 470, o[1] + 640, 230, 275); g.fillStyle = 'rgba(0,0,0,.5)'; g.fillRect(o[0] + 470, o[1] + 640, 12, 275) }  // the cupboard door pulled to
  }
  // the living: breath swells them, the index strikes they know make them flinch toward the room it happened in
  for (const id of IDS) {
    const w = C.where[id]; if (w.kind !== 'alive') continue;
    let br = 0; for (const b of S.breath) if (b.id === id) br += ad(u, b.t, b.P * .4, b.P * .35) * (u < b.t + b.P * 1.2 ? 1 : 0);
    let fl = 0, lean = 0; for (const r of S.react) if (r.id === id) { const k = ad(u, r.t, .03, .22) * r.amt; fl += k; lean += k * r.toward }
    fl = Math.tanh(fl); lean = Math.tanh(lean);
    const hold = sm(T_HOLD - .2, T_HOLD + .1, u);  // the silence: everyone holds still, leaning a touch toward the parlour
    const toP = Math.sign(PC[0] - w.p[0]) || 0;
    drawSprite(g, C, id, w.p, { sy: 1 + .03 * br - .05 * fl, sx: 1 - .012 * br + .04 * fl, lean: .16 * lean + .05 * hold * toP, cs: s });
  }
  // contradictions: ghosts, opacity = the glass grain's envelope (with a held after-glow)
  const gn = 1 / Math.sqrt(Math.max(1, S.ghost.length));
  for (const gh of S.ghost) {
    const e = ad(u, gh.t, .05, .5), a = (gh.k === 11 ? 1 : gn) * cl(0, 1, .25 * (u > gh.t - .4 ? sm(gh.t - .4, gh.t, u) : 0) + .55 * e) * (1 - sm(T_IN0, T_IN1 - .2, u));
    if (a < .01) continue;
    if (gh.parlour || C.where[gh.who].kind === 'parlour' && gh.k === 11) {
      const ly = gh.who === C.e.A ? 'A' : 'V', c = ghostCrop(C, ly); if (!c) continue;
      g.save(); g.translate(P0[0] + c.x, P0[1] + c.y); g.globalAlpha = a; g.filter = `sepia(1) hue-rotate(70deg) saturate(2.2) brightness(1.2) drop-shadow(0 0 ${Math.max(2, Math.round(30 * s))}px rgba(120,220,150,.9))`; g.drawImage(c.c, 0, 0); g.restore();
    } else drawSprite(g, C, gh.who, gh.p, { alpha: a, filter: `sepia(1) hue-rotate(70deg) saturate(2.2) brightness(1.15) drop-shadow(0 0 ${Math.max(2, Math.round(30 * s))}px rgba(120,220,150,.9))`, sy: 1 + .04 * Math.sin(u * 9 + gh.k), cs: s });
  }
  // flour dust: one puff per dust grain scheduled; it rises to the ceiling of its room and hangs
  // in the last moments the parlour's motes settle onto the motes the fire will raise (same places, alpha -> 0)
  if (!C.FIREQ) C.FIREQ = Array.from({ length: 500 }, (_, i) => i).sort((a, b) => K.hash(a * .7) - K.hash(b * .7));
  const hand = sm(T_SPARK - .05, DUR, u); let pc = 0;
  const roomHaze = {};
  for (const d of S.dust) {
    if (u < d.t) break; const age = u - d.t, ro = roomO(d.room), ceil = ro[1] + 60;
    roomHaze[d.room] = (roomHaze[d.room] || 0) + Math.min(1, age * 2);
    for (let j = 0; j < 5; j++) {
      const h1 = H(d.i * 13.1 + j), h2 = H(d.i * 7.7 + j * 3.3), h3 = H(d.i * 3.9 + j * 5.1);
      const V = 520 + 680 * h1, rise = V * .8 * (1 - Math.exp(-age / .8));
      const y = Math.max(ceil + h3 * 380, d.p[1] - rise), x = cl(ro[0] + 10, ro[0] + CW - 10, d.p[0] + (h2 - .5) * 900 * (1 - Math.exp(-age / 1.1)) + 40 * Math.sin(u * 1.7 + j + d.i));
      const a = Math.min(1, age * 6) * (.35 + .35 * h3) * (d.room === 'parlour' ? .55 : 1), r = 5 + 11 * h2;
      if (d.room === 'parlour' && hand > 0) {
        const fi = C.FIREQ[pc++ % 500], fx = P0[0] + K.hash(fi * 1.3) * 1920 + Math.sin(fi) * 8, fy = P0[1] + K.hash(fi * 2.7) * 1080, fr = 2 + K.hash(fi) * 3;
        g.fillStyle = `rgba(251,247,238,${a * (1 - hand)})`; g.beginPath(); g.arc(x + (fx - x) * hand, y + (fy - y) * hand, r + (fr - r) * hand, 0, 7); g.fill(); continue;
      }
      g.fillStyle = `rgba(251,247,238,${a})`; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
    }
  }
  for (const [rm, n] of Object.entries(roomHaze)) {
    if (rm === 'parlour') continue; const [ox, oy] = roomO(rm), a = Math.min(.2, n * .012) * (1 - sm(T_IN0, T_IN1, u) * .0);
    const gr = g.createLinearGradient(0, oy, 0, oy + CH); gr.addColorStop(0, `rgba(251,247,238,${a})`); gr.addColorStop(1, 'rgba(251,247,238,0)'); g.fillStyle = gr; g.fillRect(ox, oy, CW, CH);
  }
  // the spark: the thirteenth note; it drops from the parlour lamp toward where the fire will open
  if (u >= S.spark) {
    const v = cl(0, 1, (u - S.spark) / (DUR - S.spark)), x = P0[0] + SPARK0[0] + 14 * Math.sin(v * 7), y = P0[1] + SPARK0[1] + (SPARK1[1] - SPARK0[1]) * v * v;
    const fl = ad(u, S.spark, .02, .08);
    for (let i = 0; i < 6; i++) { const vv = Math.max(0, v - i * .05); g.fillStyle = `rgba(255,${190 - i * 20},80,${.5 - i * .07})`; g.beginPath(); g.arc(P0[0] + SPARK0[0] + 14 * Math.sin(vv * 7), P0[1] + SPARK0[1] + (SPARK1[1] - SPARK0[1]) * vv * vv, 4 - i * .5, 0, 7); g.fill() }
    const gr = g.createRadialGradient(x, y, 1, x, y, 40 + 140 * fl); gr.addColorStop(0, 'rgba(255,250,220,.95)'); gr.addColorStop(.25, `rgba(255,180,70,${.4 + .4 * fl})`); gr.addColorStop(1, 'rgba(255,140,40,0)');
    g.fillStyle = gr; g.fillRect(x - 200, y - 200, 400, 400);
  }
  g.restore();
}
function ghostCrop(C, ly) {
  C.GC = C.GC || {}; if (C.GC[ly]) return C.GC[ly]; const src = C.LY[ly], b = C.MK && C.MK[ly]; if (!src || !b) return null;
  const m = 120, x = Math.max(0, Math.floor(b.x - m)), y = Math.max(0, Math.floor(b.y - m)), w = Math.min(1920 - x, Math.ceil(b.w + 2 * m)), h = Math.min(1080 - y, Math.ceil(b.h + 2 * m));
  const c = mkc(w, h); c.getContext('2d').drawImage(src, -x, -y); return (C.GC[ly] = { c, x, y });
}
function pendulum(g, u, S) {
  // zero crossings at the clock grains; it stops at the extreme after the last tick (the hold)
  const P = .5, t0 = S.clock[0], last = S.clock[S.clock.length - 1];
  const uu = Math.min(u, last + P / 2), ang = .32 * Math.sin(Math.PI * (uu - t0) / P);
  g.save(); g.translate(1300, 410); g.rotate(ang); g.strokeStyle = '#b08a4a'; g.lineWidth = 6; g.beginPath(); g.moveTo(0, 0); g.lineTo(0, 290); g.stroke();
  g.fillStyle = '#d9a64a'; g.beginPath(); g.arc(0, 300, 26, 0, 7); g.fill(); g.restore();
}

function sound(ac, out, t0, X, K) {
  const C = build(X, K), S = C.score, SND = K.SND, mf = m => 440 * Math.pow(2, (m - 69) / 12);
  // the clock
  S.clock.forEach((t, i) => SND.grain(ac, out, t0 + t, { f: i % 2 ? 1900 : 2300, d: .018, a: .06, noise: .5, bp: 2600, att: .05, pan: panOf([roomO('hall')[0] + 1300, 0]) }));
  // the index struck as a scale, one strike per evidence; a refused deed is struck muted
  for (const ix of S.idx) {
    const pan = panOf(ix.p), a = ix.muted ? .05 : .13;
    SND.grain(ac, out, t0 + ix.t, { f: mf(ix.m), d: .32, a, pan, att: .04, type: 'triangle' });
    SND.grain(ac, out, t0 + ix.t, { bp: 2200, q: 2, d: .03, a: .06, pan, att: .1 });
  }
  // the living answer only what they know, in their own voices, as loud as they remember it
  for (const r of S.react) SND.say(ac, out, r.id, t0 + r.t, 'tick', .5 + .6 * r.amt, panOf(r.p));
  for (const b of S.breath) SND.say(ac, out, b.id, t0 + b.t, 'breathe', .28, panOf(b.p));
  // contradictions: a glass glide in the ghost's register
  for (const gh of S.ghost) { const v = SND.VOICE[gh.who]; for (let j = 0; j < 3; j++) SND.grain(ac, out, t0 + gh.t + j * .09, { f: mf(v.base + 24 + j * 5), glide: .35, d: .35, a: .035, pan: panOf(gh.p), att: .7 }) }
  // flour dust: every grain is a puff we see
  for (const d of S.dust) SND.grain(ac, out, t0 + d.t, { bp: 3200 + 2600 * H(d.i * 1.3), q: 3, d: .04 + .06 * H(d.i * 2.9), a: .012 + .028 * (d.t - T_DUST0) / (T_DUST1 - T_DUST0), pan: panOf(d.p), att: .6 });
  // silence, then the thirteenth note: the spark
  SND.grain(ac, out, t0 + S.spark, { f: mf(55 + 36), d: .06, a: .42, att: .02, pan: 0 });
  SND.grain(ac, out, t0 + S.spark, { f: mf(55), d: .28, a: .06, type: 'triangle', att: .04, pan: 0 });
  for (let i = 0; i < 9; i++) SND.grain(ac, out, t0 + S.spark + .03 + .27 * Math.pow(H(i * 4.1), .7), { bp: 2500 + 3500 * H(i * 1.7), q: 4, d: .008 + .01 * H(i), a: .05 + .08 * H(i * 2.2), pan: (H(i * 6.1) - .5) * .3, att: .1 });
}

TRANSITION({
  k: 12, scion: 47, lineage: 'Sound-to-Action — Viseme and Gesture Swarm',
  op: 'Score first: the ledger is turned into one event list (clock ticks, the twelve index entries struck as a descending scale, the living answering the strikes they know, ghost glides, breaths, flour-dust grains, a silence, a thirteenth note); the camera pulls out of the strangling room to the whole house and back, and every light, flinch, ghost, mote and the spark is that list\'s envelope.',
  made: 'The strangling room becomes one cell in a section of nine rooms papered with the deed\'s own mesh-lattice backdrop, furnished in its palette; the sacks outside the parlour are cut from the same ARAP solver with their carried damage, and the evidence is each consequence swarm\'s own trace drawn where it was left. The dead are grey sacks lying where they fell or were hidden, contradictions are green ghosts, and the flour dust is pale motes rising to each ceiling.',
  moved: 'An event score computed from the ledger: each grain\'s attack-decay envelope lights an evidence item, makes a knowing sack flinch toward that room (amplitude = its memory weight), swells a breath, raises a ghost or releases a puff of flour. A hall clock\'s pendulum crosses zero on its ticks and stops for the silence; the thirteenth note drops a spark from the parlour lamp.',
  dur: DUR,
  draw(g, u, X, K) { draw(g, u, X, K) },
  sound(ac, out, t0, X, K) { sound(ac, out, t0, X, K) },
});
})();
