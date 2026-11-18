"""TEST SHOT S5c (film 51.5-58.0 s): the key narrates beat 5. 6.5 s, 960x540, 24 fps.

Material: FORAGED Agence Rol 1917 print (PD) cut by GrabCut + trimap matte and rigged as an FK puppet;
FORAGED CC0 Index of American Design watercolour key (Edna C. Rex, NGA 24027); FORAGED sound
(footsteps CC BY-SA 4.0, thud PD, 1935 optical-track room tone). HANDMADE: cut-paper bench/door, page,
type. Rendered through films/kit.py (Film/Mix), unedited. Run: python3 -I test_shot.py [--stills t ...]
"""
import sys, math, wave, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films')
import kit
from kit import Film, ease, ramp, smooth, clamp, lerp

M = Path('/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style/test-shot')
OUTDIR = Path('/home/user/bolas/paeleo/scion/oulipo/films/swarm/exercices-de-style')
W, H, FPS, DUR = 960, 540, 24, 6.5
RIG = json.load(open(M / 'rig_pieces.json'))

# ---------------------------------------------------------------- palette (sampled from the reference)
PAGE = (253, 219, 140)      # #fddb8c median page
PAGE_HI = (254, 228, 152)   # #fee498
PAGE_TOP = (255, 239, 178)  # #ffefb2
GHOST = (253, 239, 177)     # #fdefb1, LIGHTER than the page
RED = (214, 40, 10)         # #d6280a
BLACK = (25, 19, 4)         # #191304
GREEN = (40, 55, 22)        # #283716
CREAM = (236, 228, 196)     # bus cream
BAND = (142, 132, 123)      # #8e847b
SHADOW = (92, 58, 14)

F = '/usr/share/fonts/truetype/'
def fnt(p, s): return ImageFont.truetype(p, s)
SERIF_I = F + 'liberation/LiberationSerif-Italic.ttf'
HUMAN = F + 'crosextra/Carlito-Regular.ttf'
HUMAN_B = F + 'crosextra/Carlito-Bold.ttf'
FACES = [F + 'liberation/LiberationSerif-BoldItalic.ttf', '/usr/share/fonts/opentype/inter/Inter-Black.otf',
         F + 'crosextra/Caladea-Italic.ttf', F + 'dejavu/DejaVuSerif-Bold.ttf', F + 'freefont/FreeSansBold.ttf',
         F + 'crosextra/Carlito-BoldItalic.ttf', F + 'liberation/LiberationSerif-Regular.ttf']

rs = np.random.RandomState(5)

def blurnoise(h, w, sigma, seed):
    r = np.random.RandomState(seed).normal(0, 1, (h, w)).astype(np.float32)
    im = Image.fromarray(((r * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
    a = np.asarray(im, np.float32) - 128
    return a / (np.abs(a).max() + 1e-6)

# ---------------------------------------------------------------- the printed page (static paper mottle)
def make_page():
    m = 0.55 * blurnoise(H, W + 200, 40, 1) + 0.45 * blurnoise(H, W + 200, 9, 2)
    m = (m - m.min()) / (m.max() - m.min())
    p = np.array(PAGE, np.float32); hi = np.array(PAGE_HI, np.float32); top = np.array(PAGE_TOP, np.float32)
    x = m[..., None]
    a = np.where(x < 0.62, p + (hi - p) * (x / 0.62), hi + (top - hi) * ((x - 0.62) / 0.38) * 0.5)
    a = p * 0.5 + a * 0.5 + (hi - p) * 0.25
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))
PAGE_IMG = make_page()

def fibre(size, seed, amt=0.05):
    h, w = size[1], size[0]
    n = 0.6 * blurnoise(h, w, 0.8, seed) + 0.4 * blurnoise(h, w, 3, seed + 1)
    return Image.fromarray((255 * (1 - amt + amt * (n * 0.5 + 0.5))).clip(0, 255).astype(np.uint8))

def cut_paper(poly, color, seed, jitter=1.6, size=(W + 400, H)):
    """A scissor-cut polygon: edges subdivided and nudged once (cut once, it does not boil)."""
    r = np.random.RandomState(seed); pts = []
    poly = list(poly) + [poly[0]]
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 7))
        for k in range(n):
            f = k / n
            pts.append((x0 + (x1 - x0) * f + r.uniform(-jitter, jitter), y0 + (y1 - y0) * f + r.uniform(-jitter, jitter)))
    m = Image.new('L', size, 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.6))
    col = Image.new('RGB', size, color)
    col = ImageChops.multiply(col, fibre(size, seed).convert('RGB'))
    col.putalpha(m)
    return col

