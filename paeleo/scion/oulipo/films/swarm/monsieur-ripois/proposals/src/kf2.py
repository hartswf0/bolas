"""KF2 - Ombres du retour: articulated shadow theatre of the visitor's flashback (E2, his perspective).
Jointed card puppets posed by forward kinematics; far plane is the foraged Vachon lounge window,
thresholded and printed faintly on the back of the screen (multiplane)."""
import sys; sys.path.insert(0, __file__.rsplit('/', 1)[0])
import numpy as np, cv2, json, math
from PIL import Image, ImageDraw, ImageFilter
from common import *

W, H, S = 1280, 720, 3
INK = 0

def T(pts, ox, oy, ang=0.0, sx=1.0):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [((ox + (x * sx) * c - y * s) * S, (oy + (x * sx) * s + y * c) * S) for x, y in pts]

def limb(p0, ang, L, w0, w1):
    """capsule-ish card limb from p0 in direction ang (deg, screen coords); returns polygon and end point"""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang)); nx, ny = -s, c
    x0, y0 = p0; x1, y1 = x0 + c * L, y0 + s * L
    poly = [(x0 + nx * w0, y0 + ny * w0), (x1 + nx * w1, y1 + ny * w1), (x1 - nx * w1, y1 - ny * w1), (x0 - nx * w0, y0 - ny * w0)]
    return poly, (x1, y1)

def disc(d, x, y, r, fill):
    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=fill)

# ---------- the screen: backlit paper -----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - 640) / 760) ** 2 + ((yy - 330) / 470) ** 2)
lum = np.clip(1.0 - 0.75 * r ** 1.6, 0.18, 1.0)
paper = np.stack([238 * lum, 224 * lum, 196 * lum], -1)
fib = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.2) * 5
fib += cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 9) * 7
paper = paper + fib[..., None]

# far plane: foraged lounge window (LoC 2017831564) thresholded into a faint grey shadow behind the paper
win = np.array(Image.open(SRC + "8d04830.jpg").convert("L").crop((830, 120, 1010, 470)))
win = cv2.resize(win, (250, 486))
far = (win < 120).astype(np.float32)
far = cv2.GaussianBlur(far, (0, 0), 3.0) * 0.30
ex = np.minimum(np.linspace(0, 1, 250), np.linspace(1, 0, 250))[None, :] * 5; ey = np.minimum(np.linspace(0, 1, 486), np.linspace(1, 0, 486))[:, None] * 5
fe = np.minimum(ex, ey)
far *= np.clip(fe, 0, 1)        # out of focus: it sits further from the screen
fx, fy = 900, 40
paper[fy:fy + 486, fx:fx + 250] *= (1 - far[..., None])
paper = np.clip(paper, 0, 255).astype(np.uint8)

sil = Image.new("L", (W * S, H * S), 0)   # 255 = card (ink)
d = ImageDraw.Draw(sil)

# floor rail and a rug band (card)
d.rectangle([0, 612 * S, W * S, H * S], fill=255)
for k in range(40): disc(d, 20 + k * 32, 612, 5, 0)   # punched scallops on the rail edge = light dots
d = ImageDraw.Draw(sil)

# door frame on the right (mid plane) - he came through it
d.polygon(T([(0, 0), (26, 0), (26, 470), (0, 470)], 1110, 142), fill=255)
d.polygon(T([(0, 0), (150, 0), (150, 22), (0, 22)], 1110, 120), fill=255)
d.polygon(T([(0, 0), (8, 0), (8, 470), (0, 470)], 1250, 142), fill=255)
# standard lamp between them, its shade punched with a light slot
d.polygon(T([(-3, 0), (3, 0), (3, 330), (-3, 330)], 760, 282), fill=255)
d.polygon(T([(-40, 0), (40, 0), (56, 62), (-56, 62)], 760, 222), fill=255)
d.polygon(T([(-22, 0), (22, 0), (8, 14), (-8, 14)], 760, 602), fill=255)
d.rectangle([(760 - 44) * S, 244 * S, (760 + 44) * S, 250 * S], fill=0)

