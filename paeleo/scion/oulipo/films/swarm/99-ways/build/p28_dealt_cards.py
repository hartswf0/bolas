"""Page 28 Dealt cards (layout and page grammar; medium: paper-hands).

Seven lit paper cards dealt one on another across the felt board of the 99-ways-subjective lightbox:
each card a first-person view (the agent's own scissor-cut paper hands, sleeve and cuff, from the
99-ways-subjective RightHand rig; set pieces cut sharp against the lit sheet), each later beat laid
partly over the one before, the last (the forgetting) uncovered.
Reused HANDMADE code (imported, not copied): 99-ways-subjective/test-shot-build/lightbox.py (lit fibrous
paper sheet, felt board, scissor facets) and e4.py (RightHand pieces); b1m2 (stranger bust, clock, ANRC key
cutout); pen99/penlib (shared pen hand, cut-paper balloons).
Run: python3 -I p28_dealt_cards.py [beats]
"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
SUBJ = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-subjective/test-shot-build"
sys.path.insert(0, SUBJ)
from b1m2 import *  # noqa
import lightbox as lb  # noqa: E402
import e4  # noqa: E402
from lightbox import facet, dense_poly, capsule_pts, ellipse_pts, xf  # noqa: E402

N, PID, TITLE = 28, "dealt-cards", "Dealt cards"
CW, CH = 1100, 800            # card model size (hand rig units)
CS = 0.86                     # card model -> page scale (card on page 946 x 688)
SILK = lb.SIL_K
VELLUM = lb.VELLUM


# ------------------------------------------------------------------ grounds
def lit_paper(seed):
    """One lamp-lit fibrous sheet (lightbox.make_page restricted to one window of the card's size)."""
    saved = (lb.PAGE_W, lb.PAGE_H, lb.PANELS)
    lb.PAGE_W, lb.PAGE_H, lb.PANELS = CW, CH, {1: (0, 0, CW, CH)}
    try:
        p = lb.make_page(seed)
    finally:
        lb.PAGE_W, lb.PAGE_H, lb.PANELS = saved
    return p


def felt():
    """The felt board (lightbox.make_page with no windows) laid on the LoC 1934 sheet inside the live area."""
    saved = (lb.PAGE_W, lb.PAGE_H, lb.PANELS)
    lb.PAGE_W, lb.PAGE_H, lb.PANELS = W, H, {}
    try:
        f = lb.make_page(2801)
    finally:
        lb.PAGE_W, lb.PAGE_H, lb.PANELS = saved
    page = pen99.sheet99()
    x0, y0, x1, y1 = BOARD
    q = facet(dense_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 3.0), 2802, 8, 14, 0.8)
    a = np.zeros((H, W), np.uint8)
    cv2.fillPoly(a, [np.int32(q * 4)], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(page, a, off=7, blur=6, opacity=0.45)
    af = a.astype(np.float32)[..., None] / 255
    return page * (1 - af) + f * af


# ------------------------------------------------------------------ card drawing helpers (card-local coords)
HS = 0.62


class Card:
    def __init__(self, seed):
        self.paper = lit_paper(seed)
        self.R = lb.Raster(0, 0, CW, CH)
        self.set = self.R.blank()          # sharp set pieces against the sheet
        self.hands = self.R.blank()        # the agent's hands (behind the sheet: soft)
        self.far = self.R.blank()          # held back beyond glass: soft grey
        self.light = []                    # (mask, gain) brighter patches (lit interiors)
        self.post = []                     # callables(rgb) after silhouettes (slips, balloons)
        self.seed = seed

    def poly(self, pts, v=1.0, layer="set", cut=True, s=0):
        P = facet(dense_poly(pts, 3.0), self.seed + s) if cut else np.asarray(pts, float)
        self.R.fill(getattr(self, layer), P, v)

    def rect(self, x0, y0, x1, y1, v=1.0, layer="set", s=0):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], v, layer, s=s)

    def shapes(self, shapes, layer="set", holes=True):
        m = raster(shapes, CW, CH, holes=holes).astype(np.float32) / 255
        L = getattr(self, layer)
        L[:] = np.maximum(L, m) if layer != "set" else L * (1 - m) + m

    def hand(self, target, h_deg, pencil=None, scale=HS):
        """RightHand (99-ways-subjective e4) posed with its pinch on target; pencil = length held in the pinch.
        Drawn on a 1/scale canvas (the rig's own units) and reduced, so the paper hand keeps its cut facets."""
        rh = RH
        h = math.radians(h_deg)
        Rm = np.array([[math.cos(h), -math.sin(h)], [math.sin(h), math.cos(h)]])
        target = np.asarray(target, float)
        tb = target / scale
        P = dict(h=h, R=Rm, wrist=tb - Rm @ rh.PINCH, idx_w=tb, th_w=tb + Rm @ np.array([-4.0, -12.0]),
                 lift=0.15, contact=True)
        e4.O[:] = 0
        Rb = lb.Raster(0, 0, int(CW / scale), int(CH / scale))
        D, pins, info = rh.draw(Rb, P, tb)
        D = cv2.resize(D, (CW, CH), interpolation=cv2.INTER_AREA)
        self.hands[:] = np.maximum(self.hands, D)
        if pencil:
            # the pencil: a cut bar through the pinch, pointing along the fingers and a little across
            d = Rm @ np.array([math.cos(math.radians(-30)), math.sin(math.radians(-30))])
            a, b = target - d * 30 * scale, target + d * pencil
            nrm = np.array([-d[1], d[0]]) * 6
            self.R.fill(self.hands, facet(dense_poly([a + nrm, b + nrm * 0.6, b + d * 22, b - nrm * 0.6, a - nrm]), self.seed + 77))
        return info

    def slip(self, x0, y0, lines, cap, seed, tilt=0.0, paper=None):
        self.post.append(lambda rgb: slip(rgb, x0, y0, lines, cap, seed, paper=VELLUM if paper is None else paper,
                                          pad=(18, 10), tilt=tilt, shadow=0.35))

    def balloon(self, lines, cap, at, tip, seed, tail_w=0.26):
        self.post.append(lambda rgb: balloon(rgb, lines, cap, at, tip, seed, tail_w=tail_w))

    def cut_letters(self, text, cap, cx, cy, seed):
        """Letters cut out of a dark board: light shows through them."""
        m = np.zeros((CH, CW), np.uint8)
        put_mask(m, letter([text], cap, seed, weight=0.17), cx, cy)
        self.set[:] = self.set * (1 - m.astype(np.float32) / 255)

    def render(self):
        rgb = self.paper.copy()
        for m, g in self.light:
            mm = cv2.GaussianBlur(m, (0, 0), 5)
            rgb = np.minimum(rgb * (1 + g * mm[..., None]), 253)
        paper = rgb.copy()
        # hands behind the sheet: soft body + penumbra offset (lightbox.composite's hand model)
        D = self.hands
        body = cv2.GaussianBlur(D, (0, 0), 1.9)
        sh = cv2.warpAffine(D, np.float32([[1, 0, 5], [0, 1, 4]]), (CW, CH))
        pen = cv2.GaussianBlur(sh, (0, 0), 1.9 * 2.2 + 2) * 0.42
        Dt = np.maximum(body, pen)
        F = cv2.GaussianBlur(self.far, (0, 0), 3.0) * 0.62
        rgb = rgb * (1 - (1 - SILK) * F[..., None])
        sd = cv2.GaussianBlur(self.set, (0, 0), 0.6)
        rgb = rgb * (1 - sd[..., None]) + (paper * SILK) * sd[..., None]
        for f in self.post:          # slips and balloons, then the hands over them (they hold the memo)
            f(rgb)
        rgb = rgb * (1 - (1 - SILK) * Dt[..., None])
        return rgb