def lift_shadow(layer, off=(2, 3), blur=3.5, alpha=0.30):
    a = layer.getchannel('A').filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    sh = Image.new('RGBA', layer.size, SHADOW + (0,)); sh.putalpha(a)
    out = Image.new('RGBA', layer.size, (0, 0, 0, 0)); out.alpha_composite(sh, off); return out

# ---------------------------------------------------------------- handmade planes
# Bench (plane 1.0): wider than the frame so it can slide.  Offset by -200 in its own sheet.
BX = -200
bench = Image.new('RGBA', (W + 400, H), (0, 0, 0, 0))
for poly, col, sd in [
    ([(0, 352), (W + 400, 349), (W + 400, 377), (0, 380)], GREEN, 11),      # back slat
    ([(0, 380), (W + 400, 377), (W + 400, 384), (0, 386)], CREAM, 12),      # cream gap, the bus's cream
    ([(0, 386), (W + 400, 384), (W + 400, 408), (0, 410)], (46, 62, 26), 13),  # middle slat
    ([(0, 410), (W + 400, 408), (W + 400, 414), (0, 415)], CREAM, 14),
    ([(0, 415), (W + 400, 414), (W + 400, 445), (0, 445)], GREEN, 15),      # front lip
]:
    bench.alpha_composite(cut_paper(poly, col, sd))
BENCH = Image.alpha_composite(lift_shadow(bench, (0, -2), 4, 0.35), bench)

# Service door (plane 0.55): fixed, closed.  Drawn in its own sheet at absolute x.
door = Image.new('RGBA', (W + 400, H), (0, 0, 0, 0))
DX = 0
dx0, dy0, dx1, dy1 = 842, 30, 978, 350
door.alpha_composite(cut_paper([(dx0 - 8, dy0 - 10), (dx1 + 8, dy0 - 10), (dx1 + 8, dy1), (dx0 - 8, dy1)], CREAM, 21))  # frame
door.alpha_composite(cut_paper([(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)], GREEN, 22))
door.alpha_composite(cut_paper([(dx0 + 14, dy0 + 22), (dx1 - 14, dy0 + 22), (dx1 - 14, dy0 + 140), (dx0 + 14, dy0 + 140)], (52, 70, 30), 23, 1.2))
door.alpha_composite(cut_paper([(dx0 + 14, dy0 + 160), (dx1 - 14, dy0 + 160), (dx1 - 14, dy1 - 22), (dx0 + 14, dy1 - 22)], (52, 70, 30), 24, 1.2))
door.alpha_composite(cut_paper([(dx0 + 10, dy0 + 150), (dx0 + 22, dy0 + 148), (dx0 + 22, dy0 + 172), (dx0 + 10, dy0 + 172)], CREAM, 25, 0.8))  # handle plate
door.alpha_composite(cut_paper([(dx0 + 30, dy0 + 54), (dx1 - 30, dy0 + 54), (dx1 - 30, dy0 + 80), (dx0 + 30, dy0 + 80)], CREAM, 26, 0.8))  # plaque
ImageDraw.Draw(door).text(((dx0 + dx1) / 2 + 4, dy0 + 67), 'SERVICE', font=fnt(HUMAN_B, 13), fill=BLACK + (235,), anchor='mm')
DOOR = Image.alpha_composite(lift_shadow(door), door)

# Ghost « Je » (plane 0.25): lighter than the page, cropped, huge.
ghost = Image.new('RGBA', (W + 400, H), (0, 0, 0, 0))
ImageDraw.Draw(ghost).text((60, -150), 'Je', font=fnt(F + 'liberation/LiberationSerif-Regular.ttf', 640), fill=GHOST + (255,))
GHOST_IMG = ghost

