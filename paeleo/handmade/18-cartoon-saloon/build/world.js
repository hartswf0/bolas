/* SCION 18 · the world, painted layer by layer: exterior dusk, the patterned interior, the cut-away wall and porch.
   Static layers are painted once into their own canvases (layered drawings); per-frame layers are the door leaf,
   the light that comes out of the door, the hearth flicker and the stars. */
'use strict';
const LAYERS = {};
function mk(w = W, h = H) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
const XW0 = sx(WALL[0]), XW1 = sx(WALL[1]);            // wall band in px (404.6 .. 444.2)
const LINTEL = sy(2.05), CEIL = sy(2.45), PORCH_END = sx(4.95), POST = sx(4.62);
const rect = (x0, y0, x1, y1) => [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];

function spiral(ctx, cx, cy, r, turns, rot, color, w, seed) {
  const pts = []; const n = 40;
  for (let i = 0; i <= n; i++) { const u = i / n, a = rot + u * turns * 6.283, rr = r * (1 - u * 0.92); pts.push([cx + rr * Math.cos(a), cy + rr * Math.sin(a)]); }
  brush(ctx, pts, false, w, color, seed);
}
function triskele(ctx, cx, cy, r, color, w, seed) {
  for (let k = 0; k < 3; k++) { const a = k * 2.094 - 1.57; spiral(ctx, cx + r * 0.5 * Math.cos(a), cy + r * 0.5 * Math.sin(a), r * 0.5, 1.3, a + 3.14, color, w, seed + k); }
}
function gradRect(ctx, x0, y0, x1, y1, stops, vertical = true) {
  const g = vertical ? ctx.createLinearGradient(0, y0, 0, y1) : ctx.createLinearGradient(x0, 0, x1, 0);
  for (const [o, c] of stops) g.addColorStop(o, c);
  ctx.fillStyle = g; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
}
function washOver(ctx, x0, y0, w, h, k, a, mode = 'multiply') {
  ctx.save(); ctx.globalCompositeOperation = mode; ctx.globalAlpha = a; const p = TEX.pat[k]; p.setTransform(new DOMMatrix().translate(x0 * 0.7, y0 * 0.3));
  ctx.fillStyle = p; ctx.fillRect(x0, y0, w, h); ctx.restore();
}

