"""Page 54 Questions for the reader (reader and object; medium: paper-hands).

Six lit paper cards (page 28's first-person lightbox cards, built from the HANDMADE 99-ways-subjective lightbox and
its scissor-cut RightHand rig) are laid square on the felt board, two by three. Under each card a strip of the same
lit paper carries a printed question for the reader, and behind the strip a paper hand (the same RightHand rig, posed
here with the index finger straight and the thumb tucked: a cut-paper pointing hand) reaches in from the left and points
at it. The answers run upside down along the foot of the board, numbered to match.
Run: python3 -I p54_questions_for_you.py
"""
import json
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p28_dealt_cards as p28  # noqa: E402
from p28_dealt_cards import lb, e4, facet, dense_poly  # noqa: E402
from b1m2 import (pen99, penlib, letter_left, blit_mask, comp, INK, save_page, save_beats, write_record,  # noqa: E402
                  credit_pages, ROOT, W, H)

N, PID, TITLE = 54, "questions-for-you", "Questions for the reader"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}

QUESTIONS = [
    ["1. What is he to do at 4:15,", "and where is the key?"],
    ["2. Who is at the glass,", "and what does she want?"],
    ["3. What time does the", "clock say?"],
    ["4. Does she stay", "at the window?"],
    ["5. Where is the", "key now?"],
    ["6. Will he open the", "SERVICE door?"],
]
ANSWERS = [
    "1. Open the SERVICE door; key in the cupboard.",
    "2. The stranger; she wants the time.",
    "3. Ten past four (4:10).",
    "4. No: 'Much obliged!', and she goes.",
    "5. On its hook, tagged SERVICE.",
    "6. No. He has forgotten why he came.",
]
# ------------------------------------------------------------------ the two cards re-staged for this page
WIN = (120, 90, 560, 680, 74)        # window_set(x0, y0, w, h, header) as on page 28's cards 3 and 5
GLASS_STATS = {}


def glass_mask():
    x0, y0, w, h, hd = WIN
    sill = y0 + h * 0.70
    m = np.zeros((p28.CH, p28.CW), np.float32)
    m[int(y0 + hd):int(sill), int(x0):int(x0 + w)] = 1.0
    return m


def card4_leaving():
    """E3 'Much obliged!': she has turned in profile (facing right, the way out) and is half past the right edge of the
    pane: her shadow is seen only through the glass, cut by the right post, and fading as she goes; the left pane empty.
    The thanks balloon stays tailed to her."""
    c = p28.Card(2851)
    sill = p28.window_set(c, *WIN[:4], 60)
    far = p28.stranger(668, sill + 40, face=1, scale=1.35, tilt=4)
    c.shapes(far, layer="far", holes=False)
    g = glass_mask()
    c.far[:] = c.far * g * 0.80                     # behind the office wall once she is past the post; fading
    c.balloon(["Much", "obliged!"], 50, (330, 250), (600, 300), 2852)
    GLASS_STATS["card4_far_on_glass"] = float((c.far > 0.05).sum())
    return c


def card2_ref_area():
    c = p28.card3()
    GLASS_STATS["card2_far_on_glass"] = float(((c.far * glass_mask()) > 0.05).sum())
    return GLASS_STATS["card2_far_on_glass"]


def card6_pencil_up():
    """E5: the forgetting; key still on its hook, SERVICE door shut; his pencil hand raised so the pencil point
    reaches the upper third of the card (pencil to his chin, seen from his own eyes)"""
    c = p28.Card(2871)
    c.rect(-10, 730, p28.CW + 10, p28.CH + 10, s=1)
    box, leaf = p28.cupboard_set(c, 200, 170, 320, 560, open_=True, seed=80)
    p28.key_on_hook(c, 360, 330, 0.30, 2872)
    p28.service_door_set(c, 840, 110, 220, 620, 90)
    tgt, hdeg, plen = (722, 368), -100, 120
    c.hand(tgt, hdeg, pencil=plen)
    h = math.radians(hdeg)
    Rm = np.array([[math.cos(h), -math.sin(h)], [math.sin(h), math.cos(h)]])
    d = Rm @ np.array([math.cos(math.radians(-30)), math.sin(math.radians(-30))])
    tip = np.array(tgt) + d * (plen + 22)
    GLASS_STATS["card6_pencil_tip"] = [round(float(tip[0]), 1), round(float(tip[1]), 1)]
    GLASS_STATS["card6_pencil_tip_frac_of_height"] = round(float(tip[1] / p28.CH), 3)
    c.balloon(["Well, here I am...", "and what for?"], 48, (585, 116), (500, 800), 2873)
    return c