RH = e4.RightHand()


def key_on_hook(c, kx, ky, scale, seed):
    """ANRC 1922 key cutout as a sharp silhouette with brass light inside, on a cut hook; SERVICE tag."""
    a = key_alpha()
    h, w = a.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, scale)
    M[0, 2] += kx - w / 2
    M[1, 2] += ky - h / 2
    A = cv2.warpAffine(a, M, (CW, CH)).astype(np.float32) / 255
    c.set[:] = np.maximum(c.set, A)
    top = ky - h * scale / 2
    c.poly([(kx - 26, top - 12), (kx + 4, top - 12), (kx + 4, top + 22), (kx - 4, top + 22), (kx - 4, top - 4), (kx - 26, top - 4)], s=seed)
    c.slip(int(kx + 16), int(ky + h * scale * 0.18), ["SERVICE"], 24, seed + 1, tilt=9)


def window_set(c, x0, y0, w, h, seed, header=74):
    """Ticket window seen from inside: header board with TICKET OFFICE cut through, posts, glazing bars, counter."""
    sill = y0 + h * 0.70
    c.rect(x0 - 30, y0, x0 + w + 30, y0 + header, s=seed)
    c.rect(x0 - 30, y0, x0, sill, s=seed + 1)
    c.rect(x0 + w, y0, x0 + w + 30, sill, s=seed + 2)
    c.rect(x0 + w / 2 - 7, y0 + header, x0 + w / 2 + 7, sill, s=seed + 3)
    c.rect(x0, y0 + header + (sill - y0 - header) * 0.45, x0 + w, y0 + header + (sill - y0 - header) * 0.45 + 12, s=seed + 4)
    c.rect(x0 - 70, sill, x0 + w + 70, sill + 30, s=seed + 5)
    c.rect(x0 - 50, sill + 30, x0 + w + 50, CH + 10, s=seed + 6)
    c.cut_letters("TICKET OFFICE", 38, x0 + w / 2, y0 + header / 2 + 2, seed + 7)
    return sill


