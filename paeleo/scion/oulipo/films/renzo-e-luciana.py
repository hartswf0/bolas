"""Renzo e Luciana · "Pausa delle dodici" (SCION direction 2, Collage al marcatempo).

72.0 s = Version A 0-35 (12:00-12:07) + handmade slate 35-37 + Version B 37-72 (the late bell).
Every photographic piece is a real Library of Congress FSA/OWI negative (see films/credits/renzo-e-luciana.json):
  wall plate + near pail pile ............ Russell Lee 1941 (LoC 2017789670)
  Luciana (body, head, forearm, apple) ... Marjory Collins 1943 (LoC 2017851428)
  Renzo (body, head) ..................... Arthur S. Siegel 1942 (LoC 2017835701)
  foreman FRONT .......................... Arthur S. Siegel 1943 (LoC 2017851041)
  foreman BACK + CAPOREPARTO doorway ..... Jack Delano 1942 (LoC 2017829778)
SCION techniques: #29 GrabCut pieces (cutout-performance unit), #32 FK rigs keyed on twos, #45 occlusion DAG
(wall < door < foreman < puppets < pail occluder < lid props < paper clock hands), contact shadows from the plate's
upper-left key, 0.6x/1.0x multiplane drift, one WIDE -> 1.35x MEDIUM push per version.
All timing is computed from films/swarm/renzo-e-luciana/rules.json (rules.py); per-frame asserts run in the render.
Grade = per-piece levels/gamma only (no filter, no tint, no faux grain: kit grain is switched off).
Sound = films/swarm/renzo-e-luciana/sound.wav (foraged Commons + Moving Image Archive recordings), added via mix.

  python3 films/renzo-e-luciana.py                 render assets/films/renzo-e-luciana.mp4
  python3 films/renzo-e-luciana.py --stills 3 10   stills -> films/stills/renzo-e-luciana/
  python3 films/renzo-e-luciana.py --compare       swarm/renzo-e-luciana/aesthetic-compare.jpg
"""
import os, sys, json, math, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit
SW_DIR = os.path.join(HERE, 'swarm', 'renzo-e-luciana')
sys.path.insert(0, SW_DIR)
import rules as R                                     # clock, schedules, cue times and the frame asserts

SRC = os.path.join(HERE, 'sources', 'renzo-e-luciana')
PC = SRC + '/cutout-performance/pieces'
C2 = SW_DIR + '/test-shot-build/cache2'
HI = SRC + '/test-shot/r2/hi'
SLATE_DIR = SRC + '/rule-modeler/slate'
FPS = 24
r2 = json.load(open(C2 + '/rig.json')); r3 = json.load(open(PC + '/pieces.json'))['pieces']


# ------------------------------------------------------------------ pieces (#29 output, graded per piece) ---
def lv(g, lo, hi, gamma): return np.clip((g - lo) / (hi - lo), 0, 1) ** gamma * 255
def load(path, lo=0, hi=255, gamma=1.0):
    a = np.asarray(Image.open(path)).astype(np.float32); return np.dstack([lv(a[..., 0], lo, hi, gamma), a[..., 3] / 255.0])
PV = {k: v['pivots'] for k, v in r2.items()}; PV.update({k: v['pivots'] for k, v in r3.items()})
P = {'re_body': load(C2 + '/re_body.png', 22, 200, 1.08), 're_head': load(C2 + '/re_head.png', 22, 226, 1.1),
     'door': load(C2 + '/door_empty.png', 18, 236, 1.0), 'foreman': load(C2 + '/foreman.png', 18, 236, 1.0),
     'pails': load(C2 + '/pails.png', 40, 215, 0.8),
     'lu_body': load(PC + '/lu_body.png', 12, 200, .85), 'lu_head': load(PC + '/lu_head.png', 10, 214, .92),
     'lu_arm': load(PC + '/lu_arm.png', 10, 214, .92), 'apple': load(PC + '/apple.png', 10, 214, .92),
     'fm_front': load(PC + '/foreman_front.png', 20, 228, .95)}
# foreman FRONT split at the collar into body + head on a neck pin (his pan across the floor is a head turn on the pin)
_ff = P['fm_front']; _nk = PV['foreman_front']['neck']
_yy = np.arange(_ff.shape[0])[:, None].astype(np.float32)
_cut = np.clip((_yy - (_nk[1] + 6)) / 6.0, 0, 1)                    # soft 6 px collar seam
P['fm_head'] = np.dstack([_ff[..., 0], _ff[..., 1] * (1 - _cut)])
P['fm_body'] = np.dstack([_ff[..., 0], _ff[..., 1] * _cut])

