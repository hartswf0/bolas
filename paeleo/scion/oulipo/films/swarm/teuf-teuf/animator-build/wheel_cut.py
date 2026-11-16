"""GrabCut the Ljubljana Marshes wheel out of its (CC BY-SA 4.0) photograph, undo the oblique
view by fitting an ellipse to the cut and mapping it to a circle, tone to charcoal luminance.
Decode with PIL/cv2 only."""
import numpy as np, cv2, json
from PIL import Image
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/teuf-teuf/wheel_ljubljana.jpg"
OUT = "/home/user/bolas/paeleo/scion/oulipo/films/sources/teuf-teuf/animator/"
img = np.asarray(Image.open(SRC).convert("RGB"))[:, :, ::-1].copy()
mask = np.zeros(img.shape[:2], np.uint8)
rect = (140, 30, 680, 480)
bg = np.zeros((1, 65), np.float64); fg = np.zeros((1, 65), np.float64)
cv2.grabCut(img, mask, rect, bg, fg, 6, cv2.GC_INIT_WITH_RECT)
m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
# keep the wood only: it is brighter/warmer than the black case and the acrylic disc
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
wood = ((hsv[..., 2] > 70) & (hsv[..., 1] > 25)).astype(np.uint8) * 255
m = cv2.bitwise_and(m, wood)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
keep = np.zeros_like(m)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] > 4000:
        keep[lab == i] = 255
m = keep
cv2.imwrite(OUT + "wheel_grabcut_mask_src.png", m)
cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
pts = np.vstack(cs)
hull = cv2.convexHull(pts)
(cx, cy), (w, h), ang = cv2.fitEllipse(hull)
print("ellipse", cx, cy, w, h, ang)
json.dump(dict(center=[cx, cy], axes=[w, h], angle=ang, rect=rect), open(OUT + "wheel_ellipse.json", "w"))
# map ellipse -> circle of radius R0
R0 = 300
a = np.deg2rad(ang)
# ellipse axes: w along angle a, h perpendicular
ca, sa = np.cos(a), np.sin(a)
Rm = np.array([[ca, sa], [-sa, ca]])               # rotate image so axis w is horizontal
S = np.diag([2 * R0 / w, 2 * R0 / h])
A = S @ Rm
t = np.array([R0 + 10, R0 + 10]) - A @ np.array([cx, cy])
M = np.hstack([A, t[:, None]]).astype(np.float32)
size = (2 * R0 + 20, 2 * R0 + 20)
rgb = cv2.warpAffine(img, M, size, flags=cv2.INTER_CUBIC)
mm = cv2.warpAffine(m, M, size, flags=cv2.INTER_LINEAR)
cv2.imwrite(OUT + "wheel_unwarped_rgb.png", rgb)
cv2.imwrite(OUT + "wheel_unwarped_mask.png", mm)

# ---- second pass: the hull fit above is biased by the broken edge. Fit the ellipse only to
# rim points of the intact arc, centred on the real (square) axle hole.
inv = cv2.bitwise_not(m)
n2, lab2, st2, cen2 = cv2.connectedComponentsWithStats(inv)
holes = [(st2[i, cv2.CC_STAT_AREA], i) for i in range(1, n2)
         if st2[i, cv2.CC_STAT_LEFT] > 0 and st2[i, cv2.CC_STAT_TOP] > 0 and
         st2[i, cv2.CC_STAT_LEFT] + st2[i, cv2.CC_STAT_WIDTH] < m.shape[1] and 500 < st2[i, cv2.CC_STAT_AREA] < 20000]
