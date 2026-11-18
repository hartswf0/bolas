"""Page 70 Footnotes (reduction and expansion; medium: pen-hand).

The incident in small panels across the top third; the rest of the page is numbered footnotes on every object and
word. Page 51's eight pen-hand panels (one pen, outlines only, the base page's order E0 x3, E1, E2, E3, E4, E5) are
redrawn small in two tiers across the top of the sheet; every object and every word of the four canon lines carries
a superscript footnote number written in a red-brown ink; below a short footnote rule, twenty-seven numbered notes
in two columns, in the shared pen hand, annotate them (our own text). The four lines verbatim; the outcome unchanged.
HANDMADE throughout (page 51's drawing: build/p51_pen_alone.py, figure model build/b1m2.py) on the LoC 1934 sheet.
Run: python3 -I p70_footnotes.py [--page-only] [--grid]
"""
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
from b1m2 import pen99, penlib  # noqa: E402
import p51_pen_alone as P51  # noqa: E402

N, PID, TITLE = 70, "footnotes", "Footnotes"
W, H = 2200, 2850
SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 5.0)   # scan grain softened for the JPEG budget (a text-heavy page)
SHEET = SHEET.mean((0, 1)) + (SHEET - SHEET.mean((0, 1))) * 0.35
RED = np.array([150, 52, 34], np.float32)          # the annotator's red-brown ink
S = 0.56                                            # panel scale
CROP0, CROP1 = 0, 800                              # panel rows kept (p51 panel px)
PWID = {1: 640, 2: 640, 3: 640, 4: 640, 5: 640, 6: 640, 7: 975, 8: 975}
ROWS = [(1, 2, 3, 4), (5, 6, 7, 8)]
Y0 = (110, 110 + int((CROP1 - CROP0) * S) + 30)
PANEL_H = int((CROP1 - CROP0) * S)


def layout():
    box = {}
    for r, ks in enumerate(ROWS):
        widths = [PWID[k] * S for k in ks]
        if r == 0:     # the upper tier's frames widened to the full measure; the drawing centred in each
            fw = [(1980 - 3 * 30) / 4] * 4
        else:
            fw = widths
        gap = (1980 - sum(fw)) / (len(ks) - 1)
        x = 110.0
        for k, f, w in zip(ks, fw, widths):
            box[k] = (int(round(x)), Y0[r], int(round(x + f)), Y0[r] + PANEL_H, int(round(x + (f - w) / 2)))
            x += f + gap
    return box


BOX = layout()

BAL = {   # p51's balloons: panel -> (lines, centre (panel px), cap)
    4: (["Pardon me —", "have you the", "right time?"], (250, 118 - 44 * 0.05), 44),
    5: (["Ten past four,", "by the clock."], (400, 100 - 44 * 0.05), 44),
    6: (["Much", "obliged!"], (250, 110 - 50 * 0.05), 50),
    8: (["Well, here I am...", "and what for?"], (560, 110 - 44 * 0.05), 44),
}

