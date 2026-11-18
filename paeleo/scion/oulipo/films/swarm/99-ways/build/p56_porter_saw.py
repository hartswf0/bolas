"""Page 56 The porter saw (point of view; medium: daumier-collage).

A porter on the platform bench watches it all and gives his partial account in captions; he cannot see into
the cupboard. Every panel is seen from the platform, from his bench; the office is only what shows through
the ticket window, and the cupboard corner lies behind the wall pier beside it, out of his sight. The four
canon lines verbatim in the balloons; E4-E5 reported as he guesses them (the forgetting line heard from
behind the pier).
Reuses page 12's Daumier collage kit (build/daumier12.py, build/p12_loop.py): FORAGED CC0 lithographs by
Honore Daumier (Rijksmuseum via Commons). NEW cuts from the same 'Un premier voyage en chemin de fer' (1846):
the dozing gentleman's seated body and sleeping head, and the staring top-hatted man's wide-eyed head, glued
together as the PORTER (his top hat replaced by a HANDMADE cut-paper porter's cap with a brass badge).
HANDMADE: the cuts, the bench, the station front and pier, slips, balloons and lettering in the shared pen
hand, on the LoC 1934 sheet.
Run: python3 -I p56_porter_saw.py [--page-only]
"""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import daumier12 as D
import p12_loop as L

N, PID, TITLE = 56, "the-porter-saw", "The porter saw"
SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 1.6)
PAPER = np.array([246, 242, 230], np.float32)
BRASS = np.array([1.0, 0.84, 0.50], np.float32)
BCAP, CAP = 40, 31

# ------------------------------------------------------------------ new scissor cuts (source px of c4.jpg)
D.POLY["porter_body"] = ("voyage", [(1062, 808), (1110, 800), (1150, 770), (1182, 758), (1206, 785), (1218, 850), (1222, 950),
                                    (1222, 1050), (1216, 1150), (1210, 1250), (1196, 1300), (1170, 1330), (1080, 1390), (1000, 1405),
                                    (880, 1422), (780, 1440), (722, 1442), (712, 1400), (728, 1358), (770, 1312), (850, 1282),
                                    (918, 1255), (915, 1222), (930, 1190), (935, 1185), (952, 1015), (985, 1010), (1022, 1010),
                                    (1036, 950), (1046, 870)])
D.POLY["porter_doze"] = ("voyage", [(1012, 710), (1060, 702), (1120, 700), (1180, 708), (1190, 758), (1162, 808), (1100, 830),
                                    (1070, 832), (1032, 802), (1016, 752)])
D.POLY["porter_stare"] = ("voyage", [(472, 648), (530, 645), (592, 652), (600, 690), (598, 720), (585, 752), (565, 785),
                                     (525, 800), (490, 792), (474, 765), (466, 725), (466, 685)])
PBODY, PDOZE, PSTARE = D.poly_piece("porter_body"), D.poly_piece("porter_doze"), D.poly_piece("porter_stare")
NECK_BODY = (1112, 804)
NECK = {"doze": (1102, 826), "stare": (522, 796)}
TOP = {"doze": (1100, 706), "stare": (532, 648)}


def porter(c, seat, scale=0.62, head="stare", head_deg=0.0):
    """The porter, seated, facing right (toward the station front). `seat` = panel point where his seat (thigh
    underside below the hip) rests; body flipped from the print's left-facing dozer."""
    hip_src = np.array((1180.0, 1330.0))
    Mb = D.M_for(PBODY, seat, scale, 0, True, anchor=tuple(hip_src))
    D.glue(c, PBODY, Mb, rim=3)
    neck = L.at_src(Mb, PBODY, NECK_BODY)
    if head == "doze":
        piece, flip = PDOZE, True
    else:
        piece, flip = PSTARE, False
    hs = scale * (1.0 if head == "doze" else 0.92)
    Mh = D.M_for(piece, tuple(neck + np.array([4 * scale, 6 * scale])), hs, head_deg, flip, anchor=NECK[head])
    D.glue(c, piece, Mh, rim=3)
    top = L.at_src(Mh, piece, TOP[head])
    cap(c, top, 150 * hs, head_deg)
    return Mb, Mh


