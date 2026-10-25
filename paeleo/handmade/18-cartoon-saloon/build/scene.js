/* SCION 18 · the shot: acting timeline (performance editor), gait, compositing, measurement, cards.
   Time base: film frame f (24 fps); scene frame i = f - 72 is score frame i. The dog's x IS the score's x. */
'use strict';
const FPS = 24, TITLE = 72, SCENE = 768, END = 72, TOTAL = TITLE + SCENE + END;
const VOICE = [ // syllables [t0, t1, loudness]; shared with sound.py through the driver
  { line: 'Come here.', kind: 'call', syl: [[1.02, 1.30, 1], [1.42, 1.88, 1]] },
  { line: 'Come here!', kind: 'call', syl: [[3.45, 3.72, 1.1], [3.82, 4.34, 1.1]] },
  { line: "It's all right.", kind: 'soft', syl: [[7.46, 7.62, 1], [7.74, 8.08, 1], [8.18, 8.80, 1]] },
  { line: "It's all right.", kind: 'soft', syl: [[10.46, 10.62, 1], [10.74, 11.06, 1], [11.16, 11.62, 1]] },
  { line: 'Come in.', kind: 'soft', syl: [[26.42, 26.68, 1], [26.80, 27.32, 1]] },
];
// keyed curve with smooth segments
function key(t, ks) { if (t <= ks[0][0]) return ks[0][1]; for (let i = 1; i < ks.length; i++) if (t <= ks[i][0]) return lerp(ks[i - 1][1], ks[i][1], ss(ks[i - 1][0], ks[i][0], t)); return ks[ks.length - 1][1]; }
const onTwos = t => Math.floor(t * 12) / 12; // drawn turns are timed on twos
function mouthAt(t) { for (const v of VOICE) for (const [a, b, l] of v.syl) if (t >= a && t <= b) { const u = (t - a) / (b - a); return Math.sin(Math.PI * Math.min(1, u * 1.3)) * (v.kind === 'call' ? 1 : 0.45) * l; } return 0; }

let GAIT = null, EVENTS = [];
function viewU(t) {
  if (t < 3.46) return 0;
  if (t < 3.74) return 3 * clamp((onTwos(t) - 3.46) / 0.26);
  if (t < 8.12) return 3;
  if (t < 8.6) return 3 * (1 - clamp((onTwos(t) - 8.12) / 0.42));
  return 0;
}
function lieAt(t) { return t < 10 ? key(t, [[4.2, 0], [4.85, 1], [7.58, 1], [8.08, 0]]) : key(t, [[23.72, 0], [24.4, 1]]); }

function initGait() { // feet planted on the boards: stance feet never move in the world; swing feet land ahead
  const F = SCORE.frames, stride = 0.34, beta = 0.62;
  const home = [-20, -16, 20, 16], off = [0.25, 0.75, 0, 0.5], far = [0, 1.5, 0, 1.5];
  GAIT = []; EVENTS = [];
  let Dist = 0, wasFree = false; const plant = [0, 0, 0, 0], start = [0, 0, 0, 0], tgt = [0, 0, 0, 0], last = [0, 0, 0, 0], prevP = off.slice();
  for (let i = 0; i < F.length; i++) {
    const t = F[i].t, x = F[i].dog.x, dx = i ? x - F[i - 1].dog.x : 0, mv = F[i].dog.act.moving;
    const free = viewU(t) === 0 && lieAt(t) === 0;
    if (!free) { GAIT.push(null); wasFree = false; continue; }
    if (!wasFree) for (let k = 0; k < 4; k++) { plant[k] = last[k] = tgt[k] = start[k] = x + home[k] / 100; }
    wasFree = true;
    Dist += Math.abs(dx);
    const d = Math.sign(dx);
    const feet = [];
    for (let k = 0; k < 4; k++) {
      const p = ((Dist / stride + off[k]) % 1 + 1) % 1, pp = prevP[k];
      let fx = last[k], lift = 0;
      if (dx !== 0) {
        if (p < beta) {
          if (pp >= beta) { plant[k] = tgt[k]; if (mv > 0.15) EVENTS.push({ t, type: 'paw', leg: k, x }); }
          fx = plant[k];
        } else {
          if (pp < beta) start[k] = last[k];
          const s = (p - beta) / (1 - beta);
          tgt[k] = x + d * (1 - p) * stride + home[k] / 100 + d * stride * beta / 2;
          fx = lerp(start[k], tgt[k], s * s * (3 - 2 * s));
          lift = Math.sin(Math.PI * s) * 6 * clamp(mv * 1.4);
          plant[k] = fx;
        }
        prevP[k] = p;
      }
      last[k] = fx;
      feet.push([(fx - x) * 100, far[k], lift]);
    }
    GAIT.push(feet);
  }
}

