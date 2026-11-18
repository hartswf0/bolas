"""Page 72 Lift the flap (reader and object; medium: cut-paper).

Three cut-paper scenes stacked like the pages of a lift-the-flap book, each with one paper flap hinged on a strip of
tape, numbered and given a pull tab: flap 1 the ticket-window shutter (hinged at its top) hides the stranger, flap 2 a
paper disc (hinged at its top) hides the clock face, flap 3 the cupboard door itself (hinged on its LEFT jamb, as the
canon's cupboard) hides the key. The page shows all three lifted back, their plain backs and pull tabs turned toward
us, their shadows on the scene; the film (beats) lifts them in order 1, 2, 3.
HANDMADE cut paper (kit/cutpaper99.py), page 02's cut-paper agent and clock (kit/build_page02.py), page 64's
cut-paper stranger (build/p64_window_in_window.woman). A flap is a separately cut paper whose front and back are
cut here and laid by a projective warp about its hinge line (foreshortening only; no filter).
Run: python3 -I p72_lift_the_flap.py [beats]
"""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
from cutpaper99 import Cut, rect, ellipse, hexc  # noqa: E402
import build_page02 as p02  # noqa: E402
import p64_window_in_window as p64  # noqa: E402
from b1m2 import save_page, save_beats, slip, wrap  # noqa: E402

N, PID, TITLE = 72, "through-the-flap", "Lift the flap"
W, H = pen99.PAGE_W, pen99.PAGE_H
WALL, WAINS, RAIL, FLOOR = p02.WALL, p02.WAINS, p02.RAIL, p02.FLOOR
GLASS, WFRAME = p02.GLASS, p02.WFRAME
BRASS, BRASS2, TAG = "#c9a13b", "#9c7a2c", "#e9dcb6"
BACK = "#ddd0b0"          # the plain back of every flap
TAB = "#efe3c4"
TAPE = "#e9dfc8"
BOXES = {"A": (110, 110, 2090, 890), "B": (110, 930, 2090, 1640), "C": (110, 1680, 2090, 2730)}
BCAP, CAP = 46, 42
Q = ["Pardon me —", "have you the", "right time?"]
A_ = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]


def sz(k):
    x0, y0, x1, y1 = BOXES[k]
    return x1 - x0, y1 - y0


def caption(img, text, x, y, wmax, seed, cap=CAP):
    return slip(img, x, y, wrap(text, cap, wmax), cap, seed)


def frame(img, seed):
    h, w = img.shape[:2]
    m = penlib.border_mask((h, w), [(4, 4, w - 5, h - 5)], 9, seed)
    penlib.ink_onto(img, m)


