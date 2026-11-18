"""Page 86 Picture book (genre; medium: cut-paper).

A children's picture book: eight large, flat cut-paper pictures, each on its own coloured card, and under each picture
exactly one short sentence in the shared pen hand (no balloons: the four canon lines sit inside the sentences, as
picture books quote speech). HANDMADE cut paper (kit/cutpaper99.py), page 02's cut-paper agent and clock
(kit/build_page02.py), page 64's cut-paper stranger (build/p64_window_in_window.woman), on the LoC 1934 sheet.
Run: python3 -I p86_picture_book.py [beats]
"""
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
from cutpaper99 import Cut, rect, ellipse  # noqa: E402
import build_page02 as p02  # noqa: E402
import p64_window_in_window as p64  # noqa: E402
from b1m2 import save_page, save_beats, wrap, letter, blit_mask, comp, INK, write_record, credit_pages  # noqa: E402

N, PID, TITLE = 86, "picture-book", "Picture book"
W, H = pen99.PAGE_W, pen99.PAGE_H
PW, PH = 960, 450            # picture card
TCAP = 46                    # sentence cap height
COLS = (110, 1130)
ROWS = (110, 765, 1420, 2075)
BRASS, BRASS2, TAG = "#d8a93a", "#a37c2a", "#f4ead0"
FLOOR = "#b07a4a"
DESK, DESK2 = "#7a4a2a", "#5e3820"
CUP, CUP2, CUPIN = "#8a5a32", "#6c4426", "#3a281a"
SDOOR = "#3f6b8a"            # picture-book blue for the SERVICE door
WALLS = ["#f6d77a", "#f4b98a", "#bfe0c4", "#f6d77a", "#c9dcef", "#f4b98a", "#e9c6dc", "#c9dcef"]

SENT_L = [
    ["His memo says: open the", "SERVICE door at 4:15."],
    ["Off he goes to fetch the key", "from the cupboard."],
    ["A lady at the window asks,", '"Pardon me — have you the right time?"'],
    ["He looks at the clock and says,", '"Ten past four, by the clock."'],
    ['"Much obliged!" says the lady,', "and away she goes."],
    ["He opens the cupboard, and", "there hangs the brass key."],
    ["Pencil to his chin, he says,", '"Well, here I am... and what for?"'],
    ["The key stays on its hook, and", "the SERVICE door stays shut."],
]
SENT = [" ".join(l) for l in SENT_L]


def ground(c, wall_i, floor_y=360):
    c.piece(rect(-20, floor_y, PW + 20, PH + 20), FLOOR, shadow=False)


def window(c, x0, x1, top=110, sill=330, lady=None):
    c.piece(rect(x0 - 22, top - 22, x1 + 22, sill + 16), "#6b4a2e")
    c.piece(rect(x0, top, x1, sill), "#e8f3f6", shadow=False)
    if lady is not None:
        lady(c)
    c.piece(rect(x0 - 30, sill, x1 + 30, PH + 20), "#7a5232")          # the counter front: she is on the far side
    c.piece(rect(x0 - 50, sill - 4, x1 + 50, sill + 30), "#5a3a22")


def memo(c, x, y, s=1.0, tilt=-4):
    a = np.radians(tilt)
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    pts = np.array([(-150, -70), (150, -70), (150, 70), (-150, 70)], np.float32) * s
    c.piece(pts @ R.T + (x, y), "#fbf7ea")
    c.ink_letters(["4:15 - SERVICE", "key - cupboard"], 30 * s, (x, y), 8601)


def desk(c, x0, x1, top):
    c.piece(rect(x0, top, x1, top + 30), DESK)
    c.piece(rect(x0 + 20, top + 30, x1 - 20, PH + 20), DESK2)


def cupboard(c, x0, x1, y0, y1, open_=False, key=True):
    c.piece(rect(x0 - 16, y0 - 26, x1 + 16, y0 + 2), CUP2)
    c.piece(rect(x0, y0, x1, y1), CUP)
    if not open_:
        c.piece(rect(x0 + 22, y0 + 22, x1 - 22, y1 - 22), CUP2, off=(3, 4))
        c.piece(ellipse(x1 - 44, (y0 + y1) / 2, 11, 11), BRASS)
        return
    c.piece(rect(x0 + 18, y0 + 18, x1 - 18, y1 - 18), CUPIN, shadow=False)
    # the door swung open on its left jamb: a narrow foreshortened leaf to the left
    dw = (x1 - x0) * 0.42
    c.piece(np.float32([(x0 - dw, y0 + 14), (x0, y0), (x0, y1), (x0 - dw, y1 - 14)]), CUP2)
    c.piece(ellipse(x0 - dw + 18, (y0 + y1) / 2, 8, 10), BRASS)
    if key:
        kx, ky = (x0 + x1) / 2, y0 + 60
        brass_key(c, kx, ky, (x1 - x0) / 220)


