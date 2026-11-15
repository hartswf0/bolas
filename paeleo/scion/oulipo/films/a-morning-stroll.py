"""A Morning Stroll — station variation. One visitor, one goose, one bench, three eras on
the same street-side station: 1959 in stark black line with solid black shadows, 2009 in
flat colour with graphic shading at dusk, 2059 in a worn, desaturated, textured world with
long hard shadows. Every era runs the same 15-second event score (arrive · three-stroke
bell · envelope · key on bench · goose taps key · HAT TIP · departure). Era chooses props
and bell timbre; technique chooses the drawing. A diagnostic renders 1959 in two techniques."""
import math
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from kit import *
from kit_anim import run, sub_frame

film = Film("a-morning-stroll", seconds=55.0, boil=2, wobble=0.0, seed=5)
film.poster_at = 25.2

FLOOR = 440       # feet on the sidewalk
SEAT = 394
WALL = 380        # where the façade meets the pavement
CURB = 478
ERA_LEN = 15.0
TITLE_END = 2.0
ERAS = [("1959", "line", 2.0), ("2009", "flat", 17.0), ("2059", "grit", 32.0)]
DIAG = (47.0, 55.0)
DIAG_FROM = 4.0
BELL = (4.5, 4.9, 5.3)   # matched sound cue: three strokes
TAPS = (9.0, 9.4)
TIP = (10.0, 10.7)       # matched action: the hat tip to the goose
KEY_SPOT = (522, SEAT - 3)

LWHITE = (232, 232, 228)
LBLACK = (14, 14, 14)

PALETTES = {
    "1959": dict(wall=(200, 196, 186), wall2=(150, 146, 140), floor=(214, 212, 206), road=(120, 120, 120), bench=(150, 110, 80),
                 iron=(30, 30, 34), door=(110, 90, 76), coat=(70, 70, 76), trouser=(40, 40, 46), skin=(236, 206, 180), hat=(40, 40, 44),
                 goose=(248, 248, 244), beak=(232, 150, 50), bell=(190, 160, 80), key=(214, 172, 70), env=(244, 240, 230),
                 seal=(160, 40, 40), win=(40, 44, 50), frame=(220, 220, 214), tree=(90, 140, 80), sky=(200, 210, 214), sign=(240, 236, 226),
                 pod=(150, 150, 150), curb=(170, 170, 166)),
    "2009": dict(wall=(112, 108, 136), wall2=(84, 78, 110), floor=(168, 168, 172), road=(104, 104, 110), bench=(214, 88, 64),
                 iron=(22, 22, 28), door=(58, 92, 112), coat=(40, 150, 150), trouser=(210, 160, 40), skin=(232, 186, 150), hat=(200, 40, 50),
                 goose=(250, 250, 248), beak=(246, 150, 40), bell=(226, 54, 44), key=(240, 196, 60), env=(250, 248, 238),
                 seal=(200, 40, 40), win=(16, 18, 30), frame=(150, 146, 160), tree=(60, 150, 60), sky=(28, 46, 96), sign=(234, 220, 120),
                 pod=(120, 200, 220), curb=(236, 200, 30)),
    "2059": dict(wall=(104, 84, 72), wall2=(74, 62, 56), floor=(122, 128, 128), road=(70, 72, 74), bench=(96, 80, 64),
                 iron=(40, 42, 44), door=(64, 66, 64), coat=(70, 72, 66), trouser=(46, 46, 44), skin=(196, 170, 150), hat=(52, 50, 46),
                 goose=(240, 238, 230), beak=(220, 120, 40), bell=(140, 120, 80), key=(196, 160, 70), env=(214, 210, 198),
                 seal=(140, 40, 40), win=(22, 24, 26), frame=(110, 100, 92), tree=(70, 64, 56), sky=(176, 182, 178), sign=(160, 154, 140),
                 pod=(170, 172, 168), curb=(110, 112, 112)),
}


class Tech:
    """A drawing system. Scenes give shapes by tone (0 dark .. 1 light) and hue."""

    def __init__(self, ink, kind, era):
        self.ink, self.kind, self.era = ink, kind, era
        self.pal = PALETTES[era]
        ink.wobble = 0.8 if kind == "line" else 0.0

    def col(self, hue):
        return self.pal.get(hue, (128, 128, 128))

    def shape(self, pts, tone, hue, outline=True, alpha=255, **_):
        ink = self.ink
        if self.kind == "mask":
            ink.d.polygon([tuple(p) for p in pts], fill=255)
        elif self.kind == "line":
            if tone < 0.3:
                ink.poly(pts, fill=LBLACK, color=LBLACK, width=2)
            else:
                ink.poly(pts, fill=LWHITE + (alpha,), color=LBLACK if outline else None, width=2.4, alpha=alpha)
        else:
            c = self.col(hue)
            if self.kind == "flat" and tone < 0.5 and hue in ("wall", "wall2", "pod", "door"):
                c = tuple(int(v * 0.8) for v in c)
            if self.kind == "grit":
                c = tuple(min(255, int(v * (0.62 + 0.5 * tone))) for v in c)
            ink.poly(pts, fill=c + (alpha,), color=None, rough=False)

    def line(self, pts, hue, width=2.0, tone=0.1, alpha=255):
        ink = self.ink
        if self.kind == "mask":
            ink.d.line([tuple(p) for p in pts], fill=255, width=int(width + 1))
        elif self.kind == "line":
            if tone >= 0.6:
                ink.line(pts, LBLACK, width + 4, alpha=alpha)
                ink.line(pts, LWHITE, width, alpha=alpha, rough=False)
            else:
                ink.line(pts, LBLACK, width + 0.6, alpha=alpha)
        else:
            ink.line(pts, self.col(hue), width + 1, rough=False, alpha=alpha)

    def shadow(self, pts):
        if self.kind == "line":
            self.ink.poly(pts, fill=LBLACK, color=None, rough=False)
        elif self.kind == "flat":
            self.ink.poly(pts, fill=(30, 18, 54, 120), color=None, rough=False)
        elif self.kind == "grit":
            self.ink.poly(pts, fill=(10, 12, 16, 150), color=None, rough=False)

    def circle(self, cx, cy, r, tone, hue, outline=True, n=None, alpha=255):
        n = n or max(14, int(r * 1.2))
        self.shape([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)], tone, hue, outline, alpha=alpha)

    def ellipse(self, cx, cy, rx, ry, tone, hue, ang=0.0, outline=True):
        n = max(16, int(max(rx, ry)))
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(cx + rx * math.cos(2 * math.pi * k / n) * ca - ry * math.sin(2 * math.pi * k / n) * sa,
                cy + rx * math.cos(2 * math.pi * k / n) * sa + ry * math.sin(2 * math.pi * k / n) * ca) for k in range(n)]
        self.shape(pts, tone, hue, outline)

    def rect(self, x0, y0, x1, y1, tone, hue, outline=True, alpha=255, **_):
        self.shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], tone, hue, outline, alpha=alpha)

    def text(self, xy, s, size, hue="iron", anchor="la", kind="sans"):
        if self.kind == "mask":
            return
        c = LBLACK if self.kind == "line" else self.col(hue)
        self.ink.text(xy, s, kind, size, c, anchor=anchor)