# ---------------------------------------------------------------- foraged pieces
def tint_bw(img, amt=0.08):
    """The Rol print is genuinely B&W: force chroma ~0 then a <=8% warm tint toward the page."""
    a = np.asarray(img.convert('RGBA'), np.float32)
    L = a[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    g = np.repeat(L[..., None], 3, 2)
    t = g * (1 - amt) + (g * np.array(PAGE, np.float32) / 255.0) * amt
    a[..., :3] = t
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

P = {}
for k, v in RIG.items():
    im = tint_bw(Image.open(M / v['file']))
    piv = (v['pivot'][0] + v['origin'][0], v['pivot'][1] + v['origin'][1])  # pivot in source coords
    P[k] = dict(img=im, origin=tuple(v['origin']), pivot=piv)
# far leg slightly darker (depth, a print-shop trick: a darker proof of the same cut)
def darker(im, f):
    a = np.asarray(im, np.float32).copy(); a[..., :3] *= f; return Image.fromarray(a.clip(0, 255).astype(np.uint8))
for k in ('thigh', 'shin'):
    im = P[k]['img']; w0 = im.size[0]; im2 = im.resize((int(w0 * 1.45), im.size[1]), Image.LANCZOS)
    P[k]['img'] = im2; P[k]['origin'] = (P[k]['pivot'][0] - (P[k]['pivot'][0] - P[k]['origin'][0]) * 1.45, P[k]['origin'][1])
for k in ('thigh', 'shin', 'shoe'):
    P[k + '_far'] = dict(P[k]); P[k + '_far']['img'] = darker(P[k]['img'], 0.78)

KEY = Image.open(M / 'key_cut.png').convert('RGBA').rotate(-90, expand=True, resample=Image.BICUBIC)  # bow left, bit up
KL = 432.0
KS = KL / KEY.size[0]
KEY = KEY.resize((int(KEY.size[0] * KS), int(KEY.size[1] * KS)), Image.LANCZOS)
KW, KH = KEY.size

def place(canvas, img, src_origin, src_pivot, world, angle_deg, scale):
    """Paste an RGBA piece so that its pivot (source coords) lands on `world`, rotated and scaled.
    y-down convention; positive angle turns the piece's 'down' toward -x."""
    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)
    # forward map: w = world + scale*R*(p - pivot),  R=[[c,-s],[s,c]] applied to (x,y) gives (c x - s y, s x + c y)
    # we want down (0,1) -> (-sin, cos): use R' = [[c, -s],[s, c]] with s -> sin(th): (0,1)->(-s, c). ok.
    # inverse: p = pivot + R^T (w - world)/scale ; then local = p - origin
    ox, oy = src_origin; px, py = src_pivot; wx, wy = world
    a, b = c / scale, s / scale
    d, e = -s / scale, c / scale
    # p_x = px + a*(X-wx) + b*(Y-wy) ; p_y = py + d*(X-wx) + e*(Y-wy)
    A = (a, b, px - ox - a * wx - b * wy, d, e, py - oy - d * wx - e * wy)
    layer = img.transform(canvas.size, Image.AFFINE, A, resample=Image.BICUBIC)
    canvas.alpha_composite(layer)

def R(angle_deg, v):
    th = math.radians(angle_deg); c, s = math.cos(th), math.sin(th)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])

# ---------------------------------------------------------------- the walk (FK, on twos, no-slip feet)
HIP = (650.0, 1600.0)                        # body root in source px
HIPJ = {'far': (640.0, 1600.0), 'near': (662.0, 1600.0)}
L1, L2 = 330.0, 280.0                        # thigh, shin lengths (source px)
ANK_SHOE = (585.0, 215.0)
T0, STEP = 1.95, 0.5                         # walk start, seconds per step
A_TH = 22.0
SC0 = 0.122
HORIZON, G0 = 226.0, 350.0

