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
SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 2.0)
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


def tone_tiled(name, w, h, k=1.7):
    """a crayon-tone patch enlarged uniformly (k) and mirror-tiled to w x h, so the crayon grain keeps its
    own proportion instead of being stretched into streaks"""
    sname, (x0, y0, x1, y1) = D.TONE[name]
    t = D.src(sname)[y0:y1, x0:x1]
    t = cv2.resize(t, (int((x1 - x0) * k), int((y1 - y0) * k)), interpolation=cv2.INTER_CUBIC)
    th, tw = t.shape
    big = np.block([[t, t[:, ::-1]], [t[::-1], t[::-1, ::-1]]])
    reps = (int(math.ceil(h / (2 * th))) + 1, int(math.ceil(w / (2 * tw))) + 1)
    return cv2.GaussianBlur(np.tile(big, reps)[:h, :w], (0, 0), 0.9)


def ground(w, h, fl_frac=0.82, dark=False):
    c = np.zeros((h, w, 3), np.float32)
    fl = int(h * fl_frac)
    wl = tone_tiled("wall", w, fl)
    wl = wl.mean() + (wl - wl.mean()) * 0.45
    f = tone_tiled("floor", w, h - fl, k=1.3)
    f = f.mean() + (f - f.mean()) * 0.8
    c[:fl] = np.clip(wl * (0.86 if dark else 1.02) + 6, 0, 255)[..., None] * D.TINT
    c[fl:] = f[..., None] * D.TINT
    sk = np.zeros(c.shape[:2], np.uint8)                 # the skirting: a pen line where wall meets floor
    penlib.brush_line(sk, [(0, fl), (w, fl)], 4, 5099 + w)
    comp(c, sk, INK, 0.7)
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


# ------------------------------------------------------------------ the agent re-cut (HANDMADE cuts of the CC0 print)
# His near arm (the one that held the cane in 'Il est devenu pro-pri-e-taire !') is cut off the body at the coat's
# edge and split at the elbow, so it can swing on two pinned joints: shoulder (712, 712), elbow (686, 850), source px.
SHOULDER, ELBOW, GRIP = (712.0, 712.0), (686.0, 850.0), (676.0, 962.0)
ARM_U_POLY = [(703, 690), (726, 696), (726, 760), (720, 800), (716, 856), (658, 858), (668, 820), (680, 790),
              (686, 750), (692, 718)]
ARM_F_POLY = [(660, 842), (716, 842), (713, 880), (705, 905), (707, 945), (703, 984), (688, 1005), (661, 997),
              (651, 962), (653, 930), (651, 890), (655, 860)]


def _poly_cut(poly):
    g = D.src("stair")
    P = np.array(poly, np.float32)
    x0, y0 = np.floor(P.min(0)).astype(int) - 2
    x1, y1 = np.ceil(P.max(0)).astype(int) + 2
    a = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(a, [np.int32(np.round((P - [x0, y0]) * 4))], 255, cv2.LINE_AA, shift=2)
    return dict(gray=g[y0:y1, x0:x1].copy(), alpha=a, origin=(int(x0), int(y0)))


ARM_U, ARM_F = _poly_cut(ARM_U_POLY), _poly_cut(ARM_F_POLY)
_bm = L.BODY["alpha"].copy()
_ox, _oy = L.BODY["origin"]
_cut = np.zeros_like(_bm)
for _P in (ARM_U_POLY, ARM_F_POLY):
    cv2.fillPoly(_cut, [np.int32(np.round((np.array(_P, np.float32) - [_ox, _oy]) * 4))], 255, cv2.LINE_AA, shift=2)
_cut[: int(700 - _oy)] = 0          # the shoulder cap stays on the body
BODY_NOARM = dict(L.BODY, alpha=np.where(_cut > 127, 0, _bm).astype(np.uint8))


