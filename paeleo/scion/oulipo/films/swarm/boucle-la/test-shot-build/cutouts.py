"""SCION 29 cut-out extraction for the boucle-la test shot.

Source: Honore Daumier, Moeurs conjugales no. 3 (1839), Rijksmuseum RP-P-OB-41.183, CC0 (Commons).
All geometry is hand-set in the coordinates of the 960 px Commons thumbnail (d0.jpg) and scaled by
K when the original-resolution file is used.

Per figure: a hand-set scissor envelope; per method a matte:
  * grabcut  - cv2.grabCut seeded by the envelope (probable FG), an eroded core (sure FG), the outside
               (sure BG) and dark-backdrop scribbles (probable BG) on the colour print;
  * tonal    - luminance against Daumier's dark crayon vignette inside the envelope;
  * manual   - the envelope polygon itself (hand-placed scissor snips).
The winner per figure is chosen by score (one component, no pixel inside the other figure's
hand-marked region, least backdrop leakage); the contour is then re-cut as straight snips.
Pieces: body / head (neck pin) / forearm (elbow pin).  Levels only: black point / white point on
luminance, mapped to ink #0D0D0D .. page #FBFBFB.  Run: python3 -I cutouts.py
"""
import hashlib
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
MEDIA = os.path.join(ROOT, "films/sources/boucle-la/test-shot")
ORIG = os.path.join(MEDIA, "daumier-orig.jpg")
THUMB = os.path.join(ROOT, "films/sources/boucle-la/daumier/d0.jpg")
OUT = os.path.join(MEDIA, "cut")

INK, PAGE = 13, 251
BP, WP = 95, 198  # levels: black point, white point (luminance of the print)

# -- hand-set scissor envelopes (thumb coords).  Upper body to the thigh: the panels frame waist/knee-up.
ENV = {
    "gustave": [(372, 318), (400, 296), (450, 300), (478, 326), (482, 356), (500, 372), (500, 384), (482, 392),
                (470, 418), (452, 440), (458, 470), (452, 520), (462, 545), (500, 548), (538, 552), (538, 594),
                (470, 600), (456, 612), (448, 700), (440, 790), (300, 800), (232, 760), (226, 560), (262, 470),
                (330, 425), (372, 408), (368, 360)],
    "odette": [(560, 330), (585, 316), (640, 318), (664, 334), (674, 362), (676, 400), (690, 418), (722, 440), (748, 520),
               (760, 640), (768, 800), (640, 812), (586, 800), (590, 640), (590, 600), (542, 600), (542, 552),
               (580, 552), (586, 480), (600, 445), (572, 430), (552, 405), (548, 372)],
}
# hand-marked exclusive regions: no pixel of one figure may fall in the other's region (the meeting hands)
OWN = {"gustave": [(420, 530), (538, 530), (538, 610), (420, 610)],
       "odette": [(542, 530), (640, 530), (640, 610), (542, 610)]}
# articulated pieces: polygon (thumb coords) and pin
PIECES = {
    "gustave": {"head": ([(330, 280), (520, 280), (520, 440), (470, 440), (448, 452), (330, 452)], (436, 438)),
                "fore": ([(408, 528), (540, 540), (540, 600), (470, 606), (408, 618)], (424, 574))},
    "odette": {"head": ([(530, 300), (710, 300), (710, 438), (650, 440), (608, 452), (530, 452)], (618, 440)),
               "fore": ([(542, 548), (600, 546), (646, 556), (648, 604), (600, 600), (542, 596)], (634, 584))},
}
FEET = {"gustave": (380, 930), "odette": (660, 930)}       # root pivots (lean about the feet)
HAND = {"gustave": (532, 566), "odette": (552, 570)}       # view anchors on the forearm (note anchor: odette)
CLOTH = (262, 600, 330, 690)                              # nightshirt patch used to re-cloth the vacated sleeve


