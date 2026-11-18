"""Editor repair round 2 (E3) for La belle Hortense: the beats the second critic could not read.

Same foraged cut pieces, same dye, same integrator as E2 (repair_beats imports and patches the animator's beats).
New here:
  * COAT SCALE: the coat lies on the LEFT half of the bench at 0.30 (was 0.225 at the centre), so it is a coat a
    man could wear and the visitor can reach it without overlapping the bench.  Every I-module coat shot re-renders.
  * I.4: the visitor (U2's back-view cut, LoC 2017750547, mirrored) stands clear of the bench's left end; her
    forearm piece hinges at the elbow, out over the coat; the key hangs from her hand by its bow, is let go, falls
    on a parabola onto the open folded skirt, rocks and lies; the forearm comes back.  Gap figure-bench >= 20 px.
  * II.2: the conductor as a full figure (cap, dark jacket = his own print undyed and narrowed below the collar,
    trousers, knee-jointed legs) walks in, leans, closes his hand on the collar, lifts the coat (skirt opens, brass
    glint in the fold), carries it to his shoulders and is then the red-coated figure (Reiniger replacement).
  * II.6: the key motif shown as its absence: a chalk outline of the key on the empty seat, the receipt beside it
    with 'une clé' struck through (U4's strike frames).
  * III.4: the crossing figure brought to the middle plane at 0.22 (>= 25 % of frame height).
  * TITLE: pan exposure over 240 px per frame (was 420) and the print curve stretched toward the cover's range.

    python3 -I films/swarm/la-belle-hortense/editor/repair3_beats.py [name ...|sil|measure]
"""
import os, sys, math, json
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = sys.argv[:1] + sys.argv[1:]
import repair_beats as RB              # noqa: E402  (patches beats: draped coat)
import editor_beats as EB              # noqa: E402
S, B = RB.S, RB.B
from scene import W, H, FPS, T, R, SY, SX, tp, over, paint, sm, RUN, PIECES, SIL, KEY, KPIV   # noqa: E402

ROOT = RB.ROOT
OUT = RB.OUT; STILLS = RB.STILLS; MEAS = RB.MEAS
CHECKS = os.path.join(ROOT, 'films/sources/la-belle-hortense/editor/checks')
os.makedirs(CHECKS, exist_ok=True)

# ------------------------------------------------------------------ coat: bigger, on the bench's left half
RB.COAT_ON = (112.0, 64.0)
RB.COAT_S = 0.30
def coat_place(v):
    x, y = tp(B.bench_M(v), RB.COAT_ON)
    return x, y, RB.COAT_S * v.z
RB.coat_place = coat_place

# ------------------------------------------------------------------ the visitor (U2 back-view cut, mirrored)
VC = os.path.join(ROOT, 'films/sources/la-belle-hortense/forage/cut/visitor')
RIG = json.load(open(os.path.join(ROOT, 'films/swarm/la-belle-hortense/rig.json')))['figures']['visitor']['pieces']
CROP_W, CROP_H = 240, 440
def _vpiece(name):
    a = np.asarray(Image.open(os.path.join(VC, name + '.png')).convert('RGBA'), np.float32) / 255.
    g = a[..., :3].mean(-1)
    full = np.zeros((CROP_H, CROP_W, 4), np.float32)
    ox, oy = RIG[name]['offset_in_crop']
    h, w = a.shape[:2]
    full[oy:oy + h, ox:ox + w] = np.dstack([S.mono(g, 1.0), a[..., 3]])
    return full
