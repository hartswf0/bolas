"""Page 76 You (voice and language; medium: paper-hands).

Captions address the reader as the agent, second person, present tense ('You are the station agent at Randolph...').
Eight lit paper cards on the 99-ways-subjective lightbox felt board, two by four, each a view through your own eyes:
your scissor-cut paper hands (the 99-ways-subjective RightHand rig, the left hand cut mirror-wise), your cuff, your
pencil; under each card a pasted caption slip in the shared pen hand, every one containing 'you'. The four canon lines
are kept in the cut-paper balloons; your own two come from below the card, from your mouth.
Reused HANDMADE code (imported): p28_dealt_cards (lit card, set pieces, key on hook), 99-ways-subjective lightbox.py
and e4.py through it; p65_through_his_eyes (mirror-cut left hand); b1m2 (stranger bust, clock, slips).
Run: python3 -I p76_you.py
"""
import json
import math
import re
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p28_dealt_cards as p28  # noqa: E402
import p65_through_his_eyes as p65  # noqa: E402
from p28_dealt_cards import lb  # noqa: E402
from p54_questions_for_you import lay  # noqa: E402
from b1m2 import (pen99, penlib, stranger, clock, save_page, save_beats, write_record, credit_pages, slip,  # noqa: E402
                  letter_left, wrap, blit_mask, comp, INK, ROOT, W, H)

N, PID, TITLE = 76, "you", "You"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
CW, CH = 1100, 568

CAPTIONS = [
    "You are the station agent at Randolph. You read your memo, and you rise.",
    "You set off across your office for the cupboard, as the memo tells you.",
    "On your way a woman at your ticket window stops you.",
    "You look up at your clock, and you tell her.",
    "She thanks you and goes. You go on to the cupboard.",
    "You open it. The brass key hangs on its hook, tagged SERVICE, right in front of you.",
    "You stand before it, your pencil at your chin. You cannot think why you came.",
    "The key stays on its hook. The SERVICE door stays shut. And you stay where you are.",
]


class You(p28.Card):
    left_hand = p65.Eye.left_hand

    def __init__(self, seed):
        super().__init__(seed)
        self.w, self.h = p28.CW, p28.CH


def v1():   # E0 your memo in your left hand, your pencil at the 4:15 line
    c = You(7611)
    c.rect(-10, 470, c.w + 10, c.h + 10, s=1)                        # desk edge
    c.rect(890, 370, 960, 470, s=2)                                  # inkwell
    c.poly([(890, 370), (906, 350), (944, 350), (960, 370)], s=3)
    c.slip(250, 110, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 44, 7612, tilt=-3)
    c.left_hand((262, 318), -70)
    c.hand((770, 360), -150, pencil=130)
    return c


def v2():   # E0 your hands push up from the desk: the cupboard and the SERVICE door ahead
    c = You(7621)
    c.rect(-10, 470, c.w + 10, 482, s=1)                             # the floor line far ahead
    p28.cupboard_set(c, 500, 170, 160, 300, open_=False, seed=10)
    p28.service_door_set(c, 740, 130, 150, 340, 30)
    c.rect(-10, 90, 70, 450, s=40)                                   # the ticket window's jamb at the edge
    c.rect(-10, 530, c.w + 10, c.h + 10, s=2)                        # your desk edge, close
    c.left_hand((250, 462), -80)
    c.hand((860, 462), -100)
    return c


def v3():   # E1 the woman at your window (you have turned toward it: it stands to your right)
    c = You(7631)
    sill = p28.window_set(c, 470, 50, 560, 500, 50)
    c.shapes(stranger(700, sill + 34, face=-1, scale=1.25, glove=True), layer="far", holes=False)
    c.balloon(Q, 46, (230, 175), (640, 250), 7632)
    c.hand((300, 560), -80, pencil=110)
    return c


def v4():   # E2 your clock at 4:10; your answer comes from your own mouth, below the card
    c = You(7641)
    c.shapes(clock(300, 190, 118, hh=4, mm=10, swing=-4))
    c.hand((420, 470), -70, pencil=130)
    c.balloon(A, 46, (800, 170), (640, 600), 7642)
    return c


def v5():   # E3 her thanks; she turns from the glass and goes off to the right
    c = You(7651)
    sill = p28.window_set(c, 470, 50, 560, 500, 60)
    c.shapes(stranger(930, sill + 34, face=1, scale=1.05, tilt=6), layer="far", holes=False)
    c.balloon(T, 48, (220, 190), (840, 255), 7652)
    c.hand((180, 560), -84, pencil=100)
    return c


