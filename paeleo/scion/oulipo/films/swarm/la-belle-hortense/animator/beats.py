"""Every animated beat other than V.3, as frame functions (sub-frame -> RGB float) + prepared clips.
Clips carry no type (typesetting is the print-sound unit's / editor's).  Time inside a beat is local (0..1.5 s);
film time = slot start + local."""
import os, sys, json, math
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene as S
from scene import (W, H, FPS, T, R, SY, SX, tp, over, paint, sm, RUN, PIECES, SIL, BENCH, KEY, KPIV, VISF, VISB)

# ---------------------------------------------------------------- the wide station (meadow plate, sky as cream paper)
class View:
    """camera over the wide plate: plate px -> screen px = (p - c) * z + centre.  Planes: far (above horizon,
    ratio 0.35) and ground (ratio 1.0); at rest both show the same photograph."""
    BASE = 0.85
    def __init__(self, z=1.0, c=(560.0, 420.0)):
        self.z, self.c = z, c
    def k(self): return self.BASE * self.z
    def pt(self, p, pan=0.0, ratio=1.0):
        return ((p[0] - self.c[0]) * self.k() + W / 2 - pan * ratio, (p[1] - self.c[1]) * self.k() + H / 2)
_bg = {}
REST_FOLD = 0.84
HZ = 470                                       # horizon row of the meadow plate
def wide_bg(v, pan=0.0):
    key = round(v.k(), 4)
    if key not in _bg:
        _bg[key] = cv2.resize(S.plate('meadow'), None, fx=v.k(), fy=v.k(), interpolation=cv2.INTER_AREA)
    img = _bg[key]
    fr = np.zeros((H, W, 3), np.float32)
    for ratio, y0, y1 in ((0.35, 0, HZ + 6), (1.0, HZ - 6, 960)):
        ox = (v.c[0] * v.k() - W / 2) + pan * ratio; oy = v.c[1] * v.k() - H / 2
        M = np.float32([[1, 0, -ox], [0, 1, -oy]])
        a = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        rows = (np.arange(H) + oy) / v.k()
        m = np.clip((rows - y0) / 8, 0, 1) * np.clip((y1 - rows) / 8, 0, 1)
        fr = over(fr, a, m[:, None]) if ratio < 1 else over(fr, a, np.clip((rows - HZ + 6) / 12, 0, 1)[:, None])
    return fr

BENCH_AT = (760.0, 690.0)          # bench feet (plate coords)
BENCH_S = 0.85
SEAT = (225.0, 146.0)              # point on the seat (bench piece coords) where the coat lies
def bench_M(v):
    x, y = v.pt(BENCH_AT); s = BENCH_S * v.z
    return T(x - 220 * s, y - 380 * s) @ np.diag([s, s, 1.0])
def seat_pt(v): return tp(bench_M(v), SEAT)
def draw_bench(fr, v, sil=False):
    b = BENCH.copy()
    if sil: b[..., :3] = 0
    return paint(fr, b, bench_M(v))
def coat_on_bench(fr, v, fold=REST_FOLD, lift=0.0, glint=0.0, key_ang=None, sil=False):
    x, y = seat_pt(v)
    fr, L = S.coat_folded_draw(fr, x - 44 * v.z, y - 18 * v.z, 0.55 * v.z, fold, lift, sil=sil, glint=glint, key_on=key_ang)
    return fr
def key_on_coat_pt(v): x, y = seat_pt(v); return x - 40 * v.z, y - 30 * v.z

def shadow(fr, x, y, rx, ry, k=0.55):
    m = np.zeros((H, W), np.float32); cv2.ellipse(m, (int(x), int(y)), (int(rx), int(ry)), 0, 0, 360, 1, -1)
    m = cv2.GaussianBlur(m, (0, 0), max(ry * 0.6, 1))           # the contact shadow is a cut mask, softened
    return fr * (1 - (1 - k) * m[..., None])

VIS_S = 1.5
# ================================================================= beats
def I1(t, sil=False):
    v = View(1.0)
    fr = wide_bg(v)
    fr = draw_bench(fr, v)
    return coat_on_bench(fr, v)

