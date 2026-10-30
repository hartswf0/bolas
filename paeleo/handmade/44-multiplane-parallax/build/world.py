"""The depth scene graph: collage planes cut from rights-recorded archive frames, set at measured depths.

Every plane is a typed record: name, kind ('card' = vertical plane parallel to the film at depth Z, 'quad' = a plane
in any orientation given by four 3D corners, mapped by its own homography: the per-plane projection), its world
rectangle, its RGBA image (premultiplied later), the fragments it was cut from, and its atmosphere (fog) factor.
"""
import os, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps, ImageEnhance
from common import *

RNG = np.random.default_rng(44)
SRC = {
    'cloud': SHOTS + '/cloud-sam/frames/f000.jpg',
    'cloud2': SHOTS + '/cloud-sam/frames/f040.jpg',
    'windmill': SHOTS + '/windmill-sam/frames/f000.jpg',
    'windmill2': SHOTS + '/windmill-sam/frames/f030.jpg',
    'door': SHOTS + '/door-sam/frames/f000.jpg',
    'doorway': KIT + '/archive-door/frames/f020.jpg',
    'bulb': SHOTS + '/light-bulb-sam/frames/f020.jpg',
    'lantern': SHOTS + '/lantern-sam/frames/f010.jpg',
    'horse': SHOTS + '/horse-sam/frames/f000.jpg',
    'dog0': KIT + '/archive-dog/frames/f000.jpg',
    'dog10': KIT + '/archive-dog/frames/f010.jpg',
    'river': SHOTS + '/river-sam/frames/f000.jpg',
    'book': SHOTS + '/book-sam/frames/f020.jpg',
    'flower': SHOTS + '/flower-sam/frames/f000.jpg',
}
USED = {}   # fragment id -> {src, box, operation}


def frag(key, box, op, size=None):
    im = Image.open(SRC[key]).convert('RGB').crop(box)
    USED.setdefault(f'{key}:{box}', {'src': SRC[key], 'box': list(box), 'ops': set()})['ops'].add(op)
    if size:
        im = im.resize(size, Image.BICUBIC)
    return im


def arr(im):
    return np.asarray(im, np.float32) / 255.0


def img(a):
    return Image.fromarray(np.clip(a * 255 + .5, 0, 255).astype(np.uint8))


def tint(a, col, amt=1.0):
    """duotone: luminance remapped into a colour (dusk grading of a found fragment)."""
    l = a[..., :3].mean(-1, keepdims=True) if a.ndim == 3 else a[..., None]
    out = l * np.array(col, np.float32)
    return out if amt >= 1 else a[..., :3] * (1 - amt) + out * amt


def paper_edge(alpha, seed, rough=2.0):
    """hand-cut edge: jitter the alpha boundary with low-frequency noise (scissors), keep it crisp."""
    h, w = alpha.shape
    r = np.random.default_rng(seed)
    n = r.standard_normal((h // 8 + 2, w // 8 + 2)).astype(np.float32)
    n = np.asarray(Image.fromarray(n).resize((w, h), Image.BICUBIC))
    blur = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rough)), np.float32) / 255
    return np.clip((blur + n * 0.12 - 0.5) * 6 + 0.5, 0, 1)


def rgba(rgb, a):
    return np.dstack([rgb, a])


