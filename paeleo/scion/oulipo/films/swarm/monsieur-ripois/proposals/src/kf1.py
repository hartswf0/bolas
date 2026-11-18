"""KF1 - Le canapé articulé: articulated photo-cutout puppetry on the Vachon lounge print.
Pieces (woman head, man head) are cut with GrabCut, pivoted at the neck, the vacated plate inpainted;
the handmade silver box is drawn as its own layer in the man's hand."""
import sys; sys.path.insert(0, __file__.rsplit('/', 1)[0])
import numpy as np, cv2, json
from PIL import Image, ImageDraw, ImageFilter
from common import *

W, H = 900, 720
src = Image.open(SRC + "8d04830.jpg").convert("L").crop((220, 340, 720, 740)).resize((W, H), Image.LANCZOS)
g = np.array(src)
rgb = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)

def cut(rect, keep_poly=None, iters=6, seed_poly=None):
    m = np.zeros(g.shape, np.uint8); bg = np.zeros((1, 65), np.float64); fg = np.zeros((1, 65), np.float64)
    if seed_poly is None:
        cv2.grabCut(rgb, m, rect, bg, fg, iters, cv2.GC_INIT_WITH_RECT)
    else:   # hand-seeded matte: inside the drawn outline = probable fg, its eroded core = fg
        poly = np.zeros(g.shape, np.uint8); cv2.fillPoly(poly, [np.array(seed_poly, np.int32)], 1)
        m[:] = cv2.GC_BGD; m[cv2.dilate(poly, np.ones((15, 15), np.uint8)) > 0] = cv2.GC_PR_BGD
        m[poly > 0] = cv2.GC_PR_FGD; m[cv2.erode(poly, np.ones((21, 21), np.uint8)) > 0] = cv2.GC_FGD
        cv2.grabCut(rgb, m, None, bg, fg, iters, cv2.GC_INIT_WITH_MASK)
    a = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    if keep_poly is not None:
        k = np.zeros_like(a); cv2.fillPoly(k, [np.array(keep_poly, np.int32)], 255); a &= k
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    a = cv2.GaussianBlur(a, (3, 3), 0)
    return a

# piece 1: woman's head (hat, hair, face) - keep polygon ends at the collar line
WOMAN_HEAD = [(215,135),(255,100),(300,92),(330,118),(352,140),(372,185),(390,225),(402,248),(390,262),(385,285),(360,300),(330,318),(280,318),(225,305),(195,280),(190,240),(200,180)]
wh = cut(None, seed_poly=WOMAN_HEAD, keep_poly=[(170, 88), (420, 88), (420, 300), (360, 318), (300, 322), (200, 300), (170, 260)])
# piece 2: man's head - ends at the shirt collar
mh = cut((495, 50, 160, 215), [(495, 50), (660, 50), (660, 230), (630, 250), (560, 262), (520, 240), (495, 200)])

pieces = [("woman_head", wh, (340, 312), -11.0), ("man_head", mh, (585, 255), 3.0)]
hole = np.zeros_like(g)
for _, a, _, _ in pieces: hole |= (a > 40).astype(np.uint8) * 255
hole = cv2.dilate(hole, np.ones((5, 5), np.uint8))
plate = cv2.inpaint(g, hole, 7, cv2.INPAINT_TELEA)
# the inpainted head region would read as a blur; we lay the cut original back first, then the rotated piece
canvas = Image.fromarray(plate).convert("RGBA")
for name, a, piv, ang in pieces:
    layer = Image.fromarray(g).convert("RGBA"); layer.putalpha(Image.fromarray(a))
    # paper-cut edge: slight dark rim + contact shadow, as with a card puppet laid on the plate
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0)); sh.putalpha(Image.fromarray((a * 0.35).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)))
    sh = sh.rotate(ang, center=piv, resample=Image.BICUBIC, translate=(4, 5))
    canvas.alpha_composite(sh)
    canvas.alpha_composite(layer.rotate(ang, center=piv, resample=Image.BICUBIC))