def leg_angles(phi):
    """phi in [0,1): stance 0-0.5, swing 0.5-1. Returns thigh angle, shin angle, shoe angle (absolute)."""
    if phi < 0.5:
        s = phi / 0.5
        a = A_TH * (1 - 2 * s)
        b = 5 * math.sin(math.pi * s)
        return a, a - b, 0.0
    s = (phi - 0.5) / 0.5
    a = -A_TH + 2 * A_TH * smooth(s)
    b = 58 * math.sin(math.pi * s) ** 1.2
    return a, a - b, -14 * math.sin(math.pi * min(1, s * 1.4))

def ankle_rel(th, sh, sc):
    k = R(th, (0, L1)); a = R(sh, (0, L2))
    return ((k[0] + a[0]) * sc, (k[1] + a[1]) * sc)

def steps_done(u):
    return max(0.0, u / STEP)

def scale_at(u):
    return SC0 * (0.97 ** steps_done(u))

def ground_at(sc):
    return HORIZON + (G0 - HORIZON) * sc / SC0

# simulate the hip path on twos, state carried frame to frame
WALK = {}
def simulate():
    hipx = 452.0
    planted = None; stance_prev = None
    for k in range(0, int(DUR * FPS) + 2, 2):
        t = k / FPS; u = t - T0
        sc = scale_at(u); g = ground_at(sc)
        if u < 0:
            ang = {'far': (0.0, 0.0, 0.0), 'near': (0.0, 0.0, 0.0)}
            rel = ankle_rel(0, 0, sc)
            hipy = g - rel[1]
            WALK[k] = dict(hip=(hipx, hipy), ang=ang, sc=sc, contact=False, ph=0.0)
            continue
        ph = u / (2 * STEP)
        phis = {'near': ph % 1.0, 'far': (ph + 0.5) % 1.0}
        ang = {n: leg_angles(p) for n, p in phis.items()}
        stance = 'near' if phis['near'] < 0.5 else 'far'
        rel = ankle_rel(ang[stance][0], ang[stance][1], sc)
        contact = False
        if stance != stance_prev:
            # new stance foot: plant it where it is now (computed from the current hip)
            planted = hipx + rel[0]
            contact = stance_prev is not None or True
            stance_prev = stance
        hipx = planted - rel[0]
        hipy = g - rel[1] - 0.0
        WALK[k] = dict(hip=(hipx, hipy), ang=ang, sc=sc, contact=contact, ph=ph, stance=stance)
simulate()
CONTACTS = [k / FPS for k, v in sorted(WALK.items()) if v.get('contact')]

def body_xf(hipw, sc, lean, p):
    v = R(lean, (p[0] - HIP[0], p[1] - HIP[1]))
    return (hipw[0] + sc * v[0], hipw[1] + sc * v[1])

