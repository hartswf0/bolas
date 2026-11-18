"""Page 65 Through his eyes (point of view; medium: paper-hands).

Eight lit paper cards on the felt board of the 99-ways-subjective lightbox, two by four, every one the agent's own
view: only his scissor-cut paper hands, cuffs and pencil are seen (the 99-ways-subjective RightHand rig; the left hand
is the same rig cut mirror-wise), never his face; the rims and bridge of his spectacles, a cut card held close to the
lamp, fall as soft out-of-focus shadows in the top corners of every card. The stranger is only heard (her balloons
come from beyond the glass) and glimpsed as a soft grey shape behind the TICKET OFFICE window.
Reused HANDMADE code (imported): p28_dealt_cards (lit card, set pieces, window, cupboard, SERVICE door, key on hook),
which itself imports 99-ways-subjective/test-shot-build/lightbox.py and e4.py; b1m2 (stranger bust, clock).
Run: python3 -I p65_through_his_eyes.py
"""
import json
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p28_dealt_cards as p28  # noqa: E402
from p28_dealt_cards import lb, facet, dense_poly, ellipse_pts  # noqa: E402
from p54_questions_for_you import pointing_hand, lay  # noqa: E402
from b1m2 import (pen99, penlib, stranger, clock, save_page, save_beats, write_record, credit_pages,  # noqa: E402
                  ROOT, W, H)

N, PID, TITLE = 65, "through-his-eyes", "Through his eyes"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
CW, CH = 1100, 680
SILK = lb.SIL_K


class Sized:
    def __init__(self, w, h):
        self.w, self.h = w, h

    def __enter__(self):
        self.saved = (p28.CW, p28.CH)
        p28.CW, p28.CH = self.w, self.h

    def __exit__(self, *a):
        p28.CW, p28.CH = self.saved


class Eye(p28.Card):
    """A p28 lit card seen from behind his spectacles: the rims fall as a soft near shadow."""
    def __init__(self, seed):
        super().__init__(seed)
        self.w, self.h = p28.CW, p28.CH
        self.rim = np.zeros((self.h, self.w), np.float32)
        w, h = self.w, self.h
        # his spectacle lens: a cut card frame near the lamp; its rim and the dark beyond it catch the card's corners,
        # with the bridge of the frame coming in at the upper left (the nose side of his right eye)
        lens = np.zeros_like(self.rim)
        self.R.fill(lens, facet(ellipse_pts(w * 0.52, h * 0.53, w * 0.57, h * 0.70), seed + 3))
        self.rim = 1 - lens
        self.R.fill(self.rim, facet(dense_poly([(-20, h * 0.10), (w * 0.05, h * 0.16), (w * 0.05, h * 0.30), (-20, h * 0.36)]), seed + 5))

    def left_hand(self, target, h_deg, pencil=None):
        """the same paper hand rig, cut mirror-wise: drawn at the mirrored place and flipped"""
        save = self.hands.copy()
        self.hands[:] = 0
        info = self.hand((self.w - target[0], target[1]), 180 - h_deg, pencil=pencil)
        flipped = self.hands[:, ::-1].copy()
        self.hands[:] = np.maximum(save, flipped)
        return info

    def render(self):
        rgb = super().render()
        rim = cv2.GaussianBlur(self.rim, (0, 0), 15) * 0.72
        rgb = rgb * (1 - (1 - SILK) * rim[..., None])
        return rgb


def desk_edge(c, y, seed):
    c.rect(-10, y, c.w + 10, c.h + 10, s=seed)


# ------------------------------------------------------------------ the eight views (card-local, 1100 x 680)
def v1():   # E0 the memo in his left hand, his pencil at the 4:15 line
    c = Eye(6511)
    desk_edge(c, 560, 1)
    c.rect(880, 440, 950, 560, s=2)                                  # inkwell
    c.poly([(880, 440), (896, 418), (934, 418), (950, 440)], s=3)
    c.slip(250, 150, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 46, 6512, tilt=-3)
    c.left_hand((262, 372), -70)
    c.hand((760, 440), -150, pencil=130)
    return c


def v2():   # E0 he pushes up from the desk: the cupboard and the SERVICE door ahead, the window to the left
    c = Eye(6521)
    c.rect(-10, 560, c.w + 10, c.h + 10, s=1)                        # floor far ahead
    p28.cupboard_set(c, 520, 210, 170, 350, open_=False, seed=10)
    p28.service_door_set(c, 760, 170, 160, 390, 30)
    c.rect(-10, 120, 70, 520, s=40)                                  # the ticket window's jamb, at the edge
    desk_edge(c, 650, 2)
    c.left_hand((230, 600), -78)
    c.hand((870, 600), -102)
    return c


def v3():   # E1 a voice beyond the glass: he turns to the window
    c = Eye(6531)
    sill = p28.window_set(c, 130, 70, 560, 600, 50)
    c.shapes(stranger(410, sill + 40, face=1, scale=1.45, glove=True), layer="far", holes=False)
    c.balloon(Q, 46, (870, 200), (560, 290), 6532)
    c.hand((900, 640), -100, pencil=110)
    return c