# ---------- woman (listener in his telling), wing chair, facing right ----------
cx, cy = 300, 430
chair_back = [(-74, -190), (-54, -204), (-34, -196), (-26, -50), (-70, -40), (-84, -120)]
seat = [(-80, -44), (84, -52), (92, -30), (86, 6), (-84, 10)]
d.polygon(T(chair_back, cx, cy), fill=255); d.polygon(T(seat, cx, cy), fill=255)
for lx in (-76, 76): d.polygon(T([(-5, 0), (5, 0), (lx * 0.03 + 7, 172), (lx * 0.03 - 3, 172)], cx + lx, cy + 8), fill=255)
for k in range(6): disc(d, cx - 58 + k * 2, cy - 180 + k * 24, 4, 0)   # punched lace down the chair back
d = ImageDraw.Draw(sil)
torso_w = [(-16, 0), (30, 0), (24, -30), (18, -58), (30, -92), (26, -112), (6, -124), (-14, -120), (-20, -92), (-12, -60), (-18, -28)]
d.polygon(T(torso_w, cx + 10, cy - 70), fill=255)
skirt = [(-30, 6), (40, -6), (96, -2), (108, 14), (104, 40), (100, 232), (124, 240), (126, 248), (82, 250), (76, 60), (40, 46), (-26, 44)]
d.polygon(T(skirt, cx + 4, cy - 70), fill=255)
neck = (cx + 22, cy - 190)
d.polygon(T([(-7, 0), (7, 0), (9, -30), (-5, -30)], *neck), fill=255)
head_w = [(-16, -28), (-4, -30), (8, -36), (14, -46), (20, -50), (16, -54), (19, -60), (16, -68), (12, -78), (0, -86), (-14, -84), (-22, -72), (-22, -50)]
d.polygon(T(head_w, *neck, sx=1.2), fill=255)
disc(d, neck[0] - 18, neck[1] - 84, 17, 255)       # chignon, as the reference
disc(d, neck[0] - 6, neck[1] - 96, 11, 255)
# earring: a drop on a thread, punched centre catches the light
d.line(T([(-2, -44), (-2, -30)], *neck), fill=255, width=2 * S); disc(d, neck[0] - 2, neck[1] - 26, 5, 255); disc(d, neck[0] - 2, neck[1] - 26, 2, 0)
d = ImageDraw.Draw(sil)
# her arm reaching to receive (FK: shoulder -> elbow -> wrist)
sh_w = (cx + 30, cy - 176)
ua, el = limb(sh_w, 62, 54, 9, 7); fa, wr = limb(el, -12, 60, 7, 5)
for p in (ua, fa): d.polygon([(x * S, y * S) for x, y in p], fill=255)
d.polygon(T([(0, -5), (22, -9), (26, -4), (14, 4), (0, 5)], *wr, ang=-12), fill=255)   # open palm

# ---------- the visitor (teller), standing, facing left ----------
hx, hy = 640, 400
legs = [[(-26, 0), (4, 0), (0, 95), (-6, 196), (-44, 210), (-46, 202), (-24, 194), (-26, 95)],
        [(0, 0), (26, 0), (28, 95), (26, 196), (12, 210), (-8, 208), (4, 196), (2, 95)]]
for L in legs: d.polygon(T(L, hx, hy), fill=255)
jacket = [(-36, 26), (32, 26), (34, -10), (30, -92), (24, -142), (8, -156), (-18, -156), (-30, -142), (-40, -100), (-38, -40)]
d.polygon(T(jacket, hx, hy), fill=255)
d.polygon(T([(-40, -112), (-30, -108), (-36, -100)], hx, hy), fill=0)   # lapel notch, cut out
neck_m = (hx - 6, hy - 154)
d.polygon(T([(-8, 0), (8, 0), (8, -22), (-6, -22)], *neck_m), fill=255)
head_m = [(-2, -16), (12, -18), (16, -32), (18, -52), (14, -64), (2, -76), (-10, -80), (-20, -72), (-22, -62), (-21, -56),
          (-30, -46), (-23, -42), (-24, -36), (-28, -30), (-23, -27), (-24, -20), (-16, -12)]
