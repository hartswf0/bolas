"""boucle-la U1 panel artist: SCION 29 cut-out extraction + SCION 32 rig definition.

Source: Honore Daumier, Moeurs conjugales no. 3 (1839), Rijksmuseum RP-P-OB-41.183, CC0 (Commons).
All hand-placed geometry is in the coordinates of the 960 px wide view of the print ("thumb px") and is
scaled by K = source_width / 960 to the file actually cut.

Pieces per figure (back to front):  head (behind the body; its neck underlap tucks under the collar),
body (silhouette minus the visible head and forearm; the vacated sleeve area re-clothed with Daumier's own
shirt crayon cloned from the same figure), forearm+hand (on top; round elbow cap over the upper sleeve).
Per piece three candidates are cut and scored: seeded grabCut, tonal matte, manual contour (hand-placed
scissor snips).  Seeds and failure masks are exported.  Tone: levels only, per piece (black point, white
point, gamma) on a red-weighted luminance (the photographer's red filter: drops the orange foxing, keeps the
neutral crayon), mapped to ink #0D0D0D .. page #FBFBFB.  No threshold, no posterize, no sharpening.
Run: python3 -I cutouts.py
"""
import hashlib
import json
import math
import os

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
MEDIA = os.path.join(ROOT, "films/sources/boucle-la/panel-artist")
OUT = os.path.join(MEDIA, "cut")
DBG = os.path.join(MEDIA, "masks")
SRC_ORIG = os.path.join(MEDIA, "orig/daumier-original.jpg")
SRC_1920 = os.path.join(MEDIA, "daumier-1920.jpg")
INK, PAGE = 13, 251

# ---------------------------------------------------------------- hand-placed geometry (thumb px)
# whole-figure scissor envelopes (from shoulder to thigh; the panels frame waist/knee-up)
ENV = {
    "gustave": [(372, 318), (400, 296), (450, 300), (478, 326), (482, 356), (500, 372), (500, 384), (482, 392),
                (470, 418), (452, 440), (458, 470), (452, 520), (462, 545), (500, 548), (538, 552), (558, 566),
                (540, 600), (456, 612), (448, 700), (440, 790), (300, 800), (232, 760), (226, 560), (262, 470),
                (330, 425), (372, 408), (368, 360)],
    "odette": [(560, 330), (585, 316), (640, 318), (664, 334), (674, 362), (676, 400), (690, 418), (722, 440),
               (748, 520), (760, 640), (768, 800), (640, 812), (586, 800), (590, 640), (594, 606), (560, 600),
               (515, 576), (520, 566), (580, 552), (586, 480), (600, 445), (572, 430), (552, 405), (548, 372)],
}
# visible head contour above the collar line (closed along the collar, which is Daumier's own drawn line)
HEAD_VIS = {
    "gustave": [(380, 392), (383, 384), (384, 360), (388, 345), (398, 330), (410, 318), (425, 310), (440, 306),
                (455, 308), (470, 314), (479, 325), (482, 333), (473, 350), (477, 369), (490, 376), (501, 382),
                (493, 388), (481, 391), (477, 399), (471, 406), (481, 411), (473, 422), (450, 428), (428, 432),
                (415, 436), (402, 433), (392, 420), (385, 405)],
    "odette": [(578, 328), (586, 321), (600, 320), (620, 318), (640, 318), (655, 323), (666, 335), (671, 355),
               (672, 375), (669, 393), (662, 405), (652, 416), (640, 424), (628, 432), (618, 438), (612, 442),
               (602, 436), (590, 428), (580, 421), (573, 411), (568, 403), (566, 398), (560, 394), (564, 388),
               (569, 376), (573, 363), (577, 350), (579, 338)],
}
NECK_PIN = {"gustave": (405, 424), "odette": (634, 432)}
UNDERLAP_R = 24  # thumb px: the neck paper that continues under the collar (hidden at rest)
# forearm + hand; the elbow end is a round cap centred on the elbow pin
FORE = {
    "gustave": [(370, 532), (388, 525), (405, 530), (425, 540), (447, 548), (470, 553), (490, 556), (505, 558),
                (520, 555), (535, 555), (548, 561), (557, 568), (548, 572), (530, 569), (518, 570), (505, 580),
                (490, 592), (470, 600), (447, 603), (425, 600), (405, 588), (388, 572), (374, 558), (366, 545)],
    "odette": [(516, 571), (530, 569), (545, 572), (556, 570), (566, 563), (580, 561), (595, 560), (612, 556),
               (628, 548), (645, 548), (660, 560), (672, 580), (675, 600), (668, 616), (652, 622), (632, 616),
               (612, 606), (595, 603), (580, 600), (565, 594), (552, 585), (536, 580), (520, 577)],
}
ELBOW_PIN = {"gustave": (386, 548), "odette": (655, 596)}
ELBOW_CAP_R = 20
HAND = {"gustave": (530, 563), "odette": (572, 580)}      # view anchors; odette's = the note anchor (her grip)
FEET = {"gustave": (380, 930), "odette": (660, 930)}      # root pivots (lean about the feet, off-panel)
# hand-marked exclusive regions where the hands meet (no pixel of one figure in the other's)
OWN = {"gustave": [(500, 548), (556, 556), (560, 567), (546, 571), (530, 568), (517, 569), (500, 572)],
       "odette": [(516, 572), (530, 570), (546, 573), (561, 571), (590, 566), (590, 600), (516, 590)]}
