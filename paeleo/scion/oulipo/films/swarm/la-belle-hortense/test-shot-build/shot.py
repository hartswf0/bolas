"""La Belle Hortense, TEST SHOT: module V, slot 3 (MANTEAU), with its handles.

python3 -I shot.py [--stills t ...]        (run cut.py first)

Shot time 0.0-5.0 s  ==  film time 40.0-45.0 s  (film t = 40.0 + shot t)
  0.0-0.5  V.1 banc (tail)   pan already running, runner still off frame right
  0.5-2.0  V.2 recu          the handmade ticket lifts in the runner's wind; he catches the camera
  2.0-3.5  V.3 MANTEAU       locked tight on the red coat, full streak; key slips from the fold at 3.2 (film 43.2)
  3.5-5.0  V.4 cle           key lands brass-on-green; the operator overshoots and whips back to it; hold

SCION 2 (Reiniger): pinned FK rig from rig.json (body root, forearm at elbow, two substitution shins at hem).
SCION 44 (multiplane): far 0.35 / mid 0.6 / ground 1.0 / near 1.6, all cut from the Bourre plate.
Streak = real temporal integration: each output frame is the mean of N=36 sub-frames over a 360-degree
shutter (1/24 s) of the moving stage. No blur filter anywhere.
Stencil colour: monochrome print of every plate + dye masks keyed from the plate's own hues.
"""
import sys, os, json, math, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
sys.path.insert(0, os.path.join(ROOT, 'films'))
import kit                                                      # noqa: E402
from pathlib import Path                                        # noqa: E402