def load():
    p = ORIG if os.path.exists(ORIG) and os.path.getsize(ORIG) > 1e6 else THUMB
    img = cv2.imread(p, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit("cannot decode " + p)
    return img, img.shape[1] / 960.0, p


def poly_mask(shape, pts, K):
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillPoly(m, [np.round(np.array(pts, np.float64) * K).astype(np.int32)], 255)
    return m


def largest(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8), connectivity=8)
    if n <= 1:
        return m
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return np.where(lab == k, 255, 0).astype(np.uint8)


def fill_holes(m):
    ff = m.copy()
    h, w = m.shape
    pad = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, pad, (0, 0), 255)
    return m | cv2.bitwise_not(ff)


def matte_grabcut(img, E, K):
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gm = np.full(E.shape, cv2.GC_BGD, np.uint8)
    gm[E > 0] = cv2.GC_PR_FGD
    core = cv2.erode(E, np.ones((int(25 * K), int(25 * K)), np.uint8))
    gm[(core > 0)] = cv2.GC_FGD
    dark = cv2.GaussianBlur(lum, (0, 0), 2 * K) < 105
    gm[(E > 0) & dark & (core == 0)] = cv2.GC_PR_BGD
    ys, xs = np.nonzero(E)
    pad = int(30 * K)
    y0, y1, x0, x1 = max(0, ys.min() - pad), ys.max() + pad, max(0, xs.min() - pad), xs.max() + pad
    sub = gm[y0:y1, x0:x1].copy()
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img[y0:y1, x0:x1], sub, None, bg, fg, 5, cv2.GC_INIT_WITH_MASK)
    out = np.zeros(E.shape, np.uint8)
    out[y0:y1, x0:x1] = np.where((sub == cv2.GC_FGD) | (sub == cv2.GC_PR_FGD), 255, 0)
    return out & E, gm


def matte_tonal(img, E, K):
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gb = cv2.GaussianBlur(lum, (0, 0), 3 * K)
    m = ((gb > 118) & (E > 0)).astype(np.uint8) * 255
    el = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(r * K) | 1,) * 2)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, el(9))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, el(7))
    return m


def clean(m, K):
    m = largest(fill_holes(largest(m)))
    m = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3.5 * K) > 127).astype(np.uint8) * 255  # scissor hand, not pixel stairs
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)
    snips = cv2.approxPolyDP(c, 2.6 * K, True)  # scissors: straight snips, not pixel steps
    out = np.zeros_like(m)
    cv2.fillPoly(out, [snips], 255)
    return out, len(snips)


def score(m, other_own, lum):
    n = cv2.connectedComponents((m > 0).astype(np.uint8))[0] - 1
    trespass = int(((m > 0) & (other_own > 0)).sum())
    ring = (cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0) & (cv2.erode(m, np.ones((5, 5), np.uint8)) == 0)
    leak = float((lum[ring] < 100).mean()) if ring.any() else 1.0  # dark backdrop carried along the cut edge
    return dict(components=int(n), trespass=trespass, edge_dark_frac=round(leak, 4),
                ok=bool(n == 1 and trespass == 0))


def levels(lum):
    t = np.clip((lum.astype(np.float32) - BP * 1.0) / (WP - BP), 0, 1)
    return (INK + t * (PAGE - INK)).round().astype(np.uint8)