VP = {k: _vpiece(k) for k in ('shinL', 'shinR', 'body', 'forearm')}
# the upper arm, cut from the body piece along the inner edge of the sleeve (crop coords), hinged at the shoulder
_poly = np.array([[50, 88], [84, 90], [81, 190], [50, 192]], np.int32)
_um = np.zeros((CROP_H, CROP_W), np.uint8); cv2.fillPoly(_um, [_poly], 1)
_um = cv2.GaussianBlur(_um.astype(np.float32), (3, 3), 0)
VP['upper'] = VP['body'].copy(); VP['upper'][..., 3] *= _um
VP['torso'] = VP['body'].copy(); VP['torso'][..., 3] *= (1 - _um)
SHOULDER = (69.0, 99.0)
ELBOW = RIG['forearm']['pivots_crop']['pivot_elbowL']
HAND = RIG['forearm']['pivots_crop']['hand']
FEET_Y = 386.0
def visitor_mats(x, y, s, arm, lean=0.0):
    """crop coords -> screen, mirrored (her left arm on the bench side); feet at (x, y).  arm = (upper, fore) deg."""
    ua, fa = arm if isinstance(arm, tuple) else (0.0, arm)
    base = T(x, y) @ np.diag([-s, s, 1.0]) @ T(-110, -FEET_Y) @ R((110, 300), lean)
    Mu = base @ R(SHOULDER, ua)
    return base, Mu, Mu @ R(ELBOW, fa)
def visitor_draw(fr, x, y, s, arm, lean=0.0, sil=False):
    Mb, Mu, Mf = visitor_mats(x, y, s, arm, lean)
    def P(k):
        p = VP[k]
        return np.dstack([np.zeros_like(p[..., :3]), p[..., 3]]) if sil else p
    for k in ('shinL', 'shinR', 'torso'):
        fr = paint(fr, P(k), Mb)
    fr = paint(fr, P('upper'), Mu)
    fr = paint(fr, P('forearm'), Mf)
    return fr, tp(Mf, HAND)

# ------------------------------------------------------------------ I.4
I4_V = B.View(1.55, (655.0, 520.0))
VIS_Y, VIS_SC = 440.0, 1.12
ARM_OUT = (-58.0, -4.0)                # upper arm / forearm at full reach (negative = out toward the bench, mirrored)
LEAN_OUT = 0.0                         # she leans from the hips toward the bench while reaching
GAP = 30.0                             # body (forearm down) to bench, px, at rest
def _auto_x():
    fb = B.draw_bench(np.ones((H, W, 3), np.float32), I4_V, sil=True)
    xb = np.nonzero((fb.mean(-1) < 0.5).any(0))[0].min()
    fv, _ = visitor_draw(np.ones((H, W, 3), np.float32), 300.0, VIS_Y, VIS_SC, 0.0, sil=True)
    xv = np.nonzero((fv.mean(-1) < 0.5).any(0))[0].max()
    return 300.0 + (xb - GAP - xv)
T_REL, KEY_S = 0.50, 0.85
G_ACC = 2600.0

VIS_X = None
def _fore(t):
    u = sm((t - 0.10) / 0.36) * (1 - sm((t - 0.92) / 0.40))
    w = sm((t - 0.18) / 0.30) * (1 - sm((t - 0.86) / 0.36))      # the forearm follows the upper arm (overlap)
    return (ARM_OUT[0] * u, ARM_OUT[1] * w + 8 * (u - w))

def _lean(t): return LEAN_OUT * sm((t - 0.10) / 0.36) * (1 - sm((t - 0.92) / 0.40))

def i4_key(t):
    """key state: hanging from the hand by its bow, then released at T_REL on a parabola to the folded skirt."""
    _, hand = visitor_draw(np.zeros((H, W, 3), np.float32), VIS_X, VIS_Y, VIS_SC, _fore(min(t, T_REL)), _lean(min(t, T_REL)))
    x, y, s = coat_place(I4_V)
    _, kp, _ = RB.draped_coat(np.zeros((H, W, 3), np.float32), x, y, s, shadow=False)
    _, h_rel = visitor_draw(np.zeros((H, W, 3), np.float32), VIS_X, VIS_Y, VIS_SC, _fore(T_REL), _lean(T_REL))
    land = (h_rel[0] + 6, kp[1] + 4)                 # straight down from the hand onto the near half of the skirt
    if t < T_REL:
        sw = 10 * math.sin(2 * math.pi * 2.2 * t) * math.exp(-1.5 * t)
        return hand[0], hand[1] + 4, 180 + sw, 'hang', None
    # ballistic from the release point (bow at the hand) to the landing point; time to fall from height
    hx, hy = hand[0], hand[1] + 4
    dy = land[1] - hy
    tf = math.sqrt(2 * max(dy, 1.0) / G_ACC)
    u = t - T_REL
    if u < tf:
        vx = (land[0] - hx) / tf
        return hx + vx * u, hy + 0.5 * G_ACC * u * u, 180 + (70 - 180) * (u / tf) - 40 * math.sin(math.pi * u / tf), 'fall', tf
    v = u - tf                                    # landed: rocks on the cloth, damped, then lies
    return land[0], land[1], 70 + 14 * math.exp(-v / 0.08) * math.cos(2 * math.pi * 6 * v), 'lie', tf

