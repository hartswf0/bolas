"""Page 66 The plan (time and order; medium: pen-hand).

Six panels, each drawn twice over in the shared pen hand: what the 4:15 memo planned, in pale washed ink (the ghost),
and what happened, in full black ink (the solid). The ghost agent keeps to the memo: rises, walks straight past the
window, lifts the key off its hook, carries it to the SERVICE door, turns it in the lock at 4:14 and at 4:15 the ghost
door swings open. The solid agent is stopped at the window, answers, is thanked, opens the cupboard, and forgets: the
key stays on its hook and the real SERVICE door stays shut under the open ghost leaf. A two-line caption tops every
panel, the plan in pale ink and the fact in black.
Pen: page 51's one pen (p51_pen_alone.Pen: the folio's 4.42 px pen run along b1m2's HANDMADE figure model outlines,
hidden lines lifted), here in two inks. Ground: the LoC 1934 sheet.
Run: python3 -I p66_the_plan.py
"""
import json
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
from b1m2 import pen99, penlib, ROOT  # noqa: E402
import p51_pen_alone as P51  # noqa: E402
from p51_pen_alone import Pen, floor, memo, key, service_card, window_with, letters  # noqa: E402

N, PID, TITLE = 66, "the-plan", "The plan"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
W, H = 2200, 2850
GHOST = np.array([120, 146, 170], np.float32)      # washed blue-grey ink
GHOST_A = 0.62
PW, PH = 975, 845
COLS = [(110, 1085), (1115, 2090)]
ROWS = [(110, 955), (990, 1835), (1870, 2715)]
BOX = {k: (COLS[(k - 1) % 2][0], ROWS[(k - 1) // 2][0], COLS[(k - 1) % 2][1], ROWS[(k - 1) // 2][1]) for k in range(1, 7)}
FL = 790
CAPS = [
    ("Plan: up from the desk, straight to the cupboard.", "Fact: he rises and sets off."),
    ("Plan: on past the ticket window.", "Fact: a voice at the window stops him."),
    ("Plan: the key lifted off its hook.", "Fact: he looks up at the clock."),
    ("Plan: key in hand, on to the SERVICE door.", "Fact: she thanks him and goes."),
    ("Plan: 4:14, the key turns in the lock.", "Fact: the cupboard opens on the key."),
    ("Plan: 4:15, the SERVICE door opens.", "Fact: the key stays; the door stays shut."),
]
GHOST_DID = ["rises and heads straight for the cupboard (dotted route)", "walks on past the window",
             "at the open cupboard, lifts the key off its hook", "carries the key toward the SERVICE door",
             "turns the key in the SERVICE door's lock", "the ghost leaf of the SERVICE door swings open; he steps through"]


def hand_of(shapes):
    hs = [s for s in shapes if s.role == "skin" and s.z == 5]
    return np.asarray(hs[-1].curve(), float).mean(0)


def ghost_key(p, at, s=0.7, deg=0):
    """a small key in outline held in the ghost hand (bow, shank, bit)"""
    x, y = at
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    T = lambda pts: [tuple(np.array([x, y]) + R @ (np.array(q) * s)) for q in pts]
    ring = [(14 * math.cos(t), 14 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    p.shape(T(ring))
    p.shape(T([(10, -4), (78, -4), (78, 4), (10, 4)]))
    p.shape(T([(62, 4), (62, 18), (70, 18), (70, 10), (78, 10), (78, 4)]))


def caption(p, k):
    """two lines at the panel head: the plan (ghost pen) and the fact (solid pen); returns the ghost part"""
    g = Pen(PW, PH, 6690 + k)
    g.text.append((letters([CAPS[k][0]], 34, 660 + k), PW / 2, 46))
    p.text.append((letters([CAPS[k][1]], 34, 670 + k), PW / 2, 100))
    return g


def dotted(p, pts, dash=14, gap=16):
    pts = np.asarray(pts, float)
    for a, b in zip(pts[:-1], pts[1:]):
        L = np.hypot(*(b - a))
        n = int(L // (dash + gap))
        for i in range(n + 1):
            t0, t1 = i * (dash + gap) / L, min(1, (i * (dash + gap) + dash) / L)
            if t0 < 1:
                p.line([a + (b - a) * t0, a + (b - a) * t1])


def ticket_window(p, sill, st_at, face, seed, wx0=50, wy0=350, ww=330):
    """p51.window_with with its lettering set right of centre, so a balloon tail can come in through the glass"""
    p.shapes(B.stranger(*st_at, face=face, scale=1.15))
    ws, _ = B.window(wx0, wy0, ww, FL - wy0, sill=sill, header=72)
    p.shapes(ws)
    p.word(["TICKET OFFICE"], 30, wx0 + ww / 2 + 40, wy0 + 38, seed)


# ------------------------------------------------------------------ panels: (solid Pen, ghost Pen)
def P1(st):
    s, g = Pen(PW, PH, 6601), None
    g = caption(s, 0)
    floor(s, PW, FL)
    s.shapes(B.desk(60, 560, 420, FL))
    memo(s, 200, 506, 6602)
    cs, _ = B.cupboard(790, 330, 150, FL - 330 - 20)
    s.shapes(cs)
    s.shapes(B.agent(540, FL, face=1, scale=0.62, legs=(18, -16), sh=-16, el=20, lean=3, pencil_deg=200))
    g.shapes(B.agent(690, FL, face=1, scale=0.62, legs=(-22, 24), sh=26, el=10, lean=6, pencil_deg=200))
    dotted(g, [(520, FL + 30), (780, FL + 30)])
    g.line([(770, FL + 18), (790, FL + 30), (770, FL + 42)])
    return s, g


def P2(st):
    s = Pen(PW, PH, 6611)
    g = caption(s, 1)
    floor(s, PW, FL)
    ticket_window(s, 680, (130, 770), 1, 6612)
    s.shapes(B.agent(510, FL, face=-1, scale=0.62, sh=6, el=16, tilt=4, pencil_deg=190))
    s.balloon(["Pardon me —", "have you the", "right time?"], 250, 236, (110, 470), 6613, cap=38)
    cs, _ = B.cupboard(880, 330, 150, FL - 330 - 20)
    s.shapes(cs)
    g.shapes(B.agent(740, FL, face=1, scale=0.62, legs=(-22, 24), sh=26, el=10, lean=6, pencil_deg=200))
    return s, g


def P3(st):
    s = Pen(PW, PH, 6621)
    g = caption(s, 2)
    floor(s, PW, FL)
    s.shapes(B.clock(140, 330, 78, 4, 10))
    s.shapes(B.agent(380, FL, face=-1, scale=0.62, sh=6, el=16, tilt=-24, pencil_deg=190, lean=-4))
    s.balloon(["Ten past four,", "by the clock."], 236, 178, (360, 346), 6622, cap=32)   # up-left, his head clear
    cs, _ = B.cupboard(650, 300, 230, FL - 300 - 20)          # the real cupboard, still shut
    s.shapes(cs)
    gc, ins = B.cupboard(650, 300, 230, FL - 300 - 20, open_deg=70)
    g.shapes([q for q in gc if q.role in ("door", "inside", "shelf")])
    ga = B.agent(560, FL, face=1, scale=0.62, sh=88, el=-30, tilt=-6, pencil=False)
    g.shapes(ga)
    ghost_key(g, hand_of(ga) + (6, 10), 0.8, 80)
    return s, g


def P4(st):
    s = Pen(PW, PH, 6631)
    g = caption(s, 3)
    floor(s, PW, FL)
    ticket_window(s, 680, (80, 770), -1, 6632)
    s.shapes(B.agent(500, FL, face=-1, scale=0.62, sh=4, el=12, pencil_deg=190))
    s.balloon(["Much", "obliged!"], 220, 232, (70, 470), 6633, cap=42)
    s.shapes(B.service_door(820, 250, 130, FL - 250))
    service_card(s, 885, 330, 6634)
    ga = B.agent(700, FL, face=1, scale=0.62, legs=(-22, 24), sh=40, el=-40, lean=6, pencil=False)
    g.shapes(ga)
    ghost_key(g, hand_of(ga) + (4, 6), 0.8, 10)
    return s, g


def P5(st):
    s = Pen(PW, PH, 6641)
    g = caption(s, 4)
    floor(s, PW, FL)
    cs, ins = B.cupboard(110, 300, 240, FL - 300 - 20, open_deg=72)
    s.shapes(cs)
    key(s, (ins[0] + ins[2]) / 2 + 10, ins[1] + 70, 1.1)
    s.shapes(B.agent(460, FL, face=-1, scale=0.62, sh=26, el=30, tilt=6, pencil_deg=190))
    s.shapes(B.service_door(760, 250, 150, FL - 250))
    service_card(s, 835, 330, 6642)
    ga = B.agent(650, FL, face=1, scale=0.62, sh=62, el=-50, pencil=False)
    g.shapes(ga)
    ghost_key(g, hand_of(ga) + (6, 0), 0.8, 0)
    g.text.append((letters(["4:14"], 30, 6643), 700, 210))
    return s, g


def P6(st):
    s = Pen(PW, PH, 6651)
    g = caption(s, 5)
    floor(s, PW, FL)
    cs, ins = B.cupboard(90, 300, 240, FL - 300 - 20, open_deg=72)
    s.shapes(cs)
    key(s, (ins[0] + ins[2]) / 2 + 10, ins[1] + 70, 1.1)
    s.shapes(B.agent(470, FL - 10, face=-1, scale=0.64, sh=48, el=118, wr=8, pencil_deg=40, tilt=-6, lean=-2))
    if st.get("line", True):
        s.balloon(["Well, here I am...", "and what for?"], 205, 182, (428, 296), 6652, cap=30)   # above the cupboard, tail to his mouth
    dx0, dy0, dw = 720, 250, 150
    s.shapes(B.service_door(dx0, dy0, dw, FL - dy0))            # the real door: shut
    service_card(s, dx0 + dw / 2, 330, 6653)
    # the ghost door: the same door swung open on its left jamb toward us, the doorway dark beyond
    t = st.get("ghost_open", 1.0)
    if t > 0:
        th = math.radians(78 * t)
        ex = dx0 - dw * 0.62 * math.sin(th) + dw * math.cos(th)
        dy = (FL - dy0) * 0.08 * math.sin(th)
        g.shape([(dx0, dy0), (ex, dy0 - dy), (ex, FL + dy), (dx0, FL)])
        for fy in (0.30, 0.62):                                  # its two panels, seen on the swung leaf
            ya, yb = dy0 + (FL - dy0) * fy, dy0 + (FL - dy0) * (fy + 0.26)
            g.line([(dx0 - 8, ya), (ex + 10, ya - dy * 0.5), (ex + 10, yb + dy * 0.5), (dx0 - 8, yb)], closed=True)
        if t >= 1:
            g.shapes(B.agent(dx0 + dw * 0.55, FL, face=1, scale=0.62, legs=(-22, 24), sh=20, el=10, lean=6, pencil=False))
        g.text.append((letters(["4:15"], 30, 6654), dx0 + dw / 2, 205))
    return s, g


PANELS = [P1, P2, P3, P4, P5, P6]


def frames_mask(ks):
    p = Pen(W, H, 6690)
    for k in ks:
        x0, y0, x1, y1 = BOX[k]
        p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True)
    return cv2.resize(p.m, (W, H), interpolation=cv2.INTER_AREA)


CACHE = {}


def build(state=None, upto=6, ghosts=6):
    state = state or {}
    pg = P51.SHEET.copy()
    if "frames" not in CACHE:
        CACHE["frames"] = frames_mask(range(1, 7))
    solid = CACHE["frames"].copy()
    ghost = np.zeros((H, W), np.uint8)
    for k in range(1, upto + 1):
        x0, y0, x1, y1 = BOX[k]
        s, g = PANELS[k - 1](state.get(k, {}))
        sm, gm = s.render(), g.render()
        np.maximum(solid[y0:y1, x0:x1], sm[:y1 - y0, :x1 - x0], out=solid[y0:y1, x0:x1])
        if k <= ghosts:
            np.maximum(ghost[y0:y1, x0:x1], gm[:y1 - y0, :x1 - x0], out=ghost[y0:y1, x0:x1])
    ghost[solid > 60] = 0            # where the two inks cross, the black lies over the wash
    penlib.ink_onto(pg, ghost, GHOST, alpha=GHOST_A)
    penlib.ink_onto(pg, solid, penlib.INK)
    return pg


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    from PIL import Image
    page = build()
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    # beats: the page is drawn solid first (what happened), then the plan is washed in panel by panel; last, the
    # ghost door swings open over the shut real one
    states = [({6: {"ghost_open": 0}}, 6, 0), ({6: {"ghost_open": 0}}, 6, 2), ({6: {"ghost_open": 0}}, 6, 4),
              ({6: {"ghost_open": 0}}, 6, 5), ({6: {"ghost_open": 0.5}}, 6, 6), ({}, 6, 6)]
    frames = [finish(build(s, u, gh)) for s, u, gh in states]
    B.save_beats(N, [np.asarray(Image.fromarray(f).resize((960, 1242), Image.LANCZOS)) for f in frames])
    src = ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    B.credit_pages(src, N)
    ink = img.astype(np.float32)
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p66_the_plan.py (pen: p51_pen_alone.Pen; figure model: b1m2.py)",
        "sources": src,
        "made": [
            "six panels drawn with page 51's one pen (the folio's 4.42 px pen along b1m2's HANDMADE figure-model outlines, hidden lines lifted), in two inks: the plan in a pale washed blue-grey (62% wash), what happened in full black",
            "the ghost strand (an unrealised plan, declared by the canon): the agent rising and taking the dotted route straight to the cupboard, walking on past the window, lifting the key off its hook from a ghost-open cupboard, carrying it to the SERVICE door, turning it at 4:14, the ghost door swinging open at 4:15 with him stepping through",
            "the solid strand: E0-E5 with the four canon lines in pen-drawn balloons; the real cupboard drawn shut while the ghost one stands open over it (panel 3); the real SERVICE door drawn shut under the open ghost leaf (panel 6)",
            "a two-line caption at each panel's head in the shared pen hand: 'Plan: ...' in the ghost ink, 'Fact: ...' in black",
            "folio '66 / The plan' (pen99.folio)"],
        "captions": [{"plan": a, "fact": b} for a, b in CAPS],
        "ghost": GHOST_DID,
        "events": {"E0": "1: memo on the desk; he rises and sets off (ghost: already striding along the dotted route to the cupboard)",
                   "E1": "2: the stranger at the TICKET OFFICE window: 'Pardon me — have you the right time?' (ghost walks on past)",
                   "E2": "3: he looks up at the clock, 4:10: 'Ten past four, by the clock.' (ghost lifts the key from the ghost-open cupboard; the real one is shut)",
                   "E3": "4: 'Much obliged!' as she turns away (ghost carries the key to the SERVICE door)",
                   "E4": "5: the cupboard open, the key on its hook, tagged SERVICE (ghost at the lock, 4:14)",
                   "E5": "6: pencil to chin, 'Well, here I am... and what for?'; key on hook, the real SERVICE door shut; the ghost door open at 4:15"},
        "lines": LN,
        "beat": "what happened lies drawn in black; the plan is washed in beside it panel by panel in pale ink; last the ghost door swings open over the real one, which stays shut",
        "beat_frames": ["b01: solid strand only (six panels)", "b02: ghost strand in panels 1-2", "b03: ghost in panels 1-4",
                        "b04: ghost in panels 1-5", "b05: panel 6 ghost door half open", "b06: ghost door open, ghost agent going through; the real door shut"],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "inks": {"ghost_rgb": GHOST.tolist(), "ghost_alpha": GHOST_A, "solid": "penlib.INK #121110"},
                       "every_panel_has_ghost_and_solid_agent": True,
                       "real_service_door": "drawn shut in panels 4-6; only the ghost leaf opens",
                       "check": C["check"],
                       "pending": "independent blind reading not run by the maker"},
    }
    B.write_record(rec)
    print(json.dumps(rec["self_check"], indent=1))