d.polygon(T(head_m, *neck_m), fill=255)
d.polygon(T([(-22, -66), (-14, -84), (6, -86), (18, -66), (10, -74)], *neck_m), fill=255)    # slicked quiff
# arm toward her, holding the box (FK chain angles recorded below)
RIG = {"m_front": {"shoulder": [hx - 18, hy - 138], "upper": 118, "fore": 186}, "m_back": {"shoulder": [hx + 10, hy - 136], "upper": 84, "fore": 196},
       "w_arm": {"shoulder": list(sh_w), "upper": 62, "fore": -12}}
ua, el = limb(tuple(RIG["m_front"]["shoulder"]), RIG["m_front"]["upper"], 64, 11, 9)
fa, wr_m = limb(el, RIG["m_front"]["fore"], 60, 9, 7)
for p in (ua, fa): d.polygon([(x * S, y * S) for x, y in p], fill=255)
d.polygon(T([(0, -7), (-16, -8), (-20, 0), (-10, 8), (0, 7)], *wr_m), fill=255)
# the box in his hand: open, lid back, the ring standing in its slit (his claim: it was there)
bx, by = wr_m[0] - 52, wr_m[1] - 18
d.polygon(T([(0, 0), (44, -2), (44, 20), (2, 22)], bx, by), fill=255)             # body
d.polygon(T([(2, 0), (40, -2), (50, -34), (14, -36)], bx, by), fill=255)          # raised lid
d.polygon(T([(10, -8), (38, -10), (44, -28), (18, -30)], bx, by), fill=0)         # lid's mirror: cut away, it glows
d.ellipse([(bx + 16) * S, (by - 15) * S, (bx + 30) * S, (by + 1) * S], fill=255)   # ring
d.ellipse([(bx + 19) * S, (by - 12) * S, (bx + 27) * S, (by - 2) * S], fill=0)
disc(d, bx + 23, by - 16, 3, 255)
# the far arm: bent behind his back - the gesture the telling hides; only the elbow juts past the jacket
ua, el = limb(tuple(RIG["m_back"]["shoulder"]), RIG["m_back"]["upper"], 58, 10, 9)
fa, wr_b = limb(el, RIG["m_back"]["fore"], 46, 9, 7)
for p in (ua, fa): d.polygon([(x * S, y * S) for x, y in p], fill=255)
d.ellipse([(el[0] - 9) * S, (el[1] - 9) * S, (el[0] + 9) * S, (el[1] + 9) * S], fill=255)

# rivets at the joints: tiny light pin-holes, as on Reiniger's card figures
for p in [RIG["m_front"]["shoulder"], el, RIG["w_arm"]["shoulder"]]:
    disc(d, p[0], p[1], 1.4, 0)

sil = sil.resize((W, H), Image.LANCZOS)
a = np.array(sil).astype(np.float32) / 255
# card sits on the screen: tiny halo where light leaks around the edge
halo = cv2.GaussianBlur(a, (0, 0), 2.2)
ink = np.array([20, 15, 12], np.float32)
img = paper.astype(np.float32) * (1 - a[..., None]) + ink * a[..., None]
img *= (1 - 0.18 * np.clip(halo - a, 0, 1))[..., None]
img = grain(np.clip(img, 0, 255).astype(np.uint8), 5, 2)
fr = Image.fromarray(img)
dr = ImageDraw.Draw(fr)
f = font(SERIF_I, 26); dr.text((560, 60), "— selon lui —", font=f, fill=(88, 64, 44))
subtitle(fr, "« Elle l'a ouverte devant moi. La bague y était. »", 650)
fr.save(OUT + "kf-2.png")
json.dump(RIG, open(OUT + "src/kf2-rig.json", "w"), indent=1)
print("ok")