# ------------------------------------------------------------ backdrops ---

_bg_cache = {}


def backdrop_image(era, kind):
    key = (era, kind)
    if key not in _bg_cache:
        ink = Ink(0, 0, (W, H), 0, 0.8, 5)
        ink.fill(LWHITE if kind == "line" else PALETTES[era]["wall"])
        P = Tech(ink, kind, era)
        ink.wobble = 0.8 if kind == "line" else 0.0
        draw_backdrop(P, era, kind)
        img = ink.img.convert("RGB")
        if kind == "grit":
            img = grit_texture(img)
        _bg_cache[key] = img
    return _bg_cache[key]


def grit_texture(img):
    rs = np.random.RandomState(12)
    a = np.asarray(img, np.float32)
    n1 = np.asarray(Image.fromarray(rs.uniform(0, 255, (H // 3, W // 3)).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    n2 = rs.normal(0, 1, (H, W)).astype(np.float32)
    n3 = np.asarray(Image.fromarray(rs.uniform(0, 255, (H // 40, W // 40)).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    yy = np.arange(H, dtype=np.float32)[:, None] / H
    soot = 1 - 0.35 * np.clip(1 - yy * 2.2, 0, 1) * (0.5 + 0.5 * n3)      # darker high on the wall
    a = a * (0.82 + 0.3 * n1[..., None]) * soot[..., None] + n2[..., None] * 6
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def draw_backdrop(P, era, kind):
    ink = P.ink
    # façade
    P.rect(-4, -4, 884, WALL, 0.9, "wall", outline=False)
    if kind != "line":
        P.rect(-4, -4, 300, WALL, 0.4, "wall2", outline=False)  # flat graphic shading on the left
    P.line([(-4, WALL), (884, WALL)], "iron", 2)
    # sky and the next lot beyond the building edge
    P.rect(884, -4, 964, WALL, 0.95 if era != "2009" else 0.2, "sky", outline=False)
    P.line([(884, -4), (884, WALL)], "iron", 2.4)
    # pavement, curb, road
    P.rect(-4, WALL, 964, CURB, 0.92, "floor", outline=False)
    P.rect(-4, CURB, 964, CURB + 14, 0.8 if era != "2009" else 0.9, "curb")
    P.rect(-4, CURB + 14, 964, 544, 0.35 if kind != "line" else 0.95, "road", outline=False)
    if kind == "line":
        P.line([(-4, CURB), (964, CURB)], "iron", 2.6)
        P.shadow([(-4, CURB + 14), (964, CURB + 14), (964, 544), (-4, 544)]) if False else None
        P.shadow([(-4, CURB + 14), (964, CURB + 14), (964, CURB + 30), (-4, CURB + 26)])
    if era == "2059":
        for x in range(-40, 1000, 96):   # flagstones with cracks
            P.line([(x, WALL), (x - 30, CURB)], "iron", 1, alpha=110)
        for y in (408, 446):
            P.line([(-4, y), (964, y)], "iron", 1, alpha=90)
        for cx, cy in ((180, 460), (640, 420), (820, 455)):
            P.line([(cx, cy), (cx + 18, cy - 6), (cx + 30, cy + 2), (cx + 46, cy - 4)], "iron", 1, alpha=140)
    if era == "2009":
        P.text((520, CURB + 1), "K E E P   C L E A R", 12, "iron", anchor="ma")
    # windows
    wins = [(70, 30), (320, 30), (560, 30), (760, 30), (560, 196), (760, 196)]
    for wx, wy in wins:
        w, h = 104, 112
        P.rect(wx - 6, wy - 6, wx + w + 6, wy + h + 10, 0.9, "frame")
        dark = era == "2009" or era == "2059"
        P.rect(wx, wy, wx + w, wy + h, 0.1 if dark else 0.95, "win")
        if kind == "line":
            P.shadow([(wx, wy), (wx + w, wy), (wx + w, wy + 16), (wx + 18, wy + 16), (wx + 18, wy + h), (wx, wy + h)])
        if era == "2059" and (wx + wy) % 3 == 0:   # boarded
            for k in range(3):
                P.shape([(wx - 4, wy + 18 + k * 34), (wx + w + 4, wy + 10 + k * 34), (wx + w + 4, wy + 26 + k * 34), (wx - 4, wy + 34 + k * 34)], 0.6, "bench")
        else:
            P.line([(wx + w / 2, wy), (wx + w / 2, wy + h)], "frame", 3, 0.9)
            P.line([(wx, wy + h / 2), (wx + w, wy + h / 2)], "frame", 3, 0.9)
        P.rect(wx - 10, wy + h + 6, wx + w + 10, wy + h + 16, 0.9, "frame")
    # fire escape over the upper right windows
    if era != "2059":
        for y in (150, 160):
            P.line([(540, y), (890 - 12, y)], "iron", 2.4)
        for x in range(546, 880, 18):
            P.line([(x, 150), (x, 130)], "iron", 1.4)
        P.line([(540, 130), (878, 130)], "iron", 2)
        P.line([(700, 160), (760, 196 + 60)], "iron", 2)
        P.line([(712, 160), (772, 196 + 60)], "iron", 2)
        for k in range(1, 6):
            P.line([(700 + k * 10, 160 + k * 16), (712 + k * 10, 160 + k * 16)], "iron", 1.4)
    else:
        P.line([(540, 150), (700, 154), (760, 190)], "iron", 2.4)   # what is left of it
    # stoop with railing, at the left
    steps = 5
    for k in range(steps):
        y0 = WALL - (k + 1) * 16
        P.rect(20 + k * 12, y0, 170, y0 + 16, 0.85, "wall2")
    if kind == "line":
        P.shadow([(170, WALL - 80), (196, WALL - 70), (196, WALL), (170, WALL)])
        P.shadow([(20, WALL), (196, WALL), (240, WALL + 30), (40, WALL + 30)])
    elif kind == "flat":
        P.shadow([(170, WALL - 80), (210, WALL - 64), (210, WALL), (170, WALL)])
    for k in range(9):
        x = 26 + k * 18
        P.line([(x, WALL - 16 - k * 8), (x, WALL - 60 - k * 8)], "iron", 1.8)
    P.line([(20, WALL - 60), (180, WALL - 132)], "iron", 2.6)
    # the station entrance: sign and the service door, closed
    dx = 250
    P.rect(dx - 52, WALL - 186, dx + 52, WALL, 0.9, "frame")
    P.rect(dx - 42, WALL - 176, dx + 42, WALL, 0.25 if kind == "line" else 0.4, "door")
    P.circle(dx + 28, WALL - 88, 5, 0.9, "key")
    P.line([(dx, WALL - 230), (dx, WALL - 210)], "iron", 2)
    P.rect(dx - 62, WALL - 214, dx + 62, WALL - 190, 0.9, "sign")
    P.text((dx, WALL - 210), "STATION · SERVICE", 13, "iron", anchor="ma")
    # lamp post and the far tree
    if era != "2059":
        P.rect(696, 120, 704, FLOOR - 10, 0.1, "iron")
        P.shape([(684, 98), (716, 98), (710, 124), (690, 124)], 0.9 if era == "1959" else 0.95, "sign")
    else:
        P.shape([(694, 260), (704, 260), (740, FLOOR - 12), (728, FLOOR - 10)], 0.1, "iron")   # bent post
    if era == "1959":   # cloud-crowned tree, outline only
        cx, cy = 925, 150
        pts = []
        for k in range(14):
            a = 2 * math.pi * k / 14
            r = 70 + 12 * math.sin(3 * a)
            for q in range(5):
                b = a + q * (2 * math.pi / 14) / 4
                bump = 1 + 0.12 * math.sin(math.pi * q / 4)
                pts.append((cx + math.cos(b) * r * bump * 0.8, cy + math.sin(b) * r * bump))
        P.shape(pts, 0.95, "tree")
        P.rect(918, 220, 932, WALL + 20, 0.95, "tree")
        P.shadow([(890, WALL + 20), (960, WALL + 20), (960, WALL + 34), (880, WALL + 30)])
    elif era == "2009":
        for cx, cy, r in ((930, 120, 60), (900, 200, 46), (950, 230, 40)):
            P.circle(cx, cy, r, 0.5, "tree", outline=False)
        P.circle(915, 110, 30, 0.5, "frame", outline=False, alpha=60)
        P.rect(924, 240, 934, WALL + 10, 0.2, "iron")
        # neon and posters: flat graphic signs
        P.rect(330, 52, 410, 120, 0.1, "win")
        P.text((370, 64), "TICKETS", 15, "sign", anchor="ma")
        P.rect(332, 54, 408, 118, 0.9, "bell", outline=False, alpha=0) if False else None
        ink.d.rectangle([336, 58, 404, 116], outline=(255, 90, 170), width=3)
        ink.d.rectangle([588, 250, 640, 274], fill=(220, 40, 40))
        ink.text((614, 254), "OPEN", "sans", 14, (250, 240, 230), anchor="ma")
        ink.d.rectangle([140, 140, 186, 196], fill=(240, 236, 226))
        ink.text((163, 146), "LOST", "sans", 11, (30, 30, 40), anchor="ma")
        key_shape(ink, 152, 176, 0.6)
        for gx, gy, gc in ((120, 330, (90, 200, 90)), (430, 340, (230, 110, 200)), (470, 300, (240, 220, 80))):
            ink.d.ellipse([gx, gy, gx + 60, gy + 26], fill=gc + (200,))
    else:
        for b in ((925, WALL, 905, 220), (912, 290, 870, 250), (918, 260, 950, 210)):
            P.line([b[:2], b[2:]], "tree", 4)
        # the wreck, low in the road
        P.shape([(620, 544), (640, 500), (700, 488), (820, 486), (880, 500), (900, 544)], 0.15, "iron")
        P.shape([(700, 488), (720, 470), (800, 468), (820, 486)], 0.1, "win")
        for cx in (660, 860):
            P.circle(cx, 534, 18, 0.1, "iron")
        for cx, cy in ((120, 450), (430, 468), (600, 432), (760, 462)):   # litter
            P.shape([(cx, cy), (cx + 12, cy - 2), (cx + 14, cy + 6), (cx + 2, cy + 8)], 0.9, "env")
    if kind == "line":
        # smoke smudge, top left, like a grey wash over the drawing
        sm = Image.new("L", (W, H), 0)
        ImageDraw.Draw(sm).ellipse([-200, -160, 360, 140], fill=150)
        sm = sm.filter(ImageFilter.GaussianBlur(60))
        ink.img.paste(Image.new("RGB", (W, H), (60, 60, 60)), (0, 0), sm)
        ink.d = ImageDraw.Draw(ink.img, "RGBA")


def bell(P, era, tau):
    x, y = 480, 170
    hit = [tau - b for b in BELL if 0 <= tau - b < 0.4]
    h = hit[0] if hit else None
    if era == "1959":
        sw = 0.35 * math.sin(tau * 18) * math.exp(-(tau - BELL[0]) * 1.2) if BELL[0] <= tau < BELL[-1] + 2 else 0
        P.line([(x - 40, y - 30), (x, y - 30), (x, y - 16)], "iron", 3)
        cx, cy = x + 30 * sw, y + 10
        P.shape([(x, y - 16), (cx - 20, cy + 24), (cx + 20, cy + 24)], 0.9, "bell")
        P.ellipse(cx, cy + 24, 20, 5, 0.1, "bell")
    elif era == "2009":
        P.circle(x, y, 26, 0.35, "bell")
        P.rect(x - 6, y + 22, x + 6, y + 40, 0.1, "iron")
        hx = x + (8 if h is not None and int(h * 40) % 2 else 0)
        P.circle(hx + 20, y + 22, 6, 0.1, "iron")
    else:
        P.rect(x - 22, y - 18, x + 22, y + 18, 0.4, "bell")
        for k in range(4):
            P.line([(x - 14, y - 10 + k * 7), (x + 14, y - 10 + k * 7)], "iron", 1.4)
        if h is not None:
            P.ink.d.ellipse([x + 26, y - 22, x + 34, y - 14], fill=(240, 120, 60))
    if h is not None:
        for k in range(3):
            a = -0.6 + k * 0.6
            P.line([(x + 36 * math.cos(a - 1.57) * 1.5, y + 20 + 36 * math.sin(a - 1.57)),
                    (x + 50 * math.cos(a - 1.57) * 1.5, y + 20 + 50 * math.sin(a - 1.57))], "iron", 2)


def bench_draw(P, era):
    x0, x1 = 360, 600
    if era == "1959":
        P.rect(x0 + 10, SEAT - 66, x1 - 10, SEAT - 52, 0.9, "bench")
        P.rect(x0, SEAT - 6, x1, SEAT + 6, 0.9, "bench")
        for px in (x0 + 18, x1 - 18):
            P.shape([(px - 6, SEAT - 66), (px + 6, SEAT - 66), (px + 10, FLOOR), (px - 10, FLOOR)], 0.1, "iron")
    elif era == "2009":
        P.rect(x0, SEAT - 8, x1, SEAT + 6, 0.5, "bench")
        for px, d in ((x0 + 22, -14), (x1 - 22, 14)):
            P.shape([(px - 3, SEAT + 6), (px + 3, SEAT + 6), (px + d + 2, FLOOR), (px + d - 2, FLOOR)], 0.1, "iron", outline=False)
        P.rect(x0 + 10, SEAT - 62, x1 - 10, SEAT - 44, 0.5, "bench")
    else:
        P.rect(x0, SEAT - 6, x1, SEAT + 6, 0.5, "bench")
        P.shape([(x0 + 10, SEAT - 62), (x1 - 60, SEAT - 58), (x1 - 60, SEAT - 46), (x0 + 10, SEAT - 50)], 0.5, "bench")  # one slat left
        for px in (x0 + 18, x1 - 18):
            P.rect(px - 5, SEAT + 6, px + 5, FLOOR, 0.2, "iron")



# ------------------------------------------------------------ the score ---

def visitor_state(tau):
    """Position, seating blend, walk phase, facing, hand target, props for era-time tau."""
    st = dict(x=-80, sit=0.0, phase=0.0, facing=1, hand=None, env="hand", env_open=0.0, key="env", tip=0.0, visible=True)
    if tau < 0.6:
        st["visible"] = False
        return st
    if tau < 3.6:
        f = ramp(tau, 0.6, 3.6)
        st["x"] = lerp(-60, 452, f)
        st["phase"] = st["x"] / 64
        return st
    st["x"] = 452
    if tau < 10.8:
        st["sit"] = ease(tau, 3.6, 4.0)
        lap = (st["x"] + 28, SEAT - 8)
        st["hand"] = lap
        st["env"] = "lap"
        if 5.6 <= tau < 7.2:
            st["hand"] = lerp2(lap, (st["x"] + 30, SEAT - 40), ease(tau, 5.6, 5.9))
            st["env"] = "hand"
            st["env_open"] = ease(tau, 5.9, 6.5)
            if tau >= 6.6:
                st["key"] = "hand"
        elif 7.2 <= tau < 7.8:
            st["hand"] = lerp2((st["x"] + 30, SEAT - 40), (KEY_SPOT[0], KEY_SPOT[1] - 6), ease(tau, 7.2, 7.7))
            st["env"], st["env_open"], st["key"] = "lap", 1.0, "hand"
        elif tau >= 7.8:
            st["hand"] = lerp2((KEY_SPOT[0], KEY_SPOT[1] - 6), lap, ease(tau, 7.8, 8.2))
            st["env"], st["env_open"], st["key"] = "lap", 1.0, "bench"
            if TIP[0] <= tau < TIP[1]:
                u = math.sin(math.pi * ramp(tau, TIP[0], TIP[1]))
                st["tip"] = u
                st["hand"] = lerp2(lap, (st["x"] + 8, SEAT - 100), min(1, u * 1.6))
        return st
    st["env"], st["env_open"], st["key"] = "hand", 1.0, "bench"
    if tau < 11.2:
        st["sit"] = 1 - ease(tau, 10.8, 11.2)
        return st
    st["facing"] = -1
    f = ramp(tau, 11.2, 14.2)
    st["x"] = lerp(452, -90, f)
    st["phase"] = -st["x"] / 64
    if st["x"] < -70:
        st["visible"] = False
    return st


def goose_state(tau, era):
    st = dict(x=1020, facing=-1, phase=0.0, neck=0.0, sit=0.0, hop=0.0, visible=tau >= 5.8, inside=False)
    if tau < 8.2:
        f = ramp(tau, 5.8, 8.2)
        st["x"] = lerp(1020, 628, f)
        st["phase"] = st["x"] / 40
        return st
    st["x"] = 628
    if tau < 10.2:
        # reach, then two taps on the key
        st["neck"] = ease(tau, 8.4, 8.9) * (1 - ease(tau, 9.7, 10.2))
        for tp in TAPS:
            if tp - 0.12 <= tau < tp + 0.12:
                st["neck"] = 1.08
        return st
    if era == "1959":
        st["sit"] = ease(tau, 11.0, 11.6)
    elif era == "2009":
        u = ramp(tau, 11.4, 12.0)
        st["hop"] = math.sin(math.pi * u) * 30 + 52 * smooth(u)
        st["x"] = lerp(628, 566, smooth(u))
        st["sit"] = ease(tau, 12.1, 12.6)
    else:
        st["facing"] = 1 if tau > 10.9 else -1
        f = ramp(tau, 11.0, 12.7)
        st["x"] = lerp(628, 846, f)
        st["phase"] = st["x"] / 40
        if tau > 12.95:
            st["inside"] = True
    return st


def pod_state(tau):
    door = ease(tau, 11.8, 12.4) * (1 - ease(tau, 13.0, 13.5))
    slide = ease(tau, 13.6, 15.0) ** 1.5 * 340
    return door, slide


# --------------------------------------------------------------- scenes ---

def key_draw(P, x, y, s=1.0):
    P.circle(x - 10 * s, y, 6 * s, 0.85, "key")
    P.rect(x - 4 * s, y - 2 * s, x + 16 * s, y + 2 * s, 0.85, "key")
    P.rect(x + 10 * s, y + 2 * s, x + 13 * s, y + 6 * s, 0.85, "key", outline=False)


def envelope_draw(P, x, y, opened):
    P.rect(x - 18, y - 11, x + 18, y + 11, 0.95, "env")
    tip = lerp(y + 2, y - 22, opened)
    P.shape([(x - 18, y - 11), (x + 18, y - 11), (x, tip)], 0.85 if opened > 0.5 else 0.95, "env")
    if opened < 0.5:
        P.circle(x, y - 1, 3.5, 0.15, "seal")


def visitor(P, era, tau):
    st = visitor_state(tau)
    if not st["visible"]:
        return
    x, s, f = st["x"], st["sit"], st["facing"]
    # standing frame
    hip_s = (x, FLOOR - 64)
    hip_t = (x, SEAT - 6)
    hip = lerp2(hip_s, hip_t, s)
    sh = (hip[0] + 4 * f * s, hip[1] - 52)
    head = (sh[0] + 3 * f, sh[1] - 20)
    # legs
    if s > 0.5:
        for dx in (0, -5):
            P.line([hip, (x + 34 + dx, SEAT - 4), (x + 36 + dx, FLOOR)], "trouser", 5, 0.05)
            P.line([(x + 36 + dx, FLOOR), (x + 46 + dx, FLOOR)], "trouser", 5, 0.05)
    else:
        for sgn in (1, -1):
            a = math.sin(2 * math.pi * st["phase"]) * 0.42 * sgn if st["phase"] else 0.06 * sgn
            knee = (hip[0] + math.sin(a) * 32 * f, hip[1] + 32)
            foot = (knee[0] + math.sin(a - 0.12) * 32 * f, FLOOR)
            P.line([hip, knee, foot], "trouser", 5, 0.05)
            P.line([foot, (foot[0] + 10 * f, FLOOR)], "trouser", 5, 0.05)
    # coat (era cut)
    hem = {"1959": 34, "2009": 10, "2059": 22}[era]
    flare = {"1959": 14, "2009": 4, "2059": 8}[era]
    P.shape([(sh[0] - 13, sh[1]), (sh[0] + 13, sh[1]), (hip[0] + 14 + flare * f + s * 20 * f, hip[1] + hem * (1 - s * 0.6)),
             (hip[0] - 14 - flare * 0.4, hip[1] + hem * (1 - s * 0.6))], {"1959": 0.9, "2009": 0.5, "2059": 0.5}[era], "coat")
    # arm and hand
    hand = st["hand"]
    if hand is None:
        a = math.sin(2 * math.pi * st["phase"]) * 0.4
        hand = (sh[0] + math.sin(a) * 42 * f, sh[1] + 44)
    elbow = ((sh[0] + hand[0]) / 2 - 6 * f, (sh[1] + hand[1]) / 2 + 10)
    # head and hat
    P.circle(head[0], head[1], 13, 0.88, "skin")
    lift = st["tip"] * 16
    tilt = st["tip"] * 0.35
    hx, hy = head[0] + st["tip"] * 4, head[1] - 9 - lift
    if era == "1959":   # trilby
        P.shape([(hx - 20, hy + 3), (hx + 20, hy + 1), (hx + 12, hy - 2), (hx + 10, hy - 14), (hx - 10, hy - 14), (hx - 12, hy - 2)], 0.1, "hat")
    elif era == "2009":  # cap, peak forward
        P.shape([(hx - 13, hy + 2), (hx + 13, hy + 2), (hx + 10, hy - 10), (hx - 10, hy - 10)], 0.4, "hat")
        P.shape([(hx + 6 * f, hy - 1), (hx + 28 * f, hy + 2), (hx + 26 * f, hy + 5), (hx + 6 * f, hy + 4)], 0.4, "hat")
    else:  # wide brim against the low sun
        P.shape([(hx - 26, hy + 4), (hx + 26, hy + 2), (hx + 24, hy - 1), (hx - 24, hy + 1)], 0.2, "hat")
        P.shape([(hx - 11, hy + 1), (hx + 11, hy + 1), (hx + 9, hy - 13), (hx - 9, hy - 13)], 0.2, "hat")
    P.line([(sh[0], sh[1] + 4), elbow, hand], "coat", 4.5, 0.9 if era == "1959" else 0.1)
    P.circle(hand[0], hand[1], 4.5, 0.88, "skin")
    # props
    if st["env"] == "hand":
        envelope_draw(P, hand[0] + 6 * f, hand[1] + 2, st["env_open"])
    elif st["env"] == "lap":
        envelope_draw(P, x + 20, SEAT - 14, st["env_open"])
    if st["key"] == "hand":
        key_draw(P, hand[0] + 4, hand[1] - 16 if tau < 7.2 else hand[1] - 4)
    elif st["key"] == "env" and st["env"] == "hand" and st["env_open"] > 0.6:
        pass


def goose(P, era, tau, alpha_inside=False):
    st = goose_state(tau, era)
    if not st["visible"] or st["inside"]:
        return
    x, f = st["x"], st["facing"]
    base = FLOOR - st["hop"]
    body_y = base - 30 + st["sit"] * 12
    if st["sit"] < 0.8:
        for sgn in (1, -1):
            a = math.sin(2 * math.pi * st["phase"]) * 0.4 * sgn if st["phase"] else 0
            P.line([(x, body_y + 14), (x + math.sin(a) * 12, base)], "beak", 3, 0.5)
            P.line([(x + math.sin(a) * 12, base), (x + math.sin(a) * 12 + 8 * f, base)], "beak", 3, 0.5)
    P.ellipse(x, body_y, 30, 17, 0.9, "goose", ang=0.12 * f)
    P.shape([(x - 26 * f, body_y - 4), (x - 44 * f, body_y - 14), (x - 30 * f, body_y + 4)], 0.9, "goose")
    P.line([(x - 18 * f, body_y - 2), (x + 10 * f, body_y - 6), (x + 16 * f, body_y + 2)], "goose", 1.5, 0.2)
    # neck: rest pose -> reach to the key
    n = st["neck"]
    rest = (x + 26 * f, body_y - 44)
    target = (KEY_SPOT[0] + 18, KEY_SPOT[1] - 10)
    hd = lerp2(rest, target, min(1, n)) if n <= 1 else (target[0] - 2, target[1] + 5)
    mid = ((x + 22 * f + hd[0]) / 2, min(body_y - 30, hd[1] - 8))
    P.line([(x + 20 * f, body_y - 8), mid, hd], "goose", 9, 0.95)
    P.circle(hd[0], hd[1], 8, 0.9, "goose")
    bf = -1 if n > 0.5 else f
    P.shape([(hd[0] + 6 * bf, hd[1] - 3), (hd[0] + 20 * bf, hd[1] + 2), (hd[0] + 6 * bf, hd[1] + 4)], 0.5, "beak")
    P.circle(hd[0] + 2 * bf, hd[1] - 2, 1.6, 0.05, "iron", outline=False)


def pod(P, tau):
    door, slide = pod_state(tau)
    ox = slide
    x0, x1, y0, y1 = 760 + ox, 1010 + ox, 230, FLOOR - 4
    P.shape([(x0 + 30, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0 + 40)], 0.25, "pod")
    dxl, dxr = 820 + ox, 900 + ox
    w = (dxr - dxl) / 2
    P.rect(dxl - w * door * 0.9, y0 + 30, dxl + w - w * door * 0.9, y1 - 6, 0.5, "pod")
    P.rect(dxl + w + w * door * 0.9, y0 + 30, dxr + w * door * 0.9, y1 - 6, 0.5, "pod")
    P.line([(x0 + 20, y1 + 6), (x1, y1 + 6)], "pod", 2)
    sensor = 0.9 if 11.6 < tau < 13.5 else 0.3
    P.circle(dxl + w, y0 + 18, 4, sensor, "door")
    gs = goose_state(tau, "2059")
    if gs["inside"]:
        # a white shape behind the glass
        P.ellipse(860 + ox, y1 - 50, 26, 15, 0.7, "goose")
        P.circle(884 + ox, y1 - 92, 7, 0.7, "goose")
        P.line([(878 + ox, y1 - 58), (884 + ox, y1 - 88)], "goose", 6, 0.7)



# ------------------------------------------------------------- shadows ---

SUN = {  # how a caster's silhouette is thrown onto the pavement: (run per px of height, rise per px)
    "line": (0.6, 0.12),     # high sun: a short solid black pool at the feet
    "flat": (0.5, 0.06),
    "grit": (1.3, 0.42),      # low sun: long hard shadows across the flagstones
}


def cast(ink, era, kind, tau):
    """Draw visitor, goose and bench as a mask, then shear it onto the ground."""
    m = Ink(tau, 0, (W, H), 0, 0, 0)
    m.img = Image.new("L", (W, H), 0)
    m.d = ImageDraw.Draw(m.img)
    P = Tech(m, "mask", era)
    bench_draw(P, era)
    visitor(P, era, tau)
    goose(P, era, tau)
    run_, rise = SUN[kind]
    # inverse map: ground point (X, Y) comes from caster point (x, y) with height F - y
    k = 1.0 / rise
    F = FLOOR
    sh = m.img.transform((W, H), Image.AFFINE, (1, run_ * k, -run_ * k * F, 0, k, F - k * F), resample=Image.BILINEAR)
    cut = Image.new("L", (W, H), 0)
    ImageDraw.Draw(cut).rectangle([0, WALL - 10, W, CURB + 14], fill=255)
    sh = ImageChops.multiply(sh, cut)
    if kind == "line":
        ink.img.paste(Image.new("RGB", (W, H), LBLACK), (0, 0), sh.point(lambda v: 255 if v > 90 else 0))
    elif kind == "flat":
        ink.img.paste(Image.new("RGB", (W, H), (40, 26, 70)), (0, 0), sh.point(lambda v: int(v * 0.45)))
    else:
        ink.img.paste(Image.new("RGB", (W, H), (12, 14, 18)), (0, 0), sh.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: int(v * 0.8)))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def scene(ink, era, kind, tau, label=True):
    ink.img.paste(backdrop_image(era, kind), (0, 0))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    P = Tech(ink, kind, era)
    cast(ink, era, kind, tau)
    bell(P, era, tau)
    if era == "2059":
        pod(P, tau)
    bench_draw(P, era)
    if tau >= 7.75:
        key_draw(P, *KEY_SPOT)
    visitor(P, era, tau)
    goose(P, era, tau)
    finish(ink, kind, tau)
    if label:
        tag = {"line": "black line, solid shadow", "flat": "flat colour, graphic shade", "grit": "worn texture, low sun"}[kind]
        txt = f"{era} · {tag}"
        tw = ink.text_size(txt, "mono", 15)[0]
        ink.d.rectangle([16, 12, 36 + tw, 40], fill=(LBLACK if kind == "line" else (20, 18, 30) if kind == "flat" else (30, 32, 34)) + (210,))
        ink.label((26, 17), txt, 15, LWHITE)
    return P


_grit_noise = None


def finish(ink, kind, tau):
    global _grit_noise
    if kind == "line":
        # old print: lift blacks a little, flicker, heavy vignette
        img = ink.img.convert("L")
        fl = 1 + 0.03 * math.sin(tau * 23) + 0.02 * math.sin(tau * 61)
        img = img.point(lambda v: int(min(255, (22 + v * 0.86) * fl)))
        ink.img = img.convert("RGB")
        ink.vignette(0.6)
    elif kind == "grit":
        if _grit_noise is None:
            rs = np.random.RandomState(31)
            _grit_noise = rs.normal(0, 1, (H, W)).astype(np.float32)
        a = np.asarray(ink.img, np.float32)
        g = a.mean(axis=2, keepdims=True)
        a = g + (a - g) * 0.55                                      # drained colour
        a = a * np.array([0.94, 1.0, 1.04], np.float32) + _grit_noise[..., None] * 4
        ink.img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        ink.vignette(0.35)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


@film.picture
def frame(t, ink):
    if t < TITLE_END:
        ink.fill(LWHITE)
        ink.text((W / 2, 220), "A Morning Stroll", "sans", 60, LBLACK, anchor="mm")
        ink.label((W / 2, 282), "station variation · three eras · one gesture, one bell", 15, (70, 70, 70), anchor="mm")
        ink.label((W / 2, 308), "1959 black line  ·  2009 flat colour  ·  2059 worn and textured", 13, (140, 40, 40), anchor="mm")
        ink.vignette(0.6)
        return
    for era, kind, start in ERAS:
        if start <= t < start + ERA_LEN:
            tau = t - start
            ink._grain = kind == "line"
            scene(ink, era, kind, tau)
            cue = None
            if TIP[0] <= tau < TIP[1] + 0.3:
                cue = "GESTURE · hat tip"
            if BELL[0] <= tau < BELL[-1] + 0.4:
                cue = "CUE · three-stroke bell"
            if cue:
                tw = ink.text_size(cue, "mono", 15)[0]
                ink.d.rectangle([W - 40 - tw, 12, W - 16, 40], fill=(150, 30, 40, 230))
                ink.label((W - 28, 17), cue, 15, LWHITE, anchor="ra")
            fade = min(1, tau / 0.3, (ERA_LEN - tau) / 0.3)
            if fade < 1:
                ink.d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - fade))))
            return
    lt = t - DIAG[0]
    tau = DIAG_FROM + lt
    ink._grain = False
    ink.fill((30, 30, 32))
    ink.text((W / 2, 40), "Diagnostic · the 1959 era in two techniques, same timing", "sans", 26, LWHITE, anchor="mm")
    for k, kind in enumerate(("line", "flat")):
        img = sub_frame(lambda tt, sub: scene(sub, "1959", kind, tau, label=False), tau, int(t * FPS), boil=2, wobble=0.8, seed=5)
        img = img.resize((456, 256), Image.LANCZOS)
        x = 16 + k * 472
        ink.paste(img, (x, 120))
        ink.label((x, 386), f"era 1959 · technique: {'black line' if k == 0 else 'flat colour'}", 13, (200, 200, 200))
    ink.label((W / 2, 420), f"era-time {tau:4.1f} s", 14, (220, 180, 90), anchor="mm")
    ink.text((W / 2, 480), "Props and bell timbre come from the era; line, fill and shadow come from the technique.", "sans", 18, LWHITE, anchor="mm")
    if lt < 0.3:
        ink.d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - lt / 0.3))))


