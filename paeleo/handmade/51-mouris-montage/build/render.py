"""SCION 51 · render the 32 s scene by montage.
The dog: one steady body of spheres (stable silhouette, stable shading, stable dark contour). Its surface carries whole
images that are substituted on the cutting score (coat, eyes, paws); textures are pinned to the body (rest-pose coordinates),
so they turn with it. The room (facade, door leaf, lit interior) is substituted on the same score. The words are cut letters.
Usage: python3 render.py [start end]  -> build/cache/frames/s%03d.jpg  and build/cache/meas/%03d.json (measurements)."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from lib import *
from lib import dog_world, person_world, feet_for
import lib

CACHE = os.path.join(OUT, 'build/cache')
FR_DIR = os.path.join(CACHE, 'frames'); MEAS = os.path.join(CACHE, 'meas')
os.makedirs(FR_DIR, exist_ok=True); os.makedirs(MEAS, exist_ok=True)
INV = {r['id']: r for r in json.load(open(os.path.join(OUT, 'inventory.json')))['records']}
CUTS = json.load(open(os.path.join(OUT, 'cutting-score.json')))['cuts']
WORDS = json.load(open(os.path.join(OUT, 'words.json')))['words']
POSES = json.load(open(os.path.join(CACHE, 'poses.json')))
CUT_AT = []
for c in CUTS:
    CUT_AT += [c] * c['hold']

PAL = {'cold': (np.array([0.09, 0.12, 0.19]), np.array([0.60, 0.71, 0.86])),
       'neutral': (np.array([0.15, 0.12, 0.11]), np.array([0.74, 0.67, 0.58])),
       'warm': (np.array([0.24, 0.10, 0.05]), np.array([0.99, 0.79, 0.52]))}

# ------------------------------------------------------------- textures (whole images, normalised)
_tex = {}


def tex(rid, size=256, color=False):
    k = (rid, size, color)
    if k not in _tex:
        r = INV[rid]; im = Image.open(os.path.join(OUT, r['file'])).convert('RGB'); w, h = im.size; c = r['crop_norm']
        im = im.crop((int(c[0] * w), int(c[1] * h), int(c[2] * w), int(c[3] * h))).resize((size, size), Image.BICUBIC)
        a = np.asarray(im, np.float32) / 255
        if color:
            _tex[k] = a
        else:
            L = a @ np.array([0.3, 0.59, 0.11], np.float32)
            lo, hi = np.percentile(L, 3), np.percentile(L, 97)
            _tex[k] = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
    return _tex[k]


def sample(T, u, v):
    """bilinear, mirrored repeat"""
    n = T.shape[0]
    def mir(x):
        x = np.mod(x, 2.0); return np.where(x > 1, 2 - x, x)
    x = mir(u) * (n - 1); y = mir(v) * (n - 1)
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); x1 = np.minimum(x0 + 1, n - 1); y1 = np.minimum(y0 + 1, n - 1)
    fx = x - x0; fy = y - y0
    if T.ndim == 3:
        fx = fx[..., None]; fy = fy[..., None]
    return (T[y0, x0] * (1 - fx) * (1 - fy) + T[y0, x1] * fx * (1 - fy) + T[y1, x0] * (1 - fx) * fy + T[y1, x1] * fx * fy)


def tint(L, temp, lo=0.0, hi=1.0):
    d, l = PAL[temp]; L = lo + (hi - lo) * L
    return d[None] + (l - d)[None] * L[..., None]


# ------------------------------------------------------------- static environment (2x)
LAMP = np.array([-0.05, 1.9, -1.7])
GROUP = {'torso': 'body', 'neck': 'neck', 'head': 'head', 'muzzle': 'head', 'ear': 'head', 'tail': 'tail', 'leg': 'leg', 'paw': 'leg', 'eye': 'eye', 'nose': 'nose'}
ENV_IDS = {'sky': 0, 'floor': 1, 'yard': 2, 'facade': 3, 'trim': 4, 'jamb': 5, 'lintel': 6, 'sill': 7, 'ifloor': 8, 'back': 9, 'side': 10, 'ceil': 11, 'leaf': 12}


def build_env(D):
    Hh, Ww = D.shape[:2]
    best_t = np.full((Hh, Ww), np.inf, np.float32); idm = np.zeros((Hh, Ww), np.uint8)
    def plane(axis, val, cond, name):
        dd = D[..., axis]
        with np.errstate(divide='ignore', invalid='ignore'):
            t = (val - lib.CAM[axis]) / dd
        t = np.where(t > 0.05, t, np.inf)
        P = lib.CAM[None, None] + D * t[..., None]
        ok = cond(P) & (t < best_t)
        best_t[ok] = t[ok]; idm[ok] = ENV_IDS[name]
    x = lambda P: P[..., 0]; y = lambda P: P[..., 1]; z = lambda P: P[..., 2]
    inopen = lambda P: (np.abs(x(P)) < DOOR_HW) & (y(P) < DOOR_H)
    plane(1, 0.0, lambda P: (z(P) >= 0) & (z(P) < 4.9) & (np.abs(x(P)) < 7), 'floor')
    plane(1, -0.45, lambda P: (z(P) >= 4.9) & (np.abs(x(P)) < 30), 'yard')
    plane(2, 0.0, lambda P: (y(P) > -0.5) & (y(P) < 3.3) & (np.abs(x(P)) < 7) & ~inopen(P), 'facade')
    plane(0, -DOOR_HW, lambda P: (z(P) <= 0) & (z(P) >= -WALL_T) & (y(P) >= 0) & (y(P) <= DOOR_H), 'jamb')
    plane(1, DOOR_H, lambda P: (z(P) <= 0) & (z(P) >= -WALL_T) & (np.abs(x(P)) <= DOOR_HW), 'lintel')
    plane(1, 0.04, lambda P: (z(P) <= 0.12) & (z(P) >= -WALL_T) & (np.abs(x(P)) <= DOOR_HW + 0.05), 'sill')
    plane(2, 0.12, lambda P: (y(P) <= 0.04) & (y(P) >= 0) & (np.abs(x(P)) <= DOOR_HW + 0.05), 'sill')
    plane(1, 0.0, lambda P: (z(P) < -WALL_T) & (z(P) > -3.2) & (np.abs(x(P)) < 2.6), 'ifloor')
    plane(2, -3.2, lambda P: (np.abs(x(P)) < 2.6) & (y(P) < 2.6) & (y(P) > 0), 'back')
    plane(0, -2.6, lambda P: (z(P) < -WALL_T) & (z(P) > -3.2) & (y(P) < 2.6) & (y(P) > 0), 'side')
    plane(1, 2.6, lambda P: (z(P) < -WALL_T) & (z(P) > -3.2) & (np.abs(x(P)) < 2.6), 'ceil')
    P = lib.CAM[None, None] + D * np.where(np.isfinite(best_t), best_t, 50)[..., None]
    # trim around the door on the facade
    fac = idm == ENV_IDS['facade']
    trim = fac & (((np.abs(P[..., 0]) < DOOR_HW + 0.1) & (P[..., 1] < DOOR_H + 0.1)) )
    idm[trim] = ENV_IDS['trim']
    return best_t, idm, P.astype(np.float32)


def plank_albedo(P, warm=False, seed=3):
    rng = np.random.RandomState(seed)
    tones = rng.uniform(0.82, 1.08, 400)
    k = np.floor(P[..., 0] / 0.14).astype(int) + 200
    a = tones[np.clip(k, 0, 399)]
    g = 0.94 + 0.06 * np.sin(P[..., 2] * 23 + k * 1.7) * np.sin(P[..., 2] * 7.1 + k)
    seam = np.abs((P[..., 0] / 0.14) - np.round(P[..., 0] / 0.14)) < 0.05
    a = a * g * np.where(seam, 0.45, 1.0)
    return a.astype(np.float32)


def door_light(Pts, theta, level):
    """warm light from the lamp, through the opening (ajar: only through the gap). Pts (...,3) outside or on the sill"""
    d = Pts - LAMP
    out = np.zeros(Pts.shape[:-1], np.float32)
    for zc in (0.0, -WALL_T):
        with np.errstate(divide='ignore', invalid='ignore'):
            s = (zc - LAMP[2]) / d[..., 2]
        X = LAMP + d * s[..., None]
        xg = -DOOR_HW + 2 * DOOR_HW * (1 - math.sin(theta)) if theta < math.radians(88) else -DOOR_HW
        ok = (s > 0) & (s < 1.0001) & (X[..., 0] < DOOR_HW) & (X[..., 0] > xg) & (X[..., 1] < DOOR_H) & (X[..., 1] > 0)
        out = ok.astype(np.float32) if zc == 0 else out * ok
    dist = np.linalg.norm(d, axis=-1)
    return out * level / (1 + (dist / 2.4) ** 2)


# ------------------------------------------------------------- sphere renderer
def render_spheres(D, C, R, ox=0, oy=0, ss=SS):
    """depth along the ray and sphere index for the pixels of D (a box whose top-left is (ox, oy) in ss-pixels)"""
    Hh, Ww = D.shape[:2]
    tbuf = np.full((Hh, Ww), np.inf, np.float32); ibuf = np.full((Hh, Ww), -1, np.int32)
    pr = project(C, ss)
    for k in range(len(C)):
        cx, cy, dep = pr[k]; cx -= ox; cy -= oy
        if dep <= 0.1:
            continue
        rad = lib.FOCAL * ss * R[k] / dep * 1.15 + 2
        x0, x1 = int(max(0, cx - rad)), int(min(Ww, cx + rad + 1)); y0, y1 = int(max(0, cy - rad)), int(min(Hh, cy + rad + 1))
        if x0 >= x1 or y0 >= y1:
            continue
        d = D[y0:y1, x0:x1]; oc = C[k] - lib.CAM
        b = d @ oc; cc = oc @ oc - R[k] ** 2
        disc = b * b - cc
        hit = disc > 0
        t = np.where(hit, b - np.sqrt(np.maximum(disc, 0)), np.inf)
        sub = tbuf[y0:y1, x0:x1]; m = t < sub
        sub[m] = t[m]; ibuf[y0:y1, x0:x1][m] = k
    return tbuf, ibuf


def dilate(m, r):
    o = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


# ------------------------------------------------------------- words: cut letters
FONT_BOLD = os.path.join(REPO, 'tools/paeleo/fonts/f8.woff2')
FONT_SOFT = os.path.join(REPO, 'tools/paeleo/fonts/f34.woff2')
_letters = {}


def letter_sprite(ch, size, rid, temp, seed, soft):
    key = (ch, size, rid, temp, seed)
    if key in _letters:
        return _letters[key]
    font = ImageFont.truetype(FONT_SOFT if soft else FONT_BOLD, size)
    font.set_variation_by_axes([36, 800] if soft else [900])
    bb = font.getbbox(ch); w, h = bb[2] - bb[0] + 16, bb[3] - bb[1] + 16
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((8 - bb[0], 8 - bb[1]), ch, font=font, fill=255)
    rng = np.random.RandomState(seed)
    T = tex(rid, 256)
    yy, xx = np.mgrid[0:h, 0:w]
    ox, oy = rng.uniform(0, 0.5, 2)
    L = sample(T, ox + xx / 300.0, oy + yy / 300.0)
    col = tint(L, temp, 0.15, 1.0)
    mg = np.asarray(m, np.float32) / 255
    chip = np.asarray(m.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    chip = (chip > 0.35).astype(np.float32)                      # a cut-paper chip around each letter
    paper_col = np.array([0.94, 0.90, 0.80]) if temp != 'cold' else np.array([0.90, 0.91, 0.92])
    col = tint(L, temp, 0.0, 0.62) if temp == 'cold' else tint(L, temp, 0.0, 0.5)
    rgb = paper_col[None, None] * (1 - mg[..., None]) + col * mg[..., None]
    rgba = np.dstack([rgb, chip]).astype(np.float32)
    im = Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').rotate(rng.uniform(-9, 9), resample=Image.BICUBIC, expand=True)
    _letters[key] = im
    return im


def word_anchor(wd):
    """fixed places in the frame, chosen so the letters never cover the dog (checked on the frames)"""
    return {'above_person': (300, 70), 'by_hand': (640, 600), 'by_hand2': (680, 612), 'in_doorway': (880, 130)}.get(wd['anchor'], (W / 2, H / 3))


def words_layer(img, t):
    """paste cut letters for every phrase active at t (img: PIL RGB 1x). Returns list of visible words."""
    vis = []
    for wn, wd in enumerate(WORDS):
        s0, s1 = wd['spoken']
        tail = 0.6 if wd['exit'] == 'drop' else (1.2 if wd['exit'] == 'fade' else 1.9)
        if not (s0 <= t < s1 + tail):
            continue
        soft = wd['voice'] == 'soft'
        words = wd['text'].split(' ')
        ax, ay = word_anchor(wd)
        x = ax; rng = np.random.RandomState(wn * 31 + 7)
        alpha_all = 1.0
        if wd['exit'] in ('fade', 'fade_late') and t > s1:
            alpha_all = max(0.0, 1 - (t - s1) / tail)
        li = 0; shown = []
        for wi, wword in enumerate(words):
            ton = wd['syll'][min(wi, len(wd['syll']) - 1)]
            for ch in wword:
                rid = wd['letters_from'][li % len(wd['letters_from'])]
                sp = letter_sprite(ch, wd['size'], rid, wd['temperature'], wn * 100 + li, soft)
                on = ton + (0.0 if soft else 0.0) + li * (0.0 if not soft else 0.0)
                yj = rng.uniform(-8, 8)
                if t >= on:
                    a = alpha_all
                    if soft:
                        a *= min(1.0, 0.5 + (t - on) / 0.08)   # appears at its spoken frame
                    dy = 0
                    if wd['exit'] == 'drop' and t > s1:
                        k = (t - s1) / tail; dy = (k ** 2) * 500 * (0.6 + 0.4 * ((li * 37) % 7) / 7)
                    if a > 0.01:
                        spa = sp
                        if a < 0.999:
                            r, g, b, al = sp.split(); al = al.point(lambda v: int(v * a)); spa = Image.merge('RGBA', (r, g, b, al))
                        shadow = Image.new('RGBA', sp.size, (0, 0, 0, 0)); shadow.putalpha(spa.split()[3].point(lambda v: int(v * 0.45)))
                        img.paste((10, 8, 6), (int(x + 4), int(ay + yj + dy + 5)), shadow.split()[3])
                        img.paste(spa, (int(x), int(ay + yj + dy)), spa)
                        shown.append(ch)
                x += sp.size[0] * (0.82 if not soft else 0.86); li += 1
            x += wd['size'] * 0.35
        if shown:
            vis.append(wd['text'])
    return vis


# ------------------------------------------------------------- one frame
G1 = None; G1_KEY = None; BG = None; BG_KEY = None
_yy1, _xx1 = np.mgrid[0:H, 0:W]
VIGN = (1 - 0.35 * (((_xx1 - W / 2) / (W / 2)) ** 2 + ((_yy1 - H / 2) / (H / 2)) ** 2) * 0.5)[..., None]


def door_theta(t):
    return math.radians(lerp(34, 100, smooth(6.2, 6.85, t)))


def light_level(t):
    return lerp(0.42, 1.0, smooth(6.2, 6.85, t))


def rays_box(ss, x0, y0, x1, y1):
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    px = (xs + .5) / ss - W / 2; py = H / 2 - (ys + .5) / ss
    d = lib.U[None, None] * px[..., None] / lib.FOCAL + lib.V[None, None] * py[..., None] / lib.FOCAL + lib.Wd[None, None]
    return (d / np.linalg.norm(d, axis=-1, keepdims=True)).astype(np.float32)


def env_shade(D, tenv, idm, Penv, cut, theta, lvl):
    """the room, with this cut's whole images. Returns rgb, ids (with leaf), depth tE, points PE"""
    temp = cut['temperature']
    rgb = np.zeros(D.shape, np.float32)
    hinge = np.array([-DOOR_HW, 0, -WALL_T]); e = np.array([math.cos(theta), 0, -math.sin(theta)]); n = np.array([math.sin(theta), 0, math.cos(theta)])
    inside_ids = np.isin(idm, [ENV_IDS[k] for k in ('ifloor', 'back', 'side', 'ceil')])
    with np.errstate(divide='ignore', invalid='ignore'):
        tl = ((hinge - lib.CAM) @ n) / (D @ n)
    Pl = lib.CAM[None, None] + D * tl[..., None]
    sl = (Pl - hinge) @ e
    leaf = inside_ids & (tl > 0) & (tl < tenv) & (sl >= 0) & (sl <= 2 * DOOR_HW) & (Pl[..., 1] >= 0) & (Pl[..., 1] <= 2.0)
    ids = idm.copy(); ids[leaf] = ENV_IDS['leaf']
    tE = np.where(leaf, tl, tenv); PE = np.where(leaf[..., None], Pl, Penv)
    X, Y, Z = PE[..., 0], PE[..., 1], PE[..., 2]
    m = ids == ENV_IDS['facade']
    if m.any():
        Lr = sample(tex(cut['room']), X[m] / 2.3 + 0.5, 1 - Y[m] / 2.7)
        clap = (np.abs((Y[m] / 0.19) - np.round(Y[m] / 0.19)) < 0.06)
        rgb[m] = tint(Lr, temp, 0.33, 0.58) * np.where(clap, 0.62, 1.0)[:, None] * 0.62
    m = ids == ENV_IDS['trim']; rgb[m] = np.array([0.55, 0.52, 0.47]) * 0.62
    m = ids == ENV_IDS['jamb']; rgb[m] = np.array([0.30, 0.22, 0.16]) * (0.6 + 0.6 * lvl)
    m = ids == ENV_IDS['lintel']; rgb[m] = np.array([0.20, 0.15, 0.11]) * (0.5 + 0.5 * lvl)
    m = (ids == ENV_IDS['floor']) | (ids == ENV_IDS['sill'])
    if m.any():
        Pm = PE[m]; alb = plank_albedo(Pm)
        dl = door_light(Pm, theta, lvl)
        base = np.array([0.30, 0.31, 0.36]) * alb[:, None]
        base = np.where((ids[m] == ENV_IDS['sill'])[:, None], np.array([0.42, 0.33, 0.24]) * 0.9, base)
        rgb[m] = base * 0.75 + (np.array([1.0, 0.70, 0.38]) * 1.15 * dl[:, None]) * alb[:, None]
    m = ids == ENV_IDS['yard']; rgb[m] = np.array([0.07, 0.08, 0.11])
    m = ids == ENV_IDS['sky']; rgb[m] = np.array([0.20, 0.22, 0.33])
    warm = np.array([1.0, 0.80, 0.55])
    for nm in ('back', 'side'):
        m = ids == ENV_IDS[nm]
        if m.any():
            uu = (X[m] + 2.6) / 2.6 if nm == 'back' else (Z[m] + 3.2) / 3.2
            Li = sample(tex(cut['interior']), uu, 1 - Y[m] / 2.6)
            fall = 1 / (1 + (np.linalg.norm(PE[m] - LAMP, axis=-1) / 2.2) ** 2)
            rgb[m] = tint(Li, 'warm', 0.35, 1.0) * (0.35 + 0.9 * fall)[:, None] * lvl
    m = ids == ENV_IDS['ifloor']
    if m.any():
        rgb[m] = np.array([0.55, 0.38, 0.22]) * plank_albedo(PE[m], True, 9)[:, None] * lvl * (0.5 + 0.8 / (1 + (np.linalg.norm(PE[m] - LAMP, axis=-1) / 2.0) ** 2))[:, None]
    m = ids == ENV_IDS['ceil']; rgb[m] = np.array([0.45, 0.35, 0.25]) * lvl
    m = ids == ENV_IDS['leaf']
    if m.any():
        Ld = sample(tex(cut['door']), sl[m] / (2 * DOOR_HW), 1 - Y[m] / 2.0)
        fall = 1 / (1 + (np.linalg.norm(PE[m] - LAMP, axis=-1) / 2.2) ** 2)
        rgb[m] = tint(Ld, 'neutral', 0.35, 0.9) * (0.35 + 0.8 * fall)[:, None] * lvl * warm
    return rgb, ids, tE, PE