def bell_hang(fr, t_since, x=150, y=-20, s=0.42, theta0=26.0, tau=1.5, sil=False):
    th, cl = S.bell_angles(t_since, theta0, tau)
    fr, Mb, Mc = S.bell_draw(fr, x, y, s, th, cl, sil=sil)
    return fr, th, cl

def visitor_path(t):     # I.2: enters from the far left, walking toward the bench
    u = sm(t / 1.5)
    return (260 + 300 * u, 520 + 160 * u, 0.45 + 0.45 * u)
def I2(t, sil=False):
    v = View(1.0)
    fr = wide_bg(v); fr = draw_bench(fr, v); fr = coat_on_bench(fr, v)
    px, py, s = visitor_path(t)
    x, y = v.pt((px, py))
    fr = shadow(fr, x, y, 22 * s, 5 * s)
    fr, _ = S.walker_draw(fr, VISF, x, y, s * VIS_S, t, hz=0.9)
    fr, th, cl = bell_hang(fr, t - 0.1)
    return fr

def I3(t, sil=False):
    """insert: the handmade envelope on the gravel; the flap hinges open; the key slides out."""
    gnd = S.plate('meadow')
    fr = cv2.resize(gnd[600:960, 200:840], (W, H), interpolation=cv2.INTER_AREA).copy()
    ex, ey = 300, 210
    env = S.ENV.copy(); flap = S.FLAP.copy()
    # key inside: slides up out of the mouth, rotating a little
    u = sm((t - 0.55) / 0.75)
    kx, ky = ex + 200, ey + 120 - 210 * u
    ang = 90 - 25 * u
    fr = paint(fr, env, T(ex, ey))
    # flap: hinge at the envelope's top edge; theta 0 -> 180 deg; foreshortened by cos, reverse printed darker
    th = math.pi * sm(t / 0.5)
    c = math.cos(th)
    f2 = flap.copy()
    if c < 0: f2[..., :3] *= 0.80
    Mf = T(ex, ey) @ SY((0, 0), c if abs(c) > 0.02 else 0.02)
    fr = paint(fr, f2, Mf)
    if u > 0:                                   # the key above the mouth (inside the envelope it is hidden)
        keyfr = S.draw_key(fr.copy(), kx, ky, ang, s=1.5)
        mouth = np.zeros((H, W), np.float32); mouth[:ey + 1] = 1
        fr = over(fr, keyfr, mouth[..., None])
    return fr

def lay_key_state(t):
    """I.4: she bows (0.15-0.75), the key travels from her hands to the coat along an arc, she straightens."""
    bend = sm((t - 0.10) / 0.45) * (1 - sm((t - 0.95) / 0.45))
    u = sm((t - 0.30) / 0.45)
    return bend, u
def I4(t, sil=False, stage=True):
    v = View(1.0)
    fr = wide_bg(v) if (stage and not sil) else np.ones((H, W, 3), np.float32)
    fr = draw_bench(fr, v, sil=sil); fr = coat_on_bench(fr, v, sil=sil)
    bend, u = lay_key_state(t)
    x, y = v.pt((560, 690))
    fr = shadow(fr, x, y, 18, 4) if not sil else fr
    fr, hand = S.walker_draw(fr, VISF, x, y, 0.9 * VIS_S, 0.0, hz=0.0, sil=sil, bend=bend)
    hx_, hy_ = hand[0] + 18 + 30 * bend, hand[1] + 40 * bend
    kx, ky = key_on_coat_pt(v)
    if u < 1:
        px = hx_ + (kx - hx_) * u; py = hy_ + (ky - hy_) * u - 30 * math.sin(math.pi * u)
        fr = S.draw_key(fr, px, py, 30 + 40 * u, s=0.5, sil=sil)
    else:
        if not sil: fr = shadow(fr, kx + 2, ky + 4, 10, 2.5, 0.6)
        fr = S.draw_key(fr, kx, ky, 70, s=0.5, sil=sil)
    return fr

