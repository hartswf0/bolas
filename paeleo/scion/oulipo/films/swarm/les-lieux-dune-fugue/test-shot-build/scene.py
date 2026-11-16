"""Builds the P01 facade (capture B), the hinged leaves, the memory planes and the P03 plate,
and renders any frame of the test shot.  Run directly to bake caches + write test stills."""
import sys, json, math, pickle, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stage import *

OUTDIR = ROOT + "/films/swarm/les-lieux-dune-fugue"
LOG = {"pieces": [], "prints": {}, "events": []}

# ---------------------------------------------------------------- lamp states
LAMP_B = Lamp(x=P + 1500, y=P + 120, z=1500, size=0.10, warm=(1.0, 0.97, 0.92), shadow=0.46)  # evening, right, raking
LAMP_A = Lamp(x=P - 500, y=P - 380, z=1500, size=0.10, warm=(1.0, 0.98, 0.94), shadow=0.42)  # morning, upper left
# memory light: its own direction (upper left, cold), never a stage lamp state (invariant I5 / [pair] 6)
MEM_LIGHT = dict(dx=+5.0, dy=+6.0, blur=3.0, strength=0.40, aperture_dx=+26, aperture_dy=+34)

# ---------------------------------------------------------------- prints (one curve per run)
PR = {
    "PRINT-1 DOOR-C ochre": dict(src="DOOR-C", target=(108, 94, 66), ref_L=0.67, gamma=1.8),
    "PRINT-2 DOOR-C buff": dict(src="DOOR-C", target=(158, 146, 128), ref_L=0.60, gamma=1.0),
    "PRINT-3 DOOR-C iron": dict(src="DOOR-C", target=(52, 43, 29), ref_L=0.38, gamma=0.7),
    "PRINT-4 DOOR-S dark": dict(src="DOOR-S", target=(21, 18, 20), ref_L=0.42, gamma=0.35),
}
SRCIMG = {"DOOR-C": DOOR_C, "DOOR-S": DOOR_S}
PRINTS = {k: print_run(SRCIMG[v["src"]], v["target"], v["ref_L"], v["gamma"], 0, 1.6) for k, v in PR.items()}
LOG["prints"] = {k: dict(v, curve="out_c = target_c * (L/ref_L)**gamma, whole photograph") for k, v in PR.items()}
LOG["prints"]["PRINT-5 BENCH cold"] = dict(src="BENCH", curve="blue-grey ramp lo(28,33,42)->hi(153,170,189) on L")
LOG["prints"]["PRINT-6 BENCH warm"] = dict(src="BENCH", curve="rgb*(1.0,0.95,0.84)*0.9, gamma 1.1")

# ---------------------------------------------------------------- layout (frame coords)
OX0, OX1, OY0 = 125, 520, 216              # door opening; runs out of the bottom
JW = 58
JL0, JR0 = 63, 524                         # jamb x
TOPY = 97                                  # top of carved surround
PLY = 604                                  # plinth top
SILL_Y0, SILL_Y1 = 50, 72


def F(x, y):
    return int(x + P), int(y + P)


