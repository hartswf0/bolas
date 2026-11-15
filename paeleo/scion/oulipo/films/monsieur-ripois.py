"""Monsieur Ripois — an interested confession at a lost-property window.
The visitor claims the envelope came back untouched; the flashback (as told) hides one gesture;
the clerk's receipt, a silent shake and the sweeper's tag let him decide otherwise."""
import math
from PIL import Image, ImageOps, ImageDraw, ImageFilter
from kit_cinema_b import *
from kit_cinema_b import _Draw, _Image, _Filter

SC = Score([(0, 3.0, "title"), (3.0, 14.0, "present1"), (14.0, 24.0, "flashback"), (24.0, 27.0, "shake"),
            (27.0, 30.0, "receipt"), (30.0, 33.0, "tag"), (33.0, 37.5, "verdict"), (37.5, 43.0, "ledger")])
film = PhotoFilm("monsieur-ripois", seconds=SC.total, seed=5)
film.poster_at = 19.6

V_COAT, C_COAT = (92, 70, 62), (70, 84, 96)
CAPS = [  # (start, end, speaker, line)
    (4.0, 7.0, "VISITOR", "I'm returning your envelope. Exactly as you lent it."),
    (7.2, 10.6, "VISITOR", "Sealed. I sat on the bench, the bell rang, I left."),
    (11.0, 13.8, "VISITOR", "Let me tell you how it was."),
    (24.6, 26.9, "CLERK", "When I lent it, it rattled."),
    (33.3, 35.6, "VISITOR", "…The bench was damp. It must have slipped out."),
    (35.8, 37.4, "CLERK", "Then I'll write what it is."),
]
FB_CUT = 19.4   # the splice in the flashback that hides the gesture


# ---- look: a glossy black-and-white studio still -------------------------
LOOK = {"bw": True, "gamma": 1.12, "contrast": 0.6, "lift": 0.06, "gain": 0.96, "halation": (0.3, 0.75, 7),
        "soft": 0.5, "grain": (0.04, 1.1), "vignette": 0.3}
DREAM = {"bw": True, "gamma": 0.85, "contrast": 0.2, "lift": 0.16, "gain": 0.98, "halation": (0.75, 0.55, 16),
         "soft": 1.6, "grain": (0.06, 1.6), "vignette": 0.8}
KEY_LIGHT = (-0.6, -0.55, 0.58)   # studio key from the upper left


def hash2(i, j, seed=0.0):
    v = np.sin(i * 12.9898 + j * 78.233 + seed) * 43758.5453
    return v - np.floor(v)


def leopard(wx, wy):
    cs = 17.0
    i, j = np.floor(wx / cs), np.floor(wy / (cs * 0.8))
    cx = (i + 0.25 + 0.5 * hash2(i, j)) * cs
    cy = (j + 0.25 + 0.5 * hash2(i, j, 3.1)) * cs * 0.8
    d = np.hypot((wx - cx) / (0.42 * cs), (wy - cy) / (0.36 * cs)) + 0.25 * value_noise(wx, wy, 6, 2, 2)
    ring = (d > 0.5) & (d < 0.92) & (value_noise(wx * 1.3, wy * 1.3, 4, 9, 1) > -0.35)
    centre = d <= 0.45
    base = 0.78 + 0.06 * value_noise(wx, wy, 30, 4)
    return np.where(ring, 0.16, np.where(centre, base * 0.8, base))


def pinstripe(wx, wy):
    st = (np.abs(((wx - wy * 0.05) % 9) - 4.5) < 0.45)
    return np.where(st, 0.34, 0.1) + 0.02 * value_noise(wx, wy, 12, 7)


