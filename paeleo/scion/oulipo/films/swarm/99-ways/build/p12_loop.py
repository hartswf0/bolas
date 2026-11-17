"""Page 12 Loop (time and order; medium: daumier-collage).

Eight collage panels in a ring round the memo, read clockwise from the top left; the eighth panel walks him
back to his desk, and its arrow runs up into the first, where he reads the memo again and sets off again.
FORAGED: Daumier lithographs (CC0, Rijksmuseum via Commons): the bourgeois of 'Il est devenu
pro-pri-e-taire !' (1846) is the agent; the old woman of 'Un premier voyage en chemin de fer' (1846) is the
stranger, her carriage window our ticket window, the young man's clasped hands his pondering hands; the
'CONCIERGE' door our SERVICE door; set pieces cut from the prints' own crayon tone (the stairwell wall and
floor, the carriage wall, the tunnel's black in 'L'entree du grand tunnel', 1843); the ANRC 1922 key
(99-ways-template cutout). HANDMADE: the cuts, the pencil, the clock dial lettering and hands, the slips,
balloons, arrows and lettering in the shared pen hand; the LoC 1934 sheet is the ground.
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import daumier12 as D

N, PID, TITLE = 12, "loop", "Loop"
SHEET = pen99.sheet99()
COLS = ((110, 737), (787, 1414), (1463, 2090))
ROWS = ((110, 950), (1000, 1840), (1890, 2730))
RING = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
CELL = {"P1": (0, 0), "P2": (1, 0), "P3": (2, 0), "P4": (2, 1), "P5": (2, 2), "P6": (1, 2), "P7": (0, 2), "P8": (0, 1)}
BOXES = {k: (COLS[c][0], ROWS[r][0], COLS[c][1], ROWS[r][1]) for k, (c, r) in CELL.items()}
CENTRE = (COLS[1][0], ROWS[1][0], COLS[1][1], ROWS[1][1])
PW, PH = 627, 840
BCAP = 44
CAP = 34

HEAD, BODY = D.poly_piece("agent_head"), D.poly_piece("agent_body")
WOMAN, HANDS = D.poly_piece("woman"), D.poly_piece("hands")
WINDOW, DOOR = D.poly_piece("window"), D.poly_piece("door")
AG_SCALE = 0.62


def ground():
    """Panel ground: the stairwell wall's crayon tone (stretched) above a strip of its floor, glued edge to edge."""
    c = np.zeros((PH, PW, 3), np.float32)
    fl = int(PH * 0.80)
    w = cv2.GaussianBlur(D.tone("wall", PW, fl), (0, 0), 3.2)
    w = w.mean() + (w - w.mean()) * 0.75
    f = cv2.GaussianBlur(D.tone("floor", PW, PH - fl), (0, 0), 3.0)
    c[:fl] = (np.clip(w * 1.02 + 6, 0, 255)[..., None] * D.TINT)
    c[fl:] = (f[..., None] * D.TINT)
    return c, fl


def agent(c, foot, face=1, head_deg=0.0, body_deg=0.0, scale=AG_SCALE, waist=False, head_dx=0.0, lift=0.0):
    """The Daumier bourgeois, glued: body, then his head pinned at the collar (so it can tilt).
    face=-1 is the print's own direction (looking left); +1 flips him to look right."""
    flip = face > 0
    # body: feet at `foot` (panel px); the source's feet are at y~1410, the neck at (812, 676)
    neck_src = np.array(D.ANCHOR["agent_body"], float)
    feet_src_y = 1410.0
    neck = np.array([foot[0], foot[1] - (feet_src_y - neck_src[1]) * scale])
    body = BODY
    if waist:
        a = body["alpha"].copy()
        cut = int(1000 - body["origin"][1])
        a[cut:] = 0
        body = dict(body, alpha=a)
    Mb = D.M_for(body, tuple(neck), scale, body_deg, flip, anchor=tuple(neck_src))
    D.glue(c, body, Mb, rim=3, lift=lift)
    hn = at_src(Mb, BODY, neck_src) + np.array([head_dx, 0])
    Mh = D.M_for(HEAD, tuple(hn), scale, head_deg + body_deg, flip, anchor=D.ANCHOR["agent_head"])
    D.glue(c, HEAD, Mh, rim=3, lift=lift)
    return Mb, Mh


def at_src(M, piece, p):
    """Canvas position of a SOURCE-pixel point of a glued piece."""
    return penlib.apply(M, (p[0] - piece["origin"][0], p[1] - piece["origin"][1]))


