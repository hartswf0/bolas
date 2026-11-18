"""Page 87 Two-colour stencil (medium and material; medium: stencil-dye).

The whole page (folio line excepted) is printed from exactly two cut stencils, one per dye: VERMILION and INDIGO,
by page 08's stencil method (build/p08_lipogram.dye: paper ties, misregistration, mottle, dye pooling at the edges)
on the LoC 1934 sheet. There is no drawn line anywhere: no panel border, no balloon outline, no shading. Panels are
fields of vermilion wall and indigo floor; everything else is either a vermilion or indigo shape, the two overprinted
(a dark plum where indigo falls on vermilion), or bare paper RESERVED by both stencils (faces, shirt, glass, clock
dial, balloons, the memo, the cards). Lettering is cut in the indigo stencil from the shared pen hand's strokes
(fattened, as page 08's cut letters) and printed on reserved paper; TICKET OFFICE is reserved out of an indigo board.
Figures and furniture: the b1m2 cut model; the key: the ANRC 1922 key cutout as a vermilion stencil.
Run: python3 -I p87_two_colour_stencil.py [beats]
"""
import math
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from cutpaper99 import Cut, ellipse  # noqa: E402
import b1m2 as B  # noqa: E402
import p08_lipogram as S  # noqa: E402

N, PID, TITLE = 87, "two-colour-stencil", "Two-colour stencil"
W, H = pen99.PAGE_W, pen99.PAGE_H
VERM = np.array([204, 70, 44], np.float32)
INDI = np.array([40, 58, 112], np.float32)
SHIFT_V, SHIFT_I = (-3, 2), (3, -2)

ROWS = [(110, 730), (770, 1390), (1430, 2050), (2090, 2710)]
WIDE = (110, 2090)
HALF = [(110, 1080), (1120, 2090)]
CAPH = 104           # caption band (bare paper) at the head of each panel
TCAP, BCAP = 40, 44


