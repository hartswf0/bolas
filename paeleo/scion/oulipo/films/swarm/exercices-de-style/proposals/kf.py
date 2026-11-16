"""Keyframe builder for the three proposed directions of exercices-de-style.
Deterministic. Reads cutouts made by work/mattes.py + work/man.py, foraged frames
extracted to work/*.png (ffmpeg, Moving Image Archive cache), and the reference.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/exercices-de-style/proposals/'
WK = HERE + 'work/'
REF = '/home/user/bolas/paeleo/scion/oulipo/assets/references/styleBook.webp'
W, H = 1280, 720
F = '/usr/share/fonts/truetype/'
SERIF_I = F + 'liberation/LiberationSerif-Italic.ttf'
SERIF = F + 'liberation/LiberationSerif-Regular.ttf'
SERIF_B = F + 'dejavu/DejaVuSerif-Bold.ttf'
FSERIF_BI = F + 'freefont/FreeSerifBoldItalic.ttf'
SANS = F + 'liberation/LiberationSans-Regular.ttf'
SANS_B = F + 'dejavu/DejaVuSans-Bold.ttf'
MONO = F + 'freefont/FreeMono.ttf'
MONO_B = F + 'freefont/FreeMonoBold.ttf'
CREAM_T, CREAM_B = (250, 238, 196), (243, 226, 168)
GHOST = (240, 224, 160)
RED = (220, 38, 34)
INK = (22, 20, 18)
GREY = (146, 146, 142)

def font(p, s): return ImageFont.truetype(p, s)

def page(seed):
    """Cover-like page: warm cream gradient with fine paper tooth, grey band at foot."""
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array(CREAM_T, float); b = np.array(CREAM_B, float)
    img = a * (1 - y) + b * y + np.zeros((H, W, 3))
    tooth = rng.normal(0, 3.2, (H, W, 1))
    img = np.clip(img + tooth, 0, 255).astype(np.uint8)
    im = Image.fromarray(img).convert('RGBA')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 618, W, H], fill=GREY + (255,))
    return im

def ghost(im, text, xy, size, fnt=SERIF):
    d = ImageDraw.Draw(im)
    d.text(xy, text, font=font(fnt, size), fill=GHOST + (255,))

def mixed(im, parts, x, y):
    """Mixed-face title like the cover's 'de Style': list of (text, fontpath, size, colour, dy)."""
    d = ImageDraw.Draw(im)
    for t, fp, s, c, dy in parts:
        f = font(fp, s)
        d.text((x, y + dy), t, font=f, fill=c)
        x += d.textlength(t, font=f)
    return x

def band(im, left, right):
    d = ImageDraw.Draw(im)
    d.text((40, 642), left, font=font(SANS, 44), fill=(255, 255, 255))
    f = font(SANS_B, 15)
    d.text((W - 40 - d.textlength(right, font=f), 688), right, font=f, fill=(255, 255, 255))

def strip(im, cells, active, y=560, h=50):
    """The cover's row of vignettes: six beat cells, active beat ringed in red."""
    n = len(cells); gap = 4; cw = 74
    x0 = W - 40 - n * cw - (n - 1) * gap
    d = ImageDraw.Draw(im)
    for i, c in enumerate(cells):
        x = x0 + i * (cw + gap)
        if isinstance(c, Image.Image):
            t = fit(c, cw, h); im.paste(t, (x, y))
        else:
            d.rectangle([x, y, x + cw, y + h], fill=c)
        lab = str(i + 1) if not isinstance(c, tuple) else ''
    for i in range(n):
        x = x0 + i * (cw + gap)
        if i == active:
            d.rectangle([x - 3, y - 3, x + cw + 3, y + h + 3], outline=RED, width=3)
    return x0

def fit(img, w, h):
    img = img.convert('RGB'); r = max(w / img.width, h / img.height)
    t = img.resize((max(w, int(img.width * r + .5)), max(h, int(img.height * r + .5))), Image.LANCZOS)
    l = (t.width - w) // 2; u = (t.height - h) // 2
    return t.crop((l, u, l + w, u + h))