def draw_visitor(canvas, k, dx):
    kk = (k // 2) * 2                     # puppet on twos
    st = WALK[min(kk, max(WALK))]
    t = kk / FPS; u = t - T0
    sc = st['sc']; hip = (st['hip'][0] + dx, st['hip'][1])
    walking = u >= 0
    ph = st['ph']
    lean = -2.0 * ease(t, T0 - 0.2, T0 + 0.3)
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    for side in ('far', 'near'):
        th, sh, shoe = st['ang'][side]
        sfx = '_far' if side == 'far' else ''
        j = body_xf(hip, sc, 0, HIPJ[side])
        place(layer, P['thigh' + sfx]['img'], P['thigh']['origin'], P['thigh']['pivot'], j, th, sc * L1 / 340)
        kn = (j[0] + R(th, (0, L1))[0] * sc, j[1] + R(th, (0, L1))[1] * sc)
        place(layer, P['shin' + sfx]['img'], P['shin']['origin'], P['shin']['pivot'], kn, sh, sc * L2 / 280)
        an = (kn[0] + R(sh, (0, L2))[0] * sc, kn[1] + R(sh, (0, L2))[1] * sc)
        place(layer, P['shoe' + sfx]['img'], P['shoe']['origin'], P['shoe']['pivot'], (an[0], an[1] - 4 * sc), shoe, sc * 0.95)
    # coat hem: secondary motion, lags the legs by ~3 frames, trails behind the walk direction
    lag = (ph - 0.06) if walking else 0.0
    hem = (-2.5 * ease(t, T0, T0 + 0.5) + (3.2 * math.sin(2 * math.pi * 2 * lag) if walking else 0.0))
    place(layer, P['hem']['img'], P['hem']['origin'], P['hem']['pivot'], body_xf(hip, sc, lean, P['hem']['pivot']), lean + hem, sc)
    place(layer, P['torso']['img'], P['torso']['origin'], P['torso']['pivot'], body_xf(hip, sc, lean, P['torso']['pivot']), lean, sc)
    tilt = (2.0 * math.sin(2 * math.pi * 2 * ph + 0.6) if walking else 0.0)
    place(layer, P['head']['img'], P['head']['origin'], P['head']['pivot'], body_xf(hip, sc, lean, P['head']['pivot']), lean + tilt, sc)
    canvas.alpha_composite(lift_shadow(layer, (2, 3), 3, 0.28))
    canvas.alpha_composite(layer)

# ---------------------------------------------------------------- key, hand, settle (#41)
K_CONTACT = 28                               # frame of first touch (1.167 s): the clink lands here
KEY_REST = (262.0, 426.0)                    # world point of the bow's bottom contact, at rest
KEY_PIV = (0.10 * KW, 0.985 * KH)            # contact point in key image coords
SETTLE_ANG = [-6.0, -4.3, -2.6, -1.2, 0.6, 0.9, 0.5, 0.15, -0.05, 0.0]
SETTLE_DY = [0, 0, 0, -1.5, -3.0, -1.4, -0.3, 0, 0, 0]  # the one bounce peaks on frame 4

def key_pose(k):
    if k < K_CONTACT:
        f = k / K_CONTACT
        drop = 340 * (1 - smooth(f) ** 0.8) * (1 - f) ** 0.4    # lowered, slowing into the bench
        return KEY_REST[0] - 30 * (1 - f), KEY_REST[1] - drop, -6.0
    f = k - K_CONTACT
    if f < len(SETTLE_ANG):
        return KEY_REST[0], KEY_REST[1] + SETTLE_DY[f], SETTLE_ANG[f]
    return KEY_REST[0], KEY_REST[1], 0.0

def draw_key_and_hand(canvas, k, dx):
    kx, ky, ka = key_pose(k)
    lay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    place(lay, KEY, (0, 0), KEY_PIV, (kx + dx, ky), ka, 1.0)
    # the hand: holds the shaft near the bit, releases 2 frames after contact, then lifts away
    grip_local = (0.70 * KW, 0.40 * KH)
    gx, gy = R(ka, (grip_local[0] - KEY_PIV[0], grip_local[1] - KEY_PIV[1]))
    grip = (kx + dx + gx, ky + gy)
    t = k / FPS
    lift = 380 * ease(t, (K_CONTACT + 3) / FPS, (K_CONTACT + 3) / FPS + 0.85)
    hs = 0.62
    HA = -62.0
    tip = (650.0, 1585.0)
    v = R(HA, (tip[0] - P['hand']['pivot'][0], tip[1] - P['hand']['pivot'][1]))
    wrist = (grip[0] - v[0] * hs, grip[1] - v[1] * hs - lift)
    hl = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    cuff = (1100.0, 1468.0)
    place(hl, P['sleeve']['img'], P['sleeve']['origin'], cuff, (wrist[0] + 6, wrist[1] + 8), 24, hs * 1.05)
    place(hl, P['hand']['img'], P['hand']['origin'], P['hand']['pivot'], wrist, HA, hs)
    if lift < 379:
        lay.alpha_composite(hl)
    canvas.alpha_composite(lift_shadow(lay, (3, 4), 4, 0.32))
    canvas.alpha_composite(lay)

# ---------------------------------------------------------------- type
def title(img):
    d = ImageDraw.Draw(img)
    r = np.random.RandomState(3)
    x = 30
    spec = [('N', 0, 1.25), ('a', 2, 1.0), ('r', 5, 0.85), ('r', 3, 1.1), ('é', 0, 1.0), (' ', 0, 1),
            ('p', 6, 0.7), ('a', 6, 0.7), ('r', 6, 0.7), (' ', 0, 1), ('l', 6, 0.75), ('a', 6, 0.75), (' ', 0, 1),
            ('c', 1, 1.15), ('l', 0, 1.25), ('é', 3, 0.95)]
    base = 64
    for i, (ch, face, sz) in enumerate(spec):
        if ch == ' ':
            x += 12; continue
        f = fnt(FACES[face], int(46 * sz))
        col = RED if (i < 5 or i in (14,)) else BLACK
        if i >= 13: col = BLACK if i != 14 else RED
        dy = r.uniform(-8, 8) if i not in (6, 7, 8, 10, 11) else 2
        d.text((x, base + dy), ch, font=f, fill=col, anchor='ls')
        x += d.textlength(ch, font=f) + 1

LINES = [("On m'a posée sur le banc.", BLACK), ("Sa main était tiède,", BLACK),
         ("puis il n'y eut que son manteau.", BLACK), ("La porte de service n'a pas bougé.", RED)]
CPS, PAUSE, TSTART = 18.0, 0.1, 0.1
WORD_TIMES = []  # (line, word_index, t_appear)
def _schedule():
    t = TSTART
    for li, (s, _) in enumerate(LINES):
        words = s.split(' ')
        for wi, w in enumerate(words):
            WORD_TIMES.append((li, wi, t))
            t += (len(w) + 1) / CPS
        t += PAUSE
_schedule()
CAP_F = fnt(SERIF_I, 23)
def captions(img, t):
    d = ImageDraw.Draw(img)
    d.text((500, 26), '— la clé, 18:06', font=fnt(HUMAN, 15), fill=(110, 84, 40))
    for li, (s, col) in enumerate(LINES):
        words = s.split(' ')
        shown = [w for (l, wi, ta) in WORD_TIMES if l == li and ta <= t for w in [words[wi]]]
        if shown:
            d.text((498, 50 + li * 30), ' '.join(shown), font=CAP_F, fill=col, anchor='la')

# strip cells: tiny frames of this film's own material
def make_cells():
    cells = []
    def cell(fill=PAGE_HI):
        return Image.new('RGBA', (44, 44), fill + (255,))
    c = cell(); m = P['head']['img'].copy(); m.thumbnail((40, 40)); c.alpha_composite(m, (2, 2)); cells.append(c)  # 1 arrival
    c = cell(CREAM); m = P['head']['img'].rotate(12, expand=True); m.thumbnail((34, 34)); c.alpha_composite(m, (5, 6)); cells.append(c)  # 2 the bell: head up
    c = cell(); m = P['hand']['img'].copy(); m.thumbnail((40, 40)); c.alpha_composite(m, (2, 8)); cells.append(c)  # 3 tear (hand)
    c = cell(CREAM); m = KEY.copy(); m.thumbnail((42, 42)); c.alpha_composite(m, (1, 14)); cells.append(c)  # 4 the key found
    c = cell(); ImageDraw.Draw(c).rectangle([0, 30, 44, 44], fill=GREEN); m = KEY.copy(); m.thumbnail((40, 40)); c.alpha_composite(m, (2, 18)); cells.append(c)  # 5 on the bench
    c = cell(GREEN); ImageDraw.Draw(c).rectangle([12, 6, 32, 44], fill=(52, 70, 30), outline=CREAM); cells.append(c)  # 6 door shut
    return cells
CELLS = make_cells()

def band_img():
    m = blurnoise(108, W, 6, 9) * 0.5 + blurnoise(108, W, 1.2, 10) * 0.5
    a = np.array(BAND, np.float32)[None, None, :] + (m[..., None] * 5.0)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))
