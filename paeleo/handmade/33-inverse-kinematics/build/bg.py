"""SCION 33 · the set: dusk, a house front with a doorway and sill, porch boards, steps, a yard.
Everything here is computed (projected 3D geometry and per-pixel ray casts); nothing is found or drawn by hand.
Writes build/cache/bg.png (porch at dusk, door opening left empty), build/cache/interior.png (the lit room seen through
the opening), build/cache/floor.npz (per-pixel porch-floor coordinates, used to cast the door light each frame)."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from geom import *

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
os.makedirs(CACHE, exist_ok=True)
SS = 2
cam = Camera()
camS = Camera(w=W * SS, h=H * SS)


def clip_near(pts, near=0.08):
    """Sutherland-Hodgman clip of a 3D polygon against the camera's near plane."""
    pts = [np.asarray(p, float) for p in pts]
    dep = [(p - camS.pos) @ camS.fwd for p in pts]
    out = []
    for k in range(len(pts)):
        a, b = pts[k], pts[(k + 1) % len(pts)]; da, db_ = dep[k], dep[(k + 1) % len(pts)]
        if da >= near: out.append(a)
        if (da >= near) != (db_ >= near):
            s = (near - da) / (db_ - da); out.append(a + (b - a) * s)
    return out


def P(pts, closed=True):
    pts = clip_near(pts) if closed else pts
    if len(pts) == 0: return []
    q = camS.project(np.asarray(pts, float))
    return [(float(a), float(b)) for a, b, _ in q]


def col(c, k=1.0):
    return tuple(int(max(0, min(255, v * k))) for v in c)


def facing(pts, normal):
    return normal is None or (camS.pos - np.asarray(pts[0], float)) @ np.asarray(normal, float) > 0


def poly(dr, pts, fill, outline=None, width=1, normal=None):
    if not facing(pts, normal): return
    q = P(pts)
    if len(q) < 3: return
    dr.polygon(q, fill=fill, outline=outline, width=width); return
    dr.polygon(P(pts), fill=fill, outline=outline, width=width)


def line(dr, a, b, fill, width=2):
    a = np.asarray(a, float); b = np.asarray(b, float)
    da = (a - camS.pos) @ camS.fwd; db_ = (b - camS.pos) @ camS.fwd
    if da < 0.08 and db_ < 0.08: return
    if da < 0.08: a = a + (b - a) * (0.08 - da) / (db_ - da)
    if db_ < 0.08: b = b + (a - b) * (0.08 - db_) / (da - db_)
    dr.line(P([a, b], closed=False), fill=fill, width=width); return
    dr.line(P([a, b]), fill=fill, width=width)


def sky_and_yard():
    ys, xs = np.mgrid[0:H * SS, 0:W * SS]
    rays = camS.ray(xs.ravel(), ys.ravel()).reshape(H * SS, W * SS, 3)
    el = rays[..., 1]
    # dusk sky: violet-blue overhead to a low ember band at the horizon
    top = np.array([22, 28, 58.0]); mid = np.array([58, 58, 96.0]); low = np.array([150, 104, 104.0])
    u = np.clip(el / 0.35, 0, 1)[..., None]
    sky = np.where(u < 0.35, low + (mid - low) * (u / 0.35), mid + (top - mid) * ((u - 0.35) / 0.65))
    img = sky.copy()
    # yard: ground plane Y = -0.45 seen beyond the porch
    t = (-0.45 - camS.pos[1]) / np.minimum(el, -1e-6)
    gx = camS.pos[0] + rays[..., 0] * t; gz = camS.pos[2] + rays[..., 2] * t
    dist = np.sqrt((gx - camS.pos[0]) ** 2 + (gz - camS.pos[2]) ** 2)
    ground = el < -0.002
    fog = np.clip(dist / 60.0, 0, 1)[..., None]
    gcol = np.array([26, 34, 40.0]) * (1 - fog) + np.array([70, 62, 84.0]) * fog
    # mown stripes, faint
    gcol = gcol * (0.96 + 0.04 * np.sin(gx * 0.7 + np.sin(gz * 0.5))[..., None])
    img = np.where(ground[..., None], gcol, img)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def trees(dr):
    rng = np.random.default_rng(33)
    # a far tree line and two near trees, as computed silhouettes (stacked ellipses on trunks)
    for zx in [(-14, -6), (-10, -2), (-16, 3), (-12, 8), (-9, 12), (-18, 16), (-8, 19), (-13, 24)]:
        z, x = zx
        base = np.array([x, -0.45, z]); h = 3.5 + rng.random() * 3
        for k in range(90):
            c = base + np.array([rng.normal(0, 1.0), h * (0.4 + 0.6 * rng.random() ** 0.7), rng.normal(0, 0.8)])
            q = camS.project(c)
            if q[2] < 0.5: continue
            r = camS.scale(q[2]) * (0.25 + rng.random() * 0.45)
            v = int(rng.integers(-3, 4))
            dr.ellipse([q[0] - r, q[1] - r * 0.8, q[0] + r, q[1] + r * 0.8], fill=(24 + v, 26 + v, 44 + v))
        a = camS.project(base); b = camS.project(base + [0, h * 0.5, 0])
        if a[2] < 0.5: continue
        dr.line([(a[0], a[1]), (b[0], b[1])], fill=(24, 26, 44), width=int(max(2, camS.scale(a[2]) * 0.25)))
    # a fence along the yard's edge
    for x in np.arange(5.6, 16, 0.55):
        line(dr, [x, -0.45, -6.0], [x, 0.55, -6.0], (36, 38, 58), 3)
    line(dr, [5.6, 0.35, -6.0], [16, 0.35, -6.0], (36, 38, 58), 3)
    line(dr, [5.6, 0.05, -6.0], [16, 0.05, -6.0], (36, 38, 58), 3)


