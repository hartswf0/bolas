"""Renzo e Luciana — two co-workers, one overlapping break, one watched doorway.
CUT 1 plays the original shift; CUT 2 moves Bruno's bell to 12:03 and the safe window closes."""
import math
from kit_cinema_b import *
from kit_cinema_b import _Draw

S_PER_MIN = 5.0
CUT = 26.5            # seconds per cut; clock runs 11:59:42 .. 12:05:00
PRE = 1.5             # local seconds before 12:00
SC = Score([(0, 3.0, "title"), (3.0, 7.5, "rule"), (7.5, 7.5 + CUT, "cut1"), (7.5 + CUT, 10.0 + CUT, "card2"),
            (10.0 + CUT, 10.0 + 2 * CUT, "cut2"), (10.0 + 2 * CUT, 17.0 + 2 * CUT, "ledger")])
film = PhotoFilm("renzo-e-luciana", seconds=SC.total, seed=3)
film.poster_at = SC.start("cut1") + PRE + 2.0 * S_PER_MIN

FLOOR = 470
DOOR_X = 600          # partition wall with the doorway the supervisor watches
ADA_HOME, BRUNO_HOME = 165, 350
BENCH_X = 790
ADA_COAT, BRUNO_COAT = (150, 66, 60), (66, 88, 118)

# ---- schedules (minutes after 12:00) ------------------------------------
SCHED = {
    "cut1": {"ada": (0, 3), "bruno": (0, 4), "unwatched": (1, 4), "window": (1, 3)},
    "cut2": {"ada": (0, 3), "bruno": (3, 7), "unwatched": (1, 4), "window": None},
}
# actor x keyframes (minute, x)
PATHS = {
    "cut1": {
        "ada": [(-9, ADA_HOME), (1.0, ADA_HOME), (1.6, BENCH_X - 40), (2.4, BENCH_X - 40), (3.0, ADA_HOME), (9, ADA_HOME)],
        "bruno": [(-9, BRUNO_HOME), (1.15, BRUNO_HOME), (1.7, BENCH_X + 40), (3.45, BENCH_X + 40), (3.9, BRUNO_HOME), (9, BRUNO_HOME)],
    },
    "cut2": {
        "ada": [(-9, ADA_HOME), (1.0, ADA_HOME), (1.6, BENCH_X - 40), (2.9, BENCH_X - 40), (3.5, ADA_HOME), (9, ADA_HOME)],
        "bruno": [(-9, BRUNO_HOME), (3.0, BRUNO_HOME), (3.55, BENCH_X + 10), (9, BENCH_X + 10)],
    },
}
# supervisor gaze: (from, to, target)
GAZE = {
    "cut1": [(-9, 1, "door"), (1, 4, "ledger"), (4, 9, "door")],
    "cut2": [(-9, 1, "door"), (1, 3.2, "ledger"), (3.2, 3.95, "floor"), (3.95, 9, "door")],
}
CAPS = {
    "cut1": [(1.75, 2.05, "ADA", "For us. Open it."), (2.15, 2.4, "BRUNO", "Third floor, over the canal?"),
             (2.4, 2.65, "ADA", "Sunday. Don't be early."), (3.45, 3.8, "", "(the doorway is still unwatched)")],
    "cut2": [(1.8, 2.3, "ADA", "(where is he?)"), (2.35, 2.8, "BRUNO", "(stamping — his bell has not rung)"),
             (2.9, 3.15, "", "she leaves the sealed envelope on the bench"), (3.18, 3.42, "ADA", "Bench."),
             (3.5, 3.9, "SUPERVISOR", "Late from break, Ada. Noted."), (4.0, 4.6, "", "he finds the brass key alone")],
}


def path_x(keys, m):
    for (m0, x0), (m1, x1) in zip(keys, keys[1:]):
        if m0 <= m < m1:
            f = (m - m0) / (m1 - m0)
            return lerp(x0, x1, f), (x1 - x0) / (m1 - m0)
    return keys[-1][1], 0.0


def clock_str(m):
    secs = int(round(m * 60))
    hh, mm, ss = 12, 0, 0
    total = 12 * 3600 + secs
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def gaze_at(cut, m):
    for a, b, g in GAZE[cut]:
        if a <= m < b:
            return g
    return "door"


# ---- drawing ------------------------------------------------------------

