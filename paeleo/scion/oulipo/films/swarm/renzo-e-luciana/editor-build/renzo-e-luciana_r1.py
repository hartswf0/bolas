"""Renzo e Luciana · "Pausa delle dodici" (SCION direction 2, Collage al marcatempo) — editor repair round 1.

72.0 s = Version A 0-35 (12:00-12:07) + neutral handmade 'B' card 35-37 + Version B 37-72 (the late bell).
Every photographic piece is a real Library of Congress FSA/OWI negative (see films/credits/renzo-e-luciana.json):
  wall plate + near pail pile ............ Russell Lee 1941 (LoC 2017789670)
  Luciana (body, head, forearm, apple) ... Marjory Collins 1943 (LoC 2017851428)
  Renzo (body, head, arm, hands) ......... Arthur S. Siegel 1942 (LoC 2017835701, master TIFF re-fetched at 2x)
  the foreman (one man) .................. Arthur S. Siegel 1943 (LoC 2017851041)
  CAPOREPARTO doorway (office emptied) ... Jack Delano 1942 (LoC 2017829778), lab technician retouched out
The foreman's two states are ONE man: in the doorway watching the floor (FLOOR), or gone back into his office out of sight
behind the left jamb (OFFICE).  Luciana waits at the time clock in his sight; only while the doorway is empty does she go
behind the pails.  SCION techniques: #29 GrabCut pieces, #32 FK rigs (Renzo hip/neck/shoulder/wrist, Luciana hip/neck/elbow,
foreman feet/neck) with IK-solved key poses, keyed on twos, jaw-substitution drawings for chewing; #45 occlusion DAG
(wall < door frame < foreman < left jamb < puppets < pail occluder < lid props < paper clock hands), contact shadows from the
plate's upper-left key, 0.6x/1.0x multiplane drift, one WIDE -> 1.35x MEDIUM push per version.
Timing from films/swarm/renzo-e-luciana/rules.json (rules.py); per-frame asserts run in the render.
Grade = per-piece levels/gamma only (no filter, no tint, no faux grain: kit grain is switched off).
Sound = films/swarm/renzo-e-luciana/sound.wav (Commons recordings, mixed by the sound unit), added via mix.

  python3 films/renzo-e-luciana.py                 render assets/films/renzo-e-luciana.mp4 (+ performance.json ledger)
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
EP = SRC + '/editor/pieces'
C2 = SW_DIR + '/test-shot-build/cache2'
HI = SRC + '/test-shot/r2/hi'
FPS = 24
r2 = json.load(open(C2 + '/rig.json')); r3 = json.load(open(PC + '/pieces.json'))['pieces']
r4 = {k: v for k, v in json.load(open(EP + '/renzo_pieces.json')).items() if not k.startswith('_')}


# ------------------------------------------------------------------ pieces (#29 output, graded per piece) ---
def lv(g, lo, hi, gamma): return np.clip((g - lo) / (hi - lo), 0, 1) ** gamma * 255
def load(path, lo=0, hi=255, gamma=1.0):
    a = np.asarray(Image.open(path)).astype(np.float32); return np.dstack([lv(a[..., 0], lo, hi, gamma), a[..., 3] / 255.0])
PV = {k: v['pivots'] for k, v in r2.items()}; PV.update({k: v['pivots'] for k, v in r3.items()}); PV.update({k: v['pivots'] for k, v in r4.items()})
RG = (28, 214, 1.12)                                                  # Renzo grade (one for all his pieces: same negative)
P = {'re_body': load(EP + '/re2_body.png', *RG), 're_head': load(EP + '/re2_head.png', *RG),
     're_chew1': load(EP + '/re2_head_chew1.png', *RG), 're_chew2': load(EP + '/re2_head_chew2.png', *RG),
     're_uarm': load(EP + '/re2_uarm.png', *RG), 're_larm': load(EP + '/re2_larm.png', *RG), 're_farm': load(EP + '/re2_farm.png', *RG),
     'door': load(SRC + '/editor/door_clean.png', 18, 236, 1.0),
     'pails': load(C2 + '/pails.png', 46, 215, 0.8),
     'lu_body': load(PC + '/lu_body.png', 14, 200, .92), 'lu_head': load(PC + '/lu_head.png', 12, 214, .98),
     'lu_arm': load(PC + '/lu_arm.png', 10, 214, .92), 'apple': load(PC + '/apple.png', 10, 214, .92),
     'fm_front': load(PC + '/foreman_front.png', 20, 228, .95)}

P['re_body'][..., 1] = cv2.GaussianBlur(cv2.erode(P['re_body'][..., 1], np.ones((5, 5), np.uint8)), (0, 0), 1.0)   # trim the crate sliver on his back edge
# jaw-substitution drawings for Luciana (her own lower face re-pinned at the jaw hinge, closing on the bite) — Renzo's are
# cut by editor-build/renzo_cut.py.  Two extra drawings per head; which drawing is on screen is listed per frame in performance.json.
def jaw_drawings(piece, mouth, hinge, slope, xlim, ylim, angs):
    hd = piece; h, w = hd.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
    jaw = ((yy > mouth[1] + (xx - mouth[0]) * slope) & xlim(xx) & (yy < ylim)).astype(np.float32)
    jaw = cv2.GaussianBlur(jaw, (0, 0), 1.5); out = []
    for ang in angs:
        M = cv2.getRotationMatrix2D(hinge, ang, 1.0)
        jw = cv2.warpAffine(np.dstack([hd[..., 0], hd[..., 1] * jaw]), M, (w, h), flags=cv2.INTER_LINEAR)
        base = hd[..., 1] * (1 - jaw); a = jw[..., 1] + base * (1 - jw[..., 1])
        c = (jw[..., 0] * jw[..., 1] + hd[..., 0] * base * (1 - jw[..., 1])) / np.maximum(a, 1e-4)
        out.append(np.dstack([c, a]))
    return out
P['lu_chew1'], P['lu_chew2'] = jaw_drawings(P['lu_head'], (205, 372), (150, 330), -0.25, lambda x: x > 120, 460, (3.0, 6.0))
HEADS = {'R': {0: 're_head', 1: 're_chew1', 2: 're_chew2'}, 'L': {0: 'lu_head', 1: 'lu_chew1', 2: 'lu_chew2'}}

# foreman (one man, Siegel 1943): split at the collar into body + head on a neck pin
_ff = P['fm_front']; _nk = (150.0, 134.0)                           # neck pin at the chin/collar line (the r3 pin at y 102 cut his face)
# the r3 matte carried a strip of the bright ground in front of his face and chest: per row, cut 3 px beyond the last dark
# (figure) pixel, and drop the 0.66-alpha rectangle of ground below his boots
_lum = _ff[..., 0]; _a = np.clip((_ff[..., 1] - 0.75) / 0.25, 0, 1)
for _y in range(_ff.shape[0]):
    _xs = np.nonzero((_a[_y] > .5) & (_lum[_y] < 175))[0]
    if len(_xs): _a[_y, _xs.max() + 4:] = 0
_ff[..., 1] = cv2.GaussianBlur(_a.astype(np.float32), (0, 0), 0.8)
_yy = np.arange(_ff.shape[0])[:, None].astype(np.float32)
_cut = np.clip((_yy - (_nk[1] + 6)) / 6.0, 0, 1)
P['fm_head'] = np.dstack([_ff[..., 0], _ff[..., 1] * (1 - _cut)])
P['fm_body'] = np.dstack([_ff[..., 0], _ff[..., 1] * _cut])
# the faint light strip along the cut's left edge (critic r1): erode the matte 2 px and re-feather
for k in ('fm_head', 'fm_body'):
    P[k][..., 1] = cv2.GaussianBlur(cv2.erode(P[k][..., 1], np.ones((3, 3), np.uint8)), (0, 0), 0.8)

plate = np.asarray(Image.open(HI + '/plate_8c01492.png').convert('L')).astype(np.float32)
SH, SW = plate.shape                                                 # 1087 x 1933 (native sampling)
CX, CY, CR = 604.5 * SW / 1296, 89.5 * SH / 729, 45.7 * SW / 1296
ring = np.zeros(plate.shape, np.uint8); cv2.circle(ring, (int(CX), int(CY)), int(CR * .62), 255, -1)
hands = cv2.dilate(((plate < 110) & (ring > 0)).astype(np.uint8) * 255, np.ones((3, 3), np.uint8))
plate = cv2.inpaint(plate.astype(np.uint8), hands, 3, cv2.INPAINT_TELEA).astype(np.float32)   # photographed hands lifted off
plate = lv(plate, 14, 218, 0.5)
plate = cv2.GaussianBlur(plate, (0, 0), 1.1)                         # the wall is behind the focal plane
CARD = plate[89:103, 1203:1233].copy()
CARD_SLOT = {('A', 'renzo'): 1, ('A', 'luciana'): 2, ('B', 'renzo'): 1, ('B', 'luciana'): 2}
def drop_cards(pl, ver, tau):
    for (tt, who, _) in R.CARDS[ver]:
        n = CARD_SLOT[(ver, who)]; y = 89 + 14 * n
        if tau >= tt + 1 / 24.0 - 1e-9: pl[y:y + 14, 1203:1233] = CARD
        elif tau >= tt - 1e-9: pl[y - 5:y + 9, 1203:1233] = CARD
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
OPEN_X0, OPEN_X1 = D_XY[0] + 23, D_XY[0] + 369                       # the doorway opening (stage x)
FF_S = .54
FM_FEET = np.array([592.0, 628.0])                                   # the foreman's place in the doorway (FLOOR)
FM_GONE = np.array([300.0, 612.0])                                   # stepped back into the office, behind the left jamb
PS, P_XY = .93, np.array([470.0, 318.0])                             # near pail pile (occluder)
SL, SA, SR = .42, .42, .55
# ---- the places (stage coords).  CORNER_X = the hiding place behind the pile; her STATION is at the time clock, in the
# foreman's sight and clear of CORNER_X; his station is at the right edge.
CORNER_X = (962.0, 1500.0)
L_DUCK = np.array([600.0, 772.0])                                   # she comes in low, below the frame line, until the boxes hide her waist
L_OFF, L_STATION, L_CORNER = np.array([150.0, 790.0]), np.array([808.0, 640.0]), np.array([1132.0, 560.0])
R_OFF, R_STATION, R_CORNER, R_CLOCK = np.array([2150.0, 840.0]), np.array([1650.0, 846.0]), np.array([1500.0, 846.0]), np.array([1130.0, 860.0])
def lu_fk(hip_xy, hip, neck, elbow):
    lb = PV['lu_body']; Mb = mat(lb['hip'], hip_xy, hip, SL)
    Mh = mat(PV['lu_head']['neck'], ap(Mb, lb['neck']), hip + neck, SL)
    Ma = mat(PV['lu_arm']['elbow'], ap(Mb, lb['elbow']), hip + elbow, SL)
    Mp = mat(PV['apple']['grip'], ap(Ma, PV['lu_arm']['grip']), hip + elbow, SA)   # apple rigid in her fingers
    return Mb, Mh, Ma, Mp
def re_fk(root, hip, head, sh, el, wr):
    pb, ph, pu, pl, pf = PV['re2_body'], PV['re2_head'], PV['re2_uarm'], PV['re2_larm'], PV['re2_farm']
    Mb = mat(pb['hip'], root, hip, SR)
    Mh = mat(ph['neck'], ap(Mb, pb['neck']), hip + head, SR)
    Mu = mat(pu['shoulder'], ap(Mb, pb['shoulder']), hip + sh, SR)
    Ml = mat(pl['elbow'], ap(Mu, pu['elbow']), hip + sh + el, SR)
    Mf = mat(pf['wrist'], ap(Ml, pl['wrist']), hip + sh + el + wr, SR)
    return Mb, Mh, Mu, Ml, Mf, ap(Mh, ph['mouth']), ap(Mf, pf['grip'])
def l_apple(hip_xy, hip, elbow): return ap(lu_fk(hip_xy, hip, 0, elbow)[3], PV['apple']['c'])
def solve(f, target, grid):
    """IK for a key pose: brute-force over the joint grid, then the FK pins carry it (the angles become ordinary keys)."""
    best = None
    for v in grid:
        d = np.hypot(*(np.array(f(*v)) - target)) + 0.04 * sum(abs(x) for x in v)          # prefer the least bent pose
        if best is None or d < best[0]: best = (d, v)
    return best[1]
G1 = lambda a, b, s: np.arange(a, b + 1e-9, s)
# key poses, solved once (target -> joint angles; errors logged in performance.json)
IKERR = {}
def solve_log(name, f, target, grid):
    v = solve(f, target, grid); IKERR[name] = round(float(np.hypot(*(np.array(f(*v)) - target))), 1); return v
SHW = [(s_, e_, w_) for s_ in G1(-140, 30, 4) for e_ in G1(-160, 0, 4) for w_ in (-40, -20, 0, 20, 40)]
FEED_E = -30.0; FEED_R = (0.0, FEED_E); FEED_PT = l_apple(L_CORNER, 0, FEED_E)
R_BITE = solve_log('R_BITE', lambda h, hd: re_fk(R_CORNER, h, hd, 0, 0, 0)[5], FEED_PT + [12, -10], [(h, hd) for h in G1(0, 18, .5) for hd in G1(-6, 14, 1)])
GIVE_E = -14.0; GIVE = (0.0, GIVE_E); HAND_PT = l_apple(L_CORNER, 0, GIVE_E)        # where the apple passes between their hands
R_TAKE = solve_log('R_TAKE', lambda s_, e_, w_: re_fk(R_CORNER, 4, 0, s_, e_, w_)[6], HAND_PT + [18, 14], SHW)
R_REST = (0.0, 0.0, 0.0)
R_LID_PT = np.array([1205.0, 505.0])                                 # his lid, on the box between them (A: the core is left here)
L_LID_PT = np.array([1062.0, 515.0])                                 # her lid (B: he leaves the bitten apple here)
R_TOLID = solve_log('R_TOLID', lambda s_, e_, w_: re_fk(R_CORNER, 1, 0, s_, e_, w_)[6], R_LID_PT + [10, 8], SHW)
R_TOHERLID = solve_log('R_TOHERLID', lambda s_, e_, w_: re_fk(R_CORNER, 3, 0, s_, e_, w_)[6], L_LID_PT + [12, 8], SHW)
R_HOLD = solve_log('R_HOLD', lambda s_, e_, w_: re_fk(R_CORNER, 1, 0, s_, e_, w_)[6], np.array([1250.0, 470.0]), SHW)
R_EAT = solve_log('R_EAT', lambda s_, e_, w_: re_fk(R_CORNER, 10, 6, s_, e_, w_)[6] + [-6, -14], re_fk(R_CORNER, 10, 6, 0, 0, 0)[5] + [-4, 4], SHW)
R_TAKE_CORE = solve_log('R_TAKE_CORE', lambda s_, e_, w_: re_fk(R_CORNER, R_BITE[0], 0, s_, e_, w_)[6] + [-6, -14], FEED_PT, SHW)
L_OWN = (0.0, 0.0)                                                    # her photographed pose: the apple at her own mouth
L_LOW = (2.0, -8.0)
L_REACH = solve_log('L_REACH', lambda h, e: l_apple(L_CORNER, h, e), L_LID_PT + [0, -12], [(h, e) for h in G1(-4, 8, 1) for e in G1(-100, 60, 1)])

# ------------------------------------------------------------------ keys (film seconds; eased; drawings on twos) ---
def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def K(kf, t):
    if t <= kf[0][0]: return kf[0][1]
    for (ta, va), (tb, vb) in zip(kf, kf[1:]):
        if t <= tb:
            if tb <= ta: return vb
            return va + (vb - va) * ease((t - ta) / (tb - ta))
    return kf[-1][1]
def KV(kf, t):                                                       # vector keys
    if t <= kf[0][0]: return np.array(kf[0][1], float)
    for (ta, va), (tb, vb) in zip(kf, kf[1:]):
        if t <= tb:
            if tb <= ta: return np.array(vb, float)
            return np.array(va, float) + (np.array(vb, float) - np.array(va, float)) * ease((t - ta) / (tb - ta))
    return np.array(kf[-1][1], float)
def heads_keys(ver, who, amap, t_off, turn=.16, over=1.5, until=None):
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
R_HEAD = {'walk': -3, 'clock': -16, 'door': -9, 'her': 4, 'forward': 6, 'empty_place': 10, 'lid': 12}
L_NECK = {'walk': 0, 'pail': -5, 'door': 7, 'him': -2, 'clock': 8, 'forward': -4}
KEYS = {'A': {}, 'B': {}}
A = KEYS['A']
# ---- A: positions
A['R.pos'] = [(0, R_OFF), (.4, R_OFF), (2.0, R_STATION), (5.0, R_STATION), (6.0, R_CORNER), (14.3, R_CORNER), (15.0, R_CLOCK),
              (15.8, R_CLOCK), (17.0, R_OFF)]
A['L.pos'] = [(0, L_OFF), (1.0, L_OFF), (1.9, L_DUCK), (2.6, L_STATION), (5.0, L_STATION), (7.0, L_CORNER), (19.0, L_CORNER), (19.6, L_STATION),
              (20.6, L_STATION), (21.3, L_DUCK), (21.8, L_OFF)]
# ---- A: Renzo (hip, head, shoulder, wrist)
A['R.hip'] = [(0, -1), (5.0, -1), (6.2, 1), (8.2, 1), (8.45, R_BITE[0]), (8.9, R_BITE[0]), (9.3, 4), (10.6, 4), (11.0, 1), (12.7, 1),
              (12.95, R_BITE[0]), (13.4, R_BITE[0]), (14.0, 1.5), (14.3, 0), (15.0, -2), (15.8, -2)]
A['R.head'] = merge(heads_keys('A', 'renzo', R_HEAD, 0, until=(0, 5.5)),
                    [(5.6, 4), (8.2, 4), (8.45, R_BITE[1]), (8.9, R_BITE[1]), (9.3, 3), (10.6, 3), (10.8, 5), (12.7, 5), (12.95, R_BITE[1]),
                     (13.4, R_BITE[1]), (13.7, 12), (14.2, 12)],
                    heads_keys('A', 'renzo', R_HEAD, 0, until=(14.3, 99)))
A['R.sh'] = [(0, R_REST[0]), (9.2, R_REST[0]), (9.8, R_TAKE[0]), (10.6, R_TAKE[0]), (11.0, R_REST[0]), (13.0, R_REST[0]),
             (13.2, R_TAKE_CORE[0]), (13.4, R_TAKE_CORE[0]), (13.9, R_TOLID[0]), (14.1, R_TOLID[0]), (14.4, R_REST[0])]
A['R.el'] = [(0, R_REST[1]), (9.2, R_REST[1]), (9.8, R_TAKE[1]), (10.6, R_TAKE[1]), (11.0, R_REST[1]), (13.0, R_REST[1]),
             (13.2, R_TAKE_CORE[1]), (13.4, R_TAKE_CORE[1]), (13.9, R_TOLID[1]), (14.1, R_TOLID[1]), (14.4, R_REST[1])]
A['R.wr'] = [(0, R_REST[2]), (9.2, R_REST[2]), (9.8, R_TAKE[2]), (10.6, R_TAKE[2]), (11.0, R_REST[2]), (13.0, R_REST[2]),
             (13.2, R_TAKE_CORE[2]), (13.4, R_TAKE_CORE[2]), (13.9, R_TOLID[2]), (14.1, R_TOLID[2]), (14.4, R_REST[2])]
# ---- A: Luciana (hip, neck, elbow)
A['L.hip'] = [(0, 1), (7.0, 1), (8.2, FEED_R[0]), (8.6, FEED_R[0]), (9.4, GIVE[0]), (10.6, GIVE[0]), (10.9, 0), (11.4, 0),
              (12.4, FEED_R[0]), (13.2, FEED_R[0]), (13.6, 1), (19.0, 1), (19.4, 0)]
A['L.neck'] = merge(heads_keys('A', 'luciana', L_NECK, 0, until=(0, 5.7)),
                    [(5.6, 0), (7.0, -2), (8.2, -4), (9.4, -6), (10.6, -6), (10.9, 0), (11.6, 2), (12.4, -3), (13.4, -3), (14.0, 0)],
                    heads_keys('A', 'luciana', L_NECK, 0, until=(14.9, 99)))
A['L.elbow'] = [(0, -30), (2.6, -30), (2.8, -36), (3.0, L_LOW[1]), (5.0, L_LOW[1]), (7.0, L_LOW[1]), (8.2, FEED_R[1]), (8.6, FEED_R[1]),
                (9.4, GIVE[1]), (10.6, GIVE[1]), (10.95, L_OWN[1]), (11.4, L_OWN[1]), (12.4, FEED_R[1]), (13.2, FEED_R[1]),
                (13.5, -4), (14.6, -6), (15.5, -12), (16.5, -5), (17.8, -10), (19.0, -8), (19.6, -30)]
B = KEYS['B']                                                         # t = 37 + tau
B['R.pos'] = [(37, R_OFF), (37.4, R_OFF), (39.0, R_STATION), (42.0, R_STATION), (43.0, R_CORNER), (51.3, R_CORNER), (52.0, R_CLOCK),
              (52.4, R_CLOCK), (53.5, R_OFF)]
B['R.hip'] = [(37, -1), (43.0, 1), (45.2, 3), (46.0, 1), (50.6, 1), (50.9, 10), (51.05, 10), (51.25, 3), (51.35, 3), (51.6, 0), (52.4, 0), (52.75, -3)]
B['R.head'] = merge(heads_keys('B', 'renzo', R_HEAD, 37, until=(37, 50.6)),
                    [(50.6, 6), (50.9, 6), (51.05, 6), (51.2, 12), (51.35, -3)],
                    heads_keys('B', 'renzo', R_HEAD, 37, until=(51.9, 99)))
B['R.sh'] = [(37, R_REST[0]), (43.3, R_REST[0]), (43.9, R_HOLD[0]), (50.6, R_HOLD[0]), (50.9, R_EAT[0]), (51.05, R_EAT[0]),
             (51.25, R_TOHERLID[0]), (51.35, R_TOHERLID[0]), (51.6, R_REST[0])]
B['R.el'] = [(37, R_REST[1]), (43.3, R_REST[1]), (43.9, R_HOLD[1]), (50.6, R_HOLD[1]), (50.9, R_EAT[1]), (51.05, R_EAT[1]),
             (51.25, R_TOHERLID[1]), (51.35, R_TOHERLID[1]), (51.6, R_REST[1])]
B['R.wr'] = [(37, R_REST[2]), (43.3, R_REST[2]), (43.9, R_HOLD[2]), (50.6, R_HOLD[2]), (50.9, R_EAT[2]), (51.05, R_EAT[2]),
             (51.25, R_TOHERLID[2]), (51.35, R_TOHERLID[2]), (51.6, R_REST[2])]
B['L.pos'] = [(37, L_OFF), (52.0, L_OFF), (52.6, L_DUCK), (53.5, L_CORNER), (56.2, L_CORNER), (56.8, L_STATION), (72, L_STATION)]
B['L.hip'] = [(37, 1), (53.5, 1), (53.9, L_REACH[0]), (54.3, L_REACH[0]), (54.8, 1), (55.4, 0), (56.2, 1), (72, 1)]
B['L.neck'] = merge(heads_keys('B', 'luciana', L_NECK, 37, until=(52, 54.95)),
                    [(54.95, -3), (55.0, 2), (55.5, 2)],
                    heads_keys('B', 'luciana', L_NECK, 37, until=(55.5, 57.9)),
                    [(57.9, 6), (58.1, 3.5), (59.5, 3.5)],
                    heads_keys('B', 'luciana', L_NECK, 37, until=(59.9, 99)))
B['L.elbow'] = [(37, -30), (53.5, -30), (53.9, L_REACH[1]), (54.3, L_REACH[1]), (54.9, L_OWN[1]), (55.5, L_OWN[1]), (55.9, -6),
                (56.8, L_LOW[1]), (58.2, L_LOW[1]), (59.5, -3), (60.0, L_LOW[1]), (62.0, -4), (64.0, -7), (66.0, -4), (68.5, -7), (71.0, -5)]
BITES = {v: [(b['t'], b['who']) for b in json.load(open(SW_DIR + '/rules.json'))['bites'][v]] for v in 'AB'}
# chewing (jaw substitutions) after each bite, on twos: drawing 1, 2, 1, 0 ...
def chew(t_bite, dur=0.9):
    return [(t_bite + .0, 2), (t_bite + 1 / 12, 1), (t_bite + 2 / 12, 2), (t_bite + 3 / 12, 1), (t_bite + 4 / 12, 0), (t_bite + 6 / 12, 1),
            (t_bite + 7 / 12, 2), (t_bite + 8 / 12, 1), (t_bite + 9 / 12, 0), (t_bite + dur, 0)]
CHEW = {'A': {'R': [], 'L': []}, 'B': {'R': [], 'L': []}}
for v in 'AB':
    for tt, who in BITES[v]:
        CHEW[v]['R' if who == 'renzo' else 'L'] += chew(tt)
def chew_at(ver, who, tq):
    d = 0
    for t, s in sorted(CHEW[ver][who]):
        if tq + 1e-9 >= t: d = s
    return d
# ---- foreman: present in the doorway (FLOOR) or gone into the office (OFFICE); one man throughout
FM_HEAD = {'front_pan_left': 6.0, 'front_pan_centre': 0.0, 'front_pan_right': -6.0, 'front_on_luciana': 3.0}
def fm_head_keys(ver):
    off = 0 if ver == 'A' else 37; out = []; prev = None
    for tau, s in R.HEADS[ver]['foreman']:
        if s not in FM_HEAD: continue
        t = tau + off; a = FM_HEAD[s]
        out += [(t, prev), (t + .5, a)] if prev is not None else [(t, a)]; prev = a
    return out
FMK = {v: fm_head_keys(v) for v in 'AB'}
# exit: head turns to the office (+12) on the turn, then he steps back behind the left jamb; return: steps in, already looking out
FM_POS = {'A': [(0, FM_FEET), (5.0, FM_FEET), (5.25, FM_FEET), (5.9, FM_GONE), (19.4, FM_GONE), (20.0, FM_FEET)],
          'B': [(37, FM_FEET), (42.0, FM_FEET), (42.25, FM_FEET), (42.9, FM_GONE), (56.4, FM_GONE), (57.0, FM_FEET),
                (57.5, FM_FEET), (58.3, FM_FEET + [52, 6])]}               # B: one step out of the doorway, gaze held on her
FM_TURN = {'A': [(0, 0), (5.0, 0), (5.2, 14), (19.4, 14), (19.9, 0)], 'B': [(37, 0), (42.0, 0), (42.2, 14), (56.4, 14), (56.9, 0)]}

def q(t): return math.floor(t * 12 + 1e-6) / 12                    # drawings on twos (12/s)
def ver_of(t):
    if t < 35.0: return 'A', t, t
    if t < 37.0: return 'slate', t, t - 35.0
    return 'B', t, t - 37.0

def apple_state(ver, tq):
    off = 0 if ver == 'A' else 37
    n = sum(1 for (bt, _) in BITES[ver] if tq >= bt - 1e-9)
    at = None
    for tau, _s, a in R.APPLE[ver]:
        if tau + off <= tq + 1e-9: at = a
    if ver == 'B' and at == 'R_hand' and tq >= 51.3: at = 'L_lid'      # declared: he leaves it on her lid as he rises (rules: 53.0)
    return n, at

def state(t):
    ver, tf, tau = ver_of(t)
    tq = q(tf); k = KEYS[ver]
    s = {n: (KV(k[n], tq) if n.endswith('.pos') else K(k[n], tq)) for n in k}
    s['ver'] = ver; s['tq'] = tq; s['tau'] = tau
    fa = R.facing_at(R.fixture_minutes(tau))
    s['facing'] = fa
    s['fm_pos'] = KV(FM_POS[ver], tq)
    s['fm_visible'] = bool(s['fm_pos'][0] > OPEN_X0 - 60)
    s['fm_head'] = (K(FMK[ver], tq) if FMK[ver] else 0.0) + K(FM_TURN[ver], tq)
    s['apple_n'], s['apple_at'] = apple_state(ver, tq)
    s['L_on'] = s['L.pos'][0] > L_OFF[0] + 1; s['R_on'] = s['R.pos'][0] < R_OFF[0] - 1
    s['L_corner'] = bool(np.hypot(*(s['L.pos'] - L_CORNER)) < .5); s['R_corner'] = bool(np.hypot(*(s['R.pos'] - R_CORNER)) < .5)
    s['meet_drawn'] = bool(ver == 'A' and s['L_corner'] and s['R_corner'])
    s['L_draw'] = chew_at(ver, 'L', tq); s['R_draw'] = chew_at(ver, 'R', tq)
    return s

# ------------------------------------------------------------------ camera (WIDE 1296 window -> MEDIUM 960 window = 1.35x) ---
WIDE = (360.0, 20.0, 1296.0); MED = (600.0, 50.0, 960.0)
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
def drift_of(tau): return 12.0 * math.sin(2 * math.pi * tau / 35.0)
def view(stage_img, win):
    x0, y0, w = win; h = w * 540 / 960
    M = np.array([[960 / w, 0, -x0 * 960 / w], [0, 540 / h, -y0 * 540 / h]])
    return cv2.warpAffine(stage_img, M, (960, 540), flags=cv2.INTER_AREA if w > 960 else cv2.INTER_LINEAR)

# ------------------------------------------------------------------ compositing (#45) ---
class Comp:
    def __init__(self):
        self.C = np.zeros((SH, SW), np.float32); self.A = np.zeros((SH, SW), np.float32); self.S = np.ones((SH, SW), np.float32)
        self.order = []; self.cover = {}
    def over(self, name, lay, shadow=True, off=(10, 8), blur=10, dark=.30):
        g, a = lay[..., 0], lay[..., 1]
        if shadow:
            sh = 1 - cv2.GaussianBlur(np.roll(np.roll(a, off[1], 0), off[0], 1), (0, 0), blur) * dark
            self.C *= sh; self.S *= sh
        self.C = self.C * (1 - a) + g * a; self.A = self.A * (1 - a) + a
        self.order.append(name); self.cover[name] = np.maximum(self.cover.get(name, 0), a)
def W(piece, M, interp=cv2.INTER_AREA):
    return cv2.warpAffine(piece, M, (SW, SH), flags=interp, borderValue=(0, 0))
DOOR_LAY = W(P['door'], mat((0, 0), D_XY + [0, 4], 0, 1.0))
JAMB_LAY = DOOR_LAY.copy(); JAMB_LAY[:, int(OPEN_X0):, 1] = 0                       # the left jamb, cut from the doorway print
OPEN_MASK = np.zeros((SH, SW), np.float32); OPEN_MASK[:, int(OPEN_X0):] = 1
OPEN_MASK = cv2.GaussianBlur(OPEN_MASK, (0, 0), 1.0)                                # the wall left of the opening hides him
PAILS_LAY = W(P['pails'], mat((0, 0), P_XY, 0, PS))
SIGN_LAY = W(SIGN, mat((0, 0), (612, 54), 0, 1.0), cv2.INTER_LINEAR)

HS = 4
_HB = (int(CX - CR) - 4, int(CY - CR) - 4, int(2 * CR) + 8)
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
    x0, y0 = int(CX - CR), int(CY - CR); sub = hl[y0:int(CY + CR), x0:int(CX + CR)]
    yy, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
    dx = xx + x0 - CX; dy = yy + y0 - CY; wgt = sub * (np.hypot(dx, dy) > CR * .55)
    if wgt.sum() < 1: return None
    return math.degrees(math.atan2((dx * wgt).sum(), -(dy * wgt).sum())) % 360

# ------------------------------------------------------------------ handmade cards: the neutral 'B' slate and the 'A' label ---
_F = '/usr/share/fonts/truetype/dejavu/'
def _card():
    c = Image.new('L', (960, 540), 196); d = ImageDraw.Draw(c)
    d.text((480, 250), 'B', font=ImageFont.truetype(_F + 'DejaVuSerif-Bold.ttf', 150), fill=34, anchor='mm')
    d.text((480, 470), 'messa in scena con ritagli di fotografie FSA/OWI 1941-43 (Library of Congress)',
           font=ImageFont.truetype(_F + 'DejaVuSerif.ttf', 17), fill=58, anchor='mm')
    d.text((480, 494), 'suoni: registrazioni Wikimedia Commons  ·  crediti completi a parte',
           font=ImageFont.truetype(_F + 'DejaVuSerif.ttf', 17), fill=58, anchor='mm')
    return np.asarray(c).astype(np.float32)
SLATE = _card()
def slate(u):
    # a typed card laid on the dark ground: it slides in (0-0.25 s) and lies still; no timeline, no caption of the plot
    g = np.full((540, 960), 26.0, np.float32); k = ease(u / 0.25)
    dy = int(round((1 - k) * 60)); g[max(0, dy):, :] = SLATE[:540 - max(0, dy), :] * k + 26 * (1 - k)
    return g
_LAB = Image.new('LA', (64, 64), (0, 0)); _ld = ImageDraw.Draw(_LAB)
_ld.rectangle([0, 0, 52, 56], fill=(196, 255)); _ld.text((26, 29), 'A', font=ImageFont.truetype(_F + 'DejaVuSerif-Bold.ttf', 40), fill=(34, 255), anchor='mm')
_LAB = np.asarray(_LAB).astype(np.float32)
def label(img, t, letter_img, t0, t1):
    if not (t0 <= t < t1): return img
    a = (_LAB[..., 1] / 255.0) * min(1.0, (t1 - t) / 0.3, (t - t0) / 0.15 + 1e-3)
    y, x = 18, 18; h, w = a.shape
    img[y:y + h, x:x + w] = img[y:y + h, x:x + w] * (1 - a) + _LAB[..., 0] * a
    return img

ASSERT_LOG = {'frames': 0, 'meet_frames': [], 'layer_checks': 0, 'clock_max_err': 0.0, 'station_checks': 0, 'foreman_checks': 0}
CROSS = (52.0, 53.5)
PERF = {'A': [], 'B': []}
def frame_img(t, check=True):
    k = int(round(t * FPS)); ver, tf, tau = ver_of(t)
    if ver == 'slate':
        if check: R.assert_frame(k, None, meet_drawn=False); ASSERT_LOG['frames'] += 1
        return slate(tau)
    S = state(t); tq = S['tq']
    u = cam_u(tau); dr = drift_of(tau)
    pl = plate.copy(); drop_cards(pl, ver, tau)
    hl, md = clock_hands(tau)
    pl = pl * (1 - cv2.GaussianBlur(np.roll(np.roll(hl, 3, 0), 3, 1), (0, 0), 1.5) * .35)
    pl = pl * (1 - hl) + 22 * hl
    cp = Comp()
    cp.over('door_frame', DOOR_LAY, off=(6, 5), blur=6, dark=.25)
    cp.over('door_sign', SIGN_LAY, off=(3, 3), blur=2, dark=.3)
    # ---- the foreman: one photograph; on the turn he looks to the office and steps back out of sight behind the left jamb
    feet = S['fm_pos']; moving = abs(KV(FM_POS[ver], tq + .05)[0] - feet[0]) > .8
    bob = 2.0 * abs(math.sin(tq * math.pi / .35)) if moving else 0
    depth = 1 - .06 * ease((FM_FEET[0] - feet[0]) / (FM_FEET[0] - FM_GONE[0])) if feet[0] < FM_FEET[0] else 1.0
    Mb = mat(PV['foreman_front']['feet'], feet - [0, bob], 0, FF_S * depth)
    fb = W(P['fm_body'], Mb); fb[..., 1] *= OPEN_MASK
    Mh = mat(_nk, ap(Mb, _nk), S['fm_head'], FF_S * depth)
    fh = W(P['fm_head'], Mh); fh[..., 1] *= OPEN_MASK
    if fb[..., 1].max() > .02:
        cp.over('foreman', fb, off=(5, 3), blur=4, dark=.2); cp.over('foreman', fh, shadow=False)
    cp.over('door_leaf', JAMB_LAY, shadow=False)                    # #45: the jamb is in front of him
    # ---- puppets
    Lp = S['L.pos']; Rp = S['R.pos']
    lmov = np.hypot(*(KV(KEYS[ver]['L.pos'], tq + .05) - Lp)) > .8
    rmov = np.hypot(*(KV(KEYS[ver]['R.pos'], tq + .05) - Rp)) > .8
    lbob = 5 * abs(math.sin(tq * math.pi / .5)) if lmov else 0.0
    rbob = 6 * abs(math.sin(tq * math.pi / .45)) if rmov else 0.0
    Lb, Lh, La, Lap = lu_fk(Lp - [0, lbob], S['L.hip'], S['L.neck'], S['L.elbow'])
    Rb, Rh, Ru, Rl, Rf, Rmouth, Rgrip = re_fk(Rp - [0, rbob], S['R.hip'], S['R.head'], S['R.sh'], S['R.el'], S['R.wr'])
    if S['L_on']:
        cp.over('luciana_body', W(P['lu_body'], Lb), off=(12, 9), blur=12)
        cp.over('luciana_head', W(P[HEADS['L'][S['L_draw']]], Lh), off=(10, 8), blur=10)
    crossing_now = ver == 'B' and CROSS[0] <= tf < CROSS[1]
    if S['L_on'] and crossing_now:                                    # B near-miss: she passes wholly behind him
        cp.over('luciana_forearm_low', W(P['lu_arm'], La), off=(9, 8), blur=8)
    apc = APPLES[ver][min(S['apple_n'], len(APPLES[ver]) - 1)]; at = S['apple_at']
    if S['R_on']:
        cp.over('renzo_body', W(P['re_body'], Rb), off=(12, 9), blur=12)
        cp.over('renzo_head', W(P[HEADS['R'][S['R_draw']]], Rh), off=(9, 8), blur=9)
        cp.over('renzo_uarm', W(P['re_uarm'], Ru), off=(9, 8), blur=9)
        cp.over('renzo_larm', W(P['re_larm'], Rl), off=(9, 8), blur=9)
        if at == 'R_hand':
            cp.over('apple', W(apc, mat(PV['apple']['c'], Rgrip + [-6, -14], -8, SA)), off=(7, 6), blur=6, dark=.32)
        cp.over('renzo_farm', W(P['re_farm'], Rf), off=(8, 7), blur=7)
    if at == 'L_wrist' and S['L_on']:
        cp.over('apple', W(apc, Lap), off=(7, 6), blur=6, dark=.32)
    if S['L_on'] and not crossing_now:
        cp.over('luciana_forearm', W(P['lu_arm'], La), off=(9, 8), blur=8)
    cp.over('pail_pile_occluder', PAILS_LAY, off=(12, 10), blur=12, dark=.30)
    if at in ('R_lid', 'L_lid'):
        pos = R_LID_PT if at == 'R_lid' else L_LID_PT
        cp.over('lid_props', W(apc, mat(PV['apple']['c'], pos, -8, SA)), off=(5, 4), blur=3, dark=.5)
    # ---- per-frame asserts
    if check:
        mm = measure_minute(hl)
        if mm is not None:
            err = abs((mm - md + 180) % 360 - 180); ASSERT_LOG['clock_max_err'] = max(ASSERT_LOG['clock_max_err'], err)
        R.assert_frame(k, minute_deg=mm, meet_drawn=S['meet_drawn'])
        order = ['wall_plate'] + [n for n in cp.order if n in R.LAYERS] + ['clock_hands']
        R.assert_layer_order(order)
        crossing = ver == 'B' and CROSS[0] <= tf < CROSS[1]
        li = [i for i, n in enumerate(cp.order) if n.startswith('luciana')]; ri = [i for i, n in enumerate(cp.order) if n.startswith('renzo')]
        if crossing: assert not (li and ri) or max(li) < min(ri), cp.order
        # (r1) the hiding place is only used while the foreman is away: Luciana's DRAWN x-range never enters CORNER_X while he
        # faces the floor (except the 1.5 s B crossing), and the foreman is drawn iff he faces the floor (outside his 0.6 s steps)
        if S['facing'] == 'FLOOR' and S['L_on'] and not crossing:
            cov = np.maximum(cp.cover.get('luciana_body', 0), cp.cover.get('luciana_head', 0))
            xs = np.nonzero((np.asarray(cov) > .1).any(0))[0]
            assert len(xs) == 0 or xs.max() < CORNER_X[0] or xs.min() > CORNER_X[1], ('L in corner zone under his eye', t, xs.min(), xs.max())
            ASSERT_LOG['station_checks'] += 1
        steps = [(5.0, 5.9), (19.4, 20.0), (42.0, 42.9), (56.4, 57.0)]
        if not any(a <= tf <= b for a, b in steps):
            assert S['fm_visible'] == (S['facing'] == 'FLOOR'), ('foreman state', t, S['facing'], S['fm_pos'])
            ASSERT_LOG['foreman_checks'] += 1
        ASSERT_LOG['layer_checks'] += 1; ASSERT_LOG['frames'] += 1
        if S['meet_drawn']: ASSERT_LOG['meet_frames'].append(k)
        if k % 2 == 0:
            PERF[ver].append({'frame': k, 't': round(t, 4), 'tq': round(tq, 4), 'R': {'pos': [round(float(x), 1) for x in Rp], 'hip': round(S['R.hip'], 2),
                              'neck': round(S['R.head'], 2), 'shoulder': round(S['R.sh'], 2), 'elbow': round(S['R.el'], 2), 'wrist': round(S['R.wr'], 2), 'head_drawing': HEADS['R'][S['R_draw']]},
                              'L': {'pos': [round(float(x), 1) for x in Lp], 'hip': round(S['L.hip'], 2), 'neck': round(S['L.neck'], 2), 'elbow': round(S['L.elbow'], 2),
                                    'head_drawing': HEADS['L'][S['L_draw']]},
                              'foreman': {'facing': S['facing'], 'drawn': S['fm_visible'], 'feet': [round(float(x), 1) for x in feet], 'neck': round(S['fm_head'], 2)},
                              'apple': {'bites': S['apple_n'], 'at': at}, 'clock_minute_deg': round(md, 2), 'camera_u': round(u, 3)})
    # ---- camera: wall plate at 0.6x parallax, everything in front of it at 1.0x
    wf = window(u, dr, 1.0); wp = window(u, dr, 0.6)
    bg = view(pl, wp)
    C, A_, S_ = view(cp.C, wf), view(cp.A, wf), view(cp.S, wf)
    img = bg * S_ * (1 - A_) + C
    if ver == 'A': img = label(img, t, _LAB, 0.0, 1.6)
    return img

# ------------------------------------------------------------------ film ---
TOTAL = 72.0
film = kit.Film('renzo-e-luciana', seconds=TOTAL)
film.poster_at = 10.0
def pic(t, ink):
    ink._grain = False
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

def write_performance():
    subs = {v: [] for v in 'AB'}
    for v in 'AB':
        prev = {}
        for fr in PERF[v]:
            for who in ('R', 'L'):
                d = fr[who]['head_drawing']
                if prev.get(who) != d: subs[v].append({'frame': fr['frame'], 't': fr['t'], 'who': who, 'drawing': d}); prev[who] = d
            fs = 'in_doorway' if fr['foreman']['drawn'] else 'gone_into_office'
            if prev.get('F') != fs: subs[v].append({'frame': fr['frame'], 't': fr['t'], 'who': 'foreman', 'state': fs}); prev['F'] = fs
            ab = fr['apple']['bites']
            if prev.get('ap') != ab: subs[v].append({'frame': fr['frame'], 't': fr['t'], 'who': 'apple', 'drawing': f'apple{ab}'}); prev['ap'] = ab
    out = {'note': 'Regenerated by the editor (repair round 1) from films/renzo-e-luciana.py as rendered: the film is the source of truth. '
                   'Frames on twos (12 drawings/s). Bite frames equal rules.json/cues.json (A 8.5 R, 11.0 L, 13.0 R; B 51.0 R, 55.0 L).',
           'ik_errors_px': IKERR, 'joints': {'renzo': ['hip', 'neck', 'shoulder', 'elbow', 'wrist'], 'luciana': ['hip', 'neck', 'elbow'], 'foreman': ['feet (root)', 'neck']},
           'ik_solved_key_poses': {'FEED_R (L hip, elbow)': FEED_R, 'GIVE': GIVE, 'R_TAKE (shoulder, wrist)': R_TAKE, 'R_TOLID': R_TOLID,
                                   'R_TOHERLID': R_TOHERLID, 'R_EAT': R_EAT, 'R_HOLD': R_HOLD, 'L_REACH': L_REACH},
           'substitutions': subs, 'frames': PERF}
    json.dump(out, open(SW_DIR + '/performance.json', 'w'), indent=0, default=lambda o: [float(x) for x in o] if hasattr(o, '__iter__') else float(o))

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--compare':
        compare()
    else:
        film.render()
        if not (len(sys.argv) > 1 and sys.argv[1] == '--stills'):
            ASSERT_LOG['meet_range'] = [min(ASSERT_LOG['meet_frames']), max(ASSERT_LOG['meet_frames'])] if ASSERT_LOG['meet_frames'] else None
            ASSERT_LOG['meet_frames'] = len(ASSERT_LOG['meet_frames'])
            json.dump(ASSERT_LOG, open(SW_DIR + '/render-asserts.json', 'w'), indent=1); print(ASSERT_LOG)
            write_performance()