def house(dr):
    wall = (62, 66, 92); wall_d = (44, 46, 70)
    Z0, Z1 = -4.2, 2.1
    # side wall at the near corner (faces the camera)
    side_vis = facing([[WALL_OUT, 0, Z1]], [0, 0, 1])
    poly(dr, [[WALL_OUT, -0.45, Z1], [WALL_OUT, 3.3, Z1], [-7, 3.3, Z1], [-7, -0.45, Z1]], wall_d, normal=[0, 0, 1])
    # front face
    poly(dr, [[WALL_OUT, -0.45, Z0], [WALL_OUT, 3.3, Z0], [WALL_OUT, 3.3, Z1], [WALL_OUT, -0.45, Z1]], wall)
    # clapboards
    for y in np.arange(0.0, 3.3, 0.145):
        line(dr, [WALL_OUT + 0.003, y, Z0], [WALL_OUT + 0.003, y, Z1], (50, 53, 78), 2)
        if side_vis: line(dr, [WALL_OUT, y + 0.01, Z1], [-7, y + 0.01, Z1], (36, 38, 60), 2)
    # a window, dimly lit from the same room
    wz = (-2.65, -1.75); wy = (0.95, 2.05)
    poly(dr, [[WALL_OUT + .004, wy[0], wz[0]], [WALL_OUT + .004, wy[1], wz[0]], [WALL_OUT + .004, wy[1], wz[1]], [WALL_OUT + .004, wy[0], wz[1]]], (96, 74, 54))
    line(dr, [WALL_OUT + .006, sum(wy) / 2, wz[0]], [WALL_OUT + .006, sum(wy) / 2, wz[1]], (40, 40, 60), 5)
    line(dr, [WALL_OUT + .006, wy[0], sum(wz) / 2], [WALL_OUT + .006, wy[1], sum(wz) / 2], (40, 40, 60), 5)
    for a, b in [((wy[0], wz[0]), (wy[1], wz[0])), ((wy[1], wz[0]), (wy[1], wz[1])), ((wy[1], wz[1]), (wy[0], wz[1])), ((wy[0], wz[1]), (wy[0], wz[0]))]:
        line(dr, [WALL_OUT + .008, a[0], a[1]], [WALL_OUT + .008, b[0], b[1]], (82, 84, 110), 7)
    # the door opening (to be filled each frame) is cut later; here the casing
    zA, zB = DOOR_Z
    trim = (92, 92, 120)
    for (a, b) in [((0, zA - 0.06), (DOOR_H + 0.08, zA - 0.06)), ((0, zB + 0.06), (DOOR_H + 0.08, zB + 0.06)), ((DOOR_H + 0.06, zA - 0.08), (DOOR_H + 0.06, zB + 0.08))]:
        line(dr, [WALL_OUT + .01, a[0], a[1]], [WALL_OUT + .01, b[0], b[1]], trim, 14)


