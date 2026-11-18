"""99 ways, page 83 "The clock's eye" (point of view; medium: engraving-puppet).
Seen from the wall clock: one fixed high downward view, the clock's own hand edging into the panel border.
Six boards, one per event E0-E5, all photographed from the same place: the clock's face, high on the near wall of the
office, looking down across the floor at the far wall (ticket window, cupboard, SERVICE door). The set is a small
model room: a far-wall card and a desk built as standing cards on a pen-ruled floor, projected through one fixed
camera (a true perspective homography per standing card), so the floorboards converge, the desk top and memo are
seen from above, and the figures stand small below the eye. The clock's own minute hand, a cut black card seen from
behind its face, rises from below the bottom border of every board (where the clock itself is, beneath its eye) and
creeps 4:09 -> 4:11 from board to board.
Reuses page 03/49's ENGRAVING PUPPETS (kit/build_page03.py, build/p49_epic.py): AGENT = the Harper's Weekly 1863
telegraph operator (LoC cph.3c11072), STRANGER = the hatted woman of the 1867 Steinway Hall engraving (LoC
cph.3c32079) seen through the 1863 plate's window glass, his table from the same plate. Set, hand and lettering
HANDMADE in the shared pen hand. Run: python3 -I p83_clocks_eye.py [--page-only]"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
import build_page03 as b3  # noqa: E402
import b1m2 as B  # noqa: E402
import p49_epic as E  # noqa: E402

N, PID, TITLE = 83, "clocks-eye", "The clock's eye"
W, H = pen99.PAGE_W, pen99.PAGE_H
OPS = b3.OPS
pen, Mof, lay = b3.pen, b3.Mof, b3.lay
Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == E.LN["question"] and " ".join(A) == E.LN["answer"]
assert " ".join(T) == E.LN["thanks"] and " ".join(F) == E.LN["forgetting"]

PW, PH = 960, 760
COLX = (110, 1130)
ROWY = (110, 980, 1850)
BOX = {i + 1: (COLX[i % 2], ROWY[i // 2], PW, PH) for i in range(6)}
TIMES = {1: (4, 9, 5), 2: (4, 9, 40), 3: (4, 10, 2), 4: (4, 10, 14), 5: (4, 10, 50), 6: (4, 11, 20)}
WALLZ, ROOMX, ROOMH = 3.9, 3.3, 3.4

# ------------------------------------------------------------------ the clock's camera
CAM = np.array([0.0, 3.1, 0.0])          # the clock's face: high on the near wall, centre
PITCH = math.radians(33)                  # looking down
FOC = 640.0
CX, CY = PW / 2, PH * 0.33
fwd = np.array([0, -math.sin(PITCH), math.cos(PITCH)])
upv = np.array([0, math.cos(PITCH), math.sin(PITCH)])
rgt = np.array([1.0, 0, 0])


def proj(P):
    d = np.asarray(P, float) - CAM
    zc = d @ fwd
    return np.array([CX + FOC * (d @ rgt) / zc, CY - FOC * (d @ upv) / zc])


def card_bg(w, h, seed):
    return np.zeros((h, w, 3), np.float32) + b3.CARD + (np.random.RandomState(seed).rand(h, w, 1) - 0.5) * 3


def twin(draw, w, h):
    """draw the same cut-card scene on black and on white grounds; recover colour and alpha (lay is linear)"""
    c0 = np.zeros((h, w, 3), np.float32)
    c1 = np.full((h, w, 3), 255.0, np.float32)
    random.seed(1)
    out0 = draw(c0)
    random.seed(1)
    draw(c1)
    a = np.clip(1 - (c1 - c0).mean(2) / 255.0, 0, 1)
    rgb = np.where(a[..., None] > 1e-3, c0 / np.maximum(a[..., None], 1e-3), 0)
    return np.clip(rgb, 0, 255), a, out0


def warp_card(panel, rgb, a, src4, dst4):
    Hm = cv2.getPerspectiveTransform(np.float32(src4), np.float32(dst4))
    r = cv2.warpPerspective(rgb.astype(np.float32), Hm, (PW, PH), flags=cv2.INTER_AREA)
    al = cv2.warpPerspective(a.astype(np.float32), Hm, (PW, PH), flags=cv2.INTER_LINEAR)[..., None]
    panel[:] = panel * (1 - al) + r * al
    return Hm


def stand(panel, rgb, a, ppm, foot_uv, X, Z, Y0=0.0):
    """a card standing upright in the model room, facing the clock, its foot point at (X, Y0, Z)"""
    h, w = a.shape
    fu, fv = foot_uv
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = [proj((X + (u - fu) / ppm, Y0 + (fv - v) / ppm, Z)) for u, v in src]
    return warp_card(panel, rgb, a, src, dst)


def flat(panel, rgb, a, corners3d):
    """a card lying flat (desk top, memo): its four corners in the room"""
    h, w = a.shape
    return warp_card(panel, rgb, a, [(0, 0), (w, 0), (w, h), (0, h)], [proj(p) for p in corners3d])


def floor_shadow(panel, X, Z, rx=0.34, rz=0.22, op=0.30):
    m = np.zeros((PH, PW), np.uint8)
    pts = [proj((X + rx * math.cos(t), 0, Z + rz * math.sin(t))) for t in np.linspace(0, 2 * math.pi, 30)]
    cv2.fillPoly(m, [np.int32(np.array(pts) * 4)], 255, cv2.LINE_AA, shift=2)
    m = cv2.GaussianBlur(m, (0, 0), 7).astype(np.float32)[..., None] / 255
    panel[:] = panel * (1 - op * m)


# ------------------------------------------------------------------ the model room (fixed)
WPPM = 200.0                       # far-wall card px per metre
WALL_W, WALL_H = int(2 * ROOMX * WPPM), int(ROOMH * WPPM)
WIN_X = 260                        # window board x on the wall card (p49 window_board coords)
CUP = (840, 330, 1030, 650)        # cupboard on the wall card (x0, y0, x1, y1); floor = WALL_H
SDOOR = (1110, 250, 1290, WALL_H)


def wall_card(P, open_k, woman, seed):
    def draw(c):
        c[:] = card_bg(WALL_W, WALL_H, seed) if c.mean() > 100 or True else c
        # wainscot rail and boards
        pen(c, [(10, 470), (WALL_W - 10, 470)], 3, seed + 1)
        for k in range(14):
            x = 40 + k * 96
            pen(c, [(x, 480), (x, WALL_H - 8)], 1.6, seed + 10 + k, colour=b3.GRAPH)
        sub = c[200:, :]
        wm = E.window_board(sub, P, WIN_X, seed + 30, woman=woman)
        b3.cupboard(c, *CUP, open_k, seed + 40)
        x0_, y0_, x1_, y1_ = CUP
        pen(c, [(x0_ - 16, y0_ - 4), (x1_ + 16, y0_ - 4), (x1_ + 16, y0_ - 26), (x0_ - 16, y0_ - 26)], 4, seed + 45, closed=True)
        pen(c, [(x0_ + 4, y1_), (x0_ + 4, WALL_H - 4)], 5, seed + 46)
        pen(c, [(x1_ - 4, y1_), (x1_ - 4, WALL_H - 4)], 5, seed + 47)
        b3.service_door(c, *SDOOR, seed + 50)
        return wm
    # the wall card is opaque: draw once on card
    c = card_bg(WALL_W, WALL_H, seed)
    out = draw(c)
    return c, np.ones((WALL_H, WALL_W), np.float32), out


def room(panel, P, open_k, woman, seed):
    """floor, far wall, side walls: all from the one fixed eye"""
    panel[:] = card_bg(PW, PH, seed) * 0.93
    # side walls and floor edges, pen lines
    fl = [proj((-ROOMX, 0, 0.4)), proj((-ROOMX, 0, WALLZ)), proj((ROOMX, 0, WALLZ)), proj((ROOMX, 0, 0.4))]
    m = np.zeros((PH, PW), np.uint8)
    cv2.fillPoly(m, [np.int32(np.array(fl) * 4)], 255, cv2.LINE_AA, shift=2)
    floorc = hexc("#e9dfc6")
    panel[:] = panel * (1 - m[..., None] / 255) + floorc * (m[..., None] / 255)
    for k in range(17):                    # floorboards running away from the clock, converging
        x = -ROOMX + k * (2 * ROOMX / 16)
        pen(panel, [proj((x, 0, 0.2)), proj((x, 0, WALLZ))], 1.8, seed + 100 + k, colour=b3.GRAPH)
    for z in (1.3, 2.6, 3.9):              # board ends
        for k in range(16):
            if (k + int(z * 3)) % 3 == 0:
                x = -ROOMX + k * (2 * ROOMX / 16)
                pen(panel, [proj((x, 0, z + 0.2 * (k % 2))), proj((x + 2 * ROOMX / 16, 0, z + 0.2 * (k % 2)))], 1.4,
                    seed + 200 + k, colour=b3.GRAPH)
    rgb, a, wm = wall_card(P, open_k, woman, seed + 300)
    stand(panel, rgb, a, WPPM, (WALL_W / 2, WALL_H), 0.0, WALLZ)
    for s_ in (-1, 1):                     # wall corners
        pen(panel, [proj((s_ * ROOMX, 0, WALLZ)), proj((s_ * ROOMX, ROOMH, WALLZ))], 4, seed + 400 + s_)
        pen(panel, [proj((s_ * ROOMX, 0, WALLZ)), proj((s_ * ROOMX, 0, 0.0))], 4, seed + 410 + s_)
    pen(panel, [proj((-ROOMX, 0, WALLZ)), proj((ROOMX, 0, WALLZ))], 4, seed + 420)
    return wm


def wall_pt(u, v):
    """wall-card px -> panel px"""
    return proj(((u - WALL_W / 2) / WPPM, (WALL_H - v) / WPPM, WALLZ))


DESK = (-2.2, -0.75, 1.15, 1.8, 0.78)    # x0, x1, z0, z1, top height (m)


def desk(panel, P, seed, memo=True):
    x0, x1, z0, z1, ht = DESK
    # the table from the 1863 plate as the desk's front, standing at its near edge
    def dr(c):
        lay(c, P["table"], Mof(0.62, 0, np.array([250, 980]) * OPS, (330, 640)))
    rgb, a, _ = twin(dr, 660, 660)
    ys, xs = np.where(a > 0.3)
    # fit the cut table between x0..x1, its top edge at ht
    tw = xs.max() - xs.min()
    ppm = tw / (x1 - x0)
    th_m = (640 - ys.min()) / ppm
    ppm_y = (640 - ys.min()) / ht
    sc = np.float32([[1, 0, 0], [0, ppm / ppm_y, 0]])
    rgb2 = cv2.warpAffine(rgb, sc, (660, 660))
    a2 = cv2.warpAffine(a, sc, (660, 660))
    # the desk top seen from above: a card lying flat on the frame
    top = card_bg(400, 220, seed)
    pen(top, [(6, 6), (394, 6), (394, 214), (6, 214)], 4, seed + 1, closed=True)
    pen(top, [(18, 22), (382, 22)], 1.5, seed + 2, colour=b3.GRAPH)
    if memo:
        b3.memo(top, 230, 112, 1.12, seed + 3, deg=-4)
        pen(top, b3.circle_pts(60, 60, 18, 16), 3, seed + 4, closed=True)
        pen(top, [(52, 150), (120, 196)], 4, seed + 5)
    flat(panel, top, np.ones((220, 400), np.float32), [(x0, ht, z1), (x1, ht, z1), (x1, ht, z0), (x0, ht, z0)])
    stand(panel, rgb2, a2, ppm, ((xs.min() + xs.max()) / 2, 640 * ppm / ppm_y), (x0 + x1) / 2, z0)


APPM = 330.0
AFOOT = (360, 1240)


def agent_card(P, arms, head, flip, seed):
    def dr(c):
        return b3.agent(c, P, AFOOT, 0.92, arms=arms, head=head, flip=flip)
    return twin(dr, 760, 1280)


def place_agent(panel, P, X, Z, arms=(0, 0, 0), head=0, flip=True, seed=0):
    rgb, a, hand = agent_card(P, arms, head, flip, seed)
    ys, xs = np.where(a > 0.3)
    ppm = (AFOOT[1] - ys.min()) / 1.74          # he stands 1.74 m
    floor_shadow(panel, X, Z + 0.05)
    Hm = stand(panel, rgb, a, ppm, AFOOT, X, Z)
    def tp(p):
        q = Hm @ np.array([p[0], p[1], 1.0])
        return q[:2] / q[2]
    head_top = tp(((xs[ys == ys.min()]).mean(), ys.min()))
    mouth = tp((((xs[ys == ys.min()]).mean()) + (-1 if not flip else 1) * 0, ys.min() + 0.12 * (AFOOT[1] - ys.min())))
    return dict(head=head_top, mouth=mouth, hand=tp(hand))


# ------------------------------------------------------------------ the clock's own hand
def clock_hand(pg, x0, y0, t, seed):
    """the minute hand, a cut black card, seen from behind the face (so it turns the other way), pivot below the
    board's bottom border; it edges up across the border into the view; hour hand stub below; brass boss."""
    hh, mm, ss = t
    mf = mm + ss / 60
    ang = -math.radians(mf * 6)            # mirrored: seen from behind the dial
    piv = np.array([x0 + PW * 0.80, y0 + PH + 58.0])
    L = 250
    d = np.array([math.sin(ang), -math.cos(ang)])
    n_ = np.array([-d[1], d[0]])
    tip = piv + d * L
    spade = piv + d * (L - 46)
    poly = [piv - n_ * 9 - d * 30, spade - n_ * 7, spade - n_ * 22 - d * 10, tip, spade + n_ * 22 - d * 10, spade + n_ * 7,
            piv + n_ * 9 - d * 30]
    # the hour hand (pointing near 4, mirrored), short, mostly behind the gutter
    ah = -math.radians((hh % 12) * 30 + mf * 0.5)
    dh = np.array([math.sin(ah), -math.cos(ah)])
    nh = np.array([-dh[1], dh[0]])
    polyh = [piv - nh * 12, piv + dh * 70 - nh * 10, piv + dh * 92, piv + dh * 70 + nh * 10, piv + nh * 12]
    m = np.zeros(pg.shape[:2], np.uint8)
    for pl in (poly, polyh):
        cv2.fillPoly(m, [np.int32(np.array(pl) * 4)], 255, cv2.LINE_AA, shift=2)
    cv2.circle(m, (int(piv[0] * 4), int(piv[1] * 4)), 22 * 4, 255, -1, cv2.LINE_AA, shift=2)
    # a hole pierced in the spade, as old hands have
    hole = np.zeros_like(m)
    cv2.circle(hole, (int((spade[0] + d[0] * 8) * 4), int((spade[1] + d[1] * 8) * 4)), 7 * 4, 255, -1, cv2.LINE_AA, shift=2)
    m = np.where(hole > 0, 0, m).astype(np.uint8)
    penlib.shadow_onto(pg, m, off=6, blur=5, opacity=0.45)
    penlib.ink_onto(pg, m, hexc("#151311"))
    b3.pin(pg, piv[0], piv[1], 9)
    return tip