# torso outlines: where the forearm crosses in front of the torso its footprint is re-clothed, elsewhere cut away
TORSO = {"gustave": [(330, 495), (416, 505), (420, 560), (424, 612), (330, 625)],
         "odette": [(612, 540), (720, 540), (720, 650), (598, 650), (596, 606), (606, 600)]}
# the reach zone beyond the torso: belongs to the forearm piece or to nobody (towel, backdrop)
ARMZONE = {"gustave": [(418, 500), (600, 500), (600, 630), (424, 630)],
           "odette": [(500, 540), (606, 540), (604, 604), (596, 612), (500, 625)]}
# cloth patches (Daumier's own crayon on the same garment) to re-clothe the area the forearm vacates
CLOTH = {"gustave": (262, 600, 340, 690), "odette": (690, 640, 740, 720)}
# the print's dark backdrop crayon behind the heads, cut as a spot-black set piece
BACK_POLY = [(168, 300), (240, 268), (330, 254), (450, 250), (560, 252), (650, 262), (684, 300), (690, 470),
             (676, 560), (560, 556), (420, 552), (300, 556), (200, 548), (160, 520)]

# per-piece levels (black point, white point, gamma>1 deepens the crayon mid-tones) on red-weighted luminance
LEVELS = {
    "gustave_head": (112, 196, 1.45), "gustave_body": (128, 200, 1.6), "gustave_fore": (128, 200, 1.6),
    "odette_head": (118, 198, 1.5), "odette_body": (130, 200, 1.65), "odette_fore": (130, 200, 1.6),
    "backdrop": (100, 190, 1.2),
}
MARGIN = 3.5  # thumb px of white scissor margin on the silhouette's outside edge (~3.8 px at page scale 1.1)


def load():
    for p in (SRC_ORIG, SRC_1920):
        if os.path.exists(p) and os.path.getsize(p) > 1e6:
            img = cv2.imread(p, cv2.IMREAD_COLOR)
            if img is not None:
                return img, img.shape[1] / 960.0, p
    raise SystemExit("no source")


def pm(shape, pts, K):
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillPoly(m, [np.round(np.array(pts, np.float64) * K).astype(np.int32)], 255, lineType=cv2.LINE_8)
    return m


def disk(shape, c, r, K):
    m = np.zeros(shape[:2], np.uint8)
    cv2.circle(m, (int(round(c[0] * K)), int(round(c[1] * K))), int(round(r * K)), 255, -1)
    return m


def el(r):
    r = max(1, int(round(r)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def largest(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8), connectivity=8)
    if n <= 1:
        return m
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    return np.where(lab == k, 255, 0).astype(np.uint8)


def fill_holes(m):
    ff = m.copy()
    pad = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, pad, (0, 0), 255)
    return m | cv2.bitwise_not(ff)


def ncomp(m):
    return cv2.connectedComponents((m > 0).astype(np.uint8), connectivity=8)[0] - 1


def snip(m, K):
    """Scissor hand: smooth pixel stairs, then straight snips (polygon approximation)."""
    m = largest(fill_holes(largest(m)))
    m = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.6 * K) > 127).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return m, 0
    c = max(cnts, key=cv2.contourArea)
    s = cv2.approxPolyDP(c, 1.3 * K, True)
    out = np.zeros_like(m)
    cv2.fillPoly(out, [s], 255)
    return out, len(s)