def v6():   # E4 your hand swings the leaf: the key on its hook
    c = You(7661)
    c.rect(-10, 530, c.w + 10, c.h + 10, s=1)
    box, leaf = p28.cupboard_set(c, 520, 70, 330, 460, open_=True, seed=70)
    p28.key_on_hook(c, 690, 230, 0.27, 7662)
    c.hand((leaf[1][0] - 6, 190), -58)
    return c


def v7():   # E5 pencil up to your chin (from below the card), the line
    c = You(7671)
    c.rect(-10, 530, c.w + 10, c.h + 10, s=1)
    box, leaf = p28.cupboard_set(c, 220, 90, 300, 440, open_=True, seed=80)
    p28.key_on_hook(c, 370, 250, 0.27, 7672)
    p28.service_door_set(c, 840, 50, 200, 480, 90)
    c.hand((560, 500), -100, pencil=140)
    c.balloon(F, 44, (650, 105), (640, 620), 7673)
    return c


def v8():   # outcome: key still on its hook, SERVICE door shut, your empty hands at your sides
    c = You(7681)
    c.rect(-10, 530, c.w + 10, c.h + 10, s=1)
    box, leaf = p28.cupboard_set(c, 300, 90, 300, 440, open_=True, seed=81)
    p28.key_on_hook(c, 450, 250, 0.27, 7682)
    p28.service_door_set(c, 820, 50, 200, 480, 91)
    c.left_hand((170, 455), -92)
    c.hand((940, 455), -88, pencil=90)
    return c


VIEWS = [v1, v2, v3, v4, v5, v6, v7, v8]
CARD_W = 930
CARD_H = int(round(CARD_W * CH / CW))            # 480
COLX = [150, 1120]
PITCH = 655
ROWY = [110 + r * PITCH for r in range(4)]
CAP = 36
CACHE = {}


def card_rgb(k):
    if k not in CACHE:
        with p65.Sized(CW, CH):
            rgb = VIEWS[k]().render()
        CACHE[k] = cv2.resize(rgb, (CARD_W, CARD_H), interpolation=cv2.INTER_AREA)
    return CACHE[k]


def caption(page, k, x0, y0, text=None, seed=None):
    text = CAPTIONS[k] if text is None else text
    lines = wrap(text, CAP, CARD_W - 70) if text else [" "]
    slip(page, x0 + 6, y0, lines, CAP, 7690 + k if seed is None else seed, paper=lb.VELLUM, pad=(22, 12),
         min_w=CARD_W - 12, tilt=0.4 if k % 2 else -0.4, shadow=0.34)


