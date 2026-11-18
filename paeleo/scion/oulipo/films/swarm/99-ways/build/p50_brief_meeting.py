"""Page 50 Brief meeting (genre; medium: daumier-collage).

Played as romance: glances through the glass, a lingering thanks, the lost errand as a heart's distraction.
A love-story page: a masthead slip 'BRIEF MEETING / a love story at the ticket window', seven collage panels,
the centre one an oval close-up of the two faces with the pane of glass between them, romance narration on
pasted slips, cut rose-paper hearts. The four canon lines verbatim in the balloons; the outcome unchanged.
Reuses page 12's Daumier collage kit (build/daumier12.py, build/p12_loop.py): FORAGED CC0 lithographs by
Honore Daumier (Rijksmuseum via Commons) and the ANRC 1922 key cutout; HANDMADE: the cuts, the glass glints,
the rose-paper hearts (scissor polygons), balloons, slips and lettering in the shared pen hand on the LoC sheet.
Run: python3 -I p50_brief_meeting.py [--page-only]
"""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import daumier12 as D
import p12_loop as L

N, PID, TITLE = 50, "brief-meeting", "Brief meeting"
SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 1.6)
PAPER = np.array([246, 242, 230], np.float32)
ROSE = np.array([1.0, 0.66, 0.68], np.float32)
BCAP, CAP = 42, 31

BOX = {"P1": (110, 330, 1035, 920), "P2": (1075, 330, 2090, 920),
       "P3": (110, 960, 2090, 1460),
       "P4": (110, 1500, 1035, 2090), "P5": (1075, 1500, 2090, 2090),
       "P6": (110, 2130, 850, 2730), "P7": (890, 2130, 2090, 2730)}


def slip_hw(text, width):
    m = letter_left(wrap(text, CAP, width), CAP, 1)
    return m.shape[0] + 2 * 16 - int(CAP * 0.3), m.shape[1] + 2 * 22 - CAP


def cap_at(c, text, width, seed, corner="tl", inset=16):
    """a narration slip pasted in a panel corner, measured so it never runs off the panel"""
    hh, ww = slip_hw(text, width)
    h, w = c.shape[:2]
    x = inset if corner[1] == "l" else w - ww - inset
    y = inset if corner[0] == "t" else h - hh - inset
    return slip(c, int(x), int(y), wrap(text, CAP, width), CAP, seed, paper=PAPER, shadow=0.35)


def ground(w, h, fl_frac=0.82, dark=False):
    c = np.zeros((h, w, 3), np.float32)
    fl = int(h * fl_frac)
    wl = cv2.GaussianBlur(D.tone("wall", w, fl), (0, 0), 3.2)
    wl = wl.mean() + (wl - wl.mean()) * 0.75
    f = cv2.GaussianBlur(D.tone("floor", w, h - fl), (0, 0), 3.0)
    c[:fl] = np.clip(wl * (0.86 if dark else 1.02) + 6, 0, 255)[..., None] * D.TINT
    c[fl:] = f[..., None] * D.TINT
    return c, fl


def heart_poly(cx, cy, s, deg=0.0, n=40):
    pts = []
    a = math.radians(deg)
    for t in np.linspace(0, 2 * math.pi, n, endpoint=False):
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        x, y = x * s / 16, y * s / 16
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return pts


def heart(c, cx, cy, s, deg=0.0, seed=0):
    """a heart cut from rose paper: scissor-faceted outline (every 3rd point kept), rim and shadow"""
    P = heart_poly(cx, cy, s, deg, n=27)
    P = np.array(P, np.float32)
    x0, y0 = np.floor(P.min(0)).astype(int) - 2
    x1, y1 = np.ceil(P.max(0)).astype(int) + 2
    a = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(a, [np.int32(np.round((P - [x0, y0]) * 4))], 255, cv2.LINE_AA, shift=2)
    g = 236 + (np.random.RandomState(seed).rand(*a.shape) - 0.5) * 6
    piece = dict(gray=g.astype(np.float32), alpha=a, origin=(0, 0))
    D.glue(c, piece, penlib.T(float(x0), float(y0)), rim=3, tint=ROSE)


def cap(c, text, w, seed, x=18, y=16):
    return slip(c, x, y, wrap(text, CAP, w), CAP, seed, paper=PAPER, shadow=0.35)


def window(c, x, y, scale, fl, woman=None):
    L.PH = fl / 0.80
    return L.window_unit(c, x, y, scale, woman=woman)