def cupboard_set(c, x0, y0, w, h, open_=False, seed=0):
    c.rect(x0 - 18, y0 - 34, x0 + w + 18, y0, s=seed)
    if not open_:
        c.rect(x0, y0, x0 + w, y0 + h, s=seed + 1)
        for (a, b) in ((0.08, 0.46), (0.54, 0.92)):
            m = np.zeros((CH, CW), np.float32)
            c.R.fill(m, facet(dense_poly([(x0 + w * .18, y0 + h * a), (x0 + w * .82, y0 + h * a), (x0 + w * .82, y0 + h * b),
                                         (x0 + w * .18, y0 + h * b)]), seed + 2))
            inner = cv2.erode(m, np.ones((11, 11), np.uint8))
            c.set[:] = c.set * (1 - (m - inner))
        c.R.fill(c.set, ellipse_pts(x0 + w * 0.9, y0 + h * 0.5, 9, 9), 0.0)
        return None
    # open: case jambs, top, base, shelves; lit interior; leaf swung on the left jamb toward us
    c.rect(x0, y0, x0 + 22, y0 + h, s=seed + 1)
    c.rect(x0 + w - 22, y0, x0 + w, y0 + h, s=seed + 2)
    c.rect(x0, y0 + h - 26, x0 + w, y0 + h, s=seed + 3)
    for fy in (0.30, 0.70):
        c.rect(x0 + 22, y0 + h * fy, x0 + w - 22, y0 + h * fy + 14, s=seed + 4 + int(fy * 10))
    lm = np.zeros((CH, CW), np.float32)
    lm[int(y0):int(y0 + h), int(x0 + 22):int(x0 + w - 22)] = 1
    c.light.append((lm, 0.10))
    leaf = [(x0, y0), (x0 - w * 0.42, y0 - 46), (x0 - w * 0.42, y0 + h + 46), (x0, y0 + h)]
    c.poly(leaf, s=seed + 9)
    return (x0 + 22, y0, x0 + w - 22, y0 + h), leaf


