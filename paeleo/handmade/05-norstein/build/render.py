"""The multiplane: lays the painted glasses at their depths under a moving camera, with fog fields between them,
the door's light passing through the fog, and the two cutouts; defocus per plane from the focus schedule.
Run: python3 render.py [--frames a:b] [--every k]  -> build/cache/frames/s%04d.jpg + build/cache/measure/*.json
"""
import json, math, os, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from multiprocessing import Pool
from common import *
import dog as DOG
import person as PERSON
import pieces as PIECES

PL = os.path.join(CACHE, 'planes')
FRAMES = os.path.join(CACHE, 'frames')
MEAS = os.path.join(CACHE, 'measure')
G = {}

DUSK = np.array([112, 124, 150.], np.float32)       # fog in the blue hour
WARM = np.array([255, 190, 122.], np.float32)      # the house's light
LAMP = np.array([-0.15, 1.25, 6.9])                # where the room's light comes from


def init():
    meta = json.load(open(os.path.join(PL, 'planes.json')))
    G['planes'] = {}
    for m in meta:
        im = Image.open(os.path.join(PL, m['name'] + '.png')).convert('RGBa')
        G['planes'][m['name']] = (m, im)
    G['fog'] = np.load(os.path.join(CACHE, 'fog_cloud.npy')).astype(np.float32)
    G['fog_inner'] = np.load(os.path.join(CACHE, 'fog_inner.npy')).astype(np.float32)
    G['dogP'] = json.load(open(os.path.join(CACHE, 'dog_params.json')), object_hook=_obj)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    G['xs'], G['ys'] = xs, ys
    r = np.random.default_rng(3)
    G['fur'] = np.asarray(Image.fromarray((r.random((900, 1500)) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1)), np.float32) / 255
    coat = np.load(os.path.join(CACHE, 'coat_tex.npy'))
    G['coat'] = np.tile(coat, (4, 6))
    G['board'] = np.random.default_rng(9).random((2000,)).astype(np.float32)


def _obj(d):
    if 'feet' in d:
        d['feet'] = {k: (np.array(v[0]), v[1], v[2]) for k, v in d['feet'].items()}
    return d


# ------------------------------------------------------------------------------------------------ helpers
def blur(im, r):
    """defocus a premultiplied layer; large radii are done at reduced size (cheap, and softer like a far glass)."""
    if r < 0.6:
        return im
    if r > 7:
        k = r / 5.0
        sm = im.resize((max(1, int(W / k)), max(1, int(H / k))), Image.BILINEAR)
        sm = sm.filter(ImageFilter.GaussianBlur(r / k))
        return sm.resize((W, H), Image.BILINEAR)
    return im.filter(ImageFilter.GaussianBlur(r))


def to_np(im):
    a = np.asarray(im, np.float32) / 255.0
    return a[..., :3], a[..., 3]


def over(out, rgb, a):
    """premultiplied 'over'."""
    out *= (1 - a)[..., None]
    out += rgb


def place(name, c, t, extra_blur=0.0, rmax=40):
    m, im = G['planes'][name]
    zc = m['z'] - c[2]
    s = F / zc  # px per metre on screen
    k = zc * m['ppm'] / F
    a_ = k
    c_ = -(CX + s * (m['X0'] - c[0])) * k
    e_ = k
    f_ = -(CY - s * (m['Y1'] - c[1])) * k
    out = im.transform((W, H), Image.AFFINE, (a_, 0, c_, 0, e_, f_), Image.BILINEAR)
    r = min(rmax, blur_px(m['z'], t) + extra_blur)
    return blur(out, r)


