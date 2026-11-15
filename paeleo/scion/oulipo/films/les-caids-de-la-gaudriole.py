"""Les caïds de la gaudriole — a folded dialogue. Two open panels argue over a
borrowed key; one marked fold (fold back so A meets B) joins two existing text
fragments and the porter's hand to the key. Only ink already on the sheet."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from kit import *
from kit_comics import *

SLUG = "les-caids-de-la-gaudriole"
SW, SH = 2400, 840            # the printable sheet (strip) in px
PY0, PHT = 40, 760            # panel band
P1 = (0, 1170)
P2 = (1230, 2400)
A, B = 760, 1640              # fold back so A meets B
D = B - A                     # hidden width; right part moves by -D
M = (A + B) / 2               # the second crease, in the gutter's middle
FLOOR_Y = 600
LS = 44
BAL_Y = 120                   # balloon centre (panel coords)

U = 1.75                      # figure scale
PORTER_X = 556
# the porter's arm: computed once so the key in panel 2 can be registered to the hand
_probe = Ink(0, 0, (10, 10), boil=0)
_o = person(_probe, PORTER_X, 735, U, "porter", 1, arms={"front": (74, 84), "back": (-8, -4)})
HAND = _o["hands"]["front"]   # panel-1 coords == sheet x (panel 1 starts at 0)
KEY_Y = HAND[1]
KEY_BOW_X = HAND[0] + 8.5 * U + 9 * 2.6 - 4 + D   # bow meets the hand once folded


def bg(ink, w, h, x_off):
    station_bg(ink, w, h, FLOOR_Y, dado=380)


def panel1(ink, w, h):
    bg(ink, w, h, 0)
    person(ink, PORTER_X, 735, U, "porter", 1, mouth="shout", brows="angry", look=(1, 0),
           arms={"front": (74, 84), "back": (-8, -4)})
    # hidden band of panel 1: the visitor and her envelope
    person(ink, 1010, 735, 1.45, "visitor", -1, mouth="smile", brows="raised", look=(-1, 0),
           arms={"front": (40, 90), "back": (30, 80)},
           holding=lambda k, hf, hb: envelope_s(k, hf[0] - 6, hf[1] - 6, 90, 58))
    # the big balloon: fragment left of A + fragment in the band
    f = lfont(LS, "Bold")
    x0, x1 = 50, 1130
    _balloon_frame(ink, x0, x1, BAL_Y, tail=(PORTER_X + 20, 255))
    ink.d.text((A - 7, BAL_Y), "THE KEY IS", font=f, fill=INK, anchor="rm")
    ink.d.text((A + 7, BAL_Y), "MISSING!", font=f, fill=INK, anchor="lm")
    balloon(ink, 985, 224, "You borrowed it!", 28, tail=(800, 250), maxw=330)
    balloon(ink, 1020, 312, "This? Just a dull envelope.", 28, tail=(1000, 375), maxw=330)


def panel2(ink, w, h):
    ox = P2[0]
    bg(ink, w, h, ox)
    door_s(ink, 2060 - ox, FLOOR_Y, 150, 280, u=1.3)
    bell_s(ink, 2250 - ox, 210, 1.5)
    bench_s(ink, 2290 - ox, 735, 380, 1.4)
    # a key rack on the wall: one brass clip holds the key level, bow toward the band
    for px in (B + 60 - ox, B + 118 - ox):
        ink.rect(px - 6, KEY_Y + 2, px + 6, KEY_Y + 18, fill=BRASS, color=INK, width=2)
    key_shape(ink, KEY_BOW_X - ox, KEY_Y, 2.6)
    # hidden band of panel 2: the visitor shows empty hands
    person(ink, 1420 - ox, 735, U, "visitor", 1, mouth="open", brows="raised", look=(1, -0.3),
           arms={"front": (120, 150), "back": (-120, -150)})
    f = lfont(LS, "Bold")
    x0, x1 = 1250, 2370
    _balloon_frame(ink, x0 - ox, x1 - ox, BAL_Y, tail=(1440 - ox, 260))
    ink.d.text((B - 7 - ox, BAL_Y), "LOOK: NOTHING", font=f, fill=INK, anchor="rm")
    ink.d.text((B + 7 - ox, BAL_Y), "IN MY HAND.", font=f, fill=INK, anchor="lm")


def _balloon_frame(ink, x0, x1, cy, tail):
    """A wide speech balloon whose top and bottom run level through the fold lines."""
    rx, ry = (x1 - x0) / 2, 62
    cx = (x0 + x1) / 2
    pts = []
    for k in range(160):
        a = 2 * math.pi * k / 160
        c, s = math.cos(a), math.sin(a)
        pts.append((cx + rx * math.copysign(abs(c) ** (2 / 6), c), cy + ry * math.copysign(abs(s) ** (2 / 6), s)))
    tx, ty = tail
    b1, b2 = (tx - 22, cy + ry - 4), (tx + 22, cy + ry - 4)
    ink.d.polygon(pts, fill=PAGE)
    ink.d.polygon([b1, b2, (tx, ty)], fill=PAGE)
    ink.line(pts + [pts[0]], INK, 4, rough=False)
    ink.d.polygon([(b1[0] + 3, b1[1] - 6), (b2[0] - 3, b2[1] - 6), (tx, ty - 4)], fill=PAGE)
    ink.line([b1, (tx, ty), b2], INK, 4, rough=False)


def build_sheet():
    sheet = Ink(0, 0, (SW, SH), boil=0, wobble=0.8, seed=5)
    sheet.d.rectangle([0, 0, SW, SH], fill=PAGE)
    im1 = make_panel(P1[1] - P1[0], PHT, panel1, seed=1)
    im2 = make_panel(P2[1] - P2[0], PHT, panel2, seed=2)
    sheet.img.paste(im1, (P1[0], PY0))
    sheet.img.paste(im2, (P2[0], PY0))
    sheet.d = ImageDraw.Draw(sheet.img, "RGBA")
    # fold marks in the margins only
    for x, lab in ((A, "A"), (B, "B")):
        for y0, y1 in ((0, PY0 - 4), (PY0 + PHT + 4, SH)):
            for yy in range(int(y0), int(y1), 10):
                sheet.d.line([(x, yy), (x, min(y1, yy + 5))], fill=ACCENT, width=3)
        sheet.d.polygon([(x - 9, 0), (x + 9, 0), (x, 14)], fill=ACCENT)
        sheet.d.text((x + (-14 if lab == "A" else 14), 18), lab, font=lfont(22), fill=ACCENT, anchor="rm" if lab == "A" else "lm")
    sheet.d.text(((A + B) / 2, PY0 + PHT + 20), "FOLD BACK SO A MEETS B", font=lfont(18, "SemiBold"), fill=MUTED, anchor="mm")
    return sheet.img.convert("RGB")


SHEET = build_sheet()
SA = np.asarray(SHEET).astype(np.float32)
SHEET.save(HERE / "stills" / f"{SLUG}-sheet.png") if (HERE / "stills").exists() else None

# registration check: at the folded state the hand's right edge and the key bow meet at the seam
seam_gap = (KEY_BOW_X - 9 * 2.6 - D) - (HAND[0] + 8.5 * U)
assert abs(seam_gap) < 12, seam_gap


def folded(theta):
    """Two creases (valley at A, mountain at M): each reflection maps x -> 2f - x;
    composed they translate the right part by -2(M - A) = -D. Orthographic view."""
    c, s = math.cos(theta), math.sin(theta)
    h = D / 2
    ow = int(round(SW - D * (1 - c)))
    xs = np.arange(ow, dtype=np.float32)
    src = np.empty(ow, np.float32)
    shade = np.ones(ow, np.float32)
    depth = np.zeros(ow, np.float32)
    s1 = A + h * c
    s2 = A + 2 * h * c
    m0 = xs < A
    m1 = (xs >= A) & (xs < s1)
    m2 = (xs >= s1) & (xs < s2)
    m3 = xs >= s2
    src[m0] = xs[m0]
    if c > 1e-3:
        f1 = (xs[m1] - A) / (h * c)
        src[m1] = A + f1 * h
        depth[m1] = f1
        shade[m1] = 1 - 0.38 * s
        f2 = (xs[m2] - s1) / (h * c)
        src[m2] = M + f2 * h
        depth[m2] = 1 - f2
        shade[m2] = 1 - 0.12 * s
    src[m3] = xs[m3] + D * (1 - c)
    src = np.clip(src, 0, SW - 1)
    k = 1 - 0.10 * s * depth           # receding pleat shrinks a little
    ys = np.arange(SH, dtype=np.float32)[:, None]
    cy = SH / 2
    sy = np.clip(cy + (ys - cy) / k[None, :], 0, SH - 1)
    out = SA[sy.astype(np.int32), np.broadcast_to(src.astype(np.int32), (SH, ow))]
    outside = (sy != np.clip(cy + (ys - cy) / k[None, :], -1e9, 1e9))
    out = out * shade[None, :, None]
    img = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    # blank where perspective pulled the pleat inside its bounds
    return img, ow


# board canvas
CWID, CHGT = 3000, 1500
CX, CY = CWID / 2, CHGT / 2
BASE = Image.new("RGB", (CWID, CHGT), BOARD)


def canvas(theta):
    img, ow = folded(theta)
    cv = BASE.copy()
    x0 = int(CX - ow / 2)
    y0 = int(CY - SH / 2)
    sh = Image.new("L", cv.size, 0)
    ImageDraw.Draw(sh).rectangle([x0 + 14, y0 + 18, x0 + ow + 14, y0 + SH + 18], fill=150)
    cv.paste(Image.new("RGB", cv.size, (20, 18, 18)), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
    cv.paste(img, (x0, y0))
    return cv, x0, y0, ow


OPEN = canvas(0.0)
SHUT = canvas(math.pi / 2)


def sheet_box(state, x0, x1, y0=PY0, y1=PY0 + PHT, pad=0.03):
    _, ox, oy, _ = state
    return fit_box((ox + x0, oy + y0, ox + x1, oy + y1), pad=pad)


FULL_OPEN = sheet_box(OPEN, 0, SW, 0, SH, 0.02)
FULL_SHUT = sheet_box(SHUT, 0, SW - D, 0, SH, 0.06)
SEAM = sheet_box(SHUT, A - 330, A + 330, PY0, PY0 + 520, 0.02)

# timeline: (t0, t1, kind, args)
TITLE = 2.8
segs = []
t = TITLE
sh = Shots(start=0)
sh.add(FULL_OPEN, 2.2, 0)
VO = []
for x0, x1, who, line in ((0, 900, "porter", "The key is missing!"), (700, 1170, "visitor", "This? Just a dull envelope."),
                          (1230, 1900, "visitor", "Look: nothing in my hand."), (1700, 2400, None, "")):
    sh.add(sheet_box(OPEN, x0, x1), 2.9, 0.6)
    VO.append((sh.t - 2.9, who, line))
sh.add(FULL_OPEN, 2.6, 0.8)
OPEN_SHOTS = sh
T_FOLD1 = TITLE + sh.t
FOLD1 = 3.4
T_SHUT1 = T_FOLD1 + FOLD1
sh2 = Shots()
sh2.add(FULL_SHUT, 1.8, 0)
sh2.add(SEAM, 3.6, 1.0)
sh2.add(FULL_SHUT, 1.0, 0.9)
T_UN = T_SHUT1 + sh2.t
UNF = 2.0
T_RE = T_UN + UNF + 1.2
REF = 2.0
T_END = T_RE + REF
FINAL = 5.0
DUR = round(T_END + FINAL, 2)

film = Film(SLUG, seconds=DUR, boil=0, wobble=0)
grayscale_frames(film)
film.poster_at = T_SHUT1 + 3.0

_fold_cache = {}


def fold_frame(theta):
    key = round(theta, 3)
    if key not in _fold_cache:
        if len(_fold_cache) > 4:
            _fold_cache.clear()
        st = canvas(theta)
        box = lerp_box(FULL_OPEN, FULL_SHUT, theta / (math.pi / 2))
        _fold_cache[key] = view(st[0], box)
    return _fold_cache[key]


@film.picture
def frame(t, ink):
    if t < TITLE:
        ink.card("Les caïds de la gaudriole", "two panels, one marked fold · no new ink")
        if t > TITLE - 0.4:
            ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (t - TITLE + 0.4) / 0.4),))
        return
    if t < T_FOLD1:
        ink.paste(view(OPEN[0], OPEN_SHOTS.at(t - TITLE)))
        if t > T_FOLD1 - 2.0:
            ink.caption("fold back along the marks so that A meets B", min(1, (t - T_FOLD1 + 2.0) / 0.4), y=H - 30, size=20, kind="sans")
        return
    if t < T_SHUT1:
        th = (math.pi / 2) * smooth((t - T_FOLD1) / FOLD1)
        ink.paste(fold_frame(th))
        return
    if t < T_UN:
        ink.paste(view(SHUT[0], sh2.at(t - T_SHUT1)))
        return
    if t < T_UN + UNF:
        th = (math.pi / 2) * (1 - smooth((t - T_UN) / UNF))
        ink.paste(fold_frame(th))
        return
    if t < T_RE:
        ink.paste(view(OPEN[0], FULL_OPEN))
        return
    if t < T_END:
        th = (math.pi / 2) * smooth((t - T_RE) / REF)
        ink.paste(fold_frame(th))
        return
    ink.paste(view(SHUT[0], FULL_SHUT))
    a = min(1, (t - T_END) / 0.5)
    ink.caption(f"same ink · creases at x={A} and x={int(M)} · x > {B} moves to x - {D}", a, y=H - 26, size=17, kind="sans")


@film.sound
def sound(mix):
    mix.room(0, DUR, 0.03)
    for t0, who, line in VO:
        if who:
            voice(mix, TITLE + t0 + 0.3, line, 108 if who == "porter" else 182, -0.3 if who == "porter" else 0.3, 0.09)
    for t0, dur in ((T_FOLD1, FOLD1), (T_UN, UNF), (T_RE, REF)):
        mix.whoosh(t0 + 0.2, dur * 0.8, 0.10)
        for k in range(6):
            mix.click(t0 + 0.3 + k * dur * 0.11, 0.06, 0, 7000, 0.06)   # paper creak
        mix.click(t0 + dur - 0.05, 0.25, 0, 3000, 0.05)                    # crease lands
    mix.note(T_SHUT1 + 0.1, 196, 1.4, 0.10, 0, "tri")
    mix.bell(T_SHUT1 + 2.9, 523, 3.0, 0.12)
    mix.bell(T_END + 0.2, 392, 4.0, 0.10)
    mix.reverb(0.15)


if __name__ == "__main__":
    print("seam gap px", seam_gap, "dur", DUR)
    film.render()