def I4(t, sil=False):
    v = I4_V
    fr = B.wide_bg(v) if not sil else np.ones((H, W, 3), np.float32)
    fr = B.draw_bench(fr, v, sil=sil)
    x, y, s = coat_place(v)
    fr, kp, L = RB.draped_coat(fr, x, y, s, sil=sil)
    if not sil: fr = B.shadow(fr, VIS_X, VIS_Y + 2, 46, 8)
    fr, hand = visitor_draw(fr, VIS_X, VIS_Y, VIS_SC, _fore(t), lean=_lean(t), sil=sil)
    kx, ky, ang, st, _ = i4_key(t)
    if st == 'hang':
        fr = S.draw_key(fr, kx, ky, ang, kp=(KEY.shape[1] / 2, KEY.shape[0] * 0.80), s=KEY_S, sil=sil)
    else:
        if st == 'lie' and not sil: fr = B.shadow(fr, kx + 3, ky + 4, 14, 3.5, 0.6)
        fr = S.draw_key(fr, kx, ky, ang, s=KEY_S, sil=sil)
    return fr

VIS_X = _auto_x()

# ------------------------------------------------------------------ the conductor without his coat (II.2)
_tor = PIECES['torso']
_g_u = S.PZ['g_under']
_rows = np.arange(900)[:, None]
_body = S.PZ['torso_a'].astype(np.float32)
_narrow = cv2.warpAffine(np.dstack([_g_u, _body]).astype(np.float32), SX((160, 0), 0.70)[:2], (312, 900),
                         flags=cv2.INTER_LINEAR, borderValue=0)
_keep_head = (_rows < 168).astype(np.float32)
_ga = _g_u * _keep_head + _narrow[..., 0] * (1 - _keep_head)
_aa = _body * _keep_head + _narrow[..., 1] * (1 - _keep_head)
SUIT = {
    'torso': RB.rgba(S.mono(_ga, 0.62) * (1 - 0.0), _aa),
    'sleeve': RB.rgba(S.mono(S.G, 0.55), S.PZ['sleeve_a'] * np.clip((470 - _rows) / 12, 0, 1)),   # jacket sleeve
    'forearm': RB.rgba(S.mono(S.G, 0.9), S.PZ['fore_a']),
    'thighN': PIECES['thighN'], 'thighF': PIECES['thighF'], 'shinN': PIECES['shinN'], 'shinF': PIECES['shinF'],
}
SUIT_SIL = {k: RB.rgba(np.zeros_like(v[..., :3]), v[..., 3]) for k, v in SUIT.items()}
SUIT_ORDER = ['thighF', 'shinF', 'sleeve', 'thighN', 'shinN', 'torso', 'forearm']

def mirror_mats(M, x):
    Mm = T(x, 0) @ np.diag([-1.0, 1.0, 1.0]) @ T(-x, 0)
    return {k: Mm @ v for k, v in M.items()}

def suit_draw(fr, M, sil=False, alpha=1.0):
    P = SUIT_SIL if sil else SUIT
    for k in SUIT_ORDER:
        p = P[k]
        if alpha < 1: p = np.dstack([p[..., :3], p[..., 3] * alpha])
        fr = paint(fr, p, M[k])
    return fr

