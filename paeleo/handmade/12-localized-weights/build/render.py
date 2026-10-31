"""Render scene frames [a, b) to cache/frames/NNNN.jpg and measure the dog from its own rendered mask (cache/meas/NNNN.json).
python3 render.py a b"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
import world as Wd
import rig, person, perform, bbw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cache', 'frames'); MEAS = os.path.join(HERE, 'cache', 'meas')
os.makedirs(OUT, exist_ok=True); os.makedirs(MEAS, exist_ok=True)
FR = perform.FR
FPS = 24

DV, DF, DW, DH = rig.load()
TG = rig.tri_groups(DF, DW, DH)
PV, PF, PW, PH = person.load()
POSES = perform.dog_poses()
HEAD_J = [h['name'] for h in DH].index('head')
NECK_J = [h['name'] for h in DH].index('neck')


def smooth(e):
    e = np.clip(e, 0, 1); return e * e * (3 - 2 * e)


# ---- camera: wide on the whole porch, then closing on the door as the dog approaches (zero-phase smoothed)
def camera_series():
    xd = np.array([p['x'] for p in POSES])
    R = np.full(len(xd), 5.25)
    T = np.array([f['t'] for f in FR])
    follow = np.clip(xd + 1.40, 2.75, 5.25)
    w = smooth((T - 14.6) / 1.5)
    R = R * (1 - w) + np.minimum(R, follow) * w
    for _ in range(2):                      # forward-backward exponential smoothing
        for direction in (1, -1):
            idx = range(len(R)) if direction > 0 else range(len(R) - 1, -1, -1)
            prev = None
            for i in idx:
                prev = R[i] if prev is None else prev + 0.06 * (R[i] - prev)
                R[i] = prev
    R = np.round(R, 3)
    R[R < 2.756] = 2.75                     # settle exactly, so the still shots reuse one cached set
    return R


CAM_R = camera_series()


def cam_at(i):
    left, right = -1.9, CAM_R[i]
    s = Wd.W / (right - left)
    s_w, s_c = Wd.W / (5.25 + 1.9), Wd.W / (2.75 + 1.9)
    y0 = 548 + (s - s_w) / (s_c - s_w) * 66
    return Wd.Camera(left, right, y0)


# ---- the door, the light, the person, the voice (from the score)
T = np.array([f['t'] for f in FR])
OPEN_T = next(f['t'] for f in FR if f['door'] == 'open')


def door_open(t):
    return smooth((t - (OPEN_T - 0.05)) / 0.75)


def light_at(t):
    return smooth((t - OPEN_T) / 0.9)


WORDS = perform.WORDS


def person_pose(i):
    f = FR[i]; p = f['person']; t = f['t']
    xs = [g['person']['x'] for g in FR]
    v = (xs[min(i + 1, len(xs) - 1)] - xs[max(i - 1, 0)]) * FPS / 2
    dist = sum(abs(xs[k] - xs[k - 1]) for k in range(1, i + 1))
    call = 0.0
    for a, b, w, kind in WORDS:
        if kind == 'call' and a - 0.05 <= t <= b:
            call = smooth((t - a + 0.05) / 0.15) * (1 - smooth((t - b + 0.2) / 0.2))
    return {'x': p['x'], 'sit': p['sit'], 'reach': p['reach'], 'low': p['low'], 'call': call,
            'stepping': min(1.0, abs(v) / 0.5) * (1 - p['sit']), 'step': dist / 0.32 * np.pi, 't': t}


def tri_mask_polys(Xpx, F):
    return [Xpx[f] for f in F]


def caption(canvas, cam, i, ppos):
    t = T[i]
    for a, b, w, kind in WORDS:
        if a - 0.02 <= t <= b + 0.5:
            alpha = smooth((t - a + 0.02) / 0.12) * (1 - smooth((t - b) / 0.5))
            size = 36 if kind == 'call' else 29
            f = Wd.font('f27.ttf', size * Wd.SS)
            hx, hy = cam.px(ppos[0] + 0.10, 2.02 if ppos[1] < 0.5 else 1.62)
            img = Image.new('L', (Wd.W * Wd.SS, Wd.H * Wd.SS), 0)
            d = ImageDraw.Draw(img)
            d.text((hx, hy), w, font=f, fill=255, anchor='lm')
            m = np.asarray(img.resize((Wd.W, Wd.H), Image.LANCZOS), np.float32) / 255.0 * alpha
            col = Wd.PAL['cream'] if kind == 'call' else (236, 214, 176)
            Wd.comp(canvas, m, col, shadow=(2, 3, 2, .55 * alpha), tex=False)


BACK = Wd.backdrop()
STATIC = {}


def render(i):
    f = FR[i]; t = f['t']
    cam = cam_at(i)
    light = light_at(t); op = door_open(t)
    key = (round(cam.right, 4), round(light, 3), round(op, 3))
    if key not in STATIC:
        STATIC.clear()
        s = BACK.copy()
        Wd.room(s, cam, light, t)
        Wd.door_leaf(s, cam, op, light)
        Wd.jamb(s, cam, light)
        Wd.stool(s, cam)
        Wd.house_and_porch(s, cam, light, t)
        Wd.light_pool(s, cam, light)
        STATIC[key] = s
    c = STATIC[key].copy()
    # person (ink-blue paper)
    pp = person_pose(i)
    PX = bbw.skin(PV, PW, person.pose_affines(pp, PH))
    pm = Wd.tri_mask(cam.px(PX[:, 0], PX[:, 1]), PF)
    pcol = np.asarray(Wd.PAL['person']) * (0.8 + 0.35 * light)
    Wd.comp(c, pm, pcol, shadow=(-5, 3, 4, .45), edge=Wd.PAL['person_edge'])
    # dog (red lace paper), drawn as layers in depth order when its handle groups face different ways mid-turn
    P = POSES[i]
    A = rig.pose_affines(P, DH)
    X = bbw.skin(DV, DW, A)
    Xpx = cam.px(X[:, 0], X[:, 1])
    yaw = P['yaw']
    turning = max(yaw.values()) - min(yaw.values()) > 0.5
    warm = 1 + 0.22 * light * float(np.clip(1 - (P['x'] - 0.3) / 2.6, 0, 1))
    dcol = np.minimum(np.asarray(Wd.PAL['dog'], np.float32) * warm, 255)
    total = np.zeros((Wd.H, Wd.W), np.float32)
    layers = [None] if not turning else [2, 1, 0]
    for g in layers:
        tri = DF if g is None else DF[TG == g]
        m = Wd.tri_mask(Xpx, tri)
        Wd.comp(c, m, dcol, shadow=(-6, 4, 4, .5), edge=Wd.PAL['dog_edge'])
        total = np.maximum(total, m)
    caption(c, cam, i, (pp['x'], pp['sit']))
    out = np.clip(c, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(os.path.join(OUT, '%04d.jpg' % i), quality=93)
    # measurement from the rendered dog mask
    ys, xs = np.nonzero(total > 0.5)
    cx, cy = float(xs.mean()), float(ys.mean())
    hb = A[HEAD_J] @ np.array([*DH[HEAD_J]['b'], 1.0]); ha = A[HEAD_J] @ np.array([*DH[HEAD_J]['a'], 1.0])
    facing = 1 if hb[0] < ha[0] else -1
    # head top vs back line (world metres): highest head-group vertex vs withers height
    head_v = DW[:, HEAD_J] + DW[:, NECK_J] > 0.5
    back_v = (np.abs(DV[:, 0] + 0.10) < 0.12) & (DV[:, 1] > 0.45)
    meas = {'i': i, 't': round(t, 4), 'x_screen': round(cx, 2), 'y_screen': round(cy, 2),
            'x_world_measured': round(float(cam.inv_x(cx)) - perform.X_OFFSET, 4),
            'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], 'facing': facing,
            'muzzle_world_x': round(float(hb[0]), 4), 'head_top_y': round(float(X[head_v, 1].max()), 4),
            'back_y': round(float(X[back_v, 1].max()), 4),
            'flipped_triangles': int(((bbw.signed_areas(X, DF) * np.sign(bbw.signed_areas(DV, DF))) < 0).sum()),
            'yaw': {k: round(v, 1) for k, v in yaw.items()}, 'cam': [cam.left, round(cam.right, 4), round(cam.y0, 2)]}
    json.dump(meas, open(os.path.join(MEAS, '%04d.json' % i), 'w'))


if __name__ == '__main__':
    a, b = int(sys.argv[1]), int(sys.argv[2])
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    for i in range(a, b, step):
        if not os.path.exists(os.path.join(MEAS, '%04d.json' % i)):
            render(i)
