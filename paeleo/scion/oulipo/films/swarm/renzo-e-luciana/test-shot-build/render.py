"""TEST SHOT · Renzo e Luciana · the shared apple behind the pails (Version A 12:01:30-12:02:30, then Version B same minute).
#29 GrabCut pieces (cuts.py) -> #32 FK rigs (hip > neck > head, hip > elbow > forearm+apple) -> #45 occlusion DAG.
Puppet keys sampled on twos (12 drawings/s); clock and camera computed from the fixture clock. Rendered with kit.Film."""
import os, sys, json, math, numpy as np, cv2
from PIL import Image
B = os.path.dirname(os.path.abspath(__file__)); C = B + '/cache'
sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films')
import kit
SW, SH = 1296, 729
rig = json.load(open(C + '/rig.json'))
def load(name, gamma=1.0, lo=0, hi=255):
    a = np.asarray(Image.open(f'{C}/{name}.png')).astype(np.float32)
    g = np.clip((a[..., 0] - lo) / (hi - lo), 0, 1) ** gamma * 255     # per-piece levels/gamma only
    return np.dstack([g, a[..., 3] / 255.0])
P = {  # per-piece grade toward the reference key (median ~122, p95 >= 220)
    'lu_body': load('lu_body', 1.0, 10, 235), 'lu_head': load('lu_head', 1.05, 8, 238), 'lu_arm': load('lu_arm', 1.05, 8, 238),
    're_body': load('re_body', .9, 0, 225), 're_head': load('re_head', 1.1, 10, 245), 'foreman_back': load('foreman_back', 1.0, 15, 235),
    'apple': load('apple', 1.05, 8, 238)}
plate = np.asarray(Image.open(C + '/plate.png')).astype(np.float32)
plate = np.clip((plate - 14) / (222 - 14), 0, 1) ** 1.22 * 246 + 4    # plate levels: pull the pale wall down into the mid belly
occ = np.load(C + '/occ.npy').astype(np.float32) / 255
occ = cv2.GaussianBlur(occ, (3, 3), 0)
DX0, DY0, DX1, DY1 = np.load(C + '/door.npy')
backroom = np.asarray(Image.open(C + '/backroom.png')).astype(np.float32)
def rgba(path):
    a = np.asarray(Image.open(path)).astype(np.float32); return np.dstack([a[..., 0], a[..., 3] / 255])
doorframe, leaf = rgba(C + '/doorframe.png'), rgba(C + '/leaf.png')
CX, CY, CR = np.load(C + '/clock.npy')
def bite(piece, centre, r, seed):
    """cut a bite out of the apple with scissor arcs; the cut edge shows the print's pale paper core."""
    p = piece.copy(); h, w = p.shape[:2]; Y, X = np.mgrid[0:h, 0:w]
    rng = np.random.default_rng(seed); ang = np.arctan2(Y - centre[1], X - centre[0])
    rr = r * (1 + .12 * np.sin(ang * 5 + rng.uniform(0, 6)))         # scalloped tooth-arc
    dist = np.hypot(X - centre[0], Y - centre[1])
    cut = dist < rr; rim = (dist >= rr) & (dist < rr + 2.2) & (p[..., 1] > .5)
    p[cut, 1] = 0; p[rim, 0] = 214
    return p
# arm piece: apple centre at (65,32) in piece coords.  bite 1 (Renzo, side toward him when lifted), bite 2 (Luciana, top)
A0 = P['lu_arm']; A1 = bite(A0, (32, 22), 15, 1); A2 = bite(A1, (80, 6), 13, 2)
def warp(piece, pivot, world, ang, s):
    M = cv2.getRotationMatrix2D((float(pivot[0]), float(pivot[1])), ang, s)
    M[:, 2] += np.array(world) - np.array(pivot)
    return cv2.warpAffine(piece, M, (SW, SH), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderValue=(0, 0)), M