def cap(c, top, w, deg=0.0):
    """HANDMADE porter's cap: a crown cut from the tunnel black, a peak to the front (right), a brass badge."""
    x, y = float(top[0]), float(top[1]) + w * 0.10
    a = math.radians(deg)

    def rot(pts):
        return [(x + (px) * math.cos(a) - (py) * math.sin(a), y + (px) * math.sin(a) + (py) * math.cos(a)) for px, py in pts]
    crown = rot([(-0.52 * w, 0.02 * w), (-0.50 * w, -0.34 * w), (-0.30 * w, -0.46 * w), (0.36 * w, -0.46 * w),
                 (0.52 * w, -0.30 * w), (0.54 * w, 0.02 * w)])
    L.set_piece(c, "dark", crown, rim=3)
    peak = rot([(0.30 * w, -0.02 * w), (0.82 * w, 0.06 * w), (0.80 * w, 0.14 * w), (0.28 * w, 0.10 * w)])
    L.set_piece(c, "dark", peak, rim=2)
    band = rot([(-0.52 * w, -0.08 * w), (0.54 * w, -0.08 * w), (0.54 * w, 0.02 * w), (-0.52 * w, 0.02 * w)])
    L.set_piece(c, "mid", band, rim=0, shade=0.8)
    cx, cy = rot([(0.18 * w, -0.24 * w)])[0]
    r = 0.10 * w
    badge = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
    piece, (x0, y0) = D.shape_piece("pale", badge)
    D.glue(c, piece, penlib.T(x0, y0), rim=2, tint=BRASS)


def bench(c, x0, x1, seat_y, floor):
    """HANDMADE platform bench: slat seat and back cut from the carriage wall's crayon tone, iron legs from the black."""
    L.set_piece(c, "mid", [(x0, seat_y - 14), (x1, seat_y - 14), (x1 + 10, seat_y + 18), (x0 - 10, seat_y + 18)], shade=0.95)
    L.set_piece(c, "mid", [(x0 + 6, seat_y - 210), (x0 + 30, seat_y - 210), (x0 + 30, seat_y - 14), (x0 + 6, seat_y - 14)], shade=0.8)
    for lx in (x0 + 20, x1 - 40):
        L.set_piece(c, "dark", [(lx, seat_y + 18), (lx + 22, seat_y + 18), (lx + 26, floor), (lx - 4, floor)], rim=2)


def slip_hw(text, width, capsize=CAP):
    m = letter_left(wrap(text, capsize, width), capsize, 1)
    return m.shape[0] + 2 * 16 - int(capsize * 0.3), m.shape[1] + 2 * 22 - capsize


def cap_at(c, text, width, seed, corner="tl", inset=16):
    hh, ww = slip_hw(text, width)
    h, w = c.shape[:2]
    x = inset if corner[1] == "l" else w - ww - inset
    y = inset if corner[0] == "t" else h - hh - inset
    return slip(c, int(x), int(y), wrap(text, CAP, width), CAP, seed, paper=PAPER, shadow=0.35)


# ------------------------------------------------------------------ the station front seen from the bench
def platform_ground(w, h, fl_frac=0.86):
    """Outside: the station's clapboard front cut from the carriage wall's darker tone, the platform from the floor."""
    c = np.zeros((h, w, 3), np.float32)
    fl = int(h * fl_frac)
    wl = cv2.GaussianBlur(D.tone("mid", w, fl), (0, 0), 2.6)
    wl = wl.mean() + (wl - wl.mean()) * 0.6
    c[:fl] = np.clip(wl * 0.92 + 18, 0, 255)[..., None] * D.TINT
    # clapboard lines drawn in pen (the station's siding), faint
    m = np.zeros((h, w), np.uint8)
    for k, yy in enumerate(range(40, fl, 46)):
        penlib.brush_line(m, [(0, yy), (w, yy + 2)], 2, 5600 + k)
    comp(c, m, INK, 0.28)
    f = cv2.GaussianBlur(D.tone("floor", w, h - fl), (0, 0), 3.0)
    c[fl:] = f[..., None] * D.TINT
    return c, fl


