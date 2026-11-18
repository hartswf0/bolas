"""99 ways, page 09 "The memo itself" (pen-hand). The page IS the agent's memo slip, front and back:
the printed slip and his 4:15 errand on the front, then his later pencil notes (E1-E5), crossings-out,
one doodle (the key on its hook), the front's writing showing through faintly on the back.
All HANDMADE in the shared pen hand on the LoC 1934 sheet.  Run: python3 -I p09_memo.py"""
import json
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402

ROOT = pen99.ROOT
W, H = pen99.PAGE_W, pen99.PAGE_H
INK = np.array([18, 17, 16], np.float32)
PENCIL = np.array([62, 62, 70], np.float32)

FRONT = (150, 135, 2050, 1395)
BACK = (150, 1470, 2050, 2715)


def adv(s, cap):
    """Advance width of a string in the pen hand (as letter_lines lays it)."""
    s = pen99.clean(s)
    return sum(penlib.GLYPHS[c][0] * cap + cap * .1 for c in s) - cap * .1


def text_at(mask, s, x, base, cap, seed, weight=0.12):
    """Left-aligned line, baseline at y=base; returns x of each char boundary list (approx)."""
    m = pen99.letter([s], cap, seed, weight=weight)
    top = int(round(base - cap * 1.15))
    left = int(round(x - cap * 0.6))
    h, w = m.shape
    ys, xs = max(0, top), max(0, left)
    ye, xe = min(mask.shape[0], top + h), min(mask.shape[1], left + w)
    sub = mask[ys:ye, xs:xe]
    np.maximum(sub, m[ys - top:ye - top, xs - left:xe - left], out=sub)


def strike(mask, x0, x1, ymid, seed, w=6, passes=2):
    rnd = random.Random(seed)
    for p in range(passes):
        y0 = ymid + rnd.uniform(-6, 6)
        y1 = ymid + rnd.uniform(-8, 8)
        pts = [(x0 - 10, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + rnd.uniform(-5, 5)), (x1 + 10, y1)]
        penlib.brush_line(mask, pts, w, seed + p, tremor=1.6)


def line(mask, pts, w, seed, tremor=0.9):
    penlib.brush_line(mask, pts, w, seed, tremor)


def slip_frame(mask, box, seed, torn_top=False):
    x0, y0, x1, y1 = box
    rnd = random.Random(seed)
    if torn_top:   # tear-off edge of a pad: small zigzag
        pts, x = [], x0
        while x < x1:
            pts.append((x, y0 + rnd.uniform(-7, 7)))
            x += rnd.uniform(18, 34)
        pts.append((x1, y0))
        line(mask, pts, 5, seed)
    else:
        line(mask, [(x0, y0), (x1, y0)], 6, seed)
    line(mask, [(x1, y0), (x1, y1)], 6, seed + 1)
    line(mask, [(x1, y1), (x0, y1)], 6, seed + 2)
    line(mask, [(x0, y1), (x0, y0)], 6, seed + 3)


def rules(mask, box, y_first, step, x_from, seed):
    x0, y0, x1, y1 = box
    y, k = y_first, 0
    while y < y1 - 30:
        line(mask, [(x_from, y), (x1 - 40, y + 1)], 2, seed + k, tremor=0.5)
        y += step
        k += 1


# --------------------------------------------------------------- content (each item = one note, in order)
CAP_N = 58
LH = 104


def front_items():
    x0, y0, x1, y1 = FRONT
    L = x0 + 70
    yb = y0 + 420
    it = []
    it.append(("E1", [("t", "Got up from desk to fetch it.", L, yb)]))
    it.append(("E1", [("t", "Lady at window, platform side:", L, yb + LH),
                      ("t", "\"Pardon me — have you the right time?\"", L + 60, yb + 2 * LH)]))
    q = "Looked at the clock: "
    xa = L + adv(q, CAP_N)
    it.append(("E2", [("t", q, L, yb + 3 * LH), ("t", "4:12", xa + 22, yb + 3 * LH),
                      ("s", xa + 22, xa + 22 + adv("4:12", CAP_N), yb + 3 * LH - CAP_N * 0.45),
                      ("t", "4:10.", xa + 52 + adv("4:12", CAP_N), yb + 3 * LH),
                      ("t", "Told her \"Ten past four, by the clock.\"", L, yb + 4 * LH)]))
    it.append(("E3", [("t", "She: \"Much obliged!\" and off she went.", L, yb + 5 * LH),
                      ("t", "(over)", x1 - 70 - adv("(over)", 46), y1 - 45, 46)]))
    return it