# ---- look: a sunlit 1960s black-and-white photograph ---------------------
LOOK = {"bw": True, "gamma": 1.05, "contrast": 0.55, "lift": 0.03, "gain": 0.97, "halation": (0.35, 0.72, 9),
        "soft": 0.6, "grain": (0.055, 1.3), "vignette": 0.35}
LIGHT = (0.62, -0.62, 0.48)          # hard sun from the terrace, high on the right
WALL_BASE = 400
OUT_AMT = 0.55                        # interior is this much darker than the terrace
ADA = {"skin": 0.70, "top": lambda wx, wy: np.where(((wx * 0.9 + wy * 0.25) // 7) % 2 == 0, 0.93, 0.16),
       "bottom": lambda wx, wy: np.where(((wx * 0.9 + wy * 0.25) // 7) % 2 == 0, 0.93, 0.16), "skirt": True,
       "legs": 0.66, "shin": 0.66, "hair": 0.08, "hair_style": "up", "hat": "bucket", "hat_col": 0.96, "shoes": 0.05,
       "bare_forearms": True, "lips": 0.18}
BRUNO = {"skin": 0.62, "top": 0.92, "bare_arms": True, "bottom": 0.1, "hair": 0.06, "shoes": 0.08}
SUPER = {"skin": 0.6, "top": 0.1, "bottom": 0.1, "hair": 0.55, "collar": 0.95}
BODY_S = 0.74


def bg_field(wx, wy):
    """Static plaster, brick, tile and pergola light as a value field."""
    v = np.zeros_like(wx)
    n = value_noise(wx, wy, 40, 3)
    inside = wx < DOOR_X + 7
    wall = wy < WALL_BASE
    # interior plaster
    v = np.where(inside & wall, 0.55 + 0.04 * n - 0.15 * np.clip((WALL_BASE - wy) / 300, 0, 1), v)
    # terrace brick (as in a sunny courtyard)
    bx = (wx + np.where((wy // 13) % 2 == 0, 0, 15)) % 30
    by = wy % 13
    brick = 0.66 + 0.06 * value_noise(wx // 30 * 30, wy // 13 * 13, 9, 5) + 0.03 * n
    mortar = (bx < 2.2) | (by < 2.2)
    v = np.where(~inside & wall, np.where(mortar, 0.84, brick), v)
    # tiled floor in perspective (small square tiles)
    depth = np.maximum(wy - (WALL_BASE - 90), 1)
    u = (wx - 620) / depth * 3.2
    w_ = 300 / depth * 3.0
    grout = (np.abs(u - np.round(u)) < 0.05 * 1) | (np.abs(w_ - np.round(w_)) < 0.035 * (depth / 60))
    tile = np.where(inside, 0.62, 0.86) + 0.03 * n
    v = np.where(~wall, np.where(grout, tile - 0.16, tile), v)
    # pergola slat shadows across the terrace wall and floor
    ph_ = (wx * 1.0 + wy * 0.62 + 6 * value_noise(wx, wy, 60, 8)) % 86
    soft = np.clip(np.minimum(ph_ - 4, 34 - ph_) / 5, 0, 1)
    shade = 1 - 0.5 * soft
    beam = np.clip(1 - np.abs(wy - 150) / 22, 0, 1)  # the pergola beam's shadow high on the wall
    v = np.where(~inside, v * shade * (1 - 0.45 * beam), v)
    # interior is shaded except a patch of sun thrown through the doorway onto the floor
    patch = (~wall) & inside & (wx > DOOR_X - 230 + (wy - WALL_BASE) * 1.2) & (wx < DOOR_X + 8)
    v = np.where(inside & ~patch, v * OUT_AMT, v)
    return v


_BG = {}


def background(cam):
    if cam not in _BG:
        ph = Photo(cam=cam, light=LIGHT)
        ph.field(bg_field)
        static_props(ph)
        _BG[cam] = ph.a.copy()
    return _BG[cam]


def box3(ph, x0, y0, x1, y1, val, depth=10, top=None):
    """A lit box: front face, top face, sunlit side."""
    ph.shadow([(x0 - 30, y1), (x1, y1), (x1 - 20, y1 + 8), (x0 - 46, y1 + 8)], 0.45, 4)
    ph.rect(x0, y0, x1, y1, val, grad=((x0, y0), 1.05, (x0, y1), 0.8))
    ph.poly([(x0, y0), (x1, y0), (x1 + depth, y0 - depth * 0.6), (x0 + depth, y0 - depth * 0.6)], top if top is not None else C(val) * 1.15)
    ph.poly([(x1, y0), (x1 + depth, y0 - depth * 0.6), (x1 + depth, y1 - depth * 0.6), (x1, y1)], C(val) * 1.25)


def deck_chair(ph, x, y, s=1.0):
    """A folding chair: white tubular frame, striped canvas sling."""
    sling = lambda wx, wy: np.where(((wx - wy * 0.2) // (6 * s)) % 2 == 0, 0.9, 0.3)
    ph.poly([(x - 26 * s, y - 70 * s), (x + 4 * s, y - 64 * s), (x + 22 * s, y - 26 * s), (x - 4 * s, y - 30 * s)], sling, blur=0.8,
            grad=((x - 26 * s, y - 70 * s), 1.0, (x + 22 * s, y - 26 * s), 0.7))
    for a, b in (((x - 30 * s, y - 74 * s), (x + 24 * s, y)), ((x + 6 * s, y - 64 * s), (x - 24 * s, y)), ((x - 30 * s, y - 74 * s), (x + 6 * s, y - 64 * s)),
                 ((x + 22 * s, y - 26 * s), (x + 34 * s, y - 30 * s))):
        ph.capsule(a, b, 2.2 * s, 2.2 * s, 0.97, amb=0.45, spec=0.4)
    ph.shadow([(x - 40 * s, y), (x + 30 * s, y), (x - 10 * s, y + 10 * s), (x - 90 * s, y + 10 * s)], 0.4, 4)


def static_props(ph):
    # conveyor
    ph.capsule((50, 398), (270, 398), 8, 8, 0.25, amb=0.3, spec=0.3)
    for x in (70, 250):
        ph.capsule((x, 404), (x, FLOOR), 3, 3, 0.2, spec=0.3)
    # service desk with papers
    ph.shadow([(250, FLOOR), (420, FLOOR), (400, FLOOR + 10), (220, FLOOR + 10)], 0.5, 5)
    box3(ph, 290, 382, 420, FLOOR, 0.42, depth=12)
    ph.rect(312, 366, 352, 378, 0.95, blur=0.5)
    ph.rect(356, 370, 392, 377, 0.8, blur=0.5)
    # supervisor booth: dark interior behind glass
    ph.rect(430, 140, 580, 262, 0.62, grad=((430, 140), 1.0, (580, 262), 0.6))
    ph.rect(430, 262, 580, FLOOR, 0.3, grad=((430, 262), 1.0, (430, FLOOR), 0.7))
    for x in (430, 580):
        ph.capsule((x, 136), (x, FLOOR), 3.5, 3.5, 0.12, spec=0.3)
    ph.capsule((428, 138), (582, 138), 4, 4, 0.12, spec=0.3)
    ph.capsule((428, 262), (582, 262), 4, 4, 0.12, spec=0.3)
    # partition pillar (edge of the doorway)
    ph.rect(DOOR_X, 100, DOOR_X + 14, 300, 0.6, grad=((DOOR_X, 0), 0.7, (DOOR_X + 14, 0), 1.1))
    ph.rect(DOOR_X - 2, 296, DOOR_X + 16, 304, 0.4)
    # terrace: deck chairs behind, crates, bench, the closed service door
    deck_chair(ph, 690, 440, 0.8)
    deck_chair(ph, 745, 442, 0.8)
    for (x0, y0) in ((626, 410), (676, 410), (640, 352)):
        box3(ph, x0, y0, x0 + 50, y0 + 58, 0.62, depth=8)
        ph.stroke([(x0, y0 + 20), (x0 + 50, y0 + 20)], 1.2, 0.4)
        ph.stroke([(x0, y0 + 40), (x0 + 50, y0 + 40)], 1.2, 0.4)
    # bench
    ph.shadow([(BENCH_X - 85, FLOOR), (BENCH_X + 85, FLOOR), (BENCH_X + 20, FLOOR + 14), (BENCH_X - 150, FLOOR + 14)], 0.5, 5)
    for yy in (FLOOR - 48, FLOOR - 76):
        ph.capsule((BENCH_X - 85, yy), (BENCH_X + 85, yy), 4, 4, 0.55, spec=0.2)
    for xx in (BENCH_X - 70, BENCH_X + 70):
        ph.capsule((xx, FLOOR - 48), (xx, FLOOR), 2.5, 2.5, 0.2)
    # service door in the brick wall: dark varnished wood, brass knob, closed
    ph.rect(865, 230, 945, 400, 0.22, grad=((865, 230), 0.8, (945, 400), 1.1))
    ph.rect(873, 240, 937, 310, 0.28, blur=1)
    ph.rect(873, 320, 937, 392, 0.28, blur=1)
    ph.ellipsoid(878, 330, 3.5, 3.5, 0.8, spec=0.8)
    ph.rect(870, 214, 940, 226, 0.92, blur=0.6)


def dyn_props(ph, m, cut):
    # moving boxes on the conveyor
    off = (m * 60 * 1.6) % 60
    for k in range(5):
        bx = 50 + ((k * 60 + off) % 220)
        box3(ph, bx, 372, bx + 30, 390, 0.7, depth=6)
    # wall clock
    cx, cy, r = 140, 200, 30
    ph.shadow(((cx - 4, cy + 4), (r, r)), 0.4, 4, kind="ellipse")
    ph.ellipsoid(cx, cy, r, r, 0.9, amb=0.6)
    hrs = 12 + m / 60
    for a, ln, wd in ((2 * math.pi * (hrs / 12) - math.pi / 2, 0.5, 2.8), (2 * math.pi * (hrs % 1) - math.pi / 2, 0.8, 1.8)):
        ph.stroke([(cx, cy), (cx + math.cos(a) * r * ln, cy + math.sin(a) * r * ln)], wd, 0.05)
    if cut == "cut2" and m >= 3.05:
        f = ease(m, 3.05, 3.15)
        box3(ph, 262, lerp(372, FLOOR - 20, f), 292, lerp(390, FLOOR, f), 0.7, depth=6)


def supervisor_draw(ph, m, cut):
    g = gaze_at(cut, m)
    face = {"door": 1, "floor": -1, "ledger": 1}[g]
    sk = skeleton(505, 330, 0.72, "stand", 0, face, arm=60 if g == "ledger" else 10, arm2=50 if g == "ledger" else -5)
    if g == "ledger":
        sk["head"] = (sk["head"][0] + 2, sk["head"][1] + 6)
    person(ph, sk, SUPER)
    ph.rect(430, 262, 580, FLOOR, 0.3 * 0.82, grad=((430, 262), 1.0, (430, FLOOR), 0.7))
    ph.rect(486, 238, 528, 246, 0.9 if g == "ledger" else 0.75, blur=0.6)  # ledger on the sill
    # glass reflections over him
    ph.light_patch([(440, 145), (470, 145), (420, 258), (432, 258)], 0.18, 3)
    ph.light_patch([(520, 145), (532, 145), (500, 258), (494, 258)], 0.12, 3)
    return g


def actor_draw(ph, cut, who, m):
    x, v = path_x(PATHS[cut][who], m)
    walking = abs(v) > 1
    facing = 1 if v > 0 else -1
    pose, arm, arm2 = ("walk" if walking else "stand"), None, None
    if not walking:
        facing = -1 if x > DOOR_X else 1
        if who == "ada" and x > DOOR_X:
            facing = 1
        if who == "bruno" and x > DOOR_X:
            facing = -1
        if who == "ada" and x < DOOR_X and 0 <= m < 1:
            arm = 120  # pouring from a thermos
        if who == "bruno" and x < DOOR_X and cut == "cut2" and m < 3:
            arm = 70 + 25 * abs(math.sin(m * 60 * 2.2))  # stamping
        if who == "bruno" and x < DOOR_X and cut == "cut1" and 0 <= m < 1:
            arm = 95  # winding his watch
        if x > DOOR_X:
            pose, arm, arm2 = "sit", 62, 40
    xx = x if pose != "sit" else (BENCH_X - 42 if who == "ada" else BENCH_X + 42)
    sk = skeleton(xx, FLOOR - (0 if pose != "sit" else 2), BODY_S, pose, x / 64.0, facing, arm=arm, arm2=arm2)
    if pose != "sit":
        cast_shadow(ph, sk, dx=-0.8, dy=0.12, strength=0.5 if x > DOOR_X else 0.25)
    person(ph, sk, ADA if who == "ada" else BRUNO)
    return x, sk


def props_draw(ph, cut, m, ada, bruno):
    (ax, ask), (bx, bsk) = ada, bruno
    ha, hb = ask["arms"][0][1], bsk["arms"][0][1]
    if cut == "cut1":
        if m < 1.85:
            photo_envelope(ph, ha[0], ha[1] - 4, 26, 17)
        elif m < 2.0:
            p = lerp2(ha, hb, ease(m, 1.85, 2.0))
            photo_envelope(ph, p[0], p[1] - 4, 26, 17)
        elif m < 2.4:
            photo_envelope(ph, hb[0], hb[1] - 2, 26, 17, open_=ease(m, 2.05, 2.15))
            if m > 2.12:
                photo_key(ph, hb[0] - 14, hb[1] - 20, 0.5, angle=-0.3, spec=0.9)
        elif m < 3.4:
            photo_envelope(ph, BENCH_X + 4, FLOOR - 54, 26, 17, open_=1)
            photo_key(ph, hb[0] - 12, hb[1] - 6, 0.5, angle=-0.3, spec=0.9)
    else:
        if m < 2.9:
            photo_envelope(ph, ha[0], ha[1] - 4, 26, 17)
        elif m < 3.62:
            photo_envelope(ph, BENCH_X - 20, FLOOR - 54, 26, 17)
        elif m < 3.85:
            photo_envelope(ph, hb[0], hb[1] - 2, 26, 17, open_=ease(m, 3.65, 3.78))
        else:
            photo_envelope(ph, BENCH_X - 20, FLOOR - 54, 26, 17, open_=1)
            photo_key(ph, hb[0] - 12, hb[1] - 18, 0.5, angle=-0.3 + 0.2 * math.sin(m * 40), spec=0.9)


# camera plan per cut: (from minute, to minute, (scale, centre x, centre y))
WIDE = (1.0, 480, 296)
CAMS = {
    "cut1": [(-9, 1.72, WIDE), (1.72, 2.45, (2.45, 792, 392)), (2.45, 9, WIDE)],
    "cut2": [(-9, 1.65, WIDE), (1.65, 2.25, (2.3, 770, 392)), (2.25, 2.62, (2.2, 360, 380)), (2.62, 3.12, WIDE),
             (3.12, 3.45, (1.9, 610, 380)), (3.45, 3.88, WIDE), (3.88, 4.7, (2.45, 800, 392)), (4.7, 9, WIDE)],
}


def cam_at(cut, m):
    for a, b, c in CAMS[cut]:
        if a <= m < b:
            return c
    return WIDE


def header_band(img, cut, m):
    ink = ink_on(img)
    d = ink.d
    d.rectangle([0, 0, W, 60], fill=(6, 6, 6, 255))
    sc = SCHED[cut]
    ink.text((20, 10), "CUT 1 · ORIGINAL SHIFT" if cut == "cut1" else "CUT 2 · LATE BELL", "mono", 12, (230, 228, 220))
    x0, x1, t0, t1 = 290, 700, -0.3, 5.0
    X = lambda v: lerp(x0, x1, (clamp(v, t0, t1) - t0) / (t1 - t0))
    rows = [("ADA", sc["ada"], (225, 225, 220)), ("BRUNO", sc["bruno"], (150, 150, 146)),
            ("DOOR UNWATCHED", sc["unwatched"], (90, 90, 88)), ("MEETING", sc["window"], (255, 255, 255))]
    for k, (lab, span, col) in enumerate(rows):
        y = 6 + k * 12
        ink.text((x0 - 8, y + 4), lab, "mono", 9, (170, 168, 160), anchor="rm")
        d.rectangle([x0, y, x1, y + 8], fill=(30, 30, 30, 255))
        if span:
            d.rectangle([X(span[0]), y, X(span[1]), y + 8], fill=col + (255,))
        elif lab == "MEETING":
            ink.text((X(2.2), y + 4), "none: the breaks no longer overlap", "mono", 9, (230, 228, 220), anchor="mm")
    nx = X(m)
    d.line([(nx, 3), (nx, 54)], fill=(255, 255, 255, 255), width=2)
    for mm in range(0, 6):
        ink.text((X(mm), 56), f"12:0{mm}", "mono", 8, (140, 138, 130), anchor="mb")
    ink.text((830, 22), clock_str(m), "mono", 28, (244, 242, 236), anchor="mm")
    seen = cut == "cut2" and m >= 3.5
    ink.text((830, 48), "EXPOSURE: " + ("ADA LATE · ON RECORD" if seen else "NONE"), "mono", 10, (255, 255, 255) if seen else (150, 148, 140), anchor="mm")
    return ink.img


def sightline_overlay(img, ph, cut, m):
    """A thin chinagraph mark on the print: where the supervisor is looking (wide shots only)."""
    g = gaze_at(cut, m)
    if g == "ledger":
        return img
    eye = ph.P(512, 214) if g == "door" else ph.P(498, 214)
    tgts = [ph.P(DOOR_X - 2, 300), ph.P(DOOR_X + 20, FLOOR)] if g == "door" else [ph.P(110, 340), ph.P(300, FLOOR)]
    d = _Draw.Draw(img, "RGBA")
    for q in tgts:
        n = 24
        for k in range(0, n, 2):
            a, b = k / n, (k + 1) / n
            d.line([lerp2(eye, q, a), lerp2(eye, q, b)], fill=(255, 255, 255, 150), width=2)
    d.polygon([eye] + tgts, fill=(255, 255, 255, 26))
    return img


def play_cut(cut, local, k):
    m = (local - PRE) / S_PER_MIN
    cam = cam_at(cut, m)
    ph = Photo(cam=cam, light=LIGHT)
    ph.a[:] = background(cam)
    dyn_props(ph, m, cut)
    supervisor_draw(ph, m, cut)
    bruno = actor_draw(ph, cut, "bruno", m)
    ada = actor_draw(ph, cut, "ada", m)
    props_draw(ph, cut, m, ada, bruno)
    # interior exposure: people inside the factory sit in shade
    x_door = ph.P(DOOR_X + 7, 0)[0]
    if x_door > 0:
        box = (0, 0, int(clamp(x_door, 0, W)), H)
        if box[2] > 0:
            yy, xx = np.mgrid[0:H, 0:box[2]].astype(np.float32)
            wx, wy = ph.world(xx, yy)
            patch = (wy > WALL_BASE) & (wx > DOOR_X - 230 + (wy - WALL_BASE) * 1.2)
            mul = np.where(patch, 1.0, 0.82)[..., None]
            ph.a[:, :box[2]] *= mul
    img = finish(ph, LOOK, k)
    if cam == WIDE:
        img = sightline_overlay(img, ph, cut, m)
    for b in bells(cut):
        if b[0] <= m < b[0] + 0.12:
            ink = ink_on(img)
            ink.text((ph.P(140, 250)[0], ph.P(140, 250)[1]), "BELL", "mono", 14, (255, 255, 255), anchor="mm")
            img = ink.img
    img = header_band(img, cut, m)
    for a, b, who, line in CAPS[cut]:
        if a <= m < b:
            subtitle(img, line, who=who.title() if who else None, size=24)
    return img


def bells(cut):
    # (minute, label, pan)
    if cut == "cut1":
        return [(0, "both breaks", 0.0), (3, "Ada back", -0.5), (4, "Bruno back", 0.0)]
    return [(0, "Ada's break", -0.5), (3, "Ada back / Bruno's late break", 0.0)]


def text_card(lines, k, kicker=None):
    ph = Photo()
    ph.ground(0.04)
    img = finish(ph, {"grain": (0.04, 1.3), "bw": True}, k)
    ink = ink_on(img)
    if kicker:
        ink.text((W / 2, 64), kicker, "mono", 14, (190, 188, 180), anchor="mm")
    for (x, y, s, kind, size, col, anc) in lines:
        ink.text((x, y), s, kind, size, col, anchor=anc)
    return ink.img


@film.picture
def frame(t, k):
    name, local, a, b = SC.at(t)
    if name == "title":
        img = photo_card("AFTER RENZO E LUCIANA · MONICELLI / CALVINO 1962", "One break, one doorway",
                         "two co-workers · a private commitment · a supervisor's sightline", k=k)
    elif name == "rule":
        WH, GR = (244, 242, 236), (170, 168, 160)
        lines = [(W / 2, 128, "No private meetings on shift.", "serif", 42, WH, "mm"),
                 (W / 2, 178, "The supervisor watches the only doorway to the terrace.", "serif", 26, GR, "mm"),
                 (200, 250, "Ada's break        12:00 – 12:03", "mono", 20, WH, "la"),
                 (200, 288, "Bruno's break      12:00 – 12:04", "mono", 20, WH, "la"),
                 (200, 326, "doorway unwatched  12:01 – 12:04   (supervisor at his ledger)", "mono", 20, WH, "la"),
                 (200, 364, "safe meeting       12:01 – 12:03", "mono", 20, (255, 255, 255), "la"),
                 (W / 2, 440, "Ada carries a sealed envelope. Nobody at work may know why.", "mono", 14, GR, "mm")]
        img = text_card(lines, k, "THE RULE")
    elif name in ("cut1", "cut2"):
        img = play_cut(name, local, k)
    elif name == "card2":
        img = photo_card("CUT 2 · same rule, same people", "The late bell", "Bruno's break moves to 12:03 – 12:07 · overlap with Ada: none", k=k)
    else:
        WH, GR = (244, 242, 236), (160, 158, 150)
        rows = [("", "CUT 1 · original", "CUT 2 · late bell"),
                ("breaks", "overlap [12:00,12:03)", "overlap: none"),
                ("meeting", "12:01:42 – 12:02:24 on the bench", "none · one word in the doorway"),
                ("envelope", "hand to hand", "left sealed on the bench"),
                ("brass key", "Bruno, 12:02:10", "Bruno, 12:03:50, alone"),
                ("exposure", "none", "Ada 30 s late · on record"),
                ("service door", "closed", "closed")]
        lines = []
        for i, (a1, b1, c1) in enumerate(rows):
            y = 110 + i * 50
            lines += [(70, y, a1, "mono", 15, GR, "la"), (230, y, b1, "mono" if i else "serif", 17 if i else 26, WH, "la"),
                      (580, y, c1, "mono" if i else "serif", 17 if i else 26, WH, "la")]
        lines.append((W / 2, 480, "the small action that kept it: the envelope left where only he would sit", "mono", 14, (255, 255, 255), "mm"))
        img = text_card(lines, k, "RULE LEDGER")
    f = min(1.0, (t - a) / 0.35, (b - t) / 0.35)
    return fade_img(img, f)


@film.sound
def sound(mix):
    T = SC.total
    for cut in ("cut1", "cut2"):
        c0 = SC.start(cut)

        def at(m):
            return c0 + PRE + m * S_PER_MIN
        # machine room: drone + press thuds every 0.75 s
        mix.drone(c0, CUT, (49, 73.5, 98), gain=0.05, attack=0.6, release=0.6)
        k = 0.0
        while k < CUT - 0.5:
            mix.thud(c0 + k, 60, 0.12, -0.4, 0.25)
            mix.click(c0 + k + 0.37, 0.05, -0.5, 3000)
            k += 0.75
        for m, lab, pan in bells(cut):
            mix.ring(at(m), 1.6, 0.16, pan, 1650)
        # footsteps from the paths
        for who in ("ada", "bruno"):
            keys = PATHS[cut][who]
            for (m0, x0), (m1, x1) in zip(keys, keys[1:]):
                if x0 != x1 and m1 - m0 < 2:
                    mix.steps(at(m0), at(m1), 0.42, 0.14, "stone", (x0 / W) * 2 - 1, (x1 / W) * 2 - 1)
        for a, b, who, line in CAPS[cut]:
            if who in ("ADA", "BRUNO") and not line.startswith("("):
                mix.murmur(at(a) + 0.1, (b - a) * S_PER_MIN - 0.3, 0.07, 210 if who == "ADA" else 120, 0.4, seed=int(a * 100))
            if who == "SUPERVISOR":
                mix.murmur(at(a) + 0.1, (b - a) * S_PER_MIN - 0.3, 0.09, 95, -0.4, seed=7)
        if cut == "cut1":
            mix.click(at(2.12), 0.25, 0.5, 7000)   # key clink
            mix.click(at(2.14), 0.18, 0.5, 9000)
        else:
            for k in range(int(3.0 * S_PER_MIN / 0.55)):
                tt = at(0) + k * 0.55
                if tt < at(3.0):
                    mix.thud(tt, 140, 0.13, -0.1, 0.12)   # Bruno stamping forms
            mix.thud(at(3.12), 90, 0.4, -0.7, 0.3)        # box falls off the conveyor
            mix.click(at(2.92), 0.12, 0.5, 2500)          # envelope set on bench
            mix.click(at(3.8), 0.25, 0.5, 7000)
            mix.click(at(3.82), 0.18, 0.5, 9000)
    mix.bell(SC.start("card2") + 0.2, 392, 2.4, 0.12)
    mix.bell(SC.start("ledger") + 0.3, 523, 3.5, 0.1)
    mix.reverb(0.15, 1.2)


if __name__ == "__main__":
    film.render()
