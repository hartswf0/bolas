# Plan section 11 second-object test: the same retrieval frames (U2's L-S5 close, world trace, FK) rendered with the
# bar shoe (new cut) and with the LACMA M.83.156.1a-b oxford. Same mechanics, same hand; only the object changes.
# python3 second_object.py  -> object-sound/stills/second-object-*.png and second-object-compare.jpg
import sys, os, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "performance"))
import render_ls5 as R  # noqa: E402
OUT = os.path.join(HERE, "..", "..", "..", "sources", "la-mort-en-ce-jardin", "object-sound", "stills")
CUT = os.path.join(OUT, "..", "cut")
TS = [19.25, 19.62, 20.2]
rows = []
for name in ("bar", "oxford"):
    R.S.SHOE_FULL = np.asarray(Image.open(os.path.join(CUT, f"shoe_{name}_white.png")).convert("RGBA"), np.float32)
    row = []
    for t in TS:
        C, rec = R.frame(t)
        im = Image.fromarray(C.astype(np.uint8)); im.save(os.path.join(OUT, f"second-object-{name}-{t:05.2f}.png"))
        row.append(im); print(name, t, rec.get("shoe"), rec.get("shoe_to_face_px"))
    rows.append(row)
W = Image.new("RGB", (3 * 400 + 20, 2 * 270 + 10), (27, 27, 27)); d = ImageDraw.Draw(W)
for r, row in enumerate(rows):
    for c, im in enumerate(row):
        W.paste(im.resize((400, 270), Image.LANCZOS), (c * 410, r * 280))
W.save(os.path.join(OUT, "second-object-compare.jpg"), quality=90)