def beam(X, Y, Zp, t):
    """the door's light at world points: is the point lit from the room through the open part of the doorway?"""
    u = (Z['wall'] - LAMP[2]) / (Zp - LAMP[2])
    Xw = LAMP[0] + (X - LAMP[0]) * u
    Yw = LAMP[1] + (Y - LAMP[1]) * u
    th = math.radians(door_angle(t))
    xe = 0.46 - 0.92 * math.cos(th)  # the leaf's free edge (the open part is from the left jamb to here)
    soft = 0.05 + 0.06 * max(0.0, Z['wall'] - float(np.mean(Zp)))
    inx = np.clip((Xw + 0.46) / soft + 0.5, 0, 1) * np.clip((xe - Xw) / soft + 0.5, 0, 1)
    iny = np.clip((Yw + 0.02) / soft + 0.5, 0, 1) * np.clip((2.08 - Yw) / soft + 0.5, 0, 1)
    d2 = (X - LAMP[0]) ** 2 + (Zp - LAMP[2]) ** 2
    fall = 1.0 / (1 + np.maximum(d2 - 3.0, 0) / 5.0)
    block = 1.0 - 0.6 * (1 - smooth(5.3, 5.8, t))  # the person standing in the doorway holds most of it back
    return inx * iny * fall * block


def light_level(t):
    return 0.55 + 0.45 * smooth(6.2, 6.9, t)


def ambient(t):
    """exposure schedule: the blue hour darkens slowly while the house's light grows."""
    return 1.0 - 0.12 * smooth(4, 30, t)


# ------------------------------------------------------------------------------------------------ fog fields
DRIFT_KEYS = [(0, 0.05), (1.0, 0.10), (6.2, 0.10), (6.6, -0.16), (14.7, -0.12), (23.8, -0.05), (25.5, -0.008), (32, -0.008)]


def drift(t):
    """the atmosphere's own motion (m along X): obscure rolls out towards the dog, lure is drawn in to the light,
    reveal parts, suspend hangs."""
    n = int(t * 24)
    return sum(keyed(DRIFT_KEYS, k / 24) for k in range(n)) / 24


def atmosphere_state(t):
    if t < 1.0: return 'suspend'
    if t < 6.2: return 'obscure'
    if t < 14.7: return 'lure'
    if t < 23.8: return 'reveal'
    return 'suspend'


def fog_layer(zf, c, t, amount, amax, profile, kscale=60.0, seed_off=0.0, warmk=1.0, rows_per_m=46.0, ytop=2.6, src='fog'):
    zc = zf - c[2]
    Xcol = c[0] + (np.arange(W, dtype=np.float32) - CX) * zc / F
    Yrow = c[1] - (np.arange(H, dtype=np.float32) - CY) * zc / F
    fi = (t * 1.9 + seed_off * 7) % 61
    f0 = int(fi)
    w = fi - f0
    strip = G[src][f0] * (1 - w) + G[src][f0 + 1] * w
    strip = np.concatenate([strip] * 3, 1)
    sw = strip.shape[1]
    im = Image.fromarray(np.clip(strip * 255, 0, 255).astype(np.uint8))
    # texture coordinates: u = X*kscale + drift ; v = (2.6 - Y) * rows_per_m
    dr = drift(t) * (1.0 if zf > 3.5 else 1.4)
    u0 = (Xcol[0] * kscale - dr * kscale + seed_off * 300) % (sw / 3) + sw / 3
    du = (Xcol[1] - Xcol[0]) * kscale
    v0 = (ytop - Yrow[0]) * rows_per_m
    dv = -(Yrow[1] - Yrow[0]) * rows_per_m
    tex = im.transform((W, H), Image.AFFINE, (du, 0, u0, 0, dv, v0), Image.BILINEAR)
    tex = np.asarray(tex.filter(ImageFilter.GaussianBlur(2.5)), np.float32) / 255
    dens = (0.15 + 1.5 * tex ** 1.4) * profile(Xcol[None, :], Yrow[:, None], t)
    a = np.clip(dens * amount, 0, amax)
    b = beam(Xcol[None, :], Yrow[:, None], np.float32(zf), t) * light_level(t) * warmk
    col = DUSK[None, None, :] * ambient(t) * (0.85 + 0.3 * tex[..., None]) + WARM[None, None, :] * b[..., None] * 0.85
    col = np.minimum(col, 255) / 255
    r = blur_px(zf, t)
    rgb = col * a[..., None]
    if r > 2:
        img = Image.fromarray(np.dstack([rgb * 255, a * 255]).astype(np.uint8), 'RGBa')
        rgb, a = to_np(blur(img, r * 0.6))
    return rgb, a


def prof_back(X, Y, t):
    return 0.85 * np.exp(-np.maximum(Y - 0.3, 0) / 2.2) + 0 * X


