"""Editor repair round 1 (E2) for La Belle Hortense: re-made beats answering the critic's review.

Same scene module, same foraged cut pieces (FSA/OWI conductor LoC 2017844115, Highsmith bench, Bourre plates,
CC0 key), same integrator.  New here:
  * DRAPED COAT: the conductor's coat panel (collar, shoulders, sleeve seam, buttons) hung over the bench
    back as a coat, its skirt folded forward on the seat (hinge, foreshortened, reverse in shade), hem
    over the seat edge, contact shadow on the slats.  Replaces the stepped Z-fold block everywhere the coat
    lies on the bench (I.1-I.6, II.2, VI.6, and the I.4 replays IV.2 / VI.2).
  * II.2: the conductor's own forearm piece (sleeve + hand, cut from the same print) comes down, closes on
    the collar and lifts the coat; the folded skirt opens on its hinge as it rises; glint at the fold.
  * I.3: a foraged photographed envelope (see ENV_SRC) with the key half out of its mouth at the sample time.
  * III.1: the false lead drawn as the visitor's silhouette walking off with the key dangling from her hand.
  * IV.5 / V.1 / V.2: re-timed so the coat, the bench and the receipt card are in frame at the sample times.
  * V.4: a labelled half-speed replay of the key leaving the hem (measured from the rendered frames), then
    the key landed on one photograph of grass (no strip seam), large, with a contact shadow; a hand takes it.

    python3 -I films/swarm/la-belle-hortense/editor/repair_beats.py [name ...]
"""
import os, sys, math, json
import numpy as np, cv2
from PIL import Image

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
sys.path.insert(0, os.path.join(ROOT, 'films/swarm/la-belle-hortense/animator'))
import scene as S                      # noqa: E402
import beats as B                      # noqa: E402
from scene import W, H, FPS, T, R, SY, SX, tp, over, paint, sm, RUN, PIECES, SIL, KEY, KPIV, VISF, VISB   # noqa: E402

PRINT = os.path.join(ROOT, 'films/sources/la-belle-hortense/print-sound/print')
OUT = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/clips')
STILLS = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/stills')
MEAS = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/measures')
ENV_SRC = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/forage')
for d in (OUT, STILLS, MEAS):
    os.makedirs(d, exist_ok=True)

def rgba(rgb, a): return np.dstack([rgb, a]).astype(np.float32)

# ================================================================== the draped coat (same panel, same dye)
_rows = np.arange(900)[:, None]
_PZ = S.PZ
_holes = ((_PZ['body_a'] > 0.5) & (S.COAT < 0.5) & (_rows >= 150)).astype(np.uint8)          # hand, newspaper, shirt
_gp = cv2.inpaint((_PZ['g_under'] * 255).astype(np.uint8), cv2.dilate(_holes, np.ones((5, 5), np.uint8)), 9,
                  cv2.INPAINT_TELEA).astype(np.float32) / 255.
_red = S.coat_print(_gp, np.maximum(S.COAT, _holes))
_red = np.minimum(_red, S.RED * 1.0)                 # no sheen hot-spots on the laid coat (the hand area)
_collar = ((_PZ['g_under'] < 0.30) & (_rows >= 128) & (_rows < 175) & (_PZ['body_a'] > 0.5)).astype(np.float32)
_cmask = np.clip(np.maximum(S.COAT, _holes) * (_rows >= 150) + _collar, 0, 1)
COAT_RGB = over(S.mono(_gp) * 0.55, _red, np.clip(np.maximum(S.COAT, _holes) * (_rows >= 150), 0, 1))
_body = np.clip(_PZ['body_a'] * (_rows < 640), 0, 1) * np.clip(_cmask + _collar, 0, 1)
COATP = rgba(COAT_RGB, cv2.GaussianBlur(_body.astype(np.float32), (3, 3), 0))
FOLD_Y = 430.0                 # waist line: the skirt folds forward about it
HEM_Y = 600.0                  # hem flap hinge (over the seat's front edge)
C_TOP = 128.0                  # collar top row
C_CX = 160.0                   # coat centre column