II2_V = B.View(1.45, (640.0, 520.0))
MAN_S = 0.40 * 1.45 * 0.86
MAN_Y = 236.0                          # hip (root pivot) screen row when standing
HAND_PT = (150.0, 240.0)               # fingers on the forearm piece (piece coords)
REACH_A = -100.0                        # II.2 reach pose: the forearm swung out from the elbow toward the bench
                                       # (declared extension of the runner's forearm limit [-30, 22] for this beat)
T_GRAB = 0.66
STAND_X = 318.0

BACK = 130.0                           # he steps back from the bench with the coat (clear of the bench plane)
def man_root(t):
    """walk in from off-screen left to the bench's left end (0-0.5); reach, grab (0.66); step back with the coat
    (0.70-1.00); coat on (1.00-1.20); walk off to the left (1.20-1.5)."""
    x = -140 + (STAND_X + 140) * sm(t / 0.50) - BACK * sm((t - 0.70) / 0.30) - 90 * sm((t - 1.20) / 0.40)
    walking = t < 0.52 or 0.70 < t < 1.0 or t > 1.22
    lean = 6 * sm((t - 0.46) / 0.18) * (1 - sm((t - 0.70) / 0.20))
    return x, MAN_Y + (2.5 * abs(math.sin(2 * math.pi * 1.4 * t)) if walking else 0), lean, walking

def man_mats(t):
    x, y, lean, walking = man_root(t)
    pose, _ = S.walk_pose(t * 1.4, 1.0)
    amp = 1.0 if t < 0.50 else (0.6 if 0.70 < t < 1.0 else (1.0 if t > 1.22 else 0.0))
    amp_s = sm((0.58 - t) / 0.08) if 0.5 <= t < 0.70 else amp          # legs settle, then step again
    pose = {j: v * amp_s for j, v in pose.items()}
    M = RUN.mats(x, y, MAN_S, lean, pose)
    reach = sm((t - 0.44) / 0.20) * (1 - sm((t - 0.78) / 0.22))
    a = pose.get('forearm', 0) * (1 - reach) + REACH_A * reach
    M['forearm'] = M['torso'] @ R(S.JN['forearm']['pivot'], a)
    return M, x                                      # not mirrored: his right forearm is on the bench side

def _solve_stand():
    global STAND_X
    x, y, s0 = coat_place(II2_V)
    for _ in range(3):
        M, _ = man_mats(T_GRAB)
        STAND_X += (x - 2) - tp(M['forearm'], HAND_PT)[0]
_solve_stand()

def II2(t, sil=False):
    v = II2_V
    fr = B.wide_bg(v) if not sil else np.ones((H, W, 3), np.float32)
    fr = B.draw_bench(fr, v, sil=sil)
    x, y, s0 = coat_place(v)
    M, mx = man_mats(t)
    hand = tp(M['forearm'], HAND_PT)
    T_ON0, T_ON1 = 0.98, 1.20
    k = int(t * FPS)
    if t < T_GRAB:                                   # coat on the bench, untouched
        fr, kp, L = RB.draped_coat(fr, x, y, s0, sil=sil)
        fr = suit_draw(fr, M, sil=sil)
    elif t < T_ON0:                                  # lifted by the collar, skirt opening, glint in the fold
        u = sm((t - T_GRAB) / (T_ON0 - T_GRAB))
        s = s0 + (MAN_S - s0) * u
        g = sm((t - T_GRAB) / 0.08)                  # the collar comes up into the closed hand
        cx, cy = x + (hand[0] - x) * g, y + (hand[1] + 6 - y) * g
        glint = 1.0 if 17 <= k < 23 else 0.0
        fr = suit_draw(fr, M, sil=sil)
        fr, kp, L = RB.draped_coat(fr, cx, cy, s, open_=u, sil=sil, glint=glint, shadow=False, tilt=-6 + 16 * u)
        if glint and not sil:
            kx, ky = tp(L, (RB.C_CX + 38, RB.FOLD_Y - 6))
            fr = S.draw_key(fr, kx, ky, 75, s=0.55 * s / 0.2, glint=0.7)
        fr = paint(fr, SUIT_SIL['forearm'] if sil else SUIT['forearm'], M['forearm'])     # his hand over the collar
    else:                                            # swung onto his shoulders, then he wears it (replacement)
        Mr, _ = man_mats(t)
        torso_collar = tp(Mr['torso'], (RB.C_CX, RB.C_TOP))
        u = sm((t - T_ON0) / (T_ON1 - T_ON0))
        if u < 1:
            cx = hand[0] + (torso_collar[0] - hand[0]) * u; cy = hand[1] + 6 + (torso_collar[1] - hand[1] - 6) * u
            fr = suit_draw(fr, Mr, sil=sil)
            fr2, kp, L = RB.draped_coat(fr.copy(), cx, cy, MAN_S, open_=1.0, sil=sil, shadow=False, tilt=10 * (1 - u))
            # mirrored coat as he swings it round (the coat turns to face as he does)
            fr = fr2
        a = sm((t - (T_ON1 - 0.08)) / 0.12)
        if a > 0:
            red = RUN.draw(fr.copy(), Mr, sil=sil)
            fr = fr * (1 - a) + red * a
    return fr