BUILD = os.path.dirname(os.path.abspath(__file__))
MED = os.path.join(ROOT, 'films/sources/la-belle-hortense/test-shot')
OUTD = Path(os.path.join(ROOT, 'films/swarm/la-belle-hortense'))
W, H, FPS = 960, 540, 24
DUR = 5.0
N_SUB = 72
SHUTTER = 1.0                          # fraction of the frame interval (1.0 = 360 degrees)
CB = '/usr/share/fonts/X11/Type1/c0583bt_.pfb'
CR = '/usr/share/fonts/X11/Type1/c0419bt_.pfb'
_fc = {}
def font(sz, bold=True):
    k = (sz, bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(CB if bold else CR, sz)
    return _fc[k]

def hexc(s): return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.
RED = hexc('#e2011b'); TRED = hexc('#b00a1a'); INKC = hexc('#010201'); BRASS = hexc('#c9a23a')
GREEN_Y = hexc('#86b23c'); GREEN_B = hexc('#2f9a3a'); OCHRE = hexc('#8a7432'); PAPERC = hexc('#e6e6c0')

def over(dst, src, a): return dst * (1 - a[..., None]) + src * a[..., None]
def smooth(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def printc(g):
    """the one shared print curve (grade only to unify plates and figure)"""
    return np.clip((g - 0.10) / 0.72, 0, 1) ** 1.15        # a hard (grade-4) paper

# ------------------------------------------------------------------ stage (multiplane)
def build_stage():
    im = cv2.imread(os.path.join(MED, 'plates/Bourr_Loir-et-Cher_50866798791_.jpg'))  # 1280x960, BGR
    S = 0.9
    im = cv2.resize(im, (int(1280 * S), int(960 * S)), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.
    hh, ww = g.shape
    rows = np.arange(hh)[:, None] * np.ones((1, ww))
    hue, sat = hsv[..., 0], hsv[..., 1]
    grass = ((hue > 24) & (hue < 75) & (sat > 38) & (rows > 398)).astype(np.float32)
    grass = cv2.morphologyEx(grass, cv2.MORPH_OPEN, np.ones((3, 3)))
    grass = cv2.GaussianBlur(grass, (7, 7), 0)          # soft stencil edge (the cut mask, not the image)
    yellow = np.clip((46 - hue) / 10, 0, 1)              # yellower blades -> yellow-green dye, bluer -> deep green
    brick = (((hue < 10) | (hue > 168)) & (sat > 70)).astype(np.float32)
    brick = cv2.GaussianBlur(brick, (3, 3), 0)
    soil = ((sat < 60) & (rows > 420) & (g < 0.62)).astype(np.float32) * (1 - grass)
    soil = cv2.GaussianBlur(soil, (9, 9), 0)
    p = np.clip((g - 0.08) / 0.40, 0, 1) ** 0.9             # the plate's own print: lighter, hard grade
    base = p[..., None] * PAPERC                         # the monochrome print on cream stock
    dyeG = (0.06 + 0.98 * p)[..., None] * (GREEN_Y * yellow[..., None] + GREEN_B * (1 - yellow[..., None])) * 1.12
    col = over(base, dyeG, grass)
    col = over(col, (0.2 + 0.8 * p)[..., None] * OCHRE * 1.2, soil * 0.85)
    col = over(col, (0.25 + 0.75 * p)[..., None] * RED * 0.95, brick * 0.9)
    col = np.clip(col, 0, 1).astype(np.float32)
    # frame placement of the plate at rest: plate y -> frame y = y - OY
    OY = 282                                             # camera tilted down: the shed's lower wall behind his shoulders
    col = col[OY:]
    # planes (rows in frame space), each a horizontal strip wrapped with its mirror
    def strip(y0, y1, scale=1.0):
        a = col[max(0, y0):y1]
        if scale != 1.0:
            a = cv2.resize(a, (int(a.shape[1] * scale), int(a.shape[0] * scale)), interpolation=cv2.INTER_CUBIC)
        return np.ascontiguousarray(np.concatenate([a, a[:, ::-1]], 1))
    far = strip(0, 140)                                  # goods-shed wall, door, quoins, trees (0..200)
    mid = strip(96, 280)                                 # platform wall + far meadow (placed at 96)
    gnd = strip(236, 560)                                # the runner's ground (placed at 236)
    near = strip(470, hh - OY, 1.5)                      # close grass blades, enlarged (placed at 506)
    return dict(far=(far, 0, 0.35, None), mid=(mid, 96, 0.60, 24), gnd=(gnd, 236, 1.0, 40), near=(near, 506, 1.6, 22))

def place_plane(fr, plane, cx):
    img, y0, ratio, feather = plane
    sw = img.shape[1]
    off = (ratio * (cx - CX_END) + REST_X0) % sw         # at rest every plane shows the same plate column: the photo re-forms
    i0 = int(off); fx = off - i0
    idx = (np.arange(i0, i0 + W + 1)) % sw
    a = img[:, idx]
    a = a[:, :W] * (1 - fx) + a[:, 1:W + 1] * fx       # sub-pixel translation (bilinear, no blur kernel)
    h = min(a.shape[0], H - y0)
    if feather is None:
        fr[y0:y0 + h] = a[:h]
    else:
        m = np.clip(np.arange(h) / feather, 0, 1)[:, None, None]
        fr[y0:y0 + h] = fr[y0:y0 + h] * (1 - m) + a[:h] * m

# ------------------------------------------------------------------ rig (SCION 2)
RIG = json.load(open(os.path.join(BUILD, 'rig.json')))
PZ = np.load(os.path.join(MED, 'cut/pieces.npz'))
HEM = RIG['pieces']['body']['pivot_hip'][1]
ELB = tuple(RIG['pieces']['forearm']['pivot_elbow'])
PIVN = tuple(RIG['pieces']['shinN']['pivot_hem']); PIVF = tuple(RIG['pieces']['shinF']['pivot_hem'])
STRETCH = RIG['pieces']['shinN']['stretch_y']

def dye_piece(gray, alpha, coat):
    gc = np.clip((gray - 0.03) / 0.40, 0, 1) ** 0.8               # coat densities re-printed light so the dye reads
    mono = printc(gray)[..., None] * PAPERC
    red = (0.10 + 0.90 * gc)[..., None] * RED
    rgb = over(mono, red, coat)
    return np.dstack([rgb, alpha]).astype(np.float32)

BODY = dye_piece(PZ['body_g'], PZ['body_a'], PZ['coat'])
FORE = dye_piece(PZ['g'], PZ['fore_a'], PZ['fore_coat'])
SHN = np.dstack([printc(PZ['g'])[..., None] * PAPERC * 0.9, PZ['shinN']]).astype(np.float32)
SHF = np.dstack([printc(PZ['g'])[..., None] * PAPERC * 0.5, PZ['shinF']]).astype(np.float32)

def A3(M): return np.vstack([M, [0, 0, 1]])
def rot(p, ang): return A3(cv2.getRotationMatrix2D(p, ang, 1.0))
def stretch(p, sy): return np.array([[1, 0, 0], [0, sy, p[1] * (1 - sy)], [0, 0, 1]], np.float64)
def tp(M, p): v = M @ np.array([p[0], p[1], 1.0]); return v[:2]

SCALE = 0.74
LEAN = 9.0
STRIDE_HZ = 2.3
def rig_mats(t, hip_x, hip_y):
    ph = STRIDE_HZ * t
    a = 32 * math.sin(2 * math.pi * ph)
    bob = -7 * abs(math.cos(2 * math.pi * ph))                     # body rises between footfalls
    Mb = A3(cv2.getRotationMatrix2D(PIVN, LEAN, SCALE))
    Mb[0, 2] += hip_x - PIVN[0]; Mb[1, 2] += hip_y + bob - PIVN[1]
    lim = RIG['pieces']['shinN']['limits_deg']
    aN = float(np.clip(a, *lim)); aF = float(np.clip(-a, *lim))
    MN = Mb @ rot(PIVN, aN) @ stretch(PIVN, STRETCH)
    MF = Mb @ rot(PIVF, aF) @ stretch(PIVF, STRETCH)
    fl = RIG['pieces']['forearm']['limits_deg']
    MA = Mb @ rot(ELB, float(np.clip(-7 * math.sin(2 * math.pi * ph) - 2, *fl)))
    return Mb, MN, MF, MA, ph

def paint(fr, piece, M):
    rgba = cv2.warpAffine(piece, M[:2], (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    return over(fr, rgba[..., :3], rgba[..., 3])

# ------------------------------------------------------------------ key (CC0 photo) and ticket (handmade)
kim = cv2.imread(os.path.join(MED, 'plates/skeletonkey.png'), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.
kp = kim[60:640, 160:440]
km = (kp < 0.45).astype(np.float32)
km = cv2.morphologyEx(km, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
KH = 96; KW = int(kp.shape[1] * KH / kp.shape[0])
kgr = cv2.resize(np.clip(1.0 - kp, 0, 1) * 0.55 + 0.45 * (kp > 0.7), (KW, KH), interpolation=cv2.INTER_AREA)
kal = cv2.resize(km, (KW, KH), interpolation=cv2.INTER_AREA)
KEY = np.dstack([(0.30 + 0.70 * kgr)[..., None] * BRASS * 1.08, kal]).astype(np.float32)
KPIV = (KW / 2, KH * 0.35)

def make_ticket():
    """HANDMADE: the receipt REÇU N° 6, typeset on cream card with a red number stamp."""
    tw, th = 150, 84
    im = Image.new('RGBA', (tw, th), (236, 230, 205, 255)); d = ImageDraw.Draw(im)
    d.rectangle((2, 2, tw - 3, th - 3), outline=(30, 28, 24, 255), width=2)
    d.text((10, 8), 'REÇU', font=font(22), fill=(12, 12, 10, 255))
    d.text((10, 36), 'une clé', font=font(14, False), fill=(12, 12, 10, 255))
    d.text((10, 54), 'remise au banc', font=font(14, False), fill=(12, 12, 10, 255))
    d.ellipse((92, 8, 140, 52), outline=(200, 16, 28, 255), width=3)
    d.text((106, 12), '6', font=font(30), fill=(200, 16, 28, 255))
    a = np.asarray(im, np.float32) / 255.
    return a
TICKET = make_ticket()

# ------------------------------------------------------------------ camera, runner, key physics (exposure sheet)
VR = 5500.0                      # runner speed (px/s at the figure plane), running left
X_LOCK = 610.0                   # hip screen x while the camera is locked on him
HIP_Y = 420.0             # hem height on screen
T_IN0, T_IN1 = 0.0, 1.6          # runner catches the camera
T_DROP = 3.2                     # film 43.2
T_STOP = 4.55                    # camera at rest on the key

def runner_screen_x(t):
    if t < T_IN1:
        return X_LOCK + 700 * (1 - smooth((t - T_IN0) / (T_IN1 - T_IN0))) ** 1.0
    return X_LOCK

# camera position cx (figure-plane px; screen x of world X = X - cx). Runner world X = -VR t.
def cam_run(t):
    return -VR * t - runner_screen_x(t)

# key: released from the coat fold at T_DROP
FOLD = (214.0, 600.0)            # piece coords of the fold at the coat's front edge
def key_world_state():
    Mb, *_ = rig_mats(T_DROP, X_LOCK, HIP_Y)
    sx, sy = tp(Mb, FOLD)
    X0 = sx + cam_run(T_DROP)
    return X0, sy
KX0, KY0 = key_world_state()
G = 3270.0; VY0 = -330.0; GROUND_Y = 488.0
T_LAND = T_DROP + (-VY0 + math.sqrt(VY0 ** 2 + 2 * G * (GROUND_Y - KY0))) / G
VY_LAND = VY0 + G * (T_LAND - T_DROP)
T_HOP = 2 * 0.28 * VY_LAND / G
SLIDE_T = 0.16
def key_state(t):
    """world x, screen y, angle (deg)"""
    if t < T_DROP: return None
    if t < T_LAND:
        dt = t - T_DROP
        return KX0 - VR * dt, KY0 + VY0 * dt + 0.5 * G * dt * dt, 30 + 760 * dt
    xl = KX0 - VR * (T_LAND - T_DROP)
    ang_l = 30 + 760 * (T_LAND - T_DROP)
    dt = t - T_LAND
    s = min(dt, SLIDE_T)
    x = xl - VR * (s - s * s / (2 * SLIDE_T))         # friction: velocity decays linearly to 0
    y = GROUND_Y
    if dt < T_HOP:
        v = 0.28 * VY_LAND
        y = GROUND_Y - (v * dt - 0.5 * G * dt * dt)
    ang = ang_l + 300 * (1 - math.exp(-dt / 0.08)) * 0.4
    ang_rest = 98.0                                    # lies nearly flat, bow toward camera-right
    ang = ang + (ang_rest - ang) * smooth(dt / 0.35)
    return x, y, ang
KX_REST = key_state(T_LAND + 1.0)[0]
CX_END = KX_REST - 700.0                               # key rests at screen x 700

T_BRK = 3.62
def cam(t):
    if t <= T_BRK: return cam_run(t)
    if t >= T_STOP: return CX_END
    # operator brakes, overshoots and whips back: Hermite from (T_BRK, cam, -VR) to (T_STOP, CX_END, 0)
    c0 = cam_run(T_BRK); v0 = -VR
    L = T_STOP - T_BRK; s = (t - T_BRK) / L
    h00 = 2 * s ** 3 - 3 * s ** 2 + 1; h10 = s ** 3 - 2 * s ** 2 + s; h01 = -2 * s ** 3 + 3 * s ** 2
    return h00 * c0 + h10 * L * v0 + h01 * CX_END

def runner_hip_x(t):
    # the camera follows smoothly; the body surges at footfall rate, so the tracking is never perfect
    return -VR * t - cam(t) + 16 * math.sin(2 * math.pi * 2 * STRIDE_HZ * t)

def ticket_state(t):
    """screen x, y, angle, flip -- the ticket rides the runner's wake (air plane ~0.9 of figure speed)"""
    if not (0.45 <= t <= 2.25): return None
    u = (t - 0.45) / 1.8
    x = 940 - 820 * u + 30 * math.sin(7.0 * t)
    y = 520 - 470 * u + 40 * math.sin(4.3 * t + 1) - 160 * math.sin(math.pi * u)
    return x, y, 25 * math.sin(5.1 * t) + 260 * u, math.cos(2 * math.pi * 1.6 * t)

# ------------------------------------------------------------------ one sub-frame of the stage
REST_X0 = 40.0
STAGE = build_stage()
def subframe(t):
    cx = cam(t)
    fr = np.zeros((H, W, 3), np.float32)
    place_plane(fr, STAGE['far'], cx)
    place_plane(fr, STAGE['mid'], cx)
    place_plane(fr, STAGE['gnd'], cx)
    ts = ticket_state(t)
    if ts:
        x, y, ang, flip = ts
        M = A3(cv2.getRotationMatrix2D((75, 42), ang, 1.0)) @ stretch((75, 42), max(0.08, abs(flip)))
        M[0, 2] += x - 75; M[1, 2] += y - 42
        rgba = cv2.warpAffine(TICKET, M[:2], (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        shade = 1.0 if flip > 0 else 0.78
        fr = over(fr, rgba[..., :3] * shade, rgba[..., 3])
    hx = runner_hip_x(t)
    if -400 < hx < W + 400:
        Mb, MN, MF, MA, ph = rig_mats(t, hx, HIP_Y)
        fr = paint(fr, SHF, MF)
        ks = key_state(t)
        if ks and t < T_LAND:          # falling key passes behind the near shin
            fr = draw_key(fr, ks, cx)
        fr = paint(fr, SHN, MN)
        fr = paint(fr, BODY, Mb)
        fr = paint(fr, FORE, MA)
        if t < T_DROP:                 # the key's bow shows in the fold until it slips
            Mk = A3(cv2.getRotationMatrix2D(KPIV, 30 + 6 * math.sin(2 * math.pi * ph), 0.9))
            fx, fy = tp(Mb, FOLD)
            Mk[0, 2] += fx - KPIV[0]; Mk[1, 2] += fy - KPIV[1]
            rgba = cv2.warpAffine(KEY, Mk[:2], (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
            fr = over(fr, rgba[..., :3], rgba[..., 3])
    ks = key_state(t)
    if ks and t >= T_LAND:
        fr = draw_key(fr, ks, cx)
    place_plane(fr, STAGE['near'], cx)
    return fr

def draw_key(fr, ks, cx):
    X, y, ang = ks
    sx = X - cx
    Mk = A3(cv2.getRotationMatrix2D(KPIV, ang, 1.0)); Mk[0, 2] += sx - KPIV[0]; Mk[1, 2] += y - KPIV[1]
    rgba = cv2.warpAffine(KEY, Mk[:2], (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    return over(fr, rgba[..., :3], rgba[..., 3])

def exposure(k):
    """frame k: mean of N_SUB sub-frames spread over the open shutter, centred on k/FPS"""
    t0 = k / FPS
    acc = np.zeros((H, W, 3), np.float32)
    for i in range(N_SUB):
        acc += subframe(t0 + ((i + 0.5) / N_SUB - 0.5) * SHUTTER / FPS)
    return acc / N_SUB

# ------------------------------------------------------------------ type (HANDMADE typesetting)
ORDER_V = ['banc', 'reçu', 'manteau', 'clé', 'porte', 'cloche']
SLOTS = [(-1.0, 0.5, 0), (0.5, 2.0, 1), (2.0, 3.5, 2), (3.5, 5.01, 3)]
CAPS = {2: ('le manteau revient', 'the coat comes back'), 3: ('La clé était dans le pli.', 'The key was in the fold.')}
def typeset(img, t):
    d = ImageDraw.Draw(img)
    slot = [s for s in SLOTS if s[0] <= t < s[1]][0]
    k = slot[2]
    x, y = 44, 376
    d.text((x, y), 'V.', font=font(44), fill=(1, 2, 1))
    if k in CAPS:
        fr, en = CAPS[k]
        n = int(len(fr) * min(1, (t - slot[0]) / 0.35)) + 1        # typed on over 0.35 s
        d.text((x, y + 50), fr[:n], font=font(36), fill=tuple(int(c * 255) for c in TRED))
        if t - slot[0] > 0.3:
            d.text((x + 2, y + 92), en, font=font(18, False), fill=(1, 2, 1))
    xx = x + 2; yy = y + 124
    for j, wd in enumerate(ORDER_V):
        on = j == k
        s = wd.upper() if on else wd
        d.text((xx, yy), s, font=font(18, on), fill=(226, 1, 27) if on else (1, 2, 1))
        xx += d.textlength(s, font=font(18, on))
        if j < 5:
            d.text((xx, yy), ' · ', font=font(18, False), fill=(1, 2, 1)); xx += d.textlength(' · ', font=font(18, False))
    return img

def frame_img(k):
    a = exposure(k)
    img = Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8))
    return typeset(img, k / FPS)

# ------------------------------------------------------------------ sound
def readwav(p):
    w = wave.open(p); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768.
    return x if w.getnchannels() == 1 else x.reshape(-1, w.getnchannels()).mean(1)

def sound(mix):
    R = kit.RATE
    steps = readwav(os.path.join(MED, 'sound/Concrete_Steps_2.wav'))
    grains = [steps[int(0.0 * R):int(0.30 * R)], steps[int(0.33 * R):int(0.79 * R)]]
    paper = readwav(os.path.join(MED, 'sound/Book_paper_pages_assorted.wav'))
    mix.wind(0.0, DUR, gain=0.05)
    # footfalls at stride rate (two per stride cycle), only while he is on/near frame
    k = 0; tt = 0.08
    while tt < 4.2:
        hx = runner_hip_x(tt)
        if -300 < hx < W + 500:
            near = 1.0 - min(1, abs(hx - X_LOCK) / 900)
            g = 0.35 + 0.65 * near
            gr = grains[k % 2]
            rate = 1.0 + 0.03 * ((k * 7919) % 5 - 2) / 2
            idx = np.arange(0, len(gr) - 1, rate)
            mix.add(np.interp(idx, np.arange(len(gr)), gr) * 3.0, tt, g, float(np.clip((hx - 480) / 600, -0.8, 0.8)))
        tt += 1 / (2 * STRIDE_HZ); k += 1
    # the pan: air past the lens, then the whip-back
    mix.whoosh(0.2, 1.4, gain=0.10, pan=0.4)
    mix.whoosh(1.6, 2.0, gain=0.06)
    mix.whoosh(3.75, 0.7, gain=0.16, pan=0.3)
    # ticket flutter: a grain of real paper handling
    pg = paper[int(2.0 * R):int(3.2 * R)] * np.hanning(int(1.2 * R))
    mix.add(pg, 0.6, 0.9, -0.2)
    # slot clicks (typewriter) at slot starts
    for s in (0.5, 2.0, 3.5):
        mix.click(s, gain=0.35, bright=5000)
    # key: a faint slip at the fold, then tinks at landing and at the hop (synthesised struck brass)
    for at, gn in ((T_DROP, 0.05), (T_LAND, 0.22), (T_LAND + T_HOP, 0.10)):
        n = int(0.25 * R); tt_ = np.arange(n) / R
        sig = sum(a * np.sin(2 * np.pi * f * tt_) * np.exp(-tt_ * d) for f, a, d in ((3150, 1.0, 38), (4720, 0.6, 52), (6890, 0.35, 70), (2210, 0.3, 30)))
        mix.add(sig, at, gn, 0.25)

# ------------------------------------------------------------------ main
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        os.makedirs(os.path.join(MED, 'stills'), exist_ok=True)
        for ts in sys.argv[2:]:
            k = int(round(float(ts) * FPS))
            frame_img(k).save(os.path.join(MED, 'stills', f'{float(ts):05.2f}.png'))
        print('T_LAND', T_LAND, 'KX0', KX0, 'KY0', KY0)
        sys.exit()
    film = kit.Film('test-shot', DUR)
    film.poster_at = 3.3
    def pic(t, ink):
        ink._grain = False
        ink.img.paste(frame_img(int(round(t * FPS))))
    film.picture(pic)
    film.sound(sound)
    film.render(out_dir=OUTD)