# number, panel, anchor, note. anchor: ("pt", x, y) in p51 panel px, or ("w", line index, prefix) in that panel's balloon
NOTES = [
    (1, 1, ("pt", 300, 440), "The memo. A slip of railway paper on the desk, pencilled '4:15 - open SERVICE door. Key in "
                             "cupboard.' Seven words and a time, and every one of them is about to be needed."),
    (2, 1, ("pt", 560, 560), "The desk. Oak, scarred, the agent's post of command, which he is about to leave."),
    (3, 1, ("pt", 470, 250), "The agent. Randolph's station agent, September 1937, waistcoat and shirt sleeves. Not, on "
                             "the evidence below, a man to be trusted with two things at once."),
    (4, 2, ("pt", 440, 470), "The pencil. In his hand from first to last. It reaches his chin in note 25."),
    (5, 2, ("pt", 520, 250), "He gets up and sets off. Distance to the cupboard: a few strides. Time needed: under a minute. "
                             "Time taken: see note 18."),
    (6, 3, ("pt", 460, 300), "The cupboard. Its door opens on the left jamb. He walks past it here, meaning to come back to it. "
                             "He will."),
    (7, 3, ("pt", 630, 250), "The SERVICE door, marked by a card lettered SERVICE, to be opened at 4:15. It is not opened on "
                             "this page, nor on any of the other ninety-eight."),
    (8, 4, ("pt", 380, 280), "TICKET OFFICE. The glazed window between office and platform. She stays on the platform side "
                             "of it; she never enters the office."),
    (9, 4, ("pt", 240, 560), "The stranger. A woman traveller in a hat. Her name is not recorded; nor is her train."),
    (10, 4, ("w", 0, "Pardon"), "'Pardon me': the formula of interruption. It costs the speaker nothing. For what it costs "
                                   "the hearer, see note 24."),
    (11, 4, ("w", 0, "Pardon me —"), "The dash. A breath taken. In it, the errand begins to slip."),
    (12, 4, ("w", 2, "right time?"), "'The right time', as against the wrong one. Railway clocks kept the true time; she asks the "
                                     "one man in town bound to know it."),
    (13, 5, ("pt", 250, 300), "The clock. The office wall clock, reading ten past four: five minutes before the memo's hour."),
    (14, 5, ("w", 0, "Ten past four,"), "Ten past four, i.e. 4:10. Correct; compare note 13."),
    (15, 5, ("w", 1, "by the clock."), "'By the clock': he names his authority. He does not consult the memo, which would have "
                                       "named his errand."),
    (16, 6, ("w", 1, "obliged!"), "'Much obliged!' An old courtesy, and the last thing anyone says to him. The interruption is "
                                  "over."),
    (17, 6, ("pt", 140, 560), "Her going. Through the glass, a hat turning away down the platform. Some readers hold that "
                              "the errand went with her (see page 67)."),
    (18, 7, ("pt", 160, 250), "The cupboard again, reached at last, its door swung open on the left jamb (note 6)."),
    (19, 7, ("pt", 440, 300), "The key. Brass, on its hook inside the cupboard, in plain view: the object of the errand, "
                              "within arm's reach, and of no further interest to anyone."),
    (20, 7, ("pt", 470, 470), "The tag, lettered SERVICE. It says what the key is for. He does not read it."),
    (21, 7, ("pt", 345, 310), "The hook, on which the key hangs at the start of this page, at the end of it, and in every "
                              "note between."),
    (22, 8, ("w", 0, "Well,"), "'Well': the word of a man taking stock and finding the stock short."),
    (23, 8, ("w", 0, "Well, here I am"), "'Here I am': true. He is there. Where he is was never the problem."),
    (24, 8, ("w", 1, "and what for?"), "'And what for?' A question with an answer, which is in note 1. The ellipsis before it "
                                       "is three dots in which the errand should have come back."),
    (25, 8, ("pt", 690, 300), "Pencil to chin: the gesture of thought. A pencil that could write the answer down props up the "
                              "question instead."),
    (26, 8, ("pt", 330, 470), "The key, still on its hook. See note 21."),
    (27, 8, ("pt", 930, 400), "The SERVICE door, still closed. It stays so."),
]
NCAP, SUPCAP = 30, 25


def to_page(k, p):
    x0, y0, x1, y1, dx = BOX[k]
    return (dx + p[0] * S, y0 + (p[1] - CROP0) * S)


def adv(s, cap):
    return sum(penlib.GLYPHS[c][0] * cap + cap * .1 for c in pen99.clean(s)) - cap * .1


def word_anchor(k, li, prefix):
    lines, (cx, cy), cap = BAL[k]
    m = P51.letters(lines, cap, 0)
    hm, wm = m.shape
    wl = adv(lines[li], cap)
    left = cx - wl / 2
    base = cy - hm / 2 + cap * 1.15 + li * cap * 1.42
    return (left + adv(prefix, cap) + 3, base - cap * 0.78)


def anchor(k, a):
    if a[0] == "pt":
        return to_page(k, (a[1], a[2]))
    return to_page(k, word_anchor(k, a[1], a[2]))


def panels_ink(upto=8, state=None):
    state = state or {}
    ink = np.zeros((H, W), np.uint8)
    p = P51.Pen(W, H, 7090)
    for k in range(1, upto + 1):
        x0, y0, x1, y1, dx = BOX[k]
        p.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True)
    fr = cv2.resize(p.m, (W, H), interpolation=cv2.INTER_AREA)
    ink = np.maximum(ink, fr)
    for k in range(1, upto + 1):
        x0, y0, x1, y1, dx = BOX[k]
        m = P51.PANELS[k](state.get(k, {})).render()[CROP0:CROP1, :PWID[k]]
        m = cv2.resize(m, (int(round(PWID[k] * S)), PANEL_H), interpolation=cv2.INTER_AREA)
        m = np.clip(m.astype(np.float32) * 1.25, 0, 255).astype(np.uint8)     # the small pen kept dark
        sub = ink[y0:y1, dx:dx + m.shape[1]]
        np.maximum(sub, m[:sub.shape[0], :sub.shape[1]], out=sub)
        if k <= 4:       # the floor and wainscot lines run on to the widened frame
            for yy in (to_page(k, (0, 770))[1], to_page(k, (0, 540))[1]):
                for xa, xb in ((x0, dx + 2), (dx + m.shape[1] - 2, x1)):
                    lm = np.zeros((H, W), np.uint8)
                    cv2.line(lm, (int(xa * 4), int(yy * 4)), (int(xb * 4), int(yy * 4)), 255, 3, cv2.LINE_AA, shift=2)
                    ink = np.maximum(ink, lm)
    return ink