holes.sort(reverse=True)
hx, hy = cen2[holes[0][1]]
print("hole", hx, hy, holes[0][0])
cpts = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float64)
angs = np.degrees(np.arctan2(cpts[:, 1] - hy, cpts[:, 0] - hx))
# intact rim: left half + top (screen angles 100..260 and -150..-60 approx: exclude the broken right/bottom-right)
sel = (angs > 95) | (angs < -55)
rim = cpts[sel]
# conic centred on the hub: A x^2 + B xy + C y^2 = 1 (least squares on the intact rim)
dx_, dy_ = rim[:, 0] - hx, rim[:, 1] - hy
Q = np.c_[dx_ * dx_, dx_ * dy_, dy_ * dy_]
qa, qb, qc = np.linalg.lstsq(Q, np.ones(len(rim)), rcond=None)[0]
ev, evec = np.linalg.eigh(np.array([[qa, qb / 2], [qb / 2, qc]]))
ax_ = 1 / np.sqrt(ev)                       # semi-axes
eang = float(np.degrees(np.arctan2(evec[1, 0], evec[0, 0])))
ecx, ecy, ew, eh = hx, hy, 2 * ax_[0], 2 * ax_[1]
print("rim ellipse", ecx, ecy, ew, eh, eang)
a = np.deg2rad(eang); ca, sa = np.cos(a), np.sin(a)
Rm = np.array([[ca, sa], [-sa, ca]])
S = np.diag([2 * R0 / ew, 2 * R0 / eh])
A = S @ Rm
C = R0 + 10
t = np.array([C, C]) - A @ np.array([ecx, ecy])
M = np.hstack([A, t[:, None]]).astype(np.float32)
rgb = cv2.warpAffine(img, M, size, flags=cv2.INTER_CUBIC)
mm = cv2.warpAffine(m, M, size, flags=cv2.INTER_LINEAR).astype(np.float32) / 255
hc = A @ np.array([hx, hy]) + t
print("hole in unwarped", hc)
lum = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
# restore the missing fragment with the wheel's own wood, point-mirrored through the hub
rot = cv2.warpAffine(lum, cv2.getRotationMatrix2D((C, C), 180, 1.0), size, flags=cv2.INTER_LINEAR)
rotm = cv2.warpAffine(mm, cv2.getRotationMatrix2D((C, C), 180, 1.0), size, flags=cv2.INTER_LINEAR)
yy, xx = np.mgrid[0:size[1], 0:size[0]]
disc = (np.hypot(xx - C, yy - C) <= R0 * 0.985).astype(np.float32)
hole = np.zeros_like(disc)
hw = 26
hole[int(hc[1]) - hw:int(hc[1]) + hw, int(hc[0]) - hw:int(hc[0]) + hw] = 1
# the real hole sits slightly off the fitted centre; re-centre the square hole at the hub
hole = np.zeros_like(disc); hole[C - hw:C + hw, C - hw:C + hw] = 1
fill = np.clip(rotm - mm, 0, 1) * disc
L = lum * mm + rot * fill
alpha = np.clip(mm + fill, 0, 1) * disc
alpha = cv2.GaussianBlur(alpha, (0, 0), 1.2) * (1 - hole)
real_frac = float((mm * disc).sum() / disc.sum())
# tone to charcoal: keep the real grain/plank seams, map into the dark range of the ramp
lo, hi = np.percentile(L[alpha > 0.5], [3, 97])
Ln = np.clip((L - lo) / (hi - lo + 1e-6), 0, 1)
tone = 0.05 + 0.30 * Ln ** 1.2
tone = tone * (1 - 0.25 * fill)            # restored half a touch darker (declared)
np.save(OUT + "wheel_lum.npy", tone.astype(np.float32))
np.save(OUT + "wheel_alpha.npy", alpha.astype(np.float32))
Image.fromarray((tone * alpha * 255 + (1 - alpha) * 230).astype(np.uint8)).save(OUT + "wheel_charcoal_preview.png")
json.dump(dict(center=[ecx, ecy], axes=[ew, eh], angle=eang, hole_src=[hx, hy], R0=R0, real_fraction_of_disc=real_frac),
          open(OUT + "wheel_ellipse.json", "w"))
print("real fraction", real_frac)