def I5(t, sil=False):
    v = View(1.0)
    fr = wide_bg(v); fr = draw_bench(fr, v); fr = coat_on_bench(fr, v)
    kx, ky = key_on_coat_pt(v); fr = S.draw_key(fr, kx, ky, 70, s=0.5)
    x, y = v.pt((560, 690))
    fr = shadow(fr, x, y, 18, 4)
    fr, hand = S.walker_draw(fr, VISF, x, y, 0.9 * VIS_S, 0.0, hz=0.0)
    # receipt: drift + flutter (rotation and flip), terminal velocity ~ 170 px/s, lands on the gravel
    x0, y0 = hand[0] + 20, hand[1] + 10
    yl = y + 6
    tt = min(t, 1.25)
    yy = y0 + 170 * tt - 60 * math.sin(2 * math.pi * 1.4 * tt) * math.exp(-tt) * 0.4
    xx = x0 + 60 * math.sin(2 * math.pi * 0.9 * tt) + 30 * tt
    if yy >= yl: yy = yl
    ang = 40 * math.sin(2 * math.pi * 1.1 * tt); flip = math.cos(2 * math.pi * 0.8 * tt) if yy < yl else 0.25
    return S.ticket_draw(fr, xx, yy, ang, flip * 0.36 if False else flip)

def I6(t, sil=False):
    z = 1.0 + 0.07 * sm(t / 1.5)
    v = View(z, (560 - 60 * sm(t / 1.5), 400 - 30 * sm(t / 1.5)))      # slow push toward the shed door
    fr = wide_bg(v); fr = draw_bench(fr, v); fr = coat_on_bench(fr, v)
    kx, ky = key_on_coat_pt(v); fr = S.draw_key(fr, kx, ky, 70, s=0.5 * z)
    u = t / 1.5
    x, y = v.pt((600 + 330 * u, 690 - 90 * u))
    fr = shadow(fr, x, y, 16, 4)
    fr, _ = S.walker_draw(fr, VISB, x, y, (0.9 - 0.35 * u) * z * VIS_S * 0.68, t, hz=0.9)
    return fr

def II2(t, sil=False, stage=True):
    """the coat lifted off the bench (unfolding on its hinges); 6-frame brass glint in the fold; cut at 0.9 s,
    through the bench holdout, to the conductor wearing it, rising from behind the bench and walking left."""
    v = View(1.45, (760, 470))
    fr = wide_bg(v) if (stage and not sil) else np.ones((H, W, 3), np.float32)
    if t < 0.9:
        u = sm((t - 0.05) / 0.8)
        fold = REST_FOLD * (1 - u)
        lift = 520 * u ** 1.6
        k = int(t * FPS)
        glint = 1.0 if 6 <= k < 12 else 0.0
        if not sil: fr = draw_bench(fr, v)
        else: fr = draw_bench(fr, v, sil=True)
        fr = coat_on_bench(fr, v, fold=fold, lift=lift, glint=glint, key_ang=(60 if glint or u < 0.25 else None), sil=sil)
    else:
        tt = t - 0.9
        pose, _ = S.walk_pose(tt, 1.0)
        x, y = seat_pt(v)
        hx = x - 70 - 80 * tt; hy = y + 30 - 50 * sm(tt / 0.3)
        M = RUN.mats(hx, hy, 0.42 * v.z * 0.6, 4.0, pose)
        fr = RUN.draw(fr, M, sil=sil)
        fr = draw_bench(fr, v, sil=sil)                            # holdout: the bench plane occludes him
    return fr

def bell_clip(t, t_strike=0.1, theta0=26.0, tau=1.5, sil=False):
    sh = S.plate('shed')
    bg = cv2.resize(sh, (960, 720), interpolation=cv2.INTER_AREA)[110:650].copy()
    fr, th, cl = bell_hang(bg, t - t_strike, x=560, y=-40, s=0.78, theta0=theta0, tau=tau, sil=sil)
    return fr
