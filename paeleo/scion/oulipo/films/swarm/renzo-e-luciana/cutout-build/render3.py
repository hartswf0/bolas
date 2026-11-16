"""TEST SHOT r3 (cutout-performance) · Renzo e Luciana · A 4.5-15 s then B 41.5-53.5 s (each starts 0.5 s early so the foreman's
FLOOR->OFFICE turn at 12:01 is seen as a substitution of two real photographs, front then back).
#29 GrabCut pieces (cuts3.py: Luciana = Marjory Collins' young woman with the apple, Ross Heater 1943; foreman front = Siegel 1943;
r2 pieces reused: Renzo = Siegel, Dodge 1942; doorway + foreman back = Delano 1942; wall plate + near pails = Russell Lee 1941)
-> #32 FK rigs (L: root > hip > neck > head; hip > elbow > forearm+hand > grip > apple | R: root > hip > neck > head)
-> #45 occlusion DAG: wall plate < doorway < foreman < L body/head < R body/head < L forearm (apple behind fingers) < near pails
< apple on a lid < paper clock hands.  Stage = the wall plate at its native 1:1 sampling (1933x1087); WIDE = 1536x864 window
(downsampled to 960), MEDIUM = 960x540 window at 1:1 (a 1.6x push).  Keys on twos (12 drawings/s), eased, with overshoot."""
import os, sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
B = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films'); import kit
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana'
CP = SRC + '/cutout-performance'; PC = CP + '/pieces'
C2 = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana/test-shot-build/cache2'
HI = SRC + '/test-shot/r2/hi'
r2 = json.load(open(C2 + '/rig.json')); r3 = json.load(open(PC + '/pieces.json'))['pieces']
def lv(g, lo, hi, gamma): return np.clip((g - lo) / (hi - lo), 0, 1) ** gamma * 255          # per-piece levels/gamma only
def load(path, lo=0, hi=255, gamma=1.0):
    a = np.asarray(Image.open(path)).astype(np.float32); return np.dstack([lv(a[..., 0], lo, hi, gamma), a[..., 3] / 255.0])
PV = {k: v['pivots'] for k, v in r2.items()}; PV.update({k: v['pivots'] for k, v in r3.items()})
P = {'re_body': load(C2 + '/re_body.png', 22, 200, 1.08), 're_head': load(C2 + '/re_head.png', 22, 226, 1.1),
     'door': load(C2 + '/door_empty.png', 18, 236, 1.0), 'foreman': load(C2 + '/foreman.png', 18, 236, 1.0),
     'pails': load(C2 + '/pails.png', 14, 215, 1.0),
     'lu_body': load(PC + '/lu_body.png', 12, 200, .85), 'lu_head': load(PC + '/lu_head.png', 10, 214, .92),
     'lu_arm': load(PC + '/lu_arm.png', 10, 214, .92), 'apple': load(PC + '/apple.png', 10, 214, .92),
     'fm_front': load(PC + '/foreman_front.png', 20, 228, .95)}
plate = np.asarray(Image.open(HI + '/plate_8c01492.png').convert('L')).astype(np.float32)
SH, SW = plate.shape                                                    # 1087 x 1933, native
CX, CY, CR = 604.5 * SW / 1296, 89.5 * SH / 729, 45.7 * SW / 1296
ring = np.zeros(plate.shape, np.uint8); cv2.circle(ring, (int(CX), int(CY)), int(CR * .62), 255, -1)
hands = cv2.dilate(((plate < 110) & (ring > 0)).astype(np.uint8) * 255, np.ones((3, 3), np.uint8))
plate = cv2.inpaint(plate.astype(np.uint8), hands, 3, cv2.INPAINT_TELEA).astype(np.float32)
plate = lv(plate, 22, 222, 1.0)
DOF = float(os.environ.get('DOF', '1.1'))
plate = cv2.GaussianBlur(plate, (0, 0), DOF)                           # the wall is behind the focal plane (couple)
sign = Image.new('L', (190, 32), 214); sd = ImageDraw.Draw(sign)
sd.text((11, 5), 'CAPOREPARTO', font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 18), fill=34)
sign = np.asarray(sign.rotate(-1.2, expand=True, resample=Image.BICUBIC, fillcolor=0)).astype(np.float32)
sign_a = cv2.GaussianBlur((sign > 0).astype(np.float32), (0, 0), .6)
def warp(piece, pivot, world, ang, s):
    M = cv2.getRotationMatrix2D((float(pivot[0]), float(pivot[1])), ang, s); M[:, 2] += np.array(world, float) - np.array(pivot, float)
    return cv2.warpAffine(piece, M, (SW, SH), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderValue=(0, 0)), M
