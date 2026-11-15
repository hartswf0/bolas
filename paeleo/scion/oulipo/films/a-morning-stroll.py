"""A Morning Stroll — station variation. One visitor, one goose, one bench, three eras.
Every era runs the same 15-second event score (arrive · three-stroke bell · envelope ·
key on bench · goose taps key · HAT TIP · departure). Era chooses props and bell timbre;
technique chooses the drawing system. A diagnostic pass renders the 1909 era in two
techniques side by side with unchanged timing."""
import math
from kit import *
from kit_anim import run, hatch_poly, glow, sub_frame

film = Film("a-morning-stroll", seconds=55.0, boil=2, wobble=1.0, seed=5)
film.poster_at = 41.5

FLOOR = 420
SEAT = 374
ERA_LEN = 15.0
TITLE_END = 2.0
ERAS = [("1909", "engraved", 2.0), ("1959", "cel", 17.0), ("2059", "glow", 32.0)]
DIAG = (47.0, 55.0)
DIAG_FROM = 4.0          # diagnostic shows era-time 4.0 .. 12.0
BELL = (4.5, 4.9, 5.3)   # matched sound cue: three strokes
TAPS = (9.0, 9.4)        # goose beak on key
TIP = (10.0, 10.7)       # matched action: the visitor tips the hat to the goose
KEY_SPOT = (522, SEAT - 3)

# ----------------------------------------------------------- techniques ---

CREAM = (238, 229, 206)
BLACK = (24, 20, 18)

PALETTES = {
    # local colour per era (used by cel directly, by glow as the neon hue)
    "1909": dict(wall=(170, 120, 96), wall2=(120, 84, 70), floor=(150, 128, 100), bench=(130, 90, 60), iron=(50, 50, 55),
                 door=(96, 78, 66), coat=(40, 40, 46), skin=(232, 200, 170), hat=(30, 30, 34), goose=(245, 245, 240),
                 beak=(230, 140, 40), bell=(200, 160, 70), key=(214, 172, 70), env=(240, 234, 220), lamp=(255, 220, 140),
                 board=(40, 44, 40), seal=(160, 40, 40), pod=(120, 200, 220)),
    "1959": dict(wall=(156, 206, 196), wall2=(232, 186, 80), floor=(220, 210, 186), bench=(232, 104, 84), iron=(40, 40, 46),
                 door=(70, 116, 140), coat=(64, 84, 120), skin=(240, 196, 160), hat=(150, 110, 70), goose=(252, 250, 244),
                 beak=(244, 150, 50), bell=(220, 60, 50), key=(232, 186, 60), env=(250, 246, 236), lamp=(250, 236, 180),
                 board=(40, 60, 70), seal=(200, 50, 50), pod=(120, 200, 220)),
    "2059": dict(wall=(60, 120, 200), wall2=(120, 80, 220), floor=(70, 200, 230), bench=(90, 240, 220), iron=(80, 160, 255),
                 door=(255, 90, 160), coat=(150, 120, 255), skin=(255, 220, 200), hat=(90, 240, 255), goose=(250, 250, 255),
                 beak=(255, 170, 60), bell=(255, 220, 120), key=(255, 196, 70), env=(230, 240, 255), lamp=(150, 230, 255),
                 board=(80, 200, 255), seal=(255, 80, 120), pod=(120, 230, 255)),
}