BELL_SETTLE_T0 = 1.5 - 0.1           # VI.1 follows V.6: t_since at its start
def VI1(t, sil=False):
    # V.6 strike decays with tau 1.5; the settle continues it with an added damper (tau 0.6) so it comes to rest
    th0 = 26.0 * math.exp(-BELL_SETTLE_T0 / 1.5)
    sh = S.plate('shed')
    bg = cv2.resize(sh, (960, 720), interpolation=cv2.INTER_AREA)[110:650].copy()
    w = 2 * math.pi * 1.05; ts = BELL_SETTLE_T0 + t
    th = th0 * math.exp(-t / 0.6) * math.sin(w * ts); cl = 1.35 * th0 * math.exp(-t / 0.45) * math.sin(w * ts - 0.9)
    fr, Mb, Mc = S.bell_draw(bg, 560, -40, 0.78, th, cl)
    return fr

def III4(t, sil=False):
    pan = 160 * t
    v = View(1.0)
    fr = wide_bg(v, pan)
    fr = draw_bench(fr, View(1.0, (560 + pan / 0.85, 420)))
    pose, _ = S.run_pose(t)
    x, y = v.pt((150 + 520 * t, 452), pan, 0.6)
    M = RUN.mats(x, y, 0.14, -8.0, pose)
    return RUN.draw(fr, M)

def IV5(t, sil=False):
    planes = S.run_stage()
    cx = 1500 * t
    fr = np.zeros((H, W, 3), np.float32)
    for p in planes[:3]: p.draw(fr, cx, 3000)
    pose, _ = S.run_pose(t)
    hx = 1700 - 2400 * t                                   # the coat sweeps across the near plane, right -> left
    if -800 < hx < 1800:
        M = RUN.mats(hx, 120, 1.9, 8.0, pose)
        fr = RUN.draw(fr, M, skip=('thighN', 'thighF', 'shinN', 'shinF'))
    planes[3].draw(fr, cx, 3000)
    return fr

def cam_V1(t): return S.VR * t * t / 3.0                  # 0 -> VR over 1.5 s (a = VR/1.5)
def V1(t, sil=False):
    planes = S.run_stage()
    cx = cam_V1(t)
    fr = np.zeros((H, W, 3), np.float32)
    for p in planes[:3]: p.draw(fr, cx, 6000)
    # bench on its own plane (0.8), close
    bx = 520 - 0.8 * cx
    fr = paint(fr, BENCH, T(bx - 220 * 1.1, 470 - 380 * 1.1) @ np.diag([1.1, 1.1, 1.0]))
    planes[3].draw(fr, cx, 6000)
    return fr

V2_CX0 = S.VR * 1.5 * 1.5 / 3.0
def V2(t, sil=False):
    planes = S.run_stage()
    cx = V2_CX0 + S.VR * t
    fr = np.zeros((H, W, 3), np.float32)
    for p in planes[:3]: p.draw(fr, cx, 6000)
    u = t / 1.5
    xx = 900 - 700 * u + 40 * math.sin(7 * t); yy = 470 - 360 * u + 30 * math.sin(4.3 * t + 1) - 120 * math.sin(math.pi * u)
    fr = S.ticket_draw(fr, xx, yy, 25 * math.sin(5.1 * t) + 260 * u, math.cos(2 * math.pi * 1.6 * t))
    if t > 0.9:                                           # the runner catches the camera
        pose, _ = S.run_pose(40.5 + t)
        hx = S.X_LOCK - 760 * (1 - sm((t - 0.9) / 0.6))
        M = RUN.mats(hx, S.HIP_Y + S.bob(40.5 + t), S.SCALE, S.LEAN, pose)
        fr = RUN.draw(fr, M)
    planes[3].draw(fr, cx, 6000)
    return fr

