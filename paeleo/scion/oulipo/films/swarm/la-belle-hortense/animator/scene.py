"""La Belle Hortense -- animator unit: reusable scene module (SCION 2 Reiniger rig, SCION 44 multiplane,
SCION 29 cutouts from cut.py), Pathe-style stencil dye, real pan exposure.

    python3 -I cut.py                 # cutouts (once)
    python3 -I scene.py testshot      # V.3 test shot 41.5-44.0 s: testshot.mp4, testshot_43.3.png, board
    python3 -I scene.py beats         # every other animated beat as a prepared clip + a mid still
    python3 -I scene.py json          # scenes.json (invariants measured)

Everything a frame contains is (a) a foraged photograph, printed monochrome and stencil-dyed through masks
keyed from that photograph, (b) a cutout of one, articulated on pinned joints, or (c) a named handmade object
(envelope, receipt, type).  Motion blur exists only as the mean of N sub-frames of the moving stage
(shutter integration); no blur kernel is ever applied to a picture.
"""
import sys, os, json, math, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
SRC = os.path.join(ROOT, 'films/sources')
TS = os.path.join(SRC, 'la-belle-hortense/test-shot')
AN = os.path.join(SRC, 'la-belle-hortense/animator')
CUT = os.path.join(AN, 'cut')
ED = os.path.join(SRC, 'la-belle-hortense/animator-scene-authors-reiniger-rig-multiplane-stencil-dye-pan-exposure-scions-2-and-44-')
SW = os.path.join(ROOT, 'films/swarm/la-belle-hortense')
HERE = os.path.dirname(os.path.abspath(__file__))
for d in (ED, os.path.join(ED, 'clips'), os.path.join(ED, 'stills'), os.path.join(AN, 'dye'), os.path.join(AN, 'checks')):
    os.makedirs(d, exist_ok=True)