# which panel answers which question (page 28's cards carrying E0-E2 and E4; E3 and E5 re-staged here)
CARDS = [p28.card1, p28.card3, p28.card4, card4_leaving, p28.card6, card6_pencil_up]
EVENTS = ["E0", "E1", "E2", "E3", "E4", "E5"]

# ------------------------------------------------------------------ layout (page px)
CELL_W = 900
COLX = [150, 1150]
CARD_H = int(round(CELL_W * p28.CH / p28.CW))       # 684
STRIP_H = 140
ROW_Y = [118, 118 + 830, 118 + 2 * 830]
ANS = (150, 2606, 2050, 2722)


def cells():
    out = []
    for k in range(6):
        col, row = k % 2, k // 2
        x0, y0 = COLX[col], ROW_Y[row]
        out.append(((x0, y0, x0 + CELL_W, y0 + CARD_H), (x0, y0 + CARD_H + 12, x0 + CELL_W, y0 + CARD_H + 12 + STRIP_H)))
    return out


# ------------------------------------------------------------------ lit strips (p28.Card at another size)
class Sized:
    def __init__(self, w, h):
        self.w, self.h = w, h

    def __enter__(self):
        self.saved = (p28.CW, p28.CH)
        p28.CW, p28.CH = self.w, self.h

    def __exit__(self, *a):
        p28.CW, p28.CH = self.saved


def pointing_hand(c, tip, h_deg, scale, w, h):
    """The 99-ways-subjective RightHand rig posed to point: index straight along the hand, thumb tucked over the
    curled fingers; drawn behind the lit sheet (c.hands) on the rig's own 1/scale canvas, then reduced."""
    rh = p28.RH
    hd = math.radians(h_deg)
    Rm = np.array([[math.cos(hd), -math.sin(hd)], [math.sin(hd), math.cos(hd)]])
    tb = np.asarray(tip, float) / scale
    idx_local = rh.IDX_ROOT + np.array([sum(rh.IDX_L) - 1.0, 0.0])      # nearly straight finger
    wrist = tb - Rm @ idx_local
    P = dict(h=hd, R=Rm, wrist=wrist, idx_w=wrist + Rm @ idx_local, th_w=wrist + Rm @ np.array([252.0, -100.0]),
             lift=0.15, contact=False)
    e4.O[:] = 0
    Rb = lb.Raster(0, 0, int(w / scale), int(h / scale))
    D, pins, info = rh.draw(Rb, P, tb)
    D = cv2.resize(D, (w, h), interpolation=cv2.INTER_AREA)
    c.hands[:] = np.maximum(c.hands, D)
    return info


def ink_text(lines, cap, x, y, seed):
    def f(rgb):
        m = letter_left(lines, cap, seed, 0.14)
        lm = np.zeros(rgb.shape[:2], np.uint8)
        blit_mask(lm, m, int(x - cap * 0.6), int(y))
        comp(rgb, lm, INK)
    return f


def strip_rgb(k, with_hand=True, hand_t=1.0):
    """one lit question strip at page size (CELL_W x STRIP_H): the hand behind, the question printed on"""
    w, h = CELL_W, STRIP_H
    with Sized(w, h):
        c = p28.Card(5400 + k)
        info = None
        if with_hand:
            tipx = 236 - (1 - hand_t) * 330
            info = pointing_hand(c, (tipx, h * 0.62), -6.0, 0.44, w, h)
            c.post.append(ink_text(QUESTIONS[k], 42, 272, 10, 5410 + k * 3))
        rgb = c.render()
    return rgb, info