def pencil(c, p, q, w=7, pale=False):
    """A handmade pencil: a strip cut from the tunnel's black tone, with a paper-rim point.
    pale=True: the shaft cut from the window's pale paper (warmed), the point from the black, so it reads on a dark coat."""
    L = float(np.hypot(q[0] - p[0], q[1] - p[1]))
    ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
    M = penlib.T(p[0], p[1]) @ penlib.R(ang) @ penlib.T(0, -w / 2)
    if not pale:
        piece, (x0, y0) = D.shape_piece("dark", [(0, 0), (L, w * 0.3), (L, w), (0, w * 0.7)])
        D.glue(c, piece, M, rim=2)
        return
    tip = w * 1.9
    shaft, _ = D.shape_piece("pale", [(0, 0), (L - tip, 0), (L - tip, w), (0, w)])
    D.glue(c, shaft, M, rim=3, tint=np.array([1.0, 0.86, 0.50], np.float32))
    fer, _ = D.shape_piece("mid", [(0, 0), (w * 1.1, 0), (w * 1.1, w), (0, w)])
    D.glue(c, fer, M, rim=0, shadow=False)
    cone, _ = D.shape_piece("pale", [(0, 0), (tip, w * 0.40), (tip, w * 0.60), (0, w)])
    D.glue(c, cone, M @ penlib.T(L - tip, 0), rim=2, shadow=False, tint=np.array([1.0, 0.95, 0.85], np.float32))
    lead, _ = D.shape_piece("dark", [(0, 0), (tip * 0.45, w * 0.14), (tip * 0.45, w * 0.22), (0, w * 0.36)])
    D.glue(c, lead, M @ penlib.T(L - tip * 0.45, w * 0.32), rim=0, shadow=False)
    fm = np.zeros(c.shape[:2], np.uint8)
    a, b = penlib.apply(M, (w * 1.1, w * 0.5)), penlib.apply(M, (L - tip, w * 0.5))
    penlib.brush_line(fm, [tuple(a), tuple(b)], 2, 1209)
    comp(c, fm, INK, 0.55)


def set_piece(c, tone_name, poly, rim=3, shade=1.0, lift=0.0):
    piece, (x0, y0) = D.shape_piece(tone_name, poly)
    D.glue(c, piece, penlib.T(x0, y0), rim=rim, shade=shade, lift=lift)


def desk(c, x0, top, w, floor):
    set_piece(c, "mid", [(x0 - 14, top), (x0 + w + 14, top), (x0 + w + 14, top + 26), (x0 + w, top + 26), (x0 + w, floor),
                         (x0 + w - 30, floor), (x0 + w - 30, top + 110), (x0 + w * 0.42, top + 110), (x0 + w * 0.42, floor),
                         (x0, floor), (x0, top + 26), (x0 - 14, top + 26)])


def memo_slip(c, x, y, cap=26, tilt=-3, seed=1201):
    return slip(c, x, y, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], cap, seed, tilt=tilt,
                paper=np.array([246, 242, 230], np.float32), shadow=0.45)


def window_unit(c, x, y, scale, woman=None):
    """The carriage window as ticket window, the woman behind it, the counter sill across, the header slip."""
    Mw = D.M_for(WINDOW, (x, y), scale)
    D.glue(c, WINDOW, Mw, rim=3)
    w = WINDOW["gray"].shape[1] * scale
    h = WINDOW["gray"].shape[0] * scale
    if woman is not None:
        dx, face, s = woman
        Mwo = D.M_for(WOMAN, (x + dx, y + h * 0.05), s, 0, face > 0)
        D.glue(c, WOMAN, Mwo, rim=3)
    sill_y = y + h * 0.30
    set_piece(c, "dark", [(x - w / 2 - 30, sill_y), (x + w / 2 + 30, sill_y), (x + w / 2 + 30, sill_y + 30), (x - w / 2 - 30, sill_y + 30)])
    set_piece(c, "mid", [(x - w / 2 - 10, sill_y + 30), (x + w / 2 + 10, sill_y + 30), (x + w / 2 + 10, PH * 0.80 + 6), (x - w / 2 - 10, PH * 0.80 + 6)])
    slip(c, int(x - 150), int(y - h / 2 - 66), ["TICKET OFFICE"], 34, 1210, paper=np.array([246, 242, 230], np.float32),
         pad=(18, 8), shadow=0.4)
    return sill_y


