"""99 ways, page 44 "N+7" (formal / Oulipian rule; medium: pen-hand).
Rule: every noun of the captions and lines is replaced by the seventh noun after it in our own station glossary,
printed in the margin. The pictures stay true (pen line drawings: the b1m2 figures and scenery traced as on page 32,
reused from build/p32_how_to_forget.py); every word on the page that is a glossary noun -- in captions, in the four
lines, on the memo slip, on the window header, on the key tag and the door card -- is moved seven places on.
All HANDMADE: the shared pen hand (pen99 / penlib) on the LoC 1934 sheet; one ink.
Run: python3 -I p44_n_plus_seven.py [--page-only]"""
import json
import re
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p32_how_to_forget as P  # noqa: E402  (pen helpers and line diagrams of page 32)

N, PID, TITLE = 44, "n-plus-seven", "N+7"
W, H = 2200, 2850
INK = np.array([18, 17, 16], np.float32)
CANON = json.load(open(B.ROOT / "films/swarm/99-ways/canon.json"))
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}

# ------------------------------------------------------------------ our station glossary (alphabetical)
GLOSSARY = sorted(set("""agent almanac axle baggage ballast bell boiler brakeman caboose chin cinder clock coal
conductor coupling cupboard depot desk dispatcher door engine freight gauge hook inkwell junction key lamp lantern
ledger lever memo padlock parcel pencil platform porter rail schedule semaphore service siding signal stove stranger
switch tag telegraph ticket time timetable trunk valise way whistle window wire yard""".split()))
NG = len(GLOSSARY)
IDX = {w: i for i, w in enumerate(GLOSSARY)}


def n7(word):
    return GLOSSARY[(IDX[word] + 7) % NG]


ON = {"n7": True}
SEEN = {}       # source noun -> replacement, for every word actually moved on the page


def transform(s):
    if not ON["n7"]:
        return s

    def rep(m):
        w = m.group(0)
        lw = w.lower()
        if lw not in IDX:
            return w
        r = n7(lw)
        SEEN[lw] = r
        if w.isupper() and len(w) > 1:
            return r.upper()
        if w[0].isupper():
            return r[0].upper() + r[1:]
        return r
    return re.sub(r"[A-Za-z]+", rep, s)


# every word drawn by the page-32 pen helpers passes through the N+7 transform
_text, _text_c = P.text, P.text_c
def _fit(s, a):
    """A short drawn label (tag, card, header) keeps its width: a longer replacement is lettered smaller."""
    t = transform(s)
    if len(s) <= 14 and len(t) > len(s) and len(a) >= 3:
        a = list(a)
        a[2] = a[2] * len(s) / len(t)
    return t, a


def _wt(mask, s, *a, **k):
    t, a = _fit(s, a)
    return _text(mask, t, *a, **k)


def _wtc(mask, s, *a, **k):
    t, a = _fit(s, a)
    return _text_c(mask, t, *a, **k)


P.text, P.text_c = _wt, _wtc

# the incident in our own captions (nouns: desk agent memo service door key cupboard way stranger ticket window time
# clock hook tag pencil chin); the four canon lines verbatim before the transform
CAPS = [
    "At his desk the agent reads the memo: at 4:15 open the SERVICE door; the key is in the cupboard. He sets off.",
    "On his way a stranger at the TICKET window asks: “" + LN["question"] + "”",
    "He looks up at the clock and answers: “" + LN["answer"] + "”",
    "The stranger says “" + LN["thanks"] + "” and leaves the window. He walks on to the cupboard.",
    "He opens the cupboard. The key hangs on its hook, its tag lettered SERVICE.",
    "Pencil to his chin, he asks himself: “" + LN["forgetting"] + "” The key stays on its hook; the SERVICE door stays shut.",
]

CELLS = []
for r, y0 in enumerate((350, 1150, 1950)):
    for c, x0 in enumerate((110, 815)):
        CELLS.append((x0, y0, x0 + 685, y0 + 780))
GX0, GX1 = 1560, 2090
CAP = 38