def office_view(w, h, fl_frac=0.86):
    """Inside the office as it shows through the glass: the stairwell wall tone, lighter than the outside."""
    c = np.zeros((h, w, 3), np.float32)
    fl = int(h * fl_frac)
    wl = cv2.GaussianBlur(D.tone("wall", w, fl), (0, 0), 3.2)
    wl = wl.mean() + (wl - wl.mean()) * 0.7
    c[:fl] = np.clip(wl * 1.04 + 8, 0, 255)[..., None] * D.TINT
    f = cv2.GaussianBlur(D.tone("floor", w, h - fl), (0, 0), 3.0)
    c[fl:] = f[..., None] * D.TINT
    return c, fl


def ticket_window(c, box, inside, sign=True, pier=None):
    """Glue the office view into the window opening `box`, then the sash bars, sill and header slip in front.
    `pier`: x where the window's right jamb (a wall pier) begins; the office beyond it is hidden."""
    x0, y0, x1, y1 = box
    ow, oh = x1 - x0, y1 - y0
    c[y0:y1, x0:x1] = inside[:oh, :ow]
    # glass sheen: two pale pen glints
    gm = np.zeros(c.shape[:2], np.uint8)
    for k, (gx, gy, l) in enumerate([(x0 + ow * 0.12, y0 + oh * 0.18, 70), (x0 + ow * 0.18, y0 + oh * 0.12, 120)]):
        penlib.brush_line(gm, [(gx, gy + l), (gx + l * 0.45, gy)], 3, 5610 + k)
    comp(c, gm, np.array([252, 250, 244], np.float32), 0.55)
    # frame: jambs and head cut from the tunnel black, the centre mullion, the counter sill
    L.set_piece(c, "dark", [(x0 - 22, y0 - 22), (x1 + 22, y0 - 22), (x1 + 22, y0), (x0 - 22, y0)], rim=2)
    L.set_piece(c, "dark", [(x0 - 22, y0), (x0, y0), (x0, y1), (x0 - 22, y1)], rim=2)
    L.set_piece(c, "dark", [(x1, y0), (x1 + 22, y0), (x1 + 22, y1), (x1, y1)], rim=2)
    mx = x0 + ow * 0.5
    L.set_piece(c, "dark", [(mx - 7, y0), (mx + 7, y0), (mx + 7, y0 + oh * 0.20), (mx - 7, y0 + oh * 0.20)], rim=1)
    L.set_piece(c, "dark", [(x0, y0 + oh * 0.20 - 6), (x1, y0 + oh * 0.20 - 6), (x1, y0 + oh * 0.20 + 6), (x0, y0 + oh * 0.20 + 6)], rim=1)
    L.set_piece(c, "pale", [(x0 - 40, y1), (x1 + 40, y1), (x1 + 48, y1 + 26), (x0 - 48, y1 + 26)], shade=0.86)
    if sign:
        slip(c, int(x0 + ow / 2 - 140), int(y0 - 84), ["TICKET OFFICE"], 34, 5620, paper=PAPER, pad=(18, 8), shadow=0.4)


# ------------------------------------------------------------------ panels
BOX = {"P1": (110, 330, 2090, 960),
       "P2": (110, 1000, 1035, 1590), "P3": (1075, 1000, 2090, 1590),
       "P4": (110, 1630, 1035, 2190), "P5": (1075, 1630, 2090, 2190),
       "P6": (110, 2230, 760, 2730), "P7": (800, 2230, 1500, 2730), "P8": (1540, 2230, 2090, 2730)}
AS = 0.50          # the agent's scale inside the glass (waist up above the counter)


def inside_agent(inside, x, sill_in, face=-1, head_deg=0.0, body_deg=0.0, scale=AS):
    """the agent behind the counter: his waist (source y 1000) a little below the sill line"""
    return L.agent(inside, (x, sill_in + (1410 - 1000) * scale + 10), face=face, scale=scale, waist=True,
                   head_deg=head_deg, body_deg=body_deg)


def view(win, extra_w=0):
    inside, ifl = office_view(win[2] - win[0] + extra_w, win[3] - win[1] + 40)
    return inside, win[3] - win[1]           # sill line inside = the window's foot


