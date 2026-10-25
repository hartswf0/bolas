"""The glass planes: each is painted once, in world metres, and laid at its depth Z in the multiplane.
Run: python3 world.py   -> build/cache/planes/*.png + planes.json (regenerable)

Everything here is painted by this script (gradients, noise, brushed shapes), except
  - the fog, which is keyed from real time-lapse cloud footage (found-frames: cloud, 'Top Of The Cloud', public domain)
  - the bowl inside the house, cut from the archive dog film (kit/archive-dog f000, 'Amateur Film New Jersey C', PD)
"""
import json, math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import *

OUT = os.path.join(CACHE, 'planes')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(5)


def noise(h, w, scale, seed, octaves=3):
    """smooth value noise in [0,1] made by upscaling random fields (a painter's mottling)."""
    r = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        sh = max(2, int(h / scale * 2 ** o)), max(2, int(w / scale * 2 ** o))
        f = Image.fromarray((r.random(sh) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(f, np.float32) / 255
        tot += amp
        amp *= 0.5
    return acc / tot


class Plane:
    """a painted glass: an RGBA image covering world rect [X0,X1] x [Y0 (bottom), Y1 (top)] at depth z."""
    def __init__(self, name, z, X0, X1, Y0, Y1, ppm):
        self.name, self.z, self.X0, self.X1, self.Y0, self.Y1, self.ppm = name, z, X0, X1, Y0, Y1, ppm
        self.w, self.h = int((X1 - X0) * ppm), int((Y1 - Y0) * ppm)
        self.rgb = np.zeros((self.h, self.w, 3), np.float32)
        self.a = np.zeros((self.h, self.w), np.float32)
        self.img = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))

    def px(self, X, Y):
        return ((X - self.X0) * self.ppm, (self.Y1 - Y) * self.ppm)

    def poly(self, pts, col, a=1.0, blur=0):
        m = Image.new('L', (self.w, self.h), 0)
        ImageDraw.Draw(m).polygon([self.px(*q) for q in pts], fill=255)
        self.lay(m, col, a, blur)

    def lay(self, m, col, a=1.0, blur=0, tex=None):
        if blur:
            m = m.filter(ImageFilter.GaussianBlur(blur))
        mm = np.asarray(m, np.float32) / 255 * a
        c = np.array(col, np.float32)[None, None, :] * (np.ones_like(mm)[..., None] if tex is None else tex[..., None])
        self.rgb = self.rgb * (1 - mm[..., None]) + c * mm[..., None]
        self.a = self.a + mm * (1 - self.a)

    def save(self):
        arr = np.dstack([np.clip(self.rgb, 0, 255), np.clip(self.a * 255, 0, 255)]).astype(np.uint8)
        Image.fromarray(arr, 'RGBA').save(os.path.join(OUT, self.name + '.png'))
        return dict(name=self.name, z=self.z, X0=self.X0, X1=self.X1, Y0=self.Y0, Y1=self.Y1, ppm=self.ppm)


def tree(pl, x, ybase, height, col, a, seed, lean=0.0, blur=1.5):
    """a tree in fog: trunk and recursive branches, painted as tapered strokes, plus soft crown masses."""
    r = random.Random(seed)
    m = Image.new('L', (pl.w, pl.h), 0)
    d = ImageDraw.Draw(m)

    def br(X, Y, ang, L, wdt, depth):
        X2, Y2 = X + L * math.cos(ang), Y + L * math.sin(ang)
        d.line([pl.px(X, Y), pl.px(X2, Y2)], fill=255, width=max(1, int(wdt * pl.ppm)))
        if depth == 0 or L < 0.12:
            for _ in range(3):
                cx, cy = X2 + r.uniform(-0.4, 0.4) * L * 2, Y2 + r.uniform(-0.2, 0.4) * L * 2
                rr = r.uniform(0.25, 0.6) * height * 0.12
                p0, p1 = pl.px(cx - rr, cy + rr), pl.px(cx + rr, cy - rr)
                d.ellipse([p0, p1], fill=150)
            return
        for k in range(r.choice([2, 2, 3])):
            br(X2, Y2, ang + r.uniform(-0.75, 0.75), L * r.uniform(0.6, 0.78), wdt * 0.62, depth - 1)

    br(x, ybase, math.pi / 2 + lean, height * 0.36, height * 0.035, 6)
    pl.lay(m, col, a, blur)