def prof_porch(X, Y, t):
    """the bank between the door and the dog: thick while commands are given (obscure), pierced and drawn in by the
    light (lure), parted along the dog's way (reveal), hanging (suspend)."""
    obscure = smooth(0.8, 2.6, t) * (1 - 0.55 * smooth(6.4, 9.0, t))
    bank = np.exp(-((X - 2.2) ** 2) / 0.9) * (0.25 + 0.85 * obscure)
    i = min(N - 1, int(t * 24))
    xd = FR[i]['dog']['x']
    part = 1 - 0.5 * np.exp(-((X - xd + 0.6) ** 2) / 0.7) * smooth(14.5, 16.0, t)
    u_ = np.clip((X - 3.6) / 1.8, 0, 1)
    edge = 0.35 * u_ * u_ * (3 - 2 * u_) * (1 - 0.8 * smooth(6.6, 7.2, t) * (1 - smooth(8.8, 10, t)))  # the bank lifts off the dog for the turn to look
    # the silhouette is kept readable exactly when it acts: the fog thins round the dog, most at its choices
    near_choice = max([1 - smooth(0.25, 0.9, abs(t - ct)) for ct in (1.0, 2.33, 3.42, 3.9, 7.0, 7.46, 7.9, 8.4, 14.71, 23.79, 26.6, 27.3)])
    clear = 1 - (0.6 + 0.35 * near_choice) * np.exp(-((X - xd) ** 2) / 0.6)  # towards the steps the fog comes up from the yard
    low = np.exp(-np.maximum(Y - 0.1, 0) / 1.0)
    return (0.18 + bank * part + edge) * low * clear


def prof_near(X, Y, t):
    # ground fog in front of the porch (lies below the boards), and wisps that rise towards the steps
    ground = 1.1 * np.exp(-np.maximum(Y + 0.15, 0) / 0.35)
    side = (0.15 + 0.6 * np.clip((X - 2.6) / 3.0, 0, 1) + 0.25 * np.clip((-1.2 - X) / 2, 0, 1)) * np.exp(-np.maximum(Y, 0) / 1.2)
    return ground + side


def prof_far(X, Y, t):
    return 0.9 * np.exp(-np.maximum(Y + 0.2, 0) / 3.5) + 0 * X