def room_background(k):
    """A soft-focus salon behind the counter: panelling, a lamp, chair backs, a mirror."""
    ph = Photo(light=KEY_LIGHT)
    ph.ground(0.5, 0.3)
    ph.field(lambda wx, wy: 0.5 + 0.06 * np.sin(wx / 50) * (wy < 300) + 0.04 * value_noise(wx, wy, 80, 1), alpha=0.9)
    for x in range(40, 960, 160):
        ph.rect(x, 30, x + 120, 250, 0.62, blur=2, grad=((x, 30), 1.1, (x + 120, 250), 0.75))
        ph.rect(x + 10, 40, x + 110, 240, 0.48, blur=2)
    ph.rect(0, 250, 960, 262, 0.75, blur=2)
    ph.poly([(800, 20), (900, 20), (930, 120), (770, 120)], 0.95, blur=3)   # lamp shade
    ph.capsule((850, 120), (850, 300), 6, 6, 0.4)
    for x in (120, 300, 460):  # chair backs, ornate rails
        ph.capsule((x, 150), (x, 320), 7, 7, 0.82, spec=0.4)
        ph.capsule((x + 70, 150), (x + 70, 320), 7, 7, 0.82, spec=0.4)
        ph.capsule((x, 160), (x + 70, 160), 7, 7, 0.82, spec=0.4)
        for kk in range(4):
            ph.capsule((x + 8 + kk * 18, 170), (x + 8 + kk * 18, 240), 3, 3, 0.7)
    img = ph.image().filter(_Filter.GaussianBlur(7))
    return np.asarray(img, np.float32) / 255.0


_ROOM = None