def apply(M, p): return M @ np.array([p[0], p[1], 1.0])
def over(canvas, lay, shadow=True, off=(7, 6), blur=7, dark=.38):
    a = lay[..., 1]
    if shadow:   # soft contact shadow cast down-right from the plate's upper-left key light
        sh = cv2.GaussianBlur(np.roll(np.roll(a, off[1], 0), off[0], 1), (0, 0), blur) * dark
        canvas *= (1 - sh)
    canvas[:] = canvas * (1 - a) + lay[..., 0] * a
# ------------------------------------------------------------------ timing ----
FPS = 24
SEG = [('A', 0.0, 5.0, 7.5), ('B', 5.25, 9.25, 45.0)]   # (version, shot t0, t1, film t at t0)
def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def keys(kf, t):
    """piecewise eased interpolation of joint keys [(t, value), ...]"""
    if t <= kf[0][0]: return kf[0][1]
    for (ta, va), (tb, vb) in zip(kf, kf[1:]):
        if t <= tb: return va + (vb - va) * ease((t - ta) / (tb - ta))
    return kf[-1][1]
# Version A, in version-local fixture seconds tau (12:00 + tau/5 min).  t_film = tau for A.
#   Luciana forearm (elbow pin, deg ccw): 0 = apple at her own mouth; 41 = at Renzo's mouth.
LA_ARM = [(7.5, 30), (8.3, 41), (8.9, 41), (9.4, 30), (9.7, 33), (10.0, 40), (10.4, 41), (10.8, 22), (11.0, 2), (11.6, 0), (12.5, 6)]
LA_HEAD = [(7.5, 4), (8.4, 6), (9.0, 8), (10.0, 9), (10.6, 4), (11.0, -4), (11.4, -6), (11.8, 0), (12.5, 2)]
LA_HIP = [(7.5, -3), (8.4, -5), (9.6, -4), (10.4, -6), (11.0, -1), (12.5, -2)]
#   Renzo head (neck pin, deg ccw): +24 = chin up to the clock (watch); -3 = forward to the apple
RA_HEAD = [(7.5, 32), (8.0, 31), (8.3, -1), (8.5, -4), (8.9, -2), (9.25, 36), (9.4, 32), (12.5, 33)]
RA_HIP = [(7.5, 1), (8.4, -1.5), (9.2, 1), (12.5, 1.5)]
# Version B: Renzo alone; head swings clock -> empty place (her spot, low right) on a tightening rhythm
RB_HEAD = [(45.0, 32), (45.6, 32), (46.0, -13), (46.1, -15), (46.6, -14), (47.0, 35), (47.1, 32), (47.6, 32), (47.85, -14), (48.4, -14), (48.65, 34), (49.0, 32)]
RB_HIP = [(45.0, 1), (46.0, -2), (47.0, 1), (48.0, -2), (49.0, 1)]
# positions (stage px) and scales
SL, SR, SF = .80, .90, 1.25
EL = np.array([770.0, 640.0])          # Luciana's elbow pin (hidden behind the pails)
HL = None
F_BASE = np.array([212.0, 492.0])
def _solve_renzo():
    lb = rig['lu_body']['pivots']; la = rig['lu_arm']['pivots']
    hip_world = EL + (np.array(lb['hip']) - np.array(lb['elbow'])) * SL
    _, M = warp(P['lu_body'][..., :1].repeat(2, -1) * 0, lb['hip'], hip_world, -5, SL)
    _, Ma = warp(A0[..., :1].repeat(2, -1) * 0, la['elbow'], apply(M, lb['elbow']), -5 + 41, SL)
    apple = apply(Ma, la['apple'])
    pb = rig['re_body']['pivots']; ph = rig['re_head']['pivots']
    mouth_head = np.array([140.0, 150.0])
    R = lambda a: np.array([[math.cos(math.radians(a)), math.sin(math.radians(a))], [-math.sin(math.radians(a)), math.cos(math.radians(a))]])
    m_rel_neck = R(-1.5 - 4) @ ((mouth_head - ph['neck']) * SR)
    neck_rel_hip = R(-1.5) @ ((np.array(pb['neck']) - pb['hip']) * SR)
    return apple - np.array([20.0, -4.0]) - m_rel_neck - neck_rel_hip
      # foreman, at his desk inside the doorway, back to the floor