W, H, FPS = 960, 540, 24
CB = '/usr/share/fonts/X11/Type1/c0583bt_.pfb'; CR = '/usr/share/fonts/X11/Type1/c0419bt_.pfb'
_fc = {}
def font(sz, bold=True):
    k = (sz, bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(CB if bold else CR, sz)
    return _fc[k]

def hx(s): return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.
RED = hx('#e2011b'); TRED = hx('#a50917'); INK = hx('#010201'); BRASS = hx('#c9a23a'); CREAM = hx('#e1e5b2')
YG3 = hx('#b2ae44'); YG2 = hx('#80b13b'); YG1 = hx('#6ba334'); MG2 = hx('#46a63d'); MG1 = hx('#2f9036')
DG1 = hx('#0a7732'); DG2 = hx('#1b4c22'); OCHRE = hx('#837030'); REARTH = hx('#8d3b24'); BRONZE = hx('#8a6a34')
PAPER = hx('#ece6c8')

def over(dst, rgb, a):
    a = np.asarray(a, np.float32)
    a = a[..., None] if a.ndim == 2 else a
    return dst * (1 - a) + rgb * a
def sm(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def A3(M): return np.vstack([M, [0, 0, 1]])
def R(p, ang, s=1.0): return A3(cv2.getRotationMatrix2D((float(p[0]), float(p[1])), float(ang), float(s)))
def T(dx, dy): return np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1]], np.float64)
def SY(p, sy): return np.array([[1, 0, 0], [0, sy, p[1] * (1 - sy)], [0, 0, 1]], np.float64)
def SX(p, sx): return np.array([[sx, 0, p[0] * (1 - sx)], [0, 1, 0], [0, 0, 1]], np.float64)
def tp(M, p): v = M @ np.array([p[0], p[1], 1.0]); return v[:2]
def paint(fr, rgba, M):
    w = cv2.warpAffine(rgba, M[:2], (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    return over(fr, w[..., :3], w[..., 3])
def lin_lut(g, lo, hi, gamma=1.0): return np.clip((g - lo) / (hi - lo), 0, 1) ** gamma

# ====================================================================== STENCIL DYE (Pathecolor practice)
def dye_plate(bgr, horizon, name, sky='cream', wall_box=None):
    """Monochrome print of a colour photograph + dye masks keyed from its own hues. Returns RGB float.
    Print: one hard curve per plate (p1 -> black, p99.6 -> paper white) so true blacks and cream highlights exist.
    Dyes (multiplied over the print density): grass greens by original hue, soil ochre/red-earth,
    brick quoins red, plaster yellow-ochre, trees deep green, sky left as cream paper."""
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hue, sat = hsv[..., 0], hsv[..., 1]
    lo, hi = np.percentile(g, 1.0), np.percentile(g, 99.6)
    p = lin_lut(g, lo, hi, 1.15)
    rows = np.arange(g.shape[0])[:, None] * np.ones((1, g.shape[1]))
    ground = (rows > horizon).astype(np.float32)
    gv = g[horizon:]
    pg = lin_lut(g, np.percentile(gv, 0.5), np.percentile(gv, 99.7), 0.95)    # the ground printed on its own curve
    def soft(m, k=5): return cv2.GaussianBlur(m.astype(np.float32), (k, k), 0)   # the cut edge of a stencil, not the image
    grass = soft((hue > 22) & (hue < 92) & (sat > 28)) * ground
    soil = soft(((sat <= 28) | (hue <= 22)) & (g < 0.80)) * ground * (1 - grass)
    brick = soft(((hue < 9) | (hue > 165)) & (sat > 60), 3) * (1 - ground)
    skym = soft((sat < 45) & (g > 0.62) & (rows < horizon), 9) * (1 - brick)
    wb = np.zeros_like(g)
    if wall_box: wb[wall_box[1]:wall_box[3], wall_box[0]:wall_box[2]] = 1
    trees = soft((g < 0.30) & (rows < horizon), 7) * (1 - brick) * (1 - skym) * (1 - wb)
    wall = (1 - ground) * (1 - brick) * (1 - skym) * (1 - trees)
    # grass dye: yellow blades -> yellow-green / straw, blue-green blades -> mid/deep green; density from the print
    yel = np.clip((40 - hue) / 12, 0, 1)[..., None]
    gcol = (YG3 * 0.5 + YG2 * 0.5) * yel + (MG2 * 0.55 + MG1 * 0.45) * (1 - yel)
    dg = gcol * (0.02 + 1.55 * pg[..., None])
    dg = over(dg, DG2 * 0.5, np.clip(0.22 - pg, 0, 0.22) * 3.5)                 # deep green-black in shadow
    dg = over(dg, CREAM, np.clip((pg - 0.84) / 0.16, 0, 1) * 0.8)               # hot cream highlights
    ecol = OCHRE * 1.5 * (pg[..., None] > 0.38) + REARTH * 1.45 * (pg[..., None] <= 0.38)
    de = ecol * (0.06 + 1.2 * pg[..., None])
    de = over(de, CREAM, np.clip((pg - 0.82) / 0.18, 0, 1) * 0.85)
    dw = YG3 * (0.05 + 1.05 * p[..., None])
    dt = DG2 * (0.10 + 1.6 * p[..., None])
    dr = RED * (0.15 + 0.95 * p[..., None])
    ds = CREAM * (0.55 + 0.45 * p[..., None]) if sky == 'cream' else dw
    base = PAPER * p[..., None]                                                # undyed print on cream stock
    col = base
    for dye, m in ((dw, wall), (dt, trees), (ds, skym), (dr, brick), (de, soil), (dg, grass)):
        col = over(col, dye, np.clip(m, 0, 1))
    col = np.clip(col, 0, 1).astype(np.float32)
    for k, m in (('grass', grass), ('soil', soil), ('brick', brick), ('wall', wall), ('trees', trees), ('sky', skym)):
        cv2.imwrite(os.path.join(AN, 'dye', f'{name}_{k}.png'), (np.clip(m, 0, 1) * 255).astype(np.uint8))
    return col

_plates = {}
def plate(key):
    if key in _plates: return _plates[key]
    if key == 'meadow':            # Bourre 50866798791: shed across the meadow
        b = cv2.imread(os.path.join(TS, 'plates/Bourr_Loir-et-Cher_50866798791_.jpg')); hz = 470; wbx = (50, 100, 780, 470)
    elif key == 'shed':            # Bourre 50866795131: goods shed and door
        b = cv2.imread(os.path.join(TS, 'plates/Bourr_Loir-et-Cher_50866795131_.jpg')); hz = 600; wbx = (280, 100, 1180, 640)
    _plates[key] = dye_plate(b, hz, key, wall_box=wbx)
    return _plates[key]

# ====================================================================== MULTIPLANE (SCION 44)
def strip(bands, h, length, seed, wmin=420, wmax=760, xf=72):
    """A long plane assembled from distinct crops of the plates (no mirror tiling): each crop is resized to
    height h and joined to the next with a 72 px cross-fade. bands: list of (img, y0, y1, x0, x1)."""
    rng = np.random.default_rng(seed)
    out = None
    while out is None or out.shape[1] < length:
        img, y0, y1, x0, x1 = bands[rng.integers(len(bands))]
        k = h / (y1 - y0)
        w = int(rng.integers(wmin, wmax))
        sw = min(int(w / k), x1 - x0 - 1)
        sx = int(rng.integers(x0, x1 - sw))
        c = cv2.resize(img[y0:y1, sx:sx + sw], (max(int(sw * k), xf + 2), h), interpolation=cv2.INTER_AREA)
        if out is None: out = c; continue
        r = np.linspace(0, 1, xf)[None, :, None]
        out = np.concatenate([out[:, :-xf], out[:, -xf:] * (1 - r) + c[:, :xf] * r, c[:, xf:]], 1)
    return np.ascontiguousarray(out[:, :length].astype(np.float32))

class Plane:
    def __init__(self, name, img, y0, ratio, feather=None):
        self.name, self.img, self.y0, self.ratio, self.feather = name, img, y0, ratio, feather
    def offset(self, cx): return self.ratio * cx
    def draw(self, fr, cx, x_origin=0.0):
        sw = self.img.shape[1]
        off = self.offset(cx) + x_origin
        i0 = int(math.floor(off)); fx = off - i0
        idx = np.clip(np.arange(i0, i0 + W + 1), 0, sw - 1)
        a = self.img[:, idx]
        a = a[:, :W] * (1 - fx) + a[:, 1:W + 1] * fx                   # sub-pixel translation (no blur kernel)
        y0 = self.y0; h = min(a.shape[0], H - y0)
        if self.feather:
            m = np.clip(np.arange(h) / self.feather, 0, 1)[:, None, None]
            fr[y0:y0 + h] = fr[y0:y0 + h] * (1 - m) + a[:h] * m
        else:
            fr[y0:y0 + h] = a[:h]

_runstage = None
def run_stage():
    """The V.3 stage: no sky anywhere (the camera is tilted down), colour edge to edge."""
    global _runstage
    if _runstage: return _runstage
    md, sh = plate('meadow'), plate('shed')
    L = 16000
    far = strip([(sh, 470, 640, 0, 700), (md, 330, 470, 60, 760), (md, 470, 600, 0, 1280)], 120, int(L * 0.35) + 2400, 1, 300, 560)
    mid = strip([(md, 440, 640, 0, 1280), (sh, 560, 760, 0, 1280)], 170, int(L * 0.6) + 2400, 2)
    gnd = strip([(md, 610, 960, 0, 1280), (sh, 700, 960, 0, 640), (md, 700, 960, 0, 1280)], 370, L + 2400, 3)
    near = strip([(md, 820, 960, 0, 1280), (sh, 840, 960, 0, 640)], 110, int(L * 1.6) + 2400, 4)
    _runstage = [Plane('far', far[30:], 0, 0.35), Plane('mid', mid, 58, 0.60, 44), Plane('ground', gnd, 170, 1.0, 50),
                 Plane('near', near, 432, 1.6, 26)]
    return _runstage

def integrate(sub, t, n=36, shutter=0.5):
    """frame centred at t = mean of n sub-frames spread over the open shutter (0.5 = 180 degrees)."""
    acc = np.zeros((H, W, 3), np.float32)
    for i in range(n):
        acc += sub(t + ((i + 0.5) / n - 0.5) * shutter / FPS)
    return acc / n

# ====================================================================== PIECES & RIGS (SCION 2 / FK 32)
PZ = np.load(os.path.join(CUT, 'pieces.npz'))
RIGJ = json.load(open(os.path.join(AN, 'rig_runner.json')))
JN = RIGJ['joints']

def coat_print(g, coat):
    """stencil red over a locally stretched print of the coat: the folds stay (p2..p98 of the coat itself)."""
    v = g[coat > 0.5]
    lo, hi = np.percentile(v, 2), np.percentile(v, 98.5)
    gc = lin_lut(g, lo, hi, 0.8)
    red = RED * (0.10 + 0.98 * gc[..., None])
    red = over(red, hx('#f2b49a'), np.clip((gc - 0.88) / 0.12, 0, 1) * 0.45)    # a few warm sheen highlights
    return red
def mono(g, k=1.0):
    return (lin_lut(g, 0.04, 0.80, 1.1) * k)[..., None] * PAPER

G = PZ['g']; COAT = PZ['coat']
_red = coat_print(G, COAT); _red_u = coat_print(PZ['g_under'], COAT)
def fig_rgb(gsrc, red):
    return over(mono(gsrc), red, np.clip(COAT * 1.0, 0, 1))
_zt = np.load(os.path.join(TS, 'cut/pieces.npz'))
FORE_COAT = np.zeros_like(G); FORE_COAT[:_zt['fore_coat'].shape[0]] = _zt['fore_coat']
RGB_TOP = fig_rgb(PZ['g_under'], _red_u)          # torso/skirt under the sleeve: re-made cloth
RGB_SL = fig_rgb(G, _red)
def rgba(rgb, a): return np.dstack([rgb, a]).astype(np.float32)
PIECES = {
    'torso': rgba(RGB_TOP, PZ['torso_a']), 'skirt': rgba(RGB_TOP, PZ['skirt_a']), 'sleeve': rgba(RGB_SL, PZ['sleeve_a']),
    'forearm': rgba(over(mono(G), _red, cv2.GaussianBlur((PZ['fore_a'] * (G < 0.30)).astype(np.float32), (5, 5), 0)), PZ['fore_a']),
    'thighN': rgba(mono(PZ['thN_g'], 0.8), PZ['thN_a']), 'thighF': rgba(mono(PZ['thF_g'], 0.45), PZ['thF_a']),
    'shinN': rgba(mono(G, 0.95), PZ['shinN']), 'shinF': rgba(mono(G, 0.5), PZ['shinF']),
}
SIL = {k: rgba(np.zeros_like(v[..., :3]), v[..., 3]) for k, v in PIECES.items()}

class Runner:
    """FK joint tree from rig_runner.json.  pose = dict(joint -> angle); root transform = (x, y, scale, lean)."""
    ORDER = ['thighF', 'shinF', 'sleeve', 'skirt', 'thighN', 'shinN', 'torso', 'forearm']
    def mats(self, x, y, s, lean, pose):
        root = JN['root']['pivot']
        M = {}
        Mr = T(x - root[0], y - root[1]) @ R(root, lean, 1.0)
        Mr = T(x, y) @ np.array([[s, 0, 0], [0, s, 0], [0, 0, 1]]) @ T(-root[0], -root[1]) @ R(root, lean)
        M['torso'] = Mr
        for j, piece in (('skirt', 'skirt'), ('sleeve', 'sleeve'), ('forearm', 'forearm'), ('hipN', 'thighN'), ('hipF', 'thighF')):
            lim = JN[j].get('limits_deg', [-360, 360])
            a = float(np.clip(pose.get(j, 0.0), *lim))
            M[piece] = Mr @ R(JN[j]['pivot'], a)
        for j, piece, par in (('kneeN', 'shinN', 'thighN'), ('kneeF', 'shinF', 'thighF')):
            lim = JN[j]['limits_deg']; a = float(np.clip(pose.get(j, 0.0), *lim))
            pv = JN[j]['pivot']; cp = JN[j].get('child_pivot', pv)
            M[piece] = M[par] @ T(pv[0] - cp[0], pv[1] - cp[1]) @ R(cp, a) @ SY(cp, JN[j]['stretch_y'])
        return M
    def draw(self, fr, M, sil=False, skip=()):
        P = SIL if sil else PIECES
        for k in self.ORDER:
            if k in skip: continue
            fr = paint(fr, P[k], M[k])
        return fr
    def pivot_errors(self, M):
        """distance between each child pivot as carried by the child and by its parent (px, screen)."""
        err = {}
        for j, piece, par in (('skirt', 'skirt', 'torso'), ('sleeve', 'sleeve', 'torso'), ('forearm', 'forearm', 'torso'),
                              ('hipN', 'thighN', 'torso'), ('hipF', 'thighF', 'torso'), ('kneeN', 'shinN', 'thighN'), ('kneeF', 'shinF', 'thighF')):
            pv = JN[j]['pivot']; cp = JN[j].get('child_pivot', pv)
            err[j] = float(np.linalg.norm(tp(M[piece], cp) - tp(M[par], pv)))
        return err
RUN = Runner()

def run_pose(t, hz=2.3):
    """running gait, phase from time; near leg phase 0, far leg phase pi."""
    ph = 2 * math.pi * hz * t
    def leg(p):
        hip = 6 + 34 * math.sin(p)                                  # + = knee forward (screen right)
        swing = 0.5 + 0.5 * math.cos(p - 0.5)                       # leg travelling forward -> foot tucked
        knee = -(6 + 69 * swing ** 1.6)
        return hip, knee
    hN, kN = leg(ph); hF, kF = leg(ph + math.pi)
    return dict(hipN=hN, kneeN=kN, hipF=hF, kneeF=kF, skirt=-4.5 * math.sin(ph),
                sleeve=-9 * math.sin(ph), forearm=-6 + 22 * math.sin(ph + math.pi)), ph
def walk_pose(t, hz=1.0):
    ph = 2 * math.pi * hz * t
    def leg(p):
        return 2 + 20 * math.sin(p), -(4 + 40 * max(0.0, math.cos(p - 0.8)) ** 2)
    hN, kN = leg(ph); hF, kF = leg(ph + math.pi)
    return dict(hipN=hN, kneeN=kN, hipF=hF, kneeF=kF, skirt=-2 * math.sin(ph), sleeve=-12 * math.sin(ph),
                forearm=-4 + 6 * math.sin(ph + math.pi)), ph

# ---- key (CC0 photo), dyed brass
kim = cv2.imread(os.path.join(TS, 'plates/skeletonkey.png'), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.
_kp = kim[60:640, 160:440]
_km = cv2.morphologyEx((_kp < 0.45).astype(np.float32), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
def key_piece(hh):
    kw = int(_kp.shape[1] * hh / _kp.shape[0])
    gr = cv2.resize(np.clip(1.0 - _kp, 0, 1) * 0.55 + 0.45 * (_kp > 0.7), (kw, hh), interpolation=cv2.INTER_AREA)
    al = cv2.resize(_km, (kw, hh), interpolation=cv2.INTER_AREA)
    rgb = over((0.25 + 0.8 * gr)[..., None] * BRASS * 1.1, CREAM, np.clip((gr - 0.8) * 3, 0, 0.6))
    return rgba(np.clip(rgb, 0, 1), al), (kw / 2, hh * 0.35)
KEY, KPIV = key_piece(64)
def draw_key(fr, x, y, ang, k=KEY, kp=KPIV, s=1.0, glint=0.0, sil=False):
    M = T(x - kp[0], y - kp[1]) @ R(kp, ang, s)
    piece = k.copy()
    if glint: piece[..., :3] = np.clip(piece[..., :3] + glint * (CREAM - piece[..., :3]) * 0.8, 0, 1)
    if sil: piece[..., :3] = 0
    return paint(fr, piece, M)

# ---- other cutouts (monochrome prints, bell dyed bronze)
def cut_rgba(gk, ak, k=1.0, dye=None, dye_amt=0.0):
    g = PZ[gk]; rgb = mono(g, k)
    if dye is not None: rgb = over(rgb, dye * (0.08 + 1.15 * lin_lut(g, 0.04, 0.8))[..., None], dye_amt)
    return rgba(rgb, PZ[ak])
BENCH = cut_rgba('bench_g', 'bench_a', 1.0)
BELL = cut_rgba('bell_g', 'bell_a', 1.0, BRONZE, 0.85); CLAP = cut_rgba('bell_g', 'clap_a', 0.9, BRONZE, 0.7)
VISF = cut_rgba('visF_g', 'visF_a', 1.0)
_r = np.arange(VISF.shape[0])[:, None]
VISF[..., 3] *= ~((_r > 196) & (PZ['visF_g'] > 0.52)) * (_r < 238)          # sidewalk caught under the shoes
VISB = cut_rgba('visB_g', 'visB_a', 1.0)

def walker_draw(fr, piece, x, y, s, t, hz=1.0, sil=False, bend=0.0):
    """front/back replacement profile walking: legs below the hem alternate (lift + foreshorten),
    upper body bobs and sways; bend (0..1) bows the upper body forward (front view: compress + drop)."""
    p = piece.copy()
    if sil: p[..., :3] = 0
    h, w = p.shape[:2]
    hem = int(h * 0.80); mid = w // 2 + (2 if piece is VISF else 0)
    ph = 2 * math.pi * hz * t
    bob = -2.5 * abs(math.cos(ph)) * s
    sway = 1.5 * math.sin(ph)
    up = p.copy(); up[hem:] *= np.clip((hem + 6 - np.arange(h - hem))[:, None, None] / 6.0, 0, 1)
    up[hem + 6:, :, 3] = 0
    legL = p.copy(); legL[:hem] = 0; legL[:, mid:] = 0
    legR = p.copy(); legR[:hem] = 0; legR[:, :mid] = 0
    base = T(x - w / 2 * s, y - h * s) @ np.diag([s, s, 1.0])
    for leg, sg in ((legL, 1), (legR, -1)):
        lift = max(0.0, sg * math.sin(ph))
        Ml = base @ T(0, -6 * lift) @ SY((0, hem), 1 - 0.12 * lift)
        fr = paint(fr, leg, Ml)
    waist = (w / 2, hem)
    Mu = base @ T(0, bob / max(s, 1e-3)) @ R(waist, sway) @ SY(waist, 1 - 0.32 * bend) @ T(0, 0)
    fr = paint(fr, up, Mu)
    return fr, tp(Mu, (w / 2, h * 0.45))

# ---- folded coat (3 hinged pieces of the same coat panel, folded flat) -- the clue on the bench
_rows = np.arange(900)[:, None]
_holes = ((PZ['body_a'] > 0.5) & (COAT < 0.5) & (_rows >= 150)).astype(np.uint8)          # hand, newspaper, shirt
_gp = cv2.inpaint((PZ['g_under'] * 255).astype(np.uint8), cv2.dilate(_holes, np.ones((5, 5), np.uint8)), 9, cv2.INPAINT_TELEA).astype(np.float32) / 255.
_cm = np.clip(PZ['body_a'] * (_rows >= 168) * (_rows < 640), 0, 1)
COAT_PANEL = rgba(coat_print(_gp, np.maximum(COAT, _holes)), _cm)     # the same coat panel, folded: cloth only
FOLD_LINES = (330, 485)
def coat_folded_draw(fr, x, y, s, fold, lift=0.0, sil=False, glint=0.0, key_on=None):
    """Z-fold about two hinge lines; fold in 0..1 (1 = flat folded on the seat).  A piece rotated by theta about
    a horizontal hinge is foreshortened by cos(theta) in y (its reverse side printed darker when cos<0).
    The bundle then lies on the seat: rotated -90 and squashed 0.5 for the seat's perspective.  lift raises it."""
    th = math.radians(172 * fold)
    c = math.cos(th)
    src = SIL['torso'] if sil else COAT_PANEL
    y1, y2 = FOLD_LINES
    A = src.copy(); A[y1:] = 0
    B = src.copy(); B[:y1] = 0; B[y2:] = 0
    C = src.copy(); C[:y2] = 0
    # B hinged at y1 folds back under A (cos), C hinged at B's far edge folds forward again (z-fold)
    MB = SY((0, y1), c)
    y2b = y1 + (y2 - y1) * c
    MC = T(0, y2b - y2)                     # z-fold: C turns back by -theta relative to B -> lies in A's orientation
    L = T(x, y - lift) @ np.diag([s, s, 1]) @ SY((0, 0), 1 - 0.5 * min(1.0, fold * 1.2)) @ R((0, 0), -90 * min(1.0, fold * 1.2)) @ T(-160, -240)
    darkB = B.copy(); darkC = C.copy()
    if c < 0 and not sil: darkB[..., :3] *= 0.62
    fr = paint(fr, darkB, L @ MB)
    fr = paint(fr, A, L)
    fr = paint(fr, darkC, L @ MC)
    if key_on is not None:     # the key's bow showing at the fold line
        kx, ky = tp(L @ MC, (150, y2 - 10))
        fr = draw_key(fr, kx, ky, key_on, s=0.30 * s / 0.35, glint=glint, sil=sil)
    return fr, L

# ---- handmade objects: receipt and envelope (typeset here; print-sound unit may supersede with its own print)
def make_ticket():
    tw, th = 150, 84
    im = Image.new('RGBA', (tw, th), (236, 230, 205, 255)); d = ImageDraw.Draw(im)
    d.rectangle((2, 2, tw - 3, th - 3), outline=(30, 28, 24, 255), width=2)
    d.text((10, 8), 'REÇU', font=font(22), fill=(12, 12, 10, 255))
    d.text((10, 36), 'une clé', font=font(14, False), fill=(12, 12, 10, 255))
    d.text((10, 54), 'remise au banc', font=font(14, False), fill=(12, 12, 10, 255))
    d.ellipse((92, 8, 140, 52), outline=(200, 16, 28, 255), width=3)
    d.text((106, 12), '6', font=font(30), fill=(200, 16, 28, 255))
    return np.asarray(im, np.float32) / 255.
TICKET = make_ticket()
def make_envelope():
    ew, eh = 360, 220
    body = Image.new('RGBA', (ew, eh), (232, 224, 196, 255)); d = ImageDraw.Draw(body)
    d.rectangle((1, 1, ew - 2, eh - 2), outline=(60, 54, 44, 255), width=2)
    d.line((0, eh, ew // 2, eh // 2 + 20), fill=(150, 140, 118, 255), width=2)
    d.line((ew, eh, ew // 2, eh // 2 + 20), fill=(150, 140, 118, 255), width=2)
    d.text((150, 140), 'Bourré, quai', font=font(20, False), fill=(20, 20, 18, 255))
    flap = Image.new('RGBA', (ew, eh // 2 + 30), (0, 0, 0, 0)); d2 = ImageDraw.Draw(flap)
    d2.polygon([(0, 0), (ew, 0), (ew // 2, eh // 2 + 26)], fill=(226, 216, 186, 255), outline=(60, 54, 44, 255))
    return np.asarray(body, np.float32) / 255., np.asarray(flap, np.float32) / 255.
ENV, FLAP = make_envelope()
def ticket_draw(fr, x, y, ang, flip, sil=False):
    tk = TICKET.copy()
    if sil: tk[..., :3] = 0
    M = T(x - 75, y - 42) @ R((75, 42), ang) @ SY((75, 42), max(0.08, abs(flip)))
    shade = 1.0 if flip > 0 else 0.78
    w = cv2.warpAffine(tk, M[:2], (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    return over(fr, w[..., :3] * shade, w[..., 3])

# ---- bell: damped pendulum, clapper as child pendulum
BELL_PIV = (184, 6)       # headstock pin (piece coords of the bell crop)
CLAP_PIV = (176, 300)
def bell_angles(t_since, theta0=26.0, tau=1.5, f=1.05):
    """theta(t) = theta0 e^(-t/tau) sin(2 pi f t); clapper lags by 0.9 rad with a shorter tau (strikes the lip)."""
    if t_since < 0: return 0.0, 0.0
    w = 2 * math.pi * f
    th = theta0 * math.exp(-t_since / tau) * math.sin(w * t_since)
    cl = 1.35 * theta0 * math.exp(-t_since / (tau * 0.8)) * math.sin(w * t_since - 0.9)
    return float(np.clip(th, -38, 38)), float(np.clip(cl, -38, 38))
def bell_draw(fr, x, y, s, th, cl, sil=False):
    Mb = T(x - BELL_PIV[0], y - BELL_PIV[1]) @ R(BELL_PIV, th, 1.0)
    Mb = T(x, y) @ np.diag([s, s, 1]) @ T(-BELL_PIV[0], -BELL_PIV[1]) @ R(BELL_PIV, th)
    Mc = Mb @ R(CLAP_PIV, cl - th)
    c = CLAP.copy(); b = BELL.copy()
    if sil: c[..., :3] = 0; b[..., :3] = 0
    fr = paint(fr, c, Mc)
    fr = paint(fr, b, Mb)
    return fr, Mb, Mc

# ====================================================================== TEST SHOT V.3 (film 41.5 - 44.0)
VR = 4200.0                     # runner (= camera) speed, px/s at the figure plane -> 62 px ground streak per 1/48 s
SCALE = 0.68; X_LOCK = 470.0; HIP_Y = 268.0; LEAN = -10.0
T_DROP = 43.2
FOLD_PT = (226.0, 520.0)        # piece coords: the fold at the front of the hem
G_ACC = 2600.0; VY0 = -160.0; GROUND_Y = 418.0; DRAG = 900.0
def runner_x(t): return X_LOCK + 10 * math.sin(2 * math.pi * 4.6 * t)      # tracking is never perfect
def cam_x(t, t0=41.5): return VR * (t - t0)
def key_release():
    pose, _ = run_pose(T_DROP)
    M = RUN.mats(runner_x(T_DROP), HIP_Y + bob(T_DROP), SCALE, LEAN, pose)
    return tp(M['torso'], FOLD_PT)
def bob(t): return -9 * abs(math.cos(2 * math.pi * 2.3 * t))
KX0, KY0 = None, None
T_LAND = None
def key_screen(t):
    """screen position while falling: x lags (air drag relative to the runner), y a gravity parabola"""
    global KX0, KY0, T_LAND
    if KX0 is None:
        KX0, KY0 = key_release()
        T_LAND = T_DROP + (-VY0 + math.sqrt(VY0 ** 2 + 2 * G_ACC * (GROUND_Y - KY0))) / G_ACC
    if t < T_DROP: return None
    if t < T_LAND:
        dt = t - T_DROP
        return KX0 - 0.5 * DRAG * dt * dt, KY0 + VY0 * dt + 0.5 * G_ACC * dt * dt, 20 + 690 * dt, 'fall'
    # on the ground it belongs to the ground plane: moves with ratio 1.0 against the camera
    dl = T_LAND - T_DROP
    xl = KX0 - 0.5 * DRAG * dl * dl - VR * (t - T_LAND)
    return xl, GROUND_Y, 20 + 690 * dl, 'ground'

def v3_sub(t, sil=False, stage=True):
    fr = np.zeros((H, W, 3), np.float32) + (1.0 if sil else 0)
    cx = cam_x(t)
    planes = run_stage()
    if stage and not sil:
        for p in planes[:3]: p.draw(fr, cx)
    pose, ph = run_pose(t)
    M = RUN.mats(runner_x(t), HIP_Y + bob(t), SCALE, LEAN, pose)
    ks = key_screen(t)
    fr = RUN.draw(fr, M, sil, skip=('shinN', 'torso', 'forearm'))
    if ks and ks[3] == 'ground': fr = draw_key(fr, ks[0], ks[1], ks[2], sil=sil)
    if ks and ks[3] == 'fall': fr = draw_key(fr, ks[0], ks[1], ks[2], sil=sil)       # behind the near shin
    fr = paint(fr, (SIL if sil else PIECES)['shinN'], M['shinN'])
    fr = paint(fr, (SIL if sil else PIECES)['torso'], M['torso'])
    if t < T_DROP:                                                # bow of the key showing at the fold
        fx, fy = tp(M['torso'], FOLD_PT)
        fr = draw_key(fr, fx, fy, 20 + 5 * math.sin(ph), s=0.9, sil=sil)
    fr = paint(fr, (SIL if sil else PIECES)['forearm'], M['forearm'])
    if stage and not sil: planes[3].draw(fr, cx)
    return fr

def typeset_v(img, t, slot='MANTEAU'):
    """HANDMADE type for the test shot: V. / caption / gloss on a black band / slot line."""
    order = ['banc', 'reçu', 'manteau', 'clé', 'porte', 'cloche']
    k = 2 if t < 43.5 else 3
    if t < 42.0: k = 1
    caps = {1: ('', ''), 2: ('le manteau revient', 'the coat comes back'), 3: ('La clé était dans le pli.', 'The key was in the fold.')}
    d = ImageDraw.Draw(img)
    x, y = 40, 360
    d.text((x, y), 'V.', font=font(46), fill=(1, 2, 1))
    fr_, en = caps[k]
    if fr_:
        s0 = {2: 42.0, 3: 43.5}[k]
        n = int(len(fr_) * min(1, (t - s0) / 0.35)) + 1
        d.text((x, y + 52), fr_[:n], font=font(36), fill=(165, 9, 23))
        if t - s0 > 0.3:
            tw = d.textlength(en, font=font(20))
            d.rectangle((x - 4, y + 96, x + tw + 10, y + 124), fill=(1, 2, 1))
            d.text((x + 3, y + 99), en, font=font(20), fill=(225, 229, 178))
    xx, yy = x + 2, y + 134
    for j, wd in enumerate(order):
        on = j == k
        s = wd.upper() if on else wd
        d.text((xx, yy), s, font=font(19, True), fill=(226, 1, 27) if on else (1, 2, 1))
        xx += d.textlength(s, font=font(19, True))
        if j < 5:
            d.text((xx, yy), ' · ', font=font(19, True), fill=(1, 2, 1)); xx += d.textlength(' · ', font=font(19, True))
    return img

def to_img(a): return Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8))

class Writer:
    def __init__(self, path, fps=FPS):
        self.p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                   '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium',
                                   '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    def add(self, img): self.p.stdin.write(np.asarray(img.convert('RGB')).tobytes())
    def close(self): self.p.stdin.close(); self.p.wait()

# ---------------------------------------------------------------- measurement (plan 10.4 / 10.5)
def measure(rgb8):
    a = rgb8.astype(np.float32)
    hsv = cv2.cvtColor(rgb8, cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    hue = hsv[..., 0] * 360 / 256; sat = hsv[..., 1] / 255.; val = hsv[..., 2] / 255.
    luma = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    hh = luma.shape[0]
    red = ((hue < 20) | (hue > 340)) & (sat > 0.55) & (val > 0.25)
    green = (hue > 55) & (hue < 160) & (sat > 0.30)
    rh = hue[red]; rh = np.where(rh > 180, rh - 360, rh)
    lo = luma[hh // 2:]
    gy = np.abs(np.diff(lo, axis=0))[:, :-1]; gxx = np.abs(np.diff(lo, axis=1))[:-1]
    rows = np.where(red.sum(1) > 6)[0]
    return dict(luma=[int(v) for v in np.percentile(luma, [5, 25, 50, 75, 95])], med_sat=int(np.median(hsv[..., 1])),
                coat_hue_deg=round(float(np.median(rh)), 1) if rh.size else None,
                coat_sat=round(float(np.median(sat[red])), 2) if rh.size else None,
                green_pct=round(100 * float(green.mean()), 1), lower_gy_gx=round(float(gy.mean() / max(gxx.mean(), 1e-6)), 2),
                red_rows_frac=round(float((rows.max() - rows.min() + 1) / hh), 2) if rows.size else 0,
                red_top_row=int(rows.min()) if rows.size else None)

def readwav(p):
    w = wave.open(p); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.
    return x if w.getnchannels() == 1 else x.reshape(-1, w.getnchannels()).mean(1)

def testshot():
    t0, t1 = 41.5, 44.0
    nfr = int(round((t1 - t0) * FPS))
    log = dict(frames=[], pivot_max_px=0.0, parallax=[], key=[])
    path_silent = os.path.join(AN, 'testshot_silent.mp4')
    wr = Writer(path_silent); wc = Writer(os.path.join(ED, 'clips', 'V3_manteau_clean.mp4'))
    planes = run_stage()
    prev = None
    for k in range(nfr):
        t = t0 + (k + 0.5) / FPS
        a = integrate(v3_sub, t, 36, 0.5)
        clean = to_img(a)
        wc.add(clean)
        img = typeset_v(clean.copy(), t)
        wr.add(img)
        pose, _ = run_pose(t)
        M = RUN.mats(runner_x(t), HIP_Y + bob(t), SCALE, LEAN, pose)
        e = RUN.pivot_errors(M); log['pivot_max_px'] = max(log['pivot_max_px'], max(e.values()))
        offs = [p.offset(cam_x(t)) for p in planes]
        if prev is not None:
            d = [abs(o - q) for o, q in zip(offs, prev)]
            log['parallax'].append(d)
        prev = offs
        ks = key_screen(t)
        if ks and ks[3] == 'fall': log['key'].append([round(t, 4), round(ks[0], 2), round(ks[1], 2), round(ks[2], 1)])
        log['frames'].append(dict(t=round(t, 4), pose={j: round(v, 2) for j, v in pose.items()}))
        if abs(t - 43.3) < 0.5 / FPS + 1e-6 or k == int(round((43.3 - t0) * FPS)):
            pass
    wr.close(); wc.close()
    # the still at exactly 43.3
    a = integrate(v3_sub, 43.3, 36, 0.5)
    still = typeset_v(to_img(a), 43.3)
    still.save(os.path.join(SW, 'testshot_43.3.png')); to_img(a).save(os.path.join(ED, 'stills', 'V3_43.3_clean.png'))
    sil = integrate(lambda tt: v3_sub(tt, sil=True), 43.3, 36, 0.5)
    to_img(sil).convert('L').save(os.path.join(AN, 'checks', 'sil_V3_43.3.png'))
    # sound
    sys.path.insert(0, os.path.join(ROOT, 'films')); import kit
    R_ = kit.RATE
    mix = kit.Mix(t1 - t0)
    steps = readwav(os.path.join(TS, 'sound/Concrete_Steps_2.wav'))
    grains = [steps[int(0.0 * R_):int(0.30 * R_)], steps[int(0.33 * R_):int(0.79 * R_)]]
    mix.wind(0.0, t1 - t0, gain=0.05)
    tt = 0.05; j = 0
    while tt < t1 - t0:
        gr = grains[j % 2]; rate = 1.0 + 0.03 * ((j * 7919) % 5 - 2) / 2
        idx = np.arange(0, len(gr) - 1, rate)
        mix.add(np.interp(idx, np.arange(len(gr)), gr) * 3.0, tt, 0.8, -0.1)
        tt += 1 / 4.6; j += 1
    mix.whoosh(0.0, 1.0, gain=0.08, pan=0.3); mix.whoosh(1.2, 1.2, gain=0.10, pan=-0.3)
    mix.click(0.5, gain=0.35, bright=5000); mix.click(2.0, gain=0.35, bright=5000)
    key_screen(43.0)
    for at, gn in ((T_DROP - t0, 0.05), (T_LAND - t0, 0.2)):
        n = int(0.25 * R_); q = np.arange(n) / R_
        sig = sum(am * np.sin(2 * np.pi * f * q) * np.exp(-q * dd) for f, am, dd in ((3150, 1.0, 38), (4720, 0.6, 52), (6890, 0.35, 70), (2210, 0.3, 30)))
        mix.add(sig, at, gn, 0.2)
    wav = os.path.join(AN, 'testshot.wav')
    st = mix.master() if hasattr(mix, 'master') else None
    data = st if st is not None else mix.buf
    data = np.asarray(data)
    if data.ndim == 1: data = np.stack([data, data], 1)
    if data.shape[0] == 2 and data.shape[1] != 2: data = data.T
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    w = wave.open(wav, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(R_); w.writeframes(pcm.tobytes()); w.close()
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path_silent, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                    '-shortest', os.path.join(SW, 'testshot.mp4')], check=True)
    # board: still beside the reference, measured
    ref = Image.open(os.path.join(ROOT, 'assets/references/hortense.webp')).convert('RGB')
    mref = measure(np.asarray(ref)); mst = measure(np.asarray(still.convert('RGB')))
    k = 540 / ref.size[1]; refr = ref.resize((int(ref.size[0] * k), 540))
    board = Image.new('RGB', (refr.size[0] + 960 + 30, 540 + 150), (18, 18, 18))
    board.paste(refr, (10, 10)); board.paste(still, (refr.size[0] + 20, 10))
    d = ImageDraw.Draw(board)
    def ln(x, y, s, c=(230, 230, 230)): d.text((x, y), s, font=font(15, False), fill=c)
    ln(10, 560, 'REFERENCE hortense.webp'); ln(refr.size[0] + 20, 560, 'FILM 43.3 s  V.3 MANTEAU (36 sub-frames, 180 deg shutter)')
    for i, (lab, m) in enumerate((('ref', mref), ('film', mst))):
        x = 10 if i == 0 else refr.size[0] + 20
        ln(x, 585, f"luma p5/25/50/75/95 {m['luma']}  med sat {m['med_sat']}")
        ln(x, 605, f"coat hue {m['coat_hue_deg']} deg  sat {m['coat_sat']}  red height {m['red_rows_frac']}")
        ln(x, 625, f"green {m['green_pct']}%  lower-half gy/gx {m['lower_gy_gx']}")
    ln(refr.size[0] + 20, 650, 'targets: coat hue within 8 deg of #e2011b (-6.0 deg), sat>=0.75, green>=25%, gy/gx>=1.3, coat>=55% height, head at top edge', (240, 180, 120))
    board.save(os.path.join(SW, 'testshot-board.jpg'), quality=90)
    # coat height (rig geometry, independent of colour keying)
    pose, _ = run_pose(43.3)
    M = RUN.mats(runner_x(43.3), HIP_Y + bob(43.3), SCALE, LEAN, pose)
    collar = tp(M['torso'], (170, 140)); hem = tp(M['torso'], (170, 640)); cap = tp(M['torso'], (150, 15))
    # parabola fit of the falling key (frame centres)
    kk = np.array(log['key'])
    fit = None
    if len(kk) >= 3:
        c2 = np.polyfit(kk[:, 0] - T_DROP, kk[:, 2], 2); res = kk[:, 2] - np.polyval(c2, kk[:, 0] - T_DROP)
        fit = dict(y_coeffs=[round(float(v), 2) for v in c2], g_fit_px_s2=round(float(2 * c2[0]), 1), max_resid_px=round(float(np.abs(res).max()), 4),
                   rotation_deg_per_s=690.0, n=len(kk))
    par = np.array(log['parallax'])
    par_ok = bool(np.all((par[:, 3] > par[:, 2]) & (par[:, 2] > par[:, 1]) & (par[:, 1] > par[:, 0])))
    res = dict(window=[t0, t1], frames=nfr, n_sub=36, shutter_deg=180, still_measures=mst, reference_measures=mref,
               coat_height_frac=round(float((hem[1] - collar[1]) / H), 3), cap_top_y=round(float(cap[1]), 1),
               pivot_max_px=log['pivot_max_px'], parallax_order_near_gt_ground_gt_mid_gt_far_all_frames=par_ok,
               parallax_px_per_frame=dict(zip(['far', 'mid', 'ground', 'near'], [round(float(v), 1) for v in par.mean(0)])),
               streak_px_per_exposure=dict(zip(['far', 'mid', 'ground', 'near'], [round(VR * r / 48, 1) for r in (0.35, 0.6, 1.0, 1.6)])),
               key_drop=dict(t_release=T_DROP, t_land=round(T_LAND, 3), positions=log['key'], parabola=fit),
               shin_angles_per_frame=[[f['pose']['kneeN'], f['pose']['hipN']] for f in log['frames']])
    json.dump(res, open(os.path.join(AN, 'testshot_measures.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ('shin_angles_per_frame', 'key_drop')}, indent=1))
    print('key', fit, 'land', T_LAND)

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'testshot'
    if cmd == 'testshot': testshot()
    elif cmd == 'still':
        t = float(sys.argv[2])
        a = integrate(v3_sub, t, int(sys.argv[3]) if len(sys.argv) > 3 else 36, 0.5)
        typeset_v(to_img(a), t).save(os.path.join(AN, f'probe_{t:.2f}.png'))
    elif cmd == 'beats':
        import beats; beats.main()
