"""TEST SHOT r2 · Renzo e Luciana · the shared apple behind the pails (Version A 12:01:30-12:02:30 -> Version B same minute).
#29 GrabCut pieces (cuts2.py, hi-res LoC master-TIFF crops) -> #32 FK rigs (hip > neck > head; hip > elbow > forearm > grip > apple)
-> #45 occlusion DAG: wall plate < CAPOREPARTO doorway (real casing + back room) < foreman < Luciana body/head < Renzo
< Luciana forearm + apple < NEAR pail pile < paper clock hands.  Keys on twos (12 drawings/s); clock + camera from the fixture clock."""
import os, sys, json, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
B = os.path.dirname(os.path.abspath(__file__)); C = B + '/cache2'
sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films')
import kit
HI = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana/test-shot/r2/hi'
SW, SH = 1296, 729
rig = json.load(open(C + '/rig.json'))
def lv(g, lo, hi, gamma): return np.clip((g - lo) / (hi - lo), 0, 1) ** gamma * 255     # per-piece levels/gamma only
def load(name, lo=0, hi=255, gamma=1.0):
    a = np.asarray(Image.open(f'{C}/{name}.png')).astype(np.float32)
    return np.dstack([lv(a[..., 0], lo, hi, gamma), a[..., 3] / 255.0])
P = {'lu_body': load('lu_body', 0, 240, 1.08), 'lu_head': load('lu_head', 0, 236, 1.0), 'lu_arm': load('lu_arm', 0, 236, 1.0),
     're_body': load('re_body', 14, 205, 1.0), 're_head': load('re_head', 16, 232, 1.05), 'apple': load('apple', 8, 238, 1.0),
     'door': load('door_empty', 18, 236, 1.0), 'foreman': load('foreman', 18, 236, 1.0), 'pails': load('pails', 14, 215, 1.0)}
# ---- wall plate (Russell Lee 8c01492u, K=7 crop -> 1296x729 by area averaging: a downsample, never an enlargement)
plate = np.asarray(Image.open(HI + '/plate_8c01492.png').convert('L'))
plate = cv2.resize(plate, (SW, SH), interpolation=cv2.INTER_AREA)
CX, CY, CR = 604.5, 89.5, 45.7
ring = np.zeros_like(plate); cv2.circle(ring, (int(CX), int(CY)), int(CR * .62), 255, -1)
hands = cv2.dilate(((plate < 110) & (ring > 0)).astype(np.uint8) * 255, np.ones((3, 3), np.uint8))
plate = cv2.inpaint(plate, hands, 3, cv2.INPAINT_TELEA).astype(np.float32)   # photographed hands lifted off; paper hands drawn per frame
plate = lv(plate, 22, 218, 1.0)
# multiplane focus: the camera is focused on the couple (near plane); the wall 2-3 m behind them sits slightly outside the depth of field
plate = cv2.GaussianBlur(plate, (0, 0), .75)
# ---- handmade typed CAPOREPARTO card (diegetic sign), pinned above the door casing
sign = Image.new('L', (178, 30), 214); sd = ImageDraw.Draw(sign)
sd.text((11, 5), 'CAPOREPARTO', font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 17), fill=34)
sign = np.asarray(sign.rotate(-1.2, expand=True, resample=Image.BICUBIC, fillcolor=0)).astype(np.float32)
sign_a = (sign > 0).astype(np.float32); sign_a = cv2.GaussianBlur(sign_a, (0, 0), .6)
def warp(piece, pivot, world, ang, s):
    M = cv2.getRotationMatrix2D((float(pivot[0]), float(pivot[1])), ang, s)
    M[:, 2] += np.array(world, float) - np.array(pivot, float)
    return cv2.warpAffine(piece, M, (SW, SH), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderValue=(0, 0)), M
def apply(M, p): return M @ np.array([p[0], p[1], 1.0])
def over(cv, lay, shadow=True, off=(10, 8), blur=10, dark=.30):
    a = lay[..., 1]
    if shadow:   # soft cast shadow on what is behind, down-right of the plate's upper-left key light
        sh = cv2.GaussianBlur(np.roll(np.roll(a, off[1], 0), off[0], 1), (0, 0), blur) * dark
        cv *= (1 - sh)
    cv[:] = cv * (1 - a) + lay[..., 0] * a