class Panel:
    def __init__(self, box, floor):
        self.x0, self.y0, self.x1, self.y1 = box
        self.w, self.h = self.x1 - self.x0, self.y1 - self.y0
        self.V = np.zeros((self.h, self.w), np.uint8)
        self.I = np.zeros((self.h, self.w), np.uint8)
        self.floor = floor
        self.V[CAPH:floor] = 255                    # the vermilion wall
        self.I[floor:] = 255                         # the indigo floor
        self.cut = Cut(self.h, self.w, box[0] * 7 + box[1], ground="#ffffff")

    # ops ---------------------------------------------------------------
    def rast(self, shapes, roles):
        return B.raster(shapes, self.w, self.h, roles=roles, facet=0.8)

    def poly(self, pts, jitter=0.7):
        return self.cut.mask(np.asarray(pts, np.float32), jitter=jitter)

    def reserve(self, m):
        self.V[m > 127] = 0
        self.I[m > 127] = 0

    def ind(self, m):
        self.I = np.maximum(self.I, m)

    def ver(self, m):
        self.V = np.maximum(self.V, m)

    def only_ind(self, m):        # indigo on bare paper (vermilion reserved there)
        self.V[m > 127] = 0
        self.ind(m)

    def only_ver(self, m):
        self.I[m > 127] = 0
        self.ver(m)

    def letters(self, lines, cap, cx, cy, reserve_ground=False, align="center", seed=0):
        """indigo stencil letters cut from the pen hand's strokes; centred at (cx, cy) or left at cx."""
        if align == "left":
            m = B.letter_left(lines, cap, seed, weight=0.16)
            x = int(cx - cap * 0.5)
        else:
            m = pen99.letter(lines, cap, seed, weight=0.16)
            x = int(cx - m.shape[1] / 2)
        y = int(cy - m.shape[0] / 2)
        full = np.zeros((self.h, self.w), np.uint8)
        B.blit_mask(full, m, x, y)
        full = np.where(full > 100, 255, 0).astype(np.uint8)
        if reserve_ground:
            return full
        self.only_ind(full)
        return full

    def caption(self, text, seed, width=None):
        lines = B.wrap(text, TCAP, (width or self.w) - 60)
        assert len(lines) == 1, lines
        self.letters(lines, TCAP, 26, 14 + len(lines) * TCAP * 0.71 + 8, align="left", seed=seed)

    def balloon(self, lines, centre, tip, seed, cap=BCAP):
        """a reserved paper balloon (no outline): an oval and a tail cut out of the stencils, letters in indigo"""
        lm = pen99.letter(lines, cap, seed, weight=0.16)
        rx, ry = lm.shape[1] / 2 + cap * 0.55, lm.shape[0] / 2 + cap * 0.45
        cx, cy = centre
        ov = ellipse(cx, cy, rx, ry, n=64)
        d = np.subtract(tip, centre)
        a = math.atan2(d[1], d[0])
        nrm = np.array([-math.sin(a), math.cos(a)])
        base = np.array([cx + rx * 0.8 * math.cos(a), cy + ry * 0.8 * math.sin(a)])
        tail = [base + nrm * cap * 0.55, base - nrm * cap * 0.55, tip]
        m = np.maximum(self.poly(ov, 0.9), self.poly(tail, 0.6))
        self.reserve(m)
        self.letters(lines, cap, cx, cy + cap * 0.08, seed=seed)

    def slip(self, lines, cap, cx, cy, seed, pad=(18, 12), tilt=0):
        lm = pen99.letter(lines, cap, seed, weight=0.16)
        hw, hh = lm.shape[1] / 2 + pad[0] - cap * 0.4, lm.shape[0] / 2 + pad[1] - cap * 0.2
        pts = np.array([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)])
        t = math.radians(tilt)
        R = np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])
        self.reserve(self.poly(pts @ R.T + (cx, cy)))
        full = self.letters(lines, cap, cx, cy, reserve_ground=True, seed=seed)
        if tilt:
            M = cv2.getRotationMatrix2D((float(cx), float(cy)), -tilt, 1.0)
            full = cv2.warpAffine(full, M, (self.w, self.h))
        self.only_ind(full)

    # figures -------------------------------------------------------------
    def agent(self, **kw):
        fig = B.agent(**kw)
        allroles = {s.role for s in fig} - {"button", "glass", "glass_arm", "pin", "garter"}
        self.reserve(self.rast(fig, allroles))                                        # paper: face, shirt, hands
        self.only_ind(self.rast(fig, {"waistcoat", "button", "trousers", "hair", "tie"}))
        eyes = self.rast(fig, {"glass_in"})
        self.only_ind(cv2.dilate(eyes, np.ones((3, 3), np.uint8)))
        self.only_ver(self.rast(fig, {"pencil"}))
        return fig

    def stranger(self, **kw):
        fig = B.stranger(**kw)
        self.reserve(self.rast(fig, {"coat", "collar", "skin_s", "hat", "bow", "glove"}))
        self.only_ver(self.rast(fig, {"coat", "bow"}))
        self.only_ind(self.rast(fig, {"collar", "hat"}))
        for s in fig:
            if s.role == "eye":
                self.only_ind(self.poly(np.asarray(s.curve()) , 0.2))
        return fig

    def window(self, x0, y0, w, h, sill):
        ws, sill = B.window(x0, y0, w, h, sill=sill, header=64)
        glass = self.poly([(x0, y0 + 64), (x0 + w, y0 + 64), (x0 + w, sill), (x0, sill)], 0.4)
        self.reserve(glass)
        return ws, sill

    def window_front(self, ws, x0, y0, w, seed):
        self.ind(self.rast(ws, {"window"}))
        m = self.letters(["TICKET OFFICE"], 28, x0 + w / 2, y0 + 33, reserve_ground=True, seed=seed)
        self.reserve(m)

    def key(self, x, y, scale):
        km = S.key_stencil(self.w, self.h, x, y, scale)
        km = np.where(km > 110, 255, 0).astype(np.uint8)
        self.only_ver(km)

    def paste(self, PV, PI):
        PV[self.y0:self.y1, self.x0:self.x1] = self.V
        PI[self.y0:self.y1, self.x0:self.x1] = self.I


