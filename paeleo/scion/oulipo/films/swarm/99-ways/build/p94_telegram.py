"""Page 94 Telegram (voice and language; medium: cut-paper).

The page is a station telegraph blank (our own invented form: no real company's name or mark) on which the incident
is wired: six cut-paper pictures pasted on the blank, and under each the captions as lengths of telegraph tape,
cut and pasted one sentence to a strip, in telegraphese: capitals, no articles, every sentence ending STOP.
The four canon lines stay verbatim, spoken in cut-paper balloons inside the pictures (balloons are not captions).
HANDMADE cut paper (kit/cutpaper99.py); page 02's cut-paper agent and clock (kit/build_page02.py); page 64's cut-paper
stranger (build/p64_window_in_window.woman); page 86's cut-paper cupboard, brass key, memo and SERVICE door
helpers (build/p86_picture_book.py), recoloured; all on the LoC 1934 sheet.
Run: python3 -I p94_telegram.py [beats]
"""
import re
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
from cutpaper99 import Cut, rect, ellipse, fibre  # noqa: E402
import build_page02 as p02  # noqa: E402
import p64_window_in_window as p64  # noqa: E402
import p86_picture_book as p86  # noqa: E402
from b1m2 import save_page, save_beats, wrap, letter, blit_mask, comp, INK, write_record, credit_pages  # noqa: E402

N, PID, TITLE = 94, "telegram", "Telegram"
W, H = pen99.PAGE_W, pen99.PAGE_H
PW, PH = 900, 470
p86.PW, p86.PH = PW, PH                      # p86's helpers read these for their floor-length pieces
COLS = (170, 1130)
ROWS = (520, 1255, 1990)
BLANK = "#efe2b4"                             # the telegraph blank: buff paper
TAPE = "#f7f1dc"
FORMINK = "#5a3424"                           # the blank's printed heads (cut from brown paper / brown ink)
FLOORC = "#7d6448"
WALLS = ["#d8cfb2", "#cdd3bf", "#d9c9a6", "#cdd3bf", "#d8cfb2", "#d9c9a6"]
TCAP = 34

# telegraphese: capitals, no articles, every sentence ends STOP
CAPS = [
    ["MEMO SAYS OPEN SERVICE DOOR 4:15 STOP", "KEY IN CUPBOARD STOP", "AGENT RISES TO FETCH IT STOP"],
    ["STRANGER AT TICKET WINDOW ASKS TIME STOP"],
    ["AGENT CONSULTS WALL CLOCK STOP", "CLOCK READS 4:10 STOP"],
    ["LADY THANKS HIM STOP", "DEPARTS STOP"],
    ["AGENT REACHES CUPBOARD STOP", "OPENS IT STOP", "BRASS KEY ON HOOK TAGGED SERVICE STOP"],
    ["AGENT FORGETS ERRAND STOP", "KEY STAYS ON HOOK STOP", "SERVICE DOOR STAYS CLOSED STOP"],
]
EVENTS = ["E0", "E1", "E2", "E3", "E4", "E5"]
Q = ["Pardon me —", "have you the", "right time?"]
A_ = ["Ten past four,", "by the clock."]
T_ = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]


def check_caps():
    bad = []
    for strips in CAPS:
        for s in strips:
            if not s.endswith(" STOP"):
                bad.append(("no STOP", s))
            for w in re.findall(r"[A-Za-z']+", s):
                if w.lower() in ("a", "an", "the"):
                    bad.append(("article", s))
    return bad


def ground(c, i, floor_y=380):
    c.piece(rect(-20, floor_y, PW + 20, PH + 20), FLOORC, shadow=False)


def pic(i):
    c = Cut(PH, PW, 9410 + i, ground=WALLS[i], fibre_off=(91 * i, 47 * i))
    ground(c, i)
    if i == 0:      # E0 the memo; he rises
        cupboard_closed(c, 700, 860, 70, 380)
        p02.agent(c, 470, 600, 66, pose="walk", look=(1, 0.2))
        p86.desk(c, 30, 380, 340)
        p86.memo(c, 200, 300, 1.15)
    elif i == 1:    # E1 the question
        def lady(cc):
            p64.woman(cc, 240, 630, 48)
        p86.window(c, 70, 430, top=120, sill=350, lady=lady)
        c.cut_letters(["TICKET OFFICE"], 32, (250, 70), "#f3ead0", 9421)
        p02.agent(c, 720, 600, 64, pose="stand", look=(-1, 0))
        c.balloon(Q, 34, (505, 150), (300, 255), 9431)
    elif i == 2:    # E2 the clock
        p02.clock(c, PW, PH, 200, 120, 78, 4, 10)
        p02.agent(c, 730, 600, 66, pose="stand", look=(-0.8, -1))
        c.balloon(A_, 36, (500, 95), (690, 165), 9432)
    elif i == 3:    # E3 she thanks him and goes
        def lady(cc):
            p64.woman(cc, 150, 630, 48, away=True)
        p86.window(c, 70, 430, top=120, sill=350, lady=lady)
        c.cut_letters(["TICKET OFFICE"], 32, (250, 70), "#f3ead0", 9422)
        p02.agent(c, 720, 600, 64, pose="stand", look=(-1, 0))
        c.balloon(T_, 38, (420, 190), (200, 265), 9433)
    elif i == 4:    # E4 the open cupboard, the key on its hook
        p86.cupboard(c, 260, 540, 50, 400, open_=True)
        p86.service_door(c, 600, 760, y0=60)
        p02.agent(c, 830, 600, 62, pose="stand", look=(-1, -0.3))
    else:           # E5 the forgetting
        p86.cupboard(c, 200, 470, 60, 400, open_=True)
        p86.service_door(c, 730, 880, y0=60)
        p02.agent(c, 590, 610, 64, pose="chin", look=(-0.5, -0.6))
        c.balloon(F, 32, (330, 70 + 20), (565, 175), 9434)
    return c.img