BAND_IMG = band_img()

def furniture(img):
    img.paste(BAND_IMG, (0, 432))
    d = ImageDraw.Draw(img)
    d.text((30, 486), 'Narré par la clé', font=fnt(HUMAN, 40), fill=(255, 255, 255), anchor='lm')
    d.text((930, 512), 'EXERCICE 5 · OBJET NARRATEUR · 18:06', font=fnt(HUMAN_B, 14), fill=(255, 255, 255), anchor='rm')
    # strip of six cells sitting directly on the band
    x0 = 650
    strip = Image.new('RGBA', img.size, (0, 0, 0, 0))
    for i, c in enumerate(CELLS):
        strip.alpha_composite(c, (x0 + i * 47, 388))
    img.alpha_composite(lift_shadow(strip, (1, 2), 2, 0.25)); img.alpha_composite(strip)
    d.rectangle([x0 + 4 * 47 - 2, 386, x0 + 4 * 47 + 45, 433], outline=RED, width=2)

# ---------------------------------------------------------------- frame
def cam(t):
    """Lateral drift of the camera: the page planes slide by depth (multiplane #44)."""
    return 46 * ease(t, 1.6, 6.5)

def render_frame(t, k):
    c = cam(t)
    img = Image.new('RGBA', (W, H))
    img.paste(PAGE_IMG.crop((int(100 - 0.0 * c), 0, int(100 - 0.0 * c) + W, H)), (0, 0))
    img.alpha_composite(GHOST_IMG, (int(-0 + 0.25 * c) - 0, 0)) if False else img.alpha_composite(GHOST_IMG.crop((0, 0, W, H)).transform((W, H), Image.AFFINE, (1, 0, -0.25 * c, 0, 1, 0)))
    title(img)
    captions(img, t)
    img.alpha_composite(DOOR.crop((0, 0, W, H)).transform((W, H), Image.AFFINE, (1, 0, -0.55 * c, 0, 1, 0)))
    draw_visitor(img, k, 0.55 * c)
    img.alpha_composite(BENCH.transform((W, H), Image.AFFINE, (1, 0, -BX - 1.0 * c, 0, 1, 0)))
    draw_key_and_hand(img, k, 1.0 * c)
    furniture(img)
    return img.convert('RGB')