def bite(piece, centre, r, seed):
    """cut a bite out of the apple cut-out with a scalloped scissor arc; the cut rim shows the print's pale core."""
    p = piece.copy(); h, w = p.shape[:2]; Y, X = np.mgrid[0:h, 0:w]
    ang = np.arctan2(Y - centre[1], X - centre[0]); rng = np.random.default_rng(seed)
    rr = r * (1 + .12 * np.sin(ang * 5 + rng.uniform(0, 6))); dist = np.hypot(X - centre[0], Y - centre[1])
    cut = dist < rr; rim = (dist >= rr) & (dist < rr + 2.0) & (p[..., 1] > .5)
    p[cut, 1] = 0; p[rim, 0] = 206
    return p
AP0 = P['apple']; AP1 = bite(AP0, (70, 30), 13, 1)            # bite 1 on Renzo's side (right)
# ---- geometry (stage px)
DS, DOFF = .69, np.array([-100.0, -12.0])                      # doorway piece: real casing scaled to ~620 px tall, cut by frame left
door_xy = DOFF + np.array(rig['door']['crop'][:2]) * DS
F_FEET = DOFF + np.array([280.0, 728.0]) * DS
SL, SR, SA = .60, .75, .66                                     # Luciana, Renzo, apple scales (heads ~135 px)
PS, P_XY = .62, np.array([330.0, 360.0])                       # near pail pile
L_HIP = np.array([470.0, 584.0])
def lu_fk(hip_ang, neck_ang, elbow_ang):
    lb, lh, la = rig['lu_body']['pivots'], rig['lu_head']['pivots'], rig['lu_arm']['pivots']
    _, Mb = warp(np.zeros((2, 2, 2), np.float32), lb['hip'], L_HIP, hip_ang, SL)
    _, Ma = warp(np.zeros((2, 2, 2), np.float32), la['elbow'], apply(Mb, lb['elbow']), hip_ang + elbow_ang, SL)
    return Mb, Ma, apply(Ma, la['grip'])
FEED = 7.0                                                     # elbow angle (deg ccw) at which the apple reaches his mouth
_, _, GRIP_FEED = lu_fk(-2, 0, FEED)
APPLE_OFF = np.array([-2.0, 9.0])                              # apple centre under her pinching fingertips
MOUTH_AT = GRIP_FEED + APPLE_OFF + np.array([24.0, -3.0])      # his mouth meets the apple's right side
def re_fk(hip_ang, head_ang, hip_world):
    pb, ph = rig['re_body']['pivots'], rig['re_head']['pivots']
    _, Mb = warp(np.zeros((2, 2, 2), np.float32), pb['hip'], hip_world, hip_ang, SR)
    _, Mh = warp(np.zeros((2, 2, 2), np.float32), ph['neck'], apply(Mb, pb['neck']), hip_ang + head_ang, SR)
    return Mb, Mh, apply(Mh, ph['mouth'])
R_BITE_HEAD, R_BITE_HIP = 9.0, 3.0                             # head dipped, torso leaning in, at the bite
_, _, m0 = re_fk(R_BITE_HIP, R_BITE_HEAD, np.zeros(2))
R_HIP = MOUTH_AT - m0                                          # solve the hip so the FK chain lands his mouth on the apple
print('Renzo hip', R_HIP, 'grip', GRIP_FEED)
# ---- timing
SEG = [('A', 0.0, 5.5, 7.5), ('B', 5.5, 9.5, 45.0)]            # (version, shot t0, t1, film t at t0)
def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def keys(kf, t):
    if t <= kf[0][0]: return kf[0][1]
    for (ta, va), (tb, vb) in zip(kf, kf[1:]):
        if t <= tb: return va + (vb - va) * ease((t - ta) / (tb - ta))
    return kf[-1][1]
