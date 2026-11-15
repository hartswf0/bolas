"""Teuf-Teuf, painted as a cave wall: one load, one push, three mechanisms (drag, loose
logs, axled wheels) in black and ochre pigment on limestone. Same stage, load, hand
height and seven-second push window in every trial; a counter-check removes the axle."""
import math
from kit import *
import random
from kit_anim import run

film = Film("teuf-teuf", seconds=30.5, boil=6, wobble=0.9, seed=3)
film.poster_at = 21.0

G = 430            # ground line
PX = 70            # pixels per metre
X0 = 230           # crate front edge at 0 m
CW, CH = 120, 80   # crate
HAND_Y = G - 78    # same hand height in every trial
PUSH = 7.0         # same push window in every trial
TITLE = (0.0, 1.8)
SECT = {"drag": (1.8, 9.4), "roll": (9.4, 17.0), "wheel": (17.0, 24.6)}
LEAD = 0.3
COUNTER = (24.6, 27.2)
SUMMARY = (27.2, 30.5)
ROLL_R = 12
WHEEL_R = 20


# ------------------------------------------------------------- mechanics ---

def drag_m(tau):
    """Stick-slip: nine lurches in the push window, 1.2 m total."""
    tau = clamp(tau, 0, PUSH)
    n = 9
    per = PUSH / n
    k = min(n - 1, int(tau / per))
    f = (tau - k * per) / per
    if tau >= PUSH:
        k, f = n - 1, 1.0
    return 1.2 * (k + smooth((f - 0.45) / 0.35)) / n


def roll_load_m(tau):
    tau = clamp(tau, 0, PUSH)
    if tau < 2.2:
        return 1.5 * smooth(tau / 2.2)
    if tau < 4.8:
        return 1.5
    return 1.5 + 1.5 * smooth((tau - 4.8) / 2.2)


def wheel_m(tau):
    return 8.0 * ease(tau, 0, 6.0)


def roll_sim(tau):
    """Integrate the loose rollers: under the load they travel at half its speed;
    once their centre is behind the crate they stay where they fell. At 2.2–3.8 s the
    pusher carries the rear roller to the front."""
    tau = clamp(tau, 0, PUSH)
    L0 = X0 - CW
    rollers = [dict(x=L0 + r, a=0.0, carried=False) for r in (18, 60, 102)]
    dt = 1 / 240
    s, prevL = 0.0, L0
    picked = None
    while s < tau:
        s = min(tau, s + dt)
        L = X0 - CW + roll_load_m(s) * PX
        dL = L - prevL
        prevL = L
        if picked is None and s >= 2.5:
            picked = min(range(3), key=lambda k: rollers[k]["x"])
            rollers[picked]["carried"] = True
        if picked is not None and s >= 3.8 and rollers[picked]["carried"]:
            rollers[picked]["carried"] = False
            rollers[picked]["x"] = L + CW + 8
        for r in rollers:
            if r["carried"]:
                continue
            rel = r["x"] - L
            if 0 <= rel <= CW:
                r["x"] += dL / 2
                r["a"] += (dL / 2) / ROLL_R
    return rollers, picked


def carry_pose(tau, L):
    """Pusher x (hands) and what it holds during the roller carry."""
    if tau < 2.2 or tau >= 4.8:
        return L, False, 0.0
    if tau < 2.5:   # stoop and pick up
        return L - 6, False, ease(tau, 2.2, 2.45)
    if tau < 3.5:
        return lerp(L - 6, L + CW + 60, ease(tau, 2.5, 3.5)), True, 1.0
    if tau < 3.8:
        return L + CW + 60, tau < 3.8, 1 - ease(tau, 3.5, 3.8)
    return lerp(L + CW + 60, L, ease(tau, 3.8, 4.8)), False, 0.0


# --------------------------------------------------------------- drawing ---

# ------------------------------------------------------ cave-wall idiom ---
# Everything is painted as pigment on a mottled limestone wall: black and ochre
# silhouettes with soft dry edges, sprayed hand stencils, light incised lines.

