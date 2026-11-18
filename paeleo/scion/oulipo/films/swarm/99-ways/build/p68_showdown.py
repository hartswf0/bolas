"""99 ways, page 68 "Showdown" (genre; medium: engraving-puppet).
Framed as a frontier standoff at the ticket window, hands at the hip, the clock as the duel's timer.
A storyboard sheet for a western: a torn bill pinned at the head ('SHOWDOWN AT THE TICKET WINDOW'), eight
widescreen shot boards (letterboxed, each headed SHOT n, its framing and a running clock time to the second with a
small pen clock face: the duel's timer), torn commentary slips in a frontier drawl, written for this page.
Shot 3 is the western's eyes-only extreme close-up; shot 4 the hands at the hip; shot 5 the clock filling the
frame at 4:10. The four canon lines verbatim in cut-paper balloons; the outcome unchanged.
Reuses page 03/49's ENGRAVING PUPPETS (kit/build_page03.py, build/p49_epic.py): AGENT = the Harper's Weekly 1863
telegraph operator (LoC cph.3c11072), his table and the window from the 1863 plate; set, tumbleweed, clock faces and lettering in the
shared pen hand. Batch 7 repair: the STRANGER is the hatted woman of John N. Hyde's 1883 Frank Leslie's wood
engraving (LoC 2014645364, forage/p68), her eyes under the brim in SHOT 3 and her bust behind the window glass; the
agent carries a HANDMADE pencil; SHOT 8 stands him before the open cupboard, pencil to chin. Run: python3 -I p68_showdown.py [--page-only]"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import build_page03 as b3  # noqa: E402
import b1m2 as B  # noqa: E402
import p49_epic as E  # noqa: E402

N, PID, TITLE = 68, "showdown", "Showdown"
W, H = pen99.PAGE_W, pen99.PAGE_H
OPS = b3.OPS
pen, letters, Mof, lay = b3.pen, b3.letters, b3.Mof, b3.lay
K = 0.82                          # boards are cut at 372 px high and laid on the sheet at 0.82
BH = 372
Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == E.LN["question"] and " ".join(A) == E.LN["answer"]
assert " ".join(T) == E.LN["thanks"] and " ".join(F) == E.LN["forgetting"]

SHOTS = {  # n: (framing, h, m, s, slip)
    1: ("WIDE", 4, 9, 30, "Randolph, Vermont. Four-oh-nine. One man, one job: open the SERVICE door at a quarter past, "
                          "with the key in the cupboard. He gets up out of that chair, slow."),
    2: ("MEDIUM", 4, 9, 50, "Halfway across the floor, he stops. Somebody's at the window."),
    3: ("EXTREME CLOSE-UP", 4, 10, 0, "His eyes. Her eyes. Nobody blinks."),
    4: ("HANDS AT THE HIP", 4, 10, 4, "Hands at the hip. She draws first."),
    5: ("CLOSE: THE CLOCK", 4, 10, 9, "He draws the time off the wall clock, quick and clean."),
    6: ("MEDIUM", 4, 10, 15, "She tips her head and leaves the window. Nothing left in here now but a bit of blown hay, rolling by."),
    7: ("MEDIUM", 4, 10, 45, "He makes it to the cupboard. There's the key, on its hook."),
    8: ("WIDE", 4, 11, 0, "Showdown's over, and nobody won. The key stays on its hook; the SERVICE door stays shut."),
}
FULL = (1, 8)
SCAP = 28
BILL_OV = 34
BILL_T = (pen99.letter(["SHOWDOWN"], 84, 6990, weight=0.15), pen99.letter(["AT THE TICKET WINDOW"], 40, 6991, weight=0.13),
          pen99.letter(["Randolph station, 4:10 sharp. Eight shots, one clock."], 26, 6992))
BILL_H = sum(m.shape[0] - BILL_OV for m in BILL_T) + 14
TOP0 = 104 + BILL_H + 12
COLX = ((110, 1070), (1130, 2090))


def slip_h(n, w):
    let = B.letter_left(B.wrap(SHOTS[n][4], SCAP, w - 90), SCAP, 6800 + n)
    return let.shape[0] + int(SCAP * 0.9)


def layout():
    rows = [(1,), (2, 3), (4, 5), (6, 7), (8,)]
    bh = int(BH * K)
    hdr = 40
    need = 0
    for r in rows:
        w = 1980 if r[0] in FULL else 960
        need += hdr + bh + 10 + max(slip_h(n, w) for n in r)
    gap = (2728 - TOP0 - need) / (len(rows) - 1)
    assert gap >= 8, gap
    bx, y = {}, TOP0
    for r in rows:
        for i, n in enumerate(r):
            x0, x1 = (110, 2090) if n in FULL else COLX[i]
            bx[n] = (x0, int(y + hdr), x1 - x0, bh)
        w = 1980 if r[0] in FULL else 960
        y += hdr + bh + 10 + max(slip_h(n, w) for n in r) + gap
    return bx


BX = layout()


# ------------------------------------------------------------------ HANDMADE pen props
def tumbleweed(c, cx, cy, r, seed, rot=0.0):
    """a ball of blown hay: tangled pen loops"""
    rnd = random.Random(seed)
    m = np.zeros(c.shape[:2], np.uint8)
    for k in range(14):
        a0 = rnd.uniform(0, 6.28) + rot
        rr = r * rnd.uniform(0.25, 0.6)
        ex = rnd.uniform(0.6, 1.0)
        ox, oy = rnd.uniform(-0.4, 0.4) * r, rnd.uniform(-0.35, 0.35) * r
        pts = [(cx + ox + rr * math.cos(a0 + t) * ex, cy + oy + rr * math.sin(a0 + t) * (2 - ex) * 0.8)
               for t in np.linspace(0, rnd.uniform(2.5, 5.5), 18)]
        penlib.brush_line(m, pts, 2.6, seed + k, tremor=0.7)
    penlib.ink_onto(c, m, b3.INK)
    pen(c, [(cx - r * 2.4, cy + r * 0.95), (cx - r * 1.4, cy + r * 0.95)], 2, seed + 40)        # dust trail
    pen(c, [(cx - r * 3.6, cy + r * 0.80), (cx - r * 2.8, cy + r * 0.80)], 2, seed + 41)


def mini_clock(pg, cx, cy, r, hh, mm, ss, seed):
    """the duel's timer in each shot's header: pen face, hour, minute and second hands"""
    pen(pg, b3.circle_pts(cx, cy, r, 30), 3, seed, closed=True)
    for k in range(12):
        a = math.radians(k * 30)
        pen(pg, [(cx + math.sin(a) * r * .78, cy - math.cos(a) * r * .78), (cx + math.sin(a) * r * .92, cy - math.cos(a) * r * .92)],
            2, seed + 3 + k)
    mmf = mm + ss / 60
    ah, am, asx = math.radians((hh % 12) * 30 + mmf * .5), math.radians(mmf * 6), math.radians(ss * 6)
    pen(pg, [(cx, cy), (cx + math.sin(ah) * r * .5, cy - math.cos(ah) * r * .5)], 4, seed + 20)
    pen(pg, [(cx, cy), (cx + math.sin(am) * r * .8, cy - math.cos(am) * r * .8)], 3, seed + 21)
    pen(pg, [(cx, cy), (cx + math.sin(asx) * r * .86, cy - math.cos(asx) * r * .86)], 1.6, seed + 22, colour=b3.GRAPH)


def big_clock(c, cx, cy, r, ss, seed):
    """the wall clock filling the shot at 4:10, its pendulum and second hand"""
    b3.clock(c, cx, cy, r, 4, 10, seed)
    a = math.radians(ss * 6)
    pen(c, [(cx, cy), (cx + math.sin(a) * r * .82, cy - math.cos(a) * r * .82)], 2, seed + 400, colour=b3.GRAPH)


def eyes_piece(P, key, box):
    """a strip cut across a puppet's eyes (piece px box x0, y0, x1, y1)"""
    pc = P[key]
    ox, oy = pc["origin"]
    x0, y0, x1, y1 = box
    a = np.zeros_like(pc["a"])
    a[y0 - oy:y1 - oy, x0 - ox:x1 - ox] = pc["a"][y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return dict(pc, a=a)



# ------------------------------------------------------------------ repair (batch 7): the stranger re-cast, the agent's pencil
HYDE = b3.SRC / "forage/p68/hyde_woman_u.jpg"     # LoC 2014645364 region (x 2650, y 2950) of the 5454x8010 master
# her bust, scissor path in quarter-scale px of the region (x4 = region px): hat (bird tops trimmed), face, fur collar
HYDE_BUST = [(150, 215), (150, 160), (165, 125), (190, 100), (230, 84), (270, 76), (310, 72), (350, 84), (385, 108),
             (410, 140), (414, 178), (404, 220), (394, 258), (376, 292), (348, 318), (318, 330), (300, 342), (380, 380),
             (424, 430), (446, 520), (430, 610), (36, 610), (40, 520), (72, 450), (112, 400), (160, 342), (168, 300),
             (156, 262)]
HYDE_EYES = (480, 560, 1440, 1260)                  # region px: the brim's edge over her curls, her two eyes, the nose
HYDE_EYES_C = (1010, 975)                           # region px: under the brim, her eyes in the lower half
HYDE_FACE_X = 207                                   # quarter px: just left of her left eye; the sash bar falls here
HYDE_CROWN_Y = 92                                   # quarter px: the hat crown, set under the window head
MOUTH, CHIN = (662, 300), (664, 336)                # agent head piece, tel_operator_crop px (beard at the lips; chin)
PENCIL_Y = b3.hexc("#d2a23a")


def hyde_gray():
    from PIL import Image
    return np.asarray(Image.open(HYDE).convert("L"))


def hyde_pieces():
    g = hyde_gray()
    bust = b3.cut_piece(g, HYDE_BUST, 4.0)
    x0, y0, x1, y1 = HYDE_EYES
    eyes = b3.cut_piece(g, [(x0, y0), (x1, y0 + 8), (x1 - 6, y1), (x0 + 4, y1 - 10)], 1.0)
    return bust, eyes


def agent_pts(foot, s, arms=(0, 0, 0), head=0, flip=False):
    """the same transforms as b3.agent: hand, mouth, chin and the forearm's direction, board px"""
    J = {k: np.array(v, np.float32) * OPS for k, v in b3.JOINTS.items()}
    legs_foot = np.array([510, 940], np.float32) * OPS
    Mb = np.vstack([Mof(s, 0, legs_foot, foot), [0, 0, 1]])
    if flip:
        Mb = np.array([[-1, 0, 2 * foot[0]], [0, 1, 0], [0, 0, 1]], np.float64) @ Mb
    Rj = lambda k, deg: np.vstack([cv2.getRotationMatrix2D((float(J[k][0]), float(J[k][1])), deg, 1.0), [0, 0, 1]])
    Mu = Mb @ Rj("armU", arms[0])
    Mf = Mu @ Rj("armF", arms[1])
    Mh = Mb @ Rj("head", head)
    ap = lambda M, p: (M @ np.array([p[0], p[1], 1.0]))[:2]
    hand = np.array([336, 446], np.float32) * OPS
    return dict(hand=ap(Mf, hand), elbow=ap(Mf, J["armF"]), mouth=ap(Mh, MOUTH), chin=ap(Mh, CHIN),
                top=ap(Mh, np.array([530, 122]) * OPS))


def pencil(c, a, b, seed):
    """HANDMADE pen prop: the agent's pencil from a (butt, in the hand) to b (the point): a yellow cut-paper rod, pen
    outline, pale sharpened wood and a graphite tip"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = float(np.hypot(*d)) or 1.0
    u = d / L
    n = np.array([-u[1], u[0]])
    hw = max(3.2, L * 0.075)
    cone = a + u * L * 0.78
    body = [a + n * hw, cone + n * hw, cone - n * hw, a - n * hw]
    m = np.zeros(c.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32(np.array(body) * 4)], 255, cv2.LINE_AA, shift=2)
    al = m[..., None].astype(np.float32) / 255
    c[:] = c * (1 - al) + PENCIL_Y * al
    m2 = np.zeros(c.shape[:2], np.uint8)
    cv2.fillPoly(m2, [np.int32(np.array([cone + n * hw, b, cone - n * hw]) * 4)], 255, cv2.LINE_AA, shift=2)
    al = m2[..., None].astype(np.float32) / 255
    c[:] = c * (1 - al) + b3.hexc("#ead2a6") * al
    pen(c, [tuple(p) for p in body] + [tuple(b)], 2.4, seed, closed=True)
    pen(c, [tuple(cone + u * L * 0.14 + n * hw * 0.35), tuple(b)], 3.4, seed + 1)


def agent_with_pencil(c, P, foot, s, arms=(0, 0, 0), head=0, flip=True, pdeg=None, plen=None, to=None, seed=0):
    """b3.agent, then the pencil in his hand (along the forearm, turned by pdeg, or pointing at `to`)"""
    b3.agent(c, P, foot, s, arms=arms, head=head, flip=flip)
    q = agent_pts(foot, s, arms, head, flip)
    plen = plen or 150 * s
    if to is not None:
        tip = np.asarray(to, float)
    else:
        d = q["hand"] - q["elbow"]
        ang = math.atan2(d[1], d[0]) + math.radians(pdeg or 0)
        tip = q["hand"] + plen * np.array([math.cos(ang), math.sin(ang)])
    d = tip - q["hand"]
    pencil(c, q["hand"] - d / np.hypot(*d) * plen * 0.18, tip, seed)
    q["pencil_tip"] = tip
    return q


def reach(foot, s, target, head=0, flip=True, a0=(-180, 180), a1=(0, 175)):
    """arm angles that bring the hand nearest a target point"""
    best = None
    for u in range(a0[0], a0[1], 3):
        for f in range(a1[0], a1[1], 3):
            h = agent_pts(foot, s, (u, f, 0), head, flip)["hand"]
            d = float(np.hypot(*(h - target)))
            if best is None or d < best[0]:
                best = (d, (u, f, 0))
    return best[1], best[0]


def stranger_in_window(c, P, wx, bust, shift=0.0, flip=False, deg=0.0, s=0.16, fade=0.28):
    """the stranger (Hyde's 1883 woman in her hat) seen through the whole ticket window, upper and lower sash: her
    bust cut along its scissor path, laid behind the glass so the sash bars and frame stay in front; the plate's own
    glass hatching kept faintly over her (fade)"""
    h, w = c.shape[:2]
    panes = [(104, 214, 150, 383), (163, 214, 227, 383), (104, 402, 150, 530), (162, 402, 227, 530)]
    glass = np.zeros((h, w), np.uint8)
    for x0, y0, x1, y1 in panes:
        a0, a1 = E.win_px(wx, (x0, y0)), E.win_px(wx, (x1, y1))
        cv2.rectangle(glass, (int(a0[0]) + 1, int(a0[1]) + 1), (int(a1[0]) - 1, int(a1[1]) - 1), 255, -1)
    glass = cv2.GaussianBlur(glass.astype(np.float32) / 255, (0, 0), 1.0)
    bar = E.win_px(wx, (163, 214))
    target = np.array([bar[0] + shift * 66, bar[1] + 6])
    anchor = np.array([HYDE_FACE_X * 4.0, HYDE_CROWN_Y * 4.0])
    F = np.diag([-1.0 if flip else 1.0, 1.0])
    th = math.radians(deg)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    A = s * R @ F
    ox, oy = bust["origin"]
    MM = np.zeros((2, 3))
    MM[:, :2] = A
    MM[:, 2] = target - A @ anchor + A @ np.array([ox, oy], np.float64)
    rgb = cv2.warpAffine(bust["rgb"].astype(np.float32), MM, (w, h), flags=cv2.INTER_AREA,
                         borderValue=tuple(float(v) for v in b3.CARD))
    al = cv2.warpAffine(bust["a"], MM, (w, h), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
    aa = (al * glass)[..., None]
    behind = b3.CARD * (1 - fade) + c * fade          # the glass hatching thinned where she stands close behind it
    wn = np.clip(rgb / b3.CARD, 0, 1)
    c[:] = c * (1 - aa) + (behind * wn) * aa
    return MM


def window_with_stranger(c, P, wx, seed, bust, **kw):
    Mw = Mof(E.WIN_S, 0, E.WIN_ABOUT, (wx, 175))
    lay(c, P["window"], Mw)
    if bust is not None:
        stranger_in_window(c, P, wx, bust, **kw)
    letters(c, ["TICKET", "OFFICE"], 22, wx, 300, seed)


# ------------------------------------------------------------------ boards (cut at native 372 px height)
def board(n, P, st):
    full = n in FULL
    w = int(round((1980 if full else 960) / K))
    h = BH
    c = E.card(w, h, 6810 + n)
    gy = h - 30
    rec = {}
    if n != 3:
        b3.ground_line(c, 0, w, gy, 6820 + n)
    s = 0.33
    bust = P["hyde_bust"]
    if n == 1:      # E0: the office, wide: desk and memo, the wall clock, the cupboard and the SERVICE door far off
        lay(c, P["table"], Mof(0.40, 0, np.array([250, 980]) * OPS, (380, gy + 2)))
        b3.memo(c, 335, 186, 0.62, 6830, deg=-4)
        b3.clock(c, 1180, 92, 44, 4, 9, 6831)
        window_with_stranger(c, P, 1560, 6832, None)
        b3.cupboard(c, 1960, 70, 2140, gy - 20, 0.0, 6833)
        b3.service_door(c, 2210, 54, 2370, gy, 6834)
        rise = st.get("rise", 1.0)
        rec["agent"] = agent_with_pencil(c, P, (620 + 120 * rise, gy + 2), s, arms=(-30 * rise, 10, -10), head=8,
                                         pdeg=-70, seed=6835)
    elif n == 2:    # E0-E1: crossing the floor, he stops; a hat behind the glass. Pose: arm swung back, mid-stride
        window_with_stranger(c, P, 830, 6840, bust, shift=0.0, s=0.13)
        b3.cupboard(c, 980, 70, 1140, gy - 20, 0.0, 6841)
        rec["agent"] = agent_with_pencil(c, P, (420, gy + 2), s, arms=(-38, 22, 18), flip=True, head=4, pdeg=80,
                                         seed=6842)
    elif n == 3:    # the eyes, split by the window's sash: his (left), hers under her hat brim (right)
        mid = w // 2
        hp = eyes_piece(P, "head", (596, 147, 596 + 187, 147 + 227))
        Mh = Mof(2.3, 0, (596 + 95, 147 + 112), (mid * 0.5, h * 0.48))
        lay(c, hp, Mh, margin=0)
        ep = P["hyde_eyes"]
        x0, y0, x1, y1 = HYDE_EYES
        sc = (w - mid - 20) / (x1 - x0) * 1.04
        lay(c, ep, Mof(sc, 0, HYDE_EYES_C, (mid + (w - mid) / 2 + 6, h * 0.50)), margin=0)
        m = np.zeros(c.shape[:2], np.uint8)
        cv2.rectangle(m, (mid - 14, 0), (mid + 14, h), 255, -1)
        penlib.ink_onto(c, m, b3.INK)
    elif n == 4:    # E1: the standoff at the glass, hands at the hip; she draws first
        window_with_stranger(c, P, 860, 6850, bust, shift=0.0)
        # close on his middle: both hands at the hip, the near one hovering, fingers ready (head out of shot)
        rec["hand"] = b3.agent(c, P, (330, gy + 560), 0.78, arms=st.get("arms", (-8, -6, 0)), flip=True, head=-2)
        q = rec["hand"]
        for k, (dx, dy, ex, ey) in enumerate(((-40, -30, -64, -62), (0, -46, 0, -86), (40, -30, 64, -62))):
            pen(c, [(q[0] + dx, q[1] + dy), (q[0] + ex, q[1] + ey)], 4, 6855 + k)      # pen twitch marks
    elif n == 5:    # E2: the clock fills the shot, the duel's timer; his head turned up to it, low left, pencil in hand
        big_clock(c, w * 0.62, h * 0.38, 118, st.get("ss", 9), 6860)
        rec["agent"] = agent_with_pencil(c, P, (170, gy + 120), 0.40, arms=(-20, 40, 0), flip=True, head=-22,
                                         pdeg=-60, seed=6863)
        letters(c, ["tick"], 26, w * 0.62 + 200, 90, 6861, colour=b3.GRAPH)
        letters(c, ["tock"], 26, w * 0.62 + 230, 150, 6862, colour=b3.GRAPH)
    elif n == 6:    # E3: the thanks; she tips her head and turns away; a tumbleweed rolls past on the platform.
        # Pose: his pencil hand raised, half a salute, as she goes
        window_with_stranger(c, P, 560, 6870, bust, shift=0.30, flip=True, deg=-8)
        rec["agent"] = agent_with_pencil(c, P, (270, gy + 2), s, arms=(70, 95, 0), flip=True, head=10, pdeg=-20,
                                         seed=6873)
        tx = st.get("tw", 1.0)
        tumbleweed(c, 800 + 280 * tx, gy - 62, 64, 6871, rot=tx * 6)
    elif n == 7:    # E4: the cupboard open, the key on its hook. Pose: his arm out to the open door, pencil in hand
        b3.service_door(c, 840, 60, 1000, gy, 6880)
        b3.cupboard(c, 480, 70, 700, gy - 20, st.get("open", 0.8), 6881)
        q0 = agent_pts((300, gy + 2), s, (0, 0, 0), -4, True)
        arms7, _ = reach((300, gy + 2), s, q0["chin"] + np.array([118, 70]), -4, a1=(0, 60))
        rec["agent"] = agent_with_pencil(c, P, (300, gy + 2), s, arms=(arms7[0], arms7[1], -6), flip=True, head=-4,
                                         pdeg=0, seed=6883)
    else:           # E5: the wide again: before the open cupboard, facing it, pencil to chin; the window empty
        lay(c, P["table"], Mof(0.40, 0, np.array([250, 980]) * OPS, (380, gy + 2)))
        b3.memo(c, 335, 186, 0.62, 6890, deg=-4)
        b3.clock(c, 820, 92, 44, 4, 11, 6891)
        window_with_stranger(c, P, 1080, 6892, None)
        cx0, cx1 = 1760, 1960
        b3.cupboard(c, cx0, 132, cx1, gy - 20, 1.0, 6893)     # (set lower: the balloon hangs above it)
        b3.service_door(c, 2100, 54, 2270, gy, 6894)
        s8 = 0.27
        foot = (cx0 - 118, gy + 2)
        hd = -6
        q0 = agent_pts(foot, s8, (0, 0, 0), hd, True)
        want = q0["chin"] + np.array([14, 58])                    # the hand below and before the chin
        arms, err = reach(foot, s8, want, hd)
        rec["agent"] = agent_with_pencil(c, P, foot, s8, arms=arms, head=hd, flip=True, plen=60,
                                         to=q0["chin"] + np.array([4, 3]), seed=6895)
        rec["agent"]["reach_err"] = err
        rec["agent"]["foot"] = foot
        rec["cupboard"] = (cx0, cx1)
    return c, rec


BALLOONS = {   # n: (lines, cap, centre (board px at sheet scale), tail tip)
    4: (Q, 30, (520, 84), (680, 110)),
    5: (A, 30, (330, 70), (190, 92)),
    6: (T, 34, (640, 82), (488, 92)),
    8: (F, 25, None, None),     # set in build(): beside his head, the tail ending at his mouth
}


def letterbox(pg, x0, y0, w, h, bar=16):
    m = np.zeros(pg.shape[:2], np.uint8)
    m[y0:y0 + bar, x0:x0 + w] = 255
    m[y0 + h - bar:y0 + h, x0:x0 + w] = 255
    penlib.ink_onto(pg, m, b3.INK)


def bill(pg, seed=6990):
    """the head of the sheet: a torn bill pinned up, frontier-poster lettering in the pen hand"""
    t1, t2, t3 = BILL_T
    ww = max(t1.shape[1], t2.shape[1], t3.shape[1]) + 200
    hh = BILL_H
    x, y = (W - ww) // 2, 104
    rnd = random.Random(seed)
    m = np.zeros(pg.shape[:2], np.uint8)
    top = [(x + k, y + rnd.uniform(-5, 4)) for k in range(0, ww, 14)]
    rt = [(x + ww + rnd.uniform(-4, 4), y + k) for k in range(0, hh, 14)]
    bot = [(x + ww - k, y + hh + rnd.uniform(-6, 5)) for k in range(0, ww, 14)]
    lt = [(x + rnd.uniform(-4, 4), y + hh - k) for k in range(0, hh, 14)]
    cv2.fillPoly(m, [np.int32([[p[0] * 4, p[1] * 4] for p in top + rt + bot + lt])], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(pg, m, off=6, blur=5, opacity=0.32)
    pg[:] = pg * (1 - m[..., None] / 255) + b3.SLIPC * (m[..., None] / 255)
    yy = y + 2
    for mm in (t1, t2, t3):
        sub = np.zeros(pg.shape[:2], np.uint8)
        xx = (W - mm.shape[1]) // 2
        sub[yy:yy + mm.shape[0], xx:xx + mm.shape[1]] = mm
        penlib.ink_onto(pg, sub, penlib.INK)
        yy += mm.shape[0] - BILL_OV
    # a pen five-point star each side, the frontier bill's ornament
    for side in (-1, 1):
        cx, cy, r = W / 2 + side * (t1.shape[1] / 2 + 70), y + 70, 40
        pts = [(cx + (r if k % 2 == 0 else r * 0.42) * math.sin(k * math.pi / 5),
                cy - (r if k % 2 == 0 else r * 0.42) * math.cos(k * math.pi / 5)) for k in range(10)]
        pen(pg, pts, 4, seed + 10 + side, closed=True)
    for px in (x + 24, x + ww - 24):
        b3.pin(pg, px, y + 22, 7)


SHEET = E.SHEET
RECS = {}
_P = {}


def load_all():
    if not _P:
        _P.update(b3.load_puppets())
        _P["hyde_bust"], _P["hyde_eyes"] = hyde_pieces()
    return _P


def shot8_balloon(rec):
    """the forgetting balloon in front of his face, over the cupboard's top (sheet-scale px from the board
    origin); its tail ends at his mouth"""
    q = rec["agent"]
    m = q["mouth"] * K
    top = q["top"] * K
    ctr = (m[0] + 182, 60)            # in front of his face, above the open cupboard
    tip = (m[0] + 6, m[1] + 1)
    return ctr, tip


def build(upto=8, st=None, line_upto=8):
    st = st or {}
    pg = SHEET.copy()
    P = load_all()
    bill(pg)
    for n in range(1, 9):
        if n > upto:
            continue
        x0, y0, w, h = BX[n]
        fr, hh, mm, ss, txt = SHOTS[n]
        hdr = pen99.letter([f"SHOT {n}    {fr}"], 30, 6900 + n)
        sub = np.zeros(pg.shape[:2], np.uint8)
        sub[y0 - 44:y0 - 44 + hdr.shape[0], x0 - 14:x0 - 14 + hdr.shape[1]] = hdr
        penlib.ink_onto(pg, sub, b3.GRAPH)
        tm = pen99.letter([f"{hh}:{mm:02d}:{ss:02d}"], 30, 6910 + n)
        sub = np.zeros(pg.shape[:2], np.uint8)
        tx = x0 + w - tm.shape[1] - 40
        sub[y0 - 44:y0 - 44 + tm.shape[0], tx:tx + tm.shape[1]] = tm
        penlib.ink_onto(pg, sub, b3.INK)
        mini_clock(pg, x0 + w - 22, y0 - 22, 17, hh, mm, ss, 6920 + n)
        art, rec = board(n, P, st.get(n, {}))
        RECS[n] = rec
        art = cv2.resize(art, (w, h), interpolation=cv2.INTER_AREA)
        pg[y0:y0 + h, x0:x0 + w] = art
        letterbox(pg, x0, y0, w, h)
        if n in BALLOONS and n <= line_upto:
            lines, cap, ctr, tip = BALLOONS[n]
            if n == 8:
                ctr, tip = shot8_balloon(rec)
            (cx, cy), (tx_, ty_) = ctr, tip
            E.balloon(pg, lines, cap, (x0 + cx, y0 + cy), (x0 + tx_, y0 + ty_), 6940 + n)
        bm = penlib.border_mask(pg.shape[:2], [(x0, y0, x0 + w, y0 + h)], 7, 6950 + n)
        penlib.ink_onto(pg, bm)
        E.slip_left(pg, B.wrap(txt, SCAP, w - 90), SCAP, x0 + 8, y0 + h + 10, 6800 + n)
    return pg


def main():
    page = build()
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    # the duel on the clock: shot by shot, the timer running; the question laid, the clock's second hand ticking,
    # the answer, the tumbleweed rolling past, the forgetting
    frames = [build(2), build(3), build(4, line_upto=3), build(4), build(5, {5: {"ss": 4}}, line_upto=4),
              build(5, {5: {"ss": 9}}), build(6, {6: {"tw": 0.0}}), build(8)]
    for f in frames:
        pen99.folio(f, N, TITLE)
    print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    main()