def mat(pivot, world, ang, s):
    M = cv2.getRotationMatrix2D((float(pivot[0]), float(pivot[1])), ang, s); M[:, 2] += np.array(world, float) - np.array(pivot, float); return M
def ap(M, p): return M @ np.array([p[0], p[1], 1.0])
def over(cv, lay, shadow=True, off=(10, 8), blur=10, dark=.30):
    a = lay[..., 1]
    if shadow:                                  # soft contact shadow down-right: the plate's key light is upper left
        cv *= (1 - cv2.GaussianBlur(np.roll(np.roll(a, off[1], 0), off[0], 1), (0, 0), blur) * dark)
    cv[:] = cv * (1 - a) + lay[..., 0] * a
def bite(piece, centre, r, seed):
    p = piece.copy(); h, w = p.shape[:2]; Y, X = np.mgrid[0:h, 0:w]
    ang = np.arctan2(Y - centre[1], X - centre[0]); rng = np.random.default_rng(seed)
    rr = r * (1 + .12 * np.sin(ang * 5 + rng.uniform(0, 6))); dist = np.hypot(X - centre[0], Y - centre[1])
    cut = dist < rr; rim = (dist >= rr) & (dist < rr + 3.0) & (p[..., 1] > .5)
    p[cut, 1] = 0; p[rim, 0] = np.maximum(p[rim, 0], 196)              # scissor-cut bite; the rim shows the print's pale flesh
    return p
A0 = P['apple']; A1 = bite(A0, (138, 40), 22, 1); A2 = bite(A1, (8, 52), 20, 2); A3 = bite(A2, (128, 92), 21, 3)   # R, L, R
B1 = bite(A0, (138, 40), 22, 7)                                         # B: the single bite Renzo leaves for her
# ---------------- stage geometry (native plate px) ----------------
DS, D_XY = 1.0, np.array([367.0, -30.0])                                # doorway just left of the clock (casing ~x 800)
F_FEET = D_XY + np.array(PV['foreman']['feet']) + np.array(r2['foreman']['crop'][:2]) - np.array(r2['door']['crop'][:2])
FF_S = .54                                                              # foreman front scaled to the back-view man's height
PS, P_XY = .93, np.array([470.0, 318.0])                                # near pail pile
SL, SR, SA = .44, .70, .44
L_HIP0 = np.array([892.0, 601.0])
def lu_fk(dx, hip, neck, elbow):
    lb = PV['lu_body']; Mb = mat(lb['hip'], L_HIP0 + [dx, 0], hip, SL)
    Mh = mat(PV['lu_head']['neck'], ap(Mb, lb['neck']), hip + neck, SL)
    Ma = mat(PV['lu_arm']['elbow'], ap(Mb, lb['elbow']), hip + elbow, SL)
    # apple attachment: the apple's own grip point rides the hand's grip point, same rotation (rigid in the fingers)
    Mp = mat(PV['apple']['grip'], ap(Ma, PV['lu_arm']['grip']), hip + elbow, SA)
    return Mb, Mh, Ma, Mp
FEED, L_FEED_HIP = -16.0, -3.0
Mp_feed = lu_fk(0, L_FEED_HIP, 0, FEED)[3]
APPLE_FEED_RIGHT = ap(Mp_feed, (PV['apple']['c'][0] + 64, PV['apple']['c'][1] - 6))      # the apple's right flank at the feed
def re_fk(root, hip, head):
    pb, ph = PV['re_body'], PV['re_head']; Mb = mat(pb['hip'], root, hip, SR)
    Mh = mat(ph['neck'], ap(Mb, pb['neck']), hip + head, SR); return Mb, Mh, ap(Mh, ph['mouth'])
