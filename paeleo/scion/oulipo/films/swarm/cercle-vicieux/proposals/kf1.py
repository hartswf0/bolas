"""KF1 'Union Station cutouts': page 4 (D C / B A) at 56.0 s, the closing A.
Gilliam/Reiniger cutout puppetry from FSA/OWI photographs (LoC, PD), each piece
GrabCut-extracted, printed to ink (black / dot screen / paper) and pasted into hand-inked panels.
Run: python3 -I kf1.py"""
import sys, math
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/cercle-vicieux/proposals")
from kf_common import *

OUT = ROOT + "/films/swarm/cercle-vicieux/proposals/"
CUT = SRC + "/cercle-vicieux/cutouts/"
import os; os.makedirs(CUT, exist_ok=True)


def grabcut(path, rect, poly=None, iters=6):
    im = cv2.imread(path)
    mask = np.zeros(im.shape[:2], np.uint8)
    if poly is not None:
        mask[:] = cv2.GC_BGD
        cv2.fillPoly(mask, [np.array(poly, np.int32)], cv2.GC_PR_FGD)
        bg = np.zeros((1, 65), np.float64); fg = np.zeros((1, 65), np.float64)
        cv2.grabCut(im, mask, None, bg, fg, iters, cv2.GC_INIT_WITH_MASK)
    else:
        bg = np.zeros((1, 65), np.float64); fg = np.zeros((1, 65), np.float64)
        cv2.grabCut(im, mask, rect, bg, fg, iters, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    # keep the largest piece, close small holes: a paper cutout has no specks
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = np.where(lab == big, 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return im, m


def paste_piece(canvas, gray, mask, box_src, dst_xy, scale, angle=0, pivot=None, outline=4, lo=.30, hi=.66, flip=False):
    """Print a cut piece to ink and paste it with an ink scissor-edge.
    angle/pivot rotate the piece about its joint (forward kinematics)."""
    x0, y0, x1, y1 = box_src
    g = gray[y0:y1, x0:x1]; m = mask[y0:y1, x0:x1]
    if flip:
        g = g[:, ::-1]; m = m[:, ::-1]
    w, h = int((x1 - x0) * scale), int((y1 - y0) * scale)
    g = cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR)
    pad = int(max(w, h) * 0.6)
    G = np.full((h + 2 * pad, w + 2 * pad), 255, np.uint8); M = np.zeros_like(G)
    G[pad:pad + h, pad:pad + w] = g; M[pad:pad + h, pad:pad + w] = m
    if angle:
        px, py = pivot
        c = (pad + (px - x0) * scale, pad + (py - y0) * scale)
        R = cv2.getRotationMatrix2D(c, angle, 1.0)
        G = cv2.warpAffine(G, R, G.shape[::-1], borderValue=255)
        M = cv2.warpAffine(M, R, M.shape[::-1], borderValue=0)
    P = ink_print(G, lo, hi, dot=7)
    M = (M > 127).astype(np.uint8)
    edge = cut_line(M * 255, outline)
    a = np.array(canvas)
    ox, oy = dst_xy[0] - pad, dst_xy[1] - pad
    H_, W_ = a.shape
    ys, xs = slice(max(0, oy), min(H_, oy + G.shape[0])), slice(max(0, ox), min(W_, ox + G.shape[1]))
    sy, sx = slice(ys.start - oy, ys.stop - oy), slice(xs.start - ox, xs.stop - ox)
    reg = a[ys, xs]
    reg[edge[sy, sx]] = INK
    mm = M[sy, sx] > 0
    reg[mm] = P[sy, sx][mm]
    a[ys, xs] = reg
    return Image.fromarray(a)


def plate(canvas, gray, src_box, box, lo=.28, hi=.62, dot=7):
    x0, y0, x1, y1 = box
    g = fit_crop(gray, src_box, x1 - x0, y1 - y0)
    p = ink_print(g, lo, hi, dot)
    a = np.array(canvas); a[y0:y1, x0:x1] = p
    return Image.fromarray(a)


def clip_to(canvas, box, fn):
    """Draw into a panel without spilling across the gutter."""
    x0, y0, x1, y1 = box
    sub = Image.new("L", (x1 - x0, y1 - y0), PAPER)
    full = canvas.copy()
    full = fn(full)
    a = np.array(canvas); b = np.array(full)
    a[y0:y1, x0:x1] = b[y0:y1, x0:x1]
    return Image.fromarray(a)


def door(d, x, y, w, h, seed):
    d.rectangle([x, y, x + w, y + h], fill=INK)
    brush_poly(d, [(x - 14, y - 14), (x + w + 14, y - 14), (x + w + 14, y + h)], 8, seed, closed=False)
    brush_poly(d, [(x - 14, y + h), (x - 14, y - 14)], 8, seed + 1, closed=False)
    d.rectangle([x + w * .22, y - 70, x + w * .78, y - 30], fill=PAPER)
    brush_poly(d, [(x + w * .22, y - 70), (x + w * .78, y - 70), (x + w * .78, y - 30), (x + w * .22, y - 30)], 4, seed + 2)
    d.ellipse([x + w - 40, y + h * .5, x + w - 22, y + h * .5 + 18], fill=PAPER)


def build():
    cond_p = LOC % "2017844115"
    im, cm = grabcut(cond_p, (330, 285, 330, 730))
    head = np.array([(468, 308), (540, 296), (594, 338), (562, 372), (552, 420), (548, 470), (600, 470), (480, 470), (472, 420), (456, 378)], np.int32)
    hm = np.zeros_like(cm); cv2.fillPoly(hm, [head], 255)
    # GrabCut lost the cap and face against the pale wall: refine inside the head polygon only
    hg = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    cm = cm | hm
    cv2.imwrite(CUT + "conductor_mask.png", cm)
    cg = clahe(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 1.6)
    # forearm piece (elbow -> hand with watch), cut out of the body mask
    arm_poly = np.array([(455, 495), (560, 478), (640, 505), (662, 585), (615, 600), (548, 552), (455, 548)], np.int32)
    am = np.zeros_like(cm); cv2.fillPoly(am, [arm_poly], 255); am = am & cm
    body = cm.copy(); body[am > 0] = 0
    # the coat where the arm was: the puppet's underlayer is black coat paper
    under = np.zeros_like(cm); cv2.fillPoly(under, [arm_poly], 255); under &= cv2.dilate(cm, np.ones((5, 5), np.uint8))
    cg_body = cg.copy(); cg_body[under > 0] = 25; body[under > 0] = 255

    vis_p = SRC + "/la-machine-a-tuer-le-temps/loc_2017843935.jpg"
    vpoly = [(705, 385), (750, 380), (768, 420), (762, 470), (800, 500), (835, 540), (845, 640), (850, 780), (800, 790), (800, 960), (680, 965), (672, 850), (640, 820), (628, 700), (640, 560), (690, 490), (700, 440)]
    vim = cv2.imread(vis_p)
    vpm = np.zeros(vim.shape[:2], np.uint8); cv2.fillPoly(vpm, [np.array(vpoly, np.int32)], 255)
    gm = np.full(vpm.shape, cv2.GC_BGD, np.uint8); gm[vpm > 0] = cv2.GC_PR_FGD
    gm[cv2.erode(vpm, np.ones((5, 5), np.uint8), iterations=12) > 0] = cv2.GC_FGD
    bgm = np.zeros((1, 65)); fgm = np.zeros((1, 65))
    cv2.grabCut(vim, gm, None, bgm, fgm, 5, cv2.GC_INIT_WITH_MASK)
    vm = np.where((gm == 1) | (gm == 3), 255, 0).astype(np.uint8) & vpm
    vm = cv2.morphologyEx(vm, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    cv2.imwrite(CUT + "visitor_mask.png", vm)
    vg = clahe(cv2.cvtColor(vim, cv2.COLOR_BGR2GRAY), 1.4)

    redcap = clahe(load_gray(LOC % "2017843923"), 1.5)
    hall = clahe(load_gray(SRC + "/la-machine-a-tuer-le-temps/loc_2017843779.jpg"), 2.0)
    keyg = load_gray(SRC + "/la-belle-hortense/skeletonkey.png")
    keym = np.where(keyg < 200, 255, 0).astype(np.uint8)
    keym = cv2.morphologyEx(keym, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    c = Image.new("L", (W, H), PAPER)
    d = ImageDraw.Draw(c)
    G = 44
    X0, X1, Y0, Y1 = 90, 2470, 60, 1330
    cw = (X1 - X0 - G) // 2; ch = (Y1 - Y0 - G) // 2
    boxes = {"D": (X0, Y0, X0 + cw, Y0 + ch), "C": (X0 + cw + G, Y0, X1, Y0 + ch),
             "B": (X0, Y0 + ch + G, X0 + cw, Y1), "A": (X0 + cw + G, Y0 + ch + G, X1, Y1)}

    # ---- D: the envelope on the bench plank, the key half out
    bx = boxes["D"]
    c = plate(c, hall, (560, 700, 900, 880), bx, lo=.33, hi=.70, dot=9)
    d = ImageDraw.Draw(c)
    ex, ey = bx[0] + 300, bx[1] + 200
    env = [(ex, ey), (ex + 520, ey - 40), (ex + 560, ey + 300), (ex + 40, ey + 340)]
    d.polygon(env, fill=PAPER); brush_poly(d, env, 7, 31)
    brush_poly(d, [(ex, ey), (ex + 290, ey + 180), (ex + 520, ey - 40)], 5, 32, closed=False)
    d.ellipse([ex + 262, ey + 150, ex + 318, ey + 206], fill=INK)
    c = paste_piece(c, keyg, keym, (0, 0, 480, 720), (ex + 250, ey - 150), 0.62, angle=-62, pivot=(240, 360), outline=3, lo=.5, hi=.8)
    c = balloon(c, "...", bx[0] + 190, bx[1] + 110, 40, (bx[0] + 330, bx[1] + 230), seed=40, maxc=6)

    # ---- C: the porter's question (red cap portrait)
    bx = boxes["C"]
    c = plate(c, redcap, (150, 120, 900, 560), bx, lo=.30, hi=.62, dot=7)
    c = balloon(c, "Who sent you?", bx[0] + 250, bx[1] + 120, 44, (bx[0] + 420, bx[1] + 250), seed=50, maxc=14)

    # ---- B: visitor by the bench, waiting
    bx = boxes["B"]
    c = plate(c, hall, (500, 380, 1009, 960), bx, lo=.26, hi=.60, dot=7)
    def pB(cc):
        cc = paste_piece(cc, vg, vm, (620, 370, 860, 975), (bx[0] + 140, bx[1] + 40), 1.0, lo=.22, hi=.88)
        dd = ImageDraw.Draw(cc)
        e = [(bx[0] + 300, bx[1] + 420), (bx[0] + 440, bx[1] + 408), (bx[0] + 448, bx[1] + 500), (bx[0] + 308, bx[1] + 512)]
        dd.polygon(e, fill=PAPER); brush_poly(dd, e, 6, 61)
        brush_poly(dd, [e[0], (bx[0] + 375, bx[1] + 462), e[1]], 4, 62, closed=False)
        return cc
    c = clip_to(c, bx, pB)
    c = balloon(c, "I was only told to wait on the bench.", bx[0] + 770, bx[1] + 140, 40, (bx[0] + 470, bx[1] + 230), seed=60, maxc=15)

    # ---- A: the closing shout, now a guard between visitor and the door
    bx = boxes["A"]
    d = ImageDraw.Draw(c)
    d.rectangle(bx, fill=PAPER)
    # handmade ink set: floor line, wall hatch, the service door
    for i in range(0, bx[2] - bx[0], 40):
        brush_poly(d, [(bx[0] + i, bx[1] + 20), (bx[0] + i - 60, bx[1] + 380)], 2, 70 + i, closed=False)
    d.rectangle([bx[0], bx[1] + 380, bx[2], bx[3]], fill=PAPER)
    brush_poly(d, [(bx[0], bx[1] + 380), (bx[2], bx[1] + 380)], 6, 71, closed=False)
    door(d, bx[0] + 120, bx[1] + 120, 200, 270, 72)
    letter_line_res = letter_line(c, "SERVICE", bx[0] + 220, bx[1] + 70, 24, 73)
    c = letter_line_res[0]
    def pA(cc):
        cc = paste_piece(cc, vg, vm, (620, 370, 860, 975), (bx[0] + 470, bx[1] + 200), 0.70, lo=.22, hi=.88)
        # porter: body piece, then forearm rotated up about the elbow (FK joint)
        cc = paste_piece(cc, cg_body, body, (320, 280, 690, 1010), (bx[0] + 700, bx[1] - 10), 0.92, lo=.26, hi=.6)
        cc = paste_piece(cc, cg, am, (440, 470, 680, 610), (bx[0] + 700 + int(120 * .92), bx[1] - 10 + int(190 * .92)), 0.92,
                         angle=-12, pivot=(640, 560), outline=4, lo=.26, hi=.6)
        return cc
    c = clip_to(c, bx, pA)
    c = balloon(c, "You! Stay right there.", bx[0] + 525, bx[1] + 112, 44, (bx[0] + 815, bx[1] + 95), seed=80, maxc=12)

    d = ImageDraw.Draw(c)
    for k, bx in boxes.items():
        panel_frame(d, bx, seed=ord(k), width=9)
    c, _ = letter_line(c, "- 4 -", W // 2, 1395, 26, 90)
    return finish(c, OUT + "kf-1.png")


if __name__ == "__main__":
    build()