# ----------------------------------------------------------------- sound ---

PITCH = (659.3, 523.3, 392.0)


def era_bell(mix, era, at, gain=1.0, pan=0.0):
    for b, f in zip(BELL, PITCH):
        if era == "1959":
            mix.bell(at + b, f, 2.6, 0.32 * gain, pan)
        elif era == "2009":
            mix.ring(at + b, 0.3, 0.16 * gain, pan, freq=f * 2)
        else:
            tt = mix.t(1.6)
            sig = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.001 * tt)) * np.exp(-tt * 2.2)
            sig *= np.minimum(1, tt / 0.02)
            mix.add(sig, at + b, 0.28 * gain, pan)


def era_sound(mix, era, at, gain=1.0):
    if era == "1959":
        mix.room(at, ERA_LEN, gain=0.018 * gain, hum=0.5)
        for k in range(3):
            x = mix.band(mix.noise(1.2), 2000, 8000) * np.hanning(int(1.2 * mix.rate))
            mix.add(x, at + 1.2 + k * 4.4, 0.04 * gain, 0.7)
        surface = "wood"
    elif era == "2009":
        mix.room(at, ERA_LEN, gain=0.022 * gain, hum=60)
        surface = "stone"
    else:
        mix.drone(at, ERA_LEN, (110, 165, 220), gain=0.03 * gain)
        surface = "water"
    if era == "2059":
        for k in range(int(3.0 / 0.46)):
            mix.click(at + 0.7 + k * 0.46, 0.08 * gain, -0.6, 1200)
        for k in range(int(3.0 / 0.46)):
            mix.click(at + 11.3 + k * 0.46, 0.07 * gain, -0.6, 1200)
    else:
        mix.steps(at + 0.7, at + 3.6, 0.46, 0.17 * gain, surface, -0.7, -0.1)
        mix.steps(at + 11.3, at + 14.2, 0.46, 0.15 * gain, surface, -0.1, -0.8)
    era_bell(mix, era, at, gain)
    # paper, key on wood, goose honk, the two taps (matched in every era)
    mix.add(mix.band(mix.noise(0.5), 1500, 7000) * np.exp(-np.linspace(0, 4, int(0.5 * mix.rate))), at + 5.9, 0.08 * gain)
    mix.click(at + 7.72, 0.25 * gain, 0.1, 3000)
    tt = mix.t(0.3)
    honk = sum(np.sin(2 * np.pi * 310 * k * tt) / k for k in range(1, 8)) * np.sin(np.pi * tt / 0.3)
    mix.add(mix.band(honk, 400, 2400) * 0.5, at + 6.1, 0.2 * gain, 0.6)
    for tp in TAPS:
        mix.click(at + tp, 0.28 * gain, 0.2, 2200, 0.02)
        mix.thud(at + tp, 260, 0.08 * gain, 0.2, 0.08)
    if era == "2009":
        mix.whoosh(at + 11.5, 0.4, 0.06 * gain, 0.3)
        mix.step(at + 12.0, 0.12 * gain, 0.3, "wood")
    if era == "2059":
        mix.whoosh(at + 11.8, 0.6, 0.08 * gain, 0.7)
        mix.whoosh(at + 13.0, 0.5, 0.06 * gain, 0.7)
        tt = mix.t(1.8)
        hum = np.sin(2 * np.pi * (80 + 120 * tt) * tt) * np.minimum(1, tt) * np.exp(-tt * 0.8)
        mix.add(hum, at + 13.4, 0.12 * gain, 0.8)


@film.sound
def sound(mix):
    mix.note(0.3, 392, 1.2, 0.08)
    for era, kind, start in ERAS:
        era_sound(mix, era, start)
    # diagnostic: the 1909 track, same timing, cut to the shown window
    sub = Mix(ERA_LEN, seed=9)
    era_sound(sub, "1959", 0.0)
    a = int(DIAG_FROM * mix.rate)
    n = int((DIAG[1] - DIAG[0]) * mix.rate)
    i = int(DIAG[0] * mix.rate)
    seg_l, seg_r = sub.L[a:a + n], sub.R[a:a + n]
    env = np.minimum(1, np.arange(len(seg_l)) / (0.2 * mix.rate))
    mix.L[i:i + len(seg_l)] += seg_l * env * 0.8
    mix.R[i:i + len(seg_r)] += seg_r * env * 0.8
    mix.reverb(0.14)


if __name__ == "__main__":
    run(film)