R_BITE_HEAD, R_BITE_HIP = 9.0, 3.0
R_ROOT = APPLE_FEED_RIGHT - re_fk(np.zeros(2), R_BITE_HIP, R_BITE_HEAD)[2] + [6, 0]       # FK solve: his mouth lands on the apple
_pa = np.asarray(Image.open(C2 + '/pails.png'))[..., 3] > 128
def pile_top(x):                                                        # stage y of the near pile's top edge at stage x
    c = np.nonzero(_pa[:, int(np.clip((x - P_XY[0]) / PS, 0, _pa.shape[1] - 1))])[0]; return P_XY[1] + (c[0] if len(c) else 0) * PS
_rel = ap(lu_fk(0, -4.5, 0, -34)[3], PV['apple']['c'])
LID_A = np.array([_rel[0], pile_top(_rel[0]) - 22 * SA / .44])          # his pail lid (A: the core is set here at 14.0)
LID_B = np.array([L_HIP0[0] + 70, pile_top(L_HIP0[0] + 70) - 22 * SA / .44])   # her pail lid (B: he leaves the one-bite apple here)
# ---------------- keys (film seconds) ----------------
def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def K(kf, t):
    if t <= kf[0][0]: return kf[0][1]
    for (ta, va), (tb, vb) in zip(kf, kf[1:]):
        if t <= tb: return va + (vb - va) * ease((t - ta) / (tb - ta))
    return kf[-1][1]
KEYS = {
 'A': {
  'L.root_dx': [(4.5, -900), (5.08, -900), (5.1, -640), (6.9, 0)],
  'L.hip':     [(4.5, 2), (5.1, 2), (6.0, -1), (6.9, -2), (8.2, L_FEED_HIP), (10.4, L_FEED_HIP), (11.0, 1.5), (11.6, -2), (12.4, L_FEED_HIP), (13.4, -2), (14.0, -4.5), (14.6, 0), (15.0, 0)],
  'L.neck':    [(4.5, 0), (6.9, 0), (8.2, -2.5), (9.4, 1.5), (10.4, -1), (11.0, 3.5), (11.5, 3.5), (12.2, -2), (13.4, -1.5), (14.6, 1), (15.0, 1)],
  'L.elbow':   [(4.5, -3), (6.9, -3), (7.4, -1), (8.05, FEED - 1.5), (8.2, FEED), (10.4, FEED), (10.95, 1.2), (11.0, 0), (11.5, 0), (12.25, FEED - 1.2), (12.4, FEED), (13.4, FEED), (13.95, -34), (14.0, -34), (14.6, -4), (15.0, -3)],
  'R.root_dy': [(4.5, 0), (14.4, 0), (15.0, -55)],
  'R.hip':     [(4.5, -1), (5.1, -1), (6.5, 1.5), (8.25, R_BITE_HIP + .6), (8.35, R_BITE_HIP), (9.0, R_BITE_HIP), (9.4, 1.0), (12.6, 1.0), (12.85, R_BITE_HIP), (13.3, R_BITE_HIP), (13.7, 1.0), (14.4, 0), (15.0, -3)],
  'R.head':    [(4.5, -23), (5.1, -23), (5.6, 4), (5.75, 2.5), (6.6, 2.5), (7.0, -24), (7.1, -23), (8.0, -23), (8.3, R_BITE_HEAD + 1.5), (8.4, R_BITE_HEAD), (9.0, R_BITE_HEAD), (9.25, -26), (9.35, -23), (10.6, -23), (10.8, -6), (11.3, -6), (11.5, -23), (12.55, -23), (12.85, R_BITE_HEAD + 1.2), (12.95, R_BITE_HEAD), (13.3, R_BITE_HEAD), (13.55, -25), (13.65, -23), (15.0, -20)],
 },
 'B': {
  'R.root_dx': [(41.5, 240), (42.2, 240), (43.8, 0), (52.6, 0), (53.3, -820), (53.5, -900)],
  'R.root_dy': [(41.5, 0), (52.55, 0), (52.9, -70), (53.3, -110), (53.5, -110)],
  'R.hip':     [(41.5, -1), (43.8, 1), (45.2, 4), (46.0, 1), (52.0, 1), (52.25, 9.5), (52.35, 9), (52.6, 6), (53.0, -2), (53.5, -3)],
  'R.head':    [(41.5, -23), (44.0, -23), (44.4, 3), (44.5, 2), (45.4, 2), (45.7, 16), (45.8, 14.5), (46.6, 14.5), (46.9, -25), (47.0, -23),
                (48.0, -23), (48.25, 3), (48.9, 3), (49.1, 15), (49.6, 15), (49.8, -24), (49.9, -23), (50.5, -23), (50.65, 14), (51.1, 14),
                (51.25, -24), (51.35, -23), (51.7, -23), (51.8, 14), (52.0, 15), (52.2, 21), (52.3, 20), (52.55, 20), (52.9, -4), (53.5, -8)],
  'L.root_dx': [(41.5, -900), (52.6, -900), (52.62, -560), (53.5, -150)],
  'L.hip':     [(41.5, 3), (52.35, 3), (53.0, 1.5), (53.5, 0)],
  'L.neck':    [(41.5, -2), (52.35, -2), (53.2, 2), (53.5, 4)],
  'L.elbow':   [(41.5, -30), (53.0, -30), (53.5, -26)],                # empty hand low: the apple is still on her lid
 }}