def cupboard_closed(c, x0, x1, y0, y1):
    p86.cupboard(c, x0, x1, y0, y1, open_=False)


def tape_strip(pg, text, x0, y0, seed, tilt):
    """One length of telegraph tape: a cut strip of pale paper with the sentence inked on it in the pen hand."""
    m = letter([text], TCAP, seed, weight=0.15)
    mh, mw = m.shape
    L = mw - int(TCAP * 0.6)
    h = int(TCAP * 1.9)
    c = Cut(h + 40, L + 60, seed, ground="#ffffff")
    rnd = np.random.default_rng(seed)
    cutl, cutr = rnd.uniform(-5, 5), rnd.uniform(-5, 5)        # each end cut by hand, slightly askew
    sm = c.mask(np.float32([(20 + cutl, 20), (L + 40, 20), (L + 40 + cutr, 20 + h), (20 - cutl, 20 + h)]), jitter=0.6)
    a = np.deg2rad(tilt)
    M = cv2.getRotationMatrix2D(((L + 60) / 2, (h + 40) / 2), -tilt, 1.0)
    sm = cv2.warpAffine(sm, M, (L + 60, h + 40))
    lm = np.zeros_like(sm)
    blit_mask(lm, m, int(30 - TCAP * 0.25), int(20 + h / 2 - mh / 2 + TCAP * 0.08))
    lm = cv2.warpAffine(lm, M, (L + 60, h + 40))
    full = np.zeros((H, W), np.uint8)
    fl = np.zeros((H, W), np.uint8)
    full[y0 - 20:y0 + h + 20, x0 - 20:x0 + L + 40] = sm
    fl[y0 - 20:y0 + h + 20, x0 - 20:x0 + L + 40] = lm
    penlib.shadow_onto(pg, full, off=4, blur=3, opacity=0.35)
    tex = fibre()[:H, :W]
    col = np.array([247, 241, 220], np.float32)
    aa = (full.astype(np.float32) / 255)[..., None]
    pg[:] = pg * (1 - aa) + (col + tex[..., None] * 0.9) * aa
    penlib.ink_onto(pg, fl)
    return L + 20, h


def blank(pg):
    """The telegraph blank itself: one big cut sheet of buff paper with its printed heads cut in brown paper."""
    c = Cut(H, W, 9400, ground=pg)
    c.img = pg
    c.piece(rect(120, 120, 2080, 2725), BLANK, opacity=0.40)
    c.piece(rect(150, 150, 2050, 168), FORMINK, shadow=False)
    c.cut_letters(["TELEGRAM"], 120, (1100, 260), FORMINK, 9401)
    c.ink_letters(["STATION WIRE  -  DAY MESSAGE  -  FORM 94"], 30, (1100, 372), 9402, colour=FORMINK)
    c.piece(rect(150, 408, 2050, 416), FORMINK, shadow=False)
    c.ink_letters(["FROM: AGENT, RANDOLPH VT."], 30, (470, 455), 9403, colour=FORMINK)
    c.ink_letters(["TO: DIVISION OFFICE"], 30, (1110, 455), 9404, colour=FORMINK)
    c.ink_letters(["SEPT 1937  4:16 PM"], 30, (1760, 455), 9405, colour=FORMINK)
    c.piece(rect(150, 486, 2050, 491), FORMINK, shadow=False)
    return c.img


def build(n=6, taped=None):
    taped = n if taped is None else taped
    pg = pen99.sheet99()
    blank(pg)
    rec = []
    for i in range(n):
        x0, y0 = COLS[i % 2], ROWS[i // 2]
        img = pic(i)
        cm = p86.card_mask(x0, y0, 9450 + i)
        full = np.zeros((H, W), np.uint8)
        full[y0 - 20:y0 + PH + 20, x0 - 20:x0 + PW + 20] = cm
        penlib.shadow_onto(pg, full, off=8, blur=8, opacity=0.40)
        a = (cm[20:-20, 20:-20].astype(np.float32) / 255)[..., None]
        sub = pg[y0:y0 + PH, x0:x0 + PW]
        sub[:] = sub * (1 - a) + img * a
        if i < taped:
            y = y0 + PH + 22
            for j, s in enumerate(CAPS[i]):
                tilt = [-0.6, 0.5, -0.3, 0.7][(i + j) % 4]
                L, h = tape_strip(pg, s, x0 + 4 + 12 * (j % 2), y, 9460 + 10 * i + j, tilt)
                assert L <= PW + 30, (s, L)
                y += h + 6
        rec.append(dict(picture=i + 1, event=EVENTS[i], captions=CAPS[i]))
    return pg, rec


def _fol(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


def beats():
    seq = [(0, 0), (2, 1), (2, 2), (4, 3), (4, 4), (6, 5), (6, 6)]
    return [cv2.resize(_fol(build(n, t)[0]), (960, 1242), interpolation=cv2.INTER_AREA) for n, t in seq]


if __name__ == "__main__":
    assert not check_caps(), check_caps()
    page, rec = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        print("beats", save_beats(N, beats()))
