"""test-page.png: the hinge panel P4 (final drawing, identical to the shot's last frame) and its
reading-order neighbours P3 and P5, at print resolution 3200x1800. P1, P2, P6 are left as lit blank
paper (not built in this test). Also checks page = film on P4."""
import math, sys, subprocess
from pathlib import Path
import numpy as np, cv2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lightbox as lb, e4
from lightbox import facet, dense_poly, ellipse_pts, Card

SW = HERE.parent
page = lb.make_page()
shot = e4.Shot(page)
full = (0, 0, lb.PAGE_W, lb.PAGE_H)
rgb = shot.render(e4.DUR - 1 / e4.FPS, rect=full, page_mode=True).astype(np.float32)


def board_mask(R):
    b = np.ones((R.h, R.w), np.float32)
    for (a, bb, c, d) in lb.PANELS.values():
        b[max(bb - R.y0, 0):max(d - R.y0, 0), max(a - R.x0, 0):max(c - R.x0, 0)] = 0
    return b


def panel(k, build):
    x0, y0, x1, y1 = lb.PANELS[k]
    m = 60
    rect = (x0 - m, y0 - m, x1 - x0 + 2 * m, y1 - y0 + 2 * m)
    R = lb.Raster(*rect)
    paper = page[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]].copy()
    setd, groups, cards, paper = build(R, np.array([x0, y0], float), paper)
    out = lb.composite(R, paper, groups, setd, cards, board_mask(R))
    rgb[y0:y1, x0:x1] = out[m:-m, m:-m]


rh = e4.RightHand()


def hand_at(R, O_, target, h_deg, t=9.0):
    """right hand pose with its pinch on a world target (panel-local coords)"""
    P = rh.pose(t, target)
    h = h_deg * e4.DEG
    Rm = np.array([[math.cos(h), -math.sin(h)], [math.sin(h), math.cos(h)]])
    P.update(h=h, R=Rm, wrist=target - Rm @ rh.PINCH, idx_w=target, th_w=target + Rm @ np.array([-4.0, -12.0]))
    saveO = e4.O.copy(); e4.O[:] = O_
    D, pins, info = rh.draw(R, P, target)
    e4.O[:] = saveO
    return D


def build_p3(R, O3, paper):
    st = e4.Strip()
    setd = R.blank()
    off = np.array([-300.0, 330.0]) + O3
    for p in st.pieces[:-4]:                       # stair, balusters, rail, post (no floor seams on the stair)
        R.fill(setd, p + off)
    R.fill(setd, facet(dense_poly([(30, 470), (250, 470), (250, 805), (30, 805)]), 61) + O3)   # dark doorway, lower left
    rail = lambda x: 300 - 0.857 * (x - 700)
    tgt = np.array([1020.0 - 300, rail(1020) + 330 + 14])
    D = hand_at(R, O3, tgt, -128)
    dk, vl, ik = R.blank(), R.blank(), R.blank()
    Card('What time\nis it?', 50, tail_vec=(-400, -250), seed=31, rod_vec=(0, -1)).draw(R, dk, vl, ik, O3 + [330.0, 178.0])
    return setd, [(D, 1.9, (5, 4), 0.42)], [(dk, vl, ik)], paper


def build_p5(R, O5, paper):
    setd = R.blank()
    A = lambda pts: np.asarray(pts, float) + O5
    # interior light: the open refrigerator is a brighter patch of the lightbox
    ix0, iy0, ix1, iy1 = 95, 105, 405, 790
    yy, xx = np.mgrid[0:R.h, 0:R.w]
    gx, gy = xx + R.x0 - O5[0], yy + R.y0 - O5[1]
    inside = ((gx > ix0) & (gx < ix1) & (gy > iy0) & (gy < iy1)).astype(np.float32)
    inside = cv2.GaussianBlur(inside, (0, 0), 6)
    paper = np.minimum(paper * (1 + 0.12 * inside[..., None]), 252)
    cab = dense_poly([(55, 55), (440, 55), (440, 820), (55, 820)])
    m = R.blank(); R.fill(m, A(facet(cab, 71))); R.fill(m, A(facet(dense_poly([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)]), 72)), 0.0)
    setd = np.maximum(setd, m)
    for i, sy in enumerate((300, 480, 650)):
        R.fill(setd, A(facet(dense_poly([(ix0, sy), (ix1, sy), (ix1, sy + 12), (ix0, sy + 12)]), 73 + i)))
    jars = [(120, 300, 60, 110), (200, 300, 46, 80), (300, 300, 70, 60), (130, 480, 44, 95), (320, 480, 56, 120),
            (115, 650, 80, 70), (240, 650, 40, 100)]
    for j, (x, y, w, h) in enumerate(jars):
        R.fill(setd, A(facet(dense_poly([(x, y), (x, y - h + 12), (x + 8, y - h), (x + w - 8, y - h), (x + w, y - h + 12), (x + w, y)]), 80 + j)))
    door = dense_poly([(440, 55), (690, 20), (700, 820), (440, 820)])
    R.fill(setd, A(facet(door, 90)))
    R.fill(setd, A(facet(dense_poly([(610, 250), (622, 250), (624, 520), (612, 520)]), 91)), 0.0)  # light slot behind the handle
    tgt = np.array([600.0, 400.0])
    D = hand_at(R, O5, tgt, -96)
    dk, vl, ik = R.blank(), R.blank(), R.blank()
    Card('Thanks!', 52, tail_vec=(-320, 40), seed=41, rod_vec=(-1, 0)).draw(R, dk, vl, ik, O5 + [250.0, 150.0])
    return setd, [(D, 1.9, (5, 4), 0.42)], [(dk, vl, ik)], paper


panel(3, build_p3)
panel(5, build_p5)
out = np.clip(rgb, 0, 255).astype(np.uint8)
cv2.imwrite(str(SW / 'test-page.png'), cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
# page = film check on P4: last film frame vs page crop at the same size
f = subprocess.run(['ffmpeg', '-v', 'error', '-sseof', '-0.05', '-i', str(SW / 'test-shot.mp4'), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                   capture_output=True).stdout
fr = np.frombuffer(f, np.uint8)[:1280 * 720 * 3].reshape(720, 1280, 3).astype(np.float32)
x0, y0, w, h = e4.CROP
pc = cv2.resize(out[y0:y0 + h, x0:x0 + w], (1280, 720), interpolation=cv2.INTER_AREA).astype(np.float32)
print('page vs film last frame MAD per channel:', np.abs(pc - fr).mean(axis=(0, 1)))