function dogPose(i) {
  const F = SCORE.frames[i], t = F.t, A = F.dog.act;
  const P = { x: F.dog.x, t, u: viewU(t), lie: lieAt(t), crouch: 0, h: 0.9, pitch: -4, head: 'prof', ear: 0.85, eye: 1, brow: 0, mouth: 0, T: 0.45, wag: 0, bob: 0 };
  const breathe = 0.35 * Math.sin(t * 2 * Math.PI * 0.45);
  const blink = (tt) => { const ph = (tt % 3.3) / 3.3; return ph > 0.96 ? 0.1 : 1; };
  if (t < 3.46) { // watch → retreat → watch
    P.crouch = key(t, [[0, 0.02], [1.0, 0.03], [1.28, 0.9], [2.3, 0.85], [2.65, 0.25], [3.2, 0.08]]);
    P.h = key(t, [[0, 0.9], [1.0, 0.9], [1.22, 0.15], [2.25, 0.2], [2.55, 0.75], [3.0, 0.88], [3.42, 0.8], [3.46, 0.55]]);
    P.pitch = key(t, [[0, -4], [1.0, -4], [1.22, 14], [2.3, 12], [2.6, 0], [3.0, -4], [3.42, -2], [3.46, 14]]);
    P.ear = key(t, [[0, 0.85], [1.02, 0.9], [1.16, 0.05], [2.3, 0.1], [2.7, 0.7], [3.2, 0.8], [3.42, 0.6], [3.46, 0.1]]);
    P.eye = t > 1.05 && t < 2.5 ? 1.25 : blink(t + 1.1);
    P.brow = key(t, [[1.0, 0], [1.2, 1], [2.4, 1], [2.8, 0.3]]);
    P.T = A.tail; P.bob = breathe * (1 - A.moving);
  } else if (t < 8.6) { // refusal: turned back, lies down with its back to the door; then turns back to look
    P.T = key(t, [[3.42, 0.8], [3.9, 1.05], [7.46, 1.0], [8.25, 0.95], [8.6, 0.45]]);
    P.ear = key(t, [[3.46, 0.1], [4.8, 0.15], [6.2, 0.15], [6.3, 0.55], [6.55, 0.2], [7.05, 0.25], [7.2, 0.6], [7.4, 0.45], [7.5, 0.9]]);
    P.h = key(t, [[3.46, 0.3], [3.9, 0.2], [5.4, 0.15], [6.0, 0.0]]);
    P.pitch = key(t, [[3.46, 14], [4.2, 16], [6.0, 22]]);
    const u = P.u;
    if (u > 0 && u < 0.5) P.head = 'prof';
    else if (u >= 0.5 && u < 1.5) { P.head = 'back34'; P.headFace = 1; }
    else if (u >= 1.5 && u < 2.5) { P.head = 'rear'; P.headFace = 1; }
    else if (u >= 2.5) { P.head = 'back34'; P.headFace = -1; }
    if (t >= 7.46) { // the head comes round to the door first, over the shoulder
      P.ear = key(t, [[7.46, 0.6], [7.56, 0.95], [8.6, 0.85]]);
      P.eye = 1; P.brow = 0.2;
      if (u >= 2.5) { P.head = 'front34'; P.headFace = 1; P.headFront = true; P.headPivot = lp([12, 58], [12, 33], P.lie); P.pitch = key(t, [[7.46, 10], [7.6, 2], [8.1, -2]]); }
      else if (u >= 0.5) { P.head = 'prof'; P.headFace = 1; P.headFront = u >= 1.5 ? false : false; P.h = 0.85; P.pitch = -2; }
      else { P.head = 'prof'; P.h = 0.85; P.pitch = -3; }
    }
    if (u > 0 && u < 3) { // feet step round during the turn: each lifts in turn
      const s = t < 5 ? clamp((t - 3.46) / 0.4) : clamp((t - 8.12) / 0.46);
      P.turnLift = [0, 1, 2, 3].map(k => (k < 2 ? 7 : 3) * Math.sin(Math.PI * clamp((s - (k < 2 ? 0.1 : 0.45) - (k % 2) * 0.1) / 0.45))); // forefeet swing round first
    }
  } else if (t < 14.708) { // watching, the door open, the hand low, the soft voice
    P.h = key(t, [[8.6, 0.85], [9.2, 0.9], [11.0, 0.9], [11.4, 0.78], [12.4, 0.82], [13.6, 0.86]]);
    P.pitch = key(t, [[8.6, -3], [10.9, -3], [11.3, 7], [12.2, 5], [12.8, -2]]);
    P.ear = key(t, [[8.6, 0.85], [10.4, 0.8], [10.55, 1], [10.9, 0.75], [12.5, 0.7], [13.9, 0.75]]);
    P.T = key(t, [[8.6, 0.45], [11.8, 0.42], [13.8, 0.35]]); P.wag = key(t, [[10.6, 0], [11.2, 0.08], [13.0, 0.05]]);
    P.eye = blink(t); P.bob = breathe; P.brow = key(t, [[10.5, 0.3], [11.4, 0.5], [12.6, 0.1]]);
  } else if (t < 23.79) { // coming, head low below the line of the back
    P.h = key(t, [[14.708, 0.75], [14.95, 0.05], [23.79, 0.05]]);
    P.pitch = key(t, [[14.708, 2], [14.95, 18], [22.8, 16], [23.6, 12]]);
    P.ear = key(t, [[14.708, 0.75], [15.0, 0.35], [20.0, 0.4], [23.0, 0.5]]);
    P.T = key(t, [[14.708, 0.35], [15.2, 0.5], [23.0, 0.5]]); P.wag = 0.12 + 0.04 * Math.sin(t * 0.7);
    P.crouch = 0.15; P.eye = Math.min(0.85, blink(t + 0.7)); P.brow = 0.25;
    P.bob = -0.6 * Math.abs(Math.sin(t * 5.2)) * A.moving;
  } else { // lies across the sill; hears "come in": looks in; settles and stays
    P.h = key(t, [[23.79, 0.1], [24.45, 0.55], [25.4, 0.6], [26.1, 0.3], [26.4, 0.32], [26.62, 0.88], [28.3, 0.85], [28.9, 0.0]]);
    P.pitch = key(t, [[23.79, 16], [24.45, 2], [25.4, 0], [26.1, 8], [26.4, 8], [26.62, 3], [28.3, 2], [28.9, 8]]);
    P.ear = key(t, [[23.79, 0.5], [25.0, 0.45], [26.4, 0.45], [26.5, 1], [28.3, 0.9], [29.0, 0.35]]);
    P.T = 0.42; P.wag = key(t, [[26.4, 0.05], [26.7, 0.5], [28.2, 0.45], [29.0, 0.05]]); P.tailCurl = 10;
    P.eye = t > 29.3 ? key(t, [[29.3, 0.6], [29.8, 0]]) : t > 28.9 ? 0.6 : blink(t);
    if (t >= 26.62 && t < 28.3) { P.head = 'in34'; P.headFace = 1; P.headFront = true; }
    P.bob = 0;
  }
  if (P.u === 0 && P.lie === 0 && GAIT[i]) P.feet = GAIT[i];
  return P;
}