BLK = (30, 24, 20)
OCH = (166, 102, 46)
RED = (122, 50, 32)
SCR = (236, 228, 210)      # incised line: the pale stone under the surface
STONE = (206, 197, 178)

_wall = None
_tex = None


def _noise(rs, w, h, cells_w, cells_h):
    a = rs.uniform(0, 1, (cells_h, cells_w)).astype(np.float32)
    return np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255


def wall():
    """Limestone: low and mid mottling, dark wavy bands top and bottom, a few old incisions."""
    global _wall, _tex
    if _wall is None:
        rs = np.random.RandomState(7)
        m = 0.55 * _noise(rs, W, H, 9, 6) + 0.3 * _noise(rs, W, H, 40, 24) + 0.15 * _noise(rs, W, H, 160, 90)
        wash = np.zeros((H, W), np.float32)
        yy, xx = np.mgrid[0:H, 0:W]
        for cx, cy, rx, ry, g in ((760, 120, 260, 50, 0.22), (300, 330, 380, 40, 0.10), (90, 200, 120, 140, 0.12), (620, 400, 300, 30, 0.08)):
            wash += g * np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
        base = np.array(STONE, np.float32)[None, None, :] * (0.78 + 0.36 * m[..., None] - wash[..., None])
        y = np.arange(H)[:, None]
        x = np.arange(W)[None, :]
        top = 58 + 16 * np.sin(x / 140.0) + 8 * np.sin(x / 47.0 + 1)
        bot = 472 + 12 * np.sin(x / 120.0 + 2) + 6 * np.sin(x / 37.0)
        dark = np.clip((top - y) / 22, 0, 1) + np.clip((y - bot) / 18, 0, 1)
        dark = np.clip(dark, 0, 1)[..., None]
        band = np.array((96, 86, 76), np.float32)[None, None, :] * (0.8 + 0.4 * m[..., None])
        img = base * (1 - dark * 0.9) + band * dark * 0.9
        im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im, "RGBA")
        r = random.Random(3)
        for cx, cy, rx, ry, a0, a1 in ((640, 210, 150, 60, 3.3, 6.0), (380, 160, 90, 40, 3.0, 6.2), (720, 330, 120, 50, 3.6, 5.9)):
            arc = [(cx + rx * math.cos(a0 + (a1 - a0) * q / 30), cy + ry * math.sin(a0 + (a1 - a0) * q / 30)) for q in range(31)]
            d.line(arc, fill=SCR + (120,), width=2)  # older incised animal backs, half lost
        for _ in range(26):  # old scratches, like the wall's earlier marks
            x0, y0 = r.uniform(0, W), r.uniform(80, 440)
            pts = [(x0, y0)]
            a = r.uniform(0, 6.28)
            for _k in range(r.randint(3, 8)):
                a += r.uniform(-0.6, 0.6)
                pts.append((pts[-1][0] + 14 * math.cos(a), pts[-1][1] + 14 * math.sin(a)))
            d.line(pts, fill=SCR + (90,), width=1)
        for _ in range(60):  # pigment speckle at right, like a dotted herd
            px, py = r.gauss(880, 40), r.gauss(150, 28)
            d.ellipse([px, py, px + r.uniform(2, 4), py + r.uniform(2, 4)], fill=BLK + (150,))
        _wall = im
        tex = 0.55 + 0.45 * (0.6 * _noise(rs, W, H, 300, 170) + 0.4 * _noise(rs, W, H, 60, 34))
        _tex = Image.fromarray((tex * 255).clip(0, 255).astype(np.uint8), "L")
    return _wall


def paint(ink, sheet, soft=1.1):
    """Lay the sheet onto the wall as pigment: soft edge, stone grain showing through."""
    a = sheet.img.getchannel("A").filter(ImageFilter.GaussianBlur(soft))
    a = ImageChops.multiply(a, _tex)
    rgb = sheet.img.convert("RGB")
    ink.img.paste(rgb, (0, 0), a)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