def v4():   # E2 he looks up at the clock: 4:10, and answers (his own balloon comes from below the frame)
    c = Eye(6541)
    c.shapes(clock(760, 230, 140, hh=4, mm=10, swing=4))
    c.hand((640, 560), -112, pencil=130)
    c.balloon(A, 46, (300, 190), (470, 700), 6542)
    return c


def v5():   # E3 her thanks; through the glass she turns and goes
    c = Eye(6551)
    sill = p28.window_set(c, 130, 70, 560, 600, 60)
    c.shapes(stranger(260, sill + 40, face=-1, scale=1.2, tilt=-6), layer="far", holes=False)
    c.balloon(T, 48, (880, 210), (330, 300), 6552)
    c.hand((960, 660), -96, pencil=100)
    return c


def v6():   # on toward the cupboard: it grows ahead, the SERVICE door beside it; his hand reaches
    c = Eye(6561)
    c.rect(-10, 610, c.w + 10, c.h + 10, s=1)
    p28.cupboard_set(c, 300, 90, 330, 520, open_=False, seed=20)
    p28.service_door_set(c, 780, 50, 250, 560, 40)
    c.hand((560, 380), -140)
    return c


def v7():   # E4 his hand swings the leaf open: the key on its hook, tagged SERVICE
    c = Eye(6571)
    c.rect(-10, 640, c.w + 10, c.h + 10, s=1)
    box, leaf = p28.cupboard_set(c, 520, 90, 340, 550, open_=True, seed=70)
    p28.key_on_hook(c, 690, 270, 0.30, 6572)
    c.hand((leaf[1][0] - 6, 220), -58)
    return c


def v8():   # E5 the key still on its hook, SERVICE door shut; his pencil goes up out of the frame to his chin
    c = Eye(6581)
    c.rect(-10, 640, c.w + 10, c.h + 10, s=1)
    box, leaf = p28.cupboard_set(c, 220, 110, 320, 530, open_=True, seed=80)
    p28.key_on_hook(c, 380, 290, 0.30, 6582)
    p28.service_door_set(c, 840, 60, 210, 580, 90)
    c.hand((520, 640), -100, pencil=130)
    c.balloon(F, 44, (640, 110), (650, 720), 6583)
    return c


VIEWS = [v1, v2, v3, v4, v5, v6, v7, v8]
EVENTS = ["E0", "E0", "E1", "E2", "E3", "E3-E4", "E4", "E5"]
CARD_W = 930
CARD_H = int(round(CARD_W * CH / CW))
COLX = [150, 1120]
ROWY = [150 + r * (CARD_H + 50) for r in range(4)]
CACHE = {}


def card_rgb(k):
    if k not in CACHE:
        with Sized(CW, CH):
            rgb = VIEWS[k]().render()
        CACHE[k] = cv2.resize(rgb, (CARD_W, CARD_H), interpolation=cv2.INTER_AREA)
    return CACHE[k]