plate = np.asarray(Image.open(HI + '/plate_8c01492.png').convert('L')).astype(np.float32)
SH, SW = plate.shape                                                 # 1087 x 1933 (native sampling)
CX, CY, CR = 604.5 * SW / 1296, 89.5 * SH / 729, 45.7 * SW / 1296
ring = np.zeros(plate.shape, np.uint8); cv2.circle(ring, (int(CX), int(CY)), int(CR * .62), 255, -1)
hands = cv2.dilate(((plate < 110) & (ring > 0)).astype(np.uint8) * 255, np.ones((3, 3), np.uint8))
plate = cv2.inpaint(plate.astype(np.uint8), hands, 3, cv2.INPAINT_TELEA).astype(np.float32)   # photographed hands lifted off
plate = lv(plate, 14, 218, 0.5)
plate = cv2.GaussianBlur(plate, (0, 0), 1.1)                         # the wall is behind the focal plane
# time cards: a real card cut from the plate's own rack (4th column, top slot), dropped into empty slots at each punch
CARD = plate[89:103, 1203:1233].copy()
CARD_SLOT = {('A', 'renzo'): 1, ('A', 'luciana'): 2, ('B', 'renzo'): 1, ('B', 'luciana'): 2}
def drop_cards(pl, ver, tau):
    for (tt, who, _) in R.CARDS[ver]:
        n = CARD_SLOT[(ver, who)]; y = 89 + 14 * n
        if tau >= tt + 1 / 24.0 - 1e-9: pl[y:y + 14, 1203:1233] = CARD
        elif tau >= tt - 1e-9: pl[y - 5:y + 9, 1203:1233] = CARD     # the frame of the punch: card half-way into the slot
sign = Image.new('L', (190, 32), 214); sd = ImageDraw.Draw(sign)
sd.text((11, 5), 'CAPOREPARTO', font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 18), fill=34)
sign = np.asarray(sign.rotate(-1.2, expand=True, resample=Image.BICUBIC, fillcolor=0)).astype(np.float32)
SIGN = np.dstack([sign, cv2.GaussianBlur((sign > 0).astype(np.float32), (0, 0), .6)])


# ------------------------------------------------------------------ geometry + FK (#32) ---
def mat(pivot, world, ang, s):
    M = cv2.getRotationMatrix2D((float(pivot[0]), float(pivot[1])), ang, s); M[:, 2] += np.array(world, float) - np.array(pivot, float); return M
def ap(M, p): return M @ np.array([p[0], p[1], 1.0])
def bite(piece, centre, r, seed):
    p = piece.copy(); h, w = p.shape[:2]; Y, X = np.mgrid[0:h, 0:w]
    ang = np.arctan2(Y - centre[1], X - centre[0]); rng = np.random.default_rng(seed)
    rr = r * (1 + .12 * np.sin(ang * 5 + rng.uniform(0, 6))); dist = np.hypot(X - centre[0], Y - centre[1])
    cut = dist < rr; rim = (dist >= rr) & (dist < rr + 3.0) & (p[..., 1] > .5)
    p[cut, 1] = 0; p[rim, 0] = np.maximum(p[rim, 0], 196)            # scissor-cut bite; rim = the print's pale flesh
    return p
A0 = P['apple']; A1 = bite(A0, (138, 40), 22, 1); A2 = bite(A1, (8, 52), 20, 2); A3 = bite(A2, (128, 92), 21, 3)
B1 = bite(A0, (40, 20), 22, 7); B2 = bite(B1, (8, 52), 20, 8)
APPLES = {'A': [A0, A1, A2, A3], 'B': [A0, B1, B2]}

D_XY = np.array([367.0, -30.0])                                      # doorway just left of the clock
F_FEET = D_XY + np.array(PV['foreman']['feet']) + np.array(r2['foreman']['crop'][:2]) - np.array(r2['door']['crop'][:2])
FF_S = .54
PS, P_XY = .93, np.array([470.0, 318.0])                             # near pail pile (occluder)
SL, SR, SA = .44, .70, .44
L_HIP0 = np.array([892.0, 601.0])
def lu_fk(dx, dy, hip, neck, elbow):
    lb = PV['lu_body']; Mb = mat(lb['hip'], L_HIP0 + [dx, dy], hip, SL)
    Mh = mat(PV['lu_head']['neck'], ap(Mb, lb['neck']), hip + neck, SL)
    Ma = mat(PV['lu_arm']['elbow'], ap(Mb, lb['elbow']), hip + elbow, SL)
    Mp = mat(PV['apple']['grip'], ap(Ma, PV['lu_arm']['grip']), hip + elbow, SA)   # apple rigid in her fingers
    return Mb, Mh, Ma, Mp
FEED, L_FEED_HIP = -16.0, -3.0
APPLE_FEED_RIGHT = ap(lu_fk(0, 0, L_FEED_HIP, 0, FEED)[3], (PV['apple']['c'][0] + 64, PV['apple']['c'][1] - 6))
def re_fk(root, hip, head):
    pb, ph = PV['re_body'], PV['re_head']; Mb = mat(pb['hip'], root, hip, SR)
    Mh = mat(ph['neck'], ap(Mb, pb['neck']), hip + head, SR); return Mb, Mh, ap(Mh, ph['mouth'])
