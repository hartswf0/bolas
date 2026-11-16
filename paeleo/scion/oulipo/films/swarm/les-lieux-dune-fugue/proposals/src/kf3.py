"""KF3 La façade de papier (cutout collage + multiplane).
Stone: blocks and carved jambs cut from the Highsmith Columbus doorway (LoC 2010719611).
Door leaves: cut from the Highsmith Savannah Custom House door (LoC 2014630119).
Remembered bench plane: Highsmith Sacramento park bench (LoC 2013633886); the bench itself
is a separate GrabCut cutout on its own plane.
Each piece is a cut paper part with a cut edge and a depth-dependent shadow; the door
leaves are hinged cards rotated about their jambs (forward kinematics, projected)."""
import sys
sys.path.insert(0, sys.path[0])
from common import *
import cv2

W, H = 1280, 720
rng = np.random.default_rng(3)
col = load(SRC + "/hs_10700_10776.jpg")
sav = load(SRC + "/hs_25800_25800.jpg")
sac = load(SRC + "/bench/sac_23429.jpg")

canvas = np.zeros((H, W, 3), np.float32)
OX0, OY0, OX1, OY1 = 486, 168, 794, 700          # the opening
CAM = np.array([6.0, -2.0])                        # this frame's camera offset (multiplane)