def frame(i):
    global G1, G1_KEY, BG, BG_KEY
    t = i / FPS
    key = lib.set_camera(t)
    pose = POSES[i]; P = pose['dog']; Q = pose['person']; cut = CUT_AT[i]
    temp = cut['temperature']
    theta = door_theta(t); lvl = light_level(t)
    if G1 is None or key != G1_KEY:
        G1_KEY = key; D1 = rays_box(1, 0, 0, W, H); G1 = (D1,) + build_env(D1)
    bkey = (key, cut['n'], round(theta, 4), round(lvl, 4))
    if BG is None or bkey != BG_KEY:
        BG_KEY = bkey; BG = env_shade(G1[0], G1[1], G1[2], G1[3], cut, theta, lvl)[0]
    rgb1 = BG.copy()
    # ---------------- bodies, rendered at 2x inside their box
    feet = feet_for(P, P['walk']); P = dict(P); P['feet'] = feet
    Cd, Rd, partd, Rsd, Rwd = dog_world(P)
    Cp, Rp, partp, Rsp, Rwp, headp = person_world(Q)
    C = np.concatenate([Cd, Cp]); R = np.concatenate([Rd, Rp]); parts = partd + partp; Rs = Rsd + Rsp
    nd = len(Cd)
    pr = project(C, 1); prg = project(C * np.array([1, 0, 1]), 1)
    rad = lib.FOCAL * R / pr[:, 2]
    bx0 = int(max(0, min((pr[:, 0] - rad).min(), prg[:, 0].min()) - 70)); bx1 = int(min(W, max((pr[:, 0] + rad).max(), prg[:, 0].max()) + 70))
    by0 = int(max(0, (pr[:, 1] - rad).min() - 30)); by1 = int(min(H, max((pr[:, 1] + rad).max(), prg[:, 1].max()) + 40))
    D = rays_box(SS, bx0 * SS, by0 * SS, bx1 * SS, by1 * SS)
    tenv, idm, Penv = build_env(D)
    rgb, ids, tE, PE = env_shade(D, tenv, idm, Penv, cut, theta, lvl)
    tb, ib = render_spheres(D, C, R, bx0 * SS, by0 * SS)
    vis = (ib >= 0) & (tb < tE)
    # shadows on the floor (soft contact occlusion from spheres)
    fl = ((ids == ENV_IDS['floor']) | (ids == ENV_IDS['sill'])) & ~vis
    ys, xs = np.nonzero(fl)
    if len(ys):
        # occlusion accumulated on a world-space floor grid (2 cm), then read at the floor pixels
        low = (C[:, 1] - R) < 0.6
        Cl, Rl = C[low], R[low]
        gx0, gz0 = Cl[:, 0].min() - 0.5, Cl[:, 2].min() - 0.5; cs = 0.02
        nx, nz = int((Cl[:, 0].max() + 0.5 - gx0) / cs) + 2, int((Cl[:, 2].max() + 0.5 - gz0) / cs) + 2
        gz_, gx_ = np.mgrid[0:nz, 0:nx]; gxw = gx0 + gx_ * cs; gzw = gz0 + gz_ * cs
        grid = np.zeros((nz, nx), np.float32)
        for k in range(len(Cl)):
            s = Rl[k] + 0.05; a = math.exp(-max(Cl[k, 1] - Rl[k], 0) / 0.35) * 0.35
            i0, i1 = max(0, int((Cl[k, 2] - 3 * s - gz0) / cs)), min(nz, int((Cl[k, 2] + 3 * s - gz0) / cs) + 1)
            j0, j1 = max(0, int((Cl[k, 0] - 3 * s - gx0) / cs)), min(nx, int((Cl[k, 0] + 3 * s - gx0) / cs) + 1)
            d2 = (gxw[i0:i1, j0:j1] - Cl[k, 0]) ** 2 + (gzw[i0:i1, j0:j1] - Cl[k, 2]) ** 2
            grid[i0:i1, j0:j1] += a * np.exp(-d2 / (2 * s * s))
        Pg = PE[ys, xs]
        gi = np.clip(((Pg[:, 2] - gz0) / cs).astype(int), 0, nz - 1); gj = np.clip(((Pg[:, 0] - gx0) / cs).astype(int), 0, nx - 1)
        inside = (Pg[:, 2] >= gz0) & (Pg[:, 2] < gz0 + nz * cs) & (Pg[:, 0] >= gx0) & (Pg[:, 0] < gx0 + nx * cs)
        occ = np.where(inside, grid[gi, gj], 0)
        rgb[ys, xs] *= (1 - 0.6 * np.minimum(1, occ))[:, None]
    # shade bodies
    if vis.any():
        yy, xx = np.nonzero(vis)
        k = ib[yy, xx]; tt = tb[yy, xx]
        Pw = lib.CAM[None] + D[yy, xx] * tt[:, None]
        Nrm = (Pw - C[k]) / R[k][:, None]
        out = np.zeros((len(k), 3), np.float32)
        pa = np.array(parts)[k]
        # local, pinned coordinates
        Rk = np.stack([Rs[j] for j in range(len(Rs))])[k]
        q = np.einsum('nji,nj->ni', Rk, Pw - C[k])           # R^T (p - c)
        # rest-centre: approximate with sphere index along body (stable per sphere): use world-free rest table
        q = q + REST[np.minimum(k, len(REST) - 1)] * (k < nd)[:, None]
        nl = np.einsum('nji,nj->ni', Rk, Nrm)
        wx, wy, wz = np.abs(nl[:, 0]) ** 4, np.abs(nl[:, 1]) ** 4, np.abs(nl[:, 2]) ** 4; ws = wx + wy + wz + 1e-6
        def tri(T, sc=1.0, ox=0.0, oy=0.0):
            a = sample(T, ox + q[:, 0] / sc, oy + 1 - q[:, 1] / sc)
            b = sample(T, ox + q[:, 2] / sc + 0.3, oy + 1 - q[:, 1] / sc)
            c = sample(T, ox + q[:, 0] / sc, oy + q[:, 2] / sc + 0.3)
            return (a * wz + b * wx + c * wy) / ws
        lkey = np.array([0.35, 0.9, 0.45]); lkey /= np.linalg.norm(lkey)
        amb = 0.50 + 0.55 * np.clip(Nrm @ lkey, 0, 1)
        dlb = door_light(Pw, theta, lvl)
        tl_ = LAMP[None] - Pw; tl_ /= np.linalg.norm(tl_, axis=-1, keepdims=True)
        lamb = np.clip((Nrm * tl_).sum(-1), 0, 1)
        rim = np.clip(1 - np.abs((Nrm * (-D[yy, xx])).sum(-1)), 0, 1) ** 3
        warmL = np.array([1.0, 0.72, 0.42])
        # dog (round 2): every part is a flat cut from a whole image, untinted, unshaded; the cut makes the silhouette
        sd = k < nd
        if sd.any():
            pr2 = project(Cd, SS); pr2[:, 0] -= bx0 * SS; pr2[:, 1] -= by0 * SS
            rad2 = lib.FOCAL * SS * Rd / pr2[:, 2]
            gk = np.array([GROUP.get(p if not p[-1].isdigit() else p[:-1], p) + (p[-1] if p[:3] in ('leg', 'paw') else '') for p in partd])
            gpx = gk[np.minimum(k, nd - 1)]
            for g in np.unique(gk):
                s = sd & (gpx == g)
                if not s.any():
                    continue
                if g in ('eye', 'nose'):
                    out[s] = np.array([0.07, 0.05, 0.04]) if g == 'eye' else np.array([0.03, 0.025, 0.02]); continue
                sel = gk == g
                gx0, gx1 = (pr2[sel, 0] - rad2[sel]).min(), (pr2[sel, 0] + rad2[sel]).max()
                gy0, gy1 = (pr2[sel, 1] - rad2[sel]).min(), (pr2[sel, 1] + rad2[sel]).max()
                rid = cut['dog_body'] if g in ('body', 'neck', 'tail') else cut['dog_head_legs']
                T = tex(rid, 384, color=True)
                u = (xx[s] - gx0) / max(gx1 - gx0, 1); v_ = (yy[s] - gy0) / max(gy1 - gy0, 1)
                out[s] = sample(T, np.clip(u, 0, 1), np.clip(v_, 0, 1))
        # person
        s = (k >= nd)
        if s.any():   # the person (round 3): flat cut-outs from public-domain images, like the dog; no shading
            prp = project(Cp, SS); prp[:, 0] -= bx0 * SS; prp[:, 1] -= by0 * SS
            radp = lib.FOCAL * SS * Rp / prp[:, 2]
            pk = np.array(partp)
            src = {'pcoat': 'soft.person.coat', 'pleg': 'person.suit', 'phead': 'person.head', 'skin': cut['hand'], 'hand': cut['hand'], 'pshoe': 'person.suit'}
            for g, rid in src.items():
                sg = s & (pa == g)
                if not sg.any():
                    continue
                sel = pk == g
                gx0, gx1 = (prp[sel, 0] - radp[sel]).min(), (prp[sel, 0] + radp[sel]).max()
                gy0, gy1 = (prp[sel, 1] - radp[sel]).min(), (prp[sel, 1] + radp[sel]).max()
                T = tex(rid, 384, color=True)
                out[sg] = sample(T, np.clip((xx[sg] - gx0) / max(gx1 - gx0, 1), 0, 1), np.clip((yy[sg] - gy0) / max(gy1 - gy0, 1), 0, 1))
            out[s & (pa == 'pshoe')] *= 0.4
        shade = amb[:, None] * np.array([0.78, 0.82, 0.95]) + (lamb * dlb * 1.5)[:, None] * warmL + (rim * 0.25)[:, None] * np.array([0.5, 0.55, 0.7])
        shade[:] = 1.0                           # no light on dog or person but what is in their images
        rgb[yy, xx] = out * shade
        gmap = np.full(vis.shape, -1, np.int32)
        if (k < nd).any():
            gk_ids = {g: n for n, g in enumerate(np.unique(gk))}
            gmap[yy[k < nd], xx[k < nd]] = np.array([gk_ids[g] for g in gpx[k < nd]])
    # contours: silhouette and depth breaks (legs over legs, head over body)
    if vis.any():
        ys_, xs_ = np.nonzero(vis)
        y0, y1 = max(0, ys_.min() - 8), min(vis.shape[0], ys_.max() + 9); x0, x1 = max(0, xs_.min() - 8), min(vis.shape[1], xs_.max() + 9)
        v = vis[y0:y1, x0:x1]; ibs = ib[y0:y1, x0:x1]; tbs = tb[y0:y1, x0:x1]
        dogm = v & (ibs < nd) & (ibs >= 0); perm = v & (ibs >= nd)
        dep = np.where(v, tbs, 100)
        brk = np.zeros_like(v)
        for ax in (0, 1):
            dd = np.abs(np.diff(dep, axis=ax, prepend=dep[:1] if ax == 0 else dep[:, :1]))
            brk |= (dd > 0.07) & v
        gm = gmap[y0:y1, x0:x1]
        for ax in (0, 1):   # the cut edges between pieces (body, neck, head, each leg, tail)
            gd = np.diff(gm, axis=ax, prepend=gm[:1] if ax == 0 else gm[:, :1])
            brk |= (gd != 0) & (gm >= 0)
        bod = dogm | perm
        paper = dilate(bod, 2) & ~bod                        # a thin paper margin left by the scissors
        dark = dilate(bod, 4) & ~dilate(bod, 2)
        edge = dilate(brk, 1) & v
        sub = rgb[y0:y1, x0:x1]
        sub[paper & ~v] = np.array([0.90, 0.86, 0.76])
        sub[dark & ~v & ~paper] = np.array([0.04, 0.035, 0.03])
        sub[edge] *= 0.3
    # ---------------- downsample the box to 1x and lay it into the frame
    hb, wb = by1 - by0, bx1 - bx0
    rgb1[by0:by1, bx0:bx1] = rgb[:hb * SS, :wb * SS].reshape(hb, SS, wb, SS, 3).mean((1, 3))
    img = np.clip(rgb1 * VIGN, 0, 1)
    pil = Image.fromarray((img ** (1 / 1.1) * 255).astype(np.uint8))
    vw = words_layer(pil, t)
    pil.save(os.path.join(FR_DIR, f's{i:03d}.jpg'), quality=92)
    meas = measure(i, D, tb, ib, vis, nd, partd, Cd, bx0 * SS, by0 * SS)
    meas['cut'] = cut['n']; meas['coat'] = cut['dog_body']; meas['dog_head_legs'] = cut['dog_head_legs']; meas['words'] = vw; meas['camera'] = key
    json.dump(meas, open(os.path.join(MEAS, f'{i:03d}.json'), 'w'))