def build(n=8):
    if "felt" not in CACHE:
        CACHE["felt"] = p28.felt()
    page = CACHE["felt"].copy()
    for k in range(n):
        x0, y0 = COLX[k % 2], ROWY[k // 2]
        lay(page, card_rgb(k), (x0, y0, x0 + CARD_W, y0 + CARD_H), 7600 + k)
        caption(page, k, x0, y0 + CARD_H + 14)
    return page


def check():
    for t in CAPTIONS:
        assert re.search(r"\byou\b", t, re.I), t
        for w_ in re.findall(r"[A-Za-z']+", t):
            pen99.clean(w_)
    # present tense: no past-tense verbs from the incident's vocabulary
    past = r"\b(was|were|had|said|went|opened|looked|stood|came|stayed|told|read his)\b"
    assert not any(re.search(past, t) for t in CAPTIONS if "why you came" not in t)
    return True


# ------------------------------------------------------------------ beats: two cards laid, each caption written on
BW, BH = 960, 1242


def beat_frames():
    saved = (lb.PAGE_W, lb.PAGE_H, lb.PANELS)
    lb.PAGE_W, lb.PAGE_H, lb.PANELS = BW, BH, {}
    try:
        felt = lb.make_page(7699)
    finally:
        lb.PAGE_W, lb.PAGE_H, lb.PANELS = saved
    cw = 900
    ch = int(round(cw * CH / CW))
    cards = [cv2.resize(card_rgb(k), (cw, ch), interpolation=cv2.INTER_AREA) for k in (5, 6)]
    ys = [18, 18 + ch + 142]

    def words(k, n):
        ws = CAPTIONS[k].split()
        return " ".join(ws[:n])

    states = [(1, 0, 0), (1, 6, 0), (1, 99, 0), (2, 99, 0), (2, 99, 5), (2, 99, 9), (2, 99, 99)]
    out = []
    for ncard, w6, w7 in states:
        fr = felt.copy()
        import p54_questions_for_you as p54
        for i in range(ncard):
            G = np.zeros((BH, BW, 3), np.float32)
            a = p54.edge_alpha(cw, ch, 7700 + i)
            A = np.zeros((BH, BW), np.uint8)
            A[ys[i]:ys[i] + ch, 30:30 + cw] = a
            G[ys[i]:ys[i] + ch, 30:30 + cw] = cards[i]
            penlib.shadow_onto(fr, A, off=8, blur=8, opacity=0.5)
            af = A.astype(np.float32)[..., None] / 255
            fr[:] = fr * (1 - af) + G * af
            n = w6 if i == 0 else w7
            k = 5 + i
            full = wrap(CAPTIONS[k], CAP, cw - 70)
            part = words(k, n) if n < 99 else CAPTIONS[k]
            lines = wrap(part, CAP, cw - 70) if part else []
            # the slip at full size first (paper), then only the words written so far
            slip(fr, 36, ys[i] + ch + 14, [" "] * len(full), CAP, 7710 + i, paper=lb.VELLUM, pad=(22, 12),
                 min_w=cw - 12, shadow=0.34)
            if lines:
                m = letter_left(lines, CAP, 7690 + k)
                lm = np.zeros((BH, BW), np.uint8)
                blit_mask(lm, m, int(36 + 22 - CAP * 0.5), int(ys[i] + ch + 14 + 12 - CAP * 0.15))
                comp(fr, lm, INK)
        out.append(fr)
    return out


if __name__ == "__main__":
    check()
    page = build()
    img, size_b = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size_b)
    nb = save_beats(N, beat_frames())
    src = ["99-ways-template:loc-blank-sheet-1934", "99-ways-subjective:lightbox-paper-hands",
           "99-ways-template:anrc-gold-key-1922", "99-ways:handmade"]
    credit_pages(src, N)
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p76_you.py (lit cards and set pieces: p28_dealt_cards.py -> 99-ways-subjective lightbox.py, e4.py; left hand: p65_through_his_eyes.Eye.left_hand)",
        "sources": src,
        "made": [
            "eight lit paper cards (p28_dealt_cards.Card: the 99-ways-subjective lamp-lit fibrous sheet, set pieces cut sharp against it) laid two by four on the lightbox felt board, each a view through your eyes",
            "your hands: the 99-ways-subjective scissor-cut RightHand rig behind the sheet (soft body and penumbra) in pinch, push and reach poses, the left hand the same rig cut mirror-wise; your pencil a cut bar through the pinch",
            "eight caption slips of vellum pasted under the cards, lettered in the shared pen hand: second person, present tense, every one containing 'you'; the first says who you are ('You are the station agent at Randolph')",
            "the four canon lines in the shared cut-paper balloons; your own two tailed off the card's bottom edge toward your mouth; the stranger's from beyond the TICKET OFFICE glass, her figure (b1m2 stranger bust) soft grey behind it",
            "the ANRC 1922 key cutout as the key on its hook (p28.key_on_hook), SERVICE tag slip; folio '76 / You' (pen99.folio)"],
        "captions": CAPTIONS,
        "events": {"E0": "1-2: your memo; your hands push up from the desk", "E1": "3: the question through your ticket window",
                   "E2": "4: your clock at 4:10, your answer", "E3": "5: her thanks; she goes",
                   "E4": "6: your hand swings the cupboard open, the key on its hook",
                   "E5": "7: your pencil at your chin, 'Well, here I am... and what for?'; 8: key on its hook, SERVICE door shut, your empty hands"},
        "lines": LN,
        "beat": "the cupboard card is laid and its caption is written on word by word ('You open it...'), then the forgetting card is laid beneath and its caption written: 'You stand before it, your pencil at your chin. You cannot think why you came.'",
        "beat_frames": ["b01: card 6 laid, blank slip", "b02: 'You open it. The brass key hangs'", "b03: caption 6 complete",
                        "b04: card 7 laid under it, blank slip", "b05: 'You stand before it, your pencil'",
                        "b06: '... at your chin. You cannot'", "b07: caption 7 complete"],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size_b, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size_b <= 1200000,
                       "captions": len(CAPTIONS), "every_caption_contains_you": check(),
                       "who_is_you": "caption 1: 'You are the station agent at Randolph'",
                       "tense": "present throughout ('why you came' is the only past form, inside a present sentence)",
                       "agent_face_drawn": False, "beat_frames": nb,
                       "check": C["check"], "pending": "independent blind reading not run by the maker"},
    }
    write_record(rec)
    print(json.dumps(rec["self_check"], indent=1))
