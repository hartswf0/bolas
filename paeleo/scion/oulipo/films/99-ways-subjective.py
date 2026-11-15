"""99 Ways to Tell a Story · Subjective — the template's office anecdote through the
clerk's own eyes. Same events E1-E5, same failed outcome. The question arrives from
outside the frame; the clock only enters the picture after a head turn."""
import importlib.util
import math
from PIL import Image, ImageDraw
from kit import *
from kit_comics import *

SLUG = "99-ways-subjective"
_spec = importlib.util.spec_from_file_location("ways_template", HERE / "99-ways-template.py")
TPL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(TPL)

CW, CH, G, PW = TPL.CW, TPL.CH, TPL.G, TPL.PW
LS = 36
SLEEVE = OLIVE
WALLC = (226, 214, 190)
DADO = (206, 190, 162)
FLOORC = (170, 136, 100)


def hand(ink, x, y, ang=0.0, s=1.0, palm=False):
    """A forearm coming up from the bottom edge to a hand at (x, y)."""
    ca, sa = math.cos(ang), math.sin(ang)
    bx, by = x - sa * 260 * s, y + ca * 260 * s
    wdt = 46 * s
    nx, ny = ca * wdt, sa * wdt
    ink.poly([(bx - nx, by - ny), (bx + nx, by + ny), (x + nx * 0.8, y + ny * 0.8), (x - nx * 0.8, y - ny * 0.8)],
             fill=SLEEVE, color=INK, width=4)
    ink.poly([(x - nx * 0.9, y - ny * 0.9), (x + nx * 0.9, y + ny * 0.9), (x + nx * 0.9 + sa * 8, y + ny * 0.9 - ca * 8),
              (x - nx * 0.9 + sa * 8, y - ny * 0.9 - ca * 8)], fill=SHIRT, color=INK, width=2.5)
    hx, hy = x + sa * 44 * s, y - ca * 44 * s
    ink.ellipse(hx, hy, 40 * s, 48 * s, fill=SKIN, color=INK, width=4, angle=ang)
    if palm:
        for k in range(4):
            fx = hx + (k - 1.5) * 18 * s * ca + sa * 40 * s
            fy = hy + (k - 1.5) * 18 * s * sa - ca * 40 * s
            ink.ellipse(fx, fy, 8 * s, 18 * s, fill=SKIN, color=INK, width=2.5, angle=ang)
    return hx, hy


def room_ahead(ink, w, h):
    """One-point view toward the far wall and the key cupboard."""
    vx, vy = w * 0.55, h * 0.42
    bw0, bh0, bw1, bh1 = 120, 60, w - 90, 380
    ink.d.rectangle([0, 0, w, h], fill=WALLC)
    ink.d.polygon([(0, h), (w, h), (bw1, bh1), (bw0, bh1)], fill=FLOORC)
    for k in range(-6, 8):
        ink.line([(vx + k * 120, h + 200), lerp2((vx + k * 120, h + 200), (vx, vy), 0.62)], (140, 108, 78), 2)
    ink.d.rectangle([bw0, bh0, bw1, bh1], fill=WALLC)
    ink.d.rectangle([bw0, bh1 - 80, bw1, bh1], fill=DADO)
    ink.line([(bw0, bh1 - 80), (bw1, bh1 - 80)], INK, 3)
    for p, q in (((0, 0), (bw0, bh0)), ((w, 0), (bw1, bh0)), ((0, h), (bw0, bh1)), ((w, h), (bw1, bh1))):
        ink.line([p, q], INK, 3)
    ink.line([(bw0, bh0), (bw0, bh1), (bw1, bh1), (bw1, bh0)], INK, 3)
    # the cupboard on the far wall
    cx0, cx1 = 330, 470
    ink.rect(cx0, 150, cx1, bh1, fill=(120, 88, 60), color=INK, width=4)
    ink.line([((cx0 + cx1) / 2, 150), ((cx0 + cx1) / 2, bh1)], INK, 3)
    ink.rect(cx0 + 30, 122, cx1 - 30, 144, fill=PAGE, color=INK, width=2)
    ink.d.text(((cx0 + cx1) / 2, 133), "KEYS", font=lfont(14, "Bold"), fill=INK, anchor="mm")