def answer_rgb():
    x0, y0, x1, y1 = ANS
    w, h = x1 - x0, y1 - y0
    with Sized(w, h):
        c = p28.Card(5490)
        cw = w / 2
        for i, a in enumerate(ANSWERS):
            col, row = i // 3, i % 3
            c.post.append(ink_text([a], 26, 26 + col * cw, 2 + row * 35, 5491 + i))
        rgb = c.render()
    return np.ascontiguousarray(rgb[::-1, ::-1])          # turned through 180 degrees: upside down at the foot


def edge_alpha(w, h, seed):
    rnd = random.Random(seed)
    q = [(rnd.uniform(0, 3), rnd.uniform(0, 3)), (w - rnd.uniform(0, 3), rnd.uniform(0, 3)),
         (w - rnd.uniform(0, 3), h - rnd.uniform(0, 3)), (rnd.uniform(0, 3), h - rnd.uniform(0, 3))]
    a = np.zeros((h, w), np.uint8)
    cv2.fillPoly(a, [np.int32(facet(dense_poly(q, 3.0), seed, 6, 12, 0.5) * 4)], 255, cv2.LINE_AA, shift=2)
    return a


def lay(page, rgb, box, seed, off=9):
    x0, y0, x1, y1 = box
    h, w = rgb.shape[:2]
    a = edge_alpha(w, h, seed)
    A = np.zeros((H, W), np.uint8)
    A[y0:y0 + h, x0:x0 + w] = a
    G = np.zeros((H, W, 3), np.float32)
    G[y0:y0 + h, x0:x0 + w] = rgb
    penlib.shadow_onto(page, A, off=off, blur=8, opacity=0.5)
    af = A.astype(np.float32)[..., None] / 255
    page[:] = page * (1 - af) + G * af


CACHE = {}


def card_page_rgb(k):
    if ("card", k) not in CACHE:
        rgb = CARDS[k]().render()
        CACHE[("card", k)] = cv2.resize(rgb, (CELL_W, CARD_H), interpolation=cv2.INTER_AREA)
    return CACHE[("card", k)]


INFO = {}


def build(hands=6, answers=True, moving=None):
    """hands: strips 0..hands-1 carry their pointing hand and question; moving=(k, t) hand k still sliding in"""
    if "felt" not in CACHE:
        CACHE["felt"] = p28.felt()
    page = CACHE["felt"].copy()
    for k, (cb, sb) in enumerate(cells()):
        lay(page, card_page_rgb(k), cb, 5450 + k)
        if moving is not None and moving[0] == k:
            rgb, _ = strip_rgb(k, True, moving[1])
        else:
            key = ("strip", k, k < hands)
            if key not in CACHE:
                CACHE[key], inf = strip_rgb(k, k < hands)
                if inf:
                    INFO[k] = inf
            rgb = CACHE[key]
        lay(page, rgb, sb, 5460 + k, off=6)
    if answers:
        if "ans" not in CACHE:
            CACHE["ans"] = answer_rgb()
        lay(page, CACHE["ans"], ANS, 5499, off=6)
    return page