# ------------------------------------------------------------------ flaps
class Flap:
    """A cut paper flap: front and back cut on their own sheets (same local coordinates: hinge along v=0 for a
    'top' flap, along u=0 for a 'left' flap), laid on the scene at angle theta (0 closed .. 180 laid back flat)."""

    def __init__(self, fw, fh, hinge, at, seed, front_fn, back_fn, shape="rect", tab=None):
        self.fw, self.fh, self.hinge, self.at = fw, fh, hinge, at      # at = hinge origin in scene px
        fr = Cut(fh, fw, seed, ground=BACK, fibre_off=(seed * 7, seed * 3))
        bk = Cut(fh, fw, seed + 1, ground=BACK, fibre_off=(seed * 5, seed * 11))
        m = np.zeros((fh, fw), np.uint8)
        if shape == "rect":
            body = rect(0, 0, fw - (tab[2] if tab and hinge == "left" else 0), fh - (tab[2] if tab and hinge == "top" else 0))
        else:   # disc: shape = ("disc", r); hinge chord at its top
            r = shape[1]
            body = ellipse(fw / 2, r, r, r)
        mm = fr.mask(body, jitter=0.7)
        m = np.maximum(m, mm)
        if tab:   # pull tab beyond the free edge: (centre along the edge, width, depth)
            c, tw, td = tab
            if hinge == "top":
                e = fh - td
                tp = np.float32([(c - tw / 2, e - 4), (c + tw / 2, e - 4), (c + tw / 2 - 8, e + td - 2), (c - tw / 2 + 8, e + td - 2)])
            else:
                e = fw - td
                tp = np.float32([(e - 4, c - tw / 2), (e - 4, c + tw / 2), (e + td - 2, c + tw / 2 - 8), (e + td - 2, c - tw / 2 + 8)])
            m = np.maximum(m, fr.mask(tp, jitter=0.6))
        self.mask = m
        front_fn(fr, fw, fh)
        back_fn(bk, fw, fh)
        # seen from behind after the lift, the back runs the other way about the hinge: it is drawn readable
        # (back_fn's coordinates) and laid reversed, so its numeral reads upright once the flap is back
        bk.img = np.ascontiguousarray(bk.img[::-1] if hinge == "top" else bk.img[:, ::-1])
        if tab:
            for cc in (fr, bk):
                cc.fill(cc.mask(tp, jitter=0.0, eps=0.5), TAB)
        self.front, self.back = fr.img, bk.img

    def quad(self, th):
        x, y = self.at
        c, s = math.cos(th), math.sin(th)
        if self.hinge == "top":
            d = 0.06 * self.fw * s
            return np.float32([[x, y], [x + self.fw, y], [x + self.fw + d, y + self.fh * c], [x - d, y + self.fh * c]])
        d = 0.06 * self.fh * s
        return np.float32([[x, y], [x + self.fw * c, y - d], [x + self.fw * c, y + self.fh + d], [x, y + self.fh]])

    def lay(self, img, deg):
        th = math.radians(deg)
        h, w = img.shape[:2]
        src = np.float32([[0, 0], [self.fw, 0], [self.fw, self.fh], [0, self.fh]])
        if self.hinge == "left":
            src = np.float32([[0, 0], [self.fw, 0], [self.fw, self.fh], [0, self.fh]])
        dst = self.quad(th)
        if abs(math.cos(th)) < 0.02:      # edge-on: a thin sliver of paper
            dst = self.quad(math.radians(88 if deg < 90 else 92))
        M = cv2.getPerspectiveTransform(src, dst)
        mk = cv2.warpPerspective(self.mask, M, (w, h), flags=cv2.INTER_LINEAR)
        s = math.sin(th)
        # its one shadow, down-right, longer while the flap stands up from the page
        off = (int(5 + 16 * s), int(7 + 20 * s))
        sh = np.zeros_like(mk)
        sh[off[1]:, off[0]:] = mk[:h - off[1], :w - off[0]]
        sh = cv2.GaussianBlur(sh, (0, 0), 4 + 8 * s).astype(np.float32) / 255 * (0.40 + 0.15 * s)
        img *= (1 - sh[..., None])
        if deg <= 90:
            face, shade = self.front, 1 - 0.30 * s
        else:
            face, shade = self.back, 0.86 + 0.14 * min(1, -math.cos(th) * 1.2)
        fw_ = cv2.warpPerspective(face, M, (w, h), flags=cv2.INTER_LINEAR)
        a = (mk.astype(np.float32) / 255)[..., None]
        img[:] = img * (1 - a) + fw_ * shade * a
        return img


def tape(img, p0, p1, wdt, seed):
    c = Cut(img.shape[0], img.shape[1], seed, ground=img)
    c.strip(p0, p1, wdt, TAPE, opacity=0.25)
    img[:] = img * 0.35 + c.img * 0.65      # the hinge tape is thin: the scene shows faintly through it


def lift_label(c, cx, cy, n, cap, seed, colour="#f4ead0"):
    c.piece(ellipse(cx, cy, cap * 0.95, cap * 0.95), colour)
    c.ink_letters([str(n)], cap * 1.0, (cx, cy + 2), seed)
    c.cut_letters(["LIFT"], cap * 0.62, (cx, cy + cap * 1.75), "#f4ead0", seed + 1)


