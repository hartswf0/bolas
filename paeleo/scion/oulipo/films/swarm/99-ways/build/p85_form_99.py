"""99 ways, page 85 "Form 99" (voice and language; medium: pen-hand).
The incident told only as a railway incident report form, its printed fields filled in pencil, with the form's own
sketch box. The whole page is the form: printed heading, numbered printed fields with ruled writing lines and
tick boxes (blue-black printer's ink, ruled straight, labels in the shared pen hand's capitals), every answer
written in by the agent in pencil (the same shared pen hand, graphite, looser and tilted, one crossing-out), the
four canon lines quoted verbatim in the STATEMENTS field, and field 13, the form's SKETCH OF SCENE box, holding his
pencil plan of the office. All HANDMADE on the LoC 1934 sheet. The form is our own invention (no real railway's
form or name). Run: python3 -I p85_form_99.py [--page-only]"""
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
import b1m2 as B  # noqa: E402

N, PID, TITLE = 85, "form-99", "Form 99"
W, H = pen99.PAGE_W, pen99.PAGE_H
PRINT = hexc("#1c2533")         # printer's blue-black
PENCIL = hexc("#55524f")        # graphite
X0, X1 = 110, 2090
LCAP, ACAP, PITCH = 23, 36, 56
LINES = {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
         "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}


# ------------------------------------------------------------------ marks
def rule(img, x0, y0, x1, y1, w=2, col=PRINT):
    m = np.zeros(img.shape[:2], np.uint8)
    cv2.line(m, (int(x0 * 4), int(y0 * 4)), (int(x1 * 4), int(y1 * 4)), 255, max(1, int(w)), cv2.LINE_AA, shift=2)
    if w > 1:
        m = cv2.dilate(m, np.ones((int(w), int(w)), np.uint8)) if w > 2 else m
    penlib.ink_onto(img, m, col)


def box(img, x0, y0, x1, y1, w=2):
    for a in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        rule(img, *a, w=w)


def text(img, s, cap, x, base, seed, col=PRINT, weight=0.12, tilt=0.0, pencil=False, align="left"):
    m = pen99.letter([s], cap, seed, weight=weight)
    if tilt:
        M = cv2.getRotationMatrix2D((m.shape[1] * 0.0, m.shape[0] * 0.6), tilt, 1.0)
        m = cv2.warpAffine(m, M, (m.shape[1], m.shape[0] + int(abs(tilt) * m.shape[1] / 50)))
    top = int(round(base - cap * 1.15))
    left = int(round(x - cap * 0.6)) if align == "left" else int(round(x - m.shape[1] / 2))
    sub = np.zeros(img.shape[:2], np.uint8)
    B.blit_mask(sub, m, left, top)
    if pencil:
        g = np.random.default_rng(seed).random(sub.shape).astype(np.float32)
        g = cv2.GaussianBlur(g, (0, 0), 0.7)
        sub = (sub.astype(np.float32) * np.clip(0.55 + 0.7 * g, 0, 1)).astype(np.uint8)
    penlib.ink_onto(img, sub, col, 0.92 if pencil else 1.0)
    nz = np.nonzero(m.max(0))[0]
    return left + (nz.max() if len(nz) else 0)


def pencil_line(img, pts, w, seed, alpha=0.9):
    m = np.zeros(img.shape[:2], np.uint8)
    penlib.brush_line(m, pts, w, seed, tremor=1.0)
    g = cv2.GaussianBlur(np.random.default_rng(seed).random(m.shape).astype(np.float32), (0, 0), 0.7)
    m = (m.astype(np.float32) * np.clip(0.6 + 0.6 * g, 0, 1)).astype(np.uint8)
    penlib.ink_onto(img, m, PENCIL, alpha)


def answer(img, lines, x, base0, seed, tilt0=0.12):
    rnd = random.Random(seed)
    ends = []
    for i, l in enumerate(lines):
        ends.append(text(img, l, ACAP, x + rnd.uniform(-4, 6), base0 + i * PITCH - 6 + rnd.uniform(-3, 2), seed + i,
                         col=PENCIL, weight=0.115, tilt=tilt0 + rnd.uniform(-0.18, 0.18), pencil=True))
    return ends


def tick(img, cx, cy, seed):
    pencil_line(img, [(cx - 16, cy - 16), (cx + 2, cy + 2), (cx + 18, cy + 18)], 5, seed)
    pencil_line(img, [(cx + 17, cy - 17), (cx - 1, cy + 1), (cx - 17, cy + 16)], 5, seed + 1)


# ------------------------------------------------------------------ the form
FIELDS = [   # (no, label, answer lines); wrap width computed
    (4, "DUTY ASSIGNED (QUOTE ORDER OR MEMO)", ["As per memo on my desk: \"4:15 - open SERVICE door. Key in cupboard.\""]),
    (5, "WHAT WAS BEING DONE WHEN IRREGULARITY OCCURRED", ["Got up from desk about 4:09 and started across the office to the cupboard for the key."]),
    (6, "INTERRUPTION, IF ANY (STATE BY WHOM)", ["A lady traveller at the ticket window, platform side, stopped me and asked the time."]),
    (7, "ACTION TAKEN", ["Looked at the office clock, which read 4:10, and told her so. She thanked me and left the window."]),
    (8, "CONDITION OF CUPBOARD AND KEYS", ["Went on to the cupboard and opened it. Brass key on its hook, tagged SERVICE, in plain view."]),
]
STATEMENTS = [("Lady (at window):", LINES["question"]), ("Self:", LINES["answer"]), ("Lady:", LINES["thanks"]),
              ("Self (to myself, at the cupboard):", LINES["forgetting"])]


def layout():
    """returns a list of row specs with y positions"""
    rows = []
    y = 352
    rows.append(("top", y, y + 120)); y += 120
    for no, lab, ans in FIELDS:
        wl = B.wrap(ans[0], ACAP, X1 - X0 - 220)
        h = 52 + max(2, len(wl)) * PITCH + 8
        rows.append((no, y, y + h, wl, lab)); y += h
    rows.append(("check", y, y + 210)); y += 210
    rows.append(("stmt", y, y + 52 + 4 * PITCH + 10)); y += 52 + 4 * PITCH + 10
    rows.append(("sketch", y, 2725))
    return rows


ROWS = layout()


def printed(img):
    """the blank printed form"""
    # heading
    text(img, "FORM 99", 70, X0 + 6, 196, 8501, weight=0.15)
    text(img, "REPORT OF IRREGULARITY AT STATION", 48, 1230, 190, 8502, weight=0.13, align="centre")
    text(img, "To be made out by the agent in charge in his own hand and forwarded to the Superintendent the same day.",
         22, 1230, 248, 8503, align="centre")
    text(img, "Write plainly. Answer every question. Quote all statements exactly.", 22, 1230, 286, 8504, align="centre")
    rule(img, X0, 316, X1, 316, 5)
    rule(img, X0, 326, X1, 326, 2)
    for r in ROWS:
        kind, y0, y1 = r[0], r[1], r[2]
        box(img, X0, y0, X1, y1, 3)
        if kind == "top":
            xs = [X0, 760, 1300, X1]
            for x in xs[1:-1]:
                rule(img, x, y0, x, y1, 3)
            for i, lab in enumerate(["1. STATION", "2. DATE", "3. TIME OF OCCURRENCE"]):
                text(img, lab, LCAP, xs[i] + 22, y0 + 36, 8510 + i)
                rule(img, xs[i] + 22, y0 + 98, xs[i + 1] - 22, y0 + 98, 1)
        elif kind == "check":
            text(img, "9. KEY REMOVED FROM HOOK?", LCAP, X0 + 22, y0 + 46, 8520)
            text(img, "10. SERVICE DOOR OPENED?", LCAP, 1110, y0 + 46, 8521)
            for bx, lab in ((X0 + 470, "YES"), (X0 + 700, "NO"), (1560, "YES"), (1790, "NO")):
                box(img, bx, y0 + 14, bx + 46, y0 + 60, 3)
                text(img, lab, LCAP, bx + 70, y0 + 46, 8522 + bx)
            rule(img, X0, y0 + 80, X1, y0 + 80, 1)
            text(img, "11. IF NOT, STATE CAUSE", LCAP, X0 + 22, y0 + 116, 8530)
            rule(img, X0 + 22, y0 + 190, X1 - 22, y0 + 190, 1)
        elif kind == "stmt":
            text(img, "12. STATEMENTS OF PERSONS PRESENT (VERBATIM; NAME EACH SPEAKER)", LCAP, X0 + 22, y0 + 36, 8540)
            for i in range(4):
                rule(img, X0 + 22, y0 + 52 + (i + 1) * PITCH, X1 - 22, y0 + 52 + (i + 1) * PITCH, 1)
        elif kind == "sketch":
            sx = 1440
            rule(img, sx, y0, sx, y1, 3)
            text(img, "13. SKETCH OF SCENE (SHOW POSITIONS OF PERSONS AND OBJECTS)", LCAP, X0 + 22, y0 + 36, 8550)
            text(img, "14. SIGNATURE OF AGENT", LCAP, sx + 22, y0 + 36, 8551)
            rule(img, sx + 22, y0 + 190, X1 - 22, y0 + 190, 1)
            rule(img, sx, y0 + 230, X1, y0 + 230, 3)
            text(img, "15. REMARKS OF SUPERINTENDENT", LCAP, sx + 22, y0 + 266, 8552)
            for k in range(5):
                rule(img, sx + 22, y0 + 330 + k * PITCH, X1 - 22, y0 + 330 + k * PITCH, 1)
            text(img, "(Not to be filled in by agent)", 20, sx + 22, y1 - 22, 8553)
        else:
            no, _, _, wl, lab = r
            text(img, f"{no}. {lab}", LCAP, X0 + 22, y0 + 36, 8560 + no)
            for i in range(max(2, len(wl))):
                rule(img, X0 + 22, y0 + 52 + (i + 1) * PITCH, X1 - 22, y0 + 52 + (i + 1) * PITCH, 1)


def fill(img, stage):
    """pencil, field by field. stage 1: 1-5, 2: 6-7, 3: 8, 4: 9-11, 5: statements, 6: sketch, 7: signature"""
    for r in ROWS:
        kind, y0, y1 = r[0], r[1], r[2]
        if kind == "top" and stage >= 1:
            answer(img, ["Randolph, Vt."], X0 + 30, y0 + 92, 8600)
            answer(img, ["Sept. 1937, afternoon"], 790, y0 + 92, 8602)
            answer(img, ["4:09 to 4:11 p.m."], 1330, y0 + 92, 8604)
        elif kind == "check" and stage >= 4:
            tick(img, X0 + 723, y0 + 37, 8610)
            tick(img, 1813, y0 + 37, 8612)
            e = answer(img, ["Key was"], X0 + 420, y0 + 116 + 70, 8614)
            pencil_line(img, [(X0 + 410, y0 + 172), (e[0] + 6, y0 + 168)], 4, 8615)          # struck out
            answer(img, ["Stood at the open cupboard and could not think what I had come for."], e[0] + 40, y0 + 186, 8616)
        elif kind == "stmt" and stage >= 5:
            for i, (who, line) in enumerate(STATEMENTS):
                base = y0 + 52 + (i + 1) * PITCH
                e = answer(img, [who], X0 + 34, base, 8620 + i * 3)
                answer(img, ["\"" + line + "\""], max(e[0] + 30, X0 + 420), base, 8621 + i * 3)
        elif kind == "sketch":
            if stage >= 6:
                sketch(img, X0 + 30, y0 + 70, 1410, y1 - 24)
            if stage >= 7:
                signature(img, 1480, y0 + 120)
        elif kind in (4, 5, 6, 7, 8):
            need = {4: 1, 5: 1, 6: 2, 7: 2, 8: 3}[kind]
            if stage >= need:
                answer(img, r[3], X0 + 34, y0 + 52 + PITCH, 8630 + kind * 10)


def sketch(img, x0, y0, x1, y1):
    """his pencil plan of the office: walls, window, clock, cupboard (open, key on its hook), SERVICE door, his path"""
    s = 8700
    L, T, R, Bt = x0 + 60, y0 + 70, x1 - 60, y1 - 60
    pl = lambda pts, w=4: pencil_line(img, pts, w, s + int(pts[0][0] + pts[0][1]) % 997)
    # walls, a gap for the window (left wall), the SERVICE door (right wall, shut)
    wy0, wy1 = T + 120, T + 300
    pl([(L, T), (R, T)], 5)
    pl([(L, T), (L, wy0)], 5); pl([(L, wy1), (L, Bt)], 5)
    pl([(L, Bt), (R, Bt)], 5)
    dy0, dy1 = Bt - 230, Bt - 80
    pl([(R, T), (R, dy0)], 5); pl([(R, dy1), (R, Bt)], 5)
    # window: double line with glazing tick
    pl([(L - 10, wy0), (L - 10, wy1)], 3); pl([(L + 10, wy0), (L + 10, wy1)], 3)
    text(img, "ticket", 26, L + 30, (wy0 + wy1) / 2 - 10, s + 1, col=PENCIL, pencil=True)
    text(img, "window", 26, L + 30, (wy0 + wy1) / 2 + 28, s + 2, col=PENCIL, pencil=True)
    # the lady outside: an X and her label
    cx, cy = L - 46, (wy0 + wy1) / 2
    pl([(cx - 16, cy - 16), (cx + 16, cy + 16)], 4); pl([(cx + 16, cy - 16), (cx - 16, cy + 16)], 4)
    text(img, "lady", 26, L - 70, wy0 - 20, s + 3, col=PENCIL, pencil=True)
    # SERVICE door: a closed door line across the gap, label
    pl([(R, dy0), (R, dy1)], 7)
    pl([(R - 16, dy0), (R - 16, dy1)], 3); pl([(R - 16, dy0), (R, dy0)], 3); pl([(R - 16, dy1), (R, dy1)], 3)
    text(img, "SERVICE door", 26, R - 230, (dy0 + dy1) / 2 + 10, s + 4, col=PENCIL, pencil=True)
    text(img, "(shut)", 26, R - 160, (dy0 + dy1) / 2 + 48, s + 5, col=PENCIL, pencil=True)
    # cupboard on the right wall, above the door: box, door swung open (left jamb), key
    cu0, cu1 = T + 70, T + 260
    pl([(R - 90, cu0), (R, cu0)], 4); pl([(R - 90, cu1), (R, cu1)], 4); pl([(R - 90, cu0), (R - 90, cu1)], 4)
    pl([(R - 90, cu1), (R - 190, cu1 + 60)], 4)                 # its door, swung open
    pl([(R - 150, cu1 + 6), (R - 168, cu1 + 34)], 2)             # swing arc tick
    text(img, "cupb'd", 26, R - 300, cu0 + 30, s + 6, col=PENCIL, pencil=True)
    text(img, "(open)", 26, R - 300, cu0 + 68, s + 7, col=PENCIL, pencil=True)
    kx, ky = R - 44, (cu0 + cu1) / 2 - 10                         # key on its hook
    pl([(kx, ky - 30), (kx, ky + 30)], 3)
    pencil_line(img, B.circle_pts(kx, ky - 42, 12, 12) + [B.circle_pts(kx, ky - 42, 12, 12)[0]], 3, s + 8)
    pl([(kx, ky + 22), (kx + 12, ky + 22)], 3)
    text(img, "key", 24, R - 70, cu1 - 18, s + 9, col=PENCIL, pencil=True)
    # clock on the top wall
    ccx = (L + R) / 2 - 40
    pencil_line(img, B.circle_pts(ccx, T + 38, 26, 18) + [B.circle_pts(ccx, T + 38, 26, 18)[0]], 3, s + 10)
    pl([(ccx, T + 38), (ccx + 13, T + 30)], 2); pl([(ccx, T + 38), (ccx + 4, T + 18)], 2)
    text(img, "clock (4:10)", 26, ccx + 40, T + 50, s + 11, col=PENCIL, pencil=True)
    # desk lower left
    dx0, dyy = L + 60, Bt - 190
    pl([(dx0, dyy), (dx0 + 230, dyy), (dx0 + 230, dyy + 110), (dx0, dyy + 110), (dx0, dyy)], 4)
    text(img, "desk", 26, dx0 + 70, dyy + 66, s + 12, col=PENCIL, pencil=True)
    # my path: dotted, numbered 1 (desk) 2 (stopped by window) 3 (cupboard)
    path = [(dx0 + 250, dyy + 40), ((L + R) / 2 - 120, (T + Bt) / 2 + 40), (L + 260, (wy0 + wy1) / 2 + 30),
            ((L + R) / 2 + 60, (T + Bt) / 2 - 30), (R - 230, cu1 + 110)]
    pts = []
    for a, b in zip(path[:-1], path[1:]):
        for t in np.linspace(0, 1, 9)[:-1]:
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    pts.append(path[-1])
    for i, p in enumerate(pts):
        if i % 2 == 0 and i < len(pts) - 1:
            q = pts[i + 1]
            pencil_line(img, [p, ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)], 3, s + 20 + i)
    for n_, p in ((1, path[0]), (2, path[2]), (3, path[4])):
        pencil_line(img, B.circle_pts(p[0], p[1], 22, 14) + [B.circle_pts(p[0], p[1], 22, 14)[0]], 3, s + 60 + n_)
        text(img, str(n_), 26, p[0], p[1] + 13, s + 70 + n_, col=PENCIL, pencil=True, align="centre")
    text(img, "1 got up   2 asked the time   3 here, and ?", 26, L, Bt + 46, s + 80, col=PENCIL, pencil=True)


def signature(img, x, base):
    """his signature: a pencil scrawl, and 'Agent, Randolph' under it"""
    rnd = random.Random(8800)
    pts = []
    for k in range(60):
        t = k / 59
        pts.append((x + 20 + t * 420, base - 20 - 28 * math.sin(t * 19) * (0.6 + 0.4 * math.sin(t * 5)) + rnd.uniform(-3, 3)))
    pencil_line(img, pts, 3.5, 8801)
    pencil_line(img, [(x + 30, base + 6), (x + 470, base - 4)], 3, 8802)
    answer(img, ["Agent, Randolph"], x + 40, base + 72, 8803)


SHEET = pen99.sheet99()


def build(stage=7):
    pg = SHEET.copy()
    printed(pg)
    fill(pg, stage)
    return pg


def main():
    page = build(7)
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg", size, [(r[0], r[1], r[2]) for r in ROWS])
    if "--page-only" in sys.argv:
        return
    frames = [build(s) for s in range(0, 8)]
    for f in frames:
        pen99.folio(f, N, TITLE)
    print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    main()