# ------------------------------------------------------------------ panels
def P1(st):
    w, h = 925, 590
    c, fl = ground(w, h)
    L.desk(c, 60, 340, 380, fl + 8)
    L.memo_slip(c, 80, 372, cap=22, tilt=-5, seed=5011)
    rise = st.get("rise", 1.0)
    L.agent(c, (430 + 250 * rise, fl + 66), face=1, scale=0.40, head_deg=6)
    cap_at(c, "September, 1937. A quiet office; a memo: 4:15, the SERVICE door, the key in the cupboard. "
              "Nothing else on his mind.", 560, 5012)
    return c


def P2(st):
    w, h = 1015, 590
    c, fl = ground(w, h)
    window(c, 210, 330, 0.60, fl, woman=(-10, -1, 0.50))
    L.agent(c, (870, fl + 66), face=-1, scale=0.40, head_deg=-6)
    balloon(c, ["Pardon me —", "have you the", "right time?"], BCAP, (540, 190), (290, 290), 5021, tail_w=0.22)
    cap_at(c, "Then a voice at the glass, soft as the afternoon.", 300, 5022, corner="tr")
    return c


def P3(st):
    """the glance: an oval close-up, the two faces large, the pane between them"""
    w, h = 1980, 500
    c, fl = ground(w, h, fl_frac=0.99, dark=True)
    # the pane: the carriage window's pale paper as glass, its sash bars cut from the tunnel black
    L.set_piece(c, "pale", [(870, 0), (1110, 0), (1110, h), (870, h)], rim=0, shade=1.02)
    L.set_piece(c, "dark", [(848, 0), (880, 0), (880, h), (848, h)], rim=2)
    L.set_piece(c, "dark", [(1104, 0), (1134, 0), (1134, h), (1104, h)], rim=2)
    gap = st.get("gap", 0.0)
    # her (left, the platform side, looking right): head and shoulders cut from her figure
    wo = dict(L.WOMAN)
    a = wo["alpha"].copy()
    a[250:] = 0
    wo["alpha"] = a
    D.glue(c, wo, D.M_for(wo, (640 - gap, 290), 1.85, 0, False, anchor=(372, 700)), rim=3)
    # him (right, the office side, looking left): the whole pinned figure, close, cut by the panel's foot
    L.agent(c, (1400 + gap, 1300), face=-1, scale=1.30, head_deg=-6)
    gm = np.zeros(c.shape[:2], np.uint8)
    for k, (x, y, l) in enumerate([(905, 70, 120), (935, 50, 200), (1000, 290, 150), (1035, 270, 80)]):
        penlib.brush_line(gm, [(x, y + l), (x + l * 0.45, y)], 4, 5030 + k)
    comp(c, gm, np.array([252, 250, 244], np.float32), 0.85)
    if st.get("heart", True):
        heart(c, 990, 175, 56, -8, 5035)
    return c


def P4(st):
    w, h = 925, 590
    c, fl = ground(w, h)
    L.clock(c, 160, 170, 92)
    Mb, Mh = L.agent(c, (450, fl + 66), face=-1, scale=0.40, head_deg=st.get("look", 16))
    mouth = L.at_src(Mh, L.HEAD, (786, 642))
    balloon(c, ["Ten past four,", "by the clock."], BCAP, (700, 120), (mouth[0] + 6, mouth[1] + 4), 5041, tail_w=0.22)
    cap_at(c, "He gave her the hour. He would have given her the clock.", 330, 5042, corner="br")
    return c


def P5(st):
    w, h = 1015, 590
    c, fl = ground(w, h)
    window(c, 225, 330, 0.60, fl, woman=(-150, 1, 0.50))
    L.agent(c, (850, fl + 66), face=-1, scale=0.36, head_deg=-4)
    balloon(c, ["Much", "obliged!"], 48, (530, 175), (130, 280), 5051, tail_w=0.24)
    for k, (x, y, s, d) in enumerate([(420, 70, 24, -12), (372, 40, 18, 10), (334, 20, 12, -6)][:st.get("hearts", 3)]):
        heart(c, x, y, s, d, 5052 + k)
    cap_at(c, "Her thanks lingered... and then she was gone.", 290, 5056, corner="tr")
    return c


def P6(st):
    w, h = 740, 600
    c, fl = ground(w, h)
    L.cupboard(c, 230, 190, 180, 290, open_=st.get("open", True))
    L.agent(c, (560, fl + 64), face=-1, scale=0.38, head_deg=6)
    cap_at(c, "The cupboard. The key on its hook, just where it always was.", 400, 5061, corner="tr")
    return c


