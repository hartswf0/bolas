"""99 ways, page 41 "The case of the closed door" (genre; medium: photo-cutout).

A detective arrives at 4:30 and reconstructs the forgetting from three clues: the memo, the clock, the open cupboard.
Photo-cutout grammar (pages 01, 10, 27): prints cut with a white scissor margin, laid on the LoC 1934 sheet, with
cut-paper balloons and pasted slips in the shared pen hand.
- 4:30, the scene: the 99-ways-template rest layers of P8 with the agent's layers left out (the office as he left it:
  cupboard open, the ANRC 1922 key on its hook with its SERVICE tag, the SERVICE door shut under its card), printed in
  a cold neutral grey; the detective = the Agence Rol 49112 man in overcoat and bowler (1917, cut out by
  exercices-de-style), standing at the print's edge; his card (HANDMADE) names him: Det. Pruett, railway police.
- three clue prints, each pinned with a HANDMADE yellow evidence tag and a note slip in his voice: CLUE 1 the memo
  (P2 layers, the desk without the agent); CLUE 2 the clock (P5 plate without agent and clock, the LoC clock pieces
  re-cut onto it with their own hands re-set on the arbor to 4:30); CLUE 3 the open cupboard (P7 layers without the
  agent) under a HANDMADE cut-paper magnifying glass whose lens enlarges the key.
- the reconstruction: the page-01 rest panels P1 P4 P5 P6 P7 P8 (with the agent) printed small in warm sepia, each
  with its time slip, the four canon lines lettered afresh in the balloons; a CASE CLOSED slip ends it.
Declared: E0-E5 are framed as a reconstruction after the fact; the agent is not in the office at 4:30 (where he went
is not told); the detective, his card, his lines and the clue notes are added.
Run: python3 -I p41_the_case.py [--page-only]"""
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image

KIT = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit"
sys.path.insert(0, KIT)
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
import build_page01 as b01  # noqa: E402
import build_page04 as K  # noqa: E402  (paste, affine, slip, man)
from cutpaper99 import hexc  # noqa: E402
import b1m2 as B  # noqa: E402

N, PID = 41, "the-case"
W, H = pen99.PAGE_W, pen99.PAGE_H
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
TITLE = C["title"]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
REST = b01.REST
OLD = b01.OLD
PCS = ROOT / "films/sources/99-ways-template/page-cartoonist/pieces"
MAN = json.load(open(PCS / "manifest.json"))

INK = hexc("#121110")
PRINT_W = hexc("#f7f5ef")
TAG = hexc("#efd47e")
CARD = hexc("#f4efe2")
SLIPC = hexc("#fbf8ef")
SEPIA_LO, SEPIA_HI = hexc("#2a1d12"), hexc("#f3e6cc")
GREY_LO, GREY_HI = hexc("#141518"), hexc("#eef0ef")

Q = ["Pardon", "me — have", "you the right", "time?"]
A = ["Ten past", "four, by the", "clock."]
T = ["Much", "obliged!"]
F = ["Well,", "here I am... and", "what for?"]
assert " ".join(Q) == LN["question"] and " ".join(A) == LN["answer"] and " ".join(T) == LN["thanks"]
assert " ".join(F) == LN["forgetting"]


# ------------------------------------------------------------------ material
def rest(key, skip=()):
    """a rest panel recomposed from its layers; balloons, border and any layer whose name starts with skip left out"""
    c, used = None, []
    for r in json.load(open(REST / key / "layers.json"))["layers"]:
        n = r["name"]
        if n.startswith("b_") or n == "border" or any(n.startswith(s) for s in skip):
            continue
        im = np.asarray(Image.open(REST / key / r["file"])).astype(np.float32)
        if c is None:
            c = im[..., :3].copy()
        else:
            a = im[..., 3:4] / 255
            c = c * (1 - a) + im[..., :3] * a
        used.append(n)
    return c, used