BITES = {'A': [(8.4, 'R', 1), (11.0, 'L', 2), (12.95, 'R', 3)], 'B': [(52.3, 'R', 1)]}
APPLE_RELEASE_A = 14.0
SEG = [('A', 0.0, 10.5, 4.5), ('B', 10.5, 22.5, 41.5)]                  # (version, shot t0, t1, film t at t0)
TURN = {'A': 5.0, 'B': 42.0}
def q(t): return math.floor(t * 12 + 1e-6) / 12                         # on twos
pails_lay, _ = warp(P['pails'], (0, 0), P_XY, 0, PS)
door_lay, _ = warp(P['door'], (0, 0), D_XY + [0, 4], 0, DS)
def apple_piece(ver, tq):
    n = sum(tq >= b[0] for b in BITES[ver])
    if ver == 'A': return [A0, A1, A2, A3][n], n
    return [A0, B1][n], n
def state(ver, tq):
    k = KEYS[ver]; g = lambda name, d=0.0: K(k[name], tq) if name in k else d
    return {'L.root_dx': g('L.root_dx'), 'L.hip': g('L.hip'), 'L.neck': g('L.neck'), 'L.elbow': g('L.elbow'),
            'R.root_dx': g('R.root_dx'), 'R.root_dy': g('R.root_dy'), 'R.hip': g('R.hip'), 'R.head': g('R.head'),
            'foreman': 'front' if tq < TURN[ver] else 'back', 'apple_bites': apple_piece(ver, tq)[1],
            'apple_on': ('L.hand' if (ver == 'A' and tq < APPLE_RELEASE_A) else ('R.lid' if ver == 'A' else 'L.lid'))}
CAM = {'A': [(4.5, 0.0), (5.3, 0.0), (7.2, 1.0), (15.0, 1.0)], 'B': [(41.5, 0.0), (42.3, 0.0), (44.2, 1.0), (52.15, 1.0), (53.5, 0.0)]}
WIDE = (400.0, 40.0, 1200.0); MED = (600.0, 48.0, 960.0)               # (x0, y0, width) of the camera window on the stage
def cam(ver, tf):
    u = K(CAM[ver], tf); x0 = WIDE[0] + (MED[0] - WIDE[0]) * u; y0 = WIDE[1] + (MED[1] - WIDE[1]) * u
    w = 1.0 / (1.0 / WIDE[2] + (1.0 / MED[2] - 1.0 / WIDE[2]) * u); return x0, y0, w, u