def sup_mask(n_list):
    m = np.zeros((H, W), np.uint8)
    for n, k, a, _ in NOTES:
        if n not in n_list:
            continue
        x, y = anchor(k, a)
        t = pen99.letter([str(n)], SUPCAP, 7100 + n, weight=0.16)
        B.put_mask(m, t, x + t.shape[1] / 2 - SUPCAP * 0.6, y)
    return m


NOTE_TOP = Y0[1] + PANEL_H + 100
COLW = 940
COLX = (110, 1150)


def notes_masks(upto):
    """two columns of numbered notes; returns (ink mask, red number mask, last y)"""
    ink = np.zeros((H, W), np.uint8)
    red = np.zeros((H, W), np.uint8)
    lh = int(NCAP * 1.42)
    # the footnote rule: a short pen line at the left, as in a printed book
    lm = np.zeros((H, W), np.uint8)
    penlib.brush_line(lm, [(110, NOTE_TOP - 64), (620, NOTE_TOP - 64)], 4, 7190)
    ink = np.maximum(ink, lm)
    blocks = []
    for n, k, a, txt in NOTES:
        lines = B.wrap(txt, NCAP, COLW - 70)
        blocks.append((n, lines))
    total = sum(len(l) * lh + 14 for _, l in blocks)
    col_h = 2725 - NOTE_TOP
    assert total <= 2 * col_h, (total, 2 * col_h)
    # fill the left column first, then the right
    col, y = 0, NOTE_TOP
    half = total / 2
    acc = 0
    for n, lines in blocks:
        if col == 0 and acc + len(lines) * lh / 2 > half:
            col, y = 1, NOTE_TOP
        acc += len(lines) * lh + 14
        if n <= upto:
            x = COLX[col]
            num = pen99.letter([f"{n}."], NCAP, 7200 + n, weight=0.15)
            B.blit_mask(red, num, int(x - NCAP * 0.6), int(y - NCAP * 1.15))
            body = B.letter_left(lines, NCAP, 7300 + n)
            B.blit_mask(ink, body, int(x + 62 - NCAP * 0.6), int(y - NCAP * 1.15))
        y += len(lines) * lh + 14
        assert y < 2740, (n, y)
    return ink, red


def build(panels=8, sups=27, notes=27, state=None):
    pg = SHEET.copy()
    ink = panels_ink(panels, state)
    ni, nr = notes_masks(notes)
    ink = np.maximum(ink, ni)
    penlib.ink_onto(pg, ink, penlib.INK)
    red = np.maximum(nr, sup_mask([n for n, k, _, _ in NOTES if n <= sups and k <= panels]))
    penlib.ink_onto(pg, red, RED)
    return pg


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    if "--grid" in sys.argv:
        g = finish(page.copy())
        for k in BOX:
            for px in range(0, PWID[k], 50):
                x, y = to_page(k, (px, CROP0))
                cv2.putText(g, str(px), (int(x), int(y) + 12), 0, 0.35, (0, 0, 255), 1)
                cv2.line(g, (int(x), int(y)), (int(x), int(y) + PANEL_H), (180, 180, 255), 1)
            for py in range(50, CROP1, 50):
                x, y = to_page(k, (0, py))
                cv2.putText(g, str(py), (int(x), int(y)), 0, 0.35, (255, 0, 0), 1)
        from PIL import Image
        Image.fromarray(g[100:1100]).save("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/g70.png")
        sys.exit()
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if "--page-only" not in sys.argv:
        from PIL import Image
        # the scholar at work: the little strip first, then each tier's numbers go in, and the notes are written
        # under the rule a few at a time
        states = [dict(panels=8, sups=0, notes=0), dict(panels=8, sups=9, notes=0), dict(panels=8, sups=9, notes=9),
                  dict(panels=8, sups=17, notes=9), dict(panels=8, sups=17, notes=17), dict(panels=8, sups=27, notes=17),
                  dict(panels=8, sups=27, notes=27)]
        B.save_beats(N, [np.asarray(Image.fromarray(finish(build(**s))).resize((960, 1242), Image.LANCZOS)) for s in states])
        print("beats", len(states))