function paintExterior() {
  const c = mk(), x = c.getContext('2d'); x.setTransform(CAM.z, 0, 0, CAM.z, CAM.tx, CAM.ty);
  gradRect(x, 0, 0, W, FLOOR, [[0, PAL.skyTop], [0.45, PAL.skyMid], [0.78, PAL.skyLow], [0.93, PAL.skyHorizon], [1, '#f0c48a']]);
  washOver(x, 0, 0, W, FLOOR, 0, 0.5);
  x.fillStyle = '#1d2033'; x.fillRect(0, FLOOR - 2, W + 20, H - FLOOR + 40); // the dark yard below the horizon
  // moon with a painted halo
  const mx = 1068, my = 96;
  const hg = x.createRadialGradient(mx, my, 10, mx, my, 120); hg.addColorStop(0, 'rgba(250,236,200,0.35)'); hg.addColorStop(1, 'rgba(250,236,200,0)');
  x.fillStyle = hg; x.fillRect(mx - 130, my - 130, 260, 260);
  const mp = []; for (let k = 0; k < 40; k++) { const a = k / 40 * 6.283; mp.push([mx + 24 * Math.cos(a), my + 24 * Math.sin(a)]); }
  ink(x, mp, { fill: PAL.moon, line: '#b9a27a', lw: 1.6, seed: 31, tex: 2, texA: 0.35 });
  // far hills, two bands
  const hill = (y0, amp, ph, col, seed) => { const p = [[440, FLOOR]]; for (let X = 440; X <= W + 10; X += 40) p.push([X, y0 - amp * (0.5 + 0.5 * Math.sin(X / 170 + ph)) - amp * 0.4 * Math.sin(X / 61 + ph * 2)]); p.push([W + 10, FLOOR]); ink(x, crSample(p, true, 6), { fill: col, line: '#151833', lw: 1.4, seed, tex: 1, texA: 0.5 }); };
  hill(520, 34, 1.3, '#3a3863', 32); hill(552, 22, 4.1, PAL.hill, 33);
  // stylised trees: trunks + round canopies carrying spiral pattern
  const tree = (cx, base, r, seed) => {
    ink(x, rect(cx - 5, base - r * 1.2, cx + 5, base), { fill: '#1a2a30', line: PAL.treeLine, lw: 1.5, seed, tex: 1 });
    const cp = []; for (let k = 0; k < 14; k++) { const a = k / 14 * 6.283; const rr = r * (1 + 0.08 * Math.sin(k * 2.7 + seed)); cp.push([cx + rr * Math.cos(a), base - r * 1.5 + rr * 1.05 * Math.sin(a)]); }
    ink(x, crSample(cp, true, 6), { fill: PAL.tree, line: PAL.treeLine, lw: 1.8, seed, tex: 0, texA: 0.6 });
    x.save(); polyPath(x, crSample(cp, true, 6)); x.clip();
    for (let k = 0; k < 7; k++) { const a = k * 0.9 + seed; spiral(x, cx + r * 0.55 * Math.cos(a), base - r * 1.5 + r * 0.55 * Math.sin(a), r * 0.32, 1.2, a, 'rgba(70,110,110,0.55)', 1.3, seed + k); }
    x.restore();
  };
  tree(640, 548, 46, 41); tree(860, 540, 62, 42); tree(1250, 545, 54, 43); tree(1010, 556, 30, 44);
  // the far railing of the porch (behind the dog): low, dark, sparse
  x.save(); x.globalAlpha = 0.8;
  ink(x, rect(XW1, 494, POST, 501), { fill: '#3a3047', line: '#1c1726', lw: 1.4, seed: 45, tex: 1 });
  for (let X = XW1 + 30; X < POST - 8; X += 46) ink(x, rect(X - 3, 501, X + 3, 590), { fill: '#352b42', line: '#1c1726', lw: 1.2, seed: 46 + X, tex: 1 });
  x.restore();
  LAYERS.ext = c;
}

