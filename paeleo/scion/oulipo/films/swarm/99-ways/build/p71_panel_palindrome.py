"""Page 71 Panel palindrome (formal / Oulipian rule; medium: shadow-puppet).

Eight shadow-theatre strips stacked in one column, their heights symmetric about the page's middle
(355/292/292/280 | 280/292/292/355). Panel k and panel 9-k are played on the SAME set, cut once and laid
at the same x: P1/P8 the office master (desk, lamp, clock, cupboard, SERVICE door), P2/P7 the cupboard
wall, P3/P6 the ticket window close, P4/P5 window-clock-cupboard. The text of P1-P4 sits in the top half
of its strip, that of P5-P8 in the bottom half, and the corner numerals likewise, so the page folded across
its middle (the dashed fold line) lays each strip, its set, its figure and its words on its partner.
Black cut-paper puppets (b1m2 figure model, HANDMADE) on lit paper screens (page 05's screen); the brass
key is the ANRC 1922 key cutout (99-ways-template piece) as an amber gel.
Run: python3 -I p71_panel_palindrome.py [beats]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p05_noir as p5
from p05_noir import sil, far, window_letters, brass_key, paper_card, hook

N, PID, TITLE = 71, "panel-palindrome", "Panel palindrome"
SHEET = pen99.sheet99()
CAP = 44
BCAP = 48
X0, X1 = 110, 2090
HTS = [355, 292, 292, 280]
GUT, MIDGUT = 22, 50


def boxes():
    hs = HTS + HTS[::-1]
    out, y = {}, 110
    for i, h in enumerate(hs):
        out[f"P{i + 1}"] = (X0, y, X1, y + h)
        y += h + (MIDGUT if i == 3 else GUT)
    return out


BOXES = boxes()
YMID = (BOXES["P4"][3] + BOXES["P5"][1]) / 2          # the fold line
assert abs((BOXES["P1"][1] + BOXES["P8"][3]) / 2 - YMID) < 0.5


def scr(k, hot=(0.5, 0.5)):
    x0, y0, x1, y1 = BOXES[k]
    w, h = x1 - x0, y1 - y0
    return p5.screen(w, h, x0, y0, hot=hot, spread=1.3, slats=None), w, h


def mouth(x, floor, s, face, tilt=0):
    return (x + face * 66 * s, floor - 760 * s)


def numeral(img, k, top):
    """corner tab: P1-P4 top left, P5-P8 bottom left (mirrored across the fold)"""
    h = img.shape[0]
    y = 12 if top else h - 12 - 52
    slip(img, 14, y, [str(k)], 34, 7100 + k, paper=np.array([236, 226, 196], np.float32), pad=(20, 8), align="centre")


def text_slip(img, lines, x, top, seed, cap=CAP):
    """caption slip in the top half (P1-P4) or the bottom half (P5-P8) of the strip"""
    h = img.shape[0]
    hh = int(cap * 1.42) * (len(lines) - 1) + cap * 2
    y = 16 if top else h - 16 - hh
    return slip(img, x, y, lines, cap, seed)


# ------------------------------------------------------------ shared sets (cut once, laid twice)
def office_set(img, h, floor, open_deg, mm, key=True):
    """P1/P8 set: desk + lamp (left), clock, cupboard, SERVICE door."""
    sh = desk(300, floor - 112, 300, floor) + lamp(560, floor - 236, 122)
    sh += clock(990, 92, 40, hh=4, mm=mm, swing=-4 if mm == 9 else 4)
    sil(img, sh)
    cup(img, 1240, floor - 262, 160, 262, open_deg, 0.19 if key else None, card_seed=7111)
    sdoor(img, 1560, floor - 300, 150, 300, 7112)


def cup(img, x0, y0, w, h, open_deg, ks, card_seed):
    c, ins = cupboard(x0, y0, w, h, open_deg=open_deg)
    sil(img, c)
    if ins is not None and ks:
        ix0, iy0, ix1, iy1 = ins
        kx, ky = (ix0 + ix1) / 2, iy0 + (iy1 - iy0) * 0.50
        hook(img, kx, ky - 723 * ks / 2 - 10)
        brass_key(img, kx, ky, ks)
        paper_card(img, kx + 130 * ks, ky + 300 * ks, ["SERVICE"], 20, card_seed, tilt=8)
        sil(img, [s for s in c if s.role == "door"])


def sdoor(img, x0, y0, w, h, seed):
    sil(img, service_door(x0, y0, w, h))
    paper_card(img, x0 + w / 2, y0 + h * 0.15, ["SERVICE"], 26, seed)


def cupboard_wall(img, h, floor, open_deg, ks):
    """P2/P7 set: the desk's end (left), the cupboard, the SERVICE door."""
    sil(img, desk(-180, floor - 112, 320, floor, drawers=1))
    cup(img, 1180, floor - 250, 210, 250, open_deg, ks, 7121)
    sdoor(img, 1560, floor - 286, 160, 286, 7122)