def measure(i, D, tb, ib, vis, nd, partd, Cd, ox=0, oy=0):
    dm = vis & (ib >= 0) & (ib < nd)
    yy, xx = np.nonzero(dm)
    res = {'i': i, 'visible_px': int(len(yy) / SS / SS)}
    if not len(yy):
        return res
    k = ib[yy, xx]; Pw = lib.CAM[None] + D[yy, xx] * tb[yy, xx][:, None]
    pa = np.array(partd)[k]
    res['x_screen'] = round(float((xx.mean() + ox) / SS), 1); res['y_screen'] = round(float((yy.mean() + oy) / SS), 1)
    torso_idx = pa == 'torso'
    if torso_idx.any():
        res['torso_z'] = float(Pw[torso_idx, 2].mean()); res['torso_top_y'] = float(np.percentile(Pw[torso_idx, 1], 95))
        res['torso_mean_y'] = float(Pw[torso_idx, 1].mean())
    hd = (pa == 'head') | (pa == 'muzzle') | (pa == 'nose') | (pa == 'eye') | (pa == 'ear')
    if hd.any():
        res['head_top_y'] = float(np.percentile(Pw[hd, 1], 95)); res['head_z'] = float(Pw[hd, 2].mean())
        res['head_x'] = float(Pw[hd, 0].mean())
    mz = (pa == 'muzzle') | (pa == 'nose'); sk = pa == 'head'; nk = pa == 'neck'
    if mz.sum() > 4 * SS * SS and sk.sum() > 4:
        dv = Pw[mz].mean(0) - Pw[sk].mean(0); res['head_dir_from'] = 'muzzle-skull'
    elif hd.sum() > 4 and nk.sum() > 4:      # muzzle hidden (back of the head to the camera): neck -> head
        dv = Pw[hd].mean(0) - Pw[nk].mean(0); res['head_dir_from'] = 'neck-head'
    else:
        dv = None
    if dv is not None:
        res['muzzle_dir_xz'] = [float(dv[0]), float(dv[2])]; res['muzzle_dy'] = float(dv[1])
    res['frac_past_outer_face'] = round(float((Pw[:, 2] < 0).mean()), 3)
    tl = pa == 'tail'
    res['tail_z'] = float(Pw[tl, 2].mean()) if tl.any() else None
    res['n_px_head'] = int(hd.sum())
    return res


# rest-pose table: sphere centres of the standing dog in its local frame (texture pinning)
def _rest():
    from lib import dog_local
    P = {'t': 0, 'lie': 0, 'crouch': 0, 'ear': 0.9, 'tail': 0.5, 'wag': 0, 'neck': 50, 'muzzle': -12, 'head_yaw': 0, 'moving': 0, 'walk': 0}
    P['feet'] = feet_for(P, 0)
    return np.array(dog_local(P).c)


REST = _rest()

if __name__ == '__main__':
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 0; b = int(sys.argv[2]) if len(sys.argv) > 2 else 768
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    for i in range(a, b, step):
        frame(i)