R_BITE_HEAD, R_BITE_HIP = 9.0, 3.0
R_ROOT = APPLE_FEED_RIGHT - re_fk(np.zeros(2), R_BITE_HIP, R_BITE_HEAD)[2] + [6, 0]   # FK solve: mouth meets the apple
_pa = np.asarray(Image.open(C2 + '/pails.png'))[..., 3] > 128
def pile_top(x):
    c = np.nonzero(_pa[:, int(np.clip((x - P_XY[0]) / PS, 0, _pa.shape[1] - 1))])[0]; return P_XY[1] + (c[0] if len(c) else 0) * PS
_rel = ap(lu_fk(0, 0, -4.5, 0, -34)[3], PV['apple']['c'])
LID_A = np.array([_rel[0], pile_top(_rel[0]) - 22])                  # his pail lid (A: she sets the core here at 14.0)
L_REACH = (-1.0, -14.0)                                              # (hip, elbow) of her reach to her own lid
_relb = ap(lu_fk(0, 0, L_REACH[0], 0, L_REACH[1])[3], PV['apple']['c'])
LID_B = np.array([_relb[0], pile_top(_relb[0]) - 22])                # her pail lid (B: he leaves the bitten apple here)
# Renzo has no free forearm in the Siegel negative: in B "the apple in his hand" is the apple on HIS lid (LID_A, where the A
# core lies), his hand hidden behind the pile edge; his bite is a lean-in on the root/neck pins (FK pose checked: mouth meets
# the apple's top-left, where the B1 bite is cut).
R_EAT = (38.0, 2.0, 8.0)                                             # (root dy, hip, head)

# ------------------------------------------------------------------ keys (film seconds; eased; drawings on twos) ---
def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def K(kf, t):
    if t <= kf[0][0]: return kf[0][1]
    for (ta, va), (tb, vb) in zip(kf, kf[1:]):
        if t <= tb: return va + (vb - va) * ease((t - ta) / (tb - ta)) if tb > ta else vb
    return kf[-1][1]
def heads_keys(ver, who, amap, t_off, turn=.16, over=1.5, until=None):
    """Head substitution times from rules.HEADS -> eased turns on the neck pin with a small overshoot (weight)."""
    out = []; prev = None
    for tau, s in R.HEADS[ver][who]:
        t = tau + t_off
        if until and not (until[0] <= t < until[1]): continue
        a = amap.get(s)
        if a is None: continue
        if prev is None: out.append((t, a)); prev = a; continue
        sgn = 1 if a > prev else -1
        out += [(t, prev), (t + turn, a + sgn * over), (t + turn + .08, a)]; prev = a
    return out
def merge(*lists):
    k = sorted([x for l in lists for x in l], key=lambda x: x[0]); out = []
    for x in k:
        if out and abs(out[-1][0] - x[0]) < 1e-6: out[-1] = x
        else: out.append(x)
    return out
R_HEAD = {'walk': -5, 'clock': -23, 'door': -12, 'her': 3, 'forward': R_BITE_HEAD, 'empty_place': 15, 'lid': 17}
L_NECK = {'walk': 0, 'pail': -6, 'door': 6, 'him': 0, 'clock': 8}
OPEN_R = (300.0, -120.0); OPEN_L = (-62.0, 35.0)                     # seated at the open ends of the pile
RB = R_BITE_HEAD
KEYS = {'A': {}, 'B': {}}
A = KEYS['A']
A['R.dx'] = [(0, 900), (.4, 900), (2.0, OPEN_R[0]), (5.0, OPEN_R[0]), (6.0, 0), (14.3, 0), (14.34, -3), (15.0, -90), (15.8, -90), (17.0, 900)]
A['R.dy'] = [(0, OPEN_R[1]), (5.0, OPEN_R[1]), (6.0, 0), (14.3, 0), (14.34, -5), (15.0, -150), (15.8, -150), (17.0, -110)]
A['R.hip'] = [(0, -1), (5.1, -1), (6.5, 1.5), (8.35, R_BITE_HIP + .6), (8.45, R_BITE_HIP), (9.1, R_BITE_HIP), (9.5, 1.0),
              (12.65, 1.0), (12.9, R_BITE_HIP), (13.35, R_BITE_HIP), (13.75, 1.0), (14.3, 0), (15.0, -3)]
A['R.head'] = merge(heads_keys('A', 'renzo', R_HEAD, 0, until=(0, 5.5)),
                    [(5.5, -12), (5.6, 4), (5.75, 2.5), (6.6, 2.5), (7.0, -24), (7.1, -23), (8.0, -23), (8.4, RB + 1.5), (8.5, RB), (9.1, RB),
                     (9.35, -26), (9.45, -23), (10.6, -23), (10.8, -6), (11.3, -6), (11.5, -23), (12.6, -23), (12.9, RB + 1.2), (13.0, RB),
                     (13.35, RB), (13.6, -25), (13.7, -23), (13.9, -23), (14.05, 18.5), (14.13, 17), (14.3, 17), (14.45, -5)],
                    heads_keys('A', 'renzo', R_HEAD, 0, until=(14.9, 99)))