# ------------------------------------------------------------------ the three scenes
def scene_A(st):
    """E0 the memo and the rising; E1 the window, where flap 1 hides the stranger"""
    w, h = sz("A")
    c = Cut(h, w, 7201, ground=WALL, fibre_off=(31, 17))
    c.piece(rect(-20, 520, w + 20, 690), WAINS, shadow=False)
    c.strip((-20, 520), (w + 20, 520), 18, RAIL)
    c.piece(rect(-20, 680, w + 20, h + 20), FLOOR)
    # desk with the memo (left)
    c.piece(rect(90, 520, 640, 556), "#5a3b24")
    c.piece(rect(110, 556, 620, 720), "#4a311f")
    for x in (120, 590):
        c.piece(rect(x, 700, x + 22, 760), "#3a2618")
    memo = np.float32([(170, 468), (520, 452), (526, 540), (176, 556)])
    c.piece(memo, "#f6f0dc", opacity=0.3)
    c.ink_letters(["4:15 - open SERVICE door.", "Key in cupboard."], 26, (348, 503), 7202)
    # the ticket window (right): frame, glass, counter; the stranger behind it
    wx0, wy0, wx1, wy1 = 1330, 340, 1890, 620
    c.piece(rect(wx0 - 40, 240, wx1 + 40, 330), "#4a3220")
    c.cut_letters(["TICKET OFFICE"], 44, ((wx0 + wx1) / 2, 286), "#efe0b0", 7203)
    c.piece(rect(wx0 - 30, 330, wx1 + 30, wy1 + 10), WFRAME)
    c.piece(rect(wx0, wy0, wx1, wy1), GLASS, shadow=False)
    p64.woman(c, 1600, 800, 52)
    c.piece(rect(wx0 - 60, wy1 - 6, wx1 + 60, wy1 + 34), "#4a3220")           # counter
    c.piece(rect(wx0 - 30, wy1 + 34, wx1 + 30, h + 20), WFRAME)
    # the agent, risen, walking from the desk (toward the right of the room)
    p02.agent(c, 800, 785, 66, pose="walk", look=(1, 0))
    img = c.img
    caption(img, "4:09. His memo: open the SERVICE door at 4:15, the key is in the cupboard. Up he gets to fetch it... "
                 "but someone is at the window.", 24, 22, 940, 7204)
    fl = Flap(wx1 - wx0 + 20, wy1 - wy0 + 60, "top", (wx0 - 10, wy0 - 4), 7205, front_A, back_tab("1", 7206),
              tab=((wx1 - wx0 + 20) / 2, 130, 56))
    fl.lay(img, st.get("f1", 138))
    tape(img, (wx0 - 16, wy0 - 4), (wx1 + 16, wy0 - 4), 22, 7207)
    if st.get("q", True):
        c2 = Cut(h, w, 7208, ground=img)
        c2.balloon(Q, BCAP, (1130, 420), (1580, 470), 7209)
        img = c2.img
    frame(img, 7210)
    return img


def front_A(c, fw, fh):      # the shutter: boards, battens, a lifting label
    c.fill(c.mask(rect(0, 0, fw, fh), jitter=0), "#8a6238")
    for x in range(40, fw, 64):
        c.strip((x, 6), (x + 2, fh - 66), 4, "#6a4a2a", shadow=False, jitter=0.4)
    for y in (30, fh - 110):
        c.piece(rect(10, y, fw - 10, y + 34), "#74512e", off=(3, 4))
    lift_label(c, fw / 2, (fh - 56) / 2 - 18, 1, 54, 7211)


def back_tab(n, seed, cy=None):
    def fn(c, fw, fh):
        y = fh * 0.55 if cy is None else cy
        ring = ellipse(fw / 2, y, 52, 52)
        c.piece(ring, "#3a3027", holes=[ellipse(fw / 2, y, 44, 44)], shadow=False)
        c.ink_letters([n], 58, (fw / 2, y + 4), seed)
        c.ink_letters(["lifted"], 30, (fw / 2, y + 90), seed + 1)
    return fn