def agent2(c, foot, face=-1, scale=0.40, head_deg=0.0, body_deg=0.0, sh=0.0, el=0.0, front=True, pencil=False):
    """the re-cut Daumier agent: body (arm cut away), head pinned at the collar, upper arm on the shoulder,
    forearm+hand on the elbow. sh/el in degrees (screen-clockwise in the print's own left-facing frame).
    Returns dict of canvas points: mouth, chin, grip, head."""
    flip = face > 0
    neck_src = np.array(D.ANCHOR["agent_body"], float)
    neck = np.array([foot[0], foot[1] - (1410.0 - neck_src[1]) * scale])
    Mb = D.M_for(BODY_NOARM, tuple(neck), scale, body_deg, flip, anchor=tuple(neck_src))
    Ms = Mb @ penlib.T(-_ox, -_oy)                     # source px -> canvas
    Mu = Ms @ penlib.about(SHOULDER, penlib.R(sh))
    Mf = Mu @ penlib.about(ELBOW, penlib.R(el))
    arms = [(ARM_U, Mu), (ARM_F, Mf)]

    def glue_arms():
        for pc, M in arms:
            D.glue(c, pc, M @ penlib.T(*pc["origin"]), rim=3, lift=2)
        for M, pv in ((Ms, SHOULDER), (Mu, ELBOW)):
            q = penlib.apply(M, pv)
            m = np.zeros(c.shape[:2], np.uint8)
            cv2.circle(m, (int(q[0] * 4), int(q[1] * 4)), int(max(2, 5 * scale / 0.4) * 4), 255, -1, cv2.LINE_AA, shift=2)
            comp(c, m, np.array([96, 92, 84], np.float32), 0.8)     # a paper brad in the print's crayon grey
    if not front:
        glue_arms()
    D.glue(c, BODY_NOARM, Mb, rim=3)
    hn = L.at_src(Mb, L.BODY, neck_src)
    Mh = D.M_for(L.HEAD, tuple(hn), scale, head_deg + body_deg, flip, anchor=D.ANCHOR["agent_head"])
    D.glue(c, L.HEAD, Mh, rim=3)
    if front:
        glue_arms()
    rec = {}
    if pencil:       # held in his fingers: laid across the fist (butt end in his palm), its point at the chin
        ch = L.at_src(Mh, L.HEAD, (796, 668))
        bt = penlib.apply(Mf, (GRIP[0] + 4, GRIP[1] + 42))
        crayon_pencil(c, tuple(bt), tuple(ch), w=max(8, 30 * scale))
        # the thumb closes over the pencil: the forearm piece's own thumb strip re-glued on top
        th = _poly_cut([(664, 940), (690, 936), (694, 958), (668, 962)])
        D.glue(c, th, Mf @ penlib.T(*th["origin"]), rim=0, shadow=False)
        rec.update(pencil=(list(map(float, bt)), list(map(float, ch))))
    return dict(rec, Mb=Mb, Mh=Mh, Mf=Mf, mouth=L.at_src(Mh, L.HEAD, (786, 642)), chin=L.at_src(Mh, L.HEAD, (800, 676)),
                head=L.at_src(Mh, L.HEAD, (850, 500)), grip=penlib.apply(Mf, GRIP))


def crayon_pencil(c, p, q, w=9):
    """a pencil cut from the prints' own crayon tones: shaft from the carriage wall's mid grey, sharpened cone from
    the window's pale paper, lead from the tunnel black; no colour added (the print's cream tint only)"""
    Lh = float(np.hypot(q[0] - p[0], q[1] - p[1]))
    ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
    M = penlib.T(p[0], p[1]) @ penlib.R(ang) @ penlib.T(0, -w / 2)
    tip = w * 1.8
    shaft, _ = D.shape_piece("mid", [(0, 0), (Lh - tip, 0), (Lh - tip, w), (0, w)])
    D.glue(c, shaft, M, rim=2, shade=0.80)
    cone, _ = D.shape_piece("pale", [(0, 0), (tip, w * 0.40), (tip, w * 0.60), (0, w)])
    D.glue(c, cone, M @ penlib.T(Lh - tip, 0), rim=1, shadow=False)
    lead, _ = D.shape_piece("dark", [(0, 0), (tip * 0.45, w * 0.40), (tip * 0.45, w * 0.60), (0, w)])
    D.glue(c, lead, M @ penlib.T(Lh - tip * 0.45, 0), rim=0, shadow=False)


def pose_grip(foot, face, scale, body_deg, sh, el):
    flip = face > 0
    neck_src = np.array(D.ANCHOR["agent_body"], float)
    neck = np.array([foot[0], foot[1] - (1410.0 - neck_src[1]) * scale])
    Mb = D.M_for(BODY_NOARM, tuple(neck), scale, body_deg, flip, anchor=tuple(neck_src))
    Ms = Mb @ penlib.T(-_ox, -_oy)
    return penlib.apply(Ms @ penlib.about(SHOULDER, penlib.R(sh)) @ penlib.about(ELBOW, penlib.R(el)), GRIP)


def solve_to(foot, face, scale, body_deg, target):
    best = None
    for sh in range(-120, 121, 3):
        for el in range(-170, 171, 3):
            d = float(np.hypot(*(pose_grip(foot, face, scale, body_deg, sh, el) - np.array(target))))
            if best is None or d < best[0]:
                best = (d, sh, el)
    return best