A['L.dx'] = [(0, -900), (1.0, -900), (2.6, OPEN_L[0]), (5.0, OPEN_L[0]), (6.9, -6), (7.0, 0), (19.0, 0), (19.6, -40), (20.6, -40), (21.8, -900)]
A['L.dy'] = [(0, OPEN_L[1]), (5.0, OPEN_L[1]), (6.9, 3), (7.0, 0), (19.0, 0), (19.6, -60), (20.6, -60), (21.8, -40)]
A['L.hip'] = [(0, 2), (5.1, 2), (6.0, -1), (6.9, -2), (8.3, L_FEED_HIP), (10.4, L_FEED_HIP), (11.0, 1.5), (11.6, -2), (12.45, L_FEED_HIP),
              (13.4, -2), (14.0, -4.5), (14.6, 0), (19.0, 0), (19.4, -3), (20.6, -3)]
A['L.neck'] = merge(heads_keys('A', 'luciana', L_NECK, 0, until=(0, 5.7)),
                    [(5.6, 6), (5.8, 0), (6.9, 0), (8.2, -2.5), (9.4, 1.5), (10.4, -1), (11.0, 3.5), (11.5, 3.5), (12.2, -2), (13.4, -1.5), (14.6, 1), (15.0, 1)],
                    heads_keys('A', 'luciana', L_NECK, 0, until=(14.9, 99)))
A['L.elbow'] = [(0, -30), (2.6, -10), (2.8, -36), (2.9, -36), (3.4, -2), (3.5, -3), (6.9, -3), (7.4, -1), (8.15, FEED - 1.5), (8.3, FEED),
                (10.4, FEED), (10.95, 1.2), (11.0, 0), (11.5, 0), (12.3, FEED - 1.2), (12.45, FEED), (13.45, FEED), (13.95, -34), (14.0, -34),
                (14.6, -4), (15.0, -3), (15.5, -12), (16.0, -5), (16.5, -12), (17.0, -5), (17.8, -32), (18.4, -32), (18.6, -28), (19.0, -30)]
B = KEYS['B']                                                         # t = 37 + tau
B['R.dx'] = [(37, 900), (37.4, 900), (39.0, OPEN_R[0]), (42.0, OPEN_R[0]), (43.0, 0), (51.3, 0), (52.0, -90), (52.4, -90),
             (52.7, -150), (53.0, -150), (53.5, 900)]
B['R.dy'] = [(37, OPEN_R[1]), (42.0, OPEN_R[1]), (43.0, 0), (43.25, 14), (43.7, 0), (50.7, 0), (50.95, R_EAT[0]), (51.15, R_EAT[0]),
             (51.3, 30), (52.0, -150), (52.4, -150), (52.7, -105), (53.0, -105), (53.5, -110)]
B['R.hip'] = [(37, -1), (43.0, 1), (45.2, 4), (46.0, 1), (50.75, 1), (50.95, R_EAT[1]), (51.2, R_EAT[1]), (51.6, 0), (52.4, 0),
              (52.75, 8), (53.0, 8), (53.2, -3)]
B['R.head'] = merge(heads_keys('B', 'renzo', R_HEAD, 37, until=(37, 50.8)),
                    [(50.8, R_HEAD['empty_place']), (50.95, R_EAT[2] + 1.5), (51.0, R_EAT[2]), (51.2, R_EAT[2]), (51.35, -5)],
                    heads_keys('B', 'renzo', R_HEAD, 37, until=(51.9, 99)),
                    [(52.75, 14), (53.0, 14), (53.15, -5)])
B['L.dx'] = [(37, -900), (52.0, -900), (52.6, -380), (53.5, 0), (56.2, 0), (56.8, OPEN_L[0]), (71.3, OPEN_L[0]), (71.5, -40), (72, -40)]
B['L.dy'] = [(37, 30), (52.6, 30), (53.5, 0), (56.2, 0), (56.8, OPEN_L[1]), (71.3, OPEN_L[1]), (71.5, -60), (72, -60)]
B['L.hip'] = [(37, 3), (52.6, 3), (53.5, 0), (53.9, L_REACH[0]), (54.3, L_REACH[0]), (54.9, 1.5), (55.4, 1.5), (55.8, 0), (57.9, 0),
              (58.2, 1.5), (59.0, 1.5), (59.4, 0), (71.3, 0), (71.5, -3)]
B['L.neck'] = merge(heads_keys('B', 'luciana', L_NECK, 37, until=(52, 54.95)),
                    [(54.95, -4), (55.0, 3.5), (55.5, 3.5)],
                    heads_keys('B', 'luciana', L_NECK, 37, until=(55.5, 57.9)),
                    [(57.9, 6), (58.1, 3.5), (59.5, 3.5)],
                    heads_keys('B', 'luciana', L_NECK, 37, until=(59.9, 99)))