def clock(c, cx, cy, r):
    """Clock: a ring cut from the tunnel's black, a dial cut from the window's pale paper; pen hands at 4:10."""
    ring = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 60, endpoint=False)]
    set_piece(c, "dark", ring)
    rr = r * 0.80
    dial = [(cx + rr * math.cos(t), cy + rr * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 60, endpoint=False)]
    set_piece(c, "pale", dial, rim=0)
    set_piece(c, "dark", [(cx - r * 0.5, cy + r * 0.9), (cx + r * 0.5, cy + r * 0.9), (cx + r * 0.5, cy + r * 2.2),
                          (cx, cy + r * 2.45), (cx - r * 0.5, cy + r * 2.2)])
    m = np.zeros(c.shape[:2], np.uint8)
    for k in range(12):
        a = math.radians(k * 30)
        penlib.brush_line(m, [(cx + rr * 0.78 * math.sin(a), cy - rr * 0.78 * math.cos(a)),
                              (cx + rr * 0.93 * math.sin(a), cy - rr * 0.93 * math.cos(a))], 6 if k % 3 == 0 else 3, 1220 + k)
    am, ah = math.radians(60), math.radians(125)
    penlib.brush_line(m, [(cx, cy), (cx + rr * 0.50 * math.sin(ah), cy - rr * 0.50 * math.cos(ah))], 10, 1240)
    penlib.brush_line(m, [(cx, cy), (cx + rr * 0.80 * math.sin(am), cy - rr * 0.80 * math.cos(am))], 6, 1241)
    comp(c, m, INK)


def cupboard(c, x0, y0, w, h, open_=True, key=True):
    """Cupboard body cut from the carriage wall's tone; inside, the tunnel's black; the leaf on its left jamb."""
    set_piece(c, "mid", [(x0 - 12, y0 - 24), (x0 + w + 12, y0 - 24), (x0 + w + 12, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h),
                         (x0, y0), (x0 - 12, y0)])
    if not open_:
        set_piece(c, "pale", [(x0 + 16, y0 + 16), (x0 + w - 16, y0 + 16), (x0 + w - 16, y0 + h - 16), (x0 + 16, y0 + h - 16)], shade=0.92)
        return None
    set_piece(c, "dark", [(x0 + 16, y0 + 16), (x0 + w - 16, y0 + 16), (x0 + w - 16, y0 + h - 16), (x0 + 16, y0 + h - 16)], rim=0)
    set_piece(c, "pale", [(x0 + 16, y0 + h * 0.62), (x0 + w - 16, y0 + h * 0.62), (x0 + w - 16, y0 + h * 0.62 + 12),
                          (x0 + 16, y0 + h * 0.62 + 12)], rim=0, shade=0.9)
    lw = w * 0.42
    set_piece(c, "pale", [(x0, y0), (x0 - lw, y0 - 22), (x0 - lw, y0 + h + 22), (x0, y0 + h)], shade=0.88, lift=2)
    if key:
        kx, ky = x0 + w * 0.5, y0 + h * 0.36
        ka = key_alpha()
        kg = key_gray()
        kp = dict(gray=penlib.levels(kg, 22, 212, 0.95) * 1.0, alpha=ka, origin=(0, 0))
        D.glue(c, kp, D.M_for(kp, (kx, ky + 50), 0.16), rim=3, tint=np.array([1.0, 0.86, 0.55], np.float32))
        slip(c, int(kx + 8), int(ky + 74), ["SERVICE"], 20, 1251, paper=np.array([246, 242, 230], np.float32), pad=(8, 3),
             tilt=10, shadow=0.3)
    return (x0, y0, w, h)


def service_door(c, x, y, scale):
    Md = D.M_for(DOOR, (x, y), scale)
    D.glue(c, DOOR, Md, rim=3)
    hw = DOOR["gray"].shape[1] * scale
    hh = DOOR["gray"].shape[0] * scale
    slip(c, int(x - hw * 0.36), int(y - hh * 0.47), ["SERVICE"], 30, 1260, paper=np.array([246, 242, 230], np.float32),
         pad=(14, 5), shadow=0.4)


def cap(c, text, w, seed, x=18, y=16, capsize=CAP):
    return slip(c, x, y, wrap(text, capsize, w), capsize, seed, paper=np.array([246, 242, 230], np.float32), shadow=0.35)