# ------------------------------------------------------------------ the six panels
def p1():
    P = Panel((WIDE[0], ROWS[0][0], WIDE[1], ROWS[0][1]), 560)
    P.caption("Randolph, 1937. His memo: open the SERVICE door at 4:15, key in the cupboard. Up he gets.", 8701)
    cup, _ = B.cupboard(1380, 250, 230, 310)
    P.ind(P.rast(cup, {"cupboard", "slit"}))
    sd = B.service_door(1720, 200, 190, 360)
    P.ind(P.rast(sd, {"sdoor", "slit"}))
    P.slip(["SERVICE"], 26, 1815, 250, 8702, pad=(12, 6))
    P.ind(P.rast(B.desk(160, 380, 420, 560), {"desk", "slit"}))
    P.slip(["4:15 - open SERVICE door.", "Key in cupboard."], 26, 330, 330, 8703, tilt=-3)
    P.agent(x=820, floor=566, face=1, scale=0.50, legs=(16, -10), sh=10, el=40, pencil_deg=200, lean=6)
    return P


def p2():
    P = Panel((HALF[0][0], ROWS[1][0], HALF[0][1], ROWS[1][1]), 560)
    P.caption("On his way, a lady at the ticket window:", 8711)
    ws, sill = P.window(60, 124, 360, 436, 456)
    P.stranger(x=250, sill=sill + 4, face=1, scale=1.12)
    P.window_front(ws, 60, 124, 360, 8712)
    P.agent(x=780, floor=566, face=-1, scale=0.48, legs=(4, -4), sh=4, el=10, pencil_deg=190)
    P.balloon(["Pardon me —", "have you the", "right time?"], (590, 250), (330, 300), 8713)
    return P


def p3():
    P = Panel((HALF[1][0], ROWS[1][0], HALF[1][1], ROWS[1][1]), 560)
    P.caption("He looks up at the wall clock:", 8721)
    ck = B.clock(170, 230, 82, 4, 10, swing=8)
    P.ind(P.rast(ck, {"clock", "dial", "pendwin"}))
    P.reserve(P.rast(ck, {"dial"}) if False else _disc(P, 170, 230, 82 * 0.80))
    P.only_ind(P.rast(ck, {"hand"}))
    for s in ck:
        if s.role == "clock" and len(s.pts) == 4 and np.linalg.norm(s.pts.max(0) - s.pts.min(0)) < 82 * 0.3:
            P.only_ind(P.poly(s.pts, 0.2))
    P.agent(x=650, floor=566, face=-1, scale=0.48, legs=(3, -3), tilt=-22, sh=6, el=20, pencil_deg=190)
    P.balloon(["Ten past four,", "by the clock."], (440, 215), (590, 262), 8722, cap=40)
    return P


def _disc(P, cx, cy, r):
    return P.poly(ellipse(cx, cy, r, r, n=48), 0.3)


def p4():
    P = Panel((HALF[0][0], ROWS[2][0], HALF[0][1], ROWS[2][1]), 560)
    P.caption("She thanks him and goes.", 8731)
    ws, sill = P.window(60, 124, 360, 436, 456)
    P.stranger(x=160, sill=sill + 4, face=-1, scale=1.12, tilt=-4)
    P.window_front(ws, 60, 124, 360, 8732)
    P.agent(x=800, floor=566, face=-1, scale=0.48, legs=(4, -4), sh=4, el=10, tilt=2, pencil_deg=190)
    P.balloon(["Much", "obliged!"], (560, 270), (300, 300), 8733)
    return P