def _band(p, y0, y1):
    q = p.copy(); q[:int(y0)] = 0; q[int(y1):] = 0; return q
COAT_UP = _band(COATP, 0, FOLD_Y)
COAT_SK = _band(COATP, FOLD_Y, HEM_Y)
COAT_HEM = _band(COATP, HEM_Y, 900)

def draped_coat(fr, x, y, s, open_=0.0, lift=0.0, dx=0.0, sil=False, glint=0.0, key_ang=None, shadow=True, tilt=-6.0):
    """coat hung over the bench back: collar top centre at screen (x, y - lift); s scale.
    open_ 0 = skirt folded forward flat on the seat (foreshortened 0.28), 1 = skirt hanging straight (lifted).
    Returns fr and the screen point on the folded skirt where a key lies."""
    def P(p):
        if sil:
            q = p.copy(); q[..., :3] = 0; return q
        return p
    yy = y - lift
    L = T(x + dx, yy) @ R((0, 0), tilt * (1 - open_)) @ np.diag([s, s, 1.0]) @ T(-C_CX, -C_TOP)
    # skirt on its waist hinge: foreshortened by cos, shifted forward (screen right-down) as it lies on the seat
    c = 0.28 + 0.72 * open_
    Msk = L @ T(14 * (1 - open_), 0) @ SY((0, FOLD_Y), c)
    hem_y = FOLD_Y + (HEM_Y - FOLD_Y) * c
    # hem flap: over the seat's front edge it turns down again (hangs), in shade
    ch = 0.55 + 0.45 * open_
    Mhem = L @ T(14 * (1 - open_), hem_y - HEM_Y) @ SY((0, HEM_Y), ch)
    if shadow and not sil and lift < 40:
        k = 1 - lift / 40
        m = np.zeros((H, W), np.float32)
        a, b = tp(Msk, (C_CX + 30, (FOLD_Y + HEM_Y) / 2)), tp(L, (C_CX + 10, 330))
        cv2.ellipse(m, (int(a[0] + 10 * s / 0.2), int(a[1] + 6)), (int(150 * s), int(30 * s)), -4, 0, 360, 1, -1)
        cv2.ellipse(m, (int(b[0] + 14), int(b[1])), (int(120 * s), int(170 * s)), 0, 0, 360, 0.7, -1)
        m = cv2.GaussianBlur(m, (0, 0), 4)
        fr = fr * (1 - 0.5 * k * m[..., None])
    sk = P(COAT_SK).copy(); hem = P(COAT_HEM).copy()
    if not sil:
        sk[..., :3] *= 0.80 + 0.20 * open_          # skirt lies in the backrest's shade
        hem[..., :3] *= 0.55 + 0.45 * open_         # flap turned under the seat edge
    fr = paint(fr, hem, Mhem)
    fr = paint(fr, sk, Msk)
    up = P(COAT_UP)
    if glint and not sil:
        up = up.copy(); g = np.zeros(up.shape[:2], np.float32)
        cv2.ellipse(g, (int(C_CX + 40), int(FOLD_Y - 8)), (26, 7), 0, 0, 360, glint, -1)
        up[..., :3] = over(up[..., :3], S.BRASS * 1.15, np.clip(cv2.GaussianBlur(g, (0, 0), 3) * up[..., 3], 0, 1))
    if open_ < 1.0 or True:
        sl = P(PIECES['sleeve'])
        fr = paint(fr, sl, L @ R(S.JN['sleeve']['pivot'], 18 * (1 - open_) + 4))   # the empty sleeve falls aside
    fr = paint(fr, up, L)
    kp = tp(Msk, (C_CX + 40, (FOLD_Y + hem_y) / 2))
    if key_ang is not None:
        fr = S.draw_key(fr, kp[0], kp[1], key_ang, s=0.42 * s / 0.2, glint=glint, sil=sil)
    return fr, kp, L