def P1(st):
    """E0: from the bench, the window; inside, the agent at his desk with a slip of paper."""
    w, h = 1980, 630
    c, fl = platform_ground(w, h)
    win = (1000, 130, 1880, 500)
    inside, sill = view(win)
    L.clock(inside, 760, 130, 50)
    L.desk(inside, 60, sill - 40, 420, sill + 60)
    inside_agent(inside, 400, sill + 20, face=1, head_deg=24)
    L.memo_slip(inside, 40, sill - 100, cap=18, tilt=-7, seed=5630)
    ticket_window(c, win, inside)
    bench(c, 40, 560, fl - 36, fl + 40)
    porter(c, (300, fl - 40), scale=0.50, head=st.get("head", "stare"))
    cap_at(c, "I'm the porter here. Four o'clock or near it, I was on my bench by the ticket window, resting "
              "my feet. Through the glass I could see the agent at his desk, reading over some slip of paper.", 430, 5631,
           corner="tr", inset=0) if False else slip(c, 530, 20, wrap("I'm the porter here. Four o'clock or near it, I was on "
              "my bench by the ticket window, resting my feet. Through the glass I could see the agent at his desk, "
              "reading over some slip of paper.", CAP, 400), CAP, 5631, paper=PAPER, shadow=0.35)
    return c


def P2(st):
    """E0: he gets up and sets off across the office."""
    w, h = 925, 590
    c, fl = platform_ground(w, h)
    win = (300, 150, 880, 470)
    inside, sill = view(win)
    dx = st.get("walk", 1.0)
    inside_agent(inside, 180 + 200 * dx, sill, face=1, body_deg=5)
    ticket_window(c, win, inside, sign=False)
    bench(c, -20, 260, fl - 30, fl + 40)
    porter(c, (110, fl - 34), scale=0.44, head="stare")
    cap_at(c, "Then up he got, all business, like a man with somewhere to be.", 520, 5640, corner="tr")
    return c


def P3(st):
    """E1: a lady at the window; the question."""
    w, h = 1015, 590
    c, fl = platform_ground(w, h)
    win = (330, 150, 960, 470)
    inside, sill = view(win)
    inside_agent(inside, 430, sill, face=-1)
    ticket_window(c, win, inside, sign=False)
    # the woman stands at the glass on the platform side (the print's own figure), looking in
    Mwo = D.M_for(L.WOMAN, (440, 420), 0.66, 0, True)
    D.glue(c, L.WOMAN, Mwo, rim=3)
    porter(c, (90, fl - 34), scale=0.42, head="stare")
    balloon(c, ["Pardon me —", "have you the", "right time?"], BCAP, (790, 150), (510, 330), 5650, tail_w=0.22)
    cap_at(c, "A lady come up to the glass. I heard her plain:", 300, 5651, corner="tl")
    return c


def P4(st):
    """E2: he looks up at the office clock, and answers."""
    w, h = 925, 560
    c, fl = platform_ground(w, h)
    win = (270, 160, 890, 460)
    inside, sill = view(win)
    L.clock(inside, 470, 80, 58)
    Mb, Mh = inside_agent(inside, 260, sill, face=1, head_deg=-16)
    ticket_window(c, win, inside, sign=False)
    porter(c, (90, fl - 30), scale=0.42, head="stare", head_deg=-6)
    mouth = L.at_src(Mh, L.HEAD, (786, 642))
    balloon(c, ["Ten past four,", "by the clock."], BCAP, (690, 120), (win[0] + mouth[0] + 4, win[1] + mouth[1]), 5660,
            tail_w=0.22)
    cap_at(c, "He looked up at the office clock and told her.", 300, 5661, corner="br")
    return c


def P5(st):
    """E3: the thanks; she goes off down the platform past the bench."""
    w, h = 1015, 560
    c, fl = platform_ground(w, h)
    win = (360, 160, 980, 460)
    inside, sill = view(win)
    inside_agent(inside, 400, sill, face=-1)
    ticket_window(c, win, inside, sign=False)
    Mwo = D.M_for(L.WOMAN, (230, 380), 0.66, 0, False)
    D.glue(c, L.WOMAN, Mwo, rim=3)
    balloon(c, ["Much", "obliged!"], 46, (150, 125), (220, 260), 5670, tail_w=0.24)
    cap_at(c, "Off she went down the platform, right past my bench. That was that, I thought.", 420, 5671, corner="tr")
    return c