B['L.elbow'] = [(37, -30), (53.5, -30), (54.0, L_REACH[1]), (54.3, L_REACH[1]), (54.9, 1.2), (55.0, 0), (55.5, 0), (55.9, -6),
                (57.9, -6), (58.2, 0), (59.5, 0), (60.0, -6), (62.0, -4), (64.0, -7), (66.0, -4), (68.5, -7), (71.0, -5)]
BITES = {v: [(b['t'], b['who']) for b in json.load(open(SW_DIR + '/rules.json'))['bites'][v]] for v in 'AB'}
TURN = {'A': (5.0, 20.0), 'B': (42.0, 57.0)}
FM_HEAD = {'front_pan_left': 7.0, 'front_pan_centre': 0.0, 'front_pan_right': -7.0, 'front_on_luciana': -4.0}
def fm_head_keys(ver):
    off = 0 if ver == 'A' else 37; out = []; prev = None
    for tau, s in R.HEADS[ver]['foreman']:
        if s not in FM_HEAD: continue
        t = tau + off; a = FM_HEAD[s]
        out += [(t, prev), (t + .5, a)] if prev is not None else [(t, a)]; prev = a
    return out
FMK = {v: fm_head_keys(v) for v in 'AB'}
FM_STEP = {'A': [(20, 0)], 'B': [(57.0, 0), (57.5, 0), (58.3, 34)]}        # B: one step out of the doorway, gaze held on her

def q(t): return math.floor(t * 12 + 1e-6) / 12                    # drawings on twos (12/s)
def ver_of(t):
    if t < 35.0: return 'A', t, t
    if t < 37.0: return 'slate', t, t - 35.0
    return 'B', t, t - 37.0

def apple_state(ver, tq):
    """(piece index, where): from rules.APPLE (+ bite frames)."""
    off = 0 if ver == 'A' else 37
    n = sum(1 for (bt, _) in BITES[ver] if tq >= bt - 1e-9)
    at = None
    for tau, _s, a in R.APPLE[ver]:
        if tau + off <= tq + 1e-9: at = a
    if ver == 'A' and at == 'R_hand': at = 'L_wrist'                  # no free forearm for Renzo: she keeps it until she lids it
    return n, at

def state(t):
    ver, tf, tau = ver_of(t)
    tq = q(tf); k = KEYS[ver]
    s = {n: K(k[n], tq) for n in k}
    s['ver'] = ver; s['tq'] = tq; s['tau'] = tau
    fa = R.facing_at(R.fixture_minutes(tau))
    s['foreman'] = 'back' if fa == 'OFFICE' else 'front'
    s['fm_head'] = K(FMK[ver], tq) if FMK[ver] else 0.0
    s['fm_dx'] = K(FM_STEP[ver], tq)
    s['apple_n'], s['apple_at'] = apple_state(ver, tq)
    l_corner = abs(s['L.dx']) < 2 and abs(s['L.dy']) < 2
    r_corner = abs(s['R.dx']) < 2 and s['R.dy'] > -2
    s['meet_drawn'] = (ver == 'A' and l_corner and r_corner and s['L.dx'] > -880)
    s['L_on'] = s['L.dx'] > -880; s['R_on'] = s['R.dx'] < 880
    return s

# ------------------------------------------------------------------ camera (WIDE 1296 window -> MEDIUM 960 window = 1.35x) ---
WIDE = (360.0, 20.0, 1296.0); MED = (600.0, 48.0, 960.0)
def cam_u(tau):
    c = R.camera_at(tau)
    if c['state'] == 'WIDE': return 0.0
    if c['state'] == 'MEDIUM': return 1.0
    return c['u'] if c['state'] == 'PUSH' else 1.0 - c['u']
def window(u, drift, par=1.0):
    u = u * par
    x0 = WIDE[0] + (MED[0] - WIDE[0]) * u; y0 = WIDE[1] + (MED[1] - WIDE[1]) * u
    w = 1.0 / (1.0 / WIDE[2] + (1.0 / MED[2] - 1.0 / WIDE[2]) * u)
    return x0 + drift * par, y0, w
def drift_of(tau): return 16.0 * math.sin(2 * math.pi * tau / 35.0)  # slow lateral drift, same in A and B

def view(stage_img, win):
    x0, y0, w = win; h = w * 540 / 960
    M = np.array([[960 / w, 0, -x0 * 960 / w], [0, 540 / h, -y0 * 540 / h]])
    return cv2.warpAffine(stage_img, M, (960, 540), flags=cv2.INTER_AREA if w > 960 else cv2.INTER_LINEAR)