function paintInterior() {
  const c = mk(), x = c.getContext('2d'); x.setTransform(CAM.z, 0, 0, CAM.z, CAM.tx, CAM.ty);
  // back wall: deep red wash with an ochre triskele wallpaper
  ink(x, rect(-4, CEIL, XW0, 600), { fill: PAL.wallIn, line: '#3b1410', lw: 0, tex: 0, texA: 0.6 });
  x.save(); x.beginPath(); x.rect(0, CEIL, XW0, 470 - CEIL); x.clip();
  for (let row = 0, Y = CEIL + 30; Y < 470; Y += 58, row++) for (let X = (row % 2) * 34 + 18; X < XW0; X += 68) {
    triskele(x, X, Y, 13, 'rgba(217,162,74,0.7)', 1.5, X * 7 + Y);
    x.fillStyle = 'rgba(217,162,74,0.55)'; x.beginPath(); x.arc(X + 34, Y + 29, 2.2, 0, 6.283); x.fill();
  }
  x.restore();
  // wainscot boards (green) with a knot band
  ink(x, rect(-4, 470, XW0, 590), { fill: '#3e5b4a', line: '#16281f', lw: 1.6, seed: 51, tex: 1 });
  for (let X = 10; X < XW0; X += 30) brush(x, [[X, 476], [X + 1, 588]], false, 1.2, 'rgba(22,40,31,0.7)', 52 + X);
  ink(x, rect(-4, 466, XW0, 476), { fill: '#b98a45', line: '#4a3015', lw: 1.4, seed: 53, tex: 2 });
  // a shelf with a jug and two bowls
  ink(x, rect(40, 352, 168, 360), { fill: '#6d4a2c', line: '#2b1c10', lw: 1.6, seed: 54, tex: 1 });
  ink(x, crSample([[70, 351], [64, 330], [70, 312], [80, 306], [90, 312], [96, 330], [90, 351]], true, 6), { fill: '#d6c7a3', line: '#4a3b28', lw: 1.6, seed: 55, tex: 2 });
  brush(x, crSample([[94, 318], [104, 322], [100, 338], [93, 340]], false, 6), false, 1.8, '#4a3b28', 56);
  for (const bx of [118, 146]) ink(x, crSample([[bx - 13, 344], [bx + 13, 344], [bx + 9, 351], [bx - 9, 351]], true, 4), { fill: '#7c8f9a', line: '#2c3a42', lw: 1.4, seed: 57 + bx, tex: 2 });
  // hearth at the left edge (stone arch); its fire is drawn per frame
  ink(x, crSample([[-6, 590], [-6, 400], [30, 392], [70, 404], [80, 590]], true, 6), { fill: '#6b6058', line: '#2a221d', lw: 2, seed: 58, tex: 1 });
  ink(x, crSample([[6, 590], [8, 470], [36, 452], [62, 470], [64, 590]], true, 6), { fill: '#1c1210', line: '#0d0807', lw: 1.6, seed: 59, tex: null });
  // floor boards + rug with a zigzag border
  ink(x, rect(-4, 590, XW0 + 2, 608), { fill: PAL.floorIn, line: '#24160c', lw: 1.6, seed: 60, tex: 1 });
  ink(x, rect(96, 593, 384, 604), { fill: PAL.rug, line: '#132520', lw: 1.4, seed: 61, tex: 2 });
  const zz = []; for (let X = 100; X <= 380; X += 7) zz.push([X, (X / 7) % 2 < 1 ? 596 : 601]);
  brush(x, zz, false, 1.4, '#d9a24a', 62);
  // ceiling beam
  ink(x, rect(-4, CEIL - 6, XW0, CEIL + 10), { fill: '#4a3022', line: '#1d120b', lw: 1.8, seed: 63, tex: 1 });
  // stool where the person will sit
  const stx = sx(personX(-1.25)); // under the sitting person (person.js mapping)
  ink(x, rect(stx - 22, 526, stx + 24, 534), { fill: '#7b5532', line: '#2b1c10', lw: 1.6, seed: 64, tex: 1 });
  for (const lx of [stx - 18, stx + 15]) ink(x, rect(lx, 534, lx + 5, 593), { fill: '#6a4629', line: '#2b1c10', lw: 1.4, seed: 65 + lx, tex: 1 });
  // foundation in section under the floor
  ink(x, rect(-4, 608, XW1, 724), { fill: '#2b2424', line: '#120e0e', lw: 1.8, seed: 66, tex: 1 });
  for (let r = 0; r < 4; r++) for (let X = (r % 2) * 22; X < XW1; X += 44) ink(x, crSample(rect(X + 3, 614 + r * 27, X + 40, 636 + r * 27), true, 3), { fill: '#3a3131', line: '#151010', lw: 1.2, seed: 67 + X + r * 99, tex: 2 });
  LAYERS.int = c;
}