# ---------------------------------------------------------------- sound
def readwav(p):
    w = wave.open(str(p)); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    return x, w.getframerate()

STEP_ONSETS = [8.59, 9.76, 10.38, 13.8, 15.29, 15.98, 4.47, 0.67, 1.13]  # onsets measured by spectral flux

def sound(mix):
    room, r = readwav(M / 'room.wav')
    seg = room[int(5.0 * r): int(5.0 * r) + int(DUR * r) + 10]
    seg = seg / (np.sqrt(np.mean(seg ** 2)) + 1e-9) * 0.012
    n = min(len(seg), mix.n)
    mix.L[:n] += seg[:n]; mix.R[:n] += seg[:n] * 0.95
    th, _ = readwav(M / 'thud.wav')
    th = th / np.abs(th).max()
    tland = K_CONTACT / FPS
    mix.add(th[int(0.030 * r): int(0.33 * r)], tland, 0.55, -0.3)          # the key's weight on wood (PD recording)
    mix.click(tland, 0.22, -0.3, bright=7500, seconds=0.025)  # brass tick (kit synth, declared)
    mix.click(tland + 6 / FPS, 0.06, -0.3, bright=7000, seconds=0.015)  # the bounce returns
    st, _ = readwav(M / 'steps.wav')
    for i, tc in enumerate(CONTACTS):
        o = STEP_ONSETS[i % len(STEP_ONSETS)]
        g = st[int((o + 0.004) * r): int((o + 0.24) * r)].copy()
        g[:int(0.003 * r)] *= np.linspace(0, 1, int(0.003 * r))
        g = g / (np.abs(g).max() + 1e-9)
        dist = i / max(1, len(CONTACTS) - 1)
        cutoff = 5200 * (1 - 0.65 * dist)
        g = mix.lowpass(g, cutoff) if hasattr(mix, 'lowpass') else g
        mix.add(g, tc, 0.42 * (1 - 0.6 * dist), -0.1 - 0.5 * dist)

film = Film('test-shot', DUR, boil=0)
@film.picture
def _pic(t, ink):
    k = ink.i
    ink.img = render_frame(t, k)
    ink._grain = False                      # no synthetic grain: texture comes from the real material
film.sound(sound)
film.poster_at = 3.0

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        for tt in [float(x) for x in sys.argv[2:]]:
            render_frame(tt, int(tt * FPS)).save(f'/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/st_{tt:.2f}.png')
        print('contacts', [round(c, 3) for c in CONTACTS])
    else:
        film.render(out_dir=OUTDIR)