def frame_img(t):
    ver, t0, t1, f0 = [s for s in SEG if s[1] <= t < s[2] + 1e-9][0]
    tf = f0 + (t - t0); tq = f0 + q(t - t0); tau = tf if ver == 'A' else tf - 37.0
    S = state(ver, tq); cv = plate.copy()
    over(cv, door_lay, off=(6, 5), blur=6, dark=.25)
    if S['foreman'] == 'back':
        sway = .7 * math.sin(tq * 1.1) + (.35 if (tq % 2.6) < 1.3 else -.2)
        lay, _ = warp(P['foreman'], PV['foreman']['feet'], F_FEET, sway, DS); over(cv, lay, shadow=False)
    else:
        lay, _ = warp(P['fm_front'], PV['foreman_front']['feet'], F_FEET + [6, 0], 0, FF_S); over(cv, lay, off=(5, 3), blur=4, dark=.2)
    sx, sy = int(D_XY[0] + 60), 44
    cv[sy:sy + sign.shape[0], sx:sx + sign.shape[1]] = cv[sy:sy + sign.shape[0], sx:sx + sign.shape[1]] * (1 - sign_a) + sign * sign_a
    Mb, Mh, Ma, Mp = lu_fk(S['L.root_dx'], S['L.hip'], S['L.neck'], S['L.elbow'])
    lvis = S['L.root_dx'] > -880
    if lvis:
        over(cv, cv2.warpAffine(P['lu_body'], Mb, (SW, SH), flags=cv2.INTER_AREA), off=(12, 9), blur=12)
        over(cv, cv2.warpAffine(P['lu_head'], Mh, (SW, SH), flags=cv2.INTER_AREA), off=(10, 8), blur=10)
    if ver == 'B' and lvis:                       # B crossing: she passes wholly behind him (occlusion order L < R)
        over(cv, cv2.warpAffine(P['lu_arm'], Ma, (SW, SH), flags=cv2.INTER_AREA), off=(9, 8), blur=8, dark=.30)
    root = R_ROOT + [S['R.root_dx'], S['R.root_dy']]
    Rb, Rh, _ = re_fk(root, S['R.hip'], S['R.head'])
    over(cv, cv2.warpAffine(P['re_body'], Rb, (SW, SH), flags=cv2.INTER_AREA), off=(12, 9), blur=12)
    over(cv, cv2.warpAffine(P['re_head'], Rh, (SW, SH), flags=cv2.INTER_AREA), off=(9, 8), blur=9)
    apc, _ = apple_piece(ver, tq)
    if S['apple_on'] == 'L.hand' and lvis:
        over(cv, cv2.warpAffine(apc, Mp, (SW, SH), flags=cv2.INTER_AREA), off=(7, 6), blur=6, dark=.32)
    if lvis and ver == 'A': over(cv, cv2.warpAffine(P['lu_arm'], Ma, (SW, SH), flags=cv2.INTER_AREA), off=(9, 8), blur=8, dark=.30)
    over(cv, pails_lay, off=(12, 10), blur=12, dark=.30)
    if S['apple_on'] != 'L.hand':                                          # resting on a pail lid, in front of the pile
        pos = LID_A if ver == 'A' else LID_B
        lay, _ = warp(apc, PV['apple']['c'], pos, -8, SA); over(cv, lay, off=(5, 4), blur=3, dark=.5)
    mins = tau / 5.0; hl = np.zeros((SH, SW), np.float32)
    def hand(angdeg, L, w):
        a = math.radians(angdeg - 90); b = a + math.pi / 2
        pts = [(CX + w * math.cos(b), CY + w * math.sin(b)), (CX + L * math.cos(a), CY + L * math.sin(a)),
               (CX - w * math.cos(b), CY - w * math.sin(b)), (CX - 8 * math.cos(a), CY - 8 * math.sin(a))]
        cv2.fillPoly(hl, [np.round(np.array(pts) * 8).astype(np.int32)], 1.0, lineType=cv2.LINE_AA, shift=3)
    hand(0.5 * mins, CR * .48, 4.2); hand(6.0 * mins, CR * .74, 2.8); cv2.circle(hl, (int(CX), int(CY)), 4, 1.0, -1)
    over(cv, np.dstack([np.full_like(hl, 22), hl]), off=(3, 3), blur=1.5, dark=.35)
    x0, y0, w, u = cam(ver, tf); h = w * 540 / 960
    M = np.array([[960 / w, 0, -x0 * 960 / w], [0, 540 / h, -y0 * 540 / h]])
    return cv2.warpAffine(cv, M, (960, 540), flags=cv2.INTER_AREA)