# placement on the bench (bench piece coords -> screen via beats.bench_M)
COAT_ON = (186.0, 64.0)          # collar top, bench piece coords: on the back rail
COAT_S = 0.225                   # coat scale relative to the bench at BENCH_S 0.85 (View z=1)
def coat_place(v):
    x, y = tp(B.bench_M(v), COAT_ON)
    return x, y, COAT_S * v.z

def coat_on_bench(fr, v, fold=B.REST_FOLD, lift=0.0, glint=0.0, key_ang=None, sil=False):
    x, y, s = coat_place(v)
    fr, kp, L = draped_coat(fr, x, y, s, open_=0.0, lift=lift, sil=sil, glint=glint, key_ang=key_ang)
    return fr

def key_on_coat_pt(v):
    x, y, s = coat_place(v)
    fr, kp, L = draped_coat(np.zeros((H, W, 3), np.float32), x, y, s, shadow=False)
    return kp[0], kp[1]

# patch the animator's beats so every beat that lays the coat on the bench uses the draped coat
B.coat_on_bench = coat_on_bench
B.key_on_coat_pt = key_on_coat_pt

# ================================================================== the conductor's reaching arm (same print)
_f = PIECES['forearm']
_sat = _f[..., :3].max(-1) - _f[..., :3].min(-1)
_xx = np.arange(_f.shape[1])[None, :]
_handm = ((_sat < 0.18) & (_f[..., :3].mean(-1) > 0.35) & (_xx < 200) & (_f[..., 3] > 0.5)).astype(np.uint8)
_handm = cv2.morphologyEx(_handm, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(np.float32)
_armA = np.maximum(_handm, _f[..., 3] * (_xx >= 192))
ARM = rgba(_f[..., :3], cv2.GaussianBlur(_armA, (3, 3), 0))
ARM_GRIP = (112.0, 236.0)          # fingertips (forearm piece coords)
ELBOW = (262.0, 292.0)
SL_CUFF = (60.0, 585.0)            # sleeve piece: cuff end

def reach_arm(fr, gx, gy, s, ang=90.0, sil=False):
    """forearm + sleeve, fingertips at screen (gx, gy), hanging from a shoulder above the frame."""
    Mf = T(gx, gy) @ R((0, 0), ang) @ np.diag([s, s, 1.0]) @ T(-ARM_GRIP[0], -ARM_GRIP[1])
    ex, ey = tp(Mf, ELBOW)
    Ms = T(ex, ey) @ R((0, 0), -8) @ np.diag([s, s, 1.0]) @ T(-SL_CUFF[0], -SL_CUFF[1])
    sl = SIL['sleeve'] if sil else PIECES['sleeve']
    arm = ARM.copy()
    if sil: arm[..., :3] = 0
    fr = paint(fr, sl, Ms)
    fr = paint(fr, arm, Mf)
    return fr

II2_Z, II2_C = 1.9, (711.0, 440.0)
def II2(t, sil=False, stage=True):
    """push-in on the bench (as U3's II.2).  0-0.40 the red sleeve and hand come down to the collar; 0.40-0.50
    the fingers close (the coat sags); 0.50-1.05 the coat is lifted: its skirt swings open on the waist hinge,
    a brass glint in the fold (frames 12-17); 1.05- U3's swap: the conductor wearing it, behind the bench."""
    v = B.View(II2_Z, II2_C)
    if t >= 1.05:
        return B.II2(0.9 + (t - 1.05) * 1.2, sil=sil, stage=stage)
    fr = B.wide_bg(v) if (stage and not sil) else np.ones((H, W, 3), np.float32)
    fr = B.draw_bench(fr, v, sil=sil)
    x, y, s = coat_place(v)
    u = sm((t - 0.50) / 0.55)
    lift = 300 * u ** 1.5
    open_ = sm((t - 0.50) / 0.40)
    k = int(t * FPS)
    glint = 1.0 if 12 <= k < 18 else 0.0
    sag = 3 * sm((t - 0.40) / 0.10) * (1 - u)
    fr, kp, L = draped_coat(fr, x, y + sag, s, open_=open_, lift=lift, sil=sil, glint=glint,
                            key_ang=None)
    if glint and not sil:          # the key's bow caught in the fold as the skirt opens
        kx, ky = tp(L, (C_CX + 38, FOLD_Y - 6))
        fr = S.draw_key(fr, kx, ky, 75, s=0.55 * s / 0.2, glint=0.7)
    gx, gy = tp(L, (C_CX + 6, C_TOP + 22))
    down = sm(t / 0.40)
    gy_hand = -60 + (gy + 60) * down if t < 0.40 else gy
    gx_hand = gx + 40 * (1 - down)
    fr = reach_arm(fr, gx_hand, gy_hand, s * 1.8, sil=sil)
    return fr

# ================================================================== III.1  the false lead, with the key in it
def III1(t):
    """21.0-22.5  shadow-theatre silhouette of the visitor (Reiniger replacement turn, done by 0.45 s) walking
    off with the brass key dangling from her hand: the hypothesis 'she took it back', shown as a shadow."""
    v = B.View(1.5, (380.0 + 120 * t / 1.5, 600.0))
    fr = B.wide_bg(v)
    u = sm((t - 0.05) / 0.40)
    sx = math.cos(math.pi * u)
    src = S.VISF if sx >= 0 else S.VISB
    sil = np.dstack([np.zeros_like(src[..., :3]) + S.INK, src[..., 3]])
    hh = 400.0
    s = hh / src.shape[0]
    x = 300.0 + 90 * sm((t - 0.45) / 1.05)
    y = 500.0 - 6 * abs(math.sin(math.pi * 1.4 * t))
    M = T(x, y) @ np.diag([s * max(abs(sx), 0.06), s, 1.0]) @ T(-src.shape[1] / 2, -src.shape[0])
    fr = B.shadow(fr, x, y, 50, 9)
    # the key hangs from her right hand by its bow: damped pendulum, kicked by each step
    hxk, hyk = x + 0.30 * src.shape[1] * s * max(abs(sx), 0.06) + 6, y - 0.47 * hh
    ang = 180 + 14 * math.sin(2 * math.pi * 1.4 * t) * math.exp(-0.4 * t)   # shaft down from the bow
    kh, kw = KEY.shape[:2]
    bow = (kw / 2, kh * 0.80)
    Mk = T(hxk - bow[0], hyk - bow[1]) @ R(bow, ang, 1.9)
    fr = paint(fr, KEY, Mk)
    return paint(fr, sil, M)

# ================================================================== IV.5  the coat crosses mid-frame at 0.75 s
def IV5(t, sil=False):
    planes = S.run_stage()
    cx = 1500 * t
    fr = np.zeros((H, W, 3), np.float32)
    for p in planes[:3]: p.draw(fr, cx, 3000)
    pose, _ = S.run_pose(t)
    hx = 1400 - 1100 * t                                   # through x ~ 575 at 0.75 s (U3's sweep reached it at 0.47)
    if -800 < hx < 1800:
        M = RUN.mats(hx, 150, 1.5, 8.0, pose)
        fr = RUN.draw(fr, M, skip=('thighN', 'thighF', 'shinN', 'shinF'))
    planes[3].draw(fr, cx, 3000)
    return fr

# ================================================================== V.1  the bench stays in frame through 0.75 s
def cam_V1(t): return S.VR * t ** 3 / (3 * 1.5 ** 2)    # velocity VR t^2/1.5^2: 0 -> VR at 1.5 s, slow start
def V1(t, sil=False):
    planes = S.run_stage()
    cx = cam_V1(t)
    fr = np.zeros((H, W, 3), np.float32)
    for p in planes[:3]: p.draw(fr, cx, 6000)
    bx = 600 - 0.8 * cx
    fr = paint(fr, S.BENCH, T(bx - 220 * 1.1, 470 - 380 * 1.1) @ np.diag([1.1, 1.1, 1.0]))
    planes[3].draw(fr, cx, 6000)
    return fr

# ================================================================== V.2  U4's receipt card, flat to camera at 0.75 s
_RC = np.asarray(Image.open(os.path.join(PRINT, 'receipt_2_underlined.png')).convert('RGBA'), np.float32) / 255.
_rk = 230.0 / _RC.shape[1]
RCARD = cv2.resize(_RC, None, fx=_rk, fy=_rk, interpolation=cv2.INTER_AREA)
def V2(t, sil=False):
    planes = S.run_stage()
    cx = B.V2_CX0 + S.VR * t
    fr = np.zeros((H, W, 3), np.float32)
    for p in planes[:3]: p.draw(fr, cx, 6000)
    u = t / 1.5
    xx = 760 - 520 * u + 30 * math.sin(5 * t); yy = 330 - 210 * u + 22 * math.sin(4.3 * t + 1)
    ang = 14 * math.sin(3.1 * t) - 10 * u
    flip = math.cos(2 * math.pi * 0.9 * (t - 0.75))          # face-on at 0.75 s, turning edge-on either side
    h, w = RCARD.shape[:2]
    Mr = T(xx, yy) @ R((0, 0), ang) @ np.diag([1.0, max(abs(flip), 0.05), 1.0]) @ T(-w / 2, -h / 2)
    card = RCARD.copy()
    if flip < 0: card[..., :3] *= 0.75
    fr = paint(fr, card, Mr)
    if t > 0.9:
        pose, _ = S.run_pose(40.5 + t)
        hx = S.X_LOCK - 760 * (1 - sm((t - 0.9) / 0.6))
        M = RUN.mats(hx, S.HIP_Y + S.bob(40.5 + t), S.SCALE, S.LEAN, pose)
        fr = RUN.draw(fr, M)
    planes[3].draw(fr, cx, 6000)
    return fr

# ================================================================== V.4  replay at half speed, then the key at rest
V4_REPLAY = 0.70                      # local seconds of replay
V4_SRC = (43.15, 43.60)               # source (test-shot) time covered by the replay
def v4_src_t(t): return V4_SRC[0] + (V4_SRC[1] - V4_SRC[0]) * t / V4_REPLAY
V4_SPEED = (V4_SRC[1] - V4_SRC[0]) / V4_REPLAY
V4_ZOOM, V4_ZC = 1.45, (470.0, 330.0)  # crop centre (screen px of the test shot)
def _zoom(fr):
    M = np.float32([[V4_ZOOM, 0, W / 2 - V4_ZC[0] * V4_ZOOM], [0, V4_ZOOM, H / 2 - V4_ZC[1] * V4_ZOOM]])
    return cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
_GRASS = None
def grass():
    """one photograph of grass: the dyed meadow plate (Bourre 50866798791), rows 640-960 x 300-870, no seams."""
    global _GRASS
    if _GRASS is None:
        md = S.plate('meadow')
        _GRASS = cv2.resize(md[650:960, 330:881], (W, H), interpolation=cv2.INTER_CUBIC)
    return _GRASS
KEY_REST = (520.0, 250.0)
KEY_BIG, KPIV_BIG = S.key_piece(205)          # the CC0 key re-sampled at full size (not an upscale)
def v4_rest(t, sil=False):
    """local t >= V4_REPLAY: close on the grass; the key lies large (s 3.2), rocking to rest; contact shadow;
    the red sleeve and hand come down at 1.00, close on it at 1.22, lift it out by 1.5."""
    fr = grass().copy()
    tr = t - V4_REPLAY
    rock = 5 * math.exp(-tr / 0.15) * math.cos(2 * math.pi * 3.0 * tr)
    ang = 100 + rock
    took = t >= 1.22
    up = sm((t - 1.24) / 0.26) if took else 0.0
    kx, ky = KEY_REST[0], KEY_REST[1] - 420 * up
    if not took or up < 0.05:
        k = 1.0 if not took else 1 - up / 0.05
        fr = B.shadow(fr, kx + 10, ky + 12, 105, 20, 1 - 0.6 * k)          # contact shadow (cut mask)
    fr = S.draw_key(fr, kx, ky, ang, k=KEY_BIG, kp=KPIV_BIG)
    if t > 1.0:
        down = sm((t - 1.0) / 0.22)
        gy = -80 + (ky - 8 + 80) * down
        fr = reach_arm(fr, kx + 10, gy, 0.95)
    return fr
def V4(t, sil=False):
    if t < V4_REPLAY:
        ts = v4_src_t(t)
        fr = S.integrate(lambda tt: S.v3_sub(tt), ts, 24, 0.5 * V4_SPEED)       # shutter in source time
        return _zoom(fr)
    return v4_rest(t)

# ================================================================== I.3  a real envelope (LoC 2010652109, back)
ENV_FILE = os.path.join(ENV_SRC, 'loc_11331v.jpg')          # back of the stamped envelope, 1861, LoC PPOC, no known restrictions
def _envelope_cut():
    im = cv2.imread(ENV_FILE)                                   # decoded with OpenCV only
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    paper = ((hsv[..., 2] > 110) & (hsv[..., 1] < 120)).astype(np.uint8)
    paper = cv2.morphologyEx(paper, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(paper)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = (lab == big).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    m = np.zeros_like(m); cv2.drawContours(m, cnts, -1, 1, -1)          # holes filled: the paper is one sheet
    # GrabCut refinement seeded by the threshold (SCION 29): sure-bg outside a dilated mask, sure-fg eroded
    gc = np.where(cv2.erode(m, np.ones((15, 15), np.uint8)) > 0, cv2.GC_FGD,
                  np.where(cv2.dilate(m, np.ones((15, 15), np.uint8)) > 0, cv2.GC_PR_FGD, cv2.GC_BGD)).astype(np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(im, gc, None, bgd, fgd, 3, cv2.GC_INIT_WITH_MASK)
    a = np.isin(gc, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.float32)
    a = cv2.GaussianBlur(a, (3, 3), 0)
    # library pencil marks (accession number, inventory code) are not part of the story: inpainted, declared
    ys, xs = np.nonzero(a > 0.5); y1 = ys.max()
    marks = np.zeros(im.shape[:2], np.uint8)
    marks[y1 - 70:y1 - 4, :] = (hsv[y1 - 70:y1 - 4, :, 2] < 120).astype(np.uint8) & (a[y1 - 70:y1 - 4] > 0.5)
    marks = cv2.dilate(marks, np.ones((5, 5), np.uint8))
    im = cv2.inpaint(im, marks, 7, cv2.INPAINT_TELEA)
    rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.
    x0, x1 = xs.min(), xs.max()
    y0 = ys.min()
    cv2.imwrite(os.path.join(ENV_SRC, 'envelope_alpha.png'), (a * 255).astype(np.uint8))
    return rgba(rgb * 0.94, a)[y0:y1 + 1, x0:x1 + 1]
ENVP = None
def I3(t, sil=False):
    """6.0-7.5: the real envelope (back, flap side) on the gravel; the key slides up out of its slit top edge
    (0.10-0.65 s), half out by the sample time 0.75, then settles."""
    global ENVP
    if ENVP is None: ENVP = _envelope_cut()
    gnd = S.plate('meadow')
    fr = cv2.resize(gnd[600:960, 200:840], (W, H), interpolation=cv2.INTER_AREA).copy()
    eh, ew = ENVP.shape[:2]
    s = 600.0 / ew
    ex, ey = 180.0, 190.0
    Me = T(ex, ey) @ R((0, 0), -3.0) @ np.diag([s, s, 1.0])
    m = cv2.warpAffine(np.ones((eh, ew), np.float32), (T(10, 12) @ Me)[:2], (W, H), borderValue=0)
    fr = fr * (1 - 0.45 * cv2.GaussianBlur(m, (0, 0), 7)[..., None])          # contact shadow on the gravel
    u = sm((t - 0.10) / 0.55)
    top = tp(Me, (ew * 0.62, 6))
    kh = KEY_BIG.shape[0]
    kx = top[0] + 4 * math.sin(2 * math.pi * 1.2 * t) * (1 - u)
    ky = top[1] + 40 - 150 * u                             # pivot at the bow: bow first, shaft still inside
    fr = S.draw_key(fr, kx, ky, 186 - 8 * u, k=KEY_BIG, kp=(KEY_BIG.shape[1] / 2, kh * 0.80))
    return paint(fr, ENVP, Me)

# ================================================================== render
CLIPS = {   # name: (frame fn, sub-frames)  -- clips are 36 frames = one 1.5 s slot, silent, no type
    'I1_manteau_E2': (B.I1, 1), 'I2_cloche_E2': (B.I2, 4), 'I3_cle_E2': (I3, 6), 'I4_banc_E2': (B.I4, 4),
    'I5_recu_E2': (B.I5, 6), 'I6_porte_E2': (B.I6, 4), 'II2_manteau_E2': (II2, 6), 'III1_cle_E2': (III1, 6),
    'IV5_manteau_E2': (IV5, 36), 'V1_banc_E2': (V1, 36), 'V2_recu_E2': (V2, 36), 'V4_cle_E2': (V4, 4),
}

def frame(name, k):
    fn, n = CLIPS[name]
    t = (k + 0.5) / FPS
    if name == 'V4_cle_E2' and t < V4_REPLAY:
        return fn(t)                                           # the replay integrates in source time itself
    return S.integrate(fn, t, n, 0.5) if n > 1 else fn(t)

def render(name):
    w = S.Writer(os.path.join(OUT, name + '.mp4'))
    for k in range(36):
        img = S.to_img(frame(name, k)); w.add(img)
        if k == 18: img.save(os.path.join(STILLS, name + '_mid.png'))
    w.close()

def measure_v4_replay():
    """key trajectory measured from the rendered replay frames: each frame is rendered twice, with and without
    the key (S.draw_key disabled), and the key is the difference mask; centroid per frame -> parabola fit in
    source time (y = a + b t + g/2 t^2).  Written to editor/measures/v4_replay_key.json."""
    import json as _j
    rec = []
    orig = S.draw_key
    for k in range(int(V4_REPLAY * FPS)):
        t = (k + 0.5) / FPS
        a = V4(t)
        S.draw_key = lambda fr, *aa, **kw: fr
        b = V4(t)
        S.draw_key = orig
        d = np.abs(a - b).sum(-1)
        m = d > 0.12
        if m.sum() < 30: continue
        ys, xs = np.nonzero(m)
        rec.append(dict(frame=k, t_local=t, t_src=v4_src_t(t), x=float(xs.mean()), y=float(ys.mean()), px=int(m.sum())))
    ts = np.array([r['t_src'] for r in rec]); ys = np.array([r['y'] for r in rec])
    fall = (ts >= S.T_DROP) & (ts <= S.T_LAND)
    out = dict(frames=rec, note='centroid of |with key - without key| > 0.12 in the rendered replay frames (zoom %.2f)' % V4_ZOOM)
    if fall.sum() >= 3:
        c = np.polyfit(ts[fall] - S.T_DROP, ys[fall], 2)
        res = ys[fall] - np.polyval(c, ts[fall] - S.T_DROP)
        out['fit'] = dict(n=int(fall.sum()), g_screen_px_s2=float(2 * c[0]), g_source_px_s2=float(2 * c[0] / V4_ZOOM),
                          rms_residual_px=float(np.sqrt((res ** 2).mean())), visible_frames_in_replay=int(fall.sum()))
    _j.dump(out, open(os.path.join(MEAS, 'v4_replay_key.json'), 'w'), indent=1)
    return out

if __name__ == '__main__':
    names = sys.argv[1:] or list(CLIPS)
    for nm in names:
        if nm == 'measure':
            print(json.dumps(measure_v4_replay().get('fit'), indent=1)); continue
        render(nm); print('rendered', nm, flush=True)