def back_items():
    x0, y0, x1, y1 = BACK
    L = x0 + 70
    yb = y0 + 150
    it = []
    a = "Went on to the "
    xa = L + adv(a, CAP_N)
    it.append(("E4", [("t", a, L, yb), ("t", "desk", xa + 20, yb),
                      ("s", xa + 20, xa + 20 + adv("desk", CAP_N), yb - CAP_N * 0.45),
                      ("t", "cupboard. Opened it.", xa + 50 + adv("desk", CAP_N), yb),
                      ("t", "Key there on its hook,", L, yb + LH),
                      ("t", "tag says SERVICE.", L, yb + 2 * LH),
                      ("d",)]))
    it.append(("E5", [("t", "Stood there, pencil to chin:", L, yb + 3 * LH),
                      ("t", "\"Well, here I am...", L + 60, yb + 4 * LH),
                      ("t", "and what for?\"", L + 120, yb + 5 * LH)]))
    c = "Came for: "
    xc = L + adv(c, CAP_N)
    words = ["stamps", "ledger", "lamp oil"]
    parts = [("t", c, L, yb + 6 * LH)]
    x = xc + 20
    for wd in words:
        parts.append(("t", wd, x, yb + 6 * LH))
        parts.append(("s", x, x + adv(wd, CAP_N), yb + 6 * LH - CAP_N * 0.45))
        x += adv(wd, CAP_N) + 46
    parts.append(("t", "?", x, yb + 6 * LH))
    it.append(("E5", parts))
    it.append(("E5", [("t", "Key still on hook. Door still shut.", L, yb + 8 * LH)]))
    return it


def doodle(mask, seed):
    """The one doodle: the brass key on its hook with its tag, drawn in pencil at the back's right."""
    cx, cy = 1760, 1640
    line(mask, [(cx - 40, cy - 30), (cx + 40, cy - 30)], 7, seed)              # hook rail
    line(mask, [(cx, cy - 30), (cx, cy + 10), (cx - 12, cy + 26), (cx - 26, cy + 16)], 6, seed + 1)  # hook
    # bow (ring)
    pts = [(cx + 46 * math.cos(t), cy + 70 + 40 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 40)]
    line(mask, pts, 6, seed + 2)
    pts = [(cx + 20 * math.cos(t), cy + 70 + 15 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 30)]
    line(mask, pts, 4, seed + 3)
    line(mask, [(cx - 7, cy + 110), (cx - 7, cy + 380)], 6, seed + 4)
    line(mask, [(cx + 7, cy + 110), (cx + 7, cy + 380)], 6, seed + 5)
    line(mask, [(cx - 7, cy + 380), (cx + 7, cy + 380)], 6, seed + 6)
    line(mask, [(cx + 7, cy + 320), (cx + 52, cy + 320), (cx + 52, cy + 345), (cx + 30, cy + 345),
                (cx + 30, cy + 365), (cx + 7, cy + 365)], 6, seed + 7)                   # bit
    for k, yy in enumerate((cy + 150, cy + 166)):
        line(mask, [(cx - 16, yy), (cx + 16, yy)], 4, seed + 8 + k)
    # string and tag
    line(mask, [(cx - 6, cy + 150), (cx - 70, cy + 210), (cx - 120, cy + 240)], 3, seed + 10)
    tx, ty = cx - 330, cy + 230
    line(mask, [(tx, ty), (tx + 210, ty - 6), (tx + 220, ty + 70), (tx + 6, ty + 78), (tx, ty)], 5, seed + 11)
    text_at(mask, "SERVICE", tx + 26, ty + 54, 34, seed + 12)
    # question mark drawn beside
    text_at(mask, "?", cx + 90, cy + 260, 110, seed + 13, weight=0.11)


LAST_ST = {}
ST_L_MIN = 201   # OpenCV 8-bit Lab L (0-255); 1 above the 200 cap for rounding
DOODLE_SRC = (1400, 1580, 1960, 2060)      # the doodle as drawn by doodle()
DOODLE_S = 0.56                             # set smaller ...
DOODLE_AT = (1610, 2440)                    # ... in the back's lower right, below the front's show-through
DOODLE_BOX = (DOODLE_AT[0] - 12, DOODLE_AT[1] - 12, int(DOODLE_AT[0] + DOODLE_S * 560) + 12,
              int(DOODLE_AT[1] + DOODLE_S * 480) + 12)