function personPose(i) {
  const F = SCORE.frames[i], t = F.t, p = F.person;
  return {
    x: p.x, sit: ss(0, 1, p.sit), reach: p.reach, low: p.low, mouth: mouthAt(t),
    lean: key(t, [[0, 0], [0.95, 0], [1.1, 7], [2.2, 5], [2.5, 0], [3.35, 0], [3.6, 14], [4.5, 12], [4.8, 0], [6.5, 3], [7.0, 10]]),
    nod: key(t, [[6.8, 0], [7.4, 10], [9.4, 12], [12, 8], [20, 10], [26.4, 6], [26.8, 12]]),
    blink: ((t + 0.4) % 4.1) / 4.1 > 0.965 ? 1 : 0,
    bob: (t > 5.35 && t < 6.2) ? 1.2 * Math.abs(Math.sin((t - 5.35) * 7.4)) : 0,
  };
}
function doorOpen(t) { return t < 6.2 ? 0.22 : key(t, [[6.2, 0.22], [6.75, 1.03], [7.0, 1.0]]); }

let DOGC = null, DCTX = null, CTX = null;
async function initScene() {
  for (const f of ['800 54px "Big Shoulders Display"', '400 26px Literata', 'italic 400 22px Literata', '400 17px Literata']) { try { await document.fonts.load(f); } catch (e) {} }
  CTX = document.getElementById('c').getContext('2d');
  DOGC = mk(); DCTX = DOGC.getContext('2d', { willReadFrequently: true });
  initWorld(); initGait();
  return true;
}