def scene_B(st):
    """E2 the clock (flap 2) and the answer; E3 her thanks as she turns from the glass"""
    w, h = sz("B")
    c = Cut(h, w, 7221, ground=WALL, fibre_off=(301, 127))
    c.piece(rect(-20, 470, w + 20, 630), WAINS, shadow=False)
    c.strip((-20, 470), (w + 20, 470), 18, RAIL)
    c.piece(rect(-20, 620, w + 20, h + 20), FLOOR)
    # the window (left), seen from inside: she turns away
    c.piece(rect(-20, 120, 520, 480), WFRAME)
    c.piece(rect(-20, 146, 490, 450), GLASS, shadow=False)
    p64.woman(c, 250, 560, 40, away=True)
    c.piece(rect(-20, 446, 540, 490), "#4a3220")
    c.strip((-20, 300), (490, 300), 9, WFRAME)
    # the clock (centre)
    cx, cy, r = 1050, 350, 80
    p02.clock(c, w, h, cx, cy, r, 4, 10)
    # the agent, looking up to it
    p02.agent(c, 1420, 680, 66, pose="stand", look=(-0.7, -1))
    img = c.img
    caption(img, "He looks up at the clock to tell her. What does it say?", 24, 22, 760, 7222)
    R = int(r * 1.32)
    fl = Flap(2 * R + 8, 2 * R + 46, "top", (cx - R - 4, cy - R - 4), 7223, front_B(R), back_tab("2", 7224, cy=R + 10),
              shape=("disc", R), tab=(R + 4, 96, 50))
    fl.lay(img, st.get("f2", 140))
    tape(img, (cx - 60, cy - R - 4), (cx + 60, cy - R - 4), 22, 7225)
    c2 = Cut(h, w, 7226, ground=img)
    if st.get("a", True):
        c2.balloon(A_, BCAP, (1700, 200), (1440, 300), 7227)
    if st.get("t", True):
        c2.balloon(T, BCAP, (690, 560), (330, 330), 7228)
    img = c2.img
    frame(img, 7229)
    return img


def front_B(R):
    def fn(c, fw, fh):
        c.fill(c.mask(rect(0, 0, fw, fh), jitter=0), "#c99b45")
        c.piece(ellipse(fw / 2, R, R * 0.82, R * 0.82), "#d9b45a", shadow=False)
        lift_label(c, fw / 2, R - 22, 2, 46, 7231)
    return fn


def scene_C(st):
    """E4 the cupboard (its door is flap 3) and the key; E5 the forgetting"""
    w, h = sz("C")
    c = Cut(h, w, 7241, ground=WALL, fibre_off=(521, 233))
    c.piece(rect(-20, 640, w + 20, 860), WAINS, shadow=False)
    c.strip((-20, 640), (w + 20, 640), 20, RAIL)
    c.piece(rect(-20, 850, w + 20, h + 20), FLOOR)
    # the SERVICE door (right), shut
    c.piece(rect(1600, 150, 1930, 960), p02.DOOR)
    for (y0, y1) in ((300, 560), (620, 900)):
        c.piece(rect(1640, y0, 1890, y1), "#3a2a1c", off=(3, 4))
    c.piece(ellipse(1872, 600, 12, 12), BRASS)
    c.piece(rect(1660, 190, 1870, 256), "#f3ecd8")
    c.ink_letters(["SERVICE"], 40, (1765, 224), 7242)
    # the cupboard: case, interior, shelves, hook, the brass key with its SERVICE tag
    X0, Y0, X1, Y1 = 900, 200, 1480, 980
    c.piece(rect(X0 - 30, Y0 - 50, X1 + 30, Y0), "#4a2f1d")
    c.piece(rect(X0, Y0, X1, Y1), "#4a2f1d")
    ix0, iy0, ix1, iy1 = X0 + 30, Y0 + 30, X1 - 30, Y1 - 30
    c.piece(rect(ix0, iy0, ix1, iy1), "#2f2218", shadow=False)
    for y in (iy0 + 170, iy1 - 150):
        c.piece(rect(ix0, y, ix1, y + 22), "#5a3d28")
    kx, ky = (ix0 + ix1) / 2 - 20, iy0 + 230
    c.piece(rect(kx - 8, ky - 30, kx + 8, ky + 34), "#8a8478")
    c.strip((kx, ky + 20), (kx + 24, ky + 52), 9, "#8a8478")
    c.piece(ellipse(kx + 24, ky + 104, 48, 48), BRASS, holes=[ellipse(kx + 24, ky + 104, 23, 23)])
    c.strip((kx + 24, ky + 150), (kx + 24, ky + 380), 23, BRASS)
    c.piece(rect(kx + 24, ky + 318, kx + 80, ky + 344), BRASS2)
    c.piece(rect(kx + 24, ky + 358, kx + 70, ky + 380), BRASS2)
    c.strip((kx + 38, ky + 142), (kx + 100, ky + 220), 4, "#d8cfb8", shadow=False)
    tg = np.float32([(kx + 78, ky + 208), (kx + 248, ky + 226), (kx + 240, ky + 296), (kx + 70, ky + 278)])
    c.piece(tg, TAG)
    c.ink_letters(["SERVICE"], 34, (kx + 160, ky + 252), 7243)
    # the agent, pencil to his chin, before the open cupboard (left)
    p02.agent(c, 250, 1000, 92, pose="chin", look=(0.8, -0.3))
    img = c.img
    caption(img, "Then on to the cupboard. And behind its door?", 24, 22, 1200, 7244)
    if st.get("end", True):
        caption(img, "There hangs the key, in plain view. It stays on its hook; the SERVICE door stays shut.",
                900, h - 150, 1040, 7245)
    fl = Flap(X1 - X0 + 90, Y1 - Y0, "left", (X0, Y0), 7246, front_C(X1 - X0 + 20), back_tab_left("3", 7247),
              tab=((Y1 - Y0) / 2, 130, 70))
    fl.lay(img, st.get("f3", 128))
    tape(img, (X0, Y0), (X0, Y1), 24, 7248)
    if st.get("f", True):
        c2 = Cut(h, w, 7249, ground=img)
        c2.balloon(F, BCAP, (560, 300), (275, 384), 7250)
        img = c2.img
    frame(img, 7251)
    return img


