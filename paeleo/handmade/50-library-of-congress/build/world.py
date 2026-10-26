"""Pl. I, the place: a sectional elevation of a house and its porch at dusk, engraved.
Builds cache/world.npz: static ink (inkS), wash fields, masks; and plates for the door leaf and the bench.
Documented material: the door leaf (Straight Talk, NTIS 1992, frame f030) and the fieldstone of the wall (the pillar beside
which the dog walks in Amateur Film New Jersey C, frame f000). Everything else here is drawn for this plate."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from eng import engrave, screen, poly_mask, blur, blurf, contour, dilate, erode
KIT = os.path.join(HERE, '..', '..', 'kit')
OUT = os.path.join(HERE, 'cache'); os.makedirs(os.path.join(OUT, 'plates'), exist_ok=True)
W, H = 1280, 720
SS = 2
S = 190.0                    # px per metre
XS = 318.0                   # screen x of score x = 0 (the inner face of the wall)
YG = 548.0                   # porch floor line
WALL = (318.0, 420.0)        # wall section, inner and outer face
LINTEL = YG - 2.0 * S        # 168
CEIL = 112.0
STEP_X = XS + 4.9 * S        # 1249: top of the porch steps
PLATE = (26, 22, 1254, 640)  # the engraved image area; margin below carries the key

def sx(x): return XS + x * S

def hi(polys):
    return poly_mask((H * SS, W * SS), polys, SS)

def rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def scan_gray(path, box, size):
    im = Image.open(path).convert('L').crop(box).resize(size, Image.BICUBIC)
    a = np.asarray(im, np.float32) / 255.
    lo, hi_ = np.percentile(a, 3), np.percentile(a, 97)
    return np.clip((a - lo) / (hi_ - lo + 1e-4), 0, 1)

def build():
    HH, WW = H * SS, W * SS
    yy, xx = np.mgrid[0:HH, 0:WW].astype(np.float32) / SS
    ink = np.zeros((HH, WW), np.float32)
    def put(mask, tone, angle, period=3.2, warp=0.0, cross=None, aa=0.9):
        nonlocal ink
        t = tone if np.ndim(tone) else np.full((HH, WW), tone, np.float32)
        e = engrave(t * mask, angle, period * SS, warp, cross, aa=aa * SS) if cross is not None else screen(t * mask, angle, period * SS, None, 0, aa * SS)
        ink = np.maximum(ink * (1 - mask), e * mask) if True else ink
    def line(pts, w=1.6, layer=None):
        im = Image.new('L', (WW, HH), 0); d = ImageDraw.Draw(im)
        d.line([(p[0] * SS, p[1] * SS) for p in pts], fill=255, width=max(1, int(w * SS)), joint='curve')
        return np.asarray(im, np.float32) / 255.

    def stones(region, tone_src, y_top, y_bot):
        nonlocal ink
        r2 = np.random.default_rng(int(y_top))
        polys, tones = [], []
        y = y_top
        while y < y_bot:
            hh = r2.uniform(16, 30); x = WALL[0] - r2.uniform(0, 30)
            while x < WALL[1]:
                ww = r2.uniform(26, 52)
                j = lambda: r2.uniform(-2.5, 2.5)
                P = [(x + j(), y + j()), (x + ww + j(), y + j()), (x + ww + j(), y + hh + j()), (x + j(), y + hh + j())]
                polys.append(P); x += ww
            y += hh
        for P in polys:
            m = hi([P]) * region
            if m.sum() < 1: continue
            tv = float((tone_src * m).sum() / max(m.sum(), 1))
            mi = erode(m, int(1.6 * SS))
            ang = r2.uniform(30, 60)
            e = screen(np.clip(mi * (0.22 + 0.6 * tv) * np.clip(1 - 0.5 * (yy - min(p[1] for p in P)) / 30, 0.4, 1), 0, 1), ang, 2.4 * SS, None, 0, 0.9 * SS)
            ink = ink * (1 - m) + m * np.maximum(e, (m - mi) * 0.95)
    plate = hi([rect(*PLATE)])
    # --- sky, outside: horizontal rules, denser toward the top (dusk); a low horizon of fields and trees
    sky = hi([rect(WALL[1], PLATE[1], PLATE[2], YG)]) * plate
    sky_t = np.clip(0.14 + 0.46 * np.clip(1 - (yy - 60) / (YG - 60), 0, 1) ** 1.5, 0, 1)
    put(sky, sky_t, 90, 3.0)
    # distant ground beyond the porch (seen below the railing line, a darker band) and trees
    rng = np.random.default_rng(7)
    hor = 505.0
    tree = []
    x = WALL[1] + 40
    while x < PLATE[2]:
        w_ = rng.uniform(26, 80); h_ = rng.uniform(8, 30)
        pts = [(x, hor)]
        for k in range(9):
            a = np.pi * k / 8
            pts.append((x + w_ / 2 - np.cos(a) * w_ / 2 + rng.uniform(-4, 4), hor - np.sin(a) * h_ * rng.uniform(0.8, 1.1)))
        pts.append((x + w_, hor)); tree.append(pts)
        x += w_ * rng.uniform(0.6, 1.4)
    trees = hi(tree + [rect(WALL[1], hor, PLATE[2], YG)]) * sky
    put(trees, np.full((HH, WW), 0.42, np.float32), 80, 2.6, cross=None)
    # moon, a thin crescent (paper left white inside)
    moon_o = hi([[(1010 + 22 * np.cos(a), 222 + 22 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 40)]])
    moon_i = hi([[(1019 + 20 * np.cos(a), 216 + 20 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 40)]])
    moon = moon_o * (1 - moon_i)
    ink = ink * (1 - moon_o) + moon_i * moon_o * screen(np.full((HH, WW), 0.5, np.float32), 90, 3.0 * SS, None, 0, 0.9 * SS)
    ink = np.maximum(ink, contour(moon, 1) * 0.8)
    # --- porch roof (section) and its post at the steps
    roof = hi([[(WALL[0] - 10, 150), (PLATE[2], 150), (PLATE[2], 126), (WALL[0] - 10, 96)]])
    put(roof, np.full((HH, WW), 0.55, np.float32), 45, 2.4, cross=0.3)
    fascia = hi([rect(WALL[1], 150, PLATE[2], 162)])
    put(fascia, np.full((HH, WW), 0.35, np.float32), 90, 2.2)
    post = hi([rect(STEP_X - 22, 162, STEP_X - 8, YG)])
    put(post, np.clip(0.35 + 0.35 * (xx - (STEP_X - 22)) / 14, 0, 1), 90, 2.4)
    # --- the interior: walls with a wainscot, floorboards in elevation, a lamp on a table, a hanging print
    room = hi([rect(PLATE[0], CEIL, WALL[0], YG)])
    wall_t = 0.42 + 0.0 * xx
    put(room, wall_t, 90, 3.4, warp=0.0, cross=None)
    wains = hi([rect(PLATE[0], 430, WALL[0], YG)])
    put(wains, np.full((HH, WW), 0.55, np.float32), 0, 3.0)
    ink = np.maximum(ink, line([(PLATE[0], 430), (WALL[0], 430)], 2.2) + line([(PLATE[0], 437), (WALL[0], 437)], 1.0))
    ceil = hi([rect(PLATE[0], PLATE[1], WALL[1], CEIL)])
    put(ceil, np.full((HH, WW), 0.62, np.float32), 45, 2.4, cross=0.3)
    # table and lamp (drawn)
    tbl = hi([rect(70, 452, 176, 462), rect(78, 462, 86, YG), rect(160, 462, 168, YG)])
    ink = ink * (1 - tbl) + tbl * 0.92
    lamp_base = hi([[(108, 452), (138, 452), (132, 440), (126, 420), (120, 420), (114, 440)]])
    ink = ink * (1 - lamp_base) + lamp_base * screen(np.full((HH, WW), 0.7, np.float32), 90, 2.0 * SS, None, 0, 0.9 * SS)
    chimney = hi([[(117, 420), (129, 420), (131, 404), (128, 372), (118, 372), (115, 404)]])
    ink = ink * (1 - chimney) + np.maximum(ink * 0, contour(chimney, 1)) * chimney
    shade = hi([[(96, 380), (150, 380), (140, 352), (106, 352)]])
    ink = ink * (1 - shade) + shade * np.maximum(contour(shade, 1), screen(np.full((HH, WW), 0.18, np.float32), 90, 2.6 * SS, None, 0, 0.9 * SS))
    # a small framed print on the wall (blank paper with a plate mark: the room's own print, unattributed)
    fr = hi([rect(180, 250, 262, 320)]); fr_in = hi([rect(186, 256, 256, 314)])
    ink = ink * (1 - fr) + (fr - fr_in) * 0.9 + fr_in * screen(np.full((HH, WW), 0.12, np.float32), 30, 3.0 * SS, None, 0, 0.9 * SS)
    # --- wall section above the lintel and the fieldstone of the house (engraved after the pillar in the dog film)
    stone_src = os.path.join(KIT, 'archive-dog', 'frames', 'f000.jpg')
    st = scan_gray(stone_src, (324, 46, 384, 286), (int((WALL[1] - WALL[0]) * SS), int((LINTEL - CEIL + 70) * SS)))
    stone_t = np.zeros((HH, WW), np.float32)
    y0 = int((CEIL - 70) * SS)
    stone_t[y0:y0 + st.shape[0], int(WALL[0] * SS):int(WALL[0] * SS) + st.shape[1]] = 1 - st
    wall_up = hi([rect(WALL[0], PLATE[1], WALL[1], LINTEL)])
    stones(wall_up, stone_t, PLATE[1], LINTEL)
    ink = np.maximum(ink, contour(wall_up, 2.0) * 1.0)
    # lintel beam
    lint = hi([rect(WALL[0] - 4, LINTEL - 16, WALL[1] + 4, LINTEL)])
    put(lint, np.full((HH, WW), 0.5, np.float32), 0, 2.2)
    ink = np.maximum(ink, contour(lint, 1.5))
    # the far jamb of the doorway seen through the section: a casing on each face and the reveal between
    reveal = hi([rect(WALL[0], LINTEL, WALL[1], YG)])
    put(reveal, np.full((HH, WW), 0.30, np.float32), 90, 3.4)
    for xc in (WALL[0] + 1, WALL[0] + 8, WALL[1] - 8, WALL[1] - 1):
        ink = np.maximum(ink, line([(xc, LINTEL), (xc, YG)], 1.4))
    # --- floors in section: the porch boards with joists below, the interior floor, the sill stone
    floor = hi([rect(PLATE[0], YG, STEP_X, YG + 16)])
    put(floor, np.full((HH, WW), 0.5, np.float32), -45, 2.2)
    ink = np.maximum(ink, line([(PLATE[0], YG), (STEP_X, YG)], 2.4))
    for xb in np.arange(WALL[1] + 30, STEP_X, 56):
        jo = hi([rect(xb, YG + 16, xb + 12, YG + 44)]); put(jo, np.full((HH, WW), 0.7, np.float32), 45, 2.0)
    under = hi([rect(WALL[1], YG + 16, STEP_X, PLATE[3])])
    put(under, np.full((HH, WW), 0.6, np.float32), 90, 2.4, cross=0.5)
    sill = hi([rect(WALL[0], YG - 3, sx(0.64), YG + 22)])
    put(sill, np.full((HH, WW), 0.28, np.float32), 30, 2.0)
    ink = np.maximum(ink, contour(sill, 1.6))
    found = hi([rect(PLATE[0], YG + 16, WALL[1], PLATE[3])])
    put(found, np.clip(0.35 + (1 - np.pad(stone_t, 0)[:, :]) * 0, 0, 1), 45, 2.4, cross=None)
    # the foundation under the wall is stone too
    st2 = scan_gray(stone_src, (324, 120, 384, 286), (int((WALL[1] - WALL[0]) * SS), int((PLATE[3] - YG) * SS)))
    s2 = np.zeros((HH, WW), np.float32); y1 = int((YG + 22) * SS)
    hh = min(st2.shape[0], HH - y1)
    s2[y1:y1 + hh, int(WALL[0] * SS):int(WALL[0] * SS) + st2.shape[1]] = 1 - st2[:hh]
    fw = hi([rect(WALL[0], YG + 22, WALL[1], PLATE[3])])
    stones(fw, s2, YG + 22, PLATE[3])
    # steps down at the porch end
    for k in range(3):
        stp = hi([rect(STEP_X + k * 0, YG + 16 + k * 26, PLATE[2], YG + 22 + k * 26)])
        ink = np.maximum(ink, stp * 0.9)
    # --- a low stool inside, beside the door (drawn)
    bench = hi([rect(168, 462, 232, 471), rect(173, 471, 180, YG), rect(220, 471, 227, YG), rect(178, 510, 222, 515)])
    put(bench, np.full((HH, WW), 0.8, np.float32), 90, 2.0)
    ink = np.maximum(ink, contour(bench, 1.2))
    # plate mark and frame rule
    pm = hi([rect(*PLATE)]) - hi([rect(PLATE[0] + 2, PLATE[1] + 2, PLATE[2] - 2, PLATE[3] - 2)])
    ink = np.maximum(ink, pm)
    ink = ink * plate + pm

    def dn(a):
        im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)); return np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255.
    inkS = dn(ink)
    # washes (watercolour applied over the print by hand): dusk blue outside, warm lamp inside, a spill mask through the door
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    outside = (X > WALL[1]) & (Y < YG) & (Y > 150) & (X < PLATE[2] - 1)
    wash_dusk = np.zeros((H, W), np.float32); wash_dusk[outside] = 1
    wash_dusk = blur(wash_dusk, 2) * np.clip(0.55 + 0.45 * (1 - (Y - 150) / (YG - 150)), 0, 1)
    room_m = ((X < WALL[0]) & (Y > CEIL) & (Y < YG) & (X > PLATE[0])).astype(np.float32)
    lamp_glow = np.exp(-(((X - 123) / 170) ** 2 + ((Y - 380) / 190) ** 2))
    wash_room = room_m * np.clip(0.45 + 0.75 * lamp_glow, 0, 1)
    # light out of the opening: the reveal, the porch floor in a widening wedge, and a soft fall-off in the air
    reveal_m = ((X >= WALL[0]) & (X <= WALL[1]) & (Y > LINTEL) & (Y < YG + 2)).astype(np.float32)
    dxp = np.clip(X - WALL[1], 0, None)
    spread = LINTEL + (YG - LINTEL) * np.clip(dxp / 900, 0, 1) * 0.0
    wedge = ((X > WALL[1]) & (Y > LINTEL + dxp * 0.42) & (Y < YG + 2)).astype(np.float32) * np.exp(-dxp / 520)
    floor_pool = ((Y > YG - 30) & (Y < YG + 3) & (X > WALL[1])).astype(np.float32) * np.exp(-dxp / 360)
    spill = np.clip(reveal_m * 0.95 + blur(wedge, 6) * 0.75 + blur(floor_pool, 4) * 0.6, 0, 1) * (X < PLATE[2] - 1)
    np.savez_compressed(os.path.join(OUT, 'world.npz'), inkS=inkS, wash_dusk=wash_dusk, wash_room=wash_room, spill=spill)

def door_plate():
    """the door leaf, engraved after Straight Talk f030 (crop of the white door with its curtained window)."""
    src = os.path.join(KIT, 'archive-door', 'frames', 'f030.jpg')
    w, h = int(0.9 * S * SS), int(2.0 * S * SS)
    g = scan_gray(src, (116, 0, 234, 272), (w, h))
    tone = np.clip((1 - g) * 0.75 + 0.08, 0, 1)
    ink = engrave(tone, 90, 2.6 * SS, 0.8, 0.6)
    m = np.ones_like(tone)
    ink = np.maximum(ink, contour(np.pad(m[2:-2, 2:-2], 2), 1.5 * SS))
    im = Image.fromarray(np.clip(ink * 255, 0, 255).astype(np.uint8)).resize((w // SS, h // SS), Image.LANCZOS)
    z = Image.new('L', im.size, 0); a = Image.new('L', im.size, 255)
    Image.merge('RGBA', (im, z, z, a)).save(os.path.join(OUT, 'plates', 'door_leaf.png'))

if __name__ == '__main__':
    build(); door_plate(); print('world ok')