def cupboard_close(ink, w, h, open_=False):
    ink.d.rectangle([0, 0, w, h], fill=WALLC)
    ink.d.rectangle([0, h - 70, w, h], fill=DADO)
    x0, x1 = 90, w - 90
    ink.rect(x0, 20, x1, h + 20, fill=(120, 88, 60), color=INK, width=5)
    if not open_:
        ink.line([((x0 + x1) / 2, 20), ((x0 + x1) / 2, h)], INK, 4)
        for sx in (-26, 26):
            ink.circle((x0 + x1) / 2 + sx, 300, 11, fill=BRASS, color=INK, width=2)
        return
    ink.rect(x0 + 20, 40, x1 - 20, h + 20, fill=(70, 52, 40), color=INK, width=3)
    for k in range(3):
        for j in range(3):
            hx, hy = x0 + 120 + j * 140, 90 + k * 140
            ink.circle(hx, hy, 6, fill=PAGE, color=INK, width=1.5, rough=False)
            brass = (k, j) == (0, 1)
            key_shape(ink, hx, hy + 22, 2.0, angle=math.pi / 2, color=BRASS if brass else (176, 176, 168))
            if brass:
                ink.rect(hx + 16, hy + 40, hx + 96, hy + 68, fill=CAPTION, color=INK, width=2)
                ink.d.text((hx + 56, hy + 54), "SERVICE", font=lfont(16, "Bold"), fill=ACCENT, anchor="mm")


def s1(ink, w, h):
    ink.d.rectangle([0, 0, w, h], fill=(150, 110, 70))
    for k in range(6):
        ink.line([(0, 60 + k * 100), (w, 40 + k * 104)], (130, 94, 60), 2)
    # ledger
    ink.poly([(150, 70), (600, 60), (610, 360), (140, 372)], fill=PAGE, color=INK, width=4)
    ink.line([(375, 66), (376, 366)], RULE, 3)
    for k in range(8):
        y = 110 + k * 30
        ink.line([(170, y + 2), (355, y)], RULE, 2)
        ink.line([(395, y), (590, y - 2)], RULE, 2)
    # the errand note
    ink.poly([(430, 250), (690, 236), (700, 330), (440, 344)], fill=CAPTION, color=INK, width=3)
    ink.text((455, 258), "Fetch the", "serif", 36, (40, 50, 110))
    ink.text((455, 292), "service key!", "serif", 36, ACCENT)
    ink.line([(80, 330), (260, 230)], INK, 7)  # pen
    hand(ink, 170, 470, -0.25, 0.9)
    hand(ink, 560, 470, 0.25, 0.9)


def s2(ink, w, h):
    room_ahead(ink, w, h)
    hand(ink, 640, 560, 0.35, 0.8)
    balloon(ink, 190, 90, "What time is it?", LS, tail=(-4, 150), maxw=280)


def s3(ink, w, h):
    # head turned back: the left wall, the clock, the platform doorway
    ink.d.rectangle([0, 0, w, h], fill=WALLC)
    ink.d.rectangle([0, 360, w, 470], fill=DADO)
    ink.line([(0, 360), (w, 360)], INK, 3)
    ink.d.rectangle([0, 470, w, h], fill=FLOORC)
    ink.line([(0, 470), (w, 470)], INK, 3)
    ink.rect(40, 150, 200, 472, fill=(244, 236, 214), color=INK, width=4)
    ink.d.text((120, 180), "PLATFORM", font=lfont(16, "Bold"), fill=MUTED, anchor="mm")
    clock(ink, 400, 190, 110, 4 + 10 / 60)
    for k in range(7):  # the turn
        y = 80 + k * 70
        ink.line([(w - 120 + (k % 2) * 30, y), (w - 10, y + 8)], INK, 3)
    balloon(ink, 520, 400, "Ten past four!", LS + 2, tail=(470, h + 10), maxw=280)


def s4(ink, w, h):
    cupboard_close(ink, w, h, False)
    hand(ink, 300, 330, -0.15, 0.95)
    hand(ink, 450, 330, 0.15, 0.95)


def s5(ink, w, h):
    cupboard_close(ink, w, h, True)
    hand(ink, 60, 600, -0.6, 0.8)
    hand(ink, 680, 600, 0.6, 0.8)