# ------------------------------------------------------------------ the eight panels
def P1(st):
    c, fl = ground()
    agent(c, (330, fl + 300), face=1, head_deg=st.get("read", 22), waist=True, scale=0.78)
    desk(c, 60, 560, 520, fl + 10)
    memo_slip(c, 90, 500, cap=22, tilt=-6)
    pencil(c, (470, 540), (520, 470))
    cap(c, "The memo again: 4:15, open the SERVICE door; the key's in the cupboard.", 560, 1271)
    return c


def P2(st):
    c, fl = ground()
    desk(c, -200, 520, 300, fl + 10)
    cupboard(c, 470, 300, 150, 360, open_=False)
    dx = st.get("walk", 0)
    agent(c, (300 + dx, fl + 40), face=1, body_deg=4)
    pencil(c, (238 + dx, 600), (226 + dx, 520))
    cap(c, "So he sets off for the key.", 560, 1272)
    return c


def P3(st):
    c, fl = ground()
    window_unit(c, 200, 360, 0.82, woman=(-20, 1, 0.70))
    Mb, Mh = agent(c, (500, fl + 70), face=-1, scale=0.56)
    balloon(c, ["Pardon me —", "have you", "the right time?"], 40, (430, 110), (250, 300), 1273, tail_w=0.22)
    return c


def P4(st):
    c, fl = ground()
    clock(c, 190, 190, 110)
    Mb, Mh = agent(c, (420, fl + 60), face=-1, head_deg=st.get("look", 16), scale=0.62)
    mouth = at_src(Mh, HEAD, (786, 642))
    balloon(c, ["Ten past four,", "by the clock."], 40, (190, 610), (mouth[0] - 4, mouth[1] + 6), 1274, tail_w=0.24)
    return c


def P5(st):
    c, fl = ground()
    window_unit(c, 200, 360, 0.82, woman=(-150, -1, 0.70))
    agent(c, (500, fl + 70), face=-1, scale=0.56)
    balloon(c, ["Much", "obliged!"], BCAP, (450, 110), (110, 300), 1275, tail_w=0.24)
    return c


def P6(st):
    c, fl = ground()
    cupboard(c, 250, 210, 230, 470, open_=st.get("open", True))
    agent(c, (470, fl + 50), face=-1, scale=0.60, head_deg=6)
    cap(c, "The cupboard: and there's the key, on its hook.", 560, 1276)
    return c


def P7(st):
    c, fl = ground()
    cupboard(c, 110, 260, 190, 420, open_=True)
    set_piece(c, "pale", [(462, 330), (580, 330), (580, PH * 0.80 + 4), (462, PH * 0.80 + 4)], shade=0.82)
    service_door(c, 520, 250, 0.50)
    Mb, Mh = agent(c, (390, fl + 70), face=-1, scale=0.56, head_deg=-4)
    chin = at_src(Mh, HEAD, (800, 674))
    # the pencil held up from his waistcoat, its point touching the chin (no grafted hands)
    pencil(c, (chin[0] - 92, chin[1] + 96), (chin[0] - 1, chin[1] + 1), w=12, pale=True)
    if st.get("line", True):
        mouth = at_src(Mh, HEAD, (786, 642))
        balloon(c, ["Well, here I am...", "and what for?"], 40, (300, 100), (mouth[0] - 10, mouth[1] - 6), 1277, tail_w=0.22)
    return c


def P8(st):
    c, fl = ground()
    desk(c, 40, 520, 300, fl + 10)
    dx = st.get("walk", 60)
    agent(c, (470 - dx, fl + 40), face=-1, body_deg=-4)
    cap(c, "And back he goes to his desk...", 560, 1278)
    return c


PANELS = {"P1": P1, "P2": P2, "P3": P3, "P4": P4, "P5": P5, "P6": P6, "P7": P7, "P8": P8}


def arrow(m, pts, w, seed, head=26):
    penlib.brush_line(m, pts, w, seed)
    p, q = np.array(pts[-2], float), np.array(pts[-1], float)
    d = (q - p) / (np.linalg.norm(q - p) + 1e-9)
    n = np.array([-d[1], d[0]])
    penlib.brush_line(m, [tuple(q - d * head + n * head * 0.6), tuple(q)], w, seed + 1)
    penlib.brush_line(m, [tuple(q - d * head - n * head * 0.6), tuple(q)], w, seed + 2)