def porch(dr):
    Z0, Z1 = PORCH_Z
    boards = (70, 62, 70)
    # fascia under the front edge
    poly(dr, [[WALL_OUT, 0, Z1], [STEPS_X, 0, Z1], [STEPS_X, -0.45, Z1], [WALL_OUT, -0.45, Z1]], (40, 36, 52), normal=[0, 0, 1])
    poly(dr, [[WALL_OUT, 0, Z0], [STEPS_X, 0, Z0], [STEPS_X, 0, Z1], [WALL_OUT, 0, Z1]], boards)
    rng = np.random.default_rng(7)
    zs = np.arange(Z0, Z1 + 1e-6, 0.14)
    for i in range(len(zs) - 1):
        k = 0.9 + 0.16 * rng.random()
        poly(dr, [[WALL_OUT, 0, zs[i] + 0.006], [STEPS_X, 0, zs[i] + 0.006], [STEPS_X, 0, zs[i + 1] - 0.006], [WALL_OUT, 0, zs[i + 1] - 0.006]], col(boards, k))
        # butt joints, staggered
        for xj in np.arange(0.4 + 1.3 * rng.random(), STEPS_X, 2.6):
            line(dr, [xj, 0, zs[i]], [xj, 0, zs[i + 1]], (46, 40, 52), 2)
    for z in zs:
        line(dr, [WALL_OUT, 0, z], [STEPS_X, 0, z], (40, 36, 50), 2)
    # front edge nosing
    line(dr, [WALL_OUT, 0, Z1], [STEPS_X, 0, Z1], (96, 86, 96), 4)
    # steps down to the yard
    for k, (x0, x1, y) in enumerate([(STEPS_X, 5.2, -0.15), (5.2, 5.5, -0.30)]):
        yp = 0 if k == 0 else -0.15
        poly(dr, [[x0, yp, Z0 + 0.6], [x0, y, Z0 + 0.6], [x0, y, Z1], [x0, yp, Z1]], (44, 40, 54))
        poly(dr, [[x0, y, Z0 + 0.6], [x1, y, Z0 + 0.6], [x1, y, Z1], [x0, y, Z1]], (64, 58, 68))
        poly(dr, [[x0, y, Z1], [x1, y, Z1], [x1, -0.45, Z1], [x0, -0.45, Z1]], (40, 36, 52), normal=[0, 0, 1])
    poly(dr, [[5.5, -0.30, Z0 + 0.6], [5.5, -0.45, Z0 + 0.6], [5.5, -0.45, Z1], [5.5, -0.30, Z1]], (44, 40, 54))
    # the sill board (raised 3 cm, lighter, worn)
    zA, zB = DOOR_Z
    poly(dr, [[SILL, 0.0, zA - 0.06], [SILL, 0.03, zA - 0.06], [SILL, 0.03, zB + 0.06], [SILL, 0.0, zB + 0.06]], (88, 76, 74))
    poly(dr, [[WALL_IN, 0.03, zA - 0.06], [SILL, 0.03, zA - 0.06], [SILL, 0.03, zB + 0.06], [WALL_IN, 0.03, zB + 0.06]], (110, 96, 90))


def opening_poly():
    zA, zB = DOOR_Z
    return [[WALL_OUT, 0.03, zA], [WALL_OUT, DOOR_H, zA], [WALL_OUT, DOOR_H, zB], [WALL_OUT, 0.03, zB]]


