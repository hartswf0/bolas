"""GrabCut the LoC red cap (frontal, FSA 1943) into a solid head-and-shoulders mask.
Frontal outline = back-view outline: used as the porter's head, seen from behind, in X."""
import cv2, numpy as np
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/cercle-vicieux/test-shot/"
g = cv2.imread(SRC + "loc_3c30642v.jpg")
h, w = g.shape[:2]
gray = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)
mask = np.full((h, w), cv2.GC_BGD, np.uint8)
roi = np.zeros((h, w), bool); roi[180:765, 228:705] = True
mask[roi] = cv2.GC_PR_BGD
mask[roi & (cv2.GaussianBlur(gray, (9, 9), 0) > 34)] = cv2.GC_PR_FGD
mask[roi & (cv2.GaussianBlur(gray, (9, 9), 0) > 90)] = cv2.GC_FGD
rect = (215, 170, 500, 600)          # x,y,w,h around cap, head, shoulders
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
# GrabCut dropped the face (mid-grey on black); a plain luma threshold on the blurred print is cleaner here
m = np.where(roi & (cv2.GaussianBlur(gray, (11, 11), 0) > 48), 255, 0).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
# keep the largest component, fill holes (face, scarf are inside the outline)
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = np.where(lab == k, 255, 0).astype(np.uint8)
cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
f = np.zeros_like(m); cv2.drawContours(f, cs, -1, 255, -1)
f = cv2.morphologyEx(f, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8)); f = cv2.morphologyEx(f, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)); f[765:] = 0
cv2.imwrite(SRC + "work/redcap_mask.png", f)
viz = g.copy(); viz[f == 0] = (viz[f == 0] * 0.3).astype(np.uint8); cv2.drawContours(viz, cs, -1, (0, 0, 255), 2)
cv2.imwrite(SRC + "work/redcap_check.jpg", np.hstack([viz, cv2.cvtColor(255 - f, cv2.COLOR_GRAY2BGR)]))
# head piece only (cap, head, ears, collar): close the cap's lit/dark gap with the convex hull above the brim,
# keep the true photographic outline below it; the body below the collar is a handmade puppet piece.
head = np.zeros_like(f)
top = f.copy(); top[330:] = 0
hull = cv2.convexHull(cv2.findNonZero(top)); cv2.fillPoly(head, [hull], 255)
mid = f.copy(); mid[:330] = 0; mid[485:] = 0
head = cv2.bitwise_or(head, mid)
ys, xs = np.nonzero(head)
head = head[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
cv2.imwrite(SRC + "work/redcap_head.png", head)
print("head", head.shape)
# close the ear notches (31 px ellipse) so the outline reads as one cut piece
m = cv2.copyMakeBorder(head, 20, 0, 20, 20, cv2.BORDER_CONSTANT, 0)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
m = cv2.GaussianBlur(m, (0, 0), 1.5); m = np.where(m > 127, 255, 0).astype(np.uint8)
ys, xs = np.nonzero(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
cv2.imwrite(SRC + "work/redcap_head_closed.png", m)