# ------------------------------------------------------------------------------------------------ floors (per-pixel rays)
def floors(c, t, dogp, perq):
    xs, ys = G['xs'], G['ys']
    dy = -(ys - CY) / F
    dx = (xs - CX) / F
    out_far = np.zeros((H, W, 3), np.float32), np.zeros((H, W), np.float32)
    below = dy < -1e-4

    def hit(h):
        s = np.where(below, (h - c[1]) / np.where(below, dy, -1), 0.0)
        return c[0] + s * dx, c[2] + s, s

    # interior floor (seen through the doorway)
    Xi, Zi, si = hit(0.0)
    m_in = below & (Zi > 5.06) & (Zi < Z['interior_wall']) & (np.abs(Xi) < 4)
    lampd = (Xi - LAMP[0]) ** 2 + (Zi - LAMP[2]) ** 2
    seam = (np.mod(Xi, 0.12) < 0.008)
    col_in = np.array([138, 88, 52.]) * (0.45 + 0.75 / (1 + lampd / 1.5))[..., None] * np.where(seam, 0.7, 1.0)[..., None]
    interior = (col_in / 255 * m_in[..., None], m_in.astype(np.float32))
    # yard beyond the house
    Xg, Zg, sg = hit(-0.45)
    m_yard = below & (Zg > 5.0) & (Xg > 5.2) & (Zg < 16)
    fogk = 1 - np.exp(-(Zg - 4.5) / 4.0)
    gcol = np.array([30, 36, 42.]) * (1 - fogk[..., None]) + DUSK * 0.8 * fogk[..., None]
    yard = (gcol / 255 * m_yard[..., None], m_yard.astype(np.float32))
    # the porch: boards (Y=0, Z 3.8..5.0), the sill, the step, the fascia, the ground in front
    Xp, Zp, sp = Xi, Zi, si
    m_p = below & (Zp >= 3.8) & (Zp <= 5.0) & (Xp > -7) & (Xp < 4.9)
    bi = np.clip(((Zp - 3.8) / 0.135).astype(np.int32), 0, 1999)
    bn = G['board'][bi]
    bseam = np.mod(Zp - 3.8, 0.135) < 0.012
    grain = G['fur'][(ys.astype(np.int32) % 900), ((Xp * 40).astype(np.int32) % 1500)]
    pc = np.array([70, 66, 64.]) * (0.85 + 0.2 * bn[..., None]) * (0.9 + 0.2 * grain[..., None]) * np.where(bseam, 0.55, 1.0)[..., None]
    sill = m_p & (Zp > 4.93) & (np.abs(Xp) < 0.52)
    pc = np.where(sill[..., None], np.array([96, 84, 70.]), pc)
    # step down at the porch end
    Xs, Zs, ss_ = hit(-0.22)
    m_s = below & ~m_p & (Xs >= 4.9) & (Xs < 5.25) & (Zs > 3.6) & (Zs < 5.0)
    # fascia: the vertical face of the porch at Z=3.8
    sF = 3.8 - c[2]
    Yf = c[1] + sF * dy
    Xf = c[0] + sF * dx
    m_f = (Yf <= 0) & (Yf > -0.45) & (Xf > -7) & (Xf < 4.9)
    Xg2, Zg2, _ = hit(-0.45)
    m_g = below & (Zg2 < 3.8) & ~m_f
    rgb = np.zeros((H, W, 3), np.float32)
    a = np.zeros((H, W), np.float32)
    light = beam(Xp, np.zeros_like(Xp), Zp, t) * light_level(t)
    amb = ambient(t)
    pcl = pc * amb + WARM * light[..., None] * 0.62 * (pc / 70.0)
    rgb = np.where(m_p[..., None], pcl, rgb)
    rgb = np.where(m_s[..., None], np.array([58, 56, 56.]) * amb, rgb)
    rgb = np.where(m_f[..., None], np.array([30, 29, 32.]) * amb * (0.85 + 0.3 * G['fur'][(ys.astype(np.int32) % 900), (xs.astype(np.int32) % 1500)][..., None]), rgb)
    rgb = np.where(m_g[..., None], np.array([20, 24, 26.]) * amb, rgb)
    a = (m_p | m_s | m_f | m_g).astype(np.float32)
    # contact shadows of the dog and the person on the boards
    sh = np.zeros((H, W), np.float32)
    for (X0, Z0, rx, rz, k) in ((dogp['x'], dogp['z'], 0.42, 0.18, 0.55), (perq['X'] + 0.1, perq['Z'], 0.38, 0.16, 0.5)):
        sh = np.maximum(sh, k * np.exp(-((Xp - X0) ** 2) / (rx * rx) - ((Zp - Z0) ** 2) / (rz * rz)))
    rgb = rgb * (1 - sh * m_p)[..., None]
    return interior, yard, (rgb / 255 * a[..., None], a)