def hand(ph, x, y, s=1.0, angle=0.0, skin=0.78, curl=0.3):
    ca, sa = math.cos(angle), math.sin(angle)

    def R(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    ph.ellipsoid(*R(0, 0), 16 * s, 12 * s, skin, amb=0.3, spec=0.1)
    for k, dy in enumerate((-8, -2.5, 3, 8)):
        L = 20 - abs(k - 1.5) * 3
        ph.capsule(R(10, dy), R(10 + L * (1 - curl * 0.5), dy + L * curl), 3.4 * s, 2.9 * s, skin, amb=0.3, spec=0.1)
    ph.capsule(R(-4, -10), R(8, -20), 4 * s, 3.2 * s, skin, amb=0.3)


FACE_BUMPS = [(0.6, 0.12, 0.09, 0.24, 0.32), (0.68, 0.3, 0.08, 0.07, 0.22),        # nose bridge, tip
              (0.34, -0.2, 0.32, 0.07, 0.1), (0.4, -0.05, 0.12, 0.07, -0.12), (0.03, -0.05, 0.1, 0.07, -0.1),  # brow, sockets
              (0.3, 0.22, 0.2, 0.15, 0.1), (0.5, 0.52, 0.12, 0.04, 0.06), (0.48, 0.6, 0.11, 0.045, 0.07),     # cheek, lips
              (0.36, 0.86, 0.18, 0.12, 0.12), (-0.34, 0.06, 0.08, 0.16, 0.12)]                                 # chin, ear


def face_albedo(who, gaze, mouth):
    lipv = 0.45 if who == "clerk" else 0.8

    def fn(nx, ny, alb):
        a = alb.copy()
        for ex, sc in ((0.4, 1.0), (0.04, 0.7)):
            ey = -0.05
            white = ((nx - ex) / (0.1 * sc)) ** 2 + ((ny - ey) / 0.04) ** 2 < 1
            iris = ((nx - ex - (0.03 + 0.04 * gaze) * sc) / (0.04 * sc)) ** 2 + ((ny - ey) / 0.04) ** 2 < 1
            lid = (np.abs(ny - (ey - 0.04)) < 0.014) & (np.abs(nx - ex) < 0.11 * sc)
            bcurve = -0.2 - 0.035 * (1 - ((nx - ex) / (0.15 * sc)) ** 2)
            brow = (np.abs(ny - bcurve) < (0.03 if who == "visitor" else 0.018)) & (np.abs(nx - ex) < 0.15 * sc)
            a = np.where(white[..., None], 0.85, a)
            a = np.where((white & iris)[..., None], 0.07, a)
            a = np.where(lid[..., None], 0.08, a)
            a = np.where(brow[..., None], a * 0.25, a)
        lips = ((nx - 0.47) / 0.15) ** 2 + ((ny - 0.56) / (0.065 + 0.02 * mouth)) ** 2 < 1
        a = np.where(lips[..., None], a * lipv, a)
        line = (np.abs(ny - 0.555) < 0.008 + 0.02 * mouth) & (np.abs(nx - 0.47) < 0.14)
        a = np.where(line[..., None], 0.08, a)
        return a
    return fn


def strands(base, freq=0.9, seed=0):
    def fn(wx, wy):
        s_ = 0.5 + 0.5 * np.sin(wx * freq * 0.35 + wy * freq + 3 * value_noise(wx, wy, 25, seed, 2))
        return base * (0.75 + 0.5 * s_)
    return fn


def portrait(ph, cx, cy, r, f, who, gaze=0.0, lean=0.0, mouth=0.0):
    """Head and neck as smooth height fields, lit by a studio key; glossy hair; an earring for the clerk."""
    skin = 0.82 if who == "clerk" else 0.7
    P = lambda nx, ny: (cx + nx * r * f, cy + ny * r)
    pillow(ph, [P(-0.35, 0.5), P(0.25, 0.6), P(0.3, 1.9), P(-0.5, 1.9)], skin, radius=0.3 * r, amb=0.2, spec=0.08)
    ph.shadow([P(-0.3, 0.7), P(0.35, 0.75), P(0.25, 1.05), P(-0.35, 0.95)], 0.55, 0.12 * r)
    if who == "visitor":
        pillow(ph, [P(-0.85, -0.25), P(-0.5, -0.95), P(0.1, -1.12), P(0.6, -0.92), P(0.72, -0.62), P(0.35, -0.6), P(-0.1, -0.5), P(-0.4, -0.1), P(-0.55, 0.3), P(-0.8, 0.2)],
               strands(0.1, seed=1), radius=0.25 * r, amb=0.15, spec=0.55, shine=9)
    else:
        pillow(ph, [P(-0.95, -0.1), P(-0.95, -0.75), P(-0.5, -1.15), P(0.1, -1.18), P(0.55, -0.95), P(0.62, -0.6), P(0.2, -0.62), P(-0.3, -0.4), P(-0.5, 0.1), P(-0.8, 0.3)],
               lambda wx, wy: 0.09 * (0.7 + 0.6 * (0.5 + 0.5 * np.sin(np.hypot(wx % 22 - 11, wy % 22 - 11) * 0.9))), radius=0.22 * r, amb=0.15, spec=0.5, shine=8)
    face_volume(ph, cx, cy, r, f, skin, FACE_BUMPS, albedo_fn=face_albedo(who, gaze, mouth))
    if who == "visitor":
        pillow(ph, [P(-0.6, -0.55), P(-0.1, -0.85), P(0.55, -0.88), P(0.6, -0.62), P(0.1, -0.58), P(-0.35, -0.45), P(-0.45, -0.05), P(-0.62, -0.1)],
               strands(0.1, seed=2), radius=0.12 * r, amb=0.15, spec=0.6, shine=9)
    else:
        ex, ey = P(-0.34, 0.3)
        ph.capsule((ex, ey), (ex, ey + 0.2 * r), 0.012 * r, 0.012 * r, 0.9)
        for kk in range(7):
            ph.ellipsoid(ex + (kk - 3) * 0.03 * r, ey + 0.24 * r + (abs(kk - 3) * -0.025 + 0.06) * r, 0.022 * r, 0.05 * r, 0.95, spec=1.0, amb=0.3)



def visitor_body(ph, x, y, r, f):
    """Dark pinstripe suit, white shirt, dark tie, pocket square — from the chest up."""
    pillow(ph, [(x - 2.3 * r, H + 20), (x - 1.9 * r, y + 1.9 * r), (x - 1.2 * r, y + 1.4 * r), (x + 0.1 * r, y + 1.25 * r),
                (x + 1.3 * r, y + 1.45 * r), (x + 1.9 * r, y + 2.0 * r), (x + 2.1 * r, H + 20)], pinstripe, radius=0.6 * r, amb=0.3, spec=0.1)
    pillow(ph, [(x - 0.1 * r, y + 1.3 * r), (x + 0.6 * r, y + 1.32 * r), (x + 0.35 * r, y + 2.9 * r)], 0.93, radius=0.1 * r, amb=0.45)
    pillow(ph, [(x + 0.14 * r, y + 1.4 * r), (x + 0.36 * r, y + 1.4 * r), (x + 0.33 * r, y + 2.9 * r), (x + 0.18 * r, y + 2.85 * r)], 0.06, radius=0.06 * r, spec=0.3)
    pillow(ph, [(x - 0.2 * r, y + 1.32 * r), (x + 0.15 * r, y + 2.8 * r), (x - 0.05 * r, y + 3.6 * r), (x - 0.6 * r, y + 1.55 * r)], pinstripe, radius=0.1 * r, amb=0.45, spec=0.15)
    pillow(ph, [(x + 0.65 * r, y + 1.35 * r), (x + 0.4 * r, y + 2.8 * r), (x + 0.6 * r, y + 3.6 * r), (x + 1.05 * r, y + 1.6 * r)], pinstripe, radius=0.1 * r, amb=0.45, spec=0.15)
    pillow(ph, [(x - 1.25 * r, y + 2.45 * r), (x - 0.82 * r, y + 2.38 * r), (x - 0.86 * r, y + 2.6 * r), (x - 1.2 * r, y + 2.65 * r)], 0.95, radius=0.05 * r, amb=0.5)


def clerk_body(ph, x, y, r, f):
    """Bare shoulders, a dark velvet off-shoulder dress, a pale drape."""
    skin = 0.82
    pillow(ph, [(x - 2.0 * r, H + 20), (x - 1.85 * r, y + 2.3 * r), (x - 1.2 * r, y + 1.85 * r), (x - 0.4 * r, y + 1.65 * r), (x + 0.4 * r, y + 1.7 * r),
                (x + 1.2 * r, y + 1.9 * r), (x + 1.7 * r, y + 2.4 * r), (x + 1.8 * r, H + 20)], skin, radius=0.55 * r, amb=0.25, spec=0.18)
    ph.shadow([(x - 0.4 * r, y + 1.95 * r), (x + 0.5 * r, y + 2.0 * r), (x + 0.4 * r, y + 2.1 * r), (x - 0.4 * r, y + 2.05 * r)], 0.35, 0.05 * r)
    pillow(ph, [(x - 2.0 * r, H + 20), (x - 1.75 * r, y + 2.75 * r), (x - 0.5 * r, y + 2.5 * r), (x + 0.5 * r, y + 2.55 * r), (x + 1.6 * r, y + 2.8 * r), (x + 1.8 * r, H + 20)],
           0.1, radius=0.5 * r, amb=0.3, spec=0.25, shine=6)
    pillow(ph, [(x + 0.3 * r, y + 2.7 * r), (x + 1.7 * r, y + 2.8 * r), (x + 2.4 * r, H + 20), (x + 0.7 * r, H + 20)],
           lambda wx, wy: 0.85 + 0.08 * np.sin(wx * 0.15 + wy * 0.05), radius=0.4 * r, amb=0.3, spec=0.1)


def two_shot(t, k, v_lean=0.0, c_lean=0.0, c_gaze=0.0, v_gaze=0.0, env=None, stamp=False, receipt=None, key=False, c_hand=None, v_mouth=0.0):
    global _ROOM
    if _ROOM is None:
        _ROOM = room_background(0)
    ph = Photo(light=KEY_LIGHT)
    ph.a[:] = _ROOM
    # leopard upholstery behind the clerk
    ph.poly([(560, 120), (960, 90), (960, 540), (600, 540)], leopard, blur=1.5, grad=((560, 0), 0.6, (960, 0), 1.0))
    vx, vy, r = 300 + v_lean * 20, 190, 72
    cxx, cyy = 680 - c_lean * 24, 205
    visitor_body(ph, vx, vy, r, 1)
    portrait(ph, vx, vy, r, 1, "visitor", gaze=v_gaze, mouth=v_mouth)
    clerk_body(ph, cxx, cyy, 66, -1)
    portrait(ph, cxx, cyy, 66, -1, "clerk", gaze=c_gaze)
    # the counter's polished edge
    ph.rect(0, 440, W, H, 0.16, grad=((0, 440), 1.4, (0, H), 0.6))
    ph.rect(0, 436, W, 446, 0.85, blur=1.5)
    if env:
        ex, ey, ang, op = env
        photo_envelope(ph, ex, ey, 150, 96, open_=op, angle=ang, shade=0.35)
    if receipt:
        rx, ry = receipt
        ph.shadow([(rx - 60, ry - 26), (rx + 70, ry - 26), (rx + 70, ry + 34), (rx - 60, ry + 34)], 0.4, 4)
        ph.rect(rx - 64, ry - 30, rx + 64, ry + 30, 0.92, grad=((rx - 64, 0), 1.0, (rx + 64, 0), 0.8))
    if key:
        photo_key(ph, 820, 480, 1.6, angle=0.15, col=0.75, spec=0.9)
    if c_hand:
        hx, hy, ha = c_hand
        hand(ph, hx, hy, 1.4, ha, 0.8)
    img = finish(ph, LOOK, k)
    if receipt:
        ink = ink_on(img)
        ink.text((receipt[0], receipt[1] - 14), "No. 0412", "mono", 13, (40, 40, 40), anchor="mm")
        if stamp:
            ink.d.rectangle([receipt[0] - 52, receipt[1], receipt[0] + 52, receipt[1] + 22], outline=(30, 30, 30, 220), width=2)
            ink.text((receipt[0], receipt[1] + 11), "OPENED", "mono", 15, (20, 20, 20), anchor="mm")
        img = ink.img
    return img


def present1(local, t, k):
    lean = ease(local, 6.0, 7.5) * 0.8 - ease(local, 9.5, 10.5) * 0.4
    f = ease(local, 0.7, 1.8)
    env = (lerp(400, 520, f), lerp(330, 470, f), lerp(-0.15, 0.05, f), 0.0)
    talk = 0.5 + 0.5 * math.sin(t * 17) if any(c0 <= t < c1 and w == "VISITOR" for c0, c1, w, _ in CAPS) else 0.0
    return two_shot(t, k, v_lean=0.3 * ease(local, 0.5, 1.5), c_lean=lean, c_gaze=0.2 if local > 7.6 else -0.6, env=env, v_mouth=talk)


def flashback(local, t, k):
    ph = Photo(light=(0.4, -0.7, 0.6))
    ph.ground(0.62, 0.74)
    ph.rect(0, 330, W, H, 0.7, grad=((0, 330), 0.85, (0, H), 1.05))
    ph.field(lambda wx, wy: 0.04 * value_noise(wx, wy, 50, 2), mode="add")
    for xx in (-200, 120, 1100, 1500):
        ph.stroke([(xx, H), lerp2((xx, H), (595, 270), 0.75)], 2, 0.5, alpha=0.4)
    # closed service door
    ph.rect(770, 160, 870, 330, 0.25, grad=((770, 160), 0.9, (870, 330), 1.2))
    ph.ellipsoid(785, 250, 4, 4, 0.9, spec=0.8)
    # station clock: jumps at the splice
    clock_min = 3 + 10 / 60 + local / 60 if t < FB_CUT else 4 + 40 / 60 + (t - FB_CUT) / 60
    ph.capsule((150, 70), (150, 110), 2, 2, 0.3)
    ph.ellipsoid(150, 150, 40, 40, 0.95, amb=0.7)
    hrs = 12 + clock_min / 60
    for a, ln, wd in ((2 * math.pi * (hrs / 12) - math.pi / 2, 0.5, 4), (2 * math.pi * (hrs % 1) - math.pi / 2, 0.8, 2.5)):
        ph.stroke([(150, 150), (150 + math.cos(a) * 40 * ln, 150 + math.sin(a) * 40 * ln)], wd, 0.05)
    # bell
    sw = math.sin((local - 2.8) * 14) * 0.5 * (1 - ramp(local, 2.8, 4.6)) if 2.8 < local < 4.6 else 0.0
    ca, sa = math.cos(sw), math.sin(sw)
    shape = [(-7, 0), (7, 0), (12, 20), (22, 32), (-22, 32), (-12, 20)]
    ph.poly([(620 + px * ca - py * sa, 92 + px * sa + py * ca) for px, py in shape], 0.55, grad=((598, 0), 1.3, (642, 0), 0.6))
    # bench
    ph.shadow([(300, 362), (560, 362), (520, 380), (260, 380)], 0.4, 6)
    for yy in (312, 284):
        ph.capsule((315, yy), (545, yy), 5, 5, 0.5)
    for xx in (330, 530):
        ph.capsule((xx, 312), (xx, 362), 3, 3, 0.3)
    outfit = {"skin": 0.7, "top": pinstripe, "bottom": 0.12, "hair": 0.06, "hat": "brim", "hat_col": 0.12, "shoes": 0.05}
    if t < FB_CUT:
        sk = skeleton(410, 362, 1.05, "sit", 0, 1, arm=60)
        person(ph, sk, outfit)
        h = sk["arms"][0][1]
        photo_envelope(ph, h[0] + 8, h[1] - 6, 46, 30)
    else:
        photo_envelope(ph, 440, 302, 46, 30)
        wx = lerp(470, 1010, ease(t, FB_CUT + 0.3, 23.8))
        sk = skeleton(wx, 372, 1.05, "walk", wx / 70, 1)
        cast_shadow(ph, sk, dx=-0.5, dy=0.1, strength=0.3)
        person(ph, sk, outfit)
    img = finish(ph, DREAM, k)
    ink = ink_on(img)
    ink.text((30, 26), "AS TOLD · the visitor's account · no independent witness", "mono", 13, (255, 255, 255))
    if FB_CUT <= t < FB_CUT + 2.0:
        ink.text((150, 214), "the clock skips 90 s", "mono", 15, (255, 255, 255), anchor="mm", alpha=int(255 * (1 - ramp(t, FB_CUT + 1.4, FB_CUT + 2.0))))
    img = ink.img
    if FB_CUT <= t < FB_CUT + 0.09:
        img = _Image.new("RGB", img.size, (245, 245, 240))
    return img


def shake(local, t, k):
    """Close on the clerk: the envelope held up by her ear, listening for the rattle."""
    global _ROOM
    if _ROOM is None:
        _ROOM = room_background(0)
    ph = Photo(light=KEY_LIGHT)
    ph.a[:] = _ROOM
    ph.poly([(300, 0), (960, 0), (960, 540), (360, 540)], leopard, blur=1.5, grad=((300, 0), 0.55, (960, 0), 1.0))
    cx, cy, r = 560, 230, 118
    clerk_body(ph, cx, cy, r, -1)
    portrait(ph, cx, cy, r, -1, "clerk", gaze=0.6)
    j = math.sin(local * 40) * 6
    ex, ey = cx + 1.25 * r, cy + 0.1 * r + j
    photo_envelope(ph, ex, ey, 170, 110, angle=-1.2 + j * 0.01, shade=0.35)
    hand(ph, ex - 10, ey + 50, 2.0, -1.9, 0.8, curl=0.5)
    img = finish(ph, LOOK, k)
    ink = ink_on(img)
    ink.text((ex, 40), "· no rattle ·", "mono", 15, (255, 255, 255), anchor="mm", alpha=int(255 * ramp(local, 0.4, 0.8)))
    return ink.img


def paper_insert(title, rows, highlight, k, key=False):
    ph = Photo(light=(-0.4, -0.7, 0.6))
    ph.ground(0.14, 0.06)
    ph.field(lambda wx, wy: 0.05 * np.sin(wx / 9 + 4 * value_noise(wx, wy, 90, 3)) + 0.03, mode="add")  # wood grain
    ph.light_patch([(200, 40), (760, 40), (820, 500), (140, 500)], 0.15, 60)
    ph.shadow([(236, 96), (756, 96), (756, 486), (236, 486)], 0.6, 10)
    ph.poly([(220, 80), (740, 84), (736, 470), (224, 466)], 0.93, blur=0.8, grad=((220, 80), 1.02, (740, 470), 0.78))
    if key:
        photo_key(ph, 560, 420, 2.2, angle=-0.2, col=0.72, spec=1.0)
    img = finish(ph, LOOK, k)
    ink = ink_on(img)
    ink.text((250, 110), title, "mono", 15, (30, 30, 30))
    for i, s in enumerate(rows):
        y = 160 + i * 46
        ink.text((250, y), s, "mono", 20, (10, 10, 10) if i == highlight else (70, 70, 70))
        ink.d.line([(250, y + 32), (710, y + 32)], fill=(150, 150, 150, 200), width=1)
    if highlight is not None:
        y = 160 + highlight * 46
        ink.d.line([(248, y + 28), (560, y + 28)], fill=(20, 20, 20, 255), width=2)
    return ink.img


def verdict(local, t, k):
    stamping = local > 2.9
    hy = 470 - (22 * abs(math.sin(local * 18)) if stamping else 0)
    return two_shot(t, k, c_gaze=1.0 if 0.2 < local < 2.6 else 0.2, v_gaze=-0.2, receipt=(560, 478), stamp=stamping and local > 3.1,
                    key=True, c_hand=(620, hy, -1.6) if stamping else None, v_mouth=0.5 + 0.5 * math.sin(t * 17) if local < 2.4 else 0)


def ledger(k):
    ph = Photo()
    ph.ground(0.04)
    img = finish(ph, {"bw": True, "grain": (0.04, 1.2)}, k)
    ink = ink_on(img)
    WH, GR = (244, 242, 236), (160, 158, 150)
    ink.text((W / 2, 46), "CLAIM / EVIDENCE LEDGER · both records survive", "mono", 15, WH, anchor="mm")
    rows = [("C1", "claim, spoken", "“sealed, exactly as you lent it”", "visitor"),
            ("E2", "flashback", "sealed on the bench; clock skips 90 s", "as told · subjective"),
            ("E3", "receipt 0412", "contents: 1 brass key, rattles", "clerk's record"),
            ("E4", "the shake", "paper only, no rattle", "heard"),
            ("E5", "sweeper's tag", "12:04 · key found on bench 1", "independent"),
            ("D1", "decision", "stamps OPENED, keeps the key", "listener")]
    for i, (a1, kind, what, src) in enumerate(rows):
        y = 100 + i * 58
        ink.text((70, y), a1, "mono", 20, WH)
        ink.text((130, y), kind, "mono", 16, GR)
        ink.text((300, y - 4), what, "serif", 26, WH)
        ink.text((900, y), src, "mono", 13, GR, anchor="ra")
        ink.d.line([(60, y + 40), (900, y + 40)], fill=(70, 70, 70, 255), width=1)
    ink.text((W / 2, 480), "the hidden gesture: opening the envelope and leaving the key", "mono", 13, GR, anchor="mm")
    return ink.img


@film.picture
def frame(t, k):
    name, local, a, b = SC.at(t)
    if name == "title":
        img = photo_card("AFTER MONSIEUR RIPOIS · CLÉMENT / QUENEAU 1954", "The return, as told", "a visitor, a clerk, one envelope", k=k)
    elif name == "present1":
        img = present1(local, t, k)
    elif name == "flashback":
        img = flashback(local, t, k)
    elif name == "shake":
        img = shake(local, t, k)
    elif name == "receipt":
        img = paper_insert("LOST PROPERTY · RECEIPT No. 0412",
                           ["issued      11:50", "item        1 sealed envelope", "contents    1 brass key", "note        rattles when shaken"], 2, k)
    elif name == "tag":
        img = paper_insert("SWEEPER'S TAG · PLATFORM 1",
                           ["time        12:04", "place       bench, platform 1", "found       1 brass key", "envelope    none seen"], 2, k, key=True)
    elif name == "verdict":
        img = verdict(local, t, k)
    else:
        img = ledger(k)
    for c0, c1, who, line in CAPS:
        if c0 <= t < c1:
            subtitle(img, line, who=who.title(), size=24)
    if name in ("title", "ledger", "flashback", "shake"):
        f = min(1.0, (t - a) / 0.4, (b - t) / 0.4)
        img = fade_img(img, f)
    return img


@film.sound
def sound(mix):
    T = SC.total
    mix.room(3, 11, 0.025)
    mix.room(24, 13.5, 0.025)
    for k in range(int(3 * 1), int(37 * 1)):
        if not 14 <= k < 24:
            mix.click(k, 0.04, -0.6, 2500, 0.015)   # office clock
    for c0, c1, who, line in CAPS:
        mix.murmur(c0 + 0.1, c1 - c0 - 0.3, 0.08, 135 if who == "VISITOR" else 102, -0.3 if who == "VISITOR" else 0.3, seed=int(c0 * 10))
    # envelope slides under the grille
    mix.add(mix.band(mix.noise(1.0), 1500, 6000) * np.hanning(int(RATE)) * 0.3, 3.7, 0.5, 0.1)
    # flashback: thinner, echoing
    mix.whoosh(13.8, 0.8, 0.12)
    mix.wind(14, 10, 0.05)
    mix.bell(14 + 2.8, 587, 3.2, 0.22, 0.3)
    mix.click(FB_CUT, 0.3, 0, 8000, 0.01)  # the splice
    mix.steps(FB_CUT + 0.3, 23.8, 0.46, 0.15, "stone", -0.2, 0.8)
    mix.whoosh(23.7, 0.8, 0.12)
    # the shake: paper only — no rattle
    for k in range(5):
        x = mix.band(mix.noise(0.12), 1200, 7000) * np.hanning(int(0.12 * RATE))
        mix.add(x, 24.4 + k * 0.32, 0.35, 0.3)
    # the receipt insert recalls the rattle it should have made
    for k in range(4):
        mix.click(27.6 + k * 0.28, 0.16, 0.2, 9000, 0.02)
        mix.click(27.62 + k * 0.28, 0.1, 0.25, 6000, 0.02)
    mix.click(31.0, 0.3, 0.0, 8000)   # key laid down
    mix.click(31.03, 0.2, 0.0, 9500)
    for k in range(3):
        mix.thud(36.4 + k * 0.33, 120, 0.3, 0.3, 0.15)  # stamp
    mix.bell(37.6, 440, 3.5, 0.1)
    mix.reverb(0.12, 1.0)


if __name__ == "__main__":
    film.render()