def V4(t, sil=False):
    """film 43.5-45.0: the key is on the grass; the operator brakes, overshoots, comes back and rests on it;
    a red sleeve and hand come down and take it."""
    ft = 43.5 + t
    S.key_screen(43.4)
    planes = S.run_stage()
    xl = S.KX0 - 0.5 * S.DRAG * (S.T_LAND - S.T_DROP) ** 2 + S.cam_x(S.T_LAND)     # key's world x on the ground
    c_end = xl - 560
    t0, t1 = 43.5, 44.2
    if ft <= t0: cx = S.cam_x(ft)
    elif ft >= t1: cx = c_end
    else:
        c0 = S.cam_x(t0); v0 = S.VR; L = t1 - t0; s = (ft - t0) / L
        cx = (2 * s ** 3 - 3 * s ** 2 + 1) * c0 + (s ** 3 - 2 * s ** 2 + s) * L * v0 + (-2 * s ** 3 + 3 * s ** 2) * c_end
    fr = np.zeros((H, W, 3), np.float32)
    for p in planes[:3]: p.draw(fr, cx)
    kx = xl - cx; ky = S.GROUND_Y
    dl = ft - S.T_LAND
    if dl < 0.16: ky -= max(0.0, 46 * dl - 0.5 * 2600 * dl * dl * 0 - 290 * dl * dl)    # the single bounce
    ang = 20 + 690 * (S.T_LAND - S.T_DROP)
    ang = ang + (100 - ang) * sm(dl / 0.4)
    # hand: forearm piece turned down, entering from the top at 44.35, closes on the key at 44.7, lifts away
    th = ft - 44.35
    took = ft >= 44.7
    if not took: fr = S.draw_key(fr, kx, ky, ang)
    if th > 0:
        down = sm(th / 0.35) * (1 - sm((ft - 44.75) / 0.25))
        hy = -200 + (ky + 40) * down
        M = T(kx - 246 * 1.1 + 40, hy - 292 * 1.1) @ R((246, 292), 0) @ np.diag([1.1, 1.1, 1]) @ R((246, 292), 0)
        Mh = T(kx + 30, hy) @ R((0, 0), -105) @ np.diag([1.2, 1.2, 1]) @ T(-246, -292)
        if took: fr = S.draw_key(fr, *tp(Mh, (120, 240)), 140)
        fr = paint(fr, PIECES['forearm'], Mh)
    planes[3].draw(fr, cx)
    return fr