# ------------------------------------------------------------------------------------------------ door leaf and jamb reveal
def door_layer(c, t):
    im = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    th = math.radians(door_angle(t))
    hx, hz = 0.46, 5.05
    ex, ez = hx - 0.92 * math.cos(th), hz + 0.92 * math.sin(th)

    def P(X, Y, Zz):
        x, y, _ = project((X, Y, Zz), c)
        return (x * 2, y * 2)
    # left jamb's inner face (wall thickness), warm-lit from the room
    d.polygon([P(-0.46, 0, 5.0), P(-0.46, 0, 5.16), P(-0.46, 2.08, 5.16), P(-0.46, 2.08, 5.0)], fill=(150, 104, 66, 255))
    d.polygon([P(0.46, 0, 5.0), P(0.46, 0, 5.16), P(0.46, 2.08, 5.16), P(0.46, 2.08, 5.0)], fill=(96, 70, 50, 255))
    d.polygon([P(-0.46, 2.08, 5.0), P(0.46, 2.08, 5.0), P(0.46, 2.08, 5.16), P(-0.46, 2.08, 5.16)], fill=(80, 60, 46, 255))
    # the leaf (its outer face, in shadow), with two panels and a small lit pane
    lit = 0.6 + 0.4 * (1 - math.cos(th))
    d.polygon([P(hx, 0.01, hz), P(ex, 0.01, ez), P(ex, 2.05, ez), P(hx, 2.05, hz)], fill=(int(70 * lit), int(48 * lit), int(36 * lit), 255))

    def on_leaf(u, Y):
        return P(hx + (ex - hx) * u, Y, hz + (ez - hz) * u)
    for (u0, u1, y0, y1) in ((0.18, 0.82, 0.18, 0.9), (0.18, 0.82, 1.05, 1.4)):
        d.polygon([on_leaf(u0, y0), on_leaf(u1, y0), on_leaf(u1, y1), on_leaf(u0, y1)], fill=(int(58 * lit), int(40 * lit), int(30 * lit), 255))
    d.polygon([on_leaf(0.2, 1.52), on_leaf(0.8, 1.52), on_leaf(0.8, 1.9), on_leaf(0.2, 1.9)], fill=(190, 140, 90, 255))
    d.line([on_leaf(0.97, 0.01), on_leaf(0.97, 2.05)], fill=(40, 28, 22, 255), width=3)
    im = im.resize((W, H), Image.LANCZOS).convert('RGBa')
    return blur(im, blur_px(5.2, t))


