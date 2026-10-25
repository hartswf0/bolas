// SCION 09 · Igarashi — the source drawings.
// Every character in the film is one of these drawings, drawn here in code by this swarm (no found image, no model),
// rendered once to a PNG, then triangulated (mesh.py) and only ever moved by as-rigid-as-possible deformation (arap.js).
// Each drawing carries: its canvas size, its handles (named control points the rig moves), its feature-protect regions
// (eye, nose, collar tag, buttons: triangles inside are weighted stiff in the energy), and its sockets (where a head piece
// attaches). Coordinates are drawing pixels, y down. Works in the browser (window.DRAWINGS) and in node (module.exports).
(function (root) {
  const INK = '#1e1711', PAPER = '#f1e6cf';
  const COAT = '#b88550', COAT_D = '#8a5c34', SADDLE = '#3f2b1d', CREAM = '#ead3a6', COLLAR = '#9e2f26', BRASS = '#d8b24a';

  function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

  // Catmull-Rom spline through points (closed or open) as canvas path
  function cr(ctx, P, closed, t = 0.5, move = true) {
    const n = P.length; if (n < 2) return;
    const g = i => closed ? P[(i + n) % n] : P[Math.max(0, Math.min(n - 1, i))];
    if (move) ctx.moveTo(P[0][0], P[0][1]);
    const m = closed ? n : n - 1;
    for (let i = 0; i < m; i++) {
      const p0 = g(i - 1), p1 = g(i), p2 = g(i + 1), p3 = g(i + 2);
      const c1 = [p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3];
      const c2 = [p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3];
      ctx.bezierCurveTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1]);
    }
    if (closed) ctx.closePath();
  }
  function shape(ctx, P, fill) { ctx.beginPath(); cr(ctx, P, true); ctx.fillStyle = fill; ctx.fill(); }
  function line(ctx, P, w, col = INK, closed = false, alpha = 1) {
    ctx.save(); ctx.globalAlpha = alpha; ctx.beginPath(); cr(ctx, P, closed); ctx.lineWidth = w; ctx.strokeStyle = col;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke(); ctx.restore();
  }
  // a pen line whose width swells in the middle (drawn as a few overlapping passes)
  function pen(ctx, P, w, col = INK, alpha = 1) {
    line(ctx, P, w * 0.55, col, false, alpha);
    if (P.length > 2) line(ctx, P.slice(1, -1).length > 1 ? P.slice(1, -1) : P, w, col, false, alpha);
  }
  function clipTo(ctx, P) { ctx.beginPath(); cr(ctx, P, true); ctx.clip(); }
  // fur: short strokes following a flow field, clipped to the outline
  function fur(ctx, P, box, flow, cols, n, seed, len = 9, w = 1.4, alpha = 0.35) {
    const r = rng(seed); ctx.save(); clipTo(ctx, P); ctx.lineCap = 'round';
    for (let i = 0; i < n; i++) {
      const x = box[0] + r() * (box[2] - box[0]), y = box[1] + r() * (box[3] - box[1]);
      const a = flow(x, y) + (r() - 0.5) * 0.5, l = len * (0.6 + r() * 0.8);
      ctx.strokeStyle = cols[Math.floor(r() * cols.length)]; ctx.globalAlpha = alpha * (0.5 + r() * 0.5); ctx.lineWidth = w;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + Math.cos(a) * l * 0.5 + (r() - .5) * 2, y + Math.sin(a) * l * 0.5 + (r() - .5) * 2, x + Math.cos(a) * l, y + Math.sin(a) * l); ctx.stroke();
    }
    ctx.restore();
  }
  // the cut: an off-white paper margin around the figure, then the ink outline
  function cutout(ctx, P, margin = 7) {
    ctx.save(); ctx.beginPath(); cr(ctx, P, true); ctx.lineJoin = 'round'; ctx.lineWidth = margin * 2; ctx.strokeStyle = PAPER; ctx.stroke();
    ctx.fillStyle = PAPER; ctx.fill(); ctx.restore();
  }
  function outline(ctx, P, w = 3.2) {
    ctx.save(); ctx.beginPath(); cr(ctx, P, true); ctx.lineJoin = 'round'; ctx.lineWidth = w; ctx.strokeStyle = INK; ctx.stroke(); ctx.restore();
  }
  function shade(ctx, clipP, P, col) { ctx.save(); clipTo(ctx, clipP); shape(ctx, P, col); ctx.restore(); }
  function eye(ctx, x, y, r, look = [-1, 0]) {
    ctx.save();
    ctx.beginPath(); ctx.ellipse(x, y, r * 1.25, r, 0, 0, Math.PI * 2); ctx.fillStyle = '#f6efe0'; ctx.fill();
    ctx.beginPath(); ctx.arc(x + look[0] * r * 0.25, y + look[1] * r * 0.2, r * 0.82, 0, Math.PI * 2); ctx.fillStyle = '#2a1a0e'; ctx.fill();
    ctx.beginPath(); ctx.arc(x + look[0] * r * 0.25 - r * 0.28, y - r * 0.3, r * 0.26, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill();
    ctx.beginPath(); ctx.ellipse(x, y, r * 1.25, r, 0, Math.PI * 1.05, Math.PI * 1.95); ctx.lineWidth = 2.4; ctx.strokeStyle = INK; ctx.stroke();
    ctx.beginPath(); ctx.ellipse(x, y, r * 1.25, r, 0, 0, Math.PI * 2); ctx.lineWidth = 1.2; ctx.strokeStyle = INK; ctx.stroke();
    ctx.restore();
  }
  function tag(ctx, x, y, r) { // the collar tag: a brass disc with a ring and a stamped mark (a protected "button")
    ctx.save();
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = BRASS; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = INK; ctx.stroke();
    ctx.beginPath(); ctx.arc(x, y, r * 0.55, 0, Math.PI * 2); ctx.lineWidth = 1.2; ctx.strokeStyle = '#7a5a18'; ctx.stroke();
    ctx.beginPath(); ctx.arc(x - r * 0.35, y - r * 0.35, r * 0.22, 0, Math.PI * 2); ctx.fillStyle = 'rgba(255,250,220,.8)'; ctx.fill();
    ctx.restore();
  }
  function button(ctx, x, y, r, col = '#d9cbb0') {
    ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = col; ctx.fill(); ctx.lineWidth = 1.6; ctx.strokeStyle = INK; ctx.stroke();
    for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) { ctx.beginPath(); ctx.arc(x + dx * r * 0.3, y + dy * r * 0.3, r * 0.13, 0, Math.PI * 2); ctx.fillStyle = INK; ctx.fill(); }
    ctx.restore();
  }

  const D = {};

  // ───────────────────────── DOG · standing, profile, facing left (body; the head is its own piece) ─────────────────────────
  {
    const O = [ // outline, clockwise from the top of the neck
      [124, 82], [150, 104], [178, 118], [212, 125], [250, 128], [290, 126], [322, 124], [350, 130], [372, 138],
      [402, 148], [428, 168], [444, 196], [452, 228], [450, 252], [440, 254], [432, 230], [422, 200], [404, 178], [380, 166],
      [384, 192], [378, 220], [364, 248], [360, 276], [362, 304], [368, 320], [340, 322], [334, 312], [338, 292], [338, 266], [338, 246], [330, 228], [314, 214],
      [300, 220], [296, 240], [290, 262], [286, 290], [288, 320], [262, 322], [258, 312], [264, 292], [268, 266], [272, 240], [268, 222], [258, 214],
      [232, 208], [206, 208], [190, 214],
      [192, 236], [194, 262], [192, 292], [196, 320], [170, 322], [166, 312], [172, 292], [172, 262], [168, 238], [160, 228],
      [150, 232], [146, 258], [142, 290], [146, 320], [118, 322], [112, 312], [120, 292], [122, 262], [120, 236], [114, 214],
      [106, 188], [102, 160], [100, 132], [104, 110]
    ];
    const FARFRONT = [[192, 214], [194, 262], [192, 292], [196, 320], [170, 322], [166, 312], [172, 292], [172, 262], [166, 230], [180, 214]];
    const FARHIND = [[300, 216], [296, 240], [290, 262], [286, 290], [288, 320], [262, 322], [258, 312], [264, 292], [268, 266], [272, 240], [266, 216], [286, 210]];
    const SAD = [[150, 100], [190, 112], [240, 118], [300, 116], [345, 124], [372, 140], [360, 168], [330, 172], [290, 166], [250, 168], [205, 166], [170, 158], [140, 140]];
    const CHEST = [[100, 128], [112, 150], [122, 178], [128, 206], [118, 214], [106, 192], [100, 160]];
    D.dog_stand = {
      kind: 'dog', w: 470, h: 340, ground: 321, facing: -1,
      draw(ctx) {
        cutout(ctx, O);
        shape(ctx, O, COAT);
        shade(ctx, O, FARFRONT, 'rgba(60,35,18,.45)'); shade(ctx, O, FARHIND, 'rgba(60,35,18,.45)');
        fur(ctx, O, [95, 80, 455, 325], (x, y) => y > 215 ? Math.PI / 2 + 0.15 : 0.15 + (y - 120) * 0.004, [COAT_D, '#d3a26a', '#6e4a2a'], 900, 11);
        ctx.save(); clipTo(ctx, O); shape(ctx, SAD, SADDLE); ctx.restore();
        fur(ctx, SAD, [130, 95, 380, 175], () => 0.25, ['#20150d', '#6b4a30'], 260, 12, 8, 1.3, 0.5);
        shade(ctx, O, CHEST, CREAM);
        fur(ctx, CHEST, [96, 120, 132, 216], () => Math.PI / 2 - 0.2, ['#c9a777', '#fff4dc'], 80, 13, 7, 1.2, 0.5);
        // paws: cream socks
        for (const [x0, x1] of [[112, 150], [166, 198], [258, 292], [334, 370]]) shade(ctx, O, [[x0 - 4, 296], [x1 + 4, 296], [x1 + 4, 326], [x0 - 4, 326]], CREAM);
        // anatomy in pen: shoulder, elbow, thigh, stifle, hock, belly fold, toes
        pen(ctx, [[150, 150], [158, 178], [152, 206], [146, 222]], 2.2, INK, 0.75);
        pen(ctx, [[330, 150], [352, 170], [362, 196], [352, 222]], 2.4, INK, 0.75);
        pen(ctx, [[226, 196], [250, 202], [272, 204]], 1.6, INK, 0.55);
        pen(ctx, [[338, 266], [348, 262]], 1.6, INK, 0.6);
        for (const [x, y] of [[124, 314], [132, 316], [176, 314], [184, 316], [268, 314], [276, 316], [346, 314], [354, 316]]) line(ctx, [[x, y - 4], [x - 1, y + 4]], 1.3, INK, false, 0.7);
        outline(ctx, O);
      },
      handles: {
        socket: [118, 100], withers: [178, 128], back: [250, 136], hip: [330, 136], belly: [232, 196],
        f1: [132, 318], f2: [182, 318], h1: [274, 318], h2: [352, 318],
        f1k: [124, 266], f2k: [182, 266], h1k: [270, 262], h2k: [340, 258],
        tail_mid: [428, 196], tail_tip: [446, 248]
      },
      features: [],
      // explicit cuts (crack lines in the mesh, from tip to open end): the near and far forelegs, the tail and the rump
      cuts: [[[156, 226], [158, 334]], [[383, 170], [404, 192]]],
      // the far legs are drawn first (behind), so a crossing near leg passes over them instead of folding through them
      behind: [FARFRONT.map(p => [p[0], p[1] < 300 ? p[1] : p[1] + 12]), FARHIND.map(p => [p[0], p[1] < 300 ? p[1] : p[1] + 12])],
      socket: { at: [116, 102], toward: [178, 124] } // head attaches here; neck line direction toward the withers
    };
  }

  // ───────────────────────── DOG · standing, seen from behind (facing away into the yard, a little to the right) ─────────────────────────
  {
    // the back view that reads as a back: two haunches and the tail between them toward us, the spine and saddle receding
    // up to the narrower shoulders, the far forelegs small in the gap between the hind legs
    const O = [
      [176, 112], [198, 100], [230, 95], [258, 102], [272, 128], [284, 158], [298, 190], [302, 222], [292, 248], [282, 262],
      [284, 290], [288, 312], [294, 321], [262, 323], [258, 312], [262, 290], [262, 262], [256, 246],
      [246, 240], [238, 250], [240, 298], [238, 307], [222, 307], [220, 258], [214, 254], [208, 258], [206, 307], [190, 307], [188, 298], [190, 250], [182, 240],
      [174, 246], [170, 262], [170, 290], [174, 312], [178, 321], [146, 323], [142, 312], [148, 290], [150, 262], [140, 248], [130, 222], [132, 190], [144, 160], [156, 132]
    ];
    const FRONT = [[182, 240], [190, 250], [188, 298], [190, 307], [206, 307], [208, 258], [214, 254], [220, 258], [222, 307], [238, 307], [240, 298], [238, 250], [246, 240]];
    const SAD = [[172, 116], [198, 102], [230, 97], [258, 104], [270, 128], [256, 152], [232, 166], [206, 166], [182, 150], [166, 132]];
    const TAIL = [[208, 148], [204, 186], [206, 226], [212, 260], [218, 274], [228, 264], [228, 226], [230, 188], [228, 150]];
    D.dog_rear = {
      kind: 'dog', w: 360, h: 340, ground: 322, facing: 1,
      draw(ctx) {
        cutout(ctx, O);
        shape(ctx, O, COAT);
        fur(ctx, O, [125, 90, 305, 325], (x, y) => y > 240 ? Math.PI / 2 : (y < 150 ? -Math.PI / 2 + (x - 218) * 0.01 : Math.PI / 2 + (x - 216) * 0.012), [COAT_D, '#d3a26a', '#6e4a2a'], 900, 21);
        shade(ctx, O, FRONT, 'rgba(40,24,12,.55)');
        ctx.save(); clipTo(ctx, O); shape(ctx, SAD, SADDLE); ctx.restore();
        fur(ctx, SAD, [164, 94, 272, 168], (x) => -Math.PI / 2 + (x - 218) * 0.02, ['#20150d', '#6b4a30'], 200, 22, 7, 1.3, 0.5);
        pen(ctx, [[218, 98], [218, 128], [217, 150]], 2.2, '#140d08', 0.6); // spine
        // haunches: two lobes either side of the tail
        pen(ctx, [[200, 162], [180, 190], [178, 222], [186, 240]], 2.6, INK, 0.8);
        pen(ctx, [[236, 162], [258, 190], [258, 222], [250, 240]], 2.6, INK, 0.8);
        // hocks and the backs of the hind paws (heel pads toward us)
        pen(ctx, [[146, 256], [156, 262]], 2, INK, .7); pen(ctx, [[286, 256], [276, 262]], 2, INK, .7);
        for (const [x0, x1] of [[142, 178], [258, 294]]) shade(ctx, O, [[x0 - 4, 292], [x1 + 4, 292], [x1 + 4, 330], [x0 - 4, 330]], CREAM);
        for (const x of [160, 276]) { ctx.beginPath(); ctx.ellipse(x, 316, 7, 4.5, 0, 0, 7); ctx.fillStyle = '#2a1a10'; ctx.fill(); }
        shape(ctx, TAIL, COAT_D); fur(ctx, TAIL, [202, 146, 232, 276], () => Math.PI / 2, ['#3a2616', '#a0703f'], 60, 23, 7, 1.2, .6); line(ctx, TAIL, 2.6, INK, true);
        outline(ctx, O);
      },
      handles: {
        socket: [222, 102], withers: [220, 118], back: [218, 140], hip: [216, 178], belly: [214, 244],
        f1: [198, 304], f2: [230, 304], h1: [160, 318], h2: [276, 318], tail_mid: [216, 212], tail_tip: [220, 268]
      },
      features: [],
      socket: { at: [222, 104], toward: [218, 150] }
    };
  }

  // ───────────────────────── DOG · sitting, seen from behind (the held refusal) ─────────────────────────
  {
    const O = [
      [212, 116], [238, 101], [266, 97], [292, 105], [306, 126], [314, 162], [330, 208], [346, 254], [350, 290], [344, 312],
      [310, 318], [262, 320], [214, 318], [180, 312], [174, 290], [178, 254], [194, 208], [208, 162]
    ];
    const TAIL = [[268, 296], [244, 312], [204, 318], [154, 318], [114, 312], [96, 302], [104, 294], [130, 302], [170, 305], [210, 302], [242, 292], [256, 286]];
    const SAD = [[210, 118], [238, 102], [266, 98], [292, 106], [306, 128], [302, 166], [282, 186], [262, 192], [242, 186], [222, 166], [212, 140]];
    D.dog_sit_back = {
      kind: 'dog', w: 400, h: 340, ground: 320, facing: 1,
      draw(ctx) {
        cutout(ctx, O); cutout(ctx, TAIL, 5);
        shape(ctx, O, COAT);
        fur(ctx, O, [170, 96, 352, 322], (x, y) => y < 170 ? -Math.PI / 2 + (x - 262) * 0.01 : Math.PI / 2 + (x - 262) * 0.008, [COAT_D, '#d3a26a', '#6e4a2a'], 900, 32);
        ctx.save(); clipTo(ctx, O); shape(ctx, SAD, SADDLE); ctx.restore();
        fur(ctx, SAD, [206, 98, 308, 194], (x) => -Math.PI / 2 + (x - 262) * 0.02, ['#20150d', '#6b4a30'], 200, 33, 7, 1.3, 0.5);
        pen(ctx, [[262, 100], [262, 160], [262, 230], [262, 290]], 2.2, '#140d08', 0.55); // spine down to the tail
        pen(ctx, [[214, 206], [200, 252], [204, 296]], 2.6, INK, .8); // left haunch
        pen(ctx, [[310, 206], [324, 252], [320, 296]], 2.6, INK, .8); // right haunch
        for (const [x, y] of [[188, 312], [338, 312]]) { ctx.beginPath(); ctx.ellipse(x, y, 13, 7, 0, 0, 7); ctx.fillStyle = CREAM; ctx.fill(); ctx.lineWidth = 1.6; ctx.strokeStyle = INK; ctx.stroke(); ctx.beginPath(); ctx.ellipse(x, y + 1, 5, 3, 0, 0, 7); ctx.fillStyle = '#2a1a10'; ctx.fill(); }
        outline(ctx, O);
        shape(ctx, TAIL, COAT_D); fur(ctx, TAIL, [94, 284, 270, 320], () => 0, ['#3a2616', '#a0703f'], 80, 31, 8, 1.2, .6); line(ctx, TAIL, 2.6, INK, true);
      },
      handles: {
        socket: [262, 104], withers: [262, 128], back: [262, 186], hip: [262, 250], h1: [196, 312], h2: [330, 312],
        tail_mid: [180, 306], tail_tip: [102, 298], belly: [262, 296]
      },
      features: [],
      socket: { at: [262, 106], toward: [262, 160] }
    };
  }
  // ───────────────────────── DOG · lying, sphinx, profile facing left (body; head is a piece) ─────────────────────────
  {
    const O = [
      [134, 150], [164, 160], [200, 170], [250, 174], [300, 172], [344, 168], [380, 172], [408, 186], [424, 206], [430, 232], [424, 250],
      [444, 254], [480, 256], [518, 254], [540, 250], [544, 258], [530, 266], [490, 270], [450, 270], [416, 270],
      [380, 272], [340, 274], [300, 274], [262, 274], [228, 272],
      [196, 272], [160, 272], [120, 272], [84, 272], [56, 270], [50, 262], [58, 254], [92, 252], [128, 250],
      [126, 236], [118, 214], [116, 190], [122, 166]
    ];
    const THIGH = [[330, 196], [366, 192], [396, 206], [408, 232], [398, 256], [370, 262], [340, 256], [318, 240], [316, 216]];
    const HPAW = [[300, 262], [330, 258], [356, 262], [358, 272], [300, 274]];
    const FORE2 = [[128, 254], [96, 256], [66, 258], [60, 264], [70, 266], [128, 266]]; // far foreleg, behind
    const SAD = [[150, 152], [200, 166], [260, 170], [320, 166], [370, 170], [404, 186], [380, 206], [330, 200], [270, 202], [210, 196], [160, 180]];
    const CHEST = [[120, 168], [130, 198], [134, 232], [138, 252], [126, 252], [118, 214], [116, 188]];
    D.dog_lie = {
      kind: 'dog', w: 560, h: 300, ground: 273, facing: -1,
      draw(ctx) {
        cutout(ctx, O);
        shape(ctx, O, COAT);
        fur(ctx, O, [48, 148, 548, 276], (x, y) => x > 425 ? 0.05 : 0.1, [COAT_D, '#d3a26a', '#6e4a2a'], 900, 41);
        ctx.save(); clipTo(ctx, O); shape(ctx, SAD, SADDLE); ctx.restore();
        fur(ctx, SAD, [140, 150, 410, 206], () => 0.1, ['#20150d', '#6b4a30'], 240, 42, 8, 1.3, 0.5);
        shade(ctx, O, CHEST, CREAM);
        shade(ctx, O, FORE2, 'rgba(60,35,18,.4)');
        shade(ctx, O, [[48, 250], [136, 250], [136, 274], [48, 274]], 'rgba(234,211,166,.75)');
        ctx.save(); clipTo(ctx, O); shape(ctx, THIGH, COAT); fur(ctx, THIGH, [312, 188, 412, 266], () => 0.6, [COAT_D, '#d3a26a'], 160, 43); ctx.restore();
        line(ctx, THIGH.slice(0, 7), 2.6, INK, false, .8);
        ctx.save(); clipTo(ctx, O); shape(ctx, HPAW, CREAM); ctx.restore(); line(ctx, [[300, 262], [330, 258], [356, 262], [358, 272]], 2.2, INK, false, .8);
        pen(ctx, [[150, 200], [160, 228], [150, 252]], 2.2, INK, .7); // elbow
        pen(ctx, [[60, 262], [128, 262]], 1.4, INK, .6);
        for (const x of [66, 74, 82]) line(ctx, [[x, 266], [x - 1, 272]], 1.2, INK, false, .7);
        pen(ctx, [[200, 250], [250, 256], [300, 254]], 1.6, INK, .45);
        outline(ctx, O);
      },
      handles: {
        socket: [136, 156], withers: [180, 176], back: [260, 184], hip: [372, 190], belly: [250, 262],
        f1: [66, 262], f2: [100, 264], h1: [330, 266], h2: [410, 262], tail_mid: [480, 262], tail_tip: [538, 256]
      },
      features: [],
      socket: { at: [136, 158], toward: [186, 176] }
    };
  }

  // ───────────────────────── DOG HEAD · profile, facing left (eye, nose, collar tag protected) ─────────────────────────
  {
    const O = [
      [176, 150], [168, 118], [150, 92], [140, 66], [138, 40], [146, 14], [134, 18], [116, 38], [104, 58],
      [86, 62], [64, 72], [40, 84], [22, 94], [16, 104], [22, 114], [40, 118], [64, 122], [84, 132], [98, 150], [112, 170], [146, 176]
    ];
    const EAR = [[104, 58], [116, 38], [134, 18], [146, 14], [140, 40], [140, 66], [124, 68]];
    const MASK = [[16, 104], [22, 94], [40, 84], [64, 72], [86, 66], [88, 96], [70, 112], [40, 118], [22, 114]];
    D.head_side = {
      kind: 'head', w: 200, h: 200, facing: -1,
      draw(ctx) {
        cutout(ctx, O);
        shape(ctx, O, COAT);
        fur(ctx, O, [14, 10, 180, 180], (x, y) => x < 90 ? 0 : 0.6 + (y - 90) * 0.01, [COAT_D, '#d3a26a', '#6e4a2a'], 380, 51, 7);
        ctx.save(); clipTo(ctx, O); shape(ctx, MASK, '#4a3222'); shape(ctx, EAR, '#3b281b'); ctx.restore();
        fur(ctx, MASK, [14, 60, 92, 122], () => 0.05, ['#22160d', '#7b5638'], 90, 52, 6, 1.1, 0.5);
        // ear: inner line; brow, stop, lip, jaw
        line(ctx, [[118, 58], [130, 32], [138, 22]], 1.8, '#d9b892', false, .9);
        pen(ctx, [[78, 72], [84, 82]], 1.6, INK, .7);
        pen(ctx, [[22, 112], [44, 114], [66, 116], [80, 112]], 1.8, INK, .85); // lip line
        pen(ctx, [[96, 126], [118, 128], [138, 120]], 1.6, INK, .5);
        // collar band with the tag
        ctx.save(); clipTo(ctx, O);
        ctx.beginPath(); ctx.moveTo(108, 166); ctx.quadraticCurveTo(142, 148, 180, 134); ctx.lineTo(186, 150); ctx.quadraticCurveTo(146, 166, 116, 182); ctx.closePath();
        ctx.fillStyle = COLLAR; ctx.fill(); ctx.lineWidth = 1.6; ctx.strokeStyle = INK; ctx.stroke(); ctx.restore();
        outline(ctx, O);
        // nose
        ctx.beginPath(); ctx.ellipse(20, 100, 9, 7, -0.3, 0, Math.PI * 2); ctx.fillStyle = '#120c08'; ctx.fill();
        ctx.beginPath(); ctx.arc(16, 97, 2.2, 0, Math.PI * 2); ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.fill();
        eye(ctx, 72, 82, 6.5, [-1, 0]);
        tag(ctx, 118, 184, 9);
      },
      handles: { skull: [118, 90], muzzle: [28, 104], ear_tip: [144, 18], ear_base: [118, 62], neck: [150, 160] },
      features: [{ name: 'eye', c: [72, 82], r: 13 }, { name: 'nose', c: [20, 100], r: 13 }, { name: 'tag', c: [118, 184], r: 13 }],
      socket: { at: [150, 160], toward: [176, 150] }
    };
  }

  // ───────────────────────── DOG HEAD · from behind, turned a little to its right (looking away / looking in) ─────────────────────────
  {
    // the back of a head: the backs of the ears (dark, no inner ear), the round occiput, the collar's buckle at the nape,
    // and only the tip of the muzzle and nose peeking past the cheek to show where it is looking
    const O = [
      [64, 170], [58, 142], [60, 116], [50, 90], [42, 56], [46, 20], [56, 22], [76, 50], [92, 60], [108, 60], [122, 48], [138, 20], [148, 22],
      [152, 56], [148, 88], [152, 102], [164, 110], [168, 122], [156, 130], [146, 140], [146, 166], [126, 176], [86, 178]
    ];
    const EAR_L = [[50, 90], [42, 56], [46, 20], [56, 22], [76, 50], [82, 74], [66, 92]];
    const EAR_R = [[122, 48], [138, 20], [148, 22], [152, 56], [148, 88], [130, 84], [118, 62]];
    const MUZ = [[150, 100], [164, 110], [168, 122], [156, 130], [146, 128]];
    D.head_back = {
      kind: 'head', w: 200, h: 200, facing: 0,
      draw(ctx) {
        cutout(ctx, O);
        shape(ctx, O, COAT_D);
        fur(ctx, O, [40, 16, 170, 180], (x, y) => Math.atan2(y - 70, x - 100), ['#5a3c24', '#a8784a', '#3a2616'], 520, 61, 8, 1.4, .55);
        ctx.save(); clipTo(ctx, O); shape(ctx, EAR_L, '#2a1c12'); shape(ctx, EAR_R, '#2a1c12'); shape(ctx, MUZ, '#c79a63'); ctx.restore();
        fur(ctx, EAR_L, [40, 18, 84, 94], () => -Math.PI / 2 + 0.3, ['#4a3222', '#140c07'], 50, 62, 6, 1.1, .6);
        fur(ctx, EAR_R, [116, 18, 154, 90], () => -Math.PI / 2 - 0.3, ['#4a3222', '#140c07'], 50, 63, 6, 1.1, .6);
        pen(ctx, [[64, 96], [80, 78]], 1.8, INK, .7); pen(ctx, [[134, 80], [126, 62]], 1.8, INK, .7);
        pen(ctx, [[146, 104], [150, 118], [146, 132]], 2, INK, .8); // the cheek line the muzzle peeks past
        // collar around the nape with its buckle
        ctx.save(); clipTo(ctx, O);
        ctx.beginPath(); ctx.moveTo(56, 148); ctx.quadraticCurveTo(100, 164, 152, 146); ctx.lineTo(152, 164); ctx.quadraticCurveTo(100, 184, 56, 166); ctx.closePath();
        ctx.fillStyle = COLLAR; ctx.fill(); ctx.lineWidth = 1.6; ctx.strokeStyle = INK; ctx.stroke(); ctx.restore();
        ctx.save(); ctx.fillStyle = BRASS; ctx.strokeStyle = INK; ctx.lineWidth = 1.6; ctx.fillRect(92, 154, 18, 14); ctx.strokeRect(92, 154, 18, 14); ctx.beginPath(); ctx.moveTo(101, 154); ctx.lineTo(101, 168); ctx.stroke(); ctx.restore();
        outline(ctx, O);
        ctx.beginPath(); ctx.ellipse(164, 116, 5, 6, 0.3, 0, 7); ctx.fillStyle = '#120c08'; ctx.fill(); // nose tip, peeking
      },
      handles: { skull: [100, 96], muzzle: [160, 116], ear_tip: [142, 22], ear_base: [128, 70], ear2_tip: [48, 22], neck: [100, 164] },
      features: [{ name: 'buckle', c: [101, 161], r: 12 }, { name: 'nose_tip', c: [162, 116], r: 9 }],
      socket: { at: [100, 166], toward: [100, 200] }
    };
  }
  // ───────────────────────── PERSON · standing, profile facing right; cardigan with four buttons ─────────────────────────
  {
    const BODY = [
      [118, 30], [134, 26], [150, 34], [156, 52], [154, 70], [158, 82], [150, 86], [148, 100], [140, 106], [146, 118], [164, 130], [170, 170],
      [168, 220], [166, 262], [174, 330], [178, 380], [172, 420], [174, 560], [184, 600], [196, 612], [196, 622], [146, 622], [144, 600], [140, 560],
      [128, 470], [118, 560], [116, 600], [124, 614], [122, 624], [76, 624], [80, 604], [84, 560], [88, 420], [80, 380], [84, 330], [88, 262],
      [84, 200], [90, 140], [104, 118], [110, 104], [102, 80], [100, 56], [104, 40]
    ];
    const ARM = [[150, 126], [166, 144], [172, 186], [176, 234], [182, 274], [190, 300], [194, 318], [186, 330], [174, 322], [170, 300], [160, 272], [150, 232], [142, 186], [138, 146]];
    const SKIRT = [[84, 380], [178, 380], [172, 420], [176, 470], [82, 470], [88, 420]];
    const HAIR = [[104, 40], [118, 22], [140, 20], [156, 34], [150, 46], [130, 42], [118, 52], [112, 70], [102, 74], [98, 56]];
    D.person_stand = {
      kind: 'person', w: 260, h: 640, ground: 622, facing: 1,
      layers: ['body', 'arm'],
      draw(ctx, layer) {
        if (layer !== 'arm') {
        cutout(ctx, BODY);
        shape(ctx, BODY, '#4a5a6a');
        ctx.save(); clipTo(ctx, BODY);
        shape(ctx, [[90, 0], [170, 0], [170, 112], [90, 112]], '#d8b08c'); // face and neck
        shape(ctx, SKIRT, '#2c2a36');
        shape(ctx, [[60, 470], [200, 470], [200, 640], [60, 640]], '#2d2a2a');
        shape(ctx, [[60, 596], [200, 596], [200, 640], [60, 640]], '#171311');
        ctx.restore();
        fur(ctx, BODY, [80, 110, 180, 380], () => Math.PI / 2, ['#384756', '#5e7184'], 260, 71, 12, 1.4, .4);
        shape(ctx, HAIR, '#3a2a20'); line(ctx, HAIR, 2, INK, true, .8);
        eye(ctx, 142, 56, 3.4, [1, 0]);
        pen(ctx, [[152, 74], [146, 76]], 1.6, INK, .8); // mouth
        pen(ctx, [[126, 118], [130, 190], [128, 260], [130, 380]], 2, INK, .55); // cardigan edge
        for (const y of [150, 196, 242, 288]) button(ctx, 136, y, 6);
        pen(ctx, [[128, 470], [130, 560], [128, 600]], 1.8, INK, .6);
        outline(ctx, BODY);
        }
        if (layer === 'body') return;
        cutout(ctx, ARM, 5); shape(ctx, ARM, '#506275');
        fur(ctx, ARM, [136, 124, 196, 332], () => Math.PI / 2 - 0.15, ['#384756', '#6a7f93'], 90, 72, 10, 1.3, .4);
        shade(ctx, ARM, [[160, 296], [200, 290], [200, 336], [160, 336]], '#d8b08c');
        outline(ctx, ARM, 2.6);
      },
      cuts: [[[126, 476], [122, 640]]],   // between the trouser legs, so a step parts the legs instead of stretching a skirt
      handles: { head: [128, 50], chest: [128, 160], hip: [128, 380], knee: [128, 500], foot_a: [176, 620], foot_b: [96, 620], shoulder: [152, 140], elbow: [160, 230], hand: [184, 318] },
      features: [{ name: 'eye', c: [142, 56], r: 9 }, ...[150, 196, 242, 288].map((y, k) => ({ name: 'button' + k, c: [136, y], r: 10 }))]
    };
  }

  // ───────────────────────── PERSON · sitting on the step beside the door, facing right; hand offered low ─────────────────────────
  {
    const BODY = [
      [96, 80], [112, 76], [128, 84], [134, 102], [132, 120], [136, 132], [128, 136], [126, 150], [118, 156], [124, 168], [142, 182], [150, 222],
      [152, 270], [158, 300], [200, 300], [250, 304], [268, 316], [272, 340], [268, 400], [274, 436], [290, 446], [290, 458], [240, 458], [236, 440], [238, 400],
      [236, 346], [200, 344], [150, 346], [100, 344], [72, 330], [64, 300], [62, 250], [68, 190], [82, 168], [88, 154], [80, 130], [78, 106], [82, 90]
    ];
    const ARM = [[128, 176], [146, 196], [170, 236], [204, 268], [244, 288], [282, 296], [304, 300], [310, 312], [296, 318], [262, 314], [228, 306], [190, 288], [152, 256], [124, 214], [116, 188]];
    const HAIR = [[82, 90], [96, 72], [118, 70], [134, 84], [128, 96], [108, 92], [96, 102], [90, 120], [80, 124], [76, 106]];
    D.person_sit = {
      kind: 'person', w: 340, h: 470, ground: 458, facing: 1,
      layers: ['body', 'arm'],
      draw(ctx, layer) {
        if (layer !== 'arm') {
        cutout(ctx, BODY);
        shape(ctx, BODY, '#4a5a6a');
        ctx.save(); clipTo(ctx, BODY);
        shape(ctx, [[60, 50], [150, 50], [150, 162], [60, 162]], '#d8b08c');
        shape(ctx, [[60, 296], [300, 296], [300, 360], [60, 360]], '#2c2a36');
        shape(ctx, [[230, 340], [300, 340], [300, 470], [230, 470]], '#2d2a2a');
        shape(ctx, [[230, 436], [300, 436], [300, 470], [230, 470]], '#171311');
        ctx.restore();
        fur(ctx, BODY, [60, 160, 160, 300], () => Math.PI / 2, ['#384756', '#5e7184'], 200, 81, 12, 1.4, .4);
        shape(ctx, HAIR, '#3a2a20'); line(ctx, HAIR, 2, INK, true, .8);
        eye(ctx, 120, 106, 3.4, [1, 0.3]);
        pen(ctx, [[130, 124], [124, 126]], 1.6, INK, .8);
        pen(ctx, [[106, 168], [110, 230], [108, 296]], 2, INK, .55);
        for (const y of [196, 236, 274]) button(ctx, 116, y, 6);
        pen(ctx, [[160, 300], [220, 306], [262, 318]], 1.8, INK, .5);
        outline(ctx, BODY);
        }
        if (layer === 'body') return;
        cutout(ctx, ARM, 5); shape(ctx, ARM, '#506275');
        fur(ctx, ARM, [116, 170, 310, 320], (x) => 0.6 - (x - 120) * 0.003, ['#384756', '#6a7f93'], 110, 82, 10, 1.3, .4);
        shade(ctx, ARM, [[262, 280], [320, 280], [320, 330], [262, 330]], '#d8b08c');
        line(ctx, [[286, 300], [300, 302]], 1.2, INK, false, .6); line(ctx, [[284, 308], [298, 312]], 1.2, INK, false, .6);
        outline(ctx, ARM, 2.6);
      },
      handles: { head: [106, 100], chest: [106, 210], hip: [100, 320], knee: [256, 318], foot_a: [262, 456], shoulder: [128, 186], elbow: [200, 272], hand: [298, 306] },
      features: [{ name: 'eye', c: [120, 106], r: 9 }, ...[196, 236, 274].map((y, k) => ({ name: 'button' + k, c: [116, y], r: 10 }))]
    };
  }

  const api = { D, INK, PAPER, cr, rng };
  if (typeof module !== 'undefined') module.exports = api; else root.DRAWINGS = api;
})(typeof window !== 'undefined' ? window : globalThis);