def build(n_items=99, show_through=True):
    doodle_box = None
    pg = pen99.sheet99().astype(np.float32)
    ink = np.zeros((H, W), np.uint8)       # printed slip (pen ink)
    pen = np.zeros((H, W), np.uint8)       # his pencil
    # the slip, front: printed form
    slip_frame(ink, FRONT, 9100, torn_top=True)
    fx0, fy0, fx1, fy1 = FRONT
    text_at(ink, "MEMO", fx0 + 70, fy0 + 95, 54, 9110, weight=0.16)
    text_at(ink, "C.V.RY.", fx1 - 70 - adv("C.V.RY.", 54), fy0 + 95, 54, 9111, weight=0.16)
    text_at(ink, "Randolph Sta.", fx0 + 70 + adv("MEMO", 54) + 90, fy0 + 95, 40, 9112)
    line(ink, [(fx0 + 40, fy0 + 130), (fx1 - 40, fy0 + 130)], 4, 9113)
    rules(ink, FRONT, fy0 + 245, LH, fx0 + 50, 9200)
    # the errand (E0), large, his pencil
    text_at(pen, "4:15 - open SERVICE door.", fx0 + 80, fy0 + 230, 82, 9120, weight=0.12)
    text_at(pen, "Key in cupboard.", fx0 + 80, fy0 + 230 + 112, 82, 9121, weight=0.12)
    # back
    slip_frame(ink, BACK, 9300)
    bx0, by0, bx1, by1 = BACK
    rules(ink, BACK, by0 + 150, LH, bx0 + 50, 9400)
    text_at(ink, "back of slip", bx1 - 70 - adv("back of slip", 34), by0 + 50, 34, 9310)
    items = front_items() + back_items()
    k = 0
    for i, (ev, parts) in enumerate(items):
        if i >= n_items:
            break
        for p in parts:
            k += 1
            if p[0] == "t":
                cap = p[4] if len(p) > 4 else CAP_N
                text_at(pen, p[1], p[2], p[3], cap, 9500 + k * 7, weight=0.12)
            elif p[0] == "s":
                strike(pen, p[1], p[2], p[3], 9700 + k * 5)
            elif p[0] == "d":
                dm = np.zeros((H, W), np.uint8)
                doodle(dm, 9800)          # drawn at its design place, then set (scaled) in the back's clear corner
                ox0, oy0 = DOODLE_SRC[0], DOODLE_SRC[1]
                M = np.float32([[DOODLE_S, 0, DOODLE_AT[0] - DOODLE_S * ox0], [0, DOODLE_S, DOODLE_AT[1] - DOODLE_S * oy0]])
                dm = cv2.warpAffine(dm, M, (W, H), flags=cv2.INTER_AREA)
                np.maximum(pen, dm, out=pen)
                doodle_box = DOODLE_BOX
    # show-through of the front's pencil on the back: mirrored about the slip's vertical centre (FRONT and BACK
    # share x0..x1, so a flip of the front strip in place puts a line's start at the back's right margin), faint
    # (darkest show-through pixel capped at L=200 on the paper), and knocked out round the doodle and his back notes.
    if show_through:
        fr = np.ascontiguousarray(pen[fy0:fy1, fx0:fx1][:, ::-1])     # contiguous copy: cv2 ignores negative strides
        st = cv2.GaussianBlur(fr, (0, 0), 2.2)
        hh = min(fr.shape[0], by1 - by0)
        reg = np.zeros((H, W), np.uint8)
        reg[by0:by0 + hh, bx0:bx0 + fr.shape[1]] = st[:hh]
        back_pen = np.zeros((H, W), np.uint8)
        back_pen[by0:by1, bx0:bx1] = pen[by0:by1, bx0:bx1]
        keep = cv2.dilate(back_pen, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
        if doodle_box is not None:
            dx0, dy0, dx1, dy1 = doodle_box
            keep[dy0:dy1, dx0:dx1] = 255
        keep = cv2.GaussianBlur(keep, (0, 0), 3)
        if doodle_box is not None:
            keep[dy0 - 10:dy1 + 10, dx0 - 10:dx1 + 10] = 255
        reg = (reg.astype(np.float32) * (1 - keep.astype(np.float32) / 255.0)).astype(np.uint8)
        before = pg.copy()
        penlib.ink_onto(pg, reg, color=np.array([150, 148, 150], np.float32), alpha=0.22)
        Lb = cv2.cvtColor(np.clip(before, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
        La = cv2.cvtColor(np.clip(pg, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
        over = (La < ST_L_MIN) & (reg > 0)
        t = np.ones_like(La)
        t[over] = np.clip((Lb[over] - ST_L_MIN) / np.maximum(Lb[over] - La[over], 1e-3), 0, 1)
        pg[:] = before + (pg - before) * t[..., None]
        Lf = cv2.cvtColor(np.clip(np.round(pg), 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
        dk = (Lb - Lf) >= 1
        dx0, dy0, dx1, dy1 = DOODLE_BOX
        LAST_ST.update(changed=int(dk.sum()), minL=int(Lf[dk].min()) if dk.any() else None,
                       in_doodle=int(dk[dy0:dy1, dx0:dx1].sum()))
    penlib.ink_onto(pg, ink, color=INK)
    penlib.ink_onto(pg, pen, color=PENCIL, alpha=0.93)
    pen99.folio(pg, 9, "The memo itself")
    return np.clip(np.round(pg), 0, 255).astype(np.uint8), [ev for ev, _ in items]


ST_CHECK = {}


def main():
    from b1m2 import credit_pages
    out_jpg = ROOT / "assets/pages/99-ways/09-the-memo.jpg"
    out_png = ROOT / "films/sources/99-ways/masters/09-the-memo.png"
    beats = ROOT / "films/sources/99-ways/beats/09"
    beats.mkdir(parents=True, exist_ok=True)
    page, evs = build()
    ST_CHECK.update({"mirrored": "horizontal flip about the slip's vertical centre (x=%d)" % ((FRONT[0] + FRONT[2]) // 2),
                     "changed_px": LAST_ST["changed"], "darkest_L_of_darkened_px_lab255": LAST_ST["minL"],
                     "darkened_px_in_doodle_box": LAST_ST["in_doodle"],
                     "in_beats": "b05-b07 built with the same layer"})
    Image.fromarray(page).save(out_png, compress_level=6)
    Image.fromarray(page).save(out_jpg, quality=90, dpi=(300, 300))
    size = out_jpg.stat().st_size
    states = [(0, "b01: the slip with only the 4:15 errand (E0)"),
              (2, "b02: + got up, the lady's question (E1)"),
              (3, "b03: + the clock, 4:12 crossed out to 4:10, his answer (E2)"),
              (4, "b04: + her thanks, (over) (E3)"),
              (5, "b05: back of slip: cupboard (desk crossed out), key on hook, the doodle (E4)"),
              (6, "b06: + the forgetting line (E5)"),
              (8, "b07: + 'Came for:' guesses crossed out; 'Key still on hook. Door still shut.'")]
    for j, (n, _) in enumerate(states, 1):
        im = page if n >= len(evs) else build(n)[0]
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(beats / f"b{j:02d}.png")
    src = ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    credit_pages(src, 9)
    rec = {
        "n": 9, "id": "the-memo", "title": "The memo itself", "family": "reader and object", "medium": "pen-hand",
        "canon_revision": "c1",
        "rule": "The page is the agent's memo slip, both sides, the incident told in his notes, crossings-out and one doodle.",
        "declares": "E1-E5 as his later notes",
        "file": str(out_jpg.relative_to(ROOT)), "master": str(out_png.relative_to(ROOT)),
        "beats_dir": str(beats.relative_to(ROOT)), "build": "films/swarm/99-ways/build/p09_memo.py",
        "sources": src,
        "made": [
            "the memo slip drawn full-page in the shared pen hand (penlib.letter_lines via pen99, penlib.brush_line): "
            "torn pad edge, printed head 'MEMO / Randolph Sta. / C.V.RY.', ruled lines; the back of the slip below it",
            "the canon memo text '4:15 - open SERVICE door. Key in cupboard.' as his pencil, then his later pencil notes "
            "E1-E5 quoting the four canon lines verbatim",
            "three crossings-out (4:12 -> 4:10; desk -> cupboard; 'Came for: stamps, ledger, lamp oil ?')",
            "one doodle: the brass key on its hook with the SERVICE tag and a question mark, set small in the back's lower right where no show-through falls",
            "the front's pencil showing through the back: mirror-reversed about the slip's vertical centre (lines start at the back's right margin), faint (darkest show-through pixel capped at Lab L 200 of 255), kept clear of the doodle (hard box) and of a thin halo round his back notes; the same layer in beats b05-b07; folio by pen99.folio"],
        "events": {"E0": "front: '4:15 - open SERVICE door. Key in cupboard.'; 'Got up from desk to fetch it.'",
                   "E1": "front: 'Lady at window, platform side:' + the question quoted",
                   "E2": "front: 'Looked at the clock: (4:12 struck) 4:10.' + the answer quoted",
                   "E3": "front: 'She: \"Much obliged!\" and off she went.'",
                   "E4": "back: 'Went on to the (desk struck) cupboard. Opened it. Key there on its hook, tag says SERVICE.' + doodle",
                   "E5": "back: 'Stood there, pencil to chin:' + the forgetting line; guesses crossed out; 'Key still on hook. Door still shut.'"},
        "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
                  "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
        "beat": "the slip is written on: from the bare 4:15 errand, note by note down the front, over to the back, "
                "the doodle, the forgetting line, the crossed-out guesses",
        "beat_frames": [d for _, d in states],
        "self_check": {"size_px": [W, H], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "note_cap_px": CAP_N, "crossings_out": 5, "doodles": 1,
                       "show_through": ST_CHECK,
                       "check": "A reader says the page is the memo, and finds E0-E5 in its notes (maker's judgement from the full-size page; blind reading pending)",
                       "evidence": "measured (size, bytes) and perceptually judged (from frames) by the maker"},
    }
    json.dump(rec, open(ROOT / "films/swarm/99-ways/pages/09.json", "w"), indent=1, ensure_ascii=False)
    print(size)


if __name__ == "__main__":
    main()