def window_close(img, h, stranger_pose, seed):
    """P3/P6 set: the ticket window large at left."""
    x0, y0, ww = 150, 18, 430
    ws, sill = window(x0, y0, ww, h - 18, sill=y0 + 200, header=62)
    if stranger_pose is not None:
        far(img, stranger(x0 + ww / 2 + stranger_pose.get("dx", 0), sill + 26, face=stranger_pose.get("face", 1),
                          scale=0.64, glove=stranger_pose.get("glove", False), tilt=stranger_pose.get("tilt", 0)))
    sil(img, ws)
    window_letters(img, x0, y0, ww, 62, seed)


def window_clock(img, h, floor, stranger_pose, mm, seed):
    """P4/P5 set: small window (left), clock, the closed cupboard far right."""
    x0, y0, ww = 90, 20, 250
    ws, sill = window(x0, y0, ww, h - 20, sill=y0 + 150, header=58)
    if stranger_pose is not None:
        far(img, stranger(x0 + ww / 2 + stranger_pose.get("dx", 0), sill + 22, face=stranger_pose.get("face", 1),
                          scale=0.46, glove=stranger_pose.get("glove", False), tilt=stranger_pose.get("tilt", 0)))
    sil(img, ws)
    window_letters(img, x0, y0, ww, 58, seed)
    sil(img, clock(1000, 128, 38, hh=4, mm=mm, swing=5))
    cup(img, 1660, floor - 232, 170, 232, 0, None, 0)


# ------------------------------------------------------------ the eight strips
def P1(st):   # E0 the memo, at his desk
    img, w, h = scr("P1", hot=(0.35, 0.5))
    floor = h - 14
    office_set(img, h, floor, 0, 9)
    sil(img, agent(400, floor + 24, face=1, scale=0.30, seated=True, lean=8, tilt=16, sh=40, el=70, wr=-10,
                   pencil_deg=60, far_arm=(30, 60)))
    slip(img, 540, 30, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 28, 7113, tilt=-2,
         paper=np.array([240, 234, 214], np.float32), shadow=0.5)
    numeral(img, 1, True)
    return img


def P2(st):   # E0 risen, he sets off for the cupboard
    img, w, h = scr("P2", hot=(0.5, 0.5))
    floor = h - 12
    cupboard_wall(img, h, floor, 0, None)
    sil(img, agent(st.get("x", 980), floor, face=1, scale=0.30, legs=(24, -22), sh=-24, el=26, lean=4,
                   pencil_deg=200, far_arm=(24, 22)))
    text_slip(img, ["He sets off for the cupboard."], 130, True, 7123)
    numeral(img, 2, True)
    return img


def P3(st):   # E1 the question at the window
    img, w, h = scr("P3", hot=(0.3, 0.5))
    window_close(img, h, {"glove": True}, 7131)
    floor = h + 230
    sil(img, agent(1380, floor, face=-1, scale=0.58, sh=8, el=20, tilt=-2, pencil_deg=190))
    balloon(img, ["Pardon me — have", "you the right time?"], 42, (930, 82), (560, 120), 7132, tail_w=0.22)
    numeral(img, 3, True)
    return img


def P4(st):   # E2 he looks up at the clock: the answer
    img, w, h = scr("P4", hot=(0.45, 0.5))
    floor = h - 10
    window_clock(img, h, floor, {"glove": True}, 10, 7141)
    sil(img, agent(1240, floor, face=-1, scale=0.30, legs=(4, -4), sh=6, el=16, tilt=-26, pencil_deg=190, lean=-3))
    balloon(img, ["Ten past four,", "by the clock."], 40, (630, 96), mouth(1240, floor, 0.30, -1), 7142,
            tail_w=0.2)
    numeral(img, 4, True)
    return img


def P5(st):   # E3 the thanks; she turns from the glass
    img, w, h = scr("P5", hot=(0.45, 0.5))
    floor = h - 10
    window_clock(img, h, floor, {"face": -1, "dx": -26, "tilt": -6}, 10, 7151)
    sil(img, agent(1240, floor, face=-1, scale=0.30, legs=(4, -4), sh=6, el=16, tilt=8, pencil_deg=190, lean=-1))
    balloon(img, ["Much", "obliged!"], 40, (630, h - 96), (230, h - 160), 7152, tail_w=0.26)
    numeral(img, 5, False)
    return img


def P6(st):   # E3 the window empty: the interruption is over
    img, w, h = scr("P6", hot=(0.3, 0.5))
    window_close(img, h, None, 7161)
    floor = h + 230
    sil(img, agent(1380, floor, face=1, scale=0.58, sh=-6, el=14, tilt=2, pencil_deg=200))
    text_slip(img, ["She has gone.", "Back to the errand."], 720, False, 7162)
    numeral(img, 6, False)
    return img