function measureDog(bodyX) { // pixel measurements of the dog layer (alpha > 128), scanned in screen px, reported in WORLD px
  const im = DCTX.getImageData(0, 0, W, H).data, z = CAM.z, tx = CAM.tx, ty = CAM.ty;
  let n = 0, sxm = 0, sym = 0, x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1, fn = 0, fx = 0, col = null;
  const bx = Math.round(z * bodyX + tx), pb0 = z * (FLOOR - 20) + ty, pb1 = z * FLOOR + ty;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const a = im[(y * W + x) * 4 + 3]; if (a <= 128) continue;
    n++; sxm += x; sym += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    if (y >= pb0 && y < pb1) { fn++; fx += x; }                       // the paw band, 0..20 world px above the boards
    if (col === null && Math.abs(x - bx) <= 2 * z) col = y;          // top of the body over the body centre
  }
  const wx = v => (v - tx) / z, wy = v => (v - ty) / z;
  return n ? { cx: wx(sxm / n), cy: wy(sym / n), x0: wx(x0), x1: wx(x1), y0: wy(y0), y1: wy(y1), area: n / (z * z), feetX: fn ? wx(fx / fn) : null, backTopCol: col === null ? null : wy(col),
    screen: { cx: sxm / n, cy: sym / n } } : null;
}
function camAt(t) { const u = ss(21.6, 25.0, t), z = 1 + 0.85 * u, fx = lerp(640, 360, u), fy = lerp(360, 470, u); return { z, tx: 640 - z * fx, ty: 360 - z * fy }; }