def full_door(c, x0, top, x1, floor):
    """the SERVICE door at full height: the CONCIERGE door's glazed upper half (cut from the 1846 print) above a
    panelled lower leaf cut from the carriage wall's crayon tone, in a casing cut from the tunnel black"""
    L.set_piece(c, "dark", [(x0 - 12, top - 12), (x1 + 12, top - 12), (x1 + 12, floor + 2), (x0 - 12, floor + 2)], rim=3)
    k = (x1 - x0) / L.DOOR["gray"].shape[1]
    uh = L.DOOR["gray"].shape[0] * k
    D.glue(c, L.DOOR, penlib.T(x0, top) @ penlib.S(k) @ penlib.T(0, 0), rim=0, shadow=False)
    L.set_piece(c, "mid", [(x0, top + uh - 2), (x1, top + uh - 2), (x1, floor), (x0, floor)], rim=0, shade=0.95)
    lh = floor - (top + uh)
    for px0, px1 in ((x0 + 14, (x0 + x1) / 2 - 7), ((x0 + x1) / 2 + 7, x1 - 14)):
        L.set_piece(c, "pale", [(px0, top + uh + 16), (px1, top + uh + 16), (px1, floor - 18), (px0, floor - 18)], rim=2,
                  shade=0.80)
    knob = [((x1 - 22) + 7 * math.cos(t), (top + uh + 10) + 7 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
    L.set_piece(c, "dark", knob, rim=1)
    slip(c, int(x0 + (x1 - x0) / 2 - 62), int(top + 18), ["SERVICE"], 30, 1260, paper=np.array([246, 242, 230], np.float32),
         pad=(14, 5), shadow=0.4)
    return (x0 - 12, top - 12, x1 + 12, floor + 2)


def solve_chin(scale, head_deg, face=-1, target_off=(-6, 14)):
    """search shoulder/elbow angles that bring the grip to just under the chin (in the print's own frame)"""
    best = None
    tmp = np.zeros((10, 10, 3), np.float32)
    neck_src = np.array(D.ANCHOR["agent_body"], float)
    Ms = penlib.T(-0.0, 0.0)
    chin = np.array([800 + (neck_src[0] - D.ANCHOR["agent_head"][0]), 676.0]) + np.array(target_off)
    for sh in range(-80, 81, 2):
        for el in range(-180, 181, 3):
            g = penlib.apply(penlib.about(SHOULDER, penlib.R(sh)) @ penlib.about(ELBOW, penlib.R(el)), GRIP)
            e = penlib.apply(penlib.about(SHOULDER, penlib.R(sh)), ELBOW)
            d = np.hypot(*(g - chin))
            if e[1] < SHOULDER[1] + 40:     # the elbow stays low, by his side
                continue
            if best is None or d < best[0]:
                best = (d, sh, el)
    return best


# ------------------------------------------------------------------ panels
def P1(st):
    """E0: he rises from the desk: the chair pushed back behind him, his body leaning forward over the desk,
    his near hand pressing on the desk top to push himself up"""
    w, h = 925, 590
    c, fl = ground(w, h)
    rise = st.get("rise", 1.0)
    # the chair he is getting up from, pushed back and tipped (cut from the carriage wall's mid tone)
    ch = penlib.about((150, fl + 4), penlib.R(-6))
    chair = [[(120, 250), (146, 250), (146, fl + 4), (120, fl + 4)], [(120, 372), (262, 372), (262, 392), (120, 392)],
             [(240, 392), (258, 392), (258, fl + 4), (240, fl + 4)]]
    for poly in chair:
        L.set_piece(c, "mid", [tuple(penlib.apply(ch, q)) for q in poly], rim=3, shade=0.78)
    top = 352
    foot = (330, fl + 66)
    bd = 12 * rise
    d, sh, el = solve_to(foot, 1, 0.42, bd, (478, top + 4))
    POSES["P1"] = dict(foot=foot, face=1, scale=0.42, head_deg=10, body_deg=bd, sh=sh, el=el)
    agent2(c, **POSES["P1"])
    L.desk(c, 470, top, 400, fl + 8)
    L.memo_slip(c, 560, 300, cap=20, tilt=-4, seed=5011)
    cap_at(c, "September, 1937. A quiet office; a memo: 4:15, the SERVICE door, the key in the cupboard. "
              "Nothing else on his mind. He gets up.", 860, 5012, corner="tl")
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
    # E2: his head tipped right back toward the clock, his arm half lifted to it
    POSES["P4"] = dict(foot=(640, fl + 66), face=-1, scale=0.40, head_deg=st.get("look", 30), sh=-38, el=-30)
    r = agent2(c, **POSES["P4"])
    mouth = r["mouth"]
    balloon(c, ["Ten past four,", "by the clock."], BCAP, (470, 104), (mouth[0] + 6, mouth[1] + 4), 5041, tail_w=0.22)
    cap_at(c, "He gave her the hour. He would have given her the clock.", 330, 5042, corner="bl")
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
    L.cupboard(c, 170, 190, 180, 290, open_=st.get("open", True))
    DOORS["P6"] = full_door(c, 384, 178, 524, fl + 4)
    CUPS["P6"] = (170 - 12, 190 - 24, 170 + 180 + 12, 190 + 290)
    L.agent(c, (640, fl + 64), face=-1, scale=0.38, head_deg=6)
    cap_at(c, "The cupboard. The key on its hook, just where it always was.", 400, 5061, corner="tl")
    return c


def P7(st):
    w, h = 1200, 600
    c, fl = ground(w, h)
    L.cupboard(c, 150, 190, 180, 290, open_=True)
    DOORS["P7"] = full_door(c, 364, 178, 504, fl + 4)
    CUPS["P7"] = (150 - 12, 190 - 24, 150 + 180 + 12, 190 + 290)
    # E5: his hand raised to his chin, the pencil held in his fingers, its point at his chin
    d, sh, el = solve_chin(0.42, -4, target_off=(-44, 78))
    POSES["P7"] = dict(foot=(650, fl + 64), face=-1, scale=0.42, head_deg=-4, sh=sh, el=el, pencil=True)
    r = agent2(c, **POSES["P7"])
    PENCIL["P7"] = r["pencil"]
    Mh = r["Mh"]
    head = r["head"]
    if st.get("drift", True):
        heart(c, head[0] - 30, head[1] - 70, 22, 14, 5071)
    if st.get("line", True):
        mouth = L.at_src(Mh, L.HEAD, (786, 642))
        balloon(c, ["Well, here I am...", "and what for?"], BCAP, (330, 88), (mouth[0] - 8, mouth[1] - 4), 5072, tail_w=0.22)
    cap_at(c, "But his heart was out on the platform; the errand had gone with her. "
              "The key stayed on its hook. The SERVICE door stayed closed.", 430, 5073, corner="tr")
    return c


POSES, DOORS, CUPS, PENCIL = {}, {}, {}, {}
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


def checks():
    """the repair's own checks: three distinct agent poses (not pixel-identical cutouts), the pencil over his hand
    and chin, the SERVICE door at least 90% of the cupboard's height"""
    out = {}
    def solo(k):
        c = np.zeros((700, 700, 3), np.float32) + 255
        q = dict(POSES[k], foot=(350, 660))
        agent2(c, **q)
        return (c.mean(2) < 250)
    base = solo("P1")
    for k in ("P4", "P7"):
        m = solo(k)
        out[k + "_vs_P1_silhouette_IoU"] = round(float((m & base).sum() / (m | base).sum()), 3)
        assert out[k + "_vs_P1_silhouette_IoU"] < 0.97
    c = np.zeros((700, 700, 3), np.float32) + 255
    q = dict(POSES["P7"], foot=(350, 660))
    r = agent2(c, **{**q, "pencil": False})
    g, ch = r["grip"], r["chin"]
    bt, tp = PENCIL["P7"]
    off = np.array([350 - POSES["P7"]["foot"][0], 660 - POSES["P7"]["foot"][1]])
    out["pencil_butt_to_grip_px"] = round(float(np.hypot(*(np.array(bt) + off - g))), 1)
    out["pencil_tip_to_chin_px"] = round(float(np.hypot(*(np.array(tp) + off - ch))), 1)
    assert out["pencil_butt_to_grip_px"] < 30 and out["pencil_tip_to_chin_px"] < 8
    for k in ("P6", "P7"):
        dx0, dy0, dx1, dy1 = DOORS[k]
        cx0, cy0, cx1, cy1 = CUPS[k]
        out[k + "_door_over_cupboard_height"] = round((dy1 - dy0) / (cy1 - cy0), 3)
        out[k + "_door_gap_to_cupboard_px"] = int(dx0 - cx1)
        assert out[k + "_door_over_cupboard_height"] >= 0.9
    out["poses"] = {k: {kk: (round(float(v), 1) if isinstance(v, (int, float)) else v) for kk, v in d.items()
                        if kk in ("head_deg", "body_deg", "sh", "el")} for k, d in POSES.items()}
    return out


if __name__ == "__main__":
    page = build()
    import json as _json
    print(_json.dumps(checks()))
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