def main():
    os.makedirs(OUT, exist_ok=True)
    img, K, src = load()
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    tone = levels(lum)
    report = {"source": os.path.relpath(src, ROOT), "K": K, "levels": {"black_point": BP, "white_point": WP,
              "ink": INK, "page": PAGE, "method": "linear levels on luminance; no threshold, no posterize, no sharpening"},
              "figures": {}}
    masks = {}
    for name in ENV:
        E = poly_mask(img.shape, ENV[name], K)
        own_other = poly_mask(img.shape, OWN["odette" if name == "gustave" else "gustave"], K)
        cand = {}
        g, seeds = matte_grabcut(img, E, K)
        cv2.imwrite(os.path.join(OUT, f"seeds_{name}.png"), (seeds * 85).astype(np.uint8))
        cand["grabcut"] = g
        cand["tonal"] = matte_tonal(img, E, K)
        cand["manual"] = E.copy()
        res = {}
        for k, m in cand.items():
            m = m & ~own_other
            cm, nsn = clean(m, K) if m.any() else (m, 0)
            cand[k] = cm
            s = score(cm, own_other, lum)
            s["snips"] = nsn
            s["area"] = int((cm > 0).sum())
            res[k] = s
            cv2.imwrite(os.path.join(OUT, f"matte_{name}_{k}.png"), cm)
        # choose: valid, least dark backdrop along the edge, then larger area (keeps the fingers)
        ok = [k for k in res if res[k]["ok"]]
        best = min(ok, key=lambda k: (res[k]["edge_dark_frac"] > 0.35, res[k]["edge_dark_frac"] - 1e-7 * res[k]["area"]))
        m = cand[best]
        if name == "odette":  # collage rewrite: the hanging towel is dropped; the note takes its place
            m[int(596 * K):, : int(590 * K)] = 0
            m = largest(m)
        masks[name] = m
        report["figures"][name] = {"candidates": res, "chosen": best}
    # pieces
    pieces = {}
    for name in ENV:
        m = masks[name]
        rest = m.copy()
        out = {}
        for pn, (pp, piv) in PIECES[name].items():
            P = poly_mask(img.shape, pp, K)
            pm = m & P
            keep = np.zeros_like(m)
            if pn == "head":   # the body keeps the paper under the neck pin (underlap)
                keep[int((piv[1] - 30) * K):, :] = 255
            else:
                cv2.circle(keep, (int(piv[0] * K), int(piv[1] * K)), int(20 * K), 255, -1)
            rest = rest & ~(P & ~keep)
            out[pn] = (largest(pm), piv)
        out["body"] = (largest(rest), (0, 0))
        # re-cloth the vacated sleeve area: a patch of Daumier's own nightshirt crayon, inside the body only
        for pn, (pm, piv) in out.items():
            # white scissor margin only on the silhouette's outside edge; seams inside the figure are bare paper cuts
            rim = cv2.dilate(pm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(3 * K) * 2 + 1,) * 2))
            rim = np.where((rim > 0) & ((m == 0) | (pm > 0)), 255, 0).astype(np.uint8)
            a = np.where(pm > 0, tone, PAGE).astype(np.uint8)
            ys, xs = np.nonzero(rim)
            x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
            rgba = np.dstack([a, a, a, rim])[y0:y1, x0:x1]
            fn = os.path.join(OUT, f"{name}_{pn}.png")
            Image.fromarray(rgba, "RGBA").save(fn)
            pieces[f"{name}_{pn}"] = {"file": os.path.relpath(fn, ROOT), "offset": [int(x0), int(y0)],
                                      "pin": [piv[0] * K, piv[1] * K] if pn != "body" else None,
                                      "sha256": hashlib.sha256(open(fn, "rb").read()).hexdigest(),
                                      "components": int(cv2.connectedComponents((pm > 0).astype(np.uint8))[0] - 1)}
    # invariant: no pixel of one figure inside the other's marked region
    for name in ENV:
        other = poly_mask(img.shape, OWN["odette" if name == "gustave" else "gustave"], K)
        assert not ((masks[name] > 0) & (other > 0)).any(), name + " trespasses"
    for k, v in pieces.items():
        assert v["components"] == 1, k + " has islands"
    report["pieces"] = pieces
    report["rig"] = {"feet": {k: [v[0] * K, v[1] * K] for k, v in FEET.items()},
                     "hand": {k: [v[0] * K, v[1] * K] for k, v in HAND.items()},
                     "graph": "feet(root lean) -> body -> neck pin -> head; body -> elbow pin -> forearm -> hand anchor (-> note for odette)"}
    json.dump(report, open(os.path.join(OUT, "cutouts.json"), "w"), indent=1)
    # contact: the chosen mattes over the print
    vis = img.copy()
    for name, col in (("gustave", (0, 0, 255)), ("odette", (255, 0, 0))):
        cnts, _ = cv2.findContours(masks[name], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(vis, cnts, -1, col, max(1, int(2 * K)))
    cv2.imwrite(os.path.join(OUT, "mattes_vis.jpg"), vis)
    print(json.dumps(report["figures"], indent=1))


if __name__ == "__main__":
    main()