def time_label(pg, x0, y0, t, seed):
    hh, mm, ss = t
    lab = pen99.letter([f"{hh}:{mm:02d}:{ss:02d}"], 30, seed)
    sub = np.zeros(pg.shape[:2], np.uint8)
    yy = y0 + PH + 10
    sub[yy:yy + lab.shape[0], x0 - 14:x0 - 14 + lab.shape[1]] = lab
    penlib.ink_onto(pg, sub, b3.GRAPH)


# ------------------------------------------------------------------ boards
def board(n, P, figures=True, line_on=True):
    pnl = np.zeros((PH, PW, 3), np.float32)
    woman = None
    if figures and n in (2, 3):
        woman = dict(flip=False, shift=0.0)
    if figures and n == 4:
        woman = dict(flip=True, shift=0.40)
    open_k = 0.0 if (n < 5 or not figures) else (0.8 if n == 5 else 1.0)
    room(pnl, P, open_k, woman, 8300 + n * 0)
    desk(pnl, P, 8350)
    if not figures:
        return pnl
    win_mouth = wall_pt(WIN_X + 30, 330)
    if n == 1:      # E0: at the desk, the memo before him; he rises and turns for the cupboard
        f = place_agent(pnl, P, -0.35, 1.95, arms=(-30, 20, 0), head=10, flip=True)
    elif n == 2:    # E1: halfway across the floor; the question from the window
        f = place_agent(pnl, P, -0.8, 2.7, arms=(12, 0, -8), head=0, flip=False)
        if line_on:
            E.balloon(pnl, Q, 36, (470, 100), (win_mouth[0], win_mouth[1] - 6), 8361)
    elif n == 3:    # E2: he looks UP, at the clock, at us; the answer
        f = place_agent(pnl, P, -0.85, 2.6, arms=(60, 150, 0), head=-30, flip=False)
        if line_on:
            E.balloon(pnl, A, 38, (620, 110), f["mouth"], 8371)
    elif n == 4:    # E3: the thanks; she turns from the glass
        f = place_agent(pnl, P, -0.7, 2.75, arms=(0, 0, 0), head=6, flip=False)
        if line_on:
            E.balloon(pnl, T, 40, (440, 90), (win_mouth[0] + 10, win_mouth[1] - 6), 8381)
    elif n == 5:    # E4: at the cupboard; the door opens on its left jamb; the key on its hook
        f = place_agent(pnl, P, 0.5, 3.45, arms=(-62, 30, 0), head=0, flip=True)
    else:           # E5: pencil to chin before the open cupboard; the key stays; the SERVICE door stays shut
        f = place_agent(pnl, P, 0.35, 3.35, arms=(47, 132, 0), head=-6, flip=True)
        hd = f["hand"]
        pen(pnl, [(hd[0] + 1, hd[1] + 2), (hd[0] - 3, hd[1] - 16)], 3, 8391)
        if line_on:
            E.balloon(pnl, F, 36, (225, 345), (f["mouth"][0] - 4, f["mouth"][1]), 8392)
    return pnl


SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 1.8)


def build(upto=6, figures_upto=6, line_on=True):
    pg = SHEET.copy()
    P = b3.load_puppets()
    for n in range(1, 7):
        if n > upto:
            continue
        x0, y0, w, h = BOX[n]
        pg[y0:y0 + h, x0:x0 + w] = board(n, P, figures=(n <= figures_upto), line_on=(line_on or n < figures_upto))
        bm = penlib.border_mask(pg.shape[:2], [(x0, y0, x0 + w, y0 + h)], 8, 8385 + n)
        penlib.ink_onto(pg, bm)
        time_label(pg, x0, y0, TIMES[n], 8320 + n)
        clock_hand(pg, x0, y0, TIMES[n], 8330 + n)
    return pg


def main():
    page = build(6)
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    print("jpeg", size, "cam: far wall base y", proj((0, 0, WALLZ))[1], "near floor y", proj((0, 0, 0.4))[1])
    if "--page-only" in sys.argv:
        return
    frames = [build(6, figures_upto=0)]
    for k in range(1, 7):
        frames.append(build(6, figures_upto=k))
    for f in frames:
        pen99.folio(f, N, TITLE)
    print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    main()