def performance():
    out = {'fps': 24, 'drawings_per_second': 12, 'units': 'degrees ccw (cv2), stage px; film seconds', 'segments': {}}
    for ver, f0, f1 in [('A', 4.5, 15.0), ('B', 41.5, 53.5)]:
        fr = []
        for i in range(int(round((f1 - f0) * 24))):
            tf = f0 + i / 24; tq = f0 + q(i / 24); s = state(ver, tq); x0, y0, w, u = cam(ver, tf)
            s.update({'frame': int(round(tf * 24)), 't': round(tf, 4), 'drawing_t': round(tq, 4), 'clock_min_after_12': round((tf if ver == 'A' else tf - 37) / 5, 4),
                      'cam': [round(x0, 1), round(y0, 1), round(w, 1)]})
            fr.append({k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()})
        out['segments'][ver] = {'film_t': [f0, f1], 'keys': KEYS[ver], 'bites': BITES[ver], 'turn_t': TURN[ver], 'camera_keys': CAM[ver], 'frames': fr}
    out['substitutions'] = {'foreman_front_to_back': TURN, 'apple': {'A': ['A0', 'A1@8.40 R', 'A2@11.00 L', 'A3@12.95 R', 'released to R.lid@14.00'], 'B': ['A0 on L.lid', 'B1@52.30 R (one bite, left for her)']}}
    return out
TOTAL = 22.5
film = kit.Film('testshot', seconds=TOTAL)
def pic(t, ink):
    ink._grain = False
    g = np.clip(frame_img(t), 0, 255).astype(np.uint8); ink.img = Image.fromarray(np.stack([g] * 3, -1)).convert('RGBA')
film.picture(pic)
SND = SRC + '/test-shot/sound'
def wav(path):
    import wave
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2: x = x.reshape(-1, 2).mean(1)
    return x
def snd(mix):
    tick = wav(SND + '/Clock_ticking.wav')
    for (ver, t0, t1, f0) in SEG:
        n = int((t1 - t0) * kit.RATE); seg = tick[int(1 * kit.RATE): int(1 * kit.RATE) + n]
        if len(seg) < n: seg = np.tile(tick, n // len(tick) + 1)[:n]
        seg = seg * np.minimum(1, np.minimum(np.arange(len(seg)), len(seg) - np.arange(len(seg))) / 800)
        mix.add(seg, t0, gain=.45 if ver == 'A' else .75, pan=-.1)
        mix.room(t0, t1 - t0, gain=.035)
        tt = t0 + (TURN[ver] - f0)
        mix.steps(t0, tt, every=.5, gain=.12, surface='stone', pan_from=-.6, pan_to=-.6)
        for d in (0.05, 2.2):
            r = mix.band(mix.noise(.35, 'white'), 2500, 7000) * mix.env(int(.35 * kit.RATE), .02, .3); mix.add(r * .5, tt + d, gain=.18, pan=-.6)
        for (bt, who, _) in BITES[ver]:
            st = t0 + (bt - f0); n2 = int(.2 * kit.RATE)
            mix.add(mix.band(mix.noise(.2, 'white'), 1200, 5000) * mix.env(n2, .002, .13), st, gain=.5, pan=.1); mix.click(st, gain=.22, bright=3000)
    mix.click(0.0 + (14.0 - 4.5), gain=.25, bright=1800)                    # A: the core set down on his lid
    mix.bell(10.5 + (52.0 - 41.5), freq=1320, seconds=2.0, gain=.25, pan=.2)  # B: the late bell (scratch kit synthesis)
    mix.steps(10.5 + 11.0, 10.5 + 12.0, every=.33, gain=.14, pan_from=.2, pan_to=-.5)
    mix.steps(10.5 + 10.95, 10.5 + 12.0, every=.4, gain=.12, pan_from=-.8, pan_to=0)
film.sound(snd)
if __name__ == '__main__':
    from pathlib import Path
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        os.makedirs(CP + '/stills', exist_ok=True)
        for t in [float(x) for x in sys.argv[2:]]:
            Image.fromarray(np.clip(frame_img(t), 0, 255).astype(np.uint8)).save(f'{CP}/stills/f_{t:05.2f}.png')
    elif len(sys.argv) > 1 and sys.argv[1] == '--perf':
        json.dump(performance(), open('/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana/performance.json', 'w'))
    else:
        film.render(out_dir=Path(CP + '/render'))