def cand_grabcut(img, region, K):
    """Seeded graph cut: sure FG = region eroded, probable FG = region, probable BG = dark backdrop
    crayon inside the region's rim, sure BG = outside the region dilated."""
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gm = np.full(region.shape, cv2.GC_BGD, np.uint8)
    outer = cv2.dilate(region, el(6 * K))
    gm[outer > 0] = cv2.GC_PR_BGD
    gm[region > 0] = cv2.GC_PR_FGD
    core = cv2.erode(region, el(6 * K))
    gm[core > 0] = cv2.GC_FGD
    dark = cv2.GaussianBlur(lum, (0, 0), 2 * K) < 100
    rim = (region > 0) & (core == 0)
    gm[rim & dark] = cv2.GC_PR_BGD
    ys, xs = np.nonzero(outer)
    pad = int(20 * K)
    y0, y1 = max(0, ys.min() - pad), min(img.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(img.shape[1], xs.max() + pad)
    sub = gm[y0:y1, x0:x1].copy()
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img[y0:y1, x0:x1], sub, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
    out = np.zeros(region.shape, np.uint8)
    out[y0:y1, x0:x1] = np.where((sub == cv2.GC_FGD) | (sub == cv2.GC_PR_FGD), 255, 0)
    return out & outer, gm


def cand_tonal(img, region, K):
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gb = cv2.GaussianBlur(lum, (0, 0), 3 * K)
    m = ((gb > 118) & (cv2.dilate(region, el(4 * K)) > 0)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, el(4 * K))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, el(3 * K))
    return m


def score(m, region, other_own, lum, K):
    trespass = int(((m > 0) & (other_own > 0)).sum())
    ring = (cv2.dilate(m, el(2 * K)) > 0) & (cv2.erode(m, el(2 * K)) == 0)
    edge_dark = float((lum[ring] < 100).mean()) if ring.any() else 1.0   # backdrop carried along the edge
    inner = cv2.erode(region, el(5 * K)) > 0
    lost = float(((m == 0) & inner).sum()) / max(1, int(inner.sum()))     # body/cap paper lost (fingers, cap)
    return dict(components=ncomp(m), trespass=trespass, edge_dark_frac=round(edge_dark, 4),
                interior_lost_frac=round(lost, 4), area=int((m > 0).sum()))


def choose(res):
    ok = [k for k, r in res.items() if r["components"] == 1 and r["trespass"] == 0 and r["interior_lost_frac"] < 0.02]
    if not ok:
        ok = ["manual"]
    # least backdrop along the edge; ties -> keep more paper (fingers intact)
    return min(ok, key=lambda k: (round(res[k]["edge_dark_frac"], 2), -res[k]["area"]))


def red_lum(img):
    b, g, r = [img[..., i].astype(np.float32) for i in range(3)]
    return 0.70 * r + 0.30 * g


def levels(L, bp, wp, gamma):
    t = np.clip((L - bp) / float(wp - bp), 0, 1) ** gamma
    return INK + t * (PAGE - INK)