def brass_key(c, kx, ky, s):
    c.piece(rect(kx - 7 * s, ky - 22 * s, kx + 7 * s, ky + 6 * s), "#9a958a")                  # hook
    c.piece(ellipse(kx, ky + 46 * s, 34 * s, 34 * s), BRASS, holes=[ellipse(kx, ky + 46 * s, 15 * s, 15 * s)])
    c.strip((kx, ky + 76 * s), (kx, ky + 220 * s), 18 * s, BRASS)
    c.piece(rect(kx, ky + 180 * s, kx + 42 * s, ky + 200 * s), BRASS2)
    c.piece(rect(kx, ky + 204 * s, kx + 32 * s, ky + 220 * s), BRASS2)
    tg = np.float32([(kx + 30 * s, ky + 98 * s), (kx + 150 * s, ky + 110 * s), (kx + 146 * s, ky + 160 * s), (kx + 26 * s, ky + 148 * s)])
    c.strip((kx + 10 * s, ky + 80 * s), (kx + 32 * s, ky + 112 * s), 3, "#d8cfb8", shadow=False)
    c.piece(tg, TAG)
    c.ink_letters(["SERVICE"], 24 * s, (kx + 88 * s, ky + 130 * s), 8602)


def service_door(c, x0, x1, y0=40):
    c.piece(rect(x0, y0, x1, PH + 20), SDOOR)
    c.piece(rect(x0 + 24, y0 + 110, x1 - 24, y0 + 250), "#335a75", off=(3, 4))
    c.piece(ellipse(x1 - 30, y0 + 290, 10, 10), BRASS)
    c.piece(rect(x0 + 16, y0 + 24, x1 - 16, y0 + 84), "#fbf7ea")
    c.ink_letters(["SERVICE"], 30, ((x0 + x1) / 2, y0 + 54), 8603)


def sun_patch(c):     # a picture-book touch: a round paper sun through the window glass
    pass


# ------------------------------------------------------------------ the eight pictures
def pic(i):
    c = Cut(PH, PW, 8610 + i, ground=WALLS[i], fibre_off=(97 * i, 53 * i))
    ground(c, i)
    if i == 0:      # E0 the memo
        p02.agent(c, 600, 560, 64, pose="stand", look=(-0.6, 0.9))
        desk(c, 60, 920, 330)
        memo(c, 300, 300, 1.25)
        c.piece(rect(640, 308, 690, 334), "#2a2420")                                     # ink pot
        c.strip((720, 326), (840, 316), 9, p02.PENCIL)
    elif i == 1:    # E0 off he goes
        cupboard(c, 640, 900, 50, 400)
        p02.agent(c, 360, 520, 60, pose="walk", look=(1, 0))
        desk(c, -40, 170, 330)
    elif i == 2:    # E1 the question
        def lady(cc):
            p64.woman(cc, 250, 600, 46)
        window(c, 70, 440, lady=lady)
        c.cut_letters(["TICKET OFFICE"], 34, (255, 52), "#fbf2cf", 8611)
        p02.agent(c, 720, 540, 62, pose="stand", look=(-1, 0))
    elif i == 3:    # E2 the clock
        p02.clock(c, PW, PH, 300, 140, 100, 4, 10)
        p02.agent(c, 680, 560, 64, pose="stand", look=(-0.8, -1))
    elif i == 4:    # E3 away she goes
        def lady(cc):
            p64.woman(cc, 120, 600, 46, away=True)
        window(c, 70, 440, lady=lady)
        c.cut_letters(["TICKET OFFICE"], 34, (255, 52), "#fbf2cf", 8612)
        p02.agent(c, 720, 540, 62, pose="stand", look=(-1, 0))
    elif i == 5:    # E4 the open cupboard
        cupboard(c, 330, 630, 40, 400, open_=True)
        p02.agent(c, 800, 540, 62, pose="stand", look=(-1, -0.3))
    elif i == 6:    # E5 pencil to the chin
        cupboard(c, 130, 430, 40, 400, open_=True)
        p02.agent(c, 660, 560, 64, pose="chin", look=(-0.5, -0.6))
        for k, (x, y, r) in enumerate([(790, 110, 14), (830, 74, 20), (880, 38, 26)]):    # little think puffs
            c.piece(ellipse(x, y, r, r * 0.85), "#fbf7ea")
    else:           # outcome: key on its hook, door shut, nobody
        cupboard(c, 150, 450, 40, 400, open_=True)
        service_door(c, 600, 840)
    return c.img


def card_mask(x0, y0, seed):
    c = Cut(PH + 40, PW + 40, seed, ground="#ffffff")
    return c.mask(rect(20, 20, PW + 20, PH + 20), jitter=1.2)


def sentence_mask(text, cx, ytop):
    i = SENT.index(text)
    lines = SENT_L[i]
    m = letter(lines, TCAP, 8690 + 7 * i)
    return lines, m


