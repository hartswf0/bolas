"""Repair round 2: recut the Clichy tram V along its real outline (canopy, body, front platform, undercarriage and
wheels down to the road), from the full-size LoC master of P2 (2002707975, 3650 px). The bowler-hatted man and the
gas lamp standing in front of the tram in the photograph are kept whole on the same card (no retouching); they
reach the frame bottom at Chatelet. Hand polygons (full-res px) seed cv2.grabCut. Run: python3 -I tram_recut.py"""
import json, sys, hashlib
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw

SRC = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/zazie-dans-le-metro")
OUT = SRC / "editor"
im = np.asarray(Image.open(SRC / "test-shot/hires/09974u_full.png").convert("RGB"))
X0, Y0, X1, Y1 = 1150, 1800, 1760, 2210          # working crop in the master
c = im[Y0:Y1, X0:X1].copy()

def P(pts2x):                                     # 2x-crop coords (review crop at 1100,1830) -> working crop px
    return [((x / 2 + 1100) - X0, (y / 2 + 1830) - Y0) for x, y in pts2x]

TRAM = P([(150, 140), (230, 100), (380, 56), (1000, 48), (1240, 104), (1248, 120), (1250, 300), (1252, 470),
          (1160, 492), (1155, 578), (380, 580), (378, 505), (252, 505), (246, 148), (150, 150)])
MAN = P([(548, 372), (596, 372), (604, 420), (640, 452), (646, 540), (636, 620), (612, 640), (606, 790), (512, 798),
         (500, 670), (462, 660), (460, 540), (478, 450), (536, 428)])
LAMP = P([(630, -30), (720, -30), (726, 120), (700, 140), (692, 560), (712, 600), (730, 780), (596, 790), (640, 600),
          (660, 560), (652, 140), (626, 120)])
CORE = P([(420, 130), (1220, 130), (1220, 470), (420, 470)])
h, w = c.shape[:2]
def mask_of(polys, val=255):
    m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
    for q in polys:
        d.polygon(q, fill=val)
    return np.asarray(m) > 0
union = mask_of([TRAM, MAN, LAMP])
gc = np.full((h, w), cv2.GC_BGD, np.uint8)
gc[union] = cv2.GC_PR_FGD
k = np.ones((9, 9), np.uint8)
inner = cv2.erode(union.astype(np.uint8), k, iterations=2) > 0
gc[inner] = cv2.GC_FGD
gc[mask_of([CORE])] = cv2.GC_FGD
CANOPY = P([(156, 140), (380, 62), (1000, 54), (1232, 108), (1232, 126), (156, 147)])
gc[mask_of([CANOPY])] = cv2.GC_FGD
# undercarriage band: the road seen between the wheels is background (bright, low-chroma pixels)
UNDER = mask_of([P([(380, 492), (1160, 492), (1160, 590), (380, 590)])]) & ~mask_of([MAN, LAMP])
lum = c.astype(np.float32) @ np.array([0.299, 0.587, 0.114])
gc[UNDER & (lum > 150)] = cv2.GC_BGD
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(cv2.cvtColor(c, cv2.COLOR_RGB2BGR), gc, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
fg = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
fg &= union.astype(np.uint8)
fg[UNDER & (lum > 150)] = 0
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)       # keep the main body only
keep = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
fg = (lab == keep).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
fg = cv2.erode(fg, np.ones((3, 3), np.uint8), 1)
a = cv2.GaussianBlur(fg.astype(np.float32) * 255, (0, 0), 0.6)
ys, xs = np.nonzero(a > 8); bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
rgba = np.dstack([c, a.astype(np.uint8)])[by0:by1, bx0:bx1]
Image.fromarray(rgba, "RGBA").save(OUT / "V2_tram_raw.png")
# P2's own grade (forage/plate_stats.json: gamma 1.84, gain 0.661, desat 0.45, tint 0.97/1/1.06)
x = rgba[..., :3].astype(np.float32) / 255; L = (0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2])[..., None]
x = L + 0.55 * (x - L); x = np.clip(x * np.array([0.97, 1.0, 1.06]), 0, 1) ** 1.84 * 0.661
g = np.dstack([np.clip(x * 255, 0, 255).astype(np.uint8), rgba[..., 3]])
Image.fromarray(g, "RGBA").save(OUT / "V2_tram_graded.png")
# geometry, in card px (card = master px offset by X0+bx0, Y0+by0)
ox, oy = X0 + bx0, Y0 + by0
def card(xf, yf):
    return (xf - ox, yf - oy)
geo = dict(source="LoC 2002707975 master (sources/.../test-shot/hires/09974u_full.png, 3650x2759)",
           card_origin_in_master=[int(ox), int(oy)], size=[int(bx1 - bx0), int(by1 - by0)],
           canopy_top_y=card(0, 1855)[1], wheel_line_y=card(0, 2118)[1], front_platform_x=[card(1175, 0)[0], card(1310, 0)[0]],
           route_board_x=[card(1365, 0)[0], card(1600, 0)[0]], route_board_y=[card(0, 1870)[1], card(0, 1888)[1]],
           tram_right_x=card(1726, 0)[0], man_x=[card(1330, 0)[0], card(1423, 0)[0]], lamp_x=[card(1415, 0)[0], card(1465, 0)[0]],
           method="hand polygons (tram outline + man + lamp, as they stand in the photograph) seeding cv2.grabCut (6 it), largest component, close 5, erode 1, feather 0.6",
           sha256_master=hashlib.sha256(open(SRC / "test-shot/hires/09974u_full.png", "rb").read()).hexdigest())
json.dump(geo, open(OUT / "V2_tram.json", "w"), indent=1, default=float)
print(json.dumps(geo, indent=1, default=float))