def service_door_set(c, x0, y0, w, h, seed):
    c.rect(x0 - 16, y0 - 18, x0 + w + 16, y0 + h, s=seed)
    for (a, b) in ((0.30, 0.56), (0.63, 0.93)):
        m = np.zeros((CH, CW), np.float32)
        c.R.fill(m, facet(dense_poly([(x0 + w * .18, y0 + h * a), (x0 + w * .82, y0 + h * a), (x0 + w * .82, y0 + h * b),
                                     (x0 + w * .18, y0 + h * b)]), seed + 2))
        c.set[:] = c.set * (1 - (m - cv2.erode(m, np.ones((11, 11), np.uint8))))
    c.slip(int(x0 + w * 0.5 - 92), int(y0 + h * 0.12), ["SERVICE"], 36, seed + 3, tilt=0)


# ------------------------------------------------------------------ the seven cards (each a first-person view)
def card1():   # E0 the memo in his hand on the desk
    c = Card(2811)
    c.rect(-10, 640, CW + 10, CH + 10, s=4)
    c.rect(560, 520, 640, 640, s=2)                                  # inkwell
    c.poly([(560, 520), (578, 494), (622, 494), (640, 520)], s=3)
    c.slip(90, 230, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], 46, 2812, tilt=-4)
    c.hand((120, 440), -62)                                           # pinching the slip's lower corner
    return c


def card2():   # E0 he rises and sets off: the cupboard and the SERVICE door ahead
    c = Card(2821)
    c.rect(-10, 700, CW + 10, CH + 10, s=1)                          # floor
    cupboard_set(c, 430, 170, 260, 530, open_=False, seed=10)
    service_door_set(c, 790, 110, 250, 590, 30)
    return c


def card3():   # E1 the question through the ticket window
    c = Card(2831)
    sill = window_set(c, 120, 90, 560, 680, 50)
    far = stranger(410, sill + 40, face=1, scale=1.65, glove=True)
    c.shapes(far, layer="far", holes=False)
    c.balloon(["Pardon me —", "have you the", "right time?"], 48, (850, 190), (500, 300), 2832)
    return c


def card4():   # E2 he looks up at the clock: 4:10; the answer is his own (tail off the bottom edge)
    c = Card(2841)
    c.shapes(clock(760, 250, 150, hh=4, mm=10, swing=4))
    c.hand((640, 610), -112, pencil=120)
    c.balloon(["Ten past four,", "by the clock."], 48, (300, 200), (480, 790), 2842)
    return c


def card5():   # E3 the thanks: she turns from the window and goes
    c = Card(2851)
    sill = window_set(c, 120, 90, 560, 680, 60)
    far = stranger(250, sill + 40, face=-1, scale=1.35, tilt=-6)
    c.shapes(far, layer="far", holes=False)
    c.balloon(["Much", "obliged!"], 50, (870, 210), (330, 330), 2852)
    return c


def card6():   # E4 his hand swings the cupboard leaf open: the key on its hook
    c = Card(2861)
    c.rect(-10, 730, CW + 10, CH + 10, s=1)
    box, leaf = cupboard_set(c, 560, 120, 340, 610, open_=True, seed=70)
    key_on_hook(c, 730, 300, 0.30, 2862)
    c.hand((leaf[1][0] - 6, 236), -58)
    return c


def card7():   # E5 the forgetting: key still on its hook, SERVICE door shut, pencil up to his chin
    c = Card(2871)
    c.rect(-10, 730, CW + 10, CH + 10, s=1)
    box, leaf = cupboard_set(c, 200, 170, 320, 560, open_=True, seed=80)
    key_on_hook(c, 360, 330, 0.30, 2872)
    service_door_set(c, 840, 110, 220, 620, 90)
    c.hand((455, 660), -100, pencil=120)
    c.balloon(["Well, here I am...", "and what for?"], 48, (600, 128), (700, 800), 2873)
    return c