function paintArchitecture() {
  const c = mk(), x = c.getContext('2d'); x.setTransform(CAM.z, 0, 0, CAM.z, CAM.tx, CAM.ty);
  // roof in section over the room and the porch roof
  ink(x, crSample([[-10, CEIL - 6], [-10, -10], [180, -10], [XW1 + 30, 118], [PORCH_END + 40, 170], [PORCH_END + 40, 186], [XW1, 150], [XW0, CEIL - 6]], true, 2), { fill: '#3b2b2e', line: '#170f12', lw: 2.2, seed: 70, tex: 1, texA: 0.6 });
  // thatch: rows of short tapered strokes over the roof (clipped), the house's hand-made texture
  const roofP = crSample([[-10, CEIL - 6], [-10, -10], [180, -10], [XW1 + 30, 118], [PORCH_END + 40, 170], [PORCH_END + 40, 186], [XW1, 150], [XW0, CEIL - 6]], true, 2);
  x.save(); polyPath(x, roofP); x.clip();
  for (let r = 0; r < 14; r++) for (let X = -20 + (r % 2) * 9; X < PORCH_END + 40; X += 18) {
    const yTop = X < 180 ? -10 : X < XW1 + 30 ? -10 + (X - 180) * (128 / (XW1 - 150)) : 118 + (X - XW1 - 30) * (52 / (PORCH_END + 10 - XW1));
    const Y = yTop + 6 + r * 12; brush(x, [[X, Y], [X + 3, Y + 9], [X + 5, Y + 16]], false, 1.4, `rgba(${150 + (r * 7) % 40},${110 + (X * 3) % 30},80,0.35)`, 300 + r * 97 + X);
  }
  x.restore();
  // shingle scallops on the porch roof edge
  for (let X = XW1 + 10; X < PORCH_END + 40; X += 18) {
    const y = 118 + (X - XW1 - 30) * (52 / (PORCH_END + 10 - XW1)) + 22;
    brush(x, crSample([[X - 9, y - 6], [X, y + 3], [X + 9, y - 6]], false, 6), false, 1.4, 'rgba(200,150,120,0.45)', 71 + X);
  }
  // porch ceiling (soffit) line
  brush(x, [[XW1, 152], [PORCH_END + 40, 188]], false, 2.2, '#170f12', 72);
  // the cut wall above the door: hatched section
  ink(x, rect(XW0, CEIL - 6, XW1, LINTEL), { fill: PAL.section, line: '#120c0c', lw: 2.2, seed: 73, tex: 1 });
  x.save(); x.beginPath(); x.rect(XW0, CEIL - 6, XW1 - XW0, LINTEL - CEIL + 6); x.clip();
  for (let k = -20; k < 30; k++) brush(x, [[XW0 + k * 8, CEIL - 6], [XW0 + k * 8 + 40, LINTEL]], false, 1, 'rgba(160,110,90,0.35)', 74 + k);
  x.restore();
  // lintel board
  ink(x, rect(XW0 - 8, LINTEL - 10, XW1 + 8, LINTEL + 4), { fill: '#8a6a44', line: PAL.frameLine, lw: 1.8, seed: 75, tex: 1 });
  // the far jamb reveal: the door frame, carved with a running spiral
  ink(x, rect(XW0, LINTEL + 4, XW1, 591), { fill: PAL.frame, line: PAL.frameLine, lw: 2, seed: 76, tex: 2, texA: 0.5 });
  for (let Y = LINTEL + 22, k = 0; Y < 580; Y += 26, k++) spiral(x, (XW0 + XW1) / 2, Y, 9, 1.4, k * 3.14, 'rgba(90,55,25,0.55)', 1.3, 77 + k);
  // porch floor: top surface band of planks + fascia + lattice skirt
  x.save(); x.beginPath(); x.rect(XW1, 588, PORCH_END - XW1, 18); x.clip();
  x.fillStyle = PAL.plank; x.fillRect(XW1, 588, PORCH_END - XW1, 18);
  TEX.woodPat.setTransform(new DOMMatrix().translate(0, 588)); x.globalCompositeOperation = 'multiply'; x.fillStyle = TEX.woodPat; x.fillRect(XW1, 588, PORCH_END - XW1, 18); x.restore();
  brush(x, [[XW1, 588], [PORCH_END, 588]], false, 1.8, PAL.plankLine, 78);
  brush(x, [[XW1, 606], [PORCH_END, 606]], false, 1.8, PAL.plankLine, 79);
  for (let X = XW1 + 70; X < PORCH_END; X += 140) brush(x, [[X, 589], [X + 2, 605]], false, 1.1, 'rgba(43,28,20,0.6)', 80 + X);
  ink(x, rect(XW1, 606, PORCH_END, 626), { fill: '#4d3829', line: PAL.plankLine, lw: 1.8, seed: 81, tex: 1 });
  ink(x, rect(XW1, 626, PORCH_END - 8, 700), { fill: '#1f1a24', line: '#0e0b10', lw: 1.6, seed: 82, tex: 1 });
  x.save(); x.beginPath(); x.rect(XW1, 626, PORCH_END - 8 - XW1, 74); x.clip();
  for (let X = XW1 - 80; X < PORCH_END + 80; X += 24) { brush(x, [[X, 626], [X + 74, 700]], false, 2.2, '#4a3a3a', 83 + X); brush(x, [[X + 74, 626], [X, 700]], false, 2.2, '#4a3a3a', 84 + X); }
  x.restore();
  // ground beyond, steps down
  ink(x, rect(XW1, 698, W + 10, 724), { fill: '#202438', line: '#10121c', lw: 1.4, seed: 84, tex: 0 });
  ink(x, crSample([[PORCH_END - 30, 700], [PORCH_END + 10, 694], [W + 10, 690], [W + 10, 724], [PORCH_END - 30, 724]], true, 3), { fill: '#252a3f', line: '#10121c', lw: 1.6, seed: 85, tex: 0 });
  for (let k = 0; k < 3; k++) { const X = PORCH_END + k * 24, Y = 606 + k * 30; ink(x, rect(X - 6, Y + 4, W + 10, Y + 14), { fill: '#6a4d39', line: PAL.plankLine, lw: 1.6, seed: 86 + k, tex: 1 }); ink(x, rect(X - 2, Y + 14, W + 10, Y + 34), { fill: '#3d2c22', line: PAL.plankLine, lw: 1.4, seed: 89 + k, tex: 1 }); }
  // the post, with a chevron carving and a bracket
  ink(x, rect(POST - 8, 168, POST + 8, 590), { fill: '#6b4b36', line: '#22150e', lw: 2, seed: 92, tex: 1 });
  for (let Y = 260; Y < 520; Y += 14) brush(x, [[POST - 6, Y], [POST, Y + 6], [POST + 6, Y]], false, 1.1, 'rgba(230,180,130,0.4)', 93 + Y);
  ink(x, crSample([[POST - 8, 210], [POST - 60, 176], [POST - 8, 182]], true, 4), { fill: '#6b4b36', line: '#22150e', lw: 1.6, seed: 94, tex: 1 });
  // the sill board, raised across the doorway
  ink(x, crSample(rect(sx(0.40), 590, sx(0.78), 600), true, 2), { fill: '#a07448', line: PAL.frameLine, lw: 1.9, seed: 95, tex: 1 });
  LAYERS.arch = c;
}