def cup_open(P, x0, y0, w, h):
    cup, ins = B.cupboard(x0, y0, w, h, open_deg=112)
    P.ind(P.rast(cup, {"cupboard", "inside", "shelf", "door"}))
    ix0, iy0, ix1, iy1 = ins
    P.reserve(P.poly([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)], 0.4))          # the lit opening: bare paper
    P.only_ind(P.rast(cup, {"shelf"}))
    kx, ky = (ix0 + ix1) / 2 - 10, iy0 + 110
    P.only_ind(P.poly([(kx - 22, ky - 96), (kx + 6, ky - 96), (kx + 6, ky - 78), (kx - 22, ky - 78)], 0.3))   # the hook
    P.key(kx, ky, 0.22)
    # the SERVICE tag: a reserved paper slip lettered in indigo
    P.slip(["SERVICE"], 22, (kx + 18 + ix1 - 6) / 2, ky + 45, 8790, pad=(8, 4), tilt=6)
    return ins


def p5():
    P = Panel((HALF[1][0], ROWS[2][0], HALF[1][1], ROWS[2][1]), 560)
    P.caption("The cupboard opens: there hangs the key.", 8741)
    cup_open(P, 400, 170, 280, 390)
    P.agent(x=230, floor=566, face=1, scale=0.48, legs=(14, -12), sh=60, el=20, pencil_deg=200)
    return P


def p6():
    P = Panel((WIDE[0], ROWS[3][0], WIDE[1], ROWS[3][1]), 560)
    P.caption("The key stays on its hook. The SERVICE door stays shut.", 8751)
    cup_open(P, 360, 170, 280, 390)
    sd = B.service_door(1660, 160, 220, 400)
    P.ind(P.rast(sd, {"sdoor", "slit"}))
    P.slip(["SERVICE"], 30, 1770, 215, 8752, pad=(14, 6))
    P.agent(x=1120, floor=566, face=-1, scale=0.50, legs=(3, -3), sh=48, el=118, wr=8, pencil_deg=40, tilt=-6)
    P.balloon(["Well, here I am...", "and what for?"], (820, 230), (1105, 200), 8753)
    return P


PANELS = [p1, p2, p3, p4, p5, p6]


def masks():
    PV = np.zeros((H, W), np.uint8)
    PI = np.zeros((H, W), np.uint8)
    for fn in PANELS:
        fn().paste(PV, PI)
    return PV, PI


def wipe(m, frac, seed=0):
    """the dabbing brush has reached `frac` of the stencil, top to bottom, its front ragged"""
    if frac >= 1:
        return m
    if frac <= 0:
        return np.zeros_like(m)
    y = int(110 + (2710 - 110) * frac)
    out = m.copy()
    rng = np.random.default_rng(seed)
    xs = np.arange(W)
    edge = (y + 30 * np.sin(xs / 90 + seed) + rng.normal(0, 3, W)).astype(int)
    rows = np.arange(H)[:, None]
    out[rows > edge[None, :]] = 0
    return out


def print_page(PV, PI, fv=1.0, fi=1.0):
    pg = pen99.sheet99().astype(np.float32)
    if fv > 0:
        S.dye(pg, wipe(PV, fv, 1), VERM, 8781, shift=SHIFT_V, strength=0.90)
    if fi > 0:
        S.dye(pg, wipe(PI, fi, 2), INDI, 8782, shift=SHIFT_I, strength=0.92)
    return pg