def s6(ink, w, h):
    cupboard_close(ink, w, h, True)
    hand(ink, 180, 520, -0.35, 0.95, palm=True)
    hand(ink, 560, 520, 0.35, 0.95, palm=True)
    balloon(ink, 370, 370, "...what did I come for?", 34, tail=(370, 560), maxw=300, kind="thought")


SUBJ = [make_panel(CW, CH, f, seed=40 + i) for i, f in enumerate((s1, s2, s3, s4, s5, s6))]
SUBJ_EVENTS = [["E1"], ["E2"], ["E3"], ["E4"], ["E5"], ["E5"]]
assert [e for p in SUBJ_EVENTS for e in p][::1] and {e for p in SUBJ_EVENTS for e in p} == {e for e, _ in TPL.EVENTS}

board, RECTS = TPL.page(SUBJ, 3, "Subjective", "the same office, through the clerk's eyes")
FULL = fit_box(board.page(), pad=0.0)
BASEB = TPL.baseline_board()
THUMB_B = BASEB.img.crop(tuple(int(v) for v in BASEB.page())).resize((452, int(452 * BASEB.ph / BASEB.pw)), Image.LANCZOS)
THUMB_S = board.img.crop(tuple(int(v) for v in board.page())).resize((452, int(452 * board.ph / board.pw)), Image.LANCZOS)

TITLE = 2.6
sh = Shots()
sh.add(FULL, 2.0, 0)
VIS = []
for k, r in enumerate(RECTS):
    sh.add(fit_box(r, pad=0.03), 2.7, 0.5)
    VIS.append((sh.t - 2.7, k))
sh.add(FULL, 4.2, 0.8)
T_CMP = TITLE + sh.t
DUR = round(T_CMP + 7.0, 2)
film = Film(SLUG, seconds=DUR, boil=0, wobble=0)
film.poster_at = TITLE + VIS[2][0] + 1.5


@film.picture
def frame(t, ink):
    if t < TITLE:
        ink.card("99 Ways · Subjective", "the template's incident, through the clerk's eyes")
        if t > TITLE - 0.4:
            ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (t - TITLE + 0.4) / 0.4),))
        return
    if t < T_CMP:
        ink.paste(view(board.img, sh.at(t - TITLE)))
        return
    ink.fill(BOARD)
    a = min(1, (t - T_CMP) / 0.5)
    y = (H - THUMB_B.height) / 2 + 10
    ink.paste(THUMB_B, (18, y), alpha=a)
    ink.paste(THUMB_S, (W - 18 - THUMB_S.width, y), alpha=a)
    ink.label((18 + 226, y - 22), "objective · template", 15, PAGE, anchor="mm", alpha=int(255 * a))
    ink.label((W - 18 - 226, y - 22), "subjective · same E1-E5", 15, PAGE, anchor="mm", alpha=int(255 * a))
    ink.label((W / 2, y + THUMB_B.height + 26), "the question stays offscreen · the clock appears only after the turn · the key stays on its hook", 14, RULE, anchor="mm", alpha=int(255 * a))


@film.sound
def sound(mix):
    mix.room(0, DUR, 0.03)
    k = 0
    while TITLE + k < T_CMP:
        mix.click(TITLE + k, 0.03, -0.6, 3000, 0.02)  # the clock, heard before it is seen
        k += 1
    for t0, k in VIS:
        t = TITLE + t0
        if k == 0:
            mix.thud(t + 0.4, 90, 0.10)          # chair pushed back
        if k == 1:
            mix.steps(t + 0.1, t + 2.4, 0.45, 0.15, "wood")
            voice(mix, t + 0.4, "What time is it?", 108, -0.9, 0.09)   # offscreen, hard left
        if k == 2:
            mix.whoosh(t - 0.4, 0.4, 0.08, -0.5)
            voice(mix, t + 0.5, "Ten past four!", 150, 0.0, 0.09)
        if k == 3:
            mix.click(t + 0.4, 0.22, 0.2, 1500, 0.3)  # cupboard creak
    mix.reverb(0.15)


if __name__ == "__main__":
    print("dur", DUR)
    film.render()