CARDS = [card1, card2, card3, card4, card5, card6, card7]
# dealt positions (centre on page, rotation deg), zigzag down the felt, each over the last
DEAL = [((700, 530), -4.0), ((1420, 830), 3.5), ((760, 1130), -2.5), ((1460, 1430), 4.0),
        ((730, 1730), -3.5), ((1430, 2030), 2.5), ((1080, 2330), -1.5)]
BOARD = (110, 110, 2090, 2730)


def card_rgba(k):
    c = CARDS[k]()
    rgb = c.render()
    rgb = cv2.resize(rgb, (int(CW * CS), int(CH * CS)), interpolation=cv2.INTER_AREA)
    h, w = rgb.shape[:2]
    rnd = random.Random(2890 + k)
    q = [(rnd.uniform(0, 3), rnd.uniform(0, 3)), (w - rnd.uniform(0, 3), rnd.uniform(0, 3)),
         (w - rnd.uniform(0, 3), h - rnd.uniform(0, 3)), (rnd.uniform(0, 3), h - rnd.uniform(0, 3))]
    a = np.zeros((h, w), np.uint8)
    cv2.fillPoly(a, [np.int32(facet(dense_poly(q, 3.0), 2895 + k, 6, 12, 0.5) * 4)], 255, cv2.LINE_AA, shift=2)
    return rgb, a


def lay(page, rgb, a, centre, deg):
    h, w = a.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -deg, 1.0)
    M[0, 2] += centre[0] - w / 2
    M[1, 2] += centre[1] - h / 2
    A = cv2.warpAffine(a, M, (W, H))
    G = cv2.warpAffine(rgb, M, (W, H))
    penlib.shadow_onto(page, A, off=12, blur=10, opacity=0.55)
    af = A.astype(np.float32)[..., None] / 255
    page[:] = page * (1 - af) + G * af
    return A > 127


CACHE = {}


def build(n=7, slide=None):
    """n cards dealt; slide=(k, t): card k still travelling in from the deck at t in [0,1)."""
    page = felt().copy() if "felt" not in CACHE else CACHE["felt"].copy()
    CACHE.setdefault("felt", page.copy())
    masks = []
    for k in range(n):
        if k not in CACHE:
            CACHE[k] = card_rgba(k)
        rgb, a = CACHE[k]
        (cx, cy), deg = DEAL[k]
        if slide is not None and slide[0] == k:
            t = slide[1]
            sx, sy = 2500, 3100           # the deck: off the lower right corner
            cx, cy = sx + (cx - sx) * t, sy + (cy - sy) * t
            deg = deg + (1 - t) * 25
        masks.append(lay(page, rgb, a, (cx, cy), deg))
    return page, masks


def coverage(masks):
    """For each card: fraction hidden by later cards, and by the very next card."""
    out = []
    for k, m in enumerate(masks):
        later = np.zeros_like(m)
        for m2 in masks[k + 1:]:
            later |= m2
        nxt = masks[k + 1] if k + 1 < len(masks) else np.zeros_like(m)
        out.append({"card": k + 1, "hidden_by_later": round(float((m & later).sum() / m.sum()), 3),
                    "covered_by_next": round(float((m & nxt).sum() / m.sum()), 3)})
    return out


if __name__ == "__main__":
    page, masks = build()
    img, size = save_page(page, N, PID, TITLE)
    cov = coverage(masks)
    allm = np.zeros_like(masks[0])
    for m in masks:
        allm |= m
    ys, xs = np.nonzero(allm)
    print("jpeg bytes", size, cov, "bbox", xs.min(), ys.min(), xs.max(), ys.max())
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for st in ((4, None), (5, (4, 0.45)), (5, None), (6, (5, 0.5)), (6, None), (7, (6, 0.5)), (7, None)):
            p, _ = build(*st)
            p = np.clip(np.round(p), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)