def shadow(layer, off=(8, 10), blur=7, alpha=90):
    a = layer.getchannel('A').filter(ImageFilter.GaussianBlur(blur))
    a = a.point(lambda v: v * alpha // 255)
    s = Image.new('RGBA', layer.size, (60, 40, 10, 0)); s.putalpha(a)
    return s, off

def place(im, layer, xy, sh=True, **kw):
    if sh:
        s, off = shadow(layer, **kw)
        im.alpha_composite(s, (xy[0] + off[0], xy[1] + off[1]))
    im.alpha_composite(layer, xy)

def paper_edge(poly, rng, amp=1.6, step=6):
    """Torn/scissored edge: subdivide and jitter a polygon (cut paper, by hand)."""
    out = []
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L / step))
        for k in range(n):
            t = k / n
            out.append((x0 + (x1 - x0) * t + rng.normal(0, amp), y0 + (y1 - y0) * t + rng.normal(0, amp)))
    return out

def cutpaper(size, polys, seed):
    """Handmade cut-paper layer: each poly = (points, rgb). Adds a fibrous tooth."""
    rng = np.random.default_rng(seed)
    L = Image.new('RGBA', size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for pts, col in polys:
        d.polygon(paper_edge(pts, rng), fill=col + (255,))
    arr = np.array(L).astype(float)
    arr[..., :3] += rng.normal(0, 5, arr[..., :3].shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def bw_print(img, warm=(1.0, 0.95, 0.82), lift=18):
    """Warm the b/w archive print toward the cover's cream (tone only, no fake grain)."""
    g = np.array(img.convert('L')).astype(float)
    g = lift + g * (255 - lift) / 255
    rgb = np.stack([g * warm[0], g * warm[1], g * warm[2]], -1)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))

# -------------------------------------------------------------- KF1
def kf1():
    """Narré par la clé — articulated photographic cutout, beat 5 (key left on bench)."""
    im = page(1)
    ghost(im, 'Je', (-30, -150), 640, SERIF)
    ghost(im, 'clé', (700, 170), 330, SERIF_I)
    mixed(im, [('N', FSERIF_BI, 74, RED, 0), ('arré', SERIF_I, 62, RED, 10),
               (' par ', SANS, 34, INK, 34), ('la ', SERIF, 52, INK, 16), ('c', SANS_B, 64, INK, 6),
               ('l', SERIF_B, 70, RED, 0), ('é', FSERIF_BI, 66, INK, 4)], 44, 34)
    # the visitor: GrabCut cutout of an Agence Rol portrait, split into puppet layers
    man = Image.open(WK + 'man_cut.png')
    s = 390 / man.height; man = man.resize((int(man.width * s), 390), Image.LANCZOS)
    man = Image.fromarray(np.array(man)).convert('RGBA')
    tone = bw_print(man.convert('RGB'), warm=(1.0, .96, .86), lift=10); tone.putalpha(man.getchannel('A'))
    # puppet split at the collar line: head+hat layer is tilted 3 deg about the neck pin
    neck = int(0.30 * tone.height)
    head = tone.crop((0, 0, tone.width, neck + 12)); body = tone.crop((0, neck, tone.width, tone.height))
    mx, my = 120, 228
    sh_, off = shadow(tone, off=(10, 8), blur=6, alpha=110); im.alpha_composite(sh_, (mx + 10, my + 8))
    im.alpha_composite(body, (mx, my + neck))
    head = head.rotate(2.0, resample=Image.BICUBIC, center=(int(.36 * tone.width), neck), expand=False)
    im.alpha_composite(head, (mx, my))
    # handmade cut-paper bench (green and cream like the cover's bus), low key-eye view
    B = cutpaper((900, 330), [
        ([(40, 120), (880, 70), (890, 108), (36, 168)], (40, 92, 58)),     # backrest slat
        ([(30, 182), (885, 128), (893, 160), (26, 226)], (46, 102, 64)),   # backrest slat 2
        ([(0, 250), (900, 190), (900, 232), (0, 300)], (34, 82, 52)),      # seat front edge
        ([(70, 300), (100, 296), (104, 330), (72, 330)], (24, 50, 34)),    # leg
        ([(800, 222), (832, 218), (834, 330), (802, 330)], (24, 50, 34)),
        ([(50, 116), (870, 66), (872, 74), (50, 124)], (226, 214, 170)),   # cream lining
        ([(0, 246), (900, 186), (900, 192), (0, 252)], (226, 214, 170)),
    ], seed=7)
    place(im, B, (390, 300), off=(6, 12), blur=8, alpha=120)
    # the key (Index of American Design watercolour, CC0), cut on its paper, lying on the seat
    key = Image.open(WK + 'key_cut.png')
    key = key.rotate(-79, resample=Image.BICUBIC, expand=True)
    s = 470 / key.width; key = key.resize((470, int(key.height * s)), Image.LANCZOS)
    place(im, key, (470, 360), off=(5, 9), blur=5, alpha=150)
    # the key's own voice (caption is the voice; no TTS)
    d = ImageDraw.Draw(im)
    lines = [('On m’a posée sur le banc.', INK), ('Sa main était tiède,', INK), ('puis il n’y eut que son manteau.', INK),
             ('La porte de service n’a pas bougé.', RED)]
    y = 170
    for t, c in lines:
        d.text((640, y), t, font=font(SERIF_I, 31), fill=c); y += 38
    d.text((640, 140), '— la clé, beat 5 / 6', font=font(SANS, 15), fill=(120, 100, 60))
    cells = [fit(Image.open(WK + 'man_cut.png').convert('RGB'), 74, 50), (214, 196, 140), (196, 60, 40),
             (170, 140, 70), fit(Image.open(WK + 'key_cut.png').convert('RGB').rotate(-90, expand=True), 74, 50), (40, 92, 58)]
    strip(im, cells, 4)
    band(im, 'Narré par la clé', 'EXERCICE 4 · OBJET NARRATEUR · 0:44')
    return im.convert('RGB')