def paste(rgb, alpha, x, y, depth, shadow=True):
    """alpha-composite a cut piece; depth 0 = front, 1 = far. Parallax by depth."""
    global canvas
    dx = int(round(x + CAM[0] * (1 - depth)))
    dy = int(round(y + CAM[1] * (1 - depth)))
    h, w = alpha.shape
    x0, y0 = max(dx, 0), max(dy, 0)
    x1, y1 = min(dx + w, W), min(dy + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    a = alpha[y0 - dy:y1 - dy, x0 - dx:x1 - dx][..., None]
    c = rgb[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    if shadow:
        off = int(3 + 7 * (1 - depth))
        sh = np.zeros((H, W), np.float32)
        sx0, sy0 = min(max(x0 + off, 0), W), min(max(y0 + off, 0), H)
        sx1, sy1 = min(x1 + off, W), min(y1 + off, H)
        sh[sy0:sy1, sx0:sx1] = alpha[y0 - dy:y0 - dy + sy1 - sy0, x0 - dx:x0 - dx + sx1 - sx0]
        sh = cv2.GaussianBlur(sh, (0, 0), 2.5 + 4 * (1 - depth)) * 0.55
        canvas *= (1 - sh[..., None])
    canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - a) + c * a


def cut_edge(rgb, alpha, lighten=0.16):
    """paper cut edge: a thin lighter rim where the scissors went through."""
    er = cv2.erode((alpha > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8), 2)
    rim = ((alpha > 0.5) & (er == 0))[..., None]
    fib = cv2.GaussianBlur(rng.normal(0, 1, alpha.shape).astype(np.float32), (0, 0), 0.7)[..., None]
    out = rgb * (1 + 0.025 * fib)
    return np.where(rim, np.clip(out + lighten, 0, 1), out)


def ragged(h, w, amt=1.2):
    a = np.ones((h, w), np.float32)
    n = rng.normal(0, amt, 4 * max(h, w))
    for i in range(h):
        a[i, :max(0, int(abs(n[i])))] = 0
        a[i, w - max(1, int(abs(n[i + h]))):] = 0
    for j in range(w):
        a[:max(0, int(abs(n[2 * h + j % (2 * w)]))), j] = 0
        a[h - max(1, int(abs(n[3 * h + j % w]))):, j] = 0
    return cv2.GaussianBlur(a, (0, 0), 0.5)


# ------------------------------------------------ plane 3 (far): remembered park
far = fit_crop(sac, (1000, 420, 1000 + 760, 420 + 1310), (OX1 - OX0 + 40, OY1 - OY0 + 40))
fl = lum(far)
far = np.stack([fl * 0.80 + 0.07, fl * 0.84 + 0.07, fl * 0.90 + 0.09], -1) * 0.9
canvas[:] = 0.05
canvas[OY0 - 20:OY1 + 20, OX0 - 20:OX1 + 20] = far

# ------------------------------------------------ plane 2: the bench, cut out
bx0, by0, bx1, by1 = 715, 995, 985, 1240
bimg = sac[by0:by1, bx0:bx1].copy()
b8 = (np.clip(bimg, 0, 1) * 255).astype(np.uint8)[..., ::-1].copy()
gm = np.zeros(b8.shape[:2], np.uint8)
bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
cv2.grabCut(b8, gm, (12, 8, b8.shape[1] - 24, b8.shape[0] - 26), bg, fg, 6, cv2.GC_INIT_WITH_RECT)
bm = np.where((gm == 1) | (gm == 3), 1.0, 0.0).astype(np.float32)
bm = cv2.morphologyEx(bm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
bl = lum(bimg)
bench = np.stack([bl * 0.84 + 0.05, bl * 0.86 + 0.05, bl * 0.92 + 0.06], -1)
sc = 0.78
bench = cv2.resize(bench, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
bm = cv2.GaussianBlur(cv2.resize(bm, None, fx=sc, fy=sc), (0, 0), 0.6)
bench = cut_edge(bench, bm, 0.10)
paste(bench, bm, 545, 500, depth=0.6)

# depth haze between bench plane and door (multiplane glass with a little dust)
canvas[OY0:OY1, OX0:OX1] = canvas[OY0:OY1, OX0:OX1] * 0.88 + 0.03

# ------------------------------------------------ plane 1: door leaves, hinged inward
dl = sav[75:1880, 232:714]
dr = sav[75:1880, 716:1190]
lw = (OX1 - OX0) // 2
lh = OY1 - OY0


def leaf(img, theta, left=True):
    """rotate a card about its hinge by theta (deg), project with a pinhole camera."""
    h0, w0 = img.shape[:2]
    src = np.float32([[0, 0], [w0, 0], [w0, h0], [0, h0]])
    th = np.radians(theta)
    f = 1100.0
    z = lw * np.sin(th)                       # free edge recedes
    xf = lw * np.cos(th)
    k = f / (f + z)
    cy = lh / 2
    if left:
        dst = np.float32([[0, 0], [xf * k, cy - cy * k], [xf * k, cy + cy * k], [0, lh]])
    else:
        dst = np.float32([[lw - xf * k, cy - cy * k], [lw, 0], [lw, lh], [lw - xf * k, cy + cy * k]])
    M = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, M, (lw, lh), flags=cv2.INTER_AREA)
    a = cv2.warpPerspective(np.ones((h0, w0), np.float32), M, (lw, lh))
    shade = 0.62 + 0.38 * np.cos(th)          # leaf turns away from the street light
    return out * shade, a


# warm the iron toward the reference's dark warm door
def door_tone(x):
    L = lum(x)
    return np.stack([L * 0.95 + 0.02, L * 0.86 + 0.02, L * 0.72 + 0.015], -1) * 0.75


lL, aL = leaf(door_tone(dl), 58, True)
lR, aR = leaf(door_tone(dr), 64, False)
paste(cut_edge(lL, aL, 0.08), aL, OX0, OY0, depth=0.35)
paste(cut_edge(lR, aR, 0.08), aR, OX0 + lw, OY0, depth=0.35)

# ------------------------------------------------ plane 0 (front): the stone facade, cut in blocks
stone_src = warm(col[60:940, 1240:1388], keep=0.2)        # plain ashlar to the right of the door
facade = np.zeros((H, W, 3), np.float32)
fa = np.ones((H, W), np.float32)
fa[OY0:OY1, OX0:OX1] = 0
rows = [0, 92, 180, 268, 356, 444, 532, 620, 720]
for r in range(len(rows) - 1):
    y0, y1 = rows[r], rows[r + 1]
    x = -int(rng.integers(20, 180))
    while x < W:
        w = int(rng.integers(150, 260))
        sy = int(rng.integers(0, stone_src.shape[0] - (y1 - y0) - 1))
        sx = int(rng.integers(0, stone_src.shape[1] - 100))
        piece = cv2.resize(stone_src[sy:sy + (y1 - y0), sx:sx + 100], (w, y1 - y0))
        piece = piece * (0.94 + 0.10 * rng.random())
        a = ragged(y1 - y0 - 3, w - 3)
        p = np.zeros((y1 - y0, w, 3), np.float32); p[1:-2, 1:-2] = cut_edge(piece[1:-2, 1:-2], a, 0.07)
        A = np.zeros((y1 - y0, w), np.float32); A[1:-2, 1:-2] = a
        xs0, xs1 = max(x, 0), min(x + w, W)
        if xs1 > xs0:
            reg = slice(xs0 - x, xs1 - x)
            facade[y0:y1, xs0:xs1] = facade[y0:y1, xs0:xs1] * (1 - A[:, reg, None]) + p[:, reg] * A[:, reg, None]
        x += w
# mortar gaps read dark between cut blocks
gap = (facade.sum(-1) == 0)
facade[gap] = (0.30, 0.26, 0.20)
canvas_mask = fa
paste(facade, fa, -6, 2, depth=0.0)

# carved surround: jambs and lintel cut from the Columbus doorway, warm-toned, raised layer
jl = warm(col[330:1110, 462:628], keep=0.2)
jr = warm(col[330:1110, 1082:1228], keep=0.2)
li = warm(col[120:335, 462:1228], keep=0.2)
jw = 120
for img, x in [(jl, OX0 - jw), (jr, OX1)]:
    p = cv2.resize(img, (jw, OY1 - OY0 + 4))
    a = ragged(*p.shape[:2], amt=1.0)
    paste(cut_edge(p, a), a, x, OY0 - 2, depth=-0.05)
p = cv2.resize(li, (OX1 - OX0 + 2 * jw + 20, 150))
a = ragged(*p.shape[:2], amt=1.0)
paste(cut_edge(p, a), a, OX0 - jw - 10, OY0 - 150, depth=-0.08)

# a little hand-cut number plaque, as on Paris carriage doors (handmade, not copied)
pl = np.zeros((34, 46, 3), np.float32) + (0.12, 0.14, 0.22)
pim = Image.fromarray((pl * 255).astype(np.uint8)); dd = ImageDraw.Draw(pim)
dd.rectangle((2, 2, 43, 31), outline=(220, 220, 210), width=1)
dd.text((23, 17), "7", font=font("sans", 22), fill=(235, 235, 225), anchor="mm")
pl = np.asarray(pim).astype(np.float32) / 255
pa = ragged(34, 46, 0.6)
paste(cut_edge(pl, pa, 0.05), pa, OX1 + jw + 70, 250, depth=-0.06)

# warm key light from upper left over the whole tabletop; slight vignette
yy, xx = np.mgrid[0:H, 0:W]
light = 1.04 - 0.16 * ((xx / W) * 0.6 + (yy / H) * 0.4) - 0.12 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
canvas *= light[..., None]

im = Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8))
d = ImageDraw.Draw(im)
mono = font("mono", 14)
d.rectangle((0, 0, W, 30), fill=(18, 15, 12))
d.text((18, 7), "P01 porte (papier découpé) · battants 58°/64° · plan 3: P03 banc, souvenir", font=mono, fill=(228, 216, 190))
d.text((W - 120, 7), "00:34 / 00:56", font=mono, fill=(228, 216, 190))
im.save(OUT + "/kf-3.png")
print("ok")