def P7(st):   # E4 he opens the cupboard: the key on its hook
    img, w, h = scr("P7", hot=(0.5, 0.5))
    floor = h - 12
    od = st.get("open", 112)
    cupboard_wall(img, h, floor, od, 0.19)
    th = math.radians(od)
    ex = 1180 + 210 * math.cos(th)
    sil(img, agent(980, floor, face=1, scale=0.30, legs=(10, -8), sh=72, el=-6, wr=0, pencil=False, lean=4))
    # the near hand reaching to the leaf's edge (a cut bar from his forward hand to the door)
    sil(img, [Shape(bar_pts((1040, floor - 165), (ex + 8, floor - 150), 16), "arm", smooth=False),
              Shape(circle_pts(ex + 10, floor - 150, 11, 10), "hand")])
    text_slip(img, ["The cupboard open: the key on its hook."], 130, False, 7171)
    numeral(img, 7, False)
    return img


def P8(st):   # E5 the forgetting; the key stays, the SERVICE door shut
    img, w, h = scr("P8", hot=(0.35, 0.5))
    floor = h - 14
    office_set(img, h, floor, 112, 11)
    ag_x = 1110
    sil(img, agent(ag_x, floor, face=1, scale=0.30, sh=40, el=128, wr=-14, pencil_deg=90, tilt=-4, lean=-2))
    if st.get("line", True):
        balloon(img, ["Well, here I am...", "and what for?"], BCAP, (680, h - 96), mouth(ag_x, floor, 0.30, 1), 7181,
                tail_w=0.2)
    numeral(img, 8, False)
    return img


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7), ("P8", P8)]


def fold_line(page):
    """dashed pen fold line across the middle gutter, 'fold' lettered at its left end"""
    m = np.zeros(page.shape[:2], np.uint8)
    y = int(round(YMID))
    lm = letter(["fold"], 26, 7190)
    put_mask(m, lm, 160, y)
    x = 220
    k = 0
    while x < X1:
        cv2.line(m, (x, y + (k % 2)), (min(x + 34, X1), y + ((k + 1) % 2)), 255, 4, cv2.LINE_AA)
        x += 58
        k += 1
    for xe in (X0 - 70, X1 + 30):   # fold ticks in the outer margins
        cv2.line(m, (xe, y), (xe + 40, y), 255, 4, cv2.LINE_AA)
    comp(page, m, INK, 0.85)


def build(upto=8, state=None):
    state = state or {}
    page = SHEET.copy()
    shown = []
    for i, (k, fn) in enumerate(PANELS):
        if i >= upto:
            continue
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))
        shown.append(BOXES[k])
    frame_border(page, shown, w=12, seed=7190)
    fold_line(page)
    return page


# ------------------------------------------------------------ the fold (beats)
def fold_frame(page_u8, deg, size=(960, 1242)):
    """The lower half lifted about the fold line and laid over the upper, backlit: silhouettes of both
    halves read through the paper (shadow-theatre light from behind)."""
    W0, H0 = size
    pg = cv2.resize(page_u8, size, interpolation=cv2.INTER_AREA).astype(np.float32)
    ym = YMID * H0 / 2850.0
    table = np.zeros_like(pg) + np.array([58, 52, 46], np.float32)
    out = table.copy()
    upper = pg[:int(round(ym))]
    out[:upper.shape[0]] = upper
    lower = pg[int(round(ym)):]
    Lh = lower.shape[0]
    th = math.radians(deg)
    c = math.cos(th)
    grow = 1 + 0.07 * math.sin(th)              # far edge nearer the eye: a little wider
    far_y = ym + Lh * c
    src = np.float32([[0, 0], [W0, 0], [W0, Lh], [0, Lh]])
    dx = (grow - 1) * W0 / 2
    dst = np.float32([[0, ym], [W0, ym], [W0 + dx, far_y], [-dx, far_y]])
    if deg > 90:
        # past upright we see the back of the sheet; backlit, its pictures show through, flipped
        paper = np.full_like(lower, 0) + np.array([226, 218, 200], np.float32)
        dark = 1 - lower.mean(axis=2, keepdims=True) / 235.0
        back = paper * (1 - 0.82 * np.clip(dark, 0, 1))
        img = back
    else:
        shade = 1 - 0.35 * math.sin(th)
        img = lower * shade
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, size, flags=cv2.INTER_LINEAR, borderValue=0)
    mask = cv2.warpPerspective(np.ones((Lh, W0), np.float32), M, size, flags=cv2.INTER_LINEAR)
    # paper shadow of the lifted half on the table / upper half
    if 5 < deg < 175:
        sh = cv2.GaussianBlur(mask, (0, 0), 14) * 0.35 * math.sin(th)
        out *= (1 - sh[..., None])
    if deg > 90:
        # backlit: the upper half's silhouettes also read through the laid sheet (multiply)
        top = out * (1 / 235.0)
        comp_img = warped * np.clip(0.35 + 0.65 * top, 0, 1)
        out = out * (1 - mask[..., None]) + comp_img * mask[..., None]
    else:
        out = out * (1 - mask[..., None]) + warped * mask[..., None]
    return np.clip(out, 0, 255)


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "ymid", YMID, BOXES)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = [fold_frame(img, d) for d in (0, 50, 88, 130, 180)]
        # last: the page laid flat again
        frames.append(cv2.resize(img, (960, 1242), interpolation=cv2.INTER_AREA).astype(np.float32))
        save_beats(N, frames)