# page 32's line drawings, without its instruction-sheet layer: no 'you' label (panel 1), no 'LOOK' label or its
# arrow (panel 5), no prohibition circles or their little key and door (panel 6). Only the pictures and their
# drawn words (memo slip, window header, key tag, door card, 'on to the cupboard', 'to the platform', the 4:10).
def diag1(m, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    dk = P.desk(x0 + 190, fy - 150, 220, fy)
    for s_ in dk:
        s_.z += 20
    P.trace(m, P.agent(x0 + 110, fy, face=1, scale=0.36, legs=(14, -6), lean=10, tilt=4, sh=34, el=-20,
                       pencil_deg=200) + dk, 4, 3403)
    P.memo_slip(m, x0 + 250, fy - 222, 16, 3402)
    cup, _ = P.cupboard(x1 - 200, fy - 230, 130, 230)
    P.trace(m, cup, 4, 3404)
    P.arrow(m, [(x0 + 400, fy - 240), (x0 + 580, fy - 340), (x1 - 220, fy - 160)], 6, 3405)
    P.dashed(m, [(x0 + 110, fy + 14), (x1 - 210, fy + 14)], 4, 3406)


def diag5(m, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    cup, ins = P.cupboard(x0 + 310, fy - 280, 170, 280, open_deg=112)
    P.trace(m, cup, 4, 3441)
    ix0, iy0, ix1, iy1 = ins
    kx, ky = (ix0 + ix1) / 2 + 6, iy0 + 72
    P.key_outline(m, kx, ky, 0.12, 3, 3442, tag=False)
    P.trace(m, P.agent(x0 + 110, fy, face=1, scale=0.36, legs=(14, -12), sh=64, el=18, pencil_deg=200), 4, 3443)
    zx, zy, zr = x1 - 210, fy - 200, 150          # the key on its hook, close up, with its tag
    P.circle(m, zx, zy, zr, 6, 3444)
    P.line(m, [(kx + 14, ky - 10), (zx - zr * 0.96, zy - zr * 0.28)], 3, 3445, 0.2)
    P.line(m, [(kx + 14, ky + 50), (zx - zr * 0.92, zy + zr * 0.38)], 3, 3446, 0.2)
    P.key_outline(m, zx - 40, zy, 0.30, 4, 3447, tag=True)


def diag6(m, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    cup, ins = P.cupboard(x0 + 300, fy - 280, 170, 280, open_deg=112)
    P.trace(m, cup, 4, 3451)
    ix0, iy0, ix1, iy1 = ins
    kx, ky = (ix0 + ix1) / 2 + 6, iy0 + 72
    P.key_outline(m, kx, ky, 0.12, 3, 3452, tag=False)
    P.trace(m, P.service_door(x0 + 560, fy - 300, 130, 300), 4, 3453)
    P.line(m, [(x0 + 575, fy - 266), (x0 + 675, fy - 264), (x0 + 674, fy - 232), (x0 + 576, fy - 234),
               (x0 + 575, fy - 266)], 3, 3454, 0.2)
    P.text_c(m, "SERVICE", x0 + 625, fy - 240, 17, 3455)
    P.trace(m, P.agent(x0 + 100, fy, face=1, scale=0.36, legs=(3, -3), sh=50, el=120, wr=8, pencil_deg=40, tilt=6),
            4, 3456)
    P.text_c(m, "?", x0 + 215, fy - 270, 64, 3457, weight=0.14)


DIAGS = [diag1, P.diag2, P.diag3, P.diag4, diag5, diag6]


def diagram(i):
    """Draw diagram i at page 32's native 970 x 420 scale into its own mask, then fit it into a cell."""
    m = np.zeros((430, 970), np.uint8)
    dc = (0, 0, 970, 420)
    DIAGS[i](m, dc)
    ys, xs = np.nonzero(m > 20)
    return m[max(0, ys.min() - 6):ys.max() + 6, max(0, xs.min() - 6):xs.max() + 6]


def draw_cell(ink, i, cell):
    x0, y0, x1, y1 = cell
    sd = 4400 + i * 40
    for k, (a, b) in enumerate((((x0, y0), (x1, y0 + 1)), ((x1, y0), (x1 - 1, y1)), ((x1, y1), (x0, y1 - 1)),
                                ((x0, y1), (x0 + 1, y0)))):
        P.line(ink, [a, b], 5, sd + k, 0.6)
    P.circle(ink, x0 + 52, y0 + 54, 34, 6, sd + 5)
    _text_c(ink, str(i + 1), x0 + 52, y0 + 54 + 20, 44, sd + 6, weight=0.16)
    s = transform(CAPS[i])
    lines = B.wrap(s, CAP, (x1 - x0) - 130)
    for j, l in enumerate(lines):
        xo = x0 + 104 if j < 2 else x0 + 34
        _text(ink, l, xo, y0 + 62 + j * 54, CAP, sd + 10 + j)
    top = y0 + 62 + len(lines) * 54 + 6
    d = diagram(i)
    s_ = min((x1 - x0 - 20) / d.shape[1], (y1 - 14 - top) / d.shape[0])
    d = cv2.resize(d, None, fx=s_, fy=s_, interpolation=cv2.INTER_AREA)
    d = cv2.dilate(d, np.ones((2, 2), np.uint8))
    B.blit_mask(ink, d, int((x0 + x1) / 2 - d.shape[1] / 2), int(y1 - 12 - d.shape[0]))
    return s, lines


def glossary(ink, used, repl):
    x0 = GX0
    _text(ink, "STATION", x0 + 10, 410, 46, 4601, weight=0.16)
    _text(ink, "GLOSSARY", x0 + 10, 470, 46, 4602, weight=0.16)
    P.line(ink, [(x0, 500), (GX1, 502)], 5, 4603)
    _text(ink, "n + 7: count seven on;", x0 + 10, 552, 30, 4604)
    _text(ink, "after 58, go on from 1.", x0 + 10, 594, 30, 4605)
    _text(ink, "underlined: on the page", x0 + 10, 636, 30, 4606)
    rows = (NG + 1) // 2
    y_top, pitch = 712, 69
    cols = (x0, x0 + 270)
    for i, w in enumerate(GLOSSARY):
        c, r = divmod(i, rows)
        bx = cols[c]
        base = y_top + r * pitch
        num = f"{i + 1}"
        _text(ink, num, bx + 10, base, 30, 4700 + i)
        wx = bx + 72
        m = pen99.letter([w], 34, 4800 + i)
        B.blit_mask(ink, m, int(round(wx - 34 * 0.6)), int(round(base - 34 * 1.15)))
        if w in repl:
            P.line(ink, [(wx - 4, base + 9), (wx - 34 * 1.2 + m.shape[1] + 4, base + 11)], 4, 4900 + i, 0.4)
    P.line(ink, [(x0 + 262, 690), (x0 + 264, y_top + rows * pitch - 40)], 3, 4990, 0.5)


def build(n_done=6, final=True):
    """n_done: panels whose captions are already moved seven on (the rest still read in plain nouns)."""
    page = cv2.GaussianBlur(pen99.sheet99().astype(np.float32), (0, 0), 0.6)
    ink = np.zeros((H, W), np.uint8)
    SEEN.clear()
    _text(ink, "N + 7", 130, 250, 120, 4501, weight=0.15)
    ON["n7"] = True
    ex = f"door ({IDX['door'] + 1}) + 7 = {n7('door')} ({IDX[n7('door')] + 1})"
    _text(ink, "e.g. " + ex, 560, 248, 40, 4502)
    P.line(ink, [(110, 290), (1500, 292)], 6, 4503)
    out = []
    for i, cell in enumerate(CELLS):
        ON["n7"] = i < n_done
        out.append(draw_cell(ink, i, cell))
    ON["n7"] = True
    repl = set(SEEN.values())
    glossary(ink, set(SEEN), repl)
    penlib.ink_onto(page, ink, INK)
    return page, out, dict(SEEN)


def main():
    page, out, seen = build(6)
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    print("bytes", size)
    for s, l in out:
        print(s)
    rec = {"captions_n7": [s for s, _ in out], "moved": seen,
           "glossary": [f"{i + 1} {w}" for i, w in enumerate(GLOSSARY)]}
    json.dump(rec, open(B.SRC / "p44_rec.json", "w"), indent=1, ensure_ascii=False)
    if "--page-only" in sys.argv:
        return
    frames = []
    for n in range(0, 6):
        f, _, _ = build(n)
        pen99.folio(f, N, TITLE)
        frames.append(f)
    frames.append(img.astype(np.float32))
    print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    main()