# ------------------------------------------------------------------ compositing (#45) ---
class Comp:
    """Foreground stack in stage coords: premultiplied grey C, coverage A, and a shadow multiplier S falling on the wall."""
    def __init__(self):
        self.C = np.zeros((SH, SW), np.float32); self.A = np.zeros((SH, SW), np.float32); self.S = np.ones((SH, SW), np.float32)
        self.order = []
    def over(self, name, lay, shadow=True, off=(10, 8), blur=10, dark=.30):
        g, a = lay[..., 0], lay[..., 1]
        if shadow:                                 # soft contact shadow down-right (key light upper left)
            sh = 1 - cv2.GaussianBlur(np.roll(np.roll(a, off[1], 0), off[0], 1), (0, 0), blur) * dark
            self.C *= sh; self.S *= sh
        self.C = self.C * (1 - a) + g * a; self.A = self.A * (1 - a) + a
        self.order.append(name)
def W(piece, M, interp=cv2.INTER_AREA):
    return cv2.warpAffine(piece, M, (SW, SH), flags=interp, borderValue=(0, 0))
DOOR_LAY = W(P['door'], mat((0, 0), D_XY + [0, 4], 0, 1.0))
PAILS_LAY = W(P['pails'], mat((0, 0), P_XY, 0, PS))
SIGN_LAY = W(SIGN, mat((0, 0), (612, 54), 0, 1.0), cv2.INTER_LINEAR)

HS = 4                                                                  # paper hands cut at 4x, reduced to the stage
_HB = (int(CX - CR) - 4, int(CY - CR) - 4, int(2 * CR) + 8)            # (x0, y0, size) of the dial box
def clock_hands(tau):
    md, hd = R.minute_hand_deg(tau), R.hour_hand_deg(tau)
    bx, by, bs = _HB; big = np.zeros((bs * HS, bs * HS), np.float32); ox, oy = (CX - bx) * HS, (CY - by) * HS
    def hand(angdeg, L, w):
        a = math.radians(angdeg - 90); b = a + math.pi / 2; L, w = L * HS, w * HS
        pts = [(ox + w * math.cos(b), oy + w * math.sin(b)), (ox + L * math.cos(a), oy + L * math.sin(a)),
               (ox - w * math.cos(b), oy - w * math.sin(b)), (ox - 8 * HS * math.cos(a), oy - 8 * HS * math.sin(a))]
        cv2.fillPoly(big, [np.round((np.array(pts) + .5 * (HS - 1)) * 8).astype(np.int32)], 1.0, lineType=cv2.LINE_AA, shift=3)
    hand(hd, CR * .48, 4.2); hand(md, CR * .74, 2.8)
    cv2.circle(big, (int(round(ox)), int(round(oy))), 4 * HS, 1.0, -1)
    hl = np.zeros((SH, SW), np.float32); hl[by:by + bs, bx:bx + bs] = cv2.resize(big, (bs, bs), interpolation=cv2.INTER_AREA)
    return hl, md

def measure_minute(hl):
    """Read the drawn minute hand back off the canvas: ink-weighted centroid of the outer ring (beyond the hour hand's reach),
    relative to the arbor -> degrees clockwise from 12."""
    x0, y0 = int(CX - CR), int(CY - CR); sub = hl[y0:int(CY + CR), x0:int(CX + CR)]
    yy, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
    dx = xx + x0 - CX; dy = yy + y0 - CY; wgt = sub * (np.hypot(dx, dy) > CR * .55)
    if wgt.sum() < 1: return None
    return math.degrees(math.atan2((dx * wgt).sum(), -(dy * wgt).sum())) % 360

_slate_cache = {}
def slate(k):
    if k not in _slate_cache:
        _slate_cache.clear(); _slate_cache[k] = np.asarray(Image.open(f'{SLATE_DIR}/slate_{k:04d}.png').convert('L')).astype(np.float32)
    return _slate_cache[k]