def build(n=8, written=None):
    """n pictures laid; `written` sentences lettered (default all laid)."""
    written = n if written is None else written
    pg = pen99.sheet99()
    for i in range(n):
        x0, y0 = COLS[i % 2], ROWS[i // 2]
        img = pic(i)
        cm = card_mask(x0, y0, 8650 + i)
        full = np.zeros((H, W), np.uint8)
        full[y0 - 20:y0 + PH + 20, x0 - 20:x0 + PW + 20] = cm
        penlib.shadow_onto(pg, full, off=8, blur=8, opacity=0.40)
        a = (cm[20:-20, 20:-20].astype(np.float32) / 255)[..., None]
        sub = pg[y0:y0 + PH, x0:x0 + PW]
        sub[:] = sub * (1 - a) + img * a
        if i < written:
            lines, m = sentence_mask(SENT[i], x0 + PW / 2, y0 + PH)
            lm = np.zeros((H, W), np.uint8)
            mh, mw = m.shape
            blit_mask(lm, m, int(x0 + PW / 2 - mw / 2), int(y0 + PH + 18))
            comp(pg, lm, INK)
    return pg


def record(size):
    rec = {
        "n": N, "id": PID, "title": TITLE, "family": "genre", "medium": "cut-paper", "canon_revision": "c1",
        "rule": "A children's picture book: large flat shapes, one simple sentence per panel.",
        "declares": "keeps E0-E5, the four lines and the outcome",
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg",
        "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p86_picture_book.py (cut paper: kit/cutpaper99.py; agent and clock: kit/build_page02.py; stranger: build/p64_window_in_window.woman)",
        "sources": ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "eight HANDMADE cut-paper pictures, each on its own scissor-cut card of a bright flat paper (lemon, apricot, mint, sky, pink), with a plain floor paper: large flat shapes, one down-right paper shadow, the LoC 1934 sheet's fibre as relative tone (cutpaper99.Cut); no ink line inside the pictures except object lettering",
            "page 02's cut-paper agent (waistcoat, shirt sleeves, pencil) and clock (4:10), page 64's cut-paper stranger (cloche hat, coat, bag), cut larger here; a new cut-paper cupboard that opens on its left jamb, a brass key with its SERVICE tag on a hook, a blue SERVICE door with its card, desk, memo slip, think-puffs",
            "under each card exactly one short sentence in the shared pen hand at cap 46; the four canon lines are quoted inside four of the sentences (no balloons, as in a picture book)",
            "the memo slip in picture 1 is lettered as a note '4:15 - SERVICE / key - cupboard' (no full stops) so that the panel holds only its one sentence; the sentence under it states the memo",
            "folio '86 / Picture book' (pen99.folio)",
        ],
        "sentences": SENT,
        "events": {
            "E0": "pictures 1-2: the memo on the desk; he walks toward the cupboard",
            "E1": "picture 3: the lady at the TICKET OFFICE window; the question in the sentence",
            "E2": "picture 4: the clock at 4:10; the answer in the sentence",
            "E3": "picture 5: she walks away from the window; the thanks in the sentence",
            "E4": "picture 6: the cupboard open, the brass key on its hook tagged SERVICE",
            "E5": "picture 7: pencil to his chin, the forgetting line in the sentence; picture 8: key on its hook, SERVICE door shut",
        },
        "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
                  "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
        "substitutions": "none: the four lines verbatim, quoted inside the panel sentences with a speaker tag; the memo text is given by the sentence under picture 1 and only as a note on the slip",
        "beat": "the book read aloud: the cards are laid one after another, each picture first, then its one sentence written beneath it",
        "beat_frames": ["b01: pictures 1-2 with sentences", "b02: + picture 3 (no sentence yet)", "b03: + sentence 3 (the question)",
                        "b04: + pictures and sentences 4-5", "b05: + picture 6, the open cupboard", "b06: + sentence 6",
                        "b07: + picture 7 and the forgetting sentence", "b08: + picture 8, the outcome (the page)"],
        "self_check": {
            "size_px": [W, H], "jpeg_bytes": size, "jpeg_quality": 90, "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
            "panels": 8, "sentences_per_panel": [1] * 8,
            "check": "Each panel has exactly one short sentence: each card carries one sentence beneath it (each ending in a single . ? or !, quoted lines counted inside their sentence); no balloon or caption inside the pictures; checked by the maker on the full page",
            "evidence": "perceptually judged (from the full page) by the maker; blind reading pending",
        },
        "weaknesses": [
            "sentences 3, 4 and 7 quote a canon line that carries its own internal punctuation (dash, ellipsis), so they read as one sentence with speech inside rather than as the simplest picture-book sentence",
            "the reused page-02 agent and stranger are fairly detailed for a picture book (glasses, buttons); the scenery is flatter than the figures",
            "the memo slip carries a note in the picture (two short label lines without full stops); a strict reader might count it as text in the panel",
        ],
    }
    write_record(rec)
    credit_pages(rec["sources"], N)


def beats():
    seq = [(2, 2), (3, 2), (3, 3), (5, 5), (6, 5), (6, 6), (7, 7)]
    return [cv2.resize(_fol(build(n, w)), (960, 1242), interpolation=cv2.INTER_AREA) for n, w in seq]


def _fol(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    record(size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        fr = beats() + [cv2.resize(img, (960, 1242), interpolation=cv2.INTER_AREA)]
        print("beats", save_beats(N, fr))