R_HIP = _solve_renzo(); print('Renzo hip', R_HIP)
def q(t): return math.floor(t * 12) / 12          # on twos
def frame_img(t):
    seg = [s for s in SEG if s[1] <= t < s[2] + 1e-9]
    if not seg: return np.zeros((540, 960), np.float32)
    ver, t0, t1, f0 = seg[0]; tf = f0 + (t - t0); tq = f0 + q(t - t0)
    tau = tf if ver == 'A' else tf - 37.0
    cv = plate.copy()
    # back room + foreman (back turned: facing = OFFICE on [12:01,12:04)); tiny reading sway on twos
    room = cv[DY0:DY1, DX0:DX1]; room[:] = backroom
    sway = 0.8 * math.sin(tq * 1.3) + (0.6 if (tq % 3.0) < 1.5 else 0)
    lay, _ = warp(P['foreman_back'], rig['foreman_back']['pivots']['base'], F_BASE, sway, SF)
    m = np.zeros((SH, SW), np.float32); m[DY0:DY1, DX0:DX1] = 1; lay[..., 1] *= m
    over(cv, lay, off=(4, 3), blur=4, dark=.3)
    over(cv, doorframe, off=(4, 5), blur=4, dark=.5)
    # Renzo (FK: hip -> neck -> head)
    rh = keys(RA_HIP if ver == 'A' else RB_HIP, tq); rk = keys(RA_HEAD if ver == 'A' else RB_HEAD, tq)
    pb = rig['re_body']['pivots']; ph = rig['re_head']['pivots']
    def renzo():
        lay, M = warp(P['re_body'], pb['hip'], R_HIP, rh, SR); over(cv, lay)
        lay, _ = warp(P['re_head'], ph['neck'], apply(M, pb['neck']), rh + rk, SR); over(cv, lay, off=(6, 5), blur=5)
    if ver == 'B': renzo()
    if ver == 'A':
        # Luciana (FK: hip -> neck -> head; hip -> elbow -> forearm/hand/apple). Body placed so its elbow pin sits at EL.
        lb = rig['lu_body']['pivots']; lh = rig['lu_head']['pivots']; la = rig['lu_arm']['pivots']
        hipang = keys(LA_HIP, tq)
        hip_world = EL + (np.array(lb['hip']) - np.array(lb['elbow'])) * SL
        lay, M = warp(P['lu_body'], lb['hip'], hip_world, hipang, SL); over(cv, lay)
        renzo()
        lay, _ = warp(P['lu_head'], lh['neck'], apply(M, lb['neck']), hipang + keys(LA_HEAD, tq), SL); over(cv, lay, off=(6, 5), blur=5)
        piece = A0 if tq < 8.5 else (A1 if tq < 11.0 else A2)            # bite substitutions on exact frames
        lay, Ma = warp(piece, la['elbow'], apply(M, lb['elbow']), hipang + keys(LA_ARM, tq), SL); over(cv, lay, off=(8, 7), blur=6, dark=.42)
    over(cv, np.dstack([plate, occ]), shadow=False)                       # the pail pile is in front of both of them
    if ver == 'B':                                                          # the uneaten apple on his pail lid, in front of him
        lay, _ = warp(P['apple'], rig['apple']['pivots']['c'], (590, 528), -8, SL); over(cv, lay, off=(5, 4), blur=3, dark=.5)
    over(cv, leaf, off=(5, 5), blur=5, dark=.45)
    # paper clock hands from the fixture clock: minute 6 deg per fixture minute; hour 0.5 deg per minute
    mins = tau / 5.0
    hl = np.zeros((SH, SW), np.float32)
    def hand(angdeg, L, w):
        a = math.radians(angdeg - 90); b = a + math.pi / 2
        pts = [(CX + w * math.cos(b), CY + w * math.sin(b)), (CX + L * math.cos(a), CY + L * math.sin(a)),
               (CX - w * math.cos(b), CY - w * math.sin(b)), (CX - 5 * math.cos(a), CY - 5 * math.sin(a))]
        cv2.fillPoly(hl, [np.round(np.array(pts) * 8).astype(np.int32)], 1.0, lineType=cv2.LINE_AA, shift=3)
    hand(0.5 * mins, CR * .5, 3.0); hand(6.0 * mins, CR * .8, 2.2); cv2.circle(hl, (int(CX), int(CY)), 3, 1.0, -1)
    over(cv, np.dstack([np.full_like(hl, 20), hl]), off=(2, 2), blur=1.2, dark=.35)
    # camera: A pushes in WIDE-ish -> MEDIUM; B pulls back. z is relative to the stage (1.0 = whole stage = WIDE).
    u = ease((t - t0) / (t1 - t0)); z = 1.16 + .14 * u if ver == 'A' else 1.30 - .14 * u
    cw, ch = SW / z, SH / z
    cxm, cym = 610.0, 322.0
    k = (z - 1) / .30; cx = 648 + (cxm - 648) * k; cy = 364.5 + (cym - 364.5) * k
    x0 = min(max(cx - cw / 2, 0), SW - cw); y0 = min(max(cy - ch / 2, 0), SH - ch)
    M = np.array([[960 / cw, 0, -x0 * 960 / cw], [0, 540 / ch, -y0 * 540 / ch]])
    return cv2.warpAffine(cv, M, (960, 540), flags=cv2.INTER_AREA)