def sha(fn):
    return hashlib.sha256(open(fn, "rb").read()).hexdigest()


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DBG, exist_ok=True)
    img, K, src = load()
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    L = red_lum(img)
    sh = img.shape
    own = {f: pm(sh, OWN[f], K) for f in OWN}
    other = {"gustave": "odette", "odette": "gustave"}
    report = {"source": os.path.relpath(src, ROOT), "source_sha256": sha(src), "K": K,
              "coords": "pieces' offsets/pins in source px; *_thumb fields in 960-px-wide view px (x K = source px)",
              "pieces": {}, "methods": {}}
    # 1. hand-placed region per piece (manual contour) --------------------------------------------
    fig_env = {f: pm(sh, ENV[f], K) for f in ENV}
    regions = {}
    for f in ("gustave", "odette"):
        hv = pm(sh, HEAD_VIS[f], K)
        fo = pm(sh, FORE[f], K) | (disk(sh, ELBOW_PIN[f], ELBOW_CAP_R, K) & fig_env[f])
        fo &= ~own[other[f]]
        body = fig_env[f] & ~hv & ~own[other[f]] & ~pm(sh, ARMZONE[f], K)
        regions[f] = {"head": hv & ~own[other[f]], "fore": fo, "body": body}
    # 2. candidates per piece, score, choose, export seeds + failure masks ---------------------------
    chosen = {}
    for f in ("gustave", "odette"):
        oth = own[other[f]] | (fig_env[other[f]] & ~fig_env[f])
        for pn in ("head", "body", "fore"):
            key = f"{f}_{pn}"
            R = regions[f][pn]
            g, seeds = cand_grabcut(img, R, K)
            cv2.imwrite(os.path.join(DBG, f"seeds_{key}.png"), (seeds * 85).astype(np.uint8))
            cands = {"grabcut": g, "tonal": cand_tonal(img, R, K), "manual": R.copy()}
            res = {}
            for k, m in cands.items():
                m = m & ~own[other[f]]
                if pn != "body":
                    m = m & cv2.dilate(R, el(2 * K))     # a piece never grows past its hand-marked part
                cm, ns = snip(m, K) if m.any() else (m, 0)
                cm &= ~own[other[f]]
                cands[k] = cm
                s = score(cm, R, oth, lum, K)
                s["snips"] = ns
                res[k] = s
                cv2.imwrite(os.path.join(DBG, f"cand_{key}_{k}.png"), cm)
                # failure mask: interior paper lost (red) and backdrop carried (blue)
                fail = np.zeros(sh, np.uint8)
                fail[(cm == 0) & (R > 0)] = (0, 0, 255)
                fail[(cm > 0) & (R == 0)] = (255, 0, 0)
                fail[(cm > 0) & (lum < 100) & (cv2.erode(cm, el(3 * K)) == 0)] = (255, 160, 0)
                cv2.imwrite(os.path.join(DBG, f"fail_{key}_{k}.png"), fail)
            best = choose(res)
            chosen[key] = cands[best]
            report["methods"][key] = {"candidates": res, "chosen": best}
    # 3. assemble pieces: head underlap, body re-clothing, margins --------------------------------
    pieces = {}
    vis = img.copy()
    for f in ("gustave", "odette"):
        head = chosen[f"{f}_head"].copy()
        fore = chosen[f"{f}_fore"].copy()
        body = chosen[f"{f}_body"].copy()
        sil = fill_holes(head | fore | body)                # the whole figure at rest
        sil = cv2.morphologyEx(sil, cv2.MORPH_CLOSE, el(2 * K))
        # neck underlap: the head paper continues under the collar (inside the body, hidden at rest)
        under = disk(sh, NECK_PIN[f], UNDERLAP_R, K) & cv2.erode(body, el(4 * K)) & ~fore
        head_full = largest(head | under)
        # body: silhouette minus visible head minus forearm cap; the forearm's footprint inside the
        # torso is re-clothed with the figure's own crayon (cloned patch), so a raised arm leaves shirt
        torso = pm(sh, TORSO[f], K)
        body_rest = largest(sil & ~head & ~own[other[f]] & ~(fore & ~torso))
        hole = body_rest & fore
        cx0, cy0, cx1, cy1 = [int(v * K) for v in CLOTH[f]]
        patch = L[cy0:cy1, cx0:cx1]
        reps = (math.ceil(sh[0] / patch.shape[0]) + 1, math.ceil(sh[1] / patch.shape[1]) + 1)
        tile = np.tile(np.concatenate([patch, patch[:, ::-1]], 1), (reps[0], max(1, reps[1] // 2 + 1)))[:sh[0], :sh[1]]
        Lb = L.copy()
        Lb[hole > 0] = tile[hole > 0]
        # the cut sleeve shows a pen-and-scissor edge of Daumier's own contour where the forearm sat:
        # nothing is drawn; the body keeps the clone and only the true contour remains.
        body_piece = body_rest.copy()
        parts = {"head": (head_full, L, NECK_PIN[f]), "body": (body_piece, Lb, None), "fore": (fore & sil, L, ELBOW_PIN[f])}
        margin_zone = (cv2.dilate(sil, el(MARGIN * K)) > 0) & (sil == 0)
        for pn, (m, Lsrc, pin) in parts.items():
            key = f"{f}_{pn}"
            assert ncomp(m) == 1, key + " islands"
            bp, wp, ga = LEVELS[key]
            tone = levels(Lsrc, bp, wp, ga)
            rim = cv2.dilate(m, el(MARGIN * K))
            alpha = np.where((m > 0) | ((rim > 0) & margin_zone), 255, 0).astype(np.uint8)
            alpha = largest(alpha)
            a_s = cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), 0.6)  # cut paper edge, not pixel stairs
            gray = np.where(m > 0, tone, PAGE)
            ys, xs = np.nonzero(alpha)
            x0, y0, x1, y1 = xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3
            rgba = np.dstack([gray] * 3 + [a_s])[y0:y1, x0:x1].round().clip(0, 255).astype(np.uint8)
            fn = os.path.join(OUT, f"{key}.png")
            Image.fromarray(rgba, "RGBA").save(fn, optimize=True)
            inner = gray[m > 0]
            pieces[key] = {
                "file": os.path.relpath(fn, ROOT), "sha256": sha(fn), "offset": [int(x0), int(y0)],
                "size": [int(x1 - x0), int(y1 - y0)],
                "pin": None if pin is None else [round(pin[0] * K, 2), round(pin[1] * K, 2)],
                "pin_thumb": None if pin is None else list(pin),
                "method": report["methods"][key]["chosen"], "components": ncomp(m),
                "levels": {"black_point": bp, "white_point": wp, "gamma": ga,
                           "luminance": "0.70 R + 0.30 G (red filter; drops orange foxing)",
                           "map": "ink 13 .. page 251, linear then gamma; no threshold/posterize/sharpen"},
                "tone_stats": {"frac_below_L60": round(float((inner < 60).mean()), 4),
                               "frac_mid_60_200": round(float(((inner >= 60) & (inner < 200)).mean()), 4),
                               "frac_white_ge200": round(float((inner >= 200).mean()), 4)},
            }
            if pn == "body":
                pieces[key]["reclothed_px"] = int((hole > 0).sum())
                pieces[key]["reclothed_from_thumb_box"] = list(CLOTH[f])
            if pn == "head":
                pieces[key]["underlap_px"] = int((under & ~head > 0).sum())
        cnts, _ = cv2.findContours(sil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(vis, cnts, -1, (0, 0, 255) if f == "gustave" else (255, 0, 0), max(1, int(1.5 * K)))
        for pn in ("head", "fore"):
            c2, _ = cv2.findContours(parts[pn][0], cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(vis, c2, -1, (0, 200, 0), max(1, int(K)))
        np.save(os.path.join(DBG, f"sil_{f}.npy"), (sil > 0))
        cv2.imwrite(os.path.join(DBG, f"sil_{f}.png"), sil)
    # trespass invariant: no pixel of one figure's pieces inside the other's marked region
    for f in ("gustave", "odette"):
        for pn in ("head", "body", "fore"):
            a = np.asarray(Image.open(os.path.join(ROOT, pieces[f"{f}_{pn}"]["file"])))[..., 3]
            x0, y0 = pieces[f"{f}_{pn}"]["offset"]
            o = own[other[f]][y0:y0 + a.shape[0], x0:x0 + a.shape[1]]
            body_px = np.asarray(Image.open(os.path.join(ROOT, pieces[f"{f}_{pn}"]["file"])))[..., 0]
            assert not ((a > 200) & (o > 0) & (body_px < PAGE - 2)).any(), f"{f}_{pn} trespasses"
    # 4. backdrop set piece ----------------------------------------------------------------------
    bm = pm(sh, BACK_POLY, K)
    bp, wp, ga = LEVELS["backdrop"]
    btone = levels(L, bp, wp, ga)
    figs = np.zeros(sh[:2], np.uint8)
    for f in ("gustave", "odette"):
        figs |= cv2.imread(os.path.join(DBG, f"sil_{f}.png"), 0)
    btone[cv2.dilate(figs, el(3 * K)) > 0] = INK   # behind the figures the wall is solid ink
    ys, xs = np.nonzero(bm)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    rgba = np.dstack([btone] * 3 + [bm.astype(np.float32)])[y0:y1, x0:x1].round().clip(0, 255).astype(np.uint8)
    fn = os.path.join(OUT, "backdrop.png")
    Image.fromarray(rgba, "RGBA").save(fn, optimize=True)
    bin_ = btone[bm > 0]
    pieces["backdrop"] = {"file": os.path.relpath(fn, ROOT), "sha256": sha(fn), "offset": [int(x0), int(y0)],
                          "size": [int(x1 - x0), int(y1 - y0)], "pin": None, "method": "manual",
                          "components": ncomp(bm),
                          "levels": {"black_point": bp, "white_point": wp, "gamma": ga},
                          "tone_stats": {"frac_below_L60": round(float((bin_ < 60).mean()), 4)},
                          "note": "the print's own dark bed-curtain/wall crayon; spot-black set piece behind the heads (A B C)"}
    cv2.imwrite(os.path.join(DBG, "mattes_vis.jpg"), vis)
    report["pieces"] = pieces
    report["geometry_thumb"] = {"HEAD_VIS": HEAD_VIS, "FORE": FORE, "OWN": OWN, "ENV": ENV, "BACK_POLY": BACK_POLY,
                                "NECK_PIN": NECK_PIN, "ELBOW_PIN": ELBOW_PIN, "HAND": HAND, "FEET": FEET,
                                "CLOTH": CLOTH, "UNDERLAP_R": UNDERLAP_R, "ELBOW_CAP_R": ELBOW_CAP_R, "MARGIN": MARGIN}
    json.dump(report, open(os.path.join(OUT, "cut-report.json"), "w"), indent=1)
    print(json.dumps({k: (v["method"], v.get("tone_stats")) for k, v in pieces.items()}, indent=1))


if __name__ == "__main__":
    main()