def P7(st):
    w, h = 1200, 600
    c, fl = ground(w, h)
    L.cupboard(c, 150, 190, 180, 290, open_=True)
    L.set_piece(c, "pale", [(1010, 300), (1140, 300), (1140, fl + 4), (1010, fl + 4)], shade=0.82)
    L.service_door(c, 1075, 365, 0.44)
    Mb, Mh = L.agent(c, (540, fl + 64), face=-1, scale=0.38, head_deg=-4)
    chin = L.at_src(Mh, L.HEAD, (800, 674))
    L.pencil(c, (chin[0] - 66, chin[1] + 70), (chin[0] - 1, chin[1] + 1), w=10, pale=True)
    head = L.at_src(Mh, L.HEAD, (850, 500))
    if st.get("drift", True):
        heart(c, head[0] + 80, head[1] - 30, 22, 14, 5071)
    if st.get("line", True):
        mouth = L.at_src(Mh, L.HEAD, (786, 642))
        balloon(c, ["Well, here I am...", "and what for?"], BCAP, (290, 90), (mouth[0] - 8, mouth[1] - 4), 5072, tail_w=0.22)
    cap_at(c, "But his heart was out on the platform; the errand had gone with her. "
              "The key stayed on its hook. The SERVICE door stayed closed.", 560, 5073, corner="tr")
    return c


PANELS = {"P1": P1, "P2": P2, "P3": P3, "P4": P4, "P5": P5, "P6": P6, "P7": P7}


def oval_mask(w, h):
    m = np.zeros((h, w), np.uint8)
    cv2.ellipse(m, (w * 2, h * 2), (w * 2 - 8, h * 2 - 8), 0, 0, 360, 255, -1, cv2.LINE_AA, shift=2)
    return m


def masthead(pg):
    t1 = letter(["BRIEF MEETING"], 92, 5090, weight=0.12)
    t2 = letter(["a love story at the ticket window"], 40, 5091)
    x = 110
    slip(pg, 300, 122, ["BRIEF MEETING"], 92, 5090, paper=PAPER, align="centre", min_w=1600, pad=(40, 18), shadow=0.4,
         weight=0.12)
    sub = np.zeros(pg.shape[:2], np.uint8)
    put_mask(sub, t2, W / 2, 292)
    comp(pg, sub, INK)
    heart(pg, 210, 200, 62, -12, 5093)
    heart(pg, 1990, 200, 62, 12, 5094)


def build(state=None, upto=7):
    state = state or {}
    pg = SHEET.copy()
    masthead(pg)
    order = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    rects = []
    for i, k in enumerate(order):
        if i >= upto:
            break
        x0, y0, x1, y1 = BOX[k]
        p = PANELS[k](state.get(k, {}))
        if k == "P3":
            m = oval_mask(x1 - x0, y1 - y0).astype(np.float32)[..., None] / 255
            pg[y0:y1, x0:x1] = pg[y0:y1, x0:x1] * (1 - m) + p * m
            om = np.zeros(pg.shape[:2], np.uint8)
            cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 - 4, (y1 - y0) / 2 - 4
            pts = [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 181)]
            penlib.brush_line(om, pts, 11, 5095)
            comp(pg, om, INK)
            slip(pg, 150, y0 - 6, wrap("Their eyes met through the pane, and for one moment the whole station stood still.",
                                       CAP, 520), CAP, 5036, paper=PAPER, shadow=0.4, tilt=-1.5)
        else:
            pg[y0:y1, x0:x1] = p
            rects.append(BOX[k])
    if rects:
        frame_border(pg, rects, w=11, seed=5096)
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
        # the glance through the glass, then the lingering thanks, then the errand drifting off as a heart
        states = [({"P3": {"gap": 120, "heart": False}}, 3), ({"P3": {"gap": 60, "heart": False}}, 3),
                  ({"P3": {"gap": 0, "heart": True}}, 3), ({"P5": {"hearts": 0}}, 5), ({"P5": {"hearts": 3}}, 5),
                  ({"P7": {"line": False, "drift": False}}, 7), ({"P7": {"line": True, "drift": True}}, 7)]
        save_beats(N, [np.asarray(Image.fromarray(finish(build(s, u))).resize((960, 1242), Image.LANCZOS)) for s, u in states])
        print("beats", len(states))