def build():
    meta = []
    # ---------------------------------------------------------------- sky (z 400): dusk gradient, moon, cloud bands
    sky = Plane('sky', Z['sky'], -260, 300, -120, 300, 2.6)
    yy = np.linspace(1, 0, sky.h)[:, None]
    top, mid, low = np.array([30, 36, 70.]), np.array([88, 92, 128.]), np.array([158, 138, 146.])
    g = np.where(yy > 0.45, ((yy - 0.45) / 0.55), 0)[..., None]
    gl = np.clip((0.45 - yy) / 0.45, 0, 1)[..., None]
    base = mid * (1 - g) + top * g
    base = base * (1 - gl) + low * gl
    n = noise(sky.h, sky.w, 60, 11)[..., None]
    sky.rgb = base * (0.93 + 0.14 * n) * np.ones((1, sky.w, 1))
    sky.a[:] = 1
    mx, my = 150.0, 170.0  # the moon: low, to the right, above the yard
    m = Image.new('L', (sky.w, sky.h), 0)
    ImageDraw.Draw(m).ellipse([sky.px(mx - 7, my + 7), sky.px(mx + 7, my - 7)], fill=255)
    halo = Image.new('L', (sky.w, sky.h), 0)
    ImageDraw.Draw(halo).ellipse([sky.px(mx - 30, my + 30), sky.px(mx + 30, my - 30)], fill=120)
    sky.lay(halo, (190, 186, 200), 0.35, blur=40)
    sky.lay(m, (236, 232, 214), 0.95, blur=1.2)
    meta.append(sky.save())

    # ---------------------------------------------------------------- far trees (z 32) and near trees (z 15)
    far = Plane('trees_far', Z['trees_far'], -20, 40, -3, 16, 40)
    far.poly([(-20, -3), (40, -3), (40, -0.2), (-20, -0.2)], (64, 70, 96), 1.0)
    for k in range(26):
        tree(far, 2 + k * 1.45 + rng.uniform(-0.5, 0.5), -0.4, rng.uniform(6, 11), (66, 74, 102), 0.9, 100 + k, blur=4)
    meta.append(far.save())
    near = Plane('trees_near', Z['trees_near'], -10, 26, -3, 12, 60)
    near.poly([(-10, -3), (26, -3), (26, -0.45), (-10, -0.45)], (34, 40, 52), 1.0)
    for k, X in enumerate([8.2, 10.6, 13.9, 17.0, 20.5]):
        tree(near, X, -0.5, rng.uniform(5.5, 8.5), (38, 44, 62), 0.97, 200 + k, lean=rng.uniform(-0.1, 0.1), blur=2)
    # a fence, its pickets lost into the fog
    for k in range(60):
        X = 6.0 + k * 0.32
        near.poly([(X, -0.45), (X + 0.14, -0.45), (X + 0.14, 0.55), (X + 0.07, 0.68), (X, 0.55)], (46, 52, 68), 0.9)
    near.poly([(6.0, 0.25), (26, 0.25), (26, 0.33), (6.0, 0.33)], (46, 52, 68), 0.9)
    meta.append(near.save())

    # ---------------------------------------------------------------- interior back wall (z 8.2) and its near objects (z 6.6)
    iw = Plane('interior_wall', Z['interior_wall'], -5, 5, -0.2, 3.6, 120)
    n = noise(iw.h, iw.w, 50, 21)
    yy = np.linspace(1, 0, iw.h)[:, None]
    xx = np.linspace(-5, 5, iw.w)[None, :]
    glow = np.exp(-((xx + 0.7) ** 2) / 3.0 - ((yy - 0.42) ** 2) / 0.08)  # the lamp's warmth on the wall
    wall = np.array([132, 86, 52.])[None, None, :] * (0.55 + 0.9 * glow[..., None]) * (0.9 + 0.2 * n[..., None])
    iw.rgb = wall
    iw.a[:] = 1
    iw.poly([(0.45, 1.15), (1.35, 1.15), (1.35, 1.85), (0.45, 1.85)], (70, 46, 30), 0.9)       # a picture frame
    iw.poly([(0.53, 1.23), (1.27, 1.23), (1.27, 1.77), (0.53, 1.77)], (150, 120, 80), 0.85)    # its pale picture
    iw.poly([(-5, -0.2), (5, -0.2), (5, 0.12), (-5, 0.12)], (80, 50, 30), 1.0)                 # skirting
    meta.append(iw.save())
    inear = Plane('interior_near', Z['interior_near'], -3, 3, -0.2, 2.8, 160)
    # a lamp on a small table
    inear.poly([(-1.05, 0), (-1.0, 0), (-0.98, 0.62), (-1.07, 0.62)], (60, 36, 22), 1.0)
    inear.poly([(-1.35, 0.62), (-0.7, 0.62), (-0.7, 0.68), (-1.35, 0.68)], (70, 42, 26), 1.0)
    inear.poly([(-1.04, 0.68), (-1.0, 0.68), (-1.0, 1.05), (-1.04, 1.05)], (50, 30, 20), 1.0)
    shade = Image.new('L', (inear.w, inear.h), 0)
    ImageDraw.Draw(shade).polygon([inear.px(-1.2, 1.05), inear.px(-0.84, 1.05), inear.px(-0.92, 1.3), inear.px(-1.12, 1.3)], fill=255)
    inear.lay(shade, (255, 214, 150), 1.0, blur=1)
    lg = Image.new('L', (inear.w, inear.h), 0)
    ImageDraw.Draw(lg).ellipse([inear.px(-1.7, 1.75), inear.px(-0.35, 0.45)], fill=255)
    inear.lay(lg, (255, 200, 130), 0.35, blur=40)
    # a chair back
    inear.poly([(0.55, 0), (0.6, 0), (0.6, 0.95), (0.55, 0.95)], (54, 34, 22), 1.0)
    inear.poly([(1.05, 0), (1.1, 0), (1.1, 0.95), (1.05, 0.95)], (54, 34, 22), 1.0)
    inear.poly([(0.5, 0.42), (1.15, 0.42), (1.15, 0.5), (0.5, 0.5)], (60, 38, 24), 1.0)
    inear.poly([(0.55, 0.75), (1.1, 0.75), (1.1, 0.95), (0.55, 0.95)], (60, 38, 24), 1.0)
    # the bowl: cut from the archive dog film (frame 0, the bowl at the bottom of the shot), keyed, warmed
    src = Image.open(os.path.join(KIT, 'archive-dog/frames/f000.jpg')).convert('L')
    bowl = src.crop((240, 222, 320, 265)).resize((int(0.36 * inear.ppm), int(0.17 * inear.ppm)), Image.LANCZOS)
    ba = np.asarray(bowl, np.float32) / 255
    bm = Image.new('L', bowl.size, 0)
    ImageDraw.Draw(bm).ellipse([2, 2, bowl.size[0] - 3, bowl.size[1] - 3], fill=255)
    bm = np.asarray(bm.filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
    bx, by = inear.px(-0.42, 0.17)
    bx, by = int(bx), int(by)
    hb, wb = ba.shape
    tint = np.stack([ba * 230, ba * 170, ba * 110], -1)
    sl = (slice(by, by + hb), slice(bx, bx + wb))
    inear.rgb[sl] = inear.rgb[sl] * (1 - bm[..., None]) + tint * bm[..., None]
    inear.a[sl] = np.maximum(inear.a[sl], bm)
    meta.append(inear.save())

    # ---------------------------------------------------------------- the house front (z 5.0), with the doorway cut out
    wl = Plane('wall', Z['wall'], -7, 5.35, -0.05, 4.2, 240)
    n1 = noise(wl.h, wl.w, 90, 31)
    n2 = noise(wl.h, wl.w, 12, 32, 2)
    yy = (wl.Y1 - np.arange(wl.h)[:, None] / wl.ppm)
    board = 0.86 + 0.14 * ((yy % 0.17) / 0.17)       # clapboards: each board darkens to its lower edge
    seam = np.where((yy % 0.17) < 0.012, 0.6, 1.0)
    tex = board * seam * (0.85 + 0.25 * n1) * (0.9 + 0.12 * n2)
    wl.rgb = np.array([56, 66, 74.])[None, None, :] * tex[..., None]
    wl.a[:] = 1
    # the window left of the door, curtained, faintly warm
    wl.poly([(-3.05, 0.85), (-1.95, 0.85), (-1.95, 2.05), (-3.05, 2.05)], (34, 34, 38), 1.0)
    win = Image.new('L', (wl.w, wl.h), 0)
    ImageDraw.Draw(win).rectangle([wl.px(-2.98, 1.98), wl.px(-2.02, 0.92)], fill=255)
    wl.lay(win, (150, 104, 66), 0.85, blur=3)
    wl.poly([(-2.52, 0.92), (-2.48, 0.92), (-2.48, 1.98), (-2.52, 1.98)], (40, 36, 36), 1.0)
    wl.poly([(-2.98, 1.43), (-2.02, 1.43), (-2.02, 1.47), (-2.98, 1.47)], (40, 36, 36), 1.0)
    # door trim
    wl.poly([(-0.62, 0), (0.62, 0), (0.62, 2.24), (-0.62, 2.24)], (78, 80, 82), 1.0)
    wl.poly([(-0.66, 2.18), (0.66, 2.18), (0.66, 2.3), (-0.66, 2.3)], (86, 88, 90), 1.0)
    # house corner board
    wl.poly([(5.12, -0.05), (5.35, -0.05), (5.35, 4.2), (5.12, 4.2)], (70, 76, 82), 1.0)
    # cut the doorway out of the glass
    hole = Image.new('L', (wl.w, wl.h), 0)
    ImageDraw.Draw(hole).rectangle([wl.px(-0.46, 2.08), wl.px(0.46, -0.05)], fill=255)
    hm = np.asarray(hole, np.float32) / 255
    wl.a *= 1 - hm
    meta.append(wl.save())

    # ---------------------------------------------------------------- porch posts (z 3.85)
    po = Plane('posts', Z['porch_edge'] + 0.05, -6, 6, -0.5, 4.0, 200)
    for X in (-3.4, 1.55):
        po.poly([(X - 0.065, -0.5), (X + 0.065, -0.5), (X + 0.065, 4), (X - 0.065, 4)], (40, 44, 50), 1.0)
        po.poly([(X - 0.065, -0.5), (X - 0.03, -0.5), (X - 0.03, 4), (X - 0.065, 4)], (58, 62, 70), 0.6)
    # the eave fascia across the top
    po.poly([(-6, 2.62), (6, 2.62), (6, 4.0), (-6, 4.0)], (28, 30, 38), 1.0)
    meta.append(po.save())

    # ---------------------------------------------------------------- foreground weeds (z 1.9) and hanging leaves (z 2.1)
    fg = Plane('grass', Z['grass'], -4, 6, -0.5, 1.2, 160)
    m = Image.new('L', (fg.w, fg.h), 0)
    d = ImageDraw.Draw(m)
    rr = random.Random(7)
    for k in range(200):
        X = rr.uniform(-4, 6)
        # weeds thicken towards the frame edges, leaving the middle of the porch open
        dense = 1.0 if (X < -0.9 or X > 3.3) else 0.25
        if rr.random() > dense:
            continue
        hgt = rr.uniform(0.25, 1.0) * (1.0 if dense == 1.0 else 0.6)
        bend = rr.uniform(-0.25, 0.25)
        pts = [fg.px(X + bend * (s ** 2), -0.5 + hgt * s) for s in np.linspace(0, 1, 8)]
        d.line(pts, fill=255, width=int(rr.uniform(0.008, 0.02) * fg.ppm))
        if rr.random() < 0.3:  # seed heads
            hx, hy = pts[-1]
            d.ellipse([hx - 4, hy - 9, hx + 4, hy + 3], fill=255)
    fg.lay(m, (16, 18, 24), 1.0, blur=0)
    meta.append(fg.save())
    lv = Plane('leaves', Z['grass'] + 0.2, -5, 7, 1.2, 3.4, 160)
    m = Image.new('L', (lv.w, lv.h), 0)
    d = ImageDraw.Draw(m)
    rr = random.Random(8)
    for k in range(9):
        X = rr.uniform(-4.5, 6.5)
        L = rr.uniform(0.5, 1.6)
        pts = [lv.px(X + 0.08 * math.sin(s * 5), 3.4 - L * s) for s in np.linspace(0, 1, 12)]
        d.line(pts, fill=255, width=4)
        for s in np.linspace(0.05, 1, 9):
            px_, py_ = lv.px(X + 0.08 * math.sin(s * 5), 3.4 - L * s)
            sz = rr.uniform(14, 26)
            dx = sz * (1 if rr.random() < 0.5 else -1)
            d.polygon([(px_, py_), (px_ + dx, py_ + sz * 0.4), (px_ + dx * 0.4, py_ + sz * 0.9)], fill=255)
    lv.lay(m, (14, 16, 22), 1.0)
    meta.append(lv.save())

    json.dump(meta, open(os.path.join(OUT, 'planes.json'), 'w'), indent=1)

    # ---------------------------------------------------------------- the fog: density keyed from time-lapse cloud footage
    CLOUD = os.path.join(FOLDER, 'assets/found/cloud')  # copied from secondhand-motion/shots/cloud-sam/frames
    frames = sorted(f for f in os.listdir(CLOUD) if f.endswith('.jpg'))
    dens, inner = [], []
    for f in frames:
        im = np.asarray(Image.open(os.path.join(CLOUD, f)).convert('RGB'), np.float32)
        mn = im.min(2)
        sat = im.max(2) - mn
        dd = np.clip((mn - 90) / 130, 0, 1) * np.clip(1 - (sat - 40) / 120, 0, 1)  # white, unsaturated = cloud
        dens.append(dd[60:216])  # the cloud bank, with its top edge (used as the top of ground fog)
        lum = np.asarray(Image.fromarray(mn.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), np.float32)[110:216]
        inner.append(np.clip((lum - 150) / 90, 0, 1))  # inside the bank: the shading of the puffs
    dens = np.stack(dens)  # (62, 156, 384)
    inner = np.stack(inner)
    inner = np.concatenate([inner, inner[:, ::-1]], 1)  # (62, 212, 384), mirrored vertically to be taller
    # mirror-tile into wide, seamless strips so the fog can drift for 32 s
    strip = np.concatenate([dens, dens[:, :, ::-1]], 2)
    np.save(os.path.join(CACHE, 'fog_cloud.npy'), strip.astype(np.float16))
    np.save(os.path.join(CACHE, 'fog_inner.npy'), np.concatenate([inner, inner[:, :, ::-1]], 2).astype(np.float16))
    print('planes', [m_['name'] for m_ in meta], 'fog', strip.shape)


if __name__ == '__main__':
    build()
