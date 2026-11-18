"""Editor repair 1: her gloved hand JOINED to its coat sleeve (forearm), cut from the same V1 crop (LoC 2017831565,
8d04831u.tif) with GrabCut (SCION #29): glove mask = sure FG, a hand-placed sleeve polygon = probable FG, the rest
probable/sure BG. The sleeve's cut end (left edge of the crop) is feathered so the forearm melts into her own coat."""
import cv2, numpy as np
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/present/"
h = cv2.imread(SRC + "v1-master-hand.png", 0)
glove = cv2.imread(SRC + "piece-her_hand-mask.png", 0) > 128
Hh, Ww = h.shape
sleeve = np.zeros((Hh, Ww), np.uint8)
cv2.fillPoly(sleeve, [np.array([(0, 98), (100, 138), (200, 196), (300, 214), (385, 222), (385, 480), (300, 478), (200, 476), (100, 458), (0, 455)], np.int32)], 1)
core = cv2.erode(sleeve, np.ones((25, 25), np.uint8))
gc = np.full((Hh, Ww), cv2.GC_BGD, np.uint8)
gc[cv2.dilate(sleeve | glove.astype(np.uint8), np.ones((31, 31), np.uint8)) > 0] = cv2.GC_PR_BGD
gc[sleeve > 0] = cv2.GC_PR_FGD
gc[(core > 0) | glove] = cv2.GC_FGD
img = cv2.cvtColor(h, cv2.COLOR_GRAY2BGR)
bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(img, gc, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
a = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.float32)
n, lab, st, _ = cv2.connectedComponentsWithStats(a.astype(np.uint8))
a = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.float32)
a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
a = cv2.GaussianBlur(a, (0, 0), 1.5)
ramp = np.clip((np.arange(Ww) - 10) / 150.0, 0, 1)[None, :] ** 1.5          # sleeve end melts into her coat
a = np.where(glove, a, a * ramp)
cv2.imwrite(SRC + "piece-her_arm-mask.png", np.clip(a * 255, 0, 255).astype(np.uint8))
vis = cv2.cvtColor(h, cv2.COLOR_GRAY2BGR).astype(np.float32); vis[..., 2] = vis[..., 2] * (1 - 0.5 * a) + 255 * 0.5 * a
cv2.imwrite("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/armpiece.jpg", vis.astype(np.uint8))
print("arm area", int(a.sum()))