# ---------------------------------------------------------------- planes
def sky():
    """Z=140: a strip of found cumulus (Top Of The Cloud) re-graded as dusk; a Quick, Draw! moon cut from paper."""
    X0, X1, Y0, Y1, Z = -110, 120, -40, 95, 140.0
    p = 6.0
    w, h = int((X1 - X0) * p), int((Y1 - Y0) * p)
    yy = np.linspace(0, 1, h)[:, None, None]
    top = np.array([0.10, 0.11, 0.24]); mid = np.array([0.36, 0.30, 0.42]); low = np.array([0.86, 0.55, 0.36])
    g = np.where(yy < .55, top + (mid - top) * (yy / .55), mid + (low - mid) * ((yy - .55) / .45))
    out = np.broadcast_to(g, (h, w, 3)).copy()
    # cloud bands: torn horizontal strips of the found clouds, screened into the gradient
    for k, (key, yb, xs, sc) in enumerate([('cloud', (60, 150), 0.0, 1.0), ('cloud2', (70, 190), 0.45, 1.2), ('cloud', (95, 200), 0.8, .9)]):
        c = arr(frag(key, (0, yb[0], 384, yb[1]), 'crop, luminance key, dusk duotone, torn edge'))
        lum = c.mean(-1)
        blue = np.clip((c[..., 2] - c[..., 0]) * 3, 0, 1)
        a = np.clip((lum - 0.55) * 2.5, 0, 1) * (1 - blue)
        cw = int(w * 0.42 * sc); ch = int(cw * c.shape[0] / c.shape[1])
        ci = img(tint(c, (1.0, 0.72, 0.62))).resize((cw, ch), Image.BICUBIC)
        ai = Image.fromarray((a * 255).astype(np.uint8)).resize((cw, ch), Image.BICUBIC)
        ca, aa = arr(ci), arr(ai)
        x0 = int(xs * w); y0 = int(h * (0.38 + 0.08 * k))
        sl = out[y0:y0 + ch, x0:x0 + cw]
        cw2, ch2 = sl.shape[1], sl.shape[0]
        lit = 0.55 + 0.35 * k / 2
        sl[:] = sl * (1 - aa[:ch2, :cw2, None] * .75) + ca[:ch2, :cw2] * lit * aa[:ch2, :cw2, None] * .75
    im = img(out)
    # moon: a real Quick, Draw! moon doodle, filled and cut as pale paper
    d = json.loads(open('/home/user/hartswf0/quickdraw/moon.part').readline())
    USED['quickdraw-moon'] = {'src': '/home/user/hartswf0/quickdraw/moon.part', 'key_id': d['key_id'], 'ops': {'stroke polygon fill, paper cut'}}
    mo = Image.new('L', (256, 256), 0); dr = ImageDraw.Draw(mo)
    for sx, sy in d['drawing']:
        if len(sx) > 2:
            dr.polygon(list(zip(sx, sy)), fill=255)
        dr.line(list(zip(sx, sy)), fill=255, width=6)
    msz = int(9 * p)
    mo = mo.resize((msz, msz), Image.BICUBIC).filter(ImageFilter.GaussianBlur(.6))
    mx, my = int((-38 - X0) * p), int((Y1 - 62) * p)
    glow = mo.filter(ImageFilter.GaussianBlur(14)).point(lambda v: v * .5)
    im.paste(Image.new('RGB', mo.size, (250, 214, 160)), (mx, my), glow)
    im.paste(Image.new('RGB', mo.size, (246, 232, 200)), (mx, my), mo)
    a = np.ones((h, w), np.float32)
    return dict(name='sky', kind='card', Z=Z, rect=(X0, X1, Y0, Y1), img=rgba(arr(im), a), fog=0.0)