# ------------------------------------------------------------------ II.6: the key's pencilled outline + struck receipt
_ka = (KEY[..., 3] > 0.5).astype(np.uint8)
def chalk_outline(scale):
    big = cv2.resize(_ka, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    big = np.pad(big, 12)
    ring = cv2.dilate(big, np.ones((7, 7), np.uint8)) - cv2.erode(big, np.ones((3, 3), np.uint8))
    rng = np.random.default_rng(6)
    grain = (rng.random(ring.shape) > 0.22).astype(np.float32)         # chalk breaks on the slats' grain
    a = cv2.GaussianBlur(ring.astype(np.float32) * grain, (3, 3), 0) * 0.95
    return RB.rgba(np.ones(a.shape + (3,), np.float32) * S.TRED, np.clip(a, 0, 1))
CHALK = chalk_outline(2.9)            # red grease pencil round where the key lay (handmade mark), key's own size
def _view_on(z, target, p=(112.0, 140.0)):
    v = B.View(z, (700.0, 610.0))
    for _ in range(2):
        sx, sy_ = tp(B.bench_M(v), p)
        v = B.View(z, (v.c[0] + (sx - target[0]) / v.k(), v.c[1] + (sy_ - target[1]) / v.k()))
    return v
II6_C = _view_on(2.6, (300.0, 300.0)).c
def II6(t):
    v = B.View(2.6 + 0.08 * t, (II6_C[0] + 6 * t, II6_C[1]))
    fr = B.wide_bg(v)
    fr = B.draw_bench(fr, v)
    sx, sy_ = tp(B.bench_M(v), (112.0, 140.0))
    h, w = CHALK.shape[:2]
    M = T(sx + 20, sy_ + 4) @ R((0, 0), 78) @ np.diag([1.0, 0.80, 1.0]) @ T(-w / 2, -h / 2)   # lying on the seat, foreshortened
    fr = paint(fr, CHALK, M)
    kk = int((t - 0.2) / 0.085) + 1 if t >= 0.2 else 0
    img = EB.RECEIPT['0_plain'] if kk == 0 else EB.STRIKE[min(kk, 7) - 1]
    _, Mr = EB.place(fr.copy(), img, 700, 170, 0.62, -3.0)
    fr = EB.drop_shadow(fr, Mr, (600, 340), 0.5, (10, 14), 9)
    fr, _ = EB.place(fr, img, 700, 170, 0.62, -3.0)
    return fr

# ------------------------------------------------------------------ III.4: nearer crossing
def III4(t, sil=False):
    pan = 160 * t
    v = B.View(1.0)
    fr = B.wide_bg(v, pan)
    fr = B.draw_bench(fr, B.View(1.0, (560 + pan / 0.85, 420)))
    pose, _ = S.run_pose(t)
    x, y = v.pt((40 + 640 * t, 468), pan, 0.6)
    M = RUN.mats(x, y - 50, 0.275, -8.0, pose)
    return RUN.draw(fr, M)

# ------------------------------------------------------------------ title
def TITLE(t):
    planes = S.run_stage()
    n = 40
    acc = np.zeros((H, W, 3), np.float32)
    c0 = 900 + 40 * t
    for i in range(n):
        cx = c0 + 160 * ((i + 0.5) / n - 0.5)
        fr = np.zeros((H, W, 3), np.float32)
        for p in planes: p.draw(fr, cx, 1200)
        acc += fr
    acc /= n
    lo, hi = 0.03, 0.72                               # one fixed print curve for all 72 frames (no per-frame grade)
    x = np.clip((acc - lo) / (hi - lo), 0, 1)
    return x * x * (3 - 2 * x) * 0.5 + x * 0.5

CLIPS = {'I4_banc_E3': (I4, 4), 'II2_manteau_E3': (II2, 6), 'II6_cle_E3': (II6, 1), 'III4_manteau_E3': (III4, 6),
         'TITLE_E3': (TITLE, 1),
         'I1_manteau_E3': (B.I1, 1), 'I2_cloche_E3': (B.I2, 4), 'I5_recu_E3': (B.I5, 6), 'I6_porte_E3': (B.I6, 4)}
NFR = {'TITLE_E3': 72}

def frame(name, k):
    fn, n = CLIPS[name]
    t = (k + 0.5) / FPS
    return S.integrate(fn, t, n, 0.5) if n > 1 else fn(t)

def render(name):
    w = S.Writer(os.path.join(OUT, name + '.mp4'))
    nf = NFR.get(name, 36)
    for k in range(nf):
        img = S.to_img(frame(name, k)); w.add(img)
        if k == nf // 2: img.save(os.path.join(STILLS, name + '_mid.png'))
    w.close()

def sil_checks():
    """silhouette check (SCION 2): every piece black on white at the reading frames; and a gap measure."""
    out = {}
    tiles = []
    for name, fn, ts in (('I4', I4, (0.30, 0.50, 0.60, 0.75)), ('II2', II2, (0.30, 0.62, 0.92, 1.10, 1.35))):
        for t in ts:
            a = fn(t, sil=True)
            img = S.to_img(a); img.save(os.path.join(CHECKS, f'sil_{name}_{t:.2f}.png'))
            tiles.append(img.resize((320, 180)))
            m = a.mean(-1) < 0.5
            n, lab = cv2.connectedComponents(m.astype(np.uint8))
            out[f'{name}@{t:.2f}'] = dict(components=int(n - 1))
    sheet = Image.new('RGB', (320 * 3, 180 * 3), 'white')
    for i, tl in enumerate(tiles): sheet.paste(tl, ((i % 3) * 320, (i // 3) * 180))
    sheet.save(os.path.join(CHECKS, 'sil_board_E3.png'))
    # gap between the visitor and the bench in I.4 (separate renders of each, all frames)
    gaps = []
    for k in range(36):
        t = (k + 0.5) / FPS
        fv, _ = visitor_draw(np.ones((H, W, 3), np.float32), VIS_X, VIS_Y, VIS_SC, 0.0, sil=True)
        fb = B.draw_bench(np.ones((H, W, 3), np.float32), I4_V, sil=True)
        mv = fv.mean(-1) < 0.5; mb = fb.mean(-1) < 0.5
        xv = np.nonzero(mv.any(0))[0].max(); xb = np.nonzero(mb.any(0))[0].min()
        gaps.append(int(xb - xv))
    out['I4_body_to_bench_gap_px_min'] = min(gaps)
    json.dump(out, open(os.path.join(CHECKS, 'sil_E3.json'), 'w'), indent=1)
    return out

if __name__ == '__main__':
    names = sys.argv[1:] or list(CLIPS)
    for nm in names:
        if nm == 'sil':
            print(json.dumps(sil_checks(), indent=1)); continue
        render(nm); print('rendered', nm, flush=True)