def tone(c, lo, hi, gamma=1.0):
    L = np.clip(c.mean(axis=2) / 255.0, 0, 1) ** gamma
    return lo + (hi - lo) * L[..., None]


def clock_at(h, m):
    """the LoC office clock (page-cartoonist pieces), its own hands re-set on the arbor; rgb float, alpha uint8"""
    case = np.asarray(Image.open(PCS / "clock.case.png")).astype(np.float32)
    g = case[..., :3].mean(axis=2)
    a = case[..., 3].copy()
    arb = MAN["pieces"]["clock.case"]["pivots_local"]["arbor"]
    hh, ww = g.shape
    for n, ang in (("clock.hour", (h % 12) * 30 + m * 0.5), ("clock.minute", m * 6.0)):
        im = np.asarray(Image.open(PCS / f"{n}.png")).astype(np.float32)
        p = MAN["pieces"][n]
        piv = p["pivots_local"]["arbor"]
        rot = ang - p["source_angle_deg"]
        M = cv2.getRotationMatrix2D((float(piv[0]), float(piv[1])), -rot, 1.0)
        M[0, 2] += arb[0] - piv[0]
        M[1, 2] += arb[1] - piv[1]
        hg = cv2.warpAffine(im[..., :3].mean(axis=2), M, (ww, hh), flags=cv2.INTER_CUBIC)
        ha = cv2.warpAffine(im[..., 3], M, (ww, hh), flags=cv2.INTER_LINEAR) / 255
        g = g * (1 - ha) + hg * ha
    return np.repeat(g[..., None], 3, 2), a.astype(np.uint8)


def clue2_plate():
    """P5 without the agent and its clock; the clock re-cut onto it at 4:30 where the old one hung"""
    c, used = rest("P5", skip=("clerk", "clock"))
    g, a = clock_at(4, 30)
    # the old case's bbox in P5: x 732-958, y 87-455 (read from its layer's alpha)
    s = (958 - 732) / g.shape[1]
    gs = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    as_ = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
    x0, y0 = 732, 87
    hh, ww = gs.shape[:2]
    sh = np.zeros(c.shape[:2], np.uint8)
    sh[y0 + 6:y0 + 6 + hh, x0 + 5:x0 + 5 + ww] = (as_[..., 0] * 255).astype(np.uint8)
    s_ = cv2.GaussianBlur(sh, (0, 0), 5).astype(np.float32)[..., None] / 255 * 0.45
    c *= (1 - s_)
    c[y0:y0 + hh, x0:x0 + ww] = c[y0:y0 + hh, x0:x0 + ww] * (1 - as_) + gs * as_
    return c, used + ["clock re-set to 4:30 (page-cartoonist clock.case, clock.hour, clock.minute)"]


# ------------------------------------------------------------------ page tools
def print_piece(img, c, centre, scale, deg, margin=16, shadow=0.35):
    """lay a photo as a cut print: white scissor margin, its shadow; returns the 2x3 matrix (print px -> page)"""
    h, w = c.shape[:2]
    M = K.affine(centre[0], centre[1], scale, deg, w, h)
    a = np.full((h, w), 255, np.uint8)
    K.paste(img, c, a, M, margin=margin, margin_col=PRINT_W, sh=True, op=shadow)
    # a thin ink edge round the photo, as on page 27
    box = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
    pts = cv2.transform(box[None], M)[0]
    m = np.zeros((H, W), np.uint8)
    cv2.polylines(m, [np.int32(pts * 4)], True, 255, 3, cv2.LINE_AA, shift=2)
    penlib.ink_onto(img, m, INK, 0.55)
    return M


def tf(M, p):
    return (M[0, 0] * p[0] + M[0, 1] * p[1] + M[0, 2], M[1, 0] * p[0] + M[1, 1] * p[1] + M[1, 2])