# ------------------------------------------------------------------------------------------------ the cutouts, painted and lit
def shift(a, dx, dy):
    out = np.zeros_like(a)
    h, w = a.shape
    xs0, xs1 = max(0, dx), min(w, w + dx)
    ys0, ys1 = max(0, dy), min(h, h + dy)
    out[ys0:ys1, xs0:xs1] = a[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


def cutout_to_screen(x0, y0, rgb, a, t, zlayer):
    """paste a small premultiplied cutout into a full frame layer, then defocus it as its glass."""
    full_rgb = np.zeros((H, W, 3), np.float32)
    full_a = np.zeros((H, W), np.float32)
    h, w = a.shape
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(W, x0 + w), min(H, y0 + h)
    if X1 <= X0 or Y1 <= Y0:
        return full_rgb, full_a
    full_rgb[Y0:Y1, X0:X1] = rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    full_a[Y0:Y1, X0:X1] = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    r = blur_px(zlayer, t)
    if r > 0.6:
        img = Image.fromarray(np.dstack([np.clip(full_rgb, 0, 1) * 255, full_a * 255]).astype(np.uint8), 'RGBa')
        full_rgb, full_a = to_np(blur(img, r))
    return full_rgb, full_a


def dog_layer(p, c, t):
    # the replacement pieces, chosen and hinged for this frame (pieces.py); their cut edges and paint are their own
    x0, y0, tone, alpha, torso, headm, info = PIECES.render(p, c)
    SS = 2
    w, h = tone.size[0] // SS, tone.size[1] // SS
    A = np.asarray(alpha.resize((w, h), Image.BOX), np.float32) / 255
    T = np.asarray(tone.resize((w, h), Image.BOX), np.float32) / 160.0
    T = T / np.maximum(A, 1e-3)
    base = np.array([50, 42, 39.], np.float32) / 255
    col = base[None, None, :] * T[..., None]
    # light: the blue hour everywhere, the house's light where the dog stands in it (per pixel: half in, half out)
    zc = p['z'] - c[2]
    Xpx = c[0] + (np.arange(w, dtype=np.float32) + x0 - CX) * zc / F
    Ypx = c[1] - (np.arange(h, dtype=np.float32) + y0 - CY) * zc / F
    L = beam(Xpx[None, :], Ypx[:, None], np.float32(p['z'] + 0.05), t) * light_level(t)
    amb = np.array([0.66, 0.70, 0.86], np.float32) * ambient(t)
    lit = col * (amb[None, None, :] + L[..., None] * np.array([1.2, 0.85, 0.5], np.float32) * 0.75)
    # rims: warm on the edge towards the door, cool (moon, upper right) on the other
    dirx = -1 if p['x'] > 0.2 else 1
    rimw = A * (1 - shift(A, -3 * dirx, 1)) * np.clip(L * 1.6 + 0.12 * light_level(t), 0, 1)
    rimc = A * (1 - shift(A, -2, 2)) * 0.5
    lit = lit + rimw[..., None] * np.array([1.0, 0.72, 0.42]) * 0.75 + rimc[..., None] * np.array([0.62, 0.68, 0.82])
    rgb = np.clip(lit, 0, 1) * A[..., None]
    meas = measure_dog(p, c, x0, y0, A, torso, headm, w, h)
    meas.update(nose_px=[round(v, 1) for v in info['nose_px']], head_anchor_px=[round(float(v), 1) for v in info['head_anchor_px']],
                pieces=dict(body=info['body'], head=info['head'], view_body=int(info['choice']['kb']), view_head=int(info['choice']['kh'])))
    full = cutout_to_screen(x0, y0, rgb, A, t, p['z'])
    return full, meas


def measure_dog(p, c, x0, y0, A, torso, headm, w, h):
    tm = np.asarray(torso, np.float32) / 255
    hm = np.asarray(headm, np.float32) / 255
    yy, xx = np.mgrid[0:h, 0:w]
    tw = tm.sum() + 1e-6
    tcx, tcy = (tm * xx).sum() / tw + x0, (tm * yy).sum() / tw + y0
    hw = hm.sum() + 1e-6
    hcx, hcy = (hm * xx).sum() / hw + x0, (hm * yy).sum() / hw + y0
    t_rows = np.where(tm.max(1) > 0.5)[0]
    h_rows = np.where(hm.max(1) > 0.5)[0]
    a_cols = np.where(A.max(0) > 0.5)[0]
    a_rows = np.where(A.max(1) > 0.5)[0]
    xw = unproject_x(tcx, p['z'], c)
    left_x = unproject_x(a_cols.min() + x0, p['z'], c) if len(a_cols) else None
    right_x = unproject_x(a_cols.max() + x0, p['z'], c) if len(a_cols) else None
    # share of the dog's silhouette inside the door frame's span (X < 0.46)
    zc = p['z'] - c[2]
    Xpx = c[0] + (np.arange(w) + x0 - CX) * zc / F
    inside = float((A * (Xpx[None, :] < 0.46)).sum() / (A.sum() + 1e-6))
    return dict(torso_cx=round(float(tcx), 1), torso_cy=round(float(tcy), 1), head_cx=round(float(hcx), 1), head_cy=round(float(hcy), 1),
                torso_top=int(t_rows.min() + y0) if len(t_rows) else None, head_top=int(h_rows.min() + y0) if len(h_rows) else None,
                head_bottom=int(h_rows.max() + y0) if len(h_rows) else None,
                sil_w=int(len(a_cols)), sil_h=int(len(a_rows)), x_world=round(float(xw), 4),
                left_x=None if left_x is None else round(float(left_x), 3), right_x=None if right_x is None else round(float(right_x), 3),
                inside_frame=round(inside, 3), bbox=[int(x0), int(y0), int(w), int(h)])


def person_layer(t, c):
    x0, y0, tone, skin, al, q, hand_px = PERSON.render(t, c)
    SS = PERSON.SS
    w, h = tone.size[0] // SS, tone.size[1] // SS
    A = np.asarray(al.resize((w, h), Image.BOX), np.float32) / 255
    T = np.asarray(tone.resize((w, h), Image.BOX), np.float32) / 170 / np.maximum(A, 1e-3)
    S = np.asarray(skin.resize((w, h), Image.BOX), np.float32) / 255 / np.maximum(A, 1e-3)
    coat = np.array([54, 50, 58.]) / 255
    sk = np.array([150, 116, 98.]) / 255
    base = coat[None, None, :] * (1 - S[..., None]) + sk[None, None, :] * S[..., None]
    amb = np.array([0.6, 0.64, 0.8]) * ambient(t)
    col = base * T[..., None] * amb
    in_door = 1 - smooth(5.35, 5.9, t)
    # backlit in the doorway (a dark figure ringed with light); beside the door, the light on the side towards it
    rim_all = A * (1 - np.minimum.reduce([shift(A, 3, 0), shift(A, -3, 0), shift(A, 0, 3), shift(A, 0, -3)]))
    rim_r = A * (1 - shift(A, -3, 1))
    rim = rim_all * in_door * light_level(t) * 1.1 + rim_r * (1 - in_door) * 0.55 * light_level(t)
    col = col + rim[..., None] * np.array([1.0, 0.72, 0.42])
    rgb = np.clip(col, 0, 1) * A[..., None]
    full = cutout_to_screen(x0, y0, rgb, A, t, q['Z'])
    return full, q, hand_px


# ------------------------------------------------------------------------------------------------ one frame
def frame(i):
    t = i / FPS
    c = cam(t)
    p = G['dogP'][i]
    q = PERSON.pose(t)
    out = np.zeros((H, W, 3), np.float32)

    def lay(im):
        rgb, a = to_np(im)
        over(out, rgb, a)

    lay(place('sky', c, t))
    lay(place('trees_far', c, t, extra_blur=1.5))
    rgb, a = fog_layer(22.0, c, t, 0.55, 0.55, prof_far, kscale=20, seed_off=0.3, warmk=0)
    over(out, rgb, a)
    lay(place('trees_near', c, t))
    interior, yard, porch = floors(c, t, p, q)
    yrgb, ya = yard
    over(out, *[to_np(blur(Image.fromarray(np.dstack([yrgb * 255, ya * 255]).astype(np.uint8), 'RGBa'), blur_px(9, t)))][0])
    rgb, a = fog_layer(Z['fog_far'], c, t, 0.6, 0.6, prof_far, kscale=35, seed_off=0.6, warmk=0, ytop=3.5, rows_per_m=30)
    over(out, rgb, a)
    lay(place('interior_wall', c, t))
    irgb, ia = interior
    over(out, *to_np(blur(Image.fromarray(np.dstack([irgb * 255, ia * 255]).astype(np.uint8), 'RGBa'), blur_px(7.0, t))))
    lay(place('interior_near', c, t))
    # the warm haze of the room, just inside the door
    rgb, a = fog_layer(5.6, c, t, 0.28, 0.3, lambda X, Y, t_: 0.8 + 0 * X * Y, kscale=70, seed_off=0.8, warmk=1.6, src='fog_inner')
    over(out, rgb, a)
    lay(door_layer(c, t))
    lay(place('wall', c, t))
    prgb, pa = porch
    over(out, *to_np(blur(Image.fromarray(np.dstack([np.clip(prgb, 0, 1) * 255, pa * 255]).astype(np.uint8), 'RGBa'), blur_px(4.4, t))))
    rgb, a = fog_layer(4.88, c, t, 0.5, 0.55, prof_back, kscale=55, seed_off=0.1, src='fog_inner', rows_per_m=60)
    over(out, rgb, a)
    # the two cutouts, in depth order
    (drgb, da), meas = dog_layer(p, c, t)
    (qrgb, qa), q, hand_px = person_layer(t, c)
    if p['z'] > q['Z']:
        over(out, drgb, da); over(out, qrgb, qa)
    else:
        over(out, qrgb, qa); over(out, drgb, da)
    rgb, a = fog_layer(Z['fog_porch'], c, t, 0.75, 0.62, prof_porch, kscale=62, seed_off=0.45, ytop=1.55, rows_per_m=55)
    over(out, rgb, a)
    lay(place('posts', c, t))
    rgb, a = fog_layer(Z['fog_near'], c, t, 0.6, 0.7, prof_near, kscale=48, seed_off=0.7, ytop=0.75, rows_per_m=50)
    over(out, rgb, a)
    lay(place('leaves', c, t))
    lay(place('grass', c, t))
    # grade: vignette, the grain of the glass and film, a breath of exposure flicker
    vig = 1 - 0.32 * (((G['xs'] - CX) / W * 2) ** 2 * 0.6 + ((G['ys'] - 360) / H * 2) ** 2 * 0.8)
    rnd = np.random.default_rng(1000 + i)
    grain = rnd.normal(0, 0.018, (H // 2, W // 2)).astype(np.float32)
    grain = np.asarray(Image.fromarray(grain).resize((W, H), Image.BILINEAR))
    flick = 1 + 0.012 * math.sin(i * 1.7) * math.sin(i * 0.31)
    img = np.clip((out * vig[..., None] * flick + grain[..., None]) * 255, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(FRAMES, 's%04d.jpg' % i), quality=92)
    meas.update(i=i, t=round(t, 4), cam=[round(v, 4) for v in c], focus_z=round(focus_z(t), 3), atmosphere=atmosphere_state(t),
                hand_px=[round(float(v), 1) for v in hand_px], person=dict(X=round(q['X'], 3), Z=round(q['Z'], 3), sit=round(q['sit'], 3)))
    # silhouette contrast (a recorded proxy, not a verdict): mean luminance of the dog vs a ring around it
    bx, by, bw, bh = meas['bbox']
    lum = img.astype(np.float32).mean(2)
    m = da > 0.6
    ring = (blur(Image.fromarray((m * 255).astype(np.uint8)), 6) if False else None)
    if m.sum() > 10:
        dl = float(lum[m].mean())
        y0_, y1_ = max(0, by - 20), min(H, by + bh + 20)
        x0_, x1_ = max(0, bx - 20), min(W, bx + bw + 20)
        box = np.zeros_like(m); box[y0_:y1_, x0_:x1_] = True
        bg = box & (da < 0.05)
        meas['lum_dog'] = round(dl, 1)
        meas['lum_around'] = round(float(lum[bg].mean()), 1) if bg.sum() else None
    json.dump(meas, open(os.path.join(MEAS, '%04d.json' % i), 'w'))
    return i


def coat_texture():
    """grain of the archive dog's coat: pixels inside its SAM mask on frame 0, high-passed and tiled."""
    src = np.asarray(Image.open(os.path.join(KIT, 'archive-dog/frames/f000.jpg')).convert('L'), np.float32)
    masks = json.load(open(os.path.join(KIT, 'archive-dog/masks.json')))
    m = Image.new('L', (src.shape[1], src.shape[0]), 0)
    for poly in masks['0']:
        ImageDraw.Draw(m).polygon([tuple(v) for v in poly], fill=255)
    m = np.asarray(m) > 0
    ys, xs = np.where(m)
    crop = src[150 - 30:150 + 2, 150:200]  # the flank, inside the mask
    sm = np.asarray(Image.fromarray(crop.astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), np.float32)
    hp = (crop - sm) / 40.0
    tile = np.asarray(Image.fromarray(np.clip((hp + 1) * 127, 0, 255).astype(np.uint8)).resize((160, 104), Image.BICUBIC), np.float32) / 127 - 1
    tile = np.concatenate([tile, tile[:, ::-1]], 1)
    tile = np.concatenate([tile, tile[::-1]], 0)
    np.save(os.path.join(CACHE, 'coat_tex.npy'), np.clip(tile, -1, 1).astype(np.float32))
    return dict(frame='f000.jpg', crop=[150, 120, 200, 152], mask_pixels=int(m.sum()))


def main():
    os.makedirs(FRAMES, exist_ok=True)
    os.makedirs(MEAS, exist_ok=True)
    P = DOG.controller()
    ser = []
    for p in P:
        d = {k: v for k, v in p.items() if k != 'feet'}
        d['feet'] = {k: (v[0].tolist(), float(v[1]), bool(v[2])) for k, v in p['feet'].items()}
        ser.append(d)
    json.dump(ser, open(os.path.join(CACHE, 'dog_params.json'), 'w'))
    coat_texture()
    lib = PIECES.build_library(P, [cam(i / FPS) for i in range(N)])
    print('piece library:', len(lib), 'substitution pieces in use', flush=True)
    rng_ = range(N)
    for a in sys.argv[1:]:
        if a.startswith('--frames='):
            lo, hi = a.split('=')[1].split(':')
            rng_ = range(int(lo), int(hi))
        if a.startswith('--list='):
            rng_ = [int(v) for v in a.split('=')[1].split(',')]
    t0 = time.time()
    with Pool(4, initializer=init) as pool:
        for k, i in enumerate(pool.imap_unordered(frame, rng_, chunksize=4)):
            if k % 48 == 0:
                print('frame', i, '%.1fs' % (time.time() - t0), flush=True)
    print('done', len(rng_), 'frames in %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