class Tech:
    """One drawing system. Scene code describes shapes by tone (0 dark .. 1 light) and hue."""

    def __init__(self, ink, kind, era):
        self.ink, self.kind, self.pal = ink, kind, PALETTES[era]
        if kind == "engraved":
            ink.wobble = 1.0
            ink.fill(CREAM)
        elif kind == "cel":
            ink.wobble = 0.0
            ink.fill(self.pal["wall"])
        else:
            ink.wobble = 0.0
            ink.fill((7, 9, 22))
            self.sheet = ink.layer()

    def col(self, hue):
        return self.pal.get(hue, (128, 128, 128))

    def shape(self, pts, tone, hue, outline=True, angle=None, alpha=255):
        ink = self.ink
        if self.kind == "engraved":
            if tone < 0.22:
                ink.poly(pts, fill=BLACK, color=BLACK, width=2)
            elif tone > 0.8:
                ink.poly(pts, fill=CREAM, color=BLACK if outline else None, width=2.2)
            else:
                ink.poly(pts, fill=CREAM, color=None, rough=False)
                gap = int(3 + tone * 7)
                hatch_poly(ink, pts, gap=gap, angle=angle if angle is not None else 35, color=BLACK, width=1.4 if tone < 0.5 else 1,
                           cross=tone < 0.42, jitter=0.5)
                if outline:
                    ink.poly(pts, None, BLACK, 2.2)
        elif self.kind == "cel":
            c = self.col(hue)
            ink.poly(pts, fill=c + (alpha,), color=None, rough=False)
            if outline:
                ink.poly([(x + 2, y + 1) for x, y in pts], None, (40, 34, 40), 1.4, rough=False, alpha=170)
        else:
            c = self.col(hue)
            ink.poly(pts, fill=tuple(int(v * (0.10 + 0.12 * tone)) for v in c) + (alpha,), color=None, rough=False)
            if outline:
                self.sheet.poly(pts, None, c, 2 if tone > 0.3 else 1.5, rough=False, alpha=int(alpha * (0.55 + 0.45 * tone)))

    def line(self, pts, hue, width=2.0, tone=0.1, alpha=255):
        ink = self.ink
        if self.kind == "engraved":
            if tone < 0.6 and width >= 3:
                ink.line(pts, CREAM, width + 3.5, alpha=alpha, rough=False)
            ink.line(pts, BLACK if tone < 0.6 else CREAM, width + 0.6, alpha=alpha)
        elif self.kind == "cel":
            ink.line(pts, self.col(hue), width + 1, rough=False, alpha=alpha)
        else:
            self.sheet.line(pts, self.col(hue), width, rough=False, alpha=alpha)

    def circle(self, cx, cy, r, tone, hue, outline=True, n=None, alpha=255):
        n = n or max(14, int(r * 1.2))
        self.shape([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)], tone, hue, outline, alpha=alpha)

    def ellipse(self, cx, cy, rx, ry, tone, hue, ang=0.0, outline=True):
        n = max(16, int(max(rx, ry)))
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(cx + rx * math.cos(2 * math.pi * k / n) * ca - ry * math.sin(2 * math.pi * k / n) * sa,
                cy + rx * math.cos(2 * math.pi * k / n) * sa + ry * math.sin(2 * math.pi * k / n) * ca) for k in range(n)]
        self.shape(pts, tone, hue, outline)

    def rect(self, x0, y0, x1, y1, tone, hue, outline=True, angle=None, alpha=255):
        self.shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], tone, hue, outline, angle, alpha)

    def text(self, xy, s, size, hue="board", anchor="la", kind="mono"):
        ink = self.ink
        if self.kind == "engraved":
            ink.text(xy, s, "serif" if kind != "mono" else "mono", size, BLACK, anchor=anchor)
        elif self.kind == "cel":
            ink.text(xy, s, "sans", size, (40, 34, 40), anchor=anchor)
        else:
            self.sheet.text(xy, s, "mono", size, self.col(hue), anchor=anchor)

    def finish(self):
        if self.kind == "glow":
            glow(self.ink, self.sheet, radius=5, strength=1.4)
            ink = self.ink
            for y in range(0, ink.h, 3):
                ink.d.line([(0, y), (ink.w, y)], fill=(0, 0, 0, 40))
        elif self.kind == "engraved":
            self.ink.vignette(0.3)


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
    if era == "1909":
        st["sit"] = ease(tau, 11.0, 11.6)
    elif era == "1959":
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

