"""SCION 23 · the set, painted in code in the same gouache as the actors: a dusk cross-section of a porch and the
room behind its door. The plate is painted at twice the frame size; the door leaf is painted once and mapped onto
its swing per angle; the light that comes out of the door is a separate warm layer."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import paint as P

S2 = 2
PW, PH = W * S2, H * S2
rng = np.random.default_rng(7)


def wp(x, y, d=0.0):
    X, Y = wide(x, y, d)
    return X * S2, Y * S2


def poly_mask(pts):
    m = Image.new('L', (PW, PH), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    return np.asarray(m, np.float32) / 255


def layer(canvas, mask, color, strokes=True, angle=0.0, amount=0.25, length=(20, 60), width=(3, 7), shade=None,
          density=1.2, seed=0):
    amount = min(0.6, amount * 1.6); density = density * 2.2
    col = np.zeros((PH, PW, 3), np.float32) + np.asarray(color, np.float32)
    if shade is not None: col = col * shade[..., None]
    m = mask > 0.5
    if strokes and m.any():
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        sub = P.strokes(col[y0:y1, x0:x1], m[y0:y1, x0:x1], np.random.default_rng(seed), angle=angle,
                        n_per_kpx=density, length=length, width=width, amount=amount, jitter=0.12)
        col[y0:y1, x0:x1] = sub
    canvas[:] = canvas * (1 - mask[..., None]) + col * mask[..., None]


def vgrad(y0, y1, c0, c1):
    t = np.clip((np.arange(PH)[:, None] - y0) / (y1 - y0), 0, 1)
    return np.asarray(c0) + (np.asarray(c1) - np.asarray(c0)) * t[..., None]


def lines(canvas, segs, color, width, alpha):
    im = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = tuple(int(v * 255) for v in color) + (int(alpha * 255),)
    for s in segs: d.line(s, fill=c, width=width)
    a = np.asarray(im, np.float32) / 255
    canvas[:] = canvas * (1 - a[..., 3:4]) + a[..., :3] * a[..., 3:4]


def paint_plate():
    C = np.zeros((PH, PW, 3), np.float32)
    yfar = wp(0, 0, PORCH_FAR)[1]
    # sky
    sky = vgrad(0, 0.68 * PH, (0.16, 0.17, 0.31), (0.75, 0.47, 0.40))
    sky = sky * (0.97 + 0.06 * P.value_noise(PH, PW, 90, rng)[..., None])
    C[:] = sky
    C[:] = P.strokes(C, np.ones((PH, PW), bool), np.random.default_rng(40), angle=0.0, n_per_kpx=1.6,
                     length=(60, 220), width=(6, 14), amount=0.22, jitter=0.06)
    cl = Image.new('L', (PW, PH), 0); d = ImageDraw.Draw(cl)
    for k in range(26):
        x = rng.uniform(800, PW); y = rng.uniform(140, 760); L = rng.uniform(120, 420)
        d.line([x - L, y, x + L, y + rng.uniform(-8, 8)], fill=int(rng.uniform(60, 140)), width=int(rng.uniform(8, 22)))
    cl = np.asarray(cl.filter(ImageFilter.GaussianBlur(9)), np.float32)[..., None] / 255
    C[:] = C * (1 - 0.5 * cl) + np.array([0.86, 0.58, 0.55]) * 0.5 * cl
    # hills and trees beyond the railing
    hx = np.arange(PW)
    hill = 0.70 * PH + 26 * np.sin(hx / 260.0) + 14 * np.sin(hx / 97.0 + 1)
    m = (np.arange(PH)[:, None] > hill[None, :]).astype(np.float32)
    layer(C, m, (0.20, 0.20, 0.30), angle=0, amount=0.18, seed=1)
    trees = Image.new('L', (PW, PH), 0); d = ImageDraw.Draw(trees)
    for k in range(40):
        x = rng.uniform(900, PW); base = hill[int(min(PW - 1, x))] + 10; hgt = rng.uniform(40, 150)
        d.ellipse([x - hgt * 0.35, base - hgt, x + hgt * 0.35, base + 10], fill=255)
    layer(C, np.asarray(trees, np.float32) / 255, (0.15, 0.16, 0.24), angle=-1.4, amount=0.2, seed=2)
    # porch floor (boards along x), from the wall to the right edge
    xw = wp(WALL_OUT, 0)[0]
    pts = [wp(SILL[0], 0, PORCH_FAR), (PW, yfar), (PW, wp(0, 0, PORCH_NEAR)[1]), wp(SILL[0], 0, PORCH_NEAR)]
    fl = poly_mask(pts)
    sh = np.clip(0.8 + 0.25 * (np.arange(PH)[:, None] - yfar) / (wp(0, 0, PORCH_NEAR)[1] - yfar), 0.8, 1.05)
    layer(C, fl, (0.47, 0.42, 0.42), shade=np.broadcast_to(sh, (PH, PW)), angle=0, amount=0.25, length=(60, 160),
          width=(3, 6), density=0.8, seed=3)
    segs = []
    for d_ in np.arange(PORCH_NEAR, PORCH_FAR, 0.13):
        y = wp(0, 0, d_)[1]; segs.append([xw, y, PW, y])
    lines(C, segs, (0.25, 0.21, 0.24), 2, 0.55)
    # railing and posts at the far edge
    rail_top = wp(0, 0.9, PORCH_FAR)[1]; rail_bot = wp(0, 0.1, PORCH_FAR)[1]
    bal = Image.new('L', (PW, PH), 0); d = ImageDraw.Draw(bal)
    for x in np.arange(WALL_OUT + 0.1, 5.0, 0.16):
        X = wp(x, 0)[0]; d.rectangle([X - 7, rail_top, X + 7, rail_bot], fill=255)
    d.rectangle([xw, rail_top - 14, PW, rail_top + 8], fill=255)
    d.rectangle([xw, rail_bot - 8, PW, rail_bot + 6], fill=255)
    for x in (2.55, 4.75):
        X = wp(x, 0)[0]; d.rectangle([X - 22, 120, X + 22, yfar], fill=255)
    layer(C, np.asarray(bal, np.float32) / 255, (0.30, 0.27, 0.32), angle=-math.pi / 2, amount=0.2, seed=4)
    # porch roof beam
    roof = np.zeros((PH, PW), np.float32); roof[:130, int(xw):] = 1
    layer(C, roof, (0.22, 0.19, 0.22), angle=0, amount=0.2, seed=5)
    lines(C, [[xw, 130, PW, 130]], (0.12, 0.1, 0.12), 6, 0.8)
    # porch fascia and the garden below
    yn = wp(0, 0, PORCH_NEAR)[1]
    fas = np.zeros((PH, PW), np.float32); fas[int(yn):int(yn + 70), int(wp(SILL[0], 0)[0]):] = 1
    layer(C, fas, (0.33, 0.28, 0.30), angle=0, amount=0.2, seed=6)
    gr = np.zeros((PH, PW), np.float32); gr[int(yn + 70):, :] = 1
    layer(C, gr, (0.13, 0.15, 0.16), angle=-1.5, amount=0.3, length=(10, 40), width=(3, 6), density=2.0, seed=7)
    lines(C, [[0, yn + 70, PW, yn + 70]], (0.08, 0.07, 0.08), 4, 0.7)
    # ---- the room
    xin = wp(WALL_IN, 0)[0]
    yb = wp(0, 0, ROOM_BACK)[1]
    wall = np.zeros((PH, PW), np.float32); wall[130:int(yb), :int(xin)] = 1
    layer(C, wall, (0.74, 0.55, 0.38), shade=np.broadcast_to(vgrad(130, yb, (1.0,) * 3, (0.86,) * 3)[..., 0], (PH, PW)),
          angle=-math.pi / 2, amount=0.18, length=(30, 70), seed=8)
    # wallpaper sprigs
    sp = []
    for yy in range(170, int(yb) - 20, 70):
        for xx in range(20 + (yy // 70 % 2) * 35, int(xin) - 10, 70):
            sp.append([xx, yy, xx + 6, yy + 14])
    lines(C, sp, (0.62, 0.42, 0.28), 4, 0.5)
    rf = poly_mask([(0, yb), (xin, yb), (xin, PH), (0, PH)])
    rf[int(yn + 70):] = 0
    layer(C, rf, (0.55, 0.36, 0.22), angle=0, amount=0.25, length=(60, 140), density=0.9, seed=9)
    segs = [[0, wp(0, 0, d_)[1], xin, wp(0, 0, d_)[1]] for d_ in np.arange(PORCH_NEAR, ROOM_BACK, 0.16)]
    lines(C, segs, (0.36, 0.22, 0.14), 2, 0.5)
    lines(C, [[0, yb, xin, yb]], (0.35, 0.22, 0.15), 10, 0.9)
    # rug
    rug = poly_mask([wp(-1.6, 0, 1.2), wp(-0.1, 0, 1.2), wp(-0.1, 0, -0.5), wp(-1.6, 0, -0.5)])
    layer(C, rug, (0.55, 0.20, 0.17), angle=0, amount=0.3, seed=10)
    rb = [wp(-1.6, 0, 1.2) + wp(-0.1, 0, 1.2), wp(-0.1, 0, 1.2) + wp(-0.1, 0, -0.5),
          wp(-0.1, 0, -0.5) + wp(-1.6, 0, -0.5), wp(-1.6, 0, -0.5) + wp(-1.6, 0, 1.2)]
    lines(C, rb, (0.85, 0.66, 0.4), 4, 0.6)
    # picture frame, side table, lamp (against the back wall)
    fx0, fy0 = wp(-0.95, 1.75, ROOM_BACK); fx1, fy1 = wp(-0.35, 1.3, ROOM_BACK)
    fr = np.zeros((PH, PW), np.float32); fr[int(fy0):int(fy1), int(fx0):int(fx1)] = 1
    layer(C, fr, (0.33, 0.22, 0.16), seed=11)
    fr2 = np.zeros((PH, PW), np.float32); fr2[int(fy0) + 14:int(fy1) - 14, int(fx0) + 14:int(fx1) - 14] = 1
    layer(C, fr2, (0.45, 0.52, 0.48), angle=0.4, amount=0.35, seed=12)
    tx0, ty0 = wp(-1.75, 0.62, ROOM_BACK - 0.2); tx1, ty1 = wp(-1.3, 0.0, ROOM_BACK - 0.2)
    tb = np.zeros((PH, PW), np.float32); tb[int(ty0):int(ty0) + 22, int(tx0):int(tx1)] = 1
    tb[int(ty0):int(ty1), int(tx0) + 12:int(tx0) + 30] = 1; tb[int(ty0):int(ty1), int(tx1) - 30:int(tx1) - 12] = 1
    layer(C, tb, (0.30, 0.19, 0.12), seed=13)
    lx = (tx0 + tx1) / 2
    lb = np.zeros((PH, PW), np.float32); lb[int(ty0) - 80:int(ty0), int(lx) - 8:int(lx) + 8] = 1
    layer(C, lb, (0.2, 0.15, 0.12), seed=14)
    shade_pts = [(lx - 60, ty0 - 80), (lx + 60, ty0 - 80), (lx + 38, ty0 - 170), (lx - 38, ty0 - 170)]
    layer(C, poly_mask(shade_pts), (1.0, 0.86, 0.55), amount=0.15, seed=15)
    # the lamp's glow
    yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
    glow = np.exp(-((xx - lx) ** 2 + (yy - (ty0 - 120)) ** 2) / (2 * 260.0 ** 2)) * (xx < xin)
    C[:] = C + glow[..., None] * np.array([0.30, 0.20, 0.08])
    # ceiling band of the room (cut) and the wall section with the doorway
    ce = np.zeros((PH, PW), np.float32); ce[:130, :int(xin)] = 1
    layer(C, ce, (0.20, 0.16, 0.16), seed=16)
    xo = wp(WALL_OUT, 0)[0]
    ylin = wp(0, LINTEL, DOOR_DEPTH[1])[1]
    sec = np.zeros((PH, PW), np.float32); sec[:int(ylin), int(xin):int(xo)] = 1
    layer(C, sec, (0.28, 0.20, 0.19), angle=-math.pi / 2, amount=0.2, seed=17)
    hatch = [[xin + k, 0, xin + k + 60, 60] for k in range(-60, int(xo - xin) + 60, 14)]
    hatch = [[xin + k, y, xin + k + 40, y + 40] for k in range(0, int(xo - xin), 1) if False]
    lines(C, [[xin, y, xo, y + (xo - xin)] for y in range(0, int(ylin) - 60, 26)], (0.18, 0.12, 0.12), 3, 0.5)
    # the far jamb face (door frame trim, lit from the room) below the lintel
    jb = np.zeros((PH, PW), np.float32); jb[int(ylin):int(wp(0, 0, DOOR_DEPTH[1])[1]), int(xin):int(xo)] = 1
    layer(C, jb, (0.80, 0.72, 0.60), shade=np.broadcast_to(np.linspace(1.0, 0.75, PW)[None, :], (PH, PW)),
          angle=-math.pi / 2, amount=0.18, seed=18)
    lines(C, [[xin + 8, ylin, xin + 8, wp(0, 0, DOOR_DEPTH[1])[1]], [xo - 8, ylin, xo - 8, wp(0, 0, DOOR_DEPTH[1])[1]]],
          (0.45, 0.35, 0.28), 4, 0.6)
    lin = np.zeros((PH, PW), np.float32); lin[int(ylin) - 22:int(ylin) + 6, int(xin) - 30:int(xo) + 30] = 1
    layer(C, lin, (0.70, 0.62, 0.52), seed=19)
    # threshold: the sill board across the doorway (raised 3 cm)
    sl = poly_mask([wp(SILL[0], 0.035, DOOR_DEPTH[1]), wp(SILL[1], 0.035, DOOR_DEPTH[1]),
                    wp(SILL[1], 0.035, DOOR_DEPTH[0]), wp(SILL[1], 0.0, DOOR_DEPTH[0]),
                    wp(SILL[0], 0.0, DOOR_DEPTH[0]), wp(SILL[0], 0.035, DOOR_DEPTH[0])])
    layer(C, sl, (0.62, 0.50, 0.38), angle=0, amount=0.25, seed=20)
    lines(C, [list(wp(SILL[0], 0.035, DOOR_DEPTH[0])) + list(wp(SILL[1], 0.035, DOOR_DEPTH[0]))], (0.3, 0.2, 0.15), 3, 0.7)
    # paper grain over all
    C[:] = C * (1 + 0.05 * (rng.random((PH, PW, 1)) - 0.5))
    return np.clip(C, 0, 1)


def paint_door():
    """the door leaf, front face, 0.9 x 2.0 m at 300 px/m: painted panels, a brass knob"""
    w, h = 270, 600
    col = np.zeros((h, w, 3), np.float32) + np.array([0.46, 0.27, 0.17])
    m = np.ones((h, w), bool)
    col = P.strokes(col, m, np.random.default_rng(31), angle=-math.pi / 2, n_per_kpx=3, length=(40, 120),
                    width=(3, 6), amount=0.25)
    im = Image.fromarray((col * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for (x0, y0, x1, y1) in ((30, 30, 240, 270), (30, 320, 240, 570)):
        d.rectangle([x0, y0, x1, y1], outline=(70, 38, 24), width=6)
        d.rectangle([x0 + 10, y0 + 10, x1 - 10, y1 - 10], outline=(150, 96, 62), width=3)
    d.ellipse([220, 280, 246, 306], fill=(196, 160, 80))
    d.rectangle([0, 0, w - 1, h - 1], outline=(30, 26, 26), width=5)
    return np.asarray(im, np.float32) / 255


def door_quad(theta):
    """the leaf hinged at the far jamb on the inner face, swinging into the room by theta degrees"""
    th = math.radians(theta)
    hx, hd = WALL_IN, DOOR_DEPTH[1]
    fx, fd = hx - 0.9 * math.sin(th), hd - 0.9 * math.cos(th)
    return [wp(fx, 2.0, fd), wp(hx, 2.0, hd), wp(hx, 0, hd), wp(fx, 0, fd)]   # free-top, hinge-top, hinge-bottom, free-bottom


def warp_quad(canvas, tex, quad, shade=1.0):
    """map tex (h,w,3) onto a convex quad by two triangles"""
    h, w = tex.shape[:2]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    if quad[0][0] > quad[1][0]:   # face seen from the other side: mirror the texture
        src = [(w, 0), (0, 0), (0, h), (w, h)]
    for tri in ((0, 1, 2), (0, 2, 3)):
        D = np.array([quad[i] for i in tri], np.float64); Sx = np.array([src[i] for i in tri], np.float64)
        x0, y0 = np.floor(D.min(0)).astype(int); x1, y1 = np.ceil(D.max(0)).astype(int) + 1
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, canvas.shape[1]), min(y1, canvas.shape[0])
        if x1 <= x0 or y1 <= y0: continue
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64) + 0.5
        a, b, c = D
        det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(det) < 1e-6: continue
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / det
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / det
        l3 = 1 - l1 - l2
        ins = (l1 >= -0.002) & (l2 >= -0.002) & (l3 >= -0.002)
        u = l1 * Sx[0, 0] + l2 * Sx[1, 0] + l3 * Sx[2, 0]; v = l1 * Sx[0, 1] + l2 * Sx[1, 1] + l3 * Sx[2, 1]
        ui = np.clip(u.astype(int), 0, w - 1); vi = np.clip(v.astype(int), 0, h - 1)
        sub = canvas[y0:y1, x0:x1]
        sub[ins] = tex[vi[ins], ui[ins]] * shade


def spill_mask(theta):
    """the warm light thrown out of the doorway onto the porch floor and the jamb, by door angle"""
    op = min(1.0, max(0.0, theta - 22) / 70.0)
    xo = WALL_OUT
    reach = 0.6 + 3.2 * op
    pts = [wp(xo, 0, DOOR_DEPTH[0] - 0.05), wp(xo, 0, DOOR_DEPTH[1] + 0.05),
           wp(xo + reach, 0, DOOR_DEPTH[1] + 0.55 * op), wp(xo + reach, 0, DOOR_DEPTH[0] - 0.4 - 0.3 * op)]
    m = Image.fromarray((poly_mask(pts) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30))
    m = np.asarray(m, np.float32) / 255
    X = (np.arange(PW)[None, :] / S2 - X0) / K
    fall = np.exp(-np.clip(X - xo, 0, None) / (0.8 + 1.6 * op))
    return m * fall * (0.22 + 0.78 * op)


def door_angle(t):
    """ajar (24 deg) until the score opens it at 6.2 s, then swings to 96 deg over 0.75 s"""
    u = smooth(6.2, 6.95, t)
    return 24 + 72 * u


def main():
    os.makedirs(CACHE, exist_ok=True)
    plate = paint_plate()
    Image.fromarray((plate * 255).astype(np.uint8)).save(os.path.join(CACHE, 'plate.png'))
    door = paint_door()
    np.save(os.path.join(CACHE, 'door.npy'), door)
    print('plate', plate.shape)


if __name__ == '__main__':
    main()