def centre(page, seam=True):
    x0, y0, x1, y1 = CENTRE
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # the memo itself, large, pinned at the centre of the ring
    m = letter(["4:15 - open", "SERVICE door.", "Key in cupboard."], 46, 1290)
    slip(page, int(cx - m.shape[1] / 2 - 10), int(cy - 160), ["MEMO", "4:15 - open", "SERVICE door.", "Key in cupboard."], 46,
         1290, paper=np.array([246, 242, 230], np.float32), tilt=-3, shadow=0.45)
    mk = np.zeros(page.shape[:2], np.uint8)
    # a ring of arrows round the memo, clockwise
    R = 270
    for k in range(4):
        a0, a1 = -100 + k * 90 + 14, -100 + (k + 1) * 90 - 14
        pts = [(cx + R * math.cos(math.radians(a)), cy + 20 + R * 1.18 * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 18)]
        arrow(mk, pts, 7, 1291 + 5 * k)
    lm = letter(["round", "and round"], 34, 1300)
    put_mask(mk, lm, cx, y1 - 70)
    # gutter arrows between the panels, clockwise
    g = [((737, 530), (787, 530)), ((1413, 530), (1463, 530)), ((1776, 950), (1776, 1000)), ((1776, 1840), (1776, 1890)),
         ((1463, 2310), (1413, 2310)), ((787, 2310), (737, 2310)), ((424, 1890), (424, 1840))]
    # every gutter arrow as heavy as the seam arrow, reaching 22 px into each panel (about 94 px long),
    # so the bottom row's right-to-left order is unmistakable; a paper halo keeps them clear of the frame line
    am = np.zeros(page.shape[:2], np.uint8)
    for i, (a, b) in enumerate(g):
        sx = (1 if a[0] < b[0] else -1 if a[0] > b[0] else 0)
        sy = (1 if a[1] < b[1] else -1 if a[1] > b[1] else 0)
        arrow(am, [(a[0] - 22 * sx, a[1] - 22 * sy), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), (b[0] + 22 * sx, b[1] + 22 * sy)],
              11, 1310 + 3 * i, head=24)
    if seam:   # the loop seam: P8 back up into P1
        arrow(am, [(424, 1018), (424, 975), (424, 932)], 11, 1340, head=24)
    halo = cv2.dilate(am, np.ones((13, 13), np.uint8))
    hf = (halo.astype(np.float32) / 255)[..., None]
    page[:] = page * (1 - hf) + SHEET * hf
    comp(page, mk, INK)
    comp(page, am, INK)
    # ordinals: a small pasted paper disc with the panel's number at each panel's top-left corner
    for k, name in enumerate(RING, 1):
        bx0, by0 = BOXES[name][:2]
        cxn, cyn = bx0 + 6, by0 + 6
        dm = np.zeros(page.shape[:2], np.uint8)
        cv2.circle(dm, (int(cxn) * 4, int(cyn) * 4), 27 * 4, 255, -1, cv2.LINE_AA, shift=2)
        penlib.shadow_onto(page, dm, off=4, blur=3, opacity=0.35)
        comp(page, dm, np.array([246, 242, 230], np.float32))
        ring = np.zeros(page.shape[:2], np.uint8)
        cv2.circle(ring, (int(cxn) * 4, int(cyn) * 4), 27 * 4, 255, 4, cv2.LINE_AA, shift=2)
        comp(page, ring, INK)
        nm = np.zeros(page.shape[:2], np.uint8)
        put_mask(nm, letter([str(k)], 32, 1360 + k), cxn, cyn + 2)
        comp(page, nm, INK)


def build(state=None, seam=True):
    state = state or {}
    page = SHEET.copy()
    for k in RING:
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = PANELS[k](state.get(k, {}))
    frame_border(page, [BOXES[k] for k in RING], w=11, seed=1350)
    centre(page, seam)
    return page


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        # the loop seam: he walks back to the desk in P8, the seam arrow carries him up into P1, he reads again
        states = [({"P8": {"walk": 0}, "P1": {"read": 0}}, False), ({"P8": {"walk": 90}, "P1": {"read": 0}}, False),
                  ({"P8": {"walk": 170}, "P1": {"read": 0}}, False), ({"P8": {"walk": 170}, "P1": {"read": 0}}, True),
                  ({"P8": {"walk": 170}, "P1": {"read": 16}}, True), ({}, True)]
        save_beats(N, [np.asarray(Image.fromarray(finish(build(s, seam))).resize((960, 1242), Image.LANCZOS)) for s, seam in states])