# handmade object: the borrowed silver box, open on her lap, the lining shows an empty ring slit
S = 4
def quad_fill(img, pts, c0, c1, axis=0):
    """fill a quad with a linear gradient (c0->c1) along x (axis 0) or y (axis 1) - a lit metal face"""
    m = Image.new("L", img.size, 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    xs = [p[axis] for p in pts]; lo, hi = min(xs), max(xs)
    ramp = np.linspace(0, 1, img.size[axis])[None, :] if axis == 0 else np.linspace(0, 1, img.size[1])[:, None]
    full = np.broadcast_to(ramp, (img.size[1], img.size[0]))
    t = np.clip((full * img.size[axis] - lo) / max(1, hi - lo), 0, 1)
    col = (c0 + (c1 - c0) * t).astype(np.uint8)
    img.paste(Image.fromarray(col), (0, 0), m)
bw, bh = 150 * S, 130 * S
box = Image.new("L", (bw, bh), 0); A = Image.new("L", (bw, bh), 0)
def P(pts): return [(x * S, y * S) for x, y in pts]
lid = P([(22, 30), (104, 2), (128, 46), (40, 72)])        # lid raised toward him; inside is a mirror
top = P([(40, 72), (128, 46), (146, 70), (58, 100)])       # opening, velvet
front = P([(58, 100), (146, 70), (146, 98), (60, 128)])
side = P([(40, 72), (58, 100), (60, 128), (42, 100)])
for q in (lid, top, front, side): ImageDraw.Draw(A).polygon(q, fill=255)
quad_fill(box, lid, 250.0, 150.0, 0)      # mirror lid: the lamp hot at one end
quad_fill(box, top, 40.0, 26.0, 0)        # velvet
quad_fill(box, front, 180.0, 96.0, 0)     # brushed silver front
quad_fill(box, side, 120.0, 80.0, 1)
d = ImageDraw.Draw(box)
for k in range(1, 5):                     # engine-turned bands on the front
    d.line(P([(59, 100 + k * 6), (146, 70 + k * 6)]), fill=120, width=S)
cush = P([(52, 76), (126, 52), (138, 68), (64, 94)])
d.polygon(cush, fill=48)
d.line(P([(84, 75), (102, 69)]), fill=6, width=3 * S)    # empty slit where the ring sat
d.line(P([(85, 72), (101, 66)]), fill=80, width=S)
for q in (lid, front, side): d.line(q + [q[0]], fill=40, width=S)
d.line(P([(58, 100), (146, 70)]), fill=245, width=2 * S)  # rim highlight
d.line(P([(24, 33), (102, 6)]), fill=255, width=S)
box = box.resize((bw // S, bh // S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.9)).point(lambda v: 30 + v * 0.8); A = A.resize((bw // S, bh // S), Image.LANCZOS)
bx, by = 505, 440
shadow = Image.new("RGBA", box.size, (0, 0, 0, 0)); shadow.putalpha(A.point(lambda v: v * 0.6).filter(ImageFilter.GaussianBlur(6)))
canvas.alpha_composite(shadow, (bx + 8, by + 12))
bl = box.convert("RGBA"); bl.putalpha(A)
canvas.alpha_composite(bl, (bx, by))

pic = np.array(canvas.convert("L"))
pic = cv2.GaussianBlur(pic, (0, 0), 0.6)
pic = grain(silver(pic), 6, 1)
im = Image.fromarray(pic)
# vignette like a studio key
yy, xx = np.mgrid[0:H, 0:W]; v = 1 - 0.32 * (((xx - W * 0.52) / W) ** 2 + ((yy - H * 0.4) / H) ** 2) * 2.2
im = Image.fromarray(np.clip(np.array(im) * v[..., None], 0, 255).astype(np.uint8))
fr = pillar(im)
subtitle(fr, "« Je la lui ai rendue, sa boîte. Rien n'y manquait. »", 640)
fr.save(OUT + "kf-1.png")
json.dump({"pieces": [{"name": n, "pivot": p, "deg": a} for n, _, p, a in pieces], "source": "LoC 2017831564"}, open(OUT + "src/kf1-rig.json", "w"), indent=1)
print("ok")