ASSERT_LOG = {'frames': 0, 'meet_frames': [], 'layer_checks': 0, 'clock_max_err': 0.0}
CROSS = (52.0, 53.5)
def frame_img(t, check=True):
    k = int(round(t * FPS)); ver, tf, tau = ver_of(t)
    if ver == 'slate':
        if check: R.assert_frame(k, None, meet_drawn=False); ASSERT_LOG['frames'] += 1
        return slate(k)
    S = state(t); tq = S['tq']
    u = cam_u(tau); dr = drift_of(tau)
    pl = plate.copy(); drop_cards(pl, ver, tau)
    hl, md = clock_hands(tau)
    pl = pl * (1 - cv2.GaussianBlur(np.roll(np.roll(hl, 3, 0), 3, 1), (0, 0), 1.5) * .35)   # paper hands' own shadow
    pl = pl * (1 - hl) + 22 * hl
    cp = Comp()
    cp.over('door_frame', DOOR_LAY, off=(6, 5), blur=6, dark=.25)
    cp.over('door_sign', SIGN_LAY, off=(3, 3), blur=2, dark=.3)
    if S['foreman'] == 'back':
        sway = .7 * math.sin(tq * 1.1) + (.35 if (tq % 2.6) < 1.3 else -.2)
        cp.over('foreman', W(P['foreman'], mat(PV['foreman']['feet'], F_FEET, sway, 1.0)), shadow=False)
    else:
        feet = F_FEET + [6 + S['fm_dx'], 0]
        bob = 1.5 * abs(math.sin(tq * math.pi / .6)) if (S['fm_dx'] > .5 and S['fm_dx'] < 33.5) else 0
        Mb = mat(PV['foreman_front']['feet'], feet - [0, bob], 0, FF_S)
        cp.over('foreman', W(P['fm_body'], Mb), off=(5, 3), blur=4, dark=.2)
        Mh = mat(_nk, ap(Mb, _nk), S['fm_head'], FF_S)
        cp.over('foreman', W(P['fm_head'], Mh), shadow=False)
    Mb, Mh, Ma, Mp = lu_fk(S['L.dx'], S['L.dy'], S['L.hip'], S['L.neck'], S['L.elbow'])
    rbob = 6 * abs(math.sin(tq * math.pi / .45)) if (abs(K(KEYS[ver]['R.dx'], tq + .05) - S['R.dx']) > .8) else 0.0
    lbob = 5 * abs(math.sin(tq * math.pi / .5)) if (abs(K(KEYS[ver]['L.dx'], tq + .05) - S['L.dx']) > .8) else 0.0
    if lbob: Mb, Mh, Ma, Mp = lu_fk(S['L.dx'], S['L.dy'] - lbob, S['L.hip'], S['L.neck'], S['L.elbow'])
    crossing = ver == 'B' and CROSS[0] <= tf < CROSS[1]
    if S['L_on']:
        cp.over('luciana_body', W(P['lu_body'], Mb), off=(12, 9), blur=12)
        cp.over('luciana_head', W(P['lu_head'], Mh), off=(10, 8), blur=10)
        if ver == 'B' and tf < 54.0:              # B: her hand is empty and low; she passes wholly behind him
            cp.over('luciana_forearm_low', W(P['lu_arm'], Ma), off=(9, 8), blur=8)
    root = R_ROOT + [S['R.dx'], S['R.dy'] - rbob]
    Rb, Rh, _ = re_fk(root, S['R.hip'], S['R.head'])
    if S['R_on']:
        cp.over('renzo_body', W(P['re_body'], Rb), off=(12, 9), blur=12)
        cp.over('renzo_head', W(P['re_head'], Rh), off=(9, 8), blur=9)
    apc = APPLES[ver][min(S['apple_n'], len(APPLES[ver]) - 1)]
    at = S['apple_at']
    if at == 'L_wrist' and S['L_on']:
        cp.over('apple', W(apc, Mp), off=(7, 6), blur=6, dark=.32)
    if at == 'R_hand' and tq < 43.9:                                 # B 43.5-43.9: up out of his pocket, behind the pile edge
        pos = LID_A + [0, 75 * (1 - ease((tq - 43.5) / .4))]
        cp.over('apple', W(apc, mat(PV['apple']['c'], pos, -8, SA)), off=(7, 6), blur=6, dark=.32)
    if S['L_on'] and not (ver == 'B' and tf < 54.0):
        cp.over('luciana_forearm', W(P['lu_arm'], Ma), off=(9, 8), blur=8)
    cp.over('pail_pile_occluder', PAILS_LAY, off=(12, 10), blur=12, dark=.30)
    if at in ('R_lid', 'L_lid') or (at == 'R_hand' and tq >= 43.9):
        pos = LID_B if at == 'L_lid' else LID_A
        if at == 'R_hand' and tq >= 52.6:                            # his hidden hand slides it along the lids to hers by 53.0
            pos = LID_A + (LID_B - LID_A) * ease((tq - 52.6) / .4)
        cp.over('lid_props', W(apc, mat(PV['apple']['c'], pos, -8, SA)), off=(5, 4), blur=3, dark=.5)
    # ---- per-frame asserts
    if check:
        mm = measure_minute(hl)
        if mm is not None:
            err = abs((mm - md + 180) % 360 - 180); ASSERT_LOG['clock_max_err'] = max(ASSERT_LOG['clock_max_err'], err)
        R.assert_frame(k, minute_deg=mm, meet_drawn=S['meet_drawn'])     # measured hand angle vs the one clock
        order = ['wall_plate'] + [n for n in cp.order if n in R.LAYERS] + ['clock_hands']
        li = [i for i, n in enumerate(cp.order) if n.startswith('luciana')]; ri = [i for i, n in enumerate(cp.order) if n.startswith('renzo')]
        if crossing:                              # rules.LAYER_NOTES['B_crossing']: L wholly behind R
            assert not (li and ri) or max(li) < min(ri), cp.order
        R.assert_layer_order(order)                # rules.LAYERS back-to-front, every frame
        ASSERT_LOG['layer_checks'] += 1; ASSERT_LOG['frames'] += 1
        if S['meet_drawn']: ASSERT_LOG['meet_frames'].append(k)
    # ---- camera: wall plate at 0.6x parallax, everything in front of it at 1.0x
    wf = window(u, dr, 1.0); wp = window(u, dr, 0.6)
    bg = view(pl, wp)
    C, A_, S_ = view(cp.C, wf), view(cp.A, wf), view(cp.S, wf)
    return bg * S_ * (1 - A_) + C

