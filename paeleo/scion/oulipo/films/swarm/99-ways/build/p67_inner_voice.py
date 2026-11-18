"""Page 67 Inner voice (voice and language; medium: daumier-collage).

The agent's thoughts run in cloud balloons beside the spoken lines; we watch the errand leave his head.
Six collage panels under a masthead slip. Spoken lines (the four canon lines, verbatim) are in the kit's smooth
pen balloons with pointed tails; his thoughts are in HANDMADE cut-paper CLOUDS (scalloped scissor outline) joined
to his head by a chain of paper bubbles. The errand cloud carries the memo's content and a small cut of the
brass key. In panel 4, at the thanks, the bubble chain breaks and the errand cloud sails off out through the
ticket window after her; at the cupboard his cloud holds only 'Now then...', and at the forgetting it is empty.
Reuses page 12/50's Daumier collage kit (build/daumier12.py, p12_loop.py, p50_brief_meeting.py): FORAGED CC0
lithographs by Honore Daumier (Rijksmuseum via Commons) and the ANRC 1922 key cutout; LoC 1934 sheet ground.
Run: python3 -I p67_inner_voice.py [--page-only]
"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import daumier12 as D
import p12_loop as L
import p50_brief_meeting as B

N, PID, TITLE = 67, "inner-voice", "Inner voice"
SHEET = B.SHEET
PAPER = B.PAPER
CLOUD = np.array([250, 248, 240], np.float32)
BCAP, TCAP, CAP = 42, 34, 30

BOX = {"P1": (110, 330, 1035, 1030), "P2": (1075, 330, 2090, 1030),
       "P3": (110, 1070, 900, 1770), "P4": (940, 1070, 2090, 1770),
       "P5": (110, 1810, 960, 2730), "P6": (1000, 1810, 2090, 2730)}
ORDER = ["P1", "P2", "P3", "P4", "P5", "P6"]


# ------------------------------------------------------------------ HANDMADE cut-paper thought clouds
def _cut_layer(c, mask, seed, ink_w=4.6):
    """lay a paper shape: scissor rim, shadow, cream paper, pen outline"""
    pm = penlib.scissor((mask > 127).astype(np.uint8) * 255, 5)
    penlib.shadow_onto(c, pm, off=5, blur=4, opacity=0.32)
    comp(c, pm, CLOUD)
    cs, _ = cv2.findContours((mask > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    o = np.zeros(c.shape[:2], np.uint8)
    for cc in cs:
        pts = [tuple(map(float, p)) for p in cc[:, 0, :][::3]]
        if len(pts) > 3:
            penlib.brush_line(o, pts + [pts[0]], ink_w, seed)
    comp(c, o, INK)


def cloud_mask(shape, cx, cy, rx, ry, seed):
    """a cloud: an ellipse core with a ring of overlapping scallops round its rim"""
    rnd = random.Random(seed)
    m = np.zeros(shape, np.uint8)
    cv2.ellipse(m, (int(cx * 4), int(cy * 4)), (int(rx * 4), int(ry * 4)), 0, 0, 360, 255, -1, cv2.LINE_AA, shift=2)
    per = 2 * math.pi * math.sqrt((rx * rx + ry * ry) / 2)
    n = max(8, int(per / (min(rx, ry) * 0.62)))
    t0 = rnd.uniform(0, 6.28)
    for k in range(n):
        t = t0 + 2 * math.pi * k / n
        r = min(rx, ry) * rnd.uniform(0.34, 0.46)
        x, y = cx + rx * math.cos(t), cy + ry * math.sin(t)
        cv2.circle(m, (int(x * 4), int(y * 4)), int(r * 4), 255, -1, cv2.LINE_AA, shift=2)
    return m


def cloud(c, lines, cap, at, toward, seed, key=False, chain=3, broken=False, minr=(0, 0)):
    """a thought cloud centred at `at`; a chain of shrinking bubbles runs to `toward` (his head).
    broken: the chain stops short, its last bubbles lie loose by his head and the cloud is free."""
    cx, cy = at
    lm = letter(lines, cap, seed + 1) if lines else np.zeros((int(cap * 1.4), int(cap * 3)), np.uint8)
    h, w = lm.shape
    kh = int(cap * 2.2) if key else 0
    rx = max(minr[0], w * 0.5 * 1.02 + cap * 0.2)
    ry = max(minr[1], (h + kh) * 0.5 * 1.0 + cap * 0.2)
    # bubbles
    a = math.atan2(toward[1] - cy, toward[0] - cx)
    e = np.array((cx + rx * 1.15 * math.cos(a), cy + ry * 1.15 * math.sin(a)))
    t = np.array(toward, float)
    sizes = [(0.18, 0.30), (0.50, 0.22), (0.80, 0.15)][:chain]
    if broken:     # the two inner bubbles left by his head, the outer one gone with the cloud
        sizes = [(0.10, 0.27), (0.78, 0.15), (0.92, 0.11)]
    for k, (f, r) in enumerate(sizes):
        q = e + (t - e) * f
        m = np.zeros(c.shape[:2], np.uint8)
        rr = cap * r * 2.0
        cv2.ellipse(m, (int(q[0] * 4), int(q[1] * 4)), (int(rr * 1.2 * 4), int(rr * 4)), 0, 0, 360, 255, -1, cv2.LINE_AA,
                    shift=2)
        _cut_layer(c, m, seed + 10 + k, ink_w=3.6)
    _cut_layer(c, cloud_mask(c.shape[:2], cx, cy, rx, ry, seed), seed + 5)
    im = np.zeros(c.shape[:2], np.uint8)
    blit_mask(im, lm, int(cx - w / 2), int(cy - (h + kh) / 2))
    comp(c, im, INK)
    if key:
        key_icon(c, cx, cy + (h + kh) / 2 - kh * 0.5, cap * 0.0068, seed)
    return (cx - rx, cy - ry, cx + rx, cy + ry)


def key_icon(c, x, y, s, seed, deg=90):
    """the ANRC brass key cut small, lying in the thought"""
    kp = dict(gray=penlib.levels(key_gray(), 22, 212, 0.95), alpha=key_alpha(), origin=(0, 0))
    D.glue(c, kp, D.M_for(kp, (x, y), s, deg), rim=2, tint=np.array([1.0, 0.86, 0.55], np.float32))


def head_pt(Mh, dx=0, dy=0):
    p = L.at_src(Mh, L.HEAD, (846, 520))
    return (p[0] + dx, p[1] + dy)


def mouth_pt(Mh):
    return L.at_src(Mh, L.HEAD, (786, 642))


# ------------------------------------------------------------------ panels
def P1(st):
    """E0: at the desk, the memo; the errand forms in his head"""
    w, h = 925, 700
    c, fl = B.ground(w, h, fl_frac=0.84)
    ch = penlib.about((150, fl + 4), penlib.R(-6))
    for poly in [[(120, 360), (146, 360), (146, fl + 4), (120, fl + 4)], [(120, 470), (262, 470), (262, 490), (120, 490)],
                 [(240, 490), (258, 490), (258, fl + 4), (240, fl + 4)]]:
        L.set_piece(c, "mid", [tuple(penlib.apply(ch, q)) for q in poly], rim=3, shade=0.78)
    top = 450
    foot = (330, fl + 66)
    d, sh, el = B.solve_to(foot, 1, 0.40, 10, (478, top + 4))
    r = B.agent2(c, foot=foot, face=1, scale=0.40, head_deg=14, body_deg=10, sh=sh, el=el)
    L.desk(c, 470, top, 400, fl + 8)
    L.memo_slip(c, 560, 392, cap=21, tilt=-4, seed=6711)
    if st.get("think", True):
        cloud(c, ["4:15, the SERVICE door.", "The key's in the cupboard."], TCAP, (590, 150), head_pt(r["Mh"], 10, -6), 6712,
              key=True)
    B.cap_at(c, "He reads the memo. He gets up.", 420, 6713, corner="bl", inset=14)
    return c


def P2(st):
    """E0 -> E1: on his way, still thinking it; the question at the glass"""
    w, h = 1015, 700
    c, fl = B.ground(w, h, fl_frac=0.84)
    B.window(c, 200, 420, 0.60, fl, woman=(-10, -1, 0.50))
    _, Mh = L.agent(c, (860, fl + 66), face=-1, scale=0.40, head_deg=-6)
    cloud(c, ["Key, cupboard, door.", "Key, cupboard, door."], TCAP, (790, 130), head_pt(Mh, -6, -8), 6721, key=True)
    balloon(c, ["Pardon me —", "have you the", "right time?"], BCAP, (560, 410), (300, 450), 6722, tail_w=0.22)
    return c


def P3(st):
    """E2: the clock; a new thought pushes in beside the errand"""
    w, h = 790, 700
    c, fl = B.ground(w, h, fl_frac=0.84)
    L.clock(c, 140, 300, 84)
    _, Mh = L.agent(c, (600, fl + 66), face=-1, scale=0.40, head_deg=28)
    hp = head_pt(Mh, 0, -6)
    cloud(c, ["...key,", "cupboard..."], 26, (650, 118), hp, 6731, chain=2)
    cloud(c, ["Ten past.", "Five minutes yet."], TCAP, (360, 128), hp, 6732)
    balloon(c, ["Ten past four,", "by the clock."], BCAP, (400, 430), (mouth_pt(Mh)[0] - 6, mouth_pt(Mh)[1] + 2), 6733,
            tail_w=0.22)
    return c


def P4(st):
    """E3: the thanks; the bubble chain breaks and the errand cloud sails out through the ticket window after her"""
    w, h = 1150, 700
    c, fl = B.ground(w, h, fl_frac=0.84)
    B.window(c, 230, 470, 0.60, fl, woman=(-150, 1, 0.50))
    _, Mh = L.agent(c, (960, fl + 66), face=-1, scale=0.40, head_deg=-4)
    hp = head_pt(Mh, -4, -8)
    f = st.get("drift", 1.0)            # 0: still joined to his head; 1: gone out by the window
    start, end = np.array([800.0, 140.0]), np.array([290.0, 118.0])
    at = tuple(start + (end - start) * f)
    balloon(c, ["Much", "obliged!"], 46, (470, 470), (150, 400), 6741, tail_w=0.24)
    if f < 0.05:
        cloud(c, ["4:15, the SERVICE door.", "The key's in the cupboard."], 28, at, hp, 6742, key=True)
    else:
        # the chain broken: two loose bubbles left by his head, the cloud free and travelling
        cloud(c, ["4:15, the SERVICE door.", "The key's in the cupboard."], 28, at, (at[0] + 420, at[1] + 10), 6742,
              key=True, chain=0)
        for k, (dx, dy, r) in enumerate(((-30, -30, 13), (-62, -66, 9))):
            m = np.zeros(c.shape[:2], np.uint8)
            cv2.ellipse(m, (int((hp[0] + dx) * 4), int((hp[1] + dy) * 4)), (int(r * 1.2 * 4), int(r * 4)), 0, 0, 360, 255, -1,
                        cv2.LINE_AA, shift=2)
            _cut_layer(c, m, 6745 + k, ink_w=3.4)
        # pen speed lines behind the cloud, the way it went
        sm = np.zeros(c.shape[:2], np.uint8)
        x1 = at[0] + 250
        for k, dy in enumerate((-40, 0, 40)):
            penlib.brush_line(sm, [(x1 + 20, at[1] + dy), (x1 + 20 + 120 * min(1, f * 2), at[1] + dy)], 4, 6747 + k)
        comp(c, sm, INK, 0.8)
    if st.get("cap", True):
        B.cap_at(c, "Here the errand leaves his head: off it goes, after her.", 360, 6749, corner="br", inset=14)
    return c


def P5(st):
    """E4: the cupboard open, the key in plain view; nothing in the cloud to match it"""
    w, h = 850, 920
    c, fl = B.ground(w, h, fl_frac=0.86)
    L.PH = fl / 0.80
    L.cupboard(c, 200, 330, 190, 300, open_=st.get("open", True))
    B.full_door(c, 430, 318, 574, fl + 4)
    _, Mh = L.agent(c, (720, fl + 70), face=-1, scale=0.46, head_deg=4)
    cloud(c, ["Now then..."], TCAP, (560, 150), head_pt(Mh, 0, -8), 6751)
    B.cap_at(c, "The cupboard. The key on its hook, in plain view.", 400, 6752, corner="tl", inset=14)
    return c


def P6(st):
    """E5: the forgetting, spoken aloud to himself; the cloud is empty"""
    w, h = 1090, 920
    c, fl = B.ground(w, h, fl_frac=0.86)
    L.cupboard(c, 150, 330, 190, 300, open_=True)
    B.full_door(c, 380, 318, 524, fl + 4)
    d, sh, el = B.solve_chin(0.48, -4, target_off=(-44, 78))
    r = B.agent2(c, foot=(700, fl + 70), face=-1, scale=0.48, head_deg=-4, sh=sh, el=el, pencil=True)
    hp = head_pt(r["Mh"], 0, -8)
    cloud(c, [], TCAP, (st.get("cx", 860), 150), hp, 6761, minr=(120, 72))
    if st.get("line", True):
        balloon(c, ["Well, here I am...", "and what for?"], BCAP, (470, 250), (r["mouth"][0] - 8, r["mouth"][1] - 4), 6762,
                tail_w=0.22)
    B.cap_at(c, "Nothing left in it. The key stays on its hook; the SERVICE door stays closed.", 470, 6763, corner="br",
             inset=14)
    return c


PANELS = {"P1": P1, "P2": P2, "P3": P3, "P4": P4, "P5": P5, "P6": P6}


def masthead(pg):
    slip(pg, 420, 116, ["INNER VOICE"], 88, 6790, paper=PAPER, align="centre", min_w=1360, pad=(40, 16), shadow=0.4,
         weight=0.12)
    # the key to the page: a speech balloon and a thought cloud, side by side under the title
    sub = np.zeros(pg.shape[:2], np.uint8)
    put_mask(sub, letter(["what he says"], 32, 6791), 760, 288)
    put_mask(sub, letter(["what he thinks"], 32, 6792), 1440, 288)
    comp(pg, sub, INK)
    balloon(pg, ["Ah."], 30, (575, 272), (625, 300), 6793, tail_w=0.3)
    cloud(pg, ["Hm."], 28, (1660, 262), (1720, 300), 6794, chain=1)


def build(state=None, upto=6):
    state = state or {}
    pg = SHEET.copy()
    masthead(pg)
    rects = []
    for i, k in enumerate(ORDER):
        if i >= upto:
            break
        x0, y0, x1, y1 = BOX[k]
        pg[y0:y1, x0:x1] = PANELS[k](state.get(k, {}))
        rects.append(BOX[k])
    frame_border(pg, rects, w=11, seed=6796)
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
        states = [({"P1": {"think": False}}, 1), ({}, 1), ({}, 3),
                  ({"P4": {"drift": 0.0, "cap": False}}, 4), ({"P4": {"drift": 0.35, "cap": False}}, 4),
                  ({"P4": {"drift": 0.7, "cap": False}}, 4), ({"P4": {"drift": 1.0}}, 4),
                  ({}, 6)]
        save_beats(N, [np.asarray(Image.fromarray(finish(build(s, u))).resize((960, 1242), Image.LANCZOS)) for s, u in states])
        print("beats", len(states))