if __name__ == "__main__":
    page = build()
    card2_ref_area()
    ratio = GLASS_STATS["card4_far_on_glass"] / GLASS_STATS["card2_far_on_glass"]
    GLASS_STATS["card4_over_card2_shadow_on_glass"] = round(ratio, 3)
    assert ratio < 0.6 and GLASS_STATS["card6_pencil_tip_frac_of_height"] < 1 / 3, GLASS_STATS
    print(GLASS_STATS)
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    frames = []
    seq = [dict(hands=0, answers=False)] + [dict(hands=k + 1, answers=False) for k in range(6)] + [dict(hands=6, answers=True)]
    for st in seq:
        p = img if st == seq[-1] else np.clip(np.round(build(**st)), 0, 255).astype(np.uint8)
        if st != seq[-1]:
            pen99.folio(p, N, TITLE)
        frames.append(p)
    save_beats(N, frames)
    src = ["99-ways-subjective:lightbox-paper-hands", "99-ways-template:anrc-gold-key-1922",
           "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    credit_pages(src, N)
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p54_questions_for_you.py (cards and felt: p28_dealt_cards.py, which imports 99-ways-subjective/test-shot-build/lightbox.py and e4.py)",
        "sources": src,
        "made": [
            "six lit paper cards laid square on the lightbox felt board (page 28's first-person cards, rebuilt: the 99-ways-subjective lamp-lit fibrous sheet, set pieces cut sharp, the agent's own scissor-cut paper hands soft behind the sheet): memo in his hand; the stranger beyond the TICKET OFFICE glass; the clock at 4:10 with his pencil hand; his hand swings the cupboard leaf open on the left jamb, the ANRC 1922 key cutout on its hook tagged SERVICE",
            "two cards re-staged for this page (repair): card 4 (E3) her shadow turned in profile toward the right and half past the right post of the pane, seen only through the glass and fading, the left pane empty, 'Much obliged!' tailed to her; card 6 (E5) his pencil hand raised so the pencil point reaches the upper third of the card (pencil to his chin), the key still on its hook, the SERVICE door shut",
            "under each card a strip of the same lit paper with a numbered question for the reader in the shared pen hand, and behind it a paper pointing hand: the 99-ways-subjective RightHand rig (scissor-cut sleeve, cuff, forearm, palm, curled fingers, two-segment index and thumb) posed with the index straight and the thumb tucked, reaching in from the left to point at the question",
            "the six answers printed on a long lit strip, numbered, turned through 180 degrees along the foot of the board",
            "the four canon lines on the cards' cut-paper pen-hand balloons; folio '54 / Questions for the reader' (pen99.folio)"],
        "questions": [" ".join(q) for q in QUESTIONS],
        "answers": ANSWERS,
        "answered_by": {f"Q{k + 1}": f"card {k + 1} ({EVENTS[k]})" for k in range(6)},
        "events": {"E0": "card 1: the memo '4:15 - open SERVICE door. Key in cupboard.' in his hand; Q1",
                   "E1": "card 2: the stranger beyond the glass, question balloon; Q2",
                   "E2": "card 3: the clock at 4:10, his answer balloon tailed to the viewer; Q3",
                   "E3": "card 4: thanks balloon tailed to her; she has turned in profile and is half past the right edge of the pane, going; the left pane empty; Q4",
                   "E4": "card 5: the cupboard opened on its left jamb, the key on its hook tagged SERVICE; Q5",
                   "E5": "card 6: the forgetting balloon; the pencil hand raised to his chin (pencil point in the card's upper third); key on its hook, SERVICE door shut; Q6"},
        "lines": LN,
        "substitutions": "none",
        "beat": "the paper hands come in one by one, each pointing at its question as it is printed; last, the answers strip is laid upside down at the foot",
        "beat_frames": ["b01: six cards on the felt, six blank lit strips"] + [f"b{k + 2:02d}: hand {k + 1} points at question {k + 1}" for k in range(6)] + ["b08: the upside-down answers laid at the foot (= the page)"],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "panels": 6, "questions": 6, "hands": 6, "answers_upside_down": True,
                       "check": "A reader answers each question from the panels alone (each answer is on its own card: the memo text, the balloon, the clock face, the turned figure, the key on its hook, the closed door), then turns the page to check the answers (maker's judgement; blind reading pending)",
                       "repair_checks": GLASS_STATS,
                       "repair_check_rule": "card 4: her shadow on the window glass < 60% of its area in card 2 (she is leaving); card 6: the pencil point above one third of the card height",
                       "hand_rig_info": {f"hand{k + 1}": {kk: vv for kk, vv in (INFO.get(k) or {}).items() if kk in ("idx_residual", "th_residual", "limits_ok")} for k in range(6)}},
        "weaknesses": [
            "four of the six cards are page 28's cards re-laid (same compositions); cards 4 and 6 are re-staged for this page; the new work is the strips, hands, answers and those two cards",
            "card 4's departure is told by position (half past the right post, fading, profile toward the right) on a soft shadow; no blind reader was run by the maker",
            "the pointing hands are small soft silhouettes behind the strips (the hand rig's thumb sits up like a cocked thumb rather than tucked flat)",
            "the upside-down answers are small print (cap 26 px), legible at full size, tiny at phone width, as answer keys usually are",
            "first-person cards: the agent is never seen, so Q1 (what is he to do) leans on the memo text in his hand"],
    }
    write_record(rec)
    print(json.dumps(rec["self_check"], indent=1, default=str))