def front_C(dw):
    def fn(c, fw, fh):
        c.fill(c.mask(rect(0, 0, dw, fh), jitter=0), "#5a3a24")
        for (y0, y1) in ((70, fh * 0.47), (fh * 0.53, fh - 70)):
            c.piece(rect(60, y0, dw - 60, y1), "#4a2f1d", off=(3, 4))
        c.piece(ellipse(dw - 40, fh / 2, 13, 13), BRASS)
        lift_label(c, dw / 2, fh * 0.30, 3, 60, 7261)
    return fn


def back_tab_left(n, seed):
    def fn(c, fw, fh):
        x, y = fw * 0.55, fh * 0.42
        c.piece(ellipse(x, y, 60, 60), "#3a3027", holes=[ellipse(x, y, 51, 51)], shadow=False)
        c.ink_letters([n], 68, (x, y + 4), seed)
        c.ink_letters(["lifted"], 34, (x, y + 104), seed + 1)
    return fn


SCENES = [("A", scene_A), ("B", scene_B), ("C", scene_C)]


def build(state=None):
    state = state or {}
    pg = pen99.sheet99()
    for k, fn in SCENES:
        x0, y0, x1, y1 = BOXES[k]
        m = np.zeros((H, W), np.uint8)
        m[y0:y1, x0:x1] = 255
        penlib.shadow_onto(pg, m, off=7, blur=7, opacity=0.45)
        pg[y0:y1, x0:x1] = fn(state.get(k, {}))
    return pg


CLOSED = {"A": {"f1": 0, "q": False}, "B": {"f2": 0, "a": False, "t": False}, "C": {"f3": 0, "f": False, "end": False}}


def states():
    s = []
    def mk(a, b, c_):
        return {"A": a, "B": b, "C": c_}
    s.append(mk(CLOSED["A"], CLOSED["B"], CLOSED["C"]))
    s.append(mk({"f1": 62, "q": False}, CLOSED["B"], CLOSED["C"]))
    s.append(mk({"f1": 138}, CLOSED["B"], CLOSED["C"]))
    s.append(mk({"f1": 138}, {"f2": 70, "a": False, "t": False}, CLOSED["C"]))
    s.append(mk({"f1": 138}, {"f2": 140}, CLOSED["C"]))
    s.append(mk({"f1": 138}, {"f2": 140}, {"f3": 64, "f": False, "end": False}))
    s.append(mk({"f1": 138}, {"f2": 140}, {"f3": 128, "f": False, "end": False}))
    s.append({})
    return s


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for st in states():
            p = img if not st else np.clip(np.round(build(st)), 0, 255).astype(np.uint8)
            if st:
                pen99.folio(p, N, TITLE)
            frames.append(cv2.resize(p, (960, 1242), interpolation=cv2.INTER_AREA))
        save_beats(N, frames)
