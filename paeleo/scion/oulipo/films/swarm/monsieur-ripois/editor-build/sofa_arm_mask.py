"""Editor repair 1: occluder matte of the FOREGROUND sofa arm in the Vachon plate (LoC 2017831564), so the handmade
box can sit on her lap BEHIND it (compositing occlusion). Top edge found per column as the strongest light->dark
vertical step near a hand-placed guide line; the arm's rounded right end is a hand-placed polygon."""
import cv2, numpy as np
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/present/"
g = cv2.imread(SRC + "plate-1440.png", 0).astype(np.float32)
b = cv2.GaussianBlur(g, (0, 0), 2.0)
gy = cv2.Sobel(b, cv2.CV_32F, 0, 1, ksize=5)
guide_x = [0, 250, 400, 500, 600, 680, 750, 800]
guide_y = [690, 700, 720, 742, 758, 775, 790, 800]
ys = []
for x in range(0, 801):
    y0 = int(np.interp(x, guide_x, guide_y))
    win = gy[y0 - 28:y0 + 28, x]
    ys.append(y0 - 28 + int(np.argmin(win)))
ys = np.array(ys, np.float32)
ys = cv2.GaussianBlur(ys[None], (1, 0), 6)[0] if False else np.convolve(np.pad(ys, 12, mode="edge"), np.ones(25) / 25, "valid")
poly = [(0, 1080)] + [(x, float(ys[x]) - 1) for x in range(0, 801)] + [(815, 812), (828, 838), (838, 868), (845, 900), (850, 960), (856, 1080)]
M = np.zeros_like(g); cv2.fillPoly(M, [np.round(np.array(poly) * 4).astype(np.int32)], 1.0, lineType=cv2.LINE_AA, shift=2)
M = cv2.GaussianBlur(M, (0, 0), 1.2)
cv2.imwrite(SRC + "sofa-arm-occluder-mask.png", np.clip(M * 255, 0, 255).astype(np.uint8))
vis = cv2.cvtColor(g.astype(np.uint8), cv2.COLOR_GRAY2BGR)
vis[..., 2] = np.clip(vis[..., 2] * (1 - 0.5 * M) + 255 * 0.5 * M, 0, 255)
cv2.imwrite("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/armmask.jpg", vis[500:1080, 200:1000])
print("ok", ys[::100])