def backdrop(P, era, tau):
    if era == "1909":
        P.rect(-4, -4, 964, 300, 0.55, "wall", outline=False, angle=0)
        for y in range(16, 300, 22):
            P.line([(0, y), (960, y)], "wall2", 1.2)
            for x in range((y // 22 % 2) * 30, 960, 60):
                P.line([(x, y), (x, y + 22)], "wall2", 1.0)
        P.rect(-4, 300, 964, FLOOR, 0.3, "wall2", angle=70)
        P.rect(-4, FLOOR, 964, 544, 0.62, "floor", angle=-8)
        for x in range(-200, 1200, 70):
            P.line([(x, FLOOR), (480 + (x - 480) * 1.6, 544)], "floor", 1.0)
        # gas lamp
        P.rect(108, 120, 116, FLOOR, 0.1, "iron")
        P.shape([(94, 92), (130, 92), (124, 126), (100, 126)], 0.92, "lamp")
        P.shape([(90, 92), (134, 92), (112, 76)], 0.1, "iron")
        # timetable board
        P.rect(640, 80, 830, 180, 0.12, "board")
        P.text((735, 92), "DEPARTURES", 15, anchor="ma", kind="serif")
        for k in range(3):
            P.line([(660, 122 + k * 18), (810, 122 + k * 18)], "board", 1.2, tone=0.9)
    elif era == "1959":
        P.rect(-4, -4, 964, 300, 0.8, "wall", outline=False)
        P.rect(-4, 300, 964, FLOOR, 0.6, "wall2", outline=False)
        for x in range(0, 960, 40):
            P.line([(x, 300), (x, FLOOR)], "iron", 0.4, alpha=50)
        P.rect(-4, FLOOR, 964, 544, 0.8, "floor", outline=False)
        # poster: geometric
        P.rect(70, 80, 190, 250, 0.9, "env")
        P.circle(130, 140, 34, 0.5, "bench", outline=False)
        P.shape([(86, 240), (174, 240), (130, 176)], 0.3, "door", outline=False)
        P.text((130, 92), "VISIT THE SEA", 10, anchor="ma")
        # clock
        P.circle(700, 140, 46, 0.95, "env")
        for k in range(12):
            a = k * math.pi / 6
            P.line([(700 + 38 * math.cos(a), 140 + 38 * math.sin(a)), (700 + 43 * math.cos(a), 140 + 43 * math.sin(a))], "iron", 1.5)
        P.line([(700, 140), (700 + 26 * math.cos(-0.9), 140 + 26 * math.sin(-0.9))], "iron", 3)
        P.line([(700, 140), (700, 104)], "iron", 2)
    else:
        P.rect(-4, -4, 964, FLOOR, 0.2, "wall", outline=False)
        for x in range(0, 960, 120):
            P.line([(x, 20), (x, FLOOR - 10)], "wall", 1, alpha=90)
        P.line([(0, 300), (960, 300)], "wall2", 1.5, alpha=180)
        P.rect(-4, FLOOR, 964, 544, 0.3, "floor", outline=False)
        P.line([(0, FLOOR), (960, FLOOR)], "floor", 2)
        for k in range(1, 6):
            y = FLOOR + k * k * 4.5
            P.line([(0, y), (960, y)], "floor", 1, alpha=110 - k * 15)
        P.rect(600, 80, 760, 170, 0.3, "board")
        P.text((680, 96), "PLATFORM 0", 13, anchor="ma")
        P.text((680, 124), "07:12  TO  ANYWHERE", 13, "lamp", anchor="ma")
        P.text((680, 148), "doors open for all", 11, "door", anchor="ma")
    # the service door: closed in every era
    dx = 250
    P.rect(dx - 52, FLOOR - 186, dx + 52, FLOOR, 0.12 if era == "1909" else 0.5, "iron")
    P.rect(dx - 42, FLOOR - 176, dx + 42, FLOOR, 0.4, "door", angle=90)
    P.circle(dx + 28, FLOOR - 88, 5, 0.9, "key")
    P.rect(dx - 34, FLOOR - 214, dx + 34, FLOOR - 192, 0.92, "env")
    P.text((dx, FLOOR - 209), "SERVICE", 11, "door", anchor="ma")


def bell(P, era, tau):
    x, y = 480, 120
    hit = [tau - b for b in BELL if 0 <= tau - b < 0.4]
    h = hit[0] if hit else None
    if era == "1909":
        sw = 0.35 * math.sin(tau * 18) * math.exp(-(tau - BELL[0]) * 1.2) if BELL[0] <= tau < BELL[-1] + 2 else 0
        P.line([(x - 40, y - 30), (x, y - 30), (x, y - 16)], "iron", 3)
        cx, cy = x + 30 * sw, y + 10
        P.shape([(x, y - 16), (cx - 20, cy + 24), (cx + 20, cy + 24)], 0.35, "bell")
        P.ellipse(cx, cy + 24, 20, 5, 0.1, "bell")
    elif era == "1959":
        P.circle(x, y, 26, 0.35, "bell")
        P.rect(x - 6, y + 22, x + 6, y + 40, 0.1, "iron")
        hx = x + (8 if h is not None and int(h * 40) % 2 else 0)
        P.circle(hx + 20, y + 22, 6, 0.1, "iron")
    else:
        pulse = math.exp(-h * 5) if h is not None else 0
        P.circle(x, y, 22, 0.25 + 0.7 * pulse, "bell", n=40)
        P.circle(x, y, 22 + 30 * (h or 0) * 2, 0.6, "bell", n=48, alpha=int(255 * pulse))
    if h is not None and P.kind != "glow":
        for k in range(3):
            a = -0.6 + k * 0.6
            P.line([(x + 36 * math.cos(a - 1.57) * 1.5, y + 20 + 36 * math.sin(a - 1.57)),
                    (x + 50 * math.cos(a - 1.57) * 1.5, y + 20 + 50 * math.sin(a - 1.57))], "bell", 2)


def bench_draw(P, era):
    x0, x1 = 360, 600
    if era == "1909":
        P.rect(x0 + 10, SEAT - 66, x1 - 10, SEAT - 52, 0.55, "bench", angle=0)
        P.rect(x0, SEAT - 6, x1, SEAT + 6, 0.55, "bench", angle=0)
        for px in (x0 + 18, x1 - 18):
            P.shape([(px - 6, SEAT - 66), (px + 6, SEAT - 66), (px + 10, FLOOR), (px - 10, FLOOR)], 0.1, "iron")
    elif era == "1959":
        P.rect(x0, SEAT - 8, x1, SEAT + 6, 0.5, "bench")
        for px, d in ((x0 + 22, -14), (x1 - 22, 14)):
            P.shape([(px - 3, SEAT + 6), (px + 3, SEAT + 6), (px + d + 2, FLOOR), (px + d - 2, FLOOR)], 0.1, "iron", outline=False)
        P.rect(x0 + 10, SEAT - 62, x1 - 10, SEAT - 44, 0.5, "bench")
    else:
        P.rect(x0, SEAT - 6, x1, SEAT + 6, 0.7, "bench")
        P.rect(x0 + 40, SEAT + 6, x1 - 40, SEAT + 12, 0.3, "bench")
        P.line([(x0 + 20, FLOOR + 8), (x1 - 20, FLOOR + 8)], "bench", 1.5, alpha=120)


def key_draw(P, x, y, s=1.0):
    P.circle(x - 10 * s, y, 6 * s, 0.85, "key")
    P.rect(x - 4 * s, y - 2 * s, x + 16 * s, y + 2 * s, 0.85, "key")
    P.rect(x + 10 * s, y + 2 * s, x + 13 * s, y + 6 * s, 0.85, "key", outline=False)
    if P.kind == "engraved":
        P.ink.circle(x - 10 * s, y, 2, fill=BLACK, color=None, width=0)


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
            P.line([hip, (x + 34 + dx, SEAT - 4), (x + 36 + dx, FLOOR)], "coat", 5, 0.05)
            P.line([(x + 36 + dx, FLOOR), (x + 46 + dx, FLOOR)], "coat", 5, 0.05)
    else:
        for sgn in (1, -1):
            a = math.sin(2 * math.pi * st["phase"]) * 0.42 * sgn if st["phase"] else 0.06 * sgn
            knee = (hip[0] + math.sin(a) * 32 * f, hip[1] + 32)
            foot = (knee[0] + math.sin(a - 0.12) * 32 * f, FLOOR)
            P.line([hip, knee, foot], "coat", 5, 0.05)
            P.line([foot, (foot[0] + 10 * f, FLOOR)], "coat", 5, 0.05)
    # coat (era cut)
    hem = {"1909": 34, "1959": 10, "2059": 22}[era]
    flare = {"1909": 14, "1959": 4, "2059": 8}[era]
    P.shape([(sh[0] - 13, sh[1]), (sh[0] + 13, sh[1]), (hip[0] + 14 + flare * f + s * 20 * f, hip[1] + hem * (1 - s * 0.6)),
             (hip[0] - 14 - flare * 0.4, hip[1] + hem * (1 - s * 0.6))], {"1909": 0.15, "1959": 0.4, "2059": 0.5}[era], "coat", angle=70)
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
    if era == "1909":   # bowler
        P.ellipse(hx, hy + 2, 19, 4, 0.1, "hat", ang=-tilt)
        P.shape([(hx - 12, hy + 1), (hx + 12, hy + 1), (hx + 10, hy - 10), (hx, hy - 15), (hx - 10, hy - 10)], 0.1, "hat")
    elif era == "1959":  # trilby, flat colour
        P.shape([(hx - 20, hy + 3), (hx + 20, hy + 1), (hx + 12, hy - 2), (hx + 10, hy - 14), (hx - 10, hy - 14), (hx - 12, hy - 2)], 0.3, "hat")
        P.rect(hx - 11, hy - 4, hx + 11, hy - 1, 0.1, "iron", outline=False)
    else:  # visor cap with a lit rim
        P.shape([(hx - 13, hy + 2), (hx + 13, hy + 2), (hx + 10, hy - 10), (hx - 10, hy - 10)], 0.4, "hat")
        P.line([(hx + 4 * f, hy + 2), (hx + 26 * f, hy + 4)], "hat", 3, 0.9)
    P.line([(sh[0], sh[1] + 4), elbow, hand], "coat", 4.5, 0.1)
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
    if P.kind == "engraved":
        P.line([(x + 20 * f, body_y - 8), mid, hd], "goose", 6.5, 0.95)
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


def scene(ink, era, kind, tau, label=True):
    P = Tech(ink, kind, era)
    backdrop(P, era, tau)
    bell(P, era, tau)
    if era == "2059":
        pod(P, tau)
    bench_draw(P, era)
    if tau >= 7.75:
        key_draw(P, *KEY_SPOT)
    visitor(P, era, tau)
    goose(P, era, tau)
    P.finish()
    if label:
        tag = {"engraved": "engraved line", "cel": "flat cel colour", "glow": "emitted light"}[kind]
        txt = f"{era} · {tag}"
        col = BLACK if kind == "engraved" else (40, 34, 40) if kind == "cel" else (150, 230, 255)
        ink.d.rectangle([16, 12, 26 + ink.text_size(txt, "mono", 15)[0] + 10, 40], fill=(CREAM if kind == "engraved" else (250, 247, 239) if kind == "cel" else (7, 9, 22)) + (220,))
        ink.label((28, 17), txt, 15, col)
    return P


@film.picture
def frame(t, ink):
    if t < TITLE_END:
        ink.fill(PAPER)
        ink.text((W / 2, 220), "A Morning Stroll", "serif", 64, INK, anchor="mm")
        ink.label((W / 2, 280), "station variation · three eras · one gesture, one bell", 15, MUTED, anchor="mm")
        ink.label((W / 2, 306), "1909 engraved  ·  1959 flat cel  ·  2059 emitted light", 13, ACCENT, anchor="mm")
        return
    for era, kind, start in ERAS:
        if start <= t < start + ERA_LEN:
            tau = t - start
            ink._grain = kind == "cel"
            scene(ink, era, kind, tau)
            cue = None
            if TIP[0] <= tau < TIP[1] + 0.3:
                cue = "GESTURE · hat tip"
            if BELL[0] <= tau < BELL[-1] + 0.4:
                cue = "CUE · three-stroke bell"
            if cue:
                tw = ink.text_size(cue, "mono", 15)[0]
                ink.d.rectangle([W - 40 - tw, 12, W - 16, 40], fill=ACCENT + (230,))
                ink.label((W - 28, 17), cue, 15, PAGE, anchor="ra")
            fade = min(1, tau / 0.3, (ERA_LEN - tau) / 0.3)
            if fade < 1:
                ink.d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - fade))))
            return
    # diagnostic: same era, same timing, two techniques
    lt = t - DIAG[0]
    tau = DIAG_FROM + lt
    ink.fill((30, 30, 32))
    ink.text((W / 2, 40), "Diagnostic · the 1909 era in two techniques, same timing", "serif", 28, PAGE, anchor="mm")
    for k, kind in enumerate(("engraved", "glow")):
        img = sub_frame(lambda tt, sub: scene(sub, "1909", kind, tau, label=False), tau, int(t * FPS), boil=4, wobble=1.0, seed=5)
        img = img.resize((456, 256), Image.LANCZOS)
        x = 16 + k * 472
        ink.paste(img, (x, 120))
        ink.label((x, 386), f"era 1909 · technique: {'engraved line' if k == 0 else 'emitted light'}", 13, RULE)
    ink.label((W / 2, 420), f"era-time {tau:4.1f} s", 14, BRASS, anchor="mm")
    ink.caption("Props and bell timbre come from the era; line and light come from the technique.", 1, y=480, size=20)
    if lt < 0.3:
        ink.d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - lt / 0.3))))


# ----------------------------------------------------------------- sound ---

PITCH = (659.3, 523.3, 392.0)


def era_bell(mix, era, at, gain=1.0, pan=0.0):
    for b, f in zip(BELL, PITCH):
        if era == "1909":
            mix.bell(at + b, f, 2.6, 0.32 * gain, pan)
        elif era == "1959":
            mix.ring(at + b, 0.3, 0.16 * gain, pan, freq=f * 2)
        else:
            tt = mix.t(1.6)
            sig = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.001 * tt)) * np.exp(-tt * 2.2)
            sig *= np.minimum(1, tt / 0.02)
            mix.add(sig, at + b, 0.28 * gain, pan)


def era_sound(mix, era, at, gain=1.0):
    if era == "1909":
        mix.room(at, ERA_LEN, gain=0.018 * gain, hum=0.5)
        for k in range(3):
            x = mix.band(mix.noise(1.2), 2000, 8000) * np.hanning(int(1.2 * mix.rate))
            mix.add(x, at + 1.2 + k * 4.4, 0.04 * gain, 0.7)
        surface = "wood"
    elif era == "1959":
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
    if era == "1959":
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
    era_sound(sub, "1909", 0.0)
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