def P6(st):
    """E4 (guessed): he crosses to the far corner, behind the pier, where the bench can't see."""
    w, h = 650, 500
    c, fl = platform_ground(w, h)
    win = (40, 215, 430, 430)
    inside, sill = view(win, extra_w=300)
    walk = st.get("walk", 0.8)
    inside_agent(inside, 130 + 300 * walk, sill, face=1, body_deg=5, scale=0.42)
    ticket_window(c, win, inside, sign=False)
    cap_at(c, "Then he went off to the far corner. The cupboard's there, I reckon, but that's behind the wall "
              "from my bench.", 560, 5681, corner="tl")
    return c


def P7(st):
    """E5 (heard): only the wall pier; the line comes from behind it."""
    w, h = 700, 500
    c, fl = platform_ground(w, h)
    inside, sill = view((0, 110, 150, 380), extra_w=400)
    ticket_window(c, (0, 110, 150, 380), inside[:, 400:], sign=False)
    qm = np.zeros(c.shape[:2], np.uint8)
    put_mask(qm, letter(["? ?"], 110, 5690, weight=0.16), 450, 285)
    comp(c, qm, INK, 0.55)
    if st.get("line", True):
        balloon(c, ["Well, here I am...", "and what for?"], 38, (440, 110), (230, 250), 5691, tail_w=0.22)
    cap_at(c, "Couldn't see him. Heard him, though, talking to himself back there.", 560, 5692, corner="bl")
    return c


def P8(st):
    """the outcome as he can vouch for it: the window's far edge shows the SERVICE door, shut."""
    w, h = 550, 500
    c, fl = platform_ground(w, h)
    win = (250, 250, 530, 450)
    inside, sill = view(win)
    L.set_piece(inside, "pale", [(110, 40), (240, 40), (240, sill + 40), (110, sill + 40)], shade=0.80)
    L.service_door(inside, 175, 100, 0.34)
    ticket_window(c, win, inside, sign=False)
    porter(c, (80, fl + 150), scale=0.48, head="stare", head_deg=-4)
    cap_at(c, "Came out with nothing. The SERVICE door? Shut at a quarter past, shut at half past. "
              "That's all I saw.", 500, 5695, corner="tl")
    return c


PANELS = {"P1": P1, "P2": P2, "P3": P3, "P4": P4, "P5": P5, "P6": P6, "P7": P7, "P8": P8}


def masthead(pg):
    slip(pg, 330, 120, ["THE PORTER SAW"], 88, 5698, paper=PAPER, align="centre", min_w=1540, pad=(40, 16), shadow=0.4,
         weight=0.12)
    sub = np.zeros(pg.shape[:2], np.uint8)
    put_mask(sub, letter(["as told by the porter on the platform bench"], 38, 5699), W / 2, 290)
    comp(pg, sub, INK)


def build(state=None, upto=8):
    state = state or {}
    pg = SHEET.copy()
    masthead(pg)
    rects = []
    for i, k in enumerate(PANELS):
        if i >= upto:
            break
        x0, y0, x1, y1 = BOX[k]
        p = PANELS[k](state.get(k, {}))
        pg[y0:y1, x0:x1] = p[:y1 - y0, :x1 - x0]
        rects.append(BOX[k])
    frame_border(pg, rects, w=11, seed=5697)
    return pg


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if "--page-only" not in sys.argv:
        from PIL import Image
        # the porter dozing, then his head comes up; then the agent walks out of the porter's sight behind the pier,
        # and the forgetting is only heard
        states = [({"P1": {"head": "doze"}}, 1), ({"P1": {"head": "stare"}}, 1),
                  ({"P1": {"head": "stare"}, "P6": {"walk": 0.0}}, 6), ({"P1": {"head": "stare"}, "P6": {"walk": 0.55}}, 6),
                  ({"P1": {"head": "stare"}, "P6": {"walk": 1.0}}, 6),
                  ({"P1": {"head": "stare"}, "P7": {"line": False}}, 7), ({"P1": {"head": "stare"}}, 7), ({"P1": {"head": "stare"}}, 8)]
        save_beats(N, [np.asarray(Image.fromarray(finish(build(s, u))).resize((960, 1242), Image.LANCZOS)) for s, u in states])
        print("beats", len(states))