def balloon(img, lines, cap, centre, tip, seed, box=None):
    """cut-paper balloon; its centre moved only as far as needed to keep it inside box (x0, y0, x1, y1)"""
    lines = [pen99.clean(l) for l in lines]
    while True:   # shrink the lettering until the balloon fits its box (no letter cut by a print edge)
        let = pen99.letter(lines, cap, seed + 1)
        rx = let.shape[1] * 0.5 * 1.18 + cap * 0.35 + 10
        ry = let.shape[0] * 0.5 * 1.10 + cap * 0.30 + 10
        if box is None or 2 * rx <= box[2] - box[0] or cap <= 24:
            break
        cap -= 1
    cx, cy = centre
    if box is not None:
        cx = float(np.clip(cx, box[0] + rx, box[2] - rx))
        cy = float(np.clip(cy, box[1] + ry, box[3] - ry))
    b = penlib.balloon_piece(lines, cap, (tip[0] - cx, tip[1] - cy), seed, tail_w=0.22, bend=0.09)
    penlib.lay_balloon(img, b, (cx, cy))


def card(img, lines, cap, x, y, seed, deg=0.0, colour=SLIPC, w=0, weight=0.13, pad=0.55):
    """a cut card at top-left (x, y), pen lettering; returns its size"""
    let = pen99.letter(lines, cap, seed, weight=weight)
    lh, lw = let.shape
    hh = lh + int(cap * pad * 2)
    ww = max(w, lw + int(cap * 1.0))
    rgb = np.zeros((hh, ww, 3), np.float32) + colour
    a = np.zeros((hh, ww), np.uint8)
    pts = np.array([(3, 5), (ww - 3, 2), (ww - 4, hh - 4), (2, hh - 2)], np.int32)
    cv2.fillPoly(a, [pts], 255)
    ox, oy = (ww - lw) // 2 if w == 0 else int(cap * 0.5), (hh - lh) // 2
    L = np.zeros((hh, ww), np.uint8)
    L[oy:oy + lh, ox:ox + lw] = let
    rgb = rgb * (1 - L[..., None] / 255.0) + INK * (L[..., None] / 255.0)
    M = K.affine(x + ww / 2, y + hh / 2, 1.0, deg, ww, hh)
    K.paste(img, rgb, a, M, sh=True, op=0.3)
    return ww, hh


