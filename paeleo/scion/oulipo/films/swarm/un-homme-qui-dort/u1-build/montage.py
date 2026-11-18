"""montage.py out.png file1 file2 ... (2 columns, half size)"""
import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert("RGB") for f in files]
w, h = ims[0].size
cols = 2; sc = 0.5 if len(ims) > 1 else 1.0
tw, th = int(w * sc), int(h * sc)
rows = (len(ims) + cols - 1) // cols
M = Image.new("RGB", (cols * tw + 4, rows * th + 4 * rows), (255, 0, 0))
for i, im in enumerate(ims):
    M.paste(im.resize((tw, th), Image.LANCZOS), ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
M.save(out)