def build(n=8):
    if "felt" not in CACHE:
        CACHE["felt"] = p28.felt()
    page = CACHE["felt"].copy()
    for k in range(n):
        x0, y0 = COLX[k % 2], ROWY[k // 2]
        lay(page, card_rgb(k), (x0, y0, x0 + CARD_W, y0 + CARD_H), 6590 + k)
    return page


# ------------------------------------------------------------------ beats: one portrait view, his hand opens the cupboard
BW, BH = 1100, 1423


def beat_view(t):
    """t in 0..5: 0 cupboard shut, hand reaching; 1-2 leaf swinging; 3 open, key; 4 pencil hand rising; 5 the line"""
    with Sized(BW, BH):
        c = Eye(6600)
        c.rect(-10, 1200, BW + 10, BH + 10, s=1)                     # floor
        x0, y0, w, h = 250, 260, 480, 900
        c.rect(x0 - 20, y0 - 40, x0 + w + 20, y0, s=2)               # cornice
        p28.service_door_set(c, 860, 200, 240, 1000, 90)
        open_k = [0.0, 0.35, 0.7, 1.0, 1.0, 1.0][t]
        if open_k == 0:
            p28.cupboard_set(c, x0, y0, w, h, open_=False, seed=3)
            c.hand((x0 + w * 0.88, y0 + h * 0.5), -150)
        else:
            c.rect(x0, y0, x0 + 30, y0 + h, s=4)
            c.rect(x0 + w - 30, y0, x0 + w, y0 + h, s=5)
            c.rect(x0, y0 + h - 34, x0 + w, y0 + h, s=6)
            for fy in (0.28, 0.72):
                c.rect(x0 + 30, y0 + h * fy, x0 + w - 30, y0 + h * fy + 18, s=7)
            # the interior: back board in shadow until the leaf clears it
            if open_k < 1:
                c.rect(x0 + 30, y0, x0 + 30 + (w - 60) * (1 - open_k), y0 + h, s=8)
            p28.key_on_hook(c, x0 + w * 0.55, y0 + h * 0.43, 0.42, 6601)
            # the leaf swings on the left jamb toward him: its free edge sweeps from the right jamb leftward
            ex = x0 + w - (w + w * 0.45) * open_k
            spread = 70 * math.sin(math.pi * open_k)
            leaf = [(x0, y0), (ex, y0 - spread - 20 * open_k), (ex, y0 + h + spread + 20 * open_k), (x0, y0 + h)]
            c.poly(leaf, s=9)
            if t < 4:
                c.hand((ex + (10 if open_k < 1 else -6), y0 + h * 0.45), -150 if open_k < 0.5 else -60)
        if t >= 4:
            lift = [0, 0, 0, 0, 0.55, 1.0][t]
            c.hand((620 - 40 * lift, BH - 40 - 260 * lift + 260), -100, pencil=140)
        if t >= 5:
            c.balloon(F, 60, (560, 120), (640, BH + 80), 6602)
        return c.render()


def beat_frame(t):
    if "bfelt" not in CACHE:
        saved = (lb.PAGE_W, lb.PAGE_H, lb.PANELS)
        lb.PAGE_W, lb.PAGE_H, lb.PANELS = 960, 1242, {}
        try:
            CACHE["bfelt"] = lb.make_page(6699)
        finally:
            lb.PAGE_W, lb.PAGE_H, lb.PANELS = saved
    fr = CACHE["bfelt"].copy()
    rgb = cv2.resize(beat_view(t), (900, 1164), interpolation=cv2.INTER_AREA)
    fr[39:39 + 1164, 30:930] = rgb
    return fr


if __name__ == "__main__":
    page = build()
    img, size_b = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size_b, "bottom", ROWY[-1] + CARD_H)
    frames = [beat_frame(t) for t in range(6)]
    save_beats(N, frames)
    src = ["99-ways-template:loc-blank-sheet-1934", "99-ways-subjective:lightbox-paper-hands",
           "99-ways-template:anrc-gold-key-1922", "99-ways:handmade"]
    credit_pages(src, N)
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p65_through_his_eyes.py (lit cards and set pieces: p28_dealt_cards.py -> 99-ways-subjective lightbox.py, e4.py)",
        "sources": src,
        "made": [
            "eight lit paper cards (p28_dealt_cards.Card: the 99-ways-subjective lamp-lit fibrous sheet, set pieces cut sharp against it) laid square two by four on the lightbox felt board, each the agent's own view",
            "his hands: the 99-ways-subjective scissor-cut RightHand rig behind the sheet (soft body and penumbra), in pinch and reach poses; his left hand the same rig cut mirror-wise; his pencil a cut bar through the pinch",
            "his spectacles: the outer arcs of two lens rims and the bridge, a cut card nearer the lamp, falling as a soft out-of-focus shadow across the top of every card (the eyes the page looks through)",
            "the stranger only heard and glimpsed: her balloons come from beyond the TICKET OFFICE glass; her figure (b1m2 stranger bust) held back behind the glass as soft grey",
            "the four canon lines in the shared cut-paper balloons; his own two lines tailed off the bottom edge of the card, toward his unseen mouth",
            "the ANRC 1922 key cutout as the key on its hook (p28.key_on_hook), SERVICE tag slip; folio '65 / Through his eyes' (pen99.folio)"],
        "events": {"E0": "1: the memo held in his left hand, pencil at the 4:15 line; 2: his two hands push up from the desk edge, the cupboard and SERVICE door ahead",
                   "E1": "3: the ticket window, her shape soft beyond the glass: 'Pardon me — have you the right time?'",
                   "E2": "4: he looks up, pencil toward the clock at 4:10: 'Ten past four, by the clock.' (tail to below the frame: his mouth)",
                   "E3": "5: she turns from the glass: 'Much obliged!'; 6: the cupboard grows ahead, his hand reaching",
                   "E4": "7: his hand swings the leaf open on the left jamb: the key on its hook, tagged SERVICE",
                   "E5": "8: key unmoved, SERVICE door shut; his pencil hand rises out of the bottom of the frame (to his chin): 'Well, here I am... and what for?'"},
        "lines": LN,
        "beat": "one view, his eyes on the cupboard: his hand reaches, swings the leaf open in steps until the key hangs in view, then the hand drops and the pencil rises out of the frame to his chin, and the line comes",
        "beat_frames": ["b01: cupboard shut, his hand at the leaf", "b02: leaf a third open", "b03: leaf two thirds open, key showing",
                        "b04: open, key on its hook, hand on the leaf edge", "b05: hand off, pencil rising", "b06: pencil up out of frame, the line"],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size_b, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size_b <= 1200000,
                       "agent_face_drawn": False,
                       "agent_figure_drawn": "hands, cuffs, sleeves and pencil only; spectacle rims as near shadow",
                       "stranger": "heard (balloons from beyond the glass) and glimpsed soft grey behind the TICKET OFFICE glass",
                       "check": C["check"],
                       "pending": "independent blind reading not run by the maker"},
    }
    write_record(rec)
    print(json.dumps(rec["self_check"], indent=1))