def treeline(Z, X0, X1, Ytop, seed, dark, fog, keys, scale):
    """trees: dark pine masses keyed out of the Golden Gate windmill footage (tree-only boxes, sky behind them),
    cut with feathered sides, repeated, flipped and re-scaled into a treeline; the ground under them is filled dark."""
    p = 1000.0 / (Z + 5.5) * 1.4
    w, h = int((X1 - X0) * p), int((Ytop + 1.5) * p)
    out = np.zeros((h, w, 3), np.float32) + np.array(dark, np.float32) * 0.5
    al = np.zeros((h, w), np.float32)
    r = np.random.default_rng(seed)
    boxes = [('windmill', (268, 128, 372, 252)), ('windmill2', (268, 128, 372, 252)), ('windmill', (0, 60, 48, 262))]
    x = -int(w * 0.02)
    while x < w:
        key, box = boxes[r.integers(len(boxes))]
        f = arr(frag(key, box, 'crop, luminance key (trees darker than the sky), duotone, flip, feather'))
        lum = f.mean(-1)
        a = np.clip((0.58 - lum) * 5, 0, 1)
        if r.random() < .5:
            f, a = f[:, ::-1], a[:, ::-1]
        th = int(h * r.uniform(0.6, 1.0) * scale)
        tw = int(th * f.shape[1] / f.shape[0] * r.uniform(1.0, 1.8))
        fi = arr(img(f).resize((tw, th), Image.BICUBIC)); ai = arr(Image.fromarray((a * 255).astype(np.uint8)).resize((tw, th), Image.BICUBIC))
        ai = ai * np.minimum(1, np.minimum(np.linspace(0, 6, tw), np.linspace(6, 0, tw)))[None, :]
        k = max(2, th // 5)
        ai[-k:] = np.maximum(ai[-k:], np.minimum(1, np.minimum(np.linspace(0, 3, tw), np.linspace(3, 0, tw)))[None, :])
        y0 = h - th
        xa, xb = max(0, x), min(w, x + tw)
        if xb > xa:
            sl = slice(y0, h), slice(xa, xb)
            aa = ai[:, xa - x:xb - x]
            col = tint(fi[:, xa - x:xb - x], dark) * r.uniform(.85, 1.1)
            out[sl] = out[sl] * (1 - aa[..., None]) + col * aa[..., None]
            al[sl] = np.maximum(al[sl], aa)
        x += int(tw * r.uniform(.35, .6))
    gy = int(Ytop * p)
    al[gy:] = 1.0; out[gy:] = np.array(dark, np.float32) * 1.6 + 0.12
    return dict(name=f'trees_{Z:g}', kind='card', Z=Z, rect=(X0, X1, -1.5, Ytop), img=rgba(out, al), fog=fog)


def clapboard_wall():
    """Z=0: the house front. Clapboards cut as strips from found paper and plaster (the Straight Talk door, book pages,
    the vase), graded to dusk blue; a lit window; the door opening is a hole (the occlusion edge)."""
    X0, X1, Y0, Y1 = -4.6, 3.15, -0.02, 3.3
    p = 260.0
    w, h = int((X1 - X0) * p), int((Y1 - Y0) * p)
    out = np.zeros((h, w, 3), np.float32)
    r = np.random.default_rng(7)
    src = arr(frag('door', (300, 0, 372, 250), 'crop, grain only (clapboard)')).mean(-1)
    gimg = Image.fromarray((src * 255).astype(np.uint8)).rotate(90, expand=True)
    bh = int(0.16 * p)
    y = h
    while y > 0:
        x = 0
        while x < w:
            seg = int(r.uniform(1.6, 3.2) * p)
            g = np.asarray(gimg.resize((seg, bh), Image.BICUBIC), np.float32) / 255
            g = (g - g.mean()) * 0.35
            tone = r.uniform(.88, 1.06)
            col = (np.array([0.31, 0.33, 0.44], np.float32) * tone)[None, None, :] * (1 + 1.6 * g[..., None])
            grad = np.linspace(1.08, 0.80, bh)[:, None, None]
            y0 = max(0, y - bh); x1 = min(w, x + seg)
            out[y0:y, x:x1] = (col * grad)[bh - (y - y0):, :x1 - x]
            out[y0:y, x:min(w, x + 2)] *= 0.6
            x = x1
        out[max(0, y - 3):y] *= 0.5
        y -= bh
    a = np.ones((h, w), np.float32)

    def box_(xa, xb, ya, yb):
        return int((xa - X0) * p), int((Y1 - yb) * p), int((xb - X0) * p), int((Y1 - ya) * p)
    im = img(out); al = Image.fromarray((a * 255).astype(np.uint8)); dr = ImageDraw.Draw(im); da = ImageDraw.Draw(al)
    # door casing (painted wood) around the opening
    trim = (150, 150, 168)
    for bx in [(-0.62, -0.46, 0, 2.2), (0.46, 0.62, 0, 2.2), (-0.62, 0.62, 2.05, 2.22)]:
        dr.rectangle(box_(*bx), fill=trim)
    dr.line([box_(0.46, 0.47, 0, 2.05)[:2], box_(0.46, 0.47, 0, 2.05)[2:]], fill=(70, 70, 86), width=3)
    # the window, left of the door (a hole too: the lit room shows through it)
    for bx in [(-2.75, -1.75, 0.85, 0.95), (-2.75, -1.75, 2.0, 2.1), (-2.75, -2.65, 0.85, 2.1), (-1.85, -1.75, 0.85, 2.1)]:
        dr.rectangle(box_(*bx), fill=trim)
    da.rectangle(box_(-2.65, -1.85, 0.95, 2.0), fill=0)
    da.rectangle(box_(-0.46, 0.46, -0.1, 2.05), fill=0)
    # mullions stay as paper strips across the window hole
    for bx in [(-2.27, -2.23, 0.95, 2.0), (-2.65, -1.85, 1.46, 1.5)]:
        dr.rectangle(box_(*bx), fill=(60, 52, 50)); da.rectangle(box_(*bx), fill=255)
    # eave: a dark band of found roof shadow
    dr.rectangle(box_(X0, X1, 3.0, Y1), fill=(28, 26, 38))
    return dict(name='house_wall', kind='card', Z=0.0, rect=(X0, X1, Y0, Y1), img=rgba(arr(im), arr(al)), fog=0.03)


def curtain():
    """Z=0.06: the curtain behind the window glass, cut from the curtained window of the Straight Talk door; lit from
    behind (translucent)."""
    X0, X1, Y0, Y1, Z = -2.68, -1.82, 0.92, 2.04, 0.06
    p = 200.0
    w, h = int((X1 - X0) * p), int((Y1 - Y0) * p)
    f = arr(frag('door', (122, 2, 196, 92), 'crop, warm, translucent (curtain)').resize((w, h), Image.BICUBIC))
    out = tint(f, (1.0, 0.80, 0.52))
    a = np.full((h, w), 0.78, np.float32)
    a[:, w // 2 - int(.06 * p): w // 2 + int(.06 * p)] = 0.25      # parted in the middle
    return dict(name='curtain', kind='card', Z=Z, rect=(X0, X1, Y0, Y1), img=rgba(out, a), fog=0.0, interior=True)


def room_back():
    """Z=3.6: the lit room's back wall: plaster cut from the warm wall behind the Anthracite lantern, a picture
    (the windmill, framed), the lamp light falling off from the lamp."""
    X0, X1, Y0, Y1, Z = -7.5, 4.0, -0.05, 4.6, 3.6
    p = 150.0
    w, h = int((X1 - X0) * p), int((Y1 - Y0) * p)
    base = arr(frag('lantern', (2, 2, 108, 168), 'crop, mirror-tile, grain only, warm (plaster)')).mean(-1)
    base = np.concatenate([base, base[:, ::-1]] * 4, 1)
    base = np.concatenate([base, base[::-1]] * 2, 0)
    g = np.asarray(Image.fromarray((base * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    t = np.repeat((0.62 + (g - g.mean()) * 0.8)[..., None], 3, 2)
    yy, xx = np.mgrid[0:h, 0:w]
    lx, ly = (-0.55 - X0) * p, (Y1 - 1.45) * p
    fall = 0.35 + 0.95 * np.exp(-(((xx - lx) / (1.6 * p)) ** 2 + ((yy - ly) / (1.4 * p)) ** 2))
    out = tint(t, (1.0, 0.78, 0.48)) * fall[..., None]
    out[int((Y1 - 0.12) * p):] *= 0.6            # skirting
    out[:int((Y1 - 2.6) * p)] *= 0.35            # above the picture rail: the ceiling's shadow
    im = img(out)
    pic = frag('windmill', (40, 10, 330, 270), 'crop, sepia, framed (a picture on the wall)').resize((int(.62 * p), int(.56 * p)))
    pic = img(tint(arr(pic), (0.95, 0.80, 0.6)) * 0.9)
    fr = Image.new('RGB', (pic.width + 14, pic.height + 14), (60, 38, 24)); fr.paste(pic, (7, 7))
    im.paste(fr, (int((-0.25 - X0) * p), int((Y1 - 2.0) * p)))
    return dict(name='room_back', kind='card', Z=Z, rect=(X0, X1, Y0, Y1), img=rgba(arr(im), np.ones((h, w), np.float32)), fog=0.0, interior=True)


def room_lamp():
    """Z=2.3: a table and the lamp: the bulb from Light Of Your Life, keyed, on a dark table cut as a silhouette."""
    X0, X1, Y0, Y1, Z = -1.35, -0.1, 0.0, 1.55, 2.3
    p = 220.0
    w, h = int((X1 - X0) * p), int((Y1 - Y0) * p)
    im = Image.new('RGB', (w, h), (0, 0, 0)); al = Image.new('L', (w, h), 0)
    dr = ImageDraw.Draw(im); da = ImageDraw.Draw(al)
    tb = (int(0.15 * p), int((Y1 - 0.75) * p), int(1.1 * p), int((Y1 - 0.70) * p))
    for b in [tb, (int(0.22 * p), tb[3], int(0.28 * p), h), (int(0.97 * p), tb[3], int(1.03 * p), h)]:
        dr.rectangle(b, fill=(48, 30, 20)); da.rectangle(b, fill=255)
    b = frag('bulb', (112, 18, 252, 262), 'crop, mask (glass ellipse + base), warm glow')
    bm = Image.new('L', b.size, 0); bd = ImageDraw.Draw(bm)
    bd.ellipse((5, 2, 135, 200), fill=255); bd.rectangle((38, 150, 102, 240), fill=255)
    bm = bm.filter(ImageFilter.GaussianBlur(1))
    bs = (int(0.26 * p), int(0.455 * p))
    b = img(tint(arr(b), (1.25, 1.05, 0.75))).resize(bs, Image.BICUBIC); bm = bm.resize(bs, Image.BICUBIC)
    bx, by = int(0.53 * p), int((Y1 - 0.70) * p) - bs[1]
    glow = Image.new('L', (w, h), 0); ImageDraw.Draw(glow).ellipse((bx - 60, by - 50, bx + bs[0] + 60, by + bs[1] + 30), fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    im.paste(Image.new('RGB', (w, h), (255, 200, 120)), (0, 0), ImageChops.invert(al))
    al = ImageChops.lighter(al, glow)
    im.paste(b, (bx, by), bm); al.paste(255, (bx, by), bm)
    return dict(name='room_lamp', kind='card', Z=Z, rect=(X0, X1, Y0, Y1), img=rgba(arr(im), arr(al)), fog=0.0, interior=True)


def boards(Xa, Xb, Za, Zb, p, key, box, col, along='z', seed=3):
    """floor boards laid along Z (they converge to the vanishing point: a depth cue); grain from the found logs."""
    w, h = int((Xb - Xa) * p), int((Zb - Za) * p)
    r = np.random.default_rng(seed)
    f = arr(frag(key, box, 'crop, rotate, grain only (boards)')).mean(-1)
    gi = Image.fromarray((f * 255).astype(np.uint8)).rotate(90, expand=True)
    out = np.zeros((h, w, 3), np.float32)
    bw = int(0.12 * p)
    for x in range(0, w, bw):
        L = int(r.uniform(1.5, 3.5) * p)
        y = -int(r.uniform(0, L))
        while y < h:
            g = np.asarray(gi.resize((bw, L), Image.BICUBIC), np.float32) / 255
            g = (g - g.mean()) * 0.45
            st = np.array(col, np.float32)[None, None, :] * r.uniform(.85, 1.05) * (1 + g[..., None])
            y0, y1 = max(0, y), min(h, y + L)
            x1 = min(w, x + bw)
            out[y0:y1, x:x1] = st[y0 - y:y1 - y, :x1 - x]
            out[max(0, y - 1):y + 1, x:x1] *= 0.6
            y += L
        out[:, x:x + 2] *= 0.55
    return out


def porch_floor():
    Xa, Xb, Za, Zb = -4.6, 4.9, -2.1, 0.0
    p = 240.0
    out = boards(Xa, Xb, Za, Zb, p, 'horse', (240, 120, 350, 145), (0.50, 0.45, 0.52))
    out = out[::-1]   # image row 0 = far edge (Z = 0)
    a = np.ones(out.shape[:2], np.float32)
    corners = [(Xa, 0, Zb), (Xb, 0, Zb), (Xb, 0, Za), (Xa, 0, Za)]
    return dict(name='porch_floor', kind='quad', corners=corners, img=rgba(out, a), fog=0.02, Z=-1.05)


def room_floor():
    Xa, Xb, Za, Zb = -7.5, 4.0, 0.0, 3.6
    p = 110.0
    out = boards(Xa, Xb, Za, Zb, p, 'horse', (240, 120, 350, 145), (0.85, 0.60, 0.38), seed=9)[::-1]
    h, w = out.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    lx, ly = (-0.55 - Xa) * p, (Zb - 2.3) * p
    out *= (0.35 + 0.9 * np.exp(-(((xx - lx) / (1.5 * p)) ** 2 + ((yy - ly) / (1.6 * p)) ** 2)))[..., None]
    im = img(out)
    # the bowl (Amateur Film New Jersey C): a familiar object on the far floor
    bw = frag('dog10', (250, 225, 330, 268), 'crop, ellipse mask, warm (the bowl)')
    bm = Image.new('L', bw.size, 0); ImageDraw.Draw(bm).ellipse((2, 2, bw.width - 2, bw.height - 2), fill=255)
    bw = img(tint(arr(bw), (1.0, 0.8, 0.55))).resize((int(.34 * p), int(.18 * p * 2.2)))
    bm = bm.resize(bw.size)
    im.paste(bw, (int((0.05 - Xa) * p), int((Zb - 1.6) * p)), bm)
    corners = [(Xa, 0, Zb), (Xb, 0, Zb), (Xb, 0, Za), (Xa, 0, Za)]
    return dict(name='room_floor', kind='quad', corners=corners, img=rgba(arr(im), np.ones((h, w), np.float32)), fog=0.0, Z=1.8, interior=True)


def door_leaf():
    """the door itself: the white door with the curtained window, cut from Straight Talk (the woman cropped away)."""
    f = frag('door', (98, 0, 200, 250), 'crop (door leaf), slight warm')
    f = f.resize((184, 410), Image.BICUBIC)
    a = np.ones((410, 184), np.float32)
    return dict(name='door_leaf', kind='leaf', img=rgba(tint(arr(f), (0.92, 0.86, 0.8)), a), fog=0.0, interior=True)


def porch_front():
    """the porch edge board and the yard (dark grass from the Blackwater refuge reeds)."""
    X0, X1, Y0, Y1, Z = -4.6, 4.9, -0.5, 0.0, -2.1
    p = 200.0
    w, h = int((X1 - X0) * p), int((Y1 - Y0) * p)
    f = arr(frag('horse', (240, 165, 350, 185), 'crop, stretch (edge board)'))
    out = tint(arr(img(f).resize((w, h))), (0.32, 0.30, 0.36))
    out[:int(.05 * p)] *= 1.4
    return dict(name='porch_front', kind='card', Z=Z, rect=(X0, X1, Y0, Y1), img=rgba(out, np.ones((h, w), np.float32)), fog=0.0)


def yard():
    Xa, Xb, Za, Zb = -16, 18, -14, 30
    p = 30.0
    f = arr(frag('river', (0, 150, 384, 288), 'crop, tile, dark duotone (grass)'))
    w, h = int((Xb - Xa) * p), int((Zb - Za) * p)
    t = np.concatenate([f, f[:, ::-1]] * 4, 1)
    t = np.concatenate([t, t[::-1]] * 3, 0)
    out = tint(arr(img(t).resize((w, h))), (0.40, 0.42, 0.50))[::-1]
    corners = [(Xa, -0.5, Zb), (Xb, -0.5, Zb), (Xb, -0.5, Za), (Xa, -0.5, Za)]
    return dict(name='yard', kind='quad', corners=corners, img=rgba(out, np.ones((h, w), np.float32)), fog=0.12, Z=10)


def steps():
    """porch steps at x = 4.9: two treads, stone from the gate pillar in the home movie."""
    X0, X1, Y0, Y1, Z = 4.9, 5.9, -0.5, 0.0, -1.0
    p = 200.0
    w, h = int((X1 - X0) * p), int((Y1 - Y0) * p)
    f = arr(frag('dog0', (330, 30, 384, 200), 'crop, stretch, duotone (stone)'))
    out = tint(arr(img(f).resize((w, h))), (0.42, 0.42, 0.48))
    a = np.ones((h, w), np.float32)
    a[:int(.25 * p), int(.5 * p):] = 0
    return dict(name='steps', kind='card', Z=Z, rect=(X0, X1, Y0, Y1), img=rgba(out, a), fog=0.0)


def railing():
    """Z=-2.1, the nearest plane: posts, rails and the porch beam, cut from the Billie corral logs. The shield plane."""
    X0, X1, Y0, Y1, Z = -4.6, 5.0, -0.02, 2.75, -2.1
    p = 220.0
    w, h = int((X1 - X0) * p), int((Y1 - Y0) * p)
    out = np.zeros((h, w, 3), np.float32); a = np.zeros((h, w), np.float32)
    log = arr(frag('horse', (240, 118, 352, 148), 'crop, stretch, rotate, dark duotone (logs)'))

    def put(xa, xb, ya, yb, vertical, shade):
        x0, x1 = int((xa - X0) * p), int((xb - X0) * p); y0, y1 = int((Y1 - yb) * p), int((Y1 - ya) * p)
        t = img(log)
        t = t.rotate(90, expand=True) if vertical else t
        t = arr(t.resize((x1 - x0, y1 - y0), Image.BICUBIC))
        out[y0:y1, x0:x1] = tint(t, (0.30, 0.27, 0.30)) * shade
        a[y0:y1, x0:x1] = 1
    for px in (-3.35, 2.15, 4.8):
        put(px - 0.06, px + 0.06, 0, 2.6, True, 1.0)
    put(-4.6, 4.86, 0.06, 0.12, False, 0.9)        # bottom rail
    put(-4.6, 5.0, 2.55, 2.75, False, 0.7)         # porch beam
    a[:, int((4.86 - X0) * p):int((4.74 - X0) * p) + 1] *= 1
    # an opening in the rail where the steps are (x > 4.86): already absent
    return dict(name='railing', kind='card', Z=Z, rect=(X0, X1, Y0, Y1), img=rgba(out, a), fog=0.0)


def build():
    planes = [sky(),
              treeline(46.0, -40, 50, 13, 1, (0.16, 0.18, 0.27), 0.45, None, 1.0),
              treeline(16.0, -14, 22, 8.5, 2, (0.08, 0.09, 0.13), 0.22, None, 1.0),
              room_back(), room_floor(), room_lamp(), door_leaf(), curtain(),
              yard(), clapboard_wall(), porch_floor(), porch_front(), steps(), railing()]
    for pl in planes:
        a = pl['img']
        if pl.get('fog'):
            hz = np.array([0.42, 0.36, 0.46], np.float32)
            a[..., :3] = a[..., :3] * (1 - pl['fog']) + hz * pl['fog']
        if not pl.get('interior'):
            a[..., :3] *= 0.92
    return planes


if __name__ == '__main__':
    ps = build()
    for p in ps:
        print(p['name'], p['kind'], p['img'].shape, p.get('Z'))
