"""La Belle Hortense: three proposal keyframes + board.

python3 -I kf.py <oulipo root>
Deterministic. Decodes sources with PIL/ffmpeg-extracted PNGs only.
"""
import sys, os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/home/user/bolas/paeleo/scion/oulipo'
SRC = os.path.join(ROOT, 'films/sources')
MINE = os.path.join(SRC, 'la-belle-hortense')
OUT = os.path.join(ROOT, 'films/swarm/la-belle-hortense/proposals')
W, H = 1280, 720
CB = '/usr/share/fonts/X11/Type1/c0583bt_.pfb'      # Courier 10 Pitch Bold
CR = '/usr/share/fonts/X11/Type1/c0419bt_.pfb'      # Courier 10 Pitch
def font(sz, bold=True): return ImageFont.truetype(CB if bold else CR, sz)

# ---------------- the sextine machine (Hard proof fixture) ----------------
P = [6, 1, 5, 2, 4, 3]
def nxt(o): return [o[p - 1] for p in P]
ORD = [list('ABCDEF')]
for _ in range(5): ORD.append(nxt(ORD[-1]))
assert ORD[1] == list('FAEBDC')
o = ORD[0]
for _ in range(6): o = nxt(o)
assert o == list('ABCDEF')
assert all(len(set(r)) == 6 for r in ORD)
WORD = dict(A='manteau', B='cloche', C='clé', D='banc', E='reçu', F='porte')
# module V (index 4): D E A C F B -> banc reçu manteau clé porte cloche
assert ORD[4] == list('DEACFB')

RED = np.array([0.84, 0.10, 0.09]); GREEN = np.array([0.16, 0.62, 0.20])
BRASS = np.array([0.92, 0.72, 0.28]); OCHRE = np.array([0.80, 0.52, 0.16])

def f32(im): return np.asarray(im.convert('RGB'), np.float32) / 255.
def u8(a): return Image.fromarray(np.clip(a * 255 + .5, 0, 255).astype(np.uint8))
def lum(a): return a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114

def stencil(gray, mask, dye, lift=0.0):
    """Pathé-style stencil colour: transparent dye over the B&W print inside a cut mask.
    lift = printing the stencilled region lighter so the dye reads (print density)."""
    g = lift + (1 - lift) * gray
    return (g[..., None] * dye) * mask[..., None]

def shift(a, dx, dy=0):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(a, M, (a.shape[1], a.shape[0]), borderMode=cv2.BORDER_REFLECT)

