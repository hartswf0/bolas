# python3 strip.py out.jpg x0 y0 w h frame,frame,...  : crop a contact strip from cache/shot_NNN.jpg
import sys
from PIL import Image
out, x0, y0, w, h = sys.argv[1], *map(int, sys.argv[2:6]); fr = [int(v) for v in sys.argv[6].split(',')]
cols = 4; rows = (len(fr) + cols - 1) // cols
s = Image.new('RGB', (cols * w, rows * h))
for k, f in enumerate(fr): s.paste(Image.open(f'cache/shot_{f:03d}.jpg').crop((x0, y0, x0 + w, y0 + h)), ((k % cols) * w, (k // cols) * h))
s.save(out)