const LAYER_CACHE = {};
function worldLayers() { // painted once per camera framing (re-painted, never scaled, so line weight holds)
  const k = CAM.z.toFixed(4) + ',' + CAM.tx.toFixed(2) + ',' + CAM.ty.toFixed(2);
  if (!LAYER_CACHE[k]) { for (const q in LAYER_CACHE) delete LAYER_CACHE[q]; paintExterior(); paintInterior(); paintArchitecture(); LAYER_CACHE[k] = { ext: LAYERS.ext, int: LAYERS.int, arch: LAYERS.arch }; }
  const L = LAYER_CACHE[k]; LAYERS.ext = L.ext; LAYERS.int = L.int; LAYERS.arch = L.arch; return L;
}
function initWorld() { worldLayers(); LAYERS.ext1 = LAYERS.ext; }

// per-frame: door leaf (hinged at the inner face of the wall, swinging into the room)
function drawDoor(ctx, open) { // open: 0 closed .. 1 wide
  const th = lerp(0.07, Math.PI / 2, open), w = 0.9 * S * Math.sin(th);
  if (w < 3) return;
  const x1 = XW0, x0 = XW0 - w, y0 = LINTEL + 4, y1 = 598;
  ink(ctx, rect(x0, y0, x1, y1), { fill: PAL.door, line: PAL.doorLine, lw: 2.2, seed: 100, tex: 1, anchor: [x0, y0] });
  const nb = Math.max(1, Math.round(w / 26));
  for (let k = 1; k < nb; k++) brush(ctx, [[x0 + k * w / nb, y0 + 4], [x0 + k * w / nb, y1 - 4]], false, 1.3, 'rgba(14,30,22,0.8)', 101 + k);
  for (const Y of [y0 + 50, y1 - 60]) ink(ctx, rect(x0 + 4, Y, x1 - 2, Y + 7), { fill: '#2a2a2a', line: '#0c0c0c', lw: 1.2, seed: 104 + Y, tex: null });
  if (w > 60) { ctx.save(); polyPath(ctx, rect(x0, y0, x1, y1)); ctx.clip(); for (let Y = y0 + 90, k = 0; Y < y1 - 80; Y += 34, k++) spiral(ctx, x0 + w / 2, Y, 11, 1.4, k * 2.1, 'rgba(150,180,120,0.45)', 1.4, 120 + k); ctx.restore(); }
  if (w > 30) { const kx = x0 + 14, ky = (y0 + y1) / 2; ctx.strokeStyle = '#b89a5a'; ctx.lineWidth = 2 / CAM.z; ctx.beginPath(); ctx.arc(kx, ky, 6, 0, 6.283); ctx.stroke(); }
}
// the light that comes out: a painted pool on the porch boards and a glow in the air (compositing palette 'warm')
function lightAmount(open) { return 0.18 + 0.82 * open; }
function drawLight(ctx, open, flick) { // the light comes OUT of the doorway: a wedge spilling from the opening down onto the boards
  const a = lightAmount(open) * (0.94 + 0.06 * flick);
  const L = 120 + 600 * a;
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  // the wedge of lit air from the opening, falling from lintel height to the boards at distance L
  const wg = ctx.createLinearGradient(XW1, 0, XW1 + L, 0);
  wg.addColorStop(0, `rgba(255,196,120,${0.30 * a})`); wg.addColorStop(0.5, `rgba(250,170,95,${0.09 * a})`); wg.addColorStop(1, 'rgba(250,170,95,0)');
  ctx.filter = `blur(${7 * CAM.z}px)`; // a soft edge to the lit air
  ctx.fillStyle = wg; ctx.beginPath(); ctx.moveTo(XW0, LINTEL + 6); ctx.lineTo(XW1, LINTEL + 6); ctx.lineTo(XW1 + L, 604); ctx.lineTo(XW0, 604); ctx.closePath(); ctx.fill();
  ctx.filter = 'none';
  // the pool on the boards, brightest at the sill
  const fg = ctx.createLinearGradient(XW1, 0, XW1 + L, 0); fg.addColorStop(0, `rgba(255,220,150,${1.0 * a})`); fg.addColorStop(0.4, `rgba(255,200,125,${0.6 * a})`); fg.addColorStop(1, 'rgba(255,205,130,0)');
  ctx.fillStyle = fg; ctx.beginPath(); ctx.moveTo(XW0, 589); ctx.lineTo(XW1 + L, 588); ctx.lineTo(XW1 + L, 606); ctx.lineTo(XW0, 606); ctx.closePath(); ctx.fill();
  // the door frame and sill catch it
  ctx.fillStyle = `rgba(255,190,110,${0.45 * a})`; ctx.fillRect(XW0, LINTEL + 4, XW1 - XW0, 591 - LINTEL - 4);
  ctx.fillStyle = `rgba(255,230,170,${0.8 * a})`; ctx.fillRect(sx(0.40), 589, sx(0.78) - sx(0.40), 3);
  ctx.restore();
}
function warmAt(xpx, open) { const a = lightAmount(open); const L = 120 + 600 * a; return xpx < XW1 ? 1 : clamp(1 - (xpx - XW1) / L) * a; }
function drawHearth(ctx, t) {
  const f = 0.6 + 0.25 * Math.sin(t * 9.1) + 0.15 * Math.sin(t * 23.3 + 1);
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  const g = ctx.createRadialGradient(36, 560, 4, 36, 560, 150); g.addColorStop(0, `rgba(255,150,60,${0.55 * f})`); g.addColorStop(1, 'rgba(255,120,40,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 400, 220, 200); ctx.restore();
  const fl = []; for (let k = 0; k <= 8; k++) { const X = 16 + k * 5.5, h = (k % 2 ? 28 : 46) * (0.75 + 0.25 * Math.sin(t * 11 + k * 1.7)); fl.push([X, 590 - (k === 0 || k === 8 ? 0 : h)]); }
  ink(ctx, crSample(fl, true, 4), { fill: '#f0a040', line: '#a0461c', lw: 1.4, seed: 110, tex: null });
  return f;
}
function drawStars(ctx, t) {
  for (let k = 0; k < 26; k++) {
    const X = 470 + rnd(k * 3.1) * 800, Y = 12 + rnd(k * 7.7) * 260; if (Math.hypot(X - 1068, Y - 96) < 60) continue;
    const a = 0.35 + 0.35 * Math.sin(t * (1 + rnd(k) * 2) + k) ; ctx.fillStyle = `rgba(250,240,210,${clamp(a)})`;
    ctx.beginPath(); ctx.arc(X, Y, 0.8 + rnd(k * 1.3) * 0.9, 0, 6.283); ctx.fill();
  }
}
if (typeof window !== 'undefined') Object.assign(window, { initWorld, worldLayers, drawDoor, drawLight, warmAt, drawHearth, drawStars, LAYERS, XW0, XW1, spiral, triskele, rect, mk });