# Version A (film seconds).  Luciana: elbow lifts the apple (FEED) and holds it there through the defining frame (t=10)
LA_ELB = [(7.5, -6), (8.1, FEED + 1.2), (8.25, FEED), (8.9, FEED), (9.3, FEED - 2.5), (9.7, FEED + .6), (9.85, FEED), (11.6, FEED), (12.0, FEED + 1.5), (12.15, FEED), (13.0, FEED)]
LA_NECK = [(7.5, 1), (8.3, 2.5), (9.4, -1.5), (10.4, -3), (11.0, 0), (13.0, 1.5)]   # her head tips a little: towards him, then towards the door
LA_HIP = [(7.5, -3), (8.3, -1.5), (9.4, -2.2), (13.0, -1.8)]
#   Renzo head (neck pin, deg ccw; facing left): +9 = dipped to the apple; -23 = chin up to the clock (watch); overshoot on the turns
RA_HEAD = [(7.5, -23), (8.05, -23), (8.35, R_BITE_HEAD + 1.5), (8.45, R_BITE_HEAD), (8.95, R_BITE_HEAD), (9.25, -26), (9.35, -23), (11.55, -23), (11.8, R_BITE_HEAD + 1), (11.9, R_BITE_HEAD), (13.0, R_BITE_HEAD - 1)]
RA_HIP = [(7.5, 0), (8.35, R_BITE_HIP), (9.0, R_BITE_HIP), (9.4, .5), (11.6, .5), (11.9, R_BITE_HIP), (13.0, R_BITE_HIP)]
BITES = [8.45, 11.9]                                           # apple substitutions (exact frames)
# Version B: Renzo alone; head swings clock (chin up) -> her empty place (down, left); the uneaten apple on the pail top before him
RB_HEAD = [(45.0, -23), (45.6, -23), (45.95, 14), (46.05, 15.5), (46.7, 14), (47.0, -26), (47.1, -23), (47.6, -23), (47.85, 15), (48.45, 14), (48.7, -24), (49.0, -23)]
RB_HIP = [(45.0, .5), (46.0, 4), (47.0, .5), (48.0, 4), (49.0, .5)]
def q(t): return math.floor(t * 12 + 1e-6) / 12                # on twos at 24 fps
pails_lay, _ = warp(P['pails'], (0, 0), P_XY, 0, PS)
door_lay, _ = warp(P['door'], (0, 0), door_xy, 0, DS)
def frame_img(t):
    seg = [s for s in SEG if s[1] <= t < s[2] + 1e-9]
    ver, t0, t1, f0 = seg[0]; tf = f0 + (t - t0); tq = f0 + q(t - t0)
    tau = tf if ver == 'A' else tf - 37.0
    cv = plate.copy()
    over(cv, door_lay, off=(6, 5), blur=6, dark=.25)
    # foreman: back turned (facing OFFICE on [12:01,12:04)); reading sway pinned at his feet, on twos
    sway = .7 * math.sin(tq * 1.1) + (.35 if (tq % 2.6) < 1.3 else -.2)
    lay, _ = warp(P['foreman'], rig['foreman']['pivots']['feet'], F_FEET, sway, DS); over(cv, lay, shadow=False)
    m = np.zeros((SH, SW), np.float32); y0d = int(door_xy[1]); cv[:0] = 0
    sx = 18; sy = 6
    cv[sy:sy + sign.shape[0], sx:sx + sign.shape[1]] = cv[sy:sy + sign.shape[0], sx:sx + sign.shape[1]] * (1 - sign_a) + sign * sign_a
    pb, ph = rig['re_body']['pivots'], rig['re_head']['pivots']
    if ver == 'A':
        lb, lh = rig['lu_body']['pivots'], rig['lu_head']['pivots']
        ha = keys(LA_HIP, tq); Mb, Ma, grip = lu_fk(ha, 0, keys(LA_ELB, tq))
        lay, _ = warp(P['lu_head'], lh['neck'], apply(Mb, lb['neck']), ha + keys(LA_NECK, tq), SL); over(cv, lay)
        lay, _ = warp(P['lu_body'], lb['hip'], L_HIP, ha, SL); over(cv, lay)
    rh = keys(RA_HIP if ver == 'A' else RB_HIP, tq); rk = keys(RA_HEAD if ver == 'A' else RB_HEAD, tq)
    lay, Mb2 = warp(P['re_body'], pb['hip'], R_HIP, rh, SR); over(cv, lay)
    lay, _ = warp(P['re_head'], ph['neck'], apply(Mb2, pb['neck']), rh + rk, SR); over(cv, lay, off=(8, 7), blur=8)
    if ver == 'A':
        nb = sum(tq >= b for b in BITES); ap = AP0 if nb == 0 else AP1 if nb == 1 else bite(AP1, (66, 14), 12, 2)
        ang = ha + keys(LA_ELB, tq)
        lay, _ = warp(ap, rig['apple']['pivots']['c'], grip + APPLE_OFF, ang * .5, SA); over(cv, lay, off=(7, 6), blur=6, dark=.35)
        lay, _ = warp(P['lu_arm'], rig['lu_arm']['pivots']['elbow'], apply(Mb, rig['lu_body']['pivots']['elbow']), ang, SL)
        over(cv, lay, off=(9, 8), blur=8, dark=.32)                       # fingers in front of the apple they pinch
    over(cv, pails_lay, off=(12, 10), blur=12, dark=.30)                   # the near pile is in front of both of them
    if ver == 'B':                                                          # the uneaten apple left on the pail top in front of him
        lay, _ = warp(AP0, rig['apple']['pivots']['c'], (700, 482), -6, SA); over(cv, lay, off=(6, 5), blur=3, dark=.5)
    # paper clock hands on the real dial, from the fixture clock: minute 6 deg per fixture minute (= 5 s of film)
    mins = tau / 5.0; hl = np.zeros((SH, SW), np.float32)
    def hand(angdeg, L, w):
        a = math.radians(angdeg - 90); b = a + math.pi / 2
        pts = [(CX + w * math.cos(b), CY + w * math.sin(b)), (CX + L * math.cos(a), CY + L * math.sin(a)),
               (CX - w * math.cos(b), CY - w * math.sin(b)), (CX - 6 * math.cos(a), CY - 6 * math.sin(a))]
        cv2.fillPoly(hl, [np.round(np.array(pts) * 8).astype(np.int32)], 1.0, lineType=cv2.LINE_AA, shift=3)
    hand(0.5 * mins, CR * .48, 3.0); hand(6.0 * mins, CR * .74, 2.0); cv2.circle(hl, (int(CX), int(CY)), 3, 1.0, -1)
    over(cv, np.dstack([np.full_like(hl, 22), hl]), off=(2, 2), blur=1.2, dark=.35)
    # camera: A pushes WIDE-ish (1.2x) -> MEDIUM (1.35x); B pulls back.  Door jamb and clock stay in frame.
    u = ease((t - t0) / (t1 - t0)); z = 1.20 + .15 * u if ver == 'A' else 1.35 - .15 * u
    cw, ch = SW / z, SH / z
    k = (z - 1.20) / .15; cx = 556 + (540 - 556) * k; cy = 300 + (290 - 300) * k
    x0 = min(max(cx - cw / 2, 0), SW - cw); y0 = min(max(cy - ch / 2, 0), SH - ch)
    M = np.array([[960 / cw, 0, -x0 * 960 / cw], [0, 540 / ch, -y0 * 540 / ch]])
    return cv2.warpAffine(cv, M, (960, 540), flags=cv2.INTER_AREA)