# -------------------------------------------------------------- KF2
def puppet(pose, scale=1.0):
    """Handmade articulated silhouette (Reiniger): limbs are separate polygons on pins.
    pose = dict of joint angles in degrees. Returns L mask."""
    S = Image.new('L', (520, 760), 0); d = ImageDraw.Draw(S)
    def seg(origin, ang, pts):
        a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
        P = [(origin[0] + x * ca - y * sa, origin[1] + x * sa + y * ca) for x, y in pts]
        d.polygon(P, fill=255); return P
    def end(origin, ang, L):
        a = math.radians(ang); return (origin[0] - L * math.sin(a), origin[1] + L * math.cos(a))
    hip = (260, 420); sh = (262, 210)
    # legs (thigh+shin, two pins each)
    for k, (t, c) in enumerate([(pose['lt'], pose['lk']), (pose['rt'], pose['rk'])]):
        seg(hip, t, [(-24, 0), (24, 0), (20, 150), (-18, 150)])
        kn = end(hip, t, 150)
        seg(kn, t + c, [(-18, 0), (18, 0), (14, 140), (-12, 140)])
        an = end(kn, t + c, 140)
        seg(an, t + c, [(-12, -6), (44, -4), (46, 14), (-14, 14)])   # shoe, toe forward
    # coat: torso with skirt flare
    d.polygon([(214, 196), (310, 196), (322, 330), (346, 470), (178, 470), (200, 330)], fill=255)
    # head, hat (bowler), neck
    d.polygon([(250, 170), (276, 170), (278, 200), (248, 200)], fill=255)
    d.ellipse([228, 104, 298, 182], fill=255)
    d.polygon([(286, 150), (306, 156), (288, 164)], fill=255)          # nose
    d.ellipse([224, 64, 304, 124], fill=255); d.rectangle([224, 96, 304, 110], fill=255)
    d.ellipse([204, 102, 326, 120], fill=255)                          # brim
    # arms: upper + forearm + hand holding envelope (rear arm, then front arm)
    for nm in ['ra', 'la']:
        u, f = pose[nm]
        seg(sh, u, [(-16, 0), (16, 0), (13, 110), (-12, 110)])
        el = end(sh, u, 110)
        seg(el, u + f, [(-12, 0), (12, 0), (10, 100), (-9, 100)])
        wr = end(el, u + f, 100)
        d.ellipse([wr[0] - 13, wr[1] - 13, wr[0] + 13, wr[1] + 13], fill=255)
        if nm == 'la':   # the sealed envelope, held up into the light
            seg(wr, u + f + 90, [(-6, -34), (80, -34), (80, 22), (-6, 22)])
    if scale != 1.0:
        S = S.resize((int(S.width * scale), int(S.height * scale)), Image.LANCZOS)
    return S