# ------------------------------------------------------------------ film ---
TOTAL = 72.0
film = kit.Film('renzo-e-luciana', seconds=TOTAL)
film.poster_at = 10.0
def pic(t, ink):
    ink._grain = False                                                # no faux grain: the grain is the negatives' own
    g = np.clip(frame_img(t), 0, 255).astype(np.uint8)
    ink.img = Image.fromarray(np.stack([g] * 3, -1))
film.picture(pic)

def wav2(path):
    with wave.open(path) as w:
        n, ch = w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    return x.reshape(-1, ch)
def snd(mix):
    x = wav2(SW_DIR + '/sound.wav')                                  # foraged stems mixed by the sound unit (cues.json)
    mix.add(x[:, 0] / 1.414, 0, pan=-1); mix.add(x[:, 1] / 1.414, 0, pan=1)
film.sound(snd)

# ------------------------------------------------------------------ aesthetic compare ---
def stats(g):
    g = g.astype(np.float32)
    if g.shape[1] != 960: g = cv2.resize(g, (960, int(g.shape[0] * 960 / g.shape[1])), interpolation=cv2.INTER_AREA)
    hp = g - cv2.GaussianBlur(g, (0, 0), 2.0)
    return {'median': float(np.median(g)), 'p5': float(np.percentile(g, 5)), 'p95': float(np.percentile(g, 95)),
            'std': float(g.std()), 'grain_hp_std': float(hp.std())}
def compare(times=(3, 10, 25, 47, 60)):
    refp = os.path.join(HERE, '..', 'assets', 'references', 'calvino.webp')
    ref = Image.open(refp).convert('RGB'); ra = np.asarray(ref).astype(np.float32)
    rs = stats(np.asarray(ref.convert('L'))); rs['chroma'] = float(np.abs(ra - ra.mean(2, keepdims=True)).max(2).mean())
    tiles = [(ref.resize((715, 540)), 'REFERENCE calvino.webp (look target only)', rs)]
    out = {'reference': rs, 'frames': {}}
    for t in times:
        img = film.frame(int(round(t * FPS))); a = np.asarray(img).astype(np.float32)
        s = stats(np.asarray(img.convert('L'))); s['chroma'] = float(np.abs(a - a.mean(2, keepdims=True)).max(2).mean())
        s['pass'] = bool(s['chroma'] <= 2 and 112 <= s['median'] <= 132 and s['p5'] <= 30 and s['p95'] >= 220 and 8 <= s['grain_hp_std'] <= 15)
        out['frames'][str(t)] = s; tiles.append((img, f't = {t} s', s))
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    sheet = Image.new('RGB', (2 * 980, 3 * 600), (248, 248, 248)); d = ImageDraw.Draw(sheet)
    for i, (im, lab, s) in enumerate(tiles):
        x, y = (i % 2) * 980 + 10, (i // 2) * 600 + 10
        sheet.paste(im, (x + (960 - im.width) // 2, y + 28)); d.text((x, y + 2), lab, font=f, fill=(0, 0, 0))
        d.rectangle([x, y + 540, x + 960, y + 568], fill=(0, 0, 0))
        d.text((x + 6, y + 544), f"chroma {s['chroma']:.1f}  median {s['median']:.0f}  p5 {s['p5']:.0f}  p95 {s['p95']:.0f}  std {s['std']:.0f}  grain {s['grain_hp_std']:.1f}"
               + ('' if 'pass' not in s else ('   PASS' if s['pass'] else '   MISS')), font=f, fill=(255, 255, 255))
    sheet.save(SW_DIR + '/aesthetic-compare.jpg', quality=88)
    json.dump(out, open(SW_DIR + '/aesthetic-compare.json', 'w'), indent=1)
    print(json.dumps(out, indent=1))

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--compare':
        compare()
    else:
        film.render()
        if not (len(sys.argv) > 1 and sys.argv[1] == '--stills'):
            ASSERT_LOG['meet_range'] = [min(ASSERT_LOG['meet_frames']), max(ASSERT_LOG['meet_frames'])] if ASSERT_LOG['meet_frames'] else None
            ASSERT_LOG['meet_frames'] = len(ASSERT_LOG['meet_frames'])
            json.dump(ASSERT_LOG, open(SW_DIR + '/render-asserts.json', 'w'), indent=1); print(ASSERT_LOG)