TOTAL = 9.25
film = kit.Film('test-shot', seconds=TOTAL)
def pic(t, ink):
    ink._grain = False                                  # no faux grain: the grain is the prints' own
    g = np.clip(frame_img(t), 0, 255).astype(np.uint8)
    ink.img = Image.fromarray(np.stack([g] * 3, -1)).convert('RGBA')
film.picture(pic)
SND = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana/test-shot/sound'
def wav(path):
    import wave
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2: x = x.reshape(-1, 2).mean(1)
    return x
def snd(mix):
    tick = wav(SND + '/Clock_ticking.wav')
    for (ver, t0, t1, f0) in SEG:
        n = int((t1 - t0) * kit.RATE); seg = tick[int(3 * kit.RATE): int(3 * kit.RATE) + n]
        seg = seg * np.minimum(1, np.minimum(np.arange(len(seg)), len(seg) - np.arange(len(seg))) / 800)
        mix.add(seg, t0, gain=.55 if ver == 'A' else .8)                  # B: the ticking rises in the mix
        mix.room(t0, t1 - t0, gain=.035)
        # foreman's sheets: two soft paper rustles
        for tt in (0.6, 3.1):
            r = mix.band(mix.noise(.35, 'white'), 2500, 7000) * mix.env(int(.35 * kit.RATE), .02, .3)
            mix.add(r * .5, t0 + tt, gain=.25, pan=-.6)
    for tf in (8.5, 11.0):   # bite crunches (kit synthesis, declared), on the substitution frames
        tt = tf - 7.5; n = int(.18 * kit.RATE)
        cr = mix.band(mix.noise(.18, 'white'), 1200, 5000) * mix.env(n, .002, .12)
        mix.add(cr, tt, gain=.5, pan=0.05); mix.click(tt, gain=.25, bright=3000)
film.sound(snd)
if __name__ == '__main__':
    from pathlib import Path
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        for t in [float(x) for x in sys.argv[2:]]:
            Image.fromarray(np.clip(frame_img(t), 0, 255).astype(np.uint8)).save(f'{C}/still_{t:05.2f}.png')
    else:
        film.render(out_dir=Path('/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana'))