def kf2():
    """Derrière le verre dépoli — silhouette theatre, sensory inventory, beat 2 (the bell)."""
    im = page(2)
    ghost(im, 'entendu', (-20, -60), 300, SERIF_I)
    mixed(im, [('Inv', FSERIF_BI, 72, RED, 0), ('entaire', SERIF_I, 60, RED, 10),
               (' des ', SANS, 32, INK, 34), ('s', SANS_B, 62, INK, 8), ('en', SERIF, 58, INK, 12),
               ('s', SERIF_B, 66, RED, 4)], 44, 34)
    # the ticket window: a lit pane, the clerk's side; wooden frame is cut paper
    gx, gy, gw, gh = 560, 128, 580, 380
    rng = np.random.default_rng(5)
    yy, xx = np.mgrid[0:gh, 0:gw]
    glow = np.exp(-(((xx - gw * .42) / (gw * .62)) ** 2 + ((yy - gh * .38) / (gh * .75)) ** 2))
    base = np.array([255, 238, 170.]) * (0.72 + 0.28 * glow[..., None])
    pane = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    # the puppet in mid-gesture: head jerked up at the bell, envelope raised
    pose = dict(lt=14, lk=-6, rt=-12, rk=10, ra=(16, -10), la=(-150, 40))
    S = puppet(pose, scale=0.70)
    sil = Image.new('L', (gw, gh), 0); sil.paste(S, (170, 14))
    # the bell: a station bell bracket on the far wall, also only a shadow
    bd = ImageDraw.Draw(sil)
    bd.rectangle([420, 40, 510, 50], fill=200); bd.rectangle([460, 50, 468, 74], fill=200)
    bd.pieslice([436, 64, 492, 124], 180, 360, fill=200); bd.rectangle([436, 92, 492, 104], fill=200)
    bd.ellipse([456, 100, 472, 116], fill=200)
    # frosted glass: the clerk sees diffusion, not detail (blur grows with distance from glass)
    sil = sil.filter(ImageFilter.GaussianBlur(5))
    sil_np = np.array(sil).astype(float) / 255
    shade = np.array(pane).astype(float) * (1 - 0.80 * sil_np[..., None]) + np.array([40, 28, 10.]) * 0.0
    frost = rng.normal(0, 7, (gh, gw, 1)); frost = np.array(Image.fromarray(np.clip(frost * 8 + 128, 0, 255).astype(np.uint8)[..., 0]).filter(ImageFilter.GaussianBlur(1.2))).astype(float)[..., None] - 128
    pane2 = Image.fromarray(np.clip(shade + frost * .18, 0, 255).astype(np.uint8)).convert('RGBA')
    # bell shiver: three faint offset ghosts of the bell (the ring as motion)
    d2 = ImageDraw.Draw(pane2)
    for k, a in enumerate([70, 45, 25]):
        o = (k + 1) * 9
        d2.arc([436 - o, 60 - o, 492 + o, 124 + o], 200, 340, fill=(120, 90, 40, a), width=3)
    # reversed stencil lettering, read from the clerk's side
    lt = Image.new('RGBA', (gw, 90), (0, 0, 0, 0)); ImageDraw.Draw(lt).text((20, 10), 'GUICHET  3', font=font(SANS_B, 58), fill=(255, 255, 255, 120))
    pane2.alpha_composite(lt.transpose(Image.FLIP_LEFT_RIGHT), (0, gh - 100))
    frame = cutpaper((gw + 60, gh + 60), [([(0, 0), (gw + 60, 0), (gw + 60, gh + 60), (0, gh + 60)], (92, 58, 30))], seed=11)
    place(im, frame, (gx - 30, gy - 30), off=(8, 10), blur=8, alpha=110)
    im.alpha_composite(pane2, (gx, gy))
    dd = ImageDraw.Draw(im)
    dd.rectangle([gx + gw // 2 - 4, gy, gx + gw // 2 + 4, gy + gh], fill=(92, 58, 30))   # mullion
    dd.rectangle([gx - 30, gy + gh + 2, gx + gw + 30, gy + gh + 30], fill=(76, 46, 22))  # counter
    # the clerk's inventory card: typewritten, with the recorded omission
    card = cutpaper((380, 360), [([(0, 0), (380, 0), (380, 360), (0, 360)], (252, 248, 232))], seed=3)
    cd = ImageDraw.Draw(card)
    cd.text((22, 16), 'GUICHET 3 — relevé du préposé', font=font(MONO_B, 17), fill=INK)
    rows = [('18:00', 'des pas sur le carrelage', INK), ('18:02', 'une cloche — trois coups', RED),
            ('', 'l’ombre lève la tête', INK), ('18:04', 'du papier qu’on déchire', INK),
            ('18:05', 'un éclat, peut-être laiton', INK), ('18:07', 'les pas, puis plus rien', INK)]
    y = 58
    for t, s_, c in rows:
        cd.text((22, y), t, font=font(MONO, 18), fill=(110, 100, 90)); cd.text((92, y), s_, font=font(MONO, 18), fill=c); y += 34
    cd.rectangle([18, y + 6, 362, y + 64], outline=RED, width=2)
    cd.text((28, y + 12), 'NON PERÇU : ce qu’il a fait', font=font(MONO_B, 16), fill=RED)
    cd.text((28, y + 36), 'de la clé (vu de dos, flou).', font=font(MONO_B, 16), fill=RED)
    card = card.rotate(1.6, resample=Image.BICUBIC, expand=True)
    place(im, card, (52, 150), off=(7, 9), blur=6, alpha=100)
    cells = [(30, 24, 18), (255, 232, 150), (58, 40, 20), (230, 214, 170), (200, 160, 70), (240, 230, 200)]
    strip(im, cells, 1)
    band(im, 'Inventaire des sens', 'EXERCICE 2 · TÉMOIN SENSORIEL · 0:24')
    return im.convert('RGB')

# -------------------------------------------------------------- KF3
def kf3():
    """Journal à rebours — foraged archive cut newest-first, beat 6 shown first."""
    im = page(3)
    ghost(im, 'à rebours', (-40, -70), 280, SERIF_I)
    mixed(im, [('J', FSERIF_BI, 76, RED, 0), ('ournal', SERIF_I, 60, RED, 12),
               (' à ', SANS, 34, INK, 34), ('re', SERIF, 58, INK, 14), ('b', SANS_B, 66, INK, 6),
               ('ours', SERIF_B, 56, RED, 14)], 44, 34)
    main = bw_print(Image.open(WK + 'berlin-07.png'), warm=(1.0, .95, .80), lift=14)
    main = fit(main, 520, 390)
    frame = Image.new('RGBA', (536, 406), (250, 246, 230, 255))
    frame.paste(main, (8, 8))
    place(im, frame, (44, 140), off=(8, 10), blur=7, alpha=110)
    d = ImageDraw.Draw(im)
    d.text((56, 552), 'Berlin, 1927 — quai, l’aube : deux silhouettes s’éloignent', font=font(SERIF_I, 17), fill=(110, 90, 50))
    # the log, newest first; timestamps count down, causal arrows still point forward (down→up)
    log = [('18:07', 's’éloigne ; la porte reste close.', RED),
           ('18:06', 'laisse la clé sur le banc.', INK), ('18:05', 'trouve une clé de laiton.', INK),
           ('18:04', 'ouvre l’enveloppe scellée.', INK), ('18:02', 'une cloche sonne.', INK),
           ('18:00', 'arrive en gare, une enveloppe à la main.', INK)]
    x0, y = 640, 150; rows = []
    for i, (t, s_, c) in enumerate(log):
        f = font(MONO_B if i == 0 else MONO, 24 if i == 0 else 21)
        d.text((x0, y), t, font=f, fill=c if i == 0 else (120, 100, 70))
        d.text((x0 + 92, y), s_, font=font(SERIF_I if i else SERIF_B, 25 if i == 0 else 23), fill=c)
        rows.append(y); y += 62 if i == 0 else 56
    # forward causal edges (cause → effect) drawn as hand-ruled arcs in the margin
    for a, b in [(5, 4), (4, 3), (3, 2), (2, 1), (1, 0)]:
        ya, yb = rows[a] + 12, rows[b] + 12
        d.line([(x0 - 18, ya), (x0 - 32, (ya + yb) / 2), (x0 - 18, yb + 6)], fill=RED, width=2, joint='curve')
        d.polygon([(x0 - 18, yb + 2), (x0 - 10, yb + 12), (x0 - 25, yb + 12)], fill=RED)
    d.text((x0 + 92, rows[-1] + 40), 'les flèches suivent la cause, non la lecture', font=font(SANS, 15), fill=(140, 110, 60))
    # the strip runs 6 → 1, each cell a foraged shot standing for its beat
    shots = ['berlin-07', 'benchtramp-04', 'keyhand-03', 'locket-05', 'bell-11', 'berlin-01']
    cells = [bw_print(Image.open(WK + s + '.png'), lift=14) for s in shots]
    strip(im, cells, 0)
    band(im, 'Journal à rebours', 'EXERCICE 1 · CHRONOLOGIE INVERSE · 0:08')
    return im.convert('RGB')

def board(kfs, names):
    ref = Image.open(REF).convert('RGB'); rh = 2 * 360 + 24
    ref = ref.resize((int(ref.width * rh / ref.height), rh), Image.LANCZOS)
    tw, th = 640, 360
    Wb = ref.width + 2 * tw + 3 * 24; Hb = rh + 2 * 24 + 40
    B = Image.new('RGB', (Wb, Hb + 380), (34, 32, 30)); d = ImageDraw.Draw(B)
    B.paste(ref, (24, 24 + 30)); d.text((24, 22), 'REFERENCE · styleBook.webp', font=font(SANS_B, 18), fill=(240, 230, 200))
    pos = [(ref.width + 48, 54), (ref.width + 72 + tw, 54), (ref.width + 48, 54 + th + 54)]
    for (x, y), k, n in zip(pos, kfs, names):
        B.paste(k.resize((tw, th), Image.LANCZOS), (x, y)); d.text((x, y - 28), n, font=font(SANS_B, 18), fill=(240, 230, 200))
    tx, ty = ref.width + 72 + tw, 54 + th + 54
    d.text((tx, ty - 28), 'FROZEN LEDGER · the station incident (6 beats)', font=font(SANS_B, 18), fill=(240, 230, 200))
    for i, t in enumerate(['1  18:00  arrives at the empty station, sealed envelope', '2  18:02  a bell rings', '3  18:04  opens the envelope',
                           '4  18:05  finds a brass key', '5  18:06  leaves the key on the bench', '6  18:07  walks away; service door stays closed',
                           '', 'Every direction aims at the cover: cream page, ghost type,', 'red/black mixed faces, vignette strip, grey band.']):
        d.text((tx, ty + 6 + i * 30), t, font=font(MONO if i < 6 else SANS, 19), fill=(232, 222, 190))
    B = B.crop((0, 0, Wb, 54 + 2 * th + 54 + 30))
    if B.width > 2000: B = B.resize((2000, int(B.height * 2000 / B.width)), Image.LANCZOS)
    return B

if __name__ == '__main__':
    ks = [kf1(), kf2(), kf3()]
    for i, k in enumerate(ks, 1):
        assert k.size == (W, H); k.save(HERE + f'kf-{i}.png')
    names = ['1 · Narré par la clé (cutout puppet)', '2 · Inventaire des sens (shadow theatre)', '3 · Journal à rebours (archive, reversed)']
    board(ks, names).save(HERE + 'board.jpg', quality=88)
    print('ok')