def record(size, colours):
    rec = {
        "n": N, "id": PID, "title": TITLE, "family": "medium and material", "medium": "stencil-dye", "canon_revision": "c1",
        "rule": "Only stencilled shapes in two dyes: no outline, no shading.",
        "declares": "keeps E0-E5, the four lines and the outcome",
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg",
        "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p87_two_colour_stencil.py (dye method: build/p08_lipogram.dye; cut model: build/b1m2.py; scissor cuts: kit/cutpaper99.Cut.mask)",
        "sources": ["99-ways-template:loc-blank-sheet-1934", "99-ways-template:anrc-gold-key-1922", "99-ways:handmade"],
        "made": [
            "two HANDMADE stencils cut for the whole page, one per dye: VERMILION (the walls, the stranger's coat, the pencil, the brass key) and INDIGO (the floors, furniture, waistcoat, trousers, hair, hat, the ticket-window frame, clock case and hands, and all lettering); each printed once by page 08's method (paper ties across large openings, a few px of misregistration, mottled density, dye pooling at the edges) on the LoC 1934 sheet",
            "where indigo falls on vermilion it overprints to a dark plum (cupboard, desk, doors, waistcoat against the wall); no third ink",
            "bare paper RESERVED by both stencils for faces, shirt sleeves, hands, window glass, clock dial, the open cupboard's lit interior, the memo slip, the SERVICE card and tag, and the balloons: balloons are reserved paper ovals with tails, no outline",
            "every word cut in the indigo stencil from the shared pen hand's strokes (thickened, as page 08's cut letters) and printed on reserved paper; TICKET OFFICE reserved out of the indigo window board",
            "the ANRC 1922 key cutout used as the vermilion key stencil on the reserved interior of the open cupboard",
            "panels have no frame line: each is a vermilion wall field over an indigo floor, with a band of bare paper at its head for the caption",
            "folio '87 / Two-colour stencil' (pen99.folio, the book's shared pen line in the margin band, the only non-stencil mark)",
        ],
        "events": {
            "E0": "P1: the memo slip on the desk ('4:15 - open SERVICE door. Key in cupboard.'); he sets off past the closed cupboard toward the SERVICE door",
            "E1": "P2: the lady behind the TICKET OFFICE glass; the question",
            "E2": "P3: the wall clock at 4:10; the answer",
            "E3": "P4: she turns away; the thanks",
            "E4": "P5: the cupboard open, the key on its hook, tagged SERVICE",
            "E5": "P6: pencil to his chin, the forgetting line; key on its hook, SERVICE door shut",
        },
        "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
                  "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
        "substitutions": "none",
        "beat": "the page printed: the vermilion stencil dabbed down the sheet, then the indigo stencil over it, and only with the second dye do the figures, words and furniture appear",
        "beat_frames": ["b01: the bare 1934 sheet", "b02: vermilion dabbed over the top half", "b03: vermilion complete (walls, coat, key, pencil; reserved shapes blank)",
                        "b04: indigo over the top third", "b05: indigo over two thirds", "b06: indigo complete (the page)"],
        "self_check": {
            "size_px": [W, H], "jpeg_bytes": size, "jpeg_quality": 90, "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
            "dyes": ["vermilion", "indigo"], "drawn_outlines": 0,
            "ink_colour_clusters_measured": colours,
            "check": "A reader counts two ink colours and finds no drawn outline: structurally, the page is the sheet times two dye layers and nothing else (no border_mask, no balloon_piece, no ink_onto) before the folio; the measured colour clusters of the inked pixels are vermilion, indigo and their overprint",
            "evidence": "structural (build) + perceptually judged from the full page by the maker; blind reading pending",
        },
    }
    B.write_record(rec)
    B.credit_pages(rec["sources"], N)
    return rec


def measure(img, PV, PI):
    """mean colour of pixels printed by V only, I only, both (excluding the folio band)"""
    v, i = PV[:2730] > 127, PI[:2730] > 127
    im = img[:2730].astype(np.float32)
    out = {}
    for name, m in (("vermilion_only", v & ~i), ("indigo_only", i & ~v), ("overprint", v & i)):
        out[name] = [int(x) for x in im[m].mean(0)] if m.any() else None
    return out


if __name__ == "__main__":
    PV, PI = masks()
    page = print_page(PV, PI)
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    rec = record(size, measure(img, PV, PI))
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        fr = []
        for fv, fi in [(0, 0), (0.5, 0), (1, 0), (1, 0.34), (1, 0.67)]:
            p = np.clip(np.round(print_page(PV, PI, fv, fi)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            fr.append(cv2.resize(p, (960, 1242), interpolation=cv2.INTER_AREA))
        fr.append(cv2.resize(img, (960, 1242), interpolation=cv2.INTER_AREA))
        print("beats", B.save_beats(N, fr))