_stencils = {}


def stencil(color=BLK, seed=1, s=1.0, ang=0.0):
    """A sprayed negative hand: dense dots around the hand shape, none inside it."""
    key = (color, seed, s, ang)
    if key in _stencils:
        return _stencils[key]
    sz = int(120 * s)
    hand = Image.new("L", (sz, sz), 0)
    d = ImageDraw.Draw(hand)
    c = sz / 2
    d.ellipse([c - 20 * s, c - 6 * s, c + 20 * s, c + 30 * s], fill=255)
    for k, (fa, fl) in enumerate(((-0.95, 26), (-0.35, 36), (0.0, 40), (0.33, 36), (0.68, 28))):
        a = fa - math.pi / 2 + (0.9 if k == 0 else 0)
        bx, by = c + math.cos(a + 0.0) * 14 * s, c + 4 * s + math.sin(a) * 14 * s
        tx, ty = bx + math.cos(a) * fl * s, by + math.sin(a) * fl * s
        d.line([(bx, by), (tx, ty)], fill=255, width=int(11 * s))
        d.ellipse([tx - 5.5 * s, ty - 5.5 * s, tx + 5.5 * s, ty + 5.5 * s], fill=255)
    hand = hand.rotate(math.degrees(ang), resample=Image.BICUBIC)
    halo = hand.filter(ImageFilter.MaxFilter(int(17 * s) | 1)).filter(ImageFilter.GaussianBlur(9 * s))
    rs = np.random.RandomState(seed)
    dots = (rs.uniform(0, 1, (sz, sz)) < 0.32).astype(np.float32)
    h = np.asarray(halo, np.float32) / 255
    inside = np.asarray(hand.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    al = np.clip(h * 1.6, 0, 1) * (0.35 + 0.65 * dots) * (1 - inside)
    im = Image.new("RGBA", (sz, sz), color + (0,))
    im.putalpha(Image.fromarray((al * 235).astype(np.uint8), "L"))
    _stencils[key] = im
    return im


def ptext(sheet, xy, s, size, color=BLK, anchor="la", kind="serif"):
    sheet.text(xy, s, kind, size, color, anchor=anchor)


def scratch(ink, pts, width=1.6, alpha=220):
    """Incised line: a pale groove with a faint dark lip."""
    ink.line([(x + 1, y + 1) for x, y in pts], (90, 80, 70), width, alpha=alpha // 3)
    ink.line(pts, SCR, width, alpha=alpha)


# --------------------------------------------------------------- drawing ---

def backdrop(ink, sheet):
    ink.paste(wall())
    # ground: a painted line over an incised groove
    scratch(ink, [(0, G + 2), (W, G + 2)], 2.0)
    sheet.line([(0, G), (W, G)], BLK, 3.0, amount=1.4)
    # the station, in the same pigment: incised service door, ochre bench, black bell
    scratch(ink, [(480, G), (480, G - 160), (560, G - 160), (560, G)], 2.2)
    scratch(ink, [(486, G), (486, G - 154), (554, G - 154), (554, G)], 1.2, 150)
    sheet.circle(548, G - 80, 3.5, fill=BLK, color=None, width=0)
    ptext(sheet, (520, G - 186), "service", 16, RED, anchor="mm")
    bx = 885
    sheet.stroke([(bx - 75, G - 44), (bx + 75, G - 44)], OCH, 9)
    sheet.stroke([(bx - 75, G - 74), (bx + 75, G - 74)], OCH, 8)
    for px in (bx - 62, bx + 62):
        sheet.stroke([(px, G - 74), (px, G)], BLK, 5)
    # ruler: pigment dots every half metre, a big dot each metre
    for k in range(17):
        x = X0 + k * PX / 2
        r = 4 if k % 2 == 0 else 2.2
        sheet.circle(x, G + 14, r, fill=BLK, color=None, width=0)
        if k % 2 == 0:
            ptext(sheet, (x, G + 22), f"{k // 2}", 14, BLK, anchor="ma")
    ink.paste(stencil(RED, 4, 0.72, -0.3), (712, G - 185))   # the goal: a red hand over the bench
    ink.paste(stencil(BLK, 9, 0.7, 0.25), (140, 200))        # the maker's hand at the start
    return bx


def bell(sheet, swing=0.0):
    bx, by = 885, 250
    sheet.line([(bx, 222), (bx, 234)], BLK, 2.5)
    sheet.poly([(bx - 14 + 10 * swing, by + 16), (bx + 14 + 10 * swing, by + 16), (bx + 8, by - 12), (bx - 8, by - 12)], fill=BLK, color=BLK, width=2)


def crate(sheet, L, bottom):
    """The load: an ochre block with a black contour; the sealed envelope on top."""
    x0, x1, y1, y0 = L, L + CW, bottom, bottom - CH
    sheet.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill=OCH, color=BLK, width=4)
    sheet.stroke([(x0 + 6, y0 + 28), (x1 - 6, y0 + 26)], RED, 4)
    sheet.stroke([(x0 + 6, y0 + 54), (x1 - 6, y0 + 52)], RED, 4)
    ex, ey = L + CW / 2, y0 - 13
    sheet.poly([(ex - 29, ey - 12), (ex + 29, ey - 12), (ex + 29, ey + 12), (ex - 29, ey + 12)], fill=(222, 210, 186), color=BLK, width=2.5)
    sheet.line([(ex - 29, ey - 12), (ex, ey + 2), (ex + 29, ey - 12)], BLK, 2)
    sheet.circle(ex, ey + 2, 4.5, fill=RED, color=None, width=0)


def pusher(sheet, hx, hy, phase, stoop=0.0, carrying=False, walk=False):
    """A black pigment figure, leaning into the push."""
    lean = math.radians(28 if not walk else 6)
    sx, sy = hx - (38 if not walk else 10), hy - 6 - (30 if walk else 0)
    sy += stoop * 26
    hipx, hipy = sx - math.sin(lean) * 52, sy + math.cos(lean) * 52
    head = (sx + math.sin(lean) * 16 + 3, sy - math.cos(lean) * 16 - 5)
    for sgn in (1, -1):
        a = math.sin(2 * math.pi * phase) * 0.45 * sgn
        footx = hipx + math.sin(a) * 40 - (14 if not walk else 0)
        kx, ky = lerp(hipx, footx, 0.5) + 6, lerp(hipy, G, 0.5) - 4 * abs(a)
        sheet.stroke([(hipx, hipy), (kx, ky), (footx, G - 2), (footx + 10, G - 2)], BLK, 7, taper=False)
    sheet.stroke([(sx, sy), (lerp(sx, hipx, 0.5) - 2, lerp(sy, hipy, 0.5)), (hipx, hipy)], BLK, 15, taper=False)
    tx, ty = (hx, hy + stoop * 62) if not carrying else (sx + 16, sy + 4)
    for off in (0, 5):
        ex, ey = lerp(sx, tx, 0.5) - 2, lerp(sy, ty, 0.5) + 8
        sheet.stroke([(sx, sy + off), (ex, ey + off), (tx, ty + off)], BLK, 5.5, taper=False)
    sheet.ellipse(head[0], head[1], 10, 12, fill=BLK, color=BLK, width=2, angle=lean)
    return (tx, ty)


def roller(sheet, x, a, alpha=255):
    cy = G - ROLL_R
    sheet.circle(x, cy, ROLL_R, fill=OCH + (alpha,), color=BLK, width=3, alpha=alpha)
    sheet.line([(x - math.cos(a) * ROLL_R * 0.8, cy - math.sin(a) * ROLL_R * 0.8), (x + math.cos(a) * ROLL_R * 0.8, cy + math.sin(a) * ROLL_R * 0.8)], BLK, 2.4, alpha=alpha)


def wheel(sheet, cx, cy, ang):
    sheet.circle(cx, cy, WHEEL_R, fill=None, color=BLK, width=5)
    for k in range(4):
        a = ang + k * math.pi / 4
        sheet.line([(cx - math.cos(a) * (WHEEL_R - 3), cy - math.sin(a) * (WHEEL_R - 3)), (cx + math.cos(a) * (WHEEL_R - 3), cy + math.sin(a) * (WHEEL_R - 3))], BLK, 2.4)
    sheet.circle(cx, cy, 5, fill=OCH, color=BLK, width=2)
    sheet.circle(cx, G, 3.5, fill=RED, color=None, width=0)


def cart(sheet, L, ang, wheel_rel=(14, 106)):
    by = G - 2 * WHEEL_R - 10
    for rel in wheel_rel:
        wheel(sheet, L + rel, G - WHEEL_R, ang)
        sheet.rect(L + rel - 5, by + 8, L + rel + 5, G - WHEEL_R, fill=BLK, color=BLK, width=1)
    sheet.poly([(L - 10, by), (L + CW + 10, by), (L + CW + 10, by + 10), (L - 10, by + 10)], fill=BLK, color=BLK, width=3)
    return by


def header(ink, sheet, num, title, sub, tau):
    ptext(sheet, (34, 70), num, 58, RED)
    ptext(sheet, (34 + 22 * len(num) + 30, 80), title, 36, BLK)
    ptext(sheet, (36 + 22 * len(num) + 30, 122), sub, 19, (52, 42, 34))
    # push clock: seven sprayed dots, one per second of push
    for k in range(7):
        x, y = W - 210 + k * 26, 96
        on = tau >= k + 1 or (k < tau < k + 1)
        sheet.circle(x, y, 8 if on else 3, fill=BLK if on else (90, 80, 70), color=None, width=0)
    ptext(sheet, (W - 210 - 14, 88), "push", 15, (70, 58, 48), anchor="ra")


def force_mark(sheet, hx, active=True):
    if not active:
        return
    y = HAND_Y - 70
    sheet.stroke([(hx - 96, y), (hx - 28, y)], RED, 6)
    sheet.poly([(hx - 30, y - 10), (hx - 12, y), (hx - 30, y + 10)], fill=RED, color=RED, width=2)


def readout(sheet, m):
    ptext(sheet, (36, 150), f"{m:4.2f} m", 30, BLK)
    for k in range(int(m * 2 + 1e-6)):   # one tally stroke per half metre
        x = 40 + k * 9 + (k // 5) * 8
        sheet.line([(x, 192), (x - 2, 214)], BLK, 3)


def caption(ink, s, alpha=1.0, color=SCR):
    if alpha > 0:
        ink.text((W / 2, 508), s, "serif", 23, color, anchor="mm", alpha=int(255 * alpha))


# --------------------------------------------------------------- picture ---

@film.picture
def frame(t, ink):
    ink._grain = True
    sheet = ink.layer()
    if t < TITLE[1]:
        ink.paste(wall())
        ptext(sheet, (W / 2, 210), "Teuf-Teuf", 84, BLK, anchor="mm")
        ptext(sheet, (W / 2, 280), "three ways to move a load: drag, roll, ride", 22, RED, anchor="mm")
        crate(sheet, W / 2 - CW / 2, 420)
        sheet.line([(260, 420), (700, 420)], BLK, 3)
        paint(ink, sheet)
        for k, (x, y, c, a) in enumerate(((120, 120, BLK, 0.2), (760, 100, RED, -0.4), (820, 300, BLK, 0.5))):
            ink.paste(stencil(c, 20 + k, 0.8, a), (x, y))
        caption(ink, "same load · same push · same seven seconds")
        return
    for name, (a, b) in SECT.items():
        if a <= t < b:
            section(ink, sheet, name, t - a - LEAD)
            fade = min(1, (t - a) / 0.2, (b - t) / 0.2)
            break
    else:
        if t < COUNTER[1]:
            counter(ink, sheet, t - COUNTER[0])
            fade = min(1, (t - COUNTER[0]) / 0.2, (COUNTER[1] - t) / 0.2)
        else:
            summary(ink, sheet, t - SUMMARY[0])
            fade = min(1, (t - SUMMARY[0]) / 0.25)
    if fade < 1:
        ink.d.rectangle([0, 0, W, H], fill=(96, 86, 76, int(255 * (1 - fade))))


def section(ink, sheet, name, tau):
    backdrop(ink, sheet)
    cap = None
    if name == "drag":
        m = drag_m(tau)
        L = X0 - CW + m * PX
        if m > 0.01:
            for k in range(3):
                scratch(ink, [(X0 - CW + 6, G - 3 - k * 3), (L + CW - 4, G - 3 - k * 3)], 1.2, 200)
        crate(sheet, L, G)
        slipping = 0.45 < ((clamp(tau, 0, PUSH) % (PUSH / 9)) / (PUSH / 9)) < 0.8 and 0 < tau < PUSH
        if slipping:
            for k in range(9):
                sheet.circle(L + 8 + k * 13 + ink.j(4), G - 5 + ink.j(3), 2 + ink.rng.random() * 2.5, fill=OCH, color=None, width=0)
        else:
            sheet.stroke([(L, G - 1), (L + CW, G - 1)], RED, 6, taper=False)
        pusher(sheet, L, HAND_Y, m * 2.2 if tau > 0 else 0)
        force_mark(sheet, L, 0 < tau < PUSH)
        header(ink, sheet, "I", "Drag", "the whole base rubs on the ground: it sticks, then slips", max(0, tau))
        readout(sheet, m)
        cap = ("1.2 m in seven seconds. Most of the push becomes scraping.", ease(tau, PUSH, PUSH + 0.2)) if tau > PUSH else None
    elif name == "roll":
        m = roll_load_m(tau)
        L = X0 - CW + m * PX
        rollers, picked = roll_sim(max(0, tau))
        for r in rollers:
            if not r["carried"]:
                roller(sheet, r["x"], r["a"])
                if 0 <= r["x"] - L <= CW:
                    sheet.circle(r["x"], G - 2 * ROLL_R, 3, fill=RED, color=None, width=0)
        crate(sheet, L, G - 2 * ROLL_R)
        hx, carrying, stoop = carry_pose(max(0, tau), L)
        hand = pusher(sheet, hx, HAND_Y, (hx - X0) / 60, stoop=stoop, carrying=carrying, walk=2.45 < tau < 4.8)
        if carrying:
            sheet.circle(hand[0] + 4, hand[1] + 8, ROLL_R, fill=OCH, color=BLK, width=3)
        force_mark(sheet, L, (0 < tau < 2.2) or (4.8 < tau < PUSH))
        header(ink, sheet, "II", "Roll on loose logs", "the logs move at half the load's speed and fall out behind", max(0, tau))
        readout(sheet, m)
        if 2.2 < tau < 4.8:
            cap = ("The back log has fallen out. The load waits while it is carried round.", 1)
        elif tau > 5.6:
            cap = ("…and it falls out again. 3.0 m.", ease(tau, 5.6, 5.8))
    else:
        m = wheel_m(tau)
        L = X0 - CW + m * PX
        rl, _ = roll_sim(PUSH)
        for r in rl:  # faint ghosts of the logs abandoned in II
            roller(sheet, r["x"], r["a"], alpha=70)
        ang = m * PX / WHEEL_R
        by = cart(sheet, L, ang)
        crate(sheet, L, by)
        pusher(sheet, L, HAND_Y, m * 0.9)
        force_mark(sheet, L, 0 < tau < 6.0)
        header(ink, sheet, "III", "Ride on axled wheels", "one point of contact per wheel · the axle carries the turn", max(0, tau))
        readout(sheet, m)
        sw = math.sin((tau - 6.0) * 14) * math.exp(-(tau - 6.0) * 2) * 0.5 if tau >= 6.0 else 0
        bell(sheet, sw)
        if 0.6 < tau < 4.2:
            cap = ("THE WHEEL:  “I’m a log that was asked to stay.”", ease(tau, 0.6, 0.8) * (1 - ease(tau, 4.0, 4.2)))
        elif tau >= 6.0:
            cap = ("8 m: the load reaches the bench, and the bell rings.", ease(tau, 6.0, 6.2))
    if name != "wheel":
        bell(sheet)
    paint(ink, sheet)
    if cap:
        caption(ink, *cap)


def counter_state(tau):
    x = 90 * smooth(clamp(tau / 1.6))
    L0 = X0 - CW
    L = L0 + x
    wx, angs = [], []
    for rel in (14, 106):
        free = L0 + rel + x / 2
        if rel - x / 2 < -10:
            free = L0 + rel + (rel + 10)
        wx.append(free)
        angs.append((free - (L0 + rel)) / WHEEL_R)
    drop = clamp((x - 2 * (14 + 10)) / 18)
    return L, wx, angs, drop


def counter(ink, sheet, tau):
    backdrop(ink, sheet)
    L, wx, angs, drop = counter_state(tau)
    by = G - 2 * WHEEL_R - 10
    for k in range(2):
        wheel(sheet, wx[k], G - WHEEL_R, angs[k])
        sheet.line([(wx[k] - 8, G - WHEEL_R - 34), (wx[k] + 8, G - WHEEL_R - 18)], RED, 3)
        sheet.line([(wx[k] + 8, G - WHEEL_R - 34), (wx[k] - 8, G - WHEEL_R - 18)], RED, 3)
    dy = drop * (G - 10 - by)
    bed = [(L - 10, by), (L + CW + 10, by), (L + CW + 10, by + 10), (L - 10, by + 10)]
    bed = [(x, y + dy * (1 - (x - L + 10) / (CW + 20))) for x, y in bed]
    sheet.poly(bed, fill=BLK, color=BLK, width=3)
    sub = ink.layer()
    crate(sub, L, by)
    rot = sub.img.rotate(math.degrees(math.atan2(dy, CW + 20)), resample=Image.BICUBIC, center=(L + CW + 10, by))
    sheet.img.paste(rot, (0, 0), rot)
    sheet.d = ImageDraw.Draw(sheet.img, "RGBA")
    pusher(sheet, L, HAND_Y, tau)
    header(ink, sheet, "×", "Counter-check: no axle", "same cart, same push · the wheels are loose discs under the bed", min(PUSH, tau))
    bell(sheet)
    paint(ink, sheet)
    caption(ink, "Without the axle the wheels lag, drop out behind: logs again.", ease(tau, 0.4, 0.6))


def summary(ink, sheet, tau):
    ink.paste(wall())
    ptext(sheet, (W / 2, 110), "same load · same push · seven seconds", 34, BLK, anchor="mm")
    rows = [("I drag", 1.2), ("II logs", 3.0), ("III wheels", 8.0)]
    for k, (name, m) in enumerate(rows):
        y = 200 + k * 92
        x0 = 260
        ptext(sheet, (60, y - 24), name, 28, RED)
        for q in range(17):
            sheet.circle(x0 + q * 35, y, 3.5 if q % 2 == 0 else 2, fill=BLK, color=None, width=0)
        grow = ease(tau, 0.2 + k * 0.4, 1.0 + k * 0.4)
        xm = x0 + m * 70 * grow
        sheet.stroke([(x0, y - 10), (xm, y - 10)], OCH, 8, taper=False)
        sheet.rect(xm - 40, y - 46, xm, y - 16, fill=OCH, color=BLK, width=3)
        ptext(sheet, (xm + 12, y - 40), f"{m * grow:3.1f} m", 22, BLK)
    paint(ink, sheet)
    ink.paste(stencil(RED, 30, 0.6, -0.2), (x0 + 8 * 70 + 50, 300))
    caption(ink, "order shown is mechanical, not a dated history")

@film.sound
def sound(mix):
    R = mix.rate
    # title: two engine puffs, "teuf-teuf"
    for k, at in enumerate((0.35, 0.75)):
        x = mix.band(mix.noise(0.16), 120, 900) * np.exp(-np.linspace(0, 7, int(0.16 * R)))
        mix.add(x, at, 0.5, -0.2 + 0.4 * k)
    mix.room(1.8, 28.5, gain=0.02)

    def speed_env(fn, a, b, rate=200):
        n = int((b - a) * R)
        ts = np.arange(0, b - a, 1 / rate)
        v = np.abs(np.gradient([fn(tt) for tt in ts], 1 / rate))
        return np.interp(np.arange(n) / R, ts, v)

    # I drag: scraping proportional to slip speed
    a = SECT["drag"][0] + LEAD
    v = speed_env(drag_m, 0, PUSH)
    scrape = mix.band(mix.noise(PUSH), 500, 3500) * (v / (v.max() + 1e-9)) ** 0.8
    mix.add(scrape, a, 0.35)
    per = PUSH / 9
    for k in range(9):
        mix.thud(a + k * per + per * 0.8, 90, 0.18)
    # II rollers: wooden rumble while moving, clonk as a roller falls out, steps during the carry
    a = SECT["roll"][0] + LEAD
    v = speed_env(roll_load_m, 0, PUSH)
    rum = mix.lowpass(mix.noise(PUSH, "brown"), 380) * (v / (v.max() + 1e-9))
    mix.add(rum / (np.abs(rum).max() + 1e-9), a, 0.4)
    prev = roll_sim(0)[0]
    out_seen = set()
    for k in range(1, int(PUSH * 40)):
        tt = k / 40
        rs, _ = roll_sim(tt)
        L = X0 - CW + roll_load_m(tt) * PX
        for i, r in enumerate(rs):
            if not r["carried"] and r["x"] - L < 0 and (i, tt > 4.8) not in out_seen:
                out_seen.add((i, tt > 4.8))
                mix.thud(a + tt, 160, 0.4)
                mix.click(a + tt, 0.2, 0, 1500)
    mix.steps(a + 2.5, a + 3.5, 0.25, 0.14, "stone", -0.2, 0.3)
    mix.step(a + 3.75, 0.3, 0.3, "wood")
    mix.steps(a + 3.85, a + 4.8, 0.25, 0.12, "stone", 0.3, -0.2)
    # III wheels: one soft tick per sixth of a revolution, a light rumble, the bell on arrival
    a = SECT["wheel"][0] + LEAD
    last = 0
    for k in range(int(6.0 * 100)):
        tt = k / 100
        spokes = int(wheel_m(tt) * PX / WHEEL_R / (math.pi / 3))
        if spokes > last:
            last = spokes
            mix.click(a + tt, 0.07, 0.1, 2500)
    v = speed_env(wheel_m, 0, 6.0)
    mix.add(mix.lowpass(mix.noise(6.0, "pink"), 250) * (v / v.max()), a, 0.12)
    mix.murmur(a + 0.7, 3.2, gain=0.07, pitch=210, pan=0.1)
    mix.bell(a + 6.0, 660, 3.0, 0.35, 0.4)
    # counter-check: rumble, then the rear drops and grinds
    a = COUNTER[0]
    mix.add(mix.lowpass(mix.noise(1.4, "brown"), 300) * np.hanning(int(1.4 * R)), a, 0.25)
    mix.thud(a + 0.95, 120, 0.5)
    mix.add(mix.band(mix.noise(0.6), 500, 3000) * np.exp(-np.linspace(0, 5, int(0.6 * R))), a + 1.0, 0.18)
    # summary: three plucks, one per bar
    for k, f in enumerate((196, 247, 330)):
        mix.pluck(SUMMARY[0] + 0.6 + 0.4 * k, f, 1.5, 0.16, -0.3 + 0.3 * k)
    mix.reverb(0.12)


if __name__ == "__main__":
    run(film)