function renderScene(i) {
  const ctx = CTX, t = SCORE.frames[i].t, open = doorOpen(t);
  LINE_LOG.sum = 0; LINE_LOG.n = 0;
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
  Object.assign(CAM, camAt(t)); const L = worldLayers();
  const cam = () => ctx.setTransform(CAM.z, 0, 0, CAM.z, CAM.tx, CAM.ty), id = () => ctx.setTransform(1, 0, 0, 1, 0, 0);
  id(); ctx.drawImage(L.ext, 0, 0); cam(); drawStars(ctx, t);
  id(); ctx.drawImage(L.int, 0, 0); cam();
  const flick = drawHearth(ctx, t);
  ctx.fillStyle = `rgba(14,10,32,${0.5 * clamp((1 - open) / 0.78)})`; ctx.fillRect(0, 150, XW0, 460); // the room before the door opens is dim
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = `rgba(255,170,90,${0.13 * open})`; ctx.fillRect(-10, 150, XW0 + 10, 460); ctx.restore();
  drawDoor(ctx, open);
  id(); ctx.drawImage(L.arch, 0, 0); cam();
  drawLight(ctx, open, flick);
  const pq = personPose(i); const pg = drawPerson(ctx, pq);
  // dog on its own layer: drawn, measured, then graded by the compositing palette and laid down with a contact shadow
  const P = dogPose(i);
  DCTX.setTransform(1, 0, 0, 1, 0, 0); DCTX.clearRect(0, 0, W, H); DCTX.setTransform(CAM.z, 0, 0, CAM.z, CAM.tx, CAM.ty);
  const lineBefore = LINE_LOG.n, lineSumBefore = LINE_LOG.sum;
  const geo = drawDog(DCTX, P);
  const dogLine = (LINE_LOG.sum - lineSumBefore) / Math.max(1, LINE_LOG.n - lineBefore);
  const m = measureDog(sx(P.x));
  const warm = warmAt(m ? m.cx : sx(P.x), open);
  DCTX.save(); DCTX.globalCompositeOperation = 'source-atop';
  DCTX.setTransform(1, 0, 0, 1, 0, 0);
  DCTX.fillStyle = `rgba(36,44,104,${0.30 * (1 - warm)})`; DCTX.fillRect(0, 0, W, H);
  DCTX.fillStyle = `rgba(255,176,90,${0.16 * warm})`; DCTX.fillRect(0, 0, W, H);
  DCTX.restore();
  if (m) { ctx.save(); ctx.fillStyle = 'rgba(10,6,12,0.35)'; ctx.beginPath(); ctx.ellipse(sx(P.x) + (geo.fam === 'L' ? 0 : 0), 600, (P.lie > 0.5 ? 46 : 36) * K, 4.5, 0, 0, 6.283); ctx.fill(); ctx.restore(); }
  id(); ctx.drawImage(DOGC, 0, 0);
  // grade: cool dusk vignette, then paper grain (screen space, once)
  const vg = ctx.createRadialGradient(640, 400, 300, 640, 400, 820); vg.addColorStop(0, 'rgba(20,16,40,0)'); vg.addColorStop(1, 'rgba(20,16,40,0.45)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.drawImage(TEX.paper, 0, 0); ctx.restore();
  const facing = Math.abs(geo.tip[0] - geo.skullC[0]) < 3 ? 0 : (geo.tip[0] < geo.skullC[0] ? 1 : -1);
  return { i, t, x_score: P.x, cam: { z: CAM.z, tx: CAM.tx, ty: CAM.ty }, meas: m, head: { tip: geo.tip, c: geo.skullC, top: geo.headTop, mode: P.head }, backTop: geo.backTop, facing, fam: geo.fam, u: P.u, lie: P.lie, dogLineMean: dogLine, hand: pg.hand };
}

function card(ctx, lines, sub, t01) {
  ctx.fillStyle = '#17142a'; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.globalAlpha = 0.5; ctx.drawImage(LAYERS.ext1, 0, 0); ctx.restore();
  ctx.fillStyle = 'rgba(23,20,42,0.72)'; ctx.fillRect(0, 0, W, H);
  triskele(ctx, 640, 170, 34, 'rgba(217,162,74,0.85)', 2.2, 900);
  const a = clamp(Math.min(t01 / 0.15, (1 - t01) / 0.12));
  ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.fillStyle = '#f2e3c4';
  let y = 290;
  for (const [txt, font, gap] of lines) { ctx.font = font; ctx.fillText(txt, 640, y); y += gap; }
  if (sub) { ctx.font = '400 17px Literata'; ctx.fillStyle = '#d8c7a6'; for (const s of sub) { ctx.fillText(s, 640, y); y += 27; } }
  ctx.globalAlpha = 1;
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.drawImage(TEX.paper, 0, 0); ctx.restore();
}
function renderFrame(f) {
  CTX.setTransform(1, 0, 0, 1, 0, 0); if (f < TITLE || f >= TITLE + SCENE) Object.assign(CAM, { z: 1, tx: 0, ty: 0 });
  if (f < TITLE) { card(CTX, [['PAE-02 · SCION 18 · Cartoon Saloon', '800 54px "Big Shoulders Display"', 56], ['Painterly Puppet Discipline', '400 26px Literata', 50], ['The threshold, handmade', 'italic 400 22px Literata', 40]], null, f / TITLE); return null; }
  if (f >= TITLE + SCENE) {
    card(CTX, [['What it is made of', '800 40px "Big Shoulders Display"', 52]], [
      'Every drawing was written point by point for this film: a turnaround and expression sheet',
      'for the dog (profile stand, crouch and lie; three-quarter rear, rear; five heads), two drawings of the woman,',
      'a house with patterned walls. Lines are tapered brush ribbons; colour is synthesized watercolour wash.',
      'Turns, expressions and lying down are drawing substitution and in-betweens of those drawings;',
      'a selective rig moves only legs, tail, neck and the woman’s arm. No footage or found images are used.',
      'The sound is synthesized. Dog choices and timing: the PAELEO threshold score.'], (f - TITLE - SCENE) / END);
    return null;
  }
  return renderScene(f - TITLE);
}
if (typeof window !== 'undefined') Object.assign(window, { initScene, renderFrame, renderScene, dogPose, VOICE, TOTAL, TITLE, SCENE, getEvents: () => EVENTS, getGait: () => GAIT });
