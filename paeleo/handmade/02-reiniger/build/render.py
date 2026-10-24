"""Exposure: composite every frame of the shadow theatre and pipe it to ffmpeg.

Light model (a lamp behind a paper screen): L = lamp light field (dusk wash, doorway interior,
window, door glow, porch wedge, lantern, moon, stars); each plane multiplies by its transmission
(1 - density * mask).  Black card stops 97.5 %.  Figures are drawn at 2x and reduced (cut edges).
The dog's rendered mask, and two measurement masks (muzzle tip, cranium), are measured per frame
for trace.json -- the trace is what the render did, not what the rig intended.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Pool
from theatre import *
import stage

FONTS = os.path.join(REPO, 'tools', 'paeleo', 'fonts')
BLACK = np.array([14, 11, 13], np.float32) / 255.0
TITLE_N = 72; END_N = 72

CUES = [(1.0, 2.5, 'Come here.', 'call'), (3.4, 4.75, 'Come here!', 'call'),
        (7.4, 9.55, "It's all right.", 'soft'), (10.4, 11.85, "It's all right.", 'soft'),
        (26.4, 27.95, 'Come in.', 'soft')]

PAL_A = np.array([[44, 56, 104], [132, 106, 150], [240, 172, 114], [200, 140, 100]], np.float32) / 255
PAL_B = np.array([[13, 18, 46], [50, 54, 98], [150, 96, 96], [120, 80, 82]], np.float32) / 255
STOPS = np.array([0, 300, 520, 720], np.float32)

G = {}
def init():
    G['st'] = stage.load()
    G['rig'] = json.load(open(os.path.join(OUT, 'rig.json')))
    G['font_call'] = ImageFont.truetype(os.path.join(FONTS, 'f34.woff2'), 40)
    G['font_soft'] = ImageFont.truetype(os.path.join(FONTS, 'f27.woff2'), 36)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d1 = np.hypot(xx - 1010, yy - 200); d2 = np.hypot(xx - 1021, yy - 192)
    G['moon'] = (np.clip(24.5 - d1, 0, 1) * np.clip(d2 - 20.5, 0, 1)).astype(np.float32)
    G['moonglow'] = np.exp(-(d1 / 70.0) ** 2).astype(np.float32)

def sky(t):
    s = smooth(t / 32.0)
    pal = PAL_A * (1 - s) + PAL_B * s
    rows = np.arange(H, dtype=np.float32)
    col = np.stack([np.interp(rows, STOPS, pal[:, c]) for c in range(3)], 1)
    return col[:, None, :]

def draw_polys(d, polys, fill):
    for p in polys:
        d.polygon([(X(x) * SS, Y(y) * SS) for x, y in p], fill=fill)

def mask_of(polys, holes=()):
    im = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(im)
    draw_polys(d, polys, 255); draw_polys(d, holes, 0)
    return np.asarray(im.reduce(SS), np.float32) / 255.0

def leaf_mask(f):
    """Door leaf: the arch-shaped card, hinged on the right jamb, foreshortened to width f."""
    ao = stage.arch_outline()
    hx = stage.ARCH_R
    pts = ao.copy(); pts[:, 0] = hx + (pts[:, 0] - hx) * f
    im = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(im)
    d.polygon([(X(x) * SS, Y(y) * SS) for x, y in pts], fill=255)
    lines = Image.new('L', im.size, 0); dl = ImageDraw.Draw(lines)
    def fx(x): return hx + (x - hx) * f
    # window with lace curtain holes, cut through the leaf
    wx0, wx1, wy0, wy1 = -0.30, 0.30, 1.30, 2.05
    d.polygon([(X(fx(wx0)) * SS, Y(wy1) * SS), (X(fx(wx1)) * SS, Y(wy1) * SS),
               (X(fx(wx1)) * SS, Y(wy0) * SS), (X(fx(wx0)) * SS, Y(wy0) * SS)], fill=60)
    for yy in np.arange(wy0 + 0.04, wy1 - 0.02, 0.07):
        for xx in np.arange(wx0 + 0.04, wx1 - 0.02, 0.07):
            cx, cy = X(fx(xx)), Y(yy); r = 2.6 * max(0.3, f)
            d.ellipse([(cx - r) * SS, (cy - 2.6) * SS, (cx + r) * SS, (cy + 2.6) * SS], fill=0)
    for a, b in [((wx0, wy0), (wx1, wy0)), ((wx0, wy1), (wx1, wy1)), ((0.0, wy0), (0.0, wy1)),
                 ((wx0, wy0), (wx0, wy1)), ((wx1, wy0), (wx1, wy1)),
                 ((-0.30, 0.25), (0.30, 0.25)), ((-0.30, 1.05), (0.30, 1.05)), ((-0.30, 0.25), (-0.30, 1.05)),
                 ((0.30, 0.25), (0.30, 1.05)), ((ARCH_L_, 0.0), (ARCH_L_, 1.9))]:
        dl.line([(X(fx(a[0])) * SS, Y(a[1]) * SS), (X(fx(b[0])) * SS, Y(b[1]) * SS)], fill=255, width=3 * SS)
    kx = X(fx(-0.36)); ky = Y(0.98)
    dl.ellipse([(kx - 4) * SS, (ky - 4) * SS, (kx + 4) * SS, (ky + 4) * SS], fill=255)
    return np.asarray(im.reduce(SS), np.float32) / 255.0, np.asarray(lines.reduce(SS), np.float32) / 255.0
ARCH_L_ = -0.455

def compose(t, leaf, black_dyn, flick=1.0, open_amt=0.0, star_amt=0.0, sky_t=None, bare=False):
    st = G['st']
    Lf = sky(t if sky_t is None else sky_t) * st['hot'][..., None]
    if bare:
        Lf = Lf + np.array([1.0, 0.72, 0.40], np.float32) * (st['radial'] * 0.0)[..., None]
        out = Lf * st['paper'][..., None]
        b = black_dyn[..., None]
        return out * (1 - b) + BLACK * b
    interior = (np.array([1.0, 0.70, 0.40], np.float32)[None, None] * 0.62
                + np.array([1.0, 0.88, 0.62], np.float32)[None, None] * 0.55 * st['interior'][..., None])
    door = st['door'][..., None]
    Lf = Lf * (1 - door) + interior * door * flick
    win = st['window'][..., None]
    Lf = Lf * (1 - win) + np.array([0.95, 0.66, 0.36], np.float32) * 0.78 * win * flick
    gl = 0.16 + 0.84 * open_amt
    Lf = Lf + np.array([1.0, 0.72, 0.40], np.float32) * ((st['radial'] * 0.40 + st['wedge'] * 0.34) * gl)[..., None]
    Lf = Lf + np.array([1.0, 0.70, 0.35], np.float32) * (st['lantern'] * 0.55 * flick)[..., None]
    Lf = Lf + np.array([0.95, 0.92, 0.82], np.float32) * (G['moon'] * 0.85 + G['moonglow'] * 0.10)[..., None]
    Lf = Lf + (st['stars'] * star_amt)[..., None] * np.array([0.9, 0.9, 1.0], np.float32)
    T = st['paper'] * (1 - 0.22 * st['far']) * (1 - 0.42 * st['mid']) * (1 - 0.66 * st['facade'])
    T = T * (1 - 0.6 * st['curtain']) * (1 - 0.80 * leaf)
    blk = np.maximum(st['black'], black_dyn)
    out = Lf * T[..., None]
    out = out * (1 - blk[..., None]) + BLACK * blk[..., None]
    return out

def text_layer(img, t):
    for (a, b, s, kind) in CUES:
        if a - 0.1 <= t <= b + 0.2:
            al = min(1, (t - a + 0.1) / 0.2, (b + 0.2 - t) / 0.3)
            if al <= 0: continue
            font = G['font_call'] if kind == 'call' else G['font_soft']
            lay = Image.new('L', (W, H), 0); d = ImageDraw.Draw(lay)
            d.text((440, 662), s, font=font, fill=int(255 * al), anchor='mm')
            col = (250, 206, 140) if kind == 'call' else (236, 214, 176)
            img.paste(Image.new('RGB', (W, H), col), (0, 0), lay)
    return img

def render_scene(i):
    if 'st' not in G: init()
    R = G['rig'][i]; t = R['t']
    dog = DogRig()
    feet = {k: tuple(v) for k, v in R['feet'].items()}
    dp = dog.pose(i, R['dog'], feet)
    per = PersonRig(); per.prevx = R['person']['x']
    per.feet_phase = R['person']['x'] * 13.0 * -1
    pp = per.pose(i, R['person'])
    dmask = mask_of(dp['fills'], dp['holes'])
    pmask = mask_of(pp['fills'], pp['holes'])
    lf, ll = leaf_mask(R['leaf'])
    blk = np.maximum(np.maximum(dmask, pmask), ll)
    open_amt = (0.45 - R['leaf']) / 0.35
    flick = 1.0 + 0.012 * math.sin(t * 7.3) + 0.008 * math.sin(t * 17.1 + 1.0)
    star_amt = smooth((t - 9) / 14) * 0.8
    out = compose(t, lf, blk, flick, open_amt, star_amt)
    img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    img = text_layer(img, t)
    # ---- measurement from the render
    m = dmask > 0.5
    ys, xs = np.nonzero(m)
    meas = dict(i=i, t=t)
    if len(xs):
        meas.update(x_screen=round(float(xs.mean()), 2), y_screen=round(float(ys.mean()), 2),
                    bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], area=int(m.sum()))
    mz = mask_of(dp['muzzle']) if dp['muzzle'] else None
    sk = mask_of(dp['skull']) if dp['skull'] else None
    facing = 0; gaze = 'hidden'
    if mz is not None and mz.sum() > 3 and sk is not None:
        mzx = (mz * np.arange(W)[None]).sum() / mz.sum(); skx = (sk * np.arange(W)[None]).sum() / sk.sum()
        facing = 1 if mzx < skx else -1
        gaze = 'toward door' if facing == 1 else 'away from door'
    elif sk is not None and sk.sum() > 3:
        gaze = 'end-on (looking into depth)'
    meas['facing'] = facing; meas['gaze'] = gaze
    meas['row'] = dict(dp['row'], **{'p_' + k: v for k, v in pp['row'].items() if k != 'i'}, leaf=round(R['leaf'], 3))
    meas['limits'] = dog.limit_log
    return np.asarray(img).tobytes(), meas

# ---------------------------------------------------------------- cards
def cartouche(d, cx, cy, w, h):
    d.rounded_rectangle([(cx - w / 2) * SS, (cy - h / 2) * SS, (cx + w / 2) * SS, (cy + h / 2) * SS], radius=26 * SS, fill=255)
    for k in range(int(w / 18)):
        x = cx - w / 2 + 9 + k * 18
        for y in (cy - h / 2 - 4, cy + h / 2 + 4):
            d.ellipse([(x - 7) * SS, (y - 7) * SS, (x + 7) * SS, (y + 7) * SS], fill=255)
        for y in (cy - h / 2 + 10, cy + h / 2 - 10):
            d.ellipse([(x - 2.5) * SS, (y - 2.5) * SS, (x + 2.5) * SS, (y + 2.5) * SS], fill=0)

def card_text(lines):
    lay = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(lay)
    for (txt, path, size, cy) in lines:
        f = ImageFont.truetype(os.path.join(FONTS, path), size * SS)
        d.text((W * SS / 2, cy * SS), txt, font=f, fill=255, anchor='mm')
    return np.asarray(lay.reduce(SS), np.float32) / 255

def render_title(k):
    if 'st' not in G: init()
    st = G['st']
    im = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(im)
    cartouche(d, 640, 250, 900, 210)
    car = np.asarray(im.reduce(SS), np.float32) / 255
    txt = card_text([('PAE-02 · SCION 02 · LOTTE REINIGER', 'f34.woff2', 46, 236),
                     ('the threshold — a shadow theatre', 'f27.woff2', 30, 316)])
    # the puppet waits under the title, cut from the same pieces as the film
    R = G['rig'][300]; dog = DogRig()
    dpar = dict(R['dog']); dpar['x'] = 1.75
    feet = {kk: (v[0] - R['dog']['x'] + 1.75, v[1], v[2]) for kk, v in R['feet'].items()}
    dp = dog.pose(0, dpar, feet)
    dm = mask_of(dp['fills'], dp['holes'])
    gnd = np.zeros((H, W), np.float32); gnd[int(Y(0.0)):int(Y(0.0)) + 8, 380:900] = 1
    blk = np.maximum(np.maximum(np.maximum(car, dm), gnd), border_only())
    out = compose(1.0, np.zeros((H, W), np.float32), blk, bare=True)
    out = out * (1 - txt[..., None]) + np.array([0.99, 0.84, 0.60], np.float32) * txt[..., None]
    fade = min(1, k / 12, (TITLE_N - 1 - k) / 10 + 0.15)
    out = out * fade
    return (np.clip(out, 0, 1) * 255).astype(np.uint8).tobytes()

_border = {}
def border_only():
    if 'b' not in _border:
        st = G['st']; b = st['black'].copy()
        inner = np.zeros_like(b); inner[22:H - 22, 22:W - 22] = 1
        b[inner > 0] = 0
        _border['b'] = b
    return _border['b']

def render_end(k):
    if 'st' not in G: init()
    st = G['st']
    R = G['rig'][330]; dog = DogRig()
    dpar = dict(R['dog']); dpar['x'] = 0.0; dpar['dirW'] = -1
    feet = {kk: (v[0] - R['dog']['x'], v[1], v[2]) for kk, v in R['feet'].items()}
    dp = dog.pose(0, dpar, feet)
    ex = min(1, k / 30.0)
    polys = []
    pins = []
    cx = 0.0; cy = 0.35
    for p in dp['fills']:
        c = p.mean(0); off = (c - [cx, cy]) * 0.55 * smooth(ex)
        polys.append(p + off)
        j = np.argmin(np.hypot(p[:, 0] - cx, p[:, 1] - cy)); pins.append(p[j] + off)
    # place the exploded puppet in the upper half of the card
    def mv(p): q = np.asarray(p).copy(); q[:, 0] = q[:, 0] * 1.25 + 1.65; q[:, 1] = q[:, 1] * 1.25 + 1.75; return q
    dm = mask_of([mv(p) for p in polys], [mv(p) for p in dp['holes']])
    pin_mask = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(pin_mask)
    for p in pins:
        q = mv(p[None])[0]; px, py = X(q[0]), Y(q[1])
        d.ellipse([(px - 2.2) * SS, (py - 2.2) * SS, (px + 2.2) * SS, (py + 2.2) * SS], fill=255)
    pm = np.asarray(pin_mask.reduce(SS), np.float32) / 255
    im = Image.new('L', (W * SS, H * SS), 0); dd = ImageDraw.Draw(im)
    cartouche(dd, 640, 520, 1140, 236)
    car = np.asarray(im.reduce(SS), np.float32) / 255
    txt = card_text([('made of: black card and tissue paper on a lamp-lit screen — a dog of 23 cut pieces on 22 pins,', 'f34.woff2', 21, 446),
                     ('a person of 16-20 pieces; replacement heads, hands and end-on bodies; paws planted by a contact solver', 'f34.woff2', 21, 478),
                     ('proportions measured from Amateur Film New Jersey C (Home Movies, Internet Archive, public domain);', 'f27.woff2', 19, 516),
                     ('the door swing re-timed from Straight Talk (NTIS, 1992, public domain). Music and crickets synthesized.', 'f27.woff2', 19, 545),
                     ('timing: the PAELEO threshold score, frame for frame', 'f27.woff2', 19, 584)])
    blk = np.maximum(np.maximum(car, dm), border_only())
    out = compose(24.0, np.zeros((H, W), np.float32), blk, bare=True)
    out = out * (1 - txt[..., None]) + np.array([0.97, 0.82, 0.60], np.float32) * txt[..., None]
    out = out * (1 - pm[..., None]) + np.array([1.0, 0.85, 0.6], np.float32) * pm[..., None]
    fade = min(1, (END_N - 1 - k) / 14, k / 6 + 0.3)
    out = out * fade
    return (np.clip(out, 0, 1) * 255).astype(np.uint8).tobytes()

def job(spec):
    kind, k = spec
    if kind == 'title': return render_title(k), None
    if kind == 'end': return render_end(k), None
    return render_scene(k)

def main(out_mp4, only=None):
    rig = json.load(open(os.path.join(OUT, 'rig.json')))
    n = len(rig)
    specs = [('title', k) for k in range(TITLE_N)] + [('scene', i) for i in range(n)] + [('end', k) for k in range(END_N)]
    if only is not None:
        specs = [('scene', i) for i in only]
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                           '-pix_fmt', 'yuv420p', out_mp4], stdin=subprocess.PIPE)
    meas = []
    with Pool(4, initializer=init) as pool:
        for k, (buf, m) in enumerate(pool.imap(job, specs, chunksize=4)):
            ff.stdin.write(buf)
            if m is not None: meas.append(m)
            if k % 100 == 0: print('frame', k, file=sys.stderr, flush=True)
    ff.stdin.close(); ff.wait()
    json.dump(meas, open(os.path.join(OUT, 'measure.json'), 'w'))
    return meas

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, 'picture.mp4')
    only = None
    if len(sys.argv) > 2: only = [int(v) for v in sys.argv[2].split(',')]
    main(out, only)