def evidence_tag(img, n, at, deg, seed, pin_to=None):
    """HANDMADE yellow evidence tag: notched card, punched hole, string to the print, 'CLUE n'"""
    x, y = at
    let = pen99.letter([f"CLUE {n}"], 40, seed, weight=0.19)
    lh, lw = let.shape
    hh, ww = lh + 30, lw + 70
    rgb = np.zeros((hh, ww, 3), np.float32) + TAG
    a = np.zeros((hh, ww), np.uint8)
    pts = np.array([(18, 2), (ww - 2, 3), (ww - 3, hh - 2), (18, hh - 3), (2, hh // 2)], np.int32)
    cv2.fillPoly(a, [pts], 255, cv2.LINE_AA)
    cv2.circle(a, (20, hh // 2), 7, 0, -1, cv2.LINE_AA)          # the punched hole
    L = np.zeros((hh, ww), np.uint8)
    L[15:15 + lh, 44:44 + lw] = let
    rgb = rgb * (1 - L[..., None] / 255.0) + INK * (L[..., None] / 255.0)
    M = K.affine(x + ww / 2, y + hh / 2, 1.0, deg, ww, hh)
    K.paste(img, rgb, a, M, sh=True, op=0.35)
    hole = tf(M, (20, hh // 2))
    if pin_to == "hole":   # pinned through its own hole onto the print
        pm = np.zeros((H, W), np.uint8)
        cv2.circle(pm, (int(hole[0]), int(hole[1])), 10, 255, -1, cv2.LINE_AA)
        K.shadow(img, pm, off=(3, 4), blur=2, op=0.4)
        penlib.ink_onto(img, pm, hexc("#9b2a1c"), 1.0)
    elif pin_to is not None:   # the string, from the hole to a pin on the print
        m = np.zeros((H, W), np.uint8)
        mid = ((hole[0] + pin_to[0]) / 2 - 10, (hole[1] + pin_to[1]) / 2 + 18)
        pts = [(hole[0] * (1 - t) ** 2 + 2 * mid[0] * t * (1 - t) + pin_to[0] * t * t,
                hole[1] * (1 - t) ** 2 + 2 * mid[1] * t * (1 - t) + pin_to[1] * t * t) for t in np.linspace(0, 1, 30)]
        cv2.polylines(m, [np.int32(np.array(pts) * 4)], False, 255, 3, cv2.LINE_AA, shift=2)
        penlib.ink_onto(img, m, hexc("#7a5a3a"), 0.9)
        pm = np.zeros((H, W), np.uint8)
        cv2.circle(pm, (int(pin_to[0]), int(pin_to[1])), 9, 255, -1, cv2.LINE_AA)
        K.shadow(img, pm, off=(3, 4), blur=2, op=0.4)
        penlib.ink_onto(img, pm, hexc("#9b2a1c"), 1.0)


def magnifier(img, centre, r, handle_deg, zoom=1.8):
    """HANDMADE cut-paper reading glass: the lens enlarges what lies under it; dark card ring, card handle"""
    cx, cy = centre
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # handle first (under the ring)
    ang = math.radians(handle_deg)
    p0 = (cx + math.cos(ang) * (r + 8), cy + math.sin(ang) * (r + 8))
    p1 = (cx + math.cos(ang) * (r + 230), cy + math.sin(ang) * (r + 230))
    nx, ny = -math.sin(ang), math.cos(ang)
    hw0, hw1 = 15, 22
    poly = [(p0[0] + nx * hw0, p0[1] + ny * hw0), (p1[0] + nx * hw1, p1[1] + ny * hw1),
            (p1[0] - nx * hw1, p1[1] - ny * hw1), (p0[0] - nx * hw0, p0[1] - ny * hw0)]
    hm = np.zeros((H, W), np.uint8)
    cv2.fillPoly(hm, [np.int32(np.array(poly) * 4)], 255, cv2.LINE_AA, shift=2)
    K.shadow(img, hm, off=(10, 13), blur=7, op=0.4)
    ha = hm.astype(np.float32)[..., None] / 255
    grain = (np.sin(xx * 0.9 + yy * 0.25) * 6)[..., None]
    img[:] = img * (1 - ha) + (hexc("#5b3a22") + grain) * ha
    # the lens: what lies under it, enlarged
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    src = img.copy()
    mapx = (cx + (xx - cx) / zoom).astype(np.float32)
    mapy = (cy + (yy - cy) / zoom).astype(np.float32)
    mag = cv2.remap(src, mapx, mapy, cv2.INTER_CUBIC)
    lens = np.clip(r - d, 0, 1.5)[..., None] / 1.5
    img[:] = img * (1 - lens) + (mag * 0.97 + 6) * lens
    # a faint glint
    gl = np.exp(-(((xx - (cx - r * 0.45)) / (r * 0.22)) ** 2 + ((yy - (cy - r * 0.5)) / (r * 0.10)) ** 2))
    img[:] = img + (255 - img) * (gl[..., None] * 0.35)
    # the ring: a dark card annulus with a paper shadow
    ring = ((d < r + 15) & (d > r - 3)).astype(np.uint8) * 255
    ring = cv2.GaussianBlur(ring, (0, 0), 0.7)
    K.shadow(img, ring, off=(9, 12), blur=6, op=0.45)
    ra = ring.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - ra) + hexc("#26211d") * ra


# ------------------------------------------------------------------ the page
RECON = [  # key, crop (x0, y0, x1, y1) in panel px, time slip, balloon (lines, cap, centre_old, tip_old)
    ("P1", (0, 250, 740, 920), "4:09", None),
    ("P4", (0, 0, 560, 700), "4:09:50", (Q, 34, OLD["P4"][0]["centre_panel_px"], OLD["P4"][0]["tail_tip_panel_px"])),
    ("P5", (0, 0, 970, 800), "4:10", (A, 34, OLD["P5"][0]["centre_panel_px"], OLD["P5"][0]["tail_tip_panel_px"])),
    ("P6", (0, 0, 600, 700), "4:10:10", (T, 38, OLD["P6"][0]["centre_panel_px"], OLD["P6"][0]["tail_tip_panel_px"])),
    ("P7", (0, 100, 1000, 980), "4:10:40", None),
    ("P8", (100, 0, 1190, 980), "4:11", (F, 34, OLD["P8"][0]["centre_panel_px"], OLD["P8"][0]["tail_tip_panel_px"])),
]
CELL_W, CELL_H = 610, 420
CELL_C = [(430, 1935), (1100, 1935), (1770, 1935), (430, 2393), (1100, 2393), (1770, 2393)]
CELL_DEG = [-1.5, 1.2, -0.8, 1.0, -1.4, 0.9]

NOTES = [
    ["The memo. '4:15 - open SERVICE", "door. Key in cupboard.' He knew", "his errand, and he got up to do it."],
    ["The clock. It faces the ticket window.", "Somebody at the glass asked the time;", "he looked up: ten past four."],
    ["The cupboard. Open, and the key", "in plain view on its hook, never", "touched. He got this far."],
]


def build(stage=9):
    """stage: 1 scene, 2-4 + clues 1..3, 5 + magnifier, 6 + reconstruction row 1, 7 + row 2, 8 + case closed"""
    img = pen99.sheet99().astype(np.float32)
    used = {}
    # the header slip
    card(img, ["4:30 p.m. Detective Pruett of the railway police is called to Randolph:",
               "the SERVICE door, due to be opened at 4:15, is still shut."], 36, 150, 112, 4101, deg=-0.4)
    # 4:30, the scene: P8 without the agent, neutral grey
    c, u = rest("P8", skip=("clerk",))
    used["scene"] = u
    c = tone(c, GREY_LO, GREY_HI)
    Ms = print_piece(img, c, (650, 640), 0.76, 1.2)
    # the detective (Rol 49112), standing at the print's right edge
    g, a = K.man()
    Md = K.affine(1330, 668, 0.445, -1.0, g.shape[1], g.shape[0])
    K.paste(img, tone(g, GREY_LO + 4, GREY_HI), a, Md, margin=10, margin_col=PRINT_W, sh=True, op=0.4)
    mouth = tf(Md, (430, 470))
    # his card
    card(img, ["DET. H. PRUETT", "Central Vermont Ry.", "police"], 34, 1640, 820, 4102, deg=3.0, colour=CARD, weight=0.15)
    balloon(img, ["The key's still", "on its hook. Nobody", "stole it. Let the", "room tell me why."], 38,
            (1840, 420), (mouth[0] + 18, mouth[1] - 6), 4103, box=(1580, 250, 2090, 790))
    if stage >= 2:
        # CLUE 1 the memo: P2 layers (the desk, the agent gone)
        c1, u = rest("P2", skip=("clerk",))
        used["clue1"] = u
        c1 = tone(c1[540:940, 0:660], GREY_LO, GREY_HI)
        M1 = print_piece(img, c1, (420, 1235), 0.70, -1.6)
        evidence_tag(img, 1, (130, 1040), -4, 4111, pin_to="hole")
        card(img, NOTES[0], 27, 130, 1395, 4112, deg=0.8, w=580)
    if stage >= 3:
        c2, u = clue2_plate()
        used["clue2"] = u
        c2 = tone(c2[0:560, 560:970], GREY_LO, GREY_HI)
        M2 = print_piece(img, c2, (1100, 1225), 0.62, 1.4)
        evidence_tag(img, 2, (880, 1036), 3, 4121, pin_to="hole")
        card(img, NOTES[1], 27, 790, 1405, 4122, deg=-1.0, w=640)
    if stage >= 4:
        c3, u = rest("P7", skip=("clerk",))
        used["clue3"] = u
        c3 = tone(c3[120:820, 0:760], GREY_LO, GREY_HI)
        M3 = print_piece(img, c3, (1760, 1228), 0.46, -1.8)
        evidence_tag(img, 3, (1540, 1034), -3, 4131, pin_to="hole")
        card(img, NOTES[2], 27, 1490, 1400, 4132, deg=0.7, w=580)
        CHECK["key_on_clue3"] = tf(M3, (200, 450))
    if stage >= 5:
        kx, ky = tf(M3, (200, 455))
        magnifier(img, (kx + 4, ky - 6), 84, 18, zoom=1.75)
    if stage >= 6:
        m = pen99.letter(["RECONSTRUCTION, as Pruett tells it: 4:09 to 4:11"], 40, 4140, weight=0.15)
        K.ink_at(img, m, 115, 1600, INK)
        rows = 3 if stage == 6 else 6
        for i, (key, (x0, y0, x1, y1), tm, bal) in enumerate(RECON[:rows]):
            c, u = b01.panel_rest(key)
            used[f"recon_{key}"] = u
            c = c[y0:y1, x0:x1].copy()
            s = min(CELL_W / c.shape[1], CELL_H / c.shape[0])
            c = cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            c = tone(c, SEPIA_LO, SEPIA_HI, 0.95)
            if bal is not None:
                lines, cap, ctr, tip = bal
                ctr_p = ((ctr[0] - x0) * s, (ctr[1] - y0) * s)
                tip_p = ((tip[0] - x0) * s, (tip[1] - y0) * s)
                balloon(c, lines, cap, ctr_p, tip_p, 4150 + i * 7, box=(4, 4, c.shape[1] - 4, c.shape[0] - 4))
            Mr = print_piece(img, c, CELL_C[i], 1.0, CELL_DEG[i], margin=12, shadow=0.3)
            tx, ty = tf(Mr, (c.shape[1], 0)) if key != "P7" else tf(Mr, (130, 0))
            card(img, [tm], 28, tx - 130, ty - 50, 4160 + i, deg=-3, colour=TAG, weight=0.17)
    if stage >= 8:
        card(img, ["CASE CLOSED. No thief, no lock: the key never", "left its hook. He forgot.   - H.P."], 30,
             1010, 2622, 4170, deg=-1.2, colour=TAG, weight=0.16)
    return img, used


CHECK = {}


def main():
    page, used = build(9)
    page, size = B.save_page(page, N, PID, TITLE)
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    frames = []
    for st in (1, 2, 3, 4, 5, 6, 7):
        im, _ = build(st)
        pen99.folio(im, N, TITLE)
        frames.append(im)
    frames.append(page)
    nb = B.save_beats(N, frames)
    src = ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
           "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934",
           "exercices-de-style:rol-49112-homme-pardessus-1917", "99-ways:handmade"]
    B.credit_pages(src, N)
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}", "build": "films/swarm/99-ways/build/p41_the_case.py",
        "sources": src,
        "made": [
            "4:30, the scene: the 99-ways-template rest layers of P8 recomposed with the agent's layers left out (open cupboard, key on its hook with its SERVICE tag, the SERVICE door shut under its card), printed in cold neutral grey as a cut print with a white scissor margin",
            "the detective = the Agence Rol 49112 man in overcoat and bowler (1917; the exercices-de-style cutout, forage/man_rgba.png) laid at the print's edge with a white scissor margin; a HANDMADE card names him 'DET. H. PRUETT, Central Vermont Ry. police'; his balloon",
            "CLUE 1 the memo: P2 rest layers without the agent (the desk, the memo slip); CLUE 2 the clock: the P5 plate without agent or clock, the LoC clock case re-cut onto it with its own hour and minute hands re-set on the arbor to 4:30; CLUE 3 the open cupboard: P7 rest layers without the agent",
            "HANDMADE yellow evidence tags (notched card, punched hole, string to a red pin), one per clue, lettered CLUE 1-3; three note slips in the detective's voice",
            "a HANDMADE cut-paper reading glass (dark card ring, brown card handle, paper shadow) whose lens enlarges the key and tag lying under it on CLUE 3",
            "the reconstruction: the page-01 rest panels P1 P4 P5 P6 P7 P8 (Rothstein agent, clock, ANRC key) cropped, printed small in warm sepia with time slips 4:09 ... 4:11; the four canon lines lettered afresh in cut-paper balloons",
            "header slip, CASE CLOSED slip, all lettering in the shared pen hand; folio '41 / The case of the closed door' (pen99.folio)"],
        "detective": "Det. H. Pruett, Central Vermont Ry. police (named on his card, in the header slip and the reconstruction label)",
        "clues": ["CLUE 1 the memo", "CLUE 2 the clock (at 4:30 on the page; the note gives ten past four)", "CLUE 3 the open cupboard (the key on its hook, under the glass)"],
        "events": {
            "E0": "reconstruction 4:09 (P1): at the desk with the memo; CLUE 1 note: 'He knew his errand, and he got up to do it'",
            "E1": "reconstruction 4:09:50 (P4): the question through the ticket window; CLUE 2 note: 'Somebody at the glass asked the time'",
            "E2": "reconstruction 4:10 (P5): under the clock, the answer; CLUE 2 note: 'he looked up: ten past four'",
            "E3": "reconstruction 4:10:10 (P6): the thanks from the emptied window",
            "E4": "reconstruction 4:10:40 (P7): the cupboard open, the key on its hook; CLUE 3; the 4:30 scene shows the cupboard still open",
            "E5": "reconstruction 4:11 (P8): pencil to chin, the forgetting line; CASE CLOSED slip: 'the key never left its hook. He forgot.'; at 4:30 the SERVICE door is still shut"},
        "lines": {"question": LN["question"], "answer": LN["answer"], "thanks": LN["thanks"], "forgetting": LN["forgetting"]},
        "substitutions": "none: the four lines verbatim in the reconstruction prints; added: the detective's balloon, card, notes and slips",
        "added": "the detective and his 4:30 visit (declared: frames E0-E5 as a reconstruction after the fact); the agent is not in the office at 4:30 (where he went is not told)",
        "beat": "the detective finds the shut office at 4:30; the clues are pinned one by one with their tags and notes, the glass comes down on the key, then the reconstruction prints are laid E0 to E5 and the case is closed",
        "beat_frames": [
            "b01: 4:30, the scene: the office as left (cupboard open, key on its hook, SERVICE door shut), the detective at its edge, his card and his balloon",
            "b02: + CLUE 1 the memo, tagged, with its note",
            "b03: + CLUE 2 the clock at 4:30, tagged, with its note",
            "b04: + CLUE 3 the open cupboard, tagged, with its note",
            "b05: + the reading glass comes down on the key",
            "b06: + RECONSTRUCTION row 1: 4:09 memo, 4:09:50 question, 4:10 answer",
            "b07: + row 2: 4:10:10 thanks, 4:10:40 open cupboard, 4:11 the forgetting",
            "b08: + the CASE CLOSED slip (= the page)"],
        "self_check": {
            "size_px": [W, H], "jpeg_bytes": size, "jpeg_quality": 90, "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
            "beat_frames": nb, "detective_named": "DET. H. PRUETT on his card and in the header",
            "clues_tagged": ["CLUE 1 memo", "CLUE 2 clock", "CLUE 3 open cupboard"],
            "clock_at_4_30_on_clue": True, "outcome": "key on its hook in scene, clue 3 and reconstruction; SERVICE door shut",
            "layers_used": used,
            "pending": "independent blind reading not run by the maker"},
    }
    B.write_record(rec)
    print(json.dumps(rec["self_check"], indent=1)[:600])


if __name__ == "__main__":
    main()