# ---------------- cutout: conductor (FSA/OWI 1943, LoC 2017844115) ----------------
def cut_conductor():
    """Cut by density: the coat prints dark against the pale wall; the head, hand and
    newspaper are added with hand-placed ellipses; holes (shirt, collar) are filled."""
    im = cv2.imread(os.path.join(SRC, 'la-machine-a-tuer-le-temps/loc_2017844115.jpg'))
    x0, y0, x1, y1 = 368, 285, 680, 1000
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)[y0:y1, x0:x1] / 255.
    gs = cv2.GaussianBlur(g, (5, 5), 0)
    m = (gs < 0.36).astype(np.uint8)
    m[:, :18] = 0; m[:, 290:] = 0; m[700:] = 0
    m[:120, :70] = 0                                   # wall shadow behind the head
    for (c, ax) in (((150, 95), (50, 62)), ((150, 30), (62, 26)), ((145, 240), (40, 22)), ((222, 345), (24, 36))):
        cv2.ellipse(m, c, ax, 0, 0, 360, 1, -1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = (lab == k).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    ff = m.copy(); h_, w_ = ff.shape; fm = np.zeros((h_ + 2, w_ + 2), np.uint8)
    cv2.floodFill(ff, fm, (0, 0), 2); m = np.where(ff == 2, 0, 1).astype(np.uint8)
    env = np.zeros_like(m)                             # the scissor line (hand-placed envelope)
    poly = np.array([(112, 22), (150, 12), (222, 40), (222, 70), (205, 120), (252, 150), (262, 280),
                     (252, 335), (250, 450), (246, 620), (240, 640), (198, 642), (196, 705), (148, 705),
                     (140, 645), (22, 615), (16, 560), (40, 300), (72, 160), (112, 140), (100, 95), (106, 50)], np.int32)
    cv2.fillPoly(env, [poly], 1)
    m = m * env
    m = cv2.GaussianBlur(m.astype(np.float32), (5, 5), 0)
    return g, m, (x0, y0)

def warp_piece(g, m, ang, pivot, scale, tx, ty, size):
    """rotate a cut piece about its pivot (piece coords), scale, and place pivot at (tx,ty)."""
    M = cv2.getRotationMatrix2D(pivot, ang, scale)
    M[0, 2] += tx - pivot[0]; M[1, 2] += ty - pivot[1]
    gg = cv2.warpAffine(g, M, size, flags=cv2.INTER_LINEAR, borderValue=0)
    mm = cv2.warpAffine(m, M, size, flags=cv2.INTER_LINEAR, borderValue=0)
    return gg, mm

def over(dst, src, a):
    return dst * (1 - a[..., None]) + src * a[..., None]

# ---------------- KF1 · Le manteau rouge ----------------
def kf1():
    plate = Image.open(os.path.join(SRC, 'recits-dellis-island/Bourr_Loir-et-Cher_50866795131_.jpg')).convert('RGB')
    pa = f32(plate)                         # 1280x960, goods shed with shut door
    # B&W print of the plate + stencils cut from the original's own hues
    hsv = cv2.cvtColor((pa * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    gray = lum(pa)
    grass = ((hsv[..., 0] > 22) & (hsv[..., 0] < 60) & (hsv[..., 1] > 40)).astype(np.float32)
    grass[:400] = 0
    brick = (((hsv[..., 0] < 12) | (hsv[..., 0] > 165)) & (hsv[..., 1] > 70)).astype(np.float32)
    grass = cv2.GaussianBlur(cv2.morphologyEx(grass, cv2.MORPH_OPEN, np.ones((5, 5))), (9, 9), 0)
    brick = cv2.GaussianBlur(brick, (5, 5), 0)
    base = np.repeat((0.08 + 0.85 * gray)[..., None], 3, 2) * np.array([0.93, 0.95, 0.90])
    col = over(base, stencil(gray, np.ones_like(gray), GREEN * 1.25, 0.25), grass)
    col = over(col, stencil(gray, np.ones_like(gray), RED * 1.1, 0.35), brick * 0.85)
    # framing: camera low and close, shed upper-left, grass fills the lower two thirds
    col = cv2.resize(col, (1707, 1280))[300:300 + 900, 0:1600]
    col = cv2.resize(col, (W + 240, H + 80))
    fg = cv2.resize(col[int((H + 80) * .62):], (W + 600, int(H * .55)))  # near grass band (multiplane)
    # figure rig
    g, m, _ = cut_conductor()
    hgt, wid = g.shape
    leg_y = 638                              # coat hem in piece coords (~923 in source)
    body_m = m.copy(); body_m[leg_y + 8:] = 0
    leg_m = m.copy(); leg_m[:leg_y - 6] = 0; leg_m[:, :140] = 0; leg_m[:, 206:] = 0
    face = (g > 0.55).astype(np.float32) * body_m      # skin, collar, newspaper stay unstencilled
    face = cv2.GaussianBlur(face, (5, 5), 0)
    coat = np.clip(body_m - face, 0, 1); coat[:78] = 0     # cap stays black
    hd = np.zeros_like(coat); cv2.ellipse(hd, (150, 100), (58, 74), 0, 0, 360, 1, -1); coat *= 1 - hd
    body_rgb = np.repeat(g[..., None], 3, 2) * 0.95
    gc = np.clip((g - 0.03) / 0.42, 0, 1) ** 0.8          # coat densities re-printed light so the dye reads
    body_rgb = over(body_rgb, stencil(gc, np.ones_like(g), RED * 1.12, 0.12), coat)
    leg_rgb = np.repeat((g * 0.9)[..., None], 3, 2)
    S = 0.84; size = (W, H)
    N = 36; acc = np.zeros((H, W, 3), np.float32)
    keyim = np.asarray(Image.open(os.path.join(MINE, 'skeletonkey.png')).convert('L'), np.float32) / 255.
    kp = keyim[60:640, 160:440]
    km = cv2.GaussianBlur((kp < 0.45).astype(np.float32), (3, 3), 0)
    kg = np.clip(1.0 - kp, 0, 1) * 0.6 + 0.4 * (kp > 0.7)
    kg = cv2.resize(kg, (54, 112)); km = cv2.resize(km, (54, 112))
    for i in range(N):
        s = (i + .5) / N - .5                     # 180-degree shutter, centred on frame 1032
        bx = 120 - int(round(90 * s))
        fr = col[40:40 + H, bx:bx + W].copy()
        fy = H - fg.shape[0]
        fx = 300 - int(round(260 * s))
        band = fg[:, fx:fx + W]
        bandm = np.clip((np.arange(fg.shape[0])[:, None] - 30) / 60., 0, 1) * np.ones((1, W))
        fr[fy:] = over(fr[fy:], band, bandm.astype(np.float32))
        # stride: phase advances ~0.09 cycle over the open shutter
        ph = 0.22 + 0.12 * (s + .5)
        a1 = 34 * math.sin(2 * math.pi * ph); a2 = -a1
        cx, cy = 690 - 6 * s, 30
        lean = 9
        piv = (172., float(leg_y))
        Mb = cv2.getRotationMatrix2D(piv, lean, S)
        hip = (cx, cy + leg_y * S)
        Mb[0, 2] += hip[0] - piv[0]; Mb[1, 2] += hip[1] - leg_y
        bg_ = cv2.warpAffine(body_rgb, Mb, size); bm_ = cv2.warpAffine(body_m, Mb, size)
        for ang, shade in ((a2, 0.6), (a1, 1.0)):
            Ml = cv2.getRotationMatrix2D(piv, ang + lean, S)
            Ml[0, 2] += hip[0] - piv[0]; Ml[1, 2] += hip[1] - leg_y
            Ml = Ml @ np.array([[1, 0, 0], [0, 1.0, 0], [0, 0, 1]]) if False else Ml
            # substitution shin: the cut leg stretched 1.7x below the hem (a longer limb card)
            T = np.array([[1, 0, 0], [0, 1.7, -0.7 * piv[1]], [0, 0, 1]], np.float64)
            Ml2 = (np.vstack([Ml, [0, 0, 1]]) @ T)[:2]
            lg = cv2.warpAffine(leg_rgb * shade, Ml2, size); lm = cv2.warpAffine(leg_m, Ml2, size)
            fr = over(fr, lg, lm)
        # contact shadow under the runner
        fr = over(fr, fr * 0.55, cv2.GaussianBlur(cv2.warpAffine(bm_, np.float32([[1, 0, 18], [0, .12, H * .86]]), size), (41, 41), 0) * 0.7)
        fr = over(fr, bg_, bm_)
        # the key slips from the hem: falls ~34 px during the exposure, turning
        kx, ky = int(hip[0] + 95), int(hip[1] + 25 + 16 * (s + .5))
        Mk = cv2.getRotationMatrix2D((27, 56), 40 + 14 * s, 1.0); Mk[0, 2] += kx - 27; Mk[1, 2] += ky - 56
        kk = cv2.warpAffine(kg, Mk, size); kmm = cv2.warpAffine(km, Mk, size)
        krgb = stencil(kk, np.ones_like(kk), BRASS, 0.35)
        fr = over(fr, krgb, kmm)
        acc += fr
    out = acc / N
    out = np.clip(out, 0, 1)
    im = u8(out)
    d = ImageDraw.Draw(im)
    # typed title block (typewriter slab, black then red, as the module's own caption)
    x, y = 70, 548
    d.text((x, y), 'V.', font=font(60), fill=(18, 16, 14))
    d.text((x, y + 66), 'le manteau revient', font=font(54), fill=(205, 28, 26))
    d.text((x + 3, y + 130), 'banc · reçu · MANTEAU · clé · porte · cloche', font=font(22, False), fill=(20, 20, 18))
    im.save(os.path.join(OUT, 'kf-1.png'))

# ---------------- KF2 · La grille tourne (kinetic type) ----------------
def kf2():
    pa = f32(Image.open(os.path.join(SRC, 'recits-dellis-island/Bourr_Loir-et-Cher_50866798791_.jpg')))
    pa = cv2.resize(pa, (1920, 1440))[700:1440, :]
    # real pan exposure over the meadow: 120 positions, 900 px of travel -> long streaks
    acc = np.zeros_like(pa)
    for i in range(60): acc += shift(pa, -420 * i / 59)
    st = acc / 60
    st = cv2.resize(st, (W, H))
    g = lum(st)
    g = (g - g.mean(1, keepdims=True)) / (g.std(1, keepdims=True) + 1e-6) * 0.22 + 0.55   # print each streak row hard
    g = np.clip(g, 0, 1)
    rows = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    gm = np.clip(1.25 - 1.5 * rows + 0.5 * (g - .55), 0, 1)        # green over the upper field
    om = np.clip((rows - .86) * 6 + 1.2 * (g - .55), 0, 1)        # ochre/red earth at the foot, like the cover
    grain = np.clip(g + 0.25 * (np.sin(np.linspace(0, 60, H))[:, None] * 0.1), 0, 1)
    bg = stencil(grain, gm, GREEN * 1.35, 0.30) + stencil(grain, 1 - gm, np.array([0.9, 0.85, 0.6]), 0.2)
    bg = over(bg, stencil(grain, np.ones_like(g), OCHRE, 0.3), om * 0.9)
    bg = over(bg, stencil(grain, np.ones_like(g), RED, 0.2), (om > .5) * (g > .55) * 0.6)
    im = u8(np.clip(bg, 0, 1)).convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    F = font(25); cw = 128; x0 = 250; y0 = 52; rh = 62
    def cell(r, c): return (x0 + c * cw, y0 + r * rh)
    ink = (14, 14, 12, 255); red = (208, 26, 24, 255)
    romans = ['I', 'II', 'III', 'IV', 'V', 'VI']
    # braid strands: where each motif goes from module r to r+1
    for r in range(4):
        for c, m in enumerate(ORD[r]):
            c2 = ORD[r + 1].index(m)
            a = cell(r, c); b = cell(r + 1, c2)
            pts = [(a[0] + 40 + (b[0] - a[0]) * t, a[1] + 34 + (b[1] - a[1] - 4) * (3 * t * t - 2 * t * t * t)) for t in np.linspace(0, 1, 30)]
            if m == 'A' and r == 3: continue          # the coat's strand IV->V is being travelled now
            d.line(pts, fill=red if m == 'A' else (14, 14, 12, 110), width=5 if m == 'A' else 2)
    for r in range(6):
        d.text((x0 - 90, cell(r, 0)[1]), romans[r], font=font(28), fill=ink if r <= 4 else (14, 14, 12, 90))
        for c, m in enumerate(ORD[r]):
            x, y = cell(r, c)
            if r < 4:
                d.text((x, y), WORD[m], font=F, fill=red if m == 'A' else (14, 14, 12, 255 - 30 * (3 - r)))
            elif r == 4 and c < 2:
                d.text((x, y), WORD[m], font=F, fill=ink)
            elif r == 4 and c > 2:
                d.text((x, y + 6), '_' * len(WORD[m]), font=F, fill=(14, 14, 12, 120))
            elif r == 5:
                d.text((x, y + 6), '_______', font=F, fill=(14, 14, 12, 60))
    im = Image.alpha_composite(im, lay)
    # the moving word: 'manteau' travels from IV/5 to V/3 along its strand, eased (harmonic in/out);
    # the frame integrates 40 sub-positions of a 180-degree shutter at t = 0.78 of the move
    a = np.array(cell(3, ORD[3].index('A')), float); b = np.array(cell(4, 2), float)
    acc = np.zeros((H, W), np.float32)
    for i in range(40):
        t = 0.84 + 0.10 * i / 39
        e = 3 * t * t - 2 * t * t * t
        p = a + (b - a) * np.array([t, e])
        w = Image.new('L', (W, H), 0)
        ImageDraw.Draw(w).text((p[0], p[1]), 'manteau', font=font(29), fill=255)
        acc += np.asarray(w, np.float32) / 255. * (0.25 + 2.2 * (i / 39) ** 3)
    acc = np.clip(acc / acc.max() * 1.15, 0, 1)
    ra = np.dstack([np.full((H, W), 208), np.full((H, W), 26), np.full((H, W), 24), acc * 255]).astype(np.uint8)
    im = Image.alpha_composite(im, Image.fromarray(ra, 'RGBA'))
    d = ImageDraw.Draw(im)
    # the module's clause being typed below the grid (write-on stops mid-word)
    d.text((70, 470), 'V.3', font=font(44), fill=(14, 14, 12))
    d.text((70, 522), 'le manteau revient', font=font(62), fill=(205, 28, 26))
    d.text((70, 596), 'en cour', font=font(62), fill=(14, 14, 12))
    tw = d.textlength('en cour', font=font(62))
    d.rectangle((70 + tw + 4, 600, 70 + tw + 34, 656), fill=(14, 14, 12))   # typewriter cursor
    d.text((842, 470), 'I   A B C D E F', font=font(22, False), fill=(14, 14, 12))
    d.text((842, 496), 'V   D E A C F B', font=font(22, False), fill=(14, 14, 12))
    d.text((842, 522), '[6,1,5,2,4,3]', font=font(22, False), fill=(205, 28, 26))
    im.convert('RGB').save(os.path.join(OUT, 'kf-2.png'))

# ---------------- KF3 · Le passager de Vincennes (archive recut) ----------------
def kf3():
    MIA = os.path.join(MINE, 'mia')
    def frame(n, box=None):
        a = f32(Image.open(os.path.join(MIA, n)))
        if box: a = a[box[1]:box[3], box[0]:box[2]]
        return a
    main = frame('vinc_22.png', (88, 4, 552, 356))          # Méliès 1896, active picture
    main = cv2.resize(lum(main), (928, 704), interpolation=cv2.INTER_LANCZOS4)
    main = cv2.GaussianBlur(np.clip(main, 0, 1), (3, 3), 0) ** 0.85
    h, w = main.shape
    # iris on the passenger's coat (period iris, cut as a soft circular matte)
    cx, cy = int((350 - 88) / 464 * w), int((245 - 4) / 352 * h)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    iris = np.clip((330 - r) / 60, 0, 1)
    tint = stencil(main, np.ones_like(main), np.array([0.30, 0.78, 0.34]), 0.06)   # green tint bath
    sp = np.array([(330, 185), (366, 182), (386, 200), (396, 262), (393, 326), (314, 329), (311, 262), (318, 205)], float)
    sp = ((sp - [88, 4]) * [928 / 464, 704 / 352]).astype(np.int32)
    coat = np.zeros_like(main); cv2.fillPoly(coat, [sp], 1.0)          # the stencil, cut by hand
    coat = cv2.GaussianBlur(coat, (9, 9), 0)
    tint = over(tint, stencil(np.clip(main * 1.15, 0, 1) ** 1.3, np.ones_like(main), RED * 1.25, 0.0), coat)  # hand-stencilled coat
    tint = tint * (0.18 + 0.82 * iris[..., None])
    can = np.zeros((H, W, 3), np.float32) + np.array([0.05, 0.07, 0.05])
    can[8:8 + h, 8:8 + w] = tint
    im = u8(can); d = ImageDraw.Draw(im)
    # right column: module V in order, six archive shots; slot 3 lit
    shots = [('46cd8d58_2.png', 'banc'), ('3b9d2889_10.png', 'reçu'), ('vinc_22.png', 'MANTEAU'),
             ('7102b861_2.5.png', 'clé'), ('a267fee7_0.5.png', 'porte'), ('381d177e_5.png', 'cloche')]
    X = 8 + w + 22; tw_ = W - X - 16; th = 92
    d.text((X, 14), 'V  [D E A C F B]', font=font(22), fill=(232, 228, 210))
    for k, (n, lab) in enumerate(shots):
        a = frame(n, (88, 4, 552, 356) if n.startswith('vinc') else None)
        a = lum(a)
        hh = th; ww = int(a.shape[1] * hh / a.shape[0]); ww = min(ww, 140)
        a = cv2.resize(a, (ww, hh))
        dye = np.array([0.30, 0.78, 0.34]) if k != 2 else np.array([0.95, 0.35, 0.30])
        t = u8(stencil(a, np.ones_like(a), dye, 0.06) * (1.0 if k == 2 else 0.6))
        y = 50 + k * (th + 18)
        im.paste(t, (X, y))
        d.text((X + ww + 10, y + 30), f'{k + 1}  {lab}', font=font(22), fill=(232, 40, 34) if k == 2 else (200, 205, 190))
        if k == 2: d.rectangle((X - 3, y - 3, X + ww + 2, y + hh + 2), outline=(232, 40, 34), width=3)
    d.text((40, 640), 'V.3 — le manteau', font=font(48), fill=(222, 34, 30))
    im.save(os.path.join(OUT, 'kf-3.png'))

# ---------------- board ----------------
def board():
    ref = Image.open(os.path.join(ROOT, 'assets/references/hortense.webp')).convert('RGB')
    hh = 360
    ref = ref.resize((int(ref.width * hh / ref.height), hh))
    names = ['1 · Le manteau rouge', '2 · La grille tourne', '3 · Le passager de Vincennes']
    ks = [Image.open(os.path.join(OUT, f'kf-{i}.png')).resize((640, 360)) for i in (1, 2, 3)]
    bw = ref.width + 640 * 3 + 40
    scale = min(1, 2000 / bw)
    B = Image.new('RGB', (bw, hh + 50), (24, 24, 22)); d = ImageDraw.Draw(B)
    B.paste(ref, (0, 50)); d.text((6, 14), 'reference', font=font(20), fill=(230, 230, 220))
    x = ref.width + 10
    for k, n in zip(ks, names):
        B.paste(k, (x, 50)); d.text((x + 6, 12), n, font=font(24), fill=(230, 230, 220)); x += 650
    if scale < 1: B = B.resize((int(bw * scale), int((hh + 50) * scale)), Image.LANCZOS)
    B.save(os.path.join(OUT, 'board.jpg'), quality=88)

if __name__ == '__main__':
    which = sys.argv[2:] or ['1', '2', '3', 'b']
    if '1' in which: kf1()
    if '2' in which: kf2()
    if '3' in which: kf3()
    if 'b' in which: board()
