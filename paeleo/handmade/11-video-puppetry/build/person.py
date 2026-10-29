"""SCION 11 · the person: a jointed paper puppet with one real hand.

Body, head, legs and upper arm are cut card moved by rigid tracked transforms, exactly
Barnes's paper cut-outs.  The forearm and hand are not drawn: they are cut from public-domain
footage (The Door to Heaven, Internet Archive, via the kit's found-frames, hand-sam frame 0),
masked, mirrored to reach right, and placed by a two-point (elbow, wrist) similarity transform.
The puppeteer's hands never appear; the only hand in the picture is the character's.
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
HAND_DIR = '/home/user/hartswf0/secondhand-motion/shots/hand-sam'
W, H = 1280, 720
SS = 2


def _hand():
    m = json.load(open(os.path.join(HAND_DIR, 'masks.json')))['0']
    im = Image.open(os.path.join(HAND_DIR, 'frames/f000.jpg')).convert('L')
    Wd, Hd = im.size
    g = np.asarray(im, np.float32) / 255.
    mk = Image.new('L', (Wd * 4, Hd * 4), 0)
    d = ImageDraw.Draw(mk)
    for p in m:
        d.polygon([(x * 4, y * 4) for x, y in p], fill=255)
    # the forearm continues past the SAM hand mask to the frame edge: cut it by hand
    d.polygon([(x * 4, y * 4) for x, y in [(276, 66), (330, 60), (383, 56), (383, 97), (330, 98), (278, 101)]], fill=255)
    a = np.asarray(mk.resize((Wd, Hd), Image.LANCZOS), np.float32) / 255.
    a = ndimage.gaussian_filter(a, .6)
    lo, hi = np.percentile(g[a > .5], 3), np.percentile(g[a > .5], 98)
    g = np.clip((g - lo) / (hi - lo) * .75 + .12, 0, 1)
    # mirror: the found hand reaches left, ours reaches right toward the dog
    g, a = g[:, ::-1].copy(), a[:, ::-1].copy()
    elbow = np.array([Wd - 1 - 383., 77.])
    wrist = np.array([Wd - 1 - 281., 83.])
    return g, a, elbow, wrist


HAND = _hand()


def lerp(a, b, t):
    return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * t


def limb(d, p0, p1, w0, w1, fill):
    v = np.asarray(p1, float) - np.asarray(p0, float)
    n = np.array([-v[1], v[0]]) / (np.hypot(*v) + 1e-6)
    q = [p0 + n * w0 / 2, p1 + n * w1 / 2, p1 - n * w1 / 2, p0 - n * w0 / 2]
    d.polygon([(x * SS, y * SS) for x, y in q], fill=fill)
    for c, r in [(p0, w0 / 2), (p1, w1 / 2)]:
        d.ellipse(((c[0] - r) * SS, (c[1] - r) * SS, (c[0] + r) * SS, (c[1] + r) * SS), fill=fill)


def geometry(p):
    cx, sit, reach, low, lean, step = p['cx'], p['sit'], p['reach'], p['low'], p['lean'], p['step']
    hip = lerp((cx, 344), (cx, 492), sit)
    sh = lerp((cx + 6 + 10 * lean, 226 + 3 * lean), (cx + 2, 382), sit)
    head = lerp((cx + 12 + 16 * lean, 196 + 5 * lean), (cx + 8 + 6 * lean, 350), sit)
    # legs
    sw = np.sin(np.pi * 2 * step) * 22 if 0 < step < 1 else 0
    kn1 = lerp((cx + 4 + sw * .5, 424), (cx + 52, 452), sit)
    ft1 = lerp((cx + 8 + sw, 504), (cx + 96, 500), sit)
    kn2 = lerp((cx - 2 - sw * .5, 424), (cx + 44, 458), sit)
    ft2 = lerp((cx - 2 - sw, 504), (cx + 84, 503), sit)
    # arm: rest -> reach (toward the dog) -> low (offered near the floor)
    el = lerp(sh + (2, 56), sh + (56, 6), reach)
    wr = lerp(sh + (5, 106), sh + (108, 10), reach)
    el = lerp(el, sh + (40, 46), low)
    wr = lerp(wr, sh + (82, 80), low)
    return dict(hip=hip, sh=sh, head=head, kn1=kn1, ft1=ft1, kn2=kn2, ft2=ft2, el=el, wr=wr)


def layer(p):
    """RGBA float layer (H,W,4) of the person for one frame"""
    G = geometry(p)
    col = {'coat': (98, 86, 108), 'dark': (52, 48, 60), 'skin': (120, 100, 96), 'hair': (40, 34, 38)}
    im = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # far leg, near leg (trousers), shoes
    limb(d, G['hip'] + (-4, 0), G['kn2'], 26, 20, col['dark'] + (255,))
    limb(d, G['kn2'], G['ft2'], 20, 16, col['dark'] + (255,))
    limb(d, G['hip'] + (4, 0), G['kn1'], 28, 21, col['dark'] + (255,))
    limb(d, G['kn1'], G['ft1'], 21, 17, col['dark'] + (255,))
    for f in [G['ft2'], G['ft1']]:
        d.polygon([((f[0] - 8) * SS, (f[1] - 7) * SS), ((f[0] + 18) * SS, (f[1] - 4) * SS), ((f[0] + 18) * SS, (f[1] + 1) * SS),
                   ((f[0] - 8) * SS, (f[1] + 1) * SS)], fill=(30, 26, 30, 255))
    # coat: a cut trapezoid from shoulder line to below the hip
    sh, hp = G['sh'], G['hip']
    v = hp - sh
    n = np.array([-v[1], v[0]]) / np.hypot(*v)
    coat = [sh + n * 22, hp + n * 27 + v * .12, hp - n * 25 + v * .12, sh - n * 20]
    d.polygon([(x * SS, y * SS) for x, y in coat], fill=col['coat'] + (255,))
    d.line([((sh + n * 2)[0] * SS, (sh + n * 2)[1] * SS), ((hp + n * 2 + v * .1)[0] * SS, (hp + n * 2 + v * .1)[1] * SS)],
           fill=(70, 60, 78, 255), width=3)  # coat seam
    # neck, head (profile to the right), hair
    hc = G['head']
    limb(d, sh + (2, -6), hc + (-2, 12), 14, 12, col['skin'] + (255,))
    d.ellipse(((hc[0] - 19) * SS, (hc[1] - 22) * SS, (hc[0] + 19) * SS, (hc[1] + 22) * SS), fill=col['skin'] + (255,))
    d.polygon([((hc[0] + 16) * SS, (hc[1] - 4) * SS), ((hc[0] + 24) * SS, (hc[1] + 5) * SS), ((hc[0] + 15) * SS, (hc[1] + 8) * SS)],
              fill=col['skin'] + (255,))  # nose
    d.chord(((hc[0] - 21) * SS, (hc[1] - 25) * SS, (hc[0] + 19) * SS, (hc[1] + 14) * SS), 160, 350, fill=col['hair'] + (255,))
    d.ellipse(((hc[0] - 24) * SS, (hc[1] - 12) * SS, (hc[0] - 8) * SS, (hc[1] + 14) * SS), fill=col['hair'] + (255,))
    # upper arm (card)
    limb(d, sh, G['el'], 20, 16, (88, 76, 98, 255))
    small = im.resize((W, H), Image.LANCZOS)
    L = np.asarray(small, np.float32) / 255.
    rgb, a = L[..., :3].copy(), L[..., 3].copy()
    # the real forearm and hand: similarity transform elbow->elbow, wrist->wrist
    g, ha, e0, w0 = HAND
    e1, w1 = G['el'], G['wr']
    v0, v1 = w0 - e0, w1 - e1
    s = np.hypot(*v1) / np.hypot(*v0)
    ang = np.arctan2(v1[1], v1[0]) - np.arctan2(v0[1], v0[0])
    x0, x1 = int(min(e1[0], w1[0]) - 90), int(max(e1[0], w1[0]) + 90)
    y0, y1 = int(min(e1[1], w1[1]) - 90), int(max(e1[1], w1[1]) + 90)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, W), min(y1, H)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx - e1[0], yy - e1[1]
    ca, sa = np.cos(-ang), np.sin(-ang)
    ux = (dx * ca - dy * sa) / s + e0[0]
    uy = (dx * sa + dy * ca) / s + e0[1]
    hg = ndimage.map_coordinates(g, [uy, ux], order=1, cval=0)
    hal = ndimage.map_coordinates(ha, [uy, ux], order=1, cval=0)
    tint = np.array([0.66, 0.58, 0.58])
    sub = rgb[y0:y1, x0:x1]
    sub[:] = sub * (1 - hal[..., None]) + (hg[..., None] * tint) * hal[..., None]
    a[y0:y1, x0:x1] = np.maximum(a[y0:y1, x0:x1], hal)
    return rgb, a, G