def V5(t, sil=False):
    """the key turns in the lock (foreshortened about its shaft), the right leaf swings in on its hinge;
    dark inside.  Leaf: perspective quad, free edge recedes as it opens."""
    sh = S.plate('shed'); z = 1.15
    big = cv2.resize(sh, None, fx=z, fy=z, interpolation=cv2.INTER_AREA)
    cx, cy = 500 * z, 545 * z
    ox, oy = int(cx - W / 2), int(cy - H / 2)
    fr = big[oy:oy + H, ox:ox + W].copy()
    door = S.dye_plate(cv2.cvtColor((S.PZ['door_rgb'] * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), -1, 'door') if False else None
    dx0, dy0 = 440 * z - ox, 457 * z - oy; dw, dh = 121 * z, 166 * z
    leaf = fr[int(dy0):int(dy0 + dh), int(dx0 + dw / 2):int(dx0 + dw)].copy()      # the right leaf as printed+dyed
    fr[int(dy0):int(dy0 + dh), int(dx0 + dw / 2):int(dx0 + dw)] = S.INK               # the dark inside behind it
    th = math.radians(82 * sm((t - 0.45) / 0.9))
    lw, lh = leaf.shape[1], leaf.shape[0]
    hxp = dx0 + dw                                         # hinge at the leaf's outer (right) edge
    fx = hxp - lw * math.cos(th); shrink = 0.10 * math.sin(th) * lh
    src = np.float32([[0, 0], [lw, 0], [lw, lh], [0, lh]])
    dst = np.float32([[fx, dy0 + shrink], [hxp, dy0], [hxp, dy0 + lh], [fx, dy0 + lh - shrink]])
    Mp = cv2.getPerspectiveTransform(src, dst)
    la = np.ones((lh, lw), np.float32)
    # key in the lock near the free edge
    kpos = (lw * 0.12, lh * 0.52)
    turn = sm(t / 0.35)
    kl = leaf.copy()
    wl = cv2.warpPerspective(np.dstack([kl, la]), Mp, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    fr = over(fr, wl[..., :3], wl[..., 3])
    kx, ky = cv2.perspectiveTransform(np.float32([[kpos]]), Mp)[0, 0]
    Mk = T(kx - S.KPIV[0], ky - S.KPIV[1]) @ R(S.KPIV, 90, 0.55) @ SX(S.KPIV, max(0.12, abs(math.cos(math.pi / 2 * turn))) * math.cos(th))
    fr = paint(fr, KEY, Mk)
    return fr

BEATS = [
    # slot, film t0, fn, n_sub, planes/ratios, streak px (ground-plane travel per 1/48 s), note
    ('I1_manteau', 3.0, I1, 1, 'wide meadow plate (far 0.35 / ground 1.0, at rest), bench, folded coat (3 hinged pieces)', 0.0),
    ('I2_cloche', 4.5, I2, 4, 'wide plate + bench + coat; bell (foreground, damped pendulum, strike 4.6); visitor front profile walking in', 0.0),
    ('I3_cle', 6.0, I3, 6, 'insert: grass/gravel plate; HANDMADE envelope, flap hinge; key slides out', 0.0),
    ('I4_banc', 7.5, I4, 4, 'wide: visitor bows, key travels to the coat, contact shadow; she straightens', 0.0),
    ('I5_recu', 9.0, I5, 6, 'wide: the receipt falls (drift + flutter) to the gravel', 0.0),
    ('I6_porte', 10.5, I6, 4, 'wide, slow push toward the shed door; visitor back profile walks off right', 0.0),
    ('II2_manteau', 13.5, II2, 6, 'push-in on the bench: coat lifted (unfolds on its hinges), 6-frame brass glint, holdout swap behind the bench', 0.0),
    ('bell_strike', 0.0, bell_clip, 4, 'shed wall plate (dyed), bell + clapper damped pendulum; strike at local 0.1 s (use in I.2 inset, II.4, III.5, IV.3, V.6)', 0.0),
    ('III4_manteau', 25.5, III4, 12, 'wide plate panning 160 px/s (far 0.35 / ground 1.0); conductor at 0.10 scale running on the far meadow', round(160 / 48, 1)),
    ('IV5_manteau', 36.0, IV5, 36, 'run stage pan 1500 px/s (0.35/0.6/1.0/1.6); coat at 1.9 scale sweeping across the near plane', round(1500 / 48, 1)),
    ('V1_banc', 39.0, V1, 36, 'run stage + bench plane 0.8; camera accelerates 0 -> 4200 px/s', round(4200 / 48, 1)),
    ('V2_recu', 40.5, V2, 36, 'run stage at full speed; ticket in the wake; runner catches the camera', round(4200 / 48, 1)),
    ('V4_cle', 43.5, V4, 24, 'run stage; camera brakes, overshoots, returns to rest on the key; hand takes it', round(4200 / 48, 1)),
    ('V5_porte', 45.0, V5, 4, 'shed plate (dyed) close on the door: key turns, right leaf swings in (perspective), dark inside', 0.0),
    ('VI1_cloche', 48.0, VI1, 4, 'bell settling to rest (damped continuation of V.6)', 0.0),
]

def render(name, fn, n):
    w = S.Writer(os.path.join(S.ED, 'clips', name + '.mp4'))
    for k in range(36):
        t = (k + 0.5) / FPS
        a = S.integrate(fn, t, n, 0.5) if n > 1 else fn(t)
        img = S.to_img(a); w.add(img)
        if k == 18: img.save(os.path.join(S.ED, 'stills', name + '_mid.png'))
    w.close()

def main(only=None):
    for name, t0, fn, n, planes, streak in BEATS:
        if only and name not in only: continue
        render(name, fn, n); print('rendered', name, flush=True)
    # greyscale silhouette checks (Reiniger read test): figures black on white, colour removed
    for name, fn, t in (('I4', lambda tt: I4(tt, sil=True), 0.62), ('II2', lambda tt: II2(tt, sil=True, stage=False), 0.35),
                        ('II2_swap', lambda tt: II2(tt, sil=True, stage=False), 1.2)):
        S.to_img(fn(t)).convert('L').save(os.path.join(S.AN, 'checks', f'sil_{name}.png'))

if __name__ == '__main__':
    main(sys.argv[1:] or None)

def bench_empty(t, sil=False):
    """II.5 / III.3 / IV.6: the empty bench, held (same view as II.2's push-in)."""
    v = View(1.45, (760, 470))
    fr = wide_bg(v)
    return draw_bench(fr, v)
BEATS.append(('bench_empty', 0.0, bench_empty, 1, 'push-in on the bench (II.2 framing), empty, held', 0.0))