def interior():
    """The room behind the door, ray-cast per pixel: back wall, floor, side walls, ceiling, a lamp and its pool."""
    ys, xs = np.mgrid[0:H, 0:W]
    o = cam.pos
    d = cam.ray(xs.ravel(), ys.ravel()).reshape(H, W, 3)
    BX, ZL, ZR, CY = -3.4, -3.3, 2.0, 2.6
    best = np.full((H, W), np.inf); colr = np.zeros((H, W, 3)); hitp = np.zeros((H, W, 3))
    def plane(axis, val, base, mask_fn):
        nonlocal best, colr, hitp
        t = (val - o[axis]) / np.where(np.abs(d[..., axis]) > 1e-9, d[..., axis], 1e-9)
        p = o + d * t[..., None]
        ok = (t > 0) & (t < best) & mask_fn(p) & (p[..., 0] < WALL_IN + 1e-3)
        best = np.where(ok, t, best)
        colr = np.where(ok[..., None], np.array(base, float), colr)
        hitp = np.where(ok[..., None], p, hitp)
    plane(0, BX, (150, 112, 78), lambda p: (p[..., 1] > 0) & (p[..., 1] < CY))
    plane(1, 0.0, (120, 82, 58), lambda p: (p[..., 0] > BX))
    plane(1, CY, (110, 86, 68), lambda p: (p[..., 0] > BX))
    plane(2, ZL, (140, 104, 74), lambda p: (p[..., 0] > BX))
    plane(2, ZR, (130, 96, 70), lambda p: (p[..., 0] > BX))
    dist = np.linalg.norm(hitp - LAMP, axis=-1)
    dc = np.linalg.norm(hitp - CEIL, axis=-1)
    d2l = np.linalg.norm(hitp - LAMP2, axis=-1)
    lit = 1.0 / (0.5 + dist ** 1.6) + 1.3 / (0.8 + dc ** 1.5) + 0.8 / (0.4 + d2l ** 1.6)
    # floorboards inside, running across
    fl = (np.abs(hitp[..., 1]) < 1e-3)
    lit = lit * np.where(fl, 0.9 + 0.1 * np.sign(np.sin(hitp[..., 2] * 22)), 1.0)
    img = colr * np.clip(lit, 0.15, 1.6)[..., None]
    # the lamp: a shade and a hot core, plus a table
    out = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(out)
    lx, lz = LAMP[0], LAMP[2]
    tb = [[lx + .25, 0.0, lz - .4], [lx + .25, 0.0, lz + .4], [lx + .25, 0.62, lz + .4], [lx + .25, 0.62, lz - .4]]
    q = cam.project(np.array(tb)); dr.polygon([(a, b) for a, b, _ in q], fill=(70, 44, 32))
    top = [[lx - .25, 0.62, lz - .4], [lx + .25, 0.62, lz - .4], [lx + .25, 0.62, lz + .4], [lx - .25, 0.62, lz + .4]]
    q = cam.project(np.array(top)); dr.polygon([(a, b) for a, b, _ in q], fill=(96, 62, 42))
    c = cam.project(LAMP); r = float(cam.scale(c[2]) * 0.2)
    dr.polygon([(c[0] - r * 0.7, c[1] - r * 0.8), (c[0] + r * 0.7, c[1] - r * 0.8), (c[0] + r, c[1] + r * 0.4), (c[0] - r, c[1] + r * 0.4)], fill=(255, 214, 150))
    b = cam.project(LAMP + [0, -0.5, 0]); dr.line([(c[0], c[1] + r * 0.4), (b[0], b[1])], fill=(60, 40, 30), width=3)
    glow = Image.new('L', (W, H), 0); g = ImageDraw.Draw(glow)
    g.ellipse([c[0] - r * 3, c[1] - r * 3, c[0] + r * 3, c[1] + r * 3], fill=140)
    # the second lamp: a wall sconce on the back wall
    c2 = cam.project(LAMP2); r2 = float(cam.scale(c2[2]) * 0.13)
    if c2[2] > 0.5:
        dr.polygon([(c2[0] - r2 * 0.6, c2[1] - r2), (c2[0] + r2 * 0.6, c2[1] - r2), (c2[0] + r2 * 0.9, c2[1] + r2 * 0.5), (c2[0] - r2 * 0.9, c2[1] + r2 * 0.5)], fill=(255, 210, 150))
        g.ellipse([c2[0] - r2 * 3, c2[1] - r2 * 3, c2[0] + r2 * 3, c2[1] + r2 * 3], fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(r * 1.5))
    out = Image.composite(Image.new('RGB', (W, H), (255, 220, 160)), out, glow)
    return out


def floor_map():
    ys, xs = np.mgrid[0:H, 0:W]
    d = cam.ray(xs.ravel(), ys.ravel()).reshape(H, W, 3)
    t = -cam.pos[1] / np.minimum(d[..., 1], -1e-9)
    p = cam.pos + d * t[..., None]
    on = (d[..., 1] < 0) & (p[..., 0] > WALL_OUT) & (p[..., 0] < STEPS_X) & (p[..., 2] > PORCH_Z[0]) & (p[..., 2] < PORCH_Z[1])
    return p[..., 0].astype(np.float32), p[..., 2].astype(np.float32), on


def build(name):
    global cam, camS
    cam = Camera(name=name); camS = Camera(w=W * SS, h=H * SS, name=name)
    img = sky_and_yard()
    dr = ImageDraw.Draw(img)
    trees(dr)
    house(dr)
    porch(dr)
    # the opening, cut dark; the room shows through it per frame
    poly(dr, opening_poly(), (0, 0, 0))
    img = img.resize((W, H), Image.LANCZOS)
    img.save(os.path.join(CACHE, 'bg_%s.png' % name))
    mask = Image.new('L', (W * SS, H * SS), 0)
    ImageDraw.Draw(mask).polygon(P(opening_poly()), fill=255)
    mask.resize((W, H), Image.LANCZOS).save(os.path.join(CACHE, 'opening_mask_%s.png' % name))
    interior().save(os.path.join(CACHE, 'interior_%s.png' % name))
    fx, fz, on = floor_map()
    np.savez_compressed(os.path.join(CACHE, 'floor_%s.npz' % name), fx=fx, fz=fz, on=on)
    print('bg ok', name)


if __name__ == '__main__':
    for nm in CAMS:
        build(nm)