def build_facade():
    pcs = []
    st = PRINTS["PRINT-1 DOOR-C ochre"]
    # backing card (handmade): the board the blocks are glued on; seen only in the joints
    back = np.ones((SH, SW, 3), np.float32) * np.array([112, 96, 66], np.float32) / 255 * fibre(SH, SW)
    # ashlar courses: right field and left strip; blocks butted with 1-2 px gaps
    rows = [-P, 72, 160, 248, 336, 424, 514, PLY]
    plain_area, avoid = (1230, 90, 1950, 940), [(1360, 380, 1570, 780)]
    for xa, xb, tag in [(JR0 + JW, W + P, "R"), (-P, JL0, "L")]:
        for r in range(len(rows) - 1):
            y0, y1 = rows[r], rows[r + 1]
            if tag == "R" and y1 <= SILL_Y1 and False:
                continue
            x = xa - int(rng.integers(0, 120)) if tag == "R" else xa
            while x < xb:
                w = int(rng.integers(150, 235)) if tag == "R" else xb - xa
                w = min(w, xb - x + 4) if tag == "L" else w
                gx, gy = rng.uniform(0.9, 1.6), rng.uniform(0.9, 1.5)        # gap = real cut tolerance
                bx0, by0 = max(x, xa) , y0
                bw, bh = int(min(x + w, xb) - bx0 - gx), int(y1 - y0 - gy)
                if bw > 12 and bh > 12:
                    sc = 1.5
                    sx, sy = plain_patch(DOOR_C, int(bw / sc), int(bh / sc), plain_area, avoid, 500)
                    tex = crop_resize(st, sx, sy, sx + int(bw / sc), sy + int(bh / sc), bw, bh)
                    tex *= rng.uniform(0.95, 1.05)
                    pcs.append(Piece(f"ashlar-{tag}{r}-{x}", tex, scissor_alpha(bw, bh, 0.6, 0.45, 0.05),
                                     *F(bx0, by0), 2.0, 0.0, f"DOOR-C {sx},{sy} PRINT-1"))
                x += w
    # one shallow course between the sill and the carved head
    for i, (a, b) in enumerate([(-P, 170), (170, 372), (372, JR0 + JW)]):
        bw, bh = b - a - 2, TOPY - SILL_Y1 - 2
        sx, sy = plain_patch(DOOR_C, int(bw / 1.5), int(bh / 1.5), plain_area, avoid, 500)
        tex = crop_resize(st, sx, sy, sx + int(bw / 1.5), sy + int(bh / 1.5), bw, bh) * rng.uniform(0.96, 1.04)
        pcs.append(Piece(f"course-{i}", tex, scissor_alpha(bw, bh, 0.6, 0.45, 0.05), *F(a + 1, SILL_Y1 + 1), 2.0, 0.0,
                         f"DOOR-C {sx},{sy} PRINT-1"))
    # plain stone above the door: lintel blocks and reveals (between jambs)
    for i, (a, b) in enumerate([(JL0 + JW, 262), (262, 386), (386, JR0)]):
        bw, bh = b - a - 2, OY0 - (TOPY + 30) - 2
        sx, sy = plain_patch(DOOR_C, int(bw / 1.5), int(bh / 1.5), plain_area, avoid, 500)
        tex = crop_resize(st, sx, sy, sx + int(bw / 1.5), sy + int(bh / 1.5), bw, bh) * rng.uniform(0.96, 1.04)
        pcs.append(Piece(f"lintel-{i}", tex, scissor_alpha(bw, bh, 0.6, 0.45, 0.05), *F(a + 1, TOPY + 31), 3.0, 0.0,
                         f"DOOR-C {sx},{sy} PRINT-1"))
    for i, (a, b) in enumerate([(JL0 + JW, OX0), (OX1, JR0)]):        # narrow plain reveals beside the door
        bw, bh = b - a, PLY - (TOPY + 30)
        sx, sy = plain_patch(DOOR_C, bw * 2, int(bh / 0.9), plain_area, avoid, 80)
        tex = crop_resize(st, sx, sy, sx + bw * 2, sy + int(bh / 0.9), bw, bh) * 0.93
        pcs.append(Piece(f"reveal-{i}", tex, scissor_alpha(bw, bh, 0.4, 0.3, 0.0), *F(a, TOPY + 30), 2.5, 0.0,
                         f"DOOR-C {sx},{sy} PRINT-1"))
    # carved vine jambs: the Columbus jamb panel, cut narrow; two cut lengths per jamb (real joint)
    jamb_src = st[312:1088, 480:606]
    js = cv2.resize(jamb_src, (JW, int(jamb_src.shape[0] * JW / jamb_src.shape[1])), interpolation=cv2.INTER_AREA)
    for side, jx in [("L", JL0), ("R", JR0)]:
        y = TOPY + 30
        k = 0
        while y < PLY:
            hh = min(js.shape[0], PLY - y) - 1
            off = 0 if k == 0 else int(rng.integers(0, js.shape[0] - hh)) if js.shape[0] > hh else 0
            tex = js[off:off + hh] * rng.uniform(0.98, 1.03)
            pcs.append(Piece(f"jamb-{side}{k}", tex, scissor_alpha(JW, hh, 0.7, 0.55, 0.07), *F(jx, y), 8.0, 2.0,
                             "DOOR-C 480,312 jamb panel PRINT-1"))
            y += hh + 1; k += 1
    # carved top band: the same jamb carving run horizontally across the head of the surround
    band = np.rot90(js, 1).copy()
    x = JL0
    while x < JR0 + JW:
        ww = min(band.shape[1], JR0 + JW - x)
        pcs.append(Piece(f"headband-{x}", band[:30, :ww] if band.shape[0] >= 30 else band, scissor_alpha(ww, 30, 0.7, 0.55, 0.07),
                         *F(x, TOPY), 8.0, 2.0, "DOOR-C jamb panel (rotated) PRINT-1"))
        x += ww + 1
    # sill under the balcony (projecting stone strip)
    sill_w = JR0 + JW + 30
    sx, sy = plain_patch(DOOR_C, int(sill_w / 1.6), 30, plain_area, avoid, 80)
    tex = crop_resize(st, sx, sy, sx + int(sill_w / 1.6), sy + 30, sill_w, SILL_Y1 - SILL_Y0) * 1.04
    pcs.append(Piece("sill", tex, scissor_alpha(sill_w, SILL_Y1 - SILL_Y0, 0.7, 0.5, 0.05), *F(-P + 2, SILL_Y0), 12.0, 2.0,
                     f"DOOR-C {sx},{sy} PRINT-1"))
    # iron balcony band: the Columbus window grille, printed dark (PRINT-3), cut in two lengths
    ir = PRINTS["PRINT-3 DOOR-C iron"][395:755, 1385:1525]
    irs = cv2.resize(ir, (int(ir.shape[1] * 56 / ir.shape[0]), 56), interpolation=cv2.INTER_AREA)
    strip = np.concatenate([irs] * (SW // irs.shape[1] + 3), 1)
    for i, (a, b) in enumerate([(-P, 300), (300, JR0 + JW + 20)]):
        ww = b - a
        pcs.append(Piece(f"balcony-{i}", strip[:, 7 * i:7 * i + ww], scissor_alpha(ww, 56, 0.6, 0.6, 0.08), *F(a, -P + 4),
                         7.0, 2.0, "DOOR-C window grille 1385,395 PRINT-3"))
    # plinth course (PRINT-2 of DOOR-C marble base)
    pb = PRINTS["PRINT-2 DOOR-C buff"]
    for i, (a, b) in enumerate([(-P, JL0 + JW), (JR0, 700), (700, 850), (850, W + P)]):
        ww, hh = b - a - 2, H + P - PLY
        sx, sy = 1240 + int(rng.integers(0, max(1, 300 - int(ww / 1.5)))), 950
        tex = crop_resize(pb, sx, sy, sx + int(ww / 1.5), sy + int(hh / 1.5), ww, hh)
        pcs.append(Piece(f"plinth-{i}", tex, scissor_alpha(ww, hh, 0.7, 0.5, 0.06), *F(a + 1, PLY), 5.0, 0.0,
                         f"DOOR-C {sx},{sy} PRINT-2"))
    # house-number plaque: HANDMADE lettered card (no source)
    pw, ph = 36, 26
    pl = Image.new("RGB", (pw, ph), (30, 28, 31))
    d = ImageDraw.Draw(pl)
    d.text((pw / 2, ph / 2 + 1), "7", font=ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSerif.ttf", 20),
           fill=(196, 186, 164), anchor="mm")
    pcs.append(Piece("plaque-7", np.asarray(pl).astype(np.float32) / 255, scissor_alpha(pw, ph, 0.5, 0.35, 0.0),
                     *F(632, 166), 6.0, 2.0, "HANDMADE lettered card", curl=0.01))
    return back, pcs


def build_leaves():
    """leaf textures (2x) cut from the Savannah riveted door, printed dark; knob child per leaf"""
    dk = PRINTS["PRINT-4 DOOR-S dark"]
    lw, lh = OX1 - OX0, 760            # whole leaf pair; extends below frame
    half = [(232, 712), (718, 1192)]
    leaves = []
    for i, (a, b) in enumerate(half):
        w2 = (lw // 2 + 7) * 2
        hh = int(round((b - a) * lh * 2 / w2))
        tex = cv2.resize(dk[78:78 + hh, a:b], (w2, lh * 2), interpolation=cv2.INTER_AREA)
        alpha = scissor_alpha(w2, lh * 2, 1.0, 0.9, 0.03)
        fib = cv2.resize(fibre(lh, w2 // 2)[..., 0], (w2, lh * 2))[..., None]
        tex = tex * fib
        # knob child (FK): a stud cut from the same door, fixed in leaf-local coords, raised 4 px
        kx = 30 if i == 1 else w2 - 30
        ky = 2 * 300
        stud = cv2.resize(dk[905:965, 455:515], (26, 26), interpolation=cv2.INTER_AREA) * 1.5
        sa = np.zeros((26, 26), np.float32); cv2.circle(sa, (13, 13), 12, 1.0, -1, cv2.LINE_AA)
        # child shadow on the leaf (lamp B: to the left/down in leaf space when closed)
        shd = np.zeros(alpha.shape, np.float32); shd[ky - 13 + 4:ky + 13 + 4, kx - 13 - 6:kx + 13 - 6] = sa
        tex = tex * (1 - 0.5 * cv2.GaussianBlur(shd, (0, 0), 3))[..., None]
        reg = (slice(ky - 13, ky + 13), slice(kx - 13, kx + 13))
        tex[reg] = tex[reg] * (1 - sa[..., None]) + stud * sa[..., None]
        leaves.append(dict(tex=tex.astype(np.float32), a=alpha, knob=(kx / 2, ky / 2), w=w2 / 2, h=lh))
    return leaves


def leaf_pose(theta_deg, left, c_shift):
    """FK: wall -> jamb -> leaf.  Returns homography from leaf texture (2x) to stage (2x)."""
    th = math.radians(theta_deg)
    lw = (OX1 - OX0) // 2 + 7
    hx = (OX0 - 4) if left else (OX1 + 4)           # hinge axis x (frame coords), tucked under the jamb
    cx, cy = W / 2, H / 2
    def proj(u, v):                                   # u along leaf from hinge, v down
        x = hx + (u * math.cos(th) if left else -u * math.cos(th))
        z = u * math.sin(th)
        k = F_PIN / (F_PIN + z)
        return ((cx + (x - cx) * k) - c_shift + P) * 2, ((cy + (OY0 + v - cy) * k) + P) * 2
    h = 760
    if left:
        quad_l = [(0, 0), (lw * 2, 0), (lw * 2, h * 2), (0, h * 2)]
        dst = [proj(0, 0), proj(lw, 0), proj(lw, h), proj(0, h)]
    else:
        quad_l = [(0, 0), (lw * 2, 0), (lw * 2, h * 2), (0, h * 2)]
        dst = [proj(lw, 0), proj(0, 0), proj(0, h), proj(lw, h)]
    return cv2.getPerspectiveTransform(np.float32(quad_l), np.float32(dst)), proj


def ptx(M, x, y):
    v = M @ np.array([x, y, 1.0]); return v[0] / v[2], v[1] / v[2]


def build_memory():
    """cold print of the Sacramento bench; bench GrabCut-cut onto its own plane (0.6), park (1.0)"""
    cold = cold_print(BENCH)
    bx0, by0, bx1, by1 = 700, 985, 1000, 1245
    b8 = to8(BENCH[by0:by1, bx0:bx1])[..., ::-1].copy()
    gm = np.zeros(b8.shape[:2], np.uint8)
    bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(b8, gm, (22, 18, b8.shape[1] - 44, b8.shape[0] - 40), bg, fg, 8, cv2.GC_INIT_WITH_RECT)
    m = np.where((gm == 1) | (gm == 3), 1, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for k in range(1, n):
        if stats[k, cv2.CC_STAT_AREA] > 400:
            keep[lab == k] = 1
    full = np.zeros(BENCH.shape[:2], np.uint8); full[by0:by1, bx0:bx1] = keep
    cv2.imwrite(CUT + "/bench_mask.png", full[by0:by1, bx0:bx1] * 255)
    # park plane with the bench removed (cv2.inpaint; flagged as an invention under the bench)
    hole = cv2.dilate(full, np.ones((9, 9), np.uint8))
    y0, y1, x0, x1 = 560, 1420, 520, 1200
    park8 = cv2.inpaint(to8(BENCH[y0:y1, x0:x1])[..., ::-1].copy(), hole[y0:y1, x0:x1], 9, cv2.INPAINT_TELEA)
    park = park8[..., ::-1].astype(np.float32) / 255
    return cold, full, park, (x0, y0), hole


COLD, BMASK, PARK_SRC, PARK_O, BHOLE = build_memory()
MSC = 0.62            # memory scale (source px -> frame px)
BENCH_CENTER = (850, 1117)
BENCH_AT = (334, 556)  # frame position of bench centre


def memory_layers():
    s = MSC
    pc = cold_print(PARK_SRC)
    pw, ph = int(pc.shape[1] * s), int(pc.shape[0] * s)
    park = cv2.resize(pc, (pw, ph), interpolation=cv2.INTER_AREA)
    px = BENCH_AT[0] - (BENCH_CENTER[0] - PARK_O[0]) * s
    py = BENCH_AT[1] - (BENCH_CENTER[1] - PARK_O[1]) * s
    park = cv2.GaussianBlur(park, (0, 0), 1.8)            # far plane, out of focus
    canvas = np.zeros((SH, SW, 3), np.float32) + np.array([0.07, 0.08, 0.10], np.float32)
    X, Y = int(px + P), int(py + P)
    ys, xs = slice(max(Y, 0), min(Y + ph, SH)), slice(max(X, 0), min(X + pw, SW))
    canvas[ys, xs] = park[ys.start - Y:ys.stop - Y, xs.start - X:xs.stop - X]
    bx0, by0, bx1, by1 = 700, 985, 1000, 1245
    bt = cv2.resize(COLD[by0:by1, bx0:bx1], (int(300 * s), int(260 * s)), interpolation=cv2.INTER_AREA)
    ba = cv2.resize(BMASK[by0:by1, bx0:bx1].astype(np.float32), (int(300 * s), int(260 * s)), interpolation=cv2.INTER_AREA)
    ba = cv2.GaussianBlur(ba, (0, 0), 0.6)
    bt = cv2.GaussianBlur(bt, (0, 0), 0.8)
    bpos = (BENCH_AT[0] - (BENCH_CENTER[0] - bx0) * s + P, BENCH_AT[1] - (BENCH_CENTER[1] - by0) * s + P)
    return canvas, bt.astype(np.float32), ba.astype(np.float32), bpos


def p03_plate():
    """P03 present: warm print (PRINT-6) of the same photograph; bench cut out on its own plane
    with a lamp-A shadow; front leaf-litter strip raised; held still."""
    x0, y0, x1, y1 = 200, 400, 1520, 1390
    s = W / (x1 - x0)
    warm = np.clip((BENCH * np.array([1.0, 0.95, 0.84])) ** 1.1 * 0.9, 0, 1).astype(np.float32)
    park8 = cv2.inpaint(to8(warm)[..., ::-1].copy(), BHOLE, 9, cv2.INPAINT_TELEA)[..., ::-1].astype(np.float32) / 255
    base = np.zeros((SH, SW, 3), np.float32)
    base[P:P + H, P:P + W] = cv2.resize(park8[y0:y1, x0:x1], (W, H), interpolation=cv2.INTER_AREA)
    base[:P], base[-P:], base[:, :P], base[:, -P:] = base[P:P + 1], base[-P - 1:-P], base[:, P:P + 1], base[:, -P - 1:-P]
    base = cv2.GaussianBlur(base, (0, 0), 0.9) * fibre(SH, SW)
    bx0, by0, bx1, by1 = 700, 985, 1000, 1245
    bw, bh = int((bx1 - bx0) * s), int((by1 - by0) * s)
    bt = cv2.resize(warm[by0:by1, bx0:bx1], (bw, bh), interpolation=cv2.INTER_AREA)
    ba = cv2.resize(BMASK[by0:by1, bx0:bx1].astype(np.float32), (bw, bh), interpolation=cv2.INTER_AREA)
    pcs = [Piece("p03-bench", bt, np.clip(ba, 0, 1), int((bx0 - x0) * s) + P, int((by0 - y0) * s) + P, 4.0, 0.0,
                 "BENCH PRINT-6 GrabCut", curl=0.0)]
    # front litter strip, cut with a scissored top edge from the bottom of the same print
    sy = int(H * 0.86)
    lt = base[P + sy:SH, :].copy()
    la = scissor_alpha(SW, SH - P - sy, 0.5, 2.2, 0.15)
    pcs.append(Piece("p03-litter", lt, la, 0, P + sy, 6.0, 0.0, "BENCH PRINT-6 front strip", curl=0.0))
    pcs[-1].fib = np.ones_like(pcs[-1].fib)
    can, _ = compose(base, pcs, LAMP_A, LOG["pieces"])
    return can


def bake():
    back, pcs = build_facade()
    LOG["pieces"].clear()
    fac, fa = compose(np.zeros((SH, SW, 3), np.float32), pcs, LAMP_B, LOG["pieces"])
    # the backing card is only seen inside the facade (not in the door opening)
    hole = np.zeros((SH, SW), np.float32); hole[OY0 + P:, OX0 + P:OX1 + P] = 1
    board = 1 - hole
    # shadows of all pieces onto the backing are in `fac` only where pieces exist; recompose on the card
    fac_on_card, _ = compose(back, pcs, LAMP_B)
    fac_a = np.maximum(fa, board)
    fac_rgb = np.where(fa[..., None] > 0, fac_on_card, fac_on_card)
    # facade height-map shadow cast onto the recessed leaves (jambs + lintel stand ~10 px above leaves)
    occ = np.clip(fa, 0, 1)
    dx, dy, blur = LAMP_B.offset(OX1 + P, OY0 + P, -6, 14)
    leaf_shadow = cv2.GaussianBlur(shift(occ, dx, dy), (0, 0), blur)
    mem = memory_layers()
    leaves = build_leaves()
    p03 = p03_plate()
    pickle.dump(dict(fac_rgb=fac_rgb, fac_a=fac_a, leaf_shadow=leaf_shadow, mem=mem, leaves=leaves, p03=p03,
                     log=LOG), open(CUT + "/bake.pkl", "wb"))


# ---------------------------------------------------------------- timing (24 fps, paper on twos)
FPS = 24
T_OPEN, LAG, T_CLOSE, T_CUT, DUR = 0.75, 4 / 24, 6.2, 8.0, 10.0
TH_L, TH_R = 58.0, 64.0
T_FALL = 1.2


def theta(t, t0, tmax, tc):
    if t < t0:
        return 0.0
    if t < tc:                                     # opening: heavy push, under-damped (3 deg overshoot)
        s = t - t0
        s = max(0.0, s - 0.12 * (1 - math.exp(-s / 0.12)))          # inertia at the start of the push
        z, w = 0.69, 3.2
        wd = w * math.sqrt(1 - z * z)
        return tmax * (1 - math.exp(-z * w * s) * (math.cos(wd * s) + z / math.sqrt(1 - z * z) * math.sin(wd * s)))
    s = t - tc                                     # closing: swings shut, accelerating, contact + rebound
    if s < T_FALL:
        return tmax * (1 - (s / T_FALL) ** 2)
    u = s - T_FALL
    return 2.2 * abs(math.sin(math.pi * u / 0.11)) * math.exp(-u / 0.05) if u < 0.3 else 0.0


def state(t):
    tq = math.floor(t * 12) / 12.0                  # paper moves on twos
    tl = theta(tq, T_OPEN, TH_L, T_CLOSE)
    tr = theta(tq, T_OPEN + LAG, TH_R, T_CLOSE + LAG)
    c = 6.0 * (0.5 - 0.5 * math.cos(math.pi * min(max((tq - T_OPEN) / 3.2, 0), 1)))
    settle = -2.0 * (1 - min(max((tq - 1.3) / 0.9, 0), 1) ** 2)
    return tl, tr, c, settle


CONTACT_L = T_CLOSE + T_FALL
CONTACT_R = T_CLOSE + LAG + T_FALL
