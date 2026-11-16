import numpy as np, cv2
from PIL import Image, ImageDraw
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/test-shot/"
m = np.array(Image.open(SRC + "v0-master-crop.png"))
S = 7811 / 1200
x0, y0, x1, y1 = [int(round(v * S)) for v in (60, 70, 920, 715)]
c = m[y0:y1, x0:x1]
print(c.shape, (x1-x0)/(y1-y0))
w = cv2.resize(c, (1440, 1080), interpolation=cv2.INTER_AREA)
cv2.imwrite(SRC + "plate-1440.png", w)
# for the insert background: skirt/lap fabric region at higher res
open(SRC + "plate-1440.txt", "w").write(f"master-crop px {x0},{y0},{x1},{y1} -> 1440x1080 (INTER_AREA)\n")
g = Image.fromarray(w).convert("RGB"); d = ImageDraw.Draw(g)
for x in range(0, 1440, 100): d.line([(x, 0), (x, 1080)], fill=(255, 0, 0)); d.text((x + 2, 2), str(x), fill=(255, 255, 0))
for y in range(0, 1080, 100): d.line([(0, y), (1440, y)], fill=(255, 0, 0)); d.text((2, y + 2), str(y), fill=(255, 255, 0))
g.save("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/grid.jpg")