TOTAL = 9.5
film = kit.Film('test-shot', seconds=TOTAL)
def pic(t, ink):
    ink._grain = False                                                     # no faux grain: the grain is the prints' own
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
        mix.add(seg, t0, gain=.5 if ver == 'A' else .8, pan=-.25)          # B: the ticking rises in the mix
        mix.room(t0, t1 - t0, gain=.035)
        for tt in (0.7, 3.3):                                              # the foreman's time sheets, through the doorway (left)
            r = mix.band(mix.noise(.35, 'white'), 2500, 7000) * mix.env(int(.35 * kit.RATE), .02, .3)
            mix.add(r * .5, t0 + tt, gain=.18, pan=-.7)
    for tf in BITES:                                                       # bite crunches (kit synthesis, declared) on the substitution frames
        tt = tf - 7.5; n = int(.2 * kit.RATE)
        cr = mix.band(mix.noise(.2, 'white'), 1200, 5000) * mix.env(n, .002, .13)
        mix.add(cr, tt, gain=.5, pan=.15); mix.click(tt, gain=.22, bright=3000)
film.sound(snd)
if __name__ == '__main__':
    from pathlib import Path
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        for t in [float(x) for x in sys.argv[2:]]:
            Image.fromarray(np.clip(frame_img(t), 0, 255).astype(np.uint8)).save(f'{C}/f_{t}.png')
    else:
        film.render(out_dir=Path('/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana'))
